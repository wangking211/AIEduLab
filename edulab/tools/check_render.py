#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_render.py — 执行级渲染闸门（把「页面能不能画出来」变成可跑的检查）。

背景：本项目原本只有**静态**校验（`vizkit.validate()` / `check.py` / `check_output.py`），
它们检查的是**数据与结构** —— 出界、文字重叠、颜色合法性、字段拼写、残留记号、
外链白名单、canvas 高度。**它们从不执行 JS。** 于是能出现这种诡异组合：

    数据全对 + 静态闸门全绿 + 页面全白

2026-10 实际踩到：`shared/viz/viz.js` 的 `Renderer.resize` 末尾
    this.W = rect.width;   // rect 从未定义
每次 resize 抛 ReferenceError，书稿 36 张图全部挂不上，
而静态闸门一路绿灯 —— 因为它压根不跑 JS。这个 bug 潜伏了多次交付才被
真机验证抓出来（见 curriculum-roadmap.md 第 15 条）。

本闸门补的正是这个洞，分三层（同一套判据精神，不同的被测物）：

    viz   《渲染引擎 × 图层 spec》 —— viz_smoke.js，Node + stub canvas
    page  《已构建 HTML 页面》      —— page_smoke.js，Node + 最小 DOM 桩
                                    （数据块能否求值、画板能否 boot、
                                      画布是否真的有绘制、帧指纹是否互异）

page 层的三个渲染源：`skills`（各技能 `output/`）、`bookpages`（书稿）、
`mental`（仓库根独立产品 `mental-models`）。

判据（刻意比「不抛异常」严格）
    1. 渲染路径不抛异常
    2. 逻辑尺寸 W/H 必须有限且 > 0（挡住 `rect` 那类 bug 的静默残留）
    3. 必须真的产生绘制调用（挡住「没崩但空画布」）
    4. 逐档回放 steps / 参数端点 params 全部不炸
    5. 推进多帧时**画面指纹必须互不相同**
       —— 把浏览器里「逐档比较画布指纹、hashUniq == 档位数」的纪律搬进闸门；
          只要求「指纹不同」会漏掉「画布纹丝不动」的静默 bug，这条已漏过三次
    6. `Viz.audit()` 的宽度同样合法
    7. **产物不得比源码旧**：旧产物上新判据全过也只是「旧货是对的」，
       等于假装验证过。按 mtime 比对产物与它的源码集合，旧了默认报错
       （刚 pull 完还没重生成时可 `RENDER_SMOKE_BEHIND_OK=1` 降级为警告）

用法
    python edulab/tools/check_render.py            # 全部渲染源
    python edulab/tools/check_render.py --list     # 列出已注册渲染源
    python edulab/tools/check_render.py --source viz
    python edulab/tools/check_render.py --selftest # 含负向测试，确认闸门非空转

说明
    `page` 类源读的是**已构建产物**（output/ 不入库），因此与 check_output.py
    一样属于**构建后**闸门：产物不存在时会明确告知并跳过，而不是假装通过。
    想让这条闸门在全新克隆上也能跑，用 `check_skills.py`（它在临时目录里现生成）。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # edulab/
VIZ_JS = ROOT / "shared" / "viz" / "viz.js"
SMOKE_JS = HERE / "viz_smoke.js"
PAGE_SMOKE_JS = HERE / "page_smoke.js"
BOOK = ROOT / "books" / "math-thought"
SHARED_VIZ = ROOT / "shared" / "viz"
SHARED_BOARD = ROOT / "shared" / "board"

RED, GRN, YEL, DIM, END = "\033[31m", "\033[32m", "\033[33m", "\033[2m", "\033[0m"
if not sys.stdout.isatty() or os.name == "nt":
    RED = GRN = YEL = DIM = END = ""       # Windows 控制台不解释 ANSI，留空即可


# =====================================================================
# 渲染源注册表：名字 -> (类型, 集合函数)。新的可执行渲染物往这里加一行。
# =====================================================================
def collect_book_specs():
    """[viz] 书稿 chapters/*.json 引用的全部插图 spec（figures.build() 现算）。"""
    if not BOOK.exists():
        return {}
    sys.path.insert(0, str(ROOT / "shared" / "viz"))
    sys.path.insert(0, str(BOOK))
    import figures                                    # noqa: WPS433 —— 有意延后 import
    return figures.build()


