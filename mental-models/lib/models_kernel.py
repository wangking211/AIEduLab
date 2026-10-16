# -*- coding: utf-8 -*-
"""
models_kernel.py — 查理·芒格思维模型：可量化部分的精确计算核心（sympy 精确运算）。

单一数据源设计：复利、贝叶斯基率、期望值与凯利仓位、安全边际击穿概率、机会成本
全部由本模块精确算出，讲解文字只引用 tex() 输出，绝无心算误差。

覆盖（v2，10 个模型）：
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
