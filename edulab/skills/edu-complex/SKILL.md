---
name: edu-complex
description: >-
  把一道复数题解成一个自包含的交互教学网页：左栏题面 + 动态控制台
  （一个可变参数滑块驱动实时重算的量 + 状态灯 + 定值指示器），中栏 KaTeX 分步解析，
  右栏 2D Canvas 复平面画板（向量加减的平行四边形、共轭的镜像与 |z| 圆、
  乘法的旋转+伸缩与辐角弧、单位圆上的 n 次单位根、共轭复根对、轨迹圆）。
  支持三入口——给定文字题、随机出题、上传题目图片识别后解题。覆盖复数的加减法、
  共轭与模、乘法的几何意义、三角形式与棣莫弗定理、n 次单位根、
  一元二次方程的复根、几何轨迹等题型，统一由 sympy **精确**内核驱动
  （含根式化简：√3 保持为 √3，不会变成 1.7320508）。
  其它 agent 也可调用本技能生成此类网页。形态与 edu-vector 平行（复用 seq-phys
  模板家族，并新增 cplane_add / cplane_mod / cplane_rot / cplane_pow / unitroots /
  qroots / locus 七种场景）。触发词：复数, 虚数, 虚数单位, i 的幂, 复平面,
  高斯平面, 实部, 虚部, 共轭, 共轭复数, 模, 辐角, 三角形式, 棣莫弗, 棣莫弗定理,
  单位根, n 次方根, 一元二次方程, 复根, 判别式, 韦达定理, 几何轨迹, 复数的几何意义,
  复数的乘法, 解这道复数题, 随机出一道复数题, 这张图里的复数题;
  complex numbers, imaginary unit, complex plane, real part, imaginary part,
  conjugate, modulus, argument, polar form, De Moivre's theorem, roots of unity,
  complex roots of quadratic, locus, geometric meaning of multiplication,
  interactive complex numbers solution page.
---

# 复数交互教学网页 (edu-complex)

把一道复数题解成**自包含的交互教学网页**：三入口（文字 / 图片 / 随机），
sympy 精确内核驱动，2D 复平面画板 + KaTeX 分步解析。

## 与相邻技能的边界（先看清再选技能）

| 技能 | 管什么 | 判据 |
| --- | --- | --- |
| `edu-vector` | **平面向量**（数量积、投影、共线、定比分点） | 题目里是「向量」而不是「复数」 |
| `edu-analytic-geometry` | 圆锥曲线（椭圆/双曲线/抛物线） | 题目要算弦长、定点、离心率 |
| **本技能** | **复数**：代数运算、复平面、三角形式、单位根、复根、轨迹 | 题目里出现 $i$、$z$、$\\bar z$、$|z|$、$\\arg$ |

**判据**：题目里出现 $i$ 或 $z$ 且问「模/辐角/共轭/复根/轨迹」——用本技能；
`edu-vector` 的 SKILL.md 里明确写了「复数不覆盖」，现在由本技能接管。

## 依赖（重要）

计算核心 `lib/complex_kernel.py` 依赖 **sympy**（用 `sp.I` 做精确复数运算）。运行前确认：
`python -c "import sympy"`。
**缺库时**先询问用户是否安装（`python -m pip install sympy`）或换解释器，**不要未经询问直接装**。

Windows 控制台打印 ✓ 报 UnicodeEncodeError 时先设 `PYTHONIOENCODING=utf-8`。

## 命令行直接生成（不经过 AI）

```bash
cd skills/edu-complex
python scripts/generate.py list                   # 列出已注册题型
python scripts/generate.py multiply ./sol.html    # 乘法的几何意义
python scripts/generate.py all ./output           # 全部题型
python scripts/generate.py random 7 ./random.html # 随机出题（seed=7）
python lib/complex_kernel.py                     # kernel 内置自检（83 条）
```

> 不传输出路径时默认写到**当前工作目录（cwd）**。

| key | 场景 | 主问题 |
| --- | --- | --- |
| `algebra` | `cplane_add` | 复数加法为什么是平行四边形？三角不等式什么时候取等？ |
| `modulus` | `cplane_mod` | $z\\bar z$ 为什么一定是实数？$|z|$ 为什么与方向无关？ |
| `multiply` | `cplane_rot` | 「乘以一个复数」在几何上做了什么？ |
| `polar` | `cplane_pow` | 棣莫弗定理在说什么？$n$ 取何值时 $z^n = 1$？ |
| `roots` | `unitroots` | $n$ 个根为什么均匀分布？为什么它们的和恒为 0？ |
| `quadratic` | `qroots` | 判别式小于 0 时根长什么样？韦达定理还成立吗？ |
| `locus` | `locus` | $|z-z_0| = r$ 画出来是什么？ |

## 工作流程（AI 调用时）

1. **归一题面**：已知复数、所求、是否要几何解释，判断属于哪个题型。
2. **用 kernel 现算**（不要心算）：`cadd` `csub` `cmul` `cdiv` `conj` `modulus`
   `modulus2` `arg_deg` `polar` `power` `de_moivre` `roots_of_unity` `nth_roots`
   `root_sum` `root_product` `quadratic_roots` `discriminant`
   `circle_locus_pt` `same_distance_pt`。
3. **组装数据**三段 `lesson` / `steps` / `board`；可照抄 `scripts/generate.py` 的 7 个 `build_*`。
   **每个读数表达式都要与内核值对账**（`_agree`）。
