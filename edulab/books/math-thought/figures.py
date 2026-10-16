# -*- coding: utf-8 -*-
"""
figures.py — 《数学思想：从计数到无穷》的插图定义。

全部用 edulab/shared/viz/viz.js 的**声明式图形语法**表达：
    { theme, view, layers:[{geom,...}], steps:[...] }
不写任何绘制代码；需要精确值的地方由 Python 算好（如 √2 的数位、单位圆坐标）。

几何约定：每个图自己给 view.xRange / view.yRange（世界坐标），图元按世界坐标摆放；
文字标注由引擎负责像素偏移与靠边翻转，所以不会出框、不会叠字。

自检：python figures.py
"""
import json
import math
import random
from fractions import Fraction

# 纸感主题的语义色（与 viz.js 的 THEMES.paper 保持一致）
INK = "#1f1b16"
DIM = "#7d756a"
ACCENT = "#b45309"
ACCENT2 = "#6d28d9"
GOOD = "#15803d"
BAD = "#b91c1c"
TEAL = "#0f766e"
RULE = "#e7e0d5"

PAPER = "paper"


# ---------------- 小工具 ----------------
def _when(k):
    """只在第 k 步之后显示的图层条件（steps 里的字段会并进场景状态）。"""
    return ("k", k)


def card(x, y, w, h, label, sub, edge, fill="#ffffff", fid=None, on=True):
    return {"id": fid or f"c{int(x*10)}", "x": x, "y": y, "w": w, "h": h,
            "label": label, "sub": sub, "edge": edge, "fill": fill, "on": on}


def text(x, y, t, align="left", size=11, color=INK, dx=0, dy=0, weight="bold"):
    return {"geom": "text", "x": x, "y": y, "text": t, "align": align,
            "size": size, "color": color, "dx": dx, "dy": dy, "weight": weight}


def note(x, y, t, color=DIM, align="left", size=10):
    return {"geom": "text", "x": x, "y": y, "text": t, "align": align,
            "size": size, "color": color, "dy": 0}


# =====================================================================
# 第 1 章插图
# =====================================================================
def fig_crisis():
    """五次扩张的因果链：数系卡片 + 「无解方程」箭头，逐步展开。

    几何要点：卡片做得「宽大于高」（否则在竖长画布上会变成细条）；
    无解方程放在箭头**下方**的一行里，避免挤在卡片间隙中重叠。
    """
    systems = [
        ("ℕ", "自然数", "1, 2, 3, …", "#78716c"),
        ("ℤ", "整数", "＋ 负数", ACCENT),
        ("ℚ", "有理数", "＋ 分数", "#a16207"),
        ("ℝ", "实数", "＋ 无理数", TEAL),
        ("ℂ", "复数", "＋ 虚数", ACCENT2),
    ]
    eqs = ["x + 5 = 2", "2x = 3", "x² = 2", "x² = −1"]
    CW, CH, GAP = 1.46, 0.78, 2.46
    X0, Y0 = 0.32, 2.62

    nodes = [card(X0 + i * GAP, Y0, CW, CH, f"{s[0]}  {s[1]}", s[2], s[3], fid=f"s{i}")
             for i, s in enumerate(systems)]

    layers = [
        {"geom": "text", "x": X0, "y": Y0 + CH + 0.30, "text": "五个数系，五次扩张",
         "align": "left", "size": 12, "color": INK, "dy": 0},
        {"geom": "text", "x": X0, "y": 1.70,
         "text": "红色方程 = 在这个数系里无解；箭头指向「为救它而造出的新数系」",
         "align": "left", "size": 10, "color": DIM, "dy": 0, "weight": "normal"},
    ]
    # 系统卡片：第 i+1 步之后出现
    for i in range(len(systems)):
        layers.append({"geom": "card", "when": f"k >= {i + 1}", "data": [nodes[i]]})
    # 箭头 + 无解方程（方程放在箭头下方一行，不与卡片抢位）
    for i in range(len(eqs)):
        layers.append({"geom": "arrow", "nodes": nodes, "width": 2.0, "stroke": BAD,
                       "when": f"k >= {i + 2}",
                       "data": [{"from": f"s{i}", "to": f"s{i+1}", "color": BAD, "width": 2.0}]})
        cx = X0 + i * GAP + CW + (GAP - CW) / 2
        layers.append({"geom": "text", "when": f"k >= {i + 2}", "x": cx, "y": 2.12,
                       "text": eqs[i], "align": "center", "size": 10, "color": BAD, "dy": 0})
        layers.append({"geom": "text", "when": f"k >= {i + 2}", "x": cx, "y": 1.96,
                       "text": "无解", "align": "center", "size": 9, "color": BAD, "dy": 0,
                       "weight": "normal"})
    # 结尾标注
    layers.append({"geom": "text", "x": X0 + 4 * GAP + CW + 0.12, "y": Y0 + CH / 2,
                   "text": "ℂ 代数封闭\n扩张到此结束", "align": "left", "size": 10, "color": GOOD, "dy": 0,
                   "when": "k >= 6"})
    steps = [
        {"k": 1, "note": "起点：只有自然数 ℕ = {1, 2, 3, …}。它能数清羊群，但做不了减法。"},
        {"k": 2, "note": "x + 5 = 2 无解 → 造出负数，得到整数 ℤ。代价：失去「越多越好」的直觉。"},
        {"k": 3, "note": "2x = 3 无解 → 造出分数，得到有理数 ℚ。代价：稠密到没有「下一个数」。"},
        {"k": 4, "note": "x² = 2 无解 → 造出无理数，得到实数 ℝ。代价：不可数（这是最贵的一次）。"},
        {"k": 5, "note": "x² = −1 无解 → 造出虚数，得到复数 ℂ。代价：失去大小顺序。"},
        {"k": 6, "note": "ℂ 代数封闭——任何复系数多项式都有根。到这里，扩张的链条终于停下。"},
    ]
    return {"theme": PAPER, "view": {"xRange": [0, 14.3], "yRange": [1.52, 3.86],
                                     "pad": {"l": 16, "r": 16, "b": 12, "t": 16}},
            "layers": layers, "steps": steps}


def fig_sqrt2():
    """√2 不是有理数：左边是几何事实，右边是反证法的五步。"""
    root2 = math.sqrt(2)
    digits = "1.4142135623730951"

    # 单位正方形 + 对角线
    sq = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
    diag = [[0, 0], [1, 1]]
    circle_pts = [[0.5 + 0.5 * math.cos(2 * math.pi * i / 120),
                   0.5 + 0.5 * math.sin(2 * math.pi * i / 120)] for i in range(121)]

    lines = [
        {"geom": "line", "data": sq, "stroke": INK, "width": 2.4},
        {"geom": "line", "data": diag, "stroke": BAD, "width": 2.8},
        {"geom": "text", "x": 0.5, "y": -0.16, "text": "1", "align": "center", "size": 12, "color": INK, "dy": 0},
        {"geom": "text", "x": 1.06, "y": 0.5, "text": "1", "align": "left", "size": 12, "color": INK, "dy": 0},
        {"geom": "text", "x": 0.42, "y": 0.60, "text": "√2 ?", "align": "center", "size": 12, "color": BAD, "dy": 0},
        {"geom": "text", "x": 0.5, "y": 1.16, "text": "边长 1 的正方形", "align": "center", "size": 11, "color": DIM, "dy": 0},
    ]

    proof = [
        ("假设", "设 √2 = p / q，其中 p、q 是互质的整数（已约到最简）", INK),
        ("平方", "两边平方：2 = p² / q²，即 p² = 2q²", INK),
        ("推 p", "p² 是偶数 ⟹ p 必是偶数（奇数的平方是奇数）", ACCENT),
        ("代回", "设 p = 2m，则 4m² = 2q² ⟹ q² = 2m² ⟹ q 也是偶数", ACCENT),
        ("矛盾", "p 和 q 都是偶数，与「互质」矛盾 ⟹ √2 不是有理数", BAD),
    ]
    layers = list(lines)
    layers.append({"geom": "text", "x": 3.4, "y": 1.32, "text": "反证法：五步推出矛盾",
                   "align": "left", "size": 12, "color": INK, "dy": 0})
    for i, (t, d, col) in enumerate(proof):
        y = 1.02 - i * 0.29
        layers.append({"geom": "glyph", "when": f"k >= {i + 1}",
                       "size": 0.20, "fill": col, "stroke": False,
                       "data": [{"x": 3.40, "y": y - 0.02, "label": ""}]})
        layers.append({"geom": "text", "when": f"k >= {i + 1}",
                       "x": 3.70, "y": y, "text": f"{t}　{d}", "align": "left", "size": 10.5,
                       "color": col, "dy": 0, "weight": "normal"})
    layers.append({"geom": "text", "x": 3.40, "y": -0.24,
                   "text": f"√2 = {digits[:6]}…  （无限不循环 ⟹ 不是分数）",
                   "align": "left", "size": 10.5, "color": DIM, "dy": 0, "weight": "normal"})
    steps = [{"k": i + 1, "note": f"第 {i+1} 步：{t} —— {d}"} for i, (t, d, _) in enumerate(proof)]
    return {"theme": PAPER, "view": {"xRange": [-0.15, 8.6], "yRange": [-0.36, 1.42],
                                     "pad": {"l": 16, "r": 16, "b": 12, "t": 16},
                                     "equalAspect": True},
            "layers": layers, "steps": steps}


def fig_complex():
    """复数平面：乘以 i = 逆时针旋转 90°。"""
    R = 1.0
    circle = [[R * math.cos(2 * math.pi * i / 160), R * math.sin(2 * math.pi * i / 160)] for i in range(161)]
    pts = [("1", 1, 0, ACCENT), ("i", 0, 1, ACCENT2), ("−1", -1, 0, BAD), ("−i", 0, -1, TEAL)]
    layers = [
        {"geom": "axis", "xRange": [-1.5, 2.9], "yRange": [-1.4, 1.4],
         "xlab": "实部 Re", "ylab": "虚部 Im", "xticks": [-1, 0, 1, 2], "yticks": [-1, 0, 1]},
        {"geom": "line", "data": circle, "stroke": RULE, "width": 2.0},
    ]
    for name, x, y, col in pts:
        layers.append({"geom": "point", "data": [{"x": x, "y": y, "r": 7, "fill": col}], "fill": col})
        layers.append({"geom": "text", "x": x, "y": y, "text": name, "align": "center",
                       "size": 12, "color": col, "dx": 18 if x >= 0 else -18, "dy": -14 if y >= 0 else 14})
    # 旋转箭头：1 → i → −1 → −i
    seq = [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 0)]
    for i in range(4):
        a, b = seq[i], seq[i + 1]
        mx, my = (a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5
        k = 0.34
        layers.append({"geom": "point", "data": [{"x": mx + (a[1] + b[1]) * 0.0 + (-a[1]) * k * 2,
                                                  "y": my + (a[0]) * k * 2, "r": 3.0, "fill": DIM}]})
    layers += [
        {"geom": "text", "x": 0.62, "y": 0.62, "text": "× i", "align": "center", "size": 11, "color": DIM, "dy": 0},
        {"geom": "text", "x": 1.35, "y": 0.55, "text": "每乘一次 i，\n就逆时针转 90°", "align": "left",
         "size": 11.5, "color": INK, "dy": 0},
        {"geom": "text", "x": 1.35, "y": -0.05, "text": "转两次回到相反方向：\ni² = −1", "align": "left",
         "size": 11.5, "color": ACCENT2, "dy": 0},
        {"geom": "text", "x": 1.35, "y": -0.72,
         "text": "「虚数」不虚——\n它是平面上的旋转。", "align": "left",
         "size": 11.5, "color": GOOD, "dy": 0},
        {"geom": "text", "x": -1.5, "y": -1.28, "text": "方程 x² + 1 = 0 在 ℝ 上无解，在 ℂ 上有两个解 ±i",
         "align": "left", "size": 10.5, "color": DIM, "dy": 0, "weight": "normal"},
    ]
    return {"theme": PAPER, "view": {"xRange": [-1.6, 3.5], "yRange": [-1.42, 1.42],
                                     "pad": {"l": 46, "r": 14, "b": 30, "t": 14}, "equalAspect": True},
            "layers": layers}


def fig_nesting():
    """数系嵌套：ℕ ⊂ ℤ ⊂ ℚ ⊂ ℝ ⊂ ℂ ⊂ ℍ。

    布局要点：**不要用同心矩形**——同心图形共享中心，标签必然叠在一起。
    改用「阶梯式嵌套」：每层只从**左上角**内缩，于是每层都留下一条可见的 L 形带，
    名称写在带内、代价写在右侧，彼此互不遮挡。
    """
    rings = [
        ("ℕ  自然数", "#78716c", ""),
        ("ℤ  整数", ACCENT, "放弃「越多越好」的直觉"),
        ("ℚ  有理数", "#a16207", "放弃「有下一个数」"),
        ("ℝ  实数", TEAL, "放弃「可数性」"),
        ("ℂ  复数", ACCENT2, "放弃「大小顺序」"),
        ("ℍ  四元数", "#be123c", "放弃「交换律」ab ≠ ba"),
    ]
    X0, Y0, XMAX, YTOP = 0.35, 0.42, 7.10, 3.55
    DX, DY = 0.58, 0.46
    layers = [{"geom": "text", "x": X0, "y": YTOP + 0.26, "text": "越往里，集合越大",
               "align": "left", "size": 12, "color": INK, "dy": 0}]
    for i, (name, col, cost) in enumerate(rings):
        x_lo = X0 + DX * i
        y_hi = YTOP - DY * i
        layers.append({"geom": "region", "when": f"k >= {i + 1}",
                       "x": [x_lo, XMAX], "y": [Y0, y_hi],
                       "fill": "#ffffff", "outline": True, "stroke": col, "width": 1.9})
    for i, (name, col, cost) in enumerate(rings):
        yl = YTOP - DY * i - DY / 2
        layers.append({"geom": "text", "when": f"k >= {i + 1}",
                       "x": X0 + DX * i + 0.12, "y": yl, "text": name, "align": "left",
                       "size": 11, "color": col, "dy": 0})
        if cost:
            layers.append({"geom": "text", "when": f"k >= {i + 1}",
                           "x": XMAX + 0.18, "y": yl, "text": "代价：" + cost, "align": "left",
                           "size": 10.5, "color": DIM, "dy": 0, "weight": "normal"})
    layers.append({"geom": "text", "x": X0, "y": Y0 - 0.26,
                   "text": "每往外扩一层，能解的方程更多——但都要少一条原本理所当然的运算律。",
                   "align": "left", "size": 10.5, "color": INK, "dy": 0, "weight": "normal"})
    steps = [{"k": i + 1, "note": f"第 {i+1} 层：{name}" + (f" —— 代价：{cost}" if cost else "（起点）")}
             for i, (name, _, cost) in enumerate(rings)]
    return {"theme": PAPER, "view": {"xRange": [X0 - 0.15, XMAX + 2.55], "yRange": [Y0 - 0.45, YTOP + 0.45],
                                     "pad": {"l": 12, "r": 12, "b": 12, "t": 12}},
            "layers": layers, "steps": steps}


def fig_timeline():
    """五次扩张的时间轴（上下交替标注；已验证标签不重叠、不出框）。"""
    events = [
        (-6.0, "公元前 6 世纪\n发现 √2 不可通约", BAD, "up"),
        (-3.5, "公元前 3 世纪\n欧几里得《几何原本》", ACCENT, "down"),
        (0.0, "公元 7 世纪\n印度正式使用负数", ACCENT, "up"),
        (3.5, "1545 年\n卡尔达诺：出现虚数", ACCENT2, "down"),
        (6.5, "1799 年\n高斯：代数基本定理", GOOD, "up"),
        (9.0, "1843 年\n哈密顿：四元数", "#be123c", "down"),
    ]
    layers = [
        {"geom": "line", "data": [[-7.2, 0], [10.2, 0]], "stroke": RULE, "width": 3.2},
        {"geom": "text", "x": -7.2, "y": -0.72, "text": "公元前 6 世纪", "align": "left", "size": 9.5,
         "color": DIM, "dy": 0, "weight": "normal"},
        {"geom": "text", "x": 10.2, "y": -0.72, "text": "19 世纪", "align": "right", "size": 9.5,
         "color": DIM, "dy": 0, "weight": "normal"},
    ]
    for t, label, col, side in events:
        layers.append({"geom": "point", "data": [{"x": t, "y": 0, "r": 6, "fill": col}], "fill": col})
        up = side == "up"
        layers.append({"geom": "line", "data": [[t, 0], [t, 0.16 if up else -0.16]],
                       "stroke": RULE, "width": 1.4})
        layers.append({"geom": "text", "x": t, "y": (0.32 if up else -0.32), "text": label,
                       "align": "center", "size": 9.5, "color": col, "dy": 0, "weight": "bold"})
    layers.append({"geom": "text", "x": 1.5, "y": 0.86,
                   "text": "第三次扩张（无理数）拖了两千年——因为它要的不是新符号，而是重新定义「数」",
                   "align": "center", "size": 10.5, "color": INK, "dy": 0, "weight": "normal"})
    return {"theme": PAPER, "view": {"xRange": [-7.6, 10.6], "yRange": [-0.98, 1.06],
                                     "pad": {"l": 12, "r": 12, "b": 10, "t": 10}},
            "layers": layers}


# =====================================================================
# 第 2 章插图（无穷）
# =====================================================================
def fig_zeno():
    """芝诺悖论：每次走剩下的一半，永远到不了终点。

    画法：一条 0→1 的距离线 + 逐次累积点的**刻度线** + 每段长度的标签。
    （不要用方块表示段——段越来越窄，方块会叠成一块实心。）
    """
    n = 7
    cums, seg = [], 1.0
    for i in range(n):
        seg /= 2
        cums.append(1.0 - seg)          # 累积到达位置：1-1/2, 1-1/4, …
    segs = [0.5 / (2 ** i) for i in range(n)]   # 每段长度：1/2, 1/4, 1/8, …

    layers = [
        {"geom": "line", "data": [[0, 0], [1, 0]], "stroke": INK, "width": 3.0},
        {"geom": "point", "data": [{"x": 0, "y": 0, "r": 6, "fill": INK}], "fill": INK},
        {"geom": "point", "data": [{"x": 1.0, "y": 0, "r": 7, "fill": BAD}], "fill": BAD},
        {"geom": "text", "x": 1.0, "y": 0, "text": "终点", "align": "center", "size": 11,
         "color": BAD, "dy": -18},
        {"geom": "text", "x": 0, "y": 0, "text": "起点", "align": "center", "size": 10,
         "color": DIM, "dy": 18, "weight": "normal"},
    ]
    prev = 0.0
    for i, c in enumerate(cums):
        layers.append({"geom": "line", "when": f"k >= {i + 1}",
                       "data": [[c, -0.055], [c, 0.055]], "stroke": ACCENT if i % 2 == 0 else ACCENT2,
                       "width": 2.0})
        if i < 4:                        # 只有前 4 段宽到能放标签
            layers.append({"geom": "text", "when": f"k >= {i + 1}",
                           "x": (prev + c) / 2, "y": 0.13 + (0.11 if i % 2 else 0),
                           "text": f"1/{2**(i+1)}", "align": "center", "size": 9.5,
                           "color": ACCENT if i % 2 == 0 else ACCENT2, "dy": 0, "weight": "normal"})
        prev = c
    layers.append({"geom": "text", "x": 0.97, "y": 0.36,
                   "text": "…（越来越小）", "align": "right", "size": 9, "color": DIM,
                   "dy": 0, "weight": "normal"})
    layers.append({"geom": "text", "x": 0.5, "y": -0.30,
                   "text": "1/2 + 1/4 + 1/8 + … 有无穷多项，但总和恰好 = 1",
                   "align": "center", "size": 10.5, "color": INK, "dy": 0, "weight": "normal"})
    steps = []
    acc = 0.0
    for i in range(n):
        acc += segs[i]
        steps.append({"k": i + 1,
                      "note": f"第 {i+1} 步走剩下的 1/2，累计走过 {acc:.4f}（离终点还差 {1-acc:.4f}）"})
    return {"theme": PAPER, "view": {"xRange": [-0.08, 1.08], "yRange": [-0.40, 0.44],
                                     "pad": {"l": 14, "r": 14, "b": 12, "t": 12}},
            "layers": layers, "steps": steps}


def fig_cardinality():
    """可数 vs 不可数：能不能和自然数一一配对。"""
    layers = [
        {"geom": "text", "x": 0, "y": 0.86, "text": "能配对 → 可数", "align": "left", "size": 11.5,
         "color": GOOD, "dy": 0},
        {"geom": "text", "x": 5.4, "y": 0.86, "text": "配不完 → 不可数", "align": "left", "size": 11.5,
         "color": BAD, "dy": 0},
        # 左：ℕ 与偶数 一一配对
        {"geom": "text", "x": 0, "y": 0.52, "text": "ℕ  1  2  3  4  5 …", "align": "left", "size": 11,
         "color": INK, "dy": 0, "weight": "normal"},
        {"geom": "text", "x": 0, "y": 0.28, "text": "↕  ↕  ↕  ↕  ↕", "align": "left", "size": 11,
         "color": DIM, "dy": 0, "weight": "normal"},
        {"geom": "text", "x": 0, "y": 0.04, "text": "偶数 2  4  6  8  10 …", "align": "left", "size": 11,
         "color": GOOD, "dy": 0, "weight": "normal"},
        {"geom": "text", "x": 0, "y": -0.24, "text": "「整体」和「部分」一样多。", "align": "left",
         "size": 10, "color": DIM, "dy": 0, "weight": "normal"},
        # 右：实数无法列表
        {"geom": "text", "x": 5.4, "y": 0.52, "text": "0.1 2 3 4 5 …", "align": "left", "size": 11,
         "color": INK, "dy": 0, "weight": "normal"},
        {"geom": "text", "x": 5.4, "y": 0.34, "text": "0.9 8 7 6 5 …", "align": "left", "size": 11,
         "color": INK, "dy": 0, "weight": "normal"},
        {"geom": "text", "x": 5.4, "y": 0.16, "text": "0.4 4 4 4 4 …", "align": "left", "size": 11,
         "color": INK, "dy": 0, "weight": "normal"},
        {"geom": "text", "x": 5.4, "y": -0.02, "text": "0.7 1 8 2 8 …", "align": "left", "size": 11,
         "color": INK, "dy": 0, "weight": "normal"},
        {"geom": "text", "x": 5.4, "y": -0.30, "text": "对角线取反 → 造出一个不在表里的数 → 矛盾", "align": "left",
         "size": 10, "color": BAD, "dy": 0, "weight": "normal"},
    ]
    return {"theme": PAPER, "view": {"xRange": [-0.2, 10.2], "yRange": [-0.46, 1.0],
                                     "pad": {"l": 12, "r": 12, "b": 10, "t": 10}},
            "layers": layers}


def fig_hilbert():
    """希尔伯特旅馆：无穷个房间都住满了，还能再住进无穷个客人。"""
    layers = [
        {"geom": "text", "x": 0, "y": 0.72, "text": "旅馆住满了（每个房间都有人）", "align": "left",
         "size": 11, "color": INK, "dy": 0},
    ]
    n = 9
    for i in range(n):
        col = "#f7f4ee" if i < n - 1 else "#fde8e8"
        layers.append({"geom": "glyph", "size": 0.42, "fill": col, "edge": RULE,
                       "data": [{"x": i * 0.53, "y": 0.20, "label": str(i + 1)}]})
    layers.append({"geom": "text", "x": 0, "y": 0.02, "text": "1   2   3   4   5   6   7   8  …", "align": "left",
                   "size": 10, "color": DIM, "dy": 0, "weight": "normal"})
    layers.append({"geom": "text", "x": 0, "y": -0.22,
                   "text": "新客人来了 → 让 1 号搬到 2 号、2 号搬到 3 号……每个客人都往后挪一间。", "align": "left",
                   "size": 10.5, "color": ACCENT, "dy": 0, "weight": "normal"})
    layers.append({"geom": "text", "x": 0, "y": -0.46,
                   "text": "结果：1 号空出来了。住满的旅馆永远还能再住一个人——甚至无穷个人。", "align": "left",
                   "size": 10.5, "color": GOOD, "dy": 0, "weight": "normal"})
    layers.append({"geom": "text", "x": 0, "y": -0.70,
                   "text": "「无穷」不服从有限世界的直觉。这正是它危险的地方，也是它迷人的地方。", "align": "left",
                   "size": 10.5, "color": INK, "dy": 0, "weight": "normal"})
    return {"theme": PAPER, "view": {"xRange": [-0.05, 5.0], "yRange": [-0.86, 0.88],
                                     "pad": {"l": 12, "r": 12, "b": 10, "t": 10},
                                     "equalAspect": True},
            "layers": layers}


# =====================================================================
# 第 3 章插图（证明）
# =====================================================================
def fig_euclid():
    """公理 → 定理：证明是可追溯的推导链。"""
    layers = [
        {"geom": "text", "x": 0, "y": 0.92, "text": "五条公设（不证自明）", "align": "left", "size": 11, "color": ACCENT, "dy": 0},
    ]
    axioms = ["两点确定一条直线", "线段可任意延长", "可作已知圆心的圆", "直角都相等", "平行公设"]
    for i, a in enumerate(axioms):
        layers.append({"geom": "card",
                       "data": [card(0.0, 0.58 - i * 0.20, 2.6, 0.16, a, "", ACCENT, "#fffdf8", fid=f"ax{i}")]})
    layers.append({"geom": "text", "x": 3.5, "y": 0.92, "text": "推出定理（层层追溯）", "align": "left",
                   "size": 11, "color": GOOD, "dy": 0})
    thms = ["两直线平行，同位角相等",
            "三角形内角和 = 180°",
            "勾股定理 a² + b² = c²"]
    for i, t in enumerate(thms):
        layers.append({"geom": "card",
                       "data": [card(3.5, 0.52 - i * 0.30, 4.6, 0.24, t, "", GOOD, "#ffffff", fid=f"th{i}")]})
    layers.append({"geom": "text", "x": 0, "y": -0.30,
                   "text": "每一条定理都能一步步回溯到公设。这就是「证明」的含义：\n"
                           "把一个断言，接回到所有人都同意的那几条起点上。", "align": "left",
                   "size": 10.5, "color": INK, "dy": 0, "weight": "normal"})
    layers.append({"geom": "text", "x": 0, "y": -0.70,
                   "text": "欧几里得的贡献不是发现了多少定理，而是发明了「证明」这个动作本身。", "align": "left",
                   "size": 10.5, "color": DIM, "dy": 0, "weight": "normal"})
    return {"theme": PAPER, "view": {"xRange": [-0.12, 8.3], "yRange": [-0.86, 1.06],
                                     "pad": {"l": 12, "r": 12, "b": 10, "t": 10}},
            "layers": layers}


def fig_induction():
    """数学归纳法：多米诺骨牌。第一步倒 + 每块能带倒下一块 = 全部倒下。"""
    layers = [
        {"geom": "text", "x": 0, "y": 1.02, "text": "① 基础：第 1 块倒下", "align": "left", "size": 11, "color": ACCENT, "dy": 0},
        {"geom": "text", "x": 0, "y": 0.72, "text": "② 归纳：若第 k 块倒下，则第 k+1 块必倒", "align": "left",
         "size": 11, "color": ACCENT2, "dy": 0},
        {"geom": "text", "x": 0, "y": 0.42, "text": "⟹ 所有骨牌都会倒（对一切 n 成立）", "align": "left",
         "size": 11.5, "color": GOOD, "dy": 0},
    ]
    n = 8
    for i in range(n):
        x = 0.15 + i * 0.72
        tilt = 0.34 if i < 5 else 0.0
        layers.append({"geom": "card",
                       "data": [{"id": f"d{i}", "x": x, "y": 0.0, "w": 0.13, "h": 0.30,
                                 "label": "", "sub": "", "fill": ACCENT if i == 0 else "#ffffff",
                                 "edge": ACCENT if i < 5 else RULE, "on": i < 5}]})
        layers.append({"geom": "text", "x": x + 0.06, "y": -0.10, "text": str(i + 1), "align": "center",
                       "size": 9, "color": DIM, "dy": 0, "weight": "normal"})
    layers.append({"geom": "text", "x": 0.15, "y": -0.40,
                   "text": "为什么这能证明「无穷多个情形」？因为链条一旦不中断，就没有任何一块能「躲过去」。",
                   "align": "left", "size": 10.5, "color": INK, "dy": 0, "weight": "normal"})
    layers.append({"geom": "text", "x": 0.15, "y": -0.66,
                   "text": "归纳法把「无穷次检验」压缩成「两次检查」——这是数学里最省力的证明机器。",
                   "align": "left", "size": 10.5, "color": DIM, "dy": 0, "weight": "normal"})
    return {"theme": PAPER, "view": {"xRange": [0.0, 6.1], "yRange": [-0.82, 1.16],
                                     "pad": {"l": 12, "r": 12, "b": 10, "t": 10}},
            "layers": layers}


def fig_godel():
    """哥德尔不完备定理：系统无法证明自身的一致性（自指）。"""
    layers = [
        {"geom": "region", "x": [0.0, 6.4], "y": [0.30, 1.45], "fill": "#f7f4ee", "outline": True,
         "stroke": RULE, "label": ""},
        {"geom": "text", "x": 0.25, "y": 1.26, "text": "能证明的命题", "align": "left", "size": 11.5,
         "color": GOOD, "dy": 0},
        {"geom": "text", "x": 0.25, "y": 0.60, "text": "「本命题不可证」", "align": "left", "size": 11,
         "color": BAD, "dy": 0},
        {"geom": "text", "x": 3.6, "y": 0.60, "text": "↑ 这句既不能证真，也不能证假", "align": "left",
         "size": 10.5, "color": BAD, "dy": 0, "weight": "normal"},
        {"geom": "text", "x": 0.0, "y": 0.02,
         "text": "把它写成数学命题 G：「G 在本系统中不可证明」。", "align": "left", "size": 11,
         "color": INK, "dy": 0},
        {"geom": "text", "x": 0.0, "y": -0.26,
         "text": "若 G 可证 → G 说的是真的 → 系统证出了一个假命题（不一致）。", "align": "left",
         "size": 10.5, "color": BAD, "dy": 0, "weight": "normal"},
        {"geom": "text", "x": 0.0, "y": -0.50,
         "text": "若 G 不可证 → G 说的正是事实 → 系统里存在真而不可证的命题（不完备）。", "align": "left",
         "size": 10.5, "color": BAD, "dy": 0, "weight": "normal"},
        {"geom": "text", "x": 0.0, "y": -0.80,
         "text": "结论：任何足够强、又自洽的公理系统，都必然不完备。这不是缺陷，而是逻辑的边界。",
         "align": "left", "size": 11, "color": ACCENT2, "dy": 0},
    ]
    return {"theme": PAPER, "view": {"xRange": [-0.12, 6.7], "yRange": [-0.96, 1.56],
                                     "pad": {"l": 12, "r": 12, "b": 10, "t": 10}},
            "layers": layers}


# =====================================================================
# 汇总
# =====================================================================
# =====================================================================
# ---- 第 4 章插图：变化 —— 从静止到连续 ----
# =====================================================================
def _clip_seg(p0, p1, xr, yr):
    """把线段裁到矩形 xr×yr（Liang–Barsky）。

    割线/切线要画成「贯穿全图」的长线，但校验器要求所有坐标都落在 view 内
    （E5），所以必须先按视窗裁剪，而不是靠渲染端裁。
    """
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0 - xr[0]), (dx, xr[1] - x0),
                 (-dy, y0 - yr[0]), (dy, yr[1] - y0)):
        if p == 0:
            if q < 0:
                return None
            continue
        r = q / p
        if p < 0:
            if r > t1:
                return None
            if r > t0:
                t0 = r
        else:
            if r < t0:
                return None
            if r < t1:
                t1 = r
    return [[x0 + t0 * dx, y0 + t0 * dy], [x0 + t1 * dx, y0 + t1 * dy]]


