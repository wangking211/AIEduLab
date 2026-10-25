# -*- coding: utf-8 -*-
"""
bookbuild.py — 把一本书装配成一套可离线打开的书页（所有书共用这一份）。

流程：
    book.json（书元数据 + 目录）
  + chapters/chNN.json（章节正文块）
  + figures.py（插图：声明式图形语法 spec）
  + facts.py（可选：事实登记表，提供 @@记号@@ 的值与出处）
  + shared/viz/viz.js（图形语法引擎，整段内联）
  + shared/viz/page.html（书页模板）
  → output/index.html（封面 + 目录）、output/chNN.html（各章）

**为什么抽成共享模块**：第二本书出现时，最省事的做法是复制一份 build.py ——
那一份从此与第一份独立漂移；而「正文数字必须同源」这类判据恰恰依赖
**只有一条装配路径**。所以这里只留一份，各书目录下只放一层薄封装。

用法（在各书目录里）：
    python build.py            # 生成到 ./output
    python build.py <输出目录>
    python build.py --update   # 确认改动符合预期后，刷新 prose-values.json 基线
"""
import importlib.util
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent          # edulab/shared
ROOT = HERE.parent                             # edulab/
VIZ_JS = (HERE / "viz" / "viz.js").read_text(encoding="utf-8-sig")
PAGE_T = (HERE / "viz" / "page.html").read_text(encoding="utf-8-sig")

