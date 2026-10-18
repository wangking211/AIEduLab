#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「常微分方程与动力系统」网页。

按 MIT 18.03 的知识点组织；全部数值由 lib/ode_kernel.py 驱动（方向场与精确解、
欧拉法与 RK4 的误差、阻尼振动三情形、受迫振动与共振、线性系统的平衡点分类、
Logistic 方程、Lotka–Volterra 的相图与守恒量），**不手写数字**。

**轨迹一律真跑**：画板上的轨道由 JS 里的 RK4 实际推进得到（与内核同一套算法、
同一步长），凡有解析解的一律与解析解对照。

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

import ode_kernel as K                       # noqa: E402
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
    "exp": math.exp, "log": math.log, "cosh": math.cosh, "sinh": math.sinh,
}


def _find_ternary(s):
    """找第一个三目 `?` 及其所在括号组边界（支持任意深度嵌套）。"""
    depth, q, qdepth = 0, -1, 0
    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "?":
            q, qdepth = i, depth
            break
    if q < 0:
        return None
    depth, nest, colon = qdepth, 0, -1
    for i in range(q + 1, len(s)):
        ch = s[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "?" and depth == qdepth:
            nest += 1
        elif ch == ":" and depth == qdepth:
            if nest == 0:
                colon = i
                break
            nest -= 1
    if colon < 0:
        raise ValueError(f"三目表达式缺冒号：{s!r}")
    lo, d = -1, 0
    for i in range(q - 1, -1, -1):
        if s[i] == ")":
            d += 1
        elif s[i] == "(":
            if d == 0:
                lo = i
                break
            d -= 1
    if lo < 0:
        hi = len(s)
    else:
        d, hi = 0, -1
        for i in range(lo, len(s)):
            if s[i] == "(":
                d += 1
            elif s[i] == ")":
                d -= 1
                if d == 0:
                    hi = i
                    break
        if hi < 0:
            raise ValueError(f"括号不配对：{s!r}")
    return lo, q, colon, hi


def _js_to_py(expr):
    """把三目 `a?b:c` 翻成 Python 的 `b if a else c`（供构建期对账）。"""
    while True:
        f = _find_ternary(expr)
        if f is None:
            return expr
        lo, q, colon, hi = f
        base = lo + 1 if lo >= 0 else 0
        cond, yes, no = expr[base:q], expr[q + 1:colon], expr[colon + 1:hi]
        inner = f"({_js_to_py(yes)} if {_js_to_py(cond)} else {_js_to_py(no)})"
        expr = expr[:base] + inner + expr[hi:]


def _jseval(expr, **env):
    return eval(_js_to_py(expr.replace("^", "**")), {"__builtins__": {}}, {**_MATHENV, **env})


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
# 1) 方向场与解曲线
# =====================================================================
def build_firstorder() -> dict:
    y0 = 0.0
    EXPR_Y5 = "5-1+(y+1)*exp(-5)"
    EXPR_Y1 = "1-1+(y+1)*exp(-1)"
    for y in (-2.0, -0.5, 0.0, 1.0, 3.0):
        _agree(f"y(5)(y={y})", EXPR_Y5, K.first_order_exact(5.0, y), tol=1e-12, y=y)
        _agree(f"y(1)(y={y})", EXPR_Y1, K.first_order_exact(1.0, y), tol=1e-12, y=y)
    _agree("t=0 处的斜率 = −y", "0-y", K.first_order_slope(0.0, y0), tol=1e-12, y=y0)
    # 所有解都趋于 y = t − 1：t=20 时与渐近线的偏差就是那个衰减项
    _agree("t=20 时与渐近线的偏差", "(y+1)*exp(-20)",
           K.first_order_exact(20.0, y0) - 19.0, tol=1e-15, y=y0)
    assert abs(K.first_order_exact(0.0, y0) - y0) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "slopefield", "y0": "y",
                  "caption": "灰短段是方向场；绿线是过初值点（黄）的那条特解"},
        "param": {"name": "y", "label": "初值 $y(0)$", "min": -2, "max": 3, "step": 0.1,
                  "value": y0, "unit": "", "standard": y0,
                  "ticks": ["-2", "0 (题设)", "3"]},
        "readouts": [
            ro("y5", "$y(5)$", EXPR_Y5, 5),
            ro("y1", "$y(1)$", EXPR_Y1, 5),
            ro("slope0", "初值处的斜率 $y'(0)$", "0-y", 3),
            ro_status("up", "初值处是否在上升", "0-y", 0, ">",
                      "斜率 > 0，解在上升", "斜率 ≤ 0，解在下降"),
        ],
        "constant": {"of": "asym", "label": "所有解最终都贴着 y = t − 1（与初值无关）"},
    }
    lesson = {
        "language": "zh-CN", "title": "方向场与解曲线",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>一阶方程 $y' = t - y$，初值 $y(0) = y_0$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>在方向场上画出这条解曲线；</li>"
            "<li>拖动滑块改变初值，为什么所有解最终都挤向同一条直线？</li>"
            "<li>那条直线的方程是什么？</li></ol>"),
        "answerLabel": "渐近直线",
        "answer": "$y = t - 1$",
    }
    steps = [
        {"title": "方向场：把方程画成箭头",
         "content": ("<p>$y' = f(t,y)$ 只规定了「每一点该往哪个方向走」。"
                     "把每点的斜率画成一小段线段，就得到**方向场**。</p>"
                     "<p>解曲线就是从某个初值点出发、处处与方向场相切的那条曲线。"
                     "所以画解曲线不需要公式，只需要**跟着箭头走**——这就是数值方法的思想。</p>")},
        {"title": "一阶线性方程有精确解",
         "content": ("<p>$y' + y = t$ 是线性一阶，用积分因子 $e^{t}$："
                     "$(e^{t}y)' = e^{t}t$，解得</p>"
                     "<p>$y = t - 1 + (y_0+1)e^{-t}$。</p>"
                     "<p>注意末项：它以 $e^{-t}$ 衰减。所以无论 $y_0$ 取什么，"
                     "长期行为都由 $t-1$ 决定 —— 图上所有解最终都贴到红线上。</p>")},
        {"title": "为什么初值的影响会消失",
         "content": ("<p>把解写成「特解 + 齐次解」：$y = \\underbrace{(t-1)}_{特解} "
                     "+ \\underbrace{(y_0+1)e^{-t}}_{齐次解}$。</p>"
                     "<p>齐次解随时间衰减到 0，所以初值的影响**指数衰减**。"
                     "这类「长期行为与初值无关」的性质叫**稳定性**——"
                     "它是整门课的主线，后面的阻尼振动、平衡点分类都在讲同一件事。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 数值方法：步长对误差的影响
# =====================================================================
def build_euler() -> dict:
    n0 = 20
    EXPR_H = "5/n"
    EXPR_EXACT = "5-1+exp(-5)"
    _agree("步长 h", EXPR_H, 5.0 / n0, tol=1e-12, n=n0)
    _agree("精确解 y(5)（y₀=0）", EXPR_EXACT, K.first_order_exact(5.0, 0.0), tol=1e-12)
    assert abs(K.first_order_exact(5.0, 0.0) - 4.006737947) < 1e-8

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "numerror", "n": "n",
                  "caption": "三条曲线都是真跑的；右侧小图放大显示各自的误差"},
        "param": {"name": "n", "label": "步数 $n$", "min": 5, "max": 100, "step": 5,
                  "value": n0, "unit": "", "standard": n0,
                  "ticks": ["5", "20 (题设)", "100"]},
        "readouts": [
            ro("h", "步长 $h = 5/n$", EXPR_H, 4),
            ro("ex", "精确解 $y(5)$", EXPR_EXACT, 8),
            ro("hz", "步长是否够小（h < 0.1）", EXPR_H, 0, 4),
            ro_status("small", "步长 h 是否 < 0.1", EXPR_H, 0.1, "<",
                      "步长已足够小，两条数值解都贴近精确解", "步长偏大，欧拉法会明显偏离"),
        ],
        "constant": {"of": "ex", "label": "精确解 y(5) = 4.00673795 恒定（与步数无关）"},
    }
    lesson = {
        "language": "zh-CN", "title": "数值方法：欧拉法与 RK4",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>用数值方法解 $y' = t - y$、$y(0)=0$，区间 $[0,5]$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>欧拉法怎么走？为什么它会系统性偏离？</li>"
            "<li>RK4 多算了什么？为什么误差小得多？</li>"
            "<li>拖动滑块减小步长，两条误差曲线各按什么速率下降？</li></ol>"),
        "answerLabel": "精确解在 t = 5 的值",
        "answer": "$y(5) = 4 + e^{-5} \\approx 4.0067$",
    }
    steps = [
        {"title": "欧拉法：沿切线走一步，再重新算斜率",
         "content": ("<p>$y_{n+1} = y_n + h\\,f(t_n, y_n)$ —— 在每一点用**当前**斜率"
                     "外推一整步。所以它相当于「用折线逼近曲线」。</p>"
                     "<p>误差来源：一步之内斜率其实在变，欧拉法假装它不变。"
                     "单步误差 $\\sim \\dfrac{h^2}{2}|y''|$，累积 $n=5/h$ 步后"
                     "总量级是 $\\sim h$ —— **一阶方法**。</p>")},
        {"title": "RK4：一步之内采四次斜率",
         "content": ("<p>RK4 在一步里取起点、中点（两次）、终点的斜率并加权平均："
                     "$y_{n+1} = y_n + \\dfrac{h}{6}(k_1+2k_2+2k_3+k_4)$。</p>"
                     "<p>它的累积误差量级是 $\\sim h^4$ —— 所以图上蓝线与绿线"
                     "几乎完全重合，而红线明显偏低。把滑块拖到 $n=100$（$h=0.05$）"
                     "可以看得更清楚。</p>")},
        {"title": "怎么判断数值解可信",
         "content": ("<p>右侧小图把两条误差曲线放大画出来：**误差随步长单调下降**"
                     "是数值解可信的必要条件。若减小步长误差反而变大（或震荡不降），"
                     "说明实现有问题（或方程本身刚性）。</p>"
                     "<p>另一种更严格的做法是用**两个不同步长**的结果比较，"
                     "用它们的差去估计误差 —— 这是工程上「步长自适应」的基础。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 阻尼振动
# =====================================================================
def build_damped() -> dict:
    z0 = 0.2
    # y(3) 的三分支闭式（y(0)=1, y'(0)=0）
    EXPR_WD = "sqrt(max(0,1-z*z))"
    UNDER = "exp(-z*3)*(cos(sqrt(1-z*z)*3)+z/sqrt(1-z*z)*sin(sqrt(1-z*z)*3))"
    WH = "sqrt(z*z-1)"
    L1, L2 = "(-z+" + WH + ")", "(-z-" + WH + ")"
    A = "(0.5+z/(2*" + WH + "))"
    B = "(0.5-z/(2*" + WH + "))"
    OVER = f"({A}*exp({L1}*3)+{B}*exp({L2}*3))"
    EXPR_Y3 = f"(z<1) ? ({UNDER}) : ((z>1) ? ({OVER}) : (exp(-3)*(1+3)))"
    EXPR_ENV = "exp(-3*z)"
    for z in (0.0, 0.2, 0.5, 0.95, 1.0, 1.05, 2.0, 2.5):
        _agree(f"y(3)(ζ={z})", EXPR_Y3, K.damped_solution(3.0, z), tol=1e-9, z=z)
    _agree("包络 e^(−3ζ)", EXPR_ENV, math.exp(-3 * z0), tol=1e-12, z=z0)
    _agree("ω_d 的夹取式", EXPR_WD, math.sqrt(1 - z0 * z0), tol=1e-12, z=z0)
    assert K.damping_type(z0) == "under" and K.damping_type(2.0) == "over"

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "oscillator", "z": "z",
                  "caption": "灰线是 ±e^(−ζt) 包络；黄线是精确解（三分支同式）"},
        "param": {"name": "z", "label": "阻尼比 $\\zeta$", "min": 0, "max": 2.5,
                  "step": 0.05, "value": z0, "unit": "", "standard": z0,
                  "ticks": ["0", "0.2 (题设)", "1 (临界)", "2.5"]},
        "readouts": [
            ro("wd", "$\\omega_d = \\sqrt{1-\\zeta^2}$", EXPR_WD, 4),
            ro("y3", "$y(3)$", EXPR_Y3, 5),
            ro("env", "包络 $e^{-3\\zeta}$", EXPR_ENV, 5),
            ro_status("under", "是否欠阻尼（ζ < 1）", "1-z", 0, ">",
                      "欠阻尼：会振荡着衰减", "临界或过阻尼：不再振荡"),
        ],
        "constant": {"of": "th", "label": "初值恒为 y(0)=1、y'(0)=0 —— 改变 ζ 不动它"},
    }
    lesson = {
        "language": "zh-CN", "title": "阻尼振动：三种情形",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>阻尼自由振动 $y'' + 2\\zeta y' + y = 0$，$y(0)=1$、$y'(0)=0$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>$\\zeta$ 取什么值时振荡？为什么？</li>"
            "<li>拖动滑块，$\\zeta = 0, 1, 2.5$ 各是什么形态？</li>"
            "<li>包络为什么是 $e^{-\\zeta t}$？</li></ol>"),
        "answerLabel": "三种情形的分界",
        "answer": "$\\zeta < 1$ 欠阻尼、$\\zeta = 1$ 临界、$\\zeta > 1$ 过阻尼",
    }
    steps = [
        {"title": "特征方程决定一切",
         "content": ("<p>设 $y = e^{\\lambda t}$，得特征方程 "
                     "$\\lambda^2 + 2\\zeta\\lambda + 1 = 0$，"
                     "根为 $\\lambda = -\\zeta \\pm \\sqrt{\\zeta^2-1}$。</p>"
                     "<p>**判别式 $\\zeta^2-1$ 的符号**决定根的形态："
                     "$\\zeta<1$ 时根是共轭复数（振荡）、$\\zeta=1$ 是重根、"
                     "$\\zeta>1$ 是两个实根（不振荡）。</p>")},
        {"title": "三种形态",
         "content": ("<p><b>欠阻尼</b>：$\\lambda = -\\zeta \\pm i\\omega_d$，"
                     "$\\omega_d = \\sqrt{1-\\zeta^2}$ —— 振荡频率略低于 1，"
                     "振幅按 $e^{-\\zeta t}$ 衰减。</p>"
                     "<p><b>临界阻尼</b>：$y = e^{-t}(1+t)$ —— 最快地回到平衡"
                     "且不越过零点。</p>"
                     "<p><b>过阻尼</b>：两个负实根，慢的那个主导长期行为，"
                     "所以它比临界阻尼**更慢**回到平衡（滑块拖到 2.5 就能看到）。</p>")},
        {"title": "包络与其物理含义",
         "content": ("<p>欠阻尼解可写成 $y = R e^{-\\zeta t}\\cos(\\omega_d t - \\varphi)$，"
                     "于是 $|y| \\le R e^{-\\zeta t}$ —— 图上两条灰线就是它。</p>"
                     "<p>包络的衰减率恰好是特征值的**实部**。这给出一个重要直觉："
                     "**实部管衰减、虚部管振荡**。下一节的平衡点分类就是按这个划分的。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 受迫振动与共振
# =====================================================================
def build_forced() -> dict:
    z, w0 = 0.15, 1.0
    EXPR_A = "(1/sqrt((1-w*w)*(1-w*w)+(2*0.15*w)*(2*0.15*w)))"
    EXPR_WR = "sqrt(max(0,1-2*0.15*0.15))"
    EXPR_AR = "(1/(2*0.15*sqrt(1-0.15*0.15)))"
    for w in (0.0, 0.5, 0.977, 1.0, 1.5, 2.6):
        _agree(f"A(ω={w})", EXPR_A, K.forced_amplitude(w, z, w0), tol=1e-12, w=w)
    _agree("共振频率", EXPR_WR, K.resonance_omega(z, w0), tol=1e-12)
    _agree("峰值振幅", EXPR_AR, K.resonance_amplitude(z, w0), tol=1e-12)
    _agree("静力位移 A(0) = 1", EXPR_A.replace("w", "0"), 1.0, tol=1e-12)
    assert abs(K.resonance_omega(z, w0) - 0.9770) < 1e-3

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "resonance", "w": "w", "zeta": z,
                  "caption": "黄线是稳态振幅响应；绿竖线标出当前驱动频率"},
        "param": {"name": "w", "label": "驱动频率 $\\omega$", "min": 0, "max": 2.6,
                  "step": 0.05, "value": 1.0, "unit": "", "standard": 1.0,
                  "ticks": ["0", "0.977 (共振)", "1", "2.6"]},
        "readouts": [
            ro("A", "稳态振幅 $A(\\omega)$", EXPR_A, 4),
            ro("wr", "共振频率 $\\omega_r$", EXPR_WR, 4),
            ro("Ar", "峰值振幅", EXPR_AR, 4),
            ro_status("near", "当前频率是否在共振附近（|ω−ω_r| < 0.1）",
                      "abs(w-" + EXPR_WR + ")", 0.1, "<",
                      "在共振附近：振幅接近峰值", "离共振较远"),
        ],
        "constant": {"of": "zeta", "label": "阻尼比固定 0.15 —— 它越小，峰值越高"},
    }
    lesson = {
        "language": "zh-CN", "title": "受迫振动与共振",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>受迫振动 $y'' + 2\\zeta y' + y = \\cos(\\omega t)$，"
            "$\\zeta = 0.15$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>稳态振幅 $A(\\omega)$ 的表达式是什么？</li>"
            "<li>$\\omega$ 取何值时振幅最大？此时振幅是多少？</li>"
            "<li>为什么 $\\omega=0$ 时振幅恰好是 1？</li></ol>"),
        "answerLabel": "$\\zeta = 0.15$ 时的共振频率与峰值振幅",
        "answer": f"$\\omega_r \\approx {K.f(K.resonance_omega(z),4)}$，"
                  f"峰值 $\\approx {K.f(K.resonance_amplitude(z),3)}$",
    }
    steps = [
        {"title": "稳态解与复阻抗",
         "content": ("<p>设 $y = \\operatorname{Re}[Y e^{i\\omega t}]$，代入得</p>"
                     "<p>$Y = \\dfrac{1}{(1-\\omega^2) + 2\\zeta\\omega\\, i}$，"
                     "取模即振幅 $A = \\dfrac{1}{\\sqrt{(1-\\omega^2)^2 + (2\\zeta\\omega)^2}}$。</p>"
                     "<p>分母就是「离共振有多远」与「阻尼多大」这两项的合成。</p>")},
        {"title": "共振频率：让分母最小",
         "content": ("<p>把 $(1-\\omega^2)^2 + 4\\zeta^2\\omega^2$ 对 $\\omega^2$ 求导置零，"
                     "得 $\\omega_r = \\sqrt{1-2\\zeta^2}$。</p>"
                     "<p>$\\zeta = 0.15$ 时 $\\omega_r \\approx 0.977$ —— 注意它**略小于 1**，"
                     "不是恰好在固有频率 1 处。阻尼越大偏移越多；"
                     "$\\zeta \\ge 1/\\sqrt2 \\approx 0.707$ 时峰值消失，"
                     "振幅随 $\\omega$ 单调下降。</p>")},
        {"title": "峰值有多高",
         "content": ("<p>代回得峰值 $A_{max} = \\dfrac{1}{2\\zeta\\sqrt{1-\\zeta^2}}"
                     "\\approx " + f"{K.resonance_amplitude(z):.3f}" + "$。</p>"
                     "<p>$\\zeta \\to 0$ 时它**发散** —— 这就是共振的破坏力来源："
                     "无阻尼受迫振动在 $\\omega = 1$ 处振幅随时间线性增长，"
                     "没有稳态。</p>"
                     "<p>而 $\\omega = 0$ 相当于施加静力，$A(0) = 1$ 就是静力位移，"
                     "与阻尼无关 —— 图上蓝线标出了它。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 线性系统的平衡点分类
# =====================================================================
def build_phase() -> dict:
    k0 = -0.5
    EXPR_TR = "2*k"
    EXPR_DET = "k*k+1"
    for k in (-1.0, -0.5, 0.0, 0.5, 1.0):
        ev = K.linear_eigen([[k, 1], [-1, k]])
        _agree(f"Re λ(k={k})", "k", ev[0][0], tol=1e-9, k=k)
        _agree(f"|Im λ|(k={k})", "1", abs(ev[0][1]), tol=1e-9, k=k)
        _agree(f"迹(k={k})", EXPR_TR, 2 * k, tol=1e-12, k=k)
        _agree(f"det(k={k})", EXPR_DET, k * k + 1, tol=1e-12, k=k)
    _agree("k=0 时是中心", "abs(k)", 0.0, tol=1e-12, k=0.0)
    assert K.classify_2x2([[0, 1], [-1, 0]])[0] == "中心（center）"
    assert K.classify_2x2([[-1, 1], [-1, -1]])[1] is True

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "phaseplane", "k": "k",
                  "caption": "灰短段是向量场；黄线是过 (1.6,0) 的轨道（RK4 真跑）"},
        "param": {"name": "k", "label": "对角元素 $k$", "min": -1, "max": 1,
                  "step": 0.05, "value": k0, "unit": "", "standard": k0,
                  "ticks": ["-1", "-0.5 (题设)", "0 (中心)", "1"]},
        "readouts": [
            ro("tr", "迹 $\\operatorname{tr}A = 2k$", EXPR_TR, 3),
            ro("det", "行列式 $\\det A = k^2+1$", EXPR_DET, 3),
            ro("re", "特征值实部 $\\operatorname{Re}\\lambda = k$", "k", 3),
            ro_status("stable", "是否稳定（Re λ < 0）", "k", 0, "<",
                      "稳定：轨道向内盘旋", "不稳定或中性：向外盘旋 / 闭合"),
        ],
        "constant": {"of": "det", "label": "det = k²+1 恒为正 —— 所以永远不会是鞍点"},
    }
    lesson = {
        "language": "zh-CN", "title": "线性系统的相平面与平衡点分类",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>线性系统 $\\mathbf{x}' = A\\mathbf{x}$，"
            "$A = \\begin{pmatrix}k & 1\\\\ -1 & k\\end{pmatrix}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求特征值，判断平衡点类型；</li>"
            "<li>拖动滑块，轨道怎么变？什么时候是闭合的圆？</li>"
            "<li>为什么这个系统不会出现鞍点或结点？</li></ol>"),
        "answerLabel": "特征值与类型",
        "answer": "$\\lambda = k \\pm i$ —— 恒为焦点；$k=0$ 时退化为中心",
    }
    steps = [
        {"title": "按特征值给平衡点分类",
         "content": ("<p>设 $\\mathbf{x} = \\mathbf{v}e^{\\lambda t}$，得 $A\\mathbf{v} = \\lambda\\mathbf{v}$。"
                     "**实部管衰减、虚部管旋转**。按迹与行列式分类：</p>"
                     "<p>$\\det<0$ → 鞍点；$\\det>0$ 时看判别式 $\\operatorname{tr}^2-4\\det$："
                     "负 → 焦点或中心（$\\operatorname{tr}=0$ 是中心），非负 → 结点。</p>")},
        {"title": "本题：永远在虚轴上平移",
         "content": ("<p>$\\operatorname{tr}A = 2k$、$\\det A = k^2+1 > 0$、"
                     "判别式 $= 4k^2 - 4(k^2+1) = -4 < 0$。</p>"
                     "<p>判别式恒为负 ⇒ **永远是焦点**；$\\det$ 恒正 ⇒ 永不是鞍点。"
                     "特征值 $\\lambda = k \\pm i$：虚部恒为 $\\pm1$（所以总是转圈），"
                     "实部就是 $k$（所以 $k<0$ 向内、$k=0$ 闭合、$k>0$ 向外）。</p>")},
        {"title": "闭合轨道与守恒量",
         "content": ("<p>$k = 0$ 时 $A$ 是反对称矩阵，系统是简谐振子，"
                     "有一个**守恒量** $x^2+y^2$（沿轨道不变）。</p>"
                     "<p>守恒量存在 ⇒ 轨道闭合；$k \\ne 0$ 时能量被阻尼（或注入），"
                     "守恒量变成单调量，轨道就成了螺旋。这与上一节阻尼振动的"
                     "包络是同一件事。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) Logistic 方程
# =====================================================================
def build_logistic() -> dict:
    r0, y0, Kk = 0.8, 0.05, 1.0
    EXPR_Y2 = "1/(1+(1-0.05)/0.05*exp(-r*2))"
    EXPR_Y6 = "1/(1+(1-0.05)/0.05*exp(-r*6))"
    EXPR_T90 = "log(((1-0.05)/0.05)/((1-0.9)/0.9))/r"
    EXPR_RMAX = "r/4"
    for r in (0.1, 0.5, 0.8, 1.5, 2.0):
        _agree(f"y(2)(r={r})", EXPR_Y2, K.logistic_solution(2.0, r, Kk, y0), tol=1e-12, r=r)
        _agree(f"y(6)(r={r})", EXPR_Y6, K.logistic_solution(6.0, r, Kk, y0), tol=1e-12, r=r)
        _agree(f"t90(r={r})", EXPR_T90, K.logistic_time_to(0.9, r, Kk, y0), tol=1e-12, r=r)
        _agree(f"最大增长率(r={r})", EXPR_RMAX, K.logistic_max_rate(r, Kk), tol=1e-12, r=r)
    assert abs(K.logistic_solution(0.0, r0, Kk, y0) - y0) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "logisticode", "r": "r", "y0": y0,
                  "caption": "黄线是题设初值的解；蓝线是其他初值 —— 都趋于 K"},
        "param": {"name": "r", "label": "内禀增长率 $r$", "min": 0.1, "max": 2.0,
                  "step": 0.05, "value": r0, "unit": "", "standard": r0,
                  "ticks": ["0.1", "0.8 (题设)", "2.0"]},
        "readouts": [
            ro("y2", "$y(2)$", EXPR_Y2, 5),
            ro("y6", "$y(6)$", EXPR_Y6, 5),
            ro("t90", "到达 $0.9K$ 所需时间", EXPR_T90, 3),
            ro("rmax", "最大增长率 $rK/4$", EXPR_RMAX, 4),
            ro_status("fast", "是否较快到达（t₉₀ < 5）", EXPR_T90, 5, "<",
                      "较快到达 K", "到达较慢"),
        ],
        "constant": {"of": "K", "label": "环境容纳量 K = 1，初值 y₀ = 0.05"},
    }
    lesson = {
        "language": "zh-CN", "title": "Logistic 方程：有限的增长",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>Logistic 方程 $y' = r\\,y\\left(1 - \\dfrac{y}{K}\\right)$，"
            "$K = 1$、$y(0) = 0.05$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求两个平衡点，判断各自的稳定性；</li>"
            "<li>增长率在什么时候最大？为什么不是一开始？</li>"
            "<li>拖动滑块改变 $r$，曲线的形状怎么变？</li></ol>"),
        "answerLabel": "平稳点与最大增长率",
        "answer": "$y = 0$（不稳定）、$y = K$（稳定）；最大增长率出现在 $y = K/2$，值为 $rK/4$",
    }
    steps = [
        {"title": "两个平衡点，一稳一不稳",
         "content": ("<p>令 $y' = 0$ 得 $y = 0$ 与 $y = K$。看导数的符号：</p>"
                     "<p>$0 < y < K$ 时 $y' > 0$（增长），$y > K$ 时 $y' < 0$（下降）。"
                     "所以 **$y=0$ 不稳定、$y=K$ 稳定** —— 这也解释了图上"
                     "多个初值的曲线为什么都汇向 $K$。</p>")},
        {"title": "增长率为什么先升后降",
         "content": ("<p>把 $g(y) = r\\,y(1-y/K)$ 看成 $y$ 的函数：它是开口向下的抛物线，"
                     "顶点在 $y = K/2$，最大值 $rK/4$。</p>"
                     "<p>所以「增长最快」发生在**种群达到容量一半**的时候："
                     "早期个体太少、后期资源太紧。这与指数增长（$y' = ry$，"
                     "越快越大、永不停）形成鲜明对比。</p>")},
        {"title": "精确解与「S 曲线」",
         "content": ("<p>分离变量可得 "
                     "$y(t) = \\dfrac{K}{1 + \\frac{K-y_0}{y_0}e^{-rt}}$。</p>"
                     "<p>分母里那个 $e^{-rt}$ 让曲线从指数增长过渡到饱和 ——"
                     "这就是 S 形。$r$ 越大过渡越陡（滑块拖到 2.0 看看）。</p>"
                     "<p>顺带说明：$y_0 > K$ 时曲线从上方下降趋近 $K$ ——"
                     "**稳定平衡点的含义就是「两边都来」**。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) Lotka–Volterra 相图与守恒量
# =====================================================================
def build_predator() -> dict:
    N0, E0 = 0.08, 0.05
    r, a, c, m = 0.05, 1.0, 1.0, 0.05
    EXPR_H = f"N0 - {m}*log(N0) + {E0} - {r}*log({E0})"
    for N in (0.02, 0.05, 0.08, 0.12):
        _agree(f"H(N₀={N})", EXPR_H, K.lv_conserved(N, E0, r, a, c, m), tol=1e-12, N0=N)
    _agree("内部平衡点 N* = m/c", "0.05", K.lv_equilibria(r, a, c, m)[1][0], tol=1e-12)
    _agree("内部平衡点 E* = r/a", "0.05", K.lv_equilibria(r, a, c, m)[1][1], tol=1e-12)
    H0 = K.lv_conserved(N0, E0, r, a, c, m)
    assert H0 is not None

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "lvplane", "N0": "N0",
                  "caption": "黄线是题设初值的轨道（RK4 真跑 300 年）；绿线是其他初值"},
        "param": {"name": "N0", "label": "猎物初值 $N_0$", "min": 0.02, "max": 0.12,
                  "step": 0.005, "value": N0, "unit": "", "standard": N0,
                  "ticks": ["0.02", "0.08 (题设)", "0.12"]},
        "readouts": [
            ro("H", "守恒量 $H$", EXPR_H, 5),
            ro("neq", "平衡点 $N^* = m/c$", "0.05", 3),
            ro("eeq", "平衡点 $E^* = r/a$", "0.05", 3),
            ro_status("above", "$N_0$ 是否在平衡点之上", "N0-0.05", 0, ">",
                      "起点在平衡点右侧，轨道绕它转", "起点在平衡点左侧"),
        ],
        "constant": {"of": "r", "label": "r = m = 0.05、a = c = 1 固定；捕食者初值 E₀ = 0.05"},
    }
    lesson = {
        "language": "zh-CN", "title": "Lotka–Volterra：相图与守恒量",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>捕食者–被捕食模型："
            "$\\dot N = rN - aNE$，$\\dot E = cNE - mE$，"
            "取 $r = m = 0.05$、$a = c = 1$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求非零平衡点；</li>"
            "<li>为什么轨道是**闭合**的？它和守恒量有什么关系？</li>"
            "<li>拖动滑块改变初值，轨道怎么变？</li></ol>"),
        "answerLabel": "非零平衡点",
        "answer": "$(N^*, E^*) = \\left(\\dfrac{m}{c},\\ \\dfrac{r}{a}\\right) = (0.05,\\ 0.05)$",
    }
    steps = [
        {"title": "平衡点与它的意义",
         "content": ("<p>令两式为零：$N(r - aE) = 0$ 与 $E(cN - m) = 0$。</p>"
                     "<p>非零解是 $E = r/a$、$N = m/c$ —— 图上那个红点。"
                     "它的含义是：**捕食者的数量由猎物增长率决定，"
                     "猎物的数量由捕食者死亡率决定** —— 这个反直觉的结论是模型的核心。</p>")},
        {"title": "守恒量 H 与闭合轨道",
         "content": ("<p>定义 $H = cN - m\\ln N + aE - r\\ln E$，"
                     "求导得 $\\dot H = 0$ —— 它是**运动常数**。</p>"
                     "<p>因为 $H$ 是凸函数（各项都凸），它的等值线是闭合曲线；"
                     "而轨线被限制在一条等值线上，所以轨道必然闭合，"
                     "周期严格存在。图上每条轨道对应一个 $H$ 值，"
                     "读数区给出的就是当前初值的那个 $H$。</p>"
                     "<p>数值上也能验：RK4 跑 300 年，$H$ 的相对漂移在 $10^{-3}$ 以内"
                     "（内核自检里有这条）。</p>")},
        {"title": "和「王朝周期」那类模型的关系",
         "content": ("<p>这个模型的参数与初值**都可以独立测量**（生态学里真的能数），"
                     "所以它的周期是有意义的物理量。</p>"
                     "<p>但要小心：把它搬到历史解释上时，参数与初值往往都只能**拟合**——"
                     "那时「多少年一循环」就不再是模型的结论，而是输入的假设。"
                     "同一套方程，证据力完全不同。（`edu-history` 专门讲这一点。）</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "firstorder": build_firstorder,
    "euler": build_euler,
    "damped": build_damped,
    "forced": build_forced,
    "phase": build_phase,
    "logistic": build_logistic,
    "predator": build_predator,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="常微分方程与动力系统 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
