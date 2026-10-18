---
name: edu-history
description: >-
  把历史中**可算的那部分**做成自包含的交互教学网页：左栏题面 + 动态控制台
  （一个参数滑块驱动实时重算的量 + 状态灯 + 定值指示器），中栏 KaTeX 分步解析，
  右栏 2D Canvas 画板（指数增长与翻倍标记、人口转变双曲线与增长率峰值、
  技术扩散 S 曲线、SIR 疫情曲线与阈值线、Kaya 恒等式因子分解、Lotka-Volterra
  相轨迹、rank-size 双对数直线），**每一页都带证据力徽章**，显式声明这张图
  能证明到什么程度（①A 纯数学/恒等式 / ①B 模型参数靠估 / ①C 形态①证据力③）。
  覆盖长期经济增长的复利与翻倍时间、人口转变与增长率峰值、技术扩散 S 曲线
  （10%→90% 时长 = 2ln9/r）、传染病阈值 R₀ 与群体免疫、Kaya 恒等式分解、
  王朝周期模型（含「周期还取决于振幅」这一关键警告）、rank-size 幂律等
  可算题目，统一由精确计算驱动（答案、分步数值、画板读数同源一致）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。其它 agent 也可
  调用本技能生成此类网页。形态与 edu-geography 平行（复用 seq-phys 模板家族，
  并新增 expcurve / demography / logistic / epidemic / kaya / cycle / loglog
  七种场景）。触发词：历史, 世界史, 可算的历史, 长期经济增长, 人均GDP, 增长率,
  翻倍时间, 复利, 人口转变, 出生率, 死亡率, 增长率峰值, 技术扩散, S 曲线,
  渗透率, logistic, 传染病, R0, 群体免疫, SIR, 阈值, Kaya 恒等式, 碳排放分解,
  王朝周期, 历史周期, Lotka-Volterra, 相图, 幂律, rank-size, Zipf, 二八定律,
  长尾, 解这道历史题, 随机出一道历史题, 这张图里的历史题;
  history, world history, quantifiable history, long-run growth, doubling time,
  compound growth, demographic transition, technology diffusion, S-curve,
  logistic, epidemic threshold, R0, herd immunity, SIR, Kaya identity,
  dynastic cycle, Lotka-Volterra, power law, rank-size, Zipf, evidence strength,
  interactive history solution page.
---

# 可算的历史交互教学网页 (edu-history)

把历史中**可算的那部分**做成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
精确计算驱动，画板 + KaTeX 分步解析。

## 这个技能为什么与别的不同：证据力分级

历史学的立身之本 —— **史料批判、因果论证、动机推断** —— 落不到「给定参数
→ 输出数值」上。`edulab/coverage-audit.md` 已量化：世界史 ① 10/18、② 4/18、
③ 4/18，**而 ③ 那四条正是这门学科的核心方法**。

所以本技能只做 ① 层，并且**每一页都必须标注证据力等级**：

| 等级 | 含义 | 风险 |
| --- | --- | --- |
| **①A** | 纯数学 / 恒等式 | 无 —— 图上的数错不了 |
| **①B** | 模型：内核确定，但**参数来自史料估算** | 曲线光滑，但峰值/拐点取决于你怎么估参数 |
| **①C** | 形态是 ①、证据力是 ③ | **最危险**：有公式、能算、能画，看起来像推导，但参数与初值都不可独立观测，结论可以被拟合出来 |

**裸奔的图 = 误导。** 一页没有证据力徽章，就不该出。徽章画在画布左下角，
同时在 `scene.caption` 里重复一遍（`_evid_badge()` 生成）。

**明确不做的**（写进 SKILL.md、也写进步骤）：史料断代、真伪判定、人物动机、
因果反事实、条约网络的边是否成立。这些没有可算内核，写成函数就是编。

## 依赖（重要）

计算核心 `lib/hist_kernel.py` 依赖 **sympy**。运行前确认有能 import sympy 的解释器：
`python -c "import sympy"`。

