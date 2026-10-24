# 政点 · 考研政治

个人使用的考研政治选择题与背诵工具。刷题、知识点、思维导图、时间轴四合一，纯离线，可打包成安卓应用。

作者：Jayce919 · https://github.com/Jayce919

## 运行

```bash
npm install
npm run dev
```

## 构建

```bash
npm run build      # PWA，输出 dist/
```

`dist/` 可直接部署到任意静态托管（Netlify / GitHub Pages），平板用 Chrome 打开后「添加到主屏幕」即可离线使用；也可以作为 Capacitor 的 `webDir` 打包 APK。

## 内容维护

仓库里已经带好构建后的数据（`src/data/*.json`），克隆下来 `npm install && npm run dev` 就能跑。

如果要改内容，需要本地的原始资料目录（未入库：PDF、OCR 结果与整理脚本体积大且含版权文本）：

- 知识点与题库源文件：`../知识点/`（`parts/*.json` 按专题拆分，`questions_*.json` 为各来源题库）
- 打包与校验：`npm run content`（生成 `src/data/*.json`）
- 生成 Markdown 文档：`npm run doc`
- 质量检查：`python ../工具/audit.py`、`python ../工具/qa_full.py`
- 图标：`python ../工具/make_icon.py`

## 目录

```
src/pages       首页、刷题、模拟考试、理论、导图、时间轴、统计、设置
src/components  题目、图标
src/lib         内容索引、SM-2 调度、判分、状态存储、进度码
src/data        构建生成的学科、题库、时间轴、导图
```

## 数据

进度保存在本机浏览器。设置页可生成「进度码」在手机与平板之间同步，也可导出 JSON 备份。
