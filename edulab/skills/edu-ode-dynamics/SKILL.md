---
name: edu-ode-dynamics
description: >-
  把一道常微分方程 / 动力系统题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个可变参数滑块驱动实时重算的量 + 状态灯 + 定值指示器），中栏 KaTeX 分步解析，
  右栏 2D Canvas 动力系统画板（方向场与解曲线、欧拉法及 RK4 与精确解的误差对比、
  阻尼振动的三种形态与指数包络、受迫振动的稳态振幅响应与共振峰、相平面上的向量场
  与轨道、Logistic 的 S 曲线、Lotka–Volterra 的闭合轨道与守恒量）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖一阶方程与方向场、
  欧拉法与 RK4 的误差阶、二阶常系数线性方程（欠阻尼/临界/过阻尼）、受迫振动与共振、
  线性系统的平衡点分类与相平面、Logistic 方程、Lotka–Volterra 相图与守恒量等题型，
  统一由精确解与**真跑**的数值积分共同驱动（答案、分步数值、画板读数同源一致）。
  内容按 MIT 18.03 的知识点组织。其它 agent 也可调用本技能生成此类网页。
  形态与 edu-linear-algebra 平行（复用 seq-phys 模板家族，并新增 slopefield /
  numerror / oscillator / resonance / phaseplane / logisticode / lvplane 七种场景）。
  触发词：常微分方程, 微分方程, 动力系统, 方向场, 斜率场, 解曲线, 初值问题,
  欧拉法, RK4, 数值解, 步长, 误差阶, 阻尼振动, 欠阻尼, 临界阻尼, 过阻尼, 阻尼比,
  包络, 受迫振动, 共振, 共振频率, 幅频特性, 相平面, 相图, 平衡点, 稳定性, 鞍点,
  结点, 相图焦点, 中心, 特征值, Logistic, 逻辑斯蒂, S曲线, 环境容纳量, 捕食者,
  被捕食, Lotka-Volterra, 守恒量, 闭合轨道, 解这道微分方程题, 随机出一道微分方程题,
  这张图里的微分方程题; ordinary differential equations, ODE, dynamical systems,
  direction field, slope field, initial value problem, Euler method, RK4, numerical
  solution, step size, error order, damped oscillation, underdamped, critically
  damped, overdamped, damping ratio, forced oscillation, resonance, phase plane,
  equilibrium, stability, saddle, equilibrium node, spiral, equilibrium center, Logistic equation, carrying
  capacity, predator-prey, Lotka-Volterra, conserved quantity, closed orbit,
  interactive differential equations solution page.
---

# 常微分方程与动力系统交互教学网页 (edu-ode-dynamics)

把一道常微分方程 / 动力系统题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
精确解与数值积分共同驱动，动力系统画板 + KaTeX 分步解析。知识点按 **MIT 18.03** 组织。

**MIT OCW 版权提醒**：18.03 的讲义、习题、视频受 CC BY-NC-SA 约束，**不可搬用**。
本技能只借鉴它的知识点与讲解顺序（思想不受版权保护），内容全部自算自绘。

## 依赖（重要）

计算核心 `lib/ode_kernel.py` 依赖 **sympy**（用它的特征值与化简）。运行前确认有能
import sympy 的解释器：`python -c "import sympy"`。

