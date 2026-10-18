#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「热化学」交互网页。

全部数值由 lib/thermochem_kernel.py 现算（盖斯定律是**真做线性组合**，
可以反向、可以乘系数，不是套一个结论）。

覆盖七个题型（选择性必修一 · 化学反应原理）：
  sign           反应热的符号与能量图
  hess           盖斯定律（路径无关，分步与一步相等）
  formation      由标准生成焓计算 ΔH
  bond           由键能估算 ΔH
  combustion     燃烧热与热量计算
  neutralization 中和热与量热法
  catalyst       活化能与催化剂（ΔH 不变）

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

import thermochem_kernel as K                  # noqa: E402
from skillkit import cli                       # noqa: E402

_MATHENV = {
    "sqrt": math.sqrt, "abs": abs, "min": min, "max": max, "pow": pow,
    "sign": lambda v: (v > 0) - (v < 0), "floor": math.floor, "ceil": math.ceil,
    "PI": math.pi, "E": math.e,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "exp": math.exp, "log": math.log,
}


def _jseval(expr, **env):
    return eval(expr.replace("^", "**"), {"__builtins__": {}}, {**_MATHENV, **env})


def _agree(label, expr, want, tol=1e-9, **env):
    got = _jseval(expr, **env)
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
# 1) 反应热的符号与能量图
# =====================================================================
SG_EA0 = 150.0            # 正反应活化能的基准值（kJ/mol）
EXPR_SG_EA = f"max({SG_EA0:.0f}, dh+40)"
EXPR_SG_EAR = f"({EXPR_SG_EA})-dh"


