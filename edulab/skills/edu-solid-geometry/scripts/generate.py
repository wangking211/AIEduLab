#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化课程数据注入 template/lesson.html，产出单页 HTML。

数据全部由 lib/geometry_kernel.py 的确定性计算驱动（方案 A）：
坐标、向量、最终答案均为 sympy 精确计算结果，3D 坐标与解题数值同源、严格一致。

依赖: sympy。用一个能 import sympy 的 python3 运行（若缺: python3 -m pip install sympy）:
    python3 scripts/generate.py [输出路径.html]
"""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PLACEHOLDER = "__LESSON_DATA__"

sys.path.insert(0, str(SKILL_DIR.parent.parent / "shared"))   # 共享运行时（edulab/shared/skillkit.py）
sys.path.insert(0, str(SKILL_DIR / "lib"))
import geometry_kernel as gk  # noqa: E402
import bodies  # noqa: E402
from skillkit import cli      # noqa: E402


def _centroid(three_points):
    names = list(three_points)
    n = len(names)
    return [sum(three_points[k][i] for k in names) / n for i in range(3)]


def build_cube_data() -> dict:
    """正方体 ABCD-A1B1C1D1（棱长 1），求直线 A1C 与底面 ABCD 所成角的正弦值。

    几何体拓扑取自 bodies.cuboid，顶点坐标与答案取自 geometry_kernel（同源）。
    """
    sol = gk.solve_cube_line_plane_angle(edge=1, scale=2)
    mp = sol["math_points"]
    v = sol["vals"]
    ans = sol["answer_latex"]
    tp = sol["three_points"]

    topo = bodies.cuboid()  # spheres + 12 条棱
    center = _centroid(tp)

    model = {
        "target": center,
        "initialCamera": [6, 5, 7],
        "points": tp,
        "spheres": topo["spheres"],
        "edges": topo["edges"],
        "elements": {
            "Line_A1C": {"type": "line", "a": "A1", "b": "C", "color": "emphasis", "depthTest": False},
            "Plane_ABCD": {"type": "plane", "pts": ["A", "B", "C", "D"]},
            "Normal_Vector": {"type": "arrow", "origin": "A", "dir": [0, 1, 0], "length": 1.6, "color": "normal"},
            "Axis": {"type": "axes", "size": 2.6},
        },
    }

    lesson = {
        "language": "zh-CN",
        "meta": "交互解题 · 线面角",
        "title": "正方体ABCD-A₁B₁C₁D₁中，棱长为1，求直线A₁C与底面ABCD所成角的正弦值",
        "answerLabel": "直线 A₁C 与底面 ABCD 所成角的正弦值",
        "answerValue": f"${ans}$",
    }

    steps = [
        {
            "title": "建立空间直角坐标系",
            "content": (
                r"<p>以顶点 $A$ 为原点，$AB$、$AD$、$AA_1$ 分别为 $x$、$y$、$z$ 轴建立坐标系。</p>"
                r"<p>因为棱长为 $1$，关键点坐标为：</p>"
                r"$$A" + mp["A"] + r", C" + mp["C"] + r", A_1" + mp["A1"] + r"$$"
            ),
            "highlight": ["Axis"],
            "cameraPos": {"x": 6, "y": 5, "z": 7},
        },
        {
            "title": "求直线 A₁C 的方向向量",
            "content": (
                r"<p>直线 $A_1C$ 的方向向量为：</p>"
                r"$$\vec{A_1C} = C - A_1 = " + v["A1C"] + r"$$"
            ),
            "highlight": ["Line_A1C"],
            "cameraPos": {"x": 5, "y": 4, "z": 8},
        },
        {
            "title": "确定底面 ABCD 的法向量",
            "content": (
                r"<p>底面 $ABCD$ 在平面 $z = 0$ 上，其法向量竖直向上：</p>"
                r"$$\vec{n} = " + v["n_simpl"] + r"$$"
            ),
            "highlight": ["Line_A1C", "Plane_ABCD", "Normal_Vector"],
            "cameraPos": {"x": 4, "y": 6, "z": 5},
        },
        {
            "title": "利用向量公式求解",
            "content": (
                r"<p>设直线 $A_1C$ 与底面所成角为 $\theta$。</p>"
                r"<p>线面角公式：$\sin\theta = \dfrac{|\vec{A_1C} \cdot \vec{n}|}{|\vec{A_1C}|\,|\vec{n}|}$</p>"
                r"<p>计算数量积与模长：</p>"
                r"$$\vec{A_1C} \cdot \vec{n} = " + v["dot"] + r", \quad |\vec{A_1C}| = " + v["norm_line"] + r"$$"
                r"<p>代入公式：</p>"
                r"$$\sin\theta = " + v["sin"] + r"$$"
                r"<p>所以，直线 $A_1C$ 与底面 $ABCD$ 所成角的正弦值为 $" + ans + r"$。</p>"
            ),
            "highlight": ["Line_A1C", "Plane_ABCD", "Normal_Vector"],
            "cameraPos": {"x": 5, "y": 5, "z": 6},
        },
    ]

    return {"lesson": lesson, "steps": steps, "model": model, "_answer": ans}


def build_data(base_edge=2, height=1) -> dict:
    """正四棱锥 P-ABCD（E 为 PC 中点）线面角；底边、高可参数化（随机出题用）。

    数值全部来自 geometry_kernel，文字步骤只负责把这些数值组织成讲解。
    """
    sol = gk.solve_pyramid_line_plane_angle(base_edge=base_edge, height=height, scale=1.5)
    mp = sol["math_points"]   # 数学坐标的 LaTeX，例如 "(\\sqrt{2}, 0, 0)"
    v = sol["vals"]           # 各步骤中间量 LaTeX
    ans = sol["answer_latex"]
    diag_tex = gk.tex(gk.sp.sympify(base_edge) * gk.sqrt(2))
    half_tex = gk.tex(gk.sp.sympify(base_edge) * gk.sqrt(2) / 2)

    # ---- 3D 模型：顶点坐标取自 kernel（与解题同源）；拓扑/高亮在此声明 ----
    model = {
        "target": [0, 0.45, 0],
        "initialCamera": [5, 4, 5],
        "points": sol["three_points"],
        "spheres": ["O", "P", "A", "B", "C", "D", "E"],
        "edges": [
            {"a": "A", "b": "B"},
            {"a": "B", "b": "C"},
            {"a": "C", "b": "D"},
            {"a": "D", "b": "A", "dashed": True},
            {"a": "P", "b": "A"},
            {"a": "P", "b": "B"},
            {"a": "P", "b": "C"},
            {"a": "P", "b": "D"},
            {"a": "A", "b": "C", "color": "aux", "dashed": True},
            {"a": "B", "b": "D", "color": "aux", "dashed": True, "name": "Line_BD"},
        ],
        "elements": {
            "Line_BE": {"type": "line", "a": "B", "b": "E", "color": "emphasis", "depthTest": False},
            "Plane_PAC": {"type": "plane", "pts": ["P", "A", "C"]},
            "Normal_Vector": {"type": "arrow", "origin": "O", "dir": [0, 0, 1], "length": 1.5, "color": "normal"},
            "Axis": {"type": "axes", "size": 3},
            # 线段长度标注（已知条件：底边、对角线、高）
            "Len_AB": {"type": "measure", "a": "A", "b": "B", "label": str(base_edge)},
            "Len_AC": {"type": "measure", "a": "A", "b": "C", "label": diag_tex},
            "Len_PO": {"type": "measure", "a": "P", "b": "O", "label": str(height)},
        },
    }

    lesson = {
        "language": "zh-CN",
        "meta": "交互解题 · 线面角",
        "title": f"正四棱锥P-ABCD中，底面边长为{base_edge}，高为{height}，E为PC中点，求直线BE与平面PAC所成角的正弦值",
        "answerLabel": "直线 BE 与平面 PAC 所成角的正弦值",
        "answerValue": f"${ans}$",
    }

    # ---- 步骤文案：数值占位由 kernel 计算结果填入（不心算）----
    steps = [
        {
            "title": "建立空间直角坐标系",
            "content": (
                r"<p>首先，我们需要建立一个合适的空间直角坐标系来量化几何元素。</p>"
                r"<p>取底面正方形 $ABCD$ 的中心 $O$ 为原点 $(0,0,0)$。</p>"
                r"<p>让底面对角线 $AC$ 在 $x$ 轴，$BD$ 在 $y$ 轴，顶点 $P$ 在 $z$ 轴上。</p>"
                r"<p>因为底面边长为 $" + str(base_edge) + r"$，所以两条对角线长为 $" + diag_tex + r"$，半对角线长为 $" + half_tex + r"$。于是关键点坐标为：</p>"
                r"$$A" + mp["A"] + r", C" + mp["C"] + r"$$"
                r"$$B" + mp["B"] + r", D" + mp["D"] + r"$$"
                r"$$P" + mp["P"] + r"$$"
                r"<p>这样 $AC \perp BD$ 关系更明显。</p>"
            ),
            "highlight": ["Axis", "Len_AB", "Len_AC", "Len_PO"],
            "cameraPos": {"x": 5, "y": 4, "z": 5},
        },
        {
            "title": "计算中点 E 与向量 BE",
            "content": (
                r"<p>已知 $E$ 是侧棱 $PC$ 的中点。</p>"
                r"<p>利用中点坐标公式：$E = \frac{P + C}{2}$</p>"
                r"$$P" + mp["P"] + r", C" + mp["C"] + r"$$"
                r"$$E = " + v["E"] + r"$$"
                r"<p>接下来计算直线 $BE$ 的方向向量 $\vec{BE}$：</p>"
                r"$$\vec{BE} = E - B = " + v["BE"] + r"$$"
            ),
            "highlight": ["Line_BE"],
            "cameraPos": {"x": 3, "y": 3, "z": 6},
        },
        {
            "title": "确定平面 PAC 的法向量",
            "content": (
                r"<p>我们需要求直线 $BE$ 与平面 $PAC$ 的夹角。</p>"
                r"<p>观察几何体特征：</p>"
                r"<ul>"
                r"<li>底面 $ABCD$ 是正方形，对角线互相垂直，即 $AC \perp BD$。</li>"
                r"<li>顶点 $P$ 在底面的投影是中心 $O$，所以 $PO \perp AC$。</li>"
                r"</ul>"
                r"<p>因为 $AC \perp BD$ 且 $AC \perp PO$，所以直线 $BD \perp$ 平面 $PAC$。</p>"
                r"<p>因此，平面 $PAC$ 的法向量 $\vec{n}$ 就是 $\vec{BD}$ 的方向：</p>"
                r"$$\vec{n} = " + v["n"] + r"$$"
                r"<p>简化取 $\vec{n} = " + v["n_simpl"] + r"$。</p>"
            ),
            "highlight": ["Line_BE", "Plane_PAC", "Normal_Vector"],
            "cameraPos": {"x": 4, "y": 5, "z": 2},
        },
        {
            "title": "利用向量公式求解",
            "content": (
                r"<p>设直线 $BE$ 与平面 $PAC$ 所成角为 $\theta$。</p>"
                r"<p>根据线面角公式：$\sin\theta = \dfrac{|\vec{BE} \cdot \vec{n}|}{|\vec{BE}|\,|\vec{n}|}$</p>"
                r"<p>向量数据：</p>"
                r"<ul>"
                r"<li>$\vec{BE} = " + v["BE"] + r"$</li>"
                r"<li>$\vec{n} = " + v["n_simpl"] + r"$</li>"
                r"</ul>"
                r"<p>计算数量积与模长：</p>"
                r"$$\vec{BE} \cdot \vec{n} = " + v["dot"] + r", \quad |\vec{BE}| = " + v["norm_BE"] + r"$$"
                r"<p>代入公式：</p>"
                r"$$\sin\theta = " + v["sin"] + r"$$"
                r"<p>所以，直线 $BE$ 与平面 $PAC$ 所成角的正弦值为 $" + ans + r"$。</p>"
            ),
            "highlight": ["Line_BE", "Plane_PAC", "Normal_Vector"],
            "cameraPos": {"x": 4, "y": 4.5, "z": 4},
        },
    ]

    return {"lesson": lesson, "steps": steps, "model": model, "_answer": ans}


def build_box_volume_data(lx=3, ly=4, lz=5) -> dict:
    """长方体 ABCD-A1B1C1D1，已知长宽高，求体积。演示非角度题型端到端出图。"""
    V = gk.volume_box(lx, ly, lz)
    pts = gk.cuboid(lx, ly, lz)
    scale = 3.0 / max(lx, ly, lz)
    tp = gk.to_three(pts, scale=scale)
    topo = bodies.cuboid()
    center = _centroid(tp)
    ans = gk.tex(V)

    model = {
        "target": center,
        "initialCamera": [center[0] + 5, center[1] + 4, center[2] + 6],
        "points": tp,
        "spheres": topo["spheres"],
        "edges": topo["edges"],
        "elements": {
            "Edge_L": {"type": "line", "a": "A", "b": "B", "color": "emphasis"},
            "Edge_W": {"type": "line", "a": "A", "b": "D", "color": "emphasis"},
            "Edge_H": {"type": "line", "a": "A", "b": "A1", "color": "emphasis"},
            "Axis": {"type": "axes", "size": max(tp_span(tp), 2.5)},
        },
    }
    lesson = {
        "language": "zh-CN",
        "meta": "交互解题 · 体积",
        "title": f"长方体ABCD-A₁B₁C₁D₁的长、宽、高分别为 {lx}、{ly}、{lz}，求其体积",
        "answerLabel": "长方体的体积",
        "answerValue": f"${ans}$",
    }
    steps = [
        {
            "title": "明确长、宽、高",
            "content": (
                r"<p>以顶点 $A$ 为原点建立坐标系，三条从 $A$ 出发的棱即长、宽、高：</p>"
                r"<ul>"
                r"<li>长 $AB = " + str(lx) + r"$</li>"
                r"<li>宽 $AD = " + str(ly) + r"$</li>"
                r"<li>高 $AA_1 = " + str(lz) + r"$</li>"
                r"</ul>"
            ),
            "highlight": ["Edge_L", "Edge_W", "Edge_H", "Axis"],
            "cameraPos": {"x": center[0] + 5, "y": center[1] + 4, "z": center[2] + 6},
        },
        {
            "title": "应用长方体体积公式",
            "content": (
                r"<p>长方体体积等于长 × 宽 × 高：</p>"
                r"$$V = AB \times AD \times AA_1$$"
            ),
            "highlight": ["Edge_L", "Edge_W", "Edge_H"],
            "cameraPos": {"x": center[0] + 4, "y": center[1] + 5, "z": center[2] + 5},
        },
        {
            "title": "代入求值",
            "content": (
                r"$$V = " + str(lx) + r" \times " + str(ly) + r" \times " + str(lz) + r" = " + ans + r"$$"
                r"<p>所以该长方体的体积为 $" + ans + r"$。</p>"
            ),
            "highlight": ["Edge_L", "Edge_W", "Edge_H"],
            "cameraPos": {"x": center[0] + 5, "y": center[1] + 4, "z": center[2] + 5},
        },
    ]
    return {"lesson": lesson, "steps": steps, "model": model, "_answer": ans}


def tp_span(three_points):
    xs = [three_points[k][i] for k in three_points for i in range(3)]
    return max(abs(x) for x in xs) + 0.5


def build_random_data(seed=0) -> dict:
    """随机出题：随机选题型与参数，求解，答案不规整就重抽，返回可渲染数据。

    当前覆盖：长方体体积、正四棱锥线面角。可按同样的 resample 模式扩展更多题型。
    """
    import random
    rng = random.Random(seed)
    kind = rng.choice(["box_volume", "pyramid_lpa"])

    if kind == "box_volume":
        lx, ly, lz = (rng.randint(2, 6) for _ in range(3))
        return build_box_volume_data(lx, ly, lz)

    # pyramid 线面角：重抽直到答案规整
    for _ in range(50):
        a = rng.choice([2, 4, 6])
        h = rng.randint(1, 4)
        sol = gk.solve_pyramid_line_plane_angle(base_edge=a, height=h)
        if gk.is_clean(sol["_exact"]["sin_theta"]):
            return build_data(base_edge=a, height=h)
    # 兜底
    return build_box_volume_data()


# =====================================================================
# 新增题型 4：点到平面的距离
# =====================================================================
def build_distance_data(edge=1) -> dict:
    """正方体 ABCD-A1B1C1D1（棱长 a），求点 A 到平面 A1BD 的距离。"""
    sol = gk.solve_cube_point_plane_distance(edge=edge, scale=2)
    v, ans = sol["vals"], sol["answer_latex"]
    topo = bodies.cuboid()
    center = _centroid(sol["three_points"])
    frac = gk.tex(gk.sp.sympify(edge))

    model = {
        "target": center,
        "initialCamera": [6, 5, 7],
        "points": sol["three_points"],
        "spheres": topo["spheres"],
        "edges": topo["edges"],
        "elements": {
            "Plane_A1BD": {"type": "plane", "pts": ["A1", "B", "D"]},
            "Normal_Vector": {"type": "arrow", "origin": "A1", "dir": [1, 1, 1],
                              "length": 1.7, "color": "normal"},
            "Height": {"type": "line", "a": "A", "b": "A1", "color": "aux",
                       "dashed": True, "depthTest": False},
            "Axis": {"type": "axes", "size": 2.6},
        },
    }

    lesson = {
        "language": "zh-CN", "meta": "交互解题 · 点到平面距离",
        "title": f"正方体ABCD-A₁B₁C₁D₁的棱长为{frac}，求点A到平面A₁BD的距离",
        "answerLabel": "点 A 到平面 A₁BD 的距离",
        "answerValue": f"${ans}$",
    }

    steps = [
        {"title": "建系并写出关键点",
         "content": (r"<p>以 $A$ 为原点，$AB$、$AD$、$AA_1$ 分别为 $x$、$y$、$z$ 轴。</p>"
                     r"<p>棱长为 $" + frac + r"$，于是</p>"
                     r"$$A(0,0,0),\ B" + sol["math_points"]["B"] + r",\ A_1" + sol["math_points"]["A1"] + r",\ D" + sol["math_points"]["D"] + r"$$")},
        {"title": "求平面 A₁BD 的法向量",
         "content": (r"<p>取 $\overrightarrow{A_1B}$ 与 $\overrightarrow{A_1D}$ 的叉积：</p>"
                     r"<p>法向量 $n = " + v["n"] + r"$，约简到 $" + v["n_simpl"] + r"$。</p>"
                     r"<p>$|n| = " + v["norm_n"] + r"$。</p>"
                     r"<p>点到平面的距离公式是 "
                     r"$d = \dfrac{|(P-P_0)\cdot n|}{|n|}$，这里 $P=A$、$P_0=A_1$。</p>")},
        {"title": "代公式求距离",
         "content": (r"<p>$\overrightarrow{A_1A}$ 与 $n$ 的数量积绝对值为 $"
                     + v["numerator"] + r"$，除以 $|n| = " + v["norm_n"] + r"$ 得</p>"
                     r"<p>$$d = " + ans + r"$$</p>"
                     r"<p>注意这个距离**只由平面的方程与点的坐标决定**，"
                     r"与图中那条辅助线画在哪里无关 —— 换一个点算，结果会不同。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "model": model, "_answer": ans}


# =====================================================================
# 新增题型 5：二面角
# =====================================================================
def build_dihedral_data(edge=1) -> dict:
    """正方体 ABCD-A1B1C1D1（棱长 a），求二面角 A1-BD-A 的余弦值。"""
    sol = gk.solve_cube_dihedral(edge=edge, scale=2)
    v, ans = sol["vals"], sol["answer_latex"]
    topo = bodies.cuboid()
    center = _centroid(sol["three_points"])

    model = {
        "target": center,
        "initialCamera": [5, 4, 6],
        "points": sol["three_points"],
        "spheres": topo["spheres"],
        "edges": topo["edges"],
        "elements": {
            "Plane_A1BD": {"type": "plane", "pts": ["A1", "B", "D"]},
            "Plane_ABD": {"type": "plane", "pts": ["A", "B", "D"]},
            "Edge_BD": {"type": "line", "a": "B", "b": "D", "color": "emphasis",
                        "depthTest": False},
            "Axis": {"type": "axes", "size": 2.6},
        },
    }

    lesson = {
        "language": "zh-CN", "meta": "交互解题 · 二面角",
        "title": "正方体ABCD-A₁B₁C₁D₁的棱长为1，求二面角A₁-BD-A的余弦值",
        "answerLabel": "二面角 A₁-BD-A 的余弦值",
        "answerValue": f"${ans}$",
    }

    steps = [
        {"title": "建系（与上一题同一套坐标）",
         "content": (r"<p>以 $A$ 为原点，三条棱为坐标轴。棱长为 1，则</p>"
                     r"$$A(0,0,0),\ B" + sol["math_points"]["B"] + r",\ D" + sol["math_points"]["D"] + r",\ A_1" + sol["math_points"]["A1"] + r"$$")},
        {"title": "在两个半平面内各取一条垂直于棱的向量",
         "content": (r"<p>二面角的棱是 $BD$。分别在平面 $A_1BD$ 与平面 $ABD$ 内，"
                     r"作**垂直于 $BD$** 的向量，两向量的夹角就是二面角。</p>"
                     r"<p>做法：把 $\overrightarrow{BA_1}$ 与 $\overrightarrow{BA}$ "
                     r"分别减去它们在 $\overrightarrow{BD}$ 上的投影，得到两条垂直于棱的分量，"
                     r"再求它们夹角的余弦（按定义取锐角或按钝角判断符号）。</p>")},
        {"title": "算出余弦与正切",
         "content": (r"<p>两个垂分量的夹角余弦为</p>"
                     r"<p>$$\cos\theta = " + ans + r"$$</p>"
                     r"<p>再由 $\tan\theta = \dfrac{\sqrt{1-\cos^2\theta}}{\cos\theta} = "
                     + v["tan"] + r"$。</p>"
                     r"<p>所以这个二面角约 $54.7^\circ$ —— 它与「$A_1$ 到底面的距离比 $AO$」"
                     r"（$O$ 为 $BD$ 中点）是同一个数：$\tan\theta = \dfrac{AA_1}{AO}$。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "model": model, "_answer": ans}


# =====================================================================
# 新增题型 6：异面直线所成角
# =====================================================================
def build_skew_data(edge=1) -> dict:
    """正方体 ABCD-A1B1C1D1（棱长 a），求异面直线 A1B 与 B1C 所成角的余弦值。"""
    sol = gk.solve_cube_skew_lines(edge=edge, scale=2)
    v, ans = sol["vals"], sol["answer_latex"]
    topo = bodies.cuboid()
    center = _centroid(sol["three_points"])

    model = {
        "target": center,
        "initialCamera": [6, 5, 7],
        "points": sol["three_points"],
        "spheres": topo["spheres"],
        "edges": topo["edges"],
        "elements": {
            "Line_A1B": {"type": "line", "a": "A1", "b": "B", "color": "emphasis",
                         "depthTest": False},
            "Line_B1C": {"type": "line", "a": "B1", "b": "C", "color": "normal",
                         "depthTest": False},
            "Axis": {"type": "axes", "size": 2.6},
        },
    }

    lesson = {
        "language": "zh-CN", "meta": "交互解题 · 异面直线夹角",
        "title": "正方体ABCD-A₁B₁C₁D₁的棱长为1，求异面直线A₁B与B₁C所成角的余弦值",
        "answerLabel": "异面直线 A₁B 与 B₁C 所成角的余弦值",
        "answerValue": f"${ans}$",
    }

    steps = [
        {"title": "异面直线：不平行的两条线",
         "content": (r"<p>$A_1B$ 与 $B_1C$ 不在同一平面内，也不平行 —— 这叫**异面直线**。</p>"
                     r"<p>求它们所成角的标准办法是**平移**：把其中一条平移到与另一条相交，"
                     r"用向量法就是直接算两个方向向量的夹角。</p>")},
        {"title": "取方向向量并算夹角",
         "content": (r"<p>$\overrightarrow{A_1B} = " + v["d1"] + r"$，"
                     r"$\overrightarrow{B_1C} = " + v["d2"] + r"$。</p>"
                     r"<p>数量积 $\overrightarrow{A_1B}\cdot\overrightarrow{B_1C} = "
                     + v["dot"] + r"$。</p>"
                     r"<p>注意异面直线所成角规定在 $(0^\circ,90^\circ]$ 内，"
                     r"所以余弦要取**绝对值**：$\cos\theta = "
                     r"\dfrac{|\overrightarrow{A_1B}\cdot\overrightarrow{B_1C}|}"
                     r"{|\overrightarrow{A_1B}|\,|\overrightarrow{B_1C}|}$。</p>")},
        {"title": "得出结论",
         "content": (r"<p>代入得</p>"
                     r"<p>$$\cos\theta = " + ans + r"$$</p>"
                     r"<p>即两直线成 $60^\circ$。这个结果**与棱长无关** ——"
                     r"把滑块（或把棱长改成 2、3）答案不变，因为它是纯方向量的比值。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "model": model, "_answer": ans}


# =====================================================================
# 新增题型 7：正四面体的体积与外接球
# =====================================================================
def build_tetra_data(edge=None) -> dict:
    """正四面体（棱长 2√2，坐标为整数）的体积、高、外接球与内切球半径。"""
    sol = gk.solve_regular_tetrahedron() if edge is None else gk.solve_regular_tetrahedron(edge)
    v, ans = sol["vals"], sol["answer_latex"]
    topo = bodies.tri_pyramid(apex="D", base=("A", "B", "C"))
    center = _centroid(sol["three_points"])

    model = {
        "target": center,
        "initialCamera": [4, 4, 5],
        "points": sol["three_points"],
        "spheres": topo["spheres"],
        "edges": topo["edges"],
        "elements": {
            "Edge_AB": {"type": "line", "a": "A", "b": "B", "color": "emphasis",
                        "depthTest": False},
            "Axis": {"type": "axes", "size": 2.4},
        },
    }

    lesson = {
        "language": "zh-CN", "meta": "交互解题 · 正四面体",
        "title": f"正四面体ABCD的棱长为${v['a']}$，求它的体积、高、外接球半径与内切球半径",
        "answerLabel": "正四面体的体积",
        "answerValue": f"${ans}$",
    }

    steps = [
        {"title": "正四面体可以放在正方体里",
         "content": (r"<p>取正方体 $(\pm k,\pm k,\pm k)$ 中**两两异面**的四个顶点，"
                     r"恰好构成正四面体 —— 本题就取这组坐标：</p>"
                     r"$$A" + sol["math_points"]["A"] + r",\ B" + sol["math_points"]["B"]
                     + r",\ C" + sol["math_points"]["C"] + r",\ D" + sol["math_points"]["D"] + r"$$"
                     r"<p>这组坐标下棱长恰为 $" + v["a"] + r"$（整数，便于手算）。</p>")},
        {"title": "体积用混合积算",
         "content": (r"<p>四面体体积 $V = \dfrac16\left|"
                     r"(\overrightarrow{AB}\times\overrightarrow{AC})\cdot\overrightarrow{AD}"
                     r"\right|$ —— 用坐标直接算，不必先求高。</p>"
                     r"<p>得到 $V = " + ans + r"$。</p>"
                     r"<p>也可以反过来用公式 $V = \dfrac{a^3}{6\sqrt2}$ 核对，两者一致。</p>")},
        {"title": "高与两个球",
         "content": (r"<p>体积 $V = " + ans + r"$，高 $h = " + v["h"] + r"$"
                     r"（可由 $h = a\sqrt{2/3}$ 得到）。</p>"
                     r"<p>外接球半径 $R = " + v["R"] + r"$，内切球半径 $r = " + v["r"] + r"$。</p>"
                     r"<p>这三个量满足 $R = 3r$，且 $h = R + r$ ——"
                     r"**球心在高上，把高分成了 $R:r = 3:1$**。"
                     r"这是正四面体的一个漂亮性质，可以直接用来验算。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "model": model, "_answer": ans}


# =====================================================================
# 新增题型 8：正三棱柱的体积与侧面积
# =====================================================================
def build_prism_data(edge=2, height=2) -> dict:
    """正三棱柱 ABC-A1B1C1（底面边长 a、高 h）：底面积、体积、侧面积。"""
    sol = gk.solve_triangular_prism(edge=edge, height=height, scale=1.6)
    v, ans = sol["vals"], sol["answer_latex"]
    topo = bodies.prism(bottom=("A", "B", "C"), top=("A1", "B1", "C1"))
    center = _centroid(sol["three_points"])

    model = {
        "target": center,
        "initialCamera": [5, 4, 5],
        "points": sol["three_points"],
        "spheres": topo["spheres"],
        "edges": topo["edges"],
        "elements": {
            "Base_ABC": {"type": "plane", "pts": ["A", "B", "C"]},
            "Edge_AB": {"type": "line", "a": "A", "b": "B", "color": "emphasis",
                        "depthTest": False},
            "Height_AA1": {"type": "line", "a": "A", "b": "A1", "color": "normal",
                           "depthTest": False},
            "Measure_AB": {"type": "measure", "a": "A", "b": "B", "label": str(edge)},
            "Measure_AA1": {"type": "measure", "a": "A", "b": "A1", "label": str(height)},
            "Axis": {"type": "axes", "size": 2.6},
        },
    }

    lesson = {
        "language": "zh-CN", "meta": "交互解题 · 棱柱体积",
        "title": f"正三棱柱ABC-A₁B₁C₁的底面边长为{v['a']}，高为{v['h']}，求它的体积与侧面积",
        "answerLabel": "正三棱柱的体积",
        "answerValue": f"${ans}$",
    }

    steps = [
        {"title": "先求底面积",
         "content": (r"<p>底面是边长为 $" + v["a"] + r"$ 的正三角形，面积为</p>"
                     r"<p>$$S_{\text{底}} = \dfrac{\sqrt3}{4}a^2 = " + v["base_area"] + r"$$</p>"
                     r"<p>这是初中就学过的正三角形面积公式，这里只是把 $a$ 代进去。</p>")},
        {"title": "棱柱体积 = 底面积 × 高",
         "content": (r"<p>棱柱的体积与柱体一样：$V = S_{\text{底}} \cdot h$。"
                     r"注意这里的 $h$ 是**两底面之间的距离**（侧棱长），"
                     r"不是斜高。</p>"
                     r"<p>$$V = " + v["base_area"] + r" \times " + v["h"] + r" = " + ans + r"$$</p>")},
        {"title": "侧面积与「高」的辨析",
         "content": (r"<p>侧面是三个 $a \times h$ 的矩形，所以</p>"
                     r"<p>$$S_{\text{侧}} = 3ah = " + v["lateral"] + r"$$</p>"
                     r"<p>而体积 $V = " + ans + r"$（上面已算出）。</p>"
                     r"<p>凡是这类题，**先分清求的是体积、侧面积还是表面积**："
                     r"侧面积不含两个底面，表面积要把两个底面加上。"
                     r"把棱长与高改一改，三个量会同时变，但公式不变。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "model": model, "_answer": ans}


PROBLEMS = {
    "pyramid": build_data,
    "cube": build_cube_data,
    "box": build_box_volume_data,
    "distance": build_distance_data,
    "dihedral": build_dihedral_data,
    "skew": build_skew_data,
    "tetra": build_tetra_data,
    "prism": build_prism_data,
}


def _prepare(key, data):
    """自检：最终步骤展示的答案必须等于答案卡（同为 kernel 计算结果）。"""
    final_step = data["steps"][-1]["content"]
    assert data["_answer"] in final_step, "最终步骤未包含计算所得答案"
    data.pop("_answer", None)
    return data


def _random_build(rng):
    return "random", build_random_data(rng.randint(0, 10 ** 6))


def main(argv=None):
    # 统一入口（edulab/shared/skillkit.py）：
    #   python generate.py list | all <目录> | random [seed] [输出] | pyramid|cube|box [输出]
    return cli(PROBLEMS, doc=__doc__, prepare=_prepare, random_build=_random_build,
               template_name="lesson.html", token=PLACEHOLDER,
               index="立体几何 · 建系向量法 · 交互课件", argv=argv or sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
