#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
thermal_kernel.py —— 高中物理「热学 + 近代物理」内核（选择性必修三）

覆盖：
  · 理想气体状态方程与三个特殊过程（等温/等压/等容）
  · 分子动理论：平均动能、方均根速率、压强的微观解释
  · 热力学第一定律 ΔU = Q + W（W 为外界对气体做的功）
  · 循环过程与热机效率、卡诺效率
  · 光电效应：光电效应方程、截止频率、遏止电压
  · 氢原子能级与跃迁：能级公式、光子能量与波长
  · 放射性衰变：半衰期

设计原则（与全项目一致）：
  · **不手写数字**：所有结果由本内核现算，常数集中在下面一处声明。
  · 符号约定明确：热力学第一定律取「外界对气体做功为正」（教材主流约定），
    页面上必须显式说明，否则同一题会因约定不同而得出相反的符号。
  · 自检：python thermal_kernel.py
"""

import math

import sympy as sp

__all__ = [
    "tex", "f", "num_str", "sci",
    "R_GAS", "K_BOLTZ", "H_PLANCK", "C_LIGHT", "E_CHARGE", "EV_TO_J", "N_A",
    "isothermal", "isobaric", "isochoric", "gas_moles", "pv_over_t",
    "avg_ke", "rms_speed", "pressure_kinetic",
    "first_law", "heat_engine_eff", "carnot_eff",
    "photon_energy", "ek_max", "threshold_freq", "stopping_voltage", "photon_wavelength",
    "H_GROUND_EV", "energy_level", "transition_energy", "level_wavelength",
    "remaining", "half_lives", "decayed_fraction",
]


# ---------------------------------------------------------------- 物理常数（实测类）
#
# 全部取自教材常数表，**不做位数扩展**。用到的每一步都会在页面出处分级里列出。

R_GAS = 8.31              # 摩尔气体常数，J/(mol·K)
K_BOLTZ = 1.38e-23        # 玻尔兹曼常数，J/K
H_PLANCK = 6.63e-34       # 普朗克常数，J·s
C_LIGHT = 3.00e8          # 真空光速，m/s
E_CHARGE = 1.60e-19       # 元电荷，C
EV_TO_J = 1.60e-19        # 1 eV = 1.60e-19 J
N_A = 6.02e23             # 阿伏加德罗常数，1/mol
H_GROUND_EV = -13.6       # 氢原子基态能量，eV


# ---------------------------------------------------------------- 排版助手

def tex(e):
    return sp.latex(sp.simplify(sp.sympify(e)))


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


# ---------------------------------------------------------------- 理想气体

def isothermal(p1, V1, V2):
    """等温过程：p₁V₁ = p₂V₂ ⇒ p₂ = p₁V₁/V₂。"""
    if V2 == 0:
        raise ValueError("V₂ 不能为零")
    return p1 * V1 / V2


def isobaric(V1, T1, T2):
    """等压过程：V₁/T₁ = V₂/T₂ ⇒ V₂ = V₁T₂/T₁（T 为热力学温度）。"""
    if T1 == 0:
        raise ValueError("T₁ 不能为零（须用热力学温度）")
    return V1 * T2 / T1


def isochoric(p1, T1, T2):
    """等容过程：p₁/T₁ = p₂/T₂ ⇒ p₂ = p₁T₂/T₁。"""
    if T1 == 0:
        raise ValueError("T₁ 不能为零（须用热力学温度）")
    return p1 * T2 / T1


def pv_over_t(p, V, T):
    """pV/T —— 一定质量理想气体的**不变量**。"""
    if T == 0:
        raise ValueError("T 不能为零")
    return p * V / T


def gas_moles(p, V, T):
    """由 pV = nRT 求物质的量 n。"""
    if T == 0:
        raise ValueError("T 不能为零")
    return p * V / (R_GAS * T)


# ---------------------------------------------------------------- 分子动理论

def avg_ke(T):
    """分子平均动能 Ē = (3/2)kT（只由温度决定，与种类无关）。"""
    return 1.5 * K_BOLTZ * T


def rms_speed(T, M_molar):
    """方均根速率 v_rms = √(3RT/M)，M 为摩尔质量（kg/mol）。"""
    if M_molar <= 0:
        raise ValueError("摩尔质量必须为正")
    return math.sqrt(3.0 * R_GAS * T / M_molar)


def pressure_kinetic(number_density, m_molecule, v_rms):
    """压强的微观解释：p = (1/3)·(N/V)·m·v̄²。

    N/V 是分子数密度，m 是单个分子质量，v̄² 是方均根速率的平方。
    """
    return number_density * m_molecule * v_rms * v_rms / 3.0


# ---------------------------------------------------------------- 热力学第一定律

def first_law(Q, W):
    """ΔU = Q + W，约定 **W 为外界对气体做的功**（教材主流约定）。

    例如气体被压缩时 W > 0，内能增加。若题目用「气体对外做功 W′」，
    则要换成 −W′ 再代入。
    """
    return Q + W


def heat_engine_eff(Q_in, Q_out):
    """热机效率 η = 1 − Q_out/Q_in。"""
    if Q_in == 0:
        raise ValueError("吸热不能为零")
    return 1.0 - Q_out / Q_in


def carnot_eff(T_cold, T_hot):
    """卡诺效率 η = 1 − T_c/T_h（T 为热力学温度）。

    它是**任何**工作在两热源之间的热机效率的上限 —— 与工作物质无关。
    """
    if T_hot == 0:
        raise ValueError("高温热源温度不能为零")
    return 1.0 - T_cold / T_hot


# ---------------------------------------------------------------- 光电效应

def photon_energy(nu):
    """光子能量 E = hν。"""
    return H_PLANCK * nu


def ek_max(nu, W0):
    """光电效应方程：E_k = hν − W₀（逸出功）。频率低于截止频率时为负（不发生）。"""
    return H_PLANCK * nu - W0


def threshold_freq(W0):
    """截止频率 ν₀ = W₀/h。"""
    return W0 / H_PLANCK


def stopping_voltage(Ek):
    """遏止电压 U = E_k/e（使光电子的最大初动能恰好被电场做负功耗尽）。"""
    return Ek / E_CHARGE


def photon_wavelength(E):
    """由光子能量求波长 λ = hc/E（E 的单位为 J）。"""
    if E <= 0:
        raise ValueError("能量必须为正")
    return H_PLANCK * C_LIGHT / E


# ---------------------------------------------------------------- 氢原子能级

def energy_level(n):
    """氢原子能级 Eₙ = −13.6/n² eV。"""
    return H_GROUND_EV / (n * n)


def transition_energy(n_from, n_to):
    """从 n_from 跃迁到 n_to 放出的光子能量（eV）：E = E_from − E_to。

    n_from > n_to 时为正（放能）；反之为负（需吸收能量）。
    """
    return energy_level(n_from) - energy_level(n_to)


def level_wavelength(n_from, n_to):
    """跃迁对应的光子波长（m）。"""
    E = transition_energy(n_from, n_to)
    if E <= 0:
        raise ValueError("该跃迁不放能（需吸收能量），不产生光子")
    return photon_wavelength(E * EV_TO_J)


# ---------------------------------------------------------------- 放射性衰变

def remaining(N0, half_life, t):
    """剩余数量 N = N₀·(1/2)^(t/T)。"""
    if half_life <= 0:
        raise ValueError("半衰期必须为正")
    return N0 * (0.5 ** (t / half_life))


def half_lives(t, half_life):
    """经过了多少个半衰期。"""
    if half_life <= 0:
        raise ValueError("半衰期必须为正")
    return t / half_life


def decayed_fraction(half_life, t):
    """已衰变的比例 = 1 − (1/2)^(t/T)。"""
    return 1.0 - 0.5 ** (t / half_life)


# ================================================================ 自检

def _selftest():
    bad = []

    def chk(name, got, want, tol=1e-9):
        ok = abs(float(got) - float(want)) <= tol
        print(f"  {'✓' if ok else '✗'} {name:46s} = {float(got):.6g}" +
              ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    print("理想气体状态方程")
    chk("等温：p₁V₁ = p₂V₂", isothermal(1e5, 2.0, 4.0), 0.5e5, 1e-6)
    chk("等温：体积减半则压强加倍", isothermal(1e5, 2.0, 1.0), 2e5, 1e-6)
    chk("等压：温度加倍则体积加倍", isobaric(1.0, 300.0, 600.0), 2.0, 1e-12)
    chk("等容：温度加倍则压强加倍", isochoric(1e5, 300.0, 600.0), 2e5, 1e-6)
    # 标准状况：1 mol 理想气体占 22.4 L（T=273 K, p=1.013e5 Pa）
    chk("标准状况 22.4 L 的物质的量 ≈ 1", gas_moles(1.013e5, 0.0224, 273.0), 1.0, 5e-3)
    chk("pV/T 是不变量", pv_over_t(1e5, 2.0, 300.0), pv_over_t(2e5, 1.0, 300.0), 1e-6)

    print("\n分子动理论")
    chk("300 K 的平均动能 (3/2)kT", avg_ke(300.0), 6.21e-21, 1e-23)
    chk("平均动能只与温度有关（600 K 加倍）", avg_ke(600.0), 2 * avg_ke(300.0), 1e-35)
    # 氧气 M = 0.032 kg/mol，300 K 的方均根速率 ≈ 483 m/s
    chk("氧气 300 K 的 v_rms", rms_speed(300.0, 0.032), 483.4, 0.5)
    chk("温度升高则 v_rms 变大", rms_speed(600.0, 0.032) > rms_speed(300.0, 0.032), 1.0)
    chk("v_rms ∝ √T（4 倍 T → 2 倍 v）", rms_speed(1200.0, 0.032) / rms_speed(300.0, 0.032), 2.0, 1e-9)
    # 压强微观式：与宏观 pV=nRT 自洽量纲
    chk("压强微观式 p = (1/3)n m v²", pressure_kinetic(2.7e25, 5.3e-26, 500.0), 1.1925e5, 1.0)

    print("\n热力学第一定律")
    chk("吸热 100 J、外界做功 −40 J → ΔU = 60 J", first_law(100, -40), 60.0, 1e-12)
    chk("绝热压缩：Q=0、W=50 → ΔU=50", first_law(0, 50), 50.0, 1e-12)
    chk("等温：ΔU=0 ⇒ Q=−W", first_law(-30, 30), 0.0, 1e-12)
    chk("符号约定：放热为负、外界做功为正", first_law(-100, 0), -100.0, 1e-12)

    print("\n循环与热机效率")
    chk("η = 1 − Q_out/Q_in", heat_engine_eff(400.0, 250.0), 0.375, 1e-12)
    chk("全部吸热都对外做功时 η = 1", heat_engine_eff(100.0, 0.0), 1.0, 1e-12)
    chk("卡诺效率 1 − T_c/T_h", carnot_eff(300.0, 500.0), 0.4, 1e-12)
    # 卡诺效率是上限
    chk("卡诺效率 ≥ 同温差的真实效率", carnot_eff(300.0, 500.0) > heat_engine_eff(400.0, 250.0), True)

    print("\n光电效应")
    W0 = 3.0e-19
    nu = 1.5e15
    chk("光子能量 hν", photon_energy(nu), H_PLANCK * nu, 1e-40)
    chk("最大初动能 hν − W₀", ek_max(nu, W0), H_PLANCK * nu - W0, 1e-40)
    chk("截止频率 ν₀ = W₀/h", threshold_freq(W0), 4.5249e14, 1e11)
    chk("低于截止频率时不发生光电效应", ek_max(4.0e14, W0) < 0, 1.0)
    chk("遏止电压 U = E_k/e", stopping_voltage(ek_max(nu, W0)), (H_PLANCK * nu - W0) / E_CHARGE, 1e-12)
    # 波长公式与能量互逆
    E_ph = photon_energy(5.0e14)
    chk("λ = hc/E 自洽", photon_wavelength(E_ph) * E_ph, H_PLANCK * C_LIGHT, 1e-40)

    print("\n氢原子能级")
    chk("基态 E₁ = −13.6 eV", energy_level(1), -13.6, 1e-12)
    chk("E₂ = −3.4 eV", energy_level(2), -3.4, 1e-12)
    chk("E₃ ≈ −1.511 eV", energy_level(3), -1.5111, 1e-3)
    chk("3→2 跃迁放能 1.889 eV", transition_energy(3, 2), 1.8889, 1e-3)
    chk("1→2 跃迁为负（需吸能）", transition_energy(1, 2) < 0, 1.0)
    # 3→2 是 Hα 线，波长约 658 nm
    chk("3→2 的波长 ≈ 658 nm", level_wavelength(3, 2) * 1e9, 658.0, 1.0)
    chk("2→1 的波长 ≈ 122 nm（莱曼 α）", level_wavelength(2, 1) * 1e9, 121.5, 1.0)
    # 能级差越大波长越短
    chk("能级差越大波长越短", level_wavelength(2, 1) < level_wavelength(3, 2), True)

    print("\n放射性衰变")
    chk("3 个半衰期后剩 1/8", remaining(1000.0, 5.0, 15.0), 125.0, 1e-9)
    chk("经过的半衰期数", half_lives(15.0, 5.0), 3.0, 1e-12)
    chk("已衰变比例 1 − (1/2)^n", decayed_fraction(5.0, 15.0), 1 - 0.125, 1e-12)
    chk("一个半衰期后剩一半", remaining(100.0, 8.0, 8.0), 50.0, 1e-12)
    chk("半衰期与初始数量无关", remaining(200.0, 5.0, 5.0) / remaining(100.0, 5.0, 5.0), 2.0, 1e-12)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
