---
name: edu-physics-thermal
description: >-
  把一道高中物理「热学 / 近代物理」题解成一个自包含的交互教学网页：左栏题面 +
  动态控制台（一个可变参数滑块驱动实时重算的物理量 + 状态灯 + 定值指示器），
  中栏 KaTeX 分步解析，右栏 2D Canvas 物理画板（p-V 等温线、麦克斯韦速率分布、
  能量条、矩形循环、光电效应图线、氢原子能级图、衰变曲线）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖理想气体状态方程与
  等温过程、分子动理论与三种特征速率、热力学第一定律、循环过程与热机效率、
  光电效应方程与截止频率、氢原子能级与巴耳末系、放射性衰变与半衰期等题型，
  统一由 Python 内核现算（常数集中声明；答案、分步数值、画板读数同源一致）。
  其它 agent 也可调用本技能生成此类网页。形态与 edu-physics-em 平行（复用 seq-phys
  模板家族，并新增 gaspv / molecules / energybar / pvcycle / photo / levels / decay
  七种场景）。触发词：热学, 分子动理论, 理想气体, 状态方程, 玻意耳定律, 等温,
  等压, 等容, p-V 图, 麦克斯韦速率分布, 方均根速率, 最概然速率, 平均速率,
  热力学第一定律, 内能, 绝热, 做功, 热机, 热机效率, 卡诺循环, 循环过程,
  近代物理, 光电效应, 光电效应方程, 逸出功, 截止频率, 遏止电压, 光子,
  氢原子, 能级, 跃迁, 巴耳末系, 莱曼系, 光谱, 电离能, 放射性, 衰变, 半衰期,
  碳14测年, 解这道热学题, 解这道近代物理题, 随机出一道热学题, 这张图里的物理题;
  thermal physics, kinetic theory, ideal gas law, isothermal process, p-V diagram,
  Maxwell speed distribution, root-mean-square speed, first law of thermodynamics,
  heat engine efficiency, Carnot, photoelectric effect, work function, threshold
  frequency, stopping voltage, hydrogen energy levels, Balmer series, radioactive
  decay, half-life, interactive physics solution page.
---

# 热学与近代物理交互教学网页 (edu-physics-thermal)

把一道「热学 / 近代物理」题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
内核现算驱动，2D 物理画板 + KaTeX 分步解析。

## 与相邻技能的边界（先看清再选技能）

| 技能 | 管什么 | 判据 |
| --- | --- | --- |
| `edu-physics-senior` | **必修一力学**（传送带、追及、斜面、平抛、圆周、v-t） | 题目里有运动过程与牛顿定律 |
| `edu-physics-junior` | **初中物理**（杠杆、压强、浮力、滑轮、电路） | 初中内容 |
| `edu-physics-em` | **高中电磁学**（电场、电路、磁场、洛伦兹力） | 题目里有电荷、电流、磁场 |
| **本技能** | **选择性必修三**：热学（分子动理论 / 气体 / 热力学定律）+ 近代物理（光电效应 / 原子能级 / 核衰变） | 题目里有 $p,V,T$、热量、光子、能级、半衰期 |
| `edu-chem-calc` | 化学计量与溶液计算 | 题目按化学方程式、物质的量走 |

**光学与机械波尚未覆盖**（选择性必修一），遇到请直接说明未覆盖，不要硬套本技能。

## 依赖（重要）

