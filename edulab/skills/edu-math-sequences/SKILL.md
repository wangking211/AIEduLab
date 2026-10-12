---
name: edu-math-sequences
description: >-
  把一道高中数学（数列与三角）题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （项数 n / 角度 x / 夹角 A 滑块驱动实时重算的通项、前 n 项和、三角函数值 + 状态灯
  + 定值指示器），中栏 KaTeX 分步解析，右栏 2D Canvas 数学画板（数列柱状图与 Sₙ 折线、
  正弦型曲线游标、SAS 三角形拖动夹角、多曲线恒等式对比）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖等差数列、等比数列、
  裂项相消、错位相减、递推数列、y=Asin(ωx+φ) 图像性质、余弦定理解三角形、三角恒等式
  等题型，统一由 sympy 精确计算驱动（答案、分步数值、画板读数同源一致）。
  其它 agent 也可调用本技能生成此类网页。形态与 edu-physics-senior /
  edu-function-derivative 平行（复用其数据驱动 Canvas + KaTeX 模板骨架，并新增
  seq / wave / tri 三种数学场景）。触发词：数列, 等差数列, 等比数列, 通项公式,
  前n项和, 裂项相消, 错位相减, 递推数列, 数列求和, 求和公式, 三角函数, 正弦型函数,
  周期, y=Asin(ωx+φ), 最值点, 和差化积, 三角恒等式, 两角和差公式, 余弦定理,
  解三角形, SAS, 判定三角形, 解这道数列题, 解这道三角题, 随机出一道数列题,
  这张图里的数列题; sequences, arithmetic sequence, geometric sequence, telescoping,
  partial sum, recursion, sine wave, amplitude, period, trigonometric identity,
  cosine rule, solve triangle, interactive sequence and trig solution page.
---

# 高中数学·数列与三角交互教学网页 (edu-math-sequences)

把一道数列或三角题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
sympy 精确计算驱动，数学画板（数列柱状图+Sₙ 折线 / 正弦曲线游标 / SAS 三角形）+
KaTeX 分步解析。

## 依赖（重要）

计算核心 `lib/seq_kernel.py` 依赖 **sympy**。运行脚本前先确认有能 import sympy 的
解释器：`python -c "import sympy"`。

**缺库时**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python -m pip install sympy`）或换一个已装该库的解释器；**不要未经询问直接装**。
Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-math-sequences
python scripts/generate.py list                      # 列出已注册题型
python scripts/generate.py arithmetic ./sol.html     # 等差数列
python scripts/generate.py sin_wave ./sol.html       # 正弦型函数
python scripts/generate.py all ./output              # 全部题型
python scripts/generate.py random 7 ./random.html    # 随机出题（seed=7）
python lib/seq_kernel.py                             # kernel 内置自检
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面（文字/图片识别/随机）归一成：已知量（首项/公比/给定两项/递推式/
A、ω、φ/两边及夹角…）、所求（通项、前 n 项和、周期、最值点、边长、面积）、语言。
角度输入注意弧度与度数的换算（kernel 里角度用弧度或度数要与传参一致）。

### 第 2 步：用 kernel 精确计算（不要心算）
按 `references/conventions.md` 的题型配方，调用 `lib/seq_kernel.py`：
- `solve_arithmetic` `solve_geometric` `solve_telescope` `solve_offset_sum`
  `solve_recurrence` `solve_sin_wave` `solve_sas` `solve_identity`
- 通用：`tex`（LaTeX）`f`（浮点）`U`/`N`（内部符号）。
断言在 kernel 与 build_* 两层都有，答案错误会直接抛出。

### 第 3 步：组装数据并注入模板
构建脚本写在**临时目录**（如 `/tmp`），只把 `.html` 写到 cwd。数据三段
`lesson` / `steps` / `board`（schema 见 `references/problem-schema.md`），
调用 `generate.render_html(data, out)` 注入 `template/board.html`。

可直接照抄的范本：`scripts/generate.py` 里 8 个 `build_*` 覆盖全部场景
（seq 数列柱状图+折线、wave 正弦曲线、tri 三角形）。

### 第 4 步：自检（正确性方案）
- kernel 答案 == 答案卡 `lesson.answer` == 末步骤展示值 == 画板读数初值，四者一致。
- 起本地静态服务（服务输出文件所在目录）预览检查：无控制台报错、KaTeX 正常、
  滑块实时重算正确（读数与状态灯随滑块翻转）、定值指示器跟踪的读数恒定、
  画布有内容且随滑块变化。
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`，把路径告诉用户。

## 扩展

- **加题型**：在 `seq_kernel.py` 加求解函数（写成精确表达式 + `__main__` 自检），
  在 `generate.py` 加一个 `build_*` 并注册进 `REGISTRY`。
- **加画板场景**：在 `template/board.html` 的 `render()` 加 case 并实现 `drawXxx(S)`；
  场景字段放 `board.scene`，数值字段可写成表达式（按 param + scalars 求值）。
  字符串字段求值失败时保留原串，故 `kind`/`caption` 可安全写字面量。

## 目录结构

```
edu-math-sequences/
├── SKILL.md
├── template/board.html      # 数据驱动模板（三种数学场景 + 表达式引擎）
├── lib/seq_kernel.py        # sympy 精确计算核心（8 题型 + 自检）
├── scripts/generate.py      # 注入模板 + 8 个 build_* 范本 + 批量/随机出题
├── references/
│   ├── problem-schema.md    # 数据格式（三种场景字段与读数类型）
│   └── conventions.md       # 题型配方表与自检要求
└── output/                  # 生成样例
```