def fig_instant():
    """瞬时速度的危机：把 Δt 收到 0，Δs 与 Δt 同时归零，比值成了 0/0。

    画法：路程—时间曲线 s = t²，逐步缩短 Δt，每步画一个**斜率三角形**
    （水平虚线 = Δt，竖直虚线 = Δs，斜边 = 割线）。三角形越缩越小，
    最后一步给出 0/0 的结论。
    """
    t0 = 1.15
    hs = [0.90, 0.45, 0.225, 0.1125]
    s = lambda t: t * t                      # noqa: E731
    XMIN, XMAX, YMIN, YMAX = -0.35, 2.75, 0.0, 5.60
    s0 = s(t0)

    layers = [
        {"geom": "axis", "xRange": [XMIN, XMAX], "yRange": [YMIN, YMAX],
         "xlab": "时间 t", "ylab": "路程 s", "xticks": [0, 1, 2], "yticks": [0, 1, 2, 3, 4]},
        {"geom": "line", "fn": "x*x", "from": [0.0, 2.30], "stroke": INK, "width": 2.6},
        {"geom": "point", "data": [{"x": t0, "y": s0, "r": 6.5, "fill": INK}], "fill": INK},
        {"geom": "text", "x": t0, "y": s0, "text": "t₀", "align": "left", "size": 11,
         "color": INK, "dx": 13, "dy": -15, "weight": "normal"},
    ]
    for i, h in enumerate(hs):
        k = i + 1
        col = ACCENT if i % 2 == 0 else ACCENT2
        x2, y2 = t0 + h, s(t0 + h)
        layers += [
            # Δt：水平虚线（四步共起点、逐次变短 → 肉眼可见地「被吃掉」）
            {"geom": "line", "when": f"k >= {k}", "data": [[t0, s0], [x2, s0]],
             "stroke": col, "width": 2.0, "dash": True},
            # Δs：竖直虚线
            {"geom": "line", "when": f"k >= {k}", "data": [[x2, s0], [x2, y2]],
             "stroke": col, "width": 2.0, "dash": True},
            # 割线
            {"geom": "line", "when": f"k >= {k}", "data": [[t0, s0], [x2, y2]],
             "stroke": col, "width": 2.4},
            {"geom": "point", "when": f"k >= {k}",
             "data": [{"x": x2, "y": y2, "r": 4.5, "fill": col}], "fill": col},
        ]
    # 左上角（曲线与割线都到不了）放读数列
    layers.append({"geom": "text", "x": -0.24, "y": 5.15, "text": "逐步缩小 Δt：",
                   "align": "left", "size": 10.5, "color": DIM, "dy": 0, "weight": "normal"})
    for i, h in enumerate(hs):
        col = ACCENT if i % 2 == 0 else ACCENT2
        layers.append({"geom": "text", "when": f"k >= {i + 1}",
                       "x": -0.24, "y": 4.67 - 0.48 * i, "text": f"Δt = {h:g}",
                       "align": "left", "size": 10, "color": col, "dy": 0, "weight": "normal"})
    layers += [
        {"geom": "text", "when": "k >= 5", "x": -0.24, "y": 2.55,
         "text": "Δt → 0 时，Δs 也 → 0", "align": "left", "size": 12.5, "color": BAD, "dy": 0},
        {"geom": "text", "when": "k >= 5", "x": -0.24, "y": 1.95,
         "text": "Δs / Δt = 0 / 0", "align": "left", "size": 15, "color": BAD,
         "dy": 0, "weight": "bold"},
    ]
    steps = [
        {"k": 1, "note": "取一个时刻 t₀，再取它右边一点点的 t₀+Δt。两点连一条割线——它的斜率就是这一段的平均速度。"},
        {"k": 2, "note": "把 Δt 缩短一半。三角形变小，但斜边的**倾斜程度几乎没变**。"},
        {"k": 3, "note": "再缩一半。Δt 与 Δs 都在变小，可斜率稳稳地指向同一个方向。"},
        {"k": 4, "note": "继续缩。到这一步，三角形已经小得快看不见了，斜率却依然明确。"},
        {"k": 5, "note": "若真让 Δt = 0：Δs 也等于 0，式子变成 0/0 ——分子分母同时消失，比值无从谈起。这就是「瞬间的速度」字面上的荒谬。"},
    ]
    return {"theme": PAPER, "view": {"xRange": [XMIN, XMAX], "yRange": [YMIN, YMAX],
                                     "pad": {"l": 46, "r": 16, "b": 34, "t": 14}},
            "layers": layers, "steps": steps}


def fig_secant():
    """牛顿—莱布尼茨的答案：别盯着瞬间，盯住瞬间的**邻域**。

    画法：曲线 y = x² 与定点 A(1,1)，四条割线（Δt 依次减半）绕 A 旋转，
    最后落到切线上；斜率读数 2+Δt → 2。
    """
    f = lambda x: x * x                      # noqa: E731
    XMIN, XMAX, YMIN, YMAX = -0.35, 2.60, -1.80, 6.00
    XR, YR = [XMIN, XMAX], [YMIN, YMAX]
    a = 1.0
    fa = f(a)
    hs = [0.9, 0.5, 0.25, 0.1]

    layers = [
        {"geom": "axis", "xRange": XR, "yRange": YR,
         "xlab": "x", "ylab": "y", "xticks": [0, 1, 2], "yticks": [0, 1, 2, 3, 4, 5]},
        {"geom": "line", "fn": "x*x", "from": [0.0, 2.42], "stroke": INK, "width": 2.6},
        {"geom": "text", "x": 1.95, "y": 5.15, "text": "y = x²", "align": "left",
         "size": 11.5, "color": INK, "dy": 0, "weight": "normal"},
    ]
    # 割线：过 A(1,1)，斜率 m = 2 + Δt（对 y = x² 恰好如此）
    for i, h in enumerate(hs):
        k = i + 1
        m = 2 + h
        seg = _clip_seg((a - 1.6, fa + m * -1.6), (a + 2.2, fa + m * 2.2), XR, YR)
        col = ACCENT if i % 2 == 0 else ACCENT2
        layers += [
            {"geom": "line", "when": f"k >= {k}", "data": seg, "stroke": col, "width": 2.2},
            {"geom": "point", "when": f"k >= {k}",
             "data": [{"x": a + h, "y": f(a + h), "r": 4.5, "fill": col}], "fill": col},
        ]
    # 切线（最后一步，画在最上层）
    mt = 2.0
    tan = _clip_seg((a - 1.6, fa + mt * -1.6), (a + 2.2, fa + mt * 2.2), XR, YR)
    layers += [
        {"geom": "line", "when": "k >= 5", "data": tan, "stroke": TEAL, "width": 3.0},
        {"geom": "point", "data": [{"x": a, "y": fa, "r": 7.0, "fill": INK}], "fill": INK},
        {"geom": "text", "x": a, "y": fa, "text": "A (1, 1)", "align": "right",
         "size": 11, "color": INK, "dx": -14, "dy": 21},
        # 切线标注：放在「所有线都在上方」的右下空区（x>1.1 且 y<0.9）
        {"geom": "line", "when": "k >= 5", "data": [[1.48, 0.72], [1.48, fa + mt * 0.48]],
         "stroke": TEAL, "width": 1.4, "dash": True},
        {"geom": "text", "when": "k >= 5", "x": 1.30, "y": 0.42,
         "text": "切线 y = 2x − 1", "align": "left", "size": 11.5, "color": TEAL, "dy": 0},
    ]
    # 左上空区放斜率读数
    layers.append({"geom": "text", "x": -0.26, "y": 5.60, "text": "斜率 →",
                   "align": "left", "size": 10.5, "color": DIM, "dy": 0, "weight": "normal"})
    for i, h in enumerate(hs):
        col = ACCENT if i % 2 == 0 else ACCENT2
        layers.append({"geom": "text", "when": f"k >= {i + 1}",
                       "x": -0.26, "y": 5.05 - 0.55 * i,
                       "text": f"Δt = {h:g}  →  {2 + h:g}",
                       "align": "left", "size": 10, "color": col, "dy": 0, "weight": "normal"})
    layers.append({"geom": "text", "when": "k >= 5", "x": -0.26, "y": 2.85,
                   "text": "Δt = 0  →  2", "align": "left", "size": 11.5,
                   "color": TEAL, "dy": 0, "weight": "bold"})
    steps = [
        {"k": 1, "note": "先别问「瞬间」。取 A 右边一大步 Δt = 0.9，算这段的平均变化率：斜率 2.9。"},
        {"k": 2, "note": "Δt 减到 0.5，斜率 2.5。割线绕着 A 往下压。"},
        {"k": 3, "note": "Δt = 0.25，斜率 2.25。已经在贴近了。"},
        {"k": 4, "note": "Δt = 0.1，斜率 2.1。割线几乎就是那条切线。"},
        {"k": 5, "note": "斜率 = 2 + Δt，趋势清清楚楚：Δt → 0 时它 → 2。**这就是导数**——不靠「瞬时」这个含糊词，靠邻域的趋势。"},
    ]
    return {"theme": PAPER, "view": {"xRange": XR, "yRange": YR,
                                     "pad": {"l": 52, "r": 16, "b": 34, "t": 16}},
            "layers": layers, "steps": steps}


def fig_berkeley():
    """贝克莱主教 1734 年的反击：那个 h 必须同时「≠ 0」和「= 0」。

    画法：三行算式 + 两条互相矛盾的批注 + 一个「h 段 vs 塌缩成一点」的对照。
    """
    XMIN, XMAX, YMIN, YMAX = -0.30, 6.90, -1.35, 3.90
    XR, YR = [XMIN, XMAX], [YMIN, YMAX]
    PAD = {"l": 16, "r": 16, "b": 24, "t": 16}

    layers = [
        {"geom": "text", "when": "k >= 1", "x": -0.20, "y": 3.45,
         "text": "v = [ f(a+h) − f(a) ] / h", "align": "left", "size": 15, "color": INK, "dy": 0},
        {"geom": "text", "when": "k >= 2", "x": -0.20, "y": 2.55,
         "text": "= [ (a+h)² − a² ] / h = 2a + h", "align": "left", "size": 15,
         "color": INK, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": -0.20, "y": 1.65,
         "text": "= 2a", "align": "left", "size": 15, "color": INK, "dy": 0, "weight": "bold"},
        # 两条互相打架的批注
        {"geom": "text", "when": "k >= 2", "x": 6.80, "y": 3.45,
         "text": "h 在分母上 ⟹ h ≠ 0", "align": "right", "size": 12, "color": GOOD, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": 6.80, "y": 1.65,
         "text": "要 h 消失 ⟹ h = 0", "align": "right", "size": 12, "color": BAD, "dy": 0},
        # 对照图：一个有长度的 h  vs  塌缩成一点
        {"geom": "line", "when": "k >= 4", "data": [[1.40, 0.55], [3.00, 0.55]],
         "stroke": INK, "width": 3.2},
        {"geom": "point", "when": "k >= 4",
         "data": [{"x": 1.40, "y": 0.55, "r": 5, "fill": INK},
                  {"x": 3.00, "y": 0.55, "r": 5, "fill": INK}], "fill": INK},
        {"geom": "text", "when": "k >= 4", "x": 2.20, "y": 0.90, "text": "h",
         "align": "center", "size": 12.5, "color": INK, "dy": 0, "weight": "normal"},
        {"geom": "text", "when": "k >= 4", "x": 2.20, "y": 0.05,
         "text": "有长度，才除得下去", "align": "center", "size": 11,
         "color": GOOD, "dy": 0, "weight": "normal"},
        {"geom": "point", "when": "k >= 5", "data": [{"x": 4.90, "y": 0.55, "r": 7, "fill": BAD}],
         "fill": BAD},
        {"geom": "text", "when": "k >= 5", "x": 4.90, "y": 0.05,
         "text": "h = 0 才会消失", "align": "center", "size": 11, "color": BAD,
         "dy": 0, "weight": "normal"},
        # 「矛盾」另起一行（W1 只认世界坐标，靠 dy 上下分层会被判重叠）
        {"geom": "text", "when": "k >= 5", "x": 3.95, "y": 1.35, "text": "⟹ 矛盾",
         "align": "center", "size": 13, "color": BAD, "dy": 0, "weight": "bold"},
        # 贝克莱原话
        {"geom": "text", "when": "k >= 6", "x": -0.20, "y": -0.55,
         "text": "「这些量在被除掉之前还活着，除掉之后便成了消逝量的鬼魂。」",
         "align": "left", "size": 11.5, "color": DIM, "dy": 0, "weight": "normal"},
        {"geom": "text", "when": "k >= 6", "x": -0.20, "y": -1.02,
         "text": "—— 贝克莱主教《分析学家》1734",
         "align": "left", "size": 10.5, "color": DIM, "dy": 0, "weight": "normal"},
    ]
    steps = [
        {"k": 1, "note": "这是求速度的标准式子。乍看毫无问题——直到你追问每一步的合法性。"},
        {"k": 2, "note": "第二步把分子展开、约掉一个 h。**可 h 在分母上，约之前必须保证 h ≠ 0。**"},
        {"k": 3, "note": "最后令 h = 0 得到 2a。**但刚才不是说 h ≠ 0 吗？** 要它消失，就得等于 0。"},
        {"k": 4, "note": "h 有长度的那一刻，除法成立——但结论还没来。"},
        {"k": 5, "note": "h = 0 的那一刻，结论成立。同一个 h，被要求同时取两个相反的值。"},
        {"k": 6, "note": "1734 年贝克莱挖出的正是这个洞。微积分算得又快又对，却说不清**为什么对**——它缺的是「极限」的严格定义。"},
    ]
    return {"theme": PAPER, "view": {"xRange": XR, "yRange": YR, "pad": PAD},
            "layers": layers, "steps": steps}


