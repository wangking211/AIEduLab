---
name: edu-linear-algebra
description: >-
  把一道线性代数题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个可变参数滑块驱动实时重算的矩阵量 + 状态灯 + 定值指示器），中栏 KaTeX
  分步解析，右栏 2D Canvas 几何画板（网格线性变换与面积、特征方向的拉伸、
  矩阵幂与稳态收敛、最小二乘的残差竖线、秩退化时平面塌成直线、
  单位圆变成椭圆的主轴、Gram–Schmidt 的投影与残差）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖线性变换与行列式、
  特征值与特征向量、对角化与矩阵幂（马尔可夫稳态）、正交投影与最小二乘、秩与
  列空间/零空间、奇异值分解、Gram–Schmidt 正交化等题型，统一由 sympy 精确计算
  驱动（答案、分步数值、画板读数同源一致）。内容按 MIT 18.06 的知识点组织，
  主场景刻意取 2×2 —— 因为行列式、特征值、奇异值、秩都有闭式解，于是「内核精确算」
  与「画板现算」可以逐条对账。其它 agent 也可调用本技能生成此类网页。
  形态与 edu-chem-calc 平行（复用 seq-phys 模板家族，并新增
  gridmap / eigen / power / proj / subspace / svd / orth 七种场景）。触发词：
  线性代数, 大学数学, 矩阵, 线性变换, 行列式, 特征值, 特征向量, 特征方向, 对角化,
  矩阵幂, 马尔可夫, 稳态, 转移矩阵, 正交投影, 投影矩阵, 最小二乘, 法方程, 拟合,
  秩, 列空间, 零空间, 满秩, 可逆矩阵, 奇异值, 奇异值分解, SVD, 条件数, 黄金比,
  Gram-Schmidt, 正交化, 标准正交基, 网格变形, 单位圆变椭圆, 解这道线性代数题,
  随机出一道线性代数题, 这张图里的线性代数题; linear algebra, matrix, linear
  transformation, determinant, eigenvalue, eigenvector, diagonalization, matrix
  power, Markov chain, steady state, orthogonal projection, least squares, normal
  equation, rank, column space, null space, invertible, singular value
  decomposition, SVD, condition number, Gram-Schmidt, orthonormal basis,
  interactive linear algebra solution page.
---

# 线性代数交互教学网页 (edu-linear-algebra)

把一道线性代数题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
sympy 精确计算驱动，几何画板 + KaTeX 分步解析。知识点按 **MIT 18.06** 组织。

## 为什么主场景取 2×2

线性代数的几何直觉天然是二维的（网格怎么变形、特征方向为什么不变、投影落在哪）。
而 **2×2 的行列式、特征值、特征向量、奇异值、秩、逆全都有闭式解**，于是：

- 内核用 sympy **精确**算（有理数、含根号的表达式）；
- 画板用 JS **现算**（同一批闭式公式）；
- 构建期用 `_agree()` 把两者**逐条对账**。

这正是全项目「同源一致」纪律要的形态。3×3 只在需要时用于秩与行列式。

**MIT OCW 版权提醒**：18.06 的讲义、习题、视频受 CC BY-NC-SA 约束，**不可搬用**。
本技能只借鉴它的**知识点与讲解顺序**（思想不受版权保护），内容全部自算自绘。

## 依赖（重要）

计算核心 `lib/linalg_kernel.py` 依赖 **sympy**。运行前确认有能 import sympy 的解释器：
`python -c "import sympy"`。

