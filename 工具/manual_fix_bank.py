#!/usr/bin/env python3
"""人工校订：修掉无法自动处理、但依据考研政治常识可以确定原文的条目。

每条操作都断言目标文本存在，跑完打印改动数量；写盘前备份。
用法：python 工具/manual_fix_bank.py [--apply]
"""
import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
SRC = BASE / "政治刷题App" / "知识点"
BACKUP = BASE / "备份"

EDITS = []          # (file, id, field, old, new)
SETS = []           # (file, id, field, value)
DELETES = []        # (file, id)
POINT_SETS = []     # (file, pid, field, value)
POINT_EDITS = []    # (file, pid, field, index_or_None, old, new)
COUNT = {"edit": 0, "set": 0, "delete": 0, "point": 0}


def q_edit(f, i, field, old, new):
    EDITS.append((f, i, field, old, new))


def q_set(f, i, field, value):
    SETS.append((f, i, field, value))


def q_del(f, i):
    DELETES.append((f, i))


def p_set(f, pid, field, value):
    POINT_SETS.append((f, pid, field, value))


def p_edit(f, pid, field, idx, old, new):
    POINT_EDITS.append((f, pid, field, idx, old, new))


# ---------------- 时政单选题 / 多选题 ----------------
q_edit("questions_shizheng.json", "q-shizheng-single-006", "options", "D. “坚持健全上下贯通、执行有力的组织体系",
       "D. “坚持健全上下贯通、执行有力的组织体系”")
q_set("questions_shizheng.json", "q-shizheng-single-010", "stem",
      "2026年1月，在省部级主要领导干部学习贯彻党的二十届四中全会精神专题研讨班开班式上，"
      "习近平总书记深刻指出：“‘十五五’开局之年，无论是制定规划还是部署实施，都需要有正确的政绩观。"
      "省市县乡领导班子将陆续换届，强调政绩观也很有针对性。”树立和践行正确政绩观的重要抓手是")
q_edit("questions_shizheng.json", "q-shizheng-single-025", "options", "A. 北京非首都功能疏解集中承载地：",
       "A. 北京非首都功能疏解集中承载地")
q_edit("questions_shizheng.json", "q-shizheng-single-025", "options", "B. 全面深化改革开放试验区吴】",
       "B. 全面深化改革开放试验区")
q_edit("questions_shizheng.json", "q-shizheng-single-037", "stem", "大会的主题是共创未来”", "大会的主题是“共创未来”")
q_edit("questions_shizheng.json", "q-shizheng-single-037", "options", "A. “智能伙伴", "A. “智能伙伴”")
q_edit("questions_shizheng.json", "q-shizheng-multi-035", "stem",
       "做得好、做得坏，贡献大、贡献小，青史可鉴啊！”这启示我们",
       "“做得好、做得坏，贡献大、贡献小，青史可鉴啊！”这启示我们")
q_edit("questions_shizheng.json", "q-shizheng-multi-042", "stem", "我国提】 的优势将更加彰显", "我国的优势将更加彰显")
q_edit("questions_shizheng.json", "q-shizheng-multi-052", "options", "B. 减污”", "B. 减污")
q_edit("questions_shizheng.json", "q-shizheng-multi-063", "options", "B. 科技创新的“催化剂”、制造价值的“倍增器",
       "B. 科技创新的“催化剂”、制造价值的“倍增器”")
q_edit("questions_shizheng.json", "q-shizheng-multi-068", "options", "C. 坚持好完善好运行好人民代表大会制度的现实需要最】",
       "C. 坚持好完善好运行好人民代表大会制度的现实需要")
q_edit("questions_shizheng.json", "q-shizheng-multi-090", "options", "B. 提升开发式帮扶效能摄】",
       "B. 提升开发式帮扶效能")
q_edit("questions_shizheng.json", "q-shizheng-multi-098", "stem", "疏解集中晨】 承载地", "疏解集中承载地")
q_edit("questions_shizheng.json", "q-shizheng-multi-106", "stem", "在晨】 海南商业航天发射场", "在海南商业航天发射场")
q_edit("questions_shizheng.json", "q-shizheng-multi-112", "stem", "“深入整治‘内卷式竞争", "“深入整治‘内卷式’竞争")
q_edit("questions_shizheng.json", "q-shizheng-multi-112", "stem", "加强反断、反不正当竞争", "加强反垄断、反不正当竞争")
q_edit("questions_shizheng.json", "q-shizheng-multi-121", "options", "B. 构建了全球最完整的新能源产业链晨】",
       "B. 构建了全球最完整的新能源产业链")
