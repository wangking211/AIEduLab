#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「机械振动 · 机械波 · 光」交互网页。

全部数值由 lib/waveoptics_kernel.py 现算，**不手写数字**。

覆盖七个题型（选择性必修一）：
  shm           简谐运动（参考圆 + x-t 曲线 + v/a）
  wavemotion    横波的传播（波形图 + 质点振动方向 + 波速）
  standing      驻波（波节 / 波腹）
  beat          波的叠加与拍（拍频）
  interference  双缝干涉（条纹间距 = Lλ/d）
  refraction    折射定律与全反射（临界角）
  thinlens      凸透镜成像（1/u + 1/v = 1/f）

依赖 sympy：
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

import waveoptics_kernel as K                 # noqa: E402
from skillkit import cli                      # noqa: E402

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
    if got is None or want is None:
        raise AssertionError(f"{label}: 有一侧为 None")
    d = abs(float(got) - float(want))
    if d > tol * max(1.0, abs(float(want))):
        raise AssertionError(
            f"读数表达式与内核不一致（{label}）：\n"
            f"  表达式 {expr!r}\n  按表达式算 = {got!r}\n  内核给出   = {want!r}")


def ro(rid, label, expr, digits=4, unit=None):
    d = {"id": rid, "label": label, "type": "expr", "expr": expr, "digits": digits}
    if unit:
        d["unit"] = unit
    return d


def ro_status(rid, label, expr, rhs=0, op="==", ok="成立", bad="不成立"):
    return {"id": rid, "label": label, "type": "status", "expr": expr,
            "rhs": rhs, "op": op, "okText": ok, "badText": bad}


# =====================================================================
# 1) 简谐运动
# =====================================================================
SHM_A, SHM_T = 1.0, 2.0
SHM_W = math.pi                                  # ω = 2π/T = π rad/s
EXPR_SX = f"{SHM_A}*sin({SHM_W}*t)"
EXPR_SV = f"{SHM_A}*{SHM_W}*cos({SHM_W}*t)"
EXPR_SA = f"-{SHM_A}*{SHM_W}*{SHM_W}*sin({SHM_W}*t)"


