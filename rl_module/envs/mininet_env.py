import os
import time
import numpy as np

from minitopo.evaluation import run as mininet_run
import config
from config import METRICS_DIR


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
        # Remove old Mininet logs
        if os.path.exists(self.fct_log):
            os.remove(self.fct_log)
        if os.path.exists(self.ofo_log):
            os.remove(self.ofo_log)

        # Run mininet topo
        results_path = mininet_run(self.dynamic_level)
        self._read_metrics_log(results_path)
        self._set_file_complete()
        return

    def _set_file_complete(self):
        """
        Set (flag = True) that a file transmission complete
        """
        config.FILE_COMPLETE_FLAG = True

    def close(self):
        """
        Clean Mininet cache
        """
        os.system("sudo mn -c")