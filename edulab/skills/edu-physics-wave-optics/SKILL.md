---
name: edu-physics-wave-optics
description: >-
  把一道高中物理「机械振动 / 机械波 / 光」题解成一个自包含的交互教学网页：左栏题面 +
  动态控制台（一个可变参数滑块驱动实时重算的物理量 + 状态灯 + 定值指示器），
  中栏 KaTeX 分步解析，右栏 2D Canvas 物理画板（参考圆与 x-t 曲线、波形与质点振动方向、
  驻波波节波腹、拍与包络、双缝干涉条纹、折射与全反射光路、凸透镜成像光路）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖简谐运动、
  横波的传播、驻波、波的叠加与拍、双缝干涉、折射定律与全反射、凸透镜成像等题型，
  统一由 Python 内核现算（答案、分步数值、画板读数同源一致）。
  其它 agent 也可调用本技能生成此类网页。形态与 edu-physics-thermal 平行（复用 seq-phys
  模板家族，并新增 shm / wave / standing / beat / doubleslit / refraction / lens
  七种场景）。触发词：机械振动, 简谐运动, 振幅, 周期, 频率, 角频率, 相位, 参考圆,
  回复力, 单摆, 机械波, 横波, 波长, 波速, 波形图, 振动图象, 质点振动方向,
  波的叠加, 干涉, 衍射, 驻波, 波节, 波腹, 拍, 拍频, 多普勒,
  光, 光的折射, 折射定律, 斯涅尔定律, 折射率, 全反射, 临界角, 光纤, 棱镜,
  双缝干涉, 条纹间距, 杨氏双缝, 光的干涉, 光的衍射, 光栅, 凸透镜成像, 像距,
  放大率, 实像, 虚像, 焦点, 焦距, 解这道振动题, 解这道光学题, 随机出一道物理题,
  这张图里的光学题; mechanical vibration, simple harmonic motion, reference circle,
  mechanical wave, transverse wave, wavelength, wave speed, standing wave, node,
  antinode, beats, superposition, interference, double slit, fringe spacing,
  refraction, Snell's law, refractive index, total internal reflection, critical
  angle, optical fibre, thin lens, image distance, magnification, real image,
  virtual image, interactive wave optics solution page.
---

# 机械振动 · 机械波 · 光 交互教学网页 (edu-physics-wave-optics)

把一道「振动 / 波 / 光」题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
内核现算驱动，2D 物理画板 + KaTeX 分步解析。
**至此高中物理五大板块（力学 / 电磁 / 热学 / 振动波光 / 近代）全部有技能覆盖。**

## 与相邻技能的边界（先看清再选技能）

| 技能 | 管什么 | 判据 |
| --- | --- | --- |
| `edu-physics-senior` | **必修一力学**（传送带、追及、斜面、平抛、圆周、v-t） | 题目里有运动过程与牛顿定律 |
| `edu-physics-junior` | **初中物理** | 初中内容 |
| `edu-physics-em` | **高中电磁学** | 题目里有电荷、电流、磁场 |
| `edu-physics-thermal` | **热学 + 近代物理**（选择性必修三） | 题目里有 $p,V,T$ / 光子 / 能级 / 半衰期 |
| **本技能** | **选择性必修一**：机械振动、机械波、光 | 题目里有周期/波长/折射角/条纹/像距 |
| `edu-math-sequences` | 数学的三角与数列 | 题目是纯数学 |

**尚未覆盖**：动量定理与动量守恒、碰撞（都在选择性必修一，但属「力学」而非波动）。

## 依赖（重要）

