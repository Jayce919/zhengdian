#!/usr/bin/env python3
"""扫描 知识点/ 下的题库与知识点 JSON，找出 OCR 残留的错字、空白、标点问题。

只读，不改任何文件；输出按类别统计与样例。

用法：
    python 工具/bank_audit.py            # 统计 + 每类 3 条样例
    python 工具/bank_audit.py --samples 10
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
SRC = BASE / "政治刷题App" / "知识点"
SAMPLES = 3
if "--samples" in sys.argv:
    SAMPLES = int(sys.argv[sys.argv.index("--samples") + 1])

CJK = r"\u3400-\u4dbf\u4e00-\u9fff"
HALF_PUNCT = ",;:?!"
# 只统计“人工排版字段之外”的文本
SKIP_PATH = (".refs[", ".title", ".label", ".no", ".keywords", ".name", ".short", ".summary")

TRAD = set("與這個為經濟發會學國時對開關實現應該麼樣問題認識運動變歷係"
           "產階級門爭專義設馬澤東鄧從來黨員幹軍隊戰勝敗驗訓總結論觀點踐檢錯誤辯證築態礎臺灣華僑歐亞際織聯")

LOOKALIKE = set("乂亍丬冃冐卩彐丶丿乀乁亅")

CONFUSION = [
    ("千/于", r"(?:关|由|处|等|对|至|用|基|属|位|鉴|趋|归|在|难|源|易|善|勇|敢)千|千部"),
    ("人/入", r"(?:收|深|纳|融|投)人(?![类民员才士口群家们])"),
    ("己/已", r"自已"),
    ("井/并", r"井[不且非]"),
    ("杜/社", r"杜会"),
]

CATS = defaultdict(list)
COUNTS = Counter()
TOTAL_STR = 0
TOTAL_CHARS = 0


def walk(obj, path, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            walk(v, f"{path}.{k}", out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            walk(v, f"{path}[{i}]", out)
    elif isinstance(obj, str):
        out.append((path, obj))


def note(cat, path, text, m=None):
    COUNTS[cat] += 1
    if len(CATS[cat]) < SAMPLES:
        snippet = text if len(text) <= 90 else text[:90] + "…"
        extra = f" «{m.group(0)}»" if m else ""
        CATS[cat].append(f"{path}{extra}\n      {snippet}")


def check_string(path, s):
    global TOTAL_STR, TOTAL_CHARS
    TOTAL_STR += 1
    TOTAL_CHARS += len(s)

    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", s):
        note("控制字符", path, s)
    if re.search(r"[\u200b-\u200f\u202a-\u202e\ufeff]", s):
        note("零宽字符", path, s)
    if "\u00a0" in s or "\u3000" in s:
        note("异常空格", path, s)

    if any(k in path for k in SKIP_PATH):
        return

    for m in re.finditer(rf"(?<=[{CJK}])[ ]+(?=[{CJK}])", s):
        note("汉字间空格", path, s, m)
    for m in re.finditer(rf"[{CJK}][ ]+[，。；：、！？]|[，。；：、！？][ ]+[{CJK}]", s):
        note("标点旁空格", path, s, m)
    for m in re.finditer(rf"(?<=[{CJK}])[{re.escape(HALF_PUNCT)}]|[{re.escape(HALF_PUNCT)}](?=[{CJK}])", s):
        note("半角标点", path, s, m)
    for m in re.finditer(r"([，。；：、！？])\1+", s):
        note("重复标点", path, s, m)
    if re.search(r'"', s) and re.search(f"[{CJK}]", s):
        note("英文引号", path, s)
    if s.count("“") != s.count("”"):
        note("引号不配对", path, s)
    if s.count("《") != s.count("》"):
        note("书名号不配对", path, s)
    if s.count("【") != s.count("】"):
        note("方括号不配对", path, s)
    if s.count("（") != s.count("）"):
        note("中文括号不配对", path, s)
    for op, cl in (("（", "）"), ("(" , ")"), ("《", "》")):
        if s.count(op) != s.count(cl):
            break

    bad_trad = [c for c in s if c in TRAD]
    if bad_trad:
        note("繁体字", path, s)
    if any(c in LOOKALIKE for c in s):
        note("疑似形近符号", path, s)
    for name, pat in CONFUSION:
        if re.search(pat, s):
            note(f"混淆 {name}", path, s, re.search(pat, s))

    if re.search(r"##P\d+|时政习题|【(单选题|多选题|判断题)】", s):
        note("页码/习题标记", path, s)
    if re.search(r"(?<!标准)答案[：:]|干扰选项|^选项[ABCD]", s):
        note("习题残片", path, s)
    if "\u3000" in s:
        note("全角空格", path, s)
    if s != s.strip():
        note("首尾空白", path, s)


def main():
    files = []
    subjects_dir = SRC / "subjects"
    parts_dir = SRC / "parts"
    if subjects_dir.exists():
        files += sorted(subjects_dir.glob("*.json"))
    if parts_dir.exists():
        files += sorted(parts_dir.glob("*.json"))
    files += [p for p in sorted(SRC.glob("questions*.json")) if not p.name.startswith("_")]
    files += [SRC / "timeline.json", SRC / "mindmaps.json"]
    single = SRC / "subjects.json"
    if single.exists():
        files.append(single)

    for f in files:
        try:
            data = json.loads(f.read_text("utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"!! 读取失败 {f.name}: {e}")
            continue
        out = []
        walk(data, f.name, out)
        for path, text in out:
            check_string(path, text)

    print(f"扫描 {len(files)} 个文件，{TOTAL_STR} 个字符串，{TOTAL_CHARS} 字\n")
    if not COUNTS:
        print("没有发现残留问题。")
        return
    for cat, n in COUNTS.most_common():
        print(f"■ {cat}: {n}")
        for sample in CATS[cat]:
            print("    " + sample)
        print()


if __name__ == "__main__":
    main()
