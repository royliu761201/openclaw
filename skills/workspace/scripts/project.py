#!/usr/bin/env python3
import os
import sys
import argparse
import re

# =========================================================================================
# 🚨 CRITICAL AI AGENT INSTRUCTION (ANTI-BYPASS PROTOCOL) 🚨
# =========================================================================================
# IF YOU ARE AN AI AGENT EXECUTING THIS SCRIPT, YOU MUST OBEY THE FOLLOWING CONSTITUTION:
# 1. DO NOT try to write the output of this script directly to a file via python `open(f, 'w')`.
# 2. Doing so completely bypasses the Frontend UI Artifact Registry, causing a blank screen (UI Blackhole).
# 3. Instead, you MUST capture the `stdout` text of this script, and natively use YOUR system tool:
#    `write_to_file(TargetFile=..., CodeContent=<STDOUT>, IsArtifact=True, ArtifactMetadata=...)`
# 4. This script ALREADY purges `file://` protocols for you to prevent React Router crashes.
# =========================================================================================

def resolve_markdown_links(content, base_dir, brain_dir, visited, projections_output):
    """
    Transforms relative links in the projection into absolute file:// URIs.
    If a link points to a .md file, recurses and generates a projection for it,
    then rewrites the link to point to the newly generated projection.
    """
    def replacer(match):
        text = match.group(1)
        url = match.group(2)
        
        # Clean URL (remove #anchor if present)
        url_core = url.split('#')[0]
        anchor = '#' + url.split('#')[1] if '#' in url else ''
            
        if url_core.startswith('http'):
            return match.group(0)
            
        if url_core.startswith('file://'):
            abs_path = url_core[7:]
        elif url_core.startswith('/'):
            abs_path = url_core
        else:
            abs_path = os.path.normpath(os.path.join(base_dir, url_core))
            
        if abs_path.endswith('.md') and os.path.exists(abs_path) and brain_dir:
            # Generate recursive projection!
            proj_name = os.path.splitext(os.path.basename(abs_path))[0] + "_PROJECTION.md"
            proj_path = os.path.join(brain_dir, proj_name)
            
            # Recurse if not visited
            if abs_path not in visited:
                project_artifact_recursive(abs_path, proj_path, brain_dir, visited, projections_output)
            
            return f"[{text}]({proj_path}{anchor})"
        
        return f"[{text}]({abs_path}{anchor})"

    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replacer, content)

def project_artifact_recursive(source_file, target_path, brain_dir, visited, projections_output):
    visited.add(source_file)
    filename = os.path.basename(source_file)
    basename, ext = os.path.splitext(filename)
    
    header = f"""# 🚀 全息底座子投影: `{filename}`

> [!NOTE]
> **投影交互说明 (Projection Note):** 
> 欢迎来到 {basename} 工作面板！这是由主面板级联生成的次级 SSoT 投影。
> 🚨 **微操指令:** 如果您阅读这侧的投影内容时，需要对某个任务做进度批示，请直接在当前面板里【用鼠标拉选文本】，然后执行【Comment】！

---

"""
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()

        base_dir = os.path.dirname(os.path.abspath(source_file))
        content = resolve_markdown_links(content, base_dir, brain_dir, visited, projections_output)

        final_content = header + content
        # Append to projections output instead of writing to disk
        projections_output.append({
            "path": target_path,
            "content": final_content
        })
    except Exception as e:
        print(f"❌ 级联投影 {filename} 时发生物理故障: {str(e)}", file=sys.stderr)

def project_artifact(source_file, brain_dir):
    if not os.path.exists(source_file):
        print(f"❌ 错误：兵营源 SSoT 文件不存在: {source_file}", file=sys.stderr)
        sys.exit(1)

    filename = os.path.basename(source_file)
    basename, ext = os.path.splitext(filename)
    if ext.lower() != '.md':
        print(f"❌ 警告：您投影的文件 [{filename}] 不是 Markdown 格式。投影引擎只适配 SSoT 的纯文本 .md 源码。", file=sys.stderr)
        sys.exit(1)

    # Generate the Boss Directive Header
    header = f"""# 🚀 全息底座主投影: `{filename}`

> [!NOTE]
> **投影交互说明 (Projection Note):** 
> 欢迎来到 {basename} 工作面板！这是底座 SSoT 源码的实时 UI 投影。已开启【级联投射层】，点击内部链接即可跃迁至子投影面板。
> 🚨 **如何下达微操指令 (The Boss Directive):** 如果您阅读这侧的投影内容时，需要对某个任务、某段文本做进度批示，请直接在当前面板里【用鼠标拉选文本】，然后执行【Comment】，留下一句批示。
> 老板的神谕将被底层探针自动倒灌回物理源码文件！禁止在当前界面修改原文件！

---

"""
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()

        visited = {os.path.abspath(source_file)}
        base_dir = os.path.dirname(os.path.abspath(source_file))
        projections_output = []
        
        content = resolve_markdown_links(content, base_dir, brain_dir, visited, projections_output)

        final_content = header + content
        
        # Output main to stdout
        print("=== PROJECTION_START ===")
        print(f"FILE: {os.path.join(brain_dir, basename + '_PROJECTION.md')}")
        print("CONTENT:")
        print(final_content)
        print("=== PROJECTION_END ===")
        print("")
        
        # Output cascades
        for proj in projections_output:
            print("=== PROJECTION_START ===")
            print(f"FILE: {proj['path']}")
            print("CONTENT:")
            print(proj['content'])
            print("=== PROJECTION_END ===")
            print("")

    except Exception as e:
        print(f"❌ 投影仪主轴发生物理故障: {str(e)}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Generate Universal Artifact Projection Payload")
    parser.add_argument("--source", type=str, required=True, help="Absolute path to the raw SSoT Markdown file")
    parser.add_argument("--brain_dir", type=str, required=False, default=os.environ.get("BRAIN_DIR", ""), help="Brain directory for recursive projections")
    args = parser.parse_args()
    
    project_artifact(args.source, args.brain_dir)

if __name__ == "__main__":
    main()
