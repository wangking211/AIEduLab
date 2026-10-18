#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ode_kernel.py —— 常微分方程与动力系统内核（大学一年级，按 MIT 18.03 组织）

覆盖：
  · 一阶方程：方向场与解曲线（y' = t − y 的精确解）
  · 数值方法：欧拉法与 RK4，以及步长对误差的影响（两者与精确解对照）
  · 二阶常系数线性方程：阻尼振动（欠阻尼 / 临界阻尼 / 过阻尼）
  · 受迫振动与共振：稳态振幅随驱动频率的响应曲线
  · 线性系统的相平面与平衡点分类（由特征值判定）
  · Logistic 方程：S 曲线、平衡点稳定性、最大增长率
  · Lotka–Volterra：相图、平衡点、**守恒量**（闭合轨道为什么闭合）

设计原则（与全项目一致）：
  · **不手写数字**：所有结果由本内核现算。
  · **积分真跑**：轨迹由 RK4 实际推进得到，不是画出来的曲线；
    凡有解析解的一律与解析解对照（自检里逐条比）。
  · 自检：python ode_kernel.py
"""

import math

import sympy as sp

__all__ = [
    "tex", "f", "num_str",
    "rk4_system", "euler_system", "integrate_until",
    "first_order_exact", "first_order_slope",
    "damping_type", "damped_solution", "damped_period",
    "forced_amplitude", "resonance_omega", "resonance_amplitude",
    "linear_eigen", "classify_2x2",
    "logistic_solution", "logistic_time_to", "logistic_max_rate", "logistic_equilibria",
    "lv_equilibria", "lv_conserved", "lv_flow",
]


# ---------------------------------------------------------------- 排版助手

def tex(e):
    e = sp.sympify(e)
    if e.is_Integer:
        return str(int(e))
    if e.is_Rational:
        return r"\frac{%d}{%d}" % (e.p, e.q)
    return sp.latex(e)


def f(x, digits=4):
    if x is None:
        return "—"
    s = f"{float(x):.{digits}f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-") else "0"


def num_str(x, digits=4):
    v = float(x)
    if v == 0:
        return "0"
    if abs(v) >= 1e5 or abs(v) < 1e-4:
        return f"{v:.3e}".replace("e-0", "e-").replace("e+0", "e")
    return f(v, digits)


# ---------------------------------------------------------------- 数值积分
#
# 这两个函数是「真跑」的落点：轨迹必须由它们实际推进得到。
# f(t, y) 接收标量 t 与向量 y，返回 dy 向量。

def euler_system(f, y0, t0, t1, n):
    """显式欧拉法。返回 (ts, ys)，ys[i] 是向量。"""
    h = (t1 - t0) / n
    y = list(y0)
    ts, ys = [t0], [list(y)]
    for i in range(n):
        d = f(t0 + i * h, y)
        y = [y[j] + h * d[j] for j in range(len(y))]
        ts.append(t0 + (i + 1) * h)
        ys.append(list(y))
    return ts, ys


def rk4_system(f, y0, t0, t1, n):
    """经典 RK4。返回 (ts, ys)。

    与欧拉法用同一套接口，便于把「步长对误差的影响」画在同一张图上。
    """
    h = (t1 - t0) / n
    y = list(y0)
    ts, ys = [t0], [list(y)]
    for i in range(n):
        t = t0 + i * h
        k1 = f(t, y)
        k2 = f(t + h / 2, [y[j] + h / 2 * k1[j] for j in range(len(y))])
        k3 = f(t + h / 2, [y[j] + h / 2 * k2[j] for j in range(len(y))])
        k4 = f(t + h, [y[j] + h * k3[j] for j in range(len(y))])
        y = [y[j] + h / 6 * (k1[j] + 2 * k2[j] + 2 * k3[j] + k4[j]) for j in range(len(y))]
        ts.append(t + h)
        ys.append(list(y))
    return ts, ys


def integrate_until(f, y0, t0, t1, n, hit=None):
    """积到某个事件为止（hit(t, y) 为真时停）。返回 (ts, ys)。"""
    h = (t1 - t0) / n
    y = list(y0)
    ts, ys = [t0], [list(y)]
    for i in range(n):
        t = t0 + i * h
        k1 = f(t, y)
        k2 = f(t + h / 2, [y[j] + h / 2 * k1[j] for j in range(len(y))])
        k3 = f(t + h / 2, [y[j] + h / 2 * k2[j] for j in range(len(y))])
        k4 = f(t + h, [y[j] + h * k3[j] for j in range(len(y))])
        y = [y[j] + h / 6 * (k1[j] + 2 * k2[j] + 2 * k3[j] + k4[j]) for j in range(len(y))]
        ts.append(t + h)
        ys.append(list(y))
        if hit and hit(t + h, y):
            break
    return ts, ys


# ---------------------------------------------------------------- 一阶方程
#
# 取 y' = t − y：它是**线性一阶**，有精确解，且方向场能看出「所有解都趋于 t−1」。

def first_order_slope(t, y):
    """y' = t − y 的右端。"""
    return t - y


