# -*- coding: utf-8 -*-
r"""对 OCR 结果做保守的系统性纠错，生成 *.fixed.md（原始 *.md 不动）。

只处理扫描件里反复出现的固定误识，不做上下文改写，便于人工复核差异。

用法：python 工具\fix_ocr.py
"""
from __future__ import annotations

import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
OCR = BASE / "原始OCR"

# 左为 OCR 常见误识，右为正确写法。按长度从长到短替换，避免互相覆盖。
FIXES = [
    ("垒断", "垄断"),
    ("华断", "垄断"),
    ("董断", "垄断"),
    ("芍断", "垄断"),
    ("八断", "垄断"),
    ("鞋断", "垄断"),
    ("更蔡", "更替"),
    ("翟秋白", "瞿秋白"),
    ("士地", "土地"),
    ("收关", "攸关"),
    ("换救", "挽救"),
    ("禹于", "寓于"),
    ("金触", "金融"),
    ("资未", "资本"),
    ("资杰", "资本"),
    ("剩金", "剩余"),
    ("商晶", "商品"),
    ("资木", "资本"),
    ("揭不", "揭示"),
    ("资支", "资本"),
    ("写人党章", "写入党章"),
    ("加人", "加入"),
    ("纳人", "纳入"),
    ("进人", "进入"),
]


def main() -> None:
    for src in OCR.glob("*.md"):
        if src.stem.endswith(".fixed") or src.stem.endswith(".clean"):
            continue
        text = src.read_text("utf-8")
        before = text
        for bad, good in FIXES:
            text = text.replace(bad, good)
        out = OCR / (src.stem + ".fixed.md")
        out.write_text(text, "utf-8")
        changed = sum(before.count(b) for b, _ in FIXES)
        print(f"{src.name}: 替换 {changed} 处 -> {out.name}")


if __name__ == "__main__":
    main()
