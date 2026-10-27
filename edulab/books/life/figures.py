# -*- coding: utf-8 -*-
"""《生命的尺度》插图。

第一张图用**双对数**（横轴时间、纵轴长度）—— 这是前两本书没画过的类型：
一个点要两个坐标才能定位，而「同一个量级」在图上变成一条斜率固定的斜带。
"""
import importlib.util
import math
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[1]                     # edulab/
for _p in (str(_REPO / "shared" / "viz"), str(_REPO / "shared")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import vizkit as vk                          # noqa: E402

INK = "#1f1b16"
DIM = "#7d756a"
ACCENT = "#b45309"
ACCENT2 = "#6d28d9"
GOOD = "#15803d"
BAD = "#b91c1c"
PAPER = "paper"


def _load_facts():
    """按路径加载同目录的 facts.py（与 bookbuild 共用同一份模块实例）。

    如果这里自己再 importlib 一次，就会得到**第二个 Registry**：
    插图读的是这一份，闸门读的是那一份，F3 的「是否被读过」永远对不上。
    """
    from bookbuild import load_book_module
    return load_book_module(_HERE, "facts")


REG = _load_facts().REGISTRY


def _v(cid):
    return REG.items[cid]["value"]


SPECIES = [
    ("ecoli", "大肠杆菌", "2.0×10⁻⁶ 米"),
    ("yeast", "酵母", "5.0×10⁻⁶ 米"),
    ("paramecium", "草履虫", "0.2 毫米"),
    ("drosophila", "果蝇", "2.5 毫米"),
    ("mouse", "小鼠", "9 厘米"),
    ("human", "人", "1.7 米"),
    ("whale", "蓝鲸", "25 米"),
    ("redwood", "红杉", "80 米"),
]

_SPAN = "体长与世代时间都取量级示意"


def fig_band():
    """生命在「时间 × 空间」平面上的位置：八个物种落在一条斜率≈1 的窄带里。"""
    X0, X1 = 1e3, 1e11
    Y0, Y1 = 1e-7, 1e2
    layers = [
        {"geom": "axis", "xRange": [X0, X1], "yRange": [Y0, Y1],
         "xticks": [1e3, 1e5, 1e7, 1e9, 1e11],
         "xticklabels": ["17 分钟", "1 天", "4 个月", "32 年", "3200 年"],
         "yticks": [1e-6, 1e-3, 1.0],
         "yticklabels": ["1 微米", "1 毫米", "1 米"],
         "xlab": "世代时间（对数尺度）",
         "ylab": "成体体长（对数尺度）"},
        # 两条参考斜线：体长/世代时间 = 10⁻⁹ 与 10⁻⁷ 米每秒
        {"geom": "line", "when": "k >= 2",
         "data": [[1e3, 1e3 * _v("rate_min")], [1e11, 1e11 * _v("rate_min")]],
         "stroke": GOOD, "width": 1.2, "dash": True},
        {"geom": "line", "when": "k >= 2",
         "data": [[1e3, 1e3 * _v("rate_max")], [1e11, 1e11 * _v("rate_max")]],
         "stroke": GOOD, "width": 1.2, "dash": True},
        {"geom": "text", "when": "k >= 2", "x": 3e3, "y": 3e3 * _v("rate_max"),
         "text": f"这条带只宽 {_v('rate_span'):.1f} 个数量级", "align": "left",
         "size": 9.5, "color": GOOD, "dy": -10},
    ]
    for i, (cid, name, size_txt) in enumerate(SPECIES):
        g = _v(f"{cid}_gen")
        s = _v(f"{cid}_size")
        layers += [
            {"geom": "point", "when": f"k >= {2 if i < 4 else 3}",
             "data": [{"x": g, "y": s}], "r": 4.2, "fill": INK},
            {"geom": "text", "when": f"k >= {2 if i < 4 else 3}", "x": g, "y": s,
             "text": name, "align": "left", "size": 9.5, "color": DIM, "dy": -11},
        ]
    steps = [
        {"k": 1, "note": "横轴是世代时间，纵轴是成体体长 —— 两个轴都是对数。"
                         "一个点需要两个数才能定位，这是前两本书没有的类型。"},
        {"k": 2, "note": f"最小的一端：大肠杆菌约 2 微米、20 分钟一代；草履虫 0.2 毫米、一天一代。"
                         f"体长差了 100 倍，时间也差了 70 倍 —— 点在图上沿斜线上升。"},
        {"k": 3, "note": f"再加上大一点的：小鼠、人、蓝鲸、红杉。从细菌到红杉，体长跨 "
                         f"{_v('size_span'):.0f} 个数量级、世代跨 {_v('gen_span'):.0f} 个数量级。"},
        {"k": 4, "note": f"两条绿虚线之间的距离，就是「体长 ÷ 世代时间」的跨度 —— 只有 "
                         f"{_v('rate_span'):.1f} 个数量级。八个物种挤在一条斜率≈1 的窄带里。"},
    ]
    return {"theme": PAPER,
            "view": {"xRange": [X0, X1], "yRange": [Y0, Y1],
                     "xlog": True, "ylog": True,
                     "pad": {"l": 64, "r": 26, "b": 46, "t": 18}},
            "layers": layers, "steps": steps}


FIGS = {"fig-band": fig_band}


def _centroid():
    """五个物种在 log-log 平面上的质心 —— 两条参考斜线都过这一点。"""
    xs = [math.log10(_v(f"{a}_mass")) for a in ("mouse", "rat", "human_m", "horse", "elephant")]
    ys = [math.log10(_v(f"{a}_bmr")) for a in ("mouse", "rat", "human_m", "horse", "elephant")]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _line_through(mx, my, slope, x0, x1):
    return [[10 ** x0, 10 ** (my + slope * (x0 - mx))],
            [10 ** x1, 10 ** (my + slope * (x1 - mx))]]


def fig_kleiber():
    """第 2 章：代谢率对体重。两条参考线都过质心，只有斜率不同 —— 差别一眼可见。"""
    X0, X1 = 1e-2, 1e4
    Y0, Y1 = 1e0, 1e5
    mx, my = _centroid()
    e_fit = _v("metabolic_exponent")
    layers = [
        {"geom": "axis", "xRange": [X0, X1], "yRange": [Y0, Y1],
         "xticks": [1e-2, 1e-1, 1, 10, 100, 1000],
         "xticklabels": ["10 克", "100 克", "1 千克", "10 千克", "100 千克", "1 吨"],
         "yticks": [1, 10, 100, 1000, 10000],
         "yticklabels": ["1", "10", "100", "1000", "10000"],
         "xlab": "体重（对数尺度）",
         "ylab": "基础代谢率（千卡每天，对数尺度）"},
        {"geom": "line", "when": "k >= 2",
         "data": _line_through(mx, my, e_fit, -2, 4),
         "stroke": ACCENT, "width": 2.2},
        {"geom": "text", "when": "k >= 2", "x": 10 ** -1.9, "y": 10 ** (my + e_fit * (-1.9 - mx)),
         "text": f"拟合斜率 {e_fit:.3f}", "align": "left", "size": 10, "color": ACCENT,
         "dy": -12},
        {"geom": "line", "when": "k >= 3",
         "data": _line_through(mx, my, _v("metabolic_slope_two_thirds"), -2, 4),
         "stroke": BAD, "width": 1.6, "dash": True},
        {"geom": "text", "when": "k >= 3", "x": 10 ** 2.6,
         "y": 10 ** (my + _v("metabolic_slope_two_thirds") * (2.6 - mx)),
         "text": "按表面积推算的斜率 2/3", "align": "right", "size": 9.5, "color": BAD,
         "dy": 14},
    ]
    for i, (cid, name) in enumerate((("mouse", "小鼠"), ("rat", "大鼠"),
                                     ("human_m", "人"), ("horse", "马"),
                                     ("elephant", "大象"))):
        layers += [
            {"geom": "point", "when": "k >= 1",
             "data": [{"x": _v(f"{cid}_mass"), "y": _v(f"{cid}_bmr")}],
             "r": 4.4, "fill": INK},
            {"geom": "text", "when": "k >= 1", "x": _v(f"{cid}_mass"), "y": _v(f"{cid}_bmr"),
             "text": name, "align": "left", "size": 9.5, "color": DIM, "dy": -12},
        ]
    steps = [
        {"k": 1, "note": "五个物种，两列数字：体重、基础代谢率。都是文献量级值。"},
        {"k": 2, "note": f"对数—对数最小二乘，斜率 {e_fit:.3f} —— 与 3/4 只差 0.001。"},
        {"k": 3, "note": f"如果生命只是一块被动散热的石头，代谢该正比于表面积 ∝ 质量^(2/3)。"
                         f"两条线从质心出发、越走越开：在大象的体重上，两种预测相差约 "
                         f"{10 ** ((e_fit - 2 / 3) * (math.log10(_v('elephant_mass')) - mx)):.1f} 倍。"},
    ]
    return {"theme": PAPER,
            "view": {"xRange": [X0, X1], "yRange": [Y0, Y1],
                     "xlog": True, "ylog": True,
                     "pad": {"l": 62, "r": 26, "b": 46, "t": 18}},
            "layers": layers, "steps": steps}


FIGS["fig-kleiber"] = fig_kleiber


def _count(v):
    """数量标签：用「万/亿/亿亿」叠字，避免把 10^13 写成 10000000000000。"""
    if v < 1e4:
        return f"{v:,.0f}"
    if v < 1e8:
        return f"{v / 1e4:,.0f} 万"
    if v < 1e12:
        return f"{v / 1e8:,.1f} 亿".replace(".0 亿", " 亿")
    return f"{v / 1e8:,.0f} 亿"


def fig_cells():
    """第 3 章：四个数放在一条对数轴上 —— 其中一个是错的。"""
    X0, X1 = 1e9, 1e15
    rows = [
        ("一个人身上的细菌（旧说法推出来）", _v("myth_bacteria"), BAD),
        ("一个人身上的细菌（2016 年重算）", _v("bacteria_cells"), ACCENT2),
        ("一个人自己的细胞", _v("human_cells"), GOOD),
        ("一个人的基因组（碱基对，另一回事）", _v("genome_bp"), DIM),
    ]
    layers = [
        {"geom": "axis", "xRange": [X0, X1], "yRange": [-0.6, 3.9],
         "xticks": [1e9, 1e11, 1e13, 1e15],
         "xticklabels": ["10 亿", "1000 亿", "10 万亿", "1000 万亿"],
         "yticks": False,
         "xlab": "个数（对数尺度：图上等距 = 相差 10 倍）"},
    ]
    for i, (name, val, color) in enumerate(rows):
        y = float(i)
        layers += [
            {"geom": "line", "when": "k >= 1", "data": [[X0, y], [val, y]],
             "stroke": color, "width": 6},
            {"geom": "point", "when": "k >= 1", "data": [{"x": val, "y": y}],
             "r": 3.6, "fill": color},
            {"geom": "text", "when": "k >= 1", "x": X0, "y": y + 0.32, "text": name,
             "align": "left", "size": 9.5,
             "color": BAD if color == BAD else DIM},
        ]
    layers.append({"geom": "text", "when": "k >= 2", "x": _v("bacteria_cells"), "y": 2.55,
                   "text": f"≈ {_v('bacteria_to_human'):.1f} : 1", "align": "left",
                   "size": 10, "color": ACCENT2, "dy": 0})
    layers.append({"geom": "text", "when": "k >= 2", "x": _v("myth_bacteria"), "y": 0.55,
                   "text": f"旧说法多算了 {_v('myth_overestimate'):.1f} 倍", "align": "right",
                   "size": 9.5, "color": BAD, "dy": 0})
    steps = [
        {"k": 1, "note": "一条对数轴，四个数。最上面那行是**旧说法**（按 10 : 1 反推），"
                         "它比下面两行高出一截。"},
        {"k": 2, "note": f"2016 年的重算把比例拉到 {_v('bacteria_to_human'):.1f} : 1 —— "
                         f"细菌和人体细胞的数量几乎是 1 : 1，而不是 10 : 1。"},
        {"k": 3, "note": f"最下面那行是另一个量：基因组碱基对数。把它放进来是为了提醒 —— "
                         f"「个数」这个词在这张图上指的是三种完全不同的东西。"},
    ]
    return {"theme": PAPER,
            "view": {"xRange": [X0, X1], "yRange": [-0.6, 3.9], "xlog": True,
                     "pad": {"l": 30, "r": 26, "b": 46, "t": 16}},
            "layers": layers, "steps": steps}


FIGS["fig-cells"] = fig_cells


def fig_deeptime():
    """第 4 章：同一段历史（显生宙）在两种轴上的占比。

    横轴是「占整条轴的比例」，三行：线性轴、对数轴、以及两者之比。
    这张图想说的不是历史，而是**读数方式本身带来的偏置**。
    """
    X0, X1 = 0.0, 1.0
    rows = [
        ("线性时间轴上的显生宙", _v("frac_linear"), GOOD),
        ("对数时间轴上的显生宙", _v("frac_log"), ACCENT),
    ]
    layers = [
        {"geom": "axis", "xRange": [X0, X1], "yRange": [-0.7, 2.2],
         "xticks": [0, 0.25, 0.5, 0.75, 1],
         "xticklabels": ["0%", "25%", "50%", "75%", "100%"],
         "yticks": False,
         "xlab": "占整条轴的宽度比例"},
    ]
    for i, (name, frac, color) in enumerate(rows):
        y = float(i) * 1.4
        gate = "k >= 1" if i == 0 else "k >= 2"     # 第 2 步才加上对数轴那一行
        layers += [
            {"geom": "text", "when": gate, "x": 0.0, "y": y + 0.42, "text": name,
             "align": "left", "size": 9.5, "color": DIM},
            {"geom": "region", "when": gate, "x": [0.0, frac], "y": [y - 0.16, y + 0.16],
             "fill": color, "outline": False},
            {"geom": "text", "when": gate, "x": frac, "y": y, "text": f"{frac * 100:.1f}%",
             "align": "left", "size": 11, "color": color, "dy": 0},
        ]
    layers.append({"geom": "text", "when": "k >= 2", "x": 0.02, "y": -0.45,
                   "text": f"同一段历史，换一条轴，宽度变成 {_v('frac_ratio'):.1f} 倍",
                   "align": "left", "size": 9.5, "color": BAD})
    steps = [
        {"k": 1, "note": f"显生宙（寒武纪以来）约 {_v('cambrian_year'):.2e} 年。"
                         f"在线性轴上，它只占整条轴的 {_v('frac_linear_pct'):.0f}% —— "
                         f"一小截，符合直觉。"},
        {"k": 2, "note": f"换成对数轴，同一段历史占 {_v('frac_log_pct'):.0f}% —— "
                         f"接近整条轴。**轴的选择改变了「哪段时间看起来重要」**。"},
    ]
    return {"theme": PAPER,
            "view": {"xRange": [X0, X1], "yRange": [-0.7, 2.2],
                     "pad": {"l": 30, "r": 30, "b": 46, "t": 16}},
            "layers": layers, "steps": steps}


FIGS["fig-deeptime"] = fig_deeptime


def _sv(size_m):
    """立方体近似的表面积/体积比（与 facts.py 里同一公式；只用于画那条参考线）。"""
    return 6.0 / size_m


def fig_limit():
    """第 5 章：几何给的那条线（S/V = 6/L），以及三个蹲在线上、三个跳出线的点。

    线是纯几何（现算）；点是真的生物。**线不解释谁大谁小，它只解释「为什么大起来更贵」。**
    """
    X0, X1 = 1e-7, 1e0
    Y0, Y1 = 1e0, 1e8
    pts = [
        ("大肠杆菌", _v("ecoli_size_m"), INK, "up"),
        ("酵母", _v("yeast_size_m"), INK, "down"),
        ("草履虫", _v("paramecium_size_m"), INK, "up"),
        ("变形虫", _v("amoeba_size_m"), INK, "down"),
        ("鸵鸟蛋", _v("ostrich_egg_size_m"), ACCENT2, "down"),
        ("巨型细菌", _v("thiomargarita_size_m"), BAD, "up"),
    ]
    layers = [
        {"geom": "axis", "xRange": [X0, X1], "yRange": [Y0, Y1],
         "xticks": [1e-6, 1e-4, 1e-2, 1e0],
         "xticklabels": ["1 微米", "0.1 毫米", "1 厘米", "1 米"],
         "yticks": [1e1, 1e3, 1e5, 1e7],
         "yticklabels": ["10", "10³", "10⁵", "10⁷"],
         "xlab": "体长（对数尺度）",
         "ylab": "表面积 ÷ 体积（1/米，对数尺度）"},
        {"geom": "line", "when": "k >= 1",
         "data": [[1e-7, _sv(1e-7)], [1e0, _sv(1e0)]],
         "stroke": GOOD, "width": 2.0},
        {"geom": "text", "when": "k >= 1", "x": 3e-7, "y": _sv(3e-7),
         "text": "S/V = 6/L（立方体近似）", "align": "left", "size": 9.5, "color": GOOD,
         "dy": -12},
    ]
    for name, size, color, side in pts:
        dy = -13 if side == "up" else 14
        layers += [
            {"geom": "point", "when": "k >= 2", "data": [{"x": size, "y": _sv(size)}],
             "r": 4.2, "fill": color},
            {"geom": "text", "when": "k >= 2", "x": size, "y": _sv(size), "text": name,
             "align": "left", "size": 9.5, "color": color, "dy": dy},
        ]
    layers.append({"geom": "text", "when": "k >= 3", "x": _v("thiomargarita_size_m"),
                   "y": _sv(_v("thiomargarita_size_m")) / 3, "text": "↑ 它靠「不按几何生活」跳出了这条线",
                   "align": "right", "size": 9.5, "color": BAD})
    steps = [
        {"k": 1, "note": "先只有这条线：S/V = 6/L。它是纯几何 —— 体长每涨十倍，"
                         "每单位体积能用的膜面积就掉到十分之一。"},
        {"k": 2, "note": f"六个真实尺寸落上去。大肠杆菌的 S/V 约 {_v('sv_ecoli'):.1e} 每米；"
                         f"鸵鸟蛋低得多 —— 它确实是一个细胞，但几乎不代谢。"},
        {"k": 3, "note": f"2022 年发现的巨型细菌体长可到 1 厘米，S/V 掉到 "
                         f"{_v('sv_thiomargarita'):.0f} 每米（大肠杆菌的 1/{_v('sv_drop'):.0f}）。"
                         f"它没有推翻几何，而是**改了自己的内部分工**。"},
    ]
    return {"theme": PAPER,
            "view": {"xRange": [X0, X1], "yRange": [Y0, Y1],
                     "xlog": True, "ylog": True,
                     "pad": {"l": 60, "r": 30, "b": 46, "t": 18}},
            "layers": layers, "steps": steps}


FIGS["fig-limit"] = fig_limit


def fig_trophic():
    """第 6 章：能量沿营养级逐级衰减（每级约十分之一）。

    这一章想说两件事：① 四级之后就没有足够的能量再养一个捕食者；
    ② 能量金字塔**永远不会倒**，但生物量金字塔可以 —— 那是储量，不是流量。
    """
    X0, X1 = 5e-3, 2e2
    labels = ["生产者", "初级消费者", "二级消费者", "三级消费者", "四级消费者"]
    vals = [_v("base_pct"), _v("level2_pct"), _v("level3_pct"),
            _v("level4_pct"), _v("level5_pct")]
    layers = [
        {"geom": "axis", "xRange": [X0, X1], "yRange": [-0.7, 4.9],
         "xticks": [1e-2, 1.0, 100.0],
         "xticklabels": ["0.01%", "1%", "100%"],
         "yticks": False,
         "xlab": "相对生产者的能量（对数尺度，%）"},
    ]
    for i, (name, val) in enumerate(zip(labels, vals)):
        y = float(4 - i)
        color = GOOD if i == 0 else (DIM if i < 4 else BAD)
        layers += [
            {"geom": "line", "data": [[X0, y], [val, y]], "stroke": color, "width": 7},
            {"geom": "text", "x": X0, "y": y + 0.34, "text": name, "align": "left",
             "size": 9.5, "color": DIM},
            {"geom": "text", "x": val, "y": y, "text": f"{val:g}%", "align": "left",
             "size": 10, "color": color, "dy": -11},
        ]
        if i < 4:
            layers.append({"geom": "text", "x": X0 * 1.6, "y": y - 0.5,
                           "text": f"↓ 只剩约 {_v('transfer_efficiency') * 100:.0f}%",
                           "align": "left", "size": 9, "color": DIM})
    layers.append({"geom": "text", "when": "k >= 2", "x": _v("level5_pct"), "y": -0.35,
                   "text": "再往上：能量不够再养一级", "align": "left", "size": 9.5,
                   "color": BAD, "dy": 0})
    steps = [
        {"k": 1, "note": f"生产者记 100%。每往上一级，只剩约 "
                         f"{_v('transfer_efficiency') * 100:.0f}% —— 其余都变成了热、"
                         f"呼吸与排泄。"},
        {"k": 2, "note": f"到第四级消费者只剩 {_v('level5_pct'):g}%，也就是万分之一。"
                         f"从 100% 掉到这里，正好要乘 {_v('levels_to_drop'):.0f} 次十分之一。"},
    ]
    return {"theme": PAPER,
            "view": {"xRange": [X0, X1], "yRange": [-0.7, 4.9], "xlog": True,
                     "pad": {"l": 28, "r": 34, "b": 46, "t": 16}},
            "layers": layers, "steps": steps}


FIGS["fig-trophic"] = fig_trophic


def build(ids=None):
    return {k: FIGS[k]() for k in (ids or FIGS)}
