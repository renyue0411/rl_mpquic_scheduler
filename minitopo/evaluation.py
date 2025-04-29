#! /usr/bin/python2.7
from __future__ import print_function
import time
from multiprocessing import Queue
import argparse

# Doing * imports is bad :'(
from core.generate_topo import *
from core.generate_xp import *

import core.core as core
# import numpy as np
import os
import random
import sys

REMOTE_SERVER_RUNNER_HOSTNAME = ["server@localhost"]
REMOTE_SERVER_RUNNER_PORT = ["22"]


def getPostProcessingList(**kwargs):
    toReturn = []
    topoBasename = os.path.basename(kwargs["topoAbsPath"])
    toReturn.append(("client.pcap",
                      "_".join([str(x) for x in [kwargs["testDirectory"], kwargs["xp"], kwargs["protocol"], kwargs["multipath"],
                                                 topoBasename, "client.pcap"]])))
    toReturn.append(("server.pcap",
                      "_".join([str(x) for x in [kwargs["testDirectory"], kwargs["xp"], kwargs["protocol"], kwargs["multipath"],
                                                 topoBasename, "server.pcap"]])))
    toReturn.append(("command.log", "command.log"))
    toReturn.append(("ping.log", "ping.log"))
    if kwargs["xp"] == HTTPS:
        toReturn.append(("https_client.log", "https_client.log"))
        toReturn.append(("https_server.log", "https_server.log"))
    else:
        toReturn.append(("quic_client.log", "quic_client.log"))
        toReturn.append(("quic_server.log", "quic_server.log"))

    toReturn.append(("netstat_client_before", "netstat_client_before"))
    toReturn.append(("netstat_server_before", "netstat_server_before"))
    toReturn.append(("netstat_client_after", "netstat_client_after"))
    toReturn.append(("netstat_server_after", "netstat_server_after"))

    return toReturn


def quicTests(topos, scheduler, path_1_ban, path_1_rtt, scenario, protocol="mptcp", tmpfs="/mnt/tmpfs"):
    experienceLauncher = core.ExperienceLauncher(REMOTE_SERVER_RUNNER_HOSTNAME, REMOTE_SERVER_RUNNER_PORT)

    def testsXp(**kwargs):
        def testsMultipath(**kwargs):
            def test(**kwargs):
                xpDict = {
                    XP_TYPE: kwargs["xp"],
                    SCHEDULER_CLIENT: "default",
                    SCHEDULER_SERVER: "default",
                    CC: "olia" if kwargs["multipath"] == 1 else "cubic",
                    CLIENT_PCAP: "yes",
                    SERVER_PCAP: "yes",
                    HTTPS_FILE: "random",
                    HTTPS_RANDOM_SIZE: "20000",
                    QUIC_MULTIPATH: kwargs["multipath"],
                    RMEM: (10240, 87380, 16777216),
                }
                if int(kwargs["multipath"]) == 0:
                    kwargs["protocol"] = "tcp"

                kwargs["postProcessing"] = getPostProcessingList(**kwargs)
                core.experiment(experienceLauncher, xpDict, **kwargs)

            # core.experimentFor("multipath", [0, 1], test, **kwargs)
            core.experimentFor("multipath", [1], test, **kwargs)

        # core.experimentFor("xp", [HTTPS, QUIC], testsMultipath, **kwargs)
        core.experimentFor("xp", [QUIC], testsMultipath, **kwargs)
    
    core.experimentTopos(topos, "https_quic", protocol, tmpfs, testsXp, scheduler, path_1_ban, path_1_rtt, scenario)
    experienceLauncher.finish()


