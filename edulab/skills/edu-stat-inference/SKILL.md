---
name: edu-stat-inference
description: >-
  把一道统计推断题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个可变参数滑块驱动实时重算的量 + 状态灯 + 定值指示器），中栏 KaTeX 分步解析，
  右栏 2D Canvas 画板（样本均值的直方图与理论正态、两种方差估计量的分布对比、
  逐条绘制并标色的置信区间、p 值的直方图、功效曲线、散点与残差、样本比例分布）。
  **所有分布都是内核真实蒙特卡洛跑出来的**（固定种子 ⇒ 可复现），
  理论值与模拟值并列给出、互相印证。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖抽样分布与标准误、
  无偏估计、置信区间与覆盖率、t 检验与 p 值、功效与样本量、最小二乘回归、
  比例的估计与检验等题型。
  其它 agent 也可调用本技能生成此类网页。形态与 edu-probability 平行（复用 seq-phys
  模板家族，并新增 histmean / histvar / ciplot / phist / powercurve / scatter /
  prophist 七种场景）。触发词：统计推断, 抽样分布, 标准误, 样本均值, 无偏估计, 无偏性,
  置信区间, 置信水平, 覆盖率, 假设检验, t 检验, z 检验, p 值, 显著性, 拒绝域,
  第一类错误, 第二类错误, 功效, 样本量, 效应量, 中心极限定理, 极大似然,
  最小二乘, 回归, 残差, 决定系数, R², 比例估计, 比例的检验, 解这道统计推断题,
  随机出一道统计题, 这张图里的统计题;
  statistical inference, sampling distribution, standard error, unbiased estimator,
  confidence interval, coverage, hypothesis testing, t test, p-value, significance,
  type I error, type II error, statistical power, sample size, effect size,
  central limit theorem, least squares, regression, residuals, R squared,
  proportion estimation, interactive statistics solution page.
---

# 统计推断交互教学网页 (edu-stat-inference)

把一道统计推断题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
**真实蒙特卡洛**内核驱动，2D 画板 + KaTeX 分步解析。

## 与相邻技能的边界（先看清再选技能）

| 技能 | 管什么 | 判据 |
| --- | --- | --- |
| `edu-probability` | **概率论**：古典概型、二项/超几何/正态、大数定律、CLT 本身 | 题目问「某个事件的概率是多少」 |
| **本技能** | **统计推断**：由样本反推总体（估计、区间、检验、回归） | 题目里有「样本」「置信」「检验」「p 值」「回归」 |
| `edu-cs` | 算法与数据结构（含简单统计量） | 题目是算法题 |

**判据**：题目是「**已知总体算概率**」——用 `edu-probability`；
「**已知样本推总体**」——用本技能。

## 依赖（重要）

计算核心 `lib/stat_kernel.py` **只用标准库**（`math` + `random`，t 分布用不完全贝塔函数的
连分式实现，不需要 scipy）。运行前确认：`python -c "import math, random"`（必然成立）。

**注意耗时**：`scripts/generate.py` 在**导入时**就要跑完全部蒙特卡洛
（约 150 万次抽样 + 2 万次 t 检验），实测约 **2–3 秒**，属正常。
若把模拟次数调大请留意耗时。

