# 数据格式参考（problem-schema）

与 `edu-analytic-geometry` 的 schema 同源（`lesson` / `steps` / `board` 三段），
本文档重点列**本技能新增/有差异**的部分。通用字段（view/conics/points/param/scalars/
rangeBar/constant/answerBand/trace/legend、line_* / point_on_conic / intersect_line_* /
midpoint / point_reflect / foot_perp / reflect / tangent_at / vector / polygon 等
derived 类型、coord/length/distance/dot/slope/slope_product/area_triangle/
distance_point_line/expr/status 等 readout 类型）见
`../edu-analytic-geometry/references/problem-schema.md`。

## 1. view 新增开关（初中几何默认隐藏坐标系）

```jsonc
"view": { "xRange": [-1.5, 15.5], "yRange": [-1.5, 13.5],
          "grid": false,   // 隐藏网格（默认 true）
          "axes": false }  // 隐藏坐标轴（默认 true）
```
`generate.py` 里用 `NO_AXES = {"grid": False, "axes": False}` 便捷构造。
纯几何图形（三角形、圆）通常不需要坐标系；轨迹/函数类可保留。

## 2. derived 新增类型

| type | 字段 | 产出 |
|---|---|---|
| `angle_bisector` | `name, a, vertex, b` | ∠avb 的角平分线（内角，过 vertex） |
| `perp_bisector` | `name, a, b` | 线段 ab 的中垂线 |
| `parallel_through` | `name, line, point` | 过点作已知直线的平行线 |
| `perp_through` | `name, line, point` | 过点作已知直线的垂线 |
| `rotate` | `name, of, center, deg`(数或`"@param"`) | 绕 center 旋转 deg°（逆时针） |
| `homothety` | `name, of, center, k`(数或表达式/`"@param"`) | 以 center 为位似中心缩放 k 倍（A 型相似滑块驱动） |
| `circle_from_center_pt` | `name, center, through` | 由圆心 + 圆上一点构造圆（内心用：圆心 I、过切点） |
| `circumcircle` | `name, a, b, c` | △abc 的外心点 `<name>_O` + 外接圆 |
| `angle_arc` | `a, vertex, b, r`(弧半径,默认0.3), `color`, `arcs`(条数,默认1), `label`, `labelR` | 角弧标注（1 条=∠1，2 条=圆心角等；同数弧=等角） |
| `right_angle_mark` | `a, vertex, b, s`(方框边长,默认0.22), `color` | 直角小方框符号 |
| `arc_mark` | `a, b, n`, `color` | 等长刻度（保留类型名；实际等长刻度写在 segment 上） |

`segment` 新增字段：
- `ticks`: 1/2/3 —— 线段中点处的短杠数（等长标记；两条线段 ticks 相同 ⇒ 等长）
- `arrow`: `">"` / `">>"` —— 平行箭头（两线段箭头数相同 ⇒ 平行）

## 3. readouts 新增类型

| type | 字段 | 显示 |
|---|---|---|
| `angle_deg` | `a, vertex, b`(点名) | ∠avb 的度数（0~180°，`°` 后缀） |
| `ratio` | `a:[p,q]`, `b:[r,s]` | \|PQ\| / \|RS\|（如 AD/AB） |
| `product` | `a:[p,q]`, `b:[r,s]`, `digits` | \|PQ\| · \|RS\|（圆幂 PA·PB 用；配 `constant` 跟踪） |

`constant`（定值指示器）在本技能大量使用：圆周角恒定、PA·PB 恒定、三比值恒等、
内切圆三距离恒等、外接圆三半径恒等——`of` 指向一个高亮 readout。

## 4. points 坐标与 kernel 同源

`points[*].xy` 必须来自 kernel 的精确值经 `float()` 转换（`generate.py` 的 `pt()` 帮手）。
构造点（切点、内心 I、外心 O、正方形顶点）同样先在 kernel 算出再放入 points；
正方形等填充图形的顶点用 `hidden: true` 只参与 polygon 不显示标签。

## 5. 三入口归一

| 入口 | 处理 |
|---|---|
| 文字题 | 抽取图形/已知/所求 → 匹配 `conventions.md` 配方 → kernel 求解 |
| 图片 | 视觉读图识别题面，回显确认后同上 |
| 随机 | `generate.py random [seed]`：随机选题型与规整参数（勾股数表、整数比） |
