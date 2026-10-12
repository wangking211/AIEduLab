# -*- coding: utf-8 -*-
"""
cs_kernel.py — 计算机科学：**步骤轨迹引擎**（不是"算一个数"，而是"跑一遍算法、录下每一步"）。

设计要点：
  · 每个算法在 Python 端**真实执行**，把每一步的状态快照录进 steps 列表；
  · 模板（board.html）拿到 steps 后按进度滑块逐帧回放——动画里的每一步都是算出来的，不会编造；
  · 复杂度/进制/位运算这类"可精确算"的量用 sympy 或整数运算给出精确值。

覆盖（五个模块）：
  1. 算法可视化：冒泡/选择/插入/归并/快速排序、顺序/二分查找、复杂度曲线
  2. 数据结构：栈、队列、链表、二叉树、二叉搜索树、堆、哈希表
  3. 图算法：BFS、DFS、Dijkstra、最小生成树（Prim）
  4. 计算原理：进制转换、位运算、字符编码
  5. 算法思想：递归（调用树/栈帧）、贪心、动态规划（斐波那契/0-1 背包）

依赖: 仅标准库（sympy 可选，用于复杂度的精确表达式）。自检：python cs_kernel.py
"""

import math
from fractions import Fraction


# ==================== 轨迹记录器 ====================
class Trace:
    """收集步骤快照。每步是一个 dict，模板据此回放。"""

    def __init__(self):
        self.steps = []
        self.counters = {}
        self.meta = {}

    def add(self, **kw):
        self.steps.append(kw)
        return self

    def bump(self, key, n=1):
        self.counters[key] = self.counters.get(key, 0) + n
        return self

    def out(self, **meta):
        """把 meta 直接平铺到顶层，方便调用方 r["pos"] / r["result"] 读取。"""
        self.meta.update(meta)
        return {"steps": self.steps, "counters": self.counters, **self.meta}


# ==================== 1) 排序 ====================
def _snap(a, **kw):
    d = {"a": list(a)}
    d.update(kw)
    return d


def bubble_sort(arr):
    a, t = list(arr), Trace()
    n = len(a)
    t.add(**_snap(a, phase="start", note=f"初始数组（n={n}）"))
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            t.bump("compare")
            t.add(**_snap(a, cmp=[j, j + 1], sorted=list(range(n - i, n)),
                          note=f"比较 a[{j}]={a[j]} 与 a[{j+1}]={a[j+1]}"))
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                t.bump("swap")
                swapped = True
                t.add(**_snap(a, swap=[j, j + 1], sorted=list(range(n - i, n)),
                              note=f"逆序 → 交换，大的冒到右边"))
        t.add(**_snap(a, sorted=list(range(n - i - 1, n)), note=f"第 {i+1} 轮结束：a[{n-1-i}] 归位"))
        if not swapped:
            t.add(**_snap(a, sorted=list(range(n)), note="本轮无交换 → 已有序，提前结束"))
            break
    t.add(**_snap(a, sorted=list(range(n)), note="排序完成"))
    return t.out(algo="bubble", name="冒泡排序", complex="O(n²)")


def selection_sort(arr):
    a, t = list(arr), Trace()
    n = len(a)
    for i in range(n):
        k = i
        for j in range(i + 1, n):
            t.bump("compare")
            t.add(**_snap(a, cmp=[k, j], sorted=list(range(i)),
                          note=f"在未排序区找最小：当前最小 a[{k}]={a[k]}，比较 a[{j}]={a[j]}"))
            if a[j] < a[k]:
                k = j
        if k != i:
            a[i], a[k] = a[k], a[i]
            t.bump("swap")
        t.add(**_snap(a, swap=[i, k] if k != i else None, sorted=list(range(i + 1)),
                      note=f"把最小元素 a[{k}] 换到位置 {i}"))
    t.add(**_snap(a, sorted=list(range(n)), note="排序完成"))
    return t.out(algo="selection", name="选择排序", complex="O(n²)")


def insertion_sort(arr):
    a, t = list(arr), Trace()
    n = len(a)
    for i in range(1, n):
        key, j = a[i], i - 1
        t.add(**_snap(a, cmp=[i], sorted=list(range(i)), note=f"取出 a[{i}]={key}，准备插入左边的有序区"))
        while j >= 0:
            t.bump("compare")
            t.add(**_snap(a, cmp=[j, i], sorted=list(range(i)), note=f"比较 {a[j]} 与 {key}"))
            if a[j] > key:
                a[j + 1] = a[j]
                t.bump("move")
                t.add(**_snap(a, swap=[j, j + 1], sorted=list(range(i)), note=f"{a[j]} 比 {key} 大 → 后移一位"))
                j -= 1
            else:
                break
        a[j + 1] = key
        t.add(**_snap(a, sorted=list(range(i + 1)), note=f"把 {key} 插入位置 {j+1}"))
    t.add(**_snap(a, sorted=list(range(n)), note="排序完成"))
    return t.out(algo="insertion", name="插入排序", complex="O(n²)，近乎有序时接近 O(n)")


def merge_sort(arr):
    a, t = list(arr), Trace()
    t.add(**_snap(a, note="初始数组"))

    def rec(lo, hi, depth):
        if hi - lo <= 1:
            return
        mid = (lo + hi) // 2
        t.add(**_snap(a, range=[lo, hi], note=f"分：把 [{lo},{hi}) 拆成 [{lo},{mid}) 与 [{mid},{hi})"))
        rec(lo, mid, depth + 1)
        rec(mid, hi, depth + 1)
        L, R = a[lo:mid], a[mid:hi]
        i = j = 0
        for k in range(lo, hi):
            t.bump("compare")
            if j >= len(R) or (i < len(L) and L[i] <= R[j]):
                a[k] = L[i]; i += 1
            else:
                a[k] = R[j]; j += 1
            t.add(**_snap(a, range=[lo, hi], merge=k, note=f"合：把较小者写回 a[{k}]={a[k]}"))

    rec(0, len(a), 0)
    t.add(**_snap(a, sorted=list(range(len(a))), note="排序完成"))
    return t.out(algo="merge", name="归并排序", complex="O(n log n)")


