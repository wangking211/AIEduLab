---
name: edu-function-derivative
description: >-
  把一道高中函数与导数题解成一个自包含的交互教学网页：左栏题面 + 动态控制台（参数滑块
  驱动实时重算的函数值/导数值/单调性/状态指示 + 定值指示器），中栏 KaTeX 分步解析，
  右栏 2D Canvas 函数画板（任意 y=f(x) 曲线实时采样 + 切线/割线/垂足/零点/阴影面积）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖切线方程、割线逼近切线
  （导数定义）、三次函数极值与单调区间、奇偶性、零点存在定理与二分法、指数函数 y=aˣ、
  绝对值不可导点、对数切线族截距等题型，统一由 sympy 精确计算驱动（导数、切线、极值、
  零点、左右导数与画板读数同源一致）。其它 agent 也可调用本技能生成此类网页。
  形态与 edu-plane-geometry / edu-analytic-geometry 平行（复用其 Canvas-2D + KaTeX
  数据驱动模板，并新增 function 曲线类型与 point_on_function / tangent_function /
  secant_function / root_on_function / area_fill 构造及 fn_value / fn_slope / fn_status
  读数）。触发词：函数与导数, 导数, 切线方程, 求切线, 割线, 导数的定义, 极值, 极大值,
  极小值, 单调区间, 单调性, 奇函数, 偶函数, 奇偶性, 零点, 零点存在定理, 二分法,
  指数函数, 对数函数, 不可导, 左右导数, 尖点, 解这道导数题, 随机出一道函数题,
  这张图里的函数题; function and derivative, tangent line, secant line, derivative
  definition, extrema, monotonicity, parity, odd function, even function, zero point,
  bisection method, exponential function, non-differentiable, interactive function
  and derivative solution page.
---

# 高中函数与导数交互教学网页 (edu-function-derivative)

把一道函数与导数题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
sympy 精确计算驱动，函数画板 + KaTeX 分步解析。

## 依赖（重要）

计算核心 `lib/fn_kernel.py` 依赖 **sympy**。运行脚本前先确认有能 import sympy 的
解释器：`python -c "import sympy"`。

**缺库时**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python -m pip install sympy`）或换一个已装该库的解释器；**不要未经询问直接装**。
Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-function-derivative
python scripts/generate.py list                        # 列出已注册题型
python scripts/generate.py tangent_line ./sol.html     # 切线方程
python scripts/generate.py cubic_extrema ./sol.html    # 三次函数极值
python scripts/generate.py all ./output                # 全部题型
python scripts/generate.py random 7 ./random.html      # 随机出题（seed=7）
python lib/fn_kernel.py                                # kernel 内置自检
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面（文字/图片识别/随机）归一成：函数表达式（尽量取整系数）、所含参数（滑块变量）、
所求（切线方程/极值/单调区间/奇偶性/零点/定点/可导性）、语言。

### 第 2 步：用 kernel 精确计算（不要心算）
按 `references/conventions.md` 的题型配方，调用 `lib/fn_kernel.py`：
- 通用：`derivative` `tangent_at` `tangent_line_latex` `extrema_of`
  `monotonic_intervals` `parity_check` `zero_interval` `bisect_zero`
  `left_right_derivative` `js` `tex`。
- 题型函数：`solve_tangent_line` `solve_secant_limit` `solve_cubic_extrema`
  `solve_parity` `solve_zero_crossing` `solve_exp_family` `solve_abs_corner`
  `solve_tangent_family`。
- 函数表达式同时用 `js()` 翻译成 JS（画板采样用）与 `tex()` 输出 LaTeX（讲解用），
  两者同源——保证"图、解、答"一致。

### 第 3 步：组装数据并注入模板
构建脚本写在**临时目录**（如 `/tmp`），只把 `.html` 写到 cwd。数据三段
`lesson` / `steps` / `board`（schema 见 `references/problem-schema.md`），
调用 `generate.render_html(data, out)` 注入 `template/board.html`。

可直接照抄的范本：`scripts/generate.py` 里 8 个 `build_*` 覆盖全部交互范式
（滑动切点、割线逼近、驻点符号表、原点对称验证、二分试根、底数滑块、尖点差商、切线族截距）。

### 第 4 步：自检（正确性方案）
- kernel 答案 == 答案卡 `lesson.answer` == 末步骤展示值 == 画板读数初值，四者一致。
- 起本地静态服务（服务输出文件所在目录）预览检查：无控制台报错、KaTeX 正常、
  滑块实时重算正确（曲线随参数重采样）、定值指示器跟踪的读数恒定、
  状态指示灯（单调性/可导性/符号判断）随滑块正确翻转。
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`，把路径告诉用户。

## 扩展

- **加题型**：在 `fn_kernel.py` 加求解函数（写成精确表达式 + `__main__` 自检），
  在 `generate.py` 加一个 `build_*` 并注册进 `REGISTRY`。
- **加画板能力**：在 `template/board.html` 的 `resolveConic` 加曲线类型、
  `buildScene` 加 `derived` 分支、`computeReadouts` 加读数类型
  （参考 `function` 曲线与 `fn_value`/`fn_slope`/`fn_status` 的实现）。

## 目录结构

```
edu-function-derivative/
├── SKILL.md
├── template/board.html      # 数据驱动模板（2D 引擎 + function 曲线/切线/零点/阴影）
├── lib/fn_kernel.py         # sympy 精确计算核心（8 题型 + 通用基元）
├── scripts/generate.py      # 注入模板 + 8 个 build_* 范本 + 批量/随机出题
├── references/
│   ├── problem-schema.md    # 数据格式（含新增构造与读数）
│   └── conventions.md       # 题型配方表与自检要求
└── output/                  # 生成样例
```
