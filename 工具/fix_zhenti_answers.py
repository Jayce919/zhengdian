#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修正真题答案的录入错误（有 OCR 答案原文作依据）。

每题断言旧答案，避免误改；--apply 前自动备份。
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "政治刷题App" / "知识点" / "questions_zhenti.json"
BACKUP = ROOT / "备份"

FIXES = {
    # 2025 第4题：OCR 答案原文「4．【答案】C」，题库录成了 A
    "q-zt-2025-04": ("A", "C"),
    # 2022 第30题：OCR 答案原文「30.【答案】ACD」，题库录成了 AC
    "q-zt-2022-30": ("AC", "ACD"),
    # 2024 第14题：OCR 答案原文「14.【答案】C」，题库录成了 B
    "q-zt-2024-14": ("B", "C"),
}


def main():
    apply = "--apply" in sys.argv
    questions = json.loads(BANK.read_text(encoding="utf-8"))
    by_id = {q["id"]: q for q in questions}
    errors, changed = [], 0

    for qid, (old, new) in FIXES.items():
        q = by_id.get(qid)
        if q is None:
            errors.append(f"{qid}: 题目不存在")
            continue
        current = "".join(q["answer"]) if isinstance(q["answer"], list) else q["answer"]
        if current == new:
            print(f"· {qid}: 已是 {new}，跳过")
            continue
        if current != old:
            errors.append(f"{qid}: 当前答案是 {current}，与预期 {old} 不符")
            continue
        letters = [o.strip()[0] for o in q["options"]]
        for ch in new:
            if ch not in letters:
                errors.append(f"{qid}: 新答案 {ch} 不在选项内")
        if any(e.startswith(qid) for e in errors):
            continue
        q["answer"] = list(new) if isinstance(q["answer"], list) else new
        changed += 1
        print(f"✓ {qid}: {old} → {new}")

    if errors:
        print("\n".join("✗ " + e for e in errors))
        sys.exit(1)
    print(f"共修正 {changed} 题答案")

    if not apply:
        print("（试运行，未写盘；加 --apply 生效）")
        return

    BACKUP.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = BACKUP / f"知识点-真题答案修复-{stamp}"
    dst.mkdir(parents=True)
    shutil.copy2(BANK, dst / BANK.name)
    BANK.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写盘；备份 → {dst}")


if __name__ == "__main__":
    main()
