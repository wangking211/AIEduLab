---
name: edu-computation-theory
description: >-
  把一道计算理论题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个可变参数滑块驱动实时重算的量 + 状态灯 + 定值指示器），中栏 KaTeX 分步解析，
  右栏 2D Canvas 画板（状态机图 + 逐步高亮、子集构造表、推导序列与推导树、
  泵引理的 x|y|z 分块、图灵机纸带与读写头、停机问题的对角线表、复杂度增长曲线）。
  自动机与图灵机都是**真的逐步跑**（每一步留下快照供滑块回放），
  子集构造**真的算 ε-闭包**，停机问题的矛盾表**真的构造**。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖 DFA 模拟、
  NFA→DFA 子集构造、上下文无关文法与推导树、泵引理、图灵机、停机问题的对角线法、
  P/NP 与复杂度增长等题型。
  其它 agent 也可调用本技能生成此类网页。形态与 edu-cs 平行（复用 seq-phys
  模板家族，并新增 statemachine / dfatable / parsetree / pumpstr / tape /
  haltmatrix / growthcurve 七种场景）。触发词：计算理论, 自动机, 有限自动机, DFA,
  确定型有限自动机, NFA, 非确定型有限自动机, 状态转移, 接受状态, 正则语言,
  正则表达式, 子集构造法, ε-闭包, 上下文无关文法, 文法, 推导, 推导树, 语法分析,
  泵引理, 图灵机, 纸带, 读写头, 停机问题, 不可判定, 可判定性, 对角线法,
  丘奇-图灵论题, 通用图灵机, 丘奇图灵, 计算复杂度, P, NP, NP完全, 多项式时间,
  归约, SAT, 千禧年问题, 解这道计算理论题, 随机出一道计算理论题,
  这张图里的计算理论题; computation theory, automata, DFA, NFA, finite automaton,
  regular language, subset construction, context-free grammar, derivation tree,
  pumping lemma, Turing machine, halting problem, undecidability, diagonalization,
  Church-Turing thesis, P vs NP, NP-complete, reduction, complexity classes,
  interactive computation theory solution page.
---

# 计算理论交互教学网页 (edu-computation-theory)

把一道计算理论题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
**真跑**内核驱动，2D 画板 + KaTeX 分步解析。

## 与相邻技能的边界（先看清再选技能）

| 技能 | 管什么 | 判据 |
| --- | --- | --- |
| `edu-cs` | **算法与数据结构**：排序、查找、树、图、DP、贪心 | 题目是「怎么算得更快」 |
| **本技能** | **计算理论**：自动机、文法、可计算性、复杂度类 | 题目是「什么能算、什么不能算、有多难」 |
| `edu-probability` / `edu-stat-inference` | 概率与统计推断 | 题目里有概率/样本 |
| `edu-multivariable-calc` | 多元微积分 | 题目要算积分/偏导 |

**判据**：题目里出现 DFA/NFA/文法/图灵机/可判定/P 与 NP —— 用本技能；
出现「用某种数据结构实现某个算法」—— 用 `edu-cs`。

## 依赖（重要）

计算核心 `lib/comptheory_kernel.py` **只用标准库**（`math` + `itertools`）。
运行前确认：`python -c "import math, itertools"`（必然成立）。

Windows 控制台打印 ✓ 报 UnicodeEncodeError 时先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-computation-theory
python scripts/generate.py list                    # 列出已注册题型
python scripts/generate.py dfa ./sol.html          # DFA 逐步模拟
python scripts/generate.py all ./output            # 全部题型
python scripts/generate.py random 7 ./random.html  # 随机出题（seed=7）
python lib/comptheory_kernel.py                   # kernel 内置自检（75 条）
```

> 不传输出路径时默认写到**当前工作目录（cwd）**。

| key | 场景 | 主问题 |
| --- | --- | --- |
| `dfa` | `statemachine` | 状态该记住什么？「确定型」体现在哪？ |
| `subset` | `dfatable` | DFA 的状态是什么？为什么两者等价？ |
| `grammar` | `parsetree` | 为什么 CFG 能配对计数而正则不能？ |
| `pumping` | `pumpstr` | 泵出后为什么跑出语言？矛盾在哪？ |
| `turing` | `tape` | 比自动机多了什么？为什么它定义「可计算」？ |
| `halting` | `haltmatrix` | D 与每一行什么关系？两种填法为什么都矛盾？ |
| `pnp` | `growthcurve` | 增长率差多少？P 与 NP 的定义与关系？ |

## 工作流程（AI 调用时）

1. **归一题面**：对象（DFA/NFA/CFG/TM）、所求（接受性/构造/证明/复杂度），判断题型。
2. **用 kernel 现算**（不要心算）：`dfa_run` `nfa_run` `nfa_epsilon_closure`
   `subset_construction` `reachable_states` `cfg_derive` `cfg_parse_tree`
   `pumping_check` `pumping_sequence` `tm_run` `tm_tape_str`
   `halting_matrix` `diagonal_program` `growth` `GROWTH_KINDS`。
3. **组装数据**三段 `lesson` / `steps` / `board`；可照抄 `scripts/generate.py` 的 7 个 `build_*`。
4. **自检**：kernel 自检全过（75 条）；答案卡 == 末步展示值 == 画板读数初值；
   起本地静态服务，滑块走过**每个档位**，确认
   ① 无控制台报错 ② **画布指纹数 = 档位数** ③ 不裁边
   ④ 状态灯在该翻转的参数值上翻转 ⑤ **没有读数显示成「—」**。

## 本技能特有的坑

### 1. 改了 `template/parts/` **必须重新 compose**
`generate.py` 读的是**组装产物** `template/board.html`。改完 parts 若不跑
`python ../../tools/compose_templates.py`，页面用的还是旧代码 ——
**改了没生效，看起来像「修改无效」**。本轮就因此白查了一轮
（先以为 `S.n` 写错、又以为索引字段写错，其实真正的 bug 是注释把 `wSeg` 吞掉了，
而那个修复也因为没 compose 而没生效）。

### 2. 注释会「吃掉」下一行语句
本轮的**真 bug**：`// 当前 n 的竖线` 与后面的 `wSeg(...)` 被挤到了同一行
（换行在某次文件读写中丢失），于是整条画线语句被注释掉了。
> 症状：**读数正常、控制台无报错，但画布有一部分永远不动**。
> 教训：批量改文件后要**抽查关键语句是否还在独立行上**。
> 本轮已全库扫过一遍 `//` 后粘代码的情况（当前为零）。

