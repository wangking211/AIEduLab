#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「概率与统计」交互网页。

全部数值由 lib/prob_kernel.py 精确计算驱动（单一数据源）：排列组合、古典概型、
贝叶斯后验、二项与超几何的 pmf/期望/方差、正态覆盖率、置信区间都由内核算出，
**不手写数字**。

两处「同源」是刻意做的，且都有构建期断言兜底：
  1. 画板读数的表达式（JS）与内核值逐条对账（_agree）—— 公式漂移当场抛错；
  2. 大数定律 / 中心极限定理的模拟用**与内核逐位一致**的 LCG，且 CLT 走
     「同一条随机带按下标切片」，所以拖动滑块不会偷偷换一批随机数。

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

import prob_kernel as K                      # noqa: E402
from skillkit import cli                     # noqa: E402

# =====================================================================
# 读数表达式 ↔ 内核 的对账机制
#
# 画板上的读数由 JS 表达式在浏览器里求值，内核在 Python 里算 —— 两边各写一遍
# 公式就会漂移（改了内核忘了改表达式，页面上数字照显示，只是错了）。所以每个
# 读数表达式都在构建期用**等价的 Python 实现**求值一次，与内核值比对。
# =====================================================================

def _fact(n):
    """与画板 pfact 同语义。"""
    n = int(math.floor(float(n) + 0.5))
    r = 1
    for i in range(2, n + 1):
        r *= i
    return r


def _comb(n, k):
    """与画板 pcomb 同语义。"""
    n = int(math.floor(float(n) + 0.5))
    k = int(math.floor(float(k) + 0.5))
    if k < 0 or k > n:
        return 0
    r = 1
    for i in range(k):
        r = r * (n - i) / (i + 1)
    return int(round(r))


def _normcdf_approx(z):
    """与画板 normcdf / erfA 同一条 A&S 7.1.26 逼近（用来验证逼近够准）。

    Φ(z) = ½(1 + erf(z/√2)) —— erf 的**自变量是 z/√2**，不是 z。
    （第一版这里漏了除以 √2，误差 3e-3，被下面的 _check_js_math 当场抓住。）
    """
    s = 1.0 if z >= 0 else -1.0
    x = abs(z) / math.sqrt(2.0)
    t = 1.0 / (1.0 + 0.3275911 * x)
    y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t
              - 0.284496736) * t + 0.254829592) * t * math.exp(-x * x)
    return 0.5 * (1.0 + s * y)


_MATHENV = {
    "sqrt": math.sqrt, "abs": abs, "min": min, "max": max, "pow": pow,
    "sign": lambda x: (x > 0) - (x < 0), "floor": math.floor, "ceil": math.ceil,
    "PI": math.pi, "E": math.e,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "exp": math.exp, "log": math.log,
    "fact": _fact, "comb": _comb, "normcdf": _normcdf_approx,
}


def _jseval(expr, **env):
    return eval(expr, {"__builtins__": {}}, {**_MATHENV, **env})


def _agree(label, expr, want, tol=1e-9, **env):
    """断言「画板读数表达式」与「内核值」一致；不一致直接停构建。"""
    got = _jseval(expr, **env)
    if abs(float(got) - float(want)) > tol:
        raise AssertionError(
            f"读数表达式与内核不一致（{label}）：\n"
            f"  表达式 {expr!r}\n  按表达式算 = {got!r}\n  内核给出   = {want!r}")
    return got


def _check_js_math():
    """验证画板自带的 erf 逼近与 Python 的 math.erf 在显示精度上一致。

    浏览器没有 erf，所以画板用 A&S 7.1.26 有理逼近。若它和内核的 Φ 差到能看见，
    读数就会与分步矛盾 —— 这条断言把它挡在构建期。
    """
    worst = 0.0
    for i in range(-400, 401):
        z = i / 100.0
        worst = max(worst, abs(_normcdf_approx(z) - K.normal_cdf(z)))
    if worst > 1e-6:
        raise AssertionError(f"画板 erf 逼近误差过大：{worst:.3e} > 1e-6")
    return worst


_JS_ERF_WORST = _check_js_math()


def ro(rid, label, expr, digits=4, unit=None):
    d = {"id": rid, "label": label, "type": "expr", "expr": expr, "digits": digits}
    if unit:
        d["unit"] = unit
    return d


def ro_status(rid, label, expr, rhs=0, op="==", ok="成立", bad="不成立"):
    return {"id": rid, "label": label, "type": "status", "expr": expr,
            "rhs": rhs, "op": op, "okText": ok, "badText": bad}


