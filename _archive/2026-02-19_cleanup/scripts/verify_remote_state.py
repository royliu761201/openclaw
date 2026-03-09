import asyncio
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'research_tools'))
from skills.ssh_executor import SSHExecutor

async def main():
    executor = SSHExecutor()
    print("🔍 Auditing Remote Environment...")
    
    # 1. Check Conda Envs
    print("\n[1] Checking Conda Environments:")
    cmd_conda = "source /root/miniconda3/etc/profile.d/conda.sh && conda env list"
    res = await executor.execute_command(cmd_conda)
    print(res.get("stdout"))
    
    # 2. Check Shared Data & Models
    print("\n[2] Checking Shared Storage (/root/research_bot/data & models):")
    cmd_ls = "ls -F /root/research_bot/data/ /root/research_bot/models/ 2>/dev/null"
    res = await executor.execute_command(cmd_ls)
    print(res.get("stdout"))

    # 3. Check Project Links
    print("\n[3] Checking Project Symlinks:")
    projects = ["pesso", "calam", "frenet", "medtime", "cogd"]
    for p in projects:
        cmd_link = f"ls -l /root/research_bot/projects/{p}/data 2>/dev/null"
        res = await executor.execute_command(cmd_link)
        output = res.get("stdout").strip()
        if output:
            print(f"   {p}: {output}")
        else:
            print(f"   {p}: ⚠️ No data link found.")

if __name__ == "__main__":
    asyncio.run(main())
