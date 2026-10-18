---
name: edu-organic-chem
description: >-
  把一道有机化学题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个可变参数滑块驱动实时重算的量 + 状态灯 + 定值指示器），中栏 KaTeX 分步解析，
  右栏 2D Canvas 画板（Ω 标尺、燃烧条形图、两个吸收管、碳骨架 + 等效氢着色、
  官能团消耗量条形、聚合链、主链高亮 + 编号）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖不饱和度、燃烧耗氧量、
  由燃烧产物确定分子式、等效氢与一氯代物、官能团定量反应、加聚缩聚与聚合度、
  主链选择与编号等题型，统一由 Python 内核现算（**等效氢用碳骨架的自同构群轨道算，
  主链用路径枚举算 —— 都不查表**）。
  其它 agent 也可调用本技能生成此类网页。形态与 edu-chem-calc 平行（复用 seq-phys
  模板家族，并新增 unsat / burn / formula / skeleton_h / funcgroup / polymer /
  skeleton_chain 七种场景）。触发词：有机化学, 有机物, 烃, 烷烃, 烯烃, 炔烃, 苯,
  同系物, 同分异构体, 同分异构, 等效氢, 一氯代物, 二氯代物, 取代反应, 加成反应,
  加聚, 缩聚, 聚合度, 单体, 链节, 高分子, 不饱和度, 分子式, 实验式, 最简式,
  燃烧, 耗氧量, 官能团, 羟基, 羧基, 醛基, 酚羟基, 酯基, 银镜反应, 溴水,
  活泼氢, 系统命名, 主链, 取代基, 位号, 官能团异构, 解这道有机题,
  随机出一道有机化学题, 这张图里的有机化学题;
  organic chemistry, alkane, alkene, alkyne, benzene, isomer, equivalent hydrogens,
  monochloro derivative, degree of unsaturation, empirical formula, combustion,
  oxygen demand, functional group, hydroxyl, carboxyl, aldehyde, phenol, ester,
  silver mirror test, addition polymerisation, condensation polymerisation,
  degree of polymerisation, IUPAC naming, parent chain, substituent, locant,
  interactive organic chemistry solution page.
---

# 有机化学基础交互教学网页 (edu-organic-chem)

把一道有机化学题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
内核现算驱动，2D 画板 + KaTeX 分步解析。

## 与相邻技能的边界（先看清再选技能）

| 技能 | 管什么 | 判据 |
| --- | --- | --- |
| `edu-chem-reaction` | **无机反应 / 反应机理**（微观 3D、配平、电子转移） | 题目要「看分子怎么变」 |
| `edu-chem-calc` | **化学计量与溶液计算**（浓度、稀释、pH） | 题目要算物质的量浓度 |
| **本技能** | **有机化学**：结构、同分异构、官能团、聚合、命名 | 题目里是碳骨架 / 官能团 / 同分异构 |

**判据**：题目里出现「**碳骨架 / 官能团 / 同分异构 / 聚合**」——用本技能；
出现「**分子式 → 反应现象**」且要微观演示——用 `edu-chem-reaction`；
纯溶液浓度计算——用 `edu-chem-calc`。

## 依赖（重要）

计算核心 `lib/organic_kernel.py` **只用标准库**（不需要 sympy），
但 `scripts/generate.py` 仍按项目约定 `import sympy` 之外无额外依赖 —— 实际只用 `math` / `itertools`。
运行前确认：`python -c "import math"`（必然成立）。

**注意**：等效氢的计算会对碳骨架的**自同构群**做枚举，碳数越多越慢。
本技能内置的烷烃库最大 6 个碳（候选置换 ≤ 几百个），毫秒级完成；
若要扩到 8 个碳仍可行，**9 个以上请先测一下耗时**。

