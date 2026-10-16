# -*- coding: utf-8 -*-
"""
models_kernel.py — 查理·芒格思维模型：可量化部分的精确计算核心（sympy 精确运算）。

单一数据源设计：复利、贝叶斯基率、期望值与凯利仓位、安全边际击穿概率、机会成本
全部由本模块精确算出，讲解文字只引用 tex() 输出，绝无心算误差。

覆盖（v4，17 个模型）：
 1. compound    —— 复利/单利/翻倍时间（"时间是朋友还是敌人"的数学根据）
 2. bayes       —— 贝叶斯基率更新（基率忽视 → 假阳性的数学根源）
 3. expected    —— 期望值 + 幸存者偏差 + 凯利公式 f* = (bp − q)/b
 4. safety      —— 安全边际：正态内在价值分布 vs 价格线的击穿概率
 5. opportunity —— 机会成本：隐性成本 = 放弃的最优替代
 6. inversion   —— 反过来想：串联系统的存活率 = ∏(1−pᵢ)，最弱环节优先
 7. incentive   —— 激励优先：把提成写进效用函数，代理人最优点必然偏离委托人
 8. competence  —— 能力圈：圈外暴露比例 → σ → 击穿概率
 9. lollapalooza—— 多倾向同向叠加：乘法放大 (1+a)ⁿ vs 线性直觉 1+na
10. checklist   —— 误判清单的拦截率 1−(1−hit)^k
11. dcf         —— 两阶段 DCF：显性期现值 + 终值现值，终值占比
12. scale       —— 规模优势：单位成本 u(q) = F/q + v
13. network     —— 网络效应：连接数 n(n−1)/2（用户翻倍 → 连接数 ×4）
14. tipping     —— 临界点：SIR 的 R₀ = βS₀/γ，解析峰值与 RK4 数值解互校
15. sunk        —— 沉没成本：决策只看增量，已投入不该出现
16. redundancy  —— 冗余备份：串联 rⁿ 与并联 1−(1−r)ⁿ（inversion 的对偶）
17. divergence  —— 大分叉（**数据驱动**）：读 data/maddison-gdp-per-capita.csv，
                   用复利公式量 1820 年前后两段的年化增长率

依赖: sympy（tipping 另用 math 做 RK4 数值积分）。
数据: data/maddison-gdp-per-capita.csv + data/SOURCES.md（出处/许可/归属要求）。
自检：python models_kernel.py
"""

import collections
import csv
import io
import math
import pathlib

import sympy as sp

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
MADDISON_CSV = SKILL_DIR / "data" / "maddison-gdp-per-capita.csv"
MADDISON_META = SKILL_DIR / "data" / "maddison-source.json"


# ---------------- 通用工具 ----------------
def tex(expr):
    return sp.latex(sp.nsimplify(sp.simplify(expr), rational=True))


def f(expr):
    return float(sp.N(expr))


def _num(v):
    """输入容错：把 int/float/str/Fraction 转成 sympy 精确有理数。"""
    return sp.nsimplify(sp.sympify(v), rational=True)


def _pct(r):
    """把 '8' 或 0.08 都归一成 0.08 这样的小数（约定：传整数按百分数理解）。"""
    v = _num(r)
    return v / 100 if abs(v) > 1 else v


# ==================== 1) 复利 ====================
def compound(P, r, t, n=1):
    """复利 F = P·(1 + r/n)^(n·t)，同时给出单利对照与翻倍时间。

    P 本金；r 年利率（传 8 或 0.08 均可）；t 年数；n 每年计息次数（n→∞ 为连续复利）。
    返回 {F, F_simple, gain_multiple, doubling_years, ...}。
    """
    P, t = _num(P), _num(t)
    r = _pct(r)
    n = _num(n) if not isinstance(n, int) else n
    assert P > 0 and t >= 0, "本金须为正、年数须非负"
    if n is None or n == sp.oo:
        F = P * sp.exp(r * t)
        mode = "连续复利"
    else:
        F = P * (1 + r / n) ** (n * t)
        mode = f"每年计息 {n} 次"
    F_simple = P * (1 + r * t)                       # 单利对照
    F = sp.simplify(F)
    F_simple = sp.simplify(F_simple)
    assert sp.simplify(F - F_simple) >= 0, "复利不可能低于单利"
    doubling = sp.simplify(sp.log(2) / sp.log(1 + r)) if r > 0 else sp.oo
    return {
        "mode": mode, "P": P, "r": r, "t": t, "F": F, "F_simple": F_simple,
        "gain_multiple": sp.simplify(F / P),                  # 本金倍数
        "interest_multiple": sp.simplify((F - P) / P),        # 纯收益倍数
        "double_vs_simple": sp.simplify(F - F_simple),        # 复利比单利多出的钱
        "doubling_years": doubling,
        "doubling_tex": tex(doubling) if r > 0 else "\\infty",
    }


def rule_of_72(r):
    """72 法则：翻倍年数 ≈ 72 / r(百分数)。与精确解对比，给出误差。"""
    r_pct = _num(r) if abs(_num(r)) > 1 else _num(r) * 100
    approx = sp.simplify(72 / r_pct)
    exact = sp.simplify(sp.log(2) / sp.log(1 + r_pct / 100))
    err = sp.simplify((approx - exact) / exact * 100)
    return {"approx": approx, "exact": exact, "error_pct": err,
            "approx_tex": tex(approx), "exact_tex": tex(exact)}


# ==================== 2) 贝叶斯基率 ====================
def bayes(prior, sens, spec, per=1000):
    """P(病|阳性) = 灵敏度·先验 / (灵敏度·先验 + (1−特异度)·(1−先验))。

    prior 先验患病率；sens 灵敏度(真阳率)；spec 特异度(真阴率)。
    同时给出 per 人规模下的四格人数（整数，供网格可视化）。
    """
    prior, sens, spec = _pct(prior), _pct(sens), _pct(spec)
    per = _num(per)
    assert 0 < prior < 1 and 0 < sens <= 1 and 0 < spec <= 1, "概率须落在 (0,1]"
    numerator = sens * prior
    denominator = sens * prior + (1 - spec) * (1 - prior)
    posterior = sp.simplify(numerator / denominator)
    # 假阳性占全部阳性的比例（这就是"为什么阳性大多没事"）
    fp_share = sp.simplify((1 - spec) * (1 - prior) / denominator)
    sick = sp.simplify(prior * per)
    tp = sp.simplify(numerator * per)
    fp = sp.simplify((1 - spec) * (1 - prior) * per)
    fn = sp.simplify(sick - tp)
    tn = sp.simplify(per - tp - fp - fn)
    assert sp.simplify(tp + fp + fn + tn - per) == 0, "四格人数必须加回总数"
    return {
        "prior": prior, "sens": sens, "spec": spec, "per": per,
        "posterior": posterior, "fp_share": fp_share,
        "odds_prior": sp.simplify(prior / (1 - prior)),
        "odds_post": sp.simplify(posterior / (1 - posterior)),
        "lift": sp.simplify(posterior / prior),       # 阳性把风险放大多少倍
        "tp": tp, "fp": fp, "fn": fn, "tn": tn, "sick": sick,
        "posterior_tex": tex(posterior),
        "fp_share_tex": tex(fp_share),
    }


