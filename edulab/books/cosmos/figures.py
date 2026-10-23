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
BAD = "#b91c1c"          # 强调 / 边界警示
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


def _hum_m(v):
    """把长度写成人话（由登记值算出来：光年也是算的）。"""
    ly = _v("light_year_m")
    if v < 1e-6:
        return f"{v * 1e9:.1f} 纳米"
    if v < 1e-2:
        return f"{v * 1e3:.2f} 毫米"
    if v < 1e3:
        return f"{v:.2f} 米"
    if v < 1e12:
        return f"{v / 1e3:,.0f} 公里"
    if v < 1e15:
        return f"{v / 1e9:.2f} 亿公里"
    if v < 1e24:
        return f"{v / ly:.2f} 光年"
    return f"{v / ly / 1e9:.1f} 十亿光年"


def fig_length():
    """第 2 章：长度的阶梯。横轴是米（对数），每一行是一个尺度。

    为什么按「行」排、不按真实位置排：地月距离与太阳直径只差半个数量级，
    照真实位置画会叠成一点 —— 而这恰恰是这张图想说的（见第 3 步的说明）。
    """
    X0, X1 = 1e-12, 1e28
    rows = [
        ("氢原子（玻尔半径）", _v("bohr_radius_m"), GOOD),
        ("病毒（量级示意）", _v("virus_m"), DIM),
        ("细胞（量级示意）", _v("cell_m"), DIM),
        ("一个人", _v("human_h_m"), DIM),
        ("地月距离", _v("moon_distance_m"), ACCENT),
        ("太阳直径", _v("sun_diameter_m"), DIM),
        ("天文单位", _v("au_m"), DIM),
        ("一光年", _v("light_year_m"), GOOD),
        ("可观测宇宙", _v("universe_diameter_m"), ACCENT2),
    ]
    layers = [
        {"geom": "axis", "xRange": [X0, X1], "yRange": [-0.7, 8.7],
         "xticks": [1e-9, 1e-3, 1.0, 1e6, _v("light_year_m")],
         "xticklabels": ["1 纳米", "1 毫米", "1 米", "一千公里", "1 光年"],
         "yticks": False,
         "xlab": "长度（对数尺度：图上等距 = 相差 10 倍）"},
        {"geom": "region", "when": "k >= 2", "x": [1e-3, 1e3], "y": [-0.6, 8.6],
         "fill": "#eef7f0", "outline": False},
        {"geom": "text", "when": "k >= 2", "x": 1e-3, "y": 8.35,
         "text": "← 人能直接感知的范围", "align": "left", "size": 9.5, "color": GOOD},
    ]
    steps_k = [1, 1, 1, 2, 3, 3, 3, 4, 4]
    for i, (name, val, color) in enumerate(rows):
        y = float(i)
        k = steps_k[i]
        layers += [
            {"geom": "line", "when": f"k >= {k}", "data": [[X0, y], [val, y]],
             "stroke": color, "width": 6},
            {"geom": "point", "when": f"k >= {k}", "data": [{"x": val, "y": y}],
             "r": 3.6, "fill": color},
            {"geom": "text", "when": f"k >= {k}", "x": val, "y": y,
             "text": f"{name}  {_hum_m(val)}",
             # 靠近右边界的那一行必须右对齐，否则标签冲出画布
             "align": "right" if math.log10(val) > 22 else "left",
             "size": 10, "color": color, "dy": -11},
        ]
    steps = [
        {"k": 1, "note": f"从原子这一头开始：氢原子的玻尔半径 {_hum_m(_v('bohr_radius_m'))}。"
                         f"它不是被尺子量出来的 —— 由 ħ、电子质量、精细结构常数推出来。"},
        {"k": 2, "note": f"人的尺度落在绿色带里：{_hum_m(_v('human_h_m'))}。"
                         f"这条带子（1 毫米到 1 公里）几乎就是人凭感官能直接把握的全部范围。"},
        {"k": 3, "note": f"太阳系：地月距离 {_hum_m(_v('moon_distance_m'))}，太阳直径 "
                         f"{_hum_m(_v('sun_diameter_m'))} —— 两者只差半个数量级，"
                         f"在这张图上几乎叠成一行。天文单位 {_hum_m(_v('au_m'))}。"},
        {"k": 4, "note": f"最后一跨：一光年 {_hum_m(_v('light_year_m'))}，"
                         f"可观测宇宙 {_hum_m(_v('universe_diameter_m'))}。整条轴 "
                         f"{_v('span_len_decades'):.1f} 个数量级。"},
    ]
    return {"theme": PAPER,
            "view": {"xRange": [X0, X1], "yRange": [-0.7, 8.7], "xlog": True,
                     "pad": {"l": 30, "r": 24, "b": 46, "t": 16}},
            "layers": layers, "steps": steps}


