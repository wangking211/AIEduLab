---
name: edu-signals
description: >-
  把一道信号与系统题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个可变参数滑块驱动实时重算的量 + 状态灯 + 定值指示器），中栏 KaTeX 分步解析，
  右栏 2D Canvas 信号画板（卷积的滑动重叠、离散卷积的逐项相乘、傅里叶级数逼近方波
  与 Gibbs 过冲、采样点与混叠后的表观波形、矩形脉冲的时频对偶、RC 低通的幅频曲线、
  z 平面极点与脉冲响应）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖连续卷积、
  离散卷积、傅里叶级数与 Gibbs 现象、采样定理与混叠、时宽频宽积（时频互易）、
  RC 低通频率响应、一阶离散系统的极点与稳定性等题型，统一由精确内核与
  **真跑**的求和/积分共同驱动（答案、分步数值、画板读数同源一致）。
  内容按 MIT 6.003 的知识点组织。其它 agent 也可调用本技能生成此类网页。
  形态与 edu-ode-dynamics 平行（复用 seq-phys 模板家族，并新增 convolve / dconv /
  fseries / alias / fdomain / freqresp / zplane 七种场景）。触发词：信号与系统,
  卷积, 连续卷积, 离散卷积, 脉冲响应, 单位冲激, 滑动平均, 傅里叶级数, 谐波,
  Gibbs 现象, 过冲, 方波, 采样, 采样定理, 奈奎斯特, 混叠, 折叠频率, 抗混叠,
  时宽频宽积, 时频互易, 不确定性原理, 频谱, sinc, 主瓣, 频率响应, 幅频特性,
  相频特性, 截止频率, 低通, 高通, RC 电路, 传递函数, 极点, 单位圆, 稳定性,
  z 变换, 解这道信号题, 随机出一道信号与系统题, 这张图里的信号题;
  signals and systems, convolution, impulse response, Fourier series, harmonics,
  Gibbs phenomenon, overshoot, square wave, sampling, Nyquist, aliasing,
  time-bandwidth product, spectrum, sinc, frequency response, cutoff frequency,
  low-pass filter, RC circuit, transfer function, pole, unit circle, stability,
  z-transform, interactive signals and systems solution page.
---

# 信号与系统交互教学网页 (edu-signals)

把一道信号与系统题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
精确内核与真跑求和/积分共同驱动，信号画板 + KaTeX 分步解析。按 **MIT 6.003** 组织。

**MIT OCW 版权提醒**：6.003 的讲义、习题、视频受 CC BY-NC-SA 约束，**不可搬用**。
本技能只借鉴它的知识点与讲解顺序（思想不受版权保护），内容全部自算自绘。

## 依赖（重要）

计算核心 `lib/signal_kernel.py` 依赖 **sympy**（离散卷积用 sympy 精确整数）。
运行前确认有能 import sympy 的解释器：`python -c "import sympy"`。

**缺库时**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python -m pip install sympy`）或换一个已装该库的解释器；**不要未经询问直接装**。
Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-signals
python scripts/generate.py list                      # 列出已注册题型
python scripts/generate.py convolution ./sol.html     # 连续卷积
python scripts/generate.py all ./output              # 全部题型
python scripts/generate.py random 7 ./random.html    # 随机出题（seed=7）
python lib/signal_kernel.py                         # kernel 内置自检（57 条）
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

七个题型 key 与画板场景的对应：

| key | 场景 | 主问题 |
| --- | --- | --- |
| `convolution` | `convolve` | 为什么两个矩形卷出三角形？ |
| `discrete` | `dconv` | 离散卷积怎么逐项算？为什么输出更长？ |
| `fourier` | `fseries` | 谐波多了为什么过冲不消失？ |
| `sampling` | `alias` | 采样率不足时看到的频率是什么？ |
| `spectrum` | `fdomain` | 为什么「时宽 × 第一零点」恒为 1？ |
| `filter` | `freqresp` | 截止频率处 |H| 与相位为什么总是那两个数？ |
| `discrete_sys` | `zplane` | 极点在哪里？为什么 |a|<1 才稳定？ |

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面归一成：信号/系统、参数、所求、单位、语言。先判断属于哪个题型。

### 第 2 步：用 kernel 精确计算（不要心算）
`lib/signal_kernel.py` 提供：
- 卷积：`rect` `tri` `conv_rect_rect` `discrete_conv`
- 傅里叶：`square_partial` `square_partial_peak` `gibbs_limit` `square_jump`
- 采样：`aliased_freq` `sampling_rate_ok`
- 时频：`sinc` `rect_spectrum` `mainlobe_width`
- 滤波：`rc_cutoff` `rc_mag` `rc_phase_deg` `rc_H`
- 离散系统：`disc_pole` `disc_stable` `disc_impulse` `disc_conv_system`

### 第 3 步：组装数据并注入模板
数据三段 `lesson` / `steps` / `board`。可直接照抄 `scripts/generate.py` 的 7 个 `build_*`。

**读数表达式必须与内核值对账**：`_agree(label, expr, want)` 在构建期用等价的 Python
实现求值一次再比对。分段式（如 `y[n]` 的 6 段）写成三目链即可，`_js_to_py()` 会翻成
Python 表达式验证。

**序列型结果进不了读数表达式**时（如部分和随谐波数变化），读数只放**闭式的量**，
数列/曲线放画布上由 JS 真跑。

### 第 4 步：自检（正确性方案）
- kernel 答案 == 答案卡 `lesson.answer` == 末步展示值 == 画板读数初值，四者一致。
- `python lib/signal_kernel.py` 自检全过（57 条）。
- 起本地静态服务预览检查：
  - 无控制台报错；
  - **逐个片段试渲染 LaTeX**（`katex.renderToString(frag,{throwOnError:true})`）；
  - 滑块拨到**多个档位（至少含两端）**，读数与画布都跟着变，且**每一档都不裁边**；
  - 定值指示器跟踪的读数恒定（`spectrum` 的时宽频宽积、`filter` 的 |H(f_c)|、
    `discrete` 的输出长度）；
  - **数值解与内核对照**：在浏览器里用同一套公式真跑一遍
    （实测：离散卷积 JS `[1,3,6,6,4,1]` 与内核一致；混叠公式
     `fs=0.6 → 0`、`2.0 → 0.8` 两边一致）。
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`。