# ==================== 3) 期望值 / 凯利 ====================
def expected_value(outcomes):
    """期望值 Σ pᵢvᵢ + 凯利最优仓位 f* = (bp − q)/b。

    outcomes: [(概率, 收益倍数), ...]，收益倍数按"净赔率 b"记（投 1 赢得 b）。
    """
    assert outcomes, "至少要有一个结果"
    ps = [_pct(o[0]) for o in outcomes]
    vs = [_num(o[1]) for o in outcomes]
    assert abs(sum(ps) - 1) < sp.Rational(1, 10**9), "概率之和必须为 1"
    ev = sp.simplify(sum(p * v for p, v in zip(ps, vs)))
    var = sp.simplify(sum(p * (v - ev) ** 2 for p, v in zip(ps, vs)))
    sd = sp.simplify(sp.sqrt(var))
    out = {"ev": ev, "variance": var, "sd": sd, "ev_tex": tex(ev)}
    # 凯利仅在两结果（赢 b / 输 1）时定义
    if len(outcomes) == 2:
        (p1, b), (p2, _) = outcomes[0], outcomes[1]
        b, p, q = _num(b), _pct(p1), _pct(p2)
        assert b > 0, "净赔率须为正"
        kelly = sp.simplify((b * p - q) / b)
        out.update({
            "kelly": kelly, "kelly_tex": tex(kelly),
            "kelly_half": sp.simplify(kelly / 2),      # 半凯利（芒格/巴菲特式保守）
            "edge": sp.simplify(ev),                   # 期望优势
            "grow_rate": sp.simplify(1 + p * b + q * (-1)),   # 每次下注的资金增长率
        })
        assert out["grow_rate"] == 1 + ev, "增长率 = 1 + 期望值"
    return out


def survivor_bias(startups=100, fail_rate=None, witness_return=None, lose=1.0):
    """幸存者偏差的算术：n 家创业公司，只有被看见的成功者回报 w，
    失败者血本无归（-lose）。观察到的"平均回报" vs 真实期望的差距。"""
    n = _num(startups)
    q = _pct(fail_rate) if fail_rate is not None else sp.Rational(1, 2)
    w = _num(witness_return)
    survivors = sp.simplify(n * (1 - q))
    observed = sp.simplify(w)                       # 只看得见赢家
    true_ev = sp.simplify((1 - q) * w - q * _num(lose))
    return {
        "n": n, "fail_rate": q, "witness_return": w, "losers": sp.simplify(n * q),
        "survivors": survivors, "observed": observed, "true_ev": true_ev,
        "bias_gap": sp.simplify(observed - true_ev),
        "bias_gap_tex": tex(sp.simplify(observed - true_ev)),
        "true_ev_tex": tex(true_ev),
        "true_ev_negative": bool(true_ev < 0),
    }


# ==================== 4) 安全边际 ====================
def margin_of_safety(intrinsic, price):
    """安全边际 = (内在价值 − 价格) / 内在价值。

    intrinsic 估计的内在价值；price 买入价。同时给出"要跌多少才回本"的对称口径。
    """
    V, P = _num(intrinsic), _num(price)
    assert V > 0 and P > 0, "价值与价格都须为正"
    mos = sp.simplify((V - P) / V)
    drawdown = sp.simplify((V - P) / P)             # 从买价涨到价值的涨幅（对称口径）
    return {"V": V, "P": P, "mos": mos, "mos_pct": mos * 100,
            "upside": drawdown * 100, "mos_tex": tex(mos),
            "safe": bool(mos > 0)}


def knockthrough_prob(mu, sigma, price):
    """击穿概率：假设真实价值 ~ N(μ, σ²)，P(真实价值 < 价格) = Φ((P−μ)/σ)。

    这是"为什么要留安全边际"的定量理由——估计越不准(σ 越大)，同一价格越危险。
    """
    mu, sigma, P = _num(mu), _num(sigma), _num(price)
    assert sigma > 0, "标准差须为正"
    z = sp.simplify((P - mu) / sigma)
    prob = sp.simplify(sp.Rational(1, 2) * (1 + sp.erf(z / sp.sqrt(2))))
    return {
        "mu": mu, "sigma": sigma, "P": P, "z": z,
        "prob": prob, "prob_tex": tex(prob), "prob_pct": prob * 100,
        "coefficient_of_variation": sp.simplify(sigma / mu),
        "safe_price_for_5pct": sp.simplify(mu - sp.sqrt(2) * sp.erfinv(sp.Rational(9, 10)) * sigma),
        "z_tex": tex(z),
    }


# ==================== 5) 机会成本 ====================
def opportunity_cost(chosen_value, alternatives):
    """机会成本 = 被放弃选项中的最优值 − 所选选项。

    chosen_value 所选方案的收益；alternatives 被放弃方案的收益列表。
    返回最优替代、真实净收益（扣掉机会成本后）与排序。
    """
    c = _num(chosen_value)
    alts = [_num(a) for a in alternatives]
    assert alts, "至少要有一个替代方案"
    best = max(alts)
    cost = sp.simplify(best - c)
    net = sp.simplify(c - best)                     # 相对最优替代的净收益（≥0 才说明选对）
    ranking = sorted([c] + alts, reverse=True)
    return {
        "chosen": c, "best_alt": best, "opp_cost": cost, "net_vs_best": net,
        "is_best": bool(sp.simplify(net) >= 0),
        "opp_cost_tex": tex(cost), "net_tex": tex(net),
        "n_options": len(alts) + 1,
    }


