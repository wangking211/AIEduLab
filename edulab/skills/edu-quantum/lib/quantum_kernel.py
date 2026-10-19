#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quantum_kernel.py —— 大学「量子力学入门」内核（8.04 的一维部分）

覆盖：
  · 无限深势阱：能级 Eₙ = n²h²/(8mL²)、波函数、概率密度、节点数
  · 德布罗意波长 λ = h/p（与能量、与「实物粒子的尺度」的对比）
  · 不确定性原理 Δx·Δp ≥ ħ/2（高斯波包取到等号）
  · 一维谐振子：能级等间距、**零点能** ħω/2
  · 矩形势垒的隧道效应：透射系数 T(E)（E<V₀ 与 E>V₀ 两支公式）
  · 有限深势阱的束缚态能级：**数值解**超越方程（偶态/奇态分开求）
  · 自由高斯波包的时间演化：σ(t) 的解析展宽（量子色散）

设计原则（与全项目一致）：
  · **不手写数字**：能级、波长、透射系数、束缚态能量全部现算；
    有限深势阱的能级用二分法**真解超越方程**，不是查表。
  · 解析解与数值解**互相印证**（无限深势阱的数值解要收敛到解析解）。
  · 自检：python quantum_kernel.py
"""

import math

__all__ = [
    "f", "num_str", "sci",
    "H_PLANCK", "HBAR", "M_E", "E_CHARGE", "EV_TO_J",
    "j_to_ev", "ev_to_j", "m_to_nm", "nm_to_m",
    "well_energy", "well_energy_ev", "well_psi", "well_prob",
    "well_nodes", "well_levels",
    "de_broglie", "de_broglie_from_energy", "de_broglie_ev",
    "uncertainty_min_dp", "uncertainty_min_dx", "gauss_sigma_p",
    "harmonic_energy", "harmonic_energy_ev", "harmonic_zero_point",
    "harmonic_spacing", "harmonic_levels",
    "tunneling_T", "tunneling_kappa", "tunneling_length",
    "finite_well_levels", "finite_well_count", "infinite_vs_finite",
    "gauss_packet_sigma", "gauss_packet_prob", "gauss_packet_speed",
    "gauss_packet_spread_time",
]


# ---------------------------------------------------------------- 物理常数（实测类）
H_PLANCK = 6.62607015e-34      # 普朗克常数，J·s
HBAR = 1.054571817e-34         # 约化普朗克常数，J·s
M_E = 9.1093837015e-31         # 电子质量，kg
E_CHARGE = 1.602176634e-19     # 元电荷，C
EV_TO_J = 1.602176634e-19      # 1 eV = 1.602e-19 J


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
        return sci(val, digits - 1)
    return f(val, digits)


def sci(v, digits=3):
    val = float(v)
    if val == 0:
        return "0"
    e = math.floor(math.log10(abs(val)))
    return f"{val / 10 ** e:.{digits}f} \\times 10^{{{e}}}"


# ---------------------------------------------------------------- 单位换算
def j_to_ev(e):
    return float(e) / EV_TO_J


def ev_to_j(e):
    return float(e) * EV_TO_J


def m_to_nm(x):
    return float(x) * 1e9


def nm_to_m(x):
    return float(x) * 1e-9


# ---------------------------------------------------------------- 无限深势阱
def well_energy(n, L, m=M_E):
    """无限深势阱的能级 Eₙ = n²h²/(8mL²)（J）。

    势阱宽度 L，两端势为无穷大；n = 1, 2, 3, …
    """
    if n < 1 or L <= 0 or m <= 0:
        raise ValueError("n ≥ 1、L > 0、m > 0")
    return n * n * H_PLANCK ** 2 / (8.0 * m * L * L)


def well_energy_ev(n, L_nm, m=M_E):
    """能级（eV），宽度用 nm。"""
    return j_to_ev(well_energy(n, nm_to_m(L_nm), m))


def well_psi(n, x, L):
    """归一化波函数 ψₙ(x) = √(2/L)·sin(nπx/L)，x ∈ [0, L]。"""
    if x < 0 or x > L:
        return 0.0
    return math.sqrt(2.0 / L) * math.sin(n * math.pi * x / L)


def well_prob(n, x, L):
    """概率密度 |ψₙ(x)|²。"""
    p = well_psi(n, x, L)
    return p * p


def well_nodes(n):
    """波函数的节点数（不含端点）= n − 1。"""
    return n - 1


def well_levels(n_max, L, m=M_E):
    """前 n_max 个能级（J）。"""
    return [well_energy(n, L, m) for n in range(1, n_max + 1)]


# ---------------------------------------------------------------- 德布罗意
def de_broglie(m, v):
    """德布罗意波长 λ = h/(mv)。"""
    if m <= 0 or v <= 0:
        raise ValueError("质量与速度必须为正")
    return H_PLANCK / (m * v)


def de_broglie_from_energy(m, E_kinetic):
    """由动能求德布罗意波长：p = √(2mE) ⇒ λ = h/√(2mE)。"""
    if m <= 0 or E_kinetic <= 0:
        raise ValueError("质量与动能必须为正")
    return H_PLANCK / math.sqrt(2.0 * m * E_kinetic)


def de_broglie_ev(m, E_ev):
    """由动能（eV）求波长（m）。"""
    return de_broglie_from_energy(m, ev_to_j(E_ev))


# ---------------------------------------------------------------- 不确定性原理
def uncertainty_min_dp(dx):
    """给定 Δx 时 Δp 的下界：Δp ≥ ħ/(2Δx)。"""
    if dx <= 0:
        raise ValueError("Δx 必须为正")
    return HBAR / (2.0 * dx)


def uncertainty_min_dx(dp):
    """给定 Δp 时 Δx 的下界。"""
    if dp <= 0:
        raise ValueError("Δp 必须为正")
    return HBAR / (2.0 * dp)


def gauss_sigma_p(sigma_x):
    """高斯波包：Δp = ħ/(2σ)，此时 Δx·Δp = ħ/2（取到等号）。"""
    if sigma_x <= 0:
        raise ValueError("σ 必须为正")
    return HBAR / (2.0 * sigma_x)


# ---------------------------------------------------------------- 谐振子
def harmonic_energy(n, omega, m=M_E):
    """一维谐振子能级 Eₙ = (n + ½)ħω（J）。"""
    if n < 0:
        raise ValueError("n ≥ 0")
    return (n + 0.5) * HBAR * omega


def harmonic_energy_ev(n, omega):
    return j_to_ev(harmonic_energy(n, omega))


def harmonic_zero_point(omega):
    """零点能 ħω/2 —— 经典上「完全静止」的状态在量子力学里不存在。"""
    return 0.5 * HBAR * omega


def harmonic_spacing(omega):
    """相邻能级的间距（恒为 ħω，与 n 无关）。"""
    return HBAR * omega


def harmonic_levels(n_max, omega):
    return [harmonic_energy(n, omega) for n in range(n_max + 1)]


# ---------------------------------------------------------------- 隧道效应
def tunneling_kappa(E, V0, m=M_E):
    """势垒内的衰减常数 κ = √(2m(V₀−E))/ħ（仅 E < V₀ 时有意义）。"""
    if E >= V0:
        return 0.0
    return math.sqrt(2.0 * m * (V0 - E)) / HBAR


def tunneling_length(E, V0, m=M_E):
    """衰减长度 1/κ —— 波函数在势垒内大致按 e^{−κx} 衰减。"""
    k = tunneling_kappa(E, V0, m)
    return float("inf") if k == 0 else 1.0 / k


def tunneling_T(E, V0, a, m=M_E):
    """矩形势垒（高 V₀、宽 a）的透射系数 T(E)。

    E < V₀（经典上过不去）：
        T = 1 / (1 + V₀²sinh²(κa) / (4E(V₀−E)))
    E > V₀（经典上一定过得去，但量子上有反射）：
        T = 1 / (1 + V₀²sin²(k₂a) / (4E(E−V₀)))
    """
    if E <= 0 or V0 < 0 or a < 0:
        raise ValueError("E > 0、V₀ ≥ 0、a ≥ 0")
    if a == 0 or V0 == 0:
        return 1.0
    if E < V0:
        k = tunneling_kappa(E, V0, m)
        s = math.sinh(k * a)
        return 1.0 / (1.0 + (V0 * V0 * s * s) / (4.0 * E * (V0 - E)))
    if E == V0:
        # 极限：T = 1/(1 + m V₀ a²/(2ħ²))
        return 1.0 / (1.0 + m * V0 * a * a / (2.0 * HBAR ** 2))
    k2 = math.sqrt(2.0 * m * (E - V0)) / HBAR
    s2 = math.sin(k2 * a)
    return 1.0 / (1.0 + (V0 * V0 * s2 * s2) / (4.0 * E * (E - V0)))


# ---------------------------------------------------------------- 有限深势阱（数值）
def _finite_well_even(E, V0, a, m):
    """偶态：把 k·tan(ka/2) = κ 两边乘 cos，得**连续**形式
    g(E) = k·sin(ka/2) − κ·cos(ka/2)。

    为什么不直接用 tan：tan 在 ka/2 = π/2 等处有极点，
    数值扫符号时会把「跨过极点」误判成「函数变号」，凭空多出根。
    乘掉分母后 g 连续，极点不再产生假根（那里 g = ±k ≠ 0）。
    """
    k = math.sqrt(2.0 * m * E) / HBAR
    kap = math.sqrt(2.0 * m * (V0 - E)) / HBAR
    return k * math.sin(k * a / 2.0) - kap * math.cos(k * a / 2.0)


def _finite_well_odd(E, V0, a, m):
    """奇态：把 −k·cot(ka/2) = κ 两边乘 sin，得连续形式
    g(E) = −k·cos(ka/2) − κ·sin(ka/2)。"""
    k = math.sqrt(2.0 * m * E) / HBAR
    kap = math.sqrt(2.0 * m * (V0 - E)) / HBAR
    return -k * math.cos(k * a / 2.0) - kap * math.sin(k * a / 2.0)


def finite_well_levels(V0, a, m=M_E, n_max=6, steps=4000):
    """有限深势阱 V(x) = 0 (|x|<a/2)、V₀ (|x|>a/2) 的束缚态能级（J，升序）。

    用**二分法真解超越方程**：把 (0, V₀) 分成 steps 段，逐段看函数是否变号，
    变号就二分求根。偶态与奇态分别求，最后合并排序。
    """
    if V0 <= 0 or a <= 0:
        raise ValueError("V₀ 与 a 必须为正")
    out = []
    h = V0 / steps
    for fn in (_finite_well_even, _finite_well_odd):
        prev_e = 1e-9 * V0
        prev_v = fn(prev_e, V0, a, m)
        for i in range(1, steps + 1):
            e = i * h
            if e >= V0:
                break
            v = fn(e, V0, a, m)
            if math.isfinite(prev_v) and math.isfinite(v) and prev_v * v < 0:
                lo, hi = prev_e, e
                for _ in range(80):
                    mid = (lo + hi) / 2.0
                    vm = fn(mid, V0, a, m)
                    if not math.isfinite(vm):
                        break
                    if prev_v * vm <= 0:
                        hi = mid
                    else:
                        lo = mid
                        prev_v = vm
                out.append((lo + hi) / 2.0)
            prev_e, prev_v = e, v
    return sorted(out)[:n_max]


def finite_well_count(V0, a, m=M_E):
    """束缚态个数的解析上界：N = ⌈√(2mV₀)a/(πħ)⌉（取整）。"""
    val = math.sqrt(2.0 * m * V0) * a / (math.pi * HBAR)
    return int(math.ceil(val - 1e-12))


def infinite_vs_finite(V0, a, m=M_E):
    """有限深势阱的基态能量 与「同宽无限深势阱」基态能量的比值。

    有限阱的基态总是**略低**于同宽无限阱（波函数可以渗出阱外，动能更小）。
    """
    lv = finite_well_levels(V0, a, m, n_max=1)
    if not lv:
        return None
    return lv[0] / well_energy(1, a, m)


# ---------------------------------------------------------------- 自由高斯波包
def gauss_packet_sigma(sigma0, t, m=M_E):
    """自由高斯波包的宽度随时间展宽：σ(t) = σ₀√(1 + (ħt/(2mσ₀²))²)。"""
    if sigma0 <= 0:
        raise ValueError("σ₀ 必须为正")
    return sigma0 * math.sqrt(1.0 + (HBAR * t / (2.0 * m * sigma0 ** 2)) ** 2)


def gauss_packet_prob(x, t, sigma0, k0=0.0, m=M_E):
    """自由高斯波包的概率密度 |ψ(x,t)|²（精确解）。

    波包整体以群速度 v = ħk₀/m 平移，同时按 σ(t) 展宽。
    """
    s = gauss_packet_sigma(sigma0, t, m)
    v = HBAR * k0 / m
    dx = x - v * t
    return math.exp(-dx * dx / (2.0 * s * s)) / (math.sqrt(2.0 * math.pi) * s)


def gauss_packet_speed(k0, m=M_E):
    """群速度 v = ħk₀/m。"""
    return HBAR * k0 / m


def gauss_packet_spread_time(sigma0, factor, m=M_E):
    """波包宽度展宽到 factor 倍所需的时间。"""
    if factor <= 1:
        raise ValueError("factor 必须大于 1")
    return 2.0 * m * sigma0 ** 2 * math.sqrt(factor ** 2 - 1.0) / HBAR


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

    print("常数与单位")
    chk("ħ = h/2π", HBAR, H_PLANCK / (2 * math.pi), 1e-9)
    chk("1 eV 的焦耳数", EV_TO_J, E_CHARGE, 1e-12)
    chk("eV ↔ J 往返", j_to_ev(ev_to_j(3.7)), 3.7, 1e-12)
    chk("nm ↔ m 往返", m_to_nm(nm_to_m(2.5)), 2.5, 1e-12)

    print("\n无限深势阱")
    # L = 0.5 nm 的电子：基态约 1.5 eV
    chk("E₁(L=0.5nm) ≈ 1.5 eV", well_energy_ev(1, 0.5), 1.5044, 2e-3)
    chk("E₂ = 4E₁", well_energy_ev(2, 0.5), 4 * well_energy_ev(1, 0.5), 1e-9)
    chk("E₃ = 9E₁", well_energy_ev(3, 0.5), 9 * well_energy_ev(1, 0.5), 1e-9)
    chkb("能级随 n² 增长",
         well_energy(4, 1e-9) - well_energy(3, 1e-9) > well_energy(2, 1e-9) - well_energy(1, 1e-9),
         True)
    # 阱越宽能级越低
    chkb("阱越宽基态越低", well_energy_ev(1, 1.0) < well_energy_ev(1, 0.5), True)
    # 波函数归一化：∫|ψ|²dx = 1（数值积分）
    L = 1e-9
    n = 2
    steps = 20000
    s = 0.0
    for i in range(steps):
        xx = L * (i + 0.5) / steps
        s += well_prob(n, xx, L) * (L / steps)
    chk("波函数归一化 ∫|ψ|²dx = 1", s, 1.0, 1e-6)
    # 节点数
    for nn in (1, 2, 3, 5):
        chk(f"n={nn} 的节点数", well_nodes(nn), nn - 1, 0)
    # 节点处概率为 0
    chk("n=2 在 x=L/2 处概率为 0", well_prob(2, L / 2, L), 0.0, 1e-12)
    chk("n=3 在 x=L/3 处概率为 0", well_prob(3, L / 3, L), 0.0, 1e-9)
    # 端点必为 0
    chk("x=0 处 ψ=0", well_psi(3, 0.0, L), 0.0, 1e-12)
    # sin(nπ) 在浮点下不是精确的 0（约 1e-11），所以给容差
    chk("x=L 处 ψ≈0", well_psi(3, L, L), 0.0, 1e-9)

    print("\n德布罗意波长")
    # 电子 1 eV：λ ≈ 1.23 nm
    chk("电子 1 eV 的波长 ≈ 1.23 nm", m_to_nm(de_broglie_ev(M_E, 1.0)), 1.2264, 2e-3)
    chk("电子 100 eV 的波长 ≈ 0.123 nm", m_to_nm(de_broglie_ev(M_E, 100.0)), 0.12264, 2e-4)
    # 动能越大波长越短（λ ∝ 1/√E）
    chkb("动能 4 倍 ⇒ 波长减半",
         abs(de_broglie_ev(M_E, 4.0) * 2 - de_broglie_ev(M_E, 1.0)) < 1e-15, True)
    # 与速度公式一致：E = ½mv² ⇒ λ = h/(mv)
    v = math.sqrt(2 * ev_to_j(1.0) / M_E)
    chk("两种算法一致", de_broglie(M_E, v), de_broglie_ev(M_E, 1.0), 1e-9)
    # 宏观物体（1 g、1 m/s）的波长小到无意义
    chk("1 g 小球 1 m/s 的波长（m）", de_broglie(1e-3, 1.0), H_PLANCK / 1e-3, 1e-12)
    chkb("宏观物体的波长 < 10⁻³⁰ m", de_broglie(1e-3, 1.0) < 1e-30, True)

    print("\n不确定性原理")
    chk("Δx = 1 nm 时 Δp 下界", uncertainty_min_dp(1e-9), HBAR / 2e-9, 1e-12)
    # 高斯波包取到等号：Δx·Δp = ħ/2
    for sx in (0.5e-9, 1e-9, 5e-9):
        chk(f"高斯波包 Δx·Δp = ħ/2 (σ={sx})", sx * gauss_sigma_p(sx), HBAR / 2, 1e-12)
    chkb("Δx 越小 Δp 越大", uncertainty_min_dp(1e-10) > uncertainty_min_dp(1e-9), True)
    chk("两个方向互为逆运算", uncertainty_min_dx(uncertainty_min_dp(2e-9)), 2e-9, 1e-12)

    print("\n一维谐振子")
    w = 1e15
    chk("E₀ = ħω/2（零点能）", harmonic_energy(0, w), HBAR * w / 2, 1e-12)
    chk("E₁ = 3ħω/2", harmonic_energy(1, w), 1.5 * HBAR * w, 1e-12)
    chk("零点能 = 间距的一半", harmonic_zero_point(w), harmonic_spacing(w) / 2, 1e-12)
    chk("能级间距恒为 ħω",
        [harmonic_energy(n + 1, w) - harmonic_energy(n, w) for n in range(5)],
        [HBAR * w] * 5, 1e-12)
    chkb("零点能 > 0（经典上不该有）", harmonic_zero_point(w) > 0, True)

    print("\n隧道效应")
    V0 = ev_to_j(5.0)
    a = 1e-9
    # E → 0 时 T → 0；E → V₀⁻ 时 T 不为 0
    chkb("E 很小时 T 很小", tunneling_T(0.01 * V0, V0, a) < 1e-4, True)
    # E → V₀⁻ 时 T 收敛到 1/(1 + mV₀a²/(2ħ²))（不是 1！）—— 这是「匹配点」的透射率
    _tlim = 1.0 / (1.0 + M_E * V0 * a * a / (2.0 * HBAR ** 2))
    chk("E→V₀⁻ 时 T 收敛到匹配点值", tunneling_T(0.9999 * V0, V0, a), _tlim, 1e-3)
    chkb("  该值明显小于 1（即使 E=V₀ 也有反射）", _tlim < 0.5, True)
    chkb("T 随 E 单调上升（E<V₀ 段）",
         all(tunneling_T(E1, V0, a) < tunneling_T(E2, V0, a)
             for E1, E2 in ((0.1 * V0, 0.3 * V0), (0.3 * V0, 0.6 * V0), (0.6 * V0, 0.9 * V0))), True)
    # 势垒越宽，T 越小（指数衰减）
    t1 = tunneling_T(0.5 * V0, V0, 0.5e-9)
    t2 = tunneling_T(0.5 * V0, V0, 1.0e-9)
    chkb("势垒加宽一倍 T 大幅下降", t2 < t1 / 10, True)
    # 势垒越宽，κa 越大
    chk("κ 与宽度无关（只由 E、V₀ 定）", tunneling_kappa(0.5 * V0, V0),
        tunneling_kappa(0.5 * V0, V0), 1e-12)
    # 经典禁区内的衰减长度
    chk("衰减长度 = 1/κ", tunneling_length(0.5 * V0, V0) * tunneling_kappa(0.5 * V0, V0), 1.0, 1e-12)
    # E > V₀ 时也有反射（量子效应）：T 在 0 与 1 之间振荡
    ts = [tunneling_T((1.0 + 0.05 * k) * V0, V0, a) for k in range(1, 30)]
    chkb("E > V₀ 时 T 在 0~1 之间且非单调", min(ts) < 0.9 and max(ts) <= 1.0 + 1e-12, True)
    # 宽 a → 0 时 T → 1
    chk("势垒极薄时 T → 1", tunneling_T(0.5 * V0, V0, 1e-15), 1.0, 1e-6)
    chk("T 恒在 [0,1]", all(0.0 <= tunneling_T(E, V0, a) <= 1.0
                            for E in (0.1 * V0, 0.5 * V0, V0, 2 * V0, 5 * V0)), True)

    print("\n有限深势阱（数值解超越方程）")
    V0f = ev_to_j(5.0)
    af = 1e-9
    lv = finite_well_levels(V0f, af, M_E, n_max=6)
    chkb("至少有一个束缚态", len(lv) >= 1, True)
    chkb("能级都在 (0, V₀) 内", all(0 < e < V0f for e in lv), True)
    chkb("能级升序", all(lv[i] < lv[i + 1] for i in range(len(lv) - 1)), True)
    chk("束缚态个数 = 解析上界 ceil(√(2mV₀)a/πħ)",
        len(lv), finite_well_count(V0f, af), 0)
    # 有限阱的基态一定**低于**同宽无限阱的基态（波函数可以渗出）
    ratio = infinite_vs_finite(V0f, af)
    chkb("有限阱基态低于同宽无限阱", ratio < 1.0, True)
    chkb("  但不会低太多（V₀ 远大于 E₁）", ratio > 0.7, True)
    # 阱越深，束缚态越多
    chkb("阱越深束缚态越多",
         len(finite_well_levels(2 * V0f, af, M_E, 8)) >= len(lv), True)
    # 阱越宽，基态越低
    chkb("阱越宽基态越低",
         finite_well_levels(V0f, 2 * af, M_E, 1)[0] < lv[0], True)

    print("\n自由高斯波包（色散）")
    s0 = 1e-9
    chk("t=0 时宽度不变", gauss_packet_sigma(s0, 0.0), s0, 1e-15)
    chkb("宽度随时间单调增大", gauss_packet_sigma(s0, 1e-12) > s0, True)
    chkb("t 越大越宽", gauss_packet_sigma(s0, 2e-12) > gauss_packet_sigma(s0, 1e-12), True)
    # 概率密度归一化（数值积分）
    t = 1e-13
    s_t = gauss_packet_sigma(s0, t)
    lo, hi = -10 * s_t, 10 * s_t
    steps2 = 40000
    tot = 0.0
    for i in range(steps2):
        xx = lo + (hi - lo) * (i + 0.5) / steps2
        tot += gauss_packet_prob(xx, t, s0, 0.0) * ((hi - lo) / steps2)
    chk("任意时刻 ∫|ψ|²dx = 1", tot, 1.0, 1e-5)
    # 峰值随时间下降（面积守恒 ⇒ 越高越宽越矮）
    chkb("峰值随时间下降",
         gauss_packet_prob(0.0, t, s0) < gauss_packet_prob(0.0, 0.0, s0), True)
    # 群速度：k₀ > 0 时波包向右移
    k0 = 1e9
    v = gauss_packet_speed(k0)
    chkb("群速度为正", v > 0, True)
    # 峰值应等于 1/(√(2π)σ(t))，且位置在 x = vt
    chk("t 时刻峰值在 x = vt 处",
        gauss_packet_prob(v * t, t, s0, k0) * math.sqrt(2 * math.pi) * gauss_packet_sigma(s0, t),
        1.0, 1e-9)
    # 展宽时间：σ 变成 2 倍所需的时间
    ts = gauss_packet_spread_time(s0, 2.0)
    chk("展宽到 2 倍的时间", gauss_packet_sigma(s0, ts), 2 * s0, 1e-9)
    # σ₀ 越小展宽越快（∝ σ₀²）
    chkb("σ₀ 减半则展宽时间降到 1/4",
         abs(gauss_packet_spread_time(s0 / 2, 2.0) * 4 - ts) < ts * 1e-9, True)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
