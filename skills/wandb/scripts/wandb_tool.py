#!/usr/bin/env python3

import argparse
import sys
import json
import wandb
import os
from dotenv import load_dotenv

load_dotenv()

def get_api_key():
    key = os.getenv("WANDB_API_KEY")
    if not key:
        print(json.dumps({"error": "WANDB_API_KEY not found in environment"}))
        sys.exit(1)
    return key

def log_metric(args):
    try:
        wandb.login(key=get_api_key())
        
        project = args.project
        metric_name = args.metric
        value = args.value
        
        # Resume or start run
        run = wandb.init(project=project, resume="allow")
        
        wandb.log({metric_name: value})
        
        result = {
            "status": "success",
            "project": project,
            "run_id": run.id,
            "run_name": run.name,
            "metric": metric_name,
            "value": value
        }
        print(json.dumps(result))
        
        run.finish()
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

def list_runs(args):
    try:
        api = wandb.Api(api_key=get_api_key())
        
        path = args.path # entity/project
        if "/" not in path:
            # Assume default entity if not provided? Or just project name
            # api.runs(path) might work if user is default
            pass
            
        print(f"Fetching runs for {path}...", file=sys.stderr)
        runs = api.runs(path)
        
        run_list = []
        for run in runs:
            run_list.append({
                "id": run.id,
                "name": run.name,
                "state": run.state,
                "url": run.url
            })
            if len(run_list) >= args.limit:
                break
                
        print(json.dumps(run_list))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="WandB Skill Tool")
    subparsers = parser.add_subparsers(dest="command")
    
    # log
    l_parser = subparsers.add_parser("log")
    l_parser.add_argument("--project", required=True, help="WandB Project Name")
    l_parser.add_argument("--metric", required=True, help="Metric Name")
    l_parser.add_argument("--value", type=float, required=True, help="Metric Value")
    
    # runs
    r_parser = subparsers.add_parser("runs")
    r_parser.add_argument("--path", required=True, help="Project path (entity/project)")
    r_parser.add_argument("--limit", type=int, default=10, help="Limit number of runs")
    
    args = parser.parse_args()
    
    if args.command == "log":
        log_metric(args)
    elif args.command == "runs":
        list_runs(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
