#!/bin/bash
# VM Setup Script for Semantic Email CLI

set -e

echo "=== Setting up VM for Semantic Email CLI ==="

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.10+ and development tools
sudo apt-get install -y python3.10 python3.10-venv python3.10-dev python3-pip
sudo apt-get install -y git curl wget build-essential

# Create application directory
sudo mkdir -p /app/semantic-email-cli
sudo chown $USER:$USER /app/semantic-email-cli
cd /app/semantic-email-cli

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install PyTorch CPU (optimized for CPU-only usage)
pip install --upgrade pip
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install sentence transformers and FAISS
pip install sentence-transformers
pip install faiss-cpu

# Install CLI and utility packages
pip install typer rich click
pip install python-dotenv
pip install psutil

# Install email libraries
pip install imaplib2

# Install development tools
pip install pytest pytest-cov

# Create log directory
sudo mkdir -p /var/log/semantic-email-cli
sudo chown $USER:$USER /var/log/semantic-email-cli

# Create systemd service file
sudo tee /etc/systemd/system/semantic-email-cli.service > /dev/null <<EOF
[Unit]
Description=Semantic Email CLI Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/app/semantic-email-cli
ExecStart=/app/semantic-email-cli/venv/bin/python main.py
Restart=always
RestartSec=10
Environment=PATH=/app/semantic-email-cli/venv/bin
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable the service (don't start it yet - needs configuration)
sudo systemctl daemon-reload
sudo systemctl enable semantic-email-cli.service

echo "✅ VM setup complete!"
echo "Next steps:"
echo "1. Copy your project files to /app/semantic-email-cli"
echo "2. Configure .env file with your email credentials"
echo "3. Test the application: python main.py status"
echo "4. Start the service: sudo systemctl start semantic-email-cli"
