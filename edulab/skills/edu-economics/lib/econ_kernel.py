#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
econ_kernel.py —— 经济学内核（可算部分）

**本内核的证据力纪律（沿用 edu-history 的做法）**：经济学里「可算」的比例不低，
但「模型」与「预测」是两件完全不同的事。所以每一项都归到三类之一：

  A  纯数学 / 恒等式 —— 图上的数错不了（供需交点、剩余面积、弹性、复利、
     索洛稳态、Cobb–Douglas 恒等式、垄断最优、纳什均衡、基尼系数）
  B  模型：内核确定，**参数靠估** —— 弹性值、储蓄率、边际消费倾向
  C  形态①、证据力③ —— 政策效果预测：参数与因果都不可独立验证

**不做什么**：计量经济学的回归推断（那是统计课）、博弈论的一般理论（要证明）、
经济思想史（叙事）、任何需要真实宏观数据表的内容（那属于 ①B 数据页，
要走出处/许可/指纹一整套）。

覆盖：
  · 线性供需均衡与消费者/生产者剩余（定积分）
  · 需求价格弹性（点弹性与弧弹性）
  · 索洛增长模型的稳态
  · Cobb–Douglas 生产函数：边际产量、规模报酬、欧拉定理
  · 垄断定价：边际收益 = 边际成本
  · 2×2 博弈的纯策略纳什均衡（穷举最优反应）
  · 洛伦兹曲线与基尼系数

