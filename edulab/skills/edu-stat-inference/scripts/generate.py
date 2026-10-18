#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「统计推断」交互网页。

**所有分布都由内核真实蒙特卡洛跑出来**（固定种子 ⇒ 可复现），
不是画一条理论曲线假装是模拟结果。理论值与模拟值并列给出。

覆盖七个题型：
  sampling      抽样分布与标准误（真实重复抽样 800 次）
  unbiased      无偏估计（为什么样本方差除以 n−1）
  ci            置信区间与覆盖率（模拟覆盖率是否等于置信水平）
  ttest         t 检验与 p 值（H₀ 下 p 值服从均匀分布）
  power         两类错误与功效（功效曲线）
  regression    最小二乘回归与 R²
  proportion    比例的估计与检验

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

import stat_kernel as K                        # noqa: E402
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


def arr(values, digits=6):
    """把一串数写成 JS/Python 通用的数组字面量，并以 [idx-1] 取当前档位。\n\n    默认保留 6 位小数 —— 对账容差要与此匹配（不要再用 1e-12）。\n    """
    body = ",".join(repr(round(float(v), digits)) for v in values)
    return "[" + body + "]"


def pick(values, idx_name, digits=6):
    return arr(values, digits) + f"[{idx_name}-1]"


# =====================================================================
# 1) 抽样分布与标准误
# =====================================================================
SA_MU, SA_SIGMA = 50.0, 10.0
SA_NLIST = [1, 4, 9, 16, 25, 36, 49, 64]
SA_K = 800
SA_LO, SA_HI, SA_NB = 15.0, 85.0, 40
SA_COUNTS, SA_SE_SIM = [], []
for _i, _n in enumerate(SA_NLIST):
    _m = K.simulate_means(SA_MU, SA_SIGMA, _n, SA_K, seed=20250000 + _i * 17)
    SA_COUNTS.append(K.hist(_m, SA_LO, SA_HI, SA_NB))
    _mb = sum(_m) / len(_m)
    SA_SE_SIM.append(math.sqrt(sum((v - _mb) ** 2 for v in _m) / len(_m)))
SA_SE = [K.se_mean(SA_SIGMA, n) for n in SA_NLIST]


