uploaded_files = null;

function generate_dagre(data) {
    console.log(data)
    nodes = []
    console.log(data)

    var g = new dagre.graphlib.Graph({
        multigraph: true,
        compound: true,
        multiedgesep: 10,
        multiranksep: 50
    });

    console.log(g)

    // Set an object for the graph label
    g.setGraph({ rankdir: 'TB', nodesep: 25 });

    // Default to assigning a new object as a label for each new edge.
    g.setDefaultEdgeLabel(function () { return {}; });

    dagre.layout(g);


    for (n in data.nodes) {
        //node_data.push({ id: in_data.nodes[n]['Event_Id'], properties: in_data.nodes[n] })
        node = data.nodes[n]
        if (node.label != null) {
            node.label = node.label.replaceAll("_", "\n")
        }

        g.setNode(node.id, { label: node.label })
    }

    g.nodes().forEach(function (v) {
        var node = g.node(v);
        // Round the corners of the nodes
        node.rx = node.ry = 5;
    });

    edges = []
    for (e in data.edges) {
        edge = data.edges[e]
        edge_label = edge.label
        //        edge_properties = edge.edge_properties
        //"edge_weight": 1,   "CorrelationType": "Message",
        /*
        edge_weight = edge_properties.edge_weight
        edge_info = edge_weight + '(' + edge_properties.CorrelationType + ')\n:' + edge_label
        visibility = 'visible'
        if ((edge_weight > 0 && edge_weight < 6) || (edge_weight > 10 && edge_weight < 50)) {
            visibility = 'hidden'
        }
        if (edge_weight >= 4) {
            edge_weight = edge_weight / 20
        }
        if (edge_weight == '') {
            edge_weight = 1
        }*/
        g.setEdge(edge.from, edge.to, {
            label: edge_label,
            name: edge.from + '-' + edge_label + '-' + edge.to,
            curve: d3.curveBasis
        })
    }


    elements = nodes.concat(edges)
    console.log(nodes)

    const svg = d3.select('#graph-container').append('svg');
    const svgGroup = svg.append('g');

    let initialZoomState;

    // Create a zoom behavior
    const zoom = d3.zoom().on('zoom', (event) => {
        svgGroup.attr('transform', event.transform);
    });

    // Apply zoom to the SVG container
    svg.call(zoom);

    initialZoomState = d3.zoomTransform(svg.node());


    // Render the graph
    const render = new dagreD3.render();
    render(svgGroup, g);

    addOnFunctionalities(svgGroup, g)


    // Change the graph direction
    d3.select('#toggle-button').on('click', function () {

        const currentDirection = g.graph().rankdir; // Get the current direction

        // Toggle the direction
        const newDirection = currentDirection === 'TB' ? 'LR' : 'TB';

        const currentZoomState = d3.zoomTransform(svg.node());

        // Update the graph with the new direction
        g.setGraph({ rankdir: newDirection, nodesep: 25 });
        dagre.layout(g);


        // Render the updated graph
        svg.selectAll('*').remove(); // Clear the existing SVG content
        const svgGroup = svg.append('g');

        // Create a zoom behavior
        const zoomChange = d3.zoom().on('zoom', (event) => {
            svgGroup.attr('transform', event.transform);
        });

        // Apply zoom to the SVG container
        svg.call(zoomChange);

        const render = new dagreD3.render();

        render(svgGroup, g);
        addOnFunctionalities(svgGroup, g)

    });
}

/**
 * Graph interactions handler
 * @param {*} svgGroup 
 * @param {*} g 
 */
function addOnFunctionalities(svgGroup, g) {
    // Add unique IDs to the edge paths during rendering
    svgGroup.selectAll('g.edgePath path')
        .attr('id', (edgeId) => g.edge(edgeId).name);

    // Handle double click on nodes
    svgGroup.selectAll('g.node')
        .on('dblclick', function (event, nodeId) {
            // Reset the style of all edges
            event.stopPropagation(); // Prevent click event from triggering as well

            // Reset the style of all edges
            svgGroup.selectAll('g.edgePath path').style('stroke', '#999');

            // Highlight outgoing edges from the double-clicked node
            g.outEdges(nodeId).forEach(edge => {
                svgGroup.selectAll(`g.edgePath path[id="${g.edge(edge).name}"]`).style('stroke', '#8a67c2');
            });
            g.inEdges(nodeId).forEach(edge => {
                svgGroup.selectAll(`g.edgePath path[id="${g.edge(edge).name}"]`).style('stroke', '#e4a531');
            });
        });

    const contextMenu = d3.select('#context-menu');
    const contextMenuOptions = contextMenu.selectAll('.context-menu-option');

    // Handle right-click on nodes to show the context menu
    svgGroup.selectAll('g.node')
        .on('contextmenu', function (event, nodeId) {
            document.getElementById("activity_id").setAttribute("value", nodeId)
    
            event.preventDefault(); // Prevent the default context menu
            event.stopPropagation(); // Stop propagation to prevent triggering other click events

            // Position the context menu next to the node
            contextMenu.style('left', event.layerX + 5 + 'px');
            contextMenu.style('top', event.layerY + 'px');

            // Show the context menu
            contextMenu.style('display', 'block');
            console.log(contextMenu)

            // Handle context menu option clicks
            contextMenuOptions.on('click', function (optionId) {
                // Perform actions based on the selected option
                var option = optionId.srcElement.id

                option = option.replace('-menu', '')

                // Hide the context menu
                contextMenu.style('display', 'none');

                // Trigger the backend
                document.getElementById(option).setAttribute("value", true)
                console.log(document.getElementById(option))
                document.getElementById("see_" + option + "_graph").click();
            });
        });

    // Hide the context menu on document click
    d3.select(document).on('click', function () {
        contextMenu.style('display', 'none');
        svgGroup.selectAll('g.edgePath path').style('stroke', '#999');

    });
}

// TODO fix
function downloadGraph() {
    const svg = d3.select('#graph-container svg');

    // Clone the SVG element
    const clonedSvg = svg.node().cloneNode(true);

    // Append the cloned SVG to the document
    document.body.appendChild(clonedSvg);

    // Download SVG
    const svgData = new XMLSerializer().serializeToString(clonedSvg);
    const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'graph.svg';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    // Remove the cloned SVG from the document
    document.body.removeChild(clonedSvg);
}

function showScatterHandler(responseText) {
    var activity = responseText

    var data = [
        {
            x: activity.x,
            y: activity.y,
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


function showHide(div) {
    var x = document.getElementById(div);
    if (x.style.visibility == 'hidden') {
        x.style.visibility = 'visible';
    } else {
        x.style.visibility = 'hidden';
    }
}

function deleteRow(t) {
    var row = t.parentNode.parentNode.parentNode;
    console.log(row)
    document.getElementById("files-table").deleteRow(row.rowIndex);
}



function checkToggle() {
    var divtoggle = document.getElementById("space_div")
    if (divtoggle != null) {
        const toggle = document.querySelector('.toggle');

        toggle.addEventListener('click', () => {
            console.log('sono qui :)')
        });
    }
}

setInterval(checkToggle, 5000);