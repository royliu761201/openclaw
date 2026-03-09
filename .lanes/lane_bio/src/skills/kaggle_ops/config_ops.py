import json
import os
from typing import Dict, Optional, Any

"""
Atomic Config & Metadata Generation for Kaggle.
Pure functions for JSON processing.
"""

def generate_metadata(path: str, kernel_prefix: str, slug: str, title: str, dataset_slugs: Optional[list]):
    """Writes kernel-metadata.json"""
    metadata = {
      "id": f"username/{kernel_prefix}-{slug}",
      "title": f"{kernel_prefix}-{title}",
      "code_file": "notebook.ipynb",
      "language": "python",
      "kernel_type": "notebook",
      "is_private": "true",
      "enable_gpu": "true",
      "enable_internet": "true",
      "dataset_sources": dataset_slugs if dataset_slugs else [],
      "competition_sources": [],
      "kernel_sources": []
    }
    with open(path, "w") as f:
        json.dump(metadata, f, indent=2)
    return metadata

def build_init_code(secrets: Optional[Dict], git_repo: Optional[str]) -> str:
    """Constructs the initialization cell code."""
    init_code = "import os\nimport sys\n"
    
    if secrets:
        if "github_token" in secrets:
            init_code += f"os.environ['GITHUB_TOKEN'] = '{secrets['github_token']}'\n"
        if "wandb_api_key" in secrets:
            init_code += f"os.environ['WANDB_API_KEY'] = '{secrets['wandb_api_key']}'\n"
        if "wandb_url" in secrets:
             init_code += f"os.environ['WANDB_BASE_URL'] = '{secrets['wandb_url']}'\n"
    
    if git_repo and secrets and "github_token" in secrets:
         # Basic heuristic to insert token into URL
         # https://github.com/user/repo -> https://token@github.com/user/repo
         auth_repo = git_repo.replace("https://", f"https://{secrets['github_token']}@")
         init_code += f"\n# Auto-Clone (Minimum Necessity)\n!git clone --depth 1 {auth_repo} repo_root\nsys.path.append('repo_root')\n"
    
    return init_code

def construct_notebook_json(init_code: str, main_code: str) -> Dict[str, Any]:
    """Builds the .ipynb JSON structure."""
    return {
        "cells": [
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {"_uuid": "init_cell"},
                "outputs": [],
                "source": [init_code]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {"_uuid": "main_cell"},
                "outputs": [],
                "source": [main_code]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {
                    "name": "ipython",
                    "version": 3
                },
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.10.12"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }
