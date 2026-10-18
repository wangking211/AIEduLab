---
name: edu-probability
description: >-
  把一道概率统计题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个参数滑块驱动实时重算的概率量 + 状态灯 + 定值指示器），中栏 KaTeX 分步解析，
  右栏 2D Canvas 概率画板（组合数柱子、样本空间网格、贝叶斯图标阵列、
  离散分布柱子、正态阴影区间、大数定律轨迹、中心极限定理直方图）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖排列组合、
  古典概型、条件概率与贝叶斯（全概率）、二项分布、超几何分布、正态分布与 σ 覆盖率、
  大数定律、中心极限定理等题型，统一由 sympy 精确计算驱动（答案、分步数值、画板读数
  同源一致）；大数定律与中心极限定理的抽样是**真跑**且与内核逐位一致，不是画出来的曲线。
  内容按高中数学「概率统计」组织，并自然延伸到大学概率论入口。其它 agent 也可调用
  本技能生成此类网页。形态与 edu-math-sequences 平行（复用 seq-phys 模板家族，
  并新增 factor / sample / bayes / bars / normal / lln / clt 七种场景）。
  触发词：概率, 统计, 概率统计, 排列组合, 组合数, 古典概型, 样本空间, 条件概率,
  贝叶斯, 全概率公式, 基率谬误, 二项分布, 超几何分布, 不放回抽样, 有限总体校正,
  期望, 方差, 标准差, 正态分布, 标准正态, σ覆盖率, 68-95-99.7, 大数定律, 频率收敛,
  中心极限定理, 峰度, 置信区间, 解这道概率题, 随机出一道概率统计题, 这张图里的概率题;
  probability, statistics, combinatorics, classical probability, conditional
  probability, Bayes theorem, total probability, base rate fallacy, binomial
  distribution, hypergeometric distribution, expected value, variance, normal
  distribution, standard normal, sigma coverage, law of large numbers, central
  limit theorem, confidence interval, interactive probability solution page.
---

# 概率与统计交互教学网页 (edu-probability)

把一道概率统计题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
sympy 精确计算驱动，概率画板 + KaTeX 分步解析。覆盖高中数学「概率统计」模块，
并自然延伸到大学概率论入口（大数定律、中心极限定理、置信区间）。

## 依赖（重要）

计算核心 `lib/prob_kernel.py` 依赖 **sympy**。运行脚本前先确认有能 import sympy 的
解释器：`python -c "import sympy"`。

