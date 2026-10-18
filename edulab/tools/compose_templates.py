#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compose_templates.py —— 把「共享骨架 + 各自片段」组装成技能的 template/board.html。

背景
----
若干同族技能的模板是「复制一份再各自改」的产物，重复率很高、改一处要同步多处，
漏一处就漂移。这里把共用部分抽成唯一骨架，差异留成槽位。

两个家族
--------
    geom-fn   解析几何 / 平面几何 / 函数与导数      差异全是「在若干位置插入自己的块」
    seq-phys  数列与三角 / 初中物理 / 高中物理      差异收敛到 8 个槽位

模型
----
    edulab/shared/board/<家族>/shell.html         唯一骨架；槽位写成独占一行的 {{slot:name}}
    edulab/shared/board/<家族>/parts/<name>.html  该槽位的「base 版本」
    <技能>/template/parts/<name>.html             该技能自己的版本

解析规则（刻意做成零配置、可预测）：

    槽位内容 =   该技能自己的 parts/<name>.html
              若不存在 → <家族>/parts/<name>.html（即 base 版本）

所以 base 技能（geom-fn 的 analytic-geometry、seq-phys 的 math-sequences）
**一个片段文件都不需要**；其它技能只存自己与 base 不同的那些槽位。

产物 `template/board.html` **提交进仓库**，技能仍然自包含
（`generate.py` 只读技能自己的 template/，不依赖 shared/board/）。

换行
----
组装结果统一写成 LF。这不会让产物漂移：`skillkit.load_template` 用通用换行读模板
（CRLF→LF），`render_html` 用 `os.linesep` 写产物，所以产物的换行只由操作系统决定，
与模板在盘上的换行无关。而 git 侧 `core.autocrlf=true` 本来就按 LF 入库，
所以这里统一 LF 对仓库内容也无影响。

用法
----
    python edulab/tools/compose_templates.py            # 组装（写回各技能）
    python edulab/tools/compose_templates.py --check     # 只校验产物是否与骨架一致
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SKILLS = ROOT / "edulab" / "skills"
BOARD = ROOT / "edulab" / "shared" / "board"

# 家族 → 使用该骨架的技能（base 技能排第一，它的片段即 base 版本）
FAMILIES = {
    "geom-fn": {
        "desc": "解析几何 / 平面几何 / 函数与导数",
        "users": ["edu-analytic-geometry", "edu-plane-geometry", "edu-function-derivative",
                  "edu-math-junior"],
    },
    "seq-phys": {
        "desc": ("数列与三角 / 初中物理 / 高中物理 / 高中电磁学 / 概率与统计 / 化学计算 / "
                 "自然地理 / 可算的历史 / 经济学 / 平面向量 / 线性代数 / 微分方程 / 信号与系统"),
        "users": ["edu-math-sequences", "edu-physics-junior", "edu-physics-senior",
                  "edu-physics-em", "edu-physics-thermal", "edu-physics-wave-optics",
                  "edu-physics-momentum", "edu-probability", "edu-chem-calc",
                  "edu-geography", "edu-history", "edu-economics", "edu-vector",
                  "edu-linear-algebra", "edu-ode-dynamics", "edu-signals"],
    },
}

SLOT_LINE = re.compile(r"^\{\{slot:([A-Za-z0-9_]+)\}\}\r?\n?$")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def lf(text):
    """统一成 LF（见模块文档「换行」一节）。"""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read(path):
    """读文件并归一化换行，避免骨架/片段里的历史 CRLF 影响产物。"""
    return lf(path.read_text(encoding="utf-8"))


def compose(skill_dir, shell_text, shared_parts):
    """把骨架里的槽位替换成该技能的内容。"""
    out, unknown = [], []
    for line in shell_text.splitlines(keepends=True):
        m = SLOT_LINE.match(line)
        if not m:
            out.append(line)
            continue
        name = m.group(1)
        own = skill_dir / "template" / "parts" / f"{name}.html"
        if own.exists():
            out.append(read(own))
        else:
            shared = shared_parts / f"{name}.html"
            if not shared.exists():
                unknown.append(name)
                continue
            out.append(read(shared))
    if unknown:
        raise SystemExit(f"✗ 槽位在共享 parts 里找不到 base 版本：{sorted(set(unknown))}")
    return "".join(out)


def check_family(fam, cfg, check):
    """组装或校验一个家族，返回 (是否成功, 槽位数)。"""
    shell_path = BOARD / fam / "shell.html"
    shared_parts = BOARD / fam / "parts"
    if not shell_path.exists():
        print(f"  ✗ 骨架不存在：{shell_path.relative_to(ROOT).as_posix()}")
        return False, 0

    shell_text = read(shell_path)
    slots = sorted({SLOT_LINE.match(l).group(1)
                    for l in shell_text.splitlines(keepends=True) if SLOT_LINE.match(l)})
    print(f"骨架 {shell_path.relative_to(ROOT).as_posix()}")
    print(f"  {cfg['desc']}   槽位 {len(slots)} 个：{', '.join(slots)}")

    ok = True
    for s in cfg["users"]:
        d = SKILLS / s
        target = d / "template" / "board.html"
        html = compose(d, shell_text, shared_parts)
        if check:
            cur = read(target) if target.exists() else None
            same = cur == html
            ok &= same
            print(f"  {'✓' if same else '✗'} {s:26s} 产物 {len(html.splitlines()):4d} 行")
        else:
            target.write_text(html, encoding="utf-8", newline="")
            print(f"  ✓ {s:26s} 写出 {len(html.splitlines()):4d} 行")
    return ok, len(slots)


def check_coverage():
    """任何带 template/parts/ 的技能都必须属于某个家族。

    否则那些片段会被静默忽略——正是这套工具要防的「改了一处、别处没跟上」。
    """
    known = {u for c in FAMILIES.values() for u in c["users"]}
    stray = sorted(d.name for d in SKILLS.iterdir()
                   if (d / "template" / "parts").is_dir() and d.name not in known)
    if stray:
        raise SystemExit("✗ 这些技能有 template/parts/ 却不在任何家族里，片段会被忽略："
                         f"{stray}\n   请把它们加进 compose_templates.py 的 FAMILIES。")


def main(argv):
    check = "--check" in argv
    check_coverage()
    bad = []
    for fam, cfg in FAMILIES.items():
        ok, _ = check_family(fam, cfg, check)
        if not ok:
            bad.append(fam)
        print()

    if check and bad:
        print(f"✗ {len(bad)} 个家族的 template/board.html 与骨架/片段不一致：{bad}")
        print("   用 `python edulab/tools/compose_templates.py` 重新组装。")
        return 1
    n = sum(len(c["users"]) for c in FAMILIES.values())
    if check:
        print(f"✓ {n} 个技能的模板都与各自家族的骨架 + 片段一致")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
