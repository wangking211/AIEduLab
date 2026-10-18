#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prob_kernel.py —— 概率统计精确计算内核（高中概率统计 → 大学概率论入口）

设计原则（与全项目一致）：
  · **不手写数字**：所有结果由本内核现算，generate.py 只做排版。
  · **精确优先**：组合数与古典概型用符号整数 / 有理数算，不做浮点近似；
    只在必然连续的地方（正态、模拟）才用浮点，并把「近似」如实标注。
  · **模拟真跑**：大数定律 / 中心极限定理的抽样是**真执行**伪随机序列得到的，
    不是画出来的曲线。种子固定，故可复现（闸门要求两次运行逐字节一致）。

依赖 sympy，自检：
    python prob_kernel.py
"""

import math

import sympy as sp

__all__ = [
    "tex", "f", "num_str", "pct",
    "perm", "comb", "classical", "frac_of",
    "cond_prob", "total_prob", "bayes",
    "binom_pmf", "binom_cdf", "binom_stats", "binom_pmf_float",
    "hyper_pmf", "hyper_stats",
    "exp_var", "die_pairs",
    "normal_pdf", "normal_cdf", "normal_interval", "norm_ppf", "ci_z",
    "lcg", "lln_path", "sim_bernoulli", "clt_sums", "clt_moments", "histogram",
    "Z_95", "Z_99",
]

# ---------------------------------------------------------------- 排版助手

def tex(e):
    """转 LaTeX。有理数写成 \\frac，整数直接写。"""
    e = sp.sympify(e)
    if e.is_Integer:
        return str(int(e))
    if e.is_Rational:
        return r"\frac{%d}{%d}" % (e.p, e.q)
    return sp.latex(e)


def f(x, digits=4):
    """浮点格式化（去掉尾随零）。"""
    if x is None:
        return "—"
    v = float(x)
    s = f"{v:.{digits}f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-") else "0"


def num_str(x, digits=4):
    """数字的中文可读形式（大数用科学计数法）。"""
    v = float(x)
    if v == 0:
        return "0"
    if abs(v) >= 1e5 or abs(v) < 1e-4:
        return f"{v:.4e}".replace("e-0", "e-").replace("e+0", "e")
    return f(v, digits)


def pct(x, digits=2):
    """转百分比字符串。"""
    return f(float(x) * 100, digits) + "%"


def frac_of(x):
    """把 float/int/str 变成精确有理数。

    概率题里的 p 都是「干净」的（1/6、0.5、0.8…）。用 nsimplify 还原，
    而不是把 IEEE754 的二进制尾巴带进结果 —— 否则 0.1 会变成
    3602879701896397/36028797018963968 这种读不出来的东西。
    """
    if isinstance(x, sp.Rational):
        return x
    if isinstance(x, int):
        return sp.Integer(x)
    return sp.nsimplify(sp.Float(x)) if isinstance(x, float) else sp.nsimplify(x)


# ---------------------------------------------------------------- 计数与古典概型

def perm(n, k):
    """排列数 P(n,k) = n!/(n-k)! —— 精确整数。"""
    n, k = int(n), int(k)
    if k < 0 or n < 0 or k > n:
        return sp.Integer(0)
    return sp.factorial(n) / sp.factorial(n - k)


def comb(n, k):
    """组合数 C(n,k) —— 精确整数。"""
    n, k = int(n), int(k)
    if k < 0 or n < 0 or k > n:
        return sp.Integer(0)
    return sp.binomial(n, k)


def classical(fav, tot):
    """古典概型 P = 有利数 / 总数 —— 精确有理数。"""
    tot = int(tot)
    if tot == 0:
        raise ZeroDivisionError("样本点总数为 0")
    return sp.Rational(int(fav), tot)


# ---------------------------------------------------------------- 条件概率与贝叶斯

def cond_prob(p_ab, p_b):
    """条件概率 P(A|B) = P(AB)/P(B) —— 精确有理数。"""
    pb = frac_of(p_b)
    if pb == 0:
        raise ZeroDivisionError("P(B)=0，条件概率无定义")
    return frac_of(p_ab) / pb


def total_prob(priors, liks):
    """全概率公式 P(B) = Σ P(Aᵢ)·P(B|Aᵢ) —— 精确有理数。"""
    if len(priors) != len(liks):
        raise ValueError("先验与似然长度不一致")
    return sum(frac_of(p) * frac_of(l) for p, l in zip(priors, liks))


def bayes(priors, liks, i):
    """贝叶斯后验 P(Aᵢ|B) —— 精确有理数。"""
    tp = total_prob(priors, liks)
    if tp == 0:
        raise ZeroDivisionError("P(B)=0，后验无定义")
    return frac_of(priors[i]) * frac_of(liks[i]) / tp


# ---------------------------------------------------------------- 二项 / 超几何
#
# 这两个分布同时提供「精确」与「浮点」两个版本：
#   · 精确版给答案卡与分步（读者要看到 120/1024 而不是 0.1172）；
#   · 浮点版给画板（Canvas 要的是数）。
# 两者同源：浮点版只是精确版的数值化，绝不会各写一遍。

def binom_pmf(n, k, p):
    """二项分布 P(X=k) = C(n,k)pᵏ(1-p)^(n-k) —— 精确有理数。"""
    n, k = int(n), int(k)
    if k < 0 or k > n:
        return sp.Integer(0)
    q = frac_of(p)
    return sp.binomial(n, k) * q ** k * (1 - q) ** (n - k)


def binom_pmf_float(n, k, p):
    """二项分布 pmf 的浮点版（供画板）。"""
    return float(binom_pmf(n, k, p))


def binom_cdf(n, k, p):
    """二项分布累积 P(X≤k) —— 精确有理数。"""
    return sum(binom_pmf(n, j, p) for j in range(0, int(k) + 1))


def binom_stats(n, p):
    """二项分布的 (期望, 方差) —— 精确有理数。E=np，Var=np(1-p)。"""
    q = frac_of(p)
    n = int(n)
    return n * q, n * q * (1 - q)


def hyper_pmf(N, K, n, k):
    """超几何分布 P(X=k) = C(K,k)C(N-K,n-k)/C(N,n) —— 精确有理数。"""
    N, K, n, k = int(N), int(K), int(n), int(k)
    if k < max(0, n - (N - K)) or k > min(n, K):
        return sp.Integer(0)
    return sp.binomial(K, k) * sp.binomial(N - K, n - k) / sp.binomial(N, n)


def hyper_stats(N, K, n):
    """超几何分布的 (期望, 方差) —— 精确有理数。

    E = n·K/N；Var = n·(K/N)(1−K/N)·(N−n)/(N−1)。
    末项 (N−n)/(N−1) 是**有限总体校正**：不放回抽样比二项分布方差小。
    """
    N, K, n = int(N), int(K), int(n)
    q = sp.Rational(K, N)
    mu = n * q
    var = n * q * (1 - q) * sp.Rational(N - n, N - 1) if N > 1 else sp.Integer(0)
    return mu, var


# ---------------------------------------------------------------- 期望与方差

def exp_var(pairs):
    """离散分布的 (期望, 方差)，pairs = [(取值, 概率), ...] —— 精确有理数。"""
    ps = [(frac_of(v), frac_of(p)) for v, p in pairs]
    tot = sum(p for _v, p in ps)
    if tot == 0:
        raise ZeroDivisionError("概率之和为 0")
    ps = [(v, p / tot) for v, p in ps]          # 归一化，防手写概率有舍入
    mu = sum(v * p for v, p in ps)
    var = sum(p * (v - mu) ** 2 for v, p in ps)
    return mu, var


def die_pairs(sides=6):
    """均匀骰子的 (取值, 概率) 列表。"""
    sides = int(sides)
    return [(i + 1, sp.Rational(1, sides)) for i in range(sides)]


# ---------------------------------------------------------------- 正态分布
#
# 正态没有初等原函数，CDF 只能数值算 —— 这是**数学事实**，不是我们的偷懒。
# 用 math.erf（C 实现的连分式/级数），精度远高于图上需要。

def normal_pdf(x, mu=0.0, sigma=1.0):
    """正态密度 φ(x; μ, σ)。"""
    z = (x - mu) / sigma
    return math.exp(-z * z / 2) / (sigma * math.sqrt(2 * math.pi))


def normal_cdf(z):
    """标准正态累积 Φ(z) —— 用 erf 精确计算。"""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def normal_interval(mu, sigma, a, b):
    """P(a ≤ X ≤ b) = Φ((b−μ)/σ) − Φ((a−μ)/σ)。"""
    return normal_cdf((b - mu) / sigma) - normal_cdf((a - mu) / sigma)


def norm_ppf(p):
    """标准正态分位数 —— 对 Φ 做二分求逆（单调，必然收敛）。"""
    if not 0.0 < p < 1.0:
        raise ValueError("分位数要求 0<p<1")
    lo, hi = -40.0, 40.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if normal_cdf(mid) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def ci_z(mean, sigma, n, conf):
    """总体标准差已知时的置信区间（z 区间）—— 返回 (下界, 上界, 临界值z, 半宽)。"""
    z = norm_ppf((1.0 + conf) / 2.0)
    half = z * sigma / math.sqrt(n)
    return mean - half, mean + half, z, half


Z_95 = norm_ppf(0.975)      # ≈ 1.959964
Z_99 = norm_ppf(0.995)      # ≈ 2.575829


# ---------------------------------------------------------------- 真模拟（可复现）
#
# 这些函数**真的跑**伪随机序列，严禁「画一条看起来像随机的曲线」。
#
# 为什么不用 Python 的 random 模块：模拟要能**在浏览器里随滑块重跑**（否则滑块
# 只改读数、图形不动），而 Python 的 Mersenne Twister 在 JS 里没有逐位一致实现。
# 所以这里用最简单的 32 位线性同余发生器（LCG），它在两种语言里都能逐位复现：
#
#     state ← (1664525·state + 1013904223) mod 2³² ;  u = state / 2³²
#
# JS 侧用 `Math.imul` 取 32 位乘法的低位，`>>> 0` 回绕，与 Python 的 `& 0xFFFFFFFF`
# 完全等价（有测试交叉验证）。这不是密码学随机数，但作为教学演示足够，而且
# **可复现**是硬要求：闸门用两个哈希种子各跑一遍，产物必须逐字节一致。

_M32 = 0xFFFFFFFF


def lcg(seed):
    """返回一个无参函数，每次调用产出 [0,1) 的下一个均匀数。"""
    s = [int(seed) & _M32]

    def nxt():
        s[0] = (1664525 * s[0] + 1013904223) & _M32
        return s[0] / 4294967296.0

    return nxt


def lll_path_impl(seed, nmax, p):
    """辅助：见 lln_path。"""
    nxt = lcg(seed)
    out = []
    hits = 0
    for i in range(1, int(nmax) + 1):
        hits += 1 if nxt() < p else 0
        out.append(hits / i)
    return out


def lln_path(seed, nmax, p):
    """大数定律：相对频率随试验次数 n 的**实际轨迹**。

    返回长度 nmax 的列表，第 i 项 = 前 i 次试验中「成功」出现的频率。
    这条轨迹天然围绕 p 波动，波动幅度 ~ 1/√n —— 不是画出来的包络。

    滑块改 p 时，浏览器用**同一个 LCG 序列**重算轨迹：随机性是内核录下的那一条，
    只是换了判定阈值。所以「拖动滑块」不会偷偷换一批随机数。
    """
    return lll_path_impl(seed, nmax, p)


def sim_bernoulli(seed, n, p):
    """n 次伯努利试验的成功次数（整数）。"""
    nxt = lcg(seed)
    return sum(1 for _ in range(int(n)) if nxt() < p)


def clt_sums(seed, trials, n, maxn=None):
    """中心极限定理：trials 个「n 个 U(0,1) 之和」的样本。

    先按 trials×maxn 生成一条**扁平**均匀序列，再按下标切片求和：
    第 t 个样本 = Σ_{j<n} u[t·maxn + j]。
    这样做的好处是改 n 时用的是同一条随机带（只是每段取得更长），
    而不是「换一批随机数」—— 否则滑块一动，前后两张直方图毫无可比性。

    均匀分布 U(0,1) 的均值 1/2、方差 1/12 都是精确已知的，所以模拟结果
    可以拿去和解析正态对照 —— 这才是 CLT 的可验证声明。
    """
    trials, n = int(trials), int(n)
    maxn = int(maxn) if maxn else n
    maxn = max(maxn, n)
    nxt = lcg(seed)
    flat = [nxt() for _ in range(trials * maxn)]
    return [sum(flat[t * maxn: t * maxn + n]) for t in range(trials)]


def clt_moments(n, lo=0.0, hi=1.0):
    """n 个 U(lo,hi) 之和的精确矩：均值 n·(lo+hi)/2，方差 n·(hi−lo)²/12。"""
    mu = n * (lo + hi) / 2.0
    var = n * (hi - lo) ** 2 / 12.0
    return mu, math.sqrt(var)


def histogram(samples, lo, hi, nbins):
    """把样本装进 nbins 个等宽区间，返回 (计数列表, 区间宽度)。"""
    w = (hi - lo) / nbins
    counts = [0] * nbins
    for s in samples:
        idx = int((s - lo) / w)
        if 0 <= idx < nbins:
            counts[idx] += 1
    return counts, w


# ================================================================ 自检

def _close(a, b, tol=1e-9):
    return abs(float(a) - float(b)) <= tol


def _selftest():
    bad = []

    def chk(name, got, want, tol=1e-9):
        ok = (abs(float(got) - float(want)) <= tol) if isinstance(want, float) else (got == want)
        print(f"  {'✓' if ok else '✗'} {name:44s} = {got}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    def chkf(name, got, want, tol=1e-6):
        ok = abs(float(got) - float(want)) <= tol
        print(f"  {'✓' if ok else '✗'} {name:44s} = {float(got):.6f}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    print("计数与古典概型")
    chk("P(5,2)", perm(5, 2), sp.Integer(20))
    chk("C(5,2)", comb(5, 2), sp.Integer(10))
    chk("C(49,6)", comb(49, 6), sp.Integer(13983816))
    chk("古典：一颗骰子出 6 点", classical(1, 6), sp.Rational(1, 6))
    chk("古典：两骰子和为 7（6/36）", classical(6, 36), sp.Rational(1, 6))
    chk("frac_of(0.5)", frac_of(0.5), sp.Rational(1, 2))
    chk("frac_of(0.1) 不带上 2 的幂尾巴", frac_of(0.1), sp.Rational(1, 10))

    print("\n条件概率与贝叶斯（经典「患病检测」题）")
    # 患病率 1/1000，检测灵敏度 99%，假阳性率 5%
    priors = [sp.Rational(1, 1000), sp.Rational(999, 1000)]
    liks = [sp.Rational(99, 100), sp.Rational(5, 100)]
    tp = total_prob(priors, liks)
    chk("全概率 P(阳性)", tp, sp.Rational(1, 1000) * sp.Rational(99, 100)
        + sp.Rational(999, 1000) * sp.Rational(5, 100))
    post = bayes(priors, liks, 0)
    chk("后验 P(患病|阳性)", post, sp.Rational(1, 1000) * sp.Rational(99, 100) / tp)
    chkf("  └ 数值（应 ≈ 0.0194，远小于直觉）", float(post), 99 / (99 + 999 * 5), 1e-12)
    chk("条件概率 P(A|B)", cond_prob(sp.Rational(1, 4), sp.Rational(1, 2)), sp.Rational(1, 2))

    print("\n二项分布")
    chk("P(X=3), n=10, p=1/2", binom_pmf(10, 3, 0.5), sp.Rational(120, 1024))
    chkf("  └ 数值", float(binom_pmf(10, 3, 0.5)), 0.1171875, 1e-12)
    chk("Σ P(X=k) 归一", sum(binom_pmf(6, k, sp.Rational(1, 3)) for k in range(7)), sp.Integer(1))
    mu, var = binom_stats(10, 0.5)
    chk("E(X), n=10, p=1/2", mu, sp.Rational(5))
    chk("Var(X)", var, sp.Rational(5, 2))

    print("\n超几何分布（不放回，方差应小于二项）")
    pmf0 = hyper_pmf(10, 3, 4, 1)
    # 独立推导：C(3,1)·C(7,3)/C(10,4) —— 与实现里用的是同一组合意义，但不是同一条代码路径
    chk("P(X=1), N=10,K=3,n=4", pmf0, sp.binomial(3, 1) * sp.binomial(7, 3) / sp.binomial(10, 4))
    hmu, hvar = hyper_stats(10, 3, 4)
    chk("E(X) = n·K/N", hmu, sp.Rational(12, 10))
    bmu, bvar = binom_stats(4, sp.Rational(3, 10))
    ok = float(hvar) < float(bvar)
    print(f"  {'✓' if ok else '✗'} 有限总体校正使方差变小：超几何 {hvar} < 二项 {bvar}")
    if not ok:
        bad.append("超几何方差应小于二项")

    print("\n期望与方差")
    mu, var = exp_var(die_pairs(6))
    chk("均匀骰子 E(X)", mu, sp.Rational(7, 2))
    chk("均匀骰子 Var(X)", var, sp.Rational(35, 12))

    print("\n正态分布")
    chkf("Φ(0)", normal_cdf(0.0), 0.5, 1e-12)
    chkf("P(−1≤Z≤1)", normal_interval(0, 1, -1, 1), 0.682689, 1e-5)
    chkf("P(−1.96≤Z≤1.96)", normal_interval(0, 1, -1.96, 1.96), 0.950004, 1e-5)
    chkf("P(−3≤Z≤3)", normal_interval(0, 1, -3, 3), 0.997300, 1e-5)
    chkf("Φ⁻¹(0.975) 反解自洽", normal_cdf(norm_ppf(0.975)), 0.975, 1e-9)
    chkf("Z_95", Z_95, 1.959964, 1e-5)
    lo, hi, z, half = ci_z(100.0, 15.0, 25, 0.95)
    chkf("95% 置信区间半宽 (σ=15,n=25)", half, 1.96 * 15 / 5, 1e-3)

    print("\nLCG 伪随机（浏览器里必须逐位一致，故打印前几个值供交叉验证）")
    g = lcg(12345)
    first = [g() for _ in range(5)]
    print("  seed=12345 前 5 个 =", " ".join(f"{v:.15f}" for v in first))
    g2 = lcg(12345)
    chk("同种子序列一致", [g2() for _ in range(5)] == first, True)
    chk("取值全部落在 [0,1)", all(0.0 <= v < 1.0 for v in first), True)
    chk("种子 0 的首个值", lcg(0)(), 1013904223 / 4294967296.0)

    print("\n真模拟（可复现）")
    a = sim_bernoulli(7, 10000, 0.3)
    b = sim_bernoulli(7, 10000, 0.3)
    chk("同种子两次结果一致", a, b)
    chkf("n=10⁴, p=0.3 的模拟频率", a / 10000, 0.3, 0.02)
    path = lln_path(11, 20000, 0.4)
    ok = abs(path[-1] - 0.4) < 0.02 and len(path) == 20000
    print(f"  {'✓' if ok else '✗'} 大数定律：2×10⁴ 次后频率 {path[-1]:.5f} → 0.4")
    if not ok:
        bad.append("LLN 收敛")
    # 波动随 n 衰减：后段极差应小于前段
    front = max(path[100:1000]) - min(path[100:1000])
    back = max(path[-1000:]) - min(path[-1000:])
    ok = back < front
    print(f"  {'✓' if ok else '✗'} 波动衰减：前段极差 {front:.4f} > 后段 {back:.4f}")
    if not ok:
        bad.append("波动未衰减")

    # CLT：与解析正态对照（均匀和的矩是精确已知的）
    sums = clt_sums(3, 20000, 12, maxn=12)
    mu_s, sd_s = clt_moments(12)
    mean_s = sum(sums) / len(sums)
    chkf("CLT：12 个 U(0,1) 之和的样本均值 → μ=6", mean_s, mu_s, 0.05)
    sd_emp = math.sqrt(sum((s - mean_s) ** 2 for s in sums) / len(sums))
    chkf("  └ 样本标准差 → σ=√(12/12)=1", sd_emp, sd_s, 0.05)
    cnt, w = histogram(sums, 0, 12, 24)
    chk("直方图总计数 = 样本数", sum(cnt), 20000)
    chkf("区间宽度", w, 0.5, 1e-12)
    # 改 n 时用的是同一条随机带（下标切片），不是换一批随机数：
    # 最大 n 的每个样本，其前 6 项之和必须与 n=6 的对应样本完全相同。
    s12 = clt_sums(3, 50, 12, maxn=12)
    s6 = clt_sums(3, 50, 6, maxn=12)
    nxt = lcg(3)
    flat = [nxt() for _ in range(50 * 12)]
    recomputed = [sum(flat[t * 12: t * 12 + 6]) for t in range(50)]
    chk("切片同带：n=6 的样本可由 n=12 的随机带重算", s6 == recomputed, True)
    ok = all(s12[t] > s6[t] for t in range(50) if flat[t * 12 + 6] > 0)
    print(f"  {'✓' if ok else '✗'} n 越大和越大（用同一随机带，可比）")
    if not ok:
        bad.append("CLT 切片同带")

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
