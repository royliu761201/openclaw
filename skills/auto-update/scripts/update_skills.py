import os
import subprocess

def update_skills():
    skills_dir = os.path.join(os.getcwd(), 'skills')
    print(f"Checking for updates in {skills_dir}...")
    
    for skill in os.listdir(skills_dir):
        skill_path = os.path.join(skills_dir, skill)
        if os.path.isdir(skill_path):
            print(f"\nUpdating {skill}...")
            # Check for git
            if os.path.exists(os.path.join(skill_path, '.git')):
                try:
                    subprocess.run(['git', 'pull'], cwd=skill_path, check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Git pull failed for {skill}: {e}")
            
            # Check for npm
            if os.path.exists(os.path.join(skill_path, 'package.json')):
                try:
                    subprocess.run(['npm', 'update'], cwd=skill_path, check=True, shell=True)
                except subprocess.CalledProcessError as e:
                    print(f"Npm update failed for {skill}: {e}")

if __name__ == "__main__":
    update_skills()
