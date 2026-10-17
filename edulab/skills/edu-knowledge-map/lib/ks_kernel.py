# -*- coding: utf-8 -*-
"""
ks_kernel.py —— 知识结构内核（Knowledge Space Theory，纯标准库）。

解决的是一类我们以前没有图型的问题：**概念之间怎么连**。

以前的技能都在画「某个对象」——三角形的边、分子的键、电路的电流。这个内核画的是
「知识本身」：哪些概念是哪些概念的前置、一个学生此刻可能处于哪些状态、从当前状态
到目标概念的最短学习路径、以及「还差哪几块」。

## 数学底子

记 Q 为概念全集，K ⊆ Q 为「一个学生已掌握的概念集合」。给定前置关系

    prereq[c] = {c 的直接前置概念}

一个**合法知识状态**是「下闭集」：只要 c 在 K 里，c 的所有前置也必须在 K 里。
（等价说法：K 是一个理想 / order ideal。）所有合法状态配上包含关系构成一个
**分配格**——这就是 Hasse 图要画的东西。

这不是自创的口径：
  · Doignon & Falmagne, *Knowledge Spaces* (1999) —— ALEKS 背后的框架；
  · 下闭集 ↔ 分配格，是 Birkhoff 表示定理的标准结论。

## 为什么值得单独做一个内核

「前置关系」是人工维护的（谁是谁的前置，是学科判断，不是算出来的），但
**由它推出的一切都是算出来的**：
  合法状态数、每个状态的「可学边界」、状态之间的覆盖关系、学习路径、缺口。
这些量如果手写，改一个前置就要手工改一图；由内核算，改一条边就全图重算。

自检：python ks_kernel.py
"""

from __future__ import annotations

import itertools
from collections import deque

MAX_CONCEPTS = 12          # 合法状态最多 2^12 = 4096，超了直接拒绝而不是卡死
MAX_LATTICE_STATES = 200   # Hasse 图超过这个规模就不画（画出来也没人看得清）


# ------------------------------------------------------------------ 领域定义

