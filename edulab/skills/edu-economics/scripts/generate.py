#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「经济学」交互网页。

**本技能沿用 edu-history 的证据力纪律**：每一页都带徽章，显式声明这张图能证明到什么程度。
经济学的最大风险正是**把「模型」当成「预测」**：

    A  纯数学 / 恒等式     —— 图上的数错不了
    B  模型：参数靠估      —— 结论的形状可靠，具体数值取决于你怎么估参数
    C  形态①、证据力③     —— 只能说明「如果假设成立会怎样」

全部数值由 lib/econ_kernel.py 驱动，**不手写数字**。

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

import econ_kernel as K                      # noqa: E402
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


def _find_ternary(s):
    """找第一个三目 `?` 及其所在括号组边界（支持任意深度嵌套）。"""
    depth, q, qdepth = 0, -1, 0
    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "?":
            q, qdepth = i, depth
            break
    if q < 0:
        return None
    depth, nest, colon = qdepth, 0, -1
    for i in range(q + 1, len(s)):
        ch = s[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "?" and depth == qdepth:
            nest += 1
        elif ch == ":" and depth == qdepth:
            if nest == 0:
                colon = i
                break
            nest -= 1
    if colon < 0:
        raise ValueError(f"三目表达式缺冒号：{s!r}")
    lo, d = -1, 0
    for i in range(q - 1, -1, -1):
        if s[i] == ")":
            d += 1
        elif s[i] == "(":
            if d == 0:
                lo = i
                break
            d -= 1
    if lo < 0:
        hi = len(s)
    else:
        d, hi = 0, -1
        for i in range(lo, len(s)):
            if s[i] == "(":
                d += 1
            elif s[i] == ")":
                d -= 1
                if d == 0:
                    hi = i
                    break
        if hi < 0:
            raise ValueError(f"括号不配对：{s!r}")
    return lo, q, colon, hi


def _js_to_py(expr):
    """把三目 `a?b:c` 翻成 Python 的 `b if a else c`（供构建期对账）。"""
    while True:
        f = _find_ternary(expr)
        if f is None:
            return expr
        lo, q, colon, hi = f
        base = lo + 1 if lo >= 0 else 0
        cond, yes, no = expr[base:q], expr[q + 1:colon], expr[colon + 1:hi]
        inner = f"({_js_to_py(yes)} if {_js_to_py(cond)} else {_js_to_py(no)})"
        expr = expr[:base] + inner + expr[hi:]


def _jseval(expr, **env):
    return eval(_js_to_py(expr.replace("^", "**")), {"__builtins__": {}}, {**_MATHENV, **env})


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


def _evid_badge(level):
    tag, note = K.EVIDENCE[level]
    return f"证据力 {level}｜{tag} —— {note}"


# =====================================================================
# 1) 供需均衡与消费者/生产者剩余（① A）
# =====================================================================
def build_supply() -> dict:
    a0, b, c, d = 10.0, 2.0, 2.0, 2.0
    p0, q0 = K.market_equilibrium(a0, b, c, d)
    EXPR_P = "(a-2)/4"
    EXPR_Q = "(a+2)/2"
    EXPR_CS = "(a+2)*(a+2)/16"
    EXPR_TOT = "(a+2)*(a+2)/8"
    for a in (6.0, 8.0, 10.0, 13.0, 16.0):
        pp, qq = K.market_equilibrium(a, b, c, d)
        _agree(f"p*(a={a})", EXPR_P, float(pp), tol=1e-12, a=a)
        _agree(f"q*(a={a})", EXPR_Q, float(qq), tol=1e-12, a=a)
        _agree(f"CS(a={a})", EXPR_CS, float(K.consumer_surplus(a, b, pp)), tol=1e-12, a=a)
        _agree(f"PS(a={a})", EXPR_CS, float(K.producer_surplus(c, d, pp)), tol=1e-12, a=a)
        _agree(f"总剩余(a={a})", EXPR_TOT, float(K.total_surplus(a, b, c, d)), tol=1e-12, a=a)
    _agree("均衡处供需相等", EXPR_Q, float(K.demand_q(p0, a0, b)), tol=1e-12, a=a0)
    assert float(p0) == 2.0 and float(q0) == 6.0

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "market", "a": "a", "caption": _evid_badge("A")},
        "param": {"name": "a", "label": "需求截距 $a$（$q = a - 2p$）", "min": 6, "max": 16,
                  "step": 0.25, "value": a0, "unit": "", "standard": a0,
                  "ticks": ["6", "10 (题设)", "16"]},
        "readouts": [
            ro("p", "均衡价格 $p^*$", EXPR_P, 4),
            ro("q", "均衡数量 $q^*$", EXPR_Q, 4),
            ro("cs", "消费者剩余", EXPR_CS, 4),
            ro("ps", "生产者剩余", EXPR_CS, 4),
            ro("tot", "总剩余", EXPR_TOT, 4),
        ],
        "constant": {"of": "ap", "label": "供给固定为 q = 2 + 2p（改变需求不动它）"},
    }
    lesson = {
        "language": "zh-CN", "title": "供需均衡与两种剩余",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>需求 $q = a - 2p$，供给 $q = 2 + 2p$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求均衡价格与数量；</li>"
            "<li>计算消费者剩余与生产者剩余；</li>"
            "<li>拖动滑块改变需求，两块剩余怎么变？</li></ol>"),
        "answerLabel": "$a = 10$ 时的均衡与剩余",
        "answer": f"$p^* = {K.f(p0,2)}$，$q^* = {K.f(q0,2)}$，"
                  f"$CS = PS = {K.f(K.consumer_surplus(a0, b, p0),2)}$",
    }
    steps = [
        {"title": "均衡就是两条线的交点",
         "content": ("<p>令需求量等于供给量：$a - 2p = 2 + 2p$，得 $p^* = \\dfrac{{a-2}}{{4}}$，"
                     "回代得 $q^* = \\dfrac{{a+2}}{{2}}$。</p>"
                     "<p>这一步是**纯代数** —— 只要两条线是给定的，交点就没有争议。</p>")},
        {"title": "两种剩余都是三角形面积",
         "content": ("<p>**消费者剩余**：愿意付的减去实际付的，即需求曲线在 $p^*$ 以上的面积。"
                     "线性需求下它是一个三角形：</p>"
                     "<p>$CS = \\tfrac12 \\cdot q^* \\cdot (a - p^*) = \\dfrac{{(a+2)^2}}{{16}}$。</p>"
                     "<p>**生产者剩余**同理，是供给曲线在 $p^*$ 以下的面积，"
                     "本参数化下恰好也是 $\\dfrac{{(a+2)^2}}{{16}}$。</p>")},
        {"title": "这一页能证明什么",
         "content": ("<p>证据力 ①A：<b>图上的每个数都错不了</b>，因为它们是交点代数与"
                     "三角形面积，不依赖任何估计。</p>"
                     "<p>但要注意它**没有**说明「需求曲线为什么是这条线」。"
                     "把 $a$ 从 10 拖到 16 只说明「若需求更强，均衡与剩余会怎样」，"
                     "不说明现实中某项政策会不会把需求推强。"
                     "**模型内部的结论 ≠ 现实预测**，这是本技能每一页都要提醒的。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 需求价格弹性（① B —— 具体数值取决于估计的需求曲线）
# =====================================================================
def build_elasticity() -> dict:
    a, b = 10.0, 2.0
    p0 = 2.0
    EXPR_Q = "10-2*p"
    EXPR_E = "-2*p/(10-2*p)"
    EXPR_AE = "abs(-2*p/(10-2*p))"
    for p in (0.5, 1.0, 2.0, 2.5, 3.5, 4.5):
        _agree(f"q(p={p})", EXPR_Q, K.demand_q(p, a, b), tol=1e-12, p=p)
        _agree(f"ε(p={p})", EXPR_E, float(K.point_elasticity(p, a, b)), tol=1e-12, p=p)
        _agree(f"|ε|(p={p})", EXPR_AE, abs(float(K.point_elasticity(p, a, b))), tol=1e-12, p=p)
    _agree("单位弹性点 p = a/(2b)", "10/(2*2)", a / (2 * b), tol=1e-12)
    _agree("单位弹性处 |ε| = 1", "abs(-2*2.5/(10-2*2.5))", 1.0, tol=1e-12)
    assert abs(float(K.point_elasticity(2.5, a, b)) + 1.0) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "elastic", "p": "p", "caption": _evid_badge("B")},
        "param": {"name": "p", "label": "价格 $p$", "min": 0.5, "max": 4.5, "step": 0.1,
                  "value": p0, "unit": "", "standard": p0,
                  "ticks": ["0.5", "2 (题设)", "2.5 (单位弹性)", "4.5"]},
        "readouts": [
            ro("q", "需求量 $q = 10-2p$", EXPR_Q, 3),
            ro("e", "点弹性 $\\varepsilon$", EXPR_E, 4),
            ro("ae", "$|\\varepsilon|$", EXPR_AE, 4),
            ro("unit", "单位弹性点（$|\\varepsilon| = 1$）", "10/(2*2)", 2),
            ro_status("rich", "是否富有弹性", EXPR_AE, 1, ">",
                      "富有弹性（|ε| > 1）", "缺乏弹性（|ε| ≤ 1）"),
        ],
        "constant": {"of": "unit", "label": "单位弹性点固定在 p = 2.5 —— 与 a、b 有关但不是估计的"},
    }
    lesson = {
        "language": "zh-CN", "title": "需求价格弹性",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>需求 $q = 10 - 2p$。求任意价格处的点弹性，并找出 $|\\varepsilon| = 1$ 的位置。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $\\varepsilon(p)$；</li>"
            "<li>哪里富有弹性、哪里缺乏弹性？</li>"
            "<li>为什么涨价在缺乏弹性段能增加收入，在富有弹性段反而减少？</li></ol>"),
        "answerLabel": "$\\varepsilon(p)$",
        "answer": "$\\varepsilon = \\dfrac{dq}{dp}\\cdot\\dfrac{p}{q} = -\\dfrac{2p}{10-2p}$，"
                  "$|\\varepsilon| = 1$ 在 $p = 2.5$",
    }
    steps = [
        {"title": "弹性是「相对变化之比」",
         "content": ("<p>$\\varepsilon = \\dfrac{{dq/dp}}{{q/p}} = \\dfrac{{dq}}{{dp}}\\cdot"
                     "\\dfrac{{p}}{{q}}$ —— 它把「导数」无量纲化，所以可以跨商品比较。</p>"
                     "<p>对 $q = a - bp$，$dq/dp = -b$，于是 $\\varepsilon = -\\dfrac{{bp}}{{a-bp}}$，"
                     "代入得 $\\varepsilon = -\\dfrac{{2p}}{{10-2p}}$。</p>")},
        {"title": "线性需求上的三段",
         "content": ("<p>$|\\varepsilon| = 1$ 当且仅当 $a - bp = bp$，即 $p = \\dfrac{{a}}{{2b}} = 2.5$。</p>"
                     "<p>价格低于它时 $|\\varepsilon| < 1$（缺乏弹性，靠近纵轴的一段）；"
                     "高于它时 $|\\varepsilon| > 1$（富有弹性）。"
                     "价格趋近 $a/b = 5$ 时弹性趋于无穷 —— 那里需求量趋于 0。</p>")},
        {"title": "弹性与收入（本页的证据力）",
         "content": ("<p>收入 $R = pq$，$\\dfrac{{dR}}{{dp}} = q(1+\\varepsilon)$。"
                     "所以 $|\\varepsilon|<1$ 时涨价增收入，$|\\varepsilon|>1$ 时涨价减收入。</p>"
                     "<p><b>证据力 ①B</b>：这个**关系式**是恒等式（①A），"
                     "但「某个商品的弹性到底是多少」要靠估计需求曲线 —— "
                     "本页用 $q = 10-2p$ 只是为了图形清晰，它不是任何真实商品的需求曲线。"
                     "把模型里的数字当成现实测量值是这一类图最常见的误读。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 索洛增长模型的稳态（① B —— 参数靠估）
# =====================================================================
def build_growth() -> dict:
    s0, n, g, dl, al = 0.2, 0.01, 0.02, 0.07, 0.3
    EXPR_K = "pow(s/(0.01+0.02+0.07), 1/(1-0.3))"
    EXPR_Y = "pow(pow(s/(0.1), 1/(1-0.3)), 0.3)"
    EXPR_INV = "s*pow(pow(s/(0.1), 1/(1-0.3)), 0.3)"
    for s in (0.05, 0.1, 0.2, 0.35, 0.5):
        ks = K.solow_steady(s, n, g, dl, al)
        _agree(f"k*(s={s})", EXPR_K, ks, tol=1e-12, s=s)
        _agree(f"y*(s={s})", EXPR_Y, K.solow_output(s, n, g, dl, al), tol=1e-12, s=s)
        _agree(f"稳态投资(s={s})", EXPR_INV, s * ks ** al, tol=1e-12, s=s)
        _agree(f"  └ 等于持平投资(s={s})", EXPR_INV, (n + g + dl) * ks, tol=1e-12, s=s)
    assert abs(K.solow_steady(s0, n, g, dl, al) - 2.6918) < 1e-3

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "solow", "s": "s", "caption": _evid_badge("B")},
        "param": {"name": "s", "label": "储蓄率 $s$", "min": 0.05, "max": 0.5,
                  "step": 0.005, "value": s0, "unit": "", "standard": s0,
                  "ticks": ["0.05", "0.2 (题设)", "0.5"]},
        "readouts": [
            ro("k", "稳态资本 $k^*$", EXPR_K, 4),
            ro("y", "稳态产出 $y^*$", EXPR_Y, 4),
            ro("inv", "稳态投资 $s\\,y^*$", EXPR_INV, 4),
            ro("dep", "持平投资 $(n+g+\\delta)k^*$", EXPR_INV, 4),
            ro_status("pos", "储蓄率是否偏高（s > 0.35）", "s", 0.35, ">",
                      "储蓄率偏高：稳态资本较大", "储蓄率处于常见区间"),
        ],
        "constant": {"of": "np", "label": "n+g+δ 固定为 0.10；α = 0.3 —— 这些都要估"},
    }
    lesson = {
        "language": "zh-CN", "title": "索洛增长模型的稳态",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>索洛模型 $\\dot k = s f(k) - (n+g+\\delta)k$，"
            "取 $f(k) = k^{\\alpha}$、$\\alpha = 0.3$、$n+g+\\delta = 0.10$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求稳态 $k^*$ 与 $y^*$；</li>"
            "<li>为什么稳态就是两条曲线的交点？</li>"
            "<li>拖动滑块改变储蓄率，稳态怎么移动？</li></ol>"),
        "answerLabel": "$s = 0.2$ 时的稳态",
        "answer": f"$k^* = {K.f(K.solow_steady(s0, n, g, dl, al),4)}$，"
                  f"$y^* = {K.f(K.solow_output(s0, n, g, dl, al),4)}$",
    }
    steps = [
        {"title": "稳态：投资恰好补上折旧与稀释",
         "content": ("<p>人均资本的变化 $\\dot k = \\underbrace{{s f(k)}}_{{投资}} "
                     "- \\underbrace{{(n+g+\\delta)k}}_{{持平投资}}$。</p>"
                     "<p>稳态就是两者的**交点**：$s f(k) = (n+g+\\delta)k$。</p>"
                     "<p>对 $f(k)=k^{{\\alpha}}$ 解得 "
                     "$k^* = \\left(\\dfrac{{s}}{{n+g+\\delta}}\\right)^{{1/(1-\\alpha)}}$。</p>")},
        {"title": "代人计算",
         "content": ("<p>$k^* = \\left(\\dfrac{{0.2}}{{0.10}}\\right)^{{1/0.7}} \\approx 2.6918$，"
                     f"$y^* = (k^*)^{{0.3}} \\approx "
                     f"{K.f(K.solow_output(s0, n, g, dl, al),4)}$。</p>"
                     "<p>注意指数 $1/0.7 \\approx 1.43$ 大于 1："
                     "储蓄率的上升会让稳态资本**超比例**上升，"
                     "但产出只按 $\\alpha$ 的份额受益（$y^* \\propto s^{{\\alpha/(1-\\alpha)}}$）。</p>")},
        {"title": "这一页的证据力（重要）",
         "content": ("<p><b>证据力 ①B</b>：内核完全确定 —— 给定 $s$、$n$、$g$、$\\delta$、$\\alpha$，"
                     "稳态是唯一的、可精确计算的。**但这五个参数全都是估计出来的。**</p>"
                     "<p>所以「某国稳态人均资本是 X」这种说法，"
                     "它的不确定度**不在模型里，在参数里**。"
                     "把 $s$ 从 0.2 拖到 0.3，图上稳态就向右移动不少 —— "
                     "而现实中「储蓄率提高 0.1」本身就是个需要论证的判断，"
                     "不是本图能给出的结论。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) Cobb–Douglas 生产函数（① A —— 欧拉定理是恒等式）
# =====================================================================
def build_cobb_douglas() -> dict:
    A, L, al = 1.0, 9.0, 0.5
    K0 = 4.0
    EXPR_Y = "3*sqrt(K)"
    EXPR_MPK = "1.5/sqrt(K)"
    EXPR_MPL = "sqrt(K)/6"
    EXPR_EULER = "K*(1.5/sqrt(K))+9*(sqrt(K)/6)"
    for Kk in (1.0, 4.0, 9.0, 16.0, 20.0):
        _agree(f"Y(K={Kk})", EXPR_Y, K.cobb_douglas(A, Kk, L, al), tol=1e-12, K=Kk)
        mpk, mpl = K.marginal_products(A, Kk, L, al)
        _agree(f"MPK(K={Kk})", EXPR_MPK, mpk, tol=1e-12, K=Kk)
        _agree(f"MPL(K={Kk})", EXPR_MPL, mpl, tol=1e-12, K=Kk)
        _agree(f"欧拉定理左端(K={Kk})", EXPR_EULER, Kk * mpk + L * mpl, tol=1e-12, K=Kk)
        _agree(f"  └ 等于 Y(K={Kk})", EXPR_EULER, K.cobb_douglas(A, Kk, L, al), tol=1e-12, K=Kk)
    assert abs(K.cobb_douglas(A, K0, L, al) - 6.0) < 1e-12
    assert K.returns_to_scale(al) == "规模报酬不变（指数之和 = 1）"

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "cobb", "K": "K", "caption": _evid_badge("A")},
        "param": {"name": "K", "label": "资本 $K$", "min": 1, "max": 20, "step": 0.25,
                  "value": K0, "unit": "", "standard": K0,
                  "ticks": ["1", "4 (题设)", "20"]},
        "readouts": [
            ro("y", "产出 $Y = A K^\\alpha L^{1-\\alpha}$", EXPR_Y, 5),
            ro("mpk", "资本的边际产量 MPK", EXPR_MPK, 6),
            ro("mpl", "劳动的边际产量 MPL", EXPR_MPL, 6),
            ro("euler", "$K\\cdot MPK + L\\cdot MPL$", EXPR_EULER, 5),
            ro_status("eq", "欧拉定理是否成立（左端 = Y）", EXPR_EULER + "-(" + EXPR_Y + ")",
                      0, "==", "成立（规模报酬不变的必要结果）", "不成立"),
        ],
        "constant": {"of": "al", "label": "A = 1、L = 9、α = 0.5 固定 —— 指数之和恒为 1"},
    }
    lesson = {
        "language": "zh-CN", "title": "Cobb–Douglas 生产函数",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>$Y = A K^{{\\alpha}} L^{{1-\\alpha}}$，"
            "取 $A = 1$、$L = 9$、$\\alpha = 0.5$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求 $Y$、$MPK$、$MPL$；</li>"
            "<li>验证 $K\\cdot MPK + L\\cdot MPL = Y$；</li>"
            "<li>拖动滑块增加 $K$，$MPK$ 怎么变？为什么？</li></ol>"),
        "answerLabel": "$K = 4$ 时的产出与边际产量",
        "answer": f"$Y = {K.f(6.0,1)}$，$MPK = {K.f(0.75,4)}$，$MPL = {K.f(K.marginal_products(1,4,9,0.5)[1],4)}$",
    }
    steps = [
        {"title": "边际产量就是偏导数",
         "content": ("<p>$MPK = \\dfrac{{\\partial Y}}{{\\partial K}} = \\alpha A K^{{\\alpha-1}} L^{{1-\\alpha}} "
                     "= \\alpha\\dfrac{{Y}}{{K}}$；同理 $MPL = (1-\\alpha)\\dfrac{{Y}}{{L}}$。</p>"
                     "<p>后一个等号很漂亮：**边际产量 = 份额 ÷ 存量 × 产出**，"
                     "所以只要知道份额和总量就能算，不必知道函数细节。</p>")},
        {"title": "欧拉定理：把产出恰好分完",
         "content": ("<p>$K\\cdot MPK + L\\cdot MPL = \\alpha Y + (1-\\alpha)Y = Y$。</p>"
                     "<p>它的经济含义是：**按边际产量付给两种要素，恰好把产出分完**，"
                     "不多不少。这要求规模报酬不变（指数之和为 1），"
                     "而 Cobb–Douglas 形式**自动满足**这一点。</p>"
                     "<p>注意这是**恒等式**：滑块怎么动它都成立 —— 图上把左端和 $Y$ 并排显示，"
                     "一旦哪天不等了，就是代码算错了。</p>")},
        {"title": "边际产量递减",
         "content": ("<p>把 $K$ 从 1 拖到 20：$Y$ 上升但**越来越平缓**（$Y \\propto \\sqrt K$），"
                     "$MPK$ 单调下降。</p>"
                     "<p>这就是「边际报酬递减」：其他要素不变时，单一要素越多，"
                     "每多一单位的贡献越小。它是 Cobb–Douglas 在 $\\alpha<1$ 时的必然性质，"
                     "不是经验假设。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 垄断定价（① A —— 纯代数）
# =====================================================================
def build_monopoly() -> dict:
    a, b = 10.0, 1.0
    mc0 = 2.0
    EXPR_Q = "(10-mc)/2"
    EXPR_P = "(10+mc)/2"
    EXPR_PROFIT = "(10-mc)*(10-mc)/4"
    EXPR_LI = "(10-mc)/(10+mc)"
    for mc in (0.5, 1.0, 2.0, 5.0, 8.0):
        q, p = K.monopoly_optimum(a, b, mc)
        _agree(f"q*(mc={mc})", EXPR_Q, float(q), tol=1e-12, mc=mc)
        _agree(f"p*(mc={mc})", EXPR_P, float(p), tol=1e-12, mc=mc)
        _agree(f"利润(mc={mc})", EXPR_PROFIT, float(K.monopoly_profit(a, b, mc)), tol=1e-12, mc=mc)
        li, inv, diff = K.lerner_index(a, b, mc)
        _agree(f"勒纳(mc={mc})", EXPR_LI, float(li), tol=1e-12, mc=mc)
        _agree(f"  └ 等于 1/|ε|(mc={mc})", EXPR_LI, float(inv), tol=1e-12, mc=mc)
    assert float(K.monopoly_optimum(a, b, mc0)[0]) == 4.0
    assert abs(float(K.lerner_index(a, b, mc0)[2])) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "monopoly", "mc": "mc", "caption": _evid_badge("A")},
        "param": {"name": "mc", "label": "边际成本 $MC$", "min": 0.5, "max": 8,
                  "step": 0.1, "value": mc0, "unit": "", "standard": mc0,
                  "ticks": ["0.5", "2 (题设)", "8"]},
        "readouts": [
            ro("q", "垄断产量 $q^*$", EXPR_Q, 4),
            ro("p", "垄断价格 $p^*$", EXPR_P, 4),
            ro("prof", "利润 $(p^*-MC)q^*$", EXPR_PROFIT, 4),
            ro("li", "勒纳指数 $(p-MC)/p$", EXPR_LI, 4),
            ro_status("pos", "是否仍有正产量（MC < a）", "10-mc", 0, ">",
                      "有正产量", "边际成本已高于需求截距，产量为 0"),
        ],
        "constant": {"of": "dem", "label": "需求固定为 p = 10 − q —— 改变 MC 不动它"},
    }
    lesson = {
        "language": "zh-CN", "title": "垄断定价：MR = MC",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>垄断者面对需求 $p = 10 - q$，边际成本恒为 $MC$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出边际收益 $MR$，求最优产量与价格；</li>"
            "<li>验证勒纳指数等于 $1/|\\varepsilon|$；</li>"
            "<li>拖动滑块提高 $MC$，价格怎么变？产量怎么变？</li></ol>"),
        "answerLabel": "$MC = 2$ 时的最优",
        "answer": "$q^* = 4$，$p^* = 6$，利润 $= 16$",
    }
    steps = [
        {"title": "边际收益为什么比需求陡一倍",
         "content": ("<p>收入 $R = pq = (a - bq)q = aq - bq^2$，"
                     "所以 $MR = \\dfrac{{dR}}{{dq}} = a - 2bq$ —— "
                     "截距相同、斜率**翻倍**。</p>"
                     "<p>原因是多卖一单位有两重效果：多赚一单位价格，"
                     "但**所有**已有单位的价格都要下调。前者是一次项，后者是二次项。</p>")},
        {"title": "MR = MC 定产，需求曲线定价",
         "content": ("<p>$a - 2bq = MC \\Rightarrow q^* = \\dfrac{{a-MC}}{{2b}}$，"
                     "再回代需求得 $p^* = \\dfrac{{a+MC}}{{2}}$。</p>"
                     "<p>本例 $q^* = 4$、$p^* = 6$。注意 $p^* > MC$ —— "
                     "这个价差（加成）就是垄断的代价。</p>")},
        {"title": "勒纳指数 = 1/|ε|：一个恒等式",
         "content": ("<p>$\\dfrac{{p-MC}}{{p}} = \\dfrac{{1}}{{|\\varepsilon|}}$。</p>"
                     "<p>它的含义很直观：**需求越缺乏弹性，垄断者能加的价越高**。"
                     "$MC$ 升到 8 时 $p^* = 9$，勒纳指数变成 $1/9$；"
                     "$MC$ 降到 0.5 时 $p^* = 5.25$，勒纳指数 $0.905$ —— 接近 1，"
                     "也就是基本按需求曲线的上限定价。</p>"
                     "<p>证据力 ①A：MR、加成、勒纳指数全是代数恒等式。"
                     "但「现实中的某个市场是不是垄断」「它的需求弹性是多少」"
                     "属于估计与判断，不在本页结论内。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 2×2 纳什均衡（① A —— 有限博弈，穷举即可）
# =====================================================================
def build_nash() -> dict:
    t0 = 1.0
    PAY = lambda t: [[(t, t), (0, 2)], [(2, 0), (1, 1)]]
    EXPR_N = "(t>=2) ? 2 : 1"
    for t in (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0):
        _agree(f"均衡个数(t={t})", EXPR_N, len(K.nash_2x2(PAY(t))), tol=1e-12, t=t)
    assert len(K.nash_2x2(PAY(1.0))) == 1, "t=1 时应当只有 (1,1) 一个均衡"
    assert len(K.nash_2x2(PAY(3.0))) == 2, "t=3 时应当有两个均衡"
    n0 = K.nash_2x2(PAY(t0))
    assert n0 == [(1, 1)]

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "nash", "t": "t", "caption": _evid_badge("A")},
        "param": {"name": "t", "label": "合作成功时的收益 $t$", "min": 0, "max": 4,
                  "step": 0.1, "value": t0, "unit": "", "standard": t0,
                  "ticks": ["0", "1 (题设)", "2 (临界)", "4"]},
        "readouts": [
            ro("n", "纯策略均衡个数", EXPR_N, 0),
            ro("t", "合作收益 $t$", "t", 2),
            ro("thr", "均衡个数变多的临界值", "2", 1),
            ro_status("coop", "是否存在「合作」均衡",
                      "t-2", 0, ">=",
                      "存在（合作与独自都是均衡）", "不存在（只有「独自」是均衡）"),
        ],
        "constant": {"of": "thr", "label": "临界值恒为 2 —— 由收益矩阵而不是估计决定"},
    }
    lesson = {
        "language": "zh-CN", "title": "2×2 纳什均衡：猎鹿博弈",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>两人同时选择「合作」或「独自」。收益矩阵：</p>"
            "<p>合作/合作 $= (t, t)$；独自/独自 $= (1, 1)$；"
            "一方独自另一方合作 $= (2, 0)$ 或 $(0, 2)$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求所有纯策略纳什均衡；</li>"
            "<li>$t$ 取什么值时均衡个数会变化？</li>"
            "<li>为什么「互不信任」会把好结果挤掉？</li></ol>"),
        "answerLabel": "$t = 1$ 时的均衡",
        "answer": "只有（独自, 独自）—— 合作不是均衡",
    }
    steps = [
        {"title": "纳什均衡的判据：双方都用最优反应",
         "content": ("<p>$(i,j)$ 是纳什均衡 $\\iff$ "
                     "$i$ 是行玩家在列选 $j$ 时的最优反应，**且** "
                     "$j$ 是列玩家在行选 $i$ 时的最优反应。</p>"
                     "<p>2×2 博弈只有 4 个格子，**穷举一遍**就完了 —— "
                     "这里不存在算法争议，图上黄格就是判定结果。</p>")},
        {"title": "临界值 2 从哪来",
         "content": ("<p>对「合作」成为最优反应，需要 $t \\ge 2$ —— "
                     "因为对方合作时，你若也合作得 $t$，若独自得 $2$。</p>"
                     "<p>所以 $t < 2$ 时独自是严格占优的，唯一均衡是（独自, 独自）；"
                     "$t \\ge 2$ 时合作也是最优反应，于是**两个均衡并存**。</p>"
                     "<p>拖动滑块越过 $t = 2$，黄格会从 1 个变成 2 个。</p>")},
        {"title": "为什么「多个均衡」本身就是问题",
         "content": ("<p>当两个均衡同时存在，理论**不能**告诉你会落在哪一个 ——"
                     "这依赖预期、默契、历史。"
                     "这正是「猎鹿」的寓意：合作收益更高，"
                     "但只要不能确信对方会合作，独自就是理性的选择。</p>"
                     "<p>证据力 ①A：均衡的**判定**无争议（穷举）。"
                     "但「现实中人们会不会合作」不是博弈论能回答的 —— "
                     "那属于 ①C，需要额外的行为假设，本页不做。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 洛伦兹曲线与基尼系数（① A —— 定积分）
# =====================================================================
def build_gini() -> dict:
    beta0 = 2.0
    EXPR_G = "(beta-1)/(beta+1)"
    EXPR_F20 = "pow(0.2, beta)"
    for bta in (1.0, 1.5, 2.0, 2.5, 3.0):
        _agree(f"基尼(β={bta})", EXPR_G, K.gini_from_beta(bta), tol=1e-12, beta=bta)
        _agree(f"最穷20%份额(β={bta})", EXPR_F20, K.lorenz(0.2, bta), tol=1e-12, beta=bta)
    _agree("β=1 时基尼为 0", EXPR_G, 0.0, tol=1e-12, beta=1.0)
    _agree("β=2 时基尼为 1/3", EXPR_G, 1.0 / 3, tol=1e-12, beta=2.0)
    # 数值积分与解析式一致
    pts = [(i / 2000, K.lorenz(i / 2000, beta0)) for i in range(2001)]
    gnum, _ = K.gini_from_curve(pts)
    assert abs(gnum - K.gini_from_beta(beta0)) < 1e-4

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "lorenz", "beta": "beta", "caption": _evid_badge("A")},
        "param": {"name": "beta", "label": "洛伦兹曲线指数 $\\beta$", "min": 1, "max": 3,
                  "step": 0.05, "value": beta0, "unit": "", "standard": beta0,
                  "ticks": ["1 (完全平等)", "2 (题设)", "3"]},
        "readouts": [
            ro("g", "基尼系数 $\\dfrac{\\beta-1}{\\beta+1}$", EXPR_G, 4),
            ro("f20", "最穷 20% 占有的收入份额", EXPR_F20, 4),
            ro("area", "不平等面积 $A$（= 基尼/2）", EXPR_G + "/2", 4),
            ro("eq", "完全平等线下的面积", "0.5", 4),
            ro_status("eqp", "是否完全平等（β = 1）", "beta-1", 0, "==",
                      "完全平等：洛伦兹曲线就是对角线", "存在不平等"),
        ],
        "constant": {"of": "eq", "label": "完全平等线下的面积恒为 1/2 —— 基尼是它的两倍补数"},
    }
    lesson = {
        "language": "zh-CN", "title": "洛伦兹曲线与基尼系数",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>收入分布由洛伦兹曲线 $L(x) = x^{{\\beta}}$ 描述（$\\beta \\ge 1$，"
            "$x$ 为最穷人口比例）。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求基尼系数；</li>"
            "<li>$\\beta = 1$ 与 $\\beta \\to \\infty$ 分别对应什么？</li>"
            "<li>拖动滑块，为什么曲线越弯基尼越大？</li></ol>"),
        "answerLabel": "基尼系数",
        "answer": "$G = 1 - 2\\displaystyle\\int_0^1 x^{\\beta}dx "
                  "= \\dfrac{\\beta-1}{\\beta+1}$",
    }
    steps = [
        {"title": "洛伦兹曲线与完全平等线",
         "content": ("<p>横轴是最穷的 $x$ 比例人口，纵轴是他们占有的收入累计份额 $L(x)$。</p>"
                     "<p>如果人人相同，$L(x) = x$（图中的对角线）；"
                     "如果越不平等，曲线越向下弯。所以**曲线与对角线之间的面积**"
                     "就是不平等的度量。</p>")},
        {"title": "基尼系数是那个面积的两倍",
         "content": ("<p>对角线下方面积恒为 $\\dfrac{{1}}{{2}}$，"
                     "曲线下方面积为 $\\displaystyle\\int_0^1 x^{{\\beta}}dx = \\dfrac{{1}}{{\\beta+1}}$。</p>"
                     "<p>两者之差是不平等面积 $A$，而基尼系数定义为 $G = 2A$：</p>"
                     "<p>$G = 2\\left(\\dfrac{{1}}{{2}} - \\dfrac{{1}}{{\\beta+1}}\\right) "
                     "= \\dfrac{{\\beta-1}}{{\\beta+1}}$。</p>"
                     "<p>$\\beta = 1$ 给 $G = 0$（完全平等）；$\\beta \\to \\infty$ 时 $G \\to 1$"
                     "（一人占有全部收入）。$\\beta = 2$ 给 $G = 1/3$。</p>")},
        {"title": "这一页的证据力与边界",
         "content": ("<p>证据力 ①A：**给定**洛伦兹曲线，基尼系数是定积分，图上的数错不了；"
                     "画布上那个面积是数值积分现算的，与解析式对过。</p>"
                     "<p>但要清楚：真实的基尼系数是从**收入调查数据**算出来的，"
                     "涉及抽样、口径（税前/税后、个人/家庭）、未申报收入 —— "
                     "这些都不在本页范围。所以这里算的是「度量的定义」，"
                     "不是「某国的不平等程度」。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "supply": build_supply,
    "elasticity": build_elasticity,
    "growth": build_growth,
    "cobb_douglas": build_cobb_douglas,
    "monopoly": build_monopoly,
    "nash": build_nash,
    "gini": build_gini,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="经济学 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
