---
name: edu-plane-geometry
description: >-
  把一道初中平面几何题解成一个自包含的交互教学网页：左栏题面 + 动态控制台（参数滑块
  驱动实时重算的几何量 + 定值指示），中栏 KaTeX 分步解析，右栏 2D Canvas 动态几何画板
  （三角形/圆 + 动点 + 角弧标注 + 直角符号 + 等长刻度 + 平行箭头 + 画笔涂鸦）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖勾股定理、圆周角定理、
  切割线定理、相交弦定理（圆幂）、相似三角形 A 型、中位线定理、内切圆与内心、外接圆与外心
  等题型，统一由 sympy 精确计算驱动（答案、坐标、角度、线段比、交互引擎读数同源一致）。
  其它 agent 也可调用本技能生成此类网页。形态与 edu-analytic-geometry 平行（复用其
  Canvas-2D + KaTeX 数据驱动模板，并新增角弧/直角/刻度/平行标记与角平分线/中垂线/旋转/
  位似/圆构造）。触发词：平面几何, 初中几何, 勾股定理, 圆周角, 圆心角, 切割线定理,
  切线长定理, 相交弦定理, 圆幂定理, 相似三角形, A 型相似, 中位线, 三角形中位线,
  内切圆, 内心, 外接圆, 外心, 角平分线, 中垂线, 解这道平面几何题, 随机出一道平面几何题,
  这张图里的平面几何题; plane geometry, junior high geometry, Pythagorean theorem,
  inscribed angle, tangent-secant theorem, intersecting chords, similar triangles,
  midsegment, incircle, incenter, circumcircle, circumcenter, interactive geometry
  solution page.
---

# 初中平面几何交互教学网页 (edu-plane-geometry)

把一道初中平面几何题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
sympy 精确计算驱动，2D Canvas 画板 + KaTeX 分步解析。

## 依赖（重要）

计算核心 `lib/geom_kernel.py` 依赖 **sympy**。运行脚本前先确认有能 import sympy 的
解释器：`python -c "import sympy"`。

**缺库时**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python -m pip install sympy`）或换一个已装该库的解释器；**不要未经询问直接装**。
Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-plane-geometry
python scripts/generate.py list                          # 列出已注册题型
python scripts/generate.py pythagoras ./sol.html         # 勾股定理 3-4-5
python scripts/generate.py inscribed_angle ./sol.html    # 圆周角定理
python scripts/generate.py all ./output                  # 全部题型
python scripts/generate.py random 7 ./random.html        # 随机出题（seed=7）
python lib/geom_kernel.py                                # kernel 内置自检
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面（文字/图片识别/随机）归一成：图形类型（三角形/圆及其组合）、已知条件（边长、
角度、中点、平行、相切…）、所求（线段长/角度/比值/定值/证明目标）、语言。

### 第 2 步：用 kernel 精确计算（不要心算）
按 `references/conventions.md` 的题型配方，调用 `lib/geom_kernel.py`：
- 通用：`dist` `angle_at` `midpoint` `foot_perp` `line_intersect` `circle_through`
  `incenter_radius` `circumradius`。
- 题型函数：`solve_pythagoras` `solve_inscribed` `solve_tangent_secant`
  `solve_chord_product` `solve_similar_A` `solve_midsegment` `solve_incircle`
  `solve_circumcircle`。
- 坐标用 `V(x, y)` 构造；答案与中间量用 `tex(expr)` 输出 LaTeX。

### 第 3 步：组装数据并注入模板
构建脚本写在**临时目录**（如 `/tmp`），只把 `.html` 写到 cwd。数据三段
`lesson` / `steps` / `board`（schema 见 `references/problem-schema.md`），
调用 `generate.render_html(data, out)` 注入 `template/board.html`。

可直接照抄的范本：`scripts/generate.py` 里 8 个 `build_*` 覆盖全部交互范式
（正方形面积拼图、圆上动点、切线+动割线、双动弦、位似滑块、静态中位线、内切圆、外接圆）。

### 第 4 步：自检（正确性方案）
- kernel 答案 == 答案卡 `lesson.answer` == 末步骤展示值 == 画板读数初值，四者一致
  （`build_*` 内已加 `assert`）。
- 起本地静态服务（服务输出文件所在目录）预览检查：无控制台报错、KaTeX 正常、
  滑块实时重算正确、定值指示器跟踪的读数恒定、角弧/直角/刻度/平行标记位置正确。
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`，把路径告诉用户。

## 扩展

- **加题型**：在 `geom_kernel.py` 加求解函数（写成精确表达式 + `__main__` 自检），
  在 `generate.py` 加一个 `build_*` 并注册进 `REGISTRY`。
- **加画板能力**：在 `template/board.html` 的 `buildScene` 加 `derived` 分支、
  `computeReadouts` 加读数类型、`draw` 加标记渲染（参考角弧/直角/刻度/箭头的实现）。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页，交互页能说清就别做视频。本技能产出的是**自包含的交互教学网页**，构建与校验都有成本，不适合「随口问一句」的场景。

- 题目是圆锥曲线（椭圆 / 双曲线 / 抛物线）——用 `edu-analytic-geometry`。
- 题目需要空间中的线面角、二面角、异面直线——用 `edu-solid-geometry`。
- 题目是函数图像、切线、极值——用 `edu-function-derivative`。
- 只要求一个角度或长度、不需要看辅助线——直接算并作答。
- 本技能不覆盖：尺规作图的可行性证明（可讲，但没有对应的作图动画场景）。

## 目录结构

```
edu-plane-geometry/
├── SKILL.md
├── template/board.html      # 数据驱动模板（复用 2D 引擎 + 新增几何标记/构造）
├── lib/geom_kernel.py       # sympy 精确计算核心（8 题型 + 通用基元）
├── scripts/generate.py      # 注入模板 + 8 个 build_* 范本 + 批量/随机出题
├── references/
│   ├── problem-schema.md    # 数据格式（含新增构造与读数）
│   └── conventions.md       # 题型配方表与自检要求
└── output/                  # 生成样例
```