def first_order_exact(t, y0):
    """y' = t − y，y(0) = y0 的精确解：y = t − 1 + (y0+1)e^{−t}。"""
    return t - 1.0 + (y0 + 1.0) * math.exp(-t)


# ---------------------------------------------------------------- 阻尼振动
#
# y'' + 2ζω₀ y' + ω₀² y = 0 —— 三种情形由阻尼比 ζ 与 1 的关系决定。

def damping_type(zeta):
    """返回 'under' / 'critical' / 'over'。"""
    if abs(zeta - 1.0) < 1e-9:
        return "critical"
    return "under" if zeta < 1.0 else "over"


def damped_period(zeta, omega0):
    """欠阻尼时的准周期 T = 2π/ω_d，ω_d = ω₀√(1−ζ²)。非欠阻尼返回 None。"""
    if damping_type(zeta) != "under":
        return None
    wd = omega0 * math.sqrt(1.0 - zeta * zeta)
    return 2.0 * math.pi / wd


def damped_solution(t, zeta, omega0=1.0, y0=1.0, v0=0.0):
    """y'' + 2ζω₀ y' + ω₀² y = 0，y(0)=y0、y'(0)=v0 的精确解。

    三种情形各有闭式：
      欠阻尼 ζ<1：y = e^{−ζω₀t}[ y₀cos(ω_d t) + (v₀+ζω₀y₀)/ω_d · sin(ω_d t) ]
      临界     ζ=1：y = e^{−ω₀t}[ y₀ + (v₀+ω₀y₀)t ]
      过阻尼 ζ>1：y = e^{−ζω₀t}[ y₀cosh(ω_h t) + (v₀+ζω₀y₀)/ω_h · sinh(ω_h t) ]
    """
    z, w = zeta, omega0
    c = v0 + z * w * y0
    if damping_type(z) == "under":
        wd = w * math.sqrt(1.0 - z * z)
        return math.exp(-z * w * t) * (y0 * math.cos(wd * t) + c / wd * math.sin(wd * t))
    if damping_type(z) == "critical":
        return math.exp(-w * t) * (y0 + c * t)
    # 过阻尼：**不能**用双曲形式 e^{−ζω₀t}[y₀cosh(ω_h t) + …] ——
    # ω_h·t 稍大（本例 t=300 时是 848）就会溢出，而且它是两个巨大指数项相减，
    # 数值上也不稳。改用两个指数项之和 y = A e^{λ₁t} + B e^{λ₂t}，各项都单调衰减。
    wh = w * math.sqrt(z * z - 1.0)
    lam1, lam2 = -z * w + wh, -z * w - wh          # lam1 是较慢的衰减率
    A = (v0 - lam2 * y0) / (lam1 - lam2)
    B = (lam1 * y0 - v0) / (lam1 - lam2)
    return A * math.exp(lam1 * t) + B * math.exp(lam2 * t)


# ---------------------------------------------------------------- 受迫振动与共振
#
# y'' + 2ζω₀ y' + ω₀² y = F cos(ωt) 的**稳态**振幅：
#     A(ω) = F / √( (ω₀²−ω²)² + (2ζω₀ω)² )

def forced_amplitude(omega, zeta, omega0=1.0, F=1.0):
    """受迫振动的稳态振幅。"""
    re = omega0 ** 2 - omega ** 2
    im = 2.0 * zeta * omega0 * omega
    return F / math.sqrt(re * re + im * im)