def build_sign() -> dict:
    for dh in (-200.0, -100.0, -40.0, 0.0, 60.0, 200.0):
        _agree(f"Ea(正)(ΔH={dh})", EXPR_SG_EA, SG_EA0 if dh <= 110 else dh + 40,
               tol=1e-12, dh=dh)
        ea_f = SG_EA0 if dh <= 110 else dh + 40
        _agree(f"Ea(逆)(ΔH={dh})", EXPR_SG_EAR, ea_f - dh, tol=1e-12, dh=dh)
        # 恒有关系：ΔH = Ea(正) − Ea(逆)
        _agree(f"ΔH = Ea正 − Ea逆(ΔH={dh})", f"({EXPR_SG_EA})-({EXPR_SG_EAR})", dh,
               tol=1e-12, dh=dh)
    _agree("放热时 Ea(逆) 更大", EXPR_SG_EAR, SG_EA0 + 100.0, tol=1e-12, dh=-100.0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "energycurve", "dh": "dh",
                  "caption": "能量-反应进程曲线：山的左边是 Ea(正)，右边是 Ea(逆)"},
        "param": {"name": "dh", "label": "反应热 $\\Delta H$", "min": -200, "max": 200,
                  "step": 10, "value": -100.0, "unit": "kJ/mol", "standard": -100.0,
                  "ticks": ["-200 (强放热)", "-100 (题设)", "0", "200 (强吸热)"]},
        "readouts": [
            ro("dh", "反应热 $\\Delta H$", "dh", 0, "kJ/mol"),
            ro("eaf", "正反应活化能 $E_{a(正)}$", EXPR_SG_EA, 0, "kJ/mol"),
            ro("ear", "逆反应活化能 $E_{a(逆)}$", EXPR_SG_EAR, 0, "kJ/mol"),
            ro("chk", "校验：$E_{a(正)} - E_{a(逆)}$", f"({EXPR_SG_EA})-({EXPR_SG_EAR})", 1, "kJ/mol"),
            ro_status("exo", "是否为放热反应（$\\Delta H < 0$）", "dh", 0, "<",
                      "放热：生成物总能量更低", "吸热（或热量不变）"),
        ],
        "constant": {"of": "ea0", "label": "$E_{a(正)}$ 有下限 150 —— 山必须高过两端"},
        "scalars": [{"name": "ea0", "expr": "150"}],
    }
    lesson = {
        "language": "zh-CN", "title": "反应热 ΔH 与能量图",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>某反应的反应热 $\\Delta H$ 可调，正反应活化能为 "
            "$150\\ \\mathrm{kJ/mol}$（当 $\\Delta H$ 很大时山要更高）。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $E_{a(正)}$ 与 $E_{a(逆)}$、$\\Delta H$ 的关系；</li>"
            "<li>拖动滑块，什么时候 $E_{a(逆)} > E_{a(正)}$？</li>"
            "<li>为什么放热反应的逆反应活化能更大？</li></ol>"),
        "answerLabel": "$\\Delta H = -100$ kJ/mol 时",
        "answer": f"$E_{{a(正)}} = {K.f(SG_EA0, 0)}$、$E_{{a(逆)}} = {K.f(SG_EA0 + 100, 0)}$ kJ/mol；"
                  f"校验 $E_{{a(正)}} - E_{{a(逆)}} = {K.f(-100.0, 0)} = \\Delta H$",
    }
    steps = [
        {"title": "ΔH 的定义与符号",
         "content": ("<p>$\\Delta H = H(生成物) - H(反应物)$，也就是"
                     "**生成物总能量减去反应物总能量**。</p>"
                     "<p>· $\\Delta H < 0$：生成物能量更低，多余的能量以热的形式放出 ⇒ **放热**；</p>"
                     "<p>· $\\Delta H > 0$：生成物能量更高，需要从外界吸热 ⇒ **吸热**。</p>"
                     "<p>注意符号常常被写反：题目说「放出 890.3 kJ」时，"
                     "热化学方程式里要写 $\\Delta H = -890.3$。</p>")},
        {"title": "能量图上的三个高度",
         "content": ("<p>图上有三个关键高度：反应物能级、过渡态（山顶）、生成物能级。</p>"
                     "<p>· $E_{a(正)}$ = 山顶 − 反应物；</p>"
                     "<p>· $E_{a(逆)}$ = 山顶 − 生成物。</p>"
                     "<p>两者相减，山顶正好抵消，于是得到恒等关系</p>"
                     "<p>$\\Delta H = E_{a(正)} - E_{a(逆)}$。</p>"
                     "<p>读数区专门列了一行来校验它 —— 不管怎么拖滑块，"
                     "那一行永远等于 $\\Delta H$。这就是能量图的全部内容。</p>")},
        {"title": "放热与吸热的形状差别",
         "content": ("<p>放热反应（$\\Delta H < 0$）：生成物比反应物低，"
                     "所以**逆反应的活化能更大** —— 上山容易下山难。拖滑块到负值即可看到。</p>"
                     "<p>吸热反应则相反：生成物更高，逆反应反而更「容易」。</p>"
                     "<p>把滑块拖到 $\\Delta H = 0$，两端一样高，"
                     "正逆活化能相等 —— 状态灯会翻转。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 盖斯定律
# =====================================================================
HS_TOTAL = -145.0          # A → B 的总 ΔH（由画板上的两级高度定出）
EXPR_HS_D1 = f"{HS_TOTAL!r}*frac"
EXPR_HS_D2 = f"{HS_TOTAL!r}*(1-frac)"


def build_hess() -> dict:
    for frac in (0.1, 0.3, 0.5, 0.6, 0.9):
        d1 = HS_TOTAL * frac
        d2 = HS_TOTAL * (1 - frac)
        _agree(f"ΔH₁(frac={frac})", EXPR_HS_D1, d1, tol=1e-12, frac=frac)
        _agree(f"ΔH₂(frac={frac})", EXPR_HS_D2, d2, tol=1e-12, frac=frac)
        # 盖斯定律：分步之和 = 一步之和（内核做的线性组合）
        _agree(f"分步之和(frac={frac})", f"({EXPR_HS_D1})+({EXPR_HS_D2})",
               K.hess_combine([(1, d1), (1, d2)]), tol=1e-12, frac=frac)
        _agree(f"恒等于一步(frac={frac})", f"({EXPR_HS_D1})+({EXPR_HS_D2})",
               K.hess_path([HS_TOTAL]), tol=1e-12, frac=frac)
    _agree("内核路径和", f"{HS_TOTAL!r}", K.hess_path([HS_TOTAL]), tol=1e-12)
    # 反向书写要变号：把 C→B 反成 B→C（ΔH 取负），
    # 于是 A→C = (A→B) + (B→C) = ΔH_总 + (−ΔH₂) = ΔH₁
    for frac in (0.25, 0.75):
        d1 = HS_TOTAL * frac
        d2 = HS_TOTAL * (1 - frac)
        _agree(f"反向组合(frac={frac})", EXPR_HS_D1,
               K.hess_combine([(1, HS_TOTAL), (1, K.reverse_step(d2))]), tol=1e-12, frac=frac)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "hesspath", "frac": "frac",
                  "caption": "蓝实线 = 分两步 A→C→B；绿虚线 = 一步 A→B"},
        "param": {"name": "frac", "label": "中间体 $C$ 的相对高度", "min": 0.1, "max": 0.9,
                  "step": 0.05, "value": 0.6, "unit": "", "standard": 0.6,
                  "ticks": ["0.1 (C 很低)", "0.6 (题设)", "0.9 (C 很高)"]},
        "readouts": [
            ro("d1", "$\\Delta H_1$（A→C）", EXPR_HS_D1, 2, "kJ/mol"),
            ro("d2", "$\\Delta H_2$（C→B）", EXPR_HS_D2, 2, "kJ/mol"),
            ro("sum", "$\\Delta H_1 + \\Delta H_2$", f"({EXPR_HS_D1})+({EXPR_HS_D2})", 2, "kJ/mol"),
            ro("direct", "$\\Delta H$（A→B 一步，定值）", f"{HS_TOTAL!r}", 2, "kJ/mol"),
            ro_status("hi", "中间体 C 是否高于 A→B 的「半程」", "frac", 0.5, ">",
                      "C 偏高：后一步（C→B）放热更多", "C 偏低：前一步（A→C）放热更多"),
        ],
        "constant": {"of": "direct", "label": "一步的 $\\Delta H$ 恒为 −145 —— 与中间体 $C$ 的高低完全无关"},
    }
    lesson = {
        "language": "zh-CN", "title": "盖斯定律",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>反应 A → B 的 $\\Delta H = -145\\ \\mathrm{kJ/mol}$。"
            "若把它拆成 A → C → B 两步，中间体 $C$ 的高低可以变化。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出两步的 $\\Delta H_1$、$\\Delta H_2$ 与总 $\\Delta H$ 的关系；</li>"
            "<li>拖动滑块，$\\Delta H_1 + \\Delta H_2$ 变吗？</li>"
            "<li>为什么热化学方程式可以像代数式一样相加相减？</li></ol>"),
        "answerLabel": "$C$ 的相对高度为 0.6 时",
        "answer": f"$\\Delta H_1 = {K.f(HS_TOTAL * 0.6, 2)}$、"
                  f"$\\Delta H_2 = {K.f(HS_TOTAL * 0.4, 2)}$，"
                  f"和恒为 $\\({K.f(HS_TOTAL, 2)}\\)$ kJ/mol",
    }
    steps = [
        {"title": "焓是状态函数",
         "content": ("<p>焓 $H$ 只由系统**当前的状态**决定，"
                     "与「怎么到达这个状态」无关。</p>"
                     "<p>所以 A → B 有两种走法时，两种走法的 $\\Delta H$ 必然相等：</p>"
                     "<p>$\\Delta H(\\text{一步}) = \\Delta H_1 + \\Delta H_2$。</p>"
                     "<p>图上的蓝实线是两步，绿虚线是一步，"
                     "但「起点到终点的高度差」是同一个 —— "
                     "拖滑块只改变中间体 $C$ 的高度，改变不了总落差。</p>")},
        {"title": "于是可以做「代数运算」",
         "content": ("<p>既然 $\\Delta H$ 只与始末状态有关，"
                     "热化学方程式就可以像代数方程一样操作：</p>"
                     "<p>· **相加**：两个反应相加，$\\Delta H$ 相加；</p>"
                     "<p>· **相减**：把反应反向写，$\\Delta H$ 变号；</p>"
                     "<p>· **乘系数**：反应式乘以 $k$，$\\Delta H$ 也乘以 $k$。</p>"
                     "<p>操作时要保证中间产物（比如 $C$）能**恰好抵消**，"
                     "就像解方程组消元一样。这正是盖斯定律的用法。</p>")},
        {"title": "一个典型算例",
         "content": ("<p>已知：</p>"
                     "<p>(1) $\\mathrm{C + O_2 \\to CO_2}$，$\\Delta H_1 = -393.5$；</p>"
                     "<p>(2) $\\mathrm{CO + \\frac12 O_2 \\to CO_2}$，$\\Delta H_2 = -283.0$。</p>"
                     "<p>求 $\\mathrm{C + \\frac12 O_2 \\to CO}$ 的 $\\Delta H$。</p>"
                     "<p>把 (1) 减 (2)：(1) − (2) 得 $\\mathrm{C - CO \\to 0}$，"
                     "即目标反应；于是</p>"
                     "<p>$\\Delta H = \\Delta H_1 - \\Delta H_2 = -393.5 + 283.0 "
                     "= -110.5\\ \\mathrm{kJ/mol}$。</p>"
                     "<p>内核里就是用 `hess_combine([(1, -393.5), (-1, -283.0)])` "
                     "**真的做这个线性组合**，而不是记结论。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 由标准生成焓计算
# =====================================================================
FH_REACTIONS = [
    ("CH₄ + 2O₂ → CO₂ + 2H₂O", [(1, -74.8), (2, 0.0)], [(1, -393.5), (2, -285.8)]),
    ("C + O₂ → CO₂", [(1, 0.0), (1, 0.0)], [(1, -393.5)]),
    ("C + 2H₂ → CH₄", [(1, 0.0), (2, 0.0)], [(1, -74.8)]),
    ("CaCO₃ → CaO + CO₂", [(1, -1207.0)], [(1, -635.5), (1, -393.5)]),
    ("2H₂ + O₂ → 2H₂O", [(2, 0.0), (1, 0.0)], [(2, -285.8)]),
]
FH_SR = "[" + ",".join(repr(sum(c * v for c, v in r)) for _, r, _ in FH_REACTIONS) + "][ridx-1]"
FH_SP = "[" + ",".join(repr(sum(c * v for c, v in p)) for _, _, p in FH_REACTIONS) + "][ridx-1]"
FH_DH = f"({FH_SP})-({FH_SR})"


def build_formation() -> dict:
    for idx, (name, r, p) in enumerate(FH_REACTIONS, start=1):
        sr = sum(c * v for c, v in r)
        sp = sum(c * v for c, v in p)
        _agree(f"Σ反应物(#{idx})", FH_SR, sr, tol=1e-12, ridx=idx)
        _agree(f"Σ生成物(#{idx})", FH_SP, sp, tol=1e-12, ridx=idx)
        _agree(f"ΔH(#{idx})", FH_DH, K.delta_h_formation(p, r), tol=1e-12, ridx=idx)
    _agree("CaCO₃ 分解是吸热", FH_DH, 178.0, tol=1e-12, ridx=4)
    _agree("乙烷…… 甲烷燃烧是放热", FH_DH, -890.3, tol=1e-12, ridx=1)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "barh", "ridx": "ridx",
                  "caption": "三条按同一比例：ΔH = 生成物之和 − 反应物之和"},
        "param": {"name": "ridx", "label": "选择反应（1–5）", "min": 1, "max": 5,
                  "step": 1, "value": 1, "unit": "", "standard": 1,
                  "ticks": ["1 甲烷燃烧", "2 C+O₂", "3 合成甲烷", "4 CaCO₃分解", "5 氢燃烧"]},
        "readouts": [
            ro("sr", "$\\Sigma\\nu\\Delta H_f$(反应物)", FH_SR, 1, "kJ/mol"),
            ro("sp", "$\\Sigma\\nu\\Delta H_f$(生成物)", FH_SP, 1, "kJ/mol"),
            ro("dh", "$\\Delta H$", FH_DH, 1, "kJ/mol"),
            ro("zero", "单质的 $\\Delta H_f$（规定为 0）", "0", 0, "kJ/mol"),
            ro_status("exo", "是否为放热反应", FH_DH, 0, "<",
                      "ΔH < 0：放热反应", "ΔH > 0：吸热反应"),
        ],
        "constant": {"of": "zero", "label": "单质的标准生成焓**规定为 0** —— 这是整套计算的基准"},
    }
    lesson = {
        "language": "zh-CN", "title": "由标准生成焓计算反应热",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>已知各物质的标准生成焓 $\\Delta H_f$，求下列反应的 $\\Delta H$："
            "$\\mathrm{CH_4 + 2O_2 \\to CO_2 + 2H_2O}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $\\Delta H$ 的计算式；</li>"
            "<li>为什么氧气的 $\\Delta H_f$ 取 0？</li>"
            "<li>切换不同反应，看看哪些是吸热、哪些是放热。</li></ol>"),
        "answerLabel": "甲烷燃烧",
        "answer": f"$\\Delta H = (-393.5 - 2\\times285.8) - (-74.8) "
                  f"= {K.f(-890.3, 1)}$ kJ/mol",
    }
    steps = [
        {"title": "标准生成焓是什么",
         "content": ("<p>$\\Delta H_f$ 指「由**最稳定的单质**生成 $1\\ \\mathrm{mol}$ 该物质」"
                     "时的反应热，且规定温度为 $25\\ ^\\circ\\mathrm{C}$、压强为 $100\\ \\mathrm{kPa}$。</p>"
                     "<p>由这个定义，**单质的 $\\Delta H_f$ 必然为 0**（自己生成自己，"
                     "没有能量变化）。所以 $\\mathrm{O_2}$、$\\mathrm{H_2}$、$\\mathrm{C(石墨)}$ "
                     "等的 $\\Delta H_f$ 都记作 $0$ —— 本页专门列了一行提示。</p>")},
        {"title": "为什么要用「生成物减反应物」",
         "content": ("<p>把所有物质都看成「从单质合成来的」，"
                     "整个反应就成了一次**能量的加减法**：</p>"
                     "<p>先拆回单质（放掉反应物的生成焓），再合成产物（付出产物的生成焓），"
                     "两者之差就是净热效应：</p>"
                     "<p>$\\Delta H = \\sum \\nu\\,\\Delta H_f(\\text{生成物}) "
                     "- \\sum \\nu\\,\\Delta H_f(\\text{反应物})$。</p>"
                     "<p>注意**系数 $\\nu$ 要乘进去**：甲烷燃烧里有两个水，"
                     "所以是 $2 \\times (-285.8)$。这是最容易漏的一步。</p>")},
        {"title": "结果怎么读",
         "content": ("<p>切换五个反应可以看到两类结果：</p>"
                     "<p>· 甲烷燃烧 $-890.3$、$\\mathrm{C+O_2}$ 是 $-393.5$、"
                     "氢燃烧 $-571.6$ —— 都是**放热**，这类反应产物更稳定；</p>"
                     "<p>· $\\mathrm{CaCO_3}$ 分解是 $+178.0$ —— **吸热**，"
                     "所以工业上要高温煅烧才分解（或者说：正因为吸热，才需要持续加热）。</p>"
                     "<p>规律：由单质直接化合、或燃烧生成稳定氧化物，通常放热；"
                     "把稳定的化合物拆开，通常吸热。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 由键能估算
# =====================================================================
BD_BROKEN = 436.0 + 243.0          # H−H + Cl−Cl
EXPR_BD_FORMED = "2*ehcl"
EXPR_BD_DH = f"{BD_BROKEN:.0f}-2*ehcl"


def build_bond() -> dict:
    for e in (320.0, 340.0, 380.0, 431.0, 480.0):
        _agree(f"成键总和(E={e})", EXPR_BD_FORMED, 2 * e, tol=1e-12, ehcl=e)
        _agree(f"ΔH(E={e})", EXPR_BD_DH, K.delta_h_bonds([(1, 436.0), (1, 243.0)], [(2, e)]),
               tol=1e-12, ehcl=e)
    _agree("ΔH = 断 − 成（实数对照）", EXPR_BD_DH, -183.0, tol=1e-12, ehcl=431.0)
    _agree("断键总和恒为 679", f"{BD_BROKEN:.0f}", 679.0, tol=1e-12)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "bondbar", "ehcl": "ehcl",
                  "caption": "红 = 断键吸能、蓝 = 成键放能；两者相减才是 ΔH"},
        "param": {"name": "ehcl", "label": "取 $E(\\mathrm{H{-}Cl})$", "min": 320, "max": 480,
                  "step": 5, "value": 431.0, "unit": "kJ/mol", "standard": 431.0,
                  "ticks": ["320", "340 (临界)", "431 (实测)", "480"]},
        "readouts": [
            ro("broken", "断键总能量（定值）", f"{BD_BROKEN:.0f}", 0, "kJ/mol"),
            ro("formed", "成键总能量", EXPR_BD_FORMED, 0, "kJ/mol"),
            ro("dh", "$\\Delta H = $ 断 $-$ 成", EXPR_BD_DH, 1, "kJ/mol"),
            ro("crit", "临界值：$\\Delta H = 0$ 时的 $E(\\mathrm{H{-}Cl})$", f"{BD_BROKEN / 2:.1f}", 1, "kJ/mol"),
            ro_status("exo", "是否放热（$E(\\mathrm{H{-}Cl})$ 足够大）", EXPR_BD_DH, 0, "<",
                      "放热：新键比旧键强", "吸热：新键不够强"),
        ],
        "constant": {"of": "broken", "label": "断键总能量恒为 679 kJ/mol（$436 + 243$）"},
    }
    lesson = {
        "language": "zh-CN", "title": "由键能估算反应热",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>已知 $E(\\mathrm{H{-}H}) = 436$、$E(\\mathrm{Cl{-}Cl}) = 243$ "
            "（单位 $\\mathrm{kJ/mol}$），$E(\\mathrm{H{-}Cl})$ 可调。"
            "估算 $\\mathrm{H_2 + Cl_2 \\to 2HCl}$ 的 $\\Delta H$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出计算式；</li>"
            "<li>$E(\\mathrm{H{-}Cl})$ 至少要多大才会放热？</li>"
            "<li>已知实测 $E(\\mathrm{H{-}Cl}) \\approx 431$，代入算出 $\\Delta H$。</li></ol>"),
        "answerLabel": "$E(\\mathrm{H{-}Cl}) = 431$ kJ/mol 时",
        "answer": f"$\\Delta H = (436+243) - 2\\times431 = {K.f(-183.0, 0)}$ kJ/mol"
                  f"（与实测 $-184.6$ 很接近）",
    }
    steps = [
        {"title": "为什么是「断减成」",
         "content": ("<p>把反应拆成两步想像：</p>"
                     "<p>第一步，把反应物里的化学键**全部打断**变成原子 —— "
                     "这一定**吸热**（键能就是打断它所需的能量）；</p>"
                     "<p>第二步，让原子重新组合成生成物的键 —— "
                     "这一定**放热**（放出的能量等于新键的键能）。</p>"
                     "<p>合起来：</p>"
                     "<p>$\\Delta H = \\sum E(\\text{断开的键}) "
                     "- \\sum E(\\text{形成的键})$。</p>"
                     "<p>本页断 $1$ 个 $\\mathrm{H{-}H}$ 和 $1$ 个 $\\mathrm{Cl{-}Cl}$、"
                     "成 $2$ 个 $\\mathrm{H{-}Cl}$，所以 $\\Delta H = 679 - 2E(\\mathrm{H{-}Cl})$。</p>")},
        {"title": "什么时候转成吸热",
         "content": ("<p>令 $679 - 2E = 0$ 得 $E = 339.5\\ \\mathrm{kJ/mol}$ —— "
                     "这就是**临界值**，读数区把它单列出来了。</p>"
                     "<p>$E < 339.5$：新键太弱，断裂旧键的能量收不回来 ⇒ **吸热**；</p>"
                     "<p>$E > 339.5$：新键更强 ⇒ **放热**。</p>"
                     "<p>把滑块拖过 $339.5$，状态灯会翻转。"
                     "这也解释了「为什么大多数化合反应放热」—— "
                     "因为新生成的键通常比原来的更强。</p>")},
        {"title": "键能法的适用范围",
         "content": ("<p>键能法给出的是**估算值**，因为它假设「同一个键在任何分子里"
                     "键能都一样」。实际上 $\\mathrm{H{-}Cl}$ 在不同环境里略有差别，"
                     "所以算出来的 $-183$ 与实测 $-184.6$ 有约 $1\\%$ 的偏差 —— "
                     "这在估算里已经相当好。</p>"
                     "<p>它的优势是**不需要查生成焓表**，只要知道断哪些键、成哪些键"
                     "就能估算。反之，如果查表数据齐全，优先用生成焓法（上一节），"
                     "那个是精确的。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 燃烧热与热量计算
# =====================================================================
CB_DH = -890.3
EXPR_CB_Q = f"{abs(CB_DH)!r}*nn"


def build_combustion() -> dict:
    for n in (0.5, 1.0, 2.0, 3.5, 5.0):
        _agree(f"Q(n={n})", EXPR_CB_Q, abs(K.heat_amount(CB_DH, n)), tol=1e-12, nn=n)
        _agree(f"Q = |ΔH|·n(n={n})", EXPR_CB_Q, abs(CB_DH) * n, tol=1e-12, nn=n)
    _agree("1 mol 的燃烧热", EXPR_CB_Q, 890.3, tol=1e-12, nn=1.0)
    assert abs(K.heat_amount(CB_DH, 1.0) - CB_DH) < 1e-12, "1 mol 放出的热量应等于 ΔH"

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "heatcalc", "nn": "nn",
                  "caption": "粉条随物质的量线性增长；蓝条是 1 mol 的燃烧热作参照"},
        "param": {"name": "nn", "label": "甲烷的物质的量 $n$", "min": 0.5, "max": 5,
                  "step": 0.1, "value": 2.0, "unit": "mol", "standard": 2.0,
                  "ticks": ["0.5", "2 (题设)", "5"]},
        "readouts": [
            ro("n", "$n(\\mathrm{CH_4})$", "nn", 2, "mol"),
            ro("q", "放出的热量 $Q$", EXPR_CB_Q, 2, "kJ"),
            ro("burn", "燃烧热（定值）", f"{abs(CB_DH)!r}", 1, "kJ/mol"),
            ro("dh", "$\\Delta H$（定值）", f"{CB_DH!r}", 1, "kJ/mol"),
            ro_status("big", "放热量是否超过 2000 kJ", EXPR_CB_Q, 2000, ">",
                      "超过 2000 kJ", "不到 2000 kJ"),
        ],
        "constant": {"of": "burn", "label": "燃烧热恒为 890.3 kJ/mol —— 它与烧多少**无关**"},
    }
    lesson = {
        "language": "zh-CN", "title": "燃烧热与热量计算",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>甲烷的燃烧热为 $890.3\\ \\mathrm{kJ/mol}$："
            "$\\mathrm{CH_4(g) + 2O_2(g) \\to CO_2(g) + 2H_2O(l)}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>燃烧 $n\\ \\mathrm{mol}$ 甲烷放出多少热量？</li>"
            "<li>燃烧热的数值是正的，而 $\\Delta H$ 是负的，为什么？</li>"
            "<li>如果生成的是水蒸气而不是液态水，放热会变多还是变少？</li></ol>"),
        "answerLabel": "$n = 2$ mol 时",
        "answer": f"$Q = 2 \\times 890.3 = {K.f(2 * 890.3, 1)}$ kJ",
    }
    steps = [
        {"title": "燃烧热的定义有三个关键词",
         "content": ("<p>**燃烧热**指 $1\\ \\mathrm{mol}$ 可燃物**完全燃烧**"
                     "生成**稳定氧化物**时放出的热量。</p>"
                     "<p>三个词都要抠：</p>"
                     "<p>· 「$1\\ \\mathrm{mol}$」—— 所以它是**摩尔量**，"
                     "烧 $2\\ \\mathrm{mol}$ 就要乘以 2；</p>"
                     "<p>· 「完全燃烧」—— 碳必须变成 $\\mathrm{CO_2}$ 而不是 $\\mathrm{CO}$；</p>"
                     "<p>· 「稳定氧化物」—— $\\mathrm{H}$ 必须变成**液态水**，"
                     "因为常温常压下液态水才是稳定的。</p>")},
        {"title": "符号那一关",
         "content": ("<p>题目说「燃烧热是 $890.3\\ \\mathrm{kJ/mol}$」—— 这是**正值**，"
                     "它在说「放出的热量」；</p>"
                     "<p>而热化学方程式里要写 $\\Delta H = -890.3\\ \\mathrm{kJ/mol}$ —— "
                     "因为焓变规定**放热为负**。</p>"
                     "<p>同一个数、一个正一个负，这种反差是热化学里最常扣分的地方。"
                     "读数区把两者都列出来了：`燃烧热` 是正的，`ΔH` 是负的。</p>")},
        {"title": "液态水还是气态水",
         "content": ("<p>水由气态变液态会**放出**汽化热（$44\\ \\mathrm{kJ/mol}$）。"
                     "所以如果燃烧产物写成 $\\mathrm{H_2O(g)}$，"
                     "那么「已经放出的热」就少了这部分 —— $\\Delta H$ 会**变得不那么负**"
                     "（例如甲烷约 $-802$ 而不是 $-890$）。</p>"
                     "<p>反过来讲，如果把气态水也算成产物，那还额外有 $2\\times44 "
                     "= 88\\ \\mathrm{kJ}$ 没放出来，两者差 $88$，"
                     "与 $-890.3$ 和 $-802$ 的差正好对上。</p>"
                     "<p>所以做题时必须先看清水是 $\\mathrm{(l)}$ 还是 $\\mathrm{(g)}$。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 中和热与量热法
# =====================================================================
EXPR_NT_Q = f"{abs(K.NEUTRALIZATION_DH)!r}*nw"
EXPR_NT_DT = f"({EXPR_NT_Q})*1000/(100*4.18)"
EXPR_NT_TOTAL = "100*4.18"


def build_neutralization() -> dict:
    for nw in (0.01, 0.02, 0.05, 0.08, 0.1):
        _agree(f"Q(n={nw})", EXPR_NT_Q, abs(K.NEUTRALIZATION_DH) * nw, tol=1e-12, nw=nw)
        _agree(f"ΔT(n={nw})", EXPR_NT_DT, K.temperature_rise(57.3 * nw, 100.0), tol=1e-12, nw=nw)
    _agree("中和热定值", f"{K.NEUTRALIZATION_DH!r}", -57.3, tol=1e-12)
    _agree("0.05 mol → 2.865 kJ", EXPR_NT_Q, 2.865, tol=1e-12, nw=0.05)
    _agree("0.05 mol → ΔT ≈ 6.854 K", EXPR_NT_DT, 6.854, tol=1e-3, nw=0.05)
    _agree("中和热由实验数据反算", f"{K.neutralization_dh(2.865, 0.05)!r}",
           K.NEUTRALIZATION_DH, tol=1e-12)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "calorimeter", "nw": "nw",
                  "caption": "量热计示意图：由温升反推放出的热量，再除以生成的水量"},
        "param": {"name": "nw", "label": "生成的水 $n(\\mathrm{H_2O})$", "min": 0.01, "max": 0.1,
                  "step": 0.005, "value": 0.05, "unit": "mol", "standard": 0.05,
                  "ticks": ["0.01", "0.05 (题设)", "0.1"]},
        "readouts": [
            ro("nw", "$n(\\mathrm{H_2O})$", "nw", 3, "mol"),
            ro("q", "放出的热量 $Q$", EXPR_NT_Q, 3, "kJ"),
            ro("dt", "溶液温升 $\\Delta T$", EXPR_NT_DT, 3, "K"),
            ro("dh", "中和热 $\\Delta H$（定值）", f"{K.NEUTRALIZATION_DH!r}", 1, "kJ/mol"),
            ro_status("hot", "温升是否超过 5 K", EXPR_NT_DT, 5, ">",
                      "温升明显：适合用普通温度计测量", "温升较小"),
        ],
        "constant": {"of": "dh", "label": "$\\Delta H = -57.3$ kJ/mol 是定值 —— 与酸碱种类和浓度都无关"},
    }
    lesson = {
        "language": "zh-CN", "title": "中和热与量热法",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>用 $100\\ \\mathrm{g}$ 稀溶液做中和热实验（比热容按水算 "
            "$c = 4.18\\ \\mathrm{J/(g\\cdot K)}$），生成了 $n\\ \\mathrm{mol}$ 水。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求放出的热量与溶液的温升；</li>"
            "<li>由实验数据反求中和热；</li>"
            "<li>为什么中和热与酸碱的种类、浓度都无关？</li></ol>"),
        "answerLabel": "$n = 0.05$ mol 时",
        "answer": f"$Q = 57.3\\times0.05 = {K.f(57.3 * 0.05, 3)}$ kJ，"
                  f"$\\Delta T = {K.f(K.temperature_rise(57.3 * 0.05, 100.0), 3)}$ K",
    }
    steps = [
        {"title": "量热法的三个公式",
         "content": ("<p>实验测的是**温升**，要换算成热量：</p>"
                     "<p>$Q = m c \\Delta T$（$m$ 是溶液质量，$c$ 是比热容）；</p>"
                     "<p>再由「生成 $1\\ \\mathrm{mol}$ 水」折算成中和热：</p>"
                     "<p>$\\Delta H = -\\dfrac{Q}{n(\\mathrm{H_2O})}$。</p>"
                     "<p>注意最后那个**负号**：放热所以焓变为负。"
                     "本页读数区把 $Q$（正值）与 $\\Delta H$（负值）分开列，"
                     "就是为了避免把符号搞混。</p>")},
        {"title": "为什么与酸碱种类无关",
         "content": ("<p>关键前提是**强酸强碱且完全电离**。此时反应的本质只有一个：</p>"
                     "<p>$\\mathrm{H^+ + OH^- \\to H_2O}$。</p>"
                     "<p>不管是盐酸、硝酸还是硫酸，也不管是氢氧化钠还是氢氧化钾，"
                     "真正发生变化的都是这一件事 —— 所以放热也必然相同，"
                     "恒为 $57.3\\ \\mathrm{kJ/mol}$。</p>"
                     "<p>但如果换成**弱酸或弱碱**（如醋酸、氨水），"
                     "它们要先电离（电离吸热），测出的 $\\Delta H$ 会**偏小**"
                     "（例如醋酸约 $-56.1$）。这是本题型最常考的陷阱。</p>")},
        {"title": "实验上的注意事项",
         "content": ("<p>拖滑块把 $n$ 调小，温升会迅速变小 —— 此时用普通温度计"
                     "就测不准了。真实实验里要保持：</p>"
                     "<p>· 酸碱**浓度适中**（太稀温升太小、太浓则电离不完全）；</p>"
                     "<p>· 用**保温杯**减少散热（否则测出的温升偏小、算出的 $|\\Delta H|$ 偏小）；</p>"
                     "<p>· 温度计要**先测初始温度、混合后读最高温度**。</p>"
                     "<p>这些误差都是「系统偏小」方向，所以实验测得的中和热"
                     "往往略小于 $57.3$。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 活化能与催化剂
# =====================================================================
CT_EA0 = 130.0
CT_DH = -40.0
EXPR_CT_EAF = f"{CT_EA0:.0f}-drop"
EXPR_CT_EAR0 = f"{CT_EA0 - CT_DH:.0f}"
EXPR_CT_EAR = f"{CT_EA0 - CT_DH:.0f}-drop"
EXPR_CT_DH = f"({EXPR_CT_EAF})-({EXPR_CT_EAR})"


def build_catalyst() -> dict:
    for drop in (0.0, 20.0, 50.0, 100.0):
        _agree(f"Ea(正)(降={drop})", EXPR_CT_EAF, CT_EA0 - drop, tol=1e-12, drop=drop)
        _agree(f"Ea(逆)(降={drop})", EXPR_CT_EAR, (CT_EA0 - CT_DH) - drop, tol=1e-12, drop=drop)
        _agree(f"ΔH 不变(降={drop})", EXPR_CT_DH, CT_DH, tol=1e-12, drop=drop)
        # 用内核的 activation_effect 交叉验证（它按 Ea正 − Ea逆 算 ΔH）
        _agree(f"内核 ΔH(降={drop})", f"{K.activation_effect(CT_EA0, CT_DH, drop)[2]!r}",
               CT_DH, tol=1e-12)
        _agree(f"内核 Ea(逆)(降={drop})", EXPR_CT_EAR,
               K.activation_effect(CT_EA0, CT_DH, drop)[1], tol=1e-12, drop=drop)
    _agree("无催化剂时的 Ea(逆) = 170", EXPR_CT_EAR, 170.0, tol=1e-12, drop=0.0)
    _agree("降 40 后 Ea(逆) = 130", EXPR_CT_EAR, 130.0, tol=1e-12, drop=40.0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "catalyst", "drop": "drop",
                  "caption": "灰线 = 无催化剂；绿线 = 有催化剂（峰变矮，但两端高度不动）"},
        "param": {"name": "drop", "label": "催化剂降低的活化能", "min": 0, "max": 100,
                  "step": 5, "value": 0, "unit": "kJ/mol", "standard": 0,
                  "ticks": ["0 (无催化剂)", "50", "100 (高效催化剂)"]},
        "readouts": [
            ro("eaf", "$E_{a(正)}$（有催化剂）", EXPR_CT_EAF, 0, "kJ/mol"),
            ro("ear0", "$E_{a(逆)}$（无催化剂，定值）", EXPR_CT_EAR0, 0, "kJ/mol"),
            ro("ear", "$E_{a(逆)}$（有催化剂）", EXPR_CT_EAR, 0, "kJ/mol"),
            ro("dh", "$\\Delta H$（恒不变）", EXPR_CT_DH, 0, "kJ/mol"),
            ro_status("cat", "是否加了催化剂", "drop", 0, ">",
                      "加了催化剂：活化能下降、速率加快", "没有催化剂"),
        ],
        "constant": {"of": "ear0", "label": "$E_{a(逆)}$ 的基准值恒为 $170$ —— 它由 $E_{a(正)}$ 与 $\\Delta H$ 一起定出"},
    }
    lesson = {
        "language": "zh-CN", "title": "活化能与催化剂",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>某反应的 $\\Delta H = -40\\ \\mathrm{kJ/mol}$，"
            "无催化剂时 $E_{a(正)} = 130\\ \\mathrm{kJ/mol}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求无催化剂时的 $E_{a(逆)}$；</li>"
            "<li>加入催化剂使活化能降低 $x$，求新的正逆活化能；</li>"
            "<li>催化剂改变 $\\Delta H$ 吗？为什么？</li></ol>"),
        "answerLabel": "催化剂降低 50 kJ/mol 时",
        "answer": f"$E_{{a(正)}} = {K.f(CT_EA0 - 50, 0)}$、"
                  f"$E_{{a(逆)}} = {K.f(CT_EA0 - CT_DH - 50, 0)}$ kJ/mol；"
                  f"$\\Delta H$ 仍是 ${K.f(CT_DH, 0)}$",
    }
    steps = [
        {"title": "先由 ΔH 定出逆反应的活化能",
         "content": ("<p>沿用第 1 节的恒等关系 $\\Delta H = E_{a(正)} - E_{a(逆)}$：</p>"
                     "<p>$E_{a(逆)} = E_{a(正)} - \\Delta H = 130 - (-40) "
                     "= 170\\ \\mathrm{kJ/mol}$。</p>"
                     "<p>物理图像很自然：反应是放热的，产物更低，"
                     "所以从产物爬回山顶要走得更远。</p>")},
        {"title": "催化剂同时降低两个活化能",
         "content": ("<p>催化剂提供一条**新的反应路径**，这条路径的过渡态能量更低，"
                     "于是山顶整体下降。</p>"
                     "<p>关键是：**两个方向降的是同一个山顶**，所以正逆活化能"
                     "**同步下降相同的数值**：</p>"
                     "<p>$E'_{a(正)} = E_{a(正)} - x$，"
                     "$E'_{a(逆)} = E_{a(逆)} - x$。</p>"
                     "<p>两式相减，$x$ 恰好抵消：</p>"
                     "<p>$\\Delta H' = E'_{a(正)} - E'_{a(逆)} "
                     "= E_{a(正)} - E_{a(逆)} = \\Delta H$。</p>"
                     "<p>所以**催化剂不改变 ΔH** —— 它只让反应更快到达平衡，"
                     "不改变平衡时的能量关系。读数区那一行 `ΔH` 无论怎么拖都不动。</p>")},
        {"title": "催化剂不改变什么、改变什么",
         "content": ("<p>**不改变**：$\\Delta H$（能量关系）、平衡常数 $K$、平衡转化率。</p>"
                     "<p>**改变**：反应速率（正逆同等加快）、到达平衡所需的时间。</p>"
                     "<p>这一点常被误解成「催化剂能提高产率」—— 其实它只让系统"
                     "**更快**到达那个本来就该达到的平衡位置，"
                     "最终的转化率一模一样。</p>"
                     "<p>顺带一提：催化剂对正逆反应**同样有效**，"
                     "所以它不能把一个「热力学上不可能」的反应变得可能，"
                     "只能让「本来就可能」的反应跑得快些。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "sign": build_sign,
    "hess": build_hess,
    "formation": build_formation,
    "bond": build_bond,
    "combustion": build_combustion,
    "neutralization": build_neutralization,
    "catalyst": build_catalyst,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="热化学 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
