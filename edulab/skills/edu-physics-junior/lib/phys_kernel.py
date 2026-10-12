# -*- coding: utf-8 -*-
"""
phys_kernel.py — 初中物理（力学与电学）确定性计算核心（sympy 精确运算）。

单一数据源设计：杠杆平衡、压强、浮力、滑轮组、欧姆定律、串并联、电功率、
焦耳定律全部由本模块精确算出，讲解文字只引用 tex() 输出，绝无心算误差。
常量取初中惯例：g = 10 N/kg，ρ_水 = 1.0×10³ kg/m³，1 帕 = 1 牛/米²。

覆盖（v1，8 个题型）：
 1. lever        —— 杠杆平衡条件 F1·L1 = F2·L2（动力/动力臂/阻力/阻力臂）
 2. pressure     —— 固体压强 p = F/S（单位换算 cm²→m²，柱体放海绵）
 3. buoyancy     —— 阿基米德原理 F浮 = ρ液·g·V排 + 称重法 F浮 = G − F示
 4. pulley       —— 滑轮组 F = (G物 + G动)/n，s = n·h，η = W有/W总
 5. ohm_law      —— 欧姆定律 I = U/R（电路三读数联动）
 6. series_circ  —— 串联：R总 = R1+R2，I 同，U 按电阻分配
 7. parallel_circ—— 并联：1/R总 = 1/R1+1/R2，U 同，I 按电阻反比分配
 8. elec_power   —— 电功率 P = UI = I²R 与焦耳定律 Q = I²Rt

依赖: sympy。自检：python phys_kernel.py
"""

import sympy as sp

# 常量（初中惯例，精确有理数）
G_ACC = sp.Integer(10)                      # g = 10 N/kg
RHO_WATER = sp.Integer(1000)                # ρ_水 = 1.0×10³ kg/m³

x = sp.Symbol("x", positive=True)


# ---------------- 通用工具 ----------------
def tex(expr):
    return sp.latex(sp.nsimplify(sp.simplify(expr), rational=True))


def f(expr):
    return float(sp.N(expr))


def sci(expr, digits=2):
    """科学计数法的 latex，如 2×10³（浮力/压强大数用）。"""
    expr = sp.nsimplify(sp.simplify(expr), rational=True)
    m, e = sp.mantissa_exponent(sp.nsimplify(expr))
    if e == 0:
        return sp.latex(sp.Rational(m).limit_denominator(10**6))
    return f"{sp.latex(sp.Rational(m).limit_denominator(10**6))}\\times10^{{{e}}}"


# ==================== 力学 ====================
def solve_lever(F1=None, L1=None, F2=None, L2=None):
    """杠杆平衡 F1·L1 = F2·L2，四量缺一求一。缺的那个用 sp.solve 反解。

    返回全部四量 + 平衡判定 + 二力的方向提示（初中默认水平杠杆、力竖直）。
    """
    syms = {k: sp.Symbol(k, positive=True) for k in ("F1", "L1", "F2", "L2")}
    given = {"F1": F1, "L1": L1, "F2": F2, "L2": L2}
    missing = [k for k, v in given.items() if v is None]
    assert len(missing) == 1, "杠杆四量必须恰好缺一个（缺 %d 个）" % len(missing)
    eq = sp.Eq(syms["F1"] * syms["L1"], syms["F2"] * syms["L2"])
    subs = {syms[k]: sp.nsimplify(sp.sympify(v)) for k, v in given.items() if v is not None}
    sol = sp.solve(eq.subs(subs), syms[missing[0]], dict=True)[0]
    out = dict(subs)
    out[syms[missing[0]]] = sp.simplify(sol[syms[missing[0]]])
    res = {k: sp.simplify(out[syms[k]]) for k in ("F1", "L1", "F2", "L2")}
    prod_l = sp.simplify(res["F1"] * res["L1"])
    prod_r = sp.simplify(res["F2"] * res["L2"])
    assert sp.simplify(prod_l - prod_r) == 0, "杠杆左右乘积必须相等"
    res.update({"solved": missing[0], "prod_left": prod_l, "prod_right": prod_r})
    return res


