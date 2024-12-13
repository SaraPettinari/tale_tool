import os
import src.const as cn

from pandas import DataFrame

#PM4PY imports
import pm4py
from pm4py.algo.filtering.log.attributes import attributes_filter
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.objects.conversion.log import converter as xes_converter
from pm4py.statistics.attributes.log import get as attr_get
from pm4py.util import exec_utils
from pm4py.util import xes_constants as xes
from pm4py.visualization.dfg.variants.timeline import Parameters, get_min_max_value
from pm4py.objects.log.util import interval_lifecycle
###

ROOT_DIR = os.path.abspath(os.curdir)


def xes_to_df(log_path):
    '''
    XES to DataFrame Converter function
    
        Parameters
        ----------
        * log_path: input path of the event log
        
        Returns
        -------
        * returns the log as a dataframe
    '''
    log = xes_importer.apply(log_path)
    pd = xes_converter.apply(log, variant=xes_converter.Variants.TO_DATA_FRAME)
    return pd
 

def create_generalized_dfg(file_path, is_performance=False):
    '''
        Generate a Directly-Follows Graph (DFG)

            Parameters
            ----------
            * file_path : Path to the event log file
            * filtering_conditions : Filters selected by the user. Defaults to an empty dictionary
            * is_performance : Whether to generate a performance DFG. Defaults to False

            Returns
            -------
            A tuple containing:
                * nodes (list): A collection of nodes in the graph
                * edges (list): A collection of edges in the graph
    '''
    log = xes_importer.apply(file_path)
    

    # Discover the requested DFG
    if is_performance:
        activity_stats = get_activity_duration(log)
        # Convert to interval lifecycle if needed
        log = interval_lifecycle.to_interval(log)
        dfg, start_activities, end_activities = pm4py.discovery.discover_performance_dfg(log)
        
    else:
        # Convert to interval lifecycle if needed
        log = interval_lifecycle.to_interval(log)
        dfg, start_activities, end_activities = pm4py.discovery.discover_dfg(log)
        activity_stats = attr_get.get_attribute_values(
            log, exec_utils.get_param_value(Parameters.ACTIVITY_KEY, {}, xes.DEFAULT_NAME_KEY)
        )

    # Add start and end nodes
    nodes = [
        {'id': 'start_node', 'label': 'start', 'shape': 'diamond',
         'size': 10, 'color': {'background': '#ADFF2F', 'border': "#ADFF2F"}},
        {'id': 'end_node', 'label': 'end', 'shape': 'diamond',
         'size': 10, 'color': {'background': '#ff6666', 'border': "#ff6666"}}
    ]
    edges = []
    n_check = set()

    # Generate colors based on activity counts
    colors = generate_color(activity_stats, is_performance=is_performance)

    for (node_1, node_2), dfg_data in dfg.items():
        # Append start and end activities
        if node_1 in start_activities:
            edges.append({'from': 'start_node', 'to': node_1, 'label': start_activities[node_1], 'dashes': True})
        if node_2 in end_activities:
            edges.append({'from': node_2, 'to': 'end_node', 'label': end_activities[node_2], 'dashes': True})

        # Add nodes if not already added
        for node in [node_1, node_2]:
            if node not in n_check:
                n_check.add(node)
                color = colors[node]
                label = f"{activity_stats[node]}s" if is_performance else activity_stats[node]
                nodes.append({'id': node, 'label': node, 'color': {'background': color}, 'count': label})

        # Add edges
        if is_performance:
            mean_sec = round(dfg_data['mean'], 2)
            label = f"{mean_sec}s" if mean_sec > 0 else 'instant'
            edges.append({'from': node_1, 'to': node_2, 'label': label, 'width': mean_sec / 20})
        else:
            edges.append({'from': node_1, 'to': node_2, 'label': str(dfg_data)})

    return nodes, edges



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
    
    median_durations = durations_df.groupby('activity')['duration'].median()
    median_durations_dict = median_durations.to_dict() 
    
    return median_durations_dict


