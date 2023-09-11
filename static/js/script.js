window.token = '{{ token }}';
// Perform background initialization
doAjax("/", "POST");

var x = 0; //Initial field counter
var list_maxField = 10; //Input fields increment limitation
uploaded_files = null;

function getMethods(obj) {
    var result = [];
    for (var id in obj) {
        try {
            if (typeof (obj[id]) == "function") {
                result.push(id + ": " + obj[id].toString());
            }
        } catch (err) {
            result.push(id + ": inaccessible");
        }
    }
    return result;
}


function caseFiltering(key) {
    doAjax("/case_filtering", "POST", selectCaseHandler, { 'key': key });
}

function selectCaseHandler() {
    if (this.responseText) {
        var response = JSON.parse(this.responseText);
        console.log(response)

        var key = response.pop();
        const table = document.getElementById("files-table");
        var row = table.rows[key];
        row.deleteCell(-1);
        var cell3 = row.insertCell(-1);

        cell3.innerHTML = '<iframe name="dummy" style="display:none;"></iframe>'
            + '<form method="POST" action ="/filter/case" class="form-group" target="dummy">'
            + '<label for="selectCase">Filter by case: </label>'
            + '<select class="custom-select" name="case_select" id="selectCase"> </select>'
            + ' <button type="submit" class="btn btn-primary" onClick="view_plot(' + key + ')">3D Scatter</button>'
            + '</form>';
        var select = document.getElementById("selectCase");
        select.innerHTML = "";
        select.innerHTML += "<option value='all' selected='selected'>All</option>";
        response.forEach(element => {
            select.innerHTML += "<option value=\"" + element + "\">" + element + "</option>";
        });
    }
}

function updateTree() {
    if (this.responseText) {
        var response = JSON.parse(this.responseText);
        var key = response.file_key
        // create a network
        var container = document.getElementById('mynetwork');
        // provide the data in the vis format
        var data = {
            nodes: response.nodes,
            edges: response.edges
        };
        var options = {
            physics: {
                enabled: false,
                barnesHut: {
                    gravitationalConstant: -50000,
                    avoidOverlap: 1
                },
                stabilization: {
                    enabled: true,
                },
            },
            layout: {
                hierarchical: {
                    enabled: false,
                    direction: 'UD',
                }
            },
            edges: {
                arrows: {
                    to: true
                },
                color: {
                    color: '#919191'
                },
                font: {
                    background: '#ffffff',
                    size: 20
                },
                smooth: {
                    enabled: false,
                },
                selfReference: {
                    size: 30,
                }
            },
            nodes: {
                shape: 'box',
                color: {
                    border: '#919191'
                },
                font: {
                    size: 20
                }
            }
        }
        var network = new vis.Network(container, data, options);
        network.on("click", function (params) {
            if (params.nodes != undefined & params.nodes[0] != undefined) {
                //doAjax("/show/heatmap", "POST", showHeatmapHandler, { 'activity': params.nodes[0] });
                doAjax("/show/scatter2D", "POST", showScatterHandler, { 'activity': params.nodes[0], 'key': key });
            }
        });
    }
}

function updateArea() {
    if (this.responseText) {
        var response = JSON.parse(this.responseText);
        var key = response.file_key
        // create a network
        var container = document.getElementById('mynetwork');
        // provide the data in the vis format
        var data = {
            nodes: response.nodes,
            edges: response.edges
        };
        var options = {
            edges: {
                arrows: {
                    to: true
                }
            },
            nodes: {
                shape: 'box'
            }
        }
        var network = new vis.Network(container, data, options);
        network.on("click", function (params) {
            if (params.nodes != undefined & params.nodes[0] != undefined) {
                doAjax("/show/area", "POST", showAreaHandler, { 'location': params.nodes[0], 'key': key });
            }
        });
    }
}

function showScatterHandler() {
    if (this.responseText) {
        var response = JSON.parse(this.responseText);
        var activity = response.activity
        var data = [
            {
                x: response.x,
                y: response.y,
                type: 'scatter',
                mode: 'markers'
            }
        ];

        var layout = {
            xaxis: {
                range: [0, 10]
            },
            yaxis: {
                range: [0, 10]
            },
            title: activity
        };

        Plotly.newPlot('scatter', data, layout);
    }
}

function showHeatmapHandler() {
    if (this.responseText) {
        var response = JSON.parse(this.responseText);
        var data = [
            {
                x: response.data.x,
                y: response.data.y,
                z: response.data.z,
                type: 'heatmap'
            }
        ];

        Plotly.newPlot('heatmap', data);
    }
}

