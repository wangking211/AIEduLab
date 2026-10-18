---
name: edu-geography
description: >-
  把一道自然地理计算题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个可变参数滑块驱动实时重算的地理量 + 状态灯 + 定值指示器），中栏 KaTeX
  分步解析，右栏 2D Canvas 地理画板（太阳直射点回归曲线、地球剖面的正午太阳高度、
  昼长随纬度曲线、经线与时区色带、地形剖面与坡度、气温垂直递减、流域水量平衡）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。只覆盖自然地理中
  **可算**的部分：太阳直射点纬度的回归运动、正午太阳高度 H = 90°−|φ−δ|、
  昼长与日出日落（时角 cosω = −tanφ·tanδ，含极昼极夜）、时区与地方时、
  等高线判读与坡度、对流层气温垂直递减率、水循环水量平衡等题型，统一由
  sympy 精确计算驱动（答案、分步数值、画板读数同源一致）。其它 agent 也可调用本技能
  生成此类网页。形态与 edu-chem-calc 平行（复用 seq-phys 模板家族，并新增
  declination / sunangle / daycurve / globe / contour / atmos / basin 七种场景）。
  触发词：地理, 自然地理, 太阳直射点, 直射点纬度, 回归运动, 黄赤交角, 回归线,
  正午太阳高度, 太阳高度角, 昼长, 日出日落, 时角, 极昼, 极夜, 极圈, 晨昏线,
  时区, 区时, 地方时, 经度差, 时差, 等高线, 等高距, 相对高度, 坡度, 陡坡缓坡,
  气温垂直递减率, 递减率, 雪线, 水循环, 水量平衡, 径流, 径流深, 蒸发, 流域,
  解这道地理题, 随机出一道地理计算题, 这张图里的地理题;
  geography, physical geography, solar declination, subsolar point, noon sun
  altitude, day length, sunrise sunset, hour angle, polar day, polar night,
  time zone, local time, longitude, contour line, slope, lapse rate, snow line,
  water cycle, water balance, runoff, interactive geography solution page.
---

# 自然地理交互教学网页 (edu-geography)

把一道**可算的**自然地理题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
sympy 精确计算驱动，地理画板 + KaTeX 分步解析。

## 覆盖边界（先看清再选技能）

本技能**只做能形式化计算的部分**（判据沿用 `edulab/coverage-audit.md` 的
① 可算 / ② 结构化 / ③ 配图 分级）。自然地理里可算的，主要是**天文几何、
气象几何与水文收支**三类。下列内容**明确不覆盖**，遇到请直接说明：

| 不覆盖的内容 | 原因 |
| --- | --- |
| 气候类型判读（气温降水图 → 判断气候） | 依赖**数据集**，判读还需要区域知识，不是「给定参数→输出数值」 |
| 洋流、大气环流、地质构造、地貌成因 | 描述性/图示性，无唯一可算内核 |
| 人文地理（人口迁移、城市化、区位分析、产业布局） | ③ 配图级，不可形式化 |
| 地图投影与坐标变换 | 本技能未实现（需要额外数学） |

## 依赖（重要）

计算核心 `lib/geo_kernel.py` 依赖 **sympy**。运行前确认有能 import sympy 的解释器：
`python -c "import sympy"`。

