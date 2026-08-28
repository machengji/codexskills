# 融合地图：xhs-project-digest × xiaohongshu-post-writer

## 为什么融合
- digest 擅长：**项目事实筛选、避雷结构、服务化判断**
- post-writer 擅长：**人设表达、标题封面、去 AI 味、合规审计**
- 单用 digest：内容对，但容易像日报模板
- 单用 post-writer：文案好看，但缺少项目筛选业务闭环

## 职责切分

| 环节 | 主负责 | 产出 |
|---|---|---|
| 线索收集 | digest / maomp | today-notes / latest.json |
| 分类（推荐/观察/避雷） | digest | 事实包 bundle |
| 初稿结构 | digest 脚本 | 标题/正文骨架 |
| 封面图生成 | gemini-3.1-flash-image | 3:4 高吸引力小红书封面卡片图 |
| 人设润色 | post-writer 规则 | 口语化、反差开头、少模板句 |
| 合规与去 AI 味 | post-writer checklist | 发布前审计 |
| 发布动作 | 用户手动（默认） | 上号粘贴 |

## 触发路由
- “今天筛项目发小红书 / 项目避雷笔记” → 走本 skill 全流程
- “这段文案去 AI 味 / 换人设 / 合规检查” → 可直接调 `$xiaohongshu-post-writer`
- “根据照片配文案” → post-writer 主责，digest 仅在涉及项目筛选时补充事实

## 数据流

```text
today-notes.md / latest.json
        │
        ▼
generate_xhs_posts.py  (--stage both)
        │
        ├─ 事实层：推荐/观察/避雷 + 小验证
        └─ 表达层：3标题 + 封面 + 话题 + 图片顺序 + 合规清单
        │
        ▼
人工 3-5 分钟改语气
        │
        ▼
小红书创作者后台手动发布
```

## 不做什么
- 不自动点赞评论涨粉
- 不批量矩阵养号
- 不承诺阅读量/爆款
- 不把来源站原文当笔记