q_edit("questions_shizheng.json", "q-shizheng-multi-129", "stem", "培育发展未来产业，有利于提】",
       "培育发展未来产业，有利于")
q_edit("questions_shizheng.json", "q-shizheng-multi-147", "options", "B. 拓展了构建人类命运共同体的实践路径吴】 习题190",
       "B. 拓展了构建人类命运共同体的实践路径")
q_edit("questions_shizheng.json", "q-shizheng-multi-147", "options", "C. 开辟了国际政治文明的蕲新境界",
       "C. 开辟了国际政治文明的崭新境界")
q_edit("questions_shizheng.json", "q-shizheng-multi-147", "options", "D. 实现了全球治理体系的根本性重塑二、",
       "D. 实现了全球治理体系的根本性重塑")

# ---------------- 历年真题：题干 ----------------
q_edit("questions_zhenti.json", "q-zt-2010-01", "stem", "用简短的字旬", "用简短的字句")
q_edit("questions_zhenti.json", "q-zt-2010-01", "stem", "所作的”一些人统治，另一些人受苦难”的界定",
       "所作的“一些人统治，另一些人受苦难”的界定")
q_edit("questions_zhenti.json", "q-zt-2010-01", "stem", "这就是： ＂代替那存在着", "这就是：“代替那存在着")
q_edit("questions_zhenti.json", "q-zt-2010-12", "stem", "｀｀夸父追日”", "“夸父追日”")
q_edit("questions_zhenti.json", "q-zt-2010-17", "stem", "例如1971年版对 “科举” 这个词条的解释是： “从隋唐",
       "例如1971年版对“科举”这个词条的解释是：“从隋唐")
q_edit("questions_zhenti.json", "q-zt-2010-17", "stem", "制度\",1992年版删去”反动” 二字",
       "制度”，1992年版删去“反动”二字")
q_edit("questions_zhenti.json", "q-zt-2010-17", "stem", "1998年版又删去” 为维护其统治而设” 。",
       "1998年版又删去“为维护其统治而设”。")
q_edit("questions_zhenti.json", "q-zt-2010-17", "stem", "在解释”雉”就是”野鸡”之后，紧跟着说” 肉可以吃，羽毛可以做装饰品” 。",
       "在解释“雉”就是“野鸡”之后，紧跟着说“肉可以吃，羽毛可以做装饰品”。")
q_edit("questions_zhenti.json", "q-zt-2012-01", "stem", "恩格斯说： ｀｀鹰比人", "恩格斯说：“鹰比人")
q_edit("questions_zhenti.json", "q-zt-2012-02", "stem", "\"90% X90% X90% X90% X90% =?\"其答案是约59% 。",
       "“90%×90%×90%×90%×90%=？”其答案是约59%。")
q_edit("questions_zhenti.json", "q-zt-2012-04", "stem", "“占领华尔街 “抗议活动中", "“占领华尔街”抗议活动中")
q_edit("questions_zhenti.json", "q-zt-2012-04", "stem", "“我们是99%\"的标语", "“我们是99%”的标语")
q_edit("questions_zhenti.json", "q-zt-2012-19", "stem", "将汉语中的” 价” “值”二字", "将汉语中的“价”“值”二字")
q_edit("questions_zhenti.json", "q-zt-2012-19", "stem", "都是 “人 ＂，示意价值在” 人” 。", "都是“人”，示意价值在“人”。")
q_edit("questions_zhenti.json", "q-zt-2013-28", "stem", "以王明为代表的”左 “倾错误", "以王明为代表的“左”倾错误")
q_set("questions_zhenti.json", "q-zt-2013-28", "options",
      ["A. 排斥和打击中间势力", "B. 将反帝反封建与反资产阶级并列", "C. 集中力量攻打大城市",
       "D. 主张“一切经过统一战线”"])
