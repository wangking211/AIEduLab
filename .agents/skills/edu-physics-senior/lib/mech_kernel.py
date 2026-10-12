# -*- coding: utf-8 -*-
"""
mech_kernel.py — 高中物理·力学确定性计算核心（sympy 精确运算）。

单一数据源设计：运动学、牛顿定律、传送带、追及相遇、斜面、平抛、动能定理、
圆周运动全部由本模块精确算出，讲解文字只引用 tex() 输出，绝无心算误差。
常量取高中惯例：g = 10 m/s²（题目另有指定时改传参）。

覆盖（v1，8 个题型）：
  1. belt        —— 水平传送带：摩擦加速 a=μg、共速时间、划痕相对位移
  2. chase       —— 追及相遇：匀速 A 追匀加速 B（从静止），最大间距与相遇时刻
  3. incline     —— 竖直上滑斜面：a=g(sinθ+μcosθ)、上滑最大距离、能否下滑
  4. projectile  —— 平抛/斜抛：飞行时间、水平射程、最大高度、落点速度
  5. newton2     —— 牛顿第二定律：水平/斜面滑块 a=F合/m（含摩擦）
  6. work_energy —— 动能定理：W合=ΔEk，末速度与摩擦生热
  7. circular    —— 圆周运动：向心力 mv²/r、周期、临界速度
  8. kinematics  —— 匀变速直线运动 v-t/s-t 读数与位移（图像面积）

依赖: sympy。自检：python mech_kernel.py
"""

import sympy as sp

G_ACC = 10                              # g = 10 m/s²（高中默认）

x = sp.Symbol("x", positive=True)


# ---------------- 通用工具 ----------------
def tex(expr):
    return sp.latex(sp.nsimplify(sp.simplify(expr), rational=True))


def f(expr):
    return float(sp.N(expr))


def js(expr):
    """sympy 表达式 → JS 表达式（画板采样用，去掉 Math. 前缀）。"""
    from sympy.printing.jscode import jscode
    return jscode(sp.nsimplify(sp.nsimplify(expr))).replace("Math.", "")


# ==================== 运动学基础 ====================
def solve_kinematics(v0=None, a=None, t=None, vt=None, s=None):
    """匀变速直线运动四量 v0,a,t,vt,s 缺二求一（s = v0t + at²/2 = (v0+vt)t/2）。

    给出其中任意两个驱动量（如 v0,a,t），返回全部五量；断言自洽。
    """
    vals = {"v0": v0, "a": a, "t": t, "vt": vt, "s": s}
    given = {k: sp.nsimplify(sp.sympify(v)) for k, v in vals.items() if v is not None}
    assert len(given) >= 3, "匀变速运动需至少给 3 个量（v0,a,t 至少其三之二）"
    # 优先用 v0,a,t 推导
    if "v0" in given and "a" in given and "t" in given:
        vt_ = sp.simplify(given["v0"] + given["a"] * given["t"])
        s_ = sp.simplify(given["v0"] * given["t"] + given["a"] * given["t"] ** 2 / 2)
    elif "v0" in given and "a" in given and "vt" in given:
        vt_ = given["vt"]
        t_ = sp.simplify((vt_ - given["v0"]) / given["a"])
        s_ = sp.simplify(given["v0"] * t_ + given["a"] * t_ ** 2 / 2)
    elif "v0" in given and "t" in given and "vt" in given:
        vt_ = given["vt"]
        a_ = sp.simplify((vt_ - given["v0"]) / given["t"])
        s_ = sp.simplify(given["v0"] * given["t"] + a_ * given["t"] ** 2 / 2)
    else:
        raise AssertionError("组合暂不支持：请至少给 v0,a,t 中的两个 + 另一个量")
    if "s" in given:
        assert sp.simplify(given["s"] - s_) == 0, "位移校验失败"
    if "vt" in given:
        assert sp.simplify(vt_ - given["vt"]) == 0, "末速度校验失败"
    return {"v0": given.get("v0", sp.Integer(0)), "a": given.get("a"),
            "t": given.get("t"), "vt": vt_, "s": s_}


