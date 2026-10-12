#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把反应 spec 经 reaction_kernel 计算后注入 template/reaction.html，产出单页交互网页。

数据由 lib/reaction_kernel.py 驱动（单一数据源）：配平、原子守恒、键的断/成、坐标与方程一致。
每个 build_* 返回一个“作者 spec”，assemble_data 负责校验与装配。

依赖 sympy。用能 import sympy 的解释器运行（本机：/opt/homebrew/bin/python3.11）：
    python3 scripts/generate.py <反应key> [输出.html]
    python3 scripts/generate.py list
    python3 scripts/generate.py all <输出目录>
"""

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PLACEHOLDER = "__REACTION_DATA__"

sys.path.insert(0, str(SKILL_DIR.parent.parent / "shared"))   # 共享运行时（edulab/shared/skillkit.py）
sys.path.insert(0, str(SKILL_DIR / "lib"))
import reaction_kernel as K          # noqa: E402
from skillkit import cli             # noqa: E402


def _p(html):
    return f"<p>{html}</p>"


# =====================================================================
# 1) 甲烷燃烧（初中·morph·火焰·放热）—— 旗舰范例
# =====================================================================
def build_combustion_ch4():
    return {
        "meta": {"title": "甲烷的燃烧", "subtitle": "CH₄ + O₂ 的氧化放热燃烧反应机理",
                 "language": "zh-CN", "category": "junior", "accent": "amber", "engine": "morph"},
        "conditions": {"text": "点燃", "exothermic": True, "flame": True},
        "reactants": [{"species": "CH4", "count": 1, "pos": [-4.0, 0.2, 0]},
                      {"species": "O2", "count": 2}],   # 两个 O2 实例（O2#1 给 CO2，O2#2 给水）
        "products": [{"species": "CO2", "count": 1, "pos": [-2.7, 1.1, 0]},
                     {"species": "H2O", "count": 2}],
        "atom_map": [
            ["CH4#1.C", "CO2#1.Y"],
            ["O2#1.Oa", "CO2#1.Xa"], ["O2#1.Ob", "CO2#1.Xb"],
            ["O2#2.Oa", "H2O#1.A"], ["O2#2.Ob", "H2O#2.A"],
            ["CH4#1.H1", "H2O#1.Ha"], ["CH4#1.H2", "H2O#1.Hb"],
            ["CH4#1.H3", "H2O#2.Ha"], ["CH4#1.H4", "H2O#2.Hb"],
        ],
        "energy": {"activation": 0.5, "deltaH": -0.75, "reactantLabel": "CH₄+O₂", "productLabel": "CO₂+H₂O"},
        "steps": [
            {"title": "反应物混合",
             "html": "<span class='text-slate-700 font-semibold'>甲烷 (CH₄)</span> 与 "
                     "<span class='text-red-600 font-semibold'>氧气 (O₂)</span> 分子混合靠近。"
                     "此时 C–H 键与 O=O 键都很稳定，常温下不自发反应，需<span class='text-amber-600 font-semibold'>点燃提供活化能</span>。"},
            {"title": "点燃燃烧",
             "html": "达到着火点后，<span class='border-b border-dashed border-amber-500'>C–H 键与 O=O 键剧烈断裂</span>，"
                     "原子被打散并重新组合。这是剧烈的<span class='text-amber-600 font-semibold'>氧化放热反应</span>，"
                     "瞬间释放大量热与光，即火焰。"},
            {"title": "生成产物",
             "html": "原子重组生成 <span class='text-slate-700 font-semibold'>二氧化碳 (CO₂)</span> 与 "
                     "<span class='text-blue-600 font-semibold'>水 (H₂O)</span>。"
                     "注意反应前后原子种类与数目守恒（1C、4H、4O），质量守恒。"},
        ],
    }


# =====================================================================
# 2) 氢气燃烧（初中·morph·火焰）
# =====================================================================
def build_combustion_h2():
    return {
        "meta": {"title": "氢气的燃烧", "subtitle": "2H₂ + O₂ 点燃生成水",
                 "language": "zh-CN", "category": "junior", "accent": "sky", "engine": "morph"},
        "conditions": {"text": "点燃", "exothermic": True, "flame": True},
        "reactants": [{"species": "H2", "count": 2}, {"species": "O2", "count": 1}],
        "products": [{"species": "H2O", "count": 2}],
        "atom_map": [
            ["O2#1.Oa", "H2O#1.A"], ["O2#1.Ob", "H2O#2.A"],
            ["H2#1.Ha", "H2O#1.Ha"], ["H2#1.Hb", "H2O#1.Hb"],
            ["H2#2.Ha", "H2O#2.Ha"], ["H2#2.Hb", "H2O#2.Hb"],
        ],
        "energy": {"activation": 0.45, "deltaH": -0.7, "reactantLabel": "H₂+O₂", "productLabel": "H₂O"},
        "steps": [
            {"title": "反应物混合",
             "html": "两个 <span class='text-sky-600 font-semibold'>氢分子 (H₂)</span> 与一个 "
                     "<span class='text-red-600 font-semibold'>氧分子 (O₂)</span> 靠近。"},
            {"title": "点燃反应",
             "html": "点燃后 <span class='border-b border-dashed border-sky-400'>H–H 键与 O=O 键断裂</span>，"
                     "原子重新组合，放出大量热（氢气是清洁燃料）。"},
            {"title": "生成水",
             "html": "每个氧原子结合两个氢原子，生成两分子 <span class='text-blue-600 font-semibold'>水 (H₂O)</span>。"
                     "原子守恒：4H、2O。"},
        ],
    }


# =====================================================================
# 3) 电解水（初中·morph·分解·吸热/通电）
# =====================================================================
def build_electrolysis_water():
    return {
        "meta": {"title": "电解水", "subtitle": "通电使水分解为氢气和氧气",
                 "language": "zh-CN", "category": "junior", "accent": "cyan", "engine": "morph"},
        "conditions": {"text": "通电", "under": "电解"},
        "reactants": [{"species": "H2O", "count": 2}],
        "products": [{"species": "H2", "count": 2}, {"species": "O2", "count": 1}],
        "atom_map": [
            ["H2O#1.A", "O2#1.Oa"], ["H2O#2.A", "O2#1.Ob"],
            ["H2O#1.Ha", "H2#1.Ha"], ["H2O#1.Hb", "H2#1.Hb"],
            ["H2O#2.Ha", "H2#2.Ha"], ["H2O#2.Hb", "H2#2.Hb"],
        ],
        "energy": {"activation": 0.35, "deltaH": 0.55, "reactantLabel": "H₂O", "productLabel": "H₂+O₂"},
        "steps": [
            {"title": "通电前",
             "html": "两个 <span class='text-cyan-700 font-semibold'>水分子 (H₂O)</span> 静置，"
                     "O–H 键稳定，需要<span class='text-cyan-700 font-semibold'>持续通入电能</span>才能分解。"},
            {"title": "通电分解",
             "html": "接通直流电，<span class='border-b border-dashed border-cyan-400'>O–H 键断裂</span>，"
                     "氢、氧原子分别向两极迁移并重新组合。这是<span class='text-cyan-700 font-semibold'>吸热</span>的分解反应。"},
            {"title": "生成气体",
             "html": "氢原子两两结合成 <span class='text-sky-600 font-semibold'>氢气 (H₂)</span>（负极），"
                     "氧原子结合成 <span class='text-red-600 font-semibold'>氧气 (O₂)</span>（正极），体积比约 2:1。原子守恒：4H、2O。"},
        ],
    }


# =====================================================================
# 4) 钠在氯气中燃烧（高中无机·morph·氧化还原·电子转移）
# =====================================================================
def build_redox_na_cl2():
    return {
        "meta": {"title": "钠与氯气", "subtitle": "2Na + Cl₂ —— 电子转移的氧化还原反应",
                 "language": "zh-CN", "category": "inorganic", "accent": "violet", "engine": "morph"},
        "conditions": {"text": "点燃", "exothermic": True, "transitionGlow": True},
        "reactants": [{"species": "Na", "count": 2}, {"species": "Cl2", "count": 1}],
        "products": [{"species": "NaCl", "count": 2}],
        "atom_map": [
            ["Na#1.X", "NaCl#1.Na"], ["Na#2.X", "NaCl#2.Na"],
            ["Cl2#1.Cla", "NaCl#1.Cl"], ["Cl2#1.Clb", "NaCl#2.Cl"],
        ],
        # 电子转移：每个 Na 失去 1 个电子给对应的 Cl（全局 id 由 atom_map 顺序决定）
        "electrons": [
            {"from": "Na1", "to": "Cl1", "count": 1, "label": "e⁻"},
            {"from": "Na2", "to": "Cl2", "count": 1, "label": "e⁻"},
        ],
        "energy": {"activation": 0.4, "deltaH": -0.8, "reactantLabel": "Na+Cl₂", "productLabel": "NaCl"},
        "steps": [
            {"title": "反应物",
             "html": "<span class='text-violet-600 font-semibold'>钠原子 (Na)</span> 最外层有 1 个电子，"
                     "<span class='text-green-700 font-semibold'>氯分子 (Cl₂)</span> 每个氯原子最外层有 7 个电子，都趋向 8 电子稳定结构。"},
            {"title": "电子转移",
             "html": "点燃后 <span class='border-b border-dashed border-green-400'>Cl–Cl 键断裂</span>，"
                     "每个钠原子把 1 个 <span class='text-cyan-700 font-semibold'>电子 (e⁻)</span> 转移给氯原子："
                     "钠被<span class='text-amber-600 font-semibold'>氧化</span>为 Na⁺，氯被<span class='text-sky-600 font-semibold'>还原</span>为 Cl⁻。"},
            {"title": "生成离子化合物",
             "html": "Na⁺ 与 Cl⁻ 靠静电作用（离子键）形成 <span class='text-violet-600 font-semibold'>氯化钠 (NaCl)</span>。"
                     "化合价：Na 0→+1、Cl 0→−1，得失电子守恒，原子守恒：2Na、2Cl。"},
        ],
    }


# =====================================================================
# 5) 酯化反应（高中有机·mechanism·催化剂·过渡态）—— 复刻 3d.html，但数据驱动
# =====================================================================
_EST_FRAGS = {
    "acetyl":    {"K0": {"pos": [-4.5, 0.5, 0], "rot": [0, 0, 0]},
                  "K1": {"pos": [-0.7, 0.1, 0], "rot": [0, 0, 0]},
                  "K2": {"pos": [-2.5, 1.2, 0], "rot": [0, 0, -0.1]}},
    "leavingOH": {"K0": {"pos": [-3.5, -0.1, 0.2], "rot": [0, 0, 0]},
                  "K1": {"pos": [0.5, -0.5, -0.3], "rot": [0, 0, -0.2]},
                  "K2": {"pos": [3.2, -1.5, -0.5], "rot": [0.2, 0.3, 0.5]}},
    "ethoxy":    {"K0": {"pos": [4.5, -0.5, 0], "rot": [0, 0, 0]},
                  "K1": {"pos": [0.6, 0.2, 0.15], "rot": [0, 0, 0]},
                  "K2": {"pos": [-1.38, 1.05, 0], "rot": [0, 0, 0]}},
    "leavingH":  {"K0": {"pos": [3.9, -1.1, 0], "rot": [0, 0, 0]},
                  "K1": {"pos": [1.1, -1.3, -0.3], "rot": [0, 0, 0]},
                  "K2": {"pos": [3.9, -2.0, -0.5], "rot": [0, 0, 0]}},
    "catalyst":  {"catalyst": True,
                  "K0": {"pos": [-4.5, 2.5, 0.5], "rot": [0, 0, 0]},
                  "K1": {"pos": [-0.5, -1.0, -0.3], "rot": [0, 0, 0]},
                  "K2": {"pos": [5.0, 1.0, 1.0], "rot": [0, 0, 0]}},
}
# id, el, frag, 片段内局部坐标（取自 3d.html）
_EST_ATOMS = [
    ("C1", "C", "acetyl", [0, 0.2, 0]), ("O1", "O", "acetyl", [0, 1.25, 0]),
    ("C2", "C", "acetyl", [-1.2, -0.5, 0]), ("H1", "H", "acetyl", [-1.2, -1.2, 0.8]),
    ("H2", "H", "acetyl", [-1.2, -1.2, -0.8]), ("H3", "H", "acetyl", [-2.0, -0.1, 0]),
    ("O2", "O", "leavingOH", [0, 0, 0]), ("H4", "H", "leavingOH", [0.7, -0.5, 0.1]),
    ("O3", "O", "ethoxy", [0, 0, 0]), ("C3", "C", "ethoxy", [1.1, 0.4, 0]),
    ("H5", "H", "ethoxy", [1.1, 1.0, 0.8]), ("H6", "H", "ethoxy", [1.1, 1.0, -0.8]),
    ("C4", "C", "ethoxy", [2.3, -0.3, 0]), ("H7", "H", "ethoxy", [2.3, -0.9, 0.8]),
    ("H8", "H", "ethoxy", [2.3, -0.9, -0.8]), ("H9", "H", "ethoxy", [3.0, 0.3, 0]),
    ("H10", "H", "leavingH", [0, 0, 0]),
    ("Hp", "H", "catalyst", [0, 0, 0]),
]
# 反应物态成键（乙酸 + 乙醇）
_EST_BEFORE = [
    ("C1", "O1", 2), ("C1", "C2", 1), ("C2", "H1", 1), ("C2", "H2", 1), ("C2", "H3", 1),
    ("C1", "O2", 1), ("O2", "H4", 1),
    ("O3", "C3", 1), ("C3", "H5", 1), ("C3", "H6", 1), ("C3", "C4", 1),
    ("C4", "H7", 1), ("C4", "H8", 1), ("C4", "H9", 1), ("O3", "H10", 1),
]
# 产物态成键（乙酸乙酯 + 水）
_EST_AFTER = [
    ("C1", "O1", 2), ("C1", "C2", 1), ("C2", "H1", 1), ("C2", "H2", 1), ("C2", "H3", 1),
    ("C1", "O3", 1), ("O3", "C3", 1), ("C3", "H5", 1), ("C3", "H6", 1), ("C3", "C4", 1),
    ("C4", "H7", 1), ("C4", "H8", 1), ("C4", "H9", 1),
    ("O2", "H4", 1), ("O2", "H10", 1),
]
_EST_RMOL = {"acetyl": "乙酸#1", "leavingOH": "乙酸#1", "ethoxy": "乙醇#1", "leavingH": "乙醇#1", "catalyst": "H+"}
_EST_PMOL = {"acetyl": "乙酸乙酯#1", "ethoxy": "乙酸乙酯#1", "leavingOH": "水#1", "leavingH": "水#1", "catalyst": "H+"}


def _fit(pos, s=0.7):
    """关键帧位置整体缩放，把酯化反应物/产物收进相机视野（半宽 ≈ 6）。"""
    return [round(pos[0] * s, 3), round(pos[1] * s, 3), pos[2]]


def build_esterification():
    atoms = []
    for aid, el, frag, flocal in _EST_ATOMS:
        f = _EST_FRAGS[frag]
        atoms.append({
            "id": aid, "el": el, "frag": frag, "flocal": flocal,
            "start": K._apply(flocal, _fit(f["K0"]["pos"]), f["K0"]["rot"]),
            "end": K._apply(flocal, _fit(f["K2"]["pos"]), f["K2"]["rot"]),
            "rmol": _EST_RMOL[frag], "pmol": _EST_PMOL[frag],
        })
    fragments = [dict(v, id=k) for k, v in _EST_FRAGS.items()]
    # 浮动标签（显式提供）
    acetyl_eth = ["C1", "O1", "C2", "H1", "H2", "H3", "O3", "C3", "H5", "H6", "C4", "H7", "H8", "H9"]
    labels = [
        {"id": "r-acid", "text": "乙酸 (CH₃COOH)", "color": "red", "phase": "reactant",
         "atoms": ["C1", "O1", "C2", "H1", "H2", "H3", "O2", "H4"]},
        {"id": "r-ethanol", "text": "乙醇 (C₂H₅OH)", "color": "blue", "phase": "reactant",
         "atoms": ["O3", "C3", "H5", "H6", "C4", "H7", "H8", "H9", "H10"]},
        {"id": "p-ester", "text": "乙酸乙酯 (CH₃COOC₂H₅)", "color": "emerald", "phase": "product",
         "atoms": acetyl_eth},
        {"id": "p-water", "text": "水 (H₂O)", "color": "cyan", "phase": "product",
         "atoms": ["O2", "H4", "H10"]},
    ]
    return {
        "meta": {"title": "酯化反应", "subtitle": "乙酸 + 乙醇 的费歇尔酯化反应机理",
                 "language": "zh-CN", "category": "organic", "accent": "indigo", "engine": "mechanism",
                 "equation": r"\text{CH}_3\text{COOH} + \text{C}_2\text{H}_5\text{OH} "
                             r"\underset{\Delta}{\overset{\text{浓硫酸}}{\rightleftharpoons}} "
                             r"\text{CH}_3\text{COOC}_2\text{H}_5 + \text{H}_2\text{O}"},
        "conditions": {"text": "催化、加热", "reversible": True, "transitionGlow": True,
                       "catalyst": {"label": "浓硫酸催化剂 (H⁺)", "formula": "H^+"}},
        "reactants": [{"species": "乙酸"}, {"species": "乙醇"}],
        "products": [{"species": "乙酸乙酯"}, {"species": "水"}],
        "atoms": atoms,
        "bonds_before": [{"a": a, "b": b, "order": o} for a, b, o in _EST_BEFORE],
        "bonds_after": [{"a": a, "b": b, "order": o} for a, b, o in _EST_AFTER],
        "fragments": fragments,
        "labels": labels,
        "energy": {"activation": 0.62, "deltaH": -0.12, "reactantLabel": "酸+醇", "productLabel": "酯+水"},
        "steps": [
            {"title": "反应物准备",
             "html": "<span class='text-red-600 font-semibold'>乙酸 (CH₃COOH)</span> 与 "
                     "<span class='text-blue-600 font-semibold'>乙醇 (C₂H₅OH)</span> 在浓硫酸催化下靠近。"
                     "游离 <span class='text-cyan-700 font-semibold'>质子 (H⁺)</span> 先质子化羰基氧，使羰基碳更易被进攻。"},
            {"title": "碰撞与过渡态",
             "html": "乙醇羟基氧进攻羰基碳，临界瞬间虚线键同时断生："
                     "<span class='border-b border-dashed border-amber-500'>酸 C–OH 键、醇 O–H 键断裂</span>，"
                     "<span class='border-b border-dashed border-emerald-500'>新 C–O 酯键与 H₂O 形成</span>。能量最高的过渡态。"},
            {"title": "产物生成与分离",
             "html": "脱去一分子 <span class='text-cyan-700 font-semibold'>水 (H₂O)</span>，"
                     "生成有香味的 <span class='text-emerald-600 font-semibold'>乙酸乙酯 (CH₃COOC₂H₅)</span>。"
                     "<span class='text-indigo-600 font-semibold'>催化剂 H⁺</span> 再生，实现“酸脱羟基醇脱氢”。"},
        ],
    }


# =====================================================================
# 6) 葡萄糖有氧氧化（细胞呼吸·morph·36原子·暗色·火焰·放热）—— 最复杂示例
# =====================================================================
def build_glucose_combustion():
    return {
        "meta": {
            "title": "葡萄糖的有氧氧化",
            "subtitle": "C₆H₁₂O₆ + 6O₂ → 6CO₂ + 6H₂O（细胞呼吸核心反应）",
            "language": "zh-CN",
            "category": "inorganic",
            "accent": "amber",
            "engine": "morph",
        },
        "conditions": {"text": "酶催化", "exothermic": True, "flame": True},
        "reactants": [{"species": "Glucose", "count": 1, "pos": [-3.6, 0.2, 0]}] +
                     _placed("O2", [(-1.2, 1.5, 0), (0.4, 1.5, 0), (2.0, 1.5, 0),
                                    (-1.2, -1.4, 0), (0.4, -1.4, 0), (2.0, -1.4, 0)]),
        "products": _placed("CO2", [(-4.6, 1.8, 0), (-2.8, 1.8, 0), (-1.0, 1.8, 0),
                                    (-4.6, -0.2, 0), (-2.8, -0.2, 0), (-1.0, -0.2, 0)]) +
                    _placed("H2O", [(1.0, 1.7, 0), (2.6, 1.7, 0), (4.2, 1.7, 0),
                                    (1.0, -1.7, 0), (2.6, -1.7, 0), (4.2, -1.7, 0)]),
        "atom_map": [
            # 6 个碳原子 → 6 个 CO₂ 的中心碳
            ["Glucose#1.C1", "CO2#1.Y"], ["Glucose#1.C2", "CO2#2.Y"],
            ["Glucose#1.C3", "CO2#3.Y"], ["Glucose#1.C4", "CO2#4.Y"],
            ["Glucose#1.C5", "CO2#5.Y"], ["Glucose#1.C6", "CO2#6.Y"],
            # 葡萄糖 6 个 O → 6 个 H₂O 的氧
            ["Glucose#1.O1", "H2O#1.A"], ["Glucose#1.O2", "H2O#2.A"],
            ["Glucose#1.O3", "H2O#3.A"], ["Glucose#1.O4", "H2O#4.A"],
            ["Glucose#1.O5", "H2O#5.A"], ["Glucose#1.O6", "H2O#6.A"],
            # 葡萄糖 12 个 H → 6 个 H₂O 各 2 个 H
            ["Glucose#1.H1",  "H2O#1.Ha"], ["Glucose#1.HO2", "H2O#1.Hb"],
            ["Glucose#1.H2",  "H2O#2.Ha"], ["Glucose#1.HO3", "H2O#2.Hb"],
            ["Glucose#1.H3",  "H2O#3.Ha"], ["Glucose#1.HO4", "H2O#3.Hb"],
            ["Glucose#1.H4",  "H2O#4.Ha"], ["Glucose#1.HO5", "H2O#4.Hb"],
            ["Glucose#1.H5",  "H2O#5.Ha"], ["Glucose#1.HO6", "H2O#5.Hb"],
            ["Glucose#1.H6a", "H2O#6.Ha"], ["Glucose#1.H6b", "H2O#6.Hb"],
            # 6 个 O₂（12 个 O）→ 6 个 CO₂ 的两端氧
            ["O2#1.Oa", "CO2#1.Xa"], ["O2#1.Ob", "CO2#1.Xb"],
            ["O2#2.Oa", "CO2#2.Xa"], ["O2#2.Ob", "CO2#2.Xb"],
            ["O2#3.Oa", "CO2#3.Xa"], ["O2#3.Ob", "CO2#3.Xb"],
            ["O2#4.Oa", "CO2#4.Xa"], ["O2#4.Ob", "CO2#4.Xb"],
            ["O2#5.Oa", "CO2#5.Xa"], ["O2#5.Ob", "CO2#5.Xb"],
            ["O2#6.Oa", "CO2#6.Xa"], ["O2#6.Ob", "CO2#6.Xb"],
        ],
        "energy": {
            "activation": 0.25,
            "deltaH": -0.95,
            "reactantLabel": "C₆H₁₂O₆+O₂",
            "productLabel": "CO₂+H₂O",
        },
        "steps": [
            {
                "title": "反应物：葡萄糖与 6 个氧分子",
                "html": (
                    "<span class='text-amber-700 font-semibold'>葡萄糖 (C₆H₁₂O₆)</span> 是 6 碳醛糖，"
                    "含 1 个醛基（C₁=O）、5 个羟基（C–OH）和 5 根 C–C 骨架键，共 24 个原子。"
                    "<span class='text-red-600 font-semibold'>6 个 O₂</span> 提供 12 个氧原子。"
                    "这是生命<span class='text-amber-600'>细胞呼吸</span>的核心放热反应，释放 △G ≈ −2803 kJ/mol。"
                ),
            },
            {
                "title": "碳骨架逐步断裂·键全面重组",
                "html": (
                    "在细胞酶系（糖酵解→丙酮酸脱氢→三羧酸循环）的催化下，"
                    "C–C 链与 C–H 键<span class='border-b border-dashed border-red-400'>逐步断裂</span>，"
                    "O=O 键同步裂开；碳原子逐一氧化。共断裂 <span class='text-red-600 font-semibold'>17+ 根旧键</span>，"
                    "同时形成 <span class='text-green-700 font-semibold'>18 根新键</span>（12 根 C=O 和 12 根 O–H）。"
                ),
            },
            {
                "title": "生成 6CO₂ + 6H₂O · 原子守恒",
                "html": (
                    "6 个碳原子各与 2 个来自 O₂ 的氧原子结合，生成"
                    "<span class='text-slate-700 font-semibold'> 6 分子 CO₂</span>（线形，两个 C=O）；"
                    "12 个氢原子与葡萄糖内的 6 个氧原子结合，生成"
                    "<span class='text-cyan-700 font-semibold'> 6 分子 H₂O</span>（弯曲形）。"
                    "原子守恒：反应前后各 6C · 12H · 18O，质量守恒。"
                ),
            },
        ],
    }


# =====================================================================
# 板块⑥ 初中化学补全：酸碱盐 / 金属活动性 / 溶液
# =====================================================================
# 7) 中和反应（初中·复分解·放热）—— 酸碱盐
def build_neutralization_naoh_hcl():
    return {
        "meta": {"title": "中和反应：NaOH + HCl", "subtitle": "酸与碱生成盐和水的复分解反应",
                 "language": "zh-CN", "category": "junior", "accent": "rose", "engine": "morph"},
        "conditions": {"text": "常温混合", "exothermic": True},
        "reactants": [{"species": "NaOH", "count": 1, "pos": [-3.4, 0.3, 0]},
                      {"species": "HCl", "count": 1, "pos": [3.2, -0.2, 0]}],
        "products": [{"species": "NaCl", "count": 1, "pos": [-2.6, 0.4, 0]},
                     {"species": "H2O", "count": 1, "pos": [2.4, -0.4, 0]}],
        "atom_map": [
            ["NaOH#1.Na", "NaCl#1.Na"], ["HCl#1.Cl", "NaCl#1.Cl"],
            ["NaOH#1.O1", "H2O#1.A"], ["NaOH#1.H1", "H2O#1.Ha"], ["HCl#1.H", "H2O#1.Hb"],
        ],
        "energy": {"activation": 0.22, "deltaH": -0.45,
                   "reactantLabel": "NaOH+HCl", "productLabel": "NaCl+H₂O"},
        "steps": [
            {"title": "酸与碱靠近",
             "html": "<span class='text-rose-600 font-semibold'>氢氧化钠 (NaOH)</span> 电离出 Na⁺ 与 OH⁻，"
                     "<span class='text-sky-600 font-semibold'>盐酸 (HCl)</span> 电离出 H⁺ 与 Cl⁻。"},
            {"title": "H⁺ 遇 OH⁻",
             "html": "两种离子相互吸引：<span class='border-b border-dashed border-rose-500'>Na–OH 键与 H–Cl 键断裂</span>，"
                     "H⁺ + OH⁻ 结合成水，同时放热（中和热约 57.3 kJ/mol）。"},
            {"title": "生成盐和水",
             "html": "生成 <span class='text-violet-600 font-semibold'>氯化钠 (NaCl)</span> 与 "
                     "<span class='text-sky-600 font-semibold'>水 (H₂O)</span>。"
                     "这就是复分解反应的通式之一：酸 + 碱 → 盐 + 水。原子守恒：Na、O、H、Cl 各 1 个。"},
        ],
    }


# 8) 酸与碳酸盐（初中·复分解·生成气体）—— 实验室制 CO₂
def build_acid_carbonate_caco3():
    return {
        "meta": {"title": "实验室制取二氧化碳", "subtitle": "CaCO₃ + 2HCl → CaCl₂ + H₂O + CO₂↑",
                 "language": "zh-CN", "category": "junior", "accent": "sky", "engine": "morph"},
        "conditions": {"text": "常温", "exothermic": True},
        "reactants": [{"species": "CaCO3", "count": 1, "pos": [-3.6, 0.2, 0]},
                      {"species": "HCl", "count": 2}],
        "products": [{"species": "CaCl2", "count": 1, "pos": [-3.0, 0.3, 0]},
                     {"species": "H2O", "count": 1},
                     {"species": "CO2", "count": 1}],
        "atom_map": [
            ["CaCO3#1.Ca", "CaCl2#1.Ca"],
            ["HCl#1.Cl", "CaCl2#1.X1"], ["HCl#2.Cl", "CaCl2#1.X2"],
            ["CaCO3#1.O3", "H2O#1.A"], ["HCl#1.H", "H2O#1.Ha"], ["HCl#2.H", "H2O#1.Hb"],
            ["CaCO3#1.A", "CO2#1.Y"],
            ["CaCO3#1.O1", "CO2#1.Xa"], ["CaCO3#1.O2", "CO2#1.Xb"],
        ],
        "energy": {"activation": 0.25, "deltaH": -0.35,
                   "reactantLabel": "CaCO₃+HCl", "productLabel": "CaCl₂+CO₂+H₂O"},
        "steps": [
            {"title": "大理石遇酸",
             "html": "<span class='text-slate-600 font-semibold'>碳酸钙 (CaCO₃)</span> 是大理石、石灰石的主要成分，"
                     "与 <span class='text-sky-600 font-semibold'>稀盐酸 (HCl)</span> 接触。"},
            {"title": "碳酸根被拆开",
             "html": "H⁺ 进攻 CO₃²⁻：<span class='border-b border-dashed border-rose-500'>Ca–O 离子键与 H–Cl 键断裂</span>，"
                     "先生成不稳定的 H₂CO₃，随即分解。"},
            {"title": "放出 CO₂ 气体",
             "html": "生成 <span class='text-slate-600 font-semibold'>氯化钙 (CaCl₂)</span>、"
                     "<span class='text-sky-600 font-semibold'>水</span> 与 "
                     "<span class='text-emerald-600 font-semibold'>二氧化碳 (CO₂↑)</span>，"
                     "有气泡产生——这就是复分解反应发生的条件之一：生成气体。"},
        ],
    }


# 9) 碱与盐的复分解（初中·生成沉淀）—— CuSO₄ + 2NaOH
def build_alkali_salt_precipitate():
    return {
        "meta": {"title": "生成蓝色沉淀的复分解", "subtitle": "CuSO₄ + 2NaOH → Cu(OH)₂↓ + Na₂SO₄",
                 "language": "zh-CN", "category": "junior", "accent": "cyan", "engine": "morph"},
        "conditions": {"text": "常温混合", "exothermic": False},
        "reactants": [{"species": "CuSO4", "count": 1, "pos": [-3.6, 0.2, 0]},
                      {"species": "NaOH", "count": 2}],
        "products": [{"species": "CuOH2", "count": 1, "pos": [-2.6, 0.3, 0]},
                     {"species": "Na2SO4", "count": 1, "pos": [2.6, -0.2, 0]}],
        "atom_map": [
            ["CuSO4#1.Cu", "CuOH2#1.Cu"],
            ["NaOH#1.O1", "CuOH2#1.O1"], ["NaOH#1.H1", "CuOH2#1.H1"],
            ["NaOH#2.O1", "CuOH2#1.O2"], ["NaOH#2.H1", "CuOH2#1.H2"],
            ["NaOH#1.Na", "Na2SO4#1.Na1"], ["NaOH#2.Na", "Na2SO4#1.Na2"],
            ["CuSO4#1.A", "Na2SO4#1.A"],
            ["CuSO4#1.O1", "Na2SO4#1.O1"], ["CuSO4#1.O2", "Na2SO4#1.O2"],
            ["CuSO4#1.O3", "Na2SO4#1.O3"], ["CuSO4#1.O4", "Na2SO4#1.O4"],
        ],
        "energy": {"activation": 0.20, "deltaH": -0.30,
                   "reactantLabel": "CuSO₄+NaOH", "productLabel": "Cu(OH)₂+Na₂SO₄"},
        "steps": [
            {"title": "两种溶液混合",
             "html": "<span class='text-sky-600 font-semibold'>硫酸铜溶液 (CuSO₄)</span> 呈蓝色，"
                     "与 <span class='text-rose-600 font-semibold'>氢氧化钠溶液 (NaOH)</span> 混合，离子自由移动。"},
            {"title": "离子交换成分",
             "html": "Cu²⁺ 与 OH⁻ 相互吸引：<span class='border-b border-dashed border-rose-500'>Cu–O、Na–O 离子键重组</span>，"
                     "复分解反应发生的条件之一是生成沉淀。"},
            {"title": "蓝色沉淀析出",
             "html": "生成难溶的 <span class='text-cyan-700 font-semibold'>氢氧化铜 Cu(OH)₂↓</span>（蓝色絮状沉淀）"
                     "与 <span class='text-violet-600 font-semibold'>硫酸钠 (Na₂SO₄)</span>。"
                     "沉淀符号 ↓ 表示生成物从溶液中析出。"},
        ],
    }


# 10) 酸与金属氧化物（初中·除锈原理）—— Fe₂O₃ + 6HCl
def build_acid_metal_oxide():
    return {
        "meta": {"title": "酸除锈原理", "subtitle": "Fe₂O₃ + 6HCl → 2FeCl₃ + 3H₂O",
                 "language": "zh-CN", "category": "junior", "accent": "orange", "engine": "morph"},
        "conditions": {"text": "常温", "exothermic": True},
        "reactants": [{"species": "Fe2O3", "count": 1, "pos": [-4.2, 0.3, 0]}] +
                     _placed("HCl", [(-1.4, 1.3, 0), (0.4, 1.3, 0), (2.2, 1.3, 0),
                                     (-1.4, -1.3, 0), (0.4, -1.3, 0), (2.2, -1.3, 0)]),
        "products": _placed("FeCl3", [(-3.6, 1.5, 0), (-3.6, -1.5, 0)]) +
                    _placed("H2O", [(0.8, 1.5, 0), (2.4, 0.2, 0), (0.8, -1.4, 0)]),
        "atom_map": [
            ["Fe2O3#1.Fe1", "FeCl3#1.Fe"], ["Fe2O3#1.Fe2", "FeCl3#2.Fe"],
            ["HCl#1.Cl", "FeCl3#1.X1"], ["HCl#2.Cl", "FeCl3#1.X2"], ["HCl#3.Cl", "FeCl3#1.X3"],
            ["HCl#4.Cl", "FeCl3#2.X1"], ["HCl#5.Cl", "FeCl3#2.X2"], ["HCl#6.Cl", "FeCl3#2.X3"],
            ["Fe2O3#1.O1", "H2O#1.A"], ["Fe2O3#1.O2", "H2O#2.A"], ["Fe2O3#1.O3", "H2O#3.A"],
            ["HCl#1.H", "H2O#1.Ha"], ["HCl#2.H", "H2O#1.Hb"],
            ["HCl#3.H", "H2O#2.Ha"], ["HCl#4.H", "H2O#2.Hb"],
            ["HCl#5.H", "H2O#3.Ha"], ["HCl#6.H", "H2O#3.Hb"],
        ],
        "energy": {"activation": 0.24, "deltaH": -0.40,
                   "reactantLabel": "Fe₂O₃+HCl", "productLabel": "FeCl₃+H₂O"},
        "steps": [
            {"title": "铁锈遇到盐酸",
             "html": "<span class='text-orange-600 font-semibold'>氧化铁 (Fe₂O₃)</span> 是铁锈的主要成分，"
                     "与 <span class='text-sky-600 font-semibold'>稀盐酸 (HCl)</span> 接触，6 个 HCl 分子包围它。"},
            {"title": "金属氧化物被拆开",
             "html": "<span class='border-b border-dashed border-rose-500'>Fe–O 离子键与 H–Cl 键断裂</span>，"
                     "酸能与金属氧化物反应——这是酸的第五条化学性质。"},
            {"title": "除锈完成",
             "html": "生成 <span class='text-orange-600 font-semibold'>氯化铁 (FeCl₃)</span>（黄色溶液）"
                     "和 <span class='text-sky-600 font-semibold'>水</span>。"
                     "因此盐酸可用于清除金属表面的锈。原子守恒：Fe₂、O₃、H₆、Cl₆。"},
        ],
    }


# 11) 金属与酸（初中·置换·金属活动性）—— Zn + H₂SO₄
def build_metal_acid_zn():
    return {
        "meta": {"title": "锌与稀硫酸", "subtitle": "Zn + H₂SO₄ → ZnSO₄ + H₂↑（置换反应）",
                 "language": "zh-CN", "category": "junior", "accent": "emerald", "engine": "morph"},
        "conditions": {"text": "常温", "exothermic": True},
        "reactants": [{"species": "Zn", "count": 1, "pos": [-3.2, 0.3, 0]},
                      {"species": "H2SO4", "count": 1, "pos": [3.0, -0.2, 0]}],
        "products": [{"species": "ZnSO4", "count": 1, "pos": [-2.6, 0.3, 0]},
                     {"species": "H2", "count": 1, "pos": [2.8, -0.5, 0]}],
        "atom_map": [
            ["Zn#1.X", "ZnSO4#1.Zn"],
            ["H2SO4#1.A", "ZnSO4#1.A"],
            ["H2SO4#1.O1", "ZnSO4#1.O1"], ["H2SO4#1.O2", "ZnSO4#1.O2"],
            ["H2SO4#1.O3", "ZnSO4#1.O3"], ["H2SO4#1.O4", "ZnSO4#1.O4"],
            ["H2SO4#1.H1", "H2#1.Ha"], ["H2SO4#1.H2", "H2#1.Hb"],
        ],
        "activity": K.activity_strip("Zn", "H"),
        "energy": {"activation": 0.28, "deltaH": -0.42,
                   "reactantLabel": "Zn+H₂SO₄", "productLabel": "ZnSO₄+H₂"},
        "steps": [
            {"title": "锌投入稀硫酸",
             "html": "<span class='text-slate-600 font-semibold'>锌粒 (Zn)</span> 投入 "
                     "<span class='text-sky-600 font-semibold'>稀硫酸 (H₂SO₄)</span> 中。"
                     "锌在金属活动性顺序表中排在 <span class='font-bold'>(H)</span> 之前。"},
            {"title": "置换出氢",
             "html": "<span class='border-b border-dashed border-rose-500'>Zn–S 离子键、O–H 键重组</span>："
                     "Zn 失去 2 个电子变成 Zn²⁺，H⁺ 得电子被还原成 H 原子。"
                     "一种单质 + 一种化合物 → 另一种单质 + 另一种化合物，这是<b>置换反应</b>。"},
            {"title": "锌溶解放出氢气",
             "html": "生成 <span class='text-emerald-600 font-semibold'>硫酸锌 (ZnSO₄)</span> 与 "
                     "<span class='text-sky-600 font-semibold'>氢气 (H₂↑)</span>，"
                     "固体逐渐溶解、有气泡产生。活动性 Zn > H，故能置换出酸中的氢。"},
        ],
    }


# 12) 金属与盐溶液（初中·置换·前置后）—— Fe + CuSO₄
def build_metal_salt_fe_cuso4():
    return {
        "meta": {"title": "铁与硫酸铜：湿法炼铜", "subtitle": "Fe + CuSO₄ → FeSO₄ + Cu（前置后置换）",
                 "language": "zh-CN", "category": "junior", "accent": "amber", "engine": "morph"},
        "conditions": {"text": "常温混合", "exothermic": False},
        "reactants": [{"species": "Fe", "count": 1, "pos": [-3.2, 0.3, 0]},
                      {"species": "CuSO4", "count": 1, "pos": [3.0, -0.2, 0]}],
        "products": [{"species": "FeSO4", "count": 1, "pos": [-2.6, 0.3, 0]},
                     {"species": "Cu", "count": 1, "pos": [2.8, -0.4, 0]}],
        "atom_map": [
            ["Fe#1.X", "FeSO4#1.Fe"],
            ["CuSO4#1.Cu", "Cu#1.X"],
            ["CuSO4#1.A", "FeSO4#1.A"],
            ["CuSO4#1.O1", "FeSO4#1.O1"], ["CuSO4#1.O2", "FeSO4#1.O2"],
            ["CuSO4#1.O3", "FeSO4#1.O3"], ["CuSO4#1.O4", "FeSO4#1.O4"],
        ],
        "activity": K.activity_strip("Fe", "Cu"),
        "energy": {"activation": 0.26, "deltaH": -0.38,
                   "reactantLabel": "Fe+CuSO₄", "productLabel": "FeSO₄+Cu"},
        "steps": [
            {"title": "铁钉放入硫酸铜",
             "html": "<span class='text-orange-600 font-semibold'>铁钉 (Fe)</span> 浸入 "
                     "<span class='text-sky-600 font-semibold'>硫酸铜溶液 (CuSO₄)</span>。"
                     "Fe 活动性 < Cu 之前的 <span class='font-bold'>Cu</span>——即 Fe 更活泼。"},
            {"title": "铁置换出铜",
             "html": "<span class='border-b border-dashed border-rose-500'>Fe 与 Cu²⁺ 交换成分</span>："
                     "Fe 失 2 e⁻ 变 Fe²⁺，Cu²⁺ 得 2 e⁻ 还原为 Cu 原子。"
                     "活动性更强的金属能把较不活泼的金属从其盐溶液中置换出来（「前置后」）。"},
            {"title": "铜析出·溶液变浅",
             "html": "生成 <span class='text-emerald-600 font-semibold'>硫酸亚铁 (FeSO₄)</span>（浅绿色溶液）"
                     "与 <span class='text-orange-600 font-semibold'>红色铜 (Cu)</span> 附着在铁表面。"
                     "古代「湿法炼铜」正是这个反应。原子守恒：Fe、Cu、S、O₄ 各 1。"},
        ],
    }


# 13) 溶质质量分数（初中·溶液计算·交互控制台）
def build_solution_mass_fraction():
    mf = K.mass_fraction(20, 80)          # 溶质 20 g、溶剂 80 g → 20%（kernel 精确）
    w_pct = _int_str(mf["percent"])
    ms = _int_str(mf["solute"])
    mw = _int_str(mf["solvent"])
    return {
        "meta": {"title": "溶质质量分数", "subtitle": "溶液组成与溶质质量分数的计算",
                 "language": "zh-CN", "category": "junior", "accent": "teal", "engine": "morph"},
        "conditions": {"text": "溶解", "exothermic": False},
        "reactants": [{"species": "NaCl", "count": 1, "pos": [-3.4, 0.4, 0]}] +
                     _placed("H2O", [(-1.6, 1.4, 0), (-0.2, 1.4, 0),
                                     (-1.6, -1.3, 0), (-0.2, -1.3, 0)]),
        "products": [{"species": "NaCl", "count": 1, "pos": [-1.2, 0.2, 0]}] +
                    _placed("H2O", [(-4.4, 1.8, 0), (1.6, 1.8, 0),
                                    (-4.4, -1.7, 0), (1.6, -1.7, 0)]),
        # 溶解是物理变化：原子与化学键都不变，仅扩散分开 → 用同一物种映射自身
        "atom_map": [
            ["NaCl#1.Na", "NaCl#1.Na"], ["NaCl#1.Cl", "NaCl#1.Cl"],
            ["H2O#1.A", "H2O#1.A"], ["H2O#1.Ha", "H2O#1.Ha"], ["H2O#1.Hb", "H2O#1.Hb"],
            ["H2O#2.A", "H2O#2.A"], ["H2O#2.Ha", "H2O#2.Ha"], ["H2O#2.Hb", "H2O#2.Hb"],
            ["H2O#3.A", "H2O#3.A"], ["H2O#3.Ha", "H2O#3.Ha"], ["H2O#3.Hb", "H2O#3.Hb"],
            ["H2O#4.A", "H2O#4.A"], ["H2O#4.Ha", "H2O#4.Ha"], ["H2O#4.Hb", "H2O#4.Hb"],
        ],
        "solution": {
            "label": "溶液组成计算台",
            "note": "拖动滑块实时重算",
            "params": [
                {"name": "ms", "label": "溶质 NaCl 质量 m质（溶剂固定 80 g）",
                 "min": 0, "max": 60, "step": 1, "value": 20, "unit": "g", "digits": 0},
            ],
            "readouts": [
                {"id": "msol", "label": "溶液质量 m液 = m质 + m剂",
                 "expr": f"ms + {mw}", "unit": "g", "digits": 0},
                {"id": "w", "label": "溶质质量分数 ω = m质 / m液 × 100%",
                 "expr": f"100 * ms / (ms + {mw})", "unit": "%", "digits": 1, "highlight": True,
                 "status": {"expr": f"abs(100 * ms / (ms + {mw}) - {w_pct})", "op": "<=", "rhs": 0.5,
                            "okText": f"恰为 {w_pct}%（达标）", "badText": f"偏离 {w_pct}%"}},
            ],
            "constant": {"label": "本题定值：溶剂质量 m剂 ≡",
                         "expr": mw, "unit": "g", "digits": 0},
        },
        "energy": None,
        "steps": [
            {"title": "溶质与溶剂",
             "html": "把 <span class='text-slate-600 font-semibold'>食盐 NaCl</span>（溶质）加入 "
                     "<span class='text-sky-600 font-semibold'>水 H₂O</span>（溶剂）中。"
                     "溶液质量 <b>m液 = m质 + m剂</b>。"},
            {"title": "溶解过程",
             "html": "搅拌后 NaCl 均匀分散到水中。注意：<span class='border-b border-dashed border-rose-500'>没有新物质生成</span>，"
                     "这是<b>物理变化</b>，化学键并未断裂重组。"},
            {"title": "计算质量分数",
             "html": "溶质质量分数 <b>ω = m质 / m液 × 100%</b>。取 m质 = 20 g、m剂 = 80 g："
                     f"ω = {ms} / ({ms} + {mw}) = <span class='text-emerald-600 font-bold'>{w_pct}%</span>。"
                     "拖动上方滑块改变 m质，观察 ω 如何随之变化（m剂 固定 80 g）。"},
        ],
    }


# 14) 溶液稀释（初中·溶液计算·稀释不变量）
def build_solution_dilution():
    d = K.dilution(50, 20, 10)            # 50 g 20% 稀释到 10% → 加水 50 g（m₂=100 g）
    return {
        "meta": {"title": "溶液的稀释", "subtitle": "浓溶液加水稀释：稀释前后溶质质量不变",
                 "language": "zh-CN", "category": "junior", "accent": "indigo", "engine": "morph"},
        "conditions": {"text": "稀释", "exothermic": False},
        "reactants": [{"species": "NaCl", "count": 1, "pos": [-3.4, 0.4, 0]}] +
                     _placed("H2O", [(-1.4, 1.5, 0), (0.0, 1.5, 0), (1.4, 1.5, 0), (2.8, 1.5, 0),
                                     (-1.4, -1.4, 0), (0.0, -1.4, 0), (1.4, -1.4, 0), (2.8, -1.4, 0)]),
        "products": [{"species": "NaCl", "count": 1, "pos": [-0.8, 0.2, 0]}] +
                    _placed("H2O", [(-4.6, 2.0, 0), (-2.4, 2.0, 0), (1.6, 2.0, 0), (3.8, 2.0, 0),
                                    (-4.6, -1.9, 0), (-2.4, -1.9, 0), (1.6, -1.9, 0), (3.8, -1.9, 0)]),
        "atom_map": [
            ["NaCl#1.Na", "NaCl#1.Na"], ["NaCl#1.Cl", "NaCl#1.Cl"],
            ["H2O#1.A", "H2O#1.A"], ["H2O#1.Ha", "H2O#1.Ha"], ["H2O#1.Hb", "H2O#1.Hb"],
            ["H2O#2.A", "H2O#2.A"], ["H2O#2.Ha", "H2O#2.Ha"], ["H2O#2.Hb", "H2O#2.Hb"],
            ["H2O#3.A", "H2O#3.A"], ["H2O#3.Ha", "H2O#3.Ha"], ["H2O#3.Hb", "H2O#3.Hb"],
            ["H2O#4.A", "H2O#4.A"], ["H2O#4.Ha", "H2O#4.Ha"], ["H2O#4.Hb", "H2O#4.Hb"],
            ["H2O#5.A", "H2O#5.A"], ["H2O#5.Ha", "H2O#5.Ha"], ["H2O#5.Hb", "H2O#5.Hb"],
            ["H2O#6.A", "H2O#6.A"], ["H2O#6.Ha", "H2O#6.Ha"], ["H2O#6.Hb", "H2O#6.Hb"],
            ["H2O#7.A", "H2O#7.A"], ["H2O#7.Ha", "H2O#7.Ha"], ["H2O#7.Hb", "H2O#7.Hb"],
            ["H2O#8.A", "H2O#8.A"], ["H2O#8.Ha", "H2O#8.Ha"], ["H2O#8.Hb", "H2O#8.Hb"],
        ],
        "solution": {
            "label": "稀释计算台",
            "note": "m₁w₁ = m₂w₂：溶质不变",
            "params": [
                {"name": "madd", "label": "加入水的质量", "min": 0, "max": 300,
                 "step": 10, "value": 0, "unit": "g", "digits": 0},
            ],
            "readouts": [
                {"id": "m2", "label": "稀释后溶液质量 m₂ = m₁ + m水",
                 "expr": "50 + madd", "unit": "g", "digits": 0},
                {"id": "w2", "label": "稀释后质量分数 ω₂ = m₁w₁ / m₂ × 100%",
                 "expr": "100 * 10 / (50 + madd)", "unit": "%", "digits": 1, "highlight": True,
                 "status": {"expr": "abs(100 * 10 / (50 + madd) - 10)", "op": "<=", "rhs": 0.05,
                            "okText": "ω₂ = 10%（达标）", "badText": "未达 10%"}},
            ],
            "constant": {"label": "稀释不变量：m质 = m₁w₁ ≡",
                         "expr": "50 * 20 / 100", "unit": "g", "digits": 0},
        },
        "energy": None,
        "steps": [
            {"title": "浓溶液",
             "html": "有 <span class='text-indigo-600 font-semibold'>50 g 质量分数 20% 的 NaCl 溶液</span>，"
                     "其中溶质 m₁w₁ = 50 × 20% = <b>10 g</b>，溶剂 40 g。"},
            {"title": "加水稀释",
             "html": "向其中加入 <span class='text-sky-600 font-semibold'>水</span>。"
                     "溶质、溶剂都不与水反应——<span class='border-b border-dashed border-rose-500'>溶质质量保持 10 g 不变</span>，"
                     "这是稀释计算的关键不变量。"},
            {"title": "列式求解",
             "html": "稀释前后 <b>m₁w₁ = m₂w₂</b>。设加水 x g：<br>"
                     f"10 = (50 + x) × ω₂；若要 ω₂ = 10%，则 50 + x = 100，"
                     f"x = <span class='text-emerald-600 font-bold'>{_int_str(d['water'])} g</span>。"
                     "拖动滑块验证 ω₂ 随加水量的变化。"},
        ],
    }


def _int_str(x):
    """sympy 数 → 紧凑字符串（150 → '150'）。"""
    return str(int(x)) if x == int(x) else str(x)


def _placed(species, positions):
    """同物种多实例 → 逐实例条目（各自 pos）。

    自动布局按 3.4 间距排一行，实例一多（≥4）就会超出相机视野（半宽 ≈ 6）；
    给同一条目一个 pos 又会让所有实例重叠。因此多实例场景一律用本函数
    逐个给紧凑的二维坐标（|x| ≤ 5.5、|y| ≤ 3、同排间距 ≥ 1.6）。
    """
    return [{"species": species, "count": 1, "pos": list(p)} for p in positions]


REGISTRY = {
    "combustion_ch4": build_combustion_ch4,
    "combustion_h2": build_combustion_h2,
    "electrolysis_water": build_electrolysis_water,
    "redox_na_cl2": build_redox_na_cl2,
    "esterification": build_esterification,
    "glucose_combustion": build_glucose_combustion,
    # 板块⑥：酸碱盐 / 金属活动性 / 溶液
    "neutralization_naoh_hcl": build_neutralization_naoh_hcl,
    "acid_carbonate_caco3": build_acid_carbonate_caco3,
    "alkali_salt_precipitate": build_alkali_salt_precipitate,
    "acid_metal_oxide_fe2o3": build_acid_metal_oxide,
    "metal_acid_zn": build_metal_acid_zn,
    "metal_salt_fe_cuso4": build_metal_salt_fe_cuso4,
    "solution_mass_fraction": build_solution_mass_fraction,
    "solution_dilution": build_solution_dilution,
}


def main(argv):
    # 统一入口（edulab/shared/skillkit.py）：
    #   python generate.py list | all <目录> | random [seed] [输出] | <key> [输出]
    # chem-reaction 的 build_* 产出「反应 spec」，渲染前先过 reaction_kernel 装配与校验
    return cli(REGISTRY, doc=__doc__,
               prepare=lambda key, raw: K.assemble_data(raw),
               template_name="reaction.html", token=PLACEHOLDER,
               index="化学反应 · 微观演示 · 交互课件", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
