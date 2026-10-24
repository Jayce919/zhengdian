# -*- coding: utf-8 -*-
r"""批量 OCR：把扫描版 PDF 逐页识别成带页码的 Markdown。

默认引擎 RapidOCR（中文扫描件明显优于 Tesseract：垄断/萧条/吞并等不再误识）。

用法:
    python 工具\ocr_all.py [--engine rapid|tesseract] [--workers 8] [书名关键字...]

输出:
    原始OCR\<书名>.md      每页以 "## P<n>" 分隔（n 为 PDF 内页码，从 1 起）
    原始OCR\quality.json   {书名: [每页平均置信度 0-100]}
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

# 必须在 numpy / onnxruntime 之前设置：每进程单线程，避免多进程互相抢占
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_v] = "1"

import fitz
from PIL import Image

BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "原始OCR"
BOOKS = [
    "2027考研政治-背诵手册【上册】-全新改版--肖秀荣.pdf",
    "2027考研政治-背诵手册【下册】-全新改版--肖秀荣.pdf",
    "2027考研政治-知识点-精讲精练--肖秀荣政治序列①.pdf",
]
EXTRA_DIRS = [BASE, BASE.parent]

_engine = "rapid"
_doc: fitz.Document | None = None
_rapid = None


def _init(engine: str, path: str) -> None:
    global _engine, _doc, _rapid
    _engine = engine
    _doc = fitz.open(path)
    if engine == "rapid":
        from rapidocr_onnxruntime import RapidOCR

        _rapid = RapidOCR()


def load_page_image(doc: fitz.Document, i: int) -> Image.Image:
    page = doc[i]
    best, best_px = None, 0
    for info in page.get_images(full=True):
        try:
            raw = doc.extract_image(info[0])
        except Exception:
            continue
        px = raw.get("width", 0) * raw.get("height", 0)
        if px > best_px:
            best_px, best = px, raw
    if best is not None and best.get("width", 0) >= 400:
        img = Image.open(io.BytesIO(best["image"])).convert("L")
    else:
        # 矢量 PDF：内嵌图只是装饰，直接渲染整页
        pix = page.get_pixmap(dpi=300, colorspace=fitz.csGRAY)
        img = Image.frombytes("L", (pix.width, pix.height), pix.samples)
    if img.width < 1600:
        img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    return img


def ocr_page(i: int):
    img = load_page_image(_doc, i)

    if _engine == "rapid":
        import numpy as np

        res, _ = _rapid(np.array(img))
        res = res or []
        text = "\n".join(r[1] for r in res)
        conf = sum(float(r[2]) for r in res) / len(res) * 100 if res else 0.0
        return i, text.strip(), round(conf, 1)

    from pytesseract import Output, image_to_data, image_to_string

    data = image_to_data(img, lang="chi_sim", config="--psm 6", output_type=Output.DICT)
    lines: dict[tuple, list[str]] = {}
    order: list[tuple] = []
    confs: list[float] = []
    for k, word in enumerate(data["text"]):
        word = word.strip()
        if not word:
            continue
        try:
            conf = float(data["conf"][k])
        except (TypeError, ValueError):
            conf = -1
        if conf >= 0:
            confs.append(conf)
        key = (data["block_num"][k], data["par_num"][k], data["line_num"][k])
        if key not in lines:
            lines[key] = []
            order.append(key)
        lines[key].append(word)

    out = []
    for key in order:
        words = lines[key]
        buf = words[0]
        for w in words[1:]:
            if re.match(r"[A-Za-z0-9]$", buf[-1:]) and re.match(r"[A-Za-z0-9]", w):
                buf += " " + w
            else:
                buf += w
        out.append(buf)
    text = "\n".join(out).strip()
    if not text:
        text = image_to_string(img, lang="chi_sim", config="--psm 6").strip()
    mean = sum(confs) / len(confs) if confs else 0.0
    return i, text, round(mean, 1)


def resolve(name: str) -> Path:
    for d in EXTRA_DIRS:
        p = d / name
        if p.exists():
            return p
    raise FileNotFoundError(name)


def main() -> None:
    engine, workers, keywords = "rapid", 8, []
    argv = sys.argv[1:]
    k = 0
    while k < len(argv):
        if argv[k] == "--engine":
            engine, k = argv[k + 1], k + 2
        elif argv[k] == "--workers":
            workers, k = int(argv[k + 1]), k + 2
        else:
            keywords.append(argv[k])
            k += 1

    OUT.mkdir(exist_ok=True)
    prog_dir = OUT / ".progress"
    prog_dir.mkdir(exist_ok=True)
    books = [b for b in BOOKS if not keywords or any(w in b for w in keywords)]
    qpath = OUT / "quality.json"
    quality = json.loads(qpath.read_text("utf-8")) if qpath.exists() else {}

    for book in books:
        path = resolve(book)
        n = fitz.open(path).page_count
        stem = Path(book).stem
        prog = prog_dir / f"{stem}.jsonl"

        done: dict[int, tuple[str, float]] = {}
        if prog.exists():
            for line in prog.read_text("utf-8").splitlines():
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                done[r["i"]] = (r["text"], r["conf"])

        pending = [i for i in range(n) if i not in done]
        print(f"[{stem}] {n} 页 engine={engine} workers={workers} 已完成 {n - len(pending)}", flush=True)

        if pending:
            with open(prog, "a", encoding="utf-8") as fh, ProcessPoolExecutor(
                max_workers=workers, initializer=_init, initargs=(engine, str(path))
            ) as ex:
                for k, (i, text, conf) in enumerate(ex.map(ocr_page, pending, chunksize=2), 1):
                    done[i] = (text, conf)
                    fh.write(json.dumps({"i": i, "text": text, "conf": conf}, ensure_ascii=False) + "\n")
                    fh.flush()
                    if k % 25 == 0 or k == len(pending):
                        print(f"  {k}/{len(pending)}", flush=True)

        missing = [i for i in range(n) if i not in done]
        if missing:
            print(f"  警告：{len(missing)} 页未完成，先写出其余页", flush=True)

        parts = [f"# {stem}\n"]
        for i in range(n):
            if i in done:
                parts.append(f"\n## P{i + 1}\n\n{done[i][0]}\n")
        (OUT / f"{stem}.md").write_text("".join(parts), encoding="utf-8")
        quality[stem] = [done[i][1] if i in done else 0 for i in range(n)]
        qpath.write_text(json.dumps(quality, ensure_ascii=False, indent=1), "utf-8")
        low = sum(1 for c in quality[stem] if c and c < 70)
        print(f"  完成，低置信页 {low} 页", flush=True)


if __name__ == "__main__":
    main()
