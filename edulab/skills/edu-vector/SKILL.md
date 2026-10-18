---
name: edu-vector
description: >-
  把一道平面向量题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个可变参数滑块驱动实时重算的向量量 + 状态灯 + 定值指示器），中栏 KaTeX
  分步解析，右栏 2D Canvas 向量画板（平行四边形法则、共线点沿直线滑动、
  基底分解的平行四边形、数量积与夹角弧、投影向量与垂直分量、
  首尾相接的合力、定比分点）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖向量的线性运算
  与三角形/平行四边形法则、共线定理与三点共线、平面向量基本定理（分解的存在与唯一）、
  数量积与夹角与垂直判据、投影（数量投影与投影向量）、力的合成与余弦定理、
  定比分点等题型，统一由 sympy 精确计算驱动（含根式化简；答案、分步数值、
  画板读数同源一致）。其它 agent 也可调用本技能生成此类网页。形态与
  edu-math-sequences 平行（复用 seq-phys 模板家族，并新增 vectoradd / collinear /
  basis / dot / project / resolve / section 七种场景）。触发词：平面向量, 向量,
  向量的加法, 向量的减法, 数乘, 三角形法则, 平行四边形法则, 共线, 共线定理,
  三点共线, 平面向量基本定理, 基底, 分解, 数量积, 点积, 内积, 夹角, 垂直,
  平行, 投影, 数量投影, 投影向量, 正交分解, 力的合成, 合力, 余弦定理, 定比分点,
  中点, 重心, 解这道向量题, 随机出一道向量题, 这张图里的向量题;
  plane vectors, vector addition, parallelogram law, triangle law, collinear,
  three points collinear, basis, linear combination, dot product, angle between
  vectors, perpendicular, parallel, projection, orthogonal decomposition,
  resultant force, law of cosines, section formula, midpoint, centroid,
  interactive vector solution page.
---

# 平面向量交互教学网页 (edu-vector)

把一道平面向量题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
sympy 精确计算驱动，向量画板 + KaTeX 分步解析。

## 与 edu-solid-geometry 的边界（先看清再选技能）

两者都用向量，但管的**不是同一件事**：

| | `edu-solid-geometry` | `edu-vector`（本技能） |
| --- | --- | --- |
| 管什么 | 用「建系 + 向量法」解**立体几何** | **向量本身的运算与几何意义** |
| 画板 | Three.js 3D 模型 | 2D 平面画板 |
| 典型问题 | 线面角、二面角、异面直线夹角、点到平面距离 | 数量积、投影、共线、基底分解、定比分点 |

**判据**：题目要**算角或距离**且几何体是三维的 → `edu-solid-geometry`；
题目问**向量的运算、判据或分解** → 本技能。

## 依赖（重要）

计算核心 `lib/vector_kernel.py` 依赖 **sympy**（含根式化简与精确判据）。
运行前确认有能 import sympy 的解释器：`python -c "import sympy"`。

**缺库时**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python -m pip install sympy`）或换一个已装该库的解释器；**不要未经询问直接装**。
Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-vector
python scripts/generate.py list                      # 列出已注册题型
python scripts/generate.py dot ./sol.html            # 数量积与夹角
python scripts/generate.py all ./output              # 全部题型
python scripts/generate.py random 7 ./random.html    # 随机出题（seed=7）
python lib/vector_kernel.py                         # kernel 内置自检（48 条）
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

七个题型 key 与画板场景的对应：

| key | 场景 | 主问题 |
| --- | --- | --- |
| `add` | `vectoradd` | 和向量怎么画？$\|a+b\|$ 的范围？ |
| `collinear` | `collinear` | 系数和为 1 为什么等价于三点共线？ |
| `basis` | `basis` | 为什么任何向量都能唯一分解？ |
| `dot` | `dot` | 数量积的正负说明什么？为什么为零就是垂直？ |
| `project` | `project` | 数量投影与投影向量有什么区别？ |
| `resolve` | `resolve` | 合力为什么落在 $\|F_1-F_2\|$ 与 $F_1+F_2$ 之间？ |
| `section` | `section` | $\lambda<0$ 时点跑到哪里？$\lambda=-1$ 为什么失效？ |

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面归一成：已知向量/点、所求、符号约定、语言。先判断属于哪个题型。

### 第 2 步：用 kernel 精确计算（不要心算）
`lib/vector_kernel.py` 提供：
- 线性运算：`vec` `add` `sub` `scale` `cross2` `is_collinear`
- 共线：`affine_combo` `on_segment_line`
- 基本定理：`decompose` `basis_unique_check`
- 数量积：`dot` `norm` `angle_deg` `is_perpendicular` `is_parallel`
- 投影：`projection_scalar` `projection_vec` `rejection_vec`
- 应用：`resultant_mag` `cosine_rule`
- 分点：`section_point` `midpoint` `centroid`
- 画板：`to_px`；排版：`tex` `vec_tex`

### 第 3 步：组装数据并注入模板
数据三段 `lesson` / `steps` / `board`。可直接照抄 `scripts/generate.py` 的 7 个 `build_*`。

**每个读数表达式都必须与内核值对账**：`_agree(label, expr, want)` 在构建期用等价的
Python 实现求值一次再比对。

### 第 4 步：自检（正确性方案）
- kernel 答案 == 答案卡 `lesson.answer` == 末步展示值 == 画板读数初值，四者一致。
- `python lib/vector_kernel.py` 自检全过（48 条）。
- 起本地静态服务预览检查：
  - 无控制台报错；
  - **逐个片段试渲染 LaTeX**（`katex.renderToString(frag,{throwOnError:true})`）；
  - 滑块拨到**多个档位（至少含两端）**，读数与画布都跟着变，且**每一档都不裁边**；
  - 定值指示器跟踪的读数恒定（`add` 的 $\|a\|$、`collinear` 的系数和、
    `dot` 的 $\|a\|\|b\|$、`project` 的 $\|a\|$、`resolve` 的两个分力）；
  - 状态灯在该翻转的参数值上翻转。
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`。

