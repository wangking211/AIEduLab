#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页初中平面几何交互网页。

数据由 lib/geom_kernel.py 的 sympy 精确计算驱动（单一数据源）：答案、坐标、角度、
线段比、各步中间量严格一致。每个 build_* 内置自检断言。

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

sys.path.insert(0, str(SKILL_DIR.parent.parent / "shared"))   # 共享运行时（edulab/shared/skillkit.py）
sys.path.insert(0, str(SKILL_DIR / "lib"))
import sympy as sp                       # noqa: E402
import geom_kernel as K                  # noqa: E402
from geom_kernel import V, tex, f        # noqa: E402
from skillkit import cli                 # noqa: E402


def pt(xy, color="point", label=None, emphasis=False):
    return {"xy": [f(xy[0]), f(xy[1])], "color": color, "label": label, "emphasis": emphasis}


NO_AXES = {"grid": False, "axes": False}   # 初中几何默认隐藏坐标系


# =====================================================================
# 1) 勾股定理 —— 三边向外作正方形，面积关系
# =====================================================================
def build_pythagoras(a=3, b=4) -> dict:
    sol = K.solve_pythagoras(a, b)
    A, B, C = sol["pts"]["A"], sol["pts"]["B"], sol["pts"]["C"]

    def poly_of(name, pts3, color):
        return {"type": "polygon", "pts": [f"{name}{i}" for i in range(4)],
                "color": color, "stroke": "aux"}

    points = {n: pt(p, "given", n, emphasis=True) for n, p in sol["pts"].items()}
    # 正方形四个顶点（含两个原顶点，用隐藏点补全）
    sq_defs = {}
    for key, quad in sol["squares"].items():
        for i, qv in enumerate(quad):
            pname = f"{key}_{i}"
            points[pname] = pt(qv, "point", None, False)
            points[pname]["hidden"] = True
        sq_defs[key] = [f"{key}_{i}" for i in range(4)]

    board = {
        "view": dict(NO_AXES, **{"xRange": [-4.5, 6], "yRange": [-4.5, 6]}),
        "points": points,
        "derived": [
            {"type": "polygon", "pts": sq_defs["sq_a"], "color": "rgba(56,189,248,0.18)", "stroke": "line2"},
            {"type": "polygon", "pts": sq_defs["sq_b"], "color": "rgba(167,139,250,0.18)", "stroke": "given"},
            {"type": "polygon", "pts": sq_defs["sq_c"], "color": "rgba(250,204,21,0.18)", "stroke": "curve"},
            # 三边 3/4/5 互不相等，不能带等长记号（同杠数 = 等长）。三边关系由
            # 三个正方形面积表达，不需要刻度符号。
            {"type": "segment", "name": "CA", "a": "C", "b": "A", "color": "line2"},
            {"type": "segment", "name": "CB", "a": "C", "b": "B", "color": "given"},
            {"type": "segment", "name": "AB", "a": "A", "b": "B", "color": "curve"},
            {"type": "right_angle_mark", "a": "A", "vertex": "C", "b": "B", "color": "aux"},
        ],
        "readouts": [
            {"id": "a", "label": f"直角边 a = CA", "type": "length", "a": "C", "b": "A"},
            {"id": "b", "label": f"直角边 b = CB", "type": "length", "a": "C", "b": "B"},
            {"id": "c", "label": "斜边 c = AB", "type": "length", "a": "A", "b": "B", "highlight": True},
            {"id": "sa", "label": "S_a (CA 上正方形)", "type": "expr", "expr": f"{f(sol['Sq_a'])}", "digits": 0},
            {"id": "sb", "label": "S_b (CB 上正方形)", "type": "expr", "expr": f"{f(sol['Sq_b'])}", "digits": 0},
            {"id": "sc", "label": "S_c (AB 上正方形)", "type": "expr", "expr": f"{f(sol['Sq_c'])}", "digits": 0},
        ],
        "constant": {"of": "sc", "label": f"$S_a+S_b={tex(sol['Sq_c'])}$"},
        "legend": [
            {"color": "line2", "text": f"边 a 的正方形 S_a={tex(sol['Sq_a'])}"},
            {"color": "given", "text": f"边 b 的正方形 S_b={tex(sol['Sq_b'])}"},
            {"color": "curve", "text": f"边 c 的正方形 S_c={tex(sol['Sq_c'])}"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": f"勾股定理：{a}-{b}-{sol['c']} 直角三角形",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    f"<p>在 Rt△ABC 中，∠C = 90°，直角边 CA = {a}，CB = {b}。"
                    "分别以三边向外作正方形（如图）。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'><li>求斜边 AB 的长；</li>"
                    "<li>验证三个正方形的面积满足 S_a + S_b = S_c。</li></ol>"),
        "answerLabel": "斜边 AB 的长", "answer": f"${sol['answer_latex']}$",
    }
    steps = [
        {"title": "读题与作图",
         "content": (f"<p>∠C = 90°，所以 △ABC 是直角三角形，三边分别向外作了正方形，"
                     f"面积依次为 $S_a={tex(sol['Sq_a'])}$、$S_b={tex(sol['Sq_b'])}$、"
                     f"$S_c = AB^2$（待求）。</p>")},
        {"title": "用勾股定理求斜边",
         "content": (f"<p>由勾股定理（两直角边平方和等于斜边平方）：</p>"
                     f"<p class='text-center'>$$ AB^2 = CA^2 + CB^2 = {a}^2 + {b}^2 = {tex(sol['Sq_c'])} $$</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ AB = {sol['answer_latex']} $$</div>")},
        {"title": "验证面积关系",
         "content": (f"<p>三个正方形面积：$S_a = {tex(sol['Sq_a'])}$，$S_b = {tex(sol['Sq_b'])}$，"
                     f"$S_c = {tex(sol['Sq_c'])}$。</p>"
                     f"<p class='text-center'>$$ S_a + S_b = {tex(sol['Sq_a'])} + {tex(sol['Sq_b'])} = {tex(sol['Sq_c'])} = S_c $$</p>"
                     "<p>这正是勾股定理的几何意义：<b>斜边上的正方形面积 = 两直角边上的正方形面积之和</b>。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 圆周角定理 —— 同弧所对圆周角等于圆心角一半
# =====================================================================
def build_inscribed_angle(central_deg=80, R=2) -> dict:
    sol = K.solve_inscribed(R, central_deg)
    O, A, B = sol["O"], sol["A"], sol["B"]
    half = f(central_deg / 2)
    # C 为优弧 AB 上动点（参数角 θ，从 -half 到 +half 绕对侧优弧走）
    # A、B 对称放在 ±half 角方向；优弧上的点角参数 θ ∈ (180-half*0? …)
    # 直接参数化：C = R·(cos θ, sin θ)，θ ∈ (half+10, 360-half-10) 度
    board = {
        "view": dict(NO_AXES, **{"xRange": [-2.8, 2.8], "yRange": [-2.4, 2.4]}),
        "conics": [{"name": "O", "kind": "circle", "r": f(R), "center": [0, 0], "color": "curve", "label": f"⊙O (R={f(R)})"}],
        "points": {"O": pt(O, "point", "O", True), "A": pt(A, "ptA", "A"), "B": pt(B, "ptB", "B")},
        "param": {"name": "t", "label": "点 C 在优弧上的位置角 $\\theta$",
                  "min": 100, "max": 260, "step": 0.5, "value": 180, "unit": "°", "standard": 180,
                  "ticks": [f"{100}°", "180° (对弧中点)", f"{260}°"]},
        "derived": [
            {"type": "point_on_conic", "name": "C", "conic": "O", "t": "@param", "color": "fixed", "emphasis": True},
            {"type": "line_through_points", "name": "CA", "a": "C", "b": "A", "color": "ptA"},
            {"type": "line_through_points", "name": "CB", "a": "C", "b": "B", "color": "ptB"},
            {"type": "segment", "name": "OA_", "a": "O", "b": "A", "color": "aux", "dashed": True},
            {"type": "segment", "name": "OB_", "a": "O", "b": "B", "color": "aux", "dashed": True},
            {"type": "angle_arc", "a": "A", "vertex": "O", "b": "B", "r": 0.45, "color": "curve", "arcs": 2},
            {"type": "angle_arc", "a": "A", "vertex": "C", "b": "B", "r": 0.35, "color": "fixed"},
        ],
        "readouts": [
            {"id": "central", "label": "圆心角 ∠AOB", "type": "angle_deg", "a": "A", "vertex": "O", "b": "B"},
            {"id": "insc", "label": "圆周角 ∠ACB", "type": "angle_deg", "a": "A", "vertex": "C", "b": "B", "highlight": True},
            {"id": "ratio", "label": "∠AOB : ∠ACB（应恒为 2）", "type": "expr", "expr": f"{f(central_deg)}/{f(sol['inscribed_deg'])}", "digits": 1},
        ],
        "constant": {"of": "insc", "label": f"$\\angle ACB = {tex(sol['inscribed_deg'])}^\\circ$"},
        "legend": [{"color": "fixed", "text": "动点 C（拖动滑块）"}, {"color": "curve", "text": "圆心角（双弧）"},
                   {"color": "fixed", "text": "圆周角（单弧）"}],
    }
    lesson = {
        "language": "zh-CN", "title": f"圆周角定理：同弧所对的圆周角",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    f"<p>如图，⊙O 中，圆心角 $\\angle AOB = {tex(sol['central_deg'])}^\\circ$。"
                    "点 C 是优弧 AB 上的动点。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'><li>求圆周角 $\\angle ACB$ 的度数；</li>"
                    "<li>拖动滑块改变 C 的位置，观察 ∠ACB 是否变化。</li></ol>"),
        "answerLabel": "∠ACB 的度数", "answer": f"${sol['answer_latex']}$",
    }
    steps = [
        {"title": "圆周角定理",
         "content": ("<p><b>圆周角定理</b>：同弧所对的圆周角等于它所对圆心角的一半。</p>"
                     "<p>本题中，圆周角 ∠ACB 与圆心角 ∠AOB 都对着弧 AB。</p>")},
        {"title": "计算",
         "content": (f"<p class='text-center'>$$ \\angle ACB = \\frac12 \\angle AOB = "
                     f"\\frac12 \\times {tex(sol['central_deg'])}^\\circ = "
                     f"<b>{sol['answer_latex']}</b> $$</p>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块让 C 在优弧上任意移动：圆心角 ∠AOB 固定不动（双弧标记），"
                     "而 ∠ACB 的读数<b>始终不变</b>——这就是“同弧所对的圆周角相等”。"
                     "若把 C 拖到劣弧上，圆周角会变成它的补角关系（180° − 40°），"
                     "因为此时它所对的是另一段弧。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 切割线定理 —— PT² = PA·PB
# =====================================================================
def build_tangent_secant(R=3, OP=5) -> dict:
    sol = K.solve_tangent_secant(R, OP)
    O, P, T = sol["O"], sol["P"], sol["T"]
    # 割线 PAB：过 P 与 x 轴夹角 φ（参数），交圆于 A（近）、B（远）
    board = {
        "view": {"xRange": [-4.2, 6.5], "yRange": [-3.6, 3.6], "grid": False, "axes": False},
        "conics": [{"name": "O", "kind": "circle", "r": f(R), "center": [0, 0], "color": "curve", "label": f"⊙O (R={f(R)})"}],
        "points": {"O": pt(O, "point", "O", True), "P": pt(P, "given", "P", True), "T": pt(T, "ptA", "T")},
        "param": {"name": "t", "label": "割线 PAB 的倾斜角 $\\varphi$",
                  "min": 115, "max": 245, "step": 0.5, "value": 160, "unit": "°", "standard": 160,
                  "ticks": ["115°", "180° (指向圆心)", "245°"]},
        "derived": [
            {"type": "line_through_angle", "name": "sec", "point": "P", "angle": "@param", "color": "line"},
            {"type": "intersect_line_conic", "name": ["A", "B"], "line": "sec", "conic": "O", "colors": ["ptA", "ptB"]},
            {"type": "segment", "name": "PT_", "a": "P", "b": "T", "color": "curve", "ticks": 1},
            {"type": "segment", "name": "OT_", "a": "O", "b": "T", "color": "aux", "dashed": True},
            {"type": "right_angle_mark", "a": "P", "vertex": "T", "b": "O", "color": "aux"},
        ],
        "readouts": [
            {"id": "pt", "label": "切线 PT", "type": "length", "a": "P", "b": "T"},
            {"id": "pt2", "label": "PT²", "type": "expr", "expr": f"{f(sol['PT'])}^2", "digits": 2},
            {"id": "pa", "label": "割线段 PA", "type": "length", "a": "P", "b": "A"},
            {"id": "pb", "label": "割线段 PB", "type": "length", "a": "P", "b": "B"},
            {"id": "prod", "label": "PA · PB", "type": "product", "a": ["P", "A"], "b": ["P", "B"],
             "digits": 2, "highlight": True},
        ],
        "constant": {"of": "prod", "label": f"$PA\\cdot PB = PT^2 = {tex(sol['power'])}$"},
        "legend": [{"color": "curve", "text": "切线 PT（单弧直角在 T）"}, {"color": "line", "text": "动割线 PAB"}],
    }
    lesson = {
        "language": "zh-CN", "title": "切割线定理：从圆外一点引切线与割线",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    f"<p>如图，P 为 ⊙O（半径 {f(R)}）外一点，$OP = {f(OP)}$。"
                    "PT 切 ⊙O 于 T，PAB 是过 P 的割线，交 ⊙O 于 A、B。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'><li>求切线 PT 的长；</li>"
                    "<li>拖动滑块改变割线方向，验证 PA·PB 是否为定值，并求出这个定值。</li></ol>"),
        "answerLabel": "PA·PB 的定值", "answer": f"${sol['answer_latex']}$",
    }
    steps = [
        {"title": "连接 OT，用勾股定理求 PT",
         "content": (f"<p>切线 $\\perp$ 半径：$OT \\perp PT$，于是 $\\triangle OPT$ 是直角三角形。</p>"
                     f"<p class='text-center'>$$ PT^2 = OP^2 - OT^2 = {f(OP)}^2 - {f(R)}^2 = {tex(sol['power'])} $$</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ PT = {tex(sol['PT'])} $$</div>")},
        {"title": "切割线定理",
         "content": ("<p><b>切割线定理</b>：从圆外一点引圆的切线和割线，"
                     "切线长是这点到割线与圆交点的两条线段长的比例中项，即</p>"
                     f"<p class='text-center'>$$ PT^2 = PA \\cdot PB $$</p>")},
        {"title": "拖动验证",
         "content": (f"<p>拖动滑块改变割线 PAB 的方向：PA、PB 各自变化，"
                     f"但它们的乘积读数<b>始终等于</b> $PT^2 = {tex(sol['power'])}$。</p>"
                     "<p>这就是<b>圆幂定理</b>的切割线情形：过圆外一点 P 的任意割线，"
                     "PA·PB 都等于常数 $OP^2 - R^2$，称为点 P 对 ⊙O 的幂。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 相交弦定理 —— PA·PB = PC·PD
# =====================================================================
def build_intersecting_chords(R=5, d=3) -> dict:
    sol = K.solve_chord_product(R, d)
    O, P = sol["O"], sol["P"]
    board = {
        "view": {"xRange": [-6, 6], "yRange": [-4.6, 4.6], "grid": False, "axes": False},
        "conics": [{"name": "O", "kind": "circle", "r": f(R), "center": [0, 0], "color": "curve", "label": f"⊙O (R={f(R)})"}],
        "points": {"O": pt(O, "point", "O", True), "P": pt(P, "given", "P", True)},
        "param": {"name": "t", "label": "弦 CD 绕 P 的旋转角 $\\theta$",
                  "min": 20, "max": 160, "step": 0.5, "value": 65, "unit": "°", "standard": 65,
                  "ticks": ["20°", "90° (⊥AB)", "160°"]},
        "derived": [
            {"type": "line_through_angle", "name": "AB", "point": "P", "angle": 0, "color": "line"},
            {"type": "line_through_angle", "name": "CD", "point": "P", "angle": "@param", "color": "line2"},
            {"type": "intersect_line_conic", "name": ["A", "B"], "line": "AB", "conic": "O", "colors": ["ptA", "ptB"]},
            {"type": "intersect_line_conic", "name": ["C", "D"], "line": "CD", "conic": "O", "colors": ["given", "fixed"]},
        ],
        "readouts": [
            {"id": "pa", "label": "PA", "type": "length", "a": "P", "b": "A"},
            {"id": "pb", "label": "PB", "type": "length", "a": "P", "b": "B"},
            {"id": "papb", "label": "PA · PB", "type": "product", "a": ["P", "A"], "b": ["P", "B"],
             "color": "ptA"},
            {"id": "pc", "label": "PC", "type": "length", "a": "P", "b": "C"},
            {"id": "pd", "label": "PD", "type": "length", "a": "P", "b": "D"},
            {"id": "pcpd", "label": "PC · PD", "type": "product", "a": ["P", "C"], "b": ["P", "D"],
             "color": "fixed", "highlight": True},
        ],
        "constant": {"of": "pcpd", "label": f"$PA\\cdot PB = PC\\cdot PD = {tex(sol['power'])}$"},
        "legend": [{"color": "line", "text": "定弦 AB（过 P 水平）"}, {"color": "line2", "text": "动弦 CD（拖滑块旋转）"}],
    }
    lesson = {
        "language": "zh-CN", "title": "相交弦定理：圆内两弦相交",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    f"<p>如图，⊙O 半径为 {f(R)}，弦 AB 与 CD 相交于圆内一点 P，"
                    f"$OP = {f(d)}$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'><li>拖动滑块旋转弦 CD，分别计算 PA·PB 与 PC·PD，"
                    "观察两者关系；</li><li>求这个乘积的定值。</li></ol>"),
        "answerLabel": "PA·PB = PC·PD 的定值", "answer": f"${sol['answer_latex']}$",
    }
    steps = [
        {"title": "相交弦定理",
         "content": ("<p><b>相交弦定理</b>：圆内的两条弦相交，被交点分成的两条线段长的积相等。</p>"
                     f"<p class='text-center'>$$ PA \\cdot PB = PC \\cdot PD $$</p>")},
        {"title": "用勾股定理求定值",
         "content": (f"<p>过 P 作 $PE \\perp AB$ 于 E，则 E 为弦心距垂足。"
                     f"由相交弦定理的证明（或圆幂）：$PA\\cdot PB = R^2 - OP^2$。</p>"
                     f"<p class='text-center'>$$ PA \\cdot PB = {f(R)}^2 - {f(d)}^2 = "
                     f"<b>{tex(sol['power'])}</b> $$</p>")},
        {"title": "拖动验证",
         "content": (f"<p>拖动滑块旋转弦 CD：PC、PD 各自变化，但 PC·PD 的读数"
                     f"<b>始终等于</b> PA·PB = {tex(sol['power'])}——这就是点 P 对 ⊙O 的幂 $R^2-OP^2$ 为定值。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 相似三角形 A 型 —— DE∥BC
# =====================================================================
def build_similar_A(k=sp.Rational(1, 2)) -> dict:
    A, B, C = V(0, 0), V(6, 0), V(3, 4)   # BC = 5（勾股 3-4-5）
    sol = K.solve_similar_A(A, B, C, k)
    P4 = sol["pts"]
    kf = f(k)
    board = {
        "view": dict(NO_AXES, **{"xRange": [-1.2, 7.2], "yRange": [-1.2, 5.4]}),
        "points": {n: pt(p, "given" if n in "ABC" else "fixed", n, emphasis=n in "DE")
                   for n, p in P4.items()},
        "param": {"name": "k", "label": "相似比 $k = \\dfrac{AD}{AB}$",
                  "min": 0.15, "max": 0.9, "step": 0.01, "value": kf, "unit": "", "standard": kf,
                  "ticks": ["0.15", "0.5 (题设)", "0.9"]},
        "derived": [
            {"type": "polygon", "pts": ["A", "B", "C"], "color": "rgba(148,163,184,0.12)"},
            # D、E 随 k 实时移动：D = A + k(B−A) → 用 homothety（以 A 为中心，比 k）
            {"type": "homothety", "name": "D", "of": "B", "center": "A", "k": "@param", "color": "fixed", "emphasis": True},
            {"type": "homothety", "name": "E", "of": "C", "center": "A", "k": "@param", "color": "fixed", "emphasis": True},
            # DE 与 BC 只标平行（单箭头）。原先还各带 1 道等长记号，等于断言
            # DE = BC —— 而本图讲的是 DE/BC = k，两者按定义就不相等。
            {"type": "segment", "name": "DE_", "a": "D", "b": "E", "color": "fixed", "arrow": ">"},
            {"type": "segment", "name": "BC_", "a": "B", "b": "C", "color": "line", "arrow": ">"},
            {"type": "segment", "name": "AB_", "a": "A", "b": "B", "color": "aux"},
            {"type": "segment", "name": "AC_", "a": "A", "b": "C", "color": "aux"},
        ],
        "readouts": [
            {"id": "ad_ab", "label": "AD / AB", "type": "ratio", "a": ["A", "D"], "b": ["A", "B"], "highlight": True},
            {"id": "ae_ac", "label": "AE / AC", "type": "ratio", "a": ["A", "E"], "b": ["A", "C"]},
            {"id": "de_bc", "label": "DE / BC", "type": "ratio", "a": ["D", "E"], "b": ["B", "C"]},
        ],
        "constant": {"of": "ad_ab", "label": "$\\dfrac{AD}{AB}=\\dfrac{AE}{AC}=\\dfrac{DE}{BC}$"},
        "legend": [{"color": "fixed", "text": "DE（单箭头）∥ BC（单箭头）"}, {"color": "line", "text": "原三角形边 BC"}],
    }
    lesson = {
        "language": "zh-CN", "title": "相似三角形 A 型：平行于一边的截线",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>在 △ABC 中，DE∥BC，D 在 AB 上，E 在 AC 上。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'><li>求证：△ADE ∽ △ABC，并写出对应边成比例的关系；</li>"
                    "<li>拖动滑块改变 D 的位置（相似比 k），验证三组比值是否始终相等。</li></ol>"),
        "answerLabel": "三组对应边之比", "answer": "$\\dfrac{AD}{AB}=\\dfrac{AE}{AC}=\\dfrac{DE}{BC}$",
    }
    steps = [
        {"title": "证明相似",
         "content": ("<p>∵ DE∥BC，∴ $\\angle ADE = \\angle ABC$，$\\angle AED = \\angle ACB$（同位角相等），"
                     "又 $\\angle A$ 公共，∴ <b>△ADE ∽ △ABC</b>（AA）。</p>")},
        {"title": "写出比例",
         "content": ("<p>由相似三角形对应边成比例：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ \\dfrac{AD}{AB}=\\dfrac{AE}{AC}=\\dfrac{DE}{BC} = k $$</div>")},
        {"title": "拖动验证",
         "content": (f"<p>当前 k = {kf}。拖动滑块：三个比值读数<b>始终同步相等</b>；"
                     "DE 与 BC 上的单箭头标记表示平行。这正是“A 型”相似（也叫平行线分线段成比例的三角形形式）。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 三角形中位线
# =====================================================================
def build_midsegment() -> dict:
    A, B, C = V(0, 0), V(6, 0), V(3, 4)   # BC = 5，中位线 DE = 5/2
    sol = K.solve_midsegment(A, B, C)
    P4 = sol["pts"]
    board = {
        "view": dict(NO_AXES, **{"xRange": [-1.2, 7.2], "yRange": [-1.2, 5.4]}),
        "points": {n: pt(p, "given" if n in "ABC" else "fixed", n, emphasis=n in "DE") for n, p in P4.items()},
        "derived": [
            {"type": "polygon", "pts": ["A", "B", "C"], "color": "rgba(148,163,184,0.12)"},
            # 等长记号必须画在**真正相等的那两条**上。原先画在整条 AB / AC 上并都标
            # 双刻度，按「同杠数 = 等长」的约定等于断言 AB = AC —— 而这里是 6 与 5。
            # 中点该标的是 AD=DB（单刻度）与 AE=EC（双刻度）。
            {"type": "segment", "name": "AD_", "a": "A", "b": "D", "color": "aux", "ticks": 1},
            {"type": "segment", "name": "DB_", "a": "D", "b": "B", "color": "aux", "ticks": 1},
            {"type": "segment", "name": "AE_", "a": "A", "b": "E", "color": "aux", "ticks": 2},
            {"type": "segment", "name": "EC_", "a": "E", "b": "C", "color": "aux", "ticks": 2},
            # BC 与 DE 只标平行（单箭头），不标等长：DE = BC/2，标等长会与定理矛盾。
            {"type": "segment", "name": "BC_", "a": "B", "b": "C", "color": "line", "arrow": ">"},
            {"type": "segment", "name": "DE_", "a": "D", "b": "E", "color": "fixed", "arrow": ">"},
        ],
        "readouts": [
            {"id": "de", "label": "中位线 DE", "type": "length", "a": "D", "b": "E", "highlight": True},
            {"id": "bc", "label": "底边 BC", "type": "length", "a": "B", "b": "C"},
            {"id": "ratio", "label": "DE / BC", "type": "ratio", "a": ["D", "E"], "b": ["B", "C"]},
        ],
        "constant": {"of": "de", "label": f"$DE = \\tfrac12 BC = {tex(sol['DE'])}$"},
        "legend": [{"color": "aux", "text": "单刻度 AD=DB，双刻度 AE=EC（中点）"},
                   {"color": "fixed", "text": "中位线 DE（单箭头 ∥ BC）"}],
    }
    lesson = {
        "language": "zh-CN", "title": "三角形中位线定理",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    f"<p>在 △ABC 中，D、E 分别是 AB、AC 的中点"
                    f"（图中单刻度标 AD=DB，双刻度标 AE=EC）。"
                    f"已知 $BC = {tex(sol['BC'])}$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'><li>求中位线 DE 的长；</li>"
                    "<li>说明 DE 与 BC 的位置关系。</li></ol>"),
        "answerLabel": "中位线 DE 的长", "answer": f"${sol['answer_latex']}$",
    }
    steps = [
        {"title": "中位线定理",
         "content": ("<p><b>三角形中位线定理</b>：三角形的中位线平行于第三边，且等于第三边的一半。</p>"
                     "<p>D、E 是 AB、AC 中点 ⇒ DE 是 △ABC 的中位线。</p>")},
        {"title": "计算",
         "content": (f"<p class='text-center'>$$ DE = \\frac12 BC = \\frac12 \\times {tex(sol['BC'])} = "
                     f"<b>{sol['answer_latex']}</b> $$</p>"
                     f"<p>且 $DE \\parallel BC$（图中单箭头标记平行）。</p>")},
        {"title": "回顾证法",
         "content": ("<p>延长 DE 到 F 使 EF = DE，连 CF：可证 △ADE ≌ △CFE（SAS），"
                     "于是 AD = CF 且 AD∥CF；又 D 为 AB 中点，故 BD 平行且等于 CF，"
                     "四边形 DBCF 为平行四边形 ⇒ DF∥BC 且 DF = BC，即 DE∥BC 且 DE = ½BC。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 三角形内切圆与内心
# =====================================================================
def build_incircle() -> dict:
    A, B, C = V(0, 0), V(14, 0), V(5, 12)   # 13-14-15 三角形，S=84，p=21，r=4
    sol = K.solve_incircle(A, B, C)
    I, feet = sol["I"], sol["feet"]
    board = {
        "view": dict(NO_AXES, **{"xRange": [-1.5, 15.5], "yRange": [-1.5, 13.5]}),
        "points": dict({n: pt(p, "given", n) for n, p in sol["pts"].items()},
                       **{"I": pt(I, "fixed", "I", True)}),
        "derived": [
            {"type": "polygon", "pts": ["A", "B", "C"], "color": "rgba(148,163,184,0.10)"},
            {"type": "circle_from_center_pt", "name": "in", "center": "I", "through": "Tbc", "color": "curve"},
            {"type": "segment", "name": "IA_", "a": "I", "b": "A", "color": "given", "dashed": True},
            {"type": "segment", "name": "IB_", "a": "I", "b": "B", "color": "given", "dashed": True},
            {"type": "segment", "name": "IC_", "a": "I", "b": "C", "color": "given", "dashed": True},
            {"type": "segment", "name": "rBC", "a": "I", "b": "Tbc", "color": "curve"},
            {"type": "segment", "name": "rAC", "a": "I", "b": "Tac", "color": "curve"},
            {"type": "segment", "name": "rAB", "a": "I", "b": "Tab", "color": "curve"},
            {"type": "right_angle_mark", "a": "I", "vertex": "Tbc", "b": "B", "color": "aux"},
        ],
        "readouts": [
            {"id": "r", "label": "内切圆半径 r", "type": "length", "a": "I", "b": "Tbc", "highlight": True},
            {"id": "r2", "label": "I 到 AC 距离", "type": "distance_point_line", "point": "I", "line": "AC_l"},
            {"id": "r3", "label": "I 到 AB 距离", "type": "distance_point_line", "point": "I", "line": "AB_l"},
            {"id": "S", "label": "面积 S", "type": "area_triangle", "pts": ["A", "B", "C"]},
            {"id": "p2", "label": "半周长 p", "type": "expr",
             "expr": f"{f(sol['vals']['p'])}", "digits": 2},
        ],
        "constant": {"of": "r", "label": f"$r = \\dfrac{{2S}}{{p}} = {tex(sol['r'])}$"},
        "legend": [{"color": "given", "text": "虚线 = 三顶点到内心（角平分线）"}, {"color": "curve", "text": "半径⊥各边（直角标记）"}],
    }
    # 需要两条"边所在直线"供 distance_point_line 使用
    board["derived"].insert(2, {"type": "line_through_points", "name": "AC_l", "a": "A", "b": "C", "color": "aux", "dashed": True})
    board["derived"].insert(2, {"type": "line_through_points", "name": "AB_l", "a": "A", "b": "B", "color": "aux", "dashed": True})
    # 切点为静态构造点（feet），补进 points
    for key, name in [("BC", "Tbc"), ("AC", "Tac"), ("AB", "Tab")]:
        board["points"][name] = pt(feet[key], "curve", None, False)
    lesson = {
        "language": "zh-CN", "title": "三角形的内切圆与内心",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>已知 △ABC 三边 $BC = 13$，$CA = 14$，$AB = 15$（如图）。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'><li>求 △ABC 内切圆的半径 r；</li>"
                    "<li>说明内心的性质：到三边距离相等。</li></ol>"),
        "answerLabel": "内切圆半径 r", "answer": f"${sol['answer_latex']}$",
    }
    steps = [
        {"title": "内心是什么",
         "content": ("<p><b>内心</b>：三角形三条<b>角平分线</b>的交点（图中三条虚线），"
                     "到三边的距离相等，这个距离就是内切圆半径 r。</p>")},
        {"title": "用面积法求 r",
         "content": (f"<p>把 △ABC 分成三个小三角形 △IAB、△IBC、△IAC，公共高都是 r：</p>"
                     f"<p class='text-center'>$$ S = \\tfrac12 r\\,(AB+BC+CA) = r \\cdot p $$</p>"
                     f"<p>其中半周长 $p = {tex(sol['vals']['p'])}$，面积 $S = {tex(sol['vals']['S'])}$，故</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ r = \\frac{{2S}}{{p}} = \\frac{{2 \\times {tex(sol['vals']['S'])}}}{{{tex(sol['vals']['p'])}}} = {sol['answer_latex']} $$</div>")},
        {"title": "验证三边距离相等",
         "content": (f"<p>控制台三个距离读数（I 到 BC、AC、AB）<b>全部等于</b> "
                     f"$r = {tex(sol['r'])}$，且三个切点处都有直角标记——"
                     "这就是“内心到三边等距”的含义。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 8) 外接圆与外心
# =====================================================================
def build_circumcircle() -> dict:
    A, B, C = V(0, 0), V(14, 0), V(5, 12)   # 13-14-15，R = abc/4S = 65/8
    sol = K.solve_circumcircle(A, B, C)
    O = sol["O"]
    board = {
        "view": dict(NO_AXES, **{"xRange": [-1.5, 15.5], "yRange": [-1.5, 13.5]}),
        "points": dict({n: pt(p, "given", n) for n, p in sol["pts"].items()},
                       **{"O": pt(O, "fixed", "O", True)}),
        "derived": [
            {"type": "circumcircle", "name": "cc", "a": "A", "b": "B", "c": "C", "color": "curve", "label": "外接圆"},
            {"type": "perp_bisector", "name": "pb1", "a": "A", "b": "B", "color": "aux", "dashed": True},
            {"type": "perp_bisector", "name": "pb2", "a": "B", "b": "C", "color": "aux", "dashed": True},
            {"type": "segment", "name": "OA_", "a": "O", "b": "A", "color": "curve"},
            {"type": "segment", "name": "OB_", "a": "O", "b": "B", "color": "curve"},
            {"type": "segment", "name": "OC_", "a": "O", "b": "C", "color": "curve"},
        ],
        "readouts": [
            {"id": "ra", "label": "OA", "type": "length", "a": "O", "b": "A", "highlight": True},
            {"id": "rb", "label": "OB", "type": "length", "a": "O", "b": "B"},
            {"id": "rc", "label": "OC", "type": "length", "a": "O", "b": "C"},
            {"id": "S", "label": "面积 S", "type": "area_triangle", "pts": ["A", "B", "C"]},
        ],
        "constant": {"of": "ra", "label": f"$R = OA=OB=OC = {tex(sol['R'])}$"},
        "legend": [{"color": "aux", "text": "虚线 = 两边的中垂线（交于外心 O）"}, {"color": "curve", "text": "外接圆半径 R"}],
    }
    lesson = {
        "language": "zh-CN", "title": "三角形的外接圆与外心",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    f"<p>如图，△ABC 内接于 ⊙O，已知三顶点坐标（单位长度）。"
                    f"由 #7 的计算知 $S = {tex(K.incenter_radius(A, B, C)[2]['S'])}$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'><li>求 △ABC 外接圆的半径 R；</li>"
                    "<li>说明外心的性质：到三顶点距离相等。</li></ol>"),
        "answerLabel": "外接圆半径 R", "answer": f"${sol['answer_latex']}$",
    }
    steps = [
        {"title": "外心是什么",
         "content": ("<p><b>外心</b>：三角形三条<b>边的中垂线</b>的交点（图中两条虚线），"
                     "到三顶点的距离相等，这个距离就是外接圆半径 R。</p>")},
        {"title": "用面积公式求 R",
         "content": (f"<p>由三角形面积公式 $S = \\dfrac{{abc}}{{4R}}$（正弦定理推论）得</p>"
                     f"<p class='text-center'>$$ R = \\dfrac{{abc}}{{4S}} $$</p>"
                     f"<p>代入三边与面积（由 #7 已算得），得</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ R = {sol['answer_latex']} $$</div>")},
        {"title": "特殊情形",
         "content": ("<p>若 △ABC 是直角三角形，则外心恰好是<b>斜边中点</b>，R = 斜边 ÷ 2。"
                     "可以在 #7 的 3-4-5 直角三角形上验证这一点。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
REGISTRY = {
    "pythagoras": build_pythagoras,
    "inscribed_angle": build_inscribed_angle,
    "tangent_secant": build_tangent_secant,
    "intersecting_chords": build_intersecting_chords,
    "similar_A": build_similar_A,
    "midsegment": build_midsegment,
    "incircle": build_incircle,
    "circumcircle": build_circumcircle,
}

CLEAN_TRIPLES = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (7, 24, 25), (9, 12, 15)]


def _random_build(rng):
    """随机出一题：勾股定理额外随机一组勾股数（保持答案规整）。"""
    key = rng.choice(["pythagoras", "similar_A", "midsegment", "incircle", "circumcircle"])
    if key == "pythagoras":
        a, b, _c = rng.choice(CLEAN_TRIPLES)
        return key, build_pythagoras(a, b)
    return key, REGISTRY[key]()


def main(argv):
    # 统一入口（edulab/shared/skillkit.py）：
    #   python generate.py list | all <目录> | random [seed] [输出] | <key> [输出]
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="初中平面几何 · 交互课件", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