q_edit("questions_zhenti.json", "q-zt-2014-11", "stem", "｀有到来之可能 ＇", "“有到来之可能”")
q_set("questions_zhenti.json", "q-zt-2014-11", "options",
      ["A. “御敌于国门之外”", "B. “红旗到底打得多久”", "C. “在全国范围内先争取群众后建设政权”",
       "D. “一省或数省的首先胜利”"])
q_edit("questions_zhenti.json", "q-zt-2015-14", "stem", "钱学森曾经说过： ＂我作为", "钱学森曾经说过：“我作为")
q_edit("questions_zhenti.json", "q-zt-2015-14", "stem", "最高的奖赏。 ”这说明", "最高的奖赏。”这说明")
q_edit("questions_zhenti.json", "q-zt-2016-12", "stem", "（史称(（五四指示》）", "（史称《五四指示》）")
q_set("questions_zhenti.json", "q-zt-2016-12", "options",
      ["A. “保存富农经济”", "B. “地主不分田，富农分坏田”", "C. “耕者有其田”", "D. “没收一切土地”"])
q_edit("questions_zhenti.json", "q-zt-2016-25", "stem", "“用政府权力的 ｀减法 ＇换取市场活力的 ｀乘法I II等",
       "“用政府权力的‘减法’换取市场活力的‘乘法’”等")
q_edit("questions_zhenti.json", "q-zt-2016-28", "stem", "创办(（青年杂志》（后改名（新青年》）",
       "创办《青年杂志》（后改名《新青年》）")
q_edit("questions_zhenti.json", "q-zt-2018-04", "stem", "(（资本论》（德文版）", "《资本论》（德文版）")
q_edit("questions_zhenti.json", "q-zt-2018-14", "stem",
       "《关于（中共中央关于全面推进依法治国若干重大问题的决定〉的说明》",
       "《关于〈中共中央关于全面推进依法治国若干重大问题的决定〉的说明》")
q_edit("questions_zhenti.json", "q-zt-2018-14", "stem",
       "因为犯罪虽是无视法律—࣭好比污染了水流，而不公正的审判则毁坏法律——卿好比污染了水源。 ”",
       "因为犯罪虽是无视法律——好比污染了水流，而不公正的审判则毁坏法律——好比污染了水源。”")
q_edit("questions_zhenti.json", "q-zt-2018-21", "stem", "列宁指出： ＂一切民族", "列宁指出：“一切民族")
q_edit("questions_zhenti.json", "q-zt-2019-12", "stem", "《毛泽东先生来了！〉）的社评", "《毛泽东先生来了！》的社评")
q_edit("questions_zhenti.json", "q-zt-2022-20", "stem", "“躺平”凡尔赛\"\"YYDS\"等", "“躺平”“凡尔赛”“YYDS”等")
q_edit("questions_zhenti.json", "q-zt-2023-01", "stem", "也不能忘记走过的过去。这表明", "也不能忘记走过的过去。”这表明")
q_edit("questions_zhenti.json", "q-zt-2023-14", "stem", "法治道路；·建设", "法治道路，建设")
q_edit("questions_zhenti.json", "q-zt-2026-16", "stem", "其目的在于(", "其目的在于（ ）")
q_edit("questions_zhenti.json", "q-zt-2026-18", "stem", "植物”薯先生”", "植物“薯先生”")
q_edit("questions_zhenti.json", "q-zt-2026-18", "stem", "地上长番茄”的新型作物", "地上长番茄”的新型作物")
q_edit("questions_zhenti.json", "q-zt-2026-18", "stem", "的新型作物。科学家能够利用基因技术进行新型作物的培育，是因为(",
       "的新型作物。科学家能够利用基因技术进行新型作物的培育，是因为")
q_edit("questions_zhenti.json", "q-zt-2026-20", "stem", "也由此而决定了他们的工作的重要性。科学家对",
       "也由此而决定了他们的工作的重要性。”科学家对")
q_edit("questions_zhenti.json", "q-zt-2026-25", "stem", "是高质量发展的重要基础", "是高质量发展的重要基础")
q_edit("questions_zhenti.json", "q-zt-2026-25", "stem", "推进中国式现代化的生力军是高质量发展", "推进中国式现代化的生力军，是高质量发展")