def fig_epsilon_delta():
    """ε-δ 修复：不再说「h 是无穷小」，改说「你要多准，我就能给多窄」。

    画法：y = x² 在 x=1 处。对手挑一个容差 ε（水平带），我回一个 δ（竖直带），
    两带的交方框里曲线必须整个落进 ε 带。
    """
    f = lambda x: x * x                      # noqa: E731
    XMIN, XMAX, YMIN, YMAX = -0.40, 2.70, -1.30, 5.50
    XR, YR = [XMIN, XMAX], [YMIN, YMAX]
    a, L = 1.0, 1.0
    eps = 0.7
    delta = math.sqrt(1.0 + eps) - 1.0       # 使 (1+δ)² = 1+ε，上沿恰好贴住
    lo_e, hi_e = L - eps, L + eps
    lo_d, hi_d = a - delta, a + delta

    layers = [
        {"geom": "axis", "xRange": XR, "yRange": YR,
         "xlab": "x", "ylab": "f(x)", "xticks": [0, 1, 2], "yticks": [0, 1, 2, 3, 4, 5]},
        # ε 水平带
        {"geom": "region", "when": "k >= 2", "x": [0.0, 2.34], "y": [lo_e, hi_e],
         "fill": "#e4efe7", "outline": False},
        # δ 竖直带（画在 ε 带之上，交叠处让位给它 —— 下面的交方框会重新点亮）
        {"geom": "region", "when": "k >= 3", "x": [lo_d, hi_d], "y": [-1.18, 4.00],
         "fill": "#ece7f7", "outline": False},
        {"geom": "line", "when": "k >= 2", "data": [[-0.35, lo_e], [2.65, lo_e]],
         "stroke": GOOD, "width": 1.8, "dash": True},
        {"geom": "line", "when": "k >= 2", "data": [[-0.35, hi_e], [2.65, hi_e]],
         "stroke": GOOD, "width": 1.8, "dash": True},
        {"geom": "line", "when": "k >= 3", "data": [[lo_d, -1.18], [lo_d, 4.00]],
         "stroke": ACCENT2, "width": 1.8, "dash": True},
        {"geom": "line", "when": "k >= 3", "data": [[hi_d, -1.18], [hi_d, 4.00]],
         "stroke": ACCENT2, "width": 1.8, "dash": True},
        # 交方框：曲线必须整个落在里面才合格
        {"geom": "region", "when": "k >= 4", "x": [lo_d, hi_d], "y": [lo_e, hi_e],
         "fill": "#ffffff", "outline": True, "stroke": BAD, "width": 2.0, "dash": True},
        {"geom": "line", "fn": "x*x", "from": [0.0, 2.34], "stroke": INK, "width": 2.6},
        {"geom": "point", "data": [{"x": a, "y": L, "r": 7.0, "fill": INK}], "fill": INK},
        {"geom": "text", "x": -0.33, "y": 1.00, "text": "± ε", "align": "left",
         "size": 12, "color": GOOD, "dy": 0, "weight": "bold"},
        {"geom": "text", "when": "k >= 3", "x": 1.00, "y": -0.88, "text": "δ",
         "align": "center", "size": 12, "color": ACCENT2, "dy": 0, "weight": "bold"},
        {"geom": "text", "x": 1.55, "y": 1.00, "text": "f(1) = 1", "align": "left",
         "size": 10.5, "color": INK, "dy": 0, "weight": "normal"},
        {"geom": "text", "when": "k >= 5", "x": -0.33, "y": 5.05,
         "text": "∀ε > 0  ∃δ > 0 ： |x − 1| < δ ⟹ |f(x) − 1| < ε",
         "align": "left", "size": 13, "color": TEAL, "dy": 0},
    ]
    steps = [
        {"k": 1, "note": "先看要逼近的点：x = 1 处 f(1) = 1。"},
        {"k": 2, "note": "对手先出题——挑一个容差 ε，说「你的输出离 1 不许超过这么多」。绿色水平带就是他的底线。"},
        {"k": 3, "note": "我再回题——给出一个 δ，把 x 限制在 1 附近的紫色竖带里。δ 是**我给的**，可以比 ε 小。"},
        {"k": 4, "note": "两带的交方框：只要曲线在这个框里从左穿到右**全程不越出绿带**，这一轮就算我赢。"},
        {"k": 5, "note": "把话说成「无论你挑多小的 ε，我总能给出一个 δ 顶住」——**这就是极限的定义**。没有无穷小，只有任意小；没有「鬼魂」，只有可检验的挑战与应战。"},
    ]
    return {"theme": PAPER, "view": {"xRange": XR, "yRange": YR,
                                     "pad": {"l": 46, "r": 16, "b": 34, "t": 16}},
            "layers": layers, "steps": steps}


def riemann_values():
    """黎曼和那几项 —— 正文与图形共用同一份计算。"""
    f = lambda x: x * x / 4.0 + 0.5          # noqa: E731
    A, B = 0.0, 3.0
    out = {"exact": (B ** 3 - A ** 3) / 12.0 + 0.5 * (B - A)}
    for n in (1, 2, 4, 8):
        d = (B - A) / n
        out[f"n{n}"] = sum(f(A + j * d) * d for j in range(n))
    return out


def fig_riemann():
    """从「斜率」到「面积」：无穷多条无穷细的矩形，和是有限的。

    画法：y = x²/4 + 1/2 在 [0,3] 上的左端点矩形和，n = 1/2/4/8 逐次替换
    （互斥显示，用 k == N），右栏读数全部由 Python 现算。
    """
    f = lambda x: x * x / 4.0 + 0.5          # noqa: E731
    XMIN, XMAX, YMIN, YMAX = -0.30, 3.40, -1.10, 3.70
    XR, YR = [XMIN, XMAX], [YMIN, YMAX]
    A, B = 0.0, 3.0
    _v = riemann_values()
    exact = _v["exact"]                      # ∫ x²/4 + 1/2 = 3.75

    layers = [
        {"geom": "axis", "xRange": XR, "yRange": YR,
         "xlab": "x", "ylab": "f(x)", "xticks": [0, 1, 2, 3], "yticks": [0, 1, 2, 3]},
    ]
    # 先画矩形、再画曲线 —— 顺序反了曲线会被填充盖掉
    for i, n in enumerate((1, 2, 4, 8)):
        k = i + 2                            # n=1 → 第 2 步
        d = (B - A) / n
        for j in range(n):
            xl = A + j * d
            layers.append({"geom": "region", "when": f"k == {k}",
                           "x": [xl, xl + d], "y": [0.0, f(xl)],
                           "fill": "#f7e8d6",
                           "outline": True, "stroke": ACCENT, "width": 1.2})
    layers += [
        {"geom": "line", "fn": "x*x/4 + 0.5", "from": [0.0, 3.0], "stroke": INK, "width": 2.6},
        {"geom": "text", "x": 2.10, "y": 3.40, "text": "f(x) = x²/4 + 1/2",
         "align": "left", "size": 11.5, "color": INK, "dy": 0, "weight": "normal"},
    ]
    # 右移后的读数列（左上角空区）
    layers.append({"geom": "text", "x": -0.22, "y": 3.40, "text": "矩形面积之和 →",
                   "align": "left", "size": 10.5, "color": DIM, "dy": 0, "weight": "normal"})
    for i, n in enumerate((1, 2, 4, 8)):
        d = (B - A) / n
        total = sum(f(A + j * d) * d for j in range(n))
        layers.append({"geom": "text", "when": f"k >= {i + 2}",
                       "x": -0.22, "y": 2.95 - 0.45 * i,
                       "text": f"n = {n} → {total:.3f}",
                       "align": "left", "size": 10, "color": ACCENT, "dy": 0,
                       "weight": "normal"})
    layers.append({"geom": "text", "when": "k >= 5", "x": -0.22, "y": 1.00,
                   "text": f"极限 = {exact:.3f}", "align": "left", "size": 12,
                   "color": GOOD, "dy": 0, "weight": "bold"})
    steps = [
        {"k": 1, "note": "要求曲线下的面积——曲线是弯的，没有现成公式。"},
        {"k": 2, "note": "用 1 个矩形顶替它。误差大得离谱：左端点取值 0.5，整个矩形只有 {:.3f}，而真值是 {:.3f}。".format(_v["n1"], exact)},
        {"k": 3, "note": "切成 2 块。和跳到 {:.3f}，缺口明显缩小。".format(_v["n2"])},
        {"k": 4, "note": "切成 4 块，和 {:.3f}。每块顶端和曲线之间只剩一个小台阶。".format(_v["n4"])},
        {"k": 5, "note": "8 块时和为 {:.3f}，极限 {:.3f}。**分得越细，误差越小**——「无穷多条无穷细的矩形」不是一个比喻，它的和是一个确定的数。这就是定积分。".format(_v["n8"], exact)},
    ]
    return {"theme": PAPER, "view": {"xRange": XR, "yRange": YR,
                                     "pad": {"l": 46, "r": 16, "b": 34, "t": 16}},
            "layers": layers, "steps": steps}


# =====================================================================
# ---- 第 5 章插图：随机 —— 从命运到概率 ----
# =====================================================================
def _coin_flips(n, seed=20261015):
    """真实抛硬币（固定种子，可复现）：返回 0/1 序列，1 = 正面。"""
    rng = random.Random(seed)
    return [1 if rng.random() < 0.5 else 0 for _ in range(n)]


def _galton(rows, balls, npaths=4, seed=20261014):
    """真实高尔顿板模拟：返回 (每格计数, 前 npaths 颗球的逐行位置)。

    球的 x 坐标用半格为单位：过完第 i 排后 x = (已向右次数 - i/2)。
    最后一排走完 x 落在 [-rows/2, rows/2]，正好是各落点的中心。
    """
    rng = random.Random(seed)
    counts = [0] * (rows + 1)
    paths = []
    for b in range(balls):
        r, xs = 0, [0.0]
        for i in range(1, rows + 1):
            if rng.random() < 0.5:
                r += 1
            xs.append((2 * r - i) / 2.0)
        counts[int(round(xs[-1] + rows / 2.0))] += 1
        if b < npaths:
            paths.append(xs)
    return counts, paths


def dice_values():
    """两颗骰子的点数分布 —— 正文与图形共用。"""
    sums = {}
    for i in range(6):
        for j in range(6):
            s = (i + 1) + (j + 1)
            sums[s] = sums.get(s, 0) + 1
    return {
        "sides": 6, "total": 6 * 6,
        "at7": sums[7], "at_mid": 7,
        "extreme": sums[2], "lo": 2, "hi": 12,
    }


def fig_dice():
    """古典概型：36 种等可能的结果 → 两骰之和的分布。

    左：6×6 结果网格（点 = 一种结果，数字 = 两骰之和，颜色 = 离 7 的远近）。
    右：按「和」分组的柱状图——等可能的结果，聚出不等的和。
    """
    gx, gy = 0.9, 1.0
    sums = {}
    for i in range(6):
        for j in range(6):
            s = (i + 1) + (j + 1)
            sums[s] = sums.get(s, 0) + 1
    counts = [sums[s] for s in range(2, 13)]          # [1,2,3,4,5,6,5,4,3,2,1]
    total = sum(counts)
    ramp = {0: "#b45309", 1: "#c2410c", 2: "#ca8a04", 3: "#a16207", 4: "#78716c", 5: "#a8a29e"}

    layers = []
    # 结果网格
    dots = [{"x": i * gx, "y": j * gy, "r": 7, "fill": ramp[min(abs((i + 1) + (j + 1) - 7), 5)],
             "label": str((i + 1) + (j + 1))} for i in range(6) for j in range(6)]
    layers.append({"geom": "point", "when": "k >= 1", "data": dots, "labelColor": INK, "labelSize": 9,
                   "r": 7})
    # 柱状图
    bars = [{"x": 8.2 + k * 1.1, "y": counts[k], "w": 0.78, "fill": ACCENT} for k in range(11)]
    layers.append({"geom": "bar", "when": "k >= 2", "data": bars})
    layers.append({"geom": "line", "when": "k >= 2", "data": [[7.5, 0], [19.9, 0]],
                   "stroke": INK, "width": 1.6})
    for c in range(7):                                 # 纵轴刻度
        layers.append({"geom": "line", "when": "k >= 2", "data": [[7.5, c], [7.85, c]],
                       "stroke": RULE, "width": 1.2})
        layers.append({"geom": "text", "when": "k >= 2", "x": 7.3, "y": c, "text": str(c),
                       "align": "right", "size": 8.5, "color": DIM, "dy": 0, "weight": "normal"})
    for k in range(11):                                # 横轴：两骰之和
        layers.append({"geom": "text", "when": "k >= 2", "x": 8.2 + k * 1.1, "y": -0.55,
                       "text": str(2 + k), "align": "center", "size": 9.5, "color": DIM,
                       "dy": 0, "weight": "normal"})
    # 标题与注记
    layers += [
        {"geom": "text", "when": "k >= 1", "x": 0.0, "y": 6.35, "text": "36 种等可能的结果",
         "align": "left", "size": 11.5, "color": INK, "dy": 0},
        {"geom": "text", "when": "k >= 1", "x": 0.0, "y": 5.8, "text": "数字 = 两骰之和",
         "align": "left", "size": 9.5, "color": DIM, "dy": 0, "weight": "normal"},
        {"geom": "text", "when": "k >= 2", "x": 8.2, "y": 6.35, "text": "两骰之和的分布",
         "align": "left", "size": 11.5, "color": INK, "dy": 0},
        {"geom": "text", "when": "k >= 2", "x": 8.2, "y": 5.8, "text": "纵轴 = 出现次数",
         "align": "left", "size": 9.5, "color": DIM, "dy": 0, "weight": "normal"},
        {"geom": "text", "when": "k >= 3", "x": 13.7, "y": 6.5, "text": "最多：6 次",
         "align": "center", "size": 10, "color": ACCENT, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": 0.0, "y": -1.3,
         "text": "每种结果概率都是 1/36，但「和」不同：", "align": "left", "size": 10,
         "color": INK, "dy": 0, "weight": "normal"},
        {"geom": "text", "when": "k >= 3", "x": 0.0, "y": -1.95,
         "text": "和 = 7 有 6 种 → 1/6；和 = 2 或 12 各 1 种 → 1/36", "align": "left",
         "size": 10, "color": INK, "dy": 0, "weight": "normal"},
    ]
    steps = [
        {"k": 1, "note": "抛出两颗骰子，共有 6×6 = 36 种结果。每一种出现的可能性完全相同——这是「古典概型」的全部前提。"},
        {"k": 2, "note": "把 36 种结果按「两骰之和」分组计数：和 = 7 的组合最多，两端最少。等可能的结果，聚出了不等的和。"},
        {"k": 3, "note": f"概率 = 有利结果数 ÷ 总结果数 = 6/36 = 1/6（和 7）。这套算法（拉普拉斯）简单有力——但它要求你能断定哪些结果「等可能」，而这往往是直觉，不是数学。"},
    ]
    return {"theme": PAPER, "view": {"xRange": [-0.9, 20.4], "yRange": [-2.3, 7.0],
                                     "pad": {"l": 20, "r": 16, "b": 30, "t": 16}},
            "layers": layers, "steps": steps}


def fig_galton():
    """高尔顿钉板：每一步都随机，总体却是确定的钟形（真实模拟，固定种子）。"""
    rows, balls = 8, 200
    counts, paths = _galton(rows, balls, seed=2502)   # 该种子下模拟柱形与理论曲线贴合最紧
    mx = max(counts)
    base, hmax = -11.4, 3.4

    def path_pts(xs):
        land = xs[-1]
        return ([[0.0, 0.6]] + [[xs[i], -float(i)] for i in range(rows + 1)]
                + [[land, -float(rows) - 1.0], [land, base]])

    layers = []
    # 钉子
    pegs = [{"x": (2 * j - i) / 2.0, "y": -float(i), "r": 2.6, "fill": DIM}
            for i in range(rows) for j in range(i + 1)]
    layers.append({"geom": "point", "when": "k >= 1", "data": pegs, "r": 2.6})
    # 第一颗球的真实路径；第 2 步再补几颗（更淡），衬出「路径各不相同」
    layers.append({"geom": "line", "data": path_pts(paths[0]), "stroke": ACCENT, "width": 2.2})
    for p in paths[1:]:
        layers.append({"geom": "line", "when": "k >= 2", "data": path_pts(p),
                       "stroke": "#d8b48c", "width": 1.3})
    layers.append({"geom": "point", "data": [{"x": paths[0][-1], "y": base, "r": 5, "fill": ACCENT}],
                   "fill": ACCENT})
    # 落格与柱状图
    layers.append({"geom": "line", "when": "k >= 3", "data": [[-4.6, base], [4.6, base]],
                   "stroke": INK, "width": 1.6})
    layers.append({"geom": "bar", "when": "k >= 3", "baseline": base, "data": [
        {"x": R - rows / 2.0, "y": base + hmax * counts[R] / mx, "w": 0.82, "fill": ACCENT}
        for R in range(rows + 1)]})
    # 理论二项分布（缩放到同一高度）
    pmf = [math.comb(rows, R) / 2.0 ** rows for R in range(rows + 1)]
    pmx = max(pmf)
    layers.append({"geom": "line", "when": "k >= 4", "stroke": TEAL, "width": 2.4, "dash": True,
                   "data": [[R - rows / 2.0, base + hmax * pmf[R] / pmx] for R in range(rows + 1)]})
    # 标注
    layers += [
        {"geom": "text", "x": 0.0, "y": 1.05, "text": "每一步都随机", "align": "center",
         "size": 11, "color": ACCENT, "dy": 0},
        {"geom": "text", "when": "k >= 1", "x": -9.6, "y": -3.0,
         "text": "钉子：\n每撞一颗，\n各一半概率\n向左 / 向右", "align": "left", "size": 10.5,
         "color": DIM, "dy": 0, "weight": "normal"},
        {"geom": "text", "when": "k >= 3", "x": -9.6, "y": -9.0,
         "text": f"{balls} 颗球\n落点堆积", "align": "left", "size": 10.5,
         "color": ACCENT, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": 9.6, "y": -9.0,
         "text": "中间最多\n两端极少", "align": "right", "size": 10.5,
         "color": INK, "dy": 0, "weight": "normal"},
        {"geom": "text", "when": "k >= 4", "x": 9.6, "y": -4.0,
         "text": "理论曲线：\n二项分布 B(8, ½)", "align": "right", "size": 10.5,
         "color": TEAL, "dy": 0},
    ]
    steps = [
        {"k": 1, "note": "一颗球从顶端落下。每撞到一颗钉子，就以 1/2 的概率向左或向右——它的路径完全不可预测。"},
        {"k": 2, "note": "再放几颗球。每颗都经历 8 次随机选择，走的路径各不相同，落点也散开——但散得有章法。"},
        {"k": 3, "note": f"放下 {balls} 颗球。每颗球的路径都不相同，可落点却自动堆成了中间高、两端低的「钟形」——随机性里长出了秩序。"},
        {"k": 4, "note": "叠上理论曲线（二项分布 B(8, ½)）：模拟的柱形与它几乎重合。这就是伯努利大数定律的雏形——单次不可预测，海量却可计算。"},
    ]
    return {"theme": PAPER, "view": {"xRange": [-11.0, 11.0], "yRange": [-11.8, 0.7],
                                     "pad": {"l": 18, "r": 18, "b": 18, "t": 18}},
            "layers": layers, "steps": steps}


