#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「自然地理」交互网页。

全部数值由 lib/geo_kernel.py 精确计算驱动（单一数据源）：太阳直射点纬度、
正午太阳高度、昼长与日出日落、时区与地方时、坡度、气温垂直递减、水量平衡
都由内核算出，**不手写数字**。

读数表达式（在浏览器里求值）与内核值在构建期逐条对账（_agree），
公式漂移当场停构建。特别注意 **Python 与 JS 的取整语义差异**：
Python 的 round() 是银行家舍入，JS 的 Math.round 不是 —— 涉及取整的读数
一律写成 floor(x+0.5)，与内核的实现保持一致。

依赖 sympy。用能 import sympy 的解释器运行：
    python scripts/generate.py <题型key> [输出.html]
    python scripts/generate.py list
    python scripts/generate.py all <输出目录>
    python scripts/generate.py random [seed] [输出.html]
"""

import math
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PLACEHOLDER = "__LESSON_DATA__"

sys.path.insert(0, str(SKILL_DIR.parent.parent / "shared"))
sys.path.insert(0, str(SKILL_DIR / "lib"))

import geo_kernel as K                       # noqa: E402
from skillkit import cli                     # noqa: E402

# =====================================================================
# 读数表达式 ↔ 内核 的对账机制
# =====================================================================

_MATHENV = {
    "sqrt": math.sqrt, "abs": abs, "min": min, "max": max, "pow": pow,
    "sign": lambda x: (x > 0) - (x < 0), "floor": math.floor, "ceil": math.ceil,
    "PI": math.pi, "E": math.e,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "exp": math.exp, "log": math.log,
}


def _jseval(expr, **env):
    return eval(expr.replace("^", "**"), {"__builtins__": {}}, {**_MATHENV, **env})


def _agree(label, expr, want, tol=1e-9, **env):
    got = _jseval(expr, **env)
    if abs(float(got) - float(want)) > tol:
        raise AssertionError(
            f"读数表达式与内核不一致（{label}）：\n"
            f"  表达式 {expr!r}\n  按表达式算 = {got!r}\n  内核给出   = {want!r}")
    return got


def ro(rid, label, expr, digits=4, unit=None):
    d = {"id": rid, "label": label, "type": "expr", "expr": expr, "digits": digits}
    if unit:
        d["unit"] = unit
    return d


def ro_status(rid, label, expr, rhs=0, op="==", ok="成立", bad="不成立"):
    return {"id": rid, "label": label, "type": "status", "expr": expr,
            "rhs": rhs, "op": op, "okText": ok, "badText": bad}


# 画板侧共用的表达式片段
_COSW = "cos(max(-1,min(1,-tan(phi*PI/180)*tan(delta*PI/180))))"


# =====================================================================
# 1) 太阳直射点的回归运动
# =====================================================================
def build_declination() -> dict:
    n0 = 172                                   # 夏至
    d0 = K.declination(n0)
    EXPR = "23.44*sin(2*PI*(N-81)/365)"
    for n in (81, 172, 264, 355, 1, 200):
        _agree(f"δ(n={n})", EXPR, K.declination(n), tol=1e-12, N=n)
    assert abs(d0 - K.OBLIQUITY) < 0.01

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "declination", "N": "N",
                  "caption": "黄线是太阳直射点纬度的全年轨迹；红点 = 当前日期"},
        "param": {"name": "N", "label": "一年中的第几天 $N$", "min": 1, "max": 365,
                  "step": 1, "value": n0, "unit": "", "standard": n0,
                  "ticks": ["1", "172 (夏至)", "355 (冬至)"]},
        "readouts": [
            ro("d", "太阳直射点纬度 $\\delta$", EXPR, 2, "°"),
            ro("ad", "纬度绝对值", "abs(" + EXPR + ")", 2, "°"),
            ro("gap", "距回归线的差", "23.44-abs(" + EXPR + ")", 2, "°"),
            ro_status("north", "直射点是否在北半球", EXPR, 0, ">",
                      "在北半球（春分→秋分）", "在南半球（秋分→春分）"),
        ],
        "constant": {"of": "ob", "label": "黄赤交角 23.44° 恒定（故 δ 只能在 ±23.44° 内摆动）"},
    }
    lesson = {
        "language": "zh-CN", "title": "太阳直射点的回归运动",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>地球绕日公转时，太阳直射点在地表南北移动。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>夏至（约 6 月 22 日）太阳直射哪条纬线？</li>"
            "<li>拖动滑块，$\\delta$ 的变化范围有多大？由什么决定？</li>"
            "<li>为什么一年里有两次 $\\delta = 0$？</li></ol>"),
        "answerLabel": "夏至的 $\\delta$",
        "answer": f"$\\delta \\approx +{K.f(K.OBLIQUITY,2)}^\\circ$（北回归线）",
    }
    steps = [
        {"title": "为什么范围恰好是 ±23.44°",
         "content": ("<p>地轴与公转轨道面（黄道面）的夹角是<b>黄赤交角</b>，约 "
                     f"${K.f(K.OBLIQUITY,2)}^\\circ$。地轴在公转中方向基本不变，"
                     "于是太阳直射点在南北回归线之间来回移动。</p>"
                     "<p>所以 $\\delta$ 的极值就是 $\\pm$ 黄赤交角 —— 图上的上下两条虚线"
                     "（南北回归线）正是这个角度的直接后果。</p>")},
        {"title": "δ 随日期的正弦规律",
         "content": ("<p>教材用一条正弦近似描述它："
                     f"$\\delta \\approx {K.f(K.OBLIQUITY,2)}^\\circ \\cdot "
                     "\\sin\\dfrac{{2\\pi(N-81)}}{{365}}$。</p>"
                     "<p>取 $N=81$（约 3 月 21 日）得 $\\delta=0$，即春分；"
                     "$N=172$（约 6 月 22 日）得 $\\delta=+23.44^\\circ$，即夏至。</p>"
                     "<p><b>这是近似</b>：真实 $\\delta$ 还含地球轨道偏心率与黄赤交角"
                     "的缓慢变化，本式的误差在 1° 量级，够教学用。</p>")},
        {"title": "为什么一年两次过赤道",
         "content": ("<p>正弦函数在一个周期内过零两次：一次在上升段（春分），"
                     "一次在下降段（秋分）。</p>"
                     "<p>拖动滑块看红点在曲线上的位置：$\\delta$ 从负升到正经过 0 是春分，"
                     "从正降到负经过 0 是秋分。这也是「春分秋分昼夜等长」的根源 ——"
                     "直射赤道时全球昼长都是 12 小时。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 正午太阳高度
# =====================================================================
def build_sunalt() -> dict:
    # δ 取黄赤交角常量本身：画板 scene.delta 写的就是 23.44，两边必须同源
    phi0, delta = 40.0, K.OBLIQUITY           # 北京、夏至
    H0 = K.noon_altitude(phi0, delta)
    EXPR = "90-abs(phi-23.44)"
    for phi in (-66.5, 0.0, 23.44, 40.0, 66.5, 80.0, 90.0):
        _agree(f"H(φ={phi})", EXPR, K.noon_altitude(phi, 23.44), tol=1e-12, phi=phi)
    assert abs(H0 - 73.44) < 1e-9

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "sunangle", "phi": "phi", "delta": 23.44,
                  "caption": "黄箭头 = 正午太阳光线；黄弧 = 高度角 H"},
        "param": {"name": "phi", "label": "观测地纬度 $\\varphi$", "min": -90, "max": 90,
                  "step": 1, "value": phi0, "unit": "°", "standard": phi0,
                  "ticks": ["-90", "0", "23.44 (回归线)", "40 (北京)", "66.5", "90"]},
        "readouts": [
            ro("H", "正午太阳高度 $H$", EXPR, 2, "°"),
            ro("gap", "$|\\varphi-\\delta|$", "abs(phi-23.44)", 2, "°"),
            ro("d", "当日直射点 $\\delta$", "23.44", 2, "°"),
            ro_status("rise", "正午太阳是否在地平线上", EXPR, 0, ">",
                      "在地平线上（有正午太阳）", "仍在地平线下（极夜）"),
        ],
        "constant": {"of": "delta", "label": "直射点固定在夏至的 +23.44°"},
    }
    lesson = {
        "language": "zh-CN", "title": "正午太阳高度角",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>夏至日（$\\delta = 23.44^\\circ$），观测者在北纬 $40^\\circ$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>正午太阳高度角是多少？</li>"
            "<li>拖动滑块改变纬度，$H$ 怎么变？什么时候 $H$ 会小于 0？</li>"
            "<li>此时太阳在正南还是正北？判据是什么？</li></ol>"),
        "answerLabel": "北纬 40° 的正午太阳高度",
        "answer": f"$H = {K.f(H0,2)}^\\circ$",
    }
    steps = [
        {"title": "公式：H = 90° − |φ − δ|",
         "content": ("<p>「正午太阳高度」就是太阳光线与地平面的夹角。"
                     "把观测纬度 $\\varphi$ 与直射点纬度 $\\delta$ 之差折算过来即可：</p>"
                     "<p>$H = 90^\\circ - |\\varphi - \\delta|$。</p>"
                     "<p>直观理解：$|\\varphi-\\delta|$ 越小，观测地离直射点越近，"
                     "太阳越靠近天顶，$H$ 越大。</p>")},
        {"title": "代入计算",
         "content": ("<p>$|\\varphi-\\delta| = |40 - 23.44| = "
                     f"{K.f(abs(phi0-delta),2)}^\\circ$，</p>"
                     f"<p>$H = 90 - {K.f(abs(phi0-delta),2)} = {K.f(H0,2)}^\\circ$。</p>"
                     "<p>把纬度拖到 $\\varphi=\\delta=23.44^\\circ$ 时 $|\\varphi-\\delta|=0$，"
                     "$H=90^\\circ$ —— 太阳正位于天顶，这是「直射」的含义。</p>")},
        {"title": "H < 0 与太阳方位",
         "content": ("<p>把纬度拖到 $\\varphi = 80^\\circ$：$|\\varphi-\\delta| = 56.56^\\circ$，"
                     "$H = 33.44^\\circ$。继续往南拖到 $\\varphi = -80^\\circ$，"
                     "此时该地是极夜，$H$ 变成负值 —— 公式仍然成立，但「正午太阳」"
                     "根本不出现在地平线上。</p>"
                     "<p>方位判据：比较 $\\varphi$ 与 $\\delta$。$\\varphi>\\delta$ 时"
                     "直射点在观测点之南，太阳在<b>正南</b>；反之在<b>正北</b>。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 昼长与日出日落
# =====================================================================
def build_daylight() -> dict:
    # 同 build_sunalt：δ 用黄赤交角常量，与画板 scene.delta 同源
    phi0, delta = 40.0, K.OBLIQUITY
    w0 = K.hour_angle(phi0, delta)
    L0 = K.day_length(phi0, delta)
    sr0, ss0 = K.sunrise_sunset(phi0, delta)
    EXPR_W = f"acos(max(-1,min(1,-tan(phi*PI/180)*tan(23.44*PI/180))))*180/PI"
    EXPR_L = "2*" + EXPR_W + "/15"
    # 时角只在**非极区**比较：极昼极夜时内核有意返回 None（无日出可谈）
    for phi in (-60.0, -40.0, 0.0, 40.0, 60.0):
        _agree(f"ω(φ={phi})", EXPR_W, K.hour_angle(phi, 23.44), tol=1e-9, phi=phi)
    # 昼长则连极区一起比：画板用夹取到 ±1 的 acos，与内核的 24/0 分支必须一致
    for phi in (-89.0, -80.0, -40.0, 0.0, 40.0, 80.0, 89.0):
        _agree(f"昼长(φ={phi})", EXPR_L, K.day_length(phi, 23.44), tol=1e-9, phi=phi)
    _agree("日出(φ=40)", "12-" + EXPR_W + "/15", sr0, tol=1e-9, phi=phi0)
    _agree("日落(φ=40)", "12+" + EXPR_W + "/15", ss0, tol=1e-9, phi=phi0)
    assert abs(L0 - 14.8446) < 1e-3

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "daycurve", "phi": "phi", "delta": 23.44,
                  "caption": "昼长随纬度的变化；粉线是极昼 / 极夜边界"},
        "param": {"name": "phi", "label": "纬度 $\\varphi$", "min": -90, "max": 90,
                  "step": 1, "value": phi0, "unit": "°", "standard": phi0,
                  "ticks": ["-90", "0", "40 (北京)", "66.5 (极圈)", "90"]},
        "readouts": [
            ro("w", "半昼弧时角 $\\omega$", EXPR_W, 3, "°"),
            ro("L", "昼长", EXPR_L, 4, "h"),
            ro("sr", "日出（地方时）", "12-" + EXPR_W + "/15", 3, "h"),
            ro("ss", "日落（地方时）", "12+" + EXPR_W + "/15", 3, "h"),
            ro_status("eq", "是否昼夜等长", EXPR_L, 12, "==",
                      "昼夜等长 12 小时", "昼长夜短或昼短夜长"),
        ],
        "constant": {"of": "delta", "label": "直射点固定在夏至的 +23.44°"},
    }
    lesson = {
        "language": "zh-CN", "title": "昼长与日出日落",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>夏至日（$\\delta = 23.44^\\circ$），求北纬 $40^\\circ$ 的昼长与日出日落时刻。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>昼长是多少小时？日出、日落各在地方时几点？</li>"
            "<li>赤道上的昼长是多少？为什么与日期无关？</li>"
            "<li>拖到 $\\varphi = 80^\\circ$ 与 $\\varphi = -80^\\circ$，分别发生什么？</li></ol>"),
        "answerLabel": "北纬 40° 的昼长",
        "answer": f"$\\approx {K.f(L0,2)}$ h（约 {int(L0)} 小时 {round((L0%1)*60)} 分）",
    }
    steps = [
        {"title": "时角 ω：昼长的几何来源",
         "content": ("<p>把地球自转看成绕轴转动，太阳从地平线升起到落下扫过的角度是 "
                     "$2\\omega$（$\\omega$ 叫半昼弧时角）。由球面三角可得</p>"
                     "<p>$\\cos\\omega = -\\tan\\varphi \\cdot \\tan\\delta$。</p>"
                     "<p>再按「每小时 15°」换算：昼长 $= \\dfrac{{2\\omega}}{{15}}$ 小时。</p>")},
        {"title": "代入计算",
         "content": ("<p>$\\cos\\omega = -\\tan40^\\circ\\cdot\\tan23.44^\\circ "
                     f"= {K.f(-math.tan(math.radians(phi0))*math.tan(math.radians(delta)),4)}$，"
                     f"故 $\\omega \\approx {K.f(w0,3)}^\\circ$。</p>"
                     f"<p>昼长 $= \\dfrac{{2\\times{K.f(w0,3)}}}{{15}} "
                     f"\\approx {K.f(L0,4)}$ h；日出 $\\approx{K.f(sr0,3)}$ h，"
                     f"日落 $\\approx{K.f(ss0,3)}$ h。</p>")},
        {"title": "极昼与极夜：cosω 越过 ±1",
         "content": ("<p>当 $|\\cos\\omega| > 1$ 时方程无解 —— 太阳整日不落（极昼）"
                     "或整日不出（极夜）。临界纬度是 $|\\varphi| = 90^\\circ - |\\delta| "
                     f"= {K.f(90-abs(delta),2)}^\\circ$，正是极圈。</p>"
                     "<p>所以拖到 $\\varphi=80^\\circ$（夏至）得到 <b>24 小时</b>极昼；"
                     "拖到 $\\varphi=-80^\\circ$ 得到 <b>0 小时</b>极夜。</p>"
                     "<p>另外注意赤道：$\\tan0=0$ 使 $\\cos\\omega=0$，"
                     "$\\omega=90^\\circ$，昼长恒为 12 小时 —— 与日期无关。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 时区与地方时
# =====================================================================
def build_timezone() -> dict:
    # 用「北京实际经度 116°E」而非 87.6°E：既能落在滑块步长上，
    # 又正好演示「地方时 ≠ 区时」（东八区中央经线是 120°E）。
    lam0, base_lam, base_hour = 116.0, 120.0, 12.0
    t0 = K.local_time(lam0, base_lam, base_hour)
    z0 = K.timezone_of(lam0)
    EXPR_T = "(12+(lam-120)/15+24)-24*floor((12+(lam-120)/15+24)/24)"
    for lam in (-180.0, -120.0, 0.0, 116.0, 120.0, 135.0, 180.0):
        _agree(f"地方时(λ={lam})", EXPR_T, K.local_time(lam, 120, 12), tol=1e-12, lam=lam)
    _agree("经度差", "lam-120", lam0 - base_lam, tol=1e-12, lam=lam0)
    _agree("时差(h)", "(lam-120)/15", (lam0 - base_lam) / 15, tol=1e-12, lam=lam0)
    _agree("时区号", "floor(lam/15+0.5)", z0, lam=lam0)
    assert z0 == 8
    assert K.time_str(t0) == "11:44"

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "globe", "lam": "lam", "base_lam": base_lam,
                  "base_hour": base_hour,
                  "caption": "横向色带是时区；黄线 = 基准经线 120°E，红线 = 当前经度"},
        "param": {"name": "lam", "label": "目标经度 $\\lambda$", "min": -180, "max": 180,
                  "step": 1, "value": lam0, "unit": "°", "standard": lam0,
                  "ticks": ["-180", "0", "116 (北京实址)", "120 (中央经线)", "180"]},
        "readouts": [
            ro("dt", "经度差 $\\lambda-\\lambda_0$", "lam-120", 1, "°"),
            ro("dh", "时差 $(\\lambda-\\lambda_0)/15$", "(lam-120)/15", 3, "h"),
            ro("lt", "该地地方时", EXPR_T, 3, "h"),
            ro("zone", "所属时区（东正西负）", "floor(lam/15+0.5)", 0),
            ro_status("same", "是否与基准经线同时刻", "lam-120", 0, "==",
                      "同经度 → 地方时相同", "不同经度 → 地方时不同"),
        ],
        "constant": {"of": "base", "label": "基准经线 120°E 恒为 12:00"},
    }
    lesson = {
        "language": "zh-CN", "title": "经度、时区与地方时",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>东八区的中央经线是 $120^\\circ$E。北京市区的实际经度约 $116^\\circ$E。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>当中央经线为 $12{{:}}00$ 时，$116^\\circ$E 的地方时是几点？</li>"
            "<li>它与区时（$12{{:}}00$）差多少分钟？为什么？</li>"
            "<li>北京属于哪个时区？拖动滑块到 $180^\\circ$ 与 $-180^\\circ$，差多少小时？</li></ol>"),
        "answerLabel": "116°E 的地方时",
        "answer": f"${K.time_str(t0)}$（比区时晚 ${K.f(abs(base_lam-lam0)/15*60,0)}$ 分钟）",
    }
    steps = [
        {"title": "经度每 15° 差 1 小时",
         "content": ("<p>地球 24 小时自转 $360^\\circ$，所以每 $15^\\circ$ 对应 1 小时，"
                     "每 $1^\\circ$ 对应 4 分钟。</p>"
                     "<p>方向：地球自西向东转，所以<b>东边的地方时更早</b>"
                     "（先看到日出）。</p>")},
        {"title": "代入计算",
         "content": ("<p>经度差 $= 116 - 120 = "
                     f"{K.f(lam0-base_lam,1)}^\\circ$，"
                     f"时差 $= \\dfrac{{{K.f(lam0-base_lam,1)}}}{{15}} "
                     f"= {K.f((lam0-base_lam)/15,4)}$ 小时 $= "
                     f"{K.f((lam0-base_lam)/15*60,1)}$ 分钟。</p>"
                     "<p>$116^\\circ$E 在中央经线西边，地方时应更晚：</p>"
                     f"<p>$12{{:}}00 + ({K.f((lam0-base_lam)/15,4)}) = "
                     f"{K.time_str(t0)}$。</p>")},
        {"title": "地方时 ≠ 区时（本题真正的考点）",
         "content": ("<p>地方时随经度<b>连续</b>变化，每度 4 分钟，用它生活会乱套。"
                     "所以按每 $15^\\circ$ 划一个**时区**，区内统一用中央经线的地方时，"
                     "这就是<b>区时</b>。</p>"
                     f"<p>北京实址 $116^\\circ$E 的地方时是 ${K.time_str(t0)}$，"
                     "而东八区的区时是 $12{{:}}00$ —— 两者差 "
                     f"${K.f(abs(base_lam-lam0)/15*60,0)}$ 分钟。日常说的"
                     "「北京时间」是<b>区时</b>，不是北京当地的地方时。</p>"
                     "<p>注意时区号是取整的"
                     f"（$\\lfloor 116/15 + 0.5 \\rfloor = {z0}$），"
                     "而地方时是连续的 —— 图上色带（时区）与红线（真实经度）的错位就是这个区别。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 等高线判读：坡度
# =====================================================================
def build_terrain() -> dict:
    rise, run0, dz = 400, 2.0, 100
    pct, ang = K.slope_from_rise_run(rise, run0)
    EXPR_PCT = "400/(run*1000)*100"
    EXPR_ANG = "atan(400/(run*1000))*180/PI"
    for run in (0.5, 1.0, 2.0, 4.0, 5.0):
        _agree(f"坡度%(run={run})", EXPR_PCT, K.slope_from_rise_run(rise, run)[0],
               tol=1e-9, run=run)
        _agree(f"坡度°(run={run})", EXPR_ANG, K.slope_from_rise_run(rise, run)[1],
               tol=1e-9, run=run)
    assert abs(pct - 20.0) < 1e-9
    assert rise % dz == 0

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "contour", "run": "run", "rise": rise, "dz": dz, "lmax": 5.0,
                  "caption": "地形剖面：A 在 100 m 等高线、B 在 500 m 等高线"},
        "param": {"name": "run", "label": "A、B 的水平距离", "min": 0.5, "max": 5.0,
                  "step": 0.1, "value": run0, "unit": "km", "standard": run0,
                  "ticks": ["0.5", "2.0 (题设)", "5.0"]},
        "readouts": [
            ro("rise", "相对高度", "400", 0, "m"),
            ro("pct", "坡度（百分比）", EXPR_PCT, 2, "%"),
            ro("ang", "坡度（角度）", EXPR_ANG, 3, "°"),
            ro("per", "每千米升高", "400/run", 1, "m/km"),
            ro_status("steep", "坡度是否超过 15%", EXPR_PCT, 15, ">",
                      "陡坡（>15%）", "缓坡（≤15%）"),
        ],
        "constant": {"of": "rise", "label": "相对高度恒为 400 m（100 m → 500 m）"},
    }
    lesson = {
        "language": "zh-CN", "title": "等高线判读与坡度计算",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>地形图上，$A$ 点位于 $100$ m 等高线，$B$ 点位于 $500$ m 等高线，"
            "等高距为 $100$ m。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>$A$、$B$ 的相对高度是多少？</li>"
            "<li>若图上水平距离为 $2$ km，坡度是多少（百分比与角度）？</li>"
            "<li>拖动滑块，坡度与水平距离是什么关系？为什么？</li></ol>"),
        "answerLabel": "水平距离 2 km 时的坡度",
        "answer": f"${K.f(pct,1)}\\%$（约 ${K.f(ang,2)}^\\circ$）",
    }
    steps = [
        {"title": "相对高度只看等高线差值",
         "content": ("<p>$A$ 在 100 m、$B$ 在 500 m，相对高度 $= 500 - 100 = 400$ m。"
                     "它与两点在地图上的距离<b>无关</b> —— 这是本页的定值。</p>"
                     "<p>等高距（相邻两线的高差）是 100 m，所以 A 到 B 跨了 4 条等高线。</p>")},
        {"title": "坡度 = 相对高度 ÷ 水平距离",
         "content": ("<p>坡度是竖直升高与水平前进之比。两个量必须先统一单位：</p>"
                     "<p>$\\tan\\theta = \\dfrac{{400\\ \\mathrm{{m}}}}{{2\\ \\mathrm{{km}}}}"
                     "= \\dfrac{{400}}{{2000}} = 0.2$，即 $20\\%$。</p>"
                     "<p>换成角度：$\\theta = \\arctan(0.2) \\approx "
                     f"{K.f(ang,2)}^\\circ$。</p>"
                     "<p><b>mm/m/km 混用</b>是这类题最常见的错误 ——"
                     "把 2 km 当成 2 m 会算出 20000% 这种荒谬结果。</p>")},
        {"title": "坡度与水平距离成反比",
         "content": ("<p>相对高度固定时，$\\tan\\theta \\propto \\dfrac{{1}}{{水平距离}}$ ——"
                     "两点在图上越靠近，说明实际坡越陡。</p>"
                     "<p>把距离拖到 0.5 km：坡度变成 80%；拖到 5 km：只有 8%。"
                     "这就是等高线「密集 ⇒ 陡、稀疏 ⇒ 缓」的定量解释。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 气温垂直递减率
# =====================================================================
def build_lapse() -> dict:
    T0, h0, hmax, rate = 20.0, 3000.0, 5000.0, K.LAPSE_RATE
    T_h = K.lapse_temp(T0, h0, rate)
    EXPR_T = "20-6*h/1000"
    EXPR_D = "6*h/1000"
    for h in (0.0, 1000.0, 3000.0, 5000.0):
        _agree(f"T(h={h})", EXPR_T, K.lapse_temp(T0, h, rate), tol=1e-12, h=h)
        _agree(f"降温(h={h})", EXPR_D, K.lapse_drop(h, rate), tol=1e-12, h=h)
    assert abs(T_h - 2.0) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "atmos", "T0": T0, "h": "h", "hmax": hmax, "rate": rate,
                  "caption": "红线是气温随海拔的递减；蓝虚线是 0 °C 雪线"},
        "param": {"name": "h", "label": "海拔 $h$", "min": 0, "max": hmax, "step": 50,
                  "value": h0, "unit": "m", "standard": h0,
                  "ticks": ["0", "3000 (题设)", "5000"]},
        "readouts": [
            ro("T", "该海拔气温", EXPR_T, 2, "°C"),
            ro("d", "较山脚降温", EXPR_D, 2, "°C"),
            ro("km", "海拔（千米）", "h/1000", 2, "km"),
            ro_status("freeze", "是否已到 0 °C 以下", EXPR_T, 0, "<",
                      "在 0 °C 以下（可能积雪/结冰）", "仍在 0 °C 以上"),
        ],
        "constant": {"of": "rate", "label": "递减率恒为 6 °C/km（改变海拔不动它）"},
    }
    lesson = {
        "language": "zh-CN", "title": "气温的垂直递减率",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>某山山脚（海拔 $0$ m）气温 $20$ °C，对流层平均气温垂直递减率约 "
            "$6$ °C/km。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>海拔 $3000$ m 处的气温是多少？</li>"
            "<li>从山脚上升到多少米时气温降到 $0$ °C？</li>"
            "<li>拖动滑块，为什么气温与海拔是直线关系？</li></ol>"),
        "answerLabel": "3000 m 处的气温",
        "answer": f"${K.f(T_h,1)}$ °C",
    }
    steps = [
        {"title": "「每上升 1000 m 降 6 °C」",
         "content": ("<p>在对流层，热量主要来自地面辐射，所以离地面越高，得到的热量越少。"
                     f"平均每上升 1 km 降温约 ${K.f(rate,0)}$ °C。</p>"
                     "<p>这是个**统计平均值**：实际还要受水汽、天气系统影响，"
                     "干空气约 1 °C/100 m，湿空气更小。</p>")},
        {"title": "代入计算",
         "content": ("<p>降温量 $= \\dfrac{{6}}{{1000}}\\times 3000 = "
                     f"{K.f(K.lapse_drop(h0, rate),1)}$ °C。</p>"
                     f"<p>该处气温 $= 20 - {K.f(K.lapse_drop(h0, rate),1)} = "
                     f"{K.f(T_h,1)}$ °C。</p>")},
        {"title": "为什么是直线，以及雪线",
         "content": ("<p>公式 $T = T_0 - \\dfrac{{6}}{{1000}}h$ 是 $h$ 的一次函数，"
                     "所以图上是一条<b>直线</b>（斜率为 $-0.006$ °C/m）。</p>"
                     "<p>令 $T=0$ 得 $h = \\dfrac{{T_0}}{{6}}\\times1000 = "
                     f"{K.f(T0/rate*1000,0)}$ m —— 这就是图中蓝虚线（雪线）的高度。"
                     "把它代入滑块即可看到气温正好过零点。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 水循环水量平衡
# =====================================================================
def build_water() -> dict:
    P, e0, area = 800.0, 0.4, 1000.0
    wb = K.water_balance(P, e0, area)
    EXPR_E = "800*e"
    EXPR_R = "800*(1-e)"
    EXPR_V = "(800*(1-e)/1000)*1000*1e6"
    for e in (0.0, 0.25, 0.4, 0.75, 1.0):
        _agree(f"蒸发(e={e})", EXPR_E, K.water_balance(P, e, area)["E"], tol=1e-9, e=e)
        _agree(f"径流深(e={e})", EXPR_R, K.water_balance(P, e, area)["R"], tol=1e-9, e=e)
        _agree(f"径流总量(e={e})", EXPR_V, K.water_balance(P, e, area)["vol"],
               tol=1.0, e=e)
    # 水量平衡恒等式
    _agree("降水 = 蒸发 + 径流", EXPR_E + "+" + EXPR_R, P, tol=1e-9, e=e0)
    assert wb["E"] + wb["R"] == P

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "basin", "P": P, "e": "e", "area": area,
                  "caption": "总柱高是降水；蓝段蒸发、绿段径流，两段之和恒等于总柱"},
        "param": {"name": "e", "label": "蒸发占降水的比例 $e$", "min": 0.0, "max": 1.0,
                  "step": 0.02, "value": e0, "unit": "", "standard": e0,
                  "ticks": ["0", "0.4 (题设)", "1.0"]},
        "readouts": [
            ro("E", "蒸发量 $P e$", EXPR_E, 1, "mm"),
            ro("R", "径流深 $P(1-e)$", EXPR_R, 1, "mm"),
            ro("sum", "两者之和（应恒为 P）", EXPR_E + "+" + EXPR_R, 1, "mm"),
            ro("vol", "径流总量", EXPR_V + "/1e8", 3, "×10⁸ m³"),
            ro_status("bal", "水量是否平衡", EXPR_E + "+" + EXPR_R, P, "==",
                      "平衡（降水 = 蒸发 + 径流）", "不平衡"),
        ],
        "constant": {"of": "P", "label": "年降水量恒为 800 mm；流域面积 1000 km²"},
    }
    lesson = {
        "language": "zh-CN", "title": "水循环与水量平衡",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>某流域面积 $1000$ km²，多年平均年降水量 $800$ mm，"
            "其中蒸发量占 $40\\%$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>年径流深是多少 mm？</li>"
            "<li>折算成年径流总量是多少 m³？</li>"
            "<li>拖动滑块，为什么两段之和始终等于总降水？</li></ol>"),
        "answerLabel": "年径流总量",
        "answer": f"$\\approx {K.num_str(wb['vol'],3)}$ m³",
    }
    steps = [
        {"title": "水量平衡方程",
         "content": ("<p>对一个闭合流域，进入的水等于出去的水（忽略蓄水变化）：</p>"
                     "<p>降水 $=$ 蒸发 $+$ 径流。</p>"
                     f"<p>已知蒸发占 $40\\%$，所以蒸发 $= 800\\times0.4 = "
                     f"{K.f(wb['E'],1)}$ mm，径流深 $= 800 - {K.f(wb['E'],1)} = "
                     f"{K.f(wb['R'],1)}$ mm。</p>")},
        {"title": "径流深 → 径流总量（单位是关键）",
         "content": ("<p>径流深是「铺在流域上的水层厚度」，乘面积即得体积。"
                     "但单位必须统一到<b>米</b>与<b>平方米</b>：</p>"
                     f"<p>$R = {K.f(wb['R'],1)}$ mm $= {K.f(wb['R']/1000,3)}$ m，</p>"
                     "<p>$S = 1000\\ \\mathrm{{km}}^2 = 1000\\times10^6 = 10^9\\ \\mathrm{{m}}^2$，</p>"
                     f"<p>$V = {K.f(wb['R']/1000,3)}\\times10^9 = "
                     f"{K.num_str(wb['vol'],3)}\\ \\mathrm{{m}}^3$。</p>"
                     "<p><b>mm 直接乘 km²</b>会错 10⁶ 倍 —— 这是本页最想拦住的一步。</p>")},
        {"title": "为什么两段之和恒定",
         "content": ("<p>因为 $R = P - E$ 是**定义式**：径流不是独立变量，"
                     "而是平衡方程的余项。所以拖动滑块时，蓝色段（蒸发）与"
                     "绿色段（径流）此消彼长，总柱高（降水）纹丝不动。</p>"
                     "<p>读数里专门放了一个「两者之和」并把它与 800 mm 比对，"
                     "任何一侧写错都会当场翻红。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "declination": build_declination,
    "sunalt": build_sunalt,
    "daylight": build_daylight,
    "timezone": build_timezone,
    "terrain": build_terrain,
    "lapse": build_lapse,
    "water": build_water,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="自然地理 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
