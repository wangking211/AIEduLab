# -*- coding: utf-8 -*-
"""
check.py — 书稿校验：把 vizkit.validate 跑在本书全部插图上（退出码可入 CI）。

    python check.py            # 校验全部插图
    python check.py -v         # 连警告一起打印

校验用的画布尺寸取自章节 JSON 里每个 figure 块的 height（宽度取 vizkit.PAGE_CANVAS_W ——
实测值 693.8，推导见 vizkit 里的说明）。改了页面版式必须同步那个常量。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "shared" / "viz"))
sys.path.insert(0, str(HERE))

import vizkit as vk          # noqa: E402
import figures as FIGS       # noqa: E402

PAGE_CANVAS_W = vk.PAGE_CANVAS_W          # 书页 canvas 真实内容宽度（实测，单一真源在 vizkit）


def figure_sizes():
    """从章节 JSON 里取每个图的 height。"""
    sizes = {}
    for p in sorted((HERE / "chapters").glob("*.json")):
        ch = json.loads(p.read_text(encoding="utf-8-sig"))
        for b in ch.get("blocks", []):
            if b.get("type") == "figure":
                sizes[b["id"]] = int(b.get("height") or 300)
    return sizes


def main(argv):
    verbose = "-v" in argv or "--verbose" in argv
    sizes = figure_sizes()
    figs = FIGS.build()
    total_err = total_warn = 0
    for fid, spec in figs.items():
        h = sizes.get(fid, 300)
        rep = vk.validate(spec, W=PAGE_CANVAS_W, H=h)
        total_err += len(rep.errors)
        total_warn += len(rep.warnings)
        tag = "OK  " if rep.ok else "FAIL"
        print(f"[{tag}] {fid:16s} ({PAGE_CANVAS_W}×{h})  错误 {len(rep.errors)}  警告 {len(rep.warnings)}")
        if rep.errors or (verbose and rep.warnings):
            for line in rep.format().splitlines():
                print("       " + line)
    missing = set(figs) - set(sizes)
    if missing:
        print(f"\n⚠ 这些图没有被任何章节引用：{sorted(missing)}")
    print(f"\n合计：{len(figs)} 张图，{total_err} 个错误，{total_warn} 个警告")
    return 1 if total_err else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
