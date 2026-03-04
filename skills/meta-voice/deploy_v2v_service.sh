#!/bin/bash
# deploy_v2v_service.sh
# Run this script on the Remote GPU Server (10.190.30.220) to install V2V as a background systemd service.

SERVICE_NAME="meta-v2v"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
V2V_DIR="/tmp/meta_voice_daemon" # We will deploy the script here for the service
PORT=8001

echo "🎙️  Setting up Meta Voice V2V Daemon..."

# Ensure we are running as root
if [ "$EUID" -ne 0 ]; then 
  echo "Please run as root"
  exit 1
fi

# 1. Create a stable directory for the Daemon script if it doesn't exist
mkdir -p ${V2V_DIR}
echo "Copying v2v_server.py to ${V2V_DIR}..."
cp v2v_server.py ${V2V_DIR}/

# 2. Write the systemd service file
echo "Writing systemd service file to ${SERVICE_FILE}..."
cat << EOF > ${SERVICE_FILE}
[Unit]
Description=Meta Voice V2V Translation API Daemon
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${V2V_DIR}
Environment="PATH=/root/miniconda3/envs/v2v/bin:$PATH"
ExecStart=/root/miniconda3/envs/v2v/bin/uvicorn v2v_server:app --host 0.0.0.0 --port ${PORT}
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 3. Reload systemd, enable, and start the service
echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Enabling and starting ${SERVICE_NAME}.service..."
systemctl enable ${SERVICE_NAME}
systemctl start ${SERVICE_NAME}

echo "✅ Deployment Complete!"
echo "The V2V API is now running persistently in the background on port ${PORT}."
echo ""
echo "Helpful commands:"
echo "  Check status: systemctl status ${SERVICE_NAME}"
echo "  View logs:    journalctl -u ${SERVICE_NAME} -f"
echo "  Stop service: systemctl stop ${SERVICE_NAME}"
