# -*- coding: utf-8 -*-
"""
fn_kernel.py — 高中函数与导数确定性计算核心（sympy 精确符号运算）。

单一数据源设计：导数、切线方程、极值点/极值、单调区间、奇偶性、零点区间、
左右导数全部由本模块精确算出，讲解文字只引用 tex() 输出，绝无心算误差。
函数表达式同时翻译成 JS（js()）喂给画板引擎实时采样，保证"图、解、答"同源。

坐标约定：数学坐标，y 轴向上（画板模板已按此约定渲染）。

覆盖（v1，8 个题型）：
 1. tangent_line    —— 切线方程（f'(x0) 与切线 y=k(x-x0)+y0）
 2. secant_limit    —— 割线逼近切线（导数定义：k = lim Δy/Δx）
 3. cubic_extrema   —— 三次函数极值与单调区间（f'=0 + 符号表）
 4. parity_odd      —— 函数奇偶性（f(-x) 与 ±f(x) 比较）
 5. zero_crossing   —— 零点存在定理（f(a)f(b)<0 + 二分逼近）
 6. exp_family      —— 指数函数 y=aˣ 图像与定点（恒过 (0,1)）
 7. abs_corner      —— 绝对值函数在 x=0 处不可导（左右导数不等）
 8. tangent_family  —— 切线族包络/参数变化（a 变化时切线扫过的定值性质）

依赖: sympy。自检：python fn_kernel.py
"""

import sympy as sp

x, t, h, a_, b_, c_ = sp.symbols("x t h a b c", real=True)
e = sp.Symbol("e", positive=True)

sqrt = sp.sqrt


# ---------------- 通用工具 ----------------
def tex(expr):
    return sp.latex(sp.simplify(expr))


def f(expr):
    return float(sp.N(expr))


def js(expr):
    """把 sympy 表达式翻译成 JS 表达式（Math.* 形式，供画板 evalExpr 采样）。"""
    s = sp.jscode(sp.simplify(expr))
    return s.replace("Math.", "")


def derivative(expr, var=x):
    return sp.simplify(sp.diff(expr, var))


def tangent_at(expr, x0, var=x):
    """切线方程 (斜率 k, 过点 (x0, y0), 直线表达式 y=k(x-x0)+y0)。"""
    x0 = sp.sympify(x0)
    y0 = sp.simplify(expr.subs(var, x0))
    k = sp.simplify(sp.diff(expr, var).subs(var, x0))
    return k, y0


def tangent_line_latex(expr, x0, var=x):
    k, y0 = tangent_at(expr, x0, var)
    return sp.latex(sp.expand(k * (var - x0) + y0))


def extrema_of(expr, var=x):
    """求 f'=0 的驻点并用二阶导判别极值。

    返回 [{'x0', 'kind', 'value'}...]，kind ∈ {'极大','极小','拐点(非极值)'}。
    """
    d = sp.diff(expr, var)
    crit = sp.solve(sp.Eq(d, 0), var)
    out = []
    for c in crit:
        if c.is_real is False:
            continue
        d2 = sp.diff(expr, var, 2).subs(var, c)
        val = sp.simplify(expr.subs(var, c))
        if d2 < 0:
            kind = "极大"
        elif d2 > 0:
            kind = "极小"
        else:
            kind = "拐点(非极值)"
        out.append({"x0": sp.simplify(c), "kind": kind, "value": val})
    return out


def monotonic_intervals(expr, var=x, lo=-10, hi=10):
    """用 f' 的零点把定义域切段，判断每段符号 → 单调区间列表。

    返回 [{'interval': (l, r), 'sign': +1/-1, 'mono': '增'/'减'}...]。
    端点为 ±oo 时用 None 表示。
    """
    d = sp.diff(expr, var)
    roots = sorted({sp.re(r) for r in sp.solve(sp.Eq(d, 0), var) if r.is_real is not False})
    bounds = [None] + roots + [None]
    out = []
    for i in range(len(bounds) - 1):
        l, r = bounds[i], bounds[i + 1]
        if l is None:
            probe = sp.sympify(lo)
        elif r is None:
            probe = sp.sympify(hi)
        else:
            probe = sp.simplify((l + r) / 2)
        s = sp.sign(d.subs(var, probe))
        if s == 0:
            continue
        out.append({"interval": (l, r), "sign": int(s), "mono": "增" if s > 0 else "减"})
    return out


def parity_check(expr, var=x):
    """奇偶性：返回 'odd' / 'even' / 'neither'，并给出 f(-x) 化简式。"""
    fm = sp.simplify(expr.subs(var, -var))
    if sp.simplify(fm + expr) == 0:
        return "odd", fm
    if sp.simplify(fm - expr) == 0:
        return "even", fm
    return "neither", fm


