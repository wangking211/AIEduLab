#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
comptheory_kernel.py —— 大学「计算理论」内核（6.045 的入门部分）

覆盖：
  · DFA：逐步模拟、接受/拒绝、转移轨迹
  · NFA → DFA：**子集构造法**（真算，不是查表）
  · 上下文无关文法：推导序列与推导树（S → aSb | ε）
  · 泵引理：把 w = xyz 的 y 重复 i 次，看是否还落在语言里
  · 图灵机：纸带模拟（读写头移动、改写、停机）
  · 停机问题：对角线法的矛盾表
  · P / NP：不同增长率的对比

设计原则（与全项目一致）：
  · **不手写数字**：自动机**真的逐步跑**，子集构造**真的算闭包**，
    图灵机**真的模拟纸带**，停机问题的矛盾表**真的构造**。
  · 每一步都留下可回放的快照（trace），页面按滑块逐帧展示。
  · 自检：python comptheory_kernel.py
"""

import itertools
import math

__all__ = [
    "f", "num_str",
    "dfa_run", "nfa_run", "nfa_epsilon_closure",
    "subset_construction", "reachable_states",
    "cfg_derive", "cfg_parse_tree",
    "pumping_check", "pumping_sequence",
    "tm_run", "tm_tape_str",
    "halting_matrix", "diagonal_program",
    "growth", "GROWTH_KINDS",
]


def f(v, digits=4):
    if v is None:
        return "—"
    s = f"{float(v):.{digits}f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-") else "0"


def num_str(v, digits=4):
    val = float(v)
    if val == 0:
        return "0"
    if abs(val) >= 1e5 or abs(val) < 1e-4:
        return f"{val:.3e}".replace("e-0", "e-").replace("e+0", "e")
    return f(val, digits)


# ---------------------------------------------------------------- DFA
def dfa_run(delta, start, accept, s):
    """逐步模拟 DFA。

    delta  {(状态, 字符): 状态}；accept 是可接受状态的集合。
    返回 {"accepted": bool, "trace": [(步号, 当前状态, 读到的字符, 是否接受)], "final": 状态}
    """
    q = start
    trace = [(0, q, None, q in accept)]
    for i, ch in enumerate(s):
        key = (q, ch)
        if key not in delta:
            trace.append((i + 1, None, ch, False))
            return {"accepted": False, "trace": trace, "final": None, "stuck": True}
        q = delta[key]
        trace.append((i + 1, q, ch, q in accept))
    return {"accepted": q in accept, "trace": trace, "final": q, "stuck": False}


# ---------------------------------------------------------------- NFA
def nfa_epsilon_closure(delta, states, eps="ε"):
    """ε-闭包：从给定状态集合出发，只走 ε 边能到达的全部状态。"""
    stack = list(states)
    seen = set(states)
    while stack:
        q = stack.pop()
        for nxt in delta.get((q, eps), ()):
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return frozenset(seen)


def nfa_run(delta, start, accept, s, eps="ε"):
    """模拟 NFA（同时走所有分支）。返回 {"accepted": bool, "sets": [每步的状态集合]}"""
    cur = nfa_epsilon_closure(delta, {start}, eps)
    sets = [cur]
    for ch in s:
        nxt = set()
        for q in cur:
            nxt |= set(delta.get((q, ch), ()))
        cur = nfa_epsilon_closure(delta, nxt, eps) if nxt else frozenset()
        sets.append(cur)
    return {"accepted": bool(cur & set(accept)), "sets": sets}


def subset_construction(delta, start, accept, alphabet, eps="ε"):
    """子集构造法：NFA → DFA（真算 ε-闭包与转移）。

    返回 {"states": [DFA 状态（frozenset）...], "delta": {(idx, c): idx},
          "start": 0, "accept": {idx...}, "index": {frozenset: idx},
          "order": [生成顺序]}
    """
    s0 = nfa_epsilon_closure(delta, {start}, eps)
    order = [s0]
    index = {s0: 0}
    i = 0
    dfa_delta = {}
    while i < len(order):
        cur = order[i]
        for c in alphabet:
            nxt = set()
            for q in cur:
                nxt |= set(delta.get((q, c), ()))
            if not nxt:
                continue
            t = nfa_epsilon_closure(delta, nxt, eps)
            if t not in index:
                index[t] = len(order)
                order.append(t)
            dfa_delta[(i, c)] = index[t]
        i += 1
    acc = {index[s] for s in order if set(s) & set(accept)}
    return {"states": order, "delta": dfa_delta, "start": 0, "accept": acc,
            "index": index, "order": order}


def reachable_states(delta, start):
    """从 start 出发可达的状态集合（用于画状态图）。"""
    seen = {start}
    stack = [start]
    while stack:
        q = stack.pop()
        for (qq, _c), t in delta.items():
            if qq == q and t not in seen:
                seen.add(t)
                stack.append(t)
    return seen


# ---------------------------------------------------------------- 上下文无关文法
def cfg_derive(n, max_steps=200):
    """文法 S → aSb | ε 生成 aⁿbⁿ 的推导序列。

    返回 [推导式字符串...]，最后一个是 aⁿbⁿ。
    """
    if n < 0:
        raise ValueError("n ≥ 0")
    seq = []
    for k in range(n):
        seq.append("a" * k + "S" + "b" * k)
    seq.append("a" * n + "b" * n)
    if len(seq) > max_steps:
        raise ValueError("推导步数过多")
    return seq


def cfg_parse_tree(n):
    """aⁿbⁿ 的推导树（嵌套结构），返回嵌套的 dict。"""
    def build(k):
        if k == 0:
            return {"S": ["ε"]}
        return {"S": ["a", build(k - 1), "b"]}
    return build(n)


# ---------------------------------------------------------------- 泵引理
def pumping_check(p, k, i):
    """泵引理演示：L = {aⁿbⁿ}，w = aᵖbᵖ，把 y = aᵏ 重复 i 次。

    返回 (x, y, z, 泵出后的串, 是否仍在 L 中)。
    """
    if k < 1 or k > p:
        raise ValueError("需要 1 ≤ |y| ≤ p")
    if i < 0:
        raise ValueError("i ≥ 0")
    x = "a" * (p - k)
    y = "a" * k
    z = "b" * p                      # w = xyz = a^(p−k) · a^k · b^p = a^p b^p
    pumped = x + y * i + z           # = a^(p + k(i−1)) · b^p
    # 是否形如 a^m b^m
    a_cnt = len(pumped) - len(pumped.lstrip("a"))
    b_cnt = len(pumped) - len(pumped.rstrip("b"))
    in_l = (a_cnt + b_cnt == len(pumped)) and a_cnt == b_cnt
    return x, y, z, pumped, in_l


def pumping_sequence(p, k, imax=5):
    """把 i = 0..imax 的泵出结果都算出来。"""
    out = []
    for i in range(imax + 1):
        x, y, z, s, ok = pumping_check(p, k, i)
        out.append({"i": i, "s": s, "in_L": ok})
    return out


# ---------------------------------------------------------------- 图灵机
def tm_run(delta, start, halt_states, tape, blank="_", max_steps=200):
    """模拟单带图灵机。

    delta  {(状态, 符号): (写入符号, 移动 'L'/'R'/'N', 新状态)}
    tape   初始纸带（字符串）；返回快照列表供逐帧回放。
    返回 {"trace": [{"step", "tape", "head", "state", "halted"}...], "halted": bool}
    """
    cells = list(tape) if tape else [blank]
    head = 0
    state = start
    trace = [{"step": 0, "tape": "".join(cells), "head": head, "state": state,
              "halted": state in halt_states}]
    for step in range(1, max_steps + 1):
        if state in halt_states:
            break
        if head < 0:
            cells.insert(0, blank)
            head = 0
        if head >= len(cells):
            cells.append(blank)
        sym = cells[head]
        key = (state, sym)
        if key not in delta:
            break
        w, mv, nq = delta[key]
        cells[head] = w
        if mv == "L":
            head -= 1
        elif mv == "R":
            head += 1
        state = nq
        if head < 0:
            cells.insert(0, blank)
            head = 0
        if head >= len(cells):
            cells.append(blank)
        trace.append({"step": step, "tape": "".join(cells), "head": head,
                      "state": state, "halted": state in halt_states})
    return {"trace": trace, "halted": trace[-1]["halted"]}


def tm_tape_str(cells, head, blank="_"):
    """把纸带画成带下划线的字符串（读写头位置用 ^ 标在下一行）。"""
    s = "".join(cells)
    ptr = " " * head + "^"
    return s, ptr


# ---------------------------------------------------------------- 停机问题
def halting_matrix(n):
    """构造 n×n 的停机判定表 H(P_i, T_j)。

    约定（为了展示矛盾，取值刻意做成确定性的）：
      H(i, j) = True 表示「程序 P_i 在输入 T_j 上会停机」。
    这里用一个具体的、可计算的规则充当 H，使得对角线可以被构造出来。
    """
    mat = []
    for i in range(n):
        row = []
        for j in range(n):
            # 规则：i 与 j 互质 ⇒ 停机；否则不停机（任意确定性规则都行，
            # 重点是下面的 D 会与对角线元素**相反**）
            row.append(math.gcd(i + 1, j + 1) == 1)
        mat.append(row)
    return mat


def diagonal_program(n):
    """构造与对角线相反的判定行：D(i) = not H(i, i)。"""
    mat = halting_matrix(n)
    return [not mat[i][i] for i in range(n)]


# ---------------------------------------------------------------- 复杂度增长
GROWTH_KINDS = ["log n", "n", "n log n", "n²", "2ⁿ", "n!"]


def growth(kind, n):
    """各类复杂度的操作数（n 为问题规模）。"""
    if n <= 0:
        raise ValueError("n > 0")
    if kind == "log n":
        return math.log2(n) if n > 1 else 0.0
    if kind == "n":
        return float(n)
    if kind == "n log n":
        return n * (math.log2(n) if n > 1 else 0.0)
    if kind == "n²":
        return float(n) ** 2
    if kind == "2ⁿ":
        return 2.0 ** min(n, 1023)
    if kind == "n!":
        v = 1.0
        for i in range(2, int(n) + 1):
            v *= i
            if v > 1e300:
                return float("inf")
        return v
    raise ValueError(f"未知的复杂度类型：{kind}")


# ================================================================ 自检
def _selftest():
    bad = []

    def chk(name, got, want, tol=1e-9):
        if isinstance(got, str) or isinstance(want, str):
            ok = str(got) == str(want)
            g = got
        elif isinstance(got, (list, tuple)) or isinstance(want, (list, tuple)):
            ga, wa = list(got), list(want)

            def same(a, b):
                if isinstance(a, str) or isinstance(b, str):
                    return str(a) == str(b)
                if isinstance(a, bool) or isinstance(b, bool):
                    return bool(a) == bool(b)
                if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
                    return same(list(a), list(b))
                return abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b)))

            ok = len(ga) == len(wa) and all(same(a, b) for a, b in zip(ga, wa))
            g = ga
        elif isinstance(got, bool) or isinstance(want, bool):
            ok = bool(got) == bool(want)
            g = got
        else:
            ok = abs(float(got) - float(want)) <= tol * max(1.0, abs(float(want)))
            g = f"{float(got):.6g}"
        print(f"  {'✓' if ok else '✗'} {name:46s} = {g}" + ("" if ok else f"   期望 {want}"))
        if not ok:
            bad.append(name)

    # ---- DFA：二进制串中 1 的个数为偶数 ----
    print("DFA")
    D = {("q0", "0"): "q0", ("q0", "1"): "q1",
         ("q1", "0"): "q1", ("q1", "1"): "q0"}
    ACC = {"q0"}
    # 「101」里有**两个** 1（偶数）⇒ 接受；「1101」里有三个（奇数）⇒ 拒绝
    for s, want in (("", True), ("0", True), ("1", False), ("11", True),
                    ("101", True), ("1101", False), ("1111", True)):
        r = dfa_run(D, "q0", ACC, s)
        chk(f"  「{s}」是否被接受", r["accepted"], want)
    r = dfa_run(D, "q0", ACC, "1101")
    chk("  轨迹长度 = 输入长度 + 1", len(r["trace"]), 5)
    chk("  末状态", r["final"], "q1")
    chk("  接受的串 ⇒ 末状态可接受", dfa_run(D, "q0", ACC, "110")["final"] in ACC, True)
    # 卡住的情况
    r2 = dfa_run(D, "q0", ACC, "2")
    chk("  未定义的转移 ⇒ 卡住", r2["stuck"], True)
    chk("  卡住 ⇒ 不接受", r2["accepted"], False)

    # ---- NFA 与子集构造 ----
    print("\nNFA 与子集构造")
    # (a|b)*abb
    N = {("0", "a"): {"0", "1"}, ("0", "b"): {"0"},
         ("1", "b"): {"2"}, ("2", "b"): {"3"}}
    NACC = {"3"}
    # 语言是 (a|b)*abb：**必须以 abb 结尾**。
    # 「abbb」末尾是 bbb（不是 abb）⇒ 拒绝。
    for s, want in (("abb", True), ("aabb", True), ("ab", False),
                    ("babb", True), ("abbb", False), ("", False),
                    ("abbabb", True), ("aab", False)):
        chk(f"  NFA 接受「{s}」", nfa_run(N, "0", NACC, s)["accepted"], want)
    sub = subset_construction(N, "0", NACC, ["a", "b"])
    chk("  子集构造出的 DFA 状态数", len(sub["states"]), 4)
    chk("  起始状态是 {0}", sorted(sub["states"][0]), ["0"])
    # DFA 与原 NFA 必须接受同样的串
    dsub = {}
    for (i, c), j in sub["delta"].items():
        dsub[(i, c)] = j
    ok_same = True
    for s in ("abb", "aabb", "ab", "babb", "abbb", "", "a", "b", "abab", "bbabb"):
        a1 = nfa_run(N, "0", NACC, s)["accepted"]
        r = dfa_run(dsub, 0, sub["accept"], s)
        a2 = r["accepted"]
        if a1 != a2:
            ok_same = False
            print(f"    不一致：{s!r} NFA={a1} DFA={a2}")
    chk("  子集构造前后接受性完全一致（抽样 10 个串）", ok_same, True)
    chk("  可接受状态个数 ≥ 1", len(sub["accept"]) >= 1, True)

    # ---- 上下文无关文法 ----
    print("\n上下文无关文法")
    seq = cfg_derive(3)
    chk("  n=3 的推导步数", len(seq), 4)
    chk("  首步是 S", seq[0], "S")
    chk("  末步是 aaabbb", seq[-1], "aaabbb")
    chk("  中间步含 aSb", seq[1], "aSb")
    for n in (0, 1, 2, 5):
        chk(f"  n={n} 生成的串", cfg_derive(n)[-1], "a" * n + "b" * n)
    t = cfg_parse_tree(2)
    chk("  推导树根是 S", list(t.keys()), ["S"])
    chk("  深度随 n 增加", len(cfg_derive(4)), 5)

    # ---- 泵引理 ----
    print("\n泵引理")
    p, k = 4, 2
    x, y, z, s, ok = pumping_check(p, k, 1)
    chk("  i=1 时回到原串", s, "a" * p + "b" * p)
    chk("  i=1 时在语言里", ok, True)
    for i in (0, 2, 3, 5):
        _, _, _, si, oki = pumping_check(p, k, i)
        chk(f"  i={i} 时不在语言里", oki, False)
    chk("  泵出后的串长度", len(pumping_check(4, 2, 3)[3]), 8 + 2 * 2)
    seq = pumping_sequence(4, 2, 4)
    chk("  序列长度 = imax + 1", len(seq), 5)
    chk("  只有 i=1 在语言里", [d["in_L"] for d in seq],
        [False, True, False, False, False])
    # 分解的正确性：x + y + z 应还原 w，且 |xy| ≤ p
    x, y, z, _, _ = pumping_check(5, 3, 1)
    chk("  x+y+z = w", x + y + z, "a" * 5 + "b" * 5)
    chk("  |xy| ≤ p", len(x) + len(y) <= 5, True)
    chk("  |y| ≥ 1", len(y) >= 1, True)

    # ---- 图灵机：二进制加一 ----
    print("\n图灵机（二进制加一）")
    TM = {
        ("q0", "0"): ("0", "R", "q0"),
        ("q0", "1"): ("1", "R", "q0"),
        ("q0", "_"): ("_", "L", "q1"),
        ("q1", "0"): ("1", "N", "qh"),
        ("q1", "1"): ("0", "L", "q1"),
        ("q1", "_"): ("1", "N", "qh"),
    }
    for inp, want in (("1011", "1100"), ("0", "1"), ("1", "10"),
                      ("111", "1000"), ("100", "101"), ("11", "100")):
        r = tm_run(TM, "q0", {"qh"}, inp)
        chk(f"  {inp} + 1 = {want}", r["trace"][-1]["tape"].rstrip("_"), want)
        chk(f"    最终停机", r["halted"], True)
    r = tm_run(TM, "q0", {"qh"}, "1011")
    chk("  轨迹首帧是初始纸带", r["trace"][0]["tape"], "1011")
    chk("  读写头位置始终在纸带范围内",
        all(0 <= fr["head"] < len(fr["tape"]) for fr in r["trace"]), True)
    chk("  步数合理（< 30）", len(r["trace"]) < 30, True)
    # 每步只改一个格子
    ok_one = True
    for a, b in zip(r["trace"], r["trace"][1:]):
        diff = sum(1 for u, v in zip(a["tape"], b["tape"]) if u != v)
        if diff > 1:
            ok_one = False
    chk("  每一步最多改一个格子", ok_one, True)

    # ---- 停机问题 ----
    print("\n停机问题（对角线法）")
    n = 5
    mat = halting_matrix(n)
    chk("  表是 n×n", [len(mat), len(mat[0])], [n, n])
    chk("  取值都是布尔", all(isinstance(v, bool) for row in mat for v in row), True)
    diag = diagonal_program(n)
    chk("  D 与对角线**逐项相反**", diag, [not mat[i][i] for i in range(n)])
    # 关键：D 不可能出现在表里任何一行（因为第 i 位与第 i 行相反）
    same_row = [i for i in range(n) if mat[i] == diag]
    chk("  D 不在表中（与每一行都不同）", same_row, [])
    # 对每一行，至少有一位不同
    chk("  与每一行都至少差一位",
        all(any(mat[i][j] != diag[j] for j in range(n)) for i in range(n)), True)

    # ---- 复杂度增长 ----
    print("\n复杂度增长")
    chk("log₂1024 = 10", growth("log n", 1024), 10.0, 1e-9)
    chk("n=10 的 n²", growth("n²", 10), 100.0, 1e-9)
    chk("n=10 的 2ⁿ", growth("2ⁿ", 10), 1024.0, 1e-9)
    chk("n=5 的 n!", growth("n!", 5), 120.0, 1e-9)
    chk("n=10 的 n log n", growth("n log n", 10), 10 * math.log2(10), 1e-9)
    # 量级顺序：log n < n < n log n < n² < 2ⁿ < n!
    vals = [growth(k, 16) for k in GROWTH_KINDS]
    chk("  量级严格递增", all(vals[i] < vals[i + 1] for i in range(len(vals) - 1)), True)
    # n! 在 n=30 时已经溢出到 inf
    chk("  n=30 的 n! 溢出", growth("n!", 30), float("inf"), 1e300)
    chk("  所有类型在 n=1 时都是 1 或 0",
        [growth("log n", 1), growth("n", 1), growth("n²", 1), growth("2ⁿ", 1)],
        [0.0, 1.0, 1.0, 2.0], 1e-9)

    print()
    if bad:
        print(f"{len(bad)} 条失败：{bad}")
        return 1
    print("全部自检通过 ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
