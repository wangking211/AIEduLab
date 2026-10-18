---
name: edu-economics
description: >-
  把一道经济学题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个可变参数滑块驱动实时重算的量 + 状态灯 + 定值指示器），中栏 KaTeX 分步解析，
  右栏 2D Canvas 经济学画板（供需曲线与两种剩余的面积、需求价格弹性与单位弹性分界、
  索洛图上的投资线与持平投资线、Cobb–Douglas 曲线与切线斜率、需求/边际收益/边际成本
  三线与垄断加成、2×2 收益矩阵与纳什均衡高亮、洛伦兹曲线与基尼面积），
  每一页都带**证据力徽章**（①A 纯数学/恒等式 · ①B 模型参数靠估 · ①C 形态①证据力③）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖供需均衡与
  消费者/生产者剩余、需求价格弹性、索洛增长模型的稳态、Cobb–Douglas 生产函数
  （边际产量/规模报酬/欧拉定理）、垄断定价与勒纳指数、2×2 纯策略纳什均衡、
  洛伦兹曲线与基尼系数等题型，统一由 sympy 精确内核驱动（答案、分步数值、
  画板读数同源一致）。其它 agent 也可调用本技能生成此类网页。形态与 edu-history
  平行（复用 seq-phys 模板家族，并新增 market / elastic / solow / cobb /
  monopoly / nash / lorenz 七种场景）。触发词：经济学, 微观经济学, 宏观经济学,
  供需, 供给, 需求, 均衡价格, 均衡数量, 消费者剩余, 生产者剩余, 总剩余, 弹性,
  需求价格弹性, 单位弹性, 富有弹性, 缺乏弹性, 索洛模型, 增长模型, 稳态, 人均资本,
  储蓄率, 持平投资, 生产函数, Cobb-Douglas, 柯布道格拉斯, 边际产量, 规模报酬,
  欧拉定理, 垄断, 边际收益, 边际成本, 勒纳指数, 加成, 定价, 纳什均衡, 博弈,
  猎鹿博弈, 囚徒困境, 最优反应, 基尼系数, 洛伦兹曲线, 收入不平等, 解这道经济学题,
  随机出一道经济学题, 这张图里的经济学题; economics, microeconomics, supply and
  demand, market equilibrium, consumer surplus, producer surplus, price elasticity,
  Solow model, steady state, production function, Cobb-Douglas, marginal product,
  returns to scale, Euler theorem, monopoly, marginal revenue, Lerner index,
  Nash equilibrium, game theory, stag hunt, prisoner's dilemma, Gini coefficient,
  Lorenz curve, income inequality, interactive economics solution page.
---

# 经济学交互教学网页 (edu-economics)

把一道经济学题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
sympy 精确内核驱动，经济学画板 + KaTeX 分步解析。

## 证据力分级（本技能的第一条纪律）

**经济学的最大风险是把「模型」当成「预测」。** 所以沿用 `edu-history` 的做法：

| 等级 | 含义 | 本技能的实例 |
| --- | --- | --- |
| **①A** | 纯数学 / 恒等式 —— 图上的数错不了 | 供需交点、剩余面积、欧拉定理、勒纳指数 = 1/\|ε\|、纳什均衡判定、基尼系数 |
| **①B** | 模型：内核确定，**参数靠估** | 弹性值、索洛的 s/n/g/δ/α |
| **①C** | 形态①、证据力③ | **政策效果预测** —— 只能说明「如果假设成立会怎样」 |

**裸奔的图 = 误导。** 一页没有徽章就不该出 —— `_evid_badge()` 在每个 `build_*` 里强制。

**明确不做**（写进 SKILL.md、也写进步骤）：计量经济学的回归推断（那是统计课）、
博弈论的一般理论（要证明）、经济思想史（叙事）、任何需要**真实宏观数据表**的内容
（那属于 ①B 数据页，要走出处/许可/指纹一整套，见 `mental-models` 的两次实践）。

## 依赖（重要）

计算核心 `lib/econ_kernel.py` 依赖 **sympy**。运行前确认有能 import sympy 的解释器：
`python -c "import sympy"`。

