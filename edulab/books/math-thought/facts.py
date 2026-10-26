# -*- coding: utf-8 -*-
"""《数学思想：从计数到无穷》的事实登记表。

**按章接入**：目前只接入第 10 章（混沌）。其余九章是 2026 年之前写的，
正文里的年份与常数从未登记 —— 它们是对外的欠账，不是「已经核查过」。

接入方式：`REGISTRY.enroll("ch10", "ch09", "ch08", "ch07", "ch06", "ch05")`。未接入的章节不会静默跳过 ——
`check_facts.py` 会点名列出，账一直摆在那里。
"""
import math
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]          # edulab/
sys.path.insert(0, str(_REPO / "shared"))
from factreg import Registry, claim                  # noqa: E402

REGISTRY = Registry("数学思想（第 10 章）")
REGISTRY.enroll("ch10", "ch09", "ch08", "ch07", "ch06", "ch05")

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

# ---- 第 7 章（结构）----------------
_ref("cardano_year", 1545,
     "Cardano, G. (1545)：Ars Magna（三次与四次方程解法公开发表）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Cardan/",
     "《大术》1545 年出版；三次方程的解法源自塔尔塔利亚")
_ref("lagrange_year", 1770,
     "Lagrange, J.-L. (1770)：Réflexions sur la résolution algébrique des équations",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Lagrange/",
     "该文已含「置换」的思想，但尚未把它变成一个对象")
_ref("ruffini_year", 1799,
     "Ruffini, P. (1799)：Teoria generale delle equazioni（五次方程不可解的早期论证）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Ruffini/",
     "论证有缺口，未被当时接受")
_ref("abel_year", 1824,
     "Abel, N. H. (1824)：Mémoire sur les équations algébriques"
     "（五次方程无根式解的第一个完整证明自费印行）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Abel/",
     "仅印 6 页，为节省印刷费把论证压得极短")
_ref("galois_year", 1832,
     "Galois, É. (1832)：决斗前夕写下的手稿（群论与方程可解性）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Galois/",
     "1832 年 5 月 31 日去世，年仅 20 岁；手稿 1846 年由刘维尔整理发表")
_ref("liouville_year", 1846,
     "Liouville, J. (1846)：在《纯数学与应用数学杂志》上整理发表伽罗瓦手稿",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Galois/",
     "伽罗瓦去世十四年后，其工作才被公开")
_ref("cayley_year", 1854,
     "Cayley, A. (1854)：On the theory of groups, as depending on the symbolic "
     "equation θⁿ = 1",
     "https://doi.org/10.1080/14786445408647421",
     "Phil. Mag. 7, 40–47（抽象群的早期表述）")
_ref("bourbaki_year", 1930,
     "布尔巴基学派（1930 年代起）：以结构（群、环、域）重写数学的纲领",
     "https://www.britannica.com/topic/Bourbaki-Nicolas",
     "1934 年起草，1939 年起出版《数学原理》")


# ---- 第 5 章（随机）----------------
_ref("pascal_fermat_year", 1654,
     "帕斯卡与费马的通信（1654 年，公认的概率论起点）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Pascal/",
     "围绕「点数问题」（problem of points）的往来书信")
_ref("huygens_year", 1657,
     "Huygens, C. (1657)：De ratiociniis in ludo aleae（第一部概率论小册子）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Huygens/",
     "1657 年出版，长期作为标准教材")
_ref("jacob_bernoulli_year", 1713,
     "Bernoulli, J. (1713)：Ars Conjectandi（大数定律首次发表，遗著）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Bernoulli_Jacob/",
     "1713 年出版，作者已于 1705 年去世")
_ref("laplace_year", 1812,
     "Laplace, P.-S. (1812)：Théorie analytique des probabilités",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Laplace/",
     "1812 年出版，概率的古典定义由此定型")
_ref("bertrand_year", 1889,
     "Bertrand, J. (1889)：Calcul des probabilités（伯特兰悖论的出处）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Bertrand/",
     "书中提出「随机取一条弦」的三种答案")
_ref("kolmogorov_year", 1933,
     "Kolmogorov, A. N. (1933)：Grundbegriffe der Wahrscheinlichkeitsrechnung"
     "（概率的公理化）",
     "https://doi.org/10.1007/978-3-642-49594-4",
     "以测度论给出概率的公理体系")

# ---- 第 6 章（空间）----------------
REGISTRY.add(claim(
    "euclid_year_bce", 300, "公元前年", grade="文献",
    note="《几何原本》成书年代取通行的「约公元前 300 年」",
    source="Euclid, Elements（成书年代通行估计）",
    url="https://mathshistory.st-andrews.ac.uk/Biographies/Euclid/",
    locator="约公元前 300 年（托勒密一世时期）",
))
_ref("saccheri_year", 1733,
     "Saccheri, G. (1733)：Euclides ab omni naevo vindicatus"
     "（试图用反证法证明第五公设，结果逼近非欧几何）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Saccheri/",
     "1733 年出版，长期被忽视")
_ref("playfair_year", 1795,
     "Playfair, J. (1795)：Elements of Geometry（第五公设的等价表述流行开来）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Playfair/",
     "「过直线外一点只有一条平行线」的表述")
_ref("gauss_private_year", 1824,
     "高斯关于非欧几何的私人信件（未公开发表）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Gauss/",
     "1824 年致陶里努斯信中提到他对新几何的把握")
_ref("gauss_curvature_year", 1827,
     "Gauss, C. F. (1827)：Disquisitiones generales circa superficies curvas"
     "（内蕴曲率）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Gauss/",
     "1827 年，曲面内蕴几何的奠基之作")
_ref("lobachevsky_year", 1829,
     "Lobachevsky, N. I. (1829)：On the foundations of geometry"
     "（第一个公开发表的非欧几何）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Lobachevsky/",
     "喀山通讯 1829 年发表")
_ref("bolyai_year", 1832,
     "Bolyai, J. (1832)：Appendix scientiam spatii absolute veram exhibens"
     "（作为其父著作的附录发表）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Bolyai/",
     "1832 年，与罗巴切夫斯基独立地得到双曲几何")
_ref("riemann_year", 1854,
     "Riemann, B. (1854)：Über die Hypothesen, welche der Geometrie zu Grunde "
     "liegen（就职演说，黎曼几何）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Riemann/",
     "1854 年演讲，1868 年出版")
_ref("poincare_year", 1882,
     "Poincaré, H. (1882)：双曲几何的圆盘模型（庞加莱圆盘）",
     "https://mathshistory.st-andrews.ac.uk/Biographies/Poincare/",
     "1882 年前后给出双曲平面的欧氏嵌入模型")
_ref("einstein_gr_year", 1915,
     "Einstein, A. (1915)：广义相对论场方程（引力即时空曲率）",
     "https://doi.org/10.1002/andp.19163540702",
     "1915 年 11 月向普鲁士科学院提交")
