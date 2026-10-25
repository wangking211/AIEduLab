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