**缺库时**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python -m pip install sympy`）或换一个已装该库的解释器；**不要未经询问直接装**。
Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-economics
python scripts/generate.py list                      # 列出已注册题型
python scripts/generate.py supply ./sol.html         # 供需均衡
python scripts/generate.py all ./output              # 全部题型
python scripts/generate.py random 7 ./random.html    # 随机出题（seed=7）
python lib/econ_kernel.py                          # kernel 内置自检（49 条）
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

七个题型 key、场景与**证据力等级**：

| key | 场景 | 证据力 | 主问题 |
| --- | --- | --- | --- |
| `supply` | `market` | ①A | 均衡在哪？两种剩余各是多少？ |
| `elasticity` | `elastic` | **①B** | 哪里富有弹性？为什么涨价对收入的影响会反转？ |
| `growth` | `solow` | **①B** | 稳态由什么决定？为什么是两条线的交点？ |
| `cobb_douglas` | `cobb` | ①A | 边际产量怎么算？欧拉定理为什么成立？ |
| `monopoly` | `monopoly` | ①A | 垄断者定产定价的依据？加成与弹性什么关系？ |
| `nash` | `nash` | ①A | 有几个纯策略均衡？临界值从哪来？ |
| `gini` | `lorenz` | ①A | 基尼系数怎么从曲线算出来？ |

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面归一成：模型形式、参数、所求、符号约定、语言。先判断属于哪个题型。

### 第 2 步：用 kernel 精确计算（不要心算）
`lib/econ_kernel.py` 提供：
- 供需：`demand_q` `supply_q` `market_equilibrium` `consumer_surplus` `producer_surplus` `total_surplus`
- 弹性：`point_elasticity` `arc_elasticity` `elasticity_label`
- 增长：`solow_steady` `solow_output` `solow_convergence_time`
- 生产：`cobb_douglas` `marginal_products` `returns_to_scale` `euler_check`
- 垄断：`monopoly_optimum` `monopoly_profit` `lerner_index`
- 博弈：`nash_2x2` `best_responses`
- 分配：`lorenz` `gini_from_beta` `gini_from_curve`
- 分级：`EVIDENCE`（三档的定义与措辞）

### 第 3 步：组装数据并注入模板
数据三段 `lesson` / `steps` / `board`。可直接照抄 `scripts/generate.py` 的 7 个 `build_*`。

**每个读数表达式都必须与内核值对账**：`_agree(label, expr, want)` 在构建期用等价的
Python 实现求值一次再比对（分段式写成三目链即可，`_js_to_py()` 会翻成 Python 验证）。

### 第 4 步：自检（正确性方案）
- kernel 答案 == 答案卡 `lesson.answer` == 末步展示值 == 画板读数初值，四者一致。
- `python lib/econ_kernel.py` 自检全过（49 条）。
- 起本地静态服务预览检查：
  - 无控制台报错；
  - **逐个片段试渲染 LaTeX**（`katex.renderToString(frag,{throwOnError:true})`）；
  - 滑块拨到**多个档位（至少含两端）**，读数与画布都跟着变，且**每一档都不裁边**；
  - 定值指示器跟踪的读数恒定（`supply` 的 CS≡PS、`growth` 的 投资≡持平投资、
    `cobb_douglas` 的欧拉左端≡Y、`gini` 的完全平等线面积≡1/2）；
  - 状态灯在该翻转的参数值上翻转（`nash` 的 t=2、`gini` 的 β=1）。
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`。

## 扩展

- **加题型**：在 `econ_kernel.py` 加计算函数（+ `__main__` 自检），
  在 `generate.py` 加一个 `build_*`（含 `_agree` 对账 + `_evid_badge`）并注册进 `REGISTRY`。
  **新题型必须先决定证据力等级**，没有等级的页不许出。
- **加画板场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `template/parts/scene_dispatch.html` 加 case，然后
  `python ../../tools/compose_templates.py` 重新组装 `template/board.html`。
  **不要直接改 `board.html`**。

### 一条通用画板约定（本轮踩到的）

