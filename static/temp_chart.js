var smoothie = new SmoothieChart({
    millisPerPixel:1000, minValue:20, maxValue:105,
    grid:{fillStyle:'#bdbdbd',verticalSections:9},
    labels:{fillStyle:'#a10000'},
    timestampFormatter:SmoothieChart.timeFormatter});
smoothie.streamTo(document.getElementById("smoothie_canvas"));

var gauge_opts = {
    angle: -0.16, // The span of the gauge arc
    lineWidth: 0.23, // The line thickness
    radiusScale: 1, // Relative radius
    pointer: {
            length: 0.6, // // Relative to gauge radius
            strokeWidth: 0.035, // The thickness
            color: '#000000' // Fill color
          },
    limitMax: false,     // If false, max value increases automatically if value > maxValue
    limitMin: false,     // If true, the min value of the gauge will be fixed
    colorStart: '#6FADCF',   // Colors
    colorStop: '#8FC0DA',    // just experiment with them
    strokeColor: '#E0E0E0',  // to see which ones work best for you
    generateGradient: true,
    highDpiSupport: true,     // High resolution support
};
var target = document.getElementById('gauge_canvas'); // your canvas element
var gauge = new Gauge(target).setOptions(gauge_opts); // create sexy gauge!
gauge.maxValue = 120; // set max gauge value
gauge.setMinValue(15);  // Prefer setter over gauge.minValue = 0
gauge.animationSpeed = 32; // set animation speed (32 is default value)
gauge.setTextField(document.getElementById("gauge-value"), 2);

fetch('/status')
    .then(response => { console.log(response); return response.json(); })
    .then(myjson => { console.log(myjson.temp); });

var temp = new TimeSeries();
setInterval(function() {
    fetch('/status')
        .then(response => { return response.json() })
        .then(function(data) {
            console.log(data.temp);
            gauge.set(data.temp);
            temp.append(new Date().getTime(), data.temp);
        });
}, 5000);
smoothie.addTimeSeries(temp, {lineWidth:2, strokeStyle:'#a42300'});