for _p in (str(HERE), str(HERE / "viz")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import vizkit as vk                             # noqa: E402
from skillkit import inline_assets              # noqa: E402  （内联静态 CSS，去掉 Tailwind CDN）

PAGE_CANVAS_W = vk.PAGE_CANVAS_W                # 书页 canvas 真实内容宽度（单一真源在 vizkit）
PROSE_TOKEN = re.compile(r"@@([a-z_][a-z0-9_]*)(?::(\d+))?@@")


def esc(s):
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def load_book_module(book_dir, name):
    """按路径加载某本书里的 figures.py / facts.py。

    必须按路径 + 唯一模块名加载：两本书都有 figures.py，用 `import figures`
    会命中 sys.modules 里的第一个，第二本书就会**悄悄用错书的内核**。
    """
    p = Path(book_dir) / f"{name}.py"
    if not p.exists():
        return None
    mod_name = f"{name}_{Path(book_dir).name}"
    if mod_name in sys.modules:                  # 同一进程里重复加载 → 返回同一份实例
        return sys.modules[mod_name]             # （否则 Registery 会有两份，F3 的读取记录对不上）
    spec = importlib.util.spec_from_file_location(mod_name, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod              # 让 dataclass / 相对引用也能正常工作
    spec.loader.exec_module(mod)
    return mod


def subst_prose(text, values, where, seen=None):
    """把正文里的 @@name@@ / @@name:3@@ 换成内核现算出来的值。

    拼错的名字**直接报错**（而不是静默留白）—— 留白比错误更危险。

    `seen` 记录「记号 → 渲染出来的字符串」，用于和 prose-values.json 逐项比对：
    光有「值来自内核」还不够，还得保证**呈现方式**也没被悄悄改掉
    （曾经把默认精度写成两位小数，`6×6 = 36` 就渲染成了 `6.00\times 6.00 = 36.00`）。
    """
    if not isinstance(text, str) or "@@" not in text:
        return text

    def one(m):
        name, prec = m.group(1), m.group(2)
        if name not in values:
            raise KeyError(f"{where}：正文引用了未注册的记号 @@{name}@@"
                           f"（可用：{', '.join(sorted(values)) or '无'}）")
        v = values[name]
        if isinstance(v, Fraction):
            rendered = f"{v.numerator}/{v.denominator}"     # 1/3 这类分式，别写成 0.33
        elif prec is not None:                            # 显式指定精度
            rendered = f"{v:.{int(prec)}f}"
        elif abs(v - round(v)) < 1e-9:                    # 默认：整数就写整数，别写成 6.00
            i = int(round(v))
            rendered = f"{i:,}" if abs(i) >= 10000 else str(i)   # 五位以上用千分位
        else:
            rendered = f"{v:.2f}"
        if seen is not None:
            # 按「完整记号」做键而不是按名字：同一个名字可以带不同精度渲染
            # （图注写 @@flat_tot:1@@ 得 180.0，正文写 @@flat_tot@@ 得 180），
            # 按名字做键会让两者互相覆盖，基线就失去了分辨力。
            seen[f"{name}:{prec}" if prec else name] = rendered
        return rendered
    return PROSE_TOKEN.sub(one, text)


def subst_chapter(node, values, seen, where="章节正文"):
    """递归地把一章里所有字符串字段都过一遍替换。"""
    if isinstance(node, str):
        return subst_prose(node, values, where, seen)
    if isinstance(node, list):
        return [subst_chapter(x, values, seen, where) for x in node]
    if isinstance(node, dict):
        return {k: subst_chapter(v, values, seen, where) for k, v in node.items()}
    return node


def book_values(figs_mod, facts_mod, fig_ids):
    """一章可用的记号表 = 插图现算值 + 事实登记值。重名直接报错（否则张冠李戴）。"""
    vals = dict(figs_mod.prose_values(fig_ids)) if figs_mod and hasattr(figs_mod, "prose_values") else {}
    if facts_mod is not None:
        reg = getattr(facts_mod, "REGISTRY", None)
        if reg is not None:
            for k, v in reg.values().items():
                if k in vals:
                    raise KeyError(f"记号冲突：{k} 同时由 figures.py 与 facts.py 提供")
                vals[k] = v
    return vals


def build_chapter(book, ch, fig_specs, out_dir, figs_mod, facts_mod):
    values = book_values(figs_mod, facts_mod, ch.get("figs", []))
    seen = {}
    ch = subst_chapter(ch, values, seen)
    data = {"book": book, "chapter": ch,
            "figures": {k: fig_specs[k] for k in ch.get("figs", []) if k in fig_specs}}
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if "@@" in payload:
        raise ValueError("装配后仍残留 @@ 记号：正文里有未替换的占位符")
    html = (PAGE_T
            .replace("__PAGE_TITLE__", esc(f"{ch['num']} {ch['title']} · {book['title']}"))
            .replace("__VIZ_JS__", VIZ_JS)
            .replace("__BOOK_DATA__", payload))
    out = out_dir / f"{ch['id']}.html"
    out.write_text(inline_assets(html), encoding="utf-8-sig")
    return out, seen


def build_index(book, fig_specs, out_dir, has_sources=False):
    front = book.get("front") or []
    front_html = ""
    if front:
        items = " · ".join(
            f'<a href="{esc(f["file"])}" class="text-[#b45309] hover:underline">'
            f'{esc(f["title"])} →</a>' for f in front)
        front_html = f'<div class="mb-6 text-[13px]">{items}</div>'
    cards = []
    for c in book["chapters"]:
        figs = [k for k in c.get("figs", []) if k in fig_specs]
        cards.append(f"""
        <a href="{c['file']}" class="block bg-white border border-[#e7e0d5] rounded-xl p-6
           hover:border-[#b45309] hover:shadow-md transition-all group">
          <div class="flex items-baseline gap-3 mb-2">
            <span class="text-[11px] font-mono text-[#b45309] font-bold">第 {c['num']} 章</span>
            <span class="text-[11px] text-[#a89f92]">{len(figs)} 张插图</span>
          </div>
          <div class="text-[1.15rem] font-bold text-[#1f1b16] leading-snug mb-2
                      group-hover:text-[#b45309] transition-colors" style="font-family:system-ui">{esc(c['title'])}</div>
          <div class="text-[13px] text-[#7d756a] leading-relaxed">{esc(c.get('subtitle',''))}</div>
        </a>""")
    note = book.get("index_note") or (
        "本书为「用图解释思想」的实验样章：正文之外，每张插图都是可交互的——"
        "有的能拖滑块，有的能逐步展开（点插图下方的 ◀ ▶）。")
    sibs = book.get("siblings") or []
    sib_html = ""
    if sibs:
        links = " · ".join(
            f'<a href="{esc(s["href"])}" class="text-[#b45309] hover:underline">'
            f'{esc(s.get("title", ""))}</a>' for s in sibs)
        sib_html = f'<div class="mt-6 text-[13px] text-[#7d756a]">另见：{links}</div>'
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(book['title'])}</title>
<style>__TAILWIND_CSS__</style>
<style>
  body{{background:#faf7f2;color:#1f1b16;
        font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;}}
  .serif{{font-family:"Source Han Serif SC","Noto Serif CJK SC","Songti SC",Georgia,"SimSun",serif;}}
</style></head>
<body>
<div class="max-w-[1000px] mx-auto px-6 py-20">
  <div class="mb-16">
    <div class="text-[11px] uppercase tracking-[0.3em] text-[#b45309] font-bold mb-4">
      {esc(book.get('author',''))}</div>
    <h1 class="text-[2.6rem] font-bold leading-tight mb-5 serif">{esc(book['title'])}</h1>
    <p class="text-[1.1rem] text-[#4a423a] leading-relaxed max-w-[46rem] serif">
      {esc(book.get('subtitle',''))}</p>
    {sib_html}
    <div class="mt-6 flex items-center gap-4 text-[12px] text-[#a89f92]">
      <span>{len(book['chapters'])} 章</span><span>·</span>
      <span>{sum(len([k for k in c.get('figs',[]) if k in fig_specs]) for c in book['chapters'])} 张图解</span><span>·</span>
      <span>{esc(book.get('edition',''))}</span>
    </div>
  </div>
  <div class="text-[11px] uppercase tracking-[0.2em] text-[#7d756a] font-bold mb-5">目录</div>
  {front_html}
  <div class="grid gap-4">{''.join(cards)}</div>
  {('<div class="mt-8"><a href="sources.html" class="text-[13px] text-[#b45309] '
    'hover:underline">附录：全部数字的出处 →</a></div>') if has_sources else ''}
  <div class="mt-16 pt-6 border-t border-[#e7e0d5] text-[12px] text-[#a89f92] leading-relaxed">
    {esc(note)}
  </div>
</div>
</body></html>"""
    out = out_dir / "index.html"
    out.write_text(inline_assets(html), encoding="utf-8-sig")
    return out


def build_sources(book, facts_mod, used_by, out_dir):
    """把事实登记表导出成一张给读者看的「出处总表」。

    这张页是自动生成的：内容全部来自 facts.py 的登记项，没有一个字是手写的。
    它让「每个数字都说得出出处」这句话从**内部判据**变成**读者可核的附录**。
    """
    reg = getattr(facts_mod, "REGISTRY", None) if facts_mod is not None else None
    if reg is None or not reg.items:
        return None
    order = {"现算": 0, "实测": 1, "文献": 2, "约定": 3}
    items = sorted(reg.items.values(), key=lambda c: (order.get(c["grade"], 9), c["id"]))

    def fmt_val(c):
        v = c.get("value")
        try:
            f = float(v)
            if f == 0:
                return "0"
            if abs(f) >= 1e5 or abs(f) < 1e-3:
                return f"{f:.4e}".replace("e", "×10^")
            return f"{f:,.6g}"
        except (TypeError, ValueError):
            return esc(str(v))

    rows = []
    for c in items:
        who = ", ".join(sorted(used_by.get(c["id"], []))) or "—"
        src = esc(c.get("source") or "")
        if c.get("url"):
            src = f'<a class="text-[#b45309] hover:underline" href="{esc(c["url"])}">' \
                  f'{src or esc(c["url"])}</a>'
        loc = esc(c.get("locator") or "")
        note = esc(c.get("note") or ("由本表其它登记算出" if c["grade"] == "现算" else ""))
        unit = esc(c.get("unit") or "")
        rows.append(f"""<tr class="border-t border-[#eee7dc] align-top">
      <td class="py-2 pr-3 font-mono text-[11px] text-[#7d756a] whitespace-nowrap">{esc(c["id"])}</td>
      <td class="py-2 pr-3 text-[13px] whitespace-nowrap">{fmt_val(c)} <span class="text-[11px] text-[#a89f92]">{unit}</span></td>
      <td class="py-2 pr-3 text-[12px] whitespace-nowrap">{esc(c["grade"])}</td>
      <td class="py-2 pr-3 text-[12px] text-[#4a423a]">{src}{('<br><span class="text-[11px] text-[#7d756a]">' + loc + '</span>') if loc else ''}</td>
      <td class="py-2 pr-3 text-[11px] text-[#7d756a]">{who}</td>
      <td class="py-2 text-[11px] text-[#7d756a]">{note}</td>
    </tr>""")

    grade_note = {
        "现算": "由本表其它登记算出来 —— 出书时闸门会<b>重新算一遍</b>并比对",
        "实测": "观测/实验值，附不确定度与可核链接",
        "文献": "文献里的定值，附页码 / 表号 / DOI",
        "约定": "单位定义或演示参数 —— 不是自然规律，必须写明为什么只能约定",
    }
    counts = "".join(
        f'<span class="mr-4">{g} {sum(1 for c in items if c["grade"] == g)}</span>'
        for g in ("现算", "实测", "文献", "约定")
        if any(c["grade"] == g for c in items))
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>数字的出处 · {esc(book['title'])}</title>
<style>__TAILWIND_CSS__</style>
<style>
  body{{background:#faf7f2;color:#1f1b16;
        font-family:system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;}}
  .serif{{font-family:"Source Han Serif SC","Noto Serif CJK SC","Songti SC",Georgia,"SimSun",serif;}}
</style></head>
<body>
<div class="max-w-[1000px] mx-auto px-6 py-16">
  <div class="text-[11px] uppercase tracking-[0.2em] text-[#b45309] font-bold mb-3">
    {esc(book['title'])} · 附录</div>
  <h1 class="text-[2rem] font-bold leading-tight mb-4 serif">数字的出处</h1>
  <p class="text-[14px] text-[#4a423a] leading-relaxed max-w-[46rem] mb-3">
    本书正文里的每个数都在下面这张表里。这张表<b>自动生成</b>，直接读自书的登记表
    <code class="text-[12px] bg-[#f2ece2] px-1 rounded">facts.py</code>。</p>
  <p class="text-[13px] text-[#7d756a] mb-6">{counts}</p>
  <div class="bg-white border border-[#e7e0d5] rounded-xl px-5 py-4 mb-8 text-[12px] text-[#4a423a] leading-relaxed">
    <div class="mb-1"><b>四个等级，义务不同：</b></div>
    <div>· <b>现算</b> —— {grade_note['现算']}</div>
    <div>· <b>实测</b> —— {grade_note['实测']}</div>
    <div>· <b>文献</b> —— {grade_note['文献']}</div>
    <div>· <b>约定</b> —— {grade_note['约定']}</div>
  </div>
  <table class="w-full text-left">
    <thead class="text-[11px] uppercase tracking-[0.12em] text-[#7d756a]">
      <tr><th class="pb-2 pr-3">记号</th><th class="pb-2 pr-3">值</th>
          <th class="pb-2 pr-3">等级</th><th class="pb-2 pr-3">出处</th>
          <th class="pb-2 pr-3">用在</th><th class="pb-2">说明</th></tr>
    </thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
  <div class="mt-10 pt-6 border-t border-[#e7e0d5] text-[12px] text-[#a89f92]">
    <a href="index.html" class="text-[#b45309] hover:underline">← 回到目录</a>
  </div>
</div>
</body></html>"""
    out = out_dir / "sources.html"
    out.write_text(inline_assets(html), encoding="utf-8-sig")
    return out


def build(book_dir, argv):
    """装配一本书。argv 与旧 build.py 兼容（[输出目录] [--update]）。"""
    book_dir = Path(book_dir)
    update = "--update" in argv
    argv = [a for a in argv if not a.startswith("--")]
    out_dir = Path(argv[0]) if argv else book_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    book = json.loads((book_dir / "book.json").read_text(encoding="utf-8-sig"))

    figs_mod = load_book_module(book_dir, "figures")
    if figs_mod is None:
        raise SystemExit(f"{book_dir}：缺少 figures.py")
    facts_mod = load_book_module(book_dir, "facts")
    all_figs = figs_mod.build()

    # ---- 先校验，不通过就不出书（质量闸门）----
    sizes = {}
    for ch in book["chapters"]:
        p = book_dir / "chapters" / f"{ch['id']}.json"
        if p.exists():
            for b in json.loads(p.read_text(encoding="utf-8-sig")).get("blocks", []):
                if b.get("type") == "figure":
                    sizes[b["id"]] = int(b.get("height") or 300)
    bad = 0
    for fid, sp in all_figs.items():
        rep = vk.validate(sp, W=PAGE_CANVAS_W, H=sizes.get(fid, 300))
        if not rep.ok:
            bad += 1
            print(f"[校验失败] {fid}\n{rep.format()}")
    if bad:
        print(f"\n❌ {bad} 张插图未通过校验，已中止出书（先修图再 build）")
        return 1
    print(f"✓ 插图校验通过（{len(all_figs)} 张）")

    written, all_seen = [], {}
    used_by = {}
    # 前置页（读法 / 前言）：没有章号，但走同一条装配路径，因此也能用 @@记号@@
    for f in (book.get("front") or []):
        fp = book_dir / "chapters" / f"{f['id']}.json"
        if not fp.exists():
            print(f"  跳过（缺少前置页）：{f['id']}")
            continue
        fdata = json.loads(fp.read_text(encoding="utf-8-sig"))
        fdata.setdefault("num", "")
        fdata.setdefault("figs", f.get("figs", []))
        pg, seen = build_chapter(book, fdata, all_figs, out_dir, figs_mod, facts_mod)
        written.append(pg)
        if seen:
            all_seen[fdata["id"]] = seen
            for key in seen:
                used_by.setdefault(key.split(":")[0], set()).add(fdata["id"])
    for ch in book["chapters"]:
        ch_path = book_dir / "chapters" / f"{ch['id']}.json"
        if not ch_path.exists():
            print(f"  跳过（缺少正文）：{ch['id']}")
            continue
        cdata = json.loads(ch_path.read_text(encoding="utf-8-sig"))
        cdata.setdefault("num", ch["num"])
        cdata.setdefault("figs", ch.get("figs", []))
        p, seen = build_chapter(book, cdata, all_figs, out_dir, figs_mod, facts_mod)
        written.append(p)
        if seen:
            all_seen[cdata["id"]] = seen
            for key in seen:
                used_by.setdefault(key.split(":")[0], set()).add(cdata["id"])
    src = build_sources(book, facts_mod, used_by, out_dir)
    if src is not None:
        written.append(src)
    written.append(build_index(book, all_figs, out_dir, has_sources=src is not None))

    # ---- 生成值基线：正文里每个 @@记号@@ 渲染成什么，必须与基线逐项一致 ----
    # 光有「值来自内核」不够 —— 呈现方式（精度）被悄悄改掉也会出错。
    baseline_path = book_dir / "prose-values.json"
    baseline = (json.loads(baseline_path.read_text(encoding="utf-8-sig"))
                if baseline_path.exists() else {})
    if update:
        baseline_path.write_text(
            json.dumps(all_seen, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
            encoding="utf-8")
        print(f"✓ 生成值基线已刷新：{baseline_path.name}"
              f"（{sum(len(v) for v in all_seen.values())} 个记号）")
    else:
        diffs = []
        for cid in sorted(set(baseline) | set(all_seen)):
            b, g = baseline.get(cid, {}), all_seen.get(cid, {})
            for k in sorted(set(b) | set(g)):
                if b.get(k) != g.get(k):
                    diffs.append(f"  {cid}  @@{k}@@  基线={b.get(k)!r}  现在={g.get(k)!r}")
        if diffs:
            print("\n❌ 生成值与基线不一致（正文里的数字或精度变了）：")
            print("\n".join(diffs))
            print("  确认改动符合预期后：python build.py --update")
            return 1
        print(f"✓ 生成值基线一致（{sum(len(v) for v in all_seen.values())} 个记号）")

    for p in written:
        print(f"written: {p}")
    return 0