Windows 控制台打印 ✓ 报 UnicodeEncodeError 时先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-organic-chem
python scripts/generate.py list                     # 列出已注册题型
python scripts/generate.py equiv_h ./sol.html       # 等效氢与一氯代物
python scripts/generate.py all ./output             # 全部题型
python scripts/generate.py random 7 ./random.html   # 随机出题（seed=7）
python lib/organic_kernel.py                       # kernel 内置自检（85 条）
```

> 不传输出路径时默认写到**当前工作目录（cwd）**。

| key | 场景 | 主问题 |
| --- | --- | --- |
| `unsaturation` | `unsat` | Ω 为什么等于「双键或环」的个数？半整数说明什么？ |
| `combustion` | `burn` | 分子自带的氧为什么能「抵账」？ |
| `formula` | `formula` | 氧为什么要用差减法？实验式相同就不是同一种物质吗？ |
| `equiv_h` | `skeleton_h` | 等效氢怎么数？为什么它等于一氯代物的种数？ |
| `functional` | `funcgroup` | 醇羟基与酚羟基为什么对 NaOH 表现不同？ |
| `polymer` | `polymer` | 加聚与缩聚的聚合度公式为什么不一样？ |
| `mainchain` | `skeleton_chain` | 新戊烷的主链为什么不是 4 个碳？ |

## 工作流程（AI 调用时）

1. **归一题面**：分子式 / 结构 / 所求 / 单位，判断属于哪个题型。
2. **用 kernel 现算**（不要查表）：
   - 分子式：`molar_mass` `unsaturation` `unsat_hint`
   - 燃烧：`oxygen_demand` `combustion_products` `oxygen_mass`
   - 反推：`empirical_from_masses` `formula_multiplier`
   - 碳骨架：`h_on_carbon` `automorphisms` `equivalent_hydrogens` `tree_layout`
   - 官能团：`h2_from_sodium` `naoh_consumed` `ag_from_aldehyde` `br2_addition` `h2_addition`
   - 聚合：`addition_degree` `condensation_degree`
   - 命名：`all_paths` `main_chain`
3. **组装数据**三段 `lesson` / `steps` / `board`；可照抄 `scripts/generate.py` 的 7 个 `build_*`。
4. **自检**：kernel 自检全过（85 条）；答案卡 == 末步展示值 == 画板读数初值；
   起本地静态服务，滑块拨到**每个档位**，确认
   ① 无控制台报错 ② **每一档画布都真的变了**（指纹哈希） ③ 不裁边
   ④ 状态灯在该翻转的参数值上翻转。

## 本技能特有的坑（都踩过）

### 1. 「多档位切换」的场景数据不能用固定值（本轮最隐蔽的 bug）
`equiv_h` / `functional` / `mainchain` 三个场景要「换一个分子换一套数据」。
第一版把场景字段写成了**第 1 号分子的具体数值**，结果：
读数区跟着滑块变（因为读数表达式里带了 `mol`），
**但画布始终是第 1 号分子** —— 而且不报错、不裁边、KaTeX 也正常。

> 正确做法：把**整份数组**放进场景（`nodesAll` / `h2All` / `chainAll` …），
> 场景函数里用 `pickIdx(...)` 按滑块索引取当前那一份。
> **验证手法**：逐档比较画布指纹，并要求 **hashUniq 等于不同档位的个数**
> （只要求「≥2」是不够的，本轮的 bug 恰好能让相邻档位同图）。

### 2. 等效氢**必须**把「同一碳上的氢」也算作等价
这是最容易漏的一步。自同构群只给出**碳之间**的置换；
如果只按碳的轨道分组，一个甲基上的 3 个氢会被算成 3 种，
正戊烷会得出 7 种而不是 3 种。
> 正确做法：先在**碳**上做自同构轨道，再把同一个碳上的所有氢合并为一组。

### 3. 没有氢的碳要单独处理
新戊烷的中心碳有 4 个碳邻居、**0 个氢**。把它塞进调色板会取到
`PALETTE[-1]`（JS 里是 `undefined`），颜色会莫名沿用上一个值。
用 `-1` 标记并单独画成中性灰。

### 4. 沿用既有四条（详见 `edu-physics-thermal` 的 SKILL.md）
① 场景字段要引用标量或数组而非固定值；
② 状态灯文案是**纯文本**，不能写 `$…$`；`evalExpr` 只返回数字（布尔会变 NaN），
比较必须写在 `expr`/`op`/`rhs` 上；
③ 一行文字不超过约 28 个汉字（11px）；
④ 长直线/长条形要限制长度，避免裁边（本技能的条形图按 `maxv` 归一）。

## 数值出处分级

### ① 现算（内核现算，**不查表**）
相对分子质量、不饱和度、耗氧量与产物、由产物反推实验式与分子式、
**等效氢的种数（碳骨架自同构群轨道）**、官能团反应的消耗量、
聚合度、**主链与位号（路径枚举）**、碳骨架的 2D 布局。

> 特别说明：**没有任何「同分异构体数目表」**。等效氢种数与主链都是算法现场算的，
> 所以它天然等于一氯代物种数（因为一氯代物种数 = 氢位置的轨道数）。
> 本技能**不做**「烷烃 CₙH₂ₙ₊₂ 有几种同分异构体」的整体枚举（那是另一个算法，
> 且需要处理自由树计数），遇到请直接说明未覆盖。

### ② 实测（原子量，取自教材常数表）
$C = 12$、$H = 1$、$O = 16$、$N = 14$、$Cl = 35.5$、$Br = 80$（HCl 相对分子质量按 36.5 计）。

### ③ 约定（示例参数与输入数据）
- `unsaturation`：只含 C、H，$C$ 固定为 6；滑块 $H\in[6,14]$，题设 6（苯）。
- `combustion`：$C = 2$、$H = 6$ 固定；滑块 $z\in\{0,1,2\}$，题设 0（乙烷）。
- `formula`：样品 3.0 g、两管增重 1.8 g 与 4.4 g（**这三组数就是题设输入**，
  由此推出实验式 CH₂O）；滑块 $M_r\in\{30,60,\dots,180\}$，题设 180（葡萄糖）。
- `equiv_h` / `mainchain`：**六个烷烃的碳骨架是输入数据**（分子结构本身，不是结果）；
  滑块为分子编号 1–6。
- `functional`：**六个分子及其官能团个数是输入数据**；消耗量全部由内核算出。
- `polymer`：加聚单体取乙烯（$M_r = 28$）、缩聚单体取 6-氨基己酸（$M_r = 113$，脱去 18）；
  滑块 $M_r(\text{高分子})\in[2800,28000]$，题设 14000。

### 未覆盖
烷烃同分异构体**总数**的枚举、含取代基超过 2 个碳的完整系统命名
（本技能只做「主链 + 位号」，不做「完整中文名称」）、
立体异构（顺反、手性）、有机合成路线设计、
光谱解析（红外 / 核磁 / 质谱）、反应机理（用 `edu-chem-reaction`）。
遇到请直接说明未覆盖。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页。
本技能产出的是**自包含的交互教学网页**，构建与校验都有成本。

- 只要求**一个数值答案**（如「求 Ω」）——直接算并作答，不必做页。
- 题目是**无机反应 / 反应机理 / 配平**——用 `edu-chem-reaction`。
- 题目是**溶液浓度、稀释、pH**——用 `edu-chem-calc`。
- 题目要的是**分子 3D 动画**（成键断键）——用 `edu-chem-reaction`。

## 目录结构

```
edu-organic-chem/
├── SKILL.md
├── lib/organic_kernel.py        # 内核（7 组函数 + 85 条自检，仅用标准库）
├── scripts/generate.py          # 注入模板 + 7 个 build_* + 读数对账
└── template/
    ├── board.html               # 组装产物（勿直接修改）
    └── parts/                   # 模板片段（改这里再 compose）
        ├── scene_functions.html # 7 个 drawXxx + 碳骨架绘制 + hBar
        ├── scene_dispatch.html
        ├── page_title.html
        └── board_label.html
```

## 扩展

- **加题型**：在 `organic_kernel.py` 加计算函数（+ `__main__` 自检），
  在 `generate.py` 加 `build_*`（含对账）并注册进 `REGISTRY`。
- **加分子**：往 `ALKANES`（碳骨架）或 `FUNC_MOLS`（官能团个数）里加一条即可，
  画板布局与等效氢会自动跟上。
- **加场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `scene_dispatch.html` 加 case，然后 `python ../../tools/compose_templates.py`
  重新组装 `template/board.html`。**不要直接改 `board.html`**。
