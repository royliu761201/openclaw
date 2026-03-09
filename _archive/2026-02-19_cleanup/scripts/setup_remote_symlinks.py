import asyncio
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'research_tools'))
from skills.ssh_executor import SSHExecutor

async def main():
    executor = SSHExecutor()
    print("🔗 Configuring Remote Symlinks (Standardizing Structure)...")
    
    projects = ["pesso", "calam", "frenet", "medtime", "cogd"]
    central_models = "/root/research_bot/models"
    central_data_base = "/root/research_bot/data"
    
    # Ensure central folders exist
    await executor.execute_command(f"mkdir -p {central_models}")
    await executor.execute_command(f"mkdir -p {central_data_base}")
    
    for p in projects:
        print(f"\nProcessing project: {p}...")
        project_root = f"/root/research_bot/projects/{p}"
        
        # 1. Models Symlink
        # Link project/models -> central/models
        # Force link (ln -sf) to ensure correctness
        cmd_link_models = f"ln -sf {central_models} {project_root}/models"
        await executor.execute_command(cmd_link_models)
        print("   ✅ Linked models -> /root/research_bot/models")
        
        # 2. Data Symlink
        # Link project/data -> central/data/[project_name]
        # First ensure the central data dir exists for this project
        target_data_dir = f"{central_data_base}/{p}"
        await executor.execute_command(f"mkdir -p {target_data_dir}")
        
        # Now link
        # Note: If project/data already exists as a directory, we might need to move it?
        # For safety, let's check if it exists and is a directory (not a link)
        check_cmd = f"if [ -d {project_root}/data ] && [ ! -L {project_root}/data ]; then echo 'DIR_EXISTS'; fi"
        res = await executor.execute_command(check_cmd)
        
        if "DIR_EXISTS" in res.get("stdout", ""):
            print("   ⚠️  Existing data directory found via 'data'. Moving contents to central storage first...")
            # Move contents to central location
            move_cmd = f"mv {project_root}/data/* {target_data_dir}/ 2>/dev/null"
            await executor.execute_command(move_cmd)
            # Remove the now empty (or nearly empty) dir
            await executor.execute_command(f"rm -rf {project_root}/data")
            print("   ✅ Moved data to central storage.")
            
        # Create link
        cmd_link_data = f"ln -sf {target_data_dir} {project_root}/data"
        await executor.execute_command(cmd_link_data)
        print(f"   ✅ Linked data -> {target_data_dir}")

    print("\n🎉 All Remote Symlinks Configured.")

if __name__ == "__main__":
    asyncio.run(main())
