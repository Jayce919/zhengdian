#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""对扫描版真题解析 PDF 做一次定向 OCR，抽出 33 道客观题的答案键。

原始OCR/*.md 里 2013/2014/2015/2017 的答案解析有若干题号被 OCR 吞掉，
这里用 RapidOCR 重新识别这几份 PDF，把「N.【标准答案】X」按出现顺序落盘到
工具/zhenti_new/ocr_keys_<year>.json，供 verify_zhenti_answers.py 比对。

答案行里题号常被识别成 "H."、"44;" 之类，所以不依赖题号，按出现顺序编号 1..33。
"""
import json
import re
import sys
from pathlib import Path

import fitz
from rapidocr_onnxruntime import RapidOCR

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "2009-2021考研政治真题及解析" / "2009-2021年考研政治解析"
OUT = ROOT / "政治刷题App" / "工具" / "zhenti_new"
PAT = re.compile(r"【\s*标准答案\s*】?\s*([A-D]{1,4})")


def main(years):
    ocr = RapidOCR()
    for year in years:
        pdf = BASE / f"{year}年考研政治答案解析.pdf"
        doc = fitz.open(pdf)
        keys = []
        for page in doc:
            res, _ = ocr(page.get_pixmap(dpi=180).tobytes("png"))
            for _, text, _score in res or []:
                m = PAT.search(text)
                if m:
                    keys.append(m.group(1))
        keys = keys[:33]
        assert len(keys) == 33, f"{year} 只识别出 {len(keys)} 条答案"
        path = OUT / f"ocr_keys_{year}.json"
        path.write_text(json.dumps(keys, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{year}: 33 条 → {path.name}")


if __name__ == "__main__":
    main(sys.argv[1:] or ["2013", "2014", "2015", "2017"])
