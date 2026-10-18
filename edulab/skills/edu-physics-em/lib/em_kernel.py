# -*- coding: utf-8 -*-
"""
em_kernel.py —— 高中物理电磁学确定性计算核心（sympy 精确运算）。

覆盖六块：静电场（库仑定律 / 点电荷场强 / 电场叠加）、电容器、
带电粒子在磁场中的圆周运动、带电粒子在电场中的偏转、闭合电路欧姆定律、
法拉第电磁感应、安培力。

设计哲学与其它技能一致（单一数据源）：答案、坐标、半径、周期、偏转角、读数
全部由本模块精确算出，同一套值既喂给文字，也喂给画板，保证「图、解、答」严格一致。
**不手写数字。**

约定：SI 单位（N / C / T / V / Ω / m / s / kg）；电荷正负号参与方向判断。
坐标：数学坐标，y 轴向上；磁场「×」= 垂直纸面向里，「·」= 垂直纸面向外。

依赖 sympy。自检：python em_kernel.py
"""

import math

import sympy as sp

x = sp.symbols("x")
sqrt = sp.sqrt

K_COULOMB = sp.Float(9.0e9)     # 库仑常量，教材通用近似值（假设类，见 SKILL.md「数值出处」）

G_ACC = sp.Float(9.8)          # 重力加速度（假设类）
E_CHARGE = sp.Float(1.6e-19)   # 元电荷
M_PROTON = sp.Float(1.67e-27)  # 质子质量


def _rad(deg):
    """角度（度）→ 弧度。sympy 没有 radians()，显式换算更清楚。"""
    return sp.simplify(sp.nsimplify(deg) * sp.pi / 180)


def _deg(rad):
    """弧度 → 角度（度）。"""
    return sp.simplify(rad * 180 / sp.pi)


# ---------------------------------------------------------------- 输出格式
def tex(e):
    """sympy 表达式 → LaTeX 片段（不包 $）。"""
    return sp.latex(e)


def f(e):
    """sympy 表达式 → 浮点。"""
    return float(sp.N(e, 20))


def num_str(e):
    """数值的紧凑文本：整数按整数，否则保留 4 位有效数字。"""
    if isinstance(e, sp.Integer):
        return str(int(e))
    v = float(sp.N(e, 20))
    if v == 0:
        return "0"
    if abs(v) >= 1e5 or abs(v) < 1e-4:
        m, ex = sp.mantissa_exp(sp.nsimplify(v))
        return f"{float(m):.4g}e{int(ex)}"
    return f"{v:.4g}"


def sci_tex(e, digits=2):
    """把数量级很大的数写成 a×10ⁿ 的 LaTeX 形式（教学里这才是人话）。"""
    v = float(sp.N(e, 20))
    if v == 0:
        return "0"
    sign = "-" if v < 0 else ""
    a = abs(v)
    exp = 0
    while a >= 10:
        a /= 10.0
        exp += 1
    while a < 1:
        a *= 10.0
        exp -= 1
    if exp == 0:
        return f"{sign}{a:.{digits}g}"
    return f"{sign}{a:.{digits}g}\\times 10^{{{exp}}}"


# ---------------------------------------------------------------- 静电场
def coulomb(q1, q2, r):
    """库仑定律：两个点电荷之间的静电力大小与方向。

    F = k|q1 q2| / r²。q1 q2 同号 → 斥力，异号 → 引力。
    """
    q1, q2, r = sp.nsimplify(q1), sp.nsimplify(q2), sp.nsimplify(r)
    if r <= 0:
        raise ValueError("距离必须为正（点电荷模型在 r=0 处失效）")
    F = sp.simplify(K_COULOMB * abs(q1 * q2) / r ** 2)
    kind = "斥力" if (q1 > 0) == (q2 > 0) else "引力"
    return {"F": F, "kind": kind, "r": r, "q1": q1, "q2": q2,
            "sign": 1 if kind == "斥力" else -1}


def field_at(q, r, k=K_COULOMB):
    """单个点电荷在距离 r 处产生的场强 E = k|q|/r²，方向由电荷符号决定。"""
    q, r = sp.nsimplify(q), sp.nsimplify(r)
    if r <= 0:
        raise ValueError("场点不能与源电荷重合")
    E = sp.simplify(k * abs(q) / r ** 2)
    return {"E": E, "q": q, "r": r, "outward": bool(q > 0)}


