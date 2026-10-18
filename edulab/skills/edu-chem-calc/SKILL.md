---
name: edu-chem-calc
description: >-
  把一道高中化学计算题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个可变参数滑块驱动实时重算的化学量 + 状态灯 + 定值指示器），中栏 KaTeX
  分步解析，右栏 2D Canvas 计算画板（物质的量换算关系图、烧杯稀释、计量与限量试剂
  条形、中和滴定 pH 曲线、平衡三段式、电解池与法拉第定律、一级反应衰减、
  溶度积对数条）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖**物质的量体系**：
  摩尔换算（m↔n↔N↔标况 V）、物质的量浓度与稀释不变量、化学计量与限量试剂判断、
  强酸强碱与一元弱酸的电离与 pH、中和滴定曲线与等当点、化学平衡三段式与转化率、
  溶度积与沉淀判断、法拉第电解定律、一级反应速率与半衰期等题型，统一由 sympy
  精确计算驱动（答案、分步数值、画板读数同源一致）。其它 agent 也可调用本技能生成
  此类网页。形态与 edu-physics-em 平行（复用 seq-phys 模板家族，并新增 mole / beaker /
  stoich / titration / ice / cell / decay / ksp 八种场景）。触发词：化学计算,
  物质的量, 摩尔, 摩尔质量, 阿伏加德罗常数, 气体摩尔体积, 微粒数, 物质的量浓度,
  配制溶液, 溶液的稀释, 稀释定律, 化学计量, 限量试剂, 过量判断, 反应进度, pH,
  酸碱中和, 电离度, 弱酸, Ka, 滴定, 滴定曲线, 等当点, 化学平衡, 三段式, 转化率,
  平衡常数, 勒夏特列, 溶度积, Ksp, 沉淀, 电解, 法拉第定律, 反应用速率, 半衰期,
  一级反应, 解这道化学计算题, 随机出一道化学计算题, 这张图里的化学题;
  chemistry calculation, mole concept, molar mass, Avogadro constant, molar
  volume, molarity, dilution, stoichiometry, limiting reagent, pH, weak acid,
  titration curve, equivalence point, chemical equilibrium, ICE table, conversion
  rate, solubility product, Ksp, electrolysis, Faraday law, reaction rate,
  half-life, interactive chemistry calculation page.
---

# 化学计算交互教学网页 (edu-chem-calc)

把一道高中化学**计算**题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
sympy 精确计算驱动，计算画板 + KaTeX 分步解析。

## 依赖（重要）

计算核心 `lib/chemcalc_kernel.py` 依赖 **sympy**（化学计量用精确有理数）。
运行脚本前先确认有能 import sympy 的解释器：`python -c "import sympy"`。

