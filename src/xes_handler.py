import os
import pandas as pd
import xml.etree.ElementTree as ET
import pm4py
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.exporter.xes import exporter as xes_exporter
from pm4py.objects.log.importer.xes import importer as xes_importer


def csv_to_xes(path):
    name = path.split('\\')[-1].split('.')[0]
    data = pd.read_csv(path)
    if len(data.columns) == 8:
        cols = ['time:timestamp', 'concept:name', 'lifecycle:transition',
                'data:payload', 'x', 'y', 'z', 'case:concept:name']
    elif len(data.columns) == 9:
        cols = ['time:timestamp', 'concept:name', 'lifecycle:transition',
                'data:payload', 'x', 'y', 'z', 'case:concept:name', 'org:resource']
    else:
        cols = data.columns.values.tolist()
    data.columns = cols
    data['time:timestamp'] = pd.to_datetime(data['time:timestamp'])
    data['concept:name'] = data['concept:name'].astype(str)

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

#tocsv()

import random

# Function to retrieve unique values of a column from a CSV file
def get_unique_column_values(filename, column_name):
    unique_values = set()

    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            v = row[column_name]
            if v != 'none':
                value = int(v.split('m')[1])
                unique_values.add(value)

    return unique_values

# Function to generate a random 4-digit integer not in the given set
def generate_unique_random_int(existing_values):
    while True:
        random_int = random.randint(1000, 9999)
        if random_int not in existing_values:
            return 'm' + str(random_int)
#tocsv()
import csv, copy

# Function to process the CSV file and find the groups
def find_groups(filename):
    groups = []
    current_group = []

    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        prev_row = None

        for row in reader:
            if (row['concept:name'] == 'weed_position!' and
                row['lifecycle:transition'] == 'start'):
                current_group = [row]
            elif (row['concept:name'] == 'weed_position!' and
                  row['lifecycle:transition'] == 'complete'):
                if current_group and row['msg:id'] == current_group[0]['msg:id']:
                    current_group.append(row)
                    groups.append(current_group)
                    current_group = []
            elif current_group:
                current_group.append(row)

    return groups

# Function to clone a group of rows and modify 'msg:id'
def clone_and_modify_group(group, new_msg_id):
    cloned_group = copy.deepcopy(group)
    for row in cloned_group:
        row['msg:id'] = new_msg_id
    return cloned_group

# Function to write groups to a CSV file
def write_groups_to_csv(groups, original_filename, output_filename):
    with open(output_filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=groups[0][0].keys())  # Assuming all groups have the same structure
        writer.writeheader()

        modified_ids = set()
        for item in groups:
            if isinstance(item, list):  # Group of rows
                for row in item:
                    writer.writerow(row)
                    modified_ids.add(row['msg:id'])
            else:  # Single row
                writer.writerow(item)

        # Write remaining original rows not modified
        with open(original_filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['msg:id'] not in modified_ids:
                    writer.writerow(row)

# Example usage
filename = 'docs/logs/csv/prova.csv'# Function to process the CSV file and find the groups

output_filename = 'output_file.csv'

groups = find_groups(filename)
existing_values = set()

# Collect cloned groups with modified 'msg:id'
modified_groups = []
for group in groups:
    existing_values.add(group[0]['msg:id'])
    new_msg_id = generate_unique_random_int(existing_values)
    cloned_group = clone_and_modify_group(group, new_msg_id)
    modified_groups.append(cloned_group)
    modified_groups.extend(group)  # Extend with original group

# Write all lines to a new CSV file
write_groups_to_csv(modified_groups, filename, output_filename)