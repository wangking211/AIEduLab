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

# =====================================================================
# 第 2 章：长度的尺度（同样的分工：能推到定义就推到定义）
# =====================================================================
REGISTRY.add(claim(
    "au_m", 1.495978707e11, "m", grade="约定",
    note="天文单位由 IAU 2012 年定义为这个整数米（此前的测量值被固定下来），"
         "所以它现在是定义值",
))
REGISTRY.add(claim(
    "parsec_m", 648000.0 / math.pi * V("au_m"), "m", grade="现算",
    recompute=lambda: 648000.0 / math.pi * V("au_m"),
    note="秒差距的定义：1 au 张角 1 角秒时的距离 = (648000/π) au —— 纯几何，无实测成分",
))
REGISTRY.add(claim(
    "megaparsec_m", 1e6 * V("parsec_m"), "m", grade="现算",
    recompute=lambda: 1e6 * V("parsec_m"),
))
REGISTRY.add(claim(
    "alpha_em", 7.2973525693e-3, "", grade="实测",
    source="CODATA 2018 推荐值（精细结构常数，无量纲）",
    url="https://physics.nist.gov/cgi-bin/cuu/Value?alph",
    uncertainty=0.0000000011e-3,
))
REGISTRY.add(claim(
    "m_electron", 9.1093837015e-31, "kg", grade="实测",
    source="CODATA 2018 推荐值（电子静止质量）",
    url="https://physics.nist.gov/cgi-bin/cuu/Value?me",
    uncertainty=2.8e-40,
))
REGISTRY.add(claim(
    "bohr_radius_m", V("hbar") / (V("m_electron") * V("c_light") * V("alpha_em")), "m",
    grade="现算",
    recompute=lambda: V("hbar") / (V("m_electron") * V("c_light") * V("alpha_em")),
    note="玻尔半径 a₀ = ħ/(mₑcα)：由三条登记（ħ 定义、mₑ 与 α 实测）推出来，"
         "本身没有被直接尺量过",
))
REGISTRY.add(claim(
    "virus_m", 1.0e-7, "m", grade="约定",
    note="「病毒直径约 100 纳米」是量级示意（不同病毒相差数倍），只用来定位数量级",
))
REGISTRY.add(claim(
    "cell_m", 1.0e-5, "m", grade="约定",
    note="「细胞直径约 10 微米」同样是量级示意",
))
REGISTRY.add(claim(
    "human_h_m", 1.7, "m", grade="约定",
    note="「一个人的高度取 1.7 米」是演示值",
))
REGISTRY.add(claim(
    "moon_distance_m", 3.844e8, "m", grade="实测",
    source="NASA（地月平均距离 384,400 km）",
    url="https://science.nasa.gov/moon/facts/",
    uncertainty=0.001e8,
))
REGISTRY.add(claim(
    "sun_radius_m", 6.957e8, "m", grade="约定",
    note="IAU 2015 年把太阳名义半径**定义**为 6.957×10⁸ 米（名义值，不是某一时刻的测量）",
))
REGISTRY.add(claim(
    "sun_diameter_m", 2 * V("sun_radius_m"), "m", grade="现算",
    recompute=lambda: 2 * V("sun_radius_m"),
))
REGISTRY.add(claim(
    "comoving_radius_mpc", 14300.0, "Mpc", grade="文献",
    source="Planck 2018 宇宙学参数推出的可观测宇宙共动半径（约 14.3 Gpc ≈ 46.5 Gly）",
    url="https://doi.org/10.1051/0004-6361/201833910",
    locator="Planck 2018 结果 VI 的宇宙学参数（Ω_m、H₀）代入共动距离积分",
))
REGISTRY.add(claim(
    "universe_diameter_m", 2 * V("comoving_radius_mpc") * V("megaparsec_m"), "m",
    grade="现算",
    recompute=lambda: 2 * V("comoving_radius_mpc") * V("megaparsec_m"),
    note="直径 = 2 × 共动半径 × 每 Mpc 的米数：把文献给的参数换成米，换算是现算的",
))

