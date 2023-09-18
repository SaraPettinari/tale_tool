
import json
import os
import webview
import webbrowser
import plotly.express as px

from flask import Flask, render_template, jsonify, request, Response, session
from collections import Counter

from src.xes_handler import merge_xes, csv_to_xes
from src.utils import log_to_dataframe, create_dfg


server = Flask(__name__)
server.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1  # disable caching
server.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
server.config['SECRET_KEY'] = os.urandom(24)


files_dict = {}
resp_list = []
resources_list = []

data_dict = {}
file_name = None


@server.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response


@server.route('/')
def landing():
    """
    Render index.html. Initialization is performed asynchronously in initialize() function
    """
    return render_template('index.html')



@server.route('/csv_processing')
def csv_processing():
    return render_template('csv_parser.html')


@server.route('/select/logs', methods=['POST'])
def choose_path():
    files_list = request.files.getlist('file')
    for f in files_list:
        if f.filename.endswith('xes'):
            f.save(os.path.join(server.root_path, 'docs', 'logs', f.filename))
            resp_list.append(f.filename)

        data_dict[f.filename] = {}
        
    session['files'] = resp_list
    session['fdata'] = data_dict[f.filename]

    return render_template('index.html')


@server.route('/filter', methods=['POST'])
def get_resources():
    file_name = request.form['file_name']
    file_path = os.path.join(server.root_path, 'docs', 'logs', file_name)
    df = log_to_dataframe(file_path)

    resources_list = []
    cases_list = []

    if 'resource' in df.keys():
        resources = df["resource"].unique()
        resources_list = list(resources.tolist())

    if 'case' in df.keys():
        cases = df['case'].unique()
        cases_list = list(cases.tolist())

    data_dict[file_name] = {
        'resources': resources_list, 'cases': cases_list}

    session['fdata'] = data_dict[file_name]
    session['file_name'] = file_name
    
    return render_template('index.html')


@server.route('/discover/activity', methods=['GET', 'POST'])
def discover_dfg():
    global file_name
    if request.method == 'GET':
        res_opt = request.args.get('resource_option')
        case_opt = request.args.get('case_option')
        file_name = request.args.get('file_name')
        file_path = os.path.join(server.root_path, 'docs', 'logs', file_name)

        if(res_opt == 'none' and case_opt == 'none'):
            filtering_conditions = {}
        else:
            filtering_conditions = {'org:resource': res_opt}

        (nodes, edges) = create_dfg(file_path,
                                    filtering_conditions)
        
        session['resource_opt'] = res_opt
        session['case_opt'] = int(case_opt)
        session['response_data'] = {'nodes': nodes, 'edges': edges}

        return render_template('index.html')

    elif request.method == 'POST':
        file_name = request.form['file_name']
        file_path = os.path.join(server.root_path, 'docs', 'logs', file_name)

        (nodes, edges) = create_dfg(file_path)
        session['response_data'] = {'nodes': nodes, 'edges': edges}
        

        return render_template('index.html')


