---
name: edu-cs
description: >-
  把一道计算机科学题 / 一个算法知识点做成自包含的交互教学网页，覆盖五个模块：
  ①算法可视化（冒泡·选择·插入·归并·快速排序、顺序与二分查找、复杂度曲线）；
  ②数据结构（栈·队列·单链表、二叉树三种遍历、二叉搜索树、最小堆、哈希表链地址法）；
  ③图算法（BFS·DFS、Dijkstra 最短路、Prim 最小生成树）；
  ④计算原理（进制转换、位运算、字符编码与 UTF-8）；
  ⑤算法思想（朴素递归的调用树与重复子问题、斐波那契 DP、0-1 背包、贪心找零与区间调度）。
  与其它 edu-* 技能不同：这里的动画不是画出来的，而是**算法真实跑一遍录下来的步骤**——
  lib/cs_kernel.py 用 Python 真切执行算法并存下每一步快照，右栏按进度滑块逐帧回放，
  保证动画里的每个状态都是算出来的，绝不编造。
  支持三入口——给定文字题、随机出题、上传图片识别后出题。
  左栏题面 + 动态控制台（滑块驱动实时重算的操作数/复杂度读数 + 状态灯 + 定值不变量），
  中栏 KaTeX 分步解析（讲清「为什么这个策略是对的」并给出反例），右栏 Canvas 画板
  （11 类场景：数组柱状/复杂度曲线/栈队列/链表/树/图/表格/位/调用树/硬币/区间）。
  仅依赖标准库，无需 sympy。其它 agent 也可调用本技能生成此类网页。
  触发词：计算机科学, 算法, 算法可视化, 数据结构, 冒泡排序, 选择排序, 插入排序, 归并排序,
  快速排序, 二分查找, 顺序查找, 时间复杂度, 空间复杂度, 大O, 复杂度曲线, 递归, 调用栈, 调用树,
  重复子问题, 分治, 动态规划, DP, 记忆化, 斐波那契, 0-1背包, 贪心, 找零, 区间调度, 活动选择,
  栈, 队列, 链表, 单链表, 二叉树, 遍历, 前序, 中序, 后序, 二叉搜索树, BST, 堆, 最小堆, 优先队列,
  哈希表, 哈希函数, 冲突, 链地址法, 图, BFS, 广度优先, DFS, 深度优先, 最短路, Dijkstra, 最小生成树,
  Prim, Kruskal, 进制转换, 二进制, 十六进制, 位运算, 补码, 与或异或, 移位, 字符编码, UTF-8,
  码点, ASCII, 信息学奥赛, 信奥, 高中信息技术, 算法入门, 解这道算法题, 随机出一道算法题,
  这张图里的算法题; computer science, algorithms, algorithm visualization, data structures,
  bubble sort, merge sort, quick sort, binary search, big-O, complexity, recursion, dynamic
  programming, knapsack, greedy, stack, queue, linked list, binary tree, BST, heap, hash table,
  graph, BFS, DFS, Dijkstra, minimum spanning tree, Prim, number base conversion, bitwise,
  two's complement, UTF-8, character encoding, interactive algorithm animation.
---

# edu-cs · 计算机科学交互课件

把一道 CS 题做成**会自己跑**的三栏网页：左栏题面与动态控制台，中栏分步解析，
右栏是一块**步骤回放**画板。

## 与其它 edu-\* 技能的根本差异

别的技能是「用精确内核**算出一个数**，再把数摆到画板上」。这个技能是
「用 Python **真正跑一遍算法**，把每一步的状态录下来，再逐帧回放」。

因此有一条铁律：

> **动画里的每一步都必须是算出来的。** 不要手写 steps、不要凭记忆写「大约比较 n²/2 次」。
> 一切数字都从 `lib/cs_kernel.py` 的返回值插进去。

这条规则带来一个很实在的好处：改一个参数，画板、步骤说明、讲义数字会**一起变**，
永远不会出现「文字说交换 4 次、动画只交换了 3 次」这种事故。

## 三入口

