import csv


filename = "merged_2T.csv"
#filename = "2t.csv"

dict = []
# opening the file using "with"
# statement

with open(filename, 'r') as data:
    reader = csv.DictReader(data)
    i = 0
    for line in csv.DictReader(data):
        if line.get('activity') == 'EXPLORE':
            if float(line.get('z')) < 1.4:
                line['z'] = 1.4746659587374973
        if line.get('activity').startswith('WEED_') or line.get('activity').startswith('WEED_'):
            if float(line.get('z')) < 1.4:
                line['z'] = 1.4759587374664973
        if line.get('x').endswith('e-13') or line.get('x').endswith('e-14'):
            line['x'] = 0.0
        if line.get('y').endswith('e-13') or line.get('y').endswith('e-14'):
            line['y'] = 0.0

        #line['time'] = line.get('time').split('.')[0]
        #line['time'] = line.get('time') + '.' + str(i)
        if line.get('lifecycle') == 'STOP':
            line['lifecycle'] = 'complete'
        elif line.get('lifecycle') == 'START':
            line['lifecycle'] = 'start'

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
