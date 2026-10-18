---
name: edu-multivariable-calc
description: >-
  把一道多元微积分题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个可变参数滑块驱动实时重算的量 + 状态灯 + 定值指示器），中栏 KaTeX 分步解析，
  右栏 2D Canvas 画板（等高线 + 梯度箭头、伪 3D 曲面与切平面、等高线相切于约束曲线、
  黎曼和热力图、极坐标网格与面积元、格林公式的区域与边界、向量场箭头图）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖梯度与方向导数、
  曲面与切平面、拉格朗日乘数法、二重积分的黎曼和、极坐标下的二重积分、格林公式、
  散度与旋度等题型，统一由 sympy **精确**内核驱动（导数与积分是符号计算，
  黎曼和是真求和 —— 页面上直接给出与精确值的误差）。
  其它 agent 也可调用本技能生成此类网页。形态与 edu-linear-algebra / edu-ode-dynamics
  平行（复用 seq-phys 模板家族，并新增 gradient / surface / lagrange / riemann /
  polar / green / field 七种场景）。触发词：多元微积分, 高等数学, 偏导数, 偏导,
  梯度, 方向导数, 最陡上升, 全微分, 切平面, 最佳线性逼近, 雅可比,
  拉格朗日乘数法, 条件极值, 约束极值, 二重积分, 累次积分, 黎曼和, 重积分,
  极坐标, 面积元, 格林公式, 曲线积分, 环量, 散度, 旋度, 向量场, 源, 汇,
  无旋场, 无源场, 高斯散度定理, 解这道多元微积分题, 随机出一道多元微积分题,
  这张图里的微积分题; multivariable calculus, partial derivative, gradient,
  directional derivative, total differential, tangent plane, Jacobian,
  Lagrange multipliers, constrained extremum, double integral, iterated integral,
  Riemann sum, polar coordinates, Green's theorem, line integral, circulation,
  divergence, curl, vector field, interactive calculus solution page.
---

# 多元微积分交互教学网页 (edu-multivariable-calc)

把一道多元微积分题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
sympy 精确内核驱动，2D 画板 + KaTeX 分步解析。
**至此大学线（线性代数 ✅ / 微分方程 ✅ / 信号与系统 ✅ / 多元微积分 ✅）四门齐了。**

## 与相邻技能的边界（先看清再选技能）

| 技能 | 管什么 | 判据 |
| --- | --- | --- |
| `edu-function-derivative` | **一元**函数与导数（切线、极值、单调性） | 只有一个自变量 |
| `edu-linear-algebra` | 矩阵、行列式、特征值、向量空间 | 题目里有矩阵 |
| `edu-ode-dynamics` | 常微分方程与动力系统 | 题目里有 $dy/dx$ 与通解 |
| **本技能** | **多变量**：偏导、重积分、场论 | 题目里有 $f(x,y)$ / 二重积分 / 向量场 |

**判据**：题目里出现 $f(x,y)$、$\\iint$、$\\nabla$、$\\operatorname{div}$ —— 用本技能；
只有一个自变量 —— 用 `edu-function-derivative`。

## 依赖（重要）

计算核心 `lib/multivar_kernel.py` 依赖 **sympy**（导数与积分都是符号运算）。运行前确认：
`python -c "import sympy"`。
**缺库时**先询问用户是否安装（`python -m pip install sympy`）或换解释器，**不要未经询问直接装**。

**注意**：`riemann` 题型在构建期会对 $n = 1\\dots20$ 各做一次真求和，共约 2900 次取点，
构建耗时约 1–2 秒，属正常。若把 $n$ 上限调大请注意耗时（增长为 $O(n^2)$）。

