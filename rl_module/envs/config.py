RUN_PATH = '/home/server/Desktop/rl_mpquic_scheduler/minitopo/evaluation.py'
METRICS_DIR = '/home/server/Desktop/rl_mpquic_scheduler/minitopo/metrics_log'
FILE_COMPLETE_FLAG = False

def set_file_complete_flag(value: bool):
    global FILE_COMPLETE_FLAG
    FILE_COMPLETE_FLAG = value

def get_file_complete_flag() -> bool:
    return FILE_COMPLETE_FLAG
