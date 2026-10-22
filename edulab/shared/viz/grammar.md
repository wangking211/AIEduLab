# 图形语法契约（给 agent 用）

这是 `viz.js` 的**接口契约**。读完这份文档，你应该能一次写对一张图，并用校验器自证。

> **最重要的一条：不要手写 JSON。** 用 `vizkit.py` 的构造函数写 Python——
> 有函数签名就不会拼错字段，还能在构造后立刻校验。

```python
import vizkit as vk

spec = vk.spec(
    view=[0, 30, 0, 120000],            # [x0, x1, y0, y1]
    theme="paper",                       # "paper"（书页插图）| "dark"（解题器画板）
    layers=[
        vk.axis(xlab="年", ylab="资金"),
        vk.line(fn="P*(1+r/100)^x", from_=[0, 30], stroke=vk.PAPER.accent, width=3),
        vk.text(1.0, 108000, "复利曲线"),
    ],
)

rep = vk.validate(spec, W=783, H=300)
if not rep.ok:
    print(rep.format())        # 每条错误都带 ↳ 修法
```

**标准回路**：写 spec → `validate` → 有 error 就按 `fix` 提示改 → 直到 `ok` → 才交付。
`python vizkit.py selftest` 可自证校验器工作正常；`python vizkit.py check spec.json` 可离线校验。

---

## 一、spec 顶层结构

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `theme` | `"paper"` \| `"dark"` | ✅ | `paper` 用于书页插图（白底、印刷友好）；`dark` 用于解题器画板 |
| `view` | `{xRange:[x0,x1], yRange:[y0,y1], pad?, equalAspect?}` | ✅ | 世界坐标范围 |
| `layers` | `[图层, ...]` | ✅ | **按数组顺序绘制，后面的压在前面上** |
| `steps` | `[{note, ...}, ...]` | ⭕ | 步骤轨迹。每步的字段会并入场景状态，供 `when` 与表达式读取 |
| `params` | `[{name, min, max, step, value, ...}]` | ⭕ | 滑块。`value` 是默认值 |
| `scalars` | `[{name, expr}, ...]` | ⭕ | 由 params 派生的中间量，**按数组顺序求值** |
| `readouts` | `[{id, label, type, ...}, ...]` | ⭕ | 读数条 |
| `bg` | 颜色 | ⭕ | 覆盖主题背景色 |

### view 细则

- `xRange` / `yRange` **必须递增**，否则 E1。
- `pad` 默认 `{l:58, r:14, b:34, t:16}`（给坐标轴刻度与轴名留位）。**轴名要占左侧约 34px**，
  自行缩小时小心文字出框。
- `equalAspect: true` 让 x/y 等比例。**只要图里有方块类图元（`glyph` / `matrix`）就必须开**，
  否则方块会被拉成长方形（W2）。棋盘格、坐标图同理。
- `xlog: true` / `ylog: true` 把该轴换成**对数轴**（内部先取 `log10` 再线性映射，
  所有图元只写数据值，不用自己换算）。三条硬前提，违反即 E7：
  1. `xRange` / `yRange` 必须**全为正**（`log 0 = −∞`）；
  2. 该轴的 `ticks` **必须显式给**（自动刻度 `niceTicks` 按线性间距算，在对数轴上位置是错的）；
  3. 给了 `xticklabels` / `yticklabels` 就必须与 `ticks` **等长**。
  刻度文字建议直接给字符串（`fmtTick` 会把 `1e9` 写成「100000万」）：
  `axis(xticks=[1,1e3,1e6,1e9], xticklabels=["1 秒","10³ 秒","10⁶ 秒","10⁹ 秒"])`。
  注意 `ux/uy`（像素长度，用于 `card`/`node` 的 w/h）**仍是线性**的，对数轴上不要用它们定尺寸。

---

## 二、主题令牌（`vk.PAPER` / `vk.DARK`）