# ==================== 1) 传送带 ====================
def solve_belt(v0, vbelt, mu, g=G_ACC):
    """物块以初速 v0 滑上水平传送带（带速 vbelt），μ 已知。

    返回加速度 a=μg（方向由 v0 与 vbelt 关系决定）、共速时间 t1、
    共速前物块位移 x1、带位移 xb1、划痕长 Δs=|xb1-x1|。
    约定：物块相对带滑动时受滑动摩擦，方向使相对速度减小。
    """
    v0_, vb_ = sp.nsimplify(sp.sympify(v0)), sp.nsimplify(sp.sympify(vbelt))
    mu_ = sp.nsimplify(sp.sympify(mu))
    a = sp.simplify(mu_ * g)                       # 加速度大小
    dv = sp.simplify(vb_ - v0_)
    if dv == 0:
        t1 = sp.Integer(0)
    else:
        t1 = sp.simplify(dv / (a * sp.sign(dv)))   # |v0-vb|/a
        t1 = sp.simplify(abs(v0_ - vb_) / a)
    x1 = sp.simplify(v0_ * t1 + sp.sign(vb_ - v0_) * a * t1 ** 2 / 2)   # 物块位移
    xb1 = sp.simplify(vb_ * t1)                                       # 带位移
    delta_x = sp.simplify(xb1 - x1)                    # 相对位移（带 − 物，带符号）
    scratch = sp.simplify(abs(delta_x))                # 划痕长 = |相对位移|
    # 共速后：若无动力且 μ 足够，随带匀速（高中默认带水平、足够长）
    assert t1 >= 0, "共速时间应非负"
    return {"a": a, "t1": t1, "x1": x1, "xb1": xb1, "delta_x": delta_x,
            "scratch": scratch,
            "same_dir": bool(sp.sign(v0_) == sp.sign(vb_)) if v0_ != 0 else True,
            "v0": v0_, "vb": vb_, "mu": mu_}


# ==================== 2) 追及相遇 ====================
def solve_chase(xA0, vA, xB0, aB, g=G_ACC):
    """A 以速度 vA 匀速从 xA0 出发；B 从 xB0 由静止以 aB 匀加速。

    返回：速度相等时刻 t1（最大间距）、最大间距 Δx_max、
    相遇时刻 t_meet（二次方程正根，可能不存在）、相遇前 A 的位移。
    """
    xA0_, xB0_ = sp.nsimplify(sp.sympify(xA0)), sp.nsimplify(sp.sympify(xB0))
    vA_, aB_ = sp.nsimplify(sp.sympify(vA)), sp.nsimplify(sp.sympify(aB))
    # xA(t) = xA0 + vA t；xB(t) = xB0 + aB t²/2
    # 间距 d(t) = xA - xB = (xA0-xB0) + vA t - aB t²/2
    d = sp.Symbol("d")
    t1 = sp.simplify(vA_ / aB_)                       # vA = aB t → 间距极值
    d_max = sp.simplify((xA0_ - xB0_) + vA_ * t1 - aB_ * t1 ** 2 / 2)
    # 相遇：aB t²/2 - vA t + (xB0-xA0) = 0
    A, B, C = aB_ / 2, -vA_, (xB0_ - xA0_)
    disc = sp.simplify(B ** 2 - 4 * A * C)
    if disc < 0:
        t_meet = None
    else:
        r = sp.sqrt(disc)
        roots = [sp.simplify((-B + r) / (2 * A)), sp.simplify((-B - r) / (2 * A))]
        pos = [rt for rt in roots if rt > 0]
        t_meet = min(pos) if pos else None
    # 极值类型：d'' = -aB < 0（aB>0）→ t1 处最大
    return {"t1": t1, "d_max": d_max, "t_meet": t_meet, "disc": disc,
            "xA0": xA0_, "vA": vA_, "xB0": xB0_, "aB": aB_}


