#!/usr/bin/env python3
import concurrent.futures
import subprocess
import sys

NODES = ["01", "02", "03", "05", "gpu"]
TARGETS = {
    "GitHub": "https://github.com",
    "Google": "https://www.google.com",
    "HuggingFace": "https://huggingface.co",
    "Aliyun": "https://mirrors.aliyun.com"
}

def check_node(node):
    results = {}
    for name, url in TARGETS.items():
        if name == "GitHub" and node in ["01", "02", "03"]:
            if node == "01":
                full_cmd = "ssh -T -o ConnectTimeout=3 -o StrictHostKeyChecking=accept-new git@github.com"
            else:
                full_cmd = f"ssh -n -o BatchMode=yes -o ConnectTimeout=3 {node} 'ssh -T -o ConnectTimeout=3 -o StrictHostKeyChecking=accept-new git@github.com 2>&1'"
            try:
                import shlex
                out = subprocess.check_output(shlex.split(full_cmd), stderr=subprocess.STDOUT, timeout=10).decode().strip()
            except subprocess.CalledProcessError as e:
                out = e.output.decode().strip() if e.output else ""
            except Exception:
                out = ""
                
            if "successfully authenticated" in out:
                results[name] = "🟩 OK(SSH)"
            else:
                results[name] = "🟥 FAIL"
            continue

        if node == "05":
            # Windows powershell/cmd friendly curl
            full_cmd = f"ssh -n -o BatchMode=yes -o ConnectTimeout=3 {node} 'curl.exe -I -s -m 3 {url}'"
        elif node == "01":
            full_cmd = f"curl -I -s -m 3 {url}"
        else:
            full_cmd = f"ssh -n -o BatchMode=yes -o ConnectTimeout=3 {node} 'curl -I -s -m 3 {url}'"
        
        try:
            import shlex
            out = subprocess.check_output(shlex.split(full_cmd), stderr=subprocess.DEVNULL, timeout=5).decode().strip()
            if "HTTP" in out:
                results[name] = "🟩 OK"
            else:
                results[name] = "🟥 FAIL"
        except Exception:
            results[name] = "🟥 FAIL"
    return node, results

def main():
    print(f"\n🚀 OpenClaw Cluster Network Status Dashboard")
    print("-" * 75)
    header = f"{'Node':<6} | " + " | ".join(f"{name:<12}" for name in TARGETS.keys())
    print(header)
    print("-" * 75)
    
    # Store results to print in order
    final_output = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check_node, n): n for n in NODES}
        for future in concurrent.futures.as_completed(futures):
            node, results = future.result()
            row = f"[{node:<4}] | " + " | ".join(f"{results[name]:<12}" for name in TARGETS.keys())
            final_output[node] = row
            
    # Print in original order
    for node in NODES:
        if node in final_output:
            print(final_output[node])
            
    print("-" * 75)
    print("💡 Ref: 05=Exit Node | 03=Vault (Exit via 05) | GPU=Air-Gapped (Aliyun Only)")
    print("\n")

if __name__ == "__main__":
    main()
