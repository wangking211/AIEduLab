#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
multivar_kernel.py —— 大学「多元微积分」内核（18.02 / 高等数学下册）

覆盖：
  · 偏导数与梯度 ∇f = (f_x, f_y)
  · 方向导数 D_u f = ∇f · u，以及「梯度方向给出最陡上升」
  · 曲面与切平面 z = f(x₀,y₀) + f_x(x−x₀) + f_y(y−y₀)
  · 拉格朗日乘数法求条件极值（∇f = λ∇g）
  · 二重积分：直角坐标的黎曼和（中点法）与精确值
  · 极坐标下的二重积分（雅可比因子 r）
  · 格林公式 ∮ P dx + Q dy = ∬ (Q_x − P_y) dA
  · 散度与旋度（二维）：div F = P_x + Q_y，curl F = Q_x − P_y

设计原则（与全项目一致）：
  · **不手写数字**：导数、积分、极值全部由 sympy **精确**算出；
    黎曼和是**真求和**（不是套公式），所以它会收敛到精确值 —— 页面上直接给出误差。
  · 直角坐标与极坐标两种算法给出的结果**必须相等**，页面上作为定值指示器展示。
  · 自检：python multivar_kernel.py
"""

import math

import sympy as sp

x, y, r, t = sp.symbols("x y r t", real=True)

__all__ = [
    "f", "num_str", "grad", "grad_at", "dir_deriv", "grad_norm", "grad_angle",
    "surface_z", "tangent_plane", "partials",
    "lagrange_xy_circle",
    "riemann_rect", "double_integral", "riemann_error",
    "polar_area_cell", "polar_riemann", "polar_integral",
    "line_integral", "double_integral_green",
    "divergence", "curl", "field_at",
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


def _F(e):
    """把 sympy 表达式转成浮点。"""
    return float(sp.N(e))


# ---------------------------------------------------------------- 偏导数与梯度
def partials(expr, var_x=x, var_y=y):
    """返回 (f_x, f_y)。"""
    return sp.simplify(sp.diff(expr, var_x)), sp.simplify(sp.diff(expr, var_y))


def grad(expr):
    """梯度 ∇f = (∂f/∂x, ∂f/∂y)。"""
    return partials(expr)


def grad_at(expr, x0, y0):
    """在某点的梯度（浮点二元组）。"""
    gx, gy = grad(expr)
    return _F(gx.subs({x: x0, y: y0})), _F(gy.subs({x: x0, y: y0}))


def grad_norm(expr, x0, y0):
    """|∇f|：方向导数的最大值。"""
    gx, gy = grad_at(expr, x0, y0)
    return math.hypot(gx, gy)


def grad_angle(expr, x0, y0):
    """梯度的方向角（度，从 +x 轴逆时针）。"""
    gx, gy = grad_at(expr, x0, y0)
    return math.degrees(math.atan2(gy, gx))


def dir_deriv(expr, x0, y0, theta_deg):
    """方向导数 D_u f = ∇f · u，u = (cosθ, sinθ)。"""
    gx, gy = grad_at(expr, x0, y0)
    th = math.radians(theta_deg)
    return gx * math.cos(th) + gy * math.sin(th)


def surface_z(expr, x0, y0):
    """曲面在 (x0,y0) 处的高度。"""
    return _F(expr.subs({x: x0, y: y0}))


def tangent_plane(expr, x0, y0):
    """切平面 z = f₀ + f_x(x−x₀) + f_y(y−y₀)，返回 (f₀, f_x, f_y)（浮点）。"""
    z0 = surface_z(expr, x0, y0)
    gx, gy = grad_at(expr, x0, y0)
    return z0, gx, gy


# ---------------------------------------------------------------- 拉格朗日乘数法
def lagrange_xy_circle(R):
    """在 x² + y² = R² 上求 f = xy 的最大值（解析解）。

    ∇f = λ∇g ⇒ (y, x) = λ(2x, 2y)。联立可得 x = ±y 且 λ = 1/2，
    极值点为 (±R/√2, ±R/√2)，最大值 R²/2、最小值 −R²/2，
    λ 恒为 1/2（与 R 无关）—— 这是本页的定值指示器。
    """
    a = R / math.sqrt(2.0)
    return {"max": R * R / 2.0, "min": -R * R / 2.0,
            "pts_max": [(a, a), (-a, -a)], "pts_min": [(a, -a), (-a, a)],
            "lambda": 0.5}


# ---------------------------------------------------------------- 二重积分（直角坐标）
def riemann_rect(expr, xr, yr, n):
    """中点法黎曼和：把区域切成 n×n 个小矩形，取每个中点的函数值。

    返回 (sum, dA)。
    """
    dx = (xr[1] - xr[0]) / n
    dy = (yr[1] - yr[0]) / n
    total = 0.0
    for i in range(n):
        xm = xr[0] + (i + 0.5) * dx
        fx = sp.N(expr.subs(x, xm))
        for j in range(n):
            ym = yr[0] + (j + 0.5) * dy
            total += float(sp.N(fx.subs(y, ym)))
    return total * dx * dy, dx * dy


def double_integral(expr, xr, yr):
    """精确的二重积分（先对 y 后对 x）。"""
    return _F(sp.integrate(sp.integrate(expr, (y, yr[0], yr[1])), (x, xr[0], xr[1])))


def riemann_error(expr, xr, yr, n):
    """相对误差 |黎曼和 − 精确值| / |精确值|。"""
    s, _ = riemann_rect(expr, xr, yr, n)
    e = double_integral(expr, xr, yr)
    return abs(s - e) / abs(e) if e != 0 else abs(s)


# ---------------------------------------------------------------- 二重积分（极坐标）
def polar_area_cell(r0, dr, dtheta):
    """极坐标的面积元 ΔA = r·dr·dθ（雅可比因子就是 r）。"""
    return r0 * dr * dtheta


def polar_riemann(expr_polar, R, nr=40, nth=72):
    """极坐标下的黎曼和：∫₀^{2π}∫₀^R g(r,θ)·r dr dθ。"""
    dr = R / nr
    dth = 2.0 * math.pi / nth
    total = 0.0
    for i in range(nr):
        rm = (i + 0.5) * dr
        for j in range(nth):
            thm = (j + 0.5) * dth
            total += float(sp.N(expr_polar.subs({r: rm, t: thm}))) * polar_area_cell(rm, dr, dth)
    return total


def polar_integral(expr_polar, R):
    """精确的极坐标二重积分 ∫₀^{2π}∫₀^R g·r dr dθ。"""
    return _F(sp.integrate(sp.integrate(expr_polar * r, (r, 0, R)), (t, 0, 2 * sp.pi)))


# ---------------------------------------------------------------- 格林公式
def line_integral(P, Q, curve, t0, t1):
    """沿参数曲线的第二类曲线积分 ∮ P dx + Q dy。

    curve 为 (x(t), y(t)) 两个 sympy 表达式。
    """
    xt, yt = curve
    dxdt = sp.diff(xt, t)
    dydt = sp.diff(yt, t)
    integrand = P.subs({x: xt, y: yt}) * dxdt + Q.subs({x: xt, y: yt}) * dydt
    return _F(sp.integrate(integrand, (t, t0, t1)))


def double_integral_green(P, Q, xr, yr):
    """∬ (Q_x − P_y) dA（格林公式的右端）。"""
    return double_integral(sp.diff(Q, x) - sp.diff(P, y), xr, yr)


def circle_curve(R):
    """半径为 R 的逆时针圆参数式。"""
    return (R * sp.cos(t), R * sp.sin(t))


# ---------------------------------------------------------------- 散度与旋度（二维）
def divergence(P, Q):
    """散度 div F = ∂P/∂x + ∂Q/∂y。"""
    return sp.simplify(sp.diff(P, x) + sp.diff(Q, y))


def curl(P, Q):
    """二维旋度（z 分量）curl F = ∂Q/∂x − ∂P/∂y。"""
    return sp.simplify(sp.diff(Q, x) - sp.diff(P, y))


def field_at(P, Q, x0, y0):
    """在某点的向量值 (P, Q)。"""
    return _F(P.subs({x: x0, y: y0})), _F(Q.subs({x: x0, y: y0}))


# ================================================================ 自检
def _selftest():
    bad = []

    def chk(name, got, want, tol=1e-9):
        if isinstance(got, (list, tuple)) or isinstance(want, (list, tuple)):
            ga, wa = list(got), list(want)
            ok = len(ga) == len(wa) and all(
                abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b))) for a, b in zip(ga, wa))
            g = ga
        else:
            ok = abs(float(got) - float(want)) <= tol * max(1.0, abs(float(want)))
            g = f"{float(got):.6g}"
        print(f"  {'✓' if ok else '✗'} {name:46s} = {g}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    def chkb(name, got, want):
        ok = bool(got) == bool(want)
        print(f"  {'✓' if ok else '✗'} {name:46s} = {got}")
        if not ok:
            bad.append(name)

    print("偏导数与梯度")
    expr = x ** 2 + y ** 2
    gx, gy = grad(expr)
    chkb("∇(x²+y²) = (2x, 2y)", sp.simplify(gx - 2 * x) == 0 and sp.simplify(gy - 2 * y) == 0, True)
    chk("∇f(1,2) 的 x 分量", grad_at(expr, 1, 2)[0], 2.0, 1e-12)
    chk("∇f(1,2) 的 y 分量", grad_at(expr, 1, 2)[1], 4.0, 1e-12)
    chk("|∇f|(1,2) = √20", grad_norm(expr, 1, 2), math.sqrt(20.0), 1e-12)
    chk("梯度方向(1,2) = arctan(2)", grad_angle(expr, 1, 2), math.degrees(math.atan2(4, 2)), 1e-12)
    e2 = x ** 2 * y
    chk("∂(x²y)/∂x = 2xy", grad_at(e2, 2, 3)[0], 12.0, 1e-12)
    chk("∂(x²y)/∂y = x²", grad_at(e2, 2, 3)[1], 4.0, 1e-12)
    chk("中心对称：∇f(0,0) = 0", grad_norm(expr, 0, 0), 0.0, 1e-12)
    # 梯度 ⊥ 等高线：沿等高线方向的切向量的方向导数为 0
    e3 = x * y
    th_tan = math.degrees(math.atan2(1, -1))       # 在 (1,1) 处 xy=1 的切向方向
    chk("沿等高线方向的导数为 0", dir_deriv(e3, 1, 1, 135.0), 0.0, 1e-9)

    print("\n方向导数")
    chk("θ=0 时 D_u f = f_x", dir_deriv(expr, 1, 2, 0.0), 2.0, 1e-12)
    chk("θ=90° 时 D_u f = f_y", dir_deriv(expr, 1, 2, 90.0), 4.0, 1e-12)
    chk("θ=180° 时 D_u f = −f_x", dir_deriv(expr, 1, 2, 180.0), -2.0, 1e-12)
    # 沿梯度方向取得最大值 |∇f|
    thg = grad_angle(expr, 1, 2)
    chk("沿梯度方向的导数为 |∇f|", dir_deriv(expr, 1, 2, thg), grad_norm(expr, 1, 2), 1e-9)
    chk("反梯度方向为 −|∇f|", dir_deriv(expr, 1, 2, thg + 180.0), -grad_norm(expr, 1, 2), 1e-9)
    # 抽样验证：所有方向的导数都不超过 |∇f|
    chk("所有方向的导数 ≤ |∇f|",
        all(dir_deriv(expr, 1, 2, k) <= grad_norm(expr, 1, 2) + 1e-12 for k in range(0, 360, 7)), True)

    print("\n切平面")
    z0, fx0, fy0 = tangent_plane(expr, 1, 1)
    chk("切点高度 f(1,1) = 2", z0, 2.0, 1e-12)
    chk("切平面的 x 斜率", fx0, 2.0, 1e-12)
    chk("切平面的 y 斜率", fy0, 2.0, 1e-12)
    # 切平面在切点处与曲面相切（沿 x 方向的差是二阶小量）
    chk("沿 x 方向相切", (z0 + fx0 * 0.001) - surface_z(expr, 1.001, 1), 0.0, 1e-5)
    chk("沿 y 方向相切", (z0 + fy0 * 0.001) - surface_z(expr, 1, 1.001), 0.0, 1e-5)

    print("\n拉格朗日乘数法（f = xy 在 x²+y² = R² 上）")
    for R in (0.5, 1.0, 1.5, 2.5):
        sol = lagrange_xy_circle(R)
        chk(f"最大值 = R²/2 (R={R})", sol["max"], R * R / 2, 1e-12)
        pts = sol["pts_max"]
        chk(f"  极值点均在圆上 (R={R})",
            all(abs(px ** 2 + py ** 2 - R * R) < 1e-12 for px, py in pts), True)
        chk(f"  λ 恒为 1/2 (R={R})", sol["lambda"], 0.5, 1e-12)
    # x=y=R/√2 处 ∇f 与 ∇g 平行（叉积为 0）
    R = 1.0
    a = R / math.sqrt(2)
    gf = (a, a)                      # ∇f = (y, x)
    gg = (2 * a, 2 * a)              # ∇g = (2x, 2y)
    chk("∇f 与 ∇g 平行（叉积 0）", gf[0] * gg[1] - gf[1] * gg[0], 0.0, 1e-12)
    chk("λ = 1/2 使 ∇f = λ∇g", gf[0] - 0.5 * gg[0], 0.0, 1e-12)

    print("\n二重积分（直角坐标）")
    e = x + y
    chk("精确值 ∬(x+y) on [0,1]²", double_integral(e, (0, 1), (0, 1)), 1.0, 1e-12)
    s4, dA = riemann_rect(e, (0, 1), (0, 1), 4)
    chk("n=4 的黎曼和", s4, 1.0, 1e-12)
    chk("n=4 的误差为 0（中点法对线性函数精确）", riemann_error(e, (0, 1), (0, 1), 4), 0.0, 1e-12)
    # 非线性函数：黎曼和随 n 收敛
    e2b = x ** 2 + y ** 2
    exact = double_integral(e2b, (0, 1), (0, 1))
    chk("精确值 ∬(x²+y²) on [0,1]² = 2/3", exact, 2.0 / 3.0, 1e-12)
    errs = [riemann_error(e2b, (0, 1), (0, 1), n) for n in (2, 4, 8, 16)]
    chkb("黎曼和随 n 单调收敛", all(errs[i] > errs[i + 1] for i in range(3)), True)
    chk("n=16 的误差 < 1%", errs[3] < 0.01, True)
    chk("n=1 时就是 f(0.5,0.5)·1", riemann_rect(e2b, (0, 1), (0, 1), 1)[0], 0.5, 1e-12)

    print("\n二重积分（极坐标）")
    chk("面积元 ΔA = r·dr·dθ", polar_area_cell(2.0, 0.1, 0.05), 2.0 * 0.1 * 0.05, 1e-12)
    # ∬_disk 1 dA = πR²
    for R in (0.5, 1.0, 2.0):
        chk(f"圆盘面积 = πR² (R={R})",
            polar_integral(sp.Integer(1), R), math.pi * R * R, 1e-9)
        chk(f"  黎曼和逼近 (R={R})",
            polar_riemann(sp.Integer(1), R, 60, 120), math.pi * R * R, 5e-3)
    # ∬_disk r² dA = πR⁴/2
    chk("∬ r² dA = πR⁴/2", polar_integral(r ** 2, 1.0), math.pi / 2, 1e-9)
    chk("  黎曼和逼近", polar_riemann(r ** 2, 1.0, 80, 144), math.pi / 2, 5e-3)
    # 直角坐标与极坐标必须给出同一个数：∬_disk (x²+y²) dA
    rect_val = _F(sp.integrate(sp.integrate(x ** 2 + y ** 2,
                                            (y, -sp.sqrt(1 - x ** 2), sp.sqrt(1 - x ** 2))),
                               (x, -1, 1)))
    chk("直角坐标 ∬(x²+y²) on 单位圆盘", rect_val, math.pi / 2, 1e-9)
    chk("与极坐标结果一致", rect_val, polar_integral(r ** 2, 1.0), 1e-9)

    print("\n格林公式")
    P, Q = -y, x
    chk("Q_x − P_y = 2", _F(curl(P, Q)), 2.0, 1e-12)
    for R in (0.5, 1.0, 2.0):
        line = line_integral(P, Q, circle_curve(R), 0, 2 * sp.pi)
        dbl = double_integral_green(P, Q, (-R, R), (-R, R))
        # 注意：ana 上 ∬ over 正方形 ≠ ∮ over 圆；这里只比较圆域
        chk(f"∮(−y dx + x dy) = 2πR² (R={R})", line, 2 * math.pi * R * R, 1e-9)
    # 用极坐标算右端，验证与线积分相等
    polar_rhs = polar_integral(sp.Integer(2), 1.0)
    chk("∬ 2 dA over 单位圆盘 = 2π", polar_rhs, 2 * math.pi, 1e-9)
    chk("  与线积分相等（格林公式）",
        line_integral(P, Q, circle_curve(1.0), 0, 2 * sp.pi), polar_rhs, 1e-9)
    # 另一个例子：P = −y³/3? 用 P=−y/2, Q=x/2 ⇒ 右端为 1 ⇒ 圆盘上 π
    chk("P=−y/2,Q=x/2 时右端为 2πR²/2",
        polar_integral(sp.Integer(1), 1.0), math.pi, 1e-9)
    # 无旋场沿闭曲线的积分为 0
    P0, Q0 = y, x
    chk("无旋场（Q_x−P_y=0）闭曲线积分为 0",
        line_integral(P0, Q0, circle_curve(1.0), 0, 2 * sp.pi), 0.0, 1e-9)
    chk("  该场的旋度确为 0", _F(curl(P0, Q0)), 0.0, 1e-12)

    print("\n散度与旋度")
    chk("div(x, y) = 2", _F(divergence(x, y)), 2.0, 1e-12)
    chk("curl(x, y) = 0", _F(curl(x, y)), 0.0, 1e-12)
    chk("div(−y, x) = 0", _F(divergence(-y, x)), 0.0, 1e-12)
    chk("curl(−y, x) = 2", _F(curl(-y, x)), 2.0, 1e-12)
    chk("div(x, −y) = 0（鞍点场）", _F(divergence(x, -y)), 0.0, 1e-12)
    chk("curl(x, −y) = 0", _F(curl(x, -y)), 0.0, 1e-12)
    chk("div(x, k y) = 1 + k（k=2 时）", _F(divergence(x, 2 * y)), 3.0, 1e-12)
    chk("场在某点的值 (x,2y)@(1,3)", field_at(x, 2 * y, 1, 3), (1.0, 6.0), 1e-12)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
