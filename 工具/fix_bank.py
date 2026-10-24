#!/usr/bin/env python3
"""修正 知识点/ 下题库与知识点 JSON 的 OCR 噪声。

默认只试运行（dry-run），打印每类改动的数量与样例，不写任何文件。
加 --apply 才真正写盘，并在 备份/ 下留一份原始副本。

处理的噪声：
  1. 控制字符、零宽字符、不间断空格、换行/制表符
  2. PDF 页码标记（##P12、• 3 •）、题型标记（时政习题【多选题】）
  3. 汉字之间被行宽切断的空格、标点两侧空格
  4. 中文里的半角逗号/分号/冒号/问号/感叹号、半角括号与引号
  5. 重复标点（，，）、重复字（的的）
  6. 常见 OCR 错字（自已/自己、深人/深入、纳人/纳入、收人/收入…）
  7. 数字区间与算式里的“一”（2026一2030）
  8. 选项编号写法（A、/A．→ A.）
  9. 误粘进知识点的习题残片（时政习题、答案：、干扰选项）
"""
import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
SRC = BASE / "政治刷题App" / "知识点"
BACKUP_ROOT = BASE / "备份"

CJK = r"\u3400-\u4dbf\u4e00-\u9fff"
PUNCT_MAP = {",": "，", ";": "；", ":": "：", "?": "？", "!": "！"}

# 只在这些字段里清理“汉字之间的空格”；标题、出处、关键词、导图标签、引文保持原样
SPACE_KEYS = {"stem", "explain", "options", "why", "core", "detail", "diff", "content", "meaning", "summary"}
# 这些字段完全跳过（结构字段或人工排版过的短文本）
SKIP_KEYS = {"id", "partId", "pointId", "type", "subject", "answer", "trap", "source", "no", "refs", "keywords", "label"}

WORD_FIXES = [
    ("自已", "自己"),
    ("深人", "深入"),
    ("纳人", "纳入"),
    ("融人", "融入"),
    ("投人", "投入"),
    ("兩個", "两个"),
    ("政冶", "政治"),
    ("主乂", "主义"),
    ("马克恩", "马克思"),
    ("恩格思", "恩格斯"),
]

STATS = {}
SAMPLES = {}
CHANGED_PATHS = []
DETAIL = []


def bump(rule, before, after, path):
    STATS[rule] = STATS.get(rule, 0) + 1
    DETAIL.append({"rule": rule, "path": path, "before": before, "after": after})
    SAMPLES.setdefault(rule, [])
    if len(SAMPLES[rule]) < 4:
        SAMPLES[rule].append((path, before[:110], after[:110]))
    CHANGED_PATHS.append((path, rule))


def clean_common(s):
    s = s.replace("\u00a0", " ").replace("\u3000", " ")
    s = re.sub(r"[\u200b-\u200f\u202a-\u202e\ufeff]", "", s)
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", s)
    s = s.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    s = re.sub(r"•\s*\d+\s*•", "", s)
    s = s.replace("【试题解析】", "")
    s = re.sub(r"##P\d+", "", s)
    return s


def clean_spaces(s):
    # 汉字之间的空格是行宽切断的产物；保留拉丁词之间的空格
    s = re.sub(rf"(?<=[{CJK}])[ ]+(?=[{CJK}])", "", s)
    # 标点两侧的空格
    s = re.sub(rf"(?<=[{CJK}])[ ]+(?=[，。；：、！？”）《])", "", s)
    s = re.sub(rf"(?<=[，。；：、“（《])[ ]+(?=[{CJK}])", "", s)
    s = re.sub(r"[ ]{2,}", " ", s)
    return s.strip()


def fix_punct(s):
    s = s.replace("∶", "：").replace("︰", "：")
    s = re.sub(rf"(?<=[{CJK}])[,;:?!]", lambda m: PUNCT_MAP[m.group()], s)
    s = re.sub(rf"[,;:?!](?=[{CJK}])", lambda m: PUNCT_MAP[m.group()], s)
    s = re.sub(r"([，。；：、！？])\1+", r"\1", s)
    s = s.replace("。。。", "。").replace("......", "……").replace("...", "……")
    return s