function discoverResourceTree(key) {
    doAjax("/discover/resource", "POST", updateTree, { 'key': key });
}

function discoverActivityTree(key) {
    doAjax("/discover/activity", "POST", updateTree, { 'key': key });
}

function discoverPerformanceTree(key) {
    doAjax("/discover/performance", "POST", updateTree, { 'key': key });
}

function discoverLocationsTree(key) {
    doAjax("/discover/locations", "POST", updateArea, { 'key': key });
}

function view_plot(key) {
    //var type_filter = document.querySelector('input[name="filter_by"]:checked').value;
    doAjax("/view/3Dscatter", "POST", show3DScatter, { 'key': key, 'filter': 'activity' });
}

function showAreaHandler() {
    if (this.responseText) {
        var response = JSON.parse(this.responseText);
        x = response.x;
        y = response.y;

        var data = [
            {
                x: x,
                y: y,
                type: 'bar',
            }
        ];

        Plotly.newPlot('scatter', data);

    }
}

function show3DScatter() {
    if (this.responseText) {
        const scatterDiv = document.getElementById("scatter3d");
        scatterDiv.innerHTML = '<object data="gui/scatter3D.html"  width="1400"  height="1400"></object>';
    }
}

function printResponse() {
    if (this.responseText) {
        // Print exported filename
        var response = JSON.parse(this.responseText);
        file_name = response.saved_as;

        var p = document.getElementById("generated_xes_name");
        p.innerHTML = '<div class="banner">  <span class="closebtn" onclick="this.parentElement.style.display=\'none\';">&times;</span> ' +
            "<strong> Your file has been saved as: </strong>" + file_name + "</div>"

    }
}

function csvParser() {
    doAjax("/csv/parse", "POST", printResponse);
}

function discoverAll() {
    doAjax("/discover/all", "POST", updateTree, uploaded_files);
}

function discoverAllPerformance() {
    doAjax("/discover/all/performance", "POST", updateTree, uploaded_files);
}

function showScatter3DAll() {
    doAjax("/view/3Dscatter/all", "POST", show3DScatter);
}

function scatterAll() {
    doAjax("/discover/all", "POST", showScatter3DAll, uploaded_files);
}

function showHide(div) {
    var x = document.getElementById(div);
    if (x.style.visibility == 'hidden') {
        x.style.visibility = 'visible';
    } else {
        x.style.visibility = 'hidden';
    }
}

/*
        function show3DScatter() {
            if (this.responseText) {
                var response = JSON.parse(this.responseText);
                const a = document.getElementById("scatter3d");
                var data = [{
                    x: Object.values(response.x),
                    y: Object.values(response.y),
                    z: Object.values(response.z),
                    mode: 'markers',
                    type: 'scatter3d'
                }];

                // Define Layout
                var layout = {
                    xaxis: { range: [0, 10], title: "x" },
                    yaxis: { range: [0, 10], title: "y" },
                    zaxis: { range: [0, 2], title: "z" },
                    title: "3D Scatter"
                };

                Plotly.newPlot('scatter3d', data, layout);
            }
        }
        */

function openLink(e) {
    e.preventDefault()
    var request = { url: e.currentTarget.href }
    doAjax("/open-url", "POST", false, request)
}

// From https://gist.github.com/dharmavir/936328
function getHttpRequestObject() {
    // Define and initialize as false
    var xmlHttpRequst = false;

    // Mozilla/Safari/Non-IE
    if (window.XMLHttpRequest) {
        xmlHttpRequst = new XMLHttpRequest();
    }
    // IE
    else if (window.ActiveXObject) {
        xmlHttpRequst = new ActiveXObject("Microsoft.XMLHTTP");
    }
    return xmlHttpRequst;
}

// Does the AJAX call to URL specific with rest of the parameters
function doAjax(url, method, responseHandler, data) {
    // Set the variables
    url = url || "";
    method = method || "GET";
    async = true;
    data = data || {};
    data.token = window.token;

    if (url == "") {
        alert("URL can not be null/blank");
        return false;
    }
    var xmlHttpRequest = getHttpRequestObject();

    // If AJAX supported
    if (xmlHttpRequest != false) {
        xmlHttpRequest.open(method, url, async);
        // Set request header (optional if GET method is used)
        if (method == "POST") {
            xmlHttpRequest.setRequestHeader("Content-Type", "application/json");
        }
        // Assign (or define) response-handler/callback when ReadyState is changed.
        xmlHttpRequest.onreadystatechange = responseHandler;
        // Send data
        xmlHttpRequest.send(JSON.stringify(data));
    }
    else {
        alert("Please use browser with Ajax support.!");
    }
}