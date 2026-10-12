#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seq_kernel.py — 高中数学·数列与三角 的 sympy 精确计算核心（单一数据源）。

覆盖 8 个题型：
  arithmetic    等差数列（已知两项求 a1/d/通项/前n项和）
  geometric     等比数列（求 q/通项/前n项和）
  telescope     裂项相消求和 1/(k(k+1)) = n/(n+1) → 1
  offset_sum    错位相减求和  k·2^(k-1) = 1+(n-1)·2^n
  recurrence    递推数列 a_{n+1}=2a_n+1 → a_n = 2^n−1
  sin_wave      y = A sin(ωx+φ)（周期/最值点/零点/单调区间）
  sas_triangle  余弦定理（两边一夹角）
  identity      三角恒等式 sin(θ+60°)+sin(θ−60°) ≡ sinθ

运行自检：
    python lib/seq_kernel.py
"""

import sympy as sp

# ---- 通用符号 ----
K = sp.Symbol('k', integer=True, positive=True)   # 求和哑变量
N = sp.Symbol('N', integer=True, positive=True)   # 项数
U = sp.Symbol('u', integer=True, positive=True)   # 通项下标
TH = sp.Symbol('theta', real=True)                # 任意角


def tex(expr):
    """sympy 表达式 → LaTeX 字符串。"""
    try:
        return sp.latex(sp.nsimplify(sp.sympify(expr)))
    except Exception:
        return str(expr)


def f(expr):
    """sympy 表达式 → float。"""
    return float(sp.N(sp.sympify(expr)))


def _num(v):
    """任意输入 → sympy 精确数。"""
    return sp.nsimplify(sp.sympify(v))


# =====================================================================
# 1) 等差数列
# =====================================================================
def solve_arithmetic(terms=None, a1=None, d=None):
    """已知若干条件求 a1、d、通项 a(u)、前 N 项和 S(N)。

    terms: dict {下标: 项值}，如 {5:14, 10:29}
    a1/d : 也可直接给定（与 terms 任意组合，需能唯一确定两个未知数）
    """
    a1s, ds = sp.symbols('a1 d')
    eqs = []
    for idx, val in (terms or {}).items():
        eqs.append(sp.Eq(a1s + (idx - 1) * ds, _num(val)))
    if a1 is not None:
        eqs.append(sp.Eq(a1s, _num(a1)))
    if d is not None:
        eqs.append(sp.Eq(ds, _num(d)))
    sol = sp.solve(eqs, [a1s, ds], dict=True)[0]
    a1v, dv = sol[a1s], sol[ds]
    an = a1v + (U - 1) * dv
    Sn = sp.simplify(N / 2 * (2 * a1v + (N - 1) * dv))
    return {
        "a1": sp.simplify(a1v), "d": sp.simplify(dv),
        "an": sp.simplify(an), "Sn": Sn,
        "type": "arithmetic",
    }


# =====================================================================
# 2) 等比数列
# =====================================================================
def solve_geometric(a1, q, n=None):
    a1v, qv = _num(a1), _num(q)
    if qv == 1:
        an = a1v * U
        Sn = a1v * N
    else:
        an = sp.simplify(a1v * qv ** (U - 1))
        Sn = sp.simplify(a1v * (1 - qv ** N) / (1 - qv))
    out = {"a1": a1v, "q": qv, "an": an, "Sn": Sn, "type": "geometric"}
    if n is not None:
        out["term_n"] = sp.simplify(an.subs(U, _num(n)))
        out["S_n"] = sp.simplify(Sn.subs(N, _num(n)))
    return out


# =====================================================================
# 3) 裂项相消： 1/(k(k+1)) = 1/k − 1/(k+1)
# =====================================================================
def solve_telescope():
    term = 1 / (K * (K + 1))
    partial = sp.simplify(sp.summation(term, (K, 1, N)))      # N/(N+1)
    limit = sp.limit(partial, N, sp.oo)                        # 1
    # 裂项式（用于讲解）
    assert sp.simplify(term - (1 / K - 1 / (K + 1))) == 0
    assert sp.simplify(partial - N / (N + 1)) == 0
    # 数值抽验
    for nv in (1, 5, 10):
        direct = sp.Add(*[term.subs(K, i) for i in range(1, nv + 1)])
        assert sp.simplify(direct - partial.subs(N, nv)) == 0
    return {"term": sp.simplify(term), "partial": partial, "limit": limit,
            "type": "telescope"}


# =====================================================================
# 4) 错位相减： sum k·2^(k-1) = 1 + (n−1)·2^n
# =====================================================================
def solve_offset_sum(q=2):
    qv = _num(q)
    term = K * qv ** (K - 1)
    partial = sp.simplify(sp.summation(term, (K, 1, N)))
    # 与闭式 1+(N-1)q^N（q=2）/ 通用闭式 (1-(N+1)q^N+Nq^{N+1})/(1-q)^2 对照
    closed = sp.simplify((1 - (N + 1) * qv ** N + N * qv ** (N + 1)) / (1 - qv) ** 2)
    assert sp.simplify(partial - closed) == 0
    for nv in (1, 4, 6):
        direct = sp.Add(*[term.subs(K, i) for i in range(1, nv + 1)])
        assert sp.simplify(direct - partial.subs(N, nv)) == 0
    return {"term": sp.simplify(term), "partial": partial, "closed": closed,
            "q": qv, "type": "offset_sum"}


# =====================================================================
# 5) 递推数列 a_{n+1} = p·a_n + q0  →  构造等比
# =====================================================================
def solve_recurrence(p, q0, a1):
    pv, qv, a1v = _num(p), _num(q0), _num(a1)
    if pv == 1:
        raise ValueError("p=1 时为等差型，不在本题型范围")
    c = sp.simplify(qv / (1 - pv))                  # 不动点：c = q/(1−p)，b_n = a_n − c
    an = sp.simplify(c + (a1v - c) * pv ** (U - 1))
    # 自检：满足递推
    u2 = sp.Symbol('u2', integer=True, positive=True)
    assert sp.simplify(an.subs(U, u2 + 1) - (pv * an.subs(U, u2) + qv)) == 0
    assert sp.simplify(an.subs(U, 1) - a1v) == 0
    return {"p": pv, "q0": qv, "a1": a1v, "c": c, "ratio": pv,
            "an": an, "type": "recurrence"}


# =====================================================================
# 6) y = A sin(ωx + φ)
# =====================================================================
def solve_sin_wave(A, omega, phi):
    """phi 单位：弧度。返回周期、最值点（k=0 附近）、零点、单调递增区间。"""
    Av, wv, phv = _num(A), _num(omega), _num(phi)
    assert wv != 0
    T = sp.simplify(2 * sp.pi / abs(wv))
    # 最值点： ωx+φ = π/2 + 2kπ（最大）/ −π/2+2kπ（最小）
    x_max = sp.simplify((sp.pi / 2 - phv) / wv)
    x_min = sp.simplify((-sp.pi / 2 - phv) / wv)
    # 零点： ωx+φ = kπ
    x_zero0 = sp.simplify(-phv / wv)             # k=0 零点
    x_zero1 = sp.simplify((sp.pi - phv) / wv)    # k=1 零点
    # 单调递增区间（k=0）： ωx+φ ∈ [−π/2, π/2]
    inc_lo = sp.simplify((-sp.pi / 2 - phv) / wv)
    inc_hi = sp.simplify((sp.pi / 2 - phv) / wv)
    # 自检：最值点处函数值 = ±A
    xs = sp.Symbol('x', real=True)
    y = Av * sp.sin(wv * xs + phv)
    assert sp.simplify(y.subs(xs, x_max) - Av) == 0
    assert sp.simplify(y.subs(xs, x_min) + Av) == 0
    assert sp.simplify(y.subs(xs, x_zero0)) == 0
    return {"A": Av, "omega": wv, "phi": phv, "T": T,
            "x_max": x_max, "x_min": x_min,
            "x_zero0": x_zero0, "x_zero1": x_zero1,
            "inc": (inc_lo, inc_hi),
            "y_expr": y, "type": "sin_wave"}


# =====================================================================
# 7) 余弦定理解三角形（SAS：两边 b、c 及夹角 A）
# =====================================================================
def solve_sas(b, c, A_deg):
    bv, cv = _num(b), _num(c)
    Av = _num(A_deg) * sp.pi / 180
    a2 = sp.simplify(bv ** 2 + cv ** 2 - 2 * bv * cv * sp.cos(Av))
    a = sp.simplify(sp.sqrt(a2))
    B = sp.simplify(sp.acos((a2 + cv ** 2 - bv ** 2) / (2 * a * cv)))
    C = sp.simplify(sp.pi / 2 * 0 + (sp.pi - Av - B))   # 保持精确
    C = sp.simplify(sp.pi - Av - B)
    area = sp.simplify(sp.Rational(1, 2) * bv * cv * sp.sin(Av))
    R = sp.simplify(a / (2 * sp.sin(Av)))                # 外接圆半径
    # 自检：余弦定理与正弦定理
    assert sp.simplify(a2 - (bv ** 2 + cv ** 2 - 2 * bv * cv * sp.cos(Av))) == 0
    assert sp.simplify(a / sp.sin(Av) - bv / sp.sin(B) - 0) or True
    assert sp.simplify(a / sp.sin(Av) - bv / sp.sin(B)) == 0
    assert sp.simplify(a / sp.sin(Av) - cv / sp.sin(C)) == 0
    return {"a": a, "b": bv, "c": cv,
            "A": Av, "B": B, "C": C,
            "area": area, "R": R,
            "A_deg": _num(A_deg),
            "B_deg": sp.simplify(B * 180 / sp.pi),
            "C_deg": sp.simplify(C * 180 / sp.pi),
            "type": "sas_triangle"}


# =====================================================================
# 8) 三角恒等式  sin(θ+60°)+sin(θ−60°) ≡ sinθ
# =====================================================================
def solve_identity():
    lhs = sp.sin(TH + sp.pi / 3) + sp.sin(TH - sp.pi / 3)
    rhs = sp.sin(TH)
    assert sp.simplify(lhs - rhs) == 0          # 符号验证恒等
    # 和差化积推导的中间量
    ident = sp.trigsimp(sp.expand_trig(lhs))
    return {"lhs": sp.simplify(lhs), "rhs": rhs,
            "lhs_expanded": ident,
            "shift": sp.pi / 3,
            "type": "identity"}


# =====================================================================
# 自检
# =====================================================================
def _selfcheck():
    # 1) 等差： a5=14, a10=29 → a1=2, d=3, a_n=3n−1, S10=155
    s = solve_arithmetic(terms={5: 14, 10: 29})
    assert s["a1"] == 2 and s["d"] == 3
    assert s["an"].subs(U, 7) == 20
    assert s["Sn"].subs(N, 10) == 155

    # 2) 等比： a1=3, q=2, S5=93, a5=48
    g = solve_geometric(3, 2, n=5)
    assert g["q"] == 2 and g["S_n"] == 93 and g["term_n"] == 48

    # 3) 裂项： S10=10/11, 极限 1
    t = solve_telescope()
    assert t["partial"].subs(N, 10) == sp.Rational(10, 11)
    assert t["limit"] == 1

    # 4) 错位相减： q=2, S4=49, 闭式 1+(N−1)2^N
    o = solve_offset_sum(2)
    assert o["partial"].subs(N, 4) == 49
    assert sp.simplify(o["partial"] - (1 + (N - 1) * 2 ** N)) == 0

    # 5) 递推： a_{n+1}=2a_n+1, a1=1 → a_n=2^n−1, a5=31
    r = solve_recurrence(2, 1, 1)
    assert r["an"] == 2 ** U - 1
    assert r["an"].subs(U, 5) == 31

    # 6) y=2sin(3x+π/6): T=2π/3, 最大点 x=π/9 处 y=2
    w = solve_sin_wave(2, 3, sp.pi / 6)
    assert sp.simplify(w["T"] - 2 * sp.pi / 3) == 0
    assert sp.simplify(w["x_max"] - sp.pi / 9) == 0

    # 7) SAS: b=2,c=3,A=60° → a=√7, 面积=3√3/2
    tri = solve_sas(2, 3, 60)
    assert sp.simplify(tri["a"] - sp.sqrt(7)) == 0
    assert sp.simplify(tri["area"] - sp.Rational(3, 3) * sp.sqrt(3) / 2 * 1) == 0 \
        or sp.simplify(tri["area"] - 3 * sp.sqrt(3) / 2) == 0
    assert sp.simplify(tri["area"] - 3 * sp.sqrt(3) / 2) == 0

    # 8) 恒等式已在 solve_identity 内部断言
    solve_identity()

    print("[seq_kernel] self-check OK: 8/8")


if __name__ == "__main__":
    _selfcheck()
