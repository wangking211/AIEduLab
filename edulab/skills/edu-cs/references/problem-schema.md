# 课件 lesson 数据格式

一份课件就是一个 JSON 对象（Python dict），由 `scripts/generate.py` 注入到
`template/board.html` 的 `__LESSON_DATA__` 占位符里。模板是**唯一**的渲染入口，
所有画面都来自这份数据，不额外请求任何东西。

```
lesson = {
  "title":    str,      # 大字标题
  "subtitle": str,      # 副标题（放实测数值，如「实测比较 25 次」）
  "module":   str,      # 模块名，显示在左上角小字
  "intro":    str,      # 题面 / 情境说明
  "scene":    { "kind": ..., ... },      # 画板静态配置（见第二节）
  "steps":    [ {…}, … ],                # 回放帧序列（见第三节）
  "console":  { "params", "readouts", "lights", "constant" },  # 动态控制台
  "explain":  [ { "h": str, "body": str } ],   # 分步解析（body 内可用 $…$）
  "answer":   str,      # 结论区；为空则整个结论框隐藏
  "counters": { str: num },   # 统计卡片（来自 kernel 的 counters）
  "pills":    [ { "text", "color", "bg" } ],  # 顶栏标签
  # 其余标量键（name / result / target / total / size / n / count …）
  # 会被自动收进「统计」卡片；对象与数组不会被收。
}
```

`steps` 至少要有 1 帧 —— 静态场景（复杂度曲线、位运算表、字符编码）也用一个
占位帧，否则进度条与「第 x / y 帧」会显示 `0 / 0`。

## 一、控制台 DSL

四个数组，全部走同一套表达式求值：

```python
PARAM(id, label, value, mn=2, mx=100000, step=1, unit="")
READ (id, label, expr, color="#0f766e")
LIGHT(id, label, expr)                       # expr 为真 → 亮
const constant = {"label": str, "expr": expr, "note": str|None}
```

### 求值语义（**这几条踩过坑，务必记住**）

1. **读数按声明顺序求值，并写回作用域**：后面的读数可以引用前面的读数。
   例：`READ("ops", …)` 之后可以写 `READ("sec", "折算秒数", "ops/1e8")`。
2. **助手优先**：作用域是 `{...参数与已算读数, ...助手}` —— 助手在**后者**，
   所以即使某个读数恰好叫 `hex`，表达式里的 `hex(...)` 仍然指助手函数。
   即便如此，**不要**用助手名当 id（校验器会拦）。
3. **id 必须是合法 JS 标识符、非 JS 保留字**。用 `new` / `class` / `in` 之类当 id
   会让整个 `Function(...)` 构造抛错，该页**所有**表达式一起变 null
   —— 表现为读数全是 `—`，且没有任何报错。
4. 每个表达式内部用 `return (…);` 包裹，因此**必须是一个表达式**，不能写语句或多行。
5. 表达式里只能引用：已声明的 id、助手函数、`Math.*` 等白名单全局、字面量。

### 内置助手

| 助手 | 含义 |
|---|---|
| `pc(x)` | `x` 的二进制里 1 的个数（popcount） |
| `lg(x)` | 以 2 为底的对数，`x ≤ 1` 时取 0 的下界 |
| `ln(x)` | 自然对数 |
| `bin(x)` | 二进制字符串 |
| `hex(x)` | 十六进制字符串（带 `0x`） |
| `twos(x, w)` | 把 `x` 解释成 `w` 位补码的有符号值 |
| `pct(a, b)` | `a / b`（`b` 为 0 时返回 0） |

### 校验

`python generate.py verify` 会逐条检查上面的规则，包括
「表达式引用了未声明的标识符」。**写完就立刻 verify**，不要等页面跑起来才发现读数是 `—`。

## 二、scene —— 画板配置

`scene.kind` 决定用哪个渲染器。所有渲染器都从 `scene`（静态）与
`steps[frame]`（动态）里取数据，二者字段合起来用。

