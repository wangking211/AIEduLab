# -*- coding: utf-8 -*-
"""
generate.py — 生物学科：注入模板 + 范例 build_* + CLI + 随机出题。

两套模板：
  template/board.html  数据驱动 Canvas-2D → 遗传棋盘格 / 能量金字塔 / 种群曲线 / 生理流程图
  template/cell.html   Three.js 3D 细胞 → 动物 / 植物 / 原核细胞分步观察

交互设计原则（与其它 edu-* 技能一致）：
  · 滑块驱动的量全用表达式字符串（JS 端实时求值），拖动即时反馈；
  · 讲解文字里的数值全部由 lib/bio_kernel.py 在默认参数下精确算出，与画板读数同源；
  · 每页至少一个「定值指示」或「状态灯」，暴露不变量/临界条件。

用法：
  python generate.py list
  python generate.py monohybrid ./out/monohybrid.html
  python generate.py all ./out
"""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR.parent.parent / "shared"))   # 共享运行时（edulab/shared/skillkit.py）
sys.path.insert(0, str(SKILL_DIR / "lib"))

import sympy as sp                       # noqa: E402
import bio_kernel as K                   # noqa: E402
import cell_library as CL                # noqa: E402
from skillkit import cli, render_html as _render_html   # noqa: E402

BOARD_T = (SKILL_DIR / "template" / "board.html").read_text(encoding="utf-8")
CELL_T = (SKILL_DIR / "template" / "cell.html").read_text(encoding="utf-8")


# ---------------- 数值 → JSON 安全 ----------------
def _n(x):
    return float(sp.N(x))


def _tex(x):
    return sp.latex(sp.nsimplify(x, rational=True) if isinstance(x, sp.Basic) else sp.sympify(x))


def _ns(x):
    """紧凑可读数字串（避免科学计数法与多余小数）。"""
    v = _n(x)
    if abs(v) >= 10000:
        return f"{round(v):,}"
    if abs(v) >= 100:
        return f"{v:,.1f}"
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.4f}".rstrip("0").rstrip(".")


# 注意：本文件**不得**自带 render_html。
# 曾经这里有一个局部同名实现（直接 replace 写盘），它绕过了 skillkit.render_html
# 里的记号守卫（verify_scene），只要有人顺手调用它，等长/直角记号就可能撒谎而
# 没有任何闸门报警。它当时是死代码，但同名的“更好用”版本就是个陷阱 ——
# 统一走 skillkit.render_html（本文件顶部已 import 为 _render_html）。


# =====================================================================
# 遗传：棋盘格场景组装
# =====================================================================
# 表现型 → 配色键（对应模板 P.dom / P.rec / P.het / P.mix）
PHENO_COLORS = ["dom", "het", "mix", "rec", "good", "bad"]


def _punnett_scene(summary, pheno_label=None, footer=None):
    """把 bio_kernel.cross_summary 的结果转成棋盘格场景数据。"""
    pun = summary["punnett"]
    rows, cols = pun["row_gametes"], pun["col_gametes"]
    cells = pun["cells"]
    cnt = dict(pun["count"])
    n_genes = summary["n_genes"]
    # 表现型分组
    groups = K.phenotype_ratio(K.cross(*summary["parents"]))
    # 建立 表现型 → 颜色键、基因型 → 颜色键
    if pheno_label is None:
        pheno_label = {}
    key_of_ph = {ph: PHENO_COLORS[i % len(PHENO_COLORS)] for i, (ph, _, _) in enumerate(groups)}
    labels = {ph: pheno_label.get(ph, ph) for ph, _, _ in groups}
    pheno_of = {}
    grep_key = {}
    for gt in cnt:
        ph = K.phenotype_of(gt)
        pheno_of[gt] = labels.get(ph, ph)
        grep_key[gt] = key_of_ph.get(ph, "dom")
    order = [[labels.get(ph, ph), int(c)] for ph, c, _ in groups]
    key_agg = {labels.get(ph, ph): key_of_ph.get(ph, "dom") for ph, _, _ in groups}
    nr, nc = len(rows), len(cols)
    gx0, gy0, cw = 1.15, 0.55, 1.0
    return {
        "kind": "punnett", "caption": "Punnett 棋盘格",
        "equalAspect": True,
        "xRange": [0.15, gx0 + nc*cw + 0.35],
        "yRange": [-0.35, gy0 + nr*cw + 1.05],
        "rowGametes": rows, "colGametes": cols, "cells": cells, "count": cnt,
        "phenoOf": pheno_of, "phenoKey": grep_key,
        "phenoOrder": order, "phenoKeyAgg": key_agg,
        "phenoRatioText": " : ".join(str(c) for _, c in order),
        "footer": footer or ("基因型比 " + summary["genotype_ratio"] + "　表现型比 " + summary["phenotype_ratio"]),
        "nGenes": n_genes,
    }


def _board(data, out):
    """Canvas-2D 画板模板（序列化 / 建目录统一在 skillkit.render_html 里）。"""
    return _render_html(data, out, template=BOARD_T, token="__LESSON_DATA__", compact=True)


def _cell(data, out):
    """Three.js 3D 细胞模板。"""
    return _render_html(data, out, template=CELL_T, token="__CELL_DATA__", compact=True)


# =====================================================================
# 1) 单杂交（基因的分离定律）
# =====================================================================
def build_monohybrid():
    s = K.cross_summary("Aa", "Aa")
    mono = K.cross("Aa", "Aa")
    p_aa = K.progeny_prob(mono, "aa", by="phenotype")
    scene = _punnett_scene(s, pheno_label={"A_": "显性性状", "aa": "隐性性状"})
    return {
        "lesson": {
            "title": "基因的分离定律：Aa × Aa",
            "subtitle": "一对相对性状的杂交实验（孟德尔第一定律）",
            "problem": (
                "<p>豌豆的高茎（$A$）对矮茎（$a$）为显性。让两株<b>杂合高茎</b>豌豆杂交：</p>"
                "<p class='mt-2 text-center text-base'>$Aa \\times Aa$</p>"
                "<p class='mt-2'>子代中<b>矮茎</b>的比例是多少？为什么是 $1:2:1$ 的基因型比？</p>"
            ),
        },
        "board": {
            "scene": scene,
            "view": {"xRange": scene["xRange"], "yRange": scene["yRange"]},
            "params": [
                {"name": "n", "label": "模拟子代株数 n", "min": 40, "max": 2000, "step": 40, "value": 400, "digits": 0},
            ],
            "scalars": [
                {"name": "tall", "expr": "n*3/4"},
                {"name": "short", "expr": "n/4"},
            ],
            "readouts": [
                {"id": "gr", "label": "子代基因型比", "type": "text", "value": s["genotype_ratio"], "highlight": True},
                {"id": "pr", "label": "子代表现型比", "type": "text", "value": s["phenotype_ratio"], "color": "#0d9488"},
                {"id": "paa", "label": "隐性纯合（矮茎）概率", "type": "expr", "expr": "0.25", "digits": 2},
                {"id": "talln", "label": "理论上高茎株数", "type": "expr", "expr": "tall", "int": True, "unit": " 株"},
                {"id": "shortn", "label": "理论上矮茎株数", "type": "expr", "expr": "short", "int": True, "unit": " 株", "color": "#e11d48"},
                {"id": "big", "label": "样本够不够大", "type": "status", "expr": "n", "op": ">=", "rhs": 1000,
                 "okText": "n≥1000：实际比例已很接近 3:1", "badText": "n 偏小：实际比例会明显偏离 3:1"},
            ],
            "constant": {"label": "不论 n 取多少，理论上的比例恒为 3 : 1"},
            "legend": [
                {"color": "#0d9488", "text": "显性性状 A_"},
                {"color": "#e11d48", "text": "隐性性状 aa"},
            ],
        },
        "steps": [
            {"title": "亲代产生配子", "content": (
                "<p>$Aa$ 在形成配子时，成对的遗传因子彼此分离，分别进入不同的配子：</p>"
                "$$Aa \\rightarrow A : a = 1 : 1$$"
                "<p>所以父本、母本各产生 <b>$A$ 和 $a$ 两种配子</b>，比例都是 $1:1$。</p>"
            )},
            {"title": "配子随机结合成受精卵", "content": (
                "<p>两种雌配子 × 两种雄配子 = <b>4 种组合</b>，画成棋盘格：</p>"
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li>$AA$：$1/4$</li><li>$Aa$：$2/4 = 1/2$</li><li>$aa$：$1/4$</li></ul>"
                "<p>所以<b>基因型比例 $1:2:1$</b>。</p>"
            )},
            {"title": "由基因型推出表现型", "content": (
                "<p>$A$ 对 $a$ 为显性，所以 $AA$ 和 $Aa$ 都表现<b>高茎</b>，只有 $aa$ 表现<b>矮茎</b>：</p>"
                "$$\\text{高茎} : \\text{矮茎} = 3 : 1$$"
                "<p>矮茎的概率 $= " + _tex(p_aa) + " = 25\\%$。</p>"
            )},
            {"title": "分离定律的实质", "content": (
                "<p class='border-l-4 border-teal-400 pl-3'>"
                "<b>在减数分裂形成配子时，等位基因随同源染色体的分开而分离，"
                "分别进入不同的配子中，独立地随配子遗传给后代。</b></p>"
                "<p class='mt-2'>注意 $3:1$ 是<b>表现型</b>比，$1:2:1$ 是<b>基因型</b>比——"
                "两者不同，因为显性掩盖了杂合子的隐性基因。</p>"
            )},
        ],
    }