# ==================== 6) 反过来想（最弱环节） ====================
def inversion(n_factors, p_weak, p_rest):
    """反过来想：不问「怎么成功」，先问「怎么必然失败」。

    系统由 n 个必要环节串联——任何一环失效则全盘失败，于是存活率
        S = (1 − p_weak)·(1 − p_rest)^(n−1)
    有了生存概率，就能比大小：「先堵最弱的洞」和「把每个环节都做得更好」
    哪个更值钱。逆向思维在这里不再是格言，而是一个可排序的量。
    """
    n = _num(n_factors)
    pw, pr = _pct(p_weak), _pct(p_rest)
    assert n >= 1, "环节数须为正"
    assert 0 <= pw <= 1 and 0 <= pr <= 1, "失效概率须落在 [0,1]"
    S = sp.simplify((1 - pw) * (1 - pr) ** (n - 1))
    ceiling = sp.simplify((1 - pr) ** n)         # 最弱环节也修到普通水平后的存活率上限
    fail = sp.simplify(1 - S)
    # 归因：最弱环节一旦失效就全盘结束，故它单独造成的失败占全部失败的比例
    fatal_share = sp.Integer(0) if fail.is_zero else sp.simplify(pw / fail)
    # 策略 A：先堵最弱的洞（pw → pr）；策略 B：普通环节的失效概率各减半
    fix_gain = sp.oo if S.is_zero else sp.simplify(ceiling / S)
    polish_gain = sp.simplify(((1 - pr / 2) / (1 - pr)) ** (n - 1))
    # S ≥ 1/2 所容许的 pw 上界（< 0 即意味着再怎么修最弱环节也到不了一半）
    pw_limit = sp.simplify(1 - 1 / (2 * (1 - pr) ** (n - 1)))
    return {
        "n": n, "p_weak": pw, "p_rest": pr,
        "S": S, "fail": fail, "ceiling": ceiling, "fatal_share": fatal_share,
        "fix_weakest_gain": fix_gain, "polish_rest_gain": polish_gain,
        "fix_is_better": bool(sp.simplify(fix_gain - polish_gain) >= 0),
        "pw_limit_for_half": pw_limit, "half_reachable": bool(pw_limit >= 0),
        "S_tex": tex(S), "fail_tex": tex(fail), "ceiling_tex": tex(ceiling),
        "fatal_share_tex": tex(fatal_share),
    }


# ==================== 7) 激励优先（委托—代理） ====================
def incentive(commission, v_lin=100, v_quad=5, c_quad=2):
    """激励优先：把提成写进效用函数，代理人的最优点就必然偏离委托人。

    委托人（顾客）价值 $V(x) = v_{lin}x - v_{quad}x^2$，最优 $x_P = v_{lin}/(2v_{quad})$。
    代理人效用 $U(x) = commission\\cdot x - c_{quad}x^2$，最优 $x_A = commission/(2c_{quad})$。
    只有 $commission^* = c_{quad}v_{lin}/v_{quad}$ 时两者重合——
    偏一点，行为就偏一截。这不是道德问题，是算术问题。
    """
    c, a, b, d = _num(commission), _num(v_lin), _num(v_quad), _num(c_quad)
    assert a > 0 and b > 0 and d > 0, "系数须为正"
    x_p = sp.simplify(a / (2 * b))                       # 委托人最优
    x_a = sp.simplify(c / (2 * d))                       # 代理人最优
    V_opt = sp.simplify(a * x_p - b * x_p ** 2)          # 委托人在最优处的价值
    V_at_a = sp.simplify(a * x_a - b * x_a ** 2)         # 委托人在代理人最优处的价值
    loss = sp.simplify(V_opt - V_at_a)
    return {
        "commission": c, "x_p": x_p, "x_a": x_a,
        "misalign": sp.simplify(x_a - x_p),
        "V_at_opt": V_opt, "V_at_agent": V_at_a, "client_loss": loss,
        "loss_share": sp.simplify(loss / V_opt),
        "align_commission": sp.simplify(2 * d * x_p),    # 恰好对齐的提成
        "aligned": bool(sp.simplify(x_a - x_p) == 0),
        "x_p_tex": tex(x_p), "x_a_tex": tex(x_a), "loss_tex": tex(loss),
    }


# ==================== 8) 能力圈（暴露比例 → σ → 击穿） ====================
def competence(w_out, sigma_in, sigma_out, rho, mos, mu=100):
    """能力圈：圈外暴露比例 w 决定整体估计误差 σ，再决定击穿概率。

    组合 $\\sigma = \\sqrt{(1-w)^2\\sigma_{in}^2 + w^2\\sigma_{out}^2 + 2w(1-w)\\rho\\sigma_{in}\\sigma_{out}}$，
    击穿概率 $\\Phi((P-\\mu)/\\sigma)$，其中 $P = \\mu(1-\\text{MOS})$。
    关键：圈外方差与圈内方差相等发生在 $w^* = \\sigma_{in}/(\\sigma_{in}+\\sigma_{out})$——
    圈外只要占一小块，就吃掉一半方差。这就是「边界比大小重要」的可算版本。
    """
    w, si, so, r = _num(w_out), _num(sigma_in), _num(sigma_out), _num(rho)
    mos_, mu_ = _pct(mos), _num(mu)
    assert 0 <= w <= 1, "暴露比例须落在 [0,1]"
    assert si > 0 and so > 0, "标准差须为正"
    assert -1 <= r <= 1, "相关系数须落在 [-1,1]"
    var = sp.simplify((1 - w) ** 2 * si ** 2 + w ** 2 * so ** 2
                      + 2 * w * (1 - w) * r * si * so)
    sigma = sp.simplify(sp.sqrt(var))
    price = sp.simplify(mu_ * (1 - mos_))
    z = sp.simplify((price - mu_) / sigma)
    prob = sp.simplify(sp.Rational(1, 2) * (1 + sp.erf(z / sp.sqrt(2))))
    z_in = sp.simplify(-mos_ * mu_ / si)                  # 纯圈内（w=0）时的标准分
    prob_in = sp.simplify(sp.Rational(1, 2) * (1 + sp.erf(z_in / sp.sqrt(2))))
    return {
        "w": w, "sigma_in": si, "sigma_out": so, "rho": r, "mos": mos_, "mu": mu_,
        "sigma": sigma, "price": price, "z": z, "prob": prob,
        "prob_pure": prob_in, "prob_ratio": sp.simplify(prob / prob_in),
        "var_share_out": sp.Integer(0) if var.is_zero else sp.simplify(w ** 2 * so ** 2 / var),
        "w_crit": sp.simplify(si / (si + so)),            # 圈外方差贡献 = 圈内
        "safe": bool(prob < sp.Rational(1, 20)),
        "sigma_tex": tex(sigma), "prob_tex": tex(prob), "z_tex": tex(z),
    }


