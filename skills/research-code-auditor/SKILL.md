---
name: research-code-auditor
description: 科研实验代码发射前深度审计规范。强制执行 Fail-Fast 原则，消灭所有 fallback、mock、占位符和静默失败路径，确保实验结果的真实性和可复现性。适用于所有 GPU 实验发射前的代码合规检查。
---

# Research Code Auditor — 科研代码发射前深度审计

## 核心原则

**Fail Early, Fail Fast, No Fallback.**  
任何环节失败，立即崩溃，不允许静默降级，不允许产生看似正常但实为无意义的输出。

---

## 审计分类体系

### Category A — 🔴 数据污染级（最高优先级）

这类问题会产生虚假数据，直接污染论文：

| 检查项            | 典型错误                                        | 正确做法                                                 |
| ----------------- | ----------------------------------------------- | -------------------------------------------------------- |
| **Mock 模型**     | `if args.mock: model = MockModel()`             | `raise RuntimeError("[FAIL-FAST] --mock is PROHIBITED")` |
| **Dummy 数据**    | `dummy_sequences = ["MKHL..."] * 50`            | 从真实文件加载，缺失则 `raise FileNotFoundError`         |
| **随机 Fallback** | `DummyRiskModel()` 返回 `torch.randn()` 作 risk | 删除，不存在此类对象                                     |
| **评分 -1 污染**  | `if scorer is None: return [-1.0] * len(texts)` | `raise RuntimeError`                                     |
| **占位符物理**    | `v_next = v * 0.99` 代替真实 PDE                | 实现真实有限差分或报 `NotImplementedError`               |

### Category B — 🔴 崩溃级（发射即失败）

| 检查项           | 典型错误                                | 正确做法                                |
| ---------------- | --------------------------------------- | --------------------------------------- |
| **参数别名缺失** | `--config` 被队列传入但 argparse 未声明 | 添加别名并做解析                        |
| **KV Cache OOM** | `position_ids` 追加累积 `cat`           | 每步只传 scalar `step_pos_id`           |
| **显存未释放**   | 生成循环后未 `del past_key_values`      | 显式 `del` + `torch.cuda.empty_cache()` |
| **生成后不评分** | 生成 token 成功但 scorer 未被调用       | 检查 scorer 调用是否在循环内            |

### Category C — 🟠 静默降级级

| 检查项                    | 典型错误                                                    | 正确做法                         |
| ------------------------- | ----------------------------------------------------------- | -------------------------------- |
| **Hub Fallback**          | `except: model = hub_download(...)`                         | 删除，离线服务器无法连 Hub       |
| **数据 print+return**     | `if not path: print("Warning"); return`                     | `raise FileNotFoundError`        |
| **Unknown mode 静默**     | `if mode not in set: mode = "default"`                      | `raise ValueError`               |
| **tokenizer None 零张量** | `if tokenizer is None: return zeros(...)`                   | `raise RuntimeError`             |
| **try-except 吞异常**     | `except Exception as e: print(e)`                           | `raise RuntimeError(...) from e` |
| **AutoModel 二次重试**    | `except ValueError: model = AutoModel.from_pretrained(...)` | 直接 raise，不重试               |

### Category D — 🟡 论文参数对齐

| 检查项         | 典型错误                       | 正确做法                                     |
| -------------- | ------------------------------ | -------------------------------------------- |
| **生成长度**   | `max_new_tokens = 20` (硬编码) | 论文值：toxicity=128, instruction=256        |
| **采样策略**   | 纯 `torch.multinomial(probs)`  | temperature=0.7 + top-p=0.9 nucleus sampling |
| **数据集规模** | `limit = 100`                  | 论文规定值（RTP=99441, MMLU=5000）           |
| **Epoch 上限** | `range(200000)` 无限跑         | 可配，提供 `--smoke` 快速验证                |
| **Batch Size** | 14B 默认 batch=8               | L20 48GB + 4bit：14B=4, 32B=2                |

### Category E — 🟡 死代码与逻辑

| 检查项          | 典型错误                                                       | 正确做法                       |
| --------------- | -------------------------------------------------------------- | ------------------------------ |
| **重复 return** | 函数中双 `return lam`                                          | 删除 unreachable 代码          |
| **未触发分支**  | `if mock: ... elif HAS_UNSLOTH:` (mock raise 后接 elif 不可达) | 修复为正确 `if/elif/else` 结构 |
| **未使用参数**  | 声明了 `--proxy` 但逻辑中从未用                                | 标注 TODO 或删除               |

### Category F — 🔴 Config→Args 断链级 (AB-047)

| 检查项             | 典型错误                                                          | 正确做法                                                 |
| ------------------ | ----------------------------------------------------------------- | -------------------------------------------------------- |
| **实验配置未传递** | `EXPERIMENT_MATRIX` 定义了 `ablation=True` 但 args 代码未读取     | args 解析阶段严格映射所有 task_conf 字段                 |
| **消融对照组相同** | 缺少变量控制，导致 ablation 和 full method 执行完全相同的代码路径 | 编写 `test_config_propagation.py` 自动化校验所有配置分支 |

### Category G — 🔴 虚假数据链（形式主义） (AB-048)

