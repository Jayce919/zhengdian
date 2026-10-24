#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""修复真题选项的 OCR 截断与缺字（只改选项文本，不动答案、顺序、id）。

每题先断言旧文本存在，避免误改；--apply 前自动备份。
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
    "q-zt-2011-18": {
        "A": ("A. 通过", "A. 通过“参与制”实现其在经济领域中的统治"),
        "B": ("B. 通过同政府的", "B. 通过同政府的“个人联合”实现其对国家机器的控制"),
    },
    "q-zt-2012-18": {
        "C": ("C. 把经济作为社会的", "C. 把经济作为社会的“基础”而否认其他社会因素的作用"),
    },
    "q-zt-2013-04": {
        "D": (
            "D. 125% S. 当今世界是开放的世界，中国的发展离不开世界，实行对外开放是我国的一项基本国策。坚",
            "D. 125%",
        ),
    },
    "q-zt-2023-04": {
        "C": ("C. 断低价", "C. 垄断低价"),
    },
    "q-zt-2015-07": {
        "C": ("C. 实现", "C. 实现城镇基本公共服务常住人口全覆盖"),
    },
    "q-zt-2017-06": {
        "D": ("D. 推进", "D. 推进“三去一降一补”"),
    },
    "q-zt-2019-25": {
        "B": ("B. 把坚持", "B. 把坚持“一国”原则和尊重“两制”差异有机结合起来"),
    },
    "q-zt-2016-30": {
        "A": (
            "A. 法治体系不仅有法律规范体系，还包括法治实施体系、法治监督体系、法治保障体系和党",
            "A. 法治体系不仅有法律规范体系，还包括法治实施体系、法治监督体系、法治保障体系和党内法规体系",
        ),
    },
    "q-zt-2013-30": {
        "C": ("C. 标志着马克思主义同中国实际", "C. 标志着马克思主义同中国实际第二次结合已经完成"),
    },
    "q-zt-2020-31": {
        "A": ("A. 开启了我国太空站建设的序幕", "A. 权利行使的目的要正当"),
    },
    "q-zt-2018-28": {
        "A": ("A. 抗日民主政府在工作人员分配上实行", "A. 抗日民主政府在工作人员分配上实行“三三制”原则"),
    },
    "q-zt-2014-10": {
        "D": ("D. 把民生主义概括为", "D. 把民生主义概括为“平均地权”和“节制资本”"),
    },
    "q-zt-2023-10": {
        "A": ("A. 批评了大革命后期存在的", "A. 批评了大革命后期存在的“左”倾错误"),
    },
    "q-zt-2024-09": {
        "D": ("D. 对共同生活地域的认", "D. 对共同生活地域的认同"),
    },
    "q-zt-2023-32": {
        "A": (
            "A. 揭批",
            "A. 揭批“台独”分裂势力和外部势力勾连挑衅，企图损害中国主权和领土完整、阻挠破坏中国统一进程的恶劣言行",
        ),
        "C": (
            "C. 展现中国共产党和中国政府愿继续以最大诚意、尽最大努力争取和平统一的立场和",
            "C. 展现中国共产党和中国政府愿继续以最大诚意、尽最大努力争取和平统一的立场和态度",
        ),
        "D": (
            "D. 提振全党全国各族人民矢志追求国家统一的精气神，增强岛内和海外反·“独”促统力",
            "D. 提振全党全国各族人民矢志追求国家统一的精气神，增强岛内和海外反“独”促统力量的信心和勇气",
        ),
    },
}


def main():
    apply = "--apply" in sys.argv
    questions = json.loads(BANK.read_text(encoding="utf-8"))
    by_id = {q["id"]: q for q in questions}
    changed = 0
    errors = []

    for qid, items in FIXES.items():
        q = by_id.get(qid)
        if q is None:
            errors.append(f"{qid}: 题目不存在")
            continue
        for letter, (old, new) in items.items():
            idx = next((i for i, o in enumerate(q["options"]) if o.startswith(f"{letter}.")), None)
            if idx is None:
                errors.append(f"{qid}: 找不到选项 {letter}")
            elif q["options"][idx] == new:
                print(f"· {qid}.{letter}: 已是修复后的文本，跳过")
            elif q["options"][idx] != old:
                errors.append(f"{qid}.{letter}: 原文不符 → {q['options'][idx]!r}")
            else:
                q["options"][idx] = new
                changed += 1
                print(f"✓ {qid}.{letter}: {old!r} → {new!r}")

    # 答案必须仍落在选项字母内
    for q in questions:
        if q["type"] not in ("single", "multi"):
            continue
        letters = [o.strip()[0] for o in q["options"]]
        right = [q["answer"]] if isinstance(q["answer"], str) else q["answer"]
        for r in right:
            if r not in letters:
                errors.append(f"{q['id']}: 答案 {r} 不在选项内")

    if errors:
        print("\n".join("✗ " + e for e in errors))
        sys.exit(1)
    print(f"共修改 {changed} 个选项")

    if not apply:
        print("（试运行，未写盘；加 --apply 生效）")
        return

    BACKUP.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = BACKUP / f"知识点-真题选项修复-{stamp}"
    dst.mkdir(parents=True)
    shutil.copy2(BANK, dst / BANK.name)
    BANK.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写盘；备份 → {dst}")


if __name__ == "__main__":
    main()