## 扩展

- **加题型**：在 `signal_kernel.py` 加计算函数（+ `__main__` 自检），
  在 `generate.py` 加一个 `build_*`（含 `_agree` 对账）并注册进 `REGISTRY`。
- **加画板场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `template/parts/scene_dispatch.html` 加 case，然后
  `python ../../tools/compose_templates.py` 重新组装 `template/board.html`。
  **不要直接改 `board.html`**。

### 两条画板约定

1. **文字一律用 `labelIn`**（量宽后把锚点收进画布），不要用 `label`。
2. **曲线一律用 `sgPolyClipImpl`** —— 但注意它吃的是**数据坐标**，
   内部会做 P.X/P.Y（数据→世界）与 SX/SY（世界→像素）两次映射，
   再按世界坐标的绘图框裁剪。

   **本轮踩过的坑**：第一版把数据坐标直接当像素用、又拿它跟世界坐标的框去裁剪，
   两处都错位 —— 于是曲线被画到画布角落并贴边（`fourier` 与 `spectrum` 两页）。
   `edu-ode-dynamics` 的 `plotPolyClip` 是正确写法，可作对照。

## 数值出处分级

**现算**（内核真算/真积分，无手写数字）
矩形卷积的三角结果与重叠长度、离散卷积的完整输出、方波部分和与其峰值、
Gibbs 极限 $2\operatorname{Si}(\pi)/\pi$、混叠后的表观频率、矩形脉冲的频谱与第一零点、
主瓣宽度、RC 的截止频率/幅频/相频、一阶离散系统的极点与脉冲响应。

**约定 / 教材常数**
- 方波周期取 1（前半周 +1、后半周 −1），故级数系数是 $4/\pi$。
- $f_0 = 1.2$ 与 $RC = 1$ ms 取成便于读数的值，不是实测值。
- $1/\sqrt2$、$-45^\circ$、$2\operatorname{Si}(\pi)/\pi$ 都是**解析常数**，
  由内核现算并与表达式对账，不是手抄的数。

**假设**（每题的滑块范围与题设值，逐条如下）
- `convolution`：两个宽度 1、高度 1 的矩形；滑块为滑动位置 $t\in[-1.5,1.5]$，题设 0.5。
- `discrete`：$x=[1,2,3,1]$、$h=[1,1,1]$；滑块为输出下标 $n\in[0,5]$，题设 2。
- `fourier`：方波周期 1；滑块为最高谐波 $N\in[1,41]$（奇数），题设 11。
- `sampling`：信号频率 $f_0 = 1.2$；滑块为采样率 $f_s\in[0.6,4.0]$，题设 2.0。
- `spectrum`：矩形脉冲；滑块为脉宽 $\tau\in[0.3,2.5]$，题设 1.0。
- `filter`：$C = 1\ \mu\mathrm{F}$、$R$ 由滑块给定；滑块为时间常数 $RC\in[0.1,10]$ ms，题设 1 ms。
- `discrete_sys`：$y[n]=a\,y[n-1]+x[n]$；滑块为 $a\in[-1.2,1.2]$，题设 0.8。

**未覆盖**：拉普拉斯变换与 s 平面、z 变换的收敛域与部分分式、IIR/FIR 滤波器设计、
DFT/FFT 与窗函数、调制与解调、状态空间与可控可观性、随机信号与功率谱密度。
遇到请直接说明未覆盖。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页，
交互页能说清就别做视频。本技能产出的是**自包含的交互教学网页**，构建与校验都有成本，
不适合「随口问一句」的场景。

- 题目只要求**一个数值答案**（如「求 $y[2]$」）——直接算并作答，不必做页。
- 题目要**拉普拉斯变换、z 变换的收敛域、部分分式展开**——本技能不含，直接说明。
- 题目要**滤波器设计**（Butterworth/Chebyshev、FIR 窗函数法）——请直接说明未覆盖。
- 题目是**通信原理**（调制、信道容量、编码）——超出本技能范围，直接说明。
- 题目属**常微分方程与相平面**（平衡点、稳定性、共振）——用 `edu-ode-dynamics`。
- 题目属**概率与随机过程**（分布、大数定律、中心极限）——用 `edu-probability`。
- 题目属**线性代数**（矩阵分解、特征值）——用 `edu-linear-algebra`。

## 目录结构

```
edu-signals/
├── SKILL.md
├── lib/signal_kernel.py           # 卷积/傅里叶/采样/滤波/离散系统内核（57 条自检）
├── scripts/generate.py            # 注入模板 + 7 个 build_* + 读数对账 + 三目翻译器
└── template/
    ├── board.html                 # 组装产物（勿直接修改）
    └── parts/                     # 模板片段（改这里再 compose）
        ├── scene_functions.html   # 7 个 drawXxx + 真跑的求和 + 折线裁剪
        ├── scene_dispatch.html    # 场景分派
        ├── page_title.html        # 「信号与系统 · 交互学习」
        └── board_label.html       # 画板角标
```