# =====================================================================
# 1) 排列组合：C(8,k) 与 P(8,k)
# =====================================================================
def build_combo() -> dict:
    n, k0 = 8, 4
    cs = [int(K.comb(n, j)) for j in range(n + 1)]
    c_k = int(K.comb(n, k0))
    p_k = int(K.perm(n, k0))
    assert cs[4] == 70 and max(cs) == 70, "C(8,k) 应在 k=4 取最大 70"
    assert p_k == c_k * _fact(k0), "P(n,k) 必须等于 C(n,k)·k!"
    _agree("C(8,k) 读数", "comb(8,k)", c_k, k=k0)
    _agree("P(8,k) 读数", "fact(8)/fact(8-k)", p_k, k=k0)
    _agree("k! 读数", "fact(k)", _fact(k0), k=k0)
    _agree("P=C·k! 恒等", "fact(8)/fact(8-k) - comb(8,k)*fact(k)", 0, k=k0)

    winner = [j for j, v in enumerate(cs) if v == max(cs)]
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "factor", "n": n, "cs": cs,
                  "caption": "柱子高 = C(8,k)；拖动滑块把当前 k 移到不同柱子"},
        "param": {"name": "k", "label": "选出人数 $k$", "min": 0, "max": n, "step": 1,
                  "value": k0, "unit": "", "standard": k0,
                  "ticks": ["0", "4 (题设)", "8"]},
        "readouts": [
            ro("ck", "组合数 $C(8,k)$", "comb(8,k)", 0),
            ro("pk", "排列数 $P(8,k)$", "fact(8)/fact(8-k)", 0),
            ro("mult", "$k!$", "fact(k)", 0),
            ro_status("rel", "关系 $P=C\\cdot k!$",
                      "fact(8)/fact(8-k) - comb(8,k)*fact(k)", 0, "==",
                      "成立（排列 = 组合 × 顺序数）", "不成立"),
        ],
        "constant": {"of": "cs", "label": "整排柱子只由 n=8 决定，与 k 无关"},
    }
    lesson = {
        "language": "zh-CN", "title": "排列与组合：C(n,k) 与 P(n,k)",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>从 $8$ 名同学中选出 $k$ 人组成小组，<b>不计顺序</b>。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>当 $k=4$ 时，有多少种选法？</li>"
            "<li>若改为<b>计顺序</b>（排成一排），又是多少种？两者差几倍？</li>"
            "<li>拖动滑块，为什么 $C(8,k)$ 在 $k=4$ 最大？</li></ol>"),
        "answerLabel": "$k=4$ 时的选法数",
        "answer": f"$C(8,4) = {c_k}$ 种",
    }
    steps = [
        {"title": "乘法原理：先算「计顺序」的",
         "content": ("<p>选第 1 人 8 种、第 2 人 7 种……第 $k$ 人 $8-k+1$ 种，"
                     "由乘法原理这 $k$ 个动作的选法相乘，只需把这 $k$ 个数乘起来，"
                     "但这里给 n 从 8 降到 8-k+1 之后的另一个 $(8-k)!$，"
                     "于是 $P(8,k)=\\dfrac{8!}{(8-k)!}$。</p>"
                     f"<p>$k={k0}$ 时 $P(8,{k0})={p_k}$。</p>")},
        {"title": "去掉顺序：除以 k!",
         "content": ("<p>「不计顺序」等于把每一种组合的 $k!$ 种排法合并成一个。"
                     "所以 $C(8,k)=\\dfrac{P(8,k)}{k!}=\\dfrac{{8!}}{{k!\\,(8-k)!}}$。</p>"
                     f"<p>$k={k0}$：$C(8,{k0})={c_k}$，校验 $P={c_k}\\times{_fact(k0)}={p_k}$。</p>")},
        {"title": "为什么 k=4 最大（对称性）",
         "content": ("<p>由 $C(n,k)=C(n,n-k)$，整排柱子关于 $k=\\dfrac{{n}}{{2}}=4$ 左右对称："
                     "选 $1$ 人等价于「选 $7$ 人不选」，选法数相同。</p>"
                     f"<p>对称轴在中间，最大值就落在 $k={winner[0]}$，值 $C(8,4)={c_k}$。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 古典概型：两颗骰子的点数和
# =====================================================================
def build_classic() -> dict:
    s0 = 7
    # 6×6 样本空间中「和 = s」的格数（内核给出，不由人写成 6-|s-7|）
    fav = {s: sum(1 for i in range(1, 7) for j in range(1, 7) if i + j == s)
           for s in range(2, 13)}
    assert fav[7] == 6 and fav[2] == 1 and fav[12] == 1
    # 画板读数用的是闭式 6-|s-7|；逐点对账，保证闭式与枚举一致
    for s in range(2, 13):
        _agree(f"有利数 s={s}", "6-abs(s-7)", fav[s], s=s)
    p0 = K.classical(fav[s0], 36)
    _agree("概率读数", "(6-abs(s-7))/36", float(p0), s=s0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "sample", "s": "s",
                  "caption": "36 个等可能结果；黄格就是「和 = s」的全部情形"},
        "param": {"name": "s", "label": "目标和 $s$", "min": 2, "max": 12, "step": 1,
                  "value": s0, "unit": "", "standard": s0,
                  "ticks": ["2", "7 (最可能)", "12"]},
        "readouts": [
            ro("fav", "有利情形数", "6-abs(s-7)", 0),
            ro("p", "概率 $P$", "(6-abs(s-7))/36", 4),
            ro("pc", "百分比", "(6-abs(s-7))/36*100", 2, "%"),
        ],
        "constant": {"of": "tot", "label": "样本点总数恒为 6×6 = 36"},
    }
    lesson = {
        "language": "zh-CN", "title": "古典概型：两颗骰子的点数和",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>同时掷两颗均匀骰子，设 $X$ 为点数之和。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求 $P(X=7)$；</li>"
            "<li>拖动滑块，哪个和的概率最大？为什么不是两端？</li>"
            "<li>若有人把「和为 2」与「和为 3」当成等可能，错在哪？</li></ol>"),
        "answerLabel": "$P(X=7)$",
        "answer": f"$\\dfrac{{6}}{{36}} = {K.tex(p0)}$",
    }
    steps = [
        {"title": "样本空间是 36 个等可能结果",
         "content": ("<p>两颗骰子<b>可区分</b>（第一颗、第二颗），所以 $(1,2)$ 与 $(2,1)$ 是"
                     "两个不同样本点，总数为 $6\\times 6=36$。骰子均匀 $\\Rightarrow$ 36 个"
                     "结果等可能 —— 这是能用「有利数÷总数」的前提。</p>")},
        {"title": "数清楚有利情形",
         "content": ("<p>和为 $s$ 的有序对个数是 $6-|s-7|$：$s=7$ 时 6 个"
                     "（$(1,6)\\dots(6,1)$），越往两端越少，$s=2$ 或 $12$ 时各只有 1 个。</p>"
                     f"<p>所以 $P(X=7)=\\dfrac{{6}}{{36}}={K.tex(p0)}$。</p>")},
        {"title": "为什么两端概率最小",
         "content": ("<p>「和为 7」可以用 1+6、2+5、3+4 及其交换得到，配法最多；"
                     "「和为 2」只有 1+1 一种。直觉上「7 最中间」是错的读法 ——"
                     "真正的原因是<b>配对数</b>先增后减，图上柱高正是这个数。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 条件概率与贝叶斯：患病检测
# =====================================================================
def build_bayes() -> dict:
    prev, sens, fpr0 = 0.001, 0.99, 0.05
    priors = [prev, 1 - prev]
    liks = [sens, fpr0]
    pos = float(K.total_prob(priors, liks))
    post = float(K.bayes(priors, liks, 0))
    _agree("P(阳性) 读数", "0.001*0.99+(1-0.001)*fpr", pos, tol=1e-12, fpr=fpr0)
    _agree("后验 读数",
           "(0.001*0.99)/(0.001*0.99+(1-0.001)*fpr)", post, tol=1e-12, fpr=fpr0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "bayes", "prev": prev, "sens": sens, "fpr": "fpr", "npop": 1000,
                  "caption": "把 1000 人画成点：红=真患者且阳性，黄=健康却假阳性"},
        "param": {"name": "fpr", "label": "假阳性率（健康人误报）", "min": 0.01, "max": 0.20,
                  "step": 0.005, "value": fpr0, "unit": "", "standard": fpr0,
                  "ticks": ["0.01", "0.05 (题设)", "0.20"]},
        "readouts": [
            ro("pos", "检测阳性率 $P(B)$", "0.001*0.99+(1-0.001)*fpr", 4),
            ro("post", "后验 $P(患病\\mid 阳性)$",
               "(0.001*0.99)/(0.001*0.99+(1-0.001)*fpr)", 4),
            ro("fneg", "阳性中假阳性占比",
               "1-(0.001*0.99)/(0.001*0.99+(1-0.001)*fpr)", 4),
            ro("fprp", "假阳性率", "fpr*100", 2, "%"),
        ],
        "constant": {"of": "prev", "label": "患病率恒为 0.1%（改变假阳性率不动它）"},
    }
    lesson = {
        "language": "zh-CN", "title": "条件概率与贝叶斯：一次阳性说明了什么",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>某病在人群中的患病率为 $0.1\\%$。检测<b>灵敏度</b>（真患者被查出阳性）"
            "为 $99\\%$，<b>假阳性率</b>（健康人被误报）为 $5\\%$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>随便一人检测为阳性，他真正患病的概率是多少？</li>"
            "<li>拖动假阳性率滑块，后验怎么变？为什么它远小于 $99\\%$？</li></ol>"),
        "answerLabel": "后验概率 $P(患病\\mid 阳性)$",
        "answer": f"$\\approx {K.pct(post)}$",
    }
    steps = [
        {"title": "全概率：阳性从哪里来",
         "content": ("<p>阳性有两条来源：真患者被查出，与健康人被误报。</p>"
                     "<p>$P(B)=P(A_1)P(B\\mid A_1)+P(A_2)P(B\\mid A_2)"
                     "=0.001\\times0.99+0.999\\times0.05"
                     f"\\approx {K.f(pos, 5)}$。</p>"
                     "<p>注意：阳性里绝大多数来自<b>基数大</b>的健康人群。</p>")},
        {"title": "贝叶斯：把阳性按来源分摊",
         "content": ("<p>$P(A_1\\mid B)=\\dfrac{{P(A_1)P(B\\mid A_1)}}{{P(B)}}"
                     f"=\\dfrac{{0.001\\times0.99}}{{{K.f(pos, 5)}}}"
                     f"\\approx {K.pct(post)}$。</p>"
                     "<p>直觉的「灵敏度 99%，所以阳性 99% 有病」把"
                     "$P(B\\mid A_1)$ 与 $P(A_1\\mid B)$ 搞反了 —— 这就是"
                     "<b>基率谬误</b>。</p>")},
        {"title": "为什么假阳性率这么要命",
         "content": ("<p>患病率只有 $0.1\\%$，健康人是它的近千倍。"
                     "假阳性率从 $5\\%$ 升到 $20\\%$，阳性人数几乎全部变成误报，"
                     "后验随之塌到 $1\\%$ 以下。</p>"
                     "<p>拖动滑块看左侧点阵：<b>黄色点</b>（误报）一多，"
                     "「阳性共几人、其中真患病几人」立刻变脸。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 二项分布
# =====================================================================
def build_binom() -> dict:
    n, p0 = 10, 0.5
    mu, var = K.binom_stats(n, p0)
    _agree("期望读数", "10*p", float(mu), p=p0)
    _agree("方差读数", "10*p*(1-p)", float(var), p=p0)
    _agree("标准差读数", "sqrt(10*p*(1-p))", math.sqrt(float(var)), p=p0)
    pk5 = float(K.binom_pmf(n, 5, p0))
    _agree("P(X=5) 读数", "comb(10,5)*pow(p,5)*pow(1-p,5)", pk5, tol=1e-12, p=p0)
    assert abs(float(mu) - n * p0) < 1e-12 and abs(float(var) - n * p0 * (1 - p0)) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "bars", "dist": "binom", "n": n, "p": "p",
                  "caption": "柱子高 = P(X=k)；拖 p 看整排分布左右移动"},
        "param": {"name": "p", "label": "单次命中率 $p$", "min": 0.05, "max": 0.95,
                  "step": 0.05, "value": p0, "unit": "", "standard": p0,
                  "ticks": ["0.05", "0.5 (对称)", "0.95"]},
        "readouts": [
            ro("mean", "期望 $E(X)=np$", "10*p", 3),
            ro("var", "方差 $\\mathrm{Var}(X)=np(1-p)$", "10*p*(1-p)", 3),
            ro("sd", "标准差 $\\sigma$", "sqrt(10*p*(1-p))", 3),
            ro("pk5", "$P(X=5)$", "comb(10,5)*pow(p,5)*pow(1-p,5)", 4),
            ro_status("sym", "$p=0.5$ 时是否对称", "p", 0.5, "==",
                      "对称（此时分布关于 5 左右镜像）", "不对称（向左或右偏）"),
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "二项分布：n 次独立重复试验",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>投篮命中率恒为 $p$，独立投 $10$ 次，设 $X$ 为命中次数。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $P(X=k)$，并求 $E(X)$、$\\mathrm{{Var}}(X)$；</li>"
            "<li>$p=0.5$ 时分布长什么样？拖动滑块，$p$ 变大时分布怎么动？</li></ol>"),
        "answerLabel": "$E(X)$ 与 $\\mathrm{Var}(X)$（$p=0.5$）",
        "answer": f"$E(X)={K.num_str(mu)}$，$\\mathrm{{Var}}(X)={K.tex(var)}={K.num_str(var)}$",
    }
    steps = [
        {"title": "为什么是 C(10,k)·pᵏ(1-p)¹⁰⁻ᵏ",
         "content": ("<p>要让「恰好 $k$ 次命中」，得先决定<b>哪 k 次</b>命中 ——"
                     "共 $C(10,k)$ 种；再乘上这一串结果的概率 $p^k(1-p)^{{10-k}}$"
                     "（独立性使概率可乘）。</p>"
                     f"<p>$p=0.5$ 时 $P(X=5)=C(10,5)\\cdot0.5^{{10}}={K.f(pk5)}$。</p>")},
        {"title": "期望与方差为什么这么算",
         "content": ("<p>把 $X$ 拆成 10 个「第 $i$ 次是否命中」的指示变量 $X_i$ 之和："
                     "$E(X_i)=p$、$\\mathrm{{Var}}(X_i)=p(1-p)$。由期望的可加性"
                     "$E(X)=np$；由独立性方差也可加 $\\mathrm{{Var}}(X)=np(1-p)$。</p>"
                     f"<p>$p=0.5$：$E(X)={K.num_str(mu)}$，"
                     f"$\\mathrm{{Var}}(X)={K.tex(var)}$，$\\sigma={K.f(math.sqrt(float(var)),3)}$。</p>")},
        {"title": "p 变，分布怎么动",
         "content": ("<p>滑块把 $p$ 从 0.05 推到 0.95：分布整体从左侧滑向右侧，"
                     "最可能次数（众数）跟着 $np$ 移动；只有 $p=0.5$ 时左右完全对称。</p>"
                     "<p>蓝柱是落在 $E(X)\\pm\\sigma$ 内的（约六成概率），"
                     "它随 $p$ 变宽再变窄 —— 因为 $p(1-p)$ 在 $p=0.5$ 最大。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 超几何分布（不放回）
# =====================================================================
def build_hyper() -> dict:
    N, Ksel, n0 = 10, 3, 4
    mu, var = K.hyper_stats(N, Ksel, n0)
    bmu, bvar = K.binom_stats(n0, K.classical(Ksel, N))
    assert float(var) < float(bvar), "不放回应使方差变小"
    _agree("超几何期望", "n*3/10", float(mu), n=n0)
    _agree("超几何方差", "n*(3/10)*(7/10)*(10-n)/9", float(var), tol=1e-12, n=n0)
    _agree("有限总体校正因子", "(10-n)/9", (N - n0) / (N - 1.0), n=n0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "bars", "dist": "hyper", "n": "n", "N": N, "K": Ksel,
                  "caption": "柱子高 = P(次品数 = k)；拖 n 看抽多少件"},
        "param": {"name": "n", "label": "抽取件数 $n$", "min": 1, "max": N, "step": 1,
                  "value": n0, "unit": "", "standard": n0,
                  "ticks": ["1", "4 (题设)", "10"]},
        "readouts": [
            ro("mean", "期望 $E(X)=nK/N$", "n*3/10", 4),
            ro("var", "超几何方差", "n*(3/10)*(7/10)*(10-n)/9", 4),
            ro("bv", "同参数二项方差", "n*(3/10)*(7/10)", 4),
            ro("corr", "有限总体校正因子", "(10-n)/9", 4),
            ro_status("less", "超几何方差是否更小",
                      "n*(3/10)*(7/10) - n*(3/10)*(7/10)*(10-n)/9", 0, ">",
                      "更小（不放回减少波动）", "相等（n=1 时放不放回一样）"),
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "超几何分布：不放回抽样",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>10 件产品中有 3 件次品。从中<b>不放回</b>地抽 $n$ 件，"
            "设 $X$ 为抽到的次品数。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $P(X=k)$，并求 $E(X)$；</li>"
            "<li>与「放回抽 $n$ 件」的二项分布比，方差谁大？差的那个因子是什么？</li>"
            "<li>当 $n=10$（全部抽出）时，方差是多少？这说得通吗？</li></ol>"),
        "answerLabel": "期望与方差（$n=4$）",
        "answer": (f"$E(X)={K.tex(mu)}$，$\\mathrm{{Var}}(X)={K.tex(var)}"
                   f"\\approx{K.f(float(var),4)}$"),
    }
    steps = [
        {"title": "不放回的组合计数",
         "content": ("<p>「抽 $n$ 件得 $k$ 件次品」= 从 3 件次品取 $k$ 件、"
                     "从 7 件正品取 $n-k$ 件，故 $P(X=k)=\\dfrac{{C(3,k)C(7,n-k)}}{{C(10,n)}}$。</p>"
                     "<p>注意抽法数与抽序无关 —— 这正是「不放回」该用的计数方式。</p>")},
        {"title": "期望不变，方差要打折",
         "content": ("<p>期望仍是 $E(X)=n\\dfrac{{K}}{{N}}$（与放回一样），"
                     "因为每个位置抽到次品的边际概率都是 $K/N$。</p>"
                     "<p>但方差多了一个<b>有限总体校正因子</b> $\\dfrac{{N-n}}{{N-1}}$："
                     "$\\mathrm{{Var}}=n\\dfrac{{K}}{{N}}\\left(1-\\dfrac{{K}}{{N}}\\right)"
                     "\\dfrac{{N-n}}{{N-1}}$。不放回时后面的抽取被前面的结果「锁住」，波动更小。</p>")},
        {"title": "两个极端自检",
         "content": ("<p>$n=1$：校正因子 $\\dfrac{{9}}{{9}}=1$，退回二项（只抽一次，放不放回一样）。</p>"
                     "<p>$n=N=10$：校正因子 $\\dfrac{{0}}{{9}}=0$，方差为 $0$ ——"
                     "全部抽出来时次品数必然恰好是 3，没有随机性。这正是图上"
                     "$n=10$ 时那根孤零零的柱子。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 正态分布与 σ 覆盖率
# =====================================================================
def build_normal() -> dict:
    k0 = 1.0
    area = K.normal_interval(0, 1, -k0, k0)
    _agree("覆盖率读数", "normcdf(k)-normcdf(-k)", area, tol=1e-6, k=k0)
    _agree("等价式 2Φ(k)-1", "2*normcdf(k)-1", area, tol=1e-6, k=k0)
    _agree("尾部读数", "1-(normcdf(k)-normcdf(-k))", 1 - area, tol=1e-6, k=k0)
    ref = {s: K.normal_interval(0, 1, -s, s) for s in (1, 2, 3)}
    for s, v in ref.items():
        _agree(f"{s}σ 参考", f"normcdf({s})-normcdf(-{s})", v, tol=1e-6)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "normal", "k": "k",
                  "caption": "阴影面积 = P(|Z| ≤ k)；拖滑块看 1σ/2σ/3σ 分别覆盖多少"},
        "param": {"name": "k", "label": "区间半径 $k$（单位：σ）", "min": 0.5, "max": 3.5,
                  "step": 0.05, "value": k0, "unit": "", "standard": k0,
                  "ticks": ["0.5", "1.0", "2.0", "3.0", "3.5"]},
        "readouts": [
            ro("area", "覆盖率 $P(|Z|\\le k)$", "normcdf(k)-normcdf(-k)", 4),
            ro("area2", "等价式 $2\\Phi(k)-1$", "2*normcdf(k)-1", 4),
            ro("tail", "落在区间外的概率", "1-(normcdf(k)-normcdf(-k))", 4),
            ro_status("ident", "两式是否恒等",
                      "(normcdf(k)-normcdf(-k))-(2*normcdf(k)-1)", 0, "==",
                      "恒等（由对称性 Φ(-k)=1-Φ(k)）", "不恒等"),
        ],
        "constant": {"of": "one", "label": "1σ 覆盖率恒为 68.27%（与具体问题无关）"},
    }
    lesson = {
        "language": "zh-CN", "title": "正态分布与 σ 覆盖率",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>设 $Z$ 服从标准正态分布 $N(0,1)$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求 $P(|Z|\\le 1)$；</li>"
            "<li>拖动滑块，$k=2,3$ 时覆盖率各是多少？</li>"
            "<li>为什么教科书用 $68.27\\%,\\,95.45\\%,\\,99.73\\%$ 这一组数，"
            "而不是 $70\\%,\\,95\\%,\\,99\\%$ 这样的整数？</li></ol>"),
        "answerLabel": "$P(|Z|\\le 1)$",
        "answer": f"$\\approx {K.f(area, 4)} = {K.pct(area)}$",
    }
    steps = [
        {"title": "阴影面积就是概率",
         "content": ("<p>连续型的概率是密度曲线下的<b>面积</b>："
                     "$P(|Z|\\le k)=\\int_{{-k}}^{{k}}\\varphi(z)\\,dz"
                     "=\\Phi(k)-\\Phi(-k)$，其中 $\\Phi$ 是标准正态累积函数。</p>"
                     f"<p>$k=1$ 时得 $\\approx{K.f(area,4)}$，即 {K.pct(area)}。</p>")},
        {"title": "那组「奇怪」的数从哪来",
         "content": ("<p>$0.6827$ 不是人为定的，而是 $\\int_{{-1}}^{{1}}\\varphi$ 的值 ——"
                     "正态密度的原函数没有初等表达式，这个数只能数值算出来。</p>"
                     "<p>所以 1/2/3σ 对应 "
                     f"{K.f(ref[1],4)} / {K.f(ref[2],4)} / {K.f(ref[3],4)}。"
                     "教科书引用的就是这三个积分值，不是取整后的漂亮数字。</p>")},
        {"title": "对称性带来的恒等式",
         "content": ("<p>由 $\\Phi(-k)=1-\\Phi(k)$，覆盖率可写成 $2\\Phi(k)-1$，"
                     "与 $\\Phi(k)-\\Phi(-k)$ 完全相等 —— 右侧两个读数就是这样互相校验的。</p>"
                     "<p>拖动滑块，两式始终相等；若哪天不相等，就说明公式写错了。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 大数定律
# =====================================================================
def build_lln() -> dict:
    p0, nmax, seed = 0.5, 20000, 11
    path = K.lln_path(seed, nmax, p0)
    tail = sum(path[-2000:]) / 2000
    assert abs(tail - p0) < 0.02, "大数定律：末段频率应贴近 p"
    band = 2 / math.sqrt(nmax)
    _agree("波动尺度读数", "2/sqrt(20000)", band)
    _agree("波动尺度百分数", "2/sqrt(20000)*100", band * 100)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "lln", "p": "p", "nmax": nmax, "seed": seed,
                  "caption": "绿线是真实模拟的相对频率轨迹（LCG 真跑，非示意）"},
        "param": {"name": "p", "label": "单次成功概率 $p$", "min": 0.10, "max": 0.90,
                  "step": 0.05, "value": p0, "unit": "", "standard": p0,
                  "ticks": ["0.10", "0.50", "0.90"]},
        "readouts": [
            ro("p", "理论概率 $p$", "p", 2),
            ro("band", "波动尺度 $2/\\sqrt{{n}}$", "2/sqrt(20000)", 4),
            ro("bandp", "该尺度占比", "2/sqrt(20000)*100", 2, "%"),
            ro_status("conv", "末段是否已收敛（尺度 < 2%）",
                      "2/sqrt(20000)", 0.02, "<",
                      "已收敛（波动进入 2% 以内）", "尚未收敛"),
        ],
        "constant": {"of": "nmax", "label": "试验次数恒为 20000 次"},
    }
    lesson = {
        "language": "zh-CN", "title": "大数定律：频率为什么会稳定下来",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>反复掷一枚正面概率为 $p$ 的硬币，记前 $n$ 次的正面频率。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>拖动滑块改变 $p$，轨迹最终稳定在哪里？</li>"
            "<li>为什么样本越多越准，可曲线却始终在抖？</li>"
            "<li>红色虚线 $p\\pm\\dfrac{{2}}{{\\sqrt{{n}}}}$ 是什么？它是数据画出来的吗？</li></ol>"),
        "answerLabel": "频率的极限",
        "answer": "$\\lim\\limits_{n\\to\\infty}\\dfrac{{S_n}}{{n}}=p$（即图中黄虚线）",
    }
    steps = [
        {"title": "这条绿色轨迹是「真的掷出来的」",
         "content": ("<p>页面上的绿线不是示意曲线：它按固定种子逐次生成伪随机数、"
                     "累计成功次数再除以 $n$，得到的<b>实际</b>相对频率序列。</p>"
                     f"<p>同一个种子每次得到同一条轨迹；改 $p$ 则用<b>同一条随机带</b>"
                     "换判定阈值重算 —— 所以拖动滑块不会偷偷换一批随机数。</p>")},
        {"title": "波动为什么是 2/√n 量级",
         "content": ("<p>频率 $\\dfrac{{S_n}}{{n}}$ 的标准差是"
                     "$\\dfrac{{\\sqrt{{p(1-p)}}}}{{\\sqrt{{n}}}}\\le\\dfrac{{1}}{{2\\sqrt{{n}}}}$，"
                     "所以 $2/\\sqrt{{n}}$ 是波动的一个上界尺度，与 $\\sqrt{{n}}$ 成反比。</p>"
                     f"<p>$n={nmax}$ 时它是 $\\approx{K.f(band,4)}$，即 {K.pct(band*100)}。</p>")},
        {"title": "「收敛」不等于「不动」",
         "content": ("<p>大数定律说的是<b>依概率收敛</b>：靠后的抖动幅度趋于 0，"
                     "而不是曲线变成一条直线。看红虚线 —— 它随 $n$ 收窄，"
                     "绿线被夹在其中越夹越紧，这就是定律的直观形态。</p>"
                     "<p>把 $n$ 想成 20000：现在任何一次新试验都可能让频率动一下，"
                     "但幅度已经小到 $2\\%$ 以内。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 8) 中心极限定理
# =====================================================================
def build_clt() -> dict:
    n0, trials, maxn, seed = 12, 800, 30, 3
    mu, sd = K.clt_moments(n0)
    kurt = -6 / (5 * n0)
    _agree("均值读数", "n/2", mu, n=n0)
    _agree("标准差读数", "sqrt(n/12)", sd, tol=1e-12, n=n0)
    _agree("超额峰度读数", "-6/(5*n)", kurt, tol=1e-12, n=n0)
    # 模拟与解析对照（用同一条随机带，切片同带已在内核自检里验证）
    sums = K.clt_sums(seed, 4000, n0, maxn=maxn)
    emp_mu = sum(sums) / len(sums)
    emp_sd = math.sqrt(sum((s - emp_mu) ** 2 for s in sums) / len(sums))
    assert abs(emp_mu - mu) < 0.15 * sd and abs(emp_sd - sd) < 0.15 * sd, \
        f"CLT 模拟与解析不符：mean {emp_mu:.3f} vs {mu:.3f}, sd {emp_sd:.3f} vs {sd:.3f}"
    assert kurt > -6 / (5 * 1), "超额峰度应随 n 增大而向 0 靠近"

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "clt", "n": "n", "trials": trials, "maxn": maxn, "seed": seed,
                  "caption": "柱子是 z 分数的真实直方图（真跑），黄线是解析正态"},
        "param": {"name": "n", "label": "求和项数 $n$", "min": 1, "max": maxn, "step": 1,
                  "value": n0, "unit": "", "standard": n0,
                  "ticks": ["1", "12 (题设)", "30"]},
        "readouts": [
            ro("mu", "理论均值 $n/2$", "n/2", 2),
            ro("sd", "理论标准差 $\\sqrt{{n/12}}$", "sqrt(n/12)", 4),
            ro("kurt", "超额峰度 $-6/(5n)$", "-6/(5*n)", 4),
            ro_status("near", "是否接近正态（|超额峰度| < 0.1）",
                      "abs(-6/(5*n))", 0.1, "<",
                      "接近正态（峰度已接近 0）", "还偏离正态（n 太小）"),
        ],
        "constant": {"of": "trials", "label": "模拟组数恒为 800 组"},
    }
    lesson = {
        "language": "zh-CN", "title": "中心极限定理：为什么到处都是正态",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>取 $n$ 个独立的均匀随机数 $U(0,1)$，记它们的和为 $S_n$，"
            f"并把它标准化 $z=\\dfrac{{S_n-n/2}}{{\\sqrt{{n/12}}}}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>原始分布是「平的」，$S_n$ 的分布会是什么形状？</li>"
            "<li>拖动滑块改变 $n$，直方图怎样向黄线（标准正态）靠拢？</li>"
            "<li>用什么量能说清「靠拢」，而不只是「看起来像」？</li></ol>"),
        "answerLabel": "超额峰度（衡量偏离正态的程度）",
        "answer": f"$-\\dfrac{{6}}{{5n}}$；$n={n0}$ 时为 ${K.f(kurt,4)}\\to 0$",
    }
    steps = [
        {"title": "先算清楚矩，再谈形状",
         "content": ("<p>单个 $U(0,1)$ 的均值 $\\tfrac12$、方差 $\\tfrac1{{12}}$。"
                     "由独立性，$S_n$ 的均值 $\\tfrac{{n}}{{2}}$、方差 $\\tfrac{{n}}{{12}}$ ——"
                     "这是标准化分母的来历。</p>"
                     f"<p>$n={n0}$：均值 ${K.f(mu,2)}$，标准差 ${K.f(sd,4)}$。</p>")},
        {"title": "用一个数衡量「像不像正态」",
         "content": ("<p>说「看起来像钟形」不可验证。改用一个可算的量：<b>超额峰度</b>。"
                     "正态的超额峰度为 0；单个均匀分布是 $-\\tfrac65$。</p>"
                     "<p>$n$ 个独立同分布之和的超额峰度是 $\\dfrac{{-6/5}}{{n}}"
                     f"=-\\dfrac{{6}}{{5n}}$：$n={n0}$ 时 ${K.f(kurt,4)}$，随 $n$ 增大单调趋近 0。</p>")},
        {"title": "直方图与解析曲线对照",
         "content": ("<p>把 800 组样本标准化后装进固定区间 $[-4,4]$ 的等宽箱，"
                     "再叠加解析的标准正态密度 —— 这就是黄线。</p>"
                     "<p>$n$ 小时（如 $n=1$）柱子是平的，因为单个数本来就是均匀的；"
                     "$n$ 增大后柱子明显隆起、贴合黄线。注意这**不是**因为原始分布变正态，"
                     "而是「多个独立同分布变量之和」这个操作本身的极限行为。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "combo": build_combo,
    "classic": build_classic,
    "bayes": build_bayes,
    "binom": build_binom,
    "hyper": build_hyper,
    "normal": build_normal,
    "lln": build_lln,
    "clt": build_clt,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="概率与统计 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
