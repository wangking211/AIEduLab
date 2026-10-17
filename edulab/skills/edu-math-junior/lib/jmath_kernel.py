# -*- coding: utf-8 -*-
"""
jmath_kernel.py —— 初中代数与函数确定性计算核心（sympy 精确运算）。

覆盖四块初中代数的「数形结合」：
  1. 一次函数 y = kx + b —— 斜率、截距、与坐标轴交点、两直线交点、增减性
  2. 二次函数 y = ax² + bx + c —— 开口、顶点、对称轴、判别式、根、最值、区间最值、韦达
  3. 一元二次不等式 —— 解集（区间表示 + LaTeX）
  4. 因式分解 —— 十字相乘（整数系数）
  5. 锐角三角函数 —— 已知一锐角与一边，求三边与三角比

设计哲学与其它技能一致（单一数据源）：答案、顶点坐标、根、区间、图上标注的每个数
都由本模块精确算出，同一套值既喂给文字，也喂给画板，保证「图、解、答」严格一致。
**不手写数字。**

坐标约定：数学坐标，y 轴向上。

依赖 sympy。自检：python jmath_kernel.py
"""

import math

import sympy as sp

x = sp.symbols("x")
sqrt = sp.sqrt


# ---------------------------------------------------------------- 输出格式

def tex(e):
    """sympy 表达式 → LaTeX 片段（不包 $）。"""
    return sp.latex(e)


def f(e, digits=None):
    """sympy 表达式 → 浮点；给 digits 时按该精度四舍五入。"""
    v = float(sp.N(e, 20))
    return round(v, digits) if digits is not None else v


def js(expr):
    """把 sympy 表达式翻译成 JS 表达式（供画板 evalExpr 逐点采样）。"""
    return sp.jscode(sp.simplify(expr)).replace("Math.", "")


def num_str(e):
    """数值的紧凑文本：整数按整数，分数按 p/q，其余保留 6 位有效数字。"""
    if isinstance(e, sp.Integer):
        return str(int(e))
    fr = sp.nsimplify(e)
    if isinstance(fr, sp.Rational) and fr.q != 1 and abs(fr.q) <= 1000:
        return f"{fr.p}/{fr.q}"
    v = float(sp.N(e, 20))
    s = f"{v:.6g}"
    return s


def interval_tex(lo, hi, lo_open=True, hi_open=True):
    """把端点格式化成区间记号；None 表示无穷。"""
    def end(v, inf_sign):
        if v is None:
            return f"{inf_sign}\\infty"
        return num_str(v)
    l = ("(" if lo_open else "[") + end(lo, "-") + ",\\," + end(hi, "+") + (")" if hi_open else "]")
    return l


# ---------------------------------------------------------------- 一次函数

def solve_linear(k, b):
    """y = kx + b。

    返回斜率、纵截距、与 x 轴交点（k=0 时无）、增减性、以及两点。
    """
    k, b = sp.nsimplify(k), sp.nsimplify(b)
    expr = k * x + b
    if k == 0:
        monotone = "常数（不增不减）"
        xint = None
    else:
        monotone = "增函数" if k > 0 else "减函数"
        xint = -b / k
    return {
        "k": k, "b": b, "expr": expr, "tex": tex(expr),
        "xint": xint,                # 与 x 轴交点横坐标
        "yint": b,                   # 与 y 轴交点纵坐标
        "monotone": monotone,
        "points": [(-2, expr.subs(x, -2)), (2, expr.subs(x, 2))],
    }


def intersect_lines(k1, b1, k2, b2):
    """两直线交点；平行（含重合）返回 None。"""
    k1, b1, k2, b2 = map(sp.nsimplify, (k1, b1, k2, b2))
    if sp.simplify(k1 - k2) == 0:
        return None
    xi = sp.simplify((b2 - b1) / (k1 - k2))
    yi = sp.simplify(k1 * xi + b1)
    return {"x": xi, "y": yi}


# ---------------------------------------------------------------- 二次函数

