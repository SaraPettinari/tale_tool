import sys

import json
import os
import webview
import webbrowser
from functools import wraps

from flask import Flask, render_template, jsonify, request, flash


import pm4py
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.statistics.attributes.log import get as attr_get
from pm4py.util import exec_utils
from pm4py.util import xes_constants as xes
from pm4py.visualization.dfg.parameters import Parameters
from pm4py.visualization.dfg.variants.frequency import get_activities_color, get_min_max_value
from pm4py.objects.log.util import interval_lifecycle
from pm4py.algo.transformation.log_to_features import algorithm as log_to_features

import xml.etree.ElementTree as ET
from pandas import DataFrame
import plotly.express as px
import pandas as pd

from src.xes_handler import merge_xes, csv_to_xes
from collections import Counter


server = Flask(__name__)
server.config['SEND_FILE_MAX_AGE_DEFAULT'] = 1  # disable caching

files_dict = {}
heatmap_data = {}
resp_list = []
resources_list = []

data_dict = {}


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

    return render_template('index.html', files=resp_list, fdata=data_dict[f.filename])


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

    return render_template('index.html', files=resp_list, file_name=file_name, fdata=data_dict[file_name])


@server.route('/discover/activity', methods=['GET', 'POST'])
def discover_dfg():
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

        return render_template('index.html', files=resp_list, file_name=file_name, fdata=data_dict[file_name],
                               resource_opt=res_opt, case_opt=int(case_opt), response_data={'nodes': nodes, 'edges': edges})

    elif request.method == 'POST':
        file_name = request.form['file_name']
        file_path = os.path.join(server.root_path, 'docs', 'logs', file_name)

        (nodes, edges) = create_dfg(file_path)

        return render_template('index.html', files=resp_list, fdata=data_dict[file_name],
                               response_data={'nodes': nodes, 'edges': edges})


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


@server.route('/discover/all/performance', methods=['POST'])
def discover_all_p():
    data = json.loads(request.data)
    data.pop('token')
    file_path = merge_xes(data)
    key = 20
    files_dict[key] = file_path

    (nodes, edges) = create_performance(file_path)
    return jsonify({'nodes': nodes, 'edges': edges, 'file_key': key})


def log_to_dataframe(log_path):
    x = []
    y = []
    z = []
    lables = []
    cases = []
    times = []
    resource = []
    location_activity = []
    tree = ET.parse(log_path)
    root = tree.getroot()
    case = 0
    for trace in root.iter('trace'):
        case += 1
        for child in trace.iter('event'):
            for el in child:
                if el.attrib['key'] == 'x':
                    x.append(el.attrib['value'])
                elif el.attrib['key'] == 'y':
                    y.append(el.attrib['value'])
                elif el.attrib['key'] == 'z':
                    z.append(el.attrib['value'])
                elif el.attrib['key'] == 'concept:name':
                    lables.append(el.attrib['value'])
                    cases.append(case)
                elif el.attrib['key'] == 'time:timestamp':
                    times.append(el.attrib['value'])
                elif el.attrib['key'] == 'org:resource':
                    resource.append(el.attrib['value'])
                elif el.attrib['key'] == 'activity':
                    location_activity.append(el.attrib['value'])

    df = DataFrame({
        'x': x, 'y': y, 'z': z, 'activity': lables, 'case': cases, 'timestamp': times})

    if len(resource) > 0:
        df['resource'] = resource
    if len(location_activity) > 0:
        df['location_activity'] = location_activity

    # change column types
    df[df.columns[0:3]] = df.iloc[:, 0:3].astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['case'] = df['case'].astype(int)

    return df


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


@server.route('/show/heatmap', methods=['POST'])
def create_heatmap():
    data = json.loads(request.data)
    activity = data.get('activity')
    if (activity in heatmap_data):
        print(1)
    response = {'status': 'ok', 'data': heatmap_data[activity]}
    return jsonify(response)


