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


def fig_riemann():
    """从「斜率」到「面积」：无穷多条无穷细的矩形，和是有限的。

    画法：y = x²/4 + 1/2 在 [0,3] 上的左端点矩形和，n = 1/2/4/8 逐次替换
    （互斥显示，用 k == N），右栏读数全部由 Python 现算。
    """
    f = lambda x: x * x / 4.0 + 0.5          # noqa: E731
    XMIN, XMAX, YMIN, YMAX = -0.30, 3.40, -1.10, 3.70
    XR, YR = [XMIN, XMAX], [YMIN, YMAX]
    A, B = 0.0, 3.0
    exact = (B ** 3 - A ** 3) / 12.0 + 0.5 * (B - A)   # ∫ x²/4 + 1/2 = 3.75

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
        {"k": 2, "note": "用 1 个矩形顶替它。误差大得离谱：左端点取值 0.5，整个矩形只有 1.500，而真值是 3.750。"},
        {"k": 3, "note": "切成 2 块。和跳到 2.344，缺口明显缩小。"},
        {"k": 4, "note": "切成 4 块，和 2.977。每块顶端和曲线之间只剩一个小台阶。"},
        {"k": 5, "note": "8 块时和为 3.346，极限 3.750。**分得越细，误差越小**——「无穷多条无穷细的矩形」不是一个比喻，它的和是一个确定的数。这就是定积分。"},
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
}


def build(ids=None):
    return {k: FIGS[k]() for k in (ids or FIGS)}


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