def solve_quadratic(a, b, c):
    """y = ax² + bx + c 的完整画像。a ≠ 0。"""
    a, b, c = sp.nsimplify(a), sp.nsimplify(b), sp.nsimplify(c)
    if a == 0:
        raise ValueError("二次函数要求 a ≠ 0（这是" + str(a) + "）")

    D = sp.simplify(b * b - 4 * a * c)
    h = sp.simplify(-b / (2 * a))                 # 对称轴 x
    k = sp.simplify(c - b * b / (4 * a))          # 顶点纵坐标
    opening = "向上" if a > 0 else "向下"

    if D > 0:
        r1 = sp.simplify((-b - sqrt(D)) / (2 * a))
        r2 = sp.simplify((-b + sqrt(D)) / (2 * a))
        r1, r2 = min(r1, r2), max(r1, r2)
        roots = [r1, r2]
        root_desc = "两个不等实根"
    elif D == 0:
        r = sp.simplify(-b / (2 * a))
        roots = [r]
        root_desc = "两个相等实根（重根）"
    else:
        roots = []
        root_desc = "没有实根"

    return {
        "a": a, "b": b, "c": c,
        "expr": a * x * x + b * x + c,
        "tex": tex(a * x * x + b * x + c),
        "D": D, "tex_D": num_str(D),
        "h": h, "k": k, "vertex": (h, k),
        "axis": h,
        "opening": opening,
        "roots": roots,
        "root_desc": root_desc,
        "root_count": len(roots),
        "extreme": k,
        "extreme_kind": "最小值" if a > 0 else "最大值",
        "yint": c,
        # 韦达
        "sum": sp.simplify(-b / a),
        "prod": sp.simplify(c / a),
    }


def interval_extremum(a, b, c, lo, hi):
    """y=ax²+bx+c 在闭区间 [lo, hi] 上的最值（顶点在区间内才取顶点值）。"""
    s = solve_quadratic(a, b, c)
    lo, hi = sp.nsimplify(lo), sp.nsimplify(hi)
    if lo > hi:
        lo, hi = hi, lo
    h = s["h"]
    cand = [(lo, s["expr"].subs(x, lo)), (hi, s["expr"].subs(x, hi))]
    inside = lo <= h <= hi
    if inside:
        cand.append((h, s["k"]))
    vals = [v for _xx, v in cand]
    vmax, vmin = max(vals), min(vals)
    return {
        "max": sp.simplify(vmax), "min": sp.simplify(vmin),
        "at_max": [xx for xx, v in cand if v == vmax],
        "at_min": [xx for xx, v in cand if v == vmin],
        "vertex_inside": bool(inside),
        "lo": lo, "hi": hi,
        "solve": s,
    }


# ---------------------------------------------------------------- 一元二次不等式

def solve_quadratic_ineq(a, b, c, op):
    """ax² + bx + c op 0，op ∈ {'>', '<', '>=', '<='}。

    返回解集的区间列表（用 None 表示 ±∞）以及 LaTeX。
    """
    a, b, c = sp.nsimplify(a), sp.nsimplify(b), sp.nsimplify(c)
    if a == 0:
        raise ValueError("一元二次不等式要求 a ≠ 0")
    ops = {">", ">=", "<", "<="}
    if op not in ops:
        raise ValueError(f"op 必须是 {sorted(ops)} 之一")

    s = solve_quadratic(a, b, c)
    D = s["D"]
    loose = op in (">=", "<=")
    strict = not loose
    positive = a > 0

    # 把「表达式 ≥ 0」统一成「a>0 时的方向」判断
    want_positive = op in (">", ">=")
    if not positive:
        want_positive = not want_positive

    intervals = []      # [(lo, hi)]，None 表示无穷
    if D < 0:
        # 恒正或恒负
        if want_positive:
            intervals = [(None, None)]
    elif D == 0:
        r = s["roots"][0]
        if want_positive:
            if loose:
                intervals = [(None, None)]
            else:
                intervals = [(None, r), (r, None)]
        else:
            if loose:
                intervals = [(r, r)]
    else:
        r1, r2 = s["roots"]
        if want_positive:
            if loose:
                intervals = [(None, r1), (r2, None)]
            else:
                intervals = [(None, r1), (r2, None)]
        else:
            intervals = [(r1, r2)]

    # 开闭：严格不等号取开区间；非严格在有限端点取闭
    parts = []
    for lo, hi in intervals:
        lo_open = strict if lo is not None else True
        hi_open = strict if hi is not None else True
        parts.append(interval_tex(lo, hi, lo_open, hi_open))
    latex = r" \cup ".join(parts) if parts else r"\varnothing"
    return {
        "intervals": intervals,
        "empty": not intervals,
        "latex": latex,
        "solve": s,
        "op": op,
        "strict": strict,
    }