**缺库时**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python -m pip install sympy`）或换一个已装该库的解释器；**不要未经询问直接装**。
Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-history
python scripts/generate.py list                      # 列出已注册题型
python scripts/generate.py cycle ./sol.html          # 王朝周期模型
python scripts/generate.py all ./output              # 全部题型
python scripts/generate.py random 7 ./random.html    # 随机出题（seed=7）
python lib/hist_kernel.py                           # kernel 内置自检（48 条）
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

七个题型 key、画板场景与**证据力等级**：

| key | 场景 | 证据力 | 主问题 |
| --- | --- | --- | --- |
| `growth` | `expcurve` | ①A | 多久翻一番？翻倍时间与起点有关吗？ |
| `transition` | `demography` | **①B** | 增长率峰值在哪一年？这个年份有多可靠？ |
| `diffusion` | `logistic` | ①A | 10%→90% 要多久？为什么与开始年份无关？ |
| `epidemic` | `epidemic` | ①A | 群体免疫阈值是多少？峰值有多高？ |
| `kaya` | `kaya` | ①A | 为什么它是恒等式？能预测吗？ |
| `cycle` | `cycle` | **①C** | 周期由参数定，还是还取决于振幅？ |
| `zipf` | `loglog` | ①A | log-log 图为什么是直线？斜率是多少？ |

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面归一成：已知量（增长率/年份/参数…）、所求、单位、语言。先判断属于哪个题型。
**若题目问的是「某个史实的真伪或原因」，直接说明本技能不覆盖** —— 不要硬套模型。

### 第 2 步：用 kernel 精确计算（不要心算）
`lib/hist_kernel.py` 提供：
- 增长：`exponential` `doubling_time` `pct_change_per_year`
- 扩散：`logistic` `logistic_time` `logistic_duration` `diffusion_s_curve`
- 人口：`demographic_transition` `transition_rate_at`
- 疫情：`r0_from` `herd_threshold` `sir_peak_fraction` `sir` `rk4_step`
- 恒等式：`kaya` `kaya_decompose`
- 周期：`lv_period_analytic` `lv_integrate` `lv_scan_amplitude`
- 幂律：`pareto_sizes` `fit_rank_size_slope` `alpha_from_slope`
- 分级：`EVIDENCE`（三档的定义与措辞）

**基准值取自 `edulab/coverage-audit.md`**（那份审计已现算过），所以自检验的是
「实现与审计一致」，不是另编一套期望值。

### 第 3 步：组装数据并注入模板
数据三段 `lesson` / `steps` / `board`。可直接照抄 `scripts/generate.py` 的 7 个 `build_*`。

**每个读数表达式都必须与内核值对账**：`_agree(label, expr, want)` 在构建期用等价的
Python 实现求值一次再比对。注意运算符优先级：两个率相减必须写
`(A)-(B)`，否则 `A-B` 会被拆成 `10+35/(…) - 10 + 25/(…)`。

### 第 4 步：自检（正确性方案）
- kernel 答案 == 答案卡 `lesson.answer` == 末步展示值 == 画板读数初值，四者一致。
- `python lib/hist_kernel.py` 自检全过（48 条）。
- 起本地静态服务预览检查：
  - 无控制台报错；
  - **状态灯的文案是纯文本** —— `updateReadouts` 用 `textContent` 写入，
    `$…$` 不会被 KaTeX 渲染，会原样显示成 `$R_0$`；
  - 滑块拨到**多个档位（至少含两端）**，读数与画布都跟着变，且**每一档都不裁边**。
    只在默认档检查会漏：`transition` 的峰值标签只在滑块低端才顶出画布；
  - **滑块的参数范围必须落在模型的有效域内**：`transition` 的 `mid_b` 下限是 1930
    而非 1900，因为出生率必须晚于死亡率下降，否则增长率从窗口起点就单调下降，
    「峰值年」退化成窗口边界（那是产物，不是结论）；
  - 定值指示器跟踪的读数恒定（如 `growth` 的翻倍时间、`cycle` 的解析周期）。
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`。

## 扩展

- **加题型**：在 `hist_kernel.py` 加求解函数（+ `__main__` 自检），
  在 `generate.py` 加一个 `build_*`（含 `_agree` 对账 + `_evid_badge`）并注册进 `REGISTRY`。
  **新题型必须先决定证据力等级**，没有等级的页不许出。
- **加画板场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `template/parts/scene_dispatch.html` 加 case，然后
  `python ../../tools/compose_templates.py` 重新组装 `template/board.html`。
  **不要直接改 `board.html`**。
- 文字请用 `labelIn(...)` 而不是 `label(...)`：它会量出宽度并把锚点自动收进画布。
  「长注释顶出画布」在本项目已复发多次（概率/化学/地理各一次），别再手工试。