def solve_pressure(F=None, S=None, p=None, S_unit="m2"):
    """固体压强 p = F/S。S 可用 cm² 给（S_unit='cm2'，自动换算 m²）。

    返回 {F, S, p, S_cm2}，断言单位一致。
    """
    assert sum(v is not None for v in (F, S, p)) == 2, "压强三量须恰好给两个"
    if S is not None and S_unit == "cm2":
        S_m2 = sp.nsimplify(sp.sympify(S)) / 10000
    elif S is not None:
        S_m2 = sp.nsimplify(sp.sympify(S))
    else:
        S_m2 = None
    if p is None:
        res_p = sp.simplify(sp.nsimplify(sp.sympify(F)) / S_m2)
        res = {"F": sp.nsimplify(sp.sympify(F)), "S": S_m2, "p": res_p}
    elif S_m2 is None:
        S_m2 = sp.simplify(sp.nsimplify(sp.sympify(F)) / sp.nsimplify(sp.sympify(p)))
        res = {"F": sp.nsimplify(sp.sympify(F)), "S": S_m2, "p": sp.nsimplify(sp.sympify(p))}
    else:
        res = {"F": sp.nsimplify(sp.sympify(F)), "S": S_m2,
               "p": sp.nsimplify(sp.sympify(p))}
    res["S_cm2"] = sp.simplify(res["S"] * 10000)
    assert sp.simplify(res["F"] / res["S"] - res["p"]) == 0, "p=F/S 校验失败"
    return res


def solve_buoyancy(rho=None, V=None, G=None, F_scale=None):
    """浮力：阿基米德 F浮 = ρ液·g·V排；称重法 F浮 = G − F示。

    两种模式：
    - 给 rho、V → 算 F浮（排开液体法）
    - 给 G、F_scale → 算 F浮（称重法），并可与 V 互验。
    返回 {F_buoy, mode, ...}。
    """
    if rho is not None and V is not None:
        rho_ = sp.nsimplify(sp.sympify(rho))
        V_ = sp.nsimplify(sp.sympify(V))
        Fb = sp.simplify(rho_ * G_ACC * V_)
        out = {"mode": "排水法", "rho": rho_, "V": V_, "F_buoy": Fb,
               "G_displaced": Fb}
        if G is not None:
            G_ = sp.nsimplify(sp.sympify(G))
            out["G"] = G_
            out["F_scale"] = sp.simplify(G_ - Fb)
            assert sp.simplify(out["G"] - out["F_scale"] - out["F_buoy"]) == 0
        return out
    if G is not None and F_scale is not None:
        G_ = sp.nsimplify(sp.sympify(G))
        Fs_ = sp.nsimplify(sp.sympify(F_scale))
        Fb = sp.simplify(G_ - Fs_)
        out = {"mode": "称重法", "G": G_, "F_scale": Fs_, "F_buoy": Fb}
        if V is not None:
            V_ = sp.nsimplify(sp.sympify(V))
            out["V"] = V_
            out["rho"] = sp.simplify(Fb / (G_ACC * V_))
        return out
    raise AssertionError("浮力需给 (rho,V) 或 (G,F_scale)")


def solve_pulley(G_obj=None, G_moving=None, F=None, n=None, h=None, eta=None):
    """滑轮组：F = (G物 + G动)/n（理想绳重不计），s = n·h，
    W有 = G物·h，W总 = F·s，η = W有/W总。

    缺 F 或 η 时反解；n、h 必给。返回全部中间量供分步展示。
    """
    assert n is not None and h is not None, "滑轮组必须给段数 n 与提升高度 h"
    n_ = sp.nsimplify(sp.sympify(n))
    h_ = sp.nsimplify(sp.sympify(h))
    if F is None:
        Go = sp.nsimplify(sp.sympify(G_obj))
        Gm = sp.nsimplify(sp.sympify(G_moving)) if G_moving is not None else sp.Integer(0)
        F_ = sp.simplify((Go + Gm) / n_)
    else:
        F_ = sp.nsimplify(sp.sympify(F))
    s = sp.simplify(n_ * h_)
    if G_obj is None:
        Go = sp.simplify(F_ * n_ - (sp.nsimplify(sp.sympify(G_moving)) if G_moving is not None else 0))
    else:
        Go = sp.nsimplify(sp.sympify(G_obj))
    W_use = sp.simplify(Go * h_)                       # 有用功
    W_total = sp.simplify(F_ * s)                      # 总功
    W_extra = sp.simplify(W_total - W_use)             # 额外功（动滑轮+摩擦）
    eff = sp.simplify(W_use / W_total)                 # 机械效率
    if eta is not None:                                # 校验题给的 η
        assert sp.simplify(eff - sp.nsimplify(sp.sympify(eta))) == 0, "η 校验失败"
    assert sp.simplify(W_use + W_extra - W_total) == 0
    return {"n": n_, "h": h_, "s": s, "G_obj": Go,
            "G_moving": (sp.nsimplify(sp.sympify(G_moving)) if G_moving is not None else sp.Integer(0)),
            "F": F_, "W_use": W_use, "W_total": W_total, "W_extra": W_extra, "eta": eff}


