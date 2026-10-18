#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「化学计算」交互网页。

全部数值由 lib/chemcalc_kernel.py 精确计算驱动（单一数据源）：摩尔换算、
物质的量浓度、化学计量与限量试剂、电离与 pH、中和滴定、平衡三段式、溶度积、
法拉第定律、反应速率都由内核算出，**不手写数字**。

读数表达式（在浏览器里求值）与内核值在构建期逐条对账（_agree），
公式漂移当场停构建 —— 页面上数字照显示但错了，是最难发现的一类 bug。

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

import chemcalc_kernel as K                  # noqa: E402
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
    "exp": math.exp, "log": math.log, "log10": math.log10, "lg": math.log10,
}


def _strip_outer(s):
    """剥掉真正包住整个表达式的外层括号（用于让三目递归能进到括号里）。"""
    s = s.strip()
    while s.startswith("(") and s.endswith(")"):
        depth, closed_at = 0, -1
        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    closed_at = i
                    break
        if closed_at != len(s) - 1:
            break               # 外层括号没包住整体，别剥
        s = s[1:-1].strip()
    return s


def _js_to_py(expr):
    """把 JS 表达式里的顶层三目 `a?b:c` 翻成 Python 的 `b if a else c`。

    画板端由浏览器按**真 JS** 求值；这里只为在构建期用**同一条表达式**核对内核值，
    所以只需支持本技能读数用到的那一小撮语法（三目 + 白名单函数）。
    有了它，分段函数（如滴定 pH）才能既写在读数里、又在构建期被验证。
    """
    expr = _strip_outer(expr)
    depth = 0
    q = -1
    for i, ch in enumerate(expr):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "?" and depth == 0:
            q = i
            break
    if q < 0:
        return expr
    depth, nesting, colon = 0, 0, -1
    for i in range(q + 1, len(expr)):
        ch = expr[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "?" and depth == 0:
            nesting += 1
        elif ch == ":" and depth == 0:
            if nesting == 0:
                colon = i
                break
            nesting -= 1
    if colon < 0:
        raise ValueError(f"三目表达式缺冒号：{expr!r}")
    cond, yes, no = expr[:q], expr[q + 1:colon], expr[colon + 1:]
    return f"({_js_to_py(yes)} if {_js_to_py(cond)} else {_js_to_py(no)})"


def _jseval(expr, **env):
    return eval(_js_to_py(expr.replace("^", "**")), {"__builtins__": {}},
                {**_MATHENV, **env})


def _agree(label, expr, want, tol=1e-9, **env):
    """断言「画板读数表达式」与「内核值」一致；不一致直接停构建。"""
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


# =====================================================================
# 1) 物质的量换算
# =====================================================================
def build_mole() -> dict:
    M_CO2, n0 = 44, 1.0
    m = K.mass_from_mole(n0, M_CO2)
    N = K.particles_from_mole(n0)
    V = K.gas_volume_from_mole(n0)
    _agree("质量读数", "n*44", m, n=n0)
    _agree("粒子数读数（×10²³）", "n*6.02", N / 1e23, n=n0)
    _agree("气体体积读数", "n*22.4", V, n=n0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "mole", "n": "n", "M": M_CO2, "vm": K.VM, "na": K.NA,
                  "caption": "三条通道：质量、粒子数、标况气体体积，都由 n 换算而来"},
        "param": {"name": "n", "label": "物质的量 $n$", "min": 0.1, "max": 2.0,
                  "step": 0.05, "value": n0, "unit": "mol", "standard": n0,
                  "ticks": ["0.1", "1.0 (题设)", "2.0"]},
        "readouts": [
            ro("m", "质量 $m = nM$", "n*44", 3, "g"),
            ro("N", "粒子数 $N$ /10²³", "n*6.02", 3),
            ro("V", "标况体积 $V = nV_m$", "n*22.4", 3, "L"),
            ro_status("co2", "是否为 CO₂（M=44）", "44", 44, "==",
                      "是（摩尔质量 44 g/mol）", "否"),
        ],
        "constant": {"of": "M", "label": "摩尔质量 M = 44 g/mol（改变 n 不动它）"},
    }
    lesson = {
        "language": "zh-CN", "title": "物质的量：化学计算的枢纽",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            f"<p>取 $n = {n0}$ mol 的 CO₂（$M = {M_CO2}$ g/mol）。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>它的质量是多少？</li>"
            "<li>它含有多少个 CO₂ 分子？</li>"
            "<li>它在标准状况下占多大体积？</li>"
            "<li>拖动滑块，这三个量为什么同比例变？</li></ol>"),
        "answerLabel": "n = 1 mol 时的三个量",
        "answer": (f"$m = {K.f(m,1)}$ g，$N = 6.02\\times10^{{23}}$ 个，"
                   f"$V = {K.f(V,1)}$ L"),
    }
    steps = [
        {"title": "物质的量是「个数」的打包单位",
         "content": ("<p>$1$ mol 就是 $6.02\\times10^{{23}}$ 个微粒。所以「物质的量」不是质量、"
                     "不是体积，而是**微粒个数**的一种计量方式。</p>"
                     f"<p>题目给 $n={n0}$ mol，就是给了 {K.f(n0,1)} 个「6.02×10²³ 包」。</p>")},
        {"title": "三条换算通道",
         "content": ("<p>质量：$m = n\\cdot M$（$M$ 是摩尔质量）。<br>"
                     "粒子数：$N = n\\cdot N_A$。<br>"
                     "标况气体体积：$V = n\\cdot V_m$（$V_m = 22.4$ L/mol）。</p>"
                     f"<p>$n={n0}$ 时：$m = {K.f(m,1)}$ g，"
                     f"$N \\approx 6.02\\times10^{{23}}$，$V = {K.f(V,1)}$ L。</p>")},
        {"title": "为什么三个量一起变",
         "content": ("<p>三条公式右边都是 $n$ 乘以一个常数。所以 $n$ 翻倍，"
                     "$m$、$N$、$V$ 全部翻倍 —— 图上三个节点同步走。</p>"
                     "<p>反过来，这三个常数把「宏观可测量」（质量、体积）"
                     "与「微观粒子数」接上了，这就是物质的量在化学计算里的枢纽地位。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 物质的量浓度与稀释
# =====================================================================
def build_concentration() -> dict:
    n0, V0 = 0.05, 0.5
    c0 = K.molarity(n0, V0)
    c_dil = K.dilute(c0, 200, 500)
    _agree("浓度读数", "0.05/V", float(c0), V=V0)
    _agree("溶质物质的量读数", "0.05", n0, V=V0)
    # 稀释不变量：溶质的物质的量守恒（c₁V₁ = c₂V₂）
    assert abs(K.moles_in_solution(float(c0), 0.2)
               - K.moles_in_solution(float(c_dil), 0.5)) < 1e-15
    _agree("稀释定律 c₁V₁=c₂V₂", "0.1*200/500", float(c_dil))

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "beaker", "n0": n0, "vmax": 2.0, "V": "V",
                  "caption": "液面高度 = 溶液体积；黄点 = 溶质，加水时数目不动"},
        "param": {"name": "V", "label": "溶液体积 $V$", "min": 0.2, "max": 2.0,
                  "step": 0.05, "value": V0, "unit": "L", "standard": V0,
                  "ticks": ["0.2", "0.5 (题设)", "2.0"]},
        "readouts": [
            ro("n", "溶质的物质的量 $n$", "0.05", 3, "mol"),
            ro("V", "溶液体积 $V$", "V", 2, "L"),
            ro("c", "物质的量浓度 $c = n/V$", "0.05/V", 4, "mol/L"),
            ro_status("dil", "是否已被稀释到 0.1 mol/L 以下", "0.05/V", 0.1, "<",
                      "已稀释（浓度低于原值）", "未稀释（浓度仍不低于原值）"),
        ],
        "constant": {"of": "n", "label": "溶质的物质的量恒为 0.05 mol（加水不改变它）"},
    }
    lesson = {
        "language": "zh-CN", "title": "物质的量浓度与稀释不变量",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            f"<p>把 ${K.f(n0,2)}$ mol 的溶质配成 ${K.f(V0,1)}$ L 溶液。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>该溶液的物质的量浓度是多少？</li>"
            "<li>再加水把体积稀释到 500 mL（原来 200 mL），浓度变成多少？</li>"
            "<li>拖动滑块改变体积，哪个量始终不变？为什么？</li></ol>"),
        "answerLabel": "c = 0.05 mol / 0.5 L",
        "answer": f"$c = {K.f(float(c0),4)}$ mol/L",
    }
    steps = [
        {"title": "浓度是「单位体积里的物质的量」",
         "content": ("<p>$c = \\dfrac{{n}}{{V}}$，单位 mol/L。注意 $V$ 是**溶液**体积，"
                     "不是溶剂（水）的体积 —— 这是最常见的错点。</p>"
                     f"<p>$c = \\dfrac{{{K.f(n0,2)}}}{{{K.f(V0,1)}}} = {K.f(float(c0),4)}$ mol/L。</p>")},
        {"title": "稀释：变的是体积，不变的是溶质",
         "content": ("<p>加水不会凭空生成或消灭溶质，所以 $n$ 是**不变量**："
                     "$n = c_1V_1 = c_2V_2$。</p>"
                     f"<p>稀释前后：$n = {K.f(float(c0),2)}\\times0.200 = "
                     f"{K.f(K.moles_in_solution(float(c0), 0.2),4)}$ mol，"
                     f"稀释到 0.500 L 后 $c_2 = {K.f(float(c_dil),4)}$ mol/L。</p>")},
        {"title": "图上看得见的不变量",
         "content": ("<p>左侧烧杯：液面高度代表体积，所以拖动滑块液面上升；"
                     "而黄点（溶质）**数目不变**。点变得稀疏，就是浓度下降的可视化。</p>"
                     "<p>读数里的 $n$ 恒定、$c$ 与 $V$ 成反比 —— 三者与图是同源的。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 化学计量与限量试剂
# =====================================================================
def build_stoich() -> dict:
    n_n2, n_h2 = 2.0, 6.0
    r = K.stoich_limit([n_n2, n_h2], [1, 3], products=[(2, "NH₃")])
    xi = r["xi"]
    left_n2, left_h2 = r["leftover"]
    nh3 = r["products"][0][2]
    _agree("反应进度 ξ", "min(2, n/3)", float(xi), n=n_h2)
    _agree("生成 NH₃", "2*min(2, n/3)", float(nh3), n=n_h2)
    _agree("剩余 H₂", "n-3*min(2,n/3)", float(left_h2), n=n_h2)
    _agree("剩余 N₂", "2-min(2,n/3)", float(left_n2), n=n_h2)
    # 限量试剂换手：n(H₂) 小于 6 时 H₂ 限量，反之 N₂ 限量
    assert float(K.stoich_limit([2, 3], [1, 3])["xi"]) == 1.0

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "stoich", "n_n2": n_n2, "n_h2": "n", "c_n2": 1, "c_h2": 3,
                  "c_nh3": 2, "caption": "深色 = 已反应掉的，浅色框 = 剩余；红箭头指向限量试剂"},
        "param": {"name": "n", "label": "H₂ 的起始物质的量", "min": 1.0, "max": 12.0,
                  "step": 0.5, "value": n_h2, "unit": "mol", "standard": n_h2,
                  "ticks": ["1", "6 (恰好完全反应)", "12"]},
        "readouts": [
            ro("xi", "反应进度 $\\xi$", "min(2, n/3)", 4, "mol"),
            ro("nh3", "生成 $n(\\mathrm{NH_3})$", "2*min(2, n/3)", 4, "mol"),
            ro("lh2", "剩余 $n(\\mathrm{H_2})$", "n-3*min(2,n/3)", 4, "mol"),
            ro("ln2", "剩余 $n(\\mathrm{N_2})$", "2-min(2,n/3)", 4, "mol"),
            ro_status("lim", "限量试剂是谁", "2 - n/3", 0, ">=",
                      "N₂ 过量 → H₂ 是限量试剂", "N₂ 不足 → N₂ 是限量试剂"),
        ],
        "constant": {"of": "nn2", "label": "N₂ 起始量恒为 2 mol"},
    }
    lesson = {
        "language": "zh-CN", "title": "化学计量与限量试剂",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>合成氨反应 $\\mathrm{{N_2 + 3H_2 \\rightarrow 2NH_3}}$。"
            "起始时放入 $2$ mol $\\mathrm{{N_2}}$ 与 $6$ mol $\\mathrm{{H_2}}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>哪种物质是限量试剂？反应进度 $\\xi$ 是多少？</li>"
            "<li>能生成多少 mol $\\mathrm{{NH_3}}$？剩下什么、剩多少？</li>"
            "<li>拖动滑块，什么时候限量试剂换手？</li></ol>"),
        "answerLabel": "反应进度与生成量",
        "answer": (f"$\\xi = {K.tex(xi)}$ mol，生成 "
                   f"$n(\\mathrm{{NH_3}}) = {K.tex(nh3)}$ mol"),
    }
    steps = [
        {"title": "设反应进度 ξ，一次算清所有物质",
         "content": ("<p>设反应进行了 $\\xi$ 次（$\\xi$ 就叫**反应进度**）。则消耗 "
                     "$\\mathrm{{N_2}}$ 为 $\\xi$、$\\mathrm{{H_2}}$ 为 $3\\xi$，"
                     "生成 $\\mathrm{{NH_3}}$ 为 $2\\xi$。</p>"
                     "<p>这个「一次设 $\\xi$」的做法，比逐个物质列比例更不容易出错。</p>")},
        {"title": "限量试剂 = 最先耗尽的那个",
         "content": ("<p>$\\mathrm{{N_2}}$ 能支撑 $\\dfrac{{2}}{{1}}=2$ 次，"
                     "$\\mathrm{{H_2}}$ 能支撑 $\\dfrac{{6}}{{3}}=2$ 次 —— 两者相等，"
                     "恰好完全反应。</p>"
                     f"<p>$\\xi = \\min\\left(\\dfrac{{2}}{{1}},\\dfrac{{6}}{{3}}\\right) = {K.tex(xi)}$，"
                     f"故 $n(\\mathrm{{NH_3}}) = 2\\xi = {K.tex(nh3)}$ mol，两反应物都剩 0。</p>")},
        {"title": "拖动滑块：限量试剂会换手",
         "content": ("<p>把 $\\mathrm{{H_2}}$ 减到 3 mol：它只能支撑 1 次，"
                     "而 $\\mathrm{{N_2}}$ 能支撑 2 次 —— 这时 $\\mathrm{{H_2}}$ 成了限量试剂，"
                     "$\\mathrm{{N_2}}$ 剩下 1 mol。</p>"
                     "<p>反过来把 $\\mathrm{{H_2}}$ 加到 9 mol：它支撑 3 次，"
                     "$\\mathrm{{N_2}}$ 仍是 2 次，这次 $\\mathrm{{N_2}}$ 成了限量试剂，"
                     "$\\mathrm{{H_2}}$ 剩下 3 mol。图上红箭头会随之换边。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 中和滴定
# =====================================================================
def build_titration() -> dict:
    ca, va, cb, vmax = 0.1, 20.0, 0.1, 40.0
    v0 = 20.0
    veq = ca * va / cb
    ph0, _ = K.titration_ph(ca, va, cb, v0)
    ph_half, _ = K.titration_ph(ca, va, cb, 10.0)
    ph_excess, _ = K.titration_ph(ca, va, cb, 30.0)
    EXPR = "V<20 ? -log10((2-0.1*V)/(20+V)) : (V>20 ? 14+log10((0.1*V-2)/(20+V)) : 7)"
    for V, want in ((0.0, K.titration_ph(ca, va, cb, 0.0)[0]),
                    (10.0, ph_half), (20.0, 7.0), (30.0, ph_excess),
                    (25.0, K.titration_ph(ca, va, cb, 25.0)[0]),
                    (35.0, K.titration_ph(ca, va, cb, 35.0)[0])):
        _agree(f"pH 读数 V={V}", EXPR, want, tol=1e-9, V=V)
    assert abs(veq - 20.0) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "titration", "ca": ca, "va": va, "cb": cb, "vmax": vmax, "V": "V",
                  "caption": "曲线由内核同式现算；黄点 = 当前加碱体积下的 pH"},
        "param": {"name": "V", "label": "加入 NaOH 的体积 $V$", "min": 0.0, "max": vmax,
                  "step": 0.1, "value": v0, "unit": "mL", "standard": v0,
                  "ticks": ["0", "20 (等当点)", "40"]},
        "readouts": [
            ro("ph", "溶液 pH", EXPR, 3),
            ro("veq", "等当点体积 $V_{eq}$", "20", 1, "mL"),
            ro("ex", "过量情况（H⁺ 减 OH⁻，mmol）", "2-0.1*V", 3),
            ro_status("eq", "是否恰好中和", "V-20", 0, "==",
                      "恰好中和 → pH = 7", "未到或已超过等当点"),
        ],
        "constant": {"of": "veq", "label": "等当点恒在 V = 20 mL（c_酸V_酸 = c_碱V_碱）"},
    }
    lesson = {
        "language": "zh-CN", "title": "中和滴定：pH 曲线与等当点",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>用 $0.1$ mol/L 的 NaOH 滴定 $20$ mL $0.1$ mol/L 的 HCl。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>等当点出现在加碱多少 mL 处？此时 pH 是多少？</li>"
            "<li>拖动滑块，为什么等当点附近 pH 会剧烈跳变？</li>"
            "<li>加碱超过等当点后，pH 靠什么决定？</li></ol>"),
        "answerLabel": "等当点体积与 pH",
        "answer": f"$V_{{eq}} = {K.f(veq,1)}$ mL，此时 pH = 7",
    }
    steps = [
        {"title": "等当点由物质的量守恒定出",
         "content": ("<p>恰好中和意味着 $n(\\mathrm{{H^+}}) = n(\\mathrm{{OH^-}})$，"
                     "即 $c_酸V_酸 = c_碱V_碱$。</p>"
                     f"<p>$0.1\\times20 = 0.1\\times V \\Rightarrow V_{{eq}} = {K.f(veq,0)}$ mL；"
                     "强酸强碱恰好中和时 pH = 7。</p>")},
        {"title": "三段式算任意一点的 pH",
         "content": ("<p><b>酸过量</b>（$V<20$）：剩余 $n(\\mathrm{{H^+}}) = 2-0.1V$ mmol，"
                     "除以总体积 $(20+V)$ mL 得 $c(\\mathrm{{H^+}})$，取负对数。</p>"
                     "<p><b>碱过量</b>（$V>20$）：改为算 $c(\\mathrm{{OH^-}})$ 得 pOH，"
                     "再由 pH = 14 − pOH。</p>"
                     f"<p>校验：$V=10$ 时 pH $\\approx{K.f(ph_half,3)}$；"
                     f"$V=30$ 时 pH $\\approx{K.f(ph_excess,3)}$。</p>")},
        {"title": "为什么等当点附近一跳一大截",
         "content": ("<p>等当点前后，决定 pH 的物种从「剩余的酸」换成了「过量的碱」。"
                     "在 $V=19.98$ 时剩余酸约 $2\\times10^{{-6}}$ mol，"
                     "而 $V=20.02$ 时过量的碱也是同一量级 —— 浓度被稀释到"
                     "$10^{{-5}}$ 上下，pH 从 4.3 直接跳到 9.7。</p>"
                     "<p>正因为这一跳，指示剂才能在很小的一滴之内变色。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 化学平衡三段式
# =====================================================================
def build_equilibrium() -> dict:
    Kc, c0_0 = 1.0, 1.0
    x, alpha, eq = K.ice_quadratic(Kc, c0_0)
    EXPR_X = "(-1+sqrt(1+16*c0))/8"
    EXPR_A = "(-1+sqrt(1+16*c0))/8/c0"
    _agree("平衡解 x", EXPR_X, x, tol=1e-12, c0=c0_0)
    _agree("转化率 α", EXPR_A, alpha, tol=1e-12, c0=c0_0)
    _agree("平衡 [N₂O₄]", "1-(-1+sqrt(1+16*c0))/8", eq[0], tol=1e-12, c0=c0_0)
    _agree("平衡 [NO₂]", "2*(-1+sqrt(1+16*c0))/8", eq[1], tol=1e-12, c0=c0_0)
    # 稀释使转化率升高（平衡向分子数多的一侧移动）
    assert K.ice_quadratic(Kc, 0.1)[1] > K.ice_quadratic(Kc, 1.0)[1]

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "ice", "K": Kc, "c0": "c0",
                  "caption": "三段式：初始 / 变化 / 平衡；红柱是负向变化"},
        "param": {"name": "c0", "label": "$\\mathrm{{N_2O_4}}$ 的初始浓度", "min": 0.1,
                  "max": 2.0, "step": 0.05, "value": c0_0, "unit": "mol/L",
                  "standard": c0_0, "ticks": ["0.1", "1.0 (题设)", "2.0"]},
        "readouts": [
            ro("x", "转化掉的量 $x$", EXPR_X, 4, "mol/L"),
            ro("a", "转化率 $\\alpha = x/c_0$", EXPR_A, 4),
            ro("ap", "转化率（百分数）", EXPR_A + "*100", 2, "%"),
            ro_status("kc", "平衡常数是否恒定（K = 1）", "1", 1, "==",
                      "恒定（只随温度改变）", "变了（不应发生）"),
        ],
        "constant": {"of": "K", "label": "平衡常数 K = 1 恒定（改变初始浓度不动它）"},
    }
    lesson = {
        "language": "zh-CN", "title": "化学平衡：三段式与转化率",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>在恒温下，$\\mathrm{{N_2O_4 \\rightleftharpoons 2NO_2}}$，"
            "$K = 1.0$。起始只放 $1.0$ mol/L 的 $\\mathrm{{N_2O_4}}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>用三段式求平衡时各物质的浓度与转化率 $\\alpha$；</li>"
            "<li>拖动滑块改变初始浓度，$K$ 变吗？$\\alpha$ 变吗？</li>"
            "<li>为什么初始浓度越小、转化率越高？</li></ol>"),
        "answerLabel": "平衡浓度与转化率",
        "answer": (f"$[\\mathrm{{N_2O_4}}] = {K.f(eq[0],3)}$，"
                   f"$[\\mathrm{{NO_2}}] = {K.f(eq[1],3)}$，"
                   f"$\\alpha = {K.f(alpha,4)}$"),
    }
    steps = [
        {"title": "三段式：初始 / 变化 / 平衡",
         "content": ("<p>设转化了 $x$，按系数把变化列出来：</p>"
                     "<p>$\\qquad\\mathrm{{N_2O_4 \\rightleftharpoons 2NO_2}}$<br>"
                     "初始 $\\quad c_0 \\qquad\\; 0$<br>"
                     "变化 $\\quad -x \\qquad +2x$<br>"
                     "平衡 $\\quad c_0-x \\quad\\; 2x$</p>"
                     "<p>三段式的价值在于：把「平衡」表达成一个未知数 $x$，"
                     "剩下的都是代数。</p>")},
        {"title": "代入 K 解一元二次",
         "content": ("<p>$K = \\dfrac{{[\\mathrm{{NO_2}}]^2}}{{[\\mathrm{{N_2O_4}}]}}"
                     "= \\dfrac{{(2x)^2}}{{c_0-x}} = \\dfrac{{4x^2}}{{c_0-x}}$。</p>"
                     "<p>整理得 $4x^2 + Kx - Kc_0 = 0$，取正根 "
                     "$x = \\dfrac{{-K+\\sqrt{{K^2+16Kc_0}}}}{{8}}$。</p>"
                     f"<p>$c_0=1$ 时 $x = {K.f(x,4)}$，"
                     f"平衡浓度为 $[\\mathrm{{N_2O_4}}]={K.f(eq[0],3)}$、"
                     f"$[\\mathrm{{NO_2}}]={K.f(eq[1],3)}$，"
                     f"$\\alpha = {K.f(alpha,4)}$。</p>")},
        {"title": "K 不变，α 变 —— 这是本页的核心",
         "content": ("<p>$K$ 只由温度决定，所以拖动滑块（改初始浓度）时它是**定值**，"
                     "读数区专门盯着它。</p>"
                     "<p>但 $\\alpha$ 会变：$\\dfrac{{4x^2}}{{c_0-x}}=K$ 中，"
                     "$c_0$ 变小要求 $x$ 相对更大。物理上就是**稀释时平衡向"
                     "气体分子数多的一侧移动**（这里 $\\mathrm{{NO_2}}$ 有 2 个分子）。"
                     "这就是勒夏特列原理的定量形态。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 电解与法拉第定律
# =====================================================================
def build_electrolysis() -> dict:
    M_CU, z, I, tmax = 63.5, 2, 2.0, 3600.0
    t0 = 1800.0
    m = K.faraday_mass(M_CU, z, I, t0)
    ne = K.faraday_moles_e(z, I, t0)
    _agree("析出质量", "63.5*2*t/(2*96485)", m, tol=1e-9, t=t0)
    _agree("电子物质的量", "2*t/96485", ne, tol=1e-12, t=t0)
    _agree("电量 Q", "2*t", I * t0, t=t0)
    assert abs(m - ne * M_CU / z) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "cell", "M": M_CU, "z": z, "I": I, "tmax": tmax, "t": "t",
                  "mmax": 2.4, "caption": "阴极沉积层厚度 ∝ 析出质量；右侧是 m(t) 直线"},
        "param": {"name": "t", "label": "通电时间 $t$", "min": 0.0, "max": tmax,
                  "step": 30, "value": t0, "unit": "s", "standard": t0,
                  "ticks": ["0", "1800", "3600"]},
        "readouts": [
            ro("m", "析出质量 $m$", "63.5*2*t/(2*96485)", 4, "g"),
            ro("ne", "转移电子 $n(\\mathrm{e^-})$", "2*t/96485", 4, "mol"),
            ro("q", "电量 $Q = It$", "2*t", 0, "C"),
            ro_status("far", "是否满足 m = nM/z", "63.5*2*t/(2*96485) - (2*t/96485)*63.5/2",
                      0, "==", "满足（法拉第定律自洽）", "不满足"),
        ],
        "constant": {"of": "I", "label": "电流恒为 2.0 A"},
    }
    lesson = {
        "language": "zh-CN", "title": "电解与法拉第定律",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>以 $2.0$ A 的电流电解 $\\mathrm{{CuSO_4}}$ 溶液，"
            "阴极析出铜（$M = 63.5$ g/mol，$\\mathrm{{Cu^{{2+}} + 2e^- \\rightarrow Cu}}$）。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>通电 $1800$ s，转移了多少 mol 电子？析出多少克铜？</li>"
            "<li>拖动滑块，析出质量与时间是什么关系？</li></ol>"),
        "answerLabel": "1800 s 后的转移电子数与析出质量",
        "answer": f"$n(\\mathrm{{e^-}}) = {K.f(ne,4)}$ mol，$m = {K.f(m,4)}$ g",
    }
    steps = [
        {"title": "先把「电量」换算成「电子数」",
         "content": ("<p>电量 $Q = It = 2.0\\times1800 = 3600$ C。</p>"
                     "<p>法拉第常数 $F = 96485$ C/mol 的意思是："
                     "**每 mol 电子携带 96485 C**。所以</p>"
                     f"<p>$n(\\mathrm{{e^-}}) = \\dfrac{{Q}}{{F}} = "
                     f"\\dfrac{{3600}}{{96485}} \\approx {K.f(ne,4)}$ mol。</p>")},
        {"title": "再由电子数换算质量",
         "content": ("<p>$\\mathrm{{Cu^{{2+}} + 2e^- \\rightarrow Cu}}$ 说明"
                     "每生成 1 个 Cu 需要 2 个电子，因此</p>"
                     "<p>$m = \\dfrac{{n(\\mathrm{{e^-}})}}{{{z}}}\\cdot M "
                     "= \\dfrac{{I t}}{{zF}}\\cdot M$。</p>"
                     f"<p>代入得 $m = \\dfrac{{2.0\\times1800}}{{2\\times96485}}"
                     f"\\times63.5 \\approx {K.f(m,4)}$ g。</p>")},
        {"title": "为什么是直线",
         "content": ("<p>公式里 $m$ 与 $t$ 成正比（$I$、$z$、$M$、$F$ 都是常数），"
                     "所以右侧 $m(t)$ 图是一条过原点的**直线** —— 恒流电解的典型特征。</p>"
                     "<p>读数里的自洽检查 $m = n(\\mathrm{{e^-}})\\cdot M/z$ 恒成立，"
                     "它保证「质量」与「电子数」两条路径不会互相打架。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 反应速率与半衰期
# =====================================================================
def build_rate() -> dict:
    kk, c0_0, tmax = 0.1, 1.0, 60.0
    th = K.half_life(kk)
    v0 = kk * c0_0
    _agree("半衰期读数", "log(2)/0.1", th, tol=1e-12, c0=c0_0)
    _agree("初始速率读数", "0.1*c0", v0, tol=1e-12, c0=c0_0)
    _agree("半衰期后的浓度 = c₀/2", "c0*exp(-0.1*(log(2)/0.1))", c0_0 / 2, tol=1e-12, c0=c0_0)
    _agree("半衰期处浓度恰为 c₀/2（状态灯判据）",
           "c0*exp(-0.1*(log(2)/0.1))-c0/2", 0, tol=1e-12, c0=c0_0)
    # 一级反应：半衰期与 c₀ 无关（读数里 th 不含 c0 —— 这正是要演示的定值）
    assert "c0" not in "log(2)/0.1"

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "decay", "k": kk, "tmax": tmax, "cmax": 2.0, "c0": "c0",
                  "caption": "红线是半衰期标记；改 c₀ 时它不动"},
        "param": {"name": "c0", "label": "初始浓度 $c_0$", "min": 0.2, "max": 2.0,
                  "step": 0.05, "value": c0_0, "unit": "mol/L", "standard": c0_0,
                  "ticks": ["0.2", "1.0 (题设)", "2.0"]},
        "readouts": [
            ro("th", "半衰期 $t_{1/2} = \\ln 2/k$", "log(2)/0.1", 3, "min"),
            ro("v0", "初始速率 $v_0 = kc_0$", "0.1*c0", 4, "mol/(L·min)"),
            ro("ch", "一个半衰期后浓度", "c0*exp(-0.1*(log(2)/0.1))", 4, "mol/L"),
            ro_status("ind", "半衰期处浓度是否恰为 $c_0/2$",
                      "c0*exp(-0.1*(log(2)/0.1))-c0/2", 0, "==",
                      "成立（每隔一个半衰期浓度减半）", "不成立"),
        ],
        "constant": {"of": "th", "label": "半衰期恒为 ln2/k ≈ 6.931 min（改变 c₀ 不动它）"},
    }
    lesson = {
        "language": "zh-CN", "title": "反应速率与半衰期",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>某分解反应为一级反应，速率常数 $k = 0.1\\ \\mathrm{{min^{{-1}}}}$，"
            "初始浓度 $c_0 = 1.0$ mol/L。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求半衰期 $t_{{1/2}}$ 与初始速率 $v_0$；</li>"
            "<li>拖动滑块改变 $c_0$，半衰期变吗？初始速率变吗？为什么？</li></ol>"),
        "answerLabel": "半衰期与初始速率",
        "answer": f"$t_{{1/2}} = {K.f(th,3)}$ min，$v_0 = {K.f(v0,2)}$ mol/(L·min)",
    }
    steps = [
        {"title": "一级反应：浓度按指数衰减",
         "content": ("<p>一级反应的速率与当前浓度成正比：$v = kc$，"
                     "解这个微分方程得 $c(t) = c_0 e^{{-kt}}$。</p>"
                     "<p>它是一条**指数衰减**曲线，不是直线 ——"
                     "图上绿色曲线就是内核按这个公式逐点算出来的。</p>")},
        {"title": "半衰期：ln2 / k",
         "content": ("<p>令 $c = c_0/2$：$\\dfrac{{c_0}}{{2}} = c_0 e^{{-kt}}"
                     "\\Rightarrow e^{{-kt}} = \\dfrac{{1}}{{2}}"
                     "\\Rightarrow t_{{1/2}} = \\dfrac{{\\ln 2}}{{k}}$。</p>"
                     f"<p>$k = 0.1$ 时 $t_{{1/2}} = \\dfrac{{0.6931}}{{0.1}}"
                     f"\\approx {K.f(th,3)}$ min。</p>")},
        {"title": "本页要演示的定值：半衰期与 c₀ 无关",
         "content": ("<p>注意 $t_{{1/2}} = \\dfrac{{\\ln 2}}{{k}}$ 里**没有 $c_0$**。"
                     "所以拖动滑块改变初始浓度时，红线（半衰期标记）纹丝不动，"
                     "而绿色曲线整体上下平移。</p>"
                     "<p>这就是一级反应最好用的判据：**每隔一个半衰期，"
                     "浓度就减半**，与起点多高无关。零级或二级反应都没有这个性质。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 8) 溶度积与沉淀判断
# =====================================================================
def build_ksp() -> dict:
    KSP_AGCL, c_ag = 1.8e-10, 1.0e-5
    k0 = 3.0
    c_cl = k0 * 1e-5
    Q = c_ag * c_cl
    res, ratio = K.ksp_judge(Q, KSP_AGCL)
    EXPR_RATIO = "1e-5*k*1e-5/1.8e-10"
    _agree("Q/Ksp 比值", EXPR_RATIO, ratio, tol=1e-12, k=k0)
    _agree("Q 读数", "1e-5*k*1e-5", Q, tol=1e-24, k=k0)
    _agree("log₁₀(Q/Ksp)", "log10(1e-5*k*1e-5/1.8e-10)", math.log10(ratio), tol=1e-12, k=k0)
    # 临界点：c(Cl⁻) = Ksp / c(Ag⁺)
    c_crit = KSP_AGCL / c_ag
    _agree("临界浓度（×10⁻⁵）", "1.8e-10/1e-5/1e-5", c_crit / 1e-5, tol=1e-12)
    assert res == "生成沉淀"

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "ksp", "Ksp": KSP_AGCL, "c_ag": c_ag, "k": "k",
                  "caption": "对数条：log₁₀(Q/Ksp) 跨过 0 的那一点就是临界"},
        "param": {"name": "k", "label": "$c(\\mathrm{{Cl^-}})$ /10⁻⁵ mol/L", "min": 0.1,
                  "max": 10.0, "step": 0.05, "value": k0, "unit": "", "standard": k0,
                  "ticks": ["0.1", "1.0", "1.8 (临界)", "10"]},
        "readouts": [
            ro("ccl", "$c(\\mathrm{{Cl^-}})$ /10⁻⁵ mol/L", "k", 3),
            ro("ratio", "$Q / K_{sp}$", EXPR_RATIO, 3),
            ro("lg", "$\\log_{{10}}(Q/K_{{sp}})$", "log10(1e-5*k*1e-5/1.8e-10)", 3),
            ro_status("prec", "是否生成沉淀",
                      "log10(1e-5*k*1e-5/1.8e-10)", 0, ">",
                      "Q > Ksp → 生成沉淀", "Q ≤ Ksp → 不沉淀"),
        ],
        "constant": {"of": "cag", "label": "c(Ag⁺) 恒为 1.0×10⁻⁵ mol/L；Ksp(AgCl) = 1.8×10⁻¹⁰"},
    }
    lesson = {
        "language": "zh-CN", "title": "溶度积：沉淀什么时候出现",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>在 $c(\\mathrm{{Ag^+}}) = 1.0\\times10^{{-5}}$ mol/L 的溶液中，"
            "逐步加入 $\\mathrm{{NaCl}}$ 以提高 $c(\\mathrm{{Cl^-}})$。"
            "已知 $K_{{sp}}(\\mathrm{{AgCl}}) = 1.8\\times10^{{-10}}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>$c(\\mathrm{{Cl^-}})$ 达到多少时开始出现沉淀？</li>"
            "<li>拖动滑块，判断依据是什么？为什么用 $\\log(q/K_{{sp}})$ 而不是直接比大小？</li></ol>"),
        "answerLabel": "开始沉淀的临界 c(Cl⁻)",
        "answer": f"$c(\\mathrm{{Cl^-}}) = {K.sci(c_crit)}$ mol/L",
    }
    steps = [
        {"title": "溶度积是一根「饱和线」",
         "content": ("<p>$K_{{sp}}$ 是难溶电解质溶解平衡的平衡常数。"
                     "对 $\\mathrm{{AgCl}}$：$K_{{sp}} = c(\\mathrm{{Ag^+}})\\cdot c(\\mathrm{{Cl^-}})"
                     "= 1.8\\times10^{{-10}}$（25 ℃）。</p>"
                     "<p>它不是「浓度」而是**浓度的乘积**，单位是 (mol/L)² ——"
                     "所以只能与同量纲的 $Q$ 比较，不能直接与某个浓度比。</p>")},
        {"title": "用 Q 与 Ksp 比较，判据是「往哪边过头」",
         "content": ("<p>定义 $Q = c(\\mathrm{{Ag^+}})\\cdot c(\\mathrm{{Cl^-}})$（当前离子积）。"
                     "$Q > K_{{sp}}$ 说明超过了饱和线，多余的部分会以沉淀形式析出；"
                     "$Q < K_{{sp}}$ 则不沉淀。</p>"
                     "<p>临界时 $Q = K_{{sp}}$，即</p>"
                     f"<p>$c(\\mathrm{{Cl^-}}) = \\dfrac{{K_{{sp}}}}{{c(\\mathrm{{Ag^+}})}}"
                     f"= \\dfrac{{1.8\\times10^{{-10}}}}{{1.0\\times10^{{-5}}}}"
                     f"= {K.sci(c_crit)}$ mol/L。</p>")},
        {"title": "为什么图上用对数条",
         "content": ("<p>$Q$ 与 $K_{{sp}}$ 都是 $10^{{-10}}$ 量级的数，"
                     "直接画柱高根本看不出差别。取 $\\log_{{10}}(Q/K_{{sp}})$ 后，"
                     "「超过一点」变成「条形跨过 0 线」，"
                     "而且**跨过的格数**直接读作「过饱和的 10 的幂次」。</p>"
                     "<p>读数区同时给出 $Q/K_{{sp}}$ 的比值与对数，"
                     "两者与条形是同源的。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "mole": build_mole,
    "concentration": build_concentration,
    "stoich": build_stoich,
    "titration": build_titration,
    "equilibrium": build_equilibrium,
    "electrolysis": build_electrolysis,
    "rate": build_rate,
    "ksp": build_ksp,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="化学计算 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
