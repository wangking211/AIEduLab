# 数据格式参考（problem-schema）

与 `edu-physics-junior` / `edu-physics-senior` / `edu-function-derivative` 的 schema
同源（`lesson` / `steps` / `board` 三段），本文档重点列**本技能新增/有差异**的部分。
通用结构（param 滑块、readouts、constant 定值指示、legend 图例、bars 条、
scalars 逐帧标量）见 `../../edu-physics-junior/references/problem-schema.md`。

**本技能画板是"数学图形"**：`board.view` 提供世界坐标范围（xRange/yRange，y 向上），
核心是 `board.scene`（场景 kind + 场景字段）。三种场景：`seq` / `wave` / `tri`。

## 1. scene 通用规则

```jsonc
"scene": { "kind": "seq",            // 三种之一：seq/wave/tri
           "caption": "…画板标题…",   // 画板右上角说明
           "cur": "n",               // 数值字段：数字 或 含 param/scalars 名的表达式
           "limit": 1 }
```

- 所有数值字段按 `{p: 滑块值, <param名>: 滑块值, ...scalars}` 求值；字符串求值
  非有限数时保留原串（故 `kind`/`caption` 可安全写字面量，三元表达式也支持）。
- **数组字段的元素若是对象则原样透传**（如 `wave` 的 `multi` 曲线数组），
  对象内部的数值必须在 Python 侧算成数字，不能写表达式字符串。
- **世界坐标 y 向上**；数列/三角页 view 用 `[0,10]×[0,6.5]`，
  正弦页用 `[0,10]×[0,6.2]`（曲线围绕 y=3 上下 ±2.5）。
- `readouts` 类型：`expr`（求值显示，`highlight` 高亮）、`status`
  （`expr op rhs` → `okText` 绿 / `badText` 红，`op` ∈ `< <= > >= ==`，
  省略 op 时为 `>=`）。数值判断用 `<` 配小量（0.001）表示"恒成立"。
- `constant`：`{label}` 静态定值指示（KaTeX），如 "d ≡ 3"、"T ≡ 2π/3"。

## 2. 三种场景字段

### kind: `seq`（数列画板：上 Sₙ 折线 + 下 aₙ 柱状）
| 字段 | 含义 |
|---|---|
| `terms` | 通项数组 `[a_1, a_2, …, a_nmax]`（**数字数组**，由 kernel 在 Python 侧算好） |
| `partial` | 部分和数组 `[S_1, …, S_nmax]`（数字数组；可为空 `[]` 只画柱） |
| `cur` | 当前项数 n（**表达式**，通常是 param 名），决定高亮柱与竖直游标 |
| `limit` | 极限虚线值（可省略；如裂项和 → 1，粉虚线 + 标注） |

- 柱状图与折线各自按自身最大值缩放（两面板量纲可不同）。
- 高亮柱为深色 + 金边标签 `a_k=…`；当前 Sₙ 点金黄放大 + 标签。
- 顶部竖直金虚线标 `n = …`。

### kind: `wave`（正弦曲线：单曲线或多曲线对比）
| 字段 | 含义 |
|---|---|
| `A`/`omega`/`phi` | 单曲线 y = A·sin(ωx+φ) 的三参数（φ 用**弧度**） |
| `multi` | **对象数组** `[{A,omega,phi,color}, …]`，多曲线对比（恒等式页用）；对象内数值必须是数字 |
| `xmin`/`xmax` | x 采样范围（**弧度**；决定缩放与 π/2 刻度） |
| `cur` | 游标位置 x（**表达式**；度数 param 用 `th*PI/180` 转弧度） |
| `curLabel` | 游标标签名（如 `x` / `θ`，非表达式会原样显示） |
| `curDeg` | 游标角度制显示（表达式，如 `x*180/PI` 或 `th`） |
| `T` | 周期（弧度；画底部维度线标注 `T=…`） |

- 主曲线（`multi[0]` 或单曲线）画 ±A 水平虚线（值域上下界）。
- 多条曲线各给 `color`（hex 串），图例 legend 需与之一一对应。
- x 轴按 π/2 自动打刻度（0、π/2、π、3π/2、2π…）。

### kind: `tri`（SAS 三角形：两边固定，夹角 A 滑块驱动）
| 字段 | 含义 |
|---|---|
| `b`/`c` | 两边长（数字或表达式；题面固定值，如 2、3） |
| `Ad` | 夹角 A（**度**，通常直接是 param 名 `A`） |
| `area` | 面积表达式（右下角标注，如 `3*sin(A*PI/180)` = ½bc·sinA） |

- 顶点 A 放 (4,1)，AB 沿 +x 长 c，AC 按角 Ad 转 b 长——**自动适配 15°~165°** 不出界。
- 边 a = BC 由坐标算出并标注（金黄）；角 A 画红色弧 + 度数。
- 三边长度、B/C 角、面积放 `readouts`（用 `scalars` 先算 `aa` 再引用，避免重复长表达式）。

## 3. 读数与验证点设计

每题至少：**1 个高亮 expr 读数 + 1 个 status 状态灯**；有恒定/恒等关系的配
`constant`。数列题的状态灯写"递推/公差/公比恒成立"（`abs(差)<0.001`），
三角题写"A+B+C=180°"，恒等式题写"和 ≡ sinθ"（阈值 1e-6）。

## 4. 三入口归一

| 入口 | 处理 |
|---|---|
| 文字题 | 抽取已知/所求 → 匹配 `conventions.md` 配方 → kernel 求解 |
| 图片 | 视觉读图识别题面，回显确认后同上 |
| 随机 | `generate.py random [seed]`：随机选题型（8 种等概率） |