def _built_pages(patterns):
    out = []
    for pat in patterns:
        out.extend(sorted(str(p) for p in ROOT.glob(pat)))
    return out


def collect_skill_pages():
    """[page] 各技能已构建产物（读者双击打开的文件）。"""
    return _built_pages(["skills/*/output/*.html"])


def collect_book_pages():
    """[page] 书稿已构建页面（含 index 导航页）。"""
    return _built_pages(["books/math-thought/output/*.html"])


def collect_mental_pages():
    """[page] 仓库根独立产品 mental-models 的产物（19 个页面，同样要能渲染）。"""
    return sorted(str(p) for p in (ROOT.parent / "mental-models" / "output").glob("*.html"))


# ---------------------------------------------------------------------
# 产物新鲜度：产物比源码旧 ⇒ 下面所有判据测的都是过期产物，结论不可信
# ---------------------------------------------------------------------
def _newest_mtime(root, patterns, exts=None):
    """返回 root 下匹配 patterns 的最新**源码**文件 mtime（毫秒）。

    exts 用来排掉文档与缓存：`README.md` 改了不该让产物变「旧」，
    `__pycache__/*.pyc` 更不该（它由 import 生成，时间戳永远比产物新）。
    """
    best = 0.0
    for pat in patterns:
        try:
            for p in Path(root).glob(pat):
                if not p.is_file():
                    continue
                if "__pycache__" in p.parts:
                    continue
                if exts is not None and p.suffix.lower() not in exts:
                    continue
                best = max(best, p.stat().st_mtime_ns / 1e6)
        except OSError:
            continue
    return best


CODE_EXTS = {".py", ".js", ".html", ".css", ".json"}

# 共享渲染器里**真正被构建读取**的文件。刻意不含 README/grammar：
# 改文档不该把全部产物判旧，否则这条判据会立刻变成噪音被忽略。
VIZ_SOURCES = ("viz.js", "page.html", "vizkit.py")


def page_source_mtime(page_path):
    """一个产物页面「由哪些源码决定」——改了就必重新生成，否则闸门在测旧货。

    技能产物 = 该技能 kernel/generate/template + 共享画板骨架 + 共享渲染器；
    书稿页面 = figures/build/patch + 章节 JSON + 共享渲染器。
    刻意**不含** tools/ 下的闸门自身：改闸门不影响产物内容，不该把产物判旧。
    """
    p = Path(page_path).resolve()
    best = 0.0
    try:
        if p.is_relative_to(BOOK.resolve()):
            best = max(best, _newest_mtime(BOOK, ["figures.py", "build.py", "patch.py"]))
            best = max(best, _newest_mtime(BOOK, ["chapters/*"], CODE_EXTS))
        else:
            # <产品>/output/<页面>.html —— 技能与根级产品（mental-models）同构
            prod = p.parents[1]
            best = max(best, _newest_mtime(prod, ["scripts/*.py", "lib/*.py",
                                                  "template/**/*", "data/**/*"],
                                           CODE_EXTS))
            best = max(best, _newest_mtime(SHARED_BOARD, ["**/*"], CODE_EXTS))
        best = max(best, _newest_mtime(SHARED_VIZ, list(VIZ_SOURCES)))
    except OSError:
        return 0.0
    return best


def build_manifest(pages):
    return {str(Path(p).resolve()): page_source_mtime(p) for p in pages}


SOURCES = {
    "viz": ("viz", collect_book_specs),
    "skills": ("page", collect_skill_pages),
    "bookpages": ("page", collect_book_pages),
    "mental": ("page", collect_mental_pages),
}


# =====================================================================
# 执行
# =====================================================================
def find_node():
    for cand in ("node", "node.exe", os.path.join(r"C:\Program Files\nodejs", "node.exe")):
        p = shutil.which(cand) or (cand if Path(cand).exists() else None)
        if p:
            return p
    return None


