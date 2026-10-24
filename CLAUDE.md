# CLAUDE.md · 政点项目交接

给接手这个项目的 Claude Code / 开发者：先读这一页，再动手。
本项目 2026-10-24 做过一轮代码修复 + 题库 OCR 校订，细节都在下面。

## 这是什么

**政点 · 考研政治**：纯离线的考研政治刷题与背诵应用。
Vite + React 18 + TypeScript，`vite-plugin-pwa` 做离线，Capacitor 6 打包安卓。
没有后端，进度存浏览器 `localStorage`。

```
考研政治/
├─ 政治刷题App/      应用源码（git 仓库，GitHub: Jayce919/zhengdian）
├─ 知识点/           题库与知识点的 JSON 源数据（不在仓库里）
├─ 工具/             OCR、解析、质检、清洗脚本（不在仓库里）
├─ 备份/             每次批量改数据前的快照
├─ 审查/             前端体检报告、题库修正记录
└─ 打包/             已构建的 APK 与 PWA zip
```

## 常用命令

```bash
cd 政治刷题App
npm install
npm run dev        # 开发服务器 5173
npm run build      # PWA 构建，输出 dist/
npm run content    # 知识点/*.json → src/data/*.json（含校验）
npm run doc        # 生成 知识点/政治_知识点背诵与速查_维护版.md
npx tsc --noEmit   # 类型检查
```

```bash
cd 考研政治
python 工具/bank_audit.py     # 题库体检（只读）
python 工具/fix_bank.py       # 自动清洗，默认试运行，--apply 才写盘
```

## 数据流水线（关键）

```
知识点/parts/*.json        85 个专题、1054 个考点
知识点/questions*.json     11 个题库文件、构建后 2379 道题
        │  npm run content（tools/build_content.mjs）
        ▼
src/data/*.json            subjects / questions / timeline / mindmaps / meta
        │  npm run build
        ▼
dist/                      PWA；Capacitor 用它打 APK
```

- 背诵卡不再是独立题型：已与判断题合并成「判断」，题目全部来自 `questions_panduan.json`；构建时不再自动派生背诵卡。
- `知识点/*.json` 是 `工具/parse_*.py` 从 OCR 结果生成的，**不是手写**。改动一律走下面「改数据的正确顺序」。

## 改数据的正确顺序（重要，别踩坑）

```bash
python 工具/fix_bank.py --apply                 # 1. 自动清洗（幂等）
python 工具/manual_fix_bank.py  --apply         # 2. 第一批人工校订
python 工具/manual_fix_bank2.py --apply         # 3. 第二批（7 处引号）
python 工具/manual_fix_bank3.py --apply         # 4. 第三批（2026 模拟卷）
python 工具/fix_zhenti_answers.py --apply       # 5. 真题答案修正（3 题）
python 工具/fix_zhenti_options.py --apply       # 6. 真题选项补全（18 处，幂等）
# 7. 各学科干扰项解析（6 个 patch，全部幂等）
for s in mayuan maozhongte xisixiang sifa shizheng shigang; do
  python 工具/add_zhenti_distractors.py --patch 工具/zhenti_distractors/$s.json --apply
done
cd 政治刷题App && npm run content && npm run doc && npm run build
```

- **不要直接重跑 `parse_*.py`**：会覆盖上面所有清洗结果。若必须重解析，先跑解析，再按 1→4 重新清洗，或把清洗规则并进解析脚本。
- 这几个脚本都做了断言：目标文本不存在就报错退出，不会静默改错。重跑时如果前一批已经改过，断言会失败——这是有意设计，按顺序跑即可。
- 每次 `--apply` 会自动备份到 `备份/知识点-<批次>-<时间>/`，回滚直接拷回。

## 本轮改了什么

### 1. 代码修复（commit `3d5e6c1`）

| 问题 | 做法 | 文件 |
|---|---|---|
| 练习/考试中途切页丢进度 | 新增 `lib/navGuard.ts`，所有跳转走 `canLeave()`；作答写 `sessionStorage`，刷新可续做；确认离开才清会话 | `App.tsx`、`Practice.tsx`、`Exam.tsx`、`lib/navGuard.ts` |
| 模考倒计时后台走慢 | 开考记 `endAt`，每次按 `endAt - Date.now()` 重算，`visibilitychange` 回前台立刻重算 | `Exam.tsx` |
| 说明文字对比度不足 | 浅色 `--muted` `#7a7a7a` → `#6b6b6b`（5.33:1） | `styles.css` |
| 缺可访问名 | 搜索框、底部导航补 `aria-label` | `Theory.tsx`、`App.tsx` |
| 练习/考试中底部导航点了没反应 | 原生 `window.confirm` 在 WebView 里可能不显示、被静默取消；改为应用内确认框 `ConfirmHost`，确认后才清会话并跳转 | `lib/confirm.ts`、`components/ConfirmHost.tsx`、`App.tsx`、`Practice.tsx`、`Exam.tsx`、`Settings.tsx` |
| 确认离开后弹出两次确认 | 确认后 `nav()` 改 hash 会触发练习页自己的 `popstate`；加 `leaving` 标志忽略这次事件 | `Practice.tsx`、`Exam.tsx` |
| 粘顶题头下方有一条灰带 | `.topbar-wrap` 整层刷了页面底色，滚动时连标题下的 12px 一起冻住；改为只让红色卡片有背景，间距用 `margin-bottom` | `styles.css` |

