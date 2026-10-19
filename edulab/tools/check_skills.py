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
4. **文档边界**：每个 SKILL.md 必须有「什么时候不该用本技能」段，且至少两条、必须
   指向替代去向（兄弟技能名，或「直接回答」）。description 决定自动触发，没有边界
   就会在边界案例上乱选；只写「本技能不适合」等于没说。
5. **记号守卫**：`verify_scene` 必须真的会拒绝「直角符号画在 135° 上」「等长记号画在
   不等长线段上」——守卫若被删掉或 try/except 吞掉，跑一遍全部技能不会有任何提示。
6. **出处分级**：`mental-models/data/PROVENANCE.md` 必须与代码一致。每个数值归入
   现算 / 实测 / 假设三类，假设逐条列出。加一个滑块参数就是加一个假设，必须重新
   生成报告 —— 假设可以被加，但不能被默默加。
7. **产物自检**：每个技能生成的 `.html` 都要过一遍 `check_output.py` 的检查项
   （残留模板记号、外链白名单、本地引用断链、渲染残留的 undefined/NaN）。
   哈希只回答「产物变没变」，不回答「产物对不对」。

用法：
    python edulab/tools/check_skills.py            # 闸门（差异即失败）
    python edulab/tools/check_skills.py --update   # 刷新基线（仅在确认产物正确后）
