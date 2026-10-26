# -*- coding: utf-8 -*-
"""《数学思想：从计数到无穷》的事实登记表。

**按章接入**：目前只接入第 10 章（混沌）。其余九章是 2026 年之前写的，
正文里的年份与常数从未登记 —— 它们是对外的欠账，不是「已经核查过」。

接入方式：`REGISTRY.enroll("ch10", "ch09", "ch08")`。未接入的章节不会静默跳过 ——
`check_facts.py` 会点名列出，账一直摆在那里。
"""
import math
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]          # edulab/
sys.path.insert(0, str(_REPO / "shared"))
from factreg import Registry, claim                  # noqa: E402

REGISTRY = Registry("数学思想（第 10 章）")
REGISTRY.enroll("ch10", "ch09", "ch08")

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

# ---- 第 9 章（信息）----------------
REGISTRY.add(claim(
    "shannon_year", 1948, "年", grade="文献",
    source="Shannon, C. E. (1948)：A Mathematical Theory of Communication",
    url="https://doi.org/10.1002/j.1538-7305.1948.tb01338.x",
    locator="Bell System Technical Journal 27, 379–423 与 623–656",
))
REGISTRY.add(claim(
    "huffman_year", 1952, "年", grade="文献",
    source="Huffman, D. A. (1952)：A Method for the Construction of "
           "Minimum-Redundancy Codes",
    url="https://doi.org/10.1109/JRPROC.1952.273898",
    locator="Proceedings of the IRE 40, 1098–1101",
))
# ---- 第 8 章（计算）----------------
def _ref(cid, year, src, url, loc):
    REGISTRY.add(claim(cid, year, "年", grade="文献", source=src, url=url, locator=loc))


_ref("hilbert_year", 1900,
     "Hilbert, D. (1900)：巴黎国际数学家大会上的 23 个问题演讲",
     "https://mathworld.wolfram.com/HilbertsProblems.html",
     "问题 10：丢番图方程的一般可解性判定")
_ref("entscheidungsproblem_year", 1928,
     "Hilbert, D. & Ackermann, W. (1928)：Grundzüge der theoretischen Logik"
     "（判定问题被明确提出的教科书）",
     "https://archive.org/details/grundzgedertheo00hilb",
     "该书提出的 Entscheidungsproblem（判定问题）")
_ref("turing_year", 1936,
     "Turing, A. M. (1936)：On Computable Numbers, with an Application to the "
     "Entscheidungsproblem",
     "https://doi.org/10.1112/plms/s2-42.1.230",
     "Proc. London Math. Soc. s2-42, 230–265（图灵当年 24 岁）")
_ref("rice_year", 1953,
     "Rice, H. G. (1953)：Classes of recursively enumerable sets and their "
     "decision problems",
     "https://doi.org/10.2307/1990888",
     "Trans. Amer. Math. Soc. 74, 358–366")
_ref("edmonds_year", 1965,
     "Edmonds, J. (1965)：Paths, trees, and flowers（多项式时间可解性的早期表述）",
     "https://doi.org/10.4153/CJM-1965-045-4",
     "Canad. J. Math. 17, 449–467")
_ref("rado_year", 1962,
     "Radó, T. (1962)：On non-computable functions（忙碌海狸的提出）",
     "https://doi.org/10.1147/rd.52.0077",
     "IBM Journal of Research and Development 6, 497–500")
_ref("bb5_year", 2024,
     "BB(5) = 47,176,870 的严格证明（2024 年，协作项目 Coq-BB5）",
     "https://bbchallenge.org/",
     "bbchallenge 项目 2024 年宣布 BB(5) 的机器验证证明")
_ref("matiyasevich_year", 1970,
     "Matiyasevich, Yu. V. (1970)：Enumerable sets are diophantine"
     "（希尔伯特第十问题的否定解决）",
     "https://doi.org/10.1016/0049-237X(70)90060-9",
     "Dokl. Akad. Nauk SSSR 191, 279–282")
_ref("khwarizmi_year", 820,
     "花拉子米（al-Khwārizmī）《代数学》成书的通行纪年（约 820 年）",
     "https://www.britannica.com/biography/al-Khwarizmi",
     "Britannica：al-Khwarizmi 的算术著作约成于 9 世纪前期，「算法」一词源于其名")
_ref("cook_year", 1971,
     "Cook, S. A. (1971)：The complexity of theorem-proving procedures",
     "https://doi.org/10.1145/800157.805047",
     "STOC 1971, 151–158（NP-完全性的提出）")
_ref("karp_year", 1972,
     "Karp, R. M. (1972)：Reducibility among combinatorial problems",
     "https://doi.org/10.1007/978-1-4684-2001-2_9",
     "收于 Complexity of Computer Computations, 85–103（21 个问题）")
_ref("clay_year", 2000,
     "克莱数学研究所千禧年大奖难题（2000 年公布）",
     "https://www.claymath.org/millennium-problems/",
     "七个问题，含 P vs NP")