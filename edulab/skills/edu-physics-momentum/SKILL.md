---
name: edu-physics-momentum
description: >-
  把一道高中物理「动量与碰撞」题解成一个自包含的交互教学网页：左栏题面 +
  动态控制台（一个可变参数滑块驱动实时重算的物理量 + 状态灯 + 定值指示器），
  中栏 KaTeX 分步解析，右栏 2D Canvas 物理画板（F-t 冲量面积图、碰撞前后两行小球、
  爆炸反向飞出、人船位移与质心线、子弹打木块滑行、二维动量矢量三角形）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖动量定理与缓冲、
  完全非弹性碰撞、弹性碰撞、反冲与爆炸、人船模型、子弹打木块、等质量弹性斜碰的
  90° 定理等题型，统一由 Python 内核现算（答案、分步数值、画板读数同源一致）。
  其它 agent 也可调用本技能生成此类网页。形态与 edu-physics-senior 平行（复用 seq-phys
  模板家族，并新增 impulse / collide_in / collide_el / recoil / boat / bullet /
  collide2d 七种场景）。触发词：动量, 冲量, 动量定理, 动量守恒, 冲量定理, 缓冲,
  安全气囊, 碰撞, 弹性碰撞, 完全非弹性碰撞, 非弹性碰撞, 正碰, 对心碰撞, 斜碰,
  反冲, 爆炸, 火箭, 后坐, 人船模型, 质心, 子弹打木块, 滑块木板, 动量与能量,
  解这道动量题, 解这道碰撞题, 随机出一道动量题, 这张图里的动量题;
  momentum, impulse, impulse-momentum theorem, conservation of momentum, collision,
  elastic collision, perfectly inelastic collision, recoil, explosion, rocket,
  center of mass, bullet-block problem, 2D collision, right-angle theorem,
  interactive momentum solution page.
---

# 动量与碰撞交互教学网页 (edu-physics-momentum)

把一道「动量 / 碰撞」题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
内核现算驱动，2D 物理画板 + KaTeX 分步解析。
**这是高中物理最后一个未覆盖的力学板块；至此力学（牛顿 + 动量）完整。**

## 与相邻技能的边界（先看清再选技能）

| 技能 | 管什么 | 判据 |
| --- | --- | --- |
| `edu-physics-senior` | 必修一力学（牛顿定律、运动学、圆周、平抛） | 题目里有 $F=ma$ 与运动过程 |
| **本技能** | 选择性必修一：动量、冲量、碰撞 | 题目里有 $mv$、冲量、碰前碰后、爆炸、反冲 |
| `edu-physics-wave-optics` | 选择性必修一：振动、波、光 | 题目里有周期/波长/折射角/条纹 |
| `edu-physics-junior` | 初中物理 | 初中内容 |
| `edu-physics-em` | 高中电磁学 | 题目里有电荷、电流、磁场 |
| `edu-physics-thermal` | 热学 + 近代物理 | 题目里有 $p,V,T$ / 光子 / 能级 |

**判据**：题目里出现「**碰撞前后**」「**冲量**」「**总动量**」——用本技能；
只出现「力与加速度」——用 `edu-physics-senior`。

## 依赖（重要）