"""

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tokenize
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


DOC_HEADING = "## 什么时候不该用本技能"


def section_body(text, heading):
    """取出 heading 到下一个 `## ` 标题之间的正文。"""
    i = text.find(heading)
    if i < 0:
        return None
    rest = text[i + len(heading):]
    lines = rest.split("\n")
    out = []
    for line in lines[1:]:
        if line.startswith("## "):
            break
        out.append(line)
    return "\n".join(out)


def check_skill_docs(items=None):
    """每个 SKILL.md 必须有「什么时候不该用本技能」段，且给出可执行的替代路径。

    为什么把它做成闸门：SKILL.md 的 description 决定**自动触发**。没有「不该用」
    的边界，路由就会在边界案例上乱选 —— 用户问一道初中杠杆题，结果触发高中物理
    技能，就是这类失败。而只写「本技能不适合」等于没说，必须指向具体去向：
    兄弟技能名，或者「直接回答 / 直接算 / 直接说明」。

    注意扫描范围是 `edulab/skills/*/SKILL.md` **全部**，不是 `skill_dirs()`。
    后者只收录有 `scripts/generate.py` 的技能，视频技能（走另一套流水线）会被漏掉——
    而它们恰恰更需要写清「什么时候不该出视频」。
    """
    bad = []
    targets = sorted(p.parent for p in SKILLS_DIR.glob("*/SKILL.md"))
    for sdir in targets:
        name = sdir.name
        p = sdir / "SKILL.md"
        if not p.exists():
            # 根级产品（mental-models）不走技能安装，没有 SKILL.md 是正常的；
            # 只对它做可运行 / 可复现 / 基线三项检查。
            if sdir.parent != SKILLS_DIR:
                continue
            bad.append((name, "缺 SKILL.md"))
            continue
        body = section_body(p.read_text(encoding="utf-8"), DOC_HEADING)
        if body is None:
            bad.append((name, "缺「什么时候不该用本技能」段"))
            continue
        bullets = [ln for ln in body.split("\n") if ln.startswith("- ")]
        if len(bullets) < 2:
            bad.append((name, f"「不该用」段只有 {len(bullets)} 条，至少 2 条"))
            continue
        joined = "\n".join(bullets)
        has_sibling = "edu-" in joined or "mental-models" in joined
        has_fallback = any(k in joined for k in ("直接回答", "直接算", "直接说明"))
        if not (has_sibling or has_fallback):
            bad.append((name, "「不该用」段没给替代去向（兄弟技能名，或「直接回答」）"))

    bad.extend(check_trigger_routing())
    return bad


# ---- 触发词路由：冲突与悬空引用 ----------------------------------------
# 「选错技能」的直接来源是**同一个触发词被多个技能声明**。只查「有没有边界段」
# 是不够的 —— 两个技能可能各自都写了边界，但**没有指向对方**，路由照样会乱选。
# 所以这里把两件事机器化：
#   ① 触发词冲突是否已被边界声明消解（A 的不该用段里点了 B，或反之）；
#   ② 边界段里提到的技能名是否真实存在（防重命名后留下悬空引用）。

_TRIG_SPLIT = re.compile(r"[,，、]\s*")
_SKILL_NAME = re.compile(r"\bedu-[a-z][a-z0-9-]*\b")


def _parse_triggers(desc):
    """从 description 里抽出 (中文触发词, 英文触发词)。"""
    zh, en = set(), set()
    i = desc.find("触发词：")
    if i < 0:
        return zh, en
    body = desc[i + len("触发词："):]
    j = body.find(";")
    if j < 0:
        j = body.find("；")
    if j < 0:
        for w in _TRIG_SPLIT.split(body):
            w = w.strip().strip("。.")
            if w:
                zh.add(w)
        return zh, en
    for w in _TRIG_SPLIT.split(body[:j]):
        w = w.strip().strip("。.")
        if w:
            zh.add(w)
    for w in _TRIG_SPLIT.split(body[j + 1:]):
        w = w.strip().strip("。.")
        if w and not re.search(r"[\u4e00-\u9fff]", w):
            en.add(w.lower())
    return zh, en


def _description_line(fm):
    """把 description 的块标量拼成一行（跨行短语要拼起来才认得出）。"""
    out, grab = [], False
    for ln in fm.splitlines():
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


def check_trigger_routing():
    """触发词冲突（未消解）与悬空技能引用。"""
    bad = []
    info = {}
    for p in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = p.read_text(encoding="utf-8")
        fm = text[3:text.find("\n---", 3)] if text.startswith("---") else ""
        zh, en = _parse_triggers(_description_line(fm))
        info[p.parent.name] = {
            "trig": zh | en,
            "notuse": section_body(text, DOC_HEADING) or "",
            "desc": _description_line(fm),
        }
    names = set(info)

    # ① 悬空引用
    for n, d in info.items():
        for ref in sorted(set(_SKILL_NAME.findall(d["notuse"]))):
            if ref not in names and ref != n:
                bad.append((n, f"边界段指向不存在的技能 {ref}"))

    # ② 触发词冲突是否已消解
    index = {}
    for n, d in info.items():
        for w in d["trig"]:
            index.setdefault(w, set()).add(n)
    for w, owners in sorted(index.items()):
        if len(owners) < 2:
            continue
        owners = sorted(owners)
        pairs = [(owners[i], owners[j])
                 for i in range(len(owners)) for j in range(i + 1, len(owners))]

        def ok(a, b):
            return (b in info[a]["notuse"]) or (a in info[b]["notuse"])

        un = [(a, b) for a, b in pairs if not ok(a, b)]
        if un:
            bad.append((", ".join(owners),
                        f"触发词「{w}」冲突且未被边界声明消解（{un[0][0]} ↔ {un[0][1]}）"))
    return bad


def brace_literal_check():
    """LaTeX 花括号在**非 f-string** 字符串里不能写双份 —— 但**只限 `\\begin`/`\\end`**。

    只有 f-string 里 `{{ }}` 才表示 `{ }`；隐式拼接里没有 `f` 前缀的那些片段，
    `{{ }}` 会原样进入 LaTeX。

    **为什么只查 `\\begin`/`\\end`**：在浏览器里逐条实测过（KaTeX 0.16.8），
    「组套组」只在环境名这一处失败：
      · `\\begin{{pmatrix}}…\\end{{pmatrix}}` → 抛
        `Expected node of type textord, but got node of type ordgroup`；
      · `\\mathbf{{v}}`、`\\dfrac{{a}}{{b}}`、`\\operatorname{{tr}}`、`x^{{2}}`、
        `\\sqrt{{10}}`、`\\text{{abc}}` → **全部正常**（组套组在这些位置是合法 LaTeX）。
    所以判据必须收窄到实际会出问题的位置，否则会把一批渲染正常的技能误报成坏。

    这条坑已在两个技能上各复发一次（edu-linear-algebra、edu-ode-dynamics），
    所以入闸门。用 tokenize 精确定位字符串字面量，只看非 f-string 的那些。
    """
    bad = []
    for name, d in skill_dirs():
        p = d / "scripts" / "generate.py"
        if not p.exists():
            continue
        src = p.read_text(encoding="utf-8", errors="replace")
        try:
            toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
        except Exception as exc:                     # noqa: BLE001
            bad.append((name, f"tokenize 失败：{exc}"))
            continue
        lines = []
        for t in toks:
            if t.type != tokenize.STRING:
                continue
            s = t.string
            if "f" in re.match(r"[A-Za-z]*", s).group(0).lower():
                continue                             # f-string 里的 {{ }} 是对的
            if "begin{{" in s or "end{{" in s:
                lines.append(t.start[0])
        if lines:
            bad.append((name, f"generate.py 的 \\begin{{\\{{ 位置：第 "
                              f"{', '.join(str(x) for x in lines[:5])} 行"
                              f"{' 等' if len(lines) > 5 else ''}"))
    return bad


def scene_guard_selftest():
    """`verify_scene` 必须真的会拒绝「记号撒谎」的图，否则它只是个摆设。

    这条自检本身也是必需的：守卫挂在 `render_html` 里，一旦有人把它删掉或
    改成 try/except 吞掉，跑一遍全部技能也**不会有任何提示**（图照画）。
    """
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "edulab" / "shared"))
    import skillkit as sk

    cases = []

    # 角 ABC = 135°，却画了直角符号 → 必须拒绝
    bad_right = {"board": {
        "points": {"A": {"xy": [0, 0]}, "B": {"xy": [1, 0]}, "C": {"xy": [2, 1]}},
        "derived": [{"type": "right_angle_mark", "a": "A", "vertex": "B", "b": "C"}],
    }}
    try:
        sk.verify_scene(bad_right)
        cases.append((False, "直角符号画在 135° 上：应拒绝，实际放行"))
    except sk.SceneMarkError:
        cases.append((True, "直角符号画在 135° 上：拒绝"))

    # 两条不等长线段都带 1 道等长记号 → 必须拒绝
    bad_ticks = {"board": {
        "points": {"A": {"xy": [0, 0]}, "B": {"xy": [1, 0]}, "C": {"xy": [0, 2]}},
        "derived": [
            {"type": "segment", "name": "s1", "a": "A", "b": "B", "ticks": 1},
            {"type": "segment", "name": "s2", "a": "A", "b": "C", "ticks": 1},
        ],
    }}
    try:
        sk.verify_scene(bad_ticks)
        cases.append((False, "等长记号画在 1 与 2 上：应拒绝，实际放行"))
    except sk.SceneMarkError:
        cases.append((True, "等长记号画在 1 与 2 上：拒绝"))

    # 记号与坐标一致 → 必须放行（否则守卫会把好图也拦掉）
    good = {"board": {
        "points": {"A": {"xy": [0, 0]}, "B": {"xy": [1, 0]}, "C": {"xy": [1, 1]},
                   "D": {"xy": [0, 1]}},
        "derived": [
            {"type": "right_angle_mark", "a": "A", "vertex": "B", "b": "C"},
            {"type": "segment", "name": "s1", "a": "A", "b": "B", "ticks": 1},
            {"type": "segment", "name": "s2", "a": "C", "b": "D", "ticks": 1},
        ],
    }}
    try:
        sk.verify_scene(good)
        cases.append((True, "记号与坐标一致的图：放行"))
    except sk.SceneMarkError as e:
        cases.append((False, f"记号与坐标一致的图被误拦：{e}"))

    bad = [c for c in cases if not c[0]]
    return (not bad), cases


def artifact_problems(out_dir):
    """对某个技能的产物目录跑一遍 check_output 的检查项（读产物，不读源）。

    技能闸门原本只比对哈希：能发现「产物变了」，但发现不了「产物本来就是坏的」——
    残留记号、白名单外的外链、本地引用断链、渲染残留的 undefined/NaN。
    这些恰恰是源检查看不见的。产物目录是临时目录，所以每次现跑。
    """
    sys.path.insert(0, str(HERE))
    import check_output as CO

    bad = []
    for f in sorted(Path(out_dir).glob("*.html")):
        errs, _warns, _infos = CO.check_file(f, {}, False)
        for code, _where, msg, _fix in errs:
            bad.append(f"{f.name}: {code} {msg}")
    return bad


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

    # 0.5) 视频技能的共享素材（字体等）必须与真源逐字节一致。
    # 这些副本不入库，所以必须由闸门保证「齐全且没被改坏」——字体加载失败是
    # 静默降级（退回系统字体），光看渲染结果很难发现。
    r = _sp.run([sys.executable, str(HERE / "sync_video_assets.py"), "--check"],
                capture_output=True, text=True, encoding="utf-8", errors="replace")
    assets_ok = r.returncode == 0
    print(f"  {'✓' if assets_ok else '✗'} 视频共享素材（与 shared/video 真源一致）")
    if not assets_ok:
        for ln in (r.stdout or "").splitlines()[-4:]:
            print(f"      {ln}")

    # 0.6) 文档边界：每个技能都要说清「什么时候不该用」，并指向替代去向。
    doc_bad = check_skill_docs()
    print(f"  {'✓' if not doc_bad else '✗'} 文档边界（每个技能都有「什么时候不该用本技能」且指向替代）")
    for name, why in doc_bad:
        print(f"      {name}: {why}")

    # 0.7) 记号守卫自检：verify_scene 必须真的会拒绝「记号撒谎」的图。
    guard_ok, guard_cases = scene_guard_selftest()
    print(f"  {'✓' if guard_ok else '✗'} 记号守卫（直角 / 等长记号必须与坐标一致）")
    for ok, desc in guard_cases:
        if not ok:
            print(f"      {desc}")

    # 0.75) LaTeX 环境名：普通字符串里不能写 \begin{{…}}（见 brace_literal_check 的实测证据）
    brace_bad = brace_literal_check()
    print(f"  {'✓' if not brace_bad else '✗'} LaTeX 环境名（普通字符串里不得写 \\begin{{{{…}}}}）")
    for name, why in brace_bad:
        print(f"      {name}: {why}")

    # 0.8) 出处审计：数值分「现算 / 实测 / 假设」，报告必须与代码一致。
    r = _sp.run([sys.executable,
                 str(ROOT / "mental-models" / "lib" / "provenance.py"), "--check"],
                capture_output=True, text=True, encoding="utf-8", errors="replace")
    prov_ok = r.returncode == 0
    print(f"  {'✓' if prov_ok else '✗'} 出处分级（现算 / 实测 / 假设；假设逐条列出）")
    if not prov_ok:
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

        # 记号零盲区：render_html 已把「无法判定」的记号逐行打到 stderr（行首 ?）。
        # 有盲区却让闸门变绿，等于默认「没看见的地方都是对的」—— 那正是 verify_scene
        # 当初静默跳过的病根，只是换了个位置复发。所以盲区必须让闸门变红。
        blind = [ln.strip() for ln in (r1.stderr or "").splitlines()
                 if ln.startswith("[记号守卫]")
                 and ln[len("[记号守卫]"):].lstrip().startswith("?")]

        nondet = [k for k in set(h1) | set(h2) if h1.get(k) != h2.get(k)]
        art = artifact_problems(base / "a")
        # 新增项**没有基线记录时不能默认通过**：否则加一个新技能闸门就自动对它
        # 变绿，等于形同虚设。缺少记录视为未通过，提示用 --update 建立。
        nobase = s not in baseline
        drift = ([] if nobase else
                 [k for k in set(h1) | set(baseline[s]) if h1.get(k) != baseline[s].get(k)])

        flags = []
        if nondet:
            flags.append(f"不可复现 {nondet}")
        if art:
            flags.append(f"产物有问题 {art}")
        if blind:
            flags.append(f"记号有 {len(blind)} 处无法判定（盲区不许静默通过）")
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
    if failures or not tpl_ok or not assets_ok or doc_bad or not guard_ok or not prov_ok \
            or brace_bad:
        if failures:
            print(f"✗ {len(failures)} 项未通过")
            for s, why, tail in failures:
                print(f"    {s}: {why}")
                for ln in tail:
                    print(f"      | {ln}")
        if not tpl_ok:
            print("✗ 模板与共享骨架不一致")
        if not assets_ok:
            print("✗ 视频技能的共享素材与真源不一致")
        if doc_bad:
            print(f"✗ {len(doc_bad)} 个技能的文档边界不完整")
        if not guard_ok:
            print("✗ 记号守卫自检未通过（verify_scene 没在拦截撒谎的记号）")
        if not prov_ok:
            print("✗ 出处分级与代码不一致（有模型的假设/读数变了但报告没重新生成）")
        if brace_bad:
            print(f"✗ {len(brace_bad)} 个技能的 LaTeX 花括号写重了"
                  "（普通字符串里的 {{ }} 会原样进入 LaTeX，KaTeX 会抛错但不报错）")
        print("\n  若确认新产物正确，用 `--update` 刷新基线；"
              "模板用 compose_templates.py、素材用 sync_video_assets.py 重新组装。")
        return 1
    print(f"✓ 全部 {len(items)} 项：可运行、可复现、与基线一致、产物自检通过；"
          f"模板与素材均与真源一致；文档边界齐全；出处分级一致")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