# ==================== 3) 斜面上滑 ====================
def solve_incline(theta, v0, mu, g=G_ACC):
    """物块以 v0 沿倾角 θ 斜面上滑，动摩擦因数 μ。

    上滑：a1 = g(sinθ + μcosθ)（减速）；最大距离 s = v0²/(2a1)；
    下滑条件：tanθ > μ（重力下滑分量大于最大静摩擦）→ a2 = g(sinθ − μcosθ)。
    """
    th_ = sp.nsimplify(sp.sympify(theta)) * sp.pi / 180
    v0_, mu_ = sp.nsimplify(sp.sympify(v0)), sp.nsimplify(sp.sympify(mu))
    sin, cos = sp.sin(th_), sp.cos(th_)
    a1 = sp.simplify(g * (sin + mu_ * cos))          # 上滑减速大小
    a2 = sp.simplify(g * (sin - mu_ * cos))          # 下滑加速大小（可能 ≤0）
    s_max = sp.simplify(v0_ ** 2 / (2 * a1))
    t_up = sp.simplify(v0_ / a1)
    can_down = bool(sp.simplify(mu_ - sin / cos) < 0)   # tanθ > μ
    return {"theta": th_, "theta_deg": sp.nsimplify(sp.sympify(theta)),
            "a_up": a1, "a_down": a2, "s_max": s_max, "t_up": t_up,
            "can_down": can_down, "v0": v0_, "mu": mu_,
            "g_over": sp.simplify(mu_ * cos - sin)}    # <0 才下滑


# ==================== 4) 抛体运动 ====================
def solve_projectile(v0, theta_deg=0, g=G_ACC, h0=0):
    """斜抛（theta=0 为平抛）：从高度 h0 以 v0、仰角 θ 抛出。

    返回飞行时间 t、水平射程 R、最大高度 H（相对抛出点）、
    落地速度大小 v_land 与落地速度与水平夹角。
    """
    v0_ = sp.nsimplify(sp.sympify(v0))
    th_ = sp.nsimplify(sp.sympify(theta_deg)) * sp.pi / 180
    h0_ = sp.nsimplify(sp.sympify(h0))
    vx = sp.simplify(v0_ * sp.cos(th_))
    vy = sp.simplify(v0_ * sp.sin(th_))
    # h0 + vy t − g t²/2 = 0
    A, B, C = -sp.sympify(g) / 2, vy, h0_
    disc = sp.simplify(B ** 2 - 4 * A * C)
    t = sp.simplify((-B - sp.sqrt(disc)) / (2 * A))    # 正根
    R = sp.simplify(vx * t)
    t_peak = sp.simplify(vy / g) if vy != 0 else sp.Integer(0)
    H = sp.simplify(vy ** 2 / (2 * g)) + h0_           # 相对地面最高点
    v_land = sp.simplify(sp.sqrt(vx ** 2 + (vy - g * t) ** 2))
    alpha = sp.simplify(sp.atan((g * t - vy) / vx) * 180 / sp.pi) if vx != 0 else sp.pi / 2
    return {"t": t, "R": R, "H": H, "H_rel": sp.simplify(vy ** 2 / (2 * g)),
            "t_peak": t_peak, "vx": vx, "vy": vy, "v_land": v_land,
            "alpha_deg": alpha, "v0": v0_, "theta_deg": sp.nsimplify(sp.sympify(theta_deg)),
            "h0": h0_}


# ==================== 5) 牛顿第二定律 ====================
def solve_newton2(m, F=None, mu=None, theta_deg=None, g=G_ACC, a=None):
    """水平面（theta=None）或斜面（theta_deg 给定）滑块。

    - 水平：a = (F − μmg)/m（F 水平拉力；F=None 时 a = −μg 或 0）
    - 斜面：a = g(sinθ ± μcosθ)（F 沿斜面时 (F + ∓mg sinθ − μN)/m）
    给 F/m/μ/θ 求 a；或给 a 反求 F。返回 F合、a、支持力 N、摩擦力 f。
    """
    m_ = sp.nsimplify(sp.sympify(m))
    if theta_deg is None:                              # 水平
        N = sp.simplify(m_ * g)
        if mu is not None:
            mu_ = sp.nsimplify(sp.sympify(mu))
            fric = sp.simplify(mu_ * N)
        else:
            fric = sp.Integer(0)
        if F is not None:
            F_ = sp.nsimplify(sp.sympify(F))
            F_net = sp.simplify(F_ - fric)
        elif a is not None:
            a_ = sp.nsimplify(sp.sympify(a))
            F_net = sp.simplify(m_ * a_)
            F_ = sp.simplify(F_net + fric)
        else:
            F_, F_net = sp.Integer(0), sp.simplify(-fric)
        a_ = sp.simplify(F_net / m_)
        return {"m": m_, "F": F_, "F_net": F_net, "a": a_, "N": N, "f": fric,
                "theta_deg": None}
    # 斜面
    th_ = sp.nsimplify(sp.sympify(theta_deg)) * sp.pi / 180
    mu_ = sp.nsimplify(sp.sympify(mu)) if mu is not None else sp.Integer(0)
    N = sp.simplify(m_ * g * sp.cos(th_))
    fric = sp.simplify(mu_ * N)
    if F is not None:                                   # F 沿斜面向上拉
        F_ = sp.nsimplify(sp.sympify(F))
        F_net = sp.simplify(F_ - m_ * g * sp.sin(th_) - fric)
    else:
        F_ = sp.Integer(0)
        F_net = sp.simplify(-m_ * g * sp.sin(th_) - fric)   # 上滑（减速方向沿斜面向下）
    a_ = sp.simplify(F_net / m_)
    return {"m": m_, "F": F_, "F_net": F_net, "a": a_, "N": N, "f": fric,
            "theta_deg": sp.nsimplify(sp.sympify(theta_deg))}


