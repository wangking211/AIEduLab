# reaction spec 与 data 数据格式

`build_*` 写一个 **reaction spec**，`reaction_kernel.assemble_data(spec)` 校验并装配成注入模板的
**data**。两种作者级别都汇流到同一份 data。

---

## 一、meta（必填）
```jsonc
"meta": {
  "title": "甲烷的燃烧",              // 标题
  "subtitle": "CH₄ + O₂ 的氧化放热…",  // 副标题（accent 色）
  "language": "zh-CN",               // "zh-CN" | "en"，决定 UI 文案与图例语言
  "category": "junior",              // junior(初中) | inorganic(高中无机) | organic(有机机理)
  "accent": "amber",                 // 强调色：amber/indigo/emerald/sky/violet/cyan/red/green/orange...
  "engine": "morph",                 // auto | morph | mechanism（auto：organic 或带 fragments → mechanism）
  "equation": "..."                  // 可选；不填则由配平自动生成 LaTeX（机理路径建议显式给）
}
```

## 二、conditions（反应条件 + 叠加层开关）
```jsonc
"conditions": {
  "text": "点燃",            // 箭头上方条件文字（点燃/通电/催化…）
  "under": "电解",           // 可选，箭头下方文字
  "reversible": true,        // 可逆反应 ⇌
  "exothermic": true,        // 放热（语义标注）
  "flame": true,             // 显示火焰叠加层（燃烧/强放热）
  "transitionGlow": true,    // 过渡态能量光（黄）
  "catalyst": { "label": "浓硫酸 (H⁺)", "formula": "H^+" }  // 显示催化剂开关；机理里催化剂为 fragment
}
```

## 三、A. 高层路径（species + atom_map）—— 推荐用于“原子打散重组”反应
```jsonc
"reactants": [ {"species":"CH4","count":1,"pos":[-4,0.2,0]}, {"species":"O2","count":2} ],
"products":  [ {"species":"CO2","count":1,"pos":[-2.7,1.1,0]}, {"species":"H2O","count":2} ],
// pos 可省略 → 自动居中布局；rot 可选（弧度，[rx,ry,rz]）
"atom_map": [
  ["CH4#1.C",  "CO2#1.Y"],          // 反应物原子引用 ↔ 产物原子引用（同一个原子的去向）
  ["O2#1.Oa",  "CO2#1.Xa"], ...
]
```
- **实例引用**：`SPECIES#k.slot`。同物种多份按出现顺序编号 `#1 #2`（如两个 O2 → `O2#1 O2#2`）。
- **atom_map 必须是反应物原子↔产物原子的双射**：每个反应物原子、每个产物原子各出现且仅出现一次，
  且配对两端元素相同。kernel 会严格校验并报错。
- **全局原子 id** 由 atom_map 顺序生成：元素 + 计数（`C1 H1 H2 … O1 …`）。
  叠加层（如 `electrons`）若要引用原子，用这些 id（顺序确定，可预知）。

### 各物种的 slot 名（atom_map 里用）
| 物种 | slot |
|---|---|
| 双原子 `H2 O2 N2 Cl2` | `Ha,Hb` / `Oa,Ob` / `Na,Nb` / `Cla,Clb` |
| `CO` | `C,O` |
| 线形 `CO2` | `Y`(中心C), `Xa,Xb`(两端O) |
| 弯曲 `H2O` | `A`(O), `Ha,Hb` |
| 四面体 `CH4` | `C, H1,H2,H3,H4` |
| 三角锥 `NH3` | `A`(N), `H1,H2,H3` |
| 单原子 `Na C Fe Mg Zn Cu Ag` | `X` |
| 离子对 `NaCl AgCl` | `Na,Cl` / `Ag,Cl` |
| 一元酸 `HCl` | `H,Cl` |
| 一元碱 `NaOH` | `Na, O1, H1` |
| 二元碱 `Ca(OH)₂ Cu(OH)₂` | `M, O1,H1, O2,H2` |
| 硫酸 `H₂SO₄` | `A`(S), `O1..O4`, `H1,H2` |
| 硝酸盐 `AgNO₃` | `Ag, A`(N), `O1..O3` |
| 硝酸盐 `Cu(NO₃)₂` | `A1,O1_1..O1_3, A2,O2_1..O2_3, Cu` |
| 碳酸盐 `CaCO₃` | `Ca, A`(C), `O1..O3` |
| 碳酸盐 `Na₂CO₃` | `Na1,Na2, A`(C), `O1..O3` |
| 硫酸盐 `CuSO₄ ZnSO₄ FeSO₄` | `M, A`(S), `O1..O4` |
| 硫酸盐 `Na₂SO₄` | `Na1,Na2, A`(S), `O1..O4` |
| 氯化物 `CaCl₂` | `Ca, X1,X2` |
| 氯化物 `FeCl₃` | `Fe, X1,X2,X3` |
| 氧化物 `Fe₂O₃`（铁锈） | `Fe1,Fe2, O1,O2,O3` |

