---
name: edu-physics-junior
description: >-
  把一道初中物理（力学与电学）题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （参数滑块驱动实时重算的物理量 + 状态指示灯 + 定值指示器 + 能量条），中栏 KaTeX
  分步解析，右栏 2D Canvas 物理画板（杠杆/压强海绵/浮力弹簧秤/滑轮组/电路图，
  含力箭头、力臂标注、电流方向流动点动画）。支持三入口——给定文字题、随机出题、
  上传题目图片识别后解题。覆盖杠杆平衡条件、固体压强 p=F/S、阿基米德原理与称重法、
  滑轮组拉力与机械效率、欧姆定律、串联分压、并联分流、电功率与焦耳定律等题型，
  统一由 sympy 精确计算驱动（答案、分步数值、画板读数同源一致）。其它 agent 也可
  调用本技能生成此类网页。形态与 edu-function-derivative / edu-plane-geometry 平行
  （复用其数据驱动 Canvas + KaTeX 模板骨架，并新增 lever/pressure/buoyancy/pulley/
  circuit 五种场景与 flowDots 电流动画、bars 双色能量条）。触发词：初中物理, 杠杆,
  杠杆平衡, 撬棒, 压强, 受力面积, 浮力, 阿基米德原理, 称重法, 弹簧测力计, 滑轮组,
  机械效率, 有用功, 总功, 欧姆定律, 串联, 并联, 分压, 分流, 电功率, 电热, 焦耳定律,
  解这道物理题, 随机出一道初中物理题, 这张图里的物理题; junior high physics, lever
  balance, pressure, buoyancy, Archimedes, pulley, mechanical efficiency, Ohm's law,
  series circuit, parallel circuit, electric power, Joule heating, interactive
  physics solution page.
---

# 初中物理（力学与电学）交互教学网页 (edu-physics-junior)

把一道初中物理题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
sympy 精确计算驱动，物理画板（杠杆/压强/浮力/滑轮/电路）+ KaTeX 分步解析。

## 依赖（重要）

计算核心 `lib/phys_kernel.py` 依赖 **sympy**。运行脚本前先确认有能 import sympy 的
解释器：`python -c "import sympy"`。

**缺库时**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python -m pip install sympy`）或换一个已装该库的解释器；**不要未经询问直接装**。
Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-physics-junior
python scripts/generate.py list                      # 列出已注册题型
python scripts/generate.py lever ./sol.html          # 杠杆平衡
python scripts/generate.py series ./sol.html         # 串联分压
python scripts/generate.py all ./output              # 全部题型
python scripts/generate.py random 7 ./random.html    # 随机出题（seed=7）
python lib/phys_kernel.py                            # kernel 内置自检
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面（文字/图片识别/随机）归一成：已知量（力/面积/电阻/电压…）、所求、
单位（注意 cm²→m²、×10⁻⁴ m³ 等换算）、语言。常量按初中惯例：`g=10 N/kg`、
`ρ_水=1.0×10³ kg/m³`。

### 第 2 步：用 kernel 精确计算（不要心算）
按 `references/conventions.md` 的题型配方，调用 `lib/phys_kernel.py`：
- 力学：`solve_lever` `solve_pressure` `solve_buoyancy` `solve_pulley`
- 电学：`solve_ohm` `solve_series` `solve_parallel` `solve_elec_power`
- 通用：`tex`（LaTeX）`f`（浮点）`G_ACC` `RHO_WATER`。
断言在 kernel 与 build_* 两层都有，答案错误会直接抛出。

### 第 3 步：组装数据并注入模板
构建脚本写在**临时目录**（如 `/tmp`），只把 `.html` 写到 cwd。数据三段
`lesson` / `steps` / `board`（schema 见 `references/problem-schema.md`），
调用 `generate.render_html(data, out)` 注入 `template/board.html`。

可直接照抄的范本：`scripts/generate.py` 里 8 个 `build_*` 覆盖全部场景
（lever 杠杆、pressure 海绵下陷、buoyancy 弹簧秤、pulley 滑轮组、
circuit 的 single/series/parallel 三种电路）。

### 第 4 步：自检（正确性方案）
- kernel 答案 == 答案卡 `lesson.answer` == 末步骤展示值 == 画板读数初值，四者一致。
- 起本地静态服务（服务输出文件所在目录）预览检查：无控制台报错、KaTeX 正常、
  滑块实时重算正确（读数与状态灯随滑块翻转）、定值指示器跟踪的读数恒定、
  能量条比例正确（如 80%/20%）、电路电流点在动画推进。
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`，把路径告诉用户。

## 扩展

- **加题型**：在 `phys_kernel.py` 加求解函数（写成精确表达式 + `__main__` 自检），
  在 `generate.py` 加一个 `build_*` 并注册进 `REGISTRY`。
- **加画板场景**：在 `template/board.html` 的 `render()` 加 case 并实现 `drawXxx(S)`；
  场景字段放 `board.scene`，数值字段可写成表达式（按 param + scalars 求值）。

## 目录结构

```
edu-physics-junior/
├── SKILL.md
├── template/board.html      # 数据驱动模板（杠杆/压强/浮力/滑轮/电路 + 电流动画）
├── lib/phys_kernel.py       # sympy 精确计算核心（8 题型 + 自检）
├── scripts/generate.py      # 注入模板 + 8 个 build_* 范本 + 批量/随机出题
├── references/
│   ├── problem-schema.md    # 数据格式（五种场景字段与读数类型）
│   └── conventions.md       # 题型配方表与自检要求
└── output/                  # 生成样例
```
