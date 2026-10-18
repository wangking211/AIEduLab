#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
signal_kernel.py —— 信号与系统内核（大学二年级，按 MIT 6.003 组织）

覆盖：
  · 连续卷积：矩形与矩形卷积得到三角形（滑动窗口的几何）
  · 离散卷积：序列逐项相乘求和（真跑，结果是精确整数序列）
  · 傅里叶级数：方波的部分和逼近与 **Gibbs 现象**（过冲极限 2Si(π)/π）
  · 采样定理与混叠：采样率不足时高频被折到低频
  · 时宽频宽积：矩形脉冲与其频谱，**乘积恒为 1**
  · 频率响应：RC 低通的幅频与相频，截止频率处 |H| = 1/√2
  · 离散系统：一阶系统的极点、脉冲响应与稳定性（|a| < 1）

设计原则（与全项目一致）：
  · **不手写数字**：所有结果由本内核现算。
  · **求和真跑**：离散卷积、部分和、级数极限都由积分/求和实际算出；
    凡有解析式的一律与解析式对照（自检里逐条比）。
  · 自检：python signal_kernel.py
"""

import cmath
import math

import sympy as sp

__all__ = [
    "tex", "f", "num_str",
    "rect", "tri", "conv_rect_rect",
    "discrete_conv",
    "square_partial", "gibbs_limit", "square_jump",
    "aliased_freq", "sampling_rate_ok",
    "sinc", "rect_spectrum", "mainlobe_width",
    "rc_cutoff", "rc_mag", "rc_phase_deg", "rc_H",
    "disc_impulse", "disc_stable", "disc_pole", "disc_conv_system",
]


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


# ---------------------------------------------------------------- 连续卷积
#
# 让 x(t) = g(t) = rect(t)（宽 1、关于 0 对称）。则 (x*g)(t) 是底宽 2、
# 顶点 1（在 t=0）的三角形。

def rect(t, half=0.5):
    """宽度 2·half、关于原点对称的矩形脉冲。"""
    return 1.0 if abs(t) <= half else 0.0


def tri(t, half=1.0):
    """底宽 2·half、顶点 1 的三角脉冲。"""
    if abs(t) >= half:
        return 0.0
    return 1.0 - abs(t) / half


def conv_rect_rect(t, half=0.5):
    """两个等宽矩形脉冲的卷积（解析结果：三角形）。

    几何含义：(x*g)(t) = ∫ x(τ)g(t−τ)dτ 就是两个函数**重叠面积**随 t 的变化。
    重叠长度从 0 增到 1（宽 2·half）再回落到 0，所以面积是三角形。
    """
    return tri(t, 2.0 * half)


# ---------------------------------------------------------------- 离散卷积

def discrete_conv(x, h):
    """离散卷积 y[n] = Σ_k x[k]·h[n−k] —— **真跑**，结果是精确整数/有理数。

    对长度为 Lx、Lh 的序列，输出长度是 Lx+Lh−1。
    """
    x = [sp.nsimplify(v) for v in x]
    h = [sp.nsimplify(v) for v in h]
    n_out = len(x) + len(h) - 1
    y = []
    for n in range(n_out):
        s = sp.Integer(0)
        for k in range(len(x)):
            j = n - k
            if 0 <= j < len(h):
                s += x[k] * h[j]
        y.append(sp.simplify(s))
    return y


# ---------------------------------------------------------------- 傅里叶级数
#
# 周期 1 的方波（前半周 +1、后半周 −1）的傅里叶级数：
#     x(t) = (4/π) Σ_{k 为奇数} sin(2πkt)/k

def square_partial(t, N):
    """只取奇数谐波 k ≤ N 的部分和 S_N(t)。"""
    s = 0.0
    k = 1
    while k <= N:
        s += math.sin(2.0 * math.pi * k * t) / k
        k += 2
    return 4.0 / math.pi * s


def square_jump():
    """方波的跳变幅度（从 −1 到 +1）。"""
    return 2.0


def gibbs_limit(n=400000):
    """Gibbs 过冲的**极限峰值** 2·Si(π)/π。

    Si(x) = ∫₀ˣ sin(u)/u du 用梯形法数值积分；精确值 2Si(π)/π ≈ 1.178980。
    这就是部分和的峰值随 N→∞ 收敛到的那个数 —— 它**不趋于 1**，
    这正是 Gibbs 现象：增多谐波只能把过冲挤窄，不能削平。
    """
    h = math.pi / n
    acc = 0.0
    for i in range(n):
        u0, u1 = i * h, (i + 1) * h
        s0 = 1.0 if u0 == 0 else math.sin(u0) / u0
        s1 = math.sin(u1) / u1
        acc += (s0 + s1) / 2.0 * h
    return 2.0 * acc / math.pi


def square_partial_peak(N, samples=20001):
    """S_N 在跳变附近的最大值（数值扫描）。

    过冲随 N 增大而**变窄**，但峰值趋于 gibbs_limit()。
    """
    best = -1e9
    for i in range(samples):
        t = 0.5 * i / (samples - 1)          # 只扫 [0, 0.5]（跳变在 t=0/0.5）
        v = square_partial(t, N)
        if v > best:
            best = v
    return best


# ---------------------------------------------------------------- 采样与混叠

def aliased_freq(f0, fs):
    """采样率 fs 下，频率 f0 的**表观（折叠后）频率**，落在 [0, fs/2]。

    采样使 f0 与 f0 ± k·fs 无法区分，所以高于 fs/2 的成分会被折回低频 ——
    这就是混叠。
    """
    if fs <= 0:
        raise ValueError("采样率必须为正")
    r = f0 % fs
    return abs(((r + fs / 2.0) % fs) - fs / 2.0)


def sampling_rate_ok(f0, fs):
    """是否满足奈奎斯特条件（fs > 2·f0）。"""
    return fs > 2.0 * f0


# ---------------------------------------------------------------- 时宽频宽积

def sinc(u):
    """归一化 sinc：sin(πu)/(πu)，sinc(0)=1。"""
    if abs(u) < 1e-12:
        return 1.0
    return math.sin(math.pi * u) / (math.pi * u)


def rect_spectrum(freq, tau):
    """宽度 τ 的矩形脉冲的频谱 X(f) = τ·sinc(τf)。"""
    return tau * sinc(tau * freq)


def mainlobe_width(tau):
    """主瓣宽度（第一对零点之间的距离）= 2/τ。

    第一零点在 f = 1/τ，故「时宽 × 第一零点」恒为 1 —— 时宽频宽积不变。
    """
    if tau <= 0:
        raise ValueError("脉宽必须为正")
    return 2.0 / tau


# ---------------------------------------------------------------- RC 低通

def rc_cutoff(R, C):
    """RC 低通的截止频率 f_c = 1/(2πRC)。"""
    if R <= 0 or C <= 0:
        raise ValueError("R、C 必须为正")
    return 1.0 / (2.0 * math.pi * R * C)


def rc_H(freq, R, C):
    """频率响应 H(f) = 1/(1 + j2πfRC)（复数）。"""
    return 1.0 / (1.0 + 1j * 2.0 * math.pi * freq * R * C)


def rc_mag(freq, R, C):
    """幅频 |H(f)| = 1/√(1+(2πfRC)²)。"""
    x = 2.0 * math.pi * freq * R * C
    return 1.0 / math.sqrt(1.0 + x * x)


def rc_phase_deg(freq, R, C):
    """相频（度）：−arctan(2πfRC)。"""
    return -math.degrees(math.atan(2.0 * math.pi * freq * R * C))


# ---------------------------------------------------------------- 离散系统
#
# 一阶系统 y[n] = a·y[n−1] + x[n]，脉冲响应 h[n] = aⁿ。

def disc_pole(a):
    """系统的极点（在 z 平面上）。"""
    return a


def disc_stable(a):
    """稳定 ⟺ |极点| < 1。"""
    return abs(a) < 1.0


def disc_impulse(a, n):
    """脉冲响应 h[n] = aⁿ。"""
    return a ** n


def disc_conv_system(a, x, n_out=None):
    """一阶系统 y[n] = a·y[n−1] + x[n] 的输出。

    用**直接递推**而不是「先截断脉冲响应 h 再做卷积」—— 系统响应本来是无限长的，
    截断会凭空丢掉尾部（冲激输入时表现为输出被硬砍）。递推天然给出完整响应。
    """
    n_out = n_out if n_out is not None else len(x)
    y, prev = [], 0.0
    for n in range(n_out):
        prev = a * prev + (x[n] if n < len(x) else 0.0)
        y.append(prev)
    return y


# ================================================================ 自检

def _selftest():
    bad = []

    def chk(name, got, want, tol=None):
        ok = (got == want) if tol is None else (abs(float(got) - float(want)) <= tol)
        shown = got if tol is None else f"{float(got):.8f}"
        print(f"  {'✓' if ok else '✗'} {name:46s} = {shown}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    print("连续卷积：矩形 * 矩形 = 三角形")
    chk("t=0 处取到峰值 1", conv_rect_rect(0.0), 1.0, 1e-12)
    chk("t=±0.5 处为 0.5", conv_rect_rect(0.5), 0.5, 1e-12)
    chk("t=1 处（支撑边缘）为 0", conv_rect_rect(1.0), 0.0, 1e-12)
    chk("t=2 处仍为 0", conv_rect_rect(2.0), 0.0, 1e-12)
    # 卷积结果的总面积 = 两个函数面积之积
    n = 200000
    area = sum(conv_rect_rect(-1.0 + 2.0 * i / n) * 2.0 / n for i in range(n + 1))
    chk("三角形面积 = 1×1 = 1", area, 1.0, 1e-6)
    chk("卷积是对称的", conv_rect_rect(-0.3), conv_rect_rect(0.3), 1e-12)

    print("\n离散卷积（真跑）")
    y = discrete_conv([1, 2, 3, 1], [1, 1, 1])
    chk("输出长度 = 4+3−1 = 6", len(y), 6)
    chk("结果序列", [int(v) for v in y], [1, 3, 6, 6, 4, 1])
    chk("与直接求和一致：Σ 输出 = Σx · Σh", sum(y), sum([1, 2, 3, 1]) * 3)
    chk("与 δ 卷积还原自身", discrete_conv([2, 5, 1], [1]), [2, 5, 1])
    # 单位阶跃的卷积给出斜坡
    chk("阶跃*阶跃 给出斜坡", discrete_conv([1, 1, 1, 1], [1, 1, 1, 1]), [1, 2, 3, 4, 3, 2, 1])

    print("\n傅里叶级数与 Gibbs 现象")
    chk("S_N(0.25) 趋于 1（方波平台）", square_partial(0.25, 999), 1.0, 2e-3)
    chk("S_N(0.75) 趋于 −1", square_partial(0.75, 999), -1.0, 2e-3)
    chk("S_N 在 0.5 处为 0（奇对称）", square_partial(0.5, 999), 0.0, 1e-9)
    g = gibbs_limit()
    chk("Gibbs 极限 2Si(π)/π", g, 1.1789797, 1e-6)
    # 峰值随 N 增大趋于该极限（且始终大于 1）
    p3 = square_partial_peak(3)
    p51 = square_partial_peak(51)
    p999 = square_partial_peak(999)
    chk("N=3 的峰值已超过 1", p3 > 1.0, True)
    chk("N 越大峰值越接近极限", abs(p999 - g) < abs(p51 - g), True)
    chk("极限峰值 > 1（过冲不消失）", g > 1.0, True)
    chk("跳变幅度为 2", square_jump(), 2.0, 1e-12)

    print("\n采样与混叠")
    chk("f₀=1.2、f_s=1 → 混叠到 0.2", aliased_freq(1.2, 1.0), 0.2, 1e-12)
    chk("f₀=0.3、f_s=1 → 不变（未越界）", aliased_freq(0.3, 1.0), 0.3, 1e-12)
    chk("f₀=0.5、f_s=1 → 恰在奈奎斯特频率", aliased_freq(0.5, 1.0), 0.5, 1e-12)
    chk("f₀=2.2、f_s=1 → 折到 0.2", aliased_freq(2.2, 1.0), 0.2, 1e-12)
    chk("f₀=0.2、f_s=1 满足奈奎斯特", sampling_rate_ok(0.2, 1.0), True)
    chk("f₀=0.6、f_s=1 不满足", sampling_rate_ok(0.6, 1.0), False)
    chk("表观频率必落在 [0, f_s/2]",
        all(0 <= aliased_freq(x, 1.0) <= 0.5 + 1e-12 for x in [i / 20 for i in range(0, 100)]), True)

    print("\n时宽频宽积")
    chk("sinc(0) = 1", sinc(0.0), 1.0, 1e-12)
    chk("sinc(1) = 0（第一零点）", sinc(1.0), 0.0, 1e-12)
    for tau in (0.25, 1.0, 2.0):
        chk(f"τ={tau} 时 X(0) = τ", rect_spectrum(0.0, tau), tau, 1e-12)
        chk(f"  └ τ={tau} 的第一零点在 f=1/τ", rect_spectrum(1.0 / tau, tau), 0.0, 1e-12)
        chk(f"  └ 时宽×第一零点 = 1", tau * (1.0 / tau), 1.0, 1e-12)
    chk("主瓣宽度 = 2/τ", mainlobe_width(0.5), 4.0, 1e-12)

    print("\nRC 低通")
    R, C = 1000.0, 1e-6
    fc = rc_cutoff(R, C)
    chk("截止频率 1/(2πRC)", fc, 1.0 / (2 * math.pi * 1000 * 1e-6), 1e-12)
    chk("截止处 |H| = 1/√2", rc_mag(fc, R, C), 1 / math.sqrt(2), 1e-12)
    chk("直流增益 |H(0)| = 1", rc_mag(0.0, R, C), 1.0, 1e-12)
    chk("截止处相位 = −45°", rc_phase_deg(fc, R, C), -45.0, 1e-9)
    chk("高频衰减（f=10fc 时 |H| < 0.1）", rc_mag(10 * fc, R, C) < 0.1, True)
    chk("幅频单调下降", rc_mag(fc, R, C) > rc_mag(2 * fc, R, C) > rc_mag(10 * fc, R, C), True)
    # 复频响应的模与幅频函数一致
    chk("|H(f)| 与 rc_mag 一致", abs(rc_H(3 * fc, R, C)), rc_mag(3 * fc, R, C), 1e-12)

    print("\n离散系统：极点与稳定性")
    chk("a=0.5 稳定", disc_stable(0.5), True)
    chk("a=0.999 稳定", disc_stable(0.999), True)
    chk("a=1.0 不稳定（临界）", disc_stable(1.0), False)
    chk("a=−1.5 不稳定", disc_stable(-1.5), False)
    chk("h[0] = 1", disc_impulse(0.5, 0), 1.0, 1e-12)
    chk("h[5] = a⁵ = 1/32", disc_impulse(0.5, 5), 1.0 / 32, 1e-15)
    chk("负极点给出交替符号", disc_impulse(-0.5, 3), -0.125, 1e-15)
    chk("极点就是 a", disc_pole(0.7), 0.7, 1e-12)
    # 稳定系统的脉冲响应单调衰减到 0
    chk("稳定系统 h[30] → 0", abs(disc_impulse(0.5, 30)) < 1e-9, True)
    chk("不稳定系统 h[30] 发散", abs(disc_impulse(1.2, 30)) > 100, True)
    ysys = disc_conv_system(0.5, [1, 0, 0, 0], n_out=8)
    chk("冲激输入的系统输出 = 脉冲响应 h[n]=aⁿ",
        [round(v, 12) for v in ysys], [round(0.5 ** n, 12) for n in range(8)])
    # 阶跃输入：y[∞] → 1/(1−a)（用足够长的序列，残差 0.5⁴⁰ ≈ 9e-13）
    ystep = disc_conv_system(0.5, [1] * 40, n_out=40)
    chk("阶跃输入的稳态 → 1/(1−a) = 2", ystep[-1], 1.0 / (1 - 0.5), 1e-9)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
