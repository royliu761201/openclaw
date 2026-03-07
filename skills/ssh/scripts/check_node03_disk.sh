#!/bin/bash
SSH_HOST=03 python3 /Users/roy-jd/Documents/projects/openclaw/skills/ssh/scripts/ssh_tool.py exec 'df -h | grep -v map; ls -la /Volumes' > /tmp/node03_disk_info.txt