自检：python econ_kernel.py
"""

import math

import sympy as sp

__all__ = [
    "tex", "f", "num_str", "pct",
    "EVIDENCE",
    "demand_q", "supply_q", "market_equilibrium",
    "consumer_surplus", "producer_surplus", "total_surplus",
    "point_elasticity", "arc_elasticity", "elasticity_label",
    "solow_steady", "solow_output", "solow_convergence_time",
    "cobb_douglas", "marginal_products", "returns_to_scale", "euler_check",
    "monopoly_optimum", "monopoly_profit", "lerner_index",
    "nash_2x2", "best_responses",
    "lorenz", "gini_from_beta", "gini_from_curve",
]


# =====================================================================
# 证据力分级（每一项都必须归到其中一类）
# =====================================================================
EVIDENCE = {
    "A": ("纯数学 / 恒等式", "由定义或代数必然成立，图上的数错不了"),
    "B": ("模型：内核确定，参数靠估", "结论的形状可靠，具体数值取决于你怎么估参数"),
    "C": ("形态①、证据力③", "能算能画 —— 但参数与因果都不可独立验证，"
                            "它只说明「如果假设成立会怎样」"),
}


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


def pct(x, digits=2):
    return f(float(x) * 100, digits) + "%"


# ---------------------------------------------------------------- 供需与剩余
#
# 线性需求 q = a − b·p（p 在 [0, a/b] 内），线性供给 q = c + d·p。

def demand_q(p, a, b):
    return a - b * p


def supply_q(p, c, d):
    return c + d * p


def market_equilibrium(a, b, c, d):
    """解 a − bp = c + dp，返回 (p*, q*)。

    两条直线相交 —— 纯代数，无参数争议。
    """
    if b + d == 0:
        raise ValueError("需求与供给的斜率之和不能为零")
    p = sp.Rational(a - c, b + d)
    q = sp.simplify(a - b * p)
    if q < 0:
        raise ValueError("均衡产量为负：参数区间不合理")
    return p, q


def consumer_surplus(a, b, p_star):
    """消费者剩余 = 需求曲线在 p* 以上的面积（三角形）= (a−b·p*)²/(2b)。"""
    if b <= 0:
        raise ValueError("需求斜率必须为正")
    return sp.simplify((a - b * sp.nsimplify(p_star)) ** 2 / (2 * b))


def producer_surplus(c, d, p_star):
    """生产者剩余 = 供给曲线在 p* 以下的面积（三角形）= (c+d·p*)²/(2d)。

    供给曲线从 p_min = −c/d（q=0）出发，所以是一个底为 p*−p_min、高为 q* 的三角形。
    """
    if d <= 0:
        raise ValueError("供给斜率必须为正")
    return sp.simplify((c + d * sp.nsimplify(p_star)) ** 2 / (2 * d))


def total_surplus(a, b, c, d):
    """总剩余 = 消费者剩余 + 生产者剩余。"""
    p, q = market_equilibrium(a, b, c, d)
    return sp.simplify(consumer_surplus(a, b, p) + producer_surplus(c, d, p))


# ---------------------------------------------------------------- 弹性
#
# 点弹性 ε = (dq/dp)(p/q)。对 q = a − b·p，dq/dp = −b，故 ε = −b·p/q。

def point_elasticity(p, a, b):
    """需求的价格点弹性（需求价格弹性通常为负）。"""
    q = a - b * p
    if q == 0:
        raise ValueError("需求量不能为零")
    return sp.simplify(-b * sp.nsimplify(p) / q)


def arc_elasticity(p1, q1, p2, q2):
    """弧弹性（中点法）：Δq/Δp · (p̄/q̄)。"""
    if p2 == p1:
        raise ValueError("价格不能相同")
    pbar = (p1 + p2) / 2.0
    qbar = (q1 + q2) / 2.0
    return (q2 - q1) / (p2 - p1) * (pbar / qbar)


def elasticity_label(e):
    """按 |ε| 与 1 的关系给出口语化标签（纯比较，不含估计）。"""
    if abs(e) > 1 + 1e-12:
        return "富有弹性（|ε| > 1）"
    if abs(e) < 1 - 1e-12:
        return "缺乏弹性（|ε| < 1）"
    return "单位弹性（|ε| = 1）"


# ---------------------------------------------------------------- 索洛增长
#
# Cobb–Douglas 情形：y = k^α，稳态 k* = (s/(n+g+δ))^(1/(1−α))。

def solow_steady(s, n, g, delta, alpha):
    """Cobb–Douglas 索洛模型的稳态资本存量 k*。"""
    if not 0 < alpha < 1:
        raise ValueError("α 须在 (0,1) 内")
    denom = n + g + delta
    if denom <= 0 or s <= 0:
        raise ValueError("s 与 (n+g+δ) 必须为正")
    return (s / denom) ** (1.0 / (1.0 - alpha))


def solow_output(s, n, g, delta, alpha):
    """稳态人均产出 y* = (k*)^α。"""
    return solow_steady(s, n, g, delta, alpha) ** alpha


def solow_convergence_time(k0, k_star, s, n, g, delta, alpha):
    """从 k₀ 收敛到 k* 的一半差距所需时间（数值积分 ṫ = sf(k)−(n+g+δ)k）。

    返回 (年数, 是否收敛)。欠发达经济体的「追赶速度」就由它刻画。
    """
    h = 0.05
    k, t = float(k0), 0.0
    target = k_star + (float(k0) - k_star) * 0.5
    for _ in range(200000):
        dk = s * (k ** alpha) - (n + g + delta) * k
        k += h * dk
        t += h
        if k <= 0:
            return None, False
        if abs(k - k_star) <= abs(float(k0) - k_star) * 0.5:
            return t, True
    return None, False


# ---------------------------------------------------------------- Cobb–Douglas

def cobb_douglas(A, K, L, alpha):
    """Y = A·K^α·L^(1−α)。"""
    return A * (K ** alpha) * (L ** (1.0 - alpha))


def marginal_products(A, K, L, alpha):
    """两种要素的边际产量 (MPK, MPL)。"""
    mpk = A * alpha * (K ** (alpha - 1.0)) * (L ** (1.0 - alpha))
    mpl = A * (1.0 - alpha) * (K ** alpha) * (L ** (-alpha))
    return mpk, mpl


def returns_to_scale(alpha):
    """规模报酬：指数之和 = 1 为不变，>1 递增，<1 递减。

    对 Cobb–Douglas，两指数之和恒为 α+(1−α)=1，所以**规模报酬不变**
    —— 这是函数形式的结论，不是估计出来的。
    """
    total = alpha + (1.0 - alpha)
    if abs(total - 1.0) < 1e-12:
        return "规模报酬不变（指数之和 = 1）"
    return "规模报酬递增" if total > 1 else "规模报酬递减"


def euler_check(A, K, L, alpha):
    """欧拉定理：K·MPK + L·MPL = Y（规模报酬不变时成立）。

    返回 (左边, 右边, 相对误差)。这是纯恒等式，可用来校验边际产量算得对不对。
    """
    mpk, mpl = marginal_products(A, K, L, alpha)
    left = K * mpk + L * mpl
    right = cobb_douglas(A, K, L, alpha)
    return left, right, abs(left - right) / max(abs(right), 1e-12)


# ---------------------------------------------------------------- 垄断定价
#
# 线性需求 p = a − b·q，边际成本恒为 MC。

def monopoly_optimum(a, b, mc):
    """垄断最优：MR = a − 2b·q = MC ⇒ q* = (a−MC)/(2b)，p* = (a+MC)/2。"""
    if b <= 0:
        raise ValueError("需求斜率必须为正")
    if mc >= a:
        return sp.Integer(0), sp.nsimplify(mc)
    q = sp.Rational(a - mc, 2 * b)
    p = sp.simplify(a - b * q)
    return q, p


def monopoly_profit(a, b, mc):
    """垄断利润 (p* − MC)·q*。"""
    q, p = monopoly_optimum(a, b, mc)
    return sp.simplify((p - sp.nsimplify(mc)) * q)


def lerner_index(a, b, mc):
    """勒纳指数 (p − MC)/p —— 等于 1/|ε|（垄断定价的弹性形式）。

    返回 (勒纳指数, 1/|ε(p*)|, 两者之差)。这是纯代数恒等式，可交叉验证。
    """
    q, p = monopoly_optimum(a, b, mc)
    if p == 0:
        return None, None, None
    li = sp.simplify((p - sp.nsimplify(mc)) / p)
    e = point_elasticity(p, a, b)
    inv = sp.simplify(1 / sp.Abs(e))
    return li, inv, sp.simplify(li - inv)


# ---------------------------------------------------------------- 2×2 博弈
#
# payoffs[i][j] = (行玩家的收益, 列玩家的收益)

def best_responses(payoffs):
    """返回 (行玩家的最优反应, 列玩家的最优反应)。

    行玩家在列选 j 时选使 payoffs[i][j][0] 最大的 i；
    列玩家在行选 i 时选使 payoffs[i][j][1] 最大的 j。
    """
    n = len(payoffs)
    m = len(payoffs[0])
    row_br = []
    for j in range(m):
        vals = [payoffs[i][j][0] for i in range(n)]
        mx = max(vals)
        row_br.append([i for i in range(n) if abs(vals[i] - mx) < 1e-12])
    col_br = []
    for i in range(n):
        vals = [payoffs[i][j][1] for j in range(m)]
        mx = max(vals)
        col_br.append([j for j in range(m) if abs(vals[j] - mx) < 1e-12])
    return row_br, col_br


def nash_2x2(payoffs):
    """穷举 2×2 的纯策略纳什均衡，返回 [(i, j), ...]。

    判据：双方都在对方策略下用了最优反应 —— 即 i ∈ row_br[j] 且 j ∈ col_br[i]。
    这是有限博弈，穷举即可，**不存在算法争议**。
    """
    row_br, col_br = best_responses(payoffs)
    out = []
    for i in range(len(payoffs)):
        for j in range(len(payoffs[0])):
            if i in row_br[j] and j in col_br[i]:
                out.append((i, j))
    return out


# ---------------------------------------------------------------- 洛伦兹与基尼
#
# 参数化洛伦兹曲线 L(x) = x^β（β ≥ 1）。β=1 是完全平等。

def lorenz(x, beta):
    """洛伦兹曲线：最穷的 x 比例人口占有 L(x) 比例的收入的累积份额。"""
    return x ** beta


def gini_from_beta(beta):
    """基尼系数 = 1 − 2∫₀¹ L(x)dx = 1 − 2/(β+1) = (β−1)/(β+1)。"""
    if beta < 1:
        raise ValueError("β 必须 ≥ 1")
    return (beta - 1.0) / (beta + 1.0)


def gini_from_curve(pts):
    """由洛伦兹曲线的样本点用梯形法算基尼系数（数值，返回 (基尼, 数值积分))。

    pts = [(x, L(x)), ...]，需含 (0,0) 与 (1,1)。
    """
    area = 0.0
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        area += (y0 + y1) / 2.0 * (x1 - x0)
    return 1.0 - 2.0 * area, area


# ================================================================ 自检

def _same(a, b):
    """判断两个值是否相等 —— 标量、字符串、布尔、列表、矩阵都能处理。

    不能直接写 `sympify(a) - sympify(b) == 0`：字符串会被 sympify 报错、
    布尔相减会抛 BooleanAtom、矩阵相减得到的是**矩阵**（与 0 比较得到逐元素布尔）。
    """
    if isinstance(a, str) or isinstance(b, str):
        return str(a) == str(b)
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        a, b = list(a), list(b)
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    a, b = sp.sympify(a), sp.sympify(b)
    if isinstance(a, sp.MatrixBase) or isinstance(b, sp.MatrixBase):
        d = sp.Matrix(a) - sp.Matrix(b)
        return all(sp.simplify(x) == 0 for x in d)
    return sp.simplify(a - b) == 0


def _selftest():
    bad = []

    def chk(name, got, want, tol=None):
        shown = got
        try:
            if isinstance(want, bool) or isinstance(got, bool):
                ok = bool(got) == bool(want)
            elif isinstance(want, str) or isinstance(got, str):
                ok = str(got) == str(want)
            elif isinstance(got, (list, tuple)) or isinstance(want, (list, tuple)):
                ok = _same(got, want)
            elif tol is not None and not isinstance(got, sp.MatrixBase):
                ok = abs(float(got) - float(want)) <= tol
                shown = f"{float(got):.8f}"
            else:
                ok = _same(got, want)
        except Exception as e:                       # noqa: BLE001
            ok, shown = False, f"<{e}>"
        print(f"  {'✓' if ok else '✗'} {name:44s} = {shown}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    print("证据力分级")
    for k in ("A", "B", "C"):
        chk(f"等级 {k} 有定义", k in EVIDENCE, True)

    print("\n供需均衡与剩余")
    p, q = market_equilibrium(10, 2, 2, 2)
    chk("均衡价格", p, sp.Integer(2))
    chk("均衡产量", q, sp.Integer(6))
    chk("消费者剩余", consumer_surplus(10, 2, 2), sp.Rational(9))
    chk("生产者剩余", producer_surplus(2, 2, 2), sp.Rational(9))
    chk("总剩余 = CS + PS", total_surplus(10, 2, 2, 2), sp.Rational(18))
    # 剩余之和对参数单调：需求截距越大，消费者剩余越大
    chk("需求截距变大 → 消费者剩余变大",
        consumer_surplus(12, 2, market_equilibrium(12, 2, 2, 2)[0])
        > consumer_surplus(10, 2, 2), True)
    chk("均衡时需求量 = 供给量", demand_q(p, 10, 2), supply_q(p, 2, 2))

    print("\n需求价格弹性")
    chk("点弹性 ε = −bp/q", point_elasticity(2, 10, 2), sp.Rational(-4, 6))
    chk("价格为 0 时弹性为 0", point_elasticity(0, 10, 2), sp.Integer(0))
    chk("|ε| > 1 → 富有弹性", elasticity_label(-2.0), "富有弹性（|ε| > 1）")
    chk("|ε| < 1 → 缺乏弹性", elasticity_label(-0.5), "缺乏弹性（|ε| < 1）")
    chk("|ε| = 1 → 单位弹性", elasticity_label(-1.0), "单位弹性（|ε| = 1）")
    # 线性需求上，弹性随价格上升而变大（绝对值）
    e1 = abs(float(point_elasticity(1, 10, 2)))
    e2 = abs(float(point_elasticity(3, 10, 2)))
    chk("线性需求：价格越高 |ε| 越大", e2 > e1, True)
    chk("弧弹性（中点法）", arc_elasticity(1, 8, 3, 4), (4 - 8) / (3 - 1) * (2 / 6), 1e-12)

    print("\n索洛增长模型")
    ks = solow_steady(0.2, 0.01, 0.02, 0.07, 0.3)
    chk("稳态 k*", ks, 2.6918, 1e-3)
    chk("稳态 y* = (k*)^α", solow_output(0.2, 0.01, 0.02, 0.07, 0.3), ks ** 0.3, 1e-12)
    # 储蓄率越高，稳态资本越高
    chk("储蓄率上升 → 稳态资本上升", solow_steady(0.3, 0.01, 0.02, 0.07, 0.3) > ks, True)
    # 人口增长越快，稳态资本越低
    chk("人口增长加快 → 稳态资本下降", solow_steady(0.2, 0.03, 0.02, 0.07, 0.3) < ks, True)
    # 稳态处投资恰好等于持平投资
    chk("稳态处 sf(k*) = (n+g+δ)k*",
        0.2 * ks ** 0.3, (0.01 + 0.02 + 0.07) * ks, 1e-9)
    # 从低于稳态出发会收敛
    t, conv = solow_convergence_time(0.5, ks, 0.2, 0.01, 0.02, 0.07, 0.3)
    chk("从 k₀=0.5 出发能收敛到稳态附近", conv, True)

    print("\nCobb–Douglas 生产函数")
    chk("Y = A·K^α·L^(1−α)", cobb_douglas(1, 4, 9, 0.5), 6.0, 1e-12)
    mpk, mpl = marginal_products(1, 4, 9, 0.5)
    chk("MPK = αY/K", mpk, 0.5 * 6 / 4, 1e-12)
    chk("MPL = (1−α)Y/L", mpl, 0.5 * 6 / 9, 1e-12)
    chk("规模报酬不变（指数和为 1）", returns_to_scale(0.5), "规模报酬不变（指数之和 = 1）")
    left, right, rel = euler_check(1, 4, 9, 0.3)
    chk("欧拉定理 K·MPK + L·MPL = Y（相对误差 ~0）", rel < 1e-12, True)
    # 边际产量递减：K 越大 MPK 越小
    chk("MPK 随 K 递减", marginal_products(1, 8, 9, 0.3)[0] < marginal_products(1, 4, 9, 0.3)[0], True)

    print("\n垄断定价")
    qm, pm = monopoly_optimum(10, 1, 2)
    chk("垄断产量 q* = (a−MC)/(2b)", qm, sp.Integer(4))
    chk("垄断价格 p* = (a+MC)/2", pm, sp.Integer(6))
    chk("垄断利润", monopoly_profit(10, 1, 2), sp.Integer(16))
    li, inv, diff = lerner_index(10, 1, 2)
    chk("勒纳指数 (p−MC)/p", li, sp.Rational(2, 3))
    chk("勒纳指数 = 1/|ε|（恒等式）", diff, sp.Integer(0))
    # 边际成本上升 → 垄断产量下降、价格上升
    q2, p2 = monopoly_optimum(10, 1, 4)
    chk("MC 上升 → 产量下降", q2 < qm, True)
    chk("MC 上升 → 价格上升", p2 > pm, True)

    print("\n2×2 纳什均衡")
    # 囚徒困境（下标 0 = 合作、1 = 背叛）：双方都有占优策略「背叛」
    #   合作/合作 = (−1,−1)；背叛/合作 = (0,−3)；合作/背叛 = (−3,0)；背叛/背叛 = (−2,−2)
    pd = [[(-1, -1), (-3, 0)], [(0, -3), (-2, -2)]]
    chk("囚徒困境的唯一均衡是（背叛, 背叛）= (1,1)", nash_2x2(pd), [(1, 1)])
    # 协调博弈：两个纯策略均衡
    coord = [[(2, 2), (0, 0)], [(0, 0), (1, 1)]]
    chk("协调博弈有两个均衡", len(nash_2x2(coord)), 2)
    chk("  └ 包含 (0,0) 与 (1,1)", sorted(nash_2x2(coord)), [(0, 0), (1, 1)])
    rowa, colb = best_responses(pd)
    chk("对方合作时，行玩家的最优反应是「背叛」（下标 1）", rowa[0], [1])
    chk("  └ 列玩家同理", colb[0], [1])
    chk("对方背叛时，行玩家仍应「背叛」", rowa[1], [1])

    print("\n洛伦兹曲线与基尼系数")
    chk("L(0)=0", lorenz(0.0, 2.0), 0.0, 1e-12)
    chk("L(1)=1", lorenz(1.0, 2.0), 1.0, 1e-12)
    chk("β=1 时完全平等（基尼 = 0）", gini_from_beta(1.0), 0.0, 1e-12)
    chk("β=2 时基尼 = 1/3", gini_from_beta(2.0), 1.0 / 3, 1e-12)
    chk("β=3 时基尼 = 1/2", gini_from_beta(3.0), 0.5, 1e-12)
    chk("β 越大越不平等", gini_from_beta(4.0) > gini_from_beta(2.0), True)
    # 数值积分与解析式一致
    pts = [(i / 1000, lorenz(i / 1000, 2.0)) for i in range(1001)]
    gnum, _ = gini_from_curve(pts)
    chk("数值积分的基尼 ≈ 解析值 1/3", gnum, 1.0 / 3, 1e-4)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
