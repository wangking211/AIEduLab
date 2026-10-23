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
# =====================================================================
# 第 4 章：速度（这一章的结论是「窄」）
# =====================================================================
REGISTRY.add(claim(
    "snail_speed", 1.0e-3, "m/s", grade="约定",
    note="蜗牛速度按 1 毫米每秒取整（量级示意）",
))
REGISTRY.add(claim(
    "walk_speed", 1.4, "m/s", grade="约定",
    note="步行速度按 1.4 米每秒（演示值）",
))
REGISTRY.add(claim(
    "airliner_speed", 250.0, "m/s", grade="约定",
    note="民航巡航速度按 250 米每秒（约 900 公里每小时，演示值）",
))
REGISTRY.add(claim(
    "sound_speed", 343.0, "m/s", grade="约定",
    note="声速取 20°C 干空气中的约 343 米每秒；它随温度变化，所以这里只作量级",
))
REGISTRY.add(claim(
    "earth_orbit_speed",
    2.0 * math.pi * V("au_m") / V("year_sec"), "m/s", grade="现算",
    recompute=lambda: 2.0 * math.pi * V("au_m") / V("year_sec"),
    note="公转速度 = 周长 ÷ 周期：两个登记值（天文单位、儒略年）算出来，"
         "不需要另查一个「地球公转速度」",
))
REGISTRY.add(claim(
    "c_wan_km_s", V("c_light") / 1e4, "万公里/秒", grade="现算",
    recompute=lambda: V("c_light") / 1e4,
    texts=["万公里每秒"],
))
REGISTRY.add(claim(
    "orbit_km_s", V("earth_orbit_speed") / 1e3, "公里/秒", grade="现算",
    recompute=lambda: V("earth_orbit_speed") / 1e3,
))
REGISTRY.add(claim(
    "speed_span_decades",
    math.log10(V("c_light")) - math.log10(V("snail_speed")), "个数量级", grade="现算",
    recompute=lambda: math.log10(V("c_light")) - math.log10(V("snail_speed")),
))
REGISTRY.add(claim(
    "energy_1kg_90c_j",
    (1.0 / math.sqrt(1.0 - 0.9 ** 2) - 1.0) * V("c_light") ** 2, "J", grade="现算",
    recompute=lambda: (1.0 / math.sqrt(1.0 - 0.9 ** 2) - 1.0) * V("c_light") ** 2,
    note="把 1 千克加速到 0.9c 所需的动能 =(γ−1)mc²：γ = 1/√(1−0.81) ≈ 2.294",
))
REGISTRY.add(claim(
    "energy_1kg_90c_e17", V("energy_1kg_90c_j") / 1e17, "×10¹⁷ 焦耳", grade="现算",
    recompute=lambda: V("energy_1kg_90c_j") / 1e17, texts=["10¹⁷"],
))
REGISTRY.add(claim(
    "gamma_90c", 1.0 / math.sqrt(1.0 - 0.9 ** 2), "", grade="现算",
    recompute=lambda: 1.0 / math.sqrt(1.0 - 0.9 ** 2),
))
REGISTRY.add(claim(
    "speed_gap_c_earth",
    math.log10(V("c_light") / V("earth_orbit_speed")), "个数量级", grade="现算",
    recompute=lambda: math.log10(V("c_light") / V("earth_orbit_speed")),
    note="光速与地球公转速度的比值取对数：这一章的核心读数",
))
# =====================================================================
# 第 5 章：温度（唯一两端都有墙的量）
# =====================================================================
REGISTRY.add(claim(
    "k_boltzmann", 1.380649e-23, "J/K", grade="约定",
    note="2019 年 SI 修订把玻尔兹曼常数**定义**为这个值（开尔文由此定出）",
))