**缺库时**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python -m pip install sympy`）或换一个已装该库的解释器；**不要未经询问直接装**。
Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-linear-algebra
python scripts/generate.py list                      # 列出已注册题型
python scripts/generate.py svd ./sol.html            # 奇异值分解
python scripts/generate.py all ./output              # 全部题型
python scripts/generate.py random 7 ./random.html    # 随机出题（seed=7）
python lib/linalg_kernel.py                         # kernel 内置自检（53 条）
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

七个题型 key 与画板场景的对应：

| key | 场景 | 主问题 |
| --- | --- | --- |
| `transform` | `gridmap` | 剪切改变形状，为什么面积不变？有几个特征方向？ |
| `eigen` | `eigen` | 特征向量方向会随参数变吗？为什么 λ₁+λ₂ 恒等于迹？ |
| `power` | `power` | Aᵏ 为什么收敛？收敛到哪里？ |
| `projection` | `proj` | 最小二乘的法方程从哪来？残差为什么垂直于拟合方向？ |
| `rank` | `subspace` | 参数取什么值时秩退化？那时平面变成什么？ |
| `svd` | `svd` | 单位圆变成什么？半轴多长？为什么 σ₁σ₂ 与参数无关？ |
| `orth` | `orth` | 正交化时哪一部分不变？为什么剩下的必垂直？ |

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面归一成：矩阵/向量、所求、符号约定、语言。先判断属于哪个题型。

### 第 2 步：用 kernel 精确计算（不要心算）
`lib/linalg_kernel.py` 提供：
- 构造：`Mat2` `A_shift` `A_sym` `A_markov` `A_rank`（都用**一个参数 k** 支配，以满足单滑块契约）
- 变换：`det2` `trace2` `cols2` `apply2`
- 谱：`eigen2`（**会展开重根** —— 单位阵这类矩阵一个特征值对应多个方向）、`matrix_power` `steady_state`
- 投影：`dot` `norm` `proj_scalar` `proj_vec` `reject_vec` `least_squares` `ss_residual`
- 子空间：`rank_of` `null_basis` `col_basis`
- SVD：`svd2` `ellipse_axes`
- 正交化：`gram_schmidt`

### 第 3 步：组装数据并注入模板
数据三段 `lesson` / `steps` / `board`。可直接照抄 `scripts/generate.py` 的 7 个 `build_*`。

**每个读数表达式都必须与内核值对账**：`_agree(label, expr, want)` 在构建期用等价的
Python 实现求值一次再比对。

### 第 4 步：自检（正确性方案）
- kernel 答案 == 答案卡 `lesson.answer` == 末步展示值 == 画板读数初值，四者一致。
- `python lib/linalg_kernel.py` 自检全过（53 条）。
- 起本地静态服务预览检查：
  - 无控制台报错；
  - **逐个片段试渲染 LaTeX**：抽正文里的 `$…$` 用 `katex.renderToString(frag,{throwOnError:true})`
    验一遍。整页 `throwOnError:false` 会把畸形公式渲染成红字而不报错，
    只有这条检查能抓到；
  - 滑块拨到**多个档位（至少含两端）**，读数与画布都跟着变，且**每一档都不裁边**；
  - 定值指示器跟踪的读数恒定（`transform` 的 det、`eigen` 的迹、`svd` 的 σ₁σ₂、`orth` 的 q₁）。
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`。

## 扩展

- **加题型**：在 `linalg_kernel.py` 加求解函数（+ `__main__` 自检），
  在 `generate.py` 加一个 `build_*`（含 `_agree` 对账）并注册进 `REGISTRY`。
- **加画板场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `template/parts/scene_dispatch.html` 加 case，然后
  `python ../../tools/compose_templates.py` 重新组装 `template/board.html`。
  **不要直接改 `board.html`**。

### 三条必须遵守的画板约定

1. **文字一律用 `labelIn`**，不要用 `label` —— 它会量宽并把锚点自动收进画布。
2. **画几何图形一律用裁剪版**：`laSegClip`（线段，Liang–Barsky）与
   `laClipPoly`（凸多边形，Sutherland–Hodgman）。线性变换会把点推到极远
   （剪切 k=2 时能到 ±21），不裁剪就会顶出画布 —— 这是本技能最容易踩的坑。
3. **坐标轴用 `laAxes(s)`**：它按可见范围自适应长度并把 `x`/`y` 标签放进视窗内。

### LaTeX 花括号的坑（本轮踩过）

在 **f-string** 里写 LaTeX 必须用 `{{ }}`；但在**普通字符串**（含隐式拼接里没有
`f` 前缀的那些）里，`{{ }}` 会**原样**进入 LaTeX，变成「组里套组」——
`\begin{{pmatrix}}` 会让 KaTeX 抛 `Expected node of type textord, but got node
of type ordgroup`，而整页 `throwOnError:false` 又不把它当错误。