def _run(cmd, timeout=300):
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"fatal": f"超时（{timeout}s）", "results": [], "summary": {}}, -1
    except OSError as exc:
        return {"fatal": f"无法启动 node：{exc}", "results": [], "summary": {}}, -1
    out = (proc.stdout or "").strip()
    if not out:
        return {"fatal": f"node 无输出。stderr={(proc.stderr or '')[:300]}",
                "results": [], "summary": {}}, proc.returncode
    try:
        return json.loads(out), proc.returncode
    except json.JSONDecodeError:
        return {"fatal": f"node 输出不是 JSON：{out[:300]}", "results": [], "summary": {}}, 1


def run_viz_smoke(specs, node, viz_path, tmp):
    specs_file = Path(tmp) / "specs.json"
    specs_file.write_text(json.dumps(specs, ensure_ascii=False, separators=(",", ":")),
                          encoding="utf-8")
    cmd = [node, str(SMOKE_JS), "--viz", str(viz_path), "--specs", str(specs_file),
           "--w", "694", "--h", "400", "--dpr", "2"]
    return _run(cmd, 180)


def run_page_smoke(pages, node, tmp, manifest=None):
    inputs = Path(tmp) / "inputs.json"
    inputs.write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
    cmd = [node, str(PAGE_SMOKE_JS), "--inputs", str(inputs)]
    if manifest:
        mf = Path(tmp) / "manifest.json"
        mf.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        cmd += ["--manifest", str(mf)]
    return _run(cmd, 300)


def report_viz(source, data):
    errors, warnings = [], []
    if data.get("fatal"):
        errors.append(f"[{source}] 致命：{data['fatal']}")
    for r in data.get("results", []):
        tag = f"[{source}] {r['id']}"
        if r.get("ok"):
            extra = []
            if r.get("stepsRun", 0) > 1:
                extra.append(f"步骤 {r['stepsRun']}")
            if r.get("stepHashes", 0) > 1:
                extra.append(f"档指纹 {r['stepHashes']}")
            if r.get("paramsRun", 0):
                extra.append(f"参数端点 {r['paramsRun']}")
            if r.get("drawCalls", 0) > 0:
                extra.append(f"绘制 {r['drawCalls']} 次")
            au = r.get("audit") or {}
            if au:
                extra.append("audit " + ("✓" if au.get("ok")
                                         else f"溢出{au.get('overflow')}/出框{au.get('outside')}"))
            print(f"  [OK  ] {r['id']:<26} W={r.get('W')} H={r.get('H')}  {'  '.join(extra)}")
            if au and not au.get("ok"):
                warnings.append(f"{tag} audit 报溢出/出框：{au}")
        else:
            print(f"  [FAIL] {r['id']:<26} {r.get('error')}")
            if r.get("stack"):
                print(f"         {DIM}{r['stack']}{END}")
            errors.append(f"{tag} {r.get('error')}")
    return errors, warnings


def report_page(source, data, quiet=False):
    errors, warnings, skipped = [], [], []
    behind_ok = os.environ.get("RENDER_SMOKE_BEHIND_OK") == "1"
    if data.get("fatal"):
        errors.append(f"[{source}] 致命：{data['fatal']}")
    for r in data.get("results", []):
        tag = f"[{source}] {r['id']}"
        if r.get("skipped"):
            skipped.append(r["id"])
            print(f"  [SKIP] {r['id']:<34} {r.get('notes', [''])[0]}")
            continue
        if r.get("behind"):
            # 产物陈旧 ≠ 页面有缺陷，但**必须**让它可见：此时所有判据都在测旧产物，
            # 报绿等于假装验证过。默认算错误，只因「刚 pull 完还没重生成」才可降级。
            msg = (f"{tag} 产物比源码旧 {r.get('behindBy')}s —— 先重新生成再验"
                   f"（否则测的是旧产物）")
            if behind_ok:
                warnings.append(msg)
            else:
                errors.append(msg)
        if r.get("ok"):
            detail = (f"script {r.get('scripts')}  canvas {r.get('canvases')}  "
                      f"绘制 {r.get('drawn')}  帧 {r.get('frames')}  指纹 {r.get('hashUniq')}")
            if r.get("canvases", 0) == 0:
                detail += "  （无画布）"
            if not quiet:
                print(f"  [OK  ] {r['id']:<34} {detail}")
            for n in (r.get("notes") or []):
                # 「静态页无脚本」是导航/索引页的正常状态，不是可疑信号，
                # 混进警告会让人误以为有问题；它仍然打印出来，只是不计数。
                if n.startswith("无内联脚本"):
                    continue
                warnings.append(f"{tag} {n}")
        else:
            print(f"  [FAIL] {r['id']:<34} {r.get('error')}")
            if r.get("stack"):
                print(f"         {DIM}{r['stack']}{END}")
            dbg = r.get("debug") or {}
            if r.get("probe"):
                print(f"         {DIM}探针命中: {r['probe']}{END}")
            if dbg:
                if "identical" in dbg:
                    print(f"         {DIM}步数={dbg.get('n')} 首步=末步? {dbg.get('identical')}"
                          f"  首步={str(dbg.get('first'))[:90]}{END}")
                else:
                    print(f"         {DIM}scene={str(dbg.get('scene'))[:150]}{END}")
            errors.append(f"{tag} {r.get('error')}")
    return errors, warnings, skipped