**缺库时**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python -m pip install sympy`）或换一个已装该库的解释器；**不要未经询问直接装**。
Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 与 edu-chem-reaction 的边界（先看清再选技能）

两者都跟化学有关，但覆盖**不同体系**，不要混用：

| | `edu-chem-reaction` | `edu-chem-calc`（本技能） |
| --- | --- | --- |
| 管什么 | 反应**本身**：配平、微观断键成键、原子守恒、VSEPR 分子构型 | 化学**计算**：守恒与求解 |
| 量纲体系 | **质量分数**（m_solution、w%）配制与稀释、活动性顺序 | **物质的量**体系（mol、mol/L、mol 电子） |
| 形态 | Three.js 分子动画 + 反应方程 | 2D 计算画板 + pH/浓度曲线 |
| 典型问题 | 「这个反应怎么配平、原子怎么重组」 | 「滴定到等当点 pH 是多少」 |

**判据**：题目里出现 mol / mol/L / pH / K / Ksp / 法拉第 → 用本技能；
出现「配平 / 断键成键 / 分子构型 / 质量分数」→ 用 `edu-chem-reaction`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-chem-calc
python scripts/generate.py list                      # 列出已注册题型
python scripts/generate.py titration ./sol.html      # 中和滴定
python scripts/generate.py all ./output              # 全部题型
python scripts/generate.py random 7 ./random.html    # 随机出题（seed=7）
python lib/chemcalc_kernel.py                       # kernel 内置自检（47 条）
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

八个题型 key 与画板场景的对应：

| key | 场景 | 主问题 |
| --- | --- | --- |
| `mole` | `mole` | 质量/粒子数/标况体积与物质的量怎么互换？ |
| `concentration` | `beaker` | 稀释时什么变了、什么没变？ |
| `stoich` | `stoich` | 哪种是限量试剂？能生成多少？剩多少？ |
| `titration` | `titration` | 等当点在哪？为什么那附近 pH 剧变？ |
| `equilibrium` | `ice` | 三段式怎么列？K 与转化率谁变谁不变？ |
| `electrolysis` | `cell` | 通电量与析出质量的关系？为什么是直线？ |
| `rate` | `decay` | 半衰期怎么算？它跟初始浓度有关吗？ |
| `ksp` | `ksp` | 加到什么浓度才开始沉淀？ |

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面归一成：已知量（质量/体积/浓度/Ka/Ksp/电流/时间…）、所求、单位、语言。
先判断属于上面哪个题型，再决定用哪个 key。

### 第 2 步：用 kernel 精确计算（不要心算）
`lib/chemcalc_kernel.py` 提供：
- 换算：`mole_from_mass` `mole_from_particles` `mole_from_gas_volume`
  `mass_from_mole` `particles_from_mole` `gas_volume_from_mole`
- 浓度：`molarity` `moles_in_solution` `dilute`
- 计量：`stoich_limit`（限量试剂 + 反应进度 + 剩余量，返回精确有理数）
- 酸碱：`ph_strong_acid` `ph_strong_base` `ph_weak_acid` `ph_to_conc_H` `titration_ph`
- 平衡：`ice_quadratic`（N₂O₄⇌2NO₂ 型） `ksp_judge`
- 电化学：`faraday_moles_e` `faraday_mass`
- 动力学：`half_life` `rate_first_order`
- 常数：`NA` `VM` `F_CONST` `KW`

**精确优先**：摩尔换算与化学计量用有理数（`sp.Rational`），
答案卡要显示 `2/3` 而不是 `0.6667`。

### 第 3 步：组装数据并注入模板
数据三段 `lesson` / `steps` / `board`。可直接照抄 `scripts/generate.py` 的 8 个 `build_*`。

**每个读数表达式都必须与内核值对账**：`_agree(label, expr, want)` 在构建期用等价的
Python 实现求值一次再比对，不一致直接停构建。分段函数（如滴定 pH 的三段）也照写，
`_js_to_py()` 会把顶层三目翻成 Python 表达式来验证。

### 第 4 步：自检（正确性方案）
- kernel 答案 == 答案卡 `lesson.answer` == 末步骤展示值 == 画板读数初值，四者一致。
- `python lib/chemcalc_kernel.py` 自检全过（47 条）。
- 起本地静态服务预览检查：
  - 无控制台报错（**特别注意场景是否漏了参数字段** —— 如 `mole` 场景若没写
    `"n": "n"`，画板会拿到 `undefined` 而抛错，`render()` 会在 `updateReadouts`
    之前中断，读数全变成「—」，看上去像「没数据」而不是「有 bug」）；
  - KaTeX 正常，无残留 `{{ }}` 模板记号；
  - 滑块拨到最小/最大，读数**和画布**都跟着变；
  - 画布内容**不贴边**（长注释最容易顶出画布，宁可拆成两行）；
  - 定值指示器跟踪的读数恒定（如 `concentration` 的 n、`equilibrium` 的 K、
    `rate` 的 t½）；
  - 状态灯在该翻转的参数值上翻转。
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`。

## 扩展

- **加题型**：在 `chemcalc_kernel.py` 加求解函数（+ `__main__` 自检），
  在 `generate.py` 加一个 `build_*`（含 `_agree` 对账）并注册进 `REGISTRY`。
- **加画板场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `template/parts/scene_dispatch.html` 加 case，然后
  `python ../../tools/compose_templates.py` 重新组装 `template/board.html`。
  **不要直接改 `board.html`** —— 它是模板家族组装出来的产物，会被下次组装覆盖。
- 场景字段放 `board.scene`；**参数驱动的字段必须显式写成参数字符串**
  （如 `"n": "n"`），否则该字段不会被求值。
- 需要新的数学函数（如 lg）时，加进 `template/parts/expr_mathenv.html` 的
  `MATHENV`，**并在 `generate.py` 的 `_MATHENV` 里加一份等价实现**，否则无法对账。

## 数值出处分级

本技能的每一个数字都属下列三类之一，写步骤与图注时必须与之一致：