def zero_interval(expr, a0, b0, var=x):
    """零点存在性检查：f(a0), f(b0) 异号 → 返回端点函数值与符号。"""
    a0, b0 = sp.sympify(a0), sp.sympify(b0)
    fa, fb = sp.simplify(expr.subs(var, a0)), sp.simplify(expr.subs(var, b0))
    assert sp.sign(fa) * sp.sign(fb) < 0, "端点不同号，零点存在定理不适用"
    return {"fa": fa, "fb": fb}


def bisect_zero(expr, a0, b0, rounds=4, var=x):
    """二分法逼近零点 rounds 轮，返回每轮 (lo, hi, mid, f(mid))。"""
    lo, hi = sp.sympify(a0), sp.sympify(b0)
    hist = []
    for _ in range(rounds):
        mid = sp.simplify((lo + hi) / 2)
        fm = sp.simplify(expr.subs(var, mid))
        hist.append({"lo": lo, "hi": hi, "mid": mid, "fm": fm})
        if sp.sign(fm) == 0:
            break
        if sp.sign(fm) * sp.sign(expr.subs(var, lo)) > 0:
            lo = mid
        else:
            hi = mid
    return hist


def left_right_derivative(expr, x0, var=x):
    """左右导数（用极限定义，适合 |x| 这类不可导点）。"""
    x0 = sp.sympify(x0)
    d = sp.diff(expr, var) if expr.has(var) else expr
    # 用差分极限而不是 diff，避免在角点自动失败/误判
    dl = sp.limit((expr.subs(var, x0 - e) - expr.subs(var, x0)) / (-e), e, 0, "+")
    dr = sp.limit((expr.subs(var, x0 + e) - expr.subs(var, x0)) / e, e, 0, "+")
    return sp.simplify(dl), sp.simplify(dr)


# ==================== 题型函数 ====================

def solve_tangent_line(expr=None, x0=1):
    """题型 1：切线方程。"""
    expr = x ** 2 if expr is None else sp.sympify(expr)
    x0 = sp.sympify(x0)
    k, y0 = tangent_at(expr, x0)
    return {
        "expr": expr, "x0": x0, "y0": y0, "k": k,
        "line_expr": sp.simplify(k * (x - x0) + y0),
        "line_latex": tangent_line_latex(expr, x0),
        "d_expr": derivative(expr),
        "answer_latex": tex(sp.expand(k * (x - x0) + y0)),
    }


def solve_secant_limit(expr=None, x0=1):
    """题型 2：割线逼近切线（导数定义）。返回割线斜率表达式 k(h)。"""
    expr = x ** 2 if expr is None else sp.sympify(expr)
    x0 = sp.sympify(x0)
    k_h = sp.simplify((expr.subs(x, x0 + h) - expr.subs(x, x0)) / h)
    k0 = sp.simplify(sp.limit(k_h, h, 0))
    assert sp.simplify(k0 - derivative(expr).subs(x, x0)) == 0, "割线极限应等于导数"
    return {
        "expr": expr, "x0": x0, "k_h": k_h, "k0": k0,
        "d_expr": derivative(expr),
        "answer_latex": tex(k0),
    }


def solve_cubic_extrema(a=1, b=-3, c=0, d=0):
    """题型 3：三次函数 f(x)=ax³+bx²+cx+d 的极值与单调区间。"""
    a_, b_, c_, d_ = map(sp.sympify, (a, b, c, d))
    expr = a_ * x ** 3 + b_ * x ** 2 + c_ * x + d_
    exts = extrema_of(expr)
    mono = monotonic_intervals(expr)
    assert exts, "三次函数应有驻点"
    return {
        "expr": expr, "d_expr": derivative(expr),
        "extrema": exts, "mono": mono,
        "answer_latex": "; ".join(
            f"{e['kind']}值 {tex(e['value'])} (x={tex(e['x0'])})" for e in exts
        ),
    }


def solve_parity(expr):
    """题型 4：奇偶性判断。"""
    expr = sp.sympify(expr)
    kind, fm = parity_check(expr)
    return {"expr": expr, "fm": fm, "kind": kind,
            "answer_latex": {"odd": "奇函数", "even": "偶函数", "neither": "非奇非偶"}[kind]}


def solve_zero_crossing(expr, a0, b0):
    """题型 5：零点存在定理 + 二分逼近。"""
    expr = sp.sympify(expr)
    ends = zero_interval(expr, a0, b0)
    hist = bisect_zero(expr, a0, b0, rounds=4)
    # 真值（用数值求根，展示用）
    real_roots = [sp.re(r) for r in sp.solve(sp.Eq(expr, 0), x) if r.is_real is not False]
    inside = [r for r in real_roots if sp.sympify(a0) <= r <= sp.sympify(b0)]
    root_approx = sp.N(inside[0], 6) if inside else None
    return {
        "expr": expr, "a0": sp.sympify(a0), "b0": sp.sympify(b0),
        "ends": ends, "hist": hist, "root_approx": root_approx,
        "answer_latex": f"\\approx {sp.latex(root_approx)}" if root_approx else "无",
    }