# =====================================================================
# 负向测试：注入已知 bug，确认闸门会红
# =====================================================================
VIZ_MUTATIONS = [
    ("未定义标识符 rect（本项目真实踩过的 bug）",
     "this.W = w; this.H = h;",
     "this.W = rect.width; this.H = rect.height;",
     "渲染必须抛异常"),
    ("静默全白（W/H 归零，不抛异常）",
     "this.W = w; this.H = h;",
     "this.W = 0; this.H = 0;",
     "逻辑尺寸检查必须拦下"),
    ("步骤绑定失效（setStep 永远渲染第 0 档）",
     "ctl.step = Math.max(0, Math.min((spec.steps ? spec.steps.length : 1) - 1, i));",
     "ctl.step = Math.max(0, Math.min((spec.steps ? spec.steps.length : 1) - 1, 0));",
     "逐档指纹检查必须拦下（画布纹丝不动）"),
]


def _viz_broken(data):
    return (data.get("fatal") is not None) or any(not r.get("ok") for r in data.get("results", []))


def selftest_viz(node, specs, tmp):
    """对 viz 层做负向测试：注入已知 bug，闸门必须变红。"""
    src = VIZ_JS.read_text(encoding="utf-8-sig")
    ok = True
    for idx, (name, old, new, why) in enumerate(VIZ_MUTATIONS):
        if old not in src:
            print(f"  [FAIL] 找不到注入锚点 `{old}`（viz.js 变了？）")
            ok = False
            continue
        mutated = Path(tmp) / f"mutated_{idx}.js"
        mutated.write_text(src.replace(old, new, 1), encoding="utf-8")
        data, _ = run_viz_smoke(specs, node, mutated, tmp)
        if _viz_broken(data):
            first = next((r["id"] for r in data.get("results", []) if not r.get("ok")),
                         (data.get("fatal") or "")[:40])
            print(f"  [OK  ] 注入「{name}」→ 闸门变红，首个命中：{first}  ({why})")
        else:
            print(f"  [FAIL] 注入「{name}」→ **闸门没有变红**！({why})")
            ok = False
        clean, _ = run_viz_smoke(specs, node, VIZ_JS, tmp)
        if _viz_broken(clean):
            print(f"        {YEL}[WARN]{END} 恢复后未全绿（本轮构建本身有问题）")
            ok = False
    return ok


# =====================================================================
# page 层负向测试 —— 用**合成夹具**，不篡改真实产物
#
# 为什么不用「往真实产物里注错」：
#   * 页面外壳常把异常吞进 `console.error(...); return;`，注入的错可能根本走不到；
#   * 真实产物可能是 3D 页（会被标 skipped），那样测试会「假通过」，等于没测。
# 合成夹具精确对应每一条判据，且与仓库状态无关 —— 它测的是**闸门本身**。
# =====================================================================
def _fixture(title, body_script, canvas=True):
    cv = '<canvas id="cv" width="300" height="200"></canvas>' if canvas else ""
    return (
        '<!doctype html><html><head><meta charset="utf-8"><title>'
        + title
        + "</title></head><body>"
        + cv
        + "\n<script>\n"
        + body_script
        + "\n</script>\n</body></html>\n"
    )


