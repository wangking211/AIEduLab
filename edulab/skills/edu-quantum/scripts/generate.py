#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「量子力学入门」交互网页。

全部数值由 lib/quantum_kernel.py 现算：能级、波长、透射系数都是解析式；
**有限深势阱的束缚态能级用二分法真解超越方程**（不是查表）。

覆盖七个题型（8.04 的一维部分）：
  well          无限深势阱：能级 n²、波函数、概率密度、节点
  debroglie     德布罗意波长 λ = h/p
  uncertainty   不确定性原理 Δx·Δp ≥ ħ/2
  harmonic      一维谐振子：等间距能级与零点能
  tunneling     矩形势垒的隧道效应 T(E)
  finite_well   有限深势阱的束缚态（数值解）
  wavepacket    自由高斯波包的色散

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

import quantum_kernel as K                      # noqa: E402
from skillkit import cli                        # noqa: E402

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
# 1) 无限深势阱
# =====================================================================
WL_L_NM = 0.5                      # 阱宽（nm）
WL_NMAX = 6
WL_LEVELS = [K.well_energy_ev(n, WL_L_NM) for n in range(1, WL_NMAX + 1)]
WL_EMAX = WL_LEVELS[-1] * 1.07
WL_SAMPLES = 161
WL_PSI, WL_PROB = [], []
for _n in range(1, WL_NMAX + 1):
    _p, _q = [], []
    _mx = 0.0
    for _i in range(WL_SAMPLES):
        _x = WL_L_NM * _i / (WL_SAMPLES - 1)
        _v = K.well_psi(_n, K.nm_to_m(_x), K.nm_to_m(WL_L_NM))
        _p.append(_v)
        _mx = max(_mx, abs(_v))
    _mx = _mx or 1.0
    for _i in range(WL_SAMPLES):
        _x = WL_L_NM * _i / (WL_SAMPLES - 1)
        _v = K.well_prob(_n, K.nm_to_m(_x), K.nm_to_m(WL_L_NM))
        _q.append(_v / (_mx * _mx))
    WL_PSI.append([round(v / _mx, 5) for v in _p])
    WL_PROB.append([round(v, 5) for v in _q])
EXPR_WL_E = "[" + ",".join(repr(round(v, 6)) for v in WL_LEVELS) + "][nq-1]"


