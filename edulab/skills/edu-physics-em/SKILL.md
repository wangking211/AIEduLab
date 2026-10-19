---
name: edu-physics-em
description: >-
  把一道高中物理（电磁学）题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个可变参数滑块驱动实时重算的物理量 + 状态灯 + 定值指示器 + 能量条），中栏
  KaTeX 分步解析，右栏 2D Canvas 电磁学画板（点电荷与受力、场强叠加采样、平行板电容器、
  带电粒子在匀强磁场中的圆周、带电粒子在匀强电场中的类平抛、闭合电路、
  电磁感应线圈、通电导线受安培力）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖库仑定律与点电荷场强、
  电场强度叠加与零场点、平行板电容器、质子在磁场中的回旋半径与周期、示波管式偏转、
  闭合电路欧姆定律与输出功率、法拉第电磁感应定律、安培力与左手定则等题型，
  统一由 sympy 精确计算驱动（答案、分步数值、画板读数同源一致）。其它 agent 也可调用
  本技能生成此类网页。形态与 edu-physics-senior 平行（复用其数据驱动 Canvas + KaTeX
  模板骨架，并新增 charge / dipole / plates / circb / deff / circuit / induction /
  ampere 八种场景）。触发词：高中物理, 电磁学, 库仑定律, 库仑力, 电场强度, 场强叠加,
  合场强, 零场点, 电容器, 电容, 平行板电容器, 匀强电场, 带电粒子, 偏转, 类平抛,
  带电粒子在磁场中, 回旋半径, 洛伦兹力, 交流电周期, 闭合电路, 欧姆定律, 路端电压, 内阻,
  输出功率, 最大输出功率, 电磁感应, 感应电动势, 磁通量, 法拉第电磁感应定律, 安培力,
  左手定则, 解这道电磁学题, 随机出一道高中物理电磁学题, 这张图里的电磁学题;
  senior high physics, electromagnetism, Coulomb force, electric field, field
  superposition, equipotential-free point, parallel-plate capacitor, charged
  particle deflection, cyclotron radius, Lorentz force, closed circuit Ohm law,
  terminal voltage, electromagnetic induction, Faraday's law, magnetic flux,
  Ampere force, interactive electromagnetism solution page.
---

# 高中物理·电磁学交互教学网页 (edu-physics-em)

把一道高中电磁学题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
sympy 精确计算驱动，电磁学画板（电荷/场叠加/电容器/磁场圆周/电场偏转/电路/感应/安培力）
+ KaTeX 分步解析。

## 依赖（重要）

计算核心 `lib/em_kernel.py` 依赖 **sympy**。运行脚本前先确认有能 import sympy 的
解释器：`python -c "import sympy"`。

