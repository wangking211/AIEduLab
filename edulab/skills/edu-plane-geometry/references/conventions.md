# 解法配方与自检约定（conventions）

## 总原则

1. **单一数据源**：答案、坐标、角度、线段比全部由 `geom_kernel.py` 精确算出，
   模型只组织讲解文字。绝不在 `steps` 里心算数字。
2. **规整优先**：随机出题与自定义题优先选能出整数/简单根式答案的参数
   （勾股数 3-4-5 / 5-12-13 / 8-15-17；13-14-15 三角形 S=84 p=21 r=4）。
3. **交互必有验证点**：每题至少一个 `constant` 指示器 + 高亮读数，
   让学生"拖动滑块看它不变/相等"，这是网页比教辅强的核心。

## 题型配方表

| 题型 key | 已知设置 | kernel 函数 | 核心交互 | 定值指示 |
|---|---|---|---|---|
| `pythagoras` | Rt△，直角边 a、b（勾股数） | `solve_pythagoras(a,b)` | 三边正方形面积读数 | S_a+S_b=S_c |
| `inscribed_angle` | ⊙O，圆心角 central° | `solve_inscribed(R,central)` | 点 C 在优弧上动（point_on_conic + @param） | ∠ACB 恒 = central/2 |
| `tangent_secant` | ⊙O 半径 R，OP>d，PT 切线 | `solve_tangent_secant(R,OP)` | 割线倾斜角 @param（line_through_angle + intersect_line_conic） | PA·PB 恒 = PT² = OP²−R² |
| `intersecting_chords` | ⊙O 半径 R，OP<d 圆内一点 | `solve_chord_product(R,d)` | 弦 CD 绕 P 旋转 @param | PC·PD 恒 = PA·PB = R²−OP² |
| `similar_A` | △ABC，D 在 AB 上 | `solve_similar_A(A,B,C,k)` | homothety 滑块 k 驱动 D、E | AD/AB=AE/AC=DE/BC 恒等 |
| `midsegment` | △ABC，D/E 中点 | `solve_midsegment(A,B,C)` | 静态（中点/刻度/箭头标注） | DE = BC/2 |
| `incircle` | △ABC 三边（13-14-15） | `solve_incircle(A,B,C)` | 静态；I 到三边距离三读数 | 三距离恒 = r = 2S/p |
| `circumcircle` | △ABC 三顶点 | `solve_circumcircle(A,B,C)` | 静态；中垂线交于 O | OA=OB=OC 恒 = R = abc/4S |

## 建图约定

- **坐标**：数学坐标 y 向上。三角形常用 A 在原点、AB 在 x 轴（如 A(0,0), B(6,0), C(3,4)
  得 BC=5；13-14-15 用 A(0,0), B(14,0), C(5,12)）。
- **视窗**：`NO_AXES`（隐藏网格与轴）+ 按点包围盒外扩 ~1.2。
- **角的标注**：圆心角用 `arcs: 2`，圆周角用 `arcs: 1`（弧数不同表示不相等；
  相等的角用相同弧数）。直角用 `right_angle_mark`。
- **等长/平行**：中点两侧用 `ticks: 2`（AD=DB）；单刻度表示与其他单刻度等长；
  平行线对用 `arrow: ">"`。
- **动点**：`point_on_conic`（圆上，参数为角度°）或 `homothety`（线段上，参数为比值 k）。

## 自检清单（每题交付前）

1. `python lib/geom_kernel.py` 全部 assert 通过。
2. `build_*` 内 assert：kernel 答案与期望公式一致（如中位线 DE=BC/2、
   切割线 PT²=OP²−R²、三比值=k）。
3. 答案卡 `lesson.answer` == 末步骤展示值 == 画板高亮读数初值。
4. 本地服务预览：无 console 报错；拖动滑块后高亮读数保持定值（或三比值保持相等）；
   角弧/直角/刻度/箭头渲染正确且不遮挡。
5. 成品写到 cwd（技能目录的 `output/` 只放仓库样例）。

## 常见坑

- **GBK 控制台**：Windows 下 print ✓/° 会 UnicodeEncodeError，先
  `PYTHONIOENCODING=utf-8`（kernel/generate 均受影响）。
- **引号**：Python f-string 里不要用 ASCII 直引号包中文（用中文引号“”）。
- **割线角度范围**：tangent_secant 的割线 @param 范围要保证与圆相交
  （115°~245° 对 P(5,0) R=3 安全）；intersecting_chords 的弦旋转角
  20°~160° 避免与 AB 共线退化。
- **优弧/劣弧**：圆周角动点 C 的参数范围限制在优弧上（如中心角 80° 时
  C 的位置角取 100°~260°），否则圆周角会在互补值间跳变。
