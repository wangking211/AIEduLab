# -*- coding: utf-8 -*-
"""《万物尺度》的事实登记表 —— 由 `edulab/tools/check_facts.py` 强制核查。

每个数字都必须回答「从哪来」：

    约定  单位定义或演示参数（写清为什么只能是约定）
    实测  观测值 + 不确定度 + 可核链接
    文献  文献里的定值 + 可核定位（表号 / 页码 / DOI）
    现算  由本表里的其它登记算出来（recompute 会被闸门**真的调用**并比对）

注意「链」：普朗克时间不是抄来的，它由 c、ħ、G 三个登记值算出来；
宇宙年龄的「亿年」写法由实测值算出来。改上游一个数，下游全部跟着变 —— 这正是要的。
"""
import math
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]          # edulab/
sys.path.insert(0, str(_REPO / "shared"))
from factreg import Registry, claim                  # noqa: E402

REGISTRY = Registry("万物尺度（样章）")


def V(cid):
    """取另一条登记的值 —— 让「现算」级真的建立在别的登记之上，而不是重新写一遍字面量。"""
    return REGISTRY.items[cid]["value"]


# =====================================================================
# 一、约定：单位定义（这些不是测量结果，是**定义**）
# =====================================================================
REGISTRY.add(claim(
    "c_light", 299792458.0, "m/s", grade="约定",
    note="1983 年国际计量大会把真空光速**定义**为这个整数（米由此反推），"
         "所以它不是测量结果，写成一个测量值反而不准确",
))
REGISTRY.add(claim(
    "day_sec", 86400.0, "s", grade="约定",
    note="一天 = 86400 秒，这是民用日的定义值",
))
REGISTRY.add(claim(
    "hbar", 1.054571817e-34, "J·s", grade="约定",
    note="2019 年 SI 修订后普朗克常数 h 被定义为 6.62607015×10⁻³⁴ J·s，"
         "ħ = h/2π 随之完全确定（不是测量值）",
))
REGISTRY.add(claim(
    "heartbeat_s", 1.0, "s", grade="约定",
    note="「一次心跳 ≈ 1 秒」是量级示意，不是测量值，不用于任何计算",
))
REGISTRY.add(claim(
    "lifespan_year", 80.0, "年", grade="约定",
    note="「一生」取 80 年作演示值（不是任何地区的人均寿命统计）",
))

# =====================================================================
# 二、实测：观测值（必须带不确定度）
# =====================================================================
REGISTRY.add(claim(
    "g_newton", 6.67430e-11, "m³/(kg·s²)", grade="实测",
    source="CODATA 2018 推荐值（牛顿引力常数）",
    url="https://physics.nist.gov/cgi-bin/cuu/Value?bg",
    uncertainty=0.00015e-11,
))
REGISTRY.add(claim(
    "universe_age_year", 1.3797e10, "年", grade="实测",
    source="Planck 2018 结果 VI（A&A 641, A6）表 2：Age = 13.797 Gyr，"
           "TT,TE,EE+lowE+lensing 组合",
    url="https://doi.org/10.1051/0004-6361/201833910",
    uncertainty=0.023e9,
    texts=["Planck 2018"],       # 正文里会提到这个来源名，允许它出现
))

# =====================================================================
# 三、文献：别的领域给出的定值（必须给可核定位）
# =====================================================================
REGISTRY.add(claim(
    "earth_age_year", 4.54e9, "年", grade="文献",
    source="USGS《Age of the Earth》科普页",
    url="https://www.usgs.gov/faqs/how-old-earth",
    locator="\"4.54 billion years\"（该页给出的常用值；详见页内引用）",
))
REGISTRY.add(claim(
    "kpg_year", 6.6043e7, "年", grade="文献",
    source="Renne et al. 2013, Science 339, 684–687（K–Pg 界线年龄）",
    url="https://doi.org/10.1126/science.1232990",
    locator="66.043 ± 0.011 Ma（摘要与表 1）",
))
REGISTRY.add(claim(
    "homo_sapiens_year", 3.15e5, "年", grade="文献",
    source="Hublin et al. 2017, Nature 546, 289–293（Jebel Irhoud 化石年代）",
    url="https://doi.org/10.1038/nature22336",
    locator="315 ± 34 ka（摘要）",
))

# =====================================================================
# 四、现算：由上面的登记推出来（闸门会真的重算并比对）
# =====================================================================
REGISTRY.add(claim(
    "year_sec", V("day_sec") * 365.25, "s", grade="现算",
    recompute=lambda: V("day_sec") * 365.25,
    note="儒略年 = 365.25 天；天文学里用它定义光年（不是公历年）",
))
REGISTRY.add(claim(
    "planck_time_s",
    math.sqrt(V("hbar") * V("g_newton") / V("c_light") ** 5), "s", grade="现算",
    recompute=lambda: math.sqrt(V("hbar") * V("g_newton") / V("c_light") ** 5),
    note="普朗克时间 = √(ħG/c⁵)：由三个定义/测量常量拼出来的量，本身没有被直接测量过",
))
REGISTRY.add(claim(
    "universe_age_sec", V("universe_age_year") * V("year_sec"), "s", grade="现算",
    recompute=lambda: V("universe_age_year") * V("year_sec"),
))
REGISTRY.add(claim(
    "universe_age_yi", V("universe_age_year") / 1e8, "亿年", grade="现算",
    recompute=lambda: V("universe_age_year") / 1e8,
    note="把 13.797 Gyr 换成中文习惯的「亿年」",
))
REGISTRY.add(claim(
    "earth_age_yi", V("earth_age_year") / 1e8, "亿年", grade="现算",
    recompute=lambda: V("earth_age_year") / 1e8,
))
REGISTRY.add(claim(
    "homo_wan", V("homo_sapiens_year") / 1e4, "万年", grade="现算",
    recompute=lambda: V("homo_sapiens_year") / 1e4,
))
REGISTRY.add(claim(
    "lifespan_sec", V("lifespan_year") * V("year_sec"), "s", grade="现算",
    recompute=lambda: V("lifespan_year") * V("year_sec"),
))
REGISTRY.add(claim(
    "planck_time_e44", V("planck_time_s") * 1e44, "×10⁻⁴⁴ 秒", grade="现算",
    recompute=lambda: V("planck_time_s") * 1e44,
    texts=["10⁻⁴⁴ 秒"],
    note="正文写「5.391×10⁻⁴⁴ 秒」：尾数由本表算出来，指数写成上标（不含阿拉伯数字），"
         "这样正文既不手写尾数，也不会被 F4 当成漏登记的数字",
))
REGISTRY.add(claim(
    "span_decades",
    math.log10(V("universe_age_sec")) - math.log10(V("planck_time_s")),
    "个数量级", grade="现算",
    recompute=lambda: math.log10(V("universe_age_sec")) - math.log10(V("planck_time_s")),
    note="图上的横轴跨度：从普朗克时间到宇宙年龄，共这么多个数量级",
))
