# MPQUIC Scheduler with A2C Reinforcement Learning

## 📖 Project Overview

This project implements an intelligent scheduler based on the A2C (Advantage Actor Critic) reinforcement learning algorithm to optimize file transmission over MPQUIC (Multi-Path QUIC).  
The scheduler dynamically selects the optimal path for each data packet based on real-time path status (e.g., RTT, CWND, packet loss) to minimize transmission time, loss, and out-of-order packets.

The system consists of:
- **Mininet**: to emulate multi-path network topologies
- **mpquic-go**: real MPQUIC transport protocol stack
- **A2C Agent**: decision-making model for packet-level path selection
- **Python Server**: handles state collection, action inference, and model training

---

## 🚀 Quick Start

### 1. Environment Setup

```bash
sudo apt-get install mininet
pip install torch numpy
```

Make sure **mpquic-go** is correctly installed and configured.

---

### 2. Launching the System

#### 2.1 Start `run_unix_socket.py`
```bash
python3 scripts/run_unix_socket.py
```

#### 2.2 Train the Model
```bash
python3 scripts/main.py --mode train
```

#### 2.3 Run Inference
```bash
python3 scripts/main.py --mode infer
```

---

## ⚙️ Configuration

- Mininet topology launcher: in `envs/mininet_env.py`
- mpquic-go client launcher: in `envs/mininet_env.py`
- Log output: `log/`
- Model output: `models/`
- Unix socket path: `/tmp/mpquic_socket`

---

## 🎯 Reward Definition

- **Small reward (per packet)**: negative sum of queue sizes
- **Big reward (per file transmission)**:

\[
reward = -(0.7 \times FCT_{norm} + 0.2 \times Loss + 0.1 \times OFO)
\]

---

## 📌 Notes

- Always start `run_unix_socket.py` **before** training or inference.
- Rewards and models are saved automatically during training.
- If the model is missing during inference, an error will occur.
- Mininet topology is reset at each environment reset.

---

## ✨ Future Work

- Support for PPO, DQN and other RL algorithms
- Multi-file batch training support
- Asynchronous A3C with multiple workers
- QoS-aware adaptive scheduling
