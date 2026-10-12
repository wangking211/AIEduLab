#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「高中数学·数列与三角」交互网页。

数据由 lib/seq_kernel.py 的 sympy 精确计算驱动（单一数据源）：等差/等比数列、裂项相消、
错位相减、递推数列、y=Asin(ωx+φ)、余弦定理解三角形、三角恒等式全部精确算出；
答案、分步数值、画板读数同源一致。每个 build_* 内置自检断言。

依赖 sympy。用能 import sympy 的解释器运行：
    python scripts/generate.py <题型key> [输出.html]
    python scripts/generate.py list
    python scripts/generate.py all <输出目录>
    python scripts/generate.py random [seed] [输出.html]
"""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PLACEHOLDER = "__LESSON_DATA__"

sys.path.insert(0, str(SKILL_DIR.parent.parent / "shared"))   # 共享运行时（见 edulab/shared/skillkit.py）
sys.path.insert(0, str(SKILL_DIR / "lib"))
import sympy as sp                       # noqa: E402
import seq_kernel as K                   # noqa: E402
from seq_kernel import tex, f            # noqa: E402
from skillkit import cli, required_sections   # noqa: E402


# =====================================================================
# 1) 等差数列：已知两项求 a1/d/通项/前 n 项和
# =====================================================================
def build_arithmetic() -> dict:
    sol = K.solve_arithmetic(terms={5: 14, 10: 29})          # a1=2, d=3
    assert sol["a1"] == 2 and sol["d"] == 3
    assert sol["an"].subs(K.U, 7) == 20 and sol["Sn"].subs(K.N, 10) == 155
    terms = [float(2 + 3 * (i - 1)) for i in range(1, 9)]
    partial = [float(sum(terms[:i])) for i in range(1, 9)]
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6.5]},
        "scene": {
            "kind": "seq", "caption": "aₙ 柱状图（下）与 Sₙ 折线（上）；拖动滑块切换 n",
            "terms": terms, "partial": partial, "cur": "n",
        },
        "param": {"name": "n", "label": "项数 $n$", "min": 1, "max": 8, "step": 1,
                  "value": 5, "unit": "", "ticks": ["1", "5 (题设 a₅)", "8"]},
        "readouts": [
            {"id": "n", "label": "项数 $n$", "type": "expr", "expr": "n", "digits": 0},
            {"id": "an", "label": "$a_n = 2+3(n-1)$", "type": "expr", "expr": "2+3*(n-1)",
             "digits": 0, "highlight": True},
            {"id": "sn", "label": "$S_n = \\frac{n(3n+1)}{2}$", "type": "expr",
             "expr": "n*(3*n+1)/2", "digits": 0},
            {"id": "st", "label": "等差中项检验", "type": "status",
             "expr": "abs((2+3*(n-1))-(2+3*(n-2))-3)", "op": "<", "rhs": 0.001,
             "okText": "aₙ − aₙ₋₁ = 3 恒定 ✓", "badText": "—"},
        ],
        "constant": {"label": "$d \\equiv 3$（公差恒定；$a_5=14,\\ a_{10}=29$ 唯一确定 $a_1=2,d=3$）"},
        "legend": [
            {"color": "obj", "text": "通项 aₙ（柱状，高亮当前 n）"},
            {"color": "good", "text": "前 n 项和 Sₙ（折线）"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "等差数列：由两项确定通项与前 n 项和",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>已知等差数列 $\\{a_n\\}$ 中，$a_5=14$，$a_{10}=29$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求数列的首项 $a_1$ 与公差 $d$；</li>"
                    "<li>求通项公式 $a_n$ 与前 10 项和 $S_{10}$；</li>"
                    "<li>拖动滑块观察 $a_n$、$S_n$ 随 $n$ 的变化。</li></ol>"),
        "answerLabel": "首项 / 公差 / 通项 / 前10项和",
        "answer": (f"$a_1 = 2$，$d = {tex(sol['d'])}$，$a_n = 3n-1$，"
                   f"$S_{{10}} = {tex(sol['Sn'].subs(K.N, 10))}$"),
    }
    steps = [
        {"title": "用已知两项列方程",
         "content": ("<p>等差数列通项 $a_n = a_1+(n-1)d$，代入 $a_5$、$a_{10}$：</p>"
                     "<p class='text-center'>$$ \\begin{cases} a_1+4d=14 \\\\ a_1+9d=29 \\end{cases} $$</p>")},
        {"title": "解出 a₁ 与 d",
         "content": ("<p>两式相减：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ 5d=15 \\Rightarrow d=3,\\qquad a_1=14-4\\times3=2 $$</div>")},
        {"title": "写出通项",
         "content": ("<p>代回通项公式：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ a_n=2+3(n-1)=3n-1 $$</div>"
                     "<p>检验：$a_5=3\\times5-1=14$ ✓，$a_{10}=3\\times10-1=29$ ✓。</p>")},
        {"title": "求前 10 项和",
         "content": ("<p>由求和公式 $S_n=\\dfrac{n(a_1+a_n)}{2}$：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ S_{10}=\\frac{10(2+29)}{2}=155 $$</div>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：$a_n$ 柱状图逐项等量升高（每步 +3），$S_n$ 折线是开口向上的抛物线"
                     "（$S_n=\\frac{n(3n+1)}{2}$ 为 $n$ 的二次式）。检验灯恒绿——"
                     "<b>相邻两项之差恒为公差 3</b>（定值指示）。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 等比数列：求 q/通项/前 n 项和
# =====================================================================
def build_geometric() -> dict:
    sol = K.solve_geometric(3, 2, n=5)                        # a1=3, q=2
    assert sol["q"] == 2 and sol["S_n"] == 93 and sol["term_n"] == 48
    terms = [float(3 * 2 ** (i - 1)) for i in range(1, 9)]
    partial = [float(3 * (2 ** i - 1)) for i in range(1, 9)]
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6.5]},
        "scene": {
            "kind": "seq", "caption": "aₙ 指数增长（下）与 Sₙ 折线（上）",
            "terms": terms, "partial": partial, "cur": "n",
        },
        "param": {"name": "n", "label": "项数 $n$", "min": 1, "max": 8, "step": 1,
                  "value": 5, "unit": "", "ticks": ["1", "5 (题设 S₅)", "8"]},
        "readouts": [
            {"id": "n", "label": "项数 $n$", "type": "expr", "expr": "n", "digits": 0},
            {"id": "an", "label": "$a_n = 3\\cdot 2^{n-1}$", "type": "expr",
             "expr": "3*pow(2,n-1)", "digits": 0, "highlight": True},
            {"id": "sn", "label": "$S_n = 3(2^n-1)$", "type": "expr",
             "expr": "3*(pow(2,n)-1)", "digits": 0},
            {"id": "st", "label": "等比中项检验", "type": "status",
             "expr": "abs((3*pow(2,n-1))/(3*pow(2,n-2))-2)", "op": "<", "rhs": 0.001,
             "okText": "aₙ / aₙ₋₁ = 2 恒定 ✓", "badText": "—"},
        ],
        "constant": {"label": "$q \\equiv 2$（公比恒定；$S_n=3(2^n-1)$ 随 $n$ 指数增长）"},
        "legend": [
            {"color": "obj", "text": "通项 aₙ（柱状，指数爆炸）"},
            {"color": "good", "text": "前 n 项和 Sₙ（折线）"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "等比数列：通项与前 n 项和",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>已知等比数列 $\\{a_n\\}$ 中，$a_1=3$，公比 $q=2$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求通项公式 $a_n$；</li>"
                    "<li>求前 5 项和 $S_5$；</li>"
                    "<li>拖动滑块观察指数增长的\"爆炸\"效应。</li></ol>"),
        "answerLabel": "公比 / 通项 / 前5项和",
        "answer": (f"$q = 2$，$a_n = 3\\times 2^{{n-1}}$，"
                   f"$S_5 = {tex(sol['S_n'])} = 93$"),
    }
    steps = [
        {"title": "写出通项",
         "content": ("<p>等比数列通项 $a_n=a_1 q^{n-1}$：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ a_n=3\\times2^{n-1} $$</div>"
                     "<p>$a_5=3\\times2^4=48$。</p>")},
        {"title": "前 n 项和公式",
         "content": ("<p>$q\\ne1$ 时 $S_n=\\dfrac{a_1(1-q^n)}{1-q}$：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ S_n=\\frac{3(1-2^n)}{1-2}=3(2^n-1) $$</div>")},
        {"title": "代入求 S₅",
         "content": ("<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ S_5=3(2^5-1)=3\\times31=93 $$</div>"
                     "<p>直接验算：$3+6+12+24+48=93$ ✓。</p>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：$a_n$ 柱状图<b>翻倍式窜高</b>（$n=8$ 时 $a_8=384$，"
                     "而等差数列同期仅 $23$）——这就是等比增长与等差增长的本质差别；"
                     "检验灯恒绿（$a_n/a_{n-1}\\equiv2$）。$S_n$ 几乎贴着 $a_n$："
                     "<b>大项主导求和</b>。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 裂项相消：1/(k(k+1)) 求和 → 极限 1
# =====================================================================
def build_telescope() -> dict:
    sol = K.solve_telescope()
    assert sol["partial"].subs(K.N, 10) == sp.Rational(10, 11) and sol["limit"] == 1
    terms = [float(1 / (k * (k + 1))) for k in range(1, 11)]
    partial = [float(n / (n + 1)) for n in range(1, 11)]
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6.5]},
        "scene": {
            "kind": "seq", "caption": "通项迅速变小，部分和却趋向极限 1",
            "terms": terms, "partial": partial, "cur": "n", "limit": 1,
        },
        "param": {"name": "n", "label": "项数 $n$", "min": 1, "max": 10, "step": 1,
                  "value": 4, "unit": "", "ticks": ["1", "4", "10"]},
        "readouts": [
            {"id": "n", "label": "项数 $n$", "type": "expr", "expr": "n", "digits": 0},
            {"id": "an", "label": "$a_n=\\frac{1}{n(n+1)}$", "type": "expr",
             "expr": "1/(n*(n+1))", "digits": 4},
            {"id": "sn", "label": "$S_n=\\frac{n}{n+1}$", "type": "expr",
             "expr": "n/(n+1)", "digits": 4, "highlight": True},
            {"id": "gap", "label": "距极限 $1-S_n$", "type": "expr",
             "expr": "1-n/(n+1)", "digits": 4},
            {"id": "st", "label": "裂项公式检验", "type": "status",
             "expr": "abs(n/(n+1)-(1-1/(n+1)))", "op": "<", "rhs": 0.0001,
             "okText": "Sₙ = 1 − 1/(n+1) 成立 ✓", "badText": "—"},
        ],
        "constant": {"label": "$S_n = 1-\\dfrac{1}{n+1} \\to 1\\ (n\\to\\infty)$（和有上界，永不等于 1）"},
        "legend": [
            {"color": "obj", "text": "通项 aₙ（越来越小）"},
            {"color": "good", "text": "部分和 Sₙ（逼近极限）"},
            {"color": "meter", "text": "极限 1（粉虚线）"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "裂项相消求和：无穷逼近而不达到",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>求数列 $a_n=\\dfrac{1}{n(n+1)}$ 的前 $n$ 项和 $S_n$，并说明当 "
                    "$n\\to\\infty$ 时 $S_n$ 的变化趋势。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>把通项拆成两项之差（裂项）；</li>"
                    "<li>利用相消求出 $S_n$；</li>"
                    "<li>拖动滑块观察 $S_n$ 如何逼近 1。</li></ol>"),
        "answerLabel": "裂项 / 前 n 项和 / 极限",
        "answer": (f"$a_n=\\dfrac1n-\\dfrac1{{n+1}}$，$S_n = {tex(sol['partial'])} "
                   f"= 1-\\dfrac1{{n+1}}$，$\\lim\\limits_{{n\\to\\infty}}S_n = {tex(sol['limit'])}$"),
    }
    steps = [
        {"title": "裂项（关键一步）",
         "content": ("<p>把通项拆成相邻两项之差：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ \\frac{1}{n(n+1)}=\\frac1n-\\frac1{n+1} $$</div>"
                     "<p>（右边通分即得左边，可自行验证。）</p>")},
        {"title": "写出部分和并相消",
         "content": ("<p>把前 $n$ 项逐项展开：</p>"
                     "<p class='text-center'>$$ S_n=\\left(1-\\frac12\\right)+\\left(\\frac12-\\frac13\\right)"
                     "+\\cdots+\\left(\\frac1n-\\frac1{n+1}\\right) $$</p>"
                     "<p>中间项两两抵消（\"相消\"），只剩首尾：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ S_n=1-\\frac1{n+1}=\\frac{n}{n+1} $$</div>")},
        {"title": "分析趋势",
         "content": ("<p>$n$ 越大，$\\frac1{n+1}$ 越接近 0，$S_n$ 越接近 1，"
                     "但对任何有限的 $n$ 都有 $S_n<1$：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ \\lim_{n\\to\\infty}S_n=1 $$</div>"
                     "<p>$S_{10}=\\frac{10}{11}\\approx0.9091$，$S_{100}\\approx0.9901$。</p>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：下面板的通项柱越来越矮（第 10 项仅 $\\frac1{110}\\approx0.0091$），"
                     "上面板的 $S_n$ 折线却不断爬升、<b>无限逼近粉色虚线 1</b>（定值指示），"
                     "却永远差 $\\frac1{n+1}$——<b>有限项之和可以无限接近却达不到</b>，"
                     "这正是极限思想的雏形。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 错位相减：k·2^(k-1) 求和
# =====================================================================
def build_offset_sum() -> dict:
    sol = K.solve_offset_sum(2)
    assert sol["partial"].subs(K.N, 4) == 49
    assert sp.simplify(sol["partial"] - (1 + (K.N - 1) * 2 ** K.N)) == 0
    terms = [float(k * 2 ** (k - 1)) for k in range(1, 9)]
    partial = [float(1 + (n - 1) * 2 ** n) for n in range(1, 9)]
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6.5]},
        "scene": {
            "kind": "seq", "caption": "aₙ=k·2ᵏ⁻¹（下）与 Sₙ=1+(n−1)·2ⁿ（上）",
            "terms": terms, "partial": partial, "cur": "n",
        },
        "param": {"name": "n", "label": "项数 $n$", "min": 1, "max": 8, "step": 1,
                  "value": 4, "unit": "", "ticks": ["1", "4 (题设 S₄)", "8"]},
        "readouts": [
            {"id": "n", "label": "项数 $n$", "type": "expr", "expr": "n", "digits": 0},
            {"id": "an", "label": "$a_n=n\\cdot2^{n-1}$", "type": "expr",
             "expr": "n*pow(2,n-1)", "digits": 0, "highlight": True},
            {"id": "sn", "label": "$S_n=1+(n-1)2^n$", "type": "expr",
             "expr": "1+(n-1)*pow(2,n)", "digits": 0},
            {"id": "st", "label": "和式递推检验", "type": "status",
             "expr": "abs((1+(n-1)*pow(2,n))-(1+(n-2)*pow(2,n-1))-n*pow(2,n-1))",
             "op": "<", "rhs": 0.001,
             "okText": "Sₙ − Sₙ₋₁ = aₙ ✓", "badText": "—"},
        ],
        "constant": {"label": "$S_n \\equiv 1+(n-1)\\cdot 2^{n}$（错位相减的闭式结果）"},
        "legend": [
            {"color": "obj", "text": "通项 aₙ = k·2ᵏ⁻¹"},
            {"color": "good", "text": "前 n 项和 Sₙ"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "错位相减法：等差×等比型数列求和",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>已知 $a_n=n\\cdot 2^{n-1}$（等差 $n$ 与等比 $2^{n-1}$ 相乘），"
                    "求前 $n$ 项和 $S_n$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>写出 $S_n$ 与 $2S_n$ 两个和式；</li>"
                    "<li>作差（错位相减）求出闭式；</li>"
                    "<li>拖动滑块验证 $S_n-S_{n-1}=a_n$。</li></ol>"),
        "answerLabel": "前 n 项和",
        "answer": (f"$S_n = {tex(sol['closed'])} = 1+(n-1)\\cdot2^n$（$S_4=49$）"),
    }
    steps = [
        {"title": "写出和式",
         "content": ("<p class='text-center'>$$ S_n=1+2\\cdot2+3\\cdot2^2+\\cdots+n\\cdot2^{n-1} $$</p>"
                     "<p>两边乘公比 $2$（<b>错位</b>一格）：</p>"
                     "<p class='text-center'>$$ 2S_n=1\\cdot2+2\\cdot2^2+\\cdots+(n-1)\\cdot2^{n-1}+n\\cdot2^{n} $$</p>")},
        {"title": "作差相消",
         "content": ("<p>用第一式减第二式，中间各列合并：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ -S_n=1+2+2^2+\\cdots+2^{n-1}-n\\cdot2^n $$</div>"
                     "<p>前面是等比数列求和 $2^n-1$：</p>"
                     "<p class='text-center'>$$ -S_n=(2^n-1)-n\\cdot2^n $$</p>")},
        {"title": "整理闭式",
         "content": ("<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ S_n=1+(n-1)\\cdot2^n $$</div>"
                     "<p>验算 $S_4=1+3\\times16=49=1+4+12+32$ ✓。</p>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：检验灯恒绿，确认 $S_n-S_{n-1}=a_n$（和式的基本性质）。"
                     "注意 $a_n$ 与 $S_n$ 都<b>指数级增长</b>（$n=8$ 时 $a_8=1024$、$S_8=1793$），"
                     "柱状图已自动按最大值缩放。<b>错位相减适用于\"等差×等比\"型通项</b>。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 递推数列：a_{n+1}=2a_n+1 → 构造等比
# =====================================================================
def build_recurrence() -> dict:
    sol = K.solve_recurrence(2, 1, 1)                          # a_n = 2^n − 1
    assert sol["an"] == 2 ** K.U - 1 and sol["an"].subs(K.U, 5) == 31
    terms = [float(2 ** i - 1) for i in range(1, 9)]
    partial = [float(sum(terms[:i])) for i in range(1, 9)]
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6.5]},
        "scene": {
            "kind": "seq", "caption": "aₙ = 2ⁿ − 1（下）与前 n 项和（上）",
            "terms": terms, "partial": partial, "cur": "n",
        },
        "param": {"name": "n", "label": "项数 $n$", "min": 1, "max": 8, "step": 1,
                  "value": 5, "unit": "", "ticks": ["1", "5 (a₅=31)", "8"]},
        "readouts": [
            {"id": "n", "label": "项数 $n$", "type": "expr", "expr": "n", "digits": 0},
            {"id": "an", "label": "$a_n=2^n-1$", "type": "expr", "expr": "pow(2,n)-1",
             "digits": 0, "highlight": True},
            {"id": "nxt", "label": "$a_{n+1}$", "type": "expr", "expr": "pow(2,n+1)-1",
             "digits": 0},
            {"id": "chk", "label": "$a_{n+1}-2a_n$", "type": "expr",
             "expr": "(pow(2,n+1)-1)-2*(pow(2,n)-1)", "digits": 0},
            {"id": "st", "label": "递推关系检验", "type": "status",
             "expr": "abs((pow(2,n+1)-1)-2*(pow(2,n)-1)-1)", "op": "<", "rhs": 0.001,
             "okText": "aₙ₊₁ = 2aₙ + 1 恒成立 ✓", "badText": "—"},
        ],
        "constant": {"label": "$a_{n+1}-2a_n \\equiv 1$（$b_n=a_n+1$ 是公比 2 的等比数列）"},
        "legend": [
            {"color": "obj", "text": "通项 aₙ = 2ⁿ − 1（梅森数）"},
            {"color": "good", "text": "前 n 项和 Sₙ = 2ⁿ⁺¹ − 2 − n"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "递推数列：构造等比数列求通项",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>已知数列 $\\{a_n\\}$ 满足 $a_1=1$，$a_{n+1}=2a_n+1$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>写出数列的前 5 项，猜测通项；</li>"
                    "<li>用\"构造等比数列\"的方法证明你的猜测；</li>"
                    "<li>拖动滑块验证递推关系恒成立。</li></ol>"),
        "answerLabel": "通项公式",
        "answer": (f"$a_n = {tex(sol['an'])} = 2^n-1$（$a_5=31$）"),
    }
    steps = [
        {"title": "写出前几项找规律",
         "content": ("<p>$a_1=1$，$a_2=2\\times1+1=3$，$a_3=7$，$a_4=15$，$a_5=31$……</p>"
                     "<p>观察到 $1,3,7,15,31$ 都比 2 的幂少 1，猜测 $a_n=2^n-1$。</p>")},
        {"title": "构造等比（关键变形）",
         "content": ("<p>在递推式两边<b>同时加 1</b>：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ a_{n+1}+1=2a_n+2=2(a_n+1) $$</div>"
                     "<p>令 $b_n=a_n+1$，则 $b_{n+1}=2b_n$，$b_1=a_1+1=2$，"
                     "故 $\\{b_n\\}$ 是首项 2、公比 2 的等比数列。</p>")},
        {"title": "回代得通项",
         "content": ("<p>$b_n=2\\times2^{n-1}=2^n$，于是：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ a_n=b_n-1=2^n-1 $$</div>"
                     "<p>检验：$a_1=2-1=1$ ✓，$a_{n+1}-2a_n=(2^{n+1}-1)-2(2^n-1)=1$ ✓。</p>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：读数 $a_{n+1}-2a_n$ <b>恒为 1</b>（定值指示），"
                     "检验灯恒绿——递推关系对每个 $n$ 都成立。"
                     "顺带一提，$a_n=2^n-1$ 正是二进制下 $n$ 个 1 组成的数"
                     "（$a_5=11111_2=31$），也是$n$阶汉诺塔的最少移动次数。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) y = A sin(ωx+φ)：周期 / 最值点 / 图像
# =====================================================================
def build_sin_wave() -> dict:
    sol = K.solve_sin_wave(2, 3, sp.pi / 6)
    assert sp.simplify(sol["T"] - 2 * sp.pi / 3) == 0
    assert sp.simplify(sol["x_max"] - sp.pi / 9) == 0
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6.2]},
        "scene": {
            "kind": "wave", "caption": "y = 2 sin(3x + π/6)，游标跟随滑块",
            "A": 2, "omega": 3, "phi": f(sp.pi / 6),
            "xmin": -1.2, "xmax": 5.4, "cur": "x", "curLabel": "x",
            "curDeg": "x*180/PI", "T": f(2 * sp.pi / 3),
        },
        "param": {"name": "x", "label": "横坐标 $x$（弧度）", "min": -1.2, "max": 5.4,
                  "step": 0.01, "value": f(sp.pi / 9), "unit": " rad",
                  "ticks": ["−1.2", "π/9≈0.35（最高点）", "5.4"]},
        "readouts": [
            {"id": "x", "label": "$x$", "type": "expr", "expr": "x", "digits": 3, "unit": "rad"},
            {"id": "xd", "label": "$x$（角度）", "type": "expr", "expr": "x*180/PI",
             "digits": 1, "unit": "°"},
            {"id": "y", "label": "$y=2\\sin(3x+\\frac{\\pi}{6})$", "type": "expr",
             "expr": "2*sin(3*x+PI/6)", "digits": 3, "highlight": True},
            {"id": "T", "label": "周期 $T=\\frac{2\\pi}{\\omega}$", "type": "expr",
             "expr": "2*PI/3", "digits": 3, "unit": "rad"},
            {"id": "st", "label": "是否到达最值", "type": "status",
             "expr": "abs(abs(2*sin(3*x+PI/6))-2)", "op": "<", "rhs": 0.005,
             "okText": "y = ±2：到达最值点", "badText": "−2 < y < 2"},
        ],
        "constant": {"label": "$T \\equiv \\dfrac{2\\pi}{3}\\approx 2.094$；"
                              "$y$ 的取值范围 $[-2,2]$（$A=2$ 决定振幅）"},
        "legend": [
            {"color": "obj", "text": "曲线 y = 2 sin(3x + π/6)"},
            {"color": "load", "text": "游标（当前 x 处的函数值）"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "正弦型函数 y = A sin(ωx + φ) 的图像与性质",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>已知函数 $y=2\\sin\\left(3x+\\dfrac{\\pi}{6}\\right)$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求函数的周期 $T$ 与值域；</li>"
                    "<li>求函数取得最大值时 $x$ 的取值（最小正角）；</li>"
                    "<li>拖动滑块观察图像与最值点。</li></ol>"),
        "answerLabel": "周期 / 值域 / 最大值点",
        "answer": (f"$T = {tex(sol['T'])} = \\dfrac{{2\\pi}}{{3}}$，值域 $[-2,2]$，"
                   f"当 $x = {tex(sol['x_max'])} = \\dfrac{{\\pi}}{{9}}$ 时 $y_{{\\max}}=2$"),
    }
    steps = [
        {"title": "求周期",
         "content": ("<p>$y=A\\sin(\\omega x+\\varphi)$ 的周期只由 $\\omega$ 决定：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ T=\\frac{2\\pi}{\\omega}=\\frac{2\\pi}{3}\\approx2.094 $$</div>"
                     "<p>$\\varphi=\\pi/6$ 只让图像左右平移，不影响周期。</p>")},
        {"title": "求值域",
         "content": ("<p>$\\sin$ 的取值范围是 $[-1,1]$，乘以 $A=2$：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ y\\in[-2,\\,2] $$</div>")},
        {"title": "求最大值点",
         "content": ("<p>$y=2$ 当且仅当 $\\sin(3x+\\pi/6)=1$，即</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ 3x+\\frac{\\pi}{6}=\\frac{\\pi}{2}+2k\\pi \\Rightarrow "
                     "x=\\frac{\\pi}{9}+\\frac{2k\\pi}{3},\\ k\\in\\mathbb{Z} $$</div>"
                     "<p>最小正角为 $x=\\pi/9\\approx0.349$（$\\approx19.99^\\circ$）。</p>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：游标沿曲线上下移动，$y$ 读数始终在 $[-2,2]$ 内（定值指示）；"
                     "当 $x$ 走到 $\\pi/9$ 或 $\\pi/9+T$ 等位置时，检验灯变绿"
                     "（<b>到达最值</b>）。图像每 $T\\approx2.094$ 重复一次，"
                     "$\\varphi=\\pi/6$ 使图像相对 $y=2\\sin3x$ <b>向左平移</b> "
                     "$\\dfrac{\\varphi}{\\omega}=\\dfrac{\\pi}{18}$。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 余弦定理解三角形（SAS：两边 b、c 与夹角 A 可拖动）
# =====================================================================
def build_sas_triangle() -> dict:
    sol = K.solve_sas(2, 3, 60)
    assert sp.simplify(sol["a"] - sp.sqrt(7)) == 0
    assert sp.simplify(sol["area"] - 3 * sp.sqrt(3) / 2) == 0
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6.5]},
        "scene": {
            "kind": "tri", "caption": "SAS：b=2、c=3 固定，拖动滑块改变夹角 A",
            "b": 2, "c": 3, "Ad": "A", "area": "3*sin(A*PI/180)",
        },
        "param": {"name": "A", "label": "夹角 $A$（度）", "min": 15, "max": 165, "step": 1,
                  "value": 60, "unit": "°", "ticks": ["15°", "60° (题设)", "165°"]},
        "readouts": [
            {"id": "A", "label": "夹角 $A$", "type": "expr", "expr": "A", "digits": 0, "unit": "°"},
            {"id": "a", "label": "$a=\\sqrt{b^2+c^2-2bc\\cos A}$", "type": "expr",
             "expr": "sqrt(4+9-2*2*3*cos(A*PI/180))", "digits": 3, "highlight": True},
            {"id": "B", "label": "角 $B$", "type": "expr",
             "expr": "acos(((4+9-2*2*3*cos(A*PI/180))+9-4)/(2*sqrt(4+9-2*2*3*cos(A*PI/180))*3))*180/PI",
             "digits": 1, "unit": "°"},
            {"id": "C", "label": "角 $C$", "type": "expr",
             "expr": "180-A-acos(((4+9-2*2*3*cos(A*PI/180))+9-4)/(2*sqrt(4+9-2*2*3*cos(A*PI/180))*3))*180/PI",
             "digits": 1, "unit": "°"},
            {"id": "area", "label": "$S=\\frac12 bc\\sin A$", "type": "expr",
             "expr": "3*sin(A*PI/180)", "digits": 3},
            {"id": "st", "label": "内角和检验", "type": "status",
             "expr": "abs(A+acos(((4+9-2*2*3*cos(A*PI/180))+9-4)/(2*sqrt(4+9-2*2*3*cos(A*PI/180))*3))*180/PI"
                    "+(180-A-acos(((4+9-2*2*3*cos(A*PI/180))+9-4)/(2*sqrt(4+9-2*2*3*cos(A*PI/180))*3))*180/PI)-180)",
             "op": "<", "rhs": 0.01, "okText": "A + B + C = 180° ✓", "badText": "—"},
        ],
        "constant": {"label": "$b\\equiv2,\\ c\\equiv3$（两边固定）；$A=90^\\circ$ 时面积最大 "
                              "$S=\\frac12 bc=3$，此时 $a=\\sqrt{13}$"},
        "legend": [
            {"color": "force", "text": "角 A（可拖动）"},
            {"color": "effort", "text": "边 c = AB = 3"},
            {"color": "good", "text": "边 b = AC = 2"},
            {"color": "load", "text": "边 a = BC（由余弦定理算出）"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "余弦定理：已知两边及夹角解三角形",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>在 $\\triangle ABC$ 中，已知 $b=AC=2$，$c=AB=3$，$A=60^\\circ$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求边 $a=BC$ 的长；</li>"
                    "<li>求 $\\triangle ABC$ 的面积；</li>"
                    "<li>拖动滑块改变夹角 $A$，观察 $a$ 与面积如何变化。</li></ol>"),
        "answerLabel": "边 a / 面积",
        "answer": (f"$a = {tex(sol['a'])} = \\sqrt7 \\approx 2.646$，"
                   f"$S = {tex(sol['area'])} = \\dfrac{{3\\sqrt3}}2 \\approx 2.598$"),
    }
    steps = [
        {"title": "选择余弦定理",
         "content": ("<p>已知<b>两边及夹角</b>（SAS），求第三边用余弦定理：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ a^2=b^2+c^2-2bc\\cos A $$</div>")},
        {"title": "代入求 a",
         "content": ("<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ a^2=2^2+3^2-2\\times2\\times3\\times\\cos60^\\circ "
                     "=4+9-12\\times\\tfrac12=7 $$</div>"
                     "<p>故 $a=\\sqrt7\\approx2.646$。（$\\cos60^\\circ=\\frac12$ 是本题数值规整的关键。）</p>")},
        {"title": "求面积",
         "content": ("<p>两边及夹角还可直接用面积公式：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ S=\\frac12 bc\\sin A=\\frac12\\times2\\times3\\times\\frac{\\sqrt3}{2}"
                     "=\\frac{3\\sqrt3}{2}\\approx2.598 $$</div>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块改变 $A$：$a$ 随 $A$ 增大而<b>单调增大</b>（大角对大边），"
                     "面积 $S=3\\sin A$ 在 $A=90^\\circ$ 时达到最大值 $3$（定值指示），"
                     "两头都变小。检验灯恒绿（$A+B+C=180^\\circ$）。"
                     "<b>SAS 情形下三角形唯一确定</b>——余弦定理正是勾股定理在非直角情形的推广。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 8) 三角恒等式：sin(θ+60°)+sin(θ−60°) ≡ sinθ
# =====================================================================
def build_identity() -> dict:
    sol = K.solve_identity()
    assert sp.simplify(sol["lhs"] - sol["rhs"]) == 0
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6.2]},
        "scene": {
            "kind": "wave", "caption": "两条移动的正弦曲线之和恒等于中间那条",
            "multi": [
                {"A": 1, "omega": 1, "phi": f(sp.pi / 3), "color": "#f87171"},
                {"A": 1, "omega": 1, "phi": f(-sp.pi / 3), "color": "#38bdf8"},
                {"A": 1, "omega": 1, "phi": 0, "color": "#34d399"},
            ],
            "xmin": -0.8, "xmax": 7.1, "cur": "th*PI/180", "curLabel": "θ",
            "curDeg": "th", "T": f(2 * sp.pi),
        },
        "param": {"name": "th", "label": "角 $\\theta$（度）", "min": 0, "max": 360, "step": 1,
                  "value": 30, "unit": "°", "ticks": ["0°", "180°", "360°"]},
        "readouts": [
            {"id": "th", "label": "$\\theta$", "type": "expr", "expr": "th", "digits": 0, "unit": "°"},
            {"id": "y1", "label": "$\\sin(\\theta+60^\\circ)$", "type": "expr",
             "expr": "sin((th+60)*PI/180)", "digits": 4},
            {"id": "y2", "label": "$\\sin(\\theta-60^\\circ)$", "type": "expr",
             "expr": "sin((th-60)*PI/180)", "digits": 4},
            {"id": "sum", "label": "两者之和", "type": "expr",
             "expr": "sin((th+60)*PI/180)+sin((th-60)*PI/180)", "digits": 4, "highlight": True},
            {"id": "y3", "label": "$\\sin\\theta$", "type": "expr",
             "expr": "sin(th*PI/180)", "digits": 4},
            {"id": "st", "label": "恒等式检验", "type": "status",
             "expr": "abs(sin((th+60)*PI/180)+sin((th-60)*PI/180)-sin(th*PI/180))",
             "op": "<", "rhs": 0.000001, "okText": "和 ≡ sinθ 恒成立 ✓", "badText": "—"},
        ],
        "constant": {"label": "$\\sin(\\theta+60^\\circ)+\\sin(\\theta-60^\\circ) "
                              "\\equiv \\sin\\theta$（对任意 $\\theta$ 成立）"},
        "legend": [
            {"color": "force", "text": "sin(θ + 60°)"},
            {"color": "effort", "text": "sin(θ − 60°)"},
            {"color": "good", "text": "sin θ（= 上两式之和）"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "三角恒等式：和差化积的图像验证",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>求证：对任意角 $\\theta$，"
                    "$\\sin(\\theta+60^\\circ)+\\sin(\\theta-60^\\circ)=\\sin\\theta$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>用两角和与差的正弦公式展开左边；</li>"
                    "<li>合并化简，证明等于右边；</li>"
                    "<li>拖动滑块在图像上逐点验证恒等式。</li></ol>"),
        "answerLabel": "证明结论",
        "answer": (f"左边 $= 2\\sin\\theta\\cos60^\\circ = "
                   f"2\\sin\\theta\\times\\dfrac12 = \\sin\\theta$ = 右边，恒等式成立"),
    }
    steps = [
        {"title": "展开左边（两角和差公式）",
         "content": ("<p>由 $\\sin(\\alpha\\pm\\beta)=\\sin\\alpha\\cos\\beta"
                     "\\pm\\cos\\alpha\\sin\\beta$：</p>"
                     "<p class='text-center'>$$ \\sin(\\theta+60^\\circ)="
                     "\\sin\\theta\\cos60^\\circ+\\cos\\theta\\sin60^\\circ $$</p>"
                     "<p class='text-center'>$$ \\sin(\\theta-60^\\circ)="
                     "\\sin\\theta\\cos60^\\circ-\\cos\\theta\\sin60^\\circ $$</p>")},
        {"title": "相加合并",
         "content": ("<p>两式相加，$\\cos\\theta\\sin60^\\circ$ 项恰好抵消：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ \\text{左边}=2\\sin\\theta\\cos60^\\circ "
                     "=2\\sin\\theta\\times\\frac12=\\sin\\theta $$</div>")},
        {"title": "得证",
         "content": ("<p>左边 $=\\sin\\theta=$ 右边，恒等式对<b>任意角 $\\theta$</b> 成立。</p>"
                     "<p>它也可看作<b>和差化积</b>的特例："
                     "$\\sin P+\\sin Q=2\\sin\\frac{P+Q}{2}\\cos\\frac{P-Q}{2}$，"
                     "取 $P=\\theta+60^\\circ,Q=\\theta-60^\\circ$ 即得。</p>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：红线与蓝线是把 $\\sin\\theta$ 左右平移 $60^\\circ$ 得到的两条曲线，"
                     "在任何 $\\theta$ 处，<b>红、蓝两点的纵坐标之和</b>（读数\"两者之和\"）"
                     "都与绿线上的 $\\sin\\theta$ <b>完全相等</b>，检验灯恒绿。"
                     "这说明恒等式是<b>逐点成立的函数等式</b>，不只是个别角度的巧合。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
REGISTRY = {
    "arithmetic": build_arithmetic,
    "geometric": build_geometric,
    "telescope": build_telescope,
    "offset_sum": build_offset_sum,
    "recurrence": build_recurrence,
    "sin_wave": build_sin_wave,
    "sas_triangle": build_sas_triangle,
    "identity": build_identity,
}
SEEDS = list(REGISTRY)


def main(argv):
    # 统一入口（edulab/shared/skillkit.py）：
    #   python generate.py list | all <目录> | random [seed] [输出] | <key> [输出]
    return cli(
        REGISTRY, doc=__doc__, seeds=SEEDS,
        validate=required_sections("lesson", "steps", "board", min_steps=3),
        template_name="board.html", token=PLACEHOLDER,
        index="高中数学 · 数列与三角 · 交互课件", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