**缺库时**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python -m pip install sympy`）或换一个已装该库的解释器；**不要未经询问直接装**。
Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-probability
python scripts/generate.py list                      # 列出已注册题型
python scripts/generate.py binom ./sol.html          # 二项分布
python scripts/generate.py all ./output              # 全部题型
python scripts/generate.py random 7 ./random.html    # 随机出题（seed=7）
python lib/prob_kernel.py                           # kernel 内置自检（41 条）
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

八个题型 key 与画板场景的对应：

| key | 场景 | 主问题 |
| --- | --- | --- |
| `combo` | `factor` | 从 8 人选 k 人有多少种？为什么 C(8,k) 在 k=4 最大？ |
| `classic` | `sample` | 两颗骰子点数和为 7 的概率？为什么两端最小？ |
| `bayes` | `bayes` | 灵敏度 99% 的检测阳性，真患病概率只有 1.9%？ |
| `binom` | `bars` | n 次独立重复试验的分布、期望与方差 |
| `hyper` | `bars` | 不放回抽样的方差比二项小多少？那个因子是什么？ |
| `normal` | `normal` | P(\|Z\|≤k) 与 68.27 / 95.45 / 99.73 这组数的来历 |
| `lln` | `lln` | 频率为什么稳定？波动尺度为什么是 1/√n？ |
| `clt` | `clt` | 为什么「多个独立同分布之和」会变成正态？怎么量化？ |

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面归一成：已知量（样本点数、概率、试验次数、分布参数、区间半径…）、所求、
单位、语言。先判断它属于上面哪个题型，再决定用哪个 key。

### 第 2 步：用 kernel 精确计算（不要心算）
`lib/prob_kernel.py` 提供：
- 计数：`perm` `comb` `classical` `frac_of`
- 条件概率：`cond_prob` `total_prob` `bayes`
- 分布：`binom_pmf` `binom_cdf` `binom_stats` `hyper_pmf` `hyper_stats`
- 矩：`exp_var` `die_pairs`
- 正态：`normal_pdf` `normal_cdf` `normal_interval` `norm_ppf` `ci_z` `Z_95` `Z_99`
- 模拟：`lcg` `lln_path` `sim_bernoulli` `clt_sums` `clt_moments` `histogram`

**精确优先**：组合数、贝叶斯后验、二项/超几何的 pmf 与矩都返回**符号有理数**
（答案卡要显示 `120/1024` 而不是 `0.1172`）。只有正态与模拟必然用浮点。

### 第 3 步：组装数据并注入模板
数据三段 `lesson` / `steps` / `board`，调用 `generate.render_html`（或
`skillkit.cli`）注入 `template/board.html`。可直接照抄 `scripts/generate.py` 里
8 个 `build_*`。

**每个读数表达式都必须与内核值对账**：`generate.py` 里的 `_agree(label, expr, want)`
在构建期用等价的 Python 实现求值一次，与内核比对，不一致直接停构建。新增读数时
必须补一条 `_agree`，否则公式漂移没人拦。

### 第 4 步：自检（正确性方案）
- kernel 答案 == 答案卡 `lesson.answer` == 末步骤展示值 == 画板读数初值，四者一致。
- `python lib/prob_kernel.py` 自检全过（含 LCG 前 5 个值，供与浏览器交叉验证）。
- 起本地静态服务预览检查：
  - 无控制台报错（含 `animT is not defined` 这类循环变量未声明）；
  - KaTeX 正常，无残留 `{{ }}` 模板记号；
  - 滑块拨到最小/最大，读数**和画布**都跟着变；
  - 画布内容**不贴边**（像素包围盒四周留余量；右侧标签用 `start` 对齐最容易顶出画布）；
  - 定值指示器跟踪的读数恒定（如 `classic` 样本点总数 36）；
  - 状态灯在该翻转的参数值上翻转。
- **模拟类页面额外验一条**：在浏览器控制台重跑 `lcg(seed)`，末值必须与
  `prob_kernel.lln_path(...)` 一致（同源）；`lln` 与 `clt` 的种子与上表绑定。
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`，把路径告诉用户。

## 扩展

- **加题型**：在 `prob_kernel.py` 加求解函数（精确表达式 + `__main__` 自检），
  在 `generate.py` 加一个 `build_*`（含 `_agree` 对账）并注册进 `REGISTRY`。
- **加画板场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `template/parts/scene_dispatch.html` 加 case，然后
  `python ../../tools/compose_templates.py` 重新组装 `template/board.html`。
  **不要直接改 `board.html`** —— 它是模板家族组装出来的产物，改了会被下次组装覆盖。
- 场景字段放 `board.scene`，数值字段可写成表达式（按 param + scalars 顺序求值）。
  字符串字段求值失败时保留原串，故 `caption` 可安全写字面量。
- 需要新的数学函数（如阶乘、组合数、正态累积）时，加进
  `template/parts/expr_mathenv.html` 的 `MATHENV`，**并在 `generate.py` 的
  `_MATHENV` 里加一份等价实现**，否则 `_agree` 无法对账。

## 数值出处分级

本技能的每一个数字都属下列三类之一，写步骤与图注时必须与之一致：

**现算**（内核由公式推出，无手写数字）
排列数与组合数、古典概型概率、全概率与贝叶斯后验、二项与超几何的 pmf/CDF/期望/方差/
有限总体校正因子、离散分布期望方差、正态区间覆盖率、分位数与置信区间、
大数定律轨迹的每一个点、中心极限定理直方图的每一根柱子、以及
`-6/(5n)` 这样的解析矩。

