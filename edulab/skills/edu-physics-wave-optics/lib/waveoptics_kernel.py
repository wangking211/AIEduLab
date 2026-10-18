#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
waveoptics_kernel.py —— 高中物理「机械振动 · 机械波 · 光」内核（选择性必修一）

覆盖：
  · 简谐运动：位移/速度/加速度/回复力、周期与角频率的关系、参考圆
  · 横波的传播：波形函数 y(x,t)、波速 v = λ/T = λf、质点振动方向
  · 驻波：y(x,t) = 2A sin(kx) cos(ωt)、波节与波腹的位置
  · 波的叠加与拍：y = A sin(ω₁t) + A sin(ω₂t)、拍频 |f₁ − f₂|
  · 双缝干涉：条纹间距 Δy = Lλ/d、第 k 级明纹位置
  · 折射定律与全反射：n₁ sin i = n₂ sin r、临界角 sin C = n₂/n₁
  · 凸透镜成像：1/u + 1/v = 1/f、放大率 m = −v/u、实像/虚像判据

设计原则（与全项目一致）：
  · **不手写数字**：所有结果由本内核现算；常数集中声明在下面一处。
  · 角度一律以**度**作为对外接口，内部再转弧度（教学页面上都是度）。
  · 自检：python waveoptics_kernel.py
