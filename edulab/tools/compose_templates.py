#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compose_templates.py —— 把「共享骨架 + 各自片段」组装成技能的 template/board.html。

背景
----
Family A 的三个技能（analytic-geometry / plane-geometry / function-derivative）
的模板有约 1600 行是重复的：三份文件 90% 相同，差异全是「在若干位置插入自己的块」
加几处单行改名。手工维护三份的代价是改一处要同步三处，漏一处就漂移。

模型
----
    edulab/shared/board/shell.html          唯一骨架；槽位写成独占一行的 {{slot:name}}
    edulab/shared/board/parts/<name>.html   该槽位的「base 版本」（= analytic 的内容）
    <技能>/template/parts/<name>.html        该技能自己的版本

解析规则（刻意做成零配置、可预测）：

    槽位内容 =   该技能自己的 parts/<name>.html
              若不存在 → shared/board/parts/<name>.html（即 base 版本）

所以：
  · analytic-geometry 是 base，**一个片段文件都不需要**；
  · plane / function 只存自己与 base 不同的那些槽位；
  · 新增同族技能时，把 shell 复制过去、按需补几个片段即可。

产物 `template/board.html` **提交进仓库**，技能仍然自包含
（`generate.py` 只读技能自己的 template/，不依赖 shared/board/）。

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
SHELL = ROOT / "edulab" / "shared" / "board" / "shell.html"
SHARED_PARTS = ROOT / "edulab" / "shared" / "board" / "parts"

# 使用该骨架的技能（新增同族技能时加到这里）
USERS = ["edu-analytic-geometry", "edu-plane-geometry", "edu-function-derivative"]

SLOT_LINE = re.compile(r"^\{\{slot:([A-Za-z0-9_]+)\}\}\r?\n?$")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def read(path):
    """保留行尾读取（骨架与片段都是 CRLF）。"""
    return path.read_text(encoding="utf-8", newline="")


def compose(skill_dir, shell_text):
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
            shared = SHARED_PARTS / f"{name}.html"
            if not shared.exists():
                unknown.append(name)
                continue
            out.append(read(shared))
    if unknown:
        raise SystemExit(f"✗ 槽位在 shared/board/parts 里找不到 base 版本：{sorted(set(unknown))}")
    return "".join(out)


def main(argv):
    check = "--check" in argv
    if not SHELL.exists():
        raise SystemExit(f"✗ 骨架不存在：{SHELL}")
    shell_text = read(SHELL)
    slots = set(SLOT_LINE.match(l).group(1)
                for l in shell_text.splitlines(keepends=True) if SLOT_LINE.match(l))
    print(f"骨架 {SHELL.relative_to(ROOT).as_posix()}：{len(slots)} 个槽位")

    bad = []
    for s in USERS:
        d = SKILLS / s
        target = d / "template" / "board.html"
        html = compose(d, shell_text)
        if check:
            cur = read(target) if target.exists() else None
            mark = "✓" if cur == html else "✗"
            if cur != html:
                bad.append(s)
            print(f"  {mark} {s:26s} 产物 {len(html.splitlines()):4d} 行")
        else:
            target.write_text(html, encoding="utf-8", newline="")
            print(f"  ✓ {s:26s} 写出 {len(html.splitlines()):4d} 行")
    if check and bad:
        print(f"\n✗ {len(bad)} 个技能的 template/board.html 与骨架/片段不一致：{bad}")
        print("   用 `python edulab/tools/compose_templates.py` 重新组装。")
        return 1
    if check:
        print("\n✓ 三个技能的模板都与骨架 + 片段一致")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
