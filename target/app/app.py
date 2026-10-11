from flask import Flask, render_template, request, jsonify

from pynq import Overlay
from pynq import MMIO
from pynq import allocate
import numpy as np

from PIL import Image
import re
import base64
import io

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

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def predict():
    base64str = request.get_json(force=True)['base64str']
    #print(base64str)

    imgstr = re.search(r'base64,(.*)', str(base64str)).group(1)
    file = io.BytesIO(base64.b64decode(imgstr));
    img = Image.open(file).convert("L")
    img = img.resize((28, 28))
    im2arr = np.array(img)
    im2arr = im2arr.reshape(1,1,1,784)

    for i in range(784):
        input_buffer[i] = im2arr[0][0][0][i]        
    dma_send.transfer(input_buffer)
    dma_recv.transfer(output_buffer)
    #print(str(output_buffer[0]))

    response = {
        'prediction': str(output_buffer[0])
    }
    return jsonify(response)

print(" * Programming the FPGA...")
program_fpga()
print(" * FPGA programming done")

if __name__ == '__main__':
    app.run(host='0.0.0.0')
