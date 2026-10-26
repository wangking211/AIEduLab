# -*- coding: utf-8 -*-
"""《数学思想：从计数到无穷》的事实登记表。

**按章接入**：目前只接入第 10 章（混沌）。其余九章是 2026 年之前写的，
正文里的年份与常数从未登记 —— 它们是对外的欠账，不是「已经核查过」。

接入方式：`REGISTRY.enroll("ch10")`。未接入的章节不会静默跳过 ——
`check_facts.py` 会点名列出，账一直摆在那里。
"""
import math
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]          # edulab/
sys.path.insert(0, str(_REPO / "shared"))
from factreg import Registry, claim                  # noqa: E402

REGISTRY = Registry("数学思想（第 10 章）")
REGISTRY.enroll("ch10")

# ---- 文献：年份与原始论文 ----------------
REGISTRY.add(claim(
    "verhulst_year", 1838, "年", grade="文献",
    source="Verhulst, P.-F. (1838)：Notice sur la loi que la population suit "
           "dans son accroissement（逻辑斯蒂方程的最早提出）",
    url="https://doi.org/10.3406/arobs.1838.1060",
    locator="Correspondance mathématique et physique 10, 113–121",
))
REGISTRY.add(claim(
    "lorenz_year", 1963, "年", grade="文献",
    source="Lorenz, E. N. (1963)：Deterministic Nonperiodic Flow",
    url="https://doi.org/10.1175/1520-0469(1963)020%3C0130:DNF%3E2.0.CO;2",
    locator="J. Atmos. Sci. 20, 130–141",
))
REGISTRY.add(claim(
    "sharkovskii_year", 1964, "年", grade="文献",
    source="Sharkovskii, O. M. (1964)：存在周期序定理的原始论文"
           "（俄文，乌克兰数学杂志）",
    url="https://doi.org/10.1007/BF01085912",
    locator="Ukrain. Mat. Zh. 16, 61–71",
))
REGISTRY.add(claim(
    "butterfly_year", 1972, "年", grade="文献",
    source="Lorenz, E. N. (1972)：AAAS 会议演讲，标题提出「蝴蝶效应」的说法",
    url="https://eapsweb.mit.edu/sites/default/files/Lorenz_1972.pdf",
    locator="Does the Flap of a Butterfly's Wings in Brazil Set Off a Tornado in Texas?",
))
REGISTRY.add(claim(
    "li_yorke_year", 1975, "年", grade="文献",
    source="Li, T.-Y. & Yorke, J. A. (1975)：Period Three Implies Chaos",
    url="https://doi.org/10.1080/00029890.1975.11994008",
    locator="Amer. Math. Monthly 82, 985–992",
))

# ---- 约定：演示参数 ----------------
REGISTRY.add(claim(
    "r_355", 3.55, "", grade="约定",
    note="第 4 档演示参数：r = 3.55 落在四周期窗口内，用来展示「再裂一次」",
))
REGISTRY.add(claim(
    "factor_28", math.exp(-0.22314355131420976), "", grade="现算",
    recompute=lambda: math.exp(-0.22314355131420976),
    note="e^{λ(2.8)} = 0.8：图上读数「误差每步乘 0.8」的出处（λ 由内核现算）",
))
