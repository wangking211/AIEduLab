#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「复数」交互网页。

全部数值由 lib/complex_kernel.py 的 sympy **精确**内核算出（含根式化简）。

覆盖七个题型（新课标必修二）：
  algebra     复数的加减法 = 向量加减（平行四边形）
  modulus     共轭与模：z·z̄ = |z|²
  multiply    乘法的几何意义：模相乘、辐角相加（旋转 + 伸缩）
  polar       三角形式与棣莫弗定理 zⁿ
  roots       n 次单位根（单位圆上均匀分布）
  quadratic   实系数一元二次方程的复根
  locus       几何轨迹 |z − z₀| = r

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

import sympy as sp                             # noqa: E402
import complex_kernel as K                     # noqa: E402
from skillkit import cli                       # noqa: E402

_MATHENV = {
    "sqrt": math.sqrt, "abs": abs, "min": min, "max": max, "pow": pow,
    "sign": lambda v: (v > 0) - (v < 0), "floor": math.floor, "ceil": math.ceil,
    "PI": math.pi, "E": math.e,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
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
# 1) 加法 = 平行四边形
# =====================================================================
AD_Z1 = (2.0, 1.0)
AD_R2 = 1.5
EXPR_AD_C = "cos(thdeg*PI/180)"
EXPR_AD_S = "sin(thdeg*PI/180)"
EXPR_AD_RE = f"{AD_R2}*({EXPR_AD_C})"
EXPR_AD_IM = f"{AD_R2}*({EXPR_AD_S})"
EXPR_AD_SRE = f"{AD_Z1[0]}+({EXPR_AD_RE})"
EXPR_AD_SIM = f"{AD_Z1[1]}+({EXPR_AD_IM})"
EXPR_AD_MAG = f"sqrt(({EXPR_AD_SRE})*({EXPR_AD_SRE})+({EXPR_AD_SIM})*({EXPR_AD_SIM}))"
AD_MAX = math.sqrt(AD_Z1[0] ** 2 + AD_Z1[1] ** 2) + AD_R2


def build_algebra() -> dict:
    z1 = K.cx(*AD_Z1)
    for th in (0, 30, 90, 180, 270, 350):
        rr = math.radians(th)
        z2 = K.cx(AD_R2 * math.cos(rr), AD_R2 * math.sin(rr))
        _agree(f"z₂ 的实部(θ={th})", EXPR_AD_RE, float(sp.N(K.re(z2))), tol=1e-12, thdeg=th)
        _agree(f"z₁+z₂ 的模(θ={th})", EXPR_AD_MAG,
               float(sp.N(K.modulus(K.cadd(z1, z2)))), tol=1e-9, thdeg=th)
    _agree("|z₁| = √5", f"sqrt(({AD_Z1[0]})*({AD_Z1[0]})+({AD_Z1[1]})*({AD_Z1[1]}))",
           float(sp.N(K.modulus(z1))), tol=1e-12)
    _agree("最大值 = |z₁| + |z₂|", EXPR_AD_MAG, AD_MAX, tol=1e-6, thdeg=26.56505117707799)
    # 平行四边形的两条对角线互相平分（用「对角线中点」验证几何自洽）
    for th in (20, 100, 240):
        rr = math.radians(th)
        z2 = K.cx(AD_R2 * math.cos(rr), AD_R2 * math.sin(rr))
        s = K.cadd(z1, z2)
        mid_diag1 = K.cdiv(K.cadd(0, s), 2)      # 对角线 0 → z₁+z₂ 的中点
        mid_diag2 = K.cdiv(K.cadd(z1, z2), 2)    # 对角线 z₁ → z₂ 的中点
        assert abs(complex(sp.N(mid_diag1 - mid_diag2))) < 1e-9
    # 平行四边形定律：|z₁+z₂|² + |z₁−z₂|² = 2(|z₁|² + |z₂|²)
    for th in (0, 75, 190, 300):
        rr = math.radians(th)
        z2 = K.cx(AD_R2 * math.cos(rr), AD_R2 * math.sin(rr))
        lhs = K.modulus2(K.cadd(z1, z2)) + K.modulus2(K.csub(z1, z2))
        rhs = 2 * (K.modulus2(z1) + K.modulus2(z2))
        assert abs(float(sp.N(lhs - rhs))) < 1e-9
    _agree("平行四边形定律成立", "0", 0.0, tol=1e-12)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "cplane_add", "thdeg": "thdeg",
                  "caption": "蓝 = z₁（定值）、粉 = z₂（辐角可调）、黄 = z₁+z₂"},
        "param": {"name": "thdeg", "label": "$z_2$ 的辐角 $\\theta$", "min": 0, "max": 355,
                  "step": 5, "value": 30, "unit": "°", "standard": 30,
                  "ticks": ["0", "30 (题设)", "180", "355"]},
        "readouts": [
            ro("z2re", "$z_2$ 的实部", EXPR_AD_RE, 4),
            ro("z2im", "$z_2$ 的虚部", EXPR_AD_IM, 4),
            ro("sre", "$z_1+z_2$ 的实部", EXPR_AD_SRE, 4),
            ro("sim", "$z_1+z_2$ 的虚部", EXPR_AD_SIM, 4),
            ro("mag", "$|z_1+z_2|$", EXPR_AD_MAG, 4),
            ro_status("mx", "是否取到三角不等式的上界（$z_2 \\parallel z_1$）",
                      f"abs(({EXPR_AD_MAG})-{AD_MAX!r})", 0.05, "<",
                      "同向：|z₁+z₂| 取到最大值 |z₁|+|z₂|", "未取到最大值"),
        ],
        "constant": {"of": "z1", "label": "$|z_1| = \\sqrt5$ 是定值 —— 只有 $z_2$ 在转"},
        "scalars": [{"name": "z1", "expr": f"sqrt({AD_Z1[0]}*{AD_Z1[0]}+{AD_Z1[1]}*{AD_Z1[1]})"}],
    }
    lesson = {
        "language": "zh-CN", "title": "复数的加减法与复平面",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>设 $z_1 = 2 + i$ 固定，$z_2$ 的模为 $1.5$、辐角为 $\\theta$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $z_1+z_2$ 的实部与虚部；</li>"
            "<li>拖动滑块，$|z_1+z_2|$ 在什么范围内变化？</li>"
            "<li>为什么复数的加法可以画成平行四边形？</li></ol>"),
        "answerLabel": "$\\theta = 30°$ 时",
        "answer": f"$z_1+z_2 \\approx {K.f(AD_Z1[0] + AD_R2 * math.cos(math.radians(30)), 3)}"
                  f" + {K.f(AD_Z1[1] + AD_R2 * math.sin(math.radians(30)), 3)}i$",
    }
    steps = [
        {"title": "复数就是平面上的点（向量）",
         "content": ("<p>把 $a+bi$ 看成平面上的点 $(a,\\ b)$ 或从原点出发的向量 —— "
                     "这就是**复平面**（高斯平面）：横轴放实部、纵轴放虚部。</p>"
                     "<p>于是两个复数相加，实部加实部、虚部加虚部，"
                     "与向量的加法**完全一样**。</p>"
                     "<p>图上画的正是以 $z_1$、$z_2$ 为邻边的平行四边形，"
                     "$z_1+z_2$ 是它的对角线。加法满足交换律与结合律，"
                     "因为向量的加法满足。</p>")},
        {"title": "减法的几何意义",
         "content": ("<p>$z_1 - z_2$ 对应「从 $z_2$ 指向 $z_1$ 的向量」，"
                     "所以</p>"
                     "<p>$|z_1 - z_2|$ = 复平面上 $z_1$ 与 $z_2$ 两点之间的距离。</p>"
                     "<p>这一条是后面所有「几何轨迹」题的基础"
                     "（本技能最后一个题型就是它的直接应用）。</p>")},
        {"title": "三角不等式",
         "content": ("<p>由平行四边形的几何立刻得到</p>"
                     "<p>$\\bigl||z_1| - |z_2|\\bigr| \\le |z_1+z_2| \\le |z_1| + |z_2|$。</p>"
                     "<p>右边取等号当且仅当 $z_1$、$z_2$ **同向**（辐角相同）；"
                     "左边取等号当且仅当它们**反向**。</p>"
                     "<p>拖滑块转到 $\\theta = 26.565^\\circ$（正好等于 $z_1$ 的辐角），"
                     "状态灯会亮 —— 那就是上界 $|z_1|+|z_2| \\approx "
                     f"{K.f(AD_MAX, 4)}$。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 共轭与模
# =====================================================================
MD_R = 2.5
EXPR_MD_RE = f"{MD_R}*cos(thdeg*PI/180)"
EXPR_MD_IM = f"{MD_R}*sin(thdeg*PI/180)"
EXPR_MD_M2 = f"({EXPR_MD_RE})*({EXPR_MD_RE})+({EXPR_MD_IM})*({EXPR_MD_IM})"
EXPR_MD_M = f"sqrt({EXPR_MD_M2})"


def build_modulus() -> dict:
    for th in (0, 40, 90, 210, 300):
        rr = math.radians(th)
        z = K.cx(MD_R * math.cos(rr), MD_R * math.sin(rr))
        _agree(f"实部(θ={th})", EXPR_MD_RE, float(sp.N(K.re(z))), tol=1e-12, thdeg=th)
        _agree(f"虚部(θ={th})", EXPR_MD_IM, float(sp.N(K.im(z))), tol=1e-12, thdeg=th)
        _agree(f"|z|²(θ={th})", EXPR_MD_M2, float(sp.N(K.modulus2(z))), tol=1e-9, thdeg=th)
        _agree(f"z·z̄ 落在实轴上(θ={th})", "0", float(sp.N(K.im(K.cmul(z, K.conj(z))))), tol=1e-12)
    _agree("|z| 恒为 2.5", EXPR_MD_M, MD_R, tol=1e-9, thdeg=137.0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "cplane_mod", "aa": EXPR_MD_RE, "bb": EXPR_MD_IM,
                  "caption": "蓝 = z、紫 = z̄（关于实轴对称）、黄点 = z·z̄（必在实轴上）"},
        "param": {"name": "thdeg", "label": "$z$ 的辐角 $\\theta$", "min": 0, "max": 355,
                  "step": 5, "value": 40, "unit": "°", "standard": 40,
                  "ticks": ["0", "40 (题设)", "90", "180", "355"]},
        "readouts": [
            ro("re", "$z$ 的实部 $a$", EXPR_MD_RE, 4),
            ro("im", "$z$ 的虚部 $b$", EXPR_MD_IM, 4),
            ro("m2", "$z\\cdot\\bar z = a^2+b^2$（定值）", EXPR_MD_M2, 4),
            ro("m", "$|z| = \\sqrt{a^2+b^2}$（定值）", EXPR_MD_M, 4),
            ro_status("real", "是否在实轴上（虚部为 0）", f"abs({EXPR_MD_IM})", 1e-6, "<",
                      "在实轴上：此时 z̄ = z", "不在实轴上：z̄ 是另一个点"),
        ],
        "constant": {"of": "m2", "label": "$z\\cdot\\bar z = |z|^2 = 6.25$ 恒成立 —— 与辐角无关"},
    }
    lesson = {
        "language": "zh-CN", "title": "共轭复数与模",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>设 $|z| = 2.5$，$z$ 的辐角为 $\\theta$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $z$ 与 $\\bar z$ 的实部、虚部；</li>"
            "<li>求 $z\\cdot\\bar z$，并说明它为什么一定是实数；</li>"
            "<li>$\\theta$ 变化时 $|z|$ 变吗？$z \\cdot \\bar z$ 变吗？</li></ol>"),
        "answerLabel": "$\\theta = 40°$ 时",
        "answer": f"$z\\cdot\\bar z = |z|^2 = {K.f(MD_R * MD_R, 4)}$，$|z| = {K.f(MD_R, 2)}$",
    }
    steps = [
        {"title": "共轭就是虚部变号",
         "content": ("<p>$z = a+bi$ 的共轭是 $\\bar z = a-bi$ —— "
                     "在复平面上就是**关于实轴的镜像**。</p>"
                     "<p>两条立刻可用的性质：$|\\bar z| = |z|$、"
                     "$\\arg\\bar z = -\\arg z$（辐角相反）。</p>")},
        {"title": "z·z̄ 为什么一定是实数",
         "content": ("<p>直接乘开：</p>"
                     "<p>$(a+bi)(a-bi) = a^2 - (bi)^2 = a^2 + b^2$。</p>"
                     "<p>虚部 $abi - abi$ 正好抵消，剩下的是 $a^2+b^2$ —— "
                     "一个非负实数。所以</p>"
                     "<p>$z\\bar z = |z|^2$，即 $|z| = \\sqrt{z\\bar z}$。</p>"
                     "<p>这条式子极其有用：它把「模」这种带根号的几何量，"
                     "变成了完全代数的乘法运算，是后面做除法、证恒等式的常用工具。"
                     "图上的黄点就在实轴上，位置正好是 $6.25$。</p>")},
        {"title": "拖滑块看到什么",
         "content": ("<p>$z$ 在半径为 $2.5$ 的圆上转，$\\bar z$ 是它的镜像 —— "
                     "两个点一起转，始终关于实轴对称。</p>"
                     "<p>但 $z \\cdot \\bar z$ 那个黄点**一动不动**，"
                     "永远停在实轴的 $6.25$ 处。这说明："
                     "**模只与到原点的距离有关，与方向无关** —— "
                     "这正是「模」这个概念的几何本质。</p>"
                     "<p>转到 $\\theta = 0$ 或 $180^\\circ$ 时 $z$ 落在实轴上，"
                     "此时 $z = \\bar z$，状态灯会亮。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 乘法的几何意义
# =====================================================================
MU_Z1 = (2.0, 1.0)
MU_R2 = 1.6
MU_ARG1 = math.degrees(math.atan2(MU_Z1[1], MU_Z1[0]))
MU_M1 = math.hypot(*MU_Z1)
EXPR_MU_ARG2 = "th2"
EXPR_MU_ARGP = f"{MU_ARG1!r}+th2"
EXPR_MU_MOD = f"{MU_M1!r}*{MU_R2}"


def build_multiply() -> dict:
    z1 = K.cx(*MU_Z1)
    for th in (0, 45, 90, 200, 330):
        rr = math.radians(th)
        z2 = K.cx(MU_R2 * math.cos(rr), MU_R2 * math.sin(rr))
        prod = K.cmul(z1, z2)
        _agree(f"|z₁z₂|(θ₂={th})", EXPR_MU_MOD, float(sp.N(K.modulus(prod))), tol=1e-9, th2=th)
        # 辐角相加（模 360）
        a = float(sp.N(K.arg_deg(prod)))
        _agree(f"arg(z₁z₂) ≡ θ₁+θ₂(θ₂={th})",
               f"(({EXPR_MU_ARGP})-a0)%360", 0.0, tol=1e-6, th2=th, a0=a)
    _agree("|z₁| = √5", f"{MU_M1!r}", float(sp.N(K.modulus(z1))), tol=1e-12)
    _agree("arg z₁ = 26.565°", f"{MU_ARG1!r}", float(sp.N(K.arg_deg(z1))), tol=1e-9)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "cplane_rot", "th2": "th2",
                  "caption": "黄弧的张角 = 蓝弧 + 粉弧：乘法就是「旋转 + 伸缩」"},
        "param": {"name": "th2", "label": "$z_2$ 的辐角 $\\theta_2$", "min": 0, "max": 355,
                  "step": 5, "value": 60, "unit": "°", "standard": 60,
                  "ticks": ["0", "60 (题设)", "180", "333 (绕回)", "355"]},
        "readouts": [
            ro("arg1", "$\\arg z_1$（定值）", f"{MU_ARG1!r}", 3, "°"),
            ro("arg2", "$\\arg z_2$", EXPR_MU_ARG2, 0, "°"),
            ro("argp", "$\\arg z_1 + \\arg z_2$", EXPR_MU_ARGP, 3, "°"),
            ro("mod", "$|z_1 z_2| = |z_1|\\cdot|z_2|$（定值）", EXPR_MU_MOD, 4),
            ro_status("wrap", "辐角相加是否超过一整圈（360°）", EXPR_MU_ARGP, 360, ">",
                      "超过 360°：乘积的辐角要绕回", "不到一圈"),
        ],
        "constant": {"of": "mod", "label": "$|z_1z_2| = |z_1|\\cdot|z_2|$ 恒成立 —— 旋转不改变「模相乘」这条规律"},
    }
    lesson = {
        "language": "zh-CN", "title": "复数乘法的几何意义",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>设 $z_1 = 2+i$ 固定，$z_2$ 的模为 $1.6$、辐角 $\\theta_2$ 可调。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求 $|z_1 z_2|$ 与 $\\arg(z_1z_2)$；</li>"
            "<li>拖动滑块，$|z_1z_2|$ 变吗？为什么？</li>"
            "<li>用一句话说出「乘以一个复数」在几何上做了什么。</li></ol>"),
        "answerLabel": "$\\theta_2 = 60°$ 时",
        "answer": f"$|z_1z_2| = \\sqrt5\\times1.6 \\approx {K.f(MU_M1 * MU_R2, 4)}$，"
                  f"$\\arg(z_1z_2) \\approx {K.f(MU_ARG1 + 60, 2)}°$",
    }
    steps = [
        {"title": "模相乘、辐角相加",
         "content": ("<p>设 $z_1 = r_1(\\cos\\theta_1 + i\\sin\\theta_1)$、"
                     "$z_2 = r_2(\\cos\\theta_2 + i\\sin\\theta_2)$。乘开并用和角公式：</p>"
                     "<p>$z_1z_2 = r_1r_2\\bigl[\\cos(\\theta_1+\\theta_2) "
                     "+ i\\sin(\\theta_1+\\theta_2)\\bigr]$。</p>"
                     "<p>所以</p>"
                     "<p>$|z_1z_2| = r_1r_2$，$\\arg(z_1z_2) = \\theta_1+\\theta_2$。</p>"
                     "<p>用一句话说：**乘以 $z_2$，就是把 $z_1$ 旋转 $\\theta_2$、"
                     "再伸缩 $r_2$ 倍**。这是复数最有价值的几何含义。</p>")},
        {"title": "为什么这条这么重要",
         "content": ("<p>因为它把「旋转」这种几何操作，翻译成了**乘法**这种代数操作。</p>"
                     "<p>于是：</p>"
                     "<p>· 乘 $i$ 就是逆时针转 $90^\\circ$（$|i| = 1$，不伸缩）；</p>"
                     "<p>· $n$ 个模为 1 的复数相乘，就是在圆上连续旋转；</p>"
                     "<p>· 平面上的旋转（连同伸缩）可以用复数乘法统一表示，"
                     "这正是计算机图形学与信号处理里用复数表示旋转的原因。</p>"
                     "<p>拖滑块可以看到：黄箭头（乘积）始终保持长度 "
                     f"$|z_1|\\cdot|z_2| \\approx {K.f(MU_M1 * MU_R2, 4)}$ 不变，"
                     "只是绕原点转 —— 读数区那个定值就是它。</p>")},
        {"title": "除法是乘法的逆",
         "content": ("<p>由同一条式子，除法就是「模相除、辐角相减」：</p>"
                     "<p>$\\left|\\dfrac{z_1}{z_2}\\right| = "
                     "\\dfrac{|z_1|}{|z_2|}$，"
                     "$\\arg\\dfrac{z_1}{z_2} = \\theta_1 - \\theta_2$。</p>"
                     "<p>而代数上做除法时要「分母实数化」"
                     "（分子分母同乘分母的共轭），两种做法结果一致 —— "
                     "这正是上一节 $z\\bar z = |z|^2$ 的用处。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 三角形式与棣莫弗定理
# =====================================================================
PO_BASE = 45.0
EXPR_PO_MOD = "pow(1,nn)"
EXPR_PO_ARG = f"{PO_BASE}*nn"
EXPR_PO_MOD360 = f"({EXPR_PO_ARG})-360*floor(({EXPR_PO_ARG})/360)"


def build_polar() -> dict:
    z = K.cx(math.cos(math.radians(PO_BASE)), math.sin(math.radians(PO_BASE)))
    for n in (1, 2, 3, 4, 6, 8, 12):
        _agree(f"z^{n} 的模", EXPR_PO_MOD,
               float(sp.N(K.modulus(K.power(z, n)))), tol=1e-9, nn=n)
        # 辐角：内核给出主值，页面上用的是 45n mod 360
        ang = (PO_BASE * n) % 360.0
        mod_arg = float(sp.N(K.arg_deg(K.power(z, n))))
        # 两者可能差 360 的整数倍，取模后比较
        assert abs(((mod_arg - ang) % 360) % 360) < 1e-6 or abs(((mod_arg - ang) % 360) - 360) < 1e-6
    _agree("z^4 = −1（辐角 180°）", EXPR_PO_MOD360, 180.0, tol=1e-9, nn=4)
    _agree("z^8 = 1（辐角 0°）", EXPR_PO_MOD360, 0.0, tol=1e-9, nn=8)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "cplane_pow", "nn": "nn",
                  "caption": "z 是单位复数（|z| = 1），所以 zⁿ 始终待在单位圆上"},
        "param": {"name": "nn", "label": "幂次 $n$", "min": 1, "max": 12,
                  "step": 1, "value": 3, "unit": "", "standard": 3,
                  "ticks": ["1", "3 (题设)", "4", "8 (回到 1)", "12"]},
        "readouts": [
            ro("n", "幂次 $n$", "nn", 0),
            ro("mod", "$|z^n| = 1^n$（恒为 1）", EXPR_PO_MOD, 4),
            ro("arg", "$\\arg z^n = 45°\\times n$", EXPR_PO_ARG, 0, "°"),
            ro("a360", "折算到 $0°\\sim360°$", EXPR_PO_MOD360, 2, "°"),
            ro_status("back", "是否回到起点（$z^n = 1$）", EXPR_PO_MOD360, 1e-6, "<",
                      "zⁿ = 1：转了整数圈回到 1", "还没转回 1"),
        ],
        "constant": {"of": "mod", "label": "$|z| = 1$ ⇒ $|z^n|$ 恒为 1 —— 只在单位圆上转，不伸缩"},
    }
    lesson = {
        "language": "zh-CN", "title": "三角形式与棣莫弗定理",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>设 $z = \\cos 45° + i\\sin 45°$，$n$ 为正整数。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $z$ 的模与辐角；</li>"
            "<li>求 $z^n$；</li>"
            "<li>$n$ 取何值时 $z^n = 1$？此时 $n$ 有什么特点？</li></ol>"),
        "answerLabel": "$n = 3$ 时",
        "answer": f"$z^3 = \\cos135° + i\\sin135° = "
                  f"{K.f(-math.sqrt(2) / 2, 4)} + {K.f(math.sqrt(2) / 2, 4)}i$",
    }
    steps = [
        {"title": "三角形式",
         "content": ("<p>任何非零复数都能写成</p>"
                     "<p>$z = r(\\cos\\theta + i\\sin\\theta)$，"
                     "其中 $r = |z|$、$\\theta = \\arg z$。</p>"
                     "<p>有时简记作 $r\\,\\text{cis}\\,\\theta$ 或 $re^{i\\theta}$"
                     "（后者是欧拉公式，大学内容）。把复数写成这种形式后，"
                     "乘除法的规则变得极其简单：**模相乘除、辐角相加减**。</p>")},
        {"title": "棣莫弗定理",
         "content": ("<p>把「辐角相加」重复 $n$ 次，就得到**棣莫弗定理**：</p>"
                     "<p>$[r(\\cos\\theta+i\\sin\\theta)]^n "
                     "= r^n(\\cos n\\theta + i\\sin n\\theta)$。</p>"
                     "<p>它把「开 $n$ 次方」这种麻烦事变成了「辐角除以 $n$」—— "
                     "下一节的 n 次单位根就是这么来的。</p>"
                     "<p>本页 $|z| = 1$，所以 $|z^n|$ 永远是 1，读数区那一行不动；"
                     "变化的只有辐角 $45n$。转到 $n = 8$ 时辐角累计 $360°$，"
                     "正好绕回起点，$z^8 = 1$ —— 状态灯会亮。</p>")},
        {"title": "用棣莫弗算具体值",
         "content": ("<p>例如求 $z^4$（$z = \\cos45°+i\\sin45°$）：</p>"
                     "<p>$z^4 = \\cos180° + i\\sin180° = -1$。</p>"
                     "<p>直接乘四次当然也能得到，但棣莫弗只要一步。"
                     "更有用的是：当 $n$ 很大时（比如求 $z^{100}$），"
                     "直接展开$($用二项式$)$几乎无法手算，而棣莫弗一秒就能给出答案。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) n 次单位根
# =====================================================================
EXPR_UR_GAP = "360/n"
EXPR_UR_SUM = "0"
EXPR_UR_PROD = "pow(-1,n-1)"


def build_roots() -> dict:
    for n in range(2, 13):
        roots = K.roots_of_unity(n)
        _agree(f"根的个数(n={n})", "n", len(roots), tol=1e-12, n=n)
        _agree(f"相邻辐角差(n={n})", EXPR_UR_GAP, 360.0 / n, tol=1e-12, n=n)
        assert abs(complex(sp.N(K.root_sum(n)))) < 1e-9, f"n={n} 的根之和应为 0"
        _agree(f"之积(n={n})", EXPR_UR_PROD, float(sp.N(K.root_product(n))), tol=1e-12, n=n)
        # 每个根的模都是 1
        for z in roots:
            assert abs(abs(complex(sp.N(z))) - 1) < 1e-9

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "unitroots", "n": "n",
                  "caption": "n 个根把单位圆 n 等分，构成正 n 边形的顶点"},
        "param": {"name": "n", "label": "根的个数 $n$", "min": 2, "max": 12,
                  "step": 1, "value": 5, "unit": "", "standard": 5,
                  "ticks": ["2 (±1)", "3 (1,ω,ω²)", "5 (题设)", "8", "12"]},
        "readouts": [
            ro("n", "根的个数 $n$", "n", 0),
            ro("gap", "相邻两根的辐角差", EXPR_UR_GAP, 2, "°"),
            ro("sum", "全部根之和（恒为 0）", EXPR_UR_SUM, 0),
            ro("prod", "全部根之积 $=(-1)^{n-1}$", EXPR_UR_PROD, 0),
            ro_status("hasneg", "是否包含 $-1$（即 $n$ 为偶数）",
                      "n-2*floor(n/2)", 0, "==",
                      "n 为偶数：根里有 −1", "n 为奇数：根里没有 −1"),
        ],
        "constant": {"of": "sum", "label": "全部 $n$ 个根之和恒为 0 —— 与 $n$ 无关"},
    }
    lesson = {
        "language": "zh-CN", "title": "n 次单位根",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>求方程 $z^n = 1$ 的全部复数根（$n \\ge 2$）。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>解出全部 $n$ 个根；</li>"
            "<li>它们在复平面上怎么分布？</li>"
            "<li>证明这 $n$ 个根之和恒为 0。</li></ol>"),
        "answerLabel": "$n = 3$ 时",
        "answer": "$z = 1,\\ \\omega,\\ \\omega^2$，其中 "
                  "$\\omega = -\\dfrac12 + \\dfrac{\\sqrt3}{2}i$，且 $1+\\omega+\\omega^2 = 0$",
    }
    steps = [
        {"title": "从棣莫弗定理解出全部根",
         "content": ("<p>设 $z = r(\\cos\\theta+i\\sin\\theta)$，由 $z^n = 1$ 得</p>"
                     "<p>$r^n = 1 \\Rightarrow r = 1$（模是正数，只有一个解）；</p>"
                     "<p>$n\\theta = k\\cdot360° \\Rightarrow \\theta = "
                     "\\dfrac{k\\cdot360°}{n}$，$k = 0,1,\\dots,n-1$。</p>"
                     "<p>所以 $n$ 个根是</p>"
                     "<p>$z_k = \\cos\\dfrac{360°k}{n} + i\\sin\\dfrac{360°k}{n}$。</p>"
                     "<p>它们**模都是 1**、**辐角依次相差 $360°/n$** —— "
                     "于是均匀地分布在一个圆上，构成正 $n$ 边形的顶点。</p>")},
        {"title": "为什么k只取到 n−1",
         "content": ("<p>$k$ 取 $n$ 时辐角是 $360°$，与 $k=0$ 落在同一点；"
                     "再往后只是重复。所以**恰好有 $n$ 个不同的根** —— "
                     "这与代数基本定理一致：$z^n - 1 = 0$ 是 $n$ 次方程，"
                     "在复数范围内恰好有 $n$ 个根。</p>"
                     "<p>顺带一提：在实数范围内 $z^n=1$ 常常只有一个或两个解"
                     "（$n$ 为奇数时只有 $z=1$，为偶数时还有 $z=-1$），"
                     "在复数范围内却总是 $n$ 个。这就是复数的一大好处："
                     "**「方程有几个根」不再取决于碰巧的实数限制**。</p>")},
         {"title": "根之和为 0",
         "content": ("<p>由韦达定理，$z^n - 1 = 0$ 的 $n$ 个根之和等于"
                     "$z^{n-1}$ 项的系数取负 —— 而那一项**根本不存在**，"
                     "所以和为 0。</p>"
                     "<p>也可以直接看几何：这 $n$ 个点关于原点高度对称，"
                     "它们的「重心」必然落在原点，向量和自然为零。</p>"
                     "<p>$n=3$ 时就是熟悉的 $1 + \\omega + \\omega^2 = 0$。"
                     "这个恒等式在化简高次幂时非常好用（把 $\\omega^2$ 换成 "
                     "$-1-\\omega$ 就能不断降次）。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 一元二次方程的复根
# =====================================================================
EXPR_QR_D = "pp*pp-4"
EXPR_QR_SD = "sqrt(max(0,pp*pp-4))"
EXPR_QR_RE1 = f"-pp/2+({EXPR_QR_SD})/2"
EXPR_QR_RE2 = f"-pp/2-({EXPR_QR_SD})/2"
EXPR_QR_IM = "sqrt(max(0,4-pp*pp))/2"
EXPR_QR_SUM = "-pp"
EXPR_QR_PROD = "1"


def build_quadratic() -> dict:
    for p in (-4.0, -2.5, -1.0, 0.0, 1.0, 3.0):
        rs = K.quadratic_roots(1, p, 1)
        _agree(f"判别式(p={p})", EXPR_QR_D, float(sp.N(K.discriminant(1, p, 1))), tol=1e-12, pp=p)
        _agree(f"根₁的实部(p={p})", EXPR_QR_RE1, float(sp.N(K.re(rs[0]))), tol=1e-12, pp=p)
        _agree(f"根₂的实部(p={p})", EXPR_QR_RE2, float(sp.N(K.re(rs[1]))), tol=1e-12, pp=p)
        # 虚部：判别式 < 0 时非零，否则为 0
        want_im = abs(float(sp.N(K.im(rs[0]))))
        _agree(f"根的虚部(p={p})", EXPR_QR_IM, want_im, tol=1e-9, pp=p)
        _agree(f"两根之和(p={p})", EXPR_QR_SUM, float(sp.N(K.re(rs[0] + rs[1]))), tol=1e-12, pp=p)
        _agree(f"两根之积(p={p})", EXPR_QR_PROD, float(sp.N(K.re(rs[0] * rs[1]))), tol=1e-12, pp=p)
        # 实系数 ⇒「根的集合」对共轭封闭：Δ < 0 时两根互为共轭，Δ ≥ 0 时两根都是实数
        Dv = float(sp.N(K.discriminant(1, p, 1)))
        if Dv < 0:
            assert abs(complex(sp.N(rs[1] - K.conj(rs[0])))) < 1e-12
        else:
            assert abs(float(sp.N(K.im(rs[0])))) < 1e-12
            assert abs(float(sp.N(K.im(rs[1])))) < 1e-12
    _agree("p=1 时虚部 = √3/2", EXPR_QR_IM, math.sqrt(3) / 2, tol=1e-12, pp=1.0)
    _agree("|p| ≥ 2 时虚部为 0", EXPR_QR_IM, 0.0, tol=1e-12, pp=3.0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "qroots", "pp": "pp",
                  "caption": "判别式 < 0 时，两个根关于实轴对称（共轭）"},
        "param": {"name": "pp", "label": "一次项系数 $p$（$x^2+px+1=0$）",
                  "min": -4, "max": 4, "step": 0.1, "value": 1.0,
                  "unit": "", "standard": 1.0,
                  "ticks": ["-4", "-2 (临界)", "1 (题设)", "2 (临界)", "4"]},
        "readouts": [
            ro("d", "判别式 $\\Delta = p^2-4$", EXPR_QR_D, 4),
            ro("re1", "根₁的实部", EXPR_QR_RE1, 4),
            ro("re2", "根₂的实部", EXPR_QR_RE2, 4),
            ro("im", "根的虚部（两根互为 $\\pm$）", EXPR_QR_IM, 4),
            ro("sum", "两根之和（恒为 $-p$）", EXPR_QR_SUM, 4),
            ro("prod", "两根之积（恒为 1）", EXPR_QR_PROD, 4),
            ro_status("cx", "是否出现复根（$\\Delta < 0$）", EXPR_QR_D, 0, "<",
                      "Δ < 0：一对共轭复根", "Δ ≥ 0：两个实根"),
        ],
        "constant": {"of": "prod", "label": "两根之积**恒为 1** —— 韦达定理对复根同样成立"},
    }
    lesson = {
        "language": "zh-CN", "title": "一元二次方程的复根",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>解方程 $x^2 + px + 1 = 0$（$p$ 为实数且可调）。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出判别式，并说明 $p$ 取何值时出现复根；</li>"
            "<li>写出复根的具体形式；</li>"
            "<li>验证韦达定理（两根之和、两根之积）仍然成立。</li></ol>"),
        "answerLabel": "$p = 1$ 时",
        "answer": f"$x = -\\dfrac12 \\pm \\dfrac{{\\sqrt3}}{{2}}i$"
                  f"（$\\Delta = {K.f(-3, 0)}$）",
    }
    steps = [
        {"title": "判别式决定根的类型",
         "content": ("<p>对实系数方程 $ax^2+bx+c=0$，判别式 $\\Delta = b^2-4ac$：</p>"
                     "<p>· $\\Delta > 0$：两个不等实根；</p>"
                     "<p>· $\\Delta = 0$：一个二重实根；</p>"
                     "<p>· $\\Delta < 0$：**没有实根，但有两个共轭复根**。</p>"
                     "<p>本页 $\\Delta = p^2 - 4$，所以 $|p| < 2$ 时出现复根 —— "
                     "拖滑块越过 $\\pm2$，图上两个点会从实轴上「跳」出来，"
                     "变成上下对称的一对。</p>")},
        {"title": "复根的形式",
         "content": ("<p>求根公式不变，只是当 $\\Delta < 0$ 时 $\\sqrt\\Delta$ "
                     "要按复数理解。记 $\\Delta = -|\\Delta|$，则</p>"
                     "<p>$x = \\dfrac{-p \\pm \\sqrt{-\\Delta}\\,i}{2}$。</p>"
                     "<p>写成标准形式：实部 $-\\dfrac{p}{2}$、"
                     "虚部 $\\pm\\dfrac{\\sqrt{-\\Delta}}{2}$。</p>"
                     "<p>由于 $a$、$b$、$c$ 都是实数，$\\sqrt\\Delta$ 一定是"
                     "纯虚数或实数，所以**两个根必然互为共轭** —— "
                     "图上那两个点永远关于实轴对称。</p>")},
        {"title": "韦达定理为什么还成立",
         "content": ("<p>把方程写成 $x^2 + px + 1 = (x-x_1)(x-x_2)$，展开对比系数：</p>"
                     "<p>$x_1 + x_2 = -p$，$x_1x_2 = 1$。</p>"
                     "<p>这个推导过程**完全没有用到判别式的符号**，"
                     "所以它对实根、重根、复根**一律成立**。</p>"
                     "<p>读数区里「之和」跟着 $p$ 走、「之积」永远停在 1，"
                     "拖滑块把 $p$ 从实根调到复根，两行数值都不中断 —— "
                     "这就是韦达定理的普适性。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 几何轨迹
# =====================================================================
LC_Z0 = (1.0, 1.0)
LC_M0 = math.hypot(*LC_Z0)
LC_TH = 40.0
EXPR_LC_RE = f"{LC_Z0[0]}+rr*cos({LC_TH}*PI/180)"
EXPR_LC_IM = f"{LC_Z0[1]}+rr*sin({LC_TH}*PI/180)"
EXPR_LC_DIST = f"sqrt((({EXPR_LC_RE})-{LC_Z0[0]})*(({EXPR_LC_RE})-{LC_Z0[0]})+(({EXPR_LC_IM})-{LC_Z0[1]})*(({EXPR_LC_IM})-{LC_Z0[1]}))"


def build_locus() -> dict:
    z0 = K.cx(*LC_Z0)
    for r in (0.4, 1.0, 1.5, 2.8):
        p = K.circle_locus_pt(z0, r, LC_TH)
        _agree(f"圆上点实部(r={r})", EXPR_LC_RE, float(sp.N(K.re(p))), tol=1e-12, rr=r)
        _agree(f"圆上点虚部(r={r})", EXPR_LC_IM, float(sp.N(K.im(p))), tol=1e-12, rr=r)
        _agree(f"|z−z₀| = r(r={r})", EXPR_LC_DIST, float(sp.N(K.modulus(p - z0))), tol=1e-9, rr=r)
    _agree("|z₀| = √2", f"sqrt({LC_Z0[0]}*{LC_Z0[0]}+{LC_Z0[1]}*{LC_Z0[1]})",
           float(sp.N(K.modulus(z0))), tol=1e-12)
    # 垂直平分线
    A, B = K.cx(0, 0), K.cx(4, 0)
    for yv in (0.0, 2.0, -1.5):
        q = K.same_distance_pt(A, B, yv)
        assert abs(float(sp.N(K.modulus(q - A) - K.modulus(q - B)))) < 1e-9
    _agree("垂直平分线到两点距离相等", "0", 0.0, tol=1e-12)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "locus", "rr": "rr",
                  "caption": "把 |z − z₀| 读成「z 到 z₀ 的距离」，轨迹就是一个圆"},
        "param": {"name": "rr", "label": "半径 $r$", "min": 0.4, "max": 2.8,
                  "step": 0.05, "value": 1.5, "unit": "", "standard": 1.5,
                  "ticks": ["0.4", "1.414 (=|z₀|)", "1.5 (题设)", "2.8"]},
        "readouts": [
            ro("re", "圆上点（$40°$ 方向）的实部", EXPR_LC_RE, 4),
            ro("im", "圆上点的虚部", EXPR_LC_IM, 4),
            ro("dist", "$|z - z_0|$（恒等于 $r$）", EXPR_LC_DIST, 4),
            ro("area", "圆的面积 $\\pi r^2$", "PI*rr*rr", 4),
            ro_status("has0", "原点是否在圆内（$r > |z_0|$）", "rr", LC_M0, ">",
                      "原点在圆内：|z₀| 小于半径", "原点不在圆内"),
        ],
        "constant": {"of": "dist", "label": "$|z-z_0|$ 恒等于半径 $r$ —— 这正是「圆的定义」"},
    }
    lesson = {
        "language": "zh-CN", "title": "复数的几何轨迹",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>设 $z_0 = 1+i$，$r$ 为可调正数。说明满足下列条件的点 $z$ 的轨迹：</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>$|z - z_0| = r$；</li>"
            "<li>$|z| = |z - 4|$；</li>"
            "<li>$|z - z_0| \\le r$。</li></ol>"),
        "answerLabel": "$|z-z_0| = r$",
        "answer": "圆（圆心 $z_0$、半径 $r$）；当 $r > |z_0| = \\sqrt2$ 时原点在圆内",
    }
    steps = [
        {"title": "把模读成距离",
         "content": ("<p>$|z_1 - z_2|$ 在复平面上的意义就是 $z_1$ 与 $z_2$ 两点的距离"
                     "（上一节「减法的几何意义」已经说明了）。</p>"
                     "<p>于是 $|z - z_0| = r$ 不过是在说："
                     "**点 $z$ 到定点 $z_0$ 的距离恒为 $r$** —— "
                     "这正是圆的定义（椭圆的定义也是从这种写法来的）。</p>"
                     "<p>图上的蓝圆就是它；拖滑块改 $r$，圆跟着胀缩，"
                     "而「$|z-z_0|$ 等于半径」这条始终成立。</p>")},
        {"title": "最常见的三种轨迹",
         "content": ("<p>· $|z - z_0| = r$：**圆**，圆心 $z_0$、半径 $r$；</p>"
                     "<p>· $|z - z_0| \\le r$：**圆盘**（圆内加圆上）；</p>"
                     "<p>· $|z - A| = |z - B|$：到 $A$、$B$ 距离相等的点 —— "
                     "**线段 $AB$ 的垂直平分线**。</p>"
                     "<p>判断方法很统一：把 $z$ 写成 $x+yi$，"
                     "把 $|\\cdot|$ 按「两点距离」展开成 $\\sqrt{(\\Delta x)^2+(\\Delta y)^2}$，"
                     "两边平方，就化成了熟悉的解析几何方程。"
                     "内核里的 `same_distance_pt` 正是这么做的。</p>")},
        {"title": "一个容易搞错的细节",
         "content": ("<p>不要看到 $|z|$ 就以为「$z$ 的模等于某个数」只是数值条件 —— "
                     "**每一个模的等式都是一个几何条件**，画出来就是一条曲线。</p>"
                     "<p>反过来，很多几何问题用复数写起来会短得惊人："
                     "比如「到两点距离相等」用坐标法要写一堆根式，"
                     "用复数就是 $|z-A| = |z-B|$ 一行。</p>"
                     "<p>把滑块拖到 $r \\le \\sqrt2 \\approx 1.414$ 时，"
                     "原点会落到圆外（或圆上），状态灯会翻转。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "algebra": build_algebra,
    "modulus": build_modulus,
    "multiply": build_multiply,
    "polar": build_polar,
    "roots": build_roots,
    "quadratic": build_quadratic,
    "locus": build_locus,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="复数 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