1. **给定文字题**——按下面的工作流，把题归一成 kernel 能接的参数。
2. **随机出题**——`python scripts/generate.py random ./out`。
3. **上传图片**——视觉读图抽取题干后，**把识别到的信息回显给用户确认**
   （数组内容 / 目标值 / 图与边 / 进制与基数 / 容量等）再继续。

> **输出语言跟随提示词语言**：英文提示 → 英文网页，中文 → 中文。

## 右栏：11 类画板场景

| 场景 | 用于 | 画面 |
|---|---|---|
| `bars` | 排序 / 查找 / 数组上的贪心 | 柱子，比较=橙、交换=玫红、已就位=青，区间用蓝框 |
| `curve` | 复杂度对比 | 多条增长曲线同图 |
| `linear` | 栈 / 队列 | 一排格子 + 顶指针 / 头尾指针 |
| `linked` | 单链表增删 | 结点盒（数据+指针）+ next 箭头 + head |
| `tree` | 二叉树 / BST / 堆 | 圆圈结点 + 父子连线 + 路径高亮 |
| `graph` | BFS/DFS/Dijkstra/MST | 结点按 `pos` 铺开 + 边权标签 + dist 读数 |
| `table` | DP 表 / 哈希桶 | 二维格（1D/2D 自动识别）或桶+链 |
| `bits` | 位运算 / 进制 / 编码 | 位格子逐位点亮；短除法阶梯；UTF-8 字节流 |
| `call` | 递归 | 调用树，高亮当前调用链 |
| `coins` | 贪心找零 | 面额行 + 硬币图标 + 剩余进度条 |
| `interval` | 区间调度 | 时间轴上的横条，冲突标红 |

画板下方是回放控件（首帧 / 上一步 / 播放 / 下一步 / 末帧 / 速度 + 进度条），
支持空格播放、左右方向键单步。

## 依赖（很轻）

`lib/cs_kernel.py` **仅用 Python 标准库**（`math`、`fractions`），不需要 sympy，
所以不存在「缺库」问题。模板只依赖 CDN 上的 Tailwind 与 KaTeX，生成的 HTML 联网即可打开。

## 工作流程

### 第 1 步：把题归一成 kernel 的参数

- **排序 / 查找**：数组内容、目标值；用哪种算法（冒泡 / 归并 / 快排 / 二分）。
- **数据结构**：操作序列（`push/pop`、`enq/deq`）、链表初值与插入删除位置、
  树的层序取值、BST 插入序列与查找目标、堆的插入序列与弹出次数、哈希键与桶数。
- **图算法**：顶点表、边表（带权给三元组）、起点。
- **计算原理**：十进制值与目标基数 / 两个操作数与位宽 / 字符。
- **算法思想**：递归深度 `n` / 物品重量价值与容量 / 面额与金额 / 任务区间。

图片入口：抽取后**回显确认**再继续。

### 第 2 步：用 kernel 真跑一遍（不要心算、不要手写步骤）

```python
import cs_kernel as K
r = K.bubble_sort([5, 3, 8, 1])
r["steps"]        # 每一步的状态快照 → 直接进 lesson["steps"]
r["counters"]     # {"compare": 6, "swap": 4} → 进统计卡片
r["pos"]          # 查找命中的下标
```

内核覆盖（全部返回 `{steps, counters, …}` 或静态数据）：

| 模块 | 函数 |
|---|---|
| 排序查找 | `bubble_sort` `selection_sort` `insertion_sort` `merge_sort` `quick_sort` `linear_search` `binary_search` |
| 复杂度 | `growth_values(kinds, nmax)` `ops_at(kind, n)` `max_n_for_budget(kind, budget)`（键：`1 logn n nlogn n2 n3 2n`） |
| 数据结构 | `stack_demo` `queue_demo` `linked_list_demo` `binary_tree_traversals` `bst_insert` `heap_demo` `hash_table_demo` |
| 图 | `bfs` `dfs` `dijkstra` `prim_mst` |
| 计算原理 | `base_convert` `bitwise_ops` `encode_char` |
| 算法思想 | `fib_recursive_calls` `fib_dp` `knapsack_dp` `greedy_coins` `greedy_interval` |

