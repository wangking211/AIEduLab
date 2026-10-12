#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reaction_kernel.py — 化学反应的“精确计算核”。

职责（与几何技能里的 sympy kernel 对应）：
  1. 配平：由反应物/产物化学式，用 sympy 零空间求整数化学计量数（方程系数有保证）。
  2. 守恒/原子映射校验：反应前后原子一一对应、元素相同、键的断/成自洽。
  3. 场景装配：把分子实例摆进场景，算出每个原子在“反应物态(start)”与“产物态(end)”的世界坐标。
  4. 键差推导：bonds_before / bonds_after → broken / formed / kept（驱动断键红虚线、成键绿渐显）。
  5. 产出注入模板的 data（原子、键、标签、守恒计数、方程、步骤、可选叠加层）。

两种作者级别（都汇流到同一份 data）：
  - 高层（species + atom_map）：适合任意“原子打散重组”反应，kernel 负责展开实例 + 校验 + 算坐标。
  - 低层（显式 atoms + bonds_before/after + fragments）：适合有机机理这类需精细编排的反应。

依赖：仅 sympy（与本仓库其它 kernel 一致）。混合几何：若环境装有 RDKit，可在高层路径中
对库未收录的物种由 SMILES 生成构象（rdkit_available 探测；绝不自动安装）。
"""

import math
import sympy as sp

import molecules as M


# ===========================================================================
# 0) 混合几何：RDKit 可选探测
# ===========================================================================
def rdkit_available():
    try:
        import rdkit  # noqa: F401
        return True
    except Exception:
        return False


# ===========================================================================
# 1) 几何变换（纯 math，避免额外依赖）
# ===========================================================================
def _rot_matrix(rot):
    """欧拉角 (rx,ry,rz)，弧度；按 Rz·Ry·Rx 复合（与三维 demo 的小角度旋转一致）。"""
    rx, ry, rz = (rot + [0, 0, 0])[:3] if isinstance(rot, list) else (0, 0, 0)
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    # R = Rz Ry Rx
    return [
        [cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx],
        [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx],
        [-sy,     cy * sx,                cy * cx],
    ]


def _apply(local, pos, rot):
    R = _rot_matrix(rot)
    x, y, z = local
    wx = R[0][0] * x + R[0][1] * y + R[0][2] * z + pos[0]
    wy = R[1][0] * x + R[1][1] * y + R[1][2] * z + pos[1]
    wz = R[2][0] * x + R[2][1] * y + R[2][2] * z + pos[2]
    return [round(wx, 4), round(wy, 4), round(wz, 4)]


# ===========================================================================
# 2) 配平：sympy 零空间
# ===========================================================================
def balanced_coefficients(reactant_species, product_species):
    """
    输入反应物、产物物种 id 列表（可重复表示已知系数，但通常给去重的物种）。
    返回 (r_coef, p_coef)：与输入顺序对应的最小正整数化学计量数。
    """
    species = list(reactant_species) + list(product_species)
    elements = sorted({el for s in species for el in M.atom_counts(s)})
    # 元素×物种 矩阵；反应物为正、产物为负 → 求 M x = 0
    rows = []
    for el in elements:
        row = [M.atom_counts(s).get(el, 0) for s in reactant_species]
        row += [-M.atom_counts(s).get(el, 0) for s in product_species]
        rows.append(row)
    A = sp.Matrix(rows)
    ns = A.nullspace()
    if len(ns) != 1:
        raise ValueError(f"配平不唯一或无解（零空间维数={len(ns)}）：{reactant_species}->{product_species}")
    vec = ns[0]
    denoms = [sp.nsimplify(v).as_numer_denom()[1] for v in vec]
    lcm = sp.ilcm(*denoms) if denoms else 1
    ints = [int(sp.nsimplify(v) * lcm) for v in vec]
    g = 0
    for v in ints:
        g = math.gcd(g, abs(v))
    ints = [v // g for v in ints] if g else ints
    if any(v < 0 for v in ints):
        ints = [-v for v in ints]
    n = len(reactant_species)
    return ints[:n], ints[n:]


# ===========================================================================
# 3) 实例展开 + 自动布局
# ===========================================================================
def _expand(side_list, default_y=0.0):
    """把 [{species,count,pos?,rot?}] 展开为实例列表；缺 pos 的按居中行自动布局。"""
    inst = []
    counter = {}
    for entry in side_list:
        sp_id = entry["species"]
        cnt = entry.get("count", 1)
        for _ in range(cnt):
            counter[sp_id] = counter.get(sp_id, 0) + 1
            inst.append({
                "id": f"{sp_id}#{counter[sp_id]}",
                "species": sp_id,
                "pos": entry.get("pos"),
                "rot": entry.get("rot", [0, 0, 0]),
                "explicit": entry.get("pos") is not None,
            })
    # 自动布局：居中一行，y 轻微之字错落
    k = len(inst)
    spacing = 3.4
    for i, it in enumerate(inst):
        if not it["explicit"]:
            it["pos"] = [round((i - (k - 1) / 2.0) * spacing, 3),
                         round(default_y + (0.6 if i % 2 else -0.6), 3), 0.0]
    return inst


def _instance_atoms(inst):
    """实例 → {ref: {el, world}} 与内部键 [(refA,refB,order)]。ref = 'SPECIES#k.slot'。"""
    mol = M.get(inst["species"])
    refs = {}
    for a in mol["atoms"]:
        ref = f"{inst['id']}.{a['slot']}"
        refs[ref] = {"el": a["el"], "world": _apply(a["pos"], inst["pos"], inst["rot"])}
    bonds = [(f"{inst['id']}.{b['a']}", f"{inst['id']}.{b['b']}", b["order"]) for b in mol["bonds"]]
    return refs, bonds


# ===========================================================================
# 4) 高层解析：species + atom_map → resolved（atoms/before/after）
# ===========================================================================
def resolve_high_level(spec):
    r_inst = _expand(spec["reactants"])
    p_inst = _expand(spec["products"])

    r_refs, r_bonds = {}, []
    for it in r_inst:
        refs, bonds = _instance_atoms(it)
        r_refs.update(refs)
        r_bonds += bonds
    p_refs, p_bonds = {}, []
    for it in p_inst:
        refs, bonds = _instance_atoms(it)
        p_refs.update(refs)
        p_bonds += bonds

    amap = spec["atom_map"]
    map_r = [pair[0] for pair in amap]
    map_p = [pair[1] for pair in amap]

    # —— 校验：原子映射是反应物原子↔产物原子的双射 ——
    if set(map_r) != set(r_refs):
        missing = set(r_refs) - set(map_r)
        extra = set(map_r) - set(r_refs)
        raise ValueError(f"atom_map 反应物侧不匹配：未映射 {sorted(missing)}；未知 {sorted(extra)}")
    if set(map_p) != set(p_refs):
        missing = set(p_refs) - set(map_p)
        extra = set(map_p) - set(p_refs)
        raise ValueError(f"atom_map 产物侧不匹配：未映射 {sorted(missing)}；未知 {sorted(extra)}")
    if len(map_r) != len(set(map_r)) or len(map_p) != len(set(map_p)):
        raise ValueError("atom_map 存在重复引用（必须一一对应）")

    # —— 分配全局原子 id（元素 + 计数），同一对反应物/产物 ref 共享 id ——
    rid, pid, atoms_out = {}, {}, []
    el_counter = {}
    for rr, pr in amap:
        el = r_refs[rr]["el"]
        if p_refs[pr]["el"] != el:
            raise ValueError(f"原子映射元素不一致：{rr}({el}) ↔ {pr}({p_refs[pr]['el']})")
        el_counter[el] = el_counter.get(el, 0) + 1
        aid = f"{el}{el_counter[el]}"
        rid[rr] = pid[pr] = aid
        atoms_out.append({
            "id": aid, "el": el,
            "color": M.element_color(el), "radius": M.element_radius(el),
            "start": r_refs[rr]["world"], "end": p_refs[pr]["world"],
            "rmol": rr.split(".")[0], "pmol": pr.split(".")[0],
        })

    before = [{"a": rid[a], "b": rid[b], "order": o} for a, b, o in r_bonds]
    after = [{"a": pid[a], "b": pid[b], "order": o} for a, b, o in p_bonds]
    return atoms_out, before, after, r_inst, p_inst


# ===========================================================================
# 5) 低层解析：显式 atoms/bonds（机理路径）
# ===========================================================================
def resolve_low_level(spec):
    """
    spec["atoms"]: [{id,el,start,end,rmol,pmol, frag?, flocal?}]
    spec["bonds_before"/"bonds_after"]: [{a,b,order}]（全局 id）
    其余实例信息从 reactants/products 取（仅用于标签与方程）。
    """
    atoms_out = []
    for a in spec["atoms"]:
        el = a["el"]
        atoms_out.append({
            "id": a["id"], "el": el,
            "color": M.element_color(el), "radius": M.element_radius(el),
            "start": a["start"], "end": a["end"],
            "rmol": a.get("rmol"), "pmol": a.get("pmol"),
            **({"frag": a["frag"]} if a.get("frag") else {}),
            **({"flocal": a["flocal"]} if a.get("flocal") is not None else {}),
        })
    before = [dict(b) for b in spec.get("bonds_before", [])]
    after = [dict(b) for b in spec.get("bonds_after", [])]
    r_inst = _expand(spec.get("reactants", []))
    p_inst = _expand(spec.get("products", []))
    return atoms_out, before, after, r_inst, p_inst


# ===========================================================================
# 6) 键差、守恒、方程
# ===========================================================================
def _bkey(b):
    return (tuple(sorted([b["a"], b["b"]])), b["order"])


def bond_diff(before, after):
    bset = {_bkey(b): b for b in before}
    aset = {_bkey(b): b for b in after}
    broken = [b for k, b in bset.items() if k not in aset]
    formed = [b for k, b in aset.items() if k not in bset]
    kept = [b for k, b in aset.items() if k in bset]
    return broken, formed, kept


def element_counts(atoms):
    counts = {}
    for a in atoms:
        counts[a["el"]] = counts.get(a["el"], 0) + 1
    return counts


def verify_conservation(atoms, before, after):
    """断言：原子在反应前后元素守恒（同一批原子，故 start/end 元素计数必相等）。"""
    counts = element_counts(atoms)
    # 键级合法性：每个键端点都存在
    ids = {a["id"] for a in atoms}
    for b in before + after:
        if b["a"] not in ids or b["b"] not in ids:
            raise ValueError(f"键引用了不存在的原子：{b}")
    return counts


def _grouped(inst_list):
    """按物种聚合实例 → [(species, count)] 保持出现顺序。"""
    order, cnt = [], {}
    for it in inst_list:
        s = it["species"]
        if s not in cnt:
            order.append(s)
        cnt[s] = cnt.get(s, 0) + 1
    return [(s, cnt[s]) for s in order]


def _term(latex, c):
    return latex if c == 1 else f"{c}\\,{latex}"


def equation_latex(r_groups, p_groups, conditions):
    left = " + ".join(_term(M.get(s)["latex"], c) for s, c in r_groups)
    right = " + ".join(_term(M.get(s)["latex"], c) for s, c in p_groups)
    cond = conditions or {}
    over = cond.get("catalyst", {}).get("formula") if cond.get("catalyst") else cond.get("text")
    under = cond.get("under")
    if cond.get("catalyst") and cond.get("text"):
        over = cond["catalyst"]["formula"]
        under = under or cond["text"]
    arrow_body = r"\rightleftharpoons" if cond.get("reversible") else r"\longrightarrow"
    if over and under:
        arrow = rf"\underset{{\text{{{under}}}}}{{\overset{{\text{{{over}}}}}{{{arrow_body}}}}}"
    elif over:
        if cond.get("reversible"):
            arrow = rf"\overset{{\text{{{over}}}}}{{{arrow_body}}}"
        else:
            arrow = rf"\xrightarrow{{\text{{{over}}}}}"
    else:
        arrow = arrow_body
    return f"{left} \\;{arrow}\\; {right}"


# ===========================================================================
# 7) 引擎选择 + 标签 + UI 文案
# ===========================================================================
def resolve_engine(spec):
    eng = spec.get("meta", {}).get("engine", "auto")
    if eng in ("morph", "mechanism"):
        return eng
    if spec.get("fragments") or spec.get("meta", {}).get("category") == "organic":
        return "mechanism"
    return "morph"


def _labels(atoms, r_inst, p_inst):
    """每个分子实例一个浮动标签；锚定到其原子集合的质心。"""
    out = []
    for side, insts, key in (("reactant", r_inst, "rmol"), ("product", p_inst, "pmol")):
        for it in insts:
            ids = [a["id"] for a in atoms if a.get(key) == it["id"]]
            if not ids:
                continue
            mol = M.get(it["species"])
            out.append({
                "id": f"{side}-{it['id']}",
                "text": f"{mol['name']} ({mol['formula']})",
                "color": mol["color"], "phase": side, "atoms": ids,
            })
    return out


UI_ZH = {
    "reactants": "反应物", "products": "产物", "progress": "反应进度",
    "play": "自动演示", "pause": "暂停演示", "reset": "复位",
    "prev": "上一步", "next": "下一步",
    "hint": "拖动滑块观察化学键的断裂、原子重组与守恒，或点击上方步骤跳转。",
    "drag": "拖拽旋转 · 滚轮缩放 · 右键平移",
    "legend": "原子图例", "conservation": "原子守恒", "energy": "能量·反应进程",
    "broken": "断裂的键", "formed": "新生成的键",
    "labels": "标签", "labelsHint": "显示 / 隐藏分子标签",
}
UI_EN = {
    "reactants": "Reactants", "products": "Products", "progress": "Reaction progress",
    "play": "Auto play", "pause": "Pause", "reset": "Reset",
    "prev": "Prev", "next": "Next",
    "hint": "Drag the slider to watch bonds break, atoms recombine and mass conserve, or click a step.",
    "drag": "Drag to rotate · scroll to zoom · right-drag to pan",
    "legend": "Atom legend", "conservation": "Atom conservation", "energy": "Energy · progress",
    "broken": "Bonds broken", "formed": "Bonds formed",
    "labels": "Labels", "labelsHint": "Show / hide molecule labels",
}


# ===========================================================================
# 8) 顶层：assemble_data(spec) → 注入模板的 data
# ===========================================================================
def assemble_data(spec):
    meta = dict(spec.get("meta", {}))
    lang = meta.get("language", "zh-CN")
    is_en = str(lang).lower().startswith("en")

    if "atoms" in spec:                       # 低层（机理）
        atoms, before, after, r_inst, p_inst = resolve_low_level(spec)
    else:                                     # 高层（species + atom_map）
        atoms, before, after, r_inst, p_inst = resolve_high_level(spec)

    verify_conservation(atoms, before, after)
    broken, formed, kept = bond_diff(before, after)

    # 守恒计数：排除催化剂原子（催化剂循环再生、不计入反应物/产物配平）
    cat_frags = {f["id"] for f in spec.get("fragments", []) if f.get("catalyst")}
    counted = [a for a in atoms if a.get("frag") not in cat_frags]
    counts = element_counts(counted)

    # 图例：出现过的元素（按原子顺序），带本地化名称
    legend = [{"el": el, "color": M.element_color(el),
               "name": M.ELEMENTS.get(el, {}).get("en" if is_en else "zh", el)}
              for el in counts]

    r_groups, p_groups = _grouped(r_inst), _grouped(p_inst)
    # —— sympy 配平校验：实例计数必须与配平系数一致（去重物种）——
    r_species = [s for s, _ in r_groups]
    p_species = [s for s, _ in p_groups]
    try:
        rc, pc = balanced_coefficients(r_species, p_species)
        got = {s: c for s, c in r_groups} | {s: c for s, c in p_groups}
        want = {s: c for s, c in zip(r_species, rc)} | {s: c for s, c in zip(p_species, pc)}
        if got != want:
            raise AssertionError(f"实例计数 {got} 与 sympy 配平 {want} 不一致")
    except (ValueError, KeyError):
        pass  # 配平不唯一，或物种不在库内（机理路径由作者用 meta.equation 保证）

    eq = meta.get("equation") or equation_latex(r_groups, p_groups, spec.get("conditions"))

    engine = resolve_engine(spec)
    data = {
        "meta": {
            "title": meta.get("title", ""),
            "subtitle": meta.get("subtitle", ""),
            "language": lang,
            "category": meta.get("category", "junior"),
            "accent": meta.get("accent", "indigo"),
            "engine": engine,
            "equation": eq,
        },
        "conditions": spec.get("conditions", {}),
        "atoms": atoms,
        "bonds": {"before": before, "after": after,
                  "broken": broken, "formed": formed, "kept": kept},
        "labels": spec.get("labels") or _labels(atoms, r_inst, p_inst),
        "elementCounts": counts,
        "legend": legend,
        "steps": spec.get("steps", []),
        "fragments": spec.get("fragments", []),
        "energy": spec.get("energy"),
        "electrons": spec.get("electrons", []),
        # 初中化学扩展（可选）：金属活动性顺序条 + 溶液计算控制台
        "activity": spec.get("activity"),
        "solution": spec.get("solution"),
        "ui": UI_EN if is_en else UI_ZH,
    }
    return data


# ===========================================================================
# 7b) 金属活动性顺序 + 溶液计算（初中化学扩展，sympy 有理数精确）
# ===========================================================================
ACTIVITY_SERIES = ["K", "Ca", "Na", "Mg", "Al", "Zn", "Fe", "Sn", "Pb",
                   "H", "Cu", "Hg", "Ag", "Pt", "Au"]


def _q(x):
    """任意数字/字符串 → sympy Rational（20 → 20，'0.2' → 1/5）。"""
    try:
        return sp.Rational(str(x))
    except (sp.SympifyError, ValueError, TypeError):
        return sp.nsimplify(x, rational=True)


def _norm_frac(w):
    """质量分数归一：>1 视为百分数（20 → 1/5），≤1 视为分数（0.2 → 1/5）。"""
    v = _q(w)
    if v > 1:
        v = v / 100
    if v <= 0 or v > 1:
        raise ValueError(f"质量分数必须落在 (0, 1]，收到 {w}")
    return sp.simplify(v)


def activity_rank(sym):
    """符号在活动性顺序表中的名次，越小越活泼；H 为非金属参照位。"""
    try:
        return ACTIVITY_SERIES.index(sym)
    except ValueError:
        raise ValueError(f"未知金属/氢 {sym}；活动性顺序表：{' '.join(ACTIVITY_SERIES)}")


def activity_judge(a, b):
    """判断 a 能否把 b 从其盐溶液中置换出来（a 在 b 之前）。
    K/Ca/Na 例外：投入盐溶液先与水剧烈反应，不能置换出金属。
    b == "H" 时按“氢前/氢后金属、能否与稀酸反应放出氢气”措辞。"""
    ri, rj = activity_rank(a), activity_rank(b)
    acid = (b == "H")
    if acid:
        if a in ("K", "Ca", "Na"):
            can, note = False, f"{a} 太活泼，放入酸中先与水剧烈反应，不能平稳置换出氢气"
        elif ri < rj:
            can, note = True, f"{a} 排在 (H) 之前，属于氢前金属，能与稀酸反应放出氢气"
        else:
            can, note = False, f"{a} 排在 (H) 之后，属于氢后金属，不能与稀酸反应放出氢气"
    elif a in ("K", "Ca", "Na") and ri < rj:
        can, note = False, f"{a} 太活泼，放入盐溶液先与水反应，不能置换出 {b}"
    elif ri < rj:
        can, note = True, f"{a} 排在 {b} 之前，能把 {b} 从其盐溶液中置换出来"
    elif ri == rj:
        can, note = False, f"{a} 与 {b} 活动性相同，不能发生置换"
    else:
        can, note = False, f"{b} 排在 {a} 之前，{a} 不能把 {b} 从其盐溶液中置换出来"
    return {"left": a, "right": b, "rankLeft": ri, "rankRight": rj,
            "can": can, "note": note}


def activity_strip(a, b=None):
    """活动性顺序条数据：highlights 标出参与金属，note 给出判断结论。"""
    b = b or "H"
    j = activity_judge(a, b)
    return {"series": list(ACTIVITY_SERIES), "left": a, "right": b,
            "highlight": [a, b], "can": j["can"], "note": j["note"],
            "rankLeft": j["rankLeft"], "rankRight": j["rankRight"]}


def mass_fraction(m_solute, m_solvent):
    """溶质质量分数 w = m质 / m液 × 100%，m液 = m质 + m剂。"""
    ms, mw = _q(m_solute), _q(m_solvent)
    if ms < 0 or mw <= 0:
        raise ValueError("溶质质量须非负、溶剂质量须为正")
    w = sp.simplify(ms / (ms + mw))
    return {"solute": ms, "solvent": mw, "solution": ms + mw,
            "fraction": w, "percent": sp.simplify(w * 100)}


def prepare_solution(m_solution, w_target):
    """配制溶液：m质 = m液 × w，m剂 = m液 − m质。"""
    mt, w = _q(m_solution), _norm_frac(w_target)
    ms = sp.simplify(mt * w)
    return {"solution": mt, "fraction": w, "percent": sp.simplify(w * 100),
            "solute": ms, "solvent": sp.simplify(mt - ms)}


def dilution(m_conc, w_conc, w_target):
    """稀释：m₁w₁ = m₂w₂；加水量 = m₂ − m₁，溶质质量稀释前后不变。"""
    m1, w1, w2 = _q(m_conc), _norm_frac(w_conc), _norm_frac(w_target)
    if w1 < w2:
        raise ValueError(f"稀释要求 w₁ ≥ w₂（浓度变稀），收到 {w1} < {w2}")
    m2 = sp.simplify(m1 * w1 / w2)
    return {"m1": m1, "w1": w1, "m2": m2, "w2": w2,
            "solute": sp.simplify(m1 * w1), "water": sp.simplify(m2 - m1),
            "percent1": sp.simplify(w1 * 100), "percent2": sp.simplify(w2 * 100)}


def saturation_fraction(S):
    """某温度溶解度 S（g/100g 水）→ 饱和溶液质量分数 = S/(100+S)。"""
    S = _q(S)
    if S <= 0:
        raise ValueError("溶解度须为正")
    w = sp.simplify(S / (100 + S))
    return {"S": S, "fraction": w, "percent": sp.simplify(w * 100),
            "solvent": sp.Integer(100), "solution": sp.Integer(100) + S}


# ===========================================================================
# 自检
# ===========================================================================
def _selfcheck():
    # 甲烷燃烧：CH4 + 2 O2 -> CO2 + 2 H2O
    rc, pc = balanced_coefficients(["CH4", "O2"], ["CO2", "H2O"])
    assert (rc, pc) == ([1, 2], [1, 2]), (rc, pc)

    # 氢气燃烧：2 H2 + O2 -> 2 H2O
    rc, pc = balanced_coefficients(["H2", "O2"], ["H2O"])
    assert (rc, pc) == ([2, 1], [2]), (rc, pc)

    # 钠与氯：2 Na + Cl2 -> 2 NaCl
    rc, pc = balanced_coefficients(["Na", "Cl2"], ["NaCl"])
    assert (rc, pc) == ([2, 1], [2]), (rc, pc)

    # 一个最小高层反应：H2 + Cl2 -> 2 HCl 不在库内，改测电解水分解
    spec = {
        "meta": {"title": "电解水", "category": "junior", "engine": "morph"},
        "conditions": {"text": "通电", "under": "电解"},
        "reactants": [{"species": "H2O", "count": 2}],
        "products": [{"species": "H2", "count": 2}, {"species": "O2", "count": 1}],
        "atom_map": [
            ["H2O#1.A", "O2#1.Oa"], ["H2O#2.A", "O2#1.Ob"],
            ["H2O#1.Ha", "H2#1.Ha"], ["H2O#1.Hb", "H2#1.Hb"],
            ["H2O#2.Ha", "H2#2.Ha"], ["H2O#2.Hb", "H2#2.Hb"],
        ],
        "steps": [{"title": "通电前", "html": "两个水分子"},
                  {"title": "电解", "html": "O-H 键断裂"},
                  {"title": "产物", "html": "生成氢气与氧气"}],
    }
    data = assemble_data(spec)
    assert data["elementCounts"] == {"O": 2, "H": 4}, data["elementCounts"]
    assert len(data["atoms"]) == 6
    # 断键：4 根 O-H；成键：2 根 H-H + 1 根 O=O
    assert len(data["bonds"]["broken"]) == 4, data["bonds"]["broken"]
    assert len(data["bonds"]["formed"]) == 3, data["bonds"]["formed"]
    assert data["meta"]["engine"] == "morph"
    # —— 活动性顺序 ——
    assert activity_rank("K") == 0 and activity_rank("Au") == 14
    assert activity_judge("Fe", "Cu")["can"] is True
    assert activity_judge("Cu", "Fe")["can"] is False
    assert activity_judge("Zn", "H")["can"] is True       # Zn 能置换酸中氢
    assert "氢前金属" in activity_judge("Zn", "H")["note"]
    assert "氢后金属" in activity_judge("Cu", "H")["note"]
    assert activity_judge("Cu", "H")["can"] is False      # Cu 不与稀酸反应
    assert activity_judge("Na", "Cu")["can"] is False     # K/Ca/Na 先与水反应
    strip = activity_strip("Fe", "Cu")
    assert strip["can"] and strip["highlight"] == ["Fe", "Cu"]

    # —— 溶液计算 ——
    mf = mass_fraction(16, 84)
    assert mf["solution"] == 100 and mf["fraction"] == sp.Rational(4, 25)
    assert mf["percent"] == 16, mf["percent"]
    pr = prepare_solution(100, 16)
    assert (pr["solute"], pr["solvent"]) == (16, 84), pr
    dl = dilution(50, 20, 5)            # 50 g 20% 稀释到 5%：加水 150 g
    assert dl["m2"] == 200 and dl["water"] == 150 and dl["solute"] == 10, dl
    sf = saturation_fraction(36)        # 20 °C NaCl 溶解度 36 g → 26.47%
    assert sf["solution"] == 136 and sf["percent"] == sp.Rational(450, 17), sf

    print("reaction_kernel self-check OK ✓  rdkit_available =", rdkit_available())
    print("  electrolysis equation:", data["meta"]["equation"])


if __name__ == "__main__":
    _selfcheck()
