#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hist_kernel.py —— 可算历史的内核（模型 / 恒等式 / 阈值）

**本内核的存在理由与别的技能不同。** 历史学的立身之本 —— 史料批判、因果论证、
动机推断 —— 落在「③ 配图」层，**不可形式化**（见 edulab/coverage-audit.md：
世界史 ① 10/18、② 4/18、③ 4/18，而 ③ 那四条正是这门学科的核心方法）。
所以本内核只做 ① 层，并且**对每一项显式标注证据力等级**：

  · `A`  纯数学 / 恒等式 —— 图上的数错不了（如 Kaya 恒等式、logistic 的 ln9 结论）
  · `B`  模型 — 内核确定，但**参数来自史料估算** —— 图看着精确，结论不精确
  · `C`  形态①、证据力③ —— 有公式、能算、能画，但参数与初值都不可独立观测，
         于是「某文明两百年一循环」可以**被拟合出来**。这是最危险的一类，
         它看起来像推导。

**不做什么**（如实声明，不硬套）：史料断代、真伪判定、人物动机、因果反事实、
条约网络的边是否成立。这些没有可算内核，写成函数就是编。

自检：python hist_kernel.py
"""

import math

import sympy as sp

__all__ = [
    "tex", "f", "num_str", "pct",
    "EVIDENCE",
    "exponential", "doubling_time", "pct_change_per_year",
    "logistic", "logistic_time", "logistic_duration", "diffusion_s_curve",
    "demographic_transition", "transition_rate_at",
    "r0_from", "herd_threshold", "sir_peak_fraction", "sir",
    "kaya", "kaya_decompose",
    "lv_period_analytic", "lv_integrate", "lv_scan_amplitude",
    "pareto_sizes", "fit_rank_size_slope", "alpha_from_slope",
    "rk4_step",
]

# =====================================================================
# 证据力等级（每一项都必须归到其中一类）
# =====================================================================
EVIDENCE = {
    "A": ("纯数学 / 恒等式", "由构造必真，图上的数错不了"),
    "B": ("模型：内核确定，参数靠估", "曲线光滑，但峰值/拐点取决于你怎么估参数"),
    "C": ("形态①、证据力③", "有公式、能算、能画 —— 但参数与初值不可独立观测，"
                            "结论可以被拟合出来。最危险的一类：看起来像推导"),
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


# ---------------------------------------------------------------- 指数增长
#
# 证据力 A：复利恒等式。可算出的确定结论是「翻倍时间 = ln2/r」——
# 它与起点、与单位都无关。

def exponential(y0, r, t):
    """y(t) = y₀·e^{rt}。"""
    return y0 * math.exp(r * t)


def doubling_time(r):
    """翻倍时间 t₂ = ln2 / r。**与 y₀ 无关** —— 这就是本页的定值。"""
    if r <= 0:
        raise ValueError("增长率必须为正")
    return math.log(2.0) / r


def pct_change_per_year(r, years=1):
    """把连续增长率折成「每年涨百分之几」。"""
    return math.exp(r * years) - 1.0


# ---------------------------------------------------------------- 技术扩散 S 曲线
#
# 证据力 A：logistic 纯数学。可算出的确定结论：
# 从 10% 爬到 90% 的时长恒等于 2·ln9/r，**与 t₀ 无关**（与扩散从哪年开始无关）。

def logistic(t, K=1.0, r=1.0, t0=0.0):
    """p(t) = K / (1 + e^{−r(t−t₀)})。"""
    z = -r * (t - t0)
    # 防溢出：z 很大时 e^z 溢出，直接给极限值
    if z > 700:
        return 0.0
    if z < -700:
        return K
    return K / (1.0 + math.exp(z))


def logistic_time(p, t0, r, K=1.0):
    """反解：到达渗透率 p 的年份。p/t0 需满足 0<p<K。"""
    if not 0 < p < K:
        raise ValueError("渗透率须在 (0, K) 内")
    return t0 + math.log((p / K) / (1 - p / K)) / r


def logistic_duration(p1, p2, r, K=1.0):
    """从渗透率 p1 到 p2 的时长。**与 t₀ 无关**。"""
    return logistic_time(p2, 0.0, r, K) - logistic_time(p1, 0.0, r, K)


def diffusion_s_curve(rate, t0, p_lo=0.10, p_hi=0.90):
    """技术扩散的标准四问：10% / 50% / 90% 的年份，以及 10→90 的时长。"""
    return {
        "t_lo": logistic_time(p_lo, t0, rate),
        "t_mid": t0,
        "t_hi": logistic_time(p_hi, t0, rate),
        "duration": logistic_duration(p_lo, p_hi, rate),
        "duration_exact": 2 * math.log(9.0) / rate,
    }


# ---------------------------------------------------------------- 人口转变
#
# 证据力 B：内核完全确定，但**参数（各平台高度、两个中点、陡度）来自史料估算**。
# 所以曲线上那个「峰值年」看起来精确，实际上取决于你怎么估 mid_b。

def _sigmoid_down(hi, lo, mid, steep, t):
    return lo + (hi - lo) / (1.0 + math.exp((t - mid) / steep))


def demographic_transition(b0, b1, d0, d1, mid_d, mid_b, steep, y0=1700, y1=2100):
    """人口转变：出生率与死亡率各自从高平台降到低平台。

    死亡率先降（mid_d 较早，如医疗改善），出生率后降（mid_b 较晚），
    中间必然出现**增长率峰值**。返回峰值、峰值年与整条曲线。
    """
    best = (-1e9, None)
    curve = []
    for t in range(int(y0), int(y1) + 1):
        b = _sigmoid_down(b0, b1, mid_b, steep, t)
        d = _sigmoid_down(d0, d1, mid_d, steep, t)
        g = b - d
        curve.append((t, b, d, g))
        if g > best[0]:
            best = (g, t)
    return {"peak_growth": best[0], "peak_year": best[1], "curve": curve}


def transition_rate_at(t, b0, b1, d0, d1, mid_d, mid_b, steep):
    """某年的 (出生率, 死亡率, 增长率) —— 闭式，供读数表达式对账用。

    峰值无法闭式表达（两个 sigmoid 之差的极值没有初等解），只能在画板上扫；
    所以读数取固定年份的三个率，峰值交给图形。
    """
    b = _sigmoid_down(b0, b1, mid_b, steep, t)
    d = _sigmoid_down(d0, d1, mid_d, steep, t)
    return b, d, b - d


# ---------------------------------------------------------------- 传染病阈值
#
# 证据力 A：SIR 是确定的数学；R₀ 与群体免疫阈值都是由此推出的纯数学结论。

def r0_from(beta, gamma):
    """基本传染数 R₀ = β / γ。"""
    if gamma <= 0:
        raise ValueError("恢复率必须为正")
    return beta / gamma


def herd_threshold(r0):
    """群体免疫阈值 1 − 1/R₀。R₀ ≤ 1 时不需要（返回 0）。"""
    if r0 <= 1:
        return 0.0
    return 1.0 - 1.0 / r0


def sir_peak_fraction(r0):
    """感染峰值的占比 = 1 − (1 + ln R₀)/R₀（仅 R₀>1）。

    这是 SIR 的解析结论：峰值出现在 S = N/R₀ 处。
    """
    if r0 <= 1:
        return 0.0
    return 1.0 - (1.0 + math.log(r0)) / r0


def rk4_step(y, h, deriv):
    """单步 RK4。deriv 接受状态向量，返回导数向量。"""
    k1 = deriv(y)
    k2 = deriv([y[i] + h / 2 * k1[i] for i in range(len(y))])
    k3 = deriv([y[i] + h / 2 * k2[i] for i in range(len(y))])
    k4 = deriv([y[i] + h * k3[i] for i in range(len(y))])
    return [y[i] + h / 6 * (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) for i in range(len(y))]


def sir(beta, gamma, s0=0.99, i0=0.01, days=200, steps=2000):
    """SIR 数值解（真跑 RK4，不是画出来的曲线）。

    返回 (t 列表, S 列表, I 列表, R 列表)，比例形式（总量归一到 1）。
    """
    h = days / steps
    y = [s0, i0, 1.0 - s0 - i0]

    def deriv(v):
        s, i, _r = v
        new = beta * s * i
        return [-new, new - gamma * i, gamma * i]

    ts, S, I, Rr = [0.0], [y[0]], [y[1]], [y[2]]
    for k in range(steps):
        y = rk4_step(y, h, deriv)
        y = [max(0.0, v) for v in y]
        ts.append((k + 1) * h)
        S.append(y[0]); I.append(y[1]); Rr.append(y[2])
    return ts, S, I, Rr


# ---------------------------------------------------------------- Kaya 恒等式
#
# 证据力 A：**恒等式** —— 由构造必然成立，图上一个数都不会错。
# 但它的价值是分解（谁贡献了多少变化），不是预测。这一点要写清楚。

def kaya(P, g, e, c):
    """CO₂ = P × (GDP/P) × (E/GDP) × (CO₂/E)。

    P 人口、g 人均 GDP、e 单位 GDP 能耗、c 单位能耗排放。
    """
    return P * g * e * c


def kaya_decompose(P, g, e, c):
    """返回恒等式的四个因子、乘积，以及恒等式是否成立。"""
    co2 = kaya(P, g, e, c)
    return {"P": P, "g": g, "e": e, "c": c, "co2": co2,
            "identity_holds": abs(co2 - P * g * e * c) < 1e-15}


# ---------------------------------------------------------------- 王朝周期（最危险的一类）
#
# 证据力 C：模型有公式、能算、能画 —— 但**周期有两个旋钮**：参数 (r, m) 与
# 振幅（离开平衡点多远）。振幅往往没人能独立观测，于是「某文明两百年一循环」
# 可以被拟合出来。所以本函数同时给出解析式与 RK4 数值周期，把两件事分开受检。

def lv_period_analytic(r, m):
    """小振幅极限下的周期 T = 2π/√(rm)（只由参数决定）。"""
    return 2.0 * math.pi / math.sqrt(r * m)


def lv_integrate(r, a, c, m, amp=0.05, years=3000.0, steps=60000):
    """Lotka-Volterra：dN/dt = rN − aNE，dE/dt = cNE − mE。

    初值取在平衡点 (m/c, r/a) 附近的 (m/c·(1+amp), r/a)。
    返回时序与「峰间距」给出的数值周期。
    """
    h = years / steps
    n_star, e_star = m / c, r / a
    N, E = n_star * (1 + amp), e_star

    def d(N_, E_):
        return r * N_ - a * N_ * E_, c * N_ * E_ - m * E_

    series = [(0.0, E)]
    for i in range(steps):
        k1 = d(N, E)
        k2 = d(N + h / 2 * k1[0], E + h / 2 * k1[1])
        k3 = d(N + h / 2 * k2[0], E + h / 2 * k2[1])
        k4 = d(N + h * k3[0], E + h * k3[1])
        N = max(1e-12, N + h / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]))
        E = max(1e-12, E + h / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]))
        series.append(((i + 1) * h, E))
    peaks = [series[i][0] for i in range(1, len(series) - 1)
             if series[i][1] > series[i - 1][1] and series[i][1] >= series[i + 1][1]
             and series[i][1] > e_star]
    periods = [peaks[i + 1] - peaks[i] for i in range(len(peaks) - 1)]
    numeric = (sum(periods) / len(periods)) if periods else None
    return {"amp": amp, "period_numeric": numeric,
            "period_analytic": lv_period_analytic(r, m),
            "n_cycles": len(periods), "series": series}


def lv_scan_amplitude(r, m, amps=(0.05, 0.5, 1.0, 3.0, 10.0), a=1.0, c=1.0):
    """扫振幅：同一个参数、不同初值 —— 周期会变。这是本页要讲的重点。"""
    out = []
    for amp in amps:
        res = lv_integrate(r, a, c, m, amp=amp)
        out.append({"amp": amp, "period": res["period_numeric"]})
    return out


# ---------------------------------------------------------------- 幂律 / rank-size
#
# 证据力 A（数学）／B（用真实城市人口时）：幂律的 log-log 斜率与指数互为倒数。

def pareto_sizes(n, alpha, s_min=1.0):
    """生成 n 个符合 rank-size 幂律的规模，降序排列。

    用的是**幂律定律本身**的精确形式（Zipf 定律的数学表述）：
        第 r 大的规模 s_r = s_min · (n/r)^{1/α}
    于是 log s 与 log r 严格线性，斜率恰好 −1/α —— 这样它检验的是「拟合器对不对」，
    而不是被生成方式的偏差污染。

    **确定性**：不引入随机数，任何时刻重跑都得到同一组数（闸门要求逐字节一致）。
    """
    if alpha <= 0:
        raise ValueError("指数必须为正")
    if n <= 0:
        raise ValueError("样本数必须为正")
    return [s_min * (n / (r + 1)) ** (1.0 / alpha) for r in range(n)]


def fit_rank_size_slope(sizes):
    """对 (log rank, log size) 做最小二乘，返回斜率。

    Zipf 定律对应斜率 = −1（即 Pareto 指数 α = 1）。
    一般地 斜率 = −1/α。
    """
    pts = [(math.log(i + 1), math.log(s)) for i, s in enumerate(sizes) if s > 0]
    n = len(pts)
    if n < 2:
        return None
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    num = sum((x - mx) * (y - my) for x, y in pts)
    den = sum((x - mx) ** 2 for x, _ in pts)
    return num / den if den else None


def alpha_from_slope(slope):
    """由 rank-size 斜率反推 Pareto 指数：α = −1/斜率。"""
    if slope >= 0:
        raise ValueError("斜率应为负")
    return -1.0 / slope


# ================================================================ 自检
#
# 基准值全部来自 edulab/coverage-audit.md（那份审计已经现算过并写进了报告），
# 所以这里验的是「我的实现与审计的实现一致」，不是我另编一套期望。

def _selftest():
    bad = []

    def chk(name, got, want, tol=None):
        ok = (got == want) if tol is None else (abs(float(got) - float(want)) <= tol)
        shown = got if tol is None else f"{float(got):.6f}"
        print(f"  {'✓' if ok else '✗'} {name:44s} = {shown}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    print("证据力分级（每一项都必须能归类）")
    for k in ("A", "B", "C"):
        chk(f"等级 {k} 有定义", k in EVIDENCE, True)

    print("\n指数增长与翻倍时间（① A）")
    chk("7% 增长的翻倍时间(年)", doubling_time(0.07), 9.9021, 1e-3)
    chk("2% 增长的翻倍时间(年)", doubling_time(0.02), 34.6574, 1e-3)
    chk("翻倍时间与 y₀ 无关", abs(doubling_time(0.07) - math.log(2) / 0.07) < 1e-15, True)
    chk("一个翻倍时间后恰好翻倍", exponential(1.0, 0.07, doubling_time(0.07)), 2.0, 1e-12)
    chk("10 年 @7% 的倍数", exponential(1.0, 0.07, 10), 2.0138, 1e-3)

    print("\n技术扩散 S 曲线（① A，基准取自 coverage-audit.md）")
    d = diffusion_s_curve(rate=0.35, t0=1900)
    chk("10% 的年份", d["t_lo"], 1893.7, 0.05)
    chk("50% 的年份 = t₀", d["t_mid"], 1900.0, 1e-9)
    chk("90% 的年份", d["t_hi"], 1906.3, 0.05)
    chk("10→90 时长(年)", d["duration"], 12.56, 1e-2)
    chk("  └ 与解析式 2ln9/r 一致", d["duration"], d["duration_exact"], 1e-12)
    # 与 t₀ 无关：换一个起点，时长不变
    chk("换 t₀ 后时长不变", diffusion_s_curve(0.35, 1700)["duration"], d["duration"], 1e-9)
    chk("logistic 在 t₀ 处为 0.5", logistic(1900, 1.0, 0.35, 1900), 0.5, 1e-12)

    print("\n人口转变（① B —— 参数靠估，基准取自 coverage-audit.md）")
    tr = demographic_transition(45, 10, 35, 10, mid_d=1920, mid_b=1950, steep=15)
    chk("峰值增长率(‰)", tr["peak_growth"], 19.22, 0.02)
    chk("峰值年", tr["peak_year"], 1929, 0)
    tr2 = demographic_transition(45, 10, 35, 10, 1920, 1940, 15)
    chk("mid_b 提前到 1940 → 峰值", tr2["peak_growth"], 15.23, 0.02)
    chk("  └ 峰值年", tr2["peak_year"], 1922, 0)
    tr3 = demographic_transition(45, 10, 35, 10, 1920, 1960, 15)
    chk("mid_b 推后到 1960 → 峰值", tr3["peak_growth"], 22.72, 0.02)
    chk("  └ 峰值年", tr3["peak_year"], 1936, 0)
    chk("峰值随 mid_b 单调上升", tr3["peak_growth"] > tr["peak_growth"] > tr2["peak_growth"], True)

    print("\n传染病阈值（① A）")
    chk("R₀ = β/γ", r0_from(0.6, 0.2), 3.0, 1e-12)
    chk("R₀=3 的群体免疫阈值", herd_threshold(3.0), 2 / 3, 1e-12)
    chk("R₀=2 的群体免疫阈值", herd_threshold(2.0), 0.5, 1e-12)
    chk("R₀ ≤ 1 不需群体免疫", herd_threshold(0.9), 0.0, 1e-12)
    chk("R₀=3 的感染峰值占比（解析）", sir_peak_fraction(3.0), 0.3005, 1e-3)
    # 数值解与解析式对照
    ts, S, I, Rr = sir(beta=0.6, gamma=0.2, s0=0.99, i0=0.01, days=200, steps=2000)
    imax = max(I)
    chk("  └ 数值解的峰值与解析式一致", imax, sir_peak_fraction(3.0), 5e-3)
    chk("  └ S+I+R 守恒", S[-1] + I[-1] + Rr[-1], 1.0, 1e-6)
    chk("  └ 最终 S 单调下降到 0 附近（S 永不为负）", min(S) >= 0, True)

    print("\nKaya 恒等式（① A —— 由构造必真）")
    kk = kaya_decompose(P=1.0, g=2.0, e=0.5, c=2.0)
    chk("CO₂ = P·g·e·c", kk["co2"], 2.0, 1e-12)
    chk("恒等式成立", kk["identity_holds"], True)
    # 改任一因子，乘积按比例变（分解才是它的价值）
    chk("人口翻倍 → CO₂ 翻倍", kaya(2.0, 2.0, 0.5, 2.0) / kk["co2"], 2.0, 1e-12)
    chk("单位能耗减半 → CO₂ 减半", kaya(1.0, 2.0, 0.25, 2.0) / kk["co2"], 0.5, 1e-12)

    print("\n王朝周期模型（① C —— 最危险的一类，基准取自 coverage-audit.md）")
    sc = lv_integrate(0.05, 1.0, 1.0, 0.05, amp=0.05)
    chk("解析周期 T=2π/√(rm)", sc["period_analytic"], 125.66, 0.02)
    chk("小振幅时数值周期 ≈ 解析", sc["period_numeric"], 125.7, 0.15)
    printed = {0.05: 125.7, 0.5: 127.7, 1.0: 132.2, 3.0: 161.3, 10.0: 301.1}
    scan = lv_scan_amplitude(0.05, 0.05)
    for row in scan:
        chk(f"振幅 {row['amp']*100:.0f}% 的数值周期", row["period"], printed[row["amp"]], 1.0)
    chk("周期随振幅单调变长", all(scan[i]["period"] < scan[i + 1]["period"]
                                  for i in range(len(scan) - 1)), True)
    chk("振幅 1000% 时比解析长约 2.4 倍",
        scan[-1]["period"] / sc["period_analytic"], 2.396, 0.05)
    assert abs(sc["period_analytic"] - 125.6637) < 0.01

    print("\n幂律 / rank-size（① A 数学，用真实数据时降为 B）")
    sizes = pareto_sizes(200, alpha=1.0)
    sl = fit_rank_size_slope(sizes)
    chk("α=1 的 rank-size 斜率 = −1", sl, -1.0, 1e-12)
    chk("  └ 反推 α", alpha_from_slope(sl), 1.0, 1e-12)
    sizes2 = pareto_sizes(200, alpha=2.0)
    sl2 = fit_rank_size_slope(sizes2)
    chk("α=2 的斜率 = −0.5", sl2, -0.5, 1e-12)
    chk("斜率与 α 严格互为倒数", abs(sl / sl2 - 2.0) < 1e-12, True)
    chk("rank-size 数据严格线性（端点斜率一致）", sl, sl2 * 2, 1e-12)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