**缺库时**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python -m pip install sympy`）或换一个已装该库的解释器；**不要未经询问直接装**。
Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-ode-dynamics
python scripts/generate.py list                      # 列出已注册题型
python scripts/generate.py damped ./sol.html         # 阻尼振动
python scripts/generate.py all ./output              # 全部题型
python scripts/generate.py random 7 ./random.html    # 随机出题（seed=7）
python lib/ode_kernel.py                           # kernel 内置自检（45 条）
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

七个题型 key 与画板场景的对应：

| key | 场景 | 主问题 |
| --- | --- | --- |
| `firstorder` | `slopefield` | 方向场怎么读？为什么所有解最终挤向同一条直线？ |
| `euler` | `numerror` | 欧拉法为什么会系统性偏离？RK4 好在哪里？ |
| `damped` | `oscillator` | 阻尼比怎样决定振荡与不振荡？包络是什么？ |
| `forced` | `resonance` | 振幅什么时候最大？为什么共振频率不是固有频率？ |
| `phase` | `phaseplane` | 平衡点怎么分类？为什么轨道一定是螺旋？ |
| `logistic` | `logisticode` | 为什么增长率先升后降？两个平衡点谁稳定？ |
| `predator` | `lvplane` | 轨道为什么闭合？守恒量是什么？ |

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面归一成：方程 / 参数 / 初值 / 所求、符号约定、语言。先判断属于哪个题型。

### 第 2 步：用 kernel 精确计算（不要心算）
`lib/ode_kernel.py` 提供：
- 积分：`euler_system` `rk4_system` `integrate_until`（f(t, y) 接标量 t 与向量 y）
- 一阶：`first_order_slope` `first_order_exact`
- 阻尼：`damping_type` `damped_solution` `damped_period`
- 受迫：`forced_amplitude` `resonance_omega` `resonance_amplitude`
- 线性：`linear_eigen` `classify_2x2`
- Logistic：`logistic_solution` `logistic_time_to` `logistic_max_rate` `logistic_equilibria`
- 捕食者：`lv_equilibria` `lv_conserved` `lv_flow`

### 第 3 步：组装数据并注入模板
数据三段 `lesson` / `steps` / `board`。可直接照抄 `scripts/generate.py` 的 7 个 `build_*`。

**读数表达式必须与内核值对账**：`_agree(label, expr, want)` 在构建期用等价的 Python
实现求值一次再比对。三分支（欠/临界/过阻尼）那种分段式也能写，`_js_to_py()` 会把
三目翻成 Python 表达式来验证。

**数值解进不了读数表达式**（欧拉法/RK4 的结果没有闭式），所以：读数只放**有闭式的量**
（精确解、步长、参数化系数），数值解与误差放在画布上由 JS 真跑后标注。

### 第 4 步：自检（正确性方案）
- kernel 答案 == 答案卡 `lesson.answer` == 末步展示值 == 画板读数初值，四者一致。
- `python lib/ode_kernel.py` 自检全过（45 条）。
- 起本地静态服务预览检查：
  - 无控制台报错；
  - **逐个片段试渲染 LaTeX**（`katex.renderToString(frag,{throwOnError:true})`）——
    整页 `throwOnError:false` 不会把畸形公式当错误；
  - 滑块拨到**多个档位（至少含两端）**，读数与画布都跟着变，且**每一档都不裁边**；
  - 定值指示器跟踪的读数恒定（`firstorder` 的渐近线、`euler` 的精确解、`phase` 的 det）。
- **数值解要与内核对照**：在浏览器里用同样的步长跑一遍 JS 的 `odeEuler`/`odeRk4`，
  末值必须与 `ode_kernel` 逐位一致（实测：n=100 时欧拉 4.005920529220335 vs
  4.0059205292）。
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`。

## 扩展

- **加题型**：在 `ode_kernel.py` 加求解/积分函数（+ `__main__` 自检），
  在 `generate.py` 加一个 `build_*`（含 `_agree` 对账）并注册进 `REGISTRY`。
- **加画板场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `template/parts/scene_dispatch.html` 加 case，然后
  `python ../../tools/compose_templates.py` 重新组装 `template/board.html`。
  **不要直接改 `board.html`**。

### 三条画板约定

1. **文字一律用 `labelIn`**（量宽后把锚点收进画布），不要用 `label`。
2. **轨道一律用 `plotPolyClip`**：不稳定平衡点附近的轨道会**指数发散**
   （本例 $k>0$ 时 14 年能涨到 $10^6$），不裁剪就直接冲出绘图框。
3. 绘图框用 `mkPlot(px0, px1, py0, py1, xr, yr)` 建，坐标映射与裁剪都基于它。

### 数值健壮性的一个坑（本轮踩过）

过阻尼解**不能**写成 $e^{-\zeta t}[y_0\cosh(\omega_h t) + \cdots]$ ——
$\omega_h t$ 稍大（$t=300$ 时是 848）就 `OverflowError`，而且它是两个巨大指数项
**相减**，数值上也不稳。要改成两个指数项**之和**
$y = Ae^{\lambda_1 t} + Be^{\lambda_2 t}$，各项都单调衰减。
**通用判据**：凡闭式解里出现 $\cosh/\sinh$ 或两个大数相减，就该改写。

