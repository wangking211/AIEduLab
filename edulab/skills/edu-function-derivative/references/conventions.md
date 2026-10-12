# 解法配方与自检约定（conventions）

## 总原则

1. **单一数据源**：导数、切线、极值、单调区间、零点、左右导数全部由 `fn_kernel.py`
   精确算出，模型只组织讲解文字。绝不在 `steps` 里心算数字。
2. **图解答同源**：函数表达式用 `js()` 喂画板采样、`tex()` 喂讲解排版，
   两者出自同一个 sympy 表达式——读数、图、文字永远一致。
3. **规整优先**：优先选整系数多项式与整数切点（x²、x³−3x、x³−x−2 在 [1,2]），
   极值/截距尽量出整数（±2、−1）。
4. **交互必有验证点**：每题至少一个高亮读数 + （适用时）`constant` 指示器或
   状态指示灯，让学生"拖动滑块看它不变/翻转"。

## 题型配方表

| 题型 key | 函数设置 | kernel 函数 | 核心交互 | 验证点 |
|---|---|---|---|---|
| `tangent_line` | f(x)=x²，切点 x₀ 滑块 | `solve_tangent_line(expr, x0)` | 切点沿曲线动、切线实时旋转 | 斜率读数 = f'(x₀)=2x₀ |
| `secant_limit` | f(x)=x²，A(1,1)，增量 h 滑块 | `solve_secant_limit(expr, 1)` | 割线 AB 随 h 绕 A 旋转，h→0 贴近虚线切线 | 割线斜率 → 切线斜率 f'(1)=2 |
| `cubic_extrema` | f(x)=x³−3x | `solve_cubic_extrema(1,0,-3,0)` | 动点切线 + 单调性指示灯 | k 符号 ↔ 增减；驻点处切线水平 |
| `parity_odd` | f(x)=x³−3x（奇） | `solve_parity(expr)` | P(t) 与 Q(−t) 关于原点对称动 | f(t)+f(−t) **恒 0**（constant） |
| `zero_crossing` | f(x)=x³−x−2，[1,2] | `solve_zero_crossing(expr,1,2)` | 试根 m 滑块 + 零点 Z 二分定位 | f(m) 符号 ↔ 零点所在子区间 |
| `exp_family` | y=aˣ（a 滑块） | `solve_exp_family(2)` | **底数进表达式** `pow(a,x)`，曲线变形 | a⁰ **恒 1**（constant，定点）；a>1/a<1 指示灯 |
| `abs_corner` | f(x)=\|x\| | `solve_abs_corner(0)` | 步长 h 滑块比较 ±h 左右差商 | 左 −1 / 右 +1 恒不等 → 不可导 |
| `tangent_family` | y=ln x，切点 a 滑块 | `solve_tangent_family()` | 切线随 a 动，交 y 轴的点高亮 | 截距 = ln a − 1；a≈e 时归 0 变绿 |

## 建图约定

- **坐标**：数学坐标 y 向上；函数题默认显示网格与坐标轴（与平面几何相反）。
- **视窗**：按函数在感兴趣区间的值域外扩 ~1.2（如 x³−3x 取 [−2.8,2.8]×[−3.5,3.5]）。
- **切线/割线**：切线 `tangent_function`（需 conic 带 `dexpr`）；割线
  `secant_function`（两个 x 端点，其中一个可写表达式如 `"1+h"`）。
- **垂足/投影**：先放原点静态点，`line_through_point_dir` 造坐标轴线，
  再 `foot_perp` + `segment(dashed)`。
- **零点**：`root_on_function`（端点异号，引擎二分），配 `area_fill` 画符号阴影。
- **滑块变量进表达式**：`expr`/读数 expr 直接写参数名（如底数 `a`、增量 `h`），
  引擎每帧按 env 重求值；`"@param"` 等价于滑块当前值。

## 自检清单（每题交付前）

1. `python lib/fn_kernel.py` 全部 assert 通过。
2. `build_*` 内保证 kernel 答案与期望一致（如割线极限 = 导数、左右导数不等）。
3. 答案卡 `lesson.answer` == 末步骤展示值 == 画板高亮读数初值。
4. 本地服务预览：无 console 报错；拖滑块曲线实时变形；定值读数保持恒定
   （f(t)+f(−t)=0、a⁰=1）；状态灯正确翻转（增/减、可导/不可导、零点侧）。
5. 成品写到 cwd（技能目录的 `output/` 只放仓库样例）。

## 常见坑

- **GBK 控制台**：Windows 下 print ✓ 会 UnicodeEncodeError，先 `PYTHONIOENCODING=utf-8`。
- **derived 顺序**：被引用的名字必须先定义（先 `Yaxis` 直线，后 `intersect_line_line`）。
- **dexpr 必填**：没有 `dexpr` 的曲线无法画切线、也无法用 `fn_slope`/`fn_status`；
  不可导点（|x| 在 0）处 dexpr 求值为 NaN，读数自动显示 `—`——这正是教学点。
- **定义域**：ln x、1/x 在定义域外采样得 NaN，引擎自动断线；滑块范围避开奇点
  （tangent_family 的 a 取 0.1~4.0，恒为正）。
- **零点端点**：`root_on_function` 要求 f(a)·f(b)<0，否则二分无意义；
  build 前用 `zero_interval` 断言验证。
- **h=0 退化**：割线题的 h 范围包含 0 时，两点重合 → 割线消失（引擎返回 null 不画），
  读数显示 `—`，教学上正好说明"h=0 时割线无定义"。