PAGE_FIXTURES = [
    (
        "f-throw.html",
        "zzzTopLevelCrash();",
        True,
        "脚本运行时抛异常",
        "",
    ),
    (
        "f-blank.html",
        # 拿到上下文却一像素不画 —— 等价于「渲染器抛错被 try/catch 吞掉」
        "var cvv = document.getElementById('cv'); var g = cvv.getContext('2d');",
        True,
        "有画布但零绘制（静默全白）",
        "绘制调用都没有",
    ),
    (
        "f-frozen.html",
        "var cvv = document.getElementById('cv'); var g = cvv.getContext('2d');\n"
        "function paint(){ g.clearRect(0,0,300,200); g.fillStyle='#fff'; g.fillRect(0,0,300,200);"
        " g.strokeStyle='#08f'; g.strokeRect(4,4,60,60); }\n"
        "paint();\n"
        "function steps(){ return [0,1,2,3]; }\n"
        "function setFrame(i){ paint(); }   // 步骤钩子在，但画面一动不动\n",
        True,
        "逐帧推进却纹丝不动",
        "从不变化",
    ),
    (
        "f-good.html",
        "var cvv = document.getElementById('cv'); var g = cvv.getContext('2d');\n"
        "function paint(i){ g.clearRect(0,0,300,200); g.fillStyle='#fff'; g.fillRect(0,0,300,200);"
        " g.fillStyle='#08f'; g.fillRect(0,0,10*(i+1),20); g.fillText('frame '+i, 8, 60); }\n"
        "paint(0);\n"
        "function steps(){ return [0,1,2,3]; }\n"
        "function setFrame(i){ paint(i); }\n",
        False,
        "健康对照（必须保持绿）",
        "",
    ),
]


def selftest_page(node, tmp):
    """对 page 层做负向测试：注入三类已知故障，闸门必须逐条变红；对照组必须绿。"""
    ok = True
    paths, expect = [], []
    for name, script, must_fail, why, needle in PAGE_FIXTURES:
        p = Path(tmp) / name
        p.write_text(_fixture(name, script), encoding="utf-8")
        paths.append(str(p))
        expect.append((name, must_fail, why, needle))

    data, _ = run_page_smoke(paths, node, tmp)
    if data.get("fatal"):
        print(f"  [FAIL] 夹具跑不起来：{data['fatal']}")
        return False

    by_id = {Path(r["path"]).name: r for r in data.get("results", [])}
    for name, must_fail, why, needle in expect:
        r = by_id.get(name)
        if r is None:
            print(f"  [FAIL] 夹具 {name} 没有结果")
            ok = False
            continue
        red = not r.get("ok")
        if red == must_fail:
            if must_fail:
                err = r.get("error") or ""
                if needle and needle not in err:
                    print(f"  [FAIL] {why}：闸门确实红了，但**理由不对**：{err[:90]}")
                    ok = False
                    continue
                print(f"  [OK  ] 注入「{why}」→ 闸门变红，理由吻合")
            else:
                print(f"  [OK  ] {why} → 绿（证明闸门没把好东西判死）")
        else:
            verdict = "闸门没有变红（存在空转）" if must_fail else "闸门把健康页判死了（误报）"
            print(f"  [FAIL] {why} → **{verdict}**：{(r.get('error') or '无错误信息')[:90]}")
            ok = False
    return ok


