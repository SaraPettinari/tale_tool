import os
import csv
import math
from csv import DictReader
import datetime
import random

file = os.getcwd() + '/csv/drone_1_merged.csv'

events = ['TAKEOFF', 'EXPLORE', 'WEED_FOUND', 'WEED_POSITION',
          'TRACTOR_POSITION', 'CLOSEST_TRACTOR', 'LOW_BATTERY', 'RETURN_TO_BASE', 'LAND']

out_list = []

tractors = {'tractor_1': (0, 0, False), 'tractor_2': (
    1, 0, False)}  # (x,y, busy)

start = 'start'
complete = 'complete'

caseid = 0

obj = {'time': '', 'activity': '', 'lifecycle': '',
       'payload': '', 'x': '', 'y': '', 'z': '', 'case_id': ''}
'''
numdays = random.randint(50, 100)
base = datetime.datetime.today()
date_list = [base - datetime.timedelta(hours=x, seconds=random.randint(6, 15), microseconds=random.randint(24, 55)) for x in range(numdays)]
date_string = [date_obj.strftime('%Y/%m/%d %H:%M:%S.%f') for date_obj in date_list]
date_list.reverse()
print(date_list)
'''


def out_append(time, act, lifecycle, payload, x, y, z, case):
    obj = {'time': time, 'activity': act, 'lifecycle': lifecycle,
           'payload': payload, 'x': x, 'y': y, 'z': z, 'case_id': case}

    out_list.append(obj)


def add_to(time: datetime, case):
    toff = events[0]

    y = random.uniform(4.9, 5.1)

    out_append(time, toff, start, '', 0.0, y, 0.0, case)

    end_time = time + \
        datetime.timedelta(seconds=1, milliseconds=random.randint(15, 62))

    z_out = random.uniform(1.4, 1.45)

    x = 0.0

    out_append(end_time, toff, complete, '', x, y, z_out, case)

    return (end_time, x, y, z_out)


def add_explore(x_start: float, y_start: float, z_start: float, time: datetime, case, init, counter):
    global tractors
    j = counter + 1
    # EXPLORE
    act = 'EXPLORE'
    if z_start >= 1.45:
        z_out = z_start - random.uniform(0.0, 0.05)
    else:
        z_out = z_start + random.uniform(0.0, 0.05)

    out_append(time, act, start, '', x_start, y_start, z_out, case)

    end_explore_time = time + \
        datetime.timedelta(seconds=random.randint(
            5, 20), milliseconds=random.randint(15, 62))

    if j > 8:
        if x_start <= 8.0:
            x_stop = x_start + random.uniform(0.2, 2.4)
        else:
            x_stop = x_start - random.uniform(0.2, 0.4)

        if y_start <= 9.0:
            y_stop = y_start + random.uniform(0.0, 1.6)
        else:
            y_stop = y_start - random.uniform(0.0, 0.6)

    else:
        if x_start <= 8.0:
            x_stop = x_start + random.uniform(0.2, 2.4)
        else:
            x_stop = x_start - random.uniform(0.2, 0.4)

        if y_start <= 9.0:
            y_stop = y_start + random.uniform(0.5, 1.5)
        else:
            y_stop = y_start - random.uniform(0.5, 1.0)

    out_append(end_explore_time, act, complete,
               '', x_stop, y_stop, z_out, case)

    # WEED FOUND
    act = 'WEED_FOUND'
    weedf_time = end_explore_time + \
        datetime.timedelta(milliseconds=random.randint(30, 90))

    out_append(weedf_time, act, start, '', x_stop, y_stop, z_out, case)

    weedf_time += datetime.timedelta(milliseconds=random.randint(20, 40))

    out_append(weedf_time, act, complete, '', x_stop, y_stop, z_out, case)

    weedf_time = add_weedhandler(x_stop, y_stop, z_out, weedf_time,
                                 case, init=False)

    if not end:
        if j < 30:
            add_explore(x_stop, y_stop, z_out, weedf_time,
                        case, init=False, counter=j)
        else:
            add_end(x_stop, y_stop, z_out, weedf_time, case)