def fix_parens(s):
    while True:
        new = re.sub(
            r"\(([^()]*)\)",
            lambda m: "（" + m.group(1) + "）" if re.search(f"[{CJK}]", m.group(1)) else m.group(0),
            s,
        )
        if new == s:
            break
        s = new
    s = re.sub(rf"(?<=[{CJK}》”])\s*\)", "）", s)
    s = re.sub(rf"\(\s*(?=[{CJK}])", "（", s)
    # 重复的右括号/左括号（OCR 常见“（三））”）
    while s.count("）") > s.count("（") and "））" in s:
        s = s.replace("））", "）", 1)
    while s.count("（") > s.count("）") and "（（" in s:
        s = s.replace("（（", "（", 1)
    # 结尾被截断的半个括号：“…（四”
    if s.count("（") > s.count("）"):
        s = re.sub(r"（[^（）]{0,4}$", "", s)
    return s


def fix_bracket_extras(s):
    # 多出来的书书名号
    while s.count("》") > s.count("《") and "》》" in s:
        s = s.replace("》》", "》", 1)
    # 半角开方括号 + 全角收方括号的常见 OCR 组合
    s = s.replace("[ 标准答案】", "【标准答案】").replace("（解析】", "【解析】")
    return s


def fix_ascii_quotes(s):
    prev = None
    while prev != s:
        prev = s
        s = re.sub(
            r'"([^"\n]{1,160})"',
            lambda m: "“" + m.group(1) + "”" if re.search(f"[{CJK}]", m.group(1)) else m.group(0),
            s,
        )
    # 落单的 ASCII 引号：贴在汉字段首/段尾时按中文引号处理
    s = re.sub(rf'^"([{CJK}])', r"“\1", s)
    s = re.sub(rf'([{CJK}])\"$', r"\1”", s)
    s = re.sub(rf'(?<=[。！？；：，、.])\s*"(?=[{CJK}])', "“", s)
    s = re.sub(rf'(?<=[{CJK}])"(?=$|[，。；：！？、])', "”", s)
    return s


def fix_quote_balance(s):
    """中文引号总是成对交替出现。

    只有在引号总数为偶数、且不含单引号时才按位置重排为 “…”；数量为奇数说明
    原文被截断或多出孤立的引号，交给报告人工处理，避免自动改错。
    """
    marks = [i for i, ch in enumerate(s) if ch in "“”"]
    if not marks or len(marks) % 2 != 0 or "’" in s:
        return s
    if s.count("“") == s.count("”"):
        return s
    chars = list(s)
    for n, idx in enumerate(marks):
        chars[idx] = "“" if n % 2 == 0 else "”"
    return "".join(chars)


def fix_words(s):
    for bad, good in WORD_FIXES:
        if bad in s:
            s = s.replace(bad, good)
    s = re.sub(r"收人(?![类民员才士口群家们])", "收入", s)
    # “千”是“于”的常见 OCR 误认：关千/由千/处千/在千…
    s = re.sub(r"(?<=[关由源高基立利当等处身对难生资铸便别用属位鉴趋归易善勇敢])千", "于", s)
    s = re.sub(r"在千(?![万秋年古载里帆杯篇])", "在于", s)
    s = re.sub(r"至千(?![里米瓦克斤元年])", "至于", s)
    s = s.replace("千部", "干部")
    return s


def fix_extra(s):
    s = s.replace("22026年", "2026年")
    s = re.sub(r"(?<=\d) (?=\d)", "", s)
    s = s.replace("so%", "50%").replace("B B C", "BBC")
    # 同一处重复的括号
    s = re.sub(r"[（(]{3,}", "（", s)
    s = re.sub(r"[）)]{3,}", "）", s)
    return s