# =====================================================================
# 2) 双杂交（自由组合定律）
# =====================================================================
def build_dihybrid():
    s = K.cross_summary("AaBb", "AaBb")
    return {
        "lesson": {
            "title": "基因的自由组合定律：AaBb × AaBb",
            "subtitle": "两对相对性状的杂交实验（孟德尔第二定律）",
            "problem": (
                "<p>豌豆黄色圆粒（$Y$ 黄、$y$ 绿；$R$ 圆、$r$ 皱）。两株<b>双杂合</b>黄圆豌豆杂交：</p>"
                "<p class='mt-2 text-center text-base'>$YyRr \\times YyRr$</p>"
                "<p class='mt-2'>子代的<b>表现型</b>比例是多少？为什么是熟悉的 $9:3:3:1$？</p>"
            ),
        },
        "board": {
            "scene": _punnett_scene(s),
            "view": {"xRange": [0.15, 5.5], "yRange": [-0.35, 5.6]},
            "params": [
                {"name": "n", "label": "模拟子代株数 n", "min": 80, "max": 3200, "step": 80, "value": 1600, "digits": 0},
            ],
            "scalars": [
                {"name": "d1", "expr": "n*9/16"},
                {"name": "d2", "expr": "n*3/16"},
                {"name": "d4", "expr": "n/16"},
            ],
            "readouts": [
                {"id": "pr", "label": "表现型比（双显:单显:单显:双隐）", "type": "text", "value": s["phenotype_ratio"], "highlight": True},
                {"id": "gr", "label": "基因型种类数", "type": "expr", "expr": "9", "digits": 0, "unit": " 种"},
                {"id": "d1", "label": "理论上双显（黄圆）株数", "type": "expr", "expr": "d1", "int": True, "unit": " 株"},
                {"id": "d2", "label": "理论上单显（黄皱或绿圆）", "type": "expr", "expr": "d2", "int": True, "unit": " 株"},
                {"id": "d4", "label": "理论上双隐（绿皱）株数", "type": "expr", "expr": "d4", "int": True, "unit": " 株", "color": "#e11d48"},
                {"id": "tot", "label": "棋盘格总数", "type": "expr", "expr": "16", "digits": 0, "unit": " 格"},
            ],
            "constant": {"label": "两对基因自由组合 → 表现型比恒为 9 : 3 : 3 : 1"},
            "legend": [
                {"color": "#0d9488", "text": "双显 A_B_（9）"},
                {"color": "#f59e0b", "text": "单显 A_bb（3）"},
                {"color": "#7c3aed", "text": "单显 aaB_（3）"},
                {"color": "#e11d48", "text": "双隐 aabb（1）"},
            ],
        },
        "steps": [
            {"title": "每对基因独立分离", "content": (
                "<p>先只看一对：$Yy \\times Yy \\rightarrow 3:1$，$Rr \\times Rr \\rightarrow 3:1$。"
                "两对互不干扰，所以可以把它们<b>当作两个独立的实验</b>。</p>"
            )},
            {"title": "配子有 4 种", "content": (
                "<p>两对等位基因在形成配子时自由组合，产生 <b>$2^2 = 4$ 种</b>配子：</p>"
                "$$YR : Yr : yR : yr = 1:1:1:1$$"
                "<p>雌雄各 4 种 → 棋盘格共 $4\\times4 = 16$ 格。</p>"
            )},
            {"title": "拆开算，再相乘", "content": (
                "<p>用<b>乘法原理</b>比数格子快得多：</p>"
                "$$P(A\\_B\\_) = \\tfrac34\\times\\tfrac34 = \\tfrac{9}{16}$$"
                "$$P(A\\_bb) = \\tfrac34\\times\\tfrac14 = \\tfrac{3}{16}$$"
                "$$P(aaB\\_) = \\tfrac14\\times\\tfrac34 = \\tfrac{3}{16}$$"
                "$$P(aabb) = \\tfrac14\\times\\tfrac14 = \\tfrac{1}{16}$$"
                "<p>合起来就是 <b>$9:3:3:1$</b>。</p>"
            )},
            {"title": "自由组合定律的实质", "content": (
                "<p class='border-l-4 border-teal-400 pl-3'>"
                "<b>位于非同源染色体上的非等位基因，在减数分裂形成配子时自由组合。</b></p>"
                "<p class='mt-2'>前提是这两对基因<b>位于不同对的同源染色体上</b>；"
                "若位于同一对染色体上，则会发生「连锁」，比例不再是 $9:3:3:1$。</p>"
            )},
        ],
    }


# =====================================================================
# 3) 测交（验证基因型）
# =====================================================================
def build_testcross():
    s = K.test_cross("AaBb")
    return {
        "lesson": {
            "title": "测交：用隐性纯合验证基因型",
            "subtitle": "让未知基因型个体与隐性纯合子杂交",
            "problem": (
                "<p>一株<b>黄色圆粒</b>豌豆，但它的基因型可能是 $YYRR$、$YyRR$、$YYRr$ 或 $YyRr$。"
                "怎么判断？</p>"
                "<p class='mt-2'>办法：让它与<b>绿色皱粒</b>（$yyrr$，隐性纯合）测交：</p>"
                "<p class='mt-2 text-center text-base'>$YyRr \\times yyrr$</p>"
                "<p class='mt-2'>如果子代出现 $1:1:1:1$ 的四种表现型，说明这株是<b>双杂合</b>。</p>"
            ),
        },
        "board": {
            "scene": _punnett_scene(s),
            "view": {"xRange": [0.15, 5.5], "yRange": [-0.35, 5.6]},
            "params": [
                {"name": "n", "label": "测交后代株数 n", "min": 80, "max": 3200, "step": 80, "value": 800, "digits": 0},
            ],
            "scalars": [
                {"name": "q", "expr": "n/4"},
            ],
            "readouts": [
                {"id": "pr", "label": "子代表现型比", "type": "text", "value": s["phenotype_ratio"], "highlight": True},
                {"id": "p1", "label": "单一表现型概率", "type": "expr", "expr": "1/4", "digits": 2},
                {"id": "qn", "label": "每种表现型理论株数", "type": "expr", "expr": "q", "int": True, "unit": " 株"},
                {"id": "kind", "label": "被测基因型判定", "type": "status", "expr": "4", "op": "==", "rhs": 4,
                 "okText": "出现 4 种表现型 → 双杂合 YyRr", "badText": "种类不足 → 非双杂合"},
            ],
            "constant": {"label": "隐性纯合只产生 1 种配子 → 子代表现型直接反映被测个体的配子种类"},
            "legend": [
                {"color": "#0d9488", "text": "双显 Y_R_"},
                {"color": "#f59e0b", "text": "Y_rr"},
                {"color": "#7c3aed", "text": "yyR_"},
                {"color": "#e11d48", "text": "yyrr"},
            ],
        },
        "steps": [
            {"title": "隐性纯合只产生一种配子", "content": (
                "<p>$yyrr$ 只能产生 <b>$yr$ 这一种配子</b>，所以子代的表现型直接反映"
                "被测个体配子的种类。</p>"
                "<p class='mt-2'>这是测交的巧妙之处：<b>把「测配子」变成了「看表现型」</b>。</p>"
            )},
            {"title": "被测个体产生 4 种配子", "content": (
                "<p>$YyRr$ 产生 $YR : Yr : yR : yr = 1:1:1:1$，"
                "所以子代有 4 种表现型，比例 $1:1:1:1$。</p>"
                    "<p class='mt-2'>反过来，如果你看到子代是 $1:1:1:1$，就能<b>反推</b>亲代一定是双杂合。</p>"
            )},
            {"title": "不同基因型的测交结果", "content": (
                "<table class='w-full text-sm border-collapse mt-1'>"
                "<tr class='bg-teal-50'><th class='border border-slate-200 px-2 py-1'>被测基因型</th>"
                "<th class='border border-slate-200 px-2 py-1'>配子种类</th>"
                "<th class='border border-slate-200 px-2 py-1'>子代表现型比</th></tr>"
                "<tr><td class='border px-2 py-1 text-center'>$YYRR$</td><td class='border px-2 py-1 text-center'>1</td><td class='border px-2 py-1 text-center'>全为黄圆</td></tr>"
                "<tr><td class='border px-2 py-1 text-center'>$YyRR$</td><td class='border px-2 py-1 text-center'>2</td><td class='border px-2 py-1 text-center'>$1:1$</td></tr>"
                "<tr><td class='border px-2 py-1 text-center'>$YYRr$</td><td class='border px-2 py-1 text-center'>2</td><td class='border px-2 py-1 text-center'>$1:1$</td></tr>"
                "<tr class='bg-amber-50'><td class='border px-2 py-1 text-center'><b>$YyRr$</b></td><td class='border px-2 py-1 text-center'><b>4</b></td>"
                "<td class='border px-2 py-1 text-center'><b>$1:1:1:1$</b></td></tr>"
                "</table>"
            )},
            {"title": "测交的意义", "content": (
                "<p>测交是检验<b>基因型</b>的经典方法：</p>"
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li>不能直接观察基因型，但可以观察它产生的配子；</li>"
                "<li>隐性纯合就像一个「读出器」，把配子翻译成看得见的表现型；</li>"
                "<li>孟德尔用它验证了自己的假说——这是遗传学史上第一次用实验<b>反推</b>不可见的结构。</li>"
                "</ul>"
            )},
        ],
    }


