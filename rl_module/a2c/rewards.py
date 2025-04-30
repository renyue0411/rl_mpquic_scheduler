CWND_WEIGHT = 0.4
QUEUE_WEIGHT = 0.3
LOSS_WEIGHT = 0.3

FCT_WEIGHT = 0.5
OFO_WEIGHT = 0.5

def per_packet_reward(path_status_list):
    """
    calculate reward per packet by CWND utilization, queue size, loss rate
    """
    cwnd_total = sum(p['CWND'] for p in path_status_list)
    queue_total = sum(p['QueueSize'] for p in path_status_list)
    send_total = sum(p['Send'] for p in path_status_list)
    retrans_total = sum(p['Retrans'] for p in path_status_list)
    lost_total = sum(p['Lost'] for p in path_status_list)
    received_total = sum(p['Received'] for p in path_status_list)
    packet_size = path_status_list[0]['PacketSize']

    cwnd_utilization = ((send_total - received_total) * packet_size) / max(1, cwnd_total)
    queue_size = queue_total / 10000
    loss_rate = (lost_total + retrans_total) / max(1, (lost_total + retrans_total + send_total))
    reward = -(
        QUEUE_WEIGHT * queue_size +
        LOSS_WEIGHT * loss_rate -
        CWND_WEIGHT * cwnd_utilization
        )
    return reward

def per_file_reward(fct, ofo):
    """
    calculate reward per file by file complete time and out-of-order bytes
    """
    reward = -(
        FCT_WEIGHT * (fct/100) +
        OFO_WEIGHT * (ofo/100)
    )
    return reward
