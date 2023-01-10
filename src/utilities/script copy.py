import csv
import pandas as pd


filename = "3t.csv"

dict = []
with open(filename, 'r') as data:
    reader = csv.DictReader(data)
    i = 0
    for line in csv.DictReader(data):
        if line.get('activity') == 'WEED_POSITION':
            line['z'] = 0.0

        dict.append(line)
        i += 1

'''

with open(filename, 'r') as data:
    reader = csv.DictReader(data)
    for line in csv.DictReader(data):
        line['activity'] = line.get('activity') + '/T_3'            
        dict.append(line)
'''

with open(filename, 'w', newline='') as csv_file:
    fieldnames = ['time', 'activity', 'lifecycle',
                  'payload', 'x', 'y', 'z', 'Case_ID']
    writer = csv.DictWriter(csv_file, fieldnames)
    writer.writeheader()
    for row in dict:
        writer.writerow(row)