"""

import math

import sympy as sp

__all__ = [
    "tex", "f", "num_str",
    "C_LIGHT",
    "shm_x", "shm_v", "shm_a", "shm_force", "shm_period", "shm_omega", "shm_phase",
    "wave_y", "wave_speed", "wave_number", "wave_omega", "particle_velocity",
    "standing_y", "nodes", "antinodes", "node_spacing",
    "beat_sum", "beat_freq", "beat_period",
    "fringe_spacing", "fringe_position", "fringe_order_at",
    "snell_angle", "critical_angle", "is_total_internal", "refractive_index",
    "lens_image", "lens_magnification", "lens_is_virtual", "lens_is_inverted",
]


# ---------------------------------------------------------------- 物理常数（实测类）
C_LIGHT = 3.00e8          # 真空光速，m/s（教材三位有效数字）


# ---------------------------------------------------------------- 排版助手
def tex(e):
    return sp.latex(sp.simplify(sp.sympify(e)))


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


def _rad(deg):
    return float(deg) * math.pi / 180.0


def _deg(rad):
    return float(rad) * 180.0 / math.pi


# ---------------------------------------------------------------- 简谐运动
def shm_x(A, omega, t, phi=0.0):
    """位移 x = A sin(ωt + φ)。"""
    return A * math.sin(omega * t + phi)


def shm_v(A, omega, t, phi=0.0):
    """速度 v = Aω cos(ωt + φ)（位移对时间求导）。"""
    return A * omega * math.cos(omega * t + phi)


def shm_a(A, omega, t, phi=0.0):
    """加速度 a = −Aω² sin(ωt + φ) = −ω²x。"""
    return -A * omega * omega * math.sin(omega * t + phi)


def shm_force(m, A, omega, t, phi=0.0):
    """回复力 F = ma = −mω²x。"""
    return m * shm_a(A, omega, t, phi)


def shm_period(omega):
    """周期 T = 2π/ω。"""
    if omega == 0:
        raise ValueError("角频率不能为零")
    return 2.0 * math.pi / omega


def shm_omega(T):
    """角频率 ω = 2π/T。"""
    if T == 0:
        raise ValueError("周期不能为零")
    return 2.0 * math.pi / T


def shm_phase(omega, t, phi=0.0):
    """相位 ωt + φ（度）。"""
    return _deg(omega * t + phi)


# ---------------------------------------------------------------- 横波
def wave_y(A, T, lam, x, t, phi=0.0):
    """波形函数 y = A sin(2π(t/T − x/λ) + φ)。

    这是沿 **+x 方向**传播的波；把 x 的符号换成 −x 就是沿 −x 传播。
    """
    return A * math.sin(2.0 * math.pi * (t / T - x / lam) + phi)


def wave_speed(lam, T):
    """波速 v = λ/T（也等于 λf）。"""
    if T == 0:
        raise ValueError("周期不能为零")
    return lam / T


def wave_number(lam):
    """波数 k = 2π/λ。"""
    if lam == 0:
        raise ValueError("波长不能为零")
    return 2.0 * math.pi / lam


def wave_omega(T):
    return shm_omega(T)


def particle_velocity(A, T, lam, x, t):
    """波形图上某质点此刻的振动速度：∂y/∂t = A·(2π/T)·cos(2π(t/T − x/λ))。

    正值表示质点向上运动。它才是「质点振动方向」的正确来源 ——
    不看图猜方向很容易搞反。
    """
    return A * (2.0 * math.pi / T) * math.cos(2.0 * math.pi * (t / T - x / lam))


# ---------------------------------------------------------------- 驻波
def standing_y(A, lam, x, t, T=2.0):
    """驻波 y = 2A sin(kx) cos(ωt)，k = 2π/λ，ω = 2π/T。

    A 是**入射波**的振幅，驻波的最大振幅是 2A（波腹）。
    """
    k = wave_number(lam)
    w = shm_omega(T)
    return 2.0 * A * math.sin(k * x) * math.cos(w * t)


def nodes(lam, x_from, x_to):
    """波节位置：sin(kx) = 0 ⇒ x = nλ/2（n 为整数）。"""
    half = lam / 2.0
    lo = math.ceil(x_from / half - 1e-9)
    hi = math.floor(x_to / half + 1e-9)
    return [n * half for n in range(lo, hi + 1)]


def antinodes(lam, x_from, x_to):
    """波腹位置：|sin(kx)| = 1 ⇒ x = (2n+1)λ/4。"""
    q = lam / 4.0
    lo = math.ceil((x_from / q - 1) / 2 - 1e-9)
    hi = math.floor((x_to / q - 1) / 2 + 1e-9)
    return [(2 * n + 1) * q for n in range(lo, hi + 1)]


def node_spacing(lam):
    """相邻波节的间距 = λ/2；相邻波腹的间距也是 λ/2。"""
    return lam / 2.0


# ---------------------------------------------------------------- 波的叠加与拍
def beat_sum(A, f1, f2, t):
    """两列同振幅波叠加：y = A sin(2πf₁t) + A sin(2πf₂t)。"""
    return A * math.sin(2.0 * math.pi * f1 * t) + A * math.sin(2.0 * math.pi * f2 * t)


def beat_env(A, f1, f2, t):
    """拍的包络振幅 2A|cos(π(f₁−f₂)t)|。"""
    return 2.0 * A * abs(math.cos(math.pi * (f1 - f2) * t))


def beat_freq(f1, f2):
    """拍频 = |f₁ − f₂|（单位与 f 相同）。"""
    return abs(f1 - f2)


def beat_period(f1, f2):
    """拍周期 = 1/|f₁ − f₂|。"""
    d = beat_freq(f1, f2)
    return float("inf") if d == 0 else 1.0 / d


# ---------------------------------------------------------------- 双缝干涉
def fringe_spacing(lam, L, d):
    """相邻明纹（或暗纹）的间距 Δy = Lλ/d。

    λ 用 m，L 与 d 同单位，返回与 L 同单位。
    """
    if d == 0:
        raise ValueError("双缝间距不能为零")
    return L * lam / d


def fringe_position(k, lam, L, d):
    """第 k 级明纹到中心的位置 y_k = k·Lλ/d（k 可为 0、±1、±2…）。"""
    return k * fringe_spacing(lam, L, d)


def fringe_order_at(y, lam, L, d):
    """屏上位置 y 处是第几级 —— k = y/Δy（整数即明纹，半整数即暗纹）。"""
    return y / fringe_spacing(lam, L, d)


# ---------------------------------------------------------------- 折射与全反射
def refractive_index(c_speed, v_medium):
    """绝对折射率 n = c/v。"""
    if v_medium == 0:
        raise ValueError("介质中的光速不能为零")
    return c_speed / v_medium


def snell_angle(n1, n2, i_deg):
    """折射定律 n₁ sin i = n₂ sin r ⇒ r = arcsin(n₁ sin i / n₂)。

    若 n₁ sin i > n₂（发生全反射），返回 **None** —— 此时不存在折射光线。
    """
    s = n1 * math.sin(_rad(i_deg)) / n2
    if s > 1.0 + 1e-12:
        return None
    s = max(-1.0, min(1.0, s))
    return _deg(math.asin(s))


def critical_angle(n1, n2):
    """从光密介质 n₁ 射向光疏介质 n₂ 的临界角 C，sin C = n₂/n₁。

    n₁ ≤ n₂ 时不存在全反射，返回 None。
    """
    if n1 <= n2:
        return None
    return _deg(math.asin(n2 / n1))


def is_total_internal(n1, n2, i_deg):
    """是否发生全反射。"""
    c = critical_angle(n1, n2)
    return c is not None and i_deg > c


# ---------------------------------------------------------------- 凸透镜成像（1/u + 1/v = 1/f）
def lens_image(f_len, u):
    """像距 v = uf/(u − f)。u = f 时像在无穷远，返回 None。

    约定：u、v 都取正号表示在透镜两侧（实像），v < 0 表示虚像（与物同侧）。
    """
    if u == 0:
        raise ValueError("物距不能为零")
    denom = u - f_len
    if abs(denom) < 1e-12:
        return None
    return u * f_len / denom


def lens_magnification(f_len, u):
    """放大率 m = −v/u（负号表示倒立）。u = f 时返回 None。"""
    v = lens_image(f_len, u)
    return None if v is None else -v / u


def lens_is_virtual(f_len, u):
    """是否成虚像：v < 0（像与物在透镜同侧）。u = f 时返回 None。"""
    v = lens_image(f_len, u)
    return None if v is None else v < 0


def lens_is_inverted(f_len, u):
    """是否倒立：m < 0。u = f 时返回 None。"""
    m = lens_magnification(f_len, u)
    return None if m is None else m < 0


# ================================================================ 自检
def _selftest():
    bad = []

    def _same(a, b):
        if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
            a, b = list(a), list(b)
            return len(a) == len(b) and all(abs(x - y) <= 1e-9 for x, y in zip(a, b))
        if math.isinf(a) or math.isinf(b):
            return a == b
        return abs(float(a) - float(b)) <= 1e-9

    def chk(name, got, want, tol=1e-9):
        inf_case = (not isinstance(got, (list, tuple))) and (not isinstance(want, (list, tuple))) \
                   and got is not None and want is not None \
                   and (math.isinf(got) or math.isinf(want))
        if isinstance(got, (list, tuple)) or isinstance(want, (list, tuple)):
            ok = _same(got, want)
            g = list(got) if got is not None else "None"
        elif got is None and want is None:
            ok, g = True, "None"
        elif got is None or want is None:
            ok, g = False, ("None" if got is None else f"{float(got):.6g}")
        elif inf_case:
            ok, g = (got == want), ("inf" if math.isinf(got) else f"{float(got):.6g}")
        else:
            ok = abs(float(got) - float(want)) <= tol
            g = f"{float(got):.6g}"
        print(f"  {'✓' if ok else '✗'} {name:46s} = {g}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    def chkb(name, got, want):
        ok = bool(got) == bool(want)
        print(f"  {'✓' if ok else '✗'} {name:46s} = {got}")
        if not ok:
            bad.append(name)

    print("简谐运动")
    om = shm_omega(2.0)
    chk("ω = 2π/T（T=2 s）", om, math.pi, 1e-12)
    chk("周期与角频率互逆", shm_period(om), 2.0, 1e-12)
    chk("t=0 时 x=0", shm_x(1.0, om, 0.0), 0.0, 1e-12)
    chk("t=T/4 时 x=A", shm_x(1.0, om, 0.5), 1.0, 1e-12)
    chk("t=T/2 时 x=0", shm_x(1.0, om, 1.0), 0.0, 1e-12)
    chk("t=0 时 v=Aω（最大）", shm_v(1.0, om, 0.0), math.pi, 1e-12)
    chk("t=T/4 时 v=0", shm_v(1.0, om, 0.5), 0.0, 1e-12)
    chk("a = −ω²x", shm_a(1.0, om, 0.3), -(om ** 2) * shm_x(1.0, om, 0.3), 1e-12)
    chk("最大加速度 Aω²", shm_a(2.0, om, 0.5), -2.0 * om * om, 1e-12)
    chk("回复力 F = −mω²x", shm_force(0.5, 1.0, om, 0.5), -0.5 * om * om, 1e-12)
    chk("相位 ωt（度）", shm_phase(om, 0.5), 90.0, 1e-9)
    # 相位差 180° 的两点位移相反
    chk("相位差 180° ⇒ 位移相反",
        shm_x(1.0, om, 0.5) + shm_x(1.0, om, 1.5), 0.0, 1e-12)

    print("\n横波")
    chk("波速 v = λ/T", wave_speed(4.0, 2.0), 2.0, 1e-12)
    chk("波数 k = 2π/λ", wave_number(4.0), math.pi / 2, 1e-12)
    chk("t=0、x=0 处 y=0", wave_y(1.0, 2.0, 4.0, 0.0, 0.0), 0.0, 1e-12)
    chk("x=λ/4 处 y=A（t=0）", wave_y(1.0, 2.0, 4.0, 1.0, 0.0), -1.0, 1e-12)
    chk("t=T/4 时波形与 t=0 相差 λ/4", wave_y(1.0, 2.0, 4.0, 0.0, 0.5), 1.0, 1e-12)
    # 波沿 +x 传播：t 增加时，同一相位点向 +x 移动
    chk("波沿 +x 传播（同相位点 x 增大）",
        wave_y(1.0, 2.0, 4.0, 2.0, 0.0), wave_y(1.0, 2.0, 4.0, 1.0, 0.5), 1e-12)
    chk("质点速度 ∂y/∂t（t=0, x=0）", particle_velocity(1.0, 2.0, 4.0, 0.0, 0.0),
        math.pi, 1e-12)

    print("\n驻波")
    chk("波节间距 = λ/2", node_spacing(4.0), 2.0, 1e-12)
    chk("波节位置（0..8，λ=4）", nodes(4.0, 0.0, 8.0), [0.0, 2.0, 4.0, 6.0, 8.0])
    chk("波腹位置（0..8，λ=4）", antinodes(4.0, 0.0, 8.0), [1.0, 3.0, 5.0, 7.0])
    chk("波节处振幅恒为 0（t=0.3）", standing_y(1.0, 4.0, 2.0, 0.3), 0.0, 1e-12)
    chk("波腹处振幅为 2A（t=0）", standing_y(1.0, 4.0, 1.0, 0.0), 2.0, 1e-12)
    chk("t=T/4 时整条驻波为 0", standing_y(1.0, 4.0, 1.0, 0.5), 0.0, 1e-12)
    chk("相邻波节位置处 y 反号（t=0）",
        standing_y(1.0, 4.0, 1.0, 0.0) + standing_y(1.0, 4.0, 3.0, 0.0), 0.0, 1e-12)

    print("\n波的叠加与拍")
    chk("拍频 = |f₁ − f₂|", beat_freq(440.0, 448.0), 8.0, 1e-12)
    chk("拍周期 = 1/Δf", beat_period(440.0, 448.0), 0.125, 1e-12)
    chk("等频时拍频为 0", beat_freq(440.0, 440.0), 0.0, 1e-12)
    chk("等频时拍周期为无穷", beat_period(440.0, 440.0), float("inf"), 1.0)
    chk("t=0 时两波同相、和为 2A", beat_sum(1.0, 440.0, 448.0, 0.0), 0.0, 1e-9)
    chk("包络最大 2A", beat_env(1.0, 440.0, 448.0, 0.0), 2.0, 1e-12)
    chk("包络在半个拍周期处为 0", beat_env(1.0, 440.0, 448.0, 0.0625), 0.0, 1e-9)
    # 叠加的和不超过包络
    chk("|和| ≤ 包络（抽样）",
        all(abs(beat_sum(1.0, 440.0, 448.0, t)) <= beat_env(1.0, 440.0, 448.0, t) + 1e-9
            for t in [i / 500.0 for i in range(60)]), True)

    print("\n双缝干涉")
    chk("条纹间距 Δy = Lλ/d", fringe_spacing(600e-9, 1.0, 0.5e-3), 1.2e-3, 1e-15)
    chk("第 1 级明纹位置", fringe_position(1, 600e-9, 1.0, 0.5e-3), 1.2e-3, 1e-15)
    chk("第 3 级明纹位置", fringe_position(3, 600e-9, 1.0, 0.5e-3), 3.6e-3, 1e-15)
    chk("中心是 0 级明纹", fringe_position(0, 600e-9, 1.0, 0.5e-3), 0.0, 1e-15)
    chk("λ 越大条纹越宽",
        fringe_spacing(700e-9, 1.0, 0.5e-3) > fringe_spacing(400e-9, 1.0, 0.5e-3), True)
    chk("d 越大条纹越窄",
        fringe_spacing(600e-9, 1.0, 1e-3) < fringe_spacing(600e-9, 1.0, 0.5e-3), True)
    chk("屏上 1.2 mm 处是第 1 级", fringe_order_at(1.2e-3, 600e-9, 1.0, 0.5e-3), 1.0, 1e-12)
    chk("屏上 0.6 mm 处是第 0.5 级（暗纹）",
        fringe_order_at(0.6e-3, 600e-9, 1.0, 0.5e-3), 0.5, 1e-12)

    print("\n折射与全反射")
    chk("折射率 n = c/v（v=2e8）", refractive_index(C_LIGHT, 2.0e8), 1.5, 1e-12)
    chk("空气→玻璃：i=30° 的 r", snell_angle(1.0, 1.5, 30.0), 19.4712, 1e-4)
    chk("空气→玻璃：i=0° 的 r = 0", snell_angle(1.0, 1.5, 0.0), 0.0, 1e-12)
    chk("空气→玻璃永不发生全反射", snell_angle(1.0, 1.5, 89.0) is not None, True)
    chk("玻璃→空气的临界角", critical_angle(1.5, 1.0), 41.8103, 1e-4)
    chk("n₁ ≤ n₂ 时无临界角", critical_angle(1.0, 1.5) is None, True)
    chk("i=30° < C 时不发生全反射", is_total_internal(1.5, 1.0, 30.0), False)
    chk("i=45° > C 时全反射", is_total_internal(1.5, 1.0, 45.0), True)
    chk("全反射时无折射光线", snell_angle(1.5, 1.0, 45.0) is None, True)
    # 恰在临界角（用内核自己算出的 C 反代）时折射角为 90°
    chk("恰在临界角时 r = 90°", snell_angle(1.5, 1.0, critical_angle(1.5, 1.0)), 90.0, 1e-6)
    # i = 20° 时 sin r = 1.5·sin20° = 0.513030 ⇒ r = 30.8659°
    chk("玻璃→空气 i=20° 的折射角", snell_angle(1.5, 1.0, 20.0), 30.8659, 1e-4)
    # 折射角大于入射角（从密到疏）
    chk("从光密到光疏：r > i", snell_angle(1.5, 1.0, 20.0) > 20.0, True)

    print("\n凸透镜成像")
    chk("f=10、u=30 ⇒ v=15（实像）", lens_image(10.0, 30.0), 15.0, 1e-12)
    chk("f=10、u=20 ⇒ v=20（等大倒立）", lens_image(10.0, 20.0), 20.0, 1e-12)
    chk("f=10、u=5 ⇒ v=−10（虚像）", lens_image(10.0, 5.0), -10.0, 1e-12)
    chk("f=10、u=10 ⇒ 像在无穷远", lens_image(10.0, 10.0) is None, True)
    chk("放大率 m = −v/u（u=30）", lens_magnification(10.0, 30.0), -0.5, 1e-12)
    chk("u=2f 时 |m| = 1", abs(lens_magnification(10.0, 20.0)), 1.0, 1e-12)
    chk("u=30 成实像", lens_is_virtual(10.0, 30.0), False)
    chk("u=5 成虚像", lens_is_virtual(10.0, 5.0), True)
    chk("实像都是倒立的", lens_is_inverted(10.0, 30.0), True)
    chk("虚像是正立的", lens_is_inverted(10.0, 5.0), False)
    # 成像公式自洽：1/u + 1/v = 1/f
    u_, f_ = 12.0, 10.0
    v_ = lens_image(f_, u_)
    chk("1/u + 1/v = 1/f", 1 / u_ + 1 / v_, 1 / f_, 1e-12)
    chk("u 越大 v 越接近 f", abs(lens_image(10.0, 200.0) - 10.0) < 0.6, True)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
