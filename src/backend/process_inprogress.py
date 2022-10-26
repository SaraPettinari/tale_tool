import csv
from glob import glob
import os
import pandas as pd
import xml.etree.ElementTree as ET

from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.exporter.xes import exporter as xes_exporter

out_file = 'temp_all.csv'


def assign_progressive_state(path):
    data = []
    with open(path, 'r') as read_obj:
        reader = csv.DictReader(read_obj)
        for line in reader:
            data.append(line)

        for j in range(0, len(data), 1):
            if data[j]['activity'] != data[j + 1]['activity'] and data[j]['activity'] != data[j - 1]['activity']:
                l = {}
                l1 = {}
                l.update(data[j])
                l1.update(data[j])
                data.insert(j+1, l)
                data.insert(j+2, l1)

        for i in range(0, len(data), 1):
            if i == 0:
                data[i]['lifecycle'] = 'start'
            elif i == len(data) - 1:
                data[i]['lifecycle'] = 'complete'
            else:
                if data[i].get('activity') == data[i+1].get('activity'):
                    if data[i]['lifecycle'] == '':
                        data[i]['lifecycle'] = 'inprogress'
                        data[i+1]['lifecycle'] = 'inprogress'
                else:
                    data[i]['lifecycle'] = 'complete'
                    data[i+1]['lifecycle'] = 'start'

        with open(out_file, 'w', newline='') as csv_file:
            fieldnames = ['case', 'time', 'activity',
                          'lifecycle', 'x', 'y', 'z', 'robot']
            writer = csv.DictWriter(csv_file, fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)


def csv_to_xes(path):
    name = path.split('\\')[-1].split('.')[0]
    data = pd.read_csv(path)
    cols = []
    for c in data.columns.values:
        rcol = renaming(c)
        cols.append(rcol)
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

    with open('file.xes', 'w') as file:
        file.write(data)

    return file_name


def renaming(column: str):
    out = ''
    if 'time' in column:
        out = 'time:timestamp'
    elif 'activity' in column:
        out = 'concept:name'
    elif 'lifecycle' in column:
        out = 'lifecycle:transition'
    elif 'case' in column:
        out = 'case:concept:name'
    else:
        out = column
    return out


def apply_odom(path):
    # setting the path for joining multiple files
    files = path + "/*.csv"

    files = glob.glob(files)

    dict_obj = []
    odom_dict = []
    i = 1
    dati = []
    for f in files:
        file_name = os.path.split(f)[-1].replace('.csv', '')
        case_id = os.path.split(f)[0].replace('odometry\\', '')
        if file_name == 'macro':
            with open(f, 'r') as read_obj:
                reader = csv.DictReader(read_obj)

                for line in reader:
                    act = line.get('activity')
                    dati.append({'time': line.get('time'), 'activity': act,
                                'lifecycle': line.get('lifecycle')})
        else:
            df = pd.read_csv(f)
            df['time'] = pd.to_datetime(df['time'])
            df = df.sort_values(by='time')
            df.to_csv(f, index=False)

            with open(f, 'r') as read_obj:
                reader = csv.DictReader(read_obj)
                for line in reader:
                    odom_dict.append(line)

            for i in range(0, len(dati), 2):
                start = dati[i].get('time')
                stop = dati[i+1].get('time')
                activity = dati[i].get('activity')
                check = False
                appoggio = {}

                for elem in odom_dict:
                    elem_time = elem.get('time')
                    '''
                    if (pd.to_datetime(start) > pd.to_datetime(elem_time)):
                        odom_dict.remove(elem)
                    el
                    '''
                    if ((pd.to_datetime(start) <= pd.to_datetime(elem_time)) and (pd.to_datetime(elem_time) <= pd.to_datetime(stop))):
                        dict_obj.append(({'case': case_id, 'time': elem_time, 'activity': activity, 'x': elem.get(
                            'x'), 'y': elem.get('y'), 'z': elem.get('z')}))
                        odom_dict.remove(elem)
                        check = True
                    elif (pd.to_datetime(start) > pd.to_datetime(elem_time)):
                        appoggio = ({'case': case_id, 'time': elem_time, 'activity': activity, 'x': elem.get(
                            'x'), 'y': elem.get('y'), 'z': elem.get('z')})

                if not check:
                    dict_obj.append(appoggio)

        with open(case_id + '_all.csv', 'w', newline='') as csv_file:
            fieldnames = ['case', 'time', 'activity',
                          'lifecycle', 'x', 'y', 'z']
            writer = csv.DictWriter(csv_file, fieldnames)
            writer.writeheader()
            for row in dict_obj:
                writer.writerow(row)
            dict_obj.clear()
            odom_dict.clear()


if __name__ == '__main__':
    assign_progressive_state('all.csv')
    csv_to_xes(out_file)