### 3. `arr_str` 不要重复套方括号
写「0/1 数组字面量」的助手如果返回的是 `"[0,1,0]"`，调用方再加一层就变成
`"[[0,1,0]][i-1]"` —— 外层列表只有 1 个元素，`[1]` 直接 `IndexError`。
> 约定：助手返回**裸串**（`"0,1,0"`），方括号由调用方加。已写进函数 docstring。

### 4. 场景的字段名要与**参数名**一致
`pnp` 的参数名是 `nn`，场景里却写了 `const n = S.n` → `undefined` →
`toX(undefined)` = `NaN` → 竖线不画。**画布不动但读数全对**。
（这与 `edu-quantum` 的「索引字段引用错参数名」是同一类问题，已第二次出现。）

### 5. 沿用既有三条（详见 `edu-physics-thermal` 的 SKILL.md）
① 场景字段要是表达式或数组，不能写死某个档位的具体数值；
② 状态灯文案是**纯文本**，不能写 `$…$`；`evalExpr` 只返回数字；
③ 一行文字不超过约 28 个汉字（11px）。

## 数值出处分级

### ① 现算（**真跑**，不手写数字）
DFA/NFA 的逐步模拟与接受性、ε-闭包、子集构造的全部状态与转移、
文法的推导序列与推导树、泵引理的分解与泵出结果、
图灵机的每一步纸带快照与读写头位置、停机问题的判定表与 D 行、各复杂度在给定 n 下的操作数。

> 特别说明：**没有查表**。子集构造是**真的算闭包与转移**（本页自检里抽样 11 个串，
> 逐一核对「子集构造前后接受性完全一致」）；图灵机是**真的模拟纸带**
> （自检断言「每一步最多改一个格子」「读写头始终在纸带范围内」）；
> 停机问题的 D 行是**真的构造**（自检断言「D 与表中每一行都不同」）。

### ② 约定（示例对象与画板布局）
- `dfa`：判定「二进制串中 1 的个数为偶数」；输入串固定 `11010010`（4 个 1 ⇒ 接受）。
- `subset`：NFA 识别 `(a|b)*abb`（4 状态）；子集构造的结果由内核算出。
- `grammar`：文法 $S \to aSb \mid \varepsilon$；演示 $n = 4$ 的推导。
- `pumping`：泵长度 $p = 5$、$|y| = 2$；重复次数 $i \in [0,5]$，题设 $i = 1$。
- `turing`：二进制加一；初始纸带 `1011`；滑块为步号。
- `halting`：判定表取 5×5（规模不重要，关键是「D 与每一行都不同」）；
  表中取值由一条**约定的确定性规则**（互质则停机）生成，只为构造出可验证的矛盾。
- `pnp`：六类复杂度；滑块 $n \in [1,64]$，题设 16。
- 画板的坐标范围、采样点数与对数刻度均为**约定的显示参数**。

### 未覆盖
下推自动机（PDA）与 CFG 的等价性证明、CYK 算法、
Myhill-Nerode 定理、正则语言的封闭性运算、
图灵机的编码与通用图灵机构造、归约的具体实例（SAT → 3-SAT）、
时间/空间层级定理、随机化复杂度、近似算法、密码学归约。
遇到请直接说明未覆盖。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页。
本技能产出的是**自包含的交互教学网页**，构建与校验都有成本。

- 只要求**一个答案**（如「这个串被接受吗」）——直接算并作答，不必做页。
- 题目是**算法与数据结构**（排序、树、图、DP）——用 `edu-cs`。
- 题目是**概率与统计**——用 `edu-probability` / `edu-stat-inference`。
- 题目是**多元微积分**——用 `edu-multivariable-calc`。

## 目录结构

```
edu-computation-theory/
├── SKILL.md
├── lib/comptheory_kernel.py     # 内核（8 组函数 + 75 条自检，仅用标准库）
├── scripts/generate.py          # 注入模板 + 7 个 build_* + 读数对账
└── template/
    ├── board.html               # 组装产物（**改 parts 后必须 compose**）
    └── parts/                   # 模板片段
        ├── scene_functions.html # 7 个 drawXxx + 状态机/纸带/表格助手
        ├── scene_dispatch.html
        ├── page_title.html
        └── board_label.html
```

## 扩展

- **加题型**：在 `comptheory_kernel.py` 加计算函数（+ `__main__` 自检），
  在 `generate.py` 加 `build_*`（含 `_agree` 对账）并注册进 `REGISTRY`。
- **加场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `scene_dispatch.html` 加 case，然后**必须** `python ../../tools/compose_templates.py`
  重新组装 `template/board.html`。**不要直接改 `board.html`**；
  新技能还要记得把名字加进 `compose_templates.py` 的 `FAMILIES` 用户列表。
