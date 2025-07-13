# GCP Setup Instructions - Manual Installation

## Prerequisites

Your network appears to have connectivity issues with Google services. You'll need to:

1. **Install gcloud CLI manually:**
   - Download from: https://cloud.google.com/sdk/docs/install
   - Or use a different network/VPN if blocked

2. **Once gcloud is installed, run these commands:**

```bash
# Step 1: Authenticate with GCP
gcloud auth login

# Step 2: Create a new project
PROJECT_ID="semantic-email-cli-$(date +%s)"
gcloud projects create $PROJECT_ID
gcloud config set project $PROJECT_ID

# Step 3: Enable billing (you'll need to do this manually in console)
echo "Enable billing at: https://console.cloud.google.com/billing/projects"

# Step 4: Enable required APIs
gcloud services enable compute.googleapis.com

# Step 5: Set region and zone
gcloud config set compute/region asia-south1
gcloud config set compute/zone asia-south1-c

# Step 6: Create firewall rules
gcloud compute firewall-rules create allow-ssh --allow tcp:22 --source-ranges 0.0.0.0/0
gcloud compute firewall-rules create allow-http --allow tcp:80 --source-ranges 0.0.0.0/0
gcloud compute firewall-rules create allow-https --allow tcp:443 --source-ranges 0.0.0.0/0

# Step 7: Create VM instance
gcloud compute instances create semantic-email-vm \
    --zone=asia-south1-c \
    --machine-type=e2-medium \
    --boot-disk-size=30GB \
    --boot-disk-type=pd-standard \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --tags=http-server,https-server

# Step 8: Get VM IP
gcloud compute instances describe semantic-email-vm --zone=asia-south1-c --format='get(networkInterfaces[0].accessConfigs[0].natIP)'

# Step 9: SSH into VM
gcloud compute ssh semantic-email-vm --zone=asia-south1-c
```

## VM Setup Commands (run inside VM)

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and dependencies
sudo apt-get install -y python3.10 python3.10-venv python3.10-dev python3-pip
sudo apt-get install -y git curl wget build-essential

# Create application directory
sudo mkdir -p /app/semantic-email-cli
sudo chown $USER:$USER /app/semantic-email-cli
cd /app/semantic-email-cli

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install PyTorch CPU
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
pip install sentence-transformers faiss-cpu
pip install typer rich python-dotenv psutil
```

## Deploy Your Application

```bash
# Copy your project files to VM (from local machine)
gcloud compute scp --recurse /home/cykosynergy/projects/semantic_email_cli/* semantic-email-vm:/app/semantic-email-cli/ --zone=asia-south1-c

# SSH into VM and setup
gcloud compute ssh semantic-email-vm --zone=asia-south1-c

# Inside VM:
cd /app/semantic-email-cli
source venv/bin/activate
pip install -r requirements.txt

# Create .env file
nano .env
# Add your Gmail credentials:
# EMAIL_USER=your.email@gmail.com
# EMAIL_PASSWORD=your-app-password
# EMAIL_PROVIDER=gmail

# Test the application
python main.py status
```

## Cost Estimate
- e2-medium VM: ~$30-50/month
- 30GB standard disk: ~$2/month
- Network egress: ~$1-5/month
- **Total: ~$35-60/month**

## Next Steps
1. Fix network connectivity or use VPN
2. Install gcloud CLI
3. Run the commands above
4. Deploy your application