LITERAL_FIXES = [
    ("中英((南京条约》", "中英《南京条约》"),
    ("牢记使命”昊】", "牢记使命”"),
    ("““", "“"),
    ("“十五五’", "“十五五”"),
    ("‘内卷式’竞争”", "“内卷式”竞争"),
    # 常见单字误认
    ("井不", "并不"),
    ("井且", "并且"),
    ("杜会", "社会"),
    ("于万工程", "千万工程"),
    ("丁＿人", "工人"),
    ("吃立", "屹立"),
    ("诡杆", "桅杆"),
    ("返歌", "讴歌"),
    ("炮晌", "炮响"),
    ("青截", "青藏"),
    ("弓引力", "引力"),
    ("统－", "统一"),
    ("每－", "每一"),
    ("五于多年", "五千多年"),
    ("發展", "发展"),
]


def fix_literals(s):
    for bad, good in LITERAL_FIXES:
        if bad in s:
            s = s.replace(bad, good)
    return s


def fix_glued_marker(s, key):
    """题干/选项里被粘上的“第X部分习题190”之类出处标记。"""
    if key in {"stem", "options", "explain"}:
        s = re.sub(r"\s*第?[一二三四五六七八九十]*部分?习题\s*\d+\s*$", "", s)
    return s


def fix_numbers(s):
    if re.search(r"\d[ ]?一[ ]?\d", s):
        # 有等号的是算式，用减号；否则是年份/数量区间，用破折号
        dash = "-" if "=" in s else "—"
        s = re.sub(r"(?<=\d)[ ]?一[ ]?(?=\d)", dash, s)
    return s


def fix_option_label(s):
    return re.sub(r"^([A-D])[、．.]\s*", r"\1. ", s)


def truncate_exercise(s):
    """去掉误粘进知识点的时政习题残片（从“时政习题【多选题】”开始整段不是考点内容）。"""
    for marker in ("时政习题", "【多选题】", "【单选题】"):
        idx = s.find(marker)
        if idx == 0:
            return ""
        if idx > 0:
            s = s[:idx]
    return s.strip()


def process(path, key, s):
    orig = s
    s = clean_common(s)
    if key in SKIP_KEYS:
        if s != orig:
            bump("控制字符/标记", orig, s, path)
        return s

    s2 = fix_literals(s)
    if s2 != s:
        bump("指定替换", s, s2, path)
    s = s2

    s2 = truncate_exercise(s)
    if s2 != s:
        bump("习题残片", s, s2, path)
    s = s2

    if key in SPACE_KEYS:
        s2 = clean_spaces(s)
        if s2 != s:
            bump("空格", s, s2, path)
        s = s2

    s2 = fix_punct(s)
    if s2 != s:
        bump("半角标点", s, s2, path)
    s = s2

    # 半角逗号变全角后会留下“， 西”这样的空格，再清一遍
    if key in SPACE_KEYS:
        s2 = clean_spaces(s)
        if s2 != s:
            bump("空格", s, s2, path)
        s = s2

    s2 = fix_parens(s)
    if s2 != s:
        bump("括号", s, s2, path)
    s = s2

    s2 = fix_bracket_extras(s)
    if s2 != s:
        bump("多余括号", s, s2, path)
    s = s2

    s2 = fix_ascii_quotes(s)
    if s2 != s:
        bump("ASCII 引号", s, s2, path)
    s = s2

    s2 = fix_quote_balance(s)
    if s2 != s:
        bump("引号配对", s, s2, path)
    s = s2

    s2 = fix_words(s)
    if s2 != s:
        bump("错字", s, s2, path)
    s = s2

    s2 = fix_numbers(s)
    if s2 != s:
        bump("数字区间", s, s2, path)
    s = s2

    s2 = fix_extra(s)
    if s2 != s:
        bump("其他噪声", s, s2, path)
    s = s2

    s2 = fix_glued_marker(s, key)
    if s2 != s:
        bump("粘连出处", s, s2, path)
    s = s2

    if key == "options":
        s2 = fix_option_label(s)
        if s2 != s:
            bump("选项编号", s, s2, path)
        s = s2

    if s.strip() == "" and orig.strip() != "":
        bump("清空待人工", orig, s, path)
    return s


