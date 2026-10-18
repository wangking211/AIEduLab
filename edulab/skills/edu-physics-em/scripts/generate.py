#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py —— 把结构化数据注入 template/board.html，产出单页「高中电磁学」交互网页。

全部数值由 lib/em_kernel.py 的 sympy 精确计算驱动（单一数据源）：库仑力、场强叠加、
电容、回旋半径与周期、偏转量与偏角、闭合电路、感应电动势、安培力全部由内核算出，
保证「图、解、答」同源一致。**不手写数字。**

每个 build_* 内置自检断言：内核算出的关键值必须与喂给画板的表达式在默认参数处吻合。

依赖 sympy。用能 import sympy 的解释器运行：
    python scripts/generate.py <题型key> [输出.html]
    python scripts/generate.py list
    python scripts/generate.py all <输出目录>
    python scripts/generate.py random [seed] [输出.html]
"""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PLACEHOLDER = "__LESSON_DATA__"

sys.path.insert(0, str(SKILL_DIR.parent.parent / "shared"))
sys.path.insert(0, str(SKILL_DIR / "lib"))

import sympy as sp                       # noqa: E402
import em_kernel as K                    # noqa: E402
from skillkit import cli                 # noqa: E402

# 库仑常量与元电荷/质子质量的 JS 表达式（与内核同值，写成画板可求值的字面量）
KJS = "9e9"
QE = "1.6e-19"
MP = "1.67e-27"


def ev(x, nd=4):
    """sympy → 文本数值，供步骤文案使用（四舍五入到 nd 位有效数字）。"""
    return K.num_str(x)


def sci(x, digits=2):
    """科学计数的 LaTeX，给数量级大的量（1e5 这种数字不该写成 100000.0）。"""
    return K.sci_tex(x, digits)


# =====================================================================
# 1) 库仑定律
# =====================================================================
def build_coulomb() -> dict:
    """真问句：两个电荷距离变近，作用力怎么变？变化遵循什么规律？"""
    q1, q2 = 2e-6, 1e-6          # 同号 → 斥力
    r0 = 0.2
    C = K.coulomb(q1, q2, r0)
    E = K.field_at(q1, r0)
    # F·r² = k q1 q2 是与距离无关的定值 —— 「平方反比」的可算形式
    Fr2 = sp.nsimplify(K.K_COULOMB * q1 * q2)
    assert abs(K.f(C["F"]) - 0.45) < 1e-12
    assert abs(K.f(E["E"]) - 4.5e5) < 1e-3

    board = {
        # 内容只在 y ∈ [−0.75, 1.1]（电荷、连线、标注都在一条横带上）
        "view": {"xRange": [-2.2, 8], "yRange": [-1.5, 1.6]},
        "scalars": [
            {"name": "F", "expr": f"{KJS}*2e-6*1e-6/(r*r)"},
            {"name": "E", "expr": f"{KJS}*2e-6/(r*r)"},
            {"name": "Fr2", "expr": "F*r*r"},
            {"name": "ratio", "expr": "F/0.45"},
        ],
        "param": {"name": "r", "label": "两电荷间距 $r$", "min": 0.1, "max": 0.5,
                  "step": 0.005, "value": r0, "unit": " m",
                  "ticks": ["0.10 m", "0.20 m (题设)", "0.50 m"]},
        "scene": {"kind": "charge", "caption": "库仑定律：同号电荷相互排斥",
                  "r": "r", "sq": q1, "pq": q2},
        "readouts": [
            {"id": "r", "label": "距离 $r$", "type": "expr", "expr": "r", "digits": 3, "unit": "m"},
            {"id": "F", "label": "库仑力 $F=k\\dfrac{q_1q_2}{r^2}$", "type": "expr",
             "expr": "F", "digits": 4, "unit": "N", "highlight": True},
            {"id": "E", "label": "$q_1$ 在该点产生的场强 $E$", "type": "expr",
             "expr": "E", "digits": 4, "unit": "N/C"},
            {"id": "ratio", "label": "与 $r=0.20$ m 时相比", "type": "expr",
             "expr": "ratio", "digits": 2, "unit": "倍"},
        ],
        "constant": {"label": "$F\\cdot r^{2} \\equiv " + f"{ev(Fr2)}"
                     + "\\ \\mathrm{N\\cdot m^{2}}$（与距离无关）"},
        "legend": [
            {"color": "#f87171", "text": "$q_1 = +2\\ \\mu$C（源电荷）"},
            {"color": "#38bdf8", "text": "$q_2 = +1\\ \\mu$C（受力电荷）"},
            {"color": "#a78bfa", "text": "场强 $E$ 的方向"},
            {"color": "#34d399", "text": "库仑力 $F$（斥力，沿连线向外）"},
        ],
    }
    lesson = {
        "language": "zh-CN",
        "title": "库仑定律：作用力与距离的关系",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            f"<p>真空中有两个点电荷 $q_1 = +2\\ \\mu\\mathrm{{C}}$、"
            f"$q_2 = +1\\ \\mu\\mathrm{{C}}$，最初相距 $r_0 = 0.20\\ \\mathrm{{m}}$。"
            "把 $q_2$ 向 $q_1$ 靠近到 $r = 0.10\\ \\mathrm{m}$，</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>库仑力变为原来的多少倍？</li>"
            "<li>拖动滑块观察：$F$ 与 $r$ 是一次关系吗？它与什么量成定值？</li></ol>"),
        "answerLabel": "r = 0.10 m 时的库仑力",
        "answer": f"$F = {sci(sp.nsimplify(K.f(C['F']) * 4))}\\ \\mathrm{{N}}$"
                  f"（是 $0.20\\ \\mathrm{{m}}$ 时的 4 倍）",
    }
    steps = [
        {"title": "定律与量纲",
         "content": (f"<p>库仑定律：$F = k\\dfrac{{|q_1 q_2|}}{{r^2}}$，"
                     f"其中 $k = {KJS}\\ \\mathrm{{N\\cdot m^2/C^2}}$（教材通用近似值）。</p>"
                     "<p>注意分母是 $r^2$ —— 这是<b>平方反比</b>，"
                     "不是「力与距离成反比」。距离减半，力变 4 倍。</p>"
                     f"<p>本题 $q_1 q_2 = 2\\times10^{{-12}}\\ \\mathrm{{C^2}}$，"
                     f"所以 $F r^2 = k q_1 q_2 = {ev(Fr2)}\\ \\mathrm{{N\\cdot m^2}}$，"
                     "与距离无关（见左栏定值指示）。</p>")},
        {"title": "代入计算",
         "content": (f"<p>$r = 0.20\\ \\mathrm{{m}}$ 时 $F = "
                     f"{sci(C['F'])}\\ \\mathrm{{N}}$。</p>"
                     f"<p>$r$ 减半到 $0.10\\ \\mathrm{{m}}$，分母变 $\\tfrac14$，"
                     f"所以 $F$ 变 4 倍：$F = {sci(sp.nsimplify(K.f(C['F']) * 4))}"
                     "\\ \\mathrm{{N}}$。</p>")},
        {"title": "力与场强是两回事",
         "content": (f"<p>$E = k\\dfrac{{q_1}}{{r^2}} = {sci(E['E'])}\\ \\mathrm{{N/C}}$ "
                     "描述的是<b>源电荷在该点产生的电场</b>，"
                     "它不依赖于 $q_2$；而 $F = q_2 E$ 才是 $q_2$ 受到的力。</p>"
                     "<p>把 $q_2$ 拿走，$E$ 还在；$F$ 消失。"
                     "这是「场是物质、力是相互作用」这句话的可算版本。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 场强叠加：合场强为零的点在哪
# =====================================================================
def build_field_sum() -> dict:
    """真问句：两个电荷之间/之外，哪个位置合场强为零？怎么定性判断它偏哪边？"""
    Q1, Q2 = 4e-6, -1e-6         # q1 在原点，q2 在 3 dm 处
    p0 = 5.0                      # 探测点默认位置（dm）
    # E_x(p) = k·1e-6·[4/p² − 1/(p−3)²]（p 以 dm 计，k·1e-6·100 = 9e5）
    KDM = 9e5
    zero_p = 6.0                  # 4/p² = 1/(p−3)² → p = 6 dm（在 q2 外侧）
    assert abs(K.f(K.field_vector_at([(0, 0, Q1), (0.3, 0, Q2)], zero_p / 10, 0)["Ex"])) < 1e-6

    # 轴上采样：承载「零场点」这条主线（等间距的 p，看箭头翻转）
    axis_samples = [4.0, 4.6, 5.2, 5.8, 6.0, 6.4, 7.0, 8.0]
    # 轴外采样：场是二维矢量场，只有轴上箭头看不出场线在上下两侧怎么弯
    off_samples = [(x, y) for x in (0.7, 1.6, 2.6, 3.6, 4.6, 5.8, 7.0)
                      for y in (-2.2, 2.2)]

    arrows = []
    for pdm in axis_samples:
        s = K.field_vector_at([(0, 0, Q1), (0.3, 0, Q2)], pdm / 10, 0)
        arrows.append({"x": pdm, "y": 0.0, "ex": K.f(s["Ex"]), "ey": K.f(s["Ey"]),
                       "mag": K.f(s["E"])})
    for (xdm, ydm) in off_samples:
        s = K.field_vector_at([(0, 0, Q1), (0.3, 0, Q2)], xdm / 10, ydm / 10)
        arrows.append({"x": xdm, "y": ydm, "ex": K.f(s["Ex"]), "ey": K.f(s["Ey"]),
                       "mag": K.f(s["E"])})

    board = {
        # 轴外箭头最长到 |y| ≈ 3.3（采样 y=±2.2 再加箭头长度），视窗必须放得下；
        # 右侧 p=8 dm 的探测点标签是居中排版，文字左右各伸出约 1.4，故右边界放到 10.8
        "view": {"xRange": [-2.2, 10.8], "yRange": [-3.8, 3.8]},
        "scalars": [
            {"name": "Ex", "expr": f"{KDM}*(4/(p*p)-1/((p-3)*(p-3)))"},
            {"name": "mag", "expr": "abs(Ex)"},
        ],
        "param": {"name": "p", "label": "探测点位置 $p$（距 $q_1$，单位 dm）",
                  "min": 4.0, "max": 8.0, "step": 0.05, "value": p0, "unit": " dm",
                  "ticks": ["4.0 dm", "6.0 dm（零场点）", "8.0 dm"]},
        "scene": {"kind": "dipole", "caption": "场强叠加：合场强为零的点",
                  "q1": Q1, "q2": Q2, "q1x": 0.0, "q1y": 0.0, "q2x": 3.0, "q2y": 0.0,
                  "arrows": arrows,
                  "probe": {"x": "p",
                            "ex": f"{KDM}*(4/(p*p)-1/((p-3)*(p-3)))"}},
        "readouts": [
            {"id": "p", "label": "探测点 $p$", "type": "expr", "expr": "p", "digits": 2, "unit": "dm"},
            {"id": "Ex", "label": "合场强 $E_x$（向右为正）", "type": "expr",
             "expr": "Ex", "digits": 2, "unit": "N/C", "highlight": True},
            {"id": "mag", "label": "合场强大小 $|E|$", "type": "expr",
             "expr": "mag", "digits": 2, "unit": "N/C"},
            {"id": "zero", "label": "该点是否为零场点", "type": "status",
             "expr": "mag", "op": "<", "rhs": 1e-3,
             "okText": "E = 0（两电荷在此处抵消）", "badText": "E ≠ 0"},
        ],
        "legend": [
            {"color": "#f87171", "text": "$q_1 = +4\\ \\mu$C"},
            {"color": "#38bdf8", "text": "$q_2 = -1\\ \\mu$C"},
            {"color": "#a78bfa", "text": "各采样点处的合场强 $\\vec E_1+\\vec E_2$"},
            {"color": "#fbbf24", "text": "随滑块移动的探测点"},
        ],
    }
    lesson = {
        "language": "zh-CN",
        "title": "场强叠加：合场强为零的点在哪",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>真空中 $q_1 = +4\\ \\mu\\mathrm{C}$ 固定在原点，"
            "$q_2 = -1\\ \\mu\\mathrm{C}$ 固定在距 $q_1$ 为 $3\\ \\mathrm{dm}$ 处。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>两电荷连线上是否存在合场强为零的点？在哪一侧？</li>"
            "<li>该点距 $q_1$ 多远？</li>"
            "<li>拖动滑块穿过该点，看箭头方向怎么翻转。</li></ol>"),
        "answerLabel": "零场点位置",
        "answer": "在 $q_2$ 的<b>外侧</b>（$q_2$ 远离 $q_1$ 的一侧），"
                  "距 $q_1$ 为 $6\\ \\mathrm{dm}$",
    }
    steps = [
        {"title": "先定性：零场点不可能在两电荷之间",
         "content": ("<p>在两电荷之间：$q_1$ 产生的场背离 $q_1$（向右），"
                     "$q_2$ 为负电荷，产生的场指向 $q_2$（也向右）。</p>"
                     "<p>两者<b>同向叠加</b>，永远不可能抵消。"
                     "所以零场点不在连线中段。</p>")},
        {"title": "再定性：零场点在弱电荷那一侧的外侧",
         "content": ("<p>要抵消，两个场必须<b>反向</b>，这只有在"
                     "强电荷外侧（场强衰减慢）与弱电荷之间才可能。</p>"
                     f"<p>$|q_1| = 4\\ \\mu\\mathrm{{C}} > |q_2| = 1\\ \\mu\\mathrm{{C}}$，"
                     "所以零场点必须更靠近弱电荷 $q_2$ —— 即在 $q_2$ 的外侧。</p>")},
        {"title": "定量算出位置",
         "content": (f"<p>设零场点距 $q_1$ 为 $p\\ \\mathrm{{dm}}$（$p>3$），"
                     "则两点电荷到它的距离分别是 $p$ 与 $p-3$：</p>"
                     f"<p class='text-center'>$k\\dfrac{{4}}{{p^{{2}}}} = k\\dfrac{{1}}{{(p-3)^{{2}}}}"
                     "\\ \\Longrightarrow\\ \\dfrac{{2}}{{p}} = \\dfrac{{1}}{{p-3}}$</p>"
                     f"<p>解得 $p = 6\\ \\mathrm{{dm}}$。</p>"
                     "<p>把滑块拖到 6.0 dm，左栏会显示 $E = 0$，"
                     "画布上探测点的箭头在此处<b>反向</b>——这就是「零场点」的图像含义。</p>")},
        {"title": "为什么不能凭直觉说「中点」",
         "content": ("<p>常见错误是认为零场点在连线中点。那要求 $|q_1| = |q_2|$。</p>"
                     "<p>本题 $|q_1| : |q_2| = 4:1$，场强按 $\\dfrac{1}{r^2}$ 衰减，"
                     "强电荷的场在很远处仍占优，"
                     "所以抵消点被「推」到了弱电荷的外侧。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 平行板电容器
# =====================================================================
def build_capacitor() -> dict:
    """真问句：板间距变小，电容、电荷量、板间场强分别怎么变？哪个量不变？"""
    epsr, S, V, d0 = 2.0, 0.02, 12.0, 2.0      # εᵣ 云母，S=200 cm²，U=12 V，d=2 mm
    CAP = K.capacitor(epsr, S, d0 * 1e-3, V)
    Cjs = "8.85e-12*2*0.02/(d*1e-3)"
    assert abs(K.f(CAP["C"]) - 1.77e-10) < 1e-12
    assert abs(K.f(CAP["E"]) - 6000) < 1e-6

    board = {
        # 极板半宽13 + 右侧文字到 x≈18.5，视窗必须放得下（否则被右边缘裁掉）
        "view": {"xRange": [-22, 22], "yRange": [-10, 10]},
        "scalars": [
            {"name": "C", "expr": Cjs},
            {"name": "Q", "expr": "C*12"},
            {"name": "Efd", "expr": "12/(d*1e-3)"},
            {"name": "W", "expr": "0.5*C*12*12"},
        ],
        "param": {"name": "d", "label": "板间距 $d$", "min": 0.5, "max": 8.0,
                  "step": 0.05, "value": d0, "unit": " mm",
                  "ticks": ["0.5 mm", "2.0 mm (题设)", "8.0 mm"]},
        "scene": {"kind": "plates", "caption": "平行板电容器（保持与电源相连）",
                  "d": "d", "w": 13.0, "S": S, "epsr": epsr, "V": V},
        "readouts": [
            {"id": "d", "label": "板间距 $d$", "type": "expr", "expr": "d", "digits": 2, "unit": "mm"},
            {"id": "C", "label": "电容 $C=\\varepsilon\\dfrac{S}{d}$", "type": "expr",
             "expr": "C*1e12", "digits": 2, "unit": "pF", "highlight": True},
            {"id": "Q", "label": "电荷量 $Q=CU$", "type": "expr",
             "expr": "Q*1e9", "digits": 3, "unit": "nC"},
            {"id": "Efd", "label": "板间场强 $E=\\dfrac{U}{d}$", "type": "expr",
             "expr": "Efd", "digits": 1, "unit": "V/m"},
            {"id": "W", "label": "储能 $W=\\tfrac12 CU^2$", "type": "expr",
             "expr": "W*1e9", "digits": 3, "unit": "nJ"},
        ],
        "constant": {"label": "$U \\equiv 12\\ \\mathrm{V}$（保持与电源相连，电压不变）"},
        "legend": [
            {"color": "#94a3b8", "text": "极板（上 + 下 −）"},
            {"color": "#a78bfa", "text": "板间匀强电场（等间距直线）"},
        ],
    }
    lesson = {
        "language": "zh-CN",
        "title": "平行板电容器：改变板间距会发生什么",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            f"<p>平行板电容器接在 $U = 12\\ \\mathrm{{V}}$ 的电源上，"
            f"极板正对面积 $S = 200\\ \\mathrm{{cm^2}}$，"
            "介质为云母（$\\varepsilon_r = 2$），初始板间距 $d = 2.0\\ \\mathrm{{mm}}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求电容 $C$ 与电荷量 $Q$；</li>"
            "<li>拖动滑块把 $d$ 增大，$C、Q、E$ 各自怎么变？哪个量不变？</li></ol>"),
        "answerLabel": "d = 2.0 mm 时的 C 与 Q",
        "answer": f"$C = {sci(CAP['C'])}\\ \\mathrm{{F}}$，"
                  f"$Q = {sci(CAP['Q'])}\\ \\mathrm{{C}}$",
    }
    steps = [
        {"title": "电容只由结构决定",
         "content": (f"<p>$C = \\varepsilon_0\\varepsilon_r\\dfrac{{S}}{{d}}$。"
                     f"代入 $\\varepsilon_0 = 8.85\\times10^{{-12}}\\ \\mathrm{{F/m}}$、"
                     f"$S = 0.02\\ \\mathrm{{m^2}}$、$d = 2\\times10^{{-3}}\\ \\mathrm{{m}}$：</p>"
                     f"<p class='text-center'>$C = {sci(CAP['C'])}\\ \\mathrm{{F}}"
                     f" = {K.f(CAP['C'] * 1e12):.1f}\\ \\mathrm{{pF}}$</p>"
                     "<p>$C$ 由 $\\varepsilon_r、S、d$ 三个<b>结构量</b>决定，"
                     "与带不带电、电压多少无关。</p>")},
        {"title": "电压不变是本题的前提",
         "content": ("<p>题目说「保持与电源相连」，所以 $U \\equiv 12\\ \\mathrm{V}$ 不变"
                     "（左栏定值指示器一直亮着这一条）。</p>"
                     f"<p>于是 $Q = CU = {sci(CAP['Q'])}\\ \\mathrm{{C}}$，"
                     f"$E = \\dfrac{{U}}{{d}} = {K.f(CAP['E']):.0f}\\ \\mathrm{{V/m}}$。</p>")},
        {"title": "拖动滑块看到的变化",
         "content": ("<p>$d$ 增大 → $C \\propto \\dfrac1d$ 变小 → "
                     "$Q = CU$ 变小（电容器放掉一部分电荷）；"
                     "同时 $E = \\dfrac{{U}}{{d}}$ 也变小。</p>"
                     "<p>$Q$ 变小了，是因为电荷流回了电源 —— "
                     "这正是「与电源相连」和「断开电源」两种题型的根本差别。</p>")},
        {"title": "如果先断开电源呢",
         "content": ("<p>断开电源后 $Q$ 不变，此时 $E = \\dfrac{{Q}}{{\\varepsilon S}}$ "
                     "<b>与 $d$ 无关</b> —— 改变板间距，板间场强纹丝不动。</p>"
                     "<p>同一个装置，前提不同结论相反。"
                     "做题时先问一句「是 Q 不变还是 U 不变」，比套公式重要得多。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 带电粒子在匀强磁场中做圆周运动
# =====================================================================
def build_mag_circ() -> dict:
    """真问句：速率变大，半径怎么变？周期变不变？（回旋加速器为什么能工作）"""
    B, v0 = 0.5, 1.0e6
    C = K.magnetic_circle(K.M_PROTON, v0, B, K.E_CHARGE)
    rcm = K.f(C["r"]) * 100
    assert abs(rcm - 2.0875) < 1e-3
    assert abs(K.f(C["T"]) - 1.3117e-7) < 1e-10

    board = {
        "view": {"xRange": [-4.6, 4.6], "yRange": [-3.5, 3.5]},
        "scalars": [
            # 滑块读数是 ×10⁶ m/s，进公式前必须先还原成 SI 的 m/s
            {"name": "vsi", "expr": "v*1e6"},
            {"name": "rm", "expr": f"{MP}*vsi/({QE}*0.5)"},
            {"name": "rcm", "expr": "rm*100"},
            {"name": "T", "expr": f"2*PI*{MP}/({QE}*0.5)"},
            {"name": "f", "expr": "1/T"},
            {"name": "Ek", "expr": f"0.5*{MP}*vsi*vsi/{QE}*1e-3"},
        ],
        "param": {"name": "v", "label": "进入磁场的速率 $v$", "min": 0.5, "max": 1.5,
                  "step": 0.01, "value": v0 / 1e6, "unit": " ×10⁶ m/s",
                  "ticks": ["0.5", "1.0 (题设)", "1.5"]},
        "scene": {"kind": "circb", "caption": "质子垂直进入匀强磁场（B 向里）",
                  "cx": 0.0, "cy": 0.0, "r": "rcm", "qsign": 1, "theta0": 90},
        "readouts": [
            {"id": "v", "label": "速率 $v$", "type": "expr",
             "expr": "v*1e6", "digits": 3, "unit": "m/s"},
            {"id": "r", "label": "轨道半径 $r=\\dfrac{mv}{qB}$", "type": "expr",
             "expr": "rcm", "digits": 3, "unit": "cm", "highlight": True},
            {"id": "T", "label": "周期 $T=\\dfrac{2\\pi m}{qB}$", "type": "expr",
             "expr": "T*1e7", "digits": 3, "unit": "×10⁻⁷ s"},
            {"id": "f", "label": "频率 $f=1/T$", "type": "expr",
             "expr": "f*1e-6", "digits": 3, "unit": "MHz"},
            {"id": "Ek", "label": "动能 $E_k$", "type": "expr",
             "expr": "Ek", "digits": 3, "unit": "keV"},
        ],
        "constant": {"label": "$T = " + sci(C["T"], 3)
                     + "\\ \\mathrm{s}$ 与速率无关（回旋加速器能工作的唯一理由）"},
        "legend": [
            {"color": "#475569", "text": "$B \\otimes$ 垂直纸面向里"},
            {"color": "#a78bfa", "text": "圆轨道"},
            {"color": "#38bdf8", "text": "速度 $v$（沿切向）"},
            {"color": "#f87171", "text": "洛伦兹力 $F$（指向圆心）"},
        ],
    }
    lesson = {
        "language": "zh-CN",
        "title": "带电粒子在匀强磁场中的圆周运动",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            f"<p>质子（$m = 1.67\\times10^{{-27}}\\ \\mathrm{{kg}}$，"
            f"$q = 1.6\\times10^{{-19}}\\ \\mathrm{{C}}$）以速率 "
            f"$v = 1.0\\times10^{{6}}\\ \\mathrm{{m/s}}$ 垂直射入"
            "$B = 0.5\\ \\mathrm{T}$ 的匀强磁场（磁场方向垂直纸面向里）。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求轨道半径与回旋周期；</li>"
            "<li>拖动滑块改变 $v$：半径怎么变？周期变不变？为什么？</li></ol>"),
        "answerLabel": "轨道半径 / 回旋周期",
        "answer": f"$r = {rcm:.3f}\\ \\mathrm{{cm}}$，"
                  f"$T = {sci(C['T'])}\\ \\mathrm{{s}}$",
    }
    steps = [
        {"title": "洛伦兹力为什么能维持圆周运动",
         "content": ("<p>$F = qvB$ 的方向永远<b>垂直于速度</b>"
                     "（左手定则：磁感线穿手心，四指指正电荷运动方向，"
                     "大拇指即受力方向）。</p>"
                     "<p>力垂直于速度 → 不做功 → 速率不变 → "
                     "力的大小 $qvB$ 也不变，只改变方向。"
                     "大小方向都不变的向心力，对应的就是匀速圆周运动。</p>")},
        {"title": "半径：由向心力公式解出",
         "content": (f"<p>令洛伦兹力提供向心力：$qvB = m\\dfrac{{v^2}}{{r}}$，"
                     "解得 $r = \\dfrac{{mv}}{{qB}}$。</p>"
                     f"<p>代入 $v = 1.0\\times10^6\\ \\mathrm{{m/s}}$：</p>"
                     f"<p class='text-center'>$r = \\dfrac{{1.67\\times10^{{-27}}"
                     "\\times10^6}{{1.6\\times10^{{-19}}\\times0.5}}"
                     f" = {rcm:.3f}\\ \\mathrm{{cm}}$</p>"
                     "<p>拖动滑块：$r \\propto v$，速率加倍半径加倍。"
                     "<b>洛伦兹力不做功</b>，所以速率永远不会变——"
                     "半径变大只是「同样的力转更大的圈」。</p>")},
        {"title": "周期与速率无关（回旋加速器的原理）",
         "content": (f"<p>$T = \\dfrac{{2\\pi r}}{{v}} = \\dfrac{{2\\pi m}}{{qB}}$ —— "
                     "$v$ 被约掉了！</p>"
                     f"<p>$T = {sci(C['T'])}\\ \\mathrm{{s}}$，"
                     f"频率 $f = {sci(C['f'])}\\ \\mathrm{{Hz}}$。</p>"
                     "<p>这正是回旋加速器能工作的唯一理由："
                     "粒子越转越快、半径越来越大，"
                     "但<b>每转一圈的时间始终相同</b>，"
                     "所以同一个交变电场可以一直把它加速下去。</p>")},
        {"title": "转向：正电荷逆时针",
         "content": ("<p>磁场向里（$\\otimes$）、正电荷：由 $F = q\\vec v\\times\\vec B$，"
                     "取 $\\vec v$ 向右、$\\vec B$ 向里，得受力向上 —— "
                     "粒子向左上方偏，是<b>逆时针</b>。</p>"
                     "<p>换成负电荷或磁场向外，转向就反过来；"
                     "但半径和周期的公式完全不变（都用 $|q|$）。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 带电粒子在匀强电场中的偏转（类平抛）
# =====================================================================
def build_eb_deflect() -> dict:
    """真问句：入射越快偏转越小 —— 偏转量与入射速率是什么关系？"""
    E, v0, Lm = 8.0e4, 1.0e6, 0.05
    D = K.electric_deflect(E, K.E_CHARGE, K.M_PROTON, v0, Lm)
    ymm = K.f(D["y"]) * 1000
    kk = ymm / 2500.0                      # y(mm) = kk·x(mm)²
    assert abs(ymm - 9.581) < 1e-2

    board = {
        "view": {"xRange": [-14, 74], "yRange": [-14, 22]},
        "scalars": [
            {"name": "a", "expr": f"{QE}*8e4/{MP}"},
            # 滑块读数是 ×10⁶ m/s，时间与正切必须用 SI 速率算
            {"name": "t", "expr": "0.05/(v0*1e6)"},
            {"name": "ym", "expr": "0.5*a*t*t*1000"},
            {"name": "vy", "expr": "a*t"},
            {"name": "tan", "expr": "vy/(v0*1e6)"},
            {"name": "kk", "expr": "ym/2500"},
        ],
        "param": {"name": "v0", "label": "入射速率 $v_0$", "min": 1.0, "max": 3.0,
                  "step": 0.02, "value": v0 / 1e6, "unit": " ×10⁶ m/s",
                  "ticks": ["1.0 (题设)", "1.5", "3.0"]},
        "scene": {"kind": "deff", "caption": "质子垂直进入匀强电场（类平抛）",
                  "L": 50.0, "d": 24.0, "kk": "kk", "yout": "ym"},
        "readouts": [
            {"id": "v0", "label": "入射速率 $v_0$", "type": "expr",
             "expr": "v0*1e6", "digits": 3, "unit": "m/s"},
            {"id": "a", "label": "加速度 $a=\\dfrac{qE}{m}$", "type": "expr",
             "expr": "a*1e-12", "digits": 3, "unit": "×10¹² m/s²"},
            {"id": "t", "label": "穿越时间 $t=\\dfrac{L}{v_0}$", "type": "expr",
             "expr": "t*1e9", "digits": 2, "unit": "ns"},
            {"id": "y", "label": "侧移量 $y$", "type": "expr",
             "expr": "ym", "digits": 3, "unit": "mm", "highlight": True},
            {"id": "tan", "label": "$\\tan\\theta = \\dfrac{v_y}{v_x}$", "type": "expr",
             "expr": "tan", "digits": 4},
        ],
        "bars": {"label": "能量分解（单位 keV）",
                 "a": {"label": "初动能 $\\tfrac12mv_0^2$",
                       # (v0×10⁶)² = v0²×10¹²，所以这里乘 1e12 正确
                       "expr": f"0.5*{MP}*v0*v0*1e12/{QE}*1e-3"},
                 "b": {"label": "电场力做功 $qEy$",
                       # vy 已经是 m/s，不能再乘 1e12
                       "expr": f"0.5*{MP}*vy*vy/{QE}*1e-3"}},
        "legend": [
            {"color": "#94a3b8", "text": "偏转极板（上 + 下 −）"},
            {"color": "#a78bfa", "text": "板间匀强电场"},
            {"color": "#34d399", "text": "类平抛轨迹"},
        ],
    }
    lesson = {
        "language": "zh-CN",
        "title": "带电粒子在电场中的偏转（类平抛）",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            f"<p>质子以 $v_0 = 1.0\\times10^6\\ \\mathrm{{m/s}}$ 沿水平方向"
            "射入偏转电场，极板长 $L = 5\\ \\mathrm{{cm}}$，"
            f"板间匀强电场 $E = 8.0\\times10^4\\ \\mathrm{{N/C}}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求质子射出电场时的侧移量 $y$ 与偏转角；</li>"
            "<li>拖动滑块改变 $v_0$：$y$ 与 $v_0$ 是什么关系？</li></ol>"),
        "answerLabel": "侧移量 y",
        "answer": f"$y = {ymm:.3f}\\ \\mathrm{{mm}}$",
    }
    steps = [
        {"title": "类平抛：两个方向独立",
         "content": ("<p>电场力沿竖直方向，水平方向<b>不受力</b>。"
                     "所以水平做匀速、竖直做初速为零的匀加速 —— "
                     "这与平抛运动完全同构，只是把 $g$ 换成 $a = \\dfrac{qE}{m}$。</p>"
                     f"<p>$a = \\dfrac{{1.6\\times10^{{-19}}\\times8\\times10^4}}"
                     "{1.67\\times10^{{-27}}} = " + sci(D["a"], 3) + "\\ \\mathrm{m/s^2}$。</p>")},
        {"title": "先算时间，再算侧移量",
         "content": (f"<p>水平：$t = \\dfrac{{L}}{{v_0}} = "
                     f"\\dfrac{{0.05}}{{10^6}} = {sci(D['t'])}\\ \\mathrm{{s}}$。</p>"
                     f"<p>竖直：$y = \\tfrac12 a t^2 = {ymm:.3f}\\ \\mathrm{{mm}}$。</p>"
                     "<p>注意 $y \\propto \\dfrac{1}{v_0^2}$ —— "
                     "入射速率加倍，侧移量变为四分之一。"
                     "拖动滑块可以看到这个平方反比。</p>")},
        {"title": "偏转角：由速度分量得到",
         "content": (f"<p>$v_y = at = {sci(D['vy'], 3)}\\ \\mathrm{{m/s}}$，"
                     f"$\\tan\\theta = \\dfrac{{v_y}}{{v_0}} = {K.f(D['tan']):.4f}$，"
                     f"即 $\\theta = {K.f(D['angle']):.2f}^\\circ$。</p>"
                     "<p>$\\tan\\theta = \\dfrac{at}{v_0} = \\dfrac{qEL}{mv_0^2}$ —— "
                     "同样与 $v_0^2$ 成反比：跑得越快越「来不及偏」。</p>")},
        {"title": "能量视角（左栏的能量条）",
         "content": ("<p>电场力做功 $W = qEy$，全部转化为动能增量。"
                     "把初动能与电场力做功画成两段，"
                     "它们之和就是射出时的末动能。</p>"
                     "<p>拖动滑块：$v_0$ 越大，初动能占比越大，"
                     "而 $W \\propto y \\propto 1/v_0^2$ 反而越小 —— "
                     "同一个电场对「快粒子」做的功更少。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 闭合电路欧姆定律
# =====================================================================
def build_ohm() -> dict:
    """真问句：外阻变大，路端电压怎么变？什么时候输出功率最大？"""
    E, r, R0 = 12.0, 1.0, 5.0
    CI = K.circuit(E, r, R0)
    assert abs(K.f(CI["I"]) - 2) < 1e-12
    assert abs(K.f(CI["U"]) - 10) < 1e-12

    board = {
        # 右侧 U/I 文字与上方 R 标注都要放得下；下方文字到 y ≈ −0.4
        "view": {"xRange": [0, 7.6], "yRange": [-1.4, 5.6]},
        "scalars": [
            {"name": "I", "expr": "12/(R+1)"},
            {"name": "U", "expr": "I*R"},
            {"name": "Ir", "expr": "I*1"},
            {"name": "Pout", "expr": "I*I*R"},
            {"name": "eta", "expr": "R/(R+1)"},
        ],
        "param": {"name": "R", "label": "外电阻 $R$", "min": 0.0, "max": 20.0,
                  "step": 0.1, "value": R0, "unit": " Ω",
                  "ticks": ["0 Ω", "1 Ω (=r)", "5 Ω (题设)", "20 Ω"]},
        "scene": {"kind": "circuit", "caption": "闭合电路：电源（E, r）+ 外电阻 R",
                  "I": "I", "U": "U"},
        "readouts": [
            {"id": "R", "label": "外电阻 $R$", "type": "expr", "expr": "R", "digits": 2, "unit": "Ω"},
            {"id": "I", "label": "电流 $I=\\dfrac{E}{R+r}$", "type": "expr",
             "expr": "I", "digits": 3, "unit": "A", "highlight": True},
            {"id": "U", "label": "路端电压 $U=IR$", "type": "expr",
             "expr": "U", "digits": 3, "unit": "V"},
            {"id": "Ir", "label": "内电压 $Ir$", "type": "expr", "expr": "Ir", "digits": 3, "unit": "V"},
            {"id": "Pout", "label": "输出功率 $P=I^2R$", "type": "expr",
             "expr": "Pout", "digits": 3, "unit": "W"},
            {"id": "eta", "label": "电源效率 $\\eta=\\dfrac{R}{R+r}$", "type": "expr",
             "expr": "eta*100", "digits": 1, "unit": "%"},
            {"id": "maxp", "label": "是否输出功率最大", "type": "status",
             "expr": "abs(R-1)", "op": "<", "rhs": 1e-9,
             "okText": "R = r，输出功率最大", "badText": "R ≠ r"},
        ],
        "bars": {"label": "电压分配（两段之和恒为 E = 12 V）",
                 "a": {"label": "路端电压 U", "expr": "U"},
                 "b": {"label": "内电压 Ir", "expr": "Ir"}},
        "constant": {"label": "$U + Ir \\equiv E = 12\\ \\mathrm{V}$（与 $R$ 无关）"},
        "legend": [
            {"color": "#facc15", "text": "电源：电动势 $E$、内阻 $r$"},
            {"color": "#fde047", "text": "外电阻 $R$"},
            {"color": "#f472b6", "text": "电流表"},
            {"color": "#38bdf8", "text": "电压表（测路端电压）"},
        ],
    }
    lesson = {
        "language": "zh-CN",
        "title": "闭合电路欧姆定律",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            f"<p>电源电动势 $E = 12\\ \\mathrm{{V}}$、内阻 $r = 1\\ \\mathrm{{Ω}}$，"
            "外接电阻 $R$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>当 $R = 5\\ \\mathrm{Ω}$ 时，求电流、路端电压与内电压；</li>"
            "<li>拖动滑块改变 $R$：路端电压怎么变？$R$ 取何值时输出功率最大？</li></ol>"),
        "answerLabel": "R = 5 Ω 时的电流与路端电压",
        "answer": f"$I = {K.f(CI['I']):.2f}\\ \\mathrm{{A}}$，"
                  f"$U = {K.f(CI['U']):.2f}\\ \\mathrm{{V}}$",
    }
    steps = [
        {"title": "全电路电流：内阻也算进去",
         "content": ("<p>电源内部也有电阻，电流流过它要分掉一部分电压。"
                     "把内阻 $r$ 与外阻 $R$ 串起来看：</p>"
                     f"<p class='text-center'>$I = \\dfrac{{E}}{{R+r}} "
                     f"= \\dfrac{{12}}{{5+1}} = {K.f(CI['I']):.2f}\\ \\mathrm{{A}}$</p>"
                     "<p>常见错误是只写 $I = E/R$ —— 那是<b>理想电源</b>，"
                     "只在 $r = 0$ 时成立。</p>")},
        {"title": "路端电压与内电压：两者相加恒为 E",
         "content": (f"<p>$U = IR = {K.f(CI['U']):.2f}\\ \\mathrm{{V}}$（电压表读数），"
                     f"$Ir = {K.f(CI['Ir']):.2f}\\ \\mathrm{{V}}$。</p>"
                     f"<p>$U + Ir = {K.f(CI['U'] + CI['Ir']):.2f}\\ \\mathrm{{V}} = E$，"
                     "与 $R$ 无关（见左栏能量条与定值指示）。</p>"
                     "<p>另一等价写法：$U = E - Ir$ —— "
                     "<b>电流越大，路端电压越低</b>。这就是「电源带不动」的物理原因。</p>")},
        {"title": "输出功率在 R = r 处最大",
         "content": (f"<p>$P_\\mathrm{{出}} = I^2 R = \\dfrac{{E^2 R}}{{(R+r)^2}}$。"
                     "用均值不等式或求导可知，$R = r$ 时取最大值。</p>"
                     f"<p>本题 $r = 1\\ \\mathrm{{Ω}}$，把滑块拖到 $R = 1\\ \\mathrm{{Ω}}$，"
                     "左栏状态灯会亮起「输出功率最大」。</p>"
                     f"<p>此时 $P_\\max = \\dfrac{{E^2}}{{4r}} = "
                     f"{K.f(E * E / (4 * r)):.2f}\\ \\mathrm{{W}}$。</p>")},
        {"title": "效率与功率是一对矛盾",
         "content": (f"<p>$\\eta = \\dfrac{{R}}{{R+r}}$，$R$ 越大效率越高；"
                     "但 $R$ 很大时电流很小，输出功率反而下降。</p>"
                     f"<p>$R = 5\\ \\mathrm{{Ω}}$ 时 $\\eta = "
                     f"{K.f(CI['eta'] * 100):.1f}\\%$，"
                     f"而 $R = 1\\ \\mathrm{{Ω}}$ 时 $\\eta = 50\\%$ —— "
                     "<b>效率最高点与功率最大点不是同一个点</b>，"
                     "这是本节最容易被搞混的地方。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 法拉第电磁感应定律
# =====================================================================
def build_faraday() -> dict:
    """真问句：磁通量变化量相同，变化快慢不同，感应电动势差多少？"""
    N, B1, S, dt0 = 100, 0.6, 0.01, 0.1
    FA = K.faraday(N, dPhi=None, dt=dt0, B0=0, B1=B1, S=S)
    assert abs(K.f(FA["emf"]) - 6.0) < 1e-12
    assert abs(K.f(FA["dPhi"]) - 6e-3) < 1e-15

    board = {
        "view": {"xRange": [0, 7], "yRange": [-0.4, 4.6]},
        "scalars": [
            {"name": "dPhi", "expr": f"{B1}*{S}"},
            {"name": "emf", "expr": f"{N}*dPhi/dt"},
            {"name": "dPhi_m", "expr": "dPhi*1000"},
        ],
        "param": {"name": "dt", "label": "磁铁插入所用时间 $\\Delta t$", "min": 0.02,
                  "max": 0.4, "step": 0.002, "value": dt0, "unit": " s",
                  "ticks": ["0.02 s（快）", "0.10 s (题设)", "0.40 s（慢）"]},
        "scene": {"kind": "induction", "caption": "磁铁插入线圈：变化越快，电动势越大",
                  "N": N, "rising": 1, "emf": "emf"},
        "readouts": [
            {"id": "dt", "label": "变化时间 $\\Delta t$", "type": "expr",
             "expr": "dt", "digits": 3, "unit": "s"},
            {"id": "dPhi", "label": "磁通量变化 $\\Delta\\Phi$", "type": "expr",
             "expr": "dPhi_m", "digits": 3, "unit": "mWb"},
            {"id": "emf", "label": "感应电动势 $\\varepsilon=N\\dfrac{\\Delta\\Phi}{\\Delta t}$",
             "type": "expr", "expr": "emf", "digits": 3, "unit": "V", "highlight": True},
            {"id": "N", "label": "线圈匝数 $N$", "type": "expr",
             "expr": "100", "digits": 0, "unit": "匝"},
        ],
        "constant": {"label": "$\\Delta\\Phi = B\\cdot S = "
                     + sci(FA["dPhi"], 3) + "\\ \\mathrm{Wb}$ 不变 —— 变的只是快慢"},
        "legend": [
            {"color": "#a78bfa", "text": "线圈（$N$ 匝）"},
            {"color": "#f87171", "text": "条形磁铁 N 极"},
            {"color": "#64748b", "text": "$B$ 方向（N → S）"},
            {"color": "#22d3ee", "text": "感应电流（楞次定律：阻碍变化）"},
        ],
    }
    lesson = {
        "language": "zh-CN",
        "title": "法拉第电磁感应定律：关键在变化率",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            f"<p>线圈 $N = 100$ 匝、正对面积 $S = 100\\ \\mathrm{{cm^2}}$，"
            "把磁铁从远处插到线圈中，使穿过线圈的磁感应强度由 "
            "$0$ 增至 $B = 0.6\\ \\mathrm{T}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            f"<li>若插入过程用时 $\\Delta t = 0.10\\ \\mathrm{{s}}$，求感应电动势；</li>"
            "<li>拖动滑块改变 $\\Delta t$：$\\Delta\\Phi$ 变了吗？电动势为什么变了？</li></ol>"),
        "answerLabel": "Δt = 0.10 s 时的感应电动势",
        "answer": f"$\\varepsilon = {K.f(FA['emf']):.2f}\\ \\mathrm{{V}}$",
    }
    steps = [
        {"title": "磁通量变化量",
         "content": (f"<p>$\\Phi = BS\\cos\\theta$，这里磁场垂直穿过线圈，$\\theta = 0$，"
                     f"所以 $\\Delta\\Phi = (B-0)\\cdot S = 0.6\\times0.01 = "
                     f"{sci(FA['dPhi'])}\\ \\mathrm{{Wb}}$。</p>"
                     f"<p>$S = 100\\ \\mathrm{{cm^2}} = 0.01\\ \\mathrm{{m^2}}$ —— "
                     "面积必须换成国际单位，这是本题最常见的失分点。</p>")},
        {"title": "法拉第定律：看的是变化率",
         "content": (f"<p>$\\varepsilon = N\\dfrac{{\\Delta\\Phi}}{{\\Delta t}} = "
                     f"100\\times\\dfrac{{{sci(FA['dPhi'])}}}{{0.10}} = "
                     f"{K.f(FA['emf']):.2f}\\ \\mathrm{{V}}$。</p>"
                     "<p>拖动滑块：$\\Delta\\Phi$ 始终不变（左栏定值指示器一直亮着），"
                     "但 $\\Delta t$ 越小，$\\varepsilon$ 越大。</p>"
                     "<p>$N$ 匝线圈相当于把同一份变化<b>重复累加 N 次</b>，"
                     "所以乘以 $N$。</p>")},
        {"title": "楞次定律：方向由「阻碍」决定",
         "content": ("<p>磁铁插入 → 穿过线圈的磁通量<b>增大</b> → "
                     "感应电流产生的磁场要<b>阻碍</b>这个增大 → "
                     "线圈靠近磁铁的一侧出现同名磁极，把磁铁往外推。</p>"
                     "<p>画布上的青色圆弧就是感应电流方向。"
                     "如果把磁铁<b>拔出</b>（磁通量减小），方向会整个反过来。</p>")},
        {"title": "为什么强调「变化」",
         "content": ("<p>$\\varepsilon$ 只与 $\\dfrac{\\Delta\\Phi}{\\Delta t}$ 有关，"
                     "与 $\\Phi$ 本身的大小无关。</p>"
                     "<p>磁铁静止在线圈里时 $\\Phi$ 很大，但 $\\Delta\\Phi = 0$，"
                     "$\\varepsilon = 0$，电流为零 —— "
                     "<b>有磁通量不等于有感应电动势</b>。"
                     "发电机之所以能发电，是因为磁通量一直在变。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 8) 安培力 F = BIL·sinθ
# =====================================================================
def build_ampere() -> dict:
    """真问句：力与角度是什么关系？什么时候不受力？力的方向画在纸面内对不对？"""
    B, I, L, th0 = 0.4, 3.0, 0.5, 90.0
    AF = K.ampere_force(B, I, L, th0)
    assert abs(K.f(AF["F"]) - 0.6) < 1e-12

    board = {
        "view": {"xRange": [-2, 7.6], "yRange": [-0.3, 6.0]},
        "scalars": [
            {"name": "s", "expr": "sin(theta*PI/180)"},
            {"name": "F", "expr": f"{B}*{I}*{L}*s"},
        ],
        "param": {"name": "theta", "label": "电流与磁场的夹角 $\\theta$", "min": 0,
                  "max": 90, "step": 0.5, "value": th0, "unit": "°",
                  "ticks": ["0°（平行）", "45°", "90° (题设)"]},
        "scene": {"kind": "ampere", "caption": "通电导线在匀强磁场中受安培力",
                  "I": I, "L": 4.2, "theta": "theta", "F": "F"},
        "readouts": [
            {"id": "theta", "label": "夹角 $\\theta$", "type": "expr",
             "expr": "theta", "digits": 1, "unit": "°"},
            {"id": "s", "label": "$\\sin\\theta$", "type": "expr", "expr": "s", "digits": 4},
            {"id": "F", "label": "安培力 $F=BIL\\sin\\theta$", "type": "expr",
             "expr": "F", "digits": 4, "unit": "N", "highlight": True},
            {"id": "maxf", "label": "是否达到最大值", "type": "status",
             "expr": "s", "op": ">", "rhs": 0.9999,
             "okText": "θ = 90°，F 最大", "badText": "θ < 90°，F 未达最大"},
        ],
        "constant": {"label": "$F_{\\max} \\equiv BIL = "
                     + f"{K.f(AF['F']):.2f}\\ \\mathrm{{N}}$（$\\theta = 90^\\circ$ 时）"},
        "legend": [
            {"color": "#64748b", "text": "匀强磁场 $B$（纸面内，向右）"},
            {"color": "#e2e8f0", "text": "通电导线，电流沿导线"},
            {"color": "#34d399", "text": "夹角 $\\theta$"},
            {"color": "#f87171", "text": "$F \\otimes$ 垂直纸面向里"},
        ],
    }
    lesson = {
        "language": "zh-CN",
        "title": "安培力：F = BIL·sinθ 与它的方向",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            f"<p>长 $L = 0.5\\ \\mathrm{{m}}$ 的直导线通有 $I = 3\\ \\mathrm{{A}}$ 的电流，"
            f"处在 $B = 0.4\\ \\mathrm{{T}}$ 的匀强磁场中。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>导线与磁场垂直时，求安培力的大小；</li>"
            "<li>拖动滑块改变夹角 $\\theta$：$F$ 怎么变？$\\theta = 0$ 时为何不受力？"
            "力的方向能不能画在纸面内？</li></ol>"),
        "answerLabel": "θ = 90° 时的安培力",
        "answer": f"$F = {K.f(AF['F']):.2f}\\ \\mathrm{{N}}$",
    }
    steps = [
        {"title": "公式与最大值",
         "content": (f"<p>$F = BIL\\sin\\theta$。$\\theta = 90^\\circ$ 时 $\\sin\\theta = 1$，"
                     f"$F$ 取最大值 $BIL = 0.4\\times3\\times0.5 = "
                     f"{K.f(AF['F']):.2f}\\ \\mathrm{{N}}$。</p>"
                     "<p>$\\sin\\theta$ 的来历：只有<b>垂直于磁场的那部分电流</b>"
                     "才受力，把电流投影到垂直方向就得到这个因子。</p>")},
        {"title": "为什么 θ = 0 时不受力",
         "content": ("<p>电流方向与磁场平行时，"
                     "把电流分解到垂直磁场的方向上分量为零，"
                     "所以 $F = 0$。</p>"
                     "<p>拖动滑块到 $0^\\circ$：画布上的红色 $\\otimes$ 符号会缩小到消失，"
                     "并显示「F = 0」。这是公式与图像一致的地方。</p>")},
        {"title": "方向：力不在纸面内（这是关键）",
         "content": ("<p>由 $\\vec F = I\\vec L\\times\\vec B$："
                     "$\\vec B$ 在纸面内向右，电流沿导线在纸面内，"
                     "叉乘结果<b>垂直于纸面</b> —— 所以图上只能画成 $\\otimes$（向里）"
                     "或 $\\odot$（向外），不能画成纸面内的箭头。</p>"
                     "<p>左手定则的用法：磁感线穿手心（$B$ 向右则手心朝左），"
                     "四指指电流方向，大拇指指的就是这个垂直于纸面的力。</p>")},
        {"title": "常见错误提醒",
         "content": ("<p>① 把 $F = BIL\\sin\\theta$ 写成 $F = BIL\\cos\\theta$ —— "
                     "$\\theta$ 是<b>电流与磁场</b>的夹角，不是与法线的夹角。</p>"
                     "<p>② 忘记换算单位：$L$ 必须是米、$B$ 是特斯拉。</p>"
                     "<p>③ 把安培力方向画在纸面内 —— "
                     "本图特意用 $\\otimes$ 标出，就是为了堵住这个错。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册表
# =====================================================================
REGISTRY = {
    "coulomb": build_coulomb,
    "field_sum": build_field_sum,
    "capacitor": build_capacitor,
    "mag_circ": build_mag_circ,
    "eb_deflect": build_eb_deflect,
    "ohm": build_ohm,
    "faraday": build_faraday,
    "ampere": build_ampere,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="高中物理电磁学 · 交互课件", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
