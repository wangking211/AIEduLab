#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chemcalc_kernel.py —— 高中化学计算精确内核（物质的量体系）

与 edu-chem-reaction 的分工：
  · chem-reaction 管「反应本身」——配平、微观断键成键、原子守恒、**质量分数**体系；
  · 本内核管「计算」——**物质的量**体系：摩尔换算、物质的量浓度、化学计量与
    限量试剂判断、电离与 pH、平衡三段式、溶度积、法拉第定律、反应速率。

设计原则（与全项目一致）：
  · **不手写数字**：所有结果由本内核现算，generate.py 只做排版。
  · **精确优先**：化学计量用整数/有理数算（配比是整数比）；只有 pH 的对数与
    平衡开方必然用浮点，并把「近似」如实标注（如「忽略水的电离」）。
  · 自检：python chemcalc_kernel.py
"""

import math

import sympy as sp

__all__ = [
    "tex", "f", "num_str", "sci",
    "NA", "VM", "F_CONST", "KW",
    "mole_from_mass", "mole_from_particles", "mole_from_gas_volume",
    "mass_from_mole", "particles_from_mole", "gas_volume_from_mole",
    "molarity", "moles_in_solution", "dilute",
    "stoich_limit",
    "ph_strong_acid", "ph_strong_base", "ph_weak_acid", "ph_to_conc_H",
    "titration_ph",
    "ice_quadratic", "ksp_judge",
    "faraday_moles_e", "faraday_mass",
    "rate_first_order", "half_life",
]

# ---------------------------------------------------------------- 常数（实测类）
NA = 6.02e23            # 阿伏加德罗常数，1/mol（教材取值 6.02×10²³）
VM = 22.4               # 标准状况气体摩尔体积，L/mol（0 ℃、101.325 kPa）
F_CONST = 96485.0       # 法拉第常数，C/mol
KW = 1.0e-14            # 25 ℃ 水的离子积


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


def sci(x, digits=3):
    """科学计数法的 LaTeX（a\\times10^{b}）。"""
    v = float(x)
    if v == 0:
        return "0"
    e = math.floor(math.log10(abs(v)))
    mant = v / (10 ** e)
    return f"{mant:.{digits}f} \\times 10^{{{e}}}"


# ---------------------------------------------------------------- 物质的量换算
#
# 四条通道互相连通：m ↔ n ↔ N，以及 标况气体 V ↔ n ↔ N。
# 内核只做「一次一步」的换算，不替调用方做多步链 —— 链由问题自己串。

def mole_from_mass(m, M):
    """n = m / M（m 克，M g/mol）。"""
    if M <= 0:
        raise ValueError("摩尔质量必须为正")
    return m / M


def mole_from_particles(N):
    """n = N / N_A。"""
    return N / NA


def mole_from_gas_volume(V_liters, vm=VM):
    """n = V / V_m（标准状况）。"""
    return V_liters / vm


def mass_from_mole(n, M):
    """m = n·M。"""
    return n * M


def particles_from_mole(n):
    """N = n·N_A。"""
    return n * NA


def gas_volume_from_mole(n, vm=VM):
    """V = n·V_m（标准状况）。"""
    return n * vm


# ---------------------------------------------------------------- 物质的量浓度

def molarity(n, V_liters):
    """c = n / V（mol/L）。V 为**溶液体积**，不是溶剂体积。"""
    if V_liters <= 0:
        raise ValueError("溶液体积必须为正")
    return n / V_liters


def moles_in_solution(c, V_liters):
    """n = c·V。"""
    return c * V_liters


def dilute(c1, V1, V2):
    """稀释定律 c₁V₁ = c₂V₂ —— 返回稀释后的浓度。

    它的物理内容是一个**不变量**：加水只变体积、不变溶质的物质的量
    （也不变溶质的质量）。所以读数里 n 应当恒定，c 随 V 反比下降。
    """
    if V2 <= 0:
        raise ValueError("稀释后体积必须为正")
    if V2 < V1:
        raise ValueError("稀释后体积不能小于原体积")
    return c1 * V1 / V2


# ---------------------------------------------------------------- 化学计量与限量试剂

def stoich_limit(amounts, coeffs, products=()):
    """按化学计量判断限量试剂，并算出反应进度与各物质的量。

    参数
    ----
    amounts  反应物初始物质的量（mol），与 coeffs 一一对应
    coeffs   化学方程式中反应物的系数（正整数）
    products [(系数, 名称), ...]，生成物的系数与名称

    做法
    ----
    设反应进度 ξ（mol 反应次数），则第 i 个反应物消耗 cᵢ·ξ。
    能走的 ξ 上限是 min(aᵢ/cᵢ) —— 取到最小的那个反应物就是**限量试剂**，
    它恰好耗尽，其余按 cᵢ·ξ 消耗并留下剩余。这一步是**精确**的：
    配比是整数比，比较用有理数，不引入浮点。
    """
    if len(amounts) != len(coeffs):
        raise ValueError("反应物数量与系数数量不一致")
    if any(c <= 0 for c in coeffs):
        raise ValueError("系数必须为正")
    ratios = [sp.Rational(sp.nsimplify(a)) / int(c) for a, c in zip(amounts, coeffs)]
    xi = min(ratios)
    idx = ratios.index(xi)
    consumed = [int(c) * xi for c in coeffs]
    leftover = [sp.nsimplify(a) - con for a, con in zip(amounts, consumed)]
    prod = [(int(c), nm, int(c) * xi) for c, nm in products]
    return {
        "xi": xi,
        "limiting_index": idx,
        "limiting_is_first": idx == 0,
        "consumed": consumed,
        "leftover": leftover,
        "products": prod,
    }


# ---------------------------------------------------------------- 电离与 pH
#
# 两个透明的前提（写步骤时必须说出来，否则图在撒谎）：
#   · 强酸/强碱视为**完全电离**；
#   · 只考虑一级电离，且**忽略水的自偶电离**贡献（当 10⁻⁷ 不可忽略时，如
#     极稀溶液，标为近似失效）。

def ph_to_conc_H(pH):
    """c(H⁺) = 10⁻ᵖᴴ。"""
    return 10 ** (-pH)


def ph_strong_acid(c):
    """一元强酸：c(H⁺) = c。"""
    if c <= 0:
        raise ValueError("浓度必须为正")
    return -math.log10(c)


def ph_strong_base(c):
    """一元强碱：c(OH⁻) = c，pH = 14 − pOH（25 ℃）。"""
    if c <= 0:
        raise ValueError("浓度必须为正")
    return 14.0 + math.log10(c)


def ph_weak_acid(c, Ka):
    """一元弱酸：解 x² / (c − x) = Ka，取正根。

    把 x² + Ka·x − Ka·c = 0 的正根写成闭式：
        x = ( −Ka + √(Ka² + 4Ka·c) ) / 2
    于是 pH = −lg x。**这是精确解**（在「只考虑一级电离」的前提下），
    不是「把弱酸当强酸」之类的近似。
    """
    if c <= 0 or Ka <= 0:
        raise ValueError("浓度与 Ka 必须为正")
    disc = Ka * Ka + 4.0 * Ka * c
    x = (-Ka + math.sqrt(disc)) / 2.0
    return -math.log10(x)


def titration_ph(c_acid, V_acid_mL, c_base, V_base_mL, kw=KW):
    """一元强酸 + 一元强碱的中和滴定：任意加碱体积下的 pH。

    分三段，每段都是精确的物质的量守恒：
      · 酸过量：剩余 n(H⁺) = c_酸V_酸 − c_碱V_碱，除以总体积得 c(H⁺)；
      · 碱过量：剩余 n(OH⁻) = c_碱V_碱 − c_酸V_酸，除以总体积得 c(OH⁻)，
        再由 pH = 14 − pOH；
      · 恰好中和：pH = 7（25 ℃）。
    """
    n_h = c_acid * V_acid_mL / 1000.0
    n_oh = c_base * V_base_mL / 1000.0
    v_tot = (V_acid_mL + V_base_mL) / 1000.0
    if v_tot <= 0:
        raise ValueError("总体积必须为正")
    diff = n_h - n_oh
    scale = max(n_h, n_oh, 1e-18)
    if abs(diff) <= 1e-12 * scale:                 # 恰好中和
        return 7.0, 0.0
    if diff > 0:                                    # 酸过量
        return -math.log10(diff / v_tot), diff
    pOH = -math.log10(-diff / v_tot)                # 碱过量
    return (14.0 - pOH), diff


# ---------------------------------------------------------------- 化学平衡（三段式）

def ice_quadratic(K, c0):
    """N₂O₄ ⇌ 2NO₂ 型平衡：解 4x²/(c₀ − x) = K，返回 (x, α, 平衡浓度列表)。

    三段式（ICE）：
        初始   c₀      0
        变化   −x      +2x
        平衡   c₀−x    2x
    代入 K = (2x)²/(c₀−x) 得 4x² + Kx − Kc₀ = 0，正根
        x = ( −K + √(K² + 16Kc₀) ) / 8
    转化率 α = x / c₀。K 与 c₀ 的**联动**正是本题的教学点：K 是常数，
    但 α 随 c₀ 变（稀释使平衡向分子数多的一侧移动）。
    """
    if K <= 0 or c0 <= 0:
        raise ValueError("K 与初始浓度必须为正")
    x = (-K + math.sqrt(K * K + 16.0 * K * c0)) / 8.0
    alpha = x / c0
    return x, alpha, [c0 - x, 2.0 * x]


def ksp_judge(Q, Ksp):
    """溶度积判断：Q > Ksp 生成沉淀，Q < Ksp 不沉淀，Q = Ksp 恰好饱和。

    返回 (结论字符串, Q/Ksp 比值)。比值的意义是「过饱和倍数」——
    比单看 Q 与 Ksp 谁大更能说明「超出多少」。
    """
    if Ksp <= 0:
        raise ValueError("Ksp 必须为正")
    ratio = Q / Ksp
    if ratio > 1 + 1e-12:
        return "生成沉淀", ratio
    if ratio < 1 - 1e-12:
        return "不生成沉淀（未饱和）", ratio
    return "恰好饱和", ratio


# ---------------------------------------------------------------- 电化学（法拉第定律）

def faraday_moles_e(z, I, t):
    """转移电子的物质的量：n(e⁻) = I·t / F。"""
    return I * t / F_CONST


def faraday_mass(M, z, I, t):
    """电极析出/溶解的质量：m = M·I·t / (z·F)。

    z 是每生成 1 个该物质转移的电子数（如 Cu²⁺ + 2e⁻ → Cu，z = 2）。
    """
    if z <= 0:
        raise ValueError("电子数必须为正")
    return M * I * t / (z * F_CONST)


# ---------------------------------------------------------------- 反应速率

def half_life(k):
    """一级反应的半衰期 t½ = ln2 / k —— 与初始浓度**无关**。"""
    if k <= 0:
        raise ValueError("速率常数必须为正")
    return math.log(2.0) / k


def rate_first_order(c0, k, t):
    """一级反应：c(t) = c₀·e^(−kt)。"""
    return c0 * math.exp(-k * t)


# ================================================================ 自检

def _selftest():
    bad = []

    def chk(name, got, want, tol=None):
        if tol is None:
            ok = got == want
        else:
            ok = abs(float(got) - float(want)) <= tol
        shown = got if tol is None else f"{float(got):.6f}"
        print(f"  {'✓' if ok else '✗'} {name:46s} = {shown}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    print("物质的量换算")
    chk("44 g CO₂ 的物质的量", f(mole_from_mass(44, 44), 6), "1")
    chk("1 mol 的粒子数 = N_A", sci(particles_from_mole(1)), "6.020 \\times 10^{23}")
    chk("1 mol 标况气体体积", f(gas_volume_from_mole(1)), "22.4")
    chk("2 mol 水的质量 (M=18)", f(mass_from_mole(2, 18)), "36")
    chk("0.5 mol O₂ 的质量 (M=32)", f(mass_from_mole(0.5, 32)), "16")
    chk("3.01e23 个粒子的物质的量", f(mole_from_particles(3.01e23), 6), "0.5")

    print("\n物质的量浓度与稀释")
    chk("0.5 mol 溶于 2 L", f(molarity(0.5, 2)), "0.25")
    chk("1 mol/L × 100 mL 稀释到 500 mL", f(dilute(1, 100, 500)), "0.2")
    chk("0.5 mol/L × 200 mL 稀释到 1 L", f(dilute(0.5, 200, 1000)), "0.1")
    # 稀释不变量：溶质的物质的量恒定
    n1 = moles_in_solution(1.0, 0.100)
    n2 = moles_in_solution(dilute(1.0, 100, 500), 0.500)
    chk("稀释前后溶质物质的量守恒", n1 == n2, True)
    try:
        dilute(1, 500, 100)
        chk("稀释到更小体积应报错", False, True)
    except ValueError:
        chk("稀释到更小体积应报错", True, True)

    print("\n化学计量与限量试剂（N₂ + 3H₂ → 2NH₃）")
    r = stoich_limit([1, 2], [1, 3], products=[(2, "NH₃")])
    chk("限量试剂是 H₂（下标 1）", r["limiting_index"], 1)
    chk("反应进度 ξ = 2/3", r["xi"], sp.Rational(2, 3))
    chk("H₂ 恰好耗尽", r["leftover"][1], sp.Rational(0))
    chk("N₂ 剩余 1/3", r["leftover"][0], sp.Rational(1, 3))
    chk("生成 NH₃ = 4/3", r["products"][0][2], sp.Rational(4, 3))
    # 换一组投料：n(N₂)=1、n(H₂)=9 → 此时 N₂ 成为限量试剂
    r2 = stoich_limit([1, 9], [1, 3], products=[(2, "NH₃")])
    chk("N₂ 不足时限量试剂变 N₂", r2["limiting_index"], 0)
    chk("  └ N₂ 恰好耗尽", r2["leftover"][0], sp.Rational(0))
    chk("  └ H₂ 剩余 6", r2["leftover"][1], sp.Rational(6))

    print("\n电离与 pH")
    chk("0.01 mol/L 强酸 pH", f(ph_strong_acid(0.01)), "2")
    chk("0.01 mol/L 强碱 pH", f(ph_strong_base(0.01)), "12")
    chk("0.1 mol/L 强酸 pH", f(ph_strong_acid(0.1)), "1")
    # 醋酸 Ka=1.8e-5，0.1 mol/L：教科书值 pH≈2.87
    chk("0.1 mol/L 醋酸 pH（Ka=1.8e-5）", ph_weak_acid(0.1, 1.8e-5), 2.8756, 1e-3)
    # 弱酸必比同浓度强酸 pH 大
    ok = ph_weak_acid(0.1, 1.8e-5) > ph_strong_acid(0.1)
    chk("弱酸 pH > 同浓度强酸", ok, True)
    chk("c(H⁺) 与 pH 互逆", f(ph_to_conc_H(3.0), 6), "0.001")

    print("\n中和滴定（0.1 mol/L HCl 20 mL 对 0.1 mol/L NaOH）")
    ca, va, cb = 0.1, 20.0, 0.1
    chk("未加碱：pH = −lg 0.1", f(titration_ph(ca, va, cb, 0.0)[0]), "1")
    chk("加 10 mL（半中和）：pH ≈ 1.48", titration_ph(ca, va, cb, 10.0)[0], 1.4771, 1e-3)
    chk("加 20 mL（等当点）：pH = 7", f(titration_ph(ca, va, cb, 20.0)[0]), "7")
    chk("加 30 mL（碱过量）：pH ≈ 12.30", titration_ph(ca, va, cb, 30.0)[0], 12.301030, 1e-3)
    # 等当点附近 pH 剧变（滴定曲线的特征）
    a = titration_ph(ca, va, cb, 19.98)[0]
    b = titration_ph(ca, va, cb, 20.02)[0]
    ok = (b - a) > 5
    chk("等当点前后 0.04 mL 内 pH 跳变 > 5", ok, True)

    print("\n化学平衡三段式（N₂O₄ ⇌ 2NO₂）")
    x, alpha, eq = ice_quadratic(1.0, 1.0)
    chk("K=1, c₀=1 解得 x ≈ 0.3904", x, 0.390388, 1e-5)
    chk("  └ 平衡 [N₂O₄] = 1−x", f(eq[0]), f(1 - x))
    chk("  └ 转化率 α = x/c₀", alpha, x / 1.0, 1e-12)
    # K 恒定、α 随 c₀ 变：稀释使平衡向分子数多的一侧移动
    a1 = ice_quadratic(1.0, 1.0)[1]
    a2 = ice_quadratic(1.0, 0.1)[1]
    ok = a2 > a1
    chk("K 相同时，初始浓度越小转化率越高", ok, True)
    # 校验解确实满足平衡式
    xx = ice_quadratic(0.5, 0.8)[0]
    chk("解代入 K=4x²/(c₀−x) 自洽", 4 * xx * xx / (0.8 - xx), 0.5, 1e-12)

    print("\n溶度积")
    res, ratio = ksp_judge(1.0e-4, 1.0e-5)
    chk("Q > Ksp → 生成沉淀", res, "生成沉淀")
    chk("  └ 过饱和倍数 = 10", f(ratio), "10")
    res2, _ = ksp_judge(1.0e-6, 1.0e-5)
    chk("Q < Ksp → 不沉淀", res2, "不生成沉淀（未饱和）")

    print("\n法拉第定律")
    n_e = faraday_moles_e(2, 1.0, 1800)
    chk("1 A × 1800 s 的电子 mol", n_e, 1800 / 96485.0, 1e-15)
    chk("析出铜 (M=63.5, z=2)", faraday_mass(63.5, 2, 1.0, 1800), 0.592324, 1e-5)
    chk("析出银 (M=108, z=1)", faraday_mass(108.0, 1, 2.0, 3600), 8.059284, 1e-5)
    # 与「电子物质的量」自洽：m = n(e⁻)·M / z
    chk("m = n(e⁻)·M/z 自洽",
        faraday_mass(63.5, 2, 1.0, 1800), faraday_moles_e(2, 1.0, 1800) * 63.5 / 2, 1e-15)

    print("\n反应速率（一级）")
    chk("k=0.1 /min 的半衰期", half_life(0.1), math.log(2) / 0.1, 1e-12)
    chk("c(0) = c₀", f(rate_first_order(1.0, 0.1, 0.0)), "1")
    chk("一个半衰期后剩一半", rate_first_order(1.0, 0.1, half_life(0.1)), 0.5, 1e-12)
    chk("两个半衰期后剩四分之一", rate_first_order(1.0, 0.1, 2 * half_life(0.1)), 0.25, 1e-12)
    # 一级反应：半衰期与初始浓度无关
    ok = abs(half_life(0.1) - math.log(2) / 0.1) < 1e-15
    chk("半衰期与初始浓度无关", ok, True)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
