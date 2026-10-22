# -*- coding: utf-8 -*-
"""build.py — 《数学思想：从计数到无穷》的装配入口。

实际装配逻辑在 `edulab/shared/bookbuild.py`：第二本书出现时若复制一份 build.py，
两份会独立漂移；而「正文数字必须与内核同源」这类判据依赖**只有一条装配路径**。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "shared"))
from bookbuild import build          # noqa: E402

if __name__ == "__main__":
    raise SystemExit(build(HERE, sys.argv[1:]))
