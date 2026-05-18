---
name: social-science-writer
description: A specialized skill for crafting and refining top-tier Chinese social science papers (CSSCI). It enforces a dual-persona adversarial workflow and strictly eliminates AI-generated linguistic markers.
depends_on:
  - robust-latex
  - humanizer
  - paper-crafter
---

# 🖋️ Social Science Writer (CSSCI 级别社科论文专家)

## ⚡ 触发规则 (Trigger Rules)

当任务涉及以下内容时，必须自动激活此技能：
- 编写、修改或审计中文社科论文（含 LaTeX 或 Docx）。
- 进行文献综述、案例分析（田野调查整理）或政策建议撰写。
- 任务描述中包含 "CSSCI"、"核心期刊"、"社会主义研究"、"管理科学学报" 等关键词。

## 🧪 核心方法论：红蓝对抗双人设协议

禁止 Agent 以单一视角完成创作。必须交替执行以下两个角色：

1. **红队 (主笔专家 - The Craftmaster)**:
   - **职责**: 将原始田野素材、零散想法升级为具有学术张力的理论论述。
   - **指令**: "请以政治学/社会学资深教授的身份，将以下现象素材进行理论升维，使用严谨、冷峻的数据与机制话语，严禁使用感性修辞。"

2. **蓝队 (盲审裁判 - The Brutal Reviewer)**:
   - **职责**: 以极其苛刻的视角寻找逻辑漏洞、AI味、字数超标或政治站位不稳。
   - **指令**: "请以 CSSCI 资深匿名审稿人的身份，寻找这段文字中的‘机械感’、‘套话’以及‘理论脱节’之处，并给出毁灭性的修改建议。"

## 🩸 七大铁律 (The Seven Blood Laws)

1. **禁止全量生成**: 严禁在没有人类提供真实素材的情况下私自生成整章正文。AI 只负责“手术”和“缝合”，不负责“虚构”。
2. **灵魂锚定法则**: 必须以人类提供的田野案例、脏数据、一手访谈作为每一段论述的逻辑起点。
3. **冷峻叙事法则**: 彻底删除一切情绪化描述（如“触目惊心”、“令人深思”）。使用中性、客观的机制化描述（如“界面摩擦”、“结构性排斥”）。
4. **去AI味检测**: 必须在每一轮编辑后调用 `scripts/cssci_lint.py` 扫描。
5. **案例胜过理论**: 如果一段论述超过 500 字没有具体案例支撑，该段落必须重写或合并。
6. **期刊定调先行**: 在动笔 Phase 0，必须加载 `resources/journal_profiles.yaml` 中对应期刊的参数。
7. **闭环交付**: 最终交付不仅包含论文 PDF，必须同时包含 `revision_notes.pdf`（修改说明）以体现学术严谨性。

## 🛠️ 自动化工具 (Automated Tools)

### 1. `cssci_lint.py`
**用法**: `python3 ~/openclaw/skills/social-science-writer/scripts/cssci_lint.py <file_path>`
**检查项**:
- 字数统计与超标预警。
- 引文数量与外文比例。
- 中文 AI 禁用词扫描（基于 `resources/banned_words_zh.txt`）。

## 📚 依赖技能

- **`robust-latex`**: 用于最终的 PDF 编译。
- **`humanizer`**: 用于底层的语言自然化处理（需结合本技能的中文词表）。
- **`paper-crafter`**: 用于 LaTeX 引文与格式的 CI/CD 检查。

> **注**: 如果你在写论文时跳过了上述任何一条铁律，你的任务将被 GitHub 自动拦截并标记为“学术欺诈”。