**缺库时**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python -m pip install sympy`）或换一个已装该库的解释器；**不要未经询问直接装**。
Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-geography
python scripts/generate.py list                      # 列出已注册题型
python scripts/generate.py daylight ./sol.html       # 昼长
python scripts/generate.py all ./output              # 全部题型
python scripts/generate.py random 7 ./random.html    # 随机出题（seed=7）
python lib/geo_kernel.py                            # kernel 内置自检（48 条）
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

七个题型 key 与画板场景的对应：

| key | 场景 | 主问题 |
| --- | --- | --- |
| `declination` | `declination` | 太阳直射点纬度怎么随日期变？范围由什么决定？ |
| `sunalt` | `sunangle` | 正午太阳高度怎么算？什么时候小于 0？ |
| `daylight` | `daycurve` | 昼长怎么算？为什么会极昼极夜？ |
| `timezone` | `globe` | 地方时与区时差多少？为什么？ |
| `terrain` | `contour` | 相对高度与坡度怎么算？单位怎么统一？ |
| `lapse` | `atmos` | 每升高 1 km 降多少度？雪线在多高？ |
| `water` | `basin` | 径流深与径流总量怎么算？为什么两段之和恒定？ |

## 工作流程（AI 调用时）

### 第 1 步：得到 problem spec（三入口归一）
把题面归一成：已知量（纬度/经度/日期/海拔/距离/降水量…）、所求、单位、语言。
先判断属于上面哪个题型，再决定用哪个 key。

### 第 2 步：用 kernel 精确计算（不要心算）
`lib/geo_kernel.py` 提供：
- 日期与赤纬：`declination` `date_from_doy` `doy_from_date`
- 太阳：`hour_angle` `day_length` `sunrise_sunset` `day_status` `noon_altitude` `noon_side`
- 时间：`local_time` `timezone_of` `time_str`
- 地形：`slope_from_rise_run`
- 气象：`lapse_temp` `lapse_drop`
- 水文：`water_balance`
- 常数：`OBLIQUITY` `LAPSE_RATE` `DEG_PER_HOUR_ZONE`

### 第 3 步：组装数据并注入模板
数据三段 `lesson` / `steps` / `board`。可直接照抄 `scripts/generate.py` 的 7 个 `build_*`。

**每个读数表达式都必须与内核值对账**：`_agree(label, expr, want)` 在构建期用等价的
Python 实现求值一次再比对，不一致直接停构建。

### 第 4 步：自检（正确性方案）
- kernel 答案 == 答案卡 `lesson.answer` == 末步骤展示值 == 画板读数初值，四者一致。
- `python lib/geo_kernel.py` 自检全过（48 条）。
- 起本地静态服务预览检查：
  - 无控制台报错；
  - 滑块拨到最小/最大，读数**和画布**都跟着变；
  - **滑块的 `value` 必须落在 `step` 网格上**：`min`/`step`/`value` 不自洽时，
    浏览器会把初始值**悄悄吸附**到最近网格点，页面上「题设值」根本拖不到。
    自检时务必读回 `input.value` 核对（本技能就因此把默认经度从 87.6° 改成 116°）；
  - 画布内容**不贴边**（长注释最容易顶出画布；右侧一列文字要留足余量）；
  - 定值指示器跟踪的读数恒定（如 `terrain` 的相对高度、`lapse` 的递减率、
    `water` 的降水总量）；
  - 状态灯在该翻转的参数值上翻转。
- 交付：成品写到 cwd，命名 `solution-<题目简述>.html`。

## 扩展

- **加题型**：在 `geo_kernel.py` 加求解函数（+ `__main__` 自检），
  在 `generate.py` 加一个 `build_*`（含 `_agree` 对账）并注册进 `REGISTRY`。
- **加画板场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `template/parts/scene_dispatch.html` 加 case，然后
  `python ../../tools/compose_templates.py` 重新组装 `template/board.html`。
  **不要直接改 `board.html`** —— 它是模板家族组装出来的产物，会被下次组装覆盖。

### 两个必须小心的跨语言差异

1. **取整语义**：Python 的 `round()` 是**银行家舍入**（`round(6.5) == 6`），
   JS 的 `Math.round` 不是（`Math.round(6.5) == 7`）。涉及取整的读数一律写成
   `floor(x + 0.5)`，内核也一样 —— 否则经度正好落在时区边界上时两边会给出不同答案。
2. **字符串型场景字段**：`buildScene` 只把字符串求值成**数字**，非数字串会退回原串。
   所以「南/北」这类**随参数变化的文本**不要在 `scene` 里写成表达式，
   要在 `drawXxx` 内部按 `S.<param>` 现算（本技能 `sunangle` 的方位就是这样处理的）。

## 数值出处分级

**现算**（内核由公式推出，无手写数字）
太阳直射点纬度 δ、正午太阳高度 H、半昼弧时角 ω、昼长、日出日落地方时、极昼极夜判定、
地方时、时区号、坡度（百分比与角度）、气温递减量与各海拔气温、蒸发量、径流深、
径流总量。

**实测**（取教材常数，不是本页现算的）
黄赤交角 `23.44°`（教材 23°26′）、对流层平均气温垂直递减率 `6 °C/km`、
经度时差 `15°/h`。这些都标注为教材/约定值，不做位数扩展。

**假设**（题面给定或为使图形可读而设定，逐条如下）
- `declination`：滑块为年积日 N ∈ [1, 365]，题设 172（夏至）。
- `sunalt`：直射点固定在夏至 δ = +23.44°；滑块为观测纬度 φ ∈ [−90, 90]，题设 40°（北京）。
- `daylight`：δ 固定 +23.44°；滑块为纬度 φ ∈ [−90, 90]，题设 40°。
- `timezone`：基准经线 120°E 恒为 12:00；滑块为目标经度 λ ∈ [−180, 180]，题设 116°（北京实址）。
- `terrain`：A 在 100 m、B 在 500 m 等高线上（相对高度恒为 400 m），等高距 100 m；
  滑块为水平距离 ∈ [0.5, 5.0] km，题设 2.0 km。
- `lapse`：山脚 0 m 气温 20 °C，递减率 6 °C/km；滑块为海拔 ∈ [0, 5000] m，题设 3000 m。
- `water`：年降水量 800 mm、流域面积 1000 km²；滑块为蒸发比例 e ∈ [0, 1]，题设 0.4。

**四条必须写进步骤的近似**（否则图在撒谎）
1. δ 用教材惯用的**正弦近似** `δ ≈ 23.44°·sin(2π(N−81)/365)`，不是真正的黄道坐标解算，
   误差在 1° 量级。
2. 气温垂直递减率 `6 °C/km` 是**统计平均值**；干空气约 1 °C/100 m，湿空气更小，
   实际还受天气系统影响。
3. 水量平衡 `降水 = 蒸发 + 径流` 忽略了流域**蓄水变化 ΔS**（多年平均下可略）。
4. 地方时按**平太阳时**算，不考虑均时差（真太阳时与平太阳时之差，全年 ±16 分钟内）。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页，
交互页能说清就别做视频。本技能产出的是**自包含的交互教学网页**，构建与校验都有成本，
不适合「随口问一句」的场景。

- 题目要**判读气候类型**（给出气温降水图让判断气候）——依赖数据集与区域知识，
  本技能不覆盖，请直接说明。
- 题目属**人文地理**（人口、城市、农业区位、产业转移）——不可形式化，直接说明不覆盖。
- 题目要**洋流、大气环流、地质地貌成因**的分析——无唯一可算内核，直接说明不覆盖。
- 题目只要求**一个数值答案**（如「昼长几小时」）——直接算并作答，不必做页。
- 题目是**天文/物理**层面的（开普勒定律、轨道要素、摄动）——用 `edu-physics-senior`，
  本技能只到教材级的地理结论。
- 题目属**数学**（数列、三角恒等变换）——用 `edu-math-sequences`。

## 目录结构

```
edu-geography/
├── SKILL.md
├── lib/geo_kernel.py              # 天文/几何/水文内核（7 组求解函数 + 48 条自检）
├── scripts/generate.py            # 注入模板 + 7 个 build_* + 读数对账 + 批量/随机出题
└── template/
    ├── board.html                 # 组装产物（勿直接修改）
    └── parts/                     # 模板片段（改这里再 compose）
        ├── scene_functions.html   # 7 个 drawXxx + 与内核同式的天文量
        ├── scene_dispatch.html    # 场景分派
        ├── page_title.html        # 「自然地理 · 交互学习」
        └── board_label.html       # 画板角标
        # 注意：本技能**不覆盖** expr_mathenv.html —— 基础 MATHENV 已含
        # sin/cos/tan/acos/atan/sqrt/min/max/floor/PI，够用，少一份重复。
```
