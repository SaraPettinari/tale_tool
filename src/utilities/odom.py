import csv
import pandas as pd
import glob
import os
from csv import writer, reader


# setting the path for joining multiple files
files = "fatti/*/*.csv"

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

            for line in csv.DictReader(read_obj):
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
            for line in csv.DictReader(read_obj):
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
        fieldnames = ['case', 'time', 'activity', 'lifecycle', 'x', 'y', 'z']
        writer = csv.DictWriter(csv_file, fieldnames)
        writer.writeheader()
        for row in dict_obj:
            writer.writerow(row)
        dict_obj.clear()
        odom_dict.clear()