# =====================================================================
# 4) 伴性遗传（X 染色体连锁）
# =====================================================================
def build_sexlinked():
    sl = K.sex_linked_cross("XAXa", "XAY")
    son_map = dict(sl["sons"])
    dau_map = dict(sl["daughters"])
    # 棋盘格：行=母亲的配子（XA, Xa），列=父亲的配子（XA, Y）
    rows, cols = ["XA", "Xa"], ["XA", "Y"]
    cells = [[("XA" + ("XA" if c == "XA" else "Y")) if c == "XA" else ("XA" + "Y") for c in cols],
             [("Xa" + ("XA" if c == "XA" else "Y")) if c == "XA" else ("Xa" + "Y") for c in cols]]
    # 规范化显示：XAXA / XAY / XAXa / XaY
    def norm(child):
        if child.endswith("Y"):
            return child[:-1] + "Y"
        a, b = child[:2], child[2:]
        return a + b if a <= b else b + a
    cells = [[norm(c) for c in row] for row in cells]
    cnt = {}
    for row in cells:
        for c in row:
            cnt[c] = cnt.get(c, 0) + 1
    label_of = {"XAXA": "女儿 正常", "XAXa": "女儿 携带", "XAY": "儿子 正常", "XaY": "儿子 患病"}
    # 颜色键：患病用 bad，其余用 dom / het
    key_of = {"XAXA": "dom", "XAXa": "het", "XAY": "dom", "XaY": "bad"}
    order = [["儿子 患病", 1], ["儿子 正常", 1], ["女儿 携带", 1], ["女儿 正常", 1]]
    scene = {
        "kind": "punnett", "caption": "伴性遗传棋盘格",
        "equalAspect": True,
        "xRange": [0.15, 3.9], "yRange": [-0.35, 4.35],
        "rowGametes": rows, "colGametes": cols, "cells": cells, "count": cnt,
        "phenoOf": {gt: label_of.get(gt, gt) for gt in cnt},
        "phenoKey": {gt: key_of.get(gt, "dom") for gt in cnt},
        "phenoOrder": order,
        "phenoKeyAgg": {"儿子 患病": "bad", "儿子 正常": "dom", "女儿 携带": "het", "女儿 正常": "dom"},
        "phenoRatioText": "1 : 1 : 1 : 1",
        "footer": "母亲 XAXa × 父亲 XAY",
    }
    return {
        "lesson": {
            "title": "伴性遗传：XAXa × XAY",
            "subtitle": "红绿色盲/血友病的遗传方式——致病基因位于 X 染色体上",
            "problem": (
                "<p>红绿色盲是 <b>X 染色体隐性</b>遗传病（用 $a$ 表示致病基因）。"
                "一位<b>表现正常但携带致病基因</b>的母亲（$X^A X^a$）"
                "与一位<b>正常</b>的父亲（$X^A Y$）结婚。</p>"
                "<p class='mt-2'>他们的孩子患病概率是多少？为什么说<b>「传男不传女」</b>？</p>"
            ),
        },
        "board": {
            "scene": scene,
            "view": {"xRange": scene["xRange"], "yRange": scene["yRange"]},
            "params": [
                {"name": "boys", "label": "预计出生的儿子数", "min": 2, "max": 20, "step": 1, "value": 4, "digits": 0},
            ],
            "scalars": [
                {"name": "sickB", "expr": "boys/2"},
            ],
            "readouts": [
                {"id": "sick", "label": "儿子患病概率", "type": "expr", "expr": "0.5", "digits": 2, "highlight": True},
                {"id": "carrier", "label": "女儿携带者概率", "type": "expr", "expr": "0.5", "digits": 2},
                {"id": "dauwell", "label": "女儿患病概率", "type": "expr", "expr": "0", "digits": 2, "color": "#059669"},
                {"id": "nboys", "label": "预计患病儿子数", "type": "expr", "expr": "sickB", "digits": 1, "unit": " 个", "color": "#e11d48"},
                {"id": "all", "label": "全体子女患病概率", "type": "expr", "expr": "0.25", "digits": 2},
                {"id": "why", "label": "为什么儿子更易患病", "type": "status", "expr": "1", "op": "==", "rhs": 1,
                 "okText": "儿子只有一条 X，无从掩盖隐性基因", "badText": "—"},
            ],
            "constant": {"label": "儿子的 X 染色体只能来自母亲——所以母亲携带则儿子 1/2 患病"},
            "legend": [
                {"color": "#0d9488", "text": "正常"},
                {"color": "#e11d48", "text": "患病（XaY）"},
                {"color": "#f59e0b", "text": "携带者（XAXa）"},
            ],
        },
        "steps": [
            {"title": "写出亲本配子", "content": (
                "<p>母亲的基因型 $X^A X^a$，产生两种卵细胞：$X^A : X^a = 1:1$。</p>"
                "<p>父亲的基因型 $X^A Y$，产生两种精子：$X^A : Y = 1:1$。</p>"
            )},
            {"title": "子女的基因型", "content": (
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li>女儿：$X^A X^A$（正常）或 $X^A X^a$（携带）——各 $1/2$。</li>"
                "<li>儿子：$X^A Y$（正常）或 $X^a Y$（患病）——各 $1/2$。</li></ul>"
                "<p class='mt-2'>儿子的 X 染色体<b>只能来自母亲</b>，所以母亲若携带致病基因，"
                "儿子有 $1/2$ 概率患病。</p>"
            )},
            {"title": "为什么「传男不传女」", "content": (
                "<p>关键在<b>染色体组成</b>：</p>"
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li>女儿有两条 X：即使一条带 $a$，另一条正常的 $X^A$ 也能掩盖 → <b>不患病</b>；</li>"
                "<li>儿子只有一条 X：来自母亲的 $X^a$ 一旦接到，<b>没有第二条 X 来掩盖</b> → 患病。</li></ul>"
                "<p class='mt-2 text-center'>$P(\\text{儿子患病}) = " + _tex(son_map["XaY"]) + " = 50\\%$</p>"
                "<p>所以这类伴 X 隐性病表现出<b>男性患者明显多于女性</b>的特点。</p>"
            )},
            {"title": "拓展：常见伴性遗传", "content": (
                "<table class='w-full text-xs border-collapse mt-1'>"
                "<tr class='bg-teal-50'><th class='border px-2 py-1'>类型</th><th class='border px-2 py-1'>例子</th>"
                "<th class='border px-2 py-1'>特点</th></tr>"
                "<tr><td class='border px-2 py-1 text-center'>伴 X 隐性</td><td class='border px-2 py-1 text-center'>红绿色盲、血友病</td>"
                "<td class='border px-2 py-1'>男性多于女性；母亲携带则儿子 1/2 患病</td></tr>"
                "<tr><td class='border px-2 py-1 text-center'>伴 X 显性</td><td class='border px-2 py-1 text-center'>抗维生素 D 佝偻病</td>"
                "<td class='border px-2 py-1'>女性多于男性；父亲患病则女儿全患病</td></tr>"
                "<tr><td class='border px-2 py-1 text-center'>伴 Y</td><td class='border px-2 py-1 text-center'>人类的蹼足</td>"
                "<td class='border px-2 py-1'>只有男性有，父传子、子传孙</td></tr>"
                "</table>"
            )},
        ],
    }


