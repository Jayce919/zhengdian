#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修正 2020 年第 4 题的编号错位。

题库原来的 q-zt-2020-04 存的是第 14 题（爱国主义本质），题干、选项、答案都对，
只是 id 与 refs 写成了第 4 题。本脚本把它改名为 q-zt-2020-14，并更新 refs；
真正的第 4 题（列宁一国胜利论）由 工具/zhenti_new/batch_2020_q04.json 另行补入。

幂等：已经是 q-zt-2020-14 且 q-zt-2020-04 不存在时直接退出。
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "政治刷题App" / "知识点" / "questions_zhenti.json"
OLD, NEW = "q-zt-2020-04", "q-zt-2020-14"
STEM_HEAD = "习近平在纪念五四运动"


def main():
    qs = json.loads(BANK.read_text(encoding="utf-8"))
    ids = {q["id"] for q in qs}
    if NEW in ids and OLD not in ids:
        print("已是修正后状态，无需处理")
        return
    assert OLD in ids, f"找不到 {OLD}"
    assert NEW not in ids, f"{NEW} 已存在，拒绝覆盖"
    q = next(x for x in qs if x["id"] == OLD)
    assert q["stem"].startswith(STEM_HEAD), "题干不是第 14 题（爱国主义），中止"
    assert "第4题" in " ".join(q.get("refs", [])), "refs 不含第4题，中止"

    q["id"] = NEW
    q["refs"] = ["2020年考研政治真题 第14题"]
    qs.sort(key=lambda x: x["id"])

    backup = ROOT / "备份" / f"知识点-2020错位修复-{datetime.now():%Y%m%d-%H%M%S}"
    backup.mkdir(parents=True, exist_ok=True)
    shutil.copy2(BANK, backup / BANK.name)

    BANK.write_text(json.dumps(qs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已改名 {OLD} → {NEW}，共 {len(qs)} 题；备份 → {backup}")


if __name__ == "__main__":
    main()
