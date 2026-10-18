#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「平面向量」交互网页。

全部数值由 lib/vector_kernel.py 的 sympy 精确内核驱动（含根式化简）：
向量的线性运算、共线判据、仿射组合、基本定理的分解、数量积与夹角、投影、
定比分点、余弦定理都由内核算出，**不手写数字**。

**与 edu-solid-geometry 的边界**：那个技能用「建系 + 向量法」解立体几何
（线面角/二面角/异面直线/点到面距离）；本技能只做**向量本身的运算与几何意义**。

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

import vector_kernel as K                    # noqa: E402
import sympy as sp                           # noqa: E402
from skillkit import cli                     # noqa: E402

# =====================================================================
# 读数表达式 ↔ 内核 的对账机制
# =====================================================================

_MATHENV = {
    "sqrt": math.sqrt, "abs": abs, "min": min, "max": max, "pow": pow,
    "sign": lambda x: (x > 0) - (x < 0), "floor": math.floor, "ceil": math.ceil,
    "PI": math.pi, "E": math.e,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "exp": math.exp, "log": math.log,
}


def _jseval(expr, **env):
    return eval(expr.replace("^", "**"), {"__builtins__": {}}, {**_MATHENV, **env})


def _agree(label, expr, want, tol=1e-9, **env):
    got = _jseval(expr, **env)
    if abs(float(got) - float(want)) > tol:
        raise AssertionError(
            f"读数表达式与内核不一致（{label}）：\n"
            f"  表达式 {expr!r}\n  按表达式算 = {got!r}\n  内核给出   = {want!r}")
    return got


def ro(rid, label, expr, digits=4, unit=None):
    d = {"id": rid, "label": label, "type": "expr", "expr": expr, "digits": digits}
    if unit:
        d["unit"] = unit
    return d


def ro_status(rid, label, expr, rhs=0, op="==", ok="成立", bad="不成立"):
    return {"id": rid, "label": label, "type": "status", "expr": expr,
            "rhs": rhs, "op": op, "okText": ok, "badText": bad}


