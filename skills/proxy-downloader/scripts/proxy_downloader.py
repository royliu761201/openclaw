#!/usr/bin/env python3
import subprocess
import argparse
import sys
import os

def run_cmd(cmd, check=True):
    print(f"✅ 执行: {cmd}")
    res = subprocess.run(cmd, shell=True)
    if check and res.returncode != 0:
        print(f"❌ 命令失败 (Exit {res.returncode}): {cmd}")
        sys.exit(1)
    return res.returncode

def main():
    parser = argparse.ArgumentParser(description="全局代理下载与多跳安全热备工具")
    parser.add_argument("url", help="要下载的远程文件 URL")
    parser.add_argument("filename", help="保存的文件名 (如 model.bin)")
    parser.add_argument("--backup_dir", default="~/.openclaw_backups/downloads", help="Mac 03 (roy-003) 上的备份目录")
    
    args = parser.parse_args()
    
    url = args.url
    filename = args.filename
    backup_dir = args.backup_dir
    
    # Windows Exit Node (roy-005) Config
    win_host = "roy-005@100.98.236.51"
    win_ssh_opts = "-o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519"
    
    # Mac 03 (roy-003) Config
    mac03_host = "roy-003"
    mac03_ssh_opts = "-o StrictHostKeyChecking=no"
    
    print("\n" + "="*50)
    print(f"🚀 [阶段 1] 启动海外节点极速下载...")
    print(f"📍 目标: {win_host}")
    print(f"📦 文件: {filename}")
    print("="*50)
    
    # 1. 在 Windows 节点上通过 curl 下载文件
    download_cmd = f'ssh {win_ssh_opts} {win_host} "curl.exe -L -k -o {filename} \\"{url}\\""'
    run_cmd(download_cmd)
    
    print("\n" + "="*50)
    print(f"🔄 [阶段 2] 将文件拉取到本地临时中转区...")
    print(f"📥 路径: /tmp/{filename}")
    print("="*50)
    
    # 2. 将文件从 Windows 节点 SCP 回本地 /tmp
    pull_cmd = f'scp {win_ssh_opts} {win_host}:{filename} /tmp/{filename}'
    run_cmd(pull_cmd)
    
    print("\n" + "="*50)
    print(f"🛡️ [阶段 3] 安全转储至 Mac 03 (roy-003) 堡垒机静默热备...")
    print(f"📤 目标: {mac03_host}:{backup_dir}/{filename}")
    print("="*50)
    
    # 3. 将文件推送到 Mac 03
    run_cmd(f'ssh {mac03_ssh_opts} {mac03_host} "mkdir -p {backup_dir}"')
    push_cmd = f'scp {mac03_ssh_opts} /tmp/{filename} {mac03_host}:{backup_dir}/{filename}'
    run_cmd(push_cmd)
    
    print("\n" + "="*50)
    print(f"🧹 [阶段 4] 物理抹除痕迹，零占用还原系统...")
    print("="*50)
    
    # 4. 删除 Windows 节点上的源文件
    del_win_cmd = f'ssh {win_ssh_opts} {win_host} "del {filename}"'
    run_cmd(del_win_cmd, check=False) # 即使删除失败也只是警告
    
    # 5. 删除本地主控机的缓存
    run_cmd(f'rm -f /tmp/{filename}')
    
    print("\n🎉 [任务圆满完成] 全局链路断链清理完毕。")
    print(f"💾 最终成果安全坐落于: {mac03_host}:{backup_dir}/{filename}\n")

if __name__ == "__main__":
    main()