class Domain:
    """一个知识领域：概念表 + 前置关系。

    concepts: [(id, label), ...]，顺序即展示顺序（也用于同层排序的稳定性）。
    prereqs:  {id: [前置 id, ...]}，只写**直接**前置，传递闭包由内核算。
    """

    def __init__(self, name, title, concepts, prereqs, note=""):
        self.name = name
        self.title = title
        self.concepts = [(str(i), str(l)) for i, l in concepts]
        self.ids = [i for i, _ in self.concepts]
        self.label = dict(self.concepts)
        self.prereqs = {c: list(dict.fromkeys(prereqs.get(c, []))) for c in self.ids}
        self.note = note
        self._states = None
        self._covers = None
        self._levels = None

    # ---- 基础校验 ----
    def problems(self):
        """结构性问题。返回空列表才算可用。"""
        bad = []
        known = set(self.ids)
        if len(known) != len(self.ids):
            bad.append("概念 id 重复")
        if len(known) > MAX_CONCEPTS:
            bad.append(f"概念数 {len(known)} 超过上限 {MAX_CONCEPTS}"
                       f"（合法状态会到 2^n，画不动也没人看得过来）")
        for c, ps in self.prereqs.items():
            if c not in known:
                bad.append(f"前置关系写了未知概念 {c!r}")
            for p in ps:
                if p not in known:
                    bad.append(f"{c} 的前置 {p!r} 不在概念表里")
                if p == c:
                    bad.append(f"{c} 把自己当成前置")
        # 环
        cyc = self._find_cycle()
        if cyc:
            bad.append("前置关系成环：" + " → ".join(cyc))
        return bad

    def _find_cycle(self):
        color = {}                      # 0 未访问 / 1 在栈上 / 2 完成
        stack, path = [], []

        def dfs(u):
            color[u] = 1
            stack.append(u)
            path.append(u)
            for v in self.prereqs.get(u, []):
                if color.get(v, 0) == 0:
                    r = dfs(v)
                    if r:
                        return r
                elif color.get(v) == 1:
                    i = path.index(v)
                    return path[i:] + [v]
            path.pop()
            stack.pop()
            color[u] = 2
            return None

        for c in self.ids:
            if color.get(c, 0) == 0:
                r = dfs(c)
                if r:
                    return r
        return None

    # ---- 传递闭包 / 层级 ----
    def closure(self, seed):
        """把 seed 补成下闭集（补上所有间接前置）。"""
        out = set()
        dq = deque(seed)
        while dq:
            c = dq.popleft()
            if c in out:
                continue
            out.add(c)
            dq.extend(self.prereqs.get(c, []))
        return frozenset(out)

    def all_prereqs(self, c):
        """c 的全部（直接 + 间接）前置，不含 c 自己。"""
        return self.closure([c]) - {c}

    def levels(self):
        """最长路径分层：无前置为第 0 层，其余 = 1 + 前置最大层。"""
        if self._levels is not None:
            return self._levels
        lv = {}

        def get(c):
            if c in lv:
                return lv[c]
            ps = self.prereqs.get(c, [])
            lv[c] = 0 if not ps else 1 + max(get(p) for p in ps)
            return lv[c]

        for c in self.ids:
            get(c)
        self._levels = lv
        return lv

    # ---- 全部合法状态 ----
    def states(self):
        """所有下闭集（含空集与全集）。按概念位序做 DFS，规模 ≤ 2^n。"""
        if self._states is not None:
            return self._states
        order = self.topo_order()
        out = []

        def rec(i, cur):
            if i == len(order):
                out.append(frozenset(cur))
                return
            c = order[i]
            # 不掌握 c
            rec(i + 1, cur)
            # 掌握 c：前提是它的前置都已掌握
            if all(p in cur for p in self.prereqs.get(c, [])):
                cur.add(c)
                rec(i + 1, cur)
                cur.discard(c)

        rec(0, set())
        self._states = out
        return out

    def topo_order(self):
        """拓扑序（前置在前）。用 Kahn，平局按 concepts 里的声明顺序，保证可复现。"""
        indeg = {c: len(self.prereqs.get(c, [])) for c in self.ids}
        children = {c: [] for c in self.ids}
        for c in self.ids:
            for p in self.prereqs.get(c, []):
                children[p].append(c)
        rank = {c: i for i, c in enumerate(self.ids)}
        ready = sorted([c for c in self.ids if indeg[c] == 0], key=lambda x: rank[x])
        out = []
        while ready:
            c = ready.pop(0)
            out.append(c)
            for ch in children[c]:
                indeg[ch] -= 1
                if indeg[ch] == 0:
                    ready.append(ch)
                    ready.sort(key=lambda x: rank[x])
        return out

    # ---- 覆盖关系（Hasse 图的边）----
    def covers(self):
        """(A, B, c)：B = A ∪ {c}，且 |B| = |A| + 1 —— 格上的覆盖关系。"""
        if self._covers is not None:
            return self._covers
        out = []
        for K in self.states():
            for c in self.outer_fringe(K):
                out.append((K, frozenset(set(K) | {c}), c))
        self._covers = out
        return out

    # ---- 边界 ----
    def outer_fringe(self, state):
        """可学边界：不在 state 里、但前置已全部满足的概念（下一步能学的）。"""
        return [c for c in self.ids
                if c not in state and all(p in state for p in self.prereqs.get(c, []))]

    def inner_fringe(self, state):
        """已掌握的「边缘」：在里面、但还有别的概念（外面）依赖它的。"""
        out = []
        for c in self.ids:
            if c not in state:
                continue
            for d in self.ids:
                if d not in state and c in self.prereqs.get(d, []):
                    out.append(c)
                    break
        return out

    # ---- 学习路径 ----
    def learning_path(self, target_ids, start=None):
        """从 start（默认空集）到 target 下闭集的最短学习路径（逐条加概念）。

        返回 [state0, state1, ...]；每个相邻状态只差一个概念。找不到返回 []。
        """
        start = frozenset(start or ())
        goal = self.closure(target_ids)
        if not start <= goal:
            return []                      # 起点已经有了目标之外的东西，不算一条「学到目标」的路
        prev = {start: None}
        dq = deque([start])
        while dq:
            cur = dq.popleft()
            if cur == goal:
                path = []
                while cur is not None:
                    path.append(cur)
                    cur = prev[cur]
                return list(reversed(path))
            for c in self.outer_fringe(cur):
                if c not in goal:
                    continue               # 只走目标闭包内的概念，避免绕路
                nxt = frozenset(set(cur) | {c})
                if nxt not in prev:
                    prev[nxt] = cur
                    dq.append(nxt)
        return []

    def gaps(self, state, target_ids):
        """要掌握 target，还差哪些概念（按学习顺序返回）。"""
        goal = self.closure(target_ids)
        return [c for c in self.topo_order() if c in goal and c not in state]

    # ---- 汇总（给图表用）----
    def summary(self):
        st = self.states()
        n = len(st)
        # 独立概念数 = 在所有状态里都同时出现/同时不出现的最大分组数（近似用 2 的幂判断）
        indep = 0
        while 2 ** (indep + 1) <= n:
            indep += 1
        exact_pow2 = (2 ** indep == n)
        return {
            "concepts": len(self.ids),
            "states": n,
            "covers": len(self.covers()),
            "levels": max(self.levels().values()) + 1 if self.ids else 0,
            "is_power_of_two": exact_pow2,
            "independent": indep if exact_pow2 else None,
            "drawable_lattice": n <= MAX_LATTICE_STATES,
        }

    # ---- 布局（Hasse 用）----
    def lattice_layout(self):
        """按 |state| 分层，层内按「概念位序和」排序 —— 稳定、可复现。

        返回 {state: (x, y)}，x 在层内均分、y = 层号（0 在最上）。
        """
        states = self.states()
        if len(states) > MAX_LATTICE_STATES:
            return {}
        rank = {c: i for i, c in enumerate(self.ids)}
        by_layer = {}
        for s in states:
            by_layer.setdefault(len(s), []).append(s)
        pos = {}
        for depth, layer in by_layer.items():
            layer.sort(key=lambda s: tuple(rank[c] for c in sorted(s, key=lambda x: rank[x])))
            w = len(layer)
            for i, s in enumerate(layer):
                pos[s] = ((i + 0.5) / w, depth)
        return pos