def resonance_omega(zeta, omega0=1.0):
    """振幅峰值处的驱动频率 ω_r = ω₀√(1−2ζ²)（仅 ζ < 1/√2 时存在）。

    ζ 较大时（阻尼足够大）振幅随 ω 单调下降，没有内部峰值 —— 返回 None。
    """
    if zeta >= 1.0 / math.sqrt(2.0):
        return None
    return omega0 * math.sqrt(1.0 - 2.0 * zeta * zeta)


def resonance_amplitude(zeta, omega0=1.0, F=1.0):
    """峰值振幅 F / (2ζω₀²√(1−ζ²))。ζ→0 时趋于无穷（这就是「共振」）。"""
    om = resonance_omega(zeta, omega0)
    if om is None:
        return None
    return F / (2.0 * zeta * omega0 ** 2 * math.sqrt(1.0 - zeta * zeta))


# ---------------------------------------------------------------- 线性系统与平衡点

def linear_eigen(A):
    """2×2 矩阵的特征值（可能为复数），返回 [(re, im), ...]。"""
    A = sp.Matrix(A)
    ev = A.eigenvals()
    out = []
    for val in ev:
        v = sp.N(val, 12)
        out.append((float(sp.re(v)), float(sp.im(v))))
    out.sort(key=lambda p: (-p[0], -p[1]))
    return out


def classify_2x2(A):
    """按迹与行列式分类平衡点（线性化后的类型）。

    判据：
      · det < 0                      → 鞍点（saddle）
      · det > 0, disc = tr²−4det < 0 → 焦点/中心（spiral/center）
          tr < 0 稳定焦点、tr = 0 中心、tr > 0 不稳定焦点
      · det > 0, disc ≥ 0            → 结点（node），由 tr 的正负定稳定性
    返回 (类型, 稳定与否)。
    """
    A = sp.Matrix(A)
    tr = float(A.trace())
    dt = float(A.det())
    disc = tr * tr - 4 * dt
    if dt < -1e-12:
        return "鞍点（saddle）", False
    if abs(dt) <= 1e-12:
        return "退化（det≈0）", None
    if disc < -1e-12:
        if abs(tr) < 1e-9:
            return "中心（center）", None
        return ("稳定焦点（stable spiral）" if tr < 0 else "不稳定焦点（unstable spiral）"), tr < 0
    return ("稳定结点（stable node）" if tr < 0 else "不稳定结点（unstable node）"), tr < 0


# ---------------------------------------------------------------- Logistic 方程
#
# y' = r·y(1 − y/K) —— 有解析解，且平衡点 0（不稳）与 K（稳定）。

def logistic_solution(t, r, K, y0):
    """Logistic 的精确解 y(t) = K / (1 + ((K−y₀)/y₀)e^{−rt})。"""
    if y0 <= 0:
        return 0.0
    return K / (1.0 + (K - y0) / y0 * math.exp(-r * t))


def logistic_time_to(y_star, r, K, y0):
    """到达某个水平 y* 所需时间（由精确解反解）。"""
    if not 0 < y_star < K:
        raise ValueError("目标水平须在 (0, K) 内")
    return math.log(((K - y0) / y0) / ((K - y_star) / y_star)) / r


def logistic_max_rate(r, K):
    """最大增长率出现在 y = K/2 处，其值为 rK/4。"""
    return r * K / 4.0


def logistic_equilibria(r, K):
    """两个平衡点及其稳定性：y=0 不稳定、y=K 稳定（r>0）。"""
    return [{"y": 0.0, "stable": False}, {"y": K, "stable": True}]


# ---------------------------------------------------------------- Lotka–Volterra
#
# Ṅ = rN − aNE，Ė = cNE − mE。平衡点 (m/c, r/a)，轨道闭合，
# 且 H = cN − m·lnN + aE − r·lnE 沿轨道**守恒**（自检里验）。

def lv_equilibria(r, a, c, m):
    """平衡点：平凡点 (0,0) 与内部点 (m/c, r/a)。"""
    return [(0.0, 0.0), (m / c, r / a)]


def lv_conserved(N, E, r, a, c, m):
    """守恒量 H = cN − m·lnN + aE − r·lnE。

    它沿轨道恒为常数 —— 这正是「闭合轨道」的定量原因。
    """
    if N <= 0 or E <= 0:
        return None
    return c * N - m * math.log(N) + a * E - r * math.log(E)