FIGS["fig-length"] = fig_length


def _mant(v):
    """写成「2.9×10^9」：只给 10 的幂会失掉尾数（2.9e9 写成 10^9 差了 3 倍）。"""
    n = math.floor(math.log10(v))
    m = v / (10.0 ** n)
    if m >= 9.95:                      # 2.999… → 别写成 10.0×10^8
        n += 1
        m /= 10.0
    return f"{m:.1f}×10^{n}"


def fig_count():
    """第 3 章：数量的阶梯。横轴是「多少个」（对数），最右一格是宇宙的原子数。

    这一章真正的问题不是「大到什么程度」，而是**大到一定程度就没法用中文说了**：
    日常只有「万」「亿」两个常用量级，再往上只能把「亿」叠起来用。
    """
    X0, X1 = 1.0, 1e81
    rows = [
        ("一生的心跳", _v("heartbeats_lifetime"), GOOD),
        ("人脑神经元", _v("neurons"), ACCENT2),
        ("银河系恒星", _v("stars_milkyway"), ACCENT2),
        ("地球上的沙粒", _v("sand_grains"), ACCENT2),
        ("一杯水里的分子", _v("molecules_cup"), GOOD),
        ("可观测宇宙的原子", _v("atoms_universe"), ACCENT2),
    ]
    layers = [
        {"geom": "axis", "xRange": [X0, X1], "yRange": [-0.7, 5.9],
         "xticks": [1.0, 1e8, 1e16, 1e24, 1e32],
         "xticklabels": ["1", "1 亿", "1 亿亿", "1 亿亿亿", "1 亿亿亿亿"],
         "yticks": False,
         "xlab": "数量（对数尺度：图上等距 = 相差 10 倍）"},
    ]
    steps_k = [1, 2, 2, 2, 3, 4]
    for i, (name, val, color) in enumerate(rows):
        y = float(i)
        k = steps_k[i]
        layers += [
            {"geom": "line", "when": f"k >= {k}", "data": [[X0, y], [val, y]],
             "stroke": color, "width": 6},
            {"geom": "point", "when": f"k >= {k}", "data": [{"x": val, "y": y}],
             "r": 3.6, "fill": color},
            {"geom": "text", "when": f"k >= {k}", "x": val, "y": y,
             "text": f"{name}  {_mant(val)} 个",
             "align": "right" if math.log10(val) > 60 else "left",
             "size": 10, "color": color, "dy": -11},
        ]
    # 「10 的幂」这个说法本身也要说明：不然读者会以为 10^80 是 10 乘 80 次
    layers.append({"geom": "text", "when": "k >= 4", "x": 1.0, "y": -0.45,
                   "text": "10^80 意思是 1 后面跟 80 个 0，不是 10 乘 80 次",
                   "align": "left", "size": 9.5, "color": DIM})
    steps = [
        {"k": 1, "note": f"先从能数得清的开始：按演示寿命 80 年、每分钟 70 次，"
                         f"一生的心跳约 {_mant(_v('heartbeats_lifetime'))} 次。"},
        {"k": 2, "note": f"再往上就得靠估了：人脑神经元约 {_mant(_v('neurons'))} 个、"
                         f"银河系恒星约 {_mant(_v('stars_milkyway'))} 颗、"
                         f"地球上的沙粒约 {_mant(_v('sand_grains'))} 粒。"},
        {"k": 3, "note": f"一杯水里的分子约 {_mant(_v('molecules_cup'))} 个 —— "
                         f"它是算出来的（体积 ÷ 摩尔体积 × 阿伏伽德罗常数），不是数出来的。"},
        {"k": 4, "note": f"最后一格：可观测宇宙的原子约 {_mant(_v('atoms_universe'))} 个。"
                         f"从一杯水到这里，还差 {_v('gap_cup_to_universe'):.0f} 个数量级 —— "
                         f"这一段没有任何直觉可用，只能靠推理。"},
    ]
    return {"theme": PAPER,
            "view": {"xRange": [X0, X1], "yRange": [-0.7, 5.9], "xlog": True,
                     "pad": {"l": 30, "r": 26, "b": 46, "t": 16}},
            "layers": layers, "steps": steps}


