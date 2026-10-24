#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把人工整理的新真题追加进 questions_zhenti.json。

用法：
  python 工具/add_zhenti_questions.py --patch 工具/zhenti_new/2025.json          # 试运行
  python 工具/add_zhenti_questions.py --patch 工具/zhenti_new/2025.json --apply  # 写盘（自动备份）

patch 为题目对象数组，字段与 questions_zhenti.json 一致。
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
LETTER = set("ABCD")


def validate(q, seen):
    errs = []
    qid = q.get("id", "")
    if not qid or qid in seen:
        errs.append(f"{qid}: id 缺失或重复")
    if q.get("type") not in ("single", "multi"):
        errs.append(f"{qid}: 类型必须是 single/multi")
    if not q.get("stem", "").strip():
        errs.append(f"{qid}: 题干为空")
    opts = q.get("options") or []
    if len(opts) != 4:
        errs.append(f"{qid}: 选项不是 4 个")
    letters = [o.strip()[0] for o in opts]
    if any(l not in LETTER for l in letters):
        errs.append(f"{qid}: 选项未以 A-D 开头")
    right = [q["answer"]] if isinstance(q.get("answer"), str) else list(q.get("answer") or [])
    if q.get("type") == "single" and len(right) != 1:
        errs.append(f"{qid}: 单选答案必须 1 个")
    if q.get("type") == "multi" and len(right) < 2:
        errs.append(f"{qid}: 多选答案至少 2 个")
    for r in right:
        if r not in letters:
            errs.append(f"{qid}: 答案 {r} 不在选项内")
    wrong = [l for l in letters if l not in right]
    d = q.get("distractors") or {}
    if set(d) != set(wrong):
        errs.append(f"{qid}: 干扰项 {sorted(d)} 与错误项 {sorted(wrong)} 不一致")
    for k, v in d.items():
        if not v.get("why", "").strip():
            errs.append(f"{qid}.{k}: why 为空")
        if v.get("trap") not in TRAPS:
            errs.append(f"{qid}.{k}: trap 非法")
    if not q.get("explain", "").strip():
        errs.append(f"{qid}: 解析为空")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--patch", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    patch_path = Path(args.patch)
    if not patch_path.is_absolute():
        patch_path = ROOT / patch_path
    new = json.loads(patch_path.read_text(encoding="utf-8"))
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    seen = {q["id"] for q in bank}

    errors = []
    for q in new:
        errors += validate(q, seen)
        seen.add(q.get("id", ""))

    print(f"待新增 {len(new)} 题：{', '.join(q['id'] for q in new)}")
    if errors:
        print("\n".join("✗ " + e for e in errors))
        sys.exit(1)

    if not args.apply:
        print("（试运行，未写盘；加 --apply 生效）")
        return

    BACKUP.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = BACKUP / f"知识点-真题补题-{stamp}"
    dst.mkdir(parents=True)
    shutil.copy2(BANK, dst / BANK.name)
    bank.extend(new)
    bank.sort(key=lambda q: q["id"])
    BANK.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写盘，共 {len(bank)} 题；备份 → {dst}")


if __name__ == "__main__":
    main()