（新物种在 `lib/molecules.py` 定义其 slot；`python3 lib/molecules.py` 可打印各物种原子。）

## 三、B. 低层路径（显式 atoms + bonds）—— 推荐用于有机机理
直接给全局原子与键，kernel 只校验守恒/键差，不做实例展开：
```jsonc
"atoms": [
  {"id":"C1","el":"C","frag":"acetyl","flocal":[0,0.2,0],
   "start":[...world...],"end":[...world...],"rmol":"乙酸#1","pmol":"乙酸乙酯#1"}, ...
],
"bonds_before": [ {"a":"C1","b":"O1","order":2}, {"a":"C1","b":"O2","order":1}, ... ],
"bonds_after":  [ {"a":"C1","b":"O3","order":1}, {"a":"O2","b":"H10","order":1}, ... ],
"fragments": [
  {"id":"acetyl",   "K0":{"pos":[-4.5,0.5,0],"rot":[0,0,0]}, "K1":{...}, "K2":{...}},
  {"id":"catalyst", "catalyst":true, "K0":{...},"K1":{...},"K2":{...}}
],
"labels": [ {"id":"r-acid","text":"乙酸 (CH₃COOH)","color":"red","phase":"reactant","atoms":["C1","O1",...]}, ... ]
```
- **frag/flocal**：mechanism 引擎用——原子归属片段 `frag`，`flocal` 是片段内局部坐标；
  运行时由片段关键帧 `K0/K1/K2`（pos+rot 弧度）整体变换。
- **start/end**：morph 回退与标签用（=K0/K2 作用于 flocal，可用 `reaction_kernel._apply` 算）。
- **键序 order**：`1/2/3`；`"ionic"` 离子键（细虚弱化显示）。
- **catalyst 片段**：`catalyst:true` → 青色质子辉光 + 开关；其原子**不计入原子守恒计数**（催化剂再生）。

## 四、steps（分步讲解，建议 3 步对应三阶段）
```jsonc
"steps": [
  {"title":"反应物混合","html":"<span class='text-red-600 font-semibold'>…</span> 富文本说明"},
  {"title":"点燃燃烧","html":"…断键…"},
  {"title":"生成产物","html":"…原子守恒…"}
]
```
阶段边界固定：进度 `[0,0.4)` 接近 → `[0.4,0.7]` 过渡（断/成键高亮、抖动、火焰/能量峰）→ `(0.7,1]` 分离。
步进器按 3 步映射（>3 步会均分高亮，但分子动画仍按上述三阶段）。

> 🎨 **配色注意（重要）**：讲解面板是**亮色底**（`bg-slate-50`，默认文字 `text-slate-700`）。
> 富文本里着色只用**深色系 `-600/-700`**（`text-red-600`、`text-sky-600`、`text-emerald-600`、`text-slate-700`…）；
> **不要用 `-200/-300/-400`**（在浅底上几乎看不见）。虚线下划线 `border-b border-dashed border-rose-500` 可用。

## 五、可选叠加层
```jsonc
"electrons": [ {"from":"Na1","to":"Cl1","count":1,"label":"e⁻"} ],   // 氧化还原电子转移（全局 id）
"energy":    { "activation":0.5, "deltaH":-0.75,                     // 能量-反应进程曲线（0~1 相对量）
               "reactantLabel":"CH₄+O₂", "productLabel":"CO₂+H₂O" }  // deltaH<0 放热、>0 吸热
```