def solve_exp_family(base):
    """题型 6：指数函数 y=aˣ（a>0 且 a≠1）。"""
    a0 = sp.sympify(base)
    assert a0 > 0 and a0 != 1, "底数需 >0 且 ≠1"
    expr = a0 ** x
    return {
        "expr": expr, "base": a0, "d_expr": derivative(expr),
        "f0": sp.Integer(1), "f1": a0,
        "answer_latex": "1",
    }


def solve_abs_corner(c=0):
    """题型 7：f(x)=|x-c| 在 x=c 处不可导，求左右导数。"""
    c0 = sp.sympify(c)
    expr = sp.Abs(x - c0)
    dl, dr = left_right_derivative(expr, c0)
    assert dl != dr, "左右导数应不等（不可导）"
    return {"expr": expr, "c": c0, "dl": dl, "dr": dr,
            "answer_latex": f"{tex(dl)} \\ne {tex(dr)}"}


def solve_tangent_family(expr=None):
    """题型 8：曲线 y=ln x 在 x=a 处的切线，问 a 为何值时切线过定点/求切线恒过的点。

    取 f(x)=ln x：切线 y - ln a = (1/a)(x - a) ⇒ y = x/a + ln a - 1，
    当 a=e 时斜率 1/e……更经典的定值：切线在 y 轴截距 = ln a - 1。
    这里给定参数 a（画板滑块），求任意 a 下切线与 y 轴截距公式 + 展示族。
    """
    expr = sp.log(x) if expr is None else sp.sympify(expr)
    d = derivative(expr)
    a_sym = sp.Symbol("a", positive=True)
    k, y0 = tangent_at(expr, a_sym)
    y_intercept = sp.simplify(y0 - k * a_sym)
    return {
        "expr": expr, "d_expr": d, "a_sym": a_sym, "k": k, "y0": y0,
        "y_intercept": y_intercept,
        "answer_latex": tex(y_intercept),
    }


# ==================== 自检 ====================
if __name__ == "__main__":
    print("== 1. 切线 y=x² @x0=1 ==")
    s = solve_tangent_line(x ** 2, 1)
    print("  k =", tex(s["k"]), " 切线:", s["line_latex"])
    assert s["k"] == 2 and sp.simplify(s["line_expr"] - (2 * x - 1)) == 0

    print("== 2. 割线极限 y=x² @1 ==")
    s = solve_secant_limit(x ** 2, 1)
    print("  k(h) =", tex(s["k_h"]), " 极限 =", tex(s["k0"]))
    assert s["k_h"] == 2 + h and s["k0"] == 2

    print("== 3. 三次 f=x³-3x 极值 ==")
    s = solve_cubic_extrema(1, 0, -3, 0)
    for e_ in s["extrema"]:
        print(f"  {e_['kind']}: x={tex(e_['x0'])}, 值={tex(e_['value'])}")
    for m in s["mono"]:
        print(f"  区间 {m['interval']}: {m['mono']}")
    assert len(s["extrema"]) == 2
    kinds = sorted(e_["kind"] for e_ in s["extrema"])
    assert kinds == ["极大", "极小"]
    assert s["mono"][0]["mono"] == "增" and s["mono"][1]["mono"] == "减"

    print("== 4. 奇偶性 x³(odd), x²(even), x³+x²(neither) ==")
    assert solve_parity(x ** 3)["kind"] == "odd"
    assert solve_parity(x ** 2)["kind"] == "even"
    assert solve_parity(x ** 3 + x ** 2)["kind"] == "neither"

    print("== 5. 零点 x³-x-2 在 [1,2] ==")
    s = solve_zero_crossing(x ** 3 - x - 2, 1, 2)
    print("  f(1) =", tex(s["ends"]["fa"]), " f(2) =", tex(s["ends"]["fb"]),
          " 根 ≈", s["root_approx"])
    assert tex(s["ends"]["fa"]) == "-2" and tex(s["ends"]["fb"]) == "4"
    assert abs(float(s["root_approx"]) - 1.5213797) < 1e-5

    print("== 6. 指数 y=2ˣ f(0), f(1) ==")
    s = solve_exp_family(2)
    assert s["f0"] == 1 and s["f1"] == 2
    print("  f(0) =", tex(s["f0"]), " f(1) =", tex(s["f1"]))

    print("== 7. |x| 在 0 处左右导数 ==")
    s = solve_abs_corner(0)
    print("  左 =", tex(s["dl"]), " 右 =", tex(s["dr"]))
    assert s["dl"] == -1 and s["dr"] == 1

    print("== 8. 切线族 y=ln x，y 轴截距 ==")
    s = solve_tangent_family()
    print("  截距 =", s["answer_latex"])
    assert sp.simplify(s["y_intercept"] - (sp.log(sp.Symbol('a', positive=True)) - 1)) == 0

    print("\n全部自检通过")