def fig_lln():
    """大数定律：抛硬币的频率收敛到 1/2（真实模拟，固定种子）。"""
    flips = 500
    seq = _coin_flips(flips)
    runs, h = [], 0
    for n, x in enumerate(seq, 1):
        h += x
        runs.append([float(n), h / n])

    def upto(lo, hi):
        return [p for p in runs if lo <= p[0] <= hi]

    layers = [
        {"geom": "axis", "xRange": [0, 520], "yRange": [0, 1], "xlab": "抛掷次数 n",
         "ylab": "正面频率", "xticks": [0, 100, 200, 300, 400, 500],
         "yticks": [0, 0.25, 0.5, 0.75, 1]},
        {"geom": "region", "x": [0, 520], "y": [0.45, 0.55], "fill": "#e4efe7", "outline": False},
        {"geom": "line", "data": [[0, 0.5], [520, 0.5]], "stroke": BAD, "width": 1.6, "dash": True},
        # 三段折线：随步展开
        {"geom": "line", "when": "k >= 1", "data": upto(1, 20), "stroke": ACCENT, "width": 1.8},
        {"geom": "line", "when": "k >= 2", "data": upto(20, 120), "stroke": ACCENT, "width": 1.8},
        {"geom": "line", "when": "k >= 3", "data": upto(120, flips), "stroke": ACCENT, "width": 1.8},
        {"geom": "text", "x": 505, "y": 0.5, "text": "0.5", "align": "left", "size": 10,
         "color": BAD, "dy": -12},
    ]
    # |正 − 反| 的期望 ≈ √(2n/π) ≈ 0.8√n。用期望而非单次实测值：
    # 单次涨落会让三元组非单调，那是噪声不是规律。
    typical = [math.sqrt(2 * n / math.pi) for n in (20, 100, flips)]
    layers += [
        {"geom": "text", "x": 30, "y": 0.93, "text": f"前 20 次：频率乱跳（{runs[19][1]:.2f}）",
         "align": "left", "size": 10.5, "color": ACCENT, "dy": 0},
        {"geom": "text", "when": "k >= 2", "x": 130, "y": 0.10,
         "text": f"100 次：≈ 0.5（{runs[99][1]:.2f}）", "align": "left", "size": 10.5,
         "color": ACCENT, "dy": 0, "weight": "normal"},
        {"geom": "text", "when": "k >= 3", "x": 300, "y": 0.80,
         "text": f"{flips} 次：贴住 0.5（{h / flips:.3f}）", "align": "left", "size": 10.5,
         "color": GOOD, "dy": 0},
        {"geom": "text", "when": "k >= 4", "x": 300, "y": 0.22,
         "text": f"|正 − 反| 典型 ≈ 0.8√n：{typical[0]:.1f} → {typical[1]:.1f} → {typical[2]:.1f}（在变大）",
         "align": "left", "size": 10.5, "color": BAD, "dy": 0},
    ]
    steps = [
        {"k": 1, "note": "抛 20 次硬币。频率忽上忽下，甚至可能连续几个正面——此时「概率 = 1/2」看不出任何约束力。"},
        {"k": 2, "note": "抛到 100 次：曲线明显向 0.5 收拢。伯努利 1713 年证明：只要独立同分布，频率几乎必然收敛到概率。"},
        {"k": 3, "note": f"抛满 {flips} 次，频率几乎贴住 0.5（实际 {h / flips:.3f}）。这就是大数定律——它是「概率」第一次可以被测量的依据。"},
        {"k": 4, "note": f"一个反直觉的细节：频率在收敛，正面与反面的**典型差距**却在变大——|正 − 反| 的期望约等于 0.8√n，n = 20 / 100 / {flips} 时分别约为 {typical[0]:.1f} / {typical[1]:.1f} / {typical[2]:.1f}。收敛的是比例，不是差距。"},
    ]
    return {"theme": PAPER, "view": {"xRange": [0, 520], "yRange": [0, 1],
                                     "pad": {"l": 44, "r": 16, "b": 30, "t": 16}},
            "layers": layers, "steps": steps}


def fig_bertrand():
    """伯特兰悖论：同一个「随机弦」，三种「等可能」给出三个答案。"""
    def chord_from_d(theta, d):
        """给定法向角 theta 与到圆心距离 d，返回弦的两个端点。"""
        nx, ny = math.cos(theta), math.sin(theta)
        t = math.sqrt(max(0.0, 1.0 - d * d))
        return [[d * nx - t * -ny, d * ny - t * nx], [d * nx + t * -ny, d * ny + t * nx]]

    rng = random.Random(20261016)
    # 方法一：圆周上随机取两个端点
    m1 = []
    for _ in range(5):
        a1, a2 = rng.uniform(0, 2 * math.pi), rng.uniform(0, 2 * math.pi)
        m1.append([[math.cos(a1), math.sin(a1)], [math.cos(a2), math.sin(a2)]])
    # 方法二：随机取一条半径，再在半径上随机取一点作垂足
    m2 = [chord_from_d(rng.uniform(0, 2 * math.pi), rng.random()) for _ in range(5)]
    # 方法三：在圆盘内均匀随机取一点作中点
    m3 = []
    while len(m3) < 5:
        px, py = rng.uniform(-1, 1), rng.uniform(-1, 1)
        if px * px + py * py <= 1:
            m3.append(chord_from_d(math.atan2(py, px), math.hypot(px, py)))

    circle = [[math.cos(2 * math.pi * i / 96), math.sin(2 * math.pi * i / 96)] for i in range(97)]
    inner = [[0.5 * math.cos(2 * math.pi * i / 72), 0.5 * math.sin(2 * math.pi * i / 72)]
             for i in range(73)]
    tri = [[0.0, 1.0], [-math.sqrt(3) / 2, -0.5], [math.sqrt(3) / 2, -0.5], [0.0, 1.0]]

    layers = [
        {"geom": "line", "data": circle, "stroke": INK, "width": 2.0},
        {"geom": "line", "data": inner, "stroke": BAD, "width": 1.4, "dash": True},
        {"geom": "line", "data": tri, "stroke": DIM, "width": 1.4, "dash": True},
        {"geom": "text", "x": 0.0, "y": 1.16, "text": "分界圈 r = ½", "align": "center",
         "size": 9.5, "color": BAD, "dy": 0, "weight": "normal"},
    ]
    for i, seg in enumerate(m1):
        layers.append({"geom": "line", "when": "k == 2", "data": seg, "stroke": ACCENT, "width": 1.6})
    for i, seg in enumerate(m2):
        layers.append({"geom": "line", "when": "k == 3", "data": seg, "stroke": ACCENT2, "width": 1.6})
    for i, seg in enumerate(m3):
        layers.append({"geom": "line", "when": "k == 4", "data": seg, "stroke": TEAL, "width": 1.6})
    layers += [
        {"geom": "text", "x": -3.0, "y": 1.05, "text": "同一个圆，同一条问题：", "align": "left",
         "size": 11, "color": INK, "dy": 0},
        {"geom": "text", "x": -3.0, "y": 0.75, "text": "随机画一条弦，", "align": "left",
         "size": 11, "color": INK, "dy": 0, "weight": "normal"},
        {"geom": "text", "x": -3.0, "y": 0.45, "text": "它比内接正三角形", "align": "left",
         "size": 11, "color": INK, "dy": 0, "weight": "normal"},
        {"geom": "text", "x": -3.0, "y": 0.15, "text": "的边更长的概率？", "align": "left",
         "size": 11, "color": INK, "dy": 0, "weight": "normal"},
        {"geom": "text", "when": "k >= 2", "x": 3.0, "y": 0.75, "text": "① 随机取两端点 → 1/3",
         "align": "right", "size": 11, "color": ACCENT, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": 3.0, "y": 0.35, "text": "② 随机取半径上的点 → 1/2",
         "align": "right", "size": 11, "color": ACCENT2, "dy": 0},
        {"geom": "text", "when": "k >= 4", "x": 3.0, "y": -0.05, "text": "③ 随机取圆盘内一点 → 1/4",
         "align": "right", "size": 11, "color": TEAL, "dy": 0},
        {"geom": "text", "when": "k >= 5", "x": -3.0, "y": -0.95,
         "text": "三种随机化都「无偏」，答案却各不相同 ——", "align": "left", "size": 10.5,
         "color": BAD, "dy": 0},
        {"geom": "text", "when": "k >= 5", "x": -3.0, "y": -1.2,
         "text": "「等可能」在没有定义之前，只是直觉。", "align": "left", "size": 10.5,
         "color": BAD, "dy": 0, "weight": "normal"},
    ]
    steps = [
        {"k": 1, "note": "在圆里「随机」画一条弦，问它比内接正三角形的边更长的概率——听上去毫无歧义。"},
        {"k": 2, "note": "① 先随机取两个端点，再连线。算得概率 = 1/3。够自然吧？"},
        {"k": 3, "note": "② 先随机取一条半径，再在半径上随机取一点作垂足。同一问题的答案变成了 1/2。"},
        {"k": 4, "note": "③ 先在圆盘内均匀随机取一点作中点。答案又变成了 1/4。"},
        {"k": 5, "note": "三种做法都没有偏心，却给出三个答案。歧义不在推理，而在「随机」二字——连续情形下，没有一个天然的「等可能」。概率亟需一个不依赖直觉的定义。"},
    ]
    return {"theme": PAPER, "view": {"xRange": [-3.1, 3.1], "yRange": [-1.35, 1.35],
                                     "pad": {"l": 16, "r": 16, "b": 16, "t": 16},
                                     "equalAspect": True},
            "layers": layers, "steps": steps}


def fig_axioms():
    """柯尔莫哥洛夫公理化：概率 = 定义在事件域上的测度。"""
    layers = [
        {"geom": "region", "x": [0.6, 9.4], "y": [2.2, 5.6], "fill": "#f7f4ef",
         "outline": True, "stroke": INK, "width": 1.8},
        {"geom": "region", "when": "k >= 2", "x": [1.4, 4.2], "y": [2.7, 5.1],
         "fill": "#e4efe7", "outline": True, "stroke": GOOD, "width": 1.6},
        {"geom": "region", "when": "k >= 3", "x": [5.2, 8.6], "y": [2.7, 5.1],
         "fill": "#ece7f7", "outline": True, "stroke": ACCENT2, "width": 1.6},
        {"geom": "text", "x": 0.85, "y": 5.3, "text": "Ω  （样本空间）", "align": "left",
         "size": 11, "color": INK, "dy": 0},
        {"geom": "text", "when": "k >= 2", "x": 2.8, "y": 3.9, "text": "A", "align": "center",
         "size": 15, "color": GOOD, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": 6.9, "y": 3.9, "text": "B", "align": "center",
         "size": 15, "color": ACCENT2, "dy": 0},
        # 三条公理
        {"geom": "text", "when": "k >= 1", "x": 0.6, "y": 1.5,
         "text": "① 非负：  P(A) ≥ 0", "align": "left", "size": 11, "color": INK, "dy": 0,
         "weight": "normal"},
        {"geom": "text", "when": "k >= 2", "x": 0.6, "y": 1.0,
         "text": "② 归一：  P(Ω) = 1", "align": "left", "size": 11, "color": INK, "dy": 0,
         "weight": "normal"},
        {"geom": "text", "when": "k >= 4", "x": 0.6, "y": 0.5,
         "text": "③ 可加：  A ∩ B = ∅  ⟹  P(A ∪ B) = P(A) + P(B)", "align": "left",
         "size": 11, "color": INK, "dy": 0, "weight": "normal"},
        {"geom": "text", "when": "k >= 5", "x": 9.4, "y": 1.0,
         "text": "概率不再需要「等可能」", "align": "right", "size": 11, "color": TEAL, "dy": 0},
    ]
    steps = [
        {"k": 1, "note": "先规定舞台：Ω 是所有可能结果的集合（样本空间）。公理②说：整个 Ω 的概率是 1——必然事件。"},
        {"k": 2, "note": "事件 A 就是 Ω 的一个子集。公理①说：任何事件的概率不小于 0——没有「负概率」。"},
        {"k": 3, "note": "再放入事件 B，让 A 与 B 没有交集：它们不可能同时发生。"},
        {"k": 4, "note": "公理③（可加性）：互斥事件的概率可以直接相加。三条公理一列，概率就成了纯粹的「测度」。"},
        {"k": 5, "note": "1933 年柯尔莫哥洛夫完成这一步。从此「等可能」不再是前提而是特例——伯特兰悖论那种歧义被排除在体系之外：你必须先指定测度，才谈得上概率。"},
    ]
    return {"theme": PAPER, "view": {"xRange": [0, 10], "yRange": [0, 6.2],
                                     "pad": {"l": 16, "r": 16, "b": 16, "t": 16}},
            "layers": layers, "steps": steps}


# ================= 第 6 章：空间几何助手 =================

def _disk_geo(P, Q):
    """庞加莱圆盘内 P→Q 的测地线：与单位圆正交的圆。
    P、Q 与原点共线时返回 (None, None) —— 那时测地线是一条直线（弦）。"""
    if abs(P[0] * Q[1] - P[1] * Q[0]) < 1e-12:
        return None, None
    c1 = (1 + P[0] ** 2 + P[1] ** 2) / 2
    c2 = (1 + Q[0] ** 2 + Q[1] ** 2) / 2
    det = P[0] * Q[1] - P[1] * Q[0]
    Mx = (c1 * Q[1] - P[1] * c2) / det
    My = (P[0] * c2 - c1 * Q[0]) / det
    r2 = Mx * Mx + My * My - 1                      # 正交条件 |M|² = 1 + ρ²
    return ((Mx, My), math.sqrt(r2)) if r2 > 0 else (None, None)


def _disk_arc(P, Q, n=40):
    """P→Q 的测地线折线：落在单位圆盘内的那段圆弧（退化时是弦）。"""
    M, rho = _disk_geo(P, Q)
    if M is None:
        return [[P[0], P[1]], [Q[0], Q[1]]]
    a0 = math.atan2(P[1] - M[1], P[0] - M[0])
    a1 = math.atan2(Q[1] - M[1], Q[0] - M[0])
    d = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
    for sgn in (1, -1):
        pts, ok = [], True
        for k in range(n + 1):
            t = a0 + sgn * d * k / n
            x, y = M[0] + rho * math.cos(t), M[1] + rho * math.sin(t)
            if x * x + y * y > 1 + 1e-7:            # 只留盘内那一段
                ok = False
                break
            pts.append([x, y])
        if ok:
            return pts
    return [[P[0], P[1]], [Q[0], Q[1]]]


def _disk_tan(P, Q):
    """测地线在 P 处、指向 Q 的单位切向。"""
    M, _ = _disk_geo(P, Q)
    if M is None:
        dx, dy = Q[0] - P[0], Q[1] - P[1]
        n = math.hypot(dx, dy)
        return (dx / n, dy / n)
    tx, ty = -(P[1] - M[1]), P[0] - M[0]
    if (Q[0] - P[0]) * tx + (Q[1] - P[1]) * ty < 0:
        tx, ty = -tx, -ty
    n = math.hypot(tx, ty)
    return (tx / n, ty / n)


def _dir_deg(P, Q):
    u = _disk_tan(P, Q)
    return math.degrees(math.atan2(u[1], u[0])) % 360


def _ang_deg(u, v):
    return math.degrees(math.acos(max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1]))))


def _disk_angles(A, B, C):
    """圆盘模型共形 ⇒ 三角形内角就是两条测地线切向的欧氏夹角。"""
    return (_ang_deg(_disk_tan(A, B), _disk_tan(A, C)),
            _ang_deg(_disk_tan(B, A), _disk_tan(B, C)),
            _ang_deg(_disk_tan(C, A), _disk_tan(C, B)))


def _circle(cx, cy, r, n=72):
    """闭合圆折线。"""
    return [[cx + r * math.cos(2 * math.pi * k / n),
             cy + r * math.sin(2 * math.pi * k / n)] for k in range(n + 1)]


def _ray_arc(cx, cy, r, a0, a1, n=20):
    """极坐标圆弧折线（角度制，可跨 0°）。"""
    return [[cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))]
            for k in range(n + 1)]


def _disk_family(m, n=44):
    """过 P=(0,0.5) 的测地线族：圆心 (m,1.25)、半径 √(m²+0.5625)，与单位圆正交。
    |m|<1 不与 x 轴直径相交（平行），|m|=1 与之相切于边界（极限平行）。"""
    Mx, My = m, 1.25
    rho = math.sqrt(m * m + 0.5625)
    d = math.hypot(Mx, My)
    base = math.atan2(My, Mx) + math.pi            # 指向圆盘中心的方向
    half = math.acos(max(-1.0, min(1.0, (d * d + rho * rho - 1) / (2 * d * rho))))
    e0, e1 = base - half, base + half
    return [[Mx + rho * math.cos(e0 + (e1 - e0) * k / n),
             My + rho * math.sin(e0 + (e1 - e0) * k / n)] for k in range(n + 1)]


def _polar(lat_deg, lon_deg, rot=45.0):
    """极地俯视投影：纬度给半径，经度给方位角（整体再转 rot 度）。"""
    r = math.cos(math.radians(lat_deg))
    a = math.radians(lon_deg + rot)
    return (r * math.cos(a), r * math.sin(a))


def fig_fifth():
    """第五公设（Playfair）：过直线外一点，恰有一条平行线。"""
    xr, yr = (-1.35, 6.5), (-0.95, 3.3)
    P, PY = (2.0, 1.5), 1.5
    slopes = [0.6, 1.0, -1.0, -0.6]
    layers = [
        {"geom": "line", "data": [[xr[0], 0], [xr[1], 0]], "stroke": INK, "width": 2.8},
        {"geom": "point", "data": [{"x": P[0], "y": P[1]}], "r": 5.5, "fill": INK},
        {"geom": "text", "x": 6.35, "y": -0.45, "text": "直线 L", "align": "right",
         "size": 12, "color": INK, "dy": 0},
        {"geom": "text", "x": 2.22, "y": 1.72, "text": "点 P", "align": "left",
         "size": 12, "color": INK, "dy": 0},
    ]
    for s in slopes:
        seg = _clip_seg((P[0] - 200, P[1] - 200 * s), (P[0] + 200, P[1] + 200 * s), xr, yr)
        if seg:
            layers.append({"geom": "line", "when": "k >= 2", "data": seg,
                           "stroke": DIM, "width": 1.7})
    layers += [
        {"geom": "point", "when": "k >= 3",
         "data": [{"x": P[0] - P[1] / s, "y": 0} for s in slopes], "r": 4.5, "fill": GOOD},
        {"geom": "text", "when": "k >= 2", "x": 1.0, "y": 3.0, "text": "过 P 的直线，都撞上 L",
         "align": "left", "size": 11, "color": DIM, "dy": 0},
        {"geom": "line", "when": "k >= 4", "data": [[xr[0], PY], [xr[1], PY]],
         "stroke": ACCENT, "width": 2.2, "dash": True},
        {"geom": "text", "when": "k >= 4", "x": -1.25, "y": 1.78,
         "text": "唯一与 L 不相交的直线（平行）", "align": "left", "size": 11,
         "color": ACCENT, "dy": 0},
        {"geom": "text", "when": "k >= 5", "x": 2.5, "y": -0.78,
         "text": "两千多年里，人们一直想把它证明出来", "align": "center", "size": 11,
         "color": INK, "dy": 0},
    ]
    steps = [
        {"k": 1, "note": "先摆好舞台：一条直线 L，和它外面的一点 P。欧几里得前四条公设都短得像废话，第五条却啰嗦得可疑。"},
        {"k": 2, "note": "过 P 显然可以画无数条直线——随便转个角度就是一条。"},
        {"k": 3, "note": "只要角度不是零，这些直线迟早都会撞上 L（绿点是交点）。"},
        {"k": 4, "note": "只有水平的那一条例外：它与 L 永远不相交。这就是「平行公设」——普莱菲尔把它说成：过直线外一点，恰有一条平行线。"},
        {"k": 5, "note": "「恰有一条」听上去天经地义，可它在两千多年里被反复尝试证明：假设第五公设不成立，期望推出矛盾，结果每次都卡在某一步——而那一步，恰好偷偷用回了第五公设本身。"},
    ]
    return {"theme": PAPER, "view": {"xRange": list(xr), "yRange": list(yr),
                                     "pad": {"l": 16, "r": 16, "b": 18, "t": 18}},
            "layers": layers, "steps": steps}


def fig_hyperbolic():
    """双曲几何：过直线外一点，有无穷多条平行线（庞加莱圆盘）。"""
    layers = [
        {"geom": "line", "data": _circle(0, 0, 1), "stroke": DIM, "width": 1.6, "dash": True},
        {"geom": "line", "when": "k >= 1", "data": [[-1, 0], [1, 0]], "stroke": INK, "width": 2.8},
        {"geom": "point", "when": "k >= 1", "data": [{"x": 0, "y": 0.5}], "r": 5.5, "fill": INK},
        {"geom": "text", "when": "k >= 1", "x": -1.25, "y": -0.20, "text": "L",
         "align": "right", "size": 12, "color": INK, "dy": 0},
        {"geom": "text", "when": "k >= 1", "x": 0.14, "y": 0.60, "text": "P",
         "align": "left", "size": 12, "color": INK, "dy": 0},
    ]
    for m in (2.0, 1.4, -1.4, -2.0):
        layers.append({"geom": "line", "when": "k >= 2", "data": _disk_family(m),
                       "stroke": DIM, "width": 1.7})
    layers.append({"geom": "point", "when": "k >= 3",
                   "data": [{"x": m - math.copysign(math.sqrt(m * m - 1), m), "y": 0}
                            for m in (2.0, 1.4, -1.4, -2.0)], "r": 4, "fill": GOOD})
    for m in (-0.8, -0.4, 0.0, 0.4, 0.8):
        layers.append({"geom": "line", "when": "k >= 3", "data": _disk_family(m),
                       "stroke": ACCENT, "width": 2.2})
    for m in (-1.0, 1.0):
        layers.append({"geom": "line", "when": "k >= 4", "data": _disk_family(m),
                       "stroke": TEAL, "width": 1.8, "dash": True})
    layers += [
        {"geom": "text", "when": "k >= 1", "x": -1.42, "y": 1.00, "text": "圆周 = 无穷远",
         "align": "right", "size": 11, "color": DIM, "dy": 0},
        {"geom": "text", "when": "k >= 2", "x": -1.42, "y": -0.70, "text": "这些都会撞上 L",
         "align": "right", "size": 11, "color": DIM, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": -1.42, "y": -1.08, "text": "这一族一条都不撞",
         "align": "right", "size": 11, "color": ACCENT, "dy": 0},
        {"geom": "text", "when": "k >= 4", "x": 1.42, "y": -0.70, "text": "这两条与边界相切",
         "align": "left", "size": 11, "color": TEAL, "dy": 0},
        {"geom": "text", "when": "k >= 5", "x": 1.42, "y": 1.00, "text": "过 P 有无穷多条平行线",
         "align": "left", "size": 12, "color": ACCENT, "dy": 0},
    ]
    steps = [
        {"k": 1, "note": "整个圆盘就是一份完整的双曲平面：圆周不是墙，而是「无穷远」——走一辈子也走不到。L 是盘里的一条直线，P 是它外面的一点。"},
        {"k": 2, "note": "过 P 画直线。盘里的「直线」不是随意直线，而是与圆周正交的圆弧或直径。这几条显然会与 L 相交。"},
        {"k": 3, "note": "绿点标出交点：它们确实都撞上了 L。但别急着下结论。"},
        {"k": 4, "note": "再画一组：这一族圆弧虽然也从 P 出发，却始终停在 L 的同一侧，永不相交。另有两条恰好与圆周相切于一点——它们是「极限平行线」。"},
        {"k": 5, "note": "结论令人震惊：在双曲几何里，过直线外一点可以有无穷多条平行线。公理五被推翻了，可整个体系却处处自洽、毫无矛盾。"},
    ]
    return {"theme": PAPER, "view": {"xRange": [-3.0, 3.0], "yRange": [-1.3, 1.3],
                                     "pad": {"l": 16, "r": 16, "b": 16, "t": 16},
                                     "equalAspect": True},
            "layers": layers, "steps": steps}


