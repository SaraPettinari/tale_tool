import os
import src.const as cn

from pandas import DataFrame

#PM4PY imports
import pm4py
from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.conversion.log import converter as xes_converter
from pm4py.statistics.attributes.log import get as attr_get
from pm4py.util import exec_utils
from pm4py.util import xes_constants as xes
from pm4py.visualization.dfg.variants.timeline import Parameters, get_min_max_value
from pm4py.objects.log.util import interval_lifecycle
###

ROOT_DIR = os.path.abspath(os.curdir)

def xes_to_df(log_path):
    log = xes_importer.apply(log_path)
    pd = xes_converter.apply(log, variant=xes_converter.Variants.TO_DATA_FRAME)
    return pd

def generate_color(activities_count):
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

def generate_performance_color(duration_dict):
    activities_color = {}
    
    min_value, max_value = get_min_max_value(duration_dict)
    


def create_dfg(file_path, filtering_conditions={}):
    log = xes_importer.apply(file_path)
    parameters_filter = {attributes_filter.Parameters.ATTRIBUTE_KEY: cn.LIFECYCLE}
    log_neg = attributes_filter.apply(log, ['start', 'complete'], parameters=parameters_filter)
    
    log = interval_lifecycle.to_interval(log_neg)

    # Check if there are some filtering conditions
    if len(filtering_conditions) > 0:
        for condition in filtering_conditions.keys():
            if not condition == cn.CASE:
                parameters_filter = {attributes_filter.Parameters.ATTRIBUTE_KEY: condition}
                condition_value = filtering_conditions[condition]
                traceattr = attributes_filter.apply(log, [condition_value],  parameters=parameters_filter)
            else:
                parameters_filter = {attributes_filter.Parameters.CASE_ID_KEY: condition}
                condition_value = str(filtering_conditions[condition])
                traceattr = attributes_filter.apply(log, [condition_value],  parameters=parameters_filter)
        
    dfg, start_activities, end_activities = pm4py.discovery.discover_dfg(
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
    nodes.append({'id': 'start_node', 'label': 'start', 'shape': 'diamond',
                 'size': 10, 'color': {'background': '#ADFF2F', 'border': "#ADFF2F"}})
    nodes.append({'id': 'end_node', 'label': 'end', 'shape': 'diamond',
                 'size': 10, 'color': {'background': '#ff6666', 'border': "#ff6666"}})
    for key in dfg:
        color = "#99ccff"
        node_1 = key[0]
        node_2 = key[1]
        if (node_1 in start_activities):
            # color = "#ADFF2F"
            count = start_activities[node_1]
            edges.append(
                {'from': 'start_node', 'to': node_1, 'label': count, 'dashes': True})
        if (node_1 in end_activities):
            # color = "#ff6666"
            count = end_activities[node_1]
            edges.append(
                {'from': node_1, 'to': 'end_node', 'label': count, 'dashes': True})
        if (not (node_1 in n_check)):
            n_check.add(node_1)
            nodes.append({'id': node_1, 'label': node_1, 'color': {
                'background': color}, 'count': activity_count[node_1]})
        # color = "#99ccff"
        if (node_2 in start_activities):
            # color = "#ADFF2F"
            count = start_activities[node_2]
            edges.append(
                {'from': 'start_node', 'to': node_2, 'label': count, 'dashes': True})
        if (node_2 in end_activities):
            # color = "#ff6666"
            count = end_activities[node_2]
            edges.append(
                {'from': node_2, 'to': 'end_node', 'label': count, 'dashes': True})
        if (not (node_2 in n_check)):
            n_check.add(node_2)
            nodes.append({'id': node_2, 'label': node_2, 'color': {
                'background': color}, 'count': activity_count[node_2]})

        edges.append({'from': node_1, 'to': node_2, 'label': str(dfg[key])})

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
    colors = generate_color(activity_count)  # for location graph
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


def create_performance_dfg(file_path):
    log = xes_importer.apply(file_path)
    activity_duration = get_activity_duration(log)
    # generate_heatmap_data(file_path)
    log = interval_lifecycle.to_interval(log)
    dfg, start_activities, end_activities = pm4py.discovery.discover_performance_dfg(log)
    
    nodes = []
    n_check = set()
    edges = []
    id0 = 0
    id1 = 0
    colors = generate_color(activity_duration)
    for key in dfg:
        if (key[0] in start_activities):
            color = "#ADFF2F"
            count = 'instant'
            edges.append(
                {'from': 'start_node', 'to': key[0], 'label': count, 'dashes': True})
        color = "#000000"
        if (not (key[0] in n_check)):
            n_check.add(key[0])
            color = colors[key[0]]
            nodes.append({'id': key[0], 'label': key[0], 'color': {
                'background': color}, 'count': activity_duration[key[0]]})
        color = "#cc99ff"
        if (key[1] in end_activities):
            color = "#ff6666"
            count = 'instant'
            edges.append(
                {'from': key[1], 'to': 'end_node', 'label': count, 'dashes': True})
        if (not (key[1] in n_check)):
            n_check.add(key[1])
            color = colors[key[1]]
            nodes.append({'id': key[1], 'label': key[1], 'color': {
                'background': color}, 'count': activity_duration[key[1]]})

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


def get_file_path(file_name):
    try:
        file_path = os.path.join(ROOT_DIR, 'docs', 'logs', file_name)
        return file_path
    except:
        print("File path error")
        
        
        
def get_activity_duration(log):
    activity_durations = []

    for trace in log:
    # Dictionary to store start times for each activity
        start_times = {}
        
        for event in trace:
            activity = event[cn.ACTIVITY]
            lifecycle = event[cn.LIFECYCLE]
            timestamp = event[cn.TIMESTAMP]
            
            # Check if it's a start or complete event
            if lifecycle == 'start':
                start_times[activity] = timestamp
            elif lifecycle == 'complete' and activity in start_times:
                duration = timestamp - start_times[activity]
                activity_durations.append({
                    'trace_id': trace.attributes['concept:name'],
                    'activity': activity,
                    'duration': duration.total_seconds()  # Convert to seconds
                })
                del start_times[activity]

    durations_df = DataFrame(activity_durations)
    durations_df = zip(durations_df, durations_df.median(durations_df['duration']))
    return durations_df

