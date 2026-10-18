#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
geo_kernel.py —— 自然地理可算部分的内核（天文几何 / 气象几何 / 水文收支）

判据（沿用 coverage-audit.md）：只做「给定参数 → 输出数值/坐标」的部分。
人文地理的区划与描述落在 ②/③，本内核不碰；`climate` 这类**依赖数据集**的
内容也不做（那会触发「数据页纪律」，成本全在数据）。

覆盖：
  · 太阳直射点纬度随日期的回归运动（δ）
  · 正午太阳高度角 H = 90° − |φ − δ|
  · 昼长与日出日落地方时（时角 ω：cos ω = −tanφ·tanδ）
  · 时区与地方时（经度每 15° 差 1 小时）
  · 等高线判读：相对高度 → 坡度
  · 对流层气温垂直递减率
  · 水循环水量平衡（降水 = 蒸发 + 径流）

设计原则（与全项目一致）：
  · **不手写数字**：所有结果由本内核现算，generate.py 只做排版。
  · **近似如实标注**：δ 用教材惯用的正弦近似（不是真正的黄道坐标解算），
    必须在页面与 SKILL.md 里说清。
  · 自检：python geo_kernel.py
"""

import math

import sympy as sp

__all__ = [
    "tex", "f", "num_str",
    "OBLIQUITY", "LAPSE_RATE", "DEG_PER_HOUR_ZONE",
    "declination", "date_from_doy", "doy_from_date",
    "hour_angle", "day_length", "sunrise_sunset", "day_status",
    "noon_altitude", "noon_side",
    "local_time", "timezone_of", "time_str",
    "slope_from_rise_run",
    "lapse_temp", "lapse_drop",
    "water_balance",
]

# ---------------------------------------------------------------- 常数（实测/约定）
OBLIQUITY = 23.44          # 黄赤交角，度（教材值 23°26′ ≈ 23.43°，此处取 23.44）
LAPSE_RATE = 6.0           # 对流层平均气温垂直递减率，°C/km（教材常用 6）
DEG_PER_HOUR_ZONE = 15.0   # 经度每 15° 差 1 小时 / 一个时区


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


# ---------------------------------------------------------------- 日期与赤纬

_MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def date_from_doy(n):
    """把「一年中的第 n 天」转成 (月, 日)，平年。"""
    n = int(n)
    if not 1 <= n <= 365:
        raise ValueError("年积日须在 1..365")
    m = 0
    while n > _MONTH_DAYS[m]:
        n -= _MONTH_DAYS[m]
        m += 1
    return m + 1, n


def doy_from_date(month, day):
    """(月, 日) → 年积日，平年。"""
    month, day = int(month), int(day)
    if not 1 <= month <= 12:
        raise ValueError("月份须在 1..12")
    if not 1 <= day <= _MONTH_DAYS[month - 1]:
        raise ValueError(f"{month} 月没有第 {day} 天")
    return sum(_MONTH_DAYS[:month - 1]) + day


def declination(n):
    """太阳直射点纬度 δ（度），n 为年积日。

    用教材惯用的**正弦近似**：
        δ = 23.44° · sin( 2π (n − 81) / 365 )
    它让春分（n≈81）δ=0、夏至（n≈172）δ=+23.44°、秋分（n≈264）δ≈0、
    冬至（n≈355）δ≈−23.44°。

    这不是真正的黄道坐标解算（真实 δ 还含偏心率、黄赤交角的缓慢变化），
    误差在 1° 量级 —— 对教学够用，但**必须如实标注为近似**。
    """
    return OBLIQUITY * math.sin(2.0 * math.pi * (int(n) - 81) / 365.0)


# ---------------------------------------------------------------- 昼长与太阳高度

def hour_angle(phi_deg, delta_deg):
    """半昼弧时角 ω（度）。cos ω = −tanφ·tanδ。

    返回 None 表示 |cos ω| > 1 —— 此时太阳整日不落或整日不出，
    没有「日出」可言（极昼 / 极夜）。
    """
    c = -math.tan(math.radians(phi_deg)) * math.tan(math.radians(delta_deg))
    if c > 1.0 + 1e-12 or c < -1.0 - 1e-12:
        return None
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def day_status(phi_deg, delta_deg):
    """返回 'normal' / 'polar_day' / 'polar_night'。"""
    c = -math.tan(math.radians(phi_deg)) * math.tan(math.radians(delta_deg))
    if c <= -1.0:
        return "polar_day"
    if c >= 1.0:
        return "polar_night"
    return "normal"


def day_length(phi_deg, delta_deg):
    """昼长（小时）。极昼返回 24，极夜返回 0。"""
    st = day_status(phi_deg, delta_deg)
    if st == "polar_day":
        return 24.0
    if st == "polar_night":
        return 0.0
    w = hour_angle(phi_deg, delta_deg)
    return 2.0 * w / DEG_PER_HOUR_ZONE


def sunrise_sunset(phi_deg, delta_deg):
    """日出、日落的地方太阳时（小时）。极昼极夜返回 None。

    地方太阳时 12:00 为当地正午，故日出 = 12 − ω/15，日落 = 12 + ω/15。
    """
    w = hour_angle(phi_deg, delta_deg)
    if w is None:
        return None
    half = w / DEG_PER_HOUR_ZONE
    return 12.0 - half, 12.0 + half


def noon_altitude(phi_deg, delta_deg):
    """正午太阳高度角 H = 90° − |φ − δ|（度）。

    H < 0 表示正午时太阳仍在地平线下 —— 即极夜。
    """
    return 90.0 - abs(phi_deg - delta_deg)


def noon_side(phi_deg, delta_deg):
    """正午太阳在正南还是正北：直射点在观测点之南则太阳在正南。"""
    if phi_deg > delta_deg:
        return "正南"
    if phi_deg < delta_deg:
        return "正北"
    return "天顶"


# ---------------------------------------------------------------- 时区与地方时

def timezone_of(lam_deg):
    """经度 → 时区编号（东正西负，0 为 0 时区）。

    用 floor(x+0.5) 而**不是** Python 的 round()：round() 是银行家舍入
    （round(6.5)=6），而画板侧用 Math.round（Math.round(6.5)=7）。
    两者在 .5 处会静默给出不同答案 —— 经度正好落在时区边界上时就会出错。
    floor(x+0.5) 与 JS Math.round 在正负两侧都逐位一致。
    """
    return int(math.floor(lam_deg / DEG_PER_HOUR_ZONE + 0.5))


def local_time(lam_deg, base_lam_deg, base_hour):
    """某经度的地方时（小时，0..24）。

    经度每差 15° 差 1 小时，东边早、西边晚：
        地方时 = 基准时 + (λ − λ₀) / 15
    """
    t = base_hour + (lam_deg - base_lam_deg) / DEG_PER_HOUR_ZONE
    return t % 24.0


def time_str(hours):
    """把小时数写成 HH:MM。"""
    t = hours % 24.0
    hh = int(math.floor(t))
    mm = int(round((t - hh) * 60))
    if mm == 60:
        hh, mm = (hh + 1) % 24, 0
    return f"{hh:02d}:{mm:02d}"


# ---------------------------------------------------------------- 等高线与坡度

def slope_from_rise_run(rise_m, run_km):
    """由相对高度（m）与水平距离（km）求坡度。

    返回 (百分比, 角度)。坡度 = 相对高度 / 水平距离，两者都要统一到 m。
    """
    if run_km <= 0:
        raise ValueError("水平距离必须为正")
    tan_t = rise_m / (run_km * 1000.0)
    return tan_t * 100.0, math.degrees(math.atan(tan_t))


# ---------------------------------------------------------------- 气温垂直递减

def lapse_drop(h_m, rate=LAPSE_RATE):
    """随海拔上升的气温下降量（°C）。"""
    return rate * h_m / 1000.0


def lapse_temp(T0, h_m, rate=LAPSE_RATE):
    """山脚温度 T0 时，海拔 h 米处的气温（°C）。"""
    return T0 - lapse_drop(h_m, rate)


# ---------------------------------------------------------------- 水量平衡

def water_balance(P_mm, evap_frac, area_km2):
    """流域水量平衡：降水 = 蒸发 + 径流。

    返回 {'E', 'R', 'vol'} 单位分别为 mm、mm、m³。
    径流总量 = 径流深(m) × 流域面积(m²) —— 注意单位换算（教材题的高频错点）。
    """
    if not 0.0 <= evap_frac <= 1.0:
        raise ValueError("蒸发比例须在 0..1")
    if area_km2 <= 0:
        raise ValueError("流域面积必须为正")
    E = P_mm * evap_frac
    R = P_mm - E
    vol = (R / 1000.0) * (area_km2 * 1e6)
    return {"E": E, "R": R, "vol": vol}


# ================================================================ 自检

def _selftest():
    bad = []

    def chk(name, got, want, tol=None):
        ok = (got == want) if tol is None else (abs(float(got) - float(want)) <= tol)
        shown = got if tol is None else f"{float(got):.6f}"
        print(f"  {'✓' if ok else '✗'} {name:46s} = {shown}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    print("日期与太阳直射点纬度")
    chk("春分 n=81 的 δ", declination(81), 0.0, 1e-9)
    chk("夏至 n=172 的 δ", declination(172), 23.44, 0.02)
    chk("冬至 n=355 的 δ", declination(355), -23.44, 0.02)
    chk("秋分附近 n=264 的 δ", declination(264), 0.0, 0.5)
    chk("date_from_doy(172)", date_from_doy(172), (6, 21))
    chk("date_from_doy(355)", date_from_doy(355), (12, 21))
    chk("doy_from_date(6, 22)", doy_from_date(6, 22), 173)
    chk("doy 往返自洽", doy_from_date(*date_from_doy(200)), 200)

    print("\n正午太阳高度")
    # 北京 φ≈40°，夏至正午太阳高度 ≈ 73.44°
    chk("北京夏至正午高度", noon_altitude(40, 23.44), 73.44, 1e-9)
    chk("北京冬至正午高度", noon_altitude(40, -23.44), 26.56, 1e-9)
    chk("赤道春分正午高度", noon_altitude(0, 0), 90.0, 1e-9)
    chk("北极圈内极夜时 H<0", noon_altitude(80, -23.44) < 0, True)
    chk("直射点以北的观测点看太阳在正南", noon_side(40, 23.44), "正南")
    chk("直射点以南的观测点看太阳在正北", noon_side(10, 23.44), "正北")

    print("\n昼长与日出日落")
    # 北京夏至昼长 ≈ 14h51m
    chk("北京夏至昼长(h)", day_length(40, 23.44), 14.844, 5e-3)
    chk("北京冬至昼长(h)", day_length(40, -23.44), 24 - 14.844, 5e-3)
    chk("赤道春分昼长 = 12", day_length(0, 0), 12.0, 1e-9)
    chk("赤道任意日的昼长都是 12", day_length(0, 23.44), 12.0, 1e-9)
    chk("夏至与冬至昼长之和为 24h", day_length(40, 23.44) + day_length(40, -23.44), 24.0, 1e-9)
    chk("北极圈内(φ=80)夏至极昼", day_status(80, 23.44), "polar_day")
    chk("北极圈内(φ=80)冬至极夜", day_status(80, -23.44), "polar_night")
    chk("极昼昼长 = 24h", day_length(80, 23.44), 24.0)
    chk("极夜昼长 = 0h", day_length(80, -23.44), 0.0)
    sr, ss = sunrise_sunset(0, 0)
    chk("赤道春分日出 6:00", sr, 6.0, 1e-9)
    chk("赤道春分日落 18:00", ss, 18.0, 1e-9)

    print("\n时区与地方时")
    chk("105°E 属东七区", timezone_of(105), 7)
    chk("120°E 属东八区", timezone_of(120), 8)
    chk("0° 属 0 时区", timezone_of(0), 0)
    # .5 边界：JS Math.round 向上取，Python round 会取偶 —— 必须一致
    chk("97.5° 应取 7（floor(6.5+0.5)=7，非银行家舍入的 6）", timezone_of(97.5), 7)
    chk("-97.5° 应取 -6（floor(-6.5+0.5)=-6）", timezone_of(-97.5), -6)
    # 北京(120°E) 12:00 时，乌鲁木齐(约 87.6°E) 的地方时
    t = local_time(87.6, 120.0, 12.0)
    chk("乌鲁木齐地方时(h)", t, 9.84, 1e-9)
    chk("  └ 写成 HH:MM", time_str(t), "09:50")
    chk("同经度地方时不变", local_time(120, 120, 12), 12.0, 1e-12)
    chk("东经 15° 早 1 小时", local_time(135, 120, 12), 13.0, 1e-12)
    chk("西经方向变晚", local_time(105, 120, 12), 11.0, 1e-12)

    print("\n等高线与坡度")
    pct, ang = slope_from_rise_run(400, 2.0)
    chk("400 m / 2 km 的坡度(%)", pct, 20.0, 1e-12)
    chk("  └ 角度(°)", ang, 11.3099, 1e-3)
    chk("400 m / 4 km 的坡度(%)", slope_from_rise_run(400, 4.0)[0], 10.0, 1e-12)
    chk("坡度与距离成反比", slope_from_rise_run(400, 2.0)[0]
        / slope_from_rise_run(400, 4.0)[0], 2.0, 1e-12)

    print("\n气温垂直递减")
    chk("20 °C 山脚，3000 m 处", lapse_temp(20, 3000), 2.0, 1e-12)
    chk("  └ 下降量", lapse_drop(3000), 18.0, 1e-12)
    chk("5000 m 处低于 0 °C", lapse_temp(20, 5000) < 0, True)
    chk("每千米降 6 °C", lapse_temp(20, 1000), 14.0, 1e-12)

    print("\n水循环水量平衡")
    wb = water_balance(800, 0.4, 1000)
    chk("降水 800 mm、蒸发占 40% → 蒸发", wb["E"], 320.0, 1e-9)
    chk("  └ 径流深", wb["R"], 480.0, 1e-9)
    chk("  └ 径流总量(m³)", wb["vol"], 4.8e8, 1.0)
    chk("降水 = 蒸发 + 径流", wb["E"] + wb["R"], 800.0, 1e-9)
    chk("单位换算自洽：480mm × 1000km²",
        (480 / 1000.0) * (1000 * 1e6), wb["vol"], 1e-6)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
