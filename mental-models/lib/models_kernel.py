# -*- coding: utf-8 -*-
"""
models_kernel.py — 查理·芒格思维模型：可量化部分的精确计算核心（sympy 精确运算）。

单一数据源设计：复利、贝叶斯基率、期望值与凯利仓位、安全边际击穿概率、机会成本
全部由本模块精确算出，讲解文字只引用 tex() 输出，绝无心算误差。

覆盖（v1，5 个模型）：
 1. compound    —— 复利/单利/翻倍时间（"时间是朋友还是敌人"的数学根据）
 2. bayes       —— 贝叶斯基率更新（基率忽视 → 假阳性的数学根源）
 3. expected    —— 期望值 + 幸存者偏差 + 凯利公式 f* = (bp − q)/b
 4. safety      —— 安全边际：正态内在价值分布 vs 价格线的击穿概率
 5. opportunity —— 机会成本：隐性成本 = 放弃的最优替代

依赖: sympy。自检：python models_kernel.py
"""

import sympy as sp


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

    print("models_kernel self-check OK ✓")
    print(f"  复利 1 万 @8% 30 年 → {f(c['F']):,.0f}（单利 {f(c['F_simple']):,.0f}，翻倍需 {f(c['doubling_years']):.2f} 年）")
    print(f"  贝叶斯 1% 患病率 + 99% 灵敏度/95% 特异度 → 阳性者真实患病概率 {f(b['posterior'])*100:.1f}%")
    print(f"  凯利 60% 赔率 2:1 → 满仓 {f(k['kelly'])*100:.0f}%，半仓 {f(k['kelly_half'])*100:.0f}%")
    print(f"  安全边际 120 估价 / 80 买入 → {f(m['mos_pct']):.1f}%，σ=15 时击穿概率 {f(kp['prob_pct']):.1f}%")
    print(f"  机会成本：选 80 放弃 {o['best_alt']} → 隐性成本 {f(o['opp_cost'])}")
