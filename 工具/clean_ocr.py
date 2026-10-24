# -*- coding: utf-8 -*-
r"""把 OCR 原始逐页文本清理成可读段落：去页眉页脚、合并断行。

用法：
    python 工具\clean_ocr.py "背诵手册上册"

输出：
    原始OCR\<书名>.clean.md   按 ## P<n> 保留页码，正文合并为段落
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
OCR = BASE / "原始OCR"

# 页眉页脚：整行匹配即丢弃
DROP = [
    re.compile(r"^\d{1,3}$"),
    re.compile(r"^第[一二三四五]部分"),
    re.compile(r"^20\d\d\s*考研政治背诵手册$"),
    re.compile(r"^\d{4}\s*KAOYAN"),
    re.compile(r"^配套课程"),
    re.compile(r"^联系微信"),
    re.compile(r"^扫码|^公众号|^关注"),
    re.compile(r"^[·•]\s*$"),
]

# 段落结束标志：这些字符结尾说明句子还没完，需要与下一行合并
CONT = re.compile(r"[^。！？；：」』）】…]$")


def is_heading(line: str) -> bool:
    if re.match(r"^专题[一二三四五六七八九十百]+", line):
        return True
    if re.match(r"^\d+[.．、]\s*\S", line) and len(line) <= 30:
        return True
    if re.match(r"^\d+\.\d+\s*\S", line):
        return True
    return False


def clean_page(text: str) -> str:
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln and not any(p.search(ln) for p in DROP)]

    out: list[str] = []
    buf = ""
    for ln in lines:
        if not buf:
            buf = ln
            continue
        # 新段落：标题、编号、项目符号
        if is_heading(ln) or re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩]", ln) or re.match(r"^[（(]\d+[)）]", ln):
            out.append(buf)
            buf = ln
            continue
        if CONT.search(buf):
            buf += ln
        else:
            out.append(buf)
            buf = ln
    if buf:
        out.append(buf)
    return "\n".join(out)


def main() -> None:
    key = sys.argv[1] if len(sys.argv) > 1 else "上册"
    src = next(p for p in OCR.glob("*.md") if key in p.name and ".clean" not in p.name)
    raw = src.read_text("utf-8")

    parts = []
    for block in re.split(r"^## (P\d+)$", raw, flags=re.M):
        block = block.strip()
        if not block:
            continue
        if re.fullmatch(r"P\d+", block):
            parts.append(f"\n## {block}\n")
        else:
            parts.append(clean_page(block) + "\n")

    out = OCR / (src.stem.replace(".md", "") + ".clean.md")
    out.write_text("".join(parts), "utf-8")
    print(f"✓ {out}  ({(out.stat().st_size / 1024):.0f} KB)")


if __name__ == "__main__":
    main()
