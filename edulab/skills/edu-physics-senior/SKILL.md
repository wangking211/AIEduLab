---
name: edu-physics-senior
description: >-
  把一道高中物理（必修一力学）题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （时间/力/位移/角度滑块驱动实时重算的物理量 + 状态灯 + 定值指示器 + 能量条），中栏
  KaTeX 分步解析，右栏 2D Canvas 力学画板（传送带、追及相遇双车公路、斜面滑块、
  平抛轨迹与速度分量、水平滑块受力、竖直圆环绳模型、v-t 图像阴影面积）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖传送带摩擦与共速、
  追及相遇（速度相等间距最大）、斜面上滑与下滑判断、平抛运动、牛顿第二定律、
  动能定理、竖直圆周运动临界速度、匀变速 v-t 图像等题型，统一由 sympy 精确计算驱动
  （答案、分步数值、画板读数同源一致）。其它 agent 也可调用本技能生成此类网页。
  形态与 edu-physics-junior 平行（复用其数据驱动 Canvas + KaTeX 模板骨架，并新增
  belt/chase/ramp/projectile/ground/circle/vt 七种场景）。触发词：高中物理, 力学,
  传送带, 共速, 划痕, 追及相遇, 相遇问题, 速度相等, 斜面, 动摩擦因数, 上滑, 平抛,
  抛体运动, 射程, 牛顿第二定律, 动能定理, 动能定理应用, 圆周运动, 向心力, 临界速度,
  绳模型, v-t 图像, 匀变速直线运动, 解这道高中物理题, 随机出一道高中物理题,
  这张图里的高中物理题; senior high physics, mechanics, conveyor belt, chase problem,
  inclined plane, projectile motion, Newton's second law, work-energy theorem,
  vertical circular motion, critical speed, v-t graph, interactive physics
  solution page.
---

# 高中物理·力学交互教学网页 (edu-physics-senior)

把一道高中力学题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
sympy 精确计算驱动，力学画板（传送带/追及/斜面/平抛/滑块/圆周/v-t 图）+ KaTeX 分步解析。

## 依赖（重要）

计算核心 `lib/mech_kernel.py` 依赖 **sympy**。运行脚本前先确认有能 import sympy 的
解释器：`python -c "import sympy"`。

**缺库时**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python -m pip install sympy`）或换一个已装该库的解释器；**不要未经询问直接装**。
Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-physics-senior
python scripts/generate.py list                      # 列出已注册题型
python scripts/generate.py belt ./sol.html           # 传送带
python scripts/generate.py circular ./sol.html       # 竖直圆周
python scripts/generate.py all ./output              # 全部题型
python scripts/generate.py random 7 ./random.html    # 随机出题（seed=7）
python lib/mech_kernel.py                            # kernel 内置自检
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面（文字/图片识别/随机）归一成：已知量（速度/加速度/质量/摩擦因数/角度/高度…）、
所求、单位、语言。常量按高中惯例：`g = 10 m/s²`（题目另有指定则照办）。

### 第 2 步：用 kernel 精确计算（不要心算）
按 `references/conventions.md` 的题型配方，调用 `lib/mech_kernel.py`：
- `solve_belt` `solve_chase` `solve_incline` `solve_projectile`
- `solve_newton2` `solve_work_energy` `solve_circular` `solve_kinematics`
- 通用：`tex`（LaTeX）`f`（浮点）`G_ACC`。
断言在 kernel 与 build_* 两层都有，答案错误会直接抛出。

### 第 3 步：组装数据并注入模板
构建脚本写在**临时目录**（如 `/tmp`），只把 `.html` 写到 cwd。数据三段
`lesson` / `steps` / `board`（schema 见 `references/problem-schema.md`），
调用 `generate.render_html(data, out)` 注入 `template/board.html`。

可直接照抄的范本：`scripts/generate.py` 里 8 个 `build_*` 覆盖全部场景
（belt 传送带、chase 追及、ramp 斜面、projectile 平抛、ground 牛二/动能定理、
circle 圆周、vt v-t 图）。

### 第 4 步：自检（正确性方案）
- kernel 答案 == 答案卡 `lesson.answer` == 末步骤展示值 == 画板读数初值，四者一致。
- 起本地静态服务（服务输出文件所在目录）预览检查：无控制台报错、KaTeX 正常、
  滑块实时重算正确（读数与状态灯随滑块翻转）、定值指示器跟踪的读数恒定、
  能量条比例正确、画布有内容。
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`，把路径告诉用户。

## 扩展

- **加题型**：在 `mech_kernel.py` 加求解函数（写成精确表达式 + `__main__` 自检），
  在 `generate.py` 加一个 `build_*` 并注册进 `REGISTRY`。
- **加画板场景**：在 `template/board.html` 的 `render()` 加 case 并实现 `drawXxx(S)`；
  场景字段放 `board.scene`，数值字段可写成表达式（按 param + scalars 求值）。
  字符串字段求值失败时保留原串，故 `kind`/`caption` 可安全写字面量。

## 目录结构

```
edu-physics-senior/
├── SKILL.md
├── template/board.html      # 数据驱动模板（七种力学场景 + 表达式引擎）
├── lib/mech_kernel.py       # sympy 精确计算核心（8 题型 + 自检）
├── scripts/generate.py      # 注入模板 + 8 个 build_* 范本 + 批量/随机出题
├── references/
│   ├── problem-schema.md    # 数据格式（七种场景字段与读数类型）
│   └── conventions.md       # 题型配方表与自检要求
└── output/                  # 生成样例
```
