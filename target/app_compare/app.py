from flask import Flask, render_template, request, jsonify

from pynq import Overlay
from pynq import MMIO
from pynq import allocate
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable

from cnn_mnist import CNN

from PIL import Image
import re
import base64
import io

from time import time

import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

def program_fpga():
    global dma_send, dma_recv, input_buffer, output_buffer
    
    overlay = Overlay('/home/ubuntu/workspace/cnn_mnist.bit')
    
    dma = overlay.axi_dma_0
    dma_send = overlay.axi_dma_0.sendchannel
    dma_recv = overlay.axi_dma_0.recvchannel

    input_buffer = allocate(shape=(784,), dtype=np.uint8)
    output_buffer = allocate(shape=(1,), dtype=np.uint8)

def get_model():
    global model
    model = torch.load("./cnn_mnist.pt", weights_only=False)
    model.eval()
    print(model)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def predict():
    base64str = request.get_json(force=True)['base64str']
    print(base64str)

    imgstr = re.search(r'base64,(.*)', str(base64str)).group(1)
    file = io.BytesIO(base64.b64decode(imgstr));
    img = Image.open(file).convert("L")
    img = img.resize((28, 28))
    im2arr = np.array(img)

    # HW prediction
    im2arr_hw = im2arr.reshape(1,1,1,784)
    for i in range(784):
        input_buffer[i] = im2arr_hw[0][0][0][i]
    t1 = time()
    dma_send.transfer(input_buffer)
    dma_recv.transfer(output_buffer)
    t2 = time()
    print('HW predicted output: {}'.format(str(output_buffer[0])))
    t_diff_hw = t2 - t1
    print('Time used for HW CNN: {}s'.format(t_diff_hw))

    # SW prediction
    im2arr_sw = im2arr.reshape(1, 1, 28, 28)
    data = Variable(torch.tensor((im2arr_sw / 255), dtype = torch.float32))
    t1 = time()
    output = model(data)
    t2 = time()
    pred = output.data.max(1, keepdim=True)[1]
    pred_str = str(', '.join(map(str, pred.flatten().tolist())))
    print('SW predicted output: {}'.format(pred_str))
    t_diff_sw = t2 - t1
    print('Time used for SW CNN: {}s'.format(t_diff_sw))

    # Convet time to ms
    hw_time = t_diff_hw * 1000;
    sw_time = t_diff_sw * 1000;
    speed_up = sw_time / hw_time;

    response = {
        'prediction': str(output_buffer[0]),
        'hw_time': hw_time,
        'sw_time': sw_time,
        'speed_up': '%.1f' % (speed_up)
    }
    return jsonify(response)

print(" * Programming the FPGA...")
program_fpga()
print(" * FPGA programming done")

print(" * Loading model...")
get_model()
print(" * Loading model done")

if __name__ == '__main__':
    app.run(host='0.0.0.0')
