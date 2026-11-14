#!/usr/bin/env python3
"""news-image-01 entry (v2): copy the committed entry.png to /output/entry.png.

Standard library only. Deterministic: the same bytes are written on every
run. Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for
/output (mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py).
"""
import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
OUT.mkdir(parents=True, exist_ok=True)

shutil.copyfile(HERE / "entry.png", OUT / "entry.png")
