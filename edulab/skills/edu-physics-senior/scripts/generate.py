#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页高中力学交互网页。

数据由 lib/mech_kernel.py 的 sympy 精确计算驱动（单一数据源）：传送带、追及相遇、
斜面上滑、平抛、牛顿第二定律、动能定理、圆周运动、匀变速 v-t 图全部精确算出；
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

sys.path.insert(0, str(SKILL_DIR.parent.parent / "shared"))   # 共享运行时（edulab/shared/skillkit.py）
sys.path.insert(0, str(SKILL_DIR / "lib"))
import sympy as sp                       # noqa: E402
import mech_kernel as K                  # noqa: E402
from mech_kernel import tex, f           # noqa: E402
from skillkit import cli, required_sections   # noqa: E402


# =====================================================================
# 1) 传送带：摩擦加速 a=μg、共速时间、划痕（相对位移）
# =====================================================================
def build_belt() -> dict:
    # 物块以 v0=4 m/s 滑上以 vbelt=1 m/s 运行的水平传送带，μ=0.2（初中 g=10）
    sol = K.solve_belt(v0=4, vbelt=1, mu=sp.Rational(1, 5))
    assert sol["a"] == 2 and sol["t1"] == sp.Rational(3, 2) and sol["scratch"] == sp.Rational(9, 4)
    board = {
        "view": {"xRange": [0, 9.5], "yRange": [0, 6.2]},
        "scene": {
            "kind": "belt", "caption": "水平传送带（v带=1 m/s，物块以 v₀=4 m/s 滑上）",
            "vbelt": 1, "boxW": 0.9,
            "xblk": "1.0+0.8*(t<1.5 ? (4*t-t*t) : (3.75+(t-1.5)))",
            "vblk": "t<1.5 ? (4-2*t) : 1",
            "ffric": "t<1.5 ? -2 : 0", "fscale": 0.35,
            "scratchPx": "0.8*(t<1.5 ? (3*t-t*t) : 2.25)",
            "xbeltStart": 1.0,
            "scratchLen": "t<1.5 ? (3*t-t*t) : 2.25",
            "phase": "滑动阶段 f=μmg 向左（a=2m/s²）；共速后 f=0 随带匀速",
        },
        "param": {"name": "t", "label": "时间 $t$", "min": 0.2, "max": 3, "step": 0.02,
                  "value": 1.5, "unit": " s", "ticks": ["0.2s", "1.5s (共速)", "3s"]},
        "readouts": [
            {"id": "t", "label": "时间 $t$", "type": "expr", "expr": "t", "digits": 2, "unit": "s"},
            {"id": "v", "label": "物块速度 $v$", "type": "expr", "expr": "t<1.5?(4-2*t):1",
             "digits": 2, "unit": "m/s", "highlight": True},
            {"id": "a", "label": "加速度 $a$", "type": "expr", "expr": "t<1.5?-2:0",
             "digits": 1, "unit": "m/s²"},
            {"id": "ds", "label": "划痕 $\\Delta s$", "type": "expr", "expr": "t<1.5?(3*t-t*t):2.25",
             "digits": 2, "unit": "m"},
            {"id": "st", "label": "状态", "type": "status", "expr": "abs((t<1.5?(4-2*t):1)-1)",
             "op": "<", "rhs": 0.01, "okText": "已共速：随带匀速，f=0",
             "badText": "相对滑动：受滑动摩擦 f=μmg"},
        ],
        "constant": {"label": "$\\Delta s_{\\max} = \\dfrac{9}{4} = 2.25\\ \\mathrm{m}$（共速后划痕不再变长）"},
        "legend": [
            {"color": "effort", "text": "物块速度 v（红箭头 f 为滑动摩擦）"},
            {"color": "bad", "text": "划痕（物块相对带面滑过的距离）"},
            {"color": "metal", "text": "传送带（v带=1 m/s）"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "传送带问题：滑动摩擦与共速",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>水平传送带以 $v_{\\mathrm{带}}=1\\ \\mathrm{m/s}$ 顺时针运行，"
                    "一质量 $m=1\\ \\mathrm{kg}$ 的物块以 $v_0=4\\ \\mathrm{m/s}$ 的初速度滑上传送带，"
                    "物块与带间动摩擦因数 $\\mu=0.2$（取 $g=10\\ \\mathrm{m/s^2}$）。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求物块滑动阶段的加速度大小与方向、经多长时间与带共速；</li>"
                    "<li>求共速前物块相对传送带滑过的距离（划痕长）；</li>"
                    "<li>拖动滑块观察物块速度、摩擦力与划痕的变化。</li></ol>"),
        "answerLabel": "加速度 / 共速时间 / 划痕",
        "answer": (f"$a = \\mu g = 2\\ \\mathrm{{m/s^2}}$（向左，减速），"
                   f"$t_1 = {tex(sol['t1'])}\\ \\mathrm{{s}} = 1.5\\ \\mathrm{{s}}$，"
                   f"$\\Delta s = {tex(sol['scratch'])}\\ \\mathrm{{m}} = 2.25\\ \\mathrm{{m}}$"),
    }
    steps = [
        {"title": "分析相对运动与摩擦方向",
         "content": ("<p>物块速度 $4\\ \\mathrm{m/s}$ 大于带速 $1\\ \\mathrm{m/s}$，"
                     "物块相对传送带<b>向前</b>滑动，故滑动摩擦力方向<b>向后（向左）</b>，"
                     "物块做匀减速运动。</p>")},
        {"title": "求加速度",
         "content": ("<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ a = \\mu g = 0.2\\times10 = 2\\ \\mathrm{m/s^2} $$</div>"
                     "<p>方向水平向左。</p>")},
        {"title": "求共速时间",
         "content": (f"<p>物块减速到与带共速 $v=1\\ \\mathrm{{m/s}}$ 所需时间：</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ t_1 = \\frac{{v_0-v}}{{a}} = \\frac{{4-1}}{{2}} = {tex(sol['t1'])}\\ \\mathrm{{s}} $$</div>"),
        },
        {"title": "求划痕长度",
         "content": (f"<p>共速前：物块位移 $x_1 = v_0t_1 - \\frac{{a t_1^2}}{{2}} = "
                     f"4\\times1.5-\\frac{{2\\times2.25}}{{2}} = 3.75\\ \\mathrm{{m}}$，"
                     f"传送带位移 $x_{{\\mathrm{{带}}}} = v t_1 = 1.5\\ \\mathrm{{m}}$。</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ \\Delta s = x_1 - x_{{\\mathrm{{带}}}} = 3.75-1.5 = "
                     f"{tex(sol['scratch'])}\\ \\mathrm{{m}} $$</div>"
                     f"<p>这就是带面上划痕的长度（物块相对带面向前划过 2.25 m）。</p>"),
        },
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：$t<1.5\\ \\mathrm{s}$ 时物块减速、摩擦力箭头向左、划痕逐渐变长；"
                     "$t=1.5\\ \\mathrm{s}$ 时恰好共速（状态灯变绿），"
                     "此后物块随带以 $1\\ \\mathrm{m/s}$ 匀速、摩擦力消失、<b>划痕停在 2.25 m 不再变化</b>"
                     "（定值指示）。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 追及相遇：速度相等时间距最大
# =====================================================================
def build_chase() -> dict:
    # A 从 x=0 以 8 m/s 匀速；B 从 x=10 m 由静止以 2 m/s² 匀加速
    sol = K.solve_chase(xA0=0, vA=8, xB0=10, aB=2)
    assert sol["t1"] == 4 and sol["d_max"] == 6
    assert sol["t_meet"] is not None and sp.simplify(sol["t_meet"] - (4 - sp.sqrt(6))) == 0
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6.2]},
        "scene": {
            "kind": "chase", "caption": "A 匀速 8 m/s 追 B（B 从 x=10m 静止起，a=2m/s²）",
            "kx": 0.2, "t": "t",
            "xA": "8*t", "vA": 8,
            "xB": "10+t*t", "vB": "2*t",
        },
        "param": {"name": "t", "label": "时间 $t$", "min": 0, "max": 5, "step": 0.02,
                  "value": 2, "unit": " s", "ticks": ["0s", "2s", "5s"]},
        "readouts": [
            {"id": "t", "label": "时间 $t$", "type": "expr", "expr": "t", "digits": 2, "unit": "s"},
            {"id": "xA", "label": "$x_A = 8t$", "type": "expr", "expr": "8*t", "digits": 1, "unit": "m"},
            {"id": "xB", "label": "$x_B = 10+t^2$", "type": "expr", "expr": "10+t*t", "digits": 1, "unit": "m"},
            {"id": "gap", "label": "间距 $\\Delta x$", "type": "expr", "expr": "abs(8*t-(10+t*t))",
             "digits": 2, "unit": "m", "highlight": True},
            {"id": "st", "label": "追及状态", "type": "status", "expr": "(10+t*t)-8*t", "op": ">",
             "rhs": 0, "okText": "B 在前：A 尚未追上", "badText": "A 已反超 B"},
        ],
        "constant": {"label": "$t_1 = \\dfrac{v_A}{a_B} = 4\\ \\mathrm{s}$（速度相等时相距最远 $\\Delta x_{\\max}=6\\ \\mathrm{m}$）"},
        "legend": [
            {"color": "effort", "text": "A 车（匀速 v_A=8 m/s）"},
            {"color": "force", "text": "B 车（初速 0，a=2 m/s²）"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "追及相遇：速度相等时间距最大",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>平直公路上，A 车以 $v_A=8\\ \\mathrm{m/s}$ 匀速行驶，"
                    "经过停在 $x=10\\ \\mathrm{m}$ 处的 B 车旁时，B 车立即以 $a_B=2\\ \\mathrm{m/s^2}$ "
                    "由静止匀加速前进。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求 A、B 速度相等的时刻及此时两车间的最大间距；</li>"
                    "<li>A 车能否追上 B 车？若能，求追上时刻；</li>"
                    "<li>拖动滑块观察间距随时间的变化。</li></ol>"),
        "answerLabel": "速度相等时刻 / 最大间距 / 相遇时刻",
        "answer": (f"$t_1 = {tex(sol['t1'])}\\ \\mathrm{{s}}$ 时速度相等，"
                   f"$\\Delta x_{{\\max}} = {tex(sol['d_max'])}\\ \\mathrm{{m}}$；"
                   f"A 在 $t = {tex(sol['t_meet'])}\\ \\mathrm{{s}} \\approx 1.55\\ \\mathrm{{s}}$ 追上 B"),
    }
    steps = [
        {"title": "写出两车位移表达式",
         "content": ("<p>以 A 车出发点为原点、运动方向为正方向：</p>"
                     "<p class='text-center'>$$ x_A = v_A t = 8t,\\qquad "
                     "x_B = 10 + \\frac{a_B t^2}{2} = 10+t^2 $$</p>")},
        {"title": "速度相等 → 间距极值",
         "content": ("<p>间距 $\\Delta x = x_B - x_A = 10+t^2-8t$。"
                     "当 $v_A = v_B$ 即 $8 = 2t$ 时：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ t_1 = 4\\ \\mathrm{s},\\quad \\Delta x_{\\max} = 10+16-32 = -6\\ \\mathrm{m} $$</div>"
                     "<p>即此时 A 已反超 B <b>6 m</b>——这是 A 领先的最大距离"
                     "（$t<4\\ \\mathrm{s}$ 前 $v_A>v_B$ 间距增大，之后 $v_B>v_A$ 间距减小）。</p>")},
        {"title": "判断能否追上",
         "content": (f"<p>令 $x_A = x_B$：$8t = 10+t^2$，即 $t^2-8t+10=0$：</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ t = \\frac{{8\\pm\\sqrt{{64-40}}}}{{2}} = 4\\pm\\sqrt6 $$</div>"
                     f"<p>两根均正，说明 A 先在 $t = 4-\\sqrt6 \\approx 1.55\\ \\mathrm{{s}}$ "
                     f"<b>追上并超过</b> B（此时 $x_A = 8(4-\\sqrt6)\\approx12.4\\ \\mathrm{{m}}$），"
                     f"之后 B 不断加速，又在 $t = 4+\\sqrt6 \\approx 6.45\\ \\mathrm{{s}}$ 反超 A。</p>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：初始 B 在前 10 m；$t\\approx1.55\\ \\mathrm{s}$ 时两车相遇"
                     "（状态灯由绿变红）；随后 A 领先，在 $t=4\\ \\mathrm{s}$（速度相等）"
                     "<b>领先最多 6 m</b>（定值指示）；此后间距重新缩小。<b>解追及问题的关键"
                     "就是抓住\"速度相等\"这一临界时刻</b>。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 斜面上滑：a=g(sinθ+μcosθ)、上滑最大距离、能否下滑
# =====================================================================
def build_incline() -> dict:
    sol = K.solve_incline(theta=30, v0=6, mu=sp.Rational(1, 5))
    a_up = 5 + sp.sqrt(3)
    assert sp.simplify(sol["a_up"] - a_up) == 0 and sol["can_down"] is True
    assert sp.simplify(sol["s_max"] - 18 / a_up) == 0        # v0²/(2a) = 36/(2(5+√3))
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6.4]},
        "scene": {
            "kind": "ramp", "caption": "物块以 v₀=6 m/s 沿 θ=30° 斜面上滑（μ=0.2）",
            "rampLen": 8.6, "theta_deg": 30, "boxW": 0.8,
            "s_blk": "2.4*(t<=0.891 ? (6*t-3.366*t*t) : max(0, 2.674-1.634*pow(t-0.891,2)))",
            "sdisp": "t<=0.891 ? (6*t-3.366*t*t) : max(0, 2.674-1.634*pow(t-0.891,2))",
            "v_blk": "t<=0.891 ? (6-6.732*t) : (t<=2.17 ? -3.268*(t-0.891) : 0)",
            "G": 20, "N": "20*cos(30*PI/180)", "f_fric": "0.2*20*cos(30*PI/180)",
            "fscale": 0.06,
        },
        "param": {"name": "t", "label": "时间 $t$", "min": 0, "max": 2.2, "step": 0.01,
                  "value": 0.5, "unit": " s", "ticks": ["0s", "0.89s (最高点)", "2.2s"]},
        "readouts": [
            {"id": "t", "label": "时间 $t$", "type": "expr", "expr": "t", "digits": 2, "unit": "s"},
            {"id": "v", "label": "速度 $v$（沿斜面）", "type": "expr",
             "expr": "t<=0.891?(6-6.732*t):(t<=2.17?-3.268*(t-0.891):0)",
             "digits": 2, "unit": "m/s", "highlight": True},
            {"id": "s", "label": "上滑距离 $s$", "type": "expr",
             "expr": "t<=0.891?(6*t-3.366*t*t):max(0,2.674-1.634*pow(t-0.891,2))",
             "digits": 2, "unit": "m"},
            {"id": "a", "label": "$a_{\\mathrm{上}}$", "type": "expr", "expr": "5+sqrt(3)",
             "digits": 2, "unit": "m/s²"},
            {"id": "st", "label": "运动状态", "type": "status", "expr": "6-6.732*t", "op": ">",
             "rhs": 0, "okText": "上滑中（减速）", "badText": "已过最高点，下滑中（加速）"},
        ],
        "constant": {"label": "$a_{\\mathrm{上}} = g(\\sin\\theta+\\mu\\cos\\theta) = 5+\\sqrt3 \\approx 6.73\\ \\mathrm{m/s^2}$；"
                              "$\\tan 30^\\circ > \\mu$，物块能下滑"},
        "legend": [
            {"color": "force", "text": "重力 G=mg=20 N"},
            {"color": "good", "text": "支持力 N=mg cosθ"},
            {"color": "meter", "text": "滑动摩擦 f=μN（与运动方向相反）"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "斜面上滑：摩擦斜面的减速与下滑判断",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>质量 $m=2\\ \\mathrm{kg}$ 的物块以 $v_0=6\\ \\mathrm{m/s}$ 的初速度沿倾角 "
                    "$\\theta=30^\\circ$ 的斜面上滑，物块与斜面间动摩擦因数 $\\mu=0.2$（取 "
                    "$g=10\\ \\mathrm{m/s^2}$）。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求物块上滑时的加速度大小与上滑的最大距离；</li>"
                    "<li>判断物块到达最高点后能否下滑，若能求下滑加速度；</li>"
                    "<li>拖动滑块观察物块上滑—返回的全过程。</li></ol>"),
        "answerLabel": "a上 / s_max / 能否下滑",
        "answer": (f"$a_{{\\mathrm{{上}}}} = {tex(a_up)}\\ \\mathrm{{m/s^2}} \\approx 6.73\\ \\mathrm{{m/s^2}}$，"
                   f"$s_{{\\max}} = \\dfrac{{v_0^2}}{{2a}} = {tex(sol['s_max'])}\\ \\mathrm{{m}} \\approx 2.67\\ \\mathrm{{m}}$；"
                   f"$\\tan\\theta > \\mu$，能下滑，$a_{{\\mathrm{{下}}}} = 5-\\sqrt3 \\approx 3.27\\ \\mathrm{{m/s^2}}$"),
    }
    steps = [
        {"title": "受力分析（上滑阶段）",
         "content": ("<p>物块相对斜面<b>向上</b>滑动，摩擦力沿斜面<b>向下</b>。"
                     "沿斜面方向：重力分量 $mg\\sin\\theta$ 向下、摩擦力 $f=\\mu N$ 向下；"
                     "垂直斜面：$N = mg\\cos\\theta$。</p>")},
        {"title": "求上滑加速度",
         "content": ("<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ a_{\\mathrm{上}} = \\frac{mg\\sin\\theta+\\mu mg\\cos\\theta}{m} "
                     "= g(\\sin\\theta+\\mu\\cos\\theta) $$</div>"
                     f"<p class='text-center'>$$ = 10\\left(\\frac12+0.2\\times\\frac{{\\sqrt3}}2\\right) "
                     f"= 5+\\sqrt3 = {tex(a_up)}\\ \\mathrm{{m/s^2}} \\approx 6.73\\ \\mathrm{{m/s^2}} $$</p>")},
        {"title": "求上滑最大距离",
         "content": (f"<p>由 $v^2-v_0^2 = -2as$，到最高点 $v=0$：</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ s_{{\\max}} = \\frac{{v_0^2}}{{2a_{{\\mathrm{{上}}}}}} = "
                     f"\\frac{{36}}{{2(5+\\sqrt3)}} = {tex(sol['s_max'])}\\ \\mathrm{{m}} \\approx 2.67\\ \\mathrm{{m}} $$</div>")},
        {"title": "判断能否下滑",
         "content": ("<p>到达最高点后：下滑动力为 $mg\\sin\\theta$，最大静摩擦约 $\\mu mg\\cos\\theta$。"
                     "因为 $\\tan30^\\circ = \\frac{\\sqrt3}{3}\\approx0.577 > \\mu=0.2$，"
                     "<b>重力下滑分量大于最大静摩擦，物块将下滑</b>：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ a_{\\mathrm{下}} = g(\\sin\\theta-\\mu\\cos\\theta) = 5-\\sqrt3 \\approx 3.27\\ \\mathrm{m/s^2} $$</div>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：物块先减速上滑（$v>0$，状态灯绿），$t\\approx0.89\\ \\mathrm{s}$ 到达最高点，"
                     "再加速下滑（$v<0$，状态灯红），约 $t\\approx2.17\\ \\mathrm{s}$ 回到斜面底端。"
                     "注意上滑与下滑的加速度<b>大小不同</b>（$6.73$ vs $3.27$）——"
                     "因为两个阶段摩擦力方向都沿斜面向下/向上与相对运动相反，"
                     "上滑时摩擦\"助阻\"、下滑时摩擦\"助行\"。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 平抛运动：水平匀速 + 竖直自由落体
# =====================================================================
def build_projectile() -> dict:
    sol = K.solve_projectile(v0=10, theta_deg=0, h0=20)
    assert sol["t"] == 2 and sol["R"] == 20 and sp.simplify(sol["v_land"] - 10 * sp.sqrt(5)) == 0
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6.4]},
        "scene": {
            "kind": "projectile", "caption": "从 h=20m 高处以 v₀=10 m/s 水平抛出（g=10）",
            "h0": 4, "g": 2, "v0": 2, "theta_deg": 0,
            "t_total": 2.4, "t": "t", "vscale": 0.5,
            "H": 4, "Hdisp": 20, "t_peak": 0,
            "hdisp": "max(0,20-5*t*t)",
        },
        "param": {"name": "t", "label": "时间 $t$", "min": 0.1, "max": 2.2, "step": 0.02,
                  "value": 1, "unit": " s", "ticks": ["0.1s", "1s", "2.2s (落地)"]},
        "readouts": [
            {"id": "t", "label": "时间 $t$", "type": "expr", "expr": "t", "digits": 2, "unit": "s"},
            {"id": "vx", "label": "水平速度 $v_x$", "type": "expr", "expr": "10",
             "digits": 1, "unit": "m/s"},
            {"id": "vy", "label": "竖直速度 $v_y=gt$", "type": "expr", "expr": "10*t",
             "digits": 1, "unit": "m/s"},
            {"id": "v", "label": "合速度 $v$", "type": "expr", "expr": "sqrt(100+pow(10*t,2))",
             "digits": 2, "unit": "m/s", "highlight": True},
            {"id": "h", "label": "高度 $h$", "type": "expr", "expr": "max(0,20-5*t*t)",
             "digits": 2, "unit": "m"},
            {"id": "st", "label": "状态", "type": "status", "expr": "20-5*t*t", "op": ">",
             "rhs": 0, "okText": "在空中飞行", "badText": "已落地"},
        ],
        "constant": {"label": "$v_x \\equiv 10\\ \\mathrm{m/s}$（水平方向不受力，保持匀速）"},
        "legend": [
            {"color": "effort", "text": "水平分速度 v_x（恒定）"},
            {"color": "force", "text": "竖直分速度 v_y=gt（自由落体）"},
            {"color": "good", "text": "合速度 v"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "平抛运动：水平匀速 + 自由落体的合成",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>从距地面 $h=20\\ \\mathrm{m}$ 高处，以 $v_0=10\\ \\mathrm{m/s}$ 的速度"
                    "<b>水平抛出</b>一小球（取 $g=10\\ \\mathrm{m/s^2}$，不计空气阻力）。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求小球落地的时间与水平射程；</li>"
                    "<li>求落地时速度的大小；</li>"
                    "<li>拖动滑块观察速度分量与轨迹的变化。</li></ol>"),
        "answerLabel": "飞行时间 / 射程 / 落地速度",
        "answer": (f"$t = {tex(sol['t'])}\\ \\mathrm{{s}}$，$R = {tex(sol['R'])}\\ \\mathrm{{m}}$，"
                   f"$v = {tex(sol['v_land'])}\\ \\mathrm{{m/s}} = 10\\sqrt5 \\approx 22.4\\ \\mathrm{{m/s}}$"),
    }
    steps = [
        {"title": "运动的分解",
         "content": ("<p>平抛运动 = <b>水平方向的匀速直线运动</b>（不受力）"
                     "+ <b>竖直方向的自由落体运动</b>（初速为 0）。两个分运动独立进行、"
                     "互不影响，具有等时性。</p>")},
        {"title": "由竖直方向求时间",
         "content": (f"<p>竖直方向 $h = \\frac{{gt^2}}2$：</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ t = \\sqrt{{\\frac{{2h}}g}} = \\sqrt{{\\frac{{40}}{{10}}}} = {tex(sol['t'])}\\ \\mathrm{{s}} $$</div>")},
        {"title": "求水平射程",
         "content": (f"<p>水平方向匀速：</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ R = v_0 t = 10\\times2 = {tex(sol['R'])}\\ \\mathrm{{m}} $$</div>")},
        {"title": "求落地速度",
         "content": (f"<p>落地时 $v_x = 10\\ \\mathrm{{m/s}}$，$v_y = gt = 20\\ \\mathrm{{m/s}}$，由勾股合成：</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ v = \\sqrt{{v_x^2+v_y^2}} = \\sqrt{{100+400}} = 10\\sqrt5 "
                     f"= {tex(sol['v_land'])}\\ \\mathrm{{m/s}} \\approx 22.4\\ \\mathrm{{m/s}} $$</div>"
                     f"<p>落地速度方向与水平夹角 $\\alpha = \\arctan\\frac{{v_y}}{{v_x}} = "
                     f"\\arctan 2 \\approx 63.4^\\circ$。</p>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：水平箭头长度<b>始终不变</b>（$v_x\\equiv10\\ \\mathrm{m/s}$，定值指示），"
                     "竖直箭头越来越长（$v_y=gt$），合速度方向逐渐偏向下方——"
                     "轨迹是抛物线。$t=2\\ \\mathrm{s}$ 时高度读数归零、状态灯变红（落地）。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 牛顿第二定律：a = (F−μmg)/m
# =====================================================================
def build_newton2() -> dict:
    sol = K.solve_newton2(m=2, F=10, mu=sp.Rational(1, 10))
    assert sol["N"] == 20 and sol["f"] == 2 and sol["a"] == 4
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6.2]},
        "scene": {
            "kind": "ground", "caption": "水平面上 m=2kg 物块受水平拉力 F（μ=0.1，t=1s 后）",
            "m": 2, "boxW": 1.0, "G": 20, "fscale": 0.15, "vscale": 0.25, "t": 1,
            "F": "F", "f_fric": "F<=2 ? F : 2",
            "x_start": 1.0,
            "x_blk": "1.0+max(0,(F-2)/4)",
            "s_blk": "max(0,(F-2)/4)",
            "v_blk": "max(0,(F-2)/2)",
        },
        "param": {"name": "F", "label": "拉力 $F$", "min": 0, "max": 20, "step": 0.2,
                  "value": 10, "unit": " N", "ticks": ["0N", "10N (题设)", "20N"]},
        "readouts": [
            {"id": "F", "label": "拉力 $F$", "type": "expr", "expr": "F", "digits": 1, "unit": "N"},
            {"id": "N", "label": "支持力 $N=mg$", "type": "expr", "expr": "20", "digits": 1, "unit": "N"},
            {"id": "fr", "label": "摩擦力 $f$", "type": "expr", "expr": "F<=2?F:2",
             "digits": 1, "unit": "N"},
            {"id": "a", "label": "加速度 $a=\\frac{F-f}{m}$", "type": "expr", "expr": "max(0,(F-2)/2)",
             "digits": 2, "unit": "m/s²", "highlight": True},
            {"id": "st", "label": "状态", "type": "status", "expr": "F-2", "op": ">",
             "rhs": 0, "okText": "F > f：物块加速前进", "badText": "F ≤ f：推不动，a=0"},
        ],
        "constant": {"label": "$f = \\mu mg = 0.1\\times2\\times10 = 2\\ \\mathrm{N}$（滑动后恒定；$F\\le2\\ \\mathrm{N}$ 时 $a=0$）"},
        "legend": [
            {"color": "effort", "text": "拉力 F（滑块改变）"},
            {"color": "force", "text": "摩擦力 f（静摩擦随 F 增大，滑动后恒为 2N）"},
            {"color": "aux", "text": "重力 G 与支持力 N（二力平衡）"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "牛顿第二定律：a = (F−f)/m",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>质量 $m=2\\ \\mathrm{kg}$ 的物块静止在水平地面上，"
                    "与地面间动摩擦因数 $\\mu=0.1$（取 $g=10\\ \\mathrm{m/s^2}$）。"
                    "现用水平拉力 $F=10\\ \\mathrm{N}$ 拉动物块。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求地面对物块的支持力、摩擦力与物块的加速度；</li>"
                    "<li>拖动滑块改变 $F$，观察加速度如何变化；$F$ 小于多少时物块不动？</li></ol>"),
        "answerLabel": "支持力 N / 摩擦力 f / 加速度 a",
        "answer": (f"$N = {tex(sol['N'])}\\ \\mathrm{{N}}$，$f = {tex(sol['f'])}\\ \\mathrm{{N}}$，"
                   f"$a = \\dfrac{{F-f}}{{m}} = \\dfrac{{10-2}}{{2}} = {tex(sol['a'])}\\ \\mathrm{{m/s^2}}$"),
    }
    steps = [
        {"title": "竖直方向：求支持力",
         "content": ("<p>竖直方向物块平衡：$N = mg = 2\\times10 = 20\\ \\mathrm{N}$。</p>")},
        {"title": "求滑动摩擦力",
         "content": ("<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ f = \\mu N = 0.1\\times20 = 2\\ \\mathrm{N} $$</div>"
                     "<p>$F=10\\ \\mathrm{N} > f$，物块确实被拉动，$f$ 为滑动摩擦。</p>")},
        {"title": "牛顿第二定律求加速度",
         "content": (f"<p>水平方向合力 $F_合 = F - f = 10-2 = 8\\ \\mathrm{{N}}$：</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ a = \\frac{{F_合}}m = \\frac{{8}}2 = {tex(sol['a'])}\\ \\mathrm{{m/s^2}} $$</div>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块改变 $F$：<b>$F\\le2\\ \\mathrm{N}$ 时物块不动</b>（$a=0$，状态灯红）——"
                     "静摩擦力随 $F$ 增大而增大、恰好平衡；<b>$F>2\\ \\mathrm{N}$ 后</b>物块滑动，"
                     "摩擦力恒为 2 N，$a = \\frac{F-2}{2}$ 随 $F$ <b>线性增大</b>。"
                     "这体现了牛顿第二定律：<b>加速度与合力成正比、与质量成反比</b>。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 动能定理：W合 = ΔEk = ½mv²
# =====================================================================
def build_work_energy() -> dict:
    sol = K.solve_work_energy(m=2, v0=0, F=10, mu=sp.Rational(1, 10), s=5)
    assert sol["W_net"] == 40 and sp.simplify(sol["v"] - 2 * sp.sqrt(10)) == 0
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6.2]},
        "scene": {
            "kind": "ground", "caption": "m=2kg 物块在 F=10N、f=2N 作用下位移 s",
            "m": 2, "boxW": 1.0, "G": 20, "F": 10, "f_fric": 2,
            "fscale": 0.15, "vscale": 0.22, "t": "sqrt(s/2)",
            "x_start": 1.0, "x_blk": "1.0+s", "s_blk": "s",
            "v_blk": "sqrt(max(0,8*s))",
        },
        "param": {"name": "s", "label": "位移 $s$", "min": 0, "max": 8, "step": 0.05,
                  "value": 5, "unit": " m", "ticks": ["0m", "5m (题设)", "8m"]},
        "readouts": [
            {"id": "s", "label": "位移 $s$", "type": "expr", "expr": "s", "digits": 2, "unit": "m"},
            {"id": "wf", "label": "拉力做功 $W_F=Fs$", "type": "expr", "expr": "10*s", "digits": 1, "unit": "J"},
            {"id": "wfr", "label": "摩擦做功 $W_f=-fs$", "type": "expr", "expr": "-2*s", "digits": 1, "unit": "J"},
            {"id": "wn", "label": "合外力功 $W_合$", "type": "expr", "expr": "8*s",
             "digits": 1, "unit": "J", "highlight": True},
            {"id": "v", "label": "末速度 $v$", "type": "expr", "expr": "sqrt(max(0,8*s))",
             "digits": 2, "unit": "m/s"},
            {"id": "st", "label": "动能定理", "type": "status",
             "expr": "abs(pow(sqrt(max(0,8*s)),2)-8*s)", "op": "<", "rhs": 0.01,
             "okText": "½mv² = W合 ✓ 定理成立", "badText": "—"},
        ],
        "constant": {"label": "$W_合 = (F-f)s = 8s \\equiv \\tfrac12 mv^2$（动能定理，$s=5$ 时 $W_合=40\\ \\mathrm{J}$）"},
        "bars": {"label": "功的分配（拉力输入 vs 克服摩擦损耗）",
                 "a": {"label": "拉力做功 $W_F$", "expr": "10*s"},
                 "b": {"label": "克服摩擦 $|W_f|$", "expr": "2*s"}},
        "legend": [
            {"color": "effort", "text": "拉力 F=10 N（做正功）"},
            {"color": "force", "text": "摩擦力 f=2 N（做负功，生热 Q=fs）"},
            {"color": "good", "text": "速度 v"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "动能定理：W合 = ΔEk",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>质量 $m=2\\ \\mathrm{kg}$ 的物块在水平拉力 $F=10\\ \\mathrm{N}$ 作用下"
                    "由静止开始运动，已知物块与地面间 $\\mu=0.1$（$g=10\\ \\mathrm{m/s^2}$）。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求物块前进 $s=5\\ \\mathrm{m}$ 时拉力做的功、克服摩擦做的功与合外力的功；</li>"
                    "<li>由动能定理求此时物块的速度；</li>"
                    "<li>拖动滑块改变 $s$，观察动能与各功分量的同步增长。</li></ol>"),
        "answerLabel": "W合 / 末速度 v",
        "answer": (f"$W_F = 50\\ \\mathrm{{J}}$，$W_f = -10\\ \\mathrm{{J}}$，"
                   f"$W_合 = {tex(sol['W_net'])}\\ \\mathrm{{J}}$，"
                   f"$v = {tex(sol['v'])}\\ \\mathrm{{m/s}} = 2\\sqrt{{10}} \\approx 6.32\\ \\mathrm{{m/s}}$"),
    }
    steps = [
        {"title": "求各力做的功",
         "content": ("<p>$f = \\mu mg = 0.1\\times2\\times10 = 2\\ \\mathrm{N}$。位移 $s=5\\ \\mathrm{m}$：</p>"
                     "<p class='text-center'>$$ W_F = Fs = 10\\times5 = 50\\ \\mathrm{J},\\qquad "
                     "W_f = -fs = -2\\times5 = -10\\ \\mathrm{J} $$</p>")},
        {"title": "求合外力的功",
         "content": ("<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ W_合 = W_F + W_f = 50-10 = 40\\ \\mathrm{J} $$</div>")},
        {"title": "动能定理求末速度",
         "content": (f"<p>由 $W_合 = \\Delta E_k = \\frac12mv^2 - 0$：</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ v = \\sqrt{{\\frac{{2W_合}}m}} = \\sqrt{{\\frac{{80}}2}} = "
                     f"{tex(sol['v'])}\\ \\mathrm{{m/s}} \\approx 6.32\\ \\mathrm{{m/s}} $$</div>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块改变 $s$：$W_F$、$|W_f|$、$W_合$、动能<b>同步线性增长</b>，"
                     "能量条显示输入功的 $\\frac15$ 被摩擦损耗（转化为内能 $Q=fs=|W_f|$）；"
                     "检验灯恒绿——<b>$\\frac12mv^2 = W_合$ 始终成立</b>。"
                     "动能定理不关心过程细节，只比较初末状态，是解恒力做功问题的捷径。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 圆周运动：向心力与绳模型临界速度
# =====================================================================
def build_circular() -> dict:
    sol = K.solve_circular(m=1, r=sp.Rational(2, 5), v=2)
    assert sol["F_c"] == 10 and sol["a_c"] == 10
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6.6]},
        "scene": {
            "kind": "circle", "caption": "竖直圆环（绳模型）：m=1kg，r=0.4m，最高点 v=2m/s",
            "r": 2.0, "m": 1, "g": 10, "clockwise": False,
            "theta": "theta*PI/180",
            "v": "sqrt(4+8*(1-cos(theta*PI/180)))",
            "F_c": "pow(sqrt(4+8*(1-cos(theta*PI/180))),2)/0.4",
            "vscale": 0.25, "fscale": 0.03,
        },
        "param": {"name": "theta", "label": "位置角 $\\theta$（0°=最高点）", "min": 0, "max": 360,
                  "step": 1, "value": 0, "unit": "°", "ticks": ["0° (最高点)", "180° (最低点)", "360°"]},
        "readouts": [
            {"id": "th", "label": "位置 $\\theta$", "type": "expr", "expr": "theta", "digits": 0, "unit": "°"},
            {"id": "v", "label": "速度 $v$", "type": "expr",
             "expr": "sqrt(4+8*(1-cos(theta*PI/180)))", "digits": 2, "unit": "m/s", "highlight": True},
            {"id": "Fc", "label": "向心力 $F_向=mv^2/r$", "type": "expr",
             "expr": "pow(sqrt(4+8*(1-cos(theta*PI/180))),2)/0.4", "digits": 1, "unit": "N"},
            {"id": "T", "label": "绳拉力 $T=\\frac{mv^2}{r}-mg\\cos\\theta$", "type": "expr",
             "expr": "pow(sqrt(4+8*(1-cos(theta*PI/180))),2)/0.4-10*cos(theta*PI/180)",
             "digits": 1, "unit": "N"},
            {"id": "st", "label": "绳模型检验", "type": "status",
             "expr": "sqrt(4+8*(1-cos(theta*PI/180)))", "op": ">", "rhs": 1.999,
             "okText": "v ≥ √(gr)=2 m/s：绳绷紧", "badText": "v < 2 m/s：绳松弛"},
        ],
        "constant": {"label": "$v_{\\mathrm{临}} = \\sqrt{gr} = \\sqrt{0.4\\times10} = 2\\ \\mathrm{m/s}$"
                              "（绳模型最高点临界速度，本题恰为临界）"},
        "legend": [
            {"color": "effort", "text": "速度 v（切向，由机械能守恒决定）"},
            {"color": "force", "text": "向心力 F向=mv²/r（指向圆心，由合力提供）"},
            {"color": "aux", "text": "重力 mg"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "竖直圆周运动：向心力与临界速度",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>长 $r=0.4\\ \\mathrm{m}$ 的轻绳一端固定，另一端系一质量 "
                    "$m=1\\ \\mathrm{kg}$ 的小球，小球在竖直平面内做圆周运动"
                    "（取 $g=10\\ \\mathrm{m/s^2}$）。若小球恰能通过最高点。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求小球通过最高点的最小速度（临界速度）；</li>"
                    "<li>在临界条件下，求小球经过最低点时的速度与绳的拉力；</li>"
                    "<li>拖动滑块改变位置角，观察速度与向心力的变化。</li></ol>"),
        "answerLabel": "临界速度 / 最低点速度 / 最低点拉力",
        "answer": (f"$v_{{\\mathrm{{临}}}} = \\sqrt{{gr}} = 2\\ \\mathrm{{m/s}}$；"
                   f"最低点 $v = \\sqrt{{v_{{\\mathrm{{临}}}}^2+4gr}} = "
                   f"{tex(sp.sqrt(20))}\\ \\mathrm{{m/s}} = 2\\sqrt5\\ \\approx 4.47\\ \\mathrm{{m/s}}$，"
                   f"$T = \\dfrac{{mv^2}}r + mg = 60\\ \\mathrm{{N}}$"),
    }
    steps = [
        {"title": "最高点临界条件",
         "content": ("<p>绳模型中，最高点绳拉力 $T\\ge0$。临界时 $T=0$，重力恰好完全提供向心力：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ mg = \\frac{mv_{\\mathrm{临}}^2}{r} \\Rightarrow "
                     "v_{\\mathrm{临}} = \\sqrt{gr} = \\sqrt{0.4\\times10} = 2\\ \\mathrm{m/s} $$</div>")},
        {"title": "机械能守恒求最低点速度",
         "content": ("<p>从最高点到最低点，下降高度 $2r$，由机械能守恒"
                     "（取最低点为零势能面）：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ \\frac12 mv_{\\mathrm{临}}^2 + mg\\cdot2r = \\frac12 mv^2 $$</div>"
                     f"<p class='text-center'>$$ v = \\sqrt{{v_{{\\mathrm{{临}}}}^2+4gr}} "
                     f"= \\sqrt{{4+16}} = {tex(sp.sqrt(20))} = 2\\sqrt5\\ \\mathrm{{m/s}} \\approx 4.47\\ \\mathrm{{m/s}} $$</p>")},
        {"title": "最低点受力分析",
         "content": ("<p>最低点：重力向下、拉力向上，合力提供向心力（向上）：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ T - mg = \\frac{mv^2}{r} \\Rightarrow T = \\frac{mv^2}{r}+mg "
                     "= \\frac{1\\times20}{0.4}+10 = 60\\ \\mathrm{N} $$</div>"
                     "<p>$T=6mg$ 是最高点重力的 6 倍——<b>最低点最难承重</b>，"
                     "这就是游乐场圆周轨道底部要加固的原因。</p>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块改变位置角 $\\theta$：速度从最高点 2 m/s 增至最低点 "
                     "$2\\sqrt5\\approx4.47\\ \\mathrm{m/s}$（重力势能转化为动能），"
                     "向心力 $F_向=mv^2/r$ 同步从 10 N 增至 50 N；绳拉力读数在最高点恰为 0 N"
                     "（临界，检验灯绿）。<b>最高点速度最小、最受\"考验\"；最低点速度最大、绳最吃力</b>。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 8) 匀变速直线运动：v-t 图像（斜率=加速度，面积=位移）
# =====================================================================
def build_kinematics() -> dict:
    sol = K.solve_kinematics(v0=2, a=2, t=3)
    assert sol["vt"] == 8 and sol["s"] == 15
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6.4]},
        "scene": {
            "kind": "vt", "caption": "匀加速直线运动 v-t 图（v₀=2m/s，a=2m/s²）",
            "tmax": 6, "vmin": 0, "vmax": 14, "t": "t",
            "vt_pts": [[0, 2], [6, 14]],
            "s_blk": "2*t+t*t",
        },
        "param": {"name": "t", "label": "时间 $t$", "min": 0, "max": 6, "step": 0.02,
                  "value": 3, "unit": " s", "ticks": ["0s", "3s (题设)", "6s"]},
        "readouts": [
            {"id": "t", "label": "时间 $t$", "type": "expr", "expr": "t", "digits": 2, "unit": "s"},
            {"id": "v", "label": "速度 $v=v_0+at$", "type": "expr", "expr": "2+2*t",
             "digits": 2, "unit": "m/s", "highlight": True},
            {"id": "s", "label": "位移 $s=v_0t+\\frac{at^2}{2}$", "type": "expr", "expr": "2*t+t*t",
             "digits": 2, "unit": "m"},
            {"id": "a", "label": "斜率 $=a$", "type": "expr", "expr": "2", "digits": 1, "unit": "m/s²"},
            {"id": "st", "label": "v²=v₀²+2as", "type": "status",
             "expr": "abs(pow(2+2*t,2)-(4+4*(2*t+t*t)))", "op": "<", "rhs": 0.01,
             "okText": "公式成立 ✓（面积=位移）", "badText": "—"},
        ],
        "constant": {"label": "$v$-$t$ 图<b>斜率</b> $=a\\equiv2\\ \\mathrm{m/s^2}$；"
                              "<b>阴影面积</b> $=$ 位移 $s$（$t=3$ 时 $s=15\\ \\mathrm{m}$）"},
        "legend": [
            {"color": "curve", "text": "v-t 图线（匀加速：倾斜直线）"},
            {"color": "good", "text": "阴影面积 = 位移"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "匀变速直线运动与 v-t 图像",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>一物体做匀加速直线运动，初速度 $v_0=2\\ \\mathrm{m/s}$，加速度 "
                    "$a=2\\ \\mathrm{m/s^2}$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求 $t=3\\ \\mathrm{s}$ 时物体的速度与这段时间内的位移；</li>"
                    "<li>拖动滑块读取任意时刻的速度与位移，"
                    "理解 v-t 图\"斜率=加速度、面积=位移\"的含义。</li></ol>"),
        "answerLabel": "速度 v / 位移 s",
        "answer": (f"$v = {tex(sol['vt'])}\\ \\mathrm{{m/s}}$，"
                   f"$s = {tex(sol['s'])}\\ \\mathrm{{m}}$"),
    }
    steps = [
        {"title": "求末速度",
         "content": ("<p>匀变速速度公式 $v = v_0+at$：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ v = 2+2\\times3 = 8\\ \\mathrm{m/s} $$</div>")},
        {"title": "求位移（公式法）",
         "content": ("<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ s = v_0t+\\frac{at^2}{2} = 2\\times3+\\frac{2\\times9}{2} = 15\\ \\mathrm{m} $$</div>")},
        {"title": "图像法：面积 = 位移",
         "content": ("<p>v-t 图中，图线与时间轴围成的<b>梯形面积</b>就是位移：</p>"
                     "<p class='text-center'>$$ s = \\frac{v_0+v}{2}\\cdot t = "
                     "\\frac{2+8}{2}\\times3 = 15\\ \\mathrm{m} $$</p>"
                     "<p>与公式法结果一致——<b>阴影面积 = 位移</b>。"
                     "图线的<b>斜率</b> $=\\frac{8-2}{3}=2\\ \\mathrm{m/s^2}=a$，恒定不变。</p>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：阴影梯形随之伸展，位移读数与面积同步增长；"
                     "检验灯验证 $v^2 = v_0^2+2as$ 恒成立（$t=3$ 时 $64=4+4\\times15$）。"
                     "<b>v-t 图三大用途：斜率读加速度、面积读位移、纵截距读初速度</b>。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
REGISTRY = {
    "belt": build_belt,
    "chase": build_chase,
    "incline": build_incline,
    "projectile": build_projectile,
    "newton2": build_newton2,
    "work_energy": build_work_energy,
    "circular": build_circular,
    "kinematics": build_kinematics,
}
SEEDS = list(REGISTRY)


def main(argv):
    # 统一入口（edulab/shared/skillkit.py）：
    #   python generate.py list | all <目录> | random [seed] [输出] | <key> [输出]
    return cli(
        REGISTRY, doc=__doc__, seeds=SEEDS,
        validate=required_sections("lesson", "steps", "board", min_steps=3),
        template_name="board.html", token=PLACEHOLDER,
        index="高中物理 · 必修一力学 · 交互课件", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
