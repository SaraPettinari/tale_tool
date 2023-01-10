import csv
import pandas as pd
import glob
import os
from csv import writer, reader

# setting the path for joining multiple files
files = "csv/LogGrezzi/*/*.csv"

# list of merged files returned
files = glob.glob(files)
dict_obj = []
i = 1
nomi = {}
for f in files:
    act_name = os.path.split(f)[-1].replace('.csv', '')
    if not act_name in nomi.keys():
        nomi[act_name] = 1
    else:
        nomi[act_name] = nomi.get(act_name) + 1
        i += 1

    with open(f, 'r') as read_obj:
        reader = csv.DictReader(read_obj)
        for line in csv.DictReader(read_obj):
            dict_obj.append(
                {'time': line.get('time'), 'activity': act_name,
                 'lifecycle': 'null', 'Case_ID': nomi.get(act_name)}
            )

    with open('Spaghi/' + act_name + '_' + str(i) + '.csv', 'w', newline='') as csv_file:
        fieldnames = ['time', 'activity', 'lifecycle', 'Case_ID']
        writer = csv.DictWriter(csv_file, fieldnames)
        writer.writeheader()
        for row in dict_obj:
            writer.writerow(row)

        dict_obj.clear()
