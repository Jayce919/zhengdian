#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把知识点中被 220 字上限截断的 quote 补全到完整句。

从 时政 PDF（有文字层）与 原始OCR 全量文本中定位原句，向后取到第一个句末标点。
只处理「长度 >= 200 且不以句末标点结尾」的 quote。
"""
import glob
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
PARTS = ROOT / "政治刷题App" / "知识点" / "parts"
BACKUP = ROOT / "备份"

BAD = re.compile(r"配课程公众号.*|热联系微信.*|扫码.*|第\s*\d+\s*页.*|2027考研政治.*?讲义")


def build_corpus():
    texts = []
    for f in glob.glob(str(ROOT / "【时政】*.pdf")):
        doc = fitz.open(f)
        t = "".join(p.get_text() for p in doc)
        if t.strip():
            texts.append(t)
    for f in glob.glob(str(ROOT / "原始OCR" / "*.md")):
        texts.append(Path(f).read_text(encoding="utf-8", errors="ignore"))
    for f in glob.glob(str(ROOT / "原始OCR" / ".progress" / "*.jsonl")):
        for line in Path(f).read_text(encoding="utf-8", errors="ignore").splitlines():
            try:
                texts.append(json.loads(line)["text"])
            except Exception:
                pass
    return re.sub(r"\s+", "", "\n".join(texts))


def extend(quote, corpus):
    key = re.sub(r"\s+", "", quote)[:30]
    i = corpus.find(key)
    if i < 0:
        return None
    seg = corpus[i:]
    m = re.search(r"[。！？]", seg[220:700])
    if not m:
        return None
    new = seg[: 220 + m.end()]
    new = BAD.sub("", new)
    new = new.strip()
    if not new.endswith(("。", "！", "？", "”")):
        return None
    if len(new) <= len(quote):
        return None
    return new


def main():
    apply = "--apply" in sys.argv
    if apply:
        BACKUP.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dst = BACKUP / f"知识点-引文补全-{stamp}"
        dst.mkdir(parents=True)
        for f in PARTS.glob("*.json"):
            shutil.copy2(f, dst / f.name)
        print(f"备份 → {dst}")
    corpus = build_corpus()
    changed = []
    unresolved = []
    for f in sorted(PARTS.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        dirty = False
        for p in data.get("points", []):
            q = p.get("quote", "")
            if len(q) >= 200 and not q.rstrip().endswith(("。", "！", "？", "”")):
                new = extend(q, corpus)
                if new:
                    p["quote"] = new
                    changed.append((p["id"], len(q), len(new), new[-30:]))
                    dirty = True
                else:
                    unresolved.append(p["id"])
        if apply and dirty:
            f.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"可补全 {len(changed)} 条，仍无法定位 {len(unresolved)} 条")
    for x in changed:
        print(f"  {x[0]}  {x[1]}→{x[2]}字  …{x[3]}")
    if unresolved:
        print("未定位：" + "、".join(unresolved))
    if not apply:
        print("（试运行，未写盘；加 --apply 生效）")
    else:
        print("已写盘")


if __name__ == "__main__":
    main()
