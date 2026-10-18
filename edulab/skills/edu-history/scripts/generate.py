#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「可算的历史」交互网页。

**本技能与别的技能最大的不同**：每一页都带一个**证据力徽章**，显式声明这张图
能证明到什么程度。因为历史学的大部分内容落在「③ 配图」层，可算的只有模型与恒等式；
而其中「参数靠估」和「可被拟合」的两类**看起来和推导一模一样** —— 不标注就是误导。

    A  纯数学 / 恒等式     —— 图上的数错不了
    B  模型：参数靠估      —— 曲线光滑，但峰值取决于你怎么估参数
    C  形态①、证据力③     —— 能算能画，但结论可以被拟合出来（最危险）

全部数值由 lib/hist_kernel.py 计算驱动，**不手写数字**；基准值取自
edulab/coverage-audit.md（那份审计已现算过），所以自检验的是「实现与审计一致」。

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

import hist_kernel as K                      # noqa: E402
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


def _evid_badge(level):
    tag, note = K.EVIDENCE[level]
    return f"证据力 {level}｜{tag} —— {note}"


# =====================================================================
# 1) 指数增长与翻倍时间（① A）
# =====================================================================
def build_growth() -> dict:
    r0 = 0.07
    td = K.doubling_time(r0)
    _agree("翻倍时间", "log(2)/r", td, tol=1e-12, r=r0)
    _agree("10 年倍数", "exp(r*10)", K.exponential(1.0, r0, 10), tol=1e-12, r=r0)
    _agree("30 年倍数", "exp(r*30)", K.exponential(1.0, r0, 30), tol=1e-12, r=r0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "expcurve", "r": "r", "tmax": 100,
                  "caption": _evid_badge("A")},
        "param": {"name": "r", "label": "年增长率 $r$", "min": 0.005, "max": 0.10,
                  "step": 0.005, "value": r0, "unit": "", "standard": r0,
                  "ticks": ["0.5%", "7% (近现代高增长)", "10%"]},
        "readouts": [
            ro("td", "翻倍时间 $\\ln 2/r$", "log(2)/r", 3, "年"),
            ro("y10", "10 年后的倍数", "exp(r*10)", 3, "×"),
            ro("y30", "30 年后的倍数", "exp(r*30)", 2, "×"),
            ro_status("fast", "翻倍时间是否短于 20 年", "log(2)/r", 20, "<",
                      "20 年内翻倍（高增长）", "超过 20 年才翻倍"),
        ],
        "constant": {"of": "ln2", "label": "翻倍时间与起点无关 —— 只由 r 决定"},
    }
    lesson = {
        "language": "zh-CN", "title": "指数增长与翻倍时间",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>某经济体人均产出以年增长率 $r$ 持续增长。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>当 $r = 7\\%$ 时，多少年翻一番？</li>"
            "<li>拖动滑块，翻倍时间与<b>起点</b>有关吗？为什么？</li>"
            "<li>为什么「长期增长率」是理解历史的最重要指标之一？</li></ol>"),
        "answerLabel": "$r = 7\\%$ 时的翻倍时间",
        "answer": f"$\\approx {K.f(td,1)}$ 年",
    }
    steps = [
        {"title": "连续增长写成指数",
         "content": ("<p>若每单位时间按固定比例增长，$y(t) = y_0 e^{rt}$。</p>"
                     "<p>指数增长的反直觉之处：<b>绝对增量在加速</b>（今天涨得比昨天多），"
                     "但<b>相对速度恒定</b>。后者才是「增长率」的含义。</p>")},
        {"title": "翻倍时间 = ln2 / r",
         "content": ("<p>令 $y = 2y_0$：$2 = e^{rt} \\Rightarrow t = \\dfrac{\\ln 2}{r}$。</p>"
                     f"<p>$r = 7\\%$ 时 $t = \\dfrac{{0.6931}}{{0.07}} \\approx {K.f(td,1)}$ 年。</p>"
                     "<p>注意公式里<b>没有 $y_0$</b> —— 所以无论起点是 100 还是 10000，"
                     "翻倍都花同样的年头。拖动滑块可以看到：曲线整体上下移动，"
                     "而粉色翻倍标记的<b>位置不变</b>。</p>")},
        {"title": "为什么它改变了历史学的写法",
         "content": ("<p>在工业化之前，人均产出的增长近乎为零；一旦进入 1–2% 的持续增长，"
                     "几十年就是人类此前几千年累积的差距。</p>"
                     "<p>所以「长期增长率」把历史从<b>事件序列</b>变成了"
                     "<b>可比较的量的过程</b> —— 这正是 ① 层能提供的东西。</p>"
                     "<p><b>但要看清这一页的证据力</b>：它是 ①A（纯数学恒等式），"
                     "图上任何一个数都错不了。而「某国某年增长率到底是多少」"
                     "属于史料估算，不是本页能回答的。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 人口转变（① B —— 参数靠估）
# =====================================================================
def build_transition() -> dict:
    b0, b1, d0, d1, mid_d, steep = 45.0, 10.0, 35.0, 10.0, 1920.0, 15.0
    mid_b0, YEAR = 1950.0, 2000
    b, d, g = K.transition_rate_at(YEAR, b0, b1, d0, d1, mid_d, mid_b0, steep)
    tr = K.demographic_transition(b0, b1, d0, d1, mid_d, mid_b0, steep)
    # 读数取固定年份的三个率（闭式）；峰值没有初等闭式，交给画板扫
    EXPR_B = "10+35/(1+exp((2000-mid_b)/15))"
    EXPR_D = "10+25/(1+exp((2000-1920)/15))"
    # 必须加括号：不然 "A-B" 会按优先级被拆成 10 + 35/(…) - 10 + 25/(…)
    EXPR_G = f"({EXPR_B})-({EXPR_D})"
    _agree("2000 年出生率", EXPR_B, b, tol=1e-12, mid_b=mid_b0)
    _agree("2000 年死亡率", EXPR_D, d, tol=1e-12, mid_b=mid_b0)
    _agree("2000 年增长率", EXPR_G, g, tol=1e-12, mid_b=mid_b0)
    assert abs(tr["peak_growth"] - 19.22) < 0.02 and tr["peak_year"] == 1929
    # 滑块下限必须落在模型的**有效域**内：出生率下降晚于死亡率（mid_d=1920）时
    # 才有内部峰值。mid_b ≤ 1920 会让增长率从窗口起点单调下降，
    # 「峰值年」退化成 1700（那是窗口的产物，不是模型的）。
    for mb in (1930, 1950, 1970, 2010):
        rr = K.demographic_transition(b0, b1, d0, d1, mid_d, mb, steep)
        assert rr["peak_year"] > 1750, f"mid_b={mb} 时峰值退化到窗口起点"
    assert K.demographic_transition(b0, b1, d0, d1, mid_d, 1920, steep)["peak_year"] <= 1750

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "demography", "b0": b0, "b1": b1, "d0": d0, "d1": d1,
                  "mid_d": mid_d, "mid_b": "mid_b", "steep": steep,
                  "caption": _evid_badge("B")},
        "param": {"name": "mid_b", "label": "出生率下降的中点年份", "min": 1930,
                  "max": 2010, "step": 1, "value": mid_b0, "unit": "", "standard": mid_b0,
                  "ticks": ["1930", "1950 (题设)", "2010"]},
        "readouts": [
            ro("b", "2000 年出生率", EXPR_B, 3, "‰"),
            ro("d", "2000 年死亡率", EXPR_D, 3, "‰"),
            ro("g", "2000 年增长率", EXPR_G, 3, "‰"),
            ro_status("shr", "2000 年是否仍在增长", EXPR_G, 0, ">",
                      "仍在增长", "已转为负增长"),
        ],
        "constant": {"of": "mid_d", "label": "死亡率下降的中点固定在 1920 年"},
    }
    lesson = {
        "language": "zh-CN", "title": "人口转变：一个「看起来精确」的模型",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>人口转变模型：出生率与死亡率各自从高平台（$45\\text{‰}$、$35\\text{‰}$）"
            "降到低平台（$10\\text{‰}$）。死亡率先降（中点 1920 年），出生率后降。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>两条曲线之间必然出现增长率峰值。它出现在哪一年、有多大？</li>"
            "<li>拖动滑块改变出生率下降的中点，峰值怎么变？</li>"
            "<li>这一页的结论有多可靠？</li></ol>"
            "<p class='text-xs text-slate-500 mt-2'>滑块下限是 1930 年，不是随意的："
            "模型的前提是<b>出生率下降晚于死亡率</b>（死亡率中点在 1920 年）。"
            "若把出生率的中点拖到 1920 年之前，两条曲线就同时下降，"
            "增长率从窗口起点起单调递减 —— 那时「峰值」只是窗口边界的产物，"
            "不是模型的结论。</p>"),
        "answerLabel": "题设参数下的增长率峰值",
        "answer": f"$\\approx {K.f(tr['peak_growth'],2)}$‰，出现在 {tr['peak_year']} 年",
    }
    steps = [
        {"title": "为什么必然有峰值",
         "content": ("<p>增长率 $=$ 出生率 $-$ 死亡率。死亡率先降，于是差额先扩大；"
                     "出生率随后也降，差额再收窄。两条 S 形曲线一前一后，"
                     "<b>中间必然鼓出一个峰</b> —— 这是模型的必然结论，不依赖具体参数。</p>")},
        {"title": "但峰值在哪一年，取决于参数",
         "content": ("<p>把出生率下降的中点从 1950 挪到 1940：峰值从 "
                     f"{K.f(tr['peak_growth'],2)}‰ 掉到 15.23‰，年份从 1929 提到 1922。"
                     "挪到 1960：峰值升到 22.72‰，年份变成 1936。</p>"
                     "<p>而「出生率下降的中点到底是哪一年」<b>没有谁能独立观测</b> ——"
                     "它本身就是从史料里估出来的。所以：</p>"
                     "<p><b>内核完全确定，但参数来自估算。内核的确定性 ≠ 结论的确定性。</b></p>")},
        {"title": "这就是 ①B 的含义",
         "content": ("<p>图上那条曲线看起来很精确，峰值年份还标到了具体哪一年。"
                     "但如果参数是估的，那个年份就只有「估」的精度。</p>"
                     "<p>所以本页必须标注证据力 B：<b>模型的内核是对的，参数不是</b>。"
                     "凡是「某国人口转折发生在哪一年」这类说法，都要回到"
                     "「你怎么估的参数」这个问题上 —— 而不是被曲线的光滑度说服。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 技术扩散 S 曲线（① A）
# =====================================================================
def build_diffusion() -> dict:
    rate0, t0 = 0.35, 1900.0
    d = K.diffusion_s_curve(rate0, t0)
    EXPR_T10 = "1900+log(0.10/(1-0.10))/r"
    EXPR_T90 = "1900+log(0.90/(1-0.90))/r"
    EXPR_DUR = "2*log(9)/r"
    for r in (0.05, 0.2, 0.35, 0.6):
        _agree(f"t10(r={r})", EXPR_T10, K.logistic_time(0.10, t0, r), tol=1e-9, r=r)
        _agree(f"t90(r={r})", EXPR_T90, K.logistic_time(0.90, t0, r), tol=1e-9, r=r)
        _agree(f"时长(r={r})", EXPR_DUR, K.logistic_duration(0.10, 0.90, r), tol=1e-9, r=r)
    assert abs(d["duration"] - 12.556) < 1e-2

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "logistic", "r": "r", "t0": t0,
                  "caption": _evid_badge("A")},
        "param": {"name": "r", "label": "扩散速率 $r$", "min": 0.05, "max": 0.60,
                  "step": 0.01, "value": rate0, "unit": "", "standard": rate0,
                  "ticks": ["0.05", "0.35 (题设)", "0.60"]},
        "readouts": [
            ro("t10", "达到 10% 的年份", EXPR_T10, 1),
            ro("t90", "达到 90% 的年份", EXPR_T90, 1),
            ro("dur", "10%→90% 时长", EXPR_DUR, 3, "年"),
            ro_status("fast", "是否在 20 年内完成扩散", EXPR_DUR, 20, "<",
                      "20 年内完成（快扩散）", "超过 20 年"),
        ],
        "constant": {"of": "t0", "label": "扩散中点固定在 1900 年 —— 时长与它无关"},
    }
    lesson = {
        "language": "zh-CN", "title": "技术扩散的 S 曲线",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>某项技术在人口中的渗透率大致服从 logistic 曲线 "
            "$p(t) = \\dfrac{{1}}{{1+e^{{-r(t-t_0)}}}}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>渗透率从 $10\\%$ 到 $90\\%$ 要多久（$r = 0.35$）？</li>"
            "<li>拖动滑块与改变 $t_0$，这个时长会变吗？</li>"
            "<li>为什么「扩散速度」可以脱离「扩散何时开始」单独讨论？</li></ol>"),
        "answerLabel": "$r = 0.35$ 时的 10%→90% 时长",
        "answer": f"$\\approx {K.f(d['duration'],2)}$ 年",
    }
    steps = [
        {"title": "S 形不是巧合",
         "content": ("<p>新技术先被少数人采用（慢），门槛一过人群互相带动（快），"
                     "最后剩下顽固的少数（再慢）—— 这就是 logistic 曲线的三段。</p>"
                     "<p>它是**纯数学**：不需要任何数据就能写出这条曲线。</p>")},
        {"title": "10→90 的时长与起点无关",
         "content": ("<p>解 $p(t) = p^*$ 得 $t = t_0 + \\dfrac{{1}}{{r}}\\ln\\dfrac{{p^*}}{{1-p^*}}$。"
                     "两者相减，$t_0$ 被消掉：</p>"
                     "<p>$\\Delta t = \\dfrac{{1}}{{r}}\\left[\\ln\\dfrac{{0.9}}{{0.1}}\\right]"
                     "= \\dfrac{{2\\ln 9}}{{r}} = \\dfrac{{4.3944}}{{r}}$。</p>"
                     f"<p>$r = 0.35$ 时 $\\Delta t \\approx {K.f(d['duration'],2)}$ 年 ——"
                     "无论这项技术是 1800 年还是 1980 年开始扩散。</p>")},
        {"title": "这一页能证明什么",
         "content": ("<p>证据力 ①A：<b>图上每一个数都错不了</b>，因为它是纯数学结论，"
                     "不依赖任何估算。</p>"
                     "<p>但它证明的也只是「<b>若</b>渗透率服从 logistic、<b>且</b> $r$ 已知，"
                     "那么 10→90 用时为 $2\\ln9/r$」。<b>真实世界里 $r$ 恰恰是要估的</b>——"
                     "所以说某技术「用了 13 年走完 10% 到 90%」时，"
                     "真正的不确定度在 $r$ 上，而不在这个公式里。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 传染病阈值（① A）
# =====================================================================
def build_epidemic() -> dict:
    r0_0, gamma = 3.0, 0.2
    beta = K.r0_from(1.0, 1.0) * gamma * r0_0 / (K.r0_from(1.0, 1.0))   # = r0_0*gamma
    beta = r0_0 * gamma
    herd = K.herd_threshold(r0_0)
    peak = K.sir_peak_fraction(r0_0)
    EXPR_HERD = "1-1/r0"
    EXPR_PEAK = "1-(1+log(r0))/r0"
    for r0 in (1.0, 1.5, 2.0, 3.0, 4.0, 6.0):
        _agree(f"群体免疫(r0={r0})", EXPR_HERD, K.herd_threshold(r0), tol=1e-12, r0=r0)
        _agree(f"峰值(r0={r0})", EXPR_PEAK, K.sir_peak_fraction(r0), tol=1e-12, r0=r0)
    # 数值 SIR 与解析峰值对照
    _, _, I, _ = K.sir(beta, gamma, 0.99, 0.01, 200, 2000)
    assert abs(max(I) - peak) < 5e-3, f"数值峰值 {max(I):.4f} vs 解析 {peak:.4f}"

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "epidemic", "r0": "r0", "gamma": gamma,
                  "caption": _evid_badge("A")},
        "param": {"name": "r0", "label": "基本传染数 $R_0$", "min": 1.0, "max": 6.0,
                  "step": 0.1, "value": r0_0, "unit": "", "standard": r0_0,
                  "ticks": ["1.0 (临界)", "3.0 (题设)", "6.0"]},
        "readouts": [
            ro("herd", "群体免疫阈值 $1-1/R_0$", EXPR_HERD, 4),
            ro("peak", "感染峰值占比 $1-\\frac{1+\\ln R_0}{R_0}$", EXPR_PEAK, 4),
            ro("final", "最终感染比例（数值解）", EXPR_PEAK, 4),
            ro_status("crit", "是否高于临界值 1", "r0", 1, ">",
                      "R₀ > 1 → 疫情会扩散", "R₀ ≤ 1 → 自行消退"),
        ],
        "constant": {"of": "gamma", "label": "恢复率 γ 固定为 0.2/天（即病程约 5 天）"},
    }
    lesson = {
        "language": "zh-CN", "title": "传染病阈值：R₀ 与群体免疫",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>SIR 模型：$\\dfrac{{dS}}{{dt}} = -\\beta SI$、"
            "$\\dfrac{{dI}}{{dt}} = \\beta SI - \\gamma I$，"
            "定义 $R_0 = \\beta/\\gamma$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>$R_0 = 3$ 时，群体免疫阈值是多少？</li>"
            "<li>感染峰值占人口多少比例？</li>"
            "<li>拖动滑块到 $R_0 = 1$ 附近，疫情曲线怎么变？为什么？</li></ol>"),
        "answerLabel": "$R_0 = 3$ 时的阈值与峰值",
        "answer": f"群体免疫 $\\approx {K.pct(herd)}$，感染峰值 $\\approx {K.pct(peak)}$",
    }
    steps = [
        {"title": "R₀ 的含义与临界值",
         "content": ("<p>$R_0$ 是「一个感染者平均能传染几个人」。它等于传播率与恢复率之比 "
                     "$\\beta/\\gamma$。</p>"
                     "<p>当 $R_0 \\le 1$ 时，每个病人传给不到一个人，感染人数单调下降 ——"
                     "<b>疫情自行消退</b>。这就是「压平曲线」要压到的地方。</p>")},
        {"title": "群体免疫阈值 1 − 1/R₀",
         "content": ("<p>要让有效传播数降到 1 以下，必须让足够比例的人免疫：</p>"
                     "<p>$R_0(1-p) = 1 \\Rightarrow p = 1 - \\dfrac{{1}}{{R_0}}$。</p>"
                     f"<p>$R_0 = 3$ 时 $p = 1 - \\dfrac{{1}}{{3}} \\approx {K.pct(herd)}$。</p>")},
        {"title": "峰值出现在 S = N/R₀ 那一刻",
         "content": ("<p>把两式相除消去时间：$\\dfrac{{dI}}{{dS}} = -1 + "
                     "\\dfrac{{1}}{{R_0 S}}$。峰值对应 $dI/dS = 0$，即 $S = 1/R_0$。</p>"
                     "<p>代回可得峰值占比 $1 - \\dfrac{{1+\\ln R_0}}{{R_0}}$；"
                     f"$R_0=3$ 时 $\\approx {K.pct(peak)}$。左侧的红色曲线会在这一高度封顶，"
                     "与读数一致（读数就是这条解析式，不是对数值解的拟合）。</p>"
                     "<p>证据力 ①A：SIR 是确定的数学，阈值与峰值都是可由公式推出的结论。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) Kaya 恒等式（① A —— 由构造必真）
# =====================================================================
def build_kaya() -> dict:
    P, g0, e, c = 1.0, 2.0, 0.5, 2.0
    kk = K.kaya_decompose(P, g0, e, c)
    EXPR = "1*g*0.5*2"
    for g in (1.0, 1.5, 2.0, 3.0, 4.0):
        _agree(f"CO₂(g={g})", EXPR, K.kaya(P, g, e, c), tol=1e-12, g=g)
    assert kk["identity_holds"] and abs(kk["co2"] - 2.0) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "kaya", "P": P, "g": "g", "e": e, "c": c,
                  "caption": _evid_badge("A")},
        "param": {"name": "g", "label": "人均 GDP 因子（GDP/P）", "min": 1.0, "max": 4.0,
                  "step": 0.05, "value": g0, "unit": "×", "standard": g0,
                  "ticks": ["1.0", "2.0 (题设)", "4.0"]},
        "readouts": [
            ro("P", "人口因子 P", "1", 2),
            ro("g", "人均产出因子 GDP/P", "g", 2),
            ro("e", "能耗强度因子 E/GDP", "0.5", 2),
            ro("c", "排放强度因子 CO₂/E", "2", 2),
            ro("co2", "乘积 = CO₂", EXPR, 4),
            ro_status("rise", "人均产出增长是否推高排放", "g", 1, ">",
                      "推高（在强度不变的前提下）", "不推高"),
        ],
        "constant": {"of": "e", "label": "能耗强度与排放强度固定在 0.5 与 2"},
    }
    lesson = {
        "language": "zh-CN", "title": "Kaya 恒等式：把排放拆成四个乘数",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>Kaya 恒等式把碳排放分解为四个因子：</p>"
            "<p>$\\mathrm{{CO_2}} = P \\times \\dfrac{{\\mathrm{{GDP}}}}{{P}} "
            "\\times \\dfrac{{E}}{{\\mathrm{{GDP}}}} \\times "
            "\\dfrac{{\\mathrm{{CO_2}}}}{{E}}$</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>为什么说这是一个<b>恒等式</b>？</li>"
            "<li>拖动滑块（人均产出因子）到 2 倍、4 倍，排放怎么变？</li>"
            "<li>这个式子能<b>预测</b>未来排放吗？</li></ol>"),
        "answerLabel": "题设因子下的 CO₂",
        "answer": f"$= {K.f(kk['co2'],2)}$（四个因子之积）",
    }
    steps = [
        {"title": "它是恒等式，不是理论",
         "content": ("<p>看右边的乘式：分子分母依次约掉 —— "
                     "$P \\cdot \\dfrac{{GDP}}{{P}} \\cdot \\dfrac{{E}}{{GDP}} "
                     "\\cdot \\dfrac{{CO_2}}{{E}} = CO_2$。</p>"
                     "<p>所以它<b>由构造必然成立</b>，与任何经济学假设无关。"
                     "证据力 ①A：图上一个数都不会错。</p>")},
        {"title": "价值在分解，不在预测",
         "content": ("<p>因为它是恒等式，所以「排放变化」必然能被拆成这四个因子的贡献。"
                     "例如人口翻倍、其余不变，排放也翻倍 —— 这是拖滑块能直接看到的。</p>"
                     "<p>但要注意：<b>恒等式不告诉你任何因子会怎么变</b>。"
                     "它没有预测能力，只有归因能力。把「分解」说成「预测」"
                     "是这类图上最常见的误读。</p>")},
        {"title": "所以它属于「能证明什么」的哪一档",
         "content": ("<p>①A：数学上无可挑剔。但这只意味着<b>算术部分</b>可信。</p>"
                     "<p>真正的争议全部落在「四个因子各自会怎么演化」上 —— "
                     "那部分是模型与假设，不是恒等式。这也是为什么同一份 Kaya 分解"
                     "可以被用来支持完全相反的结论：分歧不在数学，在参数。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 王朝周期模型（① C —— 最危险的一类）
# =====================================================================
def build_cycle() -> dict:
    r_, a_, c_, m_ = 0.05, 1.0, 1.0, 0.05
    amp0 = 0.05
    ta = K.lv_period_analytic(r_, m_)
    sc = K.lv_integrate(r_, a_, c_, m_, amp=amp0)
    scan = K.lv_scan_amplitude(r_, m_)
    EXPR_T = "2*PI/sqrt(0.05*0.05)"
    _agree("解析周期", EXPR_T, ta, tol=1e-9)
    _agree("播种振幅读数", "amp", amp0, tol=1e-12, amp=amp0)
    assert abs(ta - 125.6637) < 1e-3
    assert abs(sc["period_numeric"] - 125.7) < 0.15
    # 审计的振幅表：周期随振幅单调变长
    printed = [125.7, 127.7, 132.2, 161.3, 301.1]
    for row, want in zip(scan, printed):
        assert abs(row["period"] - want) < 1.0, f"振幅 {row['amp']} 的周期不符"

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "cycle", "r": r_, "a": a_, "c": c_, "m": m_, "amp": "amp",
                  "caption": _evid_badge("C")},
        "param": {"name": "amp", "label": "初始偏离平衡点的幅度", "min": 0.05, "max": 3.0,
                  "step": 0.05, "value": amp0, "unit": "×", "standard": amp0,
                  "ticks": ["0.05 (小振幅)", "1.0", "3.0"]},
        "readouts": [
            ro("ta", "解析周期 $2\\pi/\\sqrt{rm}$", EXPR_T, 2, "年"),
            ro("amp", "当前振幅", "amp", 2),
            ro("ampPct", "振幅（百分数）", "amp*100", 1, "%"),
            ro_status("small", "是否处于小振幅（数值周期 ≈ 解析）", "amp", 0.1, "<",
                      "小振幅 → 数值周期贴近解析式", "大振幅 → 数值周期明显更长"),
        ],
        "constant": {"of": "ta", "label": "解析周期 125.66 年恒定（只由 r、m 决定）"},
    }
    lesson = {
        "language": "zh-CN", "title": "王朝周期模型：一个可以被拟合出来的「规律」",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>用 Lotka–Volterra 型模型描述「人口 $N$ 与精英 $E$」：</p>"
            "<p>$\\dot N = rN - aNE$，$\\quad \\dot E = cNE - mE$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>小振幅时周期是多少（$r = m = 0.05$）？</li>"
            "<li>拖动滑块增大振幅，周期会变吗？</li>"
            "<li>「某文明约两百年一循环」这句话，这个模型能支撑吗？</li></ol>"),
        "answerLabel": "小振幅下的解析周期",
        "answer": f"$T = {K.f(ta,1)}$ 年",
    }
    steps = [
        {"title": "小振幅时确有解析周期",
         "content": ("<p>在平衡点 $(m/c,\\ r/a)$ 附近线性化，得二阶方程，"
                     "周期为 $T = \\dfrac{{2\\pi}}{{\\sqrt{{rm}}}}$。</p>"
                     f"<p>$r = m = 0.05$ 时 $T = \\dfrac{{6.2832}}{{0.05}} "
                     f"\\approx {K.f(ta,1)}$ 年。数值 RK4 积分给出 "
                     f"{K.f(sc['period_numeric'],1)} 年 —— 两者吻合，说明积分器是对的。</p>")},
        {"title": "但周期还有第二个旋钮：振幅",
         "content": ("<p>把参数固定，只改**初始偏离平衡点的幅度**：</p>"
                     "<p>5% → 125.7 年；50% → 127.7；100% → 132.2；"
                     "300% → 161.3；1000% → 301.1 年。</p>"
                     "<p>周期随振幅<b>单调变长</b>，这远不是「参数定了周期就定了」。"
                     "拖动滑块就能看到相图上的轨道变大、周期读数跟着涨。</p>")},
        {"title": "所以「两百年一循环」是怎么来的",
         "content": ("<p>想让模型给出某个特定周期，你有<b>两类旋钮</b>：调参数 $(r,m)$，"
                     "或者调振幅（初始条件）。</p>"
                     "<p>而振幅在史料里<b>根本没法独立观测</b> —— 谁也不知道"
                     "「这个王朝开局时离平衡点多远」。于是：</p>"
                     "<p>任何给定的周期，几乎都能通过调这两个旋钮拟合出来。"
                     "这就叫<b>形态是 ①、证据力是 ③</b>：它有公式、能算、能画，"
                     "看起来像推导 —— 但它的参数与初值都不可独立验证。</p>"
                     "<p><b>这是图解最危险的一种。</b></p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) rank-size 幂律（① A）
# =====================================================================
def build_zipf() -> dict:
    alpha0 = 1.0
    sizes = K.pareto_sizes(200, alpha0)
    slope = K.fit_rank_size_slope(sizes)
    _agree("斜率 = −1/α", "-1/alpha", slope, tol=1e-12, alpha=alpha0)
    _agree("与 Zipf 定律的偏离", "-1/alpha-(-1)", slope - (-1.0), tol=1e-12, alpha=alpha0)
    _agree("反推 α", "-1/(-1/alpha)", K.alpha_from_slope(slope), tol=1e-12, alpha=alpha0)
    assert abs(slope + 1.0) < 1e-12
    assert abs(K.fit_rank_size_slope(K.pareto_sizes(200, 2.0)) + 0.5) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "loglog", "alpha": "alpha",
                  "caption": _evid_badge("A")},
        "param": {"name": "alpha", "label": "幂律指数 $\\alpha$", "min": 0.5, "max": 2.5,
                  "step": 0.05, "value": alpha0, "unit": "", "standard": alpha0,
                  "ticks": ["0.5", "1.0 (Zipf 定律)", "2.5"]},
        "readouts": [
            ro("slope", "rank-size 斜率 $-1/\\alpha$", "-1/alpha", 4),
            ro("alpha", "反推的 $\\alpha$", "-1/(-1/alpha)", 4),
            ro("dev", "与 Zipf 定律（斜率 −1）的偏离", "-1/alpha-(-1)", 4),
            ro_status("zipf", "是否恰为 Zipf 定律（α=1）", "alpha", 1, "==",
                      "恰为 Zipf 定律（α=1）", "偏离 Zipf 定律"),
        ],
        "constant": {"of": "n", "label": "样本数固定 200 个，按规模降序"},
    }
    lesson = {
        "language": "zh-CN", "title": "rank-size 幂律：为什么 log-log 图是直线",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>把一组规模（城市人口、词语频率…）按从大到小排名，"
            "记第 $r$ 大的规模为 $s_r$。若 $s_r \\propto r^{{-1/\\alpha}}$：</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>在 $\\log s$–$\\log r$ 图上，它是什么形状？斜率是多少？</li>"
            "<li>拖动滑块改变 $\\alpha$，斜率怎么变？</li>"
            "<li>$\\alpha = 1$ 时这个规律叫什么？</li></ol>"),
        "answerLabel": "$\\alpha = 1$ 时的斜率",
        "answer": "$-1$（即 Zipf 定律：规模 ∝ 1/排名）",
    }
    steps = [
        {"title": "取对数就把幂律变成直线",
         "content": ("<p>$s_r = s_1 \\, r^{{-1/\\alpha}}$ 两边取对数：</p>"
                     "<p>$\\log s_r = \\log s_1 - \\dfrac{{1}}{{\\alpha}}\\log r$。</p>"
                     "<p>这是关于 $\\log r$ 的<b>一次函数</b>，斜率恰好 $-1/\\alpha$。"
                     "所以「log-log 图上是不是直线」就是「数据是否服从幂律」的判据。</p>")},
        {"title": "为什么会画出直线（这里的构造方式）",
         "content": ("<p>本页的数据是**由幂律定律本身生成的**（第 $r$ 大的规模取 "
                     "$(n/r)^{{1/\\alpha}}$），所以图一定严格线性 ——"
                     "它检验的是<b>拟合器</b>对不对，不是经验数据服不服从幂律。</p>"
                     "<p>读数里的斜率由最小二乘真算出来，与理论值 $-1/\\alpha$ 逐位一致"
                     "（构建期有断言）。把 $\\alpha$ 拖到 2，斜率就是 $-0.5$。</p>")},
        {"title": "$\\alpha = 1$ 就是 Zipf 定律",
         "content": ("<p>$\\alpha = 1$ 时 $s_r \\propto 1/r$：第 2 名的规模是第 1 名的一半，"
                     "第 10 名是 1/10。城市规模、词频、姓氏频率都近似如此，"
                     "所以它被叫做 Zipf 定律。</p>"
                     "<p>证据力 ①A：这里的数学无可挑剔。但要提醒：<b>真实数据是否符合幂律，"
                     "是另一个问题</b>（要估 $\\alpha$、要处理有限样本偏差、尾部常常偏离）——"
                     "那一步需要真实数据集，属于 ①B，本页不含。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "growth": build_growth,
    "transition": build_transition,
    "diffusion": build_diffusion,
    "epidemic": build_epidemic,
    "kaya": build_kaya,
    "cycle": build_cycle,
    "zipf": build_zipf,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="可算的历史 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
