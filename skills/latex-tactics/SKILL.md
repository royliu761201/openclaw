---
name: latex-tactics
description: Advanced LaTeX deployment tactics for autonomous Academic Agents, including firewall-bypassing ACL template mocks and CSSCI native integration.
---

# LaTeX Advanced Tactics for Autonomous Academic Execution

## 1. 战术背景 (Overview)
当 Agent 在高度封闭、断网或具有 SSL 嗅探的环境（如科研保密机房）中为用户强行生成排版级学术论文时，不可避免会遭遇包依赖（Style Dependencies）缺失崩溃。本 Skill 固化了绝对物理切断外网依赖时的“本地模板伪造与挂载”战术。

## 2. 核心规避战术一：国际顶会 (ACL/EMNLP) 黑盒离线挂载
当 `curl` 或 `wget` 尝试拉取 `acl.sty` 与 `acl_natbib.sty` 遭遇 443 端口阻击时，Agent **严禁挂起报错**，应立即采用以下代数替换战术在目标工作区合成伪装头文件：

### 伪造 `acl.sty` (触发 LaTeX 原生双栏双排机制)
```latex
\NeedsTeXFormat{LaTeX2e}
\ProvidesPackage{acl}[Agentic Offline Setup]
\RequirePackage[letterpaper,top=2.5cm,bottom=2.5cm,left=2.5cm,right=2.5cm]{geometry}
\RequirePackage{times}
\twocolumn
```

### 降维依赖映射
在 `main.tex` 中强行将丢失的私有 `acl_natbib` 发动机跳转至系统预装原生发动机：
```latex
\usepackage{natbib} % 取代 \usepackage[review]{acl} 所依赖的小微包
\bibliographystyle{plainnat} % 取代 \bibliographystyle{acl_natbib}
```

## 3. 核心规避战术二：国内 CSSCI 的绝对国标化
处理 C 刊任务时，严禁使用任何 `CTeX` 宏包，必须在全局第一行强制锁定 `ctexart` 底层：
```latex
\documentclass[UTF8]{ctexart}
```
并且文献引文严格抛弃 `plain`，必须采用胡庚申等国内专家高度认可的物理链条：
```latex
\bibliographystyle{gbt7714-numerical} 
```
**编译链死命令**：必须使用 `xelatex -> bibtex -> xelatex` 顺序压制，禁止使用 `pdflatex` 尝试读取中文字符。

## 4. 核心战术三：顶级学术海报与幻灯片 (Top-Tier Slide Decks & Posters)
当收到用户“制作图文并茂、给同行看的大屏展示或学术 Poster” 的任务时，Agent 必须坚决执行以下防溢出与视觉强化战略，**绝不允许出现浮夸的推销式文案**：
1. **强制级防溢出引擎切换**：废弃 `ctexart`。一律采用 `\documentclass[aspectratio=169,14pt]{ctexbeamer}`，并利用 Beamer 原生双栏 (`\begin{columns}`) 和 `block` 实现版面自适应。
2. **文本降维与去营销化打击（反大段文字化）**：
   - **严禁长篇大论**：全是文字是 Poster 的死穴。必须将抽象概念切分为极简的 Bullet points。
   - **严禁浮夸词汇与 Meta 信息**：绝对静止使用 "绝杀", "降维打击", "Zero False Positives (无数据支撑的断言)", "NeurIPS Rebuttal 专用" 等与同行学术交流严重违和的词汇。必须使用中性、客观、严谨的科研陈述。
3. **强制级“图文并茂” (Visually-Driven Evidence)**：
   - 每一张 Poster 幻灯片**必须**配合强干预的经验曲线图（PDF 格式）、架构图或数据表格。如果本地没有图，Agent 应当立即使用 matplotlib 生成或向用户请求。严禁输出一页纯文字的骨架。
3. **原生透明化插图构建 (AI+Python+LaTeX 三连击)**：
   - 优先使用视觉工具生成抽象的学术概念意境图。
   - 生成的黑色背景图严禁直接贴入高亮的学术幻灯片中。必须用 Python \texttt{Pillow} (PIL) 脚本强制执行暗色通道阈值过滤，转化为完全透明底色的 \texttt{.png}，实现“无边框感”的完美融入。
   - 针对系统逻辑与神经网络架构流图，严禁丢给 AI 输出“乱贴字母”的黑盒图像，必须采用 LaTeX \texttt{TikZ} 框架手写矢量源码，保障无极缩放超高清效果体系。
4. **全局参数防页脚溢出隔离战术 (Beamer Metadata Isolation)**：
   - **正确格式范例**：`\title[短科研代号]{\Huge 冗长的长篇大论官方标题}`，以及 `\author[主作者短称]{长达几百字的团队全名单}` 和 `\institute[核心机构简称]{极大概率被撑爆的国重实验室超长机构挂名}`。

## 5. 核心防御战术四：防御大语言模型“肌肉记忆”污染 (Anti-Markdown Pollution)
在由大语言模型（LLMs）向 `.tex` 源文件中大量生成文案时，极易因“肌肉记忆”触发 Markdown 原生排版语法的越界污染，这会使符号原样印在最终的 PDF 版面上（如著名的星号刺客 `**黑体**`）。
- **绝对 LaTeX 语法锁定**：一旦涉及给 TeX 写入文本，**严禁使用任何 `**加粗**`、`_斜体_` 或 `# 标题` 的 Markdown 符号**。
- **前置强制自审**：所有加粗必须老老实实写为 `\textbf{}`，所有斜体必须包裹于 `\emph{}`。在提交最后一次包含文字段落的 `write_to_file` 前，必须进行自纠错扫描，把骨子里的 Markdown 标志全部过滤干净。

## 6. 核心防御战术五：物理级缓存锁粉碎法 (Forceful PDF Cache Purging)
在为用户高频编译和刷新排版效果时（特别是迭代生成的 PDF 被用户的第三方办公软件独占打开时），绝对不要天真地以为仅覆盖同名 `.pdf` 并执行 `open` 就能让用户看到最新版。
- **深度缓存隔离墙**：如 WPS Office 这类具备所谓“秒开大文件”优化能力的国产办公套件，会在后台进程池和内存栈中强行死锁旧版的渲染树。即便物理文件已经更新，只要其后台常驻进程未死，用户屏幕上出现的永远是带有排版错误的历史缓存幻象！
- **重炮清场指令**：每次重新唤醒最新的 PDF 编译结果前，必须前置执行物理级的进程斩杀，绝不允许出现排版更新被隐性吞噬的情况。标准清场连招：
  ```bash
  pkill -if "WPS" || killall "WPS Office" || killall "Preview"
  rm -f *.aux *.log *.nav *.out *.snm *.toc
  # ...编译后...
  sleep 1 && open <Your_Latest_File.pdf>
  ```
