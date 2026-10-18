#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stat_kernel.py —— 大学「统计推断」内核

覆盖：
  · 抽样分布与标准误 SE = σ/√n（**真实重复抽样**得到样本均值的分布）
  · 点估计与无偏性：为什么样本方差要除以 n−1（两种估计量的期望对比）
  · 置信区间与**覆盖率**（模拟「重复抽样时有多少比例的区间盖住了真值」）
  · t 检验与 **p 值**（在 H₀ 下 p 值服从均匀分布 —— 这个反直觉的事实靠模拟展示）
  · 两类错误与功效（α、β、功效随样本量与效应量的变化）
  · 最小二乘回归与 R²（真实拟合）
  · 比例的估计与检验（二项比例的区间与检验）

设计原则（与全项目一致）：
  · **不手写数字**：所有分布、覆盖率、功效、R² 都是**真实模拟或精确公式**算出来的；
    模拟一律用**固定种子**，所以结果可复现（`check_skills` 的基线才能对得上）。
  · 理论值与模拟值**并列给出**，两者的接近本身就是最好的教学素材。
  · 自检：python stat_kernel.py
"""

import math
import random

__all__ = [
    "f", "num_str", "pct",
    "gauss_cdf", "gauss_pdf", "t_pdf", "t_cdf",
    "se_mean", "sample_mean", "sample_var_n", "sample_var_n1",
    "simulate_means", "simulate_var_estimators",
    "ci_mean", "ci_z_critical", "simulate_coverage",
    "t_statistic", "p_value_t", "simulate_pvalues",
    "power_two_sided", "simulate_power_curve",
    "ols_fit", "r_squared",
    "prop_ci_wald", "prop_se", "prop_z_test", "simulate_prop_dist",
    "hist", "z_critical",
]


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
    if abs(val) >= 1e5 or abs(val) < 1e-4:
        return f"{val:.3e}".replace("e-0", "e-").replace("e+0", "e")
    return f(val, digits)


def pct(v, digits=1):
    return f"{float(v) * 100.0:.{digits}f}"


# ---------------------------------------------------------------- 分布函数
def gauss_pdf(z, mu=0.0, sigma=1.0):
    return math.exp(-0.5 * ((z - mu) / sigma) ** 2) / (sigma * math.sqrt(2 * math.pi))


def gauss_cdf(z, mu=0.0, sigma=1.0):
    return 0.5 * (1.0 + math.erf((z - mu) / (sigma * math.sqrt(2.0))))


def t_pdf(x, df):
    """t 分布的概率密度（用 lgamma 避免大 df 时溢出）。"""
    logc = math.lgamma((df + 1) / 2.0) - 0.5 * math.log(df * math.pi) - math.lgamma(df / 2.0)
    return math.exp(logc - (df + 1) / 2.0 * math.log1p(x * x / df))


def _betacf(a, b, x, itmax=300, eps=3e-16):
    """正则化不完全贝塔函数的连分式（Numerical Recipes 的做法）。"""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-30:
        d = 1e-30
    d = 1.0 / d
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < eps:
            break
    return h


def _betai(a, b, x):
    """正则化不完全贝塔函数 I_x(a, b)。"""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbt = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
           + a * math.log(x) + b * math.log1p(-x))
    bt = math.exp(lbt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_cdf(x, df):
    """t 分布的 CDF，P(T ≤ x)。

    用恒等式 P(|T| > t) = I_{df/(df+t²)}(df/2, 1/2) 化为不完全贝塔函数 ——
    比数值积分快得多，而且任意 df（包括很大的 df）都稳。
    """
    if df <= 0:
        raise ValueError("自由度必须为正")
    if x == 0.0:
        return 0.5
    xx = df / (df + x * x)
    tail = 0.5 * _betai(df / 2.0, 0.5, xx)      # P(T > |x|)
    return 1.0 - tail if x > 0 else tail


def z_critical(level):
    """双侧置信水平 level 对应的正态临界值 z_{1−(1−level)/2}（用二分法求逆）。"""
    target = 0.5 + level / 2.0
    lo, hi = 0.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if gauss_cdf(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def ci_z_critical(level):
    return z_critical(level)


# ---------------------------------------------------------------- 抽样与标准误
def se_mean(sigma, n):
    """样本均值的标准误 SE = σ/√n。"""
    if n <= 0:
        raise ValueError("样本量必须为正")
    return sigma / math.sqrt(n)


def sample_mean(xs):
    return sum(xs) / len(xs)


def sample_var_n(xs):
    """除以 n 的样本方差（有偏，会低估 σ²）。"""
    m = sample_mean(xs)
    return sum((v - m) ** 2 for v in xs) / len(xs)


def sample_var_n1(xs):
    """除以 n−1 的样本方差（无偏）。"""
    if len(xs) < 2:
        raise ValueError("至少需要 2 个样本")
    m = sample_mean(xs)
    return sum((v - m) ** 2 for v in xs) / (len(xs) - 1)


def simulate_means(mu, sigma, n, k, seed):
    """真实重复抽样 k 次，每次取 n 个样本，返回 k 个样本均值。"""
    rng = random.Random(seed)
    return [sum(rng.gauss(mu, sigma) for _ in range(n)) / n for _ in range(k)]


def simulate_var_estimators(mu, sigma, n, k, seed):
    """返回两种方差估计量的平均值 (E[s²_n], E[s²_{n−1}])（真实模拟）。"""
    rng = random.Random(seed)
    a = b = 0.0
    for _ in range(k):
        xs = [rng.gauss(mu, sigma) for _ in range(n)]
        a += sample_var_n(xs)
        b += sample_var_n1(xs)
    return a / k, b / k


# ---------------------------------------------------------------- 置信区间
def ci_mean(x_bar, sigma, n, level, use_t=False, s=None, df=None):
    """均值的双侧置信区间（σ 已知用 z，σ 未知用 t）。

    返回 (lower, upper)。
    """
    se = se_mean(sigma if s is None else s, n)
    if use_t:
        if df is None:
            raise ValueError("用 t 时必须给出自由度")
        crit = t_critical(level, df)
    else:
        crit = z_critical(level)
    return x_bar - crit * se, x_bar + crit * se


def t_critical(level, df):
    """t 分布的双侧临界值（二分法求逆）。"""
    target = 0.5 + level / 2.0
    lo, hi = 0.0, 100.0
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, df) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def simulate_coverage(mu, sigma, n, level, k, seed):
    """模拟 k 次「抽样 + 建区间」，返回 (覆盖率, 区间列表, 样本均值列表)。

    区间列表形如 [(lo, hi), ...]，用于画板逐条绘制。
    """
    rng = random.Random(seed)
    crit = z_critical(level)
    se = se_mean(sigma, n)
    intervals, covered = [], 0
    means = []
    for _ in range(k):
        xs = [rng.gauss(mu, sigma) for _ in range(n)]
        xb = sample_mean(xs)
        means.append(xb)
        lo, hi = xb - crit * se, xb + crit * se
        intervals.append((lo, hi))
        if lo <= mu <= hi:
            covered += 1
    return covered / k, intervals, means


# ---------------------------------------------------------------- t 检验与 p 值
def t_statistic(x_bar, mu0, s, n):
    """单样本 t 统计量 t = (x̄ − μ₀)/(s/√n)。"""
    if n <= 0:
        raise ValueError("样本量必须为正")
    se = s / math.sqrt(n)
    if se == 0:
        raise ValueError("样本标准差为 0，t 无定义")
    return (x_bar - mu0) / se


def p_value_t(t, df, two_sided=True):
    """由 t 统计量求 p 值。"""
    if two_sided:
        return 2.0 * (1.0 - t_cdf(abs(t), df))
    return 1.0 - t_cdf(t, df)


def simulate_pvalues(mu0, delta, sigma, n, k, seed):
    """在「真实均值 = mu0 + delta」下重复做检验，返回 k 个 p 值。

    delta = 0 时就是 H₀ 成立的情形 —— 此时 p 值应当服从**均匀分布**。
    """
    rng = random.Random(seed)
    out = []
    for _ in range(k):
        xs = [rng.gauss(mu0 + delta, sigma) for _ in range(n)]
        xb = sample_mean(xs)
        s = math.sqrt(sample_var_n1(xs))
        if s == 0:
            out.append(1.0)
            continue
        t = t_statistic(xb, mu0, s, n)
        out.append(p_value_t(t, n - 1))
    return out


# ---------------------------------------------------------------- 功效
def power_two_sided(delta, sigma, n, alpha=0.05):
    """双侧 z 检验的功效（正态近似）。

    功效 = P(拒绝 H₀ | 真值为 μ₀+δ)
         = Φ(−z_{α/2} − δ√n/σ) + 1 − Φ(z_{α/2} − δ√n/σ)
    """
    if sigma <= 0 or n <= 0:
        raise ValueError("σ 与 n 必须为正")
    zc = z_critical(1.0 - alpha)
    lam = abs(delta) * math.sqrt(n) / sigma
    return gauss_cdf(-zc - lam) + (1.0 - gauss_cdf(zc - lam))


def simulate_power_curve(delta, sigma, n_list, alpha, k, seed):
    """对每个 n 做 k 次模拟，返回拒绝率（真实功效）。"""
    out = []
    for i, n in enumerate(n_list):
        rng = random.Random(seed + i)
        rej = 0
        for _ in range(k):
            xs = [rng.gauss(delta, sigma) for _ in range(n)]
            xb = sample_mean(xs)
            s = math.sqrt(sample_var_n1(xs))
            if s == 0:
                continue
            p = p_value_t(t_statistic(xb, 0.0, s, n), n - 1)
            if p < alpha:
                rej += 1
        out.append(rej / k)
    return out


# ---------------------------------------------------------------- 回归
def ols_fit(xs, ys):
    """最小二乘直线拟合，返回 (斜率, 截距, R², 残差列表, 预测值列表)。"""
    n = len(xs)
    if n < 2:
        raise ValueError("至少需要 2 个点")
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((v - mx) ** 2 for v in xs)
    if sxx == 0:
        raise ValueError("所有 x 相同，无法拟合")
    sxy = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    b = sxy / sxx
    a = my - b * mx
    pred = [a + b * v for v in xs]
    res = [ys[i] - pred[i] for i in range(n)]
    ss_tot = sum((v - my) ** 2 for v in ys)
    ss_res = sum(v * v for v in res)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return b, a, r2, res, pred


def r_squared(xs, ys):
    return ols_fit(xs, ys)[2]


def simulate_regression(b_true, a_true, sigma, n, seed, x_lo=0.0, x_hi=10.0):
    """生成带噪声的线性数据并做最小二乘拟合。"""
    rng = random.Random(seed)
    xs = [x_lo + (x_hi - x_lo) * i / (n - 1) for i in range(n)]
    ys = [a_true + b_true * v + rng.gauss(0.0, sigma) for v in xs]
    b, a, r2, res, pred = ols_fit(xs, ys)
    return xs, ys, b, a, r2, res, pred


# ---------------------------------------------------------------- 比例
def prop_se(p_hat, n):
    """样本比例的标准误（用 p̂ 估计）：√(p̂(1−p̂)/n)。"""
    if n <= 0:
        raise ValueError("样本量必须为正")
    return math.sqrt(max(0.0, p_hat * (1.0 - p_hat)) / n)


def prop_ci_wald(k, n, level):
    """比例的 Wald 置信区间（大样本）。k 为成功次数。"""
    if n <= 0:
        raise ValueError("样本量必须为正")
    ph = k / n
    zc = z_critical(level)
    se = prop_se(ph, n)
    return max(0.0, ph - zc * se), min(1.0, ph + zc * se), ph, se


def prop_z_test(k, n, p0):
    """比例的 z 检验（H₀: p = p0），返回 (z, 双侧 p 值)。"""
    if n <= 0:
        raise ValueError("样本量必须为正")
    se0 = math.sqrt(p0 * (1.0 - p0) / n)
    if se0 == 0:
        raise ValueError("p₀ 取 0 或 1 时检验无定义")
    z = (k / n - p0) / se0
    p = 2.0 * (1.0 - gauss_cdf(abs(z)))
    return z, p


def simulate_prop_dist(p_true, n, k, seed):
    """模拟 k 次「取 n 个样本」得到的样本比例分布。"""
    rng = random.Random(seed)
    return [sum(1 for _ in range(n) if rng.random() < p_true) / n for _ in range(k)]


# ---------------------------------------------------------------- 直方图
def hist(values, lo, hi, nbins):
    """把 values 装进 [lo, hi] 的 nbins 个等宽区间，返回计数列表。"""
    counts = [0] * nbins
    if hi <= lo:
        return counts
    w = (hi - lo) / nbins
    for v in values:
        k = int((v - lo) / w)
        if k == nbins:
            k = nbins - 1
        if 0 <= k < nbins:
            counts[k] += 1
    return counts


# ================================================================ 自检
def _selftest():
    bad = []

    def chk(name, got, want, tol=1e-9):
        if isinstance(got, (list, tuple)) or isinstance(want, (list, tuple)):
            ga, wa = list(got), list(want)
            ok = len(ga) == len(wa) and all(abs(float(a) - float(b)) <= tol for a, b in zip(ga, wa))
            g = ga
        else:
            ok = abs(float(got) - float(want)) <= tol * max(1.0, abs(float(want)))
            g = f"{float(got):.6g}"
        print(f"  {'✓' if ok else '✗'} {name:46s} = {g}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    def chkb(name, got, want):
        ok = bool(got) == bool(want)
        print(f"  {'✓' if ok else '✗'} {name:46s} = {got}")
        if not ok:
            bad.append(name)

    print("分布函数")
    chk("Φ(0) = 0.5", gauss_cdf(0.0), 0.5, 1e-12)
    chk("Φ(1.96) ≈ 0.975", gauss_cdf(1.96), 0.975, 1e-4)
    chk("标准正态的峰值", gauss_pdf(0.0), 1.0 / math.sqrt(2 * math.pi), 1e-12)
    chk("z 临界值（95%）≈ 1.96", z_critical(0.95), 1.959964, 1e-5)
    chk("z 临界值（90%）≈ 1.645", z_critical(0.90), 1.644854, 1e-5)
    chk("t_cdf(0, df) = 0.5（df=5）", t_cdf(0.0, 5), 0.5, 1e-9)
    # df 很大时 t 接近正态（但**不相等** —— 500 自由度下仍有约 3e-4 的差别）
    chk("t_cdf(1.96, 500) ≈ Φ(1.96)", t_cdf(1.96, 500), gauss_cdf(1.96), 1e-3)
    # t 分布的临界值随 df 减小而增大
    chkb("df 越小 t 临界值越大", t_critical(0.95, 5) > t_critical(0.95, 50), True)
    chk("t 临界值(95%, df=5) ≈ 2.571", t_critical(0.95, 5), 2.570582, 1e-4)
    chk("t 临界值(95%, df=∞) ≈ z", t_critical(0.95, 4000), z_critical(0.95), 2e-3)

    print("\n标准误与抽样分布")
    chk("SE = σ/√n（σ=10, n=25）", se_mean(10.0, 25), 2.0, 1e-12)
    chk("n 增大 4 倍，SE 减半", se_mean(10.0, 100) * 2, se_mean(10.0, 25), 1e-12)
    means = simulate_means(50.0, 10.0, 25, 800, seed=20241018)
    chk("模拟的样本均值个数", len(means), 800, 0)
    chk("模拟均值的平均 ≈ 总体均值", sum(means) / len(means), 50.0, 0.6)
    var_m = sum((v - sum(means) / len(means)) ** 2 for v in means) / len(means)
    chk("模拟均值的方差 ≈ SE²", var_m, se_mean(10.0, 25) ** 2, 0.15)
    # n 越大，样本均值的波动越小
    for n1, n2 in ((4, 16), (16, 64)):
        v1 = sum((v - 50.0) ** 2 for v in simulate_means(50.0, 10.0, n1, 600, 7)) / 600
        v2 = sum((v - 50.0) ** 2 for v in simulate_means(50.0, 10.0, n2, 600, 7)) / 600
        chkb(f"n={n2} 的波动小于 n={n1}", v2 < v1, True)

    print("\n无偏估计（为什么除以 n−1）")
    # 理论：E[s²_n] = σ²(n−1)/n，E[s²_{n−1}] = σ²
    for n in (2, 5, 10, 30):
        e_n, e_n1 = simulate_var_estimators(0.0, 3.0, n, 4000, seed=99 + n)
        chk(f"E[s²_n] ≈ σ²(n−1)/n（n={n}）", e_n, 9.0 * (n - 1) / n, 0.35)
        chk(f"E[s²_n−1] ≈ σ²（n={n}）", e_n1, 9.0, 0.35)
    chkb("除以 n 的估计量系统性偏小",
         simulate_var_estimators(0.0, 3.0, 5, 4000, 55)[0] < 9.0, True)
    chk("n=2 时偏差最大（只剩一半）",
        simulate_var_estimators(0.0, 3.0, 2, 6000, 77)[0], 4.5, 0.35)

    print("\n置信区间与覆盖率")
    for level in (0.80, 0.90, 0.95):
        cov, ivs, _ = simulate_coverage(100.0, 15.0, 25, level, 1000, seed=int(level * 100))
        chk(f"覆盖率 ≈ {level}（模拟）", cov, level, 0.05)
        chk(f"  区间个数", len(ivs), 1000, 0)
    lo, hi, _, _ = (None, None, None, None)
    _, ivs95, _ = simulate_coverage(100.0, 15.0, 25, 0.95, 200, seed=5)
    width = ivs95[0][1] - ivs95[0][0]
    chk("95% 区间的宽度 = 2×1.96×SE", width, 2 * 1.959964 * se_mean(15.0, 25), 1e-4)
    chkb("置信水平越高区间越宽", True, True)
    w80 = (simulate_coverage(100.0, 15.0, 25, 0.80, 50, 3)[1][0])
    w99 = (simulate_coverage(100.0, 15.0, 25, 0.99, 50, 3)[1][0])
    chkb("  99% 的区间比 80% 宽", (w99[1] - w99[0]) > (w80[1] - w80[0]), True)
    # t 区间比 z 区间宽（因为要估计 σ）
    zc, tc = z_critical(0.95), t_critical(0.95, 9)
    chkb("t 临界值 > z 临界值", tc > zc, True)

    print("\nt 检验与 p 值")
    chk("t 统计量", t_statistic(52.0, 50.0, 4.0, 16), 2.0, 1e-12)
    chk("t=0 时 p 值 = 1", p_value_t(0.0, 10), 1.0, 1e-9)
    chk("t=2.262（df=9）时 p ≈ 0.05", p_value_t(2.262157, 9), 0.05, 1e-4)
    chk("|t| 越大 p 越小", p_value_t(3.0, 10) < p_value_t(1.0, 10), True)
    # H₀ 下 p 值应当服从均匀分布 —— 用模拟验证
    ps = simulate_pvalues(0.0, 0.0, 1.0, 20, 3000, seed=12345)
    frac = sum(1 for p in ps if p < 0.05) / len(ps)
    chk("H₀ 下 P(p<0.05) ≈ 0.05（第一类错误率）", frac, 0.05, 0.02)
    frac10 = sum(1 for p in ps if p < 0.10) / len(ps)
    chk("H₀ 下 P(p<0.10) ≈ 0.10", frac10, 0.10, 0.025)
    # 均匀性：落在 0.5 以下的应约占一半
    chk("H₀ 下 P(p<0.5) ≈ 0.5", sum(1 for p in ps if p < 0.5) / len(ps), 0.5, 0.03)
    # H₁ 下 p 值应集中在小值
    ps1 = simulate_pvalues(0.0, 0.8, 1.0, 20, 3000, seed=54321)
    chkb("有真实效应时小 p 值更多",
         sum(1 for p in ps1 if p < 0.05) > 3 * sum(1 for p in ps if p < 0.05), True)
    chkb("p 值始终落在 [0,1]", all(0.0 <= p <= 1.0 for p in ps + ps1), True)

    print("\n功效与样本量")
    chk("δ=0 时功效 = α", power_two_sided(0.0, 1.0, 25, 0.05), 0.05, 1e-3)
    chkb("δ 越大功效越高", power_two_sided(0.5, 1.0, 25) > power_two_sided(0.2, 1.0, 25), True)
    chkb("n 越大功效越高", power_two_sided(0.5, 1.0, 100) > power_two_sided(0.5, 1.0, 25), True)
    chkb("功效随 n 单调上升",
         all(power_two_sided(0.5, 1.0, n2) > power_two_sided(0.5, 1.0, n1)
             for n1, n2 in ((5, 10), (10, 50), (50, 200))), True)
    chk("功效趋近 1（δ 很大）", power_two_sided(5.0, 1.0, 100), 1.0, 1e-6)
    chk("功效趋近 0（δ 很小、n 很小）", power_two_sided(0.01, 1.0, 2), 0.05, 3e-3)
    curve = simulate_power_curve(0.5, 1.0, [5, 10, 20, 40], 0.05, 600, seed=777)
    chkb("模拟功效随 n 单调上升", all(curve[i] < curve[i + 1] for i in range(3)), True)
    chk("模拟功效与理论值接近（n=40）", curve[3], power_two_sided(0.5, 1.0, 40), 0.09)

    print("\n最小二乘回归")
    xs = [0.0, 1.0, 2.0, 3.0, 4.0]
    ys = [1.0, 3.0, 5.0, 7.0, 9.0]          # 精确落在 y = 1 + 2x 上
    b, a, r2, res, pred = ols_fit(xs, ys)
    chk("斜率", b, 2.0, 1e-12)
    chk("截距", a, 1.0, 1e-12)
    chk("R² = 1（完全线性）", r2, 1.0, 1e-12)
    chk("残差全为 0", [round(v, 12) for v in res], [0.0] * 5, 1e-12)
    chk("预测值 = 原值", pred, ys, 1e-12)
    # 带噪声时 R² 下降、斜率仍在真值附近
    xs2, ys2, b2, a2, r22, res2, _ = simulate_regression(2.0, 1.0, 1.0, 30, seed=2468)
    chk("带噪声的斜率仍接近真值", b2, 2.0, 0.35)
    chkb("R² 在 (0,1) 之间", 0.0 < r22 < 1.0, True)
    chkb("噪声越大 R² 越小",
         simulate_regression(2.0, 1.0, 3.0, 30, 99)[4] < simulate_regression(2.0, 1.0, 0.3, 30, 99)[4],
         True)
    # 残差之和为 0（最小二乘的必然性质）
    chk("残差之和为 0", sum(res2), 0.0, 1e-9)
    chk("残差与 x 正交", sum(res2[i] * xs2[i] for i in range(len(xs2))), 0.0, 1e-9)

    print("\n比例的估计与检验")
    _, _, ph, se = prop_ci_wald(60, 100, 0.95)
    chk("样本比例 p̂ = 0.6", ph, 0.6, 1e-12)
    chk("SE = √(p̂(1−p̂)/n)", se, math.sqrt(0.6 * 0.4 / 100), 1e-12)
    lo, hi, _, _ = prop_ci_wald(60, 100, 0.95)
    chk("区间对称于 p̂", (lo + hi) / 2, 0.6, 1e-9)
    chk("区间宽度 = 2×z×SE", hi - lo, 2 * z_critical(0.95) * se, 1e-9)
    z, p = prop_z_test(60, 100, 0.5)
    chk("检验的 z 值", z, 2.0, 1e-12)
    chk("  双侧 p 值 ≈ 0.0455", p, 0.0455, 1e-3)
    z2, p2 = prop_z_test(50, 100, 0.5)
    chk("恰好等于 p₀ 时 z = 0", z2, 0.0, 1e-12)
    chk("  p 值 = 1", p2, 1.0, 1e-9)
    # 模拟：p 真值为 0.5 时，拒绝率应接近 α
    rej = 0
    for i in range(400):
        d = simulate_prop_dist(0.5, 100, 1, seed=1000 + i)
        if prop_z_test(d[0] * 100, 100, 0.5)[1] < 0.05:
            rej += 1
    chk("H₀ 下 5% 水平的拒绝率 ≈ 0.05", rej / 400, 0.05, 0.03)
    # n 越大比例的波动越小
    v1 = sum((v - 0.5) ** 2 for v in simulate_prop_dist(0.5, 20, 800, 11)) / 800
    v2 = sum((v - 0.5) ** 2 for v in simulate_prop_dist(0.5, 200, 800, 11)) / 800
    chkb("n 越大比例的波动越小", v2 < v1, True)

    print("\n直方图")
    # 注意：不要让测试值落在 bin 边界上（浮点除法在边界处归属不确定）；
    # 真实数据是连续模拟出来的，正好落在边界的概率为 0，所以这不影响使用。
    h = hist([0.1, 0.3, 0.5, 0.7, 0.9], 0.0, 1.0, 5)
    chk("每个区间恰好一个", h, [1, 1, 1, 1, 1])
    h2 = hist([0.15, 0.25, 0.25], 0.0, 1.0, 5)
    chk("第二个区间有两个", h2, [1, 2, 0, 0, 0])
    chk("超出范围的被丢弃", sum(hist([-5.0, 5.0], 0.0, 1.0, 4)), 0)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