def quick_sort(arr):
    a, t = list(arr), Trace()
    t.add(**_snap(a, note="初始数组"))

    def part(lo, hi):
        pivot = a[hi]
        t.add(**_snap(a, pivot=hi, range=[lo, hi], note=f"选 a[{hi}]={pivot} 为枢轴"))
        i = lo
        for j in range(lo, hi):
            t.bump("compare")
            t.add(**_snap(a, pivot=hi, range=[lo, hi], cmp=[j], note=f"a[{j}]={a[j]} 与枢轴 {pivot} 比较"))
            if a[j] < pivot:
                a[i], a[j] = a[j], a[i]
                if i != j:
                    t.bump("swap")
                t.add(**_snap(a, pivot=hi, range=[lo, hi], swap=[i, j], note=f"小于枢轴 → 换到左区位置 {i}"))
                i += 1
        a[i], a[hi] = a[hi], a[i]
        t.bump("swap")
        t.add(**_snap(a, pivot=i, range=[lo, hi], sorted=[i], note=f"枢轴归位到 {i}：左边都比它小，右边都比它大"))
        return i

    def rec(lo, hi):
        if lo < hi:
            p = part(lo, hi)
            rec(lo, p - 1)
            rec(p + 1, hi)

    rec(0, len(a) - 1)
    t.add(**_snap(a, sorted=list(range(len(a))), note="排序完成"))
    return t.out(algo="quick", name="快速排序", complex="平均 O(n log n)，最坏 O(n²)")


# ==================== 2) 查找 ====================
def linear_search(arr, target):
    a, t = list(arr), Trace()
    for i, v in enumerate(a):
        t.bump("compare")
        hit = (v == target)
        t.add(**_snap(a, cmp=[i], found=i if hit else None,
                      note=f"检查 a[{i}]={v} {'==' if hit else '≠'} {target}"))
        if hit:
            t.add(**_snap(a, found=i, sorted=list(range(len(a))), note=f"找到了！在位置 {i}"))
            return t.out(algo="linear_search", name="顺序查找", complex="O(n)", target=target, pos=i)
    t.add(**_snap(a, sorted=list(range(len(a))), note=f"找遍全部 {len(a)} 个元素，没找到 {target}"))
    return t.out(algo="linear_search", name="顺序查找", complex="O(n)", target=target, pos=-1)


def binary_search(arr, target):
    a, t = list(sorted(arr)), Trace()
    lo, hi = 0, len(a) - 1
    t.add(**_snap(a, range=[lo, hi], note=f"有序数组中查找 {target}：区间 [0,{hi}]"))
    while lo <= hi:
        mid = (lo + hi) // 2
        t.bump("compare")
        t.add(**_snap(a, range=[lo, hi], mid=mid, note=f"取中点 mid={mid}（下标 [{lo},{hi}] 的中点）"))
        if a[mid] == target:
            t.add(**_snap(a, range=[lo, hi], found=mid, note=f"a[{mid}]={a[mid]} 正好等于 {target}，找到！"))
            return t.out(algo="binary_search", name="二分查找", complex="O(log n)", target=target, pos=mid)
        elif a[mid] < target:
            t.add(**_snap(a, range=[lo, hi], mid=mid, note=f"a[{mid}]={a[mid]} < {target} → 目标在右半边，丢掉左半"))
            lo = mid + 1
        else:
            t.add(**_snap(a, range=[lo, hi], mid=mid, note=f"a[{mid}]={a[mid]} > {target} → 目标在左半边，丢掉右半"))
            hi = mid - 1
    t.add(**_snap(a, note=f"区间为空，{target} 不在数组中"))
    return t.out(algo="binary_search", name="二分查找", complex="O(log n)", target=target, pos=-1)


# ==================== 3) 复杂度 ====================
GROWTH = {
    "1":      ("O(1) 常数",       lambda n: 1),
    "logn":   ("O(log n) 对数",   lambda n: math.log2(n) if n > 0 else 0),
    "n":      ("O(n) 线性",       lambda n: n),
    "nlogn":  ("O(n log n)",      lambda n: n * math.log2(n) if n > 0 else 0),
    "n2":     ("O(n²) 平方",      lambda n: n * n),
    "n3":     ("O(n³) 立方",      lambda n: n ** 3),
    "2n":     ("O(2ⁿ) 指数",      lambda n: 2 ** n),
}


def growth_values(kinds, nmax=64):
    """给出若干复杂度在 n=1..nmax 的取值表（供曲线画板）。"""
    out = {}
    for k in kinds:
        assert k in GROWTH, f"未知复杂度 {k}"
        label, fn = GROWTH[k]
        out[k] = {"label": label, "values": [fn(n) for n in range(0, nmax + 1)]}
    return out


def ops_at(kind, n):
    """某复杂度在规模 n 时的运算次数（精确整数，便于讲"差别有多大"）。"""
    label, fn = GROWTH[kind]
    v = fn(n)
    return {"kind": kind, "label": label, "n": n, "ops": int(v) if float(v).is_integer() else v}


