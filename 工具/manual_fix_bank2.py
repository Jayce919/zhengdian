#!/usr/bin/env python3
"""人工校订第二批：补全最后 7 处引号问题。

用法：python 工具/manual_fix_bank2.py [--apply]
"""
import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
SRC = BASE / "政治刷题App" / "知识点"
BACKUP = BASE / "备份"

# (题目 id, 字段, 原文, 改为)
EDITS = [
    ("q-shizheng-multi-112", "stem",
     "深入整治“内卷式”竞争。之所以", "深入整治“内卷式”竞争。”之所以"),
    ("q-zt-2018-14", "stem", "一段话： ＂一次不公正的审判", "一段话：“一次不公正的审判"),
    ("q-zt-2019-03", "explain", "“物质生活\"'B选项中的", "“物质生活”，B选项中的"),
    ("q-zt-2019-10", "explain", "D“开滦五矿工人罢工””发生于", "D“开滦五矿工人罢工”发生于"),
    ("q-zt-2022-12", "explain", "找出在中国怎样建设社会主义的道",
     "找出在中国怎样建设社会主义的道路。”"),
    ("q-zt-2023-14", "stem", "推进国家各方面工作法治化。坚持全面依法治国",
     "推进国家各方面工作法治化。”坚持全面依法治国"),
    ("q-zt-2026-18", "stem", "培育出能地下结土豆、地上长番茄”的新型作物",
     "培育出能“地下结土豆、地上长番茄”的新型作物"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    path = SRC / "questions_zhenti.json"
    data = json.loads(path.read_text("utf-8"))
    shizheng_path = SRC / "questions_shizheng.json"
    shizheng = json.loads(shizheng_path.read_text("utf-8"))
    by_id = {q["id"]: q for q in data}
    by_id.update({q["id"]: q for q in shizheng})

    for qid, field, old, new in EDITS:
        q = by_id.get(qid)
        if q is None or old not in q[field]:
            raise SystemExit(f"未命中：{qid}.{field} {old[:30]}")
        q[field] = q[field].replace(old, new, 1)

    print(f"命中 {len(EDITS)} 处")
    if not args.apply:
        print("（试运行，加 --apply 写盘）")
        return

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP / f"知识点-人工校订2-{stamp}"
    backup.mkdir(parents=True, exist_ok=True)
    for p, obj in ((path, data), (shizheng_path, shizheng)):
        shutil.copy2(p, backup / p.name)
        p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("已备份到", backup)


if __name__ == "__main__":
    main()