def add_weedhandler(x_stop: float, y_stop: float, z_out: float, weedf_time: datetime, case, init):
    # WEED POSITION
    if init:
        act = 'WEED_POSITION'
        weedf_time += datetime.timedelta(milliseconds=random.randint(20, 40))

        out_append(weedf_time, act, start,
                   '{weed: {x:' + str(x_stop) + ', y: ' + str(y_stop) + '} }', x_stop, y_stop, z_out, case)

        weedf_time += datetime.timedelta(milliseconds=random.randint(20, 40))

        out_append(weedf_time, act, complete,
                   '{weed: {x:' + str(x_stop) + ', y: ' + str(y_stop) + '} }', x_stop, y_stop, z_out, case)

    else:
        _range = random.randint(1, 4)
        for _ in range(_range):
            act = 'WEED_POSITION'
            weedf_time += datetime.timedelta(seconds=10)

            out_append(weedf_time, act, start,
                       '{weed: {x:' + str(x_stop) + ', y: ' + str(y_stop) + '} }', x_stop, y_stop, z_out, case)

            weedf_time += datetime.timedelta(seconds=10)

            out_append(weedf_time, act, complete,
                       '{weed: {x:' + str(x_stop) + ', y: ' + str(y_stop) + '} }', x_stop, y_stop, z_out, case)

    rand = random.randint(1, 30)
    if rand == 15:
        add_end(x_stop, y_stop, z_out, weedf_time, case)
    else:
        tract_pos = []
        if random.randint(0, 10) % 2 == 0:
            for t in tractors.keys():
                tractors[t] = (tractors.get(t)[0], tractors.get(t)[1], False)
        # TRACTOR POSITION
        for t in tractors.keys():
            if not tractors.get(t)[-1]:
                act = 'TRACTOR_POSITION'
                weedf_time += datetime.timedelta(
                    milliseconds=random.randint(20, 40))

                xt = tractors.get(t)[0]
                yt = tractors.get(t)[1]

                tract_pos.append((t, xt, yt))

                out_append(weedf_time, act, start,
                           '{ header: ' + str(t) + ', position: {x:' + str(xt) + ', y: ' + str(yt) + '} }', x_stop, y_stop, z_out, case)

                weedf_time += datetime.timedelta(
                    milliseconds=random.randint(20, 40))

                out_append(weedf_time, act, complete,
                           '{ header: ' + str(t) + ', position: {x:' + str(xt) + ', y: ' + str(yt) + '} }', x_stop, y_stop, z_out, case)

        min_dist = 100
        closest = ''
        act = 'CLOSEST_TRACTOR'
        if len(tract_pos) > 0:
            if len(tract_pos) == 1:
                weedf_time += datetime.timedelta(
                    milliseconds=random.randint(20, 40))
                closest = tract_pos[0][0]
                tractors[closest] = (x_stop, y_stop, True)
            else:
                for el in tract_pos:
                    weedf_time += datetime.timedelta(
                        milliseconds=random.randint(5, 10))
                    distance = math.sqrt(
                        math.pow((el[1] - x_stop), 2) + math.pow((el[2] - y_stop), 2))
                    if distance < min_dist:
                        min_dist = distance
                        closest = el[0]
                tractors[closest] = (x_stop, y_stop, True)

            out_append(weedf_time, act, start,
                       '{ name: ' + closest + ' }', x_stop, y_stop, z_out, case)

            weedf_time += datetime.timedelta(
                milliseconds=random.randint(10, 12))

            out_append(weedf_time, act, complete,
                       '{ name: ' + closest + ' }', x_stop, y_stop, z_out, case)
        else:
            weedf_time = add_weedhandler(x_stop, y_stop, z_out, weedf_time,
                            case, init=False)
    return weedf_time


def add_end(x, y, z, time: datetime, case):
    global end
    end = True
    act = 'LOW_BATTERY'

    out_append(time, act, start, '', x, y, z, case)

    end_time = time + \
        datetime.timedelta(milliseconds=random.randint(15, 62))

    out_append(end_time, act, complete, '', x, y, z, case)

    act = 'RETURN_TO_BASE'

    out_append(end_time, act, start, '', x, y, z, case)

    end_time = end_time + \
        datetime.timedelta(seconds=random.randint(5, 22))

    out_append(end_time, act, complete, '', 0.0, 5.0, z, case)

    act = 'LAND'

    out_append(end_time, act, start, '', 0.0, 5.0, z, case)

    end_time = end_time + \
        datetime.timedelta(seconds=random.randint(1, 3))

    out_append(end_time, act, complete, '', 0.0, 5.0, 0.0, case)