def build_sampling() -> dict:
    for i, n in enumerate(SA_NLIST):
        _agree(f"SE(n={n})", f"{SA_SIGMA}/sqrt(n)", K.se_mean(SA_SIGMA, n), tol=1e-12, n=n)
        # 模拟的 SE 应当接近理论值
        assert abs(SA_SE_SIM[i] - SA_SE[i]) < 0.25, f"n={n} 的模拟 SE 偏离理论值过多"
        assert sum(SA_COUNTS[i]) > SA_K * 0.97, f"n={n} 的直方图丢点太多"
    assert SA_SE[0] == SA_SIGMA and abs(SA_SE[-1] - SA_SIGMA / 8) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "histmean", "ni": "ni",
                  "countsAll": SA_COUNTS, "nList": SA_NLIST,
                  "range": [SA_LO, SA_HI], "mu": SA_MU, "sigma": SA_SIGMA,
                  "caption": "蓝柱 = 真实模拟 800 次得到的样本均值分布；黄线 = 理论正态曲线"},
        "param": {"name": "ni", "label": "样本量 $n$（档位）", "min": 1, "max": len(SA_NLIST),
                  "step": 1, "value": 5, "unit": "", "standard": 5,
                  "ticks": ["1", "9", "25 (题设)", "49", "64"]},
        "readouts": [
            ro("n", "样本量 $n$", pick(SA_NLIST, "ni", 0), 0),
            ro("se", "标准误 $SE = \\sigma/\\sqrt{n}$", f"{SA_SIGMA}/sqrt({pick(SA_NLIST, 'ni', 0)})", 4),
            ro("sesim", "模拟得到的 SE（800 次）", pick(SA_SE_SIM, "ni"), 4),
            ro("ratio", "$SE$ 相对 $n=1$ 缩小到", f"({SA_SIGMA}/sqrt({pick(SA_NLIST, 'ni', 0)}))/{SA_SIGMA}", 4),
            ro_status("big", "是否属于「大样本」（$n \\ge 30$）", pick(SA_NLIST, "ni", 0), 29, ">",
                      "n ≥ 30：大样本，可放心用正态近似", "n < 30：小样本"),
        ],
        "constant": {"of": "mu", "label": "总体均值 $\\mu = 50$ 是定值 —— 分布变窄但中心不动"},
        "scalars": [{"name": "mu", "expr": f"{SA_MU}"}],
    }
    lesson = {
        "language": "zh-CN", "title": "抽样分布与标准误",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>总体服从 $N(50, 10^2)$。从总体中取 $n$ 个样本，"
            "计算样本均值 $\\bar x$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>$\\bar x$ 是随机变量吗？它的期望与标准差是多少？</li>"
            "<li>$n$ 增大时它的分布怎么变？</li>"
            "<li>为什么「$n$ 增大 4 倍」只能把标准误减半？</li></ol>"),
        "answerLabel": "$n = 25$ 时",
        "answer": f"$E(\\bar x) = 50$，$SE = \\dfrac{{10}}{{\\sqrt{{25}}}} = "
                  f"{K.f(K.se_mean(SA_SIGMA, 25), 2)}$",
    }
    steps = [
        {"title": "样本均值本身是随机变量",
         "content": ("<p>换个说法：**再抽一次样，$\\bar x$ 会变** —— "
                     "所以它是一个随机变量，有自己的分布，叫**抽样分布**。</p>"
                     "<p>它的两条基本性质：</p>"
                     "<p>$E(\\bar x) = \\mu$（无偏）；"
                     "$\\mathrm{SD}(\\bar x) = \\dfrac{\\sigma}{\\sqrt n}$"
                     "（这个标准差专门叫**标准误**，SE）。</p>"
                     "<p>本页的蓝柱就是**真的抽样 800 次**积出来的，"
                     "黄线是理论正态曲线 —— 两者重合说明公式是对的。</p>")},
        {"title": "为什么是 √n 而不是 n",
         "content": ("<p>因为求平均时**误差会互相抵消**：有的样本偏高、有的偏低，"
                     "平均之后正负相消。但抵消是「随机游走」式的，"
                     "不是线性累加，所以误差按 $\\sqrt n$ 缩小。</p>"
                     "<p>后果很实际：**想让精度翻倍（SE 减半），"
                     "样本量要增加到 4 倍**；想精度提高 10 倍，要 100 倍样本。"
                     "这就是抽样调查里「精度与成本不成正比」的根源。</p>")},
        {"title": "拖滑块看到什么",
         "content": ("<p>把 $n$ 从 1 拖到 64：</p>"
                     "<p>· 分布越来越**窄**（$n=1$ 时就是总体本身）；</p>"
                     "<p>· 中心**始终在 50 不动**；</p>"
                     "<p>· 形状越来越接近正态（这就是中心极限定理）。</p>"
                     "<p>读数区里「模拟得到的 SE」与「理论 SE」一直很接近 —— "
                     "这正是模拟在验证理论，而不是反过来。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 无偏估计
# =====================================================================
UB_SIGMA = 3.0
UB_SIGMA2 = UB_SIGMA ** 2
UB_NLIST = [2, 5, 10, 30]
UB_K = 4000
UB_LO, UB_HI, UB_NB = 0.0, 18.0, 36
UB_CN, UB_CN1, UB_MN, UB_MN1 = [], [], [], []
for _i, _n in enumerate(UB_NLIST):
    _rng = __import__("random").Random(31337 + _i)
    _a, _b = [], []
    for _ in range(UB_K):
        _xs = [_rng.gauss(0.0, UB_SIGMA) for _ in range(_n)]
        _a.append(K.sample_var_n(_xs))
        _b.append(K.sample_var_n1(_xs))
    UB_CN.append(K.hist(_a, UB_LO, UB_HI, UB_NB))
    UB_CN1.append(K.hist(_b, UB_LO, UB_HI, UB_NB))
    UB_MN.append(sum(_a) / len(_a))
    UB_MN1.append(sum(_b) / len(_b))


def build_unbiased() -> dict:
    for i, n in enumerate(UB_NLIST):
        _agree(f"E[s²_n] 的理论值(n={n})", f"{UB_SIGMA2}*{n - 1}/{n}", UB_SIGMA2 * (n - 1) / n, tol=1e-12)
        assert abs(UB_MN[i] - UB_SIGMA2 * (n - 1) / n) < 0.6, f"n={n} 的有偏估计模拟偏离过多"
        assert abs(UB_MN1[i] - UB_SIGMA2) < 0.6, f"n={n} 的无偏估计模拟偏离过多"
        assert UB_MN[i] < UB_MN1[i], f"n={n} 时有偏估计应小于无偏估计"
    assert abs(UB_MN[0] - UB_SIGMA2 / 2) < 0.6        # n=2 时只剩一半

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "histvar", "ni": "ni",
                  "countsNAll": UB_CN, "countsN1All": UB_CN1,
                  "meanNAll": UB_MN, "meanN1All": UB_MN1,
                  "nList": UB_NLIST, "sigma2": UB_SIGMA2,
                  "range": [UB_LO, UB_HI],
                  "caption": "红 = 除以 n（有偏）；蓝 = 除以 n−1（无偏）；绿虚线 = 真值 σ²"},
        "param": {"name": "ni", "label": "样本量 $n$（档位）", "min": 1, "max": len(UB_NLIST),
                  "step": 1, "value": 3, "unit": "", "standard": 3,
                  "ticks": ["2", "5", "10 (题设)", "30"]},
        "readouts": [
            ro("n", "样本量 $n$", pick(UB_NLIST, "ni", 0), 0),
            ro("bn", "E[$s^2_n$]（除 n，模拟）", pick(UB_MN, "ni"), 4),
            ro("bn1", "E[$s^2_{n-1}$]（除 n−1，模拟）", pick(UB_MN1, "ni"), 4),
            ro("true", "真值 $\\sigma^2$（定值）", f"{UB_SIGMA2!r}", 2),
            ro_status("unb", "「除以 n−1」的估计量是否无偏（与真值差 < 0.6）",
                      f"abs(({pick(UB_MN1, 'ni')})-{UB_SIGMA2!r})", 0.6, "<",
                      "无偏：期望正好落在真值上", "偏离真值"),
        ],
        "constant": {"of": "true", "label": "真值 $\\sigma^2 = 9$ 是定值 —— 两个估计量围着它，一个准一个偏"},
    }
    lesson = {
        "language": "zh-CN", "title": "无偏估计：为什么除以 n−1",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>总体方差为 $\\sigma^2 = 9$。用同一样本构造两种方差估计量：</p>"
            "<p>$s_n^2 = \\dfrac{1}{n}\\sum(x_i-\\bar x)^2$ 与 "
            "$s_{n-1}^2 = \\dfrac{1}{n-1}\\sum(x_i-\\bar x)^2$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>哪个是 $\\sigma^2$ 的无偏估计？</li>"
            "<li>$n$ 很小时偏差有多大？</li>"
            "<li>为什么会出现这个偏差？</li></ol>"),
        "answerLabel": "$n = 10$ 时",
        "answer": f"$E[s_n^2] = \\sigma^2\\cdot\\dfrac{{n-1}}{{n}} = "
                  f"{K.f(UB_SIGMA2 * 9 / 10, 2)}$，"
                  f"$E[s_{{n-1}}^2] = \\sigma^2 = 9$",
    }
    steps = [
        {"title": "偏差来自「用样本均值代替总体均值」",
         "content": ("<p>方差公式里本该用**总体均值** $\\mu$："
                     "$\\sum(x_i-\\mu)^2$。但实际只能用它自己的均值 $\\bar x$。</p>"
                     "<p>而 $\\bar x$ 恰好是让 $\\sum(x_i-a)^2$ 达到最小的那个 $a$ —— "
                     "所以用 $\\bar x$ 算出来的平方和**系统性地偏小**。</p>"
                     "<p>可以证明 $E\\left[\\sum(x_i-\\bar x)^2\\right] = (n-1)\\sigma^2$，"
                     "于是除以 $n$ 就差了一个因子 $\\dfrac{n-1}{n}$，"
                     "除以 $n-1$ 才正好还原。</p>")},
        {"title": "偏差有多大",
         "content": ("<p>偏差比例是 $\\dfrac{1}{n}$：</p>"
                     "<p>· $n = 2$：低估 **50%**（图上红色那堆明显偏左）；</p>"
                     "<p>· $n = 10$：低估 10%；</p>"
                     "<p>· $n = 30$：只低估 3.3%。</p>"
                     "<p>所以 $n$ 大时两种估计量几乎没区别 —— "
                     "但 $n$ 小时差别很大，这就是教材坚持除以 $n-1$ 的原因。"
                     "拖滑块把 $n$ 从 2 拉到 30，可以看到红蓝两堆逐渐重合。</p>")},
        {"title": "「无偏」不等于「更好」",
         "content": ("<p>无偏是指**平均意义上**准确，不代表每次估计都更接近真值。</p>"
                     "<p>实际上在「均方误差」这个标准下，"
                     "除以 $n+1$ 的估计量有时反而更优 —— 因为它方差更小。"
                     "这就是统计学里著名的「偏差-方差权衡」。</p>"
                     "<p>所以「无偏」是一条**好性质**，但不是唯一目标。"
                     "本页把它作为主角，是因为它的含义最直观："
                     "**重复抽样很多次，估计值的平均正好等于真值**。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 置信区间与覆盖率
# =====================================================================
CI_MU, CI_SIGMA, CI_N = 100.0, 15.0, 25
CI_LEVELS = [0.50, 0.60, 0.70, 0.80, 0.90, 0.95, 0.99]
CI_K = 60
CI_IVS, CI_MEANS, CI_COV, CI_WIDTH = [], [], [], []
for _i, _lv in enumerate(CI_LEVELS):
    _cov, _ivs, _ms = K.simulate_coverage(CI_MU, CI_SIGMA, CI_N, _lv, CI_K, seed=8642 + _i * 31)
    CI_IVS.append([[round(a, 4), round(b, 4)] for a, b in _ivs])
    CI_MEANS.append([round(v, 4) for v in _ms])
    CI_COV.append(_cov)
    CI_WIDTH.append(2 * K.z_critical(_lv) * K.se_mean(CI_SIGMA, CI_N))


def build_ci() -> dict:
    for i, lv in enumerate(CI_LEVELS):
        _agree(f"区间宽度(level={lv})",
               f"2*({K.z_critical(lv)!r})*{K.se_mean(CI_SIGMA, CI_N)!r}", CI_WIDTH[i], tol=1e-9)
        # 覆盖率应当接近置信水平（模拟误差范围内）
        assert abs(CI_COV[i] - lv) < 0.14, f"level={lv} 的覆盖率 {CI_COV[i]} 偏离过多"
        for a, b in CI_IVS[i]:
            assert abs((b - a) - CI_WIDTH[i]) < 1e-3, "所有区间的宽度应当相同"
    assert CI_WIDTH[0] < CI_WIDTH[-1]

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "ciplot", "li": "li",
                  "ivsAll": CI_IVS, "meansAll": CI_MEANS, "levels": CI_LEVELS,
                  "widths": CI_WIDTH, "mu": CI_MU, "sigma": CI_SIGMA, "n": CI_N,
                  "range": [86.0, 114.0],
                  "caption": "每条横线 = 一次抽样得到的置信区间；绿 = 盖住真值、红 = 没盖住"},
        "param": {"name": "li", "label": "置信水平（档位）", "min": 1, "max": len(CI_LEVELS),
                  "step": 1, "value": 6, "unit": "", "standard": 6,
                  "ticks": ["50%", "80%", "90%", "95% (题设)", "99%"]},
        "readouts": [
            ro("lv", "置信水平", pick(CI_LEVELS, "li"), 2),
            ro("cov", "模拟覆盖率（60 次）", pick(CI_COV, "li"), 4),
            ro("w", "区间宽度", pick(CI_WIDTH, "li"), 4),
            ro("zc", "正态临界值 $z$", pick([K.z_critical(v) for v in CI_LEVELS], "li"), 4),
            ro_status("ok", "覆盖率是否与置信水平吻合（差 < 0.12）",
                      f"abs(({pick(CI_COV, 'li')})-({pick(CI_LEVELS, 'li')}))", 0.12, "<",
                      "覆盖率与置信水平一致 —— 这正是置信区间的含义", "偏离较大（样本少时正常）"),
        ],
        "constant": {"of": "nfix", "label": "$\\sigma = 15$、$n = 25$ 固定 ⇒ 区间宽度只由置信水平决定"},
        "scalars": [{"name": "nfix", "expr": "25"}],
    }
    lesson = {
        "language": "zh-CN", "title": "置信区间与覆盖率",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>总体 $N(\\mu, 15^2)$，取 $n = 25$ 得到样本均值 $\\bar x$，"
            "构造 95% 置信区间 $\\bar x \\pm 1.96\\dfrac{\\sigma}{\\sqrt n}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>「95% 置信」到底是什么意思？</li>"
            "<li>重复抽样 60 次，大概有几条区间盖住真值？</li>"
            "<li>置信水平提高，区间变宽还是变窄？</li></ol>"),
        "answerLabel": "95% 置信水平时",
        "answer": f"区间宽度 $= 2\\times1.96\\times\\dfrac{{15}}{{\\sqrt{{25}}}} = "
                  f"{K.f(CI_WIDTH[-2], 4)}$；60 次里约 57 条盖住真值",
    }
    steps = [
        {"title": "置信水平说的是「方法」而不是「这一次」",
         "content": ("<p>这是最常被误解的一句话。正确的读法是：</p>"
                     "<p>**「如果我们反复抽样、每次都用同一套公式建区间，"
                     "那么长期来看有 95% 的区间会盖住真值。」**</p>"
                     "<p>它不是「真值有 95% 的概率落在这一条区间里」—— "
                     "真值是个固定常数（不是随机的），要么在、要么不在。</p>"
                     "<p>图上那 60 条横线就是 60 次抽样的结果："
                     "绿的盖住了、红的没盖住。**红色本来就该存在**，"
                     "大约是 $60\\times5\\% = 3$ 条。</p>")},
        {"title": "宽度从哪来",
         "content": ("<p>宽度 $= 2 z \\cdot \\dfrac{\\sigma}{\\sqrt n}$，三个因素：</p>"
                     "<p>· 置信水平越高 ⇒ $z$ 越大 ⇒ 区间**越宽**"
                     "（想更有把握，就得说得更含糊）；</p>"
                     "<p>· 数据越分散（$\\sigma$ 大）⇒ 越宽；</p>"
                     "<p>· 样本量越大 ⇒ 越窄，但只按 $\\sqrt n$ 缩小。</p>"
                     "<p>拖滑块可以看到：50% 水平的区间很窄但漏得多，"
                     "99% 水平几乎全盖住但宽得几乎无用 —— "
                     "**「准」与「精」是一对矛盾**。</p>")},
        {"title": "σ 未知时改用 t",
         "content": ("<p>实际工作中 $\\sigma$ 通常也不知道，只能用样本标准差 $s$ 代替，"
                     "这时要把 $z$ 换成 **t 临界值**（自由度 $n-1$）。</p>"
                     "<p>$t$ 分布比正态「胖」，所以区间会稍微宽一点 —— "
                     "这是为「连 $\\sigma$ 也要估」付出的代价。</p>"
                     "<p>$n$ 大时 $t$ 趋近正态，两者几乎一样；"
                     "$n$ 很小（比如 5）时差别很明显。内核里两种临界值都有。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) t 检验与 p 值
# =====================================================================
TT_DELTAS = [0.0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.2]
TT_N, TT_K, TT_ALPHA = 20, 3000, 0.05
TT_NB = 20
TT_PHIST, TT_REJ = [], []
for _i, _d in enumerate(TT_DELTAS):
    _ps = K.simulate_pvalues(0.0, _d, 1.0, TT_N, TT_K, seed=555000 + _i * 13)
    TT_PHIST.append(K.hist(_ps, 0.0, 1.0, TT_NB))
    TT_REJ.append(sum(1 for p in _ps if p < TT_ALPHA) / len(_ps))


def build_ttest() -> dict:
    for i, d in enumerate(TT_DELTAS):
        _agree(f"拒绝率(delta={d})", pick(TT_REJ, "di"), TT_REJ[i], tol=1e-6, di=i + 1)
        if d == 0.0:
            # H₀ 成立时拒绝率应当接近 α
            assert abs(TT_REJ[i] - TT_ALPHA) < 0.025, f"δ=0 时的拒绝率 {TT_REJ[i]} 应接近 0.05"
            # p 值均匀 ⇒ 各区间计数大致相等
            c = TT_PHIST[i]
            mx, mn = max(c), min(c)
            assert mn > 0 and mx / mn < 1.6, "δ=0 时 p 值的直方图应当比较平"
        else:
            # 有真实效应 ⇒ 小 p 值更多
            assert TT_PHIST[i][0] > TT_PHIST[i][-1], f"δ={d} 时小 p 值应当更多"
    assert TT_REJ[0] < TT_REJ[-1], "真实效应越大，拒绝率应当越高"

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "phist", "di": "di",
                  "pHistAll": TT_PHIST, "deltas": TT_DELTAS, "rejAll": TT_REJ,
                  "np": TT_K, "n": TT_N,
                  "caption": "p 值的分布：δ = 0 时是均匀的；δ > 0 时明显向左压"},
        "param": {"name": "di", "label": "真实效应 $\\delta$（档位）", "min": 1, "max": len(TT_DELTAS),
                  "step": 1, "value": 1, "unit": "", "standard": 1,
                  "ticks": ["0 (H₀真)", "0.2", "0.5", "0.8", "1.2"]},
        "readouts": [
            ro("d", "真实效应 $\\delta$（以 σ 为单位）", pick(TT_DELTAS, "di"), 2),
            ro("rej", "模拟的拒绝率（3000 次，α = 0.05）", pick(TT_REJ, "di"), 4),
            ro("np", "模拟次数", f"{TT_K}", 0),
            ro("n", "每次检验的样本量 $n$", f"{TT_N}", 0),
            ro_status("h0", "是否恰为 $H_0$ 成立的情形（$\\delta = 0$）",
                      pick(TT_DELTAS, "di"), 1e-6, "<",
                      "δ = 0：p 值均匀 ⇒ 拒绝率就是 α", "δ > 0：有真实效应"),
        ],
        "constant": {"of": "alp", "label": "$\\alpha = 0.05$ 是定值 —— δ = 0 时拒绝率必须等于它"},
        "scalars": [{"name": "alp", "expr": "0.05"}],
    }
    lesson = {
        "language": "zh-CN", "title": "t 检验与 p 值的真正含义",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>用 $n = 20$ 的样本检验 $H_0: \\mu = 0$，"
            "真实均值是 $\\delta$（以 $\\sigma$ 为单位）。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 t 统计量与双侧 p 值；</li>"
            "<li>$\\delta = 0$ 时 p 值服从什么分布？</li>"
            "<li>为什么「$p < 0.05$」不能理解为「$H_0$ 为假的概率小于 5%」？</li></ol>"),
        "answerLabel": "$\\delta = 0$ 时",
        "answer": f"p 值服从 $U(0,1)$ ⇒ $P(p<0.05) = 0.05$"
                  f"（模拟值 ${K.f(TT_REJ[0], 4)}$）",
    }
    steps = [
        {"title": "p 值是什么",
         "content": ("<p>p 值的定义只有一句话：</p>"
                     "<p>**在 $H_0$ 成立的假设下，出现「当前这么极端或更极端」结果的概率。**</p>"
                     "<p>注意它是一个**条件概率**：条件是「$H_0$ 为真」。"
                     "所以它**不是**「$H_0$ 为真的概率」—— 这两者是完全不同的东西，"
                     "混起来就是著名的「p 值误用」。</p>"
                     "<p>本页用 $t = \\dfrac{\\bar x - \\mu_0}{s/\\sqrt n}$ 计算，"
                     "自由度 $n-1$，双侧 p 值 $= 2(1-F_{t}(|t|))$。</p>")},
        {"title": "δ = 0 时 p 值服从均匀分布",
         "content": ("<p>这是一个**反直觉但极其重要**的事实："
                     "如果 $H_0$ 恰好为真，那么 p 值在各个区间的出现概率是一样的 —— "
                     "它服从 $U(0,1)$。</p>"
                     "<p>于是：$P(p < 0.05) = 0.05$，"
                     "$P(p < 0.10) = 0.10$，$P(p < 0.5) = 0.5$。</p>"
                     "<p>图上 δ = 0 那一档的柱高基本齐平，正是这个结论的直观呈现。"
                     "它同时说明了 α 的含义：**就算 $H_0$ 是真的，"
                     "也有 5% 的概率被误判为「显著」**（第一类错误）。</p>")},
        {"title": "δ > 0 时 p 值向左压",
         "content": ("<p>把滑块拖到 δ > 0：柱子的形状立刻向左倾斜，"
                     "最左边那一格（p < 0.05）明显变高。</p>"
                     "<p>倾斜的程度就是**功效**。δ 越大、n 越大，"
                     "倾斜越厉害、越容易检出真实效应。</p>"
                     "<p>另外注意：即使 δ > 0，p 值**仍然可能很大** —— "
                     "有时抽到的样本恰好不巧，就检不出来。"
                     "这不是方法错了，而是**随机性使然**。"
                     "下一节的「功效」正是量化这件事。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 功效与样本量
# =====================================================================
PW_NLIST = [5, 10, 20, 40, 80, 160]
PW_ALPHA = 0.05
PW_DMAX = 1.0
PW_PTS = 41
PW_SIGMA = 1.0
PW_CURVES = [[K.power_two_sided(PW_DMAX * i / (PW_PTS - 1), PW_SIGMA, n, PW_ALPHA)
              for i in range(PW_PTS)] for n in PW_NLIST]
PW_AT05 = [K.power_two_sided(0.5, PW_SIGMA, n, PW_ALPHA) for n in PW_NLIST]


def _delta_for_power(target, n, sigma=PW_SIGMA, alpha=PW_ALPHA):
    """二分法求达到目标功效所需的 δ/σ。"""
    lo, hi = 0.0, 5.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if K.power_two_sided(mid, sigma, n, alpha) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


PW_DNEED = [_delta_for_power(0.80, n) for n in PW_NLIST]
PW_NFOR80 = 0
for _n in range(2, 4000):
    if K.power_two_sided(0.5, PW_SIGMA, _n, PW_ALPHA) >= 0.80:
        PW_NFOR80 = _n
        break


def build_power() -> dict:
    assert abs(K.power_two_sided(0.0, 1.0, 25, 0.05) - 0.05) < 1e-6
    for i, n in enumerate(PW_NLIST):
        _agree(f"功效(n={n}, δ=0.5)", pick(PW_AT05, "ni"), PW_AT05[i], tol=1e-6, ni=i + 1)
        assert PW_CURVES[i][0] < 0.06, "δ=0 处的功效应当等于 α"
        assert PW_CURVES[i][-1] > PW_CURVES[i][0], "功效应随 δ 上升"
    assert all(PW_AT05[i] < PW_AT05[i + 1] for i in range(len(PW_AT05) - 1)), "功效应随 n 上升"
    assert PW_NFOR80 > 0 and abs(K.power_two_sided(0.5, 1.0, PW_NFOR80, 0.05) - 0.80) < 0.01

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "powercurve", "ni": "ni",
                  "powerAll": PW_CURVES, "nList": PW_NLIST, "powerAt05": PW_AT05,
                  "dNeeded": PW_DNEED, "nFor80": PW_NFOR80, "dmax": PW_DMAX,
                  "caption": "蓝粗线 = 当前 n 的功效曲线；红虚线 = α = 0.05 的水平线"},
        "param": {"name": "ni", "label": "样本量 $n$（档位）", "min": 1, "max": len(PW_NLIST),
                  "step": 1, "value": 3, "unit": "", "standard": 3,
                  "ticks": ["5", "10", "20 (题设)", "40", "160"]},
        "readouts": [
            ro("n", "样本量 $n$", pick(PW_NLIST, "ni", 0), 0),
            ro("p05", "在 $\\delta/\\sigma = 0.5$ 处的功效", pick(PW_AT05, "ni"), 4),
            ro("dn", "要达到 0.80 功效所需的 $\\delta/\\sigma$", pick(PW_DNEED, "ni"), 4),
            ro("n80", "$\\delta/\\sigma = 0.5$ 时达到 0.80 功效所需的最少 $n$", f"{PW_NFOR80}", 0),
            ro_status("enough", "当前 $n$ 的功效是否已达 0.80", pick(PW_AT05, "ni"), 0.80, ">",
                      "功效 ≥ 0.80：够用（常用的经验门槛）", "功效 < 0.80：容易漏掉真实效应"),
        ],
        "constant": {"of": "n80", "label": "$\\delta/\\sigma=0.5$ 时 $n\\ge 64$ 才能达到 0.80 功效 —— 这是设计实验的常用门槛"},
    }
    lesson = {
        "language": "zh-CN", "title": "功效、样本量与两类错误",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>要对 $H_0: \\mu = 0$ 做双侧检验（$\\alpha = 0.05$），"
            "真实效应为 $\\delta$（以 $\\sigma$ 为单位）。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出功效的计算式；</li>"
            "<li>$\\delta = 0$ 时功效等于多少？</li>"
            "<li>$\\delta/\\sigma = 0.5$ 时要多大样本量才能达到 0.80 功效？</li></ol>"),
        "answerLabel": "$n = 20$ 时",
        "answer": f"在 $\\delta/\\sigma = 0.5$ 处功效为 "
                  f"${K.f(PW_AT05[2], 4)}$；要达到 0.80 需要 $n \\ge {PW_NFOR80}$",
    }
    steps = [
        {"title": "两类错误",
         "content": ("<p>· **第一类错误**（弃真）：$H_0$ 为真却拒绝它，"
                     "概率记作 $\\alpha$，由我们自己设定（常用 0.05）；</p>"
                     "<p>· **第二类错误**（取伪）：$H_0$ 为假却没拒绝，"
                     "概率记作 $\\beta$；</p>"
                     "<p>· **功效** $= 1 - \\beta$，即「真有差异时能查出来」的概率。</p>"
                     "<p>$\\alpha$ 和 $\\beta$ 是一对矛盾："
                     "把 $\\alpha$ 调小（更慎重）会让 $\\beta$ 变大（更容易漏掉）。"
                     "想两者都小，唯一的办法是**增大样本量**。</p>")},
        {"title": "功效的公式",
         "content": ("<p>对双侧 z 检验（$\\sigma$ 已知的近似）：</p>"
                     "<p>$\\text{功效} = \\Phi\\!\\left(-z_{\\alpha/2} - "
                     "\\dfrac{\\delta\\sqrt n}{\\sigma}\\right) "
                     "+ 1 - \\Phi\\!\\left(z_{\\alpha/2} - "
                     "\\dfrac{\\delta\\sqrt n}{\\sigma}\\right)$。</p>"
                     "<p>关键是那个 $\\dfrac{\\delta\\sqrt n}{\\sigma}$ —— "
                     "**功效只依赖于「效应量除以标准误」**，"
                     "也就是 $\\delta$、$\\sigma$、$n$ 三者的组合。</p>"
                     "<p>$\\delta = 0$ 时两项相加恰好等于 $\\alpha$（"
                     "图上曲线从 0.05 那条红线起步），这正是上一节的结论。</p>")},
        {"title": "为什么要先算样本量",
         "content": ("<p>做实验前应该先问：**「如果真实效应是这么大，我需要多少样本才能有八成把握查出来？」**</p>"
                     "<p>本页给出答案：$\\delta/\\sigma = 0.5$（中等效应）时，"
                     f"需要 $n \\ge {PW_NFOR80}$。</p>"
                     "<p>这就是为什么正经的医学试验动辄上千人 —— "
                     "小效应需要大样本，否则做出来「没差异」其实只是样本不够。</p>"
                     "<p>拖滑块把 $n$ 从 5 拉到 160，可以看到整条功效曲线整体上抬，"
                     "从左下角的「基本检不出」抬到接近 1。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 最小二乘回归
# =====================================================================
RG_SIGMAS = [0.0, 0.3, 0.7, 1.2, 2.0, 3.0]
RG_N, RG_B, RG_A = 30, 2.0, 1.0
RG_PTS, RG_BHAT, RG_AHAT, RG_R2 = [], [], [], []
for _i, _s in enumerate(RG_SIGMAS):
    _xs, _ys, _b, _a, _r2, _res, _pred = K.simulate_regression(
        RG_B, RG_A, _s, RG_N, seed=777000 + _i * 7)
    RG_PTS.append([[round(_xs[j], 3), round(_ys[j], 3)] for j in range(RG_N)])
    RG_BHAT.append(_b)
    RG_AHAT.append(_a)
    RG_R2.append(_r2)


def build_regression() -> dict:
    for i, s in enumerate(RG_SIGMAS):
        _agree(f"斜率(σ={s})", pick(RG_BHAT, "si"), RG_BHAT[i], tol=1e-6, si=i + 1)
        _agree(f"R²(σ={s})", pick(RG_R2, "si"), RG_R2[i], tol=1e-6, si=i + 1)
        if s == 0.0:
            assert abs(RG_R2[i] - 1.0) < 1e-9, "无噪声时 R² 应当为 1"
            assert abs(RG_BHAT[i] - RG_B) < 1e-9
    assert all(RG_R2[i] > RG_R2[i + 1] for i in range(len(RG_R2) - 1)), "噪声越大 R² 应当越小"
    assert 0.0 < RG_R2[-1] < 1.0

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "scatter", "si": "si",
                  "ptsAll": RG_PTS, "bAll": RG_BHAT, "aAll": RG_AHAT, "r2All": RG_R2,
                  "sigmas": RG_SIGMAS, "yrange": [-6.0, 28.0],
                  "caption": "蓝点 = 观测数据；黄线 = 最小二乘拟合；灰虚线 = 残差"},
        "param": {"name": "si", "label": "噪声标准差 $\\sigma$（档位）", "min": 1, "max": len(RG_SIGMAS),
                  "step": 1, "value": 5, "unit": "", "standard": 5,
                  "ticks": ["0", "0.7", "1.2", "2.0 (题设)", "3.0"]},
        "readouts": [
            ro("s", "噪声标准差 $\\sigma$", pick(RG_SIGMAS, "si"), 2),
            ro("b", "拟合斜率 $\\hat b$（真值 2）", pick(RG_BHAT, "si"), 4),
            ro("a", "拟合截距 $\\hat a$（真值 1）", pick(RG_AHAT, "si"), 4),
            ro("r2", "决定系数 $R^2$", pick(RG_R2, "si"), 4),
            ro_status("good", "拟合是否良好（$R^2 > 0.9$）", pick(RG_R2, "si"), 0.9, ">",
                      "R² > 0.9：x 解释了 y 的绝大部分变化", "R² ≤ 0.9：噪声占比不小"),
        ],
        "constant": {"of": "nb", "label": "样本量 $n = 30$、真值斜率 2、真值截距 1 都是定值"},
        "scalars": [{"name": "nb", "expr": f"{RG_N}"}],
    }
    lesson = {
        "language": "zh-CN", "title": "最小二乘回归与 R²",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>真实关系是 $y = 1 + 2x$。取 $n = 30$ 个点，"
            "每个点的 $y$ 上加一个标准差为 $\\sigma$ 的随机噪声。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出最小二乘的准则；</li>"
            "<li>噪声 $\\sigma$ 变化时，斜率估计与 $R^2$ 怎么变？</li>"
            "<li>为什么残差之和恒为 0？</li></ol>"),
        "answerLabel": "$\\sigma = 1.2$ 时",
        "answer": f"斜率估计 ${K.f(RG_BHAT[3], 4)}$（真值 2），"
                  f"$R^2 = {K.f(RG_R2[3], 4)}$",
    }
    steps = [
        {"title": "最小二乘的准则",
         "content": ("<p>找一条直线 $\\hat y = a + bx$，让**残差平方和**最小：</p>"
                     "<p>$\\displaystyle\\min_{a,b}\\sum_i (y_i - a - bx_i)^2$。</p>"
                     "<p>为什么用平方而不是绝对差？因为平方可导，"
                     "能直接解出闭式解（而且对应「误差服从正态分布时」的极大似然估计）。</p>"
                     "<p>解出来是 $b = \\dfrac{S_{xy}}{S_{xx}}$、"
                     "$a = \\bar y - b\\bar x$ —— 两个都是简单的算术组合。</p>")},
        {"title": "残差为什么要画出来",
         "content": ("<p>图上的灰虚线就是残差。它们有两个**必然成立**的性质：</p>"
                     "<p>· **残差之和为 0**（正负抵消）；</p>"
                     "<p>· **残差与 x 正交**（$\\sum r_i x_i = 0$）。</p>"
                     "<p>这两条不是巧合，而是「平方和最小」的一阶条件 —— "
                     "对 $a$ 与 $b$ 求偏导并令其为 0，得到的正是它们。</p>"
                     "<p>所以拿到回归结果时，**先画残差图**："
                     "如果残差还呈现弯曲的规律，说明线性模型不合适（该加二次项了）。</p>")},
        {"title": "R² 是什么",
         "content": ("<p>$R^2 = 1 - \\dfrac{SS_{res}}{SS_{tot}}$，"
                     "表示「y 的总变化中有多少比例被 x 解释掉了」。</p>"
                     "<p>· $R^2 = 1$：所有点都在直线上（本页 $\\sigma = 0$ 那一档）；</p>"
                     "<p>· $R^2$ 接近 0：x 基本没提供信息；</p>"
                     "<p>· 拖滑块增大噪声，可以看到 $R^2$ 单调下降。</p>"
                     "<p>注意：$R^2$ 高**不代表模型正确**。"
                     "数据里如果混了离群点，或者真实关系是弯曲的，"
                     "$R^2$ 也可能很高。判断模型好不好，还是要看残差图。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 比例的估计与检验
# =====================================================================
PR_P = 0.5
PR_NLIST = [10, 20, 50, 100, 200, 500]
PR_K = 800
PR_LO, PR_HI, PR_NB = 0.10, 0.90, 32
PR_COUNTS = [K.hist(K.simulate_prop_dist(PR_P, n, PR_K, seed=24680 + i * 3), PR_LO, PR_HI, PR_NB)
             for i, n in enumerate(PR_NLIST)]
PR_SE = [K.prop_se(PR_P, n) for n in PR_NLIST]


def build_proportion() -> dict:
    for i, n in enumerate(PR_NLIST):
        _agree(f"SE(n={n})", f"sqrt({PR_P}*(1-{PR_P})/n)", K.prop_se(PR_P, n), tol=1e-12, n=n)
        _agree(f"95% 半宽(n={n})", f"1.96*sqrt({PR_P}*(1-{PR_P})/n)",
               1.96 * K.prop_se(PR_P, n), tol=1e-9, n=n)
    assert PR_SE[0] > PR_SE[-1]
    assert abs(PR_SE[-1] * math.sqrt(PR_NLIST[-1] / PR_NLIST[0])
               - PR_SE[0]) < 1e-9, "SE 应按 √n 缩小"
    # 模拟的分布应当以 p 为中心
    for i, n in enumerate(PR_NLIST):
        assert sum(PR_COUNTS[i]) > PR_K * 0.85, f"n={n} 的直方图丢点太多"

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "prophist", "ni": "ni",
                  "countsAll": PR_COUNTS, "nList": PR_NLIST,
                  "range": [PR_LO, PR_HI], "pTrue": PR_P,
                  "caption": "蓝柱 = 真实模拟 800 次得到的样本比例分布；黄线 = 理论正态近似"},
        "param": {"name": "ni", "label": "样本量 $n$（档位）", "min": 1, "max": len(PR_NLIST),
                  "step": 1, "value": 4, "unit": "", "standard": 4,
                  "ticks": ["10", "20", "50", "100 (题设)", "500"]},
        "readouts": [
            ro("n", "样本量 $n$", pick(PR_NLIST, "ni", 0), 0),
            ro("se", "标准误 $\\sqrt{p(1-p)/n}$", pick(PR_SE, "ni"), 4),
            ro("hw", "95% 区间半宽 $1.96\\times SE$", pick([1.96 * v for v in PR_SE], "ni"), 4),
            ro("ratio", "$SE$ 相对 $n=10$ 缩小到",
               pick([v / PR_SE[0] for v in PR_SE], "ni"), 4),
            ro_status("prec", "95% 区间半宽是否小于 0.05", pick([1.96 * v for v in PR_SE], "ni"),
                      0.05, "<", "半宽 < 0.05：精度不错（约 ±5 个百分点）", "半宽 ≥ 0.05：精度不足"),
        ],
        "constant": {"of": "pfix", "label": "真值 $p = 0.5$ 是定值 —— $p=0.5$ 时方差最大，是最坏情形"},
        "scalars": [{"name": "pfix", "expr": "0.5"}],
    }
    lesson = {
        "language": "zh-CN", "title": "比例的估计与检验",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>真实比例为 $p = 0.5$。取 $n$ 个样本，得到样本比例 $\\hat p$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $\\hat p$ 的标准误；</li>"
            "<li>$n$ 增大时 $\\hat p$ 的分布怎么变？</li>"
            "<li>为什么 $p = 0.5$ 是最坏情形？</li></ol>"),
        "answerLabel": "$n = 100$ 时",
        "answer": f"$SE = \\sqrt{{\\dfrac{{0.5\\times0.5}}{{100}}}} = "
                  f"{K.f(K.prop_se(0.5, 100), 4)}$，95% 半宽 $\\approx 0.098$",
    }
    steps = [
        {"title": "比例的标准误",
         "content": ("<p>设 $X$ 是 $n$ 次试验中的成功次数，则 $X \\sim B(n, p)$，"
                     "而 $\\hat p = X/n$。</p>"
                     "<p>由二项分布的方差 $\\mathrm{Var}(X) = np(1-p)$ 立刻得到</p>"
                     "<p>$SE(\\hat p) = \\dfrac{\\sqrt{p(1-p)}}{\\sqrt n}$。</p>"
                     "<p>中心极限定理保证：$n$ 足够大时 $\\hat p$ 近似服从正态 —— "
                     "图上的黄线就是这个正态近似，蓝柱是真实的模拟结果。"
                     "$n$ 越大两者越贴合。</p>")},
        {"title": "p = 0.5 为什么最坏",
         "content": ("<p>看 $p(1-p)$ 这个因子：它在 $p = 0.5$ 处取到最大值 $0.25$。</p>"
                     "<p>也就是说，**当总体比例接近一半时，抽样波动最大**；"
                     "$p$ 靠近 0 或 1 时反而更稳（结果几乎注定）。</p>"
                     "<p>实际做抽样调查时，如果事先不知道 $p$ 大概是多少，"
                     "就取最保守的 $p = 0.5$ 来估算所需样本量 —— "
                     "这样算出来的 $n$ 保证够用。</p>")},
        {"title": "精度的代价",
         "content": ("<p>95% 置信区间的半宽是 $1.96\\sqrt{p(1-p)/n}$。"
                     "取 $p = 0.5$ 时约等于 $\\dfrac{0.98}{\\sqrt n}$。</p>"
                     "<p>· $n = 100$ ⇒ 半宽约 $0.098$（±10 个百分点）；</p>"
                     "<p>· $n = 1000$ ⇒ 约 $0.031$（±3 个百分点）；</p>"
                     "<p>· 想要 ±1 个百分点 ⇒ 需要 $n \\approx 9600$。</p>"
                     "<p>这就是民意调查动辄上千人的原因。"
                     "而且注意：**精度按 $\\sqrt n$ 改善**，"
                     "从 ±3% 提到 ±1% 要把样本量增加到 9 倍。"
                     "拖滑块可以看到分布随 $n$ 迅速收窄。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "sampling": build_sampling,
    "unbiased": build_unbiased,
    "ci": build_ci,
    "ttest": build_ttest,
    "power": build_power,
    "regression": build_regression,
    "proportion": build_proportion,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="统计推断 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
