#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「有机化学基础」交互网页。

全部数值由 lib/organic_kernel.py 现算，**不查表**：
同分异构体的等效氢种数用**碳骨架的自同构群轨道**算，主链与位号用**路径枚举**算。

覆盖七个题型（选择性必修三）：
  unsaturation  不饱和度 Ω
  combustion    燃烧耗氧量与产物
  formula       由燃烧产物确定分子式
  equiv_h       等效氢与一氯代物种数（自同构轨道）
  functional    官能团定量反应
  polymer       加聚/缩聚与聚合度
  mainchain     主链选择与编号（路径枚举）

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

import organic_kernel as K                    # noqa: E402
from skillkit import cli                      # noqa: E402

# =====================================================================
# 读数表达式 ↔ 内核 的对账机制
# =====================================================================

_MATHENV = {
    "sqrt": math.sqrt, "abs": abs, "min": min, "max": max, "pow": pow,
    "sign": lambda x: (x > 0) - (x < 0), "floor": math.floor, "ceil": math.ceil,
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


# =====================================================================
# 碳骨架库（输入数据：分子结构本身，不是「算出来的结果」）
# =====================================================================
ALKANES = [
    ("正戊烷", 5, [(0, 1), (1, 2), (2, 3), (3, 4)]),
    ("2-甲基丁烷", 5, [(0, 1), (1, 2), (2, 3), (1, 4)]),
    ("2,2-二甲基丙烷", 5, [(0, 1), (0, 2), (0, 3), (0, 4)]),
    ("正己烷", 6, [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]),
    ("2,3-二甲基丁烷", 6, [(0, 1), (1, 2), (2, 3), (1, 4), (2, 5)]),
    ("3-甲基戊烷", 6, [(0, 1), (1, 2), (2, 3), (3, 4), (2, 5)]),
]


def _adj_of(n, edges):
    adj = [[] for _ in range(n)]
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    return adj


def _skeleton_payload(idx):
    """返回第 idx 号（从 1 开始）烷烃的画板数据。"""
    name, n, edges = ALKANES[idx - 1]
    adj = _adj_of(n, edges)
    lay = K.tree_layout(adj)
    xs = [p[0] for p in lay.values()]
    span = max(abs(v) for v in xs) if xs else 1.0
    sx = min(3.9 / max(span, 1e-9), 1.30)
    sy = 0.80
    nodes = [[round(5.0 + lay[i][0] * sx, 4), round(4.05 + lay[i][1] * sy, 4)] for i in range(n)]
    hc = [K.h_on_carbon(adj, i) for i in range(n)]
    kinds, gid, _ = K.equivalent_hydrogens(adj)
    groups = [(gid[(i, 0)] if hc[i] > 0 else -1) for i in range(n)]
    chain, loc, nsub = K.main_chain(adj)
    return {"name": name, "nodes": nodes, "edges": [list(e) for e in edges],
            "hc": hc, "groups": groups, "chain": list(chain), "loc": list(loc),
            "nsub": nsub, "kinds": kinds}


# =====================================================================
# 1) 不饱和度
# =====================================================================
UN_C = 6
EXPR_UN_OM = f"(2*{UN_C}+2-hh)/2"


def build_unsaturation() -> dict:
    for h in range(6, 15):
        _agree(f"Ω(C={UN_C},H={h})", EXPR_UN_OM, K.unsaturation(UN_C, h), tol=1e-12, hh=h)
    _agree("Ω(己烷) = 0", EXPR_UN_OM, 0.0, tol=1e-12, hh=14)
    _agree("Ω(苯) = 4", EXPR_UN_OM, 4.0, tol=1e-12, hh=6)
    _agree("H 为奇数时 Ω 是半整数", EXPR_UN_OM, 0.5, tol=1e-12, hh=13)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "unsat", "ch": UN_C, "hh": "hh",
                  "caption": "Ω 标尺：拖滑块让氢原子数变少，看 Ω 怎么升高"},
        "param": {"name": "hh", "label": "氢原子数 $H$", "min": 6, "max": 14,
                  "step": 1, "value": 6, "unit": "", "standard": 6,
                  "ticks": ["6 (苯)", "8", "10", "12", "14 (己烷)"]},
        "readouts": [
            ro("c", "碳原子数 $C$（定值）", f"{UN_C}", 0),
            ro("h", "氢原子数 $H$", "hh", 0),
            ro("om", "不饱和度 $\\Omega$", EXPR_UN_OM, 1),
            ro_status("int", "Ω 是否为整数（分子式是否合法）",
                      f"abs(({EXPR_UN_OM})-floor(({EXPR_UN_OM})+0.5))", 0.05, "<",
                      "Ω 是整数：分子式合理", "Ω 是半整数：需有 N（或为自由基）"),
        ],
        "constant": {"of": "c", "label": "碳原子数固定为 6 —— 只改氢原子数，看 Ω 怎么变"},
    }
    lesson = {
        "language": "zh-CN", "title": "不饱和度 Ω 与分子式",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>已知一个只含碳、氢两种元素的有机物分子式为 "
            "$\\mathrm{C_6H_H}$（$H$ 可调）。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出不饱和度 $\\Omega$ 的表达式；</li>"
            "<li>拖动滑块，$H$ 从 14 减到 6，$\\Omega$ 怎么变？</li>"
            "<li>$H$ 为奇数时会出现什么情况？</li></ol>"),
        "answerLabel": "$\\mathrm{C_6H_6}$（苯）时",
        "answer": f"$\\Omega = \\dfrac{{2\\times6+2-6}}{{2}} = {K.f(K.unsaturation(6, 6), 1)}$，"
                  "对应 3 个双键 + 1 个环",
    }
    steps = [
        {"title": "Ω 的定义：跟饱和烷烃比",
         "content": ("<p>饱和烷烃的通式是 $\\mathrm{C_nH_{2n+2}}$。"
                     "如果一个分子比它**少**了 $2\\Omega$ 个氢，就说明有 $\\Omega$ 个"
                     "「双键或环」。</p>"
                     "<p>于是</p>"
                     "<p>$\\Omega = \\dfrac{2C + 2 + N - H - X}{2}$。</p>"
                     "<p>推导时记住三件事：每个双键少 2 个 H、每个环少 2 个 H、"
                     "每个三键少 4 个 H（所以三键算 2 个不饱和度）。"
                     "含 $N$ 的加 $N$，含卤素的减 $X$（卤素相当于一个氢）。</p>")},
        {"title": "常见值要记住",
         "content": ("<p>· $\\Omega = 0$：链状饱和（烷烃、饱和一元醇等）；</p>"
                     "<p>· $\\Omega = 1$：一个双键**或**一个环。"
                     "乙醛、丙酮、环己烷都是 $\\Omega = 1$；</p>"
                     "<p>· $\\Omega = 2$：三键，或两个双键；</p>"
                     "<p>· $\\Omega = 4$：苯环（3 个双键 + 1 个环），"
                     "苯、甲苯、苯酚都是 $\\Omega = 4$。</p>"
                     "<p>读数区把 $\\Omega$ 直接翻译成了这几种可能 —— "
                     "但注意它只给出**可能性**，具体结构还要靠其他信息定。</p>")},
        {"title": "为什么 H 必须是偶数（对本例）",
         "content": ("<p>本页 $C = 6$ 且不含 $N$、$X$，所以 "
                     "$\\Omega = \\dfrac{14 - H}{2}$。</p>"
                     "<p>$H$ 取奇数时 $\\Omega$ 是半整数 —— 而「双键或环的个数」"
                     "不可能是一半。所以**奇数的 $H$ 配偶数个 $C$ 不合法的中性分子**，"
                     "除非分子里含氮（比如 $\\mathrm{C_5H_5N}$ 吡啶）。"
                     "状态灯会在这里翻转。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 燃烧耗氧量
# =====================================================================
BN_C, BN_H = 2, 6
EXPR_BN_O2 = f"{BN_C}+{BN_H}/4-zo/2"


def build_combustion() -> dict:
    for z in (0, 1, 2):
        _agree(f"耗氧(z={z})", EXPR_BN_O2, K.oxygen_demand(BN_C, BN_H, z), tol=1e-12, zo=z)
        _agree(f"CO₂(z={z})", f"{BN_C}", K.combustion_products(BN_C, BN_H, z)[0], tol=1e-12)
        _agree(f"H₂O(z={z})", f"{BN_H}/2", K.combustion_products(BN_C, BN_H, z)[1], tol=1e-12)
        _agree(f"O₂ 质量(z={z})", f"({EXPR_BN_O2})*32", K.oxygen_mass(BN_C, BN_H, z), tol=1e-12, zo=z)
    _agree("乙烷耗氧 3.5", EXPR_BN_O2, 3.5, tol=1e-12, zo=0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "burn", "zo": "zo",
                  "caption": "三条按同一比例：氧原子越多，耗氧条越短（自带氧「抵账」）"},
        "param": {"name": "zo", "label": "分子中的氧原子数 $z$", "min": 0, "max": 2,
                  "step": 1, "value": 0, "unit": "", "standard": 0,
                  "ticks": ["0 (乙烷)", "1 (乙醇)", "2 (乙二醇/乙酸)"]},
        "readouts": [
            ro("o2", "耗氧量 $x + y/4 - z/2$", EXPR_BN_O2, 2, "mol"),
            ro("m", "所需 O₂ 质量", f"({EXPR_BN_O2})*32", 1, "g"),
            ro("co2", "生成 CO₂（定值）", f"{BN_C}", 0, "mol"),
            ro("h2o", "生成 H₂O（定值）", f"{BN_H}/2", 0, "mol"),
            ro_status("cheap", "自带氧是否让耗氧量降下来了（< 3.5 mol）",
                      EXPR_BN_O2, 3.5, "<",
                      "低于乙烷：分子自带的氧帮了忙", "等于乙烷的耗氧量"),
        ],
        "constant": {"of": "co2", "label": "$C = 2$、$H = 6$ 固定 ⇒ 产物恒为 2 CO₂ + 3 H₂O"},
    }
    lesson = {
        "language": "zh-CN", "title": "有机物燃烧的耗氧量",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>某有机物分子式 $\\mathrm{C_2H_6O_z}$（$z$ 可调），完全燃烧。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出燃烧的化学方程式；</li>"
            "<li>求 1 mol 该有机物耗氧的物质的量；</li>"
            "<li>为什么 $z$ 变大耗氧反而变少？</li></ol>"),
        "answerLabel": "$z = 0$（乙烷）时",
        "answer": f"$\\mathrm{{C_2H_6}} + {K.f(K.oxygen_demand(BN_C, BN_H, 0), 1)}\\ \\mathrm{{O_2}} "
                  f"\\to 2\\ \\mathrm{{CO_2}} + 3\\ \\mathrm{{H_2O}}$",
    }
    steps = [
        {"title": "配平的通用办法",
         "content": ("<p>先配碳：$x$ 个 $C$ 需要 $x$ 个 $\\mathrm{CO_2}$；</p>"
                     "<p>再配氢：$y$ 个 $H$ 需要 $\\dfrac{y}{2}$ 个 $\\mathrm{H_2O}$；</p>"
                     "<p>最后用**氧原子总数守恒**配 $\\mathrm{O_2}$：右边一共 "
                     "$2x + \\dfrac{y}{2}$ 个氧原子，其中 $z$ 个来自有机物本身，"
                     "剩下 $2x + \\dfrac{y}{2} - z$ 个由 $\\mathrm{O_2}$ 提供，"
                     "所以</p>"
                     "<p>$n(\\mathrm{O_2}) = x + \\dfrac{y}{4} - \\dfrac{z}{2}$。</p>")},
        {"title": "等物质的量下的比较",
         "content": ("<p>本页 $C = 2$、$H = 6$ 固定：</p>"
                     "<p>· 乙烷 $\\mathrm{C_2H_6}$：耗氧 $3.5\\ \\mathrm{mol}$；</p>"
                     "<p>· 乙醇 $\\mathrm{C_2H_6O}$：耗氧 $3.0\\ \\mathrm{mol}$；</p>"
                     "<p>· 乙二醇 $\\mathrm{C_2H_6O_2}$：耗氧 $2.5\\ \\mathrm{mol}$。</p>"
                     "<p>每多一个氧原子，耗氧就少 $0.5\\ \\mathrm{mol}$ —— "
                     "因为分子自己已经带了一份氧，外部的 $\\mathrm{O_2}$ 就少用一份。</p>")},
        {"title": "一个常用的等价说法",
         "content": ("<p>把分子式写成 $\\mathrm{(H_2O)_a \\cdot C_bH_c}$ 的形式，"
                     "则耗氧量只由 $\\mathrm{C_bH_c}$ 部分决定 —— "
                     "「自带的水」不参与耗氧。</p>"
                     "<p>例如乙醇 $\\mathrm{C_2H_6O = C_2H_4 \\cdot H_2O}$，"
                     "耗氧等于乙烯的：$2 + 4/4 = 3\\ \\mathrm{mol}$，与上面的结果一致。"
                     "考试里这样算比套公式快得多。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 由燃烧产物确定分子式
# =====================================================================
FM_CO2, FM_H2O, FM_SAMPLE = 4.4, 1.8, 3.0
EXPR_FM_NC = f"{FM_CO2}/44"
EXPR_FM_NH = f"2*{FM_H2O}/18"
EXPR_FM_MO = f"{FM_SAMPLE}-12*({EXPR_FM_NC})-1*({EXPR_FM_NH})"
EXPR_FM_K = "mr/30"


def build_formula() -> dict:
    emp, mC, mH, mO = K.empirical_from_masses(FM_CO2, FM_H2O, FM_SAMPLE)
    assert emp == [1, 2, 1], f"实验式应为 CH₂O，实得 {emp}"
    for mr in (30, 60, 90, 120, 180):
        _agree(f"倍数 k(Mr={mr})", EXPR_FM_K, K.formula_multiplier([1, 2, 1], mr), tol=1e-12, mr=mr)
    _agree("n(C)", EXPR_FM_NC, 0.1, tol=1e-12)
    _agree("n(H)", EXPR_FM_NH, 0.2, tol=1e-12)
    _agree("m(O)", EXPR_FM_MO, 1.6, tol=1e-12)
    _agree("m(O) 与内核一致", EXPR_FM_MO, mO, tol=1e-12)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "formula", "mr": "mr",
                  "caption": "两个吸收管分别捕集 H₂O 与 CO₂；实验式 × k = 分子式"},
        "param": {"name": "mr", "label": "相对分子质量 $M_r$", "min": 30, "max": 180,
                  "step": 30, "value": 180, "unit": "", "standard": 180,
                  "ticks": ["30", "60", "90", "120", "180 (葡萄糖)"]},
        "readouts": [
            ro("nc", "$n(\\mathrm{C}) = n(\\mathrm{CO_2})$", EXPR_FM_NC, 3, "mol"),
            ro("nh", "$n(\\mathrm{H}) = 2n(\\mathrm{H_2O})$", EXPR_FM_NH, 3, "mol"),
            ro("mo", "$m(\\mathrm{O})$（差减法）", EXPR_FM_MO, 2, "g"),
            ro("k", "倍数 $k = M_r / 30$", EXPR_FM_K, 0),
            ro_status("int", "$k$ 是否为整数", f"abs(({EXPR_FM_K})-floor(({EXPR_FM_K})+0.5))",
                      0.05, "<", "整数倍：可以确定分子式", "不是整数倍：该 Mr 不可能"),
        ],
        "constant": {"of": "e30", "label": "实验式 $\\mathrm{CH_2O}$（$M_r = 30$）是先定下来不变的"},
        "scalars": [{"name": "e30", "expr": "30"}],
        }
    lesson = {
        "language": "zh-CN", "title": "由燃烧产物确定分子式",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>取某有机物 $3.0\\ \\mathrm{g}$ 完全燃烧，"
            "生成的气体依次通过浓硫酸与 $\\mathrm{NaOH}$ 溶液，"
            "两管分别增重 $1.8\\ \\mathrm{g}$ 与 $4.4\\ \\mathrm{g}$。"
            "又测得其相对分子质量为 $M_r$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求分子中各元素的物质的量；</li>"
            "<li>求实验式；</li>"
            "<li>结合 $M_r$ 确定分子式。</li></ol>"),
        "answerLabel": "$M_r = 180$ 时",
        "answer": f"实验式 $\\mathrm{{CH_2O}}$，$k = 180/30 = 6$ ⇒ "
                  "$\\mathrm{C_6H_{12}O_6}$（葡萄糖）",
    }
    steps = [
        {"title": "碳来自 CO₂、氢来自 H₂O",
         "content": ("<p>浓硫酸吸的是**水**（增重 $1.8\\ \\mathrm{g}$），"
                     "$\\mathrm{NaOH}$ 吸的是**二氧化碳**（增重 $4.4\\ \\mathrm{g}$）。</p>"
                     "<p>$n(\\mathrm{C}) = n(\\mathrm{CO_2}) = \\dfrac{4.4}{44} "
                     "= 0.1\\ \\mathrm{mol}$；</p>"
                     "<p>$n(\\mathrm{H}) = 2n(\\mathrm{H_2O}) = 2\\times\\dfrac{1.8}{18} "
                     "= 0.2\\ \\mathrm{mol}$。</p>"
                     "<p>于是 $m(\\mathrm{C}) = 1.2\\ \\mathrm{g}$、"
                     "$m(\\mathrm{H}) = 0.2\\ \\mathrm{g}$。</p>")},
        {"title": "氧必须用差减法",
         "content": ("<p>$\\mathrm{CO_2}$ 与 $\\mathrm{H_2O}$ 里都含氧，"
                     "但氧**既可能来自有机物，也可能来自燃烧用的空气**，"
                     "所以不能直接相加，只能减：</p>"
                     "<p>$m(\\mathrm{O}) = 3.0 - 1.2 - 0.2 = 1.6\\ \\mathrm{g}$，"
                     "$n(\\mathrm{O}) = 0.1\\ \\mathrm{mol}$。</p>"
                     "<p>这正是本页把 $m(\\mathrm{O})$ 单列成一个读数的原因 —— "
                     "它是唯一一个「必须靠减法」的量。</p>")},
        {"title": "实验式 → 分子式",
         "content": ("<p>$\\mathrm{C}:\\mathrm{H}:\\mathrm{O} = 0.1:0.2:0.1 = 1:2:1$，"
                     "实验式 $\\mathrm{CH_2O}$（$M_r = 30$）。</p>"
                     "<p>再用相对分子质量定倍数：$k = \\dfrac{M_r}{30}$。</p>"
                     "<p>· $k = 1$：甲醛 $\\mathrm{CH_2O}$；</p>"
                     "<p>· $k = 2$：乙酸 $\\mathrm{C_2H_4O_2}$；</p>"
                     "<p>· $k = 6$：葡萄糖 $\\mathrm{C_6H_{12}O_6}$。</p>"
                     "<p>注意**实验式相同不代表是同一种物质**："
                     "甲醛、乙酸、葡萄糖的实验式都是 $\\mathrm{CH_2O}$。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 等效氢与一氯代物
# =====================================================================
def build_equiv_h() -> dict:
    payloads = [_skeleton_payload(i) for i in range(1, len(ALKANES) + 1)]
    for idx in range(1, len(ALKANES) + 1):
        pl = _skeleton_payload(idx)
        adj = _adj_of(ALKANES[idx - 1][1], ALKANES[idx - 1][2])
        kinds, gid, hc = K.equivalent_hydrogens(adj)
        assert kinds == pl["kinds"], f"第 {idx} 号分子的等效氢数不一致"
        # 每种等效氢至少要有一个位置
        assert len(set(gid.values())) == kinds
        # 氢总数 = 2n+2
        assert sum(hc) == 2 * len(adj) + 2

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {
            "kind": "skeleton_h", "mol": "mol",
            "nodesAll": [p["nodes"] for p in payloads],
            "edgesAll": [p["edges"] for p in payloads],
            "groupsAll": [p["groups"] for p in payloads],
            "hcAll": [p["hc"] for p in payloads],
            "kindsAll": [p["kinds"] for p in payloads],
            "namesAll": [p["name"] for p in payloads],
            "caption": "碳上的数字是氢原子个数；同色碳上的氢彼此等价（互换后分子不变）",
        },
        "param": {"name": "mol", "label": "选择分子（1–6）", "min": 1, "max": 6,
                  "step": 1, "value": 1, "unit": "", "standard": 1,
                  "ticks": ["1 正戊烷", "2 异戊烷", "3 新戊烷", "4 正己烷", "5 2,3-二甲基丁烷", "6 3-甲基戊烷"]},
        "readouts": [
            ro("kinds", "等效氢的种数（= 一氯代物数）",
               "[" + ",".join(str(p["kinds"]) for p in
                              [_skeleton_payload(i) for i in range(1, 7)]) + "][mol-1]", 0),
            ro("carbons", "碳原子数",
               "[" + ",".join(str(ALKANES[i - 1][1]) for i in range(1, 7)) + "][mol-1]", 0),
            ro("hydrogens", "氢原子总数 $2n+2$",
               "[" + ",".join(str(2 * ALKANES[i - 1][1] + 2) for i in range(1, 7)) + "][mol-1]", 0),
            ro_status("one", "是否只有一种等效氢（一氯代物唯一）",
                      "[" + ",".join(str(p["kinds"]) for p in
                                     [_skeleton_payload(i) for i in range(1, 7)]) + "][mol-1]", 1, "==",
                      "只有一种等效氢：一氯代物只有 1 种", "有多种等效氢"),
        ],
        "constant": {"of": "carbons", "label": "同分异构体的碳数相同、氢数也相同（都是 $2n+2$）"},
    }
    lesson = {
        "language": "zh-CN", "title": "等效氢与一氯代物的种数",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>下列五个烷烃：正戊烷、2-甲基丁烷、2,2-二甲基丙烷、正己烷、"
            "2,3-二甲基丁烷。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>逐一判断它们的等效氢有几种；</li>"
            "<li>对应的一氯代物各有几种？</li>"
            "<li>为什么「等效氢越多」与「氢越多」不是一回事？</li></ol>"),
        "answerLabel": "2,2-二甲基丙烷（新戊烷）",
        "answer": "它的 12 个氢**全部等效** ⇒ 一氯代物只有 1 种",
    }
    steps = [
        {"title": "什么叫等效氢",
         "content": ("<p>两个氢是**等效**的，当且仅当把它们互换之后，"
                     "整个分子的结构（包括所有原子的连接方式）**完全不变**。</p>"
                     "<p>用数学的话说：等效氢就是碳骨架**自同构群**作用下"
                     "氢原子位置的**轨道**。所以「等效氢的种数」是有严格定义的，"
                     "不是靠眼睛看的。</p>"
                     "<p>本页的数字全部由程序枚举自同构群算出 —— "
                     "对每个置换验证邻接关系是否保持，再求氢位置的轨道。</p>")},
        {"title": "两条快速判据",
         "content": ("<p>考试里不需要枚举群，用这两条就够：</p>"
                     "<p>· **同一个碳上的氢等效**（甲基上的 3 个氢永远互相等效）；</p>"
                     "<p>· **处在对称位置上的碳，其氢也等效**"
                     "（例如正戊烷里第 1 与第 5 个碳）。</p>"
                     "<p>正戊烷：两端 $\\mathrm{CH_3}$ 等效、2 与 4 位 $\\mathrm{CH_2}$ 等效、"
                     "中间的 $\\mathrm{CH_2}$ 单独一种 ⇒ 3 种，一氯代物 3 种。</p>"
                     "<p>新戊烷 $\\mathrm{C(CH_3)_4}$：四个甲基通过中心碳完全对称 ⇒ "
                     "只有 1 种 ⇒ 一氯代物也只有 1 种。状态灯会亮。</p>")},
        {"title": "换个角度理解",
         "content": ("<p>为什么「等效氢的种数」正好等于一氯代物的种数？"
                     "因为取代哪个等效氢，得到的产物结构完全一样（只是把"
                     "编号换了一下）。所以**种数 = 轨道数**。</p>"
                     "<p>这也解释了为什么同分异构体的数目要按「碳骨架」而不是"
                     "「画法」来数：2-甲基丁烷不管画成什么样子，都只有 4 种一氯代物。"
                     "把滑块拖到第 5 号分子（2,3-二甲基丁烷）会发现答案是 2 种 —— "
                     "四个甲基两两对称，但**不同碳上的甲基却等价**，"
                     "这一点只靠「同一个碳上的氢等效」是不够用的。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 官能团定量反应
# =====================================================================
# 分子结构是**输入数据**（官能团个数），消耗量由内核算出。
FUNC_MOLS = [
    ("乙醇", "C₂H₆O", {"oh": 1}),
    ("乙二醇", "C₂H₆O₂", {"oh": 2}),
    ("乙酸", "C₂H₄O₂", {"cooh": 1}),
    ("葡萄糖", "C₆H₁₂O₆", {"oh": 5, "cho": 1}),
    ("苯酚", "C₆H₆O", {"phenol": 1, "ring": 1}),
    ("丙烯醛", "C₃H₄O", {"cho": 1, "db": 1}),
]


def _func_payload(i):
    name, formula, g = FUNC_MOLS[i - 1]
    oh = g.get("oh", 0)
    cooh = g.get("cooh", 0)
    phenol = g.get("phenol", 0)
    cho = g.get("cho", 0)
    db = g.get("db", 0)
    tb = g.get("tb", 0)
    ring = g.get("ring", 0)
    return {"mname": name, "mformula": formula,
            "noh": oh, "ncooh": cooh, "ncho": cho, "ndb": db, "nring": ring,
            "h2": K.h2_from_sodium(oh, cooh),
            "naoh": K.naoh_consumed(cooh, phenol, 0),
            "ag": K.ag_from_aldehyde(cho),
            "br2": K.br2_addition(db, tb),
            "h2add": K.h2_addition(db, tb, ring)}


def build_functional() -> dict:
    import json
    cases = [_func_payload(i) for i in range(1, len(FUNC_MOLS) + 1)]

    def arr(key, digits=3):
        return "[" + ",".join(f"{c[key]:.{digits}f}" for c in cases) + "][moli-1]"

    for i in range(1, len(FUNC_MOLS) + 1):
        c = _func_payload(i)
        name, formula, g = FUNC_MOLS[i - 1]
        assert abs(c["h2"] - K.h2_from_sodium(g.get("oh", 0), g.get("cooh", 0))) < 1e-12
        assert abs(c["naoh"] - K.naoh_consumed(g.get("cooh", 0), g.get("phenol", 0), 0)) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {
            "kind": "funcgroup", "moli": "moli",
            "h2All": [c["h2"] for c in cases],
            "naohAll": [c["naoh"] for c in cases],
            "agAll": [c["ag"] for c in cases],
            "br2All": [c["br2"] for c in cases],
            "h2addAll": [c["h2add"] for c in cases],
            "nohAll": [c["noh"] for c in cases],
            "ncoohAll": [c["ncooh"] for c in cases],
            "nchoAll": [c["ncho"] for c in cases],
            "ndbAll": [c["ndb"] for c in cases],
            "nringAll": [c["nring"] for c in cases],
            "namesAll": [c["mname"] for c in cases],
            "formulasAll": [c["mformula"] for c in cases],
            "caption": "五条柱由官能团个数算出：拖滑块看哪种官能团在起作用",
        },
        "param": {"name": "moli", "label": "选择物质（1–6）", "min": 1, "max": 6,
                  "step": 1, "value": 4, "unit": "", "standard": 4,
                  "ticks": ["1 乙醇", "2 乙二醇", "3 乙酸", "4 葡萄糖", "5 苯酚", "6 丙烯醛"]},
        "readouts": [
            ro("h2", "与 Na 放出的 $\\mathrm{H_2}$", arr("h2"), 1, "mol"),
            ro("naoh", "消耗的 $\\mathrm{NaOH}$", arr("naoh"), 1, "mol"),
            ro("ag", "银镜生成的 $\\mathrm{Ag}$", arr("ag"), 1, "mol"),
            ro("br2", "加成的 $\\mathrm{Br_2}$", arr("br2"), 1, "mol"),
            ro("h2add", "加成的 $\\mathrm{H_2}$", arr("h2add"), 1, "mol"),
            ro_status("active", "是否含有活泼氢（−OH 或 −COOH）",
                      "[" + ",".join(str(c["noh"] + c["ncooh"]) for c in cases) + "][moli-1]",
                      0.5, ">", "有活泼氢：能与 Na 反应放 H₂", "没有活泼氢"),
        ],
        "constant": {"of": "h2", "label": "Na 只认活泼氢：每 2 个 −OH / −COOH 放出 1 个 H₂"},
    }
    lesson = {
        "language": "zh-CN", "title": "官能团的定量反应",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>分别取 $1\\ \\mathrm{mol}$ 下列物质：乙醇、乙二醇、乙酸、葡萄糖"
            "（含 1 个醛基与 5 个羟基）、苯酚、丙烯醛。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>与足量 $\\mathrm{Na}$ 反应，各放出多少 $\\mathrm{H_2}$？</li>"
            "<li>消耗 $\\mathrm{NaOH}$、发生银镜、加成 $\\mathrm{Br_2}$ 各多少？</li>"
            "<li>为什么葡萄糖既不是酸、也不是醛，却能同时发生银镜并被 Na 放出氢气？</li></ol>"),
        "answerLabel": "葡萄糖（1 个 −CHO + 5 个 −OH）",
        "answer": f"与 Na 放出 ${K.f(K.h2_from_sodium(5, 0), 1)}$ mol H₂，"
                  f"银镜生成 ${K.f(K.ag_from_aldehyde(1), 1)}$ mol Ag",
    }
    steps = [
        {"title": "把「官能团」翻译成「比例」",
         "content": ("<p>有机计算的关键是把结构信息翻译成计量关系：</p>"
                     "<p>· 与 $\\mathrm{Na}$：**只有** $\\mathrm{-OH}$ 与 "
                     "$\\mathrm{-COOH}$ 上的氢（活泼氢）反应，"
                     "$2\\ \\mathrm{mol}$ 活泼氢 $\\to 1\\ \\mathrm{mol}\\ \\mathrm{H_2}$；</p>"
                     "<p>· 与 $\\mathrm{NaOH}$：羧基 $1:1$、酚羟基 $1:1$、酯基水解 $1:1$；"
                     "醇羟基**不**与 $\\mathrm{NaOH}$ 反应；</p>"
                     "<p>· 与 $\\mathrm{NaHCO_3}$：**只认羧基**（酸性强弱顺序："
                     "羧酸 > 碳酸 > 苯酚）；</p>"
                     "<p>· 银镜：每 $1\\ \\mathrm{mol}$ 醛基 $\\to 2\\ \\mathrm{mol}$ "
                     "$\\mathrm{Ag}$；</p>"
                     "<p>· 加成：每个双键 $1\\ \\mathrm{mol}\\ \\mathrm{Br_2}$、"
                     "每个三键 $2\\ \\mathrm{mol}$、每个苯环 $3\\ \\mathrm{mol}\\ \\mathrm{H_2}$。</p>")},
        {"title": "逐一核对",
         "content": ("<p>· 乙醇：1 个 $\\mathrm{-OH}$ ⇒ 放 $0.5\\ \\mathrm{mol}\\ \\mathrm{H_2}$，"
                     "不消耗 $\\mathrm{NaOH}$；</p>"
                     "<p>· 乙二醇：2 个 $\\mathrm{-OH}$ ⇒ 放 $1\\ \\mathrm{mol}$；</p>"
                     "<p>· 乙酸：1 个 $\\mathrm{-COOH}$ ⇒ 放 $0.5\\ \\mathrm{mol}\\ \\mathrm{H_2}$，"
                     "消耗 $1\\ \\mathrm{mol}\\ \\mathrm{NaOH}$；</p>"
                     "<p>· 葡萄糖：5 个 $\\mathrm{-OH}$ + 1 个 $\\mathrm{-CHO}$ ⇒ "
                     "放 $2.5\\ \\mathrm{mol}$，银镜 $2\\ \\mathrm{mol}$；</p>"
                     "<p>· 苯酚：酚羟基 ⇒ 放 $0.5\\ \\mathrm{mol}$，"
                     "消耗 $1\\ \\mathrm{mol}\\ \\mathrm{NaOH}$，苯环加 $3\\ \\mathrm{mol}\\ \\mathrm{H_2}$；</p>"
                     "<p>· 丙烯醛：1 个 $\\mathrm{-CHO}$ + 1 个双键 ⇒ 银镜 $2\\ \\mathrm{mol}$、"
                     "加 $1\\ \\mathrm{mol}\\ \\mathrm{Br_2}$。</p>")},
        {"title": "葡萄糖为什么「两边都像」",
         "content": ("<p>因为它**多羟基 + 一个醛基**同时存在于一个分子里："
                     "羟基提供活泼氢（与 Na 反应、与酸成酯），"
                     "醛基提供还原性（银镜、与新制氢氧化铜）。</p>"
                     "<p>注意区分「$\\mathrm{-OH}$ 在醇上 vs 在苯环上」："
                     "酚羟基能与 $\\mathrm{NaOH}$ 反应，而醇羟基不能 —— "
                     "这是区分醇与酚的经典判据，也是本页把「酚羟基」单列的原因。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 聚合度
# =====================================================================
PL_MONOMER_ADD = 28.0      # C₂H₄
PL_MONOMER_CON = 113.0     # 6-氨基己酸 H₂N(CH₂)₅COOH
PL_LOSS = 18.0
EXPR_PL_ADD = f"mrp/{PL_MONOMER_ADD:.0f}"
EXPR_PL_CON = f"(mrp-{PL_LOSS:.0f})/({PL_MONOMER_CON:.0f}-{PL_LOSS:.0f})"


def build_polymer() -> dict:
    for mr in (2800.0, 7000.0, 14000.0, 21000.0, 28000.0):
        _agree(f"加聚 n(Mr={mr})", EXPR_PL_ADD, K.addition_degree(mr, PL_MONOMER_ADD), tol=1e-12, mrp=mr)
        _agree(f"缩聚 n(Mr={mr})", EXPR_PL_CON,
               K.condensation_degree(mr, PL_MONOMER_CON, PL_LOSS), tol=1e-12, mrp=mr)
        # 缩聚还原：Mr = n·113 − (n−1)·18
        n = K.condensation_degree(mr, PL_MONOMER_CON, PL_LOSS)
        _agree(f"缩聚还原 Mr(Mr={mr})", f"({EXPR_PL_CON})*{PL_MONOMER_CON:.0f}-(({EXPR_PL_CON})-1)*{PL_LOSS:.0f}",
               mr, tol=1e-9, mrp=mr)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "polymer", "mrp": "mrp",
                  "caption": "上排加聚（链节 = 单体），下排缩聚（每连一次脱一个水）"},
        "param": {"name": "mrp", "label": "高分子相对分子质量 $M_r$", "min": 2800, "max": 28000,
                  "step": 280, "value": 14000.0, "unit": "", "standard": 14000.0,
                  "ticks": ["2800", "14000 (题设)", "28000"]},
        "readouts": [
            ro("na", "加聚聚合度 $n = M_r / 28$", EXPR_PL_ADD, 1),
            ro("nc", "缩聚聚合度 $n = (M_r-18)/95$", EXPR_PL_CON, 1),
            ro("ma", "聚乙烯链节相对分子质量（定值）", f"{PL_MONOMER_ADD:.0f}", 0),
            ro("mc", "尼龙-6 单体相对分子质量（定值）", f"{PL_MONOMER_CON:.0f}", 0),
            ro_status("big", "缩聚的聚合度是否超过 100",
                      EXPR_PL_CON, 100, ">", "缩聚度已超过 100", "缩聚度不到 100"),
        ],
        "constant": {"of": "ma", "label": "加聚的链节就是单体（$M_r = 28$），缩聚每连一次脱去 18"},
    }
    lesson = {
        "language": "zh-CN", "title": "加聚、缩聚与聚合度",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>已知某聚乙烯样品的相对分子质量为 $M_r$；"
            "又知某尼龙-6 样品（由 6-氨基己酸缩聚而成，单体 $M_r = 113$）"
            "的相对分子质量也是 $M_r$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>分别求两种高分子的聚合度；</li>"
            "<li>为什么两条式子不一样？</li>"
            "<li>若把 $M_r$ 看错成链节的分子量，会差多少？</li></ol>"),
        "answerLabel": "$M_r = 14000$ 时",
        "answer": f"加聚 $n = {K.f(K.addition_degree(14000.0, PL_MONOMER_ADD), 0)}$，"
                  f"缩聚 $n = {K.f(K.condensation_degree(14000.0, PL_MONOMER_CON, PL_LOSS), 1)}$",
    }
    steps = [
        {"title": "加聚：链节就是单体",
         "content": ("<p>加聚时双键打开、彼此相连，**不脱去任何小分子**，"
                     "所以高分子的相对分子质量就是单体的 $n$ 倍：</p>"
                     "<p>$M_r(\\text{高分子}) = n\\cdot M_r(\\text{单体})$ "
                     "$\\Rightarrow n = \\dfrac{M_r}{28}$。</p>"
                     "<p>常见的加聚单体：乙烯 $28$、氯乙烯 $62.5$、苯乙烯 $104$、"
                     "丙烯 $42$。</p>")},
        {"title": "缩聚：每连一次脱一个小分子",
         "content": ("<p>缩聚时每两个单体相连就脱掉一个 $\\mathrm{H_2O}$（或 $\\mathrm{HCl}$）。"
                     "$n$ 个单体连成一条链，一共形成 $n-1$ 个键，"
                     "所以脱去 $n-1$ 个小分子：</p>"
                     "<p>$M_r(\\text{高分子}) = n\\cdot M_r(\\text{单体}) "
                     "- (n-1)\\cdot 18$。</p>"
                     "<p>反解：$n = \\dfrac{M_r - 18}{113 - 18} = \\dfrac{M_r - 18}{95}$。</p>"
                     "<p>分子与分母都要减 —— 这是最容易错的地方。"
                     "把 $n$ 代回去可以验证：$n\\times113-(n-1)\\times18$ 正好还原 $M_r$。</p>")},
        {"title": "两者的差别有多大",
         "content": ("<p>同一个 $M_r = 14000$：加聚 $n = 500$，"
                     "缩聚 $n \\approx 147$ —— 差了 3 倍多。</p>"
                     "<p>原因有两层：**单体的分子量不同**（28 对 113），"
                     "以及**缩聚还脱了水**。所以做题时必须先分清是加聚还是缩聚。</p>"
                     "<p>顺带记住：加聚产物只有一种（高分子）；"
                     "缩聚产物有两种（高分子 + 小分子），"
                     "这也是判断「该用哪条式子」的最快线索。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 主链选择与编号
# =====================================================================
def build_mainchain() -> dict:
    payloads = [_skeleton_payload(i) for i in range(1, len(ALKANES) + 1)]
    for idx in range(1, len(ALKANES) + 1):
        name, n, edges = ALKANES[idx - 1]
        adj = _adj_of(n, edges)
        chain, loc, nsub = K.main_chain(adj)
        paths = K.all_paths(adj)
        longest = max(len(p) for p in paths)
        assert len(chain) == longest, f"{name} 的主链不是最长路径"
        assert len(loc) == nsub
        assert all(1 <= x <= len(chain) for x in loc)
        assert loc == sorted(loc)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {
            "kind": "skeleton_chain", "mol": "mol",
            "nodesAll": [p["nodes"] for p in payloads],
            "edgesAll": [p["edges"] for p in payloads],
            "chainAll": [p["chain"] for p in payloads],
            "locAll": [p["loc"] for p in payloads],
            "nsubAll": [p["nsub"] for p in payloads],
            "namesAll": [p["name"] for p in payloads],
            "caption": "黄点 = 主链（按「最长 → 取代基最多 → 位号最小」枚举路径定出）",
        },
        "param": {"name": "mol", "label": "选择分子（1–6）", "min": 1, "max": 6,
                  "step": 1, "value": 3, "unit": "", "standard": 3,
                  "ticks": ["1 正戊烷", "2 异戊烷", "3 新戊烷", "4 正己烷", "5 2,3-二甲基丁烷", "6 3-甲基戊烷"]},
        "readouts": [
            ro("nchain", "主链碳原子数",
               "[" + ",".join(str(len(K.main_chain(_adj_of(ALKANES[i - 1][1], ALKANES[i - 1][2]))[0]))
                              for i in range(1, 7)) + "][mol-1]", 0),
            ro("nsub", "取代基个数",
               "[" + ",".join(str(K.main_chain(_adj_of(ALKANES[i - 1][1], ALKANES[i - 1][2]))[2])
                              for i in range(1, 7)) + "][mol-1]", 0),
            ro("first", "最小的取代基位号",
               "[" + ",".join(str((K.main_chain(_adj_of(ALKANES[i - 1][1], ALKANES[i - 1][2]))[1] or [0])[0])
                              for i in range(1, 7)) + "][mol-1]", 0),
            ro("maxpath", "碳骨架中最长路径的碳数",
               "[" + ",".join(str(max(len(p) for p in K.all_paths(_adj_of(ALKANES[i - 1][1], ALKANES[i - 1][2]))))
                              for i in range(1, 7)) + "][mol-1]", 0),
            ro_status("sub2", "是否在 2 位就有取代基（编号从这端更有利）",
                      "[" + ",".join(str((K.main_chain(_adj_of(ALKANES[i - 1][1], ALKANES[i - 1][2]))[1] or [9])[0])
                                     for i in range(1, 7)) + "][mol-1]", 2, "==",
                      "2 位有取代基：位号已达最小", "2 位没有取代基"),
        ],
        "constant": {"of": "maxpath", "label": "主链的碳数恒等于**最长碳链**的碳数（先看这一条）"},
    }
    lesson = {
        "language": "zh-CN", "title": "主链选择与编号",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>给定下列碳骨架：正戊烷、2-甲基丁烷、2,2-二甲基丙烷、正己烷、"
            "2,3-二甲基丁烷、3-甲基戊烷。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>对每个分子找出主链；</li>"
            "<li>确定取代基的位号；</li>"
            "<li>说清「位号最小」为什么要从固定的那一端开始数。</li></ol>"),
        "answerLabel": "2,2-二甲基丙烷",
        "answer": "主链 3 个碳（不是 4！），两个甲基都在 **2 位** ⇒ 2,2-二甲基丙烷",
    }
    steps = [
        {"title": "第一步：找最长碳链",
         "content": ("<p>主链**只能沿着碳碳键走**，而且要尽可能长。"
                     "本页的做法是把碳骨架里所有简单路径都枚举出来，取最长的那条 —— "
                     "不是靠眼睛挑。</p>"
                     "<p>注意新戊烷 $\\mathrm{C(CH_3)_4}$：它没有 4 个碳的链！"
                     "任何一条路径最多只能走 3 个碳（中心碳 + 两个甲基），"
                     "所以主链是**丙烷**，另外两个甲基作为取代基。"
                     "很多人第一眼会误以为主链是 4 个碳。</p>")},
        {"title": "第二步：取代基要最多",
         "content": ("<p>如果最长链**不止一条**，就选取代基**最多**的那条。</p>"
                     "<p>例如某骨架里有两条 5 碳链，一条旁边挂着 1 个甲基、"
                     "另一条挂着 2 个，就取后者 —— 因为一般命名规则希望"
                     "「把复杂的东西放进主链」。</p>"
                     "<p>本页读数区的「取代基个数」就是把这一条判据显式算出来了。</p>")},
        {"title": "第三步：位号要最小",
         "content": ("<p>定下主链后，从**哪一端**开始编号？"
                     "两条方向各编一遍，取「取代基位号序列」按字典序较小的那个。</p>"
                     "<p>例如 3-甲基戊烷：从左边数甲基在 3 位，从右边数也在 3 位，"
                     "一样；但 2-甲基丁烷从左边数是 2 位、从右边数是 3 位，"
                     "所以取 2 位，叫「2-甲基丁烷」而不是「3-甲基丁烷」。</p>"
                     "<p>读数区里的「最小的取代基位号」<strong>拖滑块</strong>可以看到"
                     "它总是 ≤ 主链长度的一半加一 —— 这就是「位号最小」的直接体现。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "unsaturation": build_unsaturation,
    "combustion": build_combustion,
    "formula": build_formula,
    "equiv_h": build_equiv_h,
    "functional": build_functional,
    "polymer": build_polymer,
    "mainchain": build_mainchain,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="有机化学基础 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
