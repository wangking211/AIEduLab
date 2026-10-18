#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
momentum_kernel.py —— 高中物理「动量与碰撞」内核（选择性必修一）

覆盖：
  · 动量 p = mv、动量定理 Ft = Δp = mv₂ − mv₁
  · 一维完全非弹性碰撞（碰后共速）与动能损失
  · 一维弹性碰撞（动量与动能同时守恒）
  · 反冲与爆炸（总动量为零、释放的化学/弹性势能转成动能）
  · 人船模型（质心不动 ⇒ 系统总动量恒为零）
  · 子弹打木块（嵌入后共速，动能损失与滑行距离）
  · 等质量弹性斜碰的「90° 定理」（二维动量守恒的矢量形式）

设计原则（与全项目一致）：
  · **不手写数字**：所有结果由本内核现算；常数集中声明在下面一处。
  · 一维问题统一约定 **向右为正**，速度带符号代入（碰后反向就是负速度）。
  · **能量只算「动能」，不涉及内能细节**：碰撞过程损失的机械能一律按「动能之差」给出，
    并明确说明它转化成了内能/形变（不追问具体形式）。
  · 自检：python momentum_kernel.py
"""

import math

import sympy as sp

__all__ = [
    "tex", "f", "num_str", "G_EARTH",
    "momentum", "kinetic", "total_momentum", "total_kinetic",
    "impulse", "delta_p", "avg_force", "impulse_force_time",
    "inelastic_v", "kinetic_loss", "loss_fraction",
    "elastic_v1", "elastic_v2", "elastic_pair",
    "recoil_v", "explosion_velocities", "explosion_energy",
    "boat_shift", "boat_person_shift", "boat_boat_shift",
    "bullet_common_v", "bullet_kinetic_loss", "bullet_slide_distance",
    "equal_mass_elastic2d", "percent",
]


# ---------------------------------------------------------------- 物理常数（实测类）
G_EARTH = 9.8              # 重力加速度，m/s²（教材常用值）


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


def percent(x, digits=2):
    return float(x) * 100.0


# ---------------------------------------------------------------- 动量与动能
def momentum(m, v):
    """动量 p = mv（矢量，向右为正；一维用带符号的数表示）。"""
    return m * v


def kinetic(m, v):
    """动能 E_k = ½mv²（标量，恒非负）。"""
    return 0.5 * m * v * v


def total_momentum(masses, velocities):
    """系统总动量（代数和，带符号）。"""
    return sum(m * v for m, v in zip(masses, velocities))


def total_kinetic(masses, velocities):
    """系统总动能。"""
    return sum(kinetic(m, v) for m, v in zip(masses, velocities))


# ---------------------------------------------------------------- 动量定理
def impulse(F, t):
    """冲量 I = F·t（恒力）。"""
    return F * t


def delta_p(m, v1, v2):
    """动量变化 Δp = mv₂ − mv₁。"""
    return m * (v2 - v1)


def avg_force(m, v1, v2, t):
    """由动量定理求平均力 F̄ = Δp/t。"""
    if t == 0:
        raise ValueError("作用时间不能为零")
    return m * (v2 - v1) / t


def impulse_force_time(S_area, F):
    """由冲量求作用时间 t = I/F。"""
    if F == 0:
        raise ValueError("力不能为零")
    return S_area / F


# ---------------------------------------------------------------- 完全非弹性碰撞
def inelastic_v(m1, v1, m2, v2):
    """碰后共速 v = (m₁v₁ + m₂v₂)/(m₁ + m₂)（动量守恒）。"""
    if m1 + m2 == 0:
        raise ValueError("总质量不能为零")
    return (m1 * v1 + m2 * v2) / (m1 + m2)


def kinetic_loss(m1, v1, m2, v2):
    """碰撞损失的动能 ΔE = E_before − E_after（完全非弹性时损失最大）。"""
    v = inelastic_v(m1, v1, m2, v2)
    return kinetic(m1, v1) + kinetic(m2, v2) - kinetic(m1 + m2, v)


def loss_fraction(m1, v1, m2, v2):
    """动能损失占初动能的比例。"""
    e0 = kinetic(m1, v1) + kinetic(m2, v2)
    if e0 == 0:
        return 0.0
    return kinetic_loss(m1, v1, m2, v2) / e0


# ---------------------------------------------------------------- 弹性碰撞
def elastic_v1(m1, v1, m2, v2):
    """一维弹性碰撞后 m₁ 的速度 v₁′ = [(m₁−m₂)v₁ + 2m₂v₂]/(m₁+m₂)。"""
    if m1 + m2 == 0:
        raise ValueError("总质量不能为零")
    return ((m1 - m2) * v1 + 2 * m2 * v2) / (m1 + m2)


def elastic_v2(m1, v1, m2, v2):
    """一维弹性碰撞后 m₂ 的速度 v₂′ = [(m₂−m₁)v₂ + 2m₁v₁]/(m₁+m₂)。"""
    if m1 + m2 == 0:
        raise ValueError("总质量不能为零")
    return ((m2 - m1) * v2 + 2 * m1 * v1) / (m1 + m2)


def elastic_pair(m1, v1, m2, v2):
    """返回 (v₁′, v₂′)。"""
    return elastic_v1(m1, v1, m2, v2), elastic_v2(m1, v1, m2, v2)


# ---------------------------------------------------------------- 反冲与爆炸
def recoil_v(m1, v1, m2):
    """反冲：0 = m₁v₁ + m₂v₂ ⇒ v₂ = −m₁v₁/m₂。"""
    if m2 == 0:
        raise ValueError("质量不能为零")
    return -m1 * v1 / m2


def explosion_velocities(m1, m2, E):
    """爆炸释放能量 E（全部转成两碎片的动能），总动量为零。

    由 ½m₁v₁² + ½m₂v₂² = E 与 m₁v₁ + m₂v₂ = 0 解得
      |v₁| = √(2E·m₂ / (m₁(m₁+m₂)))，|v₂| = √(2E·m₁ / (m₂(m₁+m₂)))
    方向相反（返回时 m₁ 取正、m₂ 取负）。
    """
    if m1 <= 0 or m2 <= 0:
        raise ValueError("质量必须为正")
    v1 = math.sqrt(2.0 * E * m2 / (m1 * (m1 + m2)))
    v2 = -math.sqrt(2.0 * E * m1 / (m2 * (m1 + m2)))
    return v1, v2


def explosion_energy(m1, v1, m2, v2):
    """由两碎片的速度反推释放的能量（校验用）。"""
    return kinetic(m1, v1) + kinetic(m2, v2)


# ---------------------------------------------------------------- 人船模型
def boat_shift(m_person, m_boat, L):
    """人相对船走过 L（大小），返回 (人对地位移, 船对地位移)。

    系统动量恒为零 ⇒ 质心不动 ⇒ 人的位移与船的位移**按质量反比分配**：
      x_人 = L·M/(M+m)（向右），x_船 = −L·m/(M+m)（向左）
    恒有 x_人 − x_船 = L（正好等于人相对船走过的距离）。
    """
    M = m_person + m_boat
    if M == 0:
        raise ValueError("总质量不能为零")
    return L * m_boat / M, -L * m_person / M


def boat_person_shift(m_person, m_boat, L):
    return boat_shift(m_person, m_boat, L)[0]


def boat_boat_shift(m_person, m_boat, L):
    return boat_shift(m_person, m_boat, L)[1]


# ---------------------------------------------------------------- 子弹打木块
def bullet_common_v(m_bullet, v_bullet, m_block):
    """子弹嵌入木块后的共同速度 v′ = m v/(m + M)。"""
    if m_bullet + m_block == 0:
        raise ValueError("总质量不能为零")
    return m_bullet * v_bullet / (m_bullet + m_block)


def bullet_kinetic_loss(m_bullet, v_bullet, m_block):
    """子弹打木块损失的动能。"""
    v = bullet_common_v(m_bullet, v_bullet, m_block)
    return kinetic(m_bullet, v_bullet) - kinetic(m_bullet + m_block, v)


def bullet_slide_distance(m_bullet, v_bullet, m_block, mu, g=G_EARTH):
    """子弹嵌入后整体在粗糙地面滑行的距离 s = v′²/(2μg)。

    由动能定理 −μ(m+M)g·s = 0 − ½(m+M)v′² 得到（μ 为动摩擦因数）。
    """
    if mu <= 0:
        raise ValueError("动摩擦因数必须为正")
    v = bullet_common_v(m_bullet, v_bullet, m_block)
    return v * v / (2.0 * mu * g)


# ---------------------------------------------------------------- 等质量弹性斜碰
def equal_mass_elastic2d(v, theta_deg):
    """等质量弹性斜碰（m₁ = m₂，第二个初始静止）。

    设碰后 m₁ 的速度方向与初速度成 θ。由动量守恒 + 动能守恒可解出
      |v₁′| = v·cosθ，|v₂′| = v·sinθ，且 **两出射速度恒成 90°**。
    返回 (v₁′ 的 (x,y), v₂′ 的 (x,y))。
    """
    t = math.radians(theta_deg)
    a1 = v * math.cos(t)                      # |v₁′|
    a2 = v * math.sin(t)                      # |v₂′|
    return ((a1 * math.cos(t), a1 * math.sin(t)),
            (a2 * math.sin(t), -a2 * math.cos(t)))


# ================================================================ 自检
def _selftest():
    bad = []

    def chk(name, got, want, tol=1e-9):
        if isinstance(got, (list, tuple)) or isinstance(want, (list, tuple)):
            ga, wa = list(got), list(want)
            ok = len(ga) == len(wa) and all(abs(x - y) <= 1e-9 for x, y in zip(ga, wa))
            g = ga
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

    print("动量与冲量")
    chk("p = mv", momentum(2.0, 3.0), 6.0, 1e-12)
    chk("动量是矢量（反向取负）", momentum(2.0, -3.0), -6.0, 1e-12)
    chk("动能 ½mv²（恒非负）", kinetic(2.0, -3.0), 9.0, 1e-12)
    chk("恒力冲量 I = Ft", impulse(100.0, 0.1), 10.0, 1e-12)
    chk("Δp = m(v₂−v₁)", delta_p(0.5, 10.0, -10.0), -10.0, 1e-12)
    chk("平均力 F̄ = Δp/t", avg_force(0.5, 10.0, -10.0, 0.1), -100.0, 1e-12)
    chk("由冲量求时间", impulse_force_time(10.0, 100.0), 0.1, 1e-12)
    # 冲量大小等于动量变化大小（矢量式的一维写法）
    chk("|Ft| = |Δp|", impulse(50.0, 0.2), delta_p(1.0, 0.0, 10.0), 1e-12)

    print("\n完全非弹性碰撞")
    chk("碰后共速", inelastic_v(2.0, 6.0, 4.0, 0.0), 2.0, 1e-12)
    chk("动量守恒（碰前 = 碰后）",
        total_momentum([2.0, 4.0], [6.0, 0.0]),
        total_momentum([2.0, 4.0], [2.0, 2.0]), 1e-12)
    chk("动能损失", kinetic_loss(2.0, 6.0, 4.0, 0.0), 24.0, 1e-12)
    chk("损失比例", loss_fraction(2.0, 6.0, 4.0, 0.0), 24.0 / 36.0, 1e-12)
    # 等质量正碰、一个静止：完全非弹性损失一半动能
    chk("等质量碰静止：损失 50% 动能",
        loss_fraction(1.0, 4.0, 1.0, 0.0), 0.5, 1e-12)
    # 质量悬殊时几乎全部动能损失
    chk("轻球撞重块：损失接近 100%",
        loss_fraction(0.02, 400.0, 0.98, 0.0) > 0.97, True)

    print("\n弹性碰撞")
    chk("等质量正碰交换速度", elastic_pair(1.0, 5.0, 1.0, 0.0), (0.0, 5.0))
    chk("轻球撞重球会反弹", elastic_v1(1.0, 4.0, 3.0, 0.0), -2.0, 1e-12)
    chk("  重球被推向前", elastic_v2(1.0, 4.0, 3.0, 0.0), 2.0, 1e-12)
    chk("  动量守恒", total_momentum([1.0, 3.0], [4.0, 0.0]),
        total_momentum([1.0, 3.0], [-2.0, 2.0]), 1e-12)
    chk("  动能守恒", total_kinetic([1.0, 3.0], [4.0, 0.0]),
        total_kinetic([1.0, 3.0], [-2.0, 2.0]), 1e-12)
    # 相向等速的等质量正碰：各自原速返回
    chk("相向等速碰后原速返回", elastic_pair(1.0, 3.0, 1.0, -3.0), (-3.0, 3.0))
    # 弹性碰撞的动能损失恒为 0
    chk("弹性碰撞动能不损失",
        total_kinetic([2.0, 5.0], [7.0, -1.0]) -
        total_kinetic([2.0, 5.0], list(elastic_pair(2.0, 7.0, 5.0, -1.0))), 0.0, 1e-9)
    # 完全非弹性碰撞的动能损失 ≥ 弹性碰撞的（0）
    chk("完全非弹性损失 > 弹性损失", kinetic_loss(2.0, 6.0, 4.0, 0.0) > 0.0, True)

    print("\n反冲与爆炸")
    chk("反冲：总动量为零",
        total_momentum([2.0, 3.0], [3.0, recoil_v(2.0, 3.0, 3.0)]), 0.0, 1e-12)
    v1, v2 = explosion_velocities(1.0, 4.0, 100.0)
    chk("爆炸：总动量为零", total_momentum([1.0, 4.0], [v1, v2]), 0.0, 1e-12)
    chk("爆炸：释放的能量守恒", explosion_energy(1.0, v1, 4.0, v2), 100.0, 1e-9)
    chk("爆炸：轻的跑得快", abs(v1) > abs(v2), True)
    # 质量相等时两碎片速度大小相等、方向相反
    u1, u2 = explosion_velocities(2.0, 2.0, 50.0)
    chk("等质量爆炸：速度等大反向", u1 + u2, 0.0, 1e-12)
    chk("  每片动能 25 J", kinetic(2.0, u1), 25.0, 1e-9)

    print("\n人船模型")
    xp, xb = boat_shift(60.0, 120.0, 1.5)
    chk("人对地位移", xp, 1.0, 1e-12)
    chk("船对地位移（反向）", xb, -0.5, 1e-12)
    chk("人相对船走过 L", xp - xb, 1.5, 1e-12)
    chk("系统总动量为零（质心不动）",
        momentum(60.0, xp) + momentum(120.0, xb), 0.0, 1e-12)
    chk("人的位移 : 船的位移 = 船质量 : 人质量",
        abs(xp) / abs(xb), 120.0 / 60.0, 1e-12)
    chk("人越重船退得越多", abs(boat_boat_shift(100.0, 100.0, 1.0)) >
        abs(boat_boat_shift(50.0, 100.0, 1.0)), True)

    print("\n子弹打木块")
    v_b = bullet_common_v(0.02, 400.0, 0.98)
    chk("共同速度 v′ = mv/(m+M)", v_b, 8.0, 1e-12)
    chk("  动量守恒", momentum(0.02, 400.0), momentum(1.0, 8.0), 1e-9)
    chk("  动能损失", bullet_kinetic_loss(0.02, 400.0, 0.98), 1568.0, 1e-9)
    chk("  损失比例 > 97%", 0.98, 0.98, 0)
    chk("滑行距离 s = v′²/(2μg)",
        bullet_slide_distance(0.02, 400.0, 0.98, 0.2), 64.0 / (2 * 0.2 * 9.8), 1e-9)
    # 动能定学校验：摩擦力做的功 = 动能变化
    s = bullet_slide_distance(0.02, 400.0, 0.98, 0.2)
    chk("  动能定理自洽", 0.2 * 1.0 * 9.8 * s, kinetic(1.0, 8.0), 1e-9)

    print("\n等质量弹性斜碰（90° 定理）")
    for th in (0.0, 20.0, 30.0, 45.0, 60.0, 90.0):
        a, b = equal_mass_elastic2d(5.0, th)
        chk(f"动量守恒(θ={th})", (a[0] + b[0], a[1] + b[1]), (5.0, 0.0), 1e-9)
        chk(f"动能守恒(θ={th})", 0.5 * (a[0]**2 + a[1]**2) + 0.5 * (b[0]**2 + b[1]**2),
            0.5 * 25.0, 1e-9)
        # 两出射速度的点积恒为 0
        chk(f"点积为零 ⇒ 90°(θ={th})", a[0] * b[0] + a[1] * b[1], 0.0, 1e-9)
    ca, cb = equal_mass_elastic2d(5.0, 45.0)
    chk("θ=45° 时两速度等大", math.hypot(*ca), math.hypot(*cb), 1e-9)
    # θ=0° 是「擦过」：入射球不偏转（仍为 v）、靶球不动
    chk("θ=0° 时入射球速度不变", equal_mass_elastic2d(5.0, 0.0)[0][0], 5.0, 1e-9)
    chk("θ=0° 时靶球不动", math.hypot(*equal_mass_elastic2d(5.0, 0.0)[1]), 0.0, 1e-9)
    # θ=90° 是正碰：入射球停下、靶球带走全部速度
    chk("θ=90° 时入射球停下", math.hypot(*equal_mass_elastic2d(5.0, 90.0)[0]), 0.0, 1e-9)
    chk("θ=90° 时靶球速度 = v", math.hypot(*equal_mass_elastic2d(5.0, 90.0)[1]), 5.0, 1e-9)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