**现算**（内核由公式推出，无手写数字）
摩尔换算、物质的量浓度、稀释后浓度、化学计量与限量试剂判断（反应进度、消耗量、
剩余量、生成量）、强酸/强碱/一元弱酸的 pH、任意加碱体积下的滴定 pH、平衡三段式的
解与转化率、溶度积判断、法拉第定律的析出质量与电子物质的量、一级反应浓度与半衰期。

**实测**（取自教材常数表，不是本页现算的）
阿伏加德罗常数 `N_A = 6.02×10²³ /mol`、标准状况气体摩尔体积 `V_m = 22.4 L/mol`、
法拉第常数 `F = 96485 C/mol`、水的离子积 `Kw = 1.0×10⁻¹⁴`（25 ℃）、
各物质摩尔质量（CO₂ 44、Cu 63.5、Ag 108 g/mol）。

**假设**（题面给定或为使图形可读而设定，逐条如下）
- `mole`：CO₂，M = 44 g/mol；滑块为 n ∈ [0.1, 2.0] mol，题设 1.0 mol。
- `concentration`：溶质 0.05 mol，滑块为溶液体积 V ∈ [0.2, 2.0] L，题设 0.5 L。
- `stoich`：N₂ 起始恒为 2 mol；滑块为 H₂ 起始 ∈ [1.0, 12.0] mol，题设 6.0 mol（恰好完全反应）。
- `titration`：HCl 0.1 mol/L、20 mL；NaOH 0.1 mol/L；滑块为加碱体积 ∈ [0, 40] mL。
- `equilibrium`：N₂O₄ ⇌ 2NO₂，K = 1.0；滑块为初始 c(N₂O₄) ∈ [0.1, 2.0] mol/L，题设 1.0。
- `electrolysis`：CuSO₄ 溶液，电流恒为 2.0 A，M(Cu) = 63.5、z = 2；
  滑块为通电时间 ∈ [0, 3600] s，题设 1800 s。
- `rate`：一级反应，k = 0.1 min⁻¹；滑块为初始浓度 ∈ [0.2, 2.0] mol/L，题设 1.0。
- `ksp`：AgCl，Ksp = 1.8×10⁻¹⁰；c(Ag⁺) 恒为 1.0×10⁻⁵ mol/L；
  滑块为 c(Cl⁻)/10⁻⁵ ∈ [0.1, 10]，题设 3.0（已过临界 1.8）。

**两条透明近似**（写步骤时必须说明，否则图在撒谎）
1. 强酸/强碱视为**完全电离**；弱酸只考虑**一级电离**。
2. **忽略水的自偶电离**对 c(H⁺) 的贡献。当溶液极稀（c 接近 10⁻⁷ mol/L）时该近似失效，
   本技能不覆盖那种情形。
3. 未覆盖：多元酸/碱的分级电离、缓冲溶液、盐类水解、pH 与温度的关系（Kw 随温度变）、
   二级/零级反应、活化能与阿伦尼乌斯方程。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页，
交互页能说清就别做视频。本技能产出的是**自包含的交互教学网页**，构建与校验都有成本，
不适合「随口问一句」的场景。

- 题目是**反应本身**（怎么配平、原子怎么重组、分子是什么构型、质量分数配制）
  ——用 `edu-chem-reaction`，本技能不管配平与微观结构。
- 题目要**有机化学**（同分异构、官能团性质、反应机理）——本技能只覆盖无机计算的
  物质的量体系，请直接说明未覆盖。
- 题目涉及**多元酸碱分级电离、盐类水解、缓冲溶液**——超出本技能的近似前提，
  直接说明未覆盖，不要硬套现有场景。
- 题目只要求**一个数值答案**——直接算并作答，不必做页。
- 题目属**化学平衡的理论推导**（盖斯定律的能量账、热力学 ΔG 与 K 的关系）
  ——本技能只做可算的数值演示，不做热力学推导。
- 用户明确要**视频**——用 `edu-chem-video`。

## 目录结构

```
edu-chem-calc/
├── SKILL.md
├── lib/chemcalc_kernel.py         # 精确内核（8 组求解函数 + 47 条自检）
├── scripts/generate.py            # 注入模板 + 8 个 build_* + 读数对账 + 批量/随机出题
└── template/
    ├── board.html                 # 组装产物（勿直接修改）
    └── parts/                     # 模板片段（改这里再 compose）
        ├── scene_functions.html   # 8 个 drawXxx + 与内核同式的滴定/平衡求解
        ├── scene_dispatch.html    # 场景分派
        └── expr_mathenv.html      # MATHENV（新增 log10/lg）
```
