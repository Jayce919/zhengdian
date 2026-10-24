#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把人工撰写的真题干扰项解析写回 questions_zhenti.json。

用法：
  python 工具/add_zhenti_distractors.py --patch 工具/zhenti_distractors/mayuan.json          # 试运行
  python 工具/add_zhenti_distractors.py --patch 工具/zhenti_distractors/mayuan.json --apply  # 写盘（自动备份）

patch 文件格式：{"q-zt-2009-01": {"B": {"why": "...", "trap": "张冠李戴"}, ...}, ...}
"""
import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "政治刷题App" / "知识点" / "questions_zhenti.json"
BACKUP = ROOT / "备份"
TRAPS = {"偷换概念", "扩大缩小", "张冠李戴", "绝对化", "因果倒置", "无关正确项"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--patch", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    patch_path = Path(args.patch)
    if not patch_path.is_absolute():
        patch_path = ROOT / patch_path
    patch = json.loads(patch_path.read_text(encoding="utf-8"))
    questions = json.loads(BANK.read_text(encoding="utf-8"))
    by_id = {q["id"]: q for q in questions}

    errors, filled, skipped = [], 0, 0
    for qid, entries in patch.items():
        q = by_id.get(qid)
        if q is None:
            errors.append(f"{qid}: 题目不存在")
            continue
        if q["type"] not in ("single", "multi"):
            errors.append(f"{qid}: 非选择题")
            continue
        letters = [o.strip()[0] for o in q["options"]]
        right = [q["answer"]] if isinstance(q["answer"], str) else list(q["answer"])
        for letter, d in entries.items():
            if letter not in letters:
                errors.append(f"{qid}: 选项 {letter} 不存在")
            if letter in right:
                errors.append(f"{qid}: {letter} 是正确项，不能写干扰解析")
            if not d.get("why", "").strip():
                errors.append(f"{qid}.{letter}: why 为空")
            if d.get("trap") not in TRAPS:
                errors.append(f"{qid}.{letter}: trap「{d.get('trap')}」不在词表 {sorted(TRAPS)}")
            existing = (q.get("distractors") or {}).get(letter)
            if existing:
                skipped += 1
            else:
                q.setdefault("distractors", {})[letter] = {
                    "why": d["why"].strip(),
                    "trap": d["trap"],
                }
                filled += 1

    # 覆盖度复核：每条选择题都应配齐错误项
    remaining = []
    for q in questions:
        if q["type"] not in ("single", "multi"):
            continue
        right = [q["answer"]] if isinstance(q["answer"], str) else list(q["answer"])
        wrong = [o.strip()[0] for o in q["options"] if o.strip()[0] not in right]
        lack = [w for w in wrong if w not in (q.get("distractors") or {})]
        if lack:
            remaining.append((q["id"], "".join(lack)))

    print(f"patch 条目 {sum(len(v) for v in patch.values())}；新增 {filled}，已存在跳过 {skipped}")
    print(f"题库剩余未配干扰项：{len(remaining)} 题 / {sum(len(x[1]) for x in remaining)} 条")
    if remaining:
        print("  样例：" + "，".join(f"{i}({l})" for i, l in remaining[:8]))
    if errors:
        print("\n".join("✗ " + e for e in errors))
        sys.exit(1)

    if not args.apply:
        print("（试运行，未写盘；加 --apply 生效）")
        return

    BACKUP.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = BACKUP / f"知识点-真题干扰项-{stamp}"
    dst.mkdir(parents=True)
    shutil.copy2(BANK, dst / BANK.name)
    BANK.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写盘；备份 → {dst}")


if __name__ == "__main__":
    main()
