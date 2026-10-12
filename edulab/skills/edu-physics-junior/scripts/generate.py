#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页初中物理交互网页。

数据由 lib/phys_kernel.py 的 sympy 精确计算驱动（单一数据源）：杠杆平衡、压强、
浮力、滑轮组、欧姆定律、串并联、电功率/焦耳定律全部精确算出；答案、分步数值、
画板读数同源一致。每个 build_* 内置自检断言。

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
import phys_kernel as K                  # noqa: E402
from phys_kernel import tex, f          # noqa: E402
from skillkit import cli, required_sections   # noqa: E402


# =====================================================================
# 1) 杠杆平衡条件 F1·L1 = F2·L2（撬棒）
# =====================================================================
def build_lever() -> dict:
    # 撬棒：阻力 G=600N（石块），阻力臂 L2=0.06m；F1=24N 恒定，滑块改动力臂 L1
    sol = K.solve_lever(F1=24, L2=sp.Rational(6, 100), F2=600)
    assert sol["L1"] == sp.Rational(3, 2) and sol["prod_left"] == sol["prod_right"] == 36
    board = {
        "view": {"xRange": [0, 9.2], "yRange": [0, 6.2]},
        "scene": {
            "kind": "lever", "caption": "撬棒撬起石块（示意图，力臂按比例放大）",
            "pivot": [4.6, 2.9], "beamLen": 7.6,
            "tilt": "min(max((F1*L1-F2*L2)*0.35, -10), 10)",
            "L1": "L1", "L2": "L2", "F1": "F1", "F2": "F2",
            "d1": "min(2.6, 0.9+L1*1.1)", "d2": 1.7,       # 绘图臂长（比例示意）
            "fs1": 0.045, "fs2": 0.0016,                    # 箭头标度 N→世界单位
        },
        "scalars": [{"name": "F1", "expr": "24"}, {"name": "F2", "expr": "600"},
                    {"name": "L2", "expr": "0.06"}],
        "param": {"name": "L1", "label": "动力臂 $L_1$",
                  "min": 0.3, "max": 3.0, "step": 0.01, "value": 1.5, "unit": " m",
                  "ticks": ["0.3m", "1.5m (题设)", "3.0m"]},
        "readouts": [
            {"id": "L1", "label": "动力臂 $L_1$", "type": "expr", "expr": "L1", "digits": 2, "unit": "m"},
            {"id": "prod1", "label": "$F_1L_1$", "type": "expr", "expr": "24*L1",
             "digits": 1, "unit": "N·m", "highlight": True},
            {"id": "prod2", "label": "$F_2L_2$", "type": "expr", "expr": "600*0.06",
             "digits": 1, "unit": "N·m"},
            {"id": "bal", "label": "杠杆状态", "type": "status", "expr": "abs(24*L1-36)", "op": "<", "rhs": 0.05,
             "okText": "平衡！F₁L₁ = F₂L₂", "badText": "失衡 → 将向重的一端转动"},
        ],
        "constant": {"label": "$F_2L_2 = 600\\times0.06 = 36\\ \\mathrm{N\\cdot m}$（阻力×阻力臂恒定）"},
        "legend": [
            {"color": "effort", "text": "动力 F₁（人施加）"},
            {"color": "force", "text": "阻力 F₂（石块重力 G）"},
            {"color": "metal", "text": "支点 O"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "杠杆平衡条件：撬棒撬石块",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>用撬棒撬起一块重 $G=600\\ \\mathrm{N}$ 的石块，阻力臂 $L_2=0.06\\ \\mathrm{m}$，"
                    "人施加的动力 $F_1=24\\ \\mathrm{N}$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求动力臂 $L_1$ 至少多大才能把石块撬起；</li>"
                    "<li>拖动滑块改变 $L_1$，观察 $F_1L_1$ 与 $F_2L_2$ 的关系与杠杆的倾斜方向。</li></ol>"),
        "answerLabel": "动力臂 L₁",
        "answer": f"$L_1 = {tex(sol['L1'])}\\ \\mathrm{{m}}$（即 1.5 m）",
    }
    steps = [
        {"title": "明确条件",
         "content": (f"<p>撬棒绕支点 O 转动，动力 $F_1=24\\ \\mathrm{{N}}$、动力臂 $L_1$（待求），"
                     f"阻力 $F_2=G=600\\ \\mathrm{{N}}$、阻力臂 $L_2={tex(sp.Rational(6,100))}\\ \\mathrm{{m}}$。</p>")},
        {"title": "列平衡方程",
         "content": ("<p>杠杆平衡条件（转动平衡）：</p>"
                     "<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     "$$ F_1L_1 = F_2L_2 $$</div>")},
        {"title": "代入求解",
         "content": (f"<p>$$ L_1 = \\frac{{F_2L_2}}{{F_1}} = "
                     f"\\frac{{600\\times 0.06}}{{24}} = {tex(sol['L1'])}\\ \\mathrm{{m}} $$</p>"
                     f"<p>即动力臂至少 $1.5\\ \\mathrm{{m}}$。</p>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：$F_1L_1$ 读数随 $L_1$ 变化，"
                     "$F_2L_2$ <b>恒为 36 N·m</b>（定值指示）。当 $L_1=1.5\\ \\mathrm{m}$ 时"
                     "两乘积相等、杠杆水平平衡（指示灯变绿）；$L_1<1.5$ 时右端下沉，"
                     "$L_1>1.5$ 时左端上翘。<b>动力臂越长越省力</b>——这正是撬棒做得长的原因。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 固体压强 p = F/S（砖块压海绵）
# =====================================================================
def build_pressure() -> dict:
    sol = K.solve_pressure(F=12, S=50, S_unit="cm2")
    assert sol["p"] == 2400 and sol["S"] == sp.Rational(1, 200)
    board = {
        "view": {"xRange": [0, 9.2], "yRange": [0, 5.2]},
        "scene": {
            "kind": "pressure", "caption": "砖块压海绵：压力作用效果与压强",
            "F": "F", "sink": "F/S*0.001*0.08", "k": 0.08,
            "boxW": 1.5, "boxH": 0.85, "boxLabel": "S = 50 cm²",
        },
        "scalars": [{"name": "S", "expr": "0.005"}],       # 50 cm² = 0.005 m²
        "param": {"name": "F", "label": "压力 $F$",
                  "min": 4, "max": 30, "step": 0.5, "value": 12, "unit": " N",
                  "ticks": ["4N", "12N (题设)", "30N"]},
        "readouts": [
            {"id": "F", "label": "压力 $F$", "type": "expr", "expr": "F", "digits": 1, "unit": "N"},
            {"id": "S", "label": "受力面积 $S$", "type": "expr", "expr": "S*10000", "digits": 0, "unit": "cm²"},
            {"id": "p", "label": "压强 $p=F/S$", "type": "expr", "expr": "F/S", "digits": 0, "unit": "Pa",
             "highlight": True},
            {"id": "eff", "label": "作用效果", "type": "status", "expr": "F/S", "op": ">", "rhs": 4000,
             "okText": "压强很大，海绵明显凹陷", "badText": "压强较小，凹陷较浅"},
        ],
        "constant": {"label": "$S = 50\\ \\mathrm{cm^2} = 5\\times10^{-3}\\ \\mathrm{m^2}$（受力面积恒定）"},
        "legend": [
            {"color": "obj", "text": "砖块（受压物体）"},
            {"color": "sponge", "text": "海绵（形变显示压力作用效果）"},
            {"color": "force", "text": "压力 F = G"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "固体压强 p = F/S",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>一块砖平放在海绵上，砖对海绵的压力 $F=12\\ \\mathrm{N}$，"
                    "受力面积 $S=50\\ \\mathrm{cm^2}$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求砖对海绵的压强；</li>"
                    "<li>拖动滑块增大压力，观察海绵凹陷深度与压强读数的关系。</li></ol>"),
        "answerLabel": "压强 p",
        "answer": f"$p = {tex(sol['p'])}\\ \\mathrm{{Pa}}$",
    }
    steps = [
        {"title": "统一单位",
         "content": ("<p>受力面积必须用平方米：</p>"
                     "<p class='text-center'>$$ S = 50\\ \\mathrm{cm^2} = 50\\times10^{-4}\\ \\mathrm{m^2} "
                     "= 5\\times10^{-3}\\ \\mathrm{m^2} $$</p>")},
        {"title": "代入公式",
         "content": (f"<p>$$ p = \\frac{{F}}{{S}} = \\frac{{12}}{{5\\times10^{{-3}}}} "
                     f"= {tex(sol['p'])}\\ \\mathrm{{Pa}} $$</p>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块增大压力：海绵凹陷加深、压强读数成正比增大——"
                     "<b>受力面积一定时，压强与压力成正比</b>。"
                     "想一想：把砖竖放（$S$ 减半）压强会怎样？这就是书包带做得宽、"
                     "图钉尖做得尖的道理。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 浮力：阿基米德原理 + 称重法
# =====================================================================
def build_buoyancy() -> dict:
    # 石块重 G=4N，V排 从 0 拖到 4×10⁻⁴ m³（全浸，F浮=G=4N 悬浮）；题设 V排=2×10⁻⁴
    V_FULL = sp.Rational(4, 10000)
    sol = K.solve_buoyancy(rho=1000, V=sp.Rational(2, 10000), G=4, F_scale=2)
    assert sol["F_buoy"] == 2 and sol["F_scale"] == 2
    full = K.solve_buoyancy(rho=1000, V=V_FULL, G=4, F_scale=0)
    assert full["F_buoy"] == 4 and full["F_scale"] == 0
    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 7]},
        "scene": {
            "kind": "buoyancy", "caption": "弹簧秤吊石块浸入水中（V排 由滑块控制）",
            "liquidY": 3.1, "objW": 1.15, "objH": 1.05,
            "objTop": "3.1 + 1.05*(1-V/0.0004)",
            "G": 4, "F_buoy": "1000*10*V", "F_scale": "4-1000*10*V", "fScale": 0.32,
        },
        "scalars": [{"name": "V", "expr": "v"}],
        "param": {"name": "v", "label": "排开水的体积 $V_排$",
                  "min": 0, "max": 0.0004, "step": 0.000005, "value": 0.0002, "unit": " m³",
                  "ticks": ["0（未浸入）", "2×10⁻⁴ (题设)", "4×10⁻⁴（全浸）"]},
        "readouts": [
            {"id": "V", "label": "$V_排$", "type": "expr", "expr": "V*10000", "digits": 1, "unit": "×10⁻⁴ m³"},
            {"id": "Fb", "label": "$F_浮=\\rho_水 gV_排$", "type": "expr", "expr": "1000*10*V",
             "digits": 2, "unit": "N", "highlight": True},
            {"id": "Fs", "label": "弹簧秤示数 $F_拉$", "type": "expr", "expr": "4-1000*10*V",
             "digits": 2, "unit": "N"},
            {"id": "st", "label": "状态", "type": "status", "expr": "abs(1000*10*V-4)", "op": "<", "rhs": 0.02,
             "okText": "F浮 = G：恰好悬浮（F拉=0）", "badText": "F浮 < G：弹簧秤还有示数"},
        ],
        "constant": {"label": "$F_浮 + F_拉 \\equiv G = 4\\ \\mathrm{N}$（重力被浮力与拉力分担）"},
        "legend": [
            {"color": "water2", "text": "浮力 F浮（竖直向上）"},
            {"color": "good", "text": "拉力 F拉（弹簧秤示数）"},
            {"color": "force", "text": "重力 G（竖直向下）"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "浮力的计算：称重法与阿基米德原理",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>弹簧测力计吊着一块重 $G=4\\ \\mathrm{N}$ 的石块，"
                    "把石块逐渐浸入水中（水的密度 $\\rho_水=1.0\\times10^3\\ \\mathrm{kg/m^3}$，"
                    "$g=10\\ \\mathrm{N/kg}$）。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>当 $V_排=2\\times10^{-4}\\ \\mathrm{m^3}$ 时，求石块受到的浮力与测力计示数；</li>"
                    "<li>拖动滑块改变浸入体积，验证 $F_浮+F_拉=G$ 是否恒成立。</li></ol>"),
        "answerLabel": "浮力 F浮 与 示数 F拉",
        "answer": f"$F_浮 = {tex(sol['F_buoy'])}\\ \\mathrm{{N}}$，$F_拉 = {tex(sol['F_scale'])}\\ \\mathrm{{N}}$",
    }
    steps = [
        {"title": "阿基米德原理求浮力",
         "content": (f"<p>$$ F_浮 = \\rho_水 g V_排 = 1.0\\times10^3 \\times 10 \\times "
                     f"2\\times10^{{-4}} = {tex(sol['F_buoy'])}\\ \\mathrm{{N}} $$</p>")},
        {"title": "称重法求拉力",
         "content": (f"<p>石块受三力平衡：$G = F_浮 + F_拉$，故</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ F_拉 = G - F_浮 = 4 - {tex(sol['F_buoy'])} = {tex(sol['F_scale'])}\\ \\mathrm{{N}} $$</div>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块增大 $V_排$：浮力读数线性增大、弹簧秤示数同步减小，"
                     "但两者之和<b>恒等于 4 N</b>（定值指示）。浸没后若继续下潜，"
                     "$V_排$ 不再变化、浮力保持不变——<b>浮力只与排开液体的体积有关，与深度无关</b>。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 滑轮组：F=(G物+G动)/n，η=W有/W总
# =====================================================================
def build_pulley() -> dict:
    sol = K.solve_pulley(G_obj=400, G_moving=100, n=2, h=1)
    assert sol["F"] == 250 and sol["eta"] == sp.Rational(4, 5)
    board = {
        "view": {"xRange": [0, 9.2], "yRange": [0, 6.4]},
        "scene": {
            "kind": "pulley", "caption": "一动一定滑轮组（n=2，绳重及摩擦不计）",
            "my": "2.0 + h*1.6", "myBase": 2.0, "handY": "3.4 - h*0.85",
            "n": 2, "G": 400, "F": "F", "fScale": 0.0033,
        },
        "scalars": [{"name": "h", "expr": "hv"}, {"name": "F", "expr": "(400+100)/2"}],
        "param": {"name": "hv", "label": "重物提升高度 $h$",
                  "min": 0, "max": 1.0, "step": 0.01, "value": 1.0, "unit": " m",
                  "ticks": ["0 m", "1 m (题设)"]},
        "readouts": [
            {"id": "h", "label": "提升高度 $h$", "type": "expr", "expr": "h", "digits": 2, "unit": "m"},
            {"id": "s", "label": "绳端移动 $s=nh$", "type": "expr", "expr": "2*h", "digits": 2, "unit": "m"},
            {"id": "F", "label": "拉力 $F=(G+G_动)/n$", "type": "expr", "expr": "F",
             "digits": 1, "unit": "N", "highlight": True},
            {"id": "Wu", "label": "有用功 $W_有=Gh$", "type": "expr", "expr": "400*h", "digits": 0, "unit": "J"},
            {"id": "Wt", "label": "总功 $W_总=Fs$", "type": "expr", "expr": "F*2*h", "digits": 0, "unit": "J"},
            {"id": "eta", "label": "机械效率 $\\eta$", "type": "expr", "expr": "400*h/(F*2*h)*100",
             "digits": 0, "unit": "%"},
        ],
        "constant": {"label": "$\\eta = \\dfrac{Gh}{Fs} = \\dfrac{400}{500} = 80\\%$（题设条件下恒定）"},
        "bars": {"label": "功的组成（有用功 / 额外功）",
                 "a": {"label": "有用功 W有 = Gh", "expr": "400*h"},
                 "b": {"label": "额外功 W额 = G动h", "expr": "100*h"}},
        "legend": [
            {"color": "effort", "text": "拉力 F（绳端）"},
            {"color": "force", "text": "物重 G = 400 N"},
            {"color": "rope", "text": "绳子（承担动滑轮的 2 段）"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "滑轮组的拉力与机械效率",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>用一动一定的滑轮组提升重物，物重 $G=400\\ \\mathrm{N}$，"
                    "动滑轮重 $G_动=100\\ \\mathrm{N}$，绳重及摩擦不计，承担物重的绳子段数 $n=2$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求拉力 $F$ 与重物升高 $h=1\\ \\mathrm{m}$ 时绳端移动的距离 $s$；</li>"
                    "<li>求滑轮组的机械效率 $\\eta$，并解释额外功的来源。</li></ol>"),
        "answerLabel": "拉力 F 与 机械效率 η",
        "answer": (f"$F = {tex(sol['F'])}\\ \\mathrm{{N}}$，$s = {tex(sol['s'])}\\ \\mathrm{{m}}$，"
                   f"$\\eta = {tex(sol['eta'])} = 80\\%$"),
    }
    steps = [
        {"title": "求拉力",
         "content": (f"<p>绳重及摩擦不计，$n=2$ 段绳子承担物重与动滑轮重：</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ F = \\frac{{G + G_动}}{{n}} = \\frac{{400+100}}{{2}} = {tex(sol['F'])}\\ \\mathrm{{N}} $$</div>")},
        {"title": "求绳端距离",
         "content": (f"<p>绳端移动距离是物体上升高度的 $n$ 倍：</p>"
                     f"<p class='text-center'>$$ s = nh = 2\\times1 = {tex(sol['s'])}\\ \\mathrm{{m}} $$</p>")},
        {"title": "求机械效率",
         "content": (f"<p>$W_有 = Gh = 400\\times1 = 400\\ \\mathrm{{J}}$，"
                     f"$W_总 = Fs = 250\\times2 = 500\\ \\mathrm{{J}}$（其中 $W_额 = G_动h = 100\\ \\mathrm{{J}}$）。</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ \\eta = \\frac{{W_有}}{{W_总}} = \\frac{{400}}{{500}} = {tex(sol['eta'])} = 80\\% $$</div>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块改变提升高度：$W_有$ 与 $W_总$ 同步增大，"
                     "但能量条的比例<b>保持 4:1 不变</b>、效率读数<b>恒为 80%</b>——"
                     "机械效率与提升高度无关。额外功用来提升动滑轮（100 J），"
                     "若计入摩擦与绳重，$\\eta$ 会更低。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 欧姆定律 I = U/R（单电阻电路）
# =====================================================================
def build_ohm_law() -> dict:
    sol = K.solve_ohm(U=6, R=10)
    assert sol["I"] == sp.Rational(3, 5)
    board = {
        "view": {"xRange": [0, 9.5], "yRange": [0, 6.2]},
        "scene": {
            "kind": "circuit", "layout": "single", "caption": "单电阻电路（U=6V 恒定，滑块改变 R）",
            "R1": "R", "R2": 0, "I": "6/R", "kflow": 2.0,
        },
        "scalars": [{"name": "R", "expr": "Rv"}],
        "param": {"name": "Rv", "label": "电阻 $R$",
                  "min": 4, "max": 24, "step": 0.5, "value": 10, "unit": " Ω",
                  "ticks": ["4Ω", "10Ω (题设)", "24Ω"]},
        "readouts": [
            {"id": "U", "label": "电压 $U$", "type": "expr", "expr": "6", "digits": 1, "unit": "V"},
            {"id": "R", "label": "电阻 $R$", "type": "expr", "expr": "R", "digits": 1, "unit": "Ω"},
            {"id": "I", "label": "电流 $I=U/R$", "type": "expr", "expr": "6/R",
             "digits": 3, "unit": "A", "highlight": True},
            {"id": "st", "label": "规律检验", "type": "status", "expr": "(6/R)*R", "op": "<", "rhs": 6.0001,
             "okText": "I·R ≡ U，符合欧姆定律", "badText": "—"},
        ],
        "constant": {"label": "$I \\\\cdot R \\\\equiv U = 6\\\\ \\\\mathrm{V}$（电压不变）"},
        "legend": [
            {"color": "battery", "text": "电阻 R（滑块改变）"},
            {"color": "current", "text": "电流方向（点的密集度 ∝ I）"},
            {"color": "meter", "text": "电流表 A / 电压表 V"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "欧姆定律 I = U/R",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>如图电路，电源电压 $U=6\\\\ \\\\mathrm{V}$ 恒定，电阻 $R=10\\\\ \\\\mathrm{\\\\Omega}$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求通过电阻的电流；</li>"
                    "<li>拖动滑块改变 $R$，观察电流读数与电流点流速的变化，验证 $I=U/R$。</li></ol>"),
        "answerLabel": "电流 I",
        "answer": f"$I = {tex(sol['I'])}\\\\ \\\\mathrm{{A}} = 0.6\\\\ \\\\mathrm{{A}}$",
    }
    steps = [
        {"title": "明确已知",
         "content": ("<p>$U=6\\\\ \\\\mathrm{V}$，$R=10\\\\ \\\\mathrm{\\\\Omega}$，求 $I$。</p>"
                     "<p>欧姆定律：<b>导体中的电流与导体两端的电压成正比，与导体的电阻成反比</b>。</p>")},
        {"title": "代入公式",
         "content": (f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ I = \\\\frac{{U}}{{R}} = \\\\frac{{6}}{{10}} = {tex(sol['I'])}\\\\ \\\\mathrm{{A}} $$</div>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块：$R$ 增大时电流读数减小、电流点变稀疏——"
                     "<b>电压一定时电流与电阻成反比</b>（$IR$ 乘积恒为 6，见定值指示）。"
                     "注意电压表测 $R$ 两端电压始终 6 V，电流表读数随 $R$ 变化。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) 串联电路：R总=R1+R2，U 按电阻分配
# =====================================================================
def build_series() -> dict:
    sol = K.solve_series(R1=5, R2=10, U=12)
    assert sol["U1"] == 4 and sol["U2"] == 8 and sol["U1"] + sol["U2"] == 12
    board = {
        "view": {"xRange": [0, 9.5], "yRange": [0, 6.2]},
        "scene": {
            "kind": "circuit", "layout": "series", "caption": "串联电路（U=12V，滑块改变 R₁）",
            "R1": "R1", "R2": "R2", "I": "12/(R1+R2)", "kflow": 1.6,
        },
        "scalars": [{"name": "R1", "expr": "R1v"}, {"name": "R2", "expr": "10"}],
        "param": {"name": "R1v", "label": "电阻 $R_1$",
                  "min": 2, "max": 18, "step": 0.5, "value": 5, "unit": " Ω",
                  "ticks": ["2Ω", "5Ω (题设)", "18Ω"]},
        "readouts": [
            {"id": "Rt", "label": "总电阻 $R_总=R_1+R_2$", "type": "expr", "expr": "R1+10",
             "digits": 1, "unit": "Ω"},
            {"id": "I", "label": "电流 $I=U/R_总$", "type": "expr", "expr": "12/(R1+10)",
             "digits": 3, "unit": "A", "highlight": True},
            {"id": "U1", "label": "$U_1=IR_1$", "type": "expr", "expr": "12*R1/(R1+10)",
             "digits": 2, "unit": "V"},
            {"id": "U2", "label": "$U_2=IR_2$", "type": "expr", "expr": "120/(R1+10)",
             "digits": 2, "unit": "V"},
            {"id": "st", "label": "分压规律", "type": "status", "expr": "abs(12*R1/(R1+10)+120/(R1+10)-12)",
             "op": "<", "rhs": 0.01,
             "okText": "U₁+U₂ ≡ U = 12V", "badText": "—"},
        ],
        "constant": {"label": "$U_1 + U_2 \\\\equiv U = 12\\\\ \\\\mathrm{V}$（串联分压，总电压不变）"},
        "legend": [
            {"color": "battery", "text": "R₁（滑块）、R₂=10Ω 串联"},
            {"color": "current", "text": "电流（处处相等）"},
            {"color": "meter", "text": "电压表测 R₁ 两端 / 电流表测干路"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "串联电路的分压规律",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>如图串联电路，电源电压 $U=12\\\\ \\\\mathrm{V}$，$R_1=5\\\\ \\\\mathrm{\\\\Omega}$，"
                    "$R_2=10\\\\ \\\\mathrm{\\\\Omega}$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求电路中的电流与 $R_1$、$R_2$ 两端的电压；</li>"
                    "<li>拖动滑块改变 $R_1$，观察 $U_1$、$U_2$ 如何重新分配（$U_1+U_2$ 是否仍为 12 V）。</li></ol>"),
        "answerLabel": "电流 I 与 分压 U₁/U₂",
        "answer": (f"$I = {tex(sol['I'])}\\\\ \\\\mathrm{{A}}$，"
                   f"$U_1 = {tex(sol['U1'])}\\\\ \\\\mathrm{{V}}$，$U_2 = {tex(sol['U2'])}\\\\ \\\\mathrm{{V}}$"),
    }
    steps = [
        {"title": "求总电阻",
         "content": ("<p>串联电路总电阻等于各电阻之和：</p>"
                     "<p class='text-center'>$$ R_总 = R_1 + R_2 = 5 + 10 = 15\\\\ \\\\mathrm{\\\\Omega} $$</p>")},
        {"title": "求电流与分压",
         "content": (f"<p>$$ I = \\\\frac{{U}}{{R_总}} = \\\\frac{{12}}{{15}} = {tex(sol['I'])}\\\\ \\\\mathrm{{A}} $$</p>"
                     f"<p>串联电流处处相等，故 $U_1 = IR_1 = {tex(sol['U1'])}\\\\ \\\\mathrm{{V}}$，"
                     f"$U_2 = IR_2 = {tex(sol['U2'])}\\\\ \\\\mathrm{{V}}$。</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ U_1 + U_2 = {tex(sol['U1'])} + {tex(sol['U2'])} = 12\\\\ \\\\mathrm{{V}} = U $$</div>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块增大 $R_1$：$U_1$ 增大、$U_2$ 减小，"
                     "<b>两者之和恒为 12 V</b>（定值指示）——<b>串联电路中电压与电阻成正比</b>（$U_1:U_2=R_1:R_2$）。"
                     "这就是分压原理：电阻越大，分得的电压越多。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 并联电路：I 按电阻反比分配
# =====================================================================
def build_parallel() -> dict:
    sol = K.solve_parallel(R1=6, R2=3, U=6)
    assert sol["I1"] == 1 and sol["I2"] == 2 and sol["I_total"] == 3
    board = {
        "view": {"xRange": [0, 9.5], "yRange": [0, 6.2]},
        "scene": {
            "kind": "circuit", "layout": "parallel", "caption": "并联电路（U=6V，滑块改变 L₁ 电阻）",
            "R1": "R1", "R2": "R2", "I1": "6/R1", "I2": "6/R2",
            "I": "6/R1+6/R2", "kflow": 2.0,
        },
        "scalars": [{"name": "R1", "expr": "R1v"}, {"name": "R2", "expr": "3"}],
        "param": {"name": "R1v", "label": "$L_1$ 的电阻 $R_1$",
                  "min": 2, "max": 12, "step": 0.5, "value": 6, "unit": " Ω",
                  "ticks": ["2Ω", "6Ω (题设)", "12Ω"]},
        "readouts": [
            {"id": "I1", "label": "支路 $I_1=U/R_1$", "type": "expr", "expr": "6/R1",
             "digits": 3, "unit": "A", "highlight": True},
            {"id": "I2", "label": "支路 $I_2=U/R_2$", "type": "expr", "expr": "6/3",
             "digits": 3, "unit": "A"},
            {"id": "It", "label": "干路 $I=I_1+I_2$", "type": "expr", "expr": "6/R1+6/3",
             "digits": 3, "unit": "A"},
            {"id": "st", "label": "并联规律", "type": "status", "expr": "abs((6/R1)/(6/3)-3/R1)",
             "op": "<", "rhs": 0.001,
             "okText": "I₁/I₂ = R₂/R₁（与电阻成反比）", "badText": "—"},
        ],
        "constant": {"label": "$I_2 \\\\equiv \\\\dfrac{U}{R_2} = \\\\dfrac{{6}}{{3}} = 2\\\\ \\\\mathrm{{A}}$（U、R₂ 不变则支路电流不变）"},
        "legend": [
            {"color": "battery", "text": "L₁（R₁ 滑块）与 L₂（R₂=3Ω）并联"},
            {"color": "current", "text": "电流（点的流速 ∝ 该支路电流）"},
            {"color": "meter", "text": "电流表测干路 I"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "并联电路的分流规律",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>如图并联电路，电源电压 $U=6\\\\ \\\\mathrm{V}$，灯 $L_1$ 的电阻 $R_1=6\\\\ \\\\mathrm{\\\\Omega}$，"
                    "灯 $L_2$ 的电阻 $R_2=3\\\\ \\\\mathrm{\\\\Omega}$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求通过两灯的电流与干路电流；</li>"
                    "<li>拖动滑块改变 $R_1$，观察两支路电流的分配（$I_1:I_2$ 与 $R_1:R_2$ 的关系）。</li></ol>"),
        "answerLabel": "电流 I₁ / I₂ / 干路 I",
        "answer": (f"$I_1 = {tex(sol['I1'])}\\\\ \\\\mathrm{{A}}$，$I_2 = {tex(sol['I2'])}\\\\ \\\\mathrm{{A}}$，"
                   f"$I = {tex(sol['I_total'])}\\\\ \\\\mathrm{{A}}$"),
    }
    steps = [
        {"title": "各支路电压相等",
         "content": ("<p>并联电路中，<b>各支路两端电压都等于电源电压</b>：</p>"
                     "<p class='text-center'>$$ U_1 = U_2 = U = 6\\\\ \\\\mathrm{V} $$</p>")},
        {"title": "分别求支路电流",
         "content": (f"<p>$$ I_1 = \\\\frac{{U}}{{R_1}} = \\\\frac{{6}}{{6}} = {tex(sol['I1'])}\\\\ \\\\mathrm{{A}},"
                     f"\\\\qquad I_2 = \\\\frac{{U}}{{R_2}} = \\\\frac{{6}}{{3}} = {tex(sol['I2'])}\\\\ \\\\mathrm{{A}} $$</p>")},
        {"title": "求干路电流",
         "content": (f"<p>并联干路电流等于各支路电流之和：</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ I = I_1 + I_2 = {tex(sol['I1'])} + {tex(sol['I2'])} = {tex(sol['I_total'])}\\\\ \\\\mathrm{{A}} $$</div>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块增大 $R_1$：$I_1$ 减小而 $I_2$ <b>保持 2 A 不变</b>（定值指示），"
                     "干路电流随之减小——<b>并联电路中各支路互不影响，电流与电阻成反比</b>"
                     "（$I_1:I_2=R_2:R_1$）。所以家庭电路中各用电器并联，开关互不干扰。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 8) 电功率与焦耳定律 P=UI，Q=I²Rt
# =====================================================================
def build_elec_power() -> dict:
    sol = K.solve_elec_power(U=6, R=10, t=100)
    assert sol["P"] == sp.Rational(18, 5) and sol["Q"] == 360
    board = {
        "view": {"xRange": [0, 9.5], "yRange": [0, 6.2]},
        "scene": {
            "kind": "circuit", "layout": "single",
            "caption": "电热器电路（U=6V、R=10Ω，滑块改变通电时间 t）",
            "R1": 10, "R2": 0, "I": "0.6", "kflow": 2.0,
        },
        "scalars": [{"name": "t", "expr": "tv"}],
        "param": {"name": "tv", "label": "通电时间 $t$",
                  "min": 20, "max": 240, "step": 5, "value": 100, "unit": " s",
                  "ticks": ["20s", "100s (题设)", "240s"]},
        "readouts": [
            {"id": "I", "label": "电流 $I=U/R$", "type": "expr", "expr": "6/10", "digits": 3, "unit": "A"},
            {"id": "P", "label": "电功率 $P=UI$", "type": "expr", "expr": "6*0.6",
             "digits": 2, "unit": "W", "highlight": True},
            {"id": "W", "label": "电功 $W=Pt$", "type": "expr", "expr": "6*0.6*t", "digits": 0, "unit": "J"},
            {"id": "Q", "label": "电热 $Q=I^2Rt$", "type": "expr", "expr": "0.6*0.6*10*t",
             "digits": 0, "unit": "J"},
            {"id": "st", "label": "纯电阻电路", "type": "status", "expr": "abs(0.6*0.6*10*t-6*0.6*t)",
             "op": "<", "rhs": 0.01,
             "okText": "Q ≡ W：电流做功全部转化为内能", "badText": "—"},
        ],
        "constant": {"label": "$P = UI = 6\\\\times0.6 = 3.6\\\\ \\\\mathrm{W}$（U、R 不变则功率恒定）"},
        "legend": [
            {"color": "battery", "text": "电热器 R=10Ω（纯电阻）"},
            {"color": "current", "text": "电流 I=0.6A（恒定）"},
            {"color": "meter", "text": "电流表 / 电压表"},
        ],
    }
    lesson = {
        "language": "zh-CN", "title": "电功率与焦耳定律",
        "problem": ("<p class='font-medium text-slate-800'>【题目】</p>"
                    "<p>一个电热器接在 $U=6\\\\ \\\\mathrm{V}$ 的电源上，电阻 $R=10\\\\ \\\\mathrm{\\\\Omega}$，"
                    "通电 $t=100\\\\ \\\\mathrm{s}$。</p>"
                    "<ol class='list-decimal pl-5 space-y-1'>"
                    "<li>求通过电热器的电流与它的电功率；</li>"
                    "<li>求 $100\\\\ \\\\mathrm{s}$ 内电流做的功与产生的热量，拖动滑块改变时间观察两者关系。</li></ol>"),
        "answerLabel": "电功率 P 与 电热 Q",
        "answer": (f"$P = {tex(sol['P'])}\\\\ \\\\mathrm{{W}} = 3.6\\\\ \\\\mathrm{{W}}$，"
                   f"$Q = {tex(sol['Q'])}\\\\ \\\\mathrm{{J}}$"),
    }
    steps = [
        {"title": "求电流",
         "content": ("<p>由欧姆定律：</p>"
                     "<p class='text-center'>$$ I = \\\\frac{{U}}{{R}} = \\\\frac{{6}}{{10}} = 0.6\\\\ \\\\mathrm{{A}} $$</p>")},
        {"title": "求电功率",
         "content": (f"<p>电功率表示电流做功的快慢：</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ P = UI = 6\\\\times0.6 = {tex(sol['P'])}\\\\ \\\\mathrm{{W}} = 3.6\\\\ \\\\mathrm{{W}} $$</div>"
                     f"<p>也可用 $P=I^2R = 0.6^2\\\\times10 = 3.6\\\\ \\\\mathrm{{W}}$ 或 $P=U^2/R$ 验算。</p>")},
        {"title": "求电功与电热",
         "content": (f"<p>$$ W = Pt = 3.6\\\\times100 = {tex(sol['W'])}\\\\ \\\\mathrm{{J}} $$</p>"
                     f"<p>电热器是<b>纯电阻</b>（电能全部转化为内能），由焦耳定律：</p>"
                     f"<div class='text-center py-3 bg-indigo-50 border border-indigo-100 rounded-xl text-indigo-900 font-bold'>"
                     f"$$ Q = I^2Rt = 0.6^2\\\\times10\\\\times100 = {tex(sol['Q'])}\\\\ \\\\mathrm{{J}} = W $$</div>")},
        {"title": "拖动验证",
         "content": ("<p>拖动滑块改变通电时间：$W$ 与 $Q$ 同步线性增大，"
                     "但<b>两者始终相等</b>（检验灯恒为绿）；而电功率 $P=3.6\\\\ \\\\mathrm{W}$ "
                     "<b>与时间无关</b>（定值指示）——功率描述\"快慢\"，电功描述\"总量\"。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
REGISTRY = {
    "lever": build_lever,
    "pressure": build_pressure,
    "buoyancy": build_buoyancy,
    "pulley": build_pulley,
    "ohm_law": build_ohm_law,
    "series": build_series,
    "parallel": build_parallel,
    "elec_power": build_elec_power,
}
SEEDS = ["lever", "pressure", "buoyancy", "pulley",
         "ohm_law", "series", "parallel", "elec_power"]


def main(argv):
    # 统一入口（edulab/shared/skillkit.py）：
    #   python generate.py list | all <目录> | random [seed] [输出] | <key> [输出]
    return cli(
        REGISTRY, doc=__doc__, seeds=SEEDS,
        validate=required_sections("lesson", "steps", "board", min_steps=3),
        template_name="board.html", token=PLACEHOLDER,
        index="初中物理 · 力学与电学 · 交互课件", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
