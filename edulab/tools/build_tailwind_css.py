#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_tailwind_css.py — 重新生成 shared/board/tailwind.min.css（离线排版用）。

背景
    页面原先引 `<script src="https://cdn.tailwindcss.com">`：断网就整页排版塌掉。
    现在改为**构建期把用到的 Tailwind 工具类编译成静态 CSS**，由
    `skillkit.inline_assets()` 内联进每个产物（注入到 `</head>` 之前，
    与 Play CDN 的注入位置一致 —— 否则优先级会反过来，见 inline_assets 的注释）。

何时需要重跑
    只有当**类名集合变了**（新页面用了新的工具类、或改了配色/间距）才需要。
    判断办法：跑一遍 check_output / check_render，若页面样式明显不对，
    先看看是不是漏了类 —— 本脚本按「已生成产物 + 模板」全文扫描类名，
    所以顺序是：**先重新生成产物，再重编译 CSS，再重新生成产物一次**（内联要新 CSS）。

为什么不用 Play CDN 的运行时
    407KB/页（运行时编译器），346 页 = 140MB；静态 CSS 只有 36KB/页。

用法
    python edulab/tools/build_tailwind_css.py            # 重新编译并覆盖
    python edulab/tools/build_tailwind_css.py --check    # 只比对 sha256，不写

依赖：node + npm + 网络（安装 tailwindcss，版本钉在下方 VERSION）。
"""

import argparse
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # edulab/
REPO = ROOT.parent
OUT = ROOT / "shared" / "board" / "tailwind.min.css"
VERSION = "3.4.17"                      # 与 Play CDN 当前的 v3.4.x 对齐

INPUT_CSS = "@tailwind base;\n@tailwind components;\n@tailwind utilities;\n"

# 扫描范围：产物（含动态类名的字面量）+ 模板。刻意不含 docs/*.md。
CONTENT = [
    f"{ROOT}/skills/*/output/*.html",
    f"{ROOT}/skills/*/template/*.html",
    f"{ROOT}/shared/**/*.html",
    f"{ROOT}/books/math-thought/output/*.html",
    f"{REPO}/mental-models/output/*.html",
    f"{REPO}/mental-models/template/*.html",
]


def sha256_of(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def npx():
    for c in ("npx.cmd", "npx", "npx.exe"):
        p = shutil.which(c)
        if p:
            return p
    return None


def npm():
    for c in ("npm.cmd", "npm", "npm.exe"):
        p = shutil.which(c)
        if p:
            return p
    return None


def strip_inlined_css(text):
    """剥掉产物里**已内联的** Tailwind <style> 块。

    不剥会自我污染：CSS 文本里的 `.text-xl{...}`、`--tw-*` 会被 CLI 当成新的类名
    候选，于是「重编译一次就多一批规则，sha256 永远对不上」。剥掉后本脚本对
    「产物是内联前还是内联后」不敏感（幂等）。
    """
    out, i = [], 0
    while True:
        a = text.find("<style>", i)
        if a < 0:
            out.append(text[i:])
            break
        b = text.find("</style>", a)
        if b < 0:
            out.append(text[i:])
            break
        block = text[a:b]
        out.append(text[i:a])
        if "--tw-border-spacing-x" not in block:      # 只保留页面自己的样式
            out.append(text[a:b + 8])
        i = b + 8
    return "".join(out)


def build(tmp):
    """在临时目录里装 pinned tailwindcss 并编译，返回生成的 css 文本。"""
    exe = npx()
    npm_exe = npm()
    if not exe or not npm_exe:
        raise SystemExit("找不到 npm/npx —— 需要 node + npm 才能重新编译 Tailwind")

    # 1) 先把扫描目标复制到 tmp/scan（剥掉已内联的 Tailwind CSS）
    scan = tmp / "scan"
    scan.mkdir()
    n = 0
    for pat in CONTENT:
        for f in glob.glob(pat, recursive=True):
            fp = Path(f)
            if not fp.is_file():
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            (scan / f"{n:04d}.html").write_text(strip_inlined_css(text), encoding="utf-8")
            n += 1
    if n == 0:
        raise SystemExit("扫描集为空 —— 产物还没生成？先跑 generate.py，再重编译 CSS")
    print(f"扫描 {n} 个文件（已剥掉内联 CSS）")

    (tmp / "package.json").write_text(
        json.dumps({"name": "tw-build", "private": True}), encoding="utf-8")
    r = subprocess.run([npm_exe, "i", f"tailwindcss@{VERSION}", "--no-audit", "--no-fund"],
                       cwd=str(tmp), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit("npm 安装失败（需要网络）：\n" + (r.stderr or r.stdout)[-800:])
    (tmp / "input.css").write_text(INPUT_CSS, encoding="utf-8")
    cfg = tmp / "tailwind.config.js"
    cfg.write_text("module.exports = " + json.dumps(
        {"content": [str(scan / "*.html")], "theme": {"extend": {}}, "plugins": []},
        indent=2) + ";\n", encoding="utf-8")
    r = subprocess.run([exe, "tailwindcss", "-c", str(cfg), "-i", str(tmp / "input.css"),
                        "-o", str(tmp / "out.css"), "--minify"],
                       cwd=str(tmp), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise SystemExit("tailwind 编译失败：\n" + (r.stderr or r.stdout)[-1200:])
    css = (tmp / "out.css").read_text(encoding="utf-8")
    if "--tw-border-spacing-x" not in css:
        raise SystemExit("编译产物缺少 preflight（--tw-border-spacing-x 未出现），拒绝写入")
    return css


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只比对 sha256，不写文件")
    args = ap.parse_args(argv)

    with tempfile.TemporaryDirectory() as td:
        css = build(Path(td))

    data = css.encode("utf-8")
    new_sha = hashlib.sha256(data).hexdigest()
    old_sha = sha256_of(OUT) if OUT.exists() else "(缺)"
    print(f"新旧 sha256: {old_sha[:16]}… → {new_sha[:16]}…  大小 {len(data)/1024:.1f} KB")
    if args.check:
        if old_sha != new_sha:
            print("✗ 与仓库里的 CSS 不一致 —— 类名集合变了，请重跑本脚本（不带 --check）")
            return 1
        print("✓ 一致")
        return 0
    OUT.write_text(css, encoding="utf-8", newline="\n")
    print(f"已写入 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
