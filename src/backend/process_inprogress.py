import csv
import os
import datetime
import pandas as pd
import xml.etree.ElementTree as ET
from glob import glob
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.exporter.xes import exporter as xes_exporter

out_file = 'temp_all.csv'

maxy = 9.5

def assign_progressive_state(path):
    data = []
    out_data = []
    with open(path, 'r') as read_obj:
        reader = csv.DictReader(read_obj)
        for line in reader:
            data.append(line)

        for j in range(0, len(data) - 1, 1):
            if data[j]['activity'] == data[j + 1]['activity'] and data[j]['activity'] != data[j - 1]['activity']:
                start_act = data[j]
                out_data.append(start_act)

                end_act = data[j+1]
                start_time = datetime.datetime.strptime(
                    start_act.get('time'), '%Y-%m-%d %H:%M:%S.%f')
                end_time = datetime.datetime.strptime(
                    end_act.get('time'), '%Y-%m-%d %H:%M:%S.%f')
                delta_time = (end_time - start_time)

                start_x = float(start_act.get('x'))
                start_y = float(start_act.get('y'))
                start_z = float(start_act.get('z'))
                end_x = float(end_act.get('x'))
                end_y = float(end_act.get('y'))
                end_z = float(end_act.get('z'))

                if delta_time.seconds > 1:
                    delta_x = (end_x - start_x) / delta_time.seconds
                    delta_y = (end_y - start_y) / delta_time.seconds
                    delta_z = (end_z - start_z) / delta_time.seconds

                elif delta_time.seconds == 1:
                    delta_x = (end_x - start_x) / 2
                    delta_y = (end_y - start_y) / 2
                    delta_z = (end_z - start_z) / 2

                last_act = {}
                last_act.update(start_act)
                for k in range(delta_time.seconds):
                    append_act = {}
                    append_act.update(last_act)
                    append_act['lifecycle'] = ''
                    if isinstance(append_act.get('time'), datetime.datetime):
                        append_act['time'] = append_act.get(
                            'time') + (delta_time / delta_time.seconds)
                    else:
                        append_act['time'] = datetime.datetime.strptime(append_act.get(
                            'time'), '%Y-%m-%d %H:%M:%S.%f') + delta_time / delta_time.seconds

                    append_act['x'] = float(append_act.get('x')) + delta_x
                    append_act['y'] = float(append_act.get('y')) + delta_y
                    append_act['z'] = float(append_act.get('z')) + delta_z

                    out_data.append(append_act)

                    last_act.update(append_act)

                out_data.append(end_act)

        for el in out_data:
            if el.get('lifecycle') == '':
                el['lifecycle'] = 'inprogress'

        header = line.keys()

        with open(out_file, 'w', newline='') as csv_file:
            writer = csv.DictWriter(csv_file, header)
            writer.writeheader()
            for row in out_data:
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

    with open('dronefile.xes', 'w') as file:
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
    assign_progressive_state('drone0.csv')
    csv_to_xes(out_file)