# 需要整段重写的题干
q_set("questions_zhenti.json", "q-zt-2017-30", "stem",
      "我国法律文化有悠久的历史和传承。据《说文解字》阐释，汉语中“法”的古体是“灋”。“灋，刑也，平之如水，从水；"
      "廌，所以触不直者去之，从去。”在古代，“法”主要表现为“刑”或“刑律”。“刑”既有刑戮、罚罪之意，也有规范之意；"
      "“廌”也称“獬豸”，是神话中的独角兽，它公正不阿，善断是非曲直。上述材料表明，在传统文化中人们对法律的理解和诉求是")

q_set("questions_zhenti.json", "q-zt-2023-22", "stem",
      "中国共产党的历史，是一部不断推进马克思主义中国化时代化的历史，是一部不断推进理论创新、进行理论创造的历史。"
      "在这一历程中，毛泽东是马克思主义中国化的伟大开拓者和毛泽东思想的主要创立者，其主要贡献是")
q_set("questions_zhenti.json", "q-zt-2023-22", "options",
      ["A. 第一次明确提出了“马克思主义中国化”的命题", "B. 深刻论证了马克思主义中国化的必要性和重要性",
       "C. 系统阐述了马克思主义中国化的科学内涵", "D. 全面清除了马克思主义中国化认识上的各种障碍"])
q_set("questions_zhenti.json", "q-zt-2026-01", "stem",
      "“十五五”时期在基本实现社会主义现代化进程中具有承前启后的重要地位。习近平总书记在《关于〈中共中央关于制定国民经济和社会发展第十五个五年规划的建议〉的说明》中指出："
      "“实现社会主义现代化是一个阶梯式递进、不断发展进步的历史过程，需要不懈努力、持续奋斗。”"
      "“阶梯式递进、不断发展进步”的过程是一个\n"
      "①前进性与曲折性相统一的过程 ②规律性与能动性相统一的过程 ③连续性与非连续性相统一的过程 ④直线性与循环性相统一的过程")
q_set("questions_zhenti.json", "q-zt-2026-01", "options",
      ["A. ①②③", "B. ①②④", "C. ①③④", "D. ②③④"])
q_set("questions_zhenti.json", "q-zt-2026-11", "stem",
      "毛泽东在《中国共产党在民族战争中的地位》一文中指出：“遵义会议纠正了在‘第五次反围剿’斗争中所犯的"
      "‘左’倾机会主义性质的严重的原则错误，团结了党和红军，使得党中央和红军主力胜利完成了长征，转到了抗日的前进阵地，"
      "执行了抗日民族统一战线的新政策。”遵义会议之所以成为党的历史上一个生死攸关的转折点，是因为这次会议")
q_edit("questions_zhenti.json", "q-zt-2026-11", "options", "B. 确立了马马思主义建党建军原则",
       "B. 确立了马克思主义建党建军原则")
q_set("questions_zhenti.json", "q-zt-2026-14", "stem",
      "习近平强调：“我为什么要对青年讲讲社会主义核心价值观这个问题？是因为青年的价值取向决定了未来整个社会的价值取向，"
      "而青年又处在价值观形成和确立的时期，抓好这一时期的价值观养成十分重要。这就像穿衣服扣扣子一样，如果第一粒扣子扣错了，"
      "剩余的扣子都会扣错。人生的扣子从一开始就要扣好。”习近平以“人生的扣子从一开始就要扣好”作比喻，主要强调了")

# ---------------- 历年真题：选项 ----------------
q_set("questions_zhenti.json", "q-zt-2010-11", "options",
      ["A. “道虽迩，不行不至；事虽小，不为不成”", "B. “才者，德之资也；德者，才之帅也”",
       "C. “不学礼，无以立”", "D. “是非之心，智也”"])
q_edit("questions_zhenti.json", "q-zt-2026-16", "options", "B. 促进国际社会联合起来反对美国发动的单边“关税战",
       "B. 促进国际社会联合起来反对美国发动的单边“关税战”")
