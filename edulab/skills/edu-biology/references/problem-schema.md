# 生物 lesson 数据格式

本技能有**两套模板**，对应两种 data 结构：

| 模板 | 数据岛 token | 用于 | 由谁产出 |
|---|---|---|---|
| `template/board.html` | `__LESSON_DATA__` | 遗传棋盘格 / 能量金字塔 / 种群曲线 / 生理流程图 | `build_*()` 直接返回 lesson dict |
| `template/cell.html` | `__CELL_DATA__` | 细胞结构 3D（动物 / 植物 / 原核） | `cell_library.build_payload(kind)` |

---

## 一、board 模板的 lesson dict

```jsonc
{
  "lesson": {
    "title":    "基因的分离定律：Aa × Aa",   // 左栏标题
    "subtitle": "一对相对性状的杂交实验",      // 左栏副标题（灰色小字）
    "problem":  "<p>…</p>"                   // 左栏题面 HTML，可内含 $…$ / $$…$$ KaTeX
  },
  "board": {
    "scene":    { … },          // 画板场景（见下，必含 kind）
    "view":     {"xRange":[0,4], "yRange":[0,4]},   // 静态兜底视图；scene 里的 xRange/yRange 会覆盖它
    "params":   [ … ],          // 滑块
    "scalars":  [ … ],          // 由滑块派生的中间量（表达式字符串）
    "readouts": [ … ],          // 读数条
    "constant": {"label": "…"}, // 可选：底部"定值指示"（必须与滑块无关！）
    "legend":   [ {"color":"#0d9488","text":"…"} ]
  },
  "steps": [ {"title":"…","content":"<p>…</p>"} ]   // 中栏分步解析，content 可含 KaTeX
}
```

### 表达式求值（关键约定）

滑块值实时变化，所以**所有随滑块变化的量都写成表达式字符串**，由模板在浏览器端求值：

```jsonc
"params":   [ {"name":"eff","label":"能量传递效率","min":5,"max":30,"step":1,"value":10,"unit":"%","digits":0} ],
"scalars":  [ {"name":"L2","expr":"10000*eff/100"} ],          // 可用 PARAMS 与已定义的 scalar
"readouts": [ {"id":"L2","label":"初级消费者","type":"expr","expr":"L2","int":true,"unit":" kJ"} ]
```

- 可用运算符：`+ - * / ^ ( )`（`^` 会被替换成 `**`）；白名单函数：`sqrt abs min max pow sign floor ceil round log log2 log10 exp sinh cosh`，常量 `PI E`。
- **scalars 按数组顺序求值**，后面的可以引用前面的。
- 表达式里**不能出现字符串拼接**；中文文本直接写死在 label 里。

### readouts 三种类型

```jsonc
{"id":"a","label":"…","type":"expr","expr":"L2","digits":2,"unit":" kJ","int":false,"money":false,"color":"#dc2626","highlight":true}
{"id":"b","label":"…","type":"status","expr":"eff","op":"<=","rhs":20,"okText":"符合规律","badText":"超出自然范围"}
{"id":"c","label":"…","type":"text","value":"肺循环 + 体循环，同时进行"}     // value 是纯文本
```

- `type:"expr"`：`digits` 小数位；`int:true` 千分位整数；`highlight:true` 会放大成高亮胶囊。
- `type:"status"`：状态灯，满足条件显绿 `okText`、否则显红 `badText`。`op` 支持 `> >= < <= ==`。
- `type:"text"`：**纯文本**。注意 `value` 里带中文/冒号时不会被当表达式（模板已做保护）。

> **定值指示 vs 读数**：`constant.label` 放**与滑块无关**的真不变量（如「两对基因自由组合 → 9:3:3:1」、
> 「儿子的 X 只能来自母亲」）；随滑块变的量一律放 `readouts`，不要写进 `constant`。

---

## 二、scene 场景（board 模板）

`scene` 里除 `kind`/`caption` 外的字段都会按表达式求值并注入画板。可声明 `xRange`/`yRange` 覆盖视图范围；
`equalAspect: true` 让 x/y 等比例（Punnett 棋盘格必须开，否则格子会被拉成长方形）。

### 1. `punnett` — 遗传棋盘格
```jsonc
"scene": {
  "kind":"punnett", "equalAspect":true,
  "xRange":[0.15,5.5], "yRange":[-0.35,5.6],
  "rowGametes":["AB","Ab","aB","ab"],      // 行配子（来自父本）
  "colGametes":["AB","Ab","aB","ab"],      // 列配子（来自母本）
  "cells":[["AABB","AABb",…], …],          // 二维网格，每格一个基因型字符串
  "count":{"AABB":1,"AABb":2,…},           // 每种基因型出现份数（格子重复出现时角标 ×n）
  "phenoOf":{"AABB":"A_B_", …},            // 基因型 → 表现型标签（用于图例/说明）
  "phenoKey":{"AABB":"dom", …},            // 基因型 → 配色键
  "phenoOrder":[["A_B_",9],["A_bb",3],…],  // 底部比例条：表现型 + 份数
  "phenoKeyAgg":{"A_B_":"dom", …},         // 表现型 → 配色键
  "phenoRatioText":"9 : 3 : 3 : 1",
  "footer":"基因型比 1:2:1:2:4:2:1:2:1"
}
```
**配色键**对应模板调色板：`dom`(青) / `het`(琥珀) / `mix`(紫) / `rec`(玫红) / `good` / `bad`。

> 建议用 `bio_kernel.cross_summary(父, 母)` 生成这些字段，再用 `generate._punnett_scene()` 组装，
> 不要手工拼（比例、配色、通配匹配都易错）。

