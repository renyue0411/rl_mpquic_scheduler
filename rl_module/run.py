# scripts/main.py
import argparse
from scripts.train_infer import run

def main():
    parser = argparse.ArgumentParser(description="Train or Infer A2C agent for MPQUIC scheduling")
    parser.add_argument('--mode', type=str, choices=['train', 'infer'], required=True,
                        help="Mode to run: 'train' for training, 'infer' for inference")
    args = parser.parse_args()

    print(f"[Main] Starting {args.mode} mode...")
    run(args.mode)

if __name__ == '__main__':
    main()