# ---------------------------------------------------------------- 因式分解（十字相乘）

def factor_quadratic(a, b, c):
    """ax² + bx + c 的整数系数因式分解（十字相乘）。

    返回 (p, q, r, s) 使 (px+q)(rx+s)，其中 p*r=a、q*s=c、p*s+q*r=b；
    不能分解为整数系数时返回 None。
    """
    a, b, c = int(a), int(b), int(c)
    if a == 0:
        return None
    for p in _divisors(abs(a)):
        for pp in (p, -p):
            if pp == 0 or a % pp != 0:
                continue
            r = a // pp
            for q in _divisors(abs(c)) if c != 0 else [0]:
                for qq in ((q, -q) if q != 0 else (0,)):
                    if c == 0:
                        ss = [0]
                    elif qq == 0 or c % qq != 0:
                        continue
                    else:
                        ss = [c // qq]
                    for s in ss:
                        if pp * s + qq * r == b:
                            return (pp, qq, r, s)
    return None


def _divisors(n):
    n = abs(int(n))
    if n == 0:
        return [0]
    out = []
    i = 1
    while i * i <= n:
        if n % i == 0:
            out.append(i)
            if i != n // i:
                out.append(n // i)
        i += 1
    return sorted(out)


def factor_text(fac):
    """(p,q,r,s) → LaTeX 形式的因式分解串。"""
    if not fac:
        return None
    p, q, r, s = fac

    def lin(k, m):
        if k == 1:
            body = f"x"
        elif k == -1:
            body = f"-x"
        else:
            body = f"{k}x"
        if m > 0:
            return f"({body}+{m})"
        if m < 0:
            return f"({body}{m})"
        return f"({body})"

    return lin(p, q) + lin(r, s)


# ---------------------------------------------------------------- 锐角三角函数

def solve_right_triangle(angle_deg, side, side_name):
    """直角三角形：已知一锐角 ∠A = angle_deg 与一条边，求其余边与三角比。

    side_name ∈ {"opp", "adj", "hyp"}（对边 / 邻边 / 斜边）。
    返回三边、三角比、另一锐角、面积。
    """
    if not (0 < float(angle_deg) < 90):
        raise ValueError("锐角必须在 (0°, 90°) 之间")
    A = sp.nsimplify(angle_deg) * sp.pi / 180
    side = sp.nsimplify(side)
    if side <= 0:
        raise ValueError("边长必须为正")

    sinA, cosA, tanA = sp.sin(A), sp.cos(A), sp.tan(A)
    if side_name == "opp":
        opp = side
        hyp = sp.simplify(side / sinA)
        adj = sp.simplify(side / tanA)
    elif side_name == "adj":
        adj = side
        hyp = sp.simplify(side / cosA)
        opp = sp.simplify(side * tanA)
    elif side_name == "hyp":
        hyp = side
        opp = sp.simplify(side * sinA)
        adj = sp.simplify(side * cosA)
    else:
        raise ValueError("side_name 必须是 opp / adj / hyp")

    B = sp.pi / 2 - A
    return {
        "A_deg": sp.nsimplify(angle_deg),
        "B_deg": sp.simplify(90 - sp.nsimplify(angle_deg)),
        "opp": opp, "adj": adj, "hyp": hyp,
        "sin": sp.simplify(sinA), "cos": sp.simplify(cosA), "tan": sp.simplify(tanA),
        "area": sp.simplify(opp * adj / 2),
        "given": side_name,
    }


# ---------------------------------------------------------------- 自检

def _selftest():
    cases = []

    def ok(cond, name):
        cases.append((bool(cond), name))

    # 一次函数
    L = solve_linear(2, -4)
    ok(L["k"] == 2 and L["b"] == -4, "一次函数 k / b")
    ok(L["xint"] == 2, "y=2x-4 与 x 轴交于 x=2")
    ok(L["yint"] == -4, "y=2x-4 纵截距 -4")
    ok(L["monotone"] == "增函数", "k>0 为增函数")
    ok(solve_linear(0, 3)["xint"] is None, "k=0 没有 x 轴交点")

    I = intersect_lines(2, -4, -1, 5)
    ok(I["x"] == 3 and I["y"] == 2, "两直线交点 (3, 2)")
    ok(intersect_lines(1, 1, 1, 5) is None, "平行线无交点")

    # 二次函数：y = x² - 2x - 3 = (x-3)(x+1)
    Q = solve_quadratic(1, -2, -3)
    ok(Q["D"] == 16, "判别式 Δ=16")
    ok(sorted(Q["roots"]) == [-1, 3], "两根 -1 与 3")
    ok(Q["vertex"] == (1, -4), "顶点 (1, -4)")
    ok(Q["axis"] == 1, "对称轴 x=1")
    ok(Q["opening"] == "向上", "a>0 开口向上")
    ok(Q["sum"] == 2 and Q["prod"] == -3, "韦达：和 2、积 -3")
    ok(Q["extreme"] == -4 and Q["extreme_kind"] == "最小值", "最小值 -4")
    ok(Q["yint"] == -3, "纵截距 -3")

    Q0 = solve_quadratic(1, -2, 1)          # (x-1)²
    ok(Q0["D"] == 0 and Q0["root_count"] == 1, "Δ=0 时重根只算一个")
    Qn = solve_quadratic(1, 0, 1)           # x²+1
    ok(Qn["D"] < 0 and Qn["root_count"] == 0, "Δ<0 没有实根")

    # 区间最值：y=x²-2x 在 [0,3]
    E = interval_extremum(1, -2, 0, 0, 3)
    ok(E["min"] == -1, "区间最小值 -1（顶点 x=1 在区间内）")
    ok(E["max"] == 3, "区间最大值 3（右端点）")
    E2 = interval_extremum(1, -2, 0, 2, 4)
    ok(E2["min"] == 0 and E2["max"] == 8, "顶点不在区间内时端点取最值")
    ok(E2["vertex_inside"] is False, "顶点不在区间内的判定")

    # 不等式
    U = solve_quadratic_ineq(1, -2, -3, ">")     # x²-2x-3>0 → x<-1 或 x>3
    ok(len(U["intervals"]) == 2, "x²-2x-3>0 解集是两段")
    ok(U["intervals"][0][1] == -1 and U["intervals"][1][0] == 3, "解集端点 -1 与 3")
    U2 = solve_quadratic_ineq(1, -2, -3, "<")    # → (-1, 3)
    ok(len(U2["intervals"]) == 1 and U2["intervals"][0] == (-1, 3), "x²-2x-3<0 解集 (-1,3)")
    U3 = solve_quadratic_ineq(1, 0, 1, ">")      # x²+1>0 恒成立
    ok(U3["intervals"] == [(None, None)], "x²+1>0 恒成立")
    U4 = solve_quadratic_ineq(1, 0, 1, "<")      # x²+1<0 无解
    ok(U4["empty"], "x²+1<0 无解")
    U5 = solve_quadratic_ineq(-1, 2, 3, ">")     # -x²+2x+3>0 → (-1,3)
    ok(U5["intervals"] == [(-1, 3)], "a<0 时方向自动翻转")

    # 因式分解
    ok(factor_quadratic(1, -2, -3) in [(1, -3, 1, 1), (1, 1, 1, -3)], "x²-2x-3 十字相乘")
    ok(factor_quadratic(1, 0, 1) is None, "x²+1 在整数范围内不可分解")
    ok(factor_quadratic(6, 5, -6) is not None, "6x²+5x-6 可分解")
    F = factor_quadratic(1, -2, -3)
    ok(factor_text(F) in ("(x-3)(x+1)", "(x+1)(x-3)"), "因式分解文本")

    # 锐角三角函数：30° 对边 1 → 斜边 2、邻边 √3
    T = solve_right_triangle(30, 1, "opp")
    ok(T["hyp"] == 2, "30° 对边 1 → 斜边 2")
    ok(sp.simplify(T["adj"] - sqrt(3)) == 0, "30° 对边 1 → 邻边 √3")
    ok(T["B_deg"] == 60, "另一锐角 60°")
    ok(sp.simplify(T["sin"] - sp.Rational(1, 2)) == 0, "sin30° = 1/2")
    T2 = solve_right_triangle(45, 2, "hyp")
    ok(sp.simplify(T2["opp"] - sqrt(2)) == 0, "45° 斜边 2 → 对边 √2")

    bad = [c for c in cases if not c[0]]
    for good, name in cases:
        print(f"  {'✓' if good else '✗'} {name}")
    print(f"\n{'初中代数内核自检通过 ✓' if not bad else f'{len(bad)} 项失败'}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
