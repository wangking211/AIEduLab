# -*- coding: utf-8 -*-
"""
geom_kernel.py — 初中平面几何确定性计算核心（sympy 精确符号运算）。

设计哲学与 edu-analytic-geometry 一致（单一数据源）：答案、坐标、角度、线段比、
各步中间量全部由本模块精确算出，杜绝心算误差。同一套坐标既喂给解题文案，也喂给
2D 画板渲染，保证"图、解、答"严格一致。

坐标约定：数学坐标，y 轴向上（画板模板已按此约定渲染）。

覆盖（v1，8 个题型）：
 1. 勾股定理（直角三角形三边关系 + 三边正方形面积）
 2. 圆周角定理（同弧所对圆周角 = 圆心角一半）
 3. 切割线定理（PT² = PA·PB，圆幂）
 4. 相交弦定理（PA·PB = PC·PD，圆幂）
 5. 相似三角形 A 型（DE∥BC，AD/AB = AE/AC = DE/BC）
 6. 三角形中位线（DE∥BC 且 DE = BC/2）
 7. 三角形内切圆与内心（角平分线交点，r = 2S/p）
 8. 三角形外接圆与外心（中垂线交点，R = abc/4S）

依赖: sympy（pip install sympy）。自检：python geom_kernel.py
"""

import math

import sympy as sp

sqrt = sp.sqrt


# ---------------- 通用工具 ----------------
def tex(expr):
    return sp.latex(sp.simplify(expr))


def f(e):
    return float(sp.N(e))


def is_clean(e):
    """答案是否"规整"（有理数或最简根式），随机出题筛选用。"""
    e = sp.nsimplify(sp.simplify(e))
    return e.is_rational or (e.free_symbols == set() and sp.simplify(e - sp.nsimplify(e)) == 0)


def V(*comps):
    return sp.Matrix([sp.sympify(c) for c in comps])


def dist(a, b):
    return sp.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def dot(u, v):
    return u[0] * v[0] + u[1] * v[1]


def cross2(u, v):
    """二维叉积标量 u×v。"""
    return u[0] * v[1] - u[1] * v[0]


def angle_at(A, B, C):
    """∠ABC（顶点 B），返回弧度的 sympy 表达式（atan2 形式，主值 [0, π]）。"""
    u = A - B
    v = C - B
    return sp.atan2(sp.Abs(cross2(u, v)), dot(u, v))


def angle_deg(A, B, C):
    return sp.simplify(angle_at(A, B, C) * 180 / sp.pi)


def midpoint(a, b):
    return sp.simplify((a + b) / 2)


def foot_perp(P, A, B):
    """P 到直线 AB 的垂足。"""
    ab = B - A
    t = sp.simplify(dot(P - A, ab) / dot(ab, ab))
    return sp.simplify(A + t * ab)


def line_intersect(A, B, C, D):
    """直线 AB ∩ 直线 CD（Cramer 法则，精确）。"""
    d1 = B - A
    d2 = D - C
    den = cross2(d1, d2)
    if den == 0:
        raise ValueError("两直线平行，无交点")
    t = sp.simplify(cross2(C - A, d2) / den)
    return sp.simplify(A + t * d1)


def circle_through(A, B, C):
    """不共线三点的外接圆：返回 (圆心, 半径)。中垂线交点法。"""
    M1, M2 = midpoint(A, B), midpoint(B, C)
    d1, d2 = B - A, C - B
    O = line_intersect(M1, M1 + V(-d1[1], d1[0]), M2, M2 + V(-d2[1], d2[0]))
    return O, sp.simplify(dist(O, A))


def incenter_radius(A, B, C):
    """内心 I 与内切圆半径 r。I = (aA+bB+cC)/(a+b+c)，r = 2S/p。"""
    a, b, c = dist(B, C), dist(A, C), dist(A, B)
    p = a + b + c
    I = sp.simplify((a * A + b * B + c * C) / p)
    S = sp.Abs(cross2(B - A, C - A)) / 2
    r = sp.simplify(2 * S / p)
    return I, r, {"a": a, "b": b, "c": c, "p": sp.simplify(p), "S": sp.simplify(S)}


def circumradius(A, B, C):
    """外接圆半径 R = abc / 4S。"""
    a, b, c = dist(B, C), dist(A, C), dist(A, B)
    S = sp.Abs(cross2(B - A, C - A)) / 2
    return sp.simplify(a * b * c / (4 * S))


def unit(v):
    n = sp.sqrt(dot(v, v))
    return sp.simplify(v / n), n


