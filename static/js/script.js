uploaded_files = null;


function generate_graph(data) {
    console.log(data)
    nodes = []
    console.log(data)
    for (n in data.nodes) {
        //node_data.push({ id: in_data.nodes[n]['Event_Id'], properties: in_data.nodes[n] })
        node = data.nodes[n]
        if (node.label != null) {
            node.label = node.label.replaceAll("_", "\n")
        }
        nodes.push({ data: { id: node.id, label: node.label } })
    }

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
        edges.push({ data: { source: edge.from, target: edge.to, id: e, label: edge_label } })
    }

    elements = nodes.concat(edges)
    console.log(nodes)

    var cy = cytoscape({
        container: document.getElementById('cyto'), // container to render in
        elements: elements,
        style: [ // the stylesheet for the graph
            {
                selector: 'node',
                style: {
                    'height': 50,
                    'width': 100,
                    'background-color': '#666666',
                    'shape': 'round-rectangle',
                    'label': 'data(label)',
                    'color': '#ffffff',
                    'text-wrap': 'wrap',
                    'text-halign': 'center',
                    'text-valign': 'center'
                }
            },

            {
                selector: 'edge',
                style: {
                    'label': 'data(label)',
                    'width': 1,
                    'line-color': 'data(color)',
                    'target-arrow-color': 'data(color)',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'text-background-opacity': 1,
                    'text-background-color': '#ffffff',
                    'text-wrap': 'wrap',
                    'loop-sweep': '-45deg',
                    'control-point-step-size': 100,
                    'segment-distances': "50 -50 20",

                }
            }
        ],

        layout: {
            name: 'klay',
            // transform a given node position. Useful for changing flow direction in discrete layouts
            nodeDimensionsIncludeLabels: true, // Boolean which changes whether label dimensions are included when calculating node dimensions
            fit: true, // Whether to fit
            padding: 20, // Padding on fit
            animate: false, // Whether to transition the node positions
            klay: {
                addUnnecessaryBendpoints: false, // Adds bend points even if an edge does not change direction.
                aspectRatio: 1.6, // The aimed aspect ratio of the drawing, that is the quotient of width by height
                borderSpacing: 20, // Minimal amount of space to be left to the border
                compactComponents: false, // Tries to further compact components (disconnected sub-graphs).
                crossingMinimization: 'LAYER_SWEEP', // Strategy for crossing minimization.
                /* LAYER_SWEEP The layer sweep algorithm iterates multiple times over the layers, trying to find node orderings that minimize the number of crossings. The algorithm uses randomization to increase the odds of finding a good result. To improve its results, consider increasing the Thoroughness option, which influences the number of iterations done. The Randomization seed also influences results.
                INTERACTIVE Orders the nodes of each layer by comparing their positions before the layout algorithm was started. The idea is that the relative order of nodes as it was before layout was applied is not changed. This of course requires valid positions for all nodes to have been set on the input graph before calling the layout algorithm. The interactive layer sweep algorithm uses the Interactive Reference Point option to determine which reference point of nodes are used to compare positions. */
                cycleBreaking: 'INTERACTIVE', // Strategy for cycle breaking. Cycle breaking looks for cycles in the graph and determines which edges to reverse to break the cycles. Reversed edges will end up pointing to the opposite direction of regular edges (that is, reversed edges will point left if edges usually point right).
                /* GREEDY This algorithm reverses edges greedily. The algorithm tries to avoid edges that have the Priority property set.
                INTERACTIVE The interactive algorithm tries to reverse edges that already pointed leftwards in the input graph. This requires node and port coordinates to have been set to sensible values.*/
                direction: 'DOWN', // Overall direction of edges: horizontal (right / left) or vertical (down / up)
                /* UNDEFINED, RIGHT, LEFT, DOWN, UP */
                edgeRouting: 'ORTHOGONAL', // Defines how edges are routed (POLYLINE, ORTHOGONAL, SPLINES)
                edgeSpacingFactor: 1.5, // Factor by which the object spacing is multiplied to arrive at the minimal spacing between edges.
                feedbackEdges: false, // Whether feedback edges should be highlighted by routing around the nodes.
                fixedAlignment: 'BALANCED', // Tells the BK node placer to use a certain alignment instead of taking the optimal result.  This option should usually be left alone.
                /* NONE Chooses the smallest layout from the four possible candidates.
                LEFTUP Chooses the left-up candidate from the four possible candidates.
                RIGHTUP Chooses the right-up candidate from the four possible candidates.
                LEFTDOWN Chooses the left-down candidate from the four possible candidates.
                RIGHTDOWN Chooses the right-down candidate from the four possible candidates.
                BALANCED Creates a balanced layout from the four possible candidates. */
                inLayerSpacingFactor: 5.0, // Factor by which the usual spacing is multiplied to determine the in-layer spacing between objects.
                layoutHierarchy: true, // Whether the selected layouter should consider the full hierarchy
                linearSegmentsDeflectionDampening: 0.3, // Dampens the movement of nodes to keep the diagram from getting too large.
                mergeEdges: false, // Edges that have no ports are merged so they touch the connected nodes at the same points.
                mergeHierarchyCrossingEdges: true, // If hierarchical layout is active, hierarchy-crossing edges use as few hierarchical ports as possible.
                nodeLayering: 'INTERACTIVE', // Strategy for node layering.
                nodePlacement: 'BRANDES_KOEPF', // Strategy for Node Placement
                /* BRANDES_KOEPF Minimizes the number of edge bends at the expense of diagram size: diagrams drawn with this algorithm are usually higher than diagrams drawn with other algorithms.
                LINEAR_SEGMENTS Computes a balanced placement.
                INTERACTIVE Tries to keep the preset y coordinates of nodes from the original layout. For dummy nodes, a guess is made to infer their coordinates. Requires the other interactive phase implementations to have run as well.
                SIMPLE Minimizes the area at the expense of... well, pretty much everything else. */
                randomizationSeed: 1, // Seed used for pseudo-random number generators to control the layout algorithm; 0 means a new seed is generated
                routeSelfLoopInside: false, // Whether a self-loop is routed around or inside its node.
                separateConnectedComponents: true, // Whether each connected component should be processed separately
                spacing: 20, // Overall setting for the minimal amount of space to be left between objects
                thoroughness: 25 // How much effort should be spent to produce a nice layout..
            }
        }
    });



    let defaults = {
        menuRadius: function (ele) { return 50; }, // the outer radius (node center to the end of the menu) in pixels. It is added to the rendered size of the node. Can either be a number or function as in the example.
        selector: 'node', // elements matching this Cytoscape.js selector will trigger cxtmenus
        commands: [ // an array of commands to list in the menu or a function that returns the array

            {
                fillColor: 'rgba(111, 0, 255, 0.85)', // optional: custom background color for item
                content: 'Space', // html/text content to be displayed in the menu
                contentStyle: {}, // css key:value pairs to set the command's css in js if you want
                select: function (ele) { // a function to execute when the command is selected
                    document.getElementById("activity_id").setAttribute("value", ele.id())
                    document.getElementById("see_space_graph").click();
                    var scatterDiv = document.getElementById("space_div")
                    scatterDiv.style.visibility = 'visible';
                },
                hover: function (ele) { // a function to execute when the command is hovered
                    console.log(ele.id()) // `ele` holds the reference to the active element
                },
                enabled: true // whether the command is selectable
            },
            {
                fillColor: 'rgba(200, 162, 200, 0.85)', // optional: custom background color for item
                content: 'Time', // html/text content to be displayed in the menu
                contentStyle: {}, // css key:value pairs to set the command's css in js if you want
                select: function (ele) { // a function to execute when the command is selected
                    console.log(ele.id()) // `ele` holds the reference to the active element
                },
                hover: function (ele) { // a function to execute when the command is hovered
                    console.log(ele.id()) // `ele` holds the reference to the active element
                },
                enabled: true // whether the command is selectable
            },
            {
                fillColor: 'rgba(153, 102, 255, 0.85)', // optional: custom background color for item
                content: 'Energy', // html/text content to be displayed in the menu
                contentStyle: {}, // css key:value pairs to set the command's css in js if you want
                select: function (ele) { // a function to execute when the command is selected
                    console.log(ele.id()) // `ele` holds the reference to the active element
                },
                hover: function (ele) { // a function to execute when the command is hovered
                    console.log(ele.id()) // `ele` holds the reference to the active element
                },
                enabled: true // whether the command is selectable
            },


        ],
        function(ele) { return [ /*...*/] }, // a function that returns commands or a promise of commands
        fillColor: 'rgba(0, 0, 0, 0.85)', // the background colour of the menu
        activeFillColor: 'rgba(0, 0, 0, 0.75)', // the colour used to indicate the selected command
        activePadding: 20, // additional size in pixels for the active command
        indicatorSize: 24, // the size in pixels of the pointer to the active command, will default to the node size if the node size is smaller than the indicator size, 
        separatorWidth: 3, // the empty spacing in pixels between successive commands
        spotlightPadding: 2, // extra spacing in pixels between the element and the spotlight
        adaptativeNodeSpotlightRadius: true, // specify whether the spotlight radius should adapt to the node size
        openMenuEvents: 'cxttap', // space-separated cytoscape events that will open the menu; only `cxttapstart` and/or `taphold` work here
        itemColor: 'white', // the colour of text in the command's content
        itemTextShadowColor: 'transparent', // the text shadow colour of the command's content
        zIndex: 9999, // the z-index of the ui div
    };

    let menu = cy.cxtmenu(defaults);
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