def field_vector_at(charges, px, py, k=K_COULOMB):
    """点电荷组在 (px, py) 处的合场强（矢量叠加，含符号）。

    charges: [(qx, qy, q), ...]，q 带符号（正 = 正电荷）。
    返回分量 Ex、Ey、模长，以及每个电荷的单独贡献（便于画分量箭头）。
    """
    Ex = sp.Float(0)
    Ey = sp.Float(0)
    parts = []
    for qx, qy, q in charges:
        qx, qy, q = sp.nsimplify(qx), sp.nsimplify(qy), sp.nsimplify(q)
        dx = sp.simplify(sp.nsimplify(px) - qx)
        dy = sp.simplify(sp.nsimplify(py) - qy)
        r2 = sp.simplify(dx ** 2 + dy ** 2)
        if r2 == 0:
            raise ValueError("场点与某个源电荷重合")
        r = sqrt(r2)
        m = sp.simplify(k * q / r ** 2)          # 带符号的模长（q 负 → 指向源）
        cx = sp.simplify(m * dx / r)
        cy = sp.simplify(m * dy / r)
        Ex += cx
        Ey += cy
        parts.append({"qx": qx, "qy": qy, "q": q, "Ex": sp.simplify(cx), "Ey": sp.simplify(cy),
                      "mag": sp.simplify(abs(m)), "r": sp.simplify(r)})
    Ex, Ey = sp.simplify(Ex), sp.simplify(Ey)
    return {"Ex": Ex, "Ey": Ey, "E": sp.simplify(sqrt(Ex ** 2 + Ey ** 2)),
            "parts": parts, "px": sp.nsimplify(px), "py": sp.nsimplify(py)}


# ---------------------------------------------------------------- 电容器
def capacitor(eps_r, S, d, V):
    """平行板电容器：C = ε₀εᵣS/d，Q = CU，E = U/d，储能 W = ½CV²。

    S 单位 m²，d 单位 m，V 单位 V。ε₀ 取 8.85e-12 F/m（教材值，假设类）。
    """
    eps_r, S, d, V = map(sp.nsimplify, (eps_r, S, d, V))
    if d <= 0 or S <= 0:
        raise ValueError("S 与 d 必须为正")
    EPS0 = sp.Float(8.85e-12)
    C = sp.simplify(EPS0 * eps_r * S / d)
    Q = sp.simplify(C * V)
    E = sp.simplify(V / d)
    W = sp.simplify(sp.Rational(1, 2) * C * V ** 2)
    return {"C": C, "Q": Q, "E": E, "W": W, "d": d, "S": S, "V": V, "eps_r": eps_r}


# ---------------------------------------------------------------- 带电粒子在磁场中
def magnetic_circle(m, v, B, q):
    """带电粒子垂直进入匀强磁场：洛伦兹力提供向心力，做匀速圆周运动。

    qvB = mv²/r → r = mv/(qB)；T = 2πm/(qB)，与速率无关。
    q<0 时旋转方向相反（可用 q 的符号判定）。
    """
    m, v, B, q = map(sp.nsimplify, (m, v, B, q))
    if B == 0 or m == 0:
        raise ValueError("B 与 m 都必须非零")
    r = sp.simplify(abs(m * v / (abs(q) * abs(B))))
    T = sp.simplify(2 * sp.pi * m / (abs(q) * abs(B)))
    return {"r": r, "T": T, "f": sp.simplify(1 / T), "omega": sp.simplify(2 * sp.pi / T),
            "v": v, "B": B, "q": q, "m": m,
            # B 垂直纸面向里（⊗）时：正电荷逆时针、负电荷顺时针。
            # 判据：F = qv×B。取 v = +x̂、B = −ẑ，得 v×B = +ŷ，即力向上，
            # 粒子在原点向右运动时向上偏 → 逆时针。
            "ccw": bool(q > 0),
            "period_expr": r"2\pi m/(qB)"}


def magnetic_period(m, B, q):
    """回旋周期 T = 2πm/(|q|B) —— 回旋加速器的原理：周期与速率无关。"""
    return magnetic_circle(m, 1, B, q)["T"]


