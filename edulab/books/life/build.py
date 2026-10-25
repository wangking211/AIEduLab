# -*- coding: utf-8 -*-
"""build.py — 《生命的尺度》的装配入口（逻辑在 edulab/shared/bookbuild.py）。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "shared"))
from bookbuild import build          # noqa: E402

if __name__ == "__main__":
    raise SystemExit(build(HERE, sys.argv[1:]))