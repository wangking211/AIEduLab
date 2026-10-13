#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_video_assets.py —— 把共享层的视频素材同步进各视频技能的 template/。

背景
----
三个视频技能（math / chem / physics）是同一套渲染管线的三份拷贝。按 sha256
清点，6.98 MB 里有 3.36 MB 是字节级重复，其中 3.30 MB 是两个中文字体：

    ZCOOLKuaiLe-Regular.ttf   1,514,968 B ×3
    PatrickHand-Regular.ttf     214,772 B ×3

字体**不能**简单移出技能目录去改渲染路径：`template/index.html` 里的
`@font-face` 写的是 `url(fonts/...)`，浏览器按 HTML 自身位置解析相对路径，
必须落在 `template/fonts/` 下。而且字体加载失败是**静默降级**
（`document.fonts.load` 失败不抛错，退回 PingFang / sans-serif），
只有肉眼看渲染结果才发现 —— 属于最难被自动化拦住的一类故障。

所以沿用「唯一真源 + 派生产物」的模式（与 compose_templates.py 同思路）：

    edulab/shared/video/<素材>/       唯一真源（入库，全仓只存一份）
    <技能>/template/<素材>/           派生产物（**不入库**，由本脚本同步）

渲染链路一个字节都不变：字体仍在 index.html 的同名相对位置。

用法
----
    python edulab/tools/sync_video_assets.py           # 同步（写入各技能）
    python edulab/tools/sync_video_assets.py --check   # 只校验齐全且逐字节一致
"""

import filecmp
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SHARE = ROOT / "edulab" / "shared" / "video"
SKILLS = ROOT / "edulab" / "skills"

# 共享真源子目录 → 技能内目标子目录（渲染链路要求的相对位置）
MAPPING = {"fonts": "template/fonts"}

VIDEO_SKILLS = ["edu-math-video", "edu-chem-video", "edu-physics-video"]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def iter_sources():
    """产出 (真源文件, 技能内目标相对路径)。"""
    for src_sub, dst_sub in MAPPING.items():
        src_dir = SHARE / src_sub
        if not src_dir.is_dir():
            raise SystemExit(f"✗ 共享真源不存在：{src_dir.relative_to(ROOT).as_posix()}")
        for p in sorted(src_dir.iterdir()):
            if p.is_file():
                yield p, Path(dst_sub) / p.name


def main(argv):
    check = "--check" in argv
    items = list(iter_sources())
    if not items:
        raise SystemExit("✗ 共享真源目录为空，没有可同步的素材")

    print(f"共享真源 {SHARE.relative_to(ROOT).as_posix()}：{len(items)} 个素材")
    bad = []
    for skill in VIDEO_SKILLS:
        d = SKILLS / skill
        if not d.is_dir():
            bad.append((skill, "技能目录不存在"))
            continue
        problems = []
        written = 0
        for src, rel in items:
            dst = d / rel
            if dst.exists() and filecmp.cmp(src, dst, shallow=False):
                continue
            if check:
                problems.append(f"{rel.as_posix()} "
                                + ("不存在" if not dst.exists() else "与真源不一致"))
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
            written += 1
        if problems:
            bad.append((skill, "；".join(problems)))
        mark = "✗" if problems else "✓"
        if check:
            print(f"  {mark} {skill:22s} {len(items)} 个素材" +
                  (f"   {problems}" if problems else ""))
        else:
            print(f"  ✓ {skill:22s} 同步 {written} 个 / 共 {len(items)} 个（已是最新则跳过）")

    if bad:
        print(f"\n✗ {len(bad)} 个技能的素材有问题：")
        for s, why in bad:
            print(f"    {s}: {why}")
        print("   用 `python edulab/tools/sync_video_assets.py` 重新同步。")
        return 1
    if check:
        print("\n✓ 三个视频技能的共享素材都齐全且与真源逐字节一致")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