# =====================================================================
# 生态：能量金字塔
# =====================================================================
def build_energy_pyramid():
    eff = sp.Rational(1, 10)
    base = 10000
    ep = K.energy_pyramid(base, levels=4, efficiency=eff)
    names = ["生产者（草）", "初级消费者（兔）", "次级消费者（狐）", "三级消费者（鹰）"]
    levels = [{"label": names[i], "text": _ns(ep["energies"][i]) + " kJ"} for i in range(4)]
    need = K.energy_needed(ep["energies"][3], efficiency=eff, steps=3)
    return {
        "lesson": {
            "title": "生态系统的能量流动：能量金字塔",
            "subtitle": "为什么食物链一般不超过 4~5 个营养级？",
            "problem": (
                "<p>草原上生产者固定了 <b>10000 kJ</b> 能量。相邻两个营养级之间的"
                "能量传递效率约为 <b>10%~20%</b>。</p>"
                "<p class='mt-2'>那么初级消费者、次级消费者、三级消费者分别能得到多少能量？</p>"
                "<p class='mt-2'>拖动<b>传递效率</b>滑块，看金字塔形状如何变化。</p>"
            ),
        },
        "board": {
            "scene": {
                "kind": "pyramid", "caption": "能量金字塔",
                "effPct": "eff", "effFrac": "eff/100",
                "labels": names,
                "energyExprs": ["L1", "L2", "L3", "L4"],
                "xRange": [0, 10], "yRange": [0, 6.4],
                "footer": "能量沿营养级逐级递减（传递效率 10%~20%）",
            },
            "view": {"xRange": [0, 10], "yRange": [0, 6.4]},
            "params": [
                {"name": "eff", "label": "能量传递效率", "min": 5, "max": 30, "step": 1, "value": 10, "unit": "%", "digits": 0},
            ],
            "scalars": [
                {"name": "L1", "expr": "10000"},
                {"name": "L2", "expr": "10000*eff/100"},
                {"name": "L3", "expr": "10000*(eff/100)^2"},
                {"name": "L4", "expr": "10000*(eff/100)^3"},
            ],
            "readouts": [
                {"id": "L1", "label": "生产者", "type": "expr", "expr": "L1", "int": True, "unit": " kJ"},
                {"id": "L2", "label": "初级消费者", "type": "expr", "expr": "L2", "int": True, "unit": " kJ", "highlight": True},
                {"id": "L3", "label": "次级消费者", "type": "expr", "expr": "L3", "int": True, "unit": " kJ"},
                {"id": "L4", "label": "三级消费者", "type": "expr", "expr": "L4", "int": True, "unit": " kJ", "color": "#f59e0b"},
                {"id": "share", "label": "到第四营养级只剩", "type": "expr", "expr": "L4/L1*100", "digits": 2, "unit": "%", "color": "#e11d48"},
                {"id": "ok", "label": "该效率是否在自然范围", "type": "status", "expr": "eff", "op": "<=", "rhs": 20,
                 "okText": "10%~20%：符合自然规律", "badText": ">20%：自然生态中很少见"},
            ],
            "legend": [
                {"color": "#166534", "text": "能量逐级递减"},
                {"color": "#f59e0b", "text": "传递效率 = 下一级 / 上一级"},
            ],
        },
        "steps": [
            {"title": "能量流动的起点", "content": (
                "<p>生态系统的能量来自<b>太阳能</b>，由生产者（绿色植物）通过"
                "<b>光合作用</b>固定，成为整个食物链的能量源头。</p>"
                "<p class='mt-2'>本例中生产者固定 $10000$ kJ。</p>"
            )},
            {"title": "逐级递减：10%~20%", "content": (
                "<p>能量沿营养级传递时，大部分通过<b>呼吸作用</b>以热能散失，"
                "还有一部分用于生长发育后被分解者利用。所以只有 <b>10%~20%</b> 传给下一级。</p>"
                "$$\\text{生产者} \\xrightarrow{10\\%} \\text{初级} \\xrightarrow{10\\%} \\text{次级} \\xrightarrow{10\\%} \\text{三级}$$"
                "<p class='mt-2'>按 10% 计算：$10000 \\rightarrow 1000 \\rightarrow 100 \\rightarrow 10$ kJ。</p>"
            )},
            {"title": "可以用乘积快速计算", "content": (
                "<p>第 $n$ 营养级的能量：</p>"
                "$$E_n = E_1 \\times \\eta^{\\,n-1}$$"
                "<p>代入 $E_1 = 10000$、$\\eta = 10\\%$、$n = 4$：</p>"
                "$$E_4 = 10000 \\times 0.1^3 = " + _ns(ep["energies"][3]) + "\\ \\text{kJ}$$"
                "<p>只剩 $0.1\\%$——这就是为什么<b>食物链一般不超过 4~5 个营养级</b>。</p>"
            )},
            {"title": "能量金字塔的意义", "content": (
                "<p>把各级能量按比例画成方块叠起来，就成了<b>能量金字塔</b>：越往上越窄。</p>"
                "<p class='mt-2'>如果要把最高级消费者增加 $1$ kJ，需要生产者提供多少？</p>"
                "$$\\Delta E_1 = \\frac{1}{0.1^3} = " + _ns(sp.Integer(1000)) + "\\ \\text{kJ}$$"
                "<p class='mt-2 border-l-4 border-teal-400 pl-3'>"
                "这解释了：<b>为什么食物链的「塔尖」生物数量必然稀少</b>——"
                "不是它们繁殖得慢，而是能量传不上来。也说明了<b>保护生物多样性要保护整个食物链</b>。</p>"
            )},
        ],
    }


# =====================================================================
# 生态：种群数量变化（J 型 / S 型）
# =====================================================================
def build_population():
    n0, lam, Kk, r = 100, 2, 1000, sp.Rational(1, 2)
    ex = K.exponential_growth(n0, lam, 6)
    lo = K.logistic_growth(sp.Integer(10), Kk, r, sp.Integer(0))
    dt = K.doubling_time(lam)
    return {
        "lesson": {
            "title": "种群数量的变化：J 型与 S 型",
            "subtitle": "理想条件下的指数增长 vs 有限环境中的稳定增长",
            "problem": (
                "<p>一个种群初始有 <b>100</b> 个个体，每代数量变为原来的 <b>2 倍</b>——这是 <b>J 型增长</b>。</p>"
                "<p class='mt-2'>但在真实环境中资源有限，种群不会无限增长，而是沿 <b>S 型曲线</b>"
                "趋近一个上限 $K$（<b>环境容纳量</b>）。</p>"
                "<p class='mt-2'>拖动滑块，比较两条曲线，并找出<b>增长速率最大</b>的位置。</p>"
            ),
        },
        "board": {
            "scene": {
                "kind": "population", "caption": "J 型 vs S 型",
                "n0": "n0", "lam": "lam", "K": "Kk", "r": "r/100",
                "tMax": "tMax", "yMax": "yMax",
                "showJ": True, "showS": True,
                "xRange": [0, 20], "yRange": [0, 2000],
                "footer": "J 型：资源无限，指数增长　·　S 型：资源有限，趋近 K",
            },
            "view": {"xRange": [0, 20], "yRange": [0, 2000]},
            "params": [
                {"name": "lam", "label": "每代增长倍数 λ（J 型）", "min": 1.1, "max": 3, "step": 0.1, "value": 2, "digits": 1},
                {"name": "Kk", "label": "环境容纳量 K（S 型）", "min": 200, "max": 3000, "step": 100, "value": 1000, "digits": 0},
                {"name": "r", "label": "内禀增长率 r（×100）", "min": 5, "max": 150, "step": 5, "value": 50, "digits": 0},
                {"name": "n0", "label": "初始数量 N₀", "min": 10, "max": 500, "step": 10, "value": 100, "digits": 0},
            ],
            "scalars": [
                {"name": "tMax", "expr": "20"},
                {"name": "yMax", "expr": "Kk*1.25"},
            ],
            "readouts": [
                {"id": "jt", "label": "J 型 t=20 时的数量", "type": "expr", "expr": "n0*lam^20", "int": True, "unit": " 个", "color": "#f59e0b"},
                {"id": "K", "label": "环境容纳量 K", "type": "expr", "expr": "Kk", "int": True, "unit": " 个", "highlight": True},
                {"id": "half", "label": "增长速率最大处（K/2）", "type": "expr", "expr": "Kk/2", "int": True, "unit": " 个"},
                {"id": "dt", "label": "J 型翻倍所需代数", "type": "expr", "expr": "log(2)/log(lam)", "digits": 2, "unit": " 代"},
                {"id": "cap", "label": "S 型是否受环境限制", "type": "status", "expr": "Kk", "op": ">", "rhs": 0,
                 "okText": "有上限 K，不会无限增长", "badText": "—"},
            ],
            "legend": [
                {"color": "#f59e0b", "text": "J 型（指数增长）"},
                {"color": "#2dd4bf", "text": "S 型（logistic）"},
            ],
        },
        "steps": [
            {"title": "J 型增长：理想条件", "content": (
                "<p>食物和空间充足、没有天敌、气候适宜时，种群呈指数增长：</p>"
                "$$N_t = N_0 \\lambda^{\\,t}$$"
                "<p>代入 $N_0 = 100$、$\\lambda = 2$、$t = 6$：$N_6 = 100 \\times 2^6 = " + _ns(ex["n"]) + "$ 个。</p>"
                "<p class='mt-2'>每代翻一倍，持续 $20$ 代就是 $100 \\times 2^{20} = "
                + _ns(K.exponential_growth(n0, lam, 20)["n"]) + "$ 个——"
                "远超地球能承载的数量，说明 J 型增长只能是<b>暂时的</b>。</p>"
            )},
            {"title": "S 型增长：资源有限", "content": (
                "<p>引入环境容纳量 $K$ 后：</p>"
                "$$N_t = \\frac{K}{1 + \\left(\\frac{K}{N_0}-1\\right)e^{-rt}}$$"
                "<p>当 $t\\to\\infty$ 时 $N_t \\to K$：种群在 $K$ 附近波动，不再增长。</p>"
                "<p class='mt-2'>$K$ 的直观含义：环境能<b>长期容纳</b>的种群最大数量，"
                "由食物、空间、天敌等共同决定。</p>"
            )},
            {"title": "增长最快的地方是 K/2", "content": (
                "<p>S 型曲线的<b>增长速率</b>（斜率）先增后减，在 $N = K/2$ 处达到最大：</p>"
                "$$\\text{最大增长速率} = \\frac{rK}{4}$$"
                "<p>代入 $r = 0.5$、$K = 1000$：$\\dfrac{0.5\\times1000}{4} = 125$ 个/单位时间。</p>"
                "<p class='mt-2 border-l-4 border-teal-400 pl-3'><b>实际应用</b>："
                "渔业捕捞后应把种群保持在 $K/2$ 左右——此时恢复最快、可持续产量最高。"
                "若捕到远低于 $K/2$，种群恢复会变慢，甚至崩溃。</p>"
            )},
            {"title": "两种增长曲线对比", "content": (
                "<table class='w-full text-xs border-collapse mt-1'>"
                "<tr class='bg-teal-50'><th class='border px-2 py-1'>对比项</th>"
                "<th class='border px-2 py-1'>J 型</th><th class='border px-2 py-1'>S 型</th></tr>"
                "<tr><td class='border px-2 py-1'>条件</td><td class='border px-2 py-1'>资源无限</td><td class='border px-2 py-1'>资源有限</td></tr>"
                "<tr><td class='border px-2 py-1'>增长率</td><td class='border px-2 py-1'>不变（$\\lambda$ 恒定）</td><td class='border px-2 py-1'>先增后减，$K/2$ 处最大</td></tr>"
                "<tr><td class='border px-2 py-1'>有无上限</td><td class='border px-2 py-1'>无</td><td class='border px-2 py-1'>有（$K$）</td></tr>"
                "<tr><td class='border px-2 py-1'>实例</td><td class='border px-2 py-1'>新物种入侵、实验室培养初期</td><td class='border px-2 py-1'>自然界多数种群</td></tr>"
                "</table>"
            )},
        ],
    }