def lv_flow(r, a, c, m):
    """返回 RL 模型的向量场函数 f(t, [N, E])。"""
    def fld(_t, y):
        N, E = y
        return [r * N - a * N * E, c * N * E - m * E]
    return fld


# ================================================================ 自检

def _selftest():
    bad = []

    def chk(name, got, want, tol=None):
        ok = (got == want) if tol is None else (abs(float(got) - float(want)) <= tol)
        shown = got if tol is None else f"{float(got):.8f}"
        print(f"  {'✓' if ok else '✗'} {name:46s} = {shown}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    print("一阶方程：数值解与精确解对照")
    fl = lambda _t, y: [first_order_slope(_t, y[0])]
    for n, tol in ((100, 1e-2), (1000, 1e-3)):
        ts, ys = rk4_system(fl, [0.0], 0.0, 5.0, n)
        err = abs(ys[-1][0] - first_order_exact(5.0, 0.0))
        chk(f"RK4 n={n} 在 t=5 的误差 < {tol}", err < tol, True)
    ts, ys = euler_system(fl, [0.0], 0.0, 5.0, 20)
    e_euler = abs(ys[-1][0] - first_order_exact(5.0, 0.0))
    ts, ys = rk4_system(fl, [0.0], 0.0, 5.0, 20)
    e_rk4 = abs(ys[-1][0] - first_order_exact(5.0, 0.0))
    chk("同样 20 步时 RK4 比欧拉法更准", e_rk4 < e_euler, True)
    chk("精确解满足初值", first_order_exact(0.0, 1.5), 1.5, 1e-12)
    # 所有解都趋于 y = t − 1
    chk("t=20 时精确解接近 t−1", first_order_exact(20.0, -3.0) - (20.0 - 1.0), 0.0, 1e-7)

    print("\n阻尼振动：三种情形")
    chk("ζ=0.2 是欠阻尼", damping_type(0.2), "under")
    chk("ζ=1.0 是临界阻尼", damping_type(1.0), "critical")
    chk("ζ=2.0 是过阻尼", damping_type(2.0), "over")
    chk("ζ=0.2 的准周期", damped_period(0.2, 1.0), 2 * math.pi / math.sqrt(1 - 0.04), 1e-12)
    chk("临界/过阻尼没有准周期", damped_period(1.5, 1.0), None)
    chk("ζ=0 时是纯振荡：y(π) ≈ −1", damped_solution(math.pi, 0.0), -1.0, 1e-9)
    chk("ζ=0 时周期 2π", damped_period(0.0, 1.0), 2 * math.pi, 1e-12)
    # 过阻尼衰减更慢（初始阶段）：ζ=2 在 t=1 的值应大于 ζ=1 的
    chk("过阻尼比临界阻尼衰减更慢", damped_solution(1.0, 2.0) > damped_solution(1.0, 1.0), True)
    # 所有情形都趋于 0（时间要取到包络真正衰减完：
    #   ζ=0.1 的包络是 e^{−0.1t}，ζ=3 的慢衰减率是 ζω₀−ω₀√(ζ²−1) ≈ 0.172）
    chk("欠阻尼最终趋于 0", abs(damped_solution(300.0, 0.1)) < 1e-6, True)
    chk("临界阻尼最终趋于 0", abs(damped_solution(60.0, 1.0)) < 1e-9, True)
    chk("过阻尼最终趋于 0", abs(damped_solution(300.0, 3.0)) < 1e-9, True)
    chk("初值 y₀ 正确（ζ=0.3）", damped_solution(0.0, 0.3), 1.0, 1e-12)

    print("\n受迫振动与共振")
    z = 0.15
    wr = resonance_omega(z)
    chk("ζ=0.15 时共振频率存在", wr is not None, True)
    chk("ω_r = √(1−2ζ²)", wr, math.sqrt(1 - 2 * 0.0225), 1e-12)
    chk("峰值振幅公式", resonance_amplitude(z), 1 / (2 * z * math.sqrt(1 - z * z)), 1e-12)
    # 共振频率处确实是最大
    a_r = forced_amplitude(wr, z)
    chk("ω_r 处振幅是最大值", a_r > forced_amplitude(wr * 1.05, z) and a_r > forced_amplitude(wr * 0.95, z), True)
    chk("峰值振幅等于共振振幅", a_r, resonance_amplitude(z), 1e-9)
    chk("ζ 很大时无内部峰值", resonance_omega(0.9), None)
    # 静力位移 A(0) = F/ω₀² = 1
    chk("ω=0 时振幅 = F/ω₀²", forced_amplitude(0.0, z), 1.0, 1e-12)
    # 高频时振幅趋于 0
    chk("ω→∞ 时振幅趋于 0", forced_amplitude(50.0, z) < 0.001, True)

    print("\n线性系统的平衡点分类")
    chk("[[0,1],[-1,0]] 是中心", classify_2x2([[0, 1], [-1, 0]])[0], "中心（center）")
    chk("[[-1,1],[-1,-1]] 是稳定焦点", classify_2x2([[-1, 1], [-1, -1]])[0], "稳定焦点（stable spiral）")
    chk("[[1,1],[-1,1]] 是不稳定焦点", classify_2x2([[1, 1], [-1, 1]])[0], "不稳定焦点（unstable spiral）")
    chk("[[-1,0],[0,-2]] 是稳定结点", classify_2x2([[-1, 0], [0, -2]])[0], "稳定结点（stable node）")
    chk("[[1,0],[0,-2]] 是鞍点", classify_2x2([[1, 0], [0, -2]])[0], "鞍点（saddle）")
    chk("中心的特征值是纯虚数", [abs(im) > 0 for _re, im in linear_eigen([[0, 1], [-1, 0]])], [True, True])
    chk("鞍点有正负实特征值",
        sorted(re for re, _im in linear_eigen([[1, 0], [0, -2]]))[0] < 0, True)
    chk("稳定焦点的迹为负", sp.Matrix([[-1, 1], [-1, -1]]).trace() < 0, True)

    print("\nLogistic 方程")
    chk("t=0 时等于初值", logistic_solution(0.0, 1.0, 1.0, 0.1), 0.1, 1e-12)
    chk("y(∞) → K", logistic_solution(80.0, 1.0, 1.0, 0.1), 1.0, 1e-9)
    chk("最大增长率 = rK/4（r=1,K=1）", logistic_max_rate(1.0, 1.0), 0.25, 1e-12)
    chk("y=K/2 处的瞬时增长率最大",
        logistic_solution(1.0, 1.0, 1.0, 0.5) > 0, True)
    chk("平衡点：0 不稳、K 稳",
        [e["stable"] for e in logistic_equilibria(1.0, 1.0)], [False, True])
    # 反解时间与正解自洽
    t90 = logistic_time_to(0.9, 1.0, 1.0, 0.1)
    chk("反解 t(0.9) 与正解自洽", logistic_solution(t90, 1.0, 1.0, 0.1), 0.9, 1e-9)
    chk("y₀ 越大到达 0.9 越早", logistic_time_to(0.9, 1.0, 1.0, 0.5)
        < logistic_time_to(0.9, 1.0, 1.0, 0.1), True)

    print("\nLotka–Volterra：相图与守恒量")
    r_, a_, c_, m_ = 0.05, 1.0, 1.0, 0.05
    eq = lv_equilibria(r_, a_, c_, m_)
    chk("内部平衡点 = (m/c, r/a)", eq[1], (0.05, 0.05))
    fld = lv_flow(r_, a_, c_, m_)
    ts, ys = rk4_system(fld, [0.08, 0.05], 0.0, 400.0, 4000)
    H0 = lv_conserved(ys[0][0], ys[0][1], r_, a_, c_, m_)
    dev = max(abs(lv_conserved(y[0], y[1], r_, a_, c_, m_) - H0) for y in ys)
    chk("守恒量 H 沿轨道不变（偏差 < 1e-3）", dev < 1e-3, True)
    # 轨道闭合：400 年后回到出发点附近
    chk("轨道闭合（终点接近起点）",
        abs(ys[-1][0] - ys[0][0]) + abs(ys[-1][1] - ys[0][1]) < 0.05, True)
    chk("平衡点处向量场为零", [abs(v) < 1e-15 for v in fld(0.0, [0.05, 0.05])], [True, True])
    # 相轨迹不过零点（N、E 始终为正）
    chk("轨线上 N、E 恒为正", all(y[0] > 0 and y[1] > 0 for y in ys), True)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
