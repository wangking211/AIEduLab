#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_output.py —— 产物自检：对**构建出来的 HTML** 做检查，不读源码。

其它闸门读的都是源（figures.py、chapters/*.json、SKILL.md）。源是对的不代表
产物是对的：渲染器可以把一切画歪、模板可以漏替换、构建可以引用不存在的文件。
这份闸门站在读者那一侧 —— 双击打开的那个文件，才是交付物。

它本身就是这么被逼出来的：写几何 lint 前先去浏览器量了一次真值，量出
viz.js 的 resize() 会随窗口缩放无限撑高画布（314.4 → 328.8 → 343.2 …），
以及校验一直按 783 宽做、真值却是 693.8。这两个问题源码里都看不出来，
只有量产物才现形。

    O1  残留模板记号（@@ 记号、__VIZ_JS__、{{ }}）
    O2  外链白名单（超出白名单的 CDN = 断网即白屏；白名单内的逐条列出）
    O3  本地引用必须真的存在（src/href 指向不存在的文件）
    O4  canvas 高度 == 章节声明的高度（渲染器把画布撑高时立刻现形）
    O5  画布宽度口径（从页面自身 CSS 反推列宽上限，与 PAGE_CANVAS_W 比对）
    O6  渲染残留（undefined / [object Object] / NaN 出现在正文里）
    O7  script / style 标签配对，且有 <meta charset>

    python edulab/tools/check_output.py                 # 自检全部已构建产物
    python edulab/tools/check_output.py --dir <目录>     # 指定目录（技能产物同理）
    python edulab/tools/check_output.py -v              # 打印每条外链与每个 canvas

退出码可入 CI。产物目录默认不入库（.gitignore 的 output/），因此这是**构建后**
跑的闸门，与 check_skills.py 的临时目录产物同理。
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
BOOK = ROOT / "edulab" / "books" / "math-thought"

sys.path.insert(0, str(ROOT / "edulab" / "shared" / "viz"))
import vizkit as vk                                     # noqa: E402

CDN_ALLOW = {
    "cdn.tailwindcss.com": "Tailwind 运行时（版面排版）",
    "cdn.jsdelivr.net": "KaTeX（数学公式）",
    "cdnjs.cloudflare.com": "Three.js r128（生物细胞 / 化学分子 3D）",
}
# 说明：这三项是**已知且已批准的取舍**，不是「断网也能开」。
# 现状（2026-10 实测）：348 个产物、每页 4 个外部资源；断网时页面能打开、文字可读，
# 但排版整体塌掉、公式显示为 LaTeX 源码，3D 页只剩空白。
# 引这三个之外的主机一律报错（这一条是硬的）；引这三个之内**不算通过离线可用**，
# main() 会在末尾汇总「N 个产物依赖外部资源」，让这项取舍始终可见。
# 要真离线：内联编译后的 CSS + KaTeX 连字体自带（独立工程，需像素级视觉回归）。
# 见 curriculum-roadmap.md 第 16 条。

TAG_RE = re.compile(r"<(script|link|img|meta|canvas)\b([^>]*)/?>", re.I)
ATTR_RE = re.compile(r"([a-zA-Z-]+)\s*=\s*\"([^\"]*)\"")
SCRIPT_BODY_RE = re.compile(r"<script\b[^>]*>(.*?)</script>", re.I | re.S)
STYLE_BODY_RE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.I | re.S)
TOKEN_RE = re.compile(r"@@[A-Za-z_][A-Za-z0-9_]*(:\d+)?@@")
BROKEN_TOKEN_RE = re.compile(r"@@")
CANVAS_H_RE = re.compile(r"height\s*:\s*([\d.]+)px")
MAXW_RE = re.compile(r"max-w-\[(\d+)px\]")
FIGPAD_RE = re.compile(r"\.figbox\{[^}]*?padding\s*:\s*([\d.]+)px\s+([\d.]+)px")
FIGBORDER_RE = re.compile(r"\.figbox\{[^}]*?border\s*:\s*([\d.]+)px")


def attrs_of(tag_text):
    return {k.lower(): v for k, v in ATTR_RE.findall(tag_text)}


def chapter_figure_heights():
    """章节 JSON 里声明的 figure 高度。"""
    out = {}
    for p in sorted((BOOK / "chapters").glob("*.json")):
        ch = json.loads(p.read_text(encoding="utf-8-sig"))
        for b in ch.get("blocks", []):
            if b.get("type") == "figure":
                out[b["id"]] = int(b.get("height") or 300)
    return out


def strip_code(html):
    """去掉 script / style 的内容，剩下的才是读者看得见的正文。"""
    html = SCRIPT_BODY_RE.sub("", html)
    html = STYLE_BODY_RE.sub("", html)
    return html


def check_file(path, declared_heights, verbose):
    """返回 (errors, warnings, info)。每项是 (码, 位置, 说明, 修法)。"""
    errs, warns, infos = [], [], []
    raw = path.read_text(encoding="utf-8", errors="replace")
    html = strip_code(raw)
    rel = path.name

    # ---- O1 残留模板记号 ----
    for m in TOKEN_RE.finditer(raw):
        errs.append(("O1", f"{rel}", f"装配后仍残留记号 {m.group(0)}",
                     "run build.py；记号拼错不会被替换"))
    if "__VIZ_JS__" in raw or "__BOOK_DATA__" in raw:
        errs.append(("O1", rel, "模板占位符没被替换（__VIZ_JS__ / __BOOK_DATA__）",
                     "build.py 没跑完；重跑并检查它是否提前退出"))
    # 刻意**不**检查 `{{ ... }}`：LaTeX 到处是双花括号（`{{U}}`、`\\frac{{a}}{{b}}`），
    # 拿它当模板标记只会每页报一堆假阳性。本项目也根本不用 `{{ }}` 模板——
    # 书稿用 __VIZ_JS__ / __BOOK_DATA__，技能用 __LESSON_DATA__，正文用 @@name@@。

    # ---- O2 外链白名单 ----
    for tag in TAG_RE.finditer(raw):
        a = attrs_of(tag.group(0))
        for key in ("src", "href"):
            v = a.get(key)
            if not v or not v.startswith(("http://", "https://")):
                continue
            host = re.sub(r"^https?://", "", v).split("/")[0]
            if host in CDN_ALLOW:
                infos.append(("O2", rel, f"外链 {host} → {v[:70]}",
                              f"断网不可用（{CDN_ALLOW[host]}）"))
            else:
                errs.append(("O2", rel, f"白名单外的外链：{v[:90]}",
                             f"加进白名单并说明理由，或改成本地文件 —— 产物必须断网可开"))

    # ---- O3 本地引用必须存在 ----
    for tag in TAG_RE.finditer(raw):
        a = attrs_of(tag.group(0))
        for key in ("src", "href"):
            v = a.get(key)
            if not v or v.startswith(("http://", "https://", "#", "data:", "mailto:")):
                continue
            v = v.split("#")[0].split("?")[0]
            if not v:
                continue
            if not (path.parent / v).exists():
                errs.append(("O3", rel, f"{key}={v} 指向不存在的文件",
                             "把它一起构建出来，或删掉这个引用"))

    # ---- O4 canvas 高度 == 章节声明 ----
    for tag in TAG_RE.finditer(raw):
        if tag.group(1).lower() != "canvas":
            continue
        a = attrs_of(tag.group(0))
        fid = a.get("data-fig") or a.get("id")
        cls = a.get("class", "")
        # 两种合法写法：
        #   1) 书稿：canvas 写死 style="height:Npx"，高度必须等于章节声明；
        #   2) 技能画板：class 里 inset-0 / w-full h-full，由父容器撑满，
        #      尺寸在运行时由 JS 从 getBoundingClientRect 取 —— 没有写死高度是对的。
        fills_parent = "inset-0" in cls or ("w-full" in cls and "h-full" in cls)
        m = CANVAS_H_RE.search(tag.group(0))
        if fills_parent and not m:
            infos.append(("O4", rel, f"canvas {fid!r} 由父容器撑满（尺寸运行时取）", ""))
            continue
        if not m:
            warns.append(("O4", rel, f"canvas {fid!r} 既没写 style 高度、也没撑满父容器",
                          "两种写法选一种：写死高度，或 class 加 inset-0 / w-full h-full"))
            continue
        got = float(m.group(1))
        want = declared_heights.get(fid)
        if want is None:
            infos.append(("O4", rel, f"canvas {fid!r} 不在任何章节里", "确认是否废弃"))
        elif abs(got - want) > 0.6:
            errs.append(("O4", rel,
                         f"canvas {fid!r} 实际 {got:.1f}px，章节声明 {want}px",
                         "渲染器多半把画布撑高了 —— 检查 resize() 有没有把父元素"
                         "的 rect 写回 canvas 的 style（会形成正反馈）"))
        else:
            infos.append(("O4", rel, f"canvas {fid!r} 高 {got:.1f}px == 声明", ""))

    # ---- O5 画布宽度口径 ----
    css = " ".join(STYLE_BODY_RE.findall(raw))
    mw = MAXW_RE.search(css)
    if mw:
        limit = float(mw.group(1))
        pad = FIGPAD_RE.search(css)
        bor = FIGBORDER_RE.search(css)
        slack = (2 * float(pad.group(2)) if pad else 0) + (2 * float(bor.group(1)) if bor else 0)
        upper = limit - slack
        if vk.PAGE_CANVAS_W > upper + 0.6:
            errs.append(("O5", rel,
                         f"PAGE_CANVAS_W={vk.PAGE_CANVAS_W} 比页面列宽上限 {upper:.1f} 还宽",
                         "校验宽度必须 ≤ 真实画布宽度，否则越界检查只会在一张"
                         "更宽的虚拟画布上做，永远只漏报"))
        else:
            infos.append(("O5", rel,
                          f"列宽上限 {upper:.1f} ≥ PAGE_CANVAS_W {vk.PAGE_CANVAS_W}", ""))

    # ---- O6 渲染残留 ----
    for bad in ("undefined", "[object Object]"):
        if bad in html:
            errs.append(("O6", rel, f"正文里出现 {bad!r}",
                         "多半是模板取了个不存在的字段；在产物里读者直接看得到"))
    for m in re.finditer(r"(?<![\w.])NaN(?![\w])", html):
        errs.append(("O6", rel, f"正文里出现 NaN（{html[max(0, m.start()-30):m.start()+10]!r}）",
                     "算出 NaN 就别画 —— 先在内核里算，再把有限值交给图"))

    # ---- O7 标签配对 ----
    for tagname in ("script", "style"):
        opens = len(re.findall(rf"<{tagname}\b", raw, re.I))
        closes = len(re.findall(rf"</{tagname}>", raw, re.I))
        if opens != closes:
            errs.append(("O7", rel, f"<{tagname}> 开 {opens} 个、闭 {closes} 个",
                         "标签没配对，后面整页的解析都会乱"))
    if not re.search(r"<meta[^>]+charset", raw, re.I):
        warns.append(("O7", rel, "缺 <meta charset=\"utf-8\">", "中文页面缺它会乱码"))

    return errs, warns, infos


def main(argv):
    verbose = "-v" in argv or "--verbose" in argv
    dirs = []
    if "--dir" in argv:
        d = argv[argv.index("--dir") + 1]
        dirs.append(Path(d))
    else:
        dirs.append(BOOK / "output")
        dirs.append(ROOT / "mental-models" / "output")

    declared = chapter_figure_heights()
    nfile = tot_err = tot_warn = 0
    ext_pages, ext_hosts = set(), {}
    for d in dirs:
        if not d.is_dir():
            print(f"[跳过] {d} 不存在（未构建）")
            continue
        files = sorted(d.glob("*.html"))
        if not files:
            print(f"[跳过] {d} 下没有 html")
            continue
        print(f"== {d} ==")
        for f in files:
            errs, warns, infos = check_file(f, declared, verbose)
            nfile += 1
            tot_err += len(errs)
            tot_warn += len(warns)
            for code, _where, msg, _fix in infos:
                if code == "O2":
                    m = re.match(r"外链\s+(\S+)", msg)
                    if m:
                        ext_pages.add(str(f))
                        ext_hosts[m.group(1)] = ext_hosts.get(m.group(1), 0) + 1
            tag = "OK  " if not errs else "FAIL"
            print(f"[{tag}] {f.name:16s} 错误 {len(errs)}  警告 {len(warns)}")
            show = errs + (warns if verbose else [])
            for code, where, msg, fix in show:
                print(f"       {code}  {msg}")
                if fix:
                    print(f"            → {fix}")
            if verbose:
                for code, where, msg, fix in infos:
                    print(f"       {code}·  {msg}")
    print(f"\n合计：{nfile} 个产物，{tot_err} 个错误，{tot_warn} 个警告")
    if ext_pages:
        hosts = "、".join(f"{h}×{n}" for h, n in sorted(ext_hosts.items(), key=lambda kv: -kv[1]))
        # 这条汇总存在的意义：白名单最容易变成「批准了就没人再看」。
        # 每跑一次就把取舍摆到眼前，而不是让它只活在一行注释里。
        print(f"外部资源依赖：{len(ext_pages)}/{nfile} 个产物引用 CDN（{hosts}）")
        print("  → 断网仍可打开、文字可读；但排版塌陷、公式显示为 LaTeX 源码、3D 页空白。")
        print("    这是**已批准的取舍**，不等于「自包含到可离线」；见 curriculum-roadmap.md 第 16 条。")
    return 1 if tot_err else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