Windows 控制台打印 ✓ 报 UnicodeEncodeError 时先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-multivariable-calc
python scripts/generate.py list                     # 列出已注册题型
python scripts/generate.py gradient ./sol.html      # 梯度与方向导数
python scripts/generate.py all ./output             # 全部题型
python scripts/generate.py random 7 ./random.html   # 随机出题（seed=7）
python lib/multivar_kernel.py                      # kernel 内置自检（69 条）
```

> 不传输出路径时默认写到**当前工作目录（cwd）**。

| key | 场景 | 主问题 |
| --- | --- | --- |
| `gradient` | `gradient` | 方向导数为什么是 $\nabla f$ 的投影？梯度为什么垂直等高线？ |
| `surface` | `surface` | 切平面为什么是「最佳线性逼近」？ |
| `lagrange` | `lagrange` | 极值点处两个梯度为什么平行？λ 的含义是什么？ |
| `riemann` | `riemann` | 黎曼和怎么收敛到精确值？为什么取中点？ |
| `polar` | `polar` | $dA = r\\,dr\\,d\\theta$ 里那个 $r$ 从哪来？ |
| `green` | `green` | 线积分为什么等于二重积分？逆时针为什么是正向？ |
| `field` | `field` | 散度与旋度各度量什么？什么时候「无源无汇」？ |

## 工作流程（AI 调用时）

1. **归一题面**：函数表达式、区域、所求、语言，判断属于哪个题型。
2. **用 kernel 现算**（不要心算）：`grad` `grad_at` `dir_deriv` `grad_norm` `grad_angle`
   `surface_z` `tangent_plane` `lagrange_xy_circle` `riemann_rect` `double_integral`
   `riemann_error` `polar_riemann` `polar_integral` `line_integral`
   `double_integral_green` `divergence` `curl` `field_at`。
3. **组装数据**三段 `lesson` / `steps` / `board`；可照抄 `scripts/generate.py` 的 7 个 `build_*`。
   **每个读数表达式都要与内核值对账**（`_agree`）。
4. **自检**：kernel 自检全过（69 条）；答案卡 == 末步展示值 == 画板读数初值；
   起本地静态服务，滑块拨到**每个档位**，确认
   ① 无控制台报错 ② **每一档画布都真的变了**（指纹哈希 **数 = 档位数**）
   ③ 不裁边 ④ 状态灯在该翻转的参数值上翻转。

## 本技能特有的坑

### 1. 黎曼和必须由内核真求和，不要在页面里再算一遍
`riemann` 题型要把 $n=1\\dots20$ 的和全部交给内核算好、以数组传给场景，
页面只负责**取用与上色**。这样「页面上的数」与「内核算的数」只有一个来源。
若让 JS 自己再循环一遍，两边一旦有一处细微不同就无从察觉。

### 2. 状态灯的 `rhs` 必须是**数字**
外壳的比较是 `v > rhs + 1e-9`。若把 `rhs` 写成字符串（例如 `"PI"`），
JS 会做**字符串拼接**得到 `"PI1e-9"`，比较结果为 `false` —— 不报错、界面上也不异常，
**只是状态灯永远不亮**。要写 `math.pi`（数值）。

### 3. 伪 3D 投影要自己控住边界
`surface` 题型用的是手写斜投影 `px = CX + S(x − 0.55y)`、
`py = CY + S(0.35x + 0.35y) − H·z`，**没有透视裁剪**。
把参数改大时曲面会直接冲出画布 —— 改之前先算一下四个角的落点，或直接跑裁边检查。

### 4. 沿用既有三条（详见 `edu-physics-thermal` 的 SKILL.md）
① 场景字段要是**表达式或数组**，不能写死某个档位的具体数值（否则读数变、画布不变）；
② 状态灯文案是**纯文本**，不能写 `$…$`；`evalExpr` 只返回数字（布尔会变 NaN）；
③ 一行文字不超过约 28 个汉字（11px）。

## 数值出处分级

### ① 现算（sympy 精确计算，**不手写数字**）
偏导数与梯度、方向导数、曲面高度与切平面系数、拉格朗日极值与乘数、
黎曼和（真求和）与二重积分精确值及误差、极坐标积分、曲线积分与格林公式两端、
散度与旋度。

> 特别说明：**没有查表**。所有导数都是 `sp.diff` 的结果，
> 所有积分都是 `sp.integrate` 的结果（必要时内核用极坐标独立再算一遍做交叉验证），
> 黎曼和是逐点求和 —— 所以「和 → 精确值」的收敛是**真的收敛**。

### ② 约定（示例函数与区域）
- `gradient`：$f = x^2+y^2$，点 $P(1,1)$；滑块为方向角 $\\theta\\in[0,355°]$，题设 45°。
- `surface`：$z = 4 - \\dfrac{x^2+y^2}{3}$，$y_0 = 0.8$ 固定；滑块 $x_0\\in[-2,2]$，题设 0.5。
  画板取 $x,y\\in[-2.5,2.5]$，伪 3D 参数 $(S,H)$ 为约定值。
- `lagrange`：$f = xy$，约束 $\\dfrac{x^2}{a^2} + y^2 = 1$；滑块 $a\\in[0.5,2.5]$，题设 1。
- `riemann`：$f = 4-x^2-y^2$，区域 $[-1.5,1.5]^2$；滑块 $n\\in[1,20]$（整数），题设 4。
- `polar`：被积函数 $x^2+y^2$，区域为半径 $R$ 的圆盘；滑块 $R\\in[0.6,2.4]$，题设 1。
- `green`：$P = -\\dfrac{y^3}{3}$、$Q = \\dfrac{x^3}{3}$（于是 $Q_x-P_y = x^2+y^2$），
  区域为半径 $R$ 的圆盘、边界取逆时针；滑块 $R\\in[0.6,2.0]$，题设 1。
- `field`：$F = (x,\\ ky)$；滑块 $k\\in[-2,2]$，题设 0.5。

### 未覆盖
三重积分、曲面积分与高斯 / 斯托克斯定理的**完整形式**（只在讲解里提及）、
向量值函数的微分几何（弧长、曲率、法向量、莫比乌斯）、
傅里叶级数与偏微分方程（后者部分由 `edu-ode-dynamics` 覆盖）、
复变函数。遇到请直接说明未覆盖。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页。
本技能产出的是**自包含的交互教学网页**，构建与校验都有成本。

- 只要求**一个数值答案**（如「求 $f_x$」）——直接算并作答，不必做页。
- 题目是**一元**微积分 —— 用 `edu-function-derivative` / `edu-math-sequences`。
- 题目是**线性代数 / 微分方程 / 信号** —— 用对应的 `edu-*` 技能。
- 题目是**高中解析几何 / 立体几何** —— 用 `edu-analytic-geometry` / `edu-solid-geometry`。

## 目录结构

```
edu-multivariable-calc/
├── SKILL.md
├── lib/multivar_kernel.py       # 内核（8 组函数 + 69 条自检）
├── scripts/generate.py          # 注入模板 + 7 个 build_* + 读数对账
└── template/
    ├── board.html               # 组装产物（勿直接修改）
    └── parts/                   # 模板片段（改这里再 compose）
        ├── scene_functions.html # 7 个 drawXxx + 伪 3D 投影 + 圆/箭头助手
        ├── scene_dispatch.html
        ├── page_title.html
        └── board_label.html
```

## 扩展

- **加题型**：在 `multivar_kernel.py` 加计算函数（+ `__main__` 自检），
  在 `generate.py` 加 `build_*`（含 `_agree` 对账）并注册进 `REGISTRY`。
- **加场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `scene_dispatch.html` 加 case，然后 `python ../../tools/compose_templates.py`
  重新组装 `template/board.html`。**不要直接改 `board.html`**。
