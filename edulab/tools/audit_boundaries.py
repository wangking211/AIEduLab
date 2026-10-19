#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_boundaries.py —— 跨技能「边界体检」：触发词冲突、边界声明、悬空引用。

33 个技能是快速扩张出来的，触发词与边界声明很可能已经互相打架。
本工具把这些检查**机器化**，以便复跑：

  1. 触发词冲突：同一个词被 ≥2 个技能声明（这是「选错技能」的直接来源）。
     进一步区分：该冲突是否已被**边界声明**消解（例如 A 的不该用段里写了「用 B」）。
  2. 边界声明：每个技能是否都有「什么时候不该用本技能」段。
  3. 悬空引用：边界段里提到的技能名是否真实存在。
  4. 反向可达：A 指向 B 时，B 的 description 里是否也提到 A（信息性，不报错）。
  5. 题型 key 跨技能重名（信息性）。

用法：
    python tools/audit_boundaries.py            # 打印报告
    python tools/audit_boundaries.py --strict   # 有硬错误时退出码非零
"""

import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent      # 仓库根
SKILLS = ROOT / "edulab" / "skills"

# 触发词列表里允许的分隔符（中英文逗号都见得到）
SPLIT = re.compile(r"[,，、]\s*")
SKILLNAME = re.compile(r"\bedu-[a-z][a-z0-9-]*\b")
# 「不该用」段里指向替代技能的行，例如「—— 用 `edu-vector`」/「用 edu-cs」
REDIRECT = re.compile(r"`?(edu-[a-z][a-z0-9-]*)`?")


def read(p):
    return io.open(p, encoding="utf-8", newline="").read()


def frontmatter(text):
    """取出 SKILL.md 的 frontmatter 文本（第一个 --- 与第二个 --- 之间）。"""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end > 0 else ""


def parse_description(fm):
    """把 description 的块标量拼成一行。"""
    lines = fm.splitlines()
    out, grab = [], False
    for ln in lines:
        if ln.startswith("description:"):
            grab = True
            rest = ln.split(":", 1)[1].strip()
            if rest and rest not in (">-", ">", "|", "|-"):
                out.append(rest)
            continue
        if grab:
            if ln and not ln.startswith((" ", "\t")):
                break
            out.append(ln.strip())
    return " ".join(x for x in out if x)


def parse_triggers(desc):
    """返回 (中文触发词集合, 英文触发词集合)。"""
    zh, en = set(), set()
    i = desc.find("触发词：")
    if i < 0:
        return zh, en
    body = desc[i + len("触发词："):]
    j = body.find(";")
    if j < 0:
        j = body.find("；")
    if j < 0:
        # 没有分号：整段按中文处理
        for w in SPLIT.split(body):
            w = w.strip().strip("。.")
            if w:
                zh.add(w)
        return zh, en
    for w in SPLIT.split(body[:j]):
        w = w.strip().strip("。.")
        if w:
            zh.add(w)
    tail = body[j + 1:]
    for w in SPLIT.split(tail):
        w = w.strip().strip("。.").strip()
        if w and not re.search(r"[\u4e00-\u9fff]", w):
            en.add(w.lower())
    return zh, en


def not_use_section(text):
    """取出「什么时候不该用本技能」之后到下一个二级标题之间的正文。"""
    m = re.search(r"^##\s*什么时候不该用本技能\s*$", text, re.M)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(r"^##\s", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def load_skills():
    out = {}
    for d in sorted(SKILLS.iterdir()):
        if not d.is_dir():
            continue
        f = d / "SKILL.md"
        if not f.exists():
            out[d.name] = {"dir": d, "text": "", "desc": "", "zh": set(), "en": set(),
                           "notuse": None, "missing": True}
            continue
        text = read(f)
        desc = parse_description(frontmatter(text))
        zh, en = parse_triggers(desc)
        out[d.name] = {"dir": d, "text": text, "desc": desc, "zh": zh, "en": en,
                       "notuse": not_use_section(text), "missing": False}
    return out


def main(argv):
    strict = "--strict" in argv
    skills = load_skills()
    names = set(skills)

    hard, warn = [], []

    print(f"技能总数：{len(skills)}\n")

    # ---- 1. 必备段 ----
    print("① 「什么时候不该用本技能」段")
    no_section = [n for n, s in skills.items() if s["missing"] or s["notuse"] is None]
    for n in no_section:
        print(f"   ✗ {n} 缺少该段")
        hard.append(f"{n} 缺少「什么时候不该用本技能」段")
    if not no_section:
        print("   ✓ 全部技能都有该段")
    print()

    # ---- 2. 触发词覆盖 ----
    print("② 触发词覆盖")
    no_trig = [n for n, s in skills.items() if not s["zh"] and not s["en"]]
    for n in no_trig:
        print(f"   · {n} 没有触发词（{len(skills[n]['zh'])} 中 / {len(skills[n]['en'])} 英）")
    have = len(skills) - len(no_trig)
    tot_zh = sum(len(s["zh"]) for s in skills.values())
    tot_en = sum(len(s["en"]) for s in skills.values())
    print(f"   {have}/{len(skills)} 个技能有触发词，共 {tot_zh} 个中文 + {tot_en} 个英文\n")

    # ---- 3. 触发词冲突 ----
    index = {}
    for n, s in skills.items():
        for w in (s["zh"] | s["en"]):
            index.setdefault(w, set()).add(n)
    collisions = {w: sorted(v) for w, v in index.items() if len(v) > 1}

    def disambiguated(a, b):
        """A 的「不该用」段里是否明确指向 B（或反之）。"""
        ta = (skills[a]["notuse"] or "")
        tb = (skills[b]["notuse"] or "")
        return (b in ta) or (a in tb)

    resolved, unresolved = [], []
    for w, owners in sorted(collisions.items()):
        pairs = [(owners[i], owners[j])
                 for i in range(len(owners)) for j in range(i + 1, len(owners))]
        if all(disambiguated(a, b) for a, b in pairs):
            resolved.append((w, owners))
        else:
            unresolved.append((w, owners))

    print("③ 触发词冲突（同一词被多个技能声明）")
    print(f"   冲突词共 {len(collisions)} 个：已由边界声明消解 {len(resolved)}，"
          f"未消解 {len(unresolved)}")
    for w, owners in unresolved:
        print(f"   ⚠ 「{w}」→ {', '.join(owners)}")
        warn.append(f"触发词冲突未消解：「{w}」{owners}")
    print()

    # ---- 4. 悬空引用 ----
    print("④ 边界声明里的悬空引用（指向不存在的技能）")
    dangling = []
    for n, s in skills.items():
        body = s["notuse"] or ""
        for ref in set(SKILLNAME.findall(body)):
            if ref not in names and ref != n:
                dangling.append((n, ref))
                print(f"   ✗ {n} 指向不存在的 {ref}")
    if not dangling:
        print("   ✓ 无悬空引用")
    else:
        for n, ref in dangling:
            hard.append(f"{n} 的边界段指向不存在的 {ref}")
    print()

    # ---- 5. 反向可达（信息性） ----
    print("⑤ 边界声明的反向可达（信息性：A 指向 B 时 B 是否也提到 A）")
    oneway = []
    for n, s in skills.items():
        for ref in sorted(set(SKILLNAME.findall(s["notuse"] or ""))):
            if ref in names and ref != n:
                if n not in (skills[ref]["desc"] + (skills[ref]["notuse"] or "")):
                    oneway.append((n, ref))
    if not oneway:
        print("   ✓ 所有边界声明都是双向可查的")
    else:
        print(f"   · {len(oneway)} 条单向（不一定是问题，仅供人工复核）：")
        for a, b in oneway:
            print(f"     {a} → {b}")
    print()

    # ---- 6. 题型 key 跨技能重名（信息性） ----
    print("⑥ 题型 key 跨技能重名（信息性）")
    keymap = {}
    for n, s in skills.items():
        g = s["dir"] / "scripts" / "generate.py"
        if not g.exists():
            continue
        src = read(g)
        m = re.search(r"^REGISTRY\s*=\s*\{(.*?)^\}", src, re.M | re.S)
        if not m:
            continue
        for k in re.findall(r'"([a-z0-9_]+)"\s*:', m.group(1)):
            keymap.setdefault(k, []).append(n)
    dup = {k: v for k, v in keymap.items() if len(v) > 1}
    if not dup:
        print("   ✓ 无重名")
    else:
        for k, v in sorted(dup.items()):
            print(f"   · 「{k}」出现在：{', '.join(v)}")
    print()

    # ---- 汇总 ----
    print("=" * 60)
    print(f"硬错误 {len(hard)} 条，警告 {len(warn)} 条")
    for h in hard:
        print(f"   ✗ {h}")
    if not hard:
        print("   ✓ 无硬错误")
    if strict and hard:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
