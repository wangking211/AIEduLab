#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页函数与导数交互网页。

数据由 lib/fn_kernel.py 的 sympy 精确计算驱动（单一数据源）：导数、切线、极值、
奇偶性、零点、左右导数全部精确算出；函数表达式经 js() 翻译给画板实时采样，
保证"图、解、答"同源一致。每个 build_* 内置自检断言。

依赖 sympy。用能 import sympy 的解释器运行：
    python scripts/generate.py <题型key> [输出.html]
    python scripts/generate.py list
    python scripts/generate.py all <输出目录>
    python scripts/generate.py random [seed] [输出.html]
"""

import json
import random as _random
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "template" / "board.html"
PLACEHOLDER = "__LESSON_DATA__"

sys.path.insert(0, str(SKILL_DIR / "lib"))
import sympy as sp                       # noqa: E402
import fn_kernel as K                    # noqa: E402
from fn_kernel import x, tex, f, js      # noqa: E402


def render_html(data: dict, out_path: Path) -> Path:
    template = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        raise RuntimeError(f"模板中未找到占位符 {PLACEHOLDER}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(template.replace(PLACEHOLDER, json.dumps(data, ensure_ascii=False)),
                        encoding="utf-8")
    return out_path


def pt(xy, color="point", label=None, emphasis=False):
    return {"xy": [f(xy[0]), f(xy[1])], "color": color, "label": label, "emphasis": emphasis}


def fn_conic(name, expr, dexpr=None, color="curve", label=None, dashed=False):
    """kind:'function' 曲线定义（表达式经 js() 翻译，画板逐点采样）。"""
    c = {"name": name, "kind": "function", "expr": js(expr), "color": color,
         "label": label or f"$y={tex(expr)}$"}
    if dexpr is not None:
        c["dexpr"] = js(dexpr)
    if dashed:
        c["dashed"] = True
    return c


# =====================================================================
# 1) 切线方程 —— 滑块驱动切点，切线实时重画
# =====================================================================
def build_tangent_line() -> dict:
    expr = x ** 2
    sol = K.solve_tangent_line(expr, 1)
    board = {
        "view": {"xRange": [-2.5, 3.5], "yRange": [-2.5, 6.5]},
        "conics": [fn_conic("f", expr, sol["d_expr"], label="$f(x)=x^2$")],
        "points": {"A": pt([1, 1], "given", "A", True), "O": pt([0, 0], "point", None, False)},
        "param": {"name": "x0", "label": "切点横坐标 $x_0$",
                  "min": -2.2, "max": 3.2, "step": 0.01, "value": 1.0, "unit": "", "standard": 1.0,
                  "ticks": ["-2.2", "0", "1 (题设)", "3.2"]},
        "derived": [
            {"type": "point_on_function", "name": "P", "conic": "f", "x": "@param",
             "color": "fixed", "emphasis": True},
            {"type": "tangent_function", "name": "T", "conic": "f", "x": "@param", "color": "ptB"},
            {"type": "line_through_point_dir", "name": "xaxis", "point": "O", "dir": [1, 0],
             "color": "aux", "dashed": True},
            {"type": "foot_perp", "name": "Px", "point": "P", "line": "xaxis", "color": "aux"},
            {"type": "segment", "name": "drop", "a": "P", "b": "Px", "color": "aux", "dashed": True},
        ],
        "readouts": [
            {"id": "x0", "label": "$x_0$", "type": "expr", "expr": "x0", "digits": 2},
            {"id": "fv", "label": "$f(x_0)$", "type": "fn_value", "conic": "f", "x": "@param", "highlight": True},
            {"id": "k", "label": "切线斜率 $f'(x_0)$", "type": "fn_slope", "conic": "f", "x": "@param"},
        ],
        "constant": None,
        "legend": [
            {"color": "curve", "text": "$f(x)=x^2$"},
            {"color": "ptB", "text": "切线 $y=f'(x_0)(x-x_0)+f(x_0)$"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "求曲线的切线方程",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>已知函数 $f(x)=x^2$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求曲线 $y=f(x)$ 在点 $(1, f(1))$ 处的切线方程；</li>"
                    "<li>拖动滑块改变切点 $x_0$，观察切线斜率如何随 $f'(x_0)=2x_0$ 变化。</li></ol>"),
        "answerLabel": "x=1 处的切线方程",
        "answer": f"$y={sol['line_latex']}$",
    }
    steps = [
        {"title": "求导函数",
         "content": (f"<p>由求导公式 $(x^n)' = nx^{{n-1}}$：</p>"
                     f"<p class='text-center'>$$ f'(x) = {tex(sol['d_expr'])} $$</p>")},
        {"title": "算斜率与切点",
         "content": (f"<p>在 $x_0 = 1$ 处：斜率 $k = f'(1) = {tex(sol['k'])}$，"
                     f"切点 $y_0 = f(1) = {tex(sol['y0'])}$，即切点 $(1, {tex(sol['y0'])})$。</p>")},
        {"title": "写出切线方程",
         "content": (f"<p>由点斜式 $y - y_0 = k(x - x_0)$：</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ y - {tex(sol['y0'])} = {tex(sol['k'])}(x - 1) \\Rightarrow y = {sol['line_latex']} $$</div>"
                     "<p>拖动滑块：切点移动时切线实时旋转，斜率读数始终等于 $f'(x_0)=2x_0$。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 割线逼近切线 —— 导数定义
# =====================================================================
def build_secant_limit() -> dict:
    expr = x ** 2
    sol = K.solve_secant_limit(expr, 1)
    board = {
        "view": {"xRange": [-0.5, 3.2], "yRange": [-1.2, 5.2]},
        "conics": [fn_conic("f", expr, sol["d_expr"], label="$f(x)=x^2$")],
        "points": {"A": pt([1, 1], "given", "A", True)},
        "param": {"name": "h", "label": "横坐标增量 $h = x_1 - 1$",
                  "min": -0.9, "max": 2.0, "step": 0.01, "value": 1.0, "unit": "", "standard": 1.0,
                  "ticks": ["-0.9", "0（重合）", "1 (题设)", "2.0"]},
        "derived": [
            {"type": "point_on_function", "name": "B", "conic": "f", "x": "1+h",
             "color": "fixed", "emphasis": True},
            {"type": "secant_function", "name": "S", "conic": "f", "x1": 1, "x2": "1+h", "color": "ptB"},
            {"type": "tangent_function", "name": "T", "conic": "f", "x": 1, "color": "ptA", "dashed": True},
        ],
        "readouts": [
            {"id": "h", "label": "$h$", "type": "expr", "expr": "h", "digits": 2},
            {"id": "dy", "label": "$f(1+h)-f(1)$", "type": "expr",
             "expr": f"({js(expr).replace('x', '(1+h)')})-1", "digits": 3},
            {"id": "k", "label": "割线斜率 $\\dfrac{\\Delta y}{\\Delta x}$",
             "type": "expr", "expr": f"(({js(expr).replace('x', '(1+h)')})-1)/h", "digits": 3, "highlight": True},
            {"id": "kt", "label": "切线斜率 $f'(1)$", "type": "fn_slope", "conic": "f", "x": 1},
            {"id": "near", "label": "割线≈切线？", "type": "status", "expr": "abs(h)", "op": "<", "rhs": 0.15,
             "okText": "h 足够小，二者接近", "badText": "h 较大，尚有差距"},
        ],
        "constant": None,
        "legend": [
            {"color": "curve", "text": "$f(x)=x^2$"},
            {"color": "ptB", "text": "动割线 AB"},
            {"color": "ptA", "text": "目标切线（h→0 的极限位置）"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "割线逼近切线：导数的定义",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>已知 $f(x)=x^2$，$A(1,1)$ 为曲线上一点，$B(1+h, f(1+h))$ 为曲线上另一点。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>用 h 表示割线 AB 的斜率；</li>"
                    "<li>让 h 逐渐变小（拖滑块趋近 0），观察割线斜率趋近什么值，"
                    "由此理解 $f'(1)$ 的几何意义。</li></ol>"),
        "answerLabel": "割线斜率的极限（即 f'(1)）",
        "answer": f"$\\lim_{{h\\to 0}} k = {sol['answer_latex']}$",
    }
    steps = [
        {"title": "写出割线斜率",
         "content": (f"<p>割线 AB 的斜率：</p>"
                     f"<p class='text-center'>$$ k = \\frac{{f(1+h)-f(1)}}{{h}} = "
                     f"\\frac{{(1+h)^2 - 1}}{{h}} = \\frac{{{tex(sol['k_h']).replace('h', 'h')}}}{{h}} = {tex(sol['k_h'])} $$</p>")},
        {"title": "取极限得导数",
         "content": (f"<p>令 $h \\to 0$：</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ f'(1) = \\lim_{{h\\to 0}} {tex(sol['k_h'])} = {sol['answer_latex']} $$</div>"
                     f"<p>这正是 $f'(x)={tex(sol['d_expr'])}$ 在 $x=1$ 处的值。</p>")},
        {"title": "拖动验证",
         "content": ("<p>把滑块从 $h=2$ 逐步拖向 $0$：割线（实线）不断绕点 A 旋转，"
                     "越来越贴近虚线切线；割线斜率读数从 $3 \\to 2.1 \\to 2.01 \\to \\cdots$ 趋近 2。"
                     "<b>导数就是割线斜率的极限</b>——切线是割线的\"极限位置\"。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 三次函数极值与单调区间
# =====================================================================
def build_cubic_extrema() -> dict:
    sol = K.solve_cubic_extrema(1, 0, -3, 0)      # f(x)=x³-3x
    ext_max = next(e for e in sol["extrema"] if e["kind"] == "极大")
    ext_min = next(e for e in sol["extrema"] if e["kind"] == "极小")
    board = {
        "view": {"xRange": [-2.8, 2.8], "yRange": [-3.5, 3.5]},
        "conics": [fn_conic("f", sol["expr"], sol["d_expr"], label="$f(x)=x^3-3x$")],
        "points": {"M": pt([-1, ext_max["value"]], "given", "极大(-1,2)", True),
                   "N": pt([1, ext_min["value"]], "given", "极小(1,-2)", True)},
        "param": {"name": "x0", "label": "动点横坐标 $x_0$",
                  "min": -2.5, "max": 2.5, "step": 0.01, "value": -1.0, "unit": "", "standard": -1.0,
                  "ticks": ["-2.5", "-1 (极大)", "0 (拐点)", "1 (极小)", "2.5"]},
        "derived": [
            {"type": "point_on_function", "name": "P", "conic": "f", "x": "@param",
             "color": "fixed", "emphasis": True},
            {"type": "tangent_function", "name": "T", "conic": "f", "x": "@param", "color": "ptB"},
        ],
        "readouts": [
            {"id": "x0", "label": "$x_0$", "type": "expr", "expr": "x0", "digits": 2},
            {"id": "fv", "label": "$f(x_0)$", "type": "fn_value", "conic": "f", "x": "@param"},
            {"id": "k", "label": "$f'(x_0)$", "type": "fn_slope", "conic": "f", "x": "@param", "highlight": True},
            {"id": "mono", "label": "单调性", "type": "fn_status", "conic": "f", "x": "@param",
             "posText": "k>0：递增 ↗", "negText": "k<0：递减 ↘", "zeroText": "k=0：驻点（极值候选）"},
        ],
        "constant": None,
        "legend": [
            {"color": "curve", "text": "$f(x)=x^3-3x$"},
            {"color": "ptB", "text": "动切线（斜率=f'(x₀)）"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "三次函数的极值与单调区间",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>已知 $f(x)=x^3-3x$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求 $f'(x)$，并解方程 $f'(x)=0$；</li>"
                    "<li>指出 $f(x)$ 的单调区间与极大值、极小值；</li>"
                    "<li>拖动滑块，验证 $f'(x_0)$ 的符号与增减性一致、在驻点处切线水平。</li></ol>"),
        "answerLabel": "极大值与极小值",
        "answer": "$" + sol["answer_latex"] + "$",
    }
    steps = [
        {"title": "求导并解 f'(x)=0",
         "content": (f"<p>$$ f'(x) = {tex(sol['d_expr'])} $$</p>"
                     f"<p>令 $f'(x)=0$：$3x^2-3=0 \\Rightarrow x=\\pm 1$（驻点）。</p>")},
        {"title": "列符号表判增减与极值",
         "content": ("<ul class='list-disc pl-5 space-y-1'>"
                     "<li>$x<-1$：$f'>0$，<b>递增</b> ↗</li>"
                     "<li>$-1<x<1$：$f'<0$，<b>递减</b> ↘</li>"
                     "<li>$x>1$：$f'>0$，<b>递增</b> ↗</li></ul>"
                     "<p>在 $x=-1$ 处由增转减 → <b>极大值</b> $f(-1)=2$；"
                     "在 $x=1$ 处由减转增 → <b>极小值</b> $f(1)=-2$。</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ {sol['answer_latex']} $$</div>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：切线斜率读数与\"单调性\"指示灯同步变化——"
                     "递增段绿色↗、递减段红色↘、经过 $x=\\pm1$ 时变橙色\"驻点\"且切线瞬间水平。"
                     "这正是<b>用导数符号判单调性</b>的方法。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 函数奇偶性 —— 图像关于原点对称
# =====================================================================
def build_parity_odd() -> dict:
    expr = x ** 3 - 3 * x
    sol = K.solve_parity(expr)
    board = {
        "view": {"xRange": [-2.8, 2.8], "yRange": [-3.5, 3.5]},
        "conics": [fn_conic("f", expr, label="$f(x)=x^3-3x$")],
        "points": {},
        "param": {"name": "t", "label": "动点横坐标 $t$",
                  "min": 0.15, "max": 2.4, "step": 0.01, "value": 1.5, "unit": "", "standard": 1.5,
                  "ticks": ["0.15", "1.5 (题设)", "2.4"]},
        "derived": [
            {"type": "point_on_function", "name": "P", "conic": "f", "x": "@param",
             "color": "fixed", "emphasis": True},
            {"type": "point_on_function", "name": "Q", "conic": "f", "x": "-t",
             "color": "ptA", "emphasis": True},
            {"type": "segment", "name": "PQ", "a": "P", "b": "Q", "color": "aux", "dashed": True},
        ],
        "readouts": [
            {"id": "t", "label": "$t$", "type": "expr", "expr": "t", "digits": 2},
            {"id": "fp", "label": "$f(t)$", "type": "fn_value", "conic": "f", "x": "@param", "highlight": True},
            {"id": "fq", "label": "$f(-t)$", "type": "fn_value", "conic": "f", "x": "-t", "highlight": True},
            {"id": "sum", "label": "$f(t)+f(-t)$", "type": "expr",
             "expr": f"({js(expr).replace('x', '(t)')})+({js(expr).replace('x', '(-t)')})", "digits": 3},
            {"id": "odd", "label": "是否 $f(-t)=-f(t)$", "type": "status",
             "expr": f"abs(({js(expr).replace('x', '(-t)')})+({js(expr).replace('x', '(t)')}))",
             "op": "<", "rhs": 1e-6, "okText": "恒成立：奇函数", "badText": "不成立"},
        ],
        "constant": {"of": "sum", "label": "$f(t)+f(-t) \\equiv 0$"},
        "legend": [
            {"color": "curve", "text": "$f(x)=x^3-3x$"},
            {"color": "fixed", "text": "点 P(t, f(t))"},
            {"color": "ptA", "text": "点 Q(-t, f(-t))"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "判断函数的奇偶性",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>判断函数 $f(x)=x^3-3x$ 的奇偶性，并说明其图像的对称性。</p>"
                    "<p class='text-sm text-slate-500'>拖动滑块移动 P 点，观察关于原点对称的 Q 点"
                    "是否始终落在曲线上、两纵坐标之和是否恒为 0。</p>"),
        "answerLabel": "奇偶性结论",
        "answer": f"${sol['answer_latex']}$",
    }
    steps = [
        {"title": "看定义域",
         "content": ("<p>$f(x)=x^3-3x$ 的定义域为 $\\mathbb{R}$，关于原点对称——满足奇偶性的前提。</p>")},
        {"title": "比较 f(-x) 与 f(x)",
         "content": (f"<p>$$ f(-x) = (-x)^3 - 3(-x) = -x^3 + 3x = -(x^3-3x) = -f(x) $$</p>"
                     f"<p>对定义域内一切 $x$ 都成立，故由定义 <b>是奇函数</b>。</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ {sol['answer_latex']} $$</div>")},
        {"title": "几何意义与拖动验证",
         "content": ("<p>奇函数图像关于<b>原点中心对称</b>。拖动滑块：P 与 Q 关于原点对称"
                     "（虚线 PQ 过原点且被原点平分），Q 始终在曲线上；"
                     "$f(t)+f(-t)$ 读数<b>恒为 0</b>——与代数推导互相印证。</p>"
                     "<p class='text-sm text-slate-500'>注：若把函数换成 $x^2$ 重复实验，"
                     "会看到 $f(t)=f(-t)$ 恒成立（偶函数、关于 y 轴对称）。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 零点存在定理 —— f(a)f(b)<0 + 二分逼近
# =====================================================================
def build_zero_crossing() -> dict:
    expr = x ** 3 - x - 2
    sol = K.solve_zero_crossing(expr, 1, 2)
    rk = f(sol["root_approx"])
    board = {
        "view": {"xRange": [0.2, 2.8], "yRange": [-3.5, 5.5]},
        "conics": [fn_conic("f", expr, label="$f(x)=x^3-x-2$")],
        "points": {"A": pt([1, sol["ends"]["fa"]], "ptA", "A(1,-2)", True),
                   "B": pt([2, sol["ends"]["fb"]], "ptB", "B(2,4)", True),
                   "O": pt([0, 0], "point", None, False)},
        "param": {"name": "m", "label": "二分中点 $m$",
                  "min": 1.0, "max": 2.0, "step": 0.01, "value": 1.5, "unit": "", "standard": 1.5,
                  "ticks": ["1", "1.5 (第一次二分)", "2"]},
        "derived": [
            {"type": "point_on_function", "name": "P", "conic": "f", "x": "@param",
             "color": "fixed", "emphasis": True},
            {"type": "root_on_function", "name": "Z", "conic": "f", "a": 1, "b": 2, "color": "curve"},
            {"type": "line_through_point_dir", "name": "xaxis", "point": "O", "dir": [1, 0],
             "color": "aux", "dashed": True},
            {"type": "foot_perp", "name": "Px", "point": "P", "line": "xaxis", "color": "aux"},
            {"type": "segment", "name": "PM", "a": "P", "b": "Px", "color": "aux", "dashed": True},
        ],
        "readouts": [
            {"id": "m", "label": "$m$", "type": "expr", "expr": "m", "digits": 2},
            {"id": "fm", "label": "$f(m)$", "type": "fn_value", "conic": "f", "x": "@param", "highlight": True},
            {"id": "sgn", "label": "零点在 m 的哪侧", "type": "status",
             "expr": f"({js(expr).replace('x', '(m)')})*({f(sol['ends']['fa'])})",
             "op": ">", "rhs": 0, "okText": "f(m)与f(1)同号 → 零点在 m 右侧",
             "badText": "f(m)与f(1)异号 → 零点在 (1,m) 内"},
            {"id": "root", "label": "零点（精确二分）", "type": "expr", "expr": f"{rk}", "digits": 4},
        ],
        "constant": None,
        "legend": [
            {"color": "curve", "text": "$f(x)=x^3-x-2$"},
            {"color": "fixed", "text": "试根点 P(m, f(m))"},
            {"color": "curve", "text": "真实零点 Z"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "零点存在定理与二分法",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>已知 $f(x)=x^3-x-2$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>验证 $f(x)$ 在区间 $(1,2)$ 内存在零点；</li>"
                    "<li>用二分法求出该零点（精确到 0.1）；</li>"
                    "<li>拖动滑块试根，观察 $f(m)$ 的符号如何指示零点所在子区间。</li></ol>"),
        "answerLabel": "零点所在区间与近似值",
        "answer": f"零点在 $(1,2)$ 内，${sol['answer_latex']}$",
    }
    rows = "".join(
        f"<tr><td class='px-2 py-1 border border-slate-200'>{tex(h['lo'])}</td>"
        f"<td class='px-2 py-1 border border-slate-200'>{tex(h['hi'])}</td>"
        f"<td class='px-2 py-1 border border-slate-200'>{tex(h['mid'])}</td>"
        f"<td class='px-2 py-1 border border-slate-200'>{tex(h['fm'])}</td></tr>"
        for h in sol["hist"])
    steps = [
        {"title": "验证端点异号",
         "content": (f"<p>$$ f(1) = 1 - 1 - 2 = {tex(sol['ends']['fa'])} < 0,\\quad "
                     f"f(2) = 8 - 2 - 2 = {tex(sol['ends']['fb'])} > 0 $$</p>"
                     "<p>$f(x)$ 在 $\\mathbb{R}$ 上连续且 $f(1)f(2)<0$，"
                     "由<b>零点存在定理</b>（介值定理推论）知 $(1,2)$ 内至少有一个零点。</p>")},
        {"title": "二分法逼近",
         "content": ("<table class='w-full text-sm'><thead><tr>"
                     "<th class='px-2 py-1 border border-slate-300 bg-slate-100'>a</th>"
                     "<th class='px-2 py-1 border border-slate-300 bg-slate-100'>b</th>"
                     "<th class='px-2 py-1 border border-slate-300 bg-slate-100'>中点 m</th>"
                     "<th class='px-2 py-1 border border-slate-300 bg-slate-100'>f(m)</th></tr></thead>"
                     f"<tbody>{rows}</tbody></table>"
                     "<p class='mt-2'>每次取中点、保留异号子区间，区间长度逐次减半。</p>")},
        {"title": "结论",
         "content": (f"<p>精确到 0.1，零点约为 $x \\approx {sol['answer_latex'].replace('\\\\approx ', '')}$。"
                     "拖动滑块：$f(m)$ 为负时零点在 m 右侧、为正时在左侧——"
                     "<b>符号判断 + 对半收缩</b>就是二分法的全部要领。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 指数函数 y=aˣ —— 恒过定点 (0,1)
# =====================================================================
def build_exp_family() -> dict:
    sol = K.solve_exp_family(2)
    a_sym = sp.Symbol("a", positive=True)
    expr_a = a_sym ** x                       # 底数随滑块变量 a 变化
    dexpr_a = sp.simplify(expr_a * sp.log(a_sym))
    board = {
        "view": {"xRange": [-2.2, 3.2], "yRange": [-1.2, 6.5]},
        "conics": [fn_conic("f", expr_a, dexpr_a, label="$y=a^x$")],
        "points": {"Q": pt([0, 1], "given", "(0,1)", True)},
        "param": {"name": "a", "label": "底数 $a$（a>0 且 a≠1）",
                  "min": 0.15, "max": 3.0, "step": 0.01, "value": 2.0, "unit": "", "standard": 2.0,
                  "ticks": ["0.15", "0.5（减函数）", "1（退化，非指数函数）", "2 (题设)", "3"]},
        "derived": [
            {"type": "point_on_function", "name": "P", "conic": "f", "x": "@param",
             "color": "fixed", "emphasis": True},
            {"type": "tangent_function", "name": "T", "conic": "f", "x": "@param", "color": "ptB"},
        ],
        "readouts": [
            {"id": "a", "label": "底数 $a$", "type": "expr", "expr": "a", "digits": 2},
            {"id": "f0", "label": "$a^0$", "type": "fn_value", "conic": "f", "x": 0, "highlight": True},
            {"id": "f1", "label": "$a^1$", "type": "fn_value", "conic": "f", "x": 1},
            {"id": "mono", "label": "单调性", "type": "status", "expr": "a", "op": ">", "rhs": 1,
             "okText": "a>1：在 R 上递增 ↗", "badText": "0<a<1：在 R 上递减 ↘"},
        ],
        "constant": {"of": "f0", "label": "$a^0 \\equiv 1$（图像恒过定点 (0,1)）"},
        "legend": [
            {"color": "curve", "text": "$y=a^x$（随滑块变化）"},
            {"color": "given", "text": "定点 $(0,1)$"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "指数函数 y=aˣ 的图像与性质",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>作函数 $y=a^x$（$a>0$ 且 $a\\ne 1$）的图像。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求图像恒过的定点，并计算 $a^0$、$a^1$；</li>"
                    "<li>拖动滑块改变底数 $a$，观察 $a>1$ 与 $0<a<1$ 两种情形下图像的增减性；"
                    "特别地观察 $a=1$ 时为何不再是指数函数。</li></ol>"),
        "answerLabel": "恒过的定点",
        "answer": "$(0,1)$（因 $a^0=1$ 恒成立）",
    }
    steps = [
        {"title": "求定点",
         "content": (f"<p>无论 $a$ 取何值（$a>0$ 且 $a\\ne1$）：</p>"
                     f"<p class='text-center'>$$ a^0 = {sol['answer_latex']},\\quad a^1 = a $$</p>"
                     "<p>所以图像<b>恒过定点 $(0,1)$</b>；$x=1$ 时纵坐标恰为底数 $a$（读数可验证）。</p>")},
        {"title": "单调性分类",
         "content": ("<ul class='list-disc pl-5 space-y-1'>"
                     "<li>$a>1$：$y=a^x$ 在 $\\mathbb{R}$ 上<b>递增</b>，x→-∞ 时贴近 x 轴；</li>"
                     "<li>$0<a<1$：在 $\\mathbb{R}$ 上<b>递减</b>，x→+∞ 时贴近 x 轴；</li>"
                     "<li>$a=1$：$y\\equiv1$ 是常数函数，<b>不属于</b>指数函数（滑块拖到 1 附近可见图像变水平）。</li></ul>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：$a^0$ 读数<b>始终是 1</b>（定点不动），"
                     "而 $a^1$ 读数跟随底数变化；单调性指示灯在 $a=1$ 处由绿转红。"
                     "值域恒为 $(0,+\\infty)$，图像始终在 x 轴上方。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) |x| 在 x=0 处不可导 —— 左右导数不等
# =====================================================================
def build_abs_corner() -> dict:
    sol = K.solve_abs_corner(0)
    # f(x)=|x| 的导函数（x≠0）：x/|x| = sign(x)
    d_expr = x / sp.Abs(x)
    board = {
        "view": {"xRange": [-2.8, 2.8], "yRange": [-1.2, 3.2]},
        "conics": [fn_conic("f", sol["expr"], d_expr, label="$f(x)=|x|$")],
        "points": {"C": pt([0, 0], "given", "O(0,0)", True)},
        "param": {"name": "h", "label": "步长 $h$（比较 $\\pm h$ 处的差商）",
                  "min": 0.02, "max": 2.0, "step": 0.01, "value": 0.5, "unit": "", "standard": 0.5,
                  "ticks": ["0.02", "0.5 (题设)", "2.0"]},
        "derived": [
            {"type": "point_on_function", "name": "Pp", "conic": "f", "x": "h", "color": "ptA", "emphasis": True},
            {"type": "point_on_function", "name": "Pm", "conic": "f", "x": "-h", "color": "ptB", "emphasis": True},
            {"type": "secant_function", "name": "Sp", "conic": "f", "x1": 0, "x2": "h", "color": "ptA"},
            {"type": "secant_function", "name": "Sm", "conic": "f", "x1": "-h", "x2": 0, "color": "ptB"},
        ],
        "readouts": [
            {"id": "dl", "label": "左导数 $f'_-(0)$", "type": "expr", "expr": f"(({js(sol['expr']).replace('x', '(-h)')})-0)/(-h)",
             "digits": 3, "color": "ptB", "highlight": True},
            {"id": "dr", "label": "右导数 $f'_+(0)$", "type": "expr", "expr": f"(({js(sol['expr']).replace('x', '(h)')})-0)/h",
             "digits": 3, "color": "ptA", "highlight": True},
            {"id": "diff", "label": "左右差商之差", "type": "expr",
             "expr": f"(({js(sol['expr']).replace('x', '(h)')})/h)-(({js(sol['expr']).replace('x', '(-h)')})/(-h))",
             "digits": 3},
            {"id": "judge", "label": "x=0 可导吗", "type": "status",
             "expr": f"abs((({js(sol['expr']).replace('x', '(h)')})/h)-(({js(sol['expr']).replace('x', '(-h)')})/(-h)))",
             "op": "<", "rhs": 1e-9, "okText": "左右相等，可导", "badText": "左右不等 → 不可导（尖点）"},
        ],
        "constant": None,
        "legend": [
            {"color": "curve", "text": "$f(x)=|x|$"},
            {"color": "ptA", "text": "右侧割线（斜率 +1）"},
            {"color": "ptB", "text": "左侧割线（斜率 -1）"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "绝对值函数在原点处不可导",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>讨论 $f(x)=|x|$ 在 $x=0$ 处的可导性。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>用定义分别求 $f'(0)$ 的左导数与右导数；</li>"
                    "<li>拖动滑块缩小步长 $h$，观察两侧差商是否趋于同一值。</li></ol>"),
        "answerLabel": "可导性结论",
        "answer": f"左导数 ${tex(sol['dl'])}$ ≠ 右导数 ${tex(sol['dr'])}$，故 $f(x)$ 在 $x=0$ 处<b>不可导</b>",
    }
    steps = [
        {"title": "用定义算左右导数",
         "content": (f"<p>右导数：</p>"
                     f"<p class='text-center'>$$ f'_+(0) = \\lim_{{h\\to0^+}} \\frac{{|h|-|0|}}{{h}} = "
                     f"\\lim_{{h\\to0^+}} \\frac{{h}}{{h}} = {tex(sol['dr'])} $$</p>"
                     f"<p>左导数：</p>"
                     f"<p class='text-center'>$$ f'_-(0) = \\lim_{{h\\to0^+}} \\frac{{|-h|-|0|}}{{-h}} = "
                     f"\\lim_{{h\\to0^+}} \\frac{{h}}{{-h}} = {tex(sol['dl'])} $$</p>")},
        {"title": "下结论",
         "content": (f"<p>$$ {tex(sol['dl'])} \\ne {tex(sol['dr'])} $$</p>"
                     f"<p>左右导数不相等，所以 $f(x)=|x|$ 在 $x=0$ 处<b>不可导</b>。"
                     "几何上看：图像在原点是一个<b>尖点</b>，左、右两侧\"切线\"分别是斜率 -1 与 +1 的直线，"
                     "不存在唯一切线。</p>")},
        {"title": "拖动验证",
         "content": ("<p>无论滑块 $h$ 取多小，两条割线（红/蓝）始终\"卡\"在尖点两侧，"
                     "左右差商读数恒为 +1 与 -1，差值恒为 2——<b>极限不存在</b>。"
                     "这说明\"连续\"（图像没断）不等于\"可导\"（有光滑切线）。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 8) 切线族 y 轴截距 —— 对数函数切线的定值/最值
# =====================================================================
def build_tangent_family() -> dict:
    sol = K.solve_tangent_family()          # f(x)=ln x, 切线 y 轴截距 = ln a - 1
    a_sym = sol["a_sym"]
    board = {
        "view": {"xRange": [-1.2, 4.5], "yRange": [-3.2, 2.8]},
        "conics": [fn_conic("f", sol["expr"], sol["d_expr"], label="$f(x)=\\ln x$")],
        "points": {"O": pt([0, 0], "point", None, False)},
        "param": {"name": "a", "label": "切点横坐标 $a$（a>0）",
                  "min": 0.1, "max": 4.0, "step": 0.01, "value": 1.0, "unit": "", "standard": 1.0,
                  "ticks": ["0.1", "1 (题设)", "e≈2.72（截距=0）", "4.0"]},
        "derived": [
            {"type": "line_through_point_dir", "name": "Yaxis", "point": "O", "dir": [0, 1],
             "color": "aux", "dashed": True},
            {"type": "point_on_function", "name": "P", "conic": "f", "x": "@param",
             "color": "fixed", "emphasis": True},
            {"type": "tangent_function", "name": "T", "conic": "f", "x": "@param", "color": "ptB"},
            {"type": "intersect_line_line", "name": "Y", "a": "T", "b": "Yaxis", "color": "curve", "emphasis": True},
        ],
        "readouts": [
            {"id": "a", "label": "切点 $a$", "type": "expr", "expr": "a", "digits": 2},
            {"id": "k", "label": "斜率 $f'(a)=1/a$", "type": "fn_slope", "conic": "f", "x": "@param"},
            {"id": "b", "label": "y 轴截距", "type": "expr", "expr": f"log(a)-1", "digits": 3, "highlight": True},
            {"id": "zero", "label": "截距何时为 0", "type": "status", "expr": "abs(a-2.718281828)",
             "op": "<", "rhs": 0.02, "okText": "a≈e：切线过原点", "badText": "a≠e"},
        ],
        "constant": None,
        "legend": [
            {"color": "curve", "text": "$f(x)=\\ln x$"},
            {"color": "ptB", "text": "动切线"},
            {"color": "curve", "text": "切线与 y 轴交点"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "对数曲线的切线与 y 轴截距",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>过曲线 $y=\\ln x$ 上一点 $P(a,\\ln a)$（$a>0$）作切线，切线与 y 轴相交。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求切线方程及它在 y 轴上的截距（用 a 表示）；</li>"
                    "<li>拖动滑块观察：$a$ 为何值时切线恰好过原点？</li></ol>"),
        "answerLabel": "y 轴截距",
        "answer": f"$b = {sol['answer_latex']}$（$a=e$ 时截距为 0，切线过原点）",
    }
    steps = [
        {"title": "求切线方程",
         "content": (f"<p>$$ f'(x) = {tex(sol['d_expr'])} \\Rightarrow k = f'(a) = \\frac1a $$</p>"
                     f"<p>切线：$y - \\ln a = \\dfrac1a(x - a)$，即 $y = \\dfrac1a x + \\ln a - 1$。</p>")},
        {"title": "求 y 轴截距",
         "content": (f"<p>令 $x=0$：</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ b = \\ln a - 1 $$</div>"
                     "<p>可见截距随 $a$ 变化（不是定值），但有一个特殊位置："
                     "$\\ln a - 1 = 0 \\Rightarrow a = e$ 时切线<b>恰好过原点</b>。</p>")},
        {"title": "拖动验证",
         "content": ("<p>把滑块拖到 $a \\approx 2.72$（即 $e$）：切线恰好穿过原点，"
                     "y 轴截距读数归零，指示灯变绿。$a<e$ 时截距为负、$a>e$ 时为正——"
                     "读数与 $\\ln a - 1$ 的公式处处吻合。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
REGISTRY = {
    "tangent_line": build_tangent_line,
    "secant_limit": build_secant_limit,
    "cubic_extrema": build_cubic_extrema,
    "parity_odd": build_parity_odd,
    "zero_crossing": build_zero_crossing,
    "exp_family": build_exp_family,
    "abs_corner": build_abs_corner,
    "tangent_family": build_tangent_family,
}


def main(argv):
    if not argv or argv[0] == "list":
        print("已注册题型:")
        for k in REGISTRY:
            print(" -", k)
        return
    if argv[0] == "random":
        seed = int(argv[1]) if len(argv) > 1 else 0
        out = Path(argv[2]) if len(argv) > 2 else (Path.cwd() / "random.html")
        rng = _random.Random(seed)
        key = rng.choice(list(REGISTRY))
        render_html(REGISTRY[key](), out)
        print(f"written: {out} (seed={seed} -> {key})")
        return
    if argv[0] == "all":
        out_dir = Path(argv[1]) if len(argv) > 1 else (SKILL_DIR / "output")
        out_dir.mkdir(parents=True, exist_ok=True)
        for k, fn in REGISTRY.items():
            render_html(fn(), out_dir / f"{k}.html")
            print("written:", out_dir / f"{k}.html")
        return
    key = argv[0]
    if key not in REGISTRY:
        print(f"未知题型 {key}；可用: {', '.join(REGISTRY)}")
        sys.exit(1)
    out = Path(argv[1]) if len(argv) > 1 else (Path.cwd() / f"{key}.html")
    render_html(REGISTRY[key](), out)
    print(f"written: {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