# ==================== 9) Lollapalooza（多倾向同向叠加） ====================
def lollapalooza(n, a):
    """Lollapalooza：多个倾向同向叠加时，乘法放大远快于线性直觉。

    单条倾向把「冲动」放大 (1+a) 倍，n 条同向叠加就是 (1+a)^n。
    而人的直觉按 1 + n·a 相加——两者在 n ≥ 2 就分道扬镳。
    """
    n, aa = _num(n), _num(a)
    assert n >= 1, "倾向条数须为正"
    assert aa > -1, "放大率须大于 −1"
    product = sp.simplify((1 + aa) ** n)
    linear = sp.simplify(1 + n * aa)
    excess = sp.simplify(product / linear)
    n_double = None
    for k in range(2, 61):
        if f((1 + aa) ** k / (1 + k * aa)) > 2:
            n_double = k
            break
    return {
        "n": n, "a": aa, "product": product, "linear": linear, "excess": excess,
        "extra_pct": sp.simplify((product - linear) / linear),
        "n_for_double": n_double,
        "product_tex": tex(product), "excess_tex": tex(excess),
        "superadditive": bool(sp.simplify(excess) > 1),
    }


# ==================== 10) 误判清单（拦截率） ====================
def checklist(k, a, hit):
    """误判倾向清单的净效果：每条倾向被栏下的概率为 hit。

    不上清单：放大 $(1+a)^k$；上了清单：$(1+a)^k(1-\\text{hit})^k$。
    拦截率 $= 1-(1-\\text{hit})^k$——同向倾向叠得越多，清单越值钱。
    """
    k, aa, h = _num(k), _num(a), _pct(hit)
    assert k >= 1, "倾向条数须为正"
    assert aa > -1 and 0 <= h <= 1, "参数越界"
    gross = sp.simplify((1 + aa) ** k)
    net = sp.simplify(((1 + aa) * (1 - h)) ** k)
    return {
        "k": k, "a": aa, "hit": h, "gross": gross, "net": net,
        "blocked": sp.simplify(1 - (1 - h) ** k),
        "residual_share": sp.simplify((1 - h) ** k),
        "cut": sp.simplify(gross / net) if not net.is_zero else sp.oo,   # 风险被压低多少倍
        "gross_tex": tex(gross), "net_tex": tex(net),
    }


# ==================== 11) 贴现与内在价值（两阶段 DCF） ====================
def dcf(cf0, growth, rate, years, term_growth):
    """两阶段 DCF：前 years 年按 growth 增长，其后按 term_growth 永续增长。

    内在价值 = 显性期现值 + 终值现值：
        V = Σ_{t=1..N} CF₀(1+g)^t/(1+r)^t + [CF₀(1+g)^N(1+g∞)/(r-g∞)]/(1+r)^N
    要求 r > g∞，否则级数发散（"永续增长快过贴现"是一个不自洽的假设）。
    终值占比是这张图真正的重点：它衡量估值有多依赖远期假设。
    """
    cf0, g, r, tg = _num(cf0), _pct(growth), _pct(rate), _pct(term_growth)
    N = _num(years)
    assert cf0 > 0, "现金流须为正"
    assert r > tg, "贴现率必须高于永续增长率，否则现值发散"
    assert N >= 0, "年数须非负"
    pv_flows = [sp.simplify(cf0 * (1 + g) ** t / (1 + r) ** t) for t in range(1, int(N) + 1)]
    pv_explicit = sp.simplify(sum(pv_flows))
    cash_N1 = sp.simplify(cf0 * (1 + g) ** N * (1 + tg))        # 第 N+1 年现金流
    terminal = sp.simplify(cash_N1 / (r - tg))                   # 第 N 年末的终值
    pv_terminal = sp.simplify(terminal / (1 + r) ** N)
    V = sp.simplify(pv_explicit + pv_terminal)
    # 贴现率 +1 个百分点的敏感度：估值对假设有多脆
    r2 = r + sp.Rational(1, 100)
    V2 = sp.simplify(sum(cf0 * (1 + g) ** t / (1 + r2) ** t for t in range(1, int(N) + 1))
                     + (cf0 * (1 + g) ** N * (1 + tg) / (r2 - tg)) / (1 + r2) ** N)
    return {
        "cf0": cf0, "g": g, "r": r, "tg": tg, "years": N,
        "pv_flows": pv_flows, "pv_explicit": pv_explicit,
        "cash_N1": cash_N1, "terminal": terminal, "pv_terminal": pv_terminal,
        "V": V, "terminal_share": sp.simplify(pv_terminal / V),
        "V_rate_up": V2, "rate_sensitivity": sp.simplify((V - V2) / V),
        "V_tex": tex(V), "terminal_share_tex": tex(sp.simplify(pv_terminal / V)),
    }


# ==================== 12) 规模优势（固定成本摊薄） ====================
def scale_advantage(fixed, var, q1, k):
    """规模优势：单位成本 u(q) = F/q + v —— 固定成本被产量摊薄。

    规模是 k 倍时，单位成本优势 u(q) − u(kq) 就是大者对小者的"价格战额度"。
    固定成本占单位成本降到 10% 所需的规模 q* = 9F/v，是一个干净的临界点。
    """
    F, v, q, k = _num(fixed), _num(var), _num(q1), _num(k)
    assert F >= 0 and v > 0 and q > 0 and k >= 1, "参数越界"
    u1 = sp.simplify(F / q + v)
    u2 = sp.simplify(F / (k * q) + v)
    fixed_share = sp.simplify((F / q) / u1) if F > 0 else sp.Integer(0)
    return {
        "fixed": F, "var": v, "q1": q, "k": k,
        "u1": u1, "u2": u2, "advantage": sp.simplify(u1 - u2),
        "cost_ratio": sp.simplify(u1 / u2),
        "fixed_share": fixed_share,
        "scale_for_10pct": sp.simplify(9 * F / v),          # 固定成本占比降到 10% 所需规模
        "u1_tex": tex(u1), "u2_tex": tex(u2),
        "advantage_tex": tex(sp.simplify(u1 - u2)),
    }


