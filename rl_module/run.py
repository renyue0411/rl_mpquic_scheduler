# scripts/main.py
import argparse
import threading

from scripts.unix_socket import UnixSocketServer
from envs.mininet_env import MininetEnv

def main():
    parser = argparse.ArgumentParser(description="Train or Infer A2C agent for MPQUIC scheduling")
    parser.add_argument('--mode', type=str, choices=['train', 'infer'], required=True,
                        help="Mode to run: 'train' for training, 'infer' for inference")
    args = parser.parse_args()
    print(f"[Main] Starting {args.mode} mode...")

    # create a thread of socket server for receive path states from quic-go
    socket_server = UnixSocketServer(module_mode=args.mode)
    socket_thread = threading.Thread(target=socket_server.start, daemon=True)
    socket_thread.start()

    # run Mininet enviroment
    for episode in range(100):
        episode += 1

        mininet_env = MininetEnv()
        mininet_env.start()
        mininet_env.close()

if __name__ == '__main__':
    main()
