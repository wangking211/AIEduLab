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


def build(ids=None):
    return {k: FIGS[k]() for k in (ids or FIGS)}
