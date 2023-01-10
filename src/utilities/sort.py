import csv
import pandas as pd
import glob
import os
from csv import writer, reader

# setting the path for joining multiple files
files = "csv/2Trattori/*.csv"

# list of merged files returned
files = glob.glob(files)

for f in files:
    robot_name = os.path.split(f)[-1].replace('.csv', '')
    with open(f, 'r') as read_obj, open('csv/res/' + robot_name + '.csv', 'w', newline='') as write_obj:
        csv_reader = reader(read_obj)
        csv_writer = writer(write_obj)
        # Read each row of the input csv file as list
        line_index = 0
        for row in csv_reader:
            if line_index == 0:
                row.append('resource')
            else:
                row.append(robot_name)

            csv_writer.writerow(row)
            line_index += 1


res_path = "csv/res/*.csv"
res_files = glob.glob(res_path)
df = pd.concat(map(pd.read_csv, res_files), ignore_index=True)

df['time'] = pd.to_datetime(df['time'])
df = df.sort_values(by='time')

#df['time'] = str(df['time'])
#df['time'] = df['time'].apply(lambda t: t.split('       ')[1])
#df['time'] = df['time'].apply(lambda t: t.split('.')[0])

mfile = "MRS.csv"
df.to_csv(mfile, index=False)
