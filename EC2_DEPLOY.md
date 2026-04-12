# EC2 Deployment Guide

## Overview

Deploy the bumblebee evaluation server on a standalone EC2 instance. Two modes run simultaneously on different ports:

| Mode | URL | Images |
|------|-----|--------|
| Full | `http://<IP>/?PARTICIPANT_ID=...` | 150 |
| Calibration | `http://<IP>:8080/?PARTICIPANT_ID=...` | 10 |

---

## AWS Console Setup

### 1. Launch EC2 Instance

1. Log into AWS Console → search "EC2" → **Launch Instance**
2. Configure:

| Setting | Value |
|---------|-------|
| Name | `bumblebee-eval-server` |
| AMI | Ubuntu Server 22.04 LTS |
| Instance type | `t3.micro` |
| Key pair | Create new → download `.pem` file |
| Storage | 8 GB gp3 (default) |

### 2. Security Group

Add these inbound rules:

| Type | Port | Source | Purpose |
|------|------|--------|---------|
| SSH | 22 | My IP | SSH access |
| HTTP | 80 | Anywhere | Full evaluation |
| Custom TCP | 8080 | Anywhere | Calibration evaluation |

### 3. Elastic IP

1. EC2 → Elastic IPs → **Allocate Elastic IP address**
2. Select it → Actions → **Associate** → pick your instance

---

## Server Setup

### 4. SSH In

```bash
chmod 400 ~/Downloads/<your-key>.pem
ssh -i ~/Downloads/<your-key>.pem ubuntu@<ELASTIC_IP>
```

### 5. Install Dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx git
```

### 6. Get the Code

Option A - Git clone:
```bash
cd /home/ubuntu
git clone <YOUR_REPO_URL> eval_server
```

Option B - Upload from local:
```bash
# Run from your Mac
scp -i ~/Downloads/<your-key>.pem -r eval_server/ ubuntu@<ELASTIC_IP>:/home/ubuntu/eval_server
```

### 7. Python Environment

```bash
cd /home/ubuntu/eval_server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mkdir -p logs instance flask_session
```

### 8. Nginx

```bash
sudo cp nginx.ec2.conf /etc/nginx/nginx.conf
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 9. Systemd Services

**Full mode** (port 80):
```bash
sudo tee /etc/systemd/system/bumblebee-eval-full.service <<EOF
[Unit]
Description=Bumblebee Eval - Full Mode
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/eval_server
ExecStart=/home/ubuntu/eval_server/venv/bin/gunicorn -c gunicorn_config.py wsgi:app
Restart=always
RestartSec=3
Environment="EVAL_MODE=full"

[Install]
WantedBy=multi-user.target
EOF
```

**Calibration mode** (port 8080):
```bash
sudo tee /etc/systemd/system/bumblebee-eval-calibration.service <<EOF
[Unit]
Description=Bumblebee Eval - Calibration Mode
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/eval_server
ExecStart=/home/ubuntu/eval_server/venv/bin/gunicorn -c gunicorn_config_calibration.py wsgi:app
Restart=always
RestartSec=3
Environment="EVAL_MODE=calibration"

[Install]
WantedBy=multi-user.target
EOF
```

**Start both:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable bumblebee-eval-full bumblebee-eval-calibration
sudo systemctl start bumblebee-eval-full bumblebee-eval-calibration
```

### 10. Verify

```bash
sudo systemctl status bumblebee-eval-full
sudo systemctl status bumblebee-eval-calibration
curl http://localhost/status
curl http://localhost:8080/status
```

---

## URLs for Experts

```
Full:        http://<ELASTIC_IP>/?PARTICIPANT_ID=expert_1&STUDY_ID=main&SESSION_ID=1
Calibration: http://<ELASTIC_IP>:8080/?PARTICIPANT_ID=expert_1&STUDY_ID=pilot&SESSION_ID=1
```

---

## Managing Services

```bash
# Status
sudo systemctl status bumblebee-eval-full
sudo systemctl status bumblebee-eval-calibration

# Restart (after code changes)
sudo systemctl restart bumblebee-eval-full
sudo systemctl restart bumblebee-eval-calibration

# Stop one
sudo systemctl stop bumblebee-eval-calibration

# Live logs
sudo journalctl -u bumblebee-eval-full -f
sudo journalctl -u bumblebee-eval-calibration -f
```

## Updating Code

```bash
cd /home/ubuntu/eval_server
git pull
sudo systemctl restart bumblebee-eval-full
sudo systemctl restart bumblebee-eval-calibration
```

## Export Results

```bash
# From browser
http://<ELASTIC_IP>/export              # full mode results
http://<ELASTIC_IP>:8080/export         # calibration results

# From EC2
curl http://localhost/export -o results_full.csv
curl http://localhost:8080/export -o results_calibration.csv

# Download to your Mac
scp -i ~/Downloads/<your-key>.pem \
  ubuntu@<ELASTIC_IP>:/home/ubuntu/eval_server/instance/bumblebee_evaluation_full.db \
  ~/Desktop/
```

## Backup Database

```bash
# On EC2
cp instance/bumblebee_evaluation_full.db instance/backup_$(date +%Y%m%d).db

# Download to Mac
scp -i ~/Downloads/<your-key>.pem \
  ubuntu@<ELASTIC_IP>:/home/ubuntu/eval_server/instance/*.db \
  ~/Desktop/
```

## Data Persistence

| Action | Data safe? |
|--------|-----------|
| Reboot / restart instance | Yes |
| Stop / start instance | Yes |
| **Terminate** instance | **No** - back up first |

## Cost

| Resource | Cost |
|----------|------|
| t3.micro (free tier, 1st year) | $0/mo |
| t3.micro (after free tier) | ~$8/mo |
| Elastic IP (instance running) | $0 |
| Elastic IP (instance stopped) | ~$3.60/mo |
| EBS 8 GB | ~$0.80/mo |

> **Stop** the instance when not collecting evaluations. **Never terminate** unless you've backed up.