FIGS["fig-count"] = fig_count


def _spd(v):
    """把速度写成人话。注意 0.001 这种小量：用 :,.0f 会渲染成「0」。"""
    if v < 1:
        return f"{v:.3g} 米每秒"
    if v < 1e3:
        return f"{v:g} 米每秒"
    if v < 1e5:
        return f"{v / 1e3:.1f} 公里每秒"
    return f"{v / 1e7:.2f} 万公里每秒"


def fig_speed():
    """第 4 章：速度的阶梯。这一章的要害不是「光速很快」，而是**它离我们并不远**。"""
    X0, X1 = 1e-3, 1e9
    rows = [
        ("蜗牛", _v("snail_speed"), DIM),
        ("步行", _v("walk_speed"), DIM),
        ("民航客机", _v("airliner_speed"), DIM),
        ("声速（空气）", _v("sound_speed"), DIM),
        ("地球公转", _v("earth_orbit_speed"), GOOD),
        ("光速", _v("c_light"), ACCENT),
    ]
    layers = [
        {"geom": "axis", "xRange": [X0, X1], "yRange": [-0.7, 5.9],
         "xticks": [1.0, 1e2, 1e4, 1e6, 1e8],
         "xticklabels": ["1 米每秒", "100", "10⁴ 米每秒", "10⁶", "10⁸ 米每秒"],
         "yticks": False,
         "xlab": "速度（对数尺度：图上等距 = 相差 10 倍）"},
        {"geom": "region", "when": "k >= 2", "x": [1.0, 1e3], "y": [-0.6, 5.8],
         "fill": "#eef7f0", "outline": False},
        {"geom": "text", "when": "k >= 2", "x": 1.0, "y": 5.55,
         "text": "← 人日常经历的速度", "align": "left", "size": 9.5, "color": GOOD},
    ]
    steps_k = [1, 2, 2, 3, 4, 5]
    for i, (name, val, color) in enumerate(rows):
        y = float(i)
        k = steps_k[i]
        layers += [
            {"geom": "line", "when": f"k >= {k}", "data": [[X0, y], [val, y]],
             "stroke": color, "width": 6},
            {"geom": "point", "when": f"k >= {k}", "data": [{"x": val, "y": y}],
             "r": 3.6, "fill": color},
            {"geom": "text", "when": f"k >= {k}", "x": val, "y": y,
             "text": f"{name}  {_spd(val)}",
             "align": "right" if math.log10(val) > 7 else "left",
             "size": 10, "color": color, "dy": -11},
        ]
    # 关键读数：光速与公转速度之间只差四个数量级
    layers.append({"geom": "text", "when": "k >= 5",
                   "x": math.sqrt(_v("earth_orbit_speed") * _v("c_light")), "y": 4.6,
                   "text": f"两者只差 {_v('speed_gap_c_earth'):.1f} 个数量级",
                   "align": "center", "size": 9.5, "color": ACCENT})
    steps = [
        {"k": 1, "note": f"蜗牛约 {_v('snail_speed'):g} 米每秒。这一章的下界就定在这里。"},
        {"k": 2, "note": f"人的速度挤在很窄一条带子里：步行 {_v('walk_speed'):g}、"
                         f"客机 {_v('airliner_speed'):g} 米每秒。"},
        {"k": 3, "note": f"声速 {_v('sound_speed'):g} 米每秒 —— 它不算「快」，"
                         f"只是我们日常能遇到的第一个硬上限。"},
        {"k": 4, "note": f"地球公转 {_v('orbit_km_s'):.1f} 公里每秒 —— 由天文单位与儒略年"
                         f"现算，比任何交通工具都快得多，但仍在同一个「万」的量级里。"},
        {"k": 5, "note": f"光速 {_v('c_wan_km_s'):.2f} 万公里每秒。从蜗牛到这里，一共只有 "
                         f"{_v('speed_span_decades'):.1f} 个数量级 —— 比时间那章的零头还小。"},
    ]
    return {"theme": PAPER,
            "view": {"xRange": [X0, X1], "yRange": [-0.7, 5.9], "xlog": True,
                     "pad": {"l": 30, "r": 26, "b": 46, "t": 16}},
            "layers": layers, "steps": steps}