# ==================== 13) 网络效应（连接数按平方涨） ====================
def network_value(n, target_links=1000000):
    """网络效应：连接数 n(n−1)/2，梅特卡夫口径的价值 n(n−1)。

    用户数只按 n 涨，连接数却按 n² 涨——这就是"赢家通吃"的算术。
    """
    n = _num(n)
    assert n >= 1, "用户数须为正"
    links = sp.simplify(n * (n - 1) / 2)
    metcalfe = sp.simplify(n * (n - 1))
    tgt = _num(target_links)
    # n(n−1)/2 = tgt 的正根
    n_for_target = sp.simplify((1 + sp.sqrt(1 + 8 * tgt)) / 2)
    return {
        "n": n, "links": links, "metcalfe": metcalfe,
        "links_double_ratio": sp.simplify((2 * n) * (2 * n - 1) / (n * (n - 1)))
                              if n > 1 else sp.oo,
        "n_for_target": n_for_target, "target_links": tgt,
        "links_tex": tex(links),
    }


# ==================== 14) 临界点与传染（SIR，R₀ 阈值） ====================
def _sir_rk4(beta, gamma, s0, i0, days, steps_per_day=16):
    """用 RK4 真实积分 SIR 方程（纯数值，非符号解）。

    dS/dt = −βSI,  dI/dt = βSI − γI,  dR/dt = γI，三者之和恒为 1。
    """
    b, g = float(beta), float(gamma)
    h = 1.0 / steps_per_day
    s, i, r = float(s0), float(i0), 0.0
    curve = [(0.0, s, i, r)]
    peak_i, peak_t = i, 0.0
    for step in range(int(days * steps_per_day)):
        def d(s_, i_, r_):
            return (-b * s_ * i_, b * s_ * i_ - g * i_, g * i_)
        k1 = d(s, i, r)
        k2 = d(s + h / 2 * k1[0], i + h / 2 * k1[1], r + h / 2 * k1[2])
        k3 = d(s + h / 2 * k2[0], i + h / 2 * k2[1], r + h / 2 * k2[2])
        k4 = d(s + h * k3[0], i + h * k3[1], r + h * k3[2])
        s += h / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0])
        i += h / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1])
        r += h / 6 * (k1[2] + 2 * k2[2] + 2 * k3[2] + k4[2])
        s, i, r = max(0.0, min(1.0, s)), max(0.0, min(1.0, i)), max(0.0, min(1.0, r))
        t = (step + 1) * h
        if i > peak_i:
            peak_i, peak_t = i, t
        curve.append((t, s, i, r))
    return curve, peak_i, peak_t


def tipping(beta, gamma, s0=1.0, i0=1e-4, days=80):
    """临界点：基本传染数 R₀ = βS₀/γ。R₀ 略过 1，结局天翻地覆。

    峰值感染有解析式 I_peak = I₀ + S₀ − S_peak + (1/R₀)·ln(S_peak/S₀)，
    其中 S_peak = 1/R₀。这里同时给出解析值与 RK4 数值解，两者互为校验。
    """
    b, g = _num(beta), _num(gamma)
    s0_, i0_ = _num(s0), _num(i0)
    assert b > 0 and g > 0 and 0 < s0_ <= 1, "参数越界"
    R0 = sp.simplify(b * s0_ / g)
    exploded = bool(R0 > 1)
    peak_frac_analytic = None
    if exploded:
        s_peak = sp.simplify(1 / R0)
        peak_frac_analytic = sp.simplify(i0_ + s0_ - s_peak + sp.log(s_peak / s0_) / R0)
    curve, peak_num, peak_t = _sir_rk4(b, g, float(s0_), float(i0_), days)
    final_size = sp.nsimplify(curve[-1][3], rational=False)
    # R∞ = 1 − exp(−R₀·R∞) 的二分求解（与数值积分互为校验）
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if 1 - math.exp(-float(R0) * mid) > mid:
            lo = mid
        else:
            hi = mid
    return {
        "beta": b, "gamma": g, "s0": s0_, "days": _num(days),
        "R0": R0, "exploded": exploded,
        "peak_frac_analytic": peak_frac_analytic,
        "peak_frac_numeric": peak_num, "peak_day": peak_t,
        "final_size_numeric": final_size, "final_size_solved": hi,
        "herd_threshold": sp.simplify(g / b),      # 需要压到多少易感比例以下才能熄灭
        "R0_tex": tex(R0),
    }


# ==================== 15) 沉没成本（只看增量） ====================
def sunk_cost(sunk, extra, p_success, reward):
    """沉没成本：已经花掉的，不该进入决策。

    理性算法只看未来的增量：E[继续] = p·R − C。已投入 S 完全不出现。
    而"账面"算法把 S 也算进去，于是把一个正期望的项目算成负的——
    这正是损失厌恶的入口。
    """
    S, C, p, R = _num(sunk), _num(extra), _pct(p_success), _num(reward)
    assert C >= 0 and R >= 0, "参数越界"
    ev_continue = sp.simplify(p * R - C)              # 正确：只看增量
    ev_wrong = sp.simplify(p * R - C - S)             # 错误：把沉没成本算进来
    breakeven_p = sp.simplify(C / R) if R > 0 else sp.oo
    return {
        "sunk": S, "extra": C, "p": p, "reward": R,
        "ev_continue": ev_continue, "ev_wrong": ev_wrong,
        "should_continue": bool(ev_continue > 0),
        "breakeven_p": breakeven_p,
        "ev_continue_tex": tex(ev_continue), "ev_wrong_tex": tex(ev_wrong),
        "conclusions_differ": bool((ev_continue > 0) != (ev_wrong > 0)),
    }


# ==================== 16) 冗余备份（串联的对偶） ====================
def redundancy(r, n):
    """冗余备份：同一个零件，串联与并联的可靠度天差地别。

    串联 R = r^n（任一坏则坏），并联 R = 1 − (1−r)^n（全坏才坏）。
    串联系数与「反过来想」的存活率是同一个式子——这里给出它的对偶：
    与其把每一环做得更好，不如让关键环变成并联。
    """
    r_, n_ = _pct(r), _num(n)
    assert 0 <= r_ <= 1 and n_ >= 1, "参数越界"
    series = sp.simplify(r_ ** n_)
    parallel = sp.simplify(1 - (1 - r_) ** n_)
    # 串联掉到 50% 以下所需的最少环数
    n_series_half = None
    if 0 < r_ < 1:
        n_series_half = sp.simplify(sp.log(sp.Rational(1, 2)) / sp.log(r_))
    # 并联达到 99% 所需的最少件数
    n_parallel_99 = None
    if 0 <= r_ < 1:
        n_parallel_99 = sp.simplify(sp.log(sp.Rational(1, 100)) / sp.log(1 - r_))
    return {
        "r": r_, "n": n_, "series": series, "parallel": parallel,
        "gain": sp.simplify(parallel / series) if not series.is_zero else sp.oo,
        "n_series_half": n_series_half, "n_parallel_99": n_parallel_99,
        "series_tex": tex(series), "parallel_tex": tex(parallel),
    }


