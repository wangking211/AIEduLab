# -*- coding: utf-8 -*-
"""《万物尺度》样章的插图。

图上的每个数字都来自同目录的 `facts.py`（事实登记表）—— 图、正文、登记三者同源：
改一个登记值，画板与正文一起变。
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
ACCENT = "#b45309"       # 实测
ACCENT2 = "#6d28d9"      # 文献
GOOD = "#15803d"         # 现算
PAPER = "paper"


def _load_facts():
    """按路径加载同目录的 facts.py。

    不走 `import facts`：那个名字太通用，若同进程里已经加载过别的书的 facts，
    `import` 会**悄悄拿到另一本书的登记表**。按路径 + 唯一模块名才确定。
    """
    spec = importlib.util.spec_from_file_location("cosmos_facts", _HERE / "facts.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


REG = _load_facts().REGISTRY


def _v(cid):
    return REG.items[cid]["value"]


def _hum(sec):
    """把秒数写成人话。**由登记值算出来**，不是手写的字符串。"""
    y = sec / _v("year_sec")
    if y < 1e-2:
        return f"{sec:.1e} 秒"
    if y < 1:
        return f"{sec:,.0f} 秒"
    if y < 1e4:
        return f"{y:,.0f} 年"
    if y < 1e8:
        return f"{y / 1e4:,.1f} 万年".replace(".0 万年", " 万年")
    return f"{y / 1e8:,.2f} 亿年".replace(".00 亿年", " 亿年")


def fig_scale():
    """从普朗克时间到宇宙年龄：一条横杠 = 一个时刻，长度就是它的数量级。

    颜色编码**出处等级**（绿 现算 / 灰 约定 / 紫 文献 / 橙 实测）——
    这张图想说的不只是「世界很大」，还有「每个数字是怎么被知道的」。
    """
    X0, X1 = 1e-45, 1e18
    Y = _v("year_sec")
    rungs = [
        ("普朗克时间", _v("planck_time_s"), GOOD, False),
        ("一次心跳", _v("heartbeat_s"), DIM, True),
        ("一天", _v("day_sec"), DIM, True),
        ("一年", Y, DIM, True),
        ("一生（示例）", _v("lifespan_sec"), DIM, True),
        ("智人出现", _v("homo_sapiens_year") * Y, ACCENT2, True),
        ("恐龙灭绝", _v("kpg_year") * Y, ACCENT2, True),
        ("地球形成", _v("earth_age_year") * Y, ACCENT2, True),
        ("宇宙年龄", _v("universe_age_sec"), ACCENT, True),
    ]
    layers = [{"geom": "axis", "xRange": [X0, X1], "yRange": [-1.4, 9.4],
               "xticks": [1.0, Y, 1e9 * Y],
               "xticklabels": ["1 秒", "1 年", "10 亿年"],
               "yticks": False,
               "xlab": "时间（对数尺度：图上等距 = 相差 10 倍）"}]
    steps_k = [1, 2, 2, 2, 2, 3, 3, 3, 4]          # 每个横杠从第几步开始出现
    for i, (name, sec, color, show) in enumerate(rungs):
        k = steps_k[i]
        y = float(i)
        lab = f"{name}  {_hum(sec)}" if show else name
        align = "right" if math.log10(sec) > 12 else "left"
        layers += [
            {"geom": "line", "when": f"k >= {k}", "data": [[X0, y], [sec, y]],
             "stroke": color, "width": 7},
            {"geom": "point", "when": f"k >= {k}", "data": [{"x": sec, "y": y}],
             "r": 4.0, "fill": color},
            {"geom": "text", "when": f"k >= {k}", "x": sec, "y": y, "text": lab,
             "align": align, "size": 10, "color": color, "dy": -12},
        ]
    layers.append({"geom": "text", "when": "k >= 4", "x": X0, "y": -1.1,
                   "text": "颜色 = 出处等级：绿 现算 ｜ 灰 约定 ｜ 紫 文献 ｜ 橙 实测",
                   "align": "left", "size": 9.5, "color": DIM})
    steps = [
        {"k": 1, "note": f"起点：普朗克时间 {_v('planck_time_s'):.2e} 秒 —— 它不是测出来的，"
                         f"是由光速、普朗克常数、引力常数（都是定义或实测）算出来的。"},
        {"k": 2, "note": f"加上人的尺度：心跳约 1 秒、一天 {_v('day_sec'):,.0f} 秒、"
                         f"一年 {_v('year_sec'):,.0f} 秒、一生（示例 80 年）约 "
                         f"{_v('lifespan_sec'):.1e} 秒。"},
        {"k": 3, "note": f"加上物种与地质尺度：智人约 {_hum(_v('homo_sapiens_year') * Y)}、"
                         f"恐龙灭绝约 {_hum(_v('kpg_year') * Y)}、"
                         f"地球形成约 {_hum(_v('earth_age_year') * Y)}。"},
        {"k": 4, "note": f"最后是宇宙年龄 {_hum(_v('universe_age_sec'))}。整条轴共 "
                         f"{_v('span_decades'):.1f} 个数量级 —— 图上每等距一段就是「乘 10」。"},
    ]
    return {"theme": PAPER,
            "view": {"xRange": [X0, X1], "yRange": [-1.4, 9.4], "xlog": True,
                     "pad": {"l": 30, "r": 22, "b": 46, "t": 16}},
            "layers": layers, "steps": steps}


FIGS = {"fig-scale": fig_scale}


def build(ids=None):
    return {k: FIGS[k]() for k in (ids or FIGS)}
