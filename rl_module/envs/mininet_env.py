# envs/mininet_env.py
import os
import time
import numpy as np

class MPQUICEnv:
    def __init__(self, topo_script_path, quic_client_path, log_dir):
        """
        初始化环境
        :param topo_script_path: 启动Mininet的Python脚本路径
        :param quic_client_path: 启动mpquic-go客户端的脚本路径
        :param log_dir: 保存FCT、Loss、OFO等日志的目录
        """
        self.topo_script_path = topo_script_path
        self.quic_client_path = quic_client_path
        self.log_dir = log_dir
        self.flag_file = os.path.join(log_dir, "flag.txt")
        self.fct_log = os.path.join(log_dir, "fct.log")
        self.loss_log = os.path.join(log_dir, "loss.log")
        self.ofo_log = os.path.join(log_dir, "ofo.log")

    def reset(self):
        """
        启动Mininet拓扑，准备传输
        """
        # 启动Mininet拓扑
        os.system(f"sudo python3 {self.topo_script_path}")

        # 清理旧日志
        if os.path.exists(self.fct_log):
            os.remove(self.fct_log)
        if os.path.exists(self.loss_log):
            os.remove(self.loss_log)
        if os.path.exists(self.ofo_log):
            os.remove(self.ofo_log)

        # 启动mpquic-go客户端（开始传输）
        os.system(f"{self.quic_client_path} &")

        # 等待实验开始标志（可以用flag文件，或者自己实现socket同步）

    def wait_file_complete(self):
        """
        等待一次文件传输完成，通过flag机制
        """
        while not os.path.exists(self.flag_file):
            time.sleep(0.2)
        os.remove(self.flag_file)

    def read_logs(self):
        """
        读取fct, loss, ofo日志，返回奖励相关信息
        """
        fct = self._read_single_value(self.fct_log, default=1000.0)
        loss = self._read_single_value(self.loss_log, default=0.01)
        ofo = self._read_single_value(self.ofo_log, default=0.01)
        return fct, loss, ofo

    def _read_single_value(self, filepath, default=0.0):
        if not os.path.exists(filepath):
            return default
        with open(filepath, 'r') as f:
            lines = f.readlines()
        if not lines:
            return default
        return float(lines[-1].strip())

    def compute_file_reward(self, fct, loss, ofo):
        """
        根据文件传输统计数据，计算一个总奖励
        """
        reward = -(0.7 * fct / 1000.0 + 0.2 * loss + 0.1 * ofo)
        return reward

    def close(self):
        """
        关闭Mininet拓扑，释放资源
        """
        os.system("sudo mn -c")  # 清理Mininet