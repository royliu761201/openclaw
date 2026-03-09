import asyncio
import sys
import os

sys.path.append(os.path.join(os.getcwd(), 'research_tools'))
from skills.ssh_executor import SSHExecutor

async def main():
    executor = SSHExecutor()
    print("📜 Testing Remote LaTeX Compilation...")
    
    # 1. Create a minimal LaTeX file
    tex_content = r"""
\documentclass{article}
\begin{document}
Hello from Remote Server (L20 Cluster)!
\end{document}
    """
    
    remote_dir = "/root/research_bot/test_latex"
    await executor.execute_command(f"mkdir -p {remote_dir}")
    
    # 2. Upload
    local_tex = "test.tex"
    with open(local_tex, "w") as f:
        f.write(tex_content)
        
    print("   Uploading test.tex...")
    await executor.push_file(local_tex, f"{remote_dir}/test.tex")
    os.remove(local_tex)
    
    # 3. Compile
    print("   Compiling with pdflatex...")
    cmd = f"cd {remote_dir} && pdflatex test.tex"
    res = await executor.execute_command(cmd)
    
    if res.get("exit_code") == 0:
        print("✅ Compilation SUCCESS!")
    else:
        print("❌ Compilation FAILED.")
        print(res.get("stdout"))
        print(res.get("stderr"))
        
    # 4. Check for PDF
    print("   Verifying PDF existence...")
    res = await executor.execute_command(f"ls -l {remote_dir}/test.pdf")
    print(res.get("stdout"))

if __name__ == "__main__":
    asyncio.run(main())
