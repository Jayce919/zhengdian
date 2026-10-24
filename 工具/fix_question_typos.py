#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复题库中明确的 OCR 错字、乱码题干与截断选项。

只做「原文可确定」的替换；写盘前自动备份。
用法：python 工具/fix_question_typos.py [--apply]
"""
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZT = ROOT / "政治刷题App" / "知识点" / "questions_zhenti.json"
HATS = ROOT / "政治刷题App" / "知识点" / "questions_hats.json"
BACKUP = ROOT / "备份"

STEM_REPLACE = {
    "q-zt-2022-15": "2021年9月27日至28日，中央人才工作会议在北京举行。中共中央总书记、国家主席、中央军委主席习近平出席会议并发表重要讲话，强调要坚持党管人才，坚持面向世界科技前沿、面向经济主战场、面向国家重大需求、面向人民生命健康，深入实施新时代人才强国战略，全方位培养、引进、用好人才，加快建设",
    "q-zt-2022-10": "大革命失败后，要不要坚持革命？如何坚持革命？这是摆在中国共产党面前的两个根本性的问题。党从残酷的现实中认识到，没有革命的武装就无法战胜武装的反革命，就无法夺取中国革命胜利，就无法改变中国人民和中华民族的命运，必须以武装的革命反对武装的反革命。南昌起义打响了武装反抗国民党反动派的第一枪，这是中国共产党",
    "q-zt-2016-18": "唐朝诗人张若虚《春江花月夜》中的“人生代代无穷已，江月年年只相似”两句诗蕴涵着时间一维性的哲理。下列诗句中蕴涵相同哲理的是",
}

OPTION_REPLACE = {
    "q-zt-2010-10": {
        "A": ("A. 实现了马克思主义同中国实际的", "A. 实现了马克思主义同中国实际的第二次结合"),
    },
    "q-zt-2012-29": {
        "B": (
            "B. 社会主义社会的基本矛盾仍然是生产关系和生产力之间、上层建筑和经济基础之间的",
            "B. 社会主义社会的基本矛盾仍然是生产关系和生产力之间、上层建筑和经济基础之间的矛盾",
        ),
    },
}

# 逐字段替换（题干、解析、选项）
FIELD_RULES = [
    (re.compile(r"井(?!冈山)"), "并"),
    (re.compile(r"随若"), "随着"),
    (re.compile(r"撩原"), "燎原"),
    (re.compile(r"涕湖"), "澎湖"),
    (re.compile(r"眭步"), "跬步"),
    (re.compile(r"堤高"), "提高"),
    (re.compile(r"戊戊"), "戊戌"),
    (re.compile(r"穷己"), "穷已"),
    (re.compile(r"有机构成为\s*41"), "有机构成为 4:1"),
    (re.compile(r"22020年"), "2020年"),
    (re.compile(r"生生态安全"), "生态安全"),
]

HAT_REPLACE = {
    "q-hat-065": ("标准答案：坚定中国特色社会主义文化自", "标准答案：坚定中国特色社会主义文化自信"),
    "q-hatcard-065": ("坚定中国特色社会主义文化自", "坚定中国特色社会主义文化自信"),
    "q-hat-092": ("标准答案：戊戊维新运动", "标准答案：戊戌维新运动"),
    "q-hatcard-092": ("戊戊维新运动", "戊戌维新运动"),
}


def fix_file(path, apply, backup_dir):
    bank = json.loads(path.read_text(encoding="utf-8"))
    by_id = {q["id"]: q for q in bank}
    changed = 0

    for qid, text in STEM_REPLACE.items():
        q = by_id.get(qid)
        if q and q["stem"] != text:
            q["stem"] = text
            changed += 1

    for qid, items in OPTION_REPLACE.items():
        q = by_id.get(qid)
        if not q:
            continue
        for letter, (old, new) in items.items():
            idx = next((i for i, o in enumerate(q["options"]) if o.startswith(letter + ".")), None)
            if idx is not None and q["options"][idx] == old:
                q["options"][idx] = new
                changed += 1

    for q in bank:
        for field in ("stem", "explain"):
            old = q.get(field, "")
            new = old
            for pat, repl in FIELD_RULES:
                new = pat.sub(repl, new)
            if new != old:
                q[field] = new
                changed += 1
        opts = q.get("options") or []
        for i, o in enumerate(opts):
            new = o
            for pat, repl in FIELD_RULES:
                new = pat.sub(repl, new)
            if new != o:
                opts[i] = new
                changed += 1

    for qid, pair in HAT_REPLACE.items():
        q = by_id.get(qid)
        if q and pair[0] in str(q.get("answer", "")):
            q["answer"] = q["answer"].replace(pair[0], pair[1])
            changed += 1
        if q and pair[0] in str(q.get("explain", "")):
            q["explain"] = q["explain"].replace(pair[0], pair[1])
            changed += 1

    print(f"{path.name}: 改动 {changed} 处")
    if apply:
        path.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def main():
    apply = "--apply" in sys.argv
    if apply:
        BACKUP.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dst = BACKUP / f"知识点-错字修复-{stamp}"
        dst.mkdir(parents=True)
        shutil.copy2(ZT, dst / ZT.name)
        shutil.copy2(HATS, dst / HATS.name)
        print(f"备份 → {dst}")
    total = fix_file(ZT, apply, None) + fix_file(HATS, apply, None)
    if not apply:
        print(f"合计 {total} 处（试运行，未写盘；加 --apply 生效）")
    else:
        print(f"合计 {total} 处，已写盘")


if __name__ == "__main__":
    main()
