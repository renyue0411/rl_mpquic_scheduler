# scripts/main.py
import argparse
import threading
import torch
import os

from rl_module.scripts.unix_socket import UnixSocketServer
from rl_module.envs.mininet_env import MininetEnv
from rl_module.a2c import a2c_agent
from rl_module.a2c.utils import MODEL_SAVE_PATH

def main():
    parser = argparse.ArgumentParser(description="Train or Infer A2C agent for MPQUIC scheduling")
    parser.add_argument('--mode', type=str, choices=['train', 'infer'], required=True,
                        help="Mode to run: 'train' for training, 'infer' for inference")
    args = parser.parse_args()
    print(f"[Main] Starting {args.mode} mode...")

    # load model in infer mode
    if args.mode == 'infer':
        model_path = MODEL_SAVE_PATH + "actor_critic_final.pth"
        if os.path.exists(model_path):
            a2c_agent.load_model(model_path)
            print(f"[Main] Loaded model from {model_path}")
        else:
            raise FileNotFoundError(f"[Main] No model found at {model_path}")

    # create a thread of socket server for receive path states from quic-go
    socket_server = UnixSocketServer(module_mode=args.mode)
    socket_thread = threading.Thread(target=socket_server.start, daemon=True)
    socket_thread.start()

    episodes = 300
    # run Mininet enviroment
    for episode in range(1, episodes+1):
        if episode <= episodes/3:
            dynamic_level = 'l' # Low
        elif episode <= 2 * episodes/3:
            dynamic_level = 'm' # Medium
        else:
            dynamic_level = 'h' # High

        mininet_env = MininetEnv(dynamic_level)
        mininet_env.start()
        # mininet_env.close()

        # save models once every 1/3 episodes
        if args.mode == 'train':
            if episode % (episodes // 3) == 0 or episode == episodes:
                model_save_path = MODEL_SAVE_PATH + f"actor_critic_ep{episode}.pth"
                torch.save(a2c_agent.model.state_dict(), model_save_path)
                print(f"[Main] Model saved at episode {episode}")

    # save final model after train
    if args.mode == 'train':
        model_save_path = MODEL_SAVE_PATH + "actor_critic_final.pth"
        torch.save(a2c_agent.model.state_dict(), model_save_path)
        print(f"[Main] Final model saved")
        
if __name__ == '__main__':
    main()