# ---------------------------------------------------------------- 带电粒子在电场中偏转
def electric_deflect(E, q, m, v0, L):
    """带电粒子以 v₀ 垂直进入匀强电场（类平抛）：L 长极板内的偏转。

    a = qE/m；t = L/v₀；y = ½at²；tanθ = vy/v₀ = at/v₀。
    返回偏转量、末速度偏角、动能增量。
    """
    E, q, m, v0, L = map(sp.nsimplify, (E, q, m, v0, L))
    if v0 <= 0 or L <= 0:
        raise ValueError("v₀ 与 L 必须为正")
    a = sp.simplify(abs(q) * E / m)
    t = sp.simplify(L / v0)
    y = sp.simplify(sp.Rational(1, 2) * a * t ** 2)
    vy = sp.simplify(a * t)
    tan = sp.simplify(vy / v0)
    vt = sp.simplify(sqrt(v0 ** 2 + vy ** 2))
    return {"a": a, "t": t, "y": y, "vy": vy, "tan": tan,
            "angle": _deg(sp.atan(tan)), "vt": vt,
            "Ek": sp.simplify(sp.Rational(1, 2) * m * (vt ** 2 - v0 ** 2)),
            "E": E, "q": q, "m": m, "v0": v0, "L": L}


def deflect_angle_from_speed(v0, vy):
    """由速度分量求偏角（度）。"""
    return _deg(sp.atan(sp.nsimplify(vy) / sp.nsimplify(v0)))


# ---------------------------------------------------------------- 闭合电路欧姆定律
def circuit(E, r, R):
    """闭合电路欧姆定律：I = E/(R+r)，U = IR = E - Ir，效率 η = R/(R+r)。

    同时给出输出功率 P 出 = I²R、总功率 P 总 = EI，以及「外阻等于内阻时输出功率最大」。
    """
    E, r, R = map(sp.nsimplify, (E, r, R))
    if r < 0 or R < 0:
        raise ValueError("电阻不能为负")
    if R + r == 0:
        raise ValueError("R+r=0 时短路，欧姆定律不适用")
    I = sp.simplify(E / (R + r))
    U = sp.simplify(I * R)
    Pout = sp.simplify(I ** 2 * R)
    Ptot = sp.simplify(E * I)
    return {"I": I, "U": U, "Pout": Pout, "Ptot": Ptot,
            "eta": sp.simplify(Pout / Ptot),
            "Ir": sp.simplify(I * r),
            "E": E, "r": r, "R": R,
            "max_at": r, "short": E / r if r != 0 else None}


def max_output_power(R0):
    """输出功率随外阻变化的最大值位置：R = r。"""
    return sp.simplify(R0)


# ---------------------------------------------------------------- 法拉第电磁感应
def faraday(N, dPhi, dt, B0=0, B1=0, S=0, theta_deg=0):
    """法拉第电磁感应定律：E = N·|ΔΦ/Δt|，Φ = BS·cosθ。

    ΔΦ 可以直接给（单位 Wb），也可以给 B 的变化量与面积。
    楞次定律的方向由 dΦ/dt 的符号与线圈法线方向共同决定 —— 这里给出定性结论。
    """
    N, dt = sp.nsimplify(N), sp.nsimplify(dt)
    if dt == 0:
        raise ValueError("Δt 不能为零")
    if dPhi is None:
        th = _rad(theta_deg)
        dPhi = sp.simplify((sp.nsimplify(B1) - sp.nsimplify(B0)) * sp.nsimplify(S) * sp.cos(th))
    else:
        dPhi = sp.nsimplify(dPhi)
    emf = sp.simplify(abs(N * dPhi / dt))
    rising = dPhi > 0
    return {"emf": emf, "dPhi": sp.simplify(dPhi), "dt": dt, "N": N,
            "rising": bool(rising),
            "lens": "磁通量增大，感应电流的磁场要<b>阻碍</b>它增大" if rising
                    else "磁通量减小，感应电流的磁场要<b>阻碍</b>它减小",
            "Phi0": sp.simplify(sp.nsimplify(B0) * sp.nsimplify(S)),
            "Phi1": sp.simplify(sp.nsimplify(B1) * sp.nsimplify(S))}