# ==================== 电学 ====================
def solve_ohm(U=None, I=None, R=None):
    """欧姆定律 I = U/R（U 伏、I 安、R 欧），三量缺一求一。"""
    assert sum(v is not None for v in (U, I, R)) == 2, "欧姆三量须恰好给两个"
    if R is None:
        U_, I_ = sp.nsimplify(sp.sympify(U)), sp.nsimplify(sp.sympify(I))
        R_ = sp.simplify(U_ / I_)
    elif I is None:
        U_, R_ = sp.nsimplify(sp.sympify(U)), sp.nsimplify(sp.sympify(R))
        I_ = sp.simplify(U_ / R_)
    else:
        I_, R_ = sp.nsimplify(sp.sympify(I)), sp.nsimplify(sp.sympify(R))
        U_ = sp.simplify(I_ * R_)
    assert sp.simplify(I_ * R_ - U_) == 0
    return {"U": U_, "I": I_, "R": R_}


def solve_series(R1, R2, U=None, I=None):
    """串联：R总=R1+R2，电流处处相等，U 按电阻正比分配。

    给 U 或 I 之一，返回 U1/U2/I1/I2/R_total/P1/P2。
    """
    R1_, R2_ = sp.nsimplify(sp.sympify(R1)), sp.nsimplify(sp.sympify(R2))
    Rt = sp.simplify(R1_ + R2_)
    assert U is not None or I is not None, "串联须给总电压或总电流"
    if I is None:
        U_ = sp.nsimplify(sp.sympify(U))
        I_ = sp.simplify(U_ / Rt)
    else:
        I_ = sp.nsimplify(sp.sympify(I))
        U_ = sp.simplify(I_ * Rt)
    U1 = sp.simplify(I_ * R1_)
    U2 = sp.simplify(I_ * R2_)
    assert sp.simplify(U1 + U2 - U_) == 0
    P1, P2 = sp.simplify(U1 * I_), sp.simplify(U2 * I_)
    return {"R1": R1_, "R2": R2_, "R_total": Rt, "U": U_, "I": I_,
            "U1": U1, "U2": U2, "I1": I_, "I2": I_,
            "P1": P1, "P2": P2, "P_total": sp.simplify(P1 + P2),
            "U_ratio": sp.simplify(U1 / U2)}


def solve_parallel(R1, R2, U=None, I_total=None):
    """并联：1/R总=1/R1+1/R2，各支路电压相等，I 按电阻反比分配。

    给总电压或总电流，返回 I1/I2/U1/U2/R_total/各功率。
    """
    R1_, R2_ = sp.nsimplify(sp.sympify(R1)), sp.nsimplify(sp.sympify(R2))
    Rt = sp.simplify(R1_ * R2_ / (R1_ + R2_))
    assert U is not None or I_total is not None, "并联须给总电压或总电流"
    if U is None:
        I_ = sp.nsimplify(sp.sympify(I_total))
        U_ = sp.simplify(I_ * Rt)
    else:
        U_ = sp.nsimplify(sp.sympify(U))
        I_ = None
    I1 = sp.simplify(U_ / R1_)
    I2 = sp.simplify(U_ / R2_)
    I_tot = sp.simplify(I1 + I2)
    assert sp.simplify(I1 / I2 - R2_ / R1_) == 0, "并联电流应与电阻成反比"
    P1, P2 = sp.simplify(U_ * I1), sp.simplify(U_ * I2)
    return {"R1": R1_, "R2": R2_, "R_total": Rt, "U": U_,
            "I1": I1, "I2": I2, "I_total": I_tot,
            "U1": U_, "U2": U_, "P1": P1, "P2": P2,
            "P_total": sp.simplify(P1 + P2),
            "I_ratio": sp.simplify(I1 / I2)}


