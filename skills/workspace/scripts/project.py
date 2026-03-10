#!/usr/bin/env python3
import os
import sys
import argparse
import shutil
import re

def resolve_markdown_links(content, base_dir):
    """
    Transforms relative links in the projection into absolute file:// URIs 
    so the Antigravity UI can process them as clickable links, even if the 
    projection file is sitting in the temporary brain directory.
    """
    def replacer(match):
        text = match.group(1)
        url = match.group(2)
        if not url.startswith('http') and not url.startswith('file://') and not url.startswith('/'):
            abs_path = os.path.normpath(os.path.join(base_dir, url))
            return f"[{text}](file://{abs_path})"
        elif url.startswith('/'):
            return f"[{text}](file://{url})"
        return match.group(0)

    # Convert standard markdown links [text](url)
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replacer, content)

def project_artifact(source_file, brain_dir):
    if not os.path.exists(source_file):
        print(f"❌ 错误：兵营源 SSoT 文件不存在: {source_file}")
        sys.exit(1)
        
    if not os.path.exists(brain_dir):
        print(f"❌ 错误：您提供的脑区目录 {brain_dir} 不存在。")
        sys.exit(1)

    filename = os.path.basename(source_file)
    basename, ext = os.path.splitext(filename)
    if ext.lower() != '.md':
        print(f"❌ 警告：您投影的文件 [{filename}] 不是 Markdown 格式。投影引擎只适配 SSoT 的纯文本 .md 源码。")
        sys.exit(1)

    proj_name = f"{basename}_PROJECTION.md"
    dest_path = os.path.join(brain_dir, proj_name)

    # Generate the Boss Directive Header
    header = f"""# 🚀 全息底座投影: `{filename}`

> [!NOTE]
> **投影交互说明 (Projection Note):** 
> 欢迎来到 {basename} 工作面板！这是底座 SSoT 源码的实时 UI 投影。
> 🚨 **如何下达微操指令 (The Boss Directive):** 如果您阅读这侧的投影内容时，需要对某个任务、某段文本做进度批示，请直接在当前面板里【用鼠标拉选文本】，然后执行【Comment】，留下一句批示。
> 老板的神谕将被底层探针自动倒灌回物理源码文件！禁止在当前界面修改原文件！

---

"""

    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Resolve relative MD links to absolute file:// so they work in the UI
        base_dir = os.path.dirname(os.path.abspath(source_file))
        content = resolve_markdown_links(content, base_dir)

        # Inject original contents below the header
        final_content = header + content

        # We must overwrite if it exists, since this is a dynamic snapshot checkout
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(final_content)

        print(f"✅ 投影成功降维打击！")
        print(f"原 SSoT 文件: {source_file}")
        print(f"全息投影 Artifact 锚点: {dest_path}")
        print(f"\n=========================================")
        print(f"⚠️ [行动指令]:")
        print(f"请马上调用系统的 `notify_user` 函数，把这个【全息投影 Artifact 锚点】文件通过 `PathsToReview` 传给老板！老板的界面将自动展开这块华丽的富文本面板！")
        print(f"=========================================")

    except Exception as e:
        print(f"❌ 投影仪主轴发生物理故障: {str(e)}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Unleash Universal Artifact Projection for any SSoT Document")
    parser.add_argument("--source", type=str, required=True, help="Absolute path to the raw SSoT Markdown file")
    parser.add_argument("--brain_dir", type=str, required=True, help="Absolute path to the current Agent's session brain directory")
    args = parser.parse_args()
    
    project_artifact(args.source, args.brain_dir)

if __name__ == "__main__":
    main()