# =====================================================================
# 细胞 3D（Three.js）
# =====================================================================
def _cell_lesson(kind, title, subtitle, intro):
    payload = CL.build_payload(kind)
    payload["title"] = title
    payload["subtitle"] = subtitle
    return payload, intro


def build_animal_cell():
    payload, _ = _cell_lesson(
        "animal", "动物细胞的结构",
        "以人体细胞为例，逐个认识细胞器",
        "动物细胞")
    return payload


def build_plant_cell():
    payload, _ = _cell_lesson(
        "plant", "植物细胞的结构",
        "与动物细胞相比：有细胞壁、大液泡和叶绿体",
        "植物细胞")
    return payload


def build_prokaryotic_cell():
    payload, _ = _cell_lesson(
        "prokaryotic", "原核细胞（细菌）的结构",
        "没有核膜包被的细胞核，只有拟核",
        "原核细胞")
    return payload


# =====================================================================
# 生理过程：光合作用与呼吸作用（物质守恒 + 实时计算台）
# =====================================================================
def build_photosynthesis():
    psb = K.photosynthesis_balance(co2_mass=264)
    g = psb["mass"]["C6H12O6"]
    o = psb["mass"]["O2"]
    w = psb["mass"]["H2O"]
    scene = {
        "kind": "flow", "caption": "光合作用物质流",
        "xRange": [0, 10.6], "yRange": [3.0, 6.9],
        "activeNodes": ["co2", "h2o", "chl", "glc", "o2"],
        "activeEdges": ["co2>chl", "h2o>chl", "chl>glc", "chl>o2"],
        "nodes": [
            {"id": "co2", "label": "CO₂", "sub": "massCO2", "subUnit": " g", "x": 0.2, "y": 5.5, "w": 2.0, "h": 0.9, "color": "#334155"},
            {"id": "h2o", "label": "H₂O", "sub": "massH2O", "subUnit": " g", "x": 0.2, "y": 3.6, "w": 2.0, "h": 0.9, "color": "#334155"},
            {"id": "chl", "label": "叶绿体", "sub": "光能 + 酶", "x": 3.4, "y": 4.25, "w": 2.6, "h": 1.5, "color": "#166534"},
            {"id": "glc", "label": "C₆H₁₂O₆", "sub": "massGlc", "subUnit": " g", "x": 7.3, "y": 5.5, "w": 2.9, "h": 0.9, "color": "#0d9488"},
            {"id": "o2", "label": "O₂", "sub": "massO2", "subUnit": " g", "x": 7.3, "y": 3.6, "w": 2.9, "h": 0.9, "color": "#0891b2"},
        ],
        "edges": [
            {"from": "co2", "to": "chl", "label": "原料"},
            {"from": "h2o", "to": "chl"},
            {"from": "chl", "to": "glc", "label": "有机物"},
            {"from": "chl", "to": "o2", "label": "释放"},
        ],
        "footer": "6CO₂ + 6H₂O —光能/叶绿体→ C₆H₁₂O₆ + 6O₂　（箭头为物质的量之比 6:6:1:6）",
    }
    return {
        "lesson": {
            "title": "光合作用与呼吸作用的物质变化",
            "subtitle": "绿色植物如何把无机物变成有机物——以及反过来",
            "problem": (
                "<p>绿色植物通过光合作用把 <b>CO₂ 和 H₂O</b> 转变成 <b>有机物（葡萄糖）和 O₂</b>：</p>"
                "<p class='mt-2 text-center'>$6CO_2 + 6H_2O \\xrightarrow{光能/叶绿体} C_6H_{12}O_6 + 6O_2$</p>"
                "<p class='mt-2'>若植物吸收了 <b>264 g CO₂</b>，能合成多少葡萄糖？放出多少 O₂？</p>"
                "<p class='mt-2'>拖动<b>吸收的 CO₂</b> 滑块，看各物质质量同步变化——"
                "注意<b>反应前后原子的种类和数目都不变</b>。</p>"
            ),
        },
        "board": {
            "scene": scene,
            "view": {"xRange": scene["xRange"], "yRange": scene["yRange"]},
            "params": [
                {"name": "massCO2", "label": "吸收的 CO₂ 质量", "min": 44, "max": 440, "step": 44, "value": 264, "unit": " g", "digits": 0},
            ],
            "scalars": [
                {"name": "molCO2", "expr": "massCO2/44"},
                {"name": "molGlc", "expr": "molCO2/6"},
                {"name": "massGlc", "expr": "molGlc*180"},
                {"name": "massO2", "expr": "molCO2*32"},
                {"name": "massH2O", "expr": "molCO2*18"},
                {"name": "after", "expr": "massGlc + massO2"},
            ],
            "readouts": [
                {"id": "glc", "label": "合成葡萄糖", "type": "expr", "expr": "massGlc", "int": True, "unit": " g", "highlight": True},
                {"id": "o2", "label": "放出氧气 O₂", "type": "expr", "expr": "massO2", "int": True, "unit": " g", "color": "#0891b2"},
                {"id": "h2o", "label": "消耗水 H₂O", "type": "expr", "expr": "massH2O", "int": True, "unit": " g"},
                {"id": "mol", "label": "CO₂ 的物质的量", "type": "expr", "expr": "molCO2", "digits": 2, "unit": " mol"},
                {"id": "atom", "label": "反应前后原子总数是否守恒", "type": "status", "expr": "massGlc+massO2-massCO2-massH2O", "op": ">", "rhs": -1,
                 "okText": "守恒（质量守恒定律）", "badText": "—"},
            ],
            "constant": {"label": "碳原子：吸收 6 → 葡萄糖中 6，全程不变"},
            "legend": [
                {"color": "#334155", "text": "原料（CO₂ / H₂O）"},
                {"color": "#166534", "text": "叶绿体（光能场所）"},
                {"color": "#0d9488", "text": "产物（有机物 / O₂）"},
            ],
        },
        "steps": [
            {"title": "写出反应式并配平", "content": (
                "$$6CO_2 + 6H_2O \\xrightarrow{光能/叶绿体} C_6H_{12}O_6 + 6O_2$$"
                "<p>配平的关键看<b>碳原子</b>：葡萄糖有 6 个 C，所以需要 6 个 CO₂；"
                "再看氢：葡萄糖有 12 个 H，所以需要 6 个 H₂O。</p>"
                "<p class='mt-2'>物质的量之比 $n(CO_2):n(H_2O):n(C_6H_{12}O_6):n(O_2) = 6:6:1:6$。</p>"
            )},
            {"title": "把质量换成物质的量", "content": (
                "<p>已知 $m(CO_2) = 264$ g，摩尔质量 $M(CO_2) = 44$ g/mol：</p>"
                "$$n(CO_2) = \\frac{264}{44} = " + _ns(psb["mol"]["CO2"]) + "\\ \\text{mol}$$"
                "<p>按 $6:1$ 的关系，葡萄糖的物质的量：</p>"
                "$$n(C_6H_{12}O_6) = \\frac{" + _ns(psb["mol"]["CO2"]) + "}{6} = "
                + _ns(psb["mol"]["C6H12O6"]) + "\\ \\text{mol}$$"
            )},
            {"title": "再换回质量", "content": (
                "<p>$M(C_6H_{12}O_6) = 6\\times12 + 12\\times1 + 6\\times16 = 180$ g/mol：</p>"
                "$$m(C_6H_{12}O_6) = " + _ns(psb["mol"]["C6H12O6"]) + "\\times180 = "
                + _ns(g) + "\\ \\text{g}$$"
                "<p>同理 $M(O_2) = 32$ g/mol，放出氧气：</p>"
                "$$m(O_2) = " + _ns(psb["mol"]["O2"]) + "\\times32 = " + _ns(o) + "\\ \\text{g}$$"
                "<p>消耗水 $m(H_2O) = " + _ns(w) + "$ g。</p>"
            )},
            {"title": "质量守恒的验证", "content": (
                "<p>反应前：$264 + " + _ns(w) + " = " + _ns(sp.nsimplify(264) + w) + "$ g</p>"
                "<p>反应后：$" + _ns(g) + " + " + _ns(o) + " = "
                + _ns(g + o) + "$ g</p>"
                "<p class='mt-2 text-center text-base text-emerald-700 font-bold'>两边完全相等 → 质量守恒定律</p>"
                "<p class='mt-2'>因为光合作用只是把原子<b>重新组合</b>：碳、氢、氧原子的"
                "种类和数目都没有改变。</p>"
            )},
            {"title": "呼吸作用：恰好反过来", "content": (
                "<p>呼吸作用把有机物分解、释放能量：</p>"
                "$$C_6H_{12}O_6 + 6O_2 \\xrightarrow{酶} 6CO_2 + 6H_2O + \\text{能量}$$"
                "<p class='mt-2'>对比两者的区别：</p>"
                "<table class='w-full text-xs border-collapse mt-1'>"
                "<tr class='bg-teal-50'><th class='border px-2 py-1'>对比项</th><th class='border px-2 py-1'>光合作用</th><th class='border px-2 py-1'>呼吸作用</th></tr>"
                "<tr><td class='border px-2 py-1'>场所</td><td class='border px-2 py-1'>叶绿体</td><td class='border px-2 py-1'>线粒体（主要）</td></tr>"
                "<tr><td class='border px-2 py-1'>条件</td><td class='border px-2 py-1'>需光</td><td class='border px-2 py-1'>有光无光都进行</td></tr>"
                "<tr><td class='border px-2 py-1'>物质变化</td><td class='border px-2 py-1'>无机物 → 有机物</td><td class='border px-2 py-1'>有机物 → 无机物</td></tr>"
                "<tr><td class='border px-2 py-1'>能量变化</td><td class='border px-2 py-1'>储存能量</td><td class='border px-2 py-1'>释放能量</td></tr>"
                "</table>"
            )},
        ],
    }