### 第 3 步：组装并生成

按 `references/problem-schema.md` 写 `scene` / `console` / `explain`，
再 `render_html(lesson, out)`。

```bash
python lib/cs_kernel.py                 # 内核自检（必须全部 OK ✓）
python scripts/generate.py verify       # 注册表 + 契约校验（推荐先跑）
python scripts/generate.py list         # 列出全部条目
python scripts/generate.py all ./output # 生成全部 + index.html
python scripts/generate.py sort_bubble ./out/sort_bubble.html
python scripts/generate.py random out.html
```

### 第 4 步：自检（改完必过）

1. `python lib/cs_kernel.py` → 全部 `OK ✓`
2. `python scripts/generate.py verify` → 契约校验通过
   （查 id 合法性 / 保留字 / 与助手重名 / 表达式引用了未声明的标识符 / 场景必需字段）
3. **离线回放冒烟**：桩掉 Canvas 与 DOM，把 `setFrame(0..n-1)` 全跑一遍、
   再把每个参数推到极值看读数是否变化。任何渲染器异常都会暴露。
4. **浏览器复核**：0 控制台报错、0 `.katex-error`、画板有像素、
   **拖滑块读数要真的变**（不变就是摆设）、状态灯双向可切换。

> **交付纪律**：成品写**用户指定的输出目录**，**绝不写技能自身的 `output/`**
> （那是随技能分发的开发样例）。

## 覆盖的题型（23 个 build，五模块）

| 模块 | 条目 | 右栏 |
|---|---|---|
| ① 算法可视化 | `sort_bubble` `sort_merge` `sort_quick` `search_binary` `complexity` | 柱状 / 曲线 |
| ② 数据结构 | `stack_lifo` `queue_fifo` `linked_list` `tree_traversal` `bst_search` `min_heap` `hash_table` | 栈队列 / 链表 / 树 / 表格 |
| ③ 图算法 | `bfs` `dijkstra` `mst` | 图 |
| ④ 计算原理 | `base_convert` `bitwise` `encoding` | 位 |
| ⑤ 算法思想 | `recursion_tree` `dp_fib` `dp_knapsack` `greedy_coins` `greedy_interval` | 调用树 / 表格 / 硬币 / 区间 |

## 文件结构

```
edu-cs/
├── SKILL.md                      # 本文件
├── lib/
│   └── cs_kernel.py              # 步骤轨迹引擎：真跑算法、录每一步（仅标准库，自检 OK ✓）
├── template/
│   └── board.html                # 数据驱动「步骤回放」模板（11 类场景 + 回放控件 + 控制台）
├── scripts/
│   └── generate.py               # build_* + REGISTRY + 契约校验器 + CLI（verify/list/all/random）
├── references/
│   ├── problem-schema.md         # lesson 数据格式（控制台 DSL + 全部 scene 字段 + 各渲染器约定）
│   └── conventions.md            # 建模与写作约定 + JSON 安全坑 + 自检清单
└── output/                       # 开发样例（随技能分发，非交付目录）
```

## 与其它技能的形态对照

| 技能 | 右栏 | 内核角色 |
|---|---|---|
| edu-physics-junior | Canvas-2D 力学画板 | 牛顿定律 / 运动学 |
| edu-biology | Canvas-2D 画板 或 Three.js 细胞 3D | 遗传比例 / 能量传递 |
| edu-plane-geometry | Canvas-2D 几何画板 | 几何量精确计算 |
| **edu-cs** | **Canvas-2D 步骤回放画板（11 类场景）** | **算法真实执行的轨迹录制** |

**共同点**：左栏题面 + 动态控制台（滑块 → 实时读数 + 状态灯 + 定值不变量）、
中栏 KaTeX 分步解析、右栏 Canvas 画板，数据与渲染彻底分离，
支持「预编译成课件」与「智能体现场生成」两个入口。