验证：`tsc`、`build` 通过；Playwright 脚本 26 项断言通过（离开确认、取消不丢、刷新恢复、倒计时、到期自动交卷、不限时、aria、对比度）。

### 2. 题库自动清洗（commit `d54f021`，913 个字符串）

- 汉字间空格 842、半角标点 273、ASCII 引号 41、引号重排 42、括号 60、多余括号 4
- 错字 74：自已/自己、深人/深入、纳人/纳入、千/于（关千/由千）、千部/干部、井不/并不、杜会/社会…
- 数字噪声 41：`22026年`→`2026年`、`19 89`→`1989`、`so%`→`50%`、`2026一2030`→`2026—2030`
- 习题残片 31：从“时政习题【多选题】”处截断；整条是习题的 detail 删除
- 工具：`工具/bank_audit.py`（体检）、`工具/fix_bank.py`（清洗）

### 3. 人工校订（commit `5dfa48f`）

自动清洗后剩 77 条“自动改会猜错”的，逐条按原文处理：

- 补引号/书名号 40+；18 个选项补收尾引号
- 重写被 OCR 吃字的句子 12（《说文解字》“灋…廌…獬豸”、培根名言等）
- 清理解析尾巴 6（粘着下一题的“【标准答案】”）
- 2026 模拟卷 53 处错字（准海/平海→淮海/平津、实线/实践、覆取/攫取、中流柱/中流砥柱、指导制度/领导制度…），补 2 个截断选项
- 知识点 9 处（北京“一核”、大稳定小调整、4 个时政专题标题、1 段拆开的引文）
- **删除 1 题** `q-zt-2017-03`：题干是“一带一路”，解析是“生产价格”计算题，完全错配，无法还原

结果：1279 题，0 异常（题干/解析非空、引号成对、单选答案在选项内、多选≥2 项且在选项内）。

### 4. 真题干扰项补全（本次，未单独提交）

构建一直提示 382 道真题缺干扰项解析。本轮按学科逐批读完 432 道真题，给每个错误选项补
`why` 与 `trap`，共 **855 条**（马原 278、史纲 236、毛中特 168、思修 81、习思想 51、时政 41）。
现在 `npm run content` 不再出现「错误项没写解析」。

同时按 OCR 原文修正：

- 选项补全 18 处（截断、缺字、粘入下一题句子）
- 答案修正 3 题：`q-zt-2025-04` A→C、`q-zt-2022-30` AC→ACD、`q-zt-2024-14` B→C
- 答案比对：2010–2018、2022–2025 与 OCR 答案逐题一致；2009、2019–2021 缺 OCR 答案文件

新增工具：`工具/add_zhenti_distractors.py`、`工具/fix_zhenti_options.py`、`工具/fix_zhenti_answers.py`，
人工解析源文件在 `工具/zhenti_distractors/`。详细记录见 `审查/题库修正记录-2026-10-24.md`。

### 5. 补全 2025/2026 真题与数据修复（本次）

- 补回 2025 年第 7–33 题（27 题）、2026 年第 3–4 题，两年真题均达 33/33
- 23 道 2024 题补写解析；纠正 4 处解析错配；清除下一题残片、页码、水印
- 修复 32 处 OCR 错字（井→并、撩原、涕湖、眭步、戊戊等），重写 2 道乱码题干
- 补全 40 条被 220 字截断的知识点引文
- 现在：461 道真题、1308 道题、2357 道构建题

新增工具：`工具/add_zhenti_questions.py`、`工具/fix_zhenti_explains.py`、`工具/fix_question_typos.py`、
`工具/fix_quote_truncation.py`，新题源文件在 `工具/zhenti_new/`。

### 6. 补齐 2009–2024 全部缺题（本次）

- 补入 133 道客观题，2009–2026 十八年均为 33/33，**共 594 道真题**
- 修正 2020 年第 4 题编号错位：原 `q-zt-2020-04` 实为第 14 题，已改名 `q-zt-2020-14`，
  真正的第 4 题（列宁一国胜利论）按 PDF 补入
- 答案核对：2013–2018、2020 与答案键逐题一致；2023 第 19 题按理论取 ABC（OCR 的 ABCD 有误）
- 现在：594 道真题、**2379 道构建题**

新增工具：`工具/extract_exam_questions.py`、`工具/verify_zhenti_coverage.py`、
`工具/fix_2020_q4_mislabel.py`、`工具/ocr_answer_keys.py`。

剩余：2009、2019–2021 缺 OCR 答案文件（2013–2018、2020 已用扫描版 PDF 定向 OCR 补核）。