if __name__ == "__main__":
    date_list = [datetime.datetime(2022, 12, 16, 22, 27, 8, 918367), datetime.datetime(2022, 12, 16, 23, 27, 14, 918351), datetime.datetime(2022, 12, 17, 0, 27, 10, 918358), datetime.datetime(2022, 12, 17, 1, 27, 6, 918360), datetime.datetime(2022, 12, 17, 2, 27, 7, 918370), datetime.datetime(2022, 12, 17, 3, 27, 11, 918351), datetime.datetime(2022, 12, 17, 4, 27, 11, 918353), datetime.datetime(2022, 12, 17, 5, 27, 12, 918349), datetime.datetime(2022, 12, 17, 6, 27, 7, 918348), datetime.datetime(2022, 12, 17, 7, 27, 14, 918354), datetime.datetime(2022, 12, 17, 8, 27, 5, 918366), datetime.datetime(2022, 12, 17, 9, 27, 7, 918367), datetime.datetime(2022,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               12, 17, 10, 27, 14, 918367), datetime.datetime(2022, 12, 17, 11, 27, 14, 918358), datetime.datetime(2022, 12, 17, 12, 27, 10, 918349), datetime.datetime(2022, 12, 17, 13, 27, 13, 918360), datetime.datetime(2022, 12, 17, 14, 27, 5, 918357), datetime.datetime(2022, 12, 17, 15, 27, 13, 918374), datetime.datetime(2022, 12, 17, 16, 27, 8, 918362), datetime.datetime(2022, 12, 17, 17, 27, 13, 918347), datetime.datetime(2022, 12, 17,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               18, 27, 12, 918351), datetime.datetime(2022, 12, 17, 19, 27, 7, 918368), datetime.datetime(2022, 12, 17, 20, 27, 10, 918364), datetime.datetime(2022, 12, 17, 21, 27, 13, 918345), datetime.datetime(2022, 12, 17, 22,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    27, 14, 918358), datetime.datetime(2022, 12, 17, 23, 27, 14, 918373), datetime.datetime(2022, 12, 18, 0, 27, 13, 918353), datetime.datetime(2022, 12, 18, 1, 27, 7, 918366), datetime.datetime(2022, 12, 18, 2, 27, 11, 918374), datetime.datetime(2022, 12, 18, 3, 27, 9, 918348), datetime.datetime(2022, 12, 18, 4, 27, 8, 918359), datetime.datetime(2022, 12, 18, 5, 27, 11, 918357), datetime.datetime(2022, 12, 18, 6, 27, 13, 918360), datetime.datetime(2022, 12, 18, 7, 27, 9, 918363), datetime.datetime(2022, 12, 18, 8, 27, 10, 918373), datetime.datetime(2022, 12, 18, 9, 27, 6, 918345), datetime.datetime(2022, 12, 18, 10, 27, 9, 918375), datetime.datetime(2022, 12, 18, 11, 27, 13, 918369), datetime.datetime(2022, 12, 18, 12, 27, 5, 918347), datetime.datetime(2022, 12, 18, 13, 27, 5, 918373), datetime.datetime(2022, 12, 18, 14, 27, 11, 918347), datetime.datetime(2022, 12, 18, 15, 27, 8, 918357), datetime.datetime(2022, 12, 18, 16, 27, 14, 918360), datetime.datetime(2022, 12, 18, 17, 27, 12, 918365), datetime.datetime(2022, 12, 18, 18, 27, 9, 918374), datetime.datetime(2022, 12, 18, 19, 27, 13, 918374), datetime.datetime(2022, 12, 18, 20, 27, 14, 918356), datetime.datetime(2022, 12, 18, 21, 27, 14, 918365), datetime.datetime(2022, 12, 18, 22, 27, 7, 918376), datetime.datetime(2022, 12, 18, 23, 27, 7, 918357), datetime.datetime(2022, 12, 19, 0, 27, 5, 918370), datetime.datetime(2022, 12, 19, 1, 27, 13, 918375), datetime.datetime(2022, 12, 19, 2, 27, 5, 918376), datetime.datetime(2022, 12, 19, 3, 27, 7, 918366), datetime.datetime(2022, 12, 19, 4, 27, 14, 918360), datetime.datetime(2022, 12, 19, 5, 27, 11, 918352), datetime.datetime(2022, 12, 19, 6, 27, 14, 918355), datetime.datetime(2022, 12, 19, 7, 27,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       13, 918352), datetime.datetime(2022, 12, 19, 8, 27, 13, 918346), datetime.datetime(2022, 12, 19, 9, 27, 5, 918351), datetime.datetime(2022, 12, 19, 10, 27, 10, 918368), datetime.datetime(2022, 12, 19, 11, 27, 13, 918349), datetime.datetime(2022, 12, 19, 12, 27, 10, 918373), datetime.datetime(2022, 12, 19, 13, 27, 7, 918348), datetime.datetime(2022, 12, 19, 14, 27, 12, 918348), datetime.datetime(2022, 12, 19, 15, 27, 6, 918351), datetime.datetime(2022, 12, 19, 16, 27, 14, 918368), datetime.datetime(2022, 12, 19, 17, 44, 12, 128368), datetime.datetime(2022, 12, 19, 18, 13, 28, 567368), datetime.datetime(2022, 12, 19, 19, 00, 36, 969368)]

    for timer in date_list:
        end = False
        caseid += 1

        etime, x, y, z = add_to(timer, caseid)

        add_explore(x, y, z, etime, caseid, init=True, counter=0)

    header = list(out_list[0].keys())

    with open('drone0.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=header)

        writer.writeheader()
        writer.writerows(out_list)
