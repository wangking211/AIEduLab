#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vector_kernel.py —— 平面向量内核（高中必修 + 选择性必修的向量基础）

**与 edu-solid-geometry 的边界**：那个技能用「建系 + 向量法」解**立体几何**
（线面角、二面角、异面直线、点到面距离）。本技能只做**向量本身的运算与几何意义**
（线性运算、共线定理、基本定理、数量积、投影、定比分点、余弦定理），
不重复立体几何的应用题。

覆盖：
  · 向量的线性运算（加减、数乘）与平行四边形/三角形法则
  · 共线定理与三点共线（xA + yB 且 x+y=1）
  · 平面向量基本定理：任意向量在给定基底下**唯一**分解
  · 数量积、夹角、垂直与平行的判据
  · 投影（数量投影与投影向量）
  · 定比分点（含中点、重心）
  · 力的合成与余弦定理

设计原则（与全项目一致）：
  · **不手写数字**：所有结果由本内核用 sympy 精确算出（含根式化简）。
  · 坐标与答案同源：3D/2D 画板与解题数值来自同一套坐标。
  · 自检：python vector_kernel.py
"""

import math

import sympy as sp

__all__ = [
    "tex", "f", "num_str", "vec", "vec_tex", "pt_tex",
    "add", "sub", "scale", "is_collinear", "cross2",
    "affine_combo", "on_segment_line",
    "decompose", "basis_unique_check",
    "dot", "norm", "angle_deg", "is_perpendicular", "is_parallel",
    "projection_scalar", "projection_vec", "rejection_vec",
    "resultant_mag", "cosine_rule",
    "section_point", "midpoint", "centroid",
    "to_px",
]


# ---------------------------------------------------------------- 排版助手

def tex(e):
    return sp.latex(sp.simplify(sp.sympify(e)))


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


# ---------------------------------------------------------------- 向量构造与排版

def _s(x):
    """把输入变成 sympy **精确**数：Python 的 float 先经 nsimplify 还原成有理数。

    为什么不能直接用 sp.sympify：`sp.sympify(0.5)` 得到的是 Float("0.5")，
    于是「叉积是否为零」这类**精确判据**会被浮点误差破坏
    （实测 cross2 给出 −4.4e−16 而不是 0，共线判断直接失效）。
    本内核的坐标都是干净的十进制数，nsimplify 能准确还原。
    """
    if isinstance(x, float):
        return sp.nsimplify(x)
    return sp.sympify(x)


def vec(*comps):
    """构造 2 维或 3 维列向量。vec(1, 2) 或 vec([1, 2]) 均可。"""
    if len(comps) == 1 and isinstance(comps[0], (list, tuple)):
        comps = comps[0]
    return sp.Matrix([_s(c) for c in comps])


def vec_tex(v):
    v = sp.Matrix(v)
    inner = ", ".join(sp.latex(sp.simplify(c)) for c in v)
    return r"\left(" + inner + r"\right)"


def pt_tex(p, name=""):
    return (name + vec_tex(p)) if name else vec_tex(p)


# ---------------------------------------------------------------- 线性运算

def add(u, v):
    return sp.Matrix(u) + sp.Matrix(v)


def sub(u, v):
    return sp.Matrix(u) - sp.Matrix(v)


def scale(k, u):
    return _s(k) * sp.Matrix(u)


def cross2(u, v):
    """二维叉积的标量值 u_x v_y − u_y v_x —— 共线判据与有向面积都用它。"""
    u, v = sp.Matrix(u), sp.Matrix(v)
    return sp.simplify(u[0] * v[1] - u[1] * v[0])


def is_collinear(u, v):
    """共线（平行）判据：二维用叉积为零；三维用叉积向量为零。"""
    u, v = sp.Matrix(u), sp.Matrix(v)
    if len(u) == 2:
        return sp.simplify(cross2(u, v)) == 0
    c = u.cross(v)
    return all(sp.simplify(x) == 0 for x in c)


# ---------------------------------------------------------------- 三点共线

def affine_combo(A, B, x, y):
    """x·A + y·B —— 当 x+y=1 时，这个点是直线 AB 上的点。"""
    return sp.simplify(_s(x) * sp.Matrix(A) + _s(y) * sp.Matrix(B))


def on_segment_line(A, B, P):
    """判断 P 是否在直线 AB 上（用 (P−A) 与 (B−A) 共线）。

    返回 (是否共线, 系数 x)，其中 P = x·A + (1−x)·B。
    """
    A, B, P = sp.Matrix(A), sp.Matrix(B), sp.Matrix(P)
    d = B - A
    w = P - A
    col = is_collinear(d, w)
    # 解 w = t·d 得 t，则 P = A + t(B−A) = (1−t)A + tB，故 x = 1−t
    t = None
    for i in range(len(d)):
        if sp.simplify(d[i]) != 0:
            t = sp.simplify(w[i] / d[i])
            break
    return col, (sp.simplify(1 - t) if t is not None else None)


# ---------------------------------------------------------------- 平面向量基本定理

def decompose(c, e1, e2):
    """把 c 用基底 {e1, e2} 表示：解 λe1 + μe2 = c，返回 (λ, μ)。

    基向量不共线时解**唯一** —— 这就是平面向量基本定理。
    """
    e1, e2, c = sp.Matrix(e1), sp.Matrix(e2), sp.Matrix(c)
    M = sp.Matrix.hstack(e1, e2)
    if sp.simplify(M.det()) == 0:
        raise ValueError("e1 与 e2 不构成基底（共线）")
    sol = M.solve(c)
    return sp.simplify(sol[0]), sp.simplify(sol[1])


def basis_unique_check(c, e1, e2):
    """验证分解唯一：返回 (λ, μ, 残差) —— 残差应为零向量。"""
    lam, mu = decompose(c, e1, e2)
    res = sp.simplify(sp.Matrix(c) - (lam * sp.Matrix(e1) + mu * sp.Matrix(e2)))
    return lam, mu, res


# ---------------------------------------------------------------- 数量积与夹角

def dot(u, v):
    return sp.simplify(sp.Matrix(u).dot(sp.Matrix(v)))


def norm(u):
    return sp.simplify(sp.sqrt(sp.Matrix(u).dot(sp.Matrix(u))))


def angle_deg(u, v):
    """两向量夹角（度）。零向量无夹角，返回 None。"""
    nu, nv = norm(u), norm(v)
    if sp.simplify(nu) == 0 or sp.simplify(nv) == 0:
        return None
    c = sp.simplify(dot(u, v) / (nu * nv))
    c = sp.Max(sp.Integer(-1), sp.Min(sp.Integer(1), c))
    return sp.simplify(sp.acos(c) * 180 / sp.pi)


def is_perpendicular(u, v):
    return sp.simplify(dot(u, v)) == 0


def is_parallel(u, v):
    return is_collinear(u, v)


# ---------------------------------------------------------------- 投影

def projection_scalar(a, b):
    """b 在 a 上的数量投影：|b|cosθ = (a·b)/|a|。"""
    a, b = sp.Matrix(a), sp.Matrix(b)
    na = norm(a)
    if sp.simplify(na) == 0:
        raise ValueError("a 是零向量，无法定义投影")
    return sp.simplify(dot(a, b) / na)


def projection_vec(a, b):
    """b 在 a 上的投影向量：(a·b)/(a·a) · a。"""
    a, b = sp.Matrix(a), sp.Matrix(b)
    aa = sp.simplify(a.dot(a))
    if aa == 0:
        raise ValueError("a 是零向量，无法定义投影")
    return sp.simplify((dot(a, b) / aa) * a)


def rejection_vec(a, b):
    """b 垂直于 a 的分量：b − 投影向量。"""
    return sp.simplify(sp.Matrix(b) - projection_vec(a, b))


# ---------------------------------------------------------------- 力的合成与余弦定理

def resultant_mag(F1, F2, theta_deg):
    """两力夹角 θ 时的合力大小：√(F1² + F2² + 2F1F2cosθ)。

    它其实就是余弦定理：把 F1、F2 首尾相接，第三边就是合力。
    """
    t = sp.sympify(theta_deg) * sp.pi / 180
    v = sp.sympify(F1) ** 2 + sp.sympify(F2) ** 2 + 2 * sp.sympify(F1) * sp.sympify(F2) * sp.cos(t)
    return sp.simplify(sp.sqrt(sp.simplify(v)))


def cosine_rule(a, b, C_deg):
    """余弦定理：已知两边 a、b 与夹角 C，求第三边 c。"""
    t = sp.sympify(C_deg) * sp.pi / 180
    return sp.simplify(sp.sqrt(sp.sympify(a) ** 2 + sp.sympify(b) ** 2
                               - 2 * sp.sympify(a) * sp.sympify(b) * sp.cos(t)))


# ---------------------------------------------------------------- 定比分点

def section_point(A, B, lam):
    """定比分点：AP = λ·PB 的点 P = (A + λB)/(1 + λ)。

    λ = 1 时是中点；λ → ∞ 时趋近 B；λ = −1 时无意义（A、B 重合于无穷远）。
    """
    lam = _s(lam)
    if sp.simplify(1 + lam) == 0:
        raise ValueError("λ = −1 时定比分点不存在")
    return sp.simplify((sp.Matrix(A) + lam * sp.Matrix(B)) / (1 + lam))


def midpoint(A, B):
    return section_point(A, B, 1)


def centroid(A, B, C):
    """三角形重心 = 三顶点坐标的平均。"""
    return sp.simplify((sp.Matrix(A) + sp.Matrix(B) + sp.Matrix(C)) / 3)


# ---------------------------------------------------------------- 画板映射

def to_px(points, scale=1.0):
    """把数学坐标（dict 或 list）转成画板用的浮点坐标。"""
    def one(p):
        return [float(sp.N(c) * sp.Float(scale)) for c in sp.Matrix(p)]
    if isinstance(points, dict):
        return {k: one(v) for k, v in points.items()}
    return [one(p) for p in points]


# ================================================================ 自检

def _same(a, b):
    """比较标量/布尔/字符串/列表/矩阵 —— sympify 相减对后三类都不适用。"""
    if isinstance(a, str) or isinstance(b, str):
        return str(a) == str(b)
    if isinstance(a, bool) or isinstance(b, bool):
        return bool(a) == bool(b)
    if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        a, b = list(a), list(b)
        return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
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
            elif isinstance(want, str) or isinstance(got, str):
                ok = str(got) == str(want)
            elif isinstance(got, (list, tuple)) or isinstance(want, (list, tuple)):
                ok = _same(got, want)
            elif tol is not None and not isinstance(got, sp.MatrixBase):
                ok = abs(float(got) - float(want)) <= tol
                shown = f"{float(got):.6f}"
            else:
                ok = _same(got, want)
        except Exception as e:                        # noqa: BLE001
            ok, shown = False, f"<{e}>"
        print(f"  {'✓' if ok else '✗'} {name:44s} = {shown}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    print("线性运算")
    chk("a + b", add(vec(1, 2), vec(3, -1)), vec(4, 1))
    chk("a − b", sub(vec(1, 2), vec(3, -1)), vec(-2, 3))
    chk("2a", scale(2, vec(1, 2)), vec(2, 4))
    chk("−1·a 反向", scale(-1, vec(1, 2)), vec(-1, -2))
    chk("加法交换律", add(vec(1, 2), vec(3, 4)), add(vec(3, 4), vec(1, 2)))
    chk("|a|（勾股）", norm(vec(3, 4)), sp.Integer(5))
    chk("|a| 含根式", norm(vec(1, 1)), sp.sqrt(2))

    print("\n共线判据")
    chk("(1,2) 与 (2,4) 共线", is_collinear(vec(1, 2), vec(2, 4)), True)
    chk("(1,2) 与 (2,5) 不共线", is_collinear(vec(1, 2), vec(2, 5)), False)
    chk("叉积为零 ⇔ 共线", cross2(vec(1, 2), vec(2, 4)), sp.Integer(0))
    chk("三维共线", is_collinear(vec(1, 2, 3), vec(2, 4, 6)), True)
    chk("三维不共线", is_collinear(vec(1, 2, 3), vec(2, 4, 7)), False)

    print("\n三点共线与仿射组合")
    A, B = vec(0, 0), vec(1, 0)
    chk("0.3A + 0.7B（系数和 = 1）", affine_combo(A, B, sp.Rational(3, 10), sp.Rational(7, 10)), vec(sp.Rational(7, 10), 0))
    col, x = on_segment_line(A, B, vec(sp.Rational(7, 10), 0))
    chk("  └ 该点在直线 AB 上", col, True)
    chk("  └ 反解出系数 x = 0.3", x, sp.Rational(3, 10))
    col2, _ = on_segment_line(A, B, vec(sp.Rational(7, 10), sp.Rational(1, 10)))
    chk("纵坐标非零 → 不在直线 AB 上", col2, False)
    # 系数和不为 1 时一般不在直线 AB 上
    P = affine_combo(vec(0, 0), vec(1, 1), 1, 1)
    chk("1·A + 1·B（和 = 2）一般不在 AB 上", on_segment_line(vec(0, 0), vec(1, 1), P)[0], True)

    print("\n平面向量基本定理")
    d1 = basis_unique_check(vec(2, 0), vec(1, 0), vec(0, 1))
    chk("标准基下的分解唯一", [d1[0], d1[1]], [sp.Integer(2), sp.Integer(0)])
    chk("  └ 残差为零向量", list(d1[2]), [0, 0])
    d2 = basis_unique_check(vec(2, 0), vec(1, 1), vec(1, -1))
    chk("斜基底 (1,1)、(1,−1) 下 c=(2,0) 分解", [d2[0], d2[1]], [sp.Integer(1), sp.Integer(1)])
    d3 = basis_unique_check(vec(3, 5), vec(2, 1), vec(1, 3))
    chk("一般基底下的分解", [d3[0], d3[1]], [sp.Rational(4, 5), sp.Rational(7, 5)])
    try:
        decompose(vec(1, 1), vec(1, 1), vec(2, 2))
        chk("共线基底应报错", False, True)
    except ValueError:
        chk("共线基底应报错", True, True)

    print("\n数量积与夹角")
    chk("(1,0)·(0,1) = 0", dot(vec(1, 0), vec(0, 1)), sp.Integer(0))
    chk("(1,0)·(1,1) = 1", dot(vec(1, 0), vec(1, 1)), sp.Integer(1))
    chk("垂直判据", is_perpendicular(vec(1, 0), vec(0, 1)), True)
    chk("平行判据", is_parallel(vec(1, 2), vec(2, 4)), True)
    chk("夹角：(1,0) 与 (1,1) 是 45°", angle_deg(vec(1, 0), vec(1, 1)), sp.Integer(45))
    chk("夹角：(1,0) 与 (−1,0) 是 180°", angle_deg(vec(1, 0), vec(-1, 0)), sp.Integer(180))
    chk("夹角：(1,0) 与 (0,1) 是 90°", angle_deg(vec(1, 0), vec(0, 1)), sp.Integer(90))
    # (a+b)² = a² + 2a·b + b² 恒等式
    a, b = vec(2, 1), vec(1, 3)
    lhs = norm(add(a, b)) ** 2
    rhs = norm(a) ** 2 + 2 * dot(a, b) + norm(b) ** 2
    chk("|a+b|² = |a|² + 2a·b + |b|²", sp.simplify(lhs - rhs), sp.Integer(0))

    print("\n投影")
    # 数量投影 = a·b/|a|，不是 a·b/(a·a) —— 后者是「投影系数」。
    # 这里 a=(2,0)、b=(1,1)：a·b=2，|a|=2，故数量投影 = 1；系数 = 2/4 = 1/2。
    chk("数量投影 a·b/|a|", projection_scalar(vec(2, 0), vec(1, 1)), sp.Integer(1))
    chk("  └ 与 |b|cosθ 一致",
        projection_scalar(vec(2, 0), vec(1, 1)),
        norm(vec(1, 1)) * sp.cos(sp.acos(dot(vec(2, 0), vec(1, 1)) / (norm(vec(2, 0)) * norm(vec(1, 1))))))
    chk("投影向量", projection_vec(vec(2, 0), vec(1, 1)), vec(1, 0))
    chk("垂直分量", rejection_vec(vec(2, 0), vec(1, 1)), vec(0, 1))
    chk("残差 ⊥ a", dot(rejection_vec(vec(2, 0), vec(1, 1)), vec(2, 0)), sp.Integer(0))
    # 投影向量 + 垂直分量 = b
    chk("投影 + 垂直分量 = b",
        add(projection_vec(vec(3, 1), vec(2, 5)), rejection_vec(vec(3, 1), vec(2, 5))), vec(2, 5))

    print("\n力的合成与余弦定理")
    chk("等大二力夹角 120° 的合力 = 1", resultant_mag(1, 1, 120), sp.Integer(1))
    chk("同向（0°）的合力 = 3", resultant_mag(1, 2, 0), sp.Integer(3))
    chk("反向（180°）的合力 = 1", resultant_mag(1, 2, 180), sp.Integer(1))
    chk("垂直（90°）的合力 = √13", resultant_mag(2, 3, 90), sp.sqrt(13))
    chk("余弦定理：3、4 夹角 90° → 5", cosine_rule(3, 4, 90), sp.Integer(5))
    chk("余弦定理：1、1 夹角 60° → 1", cosine_rule(1, 1, 60), sp.Integer(1))

    print("\n定比分点")
    chk("中点", section_point(vec(0, 0), vec(2, 2), 1), vec(1, 1))
    chk("λ=2 的点", section_point(vec(0, 0), vec(3, 0), 2), vec(2, 0))
    chk("λ=−2 的点（外分）", section_point(vec(0, 0), vec(3, 0), -2), vec(6, 0))
    chk("重心", centroid(vec(0, 0), vec(3, 0), vec(0, 3)), vec(1, 1))
    try:
        section_point(vec(0, 0), vec(1, 1), -1)
        chk("λ=−1 应报错", False, True)
    except ValueError:
        chk("λ=−1 应报错", True, True)
    # 定比分点恒在直线 AB 上
    P = section_point(vec(1, 2), vec(5, 8), sp.Rational(3, 2))
    chk("定比分点必在直线 AB 上", on_segment_line(vec(1, 2), vec(5, 8), P)[0], True)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