# ==================== 17) 大分叉（数据驱动） ====================
# 这是唯一一个「数据驱动」而非公式驱动的模型：数值来自 data/maddison-gdp-per-capita.csv，
# 而不是推导。纪律因此从「不手写数字」升级为「不手写数据」——见 data/SOURCES.md。
def load_maddison(path=None):
    """读蒸馏后的 Maddison 序列 → {实体: [(年, 人均 GDP 2011 国际元), ...]}，按年升序。

    刻意不做插值：1820 年前的点本来就稀疏，补出来的平滑曲线会假装比史料更确定。
    """
    p = pathlib.Path(path) if path else MADDISON_CSV
    assert p.exists(), f"缺少数据集：{p}（先跑 python scripts/fetch_maddison.py）"
    series = collections.OrderedDict()
    with io.open(p, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            series.setdefault(row["entity"], []).append(
                (int(row["year"]), sp.Rational(row["gdp_pc_2011intl"])))
    for k in series:
        series[k].sort()
    return series


def maddison_meta(path=None):
    """读 data/maddison-source.json（单位、引用、更新时间）。"""
    p = pathlib.Path(path) if path else MADDISON_META
    assert p.exists(), f"缺少元数据：{p}"
    import json
    return json.loads(p.read_text(encoding="utf-8"))


def nearest_point(series, t):
    """取最接近 t 的**实测点**（宁可换年，也不插值）。"""
    assert series, "序列为空"
    return min(series, key=lambda pt: (abs(pt[0] - t), pt[0]))


def cagr(v0, v1, years):
    """年化复合增长率 = (v1/v0)^(1/年数) − 1 —— 就是第 1 页复利公式反过来用。"""
    assert v0 > 0 and v1 > 0, "两端取值须为正"
    assert years > 0, "年数须为正"
    return sp.simplify((v1 / v0) ** (sp.Rational(1, years)) - 1)


def window_growth(series, t0, t1):
    """区间 [t0, t1] 的年化增长率；两端各自吸附到最近的实测点，并如实回报用了哪两年。"""
    a, b = nearest_point(series, t0), nearest_point(series, t1)
    if b[0] <= a[0]:
        return None
    yrs = b[0] - a[0]
    return {
        "y0": a[0], "v0": a[1], "y1": b[0], "v1": b[1], "years": yrs,
        "multiple": sp.simplify(b[1] / a[1]),
        "cagr": cagr(a[1], b[1], yrs),
        "cagr_pct": cagr(a[1], b[1], yrs) * 100,
    }


def great_divergence(series=None, pivot=1820):
    """大分叉：把每条序列在 pivot（默认 1820）处切成两段，比较年化增长率。

    返回逐实体的两段 CAGR 与所用年份 —— 全由数据集现算。
    """
    series = series or load_maddison()
    out = []
    for name, pts in series.items():
        first, last = pts[0], pts[-1]
        mid = nearest_point(pts, pivot)
        pre = cagr(first[1], mid[1], mid[0] - first[0]) if mid[0] > first[0] else None
        post = cagr(mid[1], last[1], last[0] - mid[0]) if last[0] > mid[0] else None
        out.append({
            "entity": name,
            "first_year": first[0], "first_value": first[1],
            "pivot_year": mid[0], "pivot_value": mid[1],
            "last_year": last[0], "last_value": last[1],
            "pre_cagr": pre, "post_cagr": post,
            "pre_years": mid[0] - first[0], "post_years": last[0] - mid[0],
            "ratio": sp.simplify(post / pre) if (pre and pre != 0) else None,
        })
    return out


# ==================== 自检 ====================
if __name__ == "__main__":
    # 复利
    c = compound(10000, 8, 30)
    assert sp.simplify(c["F"] - 10000 * sp.Rational(108, 100) ** 30) == 0
    assert c["F"] > c["F_simple"] > 10000
    assert abs(f(c["doubling_years"]) - 9.006) < 0.02       # 8% 约 9 年翻倍
    r72 = rule_of_72(8)
    assert abs(f(r72["approx"]) - 9) < 1e-9 and abs(f(r72["error_pct"])) < 1
    assert compound(1000, 10, 0)["F"] == 1000                # t=0 不变

    # 贝叶斯
    b = bayes(prior=0.01, sens=0.99, spec=0.95)
    assert abs(f(b["posterior"]) - 0.1666666667) < 1e-6      # 1% 患病率 + 99% 灵敏度 → 阳性仅 16.7% 有病
    assert b["posterior"] < b["sens"], "阳性预测值必然低于灵敏度（只要患病率低）"
    assert sp.simplify(b["tp"] + b["fp"] + b["fn"] + b["tn"]) == 1000
    assert f(bayes(0.5, 1, 1)["posterior"]) == 1.0           # 完美检测下后验=先验上限

    # 期望值 / 凯利
    e = expected_value([(0.6, 1), (0.4, -1)])
    assert sp.simplify(e["ev"] - sp.Rational(1, 5)) == 0
    k = expected_value([(0.6, 2), (0.4, -1)])
    assert sp.simplify(k["kelly"] - sp.Rational(2, 5)) == 0   # f* = (2·0.6 − 0.4)/2 = 0.2
    assert sp.simplify(k["kelly_half"] - sp.Rational(1, 5)) == 0
    assert sp.simplify(expected_value([(0.5, 1), (0.5, -1)])["ev"]) == 0  # 公平赌局期望为 0
    sb = survivor_bias(100, sp.Rational(10, 11), 10, 1)
    assert sp.simplify(sb["true_ev"]) == 0 and f(sb["observed"]) == 10   # 10 倍回报下真实期望仅打平
    assert sb["true_ev"] < sb["observed"], "幸存者偏差必然高估回报"

    # 安全边际
    m = margin_of_safety(120, 80)
    assert sp.simplify(m["mos"] - sp.Rational(1, 3)) == 0
    assert m["safe"] is True and margin_of_safety(80, 120)["safe"] is False
    kp = knockthrough_prob(100, 15, 80)
    assert 0 < f(kp["prob"]) < 0.5                       # 低于均值的价格 → 击穿概率 < 50%
    assert abs(f(knockthrough_prob(100, 15, 100)["prob"]) - 0.5) < 1e-12
    assert knockthrough_prob(100, 30, 90)["prob"] > knockthrough_prob(100, 10, 90)["prob"]

    # 机会成本
    o = opportunity_cost(80, [100, 50])
    assert f(o["opp_cost"]) == 20.0 and o["is_best"] is False
    assert opportunity_cost(100, [80])["is_best"] is True

    # 反过来想
    inv = inversion(8, sp.Rational(1, 2), sp.Rational(1, 10))
    assert abs(f(inv["S"]) - 0.239148450) < 1e-9              # 0.5 · 0.9^7
    assert abs(f(inv["ceiling"]) - 0.430467210) < 1e-9        # 0.9^8
    assert abs(f(inv["fix_weakest_gain"]) - 1.8) < 1e-9       # = (1−0.1)/(1−0.5)
    assert inv["fix_is_better"] is True, "先堵最弱的洞应优于全员优化"
    assert inv["half_reachable"] is False, "8 环 @10%：最弱环节修好也到不了一半"
    assert sp.simplify(inv["fatal_share"] * inv["fail"] - inv["p_weak"]) == 0
    assert f(inversion(1, sp.Rational(3, 10), sp.Rational(1, 10))["S"]) == 0.7

    # 激励优先
    inc = incentive(20)
    assert f(inc["x_p"]) == 10 and f(inc["x_a"]) == 5
    assert f(inc["client_loss"]) == 125 and abs(f(inc["loss_share"]) - 0.25) < 1e-9
    assert f(inc["align_commission"]) == 40
    assert inc["aligned"] is False and incentive(40)["aligned"] is True
    assert f(incentive(40)["x_a"]) == 10
    # 提成太低（消极）与太高（过度推销）造成的损失对称
    assert sp.simplify(incentive(60)["client_loss"] - 125) == 0
    assert sp.simplify(incentive(20)["misalign"] + incentive(60)["misalign"]) == 0

    # 能力圈
    cp = competence(sp.Rational(1, 5), 10, 40, 0, sp.Rational(1, 5))
    assert sp.simplify(cp["sigma"] ** 2 - 128) == 0            # 64（圈内）+ 64（圈外）
    assert abs(f(cp["var_share_out"]) - 0.5) < 1e-9, "20% 暴露就吃掉一半方差"
    assert abs(f(cp["w_crit"]) - 0.2) < 1e-9
    assert cp["safe"] is True
    assert competence(sp.Rational(2, 5), 10, 40, 0, sp.Rational(1, 5))["prob"] > cp["prob"]
    assert f(competence(0, 10, 40, 0, sp.Rational(1, 5))["prob_pure"] - cp["prob_pure"]) == 0

    # Lollapalooza
    lp = lollapalooza(4, sp.Rational(1, 2))
    assert sp.simplify(lp["product"] - sp.Rational(81, 16)) == 0    # 1.5^4
    assert lp["linear"] == 3 and sp.simplify(lp["excess"] - sp.Rational(27, 16)) == 0
    assert lp["n_for_double"] == 5
    assert lollapalooza(1, sp.Rational(1, 2))["excess"] == 1        # 单条无叠加
    assert lollapalooza(2, sp.Rational(1, 2))["superadditive"] is True

    # 误判清单
    ck_ = checklist(4, sp.Rational(1, 2), sp.Rational(1, 2))
    assert sp.simplify(ck_["gross"] - sp.Rational(81, 16)) == 0     # 1.5^4
    assert sp.simplify(ck_["net"] - sp.Rational(81, 256)) == 0      # 0.75^4
    assert sp.simplify(ck_["blocked"] - sp.Rational(15, 16)) == 0    # 1 − 0.5^4

    # 贴现 / DCF
    d = dcf(100, 8, 10, 10, 3)
    assert abs(f(d["V"]) - 2130.02) < 0.02
    assert abs(f(d["pv_explicit"]) - 905.26) < 0.02
    assert abs(f(d["pv_terminal"]) - 1224.76) < 0.02
    assert abs(f(d["terminal_share"]) - 0.5750) < 0.0005     # 终值占 57.5%
    assert abs(f(d["rate_sensitivity"]) * 100 - 13.54) < 0.02  # 贴现率 +1% → 估值 −13.5%
    assert d["V"] > d["V_rate_up"], "提高贴现率必然压低内在价值"

    # 规模优势
    sc = scale_advantage(1000, 10, 500, 3)
    assert sp.simplify(sc["u1"] - 12) == 0
    assert sp.simplify(sc["u2"] - sp.Rational(32, 3)) == 0    # 10 + 2/3
    assert sp.simplify(sc["advantage"] - sp.Rational(4, 3)) == 0
    assert abs(f(sc["cost_ratio"]) - 1.125) < 1e-9
    assert abs(f(sc["fixed_share"]) - 1 / 6) < 1e-9
    assert sp.simplify(sc["scale_for_10pct"] - 900) == 0

    # 网络效应
    nw = network_value(1000)
    assert sp.simplify(nw["links"] - 499500) == 0
    assert sp.simplify(nw["metcalfe"] - 999000) == 0
    assert abs(f(nw["links_double_ratio"]) - 4.002) < 0.001   # 用户翻倍 → 连接数 ×4
    assert abs(f(nw["n_for_target"]) - 1414.71) < 0.01        # 100 万连接只需 1415 人

    # 临界点 / SIR
    tp = tipping(sp.Rational(3, 5), sp.Rational(1, 5))
    assert sp.simplify(tp["R0"] - 3) == 0
    assert abs(f(tp["peak_frac_analytic"]) - 0.300556) < 1e-5
    assert abs(f(tp["peak_frac_analytic"]) - tp["peak_frac_numeric"]) < 0.01, "解析峰值应与 RK4 数值解一致"
    assert abs(tp["final_size_solved"] - 0.9405) < 0.001
    assert abs(f(tp["herd_threshold"]) - 1 / 3) < 1e-9
    assert tp["exploded"] is True
    dead = tipping(sp.Rational(3, 20), sp.Rational(1, 5))     # R₀ = 0.75
    assert dead["exploded"] is False and dead["peak_frac_analytic"] is None

    # 沉没成本
    sk = sunk_cost(100, 50, sp.Rational(2, 5), 200)
    assert sp.simplify(sk["ev_continue"] - 30) == 0
    assert sp.simplify(sk["ev_wrong"] + 70) == 0
    assert sp.simplify(sk["breakeven_p"] - sp.Rational(1, 4)) == 0
    assert sk["should_continue"] is True and sk["conclusions_differ"] is True

    # 冗余备份
    rd = redundancy(sp.Rational(9, 10), 5)
    assert abs(f(rd["series"]) - 0.59049) < 1e-9
    assert abs(f(rd["parallel"]) - 0.99999) < 1e-9
    assert abs(f(rd["n_series_half"]) - 6.57881) < 1e-5
    assert abs(f(rd["n_parallel_99"]) - 2.0) < 1e-9           # 单件 90%：并两件即 99%
    assert rd["parallel"] > rd["series"]

    # 大分叉（数据驱动：全部来自 data/maddison-gdp-per-capita.csv）
    md = load_maddison()
    assert list(md) == ["United Kingdom", "France", "United States",
                        "Japan", "China", "India"], "实体集合变了"
    assert sum(len(v) for v in md.values()) == 2188, "数据集行数变了？"
    assert maddison_meta()["unit"] == "international-$ in 2011 prices", "单位变了"
    gd = {r["entity"]: r for r in great_divergence(md)}
    assert abs(f(gd["United Kingdom"]["pre_cagr"]) * 100 - 0.1288) < 0.0005
    assert abs(f(gd["United Kingdom"]["post_cagr"]) * 100 - 1.2215) < 0.0005
    assert abs(f(gd["Japan"]["post_cagr"]) * 100 - 1.6819) < 0.0005
    assert f(gd["China"]["pre_cagr"]) < 0, "中国 1820 年前是负增长——大分叉的一半真相"
    assert f(gd["India"]["pre_cagr"]) < 0, "印度 1820 年前同样是负增长"
    assert gd["India"]["pivot_year"] == 1821, "印度最接近 1820 的实测点是 1821（宁可换年，不插值）"
    assert all(f(gd[e]["post_cagr"]) > 0 for e in md), "1820 之后六国全部转正"
    assert abs(f(window_growth(md["United Kingdom"], 1820, 2020)["cagr_pct"]) - 1.1817) < 0.0005
    assert abs(f(window_growth(md["China"], 1820, 2020)["multiple"]) - 19.53) < 0.01
    assert abs(f(window_growth(md["China"], 1000, 2020)["cagr_pct"]) - 0.2595) < 0.0005
    assert [e for e in md][0] == "United Kingdom"
    # 2022 年的高低次序（数据不插值、不修改，直接来自源文件）
    order = sorted(md, key=lambda e: -f(md[e][-1][1]))
    assert order == ["United States", "France", "United Kingdom", "Japan",
                     "China", "India"], f"2022 年次序变了：{order}"

    print("models_kernel self-check OK ✓")
    print(f"  复利 1 万 @8% 30 年 → {f(c['F']):,.0f}（单利 {f(c['F_simple']):,.0f}，翻倍需 {f(c['doubling_years']):.2f} 年）")
    print(f"  贝叶斯 1% 患病率 + 99% 灵敏度/95% 特异度 → 阳性者真实患病概率 {f(b['posterior'])*100:.1f}%")
    print(f"  凯利 60% 赔率 2:1 → 满仓 {f(k['kelly'])*100:.0f}%，半仓 {f(k['kelly_half'])*100:.0f}%")
    print(f"  安全边际 120 估价 / 80 买入 → {f(m['mos_pct']):.1f}%，σ=15 时击穿概率 {f(kp['prob_pct']):.1f}%")
    print(f"  机会成本：选 80 放弃 {o['best_alt']} → 隐性成本 {f(o['opp_cost'])}")
    print(f"  反过来想 8 环 @10%、最弱 50% → 存活 {f(inv['S'])*100:.1f}%，修最弱 ×{f(inv['fix_weakest_gain']):.2f}")
    print(f"  激励优先提成 20 → 代理人选 {f(inc['x_a']):.0f}、委托人要 {f(inc['x_p']):.0f}，损失 {f(inc['client_loss']):.0f}")
    print(f"  能力圈 20% 暴露（σ {f(cp['sigma_in']):.0f} vs {f(cp['sigma_out']):.0f}）→ σ {f(cp['sigma']):.2f}，占方差 {f(cp['var_share_out'])*100:.0f}%")
    print(f"  Lollapalooza 4 条 ×1.5 → {f(lp['product']):.2f}（线性只给 {f(lp['linear']):.0f}），超出 {f(lp['extra_pct'])*100:.0f}%")
    print(f"  误判清单 4 条 ×1.5、拦截 50% → {f(ck_['gross']):.2f} 降到 {f(ck_['net']):.2f}，拦掉 {f(ck_['blocked'])*100:.1f}%")
    print(f"  DCF 100/8%/r=10%/N=10/g∞=3% → V={f(d['V']):,.0f}，终值占 {f(d['terminal_share'])*100:.1f}%")
    print(f"  规模优势 F=1000,v=10,q=500,k=3 → 单位成本 {f(sc['u1']):.2f} vs {f(sc['u2']):.2f}（省 {f(sc['advantage']):.2f}）")
    print(f"  网络效应 n=1000 → 连接数 {f(nw['links']):,.0f}，用户翻倍变成 ×{f(nw['links_double_ratio']):.2f}")
    print(f"  临界点 R₀={f(tp['R0']):.2f} → 峰值感染 {f(tp['peak_frac_analytic'])*100:.1f}%，最终 {tp['final_size_solved']*100:.1f}%")
    print(f"  沉没成本 已投 100 + 追加 50、p=40%、回报 200 → 正确算法 {f(sk['ev_continue']):+.0f}，账面算成 {f(sk['ev_wrong']):+.0f}")
    print(f"  冗余备份 r=90%, n=5 → 串联 {f(rd['series'])*100:.2f}%，并联 {f(rd['parallel'])*100:.5f}%")
    print(f"  大分叉 {len(md)} 国 {sum(len(v) for v in md.values())} 点 → "
          f"英国前段 {f(gd['United Kingdom']['pre_cagr'])*100:.4f}%/年、"
          f"后段 {f(gd['United Kingdom']['post_cagr'])*100:.4f}%/年；"
          f"中国前段 {f(gd['China']['pre_cagr'])*100:+.4f}%/年")