q_set("questions_zhenti.json", "q-zt-2026-25", "options",
      ["A. 它是我国第一部专门关于民营经济发展的基础性法律",
       "B. 它首次将毫不动摇巩固和发展公有制经济，毫不动摇鼓励、支持、引导非公有制经济发展写入法律",
       "C. 它首次明确外商投资经济的法律地位",
       "D. 它首次在法律中规定“促进民营经济持续、健康、高质量发展是国家长期坚持的重大方针”"])

# ---------------- 历年真题：解析 ----------------
q_set("questions_zhenti.json", "q-zt-2016-10", "explain",
      "本题考查救亡图存。魏源在《海国图志》中提出了“师夷长技以制夷”的思想，这里的“长技”是指西方的军事和科学技术，"
      "故C正确。A、B、D均不符合题意。")
q_set("questions_zhenti.json", "q-zt-2012-01", "explain",
      "本题考查理性认识在认识过程中的作用。人的认识过程分为感性认识和理性认识两个阶段，感性认识是低级阶段，"
      "理性认识是高级阶段，借助抽象思维，以反映事物的本质为内容，因而更加深刻。题干说明某些动物和人一样，"
      "都具有“看”“嗅觉”这样的感官识别和感受能力，但是动物仅仅是一种本能，它们并没有人那样的抽象思维能力，故A正确。"
      "B、C意在强调“非理性因素”的重要性，非理性因素是指人的情感、意志、动机、欲望、幻想、想象、直觉等，"
      "恩格斯这句话并未强调“非理性因素”的作用。D并非人与动物的区别，某些高等动物也具有生理机能和心理活动。")
q_set("questions_zhenti.json", "q-zt-2012-26", "explain",
      "本题考查鸦片战争后签订的不平等条约。题干把时间限定在1842年8月《南京条约》签订以后，国家限定为美、法，"
      "即美、法逼迫清政府签订的不平等条约。符合题意的只有B《望厦条约》（中美双方签订，1844年7月）和"
      "C《黄埔条约》（中法双方签订，1844年10月）。A《虎门条约》是中英两国1843年10月签订的，不符合限定条件；"
      "D《天津条约》是1858年英、法、俄、美强迫清政府在天津签订的，两个限定条件都不符合。")
q_edit("questions_zhenti.json", "q-zt-2011-18", "explain", "同政府的个人联合”（", "同政府的“个人联合”（")
q_edit("questions_zhenti.json", "q-zt-2011-20", "explain", "B\"劳动价值论”", "B“劳动价值论”")
q_edit("questions_zhenti.json", "q-zt-2011-20", "explain", "四大独创理论一一一", "四大独创理论——")
q_edit("questions_zhenti.json", "q-zt-2011-27", "explain", "及吾人所决定之其他小岛。故D正确。",
       "及吾人所决定之其他小岛。”故D正确。")
q_set("questions_zhenti.json", "q-zt-2014-17", "explain",
      "本题考查物质运动与时间和空间的关系。时间和空间是物质运动的存在形式。物质运动总是在一定的时间和空间中进行的，"
      "没有离开物质运动的“纯粹”时间和空间，也没有离开时间和空间的物质运动，时间和空间是通过物质运动的变化表现出来的。"
      "题干中科学家通过物源示踪的方法判别出长江贯通东流的时限就体现了这一点，故AD正确。B表述错误，"
      "时间和空间作为物质运动的存在形式是客观的，是不以人的意志为转移的。")
q_edit("questions_zhenti.json", "q-zt-2019-03", "explain", "《（政治经济学批判〉序言》", "《〈政治经济学批判〉序言》")
q_edit("questions_zhenti.json", "q-zt-2019-03", "explain", "13 选项中的“上层建筑”", "B选项中的“上层建筑”")
q_edit("questions_zhenti.json", "q-zt-2019-10", "explain", "B“香港海员罢工“发生于1922 年 1 月",
       "B“香港海员罢工”发生于1922年1月")
q_edit("questions_zhenti.json", "q-zt-2019-10", "explain", "C” 京汉铁路工人罢工”发生于 1923 年2 月",
       "C“京汉铁路工人罢工”发生于1923年2月")
