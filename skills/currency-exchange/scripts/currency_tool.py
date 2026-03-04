#!/usr/bin/env python3

import argparse
import requests
import sys
import json

API_URL = "https://api.frankfurter.app"

def get_rate(args):
    amount = args.amount
    base = args.from_curr.upper()
    target = args.to_curr.upper()
    
    url = f"{API_URL}/latest"
    params = {
        "amount": amount,
        "from": base,
        "to": target
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        rate = data.get("rates", {}).get(target)
        date = data.get("date")
        
        if rate:
            # Text output less reliable for agent parsing
            # print(f"{amount} {base} = {rate} {target} (Date: {date})")
            
            # JSON output for agent
            print(json.dumps({"base": base, "target": target, "rate": rate, "amount": amount, "result": rate, "date": date}))
        else:
            error_msg = {"error": f"Rate for {target} not found."}
            print(json.dumps(error_msg))
            print(f"Error: Rate for {target} not found.", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error fetching rate: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Currency Exchange Tool (Frankfurter API)")
    subparsers = parser.add_subparsers(dest="command")
    
    # get_rate
    r_parser = subparsers.add_parser("get_rate")
    r_parser.add_argument("--from", dest="from_curr", required=True, help="Base currency (e.g. USD)")
    r_parser.add_argument("--to", dest="to_curr", required=True, help="Target currency (e.g. EUR)")
    r_parser.add_argument("--amount", type=float, default=1.0, help="Amount to convert")
    
    args = parser.parse_args()
    
    if args.command == "get_rate":
        get_rate(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
