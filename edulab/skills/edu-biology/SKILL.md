---
name: edu-biology
description: >-
  把一道生物题 / 一个生物知识点做成自包含的交互教学网页，覆盖初中到高中四个模块：
  ①遗传与变异（单杂交·双杂交·测交·伴性遗传，Punnett 棋盘格推演 + 基因型/表现型比例）；
  ②细胞与结构（Three.js 可交互 3D 细胞：动物·植物·原核，分步高亮各细胞器 + 三细胞对比表）；
  ③生理过程（光合与呼吸的物质守恒、尿的形成、反射弧、血液循环，流程图 + 实时计算控制台）；
  ④生态（能量金字塔与能量传递效率、种群数量变化 J 型/S 型）。
  支持三入口——给定文字题、随机出题、上传图片识别后解题。
  左栏题面 + 动态控制台（滑块驱动实时重算的读数 + 状态灯 + 定值不变量），中栏 KaTeX 分步解析，
  右栏 2D Canvas 画板（棋盘格/金字塔/增长曲线/流程图）或 Three.js 3D 细胞。
  统一由 sympy 精确内核驱动：杂交组合与比例、原子守恒、能量传递、种群增长全部精确计算，
  答案、分步数值与画板读数同源一致。其它 agent 也可调用本技能生成此类网页。
  形态与 edu-physics-junior / edu-chem-reaction 平行，但用「Canvas-2D 画板 + Three.js 细胞 3D」
  两种右栏形态并自动选择。
  触发词：生物, 遗传, 遗传与变异, 基因分离定律, 基因自由组合定律, 孟德尔, 单杂交, 双杂交, 测交,
  自交, 棋盘格, Punnett, 基因型, 表现型, 性状比, 显性, 隐性, 纯合, 杂合, 伴性遗传, 红绿色盲,
  血友病, X染色体, 系谱, 细胞, 细胞结构, 细胞器, 动物细胞, 植物细胞, 原核细胞, 细菌, 细胞壁,
  细胞膜, 细胞核, 拟核, 线粒体, 叶绿体, 液泡, 内质网, 高尔基体, 核糖体, 中心体, 光合作用,
  呼吸作用, 物质变化, 尿的形成, 肾小球, 肾小管, 重吸收, 反射, 反射弧, 缩手反射, 条件反射,
  血液循环, 肺循环, 体循环, 心脏四腔, 生态系统, 能量流动, 能量金字塔, 营养级, 能量传递效率,
  种群数量变化, J型增长, S型增长, 环境容纳量, K值, 解这道生物题, 随机出一道生物题,
  这张图里的生物题; biology, genetics, monohybrid cross, dihybrid cross, Punnett square,
  test cross, sex-linked inheritance, cell structure, organelle, animal cell, plant cell,
  prokaryotic cell, photosynthesis, respiration, urine formation, reflex arc, blood
  circulation, energy pyramid, trophic level, population growth, logistic growth,
  interactive biology solution page.
---

# 生物题 / 知识点 → 交互网页

## 这个技能产出什么

一个可直接用浏览器打开的单页 HTML，**右栏形态按内容自动二选一**：

- **Canvas-2D 画板**（遗传 / 生态 / 生理）：Punnett 棋盘格（基因型网格 + 表现型配色 + 比例条）、
  能量金字塔（宽度 ∝ 能量、标注传递效率）、种群增长曲线（J 型 vs S 型、标出 K 与 K/2）、
  生理流程图（节点 + 有向箭头，节点副标题可随滑块变化）。
- **Three.js 3D 细胞**（细胞与结构）：可拖拽旋转/缩放的动物·植物·原核细胞，**分步高亮**各细胞器
  （其余结构淡出）+ 浮动标签 + 点击查看详情 + 三种细胞对比表。

左栏是题面 + **动态控制台**（滑块 → 实时读数 + 状态灯），底部可有**定值指示**（真不变量）；
中栏是 **KaTeX 分步解析**。形态与 `template/board.html`、`template/cell.html` 一致。

## 依赖（重要）

计算核心 `lib/bio_kernel.py` 与 `lib/cell_library.py` 依赖 **sympy**。运行脚本前先确认有一个能 import
sympy 的 `python3`：跑 `python3 -c "import sympy"`。

**缺库时的处理**：若 import 报错，**先询问用户是否安装**，同意后再装
（`python3 -m pip install sympy`）或换解释器；**不要未经询问直接装**。

模板只依赖 CDN 上的 Tailwind / KaTeX / Three.js，生成的 HTML 联网即可打开。

## 工作流程

### 第 1 步：把题归一成结构化信息

