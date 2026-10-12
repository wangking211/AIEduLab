#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
molecules.py — 常见分子/离子的理想化三维几何库（VSEPR）。

每个物种给出：
  - 元素与显示信息（化学式 unicode / LaTeX / 中英文名 / 标签配色）
  - 原子列表：每个原子有 slot（在该分子内的命名槽位）、el（元素）、pos（理想局部坐标）
  - 内部成键：slot 对 + 键级（1/2/3，或 'ionic' 离子键以虚线弱化表示）

坐标采用与模板一致的场景尺度（键长 ≈ 1.0–1.4 单位，原子半径见 ELEMENTS）。
分子在反应场景中的平移/旋转由 reaction_kernel 的“装配层”负责，本库只给标准朝向的局部几何。

混合几何策略：默认查本库；若运行环境装有 RDKit，reaction_kernel 可改用 RDKit 由 SMILES
生成真实构象（本库不主动安装任何依赖）。
"""

import math

# ---------------------------------------------------------------------------
# 元素表：配色（适配深色主题，参考 CPK 习惯）+ 球半径 + 中文名
# ---------------------------------------------------------------------------
ELEMENTS = {
    "C":  {"color": "#334155", "radius": 0.50, "zh": "碳",  "en": "Carbon"},
    "O":  {"color": "#ef4444", "radius": 0.42, "zh": "氧",  "en": "Oxygen"},
    "H":  {"color": "#f1f5f9", "radius": 0.25, "zh": "氢",  "en": "Hydrogen"},
    "N":  {"color": "#3b82f6", "radius": 0.46, "zh": "氮",  "en": "Nitrogen"},
    "Cl": {"color": "#22c55e", "radius": 0.52, "zh": "氯",  "en": "Chlorine"},
    "Na": {"color": "#a855f7", "radius": 0.58, "zh": "钠",  "en": "Sodium"},
    "S":  {"color": "#eab308", "radius": 0.52, "zh": "硫", "en": "Sulfur"},
    "Fe": {"color": "#f97316", "radius": 0.58, "zh": "铁",  "en": "Iron"},
    "Cu": {"color": "#fb923c", "radius": 0.56, "zh": "铜",  "en": "Copper"},
    "Mg": {"color": "#d1d5db", "radius": 0.56, "zh": "镁",  "en": "Magnesium"},
    "Ca": {"color": "#f8fafc", "radius": 0.60, "zh": "钙",  "en": "Calcium"},
    "Zn": {"color": "#a1a1aa", "radius": 0.56, "zh": "锌",  "en": "Zinc"},
    "Ag": {"color": "#e2e8f0", "radius": 0.58, "zh": "银",  "en": "Silver"},
    "Al": {"color": "#cbd5e1", "radius": 0.52, "zh": "铝",  "en": "Aluminium"},
    "K":  {"color": "#c084fc", "radius": 0.64, "zh": "钾",  "en": "Potassium"},
}

# 离子电荷的显示（用于守恒/电子转移叠加层；几何库本身只描述原子核位置）
DEFAULT_CHARGE = {}


def element_color(el):
    return ELEMENTS.get(el, {"color": "#94a3b8"})["color"]


def element_radius(el):
    return ELEMENTS.get(el, {"radius": 0.45})["radius"]


# ---------------------------------------------------------------------------
# 几何构造工具
# ---------------------------------------------------------------------------
_INV_SQRT3 = 1.0 / math.sqrt(3.0)


def _r(v, n=4):
    return [round(float(x), n) for x in v]


def _atom(slot, el, pos):
    return {"slot": slot, "el": el, "pos": _r(pos)}


def _tetra_dirs():
    """正四面体的 4 个顶点方向（单位向量）。"""
    base = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
    return [tuple(c * _INV_SQRT3 for c in d) for d in base]


def _diatomic(slot_a, el_a, slot_b, el_b, d, order):
    half = d / 2.0
    return {
        "atoms": [_atom(slot_a, el_a, (-half, 0, 0)), _atom(slot_b, el_b, (half, 0, 0))],
        "bonds": [{"a": slot_a, "b": slot_b, "order": order}],
    }


def _linear_triatomic(center_el, out_el, d, order):
    """X=Y=X 线形（如 CO2）。中心在原点，两侧原子沿 ±x。"""
    return {
        "atoms": [
            _atom("Y", center_el, (0, 0, 0)),
            _atom("Xa", out_el, (-d, 0, 0)),
            _atom("Xb", out_el, (d, 0, 0)),
        ],
        "bonds": [
            {"a": "Y", "b": "Xa", "order": order},
            {"a": "Y", "b": "Xb", "order": order},
        ],
    }


def _bent(center_el, out_el, d, angle_deg, order=1):
    """弯曲形 AX2E（如 H2O）。中心在原点，两枝对称张开、朝 +y。"""
    half = math.radians(angle_deg) / 2.0
    sx, cy = d * math.sin(half), d * math.cos(half)
    return {
        "atoms": [
            _atom("A", center_el, (0, 0, 0)),
            _atom("Ha", out_el, (sx, cy, 0)),
            _atom("Hb", out_el, (-sx, cy, 0)),
        ],
        "bonds": [
            {"a": "A", "b": "Ha", "order": order},
            {"a": "A", "b": "Hb", "order": order},
        ],
    }


def _tetrahedral(center_el, out_el, d):
    """正四面体 AX4（如 CH4）。中心在原点，4 枝沿四面体方向。"""
    atoms = [_atom("C", center_el, (0, 0, 0))]
    bonds = []
    for i, dr in enumerate(_tetra_dirs(), start=1):
        slot = f"H{i}"
        atoms.append(_atom(slot, out_el, tuple(c * d for c in dr)))
        bonds.append({"a": "C", "b": slot, "order": 1})
    return {"atoms": atoms, "bonds": bonds}


def _pyramidal(center_el, out_el, d, h=0.38):
    """三角锥 AX3E（如 NH3）。中心抬高 h，三枝在下方均布。"""
    atoms = [_atom("A", center_el, (0, h, 0))]
    bonds = []
    rad = d * math.cos(math.radians(20))
    for i in range(3):
        ang = math.radians(90 + i * 120)
        atoms.append(_atom(f"H{i + 1}", out_el,
                           (rad * math.cos(ang), h - d * math.sin(math.radians(20)) - 0.3,
                            rad * math.sin(ang))))
        bonds.append({"a": "A", "b": f"H{i + 1}", "order": 1})
    return {"atoms": atoms, "bonds": bonds}


def _mono(el):
    """单原子物种（金属/原子，如 Na、C(石墨简化)、Fe）。"""
    return {"atoms": [_atom("X", el, (0, 0, 0))], "bonds": []}


def _ion_pair(slot_a, el_a, slot_b, el_b, d):
    """离子对（如 NaCl 式量单元）：以弱化的离子键连接。"""
    half = d / 2.0
    return {
        "atoms": [_atom(slot_a, el_a, (-half, 0, 0)), _atom(slot_b, el_b, (half, 0, 0))],
        "bonds": [{"a": slot_a, "b": slot_b, "order": "ionic"}],
    }


def _oxo_anion(center_el, n, d):
    """含氧酸根：n=3 平面正三角（CO₃²⁻、NO₃⁻），n=4 正四面体（SO₄²⁻）。
    中心槽 A，外围氧槽 O1..On；几何中心在原点。"""
    if n == 4:
        pts = [tuple(c * d for c in dr) for dr in _tetra_dirs()]
    else:
        pts = [(d * math.cos(math.radians(90 + i * 120)),
                d * math.sin(math.radians(90 + i * 120)), 0.0) for i in range(n)]
    atoms = [_atom("A", center_el, (0, 0, 0))]
    bonds = []
    for i, p in enumerate(pts, 1):
        atoms.append(_atom(f"O{i}", "O", _r(p)))
        bonds.append({"a": "A", "b": f"O{i}", "order": 1})
    return {"atoms": atoms, "bonds": bonds}


def _oxo_salt(metal_slot, metal_el, center_el, n_anion, n_metal, gap=1.55, spread=1.25):
    """式量单元：左侧金属阳离子（竖排 n_metal 个）+ 右侧含氧酸根，离子键连向酸根中心。
    槽位：金属 metal_slot（单个）或 metal_slot1..n（多个）、酸根 A 与 O1..On。"""
    anion = _oxo_anion(center_el, n_anion, 1.30 if n_anion == 4 else 1.24)
    for a in anion["atoms"]:
        a["pos"] = _r([a["pos"][0] + gap, a["pos"][1], a["pos"][2]])
    atoms, bonds = [], list(anion["bonds"])
    for j in range(n_metal):
        slot = metal_slot if n_metal == 1 else f"{metal_slot}{j + 1}"
        y = (j - (n_metal - 1) / 2.0) * spread
        atoms.append(_atom(slot, metal_el, _r((-0.15, y, 0))))
        bonds.append({"a": slot, "b": "A", "order": "ionic"})
    return {"atoms": atoms + anion["atoms"], "bonds": bonds}


def _hydroxide(metal_slot, metal_el, n_metal, n_oh, gap=1.5, spread=1.35):
    """金属氢氧化物 M(OH)n_oh：左侧 n_metal 个金属 + 右侧 n_oh 个 –OH
    （O–H 共价，金属–O 离子键）。槽位：metal_slot 或 metal_slot1..n、O1..On、H1..Hn。"""
    atoms, bonds = [], []
    my = (n_metal - 1) / 2.0
    for j in range(n_metal):
        mslot = metal_slot if n_metal == 1 else f"{metal_slot}{j + 1}"
        atoms.append(_atom(mslot, metal_el, _r((-0.15, (j - my) * spread, 0))))
    oy = (n_oh - 1) / 2.0
    for k in range(n_oh):
        y = (k - oy) * spread
        atoms.append(_atom(f"O{k + 1}", "O", _r((gap, y, 0))))
        atoms.append(_atom(f"H{k + 1}", "H", _r((gap + 0.95, y + 0.15, 0))))
        mslot = metal_slot if n_metal == 1 else f"{metal_slot}{(k % n_metal) + 1}"
        bonds.append({"a": mslot, "b": f"O{k + 1}", "order": "ionic"})
        bonds.append({"a": f"O{k + 1}", "b": f"H{k + 1}", "order": 1})
    return {"atoms": atoms, "bonds": bonds}


def _hydrogen_oxo_acid(center_el, n_anion, n_h, d=1.30, dh=0.97):
    """含氧酸（如 H₂SO₄）：中心原子 A + n 个氧（四面体），前 n_h 个氧各接一个 H。
    槽位：A、O1..On、H1..H{n_h}。"""
    pts = [tuple(c * d for c in dr) for dr in _tetra_dirs()]
    atoms = [_atom("A", center_el, (0, 0, 0))]
    bonds = []
    for i, p in enumerate(pts[:n_anion], 1):
        atoms.append(_atom(f"O{i}", "O", _r(p)))
        bonds.append({"a": "A", "b": f"O{i}", "order": 1})
    for i in range(1, n_h + 1):
        ox, oy, oz = atoms[i]["pos"]
        L = math.sqrt(ox * ox + oy * oy + oz * oz) or 1.0
        s = (L + dh) / L
        atoms.append(_atom(f"H{i}", "H", _r((ox * s, oy * s, oz * s))))
        bonds.append({"a": f"O{i}", "b": f"H{i}", "order": 1})
    return {"atoms": atoms, "bonds": bonds}


def _metal_halide(metal_slot, metal_el, halide_el, n_halide, gap=1.75, spread=1.35):
    """金属卤化物（如 CaCl₂）：金属 + n 个卤素，金属–卤素离子键。
    槽位：metal_slot、X1..Xn。"""
    atoms = [_atom(metal_slot, metal_el, _r((0, 0, 0)))]
    bonds = []
    for i in range(n_halide):
        y = (i - (n_halide - 1) / 2.0) * spread
        atoms.append(_atom(f"X{i + 1}", halide_el, _r((gap, y, 0))))
        bonds.append({"a": metal_slot, "b": f"X{i + 1}", "order": "ionic"})
    return {"atoms": atoms, "bonds": bonds}


def _metal_multi_anion(metal_slot, metal_el, center_el, n_oxy, n_groups, gap=1.55, spread=1.5):
    """一个金属 + n_groups 个含氧酸根（如 Cu(NO₃)₂）。
    槽位：金属 metal_slot；第 k 组中心 A{k}、氧 O{k}_{1..n}。"""
    atoms, bonds = [], []
    gy = (n_groups - 1) / 2.0
    for k in range(1, n_groups + 1):
        dy = (k - 1 - gy) * spread
        g = _oxo_anion(center_el, n_oxy, 1.30 if n_oxy == 4 else 1.24)
        for a in g["atoms"]:
            slot = f"A{k}" if a["slot"] == "A" else f"O{k}_{a['slot'][1]}"
            atoms.append(_atom(slot, a["el"], _r([a["pos"][0] + gap, a["pos"][1] + dy, a["pos"][2]])))
        for b in g["bonds"]:
            na = f"A{k}" if b["a"] == "A" else f"O{k}_{b['a'][1]}"
            nb = f"O{k}_{b['b'][1]}"
            bonds.append({"a": na, "b": nb, "order": b["order"]})
    atoms.append(_atom(metal_slot, metal_el, _r((-0.15, 0, 0))))
    for k in range(1, n_groups + 1):
        bonds.append({"a": metal_slot, "b": f"A{k}", "order": "ionic"})
    return {"atoms": atoms, "bonds": bonds}


def _rust():
    """氧化铁 Fe₂O₃（铁锈主要成分）：2 Fe + 3 O 的紧凑团簇。"""
    atoms = [_atom("Fe1", "Fe", _r((-1.0, 0.55, 0))),
             _atom("Fe2", "Fe", _r((-1.0, -0.55, 0))),
             _atom("O1", "O", _r((0.55, 1.05, 0))),
             _atom("O2", "O", _r((0.55, 0.0, 0))),
             _atom("O3", "O", _r((0.55, -1.05, 0)))]
    bonds = [{"a": f"Fe{f}", "b": f"O{o}", "order": "ionic"}
             for f in (1, 2) for o in (1, 2, 3)]
    return {"atoms": atoms, "bonds": bonds}


def _glucose_openchain():
    """D-葡萄糖开链式（Fischer 投影简化 3D）：6 碳醛糖，主链沿 Y 轴排列。
    slots: C1-C6, O1-O6, H1-H5, H6a, H6b, HO2-HO6（共 24 原子）。"""
    a, b = [], []
    yc = [3.75, 2.25, 0.75, -0.75, -2.25, -3.75]   # C1..C6 的 y 坐标
    # C1: 醛基 (CHO)
    a += [_atom("C1", "C", (0,    yc[0], 0)),
          _atom("O1", "O", (0,    yc[0] + 1.0, 0)),   # C=O 羰基
          _atom("H1", "H", (-1.1, yc[0], 0))]          # 醛 H
    b += [{"a": "C1", "b": "O1", "order": 2}, {"a": "C1", "b": "H1", "order": 1}]
    # C2 (OH 右)
    a += [_atom("C2",  "C", (0,    yc[1], 0)), _atom("O2",  "O", (1.4,  yc[1], 0)),
          _atom("HO2", "H", (2.1,  yc[1], 0)), _atom("H2",  "H", (-1.1, yc[1], 0))]
    b += [{"a": "C1", "b": "C2",  "order": 1}, {"a": "C2", "b": "O2",  "order": 1},
          {"a": "O2", "b": "HO2", "order": 1}, {"a": "C2", "b": "H2",  "order": 1}]
    # C3 (OH 左)
    a += [_atom("C3",  "C", (0,    yc[2], 0)), _atom("O3",  "O", (-1.4, yc[2], 0)),
          _atom("HO3", "H", (-2.1, yc[2], 0)), _atom("H3",  "H", (1.1,  yc[2], 0))]
    b += [{"a": "C2", "b": "C3",  "order": 1}, {"a": "C3", "b": "O3",  "order": 1},
          {"a": "O3", "b": "HO3", "order": 1}, {"a": "C3", "b": "H3",  "order": 1}]
    # C4 (OH 右)
    a += [_atom("C4",  "C", (0,    yc[3], 0)), _atom("O4",  "O", (1.4,  yc[3], 0)),
          _atom("HO4", "H", (2.1,  yc[3], 0)), _atom("H4",  "H", (-1.1, yc[3], 0))]
    b += [{"a": "C3", "b": "C4",  "order": 1}, {"a": "C4", "b": "O4",  "order": 1},
          {"a": "O4", "b": "HO4", "order": 1}, {"a": "C4", "b": "H4",  "order": 1}]
    # C5 (OH 左)
    a += [_atom("C5",  "C", (0,    yc[4], 0)), _atom("O5",  "O", (-1.4, yc[4], 0)),
          _atom("HO5", "H", (-2.1, yc[4], 0)), _atom("H5",  "H", (1.1,  yc[4], 0))]
    b += [{"a": "C4", "b": "C5",  "order": 1}, {"a": "C5", "b": "O5",  "order": 1},
          {"a": "O5", "b": "HO5", "order": 1}, {"a": "C5", "b": "H5",  "order": 1}]
    # C6: 伯醇 (CH₂OH)
    a += [_atom("C6",  "C", (0,    yc[5],        0)),
          _atom("H6a", "H", (-0.8, yc[5] - 0.7,  0.5)),
          _atom("H6b", "H", (-0.8, yc[5] - 0.7, -0.5)),
          _atom("O6",  "O", (1.0,  yc[5] - 0.7,  0)),
          _atom("HO6", "H", (1.7,  yc[5] - 0.7,  0))]
    b += [{"a": "C5", "b": "C6",  "order": 1}, {"a": "C6", "b": "H6a", "order": 1},
          {"a": "C6", "b": "H6b", "order": 1}, {"a": "C6", "b": "O6",  "order": 1},
          {"a": "O6", "b": "HO6", "order": 1}]
    return {"atoms": a, "bonds": b}


# ---------------------------------------------------------------------------
# 物种库：id -> 构造（几何 + 显示元数据）
# 显示用 unicode 下标化学式 + LaTeX；name 中文、name_en 英文。
# ---------------------------------------------------------------------------
def _spec(species_id, geom, formula, latex, zh, en, color):
    return {
        "id": species_id,
        "formula": formula,
        "latex": latex,
        "name": zh,
        "name_en": en,
        "color": color,
        "atoms": geom["atoms"],
        "bonds": geom["bonds"],
    }


_LIBRARY_BUILDERS = {
    # — 双原子单质 / 气体 —
    "H2":  lambda: _spec("H2",  _diatomic("Ha", "H", "Hb", "H", 0.90, 1),
                         "H₂", r"\text{H}_2", "氢气", "hydrogen", "sky"),
    "O2":  lambda: _spec("O2",  _diatomic("Oa", "O", "Ob", "O", 1.10, 2),
                         "O₂", r"\text{O}_2", "氧气", "oxygen", "red"),
    "N2":  lambda: _spec("N2",  _diatomic("Na", "N", "Nb", "N", 1.05, 3),
                         "N₂", r"\text{N}_2", "氮气", "nitrogen", "blue"),
    "Cl2": lambda: _spec("Cl2", _diatomic("Cla", "Cl", "Clb", "Cl", 1.45, 1),
                         "Cl₂", r"\text{Cl}_2", "氯气", "chlorine", "green"),
    "CO":  lambda: _spec("CO",  _diatomic("C", "C", "O", "O", 1.13, 3),
                         "CO", r"\text{CO}", "一氧化碳", "carbon monoxide", "slate"),
    # — 三原子 / 多原子分子 —
    "CO2": lambda: _spec("CO2", _linear_triatomic("C", "O", 1.16, 2),
                         "CO₂", r"\text{CO}_2", "二氧化碳", "carbon dioxide", "slate"),
    "H2O": lambda: _spec("H2O", _bent("O", "H", 0.96, 104.5),
                         "H₂O", r"\text{H}_2\text{O}", "水", "water", "cyan"),
    "CH4": lambda: _spec("CH4", _tetrahedral("C", "H", 1.10),
                         "CH₄", r"\text{CH}_4", "甲烷", "methane", "slate"),
    "NH3": lambda: _spec("NH3", _pyramidal("N", "H", 1.0),
                         "NH₃", r"\text{NH}_3", "氨气", "ammonia", "blue"),
    # — 金属 / 原子 / 离子对 —
    "Na":  lambda: _spec("Na", _mono("Na"), "Na", r"\text{Na}", "钠", "sodium", "violet"),
    "C":   lambda: _spec("C",  _mono("C"),  "C",  r"\text{C}",  "碳", "carbon", "slate"),
    "Fe":  lambda: _spec("Fe", _mono("Fe"), "Fe", r"\text{Fe}", "铁", "iron", "orange"),
    "Mg":  lambda: _spec("Mg", _mono("Mg"), "Mg", r"\text{Mg}", "镁", "magnesium", "slate"),
    "NaCl": lambda: _spec("NaCl", _ion_pair("Na", "Na", "Cl", "Cl", 1.50),
                          "NaCl", r"\text{NaCl}", "氯化钠", "sodium chloride", "violet"),
    # —— 初中·酸碱盐 / 金属活动性 新增 ——
    "HCl": lambda: _spec("HCl", _diatomic("H", "H", "Cl", "Cl", 1.28, 1),
                         "HCl", r"\text{HCl}", "盐酸（氯化氢）", "hydrochloric acid", "red"),
    "H2SO4": lambda: _spec("H2SO4", _hydrogen_oxo_acid("S", 4, 2),
                           "H₂SO₄", r"\text{H}_2\text{SO}_4", "硫酸", "sulfuric acid", "red"),
    "NaOH": lambda: _spec("NaOH", _hydroxide("Na", "Na", 1, 1),
                          "NaOH", r"\text{NaOH}", "氢氧化钠", "sodium hydroxide", "violet"),
    "CaOH2": lambda: _spec("CaOH2", _hydroxide("Ca", "Ca", 1, 2),
                           "Ca(OH)₂", r"\text{Ca(OH)}_2", "氢氧化钙（熟石灰）",
                           "calcium hydroxide", "slate"),
    "CuOH2": lambda: _spec("CuOH2", _hydroxide("Cu", "Cu", 1, 2),
                           "Cu(OH)₂", r"\text{Cu(OH)}_2", "氢氧化铜（沉淀）",
                           "copper hydroxide", "orange"),
    "Na2CO3": lambda: _spec("Na2CO3", _oxo_salt("Na", "Na", "C", 3, 2),
                            "Na₂CO₃", r"\text{Na}_2\text{CO}_3", "碳酸钠（纯碱）",
                            "sodium carbonate", "violet"),
    "Na2SO4": lambda: _spec("Na2SO4", _oxo_salt("Na", "Na", "S", 4, 2),
                            "Na₂SO₄", r"\text{Na}_2\text{SO}_4", "硫酸钠", "sodium sulfate", "violet"),
    "CaCO3": lambda: _spec("CaCO3", _oxo_salt("Ca", "Ca", "C", 3, 1),
                           "CaCO₃", r"\text{CaCO}_3", "碳酸钙（石灰石）", "calcium carbonate", "slate"),
    "CaCl2": lambda: _spec("CaCl2", _metal_halide("Ca", "Ca", "Cl", 2),
                           "CaCl₂", r"\text{CaCl}_2", "氯化钙", "calcium chloride", "slate"),
    "FeCl3": lambda: _spec("FeCl3", _metal_halide("Fe", "Fe", "Cl", 3),
                           "FeCl₃", r"\text{FeCl}_3", "氯化铁", "iron(III) chloride", "orange"),
    "CuSO4": lambda: _spec("CuSO4", _oxo_salt("Cu", "Cu", "S", 4, 1),
                           "CuSO₄", r"\text{CuSO}_4", "硫酸铜", "copper sulfate", "orange"),
    "FeSO4": lambda: _spec("FeSO4", _oxo_salt("Fe", "Fe", "S", 4, 1),
                           "FeSO₄", r"\text{FeSO}_4", "硫酸亚铁", "iron(II) sulfate", "orange"),
    "ZnSO4": lambda: _spec("ZnSO4", _oxo_salt("Zn", "Zn", "S", 4, 1),
                           "ZnSO₄", r"\text{ZnSO}_4", "硫酸锌", "zinc sulfate", "slate"),
    "AgNO3": lambda: _spec("AgNO3", _oxo_salt("Ag", "Ag", "N", 3, 1),
                           "AgNO₃", r"\text{AgNO}_3", "硝酸银", "silver nitrate", "slate"),
    "CuNO3_2": lambda: _spec("CuNO3_2", _metal_multi_anion("Cu", "Cu", "N", 3, 2),
                             "Cu(NO₃)₂", r"\text{Cu(NO}_3)_2", "硝酸铜", "copper nitrate", "orange"),
    "AgCl": lambda: _spec("AgCl", _ion_pair("Ag", "Ag", "Cl", "Cl", 1.60),
                          "AgCl", r"\text{AgCl}", "氯化银（沉淀）", "silver chloride", "slate"),
    "Fe2O3": lambda: _spec("Fe2O3", _rust(),
                           "Fe₂O₃", r"\text{Fe}_2\text{O}_3", "氧化铁（铁锈）", "iron(III) oxide", "orange"),
    "Zn": lambda: _spec("Zn", _mono("Zn"), "Zn", r"\text{Zn}", "锌", "zinc", "slate"),
    "Ag": lambda: _spec("Ag", _mono("Ag"), "Ag", r"\text{Ag}", "银", "silver", "slate"),
    "Cu": lambda: _spec("Cu", _mono("Cu"), "Cu", r"\text{Cu}", "铜", "copper", "orange"),
    "Glucose": lambda: _spec("Glucose", _glucose_openchain(),
                             "C₆H₁₂O₆", r"\text{C}_6\text{H}_{12}\text{O}_6",
                             "葡萄糖", "glucose", "amber"),
}


def known_species():
    return sorted(_LIBRARY_BUILDERS.keys())


def has_species(species_id):
    return species_id in _LIBRARY_BUILDERS


def get(species_id):
    """返回某物种的几何 + 元数据（深拷贝，可安全修改）。"""
    if species_id not in _LIBRARY_BUILDERS:
        raise KeyError(f"未知物种 {species_id}；本库已收录: {', '.join(known_species())}")
    spec = _LIBRARY_BUILDERS[species_id]()
    # 深拷贝原子/键，避免调用方互相污染
    spec["atoms"] = [dict(a, pos=list(a["pos"])) for a in spec["atoms"]]
    spec["bonds"] = [dict(b) for b in spec["bonds"]]
    return spec


def atom_counts(species_id):
    """该物种的元素原子计数，用于配平 / 守恒校验。"""
    counts = {}
    for a in _LIBRARY_BUILDERS[species_id]()["atoms"]:
        counts[a["el"]] = counts.get(a["el"], 0) + 1
    return counts


if __name__ == "__main__":
    # 自检：打印每个物种的原子数与元素计数
    for sid in known_species():
        m = get(sid)
        print(f"{sid:6s} {m['formula']:6s} atoms={len(m['atoms'])} "
              f"bonds={len(m['bonds'])} counts={atom_counts(sid)}")