def build_shm() -> dict:
    for t in (0.0, 0.25, 0.5, 1.0, 1.5, 3.0):
        _agree(f"x(t={t})", EXPR_SX, K.shm_x(SHM_A, SHM_W, t), tol=1e-12, t=t)
        _agree(f"v(t={t})", EXPR_SV, K.shm_v(SHM_A, SHM_W, t), tol=1e-12, t=t)
        _agree(f"a(t={t})", EXPR_SA, K.shm_a(SHM_A, SHM_W, t), tol=1e-12, t=t)
        _agree(f"相位(t={t})", "180*t", K.shm_phase(SHM_W, t), tol=1e-12, t=t)
    _agree("T = 2π/ω", f"2*PI/{SHM_W}", K.shm_period(SHM_W), tol=1e-12)
    _agree("a = −ω²x 的恒等关系", EXPR_SA,
           _jseval(f"-{SHM_W}*{SHM_W}*({EXPR_SX})", t=0.37), tol=1e-12, t=0.37)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "shm", "t": "t",
                  "caption": "参考圆的匀速圆周运动在竖直直径上的投影，就是右侧的简谐运动"},
        "param": {"name": "t", "label": "时间 $t$", "min": 0, "max": 4,
                  "step": 0.05, "value": 0.5, "unit": "s", "standard": 0.5,
                  "ticks": ["0", "0.5 (=T/4)", "1", "2 (=T)", "4"]},
        "readouts": [
            ro("x", "位移 $x = A\\sin\\omega t$", EXPR_SX, 4, "m"),
            ro("v", "速度 $v = A\\omega\\cos\\omega t$", EXPR_SV, 4, "m/s"),
            ro("a", "加速度 $a = -\\omega^2 x$", EXPR_SA, 4, "m/s²"),
            ro("ph", "相位 $\\omega t$", "180*t", 1, "°"),
            ro("per", "周期 $T$（定值）", f"{SHM_T}", 1, "s"),
            ro_status("ext", "是否在最大位移处（$|x| = A$）",
                      f"abs({EXPR_SX})", 0.999, ">",
                      "在最大位移：v = 0、|a| 最大", "不在最大位移处"),
        ],
        "constant": {"of": "per", "label": "$T = 2$ s、$\\omega = \\pi$ rad/s 是定值 —— 只让时间走"},
    }
    lesson = {
        "language": "zh-CN", "title": "简谐运动与参考圆",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>某质点在 $x$ 轴上做简谐运动，$x = A\\sin\\omega t$，"
            "其中 $A = 1\\ \\mathrm{m}$、$T = 2\\ \\mathrm{s}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $\\omega$，并说明 $x$、$v$、$a$ 随时间怎么变；</li>"
            "<li>拖动滑块，什么时候 $v = 0$？什么时候 $|a|$ 最大？</li>"
            "<li>为什么说 $a = -\\omega^2 x$ 就是「回复力与位移反向」？</li></ol>"),
        "answerLabel": "$t = 0.5$ s（即 $T/4$）时的状态",
        "answer": f"$x = {K.f(K.shm_x(SHM_A, SHM_W, 0.5), 3)}$ m，"
                  f"$v = {K.f(K.shm_v(SHM_A, SHM_W, 0.5), 3)}$ m/s，"
                  f"$a = {K.f(K.shm_a(SHM_A, SHM_W, 0.5), 3)}$ m/s²",
    }
    steps = [
        {"title": "什么叫「简谐」",
         "content": ("<p>合力（也就是回复力）与位移**成正比、方向相反**：$F = -kx$。"
                     "由牛顿第二定律 $ma = -kx$ 得 $a = -\\omega^2 x$，"
                     "其中 $\\omega = \\sqrt{k/m}$。</p>"
                     "<p>这个方程的解决就是正弦式函数 —— 所以「简谐运动」"
                     "等价于「位移按正弦规律变化」。本页取 $x = A\\sin\\omega t$。</p>"
                     f"<p>$T = 2\\ \\mathrm{{s}}$ ⇒ $\\omega = \\dfrac{{2\\pi}}{{T}} = \\pi\\ \\mathrm{{rad/s}}$。</p>")},
        {"title": "参考圆：把振动看成圆周运动的投影",
         "content": ("<p>图上左侧是一个半径 $R = A$ 的「参考圆」，一个点在上面**匀速转动**，"
                     "角速度就是 $\\omega$。</p>"
                     "<p>把它投影到竖直直径上（黄虚线），投影点的坐标恰好是 $A\\sin\\omega t$ —— "
                     "与右侧的 $x$-$t$ 曲线**完全相同**。</p>"
                     "<p>所以简谐运动可以看成「匀速圆周运动的投影」。这个看法有个直接好处："
                     "相位 $\\omega t$ 就是那个转过的角度，读数区里直接给出度数。</p>")},
        {"title": "v 与 a 的规律",
         "content": ("<p>对 $x = A\\sin\\omega t$ 求导：</p>"
                     "<p>$v = A\\omega\\cos\\omega t$（也是正弦式的，但提前 $\\dfrac{\\pi}{2}$）；</p>"
                     "<p>$a = -A\\omega^2\\sin\\omega t = -\\omega^2 x$。</p>"
                     "<p>于是：**在最大位移处** $v = 0$ 而 $|a|$ 最大；"
                     "**过平衡位置时** $|v|$ 最大而 $a = 0$。"
                     "把滑块拖到 $t = 0.5\\ \\mathrm{s}$（$T/4$）就会出现第一种情况 —— "
                     "状态灯会亮。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 横波的传播
# =====================================================================
W_A, W_T, W_LAM = 1.0, 2.0, 4.0
W_XP = 5.0                                       # 被标记的质点 P 的位置
EXPR_WY = f"{W_A}*sin(2*PI*(t/{W_T}-{W_XP}/{W_LAM}))"
EXPR_WV = f"{W_A}*(2*PI/{W_T})*cos(2*PI*(t/{W_T}-{W_XP}/{W_LAM}))"


def build_wave() -> dict:
    for t in (0.0, 0.25, 0.5, 1.0, 1.5, 3.0):
        _agree(f"y_P(t={t})", EXPR_WY, K.wave_y(W_A, W_T, W_LAM, W_XP, t), tol=1e-12, t=t)
        _agree(f"v_P(t={t})", EXPR_WV, K.particle_velocity(W_A, W_T, W_LAM, W_XP, t), tol=1e-12, t=t)
    _agree("波速 v = λ/T", f"{W_LAM}/{W_T}", K.wave_speed(W_LAM, W_T), tol=1e-12)
    # 波沿 +x 传播：t 增大时同一相位点右移
    _agree("波沿 +x 传播", f"{W_A}*sin(2*PI*(0.5/{W_T}-2.0/{W_LAM}))",
           K.wave_y(W_A, W_T, W_LAM, 1.0, 0.0), tol=1e-12)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "wave", "t": "t",
                  "caption": "粉点是固定质点 P（x = 5 m）：它只上下振动，不随波迁移"},
        "param": {"name": "t", "label": "时间 $t$", "min": 0, "max": 4,
                  "step": 0.05, "value": 0.5, "unit": "s", "standard": 0.5,
                  "ticks": ["0", "0.5", "1", "2 (=T)", "4"]},
        "readouts": [
            ro("yp", "质点 P 的位移", EXPR_WY, 4, "m"),
            ro("vp", "质点 P 的振动速度", EXPR_WV, 4, "m/s"),
            ro("v", "波速 $v = \\lambda/T$（定值）", f"{W_LAM}/{W_T}", 2, "m/s"),
            ro("lam", "波长 $\\lambda$（定值）", f"{W_LAM}", 1, "m"),
            ro_status("up", "质点 P 是否向上运动", EXPR_WV, 0, ">",
                      "P 此刻向上运动", "P 此刻向下运动"),
        ],
        "constant": {"of": "v", "label": "$v = \\lambda/T = 2$ m/s 是定值 —— 波形整体平移，速度不变"},
    }
    lesson = {
        "language": "zh-CN", "title": "横波的传播与质点振动方向",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>一列横波沿 $+x$ 方向传播，波形为 "
            "$y = A\\sin\\left[2\\pi\\left(\\dfrac{t}{T} - \\dfrac{x}{\\lambda}\\right)\\right]$，"
            "其中 $A = 1\\ \\mathrm{m}$、$\\lambda = 4\\ \\mathrm{m}$、$T = 2\\ \\mathrm{s}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求波速 $v$；</li>"
            "<li>拖动滑块，说明「波形平移」与「质点振动」的区别；</li>"
            "<li>$x = 5\\ \\mathrm{m}$ 处的质点 $P$ 此刻往哪个方向运动？</li></ol>"),
        "answerLabel": "$t = 0.5$ s 时的质点 P",
        "answer": f"$v = \\lambda/T = {K.f(K.wave_speed(W_LAM, W_T), 1)}$ m/s；"
                  f"$y_P = {K.f(K.wave_y(W_A, W_T, W_LAM, W_XP, 0.5), 4)}$ m，"
                  f"$v_P = {K.f(K.particle_velocity(W_A, W_T, W_LAM, W_XP, 0.5), 4)}$ m/s",
    }
    steps = [
        {"title": "波形函数在说什么",
         "content": ("<p>$y(x, t)$ 是**两个**变量的函数：</p>"
                     "<p>· 固定 $t$，$y$ 随 $x$ 的图象就是某一时刻的**波形图**（本页画的就是它）；</p>"
                     "<p>· 固定 $x$，$y$ 随 $t$ 变化就是该质点的**振动图象**。</p>"
                     "<p>注意 $\\dfrac{t}{T} - \\dfrac{x}{\\lambda}$ 里 $x$ 前面的负号 —— "
                     "它表示波沿 $+x$ 方向传播。若把减号改成加号，波就沿 $-x$ 走。</p>")},
        {"title": "波形平移 vs 质点振动",
         "content": ("<p>拖滑块可以看到：整条蓝色曲线**整体向右平移**，"
                     "每次移过一个波长 $\\lambda$，波形就与原来完全重合 —— "
                     "所以 $v = \\lambda/T$，也就是 $v = \\lambda f$。</p>"
                     "<p>但粉色的质点 $P$ **只在竖直方向上下动**，"
                     "横坐标始终是 $5\\ \\mathrm{m}$。波传出去的是**振动形式与能量**，"
                     "不是介质本身。</p>")},
        {"title": "怎么判断质点此刻的振动方向",
         "content": ("<p>两个可靠办法：</p>"
                     "<p>· **求导**：$v_P = \\dfrac{\\partial y}{\\partial t}$，"
                     "本页读数区就是这么算的（正号向上）；</p>"
                     "<p>· **平移法**：把波形朝着传播方向微微挪一点，"
                     "看 $P$ 原来的位置在新波形上对应哪个点，就知道它往哪走。</p>"
                     "<p>口算时很多人凭「波向右传，所以右边的点向下」这类口诀，"
                     "在波峰波谷附近极易弄反 —— 用求导最保险。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 驻波
# =====================================================================
ST_A, ST_LAM, ST_T = 1.0, 4.0, 2.0
ST_X = 1.0                                       # 一个波腹的位置
EXPR_STY = f"2*{ST_A}*sin((2*PI/{ST_LAM})*{ST_X})*cos((2*PI/{ST_T})*t)"


def build_standing() -> dict:
    for t in (0.0, 0.25, 0.5, 1.0, 1.5):
        _agree(f"波腹处位移(t={t})", EXPR_STY, K.standing_y(ST_A, ST_LAM, ST_X, t, ST_T), tol=1e-12, t=t)
    _agree("波节间距 = λ/2", f"{ST_LAM}/2", K.node_spacing(ST_LAM), tol=1e-12)
    _agree("波节处恒为 0", f"2*{ST_A}*sin((2*PI/{ST_LAM})*4)*cos((2*PI/{ST_T})*t)",
           K.standing_y(ST_A, ST_LAM, 4.0, 0.7, ST_T), tol=1e-12, t=0.7)
    n_nodes = len(K.nodes(ST_LAM, 0.0, 12.0))
    assert n_nodes == 7, f"波节数应为 7，实得 {n_nodes}"
    assert len(K.antinodes(ST_LAM, 0.0, 12.0)) == 6

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "standing", "t": "t",
                  "caption": "灰线是包络 ±2A|sin kx|；红点波节始终不动，绿虚线处是波腹"},
        "param": {"name": "t", "label": "时间 $t$", "min": 0, "max": 4,
                  "step": 0.05, "value": 0.5, "unit": "s", "standard": 0.5,
                  "ticks": ["0 (最大)", "0.5 (=T/4)", "1", "2 (=T)", "4"]},
        "readouts": [
            ro("styx", "波腹处位移（x = 1 m）", EXPR_STY, 4, "m"),
            ro("gap", "相邻波节间距 $\\lambda/2$（定值）", f"{ST_LAM}/2", 2, "m"),
            ro("nn", "0–12 m 内的波节个数", f"{n_nodes}", 0),
            ro("amp", "波腹最大振幅 $2A$（定值）", f"2*{ST_A}", 2, "m"),
            ro_status("flat", "是否整条弦都在平衡位置（$t = T/4$）",
                      f"abs(cos((2*PI/{ST_T})*t))", 0.02, "<",
                      "此刻所有质点都在平衡位置", "此刻波形有起伏"),
        ],
        "constant": {"of": "gap", "label": "相邻波节的间距恒为 $\\lambda/2 = 2$ m —— 与振幅、时间都无关"},
    }
    lesson = {
        "language": "zh-CN", "title": "驻波：波节与波腹",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>两列振幅相同、传播方向相反的正弦波叠加，形成驻波 "
            "$y = 2A\\sin(kx)\\cos(\\omega t)$，"
            "其中 $A = 1\\ \\mathrm{m}$、$\\lambda = 4\\ \\mathrm{m}$、$T = 2\\ \\mathrm{s}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>波节在哪些位置？相邻波节相距多远？</li>"
            "<li>拖动滑块，为什么红点始终不动？</li>"
            "<li>驻波与行波最本质的区别是什么？</li></ol>"),
        "answerLabel": "$t = 0$ 时波腹处的位移",
        "answer": f"波节在 $x = 0, 2, 4, \\dots$ m，间距 $\\lambda/2 = {K.f(K.node_spacing(ST_LAM), 1)}$ m；"
                  f"波腹最大位移 $2A = 2$ m",
    }
    steps = [
        {"title": "为什么会有不动的地方",
         "content": ("<p>$y = 2A\\sin(kx)\\cos(\\omega t)$ 里，$x$ 与 $t$ 是**分离**的："
                     "空间部分与时间部分各管一摊。</p>"
                     "<p>凡是 $\\sin(kx) = 0$ 的地方（$x = n\\lambda/2$），"
                     "无论 $t$ 取什么值 $y$ 都是 $0$ —— 这就是**波节**。</p>"
                     "<p>凡是 $|\\sin(kx)| = 1$ 的地方（$x = (2n+1)\\lambda/4$），"
                     "振幅达到最大 $2A$ —— 这就是**波腹**。</p>")},
        {"title": "相邻波节为什么恰好差 λ/2",
         "content": ("<p>$\\sin(kx)$ 的零点间隔是 $\\dfrac{\\pi}{k} = \\dfrac{\\pi}{2\\pi/\\lambda} "
                     "= \\dfrac{\\lambda}{2}$。</p>"
                     "<p>所以波节间距只由**波长**决定，与振幅 $A$、与时间都无关 —— "
                     "读数区里那一行永远不动。波腹的间距也是 $\\lambda/2$，"
                     "只是整体挪了 $\\lambda/4$。</p>"
                     "<p>$t = T/4$ 时 $\\cos(\\omega t) = 0$，整条弦同时回到平衡位置 —— "
                     "这是驻波特有的「同相」现象，状态灯会亮。</p>")},
        {"title": "与行波的区别",
         "content": ("<p>行波的波形**整体平移**，每个质点的振幅都一样，相位依次落后；"
                     "能量随波向外传播。</p>"
                     "<p>驻波的波形**原地起伏**，各点振幅不同（波节为 0、波腹为 2A），"
                     "相邻两段的振动**反相**；能量在波节之间来回转换，**不向外传播**。</p>"
                     "<p>弦乐器、管乐器发声靠的就是驻波；"
                     "它也是「共振条件」的几何表述：弦两端必为波节 ⇒ $L = n\\dfrac{\\lambda}{2}$。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 波的叠加与拍
# =====================================================================
BEAT_F1 = 440.0
EXPR_BFB = f"abs({BEAT_F1:.0f}-f2)"


def build_beat() -> dict:
    for f2 in (440.0, 444.0, 448.0, 452.0, 460.0):
        _agree(f"拍频(f2={f2})", EXPR_BFB, K.beat_freq(BEAT_F1, f2), tol=1e-12, f2=f2)
        if f2 != BEAT_F1:
            _agree(f"拍周期(f2={f2})", f"1/({EXPR_BFB})", K.beat_period(BEAT_F1, f2), tol=1e-12, f2=f2)
    _agree("等频时拍频为 0", EXPR_BFB, 0.0, tol=1e-12, f2=BEAT_F1)
    _agree("t=0 时两波同相", f"sin(0)+sin(0)", K.beat_sum(1.0, BEAT_F1, 448.0, 0.0), tol=1e-12)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "beat", "f2": "f2",
                  "caption": "灰、紫是两列分波；绿虚线是合成波的外包络"},
        "param": {"name": "f2", "label": "第二列波的频率 $f_2$", "min": 440, "max": 460,
                  "step": 0.5, "value": 448.0, "unit": "Hz", "standard": 448.0,
                  "ticks": ["440 (f₁，无拍)", "448 (题设)", "460"]},
        "readouts": [
            ro("f1", "$f_1$（定值）", f"{BEAT_F1:.0f}", 0, "Hz"),
            ro("f2", "$f_2$", "f2", 1, "Hz"),
            ro("fb", "拍频 $|f_1 - f_2|$", EXPR_BFB, 1, "Hz"),
            ro("tb", "拍周期 $1/|f_1 - f_2|$", f"1/({EXPR_BFB})", 4, "s"),
            ro_status("has", "是否有拍（两频率不同）", EXPR_BFB, 0.25, ">",
                      "有拍：包络周期性涨落", "两频率相同：合成仍是简谐波"),
        ],
        "constant": {"of": "f1", "label": "$f_1 = 440$ Hz 是定值 —— 只让 $f_2$ 变，看包络的疏密"},
    }
    lesson = {
        "language": "zh-CN", "title": "波的叠加与拍",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>两列振幅相同（$A = 1$）、频率分别为 $f_1 = 440\\ \\mathrm{Hz}$ 与 $f_2$ "
            "的声波在同一处叠加。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出合振动，说明外包络的形状；</li>"
            "<li>求拍频与拍周期；</li>"
            "<li>为什么 $f_2 = f_1$ 时「拍」消失了？</li></ol>"),
        "answerLabel": "$f_2 = 448$ Hz 时",
        "answer": f"拍频 $= |f_1 - f_2| = {K.f(K.beat_freq(BEAT_F1, 448.0), 1)}$ Hz，"
                  f"拍周期 $= {K.f(K.beat_period(BEAT_F1, 448.0), 4)}$ s",
    }
    steps = [
        {"title": "和差化积",
         "content": ("<p>两列同振幅波相加，用和差化积公式：</p>"
                     "<p>$\\sin\\omega_1 t + \\sin\\omega_2 t = "
                     "2\\cos\\dfrac{\\omega_1-\\omega_2}{2}t \\cdot "
                     "\\sin\\dfrac{\\omega_1+\\omega_2}{2}t$。</p>"
                     "<p>右边的正弦部分频率很高（是两者平均），"
                     "余弦部分频率很低 —— 它就是**包络**。</p>"
                     "<p>于是听感上是一个「嗡——嗡——」的音量起伏，"
                     "起伏频率 $= \\dfrac{|\\omega_1-\\omega_2|}{2\\pi} = |f_1 - f_2|$。</p>")},
        {"title": "包络的表达式",
         "content": ("<p>外形的**最大振幅**是 $2A\\left|\\cos\\pi(f_1-f_2)t\\right|$，"
                     "它在 $0$ 与 $2A$ 之间来回变。</p>"
                     "<p>· 包络最大（两波同相 ⇒ 加强）时振幅 $2A$；</p>"
                     "<p>· 包络为零（两波反相 ⇒ 抵消）时振幅 $0$，此刻完全听不到声音。</p>"
                     "<p>相邻两次「最大」相隔一个拍周期 $1/|f_1-f_2|$。</p>")},
        {"title": "调音师为什么用「拍」",
         "content": ("<p>$f_2$ 越接近 $f_1$，拍周期越长、拍越**稀疏**；"
                     "$f_2 = f_1$ 时拍周期变成无穷，拍彻底消失 —— 状态灯会变。</p>"
                     "<p>给钢琴调音时，让标准音叉与琴弦同时发声，"
                     "听到拍就慢慢拧，直到拍消失为止。这是「人耳当仪器」的经典做法："
                     "拍频越低，说明两个频率越接近，而且**永远知道该往哪个方向拧**。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 双缝干涉
# =====================================================================
DS_L, DS_D = 1.0, 0.5e-3                          # 屏距 1 m，双缝间距 0.5 mm
EXPR_DSDY = f"{DS_L}*(lam*1e-9)/{DS_D}*1e3"       # 条纹间距（mm）


def build_interference() -> dict:
    for lam in (400.0, 500.0, 600.0, 700.0):
        _agree(f"条纹间距(λ={lam})", EXPR_DSDY,
               K.fringe_spacing(lam * 1e-9, DS_L, DS_D) * 1e3, tol=1e-12, lam=lam)
        _agree(f"第 3 级明纹(λ={lam})", f"3*({EXPR_DSDY})",
               K.fringe_position(3, lam * 1e-9, DS_L, DS_D) * 1e3, tol=1e-12, lam=lam)
    _agree("λ 越大条纹越宽", f"{DS_L}*(700*1e-9)/{DS_D}", 
           K.fringe_spacing(700e-9, DS_L, DS_D), tol=1e-12)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "doubleslit", "lam": "lam",
                  "caption": "屏上的干涉条纹：底部彩条就是实际看到的明暗分布"},
        "param": {"name": "lam", "label": "光的波长 $\\lambda$", "min": 400, "max": 700,
                  "step": 5, "value": 600.0, "unit": "nm", "standard": 600.0,
                  "ticks": ["400 (紫)", "600 (题设)", "700 (红)"]},
        "readouts": [
            ro("dy", "条纹间距 $\\Delta y = L\\lambda/d$", EXPR_DSDY, 4, "mm"),
            ro("y1", "第 1 级明纹位置", EXPR_DSDY, 4, "mm"),
            ro("y3", "第 3 级明纹位置", f"3*({EXPR_DSDY})", 4, "mm"),
            ro("ll", "屏距 $L$（定值）", f"{DS_L}", 1, "m"),
            ro_status("wide", "条纹间距是否大于 1 mm", EXPR_DSDY, 1, ">",
                      "条纹较宽：λ/d 的比值大", "条纹较窄"),
        ],
        "constant": {"of": "ll", "label": "$L = 1$ m、$d = 0.5$ mm 都是定值 —— 只让波长变"},
    }
    lesson = {
        "language": "zh-CN", "title": "双缝干涉与条纹间距",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>用波长 $\\lambda$ 的单色光做双缝干涉实验，双缝间距 "
            "$d = 0.5\\ \\mathrm{mm}$，双缝到屏的距离 $L = 1\\ \\mathrm{m}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>导出条纹间距 $\\Delta y = \\dfrac{L\\lambda}{d}$；</li>"
            "<li>拖动滑块，$\\lambda$ 从 400 nm 变到 700 nm，条纹怎么变？</li>"
            "<li>为什么用白光做实验时中央是白的、两侧是彩色？</li></ol>"),
        "answerLabel": "$\\lambda = 600$ nm 时的条纹",
        "answer": f"$\\Delta y = \\dfrac{{L\\lambda}}{{d}} = "
                  f"{K.f(K.fringe_spacing(600e-9, DS_L, DS_D) * 1e3, 4)}$ mm",
    }
    steps = [
        {"title": "光程差决定亮暗",
         "content": ("<p>从两缝发出的光到达屏上同一点，走过**路程差** $\\Delta r$。</p>"
                     "<p>· $\\Delta r = k\\lambda$（$k = 0, \\pm1, \\pm2,\\dots$）⇒ 两光波同相叠加 ⇒ **亮**；</p>"
                     "<p>· $\\Delta r = (k + \\dfrac12)\\lambda$ ⇒ 反相抵消 ⇒ **暗**。</p>"
                     "<p>这就是「干涉」二字的核心：同一点处的亮暗完全由光程差决定。</p>")},
        {"title": "为什么间距是 Lλ/d",
         "content": ("<p>设屏上离中心 $y$ 处，由几何得 $\\Delta r \\approx "
                     "\\dfrac{dy}{L}$（小角度近似）。</p>"
                     "<p>令它等于 $\\lambda$，就得到**相邻**明纹的间距：</p>"
                     "<p>$\\Delta y = \\dfrac{L\\lambda}{d}$。</p>"
                     "<p>这个式子说明：$\\lambda$ 越大或 $d$ 越小，条纹越**宽**（越容易分辨）—— "
                     "拖滑块可以看到整个花样被均匀撑开。反过来，"
                     "还能**用条纹间距测波长**：$\\lambda = \\dfrac{d\\,\\Delta y}{L}$。</p>")},
        {"title": "白光为什么是彩色的",
         "content": ("<p>$\\Delta y$ 与 $\\lambda$ 成正比，所以不同颜色的光条纹间距不同。</p>"
                     "<p>中央 $k = 0$ 处所有波长都满足 $\\Delta r = 0$，"
                     "各色光**同时**加强 —— 所以中央条纹是**白色**的。</p>"
                     "<p>离开中心后各级明纹位置按波长排开：红条纹比紫条纹更靠外，"
                     "于是中央白纹两侧出现由紫到红展开的彩色条纹。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 折射与全反射
# =====================================================================
RF_N1, RF_N2 = 1.5, 1.0
RF_C = math.degrees(math.asin(RF_N2 / RF_N1))
EXPR_RF_R = f"asin({RF_N1}*sin(i*PI/180)/{RF_N2})*180/PI"
EXPR_RF_C = f"asin({RF_N2}/{RF_N1})*180/PI"


def build_refraction() -> dict:
    for i in (0.0, 10.0, 20.0, 30.0, 41.0):
        _agree(f"折射角(i={i})", EXPR_RF_R, K.snell_angle(RF_N1, RF_N2, i), tol=1e-9, i=i)
    _agree("临界角", EXPR_RF_C, K.critical_angle(RF_N1, RF_N2), tol=1e-12)
    # 全反射时 asin 的参数超过 1 ⇒ 页面上读数为「—」
    assert K.snell_angle(RF_N1, RF_N2, 50.0) is None
    assert K.is_total_internal(RF_N1, RF_N2, 50.0) and not K.is_total_internal(RF_N1, RF_N2, 30.0)
    assert _jseval(f"{RF_N1}*sin(50*PI/180)/{RF_N2}") > 1.0

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "refraction", "i": "i",
                  "caption": "光从玻璃射向空气；紫虚线是临界角方向，红箭头是反射光"},
        "param": {"name": "i", "label": "入射角 $i$", "min": 0, "max": 80,
                  "step": 1, "value": 30.0, "unit": "°", "standard": 30.0,
                  "ticks": ["0", "30 (题设)", "41.81 (=C)", "80"]},
        "readouts": [
            ro("i", "入射角 $i$", "i", 0, "°"),
            ro("r", "折射角 $r$", EXPR_RF_R, 2, "°"),
            ro("c", "临界角 $C = \\arcsin(n_2/n_1)$（定值）", EXPR_RF_C, 2, "°"),
            ro("sini", "$n_1\\sin i$（与 $\\sin r$ 相等）",
               f"{RF_N1}*sin(i*PI/180)", 4),
            ro_status("tir", "是否发生全反射（$i > C$）", "i", RF_C, ">",
                      "全反射：没有折射光，光全被反射回去", "有折射光射出"),
        ],
        "constant": {"of": "c", "label": "$C = \\arcsin(n_2/n_1) = 41.81°$ 由两种介质决定，与入射角无关"},
    }
    lesson = {
        "language": "zh-CN", "title": "折射定律与全反射",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>一束光从玻璃（$n_1 = 1.5$）射向玻璃与空气（$n_2 = 1.0$）的界面，"
            "入射角为 $i$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出折射角 $r$ 与 $i$ 的关系；</li>"
            "<li>求临界角 $C$，并说明 $i > C$ 时会发生什么；</li>"
            "<li>为什么光纤能把光「困」在里面传输几千公里？</li></ol>"),
        "answerLabel": "$i = 30°$ 时",
        "answer": f"$r = \\arcsin\\dfrac{{n_1\\sin i}}{{n_2}} = "
                  f"{K.f(K.snell_angle(RF_N1, RF_N2, 30.0), 2)}°$；"
                  f"临界角 $C = {K.f(RF_C, 2)}°$",
    }
    steps = [
        {"title": "折射定律（斯涅尔定律）",
         "content": ("<p>$n_1\\sin i = n_2\\sin r$。</p>"
                     "<p>它的物理含义是：**光的频率不变，波长改变** —— "
                     "光进入光密介质（$n$ 大）后速度变小、波长变短，"
                     "为保持波前连续，传播方向就向法线靠拢。</p>"
                     "<p>$n = \\dfrac{c}{v}$ 正是这个速度比。读数区里 $n_1\\sin i$ "
                     "与 $n_2\\sin r$ 始终相等，就是这条定律的直接体现。</p>")},
        {"title": "临界角是怎么来的",
         "content": ("<p>从**光密**射向**光疏**时（$n_1 > n_2$），"
                     "由 $\\sin r = \\dfrac{n_1}{n_2}\\sin i$ 可见 $r > i$ —— "
                     "折射光偏离法线。</p>"
                     "<p>$i$ 增大到让 $\\sin r = 1$ 时 $r = 90^\\circ$，"
                     "折射光贴着界面跑；此时的入射角就是**临界角**：</p>"
                     "<p>$\\sin C = \\dfrac{n_2}{n_1} = \\dfrac{1}{1.5}$ ⇒ "
                     "$C = 41.81^\\circ$。</p>")},
        {"title": "i > C 之后没有折射光",
         "content": ("<p>再把 $i$ 调大，$\\dfrac{n_1}{n_2}\\sin i > 1$ —— "
                     "方程为 $\\sin r > 1$，**没有解**。</p>"
                     "<p>物理上就是：光无法射出界面，"
                     "能量全部被反射回光密介质，这就是**全反射**。"
                     "本页把滑块拖过 41.81° 后，绿色折射光消失、红色反射光变亮，"
                     "状态灯翻转。</p>"
                     "<p>光纤就是靠它工作的：让光在纤芯里以大于临界角的角度反复全反射，"
                     "几乎无损耗地传很远。注意全反射**只可能从光密到光疏**发生 —— "
                     "从空气射向玻璃永远不会全反射。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 凸透镜成像
# =====================================================================
LENS_F = 10.0
EXPR_LV = f"u*{LENS_F}/(u-{LENS_F})"
EXPR_LM = f"-{LENS_F}/(u-{LENS_F})"


def build_thinlens() -> dict:
    for u in (5.0, 8.0, 15.0, 20.0, 30.0, 40.0):
        _agree(f"像距(u={u})", EXPR_LV, K.lens_image(LENS_F, u), tol=1e-12, u=u)
        _agree(f"放大率(u={u})", EXPR_LM, K.lens_magnification(LENS_F, u), tol=1e-12, u=u)
        # 成像公式自洽
        v = K.lens_image(LENS_F, u)
        assert abs(1 / u + 1 / v - 1 / LENS_F) < 1e-12
    assert K.lens_image(LENS_F, LENS_F) is None
    assert K.lens_is_virtual(LENS_F, 5.0) and not K.lens_is_virtual(LENS_F, 30.0)
    assert K.lens_is_inverted(LENS_F, 30.0) and not K.lens_is_inverted(LENS_F, 5.0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "lens", "u": "u",
                  "caption": "三条特征光线：平行主轴→过 F′、过光心不偏折、过 F→平行射出"},
        "param": {"name": "u", "label": "物距 $u$", "min": 4, "max": 40,
                  "step": 0.5, "value": 30.0, "unit": "cm", "standard": 30.0,
                  "ticks": ["4", "10 (=f)", "20 (=2f)", "30 (题设)", "40"]},
        "readouts": [
            ro("u", "物距 $u$", "u", 1, "cm"),
            ro("v", "像距 $v = \\dfrac{uf}{u-f}$", EXPR_LV, 2, "cm"),
            ro("m", "放大率 $m = -v/u$", EXPR_LM, 4),
            ro("fl", "焦距 $f$（定值）", f"{LENS_F:.0f}", 0, "cm"),
            ro_status("real", "是否成实像（$u > f$）", f"u-{LENS_F:.0f}", 0, ">",
                      "实像：折射光真实相交，可用光屏接收", "虚像：需要反向延长线相交"),
        ],
        "constant": {"of": "fl", "label": "$f = 10$ cm 是定值 —— 只让物距变，看像怎么跑"},
    }
    lesson = {
        "language": "zh-CN", "title": "凸透镜成像规律",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>凸透镜焦距 $f = 10\\ \\mathrm{cm}$，物距 $u$ 可变。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出像距公式，并求 $u = 30\\ \\mathrm{cm}$ 时的像距与放大率；</li>"
            "<li>拖动滑块，什么时候成实像、什么时候成虚像？</li>"
            "<li>$u = f$ 时为什么不成像？</li></ol>"),
        "answerLabel": "$u = 30$ cm 时",
        "answer": f"$v = \\dfrac{{uf}}{{u-f}} = {K.f(K.lens_image(LENS_F, 30.0), 2)}$ cm，"
                  f"$m = -\\dfrac{{v}}{{u}} = {K.f(K.lens_magnification(LENS_F, 30.0), 3)}$（倒立、缩小）",
    }
    steps = [
        {"title": "成像公式的两种写法",
         "content": ("<p>中国教材常用 $\\dfrac{1}{u} + \\dfrac{1}{v} = \\dfrac{1}{f}$，"
                     "其中 $u$、$v$ 都取正值表示在透镜两侧。</p>"
                     "<p>解得 $v = \\dfrac{uf}{u-f}$，放大率 "
                     "$m = -\\dfrac{v}{u} = -\\dfrac{f}{u-f}$。</p>"
                     "<p>$m$ 的**负号表示倒立**，$|m|$ 是放大倍数。"
                     "$u = 30\\ \\mathrm{cm}$ 时 $v = 15\\ \\mathrm{cm}$、$m = -0.5$ —— "
                     "倒立、缩小一半的实像。</p>")},
        {"title": "三条特征光线",
         "content": ("<p>任取两条即可定出像点，本页画了三条：</p>"
                     "<p>· **平行主轴**入射 → 折射后过焦点 $F'$（绿）；</p>"
                     "<p>· **过光心** → 方向不变（黄）；</p>"
                     "<p>· **过焦点 $F$** 入射 → 折射后平行主轴（紫）。</p>"
                     "<p>三条线交于一点，那就是像点。注意画图时横向与纵向比例不一定要相同 —— "
                     "只要都是线性缩放，直线仍是直线，交点仍是交点，结论不受影响。</p>")},
        {"title": "u 从大到小会看到什么",
         "content": ("<p>把滑块从 40 拖到 4，依次看到：</p>"
                     "<p>· $u > 2f$：$v$ 在 $f$ 与 $2f$ 之间，**倒立缩小实像**；</p>"
                     "<p>· $u = 2f = 20\\ \\mathrm{cm}$：$v = 2f$，**倒立等大实像**；</p>"
                     "<p>· $f < u < 2f$：$v > 2f$，**倒立放大实像**（投影仪）；</p>"
                     "<p>· $u = f = 10\\ \\mathrm{cm}$：折射光平行射出，**不成像**（像在无穷远）；</p>"
                     "<p>· $u < f$：$v < 0$，**正立放大虚像**（放大镜）。</p>"
                     "<p>口诀「一倍焦距分虚实、二倍焦距分大小」说的就是这五段。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "shm": build_shm,
    "wavemotion": build_wave,
    "standing": build_standing,
    "beat": build_beat,
    "interference": build_interference,
    "refraction": build_refraction,
    "thinlens": build_thinlens,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="机械振动 · 机械波 · 光 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