def generateExperimentalDesignRandomTopos(nbMptcpTopos=10, pathsPerTopo=2, bandwidth=(0.1, 100), rtt=(0, 400), queuingDelay=(0.0, 2.0), loss=(0.0, 2.5)):
    """ Assume only two paths per MPTCP topology, uniform distribution """
    mptcpTopos = []
    for nbTopo in range(nbMptcpTopos):
        mptcpTopo = {PATHS: [], NETEM: []}
        for nbPath in range(pathsPerTopo):
            # bandwidthPath = "{0:.2f}".format(np.random.uniform(low=bandwidth[0], high=bandwidth[1]))
            # rttPath = "{0:.0f}".format(np.random.uniform(low=rtt[0], high=rtt[1]))
            # delayPath = "{0:.1f}".format(float(rttPath) / 2.0)
            # lossPath = "{0:.2f}".format(np.random.uniform(low=loss[0], high=loss[1]))
            # queuingDelayPath = "{0:.3f}".format(np.random.uniform(low=queuingDelay[0], high=queuingDelay[1]))
            # tcpTopos.append({PATHS: [{BANDWIDTH: bandwidthPath, DELAY: delayPath}], NETEM: [(0, 0, "loss " + str(lossPath) + "%")]})
            # mptcpTopo[PATHS].append({BANDWIDTH: bandwidthPath, DELAY: delayPath, QUEUING_DELAY: queuingDelayPath})
            # mptcpTopo[NETEM].append((nbPath, 0, "loss " + str(lossPath) + "%"))
            pass

        mptcpTopos.append(mptcpTopo)
        reversedMptcpTopoPaths = mptcpTopo[PATHS][::-1]
        reversedMptcpTopoNetem = []
        nbPath = 0
        for netem in mptcpTopo[NETEM][::-1]:
            reversedMptcpTopoNetem.append((nbPath, netem[1], netem[2]))
            nbPath += 1

        reversedMptcpTopo = {PATHS: reversedMptcpTopoPaths, NETEM: reversedMptcpTopoNetem}
        mptcpTopos.append(reversedMptcpTopo)

    return mptcpTopos