def build_well() -> dict:
    for n in range(1, WL_NMAX + 1):
        # 数组字面量按 6 位小数舍入 ⇒ 容差必须与舍入匹配（不能用 1e-9）
        _agree(f"E{n}", EXPR_WL_E, K.well_energy_ev(n, WL_L_NM), tol=1e-6, nq=n)
        _agree(f"E{n}/E₁ = n²", EXPR_WL_E + f"/({WL_LEVELS[0]!r})", float(n * n), tol=1e-6, nq=n)
        # 与「n² 倍基态」的解析形式交叉核对（这里才用焦耳口径）
        assert abs(K.well_energy(n, K.nm_to_m(WL_L_NM)) / K.well_energy(1, K.nm_to_m(WL_L_NM))
                   - n * n) < 1e-9
    assert abs(WL_LEVELS[0] - 1.5044) < 2e-3
    for i in range(WL_NMAX):
        assert max(abs(v) for v in WL_PSI[i]) > 0.99
        assert all(0.0 <= v <= 1.0001 for v in WL_PROB[i])

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "wellplot", "nq": "nq",
                  "levels": WL_LEVELS, "psiAll": WL_PSI, "probAll": WL_PROB,
                  "emax": WL_EMAX,
                  "caption": "红墙 = 无穷高势壁；黄线 = 当前能级；蓝 = ψₙ，绿 = |ψₙ|²"},
        "param": {"name": "nq", "label": "量子数 $n$", "min": 1, "max": WL_NMAX,
                  "step": 1, "value": 1, "unit": "", "standard": 1,
                  "ticks": ["1 (基态)", "2", "3", "4", "6"]},
        "readouts": [
            ro("n", "量子数 $n$", "nq", 0),
            ro("e", "能级 $E_n$", EXPR_WL_E, 4, "eV"),
            ro("ratio", "$E_n / E_1$（应为 $n^2$）", f"({EXPR_WL_E})/({WL_LEVELS[0]!r})", 2),
            ro("nodes", "波函数节点数 $n-1$", "nq-1", 0),
            ro_status("ground", "是否为基态（$n = 1$）", "nq", 1.5, "<",
                      "基态：能量最低、无节点", "激发态：有节点，能量更高"),
        ],
        "constant": {"of": "e1", "label": "$E_1 = 1.5044$ eV 是定值 —— 所有能级都是它的 $n^2$ 倍"},
        "scalars": [{"name": "e1", "expr": f"{WL_LEVELS[0]!r}"}],
    }
    lesson = {
        "language": "zh-CN", "title": "无限深势阱：能级为什么按 n² 增长",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>电子被限制在宽 $L = 0.5\\ \\mathrm{nm}$ 的一维无限深势阱中。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出能级公式并求 $E_1$；</li>"
            "<li>拖动滑块，$E_n/E_1$ 等于多少？</li>"
            "<li>为什么 $n$ 越大，波函数的节点越多？</li></ol>"),
        "answerLabel": "$n = 1$ 时",
        "answer": f"$E_1 = \\dfrac{{h^2}}{{8mL^2}} = {K.f(WL_LEVELS[0], 4)}$ eV，"
                  f"$E_n = n^2E_1$",
    }
    steps = [
        {"title": "边界条件决定一切",
         "content": ("<p>势阱里 $V = 0$，定态薛定谔方程是 $-\\dfrac{\\hbar^2}{2m}"
                     "\\psi'' = E\\psi$，解是正弦函数。</p>"
                     "<p>但两端是**无穷高**的壁，波函数在那里必须为 0（否则概率会流出去）。"
                     "于是 $\\sin(kL) = 0$，即 $kL = n\\pi$，$n = 1, 2, 3,\\dots$</p>"
                     "<p>把 $k = n\\pi/L$ 代回 $E = \\dfrac{\\hbar^2k^2}{2m}$：</p>"
                     "<p>$E_n = \\dfrac{n^2h^2}{8mL^2}$。</p>"
                     "<p>关键是：**边界条件把连续的 $k$ 变成了离散的**，能量才被量子化。</p>")},
        {"title": "为什么是 n² 而不是 n",
         "content": ("<p>因为 $E \\propto k^2$，而 $k \\propto n$，所以 $E \\propto n^2$。</p>"
                     "<p>物理图像：$n$ 越大，波函数在阱内**振荡得越快**（波长越短），"
                     "曲率越大，动能就越高。图上的节点数（$n-1$ 个）正是振荡次数的体现。</p>"
                     "<p>这与后面的谐振子形成鲜明对照 —— 谐振子的能级是**等间距**的，"
                     "因为它的势不是「平底」而是抛物线形。</p>")},
        {"title": "拖滑块看到什么",
         "content": ("<p>· $E_n/E_1$ 依次是 1、4、9、16、25、36 —— 全是平方数；</p>"
                     "<p>· 波函数的节点数依次是 0、1、2、3、4、5；</p>"
                     "<p>· 概率密度 $|\\psi_n|^2$ 的峰数 = $n$（经典粒子会均匀分布，"
                     "而量子粒子在某些位置**根本不会出现**）。</p>"
                     "<p>顺带一提：把 $L$ 缩小 10 倍，$E_1$ 会变成 100 倍 —— "
                     "这正是量子点（半导体纳米晶）尺寸越小、发光越偏蓝的原因。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 德布罗意波长
# =====================================================================
DB_LO, DB_HI = 1.0, 100.0
DB_LMAX = 1.35
DB_PTS = 201
DB_LAM = [K.m_to_nm(K.de_broglie_ev(K.M_E, DB_LO + (DB_HI - DB_LO) * i / (DB_PTS - 1)))
          for i in range(DB_PTS)]
EXPR_DB_LAM = "1.2264/sqrt(ekin)"


def build_debroglie() -> dict:
    for e in (1.0, 4.0, 25.0, 100.0):
        _agree(f"λ(E={e})", EXPR_DB_LAM, K.m_to_nm(K.de_broglie_ev(K.M_E, e)), tol=1e-4, ekin=e)
    _agree("λ ∝ 1/√E（4 倍动能 ⇒ 半波长）", EXPR_DB_LAM, K.m_to_nm(K.de_broglie_ev(K.M_E, 4.0)) * 2,
           tol=1e-4, ekin=1.0)
    assert abs(DB_LAM[0] - 1.2264) < 2e-3 and abs(DB_LAM[-1] - 0.12264) < 2e-4
    assert all(DB_LAM[i] > DB_LAM[i + 1] for i in range(DB_PTS - 1)), "λ 应随动能单调下降"

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "debroglie", "ekin": "ekin",
                  "lamAll": DB_LAM, "lamNow": EXPR_DB_LAM,
                  "elo": DB_LO, "ehi": DB_HI, "lmax": DB_LMAX,
                  "caption": "λ = h/√(2mE)：动能越大波长越短，但降得越来越慢"},
        "param": {"name": "ekin", "label": "电子动能 $E$", "min": DB_LO, "max": DB_HI,
                  "step": 1, "value": 10.0, "unit": "eV", "standard": 10.0,
                  "ticks": ["1", "10 (题设)", "50", "100"]},
        "readouts": [
            ro("e", "电子动能 $E$", "ekin", 0, "eV"),
            ro("lam", "德布罗意波长 $\\lambda$", EXPR_DB_LAM, 5, "nm"),
            ro("pm", "$\\lambda$（pm）", f"({EXPR_DB_LAM})*1000", 2, "pm"),
            ro("cmp", "$\\lambda$ 是原子直径（0.1 nm）的几倍",
               f"({EXPR_DB_LAM})/0.1", 3),
            ro_status("diff", "波长是否与原子尺度可比（$\\ge 0.1$ nm）", EXPR_DB_LAM, 0.1, ">",
                      "与原子间距同量级：能观察到衍射", "远小于原子尺度：几乎表现为经典粒子"),
        ],
        "constant": {"of": "c1", "label": "$\\lambda = h/\\sqrt{2mE}$ —— 1 eV 的电子对应 1.2264 nm（记住这个数）"},
        "scalars": [{"name": "c1", "expr": "1.2264"}],
    }
    lesson = {
        "language": "zh-CN", "title": "德布罗意波长",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>电子的动能为 $E$（可调）。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出德布罗意关系，并求 $\\lambda$ 与 $E$ 的关系；</li>"
            "<li>动能增大 4 倍，波长变为几分之几？</li>"
            "<li>为什么宏观物体的波动性观察不到？</li></ol>"),
        "answerLabel": "$E = 10$ eV 时",
        "answer": f"$\\lambda = \\dfrac{{h}}{{\\sqrt{{2mE}}}} \\approx "
                  f"{K.f(K.m_to_nm(K.de_broglie_ev(K.M_E, 10.0)), 5)}$ nm",
    }
    steps = [
        {"title": "从光子推广到实物粒子",
         "content": ("<p>光子有 $p = h/\\lambda$。德布罗意大胆假设：**实物粒子也一样**。</p>"
                     "<p>于是 $\\lambda = \\dfrac{h}{p}$。对非相对论粒子 $p = \\sqrt{2mE}$，"
                     "所以</p>"
                     "<p>$\\lambda = \\dfrac{h}{\\sqrt{2mE}} \\propto \\dfrac{1}{\\sqrt E}$。</p>"
                     "<p>这个假设在 1927 年被戴维孙-革末实验证实："
                     "电子束射到镍晶体上真的出现了**衍射条纹**。</p>")},
        {"title": "为什么宏观看不到",
         "content": ("<p>关键在 $h$ 极小（$6.63\\times10^{-34}$ J·s）。</p>"
                     "<p>一个 $1\\ \\mathrm{g}$ 的小球以 $1\\ \\mathrm{m/s}$ 运动，"
                     "$\\lambda \\approx 6.6\\times10^{-31}\\ \\mathrm{m}$ —— "
                     "比原子核还小 20 个数量级，任何实验都测不出。</p>"
                     "<p>而电子在 1 eV 时 $\\lambda \\approx 1.23\\ \\mathrm{nm}$，"
                     "**恰好与晶格常数同量级**，所以能衍射。"
                     "拖滑块可以看到：要让 $\\lambda$ 与原子尺度可比，动能得在 eV 量级。</p>")},
        {"title": "这一条撑起了多少东西",
         "content": ("<p>· **电子显微镜**：用电子代替光，波长小得多 ⇒ 分辨率高得多；</p>"
                     "<p>· **电子衍射**：直接测晶体结构；</p>"
                     "<p>· **量子点的颜色**：尺寸决定能级间距（上一节的 $L$ 效应）；</p>"
                     "<p>· **物质的稳定性**：原子里的电子若没有波动性，"
                     "会螺旋掉进原子核 —— 正是波动性带来的「驻波条件」让它稳定。</p>"
                     "<p>顺带记住一个常用值：**1 eV 的电子波长约 1.23 nm**。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 不确定性原理
# =====================================================================
UN_XSPAN = 6.0
UN_DXMAX = 2.0
UN_DPMIN = K.HBAR / (2.0 * K.nm_to_m(UN_DXMAX))
EXPR_UN_DX = "sigx*1e-9"
EXPR_UN_DP = "1.054571817e-34/(2*(sigx*1e-9))"
EXPR_UN_PROD = f"({EXPR_UN_DX})*({EXPR_UN_DP})"
# 显示用量纲化单位（直接 toFixed(6) 会把 5e-10 显示成 0.000000）
EXPR_UN_DP25 = f"({EXPR_UN_DP})/1e-25"        # 以 1e-25 kg·m/s 为单位
EXPR_UN_PROD34 = f"({EXPR_UN_PROD})/1e-34"    # 以 1e-34 为单位
EXPR_UN_HBAR34 = "1.054571817e-34/2/1e-34"    # ħ/2 以 1e-34 为单位


def build_uncertainty() -> dict:
    for sx in (0.1, 0.5, 1.0, 2.0):
        _agree(f"Δp(σ={sx})", EXPR_UN_DP, K.uncertainty_min_dp(K.nm_to_m(sx)), tol=1e-9, sigx=sx)
        _agree(f"Δx·Δp(σ={sx})", EXPR_UN_PROD, K.HBAR / 2, tol=1e-9, sigx=sx)
    _agree("ħ/2", f"{K.HBAR!r}/2", K.HBAR / 2, tol=1e-12)
    # 显示单位换算也要对账（页面用的是量纲化单位）
    _agree("Δp 的显示单位换算", EXPR_UN_DP25, K.uncertainty_min_dp(K.nm_to_m(1.0)) / 1e-25,
           tol=1e-9, sigx=1.0)
    _agree("Δx·Δp 的显示单位换算", EXPR_UN_PROD34, (K.HBAR / 2) / 1e-34, tol=1e-9, sigx=1.0)
    _agree("ħ/2 的显示单位换算", EXPR_UN_HBAR34, (K.HBAR / 2) / 1e-34, tol=1e-9)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "uncert", "sigx": "sigx",
                  "dpNow": EXPR_UN_DP, "prod": EXPR_UN_PROD,
                  "hbar2": K.HBAR / 2, "dxmax": UN_DXMAX, "dpmax": UN_DPMIN * 1.05,
                  "xspan": UN_XSPAN,
                  "caption": "上：高斯波包与 Δx；下：Δp = ħ/(2Δx) 的双曲线（黄点只能在线上滑）"},
        "param": {"name": "sigx", "label": "波包宽度 $\\sigma$", "min": 0.1, "max": UN_DXMAX,
                  "step": 0.05, "value": 1.0, "unit": "nm", "standard": 1.0,
                  "ticks": ["0.1 (很窄)", "1.0 (题设)", "2.0 (很宽)"]},
        "readouts": [
            ro("dx", "$\\Delta x = \\sigma$", "sigx", 3, "nm"),
            ro("dp", "$\\Delta p$", EXPR_UN_DP25, 4, "×10⁻²⁵ kg·m/s"),
            ro("prod", "$\\Delta x\\cdot\\Delta p$", EXPR_UN_PROD34, 4, "×10⁻³⁴"),
            ro("hbar2", "$\\hbar/2$（下界，定值）", EXPR_UN_HBAR34, 4, "×10⁻³⁴"),
            ro_status("eq", "是否取到等号（高斯波包）", f"({EXPR_UN_PROD})/({K.HBAR / 2!r})", 1.0, "==",
                      "取到等号：这是**最小不确定**波包", "未取到等号"),
        ],
        "constant": {"of": "hbar2", "label": "$\\hbar/2 = 5.27\\times10^{-35}$ 是下界 —— 任何状态都跨不过它"},
    }
    lesson = {
        "language": "zh-CN", "title": "不确定性原理",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>一个电子用高斯波包描述，位置的标准差为 $\\sigma$（可调）。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出不确定性关系；</li>"
            "<li>求 $\\Delta p$，并验证 $\\Delta x\\cdot\\Delta p$；</li>"
            "<li>为什么这个「不确定」不是仪器精度的问题？</li></ol>"),
        "answerLabel": "$\\sigma = 1.0$ nm 时",
        "answer": f"$\\Delta x\\cdot\\Delta p = \\dfrac{{\\hbar}}{{2}} = "
                  f"{K.sci(K.HBAR / 2, 3)}$（高斯波包取到等号）",
    }
    steps = [
        {"title": "它不是「测不准」，而是「不存在」",
         "content": ("<p>常见误解：以为「测不准」是指仪器不够好。不是。</p>"
                     "<p>正确的说法是：**一个粒子同时具有确定位置和确定动量的状态根本不存在**。"
                     "这不是技术限制，而是量子态的数学结构决定的。</p>"
                     "<p>形式化地：$\\Delta x\\cdot\\Delta p \\ge \\dfrac{\\hbar}{2}$，"
                     "其中 $\\Delta x$、$\\Delta p$ 是**标准差**。</p>"
                     "<p>注意这个下界极小（$5.27\\times10^{-35}$），"
                     "所以宏观物体完全感觉不到它。</p>")},
        {"title": "高斯波包恰好取到等号",
         "content": ("<p>对高斯形波包 $\\psi \\propto e^{-x^2/(4\\sigma^2)}$，"
                     "可以精确算出 $\\Delta x = \\sigma$、"
                     "$\\Delta p = \\dfrac{\\hbar}{2\\sigma}$。</p>"
                     "<p>两者相乘**恒等于** $\\dfrac{\\hbar}{2}$ —— "
                     "与 $\\sigma$ 无关。图上那个黄点只能沿着红色双曲线滑动，"
                     "永远碰不到左下角（那才是「同时很确定」的区域）。</p>"
                     "<p>这类状态叫**最小不确定态**，激光里的相干态就是它的一个例子。</p>")},
        {"title": "为什么世界没有塌掉",
         "content": ("<p>把电子限制在原子尺度（$\\Delta x \\sim 10^{-10}$ m）时，"
                     "$\\Delta p \\sim 5\\times10^{-25}$ kg·m/s，"
                     "对应的动能约 $10\\ \\mathrm{eV}$ —— "
                     "这正是**原子中电子的典型能量尺度**。</p>"
                     "<p>换句话说：原子那么大、能量那么高，"
                     "**很大程度上是被不确定性原理「撑」出来的**。"
                     "如果电子能安静地待在核附近，原子早就塌缩了。</p>"
                     "<p>反过来，把波包压得很窄（$\\sigma$ 拖到 0.1 nm），"
                     "动量就变得极不确定 —— 动能随之暴涨。这也是量子点尺寸越小能级越高的另一种说法。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 一维谐振子
# =====================================================================
HM_OM_MIN, HM_OM_MAX, HM_OM_STEP = 0.5, 3.0, 0.05
HM_NMAX = 5
HM_EV_PER_UNIT = K.j_to_ev(K.HBAR * 1e15)      # ω 以 1e15 rad/s 计时，ħω 的 eV 值
EXPR_HM_HW = f"om*{HM_EV_PER_UNIT!r}"
EXPR_HM_LEVELS = [f"{n + 0.5}*({EXPR_HM_HW})" for n in range(HM_NMAX + 1)]
HM_EMAX = (HM_NMAX + 0.5) * HM_EV_PER_UNIT * HM_OM_MAX * 1.05


def build_harmonic() -> dict:
    for om in (0.5, 1.0, 2.0, 3.0):
        _agree(f"ħω(ω={om})", EXPR_HM_HW, K.j_to_ev(K.HBAR * om * 1e15), tol=1e-12, om=om)
        for n in range(HM_NMAX + 1):
            _agree(f"E{n}(ω={om})", EXPR_HM_LEVELS[n],
                   K.j_to_ev(K.harmonic_energy(n, om * 1e15)), tol=1e-12, om=om)
    _agree("零点能 = ħω/2", EXPR_HM_LEVELS[0], K.j_to_ev(K.harmonic_zero_point(1e15)), tol=1e-12, om=1.0)
    assert HM_EV_PER_UNIT > 0

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "harmonic", "om": "om",
                  "levels": EXPR_HM_LEVELS, "emax": HM_EMAX, "nmax": HM_NMAX,
                  "hwEv": EXPR_HM_HW, "zeroEv": EXPR_HM_LEVELS[0],
                  "caption": "抛物线势 + 等间距能级；绿线是零点能（n=0 也不是 0）"},
        "param": {"name": "om", "label": "角频率 $\\omega$（$\\times 10^{15}$ rad/s）",
                  "min": HM_OM_MIN, "max": HM_OM_MAX, "step": HM_OM_STEP,
                  "value": 1.0, "unit": "×10¹⁵ rad/s", "standard": 1.0,
                  "ticks": ["0.5", "1 (题设)", "2", "3"]},
        "readouts": [
            ro("hw", "能级间距 $\\hbar\\omega$", EXPR_HM_HW, 4, "eV"),
            ro("zero", "零点能 $E_0 = \\hbar\\omega/2$", EXPR_HM_LEVELS[0], 4, "eV"),
            ro("e1", "$E_1$", EXPR_HM_LEVELS[1], 4, "eV"),
            ro("e2", "$E_2$", EXPR_HM_LEVELS[2], 4, "eV"),
            ro_status("gap", "能级间距是否大于 1 eV", EXPR_HM_HW, 1.0, ">",
                      "间距 > 1 eV：达到可见光/近紫外量级", "间距 < 1 eV：远红外量级"),
        ],
        "constant": {"of": "zero", "label": "$E_0 = \\hbar\\omega/2 > 0$ 恒成立 —— 零点能无法消除"},
    }
    lesson = {
        "language": "zh-CN", "title": "一维谐振子与零点能",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>质量为 $m$ 的粒子处在势 $V(x) = \\dfrac12 m\\omega^2x^2$ 中。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出能级公式；</li>"
            "<li>能级间距是多少？与 $n$ 有关吗？</li>"
            "<li>$n = 0$ 时能量为 0 吗？为什么？</li></ol>"),
        "answerLabel": "$\\omega = 10^{15}$ rad/s 时",
        "answer": f"$\\hbar\\omega = {K.f(K.j_to_ev(K.HBAR * 1e15), 4)}$ eV，"
                  f"$E_0 = {K.f(K.j_to_ev(K.harmonic_zero_point(1e15)), 4)}$ eV",
    }
    steps = [
        {"title": "能级是等间距的",
         "content": ("<p>解薛定谔方程得到</p>"
                     "<p>$E_n = \\left(n + \\dfrac12\\right)\\hbar\\omega$，$n = 0, 1, 2, \\dots$</p>"
                     "<p>相邻能级之差恒为 $\\hbar\\omega$ —— **与 $n$ 无关**。"
                     "图上的黄线间距肉眼可见地相等，这就是它和无限深势阱（$n^2$）的最大差别。</p>"
                     "<p>为什么？因为抛物势的曲率处处不同，"
                     "粒子在势阱底附近「慢」、在两边「快」，"
                     "恰好补偿了 $n$ 带来的效应。数学上则是因为"
                     "薛定谔方程经过变换后与厄米多项式相关。</p>")},
        {"title": "零点能：为什么不能是 0",
         "content": ("<p>经典图像里，粒子可以安静地停在势阱底 $x = 0$，能量为 0。</p>"
                     "<p>量子力学说不行：停在 $x = 0$ 意味着 $\\Delta x = 0$，"
                     "由不确定性原理 $\\Delta p = \\infty$ —— 动能无穷大。</p>"
                     "<p>折中的结果是 $E_0 = \\dfrac{\\hbar\\omega}{2}$，"
                     "**这就是零点能**。图上的绿线（$n=0$）明显高于势阱底。</p>"
                     "<p>它的实验证据非常直接：**液氦在绝对零度下也不会凝固**"
                     "（零点运动让原子无法「锁」进晶格）。"
                     "卡西米尔效应、兰姆位移也都与零点能有关。</p>")},
        {"title": "它为什么无处不在",
         "content": ("<p>因为**任何势阱的底部都可以近似成抛物线**：</p>"
                     "<p>把 $V(x)$ 在极小点展开，一次项为 0，"
                     "剩下的最低阶项就是 $\\dfrac12V''(x_0)(x-x_0)^2$ —— "
                     "标准谐振子形式。</p>"
                     "<p>所以谐振子是量子力学里最重要的模型之一："
                     "分子振动、晶格振动（声子）、电磁场模式（光子）"
                     "**全都可以当作谐振子**。"
                     "量子场论里的「场」本质上就是无穷多个谐振子。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 隧道效应
# =====================================================================
TN_V0_EV, TN_A_NM = 5.0, 1.0
TN_V0, TN_A = K.ev_to_j(TN_V0_EV), K.nm_to_m(TN_A_NM)
TN_R_MIN, TN_R_MAX, TN_R_STEP = 0.1, 2.0, 0.05
TN_RATIOS = [round(TN_R_MIN + TN_R_STEP * i, 2)
             for i in range(int(round((TN_R_MAX - TN_R_MIN) / TN_R_STEP)) + 1)]
TN_T = [K.tunneling_T(r * TN_V0, TN_V0, TN_A) for r in TN_RATIOS]
TN_KA = [(K.tunneling_kappa(r * TN_V0, TN_V0) * TN_A if r < 1 else 0.0) for r in TN_RATIOS]
TN_PTS = 201
# 从 E/V₀ = 0.005 起步（E = 0 时透射系数无定义，且曲线在原点附近本来就趋于 0）
TN_CURVE = [K.tunneling_T((0.005 + (TN_R_MAX - 0.005) * i / (TN_PTS - 1)) * TN_V0, TN_V0, TN_A)
            for i in range(TN_PTS)]
EXPR_TN_RATIO = "eratio"
# 滑块是 eratio，档位序号要**由它推出来**（MATHENV 里没有 round，用 floor(x+0.5) 代替）
EXPR_TN_IDX = f"floor((eratio-{TN_R_MIN!r})/{TN_R_STEP!r}+0.5)+1"
EXPR_TN_T = "[" + ",".join(repr(round(v, 10)) for v in TN_T) + "][" + EXPR_TN_IDX + "-1]"
EXPR_TN_KA = "[" + ",".join(repr(round(v, 8)) for v in TN_KA) + "][" + EXPR_TN_IDX + "-1]"


def build_tunneling() -> dict:
    for r in (0.1, 0.5, 0.9, 1.0, 1.5, 2.0):
        _agree(f"T(E/V₀={r})", EXPR_TN_T, K.tunneling_T(r * TN_V0, TN_V0, TN_A),
               tol=1e-6, eratio=r)
    # 单调性（E < V₀ 段）与量级
    assert all(TN_T[i] < TN_T[i + 1] for i in range(len(TN_T) - 1) if TN_RATIOS[i + 1] < 1.0)
    assert TN_T[0] < 1e-4 and TN_T[-1] <= 1.0
    assert all(0.0 <= v <= 1.0 for v in TN_CURVE)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "tunnel", "eratio": "eratio", "ei": EXPR_TN_IDX,
                  "tAll": TN_CURVE, "TArr": TN_T, "kappaArr": TN_KA, "emaxR": TN_R_MAX,
                  "caption": "上：势垒与波（黄线凹陷 = 势垒内指数衰减）；下：T(E) 曲线"},
        "param": {"name": "eratio", "label": "$E/V_0$", "min": TN_R_MIN, "max": TN_R_MAX,
                  "step": TN_R_STEP, "value": 0.5, "unit": "", "standard": 0.5,
                  "ticks": ["0.1", "0.5 (题设)", "1 (E=V₀)", "2"]},
        "readouts": [
            ro("r", "$E/V_0$", EXPR_TN_RATIO, 2),
            ro("e", "入射能量 $E$", f"({EXPR_TN_RATIO})*{TN_V0_EV!r}", 3, "eV"),
            ro("ka", "势垒内的 $\\kappa a$", EXPR_TN_KA, 4),
            ro("t", "透射系数 $T$", EXPR_TN_T, 8),
            ro_status("classical", "是否处于经典禁区（$E < V_0$）", EXPR_TN_RATIO, 1.0, "<",
                      "经典禁区：经典上过不去，但量子上有非零透射", "经典允许区（但仍有量子反射）"),
        ],
        "constant": {"of": "v0", "label": "势垒 $V_0 = 5$ eV、宽 $a = 1$ nm 是定值"},
        "scalars": [{"name": "v0", "expr": f"{TN_V0_EV!r}"}],
    }
    lesson = {
        "language": "zh-CN", "title": "隧道效应",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>电子遇到高 $V_0 = 5\\ \\mathrm{eV}$、宽 $a = 1\\ \\mathrm{nm}$ 的矩形势垒，"
            "入射能量 $E$ 可调。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出透射系数 $T(E)$ 的表达式；</li>"
            "<li>$E < V_0$ 时 $T$ 为什么不为 0？</li>"
            "<li>$E > V_0$ 时 $T$ 等于 1 吗？</li></ol>"),
        "answerLabel": "$E/V_0 = 0.5$ 时",
        "answer": f"$T \\approx {K.sci(K.tunneling_T(0.5 * TN_V0, TN_V0, TN_A), 3)}$，"
                  f"$\\kappa a \\approx {K.f(K.tunneling_kappa(0.5 * TN_V0, TN_V0) * TN_A, 3)}$",
    }
    steps = [
        {"title": "波函数会「渗」进禁区",
         "content": ("<p>在势垒内 $E < V_0$，薛定谔方程的解不再是振荡的，"
                     "而是**指数衰减**的：$\\psi \\propto e^{-\\kappa x}$，"
                     "其中</p>"
                     "<p>$\\kappa = \\dfrac{\\sqrt{2m(V_0-E)}}{\\hbar}$。</p>"
                     "<p>经典粒子到这里就「没能量」了，但**波函数不是能量，它只是振幅** —— "
                     "只要势垒不太厚，它还能在另一侧留下非零的值，于是就有透射概率。</p>"
                     "<p>图上那条黄线在势垒内明显凹陷，就是 $e^{-\\kappa x}$ 的衰减。</p>")},
        {"title": "T 的表达式与量级",
         "content": ("<p>矩形势垒的精确结果是</p>"
                     "<p>$T = \\dfrac{1}{1 + \\dfrac{V_0^2\\sinh^2(\\kappa a)}"
                     "{4E(V_0-E)}}$（$E < V_0$）。</p>"
                     "<p>$\\kappa a$ 越大，$T$ 越小，且是**指数级**地小："
                     "$T \\sim e^{-2\\kappa a}$。所以势垒加宽 1 nm，"
                     "$T$ 可能掉几个数量级 —— 拖滑块可以看到 $T$ 在 0.1 处只有 $10^{-4}$ 量级。</p>"
                     "<p>这也是扫描隧道显微镜（STM）能测到**原子级起伏**的原因："
                     "探针高度变一个原子，隧道电流就变一个数量级。</p>")},
        {"title": "E > V₀ 时也不等于 1",
         "content": ("<p>经典上「有足够能量就一定能翻过去」，但量子上"
                     "**势垒边缘会反射**，所以 $T < 1$。</p>"
                     "<p>更奇怪的是：$T$ 随 $E$ **振荡**（图上下半部分的锯齿段），"
                     "因为势垒内变成了振荡解，$\\sin^2(k_2a)$ 会周期性地让 $T$ 回到 1"
                     "（**共振透射**）。</p>"
                     "<p>另外注意 $E \\to V_0^-$ 时 $T$ **不是** 1，"
                     "而是 $\\dfrac{1}{1 + mV_0a^2/(2\\hbar^2)}$ —— "
                     "本页把它叫「匹配点透射率」，读数区里能看到它明显小于 1。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 有限深势阱（数值解）
# =====================================================================
FW_A_NM = 1.0
FW_A = K.nm_to_m(FW_A_NM)
FW_D_MIN, FW_D_MAX, FW_D_STEP = 2.0, 12.0, 0.5
FW_DEPTHS = [round(FW_D_MIN + FW_D_STEP * i, 2)
             for i in range(int(round((FW_D_MAX - FW_D_MIN) / FW_D_STEP)) + 1)]
FW_LEVELS, FW_COUNTS, FW_PSI = [], [], []
FW_SAMPLES = 201
for _V in FW_DEPTHS:
    _lv = [K.j_to_ev(e) for e in K.finite_well_levels(K.ev_to_j(_V), FW_A, K.M_E, n_max=6)]
    FW_LEVELS.append([round(v, 5) for v in _lv])
    FW_COUNTS.append(K.finite_well_count(K.ev_to_j(_V), FW_A))
    # 基态波函数示意：阱内正弦、阱外指数衰减（用 k、κ 由基态能量定出）
    _ps = []
    if _lv:
        _E = K.ev_to_j(_lv[0])
        _k = math.sqrt(2 * K.M_E * _E) / K.HBAR
        _kap = math.sqrt(2 * K.M_E * (K.ev_to_j(_V) - _E)) / K.HBAR
        _amp = 0.0
        _vals = []
        for _i in range(FW_SAMPLES):
            _x = (-1.5 + 3.0 * _i / (FW_SAMPLES - 1)) * FW_A_NM      # −1.5a … 1.5a
            if abs(_x) <= FW_A_NM / 2:
                _v = math.cos(_k * _x)
            else:
                _v = math.cos(_k * FW_A_NM / 2) * math.exp(-_kap * (abs(_x) - FW_A_NM / 2))
            _vals.append(_v)
            _amp = max(_amp, abs(_v))
        _amp = _amp or 1.0
        _ps = [round(v / _amp, 5) for v in _vals]
    else:
        _ps = [0.0] * FW_SAMPLES
    FW_PSI.append(_ps)
FW_INF_E1 = K.well_energy_ev(1, FW_A_NM)
EXPR_FW_DEPTH = "depth"
EXPR_FW_IDX = f"floor((depth-{FW_D_MIN!r})/{FW_D_STEP!r}+0.5)+1"
EXPR_FW_N = "[" + ",".join(str(v) for v in FW_COUNTS) + "][" + EXPR_FW_IDX + "-1]"
EXPR_FW_E1 = "[" + ",".join(repr(v[0]) if v else "0" for v in FW_LEVELS) + "][" + EXPR_FW_IDX + "-1]"


def build_finite_well() -> dict:
    for i, V in enumerate(FW_DEPTHS):
        _lv = K.finite_well_levels(K.ev_to_j(V), FW_A, K.M_E, n_max=6)
        _agree(f"束缚态个数(V={V})", EXPR_FW_N, len(_lv), tol=1e-12, depth=V)
        assert len(_lv) == FW_COUNTS[i], f"V={V} 的个数应与解析上界一致"
        assert all(0 < e < K.ev_to_j(V) for e in _lv)
        if _lv:
            _agree(f"基态(V={V})", EXPR_FW_E1, K.j_to_ev(_lv[0]), tol=1e-5, depth=V)
            # 有限阱基态必低于同宽无限阱
            assert K.j_to_ev(_lv[0]) < FW_INF_E1
    # 阱越深束缚态越多（非严格单调，但总体上升）
    assert FW_COUNTS[-1] > FW_COUNTS[0]

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "finitewell", "depth": "depth", "di": EXPR_FW_IDX,
                  "levelsAll": FW_LEVELS, "countAll": FW_COUNTS, "psiAll": FW_PSI,
                  "infE1": FW_INF_E1,
                  "caption": "有限深势阱：波函数渗出阱外（蓝线），能级由超越方程数值解出"},
        "param": {"name": "depth", "label": "阱深 $V_0$", "min": FW_D_MIN, "max": FW_D_MAX,
                  "step": FW_D_STEP, "value": 5.0, "unit": "eV", "standard": 5.0,
                  "ticks": ["2", "5 (题设)", "8", "12"]},
        "readouts": [
            ro("v", "阱深 $V_0$", EXPR_FW_DEPTH, 1, "eV"),
            ro("n", "束缚态个数", EXPR_FW_N, 0),
            ro("e1", "基态 $E_1$", EXPR_FW_E1, 4, "eV"),
            ro("inf", "同宽无限阱的基态（定值）", f"{FW_INF_E1!r}", 4, "eV"),
            ro_status("lower", "有限阱基态是否低于同宽无限阱", EXPR_FW_E1, FW_INF_E1, "<",
                      "更低：波函数渗出阱外，动能更小", "不低于"),
        ],
        "constant": {"of": "inf", "label": "阱宽固定 1 nm ⇒ 同宽无限阱的基态恒为 0.3761 eV"},
    }
    lesson = {
        "language": "zh-CN", "title": "有限深势阱：数值解超越方程",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>电子处在深 $V_0$（可调）、宽 $a = 1\\ \\mathrm{nm}$ 的有限深势阱中。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出阱内、阱外的波函数形式；</li>"
            "<li>为什么能级要解超越方程而不是简单公式？</li>"
            "<li>为什么有限阱的基态比同宽无限阱更低？</li></ol>"),
        "answerLabel": "$V_0 = 5$ eV 时",
        "answer": f"束缚态个数 = {FW_COUNTS[FW_DEPTHS.index(5.0)]}，"
                  f"基态 $E_1 = {K.f(FW_LEVELS[FW_DEPTHS.index(5.0)][0], 4)}$ eV",
    }
    steps = [
        {"title": "两段解、两个衔接条件",
         "content": ("<p>阱内 $V = 0$：解是 $\\cos(kx)$（偶态）或 $\\sin(kx)$（奇态），"
                     "$k = \\dfrac{\\sqrt{2mE}}{\\hbar}$。</p>"
                     "<p>阱外 $V = V_0 > E$：解必须**衰减**（否则不归一），"
                     "形如 $e^{-\\kappa|x|}$，$\\kappa = \\dfrac{\\sqrt{2m(V_0-E)}}{\\hbar}$。</p>"
                     "<p>在阱壁上要求 $\\psi$ 与 $\\psi'$ **连续**，"
                     "两个条件一联立就得到超越方程：</p>"
                     "<p>偶态 $k\\tan\\dfrac{ka}{2} = \\kappa$；"
                     "奇态 $-k\\cot\\dfrac{ka}{2} = \\kappa$。</p>")},
        {"title": "为什么要数值解",
         "content": ("<p>因为方程里 $E$ 同时出现在 $k$ 和 $\\kappa$ 里，"
                     "而且一个在三角函数里、一个在根号里 —— **解不出显式表达式**。</p>"
                     "<p>本页的做法是**真解**：把 $(0, V_0)$ 扫一遍，"
                     "找出函数变号的位置再二分求根。"
                     "为了让扫描不出假根，把方程两边乘掉了分母"
                     "（$\\tan$ 在 $\\pi/2$ 处有极点，直接扫符号会把它误判成变号）—— "
                     "这是实现上的一个真坑。</p>"
                     "<p>结果可以用一个漂亮的公式核对：束缚态个数 = "
                     "$\\left\\lceil\\dfrac{\\sqrt{2mV_0}\\,a}{\\pi\\hbar}\\right\\rceil$。"
                     "读数区里的个数与它**完全一致**。</p>")},
        {"title": "为什么基态更低",
         "content": ("<p>无限深势阱要求波函数在壁上**恰好为 0**；"
                     "有限阱只要求它**平滑地接上衰减段**。</p>"
                     "<p>后者约束更松 ⇒ 波函数可以「鼓」出去一点 ⇒ "
                     "曲率更小 ⇒ **动能更小** ⇒ 基态能量更低。</p>"
                     "<p>图上的蓝线在阱外明显不为 0，这就是「渗出」。"
                     "读数区给出基态与同宽无限阱基态的比值（约 0.8 上下）。</p>"
                     "<p>拖滑块把 $V_0$ 调浅：束缚态会一个个「逃出去」，"
                     "个数减少 —— 这正是「势阱太浅就困不住粒子」。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 自由高斯波包（色散）
# =====================================================================
WP_SIG0_NM = 1.0
WP_K0 = 1e8
WP_TMAX = 1.0e-13
WP_NT = 26
WP_NX = 121
WP_XLO, WP_XHI = -12.0, 12.0
WP_TAIL = WP_TMAX / (WP_NT - 1)
WP_T = [WP_TAIL * i for i in range(WP_NT)]
WP_SIG = [K.m_to_nm(K.gauss_packet_sigma(K.nm_to_m(WP_SIG0_NM), t)) for t in WP_T]
WP_CENTER = [K.m_to_nm(K.gauss_packet_speed(WP_K0) * t) for t in WP_T]
WP_P = []
for _i, _t in enumerate(WP_T):
    _row = []
    for _j in range(WP_NX):
        _x = K.nm_to_m(WP_XLO + (WP_XHI - WP_XLO) * _j / (WP_NX - 1))
        _row.append(round(K.gauss_packet_prob(_x, _t, K.nm_to_m(WP_SIG0_NM), WP_K0) * 1e-9, 6))
    WP_P.append(_row)
WP_PMAX = max(max(r) for r in WP_P) * 1.05
WP_TREF = [0, (WP_NT - 1) // 2, WP_NT - 1]
WP_PREF = [WP_P[i] for i in WP_TREF]
EXPR_WP_SIG = "[" + ",".join(repr(round(v, 6)) for v in WP_SIG) + "][ti-1]"


def build_wavepacket() -> dict:
    for i, t in enumerate(WP_T):
        _agree(f"σ(t={t:.2e})", EXPR_WP_SIG, K.m_to_nm(K.gauss_packet_sigma(K.nm_to_m(1.0), t)),
               tol=1e-6, ti=i + 1)
    assert WP_SIG[0] == WP_SIG0_NM
    assert all(WP_SIG[i] < WP_SIG[i + 1] for i in range(WP_NT - 1)), "σ 应随时间单调增大"
    assert all(WP_CENTER[i] < WP_CENTER[i + 1] for i in range(WP_NT - 1)), "中心应匀速右移"
    # 每个时刻的总概率都应接近 1（数值积分）
    for i in (0, WP_NT // 2, WP_NT - 1):
        dx = (WP_XHI - WP_XLO) / (WP_NX - 1)
        tot = sum(WP_P[i]) * dx
        assert abs(tot - 1.0) < 0.06, f"t 索引 {i} 的面积 {tot} 偏离 1 过多"
    # 峰值随时间下降
    peaks = [max(r) for r in WP_P]
    assert all(peaks[i] > peaks[i + 1] for i in range(WP_NT - 1))

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "wavepacket", "ti": "ti",
                  "tAll": WP_T, "pAll": WP_P, "pRef": WP_PREF, "tRef": [WP_T[i] for i in WP_TREF],
                  "sigAll": WP_SIG, "sig0": WP_SIG0_NM,
                  "speed": K.gauss_packet_speed(WP_K0),
                  "centerAll": WP_CENTER,
                  "xlo": WP_XLO, "xhi": WP_XHI, "pmax": WP_PMAX,
                  "caption": "波包随时间自己变宽（灰线是更早时刻）；峰值下降但面积守恒"},
        "param": {"name": "ti", "label": "时间档位（0 → 0.1 ps）", "min": 1, "max": WP_NT,
                  "step": 1, "value": 1, "unit": "", "standard": 1,
                  "ticks": ["t=0", "中间", "0.1 ps"]},
        "readouts": [
            ro("t", "时间 $t$", f"[" + ",".join(repr(round(v, 20)) for v in WP_T) + "][ti-1]",
               15, "s"),
            ro("sig", "波包宽度 $\\sigma(t)$", EXPR_WP_SIG, 4, "nm"),
            ro("cen", "波包中心位置", "[" + ",".join(repr(round(v, 6)) for v in WP_CENTER) + "][ti-1]",
               4, "nm"),
            ro("v", "群速度 $v = \\hbar k_0/m$（定值）", f"{K.gauss_packet_speed(WP_K0)!r}", 4, "m/s"),
            ro_status("spread", "是否已显著展宽（$\\sigma/\\sigma_0 > 2$）",
                      f"({EXPR_WP_SIG})/{WP_SIG0_NM!r}", 2.0, ">",
                      "已展宽到 2 倍以上：色散明显", "展宽还不明显"),
        ],
        "constant": {"of": "s0", "label": "$\\sigma_0 = 1$ nm 是定值；波包中心以恒定群速度平移"},
        "scalars": [{"name": "s0", "expr": f"{WP_SIG0_NM!r}"}],
    }
    lesson = {
        "language": "zh-CN", "title": "自由波包的色散",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>自由电子用高斯波包描述，$t=0$ 时宽度 $\\sigma_0 = 1\\ \\mathrm{nm}$，"
            "平均波数 $k_0 = 10^8\\ \\mathrm{m^{-1}}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $\\sigma(t)$ 的表达式；</li>"
            "<li>波包中心怎么运动？</li>"
            "<li>为什么自由波包一定会越变越宽？</li></ol>"),
        "answerLabel": "$t = 0.1$ ps 时",
        "answer": f"$\\sigma \\approx {K.f(WP_SIG[-1], 3)}$ nm"
                  f"（$\\sigma_0 = 1$ nm 的 {K.f(WP_SIG[-1], 2)} 倍）",
    }
    steps = [
        {"title": "自由波包的精确解",
         "content": ("<p>自由粒子（$V = 0$）的高斯波包有**解析解**：</p>"
                     "<p>$|\\psi(x,t)|^2 = \\dfrac{1}{\\sqrt{2\\pi}\\,\\sigma(t)}"
                     "\\exp\\left[-\\dfrac{(x-vt)^2}{2\\sigma(t)^2}\\right]$，</p>"
                     "<p>其中 $\\sigma(t) = \\sigma_0\\sqrt{1 + \\left(\\dfrac{\\hbar t}"
                     "{2m\\sigma_0^2}\\right)^2}$，$v = \\dfrac{\\hbar k_0}{m}$。</p>"
                     "<p>两个要点：**中心以恒定群速度平移**（波包整体在走），"
                     "**宽度随时间增长**（波包在散）。</p>")},
        {"title": "为什么一定会散",
         "content": ("<p>因为波包是**不同动量成分的叠加**，而每个成分的速度是 $p/m$ —— "
                     "动量大的跑得快，动量小的跑得慢。</p>"
                     "<p>跑着跑着，快的跑到前面、慢的落到后面，波包就散开了。"
                     "这就是**色散**（与光学里不同波长的光折射率不同是同一回事）。</p>"
                     "<p>注意：这不是「粒子坏了」，而是**动量不确定性的必然结果**。"
                     "由 $\\Delta p = \\hbar/(2\\sigma_0)$ 可知，"
                     "$\\sigma_0$ 越小 $\\Delta p$ 越大，散得就越快 —— "
                     "这也解释了为什么展宽时间正比于 $\\sigma_0^2$。</p>")},
        {"title": "它为什么重要",
         "content": ("<p>· **波包不散才能叫「粒子」**：真实的「粒子」需要某种机制把波包束缚住"
                     "（势阱、自聚焦非线性、或者质量很大）。</p>"
                     "<p>· **量子计算/量子通信**里，波包色散是退相干的主要来源之一；</p>"
                     "<p>· 反过来，**色散本身可以被利用**：光纤通信里用「色散补偿」"
                     "让脉冲在长距离传输后仍保持形状。</p>"
                     "<p>本页把 $\\sigma_0$ 取成 1 nm 是为了让展宽在 0.1 ps 内肉眼可见 —— "
                     "对电子来说这个尺度确实很小。把质量换成宏观物体，"
                     "展宽时间会长到宇宙年龄量级，波包「看起来」永远是稳的。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "well": build_well,
    "debroglie": build_debroglie,
    "uncertainty": build_uncertainty,
    "harmonic": build_harmonic,
    "tunneling": build_tunneling,
    "finite_well": build_finite_well,
    "wavepacket": build_wavepacket,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="量子力学入门 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
