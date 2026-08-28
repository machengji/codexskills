---
name: xhs-project-digest
description: 把网创/创业项目线索整理成可发布的小红书原创筛选笔记；融合 xiaohongshu-post-writer 做人设润色、去AI味、标题封面话题优化与合规检查。支持 today-notes 或扫描 JSON，输出标题备选、正文、封面、话题、图片排序、评论引导和7天计划。Use when the user mentions 小红书、小红薯、项目筛选号、每日总结发小红书、副业避雷笔记、把项目整合成笔记、润色小红书、去AI味、人设改写，或要求生成/优化小红书发布文案。
---

# 小红书项目筛选号（筛选 + 好看文案 融合版）

本 skill 是主入口，把两套能力串成一条流水线：

1. **xhs-project-digest**：项目筛选、原创总结、禁止搬运/网盘/暴富承诺
2. **xiaohongshu-post-writer**：人设表达、标题/封面/话题、去 AI 味、合规审计、图片排序
3. **封面生图模型**：固定使用 `gemini-3.1-flash-image` 生成 3:4 比例极简高对比卡片封面

> 安装关系：`xiaohongshu-post-writer` 已作为通用润色 skill 安装；本 skill 负责“项目筛选号”业务闭环，并在润色阶段强制复用其规则。

## 目标
每天产出 **1 条原创、可直接粘贴发布** 的小红书图文：
- 不是冒泡网/项目站原文
- 不是模板味很重的 AI 稿
- 是“自己筛选后的判断 + 人设口语化表达”

## 两阶段标准流程

### 阶段 A：筛选成稿（事实层）
1. 收集线索（maomp 扫描 / 自己看到的项目）
2. 写入自己总结：
   - 工作目录：`E:\\machengji\\xhs-project-digest\\input\\today-notes.md`
3. 生成事实草稿：

```powershell
python "C:\\Users\\Administrator\\.codex\\skills\\xhs-project-digest\\scripts\\generate_xhs_posts.py" --notes "E:\\machengji\\xhs-project-digest\\input\\today-notes.md" --out-dir "E:\\machengji\\xhs-project-digest\\output" --stage both
```

输出：
- `output/xhs-YYYY-MM-DD.md`（发布包，已含润色结构）
- `output/xhs-YYYY-MM-DD.json`
- `output/week-content-plan.md`

### 阶段 B：人设润色（表达层，可自动或人工触发）
生成后必须按 post-writer 标准再审一遍：

1. 读取人设：`assets/persona-project-filter.md`
2. 读取写作模式：`C:\\Users\\Administrator\\.codex\\skills\\xiaohongshu-post-writer\\references\\writing-patterns.md`
3. 读取合规清单：`C:\\Users\\Administrator\\.codex\\skills\\xiaohongshu-post-writer\\references\\compliance-checklist.md`
4. 需要时用 `$xiaohongshu-post-writer` 对草稿做 Rewrite / Audit
5. 人工 3-5 分钟改成更像你本人的语气
6. 手动发布（默认不自动发号）

## Agent 执行协议（融合）

当用户说“发小红书 / 今日筛选 / 润色笔记”时：

1. **先做筛选**：解析 notes 或 latest.json，确保推荐/观察/避雷齐全
2. **再做润色与生图**：套用人设，给 3 个标题、封面大字与 `gemini-3.1-flash-image` 生图 Prompt、正文、话题、图片顺序、评论引导
3. **最后做审计**：输出合规与去 AI 味检查结果
4. **只交草稿**：除非用户明确要求浏览器自动发布，否则不发号

冲突优先级（继承 post-writer）：
1. 事实准确、隐私与安全
2. 用户当前指令
3. 项目筛选硬规则（不搬运、无网盘、无收益承诺）
4. 人设一致性
5. 平台合规
6. 可读性与互动
7. 流量优化

## 强制规则（筛选硬约束）
- 输出必须是“自己的筛选总结”，不是来源站点转载
- 禁止网盘链接、提取码、会员正文大段复制
- 禁止收益承诺（日入/稳赚/保底/百分百）
- 每个推荐项必须有：判断、适合谁、如何小验证
- 中文直接输出，UTF-8 无 BOM
- 不把“去 AI 味”写成规避平台检测的技巧

## 若用户只给方向不给笔记
1. 先根据今日线索起草 `today-notes.md`
2. 再生成小红书草稿
3. 明确标注哪些是暂定判断，提醒用户改成自己的语气与真实经历

## 关键文件
- 融合说明：`references/fusion-map.md`
- 流程：`references/workflow.md`
- 内容规则：`references/content-rules.md`
- 人设：`assets/persona-project-filter.md`
- 生成脚本：`scripts/generate_xhs_posts.py`
- 工作目录：`E:\\machengji\\xhs-project-digest\\`
- 通用润色 skill：`C:\\Users\\Administrator\\.codex\\skills\\xiaohongshu-post-writer\\`