### 2. `pyramid` — 能量金字塔
```jsonc
"scene": {
  "kind":"pyramid", "captions":"能量金字塔",
  "effPct":"eff", "effFrac":"eff/100",       // 传递效率（百分数 / 小数）
  "labels":["生产者（草）","初级消费者（兔）",…],
  "energyExprs":["L1","L2","L3","L4"],       // 各营养级能量（表达式，随滑块变化）
  "xRange":[0,10], "yRange":[0,6.4],
  "footer":"能量沿营养级逐级递减"
}
```
i=0 画在最下方（生产者），条形宽度 ∝ 能量；名称在左、数值在右，窄层也不会重叠。

### 3. `population` — 种群增长曲线
```jsonc
"scene": {
  "kind":"population",
  "n0":"n0","lam":"lam","K":"Kk","r":"r/100",   // 初始量 / 每代倍数 / 环境容纳量 / 内禀增长率
  "tMax":"tMax","yMax":"Kk*1.25",
  "showJ":true,"showS":true,
  "xRange":[0,20],"yRange":[0,2000],
  "footer":"J 型：资源无限，指数增长　·　S 型：资源有限，趋近 K"
}
```
> `yMax` 建议取 `K*1.25`：J 型会**冲出图外**（这正是"无限增长不可能"的直观表现），
> 模板会在越界处标出「↑ J 型冲出图外」。若按 J 型的终值定 yMax，S 型会被压成一条贴底直线。

### 4. `flow` — 生理过程流程图
```jsonc
"scene": {
  "kind":"flow",
  "xRange":[0,9],"yRange":[2.15,6.0],
  "nodes":[
    {"id":"blood","label":"血液","sub":"入球小动脉","x":0.2,"y":4.6,"w":2.2,"h":0.95,"color":"#7f1d1d"},
    {"id":"filtrate","label":"原尿","sub":"molFilt","subUnit":" L/天","x":6.0,"y":4.6,"w":2.3,"h":0.95}
  ],
  "edges":[
    {"from":"blood","to":"glomerulus","label":"滤过"},
    {"from":"filtrate","to":"tubule","dir":"v","label":"流经"}     // dir: h(默认) | v(向下) | vu(向上)
  ],
  "activeNodes":["blood","glomerulus","filtrate","tubule","urine"],  // 高亮节点
  "activeEdges":["blood>glomerulus", …],
  "footer":"…"
}
```
- 节点 `x/y` 是**世界坐标**，`y` 为**底边**；`w/h` 为世界单位尺寸。
- `sub` 可以是**表达式字符串**（随滑块变化，如原尿量）；`subUnit` 是单位后缀。
- `dir:"v"` 表示 a 在上、b 在下（竖直向下箭头）；`dir:"vu"` 反向。用于两行循环（如血液循环）。

---

## 三、cell 模板的 data（细胞 3D）

由 `cell_library.build_payload(kind)` 产出，`kind ∈ {animal, plant, prokaryotic}`：

```jsonc
{
  "kind":"animal",
  "title":"动物细胞的结构",          // generate.build_*_cell 追加
  "subtitle":"…",
  "steps":["整体观察","细胞核","线粒体","内质网 / 高尔基体","中心体"],
  "highlight":[ [], ["nucleus","nucleolus"], ["mito1","mito2"], … ],  // 每步高亮的细胞器 id
  "views":[ {"pos":[0,1.5,11],"target":[0,0,0],"label":"整体观察"}, … ],
  "boundary":[ {"geom":"sphere","size":4.0,"color":"#f2c4ce","opacity":0.14,"label":"细胞膜"}, … ],
  "organelles":[
    {"id":"nucleus","label":"细胞核","geom":"lobe","pos":[-0.6,0.5,0.2],"size":1.35,
     "color":"#8e6bb5","detail":"遗传信息库…","steps":[2]}
  ],
  "compare": { "headers":[…], "rows":[[…],…] }    // 三种细胞对比表
}
```

`geom` 取值（`template/cell.html` 的 `buildOrganelle` 支持）：

| geom | 用途 | size 含义 |
|---|---|---|
| `sphere` | 核仁、核糖体、溶酶体 | 半径 |
| `ellipsoid` | 一般椭球 | [rx, ry] |
| `capsule` | 线粒体（含内部嵴） | [rx, ry] |
| `grana` | 叶绿体（含基粒圆盘堆） | [rx, ry] |
| `disc_stack` | 高尔基体（多层扁囊） | [半径, 厚度] |
| `tube_bundle` | 内质网（几条弯曲管道） | [长度, 管径] |
| `lobe` | 细胞核（核膜 + 核质） | 半径 |
| `centriole` | 中心体（两两垂直的短管束） | 半径 |
| `dna_loop` | 拟核（环状 DNA） | [主半径, 细半径] |
| `rod` | 鞭毛 | [长度, 半径] |

> **边界渲染**：`boundary` 条目由模板渲染成「淡淡的内壁（BackSide + 无光照）+ 稀疏线框」。
> `opacity < 0.03` 的层会被跳过（不再单独画壳），用于避免多层叠加把画面糊成灰色。
> 注意线框段数刻意压低（球 16×10、盒 12 条棱），**不要**在这里改回高分段——会糊屏。

---

## 四、entry point

```bash
python scripts/generate.py list                 # 列出全部题型
python scripts/generate.py monohybrid out.html  # 生成单页
python scripts/generate.py all ./output         # 生成全部 + index
python scripts/generate.py random out.html      # 随机出题（遗传/生态/代谢）
```