Windows 控制台打印 ✓ 报 UnicodeEncodeError 时先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-stat-inference
python scripts/generate.py list                   # 列出已注册题型
python scripts/generate.py ci ./sol.html          # 置信区间与覆盖率
python scripts/generate.py all ./output           # 全部题型
python scripts/generate.py random 7 ./random.html # 随机出题（seed=7）
python lib/stat_kernel.py                        # kernel 内置自检（77 条）
```

> 不传输出路径时默认写到**当前工作目录（cwd）**。

| key | 场景 | 主问题 |
| --- | --- | --- |
| `sampling` | `histmean` | 样本均值为什么也是随机变量？为什么是 $\\sqrt n$？ |
| `unbiased` | `histvar` | 样本方差为什么除以 $n-1$？偏差有多大？ |
| `ci` | `ciplot` | 「95% 置信」到底在说什么？红条为什么允许存在？ |
| `ttest` | `phist` | $H_0$ 为真时 p 值为什么是均匀的？ |
| `power` | `powercurve` | 功效是什么？要多大样本才有八成把握？ |
| `regression` | `scatter` | 最小二乘在最小化什么？$R^2$ 高就说明模型好吗？ |
| `proportion` | `prophist` | 比例的标准误从哪来？为什么 $p=0.5$ 最坏？ |

## 工作流程（AI 调用时）

1. **归一题面**：总体/样本/所求（估计量？区间？检验？），判断属于哪个题型。
2. **用 kernel 现算**（不要心算）：`gauss_cdf` `gauss_pdf` `t_cdf` `t_pdf` `z_critical`
   `t_critical` `se_mean` `simulate_means` `simulate_var_estimators`
   `ci_mean` `simulate_coverage` `t_statistic` `p_value_t` `simulate_pvalues`
   `power_two_sided` `simulate_power_curve` `ols_fit` `simulate_regression`
   `prop_se` `prop_ci_wald` `prop_z_test` `simulate_prop_dist` `hist`。
3. **组装数据**三段 `lesson` / `steps` / `board`；可照抄 `scripts/generate.py` 的 7 个 `build_*`。
4. **自检**：kernel 自检全过（77 条）；答案卡 == 末步展示值 == 画板读数初值；
   起本地静态服务，滑块走过**每一个档位**，确认
   ① 无控制台报错 ② **画布指纹数 = 档位数** ③ 不裁边
   ④ 状态灯在该翻转的参数值上翻转。

## 本技能特有的坑

### 1. 模拟必须固定种子，否则基线对不上
项目闸门 `check_skills.py` 会比对产物与基线。含随机的内核**一律用 `random.Random(seed)`**
（而不是全局 `random`），种子逐档位错开但写死。这样「重跑生成」得到的是**同一个文件**，
模拟结果才可复现、可审计。

### 2. 模拟值要与理论值**并列**给出
本技能的每页都同时显示「模拟值」与「理论值」，并断言两者在合理误差内接近。
这不是装饰 —— 它是**用模拟验证理论**，也顺手保证了模拟代码本身没写错。

### 3. `arr()` 的舍入位数要与对账容差匹配
把模拟结果写成数组字面量（`[a,b,c][idx-1]`）供页面按档位取用时，
默认保留 6 位小数。此时 `_agree` 的容差**不能再用 1e-12**，否则会因为舍入而误报。
用 1e-6。

### 4. 又踩到「`<` 判据会减掉 1e-9」
外壳的 `<` 是 `v < rhs - 1e-9`。本技能里「δ 是否等于 0」用 `rhs = 1e-9` 会**恒假** ——
必须给足余量（用 `1e-6`）。这条在 `edu-physics-thermal` 的「整数个半衰期」上已经踩过一次，
**这是第二次**，说明凡是「判等」都要刻意留余量。

### 5. 沿用既有两条（详见 `edu-physics-thermal` 的 SKILL.md）
① 场景字段要是表达式或数组，不能写死某个档位的具体数值；
② 状态灯文案是**纯文本**，不能写 `$…$`；一行文字不超过约 28 个汉字（11px）。

## 数值出处分级

### ① 现算（**真实模拟或精确公式**，不手写数字）
抽样分布与标准误、两种方差估计量的期望、覆盖率、t 统计量与 p 值、
p 值在 $H_0$ 下的分布、功效曲线与所需样本量、最小二乘拟合物与 $R^2$、
比例的抽样分布与区间。

> 特别说明：**分布不是画出来的理论曲线冒充模拟结果**。
> 页面上的直方图来自内核真的抽了 800～4000 次样；
> 理论曲线是另外叠加上的参考线。两者贴合本身就是结论。

### ② 实测 / 教材常数
$z$ 与 $t$ 的临界值、正态与 t 分布的 CDF（都由内核数值计算，不是查表）。
热力学式的「标准表」在此不涉及。

### ③ 约定（示例参数与模拟规模）
- `sampling`：总体 $N(50, 10^2)$；每档模拟 800 次；样本量档位 $n\in\{1,4,9,\dots,64\}$，题设 25。
- `unbiased`：$\sigma^2 = 9$；每档模拟 4000 次；$n\in\{2,5,10,30\}$，题设 10。
- `ci`：$\mu = 100$、$\sigma = 15$、$n = 25$；每档模拟 60 个区间；
  水平档位 $\{50\%,60\%,\dots,99\%\}$，题设 95%。
- `ttest`：$n = 20$、每次检验模拟 3000 次、$\alpha = 0.05$；
  $\delta\in\{0,0.1,0.2,0.3,0.5,0.8,1.2\}$，题设 0。
- `power`：$\alpha = 0.05$、$\sigma = 1$；$n\in\{5,10,20,40,80,160\}$，题设 20；
  功效曲线用解析公式画 41 个点（不模拟）。
- `regression`：真值 $y = 1+2x$、$n = 30$、$x\in[0,10]$；
  $\sigma\in\{0,0.3,0.7,1.2,2.0,3.0\}$，题设 1.2。
- `proportion`：真值 $p = 0.5$；每档模拟 800 次；
  $n\in\{10,20,50,100,200,500\}$，题设 100。
- 画板的绘图框与坐标范围为**约定的显示参数**，不影响任何计算。

### 未覆盖
卡方检验与方差分析、非参数检验（秩和、符号检验）、贝叶斯推断（后验分布、可信区间）、
多重比较校正、logistic 回归、时间序列、实验设计（区组、正交表）、
极大似然估计的一般解法。遇到请直接说明未覆盖。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页。
本技能产出的是**自包含的交互教学网页**，构建与校验都有成本。

- 只要求**一个数值答案**（如「求 p 值」）——直接算并作答，不必做页。
- 题目是**概率论**（已知总体求事件概率）——用 `edu-probability`。
- 题目是**算法与数据结构**——用 `edu-cs`。
- 题目是**一元/多元微积分**——用 `edu-function-derivative` / `edu-multivariable-calc`。

## 目录结构

```
edu-stat-inference/
├── SKILL.md
├── lib/stat_kernel.py           # 内核（8 组函数 + 77 条自检，仅用标准库）
├── scripts/generate.py          # 注入模板 + 7 个 build_* + 全部蒙特卡洛在导入时跑完
└── template/
    ├── board.html               # 组装产物（勿直接修改）
    └── parts/                   # 模板片段（改这里再 compose）
        ├── scene_functions.html # 7 个 drawXxx + histBars/overlayCurve/axesBox
        ├── scene_dispatch.html
        ├── page_title.html
        └── board_label.html
```

## 扩展

- **加题型**：在 `stat_kernel.py` 加计算/模拟函数（+ `__main__` 自检），
  在 `generate.py` 加 `build_*`（含对账）并注册进 `REGISTRY`。
  **模拟记得用 `random.Random(seed)`**。
- **加场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `scene_dispatch.html` 加 case，然后 `python ../../tools/compose_templates.py`
  重新组装 `template/board.html`。**不要直接改 `board.html`**；
  新技能还要记得把名字加进 `compose_templates.py` 的 `FAMILIES` 用户列表，
  否则片段会被忽略（本轮就漏了一次）。
