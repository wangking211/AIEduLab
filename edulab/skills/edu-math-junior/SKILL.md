---
name: edu-math-junior
description: >-
  把一道初中代数 / 函数题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （参数滑块驱动实时重算的斜率/顶点/判别式/最值/解集 + 状态灯 + 定值指示器），
  中栏 KaTeX 分步解析，右栏 2D Canvas 函数画板（直线、抛物线、对称轴、顶点、
  与坐标轴交点、解集填色、直角三角形）。覆盖一次函数、两直线交点、二次函数图像与
  性质、闭区间最值、判别式与根、韦达定理、一元二次不等式、十字相乘因式分解、
  锐角三角函数。统一由 lib/jmath_kernel.py 的 sympy 精确计算驱动（答案、顶点、
  根、区间、解集、三角比与画板读数同源一致），**不手写数字**。支持三入口——
  给定文字题、随机出题、上传图片识别后解题。其它 agent 也可调用本技能生成此类
  网页。形态与 edu-function-derivative 平行（复用 geom-fn 家族的曲线画板与
  KaTeX 模板骨架）。触发词：初中数学, 代数, 一次函数, 正比例函数, 二次函数,
  抛物线, 开口方向, 对称轴, 顶点, 最值, 区间最值, 一元二次方程, 判别式,
  根的判别式, 韦达定理, 根与系数, 一元二次不等式, 解集, 因式分解, 十字相乘,
  二元一次方程组, 两直线交点, 锐角三角函数, 正弦余弦正切, 解这道初中数学题,
  随机出一道初中代数题, 这张图里的数学题; junior high math, algebra, linear
  function, quadratic function, parabola, vertex, axis of symmetry, discriminant,
  quadratic equation, Vieta, quadratic inequality, factoring, trigonometry,
  interactive algebra solution page.
---

# 初中代数与函数 (edu-math-junior)

把一道初中代数/函数题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
sympy 精确计算驱动，函数画板 + KaTeX 分步解析。

补齐的是本科目最大的一块空白：**初中数学此前只有几何（`edu-plane-geometry`），代数与函数是零。**

## 依赖（重要）

计算核心 `lib/jmath_kernel.py` 依赖 **sympy**。运行前先确认：
`python -c "import sympy"`。

**缺库时**：先询问用户是否安装，同意后再装（`python -m pip install sympy`），
**不要未经询问直接装**。Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，
先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-math-junior
python scripts/generate.py list                        # 列出题型
python scripts/generate.py quadratic ./sol.html        # 二次函数
python scripts/generate.py discriminant ./d.html       # 判别式
python scripts/generate.py all ./output                # 全部 + index.html
python scripts/generate.py random 7 ./random.html      # 随机（seed=7）
python lib/jmath_kernel.py                             # kernel 内置自检
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面归一成：已知的系数 / 条件、所求、目标题型。注意初中约定：
- 二次函数必须先确认 `a ≠ 0`；
- 区间最值要先判断**顶点是否落在区间内**，不能直接套顶点值；
- 不等式解集的端点开闭要与不等号严格对应（`>` 开、`≥` 闭）。

### 第 2 步：用 kernel 精确计算（不要心算）
按题型调用 `lib/jmath_kernel.py`：
- 一次函数：`solve_linear` / `intersect_lines`
- 二次函数：`solve_quadratic`（顶点、对称轴、判别式、根、韦达、最值一次给全）
- 区间最值：`interval_extremum`
- 不等式：`solve_quadratic_ineq`（返回区间列表 + LaTeX）
- 因式分解：`factor_quadratic` / `factor_text`
- 三角：`solve_right_triangle`
- 格式化：`tex` / `f` / `num_str` / `js` / `interval_tex`

断言在 kernel 与 build_* 两层都有；答案错会直接抛。

### 第 3 步：组装数据并注入模板
数据三段 `lesson` / `steps` / `board`，调用 `generate.render_html(data, out)`。
**画板只有一个滑块**（模板的 `BOARD.param` 是单参数契约）：多参数题就固定其余参数，
让可调的那个驱动图形。

坐标可以是**参数表达式**（如 `ptx("2*cos(ang*PI/180)", "0")`），画板按滑块值实时求值；
Python 侧的 `verify_scene` 会按默认参数代入验证记号。

### 第 4 步：自检
- `python lib/jmath_kernel.py`（37 条，含判别式三种情况、区间最值、解集方向翻转）
- `python scripts/generate.py all <临时目录>` 必须成功
- 打开产物：滑块拖动时**图形真的动**（不只是读数变）、顶点/对称轴/交点跟着走、
  解集填色与不等式方向一致、直角三角形的直角符号落在直角上
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页。

- **题目是平面几何**（全等、相似、圆、勾股）——用 `edu-plane-geometry`。
- **题目是圆锥曲线**（椭圆 / 双曲线 / 抛物线焦点、离心率、弦长）——用 `edu-analytic-geometry`；
  注意「抛物线」在初中是二次函数、在高中是圆锥曲线，先看学段。
- **题目是数列或高中三角**（正弦型函数、余弦定理）——用 `edu-math-sequences`。
- **题目是导数、切线、极值**——用 `edu-function-derivative`。
- **只需要一个数值答案、不需要看图**——直接算并作答，不必生成网页。
- **用户明确要视频讲解**——用 `edu-math-video`。
- **本技能不覆盖**：统计与概率初步、投影与视图、复数（初中不涉及）、
  含参二次函数的分类讨论（可讲，但没有对应的动态场景，容易把图画错）。

## 扩展

- **加题型**：在 `jmath_kernel.py` 加求解函数（精确表达式 + `__main__` 自检），
  在 `generate.py` 加一个 `build_*` 并注册进 `REGISTRY`。
- **加画板元素**：模板属于 `geom-fn` 家族（骨架 `shared/board/geom-fn/shell.html`），
  改自己的 `template/parts/<槽位>.html` 后运行
  `python edulab/tools/compose_templates.py` 重新组装 `template/board.html`。
  **不要直接改 board.html**——它是组装产物。

## 目录结构

```
edu-math-junior/
├── SKILL.md
├── template/
│   ├── board.html          # 组装产物（由 compose_templates.py 生成）
│   └── parts/              # 本技能对 geom-fn 骨架的 20 个槽位覆盖
├── lib/jmath_kernel.py     # sympy 精确计算核心（9 类 + 37 条自检）
├── scripts/generate.py     # 注入模板 + 9 个 build_* 范本 + 批量/随机
└── output/                 # 生成样例（不入库）
```