计算核心 `lib/waveoptics_kernel.py` 依赖 **sympy**。运行前确认：`python -c "import sympy"`。
**缺库时**先询问用户是否安装（`python -m pip install sympy`）或换解释器，**不要未经询问直接装**。
Windows 控制台打印 ✓ 报 UnicodeEncodeError 时先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-physics-wave-optics
python scripts/generate.py list                       # 列出已注册题型
python scripts/generate.py refraction ./sol.html      # 折射与全反射
python scripts/generate.py all ./output               # 全部题型
python scripts/generate.py random 7 ./random.html     # 随机出题（seed=7）
python lib/waveoptics_kernel.py                      # kernel 内置自检（66 条）
```

> 不传输出路径时默认写到**当前工作目录（cwd）**。

| key | 场景 | 主问题 |
| --- | --- | --- |
| `shm` | `shm` | 参考圆为什么能代表简谐运动？$v$、$a$ 何时最大？ |
| `wavemotion` | `wave` | 「波形平移」与「质点振动」有什么区别？质点往哪走？ |
| `standing` | `standing` | 波节在哪？为什么相邻波节恰好差 $\lambda/2$？ |
| `beat` | `beat` | 拍频是多少？为什么调音师把拍「听没了」就调准了？ |
| `interference` | `doubleslit` | 条纹间距为什么是 $L\lambda/d$？白光为什么中央是白的？ |
| `refraction` | `refraction` | 临界角怎么来的？为什么光纤不会漏光？ |
| `thinlens` | `lens` | 一倍焦距为什么分虚实？二倍焦距为什么分大小？ |

## 工作流程（AI 调用时）

1. **归一题面**：已知量、所求、单位、语言，判断属于哪个题型。
2. **用 kernel 现算**（不要心算）：
   - 简谐运动：`shm_x` `shm_v` `shm_a` `shm_force` `shm_period` `shm_omega` `shm_phase`
   - 横波：`wave_y` `wave_speed` `wave_number` `wave_omega` `particle_velocity`
   - 驻波：`standing_y` `nodes` `antinodes` `node_spacing`
   - 叠加与拍：`beat_sum` `beat_env` `beat_freq` `beat_period`
   - 双缝：`fringe_spacing` `fringe_position` `fringe_order_at`
   - 折射：`snell_angle` `critical_angle` `is_total_internal` `refractive_index`
   - 透镜：`lens_image` `lens_magnification` `lens_is_virtual` `lens_is_inverted`
3. **组装数据**三段 `lesson` / `steps` / `board`；可照抄 `scripts/generate.py` 的 7 个 `build_*`。
   **每个读数表达式都要与内核值对账**（`_agree`）。
4. **自检**：kernel 自检全过（66 条）；答案卡 == 末步展示值 == 画板读数初值；
   起本地静态服务，滑块拨到**至少 5 个档位（含两端）**，确认
   ① 无控制台报错 ② 每一档**画布都真的变了**（指纹哈希） ③ 不裁边
   ④ 状态灯在该翻转的参数值上翻转。

## 本技能特有的坑（都踩过）

### 1. 光路图：实像必须画在透镜**同侧之外**的那一侧
`1/u + 1/v = 1/f` 约定 $u$、$v$ 取正表示在透镜**两侧**。所以实像（$v>0$）在**右**，
虚像（$v<0$）在**左**。写代码时极易把相机侧的坐标映射（`X = LX − s·d`）直接套到像上 ——
这样实像会画到物体那一侧去，**而且画布指纹照样在变，看哈希根本发现不了**。
> 正确：物用 `Xo(cm) = LX − sx*cm`，像用 `Xi(cm) = LX + sx*cm`。
> **验证手法**：把画出的像的像素位置换算回世界坐标，与 `Xi(v)` 对拍
> （本轮实测 $u=30/20/15$ 分别得到 6.22 / 6.56 / 7.24，与 $Xi(v)$ 完全一致）。

### 2. 射线要**裁到绘图框**，不能让它冲出画布
光线是无限延伸的。直接画到「像点」对虚像不成立（虚像没有真实交点），
画到画布外又会触发裁边检查。用一个 `rayEnd()` 求直线与绘图框的交点，既正确又不裁边。
横纵比例可以不同（仿射变换保持直线与交点），但**物高与像高必须用同一个纵向比例**。

### 3. 双缝 / 折射的「无解」档位要显示成「—」，而不是崩掉
$i > C$ 时 $\sin r = \frac{n_1}{n_2}\sin i > 1$，$\arcsin$ 无定义 ——
页面上 `Math.asin` 返回 `NaN`，`fmt` 自动显示「—」，状态灯同时翻转成「全反射」。
**在 Python 侧对账时要避开这些档位**（`math.asin` 会直接抛异常），
并且要单独断言「该档位内核返回 `None`」。

### 4. 沿用上一轮的三条（详见 `edu-physics-thermal/SKILL.md`）
① 场景字段要引用 `scalars` 里的**标量**而非滑块原始值；
② 状态灯文案是**纯文本**，不能写 `$…$`，且 `evalExpr` 只返回数字（布尔会变 NaN），
比较必须写在 `expr`/`op`/`rhs` 上，`rhs` 要留足容差；
③ 一行文字不超过约 28 个汉字（11px）—— 本技能所有页面已按 ≤24 字排版。

## 单位契约

| 题型 | 滑块单位 | 说明 |
| --- | --- | --- |
| `shm` / `wavemotion` / `standing` | s（时间） | 只让时间走，看周期性与平衡位置 |
| `beat` | Hz | 拍频直接是差值 |
| `interference` | nm（波长） | 表达式内部乘 `1e-9` 还原成 m |
| `refraction` | °（度） | 表达式内部转弧度 |
| `thinlens` | cm | 与 cm 同量纲，比用 m 更直观 |

## 数值出处分级

### ① 现算（内核算出，**不手写数字**）
位移/速度/加速度/回复力、周期与角频率、相位；波形函数与质点振动速度、波速；
驻波振幅、波节/波腹位置与间距；合振动与包络、拍频与拍周期；
条纹间距与各级明纹位置；折射角、临界角、全反射判据；像距、放大率、实虚像判据。

### ② 实测（物理常数，取自教材常数表）
$c = 3.00\times10^8\ \mathrm{m/s}$（教材三位有效数字，**不是** CODATA 全精度值）。

### ③ 约定（示例参数，不是实测值）
- `shm`：$A = 1$ m、$T = 2$ s ⇒ $\omega = \pi$ rad/s；滑块 $t\in[0,4]$ s，题设 0.5 s。
- `wavemotion`：$A = 1$ m、$\lambda = 4$ m、$T = 2$ s；被标记的质点 $P$ 在 $x = 5$ m；
  滑块 $t\in[0,4]$ s，题设 0.5 s。
- `standing`：$A = 1$ m（入射波振幅，波腹为 $2A$）、$\lambda = 4$ m、$T = 2$ s；
  滑块 $t\in[0,4]$ s，题设 0.5 s。
- `beat`：$f_1 = 440$ Hz（**这是约定值，不是实测的「标准音」频率**）；
  滑块 $f_2\in[440,460]$ Hz，题设 448 Hz。
- `interference`：$L = 1$ m、$d = 0.5$ mm；滑块 $\lambda\in[400,700]$ nm，题设 600 nm。
- `refraction`：$n_1 = 1.5$（**取「玻璃」的典型值，实际各类玻璃在 1.5–1.9 之间**）、
  $n_2 = 1.0$（空气）；滑块 $i\in[0,80]$°，题设 30°。
- `thinlens`：$f = 10$ cm；滑块 $u\in[4,40]$ cm，题设 30 cm。
  纵向比例与横向不同（仿射缩放，不改变光线交点）；像高超出绘图框时会截断并注明。

### 未覆盖
动量定理与动量守恒、碰撞（弹性/完全非弹性）、多普勒效应、
光的偏振、光栅衍射、透镜组合、球面镜成像、电磁波与波粒二象性。
遇到请直接说明未覆盖。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页。
本技能产出的是**自包含的交互教学网页**，构建与校验都有成本。

- 只要求**一个数值答案**（如「求临界角」）——直接算并作答，不必做页。
- 题目是**力学 / 电磁学 / 热学与近代**——用 `edu-physics-senior`（力学）、`edu-physics-em`（电磁学）、`edu-physics-thermal`（热学与近代）、`edu-physics-momentum`（动量）。
- 题目是**动量与碰撞**——用 `edu-physics-momentum`。
- 题目是**纯数学的三角函数与图象**——用 `edu-math-sequences` / `edu-function-derivative`。
- 题目是**动量与碰撞**——用 `edu-physics-momentum`。
## 目录结构

```
edu-physics-wave-optics/
├── SKILL.md
├── lib/waveoptics_kernel.py     # 内核（7 组函数 + 66 条自检）
├── scripts/generate.py          # 注入模板 + 7 个 build_* + 读数对账
└── template/
    ├── board.html               # 组装产物（勿直接修改）
    └── parts/                   # 模板片段（改这里再 compose）
        ├── scene_functions.html # 7 个 drawXxx + rayEnd + 绘图框助手
        ├── scene_dispatch.html
        ├── page_title.html
        └── board_label.html
```

## 扩展

- **加题型**：在 `waveoptics_kernel.py` 加计算函数（+ `__main__` 自检），
  在 `generate.py` 加 `build_*`（含 `_agree` 对账）并注册进 `REGISTRY`。
- **加场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `scene_dispatch.html` 加 case，然后 `python ../../tools/compose_templates.py`
  重新组装 `template/board.html`。**不要直接改 `board.html`**。
