# -*- coding: utf-8 -*-
"""
build_books.py — 重建全部书稿。

为什么需要它：书稿的产物新鲜度判据把 `shared/bookbuild.py`、`bookcheck.py`、
`factreg.py`、`datasets.py` 都算作「源码」。改了其中任何一个，**每一本**书的产物
都算旧，闸门会报 `产物比源码旧`。

这件事我用手工 `cd 到每本书再 build` 忘了三次 —— 于是把它做成一条命令：

    python edulab/tools/build_books.py

它只跑构建（内含插图校验与生成值基线比对），不改任何数据。
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # edulab/
BOOKS = ROOT / "books"


def main(argv=None):
    argv = list(argv or [])
    books = sorted(p for p in BOOKS.iterdir()
                   if p.is_dir() and (p / "book.json").exists())
    if not books:
        print("没有找到任何书稿")
        return 0
    bad = []
    for book in books:
        r = subprocess.run([sys.executable, "build.py", *argv], cwd=str(book),
                           capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        tail = [ln for ln in (r.stdout or "").splitlines() if ln.strip()]
        flag = "OK  " if r.returncode == 0 else "FAIL"
        print(f"[{flag}] {book.name:14s} {tail[0] if tail else ''}")
        if r.returncode != 0:
            bad.append(book.name)
            for ln in (r.stdout or "").splitlines()[-12:]:
                print("       " + ln)
            for ln in (r.stderr or "").splitlines()[-6:]:
                print("       ! " + ln)
    print(f"\n合计：{len(books)} 本书，{len(bad)} 本失败")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
