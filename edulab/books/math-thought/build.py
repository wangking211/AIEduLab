# -*- coding: utf-8 -*-
"""
build.py — 把《数学思想：从计数到无穷》装配成一套可离线打开的书页。

流程：
    book.json（书元数据 + 目录）
  + chapters/chNN.json（章节正文块）
  + figures.py（插图：声明式图形语法 spec）
  + shared/viz/viz.js（图形语法引擎，整段内联）
  + shared/viz/page.html（书页模板）
  → output/index.html（封面 + 目录）、output/chNN.html（各章）

每章是**自包含单页**：内联 viz.js，其余靠 CDN。可直接双击打开。

用法：
    python build.py            # 生成到 ./output
    python build.py <输出目录>
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent                       # edulab/
VIZ_JS = (ROOT / "shared" / "viz" / "viz.js").read_text(encoding="utf-8-sig")
PAGE_T = (ROOT / "shared" / "viz" / "page.html").read_text(encoding="utf-8-sig")

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "shared" / "viz"))
import figures as FIGS                          # noqa: E402
import vizkit as vk                             # noqa: E402

PAGE_CANVAS_W = 783                             # 书页正文里 canvas 的实际宽度


def esc(s):
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


PROSE_TOKEN = re.compile(r"@@([a-z_][a-z0-9_]*)(?::(\d+))?@@")


def subst_prose(text, values, where):
    """把正文里的 @@name@@ / @@name:3@@ 换成 figures.py 现算出来的值。

    这是「生成路径」的落地：正文里凡是图形也算得出的数，都不再手写。
    拼错的名字**直接报错**（而不是静默留白）—— 留白比错误更危险。
    """
    if not isinstance(text, str) or "@@" not in text:
        return text

    def one(m):
        name, prec = m.group(1), m.group(2)
        if name not in values:
            raise KeyError(f"{where}：正文引用了未注册的记号 @@{name}@@"
                           f"（可用：{', '.join(sorted(values)) or '无'}）")
        return f"{values[name]:.{int(prec) if prec else 2}f}"
    return PROSE_TOKEN.sub(one, text)


def subst_chapter(ch, values):
    """递归地把一章里所有字符串字段都过一遍替换。"""
    if isinstance(ch, str):
        return subst_prose(ch, values, "章节正文")
    if isinstance(ch, list):
        return [subst_chapter(x, values) for x in ch]
    if isinstance(ch, dict):
        return {k: subst_chapter(v, values) for k, v in ch.items()}
    return ch


def build_chapter(book, ch, fig_specs, out_dir):
    values = FIGS.prose_values(ch.get("figs", []))
    ch = subst_chapter(ch, values)
    data = {"book": book, "chapter": ch, "figures": {k: fig_specs[k] for k in ch.get("figs", []) if k in fig_specs}}
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if "@@" in payload:
        raise ValueError("装配后仍残留 @@ 记号：正文里有未替换的占位符")
    html = (PAGE_T
            .replace("__PAGE_TITLE__", esc(f"{ch['num']} {ch['title']} · {book['title']}"))
            .replace("__VIZ_JS__", VIZ_JS)
            .replace("__BOOK_DATA__", payload))
    out = out_dir / f"{ch['id']}.html"
    out.write_text(html, encoding="utf-8-sig")
    return out


def build_index(book, fig_specs, out_dir):
    cards = []
    for i, c in enumerate(book["chapters"]):
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
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(book['title'])}</title>
<script src="https://cdn.tailwindcss.com"></script>
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
    <div class="mt-6 flex items-center gap-4 text-[12px] text-[#a89f92]">
      <span>{len(book['chapters'])} 章</span><span>·</span>
      <span>{sum(len([k for k in c.get('figs',[]) if k in fig_specs]) for c in book['chapters'])} 张图解</span><span>·</span>
      <span>{esc(book.get('edition',''))}</span>
    </div>
  </div>
  <div class="text-[11px] uppercase tracking-[0.2em] text-[#7d756a] font-bold mb-5">目录</div>
  <div class="grid gap-4">{''.join(cards)}</div>
  <div class="mt-16 pt-6 border-t border-[#e7e0d5] text-[12px] text-[#a89f92] leading-relaxed">
    本书为「用图解释思想」的实验样章：正文之外，每张插图都是可交互的——
    有的能拖滑块，有的能逐步展开（点插图下方的 ◀ ▶）。
  </div>
</div>
</body></html>"""
    out = out_dir / "index.html"
    out.write_text(html, encoding="utf-8-sig")
    return out


def main(argv):
    out_dir = Path(argv[0]) if argv else HERE / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    book = json.loads((HERE / "book.json").read_text(encoding="utf-8-sig"))
    all_figs = FIGS.build()

    # ---- 先校验，不通过就不出书（质量闸门）----
    sizes = {}
    for ch in book["chapters"]:
        p = HERE / "chapters" / f"{ch['id']}.json"
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

    written = []
    for ch in book["chapters"]:
        ch_path = HERE / "chapters" / f"{ch['id']}.json"
        if not ch_path.exists():
            print(f"  跳过（缺少正文）：{ch['id']}")
            continue
        cdata = json.loads(ch_path.read_text(encoding="utf-8-sig"))
        cdata.setdefault("num", ch["num"])
        cdata.setdefault("figs", ch.get("figs", []))       # 插图清单写在 book.json 的章节条目里
        written.append(build_chapter(book, cdata, all_figs, out_dir))
    written.append(build_index(book, all_figs, out_dir))
    for p in written:
        print(f"written: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
