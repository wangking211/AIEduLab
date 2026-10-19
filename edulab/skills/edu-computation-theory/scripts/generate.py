#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「计算理论」交互网页。

自动机与图灵机都是**真的逐步跑**（每一步都留下快照供滑块回放）；
子集构造**真的算 ε-闭包**；停机问题的矛盾表**真的构造**。

覆盖七个题型（6.045 的入门部分）：
  dfa          DFA 逐步模拟
  subset       NFA → DFA 子集构造法
  grammar      上下文无关文法与推导树
  pumping      泵引理（{aⁿbⁿ} 不是正则语言）
  turing       图灵机纸带模拟（二进制加一）
  halting      停机问题的对角线法
  pnp          P / NP 与复杂度增长

依赖 sympy：
    python scripts/generate.py <题型key> [输出.html]
    python scripts/generate.py list
    python scripts/generate.py all <输出目录>
    python scripts/generate.py random [seed] [输出.html]
"""

import math
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PLACEHOLDER = "__LESSON_DATA__"

sys.path.insert(0, str(SKILL_DIR.parent.parent / "shared"))
sys.path.insert(0, str(SKILL_DIR / "lib"))

import comptheory_kernel as K                  # noqa: E402
from skillkit import cli                       # noqa: E402

_MATHENV = {
    "sqrt": math.sqrt, "abs": abs, "min": min, "max": max, "pow": pow,
    "sign": lambda v: (v > 0) - (v < 0), "floor": math.floor, "ceil": math.ceil,
    "PI": math.pi, "E": math.e,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "exp": math.exp, "log": math.log,
}


def _jseval(expr, **env):
    return eval(expr.replace("^", "**"), {"__builtins__": {}}, {**_MATHENV, **env})


def _agree(label, expr, want, tol=1e-9, **env):
    got = _jseval(expr, **env)
    d = abs(float(got) - float(want))
    if d > tol * max(1.0, abs(float(want))):
        raise AssertionError(
            f"读数表达式与内核不一致（{label}）：\n"
            f"  表达式 {expr!r}\n  按表达式算 = {got!r}\n  内核给出   = {want!r}")


def ro(rid, label, expr, digits=4, unit=None):
    d = {"id": rid, "label": label, "type": "expr", "expr": expr, "digits": digits}
    if unit:
        d["unit"] = unit
    return d


def ro_status(rid, label, expr, rhs=0, op="==", ok="成立", bad="不成立"):
    return {"id": rid, "label": label, "type": "status", "expr": expr,
            "rhs": rhs, "op": op, "okText": ok, "badText": bad}


def arr_str(vals):
    """逗号分隔的 0/1 串（**不含方括号** —— 调用方自己加，别重复套）。"""
    return ",".join(("1" if v else "0") for v in vals)


# =====================================================================
# 1) DFA 逐步模拟
# =====================================================================
DFA_DELTA = {("q0", "0"): "q0", ("q0", "1"): "q1",
             ("q1", "0"): "q1", ("q1", "1"): "q0"}
DFA_START, DFA_ACC = "q0", {"q0"}
DFA_INPUT = "11010010"   # 1 的个数为 4（偶数）⇒ 应被接受
DFA_NAMES = ["q₀（偶数）", "q₁（奇数）"]
DFA_IDX = {"q0": 0, "q1": 1}          # 状态名 → 显示下标（DFA_NAMES 是显示名，不能用 index）
DFA_RUN = K.dfa_run(DFA_DELTA, DFA_START, DFA_ACC, DFA_INPUT)
DFA_STEPS = [t[1] for t in DFA_RUN["trace"]]
EXPR_DFA_STATE = "[" + ",".join(str(DFA_IDX[s]) for s in DFA_STEPS) + "][step]"
EXPR_DFA_OK = "[" + arr_str([s in DFA_ACC for s in DFA_STEPS]) + "][step]"
EXPR_DFA_DONE = f"step"


def build_dfa() -> dict:
    assert DFA_RUN["accepted"] is True, f"{DFA_INPUT} 有 {DFA_INPUT.count(chr(49))} 个 1（偶数）⇒ 应被接受"
    assert len(DFA_STEPS) == len(DFA_INPUT) + 1
    for i, s in enumerate(DFA_STEPS):
        _agree(f"第 {i} 步的状态", EXPR_DFA_STATE, float(DFA_IDX[s]), tol=1e-12, step=i)
    # 语言：1 的个数为偶数
    for s, want in (("", True), ("1", False), ("11", True), ("1010", True), ("1101", False)):
        assert K.dfa_run(DFA_DELTA, DFA_START, DFA_ACC, s)["accepted"] is want

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "statemachine", "step": "step",
                  "nodes": [[3.0, 3.05], [7.0, 3.05]],
                  "edges": [[0, 0, "0"], [1, 1, "0"], [0, 1, "1"], [1, 0, "1"]],
                  "names": DFA_NAMES, "accept": [0],
                  "input": DFA_INPUT, "trace": [[t[0], DFA_IDX[t[1]], t[2]] for t in DFA_RUN["trace"]],
                  "caption": "黄圈 = 当前状态；黄箭头 = 刚刚走过的转移；绿圈 = 接受状态"},
        "param": {"name": "step", "label": "已读入的字符数", "min": 0, "max": len(DFA_INPUT),
                  "step": 1, "value": 0, "unit": "", "standard": 0,
                  "ticks": ["0 (未开始)", "4", "8 (读完)"]},
        "readouts": [
            ro("read", "已读入的字符数", "step", 0),
            ro("st", "当前状态编号（0=偶数个1，1=奇数个1）", EXPR_DFA_STATE, 0),
            ro("len", "输入串长度", f"{len(DFA_INPUT)}", 0),
            ro("acc", "当前是否在接受状态（1 = 是）", EXPR_DFA_OK, 0),
            ro_status("done", "是否已读完整串", "step", len(DFA_INPUT) - 1, ">",
                      "已读完整串：判定已完成", "还没读完"),
        ],
        "constant": {"of": "len", "label": "输入串长度恒为 8 —— 拖滑块逐字符回放"},
    }
    lesson = {
        "language": "zh-CN", "title": "DFA：确定型有限自动机",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>设计一个 DFA，判定二进制串中 $1$ 的个数是否为偶数。"
            "输入串为 $11010011$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>需要几个状态？各自代表什么？</li>"
            "<li>逐步模拟，最后接受还是拒绝？</li>"
            "<li>「确定型」体现在哪里？</li></ol>"),
        "answerLabel": "读完整串后",
        "answer": f"停在 $q_0$（偶数个 1）⇒ **接受**"
                  f"（该串有 {DFA_INPUT.count('1')} 个 1）",
    }
    steps = [
        {"title": "状态就是「记住的信息」",
         "content": ("<p>要判断「$1$ 的个数是否为偶数」，我们**只需要记住一个 bit**："
                     "到目前为止 $1$ 的个数是奇数还是偶数。</p>"
                     "<p>于是两个状态就够：$q_0$（偶数）、$q_1$（奇数）。</p>"
                     "<p>转移很自然：读 $0$ 不改变奇偶性（自环）；读 $1$ 翻转奇偶性（在两状态间来回）。</p>"
                     "<p>这就是有限自动机的本质：**用有限个状态记住有限的信息**。</p>")},
        {"title": "「确定型」的含义",
         "content": ("<p>DFA 的三个「确定」：</p>"
                     "<p>· 每个状态对每个输入字符**恰好有一条**出边（不能没有、也不能有两条）；</p>"
                     "<p>· 没有 $\\varepsilon$ 转移；</p>"
                     "<p>· 从起点出发，给定输入串，**走出的路径唯一**。</p>"
                     "<p>所以模拟 DFA 只要跟着走就行，不需要回溯或搜索。"
                     "图上的自环（读 $0$）就是「不改变状态」的边。</p>")},
        {"title": "接受与拒绝",
         "content": ("<p>读完全部输入后，**停在接受状态就是接受，否则拒绝**。</p>"
                     "<p>$11010011$ 里有 $4$ 个 $1$（偶数），所以最后停在 $q_0$ ⇒ 接受。</p>"
                     "<p>注意：DFA 必须在**读完全串**后才给结论，中途的接受状态没有意义 —— "
                     "这一点与「读到哪里就匹配到哪里」的模式匹配不同。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 子集构造法
# =====================================================================
NFA_DELTA = {("0", "a"): {"0", "1"}, ("0", "b"): {"0"},
             ("1", "b"): {"2"}, ("2", "b"): {"3"}}
NFA_START, NFA_ACC, NFA_ALPHA = "0", {"3"}, ["a", "b"]
SUB = K.subset_construction(NFA_DELTA, NFA_START, NFA_ACC, NFA_ALPHA)
SUB_ROWS = []
for i, st in enumerate(SUB["states"]):
    a_to = SUB["delta"].get((i, "a"))
    b_to = SUB["delta"].get((i, "b"))
    SUB_ROWS.append(["{" + ",".join(sorted(st)) + "}",
                     "—" if a_to is None else "D" + str(a_to),
                     "—" if b_to is None else "D" + str(b_to)])


def build_subset() -> dict:
    assert len(SUB["states"]) == 4, f"应构造出 4 个 DFA 状态，实得 {len(SUB['states'])}"
    assert sorted(SUB["states"][0]) == ["0"]
    assert 3 in SUB["accept"] or any("3" in s for s in [SUB["states"][i] for i in SUB["accept"]])
    # 子集构造前后接受性必须一致
    dsub = dict(SUB["delta"])
    probes = ["", "a", "b", "ab", "abb", "aabb", "babb", "abbb", "abbabb", "bbabb", "aa"]
    for s in probes:
        n1 = K.nfa_run(NFA_DELTA, NFA_START, NFA_ACC, s)["accepted"]
        n2 = K.dfa_run(dsub, SUB["start"], SUB["accept"], s)["accepted"]
        assert n1 == n2, f"子集构造前后不一致：{s!r} NFA={n1} DFA={n2}"
    _agree("DFA 状态数", f"{len(SUB_ROWS)}", float(len(SUB["states"])), tol=1e-12)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "dfatable", "ri": "ri", "rows": SUB_ROWS,
                  "accept": sorted(SUB["accept"]), "nfaCount": 4,
                  "caption": "每一行是 NFA 的一个状态集合；★ 表示含接受状态"},
        "param": {"name": "ri", "label": "查看第几行（DFA 状态）", "min": 1, "max": len(SUB_ROWS),
                  "step": 1, "value": 1, "unit": "", "standard": 1,
                  "ticks": ["D0", "D1", "D2", "D3"]},
        "readouts": [
            ro("n", "DFA 状态数", f"{len(SUB_ROWS)}", 0),
            ro("acc", "DFA 接受状态个数", f"{len(SUB['accept'])}", 0),
            ro("row", "当前行号", "ri", 0),
            ro("nfa", "NFA 状态数", f"{4}", 0),
            ro_status("star", "当前行是否是接受状态", "[" + arr_str(
                [i in SUB["accept"] for i in range(len(SUB_ROWS))]) + "][ri-1]", 0.5, ">",
                "★ 含 NFA 接受状态 ⇒ DFA 的接受状态", "不含接受状态"),
        ],
        "constant": {"of": "nfa", "label": "NFA 恒为 4 个状态；构造出的 DFA 状态数由闭包决定"},
    }
    lesson = {
        "language": "zh-CN", "title": "子集构造法：NFA → DFA",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>给定识别 $(a|b)^*abb$ 的 NFA（4 个状态），用子集构造法把它转成 DFA。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>DFA 的状态是什么？</li>"
            "<li>构造出几个状态？哪些是接受状态？</li>"
            "<li>为什么 NFA 与 DFA 识别同一类语言？</li></ol>"),
        "answerLabel": "构造结果",
        "answer": f"DFA 有 {len(SUB_ROWS)} 个状态，其中 {len(SUB['accept'])} 个是接受状态",
    }
    steps = [
        {"title": "NFA 为什么「不确定」",
         "content": ("<p>NFA 允许一个状态对同一个字符有多条出边"
                     "（比如状态 $0$ 读 $a$ 可以留在 $0$，也可以去 $1$），"
                     "甚至允许 $\\varepsilon$ 转移（不读字符就换状态）。</p>"
                     "<p>所以 NFA 的「计算」是一棵**分支树**：所有可能的路径同时探索，"
                     "**只要有一条路径最终落在接受状态，就接受**。</p>"
                     "<p>本页的表里每一行就是一个「当前可能处在的状态集合」。</p>")},
        {"title": "子集构造：把集合当作新状态",
         "content": ("<p>核心想法极其简单：**NFA 的一个状态集合，就是 DFA 的一个状态**。</p>"
                     "<p>· 起点：$\\varepsilon$-闭包$(\\{0\\}) = \\{0\\}$ ⇒ DFA 的 $D_0$；</p>"
                     "<p>· 对每个 DFA 状态和每个字符，算出「从集合里任一状态出发读该字符后"
                     "能到达的集合」，再取 $\\varepsilon$-闭包 ⇒ 下一个 DFA 状态；</p>"
                     "<p>· 只要出现新集合就加进表里，直到不再产生新集合。</p>"
                     "<p>本页的 $D_0 \\sim D_3$ 就是**真的这么算出来的**，不是查表。</p>")},
        {"title": "为什么这是等价的",
         "content": ("<p>因为 DFA 的每一个状态**恰好记录了 NFA 在该前缀下所有可能的位置** —— "
                     "信息一点没丢，只是把「分支」压成了「集合」。</p>"
                     "<p>所以两者接受完全相同的串（本页自检里抽样了 11 个串逐一核对）。</p>"
                     "<p>代价是状态数可能**指数膨胀**（$n$ 个 NFA 状态最多 $2^n$ 个 DFA 状态）。"
                     "这也解释了为什么实际的正则表达式引擎常常直接用 NFA 模拟（Thompson 构造 + 并行走），"
                     "而不是先转成 DFA。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 上下文无关文法
# =====================================================================
CG_N = 4
CG_DERIV = K.cfg_derive(CG_N)
CG_TREE = K.cfg_parse_tree(CG_N)


def build_grammar() -> dict:
    for n in (0, 1, 2, 5):
        seq = K.cfg_derive(n)
        assert seq[-1] == "a" * n + "b" * n
        assert len(seq) == n + 1
    assert CG_DERIV[0] == "S" and CG_DERIV[-1] == "a" * CG_N + "b" * CG_N
    for i, s in enumerate(CG_DERIV):
        assert s.count("S") == (1 if i < len(CG_DERIV) - 1 else 0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "parsetree", "di": "di",
                  "deriv": CG_DERIV, "tree": CG_TREE, "curN": CG_N,
                  "caption": "左边是推导序列，右边是推导树（嵌套结构对应「栈」）"},
        "param": {"name": "di", "label": "推导步数", "min": 1, "max": len(CG_DERIV),
                  "step": 1, "value": 1, "unit": "", "standard": 1,
                  "ticks": ["S", "aSb", "aaSbb", "aaabbb"]},
        "readouts": [
            ro("step", "第几步（从 1 数）", "di", 0),
            ro("total", "总步数", f"{len(CG_DERIV)}", 0),
            ro("len", "当前串长度", "[" + ",".join(str(len(s)) for s in CG_DERIV) + "][di-1]", 0),
            ro("sleft", "当前串里 S 的个数", "[" + ",".join(str(s.count("S")) for s in CG_DERIV) + "][di-1]", 0),
            ro_status("done", "是否已推导完成（不含 S）",
                      "[" + ",".join(str(s.count("S")) for s in CG_DERIV) + "][di-1]",
                      0.5, "<", "推导完成：已得到终结符串", "还没推导完（还有 S）"),
        ],
        "constant": {"of": "total", "label": "推导步数恒为 n+1 —— 每步用一次 S → aSb，最后用一次 S → ε"},
    }
    lesson = {
        "language": "zh-CN", "title": "上下文无关文法与推导树",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>文法 $S \\to aSb \\mid \\varepsilon$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出它生成的语言；</li>"
            "<li>推导 $aaabbb$，并数出步数；</li>"
            "<li>为什么这个语言不是正则的？</li></ol>"),
        "answerLabel": "$n = 4$ 的推导",
        "answer": f"$S \\Rightarrow aSb \\Rightarrow aaSbb \\Rightarrow \\dots \\Rightarrow "
                  f"{CG_DERIV[-1]}$（共 {len(CG_DERIV)} 步）",
    }
    steps = [
        {"title": "文法就是「替换规则」",
         "content": ("<p>$S \\to aSb$ 的意思是：**把任意一个 $S$ 替换成 $aSb$**。</p>"
                     "<p>反复替换，最后用 $S \\to \\varepsilon$ 把 $S$ 消掉，就得到一个终结符串。</p>"
                     "<p>$n$ 次 $S \\to aSb$ 加一次 $S \\to \\varepsilon$，共 $n+1$ 步，"
                     "生成 $a^nb^n$。</p>"
                     "<p>右边那棵**推导树**把嵌套结构画了出来：每往下一层就多一对 $a$、$b$ —— "
                     "这个「嵌套」正是它能配对计数的原因。</p>")},
        {"title": "「上下文无关」是什么意思",
         "content": ("<p>指每条规则的左边**只是一个非终结符**（这里是 $S$），"
                     "不需要看它前后是什么符号。</p>"
                     "<p>对比「上下文相关」文法（如 $aSb \\to aXb$，要看左边有没有 $a$、右边有没有 $b$），"
                     "上下文无关的限制更强，但依然能描述所有程序设计语言的语法 —— "
                     "这就是为什么编译器用 CFG 来描述语法。</p>")},
        {"title": "为什么它比正则强",
         "content": ("<p>正则语言（DFA/NFA）只有**有限个状态**，"
                     "所以「记得的东西」是有限的：它没法记住「已经读了几个 $a$」。</p>"
                     "<p>而 CFG 的推导过程本质上是一台**栈**："
                     "每读一个 $a$ 就压栈，遇到 $b$ 就弹栈，栈空即配对成功。"
                     "栈可以无限深，所以能处理「$a$ 与 $b$ 数量相等」这种**计数**约束。</p>"
                     "<p>下一节的泵引理会给出严格的证明：$\\{a^nb^n\\}$ 不可能是正则语言。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 泵引理
# =====================================================================
PM_P, PM_K, PM_IMAX = 5, 2, 5
PM_SEQ = K.pumping_sequence(PM_P, PM_K, PM_IMAX)
PM_X, PM_Y, PM_Z, _, _ = K.pumping_check(PM_P, PM_K, 1)
EXPR_PM_IN = "[" + arr_str([d["in_L"] for d in PM_SEQ]) + "][pi-1]"


def build_pumping() -> dict:
    for d in PM_SEQ:
        x, y, z, s, ok = K.pumping_check(PM_P, PM_K, d["i"])
        assert s == d["s"] and ok == d["in_L"]
        assert x + y + z == "a" * PM_P + "b" * PM_P, "x+y+z 必须等于原串"
    _agree("i=1 在语言里", EXPR_PM_IN, 1.0, tol=1e-12, pi=2)
    _agree("i=0 不在语言里", EXPR_PM_IN, 0.0, tol=1e-12, pi=1)
    assert [d["in_L"] for d in PM_SEQ] == [False, True, False, False, False, False]

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "pumpstr", "pi": "pi",
                  "seq": PM_SEQ, "x": PM_X, "y": PM_Y, "z": PM_Z, "p": PM_P,
                  "caption": "把 w = aᵖbᵖ 拆成 x|y|z，把 y 重复 i 次（黄块）"},
        "param": {"name": "pi", "label": "重复次数 $i$（档位 = i+1）", "min": 1, "max": len(PM_SEQ),
                  "step": 1, "value": 2, "unit": "", "standard": 2,
                  "ticks": ["i=0", "i=1 (原串)", "i=3", "i=5"]},
        "readouts": [
            ro("i", "重复次数 $i$", "pi-1", 0),
            ro("len", "泵出后的长度", "[" + ",".join(str(len(d["s"])) for d in PM_SEQ) + "][pi-1]", 0),
            ro("inl", "是否仍在 L 中（1 = 是）", EXPR_PM_IN, 0),
            ro("p", "泵长度 $p$", f"{PM_P}", 0),
            ro_status("only", "是否只有 $i=1$ 回到原串", "abs(pi-2)", 0.5, "<",
                      "i = 1：回到原串 w（唯一在语言里的情形）", "i ≠ 1：已不在 L 中"),
        ],
        "constant": {"of": "p", "label": "泵长度 p = 5、|y| = 2 是定值 —— 拖滑块只改重复次数 i"},
    }
    lesson = {
        "language": "zh-CN", "title": "泵引理：为什么 {aⁿbⁿ} 不是正则语言",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>证明 $L = \\{a^nb^n \\mid n \\ge 0\\}$ 不是正则语言。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>陈述泵引理；</li>"
            "<li>取 $w = a^pb^p$，说明 $y$ 只能是什么；</li>"
            "<li>泵出后为什么不在 $L$ 里？</li></ol>"),
        "answerLabel": "取 $i = 2$",
        "answer": f"$xy^2z = a^{{{PM_P + PM_K}}}b^{{{PM_P}}}$ —— a 与 b 个数不等 ⇒ 不在 $L$ 中",
    }
    steps = [
        {"title": "泵引理在说什么",
         "content": ("<p>若 $L$ 是正则语言，则存在一个「泵长度」$p$，使得**任何长度 ≥ p 的串** "
                     "$w \\in L$ 都能拆成 $w = xyz$，满足</p>"
                     "<p>· $|xy| \\le p$；· $|y| \\ge 1$；· 对**一切** $i \\ge 0$，$xy^iz \\in L$。</p>"
                     "<p>直觉：DFA 只有 $p$ 个状态，读 $w$ 的前 $p$ 个字符时必然**重复经过某个状态** —— "
                     "那段「绕圈」就是 $y$，绕一次还是绕 $i$ 次，机器都回到同一状态，"
                     "所以后面的判定完全一样。</p>")},
        {"title": "为什么 y 只能是 a 的串",
         "content": ("<p>取 $w = a^pb^p$（长度 $2p \\ge p$）。由 $|xy| \\le p$ 可知 "
                     "$x$ 与 $y$ **都落在前 $p$ 个字符里**，而前 $p$ 个字符全是 $a$。</p>"
                     "<p>又 $|y| \\ge 1$，所以 $y = a^k$（$k \\ge 1$）。</p>"
                     "<p>于是 $xy^iz = a^{p-k} \\cdot a^{ki} \\cdot b^p "
                     "= a^{p+k(i-1)}b^p$。</p>")},
        {"title": "矛盾出现了",
         "content": ("<p>只要 $i \\ne 1$，指数 $p+k(i-1) \\ne p$，"
                     "于是 $a$ 与 $b$ 的个数不相等 ⇒ $xy^iz \\notin L$。</p>"
                     "<p>但泵引理要求**一切** $i$ 都在 $L$ 里 —— 矛盾！"
                     "所以 $L$ 不是正则语言 $\\blacksquare$</p>"
                     "<p>拖滑块可以看到：$i=1$ 时恰好回到 $a^5b^5$（唯一在语言里的情形），"
                     "而 $i = 0, 2, 3, 4, 5$ 全部跑出语言。这正是「正则语言没有计数器」的严格表述。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 图灵机
# =====================================================================
TM_DELTA = {
    ("q0", "0"): ("0", "R", "q0"),
    ("q0", "1"): ("1", "R", "q0"),
    ("q0", "_"): ("_", "L", "q1"),
    ("q1", "0"): ("1", "N", "qh"),
    ("q1", "1"): ("0", "L", "q1"),
    ("q1", "_"): ("1", "N", "qh"),
}
TM_INPUT = "1011"
TM_RUN = K.tm_run(TM_DELTA, "q0", {"qh"}, TM_INPUT)


def build_turing() -> dict:
    for inp, want in (("1011", "1100"), ("0", "1"), ("1", "10"), ("111", "1000"), ("100", "101")):
        r = K.tm_run(TM_DELTA, "q0", {"qh"}, inp)
        assert r["trace"][-1]["tape"].rstrip("_") == want, f"{inp}+1 应为 {want}"
        assert r["halted"]
    assert TM_RUN["trace"][0]["tape"] == TM_INPUT
    assert all(0 <= fr["head"] < len(fr["tape"]) for fr in TM_RUN["trace"])
    for a, b in zip(TM_RUN["trace"], TM_RUN["trace"][1:]):
        assert sum(1 for u, v in zip(a["tape"], b["tape"]) if u != v) <= 1

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "tape", "ti": "ti",
                  "trace": TM_RUN["trace"], "input": TM_INPUT,
                  "caption": "黄格 = 读写头所在；纸带随读写头自动延长"},
        "param": {"name": "ti", "label": "第几步（从 1 数）", "min": 1, "max": len(TM_RUN["trace"]),
                  "step": 1, "value": 1, "unit": "", "standard": 1,
                  "ticks": ["第 1 步", "中间", "停机"]},
        "readouts": [
            ro("step", "步号（从 0 数）",
               "[" + ",".join(str(fr["step"]) for fr in TM_RUN["trace"]) + "][ti-1]", 0),
            ro("head", "读写头位置",
               "[" + ",".join(str(fr["head"]) for fr in TM_RUN["trace"]) + "][ti-1]", 0),
            ro("tlen", "纸带长度",
               "[" + ",".join(str(len(fr["tape"])) for fr in TM_RUN["trace"]) + "][ti-1]", 0),
            ro("halt", "是否已停机（1 = 是）",
               "[" + arr_str([fr["halted"] for fr in TM_RUN["trace"]]) + "][ti-1]", 0),
            ro_status("fin", "是否走到最后一步", "ti", len(TM_RUN["trace"]) - 0.5, ">",
                      "已到最终快照", "还在模拟中"),
        ],
        "constant": {"of": "inp", "label": f"输入纸带恒为「{TM_INPUT}」—— 这台机器做二进制加一"},
        "scalars": [{"name": "inp", "expr": f"{len(TM_INPUT)}"}],
    }
    lesson = {
        "language": "zh-CN", "title": "图灵机：纸带上的计算",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>用一台单带图灵机实现**二进制加一**。初始纸带为 $1011$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出转移表（读符号 → 改写、移动、新状态）；</li>"
            "<li>逐步模拟，最终纸带是什么？</li>"
            "<li>为什么图灵机被视为「可计算」的定义？</li></ol>"),
        "answerLabel": "$1011 + 1$",
        "answer": f"$1011_2 = 11$，$11+1 = 12 = 1100_2$ ⇒ 纸带变成 $1100$",
    }
    steps = [
        {"title": "比自动机多了什么",
         "content": ("<p>图灵机 = **无限纸带** + **读写头** + **有限状态控制**。</p>"
                     "<p>每一步做四件事：读当前格 → 改写 → 左移/右移/不动 → 换状态。</p>"
                     "<p>与 DFA 的关键差别：纸带可以**读也可以写**，"
                     "读写头可以**来回移动**。这就让它能「记下中间结果」，"
                     "从而具备通用计算能力。</p>")},
        {"title": "这台机器怎么加一",
         "content": ("<p>二进制加一的算法：</p>"
                     "<p>· $q_0$：一直向右扫，直到遇到空格（说明到了数字末尾）；</p>"
                     "<p>· $q_1$：向左回退，把遇到的 $1$ 全部改成 $0$（进位），"
                     "遇到第一个 $0$ 就把它改成 $1$ 并**停机**；</p>"
                     "<p>· 若一路退到最左边还是 $1$（比如 $111$），"
                     "就在前面补一个 $1$（这就是 $111 + 1 = 1000$ 的情形）。</p>"
                     "<p>$1011$ 的末尾是两个 $1$，所以要进两次位："
                     "$1011 \\to 1010 \\to 1000 \\to 1100$ ✓</p>")},
        {"title": "为什么它是「可计算」的标准",
         "content": ("<p>因为**所有合理的计算模型都等价**：图灵机、$\\lambda$ 演算、"
                     "递归函数、乃至任何现代编程语言，能算的东西完全一样 —— "
                     "这就是**丘奇-图灵论题**。</p>"
                     "<p>所以「可计算」通常就定义为「存在一台图灵机能在有限步内算出」。</p>"
                     "<p>而**通用图灵机**（能读入任意图灵机的描述并模拟它）"
                     "就是现代计算机的原型 —— 你的电脑本质上就是一台通用图灵机，"
                     "只是纸带换成了内存。下一节的停机问题正是关于它。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 停机问题
# =====================================================================
HL_N = 5
HL_MAT = K.halting_matrix(HL_N)
HL_DIAG = K.diagonal_program(HL_N)
EXPR_HL_D = "[" + arr_str(HL_DIAG) + "][hi-1]"
EXPR_HL_H = "[" + arr_str([HL_MAT[i][i] for i in range(HL_N)]) + "][hi-1]"


def build_halting() -> dict:
    assert len(HL_MAT) == HL_N and all(len(r) == HL_N for r in HL_MAT)
    assert HL_DIAG == [not HL_MAT[i][i] for i in range(HL_N)]
    assert all(HL_MAT[i] != HL_DIAG for i in range(HL_N)), "D 必须与每一行都不同"
    for i in range(HL_N):
        # D(i) 必须等于 1 − H(i,i)（与对角线逐项相反）
        _agree(f"D({i}) 与 H({i},{i}) 相反", f"1-({EXPR_HL_H})", float(HL_DIAG[i]),
               tol=1e-12, hi=i + 1)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "haltmatrix", "hi": "hi",
                  "mat": HL_MAT, "diag": HL_DIAG,
                  "caption": "停 = 停机、∞ = 死循环；黄框是对角线；最下一行 D 与对角线逐项相反"},
        "param": {"name": "hi", "label": "高亮第几行", "min": 1, "max": HL_N,
                  "step": 1, "value": 1, "unit": "", "standard": 1,
                  "ticks": ["P0", "P1", "P2", "P3", "P4"]},
        "readouts": [
            ro("n", "程序（与输入）的个数", f"{HL_N}", 0),
            ro("h", "该行的对角线元素 H(i,i)（1 = 停机）", EXPR_HL_H, 0),
            ro("d", "D 在该输入上的取值（必与上者相反）", EXPR_HL_D, 0),
            ro("cnt", "表中「停机」的格子数",
               f"{sum(1 for r in HL_MAT for v in r if v)}", 0),
            ro_status("opp", "D 是否与对角线逐项相反", "abs((1-" + EXPR_HL_H + ")-(" + EXPR_HL_D + "))",
                      0.5, "<", "相反：这正是矛盾的关键", "不相反"),
        ],
        "constant": {"of": "n", "label": "表恒为 5×5 —— 关键不在规模，而在「D 与每一行都不同」"},
    }
    lesson = {
        "language": "zh-CN", "title": "停机问题与不可判定性",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>证明：不存在程序 $H(P, T)$ 能判定「程序 $P$ 在输入 $T$ 上是否停机」。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>假设 $H$ 存在，构造 $D$；</li>"
            "<li>$D$ 与表中的每一行有什么关系？</li>"
            "<li>$H(D, D)$ 该填什么？为什么两种填法都矛盾？</li></ol>"),
        "answerLabel": "结论",
        "answer": "停机问题**不可判定** —— 不存在能解它的程序",
    }
    steps = [
        {"title": "用对角线法构造反例",
         "content": ("<p>把所有程序排成一列 $P_0, P_1, P_2, \\dots$，"
                     "所有输入也排成一列 $T_0, T_1, T_2, \\dots$，"
                     "于是可以画出无穷大的表 $H(i,j)$："
                     "程序 $P_i$ 在输入 $T_j$ 上是否停机。</p>"
                     "<p>现在构造一个新程序 $D$，它在输入 $T_i$ 上：</p>"
                     "<p>**若 $H(i,i) = $ 停机，就让 $D$ 死循环；否则让 $D$ 停机。**</p>"
                     "<p>换句话说，$D$ 的第 $i$ 位**恰好与对角线相反**。"
                     "图上的粉色那一行就是它。</p>")},
        {"title": "矛盾在哪里",
         "content": ("<p>既然 $D$ 是一个程序，它就该出现在表里 —— 设它是第 $k$ 个程序 $P_k$。</p>"
                     "<p>那么看对角线上的格子 $H(k,k)$：</p>"
                     "<p>· 若填「停机」⇒ 按定义 $D$ 在 $T_k$ 上应**死循环**，矛盾；</p>"
                     "<p>· 若填「死循环」⇒ 按定义 $D$ 在 $T_k$ 上应**停机**，矛盾。</p>"
                     "<p>两种都矛盾 ⇒ **假设 $H$ 存在是错的** $\\blacksquare$</p>"
                     "<p>本页的自检里直接断言了「$D$ 与表中每一行都不同」—— "
                     "这正是矛盾的机器可验证形式。</p>")},
        {"title": "这意味着什么",
         "content": ("<p>**有些问题根本没有算法能解** —— 不是「还没想出来」，而是「原理上不存在」。</p>"
                     "<p>由此推出的著名结论：</p>"
                     "<p>· 不存在能判定两个程序是否**功能等价**的算法；</p>"
                     "<p>· 不存在能判定任意程序是否会**输出某个特定结果**的算法；</p>"
                     "<p>· 莱斯定理：程序的**任何非平凡语义性质**都不可判定。</p>"
                     "<p>实践中的意义：编译器不能替你判断「这段代码会不会死循环」，"
                     "杀毒软件也不能判断「这个程序是不是病毒」—— "
                     "它们只能做**近似**判断（保守地报可疑），这正是那些「误报」的根源。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) P / NP 与增长率
# =====================================================================
PN_NLO, PN_NHI = 1, 64
PN_COLORS = ['#34d399', '#38bdf8', '#a78bfa', '#facc15', '#f472b6', '#f87171']
PN_CURVES = [[K.growth(k, PN_NLO + (PN_NHI - PN_NLO) * j / 120) for j in range(121)]
             for k in K.GROWTH_KINDS]
PN_VMAX = 1e19
# 每个复杂度在 n = 1..64 上的值（供读数与画板共用；inf 用 1e300 代替）
PN_VALS_BY_N = [[round(K.growth(k, n), 6) if math.isfinite(K.growth(k, n)) else 1e300
                 for n in range(1, PN_NHI + 1)] for k in K.GROWTH_KINDS]
EXPR_PN_VALS = ["[" + ",".join(repr(v) for v in row) + "][nn-1]" for row in PN_VALS_BY_N]


def build_pnp() -> dict:
    for n in (4, 8, 16, 32):
        for i, k in enumerate(K.GROWTH_KINDS):
            v = K.growth(k, n)
            want = round(v, 6) if math.isfinite(v) else 1e300
            _agree(f"{k}(n={n})", EXPR_PN_VALS[i], want, tol=1e-6, nn=n)
    vals16 = [K.growth(k, 16) for k in K.GROWTH_KINDS]
    assert all(vals16[i] < vals16[i + 1] for i in range(len(vals16) - 1))

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "growthcurve", "nn": "nn",
                  "kinds": K.GROWTH_KINDS, "colors": PN_COLORS, "curves": PN_CURVES,
                  "valsByN": PN_VALS_BY_N,
                  "nlo": PN_NLO, "nhi": PN_NHI, "vmax": PN_VMAX,
                  "caption": "六条增长曲线（纵轴对数刻度）；黄虚线是当前 n"},
        "param": {"name": "nn", "label": "问题规模 $n$", "min": PN_NLO, "max": PN_NHI,
                  "step": 1, "value": 16, "unit": "", "standard": 16,
                  "ticks": ["1", "16 (题设)", "32", "64"]},
        "readouts": [
            ro("n", "问题规模 $n$", "nn", 0),
            ro("logn", "$\\log_2 n$", EXPR_PN_VALS[0], 2),
            ro("nlogn", "$n\\log_2 n$", EXPR_PN_VALS[2], 2),
            ro("n2", "$n^2$", EXPR_PN_VALS[3], 2),
            ro("2n", "$2^n$", EXPR_PN_VALS[4], 2),
            ro_status("poly", "是否是多项式时间（$n^2 \\le 10^6$）", EXPR_PN_VALS[3], 1e6, "<",
                      "多项式时间：属于 P（可行）", "已超出多项式时间的可行范围"),
        ],
        "constant": {"of": "kinds", "label": "六条曲线的类型固定；纵轴是对数刻度，否则 n! 会压平其它曲线"},
        "scalars": [{"name": "kinds", "expr": f"{len(K.GROWTH_KINDS)}"}],
    }
    lesson = {
        "language": "zh-CN", "title": "P、NP 与复杂度增长",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>六类常见复杂度：$\\log n$、$n$、$n\\log n$、$n^2$、$2^n$、$n!$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>在 $n = 16$ 时各需要多少次操作？</li>"
            "<li>哪几条属于「多项式时间」？</li>"
            "<li>为什么 $P$ 与 $NP$ 是否相等至今未解？</li></ol>"),
        "answerLabel": "$n = 16$ 时",
        "answer": f"$n^2 = 256$，$2^n = 65536$，$n! \\approx 2.09\\times10^{{13}}$",
    }
    steps = [
        {"title": "为什么要看增长而不是绝对时间",
         "content": ("<p>因为绝对时间依赖机器。**增长率**才是算法内在的性质。</p>"
                     "<p>而且增长率的影响是压倒性的：本页 $n = 64$ 时，"
                     "$n^2 = 4096$，而 $n!$ 已经超过 $10^{89}$ —— "
                     "即使每次操作只花一纳秒，也要 $10^{73}$ 年。</p>"
                     "<p>图上用**对数纵轴**正是为了让这六条线同框可见 —— "
                     "用线性轴的话，除了 $2^n$ 和 $n!$，其它四条会全部贴在地上。</p>")},
        {"title": "P 与 NP 的定义",
         "content": ("<p>· **P**：能在**多项式时间**内**解出**的问题"
                     "（$\\log n$、$n$、$n\\log n$、$n^2$、$n^3$ …）；</p>"
                     "<p>· **NP**：能在多项式时间内**验证**一个给定解是否正确的问题。</p>"
                     "<p>注意「解」与「验证」的差别：数独很难解，"
                     "但给定一个填好的答案，检查它合不合法只要扫一遍 —— "
                     "所以数独在 NP 里（很可能不在 P 里）。</p>"
                     "<p>显然 $P \\subseteq NP$（能解就能验证）。"
                     "但反过来是否成立 —— 即 **$P = NP$？** —— 至今没有答案，"
                     "它是千禧年七大问题之一，悬赏一百万美元。</p>")},
        {"title": "为什么它这么难",
         "content": ("<p>难在「证明下界」比「设计算法」难得多。"
                     "要证明 $P \\ne NP$，必须证明**任何**算法都做不到 —— "
                     "包括还没被想出来的那些。</p>"
                     "<p>目前的进展：$NP$-完全问题是 $NP$ 里「最难」的一类，"
                     "**只要其中任何一个能被多项式时间解出，就立刻有 $P = NP$**。"
                     "SAT（布尔可满足性）、旅行商、图着色都属于这一类。</p>"
                     "<p>实践含义：如果 $P = NP$，那么现在依赖「难解」的密码学（RSA 等）"
                     "会全部失效。大多数人相信 $P \\ne NP$，但没人能证明。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "dfa": build_dfa,
    "subset": build_subset,
    "grammar": build_grammar,
    "pumping": build_pumping,
    "turing": build_turing,
    "halting": build_halting,
    "pnp": build_pnp,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="计算理论 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
