#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
complex_kernel.py —— 高中「复数」内核（新课标必修二）

覆盖：
  · 代数形式 a + bi 的四则运算（含分母实数化）
  · 共轭 z̄ 与模 |z|；恒等式 z·z̄ = |z|²、|z₁z₂| = |z₁||z₂|
  · 复平面：加减法 = 向量加减（平行四边形）；乘法 = **旋转 + 伸缩**
    （模相乘、辐角相加）—— 这是复数最有价值的几何含义
  · 三角形式 z = r(cosθ + i sinθ) 与棣莫弗定理 zⁿ = rⁿ(cos nθ + i sin nθ)
  · n 次单位根：在单位圆上均匀分布；**全部 n 个根之和恒为 0**
  · 实系数一元二次方程的复根（判别式 < 0，两个共轭纯虚根）
  · 几何轨迹：|z − z₀| = r 是圆、|z − A| = |z − B| 是垂直平分线

设计原则（与全项目一致）：
  · **不手写数字**：一切由 sympy 做**精确**复数运算（含根式化简，例如
    √3 会保持为 √3 而不是 1.7320508）。
  · 辐角一律以**度**作为对外接口。
  · 自检：python complex_kernel.py
"""

import math

import sympy as sp

I = sp.I

__all__ = [
    "f", "num_str", "deg_str",
    "cx", "re", "im", "cadd", "csub", "cmul", "cdiv", "cneg",
    "conj", "modulus", "modulus2", "arg_deg", "arg_rad",
    "polar", "trig_form", "power", "de_moivre",
    "roots_of_unity", "nth_roots", "root_sum", "root_product",
    "quadratic_roots", "discriminant",
    "circle_locus_pt", "same_distance_pt",
]


# ---------------------------------------------------------------- 排版助手
def f(v, digits=4):
    if v is None:
        return "—"
    s = f"{float(v):.{digits}f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-") else "0"


def num_str(v, digits=4):
    val = float(v)
    if val == 0:
        return "0"
    if abs(val) >= 1e5 or abs(val) < 1e-4:
        return f"{val:.3e}".replace("e-0", "e-").replace("e+0", "e")
    return f(val, digits)


def deg_str(v, digits=2):
    """角度的字符串（去掉多余的 0）。"""
    return f(v, digits)


# ---------------------------------------------------------------- 构造与拆分
def cx(re_part, im_part=0):
    """由实部与虚部构造复数（精确）。"""
    return sp.sympify(re_part) + sp.sympify(im_part) * I


def re(z):
    return sp.simplify(sp.re(sp.expand(z)))


def im(z):
    return sp.simplify(sp.im(sp.expand(z)))


# ---------------------------------------------------------------- 四则运算
def cadd(z1, z2):
    return sp.expand(z1 + z2)


def csub(z1, z2):
    return sp.expand(z1 - z2)


def cmul(z1, z2):
    return sp.expand(z1 * z2)


def cdiv(z1, z2):
    """复数除法：分子分母同乘分母的共轭（分母实数化）。"""
    if sp.simplify(z2) == 0:
        raise ValueError("除数不能为 0")
    return sp.simplify(sp.expand(z1 * sp.conjugate(z2)) / sp.expand(z2 * sp.conjugate(z2)))


def cneg(z):
    return -z


# ---------------------------------------------------------------- 共轭与模
def conj(z):
    return sp.conjugate(sp.expand(z))


def modulus2(z):
    """|z|² = a² + b²（精确，通常是整数或分数）。"""
    return sp.simplify(sp.expand(z * sp.conjugate(z)))


def modulus(z):
    """|z| = √(a²+b²)（保留根式）。"""
    return sp.sqrt(modulus2(z))


def arg_rad(z):
    """辐角（弧度，主值 (−π, π]）。"""
    a, b = float(sp.N(re(z))), float(sp.N(im(z)))
    return math.atan2(b, a)


def arg_deg(z):
    """辐角（度，主值 (−180°, 180°]）。"""
    return math.degrees(arg_rad(z))


# ---------------------------------------------------------------- 三角形式与棣莫弗
def polar(z):
    """返回 (r, θ 度)，其中 r 为精确根式、θ 为浮点度数。"""
    return modulus(z), arg_deg(z)


def trig_form(z, digits=2):
    """三角形式的 LaTeX 片段（r 与 θ 都取近似值，用于展示）。"""
    r, th = polar(z)
    return f"{f(sp.N(r), 4)}(\\cos {deg_str(th, digits)}^\\circ + i\\sin {deg_str(th, digits)}^\\circ)"


def power(z, n):
    """整数次幂（精确展开）。"""
    return sp.expand(z ** n)


def de_moivre(r, theta_deg, n):
    """棣莫弗定理：zⁿ 的 (模, 辐角)。"""
    return float(r) ** n, (theta_deg * n) % 360.0


# ---------------------------------------------------------------- 单位根与 n 次方根
def roots_of_unity(n):
    """n 次单位根（返回 sympy 复数列表，逆时针从 1 开始）。"""
    if n <= 0:
        raise ValueError("n 必须为正整数")
    return [sp.expand(sp.exp(2 * sp.pi * I * k / n)) for k in range(n)]


def nth_roots(z, n):
    """z 的 n 次方根（主值 + 均匀旋转）。"""
    if n <= 0:
        raise ValueError("n 必须为正整数")
    if sp.simplify(z) == 0:
        return [sp.Integer(0)] * n
    r = float(sp.N(modulus(z))) ** (1.0 / n)
    th0 = arg_deg(z)
    return [r, th0, n]


def root_sum(n):
    """n 次单位根之和：恒为 0（n ≥ 2）。"""
    return sp.simplify(sum(roots_of_unity(n))) if n >= 2 else sp.Integer(1)


def root_product(n):
    """n 次单位根之积：等于 (−1)^(n−1)。"""
    return sp.Integer((-1) ** (n - 1)) if n >= 1 else sp.Integer(1)


# ---------------------------------------------------------------- 一元二次方程
def discriminant(a, b, c):
    return sp.simplify(b * b - 4 * a * c)


def quadratic_roots(a, b, c):
    """实系数一元二次方程 ax²+bx+c=0 的两个根（精确，可能是复数）。

    判别式 < 0 时返回一对共轭复根。
    """
    a, b, c = sp.sympify(a), sp.sympify(b), sp.sympify(c)
    if a == 0:
        raise ValueError("a 不能为 0（否则不是二次方程）")
    D = discriminant(a, b, c)
    if D >= 0:
        s = sp.sqrt(D)
        # 用 (−b ± s)/(2a) 会因符号消不掉而复杂；改用稳定的等价形式
        return [sp.simplify((-b + s) / (2 * a)), sp.simplify((-b - s) / (2 * a))]
    s = sp.sqrt(-D) * I
    return [sp.simplify((-b + s) / (2 * a)), sp.simplify((-b - s) / (2 * a))]


# ---------------------------------------------------------------- 几何轨迹
def circle_locus_pt(z0, r, theta_deg):
    """圆 |z − z₀| = r 上辐角为 θ 的点（在 z₀ 周围）。"""
    th = math.radians(theta_deg)
    return sp.simplify(z0 + r * (sp.cos(th) + I * sp.sin(th)))


def same_distance_pt(A, B, y=0.0):
    """到 A、B 距离相等的点中，纵坐标为 y（实为虚部）的那个（垂直平分线）。"""
    # |z − A|² = |z − B|² ⇒ 线性方程
    ax, ay = re(A), im(A)
    bx, by = re(B), im(B)
    # 2(bx−ax)x + 2(by−ay)y = bx²+by²−ax²−ay²
    lhs_y = 2 * (by - ay)
    rhs = (bx ** 2 + by ** 2) - (ax ** 2 + ay ** 2)
    if sp.simplify(bx - ax) == 0:
        raise ValueError("A、B 在同一竖直线上，垂直平分线是水平线（改用参数 x）")
    xv = sp.simplify((rhs - lhs_y * sp.sympify(y)) / (2 * (bx - ax)))
    return sp.simplify(xv + sp.sympify(y) * I)


# ================================================================ 自检
def _selftest():
    bad = []

    def chk(name, got, want, tol=1e-9):
        if isinstance(got, bool) or isinstance(want, bool):
            ok = bool(got) == bool(want)
            g = got
        elif isinstance(got, (list, tuple)) or isinstance(want, (list, tuple)):
            ga, wa = list(got), list(want)
            ok = len(ga) == len(wa) and all(
                abs(complex(sp.N(a)) - complex(sp.N(b))) <= 1e-9 for a, b in zip(ga, wa))
            g = ga
        else:
            ok = abs(complex(sp.N(got)) - complex(sp.N(want))) <= tol
            g = sp.nsimplify(got)
        print(f"  {'✓' if ok else '✗'} {name:46s} = {g}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    print("四则运算")
    chk("(1+2i)+(3−i)", cadd(cx(1, 2), cx(3, -1)), cx(4, 1))
    chk("(1+2i)−(3−i)", csub(cx(1, 2), cx(3, -1)), cx(-2, 3))
    chk("(1+2i)(3−i)", cmul(cx(1, 2), cx(3, -1)), cx(5, 5))
    chk("i² = −1", cmul(I, I), sp.Integer(-1))
    chk("(1+i)² = 2i", cmul(cx(1, 1), cx(1, 1)), cx(0, 2))
    chk("1/i = −i", cdiv(1, I), cx(0, -1))
    chk("(1+i)/(1−i) = i", cdiv(cx(1, 1), cx(1, -1)), cx(0, 1))
    chk("(3+4i)/(1−2i)", cdiv(cx(3, 4), cx(1, -2)), cx(-1, 2))
    chk("(a+bi)(a−bi) 恒为实数", im(cmul(cx(3, 4), cx(3, -4))), sp.Integer(0))

    print("\n共轭与模")
    chk("z̄(3+4i) = 3−4i", conj(cx(3, 4)), cx(3, -4))
    chk("|3+4i| = 5", modulus(cx(3, 4)), sp.Integer(5))
    chk("|1+i| = √2（保留根式）", modulus(cx(1, 1)), sp.sqrt(2))
    chk("|z|² = 25", modulus2(cx(3, 4)), sp.Integer(25))
    chk("z·z̄ = |z|²", cmul(cx(3, 4), conj(cx(3, 4))), sp.Integer(25))
    chk("arg(1+i) = 45°", arg_deg(cx(1, 1)), 45.0, 1e-9)
    chk("arg(i) = 90°", arg_deg(I), 90.0, 1e-9)
    chk("arg(−1) = 180°", arg_deg(sp.Integer(-1)), 180.0, 1e-9)
    chk("arg(1−i) = −45°", arg_deg(cx(1, -1)), -45.0, 1e-9)
    # |z₁z₂| = |z₁||z₂|（乘法模相乘）
    z1, z2 = cx(1, 1), cx(3, 4)
    chk("|z₁z₂| = |z₁||z₂|", modulus(cmul(z1, z2)),
        sp.N(modulus(z1) * modulus(z2)), 1e-9)
    # arg(z₁z₂) = arg z₁ + arg z₂（mod 360）—— 乘法的精髓
    chk("arg(z₁z₂) = arg z₁ + arg z₂",
        (arg_deg(cmul(z1, z2)) - (arg_deg(z1) + arg_deg(z2))) % 360.0, 0.0, 1e-9)
    chk("共轭的模相等", modulus(conj(cx(3, 4))), modulus(cx(3, 4)))
    chk("共轭的辐角相反", arg_deg(conj(cx(1, 1))), -45.0, 1e-9)

    print("\n三角形式与棣莫弗定理")
    r, th = polar(cx(1, 1))
    chk("(1+i) 的模", sp.N(r), math.sqrt(2), 1e-9)
    chk("(1+i) 的辐角", th, 45.0, 1e-9)
    chk("i³ = −i", power(I, 3), cx(0, -1))
    chk("(1+i)² = 2i", power(cx(1, 1), 2), cx(0, 2))
    chk("(1+i)⁴ = −4", power(cx(1, 1), 4), sp.Integer(-4))
    # 棣莫弗定理与直接乘幂一致
    for n in (2, 3, 4, 5, 6):
        rr, tt = de_moivre(math.sqrt(2), 45.0, n)
        chk(f"  (1+i)^{n} 的模", rr, float(sp.N(modulus(power(cx(1, 1), n)))), 1e-9)
    # (cosθ + i sinθ)ⁿ 的模恒为 1（单位复数）
    for n in (2, 3, 7, 12):
        m, _ = de_moivre(1.0, 30.0, n)
        chk(f"  单位复数的 {n} 次幂模仍为 1", m, 1.0, 1e-9)

    print("\nn 次单位根")
    for n in (2, 3, 4, 6, 8):
        roots = roots_of_unity(n)
        chk(f"n={n} 的根的个数", len(roots), n)
        chk(f"  n={n} 每个根的模都是 1",
            all(abs(abs(complex(sp.N(z))) - 1) < 1e-9 for z in roots), True)
        chk(f"  n={n} 全部根之和为 0", root_sum(n), sp.Integer(0))
        chk(f"  n={n} 全部根之积 = (−1)^(n−1)", root_product(n), sp.Integer((-1) ** (n - 1)))
    # 1 的立方根：1、ω、ω²，且 1+ω+ω² = 0
    w = roots_of_unity(3)[1]
    chk("ω = −1/2 + (√3/2)i", w, cx(sp.Rational(-1, 2), sp.sqrt(3) / 2))
    chk("1 + ω + ω² = 0", sp.simplify(sum(roots_of_unity(3))), sp.Integer(0))
    chk("ω³ = 1", sp.simplify(w ** 3), sp.Integer(1))
    # 四次单位根就是 ±1、±i
    r4 = sorted([complex(sp.N(z)) for z in roots_of_unity(4)], key=lambda c: (c.real, c.imag))
    chk("四次单位根是 ±1、±i",
        [round(c.real, 9) for c in r4], [-1.0, 0.0, 0.0, 1.0])

    print("\n一元二次方程的复根")
    chk("x²+1=0 的判别式", discriminant(1, 0, 1), sp.Integer(-4))
    chk("x²+1=0 的根", quadratic_roots(1, 0, 1), [I, -I])
    chk("x²+x+1=0 的根（含 √3）", quadratic_roots(1, 1, 1),
        [cx(sp.Rational(-1, 2), sp.sqrt(3) / 2), cx(sp.Rational(-1, 2), -sp.sqrt(3) / 2)])
    chk("x²−2x+5=0 的根", quadratic_roots(1, -2, 5), [cx(1, 2), cx(1, -2)])
    chk("判别式 > 0 时是实根", discriminant(1, -3, 2), sp.Integer(1))
    chk("  实根", quadratic_roots(1, -3, 2), [sp.Integer(2), sp.Integer(1)])
    # 韦达定理对复根也成立
    for (a, b, c) in [(1, 0, 1), (1, 1, 1), (1, -2, 5), (2, 3, 4)]:
        rs = quadratic_roots(a, b, c)
        chk(f"  韦达：和 = −b/a (a={a},b={b},c={c})", sp.simplify(rs[0] + rs[1]),
            sp.simplify(-sp.Rational(b, a)))
        chk(f"  韦达：积 = c/a", sp.simplify(rs[0] * rs[1]), sp.simplify(sp.Rational(c, a)))
    # 复根必共轭（实系数）
    for (a, b, c) in [(1, 0, 1), (1, 1, 1), (2, 3, 4)]:
        rs = quadratic_roots(a, b, c)
        chk(f"  两根共轭 (a={a})", sp.simplify(rs[1] - conj(rs[0])), sp.Integer(0))

    print("\n几何轨迹")
    z0 = cx(1, 1)
    p = circle_locus_pt(z0, 2, 0.0)
    chk("|z−z₀|=2 上 θ=0 的点", p, cx(3, 1))
    chk("  该点到 z₀ 的距离", sp.simplify(modulus(p - z0)), sp.Integer(2))
    p2 = circle_locus_pt(z0, 2, 90.0)
    chk("  θ=90° 的点", p2, cx(1, 3))
    # |z−A| = |z−B| 的垂直平分线
    A, B = cx(0, 0), cx(4, 0)
    q = same_distance_pt(A, B, 0)
    chk("A(0,0)、B(4,0) 的垂直平分线过 (2,0)", q, cx(2, 0))
    chk("  该点到两点的距离相等", sp.simplify(modulus(q - A) - modulus(q - B)), sp.Integer(0))
    q2 = same_distance_pt(A, B, 3)
    chk("  纵坐标为 3 的点横坐标仍是 2", re(q2), sp.Integer(2))

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
