#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
thermochem_kernel.py —— 高中「热化学」内核（选择性必修一 · 化学反应原理）

覆盖：
  · 反应热 ΔH 的符号约定（放热 ΔH < 0、吸热 ΔH > 0）与能量图
  · **盖斯定律**：反应热只由始态末态决定 ⇒ 热化学方程式可以像代数式一样**线性组合**
  · 由标准生成焓计算 ΔH = Σν·ΔHf(产物) − Σν·ΔHf(反应物)
  · 由键能估算 ΔH = ΣE(断裂的键) − ΣE(形成的键)
  · 燃烧热与热量计算 Q = n·|ΔH|
  · 中和热与量热法：ΔT = Q/(m·c)
  · 活化能与催化剂（只改变 Ea，不改变 ΔH）

设计原则（与全项目一致）：
  · **不手写数字**：ΔH、热量、温度变化全部由内核现算；
    盖斯定律是**真做线性组合**（可以反向、可以乘系数），不是套一个结论。
  · 符号约定写死：**ΔH 的单位是 kJ/mol，放热为负**。页面上一律标注。
  · 自检：python thermochem_kernel.py
"""

import math

__all__ = [
    "f", "num_str",
    "C_WATER", "NEUTRALIZATION_DH",
    "delta_h_formation", "delta_h_bonds",
    "reverse_step", "hess_combine", "hess_path",
    "heat_amount", "moles_for_heat", "temperature_rise", "mass_for_rise",
    "neutralization_dh", "neutralization_moles",
    "exo_or_endo", "activation_effect",
]


# ---------------------------------------------------------------- 常数（教材常用值）
C_WATER = 4.18             # 水的比热容，J/(g·K)
NEUTRALIZATION_DH = -57.3  # 强酸强碱稀溶液的中和热，kJ/mol


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
    return f(val, digits)


def _pair_list(items):
    """把 [(系数, 值), ...] 规整成 (float 系数, float 值) 的列表。"""
    out = []
    for it in items:
        c, v = it
        out.append((float(c), float(v)))
    return out


# ---------------------------------------------------------------- 符号与能量图
def exo_or_endo(dh):
    """返回 'exo'（放热）、'endo'（吸热）或 'zero'。"""
    if dh > 1e-9:
        return "endo"
    if dh < -1e-9:
        return "exo"
    return "zero"


# ---------------------------------------------------------------- 盖斯定律
def reverse_step(dh):
    """把热化学方程式反向书写时，ΔH 变号。"""
    return -dh


def hess_combine(steps):
    """盖斯定律：把若干步线性组合起来。

    steps 为 [(系数, ΔH), ...]；系数可正可负（负表示该步反向书写）。
    返回组合后的总 ΔH。这就是「反应热与路径无关」的直接体现。
    """
    return sum(float(c) * float(dh) for c, dh in steps)


def hess_path(path_dhs):
    """一条路径上各步 ΔH 之和（用来与「直接一步」对照）。"""
    return sum(float(x) for x in path_dhs)


# ---------------------------------------------------------------- 生成焓与键能
def delta_h_formation(products, reactants):
    """ΔH = Σν·ΔHf(产物) − Σν·ΔHf(反应物)。

    products / reactants 为 [(化学计量数, ΔHf), ...]（kJ/mol）。
    """
    p = sum(c * v for c, v in _pair_list(products))
    r = sum(c * v for c, v in _pair_list(reactants))
    return p - r


def delta_h_bonds(broken, formed):
    """ΔH = ΣE(断裂的键) − ΣE(形成的键)（kJ/mol）。

    broken / formed 为 [(键的数目, 键能), ...]。
    断裂要吸热（正贡献）、形成要放热（负贡献），所以是「断 − 成」。
    """
    b = sum(c * v for c, v in _pair_list(broken))
    fo = sum(c * v for c, v in _pair_list(formed))
    return b - fo


# ---------------------------------------------------------------- 热量与量热
def heat_amount(dh, n):
    """放出/吸收的热量（kJ，带符号）：Q = n·ΔH。"""
    return float(dh) * float(n)


def moles_for_heat(dh, Q):
    """由目标热量反推需要的物质的量。"""
    if abs(float(dh)) < 1e-12:
        raise ValueError("ΔH 不能为 0")
    return float(Q) / float(dh)


def temperature_rise(Q_kJ, mass_g, c=C_WATER):
    """由放出的热量求温升：ΔT = Q/(m·c)。

    Q 以 kJ 给出，内部换算成 J（×1000）；m 为溶液质量（g）；c 为比热容 J/(g·K)。
    """
    if float(mass_g) <= 0 or float(c) <= 0:
        raise ValueError("质量与比热容必须为正")
    return float(Q_kJ) * 1000.0 / (float(mass_g) * float(c))


def mass_for_rise(Q_kJ, dT, c=C_WATER):
    """由热量与温升反推质量。"""
    if abs(float(dT)) < 1e-12:
        raise ValueError("温升不能为 0")
    return float(Q_kJ) * 1000.0 / (float(dT) * float(c))


# ---------------------------------------------------------------- 中和热
def neutralization_dh(q_released_kJ, n_water):
    """由实验数据求中和热：ΔH = Q/n(生成的水)。

    q_released_kJ 用**正值**传入（实际放出的热量），返回带负号的 ΔH。
    """
    if float(n_water) <= 0:
        raise ValueError("水的物质的量必须为正")
    return -abs(float(q_released_kJ)) / float(n_water)


def neutralization_moles(c_acid, v_acid_L, c_base, v_base_L):
    """强酸强碱中和生成的水的物质的量（按物质的量少的一方算）。"""
    n_a = float(c_acid) * float(v_acid_L)
    n_b = float(c_base) * float(v_base_L)
    return min(n_a, n_b)


# ---------------------------------------------------------------- 活化能与催化剂
def activation_effect(Ea_forward, dh, catalyst_drop=0.0):
    """催化剂把正逆反应的活化能同时降低 catalyst_drop。

    **ΔH 不变** —— 因为 ΔH = Ea(正) − Ea(逆)，两边同时降低相同的量，差不变。
    返回 (Ea_正, Ea_逆, ΔH)。
    """
    ea_f = float(Ea_forward) - float(catalyst_drop)
    ea_r = ea_f - float(dh)          # 由 ΔH = Ea_正 − Ea_逆 得到
    return ea_f, ea_r, ea_f - ea_r


# ================================================================ 自检
def _selftest():
    bad = []

    def chk(name, got, want, tol=1e-9):
        if isinstance(got, str) or isinstance(want, str):
            ok = str(got) == str(want)
        elif isinstance(got, bool) or isinstance(want, bool):
            ok = bool(got) == bool(want)
        else:
            ok = abs(float(got) - float(want)) <= tol * max(1.0, abs(float(want)))
        print(f"  {'✓' if ok else '✗'} {name:46s} = {got}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    print("符号约定")
    chk("放热 ΔH < 0", exo_or_endo(-890.3), "exo")
    chk("吸热 ΔH > 0", exo_or_endo(131.3), "endo")
    chk("ΔH = 0 的情况", exo_or_endo(0.0), "zero")
    chk("放热的 ΔH 是负数", -890.3 < 0, True)

    print("\n盖斯定律")
    chk("反向书写要变号", reverse_step(-393.5), 393.5)
    # C(s) + O₂ → CO₂  ΔH = −393.5
    # CO + ½O₂ → CO₂  ΔH = −283.0  ⇒  C + ½O₂ → CO 应 = −393.5 − (−283.0) = −110.5
    chk("由两步相减得一步", hess_combine([(1, -393.5), (-1, -283.0)]), -110.5, 1e-9)
    # 路径无关：分三步还是一步，结果相同
    direct = -110.5
    path = hess_path([-393.5, 283.0])
    chk("路径无关（直接 = 分步）", path, direct, 1e-9)
    # 系数可以不为 1：2C + O₂ → 2CO ⇒ ΔH 乘以 2
    chk("总式乘 2 则 ΔH 乘 2", hess_combine([(2, -110.5)]), -221.0, 1e-9)
    # 一个循环的 ΔH 必为 0（回到始态）
    chk("闭环的 ΔH 之和为 0", hess_combine([(1, -393.5), (1, 283.0), (1, 110.5)]), 0.0, 1e-9)
    # 组装：由反应 (1)(2)(3) 线性组合出目标反应
    # (1) CH₄ + 2O₂ → CO₂ + 2H₂O  ΔH = −890.3
    # (2) H₂ + ½O₂ → H₂O           ΔH = −285.8
    # (3) C + O₂ → CO₂             ΔH = −393.5
    # 目标：C + 2H₂ → CH₄ ⇒ (3) + 2×(2) − (1)
    target = hess_combine([(1, -393.5), (2, -285.8), (-1, -890.3)])
    chk("组合出 C + 2H₂ → CH₄", target, -74.8, 1e-9)
    chk("  与标准生成焓一致（ΔHf(CH₄) = −74.8）", target, -74.8, 1e-9)

    print("\n由标准生成焓计算")
    # CH₄(g) + 2O₂(g) → CO₂(g) + 2H₂O(l)
    dh = delta_h_formation([(1, -393.5), (2, -285.8)], [(1, -74.8), (2, 0.0)])
    chk("CH₄ 燃烧的 ΔH", dh, -890.3, 1e-9)
    chk("  是放热", exo_or_endo(dh), "exo")
    # 单质的 ΔHf 规定为 0
    chk("O₂ 的 ΔHf = 0", delta_h_formation([(0, 0.0)], [(0, 0.0)]), 0.0, 1e-9)
    chk("  所以少了 O₂ 不影响结果",
        delta_h_formation([(1, -393.5), (2, -285.8)], [(1, -74.8)]), -890.3, 1e-9)
    # 吸热反应：CaCO₃ → CaO + CO₂  ΔHf: −1207.0, −635.5, −393.5
    dh2 = delta_h_formation([(1, -635.5), (1, -393.5)], [(1, -1207.0)])
    chk("CaCO₃ 分解的 ΔH", dh2, 178.0, 1e-9)
    chk("  是吸热", exo_or_endo(dh2), "endo")

    print("\n由键能估算")
    # H₂ + Cl₂ → 2HCl
    dh3 = delta_h_bonds([(1, 436.0), (1, 243.0)], [(2, 431.0)])
    chk("H₂ + Cl₂ → 2HCl 的 ΔH", dh3, -183.0, 1e-9)
    chk("  放热", exo_or_endo(dh3), "exo")
    # N₂ + 3H₂ → 2NH₃（断 1 个 N≡N + 3 个 H−H，成 6 个 N−H）
    dh4 = delta_h_bonds([(1, 946.0), (3, 436.0)], [(6, 391.0)])
    chk("合成氨的 ΔH 估算", dh4, -92.0, 1e-9)
    chk("  放热", exo_or_endo(dh4), "exo")
    # 断键吸热、成键放热：把成键项去掉，ΔH 必为正
    chk("只断不成时 ΔH > 0",
        delta_h_bonds([(1, 436.0), (1, 243.0)], []) > 0, True)
    # 断的键能与成的键能相等时 ΔH = 0
    chk("断成相等时 ΔH = 0", delta_h_bonds([(2, 400.0)], [(2, 400.0)]), 0.0, 1e-9)

    print("\n热量与量热法")
    chk("燃烧 1 mol CH₄ 放热", heat_amount(-890.3, 1.0), -890.3, 1e-12)
    chk("燃烧 2 mol CH₄ 放热", heat_amount(-890.3, 2.0), -1780.6, 1e-12)
    chk("放出 890.3 kJ 需要 1 mol", moles_for_heat(-890.3, -890.3), 1.0, 1e-12)
    chk("要放 445.15 kJ 需要 0.5 mol", moles_for_heat(-890.3, -445.15), 0.5, 1e-12)
    # 量热：5.73 kJ 使 100 g 水升温
    chk("ΔT = Q/(mc)", temperature_rise(5.73, 100.0), 5730.0 / (100.0 * 4.18), 1e-9)
    chk("  数值约为 13.7 K", temperature_rise(5.73, 100.0), 13.708, 1e-3)
    chk("反向求质量", mass_for_rise(5.73, temperature_rise(5.73, 100.0)), 100.0, 1e-9)
    # 中和热
    chk("中和热约 −57.3", neutralization_dh(57.3, 1.0), -57.3, 1e-9)
    chk("  强酸强碱中和热的常见值", NEUTRALIZATION_DH, -57.3, 1e-12)
    chk("生成 0.05 mol 水放热 2.865 kJ", neutralization_dh(2.865, 0.05), -57.3, 1e-9)
    chk("物质的量取少的一方（酸过量）", neutralization_moles(2.0, 0.05, 1.0, 0.05), 0.05, 1e-12)
    chk("  碱过量时同理", neutralization_moles(1.0, 0.05, 2.0, 0.05), 0.05, 1e-12)
    # 中和热实验的温升：0.05 mol 水 → 2.865 kJ 使 100 g 溶液升温
    chk("中和实验的温升", temperature_rise(2.865, 100.0), 2865.0 / 418.0, 1e-9)

    print("\n活化能与催化剂")
    ea_f, ea_r, dh5 = activation_effect(200.0, -50.0)
    chk("Ea(正)", ea_f, 200.0, 1e-12)
    chk("Ea(逆) = Ea(正) − ΔH", ea_r, 250.0, 1e-12)
    chk("  由 Ea 反推 ΔH", ea_f - ea_r, -50.0, 1e-12)
    for drop in (0.0, 30.0, 80.0):
        a, b, d = activation_effect(200.0, -50.0, drop)
        chk(f"催化剂降 {drop} 时 ΔH 不变", d, -50.0, 1e-12)
        chk(f"  正逆活化能同步降低 {drop}", 200.0 - a, drop, 1e-12)
    chk("催化剂不改变 ΔH（放热仍是放热）",
        exo_or_endo(activation_effect(200.0, -50.0, 80.0)[2]), "exo")

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