## 数值出处分级

**现算**（内核由公式或真积分推出，无手写数字）
一阶线性方程的精确解、欧拉法与 RK4 的数值解、阻尼振动三种情形的解与准周期、
受迫振动的稳态振幅与共振频率与峰值振幅、线性系统的特征值与平衡点分类、
Logistic 的精确解与到达时间与最大增长率、Lotka–Volterra 的平衡点与守恒量。

**教材常数 / 约定**
- 受迫振动的固有频率取 $\omega_0 = 1$、激励幅值 $F = 1$（无量纲化）。
- Lotka–Volterra 取 $r = m = 0.05$、$a = c = 1$（量纲已归一）。
- 这些取值是为了让闭式解干净、图形可读，不是实测值。

**假设**（每题的滑块范围与题设值，逐条如下）
- `firstorder`：$y' = t-y$；滑块为初值 $y_0\in[-2,3]$，题设 0。
- `euler`：$y'=t-y$、$y(0)=0$、区间 $[0,5]$；滑块为步数 $n\in[5,100]$，题设 20。
- `damped`：$y''+2\zeta y'+y=0$、$y(0)=1$、$y'(0)=0$；滑块 $\zeta\in[0,2.5]$，题设 0.2。
- `forced`：$y''+2\zeta y'+y=\cos\omega t$、$\zeta=0.15$；滑块 $\omega\in[0,2.6]$，题设 1.0。
- `phase`：$A=\begin{pmatrix}k&1\\-1&k\end{pmatrix}$；滑块 $k\in[-1,1]$，题设 −0.5。
- `logistic`：$K=1$、$y_0=0.05$；滑块为 $r\in[0.1,2.0]$，题设 0.8。
- `predator`：$r=m=0.05$、$a=c=1$、$E_0=0.05$；滑块为 $N_0\in[0.02,0.12]$，题设 0.08。

**未覆盖**：拉普拉斯变换、级数解与 Frobenius 方法、Sturm–Liouville 理论、
偏微分方程、刚性方程与隐式方法、混沌与分岔的严格理论、非线性系统的
Lyapunov 函数构造。遇到请直接说明未覆盖。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页，
交互页能说清就别做视频。本技能产出的是**自包含的交互教学网页**，构建与校验都有成本，
不适合「随口问一句」的场景。

- 题目只要求**一个数值答案**（如「$y(5)$ 等于多少」）——直接算并作答，不必做页。
- 题目要**拉普拉斯变换、级数解、Sturm–Liouville**——本技能不含，直接说明未覆盖。
- 题目是**偏微分方程**（热方程、波动方程、Laplace 方程）——超出一维 ODE 范围，
  请直接说明。
- 题目要**混沌与分岔的严格分析**（Lyapunov 指数、同宿轨道、中心流形）
  ——本技能只做到相图与平衡点分类，请直接说明未覆盖。
- 题目其实是**线性代数**（矩阵分解、特征值计算本身）——用 `edu-linear-algebra`。
- 题目其实是**高中导数与切线**——用 `edu-function-derivative`。
- 题目是**传染病 SIR 的阈值与峰值**——用 `edu-history`（那里有 R₀ 与群体免疫）。
- 题目要的是**生物种群的生态学含义**（K 值的生态解释、种群调节机制）——用 `edu-biology`。
## 目录结构

```
edu-ode-dynamics/
├── SKILL.md
├── lib/ode_kernel.py              # 精确解 + 真积分内核（7 组函数 + 45 条自检）
├── scripts/generate.py            # 注入模板 + 7 个 build_* + 读数对账 + 三目翻译器
└── template/
    ├── board.html                 # 组装产物（勿直接修改）
    └── parts/                     # 模板片段（改这里再 compose）
        ├── scene_functions.html   # 7 个 drawXxx + 真跑的 RK4/欧拉 + 折线裁剪
        ├── scene_dispatch.html    # 场景分派
        ├── page_title.html        # 「常微分方程与动力系统 · 交互学习」
        └── board_label.html       # 画板角标
```
