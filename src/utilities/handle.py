import os
import csv
from csv import DictReader

file = os.getcwd() + '/csv/drone_1_merged.csv'
with open(file) as csv_file:
    dict_reader = DictReader(csv_file)
    
    last_act = False

    list_of_dict = list(dict_reader)
    
    out_list = []
    check_case = 1
    
    for ld in list_of_dict:
        case = int(ld.get('Case_ID'))
        
        if not (last_act and case == check_case):
            if ld.get('activity') == 'EXPLORE':
                if float(ld.get('z')) < 1.4:
                    ld['z'] = 1.4746659587374973
            if ld.get('activity').startswith('WEED_') or ld.get('activity').startswith('WEED_'):
                if float(ld.get('z')) < 1.4:
                    ld['z'] = 1.4759587374664973
            if ld.get('x').endswith('e-13') or ld.get('x').endswith('e-14'):
                ld['x'] = 0.0
            if ld.get('y').endswith('e-13') or ld.get('y').endswith('e-14'):
                ld['y'] = 0.0
                
            
            if not last_act and ld.get('activity') == 'LAND' and ld.get('lifecycle') == 'STOP':
                out_list.append(ld)
                last_act = True
                check_case = case
                
            if ld.get('activity') == 'TAKEOFF' and ld.get('lifecycle') == 'START':
                last_act = True
       
            
            if last_act == True and ld.get('activity') == 'TAKEOFF' and ld.get('lifecycle') == 'STOP':
                appoggio = ld.copy()
                appoggio['lifecycle'] = 'start'
                out_list.append(appoggio)
                last_act = False
                
            if ld.get('activity') == 'TAKEOFF' and ld.get('lifecycle') == 'START':
                last_act = False
                
            if ld.get('lifecycle') == 'START':
                ld['lifecycle'] = 'start'
            
            if ld.get('lifecycle') == 'STOP':
                ld['lifecycle'] = 'complete'
            
                
            if not last_act:
                out_list.append(ld)
            
header = list(out_list[0].keys())

with open('drone0.csv', 'w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=header)

    writer.writeheader()
    writer.writerows(out_list)