q_edit("questions_zhenti.json", "q-zt-2019-10", "explain", "D\" 开洪五矿工人罢工", "D“开滦五矿工人罢工”")
q_edit("questions_zhenti.json", "q-zt-2019-11", "explain", "为了闭结国民党共同抗日", "为了团结国民党共同抗日")
q_edit("questions_zhenti.json", "q-zt-2019-11", "explain", "“将党的工作重心必须由乡村转移到城市\";",
       "“将党的工作重心必须由乡村转移到城市”；")
q_edit("questions_zhenti.json", "q-zt-2019-20", "explain", "这是因为：CD 任何社会形态", "这是因为：①任何社会形态")
q_edit("questions_zhenti.json", "q-zt-2019-20", "explain", "＠资本主义发展的不平衡性", "②资本主义发展的不平衡性")
q_edit("questions_zhenti.json", "q-zt-2019-20", "explain", "战）当代资本主义的发展", "③当代资本主义的发展")
q_edit("questions_zhenti.json", "q-zt-2019-22", "explain", "CD 从 “变”的方面看", "①从“变”的方面看")
q_edit("questions_zhenti.json", "q-zt-2019-22", "explain", "辽）从“不变”的方面看", "②从“不变”的方面看")
q_edit("questions_zhenti.json", "q-zt-2019-29", "explain", "CD\" 政社合一”", "①“政社合一”")
q_edit("questions_zhenti.json", "q-zt-2019-29", "explain", "心）还有一亿多衣民的温饱问题", "②还有一亿多农民的温饱问题")
q_edit("questions_zhenti.json", "q-zt-2021-27", "explain", "《南京条约。", "《南京条约》。")
q_edit("questions_zhenti.json", "q-zt-2022-07", "explain", "三农”工作摆在首要位置", "“三农”工作摆在首要位置")
q_edit("questions_zhenti.json", "q-zt-2022-11", "explain",
       "【光速考研考点点拨解放战争的历程坡村召开了中共七届二中全会",
       "【光速考研考点点拨】解放战争的历程 1949年3月，中共中央在西柏坡村召开了中共七届二中全会")
q_edit("questions_zhenti.json", "q-zt-2022-12", "explain", "【试题解析新中国成立初期", "【试题解析】新中国成立初期")
q_edit("questions_zhenti.json", "q-zt-2022-15", "explain", "“形势与政策 “当代世界经济与政治”", "“形势与政策”“当代世界经济与政治”")
q_edit("questions_zhenti.json", "q-zt-2022-17", "explain", "“产工即一切从实际出发", "“产”，即一切从实际出发")
q_edit("questions_zhenti.json", "q-zt-2023-09", "explain", "打破了天朝迷梦”", "打破了“天朝迷梦”")
q_edit("questions_zhenti.json", "q-zt-2019-12", "explain", "。岭．【标准答案】D 本题考查2018 年度国内重大时政", "。")
q_edit("questions_zhenti.json", "q-zt-2022-20", "explain", "在生产活动中形 2022年考研政治真题解析共12页by：光速考研成的一种",
       "在生产活动中形成的一种")
q_edit("questions_zhenti.json", "q-zt-2026-16", "explain", "。二、多项选择题（17~33小题，每小题2分，共34分）", "。")
q_edit("questions_zhenti.json", "q-zt-2017-30", "explain", "说明法律富含着公平如水、正义神圣的深刻意蕴。因此，CD正确。",
       "说明法律富含着公平如水、正义神圣的深刻意蕴。因此，CD正确。")

# 解析结尾被粘上下一题的内容，整段截掉
EDITS.append(("questions_zhenti.json", "q-zt-2017-30", "explain_trim", " 31：【标准答案】ABCD", ""))

q_del("questions_zhenti.json", "q-zt-2017-03")

# ---------------- 知识点 ----------------
p_edit("shizheng-01.json", "shizheng-01-04", "quote", None, "北京核”的辐射带动作用", "北京“一核”的辐射带动作用")
p_edit("shizheng-01.json", "shizheng-01-04", "detail", 0, "北京核”的辐射带动作用", "北京“一核”的辐射带动作用")
p_edit("shizheng-02.json", "shizheng-02-07", "quote", None, "（二），“。“大稳定”。“小调整”是指",
       "（二）“大稳定、小调整”是指")
