---
name: edu-quantum
description: >-
  把一道量子力学（一维）题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个可变参数滑块驱动实时重算的量 + 状态灯 + 定值指示器），中栏 KaTeX 分步解析，
  右栏 2D Canvas 画板（势阱 + 能级 + 波函数与概率密度、λ–E 曲线、
  高斯波包与 Δp=ħ/(2Δx) 双曲线、抛物势 + 等间距能级、
  势垒与 T(E) 曲线、有限深势阱 + 渗出阱外的波函数、随时间展宽的波包）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖无限深势阱、
  德布罗意波长、不确定性原理、一维谐振子与零点能、隧道效应、有限深势阱、波包色散
  等题型。能级与透射系数用解析式，**有限深势阱的束缚态用二分法真解超越方程**
  （不是查表），并与解析上界 ⌈√(2mV₀)a/πħ⌉ 交叉核对。
  其它 agent 也可调用本技能生成此类网页。形态与 edu-physics-thermal 平行（复用 seq-phys
  模板家族，并新增 wellplot / debroglie / uncert / harmonic / tunnel / finitewell /
  wavepacket 七种场景）。触发词：量子力学, 量子, 波函数, 概率密度, 薛定谔方程,
  定态, 无限深势阱, 势阱, 能级, 量子化, 基态, 激发态, 节点, 德布罗意, 德布罗意波长,
  物质波, 不确定性原理, 测不准关系, 零点能, 谐振子, 谐振子能级, 隧道效应,
  隧穿, 透射系数, 势垒, 扫描隧道显微镜, 有限深势阱, 束缚态, 超越方程,
  波包, 色散, 群速度, 量子点, 解这道量子力学题, 随机出一道量子力学题,
  这张图里的量子力学题; quantum mechanics, wave function, probability density,
  Schrödinger equation, infinite square well, energy levels, quantization,
  de Broglie wavelength, matter wave, uncertainty principle, zero-point energy,
  harmonic oscillator, quantum tunneling, transmission coefficient, potential
  barrier, finite square well, bound states, wave packet, dispersion, group velocity,
  interactive quantum mechanics solution page.
---

# 量子力学入门交互教学网页 (edu-quantum)

把一道一维量子力学题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
精确内核驱动，2D 画板 + KaTeX 分步解析。

## 与相邻技能的边界（先看清再选技能）

| 技能 | 管什么 | 判据 |
| --- | --- | --- |
| `edu-physics-thermal` | **高中近代物理**：光电效应、氢原子能级、半衰期 | 题目是高中选择性必修三的内容 |
| `edu-multivariable-calc` | 多元微积分（含偏微分方程的一般方法） | 题目要算积分/偏导 |
| `edu-ode-dynamics` | 常微分方程与动力系统 | 题目是经典动力学 |
| **本技能** | **一维量子力学**：波函数、能级量子化、隧道、波包 | 题目里有 $\psi$、$\hbar$、能级、透射系数 |

**判据**：题目里出现 $\psi$、$\hbar$、$|\psi|^2$、能级量子化 —— 用本技能；
出现「光子能量 / 逸出功 / 半衰期」—— 用 `edu-physics-thermal`（那边是高中口径）。

## 依赖（重要）

计算核心 `lib/quantum_kernel.py` **只用标准库**（`math`；不需要 sympy / scipy）。
运行前确认：`python -c "import math"`（必然成立）。

**注意**：`finite_well` 题型的构建期会对每个阱深做一次 4000 点的符号扫描 + 二分求根
（共 21 个阱深），实测整个技能生成约 1 秒，属正常。

