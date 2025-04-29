import os
import re
from collections import defaultdict

log_output_dir = '/home/server/Desktop/rl_scheduler_for_mqtt/rl_module/log/'

def log_fct(quic_log_path):
    log_output_file = os.path.join(log_output_dir, 'fct.log')
    found = False
    written_content = ""

    with open(quic_log_path, 'r') as infile, open(log_output_file, 'a') as outfile:
        for line in infile:
            match = re.search(r'Completed all:\s*([\d.]+)(ms|s)', line)
            if match:
                value = float(match.group(1))
                unit = match.group(2)
                if unit == 's':
                    value *= 1000
                written_content = str(value)
                outfile.write(written_content + "\n")
                found = True

        if not found:
            written_content = str(6000)
            outfile.write(written_content + "\n")

    print("fct log success: " + written_content)
    return written_content

def log_ofo(pre_ofo, quic_log_path):
    log_output_file = os.path.join(log_output_dir, 'ofo.log')
    offsets = []
    pattern = re.compile(r'stream 7 receive frame offset (\d+) from path 0')
    with open(quic_log_path, 'r') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                offset = int(match.group(1))
                offsets.append(offset)
    received = []
    ofo_size = 0
    current_expected = 0
    segment_size = 1320

    for offset in offsets:
        if offset == current_expected:
            current_expected += segment_size
        elif offset > current_expected:
            if offset not in received:
                ofo_size += segment_size
                received.append(offset)
        else:
            pass

    with open(log_output_file, 'a') as outfile:
        outfile.write(str(ofo_size) + "\n")
    print("ofo log success")

def log_ofo_avg_nil(average_ofo):
    log_output_file = os.path.join(log_output_dir, 'ofo.log')
    with open(log_output_file, 'a') as outfile:
        outfile.write(str(average_ofo) + "\n")
    print("Nil ofo log success")

def log_ofo_avg(log_path):
    log_output_file = os.path.join(log_output_dir, 'ofo.log')
    ofodict = defaultdict(list)
    segment_size = 1320
    stime = 0
    completealltime = 0
    stream_id = '7'

    with open(log_path, 'r') as f:
        for line in f:
            starttimeline = re.compile(r'GET\shttps://10.1.0.1:6121/random-mqtt,')
            completeall = re.compile(r'Completed\sall')
            validline = re.compile(r'stream\s7\sreceive\sframe\soffset')

            if starttimeline.findall(line):
                startminute = re.findall(r'(?<=:)\d+(?=:\d+\.)', line)
                starttime = re.findall(r'(?<=:)\d+\.\d+', line)
                stime = list(map(float, starttime))[0] + list(map(float, startminute))[0] * 60

            if completeall.findall(line):
                c_time = re.findall(r'(?<=:\s)\d+\.\d+', line)
                completealltime = list(map(float, c_time))[0]

            if validline.findall(line):
                minute = re.findall(r'(?<=:)\d+(?=:\d+\.)', line)
                offset = re.findall(r'(?<=offset\s)\d+', line)
                timestamp = re.findall(r'(?<=:)\d+\.\d+', line)
                ts_l = list(map(float, timestamp))
                ts_l[0] = ts_l[0] + list(map(float, minute))[0] * 60
                if stime > 0 and ts_l[0] > stime:
                    offset_l = list(map(float, offset))
                    if offset_l[0] not in ofodict[stream_id]:
                        x = ts_l + offset_l
                        ofodict[stream_id].append(x)

    if stime == 0 or completealltime == 0:
        return 0.0

    ofosize = 0
    beginofooffset = 0
    queuelist = []
    streamofo = []

    for i in range(len(ofodict[stream_id])):
        offset = ofodict[stream_id][i][1]
        ts = ofodict[stream_id][i][0]
        if beginofooffset == 0 and offset - 0 > 1340:
            queuelist.append(offset)
            queuelist.sort()
            ofosize += segment_size
            streamofo.append([ts, ofosize])
        elif beginofooffset == 0 and offset - beginofooffset <= 1340:
            queuelist.append(offset)
            queuelist.sort()
            ofosize += segment_size
            while queuelist and queuelist[0] - beginofooffset <= 1340:
                beginofooffset = queuelist[0]
                ofosize = max(0, ofosize - segment_size)
                queuelist.pop(0)
            streamofo.append([ts, ofosize])
        elif beginofooffset == 0 and offset - ofodict[stream_id][i - 1][1] > 1340 and not queuelist:
            beginofooffset = ofodict[stream_id][i - 1][1]
            queuelist.append(offset)
            queuelist.sort()
            streamofo.append([ofodict[stream_id][i - 1][0], 0])
            ofosize += segment_size
            streamofo.append([ts, ofosize])
        elif beginofooffset != 0 and offset - beginofooffset > 1340:
            queuelist.append(offset)
            queuelist.sort()
            ofosize += segment_size
            streamofo.append([ts, ofosize])
        elif beginofooffset != 0 and offset - beginofooffset <= 1340:
            if offset < beginofooffset:
                continue
            queuelist.append(offset)
            queuelist.sort()
            ofosize += segment_size
            while queuelist and queuelist[0] - beginofooffset <= 1340:
                beginofooffset = queuelist[0]
                ofosize = max(0, ofosize - segment_size)
                queuelist.pop(0)
            streamofo.append([ts, ofosize])

    # calculate average OFO size over time
    ofocallist = []
    for i in range(1, len(streamofo)):
        duration = streamofo[i][0] - streamofo[i - 1][0]
        ofo_amount = streamofo[i - 1][1]
        ofocallist.append(duration * ofo_amount)

    average_ofo = sum(ofocallist) / completealltime if completealltime > 0 else 0.0
    with open(log_output_file, 'a') as outfile:
        outfile.write(str(average_ofo) + "\n")
    print("ofo log success")
