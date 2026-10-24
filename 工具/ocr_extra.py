# -*- coding: utf-8 -*-
r"""对新补充的扫描版 PDF 做 OCR（复用 ocr_all 的 worker 与断点续跑）。

用法：python 工具\ocr_extra.py
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ocr_all  # noqa: E402

BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "原始OCR"

TARGETS = [
    "2010年考研政治答案解析.pdf",
    "2011年考研政治答案解析.pdf",
    "2012年考研政治答案解析.pdf",
    "2014年考研政治答案解析.pdf",
]


def main() -> None:
    prog_dir = OUT / ".progress"
    prog_dir.mkdir(exist_ok=True)
    workers = 8
    qpath = OUT / "quality.json"
    quality = json.loads(qpath.read_text("utf-8")) if qpath.exists() else {}

    for name in TARGETS:
        path = next(iter(BASE.rglob(name)), None) or (BASE / name)
        if not path.exists():
            print("缺失", name)
            continue
        stem = path.stem
        prog = prog_dir / f"{stem}.jsonl"
        done: dict[int, tuple[str, float]] = {}
        if prog.exists():
            for line in prog.read_text("utf-8").splitlines():
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                done[r["i"]] = (r["text"], r["conf"])
        import fitz

        n = fitz.open(path).page_count
        pending = [i for i in range(n) if i not in done]
        print(f"[{stem}] {n} 页，待识别 {len(pending)}", flush=True)
        if pending:
            with open(prog, "a", encoding="utf-8") as fh, ProcessPoolExecutor(
                max_workers=workers, initializer=ocr_all._init, initargs=("rapid", str(path))
            ) as ex:
                for k, (i, text, conf) in enumerate(ex.map(ocr_all.ocr_page, pending, chunksize=1), 1):
                    done[i] = (text, conf)
                    fh.write(json.dumps({"i": i, "text": text, "conf": conf}, ensure_ascii=False) + "\n")
                    fh.flush()
                    if k % 5 == 0 or k == len(pending):
                        print(f"  {k}/{len(pending)}", flush=True)

        parts = [f"# {stem}\n"]
        for i in range(n):
            if i in done:
                parts.append(f"\n## P{i + 1}\n\n{done[i][0]}\n")
        (OUT / f"{stem}.md").write_text("".join(parts), encoding="utf-8")
        quality[stem] = [done[i][1] if i in done else 0 for i in range(n)]
        qpath.write_text(json.dumps(quality, ensure_ascii=False, indent=1), "utf-8")
        print("  完成", flush=True)


if __name__ == "__main__":
    main()