# =====================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(description="执行级渲染闸门（真跑 JS，不只查数据）")
    ap.add_argument("--source", action="append", choices=sorted(SOURCES),
                    help="只跑指定渲染源（可重复）")
    ap.add_argument("--list", action="store_true", help="列出已注册渲染源")
    ap.add_argument("--selftest", action="store_true", help="含负向测试")
    ap.add_argument("--quiet", action="store_true", help="只输出错误")
    ap.add_argument("--no-pages", action="store_true", help="跳过需要构建产物的 page 层")
    args = ap.parse_args(argv)

    if args.list:
        for k, (kind, fn) in SOURCES.items():
            print(f"  {k:12s} {fn.__doc__}")
        return 0

    node = find_node()
    if not node:
        # 闸门跑不起来 ≠ 闸门通过。这里必须红。
        print(f"{RED}[FAIL]{END} 找不到 node —— 执行级渲染闸门无法运行。")
        print("       静态校验只能查数据，查不出 renderer 坏掉；没有 node 就等于这个洞开着。")
        print("       确实在无 node 环境时请显式跳过并自行确认渲染正常：RENDER_SMOKE_SKIP=1")
        if os.environ.get("RENDER_SMOKE_SKIP") == "1":
            print(f"{YEL}[SKIP]{END} 已按 RENDER_SMOKE_SKIP=1 显式跳过。")
            return 0
        return 2

    chosen = [k for k in SOURCES if not args.source or k in args.source]
    if args.no_pages:
        chosen = [k for k in chosen if SOURCES[k][0] == "viz"]

    total_err, total_warn = [], []
    total_checked = 0
    total_skipped = 0

    with tempfile.TemporaryDirectory() as tmp:
        for name in chosen:
            kind, fn = SOURCES[name]
            payload = fn()
            if kind == "page":
                if not payload:
                    print(f"\n=== 渲染源 {name}：无已构建产物（output/ 不入库）===")
                    print(f"  {YEL}[SKIP]{END} 属构建后闸门：先跑 generate 再跑本闸门")
                    continue
                if not args.quiet:
                    print(f"\n=== 渲染源 {name}（{len(payload)} 个页面）· page_smoke.js ===")
                data, _ = run_page_smoke(payload, node, tmp, build_manifest(payload))
            else:
                if not payload:
                    print(f"  {YEL}[SKIP]{END} 渲染源 {name} 集合为空")
                    continue
                if not args.quiet:
                    print(f"\n=== 渲染源 {name}（{len(payload)} 张）· viz_smoke.js · {VIZ_JS.name} ===")
                data, _ = run_viz_smoke(payload, node, VIZ_JS, tmp)

            if kind == "page":
                errs, warns, skipped = report_page(name, data, args.quiet)
                total_skipped += len(skipped)
            else:
                errs, warns = report_viz(name, data)
            total_err += errs
            total_warn += warns
            total_checked += len(payload)

        if args.selftest:
            viz_specs = SOURCES["viz"][1]()
            if viz_specs:
                print(f"\n=== 负向测试 · viz 层（注入已知 bug，闸门必须变红）===")
                if not selftest_viz(node, viz_specs, tmp):
                    total_err.append("viz 层负向测试未通过：闸门存在空转嫌疑")
                else:
                    print(f"  {GRN}viz 层负向测试通过{END}")
            # page 层负向测试用**合成夹具**，与真实产物无关：
            # 真实产物可能是 3D 页（注入前就会被标 skipped，测试会假通过），
            # 而且外壳常把异常吞进 console.error，注入的错未必走得到。
            print(f"\n=== 负向测试 · page 层（合成夹具，逐条判据必须变红）===")
            if not selftest_page(node, tmp):
                total_err.append("page 层负向测试未通过：闸门存在空转嫌疑")
            else:
                print(f"  {GRN}page 层负向测试通过{END}")

    print()
    # 警告不许只报个数就完事 —— 那等于逼人忽略它。逐条列出。
    if total_warn:
        for w in total_warn:
            print(f"{YEL}[WARN]{END} {w}")
        print()
    if total_err:
        for e in total_err:
            print(f"{RED}[ERROR]{END} {e}")
        print(f"\n{RED}渲染闸门失败：{len(total_err)} 错误，{len(total_warn)} 警告{END}")
        return 1
    tail = f"渲染闸门通过：{total_checked} 个被测物，0 错误，{len(total_warn)} 警告"
    if total_skipped:
        # 漏洞不许悄悄溜过去 —— 明确点名，并指出它必须由谁来补验
        tail += f"\n{YEL}另有 {total_skipped} 个页面需要 Three.js/WebGL，本闸门覆盖不到：" \
                f"它们**仍需真机浏览器验证**（见 [SKIP] 行）{END}"
    print(tail)
    return 0


if __name__ == "__main__":
    sys.exit(main())
