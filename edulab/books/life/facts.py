# -*- coding: utf-8 -*-
"""《生命的尺度》事实登记表 —— 由 `edulab/tools/check_facts.py` 强制核查。

这一章的核心是一张**双对数散点图**：横轴是世代时间，纵轴是成体体长。
八个物种的体长跨近八个数量级，而「体长 ÷ 世代时间」只跨不到两个数量级 ——
这条窄带是本章的结论，也是本章全部数值的理由。

注意分级：单物种的体长与世代时间取的是**量级**（grade=约定，note 里写明），
因为同种内部差异很大（品种、温度、营养）。但结论对输入不敏感：
即使每个点各偏一倍，带的宽度仍在两个数量级内 —— 这一句必须写进正文。
"""
import math
import sys
from fractions import Fraction
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]          # edulab/
sys.path.insert(0, str(_REPO / "shared"))
from factreg import Registry, claim                  # noqa: E402

REGISTRY = Registry("生命的尺度（样章）")


def V(cid):
    return REGISTRY.items[cid]["value"]


def _species(cid, name, size_m, gen_s, note):
    """登记一个物种的体长与世代时间，并现算「特征生长速度」。"""
    REGISTRY.add(claim(f"{cid}_size", size_m, "m", grade="约定", note=note))
    REGISTRY.add(claim(f"{cid}_gen", gen_s, "s", grade="约定", note=note))
    REGISTRY.add(claim(
        f"{cid}_rate", V(f"{cid}_size") / V(f"{cid}_gen"), "m/s", grade="现算",
        recompute=lambda c=cid: V(f"{c}_size") / V(f"{c}_gen"),
        note="体长 ÷ 世代时间 —— 本章的纵轴除以横轴；这一列只跨一个多数量级",
    ))


_MAG = "体长与世代时间都取量级示意（同种内随温度、营养、品种变化很大）"

_species("ecoli", "大肠杆菌", 2.0e-6, 20.0 * 60.0, _MAG)
_species("yeast", "酿酒酵母", 5.0e-6, 90.0 * 60.0, _MAG)
_species("paramecium", "草履虫", 2.0e-4, 86400.0, _MAG)
_species("drosophila", "果蝇", 2.5e-3, 10.0 * 86400.0, _MAG)
_species("mouse", "小鼠", 9.0e-2, 90.0 * 86400.0, _MAG)
_species("human", "人", 1.7, 25.0 * 365.25 * 86400.0, _MAG)
_species("whale", "蓝鲸", 25.0, 10.0 * 365.25 * 86400.0, _MAG)
_species("redwood", "红杉", 80.0, 100.0 * 365.25 * 86400.0, _MAG)

REGISTRY.add(claim(
    "rate_min",
    min(V(f"{c}_rate") for c in ("ecoli", "yeast", "paramecium", "drosophila",
                                 "mouse", "human", "whale", "redwood")),
    "m/s", grade="现算",
    recompute=lambda: min(V(f"{c}_rate") for c in ("ecoli", "yeast", "paramecium",
                                                   "drosophila", "mouse", "human",
                                                   "whale", "redwood")),
))
REGISTRY.add(claim(
    "rate_max",
    max(V(f"{c}_rate") for c in ("ecoli", "yeast", "paramecium", "drosophila",
                                 "mouse", "human", "whale", "redwood")),
    "m/s", grade="现算",
    recompute=lambda: max(V(f"{c}_rate") for c in ("ecoli", "yeast", "paramecium",
                                                   "drosophila", "mouse", "human",
                                                   "whale", "redwood")),
))
REGISTRY.add(claim(
    "rate_span",
    math.log10(V("rate_max")) - math.log10(V("rate_min")), "个数量级", grade="现算",
    recompute=lambda: math.log10(V("rate_max")) - math.log10(V("rate_min")),
    note="这一列的跨度：比体长那 7 个数量级窄得多 —— 本章的核心读数",
))
REGISTRY.add(claim(
    "size_span",
    math.log10(V("redwood_size")) - math.log10(V("ecoli_size")), "个数量级", grade="现算",
    recompute=lambda: math.log10(V("redwood_size")) - math.log10(V("ecoli_size")),
))
REGISTRY.add(claim(
    "gen_span",
    math.log10(V("redwood_gen")) - math.log10(V("ecoli_gen")), "个数量级", grade="现算",
    recompute=lambda: math.log10(V("redwood_gen")) - math.log10(V("ecoli_gen")),
))