用令牌而不是硬编码色值，**换主题时整张图自动适配**：

| 令牌 | 用途 |
|---|---|
| `.accent` / `.accent2` | 主强调色 / 次强调色 |
| `.good` / `.warn` / `.bad` | 语义色：正确 / 提醒 / 错误 |
| `.text` / `.dim` / `.muted` | 正文 / 次要 / 更弱 |
| `.panel` / `.panelEdge` | 卡片底 / 卡片描边 |
| `.axis` / `.grid` | 坐标轴 / 网格线 |
| `PAPER.series` | 序列色数组（多条线/多个类目时按序取） |
| `PAPER.ramp` | 深浅渐变（层级/强度类） |

---

## 三、图元清单

每个图元都是一层。**通用字段**：`when`（显示条件，见第五节）。

### 坐标类

| geom | 必填 | 常用字段 | 用途 |
|---|---|---|---|
| `axis` | — | `xlab, ylab, xticks, yticks, xticklabels, yticklabels, xn, yn` | 坐标轴 + 刻度（刻度自动取"漂亮值"） |
| `grid` | — | `xticks, yticks, x, y` | 网格线（`x:false` 只画横线） |
| `line` | `fn` 或 `data` | `from_=[x0,x1], n` 采样数, `stroke, width, dash, area, fill, baseline` | 曲线 / 折线 / 带填充的区域图 |
| `bar` | `data` | `width, fill, fillBy, palette, baseline, orient:"h"` | 条形。`data:[{x,y,w?,base?,fill?,label?}]` |
| `point` | `data` | `r, fill` | 散点。`data:[{x,y,r?,fill?,label?}]` |

> `line` 的 `fn` 是**表达式字符串**，可用 `x` 作为自变量，例如 `"P*(1+r/100)^x"`。
> 表达式里的 `P`、`r` 必须在 `params`/`scalars` 里有定义，否则 E4。

### 结构类

| geom | 必填 | 常用字段 | 用途 |
|---|---|---|---|
| `card` | `data` | `fill, edge` | 流程卡片。`data` 用 `vk.card_item(x,y,w,h,label,sub,edge)` |
| `arrow` | `data, nodes` | `stroke, width` | 卡片之间的有向连线。`dir:"h"`(默认)/`"v"`/`"vu"` |
| `node` | `data` | `r, fill, edge, labelColor` | 圆形节点（树/图）。`data` 用 `vk.node_item(id,x,y,label)` |
| `edge` | `data` | `nodes, stroke, width, directed, showWeight, trim` | 节点间的边。`data:[{u,v,w?,label?,on?}]` |
| `region` | `x, y` | `fill, outline, stroke, width, dash, label` | 高亮区 / 嵌套框。`x=[x0,x1], y=[y0,y1]` |
| `text` | `x, y, text` | `align, size, color, dx, dy, weight, expr` | 文字。**支持 `\n` 换行**；`text` **默认原样显示**，要动态文本写 `expr=True` |
| `glyph` | `data` | `size, fill, fillBy, palette, edge, stroke, shape` | 小方块/小圆（位、格子图）。**需 `equalAspect`** |
| `matrix` | — | `values, rows, cols, cellW, cellH, origin, highlight, colHeaders, rowHeaders` | 网格 / DP 表 / 哈希桶 |
| `timeline` | `data, tRange` | `y, axis, palette` | 时间轴。`data:[{t,label,color?,side:"up"/"down"}]` |

### 算法类（步骤轨迹专用）

| geom | 必填 | 常用字段 | 用途 |
|---|---|---|---|
| `array` | `data` | `origin, step, barW, colorOf, pointers, baseline` | 数组条形图（排序/查找）。`pointers:{i:3, j:5}` |
| `linear` | `data` | `mode:"stack"/"queue"/"list", origin, y, cellW, cellH, highlight` | 栈 / 队列 / 链表 |

---