@server.route('/csv/parse', methods=['POST'])
def parse_csv():
    file_types = ('CSV Files (*.csv)', 'All files (*.*)')
    files = webview.windows[0].create_file_dialog(
        webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
    if len(files) > 0:
        file_path = files[0]
        dest_name = csv_to_xes(file_path)
        response = {'saved_as': dest_name}
        return jsonify(response)
    else:
        return jsonify({})


@server.route('/discover/all', methods=['POST'])
def discover_all():
    data = json.loads(request.data)
    data.pop('token')
    file_path = merge_xes(data)
    key = 20
    files_dict[key] = file_path

    (nodes, edges) = create_dfg(file_path)
    return jsonify({'nodes': nodes, 'edges': edges, 'file_key': key})



@server.route('/view/activity/space', methods=['POST'])
def see_activity_space():
    activity_name = request.form['activity_id']
    file_path = os.path.join(server.root_path, 'docs', 'logs', file_name)
    df = log_to_dataframe(file_path)
    filtered_df = df[df['activity'] == activity_name]

    fig = px.scatter_3d(filtered_df, x='x', y='y', z='z',
                        color='case',
                        symbol='activity',
                        title="Space for: " + activity_name,
                        range_x=[0, 10],
                        range_y=[0, 10],
                        range_z=[0, 2],
                        )

    fig.update_layout(scene=dict(
        yaxis=dict(
            backgroundcolor="rgb(227, 227, 250)",
            gridcolor="white",
            showbackground=True,
            zerolinecolor="white"),
        zaxis=dict(
            backgroundcolor="rgb(227, 227, 227)",
            gridcolor="white",
            showbackground=True,
            zerolinecolor="white",),),
    )

    out_file = "space_plot.html"
    fig_path = os.getcwd() + "/templates/" + out_file
    fig.write_html(fig_path)
    
    session['space_file'] = out_file
    
    #return Response(status=204)
    return render_template('index.html')


@server.route('/view/3Dscatter', methods=['POST'])
def create_scatter3D():
    data = json.loads(request.data)
    file_key = data.get('key')
    filter = data.get('filter')

    file_path = files_dict[file_key]
    df = log_to_dataframe(file_path)

    if case_check:
        filtered_df = df[df['case'] == int(case_select)]
        fig = px.scatter_3d(filtered_df, x='x', y='y', z='z',
                            color=filter,
                            symbol='activity',
                            title="3D Space Activity",
                            range_x=[0, 10],
                            range_y=[0, 10],
                            range_z=[0, 2],
                            )
    else:
        fig = px.scatter_3d(df, x='x', y='y', z='z',
                            color=filter,
                            symbol='activity',
                            title="3D Space Activity",
                            range_x=[0, 10],
                            range_y=[0, 10],
                            range_z=[0, 2],
                            # animation_frame='case',
                            )

    fig.update_layout(scene=dict(
        yaxis=dict(
            backgroundcolor="rgb(227, 227, 250)",
            gridcolor="white",
            showbackground=True,
            zerolinecolor="white"),
        zaxis=dict(
            backgroundcolor="rgb(227, 227, 227)",
            gridcolor="white",
            showbackground=True,
            zerolinecolor="white",),),
    )

    fig_path = os.getcwd() + "/templates/scatter3D.html"
    fig.write_html(fig_path)

    return jsonify({})


@server.route('/view/3Dscatter/all', methods=['POST'])
def create_scatter3D_all():
    file_key = 20
    file_path = files_dict[file_key]
    df = log_to_dataframe(file_path)

    fig = px.scatter_3d(df, x='x', y='y', z='z',
                        color='activity',
                        symbol='resource',
                        title="3D Space Activity",
                        range_x=[0, 10],
                        range_y=[0, 10],
                        range_z=[0, 2],
                        # animation_frame='case',
                        )

    fig_path = os.getcwd() + "/templates/scatter3D.html"
    fig.write_html(fig_path)

    return jsonify({})


@server.route('/show/area', methods=['POST'])
def create_plot_area():
    data = json.loads(request.data)

    file_key = data.get('key')
    current_location = data.get('location')

    file_path = files_dict[file_key]
    df = log_to_dataframe(file_path)

    filtered_data = df[df['activity'] == current_location]
    resp = json.loads(filtered_data.to_json())
    x = []
    y = []

    act = resp['location_activity']
    activity_counter = dict(Counter(list(act.values())))

    for el in activity_counter:
        x.append(el)
        y.append(activity_counter[el])

    response = {'x': x, 'y': y}
    return jsonify(response)


@server.route('/show/scatter2D', methods=['POST'])
def create_2dscatter():
    data = json.loads(request.data)

    file_key = data.get('key')
    activity = data.get('activity')

    file_path = files_dict[file_key]
    df = log_to_dataframe(file_path)

    filtered_data = df[df['activity'] == activity]
    resp = json.loads(filtered_data.to_json())
    x = []
    y = []
    for el in resp['x']:
        x.append(resp['x'][el])
    for el in resp['y']:
        y.append(resp['y'][el])
    response = {'x': x, 'y': y, 'activity': activity}
    return jsonify(response)

'''
@server.route('/discover/all/performance', methods=['POST'])
def discover_all_p():
    data = json.loads(request.data)
    data.pop('token')
    file_path = merge_xes(data)
    key = 20
    files_dict[key] = file_path

    (nodes, edges) = create_performance(file_path)
    return jsonify({'nodes': nodes, 'edges': edges, 'file_key': key})

@server.route('/discover/performance', methods=['POST'])
def discover_performance():
    data = json.loads(request.data)
    file_key = data.get('key')
    file_path = files_dict[file_key]

    (nodes, edges) = create_performance(file_path)

    return jsonify({'nodes': nodes, 'edges': edges, 'file_key': file_key})
'''

@server.route('/filter/resource', methods=['GET', 'POST'])
def filter_resource():
    global resource
    resource = request.form['resource_option']
    return jsonify(resource)


@server.route('/filter/case', methods=['GET', 'POST'])
def filter_cases():
    global case_select
    global case_check
    case_select = request.form['case_select']
    if case_select != 'all':
        case_check = True
    else:
        case_check = False
    return jsonify(resource)


@server.route('/case_filtering', methods=['GET', 'POST'])
def case_filtering():
    data = json.loads(request.data)
    file_key = data.get('key')
    file_path = files_dict[file_key]

    df = log_to_dataframe(file_path)

    cases = df['case'].unique()

    resp = list(cases.tolist())
    resp.append(file_key)

    return jsonify(resp)


@server.route('/discover/resource', methods=['POST'])
def discover_resource():
    data = json.loads(request.data)
    file_key = data.get('key')
    file_path = files_dict[file_key]

    (nodes, edges) = create_dfg(file_path, resource=resource)

    return jsonify({'nodes': nodes, 'edges': edges, 'file_key': file_key})


@server.route('/open-url', methods=['POST'])
def open_url():
    url = request.json['url']
    webbrowser.open_new_tab(url)

    return jsonify({})
