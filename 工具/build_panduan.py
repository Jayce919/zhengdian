#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成「判断」题库：书本定义 + 常见错误表述，全部来自知识点与背诵手册。

每道题一句表述 + 对/错：
- 正确表述：考点的 core，开头与标题重复时替换成完整标题，拼成陈述句
- 错误表述：questions_judge2 的成对混淆、questions_judge 的经典干扰项
  （都来自背诵手册，不用真题选项，保证这一板块考的是书本定义）

输出：知识点/questions_panduan.json（type=judge）
用法：
  python 工具/build_panduan.py            # 试运行，打印统计与可疑语句
  python 工具/build_panduan.py --apply    # 写盘（先备份）
"""
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PARTS = ROOT / "政治刷题App" / "知识点" / "parts"
OUT = ROOT / "政治刷题App" / "知识点" / "questions_panduan.json"
OVERRIDE_FILE = ROOT / "政治刷题App" / "工具" / "panduan_overrides.json"

SUBJECTS = ["mayuan", "maozhongte", "xisixiang", "shigang", "sifa"]

# 自动规则处理不好的考点：人工改写成陈述句
OVERRIDES = {
    "mayuan-01-11": "《法兰西内战》总结了巴黎公社的经验，《哥达纲领批判》对未来社会作了原则构想，《反杜林论》全面阐述了马克思主义理论体系。",
    "mayuan-02-19": "物质与运动不可分割，脱离运动看问题会陷入形而上学，脱离物质谈运动则陷入唯心主义。",
    "mayuan-02-22": "否认运动、把静止绝对化会陷入形而上学不变论，否认静止、借口绝对运动则导致相对主义诡辩论。",
    "mayuan-09-03": "六大思维能力包括辩证思维、历史思维、系统思维、战略思维、底线思维和创新思维。",
    "mayuan-22-06": "价值源于抽象劳动，使用价值源于具体劳动，剩余价值源于剩余劳动。",
    "mayuan-26-08": "当代资本主义的新变化没有改变资本主义制度的本质，没有克服资本主义的基本矛盾，也没有改变马克思主义基本论断的科学性。",
    "maozhongte-04-20": "确立社会主义基本制度是最深刻最伟大的社会变革，为当代中国一切发展进步奠定了制度基础，实现了中华民族命运的根本扭转，使劳动人民成为国家主人。",
    "xi-07-12": "新发展格局是开放的国内国际双循环，不是封闭的单循环；以全国统一大市场基础上的国内大循环为主体，不是各地自我小循环。",
}

VERB = re.compile(
    r"(是|指|在于|包括|决定|表明|说明|体现|标志|成为|具有|必须|应该|能够|不能|没有|属于|源于|取决于|等于|构成|形成|产生|导致|要求|意味着)"
)


def to_statement(title: str, core: str) -> str:
    s = core.strip().rstrip("。")
    if s.startswith(title):
        return s + "。"
    best = ""
    for n in range(min(len(title), len(s)), 1, -1):
        head = s[:n]
        if title.endswith(head):
            best = head
            break
    if best:
        return (title + s[len(best):]).strip("：:，, ") + "。"
    m = re.match(r"^([^：:]{1,8})[：:](.+)$", s)
    if m and len(m.group(1)) <= 4:
        return f"{title}是{m.group(2)}。"
    return s + "。"


def suspicious(stmt: str) -> str:
    body = stmt.rstrip("。")
    if len(body) < 12:
        return "过短"
    if body.count("；") >= 2:
        return "多重分句"
    if not VERB.search(body):
        return "无谓语"
    return ""


def norm(text: str) -> str:
    return re.sub(r"[\s，。、“”‘’；：？！,.;:?!\"'（）()]", "", text)


def false_id(stem: str, used: set) -> str:
    """按表述内容取哈希：重生成题库、增删条目都不会让旧进度对错题。"""
    key = norm(stem)
    for n in (10, 14, 18):
        qid = f"q-pd-f-{hashlib.sha1(key.encode('utf-8')).hexdigest()[:n]}"
        if qid not in used:
            return qid
    raise RuntimeError(f"哈希冲突：{stem}")


def load_points():
    pts = []
    for subj in SUBJECTS:
        for p in sorted(PARTS.glob(f"{subj}-*.json")):
            d = json.loads(p.read_text(encoding="utf-8"))
            for pt in d.get("points", []):
                pts.append((subj, d["id"], pt))
    return pts


def strip_judge(stem: str) -> str:
    return re.sub(r"^判断[：:]\s*", "", stem).strip()


def load_overrides():
    """人工校对后的表述/解析覆盖：{原判断题 id: {stem/explain}}"""
    if not OVERRIDE_FILE.exists():
        return {}
    return json.loads(OVERRIDE_FILE.read_text(encoding="utf-8"))


def load_wrong(point_by_id, overrides):
    out, seen = [], set()

    def add(stem, explain, subject, part_id, refs, point_id=None, answer=False, qid=None):
        ov = overrides.get(qid or "", {})
        stem = ov.get("stem", stem).strip()
        explain = ov.get("explain", explain)
        if not stem.endswith("。"):
            stem += "。"
        key = norm(stem)
        if not key or key in seen:
            return
        if qid not in overrides and (
            len(stem) < 12
            or re.match(r"^[是的了而即并或与和]", stem)
            or re.match(
                r"^(取决于|能够|可以|表明|说明|意味着|标志着|体现了|反映了|表现为|具有|包括|主张|坚持|否认|认为|强调|属于|源于|构成|形成|产生|导致|要求)",
                stem,
            )
            or re.search(r"[①②③④⑤⑥⑦⑧⑨⑩]", stem)
        ):
            return
        seen.add(key)
        out.append(
            {
                "stem": stem,
                "explain": explain,
                "subject": subject,
                "partId": part_id,
                "refs": refs,
                "pointId": point_id,
                "answer": answer,
                "qid": qid,
            }
        )

    # 1) 成对混淆：q-cj-mayuan-01-01-0 → 考点 mayuan-01-01
    j2 = json.loads((ROOT / "政治刷题App" / "知识点" / "questions_judge2.json").read_text(encoding="utf-8"))
    for q in j2:
        pid = re.sub(r"^q-cj-", "", q["id"]).rsplit("-", 1)[0]
        pt = point_by_id.get(pid)
        explain = q.get("explain", "").rstrip("。") + "。"
        if pt:
            explain += f"正确表述：{pt['core'].rstrip('。')}。"
        add(
            strip_judge(q["stem"]),
            explain,
            (pt and pt["_subject"]) or q.get("subject", ""),
            (pt and pt["_partId"]) or q.get("partId", ""),
            q.get("refs", []),
            pid,
            qid=q["id"],
        )

    # 2) 经典干扰项
    j1 = json.loads((ROOT / "政治刷题App" / "知识点" / "questions_judge.json").read_text(encoding="utf-8"))
    for q in j1:
        add(
            strip_judge(q["stem"]),
            q.get("explain", "").rstrip("。") + "。该表述与教材相反。",
            q.get("subject", ""),
            q.get("partId", ""),
            q.get("refs", []),
            qid=q["id"],
        )
    # 3) 其他题库里的旧判断题（题干带“判断：”），答案可能是对也可能是错
    for f in sorted((ROOT / "政治刷题App" / "知识点").glob("questions*.json")):
        if f.name in ("questions_judge.json", "questions_judge2.json", "questions_panduan.json", "questions_cardjudge.json"):
            continue
        for q in json.loads(f.read_text(encoding="utf-8")):
            if q.get("type") != "judge":
                continue
            add(
                strip_judge(q["stem"]),
                q.get("explain", "").rstrip("。") + "。",
                q.get("subject", ""),
                q.get("partId", ""),
                q.get("refs", []),
                q.get("pointId"),
                answer=bool(q.get("answer")),
                qid=q["id"],
            )
    return out


def main():
    apply = "--apply" in sys.argv
    pts = load_points()
    point_by_id = {
        pt["id"]: {**pt, "_subject": subj, "_partId": pid} for subj, pid, pt in pts
    }

    overrides = load_overrides()
    true_items, flags = [], []
    for subj, part_id, pt in pts:
        ov = overrides.get(f"q-pd-t-{pt['id']}", {})
        stmt = ov.get("stem") or OVERRIDES.get(pt["id"]) or to_statement(pt["title"], pt["core"])
        why = "" if ov else suspicious(stmt)
        if why:
            flags.append((pt["id"], why, stmt))
        true_items.append(
            {
                "id": f"q-pd-t-{pt['id']}",
                "type": "judge",
                "subject": subj,
                "partId": part_id,
                "pointId": pt["id"],
                "stem": stmt,
                "answer": True,
                "explain": ov.get("explain") or f"{pt['core'].rstrip('。')}。{pt.get('quote', '')}".strip(),
                "refs": pt.get("refs", []),
                "source": "panduan",
            }
        )

    true_norm = {norm(x["stem"]) for x in true_items}
    wrong = [w for w in load_wrong(point_by_id, overrides) if norm(w["stem"]) not in true_norm]

    wrong_items, used = [], set()
    for w in wrong:
        qid = w["qid"] or false_id(w["stem"], used)
        used.add(qid)
        item = {
            "id": qid,
            "type": "judge",
            "subject": w["subject"],
            "partId": w["partId"],
            "stem": w["stem"],
            "answer": w["answer"],
            "explain": w["explain"],
            "refs": w["refs"],
            "source": "panduan",
        }
        if w["pointId"]:
            item["pointId"] = w["pointId"]
        wrong_items.append(item)

    items = true_items + wrong_items
    ids = [x["id"] for x in items]
    assert len(ids) == len(set(ids)), "id 重复"

    from collections import Counter

    print(f"正确表述 {len(true_items)} 条，错误表述 {len(wrong_items)} 条，合计 {len(items)}")
    print("按学科：", dict(Counter(x["subject"] for x in items)))
    print(f"可疑语句 {len(flags)} 条（前 15 条）：")
    for pid, why, stmt in flags[:15]:
        print(f"  [{why}] {pid} → {stmt}")

    if not apply:
        print("\n（试运行，未写盘；加 --apply 写入）")
        return

    backup = ROOT / "备份" / f"知识点-判断-{datetime.now():%Y%m%d-%H%M%S}"
    backup.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        shutil.copy2(OUT, backup / OUT.name)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"已写入 {OUT}（{len(items)} 条）；备份 → {backup}")


if __name__ == "__main__":
    main()