# ==================== 6) 动能定理 ====================
def solve_work_energy(m, v0, F=None, mu=None, s=None, theta_deg=None, g=G_ACC):
    """动能定理：W合 = ΔEk = m v²/2 − m v0²/2。

    水平恒力 F 拉动位移 s（可含摩擦 μmg）；或斜面（theta_deg）。
    给足参数求末速度 v 与各功分量；断言 W合 = ΔEk。
    """
    m_, v0_ = sp.nsimplify(sp.sympify(m)), sp.nsimplify(sp.sympify(v0))
    if s is None:
        raise AssertionError("需给位移 s")
    s_ = sp.nsimplify(sp.sympify(s))
    if theta_deg is None:
        N = sp.simplify(m_ * g)
        fric = sp.simplify(sp.nsimplify(sp.sympify(mu)) * N) if mu is not None else sp.Integer(0)
        W_F = sp.simplify(sp.nsimplify(sp.sympify(F)) * s_) if F is not None else sp.Integer(0)
        W_fr = sp.simplify(-fric * s_)
        W_G = sp.Integer(0)
    else:
        th_ = sp.nsimplify(sp.sympify(theta_deg)) * sp.pi / 180
        N = sp.simplify(m_ * g * sp.cos(th_))
        fric = sp.simplify(sp.nsimplify(sp.sympify(mu)) * N) if mu is not None else sp.Integer(0)
        W_F = sp.simplify(sp.nsimplify(sp.sympify(F)) * s_) if F is not None else sp.Integer(0)
        W_fr = sp.simplify(-fric * s_)
        W_G = sp.simplify(-m_ * g * sp.sin(th_) * s_)      # 上滑重力做负功
    W_net = sp.simplify(W_F + W_fr + W_G)
    Ek0 = sp.simplify(m_ * v0_ ** 2 / 2)
    Ek1 = sp.simplify(Ek0 + W_net)
    assert Ek1 >= 0, "末动能为负：参数不自洽"
    v = sp.simplify(sp.sqrt(2 * Ek1 / m_))
    assert sp.simplify(W_net - (Ek1 - Ek0)) == 0
    return {"m": m_, "s": s_, "W_F": W_F, "W_fr": W_fr, "W_G": W_G,
            "W_net": W_net, "Ek0": Ek0, "Ek1": Ek1, "v": v,
            "Q": sp.simplify(-W_fr), "v0": v0_}


# ==================== 7) 圆周运动 ====================
def solve_circular(m, r, v=None, T=None, n=None, g=G_ACC):
    """匀速圆周运动：F向 = m v²/r = m ω² r = m (2π/T)² r。

    给 v、T 或转速 n（r/s）之一，返回向心加速度、向心力、周期、角速度。
    另附竖直圆环最高/最低点的临界速度（绳模型 v_top ≥ √(gr)）。
    """
    m_, r_ = sp.nsimplify(sp.sympify(m)), sp.nsimplify(sp.sympify(r))
    if v is not None:
        v_ = sp.nsimplify(sp.sympify(v))
        T_ = sp.simplify(2 * sp.pi * r_ / v_)
    elif T is not None:
        T_ = sp.nsimplify(sp.sympify(T))
        v_ = sp.simplify(2 * sp.pi * r_ / T_)
    elif n is not None:
        n_ = sp.nsimplify(sp.sympify(n))
        T_ = sp.simplify(1 / n_)
        v_ = sp.simplify(2 * sp.pi * r_ / T_)
    else:
        raise AssertionError("需给 v、T 或 n 之一")
    omega = sp.simplify(2 * sp.pi / T_)
    a_c = sp.simplify(v_ ** 2 / r_)
    F_c = sp.simplify(m_ * a_c)
    v_crit = sp.sqrt(g * r_)                            # 绳模型最高点临界
    assert sp.simplify(F_c - m_ * omega ** 2 * r_) == 0
    return {"m": m_, "r": r_, "v": v_, "T": T_, "omega": omega,
            "a_c": a_c, "F_c": F_c, "v_crit": v_crit,
            "F_low": sp.simplify(F_c + m_ * g), "F_high": sp.simplify(F_c - m_ * g)}


