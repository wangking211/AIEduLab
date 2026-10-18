#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
linalg_kernel.py —— 线性代数精确内核（大学一年级，按 MIT 18.06 的知识点组织）

**为什么只用 2×2 做主场景**：线性代数的几何直觉天然是二维的（网格如何变形、
特征方向为什么不变、投影落在哪）。而 2×2 的行列式、特征值、奇异值、逆、秩
**全都有闭式解**，于是「内核用 sympy 精确算」与「画板用 JS 现算」可以逐位对账 ——
这正是全项目「同源一致」纪律要的东西。3×3 只在需要时用于秩与行列式。

覆盖（对应 18.06 的讲次）：
  · 线性变换与行列式（网格变形、面积缩放、定向）
  · 特征值与特征向量（对称矩阵的特征方向恒定）
  · 对角化与矩阵幂 A^k（马尔可夫链的稳态）
  · 正交投影与最小二乘（法方程）
  · 秩、列空间与零空间（退化映射）
  · 奇异值分解（单位圆 → 椭圆的主轴）
  · Gram–Schmidt 正交化

自检：python linalg_kernel.py
"""

import math

import sympy as sp

__all__ = [
    "tex", "f", "num_str", "vec_tex",
    "Mat2", "A_shift", "A_sym", "A_markov", "A_rank",
    "det2", "trace2", "apply2", "eigen2", "cols2",
    "matrix_power", "steady_state",
    "dot", "norm", "proj_scalar", "proj_vec", "reject_vec",
    "least_squares", "ss_residual",
    "rank_of", "null_basis", "col_basis",
    "svd2", "ellipse_axes",
    "gram_schmidt",
]


# ---------------------------------------------------------------- 排版助手

def tex(e):
    e = sp.sympify(e)
    if e.is_Integer:
        return str(int(e))
    if e.is_Rational:
        return r"\frac{%d}{%d}" % (e.p, e.q)
    return sp.latex(e)


def f(x, digits=4):
    if x is None:
        return "—"
    s = f"{float(x):.{digits}f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-") else "0"


def num_str(x, digits=4):
    v = float(x)
    if v == 0:
        return "0"
    if abs(v) >= 1e5 or abs(v) < 1e-4:
        return f"{v:.3e}".replace("e-0", "e-").replace("e+0", "e")
    return f(v, digits)


def vec_tex(v):
    return r"\begin{pmatrix}" + r" \\ ".join(tex(x) for x in v) + r"\end{pmatrix}"


# ---------------------------------------------------------------- 矩阵构造
#
# 本内核的矩阵家族都用**一个参数 k** 支配，以满足模板的单滑块契约。

def Mat2(a, b, c, d):
    """2×2 矩阵（行优先）。"""
    return sp.Matrix([[a, b], [c, d]])


def A_shift(k):
    """剪切矩阵 [[1, k], [0, 1]] —— 行列式恒为 1（面积不变）。"""
    return Mat2(1, k, 0, 1)


def A_sym(k):
    """对称矩阵 [[1, k], [k, 1]] —— 特征向量方向与 k 无关。"""
    return Mat2(1, k, k, 1)


def A_markov():
    """列随机矩阵（马尔可夫链），两列之和均为 1。"""
    return Mat2(sp.Rational(8, 10), sp.Rational(3, 10),
                sp.Rational(2, 10), sp.Rational(7, 10))


def A_rank(k):
    """[[1, 1], [1, k]] —— k=1 时秩退化为 1（列空间塌成一条直线）。"""
    return Mat2(1, 1, 1, k)


# ---------------------------------------------------------------- 行列式与基本量

def det2(A):
    """行列式的几何意义：单位正方形的像的面积（带符号 = 定向）。"""
    return sp.Matrix(A).det()


def trace2(A):
    return sp.Matrix(A).trace()


def cols2(A):
    """两个列向量（线性变换把 e₁、e₂ 送去的地方）。"""
    A = sp.Matrix(A)
    return [A[:, 0], A[:, 1]]


def apply2(A, v):
    """Av。"""
    return sp.Matrix(A) * sp.Matrix(v)


def eigen2(A):
    """2×2 的特征值（降序）与对应特征向量（可选为数值）。

    用 sympy 精确算；特征值可能含根号，这时返回 sympy 表达式，
    由调用方决定是保留精确形式还是取浮点。
    """
    A = sp.Matrix(A)
    if A.shape != (2, 2):
        raise ValueError("只支持 2×2")
    ev = A.eigenvects()
    out = []
    for val, mult, vecs in ev:
        # 重根要展开成多条：单位阵这类矩阵一个特征值对应多个独立特征向量，
        # 不展开的话「两个方向」的读数就会缺一个。
        for i in range(mult):
            out.append({"value": val, "mult": mult,
                        "vector": sp.Matrix(vecs[i]) if i < len(vecs) else None,
                        "defective": len(vecs) < mult})
    out.sort(key=lambda d: -float(sp.re(d["value"])))
    return out


# ---------------------------------------------------------------- 矩阵幂与稳态

def matrix_power(A, k):
    """A^k（k 为非负整数）——精确。"""
    k = int(k)
    if k < 0:
        raise ValueError("幂次须非负")
    return sp.Matrix(A) ** k


def steady_state(A):
    """列随机矩阵的稳态分布（A^k 收敛到的那个秩 1 矩阵的每一列）。

    对 2×2 列随机矩阵，稳态满足 Aπ = π 且 π₁+π₂ = 1，可直接解出。
    """
    A = sp.Matrix(A)
    a, b = A[0, 0], A[0, 1]
    # π₁ = π₁·a + π₂·b，且 π₂ = 1 − π₁  ⇒  π₁(1−a) = b(1−π₁)
    pi1 = sp.simplify(b / (1 - a + b))
    return sp.Matrix([pi1, 1 - pi1])


# ---------------------------------------------------------------- 投影与最小二乘

def dot(u, v):
    u, v = sp.Matrix(u), sp.Matrix(v)
    return (u.T * v)[0]


def norm(u):
    return sp.sqrt(dot(u, u))


def proj_scalar(a, b):
    """b 在 a 上的标量投影系数 c，使 ca 最近于 b：c = aᵀb / aᵀa。"""
    return sp.simplify(dot(a, b) / dot(a, a))


def proj_vec(a, b):
    """b 在 a 上的投影向量 p = ca。"""
    return sp.simplify(proj_scalar(a, b) * sp.Matrix(a))


def reject_vec(a, b):
    """残差 e = b − p —— 它垂直于 a（这就是「最小二乘」的来源）。"""
    return sp.simplify(sp.Matrix(b) - proj_vec(a, b))


def least_squares(points):
    """对 points=[(x,y)...] 做最小二乘拟合直线 y = m·x + c。

    法方程（normal equations）：
        [[n,   Σx ], [Σx, Σx²]] · [c, m]ᵀ = [Σy, Σxy]ᵀ
    用 sympy 精确解，返回 m、c 与残差平方和。
    """
    pts = [(sp.nsimplify(x), sp.nsimplify(y)) for x, y in points]
    n = len(pts)
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    sxx = sum(p[0] ** 2 for p in pts)
    sxy = sum(p[0] * p[1] for p in pts)
    M = sp.Matrix([[n, sx], [sx, sxx]])
    rhs = sp.Matrix([sy, sxy])
    sol = M.solve(rhs)
    c, m = sol[0], sol[1]
    resid = [p[1] - (m * p[0] + c) for p in pts]
    ss = sum(r ** 2 for r in resid)
    return {"m": sp.simplify(m), "c": sp.simplify(c),
            "residuals": [sp.simplify(r) for r in resid],
            "ss_res": sp.simplify(ss)}


def ss_residual(points, m, c):
    """给定 m、c 时的残差平方和（用于展示「换一条线就更差」）。"""
    return sum((sp.nsimplify(y) - (sp.nsimplify(x) * m + c)) ** 2 for x, y in points)


# ---------------------------------------------------------------- 秩、列空间、零空间

def _rref(A):
    A = sp.Matrix(A)
    return A.rref()[0]


def rank_of(A):
    return sp.Matrix(A).rank()


def null_basis(A):
    """零空间的一组基（Ax=0 的解空间的基向量）。"""
    return sp.Matrix(A).nullspace()


def col_basis(A):
    """列空间的一组基（取主元列）。"""
    A = sp.Matrix(A)
    pivots = A.rref()[1]
    return [A[:, j] for j in pivots]


# ---------------------------------------------------------------- 奇异值分解

def svd2(A):
    """2×2 的奇异值（降序）。

    σᵢ 是 AᵀA 的特征值的平方根 —— 对 2×2 有闭式：
        σ² = (T ± √(T² − 4D)) / 2，其中 T = ‖A‖_F²、D = (det A)²
    返回 σ₁ ≥ σ₂ ≥ 0 的浮点值与 V 的两个主方向（AᵀA 的特征向量）。
    """
    A = sp.Matrix(A)
    if A.shape != (2, 2):
        raise ValueError("只支持 2×2")
    AtA = A.T * A
    ev = AtA.eigenvects()
    pairs = []
    for val, mult, vecs in ev:
        # 同样要展开重根（如 A = I 时两个奇异值都是 1，方向可取两个坐标轴）
        for i in range(mult):
            if i >= len(vecs):
                continue
            v = sp.Matrix(vecs[i])
            nv = v / norm(v)
            pairs.append({"s": sp.sqrt(sp.simplify(val)), "v": nv})
    pairs.sort(key=lambda d: -float(sp.re(d["s"])))
    return pairs


def ellipse_axes(A):
    """单位圆在 A 之下的像：椭圆的半轴长（= 奇异值）与方向（= 主方向）。"""
    return svd2(A)


# ---------------------------------------------------------------- Gram–Schmidt

def gram_schmidt(vectors):
    """把一组向量化成标准正交组。返回 (正交向量组, 单位向量组)。

    q₁ = v₁/‖v₁‖；
    q₂ = (v₂ − ⟨v₂,q₁⟩q₁) / ‖·‖，依此类推 —— 每一步减掉已有方向上的投影。
    """
    qs = []
    for v in vectors:
        w = sp.Matrix(v)
        for q in qs:
            w = sp.simplify(w - dot(w, q) * q)
        n = norm(w)
        if sp.simplify(n) == 0:
            raise ValueError("向量组线性相关，无法正交化")
        qs.append(sp.simplify(w / n))
    return qs


# ================================================================ 自检

def _same(a, b):
    """判断两个 sympy 对象是否相等 —— 标量、矩阵、布尔都能处理。

    不能直接写 `sympify(a) - sympify(b) == 0`：矩阵相减得到的是**矩阵**，
    与 0 比较会得到逐元素布尔矩阵；布尔相减则直接报 BooleanAtom 错误。
    """
    a, b = sp.sympify(a), sp.sympify(b)
    if isinstance(a, sp.MatrixBase) or isinstance(b, sp.MatrixBase):
        d = sp.Matrix(a) - sp.Matrix(b)
        return all(sp.simplify(x) == 0 for x in d)
    return sp.simplify(a - b) == 0


def _selftest():
    bad = []

    def chk(name, got, want, tol=None):
        shown = got
        try:
            if isinstance(want, bool) or isinstance(got, bool):
                ok = bool(got) == bool(want)
            elif isinstance(got, list) and isinstance(want, list):
                ok = len(got) == len(want) and all(_same(x, y) for x, y in zip(got, want))
            elif tol is not None and not isinstance(got, sp.MatrixBase):
                ok = abs(float(got) - float(want)) <= tol
                shown = f"{float(got):.6f}"
            else:
                ok = _same(got, want)
        except Exception as e:                       # noqa: BLE001
            ok, shown = False, f"<{e}>"
        print(f"  {'✓' if ok else '✗'} {name:46s} = {shown}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    print("行列式与线性变换")
    chk("det[[1,2],[3,4]]", det2(Mat2(1, 2, 3, 4)), sp.Integer(-2))
    chk("剪切矩阵 det 恒为 1（k=0）", det2(A_shift(0)), sp.Integer(1))
    chk("剪切矩阵 det 恒为 1（k=1.7）", det2(A_shift(sp.Rational(17, 10))), sp.Integer(1))
    chk("剪切把 e₁、e₂ 送去哪", cols2(A_shift(2)), [sp.Matrix([1, 0]), sp.Matrix([2, 1])])
    chk("Av = [[1,2],[0,1]](3,4)", apply2(A_shift(2), [3, 4]), sp.Matrix([11, 4]))

    print("\n特征值与特征向量（对称矩阵 [[1,k],[k,1]]）")
    for k in (0, 1, -2, sp.Rational(1, 2)):
        vals = sorted([float(e["value"]) for e in eigen2(A_sym(k))], reverse=True)
        want = sorted([float(1 + k), float(1 - k)], reverse=True)
        chk(f"k={k} 的两个特征值 = 1±k",
            all(abs(a - b) < 1e-12 for a, b in zip(vals, want)), True)
    # 关键性质：特征向量方向与 k 无关（避开 k=0 —— 那时矩阵是单位阵，方向不定）
    v1 = eigen2(A_sym(1))[0]["vector"]
    v2 = eigen2(A_sym(sp.Rational(3, 2)))[0]["vector"]
    ratio1 = sp.simplify(v1[0] / v1[1])
    ratio2 = sp.simplify(v2[0] / v2[1])
    chk("特征向量方向与 k 无关（比值不变）", sp.simplify(ratio1 - ratio2), sp.Integer(0))
    chk("两特征向量正交（对称矩阵必如此）",
        dot(eigen2(A_sym(1))[0]["vector"], eigen2(A_sym(1))[1]["vector"]), sp.Integer(0))
    chk("特征值之和 = 迹", sum(e["value"] for e in eigen2(A_sym(3))), trace2(A_sym(3)))
    chk("特征值之积 = 行列式",
        sp.simplify(sp.prod([e["value"] for e in eigen2(A_sym(3))]) - det2(A_sym(3))),
        sp.Integer(0))

    print("\n矩阵幂与马尔可夫稳态")
    A = A_markov()
    chk("马尔可夫矩阵每列和为 1", [sum(A[:, j]) for j in range(2)], [sp.Integer(1), sp.Integer(1)])
    pi = steady_state(A)
    chk("稳态第一分量", pi[0], sp.Rational(3, 5))
    chk("稳态第二分量", pi[1], sp.Rational(2, 5))
    chk("稳态满足 Aπ = π", sp.simplify(A * pi - pi), sp.zeros(2, 1))
    chk("A⁰ 是单位矩阵", matrix_power(A, 0), sp.eye(2))
    # A^k 的列收敛到稳态
    A10 = matrix_power(A, 10)
    chk("A¹⁰ 与稳态的偏差 < 0.01", max(abs(float(A10[i, j] - pi[i])) for i in range(2) for j in range(2)) < 0.01, True)
    A50 = matrix_power(A, 50)
    chk("A⁵⁰ 已收敛到稳态", max(abs(float(A50[i, j] - pi[i])) for i in range(2) for j in range(2)) < 1e-8, True)

    print("\n投影与最小二乘")
    chk("投影系数 c = aᵀb/aᵀa", proj_scalar([1, 1], [2, 0]), sp.Integer(1))
    chk("  └ 投影向量", proj_vec([1, 1], [2, 0]), sp.Matrix([1, 1]))
    chk("  └ 残差垂直于 a", dot(reject_vec([1, 1], [2, 0]), [1, 1]), sp.Integer(0))
    # 点恰在一条直线上 -> 残差为 0
    ls = least_squares([(0, 1), (1, 2), (2, 3)])
    chk("三点共线时斜率", ls["m"], sp.Integer(1))
    chk("  └ 截距", ls["c"], sp.Integer(1))
    chk("  └ 残差平方和 = 0", ls["ss_res"], sp.Integer(0))
    # 四个点：法方程手算可核对（Σx=6, Σy=14, Σx²=14, Σxy=29, det=20）
    ls2 = least_squares([(0, 1), (1, 3), (2, 4), (3, 6)])
    chk("四点的斜率（精确）", ls2["m"], sp.Rational(8, 5))
    chk("  └ 截距（精确）", ls2["c"], sp.Rational(11, 10))
    chk("  └ 残差平方和（精确）", ls2["ss_res"], sp.Rational(1, 5))
    # 最小二乘确实最小：固定截距、只把斜率挪开一点，残差就变大
    alt = ss_residual([(0, 1), (1, 3), (2, 4), (3, 6)], sp.Rational(3, 2), sp.Rational(11, 10))
    chk("  └ 把斜率挪到 1.5 后残差更大", bool(alt > ls2["ss_res"]), True)

    print("\n秩、列空间与零空间")
    chk("rank[[1,1],[1,1]]", rank_of(A_rank(1)), 1)
    chk("rank[[1,1],[1,2]]", rank_of(A_rank(2)), 2)
    chk("k=1 时 det = 0", det2(A_rank(1)), sp.Integer(0))
    chk("k=2 时 det ≠ 0", det2(A_rank(2)) != 0, True)
    nb = null_basis(A_rank(1))
    chk("k=1 的零空间维数 = 1", len(nb), 1)
    chk("  └ 基向量满足 x+y=0", nb[0][0] + nb[0][1], sp.Integer(0))
    chk("满秩时零空间只含零向量", len(null_basis(A_rank(2))), 0)
    chk("列空间的维数 = 秩", len(col_basis(A_rank(1))), 1)
    chk("  └ 且等于秩 1", rank_of(A_rank(1)), 1)

    print("\n奇异值分解")
    s = svd2(A_shift(1))
    chk("剪切 k=1 的 σ₁（黄金比）", s[0]["s"], (1 + sp.sqrt(5)) / 2, 1e-9)
    chk("  └ σ₂ = 1/σ₁（因 det=1）", s[1]["s"], 1 / ((1 + sp.sqrt(5)) / 2), 1e-9)
    chk("  └ σ₁·σ₂ = |det|", s[0]["s"] * s[1]["s"], 1, 1e-9)
    s0 = svd2(A_shift(0))
    chk("恒等变换的两个奇异值都是 1", [s0[0]["s"], s0[1]["s"]], [sp.Integer(1), sp.Integer(1)])
    s2 = svd2(Mat2(3, 0, 0, 2))
    chk("对角矩阵的奇异值 = |对角元|", [s2[0]["s"], s2[1]["s"]], [sp.Integer(3), sp.Integer(2)])
    chk("奇异值非负", all(float(d["s"]) >= 0 for d in svd2(Mat2(-3, 0, 0, 2))), True)

    print("\nGram–Schmidt 正交化")
    qs = gram_schmidt([[1, 1], [1, 0]])
    chk("q₁ = (1,1)/√2", qs[0], sp.Matrix([1, 1]) / sp.sqrt(2))
    chk("q₂ = (1,−1)/√2", qs[1], sp.Matrix([1, -1]) / sp.sqrt(2))
    chk("q₁ ⊥ q₂", dot(qs[0], qs[1]), sp.Integer(0))
    chk("q₁ 是单位向量", norm(qs[0]), sp.Integer(1))
    chk("q₂ 是单位向量", norm(qs[1]), sp.Integer(1))
    qs3 = gram_schmidt([[2, 0], [1, 1]])
    chk("从 (2,0) 出发时 q₁ = (1,0)", qs3[0], sp.Matrix([1, 0]))
    chk("  └ q₂ = (0,1)", qs3[1], sp.Matrix([0, 1]))
    try:
        gram_schmidt([[1, 1], [2, 2]])
        chk("线性相关的向量组应报错", False, True)
    except ValueError:
        chk("线性相关的向量组应报错", True, True)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
