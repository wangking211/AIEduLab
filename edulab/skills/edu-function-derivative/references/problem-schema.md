# 数据格式参考（problem-schema）

与 `edu-plane-geometry` / `edu-analytic-geometry` 的 schema 同源（`lesson` / `steps` /
`board` 三段），本文档重点列**本技能新增/有差异**的部分。通用字段（view/conics/points/
param/scalars/rangeBar/constant/answerBand/trace/legend、line_* / point_on_conic /
intersect_line_* / midpoint / point_reflect / foot_perp / reflect / tangent_at /
vector / polygon / segment(ticks,arrow) / angle_arc / right_angle_mark 等 derived、
coord/length/distance/dot/slope/slope_product/area_triangle/distance_point_line/
angle_deg/ratio/product/expr/status 等 readout）见
`../edu-plane-geometry/references/problem-schema.md`。

## 1. conics 新增 kind: `function`

函数曲线 y=f(x)，由字符串表达式逐点采样（视窗 xRange 上 480 采样点，遇
NaN/±Infinity 或 |y|>1e6 自动断开成分段折线，定义域外如 ln x、1/x 不绘制）。

```jsonc
{ "name": "f", "kind": "function",
  "expr": "pow(a, x)",       // JS 表达式（变量 x 必用；可用 param 名、scalars 名、
                             //   + - * / ^、sqrt/pow/abs/log/exp/sin/cos/min/max/PI）
  "dexpr": "pow(a, x)*log(a)", // 导函数表达式（可选；给了才能用 tangent_function / fn_slope / fn_status）
  "color": "curve", "label": "$y=a^x$", "dashed": false, "legend": false }
```

- `expr`/`dexpr` 用 `fn_kernel.js(expr)` 生成（sympy jscode 去掉 `Math.` 前缀），
  不要手写——保证与 kernel 的 `tex()` 讲解同源。
- 参数依赖：表达式里写参数变量名（如底数滑块写 `a`），每帧按 env 重采样，
  **曲线随滑块实时变形**（exp_family 范例）。
- `fn_conic(name, expr, dexpr, color, label)` 便捷帮手见 `scripts/generate.py`。

## 2. derived 新增类型（函数曲线专用）

| type | 字段 | 产出 |
|---|---|---|
| `point_on_function` | `name, conic, x`(数/表达式/`"@param"`) | 曲线上点 (x, f(x))；x 超出定义域时点隐藏 |
| `tangent_function` | `name, conic, x`, `color`, `dashed` | 曲线在 x 处的切线（需 conic 有 `dexpr`） |
| `secant_function` | `name, conic, x1, x2`, `color`, `dashed` | 过 (x1,f(x1))、(x2,f(x2)) 的割线 |
| `root_on_function` | `name, conic, a, b`, `color` | [a,b] 上的零点（端点须异号，二分 80 轮），落 x 轴 |
| `area_fill` | `conic, a, b`, `color` | 曲线与 x 轴在 [a,b] 间的阴影（零点符号示意） |
| `intersect_line_function` | `name[], line, conic, colors[]` | 直线与函数曲线的数值交点（细分+二分） |

注意：`derived` 按数组顺序逐条构建，**被引用的名字必须先定义**（如先有 `Yaxis`
直线才能 `intersect_line_line` 求切线与 y 轴交点）。`line_through_point_dir` 的
`point` 是**点名**，原点等先在 `points` 里放静态点。

## 3. readouts 新增类型

| type | 字段 | 显示 |
|---|---|---|
| `fn_value` | `conic`, `x`(数/表达式/`"@param"`), `digits` | 曲线在 x 处的函数值 f(x) |
| `fn_slope` | `conic`, `x`, `digits` | 曲线在 x 处的导数 f'(x)（无 dexpr 或不可导显示 —） |
| `fn_status` | `conic`, `x`, `posText`, `negText`, `zeroText` | f'(x) 符号 → 绿"递增"/红"递减"/橙"驻点" |

表达式类 readout（`expr`/`status`）可用参数变量名与 MATHENV 白名单函数；
`status` 的 `op` ∈ `< <= > >= ==`，配 `okText`/`badText` 做状态指示灯
（如"割线≈切线？"、"x=0 可导吗"、"零点在 m 的哪侧"）。

## 4. constant（定值指示器）

`{"of": "<readoutId>", "label": "$...$"}` —— 跟踪一个高亮读数恒定，本技能用于：
- 奇偶性：`f(t)+f(-t) ≡ 0`（parity_odd）
- 指数定点：`a^0 ≡ 1`（exp_family）

## 5. param（滑块）

`{name, label, min, max, step, value, unit, standard, ticks[]}`：
- `name` 是表达式变量名（合法 JS 标识符），如 `x0`/`h`/`t`/`m`/`a`；
  读数与 derived 里用 `"@param"` 或直接写该变量名。
- `standard` = 题设值（对应"1 (题设)"刻度），`value` = 初值（通常取 standard）。

## 6. 三入口归一

| 入口 | 处理 |
|---|---|
| 文字题 | 抽取函数/所求 → 匹配 `conventions.md` 配方 → kernel 求解 |
| 图片 | 视觉读图识别题面，回显确认后同上 |
| 随机 | `generate.py random [seed]`：随机选题型与规整参数 |