# ---- 正文用的「尾数 ×10⁻⁹」派生根 ----
REGISTRY.add(claim("ecoli_rate_e9", V("ecoli_rate") * 1e9, "×10⁻⁹ 米每秒", grade="现算",
                   recompute=lambda: V("ecoli_rate") * 1e9, texts=["10⁻⁹"]))
REGISTRY.add(claim("human_rate_e9", V("human_rate") * 1e9, "×10⁻⁹ 米每秒", grade="现算",
                   recompute=lambda: V("human_rate") * 1e9, texts=["10⁻⁹"]))
# =====================================================================
# 第 2 章：代谢（标度律：用五个物种回归一个指数）
# =====================================================================
def _animal(cid, name, mass_kg, bmr_kcal_d):
    """登记一个物种的体重与基础代谢率（文献值，取量级）。"""
    REGISTRY.add(claim(f"{cid}_mass", mass_kg, "kg", grade="文献",
                       source="生理学常用表格（基础代谢率）与 Kleiber 定律的原始数据族",
                       url="https://doi.org/10.1017/CBO9780511790614",
                       locator=f"{name}：体重与基础代谢率的常用量级值"))
    REGISTRY.add(claim(f"{cid}_bmr", bmr_kcal_d, "千卡/天", grade="文献",
                       source="同上",
                       url="https://doi.org/10.1017/CBO9780511790614",
                       locator=f"{name}：基础代谢率量级"))


_animal("mouse", "小鼠", 0.025, 4.0)
_animal("rat", "大鼠", 0.30, 22.0)
_animal("human_m", "人", 70.0, 1700.0)
_animal("horse", "马", 600.0, 7000.0)
_animal("elephant", "大象", 3000.0, 24000.0)

ANIMALS = ("mouse", "rat", "human_m", "horse", "elephant")


def _fit_slope():
    """对数—对数最小二乘的斜率：log10(代谢) 对 log10(体重)。"""
    xs = [math.log10(V(f"{a}_mass")) for a in ANIMALS]
    ys = [math.log10(V(f"{a}_bmr")) for a in ANIMALS]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den


REGISTRY.add(claim(
    "metabolic_exponent", _fit_slope(), "", grade="现算",
    recompute=_fit_slope,
    note="五个物种的 log-log 最小二乘斜率。Kleiber 的经典值是 3/4 = 0.75；"
         "按表面积推算会得到 2/3 ≈ 0.667 —— 两者的差距就是这一章要讲的事",
))
REGISTRY.add(claim(
    "metabolic_slope_quarter", Fraction(3, 4), "", grade="约定",
    note="3/4 是 Kleiber 定律的经验指数（不是从第一原理推出来的）",
))
REGISTRY.add(claim(
    "metabolic_slope_two_thirds", Fraction(2, 3), "", grade="现算",
    recompute=lambda: Fraction(2, 3),
    note="按「散热正比于表面积」推算的指数：面积 ∝ 质量^(2/3)",
))
REGISTRY.add(claim(
    "metabolic_ratio_elephant_mouse", V("elephant_bmr") / V("mouse_bmr"), "", grade="现算",
    recompute=lambda: V("elephant_bmr") / V("mouse_bmr"),
    note="大象与小鼠的代谢率之比（约十万倍）",
))
REGISTRY.add(claim(
    "mass_ratio_elephant_mouse", V("elephant_mass") / V("mouse_mass"), "", grade="现算",
    recompute=lambda: V("elephant_mass") / V("mouse_mass"),
    note="体重之比（约十万倍）—— 但代谢率之比比它小得多",
))
REGISTRY.add(claim(
    "per_kg_elephant_vs_mouse",
    (V("elephant_bmr") / V("elephant_mass")) / (V("mouse_bmr") / V("mouse_mass")),
    "", grade="现算",
    recompute=lambda: (V("elephant_bmr") / V("elephant_mass"))
                      / (V("mouse_bmr") / V("mouse_mass")),
    note="每千克代谢率之比：大象只有小鼠的这个比例 —— 「体型越大越省」的证据",
))
REGISTRY.add(claim("mass_ratio", V("mass_ratio_elephant_mouse"), "", grade="现算",
                   recompute=lambda: V("mass_ratio_elephant_mouse")))
REGISTRY.add(claim("bmr_ratio", V("metabolic_ratio_elephant_mouse"), "", grade="现算",
                   recompute=lambda: V("metabolic_ratio_elephant_mouse")))
REGISTRY.add(claim("per_kg_pct", V("per_kg_elephant_vs_mouse") * 100.0, "%", grade="现算",
                   recompute=lambda: V("per_kg_elephant_vs_mouse") * 100.0))