def fig_sphere():
    """球面几何：八分之一球面三角形，内角和 270°，角盈 90°。"""
    vr, vl = _polar(0, 0), _polar(0, 90)
    layers = [
        {"geom": "line", "data": _circle(0, 0, 1), "stroke": INK, "width": 2.4},
        {"geom": "line", "data": _circle(0, 0, math.cos(math.radians(30))),
         "stroke": DIM, "width": 1.1},
        {"geom": "line", "data": _circle(0, 0, math.cos(math.radians(60))),
         "stroke": DIM, "width": 1.1},
    ]
    for a in range(0, 360, 45):
        layers.append({"geom": "line",
                       "data": [[0, 0], [math.cos(math.radians(a)), math.sin(math.radians(a))]],
                       "stroke": DIM, "width": 1.0})
    layers.append({"geom": "line", "when": "k >= 2",
                   "data": [[0.0, 0.0], list(vr)] + _ray_arc(0, 0, 1, 45, 135)[1:] + [[0.0, 0.0]],
                   "stroke": ACCENT, "width": 2.8})
    layers += [
        {"geom": "point", "when": "k >= 2",
         "data": [{"x": 0, "y": 0}, {"x": vr[0], "y": vr[1]}, {"x": vl[0], "y": vl[1]}],
         "r": 4.5, "fill": INK},
        {"geom": "text", "when": "k >= 1", "x": -1.55, "y": 1.05, "text": "从北极上空俯视",
         "align": "right", "size": 11, "color": INK, "dy": 0},
        {"geom": "text", "when": "k >= 1", "x": -1.55, "y": 0.55, "text": "最外圈 = 赤道",
         "align": "right", "size": 10.5, "color": DIM, "dy": 0},
        {"geom": "text", "when": "k >= 1", "x": -1.55, "y": 0.10, "text": "同心圆 = 纬线",
         "align": "right", "size": 10.5, "color": DIM, "dy": 0},
        {"geom": "text", "when": "k >= 1", "x": -1.55, "y": -0.35, "text": "放射线 = 经线",
         "align": "right", "size": 10.5, "color": DIM, "dy": 0},
        {"geom": "text", "when": "k >= 2", "x": 1.55, "y": 1.05, "text": "八分之一球面",
         "align": "left", "size": 11, "color": ACCENT, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": 1.55, "y": 0.55, "text": "三个角各 90°",
         "align": "left", "size": 11, "color": INK, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": 1.55, "y": 0.10, "text": "内角和 = 270°",
         "align": "left", "size": 12, "color": INK, "dy": 0, "weight": "bold"},
        {"geom": "text", "when": "k >= 3", "x": 1.55, "y": -0.35, "text": "多出的 90° 叫角盈",
         "align": "left", "size": 11, "color": GOOD, "dy": 0},
        {"geom": "text", "when": "k >= 4", "x": 0.0, "y": -1.22, "text": "角盈 = 球面面积 / R²",
         "align": "center", "size": 11, "color": INK, "dy": 0},
    ]
    for cx, cy, r, a0, a1 in ((0.0, 0.0, 0.26, 45, 135), (vr[0], vr[1], 0.19, 135, 225),
                              (vl[0], vl[1], 0.19, 315, 45)):
        layers.append({"geom": "line", "when": "k >= 3", "data": _ray_arc(cx, cy, r, a0, a1),
                       "stroke": GOOD, "width": 1.8})
    layers += [
        {"geom": "text", "when": "k >= 3", "x": 0.0, "y": 0.36, "text": "90°",
         "align": "center", "size": 11, "color": GOOD, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": vr[0] - 0.32, "y": vr[1], "text": "90°",
         "align": "center", "size": 11, "color": GOOD, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": vl[0] + 0.32, "y": vl[1], "text": "90°",
         "align": "center", "size": 11, "color": GOOD, "dy": 0},
    ]
    steps = [
        {"k": 1, "note": "这是从北极上空俯视的地球仪。最外圈是赤道，同心圆是纬线，放射状直线是经线——注意它们在北极汇于一点。"},
        {"k": 2, "note": "取整个球面的八分之一（两条经线相隔 90°，正好是北半球的四分之一）：两条经线与赤道的一段弧，围出一个球面三角形。它的顶点是北极和赤道上的两点。"},
        {"k": 3, "note": "三个角都是直角：北极那一个是两条经线张开的 90°（等于它们的经度差），赤道上两端各是经线与赤道正交的 90°。内角和 = 90° × 3 = 270°，比平面多出整整 90°！"},
        {"k": 4, "note": "这多出来的部分叫「角盈」，而且它有精确的公式：角盈 = 球面面积 / R²。这个八分之一球面面积正好是 4πR²/8 = πR²/2，除以 R² 得 π，正是 90°。曲面越弯，同样的三角形越「胖」。"},
    ]
    return {"theme": PAPER, "view": {"xRange": [-3.4, 3.4], "yRange": [-1.4, 1.4],
                                     "pad": {"l": 16, "r": 16, "b": 16, "t": 16},
                                     "equalAspect": True},
            "layers": layers, "steps": steps}


def poincare_values():
    """庞加莱三角形的那几个数 —— **正文与图形共用同一份计算**。

    这是「生成路径」的样板：正文里原本手写的三个角与角亏，改由 @@tot@@ / @@defect@@
    这类记号引用，装配时用本函数的返回值替换 —— 图文同源，不可能不一致。
    """
    A, B, C = (-0.5, 0.0), (0.5, 0.0), (0.0, 0.4)
    aa, ab, ac = _disk_angles(A, B, C)
    tot = aa + ab + ac
    return {
        "a1": aa, "a2": ab, "a3": ac, "tot": tot,
        "defect": 180.0 - tot,                    # 角亏（度）
        "area": math.pi - math.radians(tot),      # K = −1 时的双曲面积
    }


def fig_poincare():
    """庞加莱圆盘：测地线三角形的内角和小于 180°。"""
    _v = poincare_values()
    A, B, C = (-0.5, 0.0), (0.5, 0.0), (0.0, 0.4)
    aa, ab, ac = _v["a1"], _v["a2"], _v["a3"]
    tot = _v["tot"]
    layers = [
        {"geom": "line", "data": _circle(0, 0, 1), "stroke": DIM, "width": 1.6, "dash": True},
        {"geom": "text", "when": "k >= 1", "x": -1.42, "y": 1.00, "text": "圆周 = 无穷远",
         "align": "right", "size": 11, "color": DIM, "dy": 0},
        {"geom": "text", "when": "k >= 1", "x": -1.42, "y": -1.05, "text": "有些「直线」是圆弧",
         "align": "right", "size": 11, "color": ACCENT, "dy": 0},
    ]
    for (P, Q) in ((A, B), (B, C), (C, A)):
        layers.append({"geom": "line", "when": "k >= 2", "data": _disk_arc(P, Q),
                       "stroke": ACCENT, "width": 2.6})
    layers.append({"geom": "point", "when": "k >= 2",
                   "data": [{"x": p[0], "y": p[1]} for p in (A, B, C)], "r": 5, "fill": INK})
    marks = ((A, 0.13, 0.0, _dir_deg(A, C)), (B, 0.13, _dir_deg(B, C), 180.0),
             (C, 0.13, _dir_deg(C, A), _dir_deg(C, B)))
    for (P, r, a0, a1) in marks:
        layers.append({"geom": "line", "when": "k >= 3", "data": _ray_arc(P[0], P[1], r, a0, a1),
                       "stroke": GOOD, "width": 1.8})
    for (P, r, a0, a1), txt in zip(marks, (f"{aa:.2f}°", f"{ab:.2f}°", f"{ac:.2f}°")):
        mid = math.radians(a0 + ((a1 - a0) % 360) / 2)
        layers.append({"geom": "text", "when": "k >= 3",
                       "x": P[0] + 0.26 * math.cos(mid), "y": P[1] + 0.26 * math.sin(mid),
                       "text": txt, "align": "center", "size": 11, "color": GOOD, "dy": 0})
    layers += [
        {"geom": "text", "when": "k >= 4", "x": 1.42, "y": 0.70, "text": "内角和",
         "align": "left", "size": 11, "color": INK, "dy": 0},
        {"geom": "text", "when": "k >= 4", "x": 1.42, "y": 0.40,
         "text": f"= {tot:.2f}°", "align": "left", "size": 13, "color": INK, "dy": 0,
         "weight": "bold"},
        {"geom": "text", "when": "k >= 4", "x": 1.42, "y": 0.00,
         "text": f"少了 {180 - tot:.2f}°", "align": "left", "size": 11, "color": BAD, "dy": 0},
        {"geom": "text", "when": "k >= 5", "x": 1.42, "y": -0.90, "text": "三角形天生更「瘦」",
         "align": "left", "size": 11, "color": INK, "dy": 0},
    ]
    steps = [
        {"k": 1, "note": "还是那个庞加莱圆盘：圆周是无穷远，谁也到不了。所以盘里其实没有「边界上的点」。"},
        {"k": 2, "note": "取三个点，用测地线连起来。注意底边穿过圆心，所以是直的；另外两条是与圆周正交的圆弧，向内弓起——三角形因此比看上去「瘦」。"},
        {"k": 3, "note": "庞加莱度量是共形的：在同一点上，双曲角就等于图上量到的欧氏角。逐个量出来：三个角分别是 {:.2f}°、{:.2f}°、{:.2f}°。".format(aa, ab, ac)},
        {"k": 4, "note": "三个数严格相加：{:.2f} + {:.2f} + {:.2f} = {:.2f}°，比 180° 少了 {:.2f}°。这一差额叫「角亏」，不是测量误差，而是负曲率空间的必然结果。".format(aa, ab, ac, tot, 180 - tot)},
        {"k": 5, "note": "同一套三角形，在球面上内角和超过 180°，在平面上正好 180°，在双曲面上却不足 180°。空间的弯曲程度，直接决定了三角形的形状。"},
    ]
    return {"theme": PAPER, "view": {"xRange": [-3.0, 3.0], "yRange": [-1.3, 1.3],
                                     "pad": {"l": 16, "r": 16, "b": 16, "t": 16},
                                     "equalAspect": True},
            "layers": layers, "steps": steps}


def curvature_values():
    """三种曲率下同一个角的读数 —— 正文与图形共用同一份计算。"""
    A, B, C = (-0.5, 0.0), (0.5, 0.0), (0.0, 0.4)
    aa, ab, ac = _disk_angles(A, B, C)
    hyp_tot = aa + ab + ac
    flat_a = math.degrees(math.atan2(0.4, 0.5))
    sph_a = 90.0                       # 球面三角形的任一角：北极 + 赤道上相隔 90° 的两点
    flat_tot, sph_tot = 180.0, 270.0   # 平面内角和；球面三个角都是直角
    return {
        "hyp_angle": aa, "hyp2": ab, "hyp3": ac,
        "flat_angle": flat_a, "sph_angle": sph_a,
        "hyp_tot": hyp_tot, "flat_tot": flat_tot, "sph_tot": sph_tot,
        "hyp_gap": flat_tot - hyp_tot, "flat_gap": 0.0, "sph_gap": sph_tot - flat_tot,
        "hyp_area": math.pi - math.radians(hyp_tot),   # K = −1 时的双曲面积
    }


def fig_curvature():
    """三种曲率并置：同一个三角形顶点，内角和各不相同；角盈 = 曲率 × 面积。"""
    _v = curvature_values()
    A, B, C = (-0.5, 0.0), (0.5, 0.0), (0.0, 0.4)
    # 三种几何的内角和与角盈/角亏全部现算，图上一个数字都不许手写
    aa, ab, ac = _v["hyp_angle"], _v["hyp2"], _v["hyp3"]
    flat_a, sph_a = _v["flat_angle"], _v["sph_angle"]
    hyp_tot, flat_tot, sph_tot = _v["hyp_tot"], _v["flat_tot"], _v["sph_tot"]
    hyp_gap, flat_gap, sph_gap = _v["hyp_gap"], _v["flat_gap"], _v["sph_gap"]
    hyp_area = _v["hyp_area"]
    S, CY, PX = 0.95, 0.05, (-2.55, 0.0, 2.55)

    def tp(i, p):
        return [PX[i] + S * p[0], CY + S * p[1]]

    vr, vl = _polar(0, 0), _polar(0, 90)
    layers = [
        {"geom": "line", "data": _circle(PX[0], CY, S), "stroke": DIM, "width": 1.4, "dash": True},
        {"geom": "line", "data": _circle(PX[2], CY, S), "stroke": INK, "width": 1.6},
        {"geom": "line", "data": _circle(PX[2], CY, S * math.cos(math.radians(30))),
         "stroke": DIM, "width": 0.9},
    ]
    for (P, Q) in ((A, B), (B, C), (C, A)):
        layers.append({"geom": "line", "data": [tp(0, p) for p in _disk_arc(P, Q)],
                       "stroke": BAD, "width": 2.6})
    for (P, Q) in ((A, B), (B, C), (C, A)):
        layers.append({"geom": "line", "data": [tp(1, P), tp(1, Q)], "stroke": INK, "width": 2.6})
    layers.append({"geom": "line",
                   "data": [tp(2, p) for p in ([0.0, 0.0], list(vr))] +
                           [[PX[2] + S * math.cos(math.radians(t)), CY + S * math.sin(math.radians(t))]
                            for t in (60, 90, 120)] +
                           [tp(2, list(vl)), [PX[2], CY]],
                   "stroke": GOOD, "width": 2.6})
    layers.append({"geom": "point",
                   "data": [tp(0, p) for p in (A, B, C)] + [tp(1, p) for p in (A, B, C)],
                   "r": 4, "fill": INK})
    layers.append({"geom": "point",
                   "data": [[PX[2], CY], tp(2, list(vr)), tp(2, list(vl))], "r": 4, "fill": INK})
    # 左下角标记：负曲率 27.3° / 平坦 38.7° / 正曲率 90°（k>=2）
    layers.append({"geom": "line", "when": "k >= 2",
                   "data": _ray_arc(PX[0] + S * A[0], CY, S * 0.20, 0, aa),
                   "stroke": BAD, "width": 2.0})
    layers.append({"geom": "line", "when": "k >= 2",
                   "data": _ray_arc(PX[1] + S * A[0], CY, S * 0.20, 0, flat_a),
                   "stroke": INK, "width": 2.0})
    layers.append({"geom": "line", "when": "k >= 2",
                   "data": _ray_arc(PX[2] + S * vl[0], CY + S * vl[1], S * 0.20, 315, 45),
                   "stroke": GOOD, "width": 2.0})
    layers += [
        {"geom": "text", "x": 0.0, "y": 1.45, "text": "角盈 = 曲率 × 面积", "align": "center",
         "size": 12, "color": INK, "dy": 0, "weight": "bold", "when": "k >= 4"},
        {"geom": "text", "when": "k >= 5", "x": PX[0], "y": 1.22, "text": f"角亏 {hyp_gap:.2f}°",
         "align": "center", "size": 11, "color": BAD, "dy": 0},
        {"geom": "text", "when": "k >= 5", "x": PX[1], "y": 1.22, "text": f"角盈 {flat_gap:.2f}°",
         "align": "center", "size": 11, "color": INK, "dy": 0},
        {"geom": "text", "when": "k >= 5", "x": PX[2], "y": 1.22, "text": f"角盈 {sph_gap:.2f}°",
         "align": "center", "size": 11, "color": GOOD, "dy": 0},
        {"geom": "text", "x": PX[0], "y": -1.05, "text": "K < 0   负曲率", "align": "center",
         "size": 11, "color": BAD, "dy": 0},
        {"geom": "text", "x": PX[1], "y": -1.05, "text": "K = 0   平坦", "align": "center",
         "size": 11, "color": INK, "dy": 0},
        {"geom": "text", "x": PX[2], "y": -1.05, "text": "K > 0   正曲率", "align": "center",
         "size": 11, "color": GOOD, "dy": 0},
        {"geom": "text", "when": "k >= 2", "x": PX[0], "y": -1.27, "text": f"左下角 {aa:.1f}°",
         "align": "center", "size": 11, "color": BAD, "dy": 0},
        {"geom": "text", "when": "k >= 2", "x": PX[1], "y": -1.27, "text": f"左下角 {flat_a:.1f}°",
         "align": "center", "size": 11, "color": INK, "dy": 0},
        {"geom": "text", "when": "k >= 2", "x": PX[2], "y": -1.27, "text": f"左下角 {sph_a:.1f}°",
         "align": "center", "size": 11, "color": GOOD, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": PX[0], "y": -1.47, "text": f"内角和 = {hyp_tot:.1f}°",
         "align": "center", "size": 12, "color": BAD, "dy": 0, "weight": "bold"},
        {"geom": "text", "when": "k >= 3", "x": PX[1], "y": -1.47, "text": f"内角和 = {flat_tot:.1f}°",
         "align": "center", "size": 12, "color": INK, "dy": 0, "weight": "bold"},
        {"geom": "text", "when": "k >= 3", "x": PX[2], "y": -1.47, "text": f"内角和 = {sph_tot:.1f}°",
         "align": "center", "size": 12, "color": GOOD, "dy": 0, "weight": "bold"},
    ]
    steps = [
        {"k": 1, "note": "把三个三角形并排放在一起，顶点位置完全相同：左图是双曲圆盘里的测地线三角形，中图是平面上的直线三角形，右图是球面上的八分之一球面。"},
        {"k": 2, "note": "先只看左下角这一个角：负曲率里它是 {:.1f}°，平坦里是 {:.1f}°，正曲率里是 {:.1f}°。同一个「角」，随空间的弯曲而收缩或膨胀。".format(aa, flat_a, sph_a)},
        {"k": 3, "note": "把三个角加起来：{:.1f}° / {:.1f}° / {:.1f}°。左图少了 {:.1f}°（角亏），右图多了 {:.1f}°（角盈）。".format(hyp_tot, flat_tot, sph_tot, hyp_gap, sph_gap)},
        {"k": 4, "note": "高斯—博内定理把这件事写成一句话：角盈 = 曲率 × 面积。三角形内角和，是一把量曲率的尺子。"},
        {"k": 5, "note": "代入各自的面积与曲率：球面 K=+1、面积 π/2 ⇒ 角盈 {:.2f}°；双曲面 K=−1、面积 {:.3f} ⇒ 角亏 {:.2f}°；平坦 K=0，两者皆为零。三种几何于是统一成一族。".format(sph_gap, hyp_area, hyp_gap)},
    ]
    return {"theme": PAPER, "view": {"xRange": [-3.6, 3.6], "yRange": [-1.55, 1.55],
                                     "pad": {"l": 16, "r": 16, "b": 16, "t": 16},
                                     "equalAspect": True},
            "layers": layers, "steps": steps}


# ================= 第 7 章：群与对称助手 =================

def _rot(p, deg, c=(0.0, 0.0)):
    """把点 p 绕 c 逆时针旋转 deg 度。"""
    a = math.radians(deg)
    dx, dy = p[0] - c[0], p[1] - c[1]
    return (c[0] + dx * math.cos(a) - dy * math.sin(a),
            c[1] + dx * math.sin(a) + dy * math.cos(a))


def _reflect(p, axis_deg, c=(0.0, 0.0)):
    """把点 p 关于「过 c、方位角 axis_deg」的直线作镜像。"""
    a = math.radians(axis_deg)
    dx, dy = p[0] - c[0], p[1] - c[1]
    u = dx * math.cos(a) + dy * math.sin(a)          # 沿轴分量（镜像时保持）
    v = -dx * math.sin(a) + dy * math.cos(a)         # 垂直分量（镜像时反号）
    return (c[0] + u * math.cos(a) + v * math.sin(a),
            c[1] + u * math.sin(a) - v * math.cos(a))


def _perm_mul(g, h):
    """从左到右复合置换：先做 g，再做 h。"""
    return tuple(h[g[i]] for i in range(len(g)))


def _d3():
    """正三角形的对称群 D3（同构于 S3）：6 个元素的名字、置换、凯莱表。

    顶点编号 0/1/2 = A/B/C，置换 p 满足 p[i] = 顶点 i 的像。
    r = 逆时针转 120°，s = 关于过 A 的轴对折。
    """
    els = [("e", (0, 1, 2)), ("r", (1, 2, 0)), ("r²", (2, 0, 1)), ("s", (0, 2, 1)),
           ("sr", _perm_mul((0, 2, 1), (1, 2, 0))),        # 先 s 再 r
           ("sr²", _perm_mul((0, 2, 1), (2, 0, 1)))]       # 先 s 再 r²
    names = [n for n, _ in els]
    perms = [p for _, p in els]
    assert len(set(perms)) == 6, "D3 的 6 个元素必须互不相同"
    tbl = [[names[perms.index(_perm_mul(g, h))] for h in perms] for g in perms]
    return names, perms, tbl