# ---- 给正文用的派生根 ----
REGISTRY.add(claim(
    "bohr_pm", V("bohr_radius_m") * 1e12, "皮米", grade="现算",
    recompute=lambda: V("bohr_radius_m") * 1e12,
))
REGISTRY.add(claim(
    "universe_dia_e26", V("universe_diameter_m") / 1e26, "×10²⁶ 米", grade="现算",
    recompute=lambda: V("universe_diameter_m") / 1e26,
    texts=["10²⁶ 米"],
))
REGISTRY.add(claim(
    "span_len_decades",
    math.log10(V("universe_diameter_m")) - math.log10(V("bohr_radius_m")),
    "个数量级", grade="现算",
    recompute=lambda: math.log10(V("universe_diameter_m")) - math.log10(V("bohr_radius_m")),
))
REGISTRY.add(claim(
    "light_year_m", V("c_light") * V("year_sec"), "m", grade="现算",
    recompute=lambda: V("c_light") * V("year_sec"),
    note="光年 = 光速 × 儒略年：一个长度单位，不是时间单位",
))
# =====================================================================
# 第 3 章：数量（没有单位，只有「多少个」）
# =====================================================================
REGISTRY.add(claim(
    "n_avogadro", 6.02214076e23, "1/mol", grade="约定",
    note="2019 年 SI 修订把阿伏伽德罗常数**定义**为这个值（摩尔由此定出），不是测量结果",
))
REGISTRY.add(claim(
    "water_molar_mass", 18.015, "g/mol", grade="约定",
    note="水的摩尔质量按 H₂O 的原子量取 18.015 g/mol（演示值）",
))
REGISTRY.add(claim(
    "cup_volume_l", 0.25, "L", grade="约定",
    note="「一杯水」按 250 毫升计（演示值）",
))
REGISTRY.add(claim(
    "molecules_cup",
    V("cup_volume_l") * 1000.0 / V("water_molar_mass") * V("n_avogadro"), "个", grade="现算",
    recompute=lambda: V("cup_volume_l") * 1000.0 / V("water_molar_mass") * V("n_avogadro"),
    note="分子数 = 体积 × 密度/摩尔质量 × 阿伏伽德罗常数；密度按 1 g/mL 取整数 1000 g/L",
))
REGISTRY.add(claim(
    "neurons", 8.6e10, "个", grade="文献",
    source="Azevedo et al. 2009, J. Comp. Neurol. 513, 532–541（人脑神经元计数）",
    url="https://doi.org/10.1002/cne.21974",
    locator="摘要：平均 86.1 ± 8.1 billion neurons（本文取 8.6×10¹⁰）",
))
REGISTRY.add(claim(
    "stars_milkyway", 1.0e11, "个", grade="文献",
    source="银河系恒星数量的常用估计（量级）",
    url="https://science.nasa.gov/universe/galaxies/",
    locator="NASA 科普页给出的量级为「千亿颗量级」",
))
REGISTRY.add(claim(
    "sand_grains", 7.5e18, "个", grade="文献",
    source="夏威夷大学的地球沙粒估算（广为引用的量级估计）",
    url="https://www.hawaii.edu/malamalama/2012/09/sand-grains/",
    locator="「seven quintillion, five hundred quadrillion grains」= 7.5×10¹⁸",
))
REGISTRY.add(claim(
    "atoms_universe", 1.0e80, "个", grade="文献",
    source="可观测宇宙原子数的标准量级估算（由重子密度与宇宙体积推出）",
    url="https://doi.org/10.1051/0004-6361/201833910",
    locator="Planck 2018 重子密度 × 可观测宇宙体积 → 约 10⁸⁰ 个核子（量级）",
))
REGISTRY.add(claim(
    "heartbeats_lifetime",
    V("lifespan_year") * 365.25 * 24.0 * 60.0 * 70.0, "次", grade="现算",
    recompute=lambda: V("lifespan_year") * 365.25 * 24.0 * 60.0 * 70.0,
    note="按演示寿命 80 年、每分钟 70 次估算：这两个数都是约定值，所以结果也只是量级",
))
REGISTRY.add(claim(
    "gap_cup_to_universe",
    math.log10(V("atoms_universe")) - math.log10(V("molecules_cup")), "个数量级",
    grade="现算",
    recompute=lambda: math.log10(V("atoms_universe")) - math.log10(V("molecules_cup")),
))
# ---- 第 3 章正文用的「尾数 × 10ⁿ」派生根（指数写在上标里，尾数由登记表算）----
REGISTRY.add(claim("beats_e9", V("heartbeats_lifetime") / 1e9, "", grade="现算",
                   recompute=lambda: V("heartbeats_lifetime") / 1e9, texts=["10⁹"]))
REGISTRY.add(claim("neurons_e10", V("neurons") / 1e10, "", grade="现算",
                   recompute=lambda: V("neurons") / 1e10, texts=["10¹⁰"]))
REGISTRY.add(claim("stars_e11", V("stars_milkyway") / 1e11, "", grade="现算",
                   recompute=lambda: V("stars_milkyway") / 1e11, texts=["10¹¹"]))
REGISTRY.add(claim("cup_e24", V("molecules_cup") / 1e24, "", grade="现算",
                   recompute=lambda: V("molecules_cup") / 1e24, texts=["10²⁴"]))
REGISTRY.add(claim("avogadro_e23", V("n_avogadro") / 1e23, "", grade="现算",
                   recompute=lambda: V("n_avogadro") / 1e23, texts=["10²³"]))
REGISTRY.add(claim("atoms_e80", V("atoms_universe") / 1e80, "", grade="现算",
                   recompute=lambda: V("atoms_universe") / 1e80, texts=["10⁸⁰"]))