## 四、数据绑定：表达式规则

任何**图层字段**、`when`、`fn`、`readout.expr` 里的字符串，只要"看起来像表达式"就会被求值：

- **判定规则**：整串只含 `[空格 数字 字母 _ + - * / ( ) . ^ , % < > = ! ? : | &]` 才当表达式；
  含中文或其他字符则**原样保留**（所以 `"ℕ  自然数"` 这种标签是安全的）。
- **运算符**：`+ - * / ^ ( )`（`^` 自动转 `**`），比较 `> >= < <= ==`，逻辑 `&& ||`。
- **白名单函数**：`sqrt abs min max pow sign floor ceil round log log2 log10 exp sinh cosh`
- **常量**：`PI E`
- **可用变量**：`params` 的名字 ∪ `scalars` 的名字 ∪ 当前步的键 ∪ 内置 `x`（仅 line 的 fn）。
  **引用其它任何名字都是 E4**。

```
✅ "P*(1+r/100)^x"     ✅ "k >= 3"      ✅ "n/4"
❌ "P*(1+r)^x"  （r 若定义为百分数，这样写语义就错了）
❌ "stepIdx >= 2" （stepIdx 没定义 → E4）
```

### ⚠️ 文字默认不求值（重要）

`text` 图元的 `text` 字段**默认原样显示**，不参与表达式求值。因为数学标签里
`"1/2"`、`"-3"`、`"(a)"` 极其常见——一旦自动求值，`"1/2"` 会变成 `0.5`、`"(a)"` 会变成 `NaN`。

```python
vk.text(0.5, 1.0, "1/2")                   # ✅ 显示 "1/2"
vk.text(0.5, 1.0, "1/2", expr=True)        # ⚠️ 求值后显示 "0.5"
vk.text(0.3, 2.0, "F", expr=True)          # ✅ 动态：显示 scalars 里 F 的值
```

坐标 `x`/`y` **始终**会求值（这样可以用表达式按数据定位文字）。

---

## 五、条件与步骤

- `when`：字符串表达式，为真才绘制该层。最常用 `vk.when(k)` → `"k >= k"`。
  步骤字段会并入状态，所以 `steps=[{"k":1,...},{"k":2,...}]` 时 `when:"k >= 2"` 在第 2 步起可见。
- `steps`：**每步都要写 `note`**（读者要靠它知道这一步在讲什么），否则 W3。
- 常见的"逐步展开"写法：

```python
layers = []
for i, item in enumerate(items):
    layers.append(vk.card(when=vk.when(i + 1), data=[vk.card_item(...)]))
```
> ⚠️ 注意偏移量：**箭头通常要比左端卡片晚一步**（`when(i+2)`），别照抄卡片的 `i+1`。
> 这类"差一步"的错误不会报错，但会让读者在第 1 步就看到整条链。

---

## 六、参数与读数

```python
params=[{"name":"r", "label":"年化收益率", "min":1, "max":20, "step":0.5, "value":8, "unit":"%", "digits":1}],
scalars=[{"name":"F", "expr":"P*(1+r/100)^t"}],
readouts=[
    {"id":"F", "label":"复利终值", "type":"expr", "expr":"F", "int":True, "unit":"元", "highlight":True},
    {"id":"ok", "label":"是否值得", "type":"status", "expr":"F-Fs", "op":">", "rhs":0,
     "okText":"复利跑赢", "badText":"未跑赢"},
    {"id":"tx", "label":"备注", "type":"text", "value":"固定不变的说明"},
],
```

- `type:"expr"`：`digits` 小数位 / `int:true` 千分位整数 / `highlight:true` 放大成高亮胶囊
- `type:"status"`：状态灯，`op` 支持 `> >= < <= ==`
- `type:"text"`：纯文本，**不会被当表达式**

---

## 七、硬性约束（违反任一，校验器必报）