def _nth_roots(n):
    """x^n = 1 的 n 个根（单位圆上的正 n 边形顶点）。"""
    return [[math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n)]
            for k in range(n)]


def _cubic_roots():
    """x³ − 2 = 0 的三个根：α = ∛2，β = αω，γ = αω²（ω = e^{2πi/3}）。"""
    al = 2 ** (1 / 3)
    wr, wi = -0.5, math.sqrt(3) / 2
    return (al, 0.0), (al * wr, al * wi), (al * wr, -al * wi)


def fig_roots():
    """x^n = 1 的根等分单位圆 —— 解方程其实是在画正 n 边形。"""
    xr, yr = (-3.4, 3.4), (-1.3, 1.3)
    SUP = {1: "", 2: "²", 3: "³", 4: "⁴"}
    LAB_R = {3: 1.12, 4: 1.22, 5: 1.32}    # 各步标签半径错开，见下方注释
    layers = [
        {"geom": "line", "data": _clip_seg((-1.18, 0), (1.18, 0), xr, yr),
         "stroke": DIM, "width": 1.2},
        {"geom": "line", "data": _clip_seg((0, -1.18), (0, 1.18), xr, yr),
         "stroke": DIM, "width": 1.2},
        {"geom": "line", "data": _circle(0, 0, 1), "stroke": RULE, "width": 1.4, "dash": True},
        {"geom": "text", "x": 1.30, "y": -0.18, "text": "Re", "align": "left",
         "size": 10, "color": DIM, "dy": 0},
        {"geom": "text", "x": 0.12, "y": 1.26, "text": "Im", "align": "left",
         "size": 10, "color": DIM, "dy": 0},
    ]
    for n, cond in ((3, "k == 1"), (4, "k == 2"), (5, "k >= 3")):
        pts = _nth_roots(n)
        lr = LAB_R[n]                      # 三个 n 的标签半径错开，避免互相压字
        layers.append({"geom": "line", "when": cond, "data": pts + [pts[0]],
                       "stroke": ACCENT, "width": 2.2})
        layers.append({"geom": "point", "when": cond,
                       "data": [{"x": x, "y": y} for x, y in pts], "r": 5.5, "fill": ACCENT})
        for k, (x, y) in enumerate(pts):
            a = math.atan2(y, x)
            lab = "1" if k == 0 else ("ζ" if k == 1 else f"ζ{SUP[k]}")
            layers.append({"geom": "text", "when": cond,
                           "x": lr * math.cos(a), "y": lr * math.sin(a),
                           "text": lab, "align": "center", "size": 11, "color": ACCENT, "dy": 0})
    # 正五边形的 5 条对称轴：奇数边时每条轴都过「一个顶点 + 它的对边中点」，
    # 因此轴的方向与顶点方向完全相同。角度直接从根现算，绝不另写一组数。
    for vx, vy in _nth_roots(5):
        a = math.atan2(vy, vx)
        seg = _clip_seg((-1.06 * math.cos(a), -1.06 * math.sin(a)),
                        (1.06 * math.cos(a), 1.06 * math.sin(a)),
                        xr, yr)
        if seg:
            layers.append({"geom": "line", "when": "k >= 4", "data": seg,
                           "stroke": TEAL, "width": 1.4, "dash": True})
    layers += [
        {"geom": "text", "when": "k >= 1", "x": -1.62, "y": 1.05, "text": "n 个根等分单位圆",
         "align": "right", "size": 11, "color": DIM, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": -1.62, "y": -1.05, "text": "方程 x⁵ = 1",
         "align": "right", "size": 12, "color": INK, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": 1.50, "y": 1.05, "text": "根 = 正五边形的顶点",
         "align": "left", "size": 11, "color": INK, "dy": 0},
        {"geom": "text", "when": "k >= 4", "x": 1.50, "y": 0.55, "text": "5 条对称轴",
         "align": "left", "size": 11, "color": TEAL, "dy": 0},
        {"geom": "text", "when": "k >= 5", "x": 1.50, "y": -0.55,
         "text": "旋转 5 + 反射 5 = 10 个操作", "align": "left", "size": 11,
         "color": ACCENT, "dy": 0},
    ]
    steps = [
        {"k": 1, "note": "解 x³ − 1 = 0。三个根不是随便三个点，它们把单位圆三等分——一个正三角形。"},
        {"k": 2, "note": "解 x⁴ − 1 = 0，得到正方形；xⁿ = 1 的根永远是正 n 边形的顶点。"},
        {"k": 3, "note": "解 x⁵ − 1 = 0，得到正五边形。注意：根不是散落的点，而是<b>成团</b>的、带着对称的。"},
        {"k": 4, "note": "正五边形有 5 条对称轴：每条穿过一个顶点与它的对边中点。对折后图形与原来完全重合。"},
        {"k": 5, "note": "再加上 5 个旋转（0°、72°、144°、216°、288°），一共 10 个对称操作。<b>方程自带对称性</b>——伽罗瓦的全部工作，就是把这个对称性算出来。"},
    ]
    return {"theme": PAPER, "view": {"xRange": list(xr), "yRange": list(yr),
                                     "pad": {"l": 16, "r": 16, "b": 16, "t": 16},
                                     "equalAspect": True},
            "layers": layers, "steps": steps}


def fig_symmetry():
    """正三角形的 6 个对称操作 —— 一个物体的全部对称构成一个群。"""
    R = 0.40
    V = [_rot((0.0, R), 120 * k) for k in range(3)]      # A/B/C 三个顶点
    OPS = [("e", lambda p: p, "k >= 1", -2.45, 0.72),
           ("r（转 120°）", lambda p: _rot(p, 120), "k >= 2", 0.0, 0.72),
           ("r²（转 240°）", lambda p: _rot(p, 240), "k >= 2", 2.45, 0.72),
           ("s_A（过 A 对折）", lambda p: _reflect(p, 90), "k >= 3", -2.45, -0.78),
           ("s_B（过 B 对折）", lambda p: _reflect(p, 210), "k >= 3", 0.0, -0.78),
           ("s_C（过 C 对折）", lambda p: _reflect(p, 330), "k >= 3", 2.45, -0.78)]
    layers = []
    for name, f, cond, cx, cy in OPS:
        tv = [[cx + p[0], cy + p[1]] for p in V]
        layers.append({"geom": "line", "when": cond, "data": tv + [tv[0]],
                       "stroke": DIM, "width": 1.6})
        layers.append({"geom": "point", "when": cond,
                       "data": [{"x": p[0], "y": p[1]} for p in tv], "r": 3, "fill": INK})
        for lab, v in zip("ABC", V):
            q = f(v)
            layers.append({"geom": "text", "when": cond, "x": cx + q[0] * 1.30,
                           "y": cy + q[1] * 1.30, "text": lab, "align": "center",
                           "size": 11, "color": ACCENT, "dy": 0})
        layers.append({"geom": "text", "when": cond, "x": cx, "y": cy + 0.70,
                       "text": name, "align": "center", "size": 10.5, "color": INK, "dy": 0})
    layers += [
        {"geom": "text", "when": "k >= 4", "x": 0.0, "y": -1.45,
         "text": "封闭：任意两个操作复合，仍然是这 6 个之一", "align": "center",
         "size": 11, "color": GOOD, "dy": 0},
        {"geom": "text", "when": "k >= 5", "x": 0.0, "y": -1.80,
         "text": "有单位元、每个操作都能撤销 —— 这就是群 D₃（≅ S₃）",
         "align": "center", "size": 11, "color": ACCENT, "dy": 0},
    ]
    steps = [
        {"k": 1, "note": "什么都不做，也是一种操作：恒等 e。三角形原封不动。"},
        {"k": 2, "note": "再加两个旋转：转 120° 和转 240°。三个顶点 A、B、C 循环了一圈，图形却与原来重合。"},
        {"k": 3, "note": "还有三个「对折」：分别沿过 A、过 B、过 C 的高对折。注意每个反射只交换两个顶点、固定第三个——这与旋转的循环完全不同。"},
        {"k": 4, "note": "一共 6 个操作，不多不少。<b>封闭</b>：随便复合两个，结果一定还是这 6 个里的某一个，绝不会跑出去。"},
        {"k": 5, "note": "恒等 e 是单位元；每个操作都有逆（转 120° 的逆是转 240°，对折的逆是它自己）。这四条性质——封闭、结合、有单位、有逆——就是<b>群</b>的定义。"},
    ]
    return {"theme": PAPER, "view": {"xRange": [-3.6, 3.6], "yRange": [-2.1, 1.5],
                                     "pad": {"l": 16, "r": 16, "b": 16, "t": 16},
                                     "equalAspect": True},
            "layers": layers, "steps": steps}


def cayley_values():
    """D₃ 的规模 —— 正文与图形共用。"""
    names, _, tbl = _d3()
    n = len(names)
    return {"n": n, "cells": n * n}


def fig_cayley():
    """凯莱表：把 D3 的乘法写成 6×6 的表，四条公理一目了然。"""
    names, _, tbl = _d3()
    CW = 0.44
    ORIGIN = (0.9, 0.45)
    idx = {n: i for i, n in enumerate(names)}

    def matrix(hl, cond, fill):
        return {"geom": "matrix", "when": cond, "values": tbl, "rows": 6, "cols": 6,
                "cellW": CW, "cellH": CW, "origin": list(ORIGIN),
                "highlight": hl, "hlFill": fill, "hlEdge": fill,
                "colHeaders": names, "rowHeaders": names, "fontSize": 11}

    layers = [
        matrix([], "k == 1", GOOD),
        matrix([[0, c] for c in range(6)] + [[r, 0] for r in range(1, 6)],
               "k == 2", GOOD),
        matrix([[idx["r"], c] for c in range(6)], "k == 3", ACCENT),
        matrix([[idx["s"], idx["r"]], [idx["r"], idx["s"]]], "k >= 4", BAD),
        {"geom": "text", "when": "k >= 1", "x": 4.4, "y": 3.35,
         "text": "正三角形的对称群 D₃（≅ S₃）：6 个元素", "align": "left", "size": 11,
         "color": INK, "dy": 0, "weight": "bold"},
        {"geom": "text", "when": "k >= 2", "x": 4.4, "y": 2.55,
         "text": "第一行 / 第一列 = 单位元 e 原样照抄", "align": "left", "size": 11,
         "color": GOOD, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": 4.4, "y": 1.55,
         "text": "每一行都是 6 个元素的重排", "align": "left", "size": 11,
         "color": ACCENT, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": 4.4, "y": 1.20,
         "text": "所以每个元素都有逆 ✓", "align": "left", "size": 11,
         "color": ACCENT, "dy": 0},
        {"geom": "text", "when": "k >= 4", "x": 4.4, "y": 0.60,
         "text": "s·r = sr，而 r·s = sr²", "align": "left", "size": 12,
         "color": BAD, "dy": 0, "weight": "bold"},
        {"geom": "text", "when": "k >= 4", "x": 4.4, "y": 0.25,
         "text": "顺序一换，结果就不同 ⇒ 不交换", "align": "left", "size": 11,
         "color": BAD, "dy": 0},
        {"geom": "text", "when": "k >= 5", "x": 0.9, "y": 3.35,
         "text": "结合律在表上看不出来，但它确实成立", "align": "left", "size": 10.5,
         "color": DIM, "dy": 0},
    ]
    steps = [
        {"k": 1, "note": "把群的乘法写成一张表：行是「先做的操作」，列是「后做的操作」，格子里是复合的结果。6 行 6 列，密密麻麻 36 格。"},
        {"k": 2, "note": "第一行和第一列与表头一模一样——那就是单位元 e：先做 e 或后做 e，都等于什么都没做。<b>群必有单位元。</b>"},
        {"k": 3, "note": "任取一行（这里是 r 那一行），6 个元素<b>恰好各出现一次</b>，一个不漏、一个不重。既然 e 在这一行里出现，就说明每个元素都有逆。<b>群必有逆元。</b>"},
        {"k": 4, "note": "看这两格：先 s 后 r 得到 sr，先 r 后 s 却得到 sr²。<b>顺序不同，结果不同</b>——这个群不交换。乘法表把这件事变成了一件可以指给人看的小事。"},
        {"k": 5, "note": "表里看不出结合律 (ab)c = a(bc)，但它成立。于是「封闭、结合、有单位、有逆」四条，就是群的全部公理——我们已经不再关心这些操作对三角形做了什么，只关心这张表。"},
    ]
    return {"theme": PAPER, "view": {"xRange": [-0.2, 8.0], "yRange": [0, 3.6],
                                     "pad": {"l": 16, "r": 16, "b": 16, "t": 16},
                                     "equalAspect": True},
            "layers": layers, "steps": steps}


def fig_galois():
    """x³ − 2 的根与它的伽罗瓦群：系数只看得见根的对称性。"""
    A, B, C = _cubic_roots()
    SC, CX = 0.9, -2.0

    def tp(p):
        return [CX + SC * p[0], SC * p[1]]

    edges = [tp(A), tp(B), tp(C), tp(A)]
    layers = [
        {"geom": "line", "data": _clip_seg((-3.9, 0), (-0.3, 0), (-4.2, 4.2), (-1.7, 1.7)),
         "stroke": DIM, "width": 1.2},
        {"geom": "line", "data": _clip_seg((CX, -1.35), (CX, 1.35), (-4.2, 4.2), (-1.7, 1.7)),
         "stroke": DIM, "width": 1.2},
        {"geom": "text", "x": -3.85, "y": 1.45, "text": "x³ − 2 = 0", "align": "left",
         "size": 14, "color": INK, "dy": 0, "weight": "bold"},
        {"geom": "point", "data": [tp(A)], "r": 6, "fill": ACCENT},
        {"geom": "text", "x": tp(A)[0], "y": -0.22, "text": "α = ∛2", "align": "center",
         "size": 11, "color": ACCENT, "dy": 0},
    ]
    layers += [
        {"geom": "line", "when": "k >= 2", "data": edges, "stroke": ACCENT2, "width": 2.0},
        {"geom": "point", "when": "k >= 2", "data": [tp(B), tp(C)], "r": 6, "fill": ACCENT2},
        {"geom": "text", "when": "k >= 2", "x": tp(B)[0], "y": 1.16, "text": "β",
         "align": "center", "size": 12, "color": ACCENT2, "dy": 0},
        {"geom": "text", "when": "k >= 2", "x": tp(C)[0], "y": -1.16, "text": "γ",
         "align": "center", "size": 12, "color": ACCENT2, "dy": 0},
        {"geom": "text", "when": "k >= 3", "x": 0.7, "y": 1.30, "text": "系数 = 根的对称函数",
         "align": "left", "size": 12, "color": INK, "dy": 0, "weight": "bold"},
        {"geom": "text", "when": "k >= 3", "x": 0.7, "y": 0.95, "text": "e₁ = α + β + γ = 0",
         "align": "left", "size": 11, "color": INK, "dy": 0, "weight": "normal"},
        {"geom": "text", "when": "k >= 3", "x": 0.7, "y": 0.62,
         "text": "e₂ = αβ + αγ + βγ = 0", "align": "left", "size": 11, "color": INK,
         "dy": 0, "weight": "normal"},
        {"geom": "text", "when": "k >= 3", "x": 0.7, "y": 0.29, "text": "e₃ = αβγ = 2",
         "align": "left", "size": 11, "color": INK, "dy": 0, "weight": "normal"},
        {"geom": "text", "when": "k >= 3", "x": 0.7, "y": -0.05,
         "text": "⇒ 方程就是 x³ − 2 = 0", "align": "left", "size": 11, "color": DIM, "dy": 0},
        {"geom": "line", "when": "k >= 4",
         "data": _ray_arc(tp(B)[0], (tp(B)[1] + tp(C)[1]) / 2, 0.30, 90, 270),
         "stroke": ACCENT2, "width": 2.0, "dash": True},
        {"geom": "text", "when": "k >= 4", "x": 0.7, "y": -0.70,
         "text": "把 β、γ 的名字对调，三个数纹丝不动 ✓", "align": "left", "size": 11,
         "color": GOOD, "dy": 0},
        {"geom": "text", "when": "k >= 5", "x": 0.7, "y": -1.10,
         "text": "系数只看得见「能怎么换」", "align": "left", "size": 11, "color": INK,
         "dy": 0, "weight": "bold"},
        {"geom": "text", "when": "k >= 5", "x": 0.7, "y": -1.45,
         "text": "伽罗瓦群 = S₃（6 个置换）", "align": "left", "size": 11,
         "color": ACCENT, "dy": 0},
    ]
    steps = [
        {"k": 1, "note": "解 x³ − 2 = 0。第一个根是实数 α = ∛2 ≈ 1.260，就落在实轴上。"},
        {"k": 2, "note": "另外两个根是 β = αω 与 γ = αω²（ω 是三次单位根）。三点连起来是一个正三角形——又是<b>成团</b>的。"},
        {"k": 3, "note": "三次方程的三个系数，恰好就是根的三个<b>对称函数</b>：和 = 0，两两积之和 = 0，乘积 = 2。系数是把三个根「搅在一起」得到的，它抹掉了谁是谁。"},
        {"k": 4, "note": "把 β 和 γ 的名字对调——这是根的一个<b>置换</b>。可三个对称函数一个数都没变：系数根本分不清 β 和 γ。"},
        {"k": 5, "note": "三次方程的根有 3! = 6 种编号方式，而系数对这 6 种完全无感。<b>方程能看见的，不是根本身，而是根的对称性</b>——这个对称群（这里是 S₃）就是伽罗瓦群。"},
    ]
    return {"theme": PAPER, "view": {"xRange": [-4.2, 4.2], "yRange": [-1.7, 1.7],
                                     "pad": {"l": 16, "r": 16, "b": 16, "t": 16},
                                     "equalAspect": True},
            "layers": layers, "steps": steps}


