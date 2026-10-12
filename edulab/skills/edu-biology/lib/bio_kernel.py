# -*- coding: utf-8 -*-
"""
bio_kernel.py — 生物学科的精确计算内核（sympy 精确运算，单一数据源）。

把"看起来像算术"的生物量全部交给 sympy：
  · 遗传：配子、杂交组合、基因型/表现型比例、棋盘格、测交、伴性遗传、系谱推断
  · 代谢：光合作用与呼吸作用的物质守恒（原子/质量配平）
  · 生态：能量沿营养级传递（10%~20% 递减）、种群增长（J 型 / S 型 logistic）
讲解文字里的每个数字都由本模块算出，绝无心算误差；画板与读数同源。

依赖: sympy。自检：python bio_kernel.py
"""

from collections import Counter, OrderedDict
from itertools import product

import sympy as sp


# ==================== 通用工具 ====================
def tex(x):
    return sp.latex(sp.nsimplify(x, rational=True) if isinstance(x, sp.Basic) else sp.sympify(x))


def fl(x):
    return float(sp.N(x))


def frac_str(r):
    """分数显示：3/4 → '3/4'，整数 → '3'。"""
    r = sp.nsimplify(r, rational=True)
    if r.q == 1:
        return str(r.p)
    return f"{r.p}/{r.q}"


# ==================== 1) 遗传：基因型解析 ====================
def parse_genotype(gt):
    """把基因型字符串切成「基因」列表，每个基因是一对等位基因。

    约定：同一个字母（不分大小写）属于同一个基因，大写为显性。
    'AaBb'   → [('A','a'), ('B','b')]
    'AABb'   → [('A','A'), ('B','b')]
    'Aa'     → [('A','a')]
    """
    gt = gt.replace(" ", "")
    assert len(gt) % 2 == 0, f"基因型长度须为偶数（二倍体每基因两个等位基因）：{gt}"
    groups = OrderedDict()
    for ch in gt:
        groups.setdefault(ch.upper(), []).append(ch)
    genes = []
    for letter, alleles in groups.items():
        assert len(alleles) == 2, f"基因 {letter} 的等位基因数须为 2，实际 {len(alleles)}：{gt}"
        genes.append(tuple(alleles))
    return genes


def gametes(gt):
    """所有配子及其概率（每个基因取一个等位基因，各 1/2）。返回 {配子串: Rational}。"""
    genes = parse_genotype(gt)
    n = len(genes)
    out = Counter()
    for pick in product(*genes):
        out["".join(sorted(pick, key=lambda c: (c.upper(), c.islower())))] += 1
    total = 2 ** n
    return OrderedDict((g, sp.Rational(c, total)) for g, c in sorted(out.items()))


def _norm_pair(x, y):
    """一对等位基因规范化显示：显性在前（Aa 而非 aA）。"""
    if x.islower() and y.isupper():
        x, y = y, x
    return x + y


def _combine(ga, gb):
    """两个配子逐基因组合成子代基因型（'AB'+'ab' → 'AaBb'）。"""
    assert len(ga) == len(gb), "两个配子的基因数须一致"
    return "".join(_norm_pair(ga[i], gb[i]) for i in range(len(ga)))


def cross(gt1, gt2):
    """两亲本杂交 → 子代基因型分布。返回 {基因型: (概率, 份数)}，份数按 4^n 归一。"""
    g1, g2 = gametes(gt1), gametes(gt2)
    n_genes = len(parse_genotype(gt1))
    total_slots = 4 ** n_genes                      # 棋盘格总格数
    counts = Counter()
    for a, pa in g1.items():
        for b, pb in g2.items():
            counts[_combine(a, b)] += pa * pb
    # 用整数份数表示（乘回总格数），保证 3:1、9:3:3:1 这类比例精确可读
    out = OrderedDict()
    for gt, p in sorted(counts.items()):
        out[gt] = (p, sp.nsimplify(p * total_slots))
    assert sum(c for _, c in out.values()) == total_slots, "棋盘格份数必须回满"
    return out


def phenotype_of(gt):
    """表现型（每基因 2 字符）：显性存在记 'A_'，否则记 'aa'。

    'AaBb' → 'A_B_'；'Aabb' → 'A_bb'；'aaBb' → 'aaB_'；'aabb' → 'aabb'。
    """
    parts = []
    for g in parse_genotype(gt):
        dom = g[0].upper()
        parts.append(dom + "_" if dom in "".join(g) else dom.lower() * 2)
    return "".join(parts)