计算核心 `lib/momentum_kernel.py` 依赖 **sympy**。运行前确认：`python -c "import sympy"`。
**缺库时**先询问用户是否安装（`python -m pip install sympy`）或换解释器，**不要未经询问直接装**。
Windows 控制台打印 ✓ 报 UnicodeEncodeError 时先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-physics-momentum
python scripts/generate.py list                     # 列出已注册题型
python scripts/generate.py elastic ./sol.html       # 弹性碰撞
python scripts/generate.py all ./output             # 全部题型
python scripts/generate.py random 7 ./random.html   # 随机出题（seed=7）
python lib/momentum_kernel.py                      # kernel 内置自检（63 条）
```

> 不传输出路径时默认写到**当前工作目录（cwd）**。

| key | 场景 | 主问题 |
| --- | --- | --- |
| `impulse` | `impulse` | 冲量为什么等于 F-t 图的面积？缓冲为什么能救命？ |
| `inelastic` | `collide_in` | 动量守恒但动能不守恒，损失的钱去哪了？ |
| `elastic` | `collide_el` | 等质量为什么交换速度？$m_2>m_1$ 为什么被弹回？ |
| `recoil` | `recoil` | 爆炸后为什么总动量为零？谁跑得快？ |
| `boat` | `boat` | 人在船上走，船为什么后退？为什么质心不动？ |
| `bullet` | `bullet` | 为什么损失 98% 的动能？滑行距离与木块多重有关吗？ |
| `twod` | `collide2d` | 等质量弹性斜碰为什么恒成 90°？ |

## 工作流程（AI 调用时）

1. **归一题面**：已知量、所求、单位、**正方向约定**，判断属于哪个题型。
2. **用 kernel 现算**（不要心算）：
   - 动量与动能：`momentum` `kinetic` `total_momentum` `total_kinetic`
   - 动量定理：`impulse` `delta_p` `avg_force` `impulse_force_time`
   - 完全非弹性：`inelastic_v` `kinetic_loss` `loss_fraction`
   - 弹性：`elastic_v1` `elastic_v2` `elastic_pair`
   - 反冲爆炸：`recoil_v` `explosion_velocities` `explosion_energy`
   - 人船：`boat_shift` `boat_person_shift` `boat_boat_shift`
   - 子弹木块：`bullet_common_v` `bullet_kinetic_loss` `bullet_slide_distance`
   - 二维：`equal_mass_elastic2d`
3. **组装数据**三段 `lesson` / `steps` / `board`；可照抄 `scripts/generate.py` 的 7 个 `build_*`。
   **每个读数表达式都要与内核值对账**（`_agree`）。
4. **自检**：kernel 自检全过（63 条）；答案卡 == 末步展示值 == 画板读数初值；
   起本地静态服务，滑块拨到**至少 5 个档位（含两端）**，确认
   ① 无控制台报错 ② 每一档**画布都真的变了**（指纹哈希） ③ 不裁边
   ④ 状态灯在该翻转的参数值上翻转。

## 本技能的坑

### 1. 正方向约定必须先定，且要写进解答
动量是**矢量**。一维问题一律「取向右为正，速度带符号代入」。
本页的 `impulse`：撞前 $+10\ \mathrm{m/s}$、反弹 $v_2 = -8\ \mathrm{m/s}$，
所以 $\Delta p = -9\ \mathrm{kg\cdot m/s}$（向左）——
**不要把「反弹速度 8 m/s」直接当成 $v_2 = +8$**，那会把冲量算成 $1\ \mathrm{N\cdot s}$。

### 2. 弹性碰撞与完全非弹性碰撞**不能混用**「碰后共速」
- 完全非弹性：动量守恒，**碰后共速**，动能损失最大；
- 弹性：动量与动能**同时**守恒，碰后一般**不共速**（除等质量交换速度）。

本技能的 `inelastic` 与 `elastic` 是两个不同的题型与场景，
**不要**把子弹打木块当成弹性碰撞（那是典型的一错到底）。

### 3. 子弹打木块：先用动量守恒求共同速度，再用动能定理求位移
两步不能颠倒。滑行距离 $s = \dfrac{v'^2}{2\mu g}$ 里**质量约掉了** ——
所以它与木块多重无关。这一条很适合拿来验算。

### 4. 沿用既有四条（详见 `edu-physics-thermal` / `edu-physics-wave-optics` 的 SKILL.md）
① 场景字段要引用 `scalars` 里的**标量**而非滑块原始值；
② 状态灯文案是**纯文本**，不能写 `$…$`，且 `evalExpr` 只返回数字（布尔会变 NaN），
比较必须写在 `expr`/`op`/`rhs` 上，`rhs` 要留足容差；
③ 一行文字不超过约 28 个汉字（11px）—— 本技能所有页面已按 ≤24 字排版；
④ **画布指纹必须逐档比较**，哈希不变 = 画布没跟着动（静默 bug 的唯一线索）。

## 数值出处分级

### ① 现算（内核算出，**不手写数字**）
动量、动能、总动量与总动能；冲量、动量变化、平均力；碰后共速与动能损失；
弹性碰撞的两速度、反冲与爆炸的速度、人船模型的两位移、
子弹共同速度与滑行距离、二维出射速度与点积。

### ② 实测（物理常数，取自教材常数表）
$g = 9.8\ \mathrm{m/s^2}$（教材常用值）。

### ③ 约定（示例参数，不是实测值）
- `impulse`：$m = 0.5$ kg，撞前 10 m/s、反弹 8 m/s（**约定为一次有能量损失的反弹**）；
  滑块 $t\in[0.01,0.5]$ s，题设 0.05 s。
- `inelastic`：$m_1 = 2$ kg、$v_1 = 6$ m/s，$m_2$ 静止；滑块 $m_2\in[1,10]$ kg，题设 4 kg。
- `elastic`：$m_1 = 1$ kg、$v_1 = 4$ m/s，$m_2$ 静止；滑块 $m_2\in[0.2,5]$ kg，题设 1 kg。
- `recoil`：一块 1 kg、释放能量 $E = 100$ J（**约定为全部转成动能**）；
  滑块 $m_2\in[0.5,5]$ kg，题设 4 kg。
- `boat`：人 60 kg、船 120 kg；滑块 $L\in[0.2,3]$ m，题设 1.5 m。
- `bullet`：子弹 0.02 kg、木块 0.98 kg、$\mu = 0.2$；滑块 $v\in[200,600]$ m/s，题设 400 m/s。
  画板滑行距离的**量程固定为 40 m**（线性比例）。
- `twod`：等质量 $m$、入射速度 5 m/s、靶球静止；滑块 $\theta\in[0,90]$°，题设 45°。

### 未覆盖
动量守恒的**变质量**问题（火箭方程、传送带加料）、
三维碰撞、连续碰撞（如 $n$ 个球依次碰撞的能量传递）、
动量与电磁场的耦合（洛伦兹力冲量）、相对论动量。
遇到请直接说明未覆盖。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页。
本技能产出的是**自包含的交互教学网页**，构建与校验都有成本。

- 只要求**一个数值答案**（如「求共同速度」）——直接算并作答，不必做页。
- 题目是**牛顿力学**（受力分析、运动学）——用 `edu-physics-senior`。
- 题目是**振动 / 波 / 光**——用 `edu-physics-wave-optics`。
- 题目是**电磁学 / 热学 / 近代物理**——用 `edu-physics-em`（电磁学）、`edu-physics-thermal`（热学与近代）、`edu-physics-wave-optics`（振动波光）。
- 题目是**纯数学的向量运算**（不涉及质量与碰撞）——用 `edu-vector`。

## 目录结构

```
edu-physics-momentum/
├── SKILL.md
├── lib/momentum_kernel.py       # 内核（7 组函数 + 63 条自检）
├── scripts/generate.py          # 注入模板 + 7 个 build_* + 读数对账
└── template/
    ├── board.html               # 组装产物（勿直接修改）
    └── parts/                   # 模板片段（改这里再 compose）
        ├── scene_functions.html # 7 个 drawXxx + ball/vArrowAt + 绘图框助手
        ├── scene_dispatch.html
        ├── page_title.html
        └── board_label.html
```

## 扩展

- **加题型**：在 `momentum_kernel.py` 加计算函数（+ `__main__` 自检），
  在 `generate.py` 加 `build_*`（含 `_agree` 对账）并注册进 `REGISTRY`。
- **加场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `scene_dispatch.html` 加 case，然后 `python ../../tools/compose_templates.py`
  重新组装 `template/board.html`。**不要直接改 `board.html`**。
