import os
import subprocess
import time

import rl_module.envs.config as config
from rl_module.envs.config import METRICS_DIR, RUN_PATH


class MininetEnv:
    def __init__(self, dynamic_level, metric_dir=METRICS_DIR):
        """
        init Mininet enviroment
        :param run_path: file path of Mininet script file
        :param metric_dir: the directory for saving logs of FCT and OFO
        """
        self.dynamic_level = dynamic_level
        self.metric_dir = metric_dir
        self.fct_log = os.path.join(metric_dir, "fct.log")
        self.ofo_log = os.path.join(metric_dir, "ofo.log")

    def start(self):
        """
        run Mininet topo for mpquic test
        """
        # Run mininet topo
        print("[Mininet] Minitopo running")
        subprocess.run(['python2.7',
                        RUN_PATH,
                        '-d',
                        self.dynamic_level])
        # File transfer complete
        config.set_file_complete_flag(True)
        print(f"[Mininet] file transfer completed, status: {config.FILE_COMPLETE_FLAG}")
        return

    def _set_file_status(self, status):
        """
        Set (flag = True or Flase) that a file transmission status
        """
        config.FILE_COMPLETE_FLAG = status

    def close(self):
        """
        Clean Mininet cache
        """
        os.system("sudo mn -c")
        print("[Mininet] Cache cleand")