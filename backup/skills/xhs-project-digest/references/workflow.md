# 小红书「筛选 + 好看文案」完整流程

## 目标
每天 1 条原创笔记：
- 筛选结论：可做 / 观察 / 避雷
- 表达质量：像真人筛选日记，不像 AI 报告

## 每天 25-40 分钟

```text
1. 收集线索（5-10 分钟）
2. 自己总结到 today-notes.md（8-12 分钟）
3. 运行 generate_xhs_posts.py --stage both（1 分钟）
4. 按人设润色 + 去 AI 味（5 分钟）
5. 做封面大字图（使用 gemini-3.1-flash-image 模型生成 3:4 爆款封面）（5 分钟）
6. 手动发布 + 置顶评论（3 分钟）
7. 记录阅读/收藏/评论（2 分钟）
```

## 角色定位（固定人设）
见：`assets/persona-project-filter.md`

一句话：
> 每天筛项目，只讲能不能做。不荐挂机，不吹暴富，只看客户和交付。

## 内容栏目
1. 每日筛选：今天看了 N 个，能做 X 个
2. 深拆一条：为什么这个能做成服务
3. 避雷专题：这周别碰什么
4. 方法帖：7 天如何验证一个项目
5. 互动帖：把你看到的项目丢我，我帮你排

## 输入 A：自己总结（推荐）
`E:\\machengji\\xhs-project-digest\\input\\today-notes.md`

```markdown
## 推荐
- 名称｜判断｜适合谁

## 观察
- 名称｜判断｜适合谁

## 避雷
- 名称｜判断｜适合谁
```

## 输入 B：扫描后再改写成自己的总结
先有 JSON，再人工改成 today-notes，再生成。禁止直接把来源正文当笔记。

## 生成命令

```powershell
python "C:\\Users\\Administrator\\.codex\\skills\\xhs-project-digest\\scripts\\generate_xhs_posts.py" --notes "E:\\machengji\\xhs-project-digest\\input\\today-notes.md" --out-dir "E:\\machengji\\xhs-project-digest\\output" --stage both
```

`--stage` 可选：
- `raw`：只要筛选事实稿
- `polished`：只要发布润色包
- `both`：默认，事实 + 润色一次出齐

## 润色检查（阶段 B）
对照 post-writer：
1. 开头是否是具体反差，而不是“在这个时代”
2. 每段是否都钉在事实/判断上
3. 有没有收益承诺、绝对化、网盘、提取码
4. 标题是否给了 2-3 个可 A/B 的备选
5. 封面大字是否一眼能看懂结论
6. 话题是否覆盖：主题 + 人群 + 账号柱子
7. 是否像“项目过滤器”人设，而不是成功学导师

## 发布
- 默认手动发
- 置顶评论引导：清单 / 检测
- 不承诺效果，不诱导无意义刷评