- **遗传类**：亲本基因型（如 `AaBb × AaBb`）、显隐关系、所求（比例 / 概率 / 某种表现型）。
- **细胞类**：细胞种类（动物 / 植物 / 原核），要讲哪些结构。
- **生理类**：是物质换算（给了多少 CO₂ / 原尿量）还是过程串联（反射弧 / 循环路线）。
- **生态类**：是能量传递（起始能量、营养级数、传递效率）还是种群增长（N₀、λ 或 K、r）。
- **图片**：用视觉读图抽取题干，并**把识别到的信息回显给用户确认**（亲本基因型 / 性状显隐 /
  单位 / 所求）后再继续。显隐性没写全时按常规假设并明确告知。

> **输出语言跟随提示词语言**：英文提示 → 英文网页，中文 → 中文。

### 第 2 步：用 kernel 精确计算（不要心算）

按 `references/conventions.md` 的约定调用 kernel：

- 遗传：`cross_summary(父, 母)` 给出基因型/表现型比例与棋盘格；`test_cross`、`sex_linked_cross`、
  `progeny_prob`（通配查询）。
- 代谢：`photosynthesis_balance(co2_mass=…)` 自动配平并校验原子守恒。
- 生态：`energy_pyramid`、`energy_needed`、`exponential_growth`、`logistic_growth`、`logistic_max_rate`。
- 细胞：`cell_library.build_payload(kind)` 直接产出 3D 场景数据。

讲解文字里的每个数字都从 kernel 的返回值插进去（示例见 `references/conventions.md` 第一节）。

### 第 3 步：组装并生成

- 遗传页用 `generate._punnett_scene(cross_summary(...))` 组装棋盘格场景（**不要手工拼**）。
- 其余页按 `references/problem-schema.md` 写 `board.scene` / `board.params` / `board.readouts`，
  然后 `render_html`。
- 生产流程：

```bash
python lib/bio_kernel.py                 # 内核自检（必须 OK ✓）
python lib/cell_library.py               # 细胞库自检（必须 OK ✓）
python scripts/generate.py list          # 列出全部题型
python scripts/generate.py all ./output  # 生成全部 + index.html
python scripts/generate.py random out.html
```

### 第 4 步：自检（改完必过，见 references/conventions.md 第七、八节）

- 内核与细胞库自检都打印 `OK ✓`。
- 浏览器复核：**0 控制台报错**、**0 `.katex-error`**、画板有像素（细胞页看
  `renderer.info.render.triangles > 0`）、滑块拖动后读数改变、状态灯双向可切换、
  `constant`（定值指示）与滑块无关。
- 遗传页比例必须是**约分后**的；棋盘格必须是**正方形**（`equalAspect` 生效）。

> **交付纪律**：成品写**用户指定的输出目录**，**绝不写技能自身的 `output/`**（那是随技能分发的开发样例）。

## 覆盖的题型（14 个 build，四模块）

| 模块 | 题型 | 右栏 |
|---|---|---|
| 遗传与变异 | 单杂交 `monohybrid`、双杂交 `dihybrid`、测交 `testcross`、伴性遗传 `sexlinked` | 棋盘格 |
| 细胞与结构 | 动物 `animal_cell`、植物 `plant_cell`、原核 `prokaryotic_cell` | 3D 细胞 |
| 生理过程 | 光合与呼吸 `photosynthesis`、尿的形成 `urine`、反射弧 `reflex`、血液循环 `circulation` | 流程图 |
| 生态 | 能量金字塔 `energy_pyramid`、种群数量变化 `population` | 画板 |

## 文件结构

```
edu-biology/
├── SKILL.md                      # 本文件
├── lib/
│   ├── bio_kernel.py             # sympy 精确内核：遗传/代谢/生态（自检 OK ✓）
│   └── cell_library.py           # 程序化细胞器 3D 库（自检 OK ✓）
├── template/
│   ├── board.html                # Canvas-2D 数据驱动模板（punnett/pyramid/population/flow）
│   └── cell.html                 # Three.js 细胞 3D 模板（分步高亮 + 对比表）
├── scripts/
│   └── generate.py               # build_* + REGISTRY + CLI（list/all/random）
├── references/
│   ├── problem-schema.md         # lesson/data 数据格式（含全部 scene 字段）
│   └── conventions.md            # 建模与写作约定 + 常见坑 + 自检清单
└── output/                       # 开发样例（随技能分发，非交付目录）
```

## 与其它技能的形态对照

| 技能 | 右栏 | 内核角色 |
|---|---|---|
| edu-physics-junior | Canvas-2D 力学画板 | 牛顿定律/运动学 |
| edu-chem-reaction | Three.js 分子动画 | 配平/键差 |
| **edu-biology** | **Canvas-2D 画板 或 Three.js 细胞 3D** | **遗传比例/原子守恒/能量传递/种群增长** |
