# -*- coding: utf-8 -*-
"""check.py — 《生命的尺度》插图校验入口（逻辑在 edulab/shared/bookcheck.py）。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "shared"))
from bookcheck import check          # noqa: E402

if __name__ == "__main__":
    raise SystemExit(check(HERE, sys.argv[1:]))