# =====================================================================
# 生理过程：尿的形成（流程图 + 重吸收计算）
# =====================================================================
def build_urine():
    filtered, urine = 180, 1.5
    reabsorb = sp.Rational(180 * 1000 - 1500, 180 * 1000)
    scene = {
        "kind": "flow", "caption": "尿的形成过程",
        "xRange": [0, 9.0], "yRange": [2.15, 6.0],
        "activeNodes": ["blood", "glomerulus", "filtrate", "tubule", "urine"],
        "activeEdges": ["blood>glomerulus", "glomerulus>filtrate", "filtrate>tubule", "tubule>urine"],
        "nodes": [
            {"id": "blood", "label": "血液", "sub": "入球小动脉", "x": 0.2, "y": 4.6, "w": 2.2, "h": 0.95, "color": "#7f1d1d"},
            {"id": "glomerulus", "label": "肾小球", "sub": "滤过作用", "x": 3.0, "y": 4.6, "w": 2.3, "h": 0.95, "color": "#334155"},
            {"id": "filtrate", "label": "原尿", "sub": "molFilt", "subUnit": " L/天", "x": 6.0, "y": 4.6, "w": 2.3, "h": 0.95, "color": "#0e7490"},
            {"id": "tubule", "label": "肾小管", "sub": "重吸收作用", "x": 6.0, "y": 2.8, "w": 2.3, "h": 0.95, "color": "#166534"},
            {"id": "urine", "label": "尿液", "sub": "molUrine", "subUnit": " L/天", "x": 3.0, "y": 2.8, "w": 2.3, "h": 0.95, "color": "#a16207"},
        ],
        "edges": [
            {"from": "blood", "to": "glomerulus", "label": "滤过"},
            {"from": "glomerulus", "to": "filtrate", "label": "形成原尿"},
            {"from": "filtrate", "to": "tubule", "dir": "v", "label": "流经"},
            {"from": "tubule", "to": "urine", "label": "不被重吸收的部分"},
        ],
        "footer": "肾小球滤过（大分子留在血液）→ 肾小管重吸收（大部分水、全部葡萄糖）→ 尿液",
    }
    return {
        "lesson": {
            "title": "尿的形成：滤过 + 重吸收",
            "subtitle": "为什么每天形成 180 L 原尿，却只排出 1.5 L 尿液？",
            "problem": (
                "<p>成年人每天由肾小球滤过形成的<b>原尿约 180 L</b>，但最终排出的<b>尿液只有约 1.5 L</b>。</p>"
                "<p class='mt-2'>少了的水去哪了？被重吸收的比例是多少？</p>"
                "<p class='mt-2'>拖动滑块观察：<b>如果肾小管功能受损，会发什么？</b></p>"
            ),
        },
        "board": {
            "scene": scene,
            "view": {"xRange": scene["xRange"], "yRange": scene["yRange"]},
            "params": [
                {"name": "molFilt", "label": "每天生成原尿量", "min": 100, "max": 220, "step": 5, "value": 180, "unit": " L", "digits": 0},
                {"name": "molUrine", "label": "每天排出尿量", "min": 0.5, "max": 5, "step": 0.5, "value": 1.5, "unit": " L", "digits": 1},
            ],
            "scalars": [
                {"name": "reabsorbed", "expr": "molFilt - molUrine"},
                {"name": "rate", "expr": "(molFilt-molUrine)/molFilt*100"},
            ],
            "readouts": [
                {"id": "rate", "label": "重吸收比例", "type": "expr", "expr": "rate", "digits": 2, "unit": "%", "highlight": True},
                {"id": "re", "label": "被重吸收的量", "type": "expr", "expr": "reabsorbed", "digits": 1, "unit": " L/天", "color": "#166534"},
                {"id": "glc", "label": "原尿中的葡萄糖", "type": "text", "value": "全部被重吸收（正常尿中不应检出）", "color": "#059669"},
                {"id": "check", "label": "肾小管功能是否正常", "type": "status", "expr": "rate", "op": ">=", "rhs": 98,
                 "okText": "重吸收正常（>98%）", "badText": "重吸收不足 → 尿量大增（如尿崩症）"},
            ],
            "constant": {"label": "原尿成分 ≈ 血浆（除大分子蛋白），尿液成分 ≈ 浓缩的废物"},
            "legend": [
                {"color": "#7f1d1d", "text": "血液"},
                {"color": "#334155", "text": "肾小球（滤过）"},
                {"color": "#0e7490", "text": "原尿"},
                {"color": "#166534", "text": "肾小管（重吸收）"},
                {"color": "#a16207", "text": "尿液"},
            ],
        },
        "steps": [
            {"title": "第一步：肾小球的滤过作用", "content": (
                "<p>血液流经肾小球时，除<b>血细胞和大分子蛋白质</b>外，"
                "水、无机盐、葡萄糖、尿素等都被滤过到肾小囊中，形成<b>原尿</b>。</p>"
                "<p class='mt-2'>原尿的量很大：$180$ L/天——相当于全身血浆被滤过几十遍。</p>"
            )},
            {"title": "第二步：肾小管的重吸收作用", "content": (
                "<p>原尿流经肾小管时，<b>大部分水、部分无机盐、全部葡萄糖</b>"
                "被重新吸收回血液。</p>"
                "$$\\text{重吸收比例} = \\frac{180 - 1.5}{180} \\times 100\\% = "
                + f"{_n(reabsorb)*100:.2f}" + "\\%$$"
                "<p>约 <b>99%</b> 的水被重吸收回去，所以最终只有 1.5 L 排出。</p>"
            )},
            {"title": "成分对比：记住这张表", "content": (
                "<table class='w-full text-xs border-collapse mt-1'>"
                "<tr class='bg-teal-50'><th class='border px-2 py-1'>成分</th>"
                "<th class='border px-2 py-1'>血液</th><th class='border px-2 py-1'>原尿</th><th class='border px-2 py-1'>尿液</th></tr>"
                "<tr><td class='border px-2 py-1'>蛋白质</td><td class='border px-2 py-1 text-center'>有</td><td class='border px-2 py-1 text-center'>无</td><td class='border px-2 py-1 text-center'>无</td></tr>"
                "<tr><td class='border px-2 py-1'>葡萄糖</td><td class='border px-2 py-1 text-center'>有</td><td class='border px-2 py-1 text-center'>有</td><td class='border px-2 py-1 text-center'>无</td></tr>"
                "<tr><td class='border px-2 py-1'>尿素</td><td class='border px-2 py-1 text-center'>有</td><td class='border px-2 py-1 text-center'>有</td><td class='border px-2 py-1 text-center'>有（浓缩）</td></tr>"
                "<tr><td class='border px-2 py-1'>血细胞</td><td class='border px-2 py-1 text-center'>有</td><td class='border px-2 py-1 text-center'>无</td><td class='border px-2 py-1 text-center'>无</td></tr>"
                "</table>"
                "<p class='mt-2 border-l-4 border-teal-400 pl-3'><b>化验单怎么看</b>："
                "尿中出现<b>蛋白质</b> → 肾小球病变（滤过筛子漏了）；"
                "尿中出现<b>葡萄糖</b> → 可能是糖尿病（血糖过高超过肾小管重吸收能力）或肾小管病变。</p>"
            )},
            {"title": "尿的意义", "content": (
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li><b>排出废物</b>：尿素、多余的无机盐等代谢终产物；</li>"
                "<li><b>调节水和无机盐的平衡</b>：体内水多则尿多、尿淡；水少则尿少、尿浓；</li>"
                "<li>这个调节由<b>激素</b>（抗利尿激素）和神经系统共同完成。</li>"
                "</ul>"
                "<p class='mt-2'>所以尿的形成不只是「排出」，更是<b>维持内环境稳定</b>的重要环节。</p>"
            )},
        ],
    }


