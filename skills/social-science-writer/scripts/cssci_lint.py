#!/usr/bin/env python3
"""
CSSCI 论文质量检查器 (Linter)
检查字数、引文、禁用词等。
"""

import sys
import os
import re

def load_banned_words():
    path = os.path.join(os.path.dirname(__file__), '../resources/banned_words_zh.txt')
    words = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    words.append(line)
    return words

def lint_file(file_path):
    if not os.path.exists(file_path):
        print(f"❌ 错误：文件 {file_path} 不存在")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 字数统计 (粗略统计汉字)
    chinese_chars = re.findall(r'[\u4e00-\u9fa5]', content)
    char_count = len(chinese_chars)
    print(f"📊 字数统计 (汉字): {char_count}")

    # 2. 禁用词/机械词检查
    banned_words = load_banned_words()
    found_banned = []
    for word in banned_words:
        if word in content:
            found_banned.append(word)

    if found_banned:
        print(f"❌ 发现 AI 机械词/禁用词 ({len(found_banned)}个):")
        for word in found_banned[:10]:
            print(f"  - {word}")
        if len(found_banned) > 10:
            print(f"  ...等 {len(found_banned)-10} 个")
    else:
        print("✅ 未发现明显的 AI 机械词")

    # 3. 引文检测 (LaTeX 简单正则)
    citations = re.findall(r'\\cite\{', content)
    print(f"📚 引文数量 (估计): {len(citations)}")

    # 总结
    if found_banned:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 cssci_lint.py <file_path>")
    else:
        lint_file(sys.argv[1])
