# 数据格式参考（problem-schema）

与 `edu-function-derivative` / `edu-plane-geometry` 的 schema 同源（`lesson` / `steps` /
`board` 三段），本文档重点列**本技能新增/有差异**的部分。通用结构（param 滑块、
readouts、constant 定值指示、legend 图例、scalars 逐帧标量）见
`../edu-function-derivative/references/problem-schema.md`。

**本技能画板是"物理场景"而非坐标曲线**：`board.view` 只提供世界坐标范围
（xRange/yRange，y 向上），核心是 `board.scene`（场景 kind + 场景字段）。

## 1. scene 通用规则

```jsonc
"scene": { "kind": "lever",          // 五种之一：lever/pressure/buoyancy/pulley/circuit
           "caption": "…画板标题…",   // 画板右上角说明
           "F": "F",                  // 数值字段：数字 或 含 param/scalars 名的表达式
           "d1": "min(2.6, 0.9+L1*1.1)" }
```

- 所有数值字段按 `{p: 滑块值, <param名>: 滑块值, ...scalars}` 求值；字符串求值
  非有限数时保留原串（故 `kind`/`layout`/`caption` 可安全写字面量）。
- `scalars`：`[{name, expr}]` 逐条求值进 env，供后续场景字段与 readouts 引用
  （如 `{"name":"F","expr":"(400+100)/2"}`）。
- `readouts` 类型：`expr`（求值显示，`highlight` 高亮）、`status`
  （`expr op rhs` → `okText` 绿 / `badText` 红，`op` ∈ `< <= > >= ==`）。
- `bars`：`{label, a:{label,expr}, b:{label,expr}}` 双色能量条（宽度按占比，
  内显数值）。用于滑轮的有用功/额外功。
- `constant`：`{label}` 静态定值指示（KaTeX），如 "η ≡ 80%"。

## 2. 五种场景字段

### kind: `lever`（杠杆）
| 字段 | 含义 |
|---|---|
| `pivot` | `[x,y]` 支点位置（原始数组，不求值） |
| `beamLen` | 杠杆总长（绘图用） |
| `tilt` | 倾角（度，可为表达式；由失衡量驱动，如 `min(max((F1*L1-F2*L2)*0.35,-10),10)`） |
| `L1, L2` | 真实力臂（显示在标注里） |
| `d1, d2` | **绘图臂长**（真实 L2 常很小如 0.06m，画图用放大的示意长度） |
| `F1, F2` | 动力/阻力（牛） |
| `fs1, fs2` | 箭头标度：力(N)×fs = 世界单位长度（如 24N×0.045≈1.08） |

### kind: `pressure`（固体压强，海绵下陷）
| 字段 | 含义 |
|---|---|
| `F` | 压力（表达式） |
| `sink` | 下陷深度（世界单位；= Pa×0.001cm×0.08 世界/cm，即 `F/S*0.001*0.08`） |
| `k` | 换算标度（世界单位/cm，标注 `Δ=sink/k` 用） |
| `boxW, boxH, boxLabel` | 方块尺寸与标签 |

### kind: `buoyancy`（浮力，弹簧测力计 + 容器）
| 字段 | 含义 |
|---|---|
| `liquidY` | 液面高度（世界 y） |
| `objW, objH` | 物体宽高 |
| `objTop` | 物体顶面 y（表达式，随滑块下沉；浸没部分自动加深色） |
| `G, F_buoy, F_scale` | 重力/浮力/拉力（表达式，驱动三支箭头长度） |
| `fScale` | 力→箭头长度标度 |

### kind: `pulley`（一动一定滑轮组）
| 字段 | 含义 |
|---|---|
| `my` | 动滑轮中心 y（表达式，随提升高度上升） |
| `myBase` | 初始高度（`h=0` 标注用） |
| `handY` | 绳端（手）y（表达式，随 s=nh 下移） |
| `n` | 承担绳段数（显示 `n=…`） |
| `G, F` | 物重/拉力（驱动箭头） |
| `fScale` | 力→箭头标度（G=400N 时取 0.0033） |

### kind: `circuit`（电路图，含电流流动点动画）
| 字段 | 含义 |
|---|---|
| `layout` | `"single"` 单电阻 / `"series"` 串联 / `"parallel"` 并联 |
| `R1, R2` | 电阻值（Ω，元件标签实时显示） |
| `I, I1, I2` | 电流（表达式；流动点速度 = I×`kflow`，点密度 ∝ 弧长） |
| `kflow` | 电流→流速标度（一般 1.6~2.0） |

电路布局固定在世界坐标（左电池+开关、上电阻、右电流表、R 两端电压表），
并联时上下两支路（L₁/L₂），画板只读字段不做布局计算。

## 3. 电流点动画

`flowDots(path, speed, nDots)` 沿折线按弧长布点，`animT`（rAF 时钟）推进。
`speed=0` 则静止；标签页隐藏时浏览器会暂停 rAF（正常现象，聚焦即恢复）。
每条 `flows` 路径带自己的 `I`——并联时支路流速正比于支路电流，直观显示分流。

## 4. 三入口归一

| 入口 | 处理 |
|---|---|
| 文字题 | 抽取已知/所求/单位 → 匹配 `conventions.md` 配方 → kernel 求解 |
| 图片 | 视觉读图识别题面，回显确认后同上 |
| 随机 | `generate.py random [seed]`：随机选题型（8 种等概率） |
