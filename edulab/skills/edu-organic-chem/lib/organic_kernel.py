#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
organic_kernel.py —— 高中「有机化学基础」内核（选择性必修三）

覆盖：
  · 分子式与相对分子质量
  · 不饱和度 Ω = (2C + 2 + N − H − X)/2 及其结构含义
  · 燃烧耗氧量 CₓHᵧO_z + (x + y/4 − z/2) O₂ → x CO₂ + (y/2) H₂O
  · 由燃烧产物（CO₂ 与 H₂O 的质量）反推实验式与分子式
  · **等效氢与一氯代物种数**：用碳骨架的**自同构群轨道**真算（不是查表）
  · 官能团定量反应（Na 出 H₂、NaOH 中和、银镜 Ag、Br₂ 加成、H₂ 加成）
  · 加聚 / 缩聚与聚合度
  · **烷烃的主链选择与编号**：枚举全部碳链路径，按「最长 → 取代基最多 → 位号最小」定主链

设计原则（与全项目一致）：
  · **不手写数据**：同分异构体数、等效氢数、主链与位号都由算法现算，不查表。
  · 有机物的「结构」用**碳骨架图**表示（邻接表），碳的化合价固定为 4，
    所以第 i 个碳上的氢数 = 4 − 它的成键数（仅适用于烷烃/环烷烃）。
  · 自检：python organic_kernel.py
