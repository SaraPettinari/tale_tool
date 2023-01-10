import os
import csv
import json
import datetime
import random
from csv import DictReader

file = open(os.getcwd() + '/drone0.csv')

events = ['WEED_POSITION', 'TRACTOR_POSITION', 'CLOSEST_TRACTOR',
          'MOVE', 'CUT_GRASS', 'LOW_BATTERY', 'RETURN_TO_BASE', 'STOP']

out_list = []

tractors = {'tractor_1': (0, 0, False), 'tractor_2': (
    1, 0, False)}  # (x,y, busy)

start = 'start'
complete = 'complete'

caseid = 0

obj = {'time': '', 'activity': '', 'lifecycle': '',
       'payload': '', 'x': '', 'y': '', 'z': '', 'case_id': ''}


def do(tractor_name):
    weed_pos = ['', '']
    reader = csv.DictReader(file)
    xw = 0
    xs = 0
    yw = 0
    ys = 0
    case_check = '1'
    time_check = ''
    for line in reader:
        curr_act = line.get('activity')
        curr_payload = line.get('payload')
        case = line.get('case_id')
        if case != case_check:
            add_end(xw, yw, 0, time_check, case_check)
            case_check = case
        time_check = line.get('time')
        if curr_act == 'WEED_POSITION' and line.get('lifecycle') == 'start':
            this_line = line.copy()
            this_line['x'] = xs
            this_line['y'] = ys
            this_line['z'] = 0

            weed_pos[0] = this_line
        if curr_act == 'WEED_POSITION' and line.get('lifecycle') == 'complete':
            this_line = line.copy()
            this_line['x'] = xs
            this_line['y'] = ys
            this_line['z'] = 0

            weed_pos[1] = this_line

            xw = line.get('x')
            yw = line.get('y')

        if curr_act == 'TRACTOR_POSITION' and tractor_name in curr_payload:
            out_list.append(weed_pos[0])
            out_list.append(weed_pos[1])
            this_line = line.copy()
            this_line['x'] = xs
            this_line['y'] = ys
            this_line['z'] = 0

            out_list.append(this_line)

            this_line['lifecycle'] = complete
            out_list.append(this_line)
            # adds a singlequote and makes it more valid
            notjson = curr_payload.replace(":", "\":\"")
            notjson = notjson.replace(':" {', ':{')
            notjson = notjson.replace(", ", "\", \"")
            notjson = notjson.replace("{", "{\"")

            notjson = notjson.replace("{ ", "{\"")

            notjson = notjson.replace("}", "\"}")
            notjson = notjson.replace(' "}', "}")
            pos = json.loads(notjson)
            xs = pos.get('position').get('x').replace(' ', '')
            ys = pos.get('position').get('y').replace(' ', '')

        if curr_act == 'CLOSEST_TRACTOR' and tractor_name in curr_payload:
            out_list.append(line)

            if line.get('lifecycle') == complete:
                out_list.append(line)

                time = line.get('time')
                append_movements(time, case, xs, ys, xw, yw)


def out_append(time, act, lifecycle, payload, x, y, z, case):
    obj = {'time': time, 'activity': act, 'lifecycle': lifecycle,
           'payload': payload, 'x': x, 'y': y, 'z': z, 'case_id': case}

    out_list.append(obj)


def append_movements(time, case, xsta, ysta, xsto, ysto):
    act = 'MOVE'
    obj = {'time': time, 'activity': act, 'lifecycle': start,
           'payload': '', 'x': xsta, 'y': ysta, 'z': 0.0, 'case_id': case}

    out_list.append(obj)

    obj = {'time': time, 'activity': act, 'lifecycle': complete,
           'payload': '', 'x': xsto, 'y': ysto, 'z': 0.0, 'case_id': case}
    out_list.append(obj)
    act = 'CUT_GRASS'

    obj = {'time': time, 'activity': act, 'lifecycle': start,
           'payload': '', 'x': xsto, 'y': ysto, 'z': 0.0, 'case_id': case}
    out_list.append(obj)

    obj = {'time': time, 'activity': act, 'lifecycle': complete,
           'payload': '', 'x': xsto, 'y': ysto, 'z': 0.0, 'case_id': case}
    out_list.append(obj)


def add_end(x, y, z, time, case):
    global end
    end = True
    act = 'LOW_BATTERY'

    out_append(time, act, start, '', x, y, z, case)

    end_time = time

    out_append(end_time, act, complete, '', x, y, z, case)

    act = 'RETURN_TO_BASE'

    out_append(end_time, act, start, '', x, y, z, case)

    out_append(end_time, act, complete, '', 0.0, 1.0, z, case)

    act = 'STOP'

    out_append(end_time, act, start, '', 0.0, 1.0, z, case)

    out_append(end_time, act, complete, '', 0.0, 1.0, 0.0, case)


if __name__ == "__main__":
    name = 'tractor_2'
    do(name)

    header = list(out_list[0].keys())

    with open(name + '.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=header)

        writer.writeheader()
        writer.writerows(out_list)