- 需要 RK4 的模型（SIR / LV）在画板侧也有一份 JS 实现；改内核的积分器时
  **必须同步改 JS**，并在浏览器里用同样的步长复验（`edu-history` 的 LV 周期
  实测 JS 与 Python 差 ≤0.05 年）。

## 数值出处分级

**现算**（内核由公式推出，无手写数字）
翻倍时间与指数倍数、logistic 的 10%/50%/90% 年份与 10→90 时长、人口转变的
增长率曲线与峰值、R₀、群体免疫阈值、SIR 峰值与数值解、Kaya 乘积、
Lotka-Volterra 的解析周期与数值周期、rank-size 斜率与反推的 α。

**实测 / 取自文献**（不是本页现算的）
`coverage-audit.md` 里已算过并报告的基准值（技术扩散 r=0.35、人口转变的一组平台值、
LV 的振幅—周期表）。它们作为**自检基准**使用，并在页面上标注为「审计已算过」。

**假设**（题面给定或为使图形可读而设定，逐条如下）
- `growth`：起点 1 倍，时间窗 0–100 年；滑块为年增长率 ∈ [0.5%, 10%]，题设 7%。
- `transition`：出生率 45‰→10‰、死亡率 35‰→10‰，陡度 15 年，死亡率中点固定 1920；
  滑块为出生率中点 ∈ **[1930, 2010]**，题设 1950。
- `diffusion`：扩散中点 t₀ = 1900；滑块为速率 ∈ [0.05, 0.60]，题设 0.35。
- `epidemic`：γ = 0.2/天（病程约 5 天），初始 S=0.99、I=0.01，积分 200 天；
  滑块为 R₀ ∈ [1, 6]，题设 3。
- `kaya`：P=1、E/GDP=0.5、CO₂/E=2；滑块为人均产出因子 ∈ [1, 4]，题设 2。
- `cycle`：r = m = 0.05、a = c = 1；滑块为初始偏离幅度 ∈ [0.05, 3.0]，题设 0.05。
- `zipf`：样本数固定 200，数据**由幂律定律本身生成**（不是真实城市数据）；
  滑块为 α ∈ [0.5, 2.5]，题设 1.0。

**三条必须写进步骤的边界**
1. 每页的证据力等级（①A/①B/①C）与其含义。
2. `transition` 的峰值年与 `cycle` 的周期**都不是可靠的历史结论**：前者取决于
   估出来的中点，后者还取决于不可观测的振幅。
3. 恒等式（Kaya）**有归因能力，没有预测能力** —— 把分解说成预测是最常见的误读。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页，
交互页能说清就别做视频。本技能产出的是**自包含的交互教学网页**，构建与校验都有成本，
不适合「随口问一句」的场景。

- 题目问的是**具体史实的真伪、原因或人物动机**——**本技能完全不覆盖**，
  这是历史学的 ③ 层。请直接说明，不要用模型硬套。
- 题目要**史料批判、史学史、史学流派**——同上，不可形式化，直接说明。
- 题目只要求**一个数值答案**（如「多少年翻倍」）——直接算并作答，不必做页。
- 题目是**纯数学增长/收敛**，与历史无关——用 `edu-math-sequences`
  （数列与三角）或 `edu-function-derivative`（函数与导数）。
- 题目是**传染病模型本身**（微分方程求解、稳定性）——本技能只到阈值与峰值，
  方程层面的内容请用 `edu-function-derivative` 或直接说明未覆盖。
- 题目要**用真实数据集**（各国人均 GDP 时序、城市人口表）——那属于 ①B 的
  **数据页**，需要出处/许可/指纹一整套，本技能不含；仓库内的
  `mental-models` 已有两次这样的实践，请走那条线。

## 目录结构

```
edu-history/
├── SKILL.md
├── lib/hist_kernel.py             # 模型/恒等式内核（7 组函数 + 48 条自检）+ EVIDENCE 分级
├── scripts/generate.py            # 注入模板 + 7 个 build_* + 读数对账 + 证据力徽章
└── template/
    ├── board.html                 # 组装产物（勿直接修改）
    └── parts/                     # 模板片段（改这里再 compose）
        ├── scene_functions.html   # 7 个 drawXxx + JS 版 RK4 + labelIn + 证据力徽章
        ├── scene_dispatch.html    # 场景分派
        ├── page_title.html        # 「可算的历史 · 交互学习」
        └── board_label.html       # 画板角标
```