REGISTRY.add(claim(
    "cmb_temperature", 2.72548, "K", grade="实测",
    source="Fixsen 2009, ApJ 707, 916（COBE FIRAS 的宇宙微波背景温度）",
    url="https://doi.org/10.1088/0004-637X/707/2/916",
    uncertainty=0.00057,
    texts=["2.725"],
))
REGISTRY.add(claim(
    "human_temp_k", 310.15, "K", grade="约定",
    note="人体温度按 37°C 折算成 310.15 K（演示值）",
))
REGISTRY.add(claim(
    "water_boil_k", 373.15, "K", grade="约定",
    note="水的沸点 100°C = 373.15 K：这是摄氏温标的定义点之一",
))
REGISTRY.add(claim(
    "sun_surface_k", 5772.0, "K", grade="约定",
    note="IAU 2015 把太阳名义有效温度**定义**为 5772 K（名义值）",
))
REGISTRY.add(claim(
    "sun_core_k", 1.57e7, "K", grade="文献",
    source="Bahcall, Pinsonneault & Basu 2001, ApJ 555, 990（标准太阳模型）",
    url="https://doi.org/10.1086/321493",
    locator="标准太阳模型的中心温度约 1.57×10⁷ K",
))
REGISTRY.add(claim(
    "planck_temp_k",
    math.sqrt(V("hbar") * V("c_light") ** 5 / (V("g_newton") * V("k_boltzmann") ** 2)),
    "K", grade="现算",
    recompute=lambda: math.sqrt(V("hbar") * V("c_light") ** 5
                                / (V("g_newton") * V("k_boltzmann") ** 2)),
    note="普朗克温度 = √(ħc⁵/(Gk_B²))：由四条登记（ħ 与 k_B 是定义、G 是实测）推出来",
))
REGISTRY.add(claim(
    "temp_span",
    math.log10(V("planck_temp_k")) - math.log10(V("cmb_temperature")),
    "个数量级", grade="现算",
    recompute=lambda: math.log10(V("planck_temp_k")) - math.log10(V("cmb_temperature")),
))
REGISTRY.add(claim(
    "planck_temp_e32", V("planck_temp_k") / 1e32, "×10³² K", grade="现算",
    recompute=lambda: V("planck_temp_k") / 1e32, texts=["10³²"],
))
REGISTRY.add(claim(
    "sun_core_e7", V("sun_core_k") / 1e7, "×10⁷ K", grade="现算",
    recompute=lambda: V("sun_core_k") / 1e7, texts=["10⁷"],
))
# =====================================================================
# 第 6 章：能量（为什么它能被放在一条轴上）
# =====================================================================
REGISTRY.add(claim(
    "breath_j", 1.0, "J", grade="约定",
    note="「一次平静呼吸约 1 焦耳」是量级示意（机械功与代谢能不是一回事，这里只取量级）",
))
REGISTRY.add(claim(
    "bullet_j", 2.0e3, "J", grade="约定",
    note="步枪子弹的枪口动能按 2 千焦取整（量级示意，随弹种变化很大）",
))
REGISTRY.add(claim(
    "meal_j", 2.0e6, "J", grade="约定",
    note="一顿饭按 500 千卡（约 2 兆焦）计，演示值",
))
REGISTRY.add(claim(
    "lightning_j", 1.0e9, "J", grade="文献",
    source="Dwyer & Uman 2014, Physics Reports 534, 147–241（闪电物理综述）",
    url="https://doi.org/10.1016/j.physrep.2013.12.002",
    locator="典型云地闪电释放能量约 10⁹ J（量级）",
))
REGISTRY.add(claim(
    "tnt_ton_j", 4.184e9, "J", grade="约定",
    note="1 吨 TNT 当量 = 4.184×10⁹ J：这是**约定**，不是测量 —— 它是为了把核爆能量"
         "换算成「多少吨炸药」而人为固定的换算率",
))
REGISTRY.add(claim(
    "hiroshima_kt", 15.0, "千吨 TNT", grade="文献",
    source="广岛「小男孩」的当量估计（约 15 千吨 TNT，通行的历史估算值）",
    url="https://www.atomicheritage.org/history/little-boy",
    locator="通行为 13–18 千吨，本文取 15 千吨",
))
REGISTRY.add(claim(
    "hiroshima_j", V("hiroshima_kt") * 1000.0 * V("tnt_ton_j"), "J", grade="现算",
    recompute=lambda: V("hiroshima_kt") * 1000.0 * V("tnt_ton_j"),
    note="当量 × 每吨 TNT 的焦耳数：两个登记值相乘，没有另查「广岛释放多少焦耳」",
))
REGISTRY.add(claim(
    "sun_luminosity_w", 3.828e26, "W", grade="约定",
    note="IAU 2015 把太阳名义光度**定义**为 3.828×10²⁶ W（名义值）",
))
REGISTRY.add(claim(
    "supernova_j", 1.0e44, "J", grade="文献",
    source="核坍缩超新星释放能量的通行量级估计（中微子带走绝大部分）",
    url="https://doi.org/10.1146/annurev.astro.46.060407.145143",
    locator="量级约 10⁴⁴ J（不同文献取 10⁴⁴–10⁴⁶ J）",
))
REGISTRY.add(claim(
    "energy_span",
    math.log10(V("supernova_j")) - math.log10(V("breath_j")), "个数量级", grade="现算",
    recompute=lambda: math.log10(V("supernova_j")) - math.log10(V("breath_j")),
))

REGISTRY.add(claim("meal_e6", V("meal_j") / 1e6, "×10⁶ 焦耳", grade="现算",
                   recompute=lambda: V("meal_j") / 1e6, texts=["10⁶"]))
REGISTRY.add(claim("lightning_e9", V("lightning_j") / 1e9, "×10⁹ 焦耳", grade="现算",
                   recompute=lambda: V("lightning_j") / 1e9, texts=["10⁹"]))
REGISTRY.add(claim("hiroshima_e13", V("hiroshima_j") / 1e13, "×10¹³ 焦耳", grade="现算",
                   recompute=lambda: V("hiroshima_j") / 1e13, texts=["10¹³"]))
REGISTRY.add(claim("sun_e26", V("sun_luminosity_w") / 1e26, "×10²⁶ 瓦", grade="现算",
                   recompute=lambda: V("sun_luminosity_w") / 1e26, texts=["10²⁶"]))
REGISTRY.add(claim("supernova_e44", V("supernova_j") / 1e44, "×10⁴⁴ 焦耳", grade="现算",
                   recompute=lambda: V("supernova_j") / 1e44, texts=["10⁴⁴"]))