**文字一律用 `labelIn`，并且注意「文字比视窗还宽」这种情形。**
`labelIn` 会按对齐方式把锚点收进画布；但如果文字本身比视窗宽，
`x1 − w − pad` 会算出**负数**，于是标签被推到画布外面去。

本轮的 `cobb_douglas` 就是这么贴边的：一个 40 字的说明 ≈ 13.6 世界单位，
而视窗只有 10 单位宽。修法是两条一起上：

1. `labelIn` 里再兜一次 `Math.max(x0 + pad, …)`；
2. **把长说明拆短**（视窗宽度除以字号，就是能放下的字数上限）。

**经验值**：10 世界单位的视窗、11px 字号下，一行标签**不超过 28 个汉字**。

## 数值出处分级

**现算**（内核真算/真积分，无手写数字）
供需均衡点、消费者/生产者/总剩余、点弹性与弧弹性、索洛稳态资本与产出、
Cobb–Douglas 的产出与边际产量与欧拉左端、垄断最优产量/价格/利润/勒纳指数、
2×2 纯策略纳什均衡（穷举）、洛伦兹曲线值、基尼系数（解析式 + 数值积分双路）。

**模型假设**（本技能所有参数都不是实测值，逐条如下）
- `supply`：需求 $q = a - 2p$、供给 $q = 2 + 2p$；滑块为 $a\in[6,16]$，题设 10。
- `elasticity`：需求 $q = 10 - 2p$；滑块为 $p\in[0.5,4.5]$，题设 2。
- `growth`：$\alpha = 0.3$、$n+g+\delta = 0.10$；滑块为 $s\in[0.05,0.5]$，题设 0.2。
- `cobb_douglas`：$A=1$、$L=9$、$\alpha=0.5$；滑块为 $K\in[1,20]$，题设 4。
- `monopoly`：需求 $p = 10 - q$；滑块为 $MC\in[0.5,8]$，题设 2。
- `nash`：猎鹿博弈的收益矩阵，合作收益 $t\in[0,4]$，题设 1。
- `gini`：洛伦兹曲线 $L(x) = x^\beta$；滑块为 $\beta\in[1,3]$，题设 2。

**这些参数都是为了图形清晰而选的，不是任何真实经济体的估计值。**
凡引用本页数字，必须连同这条声明一起引用。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页，
交互页能说清就别做视频。本技能产出的是**自包含的交互教学网页**，构建与校验都有成本，
不适合「随口问一句」的场景。

- 题目要**真实宏观/微观数据**（某国 GDP、失业率、某行业弹性）——本技能不含数据集，
  请直接说明；那需要走出处/许可/指纹一整套数据页流程。
- 题目要**计量经济学**（回归、工具变量、面板数据、因果识别）——本技能不覆盖，
  请直接说明。
- 题目要**博弈论的一般理论**（混合策略的严格证明、子博弈完美、重复博弈定理）
  ——本技能只做 2×2 纯策略的穷举判定。
- 题目要**经济思想史或学派之争**——叙事，属 ③，直接说明不覆盖。
- 题目其实是**纯数学**（积分、微分、最优化）——用 `edu-function-derivative`
  或 `edu-ode-dynamics`。
- 题目其实是**统计推断**（置信区间、假设检验）——用 `edu-probability`。
- 题目其实是**线性规划 / 投入产出表**——用 `edu-linear-algebra`。

## 目录结构

```
edu-economics/
├── SKILL.md
├── lib/econ_kernel.py             # 供需/弹性/增长/生产/垄断/博弈/分配内核（49 条自检）+ EVIDENCE
├── scripts/generate.py            # 注入模板 + 7 个 build_* + 读数对账 + 证据力徽章
└── template/
    ├── board.html                 # 组装产物（勿直接修改）
    └── parts/                     # 模板片段（改这里再 compose）
        ├── scene_functions.html   # 7 个 drawXxx + labelIn（含宽度兜底）
        ├── scene_dispatch.html    # 场景分派
        ├── page_title.html        # 「经济学 · 交互学习」
        └── board_label.html       # 画板角标
```