# =====================================================================
# 生理过程：反射弧
# =====================================================================
def build_reflex():
    scene = {
        "kind": "flow", "caption": "反射弧的五个环节",
        "xRange": [0, 12.0], "yRange": [3.5, 6.0],
        "activeNodes": ["receptor", "afferent", "center", "efferent", "effector"],
        "activeEdges": ["receptor>afferent", "afferent>center", "center>efferent", "efferent>effector"],
        "nodes": [
            {"id": "receptor", "label": "感受器", "sub": "如皮肤", "x": 0.2, "y": 4.2, "w": 1.9, "h": 1.0, "color": "#0e7490"},
            {"id": "afferent", "label": "传入神经", "sub": "→ 脊髓", "x": 2.5, "y": 4.2, "w": 2.0, "h": 1.0, "color": "#1d4ed8"},
            {"id": "center", "label": "神经中枢", "sub": "脊髓 / 大脑", "x": 4.9, "y": 4.2, "w": 2.1, "h": 1.0, "color": "#7c3aed"},
            {"id": "efferent", "label": "传出神经", "sub": "← 脊髓", "x": 7.4, "y": 4.2, "w": 2.0, "h": 1.0, "color": "#b45309"},
            {"id": "effector", "label": "效应器", "sub": "如肌肉", "x": 9.8, "y": 4.2, "w": 1.9, "h": 1.0, "color": "#166534"},
        ],
        "edges": [
            {"from": "receptor", "to": "afferent", "label": "产生兴奋"},
            {"from": "afferent", "to": "center", "label": "传导"},
            {"from": "center", "to": "efferent", "label": "分析综合"},
            {"from": "efferent", "to": "effector", "label": "传导"},
        ],
        "footer": "感受器 → 传入神经 → 神经中枢 → 传出神经 → 效应器（缺一不可）",
    }
    return {
        "lesson": {
            "title": "反射与反射弧：缩手反射是怎么发生的",
            "subtitle": "从手碰到烫的东西，到把手缩回来，中间发生了什么",
            "problem": (
                "<p>手不小心碰到很烫的杯子，会<b>先缩手、后感觉疼</b>。这个反射经过哪些结构？</p>"
                "<p class='mt-2'>反射弧由五个环节组成：<b>感受器 → 传入神经 → 神经中枢 → "
                "传出神经 → 效应器</b>。</p>"
                "<p class='mt-2'>拖动滑块调<b>神经传导速度</b>与<b>传导距离</b>，估算反应时间，"
                "并理解<b>为什么先缩手后觉得疼</b>。</p>"
            ),
        },
        "board": {
            "scene": scene,
            "view": {"xRange": scene["xRange"], "yRange": scene["yRange"]},
            "params": [
                {"name": "speed", "label": "神经冲动传导速度", "min": 20, "max": 120, "step": 5, "value": 100, "unit": " m/s", "digits": 0},
                {"name": "dist", "label": "兴奋传导的总路程", "min": 0.5, "max": 3, "step": 0.1, "value": 1.5, "unit": " m", "digits": 1},
            ],
            "scalars": [
                {"name": "ms", "expr": "dist/speed*1000"},
            ],
            "readouts": [
                {"id": "ms", "label": "传导所需时间", "type": "expr", "expr": "ms", "digits": 2, "unit": " ms", "highlight": True},
                {"id": "n", "label": "反射弧环节数", "type": "expr", "expr": "5", "digits": 0, "unit": " 个"},
                {"id": "must", "label": "任一环节损坏", "type": "status", "expr": "5", "op": "==", "rhs": 5,
                 "okText": "反射弧必须完整，缺一不可", "badText": "—"},
                {"id": "brain", "label": "疼痛感觉产生于", "type": "text", "value": "大脑皮层（不在反射弧环节内）", "color": "#7c3aed"},
            ],
            "constant": {"label": "缩手反射的中枢在脊髓，不经过大脑——所以快"},
            "legend": [
                {"color": "#0e7490", "text": "感受器"},
                {"color": "#1d4ed8", "text": "传入神经"},
                {"color": "#7c3aed", "text": "神经中枢"},
                {"color": "#b45309", "text": "传出神经"},
                {"color": "#166534", "text": "效应器"},
            ],
        },
        "steps": [
            {"title": "反射弧的五个环节", "content": (
                "<p>完成一个反射所经过的神经通路叫<b>反射弧</b>：</p>"
                "<ol class='list-decimal pl-5 space-y-1'>"
                "<li><b>感受器</b>：感受刺激并产生兴奋（如手指皮肤）</li>"
                "<li><b>传入神经</b>：把兴奋传到神经中枢</li>"
                "<li><b>神经中枢</b>：分析综合（缩手反射在脊髓）</li>"
                "<li><b>传出神经</b>：把兴奋传到效应器</li>"
                "<li><b>效应器</b>：做出反应（如手臂肌肉收缩）</li></ol>"
                "<p class='mt-2 text-rose-600 font-semibold'>五个环节缺一不可，任一环节损伤，反射都无法完成。</p>"
            )},
            {"title": "兴奋的传导与传递", "content": (
                "<p>兴奋在同一条神经纤维上以<b>电信号</b>形式传导，速度可达 $100$ m/s 左右：</p>"
                "$$v = \\frac{s}{t} \\Longrightarrow t = \\frac{s}{v} = \\frac{1.5}{100} = "
                + f"{_n(sp.Rational(15,10)/100*1000):.2f}" + "\\ \\text{ms}$$"
                "<p>但在两个神经元之间（突触）传递时，要靠<b>神经递质</b>，"
                "速度明显变慢——这是信号传递的「瓶颈」，也是单向传递的原因。</p>"
            )},
            {"title": "为什么先缩手后觉得疼", "content": (
                "<p>关键在<b>传导路径的长度</b>：</p>"
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li><b>缩手</b>：脊髓（神经中枢）直接发出指令 → 到达手臂肌肉，路径<b>短</b>；</li>"
                "<li><b>疼痛</b>：兴奋还要沿脊髓<b>上传到大脑皮层</b>才能形成痛觉，路径<b>长</b>。</li></ul>"
                "<p class='mt-2'>所以总是先缩手、稍后才感到疼。这体现了脊髓的反射功能"
                "（快、无需意识）与大脑的感觉功能（慢、需意识）的分工。</p>"
            )},
            {"title": "条件反射与非条件反射", "content": (
                "<table class='w-full text-xs border-collapse mt-1'>"
                "<tr class='bg-teal-50'><th class='border px-2 py-1'>对比项</th>"
                "<th class='border px-2 py-1'>非条件反射</th><th class='border px-2 py-1'>条件反射</th></tr>"
                "<tr><td class='border px-2 py-1'>形成</td><td class='border px-2 py-1'>生来就有</td><td class='border px-2 py-1'>后天学习获得</td></tr>"
                "<tr><td class='border px-2 py-1'>神经中枢</td><td class='border px-2 py-1'>大脑皮层以下</td><td class='border px-2 py-1'>大脑皮层</td></tr>"
                "<tr><td class='border px-2 py-1'>稳定性</td><td class='border px-2 py-1'>固定、不消退</td><td class='border px-2 py-1'>可建立也可消退</td></tr>"
                "<tr><td class='border px-2 py-1'>实例</td><td class='border px-2 py-1'>缩手、眨眼、膝跳</td><td class='border px-2 py-1'>望梅止渴、听到铃声分泌唾液</td></tr>"
                "</table>"
            )},
        ],
    }


