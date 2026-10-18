---
name: edu-thermochem
description: >-
  把一道热化学题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个可变参数滑块驱动实时重算的量 + 状态灯 + 定值指示器），中栏 KaTeX 分步解析，
  右栏 2D Canvas 画板（能量-反应进程曲线、盖斯定律的分步路径与一步直连、
  标准生成焓的条形叠加、断键吸能/成键放能的对比条、燃烧放热条、
  量热计与温度刻度、催化剂前后的两条能量曲线）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖反应热的符号与
  能量图、盖斯定律、由标准生成焓计算、由键能估算、燃烧热与热量计算、
  中和热与量热法、活化能与催化剂等题型，统一由 Python 内核现算
  （盖斯定律是**真做线性组合**：可以反向、可以乘系数，不是套一个结论）。
  其它 agent 也可调用本技能生成此类网页。形态与 edu-chem-calc / edu-chem-reaction
  平行（复用 seq-phys 模板家族，并新增 energycurve / hesspath / barh / bondbar /
  heatcalc / calorimeter / catalyst 七种场景）。触发词：热化学, 反应热, 焓变,
  热量, 放热, 吸热, 能量图, 活化能, 过渡态, 催化剂, 盖斯定律, 盖斯,
  标准生成焓, 生成焓, 键能, 燃烧热, 中和热, 量热计, 比热容, 热化学方程式,
  反应热的计算, 解这道热化学题, 随机出一道热化学题, 这张图里的热化学题;
  thermochemistry, enthalpy change, heat of reaction, exothermic, endothermic,
  energy diagram, activation energy, catalyst, Hess's law, standard enthalpy of
  formation, bond energy, heat of combustion, heat of neutralization,
  calorimetry, interactive chemistry solution page.
---

# 热化学交互教学网页 (edu-thermochem)

把一道热化学题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
内核现算驱动，2D 能量画板 + KaTeX 分步解析。

## 与相邻技能的边界（先看清再选技能）

| 技能 | 管什么 | 判据 |
| --- | --- | --- |
| `edu-chem-calc` | **化学计量与溶液计算**（浓度、滴定、平衡、Ksp） | 题目要算浓度或物质的量 |
| `edu-chem-reaction` | **反应机理与配平**（微观 3D、电子转移） | 题目要「看分子怎么变」 |
| `edu-organic-chem` | **有机化学**（结构、官能团、聚合） | 题目里是碳骨架 |
| **本技能** | **热化学**：$\Delta H$、能量图、盖斯定律、生成焓/键能、燃烧热、中和热 | 题目里出现 $\Delta H$、kJ/mol、放热吸热 |

**判据**：题目里出现 $\Delta H$ 或「放出/吸收多少热量」——用本技能；
只是算浓度/物质的量——用 `edu-chem-calc`。

## 依赖（重要）

计算核心 `lib/thermochem_kernel.py` **只用标准库**（不需要 sympy）。
运行前确认：`python -c "import math"`（必然成立）。