**缺库时**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python -m pip install sympy`）或换一个已装该库的解释器；**不要未经询问直接装**。
Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-physics-em
python scripts/generate.py list                      # 列出已注册题型
python scripts/generate.py coulomb ./sol.html        # 库仑定律
python scripts/generate.py all ./output              # 全部题型
python scripts/generate.py random 7 ./random.html    # 随机出题（seed=7）
python lib/em_kernel.py                             # kernel 内置自检（41 条）
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

八个题型 key 与画板场景一一对应：

| key | 场景 | 主问题 |
| --- | --- | --- |
| `coulomb` | `charge` | 距离减半，库仑力变成几倍？ |
| `field_sum` | `dipole` | 等量异号电荷连线的延长线上，哪点合场强为零？为什么在弱电荷外侧？ |
| `capacitor` | `plates` | 极板间距变化时 C、E、Q、W 怎么变？保持与电源相连意味着什么不变？ |
| `mag_circ` | `circb` | 回旋半径与周期分别跟速率什么关系？哪个跟速率无关？ |
| `eb_deflect` | `deff` | 示波管式偏转：侧移量与偏角怎么算？初动能去哪了？ |
| `ohm` | `circuit` | 路端电压怎么算？外电阻等于内阻时输出功率最大吗？ |
| `faraday` | `induction` | 磁通量变化越快，电动势怎么变？磁通量本身变了吗？ |
| `ampere` | `ampere` | 导线与磁场成 θ 角时安培力多大？力的方向在纸面内还是垂直纸面？ |

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面（文字/图片识别/随机）归一成：已知量（电荷量/距离/电容/磁感应强度/速率/
电动势/电阻/匝数/角度…）、所求、单位、语言。

**单位务必对齐场景约定**，这是本技能最常见的错误来源：
- `mag_circ` / `eb_deflect` 的滑块值单位是 **×10⁶ m/s**，进公式前必须先还原成 SI 的 m/s
  （场景里已用 `vsi` / `v0*1e6` 处理，新增表达式时照做）。
- `capacitor` 的极板间距滑块单位是 **mm**，电场强度读数用 **V/m**（不是 V/mm）。
- `field_sum` 的位置单位是 **dm**（分米），电场强度是 N/C。
- `eb_deflect` 的侧移量读数是 **mm**，穿越时间是 **ns**。

常量按教材惯例：真空静电力常量 `k = 9.0×10⁹ N·m²/C²`，元电荷 `e = 1.6×10⁻¹⁹ C`，
质子质量 `m = 1.67×10⁻²⁷ kg`（**均为假设类常数**，见下文出处分级）。

### 第 2 步：用 kernel 精确计算（不要心算）
调用 `lib/em_kernel.py`：
- `coulomb` `field_at` `field_vector_at` `capacitor` `magnetic_circle`
  `magnetic_period` `electric_deflect` `circuit` `faraday` `flux` `ampere_force`
- 辅助：`tex`（LaTeX）`f`（浮点）`num_str` `sci_tex` `K_COULOMB` `Q_PROTON` `M_PROTON` `E_CHARGE`。
断言在 kernel 与 build_* 两层都有，答案错误会直接抛出。

**方向类结论不要靠记忆，要用判据现算**：
- 洛伦兹力 `F = qv×B`。带电粒子在 B 垂直纸面向里时做**逆时针**运动（正电荷）。
  自检里用 `_v.cross(_B)` 断言过，别写反。
- 电场方向由极性决定：极板上 `+` 下 `−` → 电场**向下**，正电荷向**下**极板偏转。
  画上去的箭头与轨迹必须与这个方向一致，否则图在撒谎。
- 安培力 `F ∝ I×B` 垂直于 I 与 B 所决定的平面。B 放在纸面内、导线与 B 成 θ 角时，
  力**垂直纸面**，只能画 `⊗`（或 `⊙`），不能在纸面内画箭头。

### 第 3 步：组装数据并注入模板
构建脚本写在**临时目录**，只把 `.html` 写到 cwd。数据三段
`lesson` / `steps` / `board`，调用 `generate.render_html(data, out)` 注入
`template/board.html`。

可直接照抄的范本：`scripts/generate.py` 里 8 个 `build_*` 覆盖全部场景。
每个 build_* 内置自检断言：内核算出的关键值必须与喂给画板的表达式在默认参数处吻合。

### 第 4 步：自检（正确性方案）
- kernel 答案 == 答案卡 `lesson.answer` == 末步骤展示值 == 画板读数初值，四者一致。
- 起本地静态服务（服务输出文件所在目录）预览检查：
  - 无控制台报错（含 `animT is not defined` 这类循环变量未声明）；
  - KaTeX 正常，无残留 `{{ }}` 模板记号；
  - 滑块拨到最小/最大，读数**和画布**都跟着变（只变读数不动图 = 坐标没写成参数表达式）；
  - 画布内容**不贴边**：像素包围盒四周留有余量（视窗要放得下最长的箭头 + 居中排版的文字）；
  - 定值指示器跟踪的读数恒定（如 `mag_circ` 的 T/f 与速率无关、`faraday` 的 ΔΦ 恒定）；
  - 状态灯在该翻转的参数值上翻转（如 `field_sum` 拖到零场点显示 E = 0）；
  - 能量条比例正确。
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`，把路径告诉用户。

## 扩展

- **加题型**：在 `em_kernel.py` 加求解函数（写成精确表达式 + `__main__` 自检），
  在 `generate.py` 加一个 `build_*` 并注册进 `REGISTRY`。
- **加画板场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  并在 `template/parts/scene_dispatch.html` 加 case，然后
  `python ../../tools/compose_templates.py` 重新组装 `template/board.html`。
  **不要直接改 `board.html`** —— 它是模板家族组装出来的产物，改了会被下次组装覆盖。
  场景字段放 `board.scene`，数值字段可写成表达式（按 param + scalars 顺序求值，
  后项可引用前项）。字符串字段求值失败时保留原串，故 `kind`/`caption` 可安全写字面量。
  嵌套对象（如 `dipole` 的 `probe`）外壳不解析，需在 `draw` 内自行 `evalExpr`。

## 数值出处分级

本技能的每一个数字都属三类之一，写步骤与图注时必须与之一致：