| 检查项                 | 典型错误                                                          | 正确做法                                                                                    |
| ---------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| **只有 `ls` 不看逻辑** | 只检查 `TruthfulQA.csv` 在不在，不管代码里有没有 Loader           | 端到端验证：`Config.dataset → config.data_path → run.py 路由 → data.py Loader类 → 真实文件` |
| **缺少配置 data_path** | config 忘记传 data_path，导致静默 fallback 到默认数据集（如 RTP） | Config 严格包含 `data_path`，代码路由未匹配时立刻 `raise`，禁止 fallback                    |

---

## 审计执行流程

### Step 1: 文件清单对照

对照项目文件清单，确保**每一个文件**都被覆盖，不凭记忆：

```
□ 主入口脚本         (run_*.py / train.py)
□ 模型控制器         (src/calam.py / src/controller.py)
□ 风险/特征模型      (src/risk.py / src/features.py)
□ 评分器             (src/scorer.py)
□ 数据加载           (src/data.py)           ← 最容易被漏掉
□ 全局配置           (src/config.py)
□ 发射脚本           (start_*.sh)
□ Pre-flight 脚本    (scripts/pre_flight_check.py)
□ Post-gate 脚本     (scripts/post_experiment_gate.py)
```

### Step 2: 语法校验（本地可执行）

```bash
python3 -c "
import ast, sys
files = ['run_calam.py', 'src/calam.py', 'src/risk.py', ...]
for f in files:
    try: ast.parse(open(f).read()); print(f'  ✅ {f}')
    except SyntaxError as e: print(f'  ❌ {f}: {e}'); sys.exit(1)
"
```

### Step 3: Grep 扫描关键词

```bash
# 扫描 fallback 关键词
grep -rn "fallback\|Dummy\|dummy_\|mock\|Mock\|return \[\-1\|print.*Warning\|except.*print\|while True" \
  --include="*.py" src/ scripts/

# 扫描硬编码数字
grep -n "max_new_tokens\s*=\s*[0-9]\|batch_size\s*=\s*[0-9]\|limit\s*=\s*[0-9]" src/config.py
```

### Step 4: 逻辑检查清单（人工）

```
□ --mock 是否直接 raise RuntimeError（不允许任何 mock 实验数据）
□ 所有数据路径不存在是否 raise FileNotFoundError
□ 所有 except Exception 是否 re-raise（不允许吞异常）
□ 采样是否用 temperature + top-p（符合论文配置）
□ max_new_tokens / limit 是否与论文参数一致
□ KV Cache 循环后是否 del past_key_values + torch.cuda.empty_cache()
□ W&B 是否记录了足够指标（batch_avg_toxicity, n_evaluated, j_score_pct）
□ **[AB-047] Config Flag 是否端到端传到 Args (是否有对应的 assert 或 test)**
□ **[AB-048] Config 定义的 dataset 是否在 data.py 中有专用 Loader 并配置了 data_path**
```

### Step 5: 三层发射门控

```bash
# Gate 1: 环境路径校验
python3 scripts/pre_flight_check.py  # exit 0 才继续

# Gate 2: Smoke Test（真实数据，50条）
bash start_calam.sh <config> true    # exit 0 才继续

# Gate 3: 全量实验
bash start_calam.sh <config> false

# Gate 4: 结果审计（才能打 [x]）
python3 scripts/post_experiment_gate.py --project calam --run_id <ID> --log logs/full_*.log
```

---

## CaLaM 专项审计历史记录

**2026-03-15/16 本轮共发现并修复 17 处问题：**

| #   | 文件              | 问题                            | 类别 |
| --- | ----------------- | ------------------------------- | ---- |
| 1   | `run_calam.py`    | `--config` 参数缺失             | B    |
| 2   | `run_calam.py`    | `position_ids` KV Cache OOM     | B    |
| 3   | `run_calam.py`    | `past_key_values` 未释放        | B    |
| 4   | `run_calam.py`    | `DummyRiskModel` 随机 risk      | A    |
| 5   | `run_calam.py`    | `AutoModel` 二次 retry fallback | C    |
| 6   | `run_calam.py`    | `--mock` 进入实验               | A    |
| 7   | `run_calam.py`    | `max_new_tokens=20`（论文=128） | D    |
| 8   | `run_calam.py`    | 纯 multinomial 无温度控制       | D    |
| 9   | `run_calam.py`    | mock→raise 后接 elif 不可达     | E    |
| 10  | `src/features.py` | tokenizer=None 返回零张量       | C    |
| 11  | `src/features.py` | Unknown mode 默认 toxicity      | C    |
| 12  | `src/risk.py`     | `DummyRiskModel` 存在           | A    |
| 13  | `src/calam.py`    | 双 `return lam` 死代码          | E    |
| 14  | `src/scorer.py`   | Hub fallback（离线 L20 超时）   | C    |
| 15  | `src/scorer.py`   | `score()=-1` 静默污染           | A    |
| 16  | `src/data.py`     | 3 Loader 数据缺失 print+return  | C    |
| 17  | `src/config.py`   | MMLU limit=100（论文=5000）     | D    |

> **根因**：前三轮审计只覆盖主链路文件，遗漏了 `scorer.py`、`data.py` 辅助链路。
> **固化行动**：每次审计必须对照文件清单逐一过，不凭记忆。