Windows 控制台打印 ✓ 报 UnicodeEncodeError 时先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-thermochem
python scripts/generate.py list                   # 列出已注册题型
python scripts/generate.py hess ./sol.html        # 盖斯定律
python scripts/generate.py all ./output           # 全部题型
python scripts/generate.py random 7 ./random.html # 随机出题（seed=7）
python lib/thermochem_kernel.py                  # kernel 内置自检（46 条）
```

> 不传输出路径时默认写到**当前工作目录（cwd）**。

| key | 场景 | 主问题 |
| --- | --- | --- |
| `sign` | `energycurve` | $\Delta H$ 与两个活化能是什么关系？放热时谁更大？ |
| `hess` | `hesspath` | 为什么分步算与一步算结果相同？ |
| `formation` | `barh` | 为什么单质的 $\Delta H_f$ 取 0？系数要不要乘进去？ |
| `bond` | `bondbar` | 为什么是「断减成」？新键多强才放热？ |
| `combustion` | `heatcalc` | 燃烧热是正的、$\Delta H$ 是负的，为什么？ |
| `neutralization` | `calorimeter` | 怎么由温升反求中和热？为什么与酸碱种类无关？ |
| `catalyst` | `catalyst` | 催化剂为什么不改变 $\Delta H$？ |

## 工作流程（AI 调用时）

1. **归一题面**：反应式、已知热效应、所求、单位，判断属于哪个题型。
2. **用 kernel 现算**（不要心算）：`delta_h_formation` `delta_h_bonds`
   `hess_combine` `hess_path` `reverse_step` `heat_amount` `moles_for_heat`
   `temperature_rise` `mass_for_rise` `neutralization_dh` `neutralization_moles`
   `activation_effect` `exo_or_endo`。
3. **组装数据**三段 `lesson` / `steps` / `board`；可照抄 `scripts/generate.py` 的 7 个 `build_*`。
   **每个读数表达式都要与内核值对账**（`_agree`）。
4. **自检**：kernel 自检全过（46 条）；答案卡 == 末步展示值 == 画板读数初值；
   起本地静态服务，滑块拨到**每个档位**，确认
   ① 无控制台报错 ② **画布指纹数 = 档位数** ③ 不裁边
   ④ 状态灯在该翻转的参数值上翻转。

## 本技能特有的坑

### 1. 符号是本科目最大的坑，必须每题都标
「燃烧热 $890.3\ \mathrm{kJ/mol}$」是**正值**（放出的热量），
而热化学方程式里要写 $\Delta H = -890.3$。
本技能把两者**分别列成两个读数**（`burn` 与 `dh`），
所有涉及 $\Delta H$ 的地方都在标签里写明「放热为负」。

### 2. 盖斯定律要「真做线性组合」，不要套结论
内核的 `hess_combine(steps)` 接收 `[(系数, ΔH), ...]`，系数可正可负，
`reverse_step` 负责变号。这样「把 (1) 减 (2)」这类操作是真的在做代数运算，
而不是把已知答案写死。页面上因此可以任意拖动中间体高度，
而「分步之和」那一行**永远等于一步的值** —— 这才是定律的演示。

### 3. 催化剂降的是**同一个山顶**
正逆活化能**同步下降相同的量**，所以 $\Delta H = E_{a(正)} - E_{a(逆)}$ 不变。
内核的 `activation_effect` 就是按这个逻辑写的：先降正反应活化能，
再由 $\Delta H$ 反推逆反应活化能，最后**用两者之差回算 $\Delta H$ 做校验**。

### 4. 沿用既有三条（详见 `edu-physics-thermal` 的 SKILL.md）
① 场景字段要是表达式或数组，不能写死某个档位的具体数值；
② 状态灯文案是**纯文本**，不能写 `$…$`；`evalExpr` 只返回数字，
且**不支持 `cond ? a : b` 三元**（Python 侧会语法错）；
③ 一行文字不超过约 28 个汉字（11px）。

## 数值出处分级

### ① 现算（内核算出，**不手写数字**）
反应热与活化能的关系、盖斯定律的线性组合、由生成焓/键能算 $\Delta H$、
热量与温升的互算、中和热的反算、催化剂的效应。

### ② 实测（教材常数表与标准热力学数据）
水的比热容 $c = 4.18\ \mathrm{J/(g\cdot K)}$；
强酸强碱稀溶液的中和热 $-57.3\ \mathrm{kJ/mol}$；
标准生成焓：$\mathrm{CH_4} = -74.8$、$\mathrm{CO_2} = -393.5$、
$\mathrm{H_2O(l)} = -285.8$、$\mathrm{CaCO_3} = -1207.0$、
$\mathrm{CaO} = -635.5$（单位 $\mathrm{kJ/mol}$）；
键能：$\mathrm{H-H} = 436$、$\mathrm{Cl-Cl} = 243$、$\mathrm{N\equiv N} = 946$、
$\mathrm{N-H} = 391$、$\mathrm{H-Cl} \approx 431$（单位 $\mathrm{kJ/mol}$）。

> **明确声明**：这些是**教材常用值**，不同教材/手册的末位可能相差 1~2。
> 所以页面上算出的 $\Delta H$ 与「用最新手册数据重算」可能差一点点 ——
> 这不是错误，但**不要**把本页数字当高精度参考值引用。
> 例如合成氨用键能法估算得 $-92\ \mathrm{kJ/mol}$，与实测 $-92.4$ 一致到两位。

### ③ 约定（示例参数与画板布局）
- `sign`：$E_{a(正)}$ 的下限取 $150\ \mathrm{kJ/mol}$（当 $\Delta H$ 很大时山要更高，
  取 $\max(150,\ \Delta H+40)$）；滑块 $\Delta H\in[-200,200]$，题设 $-100$。
- `hess`：一步的 $\Delta H$ 定为 $-145\ \mathrm{kJ/mol}$；
  滑块为中间体 $C$ 的相对高度 $\in[0.1,0.9]$，题设 0.6。
- `formation`：**五个反应及其标准生成焓是输入数据**（标准热力学数据表）；
  滑块为反应编号 1–5，题设 1。
- `bond`：断键项固定为 $\mathrm{H-H}+\mathrm{Cl-Cl}$；
  滑块为 $E(\mathrm{H-Cl})\in[320,480]$，题设 431。
- `combustion`：$\mathrm{CH_4}$ 的燃烧热取 $890.3\ \mathrm{kJ/mol}$；
  滑块为 $n\in[0.5,5]$ mol，题设 2。
- `neutralization`：溶液质量取 $100\ \mathrm{g}$、比热容按水算；
  滑块为 $n(\mathrm{H_2O})\in[0.01,0.1]$ mol，题设 0.05。
- `catalyst`：$\Delta H = -40$、无催化剂时 $E_{a(正)} = 130\ \mathrm{kJ/mol}$；
  滑块为催化剂降低的活化能 $\in[0,100]$，题设 0。
- 画板的能量刻度（每 100 kJ/mol 对应 1 个世界单位）为**约定的显示参数**。

### 未覆盖
反应速率与速率方程（`edu-chem-calc` 的 `rate`）、化学平衡常数与勒夏特列原理
（`edu-chem-calc` 的 `equilibrium`）、电化学（`edu-chem-calc` 的 `electrolysis`）、
熵变与吉布斯自由能（大学内容）、相变热的计算、燃料热值的数据比较。
遇到请直接说明未覆盖。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页。
本技能产出的是**自包含的交互教学网页**，构建与校验都有成本。

- 只要求**一个数值答案**（如「求 $\Delta H$」）——直接算并作答，不必做页。
- 题目是**溶液浓度 / 滴定 / 平衡常数**——用 `edu-chem-calc`。
- 题目要**看分子怎么断键成键**（微观机理）——用 `edu-chem-reaction`。
- 题目是**有机物的结构、同分异构、聚合**——用 `edu-organic-chem`。

## 目录结构

```
edu-thermochem/
├── SKILL.md
├── lib/thermochem_kernel.py     # 内核（7 组函数 + 46 条自检，仅用标准库）
├── scripts/generate.py          # 注入模板 + 7 个 build_* + 读数对账
└── template/
    ├── board.html               # 组装产物（勿直接修改）
    └── parts/                   # 模板片段（改这里再 compose）
        ├── scene_functions.html # 7 个 drawXxx + energyCurve/levelLine/diffArrow
        ├── scene_dispatch.html
        ├── page_title.html
        └── board_label.html
```

## 扩展

- **加题型**：在 `thermochem_kernel.py` 加计算函数（+ `__main__` 自检），
  在 `generate.py` 加 `build_*`（含 `_agree` 对账）并注册进 `REGISTRY`。
- **加热力学数据**：往 `FH_REACTIONS` 里加一条（反应式 + 反应物/生成物的
  `(系数, ΔHf)` 列表）即可，条形图与读数会自动跟上。
- **加场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `scene_dispatch.html` 加 case，然后 `python ../../tools/compose_templates.py`
  重新组装 `template/board.html`。**不要直接改 `board.html`**。