### 5.1 `activity` —— 金属活动性顺序条（置换反应题用）
在方程下方渲染 K→Au 顺序条，高亮参与金属并给出 ✓/✗ 结论。用 kernel 生成，不要手写：
```python
"activity": K.activity_strip("Zn", "H"),     # 金属 + 酸（省略第二参默认 "H"）
"activity": K.activity_strip("Fe", "Cu"),    # 金属 + 盐溶液
```
产物 data（`K.activity_strip` 返回值）：
```jsonc
{ "series": ["K","Ca","Na",…,"Au"],          // 完整活动性顺序
  "left": "Zn", "right": "H",                // 参与判断的两个符号
  "highlight": ["Zn","H"],                   // 顺序条中高亮的 chip
  "can": true,                               // 能否置换（含 K/Ca/Na 先与水反应的例外）
  "note": "✓ Zn 排在 (H) 之前，能与稀酸反应放出氢气",   // 模板自动加 ✓/✕ 前缀并按结果着色
  "rankLeft": 9, "rankRight": 10 }
```
判据在 kernel `activity_judge`：排在前可置换；`K/Ca/Na` 例外（入盐溶液先与水剧烈反应，`can=False`
并给出说明）；与 H 比较时文案自动切换为“氢前/氢后金属、能否与稀酸反应放出氢气”。

### 5.2 `solution` —— 溶液计算控制台（溶质质量分数/配制/稀释题用）
渲染在守恒计数面板之下：参数滑块 → 实时读数 + 状态灯 + 定值指示。数值一律由 kernel 算出后
拼进 `expr`（sympy 精确，别心算）：
```python
mf = K.mass_fraction(20, 80)      # 溶质/溶剂 → {solute, solvent, solution, fraction, percent}
pr = K.prepare_solution(100, 16)  # 配制 m液 g 的 w 溶液 → {solute, solvent, …}
dl = K.dilution(50, 20, 10)       # 稀释：m₁、w₁(可写 20)、w₂(可写 10) → {m2, water, solute, …}
sf = K.saturation_fraction(36)    # 溶解度 S g/100g 水 → {S, solution, fraction, percent}
```
```jsonc
"solution": {
  "label": "溶液组成计算台",            // 面板标题
  "note":  "拖动滑块实时重算",          // 副提示
  "params": [                          // 1~2 个滑块（name 是 expr 里的变量名）
    {"name":"ms", "label":"溶质 NaCl 质量 m质（溶剂固定 80 g）",
     "min":0, "max":60, "step":1, "value":20, "unit":"g", "digits":0}
  ],
  "readouts": [                        // 读数行（id 唯一）
    {"id":"msol", "label":"溶液质量 m液 = m质 + m剂",
     "expr":"ms + 80", "unit":"g", "digits":0},
    {"id":"w", "label":"溶质质量分数 ω = m质 / m液 × 100%",
     "expr":"100 * ms / (ms + 80)", "unit":"%", "digits":1, "highlight":true,
     "status": {"expr":"abs(100 * ms / (ms + 80) - 20)", "op":"<=", "rhs":0.5,
                "okText":"恰为 20%（达标）", "badText":"偏离 20%"}}   // 状态灯（可选）
  ],
  "constant": {"label":"本题定值：溶剂质量 m剂 ≡", "expr":"80", "unit":"g", "digits":0}
}
```
- `expr` 是受限表达式：只能引用 `params[].name` 与字面量，可用 `abs min max sqrt pow round floor
  ceil PI`（模板 `evalExpr` 求值）；`status.rhs` 也可写成表达式字符串。
- `status.op` ∈ `> >= < <= ==`；浮点比较带 1e-9 容差。
- **`constant.expr` 必须与滑块无关**（真正的不变量，如稀释问题的 `m₁w₁`、配制问题里固定的 `m剂`）——
  随滑块变化的量放 `readouts`，不要标成“定值”。
- 缺省（不写 `activity`/`solution` 字段）对应面板整块隐藏，不影响其它页面。

## 六、assemble_data 产出的 data（注入模板）
`{ meta, conditions, atoms[{id,el,color,radius,start,end,frag?,flocal?,rmol,pmol}],
   bonds{before,after,broken,formed,kept}, labels[], elementCounts{}, legend[],
   steps[], fragments[], energy, electrons[], activity?, solution?, ui{} }`
模板读 `__REACTION_DATA__` 数据岛即渲染；`render_html(data, out)` 负责把 data 注入模板。
`activity`/`solution` 由 kernel 原样透传（缺省 `null` → 对应面板隐藏）。