计算核心 `lib/thermal_kernel.py` 依赖 **sympy**。运行前确认：`python -c "import sympy"`。
**缺库时**先询问用户是否安装（`python -m pip install sympy`）或换解释器，**不要未经询问直接装**。
Windows 控制台打印 ✓ 报 UnicodeEncodeError 时先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-physics-thermal
python scripts/generate.py list                        # 列出已注册题型
python scripts/generate.py photoelectric ./sol.html    # 光电效应
python scripts/generate.py all ./output                # 全部题型
python scripts/generate.py random 7 ./random.html      # 随机出题（seed=7）
python lib/thermal_kernel.py                          # kernel 内置自检（39 条）
```

> 不传输出路径时默认写到**当前工作目录（cwd）**。

| key | 场景 | 主问题 |
| --- | --- | --- |
| `gas_law` | `gaspv` | 等温线为什么是双曲线？$pV$ 为什么不变？ |
| `kinetic` | `molecules` | 升温后分布曲线怎么变？三个特征速率的比值为什么恒定？ |
| `first_law` | `energybar` | $\Delta U = Q + W$ 的符号约定；等温 / 绝热各是什么样？ |
| `cycle` | `pvcycle` | 哪两段吸热？净功为什么等于面积？效率为什么 <1？ |
| `photoelectric` | `photo` | 斜率与截距是什么？为什么光强不改变 $E_k$？ |
| `levels` | `levels` | 能级为什么是负的？为什么 $n$ 越大波长越短？ |
| `decay` | `decay` | 「剩一半」是对谁说的？半衰期与外界条件有关吗？ |

## 工作流程（AI 调用时）

1. **归一题面**：已知量、所求、单位、语言，判断属于哪个题型。
2. **用 kernel 现算**（不要心算）：`thermal_kernel.py` 提供
   - 气体：`isothermal` `isobaric` `isochoric` `pv_over_t` `gas_moles`
   - 分子动理论：`avg_ke` `rms_speed` `pressure_kinetic`
   - 热一律：`first_law` `heat_engine_eff` `carnot_eff`
   - 光电：`photon_energy` `ek_max` `threshold_freq` `stopping_voltage` `photon_wavelength`
   - 能级：`energy_level` `transition_energy` `level_wavelength`
   - 衰变：`remaining` `half_lives` `decayed_fraction`
3. **组装数据**三段 `lesson` / `steps` / `board`；可照抄 `scripts/generate.py` 的 7 个 `build_*`。
   **每个读数表达式都要与内核值对账**：`_agree(label, expr, want)` 在构建期用等价的 Python
   实现求值一次再比对（两边都从同一个常数出发，才不会「页面上写 658 nm、内核算出 656 nm」）。
4. **自检**：kernel 自检全过（39 条）；答案卡 == 末步展示值 == 画板读数初值，四者一致；
   起本地静态服务，把滑块拨到**至少 5 个档位（含两端）**，确认
   ① 无控制台报错 ② 每一档**画布都真的变了**（见下面第 1 条陷阱）
   ③ 每一档都不裁边 ④ 状态灯在该翻转的参数值上翻转。

## 三条必须遵守的坑（都踩过）

### 1. 场景字段要引用**标量**，不是原始参数（最隐蔽）
模板把 `BOARD.scalars` 顺序算进 `env`，再用它解析 `scene` 的每个字段。
若场景字段写成 `"nu": "nu14"`（指向**滑块原始值**），而滑块是以 $10^{14}$ Hz 计的，
画布拿到的频率就是 `10` 而不是 `1e15` —— **游标钉在原点不动，
但读数一切正常、控制台一条错误都没有**。

> 正确写法：`"scene": {"kind": "photo", "nu": "nu"}`，
> 让 `scalars: [{"name":"nu","expr":"nu14*1e14"}]` 先把单位还原成 SI，场景再引用 `nu`。
>
> **怎么发现**：验证时不能只看读数，必须**逐档比较画布指纹**（`getImageData` 的哈希）。
> 哈希不变 = 画布没跟着动。这是本轮唯一一个「静默」的 bug。

### 2. 状态灯的文案是**纯文本**，不要写 `$…$`
`updateReadouts` 用 `textContent` 写状态灯，KaTeX 不会渲染。
写 `"$E_k > 0$"` 会原样显示成一串美元符号。用纯文本 `"E_k > 0"`。

顺带：`evalExpr` **只返回数字**（布尔表达式会变成 `NaN`），
所以状态灯的比较必须写在 `expr` + `op` + `rhs` 上，**不能**在 `expr` 里写 `<`、`and`。
外壳的判据是 `v < rhs-1e-9` / `v > rhs+1e-9` / `|v-rhs|<1e-6` ——
**rhs 留足容差**（例如「是否为整数个半衰期」用 `rhs=0.05`，给 `1e-9` 会因为减掉 1e-9 而判假）。

### 3. 一行文字不得超过约 28 个汉字
10 世界单位的视窗、11px 字号下，一行最多约 28 个汉字。
超了会把画布撑破（`labelIn` 的兜底只能把它左对齐，仍然溢出右边界）。
本模板的 `labelIn` 已加**自动缩字号**（下限 7px）作为安全网，
但正确做法是**把长句拆成两行或缩短**。经验值：11px ≤ 24 字，10px ≤ 30 字，ASCII 按半个汉字算。

## 单位契约

滑块**不一定要用 SI**，但换算必须显式写在 `scalars` 里，且**页面读数用缩放单位显示**：

| 题型 | 滑块单位 | `scalars` 还原 | 显示单位 |
| --- | --- | --- | --- |
| `gas_law` | L（体积） | 直接用（kPa·L = J） | kPa·L |
| `photoelectric` | ×10¹⁴ Hz | `nu = nu14*1e14` | ×10¹⁴ Hz / eV |
| `decay` | 年 | 直接用 | 年 |

## 数值出处分级

### ① 现算（内核算出，**不手写数字**）
等温 / 等压 / 等容过程的状态量、$pV/T$ 不变量、物质的量；平均动能、方均根速率、
压强微观式；$\Delta U = Q + W$、热机效率、卡诺效率；光子能量、最大初动能、截止频率、
遏止电压、光子波长；氢原子能级、跃迁能量、谱线波长；剩余比例、已衰变比例、半衰期数。

### ② 实测（物理常数，取自教材常数表）
$R = 8.31\ \mathrm{J/(mol\cdot K)}$、$k = 1.38\times10^{-23}$、
$h = 6.63\times10^{-34}$、$c = 3.00\times10^8$、$e = 1.60\times10^{-19}$、
$N_A = 6.02\times10^{23}$、氢基态 $E_1 = -13.6\ \mathrm{eV}$。

> **明确声明**：这些是**教材三位有效数字**的值，不是 CODATA 全精度值。
> 所以页面上的数值与「用 CODATA 常数重算」在末位可能差 1~2——
> 这不是错误，但**不要**把本页数字当高精度参考值引用。
> 由它们派生的 $hc = 1243.1\ \mathrm{eV\cdot nm}$ 同理。

### ③ 约定（示例参数，不是实测值）
- `gas_law`：$n = 1$ mol、$T = 300$ K 固定；滑块 $V\in[5,50]$ L，题设 10 L。
- `kinetic`：氧气 $M = 0.032$ kg/mol；滑块 $T\in[200,1200]$ K，题设 300 K。
- `first_law`：$W = 80$ J 固定（约定为**外界对气体做功**）；滑块 $Q\in[-200,200]$ J，题设 60 J。
- `cycle`：$V_1 = 2$ L、$V_2 = 8$ L、$p_1 = 200$ kPa 固定，
  **单原子气体**（$C_V = \tfrac32 R$）；滑块 $p_2\in[40,160]$ kPa，题设 100 kPa。
  → **气体种类会影响效率**：换成双原子分子 $C_V = \tfrac52 R$ 结果不同，页面上必须写明取的是单原子。
- `photoelectric`：逸出功 $W_0 = 4.0\times10^{-19}$ J（= 2.5 eV）；
  滑块 $\nu\in[4,14]\times10^{14}$ Hz，题设 $10\times10^{14}$ Hz。
- `levels`：跃迁到 $n = 2$（巴耳末系）；滑块 $n\in[3,6]$，题设 3。
- `decay`：$T = 5$ 年、$N_0 = 1000$；滑块 $t\in[0,30]$ 年，题设 5 年。

### 未覆盖
光学（折射、全反射、干涉衍射）与机械波、交变电流、动量守恒、原子核反应方程
（质量亏损与结合能）。遇到请直接说明未覆盖。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页，
交互页能说清就别做视频。本技能产出**自包含的交互教学网页**，构建与校验都有成本。

- 只要求**一个数值答案**（如「求剩多少个核」）——直接算并作答，不必做页。
- 题目是**力学**——用 `edu-physics-senior` / `edu-physics-junior`。
- 题目是**电磁学**——用 `edu-physics-em`。
- 题目是**光学 / 机械波**——目前没有技能覆盖，请直接说明。
- 题目是**化学**（化学方程式配平、溶液浓度）——用 `edu-chem-calc`。
- 题目涉及**恒定电流的电路计算**——用 `edu-physics-em`（那边有电路场景）。

## 目录结构

```
edu-physics-thermal/
├── SKILL.md
├── lib/thermal_kernel.py        # 内核（常数集中声明 + 7 组函数 + 39 条自检）
├── scripts/generate.py          # 注入模板 + 7 个 build_* + 读数对账
└── template/
    ├── board.html               # 组装产物（勿直接修改）
    └── parts/                   # 模板片段（改这里再 compose）
        ├── scene_functions.html # 7 个 drawXxx + labelIn + 绘图框助手
        ├── scene_dispatch.html  # 场景分派
        ├── page_title.html
        └── board_label.html
```

## 扩展

- **加题型**：在 `thermal_kernel.py` 加计算函数（+ `__main__` 自检），
  在 `generate.py` 加 `build_*`（含 `_agree` 对账）并注册进 `REGISTRY`。
- **加场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `scene_dispatch.html` 加 case，然后 `python ../../tools/compose_templates.py`
  重新组装 `template/board.html`。**不要直接改 `board.html`**。
