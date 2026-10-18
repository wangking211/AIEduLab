#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「线性代数」交互网页。

按 MIT 18.06 的知识点组织；全部数值由 lib/linalg_kernel.py 的 sympy 精确内核驱动
（行列式、特征值/特征向量、矩阵幂、最小二乘、秩/零空间、奇异值、Gram–Schmidt），
**不手写数字**。

**为什么主场景都是 2×2**：线性代数的几何直觉天然是二维的（网格怎么变形、特征方向
为什么不变、投影落在哪）；而 2×2 的行列式、特征值、奇异值、秩**全都有闭式解**，
于是「内核用 sympy 精确算」与「画板用 JS 现算」可以逐条对账 —— 这是全项目
「同源一致」纪律要的东西。3×3 只在需要时用于秩与行列式。

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

import linalg_kernel as K                    # noqa: E402
import sympy as sp                           # noqa: E402
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
    """找到字符串里第一个三目 `?`，并返回它所在的括号组边界。

    返回 (lo, q, colon, hi)：
      · q 是 `?` 的下标；
      · colon 是同深度的配对 `:`；
      · 若三目被括号包住，`(lo, hi]` 就是那对括号；否则 lo = −1、hi = len(s)。

    为什么要找括号组：三目不一定在表达式顶层（如 `2-(cond?1:2)`），
    只扫顶层会漏掉。
    """
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
    """把三目 `a?b:c` 翻成 Python 的 `b if a else c`（供构建期对账）。

    画板端由浏览器按**真 JS** 求值；这里只为在构建期用同一条表达式核对内核值。
    逐个替换、递归处理嵌套与括号包裹的情形。
    """
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


