#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「热学与近代物理」交互网页。

全部数值由 lib/thermal_kernel.py 现算（物理常数集中声明在核心里），**不手写数字**。

覆盖七个题型（选择性必修三）：
  gas_law        理想气体状态方程与等温过程的 p-V 图
  kinetic        分子动理论：麦克斯韦速率分布与三个特征速率
  first_law      热力学第一定律 ΔU = Q + W 的能量条
  cycle          矩形循环与热机效率
  photoelectric  光电效应方程 E_k = hν − W₀
  levels         氢原子能级与巴耳末系跃迁
  decay          放射性衰变与半衰期

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

import thermal_kernel as K                    # noqa: E402
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
    if abs(float(got) - float(want)) > tol * max(1.0, abs(float(want))):
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


def sc(name, expr):
    return {"name": name, "expr": expr}


# =====================================================================
# 1) 理想气体状态方程（等温过程的 p-V 图）
# =====================================================================
N_MOL, T0 = 1.0, 300.0                     # 题设：1 mol、300 K
NRT = K.R_GAS * T0                         # = 2493 kPa·L（以 kPa 与 L 为单位时）


def build_gas_law() -> dict:
    EXPR_P = f"{NRT:.0f}/V"
    for V in (5.0, 10.0, 20.0, 37.5, 50.0):
        # 内核口径：p = nRT/V（V 用 m³ 得 Pa，再换算成 kPa；V 用 L 时数值恰好就是 nRT/V）
        want = N_MOL * K.R_GAS * T0 / (V * 1e-3) / 1000.0
        _agree(f"p(V={V})", EXPR_P, want, tol=1e-12, V=V)
        _agree(f"p·V(V={V})", f"({EXPR_P})*V", NRT, tol=1e-12, V=V)
        # 由状态方程算出的 pV 与体积无关（等温不变量）
        _agree(f"等温不变量(V={V})", f"({EXPR_P})*V",
               K.pv_over_t(want * 1000, V * 1e-3, T0) * T0, tol=1e-12, V=V)
    _agree("T = pV/(nR)", f"({EXPR_P})*V/({N_MOL}*{K.R_GAS})", T0, tol=1e-12, V=10.0)
    # 顺便核对 gas_moles 的口径：标准状况（1.013e5 Pa、273 K）下 22.4 L ≈ 1 mol
    _agree("标准状况 22.4 L 的物质的量", "1.013e5*0.0224/(8.31*273)",
           K.gas_moles(1.013e5, 0.0224, 273.0), tol=1e-12)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "gaspv", "V": "V",
                  "caption": "蓝线是等温线 p = nRT/V；黄框面积就是 pV"},
        "param": {"name": "V", "label": "体积 $V$", "min": 5, "max": 50,
                  "step": 0.5, "value": 10.0, "unit": "L", "standard": 10.0,
                  "ticks": ["5", "10 (题设)", "25", "50"]},
        "scalars": [sc("p", EXPR_P)],
        "readouts": [
            ro("p", "$p$", "p", 2, "kPa"),
            ro("v", "$V$", "V", 2, "L"),
            ro("pv", "$pV = nRT$", "p*V", 2, "kPa·L"),
            ro("t", "热力学温度 $T = pV/(nR)$", "p*V/(1*8.31)", 2, "K"),
            ro_status("iso", "是否保持 300 K（等温）", "p*V/(1*8.31)", 300, "==",
                      "等温：温度始终 300 K", "温度变了"),
        ],
        "constant": {"of": "pv", "label": "$pV = nRT$ 恒为 2493 kPa·L —— 沿等温线滑动它不动"},
    }
    lesson = {
        "language": "zh-CN", "title": "理想气体状态方程与等温过程的 p-V 图",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>一定质量的理想气体，物质的量 $n = 1\\ \\mathrm{mol}$，温度恒为 "
            "$T = 300\\ \\mathrm{K}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出压强 $p$ 与体积 $V$ 的关系；</li>"
            "<li>拖动滑块，$pV$ 变不变？说明理由；</li>"
            "<li>$V$ 从 $10\\ \\mathrm{L}$ 增到 $20\\ \\mathrm{L}$，$p$ 变为原来的几分之几？</li></ol>"),
        "answerLabel": "$V = 10$ L 时的状态",
        "answer": f"$p = \\dfrac{{nRT}}{{V}} = {K.f(NRT / 10, 1)}$ kPa；"
                  f"$pV = {K.f(NRT, 0)}$ kPa·L",
    }
    steps = [
        {"title": "状态方程：三个量互相牵制",
         "content": ("<p>理想气体状态方程 $\\dfrac{pV}{T} = nR$ 把 $p$、$V$、$T$ 绑在一起。"
                     "改变其中一个，另外两个必须跟着变，但 $\\dfrac{pV}{T}$ 不变。</p>"
                     f"<p>本题 $nR T = 1 \\times 8.31 \\times 300 = {K.f(NRT, 0)}$，"
                     "所以 $p = \\dfrac{2493}{V}$ —— 一条双曲线。</p>")},
        {"title": "等温线为什么是双曲线",
         "content": ("<p>$T$ 不变时 $pV = nRT$ 是常数，即 $p \\propto \\dfrac{1}{V}$，"
                     "这正是反比例函数的形状。</p>"
                     "<p>图上黄框的面积 $= pV$。滑块滑动时，框会变高变窄或变矮变宽，"
                     "但**面积始终不变** —— 这就是读数里 $pV$ 恒定的几何含义。</p>")},
        {"title": "三个特殊过程",
         "content": ("<p>把状态方程配上不同的约束，就是三条典型的实验定律：</p>"
                     "<p>· $T$ 不变（**等温**）：$pV = $ 常数（玻意耳定律）；</p>"
                     "<p>· $p$ 不变（**等压**）：$\\dfrac{V}{T} = $ 常数（盖-吕萨克定律）；</p>"
                     "<p>· $V$ 不变（**等容**）：$\\dfrac{p}{T} = $ 常数（查理定律）。</p>"
                     "<p>三条合起来才是完整的状态方程 —— 它们是同一个式子在三条"
                     "坐标轴方向上的「切片」。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 分子动理论：速率分布与三个特征速率
# =====================================================================
M_O2 = 0.032                               # 氧气的摩尔质量，kg/mol
EXPR_VP = f"sqrt(2*{K.R_GAS}*T/{M_O2})"
EXPR_VBAR = f"sqrt(8*{K.R_GAS}*T/(PI*{M_O2}))"
EXPR_VRMS = f"sqrt(3*{K.R_GAS}*T/{M_O2})"


def build_kinetic() -> dict:
    for T in (200.0, 300.0, 600.0, 1200.0):
        _agree(f"v_rms(T={T})", EXPR_VRMS, K.rms_speed(T, M_O2), tol=1e-12, T=T)
        _agree(f"v_p(T={T}) 与 v_rms 之比", f"({EXPR_VP})/({EXPR_VRMS})",
               math.sqrt(2.0 / 3.0), tol=1e-12, T=T)
        _agree(f"v̄(T={T}) 与 v_rms 之比", f"({EXPR_VBAR})/({EXPR_VRMS})",
               math.sqrt(8.0 / (3.0 * math.pi)), tol=1e-12, T=T)
        _agree(f"平均动能(T={T})", f"1.5*{K.K_BOLTZ}*T", K.avg_ke(T), tol=1e-12, T=T)
        # 分布函数的峰值确实在 v_p
        B_ = M_O2 / (2 * K.R_GAS * T)
        _agree(f"峰值位置(T={T})", EXPR_VP, math.sqrt(1 / B_), tol=1e-12, T=T)
    # 三个特征速率的比值是常数
    _agree("v_p : v̄ : v_rms 比值恒定",
           f"({EXPR_VP})/({EXPR_VBAR})*(1)", math.sqrt(2) / math.sqrt(8 / math.pi), tol=1e-12, T=300.0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "molecules", "T": "T",
                  "caption": "麦克斯韦速率分布（已按峰值归一化）；三条竖线是三个特征速率"},
        "param": {"name": "T", "label": "温度 $T$", "min": 200, "max": 1200,
                  "step": 20, "value": 300.0, "unit": "K", "standard": 300.0,
                  "ticks": ["200", "300 (题设)", "600", "1200"]},
        "readouts": [
            ro("vp", "最概然速率 $v_p$", EXPR_VP, 1, "m/s"),
            ro("vbar", "平均速率 $\\bar v$", EXPR_VBAR, 1, "m/s"),
            ro("vrms", "方均根速率 $v_{rms}$", EXPR_VRMS, 1, "m/s"),
            ro("ratio", "$v_p : \\bar v : v_{rms}$ 的比", f"({EXPR_VP})/({EXPR_VRMS})", 4),
            ro("vr", "$\\bar v / v_p$（定值 1.128）", f"({EXPR_VBAR})/({EXPR_VP})", 4),
            ro_status("peak", "是否 $v_p < \\bar v$（比值大于 1）",
                      f"({EXPR_VBAR})/({EXPR_VP})", 1, ">",
                      "次序 v_p < v̄ < v_rms 恒成立", "顺序异常"),
        ],
        "constant": {"of": "ratio", "label": "$v_p : v_{rms} = \\sqrt{2}:\\sqrt{3}$ 恒定 —— 与温度、气体种类都无关"},
    }
    lesson = {
        "language": "zh-CN", "title": "麦克斯韦速率分布与三个特征速率",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>氧气（摩尔质量 $M = 0.032\\ \\mathrm{kg/mol}$）处于温度 $T$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $v_p$、$\\bar v$、$v_{rms}$ 的表达式；</li>"
            "<li>拖动滑块升温，曲线怎么变？曲线下的面积变吗？</li>"
            "<li>三个速率的比值与 $T$ 有关吗？</li></ol>"),
        "answerLabel": "$T = 300$ K 时的三个特征速率",
        "answer": f"$v_p \\approx {K.f(K.rms_speed(300.0, M_O2) * math.sqrt(2 / 3), 1)}$，"
                  f"$\\bar v \\approx {K.f(math.sqrt(8 * K.R_GAS * 300.0 / (math.pi * M_O2)), 1)}$，"
                  f"$v_{{rms}} \\approx {K.f(K.rms_speed(300.0, M_O2), 1)}$ m/s",
    }
    steps = [
        {"title": "为什么是「分布」而不是一个确定速率",
         "content": ("<p>分子之间不停地碰撞，每个分子的速度每时每刻都在变，"
                     "所以「某个分子跑多快」没有意义。</p>"
                     "<p>有意义的是**有多少比例**的分子速率落在某个区间 —— "
                     "把这件事画成曲线，就是麦克斯韦速率分布。</p>"
                     "<p>曲线下的**总面积恒为 1**（所有分子都会落在 $0$ 到 $\\infty$ 之间），"
                     "所以升温时曲线右移、变矮、变平，面积不许变。</p>")},
        {"title": "三个特征速率从哪来",
         "content": ("<p>从分布函数 $f(v) \\propto v^2 e^{-Mv^2/(2RT)}$ 出发：</p>"
                     "<p>· 求它的最大值点 → $v_p = \\sqrt{\\dfrac{2RT}{M}$（最概然，"
                     "即「最多分子」的速率）；</p>"
                     "<p>· 求 $\\int_0^\\infty v f(v)\\,dv$ → $\\bar v = \\sqrt{\\dfrac{8RT}{\\pi M}$（平均）；</p>"
                     "<p>· 求 $\\sqrt{\\int_0^\\infty v^2 f(v)\\,dv}$ → $v_{rms} = \\sqrt{\\dfrac{3RT}{M}$"
                     "（方均根，压强公式里用的就是它）。</p>")},
        {"title": "比值恒定与分母不同的原因",
         "content": ("<p>三个式子都正比于 $\\sqrt{T/M}$，只是系数不同，所以比值"
                     "$\\sqrt2 : \\sqrt{8/\\pi} : \\sqrt3 \\approx 1 : 1.128 : 1.225$ "
                     "**与 $T$ 和气体种类都无关** —— 读数区里那一行永远不动。</p>"
                     "<p>为什么压强用 $v_{rms}$ 而不是 $\\bar v$？因为理想气体压强公式"
                     "$p = \\dfrac13 \\dfrac{N}{V} m \\overline{v^2}$ 里出现的本来就是"
                     "速率的**平方平均**，也就是 $v_{rms}^2$。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 热力学第一定律（能量条）
# =====================================================================
W_WORK = 80.0                              # 题设：外界对气体做功 80 J（定值）
EXPR_DU = f"Q+{W_WORK:.0f}"


def build_first_law() -> dict:
    for Q in (-200.0, -80.0, 0.0, 60.0, 200.0):
        _agree(f"ΔU(Q={Q})", EXPR_DU, K.first_law(Q, W_WORK), tol=1e-12, Q=Q)
    _agree("等温时 Q = −W", EXPR_DU, 0.0, tol=1e-12, Q=-W_WORK)
    _agree("绝热时 ΔU = W", EXPR_DU, W_WORK, tol=1e-12, Q=0.0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "energybar", "Q": "Q",
                  "caption": "三条柱：吸热 Q、外界做功 W、内能变化 ΔU = Q + W"},
        "param": {"name": "Q", "label": "气体吸热 $Q$（放热为负）", "min": -200, "max": 200,
                  "step": 5, "value": 60.0, "unit": "J", "standard": 60.0,
                  "ticks": ["-200", "-80 (等温)", "0 (绝热)", "60 (题设)", "200"]},
        "readouts": [
            ro("q", "吸热 $Q$", "Q", 0, "J"),
            ro("w", "外界对气体做功 $W$（定值）", f"{W_WORK:.0f}", 0, "J"),
            ro("du", "内能变化 $\\Delta U = Q + W$", EXPR_DU, 0, "J"),
            ro("dw", "气体对外做功 $W' = -W$", f"-{W_WORK:.0f}", 0, "J"),
            ro_status("up", "内能增大还是减小", EXPR_DU, 0, ">",
                      "内能增大（温度升高）", "内能不增（温度不变或降低）"),
        ],
        "constant": {"of": "w", "label": "$W = 80$ J 是定值：只让吸热 $Q$ 变，看内能怎么跟着走"},
    }
    lesson = {
        "language": "zh-CN", "title": "热力学第一定律 ΔU = Q + W",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>一定质量的气体，外界对它做功 $W = 80\\ \\mathrm{J}$，"
            "同时它吸热 $Q$（可为负，表示放热）。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出内能变化 $\\Delta U$ 的表达式；</li>"
            "<li>拖动滑块，$\\Delta U = 0$ 对应什么样的过程？</li>"
            "<li>如果改成「气体对外做功 $80\\ \\mathrm{J}$」，$\\Delta U$ 怎么变？</li></ol>"),
        "answerLabel": "$Q = 60$ J 时的内能变化",
        "answer": f"$\\Delta U = Q + W = 60 + 80 = {K.f(K.first_law(60.0, W_WORK), 0)}$ J（内能增大）",
    }
    steps = [
        {"title": "符号约定必须先说清",
         "content": ("<p>本页采用教材主流约定：</p>"
                     "<p>· $Q > 0$ 表示气体**吸热**，$Q < 0$ 表示放热；</p>"
                     "<p>· $W > 0$ 表示**外界对气体做功**（气体被压缩），"
                     "$W < 0$ 表示气体对外做功（膨胀）。</p>"
                     "<p>于是 $\\Delta U = Q + W$。**换一套约定式子就要换符号**，"
                     "不同教材各有一套，做题时务必先看清题目怎么说 —— "
                     "本页把所有涉及 $W$ 的地方都标了「外界做功为正」。</p>")},
        {"title": "三种典型过程",
         "content": ("<p>· **绝热**（$Q = 0$）：$\\Delta U = W$ —— 绝热压缩升温、绝热膨胀降温，"
                     "光靠做功就能改内能；</p>"
                     "<p>· **等温**（$\\Delta U = 0$，理想气体内能只由温度决定）：$Q = -W$ —— "
                     "外界做的功全部以热的形式放出去；</p>"
                     "<p>· **等容**（$W = 0$）：$\\Delta U = Q$ —— 不做功，吸的热全变内能。</p>"
                     "<p>把滑块拖到 $Q = -80\\ \\mathrm{J}$ 就是等温过程（读数区状态灯会亮）。</p>")},
        {"title": "内能只由温度决定",
         "content": ("<p>对理想气体，内能只是**所有分子动能之和**，而平均动能只由 $T$ 决定，"
                     "所以 $\\Delta U = 0 \\iff \\Delta T = 0$。</p>"
                     "<p>这条性质让等温过程变得很好算：不管是膨胀还是压缩，"
                     "只要温度不变，内能就不变，吸的热与做的功恰好抵消。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 矩形循环与热机效率（单原子理想气体）
# =====================================================================
P1, V1, V2 = 200.0, 2.0, 8.0
CV_R, CP_R = 1.5, 2.5                      # 单原子：Cv/R = 3/2，Cp/R = 5/2
EXPR_WNET = f"({P1:.0f}-p2)*({V2:.0f}-{V1:.0f})"
EXPR_QAB = f"{CP_R:.1f}*{P1:.0f}*({V2:.0f}-{V1:.0f})"          # 等压吸热
EXPR_QDA = f"{CV_R:.1f}*{V1:.0f}*({P1:.0f}-p2)"                # 等容吸热
EXPR_QIN = f"({EXPR_QAB})+({EXPR_QDA})"
EXPR_ETA = f"({EXPR_WNET})/({EXPR_QIN})"


def build_cycle() -> dict:
    for p2 in (40.0, 70.0, 100.0, 130.0, 160.0):
        wnet = (P1 - p2) * (V2 - V1)
        qin = CP_R * P1 * (V2 - V1) + CV_R * V1 * (P1 - p2)
        qout = CV_R * V2 * (P1 - p2) + CP_R * p2 * (V2 - V1)   # 两个放热段
        _agree(f"W_net(p2={p2})", EXPR_WNET, wnet, tol=1e-12, p2=p2)
        _agree(f"Q_in(p2={p2})", EXPR_QIN, qin, tol=1e-12, p2=p2)
        _agree(f"η(p2={p2})", EXPR_ETA, K.heat_engine_eff(qin, qout), tol=1e-12, p2=p2)
        # 净功 = 吸热 − 放热（能量守恒的循环版本）
        _agree(f"W_net = Q_in − Q_out(p2={p2})", EXPR_WNET, qin - qout, tol=1e-12, p2=p2)
    _agree("p2 → p1 时 η → 0", EXPR_ETA, 0.0, tol=1e-12, p2=P1)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "pvcycle", "p2": "p2",
                  "caption": "顺时针循环（黄框面积 = 净功）；A→B 等压膨胀是主要吸热段"},
        "param": {"name": "p2", "label": "循环的低压 $p_2$", "min": 40, "max": 160,
                  "step": 5, "value": 100.0, "unit": "kPa", "standard": 100.0,
                  "ticks": ["40", "100 (题设)", "160"]},
        "readouts": [
            ro("wnet", "净功 $W_{net} = (p_1-p_2)(V_2-V_1)$", EXPR_WNET, 0, "J"),
            ro("qin", "总吸热 $Q_{in} = Q_{AB} + Q_{DA}$", EXPR_QIN, 0, "J"),
            ro("eta", "热机效率 $\\eta = W_{net}/Q_{in}$", EXPR_ETA, 4),
            ro("pct", "效率百分数", f"({EXPR_ETA})*100", 2, "%"),
            ro("qab", "$Q_{AB}$（定值）", EXPR_QAB, 0, "J"),
            ro_status("dir", "是否是顺时针循环（对外做正功）",
                      f"({P1:.0f}-p2)", 0, ">",
                      "顺时针：净功为正，是热机", "逆时针：净功为负，是制冷机"),
        ],
        "constant": {"of": "qab", "label": "$Q_{AB}$ 与 $V_1,V_2$ 都固定 —— 只有低压 $p_2$ 在变"},
    }
    lesson = {
        "language": "zh-CN", "title": "矩形循环与热机效率",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>单原子理想气体（$C_V = \\frac32 R$）经历矩形循环："
            "$V_1 = 2\\ \\mathrm{L}$、$V_2 = 8\\ \\mathrm{L}$、"
            "$p_1 = 200\\ \\mathrm{kPa}$，低压 $p_2$ 可调。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>哪两段吸热、哪两段放热？</li>"
            "<li>写出净功与总吸热的表达式；</li>"
            "<li>为什么效率总小于 1？把 $p_2$ 拖到接近 $p_1$ 会怎样？</li></ol>"),
        "answerLabel": "$p_2 = 100$ kPa 时的效率",
        "answer": f"$W_{{net}} = {K.f((P1 - 100) * (V2 - V1), 0)}$ J，"
                  f"$\\eta \\approx {K.f(((P1 - 100) * (V2 - V1)) / (CP_R * P1 * (V2 - V1) + CV_R * V1 * (P1 - 100)), 4)}$",
    }
    steps = [
        {"title": "先把净功读成面积",
         "content": ("<p>在 $p$-$V$ 图上，$W = \\int p\\,dV$ 就是曲线下的面积。"
                     "循环一圈回到出发点，内能恢复原值 $\\Delta U = 0$，"
                     "于是净功就等于**闭合曲线围出的面积**。</p>"
                     "<p>这里是矩形：$W_{net} = (p_1 - p_2)(V_2 - V_1)$。"
                     "**顺时针**一圈面积取正（对外做功，热机），逆时针取负（制冷机）。</p>")},
        {"title": "哪两段吸热",
         "content": ("<p>· $A \\to B$ 等压膨胀：温度升高，吸热 $Q_{AB} = nC_p\\Delta T = "
                     "C_p\\Delta(pV)/R$，代入得 $Q_{AB} = 2.5\\,p_1(V_2-V_1)$；</p>"
                     "<p>· $D \\to A$ 等容升压：温度升高，吸热 $Q_{DA} = nC_V\\Delta T = "
                     "1.5\\,V_1(p_1-p_2)$；</p>"
                     "<p>· $B \\to C$ 等容降压、$C \\to D$ 等压压缩都是**放热**。</p>"
                     "<p>所以总吸热 $Q_{in} = Q_{AB} + Q_{DA}$，"
                     "效率 $\\eta = \\dfrac{W_{net}}{Q_{in}}$。</p>")},
        {"title": "为什么 η 永远小于 1",
         "content": ("<p>因为放热段不可避免 —— 气体在低压处必须被压回去，"
                     "这一步外界对它做功、它向外放热，这部分热量无法回收。</p>"
                     "<p>把 $p_2$ 拖到接近 $p_1$，矩形变得又扁又小：净功趋近 $0$，"
                     "但 $Q_{AB}$ 一点没少，于是 $\\eta \\to 0$。反过来说，"
                     "要效率高就得让循环「围得大」，可这也意味着更高的压强与更大的温差。</p>"
                     "<p>卡诺早就证明：工作在 $T_h$ 与 $T_c$ 之间的任何热机，"
                     "效率都超不过 $1 - \\dfrac{T_c}{T_h}$ —— 与工作物质、与具体循环形状都无关。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 光电效应
# =====================================================================
W0_PHOTO = 4.0e-19                          # 逸出功 4.0e-19 J（= 2.5 eV）
NU0_14 = W0_PHOTO / K.H_PLANCK / 1e14       # 截止频率，×10^14 Hz
EXPR_NU = "nu"
EXPR_EK19 = f"({K.H_PLANCK:.2e}*nu-{W0_PHOTO:.2e})/1e-19"
EXPR_EKEV = f"({K.H_PLANCK:.2e}*nu-{W0_PHOTO:.2e})/{K.E_CHARGE:.2e}"


def build_photoelectric() -> dict:
    for nu14 in (4.0, 6.0332, 10.0, 14.0):
        nu = nu14 * 1e14
        _agree(f"截止频率×(nu={nu14})", f"{W0_PHOTO:.2e}/{K.H_PLANCK:.2e}/1e14", NU0_14, tol=1e-12)
        _agree(f"E_k(eV)(nu={nu14})", EXPR_EKEV, K.ek_max(nu, W0_PHOTO) / K.E_CHARGE, tol=1e-12, nu=nu)
        _agree(f"E_k(×10⁻¹⁹J)(nu={nu14})", EXPR_EK19,
               K.ek_max(nu, W0_PHOTO) / 1e-19, tol=1e-12, nu=nu)
        _agree(f"遏止电压(nu={nu14})", EXPR_EKEV,
               K.stopping_voltage(K.ek_max(nu, W0_PHOTO)), tol=1e-12, nu=nu)
    _agree("截止频率处 E_k = 0", EXPR_EK19, 0.0, tol=1e-9, nu=NU0_14 * 1e14)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "photo", "nu": "nu",
                  "caption": "E_k–ν 是直线：斜率 = h，横轴截距 = 截止频率 ν₀"},
        "param": {"name": "nu14", "label": "入射光频率 $\\nu$（$\\times 10^{14}$ Hz）",
                  "min": 4, "max": 14, "step": 0.1, "value": 10.0, "unit": "×10¹⁴ Hz",
                  "standard": 10.0, "ticks": ["4", "6.03 (ν₀)", "10 (题设)", "14"]},
        "scalars": [sc("nu", "nu14*1e14")],
        "readouts": [
            ro("nu14", "频率 $\\nu$", "nu14", 2, "×10¹⁴ Hz"),
            ro("ek19", "最大初动能 $E_k$", EXPR_EK19, 3, "×10⁻¹⁹ J"),
            ro("ekev", "$E_k$（eV）", EXPR_EKEV, 3, "eV"),
            ro("ustop", "遏止电压 $U = E_k/e$", EXPR_EKEV, 3, "V"),
            ro("nu0", "截止频率 $\\nu_0$（定值）",
               f"{W0_PHOTO:.2e}/{K.H_PLANCK:.2e}/1e14", 3, "×10¹⁴ Hz"),
            ro_status("on", "是否发生光电效应（$E_k > 0$）", EXPR_EK19, 0, ">",
                      "发生：E_k > 0", "不发生：ν < ν₀"),
        ],
        "constant": {"of": "nu0", "label": "$\\nu_0 = W_0/h$ 恒为 6.033×10¹⁴ Hz —— 与光强无关"},
    }
    lesson = {
        "language": "zh-CN", "title": "光电效应方程与截止频率",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>某金属的逸出功 $W_0 = 4.0\\times10^{-19}\\ \\mathrm{J}$，"
            "用频率 $\\nu$ 的单色光照射。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出光电子的最大初动能 $E_k$；</li>"
            "<li>求截止频率 $\\nu_0$，并说明低于它为什么不发生光电效应；</li>"
            "<li>增大光强（不改频率），$E_k$ 变吗？</li></ol>"),
        "answerLabel": "$\\nu = 10\\times10^{14}$ Hz 时",
        "answer": f"$\\nu_0 \\approx {K.f(NU0_14, 3)}\\times10^{{14}}$ Hz；"
                  f"$E_k \\approx {K.f(K.ek_max(1.0e15, W0_PHOTO) / K.E_CHARGE, 3)}$ eV，"
                  f"遏止电压同值",
    }
    steps = [
        {"title": "爱因斯坦方程：一份一份地给",
         "content": ("<p>光是一份一份的，每份能量 $E = h\\nu$。电子吸收一份后，"
                     "先要付出逸出功 $W_0$ 挣脱金属，剩下的才成为动能：</p>"
                     "<p>$h\\nu = W_0 + E_k$，即 $E_k = h\\nu - W_0$。</p>"
                     "<p>这条式子立刻解释了经典波动说讲不通的三件事："
                     "存在**截止频率**、$E_k$ 只由频率决定、响应几乎瞬时。</p>")},
        {"title": "图线就是一条直线",
         "content": ("<p>把 $E_k$ 对 $\\nu$ 作图，得到斜率 $h$、横轴截距 $\\nu_0 = W_0/h$ 的直线。</p>"
                     "<p>· $\\nu < \\nu_0$：一份光子的能量还不够付逸出功，"
                     "**再强的光也没用**（这是波动说无法解释的）；</p>"
                     "<p>· $\\nu > \\nu_0$：超过部分全部变成动能。</p>"
                     "<p>读数区里 $E_k$ 的 eV 数与遏止电压的伏特数是**同一个数**，"
                     "因为 $U = E_k/e$，而 eV 本来就是「电子过一个伏特得到的能量」。</p>")},
        {"title": "光强管什么",
         "content": ("<p>光强只决定**单位时间有多少个光子**，也就是有多少电子能被打出来 —— "
                     "表现为饱和光电流的大小。</p>"
                     "<p>它**不改变**每个光子的能量，所以 $E_k$ 与遏止电压都与光强无关。"
                     "把滑块拖到 $\\nu < \\nu_0$ 那一段，状态灯变红：即使光再强，"
                     "读数也是负的，光电效应不发生。</p>"
                     "<p>顺带记住：$hc = 1240\\ \\mathrm{eV\\cdot nm}$，"
                     "由能量算波长时非常好用 —— 下一节的氢光谱就要用它。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 氢原子能级与巴耳末系
# =====================================================================
HC_EVNM = 1243.1                            # hc ≈ 1243.1 eV·nm（由常数算出）
EXPR_EN = "-13.6/(n*n)"
EXPR_DE = "(-13.6/(n*n))+13.6/4"
EXPR_LAM = f"{HC_EVNM:.1f}/((-13.6/(n*n))+13.6/4)"


def build_levels() -> dict:
    for n in (3, 4, 5, 6):
        _agree(f"E_n(n={n})", EXPR_EN, K.energy_level(n), tol=1e-12, n=n)
        _agree(f"ΔE(n={n})", EXPR_DE, K.transition_energy(n, 2), tol=1e-12, n=n)
        lam_nm = K.level_wavelength(n, 2) * 1e9
        _agree(f"λ(n={n})", EXPR_LAM, lam_nm, tol=2e-4, n=n)
    _agree("基态 = −13.6 eV", EXPR_EN, K.energy_level(1), tol=1e-12, n=1)
    # 能级差越大 ⇒ 波长越短
    assert float(_jseval(EXPR_LAM, n=6)) < float(_jseval(EXPR_LAM, n=3))

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "levels", "n": "n",
                  "caption": "氢原子能级图；绿箭头是从 n 跃迁到 n=2 的巴耳末系"},
        "param": {"name": "n", "label": "跃迁的高能级 $n$", "min": 3, "max": 6,
                  "step": 1, "value": 3, "unit": "", "standard": 3,
                  "ticks": ["3 (Hα)", "4 (Hβ)", "5 (Hγ)", "6 (Hδ)"]},
        "readouts": [
            ro("en", "$E_n$", EXPR_EN, 3, "eV"),
            ro("de", "光子能量 $\\Delta E = E_n - E_2$", EXPR_DE, 4, "eV"),
            ro("lam", "波长 $\\lambda = hc/\\Delta E$", EXPR_LAM, 1, "nm"),
            ro("e1", "基态 $E_1$（定值）", "-13.6", 1, "eV"),
            ro_status("vis", "是否比 Hα 线更「紫」（$\\lambda < 650$ nm）",
                      f"({EXPR_LAM})", 650, "<",
                      "波长更短：更高的能级差 ⇒ 更偏向紫端", "仍是 Hα 附近的红光"),
        ],
        "constant": {"of": "e1", "label": "$E_1 = -13.6$ eV 是定值 —— 所有能级都由它定标"},
    }
    lesson = {
        "language": "zh-CN", "title": "氢原子能级与巴耳末系",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>氢原子能级 $E_n = -\\dfrac{13.6}{n^2}\\ \\mathrm{eV}$。"
            "电子从高能级 $n$ 跃迁到 $n = 2$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求 $E_n$ 与光子能量 $\\Delta E$；</li>"
            "<li>求波长 $\\lambda$，并判断是否可见；</li>"
            "<li>为什么 $n = 3$ 那条线是红的、$n = 6$ 那条是紫的？</li></ol>"),
        "answerLabel": "$n = 3 \\to 2$（Hα 线）",
        "answer": f"$\\Delta E \\approx {K.f(K.transition_energy(3, 2), 3)}$ eV，"
                  f"$\\lambda \\approx {K.f(K.level_wavelength(3, 2) * 1e9, 1)}$ nm（红光）",
    }
    steps = [
        {"title": "能级是「负」的，说明电子被束缚",
         "content": ("<p>$E_n = -\\dfrac{13.6}{n^2}\\ \\mathrm{eV}$：$n$ 越大越接近 $0$，"
                     "$n \\to \\infty$ 时 $E \\to 0$。</p>"
                     "<p>负号的含义是：要把电子从 $n$ 能级**移到无穷远并静止**，"
                     "必须**供给** $|E_n|$ 的能量。所以 $13.6\\ \\mathrm{eV}$ 就是基态氢原子的"
                     "电离能。</p>")},
        {"title": "跃迁：能量差变成光子",
         "content": ("<p>电子从高能级 $n$ 跳到低能级 $2$，多出来的能量以**一个光子**的形式放出去：</p>"
                     "<p>$h\\nu = E_n - E_2 = 13.6\\left(\\dfrac{1}{4} - \\dfrac{1}{n^2}\\right)\\ \\mathrm{eV}$。</p>"
                     "<p>再配上 $\\lambda = \\dfrac{hc}{\\Delta E}$。用 $hc = 1240\\ \\mathrm{eV\\cdot nm}$ "
                     "可以直接心算：$\\Delta E = 1.89\\ \\mathrm{eV}$ 对应 $\\lambda \\approx 1240/1.89 "
                     "\\approx 656\\ \\mathrm{nm}$。</p>"
                     "<p>这一类跃迁到 $n = 2$ 的谱线叫**巴耳末系**，"
                     "恰好落在可见光区 —— 所以氢放电管发出的光肉眼就能看见。</p>")},
        {"title": "为什么短波是紫的",
         "content": ("<p>$n$ 越大，起点越高，$\\Delta E$ 越大，波长 $\\lambda = hc/\\Delta E$ 就越短。</p>"
                     "<p>$n = 3$（Hα，656 nm 红）→ $n = 6$（Hδ，410 nm 紫），"
                     "谱线越来越密、越来越靠近 $364.6\\ \\mathrm{nm}$ 的系限 —— "
                     "拖滑块能看到波长单调变小。</p>"
                     "<p>顺带一提：跃迁到 $n = 1$ 的是**莱曼系**（紫外），"
                     "跃迁到 $n = 3$ 的是**帕申系**（红外），都看不见。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 放射性衰变与半衰期
# =====================================================================
HALF_LIFE, N_INITIAL = 5.0, 1000
EXPR_RATIO = f"pow(0.5, t/{HALF_LIFE:.0f})"
EXPR_COUNT = f"{N_INITIAL}*pow(0.5, t/{HALF_LIFE:.0f})"
EXPR_DEC = f"(1-pow(0.5, t/{HALF_LIFE:.0f}))*100"
EXPR_HL = f"t/{HALF_LIFE:.0f}"


def build_decay() -> dict:
    for t in (0.0, 2.5, 5.0, 15.0, 30.0):
        _agree(f"剩余比例(t={t})", EXPR_RATIO, K.remaining(1.0, HALF_LIFE, t), tol=1e-12, t=t)
        _agree(f"剩余个数(t={t})", EXPR_COUNT,
               K.remaining(float(N_INITIAL), HALF_LIFE, t), tol=1e-12, t=t)
        _agree(f"已衰变%(t={t})", EXPR_DEC,
               K.decayed_fraction(HALF_LIFE, t) * 100, tol=1e-12, t=t)
        _agree(f"半衰期数(t={t})", EXPR_HL, K.half_lives(t, HALF_LIFE), tol=1e-12, t=t)
    _agree("一个半衰期后剩一半", EXPR_RATIO, 0.5, tol=1e-12, t=HALF_LIFE)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "decay", "t": "t",
                  "caption": "指数衰减曲线；绿色阶梯线标出一个、两个、三个半衰期"},
        "param": {"name": "t", "label": "经过的时间 $t$", "min": 0, "max": 30,
                  "step": 0.5, "value": 5.0, "unit": "年", "standard": 5.0,
                  "ticks": ["0", "5 (1T)", "10 (2T)", "15 (3T)", "30"]},
        "readouts": [
            ro("ratio", "剩余比例 $N/N_0$", EXPR_RATIO, 5),
            ro("count", "剩余个数（$N_0 = 1000$）", EXPR_COUNT, 2),
            ro("hl", "经过的半衰期数 $t/T$", EXPR_HL, 2),
            ro("dec", "已衰变比例", EXPR_DEC, 2, "%"),
            ro("thalf", "半衰期 $T$（定值）", "5", 0, "年"),
            ro_status("int", "是否恰为整数个半衰期",
                      f"abs(({EXPR_HL})-floor(({EXPR_HL})+0.5))", 0.05, "<",
                      "整数个半衰期：剩余是 1/2 的整数次幂", "不是整数个半衰期"),
        ],
        "constant": {"of": "thalf", "label": "$T = 5$ 年、$N_0 = 1000$ 都是定值"},
    }
    lesson = {
        "language": "zh-CN", "title": "放射性衰变与半衰期",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>某放射性同位素有 $N_0 = 1000$ 个原子核，半衰期 $T = 5$ 年。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $t$ 年后剩余原子核数 $N$ 的表达式；</li>"
            "<li>经过 $15$ 年还剩多少个？</li>"
            "<li>再经过 $15$ 年呢？说明「一半」是对谁而言的。</li></ol>"),
        "answerLabel": "$t = 15$ 年（3 个半衰期）",
        "answer": f"$N = N_0 \\left(\\dfrac{{1}}{{2}}\\right)^{{t/T}}$；"
                  f"$t = 15$ 年时 $N = {K.f(K.remaining(float(N_INITIAL), HALF_LIFE, 15.0), 2)}$ 个",
    }
    steps = [
        {"title": "衰变是随机的，但大量核服从统计规律",
         "content": ("<p>**某一个**原子核什么时候衰变完全无法预测，"
                     "这是量子力学的随机性。</p>"
                     "<p>但当核的数目非常多时，剩下多少是有确定规律的："
                     "每过一个半衰期，**未衰变的数目减半**。</p>"
                     "<p>所以 $N = N_0\\left(\\dfrac12\\right)^{t/T}$。"
                     "把滑块拖到 $t = 15$ 年（3 个半衰期），剩 $1000/8 = 125$ 个。</p>")},
        {"title": "「一半」是对剩下的那些说的",
         "content": ("<p>常见误区：以为「过 2 个半衰期就衰变掉全部」。</p>"
                     "<p>实际上 $1/2$、$1/4$、$1/8$…… 永远不到 $0$，"
                     "只是越来越小。再过 $15$ 年（第 6 个半衰期）剩 "
                     "$1000/64 \\approx 15.6$ 个 —— 但**核的个数必须是整数**，"
                     "所以 $N_0$ 很大时公式才准；$N_0$ 只有几个时只能谈概率。</p>")},
        {"title": "半衰期是核的固有属性",
         "content": ("<p>半衰期只由原子核内部结构决定，"
                     "**与温度、压强、化学状态、是否与其他元素化合都无关** —— "
                     "因为它们只影响核外电子，碰不到核内部。</p>"
                     "<p>正因如此，半衰期成了**测年**的天然时钟："
                     "碳-14 半衰期约 5730 年，用来测几万年内的生物遗骸；"
                     "铀-238 半衰期 45 亿年，用来测岩石年龄。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "gas_law": build_gas_law,
    "kinetic": build_kinetic,
    "first_law": build_first_law,
    "cycle": build_cycle,
    "photoelectric": build_photoelectric,
    "levels": build_levels,
    "decay": build_decay,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="热学与近代物理 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
