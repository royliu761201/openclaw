import json
import os

OLD_SECRETS_PATH = os.environ.get("OPENCLAW_OLD_SECRETS_JSON", os.path.expanduser("~/workspace/.secrets/secrets.json"))
NEW_SECRETS_PATH = os.environ.get("OPENCLAW_SECRETS_JSON", os.path.expanduser("~/workspace/.secrets/secrets_flat.json"))

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
        "GOOGLE_API_KEY": old.get("google_api_key") or old.get("GOOGLE_API_KEY"),
        
        # Groq
        "GROQ_API_KEY": old.get("groq", {}).get("keys", [""])[0],
        
        # Global Auth
        "GLOBAL_SSH_PASS": old.get("global_ssh_pass") or old.get("GLOBAL_SSH_PASS"),
        "GPU_SERVER_PASS": old.get("gpu_server_pass") or old.get("GPU_SERVER_PASS"),
        
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
        
        "NVIDIA_NGC_PASS": old.get("nvidia_ngc", {}).get("password"),

        # Search APIs (dual-key rotation support)
        "TAVILY_API_KEY_1": (old.get("TAVILY_API_KEY_1")
                             or old.get("search_apis", {}).get("TAVILY_API_KEY_1")),
        "TAVILY_API_KEY_2": (old.get("TAVILY_API_KEY_2")
                             or old.get("search_apis", {}).get("TAVILY_API_KEY_2")),
        "TAVILY_API_KEY":   (old.get("TAVILY_API_KEY")
                             or old.get("search_apis", {}).get("TAVILY_API_KEY")),
        "EXA_API_KEY":      (old.get("EXA_API_KEY")
                             or old.get("search_apis", {}).get("EXA_API_KEY")),

        # Vertex AI
        "VERTEX_API_KEY":   old.get("google_vertex_api_key") or old.get("VERTEX_API_KEY"),
        "VERTEX_PROJECT":   old.get("google_vertex_project") or old.get("VERTEX_PROJECT"),
        "GEMINI_API_KEY":   old.get("GOOGLE_API_KEY") or old.get("google_api_key"),
    }

    # Remove Nones
    new_secrets = {k: v for k, v in new_secrets.items() if v}

    # ⚠️ ANTI-LOSS PROTECTION: auto-merge legacy keys that might exist in flat file but not in secrets.json mapping.
    if os.path.exists(NEW_SECRETS_PATH):
        with open(NEW_SECRETS_PATH, "r", encoding="utf-8") as f:
            existing_flat = json.load(f)
        lost_keys = [k for k in existing_flat if k not in new_secrets]
        if lost_keys:
            print(f"⚠️  [ANTI-LOSS] The following legacy keys exist in the flat file but are missing from the python mapping:")
            for k in lost_keys:
                print(f"    🛡️ PRESERVED (Auto-merged): {k}")
                new_secrets[k] = existing_flat[k]

    with open(NEW_SECRETS_PATH, "w", encoding="utf-8") as f:
        json.dump(new_secrets, f, indent=4)
        
    print(f"Created flattened secrets at {NEW_SECRETS_PATH}")

if __name__ == "__main__":
    flatten_secrets()
