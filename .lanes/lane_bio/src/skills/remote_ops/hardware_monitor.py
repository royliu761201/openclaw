
from typing import Dict, Any, Optional
import asyncio

class HardwareMonitor:
    """
    Atomic Skill: Monitors Remote Hardware (GPU).
    Depends on a 'Shell' interface (Dependency Injection? Or just pass shell output?)
    Design Choice: It consumes a Shell to run commands.
    """
    def __init__(self, shell):
        self.shell = shell # Dependency Injection of RemoteShell

    async def get_gpu_status(self) -> Dict[str, Any]:
        """
        Queries remote GPU status using `nvidia-smi`.
        """
        cmd = "nvidia-smi --query-gpu=name,memory.total,memory.free,utilization.gpu --format=csv,noheader,nounits"
        
        res = await self.shell.execute(cmd, timeout=10)
        
        if res.get("exit_code") != 0:
            return {}
            
        try:
            lines = res.get("stdout", "").strip().splitlines()
            best_gpu = None
            max_free = -1
            
            for line in lines:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 4:
                    name = parts[0]
                    total = int(parts[1])
                    free = int(parts[2])
                    util = int(parts[3])
                    
                    if free > max_free:
                        max_free = free
                        best_gpu = {
                            "name": name,
                            "total_mb": total,
                            "free_mb": free,
                            "util": util
                        }
            return best_gpu or {}
        except Exception as e:
            print(f"[HardwareMonitor] Parse Error: {e}")
            return {}