FIGS["fig-speed"] = fig_speed


def _temp(v):
    """温度标签：小量保一位小数，中量用「万 K」，大量用尾数×10^n。"""
    if v < 1e4:
        return f"{v:,.1f} K"
    if v < 1e8:
        return f"{v / 1e4:,.0f} 万 K"
    return f"{_mant(v)} K"


def fig_temperature():
    """第 5 章：温度的阶梯。这一章的要害是**两端都有墙**。

    下端那堵墙（0 K）在这张图上根本画不出来 —— 对数轴没有 0。
    所以它只能用一支指向轴外的箭头表示：最硬的边界，恰恰无法落在图上。
    """
    X0, X1 = 1.0, 1e33
    rows = [
        ("宇宙微波背景", _v("cmb_temperature"), ACCENT),
        ("人体", _v("human_temp_k"), DIM),
        ("水的沸点", _v("water_boil_k"), DIM),
        ("太阳表面", _v("sun_surface_k"), DIM),
        ("太阳核心", _v("sun_core_k"), ACCENT2),
        ("普朗克温度", _v("planck_temp_k"), GOOD),
    ]
    layers = [
        {"geom": "axis", "xRange": [X0, X1], "yRange": [-0.9, 5.9],
         "xticks": [1.0, 1e2, 1e4, 1e8, 1e16, 1e32],
         "xticklabels": ["1 K", "100 K", "1 万 K", "1 亿 K", "1 亿亿 K", "1 亿亿亿亿 K"],
         "yticks": False,
         "xlab": "温度（对数尺度：图上等距 = 相差 10 倍）"},
        # 左墙：绝对零度。0 在对数轴上是 −∞，所以画不出来，只能标一支箭头
        {"geom": "text", "when": "k >= 1", "x": 1.05, "y": 5.55,
         "text": "← 0 K：最硬的边界，但对数轴画不出 0", "align": "left",
         "size": 9.5, "color": BAD},
    ]
    steps_k = [1, 2, 2, 3, 4, 5]
    for i, (name, val, color) in enumerate(rows):
        y = float(i)
        k = steps_k[i]
        layers += [
            {"geom": "line", "when": f"k >= {k}", "data": [[X0, y], [val, y]],
             "stroke": color, "width": 6},
            {"geom": "point", "when": f"k >= {k}", "data": [{"x": val, "y": y}],
             "r": 3.6, "fill": color},
            {"geom": "text", "when": f"k >= {k}", "x": val, "y": y,
             "text": f"{name}  {_temp(val)}",
             "align": "right" if math.log10(val) > 30 else "left",
             "size": 10, "color": color, "dy": -11},
        ]
    layers.append({"geom": "text", "when": "k >= 5", "x": 1e33, "y": 4.55,
                   "text": "现有物理在这里失效 →", "align": "right", "size": 9.5,
                   "color": GOOD})
    steps = [
        {"k": 1, "note": f"左边那堵墙是绝对零度。它不在轴上 —— 对数轴没有 0，"
                         f"所以只能画一支指向轴外的箭头。最硬的边界，恰恰落在图外。"},
        {"k": 2, "note": f"人活着的地方挤在最左边：人体 {_temp(_v('human_temp_k'))}、"
                         f"水的沸点 {_temp(_v('water_boil_k'))}。这一小段就是「液态水能存在」的窗口。"},
        {"k": 3, "note": f"太阳表面 {_temp(_v('sun_surface_k'))} —— 这只是表面，"
                         f"真正的反应发生在更里面。"},
        {"k": 4, "note": f"太阳核心 {_temp(_v('sun_core_k'))}：聚变需要这个温度，"
                         f"而它来自引力压缩，不是「烧」出来的。"},
        {"k": 5, "note": f"右端是普朗克温度 {_temp(_v('planck_temp_k'))}。超过它，"
                         f"现有的物理理论本身失效。整条轴 {_v('temp_span'):.1f} 个数量级。"},
    ]
    return {"theme": PAPER,
            "view": {"xRange": [X0, X1], "yRange": [-0.9, 5.9], "xlog": True,
                     "pad": {"l": 30, "r": 26, "b": 46, "t": 16}},
            "layers": layers, "steps": steps}


FIGS["fig-temp"] = fig_temperature


def build(ids=None):
    return {k: FIGS[k]() for k in (ids or FIGS)}
