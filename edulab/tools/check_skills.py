#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_skills.py —— 技能与根级产品的一致性 / 可复现性闸门。

覆盖 `edulab/skills/` 下的全部技能，外加仓库根的独立产品（`mental-models`）——
后者不走技能安装，但同样是「内核 + 模板 + 产物」这套约定，纳入闸门才有人把关。

跑三件事：

1. **可运行**：每项的 `scripts/generate.py all <临时目录>` 必须成功退出。
2. **可复现**：用两个不同的 `PYTHONHASHSEED` 各生成一遍，产物必须**逐字节一致**。
   这条专治「拿 set 的迭代顺序生成内容」的 bug —— 比如 edu-cs 的 prim_mst 曾经
   `for u in in_tree:` 遍历字符串集合，同一份代码两次运行产出的 inTree 顺序不同，
   单进程自测完全看不出来，只有换哈希种子才会暴露。
3. **无漂移**：与 `skills-baseline.json` 里的内容哈希逐字节比对。改了 kernel 或模板
   导致产物变化时会失败；确认新产物正确后用 `--update` 刷新基线。

用法：
    python edulab/tools/check_skills.py            # 闸门（差异即失败）
    python edulab/tools/check_skills.py --update   # 刷新基线（仅在确认产物正确后）
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SKILLS_DIR = ROOT / "edulab" / "skills"
BASELINE = HERE / "skills-baseline.json"
TMP = Path(os.environ.get("TEMP", "/tmp")) / "opencode" / "skillcheck"

# 闸门覆盖：edulab/skills/ 下的技能，加上仓库根的独立产品。
# mental-models 不走技能安装（真源只有 edulab/skills/ 一处），但它同样是
# 「sympy 内核 + 模板 + 产物」这套约定的产物，没有闸门就等于改动无人把关。
ROOT_PRODUCTS = [ROOT / "mental-models"]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def skill_dirs():
    """返回 [(名字, 目录)]，按名字排序。"""
    out = [(d.name, d) for d in SKILLS_DIR.iterdir()
           if (d / "scripts" / "generate.py").exists()]
    out += [(d.name, d) for d in ROOT_PRODUCTS
            if (d / "scripts" / "generate.py").exists()]
    return sorted(out)


def run_all(sdir, out_dir, hash_seed=None):
    """跑 `<产品>/scripts/generate.py all <out_dir>`，返回 (exit_code, {相对路径: sha256})。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    if hash_seed is not None:
        env["PYTHONHASHSEED"] = str(hash_seed)
    r = subprocess.run(
        [sys.executable, str(sdir / "scripts" / "generate.py"), "all", str(out_dir)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(sdir), env=env)
    got = {p.relative_to(out_dir).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in out_dir.rglob("*") if p.is_file()}
    return r, got


def main(argv):
    update = "--update" in argv
    items = skill_dirs()
    print(f"闸门覆盖 {len(items)} 项：{', '.join(n for n, _ in items)}\n")

    # 0) 模板一致性：各家族的 board.html 必须与共享骨架 + 各自片段一致
    import subprocess as _sp
    r = _sp.run([sys.executable, str(HERE / "compose_templates.py"), "--check"],
                capture_output=True, text=True, encoding="utf-8", errors="replace")
    tpl_ok = r.returncode == 0
    print(f"  {'✓' if tpl_ok else '✗'} 模板一致性（shared/board 各家族骨架 + 片段）")
    if not tpl_ok:
        for ln in (r.stdout or "").splitlines()[-4:]:
            print(f"      {ln}")
    print()

    baseline = {}
    if BASELINE.exists():
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))

    failures, fresh = [], {}
    for s, sdir in items:
        base = TMP / s
        for sub in ("a", "b"):
            d = base / sub
            if d.exists():
                for p in sorted(d.rglob("*"), reverse=True):
                    p.unlink() if p.is_file() else p.rmdir()
        r1, h1 = run_all(sdir, base / "a", hash_seed=1)
        r2, h2 = run_all(sdir, base / "b", hash_seed=2)
        fresh[s] = h1

        if r1.returncode != 0 or r2.returncode != 0:
            tail = ((r1.stderr or "") + (r2.stderr or "")).strip().splitlines()[-4:]
            failures.append((s, "运行失败", tail))
            print(f"  ✗ {s:24s} 运行失败 exit={r1.returncode}/{r2.returncode}")
            continue

        nondet = [k for k in set(h1) | set(h2) if h1.get(k) != h2.get(k)]
        # 新增项**没有基线记录时不能默认通过**：否则加一个新技能闸门就自动对它
        # 变绿，等于形同虚设。缺少记录视为未通过，提示用 --update 建立。
        nobase = s not in baseline
        drift = ([] if nobase else
                 [k for k in set(h1) | set(baseline[s]) if h1.get(k) != baseline[s].get(k)])

        flags = []
        if nondet:
            flags.append(f"不可复现 {nondet}")
        if nobase:
            flags.append(f"无基线记录（{len(h1)} 个产物，需 --update 建立）")
        elif drift:
            flags.append(f"与基线不同 {drift}")
        print(f"  {'✗' if flags else '✓'} {s:24s} {len(h1):3d} 个产物"
              + ("   " + "；".join(flags) if flags else ""))
        for f in flags:
            failures.append((s, f, []))

    print()
    if update:
        BASELINE.write_text(json.dumps(fresh, ensure_ascii=False, indent=1, sort_keys=True),
                            encoding="utf-8")
        print(f"✓ 基线已刷新：{BASELINE.relative_to(ROOT).as_posix()}（{len(fresh)} 个技能）")
        return 0
    if failures or not tpl_ok:
        if failures:
            print(f"✗ {len(failures)} 项未通过")
            for s, why, tail in failures:
                print(f"    {s}: {why}")
                for ln in tail:
                    print(f"      | {ln}")
        if not tpl_ok:
            print("✗ 模板与共享骨架不一致")
        print("\n  若确认新产物正确，用 `--update` 刷新基线；模板用 compose_templates.py 重新组装。")
        return 1
    print(f"✓ 全部 {len(items)} 项：可运行、可复现、与基线一致；模板与骨架一致")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