def generate_heatmap_data(log_path):
    tree = ET.parse(log_path)
    root = tree.getroot()
    act_points = {}
    min_x = sys.float_info.max
    max_x = -sys.float_info.max
    min_y = sys.float_info.max
    max_y = -sys.float_info.max
    min_z = sys.float_info.max
    max_z = -sys.float_info.max

    for trace in root.iter('trace'):
        for child in trace.iter('event'):
            x = 0
            y = 0
            z = 0
            name = ""
            for el in child:
                if el.attrib['key'] == 'x':
                    x = float(el.attrib['value'])
                elif el.attrib['key'] == 'y':
                    y = float(el.attrib['value'])
                elif el.attrib['key'] == 'z':
                    z = float(el.attrib['value'])
                elif el.attrib['key'] == 'concept:name':
                    name = el.attrib['value']
            if (x > max_x):
                max_x = x
            elif (x < min_x):
                min_x = x
            if (y > max_y):
                max_y = y
            elif (y < min_y):
                min_y = y
            if (z > max_z):
                max_z = z
            elif (z < min_z):
                min_z = z
            if(not (name in act_points)):
                act_points[name] = []
            act_points[name].append([x, y, z])
    x_scale = (max_x-min_x)/10
    y_scale = (max_y-min_y)/10
    x_legend = [(2*min_x+x_scale)/2, (2*min_x+3*x_scale)/2, (2*min_x+5*x_scale)/2, (2*min_x+7*x_scale)/2, (2*min_x+9*x_scale)/2,
                (2*min_x+11*x_scale)/2, (2*min_x+13*x_scale)/2, (2*min_x+15*x_scale)/2, (2*min_x+17*x_scale)/2, (2*min_x+19*x_scale)/2]
    y_legend = [(2*min_y+y_scale)/2, (2*min_y+3*y_scale)/2, (2*min_y+5*y_scale)/2, (2*min_y+7*y_scale)/2, (2*min_y+9*y_scale)/2,
                (2*min_y+11*y_scale)/2, (2*min_y+13*y_scale)/2, (2*min_y+15*y_scale)/2, (2*min_y+17*y_scale)/2, (2*min_y+19*y_scale)/2]

    for name in act_points:
        heatmap_data[name] = {}
        data = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]
        for point in act_points[name]:
            id_x = int((float(point[0])-min_x)//x_scale)
            id_y = int((float(point[1])-min_y)//y_scale)
            if(id_x == 10):
                id_x = 9
            if(id_y == 10):
                id_y = 9
            data[id_x][id_y] = data[id_x][id_y] + 1
        heatmap_data[name] = {'x': x_legend, 'y': y_legend, 'z': data}


def test(activities_count):
    activities_color = {}

    min_value, max_value = get_min_max_value(activities_count)

    for ac in activities_count:
        v0 = activities_count[ac]
        """transBaseColor = int(
            255 - 100 * (v0 - min_value) / (max_value - min_value + 0.00001))
        transBaseColorHex = str(hex(transBaseColor))[2:].upper()
        v1 = "#" + transBaseColorHex + transBaseColorHex + "FF"""

        trans_base_color = int(
            255 - 100*(v0 - min_value) / (max_value - min_value + 0.00001))
        trans_base_color_hex = str(hex(trans_base_color))[2:].upper()
        v1 = "#" + trans_base_color_hex + trans_base_color_hex + "FF"

        activities_color[ac] = v1

    return activities_color


def create_dfg_v2(file_path, resource=''):
    log = xes_importer.apply(file_path)
    log_neg = pm4py.filter_event_attribute_values(
        log, "lifecycle:transition", ["inprogress"], level="event", retain=False)

    log = interval_lifecycle.to_interval(log_neg)

    if resource != '':
        tracefilter = pm4py.filter_event_attribute_values(
            log, "org:resource", resource, level="event", retain=True)
        dfg, start_activities, end_activities = pm4py.discover_directly_follows_graph(
            tracefilter)
    else:
        dfg, start_activities, end_activities = pm4py.discover_directly_follows_graph(
            log)
    activity_key = exec_utils.get_param_value(
        Parameters.ACTIVITY_KEY, {}, xes.DEFAULT_NAME_KEY)
    activity_count = attr_get.get_attribute_values(
        log, activity_key, parameters={})
    nodes = []
    n_check = set()
    edges = []
    id0 = 0
    id1 = 0
    nodes.append('start_node')
    nodes.append('end_node')
    for key in dfg:
        color = "#99ccff"
        if (key[0] in start_activities):
            # color = "#ADFF2F"
            edges.append(('start_node', key[0]))
        if (key[0] in end_activities):
            # color = "#ff6666"
            edges.append((key[0], 'end_node'))
        if (not (key[0] in n_check)):
            n_check.add(key[0])
            nodes.append(key[0])
        # color = "#99ccff"
        if (key[1] in start_activities):
            # color = "#ADFF2F"
            edges.append(('start_node', key[1]))
        if (key[1] in end_activities):
            # color = "#ff6666"
            edges.append((key[1], 'end_node'))
        if (not (key[1] in n_check)):
            n_check.add(key[1])
            nodes.append(key[1])

        edges.append((key[0], key[1]))

        id0 = id0 + 1
        id1 = id1 + 1

    return (nodes, edges)


def create_dfg(file_path, filtering_conditions={}):
    log = xes_importer.apply(file_path)
    log_neg = pm4py.filter_event_attribute_values(
        log, "lifecycle:transition", ["inprogress"], level="event", retain=False)

    log = interval_lifecycle.to_interval(log_neg)

    if len(filtering_conditions) > 0:
        for condition in filtering_conditions.keys():
            tracefilter = pm4py.filter_event_attribute_values(
                log, condition, filtering_conditions[condition], level="event", retain=True)
        dfg, start_activities, end_activities = pm4py.discover_directly_follows_graph(
            tracefilter)
    else:
        dfg, start_activities, end_activities = pm4py.discover_directly_follows_graph(
            log)
    activity_key = exec_utils.get_param_value(
        Parameters.ACTIVITY_KEY, {}, xes.DEFAULT_NAME_KEY)
    activity_count = attr_get.get_attribute_values(
        log, activity_key, parameters={})
    nodes = []
    n_check = set()
    edges = []
    id0 = 0
    id1 = 0
    nodes.append({'id': 'start_node', 'label': 'start', 'shape': 'triangleDown',
                 'size': 10, 'color': {'background': '#ADFF2F', 'border': "#ADFF2F"}})
    nodes.append({'id': 'end_node', 'label': 'end', 'shape': 'hexagon',
                 'size': 10, 'color': {'background': '#ff6666', 'border': "#ff6666"}})
    for key in dfg:
        color = "#99ccff"
        if (key[0] in start_activities):
            # color = "#ADFF2F"
            edges.append(
                {'from': 'start_node', 'to': key[0], 'label': 0, 'dashes': True})
        if (key[0] in end_activities):
            # color = "#ff6666"
            edges.append(
                {'from': key[0], 'to': 'end_node', 'label': 0, 'dashes': True})
        if (not (key[0] in n_check)):
            n_check.add(key[0])
            nodes.append({'id': key[0], 'label': key[0], 'color': {
                'background': color}, 'count': activity_count[key[0]]})
        # color = "#99ccff"
        if (key[1] in start_activities):
            # color = "#ADFF2F"
            edges.append(
                {'from': 'start_node', 'to': key[1], 'label': 0, 'dashes': True})
        if (key[1] in end_activities):
            # color = "#ff6666"
            edges.append(
                {'from': key[1], 'to': 'end_node', 'label': 0, 'dashes': True})
        if (not (key[1] in n_check)):
            n_check.add(key[1])
            nodes.append({'id': key[1], 'label': key[1], 'color': {
                'background': color}, 'count': activity_count[key[1]]})

        edges.append({'from': key[0], 'to': key[1], 'label': str(dfg[key])})

        id0 = id0 + 1
        id1 = id1 + 1

    return (nodes, edges)


def create_dist_dfg(file_path, location_graph=False):
    log = xes_importer.apply(file_path)
    # generate_heatmap_data(file_path)
    log = interval_lifecycle.to_interval(log)
    # Filter drone resources
    resources = pm4py.get_event_attribute_values(log, "org:resource")
    dict_kres = dict()
    dict_start = dict()
    dict_end = dict()

    for res in resources:
        tracefilter = pm4py.filter_event_attribute_values(
            log, "org:resource", res, level="event", retain=True)
        dfg, start, end = pm4py.discover_directly_follows_graph(tracefilter)
        dict_kres.update(dfg)
        dict_start.update(start)
        dict_end.update(end)

    activity_key = exec_utils.get_param_value(
        Parameters.ACTIVITY_KEY, {}, xes.DEFAULT_NAME_KEY)
    activity_count = attr_get.get_attribute_values(
        log, activity_key, parameters={})
    nodes = []
    n_check = set()
    edges = []
    colors = test(activity_count)  # for location graph
    for key in dict_kres:
        # if we it is an activity graph
        if not location_graph:
            color = "#1E90FF"
            if (key[0] in dict_start):
                color = "#ADFF2F"
            if (key[0] in dict_end):
                color = "#FF0000"
            if (not (key[0] in n_check)):
                n_check.add(key[0])
                nodes.append({'id': key[0], 'label': key[0], 'color': {
                    'background': color}, 'count': activity_count[key[0]]})
            # check key 1
            color = "#1E90FF"
            if (key[1] in dict_start):
                color = "#ADFF2F"
            if (key[1] in dict_end):
                color = "#FF0000"
            if (not (key[1] in n_check)):
                n_check.add(key[1])
                nodes.append({'id': key[1], 'label': key[1], 'color': {
                    'background': color}, 'count': activity_count[key[1]]})
        # if we it is a location graph
        else:
            if (not (key[0] in n_check)):
                n_check.add(key[0])
                nodes.append({'id': key[0], 'label': key[0], 'color': {
                    'background': colors[key[0]]}, 'count': activity_count[key[0]]})
            if (not (key[1] in n_check)):
                n_check.add(key[1])
                nodes.append({'id': key[1], 'label': key[1], 'color': {
                    'background': colors[key[1]]}, 'count': activity_count[key[1]]})

        edges.append({'from': key[0], 'to': key[1],
                     'label': str(dict_kres[key])})

    return (nodes, edges)


def get_resources(file_path):
    log = xes_importer.apply(file_path)
    log = interval_lifecycle.to_interval(log)
    resources = pm4py.get_event_attribute_values(log, "org:resource")
    return resources


def create_performance(file_path, location_graph=False):
    log = xes_importer.apply(file_path)
    # generate_heatmap_data(file_path)
    log = interval_lifecycle.to_interval(log)
    dfg, start_activities, end_activities = pm4py.discover_performance_dfg(log)
    activity_key = exec_utils.get_param_value(
        Parameters.ACTIVITY_KEY, {}, xes.DEFAULT_NAME_KEY)
    activity_count = attr_get.get_attribute_values(
        log, activity_key, parameters={})
    nodes = []
    n_check = set()
    edges = []
    id0 = 0
    id1 = 0
    colors = test(activity_count)
    for key in dfg:
        if not location_graph:
            color = "#000000"
            if (key[0] in start_activities):
                color = "#ADFF2F"
            if (key[0] in end_activities):
                color = "#FF0000"
            if (not (key[0] in n_check)):
                n_check.add(key[0])
                nodes.append({'id': key[0], 'label': key[0], 'color': {
                    'background': color}, 'count': activity_count[key[0]]})
            color = "#cc99ff"
            if (key[1] in start_activities):
                color = "#ADFF2F"
            if (key[1] in end_activities):
                color = "#FF0000"
            if (not (key[1] in n_check)):
                n_check.add(key[1])
                nodes.append({'id': key[1], 'label': key[1], 'color': {
                    'background': color}, 'count': activity_count[key[1]]})
        else:
            if (not (key[0] in n_check)):
                n_check.add(key[0])
                nodes.append({'id': key[0], 'label': key[0], 'color': {
                    'background': colors[key[0]]}, 'count': activity_count[key[0]]})
            if (not (key[1] in n_check)):
                n_check.add(key[1])
                nodes.append({'id': key[1], 'label': key[1], 'color': {
                    'background': colors[key[1]]}, 'count': activity_count[key[1]]})

        mean_sec = round(dfg[key]['mean'], 2)

        if mean_sec > 100:
            mean_sec = 100
        if mean_sec <= 0:
            mean = 'instant'
        else:
            mean = str(mean_sec) + ' s'

        edges.append({'from': key[0], 'to': key[1],
                     'label': mean, 'width': mean_sec/20})

        id0 = id0 + 1
        id1 = id1 + 1

    return (nodes, edges)


@server.route('/discover/performance', methods=['POST'])
def discover_performance():
    data = json.loads(request.data)
    file_key = data.get('key')
    file_path = files_dict[file_key]

    (nodes, edges) = create_performance(file_path)

    return jsonify({'nodes': nodes, 'edges': edges, 'file_key': file_key})


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