## Color generation
def hex_to_rgb(hex_color):
    """Convert a hexadecimal color to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        raise ValueError("Input #" + hex_color + " is not a valid hexadecimal color.")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    """Convert an RGB tuple to a hexadecimal color."""
    return '#' + ''.join(f'{value:02x}' for value in rgb)

def interpolate_color(color1, color2, scale_value, scale_max):
    """Interpolate between two colors based on scale_value and scale_max."""
    if not (0 <= scale_value <= scale_max):
        raise ValueError("Scale value must be between 0 and scale_max.")

    # Convert colors to RGB
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)

    # Interpolate each channel
    interpolated_rgb = tuple(
        round(rgb1[i] + (rgb2[i] - rgb1[i]) * (scale_value / scale_max))
        for i in range(3)
    )

    # Convert back to hexadecimal
    return rgb_to_hex(interpolated_rgb)


def generate_color(activities_count, is_performance : False):
    '''
    Color generation function to assign a color based on the activity weight
    
        Parameters
        ----------
        * activities_count: dictionary of activities and related weights
        * is_performance : Whether to generate a performance DFG. Defaults to False

        Returns
        -------
        * returns a dictionary associating a color to an activity
    '''
    activities_color = {}

    min_value, max_value = get_min_max_value(activities_count)
    
    if is_performance:
        color1 = '#ffdfd8'
        color2 = '#dc3613'
    else:
        color1 = '#d8f1ff'
        color2 = '#52a6fa'
    

    for ac in activities_count:
        v0 = activities_count[ac]
        v1 = interpolate_color(color1, color2, v0, max_value)
    
        activities_color[ac] = v1

    return activities_color

def get_resources(file_path):
    log = xes_importer.apply(file_path)
    log = interval_lifecycle.to_interval(log)
    resources = pm4py.get_event_attribute_values(log, "org:resource")
    return resources


def store_filtered_log(file_path, conditions: dict):
    """
    Stores a filtered log in a 'filters' subfolder, appending condition information to the file name.

    Parameters
    ----------
        file_path (str): Path to the original file.
        conditions (dict): Dictionary of conditions to append to the file name.
    """
    
    log = xes_importer.apply(file_path)
    
    parameters_filter = {}

    for condition, condition_value in conditions.items():
        temp_log = log

        # If the condition is based on the CASE_ID
        if condition == cn.CASE:
            parameters_filter = {
                attributes_filter.Parameters.CASE_ID_KEY: condition, 
                attributes_filter.Parameters.POSITIVE : True}
            condition_value = str(condition_value)
            traceattr = attributes_filter.apply_trace_attribute(
                temp_log, [condition_value], parameters=parameters_filter
            )
        else:
            parameters_filter = {
                attributes_filter.Parameters.ATTRIBUTE_KEY: condition, 
                attributes_filter.Parameters.POSITIVE : True}
            traceattr = attributes_filter.apply_events(
                temp_log, [condition_value], parameters=parameters_filter
            )
        
        log = traceattr

        
        
    condition_name = ''.join([f'_{key}_{value}' for key, value in conditions.items()])
    
    folder_path = os.path.join(os.path.dirname(file_path), 'filters')
    os.makedirs(folder_path, exist_ok=True)  
    
    file_name, file_extension = os.path.splitext(os.path.basename(file_path))
    outfile = f"{file_name}{condition_name}{file_extension}" 
    
    outpath = os.path.join(folder_path, outfile)
    
    xes_exporter.apply(traceattr, outpath)

    print(f"Filtered log saved to: {outpath}")
    
    return outpath


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
    colors = generate_color(activity_count, is_performance=False)
    for key in dfg:
        color = "#99ccff"
        node_1 = key[0]
        node_2 = key[1]
        if (node_1 in start_activities):
            count = start_activities[node_1]
            edges.append(
                {'from': 'start_node', 'to': node_1, 'label': count, 'dashes': True})
        if (node_1 in end_activities):
            count = end_activities[node_1]
            edges.append(
                {'from': node_1, 'to': 'end_node', 'label': count, 'dashes': True})
        if (not (node_1 in n_check)):
            n_check.add(node_1)
            color = colors[node_1]
            nodes.append({'id': node_1, 'label': node_1, 'color': {
                'background': color}, 'count': activity_count[node_1]})
        if (node_2 in start_activities):
            count = start_activities[node_2]
            edges.append(
                {'from': 'start_node', 'to': node_2, 'label': count, 'dashes': True})
        if (node_2 in end_activities):
            count = end_activities[node_2]
            edges.append(
                {'from': node_2, 'to': 'end_node', 'label': count, 'dashes': True})
        if (not (node_2 in n_check)):
            n_check.add(node_2)
            color = colors[node_2]
            nodes.append({'id': node_2, 'label': node_2, 'color': {
                'background': color}, 'count': activity_count[node_2]})

        edges.append({'from': node_1, 'to': node_2, 'label': str(dfg[key])})

        id0 = id0 + 1
        id1 = id1 + 1

    return (nodes, edges)




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
    nodes.append({'id': 'start_node', 'label': 'start', 'shape': 'diamond',
                 'size': 10, 'color': {'background': '#ADFF2F', 'border': "#ADFF2F"}})
    nodes.append({'id': 'end_node', 'label': 'end', 'shape': 'diamond',
                 'size': 10, 'color': {'background': '#ff6666', 'border': "#ff6666"}})
    colors = generate_color(activity_duration, is_performance=True)
    for key in dfg:
        if (key[0] in start_activities):
            count = 'instant'
            edges.append(
                {'from': 'start_node', 'to': key[0], 'label': count, 'dashes': True})
        if (not (key[0] in n_check)):
            n_check.add(key[0])
            color = colors[key[0]]
            nodes.append({'id': key[0], 'label': key[0], 'color': {
                'background': color}, 'count': str(activity_duration[key[0]]) + 's'})
        if (key[1] in end_activities):
            count = 'instant'
            edges.append(
                {'from': key[1], 'to': 'end_node', 'label': count, 'dashes': True})
        if (not (key[1] in n_check)):
            n_check.add(key[1])
            color = colors[key[1]]
            nodes.append({'id': key[1], 'label': key[1], 'color': {
                'background': color}, 'count': str(activity_duration[key[1]]) + 's'})

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