def launchTests(times, dynamic_level):
    """ Notice that the loss must occur at time + 2 sec since the minitopo test waits for 2 seconds between launching the server and the client """
    # mptcpTopos = generateExperimentalDesignRandomTopos(nbMptcpTopos=200)
    # logging = open("topos_with_loss.log", 'w')
    # print(mptcpTopos, file=logging)
    # logging.close()

    # renyue: random bandwidth and delay for each topo
    bandwidth_min, bandwidth_max = 5.0, 15.0
    delay_min, delay_max = 2.0, 8.0

    mptcpTopos_random = []
    for _ in range(100):
        bandwidth_values = [round(random.uniform(bandwidth_min, bandwidth_max), 2) for _ in range(2)]
        delay_values = [round(random.uniform(delay_min, delay_max), 2) for _ in range(2)]
        topology = {
            'paths': [
            {'queuingDelay': '0.048', 'bandwidth': "%.2f" % bandwidth_values[0], 'delay': "%.2f" % delay_values[0], 'jitter': '0'},
            {'queuingDelay': '0.048', 'bandwidth': "%.2f" % bandwidth_values[1], 'delay': "%.2f" % delay_values[1], 'jitter': '0'}
            ],
            'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]
        }
        mptcpTopos_random.append(topology)

    # example
    mptcpTopos_test_act = [{'paths': [{'queuingDelay': '0.048', 'bandwidth': '5.00', 'delay': '60', 'jitter': '6'},
                             {'queuingDelay': '0.048', 'bandwidth': '10.00', 'delay': '30', 'jitter': '3'}],
                   # 'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
                    'netem': [(0, 0, 'loss 1.75%'), (1, 0, 'loss 1.75%')]},
    ]

    mptcpTopos_test = [{'paths': [{'queuingDelay': '0.048', 'bandwidth': '10.00', 'delay': '5', 'jitter': '0'},
                             {'queuingDelay': '0.048', 'bandwidth': '10.00', 'delay': '5', 'jitter': '0'}],
                   'netem': [(0, 0, 'loss 0.00%'), (1, 0, 'loss 0.00%')]},
    ]


    mptcpTopos_act = []
    for _ in range(30):
        topology = {
            'paths': [{'queuingDelay': '0.048', 'bandwidth': '5.00', 'delay': '60', 'jitter': '6'},
                      {'queuingDelay': '0.048', 'bandwidth': '10.00', 'delay': '30', 'jitter': '3'}],
            # 'netem': [(0, 0, 'loss 0%'), (1, 0, 'loss 0%')]
            'netem': [(0, 0, 'loss 1.75%'), (1, 0, 'loss 1.75%')]
        }
        mptcpTopos_act.append(topology)

    # for _ in range(40):
    #     topology = {
    #         'paths': [{'queuingDelay': '0.048', 'bandwidth': '2', 'delay': '240', 'jitter': '0'},
    #                   {'queuingDelay': '0.048', 'bandwidth': '10', 'delay': '30', 'jitter': '0'}],
    #         'netem': [(0, 0, 'loss 0%'), (1, 0, 'loss 0%')]
    #         # 'netem': [(0, 0, 'loss 3.5%'), (1, 0, 'loss 1.75%')]
    #     }
    #     mptcpTopos_act.append(topology)
        
    # renyue: for mqtt test
    path_1_bandwidth_min, path_1_bandwidth_max = 40.00, 50.00 # wifi
    path_2_bandwidth_min, path_2_bandwidth_max = 5.00, 10.00 # 4G
    path_1_rtt, path_2_rtt = 30, 100
    if dynamic_level == 'l': # low
        # low dynamic
        rtt_variation, loss_rate = 0.00, 0.00
    if dynamic_level == 'm': # medium
        # medium dynamic
        rtt_variation, loss_rate = 0.10, 1.75
    if dynamic_level == 'h': # high
        # high dynamic
        rtt_variation, loss_rate = 0.20, 3.00

    path_1_bandwidth_value = round(random.uniform(path_1_bandwidth_min, path_1_bandwidth_max), 2)
    path_2_bandwidth_value = round(random.uniform(path_2_bandwidth_min, path_2_bandwidth_max), 2)

    mptcpTopos_mqtt_random = [{'paths': [{'queuingDelay': '0.048', 'bandwidth': "%.2f" % path_1_bandwidth_value, 'delay': "%d" % path_1_rtt, 'jitter': "%f" % (path_1_rtt*rtt_variation)},
                                         {'queuingDelay': '0.048', 'bandwidth': "%.2f" % path_2_bandwidth_value, 'delay': "%d" % path_2_rtt, 'jitter': "%f" % (path_2_rtt*rtt_variation)}],
                                'netem': [(0, 0, "loss %f%%" % loss_rate), (1, 0, "loss %f%%" % loss_rate)]}]

    # TESTING START.............................
    # renyue: define mptopos by customize
    scheduler = 'rl_' + dynamic_level
    path_1_bandwidth = path_1_bandwidth_value
    path_1_delay = path_1_rtt
    scenario = "mpquic"
    print("--------------------------RENYUE----------------------")
    print("path 1 bandwidth: %.2f, rtt: %d, loss: %.2f" % (path_1_bandwidth, path_1_delay, loss_rate))
    print("path 2 bandwidth: %.2f, rtt: %d, loss: %.2f" % (path_2_bandwidth_value, path_2_rtt, loss_rate))
    print("--------------------------RENYUE----------------------")
    for i in range(times):
        quicTests(mptcpTopos_mqtt_random, scheduler, str(path_1_bandwidth), str(path_1_delay), scenario)
        time.sleep(1)

def run(dynamic_level):
    import core.core as core
    from log_fct_ofo import log_fct, log_ofo_avg, log_ofo_avg_nil

    launchTests(times=1, dynamic_level=dynamic_level)
    results_file_path = "/home/server/Desktop/rl_mpquic_scheduler/" + core.TEST_DIR + "/1/quic/1/quic_client.log"
    fct = log_fct(results_file_path)
    if fct == '6000':
        log_ofo_avg_nil(10000)
    else:
        log_ofo_avg(results_file_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run MPQUIC test with dynamic level")
    parser.add_argument('-d', '--dynamic_level', type=str, choices=['l', 'm', 'h'], required=True,
                        help="Dynamic level: l (low), m (medium), h (high)")
    args = parser.parse_args()

    run(args.dynamic_level)