p_set("shizheng-05.json", "shizheng-05-04", "title", "中国的理念、倡议与行动")
p_set("shizheng-05.json", "shizheng-05-05", "title", "全球治理倡议为破解难题提供时代答案")
p_set("shizheng-05.json", "shizheng-05-06", "title", "推进全球治理事业的中国贡献")
p_set("shizheng-05.json", "shizheng-05-07", "title", "引领变革方向，迈向光明前景")
p_edit("shizheng-07.json", "shizheng-07-02", "detail", 1, "这是任何时候都丝毫不能动摇的。",
       "这是任何时候都丝毫不能动摇的。”")
p_edit("shizheng-07.json", "shizheng-07-02", "detail", 2, "”面对20世纪80年代末", "面对20世纪80年代末")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    qcache, pcache = {}, {}
    for f in (SRC.glob("questions*.json")):
        if not f.name.startswith("_"):
            qcache[f.name] = json.loads(f.read_text("utf-8"))
    for f in (SRC / "parts").glob("*.json"):
        pcache[f.name] = json.loads(f.read_text("utf-8"))

    errors = []
    for f, qid, field, old, new in EDITS:
        q = next((x for x in qcache[f] if x["id"] == qid), None)
        if q is None:
            errors.append(f"找不到题目 {qid}")
            continue
        if field == "explain_trim":
            if old not in q["explain"]:
                errors.append(f"{qid} 解析里找不到待删内容")
            else:
                q["explain"] = q["explain"].split(old)[0].strip()
                COUNT["edit"] += 1
            continue
        if field == "options":
            hit = False
            for i, o in enumerate(q["options"]):
                if o == old:
                    q["options"][i] = new
                    hit = True
                    COUNT["edit"] += 1
                    break
            if not hit:
                errors.append(f"{qid} 找不到选项 {old[:30]}")
            continue
        if old not in q[field]:
            errors.append(f"{qid}.{field} 找不到 {old[:30]}")
            continue
        q[field] = q[field].replace(old, new, 1)
        COUNT["edit"] += 1

    for f, qid, field, value in SETS:
        q = next((x for x in qcache[f] if x["id"] == qid), None)
        if q is None:
            errors.append(f"找不到题目 {qid}")
            continue
        q[field] = value
        COUNT["set"] += 1

    for f, qid in DELETES:
        before = len(qcache[f])
        qcache[f] = [x for x in qcache[f] if x["id"] != qid]
        if len(qcache[f]) == before:
            errors.append(f"找不到要删的题目 {qid}")
        else:
            COUNT["delete"] += 1

    for f, pid, field, value in POINT_SETS:
        part = pcache[f]
        p = next((x for x in part["points"] if x["id"] == pid), None)
        if p is None:
            errors.append(f"找不到考点 {pid}")
            continue
        p[field] = value
        COUNT["point"] += 1

    for f, pid, field, idx, old, new in POINT_EDITS:
        part = pcache[f]
        p = next((x for x in part["points"] if x["id"] == pid), None)
        if p is None:
            errors.append(f"找不到考点 {pid}")
            continue
        target = p[field] if idx is None else p[field][idx]
        if old not in target:
            errors.append(f"{pid}.{field}[{idx}] 找不到 {old[:30]}")
            continue
        fixed = target.replace(old, new, 1)
        if idx is None:
            p[field] = fixed
        else:
            p[field][idx] = fixed
        COUNT["point"] += 1

    if errors:
        print("有 %d 条操作没有命中：" % len(errors))
        for e in errors:
            print("  -", e)
        raise SystemExit(1)

    print("命中：", COUNT)

    if args.apply:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = BACKUP / f"知识点-人工校订-{stamp}"
        backup.mkdir(parents=True, exist_ok=True)
        for name, data in qcache.items():
            shutil.copy2(SRC / name, backup / name)
            (SRC / name).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        for name, data in pcache.items():
            shutil.copy2(SRC / "parts" / name, backup / name)
            (SRC / "parts" / name).write_text(
                json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("已备份到", backup)
    else:
        print("（试运行，加 --apply 写盘）")


if __name__ == "__main__":
    main()