Windows 控制台打印 ✓ 报 UnicodeEncodeError 时先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-quantum
python scripts/generate.py list                    # 列出已注册题型
python scripts/generate.py well ./sol.html         # 无限深势阱
python scripts/generate.py all ./output            # 全部题型
python scripts/generate.py random 7 ./random.html  # 随机出题（seed=7）
python lib/quantum_kernel.py                      # kernel 内置自检（62 条）
```

> 不传输出路径时默认写到**当前工作目录（cwd）**。

| key | 场景 | 主问题 |
| --- | --- | --- |
| `well` | `wellplot` | 能级为什么按 $n^2$ 增长？节点数与 $n$ 什么关系？ |
| `debroglie` | `debroglie` | $\lambda$ 与 $E$ 什么关系？为什么宏观看不到波动性？ |
| `uncertainty` | `uncert` | 为什么「不确定」不是仪器问题？为什么下界是 $\hbar/2$？ |
| `harmonic` | `harmonic` | 为什么能级等间距？为什么 $n=0$ 也不是 0？ |
| `tunneling` | `tunnel` | $E<V_0$ 为什么还能穿过去？$E>V_0$ 时 $T$ 是 1 吗？ |
| `finite_well` | `finitewell` | 为什么要解超越方程？为什么基态比无限阱低？ |
| `wavepacket` | `wavepacket` | 自由波包为什么会自己散开？ |

## 工作流程（AI 调用时）

1. **归一题面**：势的形式、所求（能级/波长/透射/展宽）、单位，判断属于哪个题型。
2. **用 kernel 现算**（不要心算）：`well_energy` `well_energy_ev` `well_psi` `well_prob`
   `de_broglie` `de_broglie_ev` `uncertainty_min_dp` `gauss_sigma_p`
   `harmonic_energy` `harmonic_zero_point` `harmonic_spacing`
   `tunneling_T` `tunneling_kappa` `finite_well_levels` `finite_well_count`
   `gauss_packet_sigma` `gauss_packet_prob` `gauss_packet_speed`
   以及单位换算 `j_to_ev` `ev_to_j` `m_to_nm` `nm_to_m`。
3. **组装数据**三段 `lesson` / `steps` / `board`；可照抄 `scripts/generate.py` 的 7 个 `build_*`。
   **每个读数表达式都要与内核值对账**（`_agree`）。
4. **自检**：kernel 自检全过（62 条）；答案卡 == 末步展示值 == 画板读数初值；
   起本地静态服务，滑块走过**每个档位**，确认
   ① 无控制台报错 ② **画布指纹数 = 档位数** ③ 不裁边
   ④ 状态灯在该翻转的参数值上翻转 ⑤ **没有读数显示成「—」**。

## 本技能特有的坑

### 1. 打靶法必须在**连续形式**下扫符号
有限深势阱的偶态方程是 $k\tan(ka/2)=\kappa$。直接对 $f=k\tan(ka/2)-\kappa$
扫符号找变号 —— **会多出假根**，因为 $\tan$ 在 $ka/2=\pi/2$ 处有极点，
函数从 $+\infty$ 跳到 $-\infty$，被误判成「变号」。
> 正确做法：两边乘掉分母，改成 $g=k\sin(ka/2)-\kappa\cos(ka/2)$ ——
> 连续，极点处 $g=\pm k\neq 0$，不再产生假根。
> **怎么发现**：把数值解出的个数与解析上界 $\lceil\sqrt{2mV_0}\,a/\pi\hbar\rceil$ 对拍，
> 假根会让个数偏多。本轮就是这么抓到的（修之前个数对不上）。

### 2. 场景的「档位索引」字段必须由**真实参数名**推出
本技能的 `tunneling`/`finite_well` 场景需要按档位索引数组，而滑块参数名是
`eratio`/`depth`（不是 `ei`/`di`）。第一版把场景字段写成 `"ei": "ei"` ——
`evalExpr("ei", env)` 得到 `undefined`，于是 `TArr[NaN]` 是 `undefined`，
画板抛 `Cannot read properties of undefined`，**全部读数变成「—」**。
> 正确做法：把索引写成表达式 `floor((eratio-0.1)/0.05+0.5)+1`（**MATHENV 里没有 `round`**，
> 要用 `floor(x+0.5)`），读数与场景共用同一个表达式。

### 3. 极小值不要直接 `toFixed`
$\Delta x\sim10^{-10}$ m、$\Delta p\sim10^{-25}$、$\hbar/2\sim10^{-35}$ ——
用 `digits=6` 会全部显示成 `0.000000`。
> 正确做法：**换算到量纲化单位再显示**（nm、×10⁻²⁵、×10⁻³⁴），
> 并且把换算本身也纳入 `_agree` 对账。

### 4. 数组字面量的舍入位数要与对账容差匹配
把数组写成 `[...][idx-1]` 供页面取用时，默认保留 6 位小数。
此时 `_agree` 的容差**不能再用 1e-9**（会因为舍入误报），要用 1e-6。
**这条在 `edu-stat-inference` 上已经踩过一次，本轮又踩** —— 已写进 SKILL.md 两处。

### 5. 沿用既有三条（详见 `edu-physics-thermal` 的 SKILL.md）
① 场景字段要是表达式或数组，不能写死某个档位的具体数值；
② 状态灯文案是**纯文本**，不能写 `$…$`；`evalExpr` 只返回数字；
③ 一行文字不超过约 28 个汉字（11px）。

## 数值出处分级

### ① 现算（**解析式或真解方程**，不手写数字）
无限深势阱能级与波函数、德布罗意波长、不确定关系下界、谐振子能级与零点能、
矩形势垒的透射系数、**有限深势阱的束缚态能量（二分法真解超越方程）**、
自由高斯波包的宽度演化与群速度。
解析解与数值解**互相印证**（如有限阱个数与解析上界对拍、波包面积守恒）。

### ② 实测（CODATA 常数）
$h = 6.62607015\times10^{-34}$ J·s、$\hbar = 1.054571817\times10^{-34}$ J·s、
$m_e = 9.1093837015\times10^{-31}$ kg、$e = 1.602176634\times10^{-19}$ C。

> **明确声明**：这几个常数取的是 CODATA 2018 定义值/推荐值（$h$、$e$ 是定义值，
> 精确无误差；$\hbar$ 与 $m_e$ 有末位不确定度）。所以本页算出的能级、波长
> 与「用最新 CODATA 重算」可能在**末位**差一点，这不是错误，
> 但**不要**把本页数字当高精度参考值引用。

### ③ 约定（示例参数与画板布局）
- `well`：阱宽 $L = 0.5$ nm、电子质量；滑块 $n\in[1,6]$，题设 1。
- `debroglie`：电子；滑块 $E\in[1,100]$ eV，题设 10 eV。
- `uncertainty`：高斯波包；滑块 $\sigma\in[0.1,2.0]$ nm，题设 1.0 nm。
- `harmonic`：滑块 $\omega\in[0.5,3.0]\times10^{15}$ rad/s，题设 $10^{15}$。
- `tunneling`：势垒 $V_0 = 5$ eV、宽 $a = 1$ nm；滑块 $E/V_0\in[0.1,2.0]$，题设 0.5。
- `finite_well`：阱宽 $a = 1$ nm；滑块 $V_0\in[2,12]$ eV，题设 5 eV。
- `wavepacket`：$\sigma_0 = 1$ nm、$k_0 = 10^8$ m⁻¹；滑块为时间档位
  $t\in[0,\ 0.1\ \mathrm{ps}]$（26 档），题设 $t=0$。
- 画板的坐标范围、能量刻度与采样点数均为**约定的显示参数**。

### 未覆盖
三维问题（氢原子的角向部分、球谐函数）、角动量与自旋、
多粒子系统与全同粒子、微扰论与变分法、含时薛定谔方程的**一般**数值解
（本页只给了自由高斯波包这一有解析解的特例）、相对论量子力学、
量子信息与量子计算、路径积分。遇到请直接说明未覆盖。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页。
本技能产出的是**自包含的交互教学网页**，构建与校验都有成本。

- 只要求**一个数值答案**（如「求 $E_1$」）——直接算并作答，不必做页。
- 题目是**高中近代物理**（光电效应、氢原子能级、半衰期）——用 `edu-physics-thermal`。
- 题目是**经典力学**（牛顿定律、动量、圆周）——用 `edu-physics-senior` / `edu-physics-momentum`。
- 题目是**多元微积分的方法**（拉格朗日乘数、格林公式）——用 `edu-multivariable-calc`。
- 题目是**统计推断**（置信区间、p 值）——用 `edu-stat-inference`。

## 目录结构

```
edu-quantum/
├── SKILL.md
├── lib/quantum_kernel.py        # 内核（8 组函数 + 62 条自检，仅用标准库）
├── scripts/generate.py          # 注入模板 + 7 个 build_* + 读数对账
└── template/
    ├── board.html               # 组装产物（勿直接修改）
    └── parts/                   # 模板片段（改这里再 compose）
        ├── scene_functions.html # 7 个 drawXxx + axesBox 等助手
        ├── scene_dispatch.html
        ├── page_title.html
        └── board_label.html
```

## 扩展

- **加题型**：在 `quantum_kernel.py` 加计算函数（+ `__main__` 自检），
  在 `generate.py` 加 `build_*`（含 `_agree` 对账）并注册进 `REGISTRY`。
- **加场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `scene_dispatch.html` 加 case，然后 `python ../../tools/compose_templates.py`
  重新组装 `template/board.html`。**不要直接改 `board.html`**；
  新技能还要记得把名字加进 `compose_templates.py` 的 `FAMILIES` 用户列表。