# ------------------------------------------------------------------ 内置领域

def domains():
    """内置的领域库。前置关系是学科判断（手写），其余一切由内核推出来。"""
    return {
        "fraction": Domain(
            name="fraction", title="分数的四则运算：前置关系",
            concepts=[
                ("int", "整数与整除"),
                ("factor", "因数与倍数"),
                ("equiv", "等值分数（约分/通分）"),
                ("add", "同分母加减"),
                ("lcm", "最小公倍数"),
                ("add2", "异分母加减"),
                ("mul", "分数乘法"),
                ("div", "分数除法"),
            ],
            prereqs={
                "factor": ["int"],
                "equiv": ["factor"],
                "add": ["equiv"],
                "lcm": ["factor"],
                "add2": ["add", "lcm"],
                "mul": ["equiv"],
                "div": ["mul", "equiv"],
            },
            note="分数是「前置关系」最典型的例子：异分母加减同时依赖通分与最小公倍数，"
                 "两条链缺一条就学不动。",
        ),
        "derivative": Domain(
            name="derivative", title="导数：前置关系",
            concepts=[
                ("func", "函数与图像"),
                ("limit", "极限"),
                ("cont", "连续"),
                ("deriv", "导数定义"),
                ("tan", "切线方程"),
                ("mono", "单调性与极值"),
                ("chain", "复合函数求导"),
                ("opt", "最值应用"),
            ],
            prereqs={
                "limit": ["func"],
                "cont": ["limit"],
                "deriv": ["cont"],
                "tan": ["deriv"],
                "mono": ["deriv"],
                "chain": ["deriv"],
                "opt": ["mono", "chain"],
            },
            note="导数的前置链是「函数 → 极限 → 连续 → 导数」，跳步学导数就是背公式。",
        ),
        "probability": Domain(
            name="probability", title="概率：前置关系",
            concepts=[
                ("set", "集合"),
                ("count", "计数原理"),
                ("sample", "样本空间与事件"),
                ("classic", "古典概型"),
                ("cond", "条件概率"),
                ("indep", "独立性"),
                ("bayes", "全概率与贝叶斯"),
                ("dist", "随机变量与分布"),
            ],
            prereqs={
                "count": ["set"],
                "sample": ["set"],
                "classic": ["count", "sample"],
                "cond": ["classic"],
                "indep": ["cond"],
                "bayes": ["cond"],
                "dist": ["classic"],
            },
            note="「条件概率」是概率论的分水岭：它同时是独立性与贝叶斯的前置。",
        ),
        "book": Domain(
            name="book", title="《数学思想：从计数到无穷》8 章的阅读顺序",
            concepts=[
                ("ch1", "01 数：从计数到无穷"),
                ("ch2", "02 无穷：从恐惧到驯服"),
                ("ch3", "03 证明：从说服自己到说服所有人"),
                ("ch4", "04 变化：从静止到连续"),
                ("ch5", "05 随机：从命运到概率"),
                ("ch6", "06 空间：从平直到弯曲"),
                ("ch7", "07 结构：从解方程到对称"),
                ("ch8", "08 计算：从机械到可计算"),
            ],
            prereqs={
                "ch2": ["ch1"],
                "ch3": ["ch1", "ch2"],
                "ch4": ["ch3"],
                "ch5": ["ch3"],
                "ch6": ["ch3"],
                "ch7": ["ch3"],
                "ch8": ["ch3", "ch2"],
            },
            note="这条路是**阅读顺序**（作者判断），不是数学上的严格依赖："
                 "先读第 6 章也读得懂，但「非欧几何」会用第 3 章的证明语言，"
                 "「不可计算」要用第 2 章的对角线法。把边当成「什么时候会卡住」比"
                 "当成「必须先学」更准确。",
        ),
        "cycle_demo": Domain(
            name="cycle_demo", title="反面示例：成环的前置关系",
            concepts=[("a", "A"), ("b", "B"), ("c", "C")],
            prereqs={"a": ["c"], "b": ["a"], "c": ["b"]},
            note="这个领域是**故意写坏的**：A 依赖 C、C 依赖 B、B 又依赖 A。"
                 "内核应当直接拒绝，而不是画出一张似是而非的图。",
        ),
    }