# ---------------- 题型 1：勾股定理 ----------------
def solve_pythagoras(a=3, b=4):
    """直角△ABC（C 为直角），三边向外作正方形。

    返回坐标、三边长、正方形面积、c 的精确值。
    """
    a, b = sp.sympify(a), sp.sympify(b)
    C, A, B = V(0, 0), V(a, 0), V(0, b)
    c = sp.simplify(dist(A, B))
    assert sp.simplify(a ** 2 + b ** 2 - c ** 2) == 0, "勾股关系自检失败"
    # 三边向外的正方形顶点（用于画板 polygon）
    # CA 边（x 轴正向）向下作正方形；CB 边（y 轴正向）向左；AB 斜边向外
    sq_a = [C, A, A + V(0, -a), C + V(0, -a)]              # 边 a=CA
    sq_b = [C, B, B + V(-b, 0), C + V(-b, 0)]              # 边 b=CB
    n = sp.Matrix([-b, a]) / c                              # 斜边外法向
    sq_c = [A, B, B + n * c, A + n * c]                     # 边 c=AB
    return {
        "pts": {"A": A, "B": B, "C": C},
        "a": a, "b": b, "c": c,
        "Sq_a": sp.simplify(a ** 2), "Sq_b": sp.simplify(b ** 2), "Sq_c": sp.simplify(c ** 2),
        "squares": {"sq_a": sq_a, "sq_b": sq_b, "sq_c": sq_c},
        "answer_latex": tex(c),
    }


# ---------------- 题型 2：圆周角定理 ----------------
def solve_inscribed(R=2, central_deg=80):
    """圆 O 中，∠AOB = central_deg（圆心角），C 为优弧 AB 上动点。

    结论：同弧所对圆周角 ∠ACB = central/2（恒定）。
    返回圆心、半径、A/B 坐标（C 由画板参数驱动）。
    """
    R, central = sp.sympify(R), sp.sympify(central_deg)
    half = central / 2
    O = V(0, 0)
    # A、B 关于 x 轴对称放置：∠AOB = central
    A = V(R * sp.cos(half * sp.pi / 180), -R * sp.sin(half * sp.pi / 180))
    B = V(R * sp.cos(half * sp.pi / 180), R * sp.sin(half * sp.pi / 180))
    inscribed = sp.simplify(central / 2)
    return {
        "O": O, "A": sp.simplify(A), "B": sp.simplify(B), "R": R,
        "central_deg": central, "inscribed_deg": inscribed,
        "answer_latex": tex(inscribed) + "^\\circ",
    }


# ---------------- 题型 3：切割线定理 ----------------
def solve_tangent_secant(R=3, OP=5):
    """⊙O 半径 R，P 在圆外且 OP 给定。PT 切圆于 T，PAB 为割线。

    PT² = PA·PB = OP² − R²（点 P 对 ⊙O 的幂）。返回切点 T（取上方那个）。
    """
    R, d = sp.sympify(R), sp.sympify(OP)
    assert d > R, "P 必须在圆外"
    O, P = V(0, 0), V(d, 0)
    # 切点：OT ⊥ PT，|OT|=R → T = (R²/d, ±R√(d²−R²)/d)
    Tx = sp.simplify(R ** 2 / d)
    Ty = sp.simplify(R * sqrt(d ** 2 - R ** 2) / d)
    T = V(Tx, Ty)
    PT = sp.simplify(dist(P, T))
    assert sp.simplify(PT ** 2 - (d ** 2 - R ** 2)) == 0, "切割线定理自检失败"
    power = sp.simplify(d ** 2 - R ** 2)
    return {
        "O": O, "P": P, "T": T, "R": R,
        "PT": PT, "power": power,
        "answer_latex": tex(power),
    }


# ---------------- 题型 4：相交弦定理 ----------------
def solve_chord_product(R=5, d=3, theta_deg=30):
    """⊙O 半径 R，圆内一点 P 距圆心 d。过 P 的弦 AB 与 CD。

    PA·PB = PC·PD = R² − d²（点 P 对 ⊙O 的幂，取负号方向的绝对值）。
    返回 P 与两弦方向（画板上 AB 固定为 x 轴方向，CD 由参数角度驱动）。
    """
    R, d, th = sp.sympify(R), sp.sympify(d), sp.sympify(theta_deg)
    assert d < R, "P 必须在圆内"
    O, P = V(0, 0), V(d, 0)
    power = sp.simplify(R ** 2 - d ** 2)
    return {
        "O": O, "P": P, "R": R, "power": power,
        "answer_latex": tex(power),
    }


# ---------------- 题型 5：相似三角形（A 型） ----------------
def solve_similar_A(A, B, C, k=sp.Rational(1, 2)):
    """△ABC 中 DE∥BC，D 在 AB 上且 AD/AB = k。求 AE/AC 与 DE/BC。

    返回 D、E 坐标与三个比值（都应等于 k）。
    """
    k = sp.simplify(sp.sympify(k))
    A, B, C = sp.sympify(A), sp.sympify(B), sp.sympify(C)
    D = sp.simplify(A + k * (B - A))
    E = sp.simplify(A + k * (C - A))
    r1 = sp.simplify(dist(A, D) / dist(A, B))
    r2 = sp.simplify(dist(A, E) / dist(A, C))
    r3 = sp.simplify(dist(D, E) / dist(B, C))
    assert sp.simplify(r1 - k) == 0 and sp.simplify(r2 - k) == 0 and sp.simplify(r3 - k) == 0, \
        "A 型相似三比相等自检失败"
    return {
        "pts": {"A": A, "B": B, "C": C, "D": D, "E": E},
        "k": k, "ratios": (r1, r2, r3),
        "answer_latex": tex(k),
    }