| 约束 | 违反后果 | 代码 |
|---|---|---|
| 图元名必须在清单内 | 该层被静默忽略 | E2 |
| 必填字段齐全 | 该层画不出来 | E3 |
| 表达式变量必须已定义 | 该层显示不出来（NaN） | E4 |
| `card`/`node`/`point`/`region` 坐标必须在 `view` 内 | 内容跑到画布外 | E5 |
| 文本不能超出画布 | 被裁掉 | E6 |
| 对数轴：范围/数据全为正、刻度显式、刻度文字等长 | 点画不出来或画在错位置 | E7 |
| 同水平带的文本不能横向重叠 | 叠字看不清 | W1 |
| 方块类图元要开 `equalAspect` | 方块变形 | W2 |
| 每步要有 `note` | 读者不知道在讲什么 | W3 |

### 六类**高频错误**与修法（都是我实际踩过的）

1. **标签堆叠**（最常见）——同心布局、并列卡片、时间轴密集处。
   → 标签**上下分层**（交替 y）或**改用阶梯式布局**（每层从同一角内缩，而不是同心）。
2. **文字出框**——长句 + 靠边。
   → 缩短 / 用 `\n` 折行 / 改 `align` / 放宽 `view`。
3. **卡片太窄导致文字溢出**——卡片宽 < 文字宽。
   → 缩短文字（细节留给正文）/ 加宽卡片 / 少放几列。
4. **坐标轴压住图元**——图元贴到 `xRange[0]` 或 `yRange[0]`。
   → 图元留出内边距，别贴着轴。
5. **差一步的 `when`**——第 1 步就看到全部。
   → 逐层核对偏移（卡片 `i+1`、箭头 `i+2`）。
6. **忘了 `equalAspect`**——方块变长方形、圆变椭圆。
   → `spec(..., equal_aspect=True)`。
7. **把数学标签写成了"像表达式"的字符串**——`"1/2"` 被求值成 `0.5`。
   → 文字默认不求值，正常情况不用管；**只有**你显式写了 `expr=True` 才会求值。
   反过来，如果你**想要**动态文本却忘了 `expr=True`，它会原样显示变量名。

---

## 八、把图放进书里

章节 JSON 的 `blocks` 里用 `figure` 块引用插图：

```json
{ "type": "figure", "id": "fig-crisis", "height": 250,
  "caption": "图注。可以含 $公式$。" }
```

- `id` 必须能在 `figures.py` 的 `FIGS` 里找到（否则页面报"缺少图定义"）。
- **`height` 要与校验时用的高度一致**——校验按 `height` 估算文本是否出框。
- **不需要**在这里写 `steps` 的数量：书页模板以**图定义为准**自动生成步骤控件。

其它常用块：`lead`（导语，首字下沉）、`p`、`h2`、`h3`、`quote`（`cite` 注出处）、
`note`、`warn`、`formula`（`tex`）、`list`、`steps`（`items:[{t,d}]`）、`table`（`headers, rows`）。

> 正文里可以写 `$行内公式$` 与 `$$display$$`（KaTeX）。

---

## 九、什么图适合表达什么（选型指引）

| 要表达 | 选 |
|---|---|
| 数量随时间变化 | `line`（+ `area`） |
| 分类比较 | `bar`（`orient:"h"` 适合长标签） |
| 流程 / 因果链 | `card` + `arrow`（左右或上下蛇形） |
| 包含 / 嵌套 | `region` **阶梯式**（不要同心） |
| 层级 / 逐步 | `card` 纵向堆叠，或 `stack` 条形 |
| 关系网络 | `node` + `edge` |
| 时间先后 | `timeline`（上下交替标注） |
| 二维状态表 | `matrix` |
| 逐步演算 | `array` / `linear` + `steps` |

**图不擅长**（别硬画）：否定与例外、条件分支的精确语义、价值判断、需要精确措辞的条文。
这些应交给正文，图只承担**结构与关系**。
