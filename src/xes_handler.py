import os
import pandas as pd
import xml.etree.ElementTree as ET
import pm4py
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.util import xes_constants


def csv_to_xes(path):
    name = path.split('\\')[-1].split('.')[0]
    data = pd.read_csv(path)

    cols = data.columns.values.tolist()

    remaps= {}

    for col in cols:
        if 'time' in col.lower():
            remaps[col] = xes_constants.DEFAULT_TIMESTAMP_KEY
        elif 'activity' in col.lower():
            remaps[col] = xes_constants.DEFAULT_NAME_KEY
        elif ('resource' or 'robot' or 'actor') in col.lower():
            remaps[col] = xes_constants.DEFAULT_RESOURCE_KEY
        elif 'lifecycle' in col.lower():
            remaps[col] = xes_constants.DEFAULT_TRANSITION_KEY
    data.rename(columns=remaps, inplace=True)
    
    log = pm4py.utils.format_dataframe(data, case_id='execution_id')

    data['time:timestamp'] = pd.to_datetime(data['time:timestamp'])
    data['concept:name'] = data['concept:name'].astype(str)

    data['state'] = data['state'].astype(str)
    data['msg_id'] = data['msg_id'].astype(str)
    data['msg_payload'] = data['msg_payload'].astype(str)
    data['msg_role'] = data['msg_role'].astype(str)
    data[xes_constants.DEFAULT_TRANSITION_KEY] = data[xes_constants.DEFAULT_TRANSITION_KEY].astype(str)
    


    log = log_converter.apply(
        data, variant=log_converter.Variants.TO_EVENT_LOG)

    file_name = name + '.xes'
    xes_exporter.apply(log, file_name)

    # find and replace attribute tag
    search_text = "xmlns"
    replace_text = "xes." + search_text

    with open(file_name, 'r') as file:
        data = file.read()
        data = data.replace(search_text, replace_text)

    with open(file_name, 'w') as file:
        file.write(data)

    return file_name


def merge_xes(paths: dict):
    result_file = 'merged.xes'
    i = 0
    for k in paths.keys():
        source_name = paths.get(k).split('\\')[-1].split('.')[0]
        tree = ET.parse(paths.get(k))
        root = tree.getroot()

        if i == 0:
            if os.path.exists(result_file):
                os.remove(result_file)
            for event in root.iter('event'):
                ET.SubElement(event, 'string', {
                    'key': 'resource', 'value': source_name})
            tree.write(result_file)

        else:
            tree_output = ET.parse(result_file)
            root_output = tree_output.getroot()
            for event in root.iter('event'):
                ET.SubElement(event, 'string', {
                    'key': 'resource', 'value': source_name})
            for (trace, trace_output) in zip(root.iter('trace'), root_output.iter('trace')):
                for ev in trace.iter('event'):
                    trace_output.append(ev)

            tree_output.write(result_file)
        i += 1

    return result_file

def tocsv():

    # Define the path to your log file
    log_path = 'docs/logs/mrs.xes'

    # Import the log from the XES file
    log = xes_importer.apply(log_path)

    dataframe = pm4py.convert_to_dataframe(log)
    dataframe.to_csv('prova.csv')