# ==================== 自检 ====================
if __name__ == "__main__":
    print("== 1. 传送带：v0=4, 带速=1, μ=0.2 → a, t1, 划痕 ==")
    s = solve_belt(v0=4, vbelt=1, mu=0.2)
    print("  a =", tex(s["a"]), "m/s²；t1 =", tex(s["t1"]), "s；Δs =", tex(s["scratch"]), "m")
    assert s["a"] == 2 and s["t1"] == sp.Rational(3, 2) and s["scratch"] == sp.Rational(9, 4)

    print("== 2. 追及：A 从 0 匀速 8m/s；B 从 10m 静止 a=2 → t1, Δxmax, t相遇 ==")
    s = solve_chase(xA0=0, vA=8, xB0=10, aB=2)
    print("  t1 =", tex(s["t1"]), "s；Δxmax =", tex(s["d_max"]), "m；tmeet =", tex(s["t_meet"]), "s")
    assert s["t1"] == 4 and s["d_max"] == 6
    assert s["t_meet"] is not None and sp.simplify(s["t_meet"] - (4 - sp.sqrt(6))) == 0

    print("== 3. 斜面：θ=30°, v0=6, μ=0.2 → a上, smax, 能否下滑 ==")
    s = solve_incline(theta=30, v0=6, mu=0.2)
    print("  a上 =", tex(s["a_up"]), "m/s²；s =", tex(s["s_max"]), "m；下滑 =", s["can_down"])
    # a上 = g(sin30° + μcos30°) = 10(1/2 + (1/5)(√3/2)) = 5 + √3
    assert sp.simplify(s["a_up"] - (5 + sp.sqrt(3))) == 0
    assert s["can_down"] is True and sp.simplify(s["s_max"] - 18 / (5 + sp.sqrt(3))) == 0

    print("== 4. 平抛：v0=10, θ=0, h0=20 → t, R ==")
    s = solve_projectile(v0=10, theta_deg=0, h0=20)
    print("  t =", tex(s["t"]), "s；R =", tex(s["R"]), "m；v落 =", tex(s["v_land"]), "m/s")
    assert s["t"] == 2 and s["R"] == 20

    print("== 5. 牛二：m=2, F=10, μ=0.1 水平 → a ==")
    s = solve_newton2(m=2, F=10, mu=0.1)
    print("  N =", tex(s["N"]), "N；f =", tex(s["f"]), "N；a =", tex(s["a"]), "m/s²")
    assert s["N"] == 20 and s["f"] == 2 and s["a"] == 4

    print("== 6. 动能定理：m=2, v0=0, F=10, μ=0.1, s=5 → v ==")
    s = solve_work_energy(m=2, v0=0, F=10, mu=0.1, s=5)
    print("  W合 =", tex(s["W_net"]), "J；Ek末 =", tex(s["Ek1"]), "J；v =", tex(s["v"]), "m/s")
    assert s["W_net"] == 40 and s["v"] == sp.sqrt(40)

    print("== 7. 圆周：m=1, r=0.4, v=2 → F向, T ==")
    s = solve_circular(m=1, r=sp.Rational(2, 5), v=2)
    print("  F向 =", tex(s["F_c"]), "N；T =", tex(s["T"]), "s；v临界 =", tex(s["v_crit"]), "m/s")
    assert s["F_c"] == 10 and s["a_c"] == 10

    print("== 8. 匀变速：v0=2, a=2, t=3 → vt, s ==")
    s = solve_kinematics(v0=2, a=2, t=3)
    print("  vt =", tex(s["vt"]), "m/s；s =", tex(s["s"]), "m")
    assert s["vt"] == 8 and s["s"] == 15

    print("\n全部自检通过")
