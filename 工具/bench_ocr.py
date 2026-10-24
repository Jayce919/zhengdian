# -*- coding: utf-8 -*-
"""预处理对照实验：同一页在不同放大/二值化下，哪个 OCR 结果更准。

用法: python 工具\bench_ocr.py <pdf路径> <页码1> <页码2> ...
输出每页每种方案的文本到 stdout，便于人工比对。
"""
import io
import sys
from pathlib import Path

import fitz
import pytesseract
from PIL import Image, ImageFilter, ImageOps


def page_image(doc, index: int) -> Image.Image:
    page = doc[index]
    imgs = page.get_images(full=True)
    if imgs:
        info = doc.extract_image(imgs[0][0])
        img = Image.open(io.BytesIO(info["image"]))
        return img.convert("L")
    pix = page.get_pixmap(dpi=300, colorspace=fitz.csGRAY)
    return Image.frombytes("L", (pix.width, pix.height), pix.samples)


def variants(img: Image.Image):
    yield "raw", img
    yield "gray2x", img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    sharp = img.resize((img.width * 2, img.height * 2), Image.LANCZOS).filter(
        ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=3)
    )
    yield "sharp2x", sharp
    yield "auto2x", ImageOps.autocontrast(sharp)


def main() -> None:
    pdf = Path(sys.argv[1])
    doc = fitz.open(pdf)
    for p in sys.argv[2:]:
        i = int(p)
        img = page_image(doc, i)
        print(f"\n########## {pdf.name}  P{i}  ({img.width}x{img.height}) ##########", flush=True)
        for name, v in variants(img):
            txt = pytesseract.image_to_string(v, lang="chi_sim", config="--psm 6")
            txt = "\n".join(ln for ln in txt.splitlines() if ln.strip())
            print(f"\n----- {name} -----\n{txt}", flush=True)


if __name__ == "__main__":
    main()
