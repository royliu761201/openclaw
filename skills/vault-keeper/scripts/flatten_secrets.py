import json
import os

OLD_SECRETS_PATH = "/Users/roy-jd/Documents/projects/secrets.json"
NEW_SECRETS_PATH = "/Users/roy-jd/Documents/projects/secrets_flat.json"

def flatten_secrets():
    print("Flattening secrets.json into a key-value format...")
    if not os.path.exists(OLD_SECRETS_PATH):
        print("secrets.json not found!")
        return

    with open(OLD_SECRETS_PATH, "r", encoding="utf-8") as f:
        old = json.load(f)

    new_secrets = {
        # Cloud & AI Providers
        "HF_TOKEN": old.get("hf_token") or old.get("HF_TOKEN"),
        "WANDB_API_KEY": old.get("wandb_api_key") or old.get("WANDB_API_KEY"),
        "GITHUB_TOKEN": old.get("github_token"),
        "GOOGLE_API_KEY": "AIzaSyCERCZwwRSPP2VMtCa2CaoIDIbEMV6v7W8", # Cleaned up from JSON quotes
        "VERTEX_API_KEY": old.get("google_vertex_api_key"),
        "VERTEX_PROJECT": old.get("google_vertex_project"),
        
        # Groq
        "GROQ_API_KEY": old.get("groq", {}).get("keys", [""])[0],
        
        # Global Auth
        "GLOBAL_SSH_PASS": "~lxh797612011012",
        "GPU_SERVER_PASS": "d$LgO7gljR0q9oWH$p!s%0H1WyNY8pnl",
        "VPN_ACCOUNT_PRI": "SKL03",
        "VPN_PASSWORD_PRI": "Skl@2026",
        "VPN_ACCOUNT_BAK": "SKL16",
        "VPN_PASSWORD_BAK": "Skl@2025",
        
        # Apps
        "KAGGLE_XIAOHUALIU_KEY": old.get("kaggle", {}).get("xiaohualiu"),
        "KAGGLE_ROYLXH_KEY": old.get("kaggle", {}).get("roylxh5147"),
        
        "FEISHU_RESEARCH_APP_ID": old.get("feishu", {}).get("accounts", {}).get("research", {}).get("appId"),
        "FEISHU_RESEARCH_APP_SECRET": old.get("feishu", {}).get("accounts", {}).get("research", {}).get("appSecret"),
        "FEISHU_WORK_APP_ID": old.get("feishu", {}).get("accounts", {}).get("work", {}).get("appId"),
        "FEISHU_WORK_APP_SECRET": old.get("feishu", {}).get("accounts", {}).get("work", {}).get("appSecret"),
        
        "GMAIL_APP_PASS": old.get("gmail_password"),
        "ACADEMIC_EMAIL_PASS": old.get("ACADEMIC_EMAIL_PASS"),
        "PERSONAL_126_PASS": old.get("CPOLAR_PASSWORD"),
        
        "GOG_OAUTH_CLIENT_ID": old.get("gog_oauth_client", {}).get("client_id"),
        "GOG_OAUTH_CLIENT_SECRET": old.get("gog_oauth_client", {}).get("client_secret"),
        
        "NVIDIA_NGC_PASS": old.get("nvidia_ngc", {}).get("password")
    }

    # Remove Nones
    new_secrets = {k: v for k, v in new_secrets.items() if v}

    with open(NEW_SECRETS_PATH, "w", encoding="utf-8") as f:
        json.dump(new_secrets, f, indent=4)
        
    print(f"Created flattened secrets at {NEW_SECRETS_PATH}")

if __name__ == "__main__":
    flatten_secrets()
