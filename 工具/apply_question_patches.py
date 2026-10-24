#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""应用校对补丁：只改文本字段，逐条校验原文；删除题目前单独列出。

用法：
  python 工具/apply_question_patches.py 工具/review/*.json          # 试运行
  python 工具/apply_question_patches.py 工具/review/*.json --apply  # 写盘（先备份）

补丁格式：
  {"fixes":[{"file","id","field","old","new","reason"}],
   "deletes":[{"file","id","reason"}]}
约束：old 必须在字段中精确出现；不得修改 answer/options/type/id 等结构字段。
"""
import json
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "政治刷题App" / "知识点"
TEXT_FIELDS = {"stem", "explain"}
OPTION_FIELD = "options"


def load_patches(paths):
    fixes, deletes = [], []
    for p in paths:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        fixes += data.get("fixes", [])
        deletes += data.get("deletes", [])
    return fixes, deletes


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply = "--apply" in sys.argv
    if not args:
        print("用法：python 工具/apply_question_patches.py 工具/review/*.json [--apply]")
        return

    fixes, deletes = load_patches(args)
    by_file = defaultdict(lambda: {"fixes": [], "deletes": []})
    errors = []

    for f in fixes:
        name, qid, field = f.get("file"), f.get("id"), f.get("field")
        old, new = f.get("old", ""), f.get("new", "")
        if field not in TEXT_FIELDS and field != OPTION_FIELD:
            errors.append(f"{qid}: 字段 {field} 不允许修改")
            continue
        if not old or not new:
            errors.append(f"{qid}: old/new 为空")
            continue
        if old == new:
            errors.append(f"{qid}: old 与 new 相同")
            continue
        by_file[name]["fixes"].append(f)

    for d in deletes:
        by_file[d.get("file")]["deletes"].append(d)

    backups = {}
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    total_fixes = total_del = 0

    for name, ops in by_file.items():
        path = SRC / name
        if not path.exists():
            errors.append(f"{name}: 文件不存在")
            continue
        qs = json.loads(path.read_text(encoding="utf-8"))
        index = {q["id"]: q for q in qs}
        changed = 0
        for f in ops["fixes"]:
            q = index.get(f["id"])
            if not q:
                errors.append(f"{name}/{f['id']}: 题目不存在")
                continue
            old, new = f["old"], f["new"]
            if f["field"] == OPTION_FIELD:
                opts = q.get("options") or []
                if old in opts:
                    i = opts.index(old)
                else:
                    hits = [i for i, o in enumerate(opts) if old in o]
                    if len(hits) != 1:
                        errors.append(f"{name}/{f['id']}.options: 命中 {len(hits)} 个选项")
                        continue
                    i = hits[0]
                lo = re.match(r"^([A-D])[.．、]", old)
                ln = re.match(r"^([A-D])[.．、]", new)
                if lo and (not ln or ln.group(1) != lo.group(1)):
                    errors.append(f"{name}/{f['id']}.options: 选项字母被改动")
                    continue
                opts[i] = new
                changed += 1
                continue
            text = str(q.get(f["field"], ""))
            if old not in text:
                errors.append(f"{name}/{f['id']}.{f['field']}: 找不到原文：{old[:40]}")
                continue
            q[f["field"]] = text.replace(old, new, 1)
            changed += 1
        drop = set()
        for d in ops["deletes"]:
            if d["id"] not in index:
                errors.append(f"{name}/{d['id']}: 要删除的题目不存在")
                continue
            drop.add(d["id"])
        if not changed and not drop:
            continue
        total_fixes += changed
        total_del += len(drop)
        print(f"{name}: 修改 {changed} 条，删除 {len(drop)} 条")
        for qid in sorted(drop):
            print(f"  - 删除 {qid}：{index[qid].get('stem', '')[:50]}")
        if apply:
            backup = ROOT / "备份" / f"知识点-校对-{stamp}"
            backup.mkdir(parents=True, exist_ok=True)
            if name not in backups:
                shutil.copy2(path, backup / name)
                backups[name] = True
            kept = [q for q in qs if q["id"] not in drop]
            path.write_text(json.dumps(kept, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\n合计修改 {total_fixes} 条，删除 {total_del} 条")
    if errors:
        print(f"未应用 {len(errors)} 条：")
        for e in errors[:40]:
            print("  ✗", e)
    if apply and backups:
        print(f"已写盘；备份 → {ROOT / '备份' / f'知识点-校对-{stamp}'}")
    elif not apply:
        print("（试运行，未写盘；加 --apply 生效）")


if __name__ == "__main__":
    main()