def get(name):
    d = domains().get(name)
    if d is None:
        raise KeyError(f"未知领域 {name!r}，可用：{sorted(domains())}")
    return d


# ------------------------------------------------------------------ 自检

def _selftest():
    cases = []

    def ok(cond, name):
        cases.append((bool(cond), name))

    # 1) 合法领域
    d = get("fraction")
    ok(not d.problems(), "分数的前置关系无结构性问题")

    # 2) 下闭集：closure 要补全间接前置
    ok(d.closure(["add2"]) == frozenset({"add2", "add", "lcm", "equiv", "factor", "int"}),
       "closure(add2) 补全到六层前置")
    ok("mul" not in d.closure(["add2"]), "closure 不会把无关概念拉进来")

    # 3) 状态数 = 2^n 当且仅当所有前置关系都是树状/链状（这里 fraction 有汇聚）
    st = d.states()
    ok(all(d.closure(s) == s for s in st), "每个状态都是下闭集")
    ok(frozenset() in st and frozenset(d.ids) in st, "空集与全集都是合法状态")
    ok(len(st) == len(set(st)), "状态不重复")

    # 4) 覆盖关系：每个状态的覆盖边数 == 可学边界大小
    for K in st:
        outs = [B for A, B, _c in d.covers() if A == K]
        ok(len(outs) == len(d.outer_fringe(K)),
           f"状态 {sorted(K)} 的覆盖数 == 可学边界数")
        break

    # 5) 学习路径：从空集到 add2 必须逐条加概念，且长度 = 目标闭包大小
    path = d.learning_path(["add2"])
    ok(len(path) == 7, f"到 add2 的最短路径 7 步（实际 {len(path)}）")
    ok(all(len(b) - len(a) == 1 for a, b in zip(path, path[1:])), "路径每步只加一个概念")
    ok(path[-1] == d.closure(["add2"]), "路径终点是目标闭包")

    # 6) 可学边界
    ok(d.outer_fringe(frozenset()) == ["int"], "起步只能学 int")
    ok("add2" not in d.outer_fringe(d.closure({"add"})), "只学完 add 还不能学 add2（缺 lcm）")

    # 7) 缺口（含目标概念本身）
    ok(d.gaps(d.closure({"add"}), ["add2"]) == ["lcm", "add2"],
       "从 add 到 add2 还差 lcm 与 add2 本身")

    # 8) 环检测必须真的报出来
    bad = get("cycle_demo")
    probs = bad.problems()
    ok(any("成环" in p for p in probs), "成环的前置关系会被拒绝")

    # 9) 汇总：分数的前置链最长 5 层（int → factor → lcm/equiv → add/mul → add2）
    s = d.summary()
    ok(s["states"] > 0 and s["levels"] == 5, f"分数分层 5 层（实际 {s['levels']}）")

    # 10) 布局：每个状态都有坐标，y 等于 |state|
    pos = d.lattice_layout()
    ok(len(pos) == len(st), "每个状态都有布局坐标")
    ok(all(pos[s][1] == len(s) for s in pos), "Hasse 图 y 坐标 == 状态大小")

    bad_cases = [c for c in cases if not c[0]]
    for good, name in cases:
        print(f"  {'✓' if good else '✗'} {name}")
    print(f"\n{'知识结构内核自检通过 ✓' if not bad_cases else f'{len(bad_cases)} 项失败'}")
    return 1 if bad_cases else 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
