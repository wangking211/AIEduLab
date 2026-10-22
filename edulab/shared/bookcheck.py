# -*- coding: utf-8 -*-
"""
bookcheck.py — 书稿插图校验（所有书共用这一份）。

把 vizkit 的校验器跑在一本书的全部插图上，校验用的画布尺寸取自章节 JSON 里
每个 figure 块的 height（宽度取 vizkit.PAGE_CANVAS_W —— 实测值，推导见 vizkit）。

    python check.py            # 校验全部插图
    python check.py -v         # 连警告一起打印

退出码 1 表示有错误（警告不影响退出码，但会计数）。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for _p in (str(HERE / "viz"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import vizkit as vk                       # noqa: E402
from bookbuild import load_book_module   # noqa: E402


def figure_sizes(book_dir):
    """从章节 JSON 里取每个图的 height。"""
    sizes = {}
    for p in sorted((Path(book_dir) / "chapters").glob("*.json")):
        ch = json.loads(p.read_text(encoding="utf-8-sig"))
        for b in ch.get("blocks", []):
            if b.get("type") == "figure":
                sizes[b["id"]] = int(b.get("height") or 300)
    return sizes


def check(book_dir, argv):
    book_dir = Path(book_dir)
    verbose = "-v" in argv or "--verbose" in argv
    sizes = figure_sizes(book_dir)
    figs_mod = load_book_module(book_dir, "figures")
    if figs_mod is None:
        raise SystemExit(f"{book_dir}：缺少 figures.py")
    figs = figs_mod.build()
    total_err = total_warn = total_blind = 0
    for fid, spec in figs.items():
        h = sizes.get(fid, 300)
        rep = vk.validate(spec, W=vk.PAGE_CANVAS_W, H=h)
        total_err += len(rep.errors)
        total_warn += len(rep.warnings)
        total_blind += len(rep.unread)
        tag = "OK  " if rep.ok else "FAIL"
        blind = f"  未解析 {len(rep.unread)}" if rep.unread else ""
        print(f"[{tag}] {fid:16s} ({vk.PAGE_CANVAS_W}×{h})  "
              f"错误 {len(rep.errors)}  警告 {len(rep.warnings)}{blind}")
        if rep.errors or rep.unread or (verbose and rep.warnings):
            for line in rep.format().splitlines():
                print("       " + line)
    missing = set(figs) - set(sizes)
    if missing:
        print(f"\n⚠ 这些图没有被任何章节引用：{sorted(missing)}")
    extra = ""
    if total_blind:
        extra = (f"；{total_blind} 处未能解析 —— 这些地方的几何结论不成立，"
                 f"不等于没有问题")
    print(f"\n合计：{len(figs)} 张图，{total_err} 个错误，{total_warn} 个警告{extra}")
    return 1 if total_err else 0