### 7. 背诵卡与判断题合并为「判断」（2026-10-24）

背诵卡不再单独存在，和判断题合并成一个题型：一句表述 → 判对/错 → 展开考点。
定位是**书本理论、定义、易混点的背诵**，不从真题选项里取句子。

- 数据文件 `知识点/questions_panduan.json`，**1286 条**（正确 979 + 错误 307），五科：
  马原 484、毛中特 149、习思想 294、史纲 249、思修法治 110；**时政不设判断题**
- 正确表述：每个考点的 `core` 改写成完整陈述句（开头与标题重复时替换成完整标题）
- 错误表述：`questions_judge2` 的成对混淆、`questions_judge` 的经典干扰项、
  以及旧题库里零散的判断题；均为教材层面的错项
- 构建时不再自动派生背诵卡；旧 `questions_judge*.json` 不再直接打包（内容已并入）
- 判断题题干下有提示「判断下列说法是否正确」，答完显示“正确答案：正确/错误”而不是 T/F
- 生成工具 `工具/build_panduan.py`（`--apply` 才写盘，带备份），个别表述改措辞在 `OVERRIDES` 里加

**进度码与 id（改题库前必看）**

- 正确表述 id 固定为 `q-pd-t-<考点id>`；错误表述**沿用原判断题的 id**（`q-cj-*`、`q-judge-*`、`q-mayuan-00xx`），
  所以旧设备上的答题记录、错题、SRS 在合并后能直接对上
- 旧背诵卡 id `<考点id>-card` 在读取和导入进度时自动映射到 `q-pd-t-<考点id>`，见 `src/lib/store.ts` 的 `migrate`
- 新增的错误表述若没有原 id，才用题干哈希 `q-pd-f-<hash>`，避免重生成题库后编号错位
- 已测试：全量 2379 题的进度码约 26KB；新→新、旧→新导入均正常，已删除题目的旧记录会留在存储里但不计入统计

旧的背诵判断试点（马原 570 条）已归档在 `备份/背诵判断试点-归档/`，不再参与构建。

## 约束与坑

1. **不要改 `answer`、选项顺序、题目 `id`**。多选答案是字母数组，顺序无关但字符必须 A–D。
2. **字段空格策略**：只清 `stem/explain/options/why/core/detail/diff/content/meaning` 里的汉字间空格；`refs`、`title`、`label`、`keywords` 里的空格是排版需要，别动。
3. **引号自动修复只在引号总数为偶数时生效**，且不处理含 `’` 的字符串——奇数说明原文被截断，自动补会猜错，留给人工。
4. **`quote` 字段有 220 字上限**（构建时截断），所以有些引文末尾断在半句，这是生成规则不是 OCR，改它要改 `tools/build_content.mjs` 的截断逻辑。
5. `bank_audit.py` 有 3 类误报，不要“修”：`利在千秋`/`无以至千里` 的“千”、引文里 `｜` 分栏的空格、解析里“AD为干扰选项”。
6. 仓库 `.git/config` 里有本机代理 `http.proxy=127.0.0.1:7890`（这台机器直连 GitHub 会 reset）。换机器请删掉。
7. `知识点/`、`工具/`、`备份/`、`审查/`、`打包/` **不在 git 仓库里**，只有 `政治刷题App/` 入库；克隆仓库只能拿到构建后的 `src/data`。

## 已知遗留

- APK 已更新到 `打包/政点-1.1.apk`（versionCode 2，2026-10-24）。重新打包必须走 `dist/` → `打包/apk/www/` → **`npx cap copy android`** → `gradlew assembleRelease`；漏掉 cap copy 会把旧前端打进包（本轮踩过）。
- 部分长引文在 220 字处截断（见上）。
- 2026 模拟卷只修了显眼的错字，可能还有零星 OCR 错字；`bank_audit.py` 查不出纯语义错误。
- 部分真题的 `explain` 是“标准答案：X”式简写，质量参差，没有逐题重写。

## 验证清单（改完必跑）

```bash
cd 政治刷题App
npx tsc --noEmit                                  # 0 error
npm run content                                   # 打包完成：1054 考点 / 2379 题
npm run doc
npm run build
cd .. && python 工具/bank_audit.py                # 只剩 3 类误报
```

题库改动的额外检查（结构层面）：

- 题目数、`id` 集合、`answer` 与改动前一致（除有意删除）
- 单选 4 选项、多选 4 选项且答案字母都在选项内
- 无空 `stem` / `explain`

## 下一步可以做的

1. 重新打 APK（本轮改动还没上平板）
2. 把 `知识点/` + `工具/` 收进仓库（或拆成 `content/` 子模块），让数据可版本化
3. 给 `src/data` 加一个内容校验脚本并接到 CI
4. 继续人工过一遍 2026 模拟卷与非真题题库的语义错误

相关文档：
- `审查/前端审查-quick-2026-10-24.md`：代码问题与修复记录
- `审查/题库修正记录-2026-10-24.md`：题库改动的逐类记录与前后对照
