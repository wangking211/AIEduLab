#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「动量与碰撞」交互网页。

全部数值由 lib/momentum_kernel.py 现算，**不手写数字**。

覆盖七个题型（选择性必修一）：
  impulse        动量定理（冲量 = 力-时间图的面积）
  inelastic      完全非弹性碰撞（碰后共速）
  elastic        弹性碰撞（动量与动能同时守恒）
  recoil         反冲与爆炸
  boat           人船模型（质心不动）
  bullet         子弹打木块
  twod           等质量弹性斜碰的 90° 定理（二维动量守恒）

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

import momentum_kernel as K                    # noqa: E402
from skillkit import cli                       # noqa: E402

# =====================================================================
# 读数表达式 ↔ 内核 的对账机制
# =====================================================================

_MATHENV = {
    "sqrt": math.sqrt, "abs": abs, "min": min, "max": max, "pow": pow,
    "sign": lambda x: (x > 0) - (x < 0), "floor": math.floor, "ceil": math.ceil,
    "PI": math.pi, "E": math.e,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
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
# 1) 动量定理
# =====================================================================
IM_M, IM_V1, IM_V2 = 0.5, 10.0, -8.0
EXPR_IM_DP = f"{IM_M}*({IM_V2}-{IM_V1})"
EXPR_IM_F = f"abs({EXPR_IM_DP})/t"


def build_impulse() -> dict:
    for t in (0.01, 0.05, 0.1, 0.25, 0.5):
        _agree(f"Δp(t={t})", EXPR_IM_DP, K.delta_p(IM_M, IM_V1, IM_V2), tol=1e-12, t=t)
        _agree(f"F̄(t={t})", EXPR_IM_F, abs(K.avg_force(IM_M, IM_V1, IM_V2, t)), tol=1e-12, t=t)
        # 面积恒等于 |Δp|
        _agree(f"面积(t={t})", f"({EXPR_IM_F})*t", abs(K.delta_p(IM_M, IM_V1, IM_V2)), tol=1e-12, t=t)
    _agree("冲量大小 = 动量变化大小", f"{EXPR_IM_F}*{0.05:.2f}", 9.0, tol=1e-12, t=0.05)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "impulse", "t": "t",
                  "caption": "黄框面积就是冲量 —— 拉长作用时间，高度（平均力）自动变矮"},
        "param": {"name": "t", "label": "碰撞时间 $t$", "min": 0.01, "max": 0.5,
                  "step": 0.01, "value": 0.05, "unit": "s", "standard": 0.05,
                  "ticks": ["0.01 (硬碰)", "0.05 (题设)", "0.2", "0.5 (缓冲)"]},
        "readouts": [
            ro("t", "碰撞时间 $t$", "t", 2, "s"),
            ro("f", "平均力大小 $\\bar F = |\\Delta p|/t$", EXPR_IM_F, 1, "N"),
            ro("dp", "动量变化 $\\Delta p = m(v_2-v_1)$", EXPR_IM_DP, 1, "kg·m/s"),
            ro("area", "冲量大小 $|\\Delta p|$（定值）", f"abs({EXPR_IM_DP})", 1, "N·s"),
            ro_status("hard", "平均力是否超过 500 N（硬碰）", EXPR_IM_F, 500, ">",
                      "硬碰：时间短 ⇒ 平均力很大", "缓冲：时间长 ⇒ 平均力较小"),
        ],
        "constant": {"of": "area", "label": "冲量恒为 9 N·s —— 面积不变，只改长宽比"},
    }
    lesson = {
        "language": "zh-CN", "title": "动量定理与缓冲原理",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>质量 $m = 0.5\\ \\mathrm{kg}$ 的小球以 $10\\ \\mathrm{m/s}$ 垂直撞向墙壁，"
            "反弹后速度大小为 $8\\ \\mathrm{m/s}$，碰撞时间为 $t$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求碰撞过程中小球动量的变化量；</li>"
            "<li>求球受到的平均力（用 $t$ 表示）；</li>"
            "<li>$t$ 变大时平均力怎么变？为什么安全气囊能保护人？</li></ol>"),
        "answerLabel": "$t = 0.05$ s 时",
        "answer": f"$\\Delta p = m(v_2-v_1) = {K.f(K.delta_p(IM_M, IM_V1, IM_V2), 1)}$ kg·m/s，"
                  f"$\\bar F = {K.f(abs(K.avg_force(IM_M, IM_V1, IM_V2, 0.05)), 0)}$ N",
    }
    steps = [
        {"title": "动量与动量的变化",
         "content": ("<p>动量 $p = mv$ 是**矢量**，一维问题必须带符号。取向右为正："
                     "撞前 $v_1 = +10\\ \\mathrm{m/s}$，反弹后 $v_2 = -8\\ \\mathrm{m/s}$。</p>"
                     "<p>$\\Delta p = m(v_2 - v_1) = 0.5\\times(-8-10) = -9\\ \\mathrm{kg\\cdot m/s}$。</p>"
                     "<p>负号表示动量变化的方向**向左** —— 这正是墙给球的冲量方向。</p>")},
        {"title": "冲量就是 F-t 图的面积",
         "content": ("<p>动量定理：$I = \\bar F t = \\Delta p$。</p>"
                     "<p>把它画在 $F$-$t$ 图上：矩形的高是平均力，宽是作用时间，"
                     "**面积就是冲量**。本页把面积固定成 $|\\Delta p| = 9\\ \\mathrm{N\\cdot s}$，"
                     "于是拖滑块时矩形只能「变矮变宽」或「变高变窄」，"
                     "**面积永远不变** —— 这就是读数区里那个定值。</p>")},
        {"title": "缓冲原理",
         "content": ("<p>既然面积不变，$t$ 增大 5 倍，$\\bar F$ 就必须减小到原来的 $\\dfrac{1}{5}$。</p>"
                     "<p>跳到硬地板上，$t$ 只有几毫秒，$\\bar F$ 可以大到几千牛 —— 会骨折；"
                     "跳垫把 $t$ 拉长到几百毫秒，同样的冲量分摊成很小的力。</p>"
                     "<p>安全气囊、包装泡沫、跳高软垫、汽车吸能盒，"
                     "全都只在做一件事：**延长作用时间**。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 完全非弹性碰撞
# =====================================================================
IN_M1, IN_V1 = 2.0, 6.0
EXPR_IN_VP = f"{IN_M1}*{IN_V1}/({IN_M1}+m2)"
EXPR_IN_E0 = f"0.5*{IN_M1}*{IN_V1}*{IN_V1}"
EXPR_IN_LOSS = f"{EXPR_IN_E0}-0.5*({IN_M1}+m2)*pow({EXPR_IN_VP},2)"


def build_inelastic() -> dict:
    for m2 in (1.0, 2.0, 4.0, 7.0, 10.0):
        _agree(f"共速(m2={m2})", EXPR_IN_VP, K.inelastic_v(IN_M1, IN_V1, m2, 0.0), tol=1e-12, m2=m2)
        _agree(f"动能损失(m2={m2})", EXPR_IN_LOSS,
               K.kinetic_loss(IN_M1, IN_V1, m2, 0.0), tol=1e-12, m2=m2)
        _agree(f"损失比例(m2={m2})", f"({EXPR_IN_LOSS})/({EXPR_IN_E0})",
               K.loss_fraction(IN_M1, IN_V1, m2, 0.0), tol=1e-12, m2=m2)
        # 动量守恒
        _agree(f"动量守恒(m2={m2})", f"({IN_M1}+m2)*({EXPR_IN_VP})",
               K.total_momentum([IN_M1, m2], [IN_V1, 0.0]), tol=1e-12, m2=m2)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "collide_in", "m2": "m2",
                  "caption": "碰前两球（上）→ 碰后粘在一起（下）；速度箭头长度与速度成正比"},
        "param": {"name": "m2", "label": "被碰球质量 $m_2$", "min": 1, "max": 10,
                  "step": 0.5, "value": 4.0, "unit": "kg", "standard": 4.0,
                  "ticks": ["1", "4 (题设，等质量)", "10"]},
        "readouts": [
            ro("m2", "被碰球质量 $m_2$", "m2", 1, "kg"),
            ro("vp", "碰后共同速度 $v\'$", EXPR_IN_VP, 4, "m/s"),
            ro("pb", "碰前总动量（定值）", f"{IN_M1}*{IN_V1}", 1, "kg·m/s"),
            ro("pa", "碰后总动量", f"({IN_M1}+m2)*({EXPR_IN_VP})", 4, "kg·m/s"),
            ro("loss", "损失的动能", EXPR_IN_LOSS, 3, "J"),
            ro_status("half", "动能损失是否过半（碰后者更重）",
                      f"({EXPR_IN_LOSS})/({EXPR_IN_E0})", 0.5, ">",
                      "损失过半：大部分动能变成了内能", "损失不到一半"),
        ],
        "constant": {"of": "pb", "label": "总动量恒为 12 kg·m/s —— 无论 $m_2$ 怎么变，碰前碰后都一样"},
    }
    lesson = {
        "language": "zh-CN", "title": "完全非弹性碰撞",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>质量 $m_1 = 2\\ \\mathrm{kg}$ 的小球以 $v_1 = 6\\ \\mathrm{m/s}$ 向右运动，"
            "撞上静止的质量 $m_2$ 的小球后粘在一起。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求碰后共同速度；</li>"
            "<li>动量守恒吗？动能守恒吗？</li>"
            "<li>拖动滑块，什么时候动能损失正好一半？</li></ol>"),
        "answerLabel": "$m_2 = 4$ kg 时",
        "answer": f"$v' = \\dfrac{{m_1v_1}}{{m_1+m_2}} = "
                  f"{K.f(K.inelastic_v(IN_M1, IN_V1, 4.0, 0.0), 4)}$ m/s，"
                  f"损失动能 ${K.f(K.kinetic_loss(IN_M1, IN_V1, 4.0, 0.0), 2)}$ J",
    }
    steps = [
        {"title": "只守恒动量，不守恒动能",
         "content": ("<p>碰撞过程中系统动量守恒：</p>"
                     "<p>$m_1v_1 = (m_1+m_2)v'$ ⇒ $v' = \\dfrac{m_1v_1}{m_1+m_2}$。</p>"
                     "<p>但动能**不守恒**：两球挤压、变形、发热，一部分动能变成了内能。"
                     "$v' = 2\\ \\mathrm{m/s}$ 时损失 $24\\ \\mathrm{J}$，正好是初动能 $36\\ \\mathrm{J}$ 的 $\\dfrac{2}{3}$。</p>")},
        {"title": "为什么动量一定守恒",
         "content": ("<p>因为碰撞时间极短，把两球看成一个系统时，"
                     "**系统受到的合外力**（重力与地面支持力）在短时间内产生的冲量可以忽略，"
                     "所以系统动量近似守恒。</p>"
                     "<p>动能则没有这条保护 —— 只要碰后共速，"
                     "就有动能「消失」在形变与内能里，这是**完全非弹性**的特征。</p>")},
        {"title": "什么时候损失一半",
         "content": ("<p>把损失比例算出来可以化简成：</p>"
                     "<p>$\\dfrac{\\Delta E}{E_0} = \\dfrac{m_2}{m_1+m_2}$。</p>"
                     "<p>所以 $m_2 = m_1$（等质量）时损失正好一半，"
                     "与初速度无关；$m_2 \\to \\infty$（撞不动的大块）时损失趋近 $100\\%$。</p>"
                     "<p>注意损失的能量与「谁撞谁」无关，只由**质量比**决定。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 弹性碰撞
# =====================================================================
EL_M1, EL_V1 = 1.0, 4.0
EXPR_EL_V1P = f"({EL_M1}-m2)*{EL_V1}/({EL_M1}+m2)"
EXPR_EL_V2P = f"2*{EL_M1}*{EL_V1}/({EL_M1}+m2)"
EXPR_EL_E0 = f"0.5*{EL_M1}*{EL_V1}*{EL_V1}"


def build_elastic() -> dict:
    for m2 in (0.2, 0.5, 1.0, 2.0, 5.0):
        v1p, v2p = K.elastic_pair(EL_M1, EL_V1, m2, 0.0)
        _agree(f"v₁′(m2={m2})", EXPR_EL_V1P, v1p, tol=1e-12, m2=m2)
        _agree(f"v₂′(m2={m2})", EXPR_EL_V2P, v2p, tol=1e-12, m2=m2)
        _agree(f"动量守恒(m2={m2})", f"{EL_M1}*({EXPR_EL_V1P})+m2*({EXPR_EL_V2P})",
               K.total_momentum([EL_M1, m2], [v1p, v2p]), tol=1e-12, m2=m2)
        _agree(f"动能守恒(m2={m2})",
               f"0.5*{EL_M1}*pow({EXPR_EL_V1P},2)+0.5*m2*pow({EXPR_EL_V2P},2)",
               K.total_kinetic([EL_M1, m2], [v1p, v2p]), tol=1e-12, m2=m2)
    _agree("等质量交换速度", f"({EL_M1}-{EL_M1})*{EL_V1}/(2*{EL_M1})", 0.0, tol=1e-12, m2=1.0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "collide_el", "m2": "m2",
                  "caption": "弹性碰撞：碰前碰后两个球分列上下两行；总动能恒为 8 J"},
        "param": {"name": "m2", "label": "被碰球质量 $m_2$", "min": 0.2, "max": 5,
                  "step": 0.1, "value": 1.0, "unit": "kg", "standard": 1.0,
                  "ticks": ["0.2", "1 (等质量)", "2", "5"]},
        "readouts": [
            ro("m2", "被碰球质量 $m_2$", "m2", 1, "kg"),
            ro("v1p", "碰后 $v_1\'$", EXPR_EL_V1P, 4, "m/s"),
            ro("v2p", "碰后 $v_2\'$", EXPR_EL_V2P, 4, "m/s"),
            ro("p", "碰后总动量（定值 4）",
               f"{EL_M1}*({EXPR_EL_V1P})+m2*({EXPR_EL_V2P})", 4, "kg·m/s"),
            ro("e", "碰后总动能（定值 8）",
               f"0.5*{EL_M1}*pow({EXPR_EL_V1P},2)+0.5*m2*pow({EXPR_EL_V2P},2)", 4, "J"),
            ro_status("back", "入射球是否被弹回（$v_1\' < 0$）", EXPR_EL_V1P, 0, "<",
                      "m₂ > m₁：入射球被弹回来", "m₂ ≤ m₁：入射球不反弹"),
        ],
        "constant": {"of": "e", "label": "总动能恒为 8 J —— 弹性碰撞的动能一点不损失"},
    }
    lesson = {
        "language": "zh-CN", "title": "弹性碰撞与 90° 之外的两个特例",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>质量 $m_1 = 1\\ \\mathrm{kg}$ 的小球以 $v_1 = 4\\ \\mathrm{m/s}$ 向右运动，"
            "与静止的质量 $m_2$ 的小球发生**弹性**正碰。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出碰后两球速度的表达式；</li>"
            "<li>拖动滑块，$m_2 = m_1$ 时发生什么？</li>"
            "<li>$m_2 > m_1$ 时入射球为什么会往回走？</li></ol>"),
        "answerLabel": "$m_2 = 3$ kg 时",
        "answer": f"$v_1' = {K.f(K.elastic_v1(EL_M1, EL_V1, 3.0, 0.0), 3)}$ m/s，"
                  f"$v_2' = {K.f(K.elastic_v2(EL_M1, EL_V1, 3.0, 0.0), 3)}$ m/s",
    }
    steps = [
        {"title": "两个守恒联立",
         "content": ("<p>弹性碰撞同时满足：</p>"
                     "<p>动量守恒：$m_1v_1 = m_1v_1' + m_2v_2'$；</p>"
                     "<p>动能守恒：$\\dfrac12m_1v_1^2 = \\dfrac12m_1v_1'^2 + \\dfrac12m_2v_2'^2$。</p>"
                     "<p>联立（$v_2 = 0$）解得</p>"
                     "<p>$v_1' = \\dfrac{m_1-m_2}{m_1+m_2}v_1$，"
                     "$v_2' = \\dfrac{2m_1}{m_1+m_2}v_1$。</p>"
                     "<p>读数区里总动量恒为 $4$、总动能恒为 $8\\ \\mathrm{J}$ —— "
                     "拖滑块时两个定值指示器都不动，这就是「弹性」的含义。</p>")},
        {"title": "两个必须记住的特例",
         "content": ("<p>· $m_2 = m_1$：$v_1' = 0$、$v_2' = v_1$ —— **交换速度**。"
                     "台球正面对撞就是这个效果，所以打台球要「借力」很容易。</p>"
                     "<p>· $m_2 \\gg m_1$：$v_1' \\approx -v_1$、$v_2' \\approx 0$ —— "
                     "小球原速弹回，大块几乎不动（乒乓球撞墙）。</p>"
                     "<p>· $m_2 \\ll m_1$：$v_1' \\approx v_1$、$v_2' \\approx 2v_1$ —— "
                     "大块照旧前进，小球以两倍速度弹出（铅球撞乒乓球）。</p>")},
        {"title": "为什么 m₂ > m₁ 会被弹回",
         "content": ("<p>看 $v_1' = \\dfrac{m_1-m_2}{m_1+m_2}v_1$ 的**符号**："
                     "$m_2 > m_1$ 时分子为负，$v_1' < 0$，"
                     "说明入射球反向 —— 状态灯就在 $m_2 = m_1$ 处翻转。</p>"
                     "<p>物理上：碰后 $v_2' > v_1'$ 总是成立（被碰球一定跑得不比入射球慢），"
                     "否则「追上去再撞一次」就矛盾了。</p>"
                     "<p>顺带一提：**等质量弹性斜碰**时两球出射方向恒成 $90^\\circ$，"
                     "那是下一节的二维版本。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 反冲与爆炸
# =====================================================================
RC_M1, RC_E = 1.0, 100.0
EXPR_RC_V1 = f"sqrt(2*{RC_E}*m2/({RC_M1}*({RC_M1}+m2)))"
EXPR_RC_V2 = f"-sqrt(2*{RC_E}*{RC_M1}/(m2*({RC_M1}+m2)))"


def build_recoil() -> dict:
    for m2 in (0.5, 1.0, 2.0, 4.0, 5.0):
        v1, v2 = K.explosion_velocities(RC_M1, m2, RC_E)
        _agree(f"v₁(m2={m2})", EXPR_RC_V1, v1, tol=1e-12, m2=m2)
        _agree(f"v₂(m2={m2})", EXPR_RC_V2, v2, tol=1e-12, m2=m2)
        _agree(f"总动量为零(m2={m2})", f"{RC_M1}*({EXPR_RC_V1})+m2*({EXPR_RC_V2})", 0.0, tol=1e-9, m2=m2)
        _agree(f"能量守恒(m2={m2})",
               f"0.5*{RC_M1}*pow({EXPR_RC_V1},2)+0.5*m2*pow({EXPR_RC_V2},2)", RC_E, tol=1e-9, m2=m2)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "recoil", "m2": "m2",
                  "caption": "爆炸后两块反向飞出；下方绿箭头表示两块动量等大反向"},
        "param": {"name": "m2", "label": "第二块质量 $m_2$", "min": 0.5, "max": 5,
                  "step": 0.1, "value": 4.0, "unit": "kg", "standard": 4.0,
                  "ticks": ["0.5", "1 (等质量)", "4 (题设)", "5"]},
        "readouts": [
            ro("m2", "第二块质量 $m_2$", "m2", 1, "kg"),
            ro("v1", "$v_1$（质量 1 kg 的碎片）", EXPR_RC_V1, 4, "m/s"),
            ro("v2", "$v_2$（质量 m₂ 的碎片）", EXPR_RC_V2, 4, "m/s"),
            ro("p", "总动量（定值 0）",
               f"{RC_M1}*({EXPR_RC_V1})+m2*({EXPR_RC_V2})", 4, "kg·m/s"),
            ro("e", "总动能（定值 100）",
               f"0.5*{RC_M1}*pow({EXPR_RC_V1},2)+0.5*m2*pow({EXPR_RC_V2},2)", 2, "J"),
            ro_status("fast", "质量小的那块是否跑得更快",
                      f"abs({EXPR_RC_V1})/abs({EXPR_RC_V2})", 1, ">",
                      "轻的跑得快：|v₁| : |v₂| = m₂ : m₁", "重的跑得更快"),
        ],
        "constant": {"of": "p", "label": "总动量恒为 0 —— 爆炸前后整个系统都静止"},
    }
    lesson = {
        "language": "zh-CN", "title": "反冲与爆炸",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>一个静止的物体（总质量 $1\\ \\mathrm{kg} + m_2$）因内部爆炸分成两块，"
            "释放的能量 $E = 100\\ \\mathrm{J}$ 全部变成两块的动能。"
            "其中一块质量 $1\\ \\mathrm{kg}$，另一块质量为 $m_2$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>两块的速度满足什么关系？</li>"
            "<li>求两块的速度大小；</li>"
            "<li>为什么质量小的那块一定跑得更快？</li></ol>"),
        "answerLabel": "$m_2 = 4$ kg 时",
        "answer": f"$v_1 = {K.f(K.explosion_velocities(1.0, 4.0, 100.0)[0], 3)}$ m/s，"
                  f"$v_2 = {K.f(K.explosion_velocities(1.0, 4.0, 100.0)[1], 3)}$ m/s",
    }
    steps = [
        {"title": "动量守恒 + 能量守恒",
         "content": ("<p>爆炸前整体静止，总动量为零，所以爆炸后</p>"
                     "<p>$m_1v_1 + m_2v_2 = 0$ ⇒ 两块**动量等大反向**，速度方向相反。</p>"
                     "<p>再加上能量守恒 $\\dfrac12m_1v_1^2 + \\dfrac12m_2v_2^2 = E$，"
                     "联立即可解出两个速度：</p>"
                     "<p>$|v_1| = \\sqrt{\\dfrac{2Em_2}{m_1(m_1+m_2)}}$，"
                     "$|v_2| = \\sqrt{\\dfrac{2Em_1}{m_2(m_1+m_2)}}$。</p>")},
        {"title": "速度与质量成反比",
         "content": ("<p>由动量等大反向立即得到</p>"
                     "<p>$\\dfrac{|v_1|}{|v_2|} = \\dfrac{m_2}{m_1}$ —— "
                     "**速度与质量成反比**。</p>"
                     "<p>质量小的块一定跑得快。把滑块从 $m_2 = 1$ 拖到 $5$，"
                     "可以看到 $v_1$ 变大、$v_2$ 变小，但两块的动能之和恒为 $100\\ \\mathrm{J}$，"
                     "动量之和恒为 $0$。</p>")},
        {"title": "从爆炸到火箭",
         "content": ("<p>爆炸是「一次性反冲」，火箭则是「连续反冲」："
                     "不断把燃气向后高速喷出，每一份燃气带走一份向后的动量，"
                     "箭体就获得一份向前的动量。</p>"
                     "<p>注意**火箭不靠空气推**：在真空里照样能飞，"
                     "因为它靠的是动量守恒，不需要「踩」任何东西。"
                     "枪炮后坐、章鱼喷水、溜冰者互推，都是同一套式子。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 人船模型
# =====================================================================
BT_MP, BT_MB = 60.0, 120.0
EXPR_BT_XP = f"L*{BT_MB}/({BT_MP}+{BT_MB})"
EXPR_BT_XB = f"-L*{BT_MP}/({BT_MP}+{BT_MB})"


def build_boat() -> dict:
    for L in (0.2, 0.5, 1.5, 2.0, 3.0):
        xp, xb = K.boat_shift(BT_MP, BT_MB, L)
        _agree(f"人位移(L={L})", EXPR_BT_XP, xp, tol=1e-12, L=L)
        _agree(f"船位移(L={L})", EXPR_BT_XB, xb, tol=1e-12, L=L)
        _agree(f"相对位移 = L(L={L})", f"({EXPR_BT_XP})-({EXPR_BT_XB})", L, tol=1e-12, L=L)
        _agree(f"质心不动(L={L})", f"{BT_MP}*({EXPR_BT_XP})+{BT_MB}*({EXPR_BT_XB})", 0.0, tol=1e-9, L=L)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "boat", "L": "L",
                  "caption": "绿虚线是系统质心：人在船上走，质心始终不动"},
        "param": {"name": "L", "label": "人相对船走过的距离 $L$", "min": 0.2, "max": 3,
                  "step": 0.05, "value": 1.5, "unit": "m", "standard": 1.5,
                  "ticks": ["0.2", "1.5 (题设)", "3"]},
        "readouts": [
            ro("L", "人相对船走过 $L$", "L", 2, "m"),
            ro("xp", "人对地位移（向前）", EXPR_BT_XP, 4, "m"),
            ro("xb", "船对地位移（向后）", EXPR_BT_XB, 4, "m"),
            ro("rel", "人对船的实际位移", f"({EXPR_BT_XP})-({EXPR_BT_XB})", 4, "m"),
            ro("p", "系统总动量（定值 0）",
               f"{BT_MP}*({EXPR_BT_XP})+{BT_MB}*({EXPR_BT_XB})", 4, "kg·m"),
            ro_status("ratio", "位移比是否等于质量的反比（2 : 1）",
                      f"abs({EXPR_BT_XP})/abs({EXPR_BT_XB})", 2, "==",
                      "位移与质量成反比：人走得远、船退得近", "比例异常"),
        ],
        "constant": {"of": "p", "label": "人与船的「质量 × 位移」之和恒为 0 —— 质心一动不动"},
    }
    lesson = {
        "language": "zh-CN", "title": "人船模型",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>质量 $m = 60\\ \\mathrm{kg}$ 的人站在质量 $M = 120\\ \\mathrm{kg}$ 的静止小船上，"
            "从船头走到船尾，相对船走过 $L$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>人相对地面走了多远？船相对地面退了多远？</li>"
            "<li>为什么系统质心始终不动？</li>"
            "<li>拖动滑块，两者的位移比是多少？</li></ol>"),
        "answerLabel": "$L = 1.5$ m 时",
        "answer": f"人对地 ${K.f(K.boat_person_shift(BT_MP, BT_MB, 1.5), 3)}$ m，"
                  f"船对地 ${K.f(K.boat_boat_shift(BT_MP, BT_MB, 1.5), 3)}$ m",
    }
    steps = [
        {"title": "为什么质心不动",
         "content": ("<p>系统最初静止，总动量为零；水平方向上系统不受外力"
                     "（人与船之间的摩擦力是内力），所以总动量**始终为零**。</p>"
                     "<p>动量守恒 ⇒ $m x_1 + M x_2 = 0$ ⇒ "
                     "$\\dfrac{x_1}{x_2} = -\\dfrac{M}{m}$："
                     "**位移与质量成反比、方向相反**。</p>"
                     "<p>等价的说法是：质心位置 $x_C = \\dfrac{mx_1 + Mx_2}{m+M}$ 保持不变。</p>")},
        {"title": "解出各自的位移",
         "content": ("<p>再加上「人相对船走了 $L$」：$x_1 - x_2 = L$。</p>"
                     "<p>联立解得</p>"
                     "<p>$x_1 = \\dfrac{M}{m+M}L = \\dfrac{120}{180}\\times1.5 = 1.0\\ \\mathrm{m}$；</p>"
                     "<p>$x_2 = -\\dfrac{m}{m+M}L = -0.5\\ \\mathrm{m}$。</p>"
                     "<p>人向前走 $1\\ \\mathrm{m}$、船向后退 $0.5\\ \\mathrm{m}$，"
                     "两者**相对**移动了 $1.5\\ \\mathrm{m}$ —— 正好等于 $L$。</p>")},
        {"title": "用它的场合",
         "content": ("<p>人船模型的关键词是「**系统初动量为零、水平方向不受外力**」。</p>"
                     "<p>气球上的人沿绳爬、小车上的人走动、光滑冰面上两人互推，"
                     "全部是同一个模型，直接套 $\\dfrac{x_1}{x_2} = -\\dfrac{M}{m}$。</p>"
                     "<p>注意：摩擦力虽然是内力，但它确实让船动了起来 —— "
                     "**内力能改变各部分的运动，却改不了系统总动量**，这是这一节最值得体会的一点。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 子弹打木块
# =====================================================================
BL_M, BL_MBLOCK, BL_MU, BL_G = 0.02, 0.98, 0.2, 9.8
EXPR_BL_VP = f"{BL_M}*v/({BL_M}+{BL_MBLOCK})"
EXPR_BL_E0 = f"0.5*{BL_M}*pow(v,2)"


def build_bullet() -> dict:
    for v in (200.0, 300.0, 400.0, 500.0, 600.0):
        _agree(f"共同速度(v={v})", EXPR_BL_VP,
               K.bullet_common_v(BL_M, v, BL_MBLOCK), tol=1e-12, v=v)
        _agree(f"动能损失(v={v})", f"({EXPR_BL_E0})-0.5*({BL_M}+{BL_MBLOCK})*pow({EXPR_BL_VP},2)",
               K.bullet_kinetic_loss(BL_M, v, BL_MBLOCK), tol=1e-12, v=v)
        _agree(f"滑行距离(v={v})", f"pow({EXPR_BL_VP},2)/(2*{BL_MU}*{BL_G})",
               K.bullet_slide_distance(BL_M, v, BL_MBLOCK, BL_MU, BL_G), tol=1e-12, v=v)
        # 动能定理自洽
        s = K.bullet_slide_distance(BL_M, v, BL_MBLOCK, BL_MU, BL_G)
        _agree(f"动能定理(v={v})", f"{BL_MU}*({BL_M}+{BL_MBLOCK})*{BL_G}*s",
               K.kinetic(BL_M + BL_MBLOCK, K.bullet_common_v(BL_M, v, BL_MBLOCK)),
               tol=1e-9, v=v, s=s)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "bullet", "v": "v",
                  "caption": "子弹嵌入木块后一起滑行；绿箭头标出滑行距离"},
        "param": {"name": "v", "label": "子弹速度 $v$", "min": 200, "max": 600,
                  "step": 10, "value": 400.0, "unit": "m/s", "standard": 400.0,
                  "ticks": ["200", "400 (题设)", "600"]},
        "readouts": [
            ro("v", "子弹速度 $v$", "v", 0, "m/s"),
            ro("vp", "共同速度 $v\' = mv/(m+M)$", EXPR_BL_VP, 4, "m/s"),
            ro("loss", "动能损失", f"({EXPR_BL_E0})-0.5*({BL_M}+{BL_MBLOCK})*pow({EXPR_BL_VP},2)", 1, "J"),
            ro("pct", "损失百分比",
               f"(({EXPR_BL_E0})-0.5*({BL_M}+{BL_MBLOCK})*pow({EXPR_BL_VP},2))/({EXPR_BL_E0})*100", 2, "%"),
            ro("s", "滑行距离 $s = v\'^2/(2\\mu g)$",
               f"pow({EXPR_BL_VP},2)/(2*{BL_MU}*{BL_G})", 3, "m"),
            ro_status("keep", "子弹是否保留大部分动能（损失 < 97%）",
                      f"(({EXPR_BL_E0})-0.5*({BL_M}+{BL_MBLOCK})*pow({EXPR_BL_VP},2))/({EXPR_BL_E0})*100",
                      97, "<",
                      "子弹保留了可观动能", "≤ 3%：动能几乎全被耗散"),
        ],
        "constant": {"of": "mm", "label": "子弹 0.02 kg、木块 0.98 kg、动摩擦因数 0.2 都是定值"},
        "scalars": [{"name": "mm", "expr": f"{BL_M}"}],
    }
    lesson = {
        "language": "zh-CN", "title": "子弹打木块",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>质量 $m = 0.02\\ \\mathrm{kg}$ 的子弹以速度 $v$ 水平射入静止在粗糙水平面上的"
            "木块（$M = 0.98\\ \\mathrm{kg}$），并留在其中。"
            "木块与地面间的动摩擦因数 $\\mu = 0.2$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求子弹与木块的共同速度；</li>"
            "<li>求损失的动能，并求它占初动能的百分比；</li>"
            "<li>求此后木块滑行的距离。</li></ol>"),
        "answerLabel": "$v = 400$ m/s 时",
        "answer": f"$v' = {K.f(K.bullet_common_v(BL_M, 400.0, BL_MBLOCK), 3)}$ m/s，"
                  f"损失 ${K.f(K.bullet_kinetic_loss(BL_M, 400.0, BL_MBLOCK), 1)}$ J，"
                  f"滑行 ${K.f(K.bullet_slide_distance(BL_M, 400.0, BL_MBLOCK, BL_MU, BL_G), 2)}$ m",
    }
    steps = [
        {"title": "第一步：动量守恒求共同速度",
         "content": ("<p>子弹与木块相互作用的时间极短，"
                     "地面上摩擦力在这段时间内的冲量可忽略，所以动量守恒：</p>"
                     "<p>$mv = (m+M)v'$ ⇒ $v' = \\dfrac{m}{m+M}v$。</p>"
                     "<p>代入 $m = 0.02$、$M = 0.98$：$v' = 0.02v$。"
                     "$v = 400\\ \\mathrm{m/s}$ 时 $v' = 8\\ \\mathrm{m/s}$。</p>")},
        {"title": "第二步：动能损失有多大",
         "content": ("<p>$E_0 = \\dfrac12mv^2 = \\dfrac12\\times0.02\\times400^2 = 1600\\ \\mathrm{J}$；</p>"
                     "<p>碰后 $E' = \\dfrac12(m+M)v'^2 = \\dfrac12\\times1\\times64 = 32\\ \\mathrm{J}$。</p>"
                     "<p>损失 $1568\\ \\mathrm{J}$，占 $98\\%$ —— 几乎全部动能变成了内能（发热），"
                     "这正是「子弹打得木块很烫」的原因。</p>"
                     "<p>注意这里**不能用动能守恒**：子弹嵌入属于完全非弹性碰撞。</p>")},
        {"title": "第三步：用动能定理求滑行距离",
         "content": ("<p>此后木块与子弹一起运动，只受摩擦力（大小 $\\mu(m+M)g$）作用，"
                     "由动能定理：</p>"
                     "<p>$-\\mu(m+M)g\\,s = 0 - \\dfrac12(m+M)v'^2$ ⇒ "
                     "$s = \\dfrac{v'^2}{2\\mu g}$。</p>"
                     "<p>$v' = 8\\ \\mathrm{m/s}$、$\\mu = 0.2$ 时 $s \\approx 16.3\\ \\mathrm{m}$。</p>"
                     "<p>这里质量约掉了 —— 所以**滑行距离只由 $v'$ 与 $\\mu$ 决定**，"
                     "与木块多重无关。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 等质量弹性斜碰（90° 定理）
# =====================================================================
TD_V = 5.0
EXPR_TD_C = "cos(theta*PI/180)"
EXPR_TD_S = "sin(theta*PI/180)"
EXPR_TD_A1 = f"{TD_V}*cos(theta*PI/180)"       # |v₁′|
EXPR_TD_A2 = f"{TD_V}*sin(theta*PI/180)"       # |v₂′|
# v₁′ = (a1·c, a1·s)，v₂′ = (a2·s, −a2·c)；点积恒为 0
EXPR_TD_DOT = (f"({EXPR_TD_A1}*({EXPR_TD_C}))*({EXPR_TD_A2}*({EXPR_TD_S}))"
               f"+({EXPR_TD_A1}*({EXPR_TD_S}))*(-{EXPR_TD_A2}*({EXPR_TD_C}))")


def build_twod() -> dict:
    for th in (0.0, 15.0, 30.0, 45.0, 60.0, 90.0):
        a, b = K.equal_mass_elastic2d(TD_V, th)
        _agree(f"|v₁′|(θ={th})", EXPR_TD_A1, math.hypot(*a), tol=1e-12, theta=th)
        _agree(f"|v₂′|(θ={th})", EXPR_TD_A2, math.hypot(*b), tol=1e-12, theta=th)
        _agree(f"点积为零(θ={th})", EXPR_TD_DOT, a[0] * b[0] + a[1] * b[1], tol=1e-9, theta=th)
        _agree(f"动量守恒(θ={th})", f"({EXPR_TD_A1}*({EXPR_TD_C}))+({EXPR_TD_A2}*({EXPR_TD_S}))",
               a[0] + b[0], tol=1e-9, theta=th)
        _agree(f"动能守恒(θ={th})",
               f"0.5*pow({EXPR_TD_A1},2)+0.5*pow({EXPR_TD_A2},2)", 0.5 * TD_V * TD_V, tol=1e-9, theta=th)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "collide2d", "theta": "theta",
                  "caption": "灰虚线是碰前速度；两条彩色箭头是碰后两球的速度，恒成直角"},
        "param": {"name": "theta", "label": "入射球偏转角 $\\theta$", "min": 0, "max": 90,
                  "step": 5, "value": 45.0, "unit": "°", "standard": 45.0,
                  "ticks": ["0 (擦过)", "45 (题设)", "90 (正碰)"]},
        "readouts": [
            ro("th", "偏转角 $\\theta$", "theta", 0, "°"),
            ro("a1", "$|v_1\'| = v\\cos\\theta$", EXPR_TD_A1, 4, "m/s"),
            ro("a2", "$|v_2\'| = v\\sin\\theta$", EXPR_TD_A2, 4, "m/s"),
            ro("dot", "点积 $v_1\' \\cdot v_2\'$（恒为 0）", EXPR_TD_DOT, 6),
            ro("e", "总动能（定值 12.5）",
               f"0.5*pow({EXPR_TD_A1},2)+0.5*pow({EXPR_TD_A2},2)", 3, "J"),
            ro_status("perp", "两出射速度是否垂直",
                      f"abs({EXPR_TD_DOT})", 1e-6, "<",
                      "恒垂直：90° 定理成立", "不垂直"),
        ],
        "constant": {"of": "e", "label": "总动能恒为 12.5 J，且两出射方向恒成 90°"},
    }
    lesson = {
        "language": "zh-CN", "title": "等质量弹性斜碰的 90° 定理",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>质量相同的两小球（均为 $m$）在光滑水平面上发生**弹性**碰撞。"
            "碰前一个以 $v = 5\\ \\mathrm{m/s}$ 沿 $+x$ 运动，另一个静止。"
            "碰后入射球的运动方向与 $+x$ 成 $\\theta$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求两球碰后的速度大小；</li>"
            "<li>证明两球碰后的运动方向互相垂直；</li>"
            "<li>$\\theta = 0^\\circ$ 与 $\\theta = 90^\\circ$ 分别对应什么情况？</li></ol>"),
        "answerLabel": "$\\theta = 45°$ 时",
        "answer": f"$|v_1'| = |v_2'| = {K.f(TD_V * math.cos(math.radians(45)), 4)}$ m/s，"
                  f"且 $v_1' \\perp v_2'$",
    }
    steps = [
        {"title": "用「动量三角形」定形",
         "content": ("<p>动量守恒是**矢量式**：$\\vec p_1 = \\vec p_1' + \\vec p_2'$。"
                     "画成图就是一个三角形（本页虚线补齐的正是它）。</p>"
                     "<p>等质量时 $\\vec v_1 = \\vec v_1' + \\vec v_2'$；"
                     "弹性碰撞还要求 $v_1^2 = v_1'^2 + v_2'^2$。</p>"
                     "<p>把第二个式子看成「直角三角形的勾股定理」，"
                     "就立刻知道这个动量三角形是**直角三角形**："
                     "两条出射速度互相垂直。</p>")},
        {"title": "纯代数的证明",
         "content": ("<p>由 $\\vec v_1 = \\vec v_1' + \\vec v_2'$ 两边取模方：</p>"
                     "<p>$v_1^2 = v_1'^2 + v_2'^2 + 2\\vec v_1'\\cdot\\vec v_2'$。</p>"
                     "<p>再用弹性碰撞的 $v_1^2 = v_1'^2 + v_2'^2$ 相减，"
                     "得到 $2\\vec v_1'\\cdot\\vec v_2' = 0$，即 $\\vec v_1'\\perp\\vec v_2'$。</p>"
                     "<p>这与「用哪条路径」无关，也与碰前速度大小无关 —— "
                     "只要**等质量 + 弹性 + 一个静止**，结论就成立。"
                     "读数区里的点积恒为 $0$，拖滑块时一动不动。</p>")},
        {"title": "两个端点",
         "content": ("<p>· $\\theta = 0^\\circ$：$|v_1'| = v$、$|v_2'| = 0$ —— "
                     "两球**擦过**，入射球照旧跑，靶球不动（动量三角形退化成一条线段）。</p>"
                     "<p>· $\\theta = 90^\\circ$：$|v_1'| = 0$、$|v_2'| = v$ —— "
                     "**正碰**，入射球停下、靶球带走全部速度，与一维的等质量交换速度完全一致。</p>"
                     "<p>台球里「正碰换位、斜碰分开成直角」是这个定理最直观的验证。"
                     "彩色的两条箭头把整个过程画在了同一张图上。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "impulse": build_impulse,
    "inelastic": build_inelastic,
    "elastic": build_elastic,
    "recoil": build_recoil,
    "boat": build_boat,
    "bullet": build_bullet,
    "twod": build_twod,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="动量与碰撞 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
