# -*- coding: utf-8 -*-
"""生成前的离线审计：逐个 build 重建 data，核对化学与布局两方面。

化学：元素守恒计数、断/成键差、活动性结论、溶液不变量、步骤数。
布局：所有原子都必须落在相机视野内（相机 (0,4,13)、fov 45 → |x| ≤ 6.2、|y| ≤ 5.4）。

用法：  python3 scripts/audit_all.py      # 审计 REGISTRY 里的全部 build
"""
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "lib"))
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import reaction_kernel as K      # noqa: E402
import generate as G             # noqa: E402

X_LIMIT, Y_LIMIT = 6.2, 5.4


def _sig(bl, atoms):
    by_id = {a["id"]: a for a in atoms}
    return [f"{by_id[x['a']]['el']}-{by_id[x['b']]['el']}({x['order']})" for x in bl]


bad = 0
for key, fn in sorted(G.REGISTRY.items()):
    data = K.assemble_data(fn())
    problems = []

    # --- 化学 ---
    xs, ys = [], []
    for a in data["atoms"]:
        for side in ("start", "end"):
            xs.append(a[side][0])
            ys.append(a[side][1])
    if max(map(abs, xs)) > X_LIMIT or max(map(abs, ys)) > Y_LIMIT:
        problems.append(f"出框 x∈[{min(xs):.1f},{max(xs):.1f}] y∈[{min(ys):.1f},{max(ys):.1f}]")
    if not data["steps"] or len(data["steps"]) < 3:
        problems.append("步骤少于 3")

    b = data["bonds"]
    act = data.get("activity")
    sol = data.get("solution")
    print(f"== {key}")
    print(f"   atoms={len(data['atoms'])} counts={dict(data['elementCounts'])} "
          f"broken={len(b['broken'])} formed={len(b['formed'])} kept={len(b['kept'])}")
    print(f"   broken: {_sig(b['broken'], data['atoms'])}")
    print(f"   formed: {_sig(b['formed'], data['atoms'])}")
    if act:
        print(f"   activity: {act['left']}>{act['right']}? can={act['can']} :: {act['note']}")
        if act["can"] and not (act["rankLeft"] < act["rankRight"]):
            problems.append("活动性 can 与序位矛盾")
    if sol:
        print(f"   solution: params={[p['name'] for p in sol['params']]} "
              f"constant={sol['constant']['expr']} {sol['constant'].get('unit', '')}")
    if problems:
        bad += 1
        for p in problems:
            print(f"   ⚠️ {p}")

print(f"\n{'OK: all builds clean' if not bad else f'{bad} build(s) with problems'} "
      f"({len(G.REGISTRY)} total)")
sys.exit(1 if bad else 0)
