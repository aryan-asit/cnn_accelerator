var margin = {top: 20, right: 20, bottom: 20, left: 60},
    width = 300 - margin.left - margin.right,
    height = 350 - margin.top - margin.bottom;

var zeros = [
    { name: 'CPU', value: 0.0 },
    { name: 'FPGA', value: 0.0 },
];

var xScale = d3.scale.ordinal()
    .rangeRoundBands([0, width], .3)
    .domain(zeros.map(function(d) { return d.name; }));

var yScale = d3.scale.linear()
    .range([height, 0])
    .domain([0, 20]);

var xAxis = d3.svg.axis()
    .scale(xScale)
    .orient("bottom");

var yAxis = d3.svg.axis()
    .scale(yScale)
    .orient("left")
    .ticks(5);

var svg = d3.select("#svg_chart")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
    .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var tip = d3.tip()
.attr('class', 'd3-tip')
    .offset([-10, 0])
    .html(function(d) {
        return "<strong>" + d.value + " ms</strong>";
    })

svg.call(tip);

svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
    .call(xAxis)
        .selectAll("text")
        .style("text-anchor", "middle")

svg.append("g")
        .attr("class", "y axis")
    .call(yAxis)
    .append("text")
        .attr("transform", "rotate(-90)")
        .attr("x", 0-(height/2))
        .attr("y", 0-45)
        .style("text-anchor", "middle")
        .text("Execution time [ms]");

svg.selectAll("bar")
        .data(zeros)
        .enter()
    .append("rect")
        .attr("class", "bar")
        .attr("x", function(d) { return xScale(d.name); })
        .attr("width", xScale.rangeBand())
        .attr("y", function(d) { return yScale(d.value); })
        .attr("height", function(d) { return height - yScale(d.value); })
        .on('mouseover', tip.show)
        .on('mouseout', tip.hide);

function updateChart(data) {
    d3.selectAll("rect")
        .data(data)
        .transition()
        .duration(500)
        .attr("y", function(d) { return yScale(d.value); })
        .attr("height", function(d) { return height - yScale(d.value); });
}

paper.install(window);
var canvas = document.getElementById('my_canvas');

$(window).on('load', function() {
    canvas.style.backgroundColor = 'black';
    paper.setup(canvas);

    var path;
    var tool = new Tool();
    tool.onMouseDown = function(event) {
        path = new Path();
        path.strokeColor = 'white';
        path.strokeWidth = 15;
        path.strokeCap = 'round';
        path.strokeJoin = 'round';
    }
    tool.onMouseDrag = function(event) {
        path.add(event.point);
    }
});

$('#predict').click(function(){
    var url = { base64str: canvas.toDataURL() }
    $("#txt_status").removeClass().toggleClass("fa fa-spinner fa-spin");
    $.post(window.location.origin, JSON.stringify(url), function(response) {
        console.log(response);
        $("#result").text(response.prediction);
        $('#txt_speed_up').text(response.speed_up);
        $("#txt_status").removeClass().toggleClass("fa fa-check");
        var data = [
            { name: 'CPU', value: response.sw_time },
            { name: 'FPGA', value: response.hw_time },
        ];
        updateChart(data);
    });
});

$('#clear').click(function(){
    paper.project.activeLayer.removeChildren();
    paper.view.draw();
});