**数值方法**（不是「实测常数」，而是必然用近似的数学事实）
- 标准正态累积 Φ(z) **没有初等原函数**，只能数值算。内核用 C 库 `math.erf`；
  浏览器没有 `erf`，画板自带 A&S 7.1.26 有理逼近，最大误差 ~1.5e-7，
  构建期由 `_check_js_math()` 断言「与 `math.erf` 之差 < 1e-6」，否则停构建。
- 伪随机用 32 位 LCG（`state←(1664525·state+1013904223) mod 2³²`）。
  **它不是密码学随机数**，仅用于教学演示；选它的唯一理由是 Python 与 JS 能逐位复现，
  从而「浏览器里重跑」与「内核录下」是同一条序列。

**假设**（题面给定或为使图形可读而设定，逐条如下）
- `combo`：总人数 n=8，滑块为选出人数 k∈[0,8]，题设 k=4。
- `classic`：两颗可区分的均匀骰子，滑块为目标和 s∈[2,12]，题设 s=7。
- `bayes`：患病率 0.1%、灵敏度 99% 为题设；滑块为假阳性率∈[0.01,0.20]，题设 0.05；
  图标阵列取 1000 人（为让 0.1% 显现成 1 个点而设定）。
- `binom`：试验次数 n=10，滑块为单次命中率 p∈[0.05,0.95]，题设 p=0.5。
- `hyper`：总体 N=10、其中次品 K=3，滑块为抽取件数 n∈[1,10]，题设 n=4。
- `normal`：标准正态 N(0,1)，滑块为区间半径 k∈[0.5,3.5]（单位 σ），题设 k=1。
- `lln`：试验次数 20000、种子 11 固定；滑块为成功概率 p∈[0.10,0.90]，题设 p=0.5。
- `clt`：模拟 800 组、最大项数 30、种子 3 固定；滑块为项数 n∈[1,30]，题设 n=12。
- 学生分布、泊松分布、假设检验的完整流程（t 检验、p 值推导）**尚未覆盖**，
  目前只做到置信区间（总体标准差已知的 z 区间）。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页，
交互页能说清就别做视频。本技能产出的是**自包含的交互教学网页**，构建与校验都有成本，
不适合「随口问一句」的场景。

- 只要一个数值答案（比如「C(10,3) 等于多少」）——直接算并作答，不必做页。
- 题目要的是**概率论的公理化证明**（σ-代数、可测性、收敛的严格定义、
  Kolmogorov 公理体系）——命题的证明不是「给定参数 → 输出数值」的函数，本技能不覆盖。
- 题目是**统计推断的严格理论**（抽样分布推导、t/F 检验的构造、极大似然的渐近性质）
  ——目前只做到 z 置信区间，超出部分请直接说明未覆盖，不要硬套现有场景。
- 题目属**随机化算法与数据结构分析**（随机快排的期望复杂度、哈希冲突）
  ——用 `edu-cs`。
- 题目属**数列与三角**（等差等比、和差化积、解三角形）——用 `edu-math-sequences`。
- 用户明确要**视频**——本技能只产静态交互网页（视频线见 `edu-math-video`）。

## 目录结构

```
edu-probability/
├── SKILL.md
├── lib/prob_kernel.py             # sympy 精确内核（10 组求解函数 + 41 条自检）
├── scripts/generate.py            # 注入模板 + 8 个 build_* + 读数对账 + 批量/随机出题
└── template/
    ├── board.html                 # 组装产物（勿直接修改）
    └── parts/                     # 模板片段（改这里再 compose）
        ├── scene_functions.html   # 7 个 drawXxx + LCG + 正态逼近
        ├── scene_dispatch.html    # 场景分派
        └── expr_mathenv.html      # MATHENV（新增 fact/comb/normcdf）
```