4. **自检**：kernel 自检全过（83 条）；答案卡 == 末步展示值 == 画板读数初值；
   起本地静态服务，滑块拨到**每个档位**，确认
   ① 无控制台报错 ② **画布指纹数 = 档位数** ③ 不裁边
   ④ 状态灯在该翻转的参数值上翻转。

## 本技能特有的坑

### 1. 断言要对「整个实数范围」成立，不能只对某一类根成立
本轮的教训：写「两根互为共轭」时忘了**只有判别式 < 0 才成立** ——
实根情形下两个根各自与自己共轭，彼此并不共轭。
同样，「根的实部 = $-p/2$」只在复根时是两个根共有的数，
实根时两个根实部不同（$-p/2$ 只是它们的**平均**）。
> 正确做法：把断言写成**分情形**的，或者只断言**恒成立**的量（和、积、判别式）。
> 页面读数也一样：本页把「根₁的实部」「根₂的实部」分开列，而不是笼统写「根的实部」。

### 2. 数值相等 ≠ 符号化简相等
`sp.simplify(sum(roots_of_unity(3))) == 0` 可能为 `False`（结构上没化简到 0），
但 `abs(complex(sp.N(...))) < 1e-9` 一定为 `True`。
涉及 `exp` 表示的复数时，**用数值比较而不是结构比较**。

### 3. 读数的每一步都要有几何意义
复数题最容易做成「代数练习」。本技能的每个场景都强制给出一句几何解释
（平行四边形、镜像、旋转+伸缩、正多边形顶点、对称的根对、圆），
因为**复数的价值恰恰在于几何直观**。

### 4. 沿用既有三条（详见 `edu-physics-thermal` 的 SKILL.md）
① 场景字段要是表达式或数组，不能写死某个档位的具体数值；
② 状态灯文案是**纯文本**，不能写 `$…$`；`evalExpr` 只返回数字（布尔会变 NaN），
且**不支持 `cond ? a : b` 三元**（Python 侧会语法错）—— 用 `max/min` 改写；
③ 一行文字不超过约 28 个汉字（11px）。

## 数值出处分级

### ① 现算（sympy 精确计算，**不手写数字**）
四则运算、共轭、模（保留根式）、辐角、三角形式、整数次幂、
$n$ 次单位根（含「和为 0」「积为 $(-1)^{n-1}$」两条恒等式）、
一元二次方程的复根（含韦达定理校验）、几何轨迹上的点。

### ② 约定（示例参数）
- `algebra`：$z_1 = 2+i$、$|z_2| = 1.5$；滑块为 $\\theta\\in[0,355°]$，题设 30°。
- `modulus`：$|z| = 2.5$；滑块为 $\\theta\\in[0,355°]$，题设 40°。
- `multiply`：$z_1 = 2+i$、$|z_2| = 1.6$；滑块为 $\\theta_2\\in[0,355°]$，题设 60°。
- `polar`：$z = \\cos45°+i\\sin45°$；滑块为 $n\\in[1,12]$（整数），题设 3。
- `roots`：滑块为 $n\\in[2,12]$（整数），题设 5。
- `quadratic`：方程 $x^2+px+1=0$；滑块 $p\\in[-4,4]$，题设 1。
- `locus`：$z_0 = 1+i$、圆上取 $40°$ 方向的点；滑块 $r\\in[0.4,2.8]$，题设 1.5。
- 画板的原点与比例尺（`CP_OX`/`CP_OY`/`K`）为**约定的显示参数**，不影响任何计算。

### 未覆盖
复数的指数形式与欧拉公式（大学内容）、复变函数（解析函数、留数、积分）、
复数在交流电路与信号处理里的应用（可由 `edu-signals` 部分覆盖）、
三次以上方程的求根公式、复数与矩阵表示。遇到请直接说明未覆盖。

## 什么时候不该用本技能

先用**最低够用的表达级**：一句话能说清就别做图，一张静态图能说清就别做交互页。
本技能产出的是**自包含的交互教学网页**，构建与校验都有成本。

- 只要求**一个数值答案**（如「求 $|z|$」）——直接算并作答，不必做页。
- 题目是**平面向量**（数量积、投影、定比分点）——用 `edu-vector`。
- 题目是**圆锥曲线**（求弦长、定点、离心率）——用 `edu-analytic-geometry`。
- 题目是**一元二次方程在实数范围内的讨论**（判别式、韦达定理但不涉及复数）——
  用 `edu-math-junior`。

## 目录结构

```
edu-complex/
├── SKILL.md
├── lib/complex_kernel.py        # 内核（8 组函数 + 83 条自检）
├── scripts/generate.py          # 注入模板 + 7 个 build_* + 读数对账
└── template/
    ├── board.html               # 组装产物（勿直接修改）
    └── parts/                   # 模板片段（改这里再 compose）
        ├── scene_functions.html # 7 个 drawXxx + 复平面助手（cAxes/cArc/zLabel）
        ├── scene_dispatch.html
        ├── page_title.html
        └── board_label.html
```

## 扩展

- **加题型**：在 `complex_kernel.py` 加计算函数（+ `__main__` 自检），
  在 `generate.py` 加 `build_*`（含 `_agree` 对账）并注册进 `REGISTRY`。
- **加场景**：在 `template/parts/scene_functions.html` 加 `drawXxx(S)`，
  在 `scene_dispatch.html` 加 case，然后 `python ../../tools/compose_templates.py`
  重新组装 `template/board.html`。**不要直接改 `board.html`**。