def solve_elec_power(U=None, I=None, R=None, t=None):
    """电功率 P = UI = I²R = U²/R；电热 Q = I²Rt（纯电阻）。

    三量缺一求一（同欧姆），给时间则附 Q。返回 P、Q（若给 t）。
    """
    base = solve_ohm(U=U, I=I, R=R)
    P = sp.simplify(base["U"] * base["I"])
    assert sp.simplify(P - base["I"] ** 2 * base["R"]) == 0
    assert sp.simplify(P - base["U"] ** 2 / base["R"]) == 0
    out = dict(base)
    out["P"] = P
    if t is not None:
        t_ = sp.nsimplify(sp.sympify(t))
        out["t"] = t_
        out["W"] = sp.simplify(P * t_)                 # 电功 W = UIt
        out["Q"] = sp.simplify(base["I"] ** 2 * base["R"] * t_)   # 焦耳定律
        assert sp.simplify(out["Q"] - out["W"]) == 0, "纯电阻 Q=W"
    return out


# ==================== 自检 ====================
if __name__ == "__main__":
    print("== 1. 杠杆：撬棒 L1=1.5, L2=0.06, G=600 → F ==")
    s = solve_lever(L1=sp.Rational(3, 2), L2=sp.Rational(6, 100), F2=600)
    print("  F1 =", tex(s["F1"]), "N；乘积 =", tex(s["prod_left"]), "=", tex(s["prod_right"]))
    assert s["F1"] == 24 and s["prod_left"] == s["prod_right"]

    print("== 2. 压强：F=12N, S=50cm² → p ==")
    s = solve_pressure(F=12, S=50, S_unit="cm2")
    print("  p =", tex(s["p"]), "Pa；S =", tex(s["S"]), "m²")
    assert s["S"] == sp.Rational(1, 200) and s["p"] == 2400

    print("== 3. 浮力：ρ水=1000, V排=2e-4 → F浮；称重法 G=4, F示=2 ==")
    s = solve_buoyancy(rho=1000, V=sp.Rational(2, 10000), G=4, F_scale=2)
    print("  F浮 =", tex(s["F_buoy"]), "N；F示 =", tex(s["F_scale"]), "N")
    assert s["F_buoy"] == 2 and s["F_scale"] == 2

    print("== 4. 滑轮组：G物=400N, G动=100N, n=2, h=1 → F, s, η ==")
    s = solve_pulley(G_obj=400, G_moving=100, n=2, h=1)
    print("  F =", tex(s["F"]), "N；s =", tex(s["s"]), "m；η =", tex(s["eta"]))
    assert s["F"] == 250 and s["s"] == 2 and s["eta"] == sp.Rational(4, 5)

    print("== 5. 欧姆：U=6V, R=10Ω → I ==")
    s = solve_ohm(U=6, R=10)
    print("  I =", tex(s["I"]), "A")
    assert s["I"] == sp.Rational(3, 5)

    print("== 6. 串联：R1=5, R2=10, U=12 → U1, U2 ==")
    s = solve_series(R1=5, R2=10, U=12)
    print("  I =", tex(s["I"]), "A；U1 =", tex(s["U1"]), "V；U2 =", tex(s["U2"]), "V")
    assert s["U1"] == 4 and s["U2"] == 8 and s["U1"] + s["U2"] == 12

    print("== 7. 并联：R1=6, R2=3, U=6 → I1, I2 ==")
    s = solve_parallel(R1=6, R2=3, U=6)
    print("  I1 =", tex(s["I1"]), "A；I2 =", tex(s["I2"]), "A；I总 =", tex(s["I_total"]), "A")
    assert s["I1"] == 1 and s["I2"] == 2 and s["I_total"] == 3

    print("== 8. 电功率/焦耳：U=6V, R=10Ω, t=100s → P, Q ==")
    s = solve_elec_power(U=6, R=10, t=100)
    print("  P =", tex(s["P"]), "W；Q =", tex(s["Q"]), "J")
    assert s["P"] == sp.Rational(18, 5) and s["Q"] == 360

    print("\n全部自检通过")