"""

import itertools
import math

__all__ = [
    "f", "num_str", "frac_tex",
    "molar_mass", "unsaturation", "unsat_hint",
    "oxygen_demand", "combustion_products", "oxygen_mass",
    "empirical_from_masses", "formula_multiplier",
    "h_on_carbon", "automorphisms", "equivalent_hydrogens", "tree_layout",
    "h2_from_sodium", "naoh_consumed", "ag_from_aldehyde",
    "br2_addition", "h2_addition",
    "addition_degree", "condensation_degree",
    "all_paths", "main_chain",
]


# ---------------------------------------------------------------- 排版助手
def f(x, digits=4):
    if x is None:
        return "—"
    s = f"{float(x):.{digits}f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-") else "0"


def num_str(x, digits=4):
    v = float(x)
    if v == 0:
        return "0"
    if abs(v) >= 1e5 or abs(v) < 1e-4:
        return f"{v:.3e}".replace("e-0", "e-").replace("e+0", "e")
    return f(v, digits)


def frac_tex(num, den):
    """约分后的分数字符串；整数则直接给整数。"""
    from math import gcd
    if den == 0:
        return "—"
    g = gcd(int(round(abs(num))), int(round(abs(den))))
    if g == 0:
        return "0"
    a, b = int(round(num)) // g, int(round(den)) // g
    if b == 1:
        return str(a)
    return f"\\dfrac{{{a}}}{{{b}}}"


# ---------------------------------------------------------------- 分子式与相对分子质量
# 相对原子质量（教材常用值）
AR = {"C": 12.0, "H": 1.0, "O": 16.0, "N": 14.0, "Cl": 35.5, "Br": 80.0}


def molar_mass(C=0, H=0, O=0, N=0, X=0, x_mass=35.5):
    """相对分子质量（X 为卤素，默认按 Cl 计）。"""
    return AR["C"] * C + AR["H"] * H + AR["O"] * O + AR["N"] * N + x_mass * X


def unsaturation(C, H=0, N=0, X=0):
    """不饱和度 Ω = (2C + 2 + N − H − X)/2。

    每多一个双键或一个环，Ω 就加 1；三键算 2。
    苯环（C₆H₆ 型）Ω = 4（3 个双键 + 1 个环）。
    """
    return (2.0 * C + 2.0 + N - H - X) / 2.0


def unsat_hint(omega):
    """把不饱和度翻译成可能的结构特征（定性，不唯一）。"""
    o = float(omega)
    if abs(o - round(o)) > 1e-9:
        return "不是整数或半整数 —— 检查分子式（可能含 N 或卤素）"
    k = int(round(o))
    if k < 0:
        return "Ω 为负 —— 分子式不合法"
    if k == 0:
        return "饱和：只可能是链状烷烃（或饱和烃基）"
    if k == 1:
        return "1 个双键 或 1 个环"
    if k == 2:
        return "2 个双键 / 1 个三键 / 1 双键 + 1 环 / 2 个环"
    if k == 4:
        return "常见于苯环（3 双键 + 1 环），也可能其他组合"
    return f"{k} 个「双键或环」当量"


# ---------------------------------------------------------------- 燃烧
def oxygen_demand(C, H=0, O=0):
    """燃烧 1 mol 有机物所需 O₂ 的物质的量：x + y/4 − z/2。"""
    return C + H / 4.0 - O / 2.0


def combustion_products(C, H=0, O=0, n=1.0):
    """返回 (n_CO₂, n_H₂O, n_O₂)（单位 mol）。"""
    return n * C, n * H / 2.0, n * oxygen_demand(C, H, O)


def oxygen_mass(C, H=0, O=0, n=1.0):
    """所需 O₂ 的质量（g）。"""
    return combustion_products(C, H, O, n)[2] * 32.0


# ---------------------------------------------------------------- 由燃烧产物确定分子式
def empirical_from_masses(m_co2, m_h2o, m_sample):
    """由 CO₂、H₂O 的质量与样品质量，求实验式（最简整数比 C:H:O）。

    返回 (C, H, O, m_C, m_H, m_O)；若氧的质量为负说明数据不自洽。
    """
    n_c = m_co2 / 44.0
    n_h = 2.0 * m_h2o / 18.0
    m_c = 12.0 * n_c
    m_h = 1.0 * n_h
    m_o = m_sample - m_c - m_h
    if m_o < -1e-6:
        raise ValueError("氧的质量为负：CO₂ 与 H₂O 的质量之和超过了样品质量，数据不自洽")
    n_o = max(0.0, m_o) / 16.0
    # 化为最简整数比：先除以**非零**最小值（不含氧的烃也要能约简），再放大到接近整数
    vals = [n_c, n_h, n_o]
    nz = [v for v in vals if v > 1e-12]
    if not nz:
        return vals, m_c, m_h, m_o
    mn = min(nz)
    scaled = [v / mn for v in vals]
    for k in range(1, 21):
        if all(abs(s * k - round(s * k)) < 0.02 for s in scaled):
            return [int(round(s * k)) for s in scaled], m_c, m_h, m_o
    return scaled, m_c, m_h, m_o


def formula_multiplier(empirical, Mr):
    """由实验式与相对分子质量求倍数 k（分子式 = 实验式 × k）。"""
    C, H, O = (list(empirical) + [0, 0, 0])[:3]
    m = molar_mass(C, H, O)
    if m <= 0:
        raise ValueError("实验式不合法")
    return Mr / m


# ---------------------------------------------------------------- 碳骨架：氢、自同构、等效氢
def h_on_carbon(adj, i):
    """烷烃中第 i 个碳上的氢数 = 4 − 成键数。"""
    return 4 - len(adj[i])


def _degree_classes(adj):
    g = {}
    for i in range(len(adj)):
        g.setdefault(h_on_carbon(adj, i), []).append(i)
    return list(g.values())


def automorphisms(adj):
    """碳骨架的**自同构群**：保持邻接关系不变的全部顶点置换。

    只在「氢数相同」的碳之间置换（大幅剪枝），再逐个验证邻接关系。
    烷烃碳数 ≤ 8 时组内置换的乘积很小，可以穷举。
    """
    n = len(adj)
    adjset = [set(x) for x in adj]
    classes = _degree_classes(adj)
    results = []
    # 在每个等价类内部做全排列，笛卡尔积就是全部候选置换
    for combo in itertools.product(*[list(itertools.permutations(c)) for c in classes]):
        p = [0] * n
        for c, perm in zip(classes, combo):
            for old, new in zip(c, perm):
                p[old] = new
        ok = True
        for i in range(n):
            if len(adj[i]) != len(adj[p[i]]):
                ok = False
                break
            for w in adj[i]:
                if p[w] not in adjset[p[i]]:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            results.append(tuple(p))
    return sorted(set(results))


def equivalent_hydrogens(adj):
    """等效氢分组。

    返回 (orbits, group_id, h_counts)：
      orbits   —— 等效氢的**种数**（= 一氯代物的种数）
      group_id —— 每个氢位置 (碳号, 该碳上的第几个氢) 所属的组号
      h_counts —— 每个碳上的氢数
    """
    n = len(adj)
    hc = [h_on_carbon(adj, i) for i in range(n)]
    positions = [(i, s) for i in range(n) for s in range(hc[i])]
    idx = {p: k for k, p in enumerate(positions)}
    # 并查集
    parent = list(range(len(positions)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for p in automorphisms(adj):
        for (i, s) in positions:
            union(idx[(i, s)], idx[(p[i], s)])
    # 关键一步：**同一个碳上的氢彼此也等价**（把碳上的氢互换也是整个分子的自同构）。
    # 漏掉这一步会把「一个甲基上的 3 个氢」算成 3 种，结论整体偏离。
    for i in range(n):
        for s in range(1, hc[i]):
            union(idx[(i, 0)], idx[(i, s)])
    gid = {}
    counter = 0
    for pos in positions:
        r = find(idx[pos])
        if r not in gid:
            gid[r] = counter
            counter += 1
    group_id = {pos: gid[find(idx[pos])] for pos in positions}
    return counter, group_id, hc


def tree_layout(adj):
    """把碳骨架铺成 2D 树形（根取树的中心），返回 {碳号: (x, y)}。

    y 向下为负（画板里再翻转）；x 按叶子顺序排开，父节点取子节点的中点。
    """
    n = len(adj)
    if n == 0:
        return {}
    # 找中心：反复剥掉叶子
    deg = [len(adj[i]) for i in range(n)]
    alive = set(range(n))
    while len(alive) > 2:
        leaves = [v for v in alive if sum(1 for w in adj[v] if w in alive) <= 1]
        for v in leaves:
            alive.discard(v)
    root = min(alive) if alive else 0
    # BFS 定向
    parent = {root: -1}
    order = [root]
    for v in order:
        for w in adj[v]:
            if w not in parent:
                parent[w] = v
                order.append(w)
    children = {v: [] for v in range(n)}
    for v in order:
        if parent[v] >= 0:
            children[parent[v]].append(v)
    x, depth = {}, {}

    def walk(v, d):
        depth[v] = d
        if not children[v]:
            x[v] = span[0]
            span[0] += 1.0
        else:
            for c in children[v]:
                walk(c, d + 1)
            x[v] = (x[children[v][0]] + x[children[v][-1]]) / 2.0

    span = [0.0]
    walk(root, 0)
    xs = list(x.values())
    cx = (min(xs) + max(xs)) / 2.0
    return {v: (x[v] - cx, -depth[v]) for v in range(n)}


# ---------------------------------------------------------------- 官能团定量反应
def h2_from_sodium(n_oh=0, n_cooh=0):
    """与足量 Na 反应放出 H₂ 的物质的量：2(−OH 或 −COOH) → 1 H₂。

    注意：只有**活泼氢**（羟基、羧基上的氢）才与 Na 反应，烃基上的氢不反应。
    """
    return (n_oh + n_cooh) / 2.0


def naoh_consumed(n_cooh=0, n_phenol=0, n_ester=0):
    """消耗 NaOH 的物质的量：羧基 1:1、酚羟基 1:1、酯基 1:1（水解）。"""
    return n_cooh + n_phenol + n_ester


def ag_from_aldehyde(n_cho):
    """银镜反应：1 mol 醛基 → 2 mol Ag。"""
    return 2.0 * n_cho


def br2_addition(n_double=0, n_triple=0):
    """与 Br₂ 加成：每个双键 1 mol，每个三键 2 mol。"""
    return n_double + 2.0 * n_triple


def h2_addition(n_double=0, n_triple=0, n_benzene=0):
    """与 H₂ 加成：双键 1、三键 2、苯环 3（每 mol）。"""
    return n_double + 2.0 * n_triple + 3.0 * n_benzene


# ---------------------------------------------------------------- 聚合
def addition_degree(Mr_polymer, Mr_monomer):
    """加聚：链节就是单体，聚合度 n = Mr(高分子)/Mr(单体)。"""
    if Mr_monomer <= 0:
        raise ValueError("单体相对分子质量必须为正")
    return Mr_polymer / Mr_monomer


def condensation_degree(Mr_polymer, Mr_monomer, loss=18.0):
    """缩聚：n 个单体脱去 (n−1) 个小分子（默认水，Mr = 18）。

    Mr(高分子) = n·Mr(单体) − (n−1)·Mr(小分子)
    ⇒ n = (Mr(高分子) − Mr(小分子)) / (Mr(单体) − Mr(小分子))
    """
    den = Mr_monomer - loss
    if den <= 0:
        raise ValueError("单体相对分子质量必须大于脱去的小分子")
    return (Mr_polymer - loss) / den


# ---------------------------------------------------------------- 主链选择与编号
def all_paths(adj):
    """枚举碳骨架中的全部简单路径（每条路径正反向各出现一次）。"""
    n = len(adj)
    out = []

    def dfs(path):
        out.append(tuple(path))
        for w in adj[path[-1]]:
            if w not in path:
                path.append(w)
                dfs(path)
                path.pop()

    for s in range(n):
        dfs([s])
    return out


def main_chain(adj):
    """按「最长 → 取代基最多 → 位号最小」确定主链。

    返回 (chain, locants, n_substituents)：
      chain  —— 主链上的碳号（从编号 1 开始的那个碳排在最前）
      locants—— 取代基所在的位号（升序）
      n_sub —— 取代基个数
    """
    n = len(adj)
    paths = all_paths(adj)
    best_len = max(len(p) for p in paths)
    cands = [p for p in paths if len(p) == best_len]
    # 反向视为同一条
    seen, uniq = set(), []
    for p in cands:
        key = min(p, p[::-1])
        if key not in seen:
            seen.add(key)
            uniq.append(p)

    def branches(p):
        s = set(p)
        return [w for i in p for w in adj[i] if w not in s]

    def locants_of(p):
        idx = {c: k + 1 for k, c in enumerate(p)}
        s = set(p)
        ls = []
        for i in p:
            for w in adj[i]:
                if w not in s:
                    ls.append(idx[i])
        return sorted(ls)

    max_sub = max(len(branches(p)) for p in uniq)
    uniq = [p for p in uniq if len(branches(p)) == max_sub]

    def oriented(p):
        a, b = locants_of(p), locants_of(p[::-1])
        return (a, list(p)) if a <= b else (b, list(p[::-1]))

    scored = sorted((oriented(p) for p in uniq), key=lambda x: x[0])
    ls, chain = scored[0]
    return chain, ls, max_sub


# ================================================================ 自检
def _selftest():
    bad = []

    def chk(name, got, want, tol=1e-9):
        if isinstance(got, (list, tuple)) or isinstance(want, (list, tuple)):
            ga, wa = list(got), list(want)
            ok = len(ga) == len(wa) and all(abs(float(x) - float(y)) <= 1e-9 for x, y in zip(ga, wa))
            g = ga
        else:
            ok = abs(float(got) - float(want)) <= tol
            g = f"{float(got):.6g}"
        print(f"  {'✓' if ok else '✗'} {name:46s} = {g}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    def chkb(name, got, want):
        ok = bool(got) == bool(want)
        print(f"  {'✓' if ok else '✗'} {name:46s} = {got}")
        if not ok:
            bad.append(name)

    def graph(n, edges):
        adj = [[] for _ in range(n)]
        for a, b in edges:
            adj[a].append(b)
            adj[b].append(a)
        return adj

    print("相对分子质量与不饱和度")
    chk("Mr(CH₄)", molar_mass(1, 4), 16.0, 1e-12)
    chk("Mr(C₂H₆O)", molar_mass(2, 6, 1), 46.0, 1e-12)
    chk("Mr(C₆H₆)", molar_mass(6, 6), 78.0, 1e-12)
    chk("Ω(烷烃 CₙH₂ₙ₊₂) = 0", unsaturation(5, 12), 0.0, 1e-12)
    chk("Ω(乙烯 C₂H₄) = 1", unsaturation(2, 4), 1.0, 1e-12)
    chk("Ω(乙炔 C₂H₂) = 2", unsaturation(2, 2), 2.0, 1e-12)
    chk("Ω(苯 C₆H₆) = 4", unsaturation(6, 6), 4.0, 1e-12)
    chk("Ω(乙酸 C₂H₄O₂) = 1", unsaturation(2, 4), 1.0, 1e-12)
    chk("Ω 含 N：(CH₃NH₂) CH₅N = 0", unsaturation(1, 5, 1), 0.0, 1e-12)
    chk("Ω 含卤素：CH₃Cl = 0", unsaturation(1, 3, 0, 1), 0.0, 1e-12)

    print("\n燃烧计算")
    chk("甲烷耗氧 x+y/4", oxygen_demand(1, 4), 2.0, 1e-12)
    chk("乙烷 C₂H₆ 耗氧", oxygen_demand(2, 6), 3.5, 1e-12)
    chk("乙醇 C₂H₆O 耗氧（z/2 抵扣）", oxygen_demand(2, 6, 1), 3.0, 1e-12)
    chk("苯 C₆H₆ 耗氧", oxygen_demand(6, 6), 7.5, 1e-12)
    chk("1 mol 甲烷生成 1 mol CO₂", combustion_products(1, 4)[0], 1.0, 1e-12)
    chk("1 mol 甲烷生成 2 mol H₂O", combustion_products(1, 4)[1], 2.0, 1e-12)
    chk("2 mol 乙烷耗氧 7 mol", combustion_products(2, 6, 0, 2.0)[2], 7.0, 1e-12)
    chk("甲烷耗氧质量 64 g/mol", oxygen_mass(1, 4), 64.0, 1e-12)
    # 含氧越多，耗氧越少
    chk("含氧越多耗氧越少", oxygen_demand(2, 6, 1) < oxygen_demand(2, 6, 0), True)

    print("\n由燃烧产物确定分子式")
    # 3.0 g 某有机物完全燃烧，生成 4.4 g CO₂ 与 1.8 g H₂O
    emp, mC, mH, mO = empirical_from_masses(4.4, 1.8, 3.0)
    chk("n(C)", 4.4 / 44.0, 0.1, 1e-9)
    chk("n(H)", 2 * 1.8 / 18.0, 0.2, 1e-9)
    chk("m(C) = 1.2 g", mC, 1.2, 1e-9)
    chk("m(H) = 0.2 g", mH, 0.2, 1e-9)
    chk("m(O) = 1.6 g", mO, 1.6, 1e-9)
    chk("实验式 C:H:O", emp, [1, 2, 1])
    chk("Mr = 60 时 k = 2", formula_multiplier([1, 2, 1], 60.0), 2.0, 1e-9)
    chk("  分子式 C₂H₄O₂（乙酸）", molar_mass(2, 4, 2), 60.0, 1e-12)
    # 只含碳氢的情形：8.8 g CO₂ ⇒ 0.2 mol C；3.6 g H₂O ⇒ 0.4 mol H ⇒ 实验式 CH₂
    emp2, *_ = empirical_from_masses(8.8, 3.6, 2.8)
    chk("2.8 g 烃 → C:H = 1:2", emp2, [1, 2, 0])
    try:
        empirical_from_masses(10.0, 5.0, 1.0)
        chkb("数据不自洽时应报错", False, True)
    except ValueError:
        chkb("数据不自洽时应报错", True, True)

    print("\n等效氢（图自同构轨道）")
    # 正戊烷 0-1-2-3-4：三种氢（两端、2/4 位、3 位）
    n5 = graph(5, [(0, 1), (1, 2), (2, 3), (3, 4)])
    chk("正戊烷的等效氢种数 = 3", equivalent_hydrogens(n5)[0], 3)
    # 2-甲基丁烷（异戊烷）：四种氢
    ip = graph(5, [(0, 1), (1, 2), (2, 3), (1, 4)])
    chk("2-甲基丁烷的等效氢种数 = 4", equivalent_hydrogens(ip)[0], 4)
    # 2,2-二甲基丙烷（新戊烷）：一种氢
    np5 = graph(5, [(0, 1), (0, 2), (0, 3), (0, 4)])
    chk("新戊烷的等效氢种数 = 1", equivalent_hydrogens(np5)[0], 1)
    # 正己烷：三种氢
    n6 = graph(6, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)])
    chk("正己烷的等效氢种数 = 3", equivalent_hydrogens(n6)[0], 3)
    # 2,3-二甲基丁烷：两种氢
    dmb = graph(6, [(0, 1), (1, 2), (2, 3), (1, 4), (2, 5)])
    chk("2,3-二甲基丁烷的等效氢种数 = 2", equivalent_hydrogens(dmb)[0], 2)
    # 自同构群的大小（新戊烷有 4! = 24 个）
    chk("新戊烷自同构群 |Aut| = 24", len(automorphisms(np5)), 24)
    chk("正戊烷自同构群 |Aut| = 2", len(automorphisms(n5)), 2)
    # 氢总数 = 2n+2
    for g, n in ((n5, 5), (ip, 5), (np5, 5), (n6, 6), (dmb, 6)):
        chk(f"氢总数 = 2×{n}+2", sum(h_on_carbon(g, i) for i in range(n)), 2 * n + 2)
    # 分组数与「按碳分组的细化」的关系：组数 ≤ 不同碳的氢数种类
    orbits, gid, hc = equivalent_hydrogens(ip)
    chk("每个碳上的氢数（异戊烷）", hc, [3, 1, 2, 3, 3])
    chk("C0 与 C4 等价（都接在同 C1 上）", gid[(0, 0)] == gid[(4, 0)], True)
    chk("C3 与 C0 不等价（接在 C2 上）", gid[(3, 0)] != gid[(0, 0)], True)
    chk("同碳上的氢同组", gid[(2, 0)] == gid[(2, 1)], True)
    chk("组号恰好有 orbits 个不同的值", len(set(gid.values())), orbits)
    # 新戊烷：四个甲基全等价
    _, gid2, _ = equivalent_hydrogens(np5)
    chk("新戊烷四个甲基同组",
        sorted({gid2[(i, 0)] for i in (1, 2, 3, 4)}), [gid2[(1, 0)]])

    print("\n官能团定量反应")
    chk("1 mol 乙醇与 Na 放 0.5 mol H₂", h2_from_sodium(1, 0), 0.5, 1e-12)
    chk("1 mol 乙二醇放 1 mol H₂", h2_from_sodium(2, 0), 1.0, 1e-12)
    chk("1 mol 乙酸放 0.5 mol H₂", h2_from_sodium(0, 1), 0.5, 1e-12)
    chk("2(−OH 或 −COOH) → 1 H₂", h2_from_sodium(1, 1), 1.0, 1e-12)
    chk("羧基消耗 NaOH 1:1", naoh_consumed(1, 0, 0), 1.0, 1e-12)
    chk("酚羟基也消耗 NaOH", naoh_consumed(0, 1, 0), 1.0, 1e-12)
    chk("酯基水解消耗 NaOH", naoh_consumed(0, 0, 1), 1.0, 1e-12)
    chk("苯酚 + 羧基 + 酯 共 3", naoh_consumed(1, 1, 1), 3.0, 1e-12)
    chk("1 mol 醛基 → 2 mol Ag", ag_from_aldehyde(1), 2.0, 1e-12)
    chk("1 mol 双键加 1 mol Br₂", br2_addition(1, 0), 1.0, 1e-12)
    chk("1 mol 三键加 2 mol Br₂", br2_addition(0, 1), 2.0, 1e-12)
    chk("1 mol 苯加 3 mol H₂", h2_addition(0, 0, 1), 3.0, 1e-12)
    chk("1 双键 + 1 苯环 加 4 mol H₂", h2_addition(1, 0, 1), 4.0, 1e-12)
    # 与 NaHCO₃ 只反应羧基：这里用 naoh_consumed 的羧基项核对
    chk("NaHCO₃ 只认羧基（概念核对）", naoh_consumed(1, 0, 0), 1.0, 1e-12)

    print("\n聚合")
    chk("聚乙烯 n = Mr/Mr(单体)", addition_degree(280000.0, 28.0), 10000.0, 1e-9)
    chk("聚氯乙烯链节 62.5", molar_mass(2, 3, 0, 0, 1), 62.5, 1e-12)
    chk("聚氯乙烯 n", addition_degree(62500.0, 62.5), 1000.0, 1e-9)
    # 缩聚：n 个单体脱去 n−1 个水
    n = condensation_degree(10000.0, 106.0, 18.0)
    chk("缩聚度反推", n, (10000.0 - 18.0) / (106.0 - 18.0), 1e-9)
    chk("  回代 Mr = n·106 − (n−1)·18", n * 106.0 - (n - 1) * 18.0, 10000.0, 1e-9)
    chk("加聚不脱小分子", addition_degree(10000.0, 100.0), 100.0, 1e-9)

    print("\n主链选择与编号")
    # 正戊烷：主链 5 个碳，无取代基
    ch, ls, ns = main_chain(n5)
    chk("正戊烷主链长度", len(ch), 5)
    chk("  无取代基", ns, 0)
    # 2-甲基丁烷：主链 4 个碳，一个甲基在 2 位
    ch, ls, ns = main_chain(ip)
    chk("异戊烷主链长度", len(ch), 4)
    chk("  取代基个数", ns, 1)
    chk("  取代基位号 = [2]", ls, [2])
    # 新戊烷：主链 3 个碳（中心 C 与两个甲基），两个取代基在 2 位
    ch, ls, ns = main_chain(np5)
    chk("新戊烷主链长度", len(ch), 3)
    chk("  取代基个数", ns, 2)
    chk("  取代基位号 = [2,2]", ls, [2, 2])
    # 2,3-二甲基丁烷：主链 4 个碳，两个甲基在 2、3 位
    ch, ls, ns = main_chain(dmb)
    chk("2,3-二甲基丁烷主链长度", len(ch), 4)
    chk("  取代基位号 = [2,3]", ls, [2, 3])
    # 3-甲基戊烷：主链 5 个碳，甲基在 3 位
    mp = graph(6, [(0, 1), (1, 2), (2, 3), (3, 4), (2, 5)])
    ch, ls, ns = main_chain(mp)
    chk("3-甲基戊烷主链长度", len(ch), 5)
    chk("  取代基位号 = [3]", ls, [3])
    # 正己烷
    ch, ls, ns = main_chain(n6)
    chk("正己烷主链长度", len(ch), 6)
    chk("  无取代基", ns, 0)
    # 主链一定是最长路径
    chk("主链长度 = 最长路径长度",
        len(main_chain(dmb)[0]), max(len(p) for p in all_paths(dmb)))

    print("\n碳骨架布局")
    lay = tree_layout(n5)
    chk("正戊烷布局：5 个碳都有坐标", len(lay), 5)
    chk("  中心碳的 x 居中", abs(sum(p[0] for p in lay.values()) / 5) < 1e-9, True)
    lay2 = tree_layout(np5)
    chk("新戊烷布局：4 个叶子在同一深度",
        len({round(lay2[i][1], 9) for i in (1, 2, 3, 4)}), 1)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
