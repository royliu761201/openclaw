#!/bin/bash
# OpenClaw 24/7 Battle State Guard (caffeinate)
echo "🚀 注入咖啡因，开启 24/7 战斗模式 (系统/磁盘/闲置不眠)..."
# -i: idle sleep, -s: system sleep, -m: disk sleep
# Excluding -d to allow display to sleep as requested.
nohup caffeinate -ism > /tmp/caffeinate.log 2>&1 &