def walk(obj, path, key, handler):
    if isinstance(obj, dict):
        return {k: walk(v, f"{path}.{k}", k, handler) for k, v in obj.items()}
    if isinstance(obj, list):
        return [walk(v, f"{path}[{i}]", key, handler) for i, v in enumerate(obj)]
    if isinstance(obj, str):
        return handler(path, key, obj)
    return obj


def load(p):
    raw = p.read_bytes()
    text = raw.decode("utf-8")
    return json.loads(text), raw

def dump_like(data, original_raw, p):
    crlf = b"\r\n" in original_raw
    text = json.dumps(data, ensure_ascii=False, indent=1)
    if crlf:
        text = text.replace("\n", "\r\n")
    if original_raw.endswith(b"\n"):
        text += "\r\n" if crlf else "\n"
    p.write_bytes(text.encode("utf-8"))


POINT_CORE_FIX = {
    "shizheng-03-07": "《关于更高水平更高质量做好节能降碳工作的意见》从健全法律法规、完善标准标识体系、"
    "强化政策支撑、加强技术创新应用、提升基础工作能力五个方面，强化节能降碳的支撑保障。",
}

QUIZ_HINT = re.compile(r"答案[：:]|干扰选项|^选项[ABCD]")


def is_quiz_detail(s):
    if QUIZ_HINT.search(s):
        return True
    return len(re.findall(r"[ABCD][.．]", s)) >= 2


def post_part(part, path):
    """知识点数据：改写被习题顶掉的 core，删掉整条都是习题的 detail。"""
    for pt in part.get("points", []):
        pid = pt.get("id", "")
        if pid in POINT_CORE_FIX:
            old = pt.get("core", "")
            pt["core"] = POINT_CORE_FIX[pid]
            bump("知识点改写", old, pt["core"], f"{path}.{pid}.core")
        detail = pt.get("detail")
        if isinstance(detail, list):
            kept = []
            for d in detail:
                if not d.strip() or is_quiz_detail(d):
                    bump("删除习题残片", d, "", f"{path}.{pid}.detail")
                else:
                    kept.append(d)
            pt["detail"] = kept
    return part


def files_to_fix():
    out = []
    out += sorted((SRC / "parts").glob("*.json"))
    out += [p for p in sorted(SRC.glob("questions*.json")) if not p.name.startswith("_")]
    out += [SRC / "timeline.json", SRC / "mindmaps.json"]
    return [p for p in out if p.exists()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dump", help="把每条前后对照写入该文件（JSONL）")
    args = ap.parse_args()

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_ROOT / f"知识点-{stamp}"
    total_changed = 0

    for p in files_to_fix():
        data, raw = load(p)
        before = json.dumps(data, ensure_ascii=False, sort_keys=True)
        data2 = walk(data, p.name, "", process)
        if p.parent == SRC / "parts":
            data2 = post_part(data2, p.name)
        after = json.dumps(data2, ensure_ascii=False, sort_keys=True)
        if before == after:
            continue
        total_changed += 1
        if args.apply:
            backup.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, backup / p.name)
            dump_like(data2, raw, p)

    print(f"文件：{len(files_to_fix())} 个，其中需要改动 {total_changed} 个")
    print(f"字符串改动分类：")
    for rule, n in sorted(STATS.items(), key=lambda x: -x[1]):
        print(f"  {rule}: {n}")
        for path, b, a in SAMPLES[rule]:
            print(f"     {path}")
            print(f"       前: {b}")
            print(f"       后: {a}")
    if not args.apply:
        print("\n（试运行，未写入。加 --apply 执行）")
    else:
        print(f"\n已备份原始文件到：{backup}")
        print("已写回源文件。")

    if args.dump:
        with open(args.dump, "w", encoding="utf-8") as fh:
            for row in DETAIL:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"改动明细已写入：{args.dump}")


if __name__ == "__main__":
    main()