| kind | 用途 | 必需字段 | 渲染器额外读取的 step 字段 |
|---|---|---|---|
| `bars` | 数组：排序 / 查找 / 贪心 | — | `a` `cmp` `swap` `sorted` `range` `mid` `pivot` `found` `merge` |
| `curve` | 复杂度增长曲线 | `series` `nmax` | —（静态） |
| `linear` | 栈 / 队列 | `rule` | `stack` 或 `queue` `op` `top` |
| `linked` | 单链表 | — | `nodes` `head` `hi` `new` `prev` |
| `tree` | 二叉树 / BST / 堆 | — | `heap`（堆）或 `nodes`+`pos`（树）；`path` `at` `dir` `visit` `visited` `hi` `swap` `op` `pop` |
| `graph` | BFS / DFS / Dijkstra / Prim | `pos` `edges` | `visited` `cur` `push` `queue` `stack` `done` `dist` `edge` `relax` `inTree` `chosen` `add` `depth` |
| `table` | DP 表 / 哈希桶 | `table` 或 `mode:"buckets"` | `table` `buckets` `hi` `from_` `h` `key` |
| `bits` | 位运算 / 进制 / 编码 | `mode` ∈ `ops`/`encode`/`convert` | `rows`（ops）· `utf8_bits`（encode）· `rems` `q` `r` `n` `step` `result`（convert） |
| `call` | 递归调用树 | `calls` | `node` `path` |
| `coins` | 贪心找零 | `coins` `amount` | `left` `take` `used` |
| `interval` | 区间调度 | `tasks` | `sorted_` `chosen` `hi` |

### 各渲染器的数据约定（照抄 kernel 的输出即可）

- **bars**：`a` 是数组；`cmp`/`swap`/`sorted` 是**下标数组**；`range` 是
  `[lo, hi]` 闭区间；`mid`/`pivot` 是**单个下标**；`found` 是下标（`null`/`false` 表示没找到）。
- **tree**：`treeModel()` 会统一三种形态 ——
  （a）堆：`st.heap` 数组，结点 id 自动为 `h0…hn`，孩子是 `2i+1/2i+2`；
  （b）BST：`scene.nodes=[{id,val,edges:[孩子 id]}]` + `scene.pos`；
  （c）完整二叉树遍历：`scene.nodes=[{id,val,parent}]` + `scene.pos`。
  高亮字段里的值会自动「值 → id」「下标 → id」翻译，所以 `path:[4,7,6]` 这种
  按值给的路径也能正确高亮。
- **graph**：`dist` 用 `null` 表示无穷（**不是** `Infinity`，因为要 JSON 安全）；
  `chosen` 是**边三元组** `[[u,v,w],…]`；`relax` 是**被松弛的结点 id（字符串）**；
  `edge` 是三元组。
- **table**：`table` 是一维数组时 `hi` 按「下标数组」解释（斐波那契）；
  是二维数组时 `hi` 按「`[行, 列]` 单元格」解释（背包）。`from_` 同理解释。
- **bits**：`mode` 必须显式给，别让模板靠「这一帧有没有某字段」去猜场景。
  `bitwise_ops().rows` 的行格式是 `{op, expr, bin, dec}`；
  `encode_char().utf8_bits` 单字节时是**字符串**，多字节时是数组。
- **coin/interval**：`used` 是 `[[面额, 枚数], …]`；`chosen` 是已选区间数组。

## 三、steps —— 回放帧

每一帧就是 kernel 录制的一个状态快照（`trace.add(**kw)` 的产物），
模板**只做呈现，不做推演**。硬性要求只有一条：

> 每帧必须有 `note`（或 `op`），用来填充中栏「当前步骤」卡片。

## 四、入口

```python
from scripts.generate import REGISTRY
lesson = REGISTRY["sort_bubble"]()      # 纯数据
render_html(lesson, "out/sort_bubble.html")
```

模拟智能体现场出题时，也是同一路径：调 kernel 拿 `steps` → 组 lesson → 注入模板。
