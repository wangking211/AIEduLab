#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_skills.py —— 全家族技能的一致性 / 可复现性闸门。

跑三件事：

1. **可运行**：每个技能的 `scripts/generate.py all <临时目录>` 必须成功退出。
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
SKILLS = ROOT / "edulab" / "skills"
BASELINE = HERE / "skills-baseline.json"
TMP = Path(os.environ.get("TEMP", "/tmp")) / "opencode" / "skillcheck"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def skill_names():
    return sorted(d.name for d in SKILLS.iterdir()
                  if (d / "scripts" / "generate.py").exists())


def run_all(skill, out_dir, hash_seed=None):
    """跑 `<技能>/scripts/generate.py all <out_dir>`，返回 (exit_code, {相对路径: sha256})。"""
    out_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    if hash_seed is not None:
        env["PYTHONHASHSEED"] = str(hash_seed)
    r = subprocess.run(
        [sys.executable, str(SKILLS / skill / "scripts" / "generate.py"), "all", str(out_dir)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(SKILLS / skill), env=env)
    got = {p.relative_to(out_dir).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in out_dir.rglob("*") if p.is_file()}
    return r, got


def main(argv):
    update = "--update" in argv
    names = skill_names()
    print(f"技能 {len(names)} 个：{', '.join(names)}\n")

    # 0) 模板一致性：Family A 的 board.html 必须与共享骨架 + 各自片段一致
    import subprocess as _sp
    r = _sp.run([sys.executable, str(HERE / "compose_templates.py"), "--check"],
                capture_output=True, text=True, encoding="utf-8", errors="replace")
    tpl_ok = r.returncode == 0
    print(f"  {'✓' if tpl_ok else '✗'} 模板一致性（shared/board 骨架 + 片段）")
    if not tpl_ok:
        for ln in (r.stdout or "").splitlines()[-4:]:
            print(f"      {ln}")
    print()

    baseline = {}
    if BASELINE.exists():
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))

    failures, fresh = [], {}
    for s in names:
        base = TMP / s
        for sub in ("a", "b"):
            d = base / sub
            if d.exists():
                for p in sorted(d.rglob("*"), reverse=True):
                    p.unlink() if p.is_file() else p.rmdir()
        r1, h1 = run_all(s, base / "a", hash_seed=1)
        r2, h2 = run_all(s, base / "b", hash_seed=2)
        fresh[s] = h1

        if r1.returncode != 0 or r2.returncode != 0:
            tail = ((r1.stderr or "") + (r2.stderr or "")).strip().splitlines()[-4:]
            failures.append((s, "运行失败", tail))
            print(f"  ✗ {s:24s} 运行失败 exit={r1.returncode}/{r2.returncode}")
            continue

        nondet = [k for k in set(h1) | set(h2) if h1.get(k) != h2.get(k)]
        drift = [k for k in set(h1) | set(baseline.get(s, {}))
                 if h1.get(k) != baseline.get(s, {}).get(k)] if s in baseline else []

        flags = []
        if nondet:
            flags.append(f"不可复现 {nondet}")
        if drift:
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
    print(f"✓ 全部 {len(names)} 个技能：可运行、可复现、与基线一致；模板与骨架一致")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