def max_n_for_budget(kind, budget):
    """给定运算预算，某复杂度最多能处理多大的 n（指数级会小得惊人）。"""
    label, fn = GROWTH[kind]
    lo, hi = 1, 1
    while fn(hi) <= budget and hi < 10 ** 7:
        hi *= 2
    lo = max(1, hi // 2)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if fn(mid) <= budget:
            lo = mid
        else:
            hi = mid - 1
    return {"kind": kind, "label": label, "budget": budget, "max_n": lo}


# ==================== 4) 栈 / 队列 / 链表 ====================
def stack_demo(ops):
    """ops: [("push", v) | ("pop",)]。返回每一步的栈内容（LIFO）。"""
    st, t = [], Trace()
    t.add(stack=list(st), op="初始为空", note="栈：后进先出（LIFO），只能在栈顶进出")
    for op in ops:
        if op[0] == "push":
            st.append(op[1])
            t.add(stack=list(st), op=f"push({op[1]})", top=len(st) - 1, note=f"把 {op[1]} 压入栈顶")
        else:
            if st:
                v = st.pop()
                t.add(stack=list(st), op=f"pop() → {v}", note=f"从栈顶弹出 {v}")
            else:
                t.add(stack=list(st), op="pop() 失败", note="栈已空，不能弹出（栈下溢）")
    return t.out(name="栈", rule="后进先出 LIFO")


def queue_demo(ops):
    """ops: [("enq", v) | ("deq",)]。FIFO。"""
    q, t = [], Trace()
    t.add(queue=list(q), op="初始为空", note="队列：先进先出（FIFO），队尾进、队头出")
    for op in ops:
        if op[0] == "enq":
            q.append(op[1])
            t.add(queue=list(q), op=f"enqueue({op[1]})", note=f"把 {op[1]} 加入队尾")
        else:
            if q:
                v = q.pop(0)
                t.add(queue=list(q), op=f"dequeue() → {v}", note=f"从队头取出 {v}")
            else:
                t.add(queue=list(q), op="dequeue() 失败", note="队列已空（队空下溢）")
    return t.out(name="队列", rule="先进先出 FIFO")


def linked_list_demo(values, insert_after=None, delete_index=None, value=None):
    """单链表：建表 → 插入 → 删除，记录指针重连的每一步。

    insert_after / delete_index 都是**下标**（不是值）。
    value 是新结点的值；不给就取 prev 的值 +10。
    删除时若没有前驱（说明它是表头）则移动 head。
    """
    t = Trace()
    nodes = [{"id": f"n{i}", "val": v, "next": (f"n{i+1}" if i + 1 < len(values) else None)}
             for i, v in enumerate(values)]
    head = "n0" if nodes else None

    def snap(note, **kw):
        d = {"nodes": [dict(x) for x in nodes], "head": head, "note": note}
        d.update(kw)
        return d

    t.add(**snap("初始链表：头指针 head 指向第一个结点"))
    if insert_after is not None and 0 <= insert_after < len(nodes):
        nid = f"x{len(nodes)}"
        prev = nodes[insert_after]
        new_val = value if value is not None else prev["val"] + 10
        nodes.append({"id": nid, "val": new_val, "next": prev["next"]})
        t.add(**snap("新结点先指向 prev.next（顺序不能反，否则后继会丢）",
                     new=nid, prev=prev["id"]))
        prev["next"] = nid
        t.add(**snap("再让 prev.next 指向新结点 → 插入完成",
                     new=nid, prev=prev["id"], hi=[nid]))
    if delete_index is not None and 0 <= delete_index < len(nodes):
        target = nodes[delete_index]
        prevs = [x for x in nodes if x["next"] == target["id"]]
        if prevs:
            prevs[0]["next"] = target["next"]
            t.add(**snap("让前驱绕过待删结点 → 删除完成",
                         hi=[target["id"]], prev=prevs[0]["id"]))
        else:
            head = target["next"]
            t.add(**snap("删除的是头结点 → head 后移", hi=[target["id"]]))
    return t.out(name="单链表")


# ==================== 5) 二叉树 / BST / 堆 ====================
def _layout_tree(vals):
    """按完全二叉树的层次编号给出 (x, y) 坐标（用不到的位置为 None）。"""
    pos, nodes = {}, []
    n = len(vals)
    depth = max(1, math.floor(math.log2(n)) + 1)
    for i, v in enumerate(vals):
        if v is None:
            continue
        lvl = math.floor(math.log2(i + 1))
        offset = (i + 1) - 2 ** lvl
        slots = 2 ** lvl
        x = (offset + 0.5) / slots
        y = 1 - lvl / max(1, depth)
        nid = f"t{i}"
        pos[nid] = (round(x, 4), round(y, 4))
        nodes.append({"id": nid, "val": v, "lvl": lvl,
                      "parent": f"t{(i - 1) // 2}" if i > 0 else None})
    return nodes, pos


def binary_tree_traversals(vals):
    """三种遍历（前/中/后序）在**完全二叉树**上的访问顺序。"""
    n = len(vals)
    def rec(i, order):
        if i >= n or vals[i] is None:
            return
        if order == "pre":  seq.append(i)
        rec(2 * i + 1, order)
        if order == "in":   seq.append(i)
        rec(2 * i + 2, order)
        if order == "post": seq.append(i)
    out = {}
    for order in ("pre", "in", "post"):
        seq = []
        rec(0, order)
        out[order] = seq
    nodes, pos = _layout_tree(vals)
    # 为每种遍历生成步骤
    steps = {}
    for order, seq in out.items():
        ss, seen = [], []
        for i in seq:
            seen.append(f"t{i}")
            ss.append({"visit": f"t{i}", "visited": list(seen), "note": f"访问结点 {vals[i]}"})
        steps[order] = ss
    return {"nodes": nodes, "pos": pos, "orders": out, "steps": steps,
            "names": {"pre": "前序遍历（根→左→右）", "in": "中序遍历（左→根→右）", "post": "后序遍历（左→右→根）"}}


def bst_insert(values, target=None):
    """二叉搜索树插入 + 查找，记录比较路径。"""
    t = Trace()
    tree = {"val": None, "left": None, "right": None}

    def ins(node, v, path):
        if node["val"] is None:
            node["val"] = v
            t.bump("insert")
            t.add(path=list(path), op=f"insert({v})", note=f"空位 → 插入 {v}")
            return
        t.bump("compare")
        if v < node["val"]:
            t.add(path=list(path) + [node["val"]], op=f"insert({v})",
                  note=f"{v} < {node['val']} → 往左走", at=node["val"], dir="left")
            if node["left"] is None:
                node["left"] = {"val": None, "left": None, "right": None}
            ins(node["left"], v, path + [node["val"]])
        elif v > node["val"]:
            t.add(path=list(path) + [node["val"]], op=f"insert({v})",
                  note=f"{v} > {node['val']} → 往右走", at=node["val"], dir="right")
            if node["right"] is None:
                node["right"] = {"val": None, "left": None, "right": None}
            ins(node["right"], v, path + [node["val"]])
        else:
            t.add(path=list(path) + [node["val"]], op=f"insert({v})", note=f"{v} 已存在，不重复插入")

    for v in values:
        ins(tree, v, [])
    found = None
    if target is not None:
        node, path = tree, []
        while node and node["val"] is not None:
            t.bump("compare")
            path.append(node["val"])
            if target == node["val"]:
                found = path[:]
                t.add(path=path, op=f"search({target})", note=f"命中！{target} 在第 {len(path)} 层")
                break
            t.add(path=path, op=f"search({target})",
                  note=f"{target} {'<' if target < node['val'] else '>'} {node['val']} → 往{'左' if target < node['val'] else '右'}走")
            node = node["left"] if target < node["val"] else node["right"]
        if found is None:
            t.add(path=path, op=f"search({target})", note=f"走到空结点，{target} 不在树中")
    flat = _flatten_bst(tree)
    return t.out(name="二叉搜索树", nodes=flat["nodes"], pos=flat["pos"], found=found, target=target)


def _flatten_bst(tree):
    """把 BST 拉成带坐标的节点列表（中序位置决定 x，深度决定 y）。"""
    nodes, order = [], []

    def inorder(node, depth, lo, hi):
        if node is None or node["val"] is None:
            return
        mid = (lo + hi) / 2
        inorder(node["left"], depth + 1, lo, mid)
        nid = f"b{node['val']}"
        order.append((nid, node, mid, depth))
        inorder(node["right"], depth + 1, mid, hi)

    n_est = 2 ** 5
    inorder(tree, 0, 0.0, float(n_est))

    def depth_of(node):
        d, st = 0, tree
        while st and st["val"] is not None and st is not node:
            st = st["left"] if node["val"] < st["val"] else st["right"]
            d += 1
        return d
    maxd = max([depth_of(n) for _, n, _, _ in order], default=1) or 1
    xs = [x for _, _, x, _ in order]
    x0, x1 = (min(xs), max(xs)) if xs else (0, 1)
    for nid, node, x, _ in order:
        depth = depth_of(node)
        nx = (x - x0) / (x1 - x0) if x1 > x0 else 0.5
        nodes.append({"id": nid, "val": node["val"], "x": round(nx, 4),
                      "y": round(1 - depth / (maxd + 1), 4), "depth": depth})
    byval = {n["val"]: n["id"] for n in nodes}
    for nid, node, _, _ in order:
        for side in ("left", "right"):
            ch = node[side]
            if ch and ch["val"] is not None:
                p = [n for n in nodes if n["id"] == nid][0]
                p.setdefault("edges", []).append(byval[ch["val"]])
    pos = {n["id"]: (n["x"], n["y"]) for n in nodes}
    return {"nodes": nodes, "pos": pos}


def heap_demo(push_values, pop_count=0):
    """最小堆的插入（上浮）与弹出（下沉），逐步记录数组状态。"""
    h, t = [], Trace()

    def snap(note, **kw):
        d = {"heap": list(h), "note": note}
        d.update(kw)
        return d

    t.add(**snap("初始为空堆（用数组存储：父 i → 子 2i+1 / 2i+2）"))
    for v in push_values:
        h.append(v)
        i = len(h) - 1
        t.add(**snap(f"插入 {v} 到数组末尾", hi=[i]))
        while i > 0:
            p = (i - 1) // 2
            t.bump("compare")
            if h[p] > h[i]:
                h[p], h[i] = h[i], h[p]
                t.bump("swap")
                t.add(**snap(f"{h[i]} < 父 {h[p]} → 交换（上浮）", hi=[i, p], swap=[i, p]))
                i = p
            else:
                t.add(**snap(f"{h[i]} ≥ 父 {h[p]} → 上浮停止", hi=[i, p]))
                break
    popped = []
    for _ in range(pop_count):
        if not h:
            break
        top = h[0]
        popped.append(top)
        last = h.pop()                      # 先摘掉数组末尾
        t.add(**snap(f"弹出堆顶最小值 {top}", pop=top))
        if h:                               # 还有剩余元素才需要下沉
            h[0] = last                     # 用末尾元素**顶掉**被弹出的堆顶
            i = 0
            t.add(**snap(f"把末尾 {last} 放到堆顶，再下沉", hi=[0]))
            while True:
                l, r, sm = 2 * i + 1, 2 * i + 2, i
                if l < len(h) and h[l] < h[sm]:
                    sm = l
                if r < len(h) and h[r] < h[sm]:
                    sm = r
                if sm == i:
                    break
                h[i], h[sm] = h[sm], h[i]
                t.bump("swap")
                t.add(**snap(f"与更小的孩子交换（下沉）", hi=[i, sm], swap=[i, sm]))
                i = sm
    return t.out(name="二叉堆（最小堆）", popped=popped)


def hash_table_demo(keys, size=7):
    """哈希表：h(k)=k mod size，链地址法解决冲突。"""
    t = Trace()
    buckets = [[] for _ in range(size)]
    t.add(buckets=[list(b) for b in buckets], note=f"建 {size} 个桶，哈希函数 h(k) = k mod {size}")
    for k in keys:
        idx = k % size
        collision = len(buckets[idx]) > 0
        buckets[idx].append(k)
        t.bump("collision" if collision else "insert")
        t.add(buckets=[list(b) for b in buckets], hi=[idx], key=k, h=idx,
              note=f"h({k}) = {k} mod {size} = {idx}" + ("（冲突 → 挂到该桶链表尾部）" if collision else "（空桶，直接放入）"))
    return t.out(name="哈希表（链地址法）", size=size)


# ==================== 6) 图算法 ====================
def _circular_layout(ids, r=1.0):
    n = max(1, len(ids))
    pos = {}
    for i, v in enumerate(ids):
        ang = 2 * math.pi * i / n - math.pi / 2
        pos[v] = (round(0.5 + r * 0.44 * math.cos(ang), 4), round(0.5 + r * 0.44 * math.sin(ang), 4))
    return pos


def _adj(nodes, edges, directed=False):
    g = {v: [] for v in nodes}
    for e in edges:
        u, v = e[0], e[1]
        w = e[2] if len(e) > 2 else 1
        g[u].append((v, w))
        if not directed:
            g[v].append((u, w))
    return g


def bfs(nodes, edges, start):
    g, t = _adj(nodes, edges), Trace()
    pos = _circular_layout(nodes)
    seen, order, q = {start}, [], [start]
    t.add(pos=pos, edges=[list(e) for e in edges], visited=[], queue=list(q), note=f"从 {start} 出发，把起点入队")
    while q:
        u = q.pop(0)
        order.append(u)
        t.add(pos=pos, edges=[list(e) for e in edges], visited=list(order), queue=list(q), cur=u,
              note=f"出队 {u}，访问它（第 {len(order)} 个）")
        for v, _ in g[u]:
            if v not in seen:
                seen.add(v)
                q.append(v)
                t.add(pos=pos, edges=[list(e) for e in edges], visited=list(order), queue=list(q), cur=u, push=v,
                      note=f"发现邻居 {v}（第一次遇到）→ 入队")
    return t.out(name="广度优先搜索 BFS", order=order, pos=pos, edges=[list(e) for e in edges])


def dfs(nodes, edges, start):
    g, t = _adj(nodes, edges), Trace()
    pos = _circular_layout(nodes)
    visited, order = [], []
    t.add(pos=pos, edges=[list(e) for e in edges], visited=[], stack=[start], note=f"从 {start} 出发（用栈模拟递归）")

    def rec(u, depth):
        visited.append(u)
        order.append(u)
        t.add(pos=pos, edges=[list(e) for e in edges], visited=list(order), cur=u, depth=depth,
              note=f"访问 {u}（第 {len(order)} 个，深度 {depth}）")
        for v, _ in g[u]:
            if v not in visited:
                t.add(pos=pos, edges=[list(e) for e in edges], visited=list(order), cur=u, push=v,
                      note=f"从 {u} 深入邻居 {v}")
                rec(v, depth + 1)
                t.add(pos=pos, edges=[list(e) for e in edges], visited=list(order), cur=u,
                      note=f"从 {v} 回溯到 {u}")
    # 用迭代避免深递归
    stack = [(start, 0, iter(g[start]))]
    visited.append(start); order.append(start)
    t.add(pos=pos, edges=[list(e) for e in edges], visited=list(order), cur=start, depth=0, note=f"访问 {start}")
    while stack:
        u, depth, it = stack[-1]
        nxt = None
        for v, _ in it:
            if v not in visited:
                nxt = v
                break
        if nxt is None:
            stack.pop()
            if stack:
                t.add(pos=pos, edges=[list(e) for e in edges], visited=list(order), cur=u,
                      note=f"{u} 的邻居都已访问 → 回溯")
            continue
        visited.append(nxt); order.append(nxt)
        t.add(pos=pos, edges=[list(e) for e in edges], visited=list(order), cur=nxt, depth=depth + 1,
              note=f"深入 {nxt}（第 {len(order)} 个）")
        stack.append((nxt, depth + 1, iter(g[nxt])))
    return t.out(name="深度优先搜索 DFS", order=order, pos=pos, edges=[list(e) for e in edges])


def dijkstra(nodes, edges, start):
    g, t = _adj(nodes, edges), Trace()
    pos = _circular_layout(nodes)
    INF = float("inf")
    dist = {v: INF for v in nodes}
    dist[start] = 0
    done, order = set(), []
    t.add(pos=pos, edges=[list(e) for e in edges], dist={k: (None if v == INF else v) for k, v in dist.items()},
          done=[], note=f"初始化：dist[{start}]=0，其余为 ∞")
    while len(done) < len(nodes):
        u = min((v for v in nodes if v not in done), key=lambda v: dist[v], default=None)
        if u is None or dist[u] == INF:
            break
        done.add(u); order.append(u)
        t.add(pos=pos, edges=[list(e) for e in edges], dist={k: (None if v == INF else v) for k, v in dist.items()},
              done=list(order), cur=u, note=f"选出未确定中 dist 最小的 {u}（dist={dist[u]}），标记为已确定")
        for v, w in g[u]:
            if v in done:
                continue
            nd = dist[u] + w
            t.bump("relax")
            if nd < dist[v]:
                dist[v] = nd
                t.add(pos=pos, edges=[list(e) for e in edges],
                      dist={k: (None if x == INF else x) for k, x in dist.items()},
                      done=list(order), cur=u, relax=v, edge=[u, v, w],
                      note=f"松弛：dist[{v}] 更新为 {nd}（经 {u}，边权 {w}）")
            else:
                t.add(pos=pos, edges=[list(e) for e in edges],
                      dist={k: (None if x == INF else x) for k, x in dist.items()},
                      done=list(order), cur=u, edge=[u, v, w],
                      note=f"经 {u} 到 {v} 更远（{nd} ≥ {dist[v]}），保持原值")
    return t.out(name="Dijkstra 最短路径", dist={k: (None if v == INF else v) for k, v in dist.items()},
                 pos=pos, edges=[list(e) for e in edges])


def prim_mst(nodes, edges):
    g, t = _adj(nodes, edges), Trace()
    pos = _circular_layout(nodes)
    start = nodes[0]
    in_tree = {start}
    chosen = []
    t.add(pos=pos, edges=[list(e) for e in edges], inTree=list(in_tree), chosen=[],
          note=f"从 {start} 开始，树中只有它")
    while len(in_tree) < len(nodes):
        best = None
        for u in in_tree:
            for v, w in g[u]:
                if v not in in_tree and (best is None or w < best[2]):
                    best = (u, v, w)
        if best is None:
            break
        u, v, w = best
        chosen.append([u, v, w])
        in_tree.add(v)
        t.bump("edge")
        t.add(pos=pos, edges=[list(e) for e in edges], inTree=list(in_tree), chosen=[list(c) for c in chosen],
              add=[u, v, w], note=f"选连接树内外的最小边 {u}—{v}（权 {w}），把 {v} 并进来")
    return t.out(name="最小生成树（Prim）", pos=pos, edges=[list(e) for e in edges],
                 total=sum(c[2] for c in chosen), chosen=[list(c) for c in chosen])


# ==================== 7) 计算原理：进制 / 位运算 / 编码 ====================
def base_convert(value, base):
    """把十进制 value 转成 base 进制，逐步记录"除基取余、逆序排列"。"""
    assert 2 <= base <= 16
    digits = "0123456789ABCDEF"
    t = Trace()
    n = value
    rems = []
    t.add(step="start", note=f"把十进制 {value} 转成 {base} 进制：不断除以 {base}，记下余数")
    while n > 0:
        q, r = divmod(n, base)
        rems.append(r)
        t.add(step="div", n=n, q=q, r=r, digits=digits[r], rems=list(rems),
              note=f"{n} ÷ {base} = {q} 余 {r}（记为 {digits[r]}）")
        n = q
    out = "".join(digits[r] for r in reversed(rems)) or "0"
    t.add(step="done", result=out, rems=list(rems), note=f"余数从下往上读 → {value}₁₀ = {out}₍{base}₎")
    return t.out(name=f"{base} 进制转换", result=out, rems=rems, base=base, value=value)


def bitwise_ops(a, b, width=8):
    """与/或/异或/取反/左右移 的逐位真值表。"""
    def fmt(x):
        return format(x & ((1 << width) - 1), f"0{width}b")
    rows = [
        {"op": "A",       "expr": f"{a}",        "bin": fmt(a), "dec": a},
        {"op": "B",       "expr": f"{b}",        "bin": fmt(b), "dec": b},
        {"op": "A AND B", "expr": f"{a} & {b}",  "bin": fmt(a & b), "dec": a & b},
        {"op": "A OR B",  "expr": f"{a} | {b}",  "bin": fmt(a | b), "dec": a | b},
        {"op": "A XOR B", "expr": f"{a} ^ {b}",  "bin": fmt(a ^ b), "dec": a ^ b},
        {"op": "NOT A",   "expr": f"~{a}",       "bin": fmt(~a), "dec": ~a},
        {"op": "A << 1",  "expr": f"{a} << 1",   "bin": fmt(a << 1), "dec": a << 1},
        {"op": "A >> 1",  "expr": f"{a} >> 1",   "bin": fmt(a >> 1), "dec": a >> 1},
    ]
    return {"name": "位运算", "width": width, "a": a, "b": b, "rows": rows,
            "a_bits": [int(c) for c in fmt(a)], "b_bits": [int(c) for c in fmt(b)],
            "and_bits": [int(c) for c in fmt(a & b)], "or_bits": [int(c) for c in fmt(a | b)],
            "xor_bits": [int(c) for c in fmt(a ^ b)]}


def encode_char(ch):
    """字符 → 码点 → UTF-8 字节序列（含 ASCII 的兼容性）。"""
    cp = ord(ch)
    if cp < 0x80:
        nbytes, enc = 1, bytes([cp])
    elif cp < 0x800:
        nbytes = 2
        enc = bytes([0xC0 | (cp >> 6), 0x80 | (cp & 0x3F)])
    elif cp < 0x10000:
        nbytes = 3
        enc = bytes([0xE0 | (cp >> 12), 0x80 | ((cp >> 6) & 0x3F), 0x80 | (cp & 0x3F)])
    else:
        nbytes = 4
        enc = bytes([0xF0 | (cp >> 18), 0x80 | ((cp >> 12) & 0x3F),
                     0x80 | ((cp >> 6) & 0x3F), 0x80 | (cp & 0x3F)])
    return {"char": ch, "codepoint": cp, "hex": f"U+{cp:04X}", "bytes": list(enc),
            "bytes_hex": " ".join(f"{b:02X}" for b in enc), "nbytes": nbytes,
            "utf8_bits": " ".join(format(b, "08b") for b in enc)}


# ==================== 8) 算法思想：递归 / 贪心 / DP ====================
def fib_recursive_calls(n):
    """斐波那契朴素递归：记录调用树与重复子问题的次数（说明为什么慢）。"""
    t = Trace()
    calls = []
    counter = {"n": 0}

    def fib(x, path):
        counter["n"] += 1
        calls.append(x)
        t.add(node=f"f{x}", path=list(path), calls=len(calls),
              note=f"调用 fib({x})（第 {len(calls)} 次函数调用）")
        if x <= 1:
            return x
        return fib(x - 1, path + [x]) + fib(x - 2, path + [x])

    result = fib(n, [])
    repeat = {}
    for x in calls:
        repeat[x] = repeat.get(x, 0) + 1
    return t.out(name="递归：斐波那契（朴素）", result=result, calls=len(calls),
                 repeat=repeat, n=n, complex="O(2ⁿ) 次调用")


def fib_dp(n):
    """斐波那契动态规划：自底向上填表，对比朴素递归的调用次数。"""
    t = Trace()
    if n <= 1:
        return t.out(name="动态规划：斐波那契", table=[n], result=n, n=n)
    dp = [0] * (n + 1)
    dp[1] = 1
    t.add(table=list(dp), hi=[0, 1], note="边界：f(0)=0，f(1)=1")
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
        t.bump("add")
        t.add(table=list(dp), hi=[i], from_=[i - 1, i - 2],
              note=f"f({i}) = f({i-1}) + f({i-2}) = {dp[i-1]} + {dp[i-2]} = {dp[i]}")
    naive = fib_recursive_calls(n)
    return t.out(name="动态规划：斐波那契", table=list(dp), result=dp[n], n=n,
                 naive_calls=naive["calls"], complex="O(n)")


def knapsack_dp(weights, values, capacity):
    """0-1 背包：二维 DP 表逐格填写。"""
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    t = Trace()
    t.add(table=[row[:] for row in dp], note=f"{n} 件物品、背包容量 {capacity}：dp[i][c] = 只用前 i 件、容量 c 时的最大价值")
    for i in range(1, n + 1):
        w, v = weights[i - 1], values[i - 1]
        for c in range(capacity + 1):
            if w <= c:
                dp[i][c] = max(dp[i - 1][c], dp[i - 1][c - w] + v)
                take = dp[i - 1][c - w] + v > dp[i - 1][c]
                t.add(table=[row[:] for row in dp], hi=[i, c],
                      note=f"物品{i}(重{w},值{v})：不拿={dp[i-1][c]}，拿={dp[i-1][c-w]}+{v} → 取较大者 {dp[i][c]}"
                           + ("（拿）" if take else "（不拿）"))
            else:
                dp[i][c] = dp[i - 1][c]
                t.add(table=[row[:] for row in dp], hi=[i, c],
                      note=f"物品{i} 重 {w} > 容量 {c} → 装不下，沿用上一行 {dp[i][c]}")
    return t.out(name="0-1 背包（动态规划）", table=[row[:] for row in dp], result=dp[n][capacity],
                 weights=weights, values=values, capacity=capacity)


def greedy_coins(coins, amount):
    """贪心找零：每次拿不超过剩余的最大面额。演示"贪心有时不是最优"。"""
    t = Trace()
    coins = sorted(coins, reverse=True)
    left, used = amount, []
    t.add(left=left, used=[], coins=coins, note=f"面额 {coins}，要凑 {amount}：贪心地每次拿最大的")
    for c in coins:
        cnt = left // c
        if cnt:
            used.append([c, cnt])
            for _ in range(cnt):
                left -= c
                t.add(left=left, used=[list(u) for u in used], take=c, note=f"拿一个 {c}，还剩 {left}")
        if left == 0:
            break
    return t.out(name="贪心算法：找零", coins=coins, amount=amount, used=used,
                 ok=(left == 0), remain=left,
                 count=sum(u[1] for u in used))


def greedy_interval(tasks):
    """区间调度：按结束时间贪心选择最多不冲突任务。"""
    t = Trace()
    ts = sorted(tasks, key=lambda x: x[1])
    chosen, last_end = [], None
    t.add(tasks=[list(x) for x in tasks], sorted_=[list(x) for x in ts], chosen=[],
          note="按「结束时间」从小到大排序")
    for s, e in ts:
        if last_end is None or s >= last_end:
            chosen.append([s, e])
            last_end = e
            t.add(tasks=[list(x) for x in tasks], sorted_=[list(x) for x in ts],
                  chosen=[list(c) for c in chosen], hi=[s, e],
                  note=f"[{s},{e}) 与已选不冲突 → 选它")
        else:
            t.add(tasks=[list(x) for x in tasks], sorted_=[list(x) for x in ts],
                  chosen=[list(c) for c in chosen], hi=[s, e],
                  note=f"[{s},{e}) 与已选冲突（上一个结束于 {last_end}）→ 跳过")
    return t.out(name="贪心算法：区间调度", chosen=[list(c) for c in chosen],
                 count=len(chosen), sorted_=[list(x) for x in ts])


# ==================== 自检 ====================
if __name__ == "__main__":
    ARR = [5, 2, 9, 1, 7, 3]

    # 排序：结果正确 + 步骤非空
    for fn, exp in [(bubble_sort, sorted(ARR)), (selection_sort, sorted(ARR)),
                    (insertion_sort, sorted(ARR)), (merge_sort, sorted(ARR)),
                    (quick_sort, sorted(ARR))]:
        r = fn(ARR)
        assert r["steps"][-1]["a"] == exp, f"{fn.__name__} 结果错：{r['steps'][-1]['a']}"
        assert len(r["steps"]) > 5
    assert bubble_sort([5, 4, 3, 2, 1])["counters"]["compare"] == 10, "逆序时冒泡比较次数应为 n(n-1)/2 = 10"
    assert insertion_sort([1, 2, 3, 4, 5])["counters"].get("compare", 0) == 4, "近乎有序时比较次数少"

    # 查找
    r = linear_search([4, 8, 15, 16], 15)
    assert r["pos"] == 2
    r = binary_search(list(range(0, 64, 2)), 40)
    assert r["pos"] == 20
    assert binary_search(list(range(0, 64, 2)), 41)["pos"] == -1
    # 二分查找的比较次数应 ≈ log2(n)
    assert binary_search(list(range(64)), 63)["counters"]["compare"] <= 7

    # 复杂度
    assert ops_at("n2", 1000)["ops"] == 1_000_000
    assert max_n_for_budget("n2", 10**8)["max_n"] == 10000
    assert max_n_for_budget("2n", 10**8)["max_n"] < 30, "指数级能处理的 n 应该很小"
    assert growth_values(["n", "n2"], 4)["n2"]["values"][4] == 16

    # 栈/队列
    r = stack_demo([("push", 1), ("push", 2), ("pop",), ("push", 3)])
    assert r["steps"][-1]["stack"] == [1, 3], r["steps"][-1]["stack"]
    r = queue_demo([("enq", 1), ("enq", 2), ("deq",), ("enq", 3)])
    assert r["steps"][-1]["queue"] == [2, 3]

    # 链表：按下标插入/删除，且指针确实重连了
    r = linked_list_demo([10, 20, 30], insert_after=0, value=15, delete_index=1)
    assert len(r["steps"]) == 4, [s["note"] for s in r["steps"]]
    last = {n["id"]: n for n in r["steps"][-1]["nodes"]}
    assert last["n0"]["next"] == "x3" and last["x3"]["next"] == "n2" \
        and r["steps"][-1]["head"] == "n0", last
    # 删表头 → head 后移
    r = linked_list_demo([10, 20, 30], delete_index=0)
    assert r["steps"][-1]["head"] == "n1", r["steps"][-1]["head"]

    # 二叉树遍历
    bt = binary_tree_traversals([1, 2, 3, 4, 5, 6, 7])
    assert bt["orders"]["pre"] == [0, 1, 3, 4, 2, 5, 6]
    assert bt["orders"]["in"] == [3, 1, 4, 0, 5, 2, 6]
    assert bt["orders"]["post"] == [3, 4, 1, 5, 6, 2, 0]
    assert len(bt["nodes"]) == 7

    # BST
    r = bst_insert([50, 30, 70, 20, 40, 60, 80], target=40)
    assert len(r["nodes"]) == 7
    assert r["found"] == [50, 30, 40]
    assert bst_insert([50, 30, 70], target=99)["found"] is None

    # 堆
    r = heap_demo([5, 3, 8, 1, 9, 2], pop_count=2)
    assert r["popped"] == [1, 2], r["popped"]

    # 哈希
    r = hash_table_demo([15, 22, 8, 29], size=7)
    # 15=2·7+1, 22=3·7+1, 8=1·7+1, 29=4·7+1 —— 四个键全都落在 1 号桶（链地址法）
    assert r["steps"][-1]["buckets"][1] == [15, 22, 8, 29], r["steps"][-1]["buckets"]

    # 图
    NODES = ["A", "B", "C", "D", "E"]
    EDGES = [["A", "B", 4], ["A", "C", 1], ["C", "B", 2], ["B", "D", 5], ["C", "D", 8], ["D", "E", 3]]
    assert bfs(NODES, EDGES, "A")["order"][0] == "A"
    assert len(bfs(NODES, EDGES, "A")["order"]) == 5
    assert len(dfs(NODES, EDGES, "A")["order"]) == 5
    dj = dijkstra(NODES, EDGES, "A")
    assert dj["dist"]["D"] == 8, dj["dist"]      # A→C(1)→B(2)→D(5) = 8
    assert dj["dist"]["E"] == 11
    mst = prim_mst(NODES, EDGES)
    assert mst["total"] == 1 + 2 + 5 + 3, mst["total"]   # A-C(1) C-B(2) B-D(5) D-E(3) = 11

    # 进制
    r = base_convert(45, 2)
    assert r["result"] == "101101", r["result"]
    assert base_convert(255, 16)["result"] == "FF"
    assert base_convert(1000, 8)["result"] == "1750"

    # 位运算
    bw = bitwise_ops(12, 10, width=8)
    assert bw["a_bits"] == [0, 0, 0, 0, 1, 1, 0, 0]
    d = {row["op"]: row["dec"] for row in bw["rows"]}
    assert d["A AND B"] == 8 and d["A OR B"] == 14 and d["A XOR B"] == 6

    # 编码
    e = encode_char("A")
    assert e["codepoint"] == 65 and e["nbytes"] == 1 and e["bytes_hex"] == "41"
    e = encode_char("中")
    assert e["codepoint"] == 0x4E2D and e["nbytes"] == 3 and e["bytes_hex"] == "E4 B8 AD"
    assert encode_char("😀")["nbytes"] == 4

    # 递归 / DP
    fr = fib_recursive_calls(6)
    assert fr["result"] == 8 and fr["calls"] == 25, (fr["result"], fr["calls"])
    fd = fib_dp(30)
    assert fd["result"] == 832040
    assert fd["naive_calls"] > 100000, "朴素递归调用次数应爆炸"
    kn = knapsack_dp([2, 3, 4, 5], [3, 4, 5, 6], 5)
    assert kn["result"] == 7, kn["result"]        # 2+3 重 5，值 3+4=7

    # 贪心
    gc = greedy_coins([1, 5, 10, 25], 63)
    assert gc["count"] == 6 and gc["ok"]
    assert greedy_coins([1, 3, 4], 6)["ok"], "面额 1/3/4 凑 6：贪心得 4+1+1（3 枚）"
    gi = greedy_interval([[1, 3], [2, 5], [4, 7], [6, 9], [8, 10]])
    assert gi["count"] == 3, gi["count"]

    print("cs_kernel self-check OK ✓")
    print(f"  冒泡排序 {ARR}：比较 {bubble_sort(ARR)['counters']['compare']} 次、交换 {bubble_sort(ARR)['counters']['swap']} 次")
    print(f"  二分查找 0..126 中找 63：比较 {binary_search(list(range(128)), 63)['counters']['compare']} 次")
    print(f"  复杂度：n=1000 时 O(n²)={ops_at('n2',1000)['ops']:,} 次；预算 10⁸ 下 O(2ⁿ) 最多 n={max_n_for_budget('2n',10**8)['max_n']}")
    print(f"  Dijkstra：A 到各点 {dj['dist']}；最小生成树总权 {mst['total']}")
    print(f"  十进制 45 → 二进制 {base_convert(45,2)['result']}")
    print(f"  fib(30)：朴素递归 {fd['naive_calls']:,} 次调用 vs 动态规划 {30} 次加法")
    print(f"  0-1 背包（重 [2,3,4,5]、值 [3,4,5,6]、容量 5）最大价值 {kn['result']}")
