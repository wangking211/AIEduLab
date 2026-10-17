---
name: edu-knowledge-map
description: >-
  把一个知识领域画成「知识结构图」——概念之间的**前置关系**、合法知识状态的格、
  从零到目标概念的最短学习路径、以及此刻「还差哪几块」。左栏题面 + 动态控制台
  （学习步数滑块驱动实时重算的已掌握数 / 可学边界 / 缺口 + 定值指示器），中栏 KaTeX
  分步解析，右栏 2D Canvas 画板（前置关系图 ⇄ 知识状态格两种视图）。理论底子是
  Knowledge Space Theory（Doignon & Falmagne，ALEKS 背后的框架）：合法知识状态
  就是前置关系的下闭集，所有状态配上包含关系构成一个分配格。支持三入口——给定
  领域定义、随机出题、从文字描述里抽概念与前置。前置关系是学科判断（手写），
  其余全部由 lib/ks_kernel.py 现算（状态数、覆盖关系、可学边界、学习路径、缺口），
  改一条前置全图自动重算。只依赖标准库。触发词：知识结构, 知识图谱, 前置关系,
  先修关系, 学习路径, 学习顺序, 知识状态, 知识空间, 知识状态格, 哈斯图, Hasse,
  知识点关系, 概念图, 课程结构, 还差什么, 该先学什么, 知识缺口, 掌握程度,
  knowledge structure, knowledge space, prerequisite graph, learning path,
  concept map, Hasse diagram, knowledge gap, curriculum graph.
---

# 知识结构图 (edu-knowledge-map)

把一个知识领域画成可交互的结构图：**概念怎么连、学到哪了、下一步能学什么、到目标还差什么。**

和别的 edu-* 技能的区别：那些技能画的是**某个对象**（三角形的边、分子的键、电路的电流），
这个技能画的是**知识本身**——概念与概念之间的关系。

## 依赖（重要）

只用 **Python 标准库**，不需要 sympy，也不需要任何第三方包。

Windows 控制台若打印 ✓ 等字符报 UnicodeEncodeError，先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-knowledge-map
python scripts/generate.py list                      # 列出内置领域
python scripts/generate.py fraction ./out.html       # 分数四则运算
python scripts/generate.py derivative ./out.html     # 导数
python scripts/generate.py probability ./out.html    # 概率
python scripts/generate.py all ./output              # 全部 + index.html
python scripts/generate.py random 7 ./random.html    # 随机一个领域（seed=7）
python lib/ks_kernel.py                              # kernel 内置自检
```

> 不传输出路径时，默认写到**当前工作目录（cwd）**。

## 工作流程（AI 调用时）

### 第 1 步：得到领域定义
一个领域 = **概念表** + **前置关系**。前置关系是学科判断，不能算，必须由人（或 AI 依据
教材）给出；只写**直接**前置，间接前置由内核补全。

```python
concepts = [("int", "整数与整除"), ("factor", "因数与倍数"), ...]
prereqs  = {"factor": ["int"], "add2": ["add", "lcm"], ...}
```

概念数上限 12（合法状态会到 2^n，再多既画不动也看不完）。

### 第 2 步：先让内核校验
`Domain(...).problems()` 必须返回空列表：它会查未知概念、自环、以及**前置关系成环**。
成环的前置画出来一定似是而非，所以直接拒绝，不要"先画了再说"。

### 第 3 步：用内核算，不要手写任何图上的数
- `states()` 合法知识状态（下闭集）——注意**不是** 2^n
- `covers()` 覆盖关系（状态格的边）
- `outer_fringe(K)` 现在可学 / `inner_fringe(K)` 刚学会的边缘
- `learning_path(target)` 最短学习路径
- `gaps(K, target)` 还差哪几个概念
- `summary()` 概念数 / 状态数 / 边数 / 层数

### 第 4 步：组装并注入模板
数据三段 `lesson` / `steps` / `board`，调用 `skillkit.render_html(data, out)`。
`scripts/generate.py` 里的 `build_*` 就是范本；加领域只需在 `lib/ks_kernel.py`
的 `domains()` 里加一条，再在 `REGISTRY` 里注册。

### 第 5 步：自检
- kernel 自检：`python lib/ks_kernel.py`（17 条，含成环必须被拒绝）
- `scripts/generate.py all <临时目录>` 必须成功
- 打开产物：两个视图都能画（前置关系 / 状态格）、滑块每拖一步读数都跟着变、
  「已掌握」与图上的青色节点数一致、可学边界与缺口随状态变化
- 交付：成品写到 cwd，命名 `knowledge-<领域>.html`，把路径告诉用户

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页。
「概念之间的前置关系与学习路径」本身就是一张结构图才说得清的东西，所以这条技能
适用面窄，但踩中时别用文字硬讲。

- **题目是某一道具体学科的题**（求导、受力、配平、算法）——用对应的学科技能：
  数学用 `edu-function-derivative` / `edu-analytic-geometry` / `edu-math-sequences`，
  物理用 `edu-physics-junior` / `edu-physics-senior`，化学用 `edu-chem-reaction`。
  本技能不解题，只画知识结构。
- **只是要一张概念清单 / 名词解释**——直接回答，列出概念即可，不需要前置关系和状态格。
- **领域的概念超过 12 个**——合法状态会到 2^n，画不动也看不完；请先拆成子领域，
  或在上一层用「模块」代替「概念」。
- **前置关系本身有争议、还没定**——先定关系再用本技能，图会把争议固化；关系没定的
  时候直接说明「这需要学科判断，不能由我替你们拍板」。
- **需要视频讲解**——本仓库目前**没有**知识结构视频技能，请直接说明，不要假装有。
- **用户要的是「知识点之间的关系图」但关系的方向不重要**——普通思维导图更合适；
  本技能的边是有方向的、且带传递闭包语义，用它会把无向关系讲成有向。

## 扩展

- **加领域**：在 `lib/ks_kernel.py` 的 `domains()` 里加一个 `Domain`，在
  `scripts/generate.py` 的 `REGISTRY` 里注册一个 `build_*`。
- **加视图**：`template/board.html` 里 `draw()` 按 `mode` 分派；新视图写成
  `drawXxx(state)`，数据由 kernel 提供，不要在 JS 里重算数学。
- **改布局**：`prereq_layout()`（前置图分层）与 `Domain.lattice_layout()`
  （状态格分层）都在 Python 侧算好，JS 只负责映射到像素。

## 目录结构

```
edu-knowledge-map/
├── SKILL.md
├── template/board.html      # 数据驱动模板（前置关系图 / 状态格 双视图）
├── lib/ks_kernel.py         # 知识空间内核（纯标准库 + 自检）
├── scripts/generate.py      # 注入模板 + 三个领域范本 + 批量/随机
└── output/                  # 生成样例（不入库）
```