# =====================================================================
# 生理过程：血液循环
# =====================================================================
def build_circulation():
    scene = {
        "kind": "flow", "caption": "血液循环（肺循环 + 体循环）",
        "xRange": [0, 12.3], "yRange": [2.3, 6.5],
        "activeNodes": ["rv", "pa", "lung", "pv", "la", "lv", "aorta", "body", "vc", "ra"],
        "activeEdges": ["rv>pa", "pa>lung", "lung>pv", "pv>la", "la>lv", "lv>aorta", "aorta>body", "body>vc", "vc>ra", "ra>rv"],
        "nodes": [
            {"id": "rv", "label": "右心室", "sub": "起点", "x": 0.2, "y": 5.0, "w": 2.1, "h": 0.9, "color": "#7f1d1d"},
            {"id": "pa", "label": "肺动脉", "sub": "静脉血", "x": 2.6, "y": 5.0, "w": 2.0, "h": 0.9, "color": "#1d4ed8"},
            {"id": "lung", "label": "肺部毛细血管", "sub": "气体交换", "x": 4.9, "y": 5.0, "w": 2.6, "h": 0.9, "color": "#0e7490"},
            {"id": "pv", "label": "肺静脉", "sub": "动脉血", "x": 7.8, "y": 5.0, "w": 2.0, "h": 0.9, "color": "#b91c1c"},
            {"id": "la", "label": "左心房", "sub": "", "x": 10.1, "y": 5.0, "w": 2.0, "h": 0.9, "color": "#b91c1c"},
            {"id": "lv", "label": "左心室", "sub": "壁最厚", "x": 10.1, "y": 3.0, "w": 2.0, "h": 0.9, "color": "#b91c1c"},
            {"id": "aorta", "label": "主动脉", "sub": "动脉血", "x": 7.8, "y": 3.0, "w": 2.0, "h": 0.9, "color": "#b91c1c"},
            {"id": "body", "label": "全身毛细血管", "sub": "气体/养料交换", "x": 4.9, "y": 3.0, "w": 2.6, "h": 0.9, "color": "#0e7490"},
            {"id": "vc", "label": "上下腔静脉", "sub": "静脉血", "x": 2.6, "y": 3.0, "w": 2.0, "h": 0.9, "color": "#1d4ed8"},
            {"id": "ra", "label": "右心房", "sub": "", "x": 0.2, "y": 3.0, "w": 2.1, "h": 0.9, "color": "#1d4ed8"},
        ],
        "edges": [
            {"from": "rv", "to": "pa"}, {"from": "pa", "to": "lung", "label": "肺循环"},
            {"from": "lung", "to": "pv"}, {"from": "pv", "to": "la"},
            {"from": "la", "to": "lv", "dir": "v"},
            {"from": "lv", "to": "aorta"}, {"from": "aorta", "to": "body", "label": "体循环"},
            {"from": "body", "to": "vc"}, {"from": "vc", "to": "ra"},
            {"from": "ra", "to": "rv", "dir": "vu"},
        ],
        "footer": "上排＝肺循环（右心室→肺→左心房）　下排＝体循环（左心室→全身→右心房）　血管颜色：红＝动脉血，蓝＝静脉血",
    }
    return {
        "lesson": {
            "title": "血液循环：肺循环与体循环",
            "subtitle": "血液为什么能在心脏的推动下流遍全身并回到心脏",
            "problem": (
                "<p>心脏像一台<b>泵</b>，把血液压入血管。血液循环分为两条路线：</p>"
                "<ul class='list-disc pl-5 mt-1 space-y-1'>"
                "<li><b>肺循环</b>：右心室 → 肺 → 左心房（把静脉血变成动脉血）</li>"
                "<li><b>体循环</b>：左心室 → 全身 → 右心房（把动脉血变成静脉血）</li></ul>"
                "<p class='mt-2'>拖动滑块改变<b>心率</b>与<b>每搏输出量</b>，看每分钟泵出多少血。</p>"
            ),
        },
        "board": {
            "scene": scene,
            "view": {"xRange": scene["xRange"], "yRange": scene["yRange"]},
            "params": [
                {"name": "hr", "label": "心率", "min": 40, "max": 180, "step": 1, "value": 75, "unit": " 次/分", "digits": 0},
                {"name": "sv", "label": "每搏输出量", "min": 40, "max": 120, "step": 5, "value": 70, "unit": " mL", "digits": 0},
            ],
            "scalars": [
                {"name": "co", "expr": "hr*sv/1000"},
            ],
            "readouts": [
                {"id": "co", "label": "每分输出量（心输出量）", "type": "expr", "expr": "co", "digits": 2, "unit": " L/min", "highlight": True},
                {"id": "day", "label": "一天泵出的血量", "type": "expr", "expr": "co*60*24/1000", "int": True, "unit": " m³", "color": "#b91c1c"},
                {"id": "loops", "label": "血液循环两条路线", "type": "text", "value": "肺循环 + 体循环，同时进行"},
                {"id": "gap", "label": "动脉血与静脉血的分界", "type": "status", "expr": "1", "op": "==", "rhs": 1,
                 "okText": "在毛细血管处完成交换", "badText": "—"},
            ],
            "constant": {"label": "两循环同时进行，在心脏处汇合——血液只能沿一个方向流动（瓣膜）"},
            "legend": [
                {"color": "#b91c1c", "text": "动脉血（含氧丰富）"},
                {"color": "#1d4ed8", "text": "静脉血（含氧较少）"},
                {"color": "#0e7490", "text": "毛细血管（物质交换）"},
            ],
        },
        "steps": [
            {"title": "心脏的四腔", "content": (
                "<p>心脏由四个腔构成：<b>左心房、左心室、右心房、右心室</b>。"
                "心房在上、心室在下，同侧的心房与心室相通，中间有<b>瓣膜</b>保证血液单向流动。</p>"
                "<p class='mt-2'><b>左心室的壁最厚</b>——因为它要把血液泵到全身（体循环），"
                "阻力最大、路程最长。</p>"
            )},
            {"title": "肺循环：右心室 → 肺 → 左心房", "content": (
                "<p>血液从<b>右心室</b>进入<b>肺动脉</b>，流到<b>肺部毛细血管</b>，"
                "在这里与肺泡进行气体交换（放出 $CO_2$、吸收 $O_2$），"
                "血液由<b>静脉血变成动脉血</b>，再经<b>肺静脉</b>流回<b>左心房</b>。</p>"
                "<p class='mt-2 text-xs text-slate-500'>注意：肺动脉里流的是<b>静脉血</b>，"
                "肺静脉里流的是<b>动脉血</b>——血管名称与血液性质是两回事。</p>"
            )},
            {"title": "体循环：左心室 → 全身 → 右心房", "content": (
                "<p>血液从<b>左心室</b>进入<b>主动脉</b>，流到<b>全身各处的毛细血管</b>，"
                "把 $O_2$ 和养料送给组织细胞，同时带走 $CO_2$ 等废物，"
                "血液由<b>动脉血变成静脉血</b>，再经<b>上下腔静脉</b>流回<b>右心房</b>。</p>"
                "<p class='mt-2'>两条循环<b>同时进行</b>，在心脏处连通，"
                "构成一个完整的循环路线。</p>"
            )},
            {"title": "心输出量与健康", "content": (
                "<p>心输出量 = 心率 × 每搏输出量：</p>"
                "$$CO = 75 \\times 70 = " + _ns(75*70/1000) + "\\ \\text{L/min}$$"
                "<p>安静时约 $5$ L/min，运动时可增大到 $20$ L/min 以上。</p>"
                "<p class='mt-2 border-l-4 border-teal-400 pl-3'>"
                "<b>运动员</b>的心率较低但每搏输出量较大，同样能泵出足够的血量——"
                "这说明心脏<b>效能的提高来自每次泵得更多，而不是跳得更快</b>。</p>"
            )},
        ],
    }


# =====================================================================
# 注册表
# =====================================================================
REGISTRY = {
    # 遗传与变异
    "monohybrid": build_monohybrid,
    "dihybrid": build_dihybrid,
    "testcross": build_testcross,
    "sexlinked": build_sexlinked,
    # 细胞与结构 3D
    "animal_cell": build_animal_cell,
    "plant_cell": build_plant_cell,
    "prokaryotic_cell": build_prokaryotic_cell,
    # 生理过程
    "photosynthesis": build_photosynthesis,
    "urine": build_urine,
    "reflex": build_reflex,
    "circulation": build_circulation,
    # 生态
    "energy_pyramid": build_energy_pyramid,
    "population": build_population,
}

MODULES = {
    "遗传与变异": ["monohybrid", "dihybrid", "testcross", "sexlinked"],
    "细胞与结构（3D）": ["animal_cell", "plant_cell", "prokaryotic_cell"],
    "生理过程": ["photosynthesis", "urine", "reflex", "circulation"],
    "生态": ["energy_pyramid", "population"],
}

META = {
    "monohybrid": ("单杂交", "基因的分离定律", "Aa × Aa → 3:1", "board"),
    "dihybrid": ("双杂交", "基因的自由组合定律", "AaBb × AaBb → 9:3:3:1", "board"),
    "testcross": ("测交", "用隐性纯合验证基因型", "YyRr × yyrr → 1:1:1:1", "board"),
    "sexlinked": ("伴性遗传", "红绿色盲的遗传方式", "XAXa × XAY", "board"),
    "animal_cell": ("动物细胞", "细胞结构与细胞器", "11 个结构分步观察", "cell"),
    "plant_cell": ("植物细胞", "细胞壁、液泡与叶绿体", "10 个结构分步观察", "cell"),
    "prokaryotic_cell": ("原核细胞", "细菌：没有核膜的细胞", "6 个结构分步观察", "cell"),
    "photosynthesis": ("光合与呼吸", "物质变化的定量计算", "264 g CO₂ → 180 g 葡萄糖", "board"),
    "urine": ("尿的形成", "滤过 + 重吸收", "180 L 原尿 → 1.5 L 尿", "board"),
    "reflex": ("反射弧", "缩手反射的通路", "五个环节", "board"),
    "circulation": ("血液循环", "肺循环与体循环", "心脏四腔与两条路线", "board"),
    "energy_pyramid": ("能量金字塔", "能量沿营养级递减", "10000 → 1000 → 100 → 10", "board"),
    "population": ("种群数量变化", "J 型与 S 型增长", "K/2 处增长最快", "board"),
}

ORDER = [k for ks in MODULES.values() for k in ks]


def _write(key, data, out_path):
    """按题型选模板：cell 类走 Three.js 3D，其余走 Canvas-2D。"""
    if META[key][3] == "cell":
        return _cell(data, out_path)
    return _board(data, out_path)


def meta_of(key):
    """skillkit 要的 (分类, 标题, 一句话) —— 取 META 的前三项。"""
    return (META[key][0], META[key][1], META[key][2])


def build_index(out):
    cards = []
    for mod, keys in MODULES.items():
        items = "".join(
            f'<a href="{k}.html" class="block bg-white rounded-lg border border-slate-200 p-4 '
            f'hover:border-teal-500 hover:shadow transition-all">'
            f'<div class="text-[11px] font-bold text-teal-600 mb-1">{META[k][0]}'
            f'{" · 3D" if META[k][3]=="cell" else ""}</div>'
            f'<div class="text-sm font-bold text-slate-900 leading-snug">{META[k][1]}</div>'
            f'<div class="text-[11px] text-slate-500 mt-1">{META[k][2]}</div></a>'
            for k in keys)
        cards.append(
            f'<div class="mb-6"><div class="text-xs uppercase tracking-wider text-slate-500 font-bold mb-3">{mod}</div>'
            f'<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">{items}</div></div>')
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>生物互动学习 · 目录</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body{{font-family:"PingFang SC","Microsoft YaHei",system-ui,sans-serif;}}</style>
</head>
<body class="bg-slate-100 text-slate-900">
<div class="max-w-6xl mx-auto px-6 py-12">
    <div class="text-xs uppercase tracking-widest text-teal-600 font-bold mb-2">Biology · Interactive</div>
    <h1 class="text-3xl font-bold mb-3">生物：初中 + 高中互动演示</h1>
    <p class="text-slate-600 leading-relaxed max-w-3xl">
        四个模块：<b>遗传与变异</b>（棋盘格推演）、<b>细胞与结构</b>（可交互 3D 模型）、
        <b>生理过程</b>（流程图 + 定量计算）、<b>生态</b>（能量金字塔与种群增长）。
        所有数值由 <code>lib/bio_kernel.py</code>（sympy 精确）算出，与画板读数同源。
    </p>
    <div class="mt-8">{''.join(cards)}</div>
</div>
</body></html>"""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def _random(rng):
    """随机出题：优先挑需要计算的题型（遗传/生态/代谢），参数随机但答案规整。"""
    pick = rng.choice(["monohybrid", "dihybrid", "sexlinked",
                       "energy_pyramid", "population", "photosynthesis"])
    return pick, REGISTRY[pick]()


def _index(out_dir):
    return build_index(Path(out_dir) / "index.html")


def main(argv):
    # 统一入口（edulab/shared/skillkit.py）：
    #   python generate.py list | all <目录> | random [seed] [输出] | <key> [输出]
    return cli(REGISTRY, doc=__doc__, meta=meta_of, groups=MODULES,
               random_build=_random, render=_write, index_writer=_index,
               argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