**现算**（sympy 由公式推出，无手写数字）
库仑力与点电荷场强、场强矢量叠加与合场强为零的解、平行板电容 `C = εᵣε₀S/d`、
极板间场强、极板带电量与储能、回旋半径 `r = mv/(qB)`、回旋周期 `T = 2πm/(qB)`、
带电粒子在匀强电场中的加速度/穿越时间/侧移量/偏角、闭合电路电流与路端电压与
内压降与输出功率与效率、最大输出功率条件、感应电动势 `ε = NΔΦ/Δt` 与磁通量变化、
安培力 `F = BIL sinθ`。

**实测**（取自教材常数表，不是本页现算的）
真空静电力常量 `k = 9.0×10⁹ N·m²/C²`、真空介电常数 `ε₀ = 8.85×10⁻¹² F/m`、
元电荷 `e = 1.6×10⁻¹⁹ C`、质子质量 `m = 1.67×10⁻²⁷ kg`、重力加速度 `g = 9.8 m/s²`。
这些值的有效数字按教材给定，不做位数扩展；用到 `εᵣ`（相对介电常数）时属**题设给定**。

**假设**（题面给定或为使图形可读而设定，逐条如下）
- `coulomb`：电荷量 `q₁ = +2 μC`、`q₂ = +1 μC`，初始间距 `r = 0.20 m`，**同号**故为斥力。
- `field_sum`：`q₁ = +4 μC` 在原点、`q₂ = −1 μC` 在 `3 dm` 处，探测点可在 `4~8 dm` 间移动。
- `capacitor`：`S = 0.02 m²`、`εᵣ = 2`、电源电压 `V = 12 V` 恒定（**保持与电源相连**，
  故 U 不变 —— 这是本题的定值来源，若题面改为断开电源则定值换为 Q 不变）。
- `mag_circ`：质子、`B = 0.5 T` 垂直纸面向里、速率滑块 `0.5~1.5 ×10⁶ m/s`（题设 `1.0`）。
- `eb_deflect`：质子、`E = 8×10⁴ V/m`、极板长 `L = 5 cm`、极板间距 `24 mm`、
  速率滑块 `1.0~3.0 ×10⁶ m/s`。**下限取 1.0 是有物理原因的**：速率更低时侧移量超过
  半板间距，粒子会打在极板上，类平抛解不再成立。
- `ohm`：电动势 `E = 12 V`、内阻 `r = 1 Ω`、外电阻滑块 `0~20 Ω`。
- `faraday`：`N = 100` 匝、磁通量从 `0` 匀变到 `0.6 Wb`、`Δt` 滑块 `0.02~0.4 s`。
- `ampere`：`B = 0.4 T`（纸面内）、`I = 3 A`、`L = 0.5 m`、夹角滑块 `0~90°`。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页，
交互页能说清就别做视频。本技能产出的是**自包含的交互教学网页**，构建与校验都有成本，
不适合「随口问一句」的场景。

- 题目属**初中内容**（简单串并联电路、欧姆定律基础、家庭电路）——用 `edu-physics-junior`。
- 题目是**必修一力学**（传送带、追及相遇、斜面、平抛、牛顿第二定律、动能定理、
  竖直圆周）——用 `edu-physics-senior`，本技能不覆盖力学。
- 题目是**光学、热学、原子物理、交变电流的变压器与远距离输电**——本技能只覆盖
  静电场 / 恒定电流 / 稳恒磁场 / 电磁感应，直接说明不覆盖。
- 题目要解**交流电路的相量、阻抗、谐振**——超出高中范围，直接说明。
- 只要求一个数值答案——直接算并作答。
- 用户明确要**视频**——用 `edu-physics-video`。
- 题目是**力学**——用 `edu-physics-senior` / `edu-physics-junior`。
- 题目是**热学与近代物理**——用 `edu-physics-thermal`。
- 题目是**振动 / 波 / 光**——用 `edu-physics-wave-optics`。
- 题目是**动量与碰撞**——用 `edu-physics-momentum`。
## 目录结构

```
edu-physics-em/
├── SKILL.md
├── lib/em_kernel.py               # sympy 精确计算核心（11 个求解函数 + 41 条自检）
├── scripts/generate.py            # 注入模板 + 8 个 build_* 范本 + 批量/随机出题
└── template/
    ├── board.html                 # 组装产物（勿直接修改）
    └── parts/                     # 模板片段（改这里再 compose）
        ├── scene_functions.html   # 8 个 drawXxx + wire/flowDots/meter 助手
        └── scene_dispatch.html    # 场景分派
```
