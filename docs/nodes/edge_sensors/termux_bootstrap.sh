#!/bin/bash
# --------------------------------------------------------------------
# Termux One-Click Bootstrap Script for Edge AI Nodes
# Usage: Run this script ONCE immediately after installing Termux on a new phone.
# --------------------------------------------------------------------

echo "🚀 Starting One-Click Termux Environment Bootstrap..."

echo "[1/6] 📥 Requesting Storage Permissions (Please click 'Allow' on the popup)..."
termux-setup-storage
sleep 3

echo "[2/6] 🌍 Switching to fast Tsinghua/BFSU mirror..."
termux-change-repo
# Note: The user may need to press ENTER a few times if the interactive prompt appears.
# We try to automate it for standard setups:
sed -i 's@^\(deb.*stable main\)$@#\1\ndeb https://mirrors.tuna.tsinghua.edu.cn/termux/termux-packages-24 stable main@' $PREFIX/etc/apt/sources.list
sed -i 's@^\(deb.*games stable\)$@#\1\ndeb https://mirrors.tuna.tsinghua.edu.cn/termux/game-packages-24 games stable@' $PREFIX/etc/apt/sources.list.d/game.list
sed -i 's@^\(deb.*science stable\)$@#\1\ndeb https://mirrors.tuna.tsinghua.edu.cn/termux/science-packages-24 science stable@' $PREFIX/etc/apt/sources.list.d/science.list

echo "[3/6] 📦 Updating packages & installing core dependencies (openssh, termux-api, python, rsync, tmux)..."
pkg update -y
pkg install openssh termux-api python rsync tmux jq unzip nmap -y

echo "[4/6] 🔑 Generating SSH keys (No password)..."
if [ ! -f ~/.ssh/id_rsa ]; then
    ssh-keygen -t rsa -b 2048 -f ~/.ssh/id_rsa -N ""
    echo "SSH keys generated successfully."
else
    echo "SSH keys already exist, skipping."
fi

echo "[5/6] 🔌 Starting SSH Daemon (port 8022)..."
sshd
echo "sshd is now running."

echo "[6/6] 🔋 Enabling Wake Lock (Preventing background sleep)..."
termux-wake-lock
echo "Wake lock enabled."

echo "--------------------------------------------------------------------"
echo "✅ Bootstrap Complete!"
echo "Your IP address is: $(ifconfig | grep -A 1 'wlan0' | grep 'inet ' | awk '{print $2}')"
echo "Your username is: $(whoami)"
echo "You can now connect to this phone from Mac via: ssh -p 8022 $(whoami)@<ip_address>"
echo "Don't forget to run 'cat ~/.ssh/id_rsa.pub' to add this phone's key to your servers."
echo "--------------------------------------------------------------------"