def flux(B, S, theta_deg=90):
    """Φ = B·S·cosθ，θ 是 B 与线圈法线的夹角（θ=90° 表示平行于线圈平面 → Φ=0）。"""
    B, S = sp.nsimplify(B), sp.nsimplify(S)
    th = _rad(theta_deg)
    return {"Phi": sp.simplify(B * S * sp.cos(th)), "B": B, "S": S, "theta": sp.nsimplify(theta_deg)}


# ---------------------------------------------------------------- 安培力
def ampere_force(B, I, L, theta_deg=90):
    """通电直导线在匀强磁场中受力：F = BIL·sinθ，θ 是 B 与电流的夹角。

    方向由左手定则确定；θ=0 或 180° 时 F=0（平行不受力）。
    """
    B, I, L = map(sp.nsimplify, (B, I, L))
    th = _rad(theta_deg)
    F = sp.simplify(abs(B * I * L * sp.sin(th)))
    return {"F": F, "B": B, "I": I, "L": L, "theta": sp.nsimplify(theta_deg),
            "perp": bool(abs(float(sp.sin(th))) > 1e-12)}


# ---------------------------------------------------------------- 自检
def _selftest():
    cases = []

    def ok(cond, name):
        cases.append((bool(cond), name))

    # 库仑定律：k·|q1 q2|/r²
    C1 = coulomb(1e-6, -1e-6, 0.2)
    ok(abs(f(C1["F"]) - 0.225) < 1e-9, "库仑力 0.225 N")
    ok(C1["kind"] == "引力", "异号电荷是引力")
    C2 = coulomb(2e-6, 2e-6, 0.1)
    ok(abs(f(C2["F"]) - 3.6) < 1e-9, "库仑力 3.6 N")
    ok(C2["kind"] == "斥力", "同号电荷是斥力")

    # 点电荷场强 E = kq/r²
    E1 = field_at(1e-6, 0.3)
    ok(abs(f(E1["E"]) - 1.0e5) < 1e3, "场强 1e5 N/C")

    # 场强叠加：两个等量同号电荷，中点场强为 0（对称抵消）
    S1 = field_vector_at([(0, 0, 1e-6), (2, 0, 1e-6)], 1, 0)
    ok(abs(f(S1["E"])) < 1e-6, "等量同号电荷中点场强为 0")
    # 等量异号：中点场强是两者之和（方向相同）
    S2 = field_vector_at([(0, 0, 1e-6), (2, 0, -1e-6)], 1, 0)
    ok(abs(f(S2["E"]) - 2 * f(field_at(1e-6, 1)["E"])) < 1e3, "等量异号中点场强是两倍")
    # 等量异号：中垂线上垂直于连线的分量抵消，沿连线的分量叠加
    S3 = field_vector_at([(0, 0, 1e-6), (2, 0, -1e-6)], 1, 1)
    ok(abs(f(S3["Ey"])) < 1e-6, "异号电荷中垂线上垂直分量抵消")
    ok(f(S3["Ex"]) > 0, "中垂线上合场强沿连线，由正电荷指向负电荷")

    # 电容器
    CAP = capacitor(1, 200e-4, 2e-3, 12)      # S=200 cm²=0.02 m²，d=2 mm
    ok(abs(f(CAP["C"]) - 8.85e-11) < 1e-15, "电容 C = ε₀S/d = 88.5 pF")
    ok(abs(f(CAP["E"]) - 6000) < 1e-6, "板间场强 E = U/d = 6000 V/m")
    ok(abs(f(CAP["Q"]) - f(CAP["C"]) * 12) < 1e-20, "Q = CU")
    ok(abs(f(CAP["W"]) - 0.5 * f(CAP["C"]) * 144) < 1e-18, "储能 W = ½CV²")

    # 带电粒子在磁场中
    B1 = magnetic_circle(M_PROTON, 1e6, 0.5, E_CHARGE)
    ok(abs(f(B1["r"]) - 0.0209) < 1e-4, "质子半径约 2.1 cm")
    ok(f(B1["r"]) > 0, "半径为正")
    ok(abs(f(B1["T"]) - 1.31e-7) < 1e-9, "质子回旋周期约 1.3e-7 s")
    ok(B1["ccw"] is True, "正电荷 + B 向里 → 逆时针")
    ok(magnetic_circle(M_PROTON, 1e6, 0.5, -E_CHARGE)["ccw"] is False, "负电荷转向相反（顺时针）")
    # 方向守门：F = qv×B。取 v=+x̂、B=−ẑ（向里），则 v×B = +ŷ → 力向上 → 逆时针
    _v, _B = sp.Matrix([1, 0, 0]), sp.Matrix([0, 0, -1])
    _F = _v.cross(_B)
    ok(_F == sp.Matrix([0, 1, 0]), "v×B 的方向判据（正电荷向上偏 = 逆时针）")
    # 周期与速率无关（回旋加速器的原理）
    ok(abs(f(magnetic_circle(M_PROTON, 2e6, 0.5, E_CHARGE)["T"])
           - f(magnetic_circle(M_PROTON, 1e6, 0.5, E_CHARGE)["T"])) < 1e-15,
       "周期与速率无关")

    # 电场偏转（类平抛）
    D1 = electric_deflect(1e4, E_CHARGE, M_PROTON, 1e6, 0.1)
    ok(f(D1["y"]) > 0, "偏转量为正")
    ok(abs(f(D1["a"]) - 9.58e11) < 1e9, "加速度 a = qE/m")
    ok(abs(f(D1["t"]) - 1e-7) < 1e-15, "穿越时间 t = L/v₀")
    ok(abs(f(D1["angle"])) < 90, "偏角在合理范围")
    ok(abs(f(D1["Ek"])) > 0, "动能有增量")

    # 闭合电路欧姆定律
    CI = circuit(12, 1, 5)
    ok(abs(f(CI["I"]) - 2) < 1e-12, "I = E/(R+r) = 2 A")
    ok(abs(f(CI["U"]) - 10) < 1e-12, "路端电压 U = 10 V")
    ok(abs(f(CI["Ir"]) - 2) < 1e-12, "内电压 Ir = 2 V")
    ok(abs(f(CI["eta"]) - 5 / 6) < 1e-12, "效率 η = R/(R+r)")
    ok(abs(f(CI["U"]) + f(CI["Ir"]) - 12) < 1e-12, "U + Ir = E（电压守恒）")
    # 输出功率在 R = r 处最大
    vals = [f(circuit(12, 1, R)["Pout"]) for R in (0.5, 1, 2, 5)]
    ok(max(vals) == vals[1], "外阻 = 内阻时输出功率最大")

    # 法拉第电磁感应
    FA = faraday(100, 0.02, 0.1)
    ok(abs(f(FA["emf"]) - 20) < 1e-12, "E = NΔΦ/Δt = 20 V")
    ok(FA["rising"] is True, "磁通量增大判定")
    ok("阻碍" in FA["lens"], "楞次定律文案含「阻碍」")
    # S = 0.01 m² = 100 cm²，ΔB = 0.2 T → ΔΦ = 2×10⁻³ Wb，Δt = 0.05 s
    FA2 = faraday(50, dPhi=None, dt=0.05, B0=0.2, B1=0.4, S=0.01)
    ok(abs(f(FA2["emf"]) - 2.0) < 1e-12, "由 ΔB·S 算出的感应电动势 2 V")
    ok(abs(f(FA2["dPhi"]) - 2e-3) < 1e-15, "ΔΦ = ΔB·S = 2×10⁻³ Wb")
    ok(faraday(50, dPhi=-0.002, dt=0.05)["rising"] is False, "ΔΦ 为负 → 磁通量减小")
    FL = flux(0.5, 0.02, 60)
    ok(abs(f(FL["Phi"]) - 0.5 * 0.02 * math.cos(math.radians(60))) < 1e-12, "Φ = BS·cosθ")

    # 安培力
    AF = ampere_force(0.4, 3, 0.5, 90)
    ok(abs(f(AF["F"]) - 0.6) < 1e-12, "F = BIL = 0.6 N")
    ok(ampere_force(0.4, 3, 0.5, 0)["F"] == 0, "B ∥ I 时不受力")
    ok(ampere_force(0.4, 3, 0.5, 30)["perp"] is True, "θ=30° 仍受力")

    bad = [c for c in cases if not c[0]]
    for good, name in cases:
        print(f"  {'✓' if good else '✗'} {name}")
    print(f"\n{'电磁学内核自检通过 ✓' if not bad else f'{len(bad)} 项失败'}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