def fig_tower():
    """可解塔：三次、四次修得通，五次断在 A₅。"""
    fact = math.factorial
    COLS = [-2.9, 0.0, 2.9]
    CW_, CH_ = 2.1, 1.0
    # 每一列从上往下的盒子（最上面是 S_n）
    TOWERS = {
        0: [("S₃", fact(3)), ("A₃", fact(3) // 2), ("{e}", 1)],
        1: [("S₄", fact(4)), ("A₄", fact(4) // 2), ("V₄", 4), ("{e}", 1)],
        2: [("S₅", fact(5)), ("A₅", fact(5) // 2), ("{e}", 1)],
    }
    QUOT = {0: [2, 3], 1: [2, 3, 4], 2: [2, None]}   # None = 塔断了
    layers, nodes = [], []

    def slot(i, n):
        """第 i 个盒子（i=0 是最上面那个，自上而下）的世界 y 范围。"""
        y0 = 0.3 + (n - 1 - i) * 1.62
        return y0, y0 + CH_

    for col, items in TOWERS.items():
        n = len(items)
        for i, (nm, order) in enumerate(items):
            y0, _ = slot(i, n)
            nodes.append({"id": f"c{col}{i}", "x": COLS[col] - CW_ / 2, "y": y0,
                          "w": CW_, "h": CH_, "label": nm, "sub": f"阶 {order}",
                          "edge": INK, "fill": "#ffffff", "on": True})
        for j in range(n - 1):
            q = QUOT[col][j]                      # 第 j 级商群的阶
            gy = (slot(j, n)[0] + slot(j + 1, n)[1]) / 2   # 两盒缝隙的中线
            if q is None:                         # 塔断：画一条虚线断口，不画箭头
                layers.append({"geom": "line", "when": f"k >= {col + 1}",
                               "data": [[COLS[col], slot(j, n)[0]],
                                        [COLS[col], slot(j + 1, n)[1]]],
                               "stroke": BAD, "width": 2.2, "dash": True})
            else:
                layers.append({"geom": "arrow", "when": f"k >= {col + 1}", "nodes": nodes,
                               "width": 1.8, "stroke": GOOD,
                               "data": [{"from": f"c{col}{j}", "to": f"c{col}{j + 1}",
                                         "dir": "v", "color": GOOD, "width": 1.8}]})
            layers.append({"geom": "text", "when": f"k >= {col + 1}",
                           "x": COLS[col] + 0.78, "y": gy,
                           "text": f"商 {q}" if q else "✗ 断了", "align": "left",
                           "size": 11, "color": GOOD if q else BAD, "dy": 0,
                           "weight": "bold"})
        layers.append({"geom": "text", "when": f"k >= {col + 1}", "x": COLS[col],
                       "y": 6.72, "text": f"n = {col + 3}", "align": "center",
                       "size": 12, "color": INK, "dy": 0, "weight": "bold"})
    layers += [
        {"geom": "card", "when": "k >= 1", "data": nodes},
        {"geom": "text", "when": "k >= 4", "x": 0.0, "y": -0.45,
         "text": "A₅ 是 60 阶的非交换单群：没有任何非平凡正规子群",
         "align": "center", "size": 11, "color": BAD, "dy": 0, "weight": "bold"},
        {"geom": "text", "when": "k >= 5", "x": 0.0, "y": -1.15,
         "text": "有根式解 ⟺ 这座塔能一路修到底（每一级的商都是交换群）",
         "align": "center", "size": 11.5, "color": ACCENT, "dy": 0, "weight": "bold"},
    ]
    steps = [
        {"k": 1, "note": "三次方程：S₃ 有两个子层 A₃ 与 {e}，商的阶是 2 和 3——都是素数，因此都是循环群、当然交换。塔修通了，三次方程有根式解。"},
        {"k": 2, "note": "四次方程：塔有四级，商的阶 2、3、4，全是交换群。<b>塔又通了</b>——这就是卡尔达诺与费拉里找到的四次公式。"},
        {"k": 3, "note": "五次方程：S₅ 到 A₅ 这一级没问题，商的阶是 2，交换。看起来又能一路修下去。"},
        {"k": 4, "note": "<b>然后就断了。</b>A₅ 是 60 阶的非交换单群：它没有任何非平凡的正规子群，所以从 A₅ 到 {e} 之间修不出任何一级。塔断在这里。"},
        {"k": 5, "note": "伽罗瓦的判据：一个方程有根式解，当且仅当它的伽罗瓦群「可解」——也就是这座塔能修到底。S₃、S₄ 可解，<b>S₅ 不可解</b>。于是阿贝尔与鲁菲尼的断言有了真正的解释：五次方程不是还没找到公式，而是<b>根本没有</b>根式公式。"},
    ]
    return {"theme": PAPER, "view": {"xRange": [-4.2, 4.2], "yRange": [-1.7, 7.6],
                                     "pad": {"l": 16, "r": 16, "b": 16, "t": 16}},
            "layers": layers, "steps": steps}


FIGS = {
    # 第 1 章
    "fig-crisis": fig_crisis,
    "fig-sqrt2": fig_sqrt2,
    "fig-complex": fig_complex,
    "fig-nesting": fig_nesting,
    "fig-timeline": fig_timeline,
    # 第 2 章
    "fig-zeno": fig_zeno,
    "fig-hilbert": fig_hilbert,
    "fig-cardinality": fig_cardinality,
    # 第 3 章
    "fig-euclid": fig_euclid,
    "fig-induction": fig_induction,
    "fig-godel": fig_godel,
    # 第 4 章
    "fig-instant": fig_instant,
    "fig-secant": fig_secant,
    "fig-berkeley": fig_berkeley,
    "fig-epsilon-delta": fig_epsilon_delta,
    "fig-riemann": fig_riemann,
    # 第 5 章
    "fig-dice": fig_dice,
    "fig-galton": fig_galton,
    "fig-lln": fig_lln,
    "fig-bertrand": fig_bertrand,
    "fig-axioms": fig_axioms,
    # 第 6 章
    "fig-fifth": fig_fifth,
    "fig-hyperbolic": fig_hyperbolic,
    "fig-sphere": fig_sphere,
    "fig-poincare": fig_poincare,
    "fig-curvature": fig_curvature,
    # 第 7 章
    "fig-roots": fig_roots,
    "fig-symmetry": fig_symmetry,
    "fig-cayley": fig_cayley,
    "fig-galois": fig_galois,
    "fig-tower": fig_tower,
}


# =====================================================================
# 第 8 章插图：计算 —— 从机械到可计算
# =====================================================================
# 字母表 A：0^n1^n 判定器（空白、0、1、划掉记号 X）
MA_SYM = ["_", "0", "1", "X"]
MA_SI = {s: i for i, s in enumerate(MA_SYM)}
MA_BLANK = "_"

# 字母表 B：停机矩阵。空白放在最后，于是「编码里的数字 k」喂到纸带上
# 读到的正是符号 k —— 机器因此可以直接「见 2 就停」。
MB_SYM = ["0", "1", "2", "_"]
MB_SI = {s: i for i, s in enumerate(MB_SYM)}
MB_BLANK = "_"
QHALT = "qh"


def _tm_run(delta, tape_init, start, halt, blank, max_steps=10000):
    """真跑一台图灵机。返回 (快照列表, 终态)，快照是 (纸带字典, 读写头, 状态)。

    纸带用「绝对位置 → 符号」的字典表示，往左补空白不会让整条带子错位。
    """
    tape = {i: ch for i, ch in enumerate(tape_init)}
    head, state = 0, start
    snaps = [(dict(tape), head, state)]
    for _ in range(max_steps):
        if state in halt:
            return snaps, "halt"
        sym = tape.get(head, blank)
        if (state, sym) not in delta:
            return snaps, "stuck"          # 规则表没写这一条：机器停在这里
        ns, nsym, dr = delta[(state, sym)]
        tape[head] = nsym
        head += 1 if dr == "R" else -1
        state = ns
        snaps.append((dict(tape), head, state))
    return snaps, ("halt" if state in halt else "limit")


def _encode(states, delta, si):
    """转移表 → 定长数字串：每个转移 5 位（态 符 态 符 向）。"""
    sti = {s: i for i, s in enumerate(states)}
    rows = sorted((sti[a], si[b], sti[c], si[d], 1 if dr == "R" else 0)
                  for (a, b), (c, d, dr) in delta.items())
    return "".join("%d%d%d%d%d" % r for r in rows)


def _decode(code, states, sym):
    """数字串 → 转移表（往返必须还原，图上会当场校验）。"""
    inv = {k: v for k, v in enumerate(states)}
    delta = {}
    for i in range(0, len(code), 5):
        a, b, c, d, e = (int(ch) for ch in code[i:i + 5])
        delta[(inv[a], sym[b])] = (inv[c], sym[d], "R" if e else "L")
    return delta


def _rule(key, delta):
    a, b = key
    c, d, dr = delta[key]
    return "%s,%s → %s,%s %s" % (a, b, c, d, "▶" if dr == "R" else "◀")


def _halts(delta, tape_init, start, halt, blank, max_steps=400):
    """判定机器在给定输入上是否停机。

    返回 (会停机?, 步数, 依据)。永不停机的结论来自「配置重复」——确定性机器
    只要回到同一个（状态 + 以读写头为原点的纸带），此后就必然无限重复。
    """
    tape = {i: ch for i, ch in enumerate(tape_init)}
    head, state, steps = 0, start, 0
    seen = set()
    while steps < max_steps:
        if state in halt:
            return True, steps, "到达停机态"
        cfg = (state, tuple(sorted((p - head, s) for p, s in tape.items())))
        if cfg in seen:
            return False, steps, "配置重复"
        seen.add(cfg)
        sym = tape.get(head, blank)
        if (state, sym) not in delta:
            return True, steps, "规则未写 → 停住"
        ns, nsym, dr = delta[(state, sym)]
        tape[head] = nsym
        head += 1 if dr == "R" else -1
        state = ns
        steps += 1
    return None, steps, "步数上限"


# ---- 判定 0^n 1^n 的图灵机 ----
MQ_STATES = ["q0", "q1", "q2", "qc", "qa", "qr"]
MQ_HALTS = {"qa", "qr"}
MQ_DELTA = {
    ("q0", "X"): ("q0", "X", "R"), ("q0", "0"): ("q1", "X", "R"),
    ("q0", "1"): ("qr", "1", "R"), ("q0", MA_BLANK): ("qc", MA_BLANK, "R"),
    ("q1", "0"): ("q1", "0", "R"), ("q1", "1"): ("q2", "X", "L"),
    ("q1", "X"): ("q1", "X", "R"), ("q1", MA_BLANK): ("qr", MA_BLANK, "R"),
    ("q2", "0"): ("q2", "0", "L"), ("q2", "1"): ("q2", "1", "L"),
    ("q2", "X"): ("q2", "X", "L"), ("q2", MA_BLANK): ("q0", MA_BLANK, "R"),
    ("qc", "X"): ("qc", "X", "R"), ("qc", MA_BLANK): ("qa", MA_BLANK, "R"),
    ("qc", "0"): ("qr", "0", "R"), ("qc", "1"): ("qr", "1", "R"),
}
MQ_ROWS = [("q0", "X"), ("q0", "0"), ("q0", "1"), ("q0", MA_BLANK),
           ("q1", "0"), ("q1", "1"), ("q1", "X"), ("q1", MA_BLANK),
           ("q2", "0"), ("q2", "1"), ("q2", "X"), ("q2", MA_BLANK),
           ("qc", "X"), ("qc", MA_BLANK), ("qc", "0"), ("qc", "1")]
assert sorted(MQ_ROWS) == sorted(MQ_DELTA)


def fig_machine():
    """判定 0^n1^n 的图灵机真跑一遍：纸带 + 空间-时间轨迹 + 转移表逐条高亮。"""
    snaps, status = _tm_run(MQ_DELTA, "0011", "q0", MQ_HALTS, MA_BLANK)
    assert status == "halt" and snaps[-1][2] == "qa", "0011 必须被接受"
    heads = [h for _t, h, _s in snaps]
    keys = set()
    for t, _h, _s in snaps:
        keys |= set(t)
    lo = min(min(heads), min(keys)) - 1
    hi = max(max(heads), max(keys)) + 1
    n = len(snaps) - 1
    ncell = hi - lo + 1

    CW = 0.95                      # 纸带格子边长（世界单位，equalAspect 下是正方形）
    TX, TY = 0.55, 7.95            # 纸带左下角
    SY0, SY1 = 6.55, 1.25          # 空间-时间图：第 0 步在上，第 n 步在下
    DX, DY = 11.0, 9.35            # 转移表左上角

    def cellx(col):
        return TX + (col + 0.5) * CW

    def stepty(t):
        return SY0 - t * (SY0 - SY1) / n

    layers = [
        {"geom": "text", "x": TX, "y": 9.72, "text": "纸带（输入 0011）· □ 是空白",
         "align": "left", "size": 10.5, "color": DIM, "weight": "normal"},
        {"geom": "text", "x": DX, "y": 9.72, "text": "转移表 δ —— 机器的全部内脏（16 条规则）",
         "align": "left", "size": 10.5, "color": DIM, "weight": "normal"},
        {"geom": "text", "x": TX, "y": 7.02, "text": "读写头走过的路（上=第 0 步，下=第 %d 步）" % n,
         "align": "left", "size": 10.5, "color": DIM, "weight": "normal"},
    ]
    steps = []

    for t, (tape, head, state) in enumerate(snaps):
        vals = [["□" if tape.get(p, MA_BLANK) == MA_BLANK else tape.get(p, MA_BLANK)
                 for p in range(lo, hi + 1)]]
        col = head - lo
        layers.append({"geom": "matrix", "when": f"k == {t}", "rows": 1, "cols": ncell,
                       "cellW": CW, "cellH": CW, "origin": [TX, TY], "values": vals,
                       "highlight": [[0, col]], "hlFill": "#b45309",
                       "hlEdge": "#7c3a05", "cellFill": "#ffffff",
                       "cellEdge": "#e7e0d5", "textColor": "#1f1b16"})
        layers.append({"geom": "point", "when": f"k == {t}",
                       "data": [{"x": cellx(col), "y": 7.42, "r": 6, "fill": "#b45309"}]})
        sym = tape.get(head, MA_BLANK)
        ri = MQ_ROWS.index((state, sym)) if (state, sym) in MQ_ROWS else -1
        rule = _rule((state, sym), MQ_DELTA) if ri >= 0 else "停机：状态 %s" % state
        # 读数窗用 matrix：文字居中画在格子里，不会被 W1 判成「同一水平带重叠」
        layers.append({"geom": "matrix", "when": f"k == {t}", "rows": 1, "cols": 2,
                       "cellW": 2.9, "cellH": 0.72, "origin": [DX, 0.32],
                       "values": [["当前状态 %s" % state, "第 %d / %d 步" % (t, n)]],
                       "cellFill": "#fffbeb", "cellEdge": "#b45309",
                       "textColor": "#1f1b16"})
        if ri >= 0:
            yrow = DY - 0.30 - ri * 0.50
            layers.append({"geom": "region", "when": f"k == {t}",
                           "x": [DX - 0.18, DX + 9.4], "y": [yrow - 0.22, yrow + 0.22],
                           "fill": "#fde9d0", "outline": True, "stroke": "#b45309"})
        # 空间-时间轨迹：这一条是真正逐帧增长的部分
        if t > 0:
            layers.append({"geom": "line", "when": f"k >= {t}",
                           "data": [[cellx(heads[t - 1]), stepty(t - 1)],
                                    [cellx(head), stepty(t)]],
                           "stroke": "#6d28d9", "width": 1.6})
        layers.append({"geom": "point", "when": f"k == {t}",
                       "data": [{"x": cellx(head), "y": stepty(t), "r": 4.5,
                                 "fill": "#6d28d9"}]})
        note = ("划掉一个 0，去配对" if (state, sym) == ("q0", "0")
                else "划掉一个 1，配成一对" if (state, sym) == ("q1", "1")
                else "回到最左端" if state == "q2"
                else "检查是否还剩没配对的" if state == "qc"
                else "起步" if t == 0 else "")
        steps.append({"k": t, "note": note or ("第 %d 步：%s" % (t, rule))})

    for i in range(ncell):
        layers.append({"geom": "text", "x": cellx(i), "y": TY + CW + 0.16,
                       "text": str(lo + i), "align": "center", "size": 9,
                       "color": DIM, "weight": "normal"})
    for i, k in enumerate(MQ_ROWS):
        layers.append({"geom": "text", "x": DX, "y": DY - 0.30 - i * 0.50,
                       "text": _rule(k, MQ_DELTA), "align": "left", "size": 10,
                       "color": INK, "weight": "normal"})
    layers.append({"geom": "text", "when": f"k >= {n}", "x": TX, "y": 0.32,
                   "text": "停在接受态 qa —— 输入 0011 属于 L = {0ⁿ1ⁿ}，共 %d 步" % n,
                   "align": "left", "size": 11.5, "color": GOOD})
    return {"theme": PAPER,
            "view": {"xRange": [0, 20.6], "yRange": [0, 10], "equalAspect": True,
                     "pad": {"l": 16, "r": 16, "b": 10, "t": 10}},
            "layers": layers, "steps": steps}


# ---- 停机矩阵用的四台真机 ----
def _p0():
    """见 2 就停机；找不到就一路左退，在纸带左端来回摆。"""
    d = {("q0", "2"): (QHALT, "2", "R"), ("q0", MB_BLANK): ("q1", MB_BLANK, "L"),
         ("q1", MB_BLANK): ("q2", MB_BLANK, "R"), ("q2", MB_BLANK): ("q1", MB_BLANK, "R")}
    for s in ("0", "1"):
        d[("q0", s)] = ("q0", s, "R")
    for s in MB_SYM:
        d[("q1", s)] = ("q2", s, "L")
    for s in ("0", "1", "2"):
        d[("q2", s)] = ("q2", s, "L")
    return d


def _p1():
    """一路向右扫到空白就停机（无条件停机）。"""
    d = {("q0", s): ("q0", s, "R") for s in ("0", "1", "2")}
    d[("q0", MB_BLANK)] = (QHALT, MB_BLANK, "L")
    return d


def _p2():
    """原地摆动：两个状态来回走，永不指向停机态。"""
    d = {}
    for s in MB_SYM:
        d[("q0", s)] = ("q1", s, "L")
        d[("q1", s)] = ("q0", s, "R")
    return d


def _p3():
    """「见 2 就不停」：一路右扫，见到 2 就转入原地摆动；一路没见到 2，扫到空白就停机。

    值得盯住的一点：它必须有一条针对符号 2 的规则，于是它自己的编码里
    必然出现数字 2 —— 它读自己的编码时，一定找得到那个 2。
    转入摆动之后配置立刻重复，所以「永不停」是证明出来的，不是跑够步数猜的。
    """
    WIGGLE, BACK = "q1", "q2"
    d = {("q0", "2"): (WIGGLE, "2", "L"), ("q0", MB_BLANK): (QHALT, MB_BLANK, "L")}
    for s in ("0", "1"):
        d[("q0", s)] = ("q0", s, "R")
    for s in MB_SYM:
        d[(WIGGLE, s)] = (BACK, s, "L")     # 向左退一格
        d[(BACK, s)] = (WIGGLE, s, "R")     # 再向右回一格 —— 配置就此重复
    return d


HALTING = [("见 2 就停", _p0, ["q0", "q1", "q2", QHALT]),
           ("扫到底就停", _p1, ["q0", QHALT]),
           ("原地摆动", _p2, ["q0", "q1"]),
           ("见 2 就不停", _p3, ["q0", "q1", "q2", QHALT])]


# ---- 忙碌海狸 ----
def _bb_prog(prog, n_states, limit=100000):
    """真跑一台二符号图灵机。prog[2*state + sym] = (写, 移动, 下一状态)。

    返回 (纸带字符串, 1 的个数, 步数, 是否停机)。
    """
    tape, head, state, steps = {}, 0, 0, 0
    while steps < limit and state < n_states:
        w, m, ns = prog[2 * state + (1 if tape.get(head, 0) else 0)]
        tape[head] = w
        head += m
        state = ns
        steps += 1
    lo, hi = min(tape), max(tape)
    return ("".join(str(tape.get(k, 0)) for k in range(lo, hi + 1)),
            sum(tape.values()), steps, state >= n_states)


def _bb_enum(n_states, step_limit):
    """穷举全部 n 状态二符号机，返回 (Σ, T, 获胜机, 最长机, 台数, 会停机台数)。"""
    opts = [(w, m, q) for w in (0, 1) for m in (-1, 1) for q in range(n_states + 1)]
    nopt = len(opts)
    total = nopt ** (2 * n_states)
    best, longest, champ, longp, halted = -1, -1, None, None, 0
    for code in range(total):
        c, prog = code, [None] * (2 * n_states)
        for i in range(2 * n_states):
            prog[i] = opts[c % nopt]
            c //= nopt
        tape, head, state, steps = {}, 0, 0, 0
        while steps < step_limit and state < n_states:
            w, m, ns = prog[2 * state + (1 if tape.get(head, 0) else 0)]
            tape[head] = w
            head += m
            state = ns
            steps += 1
        if state >= n_states:
            halted += 1
            ones = sum(tape.values())
            if ones > best:
                best, champ = ones, prog[:]
            if steps > longest:
                longest, longp = steps, prog[:]
    return best, longest, champ, longp, total, halted


def fig_universal():
    """通用图灵机：同一串符号既是数据又是程序。"""
    states = ["q0", QHALT]
    delta = {("q0", "0"): ("q0", "1", "R"), ("q0", MB_BLANK): (QHALT, MB_BLANK, "R")}
    code = _encode(states, delta, MB_SI)
    assert _decode(code, states, MB_SYM) == delta, "编码往返必须还原"
    snaps, status = _tm_run(delta, "00", "q0", {QHALT}, MB_BLANK)
    assert status == "halt" and snaps[-1][0].get(0) == "1" and snaps[-1][0].get(1) == "1"

    layers = []
    steps = []

    # 上：被模拟机器 M 的转移表
    layers += [
        {"geom": "text", "x": 0.6, "y": 9.55, "text": "被模拟的机器 M：把 0 改写成 1，走到空白就停机",
         "align": "left", "size": 11, "color": INK},
        {"geom": "text", "x": 0.6, "y": 8.95, "text": "q0,0 → q0,1 ▶", "align": "left",
         "size": 11, "color": INK, "weight": "normal"},
        {"geom": "text", "x": 0.6, "y": 8.45, "text": "q0,□ → qh,□ ▶", "align": "left",
         "size": 11, "color": INK, "weight": "normal"},
    ]

    # 中：编码规则 + 现场编出来的 E(M)
    layers.append({"geom": "text", "when": "k >= 1", "x": 0.6, "y": 7.75,
                   "text": "编码规则：每个转移固定写成 5 位数字（态 符 态 符 向）",
                   "align": "left", "size": 11, "color": INK})
    layers.append({"geom": "text", "when": "k >= 1", "x": 0.6, "y": 7.25,
                   "text": "q0,0 → q0,1 ▶   编成   0 0 0 1 1",
                   "align": "left", "size": 10.5, "color": ACCENT2, "weight": "normal"})
    layers.append({"geom": "text", "when": "k >= 1", "x": 0.6, "y": 6.78,
                   "text": "q0,□ → qh,□ ▶   编成   0 3 1 3 1",
                   "align": "left", "size": 10.5, "color": ACCENT2, "weight": "normal"})
    layers.append({"geom": "text", "when": "k >= 2", "x": 0.6, "y": 6.05,
                   "text": "E(M) = %s   （%d 位；本页现场编出并解码校验过）"
                           % (" ".join(code), len(code)),
                   "align": "left", "size": 11, "color": ACCENT})

    # 编码串本身画成一条纸带
    layers.append({"geom": "matrix", "when": "k >= 2", "rows": 1, "cols": len(code),
                   "cellW": 0.42, "cellH": 0.42, "origin": [0.6, 5.15],
                   "values": [list(code)], "cellFill": "#ffffff",
                   "cellEdge": "#e7e0d5", "textColor": "#1f1b16"})
    for i, ch in enumerate(code):
        layers.append({"geom": "text", "when": "k >= 2", "x": 0.6 + (i + 0.5) * 0.42,
                       "y": 5.72, "text": str(i // 5 + 1) if i % 5 == 0 else "·",
                       "align": "center", "size": 8.5,
                       "color": ACCENT if i % 5 == 0 else RULE, "weight": "normal"})

    # 下：通用机 U 读这串数字，照着它办事 —— 真跑一遍
    layers.append({"geom": "text", "when": "k >= 3", "x": 0.6, "y": 4.42,
                   "text": "通用机 U 读进 E(M)，照表办事 —— 同一串符号于是既是数据，又是程序",
                   "align": "left", "size": 11, "color": INK})
    for t, (tape, head, state) in enumerate(snaps):
        vals = [list("00□")]
        if t > 0:
            vals[0][t - 1] = "1"
        layers.append({"geom": "matrix", "when": f"k >= {3 + t}", "rows": 1, "cols": 3,
                       "cellW": 0.55, "cellH": 0.55, "origin": [0.6, 3.15],
                       "values": vals, "highlight": [[0, min(head, 2)]],
                       "hlFill": "#b45309", "hlEdge": "#7c3a05",
                       "cellFill": "#ffffff", "cellEdge": "#e7e0d5",
                       "textColor": "#1f1b16"})
    layers.append({"geom": "text", "when": "k >= %d" % (3 + len(snaps)), "x": 0.6,
                   "y": 2.62, "text": "U 模拟 M 跑完：输入 00 变成 11，然后停机。",
                   "align": "left", "size": 11.5, "color": GOOD})
    layers.append({"geom": "text", "when": "k >= 4", "x": 12.5, "y": 3.45,
                   "text": "E(M) 的每 5 位对应 M 的一条规则。", "align": "left",
                   "size": 10.5, "color": DIM, "weight": "normal"})
    layers.append({"geom": "text", "when": "k >= 4", "x": 12.5, "y": 3.0,
                   "text": "U 不需要「知道」M 是谁，", "align": "left", "size": 10.5,
                   "color": DIM, "weight": "normal"})
    layers.append({"geom": "text", "when": "k >= 4", "x": 12.5, "y": 2.55,
                   "text": "它只需要读这串数字。", "align": "left", "size": 10.5,
                   "color": DIM, "weight": "normal"})
    layers.append({"geom": "text", "when": "k >= %d" % (3 + len(snaps)), "x": 12.5,
                   "y": 1.85, "text": "M 是程序，E(M) 是数据，", "align": "left",
                   "size": 11, "color": ACCENT2})
    layers.append({"geom": "text", "when": "k >= %d" % (3 + len(snaps)), "x": 12.5,
                   "y": 1.4, "text": "而 U 把前者变成后者。", "align": "left",
                   "size": 11, "color": ACCENT2})

    steps = [{"k": 0, "note": "被模拟的机器 M 只有两条规则"},
             {"k": 1, "note": "每个转移编成固定 5 位数字"},
             {"k": 2, "note": "整张转移表变成一串数字 E(M)"},
             {"k": 3, "note": "通用机 U 把 E(M) 读进自己的纸带"},
             {"k": 4, "note": "U 照着 E(M) 模拟 M 的每一步"},
             {"k": 5, "note": "模拟结束：同一串符号既是数据又是程序"}]
    return {"theme": PAPER,
            "view": {"xRange": [0, 21.75], "yRange": [0, 10], "equalAspect": True,
                     "pad": {"l": 16, "r": 16, "b": 10, "t": 10}},
            "layers": layers, "steps": steps}


def fig_halting():
    """停机矩阵 + 对角线取反。每一格都是真模拟出来的。"""
    codes = [_encode(st, dl(), MB_SI) for _n, dl, st in HALTING]
    for c in codes:
        assert len(c) % 5 == 0
    # P3「见 2 就不停」之所以一格都不停，是因为四台机器的编码里都带着数字 2 ——
    # 它自己的那条针对 2 的规则，正是它编码里那个 2 的来源。
    assert all("2" in c for c in codes), codes
    kinds, whys = [], []
    for _nm, dl_, _st in HALTING:
        dl = dl_()
        row, wrow = [], []
        for cj in codes:
            h, s, why = _halts(dl, [MB_SYM[int(ch)] for ch in cj], "q0", {QHALT},
                               MB_BLANK, max_steps=2000)
            assert h is not None, "步数耗尽：这一格必须有确定答案"
            row.append(("停·%d" % s) if h else "不停")
            wrow.append(why)
        kinds.append(row)
        whys.append(wrow)
    # 「不停」一律由配置重复证明出来，绝不能是「跑够步数还没停」的猜测
    assert all(w == "配置重复" for i in (2, 3) for w in whys[i]), whys
    diag = [kinds[i][i].split("·")[0] for i in range(4)]
    drow = ["不停" if d == "停" else "停" for d in diag]
    assert diag == ["停", "停", "不停", "不停"], diag
    assert drow == ["不停", "不停", "停", "停"], drow
    # 图上给每一行都写了一句「为什么」，所以整行都得钉死，不能只钉对角线
    assert [k.split("·")[0] for k in kinds[0]] == ["停"] * 4, kinds[0]
    assert [k.split("·")[0] for k in kinds[1]] == ["停"] * 4, kinds[1]
    assert [k.split("·")[0] for k in kinds[2]] == ["不停"] * 4, kinds[2]
    assert [k.split("·")[0] for k in kinds[3]] == ["不停"] * 4, kinds[3]

    OX, OY, CW, CH = 6.6, 2.45, 3.2, 1.12
    layers = [
        {"geom": "text", "x": 0.6, "y": 9.6, "text": "四台真机（每台都只有有限条规则）",
         "align": "left", "size": 11, "color": INK},
        {"geom": "text", "x": 0.6, "y": 9.08, "text": "P0「见 2 就停」：一路右扫，见符号 2 就停机；",
         "align": "left", "size": 10, "color": INK, "weight": "normal"},
        {"geom": "text", "x": 0.6, "y": 8.70, "text": "     找不到 2，就退回左端来回摆。",
         "align": "left", "size": 10, "color": INK, "weight": "normal"},
        {"geom": "text", "x": 0.6, "y": 8.18, "text": "P1「扫到底就停」：一路右扫，见空白就停机。",
         "align": "left", "size": 10, "color": INK, "weight": "normal"},
        {"geom": "text", "x": 0.6, "y": 7.66, "text": "P2「原地摆动」：两个状态来回走，压根不看纸带，",
         "align": "left", "size": 10, "color": INK, "weight": "normal"},
        {"geom": "text", "x": 0.6, "y": 7.28, "text": "     规则里也没有一条指向停机态。",
         "align": "left", "size": 10, "color": INK, "weight": "normal"},
        {"geom": "text", "x": 0.6, "y": 6.76, "text": "P3「见 2 就不停」：见 2 就转入摆动。",
         "align": "left", "size": 10, "color": INK, "weight": "normal"},
        {"geom": "text", "x": 0.6, "y": 6.38, "text": "     一路右扫，见空白才停。可它必须有一条",
         "align": "left", "size": 10, "color": INK, "weight": "normal"},
        {"geom": "text", "x": 0.6, "y": 6.00, "text": "     针对 2 的规则 —— 于是它的编码里必然",
         "align": "left", "size": 10, "color": INK, "weight": "normal"},
        {"geom": "text", "x": 0.6, "y": 5.62, "text": "     带着数字 2：它永远找得到那个 2。",
         "align": "left", "size": 10, "color": INK, "weight": "normal"},
        {"geom": "text", "when": "k >= 1", "x": 0.6, "y": 5.0,
         "text": "每台机器的转移表都编成一串数字，",
         "align": "left", "size": 10.5, "color": ACCENT2},
        {"geom": "text", "when": "k >= 1", "x": 0.6, "y": 4.58,
         "text": "于是另一台机器可以把它读进纸带。",
         "align": "left", "size": 10.5, "color": ACCENT2},
    ]

    layers.append({"geom": "matrix", "when": "k >= 2", "rows": 5, "cols": 4,
                   "cellW": CW, "cellH": CH, "origin": [OX, OY], "values": kinds + [drow],
                   "colHeaders": ["P%d 的编码" % i for i in range(4)],
                   "rowHeaders": ["P%d" % i for i in range(4)] + ["D"],
                   "highlight": [[i, i] for i in range(4)],
                   "hlFill": "#b45309", "hlEdge": "#7c3a05",
                   "cellFill": "#ffffff", "cellEdge": "#e7e0d5",
                   "textColor": "#1f1b16", "fontSize": 10})
    layers.append({"geom": "text", "when": "k >= 2", "x": OX, "y": 9.34,
                   "text": "行 = 谁在跑，列 = 读谁的编码；每一格都是本页真模拟出来的。",
                   "align": "left", "size": 10.5, "color": DIM, "weight": "normal"})
    layers.append({"geom": "text", "when": "k >= 3", "x": OX, "y": 1.85,
                   "text": "对角线：P0 读自己的编码 → 停；P1 → 停；P2 → 不停；P3 → 不停。",
                   "align": "left", "size": 11, "color": ACCENT})
    layers.append({"geom": "text", "when": "k >= 4", "x": OX, "y": 1.32,
                   "text": "D 的定义：在 Pₖ 的编码上，D 干的事与对角线相反。",
                   "align": "left", "size": 11, "color": ACCENT2})
    layers.append({"geom": "text", "when": "k >= 5", "x": OX, "y": 0.68,
                   "text": "若 H 存在，D 就是合法机器 → D 有编号 k → D(D) 必须既停又不停。",
                   "align": "left", "size": 11.5, "color": BAD})
    steps = [{"k": 0, "note": "四台真机，行为都写在有限条规则里"},
             {"k": 1, "note": "转移表编成数字串，机器就能互相读"},
             {"k": 2, "note": "每台机器跑到每台机器的编码上，得到 16 格"},
             {"k": 3, "note": "看对角线"},
             {"k": 4, "note": "D 的定义就是取反对角线"},
             {"k": 5, "note": "D(D) 落进自己挖的坑"}]
    return {"theme": PAPER,
            "view": {"xRange": [0, 20.6], "yRange": [0, 10], "equalAspect": True,
                     "pad": {"l": 16, "r": 16, "b": 10, "t": 10}},
            "layers": layers, "steps": steps}


# Σ(3)、T(3) 的两台获胜机由「穷举全部 16 777 216 台三状态机」得出（本机跑了 29 分钟）；
# 本页不再重跑那八分钟，改为把它们各真跑一遍当场验证（下面的断言就是验证）。
# 注意它们是**两台不同的机器**：Σ(3) 那台写出 6 个 1 只用了 11 步；T(3) 那台走了 21 步，
# 却只写出 4 个 1 —— 「写得多」和「跑得久」是两个目标。
BB3_SIGMA_PROG = [(1, 1, 1), (1, -1, 2), (1, 1, 2), (1, -1, 3), (1, -1, 0), (0, -1, 1)]
BB3_T_PROG = [(1, -1, 2), (0, -1, 3), (1, 1, 1), (1, 1, 0), (1, 1, 2), (0, -1, 1)]


def fig_bb():
    """忙碌海狸：现场穷举 64 台与 20 736 台，再真跑两台三状态获胜机。"""
    sig1, t1, _c1, _l1, tot1, hal1 = _bb_enum(1, 100)
    assert (sig1, t1, tot1) == (1, 1, 64), (sig1, t1, tot1)
    sig2, t2, _c2, _l2, tot2, hal2 = _bb_enum(2, 400)
    assert (sig2, t2, tot2, hal2) == (4, 6, 20736, 9784), (sig2, t2, tot2, hal2)

    tape3, ones3, steps3, hal3 = _bb_prog(BB3_SIGMA_PROG, 3)
    tape3t, ones3t, steps3t, _h3t = _bb_prog(BB3_T_PROG, 3)
    assert hal3 and ones3 == 6 and steps3 == 11, (ones3, steps3, hal3)
    assert hal3 and steps3t == 21 and ones3t == 4, (ones3t, steps3t)

    GX, GY, GC = 0.95, 3.6, 0.62          # 64 台机器的 8×8 网格
    RX = GX + 6.5                          # 右栏起点
    OPTS1 = [(w, m, q) for w in (0, 1) for m in (-1, 1) for q in range(2)]
    vals1, hl1 = [], []
    for code in range(64):
        c, prog = code, [None] * 2
        for i in range(2):
            prog[i] = OPTS1[c % 8]
            c //= 8
        tape, ones, steps, halted = _bb_prog(prog, 1, 100)
        vals1.append(str(ones) if halted else "·")
        if halted and (ones == sig1 or steps == t1):
            hl1.append([code % 8, code // 8])

    layers = [
        {"geom": "text", "x": GX, "y": 9.6, "text": "穷举的对象：n 个状态、2 个符号的全部图灵机",
         "align": "left", "size": 11, "color": INK},
        {"geom": "text", "x": GX, "y": 9.08,
         "text": "每格规则有 4(n+1) 种选择，共 2n 格 → 总数 4(n+1) 的 2n 次方",
         "align": "left", "size": 10, "color": DIM, "weight": "normal"},
        {"geom": "text", "when": "k >= 1", "x": GX, "y": 8.75,
         "text": "n = 1：全部 64 台，一台不漏地画出来", "align": "left", "size": 11,
         "color": INK},
        {"geom": "matrix", "when": "k >= 1", "rows": 8, "cols": 8,
         "cellW": GC, "cellH": GC, "origin": [GX, GY],
         "values": [vals1[r * 8:(r + 1) * 8] for r in range(8)],
         "highlight": hl1, "hlFill": "#15803d", "hlEdge": "#14532d",
         "cellFill": "#ffffff", "cellEdge": "#e7e0d5", "textColor": "#1f1b16",
         "fontSize": 9},
        {"geom": "text", "when": "k >= 1", "x": GX, "y": GY - 0.45,
         "text": "格子里是停机时写出的 1 的个数；「·」表示永不停机",
         "align": "left", "size": 10, "color": DIM, "weight": "normal"},
        {"geom": "text", "when": "k >= 2", "x": RX, "y": 8.4,
         "text": "Σ(1) = %d 个 1，T(1) = %d 步" % (sig1, t1),
         "align": "left", "size": 13, "color": GOOD},
        {"geom": "text", "when": "k >= 2", "x": RX, "y": 7.85,
         "text": "64 台里有 %d 台会停机" % hal1, "align": "left", "size": 10.5,
         "color": DIM, "weight": "normal"},
        {"geom": "text", "when": "k >= 3", "x": RX, "y": 7.0,
         "text": "n = 2：20 736 台，其中 %d 台会停机" % hal2,
         "align": "left", "size": 11, "color": INK},
        {"geom": "text", "when": "k >= 3", "x": RX, "y": 6.42,
         "text": "Σ(2) = %d 个 1，T(2) = %d 步" % (sig2, t2),
         "align": "left", "size": 13, "color": GOOD},
        {"geom": "text", "when": "k >= 4", "x": RX, "y": 5.5,
         "text": "n = 3：16 777 216 台。写出 1 最多的那台只有 3 个状态、",
         "align": "left", "size": 11, "color": INK},
        {"geom": "text", "when": "k >= 4", "x": RX, "y": 5.05,
         "text": "6 条规则，走 %d 步就停，纸带上正好 %d 个 1（真跑了一遍）：" % (steps3, ones3),
         "align": "left", "size": 11, "color": INK},
        {"geom": "matrix", "when": "k >= 4", "rows": 1, "cols": len(tape3),
         "cellW": 0.45, "cellH": 0.45, "origin": [RX, 4.35],
         "values": [list(tape3)], "cellFill": "#ffffff", "cellEdge": "#e7e0d5",
         "textColor": "#15803d"},
        {"geom": "text", "when": "k >= 5", "x": RX, "y": 3.9,
         "text": "跑得最久的是另一台：%d 步，却只写出 %d 个 1。" % (steps3t, ones3t),
         "align": "left", "size": 11, "color": INK},
        {"geom": "matrix", "when": "k >= 5", "rows": 1, "cols": len(tape3t),
         "cellW": 0.45, "cellH": 0.45, "origin": [RX, 3.3],
         "values": [list(tape3t)], "cellFill": "#ffffff", "cellEdge": "#e7e0d5",
         "textColor": "#6d28d9"},
        {"geom": "text", "when": "k >= 6", "x": RX, "y": 2.7,
         "text": "Σ(3) = %d 个 1，T(3) = %d 步；往后 Σ(4) = 13，Σ(5) = 4098，" % (ones3, steps3t),
         "align": "left", "size": 11, "color": INK},
        {"geom": "text", "when": "k >= 6", "x": RX, "y": 2.1,
         "text": "而 T(5) = 47,176,870 步 —— 一台五状态机器要跑这么久。",
         "align": "left", "size": 11.5, "color": BAD},
    ]
    steps = [{"k": 0, "note": "穷举的对象与台数"},
             {"k": 1, "note": "n = 1 的全部 64 台，一台不漏"},
             {"k": 2, "note": "Σ(1) = %d，T(1) = %d" % (sig1, t1)},
             {"k": 3, "note": "n = 2：%d 台，Σ(2) = %d，T(2) = %d" % (tot2, sig2, t2)},
             {"k": 4, "note": "Σ(3) = 6 的获胜机，真跑一遍"},
             {"k": 5, "note": "T(3) = 21 的是另一台机器"},
             {"k": 6, "note": "步数才是真正爆炸的东西"}]
    return {"theme": PAPER,
            "view": {"xRange": [0, 21.75], "yRange": [0, 10], "equalAspect": True,
                     "pad": {"l": 16, "r": 16, "b": 10, "t": 10}},
            "layers": layers, "steps": steps}


def fig_layers():
    """复杂度与可判定性的层级：越往内越「容易」，最外圈连算法都没有。"""
    CX, CY = 5.4, 5.15
    rings = [(4.3, "#7d756a", "递归可枚举", 0), (3.35, "#0f766e", "可判定", 1),
             (2.35, "#6d28d9", "NP", 2), (1.35, "#b45309", "P", 3)]
    layers, steps = [], []
    for r, col, lab, k in rings:
        layers.append({"geom": "line", "when": f"k >= {k}", "data": _circle(CX, CY, r),
                       "stroke": col, "width": 1.8})
        layers.append({"geom": "text", "when": f"k >= {k}", "x": CX,
                       "y": CY + r * 0.88, "text": lab, "align": "center",
                       "size": 14 if k == 3 else 12, "color": col})
    layers += [
        {"geom": "text", "when": "k >= 0", "x": CX, "y": 0.42,
         "text": "再往外：不可判定（连「永远等下去」都做不到）",
         "align": "center", "size": 11, "color": BAD},
        {"geom": "region", "when": "k >= 4", "x": [CX + 1.85 - 0.3, CX + 1.85 + 0.3],
         "y": [CY - 0.3, CY + 0.3], "fill": "#ffffff", "outline": True,
         "stroke": "#b91c1c"},
        {"geom": "text", "when": "k >= 4", "x": CX + 1.85, "y": CY, "text": "?",
         "align": "center", "size": 15, "color": "#b91c1c"},
        {"geom": "text", "when": "k >= 4", "x": CX + 2.55, "y": CY - 0.5,
         "text": "P = NP ？", "align": "left", "size": 12, "color": BAD},
    ]
    rows = [(8.55, "排序 · 最短路 · 线性规划", "P：有快算法", "#b45309"),
            (7.35, "SAT · 哈密顿回路 · 背包", "NP：答案能快速验证", "#6d28d9"),
            (6.15, "0ⁿ1ⁿ 的判定", "可判定：算法存在，只是慢", "#0f766e"),
            (4.95, "停机问题", "递归可枚举：跑不出就永远等", "#7d756a"),
            (3.75, "程序等价 · Rice 定理", "不可判定：等待也没用", "#b91c1c")]
    for i, (y, title, sub, col) in enumerate(rows):
        k = 4 - i if i < 4 else 0
        layers.append({"geom": "text", "when": f"k >= {k}", "x": 11.0, "y": y,
                       "text": title, "align": "left", "size": 11.5, "color": col})
        layers.append({"geom": "text", "when": f"k >= {k}", "x": 11.0, "y": y - 0.42,
                       "text": sub, "align": "left", "size": 10, "color": DIM,
                       "weight": "normal"})
    steps = [{"k": 0, "note": "最外圈：不可判定"},
             {"k": 1, "note": "递归可枚举：跑不出就永远等"},
             {"k": 2, "note": "可判定：算法存在，只是慢"},
             {"k": 3, "note": "NP：答案能快速验证"},
             {"k": 4, "note": "最内圈 P，以及 P 与 NP 之间那条著名的问号"}]
    return {"theme": PAPER,
            "view": {"xRange": [0, 19.575], "yRange": [0, 10], "equalAspect": True,
                     "pad": {"l": 16, "r": 16, "b": 10, "t": 10}},
            "layers": layers, "steps": steps}


# 第 8 章：这些函数定义在上面的 FIGS 表之后，故在此补注册
FIGS.update({
    "fig-machine": fig_machine,
    "fig-universal": fig_universal,
    "fig-halting": fig_halting,
    "fig-bb": fig_bb,
    "fig-layers": fig_layers,
})


def build(ids=None):
    return {k: FIGS[k]() for k in (ids or FIGS)}


# =====================================================================
# 生成路径：正文可引用的具名数值
# =====================================================================
# 章节 JSON 里写 @@name@@（可带精度：@@name:3@@），build.py 装配时用本表替换。
# 目的：让**正文与图形共用同一份计算**，把「图文不符」从源头消掉 ——
# 书稿正文原本 0% 生成（见 edulab/generated-prose-report.md），这是第一步。
# 约定：
#   · 只有在这里注册过的名字才能在正文里用；拼错会在装配时**报错**，不会静默留白。
#   · 展示单位（度/百分比/元）由正文写，这里只给数值。
#   · 只登记「正文确实引用」的值，不做无目的的搬运。
PROSE = {
    "fig-poincare": poincare_values,
    "fig-riemann": riemann_values,
    "fig-curvature": curvature_values,
    "fig-dice": dice_values,
    "fig-cayley": cayley_values,
}


def prose_values(fig_ids):
    """收集若干张图可供正文引用的具名数值；重名会报错（避免张冠李戴）。"""
    out = {}
    for fid in fig_ids:
        fn = PROSE.get(fid)
        if not fn:
            continue
        for k, val in fn().items():
            if k in out:
                raise KeyError(f"正文记号冲突：{k}（{fid}）已在别处定义")
            out[k] = val
    return out

if __name__ == "__main__":
    figs = build()
    for k, v in figs.items():
        assert v.get("theme") == "paper", f"{k} 应使用 paper 主题"
        assert v.get("layers"), f"{k} 没有图层"
        for i, g in enumerate(v["layers"]):
            assert "geom" in g, f"{k} 第 {i} 个图层缺少 geom"
        if v.get("steps"):
            for i, s in enumerate(v["steps"]):
                assert "note" in s, f"{k} 第 {i} 步缺少 note"
        # 文本类图元必须有 x/y/text
        for g in v["layers"]:
            if g["geom"] == "text":
                assert "x" in g and "y" in g and "text" in g, f"{k} 的 text 图元字段不全"
    print("figures self-check OK ✓")
    print(f"  共 {len(figs)} 张插图：")
    for k, v in figs.items():
        ns = len(v.get("steps", []))
        print(f"    {k:16s} 图层 {len(v['layers']):2d} 个" + (f"，{ns} 步" if ns else ""))