# =====================================================================
# 1) 向量的加减与数乘
# =====================================================================
def build_add() -> dict:
    A, B, th0 = K.vec(2.5, 0.8), 1.8, 60.0
    b0 = K.vec(B * math.cos(math.radians(th0)), B * math.sin(math.radians(th0)))
    s0 = K.add(A, b0)
    EXPR_X = "2.5+1.8*cos(th*PI/180)"
    EXPR_Y = "0.8+1.8*sin(th*PI/180)"
    EXPR_M = "sqrt(10.13+9*cos(th*PI/180)+2.88*sin(th*PI/180))"
    for th in (0.0, 60.0, 120.0, 200.0, 300.0):
        b = K.vec(B * math.cos(math.radians(th)), B * math.sin(math.radians(th)))
        s = K.add(A, b)
        _agree(f"a+b 的 x(th={th})", EXPR_X, float(s[0]), tol=1e-12, th=th)
        _agree(f"a+b 的 y(th={th})", EXPR_Y, float(s[1]), tol=1e-12, th=th)
        _agree(f"|a+b|(th={th})", EXPR_M, float(K.norm(s)), tol=1e-9, th=th)
    # |a+b|² = |a|² + |b|² + 2a·b（恒等式）
    _agree("|a+b|² = 10.13+9cosθ+2.88sinθ", EXPR_M + "*" + EXPR_M,
           float(K.norm(A) ** 2 + B * B + 2 * K.dot(A, b0)), tol=1e-9, th=th0)
    assert abs(float(K.norm(s0)) - math.hypot(2.5 + 0.9, 0.8 + 1.5588457)) < 1e-6

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "vectoradd", "th": "th",
                  "caption": "蓝 = a（固定）、粉 = b（方向可调）、黄 = a+b"},
        "param": {"name": "th", "label": "$b$ 的方向角 $\\theta$", "min": 0, "max": 355,
                  "step": 5, "value": th0, "unit": "°", "standard": th0,
                  "ticks": ["0", "60 (题设)", "180", "355"]},
        "readouts": [
            ro("x", "$(a+b)_x$", EXPR_X, 4),
            ro("y", "$(a+b)_y$", EXPR_Y, 4),
            ro("m", "$|a+b|$", EXPR_M, 4),
            ro("ma", "$|a|$（定值）", "sqrt(6.89)", 4),
            ro_status("same", "是否与 $a$ 同向（θ=0°）", "th", 0, "==",
                      "同向：|a+b| 最大", "不同向"),
        ],
        "constant": {"of": "ma", "label": "|a| 恒为 √6.89 ≈ 2.625 —— 改变 θ 不动它"},
    }
    lesson = {
        "language": "zh-CN", "title": "向量的加法：三角形法则与平行四边形法则",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>$\\mathbf{a} = (2.5,\\,0.8)$ 固定，"
            "$\\mathbf{b}$ 的长度为 $1.8$、方向角为 $\\theta$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $\\mathbf{a}+\\mathbf{b}$ 的坐标；</li>"
            "<li>拖动滑块改变 $\\theta$，$|\\mathbf{a}+\\mathbf{b}|$ 在什么范围变化？</li>"
            "<li>为什么 $|\\mathbf{a}+\\mathbf{b}| \\le |\\mathbf{a}|+|\\mathbf{b}|$？</li></ol>"),
        "answerLabel": "$\\theta = 60^\\circ$ 时的和向量",
        "answer": f"$\\mathbf{{a}}+\\mathbf{{b}} = ({K.f(float(s0[0]),3)},\\ "
                  f"{K.f(float(s0[1]),3)})$，$|\\mathbf{{a}}+\\mathbf{{b}}| \\approx "
                  f"{K.f(float(K.norm(s0)),3)}$",
    }
    steps = [
        {"title": "三角形法则：首尾相接",
         "content": ("<p>把 $\\mathbf{b}$ 平移到 $\\mathbf{a}$ 的**终点**，"
                     "再从 $\\mathbf{a}$ 的起点指向 $\\mathbf{b}$ 的终点，"
                     "得到的就是 $\\mathbf{a}+\\mathbf{b}$。</p>"
                     "<p>注意向量可以自由平移 —— 判断两个向量是否相等只看"
                     "**长度与方向**，与画在哪里无关。这也是整个向量法的基础。</p>")},
        {"title": "坐标运算",
         "content": ("<p>坐标下加法就是**分量相加**："
                     "$(a_x+b_x,\\ a_y+b_y)$。</p>"
                     f"<p>$\\theta = 60^\\circ$ 时 $\\mathbf{{b}} \\approx "
                     f"({K.f(float(b0[0]),3)},\\ {K.f(float(b0[1]),3)})$，</p>"
                     f"<p>故 $\\mathbf{{a}}+\\mathbf{{b}} \\approx "
                     f"({K.f(float(s0[0]),3)},\\ {K.f(float(s0[1]),3)})$。</p>")},
        {"title": "变化范围与三角不等式",
         "content": ("<p>拖滑块转一圈可以看到：$\\theta = 0^\\circ$（同向）时 "
                     "$|\\mathbf{a}+\\mathbf{b}| = |\\mathbf{a}|+|\\mathbf{b}|$ 最大；"
                     "$\\theta = 180^\\circ$（反向）时等于 "
                     "$\\bigl||\\mathbf{a}|-|\\mathbf{b}|\\bigr|$ 最小。</p>"
                     "<p>中间的值都落在这两者之间 —— 这就是**三角不等式**</p>"
                     "<p>$\\bigl||\\mathbf{a}|-|\\mathbf{b}|\\bigr| \\le "
                     "|\\mathbf{a}+\\mathbf{b}| \\le |\\mathbf{a}|+|\\mathbf{b}|$。</p>"
                     "<p>展开 $|\\mathbf{a}+\\mathbf{b}|^2 = |\\mathbf{a}|^2 + "
                     "2\\mathbf{a}\\cdot\\mathbf{b} + |\\mathbf{b}|^2$ 也能看出："
                     "它的极值由 $\\mathbf{a}\\cdot\\mathbf{b}$ 的符号决定。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 共线定理与三点共线
# =====================================================================
def build_collinear() -> dict:
    A, B = K.vec(0.5, 0.6), K.vec(3.6, 2.4)
    x0 = sp.Rational(3, 10)
    C = K.affine_combo(A, B, x0, 1 - x0)
    EXPR_CX = "x*0.5+(1-x)*3.6"
    EXPR_CY = "x*0.6+(1-x)*2.4"
    EXPR_SUM = "x+(1-x)"
    for x in (0.0, 0.3, 0.5, 1.0, 1.5, -0.5):
        c = K.affine_combo(A, B, sp.nsimplify(x), 1 - sp.nsimplify(x))
        _agree(f"C 的 x(x={x})", EXPR_CX, float(c[0]), tol=1e-12, x=x)
        _agree(f"C 的 y(x={x})", EXPR_CY, float(c[1]), tol=1e-12, x=x)
        _agree(f"系数和(x={x})", EXPR_SUM, 1.0, tol=1e-12, x=x)
        # C 恒在直线 AB 上
        col, _ = K.on_segment_line(A, B, c)
        assert col, f"x={x} 时 C 不在直线 AB 上"
    # C = 0.3·A + 0.7·B = (0.15+2.52, 0.18+1.68) = (2.67, 1.86)
    assert abs(float(C[0]) - 2.67) < 1e-12 and abs(float(C[1]) - 1.86) < 1e-12
    # 系数之和为 1 ⇒ C 在直线 AB 上（精确判据，依赖 vec 用有理数构造）
    assert K.on_segment_line(A, B, C)[0] is True

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "collinear", "x": "x",
                  "caption": "C 沿直线 AB 滑动；它就是 x·A + (1−x)·B"},
        "param": {"name": "x", "label": "系数 $x$", "min": -0.5, "max": 1.5,
                  "step": 0.05, "value": float(x0), "unit": "", "standard": float(x0),
                  "ticks": ["-0.5", "0", "0.3 (题设)", "1", "1.5"]},
        "readouts": [
            ro("cx", "$C_x = x A_x + (1-x) B_x$", EXPR_CX, 4),
            ro("cy", "$C_y$", EXPR_CY, 4),
            ro("sum", "系数之和 $x + (1-x)$", EXPR_SUM, 6),
            ro_status("between", "$C$ 是否在线段 $AB$ 上（0 ≤ x ≤ 1）", "x", 0, ">=",
                      "在线段 AB 上（内分）", "在 AB 的延长线上（外分）"),
        ],
        "constant": {"of": "sum", "label": "系数之和恒为 1 —— 这正是三点共线的判据"},
    }
    lesson = {
        "language": "zh-CN", "title": "共线定理与三点共线",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>已知 $A(0.5,\\,0.6)$、$B(3.6,\\,2.4)$，点 $C$ 满足 "
            "$\\overrightarrow{OC} = x\\,\\overrightarrow{OA} + (1-x)\\,\\overrightarrow{OB}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>$C$ 一定在直线 $AB$ 上吗？为什么？</li>"
            "<li>$x$ 取何值时 $C$ 在线段 $AB$ 上？</li>"
            "<li>若把系数之和改成 2，$C$ 还在直线 $AB$ 上吗？</li></ol>"),
        "answerLabel": "三点共线的判据",
        "answer": "$\\overrightarrow{OC} = x\\overrightarrow{OA} + y\\overrightarrow{OB}$ "
                  "且 $x+y=1$ $\\iff$ $A,B,C$ 共线",
    }
    steps = [
        {"title": "判据：系数之和为 1",
         "content": ("<p>三点 $A,B,C$ 共线 $\\iff$ 存在 $x,y$ 使 "
                     "$\\overrightarrow{OC} = x\\overrightarrow{OA} + "
                     "y\\overrightarrow{OB}$ 且 $x+y=1$。</p>"
                     "<p>直观理解：把 $x$ 看成「$C$ 离 $A$ 有多远」的补数 —— "
                     "$x=1$ 时 $C$ 就是 $A$，$x=0$ 时 $C$ 就是 $B$，"
                     "中间的值对应线段上的点。</p>")},
        {"title": "验证一下",
         "content": ("<p>把坐标代进去：$C = x(0.5,0.6) + (1-x)(3.6,2.4)$，"
                     "整理得 $C = (3.6 - 3.1x,\\ 2.4 - 1.8x)$。</p>"
                     "<p>而 $\\overrightarrow{AB} = (3.1, 1.8)$，"
                     "所以 $\\overrightarrow{AC} = C - A = (3.1(1-x),\\ 1.8(1-x)) "
                     "= (1-x)\\overrightarrow{AB}$ —— 它确实是 $\\overrightarrow{AB}$ 的倍数，"
                     "所以 $C$ 必在直线 $AB$ 上。</p>"
                     f"<p>$x=0.3$ 时 $C = ({K.f(float(C[0]),2)},\\ {K.f(float(C[1]),2)})$。</p>")},
        {"title": "系数和不为 1 会怎样",
         "content": ("<p>若写成 $\\overrightarrow{OC} = x\\overrightarrow{OA} + "
                     "1\\cdot\\overrightarrow{OB}$（系数和为 $x+1$），"
                     "代入得 $C = B + x\\overrightarrow{OA}$ —— 这是「从 $B$ 出发、"
                     "沿 $\\overrightarrow{OA}$ 方向走」，一般**不**在直线 $AB$ 上。</p>"
                     "<p>所以「系数之和为 1」不是可有可无的条件，"
                     "它恰好把 $C$ 钉在直线 $AB$ 上。这也解释了为什么重心可以写成 "
                     "$\\dfrac{A+B+C}{3}$ —— 系数各为 $\\dfrac13$，和为 1。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 平面向量基本定理
# =====================================================================
def build_basis() -> dict:
    E1, E2 = K.vec(1.6, 0.5), K.vec(-0.6, 1.5)
    MU = 2
    lam0 = 1.0
    c0 = K.add(K.scale(lam0, E1), K.scale(MU, E2))
    EXPR_CX = "1.6*lam+2*(-0.6)"
    EXPR_CY = "0.5*lam+2*1.5"
    for lam in (-2.0, -1.0, 0.0, 1.0, 2.0):
        c = K.add(K.scale(lam, E1), K.scale(MU, E2))
        _agree(f"c 的 x(λ={lam})", EXPR_CX, float(c[0]), tol=1e-12, lam=lam)
        _agree(f"c 的 y(λ={lam})", EXPR_CY, float(c[1]), tol=1e-12, lam=lam)
        # 分解唯一性：反解应回到 (λ, 2)
        d = K.decompose(c, E1, E2)
        assert sp.simplify(d[0] - sp.nsimplify(lam)) == 0 and sp.simplify(d[1] - MU) == 0
    _agree("分解的残差", "1.6*lam+2*(-0.6)-(1.6*lam+2*(-0.6))", 0.0, tol=1e-12, lam=lam0)
    # c0 = 1·e1 + 2·e2 = (1.6-1.2, 0.5+3) = (0.4, 3.5)
    assert abs(float(c0[0]) - 0.4) < 1e-12 and abs(float(c0[1]) - 3.5) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "basis", "lam": "lam",
                  "caption": "灰框 = c 在基底 {e₁, e₂} 下分解出的平行四边形"},
        "param": {"name": "lam", "label": "系数 $\\lambda$", "min": -2, "max": 2,
                  "step": 0.05, "value": lam0, "unit": "", "standard": lam0,
                  "ticks": ["-2", "0", "1 (题设)", "2"]},
        "readouts": [
            ro("lam", "$\\lambda$", "lam", 3),
            ro("mu", "$\\mu$（固定为 2）", "2", 2),
            ro("cx", "$c_x$", EXPR_CX, 4),
            ro("cy", "$c_y$", EXPR_CY, 4),
            ro_status("sub", "是否在 $\\lambda = 0$ 处（只剩 $\\mu e_2$）", "abs(lam)", 0, "==",
                      "$c = \\mu e_2$：只有 e₂ 分量", "两个分量都不为零"),
        ],
        "constant": {"of": "uniq", "label": "e₁、e₂ 不共线 ⇒ 任何 c 的分解唯一"},
    }
    lesson = {
        "language": "zh-CN", "title": "平面向量基本定理：分解的存在与唯一",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>取 $\\mathbf{e_1} = (1.6,\\,0.5)$、$\\mathbf{e_2} = (-0.6,\\,1.5)$，"
            "向量 $\\mathbf{c} = \\lambda\\mathbf{e_1} + 2\\mathbf{e_2}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $\\mathbf{c}$ 的坐标；</li>"
            "<li>为什么任何向量都能用 $\\mathbf{e_1},\\mathbf{e_2}$ 唯一表示？</li>"
            "<li>若把 $\\mathbf{e_2}$ 换成 $2\\mathbf{e_1}$，还能唯一分解吗？</li></ol>"),
        "answerLabel": "$\\lambda = 1$ 时的 $c$",
        "answer": f"$\\mathbf{{c}} = ({K.f(float(c0[0]),2)},\\ {K.f(float(c0[1]),2)})$",
    }
    steps = [
        {"title": "分解就是解一个二元一次方程组",
         "content": ("<p>设 $\\mathbf{c} = \\lambda\\mathbf{e_1} + \\mu\\mathbf{e_2}$，"
                     "写成坐标就是</p>"
                     "<p>$\\begin{cases} 1.6\\lambda - 0.6\\mu = c_x \\\\ "
                     "0.5\\lambda + 1.5\\mu = c_y \\end{cases}$</p>"
                     "<p>它的系数行列式是 $1.6\\times1.5 - (-0.6)\\times0.5 = 2.7 \\ne 0$，"
                     "所以**有且只有一组解** —— 这就是「唯一」的来源。</p>")},
        {"title": "几何：唯一性 = 两条线只交一次",
         "content": ("<p>几何上，从 $\\mathbf{c}$ 的终点作两个基向量方向的平行线，"
                     "与「坐标轴」（即 $\\mathbf{e_1}$、$\\mathbf{e_2}$ 所在的两条直线）"
                     "各交于一点 —— 图上的灰框就是这两个交点围成的平行四边形。</p>"
                     "<p>两个交点唯一 $\\iff$ 两条「坐标轴」不重合，"
                     "也就是 $\\mathbf{e_1},\\mathbf{e_2}$ **不共线**。</p>")},
        {"title": "为什么必须不共线",
         "content": ("<p>若把 $\\mathbf{e_2}$ 换成 $2\\mathbf{e_1}$，两个方向重合，"
                     "行列式变成 $0$，方程要么无解、要么有无穷多解 —— "
                     "此时「基底」失效。</p>"
                     "<p>把这件事推广到三维，就得到**空间向量基本定理**："
                     "三个不共面的向量可以唯一表示空间中任何向量。"
                     "立体几何里的「建系」正是它的一个特例（取三个互相垂直的单位向量）。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 数量积与夹角
# =====================================================================
def build_dot() -> dict:
    A = K.vec(2.4, 1.2)
    th0 = 60.0
    EXPR_D = "4.8*cos(th*PI/180)+2.4*sin(th*PI/180)"
    # 必须给分子整体加括号：否则 "A+B/(k)" 里除法只作用于 B —— 这类优先级错
    # 在本项目已复发三次（edu-history 的 A−B、edu-chem-calc 的三目、这里的分式）。
    EXPR_COS = "(" + EXPR_D + ")/(2*sqrt(7.2))"
    EXPR_ANG = "acos(" + EXPR_COS + ")*180/PI"
    EXPR_NA = "sqrt(7.2)"
    for th in (0.0, 45.0, 90.0, 135.0, 180.0):
        b = K.vec(2 * math.cos(math.radians(th)), 2 * math.sin(math.radians(th)))
        _agree(f"a·b(th={th})", EXPR_D, float(K.dot(A, b)), tol=1e-12, th=th)
        _agree(f"|a||b|(th={th})", EXPR_NA + "*2", float(K.norm(A) * K.norm(b)), tol=1e-9, th=th)
        _agree(f"夹角的余弦(th={th})", EXPR_COS, float(K.dot(A, b) / (K.norm(A) * K.norm(b))), tol=1e-9, th=th)
        _agree(f"夹角(th={th})", EXPR_ANG, float(K.angle_deg(A, b)), tol=1e-7, th=th)
    # a = (2.4, 1.2) 的方向角是 arctan(1.2/2.4) = 26.565°，
    # 所以 b 与 a 垂直当且仅当 θ = 116.565°（**不是** 90°）。
    # θ=90° 时 a·b = 4.8·0 + 2.4·1 = 2.4 ≠ 0。
    _agree("θ=90° 时 a·b = 2.4（不垂直）", EXPR_D, 2.4, tol=1e-12, th=90.0)
    _agree("垂直时 a·b = 0", EXPR_D, 0.0, tol=1e-12, th=116.56505117707799)
    assert K.is_perpendicular(A, K.vec(2 * math.cos(math.radians(116.56505117707799)),
                                     2 * math.sin(math.radians(116.56505117707799))))

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "dot", "th": "th",
                  "caption": "黄弧是两向量的夹角；a·b 的正负由夹角是否超过 90° 决定"},
        "param": {"name": "th", "label": "$b$ 的方向角 $\\theta$", "min": 0, "max": 180,
                  "step": 5, "value": th0, "unit": "°", "standard": th0,
                  "ticks": ["0", "26.6 (同向)", "60 (题设)", "116.6 (垂直)", "180"]},
        "readouts": [
            ro("d", "$a\\cdot b$", EXPR_D, 4),
            ro("ang", "两向量的夹角", EXPR_ANG, 3, "°"),
            ro("cs", "$\\cos$ 夹角", EXPR_COS, 4),
            ro("prod", "$|a||b|$（定值）", EXPR_NA + "*2", 4),
            ro_status("perp", "是否垂直（a·b = 0）", "abs(" + EXPR_D + ")", 1e-9, "<",
                      "垂直：a·b = 0", "不垂直"),
        ],
        "constant": {"of": "prod", "label": "|a||b| 恒为 2√7.2 ≈ 5.367 —— 与 θ 无关"},
    }
    lesson = {
        "language": "zh-CN", "title": "数量积与夹角",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>$\\mathbf{a} = (2.4,\\,1.2)$，$\\mathbf{b}$ 长度为 $2$、方向角 $\\theta$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $\\mathbf{a}\\cdot\\mathbf{b}$ 与两向量夹角的关系；</li>"
            "<li>拖动滑块，$\\mathbf{a}\\cdot\\mathbf{b}$ 什么时候为正、为负、为零？</li>"
            "<li>为什么 $\\mathbf{a}\\cdot\\mathbf{b} = 0$ 就是垂直？</li></ol>"),
        "answerLabel": "$\\theta = 60^\\circ$ 时的数量积",
        "answer": f"$\\mathbf{{a}}\\cdot\\mathbf{{b}} = "
                  f"{K.f(float(K.dot(A, K.vec(2 * math.cos(math.radians(th0)), 2 * math.sin(math.radians(th0))))),4)}$",
    }
    steps = [
        {"title": "定义的两种写法",
         "content": ("<p>几何定义：$\\mathbf{a}\\cdot\\mathbf{b} = "
                     "|\\mathbf{a}||\\mathbf{b}|\\cos\\theta$。</p>"
                     "<p>坐标形式：$\\mathbf{a}\\cdot\\mathbf{b} = a_xb_x + a_yb_y$。</p>"
                     "<p>两者相等是**定理**（余弦定理的直接推论），"
                     "它把「长度与夹角」这种几何量与「坐标相乘再相加」这种代数量接了起来 ——"
                     "这是向量法能同时处理几何与代数的根本原因。</p>")},
        {"title": "符号的含义",
         "content": ("<p>$\\cos\\theta$ 的符号决定数量积的符号：</p>"
                     "<p>$\\theta < 90^\\circ$ 时为正（锐角），"
                     "$\\theta = 90^\\circ$ 时为零，$\\theta > 90^\\circ$ 时为负（钝角）。</p>"
                     "<p>图上把 $\\theta$ 拖过 $90^\\circ$，读数立刻从正变负 ——"
                     "这正是「投影方向相反」的代数表现。</p>")},
        {"title": "垂直判据与几个恒等式",
         "content": ("<p>$\\mathbf{a} \\perp \\mathbf{b} \\iff "
                     "\\mathbf{a}\\cdot\\mathbf{b} = 0$。这一条把几何的垂直"
                     "变成了代数的等式，是向量法最好用的工具。</p>"
                     "<p>另外两个常用恒等式（读数区可以相互验算）：</p>"
                     "<p>$|\\mathbf{a}\\pm\\mathbf{b}|^2 = |\\mathbf{a}|^2 \\pm "
                     "2\\mathbf{a}\\cdot\\mathbf{b} + |\\mathbf{b}|^2$；</p>"
                     "<p>$\\mathbf{a}\\cdot\\mathbf{b} = "
                     "\\dfrac{|\\mathbf{a}+\\mathbf{b}|^2 - "
                     "|\\mathbf{a}-\\mathbf{b}|^2}{4}$。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 投影
# =====================================================================
def build_project() -> dict:
    A = K.vec(3.2, 0)
    th0 = 60.0
    EXPR_SP = "2*cos(th*PI/180)"
    EXPR_PX = "2*cos(th*PI/180)"
    EXPR_RY = "2*sin(th*PI/180)"
    for th in (0.0, 60.0, 90.0, 120.0, 180.0):
        b = K.vec(2 * math.cos(math.radians(th)), 2 * math.sin(math.radians(th)))
        _agree(f"数量投影(th={th})", EXPR_SP, float(K.projection_scalar(A, b)), tol=1e-12, th=th)
        pv = K.projection_vec(A, b)
        _agree(f"投影向量 x(th={th})", EXPR_PX, float(pv[0]), tol=1e-12, th=th)
        _agree(f"投影向量 y(th={th})", "0", float(pv[1]), tol=1e-12, th=th)
        rv = K.rejection_vec(A, b)
        _agree(f"垂直分量 y(th={th})", EXPR_RY, float(rv[1]), tol=1e-12, th=th)
        _agree(f"投影 + 垂直分量 = b 的 x(th={th})", EXPR_PX + "+0", float(b[0]), tol=1e-12, th=th)
    _agree("θ=90° 时投影为零", EXPR_SP, 0.0, tol=1e-12, th=90.0)
    assert abs(float(K.projection_scalar(A, K.vec(1, math.sqrt(3)))) - 1.0) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "project", "th": "th",
                  "caption": "绿 = b 在 a 上的投影向量；红虚线 = 垂直分量"},
        "param": {"name": "th", "label": "$b$ 的方向角 $\\theta$", "min": 0, "max": 180,
                  "step": 5, "value": th0, "unit": "°", "standard": th0,
                  "ticks": ["0", "60 (题设)", "90", "180"]},
        "readouts": [
            ro("sp", "数量投影 $\\dfrac{a\\cdot b}{|a|}$", EXPR_SP, 4),
            ro("px", "投影向量的 $x$ 分量", EXPR_PX, 4),
            ro("ry", "垂直分量的 $y$ 分量", EXPR_RY, 4),
            ro("len", "$|a|$（定值）", "3.2", 3),
            ro_status("zero", "$\\theta = 90^\\circ$（投影为零）", "abs(th-90)", 1e-9, "<",
                      "投影为零：b 全在垂直方向", "投影不为零"),
        ],
        "constant": {"of": "len", "label": "|a| 恒为 3.2；a 方向固定沿 x 轴"},
    }
    lesson = {
        "language": "zh-CN", "title": "向量的投影",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>$\\mathbf{a} = (3.2,\\,0)$，$\\mathbf{b}$ 长度为 $2$、方向角 $\\theta$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $\\mathbf{b}$ 在 $\\mathbf{a}$ 上的**数量投影**与**投影向量**；</li>"
            "<li>拖动滑块，投影什么时候为零、什么时候为负？</li>"
            "<li>为什么「投影向量 + 垂直分量 = 原向量」？</li></ol>"),
        "answerLabel": "$\\theta = 60^\\circ$ 时的数量投影",
        "answer": f"$\\dfrac{{\\mathbf{{a}}\\cdot\\mathbf{{b}}}}{{|\\mathbf{{a}}|}} = "
                  f"{K.f(float(K.projection_scalar(A, K.vec(2 * math.cos(math.radians(th0)), 2 * math.sin(math.radians(th0))))),4)}$",
    }
    steps = [
        {"title": "分清「数量投影」与「投影向量」",
         "content": ("<p>**数量投影**是一个**数**："
                     "$\\dfrac{\\mathbf{a}\\cdot\\mathbf{b}}{|\\mathbf{a}|} "
                     "= |\\mathbf{b}|\\cos\\theta$ —— 它是带符号的「影子长度」。</p>"
                     "<p>**投影向量**是一个**向量**："
                     "$\\dfrac{\\mathbf{a}\\cdot\\mathbf{b}}{\\mathbf{a}\\cdot"
                     "\\mathbf{a}}\\mathbf{a}$ —— 方向沿着 $\\mathbf{a}$，"
                     "长度是数量投影的绝对值。</p>"
                     "<p>两者差一个 $\\mathbf{a}$ 方向的单位向量，考试里最容易混。</p>")},
        {"title": "符号与几何",
         "content": ("<p>把 $\\theta$ 拖过 $90^\\circ$，数量投影由正变负 ——"
                     "意味着 $\\mathbf{b}$ 的影子**落到了 $\\mathbf{a}$ 的反方向**上。</p>"
                     "<p>$\\theta = 90^\\circ$ 时投影为零：$\\mathbf{b}$ 完全垂直于 $\\mathbf{a}$，"
                     "在 $\\mathbf{a}$ 方向上没有任何分量。</p>")},
        {"title": "分解的唯一性",
         "content": ("<p>投影向量与垂直分量满足"
                     "$\\mathbf{b} = \\text{proj} + \\text{perp}$，"
                     "且后者垂直于 $\\mathbf{a}$。</p>"
                     "<p>这给出 $\\mathbf{b}$ 在「沿 $\\mathbf{a}$」与「垂直 $\\mathbf{a}$」"
                     "两个方向上的**正交分解** —— 它是傅里叶分解、最小二乘、"
                     "以及物理里「把力分解到沿运动方向与垂直方向」的共同原型。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 力的合成与余弦定理
# =====================================================================
def build_resolve() -> dict:
    F1m, F2m = 2.6, 3.0
    th0 = 60.0
    EXPR_R = "sqrt(15.76+15.6*cos(th*PI/180))"
    for th in (0.0, 60.0, 90.0, 120.0, 180.0):
        _agree(f"合力(th={th})", EXPR_R, float(K.resultant_mag(F1m, F2m, th)), tol=1e-9, th=th)
    _agree("同向时合力 = 5.6", EXPR_R, F1m + F2m, tol=1e-9, th=0.0)
    _agree("反向时合力 = 0.4", EXPR_R, abs(F1m - F2m), tol=1e-9, th=180.0)
    _agree("垂直时合力 = √(F₁²+F₂²)", EXPR_R, math.hypot(F1m, F2m), tol=1e-9, th=90.0)
    _agree("余弦定理同式", EXPR_R, float(K.cosine_rule(F1m, F2m, 180.0 - th0)), tol=1e-9, th=th0)
    assert abs(float(K.resultant_mag(1, 1, 120)) - 1.0) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "resolve", "th": "th",
                  "caption": "F₁、F₂ 首尾相接；黄箭头就是从起点到终点的合力"},
        "param": {"name": "th", "label": "两力的夹角 $\\theta$", "min": 0, "max": 180,
                  "step": 5, "value": th0, "unit": "°", "standard": th0,
                  "ticks": ["0", "60 (题设)", "90", "120", "180"]},
        "readouts": [
            ro("r", "合力大小 $|F_1+F_2|$", EXPR_R, 4),
            ro("f1", "$|F_1|$（定值）", "2.6", 2),
            ro("f2", "$|F_2|$（定值）", "3.0", 2),
            ro("lo", "下界 $\\bigl||F_1|-|F_2|\\bigr|$", "0.4", 2),
            ro_status("max", "是否同向（θ=0°）", "th", 0, "==",
                      "同向：合力最大 = 5.6", "不同向"),
        ],
        "constant": {"of": "f1", "label": "两个分力的大小固定（2.6 与 3.0），只改夹角"},
    }
    lesson = {
        "language": "zh-CN", "title": "力的合成与余弦定理",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>两个力大小分别为 $2.6$ 与 $3.0$，夹角为 $\\theta$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出合力大小的表达式；</li>"
            "<li>$\\theta = 120^\\circ$ 且两力等大时，合力是多少？</li>"
            "<li>为什么合力一定在 $0.4$ 与 $5.6$ 之间？</li></ol>"),
        "answerLabel": "$\\theta = 60^\\circ$ 时的合力",
        "answer": f"$|F_1+F_2| = "
                  f"{K.f(float(K.resultant_mag(F1m, F2m, th0)),4)}$",
    }
    steps = [
        {"title": "首尾相接，第三边就是合力",
         "content": ("<p>把 $F_1$、$F_2$ 首尾相接，从起点到终点的向量就是合力 "
                     "$F_1+F_2$。</p>"
                     "<p>于是在这个三角形里，已知两边及其**夹角**，"
                     "求第三边 —— 正是**余弦定理**的场景。</p>")},
        {"title": "用余弦定理写出来",
         "content": ("<p>注意三角形里 $F_1$、$F_2$ 所夹的**内角**是 $180^\\circ-\\theta$，"
                     "而 $\\cos(180^\\circ-\\theta) = -\\cos\\theta$，所以</p>"
                     "<p>$|F_1+F_2|^2 = F_1^2 + F_2^2 + 2F_1F_2\\cos\\theta$。</p>"
                     "<p>这就是平行四边形的对角线公式。"
                     f"代入 $F_1=2.6$、$F_2=3.0$、$\\theta=60^\\circ$ 得 "
                     f"$|F| \\approx {K.f(float(K.resultant_mag(F1m, F2m, th0)),4)}$。</p>")},
        {"title": "两个极端与一个特例",
         "content": ("<p>拖到 $\\theta = 0^\\circ$（同向）：合力 $= F_1+F_2 = 5.6$ 最大；"
                     "拖到 $180^\\circ$（反向）：合力 $= |F_1-F_2| = 0.4$ 最小。"
                     "中间夹角都落在两者之间。</p>"
                     "<p><b>特例</b>：两个**等大**的力夹角为 $120^\\circ$ 时，"
                     "合力恰好等于分力大小（因为 $1+1+2\\cos120^\\circ = 1$）。"
                     "这个结论在物理里很常用，可以直接记住。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 定比分点
# =====================================================================
def build_section() -> dict:
    A, B = K.vec(0.6, 0.6), K.vec(3.8, 2.6)
    lam0 = 1.0
    P0 = K.section_point(A, B, sp.Integer(1))
    EXPR_PX = "(0.6+lam*3.8)/(1+lam)"
    EXPR_PY = "(0.6+lam*2.6)/(1+lam)"
    for lam in (-0.9, -0.5, 0.0, 1.0, 2.0, 3.0):
        P = K.section_point(A, B, sp.nsimplify(lam))
        _agree(f"P 的 x(λ={lam})", EXPR_PX, float(P[0]), tol=1e-12, lam=lam)
        _agree(f"P 的 y(λ={lam})", EXPR_PY, float(P[1]), tol=1e-12, lam=lam)
        col, _ = K.on_segment_line(A, B, P)
        assert col, f"λ={lam} 时定比分点不在直线 AB 上"
    _agree("λ=1 时是中点", EXPR_PX, float((A[0] + B[0]) / 2), tol=1e-12, lam=1.0)
    _agree("λ=1 时是中点(y)", EXPR_PY, float((A[1] + B[1]) / 2), tol=1e-12, lam=1.0)
    assert list(P0) == [sp.Rational(11, 5), sp.Rational(8, 5)]

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "section", "lam": "lam",
                  "caption": "P 沿直线 AB 移动：λ>0 内分、λ<0 外分、λ=1 是中点"},
        "param": {"name": "lam", "label": "比值 $\\lambda$", "min": -0.9, "max": 3,
                  "step": 0.05, "value": lam0, "unit": "", "standard": lam0,
                  "ticks": ["-0.9", "0", "1 (中点)", "3"]},
        "readouts": [
            ro("px", "$P_x$", EXPR_PX, 4),
            ro("py", "$P_y$", EXPR_PY, 4),
            ro("ratio", "$AP : PB$", "lam", 3),
            ro_status("mid", "是否中点（λ = 1）", "abs(lam-1)", 1e-9, "<",
                      "λ = 1：P 恰为中点", "不是中点"),
        ],
        "constant": {"of": "den", "label": "公式 P = (A + λB)/(1 + λ) 中的分母 1+λ 恒为定比分母"},
    }
    lesson = {
        "language": "zh-CN", "title": "定比分点",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>$A(0.6,\\,0.6)$、$B(3.8,\\,2.6)$，点 $P$ 在直线 $AB$ 上且 "
            "$\\overrightarrow{AP} = \\lambda\\,\\overrightarrow{PB}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>用 $\\lambda$ 表示 $P$ 的坐标；</li>"
            "<li>$\\lambda$ 取何值时 $P$ 是中点？</li>"
            "<li>拖动滑块到 $\\lambda < 0$，$P$ 跑到哪里去了？</li></ol>"),
        "answerLabel": "$\\lambda = 1$（中点）",
        "answer": f"$P = \\left(\\dfrac{{A+\\lambda B}}{{1+\\lambda}}\\right)$；"
                  f"$\\lambda=1$ 时 $P = ({K.f(float(P0[0]),2)},\\ {K.f(float(P0[1]),2)})$",
    }
    steps = [
        {"title": "公式怎么来的",
         "content": ("<p>$\\overrightarrow{AP} = \\lambda\\overrightarrow{PB}$ "
                     "说明 $A,P,B$ 三点共线，且 $P$ 把 $AB$ **按 $\\lambda:1$ 分**。</p>"
                     "<p>把它写成 $P - A = \\lambda(B - P)$，整理得</p>"
                     "<p>$P = \\dfrac{A + \\lambda B}{1+\\lambda}$。</p>"
                     "<p>$\\lambda = 1$ 时分子分母都除以 2，得到 "
                     "$P = \\dfrac{A+B}{2}$ —— 中点公式。</p>")},
        {"title": "内分、外分与 λ 的正负",
         "content": ("<p>$\\lambda > 0$ 时 $P$ 在 $A$、$B$ **之间**（内分）；"
                     "$\\lambda < 0$ 时 $P$ 在 $AB$ 的**延长线**上（外分）。</p>"
                     "<p>把滑块从 $3$ 拖到 $-0.9$ 可以看到 $P$ 先向 $B$ 靠、"
                     "越过 $B$ 后从另一侧跑出去 —— 但**始终在直线 $AB$ 上**。</p>"
                     "<p>$\\lambda = -1$ 时分母为零，公式失效：那对应「$A$ 与 $B$ "
                     "在同一点的两侧等距」，唯一能满足的点在无穷远。"
                     "本页的滑块范围刻意避开了 $\\lambda = -1$。</p>")},
        {"title": "与重心的联系",
         "content": ("<p>三角形重心 $G = \\dfrac{A+B+C}{3}$："
                     "三个系数都是 $\\dfrac13$，**和为 1** ——"
                     "这正是上一节「系数和为 1 ⇒ 共线」那套办法的推广"
                     "（三个系数和为 1 的点落在三角形所在平面内）。</p>"
                     "<p>定比分点在解析几何里用得极多：求中点、求重心、"
                     "求直线与线段的交点，都归结为这一条公式。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "add": build_add,
    "collinear": build_collinear,
    "basis": build_basis,
    "dot": build_dot,
    "project": build_project,
    "resolve": build_resolve,
    "section": build_section,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="平面向量 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
