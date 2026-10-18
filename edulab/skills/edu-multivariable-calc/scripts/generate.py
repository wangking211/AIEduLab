#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「多元微积分」交互网页。

全部数值由 lib/multivar_kernel.py 的 sympy **精确**内核算出：
导数、积分、极值都是符号计算的结果，黎曼和是**真求和**，页面上直接给出误差。

覆盖七个题型（18.02 / 高等数学下册）：
  gradient   梯度与方向导数（等高线 + 梯度箭头 + 方向）
  surface    曲面与切平面（伪 3D）
  lagrange   拉格朗日乘数法（等高线相切于约束曲线）
  riemann    二重积分的黎曼和（热力图 + 收敛）
  polar      极坐标下的二重积分（雅可比因子 r）
  green      格林公式（线积分 = 二重积分）
  field      散度与旋度（向量场箭头图）

依赖 sympy：
    python scripts/generate.py <题型key> [输出.html]
    python scripts/generate.py list
    python scripts/generate.py all <输出目录>
    python scripts/generate.py random [seed] [输出.html]
"""

import math
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PLACEHOLDER = "__LESSON_DATA__"

sys.path.insert(0, str(SKILL_DIR.parent.parent / "shared"))
sys.path.insert(0, str(SKILL_DIR / "lib"))

import sympy as sp                             # noqa: E402
import multivar_kernel as K                    # noqa: E402
from skillkit import cli                       # noqa: E402

_MATHENV = {
    "sqrt": math.sqrt, "abs": abs, "min": min, "max": max, "pow": pow,
    "sign": lambda v: (v > 0) - (v < 0), "floor": math.floor, "ceil": math.ceil,
    "PI": math.pi, "E": math.e,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "exp": math.exp, "log": math.log,
}


def _jseval(expr, **env):
    return eval(expr.replace("^", "**"), {"__builtins__": {}}, {**_MATHENV, **env})


def _agree(label, expr, want, tol=1e-9, **env):
    got = _jseval(expr, **env)
    d = abs(float(got) - float(want))
    if d > tol * max(1.0, abs(float(want))):
        raise AssertionError(
            f"读数表达式与内核不一致（{label}）：\n"
            f"  表达式 {expr!r}\n  按表达式算 = {got!r}\n  内核给出   = {want!r}")


def ro(rid, label, expr, digits=4, unit=None):
    d = {"id": rid, "label": label, "type": "expr", "expr": expr, "digits": digits}
    if unit:
        d["unit"] = unit
    return d


def ro_status(rid, label, expr, rhs=0, op="==", ok="成立", bad="不成立"):
    return {"id": rid, "label": label, "type": "status", "expr": expr,
            "rhs": rhs, "op": op, "okText": ok, "badText": bad}


X, Y = sp.symbols("x y", real=True)

# =====================================================================
# 1) 梯度与方向导数
# =====================================================================
GR_F = X ** 2 + Y ** 2
GR_P = (1.0, 1.0)
EXPR_GR_FX = f"2*{GR_P[0]}"
EXPR_GR_FY = f"2*{GR_P[1]}"
EXPR_GR_GM = f"sqrt(({EXPR_GR_FX})*({EXPR_GR_FX})+({EXPR_GR_FY})*({EXPR_GR_FY}))"
EXPR_GR_DU = f"({EXPR_GR_FX})*cos(thdeg*PI/180)+({EXPR_GR_FY})*sin(thdeg*PI/180)"


def build_gradient() -> dict:
    assert sp.simplify(K.grad(GR_F)[0] - 2 * X) == 0
    assert sp.simplify(K.grad(GR_F)[1] - 2 * Y) == 0
    for th in (0, 45, 90, 135, 180, 225, 270, 315):
        _agree(f"D_u f(θ={th})", EXPR_GR_DU, K.dir_deriv(GR_F, *GR_P, th), tol=1e-12, thdeg=th)
    _agree("|∇f|", EXPR_GR_GM, K.grad_norm(GR_F, *GR_P), tol=1e-12)
    _agree("最大方向导数为 |∇f|", EXPR_GR_DU, K.grad_norm(GR_F, *GR_P), tol=1e-12, thdeg=45)
    _agree("垂直方向导数为 0", EXPR_GR_DU, 0.0, tol=1e-12, thdeg=135)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "gradient", "thdeg": "thdeg",
                  "caption": "绿箭头 = 梯度 ∇f（最陡上升方向）；粉箭头 = 方向 u（可调）"},
        "param": {"name": "thdeg", "label": "方向角 $\\theta$", "min": 0, "max": 355,
                  "step": 5, "value": 45, "unit": "°", "standard": 45,
                  "ticks": ["0", "45 (最陡)", "135 (沿等高线)", "180"]},
        "readouts": [
            ro("fx", "$f_x$（定值 2）", EXPR_GR_FX, 2),
            ro("fy", "$f_y$（定值 2）", EXPR_GR_FY, 2),
            ro("gm", "$|\\nabla f|$ = 方向导数最大值", EXPR_GR_GM, 4),
            ro("du", "方向导数 $D_u f$", EXPR_GR_DU, 4),
            ro("cosv", "$\\cos(\\theta-45^\\circ)$",
               f"({EXPR_GR_DU})/({EXPR_GR_GM})", 4),
            ro_status("max", "是否取得最大方向导数（$u \\parallel \\nabla f$）",
                      f"abs(({EXPR_GR_DU})-({EXPR_GR_GM}))", 1e-6, "<",
                      "u 与 ∇f 同向：方向导数取到最大", "不是最陡的方向"),
        ],
        "constant": {"of": "gm", "label": "$|\\nabla f| = 2\\sqrt2$ 是定值：它就是方向导数的上界"},
    }
    lesson = {
        "language": "zh-CN", "title": "梯度与方向导数",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>设 $f(x,y) = x^2 + y^2$，在点 $P(1,1)$ 处。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求 $\\nabla f(P)$；</li>"
            "<li>求沿方向 $u = (\\cos\\theta, \\sin\\theta)$ 的方向导数 $D_u f$；</li>"
            "<li>$\\theta$ 取何值时最大？为什么「梯度垂直等高线」？</li></ol>"),
        "answerLabel": "$\\theta = 45°$ 时",
        "answer": f"$\\nabla f = (2,2)$，$D_u f = 2\\cos\\theta+2\\sin\\theta$，"
                  f"最大值 $|\\nabla f| = {K.f(K.grad_norm(GR_F, 1.0, 1.0), 4)}$",
    }
    steps = [
        {"title": "偏导数：把一个变量冻住",
         "content": ("<p>求 $f_x$ 时把 $y$ 当成**常数**，只对 $x$ 求导：</p>"
                     "<p>$f = x^2+y^2 \\Rightarrow f_x = 2x,\\ f_y = 2y$。</p>"
                     "<p>在 $P(1,1)$：$\\nabla f = (2,2)$ —— 这就是**梯度**，"
                     "一个把点映到向量的「向量场」。</p>"
                     "<p>本页的 $f = x^2+y^2$ 的等高线是同心圆；梯度箭头永远**垂直于**"
                     "所在的那条等高线。</p>")},
        {"title": "方向导数就是梯度在方向上的投影",
         "content": ("<p>$D_u f = \\nabla f \\cdot u = |\\nabla f|\\cos\\varphi$，"
                     "其中 $\\varphi$ 是 $u$ 与 $\\nabla f$ 的夹角。</p>"
                     "<p>于是立刻得到三条结论：</p>"
                     "<p>· $u \\parallel \\nabla f$ 时取到**最大** $|\\nabla f|$"
                     "（最陡上升方向）；</p>"
                     "<p>· $u \\perp \\nabla f$ 时 $D_u f = 0$（**沿等高线走不升不降**）；</p>"
                     "<p>· 反方向取到 $-|\\nabla f|$（最陡下降）。</p>"
                     "<p>拖滑块转一圈，读数区里 $D_u f$ 正好按余弦变化，"
                     "而 $|\\nabla f|$ 那个定值一动不动 —— 它就是上界。</p>")},
        {"title": "为什么要发明梯度",
         "content": ("<p>因为「导数」在一维只有一个方向，在多元却有**无穷多个**方向。"
                     "梯度把无穷多个方向导数压缩成一个向量："
                     "只要知道 $\\nabla f$，任何方向的导数都是它的一次投影。</p>"
                     "<p>这也解释了梯度下降法：想最快下降，就朝 $-\\nabla f$ 走一步。"
                     "机器学习里训练神经网络的「梯度下降」，用的就是这一页的式子。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 曲面与切平面
# =====================================================================
SF_F = 4 - (X ** 2 + Y ** 2) / 3
SF_Y0 = 0.8
EXPR_SF_Z = f"4-(xpt*xpt+{SF_Y0}*{SF_Y0})/3"
EXPR_SF_FX = f"-2*xpt/3"
EXPR_SF_FY = f"-2*{SF_Y0}/3"


def build_surface() -> dict:
    for x0 in (-2.0, -1.0, 0.0, 1.0, 2.0):
        _agree(f"f(x={x0})", EXPR_SF_Z, K.surface_z(SF_F, x0, SF_Y0), tol=1e-12, xpt=x0)
        _agree(f"f_x(x={x0})", EXPR_SF_FX, K.grad_at(SF_F, x0, SF_Y0)[0], tol=1e-12, xpt=x0)
        _agree(f"f_y(x={x0})", EXPR_SF_FY, K.grad_at(SF_F, x0, SF_Y0)[1], tol=1e-12, xpt=x0)
        # 切平面在切点处与曲面相切（一阶接近）
        z0, ax, ay = K.tangent_plane(SF_F, x0, SF_Y0)
        _agree(f"切平面沿 x 相切(x={x0})", f"({EXPR_SF_Z})+({EXPR_SF_FX})*0.001",
               K.surface_z(SF_F, x0 + 0.001, SF_Y0), tol=1e-5, xpt=x0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "surface", "xpt": "xpt",
                  "caption": "伪 3D 斜投影：蓝网格是曲面，黄方块是切平面（贴在切点附近）"},
        "param": {"name": "xpt", "label": "切点的 $x_0$", "min": -2, "max": 2,
                  "step": 0.1, "value": 0.5, "unit": "", "standard": 0.5,
                  "ticks": ["-2", "0", "0.5 (题设)", "2"]},
        "readouts": [
            ro("z0", "切点高度 $f(x_0, 0.8)$", EXPR_SF_Z, 4),
            ro("fx", "$f_x = -2x/3$", EXPR_SF_FX, 4),
            ro("fy", "$f_y = -2y/3$（定值）", EXPR_SF_FY, 4),
            ro("slope", "切平面在 $x$ 方向的斜率", EXPR_SF_FX, 4),
            ro_status("flat", "切点是否在曲面的最高处（$f_x = 0$）",
                      f"abs({EXPR_SF_FX})", 1e-6, "<",
                      "在最陡处：切平面水平（f_x = f_y = 0）", "切平面有倾斜"),
        ],
        "constant": {"of": "fy", "label": "$y_0 = 0.8$ 固定 ⇒ $f_y$ 恒为 −0.5333 —— 只有 $x_0$ 在动"},
    }
    lesson = {
        "language": "zh-CN", "title": "曲面与切平面",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>设曲面 $z = f(x,y) = 4 - \\dfrac{x^2+y^2}{3}$，"
            "取点 $P(x_0,\\ 0.8)$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $f_x$、$f_y$；</li>"
            "<li>写出曲面在 $P$ 处的切平面；</li>"
            "<li>为什么切平面是曲面在切点附近的「最佳线性逼近」？</li></ol>"),
        "answerLabel": "$x_0 = 0.5$ 时",
        "answer": f"$f_x = {K.f(K.grad_at(SF_F, 0.5, 0.8)[0], 4)}$，"
                  f"$f_y = {K.f(K.grad_at(SF_F, 0.5, 0.8)[1], 4)}$，"
                  f"$f = {K.f(K.surface_z(SF_F, 0.5, 0.8), 4)}$",
    }
    steps = [
        {"title": "从切线到切平面",
         "content": ("<p>一维时切线是 $y = f(a) + f'(a)(x-a)$。"
                     "二维时把「两个方向的切线」拼起来，就得到**切平面**：</p>"
                     "<p>$z = f(x_0,y_0) + f_x(x_0,y_0)(x-x_0) + f_y(x_0,y_0)(y-y_0)$。</p>"
                     "<p>它其实就是「分别沿 $x$ 方向和 $y$ 方向各切一刀，"
                     "把两条切线张成的平面」。</p>")},
        {"title": "为什么叫「最佳线性逼近」",
         "content": ("<p>把曲面与切平面相减，剩下的误差是**二阶小量**：</p>"
                     "<p>$f(x,y) - L(x,y) = O\\bigl((\\Delta x)^2 + (\\Delta y)^2\\bigr)$。</p>"
                     "<p>也就是说在切点附近，切平面与曲面「贴得很紧」—— "
                     "紧到一阶导都分不出来。这正是**可微**的定义。</p>"
                     "<p>把切点拖到 $x_0 = 0$（曲面的顶点），"
                     "两个偏导都变成 0，切平面就水平了 —— 状态灯会亮。</p>")},
        {"title": "全微分",
         "content": ("<p>把上式改写成增量形式，就得到**全微分**：</p>"
                     "<p>$dz = f_x\\,dx + f_y\\,dy = \\nabla f \\cdot (dx, dy)$。</p>"
                     "<p>这与上一节的「方向导数」是同一件事："
                     "方向导数就是沿单位方向的全微分。全微分把"
                     "「多个变量的微小变化」线性打包成一个点积，"
                     "是误差估计、牛顿法、最小二乘的共同起点。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 拉格朗日乘数法
# =====================================================================
EXPR_LG_MX = "aa/sqrt(2)"
EXPR_LG_MY = "1/sqrt(2)"
EXPR_LG_MAX = "aa/2"
EXPR_LG_LAM = "aa/2"


def build_lagrange() -> dict:
    for a in (0.5, 1.0, 1.5, 2.0, 2.5):
        sol = K.lagrange_xy_circle(a)          # 同一套代数，把 b 换成 1 后 λ = a/2
        _agree(f"极值点 x(a={a})", EXPR_LG_MX, a / math.sqrt(2), tol=1e-12, aa=a)
        _agree(f"极值点 y(a={a})", EXPR_LG_MY, 1.0 / math.sqrt(2), tol=1e-12, aa=a)
        _agree(f"最大值(a={a})", EXPR_LG_MAX, a * 1.0 / 2.0, tol=1e-12, aa=a)
        _agree(f"λ(a={a})", EXPR_LG_LAM, a / 2.0, tol=1e-12, aa=a)
        # 约束满足：x²/a² + y²/b² = 1
        assert abs((a / math.sqrt(2)) ** 2 / (a * a) + (1 / math.sqrt(2)) ** 2 - 1) < 1e-12
    # ∇f ∥ ∇g 的验证（叉积为 0），且 λ = a/2 使 ∇f = λ∇g
    for a in (0.5, 1.0, 2.0):
        mx, my = a / math.sqrt(2), 1 / math.sqrt(2)
        gf = (my, mx)
        gg = (2 * mx / (a * a), 2 * my / 1.0)
        lam = a / 2.0
        assert abs(gf[0] - lam * gg[0]) < 1e-12 and abs(gf[1] - lam * gg[1]) < 1e-12
        assert abs(gf[0] * gg[1] - gf[1] * gg[0]) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "lagrange", "aa": "aa",
                  "caption": "灰曲线 = f = xy 的等高线；蓝椭圆 = 约束；四个点处两梯度平行"},
        "param": {"name": "aa", "label": "约束半轴 $a$（$x^2/a^2 + y^2 = 1$）",
                  "min": 0.5, "max": 2.5, "step": 0.1, "value": 1.0,
                  "unit": "", "standard": 1.0,
                  "ticks": ["0.5", "1 (圆)", "1.5", "2.5"]},
        "readouts": [
            ro("mx", "极值点的 $x$（定值 $\\times a$）", EXPR_LG_MX, 4),
            ro("my", "极值点的 $y$（定值）", EXPR_LG_MY, 4),
            ro("max", "最大值 $f = xy = a/2$", EXPR_LG_MAX, 4),
            ro("lam", "乘数 $\\lambda$", EXPR_LG_LAM, 4),
            ro_status("biglam", "乘数是否大于 1/2（约束的梯度是否更陡）", EXPR_LG_LAM, 0.5, ">",
                      "λ > 1/2：约束曲线的梯度更陡（椭圆较扁）", "λ ≤ 1/2：约束较「圆」"),
        ],
        "constant": {"of": "my", "label": "$y$ 坐标恒为 $1/\\sqrt2$ —— 与 $a$ 无关（约束的 $y$ 半轴固定）"},
    }
    lesson = {
        "language": "zh-CN", "title": "拉格朗日乘数法",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>求 $f(x,y) = xy$ 在约束 $\\dfrac{x^2}{a^2} + y^2 = 1$ 上的最大值与最小值。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出拉格朗日函数并列出方程组；</li>"
            "<li>求极值点与乘数 $\\lambda$；</li>"
            "<li>为什么极值点处的 $\\nabla f$ 一定与 $\\nabla g$ 平行？</li></ol>"),
        "answerLabel": "$a = 1$ 时",
        "answer": f"极值点 $(\\pm\\dfrac{{1}}{{\\sqrt2}}, \\pm\\dfrac{{1}}{{\\sqrt2}})$，"
                  f"最大值 ${K.f(0.5, 4)}$，$\\lambda = 0.5$",
    }
    steps = [
        {"title": "把约束「拉」进目标函数",
         "content": ("<p>要求 $f$ 在 $g(x,y) = \\dfrac{x^2}{a^2} + y^2 - 1 = 0$ 上的极值，"
                     "构造拉格朗日函数</p>"
                     "<p>$L(x,y,\\lambda) = f - \\lambda g$。</p>"
                     "<p>对三个变量各求偏导并令其为 0，就得到</p>"
                     "<p>$\\nabla f = \\lambda \\nabla g$，外加约束方程本身。</p>")},
        {"title": "几何意义：等高线相切于约束曲线",
         "content": ("<p>沿着约束曲线走，$f$ 的值不断变化。当**走到极值时**，"
                     "$f$ 在该点沿约束方向的导数为 0 —— 也就是约束的切向与"
                     "等高线的切向重合，两条曲线**相切**。</p>"
                     "<p>而 $\\nabla f$ 垂直等高线、$\\nabla g$ 垂直约束曲线；"
                     "两者都与同一条切线垂直，所以 $\\nabla f \\parallel \\nabla g$。"
                     "这就是图上下载黄框处那两个同向箭头的含义。</p>")},
        {"title": "解出来是 λ = a/2",
         "content": ("<p>由 $\\nabla f = (y, x)$、$\\nabla g = \\left(\\dfrac{2x}{a^2}, 2y\\right)$"
                     "联立可得 $x = \\pm\\dfrac{a}{\\sqrt2}$、"
                     "$y = \\pm\\dfrac{1}{\\sqrt2}$，且</p>"
                     "<p>$\\lambda = \\dfrac{a}{2}$。</p>"
                     "<p>最大值是 $\\dfrac{a}{2}$、最小值是 $-\\dfrac{a}{2}$"
                     "（正负号对应 $\\lambda$ 的正负：$\\lambda > 0$ 是极大，"
                     "$\\lambda < 0$ 是极小）。</p>"
                     "<p>把滑块拖过 $a = 1$，$\\lambda$ 与 $\\dfrac12$ 的大小关系会翻转 —— "
                     "它反映的是「约束曲线的梯度有多陡」。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 二重积分的黎曼和
# =====================================================================
RM_F = 4 - X ** 2 - Y ** 2
RM_XR, RM_YR = (-1.5, 1.5), (-1.5, 1.5)
RM_NMAX = 20
RM_EXACT = K.double_integral(RM_F, RM_XR, RM_YR)
RM_SUMS = [K.riemann_rect(RM_F, RM_XR, RM_YR, n)[0] for n in range(1, RM_NMAX + 1)]


def build_riemann() -> dict:
    assert abs(RM_EXACT - 22.5) < 1e-9, f"精确值应为 22.5，实得 {RM_EXACT}"
    for n in (1, 2, 4, 8, 16, 20):
        _agree(f"黎曼和(n={n})", f"{RM_SUMS[n - 1]!r}", RM_SUMS[n - 1], tol=1e-12, n=n)
    # 单调收敛且极限为精确值
    assert all(RM_SUMS[i] > RM_SUMS[i + 1] for i in range(RM_NMAX - 1)), "黎曼和应当单调下降收敛"
    assert abs(RM_SUMS[-1] - RM_EXACT) < 0.1
    _agree("ΔA(n=4)", "pow(3.0/4,2)", 9.0 / 16.0, tol=1e-12)

    arr = "[" + ",".join(repr(v) for v in RM_SUMS) + "][n-1]"
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "riemann", "n": "n", "riemannAll": RM_SUMS,
                  "caption": "把区域切成 n×n 块，颜色越亮表示该块高度 f 越大"},
        "param": {"name": "n", "label": "每边切成的块数 $n$", "min": 1, "max": RM_NMAX,
                  "step": 1, "value": 4, "unit": "", "standard": 4,
                  "ticks": ["1", "4 (题设)", "10", "20"]},
        "readouts": [
            ro("sum", "黎曼和 $\\sum f(\\Delta A)$", arr, 6),
            ro("da", "每块的面积 $\\Delta A = (3/n)^2$", "pow(3.0/n,2)", 6),
            ro("exact", "精确值 $\\iint_D$（定值）", f"{RM_EXACT!r}", 6),
            ro("err", "相对误差", f"abs(({arr})-{RM_EXACT!r})/abs({RM_EXACT!r})", 6),
            ro_status("conv", "相对误差是否小于 1%",
                      f"abs(({arr})-{RM_EXACT!r})/abs({RM_EXACT!r})", 0.01, "<",
                      "误差 < 1%：已经收敛得很好", "误差 ≥ 1%：再细分一点"),
        ],
        "constant": {"of": "exact", "label": "精确值 $\\iint_D (4-x^2-y^2)\\,dA = 22.5$ 不随 $n$ 变"},
    }
    lesson = {
        "language": "zh-CN", "title": "二重积分与黎曼和",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>把区域 $D = [-1.5,1.5]\\times[-1.5,1.5]$ 切成 $n\\times n$ 个小方块，"
            "取每块中点的函数值 $f = 4-x^2-y^2$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出黎曼和并说明它随 $n$ 怎么变；</li>"
            "<li>求精确值 $\\iint_D f\\,dA$；</li>"
            "<li>为什么「取中点」比「取角点」收敛得快？</li></ol>"),
        "answerLabel": "$n = 4$ 时",
        "answer": f"黎曼和 $\\approx {K.f(RM_SUMS[3], 6)}$，精确值 $= {K.f(RM_EXACT, 4)}$",
    }
    steps = [
        {"title": "二重积分就是二维的「求和取极限」",
         "content": ("<p>把 $D$ 切成 $n^2$ 个小块，每块面积 $\\Delta A$，"
                     "第 $(i,j)$ 块里任取一点 $(\\xi_{ij},\\eta_{ij})$，作和</p>"
                     "<p>$S_n = \\sum_{i,j} f(\\xi_{ij},\\eta_{ij})\\,\\Delta A$。</p>"
                     "<p>让 $n \\to \\infty$（每块都缩成一点），如果极限存在，"
                     "就把它记作 $\\iint_D f\\,dA$。</p>"
                     "<p>本页的黎曼和是**程序真求和**出来的，不是套公式，"
                     "所以它随 $n$ 增大而单调逼近精确值 —— 拖滑块就能看到收敛。</p>")},
        {"title": "这个积分的精确值",
         "content": ("<p>因为区域是正方形、函数是分离变量的，可以逐项积分：</p>"
                     "<p>$\\iint 4\\,dA = 4\\times 9 = 36$；</p>"
                     "<p>$\\iint x^2\\,dA = \\iint y^2\\,dA = 3\\times"
                     "\\left[\\dfrac{x^3}{3}\\right]_{-1.5}^{1.5} = 3\\times 2.25 "
                     "= 6.75$。</p>"
                     "<p>所以 $\\iint_D (4-x^2-y^2)\\,dA = 36 - 6.75 - 6.75 = 22.5$。"
                     "读数区里那个定值就是它。</p>")},
        {"title": "为什么用中点",
         "content": ("<p>如果用每块的**角点**取值，上下偏差是**一阶**的，误差 $\\sim 1/n$；"
                     "取**中点**时对称地高估与低估彼此抵消，误差提升到 $\\sim 1/n^2$。</p>"
                     "<p>本页对 $f = 4-x^2-y^2$ 这种抛物面，中点法还有一个额外好处："
                     "每块的 $\\overline{x^2}$ 恰好等于中点的 $x^2$ 加上一个与位置无关的常量，"
                     "所以误差收敛得特别干净。</p>"
                     "<p>这也是数值积分里「中点法则优于梯形法则（对光滑函数）」的原因。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 极坐标下的二重积分
# =====================================================================
EXPR_PL_AREA = "PI*rr*rr"
EXPR_PL_INT = "PI*pow(rr,4)/2"


def build_polar() -> dict:
    for R in (0.6, 1.0, 1.5, 2.0, 2.4):
        _agree(f"圆盘面积(R={R})", EXPR_PL_AREA, K.polar_integral(sp.Integer(1), R), tol=1e-9, rr=R)
        _agree(f"∬(x²+y²)(R={R})", EXPR_PL_INT, K.polar_integral(K.r ** 2, R), tol=1e-9, rr=R)
        # 极坐标的黎曼和逼近
        assert abs(K.polar_riemann(K.r ** 2, R, 80, 144) - math.pi * R ** 4 / 2) < 5e-3 * R ** 4
    # 直角坐标与极坐标必须给出同一个数
    rect_val = float(sp.integrate(sp.integrate(X ** 2 + Y ** 2,
                                               (Y, -sp.sqrt(1 - X ** 2), sp.sqrt(1 - X ** 2))),
                                  (X, -1, 1)))
    _agree("直角坐标与极坐标一致", EXPR_PL_INT, rect_val, tol=1e-9, rr=1.0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "polar", "rr": "rr",
                  "caption": "极坐标网格：圆环 × 射线；黄色是面积元 ΔA = r dr dθ"},
        "param": {"name": "rr", "label": "圆盘半径 $R$", "min": 0.6, "max": 2.4,
                  "step": 0.05, "value": 1.0, "unit": "", "standard": 1.0,
                  "ticks": ["0.6", "1 (题设)", "1.5", "2.4"]},
        "readouts": [
            ro("area", "圆盘面积 $\\iint 1\\,dA = \\pi R^2$", EXPR_PL_AREA, 6),
            ro("int", "$\\iint (x^2+y^2)\\,dA = \\pi R^4/2$", EXPR_PL_INT, 6),
            ro("r3", "被积函数（极坐标下）$g(r,\\theta) = r^2$", "pow(rr,2)", 4),
            ro("jac", "雅可比因子：$dA = r\\,dr\\,d\\theta$ 里的 $r$", "rr", 4),
            ro_status("big", "面积是否超过 $\\pi$（$R > 1$）", EXPR_PL_AREA, math.pi, ">",
                      "R > 1：圆盘比单位圆大", "R ≤ 1：圆盘不超过单位圆"),
        ],
        "constant": {"of": "jac", "label": "面积元 $dA = r\\,dr\\,d\\theta$ 里那个 $r$ 恒存在 —— 少写它是最常见的错"},
    }
    lesson = {
        "language": "zh-CN", "title": "极坐标下的二重积分",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>设 $D$ 是半径为 $R$ 的圆盘，求 $\\displaystyle\\iint_D (x^2+y^2)\\,dA$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>把被积函数与面积元都换成极坐标；</li>"
            "<li>写出累次积分并算出结果；</li>"
            "<li>为什么 $dA = r\\,dr\\,d\\theta$ 里会多出一个 $r$？</li></ol>"),
        "answerLabel": "$R = 1$ 时",
        "answer": "$\\displaystyle\\iint_D (x^2+y^2)\\,dA = "
                  "\\int_0^{2\\pi}\\!\\!\\int_0^R r^3\\,dr\\,d\\theta = \\dfrac{\\pi R^4}{2}$",
    }
    steps = [
        {"title": "三处都要换",
         "content": ("<p>换成极坐标时要同时改三样：</p>"
                     "<p>· 被积函数：$x^2+y^2 = r^2$；</p>"
                     "<p>· 区域：圆盘 $r \\le R$、$0 \\le \\theta \\le 2\\pi$；</p>"
                     "<p>· **面积元**：$dA = r\\,dr\\,d\\theta$。</p>"
                     "<p>第三样最容易被漏掉 —— 漏了 $r$，答案就完全错了。</p>")},
        {"title": "那个 r 从哪来",
         "content": ("<p>看图上那块黄色的面积元：它不是矩形，而是一个**扇形环**。"
                     "内弧长 $r\\,d\\theta$、外弧长 $(r+dr)d\\theta$、径向厚度 $dr$，"
                     "所以面积约为</p>"
                     "<p>$\\Delta A \\approx r\\,dr\\,d\\theta$。</p>"
                     "<p>$r$ 在这里就是雅可比行列式 $\\left|\\dfrac{\\partial(x,y)}{\\partial(r,\\theta)}\\right| = r$ —— "
                     "换元时「面积被拉伸了多少倍」的度量。</p>"
                     "<p>直观地说：**离原点越远的地方，同样的 $dr\\,d\\theta$ 覆盖的面积越大**，"
                     "所以要在那里乘一个更大的权重 $r$。</p>")},
        {"title": "算出来",
         "content": ("<p>$\\displaystyle\\iint_D r^2\\cdot r\\,dr\\,d\\theta = "
                     "\\int_0^{2\\pi}\\!\\!\\int_0^R r^3\\,dr\\,d\\theta "
                     "= 2\\pi\\cdot\\dfrac{R^4}{4} = \\dfrac{\\pi R^4}{2}$。</p>"
                     "<p>同一个积分用直角坐标硬算（$\\int_{-R}^{R}\\int_{-\\sqrt{R^2-x^2}}^{\\sqrt{R^2-x^2}}$）"
                     "也能得到同样的结果 —— 但麻烦得多。"
                     "**换坐标系不该改变结果，只应改变计算的难易**，"
                     "这正是读数区上下两行数值一致的原因。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 格林公式
# =====================================================================
# P = −y³/3、Q = x³/3 ⇒ Q_x − P_y = x² + y²
GRN_P = -Y ** 3 / 3
GRN_Q = X ** 3 / 3
EXPR_GN_CURL = "pow(rr,2)"
EXPR_GN_LINE = "pow(rr,4)/3*(2*PI)*(3/4)"
EXPR_GN_DBL = "2*(PI*pow(rr,4)/4)"
EXPR_GN_DIFF = f"abs(({EXPR_GN_LINE})-({EXPR_GN_DBL}))"


def build_green() -> dict:
    assert sp.simplify(K.curl(GRN_P, GRN_Q) - (X ** 2 + Y ** 2)) == 0
    for R in (0.6, 1.0, 1.5, 2.0):
        line = K.line_integral(GRN_P, GRN_Q, K.circle_curve(R), 0, 2 * sp.pi)
        _agree(f"线积分(R={R})", EXPR_GN_LINE, line, tol=1e-9, rr=R)
        _agree(f"二重积分(R={R})", EXPR_GN_DBL, math.pi * R ** 4 / 2, tol=1e-9, rr=R)
        _agree(f"两端相等(R={R})", EXPR_GN_DIFF, 0.0, tol=1e-9, rr=R)
    # 右端的 x²+y² 在圆盘上的积分正是 πR⁴/2 —— 内核独立再算一次
    for R in (0.6, 1.0, 2.0):
        _agree(f"内核二重积分(R={R})", f"{math.pi * R ** 4 / 2!r}",
               K.polar_integral(K.r ** 2, R), tol=1e-9, rr=R)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "green", "rr": "rr",
                  "caption": "灰箭头 = 场 F；蓝盘 = 区域 D；黄箭头 = 逆时针边界 L"},
        "param": {"name": "rr", "label": "区域半径 $R$", "min": 0.6, "max": 2.0,
                  "step": 0.05, "value": 1.0, "unit": "", "standard": 1.0,
                  "ticks": ["0.6", "1 (题设)", "1.5", "2"]},
        "readouts": [
            ro("line", "左端：$\\oint_L P\\,dx+Q\\,dy$", EXPR_GN_LINE, 6),
            ro("dbl", "右端：$\\iint_D (Q_x-P_y)\\,dA$", EXPR_GN_DBL, 6),
            ro("curl", "$Q_x - P_y$（即 $x^2+y^2$）", EXPR_GN_CURL, 4),
            ro("diff", "两端之差（定值 0）", EXPR_GN_DIFF, 6),
            ro_status("ok", "两端是否相等（格林公式是否成立）", EXPR_GN_DIFF, 1e-6, "<",
                      "两端相等：格林公式成立", "两端不等"),
        ],
        "constant": {"of": "diff", "label": "两端之差恒为 0 —— 这就是格林公式本身"},
    }
    lesson = {
        "language": "zh-CN", "title": "格林公式",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>设 $P = -\\dfrac{y^3}{3}$、$Q = \\dfrac{x^3}{3}$，"
            "$L$ 是半径为 $R$ 的圆盘的逆时针边界。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求 $Q_x - P_y$；</li>"
            "<li>分别算出 $\\oint_L P\\,dx+Q\\,dy$ 与 $\\iint_D (Q_x-P_y)\\,dA$；</li>"
            "<li>为什么两者一定相等？逆时针为什么是「正向」？</li></ol>"),
        "answerLabel": "$R = 1$ 时",
        "answer": f"两端都等于 $\\dfrac{{\\pi R^4}}{{2}} = {K.f(math.pi / 2, 6)}$",
    }
    steps = [
        {"title": "公式的两端",
         "content": ("<p>$\\displaystyle\\oint_L P\\,dx + Q\\,dy = "
                     "\\iint_D \\left(\\dfrac{\\partial Q}{\\partial x} - "
                     "\\dfrac{\\partial P}{\\partial y}\\right)dA$。</p>"
                     "<p>左边是**沿边界的曲线积分**，右边是**区域内部的二重积分**。"
                     "它把「一维的边界信息」与「二维的内部信息」联系了起来。</p>"
                     "<p>本页取 $P = -y^3/3$、$Q = x^3/3$，"
                     "于是 $Q_x - P_y = x^2 + y^2$ —— "
                     "这正是上一节极坐标算过的那个积分，结果为 $\\pi R^4/2$。</p>")},
        {"title": "直接算左端",
         "content": ("<p>在圆上 $x = R\\cos t$、$y = R\\sin t$：</p>"
                     "<p>$-\\dfrac{y^3}{3}dx + \\dfrac{x^3}{3}dy "
                     "= \\dfrac{R^4}{3}(\\sin^4 t + \\cos^4 t)\\,dt$。</p>"
                     "<p>再用 $\\sin^4 t + \\cos^4 t = 1 - \\dfrac12\\sin^2 2t$，"
                     "在 $[0,2\\pi]$ 上积分为 $\\dfrac{3\\pi}{2}$，于是</p>"
                     "<p>$\\oint_L = \\dfrac{R^4}{3}\\cdot\\dfrac{3\\pi}{2} "
                     "= \\dfrac{\\pi R^4}{2}$ —— 与右端完全一致。</p>"
                     "<p>两条完全不同的计算路线得到同一个数，这就是公式的价值。</p>")},
        {"title": "为什么逆时针是正向",
         "content": ("<p>格林公式的标准形式要求边界取**正方向**："
                     "沿边界行走时，区域始终在**左侧**。对圆盘来说就是**逆时针**。</p>"
                     "<p>如果取顺时针，结果要变号 —— 因为「绕行的方向」"
                     "本身带着正负。图上的黄箭头就是这个定向。</p>"
                     "<p>格林公式还有一个常见用途是**反过来算**："
                     "遇到不好算的二重积分，就把它换成边界上的曲线积分；"
                     "面积公式 $A = \\dfrac12\\oint(x\\,dy - y\\,dx)$ 也是它的直接推论。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 散度与旋度
# =====================================================================
FL_P = X
FL_Q = lambda k: k * Y
EXPR_FL_DIV = "1+kk"
EXPR_FL_CURL = "0"


def build_field() -> dict:
    for k in (-2.0, -1.0, 0.0, 0.5, 2.0):
        _agree(f"div(k={k})", EXPR_FL_DIV, float(K.divergence(FL_P, FL_Q(k))), tol=1e-12, kk=k)
        _agree(f"curl(k={k})", EXPR_FL_CURL, float(K.curl(FL_P, FL_Q(k))), tol=1e-12, kk=k)
        _agree(f"场值(k={k})", f"1", K.field_at(FL_P, FL_Q(k), 1, 1)[0], tol=1e-12, kk=k)
        _agree(f"场值 y(k={k})", f"kk*1", K.field_at(FL_P, FL_Q(k), 1, 1)[1], tol=1e-12, kk=k)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "field", "kk": "kk",
                  "caption": "向量场 F = (x, k·y)：k > −1 向外发散（源），k < −1 向内汇聚（汇）"},
        "param": {"name": "kk", "label": "参数 $k$（$F = (x,\\ k y)$）", "min": -2, "max": 2,
                  "step": 0.1, "value": 0.5, "unit": "", "standard": 0.5,
                  "ticks": ["-2 (强汇)", "-1 (无源无汇)", "0.5 (题设)", "2 (强源)"]},
        "readouts": [
            ro("div", "散度 $\\operatorname{div}F = P_x + Q_y$", EXPR_FL_DIV, 4),
            ro("curl", "旋度 $\\operatorname{curl}F = Q_x - P_y$", EXPR_FL_CURL, 4),
            ro("fx", "$F$ 在 (1,1) 处的 $x$ 分量", "1", 4),
            ro("fy", "$F$ 在 (1,1) 处的 $y$ 分量", "kk*1", 4),
            ro_status("src", "是否是「源」（散度为正）", EXPR_FL_DIV, 0, ">",
                      "散度为正：整体向外发散（源）", "散度不为正：整体不向外"),
        ],
        "constant": {"of": "curl", "label": "这个场的旋度恒为 0 —— 它只沿轴向伸缩，不绕任何点转"},
    }
    lesson = {
        "language": "zh-CN", "title": "散度与旋度",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>设向量场 $F(x,y) = (x,\\ k y)$，$k$ 可调。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求 $\\operatorname{div}F$ 与 $\\operatorname{curl}F$；</li>"
            "<li>$k$ 取何值时这个场「无源无汇」？</li>"
            "<li>为什么这个场的旋度恒为 0？</li></ol>"),
        "answerLabel": "$k = 0.5$ 时",
        "answer": f"$\\operatorname{{div}}F = 1+k = {K.f(1.5, 2)}$，"
                  "$\\operatorname{curl}F = 0$（无旋）",
    }
    steps = [
        {"title": "两个「导数」各自的含义",
         "content": ("<p>$\\operatorname{div}F = \\dfrac{\\partial P}{\\partial x} + "
                     "\\dfrac{\\partial Q}{\\partial y}$ 度量**「这一点是源还是汇」**："
                     "正数说明流从这里往外冒，负数说明往里吸。</p>"
                     "<p>$\\operatorname{curl}F = \\dfrac{\\partial Q}{\\partial x} - "
                     "\\dfrac{\\partial P}{\\partial y}$ 度量**「这一点附近有没有旋转」**。</p>"
                     "<p>本页 $F = (x, ky)$ 是**对角线场**：散度 $= 1+k$、旋度 $= 0$。"
                     "无论 $k$ 怎么变，它都不产生任何旋转 —— "
                     "读数区里旋度那一行永远不动。</p>")},
        {"title": "把滑块拖到 k = −1",
         "content": ("<p>$k = -1$ 时 $F = (x, -y)$：沿 $x$ 方向向外拉、沿 $y$ 方向向内拉，"
                     "两者恰好抵消，$\\operatorname{div}F = 0$。</p>"
                     "<p>这样的场叫**无源场**（不可压缩流）。"
                     "图上箭头会显示成「鞍点」的样子：左右外流、上下内流，"
                     "净流出为 0。</p>"
                     "<p>$k > -1$ 时 $\\operatorname{div} > 0$（源），"
                     "$k < -1$ 时 $\\operatorname{div} < 0$（汇）—— 状态灯在 $k = -1$ 处翻转。</p>")},
        {"title": "与格林公式的联系",
         "content": ("<p>把格林公式里的被积函数换成" "$\\operatorname{curl}F$，就得到**旋度形式**：</p>"
                     "<p>$\\oint_L F \\cdot d\\mathbf{r} = \\iint_D \\operatorname{curl}F\\,dA$。</p>"
                     "<p>它说明：**沿闭曲线的环量与区域内的总旋度相等**。"
                     "本页的场旋度处处为 0，所以沿任何闭曲线绕一圈的环量都是 0 "
                     "—— 上一节的「无旋场闭曲线积分为 0」正是它的特例（内核自检里有这一条）。</p>"
                     "<p>散度也有对应的**高斯散度定理**："
                     "$\\oint_{\\partial V} F\\cdot d\\mathbf{S} = \\iiint_V "
                     "\\operatorname{div}F\\,dV$ —— 二维版本就是"
                     "$\\oint_L F\\cdot \\mathbf{n}\\,ds = \\iint_D \\operatorname{div}F\\,dA$。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "gradient": build_gradient,
    "surface": build_surface,
    "lagrange": build_lagrange,
    "riemann": build_riemann,
    "polar": build_polar,
    "green": build_green,
    "field": build_field,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="多元微积分 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