所以：**隐式拼接里若只有一部分是 f-string，其余部分的 `{{ }}` 必须写成 `{ }`**。
自查手段：对生成页逐个 `$…$` 片段做 `renderToString(..., {throwOnError:true})`。

## 数值出处分级

**现算**（内核用 sympy 精确算出，无手写数字）
行列式、迹、列向量、特征值与特征向量、矩阵幂、稳态分布、投影系数与投影向量、
残差与残差平方和、最小二乘的斜率与截距、秩、零空间基、列空间基、奇异值与主方向、
Gram–Schmidt 的正交组。

**约定**（符号与示例矩阵的选择，非计算所得）
- 场景矩阵用字母 $k$ 作唯一参数；`A_markov` 的取值 (0.8/0.3/0.2/0.7) 是为让稳态
  取到整比 (0.6, 0.4) 而选的；`A_shift`/`A_sym`/`A_rank` 的形式是为让闭式解干净而选的。

**假设**（每题的滑块范围与题设值，逐条如下）
- `transform`：$A=\begin{pmatrix}1&k\\0&1\end{pmatrix}$，滑块 $k\in[-2,2]$，题设 1。
- `eigen`：$A=\begin{pmatrix}1&k\\k&1\end{pmatrix}$，滑块 $k\in[-2,2]$，题设 0.5。
- `power`：$A=\begin{pmatrix}0.8&0.3\\0.2&0.7\end{pmatrix}$ 固定，滑块为幂次 $k\in[0,20]$，题设 5。
- `projection`：四个数据点 $(0,1),(1,3),(2,y),(3,6)$，滑块 $y\in[0,8]$，题设 4。
- `rank`：$A=\begin{pmatrix}1&1\\1&k\end{pmatrix}$，滑块 $k\in[-2,3]$，题设 2（退化点在 $k=1$）。
- `svd`：$A=\begin{pmatrix}1&k\\0&1\end{pmatrix}$，滑块 $k\in[0,1.5]$，题设 1。
- `orth`：$\mathbf{v_1}=(3,1)$ 固定，$\mathbf{v_2}=(k,2)$，滑块 $k\in[-3,3]$，题设 1。

**未覆盖**：LU/QR 分解的算法过程、行列式的展开与置换定义、$n$ 维子空间的一般理论、
特征值的数值算法（幂法/QR 迭代）、正定性与二次型、Jordan 型、复数特征值、
线性变换与基变换的矩阵相似关系。遇到请直接说明未覆盖。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页，
交互页能说清就别做视频。本技能产出的是**自包含的交互教学网页**，构建与校验都有成本，
不适合「随口问一句」的场景。

- 题目只要求**一个数值答案**（如「求 det A」）——直接算并作答，不必做页。
- 题目要**算法的实现或复杂度**（高斯消元的运算量、幂法收敛速度）——本技能只做几何
  与代数结论，算法层面请直接说明未覆盖。
- 题目是**抽象代数/群环域**方向（向量空间的公理化、线性映射的一般理论）
  ——命题的证明不是「给定参数 → 输出数值」的函数，本技能不覆盖。
- 题目属**数值分析**（浮点稳定性、条件数的严格估计、迭代法收敛率）——本技能只在
  `svd` 页顺带给出条件数，不做误差分析。
- 题目其实是**解析几何/平面几何**（直线与圆锥曲线、相似与圆幂）——用
  `edu-analytic-geometry` 或 `edu-plane-geometry`。
- 题目是**高中范围内的矩阵初步**（二阶行列式、简单线性变换）——也可用
  `edu-math-sequences` 之后的高中体系；本技能的讲解深度是大学一年级。

## 目录结构

```
edu-linear-algebra/
├── SKILL.md
├── lib/linalg_kernel.py           # sympy 精确内核（7 组函数 + 53 条自检）
├── scripts/generate.py            # 注入模板 + 7 个 build_* + 读数对账 + 三目翻译器
└── template/
    ├── board.html                 # 组装产物（勿直接修改）
    └── parts/                     # 模板片段（改这里再 compose）
        ├── scene_functions.html   # 7 个 drawXxx + 线段/多边形裁剪 + labelIn
        ├── scene_dispatch.html    # 场景分派
        ├── page_title.html        # 「线性代数 · 交互学习」
        └── board_label.html       # 画板角标
```