# ---------------- 题型 6：三角形中位线 ----------------
def solve_midsegment(A, B, C):
    """D、E 分别为 AB、AC 中点。DE = BC/2 且 DE∥BC。"""
    A, B, C = sp.sympify(A), sp.sympify(B), sp.sympify(C)
    D, E = midpoint(A, B), midpoint(A, C)
    de, bc = sp.simplify(dist(D, E)), sp.simplify(dist(B, C))
    assert sp.simplify(de - bc / 2) == 0, "中位线定理自检失败"
    return {
        "pts": {"A": A, "B": B, "C": C, "D": D, "E": E},
        "DE": de, "BC": bc,
        "answer_latex": tex(de),
    }


# ---------------- 题型 7：内切圆与内心 ----------------
def solve_incircle(A, B, C):
    """△ABC 的内心 I、内切圆半径 r 及三切点（各边上的垂足）。"""
    A, B, C = sp.sympify(A), sp.sympify(B), sp.sympify(C)
    I, r, vals = incenter_radius(A, B, C)
    feet = {
        "BC": foot_perp(I, B, C),
        "AC": foot_perp(I, A, C),
        "AB": foot_perp(I, A, B),
    }
    assert all(sp.simplify(dist(I, p) - r) == 0 for p in feet.values()), "切点距离自检失败"
    return {
        "pts": {"A": A, "B": B, "C": C},
        "I": I, "r": r, "feet": feet, "vals": vals,
        "answer_latex": tex(r),
    }


# ---------------- 题型 8：外接圆与外心 ----------------
def solve_circumcircle(A, B, C):
    """△ABC 的外心 O、外接圆半径 R。"""
    A, B, C = sp.sympify(A), sp.sympify(B), sp.sympify(C)
    O, R = circle_through(A, B, C)
    R2 = circumradius(A, B, C)
    assert sp.simplify(R - R2) == 0, "外心/外径公式一致性自检失败"
    return {
        "pts": {"A": A, "B": B, "C": C},
        "O": O, "R": R,
        "answer_latex": tex(R),
    }


# ==================== 自检 ====================
if __name__ == "__main__":
    print("== 1. 勾股定理 3-4-5 ==")
    s = solve_pythagoras(3, 4)
    print("  c =", s["answer_latex"], " Sq:", s["Sq_a"], s["Sq_b"], s["Sq_c"])
    assert s["c"] == 5 and s["Sq_a"] + s["Sq_b"] == s["Sq_c"]

    print("== 2. 圆周角定理 中心角80 ==")
    s = solve_inscribed(2, 80)
    print("  圆周角 =", s["answer_latex"])
    assert s["inscribed_deg"] == 40

    print("== 3. 切割线定理 R=3 OP=5 ==")
    s = solve_tangent_secant(3, 5)
    print("  PT =", tex(s["PT"]), " PT² =", s["answer_latex"])
    assert s["power"] == 16 and s["PT"] == 4

    print("== 4. 相交弦定理 R=5 d=3 ==")
    s = solve_chord_product(5, 3)
    print("  PA·PB =", s["answer_latex"])
    assert s["power"] == 16

    print("== 5. A 型相似 k=1/2 ==")
    s = solve_similar_A(V(0, 0), V(6, 0), V(2, 4), sp.Rational(1, 2))
    print("  比 =", s["answer_latex"], " D=", tex(s["pts"]["D"].T), " E=", tex(s["pts"]["E"].T))
    assert s["ratios"] == (sp.Rational(1, 2),) * 3

    print("== 6. 中位线 ==")
    s = solve_midsegment(V(0, 0), V(6, 0), V(2, 4))
    print("  DE =", s["answer_latex"], " BC =", tex(s["BC"]))
    assert s["BC"] == 2 * s["DE"] and s["DE"] == 2 * sp.sqrt(2)

    print("== 7. 内切圆 直角3-4-5 ==")
    s = solve_incircle(V(0, 0), V(3, 0), V(0, 4))
    print("  I =", tex(s["I"].T), " r =", s["answer_latex"])
    assert s["r"] == 1, "3-4-5 内切圆半径应为 1"

    print("== 8. 外接圆 直角3-4-5（外心=斜边中点，R=斜边/2）==")
    s = solve_circumcircle(V(0, 0), V(3, 0), V(0, 4))
    print("  O =", tex(s["O"].T), " R =", s["answer_latex"])
    assert s["R"] == sp.Rational(5, 2)

    print("\n全部自检通过")
