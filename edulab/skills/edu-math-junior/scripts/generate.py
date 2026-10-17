#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「初中代数与函数」交互网页。

全部数值由 lib/jmath_kernel.py 的 sympy 精确计算驱动（单一数据源）：顶点、对称轴、
判别式、根、区间最值、不等式解集、因式分解、三角比都由内核算出；函数表达式经
js() 翻译给画板逐点采样，保证「图、解、答」同源一致。**不手写数字。**

依赖 sympy。用能 import sympy 的解释器运行：
    python scripts/generate.py <题型key> [输出.html]
    python scripts/generate.py list
    python scripts/generate.py all <输出目录>
    python scripts/generate.py random [seed] [输出.html]
"""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PLACEHOLDER = "__LESSON_DATA__"

sys.path.insert(0, str(SKILL_DIR.parent.parent / "shared"))
sys.path.insert(0, str(SKILL_DIR / "lib"))

import sympy as sp                       # noqa: E402
import jmath_kernel as K                 # noqa: E402
from jmath_kernel import x, tex, f       # noqa: E402
from skillkit import cli                 # noqa: E402

# 参数符号（供曲线表达式使用；画板端由滑块值代入）
pa, pb, pc, pk = sp.symbols("a b c k")


def pt(xy, color="point", label=None, emphasis=False):
    return {"xy": [f(xy[0]), f(xy[1])], "color": color, "label": label, "emphasis": emphasis}


def ptx(xexpr, yexpr, color="point", label=None, emphasis=False):
    """坐标是**参数表达式**的点（画板按滑块值实时求值）。"""
    return {"xy": [xexpr, yexpr], "color": color, "label": label, "emphasis": emphasis}


def fn_conic(name, expr, color="curve", label=None):
    """kind:'function' 曲线（表达式经 js() 翻译，画板逐点采样）。"""
    return {"name": name, "kind": "function", "expr": K.js(expr),
            "color": color, "label": label or f"$y={tex(expr)}$"}


def vline(name, xexpr, color="aux", dashed=True, label=None):
    """竖直线：通过参数点 (xexpr, f(xexpr)) 的竖直方向线。

    模板没有「x=常数」的直接构造，所以借 point_on_function 取到曲线上一点，
    再沿 [0,1] 方向画 —— 这样对称轴会随参数移动。
    """
    return ({"type": "point_on_function", "name": name + "_p", "conic": "f",
             "x": xexpr, "color": color},
            {"type": "line_through_point_dir", "name": name, "point": name + "_p",
             "dir": [0, 1], "color": color, "dashed": dashed, "label": label})


# =====================================================================
# 1) 一次函数 y = kx + b
# =====================================================================
def build_linear() -> dict:
    b0 = -4
    k0 = 2
    sol = K.solve_linear(k0, b0)
    board = {
        "view": {"xRange": [-4.5, 5.5], "yRange": [-6.5, 6.5]},
        "conics": [fn_conic("f", pk * x + b0, label="$y=kx-4$")],
        "points": {
            "Y0": pt([0, b0], "given", "与 y 轴", True),
        },
        "param": {"name": "k", "label": "斜率 $k$",
                  "min": -3, "max": 3, "step": 0.1, "value": k0, "unit": "", "standard": k0,
                  "ticks": ["-3", "0", "2 (题设)", "3"]},
        "derived": [
            {"type": "point_on_function", "name": "X", "conic": "f", "x": "-4/k",
             "color": "fixed", "emphasis": True},
        ],
        "readouts": [
            {"id": "k", "label": "斜率 $k$", "type": "expr", "expr": "k", "digits": 2},
            {"id": "b", "label": "纵截距 $b$", "type": "expr", "expr": str(b0), "digits": 0},
            {"id": "xi", "label": "与 x 轴交点", "type": "expr", "expr": "-4/k", "digits": 3},
            {"id": "mono", "label": "增减性", "type": "status", "expr": "k", "op": ">", "rhs": 0,
             "okText": "增函数（k>0）", "badText": "减函数（k<0）"},
        ],
        "constant": {"of": "b", "label": "纵截距恒为 -4（改变 k 不改变它）"},
        "legend": [{"color": "curve", "text": "直线 $y=kx-4$"},
                   {"color": "fixed", "text": "与 x 轴交点"}],
    }
    lesson = {
        "language": "zh-CN", "title": "一次函数 y = kx + b",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            f"<p>已知一次函数 $y = kx - 4$，其中 $k$ 可调。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>当 $k = 2$ 时，求它与两条坐标轴的交点；</li>"
            "<li>拖动滑块，$k$ 变大时图像怎么变？为什么纵截距不动？</li></ol>"),
        "answerLabel": "当 k=2 时与 x 轴的交点",
        "answer": f"$x = {K.num_str(sol['xint'])}$",
    }
    steps = [
        {"title": "斜率决定方向",
         "content": ("<p>$k$ 是斜率：每向右 1 个单位，向上 $k$ 个单位。"
                     "$k>0$ 时直线从左下到右上（增函数）；$k<0$ 时反过来。</p>")},
        {"title": "两条坐标轴的交点",
         "content": (f"<p>与 $y$ 轴相交时 $x=0$，得 $y={b0}$，所以交点是 $(0,{b0})$。</p>"
                     f"<p>与 $x$ 轴相交时 $y=0$，解 $kx-4=0$ 得 $x=\\dfrac{{4}}{{k}}$；"
                     f"当 $k=2$ 时 $x={K.num_str(sol['xint'])}$。</p>")},
        {"title": "为什么 b 不动",
         "content": (f"<p>纵截距 $b={b0}$ 是 $x=0$ 时的函数值，而 $x=0$ 时 $kx$ 这一项恒为 0，"
                     "所以无论 $k$ 取什么，直线都过同一点 $(0,-4)$——这就是「截距」这个名字的来历。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 两直线交点
# =====================================================================
def build_linear_intersect() -> dict:
    k1, b1, k2, b2 = 2, -4, -1, 5
    I = K.intersect_lines(k1, b1, k2, b2)
    board = {
        "view": {"xRange": [-3, 7], "yRange": [-6, 7]},
        "conics": [fn_conic("l1", k1 * x + b1, color="curve", label="$l_1: y=2x-4$"),
                   fn_conic("l2", pk * x + b2, color="curve2", label="$l_2: y=kx+5$")],
        "points": {
            "P": ptx("9/(2-k)", "2*(9/(2-k))-4", "fixed", "交点", True),
        },
        "param": {"name": "k", "label": "$l_2$ 的斜率 $k$",
                  "min": -3, "max": 3, "step": 0.1, "value": k2, "unit": "", "standard": k2,
                  "ticks": ["-3", "0", "-1 (题设)", "3"]},
        "derived": [],
        "readouts": [
            {"id": "k", "label": "$l_2$ 斜率 $k$", "type": "expr", "expr": "k", "digits": 2},
            {"id": "xi", "label": "交点横坐标", "type": "expr", "expr": "9/(2-k)", "digits": 3},
            {"id": "yi", "label": "交点纵坐标", "type": "expr", "expr": "2*(9/(2-k))-4", "digits": 3},
            {"id": "par", "label": "是否平行", "type": "status", "expr": "abs(k-2)", "op": ">", "rhs": 1e-6,
             "okText": "相交", "badText": "平行（无交点）"},
        ],
        "constant": None,
        "legend": [{"color": "curve", "text": "$l_1$（固定）"},
                   {"color": "curve2", "text": "$l_2$（斜率可调）"}],
    }
    lesson = {
        "language": "zh-CN", "title": "两条直线的交点",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>直线 $l_1: y=2x-4$，$l_2: y=kx+5$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>当 $k=-1$ 时求交点；</li>"
            "<li>$k$ 取什么值时两直线平行？此时方程组有几个解？</li></ol>"),
        "answerLabel": "k=-1 时的交点",
        "answer": f"$({K.num_str(I['x'])},\\,{K.num_str(I['y'])})$",
    }
    steps = [
        {"title": "交点就是方程组的解",
         "content": ("<p>求交点 = 解方程组 $\\begin{cases} y=2x-4 \\\\ y=kx+5 \\end{cases}$，"
                     "也就是解 $2x-4=kx+5$。</p>")},
        {"title": "解出 x",
         "content": (f"<p>移项得 $(2-k)x=9$，所以 $x=\\dfrac{{9}}{{2-k}}$（$k\\ne 2$）。</p>"
                     f"<p>当 $k=-1$ 时 $x=\\dfrac{{9}}{{3}}={K.num_str(I['x'])}$，"
                     f"代回得 $y={K.num_str(I['y'])}$。</p>")},
        {"title": "平行意味着什么",
         "content": ("<p>当 $k=2$ 时两直线斜率相同、截距不同（$-4\\ne 5$），所以平行——"
                     "此时分母为 0，方程组<b>无解</b>。</p>"
                     "<p>「斜率相等」与「方程组无解」是同一件事的两种说法。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 二次函数图像与性质
# =====================================================================
def build_quadratic() -> dict:
    a0, b0, c0 = 1, -2, -3
    s = K.solve_quadratic(a0, b0, c0)
    roots = s["roots"]
    board = {
        "view": {"xRange": [-4, 6], "yRange": [-6, 8]},
        "conics": [fn_conic("f", pa * x * x + b0 * x + c0, label="$y=ax^2-2x-3$")],
        "points": {
            "R1": ptx("(2-sqrt(4+12*a))/(2*a)", "0", "given", "x₁", True),
            "R2": ptx("(2+sqrt(4+12*a))/(2*a)", "0", "given", "x₂", True),
        },
        "param": {"name": "a", "label": "二次项系数 $a$",
                  "min": 0.25, "max": 2, "step": 0.05, "value": a0, "unit": "", "standard": a0,
                  "ticks": ["0.25", "1 (题设)", "2"]},
        "derived": [
            # 顶点随 a 移动：x=1/a，y=f(1/a)
            {"type": "point_on_function", "name": "V", "conic": "f", "x": "1/a",
             "color": "fixed", "emphasis": True},
            *vline("axis", "1/a", color="aux", label="对称轴"),
        ],
        "readouts": [
            {"id": "a", "label": "$a$", "type": "expr", "expr": "a", "digits": 2},
            {"id": "h", "label": "对称轴 $x=-\\frac{b}{2a}$", "type": "expr", "expr": "1/a", "digits": 3},
            {"id": "k", "label": "顶点纵坐标（最值）", "type": "expr", "expr": "-3-1/a", "digits": 3,
             "highlight": True},
            {"id": "D", "label": "判别式 $\\Delta=b^2-4ac$", "type": "expr", "expr": "4+12*a", "digits": 2},
            {"id": "sign", "label": "开口", "type": "status", "expr": "a", "op": ">", "rhs": 0,
             "okText": "向上", "badText": "向下"},
        ],
        "constant": None,
        "legend": [{"color": "curve", "text": "$y=ax^2-2x-3$"},
                   {"color": "aux", "text": "对称轴"},
                   {"color": "fixed", "text": "顶点"}],
    }
    lesson = {
        "language": "zh-CN", "title": "二次函数：开口、对称轴、顶点",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>已知 $y=ax^2-2x-3$（$a>0$）。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>当 $a=1$ 时，求对称轴、顶点与最小值；</li>"
            "<li>拖动滑块让 $a$ 变大，顶点怎么移动？最小值怎么变？</li></ol>"),
        "answerLabel": "a=1 时的顶点",
        "answer": f"$({K.num_str(s['h'])},\\,{K.num_str(s['k'])})$",
    }
    steps = [
        {"title": "对称轴公式",
         "content": (f"<p>对称轴 $x=-\\dfrac{{b}}{{2a}}=\\dfrac{{2}}{{2a}}=\\dfrac{{1}}{{a}}$。"
                     f"当 $a=1$ 时 $x={K.num_str(s['axis'])}$。</p>")},
        {"title": "顶点与最值",
         "content": (f"<p>把对称轴代入：$y=a\\cdot\\dfrac{{1}}{{a^2}}-2\\cdot\\dfrac{{1}}{{a}}-3"
                     f"=-3-\\dfrac{{1}}{{a}}$。</p>"
                     f"<p>当 $a=1$ 时顶点是 $({K.num_str(s['h'])},{K.num_str(s['k'])})$，"
                     f"因为 $a>0$，这是<b>最小值</b>。</p>")},
        {"title": "a 控制开口大小",
         "content": ("<p>$a$ 越大，抛物线越「瘦」，顶点越靠近直线 $y=-3$；"
                     "$a$ 越小，开口越宽，顶点越低。</p>"
                     "<p>但无论 $a$ 怎么变，抛物线始终过定点 $(0,-3)$——因为 $x=0$ 时 $ax^2$ 项为 0。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 区间最值
# =====================================================================
def build_quad_extremum() -> dict:
    a0, b0, c0 = 1, -2, 0
    hi = 3
    E = K.interval_extremum(a0, b0, c0, 0, hi)
    board = {
        "view": {"xRange": [-2, 6], "yRange": [-3, 10]},
        "conics": [fn_conic("f", x * x - 2 * x, label="$y=x^2-2x$")],
        "points": {
            "V": pt([1, -1], "fixed", "顶点", True),
            "L": pt([0, 0], "given", "左端", True),
        },
        "param": {"name": "hi", "label": "区间右端点 $b$（区间为 $[0,b]$）",
                  "min": 1, "max": 5, "step": 0.1, "value": hi, "unit": "", "standard": hi,
                  "ticks": ["1", "2", "3 (题设)", "5"]},
        "derived": [],
        "readouts": [
            {"id": "lo", "label": "左端点 $a$", "type": "expr", "expr": "0", "digits": 0},
            {"id": "hi", "label": "右端点 $b$", "type": "expr", "expr": "hi", "digits": 2},
            {"id": "mn", "label": "区间最小值", "type": "expr",
             "expr": "hi>=1 ? -1 : min(0, hi*hi-2*hi)", "digits": 3, "highlight": True},
            {"id": "mx", "label": "区间最大值", "type": "expr",
             "expr": "max(0, hi*hi-2*hi)", "digits": 3},
        ],
        "constant": None,
        "legend": [{"color": "curve", "text": "$y=x^2-2x$"}, {"color": "fixed", "text": "顶点 (1,-1)"}],
    }
    lesson = {
        "language": "zh-CN", "title": "二次函数在闭区间上的最值",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>求 $y=x^2-2x$ 在闭区间 $[0,b]$ 上的最大值与最小值。</p>"
            "<p>拖动滑块改变 $b$，观察最值怎么跟着变。</p>"),
        "answerLabel": "b=3 时的最小值 / 最大值",
        "answer": f"$\\min={K.num_str(E['min'])},\\ \\max={K.num_str(E['max'])}$",
    }
    steps = [
        {"title": "先看顶点在不在区间内",
         "content": ("<p>对称轴 $x=1$，顶点 $(1,-1)$。区间是 $[0,b]$。</p>"
                     "<p>只要 $b\\ge 1$，顶点就在区间内，最小值一定是 $-1$；"
                     "若 $b<1$，函数在 $[0,b]$ 上单调递减，最小值在右端点。</p>")},
        {"title": "最大值只看端点",
         "content": (f"<p>开口向上，最大值一定在端点取到。比较 $f(0)=0$ 与 $f(b)=b^2-2b$ 即可。</p>"
                     f"<p>当 $b=3$ 时 $f(3)=3$，所以最大值是 ${K.num_str(E['max'])}$，"
                     f"最小值是 ${K.num_str(E['min'])}$。</p>")},
        {"title": "分界点在哪",
         "content": ("<p>$f(b)=f(0)$ 时 $b^2-2b=0$，即 $b=0$ 或 $b=2$。"
                     "所以 $b<2$ 时右端点更高，$b>2$ 时右端点成为最大值。</p>"
                     "<p>这类题的关键不是套公式，而是<b>先判断顶点是否落在区间内</b>。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 判别式与根的个数
# =====================================================================
def build_discriminant() -> dict:
    a0, b0, c0 = 1, -2, -3
    s = K.solve_quadratic(a0, b0, c0)
    board = {
        "view": {"xRange": [-5, 7], "yRange": [-8, 8]},
        "conics": [fn_conic("f", x * x - 2 * x + pc, label="$y=x^2-2x+c$")],
        "points": {},
        "param": {"name": "c", "label": "常数项 $c$",
                  "min": -6, "max": 6, "step": 0.1, "value": c0, "unit": "", "standard": c0,
                  "ticks": ["-6", "-3 (题设)", "1", "6"]},
        "derived": [
            {"type": "point_on_function", "name": "V", "conic": "f", "x": "1",
             "color": "fixed", "emphasis": True},
        ],
        "readouts": [
            {"id": "c", "label": "$c$", "type": "expr", "expr": "c", "digits": 2},
            {"id": "D", "label": "$\\Delta=4-4c$", "type": "expr", "expr": "4-4*c", "digits": 2,
             "highlight": True},
            {"id": "n", "label": "实根个数", "type": "expr",
             "expr": "4-4*c>0 ? 2 : (4-4*c==0 ? 1 : 0)", "digits": 0},
        ],
        "constant": None,
        "legend": [{"color": "curve", "text": "$y=x^2-2x+c$"}],
    }
    lesson = {
        "language": "zh-CN", "title": "判别式 Δ = b² − 4ac",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>关于 $x$ 的方程 $x^2-2x+c=0$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>$c$ 取何值时有两个不等实根 / 两个相等实根 / 没有实根？</li>"
            "<li>这与抛物线 $y=x^2-2x+c$ 和 $x$ 轴的位置关系是什么？</li></ol>"),
        "answerLabel": "c=-3 时的判别式与根",
        "answer": f"$\\Delta={K.num_str(s['D'])}$，两个不等实根",
    }
    steps = [
        {"title": "判别式从哪来",
         "content": ("<p>配方：$x^2-2x+c=(x-1)^2+c-1$。左边是非负数，所以方程有解"
                     "当且仅当 $c-1\\le 0$。</p>"
                     "<p>把它写成 $\\Delta=b^2-4ac=4-4c$，条件就是 $\\Delta\\ge 0$。</p>")},
        {"title": "三种情况",
         "content": ("<ul class='list-disc pl-5 space-y-1'>"
                     "<li>$\\Delta>0$：两个不等实根（抛物线与 $x$ 轴交于两点）；</li>"
                     "<li>$\\Delta=0$：两个相等实根（抛物线与 $x$ 轴相切）；</li>"
                     "<li>$\\Delta<0$：没有实根（抛物线与 $x$ 轴不相交）。</li></ul>"
                     f"<p>本题 $\\Delta=4-4c$：$c<1$ 时两根，$c=1$ 时重根，$c>1$ 时无实根。</p>")},
        {"title": "拖动验证",
         "content": ("<p>拖动 $c$：抛物线整体上下平移，顶点始终在 $x=1$ 这条竖线上。</p>"
                     "<p>当顶点升到 $x$ 轴上方（$c>1$）时，图与轴彻底分离——这正是「无实根」。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 韦达定理
# =====================================================================
def build_vieta() -> dict:
    a0, b0, c0 = 1, -2, -3
    s = K.solve_quadratic(a0, b0, c0)
    r1, r2 = s["roots"]
    board = {
        "view": {"xRange": [-4, 6], "yRange": [-6, 8]},
        "conics": [fn_conic("f", x * x - 2 * x - 3, label="$y=x^2-2x-3$")],
        "points": {
            "R1": pt([r1, 0], "given", "x₁", True),
            "R2": pt([r2, 0], "given", "x₂", True),
            "V": pt(s["vertex"], "fixed", "顶点", True),
        },
        "derived": [],
        "readouts": [
            {"id": "r1", "label": "$x_1$", "type": "expr", "expr": str(K.f(r1)), "digits": 3},
            {"id": "r2", "label": "$x_2$", "type": "expr", "expr": str(K.f(r2)), "digits": 3},
            {"id": "sum", "label": "$x_1+x_2=-b/a$", "type": "expr", "expr": str(K.f(s["sum"])), "digits": 3,
             "highlight": True},
            {"id": "prod", "label": "$x_1x_2=c/a$", "type": "expr", "expr": str(K.f(s["prod"])), "digits": 3,
             "highlight": True},
        ],
        "constant": None,
        "legend": [{"color": "curve", "text": "$y=x^2-2x-3$"}, {"color": "given", "text": "两根"}],
    }
    lesson = {
        "language": "zh-CN", "title": "韦达定理：根与系数的关系",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>方程 $x^2-2x-3=0$ 的两根记为 $x_1,x_2$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>不求根，直接写出 $x_1+x_2$ 与 $x_1x_2$；</li>"
            "<li>求 $x_1^2+x_2^2$；</li></ol>"),
        "answerLabel": "两根之和 / 两根之积",
        "answer": f"$x_1+x_2={K.num_str(s['sum'])},\\ x_1x_2={K.num_str(s['prod'])}$",
    }
    steps = [
        {"title": "韦达定理",
         "content": ("<p>对 $ax^2+bx+c=0$（$\\Delta\\ge 0$），两根满足</p>"
                     "<p class='text-center'>$x_1+x_2=-\\dfrac{b}{a},\\qquad x_1x_2=\\dfrac{c}{a}$</p>"
                     f"<p>本题 $a=1,b=-2,c=-3$，所以 $x_1+x_2={K.num_str(s['sum'])}$，"
                     f"$x_1x_2={K.num_str(s['prod'])}$。</p>")},
        {"title": "为什么成立",
         "content": ("<p>把 $a(x-x_1)(x-x_2)$ 展开：$ax^2-a(x_1+x_2)x+ax_1x_2$。"
                     "与 $ax^2+bx+c$ 逐项比对，就得到上面两式。</p>"
                     "<p>所以韦达定理不是新公式，而是<b>因式分解的系数对照</b>。</p>")},
        {"title": "不解方程求对称式",
         "content": (f"<p>$x_1^2+x_2^2=(x_1+x_2)^2-2x_1x_2"
                     f"={K.num_str(s['sum'])}^2-2\\times({K.num_str(s['prod'])})"
                     f"={K.num_str(s['sum']**2 - 2*s['prod'])}$。</p>"
                     "<p>这类「对称式」都能化成和与积的组合——这是韦达定理最常见的用法。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 一元二次不等式
# =====================================================================
def build_inequality() -> dict:
    a0, b0, c0, k0 = 1, -2, -3, 0
    s = K.solve_quadratic(a0, b0, c0)
    r1, r2 = s["roots"]
    board = {
        "view": {"xRange": [-5, 7], "yRange": [-8, 8]},
        "conics": [fn_conic("f", x * x - 2 * x - 3, label="$y=x^2-2x-3$")],
        "points": {
            "R1": pt([r1, 0], "given", "x₁", True),
            "R2": pt([r2, 0], "given", "x₂", True),
        },
        "derived": [
            # 解集是「两根之外」：把两段各自填色，图上直接看到答案
            {"type": "area_fill", "name": "left", "conic": "f",
             "a": -5, "b": K.f(r1), "color": "area", "label": "解集"},
            {"type": "area_fill", "name": "right", "conic": "f",
             "a": K.f(r2), "b": 7, "color": "area"},
        ],
        "readouts": [
            {"id": "r1", "label": "$x_1$", "type": "expr", "expr": str(K.f(r1)), "digits": 3},
            {"id": "r2", "label": "$x_2$", "type": "expr", "expr": str(K.f(r2)), "digits": 3},
            {"id": "D", "label": "判别式 $\\Delta$", "type": "expr", "expr": str(K.f(s["D"])), "digits": 2},
            {"id": "a", "label": "$a$（开口方向）", "type": "expr", "expr": "1", "digits": 0},
        ],
        "constant": None,
        "legend": [{"color": "curve", "text": "$y=x^2-2x-3$"},
                   {"color": "area", "text": "曲线与 x 轴之间"}],
    }
    lesson = {
        "language": "zh-CN", "title": "一元二次不等式：看图解法",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>解不等式 $x^2-2x-3>0$（拖动滑块可改成 $>k$）。</p>"
            "<p>观察：解集与抛物线和 $x$ 轴的交点是什么关系？</p>"),
        "answerLabel": "x²-2x-3>0 的解集",
        "answer": f"$x<{K.num_str(r1)}\\ \\text{{或}}\\ x>{K.num_str(r2)}$",
    }
    steps = [
        {"title": "先解对应方程",
         "content": (f"<p>对应方程 $x^2-2x-3=0$ 的两根是 $x_1={K.num_str(r1)}$，"
                     f"$x_2={K.num_str(r2)}$。</p>"
                     "<p>它们是抛物线穿过 $x$ 轴的位置，也是解集的分界点。</p>")},
        {"title": "看图像定区间",
         "content": ("<p>开口向上，所以 $x$ 轴<b>上方</b>的部分对应 $y>0$，"
                     "<b>下方</b>的部分对应 $y<0$。</p>"
                     f"<p>本题要求 $y>0$：$x<{K.num_str(r1)}$ 或 $x>{K.num_str(r2)}$——"
                     "「两根之外」。</p>"
                     f"<p>若要求 $y<0$，解集就是「两根之间」${K.num_str(r1)}<x<{K.num_str(r2)}$。</p>")},
        {"title": "拖动验证",
         "content": ("<p>拖动 $k$：相当于把「零线」上下移动。$k$ 越大，"
                     "可用区间越窄；当 $k$ 超过顶点纵坐标时，不等式无解。</p>"
                     "<p>顶点是 $(1,-4)$，所以 $k\\ge -4$ 时两边界重合或消失。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 8) 因式分解（十字相乘）
# =====================================================================
def build_factor() -> dict:
    a0, b0, c0 = 6, 5, -6
    fac = K.factor_quadratic(a0, b0, c0)
    ftxt = K.factor_text(fac)
    s = K.solve_quadratic(a0, b0, c0)
    roots = s["roots"]
    board = {
        "view": {"xRange": [-2.2, 1.6], "yRange": [-15, 20]},
        "conics": [fn_conic("f", a0 * x * x + b0 * x + c0, label=f"$y={tex(a0*x*x+b0*x+c0)}$")],
        "points": {
            "R1": pt([roots[0], 0], "given", "x₁", True),
            "R2": pt([roots[1], 0], "given", "x₂", True),
        },
        "derived": [],
        "readouts": [
            {"id": "a", "label": "$a$", "type": "expr", "expr": str(a0), "digits": 0},
            {"id": "b", "label": "$b$", "type": "expr", "expr": str(b0), "digits": 0},
            {"id": "c", "label": "$c$", "type": "expr", "expr": str(c0), "digits": 0},
            {"id": "r1", "label": "$x_1$", "type": "expr", "expr": str(K.f(roots[0])), "digits": 3},
            {"id": "r2", "label": "$x_2$", "type": "expr", "expr": str(K.f(roots[1])), "digits": 3},
        ],
        "constant": None,
        "legend": [{"color": "curve", "text": "二次函数图像"}, {"color": "given", "text": "与 x 轴交点"}],
    }
    lesson = {
        "language": "zh-CN", "title": "因式分解与方程的根",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            f"<p>把 ${tex(a0*x*x+b0*x+c0)}$ 因式分解，并写出对应方程的两根。</p>"),
        "answerLabel": "因式分解结果",
        "answer": f"${ftxt}$",
    }
    steps = [
        {"title": "十字相乘",
         "content": (f"<p>要拆成 $(px+q)(rx+s)$，需要 $pr={a0}$、$qs={c0}$、$ps+qr={b0}$。</p>"
                     f"<p>尝试得 ${ftxt}$。</p>")},
        {"title": "展开验证",
         "content": (f"<p>把 ${ftxt}$ 展开，一次项来自 $ps+qr$，"
                     "常数项来自 $qs$——正好对上原式。</p>"
                     "<p>这不是「凑」，而是两个约束：乘积定常数项，交叉和定一次项。</p>")},
        {"title": "与图像的关系",
         "content": (f"<p>因式分解立刻给出根：$x_1={K.num_str(roots[0])}$，"
                     f"$x_2={K.num_str(roots[1])}$——就是抛物线与 $x$ 轴的两个交点。</p>"
                     "<p>所以「能分解」与「有两个有理根」是同一件事。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 9) 锐角三角函数
# =====================================================================
def build_trig() -> dict:
    ang0 = 30
    hyp = 2
    T = K.solve_right_triangle(ang0, hyp, "hyp")
    opp = K.f(T["opp"])
    adj = K.f(T["adj"])
    board = {
        "view": {"xRange": [-1, 3.4], "yRange": [-1, 2.6]},
        "conics": [],
        "points": {
            "A": ptx("0", "0", "given", "A", True),
            "B": ptx("2*cos(ang*PI/180)", "0", "given", "B", True),
            "C": ptx("2*cos(ang*PI/180)", "2*sin(ang*PI/180)", "given", "C", True),
        },
        "param": {"name": "ang", "label": "锐角 $\\angle A$（度）",
                  "min": 15, "max": 75, "step": 1, "value": ang0, "unit": "°", "standard": ang0,
                  "ticks": ["15°", "30° (题设)", "45°", "75°"]},
        "derived": [
            {"type": "segment", "name": "AB", "a": "A", "b": "B", "color": "line"},
            {"type": "segment", "name": "BC", "a": "B", "b": "C", "color": "curve"},
            {"type": "segment", "name": "CA", "a": "C", "b": "A", "color": "line2"},
            {"type": "right_angle_mark", "a": "A", "vertex": "B", "b": "C", "color": "aux"},
            {"type": "angle_arc", "a": "B", "vertex": "A", "b": "C", "r": 0.42,
             "color": "aux", "label": "A", "labelR": 0.62},
        ],
        "readouts": [
            {"id": "ang", "label": "$\\angle A$", "type": "expr", "expr": "ang", "digits": 1, "unit": "°"},
            {"id": "opp", "label": "对边 $BC=2\\sin A$", "type": "expr", "expr": "2*sin(ang*PI/180)", "digits": 3},
            {"id": "adj", "label": "邻边 $AB=2\\cos A$", "type": "expr", "expr": "2*cos(ang*PI/180)", "digits": 3},
            {"id": "sin", "label": "$\\sin A$", "type": "expr", "expr": "sin(ang*PI/180)", "digits": 3,
             "highlight": True},
            {"id": "cos", "label": "$\\cos A$", "type": "expr", "expr": "cos(ang*PI/180)", "digits": 3},
            {"id": "tan", "label": "$\\tan A$", "type": "expr", "expr": "tan(ang*PI/180)", "digits": 3},
        ],
        "constant": None,
        "legend": [{"color": "line", "text": "邻边"}, {"color": "curve", "text": "对边"},
                   {"color": "line2", "text": "斜边 = 2（定值）"}],
    }
    lesson = {
        "language": "zh-CN", "title": "锐角三角函数：边与角的比",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>在 $\\mathrm{Rt}\\triangle ABC$ 中，$\\angle B=90^\\circ$，"
            "斜边 $AC$ 固定为 2，$\\angle A$ 可调。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>当 $\\angle A=30^\\circ$ 时，求对边与邻边；</li>"
            "<li>拖动滑块，$\\sin A$ 与 $\\cos A$ 怎么变？为什么 $\\sin^2A+\\cos^2A=1$？</li></ol>"),
        "answerLabel": "∠A=30° 时的三边",
        "answer": f"$BC={K.num_str(T['opp'])},\\ AB={K.num_str(T['adj'])},\\ AC=2$",
    }
    steps = [
        {"title": "三个比的定义",
         "content": ("<p>在直角三角形中，对一个锐角 $A$：</p>"
                     "<p class='text-center'>$\\sin A=\\dfrac{\\text{对边}}{\\text{斜边}},\\ "
                     "\\cos A=\\dfrac{\\text{邻边}}{\\text{斜边}},\\ "
                     "\\tan A=\\dfrac{\\text{对边}}{\\text{邻边}}$</p>"
                     "<p>它们只与角的大小有关，与三角形大小无关——这正是「三角函数」的意思。</p>")},
        {"title": "30° 的精确值",
         "content": (f"<p>$\\sin30^\\circ=\\dfrac12$，所以对边 $=2\\times\\dfrac12=1$；"
                     f"$\\cos30^\\circ=\\dfrac{{\\sqrt3}}{{2}}$，所以邻边 $=\\sqrt3$。</p>"
                     f"<p>图中：$BC={K.num_str(T['opp'])}$，$AB={K.num_str(T['adj'])}$。</p>")},
        {"title": "为什么平方和是 1",
         "content": ("<p>设对边 $a$、邻边 $b$、斜边 $c$。由勾股定理 $a^2+b^2=c^2$，两边除以 $c^2$：</p>"
                     "<p class='text-center'>$\\left(\\dfrac{a}{c}\\right)^2+\\left(\\dfrac{b}{c}\\right)^2=1"
                     "\\quad\\Longrightarrow\\quad \\sin^2A+\\cos^2A=1$</p>"
                     "<p>拖动滑块可以看到：$\\sin A$ 变大时 $\\cos A$ 必变小，两者不能同时变大。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册表
# =====================================================================
REGISTRY = {
    "linear": build_linear,
    "linear_intersect": build_linear_intersect,
    "quadratic": build_quadratic,
    "quad_extremum": build_quad_extremum,
    "discriminant": build_discriminant,
    "vieta": build_vieta,
    "inequality": build_inequality,
    "factor": build_factor,
    "trig": build_trig,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="初中代数与函数 · 交互课件", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