## 扩展

- **加题型**：在 `vector_kernel.py` 加计算函数（+ `__main__` 自检），
  在 `generate.py` 加一个 `build_*`（含 `_agree` 对账）并注册进 `REGISTRY`。
- **加画板场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `template/parts/scene_dispatch.html` 加 case，然后
  `python ../../tools/compose_templates.py` 重新组装 `template/board.html`。
  **不要直接改 `board.html`**。

### 三条必须遵守的约定

1. **`vec()` 必须以精确有理数构造**。内核的 `_s()` 把 Python 的 float 经
   `nsimplify` 还原成有理数 —— **不能**直接用 `sp.sympify(0.5)`，那样得到的是
   `Float("0.5")`，浮点误差会让「叉积是否为零」这类**精确判据**失效
   （实测 cross2 给出 −4.4e−16 而不是 0，共线判断直接失灵）。这是本轮踩到的真 bug。
2. **文字用 `labelIn`**（会自动把锚点收进画布）；**长直线要限制延长量**，
   否则会冲出画布（`collinear` 页把 `L` 从 1.6 收到 0.45 才不贴边）。
3. **读数表达式里凡有分式或减法，必须整段加括号**。`A + B/(k)` 里除法只作用于 `B`；
   `A − B` 会被按优先级拆开。**这类优先级错在本项目已复发三次**
   （edu-history 的 `A−B`、edu-chem-calc 的分段、本技能的 `(A+B)/(k)`）。

## 数值出处分级

**现算**（内核用 sympy 精确算出，含根式化简，无手写数字）
向量的和差与数乘、叉积与共线判定、仿射组合与三点共线、基底下分解的系数与残差、
数量积、模长、夹角、垂直与平行判定、数量投影与投影向量与垂直分量、
合力大小、余弦定理的第三边、定比分点与中点与重心。

**约定**（示例向量的选择，不是实测值）
- `add`：$\mathbf{a}=(2.5,0.8)$、$|\mathbf{b}|=1.8$；滑块为 $\theta\in[0,355°]$，题设 60°。
- `collinear`：$A(0.5,0.6)$、$B(3.6,2.4)$；滑块为系数 $x\in[-0.5,1.5]$，题设 0.3。
- `basis`：$\mathbf{e_1}=(1.6,0.5)$、$\mathbf{e_2}=(-0.6,1.5)$、$\mu=2$；
  滑块为 $\lambda\in[-2,2]$，题设 1。
- `dot`：$\mathbf{a}=(2.4,1.2)$、$|\mathbf{b}|=2$；滑块为 $\theta\in[0,180°]$，题设 60°。
- `project`：$\mathbf{a}=(3.2,0)$、$|\mathbf{b}|=2$；滑块为 $\theta\in[0,180°]$，题设 60°。
- `resolve`：两个分力 2.6 与 3.0；滑块为夹角 $\theta\in[0,180°]$，题设 60°。
- `section`：$A(0.6,0.6)$、$B(3.8,2.6)$；滑块为 $\lambda\in[-0.9,3]$，题设 1。
  **下限刻意取 −0.9 而非 −1**：$\lambda=-1$ 时公式分母为零、定比分点不存在。

**未覆盖**：空间向量的坐标运算（已由 `edu-solid-geometry` 的向量法覆盖）、
向量的旋转矩阵与坐标变换、向量场与散度旋度（那是大学内容）、
复数与向量的对应关系。遇到请直接说明未覆盖。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页，
交互页能说清就别做视频。本技能产出的是**自包含的交互教学网页**，构建与校验都有成本，
不适合「随口问一句」的场景。

- 题目只要求**一个数值答案**（如「求 $a\cdot b$」）——直接算并作答，不必做页。
- 题目是**立体几何**（线面角、二面角、异面直线、点到平面距离）——用
  `edu-solid-geometry`，本技能只有平面画板。
- 题目是**解析几何**（直线与圆锥曲线的交点、弦长、定点）——用
  `edu-analytic-geometry`。
- 题目是**平面几何**（圆、相似、勾股、切线）——用 `edu-plane-geometry`。
- 题目是**复数**（复数的几何意义、三角形式）——本技能不覆盖，请直接说明。
- 题目其实是**数列与三角**（和差化积、解三角形中的正余弦定理）——用
  `edu-math-sequences`（本技能只在力的合成里用到余弦定理）。

## 目录结构

```
edu-vector/
├── SKILL.md
├── lib/vector_kernel.py           # 向量内核（9 组函数 + 48 条自检）
├── scripts/generate.py            # 注入模板 + 7 个 build_* + 读数对账
└── template/
    ├── board.html                 # 组装产物（勿直接修改）
    └── parts/                     # 模板片段（改这里再 compose）
        ├── scene_functions.html   # 7 个 drawXxx + labelIn + 向量画板助手
        ├── scene_dispatch.html    # 场景分派
        ├── page_title.html        # 「平面向量 · 交互学习」
        └── board_label.html       # 画板角标
```