def phenotype_ratio(cross_result):
    """把基因型分布归并成表现型分布，返回 [(表现型, 份数, 概率)]（按表现型字符串排序，与棋盘格顺序一致）。"""
    agg = Counter()
    for gt, (_, c) in cross_result.items():
        agg[phenotype_of(gt)] += c
    total = sum(agg.values())
    items = sorted(agg.items(), key=lambda kv: kv[0])
    return [(ph, sp.Integer(c), sp.Rational(c, total)) for ph, c in items]


def genotype_ratio(cross_result):
    """基因型分布（按基因型字符串排序：AA < Aa < aa，即棋盘格顺序）。"""
    total = sum(c for _, c in cross_result.values())
    items = sorted(cross_result.items(), key=lambda kv: kv[0])
    return [(gt, sp.Integer(c), sp.Rational(c, total)) for gt, (_, c) in items]


def ratio_str(items):
    """把 [(x, 份数, 概率)] 压成最简整数比，如 '9 : 3 : 3 : 1'、'1 : 1'。"""
    counts = [int(c) for _, c, _ in items]
    g = 0
    for c in counts:
        g = sp.gcd(g, c)
    g = int(g) or 1
    return " : ".join(str(c // g) for c in counts)


def punnett_square(gt1, gt2):
    """棋盘格：返回可绘制的二维网格。

    {row_gametes, col_gametes, cells:[[基因型,...],...], count: {基因型: 份数}}
    """
    g1 = list(gametes(gt1).keys())
    g2 = list(gametes(gt2).keys())
    cells = [[_combine(a, b) for b in g2] for a in g1]   # 行配子来自 gt1，列配子来自 gt2
    cnt = Counter()
    for row in cells:
        for c in row:
            cnt[c] += 1
    return {"row_gametes": g1, "col_gametes": g2, "cells": cells,
            "count": OrderedDict(sorted(cnt.items()))}


def cross_summary(gt1, gt2, labels=None):
    """一次杂交的完整摘要（供生成器直接用）：基因型/表现型比例 + 棋盘格 + 验证。"""
    cr = cross(gt1, gt2)
    gr = genotype_ratio(cr)
    pr = phenotype_ratio(cr)
    n_genes = len(parse_genotype(gt1))
    total = 4 ** n_genes
    assert sum(c for _, c, _ in gr) == total
    assert sum(c for _, c, _ in pr) == total
    return {
        "parents": (gt1, gt2), "n_genes": n_genes, "total": total,
        "genotypes": gr, "phenotypes": pr,
        "genotype_ratio": ratio_str(gr), "phenotype_ratio": ratio_str(pr),
        "punnett": punnett_square(gt1, gt2),
        "labels": labels or {},
    }


def test_cross(gt):
    """测交：与隐性纯合相交，用于推断基因型。"""
    genes = parse_genotype(gt)
    recessive = "".join(g[0].lower() * 2 for g in genes)
    return cross_summary(gt, recessive)


def progeny_prob(cross_result, selector, by="phenotype"):
    """在子代里挑出满足条件的比例（selector 为表现型或基因型字符串，支持 'A_bb' 通配）。"""
    def match(gt):
        ph = phenotype_of(gt)
        target = selector
        if by == "genotype":
            if "_" not in target:
                return gt == target
            return all((t == "_") or (t == g) for t, g in zip(target, gt))
        # phenotype：'_' 表示该位任意（即"含隐性"等情形由调用方写清）
        return all((t == "_") or (t == p) for t, p in zip(target, ph))
    total = sum(c for _, c in cross_result.values())
    hit = sum(c for gt, (_, c) in cross_result.items() if match(gt))
    return sp.Rational(hit, total)


# ---- 伴性遗传（X 染色体连锁） ----
def sex_linked_cross(mother, father):
    """伴性遗传：母亲 'XAXa'，父亲 'XAY'（用大写 A 表示显性等位基因）。

    返回 {女儿, 儿子} 两个分布（基因型 + 表现型），以及合计患病/正常比例。
    """
    def xgam(genotype, sex):
        if sex == "female":
            assert len(genotype) == 4 and genotype[0] == "X", f"母亲基因型须形如 XAXa：{genotype}"
            return [genotype[1], genotype[3]]
        assert len(genotype) == 3 and genotype[0] == "X" and genotype[2] == "Y", \
            f"父亲基因型须形如 XAY：{genotype}"
        return [genotype[1], "Y"]                   # X 上的等位基因 + Y

    mg = xgam(mother, "female")
    fg = xgam(father, "male")
    daughters, sons = Counter(), Counter()
    for m in mg:
        for f in fg:
            if f == "Y":
                sons[("X" + m, "Y")] += 1           # 儿子得 X 来自母亲
            else:
                daughters[tuple(sorted(("X" + m, "X" + f)))] += 1
    def norm(d):
        total = sum(d.values())
        return [("".join(k), sp.Rational(v, total)) for k, v in sorted(d.items())]
    return {"mother": mother, "father": father,
            "daughters": norm(daughters), "sons": norm(sons)}


def x_linked_affected(genotype):
    """伴性遗传表现型：X 上显性等位基因存在即正常（此处以 A=正常、a=致病为例）。"""
    gt = genotype.replace("Y", "")
    return "A" not in gt


# ==================== 2) 代谢：光合与呼吸的物质守恒 ====================
# 6CO2 + 6H2O --光/叶绿体--> C6H12O6 + 6O2
PS_REACTANTS = {"CO2": 6, "H2O": 6}
PS_PRODUCTS = {"C6H12O6": 1, "O2": 6}
MOLAR_MASS = {                     # g/mol（教学用整数原子量：C12 H1 O16）
    "CO2": sp.Integer(44), "H2O": sp.Integer(18),
    "O2": sp.Integer(32), "C6H12O6": sp.Integer(180),
}
# 每分子所含 C/H/O 原子数（用于守恒校验）
ATOMS_PER = {
    "CO2": (1, 0, 2), "H2O": (0, 2, 1), "C6H12O6": (6, 12, 6), "O2": (0, 0, 2),
}


def photosynthesis_balance(co2_mass=None, o2_mass=None, glucose_mass=None, water_mass=None):
    """光合作用/呼吸作用的定量换算：给定任一物质的量，算出其余全部。

    6CO2 + 6H2O → C6H12O6 + 6O2，按物质的量之比 6:6:1:6 精确配平。
    返回各物质的物质的量(mol)与质量(g)，并校验碳/氢/氧原子守恒。
    """
    given = [(k, v) for k, v in
             [("CO2", co2_mass), ("O2", o2_mass), ("C6H12O6", glucose_mass), ("H2O", water_mass)]
             if v is not None]
    assert len(given) == 1, "请且仅请给出一种物质的质量"
    species, mass = given[0]
    mass = sp.Rational(str(mass))
    mol = sp.nsimplify(mass / MOLAR_MASS[species], rational=True)
    # 以葡萄糖为 1 单位基准换算
    per_glucose = {"CO2": 6, "H2O": 6, "C6H12O6": 1, "O2": 6}
    glucose_mol = mol / per_glucose[species]
    amounts = {k: sp.simplify(glucose_mol * v) for k, v in per_glucose.items()}
    masses = {k: sp.simplify(amounts[k] * MOLAR_MASS[k]) for k in amounts}
    # 原子守恒校验：反应物侧 (CO2, H2O) 与产物侧 (C6H12O6, O2) 逐元素相等
    # 注意：amounts 里已含化学计量数，这里只按「每分子原子数」累加，不能再乘系数
    def side(names):
        C = H = O = sp.Integer(0)
        for name in names:
            a = amounts[name]
            c, h, o = ATOMS_PER[name]
            C += a * c
            H += a * h
            O += a * o
        return sp.simplify(C), sp.simplify(H), sp.simplify(O)
    left, right = side(PS_REACTANTS), side(PS_PRODUCTS)
    assert left == right, f"原子不守恒：反应物 {left} vs 产物 {right}"
    assert left[0] > 0, "至少要有碳原子"
    return {"given": species, "given_mass": mass, "mol": amounts, "mass": masses,
            "molar_mass": MOLAR_MASS, "equation": "6CO2 + 6H2O → C6H12O6 + 6O2"}


def net_gas_exchange(photosynthesis_rate, respiration_rate):
    """净气体交换：光合产 O2、呼吸耗 O2；净吸收 CO2 = 光合 − 呼吸（可为负）。"""
    ps, rs = sp.Rational(str(photosynthesis_rate)), sp.Rational(str(respiration_rate))
    return {"o2_net": sp.simplify(ps - rs), "co2_net": sp.simplify(rs - ps),
            "photosynthesis": ps, "respiration": rs,
            "releases_o2": bool(ps > rs), "compensation": bool(ps == rs)}


# ==================== 3) 生态：能量传递 ====================
def energy_pyramid(base_energy, levels=4, efficiency=sp.Rational(1, 10)):
    """能量沿营养级逐级递减（相邻两营养级传递效率通常 10%~20%）。

    返回每级能量 + 逐级传递率 + 相对第一级的占比。
    """
    base = sp.Rational(str(base_energy))
    eff = sp.Rational(str(efficiency))
    assert 0 < eff < 1, "传递效率须在 (0,1)"
    energies = [sp.simplify(base * eff ** i) for i in range(levels)]
    return {
        "base": base, "levels": levels, "efficiency": eff,
        "energies": energies,
        "ratios": [sp.simplify(e / base) for e in energies],
        "top_share": sp.simplify(energies[-1] / base),
        "loss_total": sp.simplify(base - energies[-1]),
    }


def energy_needed(consumer_energy, efficiency=sp.Rational(1, 10), steps=1):
    """要养活最高级消费者，需要多少生产者能量（逆推）。"""
    c = sp.Rational(str(consumer_energy))
    eff = sp.Rational(str(efficiency))
    need = c / eff ** steps
    return {"consumer": c, "producer_needed": sp.simplify(need),
            "factor": sp.simplify(need / c), "steps": steps, "efficiency": eff}


def biomass_supported(producer_energy, per_capita, efficiency=sp.Rational(1, 10), steps=1):
    """一定能量能支撑的最高级消费者数量（人口/个体数）。"""
    avail = sp.Rational(str(producer_energy)) * sp.Rational(str(efficiency)) ** steps
    n = sp.simplify(avail / sp.Rational(str(per_capita)))
    return {"available": sp.simplify(avail), "per_capita": sp.Rational(str(per_capita)),
            "count": n, "efficiency": sp.Rational(str(efficiency)), "steps": steps}


# ==================== 4) 生态：种群增长 ====================
def exponential_growth(n0, rate, t):
    """J 型增长：N = N0·λ^t（rate 为每代增长倍数 λ，t 为代数）。"""
    N0, lam, t = sp.Rational(str(n0)), sp.Rational(str(rate)), sp.Integer(int(t))
    N = sp.simplify(N0 * lam ** t)
    return {"n0": N0, "lambda": lam, "t": t, "n": N, "multiple": sp.simplify(lam ** t),
            "growth": sp.simplify(N - N0)}


def logistic_growth(n0, k, r, t):
    """S 型（logistic）增长：N = K / (1 + (K/N0 − 1)·e^(−rt))。

    返回 t 时刻数量、环境容纳量 K、以及「增长速率最大」的拐点 N=K/2。
    """
    N0, K, r, t = (sp.Rational(str(n0)), sp.Rational(str(k)),
                   sp.Rational(str(r)), sp.Rational(str(t)))
    assert N0 < K, "初始数量须小于环境容纳量"
    N = sp.simplify(K / (1 + (K / N0 - 1) * sp.exp(-r * t)))
    return {"n0": N0, "k": K, "r": r, "t": t, "n": N,
            "half_k": sp.simplify(K / 2),          # 增长最快的种群密度
            "remaining_capacity": sp.simplify(K - N)}


def doubling_time(rate):
    """J 型增长翻倍所需代数：t = ln2 / lnλ。"""
    lam = sp.Rational(str(rate))
    assert lam > 1, "增长倍数须大于 1"
    return sp.simplify(sp.log(2) / sp.log(lam))


def logistic_max_rate(k, r):
    """S 型增长的最大增长速率（在 N=K/2 处）为 rK/4。"""
    return sp.simplify(sp.Rational(str(r)) * sp.Rational(str(k)) / 4)


# ==================== 自检 ====================
if __name__ == "__main__":
    # ---- 遗传 ----
    assert gametes("Aa") == OrderedDict([("A", sp.Rational(1, 2)), ("a", sp.Rational(1, 2))])
    assert len(gametes("AaBb")) == 4
    assert sum(gametes("AaBb").values()) == 1

    mono = cross_summary("Aa", "Aa")
    assert mono["genotype_ratio"] == "1 : 2 : 1", mono["genotype_ratio"]
    assert mono["phenotype_ratio"] == "3 : 1", mono["phenotype_ratio"]
    assert sum(c for _, c, _ in mono["genotypes"]) == 4

    di = cross_summary("AaBb", "AaBb")
    assert di["genotype_ratio"] == "1 : 2 : 1 : 2 : 4 : 2 : 1 : 2 : 1", di["genotype_ratio"]
    assert di["phenotype_ratio"] == "9 : 3 : 3 : 1", di["phenotype_ratio"]
    assert sum(c for _, c, _ in di["genotypes"]) == 16

    tc = cross_summary("Aa", "aa")
    assert tc["phenotype_ratio"] == "1 : 1", tc["phenotype_ratio"]

    # 测交
    t2 = test_cross("AaBb")
    assert t2["parents"] == ("AaBb", "aabb")
    assert sorted(int(x) for x in t2["phenotype_ratio"].split(" : ")) == [1, 1, 1, 1]

    # 概率查询：Aa×Aa 中 AA 的概率
    assert progeny_prob(cross("Aa", "Aa"), "AA", by="genotype") == sp.Rational(1, 4)
    # AaBb×AaBb 中 AABB 的概率
    assert progeny_prob(cross("AaBb", "AaBb"), "AABB", by="genotype") == sp.Rational(1, 16)
    # 显性表现型（A_）概率
    assert progeny_prob(cross("Aa", "Aa"), "A_", by="phenotype") == sp.Rational(3, 4)

    # 棋盘格
    ps = punnett_square("Aa", "Aa")
    assert ps["row_gametes"] == ["A", "a"] and ps["count"]["Aa"] == 2

    # 伴性遗传：XAXa × XAY
    sl = sex_linked_cross("XAXa", "XAY")
    assert len(sl["sons"]) == 2                  # XAY / XaY
    assert len(sl["daughters"]) >= 1
    son_map = dict(sl["sons"])
    assert son_map["XaY"] == sp.Rational(1, 2), son_map
    assert son_map["XAY"] == sp.Rational(1, 2)
    assert x_linked_affected("XaY") is True and x_linked_affected("XAY") is False

    # ---- 光合作用 ----
    psb = photosynthesis_balance(co2_mass=264)
    # 264 g CO2 = 6 mol → 葡萄糖 1 mol = 180 g，O2 6 mol = 192 g，耗水 6 mol = 108 g
    assert psb["mol"]["CO2"] == 6 and psb["mol"]["C6H12O6"] == 1 and psb["mol"]["O2"] == 6
    assert psb["mass"]["C6H12O6"] == 180
    assert psb["mass"]["O2"] == 192
    assert psb["mass"]["H2O"] == 108
    assert photosynthesis_balance(o2_mass=192)["mass"]["C6H12O6"] == 180

    ng = net_gas_exchange(10, 4)
    assert ng["o2_net"] == 6 and ng["releases_o2"] is True
    assert net_gas_exchange(5, 5)["compensation"] is True

    # ---- 能量传递 ----
    ep = energy_pyramid(10000, levels=4, efficiency=sp.Rational(1, 10))
    assert ep["energies"] == [10000, 1000, 100, 10]
    assert ep["top_share"] == sp.Rational(1, 1000)
    assert energy_needed(10, steps=3)["producer_needed"] == 10000
    assert biomass_supported(10000, 100, steps=2)["count"] == 1

    # ---- 种群增长 ----
    ex = exponential_growth(100, 2, 5)
    assert ex["n"] == 3200
    assert doubling_time(2) == 1
    lo = logistic_growth(10, 1000, sp.Rational(1, 2), 0)
    assert lo["n"] == 10 and lo["half_k"] == 500
    assert logistic_max_rate(1000, sp.Rational(1, 2)) == 125

    print("bio_kernel self-check OK ✓")
    print(f"  单杂交 Aa×Aa → 基因型 {mono['genotype_ratio']}，表现型 {mono['phenotype_ratio']}")
    print(f"  双杂交 AaBb×AaBb → 表现型 {di['phenotype_ratio']}")
    print(f"  测交 AaBb×aabb → 表现型 {t2['phenotype_ratio']}")
    print(f"  伴性 XAXa×XAY → 儿子患病 {son_map['XaY']}（{float(son_map['XaY'])*100:.0f}%）")
    print(f"  光合 264 g CO2 → 葡萄糖 {float(psb['mass']['C6H12O6']):.2f} g + O2 {float(psb['mass']['O2']):.0f} g")
    print(f"  能量金字塔 10000 → {ep['energies']}")
    print(f"  J 型 100×2⁵ = {ex['n']}")