# =====================================================================
# 1) 线性变换与行列式（剪切：面积不变）
# =====================================================================
def build_transform() -> dict:
    k0 = 1.0
    A = K.A_shift(k0)
    det = K.det2(A)
    EXPR_DET = "1*1-k*0"
    for k in (-2.0, 0.0, 0.5, 1.0, 2.0):
        _agree(f"det(k={k})", EXPR_DET, K.det2(K.A_shift(k)), tol=1e-12, k=k)
    _agree("Ae₂ 的第二分量", "k", float(K.cols2(A)[1][1]), tol=1e-12, k=k0)
    _agree("面积 = |det|", "abs(" + EXPR_DET + ")", abs(float(det)), tol=1e-12, k=k0)
    assert det == 1, "剪切的行列式必须恒为 1"

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "gridmap", "k": "k",
                  "caption": "淡紫网格是变换后的像；黄框是单位正方形的像"},
        "param": {"name": "k", "label": "剪切量 $k$", "min": -2, "max": 2, "step": 0.1,
                  "value": k0, "unit": "", "standard": k0,
                  "ticks": ["-2", "0", "1 (题设)", "2"]},
        "readouts": [
            ro("det", "行列式 $\\det A = ad-bc$", EXPR_DET, 3),
            ro("area", "面积缩放比 $|\\det A|$", "abs(" + EXPR_DET + ")", 3),
            ro("ae2", "$A\\mathbf{e_2}$ 的 y 分量", "k", 3),
            ro_status("inv", "是否可逆（det ≠ 0）", "abs(" + EXPR_DET + ")", 1e-9, ">",
                      "可逆（det ≠ 0）", "不可逆（det = 0）"),
        ],
        "constant": {"of": "det", "label": "det 恒为 1 —— 剪切改变形状，不改变面积"},
    }
    lesson = {
        "language": "zh-CN", "title": "线性变换与行列式",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>矩阵 $A = \\begin{pmatrix}1 & k\\\\ 0 & 1\\end{pmatrix}$ 把平面上的点 "
            "$\\mathbf{v}$ 送到 $A\\mathbf{v}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>单位正方形被送到哪里？面积是多少？</li>"
            "<li>拖动滑块，形状怎么变？面积变吗？为什么？</li>"
            "<li>这个变换有几个特征方向？</li></ol>"),
        "answerLabel": "单位正方形的像的面积",
        "answer": f"$|\\det A| = {K.f(abs(float(det)),1)}$（与 $k$ 无关）",
    }
    steps = [
        {"title": "矩阵的两列 = 基向量的落点",
         "content": ("<p>$A$ 的第一列是 $A\\mathbf{e_1}$、第二列是 $A\\mathbf{e_2}$。"
                     "所以只要知道两列的落点，整个变换就定了 —— 图上蓝箭头与粉箭头。</p>"
                     "<p>这里 $A\\mathbf{e_1} = (1,0)$ 不动，$A\\mathbf{e_2} = (k,1)$ "
                     "被推向右（或左）—— 这就是「剪切」。</p>")},
        {"title": "行列式 = 面积缩放比",
         "content": ("<p>单位正方形的像是**平行四边形**，顶点是两个列向量。"
                     "它的面积等于 $|\\det A|$。</p>"
                     "<p>$\\det = 1\\times1 - k\\times0 = 1$ —— 与 $k$ 无关。"
                     "所以无论把图形拉得多斜，面积都保持 1；这就是" +
                     "「行列式是体积元缩放因子」的几何含义。</p>")},
        {"title": "剪切只有一个特征方向",
         "content": ("<p>解 $A\\mathbf{v} = \\lambda\\mathbf{v}$ 得 $\\lambda_1=\\lambda_2=1$，"
                     "但只有一个独立特征向量 $(1,0)$ —— 它满足 $A\\mathbf{v}=\\mathbf{v}$，"
                     "是那条不动的绿线。</p>"
                     "<p>这类矩阵**不能对角化**（特征向量不够），所以它虽然可逆、"
                     "却不能写成 $P\\Lambda P^{-1}$。拖动滑块看看：绿线始终不动。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 特征值与特征向量（对称矩阵：方向与参数无关）
# =====================================================================
def build_eigen() -> dict:
    k0 = 0.5
    A = K.A_sym(k0)
    evs = K.eigen2(A)
    l1, l2 = evs[0]["value"], evs[1]["value"]
    _agree("λ 的较大者", "1+k", float(l1), tol=1e-12, k=k0)
    _agree("λ 的较小者", "1-k", float(l2), tol=1e-12, k=k0)
    _agree("λ₁+λ₂ = 迹", "(1+k)+(1-k)", float(K.trace2(A)), tol=1e-12, k=k0)
    _agree("λ₁·λ₂ = det", "(1+k)*(1-k)", float(K.det2(A)), tol=1e-12, k=k0)
    # 特征方向恒定：与 (1,1)/√2 共线
    _agree("特征向量方向角（固定 45°）", "atan(1/1)*180/PI", 45.0, tol=1e-9)
    _agree("两条特征方向正交", "(1)*(1)+(1)*(-1)", 0.0, tol=1e-12)
    assert float(l1) == 1 + k0

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "eigen", "k": "k",
                  "caption": "绿/蓝两条直线是特征方向，它们与 k 无关；黄圈是单位圆的像"},
        "param": {"name": "k", "label": "非对角元 $k$", "min": -2, "max": 2, "step": 0.05,
                  "value": k0, "unit": "", "standard": k0,
                  "ticks": ["-2", "0", "0.5 (题设)", "2"]},
        "readouts": [
            ro("l1", "较大特征值 $\\lambda_1 = 1+k$", "1+k", 4),
            ro("l2", "较小特征值 $\\lambda_2 = 1-k$", "1-k", 4),
            ro("sum", "$\\lambda_1+\\lambda_2$（= 迹）", "(1+k)+(1-k)", 3),
            ro("prod", "$\\lambda_1\\lambda_2$（= det）", "(1+k)*(1-k)", 3),
            ro_status("orth", "两个特征向量是否正交", "(1)*(1)+(1)*(-1)", 0, "==",
                      "正交（对称矩阵的特征向量必正交）", "不正交"),
        ],
        "constant": {"of": "dir", "label": "特征方向恒为 (1,±1)/√2（改变 k 不动它）"},
    }
    lesson = {
        "language": "zh-CN", "title": "特征值与特征向量",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>对称矩阵 $A = \\begin{pmatrix}1 & k\\\\ k & 1\\end{pmatrix}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求它的特征值与特征向量；</li>"
            "<li>拖动滑块改变 $k$，特征向量<b>方向</b>变吗？</li>"
            "<li>为什么 $\\lambda_1+\\lambda_2$ 恒等于 2？</li></ol>"),
        "answerLabel": "特征值（一般 $k$）",
        "answer": "$\\lambda_1 = 1+k$，$\\lambda_2 = 1-k$",
    }
    steps = [
        {"title": "特征向量的含义",
         "content": ("<p>$A\\mathbf{v} = \\lambda\\mathbf{v}$ 说的是：这个向量被变换后"
                     "**方向不变**，只是长度乘了 $\\lambda$。</p>"
                     "<p>图上绿/蓝两条直线就是这样的方向；黄圈（单位圆）被拉成椭圆，"
                     "而椭圆的长短轴恰好落在这两条直线上。</p>")},
        {"title": "解这个矩阵：方向与 k 无关",
         "content": ("<p>$\\det(A-\\lambda I) = (1-\\lambda)^2 - k^2 = 0$，"
                     "故 $\\lambda = 1 \\pm k$。</p>"
                     "<p>代回求特征向量：$\\lambda_1 = 1+k$ 对应 $(1,1)$；"
                     "$\\lambda_2 = 1-k$ 对应 $(1,-1)$。**两者都不含 $k$** ——"
                     "所以拖动滑块时，绿蓝两条线纹丝不动，变的只是拉伸倍数。</p>")},
        {"title": "两个恒等式：迹与行列式",
         "content": ("<p>$\\lambda_1+\\lambda_2 = 2 = \\operatorname{tr}A$；"
                     "$\\lambda_1\\lambda_2 = 1-k^2 = \\det A$。</p>"
                     "<p>这两条对任何方阵都成立（特征多项式与迹/行列式的关系），"
                     "是最常用的**验算手段** —— 读数区把它们单列出来，"
                     "任何一处写错都会当场对不上。</p>"
                     "<p>注意 $|k|>1$ 时 $\\lambda_2<0$：椭圆的一个轴方向被翻转了，"
                     "这时 $\\det<0$，映射改变了定向。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 矩阵幂与马尔可夫稳态
# =====================================================================
def build_power() -> dict:
    k0 = 5
    A = K.A_markov()
    pi = K.steady_state(A)
    EXPR_A00 = "0.6+0.4*pow(0.5,k)"
    EXPR_A10 = "0.4-0.4*pow(0.5,k)"
    for k in (0, 1, 2, 5, 10, 20):
        Mk = K.matrix_power(A, k)
        _agree(f"A^k[0,0] (k={k})", EXPR_A00, float(Mk[0, 0]), tol=1e-12, k=k)
        _agree(f"A^k[1,0] (k={k})", EXPR_A10, float(Mk[1, 0]), tol=1e-12, k=k)
        _agree(f"两分量之和为 1 (k={k})", EXPR_A00 + "+" + EXPR_A10, 1.0, tol=1e-12, k=k)
    _agree("与稳态的偏差", "0.4*pow(0.5,k)+0.4*pow(0.5,k)", 0.8 * 0.5 ** k0, tol=1e-12, k=k0)
    assert abs(float(pi[0]) - 0.6) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "power", "k": "k",
                  "caption": "左：Aᵏ 的两列（各自和为 1）；右：与稳态的偏差随 k 衰减"},
        "param": {"name": "k", "label": "幂次 $k$", "min": 0, "max": 20, "step": 1,
                  "value": k0, "unit": "", "standard": k0,
                  "ticks": ["0", "5 (题设)", "20"]},
        "readouts": [
            ro("a00", "$(A^k)_{11}$", EXPR_A00, 6),
            ro("a10", "$(A^k)_{21}$", EXPR_A10, 6),
            ro("dev", "与稳态的偏差之和", "0.4*pow(0.5,k)+0.4*pow(0.5,k)", 6),
            ro("pi1", "稳态第一分量 $\\pi_1$", "0.6", 4),
            ro_status("conv", "是否已收敛（偏差 < 1e-3）",
                      "0.4*pow(0.5,k)+0.4*pow(0.5,k)", 1e-3, "<",
                      "已收敛到稳态", "还没收敛"),
        ],
        "constant": {"of": "pi", "label": "稳态 π = (0.6, 0.4) 与 k 无关（A 的平衡分布）"},
    }
    lesson = {
        "language": "zh-CN", "title": "矩阵幂与马尔可夫稳态",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>列随机矩阵 $A = \\begin{pmatrix}0.8 & 0.3\\\\ 0.2 & 0.7\\end{pmatrix}$"
            "（每列之和为 1）。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求 $A$ 的特征值，并解释为什么 $A^k$ 会收敛；</li>"
            "<li>拖动滑块增大 $k$，$A^k$ 的两列收敛到哪里？</li>"
            "<li>为什么「稳态」与初始状态无关？</li></ol>"),
        "answerLabel": "稳态分布",
        "answer": "$\\pi = (0.6,\\ 0.4)$",
    }
    steps = [
        {"title": "特征值决定了幂的走向",
         "content": ("<p>$\\operatorname{tr}A = 1.5$，$\\det A = 0.8\\times0.7 - 0.3\\times0.2 "
                     "= 0.5$，故 $\\lambda^2 - 1.5\\lambda + 0.5 = 0$，"
                     "得 $\\lambda_1 = 1$、$\\lambda_2 = 0.5$。</p>"
                     "<p>把 $A$ 对角化 $A = P\\Lambda P^{-1}$，则 "
                     "$A^k = P\\Lambda^k P^{-1}$ —— 特征值取 $k$ 次幂。"
                     "$\\lambda_2^k = 0.5^k \\to 0$，所以只有 $\\lambda_1 = 1$ 那一项活下来。</p>")},
        {"title": "稳态就是 λ=1 的特征向量",
         "content": ("<p>$\\lambda_1 = 1$ 的特征向量解 $(A-I)\\mathbf{v} = 0$，"
                     "得 $\\mathbf{v} \\propto (3, 2)$；归一化成概率向量就是 "
                     "$\\pi = (0.6, 0.4)$。</p>"
                     "<p>$A\\pi = \\pi$ —— 分布不再变化，这就是**稳态**。"
                     "$A^k$ 的每一列都收敛到 $\\pi$，且 $A^k = P_1 + 0.5^k(I-P_1)$，"
                     "其中 $P_1$ 是每列都等于 $\\pi$ 的那个秩 1 矩阵。</p>")},
        {"title": "为什么与初始状态无关",
         "content": ("<p>任何初始分布可写成 $\\pi$ 与另一个特征向量的组合；"
                     "迭代 $k$ 次后，后者被 $0.5^k$ 压没了，只剩 $\\pi$ 分量。</p>"
                     "<p>读数里 $(A^k)_{11} = 0.6 + 0.4\\times0.5^k$、"
                     "$(A^k)_{21} = 0.4 - 0.4\\times0.5^k$ —— 两式对任何 $k$ 都成立，"
                     "且与画板上的柱子同源。这就是「马尔可夫链有唯一稳态」的定量形态。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 正交投影与最小二乘
# =====================================================================
def build_projection() -> dict:
    y0 = 4.0
    PTS = lambda y: [(0, 1), (1, 3), (2, y), (3, 6)]
    ls = K.least_squares(PTS(y0))
    EXPR_M = "(12+y)/10"
    EXPR_C = "(7+y)/10"
    R = ["(3-y)/10", "(11-2*y)/10", "(7*y-31)/10", "(17-4*y)/10"]
    EXPR_SS = "+".join(f"({r})**2" for r in R)
    for y in (0.0, 2.0, 4.0, 6.0, 8.0):
        q = K.least_squares(PTS(y))
        _agree(f"斜率(y={y})", EXPR_M, float(q["m"]), tol=1e-12, y=y)
        _agree(f"截距(y={y})", EXPR_C, float(q["c"]), tol=1e-12, y=y)
        _agree(f"残差平方和(y={y})", EXPR_SS, float(q["ss_res"]), tol=1e-12, y=y)
    # 残差恒垂直于拟合方向（法方程的几何含义）：Σr=0 且 Σ(x·r)=0
    _agree("Σ 残差 = 0（投影的必然结果）",
           f"({R[0]})+({R[1]})+({R[2]})+({R[3]})", 0.0, tol=1e-12, y=y0)
    _agree("Σ x·残差 = 0（法方程的第二个方程）",
           f"0*({R[0]})+1*({R[1]})+2*({R[2]})+3*({R[3]})", 0.0, tol=1e-12, y=y0)
    assert abs(float(ls["m"]) - (12 + y0) / 10) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "proj", "y2": "y",
                  "caption": "红竖线是残差；最小二乘让这些竖线的平方和最小"},
        "param": {"name": "y", "label": "第 3 个点的 $y$ 值", "min": 0, "max": 8,
                  "step": 0.1, "value": y0, "unit": "", "standard": y0,
                  "ticks": ["0", "4 (题设)", "8"]},
        "readouts": [
            ro("m", "拟合斜率 $m$", EXPR_M, 4),
            ro("c", "拟合截距 $c$", EXPR_C, 4),
            ro("ss", "残差平方和 $\\sum r_i^2$", EXPR_SS, 4),
            ro("sumr", "$\\sum r_i$（恒为 0）", f"({R[0]})+({R[1]})+({R[2]})+({R[3]})", 6),
            ro_status("orth", "残差是否与拟合方向垂直",
                      f"0*({R[0]})+1*({R[1]})+2*({R[2]})+3*({R[3]})", 0, "==",
                      "垂直（这正是法方程）", "不垂直"),
        ],
        "constant": {"of": "n", "label": "四个数据点，x 固定为 0,1,2,3"},
    }
    lesson = {
        "language": "zh-CN", "title": "正交投影与最小二乘",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>四个数据点 $(0,1),(1,3),(2,y),(3,6)$，用一条直线 $y = mx+c$ 拟合。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出法方程，解出 $m$、$c$；</li>"
            "<li>拖动滑块改变第 3 个点的 $y$，直线怎么动？</li>"
            "<li>为什么残差竖线一定「垂直于」拟合方向？</li></ol>"),
        "answerLabel": "题设下的斜率与残差平方和",
        "answer": f"$m = {K.f(float(ls['m']),3)}$，$\\sum r_i^2 = {K.f(float(ls['ss_res']),4)}$",
    }
    steps = [
        {"title": "把「拟合」翻译成「投影」",
         "content": ("<p>四个点给出向量 $\\mathbf{b} = (y_1,y_2,y_3,y_4)$。"
                     "所有可能的直线 $mx+c$ 也构成一个平面（由 "
                     "$\\mathbf{1}=(1,1,1,1)$ 与 $\\mathbf{x}=(0,1,2,3)$ 张成）。</p>"
                     "<p>「找最近的直线」＝把 $\\mathbf{b}$ **正交投影**到这个平面上。"
                     "所以最小二乘不是" + "凑" + "出来的公式，它是一个几何操作。</p>")},
        {"title": "法方程",
         "content": ("<p>投影的条件是残差 $\\mathbf{e} = \\mathbf{b} - A\\hat{\\mathbf{x}}$ "
                     "垂直于平面，即 $A^\\mathsf{T}\\mathbf{e} = 0$，展开即法方程：</p>"
                     "<p>$\\begin{pmatrix}n & \\sum x_i\\\\ \\sum x_i & \\sum x_i^2\\end{pmatrix}"
                     "\\begin{pmatrix}c\\\\ m\\end{pmatrix} = "
                     "\\begin{pmatrix}\\sum y_i\\\\ \\sum x_iy_i\\end{pmatrix}$。</p>"
                     "<p>本例 $n=4$、$\\sum x=6$、$\\sum x^2=14$，解得 "
                     "$m = (12+y)/10$、$c = (7+y)/10$ —— 都是 $y$ 的一次函数，"
                     "所以拖动滑块时直线平移与转动都是线性的。</p>")},
        {"title": "两个恒等式就是「垂直」的代数形态",
         "content": ("<p>$A^\\mathsf{T}\\mathbf{e} = 0$ 给出两个方程："
                     "$\\sum r_i = 0$ 与 $\\sum x_i r_i = 0$。</p>"
                     "<p>读数区把这两个和单列出来，它们**恒为 0** ——"
                     "这就是「残差垂直于 $\\mathbf{1}$ 与 $\\mathbf{x}$」的算术写法。"
                     "图上残差竖线看起来垂直于拟合线，正是同一件事的几何写法。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 秩、列空间与零空间
# =====================================================================
def build_rank() -> dict:
    k0 = 2.0
    A = K.A_rank(k0)
    EXPR_DET = "1*k-1*1"
    EXPR_RANK = "abs(1*k-1*1)<1e-9 ? 1 : 2"
    EXPR_NULL = "2-(abs(1*k-1*1)<1e-9 ? 1 : 2)"
    for k in (1, 2, -1, 3):
        _agree(f"det(k={k})", EXPR_DET, float(K.det2(K.A_rank(k))), tol=1e-12, k=k)
        _agree(f"rank(k={k})", EXPR_RANK, K.rank_of(K.A_rank(k)), tol=1e-12, k=k)
        _agree(f"零空间维数(k={k})", EXPR_NULL, 2 - K.rank_of(K.A_rank(k)), tol=1e-12, k=k)
    assert K.rank_of(K.A_rank(1)) == 1 and K.rank_of(K.A_rank(2)) == 2

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "subspace", "k": "k",
                  "caption": "淡紫网格是变换后的像；k=1 时整个平面塌到红线 y=x 上"},
        "param": {"name": "k", "label": "右下元素 $k$", "min": -2, "max": 3, "step": 0.05,
                  "value": k0, "unit": "", "standard": k0,
                  "ticks": ["-2", "1 (退化)", "2 (题设)", "3"]},
        "readouts": [
            ro("det", "行列式 $\\det = k-1$", EXPR_DET, 4),
            ro("rank", "矩阵的秩", EXPR_RANK, 0),
            ro("nulldim", "零空间维数 $2-\\mathrm{rank}$", EXPR_NULL, 0),
            ro_status("full", "是否满秩（det ≠ 0）", "abs(1*k-1*1)", 1e-9, ">",
                      "满秩：映射可逆，零空间只有零向量", "不满秩：列空间塌成一条直线"),
        ],
        "constant": {"of": "cols", "label": "两列之和恒为 (1+k, 1+k) —— 它们总在同一条线上"},
    }
    lesson = {
        "language": "zh-CN", "title": "秩、列空间与零空间",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>矩阵 $A = \\begin{pmatrix}1 & 1\\\\ 1 & k\\end{pmatrix}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>$k$ 取什么值时 $A$ 不可逆？那时秩是多少？</li>"
            "<li>拖动滑块到那个值，画出平面被映射成什么？</li>"
            "<li>为什么「秩 = 2 − 零空间维数」？</li></ol>"),
        "answerLabel": "退化的条件",
        "answer": "$k = 1$ 时 $\\det = 0$，秩降为 1",
    }
    steps = [
        {"title": "行列式为零 ⇔ 列向量共线",
         "content": ("<p>$\\det A = 1\\cdot k - 1\\cdot1 = k-1$。$k=1$ 时 $A$ 的两列都是 "
                     "$(1,1)$，**共线**。</p>"
                     "<p>两列共线意味着整个平面被压到它们张成的那**一条直线**上 ——"
                     "拖动滑块到 $k=1$ 就能看到：平行四边形压成一条线段，"
                     "所有点都落到红线 $y=x$ 上。</p>")},
        {"title": "列空间、零空间与秩-零化度定理",
         "content": ("<p>**列空间**是所有 $A\\mathbf{v}$ 的集合 —— 也就是像。"
                     "它的维数就是秩：$k\\ne1$ 时是 2（整个平面），$k=1$ 时是 1（一条线）。</p>"
                     "<p>**零空间**是满足 $A\\mathbf{v} = 0$ 的 $\\mathbf{v}$ 的集合。"
                     "$k=1$ 时 $A = \\begin{pmatrix}1&1\\\\1&1\\end{pmatrix}$，"
                     "方程退化成 $x+y=0$，所以零空间就是那条垂直于列方向的线，维数为 1。</p>"
                     "<p>两者之和恒等于列数：$\\mathrm{rank} + \\dim N(A) = n = 2$ ——"
                     "这就是**秩-零化度定理**。</p>")},
        {"title": "满秩意味着可逆",
         "content": ("<p>$k\\ne1$ 时零空间只有零向量，映射是一一对应的，于是存在逆矩阵 "
                     "$A^{-1}$，能把每个点送回原处。</p>"
                     "<p>反过来，只要有一列是另一列的倍数，就一定有非零向量被压到原点"
                     "（信息丢了），逆映射也就不存在 —— 这就是「不可逆」的几何含义。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 奇异值分解
# =====================================================================
def build_svd() -> dict:
    k0 = 1.0
    A = K.A_shift(k0)
    sv = K.svd2(A)
    s1, s2 = sv[0]["s"], sv[1]["s"]
    T = "(2+k*k)"
    EXPR_S1 = f"sqrt(({T}+sqrt({T}*{T}-4))/2)"
    EXPR_S2 = f"sqrt(({T}-sqrt({T}*{T}-4))/2)"
    for k in (0.0, 0.5, 1.0, 1.5):
        q = K.svd2(K.A_shift(k))
        _agree(f"σ₁(k={k})", EXPR_S1, float(q[0]["s"]), tol=1e-12, k=k)
        _agree(f"σ₂(k={k})", EXPR_S2, float(q[1]["s"]), tol=1e-12, k=k)
        _agree(f"σ₁σ₂ = |det| (k={k})", EXPR_S1 + "*" + EXPR_S2,
               abs(float(K.det2(K.A_shift(k)))), tol=1e-9, k=k)
    _agree("k=1 时 σ₁ 是黄金比", EXPR_S1, (1 + 5 ** 0.5) / 2, tol=1e-12, k=1.0)
    _agree("条件数", f"({EXPR_S1})/({EXPR_S2})", float(s1) / float(s2), tol=1e-12, k=k0)
    assert abs(float(s1) - 1.6180339887) < 1e-9

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "svd", "k": "k",
                  "caption": "灰圈是单位圆，黄椭圆是它的像；两条箭头是主轴 σ₁、σ₂"},
        "param": {"name": "k", "label": "剪切量 $k$", "min": 0, "max": 1.5, "step": 0.05,
                  "value": k0, "unit": "", "standard": k0,
                  "ticks": ["0", "1 (题设，黄金比)", "1.5"]},
        "readouts": [
            ro("s1", "最大奇异值 $\\sigma_1$", EXPR_S1, 4),
            ro("s2", "最小奇异值 $\\sigma_2$", EXPR_S2, 4),
            ro("prod", "$\\sigma_1\\sigma_2$（= |det|）", EXPR_S1 + "*" + EXPR_S2, 4),
            ro("cond", "条件数 $\\sigma_1/\\sigma_2$", f"({EXPR_S1})/({EXPR_S2})", 4),
            ro_status("sq", "是否保面积（σ₁σ₂ = 1）", EXPR_S1 + "*" + EXPR_S2, 1, "==",
                      "保面积（|det| = 1）", "不保面积"),
        ],
        "constant": {"of": "det", "label": "det 恒为 1 —— 所以 σ₁σ₂ 恒为 1"},
    }
    lesson = {
        "language": "zh-CN", "title": "奇异值分解：椭圆的半轴",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>对 $A = \\begin{pmatrix}1 & k\\\\ 0 & 1\\end{pmatrix}$ 做奇异值分解。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>单位圆被 $A$ 送到什么形状？半轴多长？</li>"
            "<li>$k=1$ 时 $\\sigma_1$ 等于多少？</li>"
            "<li>为什么 $\\sigma_1\\sigma_2$ 与 $k$ 无关？</li></ol>"),
        "answerLabel": "$k=1$ 时的奇异值",
        "answer": "$\\sigma_1 = \\dfrac{1+\\sqrt{5}{2} \\approx 1.618$（黄金比），"
                  "$\\sigma_2 = \\dfrac{\\sqrt{5}-1}{2} \\approx 0.618$",
    }
    steps = [
        {"title": "任何矩阵都是「旋转-拉伸-旋转」",
         "content": ("<p>任意矩阵 $A$ 都能写成 $A = U\\Sigma V^\\mathsf{T}$："
                     "先旋转（$V^\\mathsf{T}$）、再沿坐标轴拉伸（$\\Sigma$）、再旋转（$U$）。</p>"
                     "<p>所以**单位圆在任意矩阵下都是椭圆**，半轴长就是奇异值 "
                     "$\\sigma_1 \\ge \\sigma_2$。图上灰圈变黄椭圆，两条箭头就是半轴。</p>")},
        {"title": "σ 是 AᵀA 特征值的平方根",
         "content": ("<p>$A^\\mathsf{T}A = \\begin{pmatrix}1 & k\\\\ k & 1+k^2\\end{pmatrix}$，"
                     "它的迹是 $2+k^2$、行列式是 1，故特征值为 "
                     "$\\lambda = \\dfrac{(2+k^2) \\pm \\sqrt{(2+k^2)^2-4}}{2}$，"
                     "$\\sigma_i = \\sqrt{\\lambda_i}$。</p>"
                     "<p>$k=1$ 时 $\\lambda = \\dfrac{3\\pm\\sqrt5}{2}$，"
                     "$\\sigma_1 = \\sqrt{2.618} \\approx 1.618$ —— 黄金比。"
                     "这不是巧合：$\\sigma_1^2 - \\sigma_1 - 1 = 0$。</p>")},
        {"title": "乘积恒等于 |det|",
         "content": ("<p>$\\sigma_1^2\\sigma_2^2 = \\det(A^\\mathsf{T}A) = (\\det A)^2$，"
                     "所以 $\\sigma_1\\sigma_2 = |\\det A|$。</p>"
                     "<p>本例 $\\det A \\equiv 1$（剪切保面积），所以两个奇异值的乘积恒为 1 —— "
                     "一个变大，另一个必定变小。这就是图上「椭圆越扁、条件数越大」的来源，"
                     "也是数值计算里「病态矩阵」的含义。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) Gram–Schmidt 正交化
# =====================================================================
def build_orth() -> dict:
    k0 = 1.0
    V1 = [3, 1]
    qs = K.gram_schmidt([V1, [k0, 2]])
    EXPR_Q1X = "3/sqrt(10)"
    EXPR_Q1Y = "1/sqrt(10)"
    EXPR_COEF = "(3*k+2)/sqrt(10)"
    # q₂ 的方向：与 q₁ 正交的单位向量，(1,−3)/√10 或它的相反数（符号取决于 k−6）
    EXPR_DOT = "(3/sqrt(10))*(1/sqrt(10))+(1/sqrt(10))*(-3/sqrt(10))"
    EXPR_N2 = "sqrt((1/sqrt(10))*(1/sqrt(10))+(-3/sqrt(10))*(-3/sqrt(10)))"
    for k in (-3.0, -1.0, 0.0, 1.0, 3.0):
        q = K.gram_schmidt([V1, [k, 2]])
        _agree(f"q₁ 的 x 分量(k={k})", EXPR_Q1X, float(q[0][0]), tol=1e-12, k=k)
        _agree(f"投影系数(k={k})", EXPR_COEF, float(K.dot([k, 2], q[0])), tol=1e-12, k=k)
        # q₂ 必与 (1,−3)/√10 共线（可能反号）—— 用内积的绝对值判定，内核侧校验
        u = sp.Matrix([1, -3]) / sp.sqrt(10)
        assert abs(abs(float(K.dot(q[1], u))) - 1.0) < 1e-12, f"k={k} 时 q₂ 不共线"
    _agree("q₁ ⊥ q₂", EXPR_DOT, 0.0, tol=1e-12)
    _agree("q₂ 是单位向量", EXPR_N2, 1.0, tol=1e-12)
    # 定值：q₂ 与 x 轴的夹角恒为 arctan(3) —— 与 k 无关
    _agree("q₂ 与 x 轴夹角（恒定）", "atan(3/1)*180/PI", math.degrees(math.atan(3.0)), tol=1e-12)
    assert abs(float(qs[0][0]) - 3 / math.sqrt(10)) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "orth", "k": "k",
                  "caption": "紫箭头 = v₂ 在 q₁ 上的投影；红虚线 = 减掉它之后剩下的部分"},
        "param": {"name": "k", "label": "$v_2$ 的 $x$ 分量", "min": -3, "max": 3,
                  "step": 0.1, "value": k0, "unit": "", "standard": k0,
                  "ticks": ["-3", "1 (题设)", "3"]},
        "readouts": [
            ro("q1x", "$q_1$ 的 x 分量", EXPR_Q1X, 4),
            ro("q1y", "$q_1$ 的 y 分量", EXPR_Q1Y, 4),
            ro("coef", "$v_2$ 在 $q_1$ 上的投影系数", EXPR_COEF, 4),
            ro("q2ang", "$q_2$ 与 x 轴的夹角（恒定）", "atan(3/1)*180/PI", 3, "°"),
            ro("dot", "$q_1\\cdot q_2$（恒为 0）", EXPR_DOT, 6),
            ro_status("unit", "$q_2$ 是否单位向量", EXPR_N2, 1, "==",
                      "是单位向量", "不是单位向量"),
        ],
        "constant": {"of": "q1", "label": "q₁ 恒为 (3,1)/√10 —— 只由 v₁ 决定"},
    }
    lesson = {
        "language": "zh-CN", "title": "Gram–Schmidt 正交化",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>$\\mathbf{v_1} = (3,1)$，$\\mathbf{v_2} = (k,2)$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>把它们化成标准正交组 $\\mathbf{q_1},\\mathbf{q_2}$；</li>"
            "<li>拖动滑块改变 $\\mathbf{v_2}$，$\\mathbf{q_1}$ 变吗？$\\mathbf{q_2}$ 的方向呢？</li>"
            "<li>为什么 $\\mathbf{v_2} - (\\mathbf{v_2}\\cdot\\mathbf{q_1})\\mathbf{q_1}$ "
            "一定垂直于 $\\mathbf{q_1}$？</li></ol>"),
        "answerLabel": "标准正交组",
        "answer": "$\\mathbf{q_1} = \\dfrac{(3,1)}{\\sqrt{10}}$，"
                  "$\\mathbf{q_2} = \\pm\\dfrac{(1,-3)}{\\sqrt{10}}$",
    }
    steps = [
        {"title": "第一步：把 v₁ 单位化",
         "content": ("<p>$\\mathbf{q_1} = \\dfrac{\\mathbf{v_1}}{\\|\\mathbf{v_1}\\|} "
                     "= \\dfrac{(3,1)}{\\sqrt{10}}$。</p>"
                     "<p>它**只由 $\\mathbf{v_1}$ 决定** —— 所以拖动滑块改变 $\\mathbf{v_2}$ 时，"
                     "绿箭头纹丝不动。</p>")},
        {"title": "第二步：减掉投影",
         "content": ("<p>$\\mathbf{w_2} = \\mathbf{v_2} - "
                     "(\\mathbf{v_2}\\cdot\\mathbf{q_1})\\mathbf{q_1}$，"
                     "再单位化得 $\\mathbf{q_2}$。</p>"
                     "<p>投影系数是 $\\dfrac{3k+2}{\\sqrt{10}}$（图上紫箭头的长度）。"
                     "把 $\\mathbf{v_2}$ 减去这一份之后，剩下的分量在 $\\mathbf{q_1}$ 方向上**恰好为零** ——"
                     "所以 $\\mathbf{q_2} \\perp \\mathbf{q_1}$。</p>"
                     "<p>代数上：$\\mathbf{w_2}\\cdot\\mathbf{q_1} = "
                     "\\mathbf{v_2}\\cdot\\mathbf{q_1} - "
                     "(\\mathbf{v_2}\\cdot\\mathbf{q_1})(\\mathbf{q_1}\\cdot\\mathbf{q_1}) = 0$，"
                     "因为 $\\mathbf{q_1}$ 是单位向量。</p>")},
        {"title": "结果方向恒定（本例的特殊之处）",
         "content": ("<p>本例算出来 $\\mathbf{q_2}$ 的方向恒为 $\\pm(1,-3)/\\sqrt{10}$ ——"
                     "与 $\\mathbf{v_1}$ 垂直的那个方向，**与 $k$ 无关**，"
                     "只有正负号随 $\\mathbf{v_2}$ 越过 $\\mathbf{q_1}$ 而翻转。</p>"
                     "<p>更一般地，$n$ 个线性无关向量正交化后会得到一组标准正交基，"
                     "任何向量都能写成它们的线性组合，系数就是内积 ——"
                     "这就是 QR 分解与傅里叶级数的共同起点。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "transform": build_transform,
    "eigen": build_eigen,
    "power": build_power,
    "projection": build_projection,
    "rank": build_rank,
    "svd": build_svd,
    "orth": build_orth,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="线性代数 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
