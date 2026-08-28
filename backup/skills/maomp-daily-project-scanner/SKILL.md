---
name: maomp-daily-project-scanner
description: 每日检测冒泡网(maomp.vip)最新网创/创业项目线索，自动抓取 RSS 与正文，按可执行性、获客、交付、合规风险评分，并输出中文可行项目日报与 7 天验证建议。Use when the user mentions 冒泡网、maomp、maomp.vip、每日项目、最新项目、可行创业项目、网创项目筛选、副业项目检测、赚钱项目日报，或要求每天检查该网站有没有能做的项目。
---

# 冒泡网每日可行项目扫描

把 `https://www.maomp.vip/` 当“项目线索库”扫描，不是当收益证据库。标题里的“日入/月入/躺赚”默认不可信。

## 快速执行

1. 运行扫描脚本：

```powershell
python "C:\Users\Administrator\.codex\skills\maomp-daily-project-scanner\scripts\monitor.py" --data-dir "E:\machengji\maomp-monitor"
```

2. 读取：

- `E:\machengji\maomp-monitor\latest.md`
- 如需结构化结果，追加：`--json-out "E:\machengji\maomp-monitor\latest.json"`

3. 只对 `可优先验证` / `可小成本验证` 的前 3-5 条抓正文做人工二次判断。
4. 按 `references/report-template.md` 用中文输出最终推荐。
5. 需要评分细则时再读 `references/scoring-rules.md`。

## 强制规则

- 不把课程介绍中的收益数字当事实。
- 不推荐挂机、挂G、外挂、破解、搬运、刷量、男粉擦边、规避风控项目。
- 不建议用户先买会员/高价课再验证。
- 优先把线索转成“可交付服务/产品”，而不是“跟做副业玩法”。
- 每个推荐项目必须给：目标客户、交付物、报价区间、7 天验证动作、风险边界。
- 文件写入统一 UTF-8（无 BOM），中文直接输出。

## 人工二次判断清单

对初筛靠前项目，至少回答：

1. 真实客户是谁？
2. 最小可交付样品是什么？
3. 7 天内能否联系 10 个潜在客户？
4. 是否必须先投广告/买课/买软件？
5. 主要风险是封号、侵权、资金还是交付能力？

若答不上 1/2/3，降级为“谨慎观察”或“不建议”。

## 输出优先级

1. 今天最值得验证的 1 个主线项目
2. 1-2 个次优可观察方向
3. 明确不建议清单
4. 下一步可立刻执行的动作

## 数据目录

默认：

```text
E:\machengji\maomp-monitor\
  latest.md
  state.json
  reports\YYYY-MM-DD.md
  reports\YYYY-MM-DD.csv
```

用户指定其他目录时，用 `--data-dir` 覆盖。

## 可选增强

- 仅重扫最新 N 条：`python ...\monitor.py --force-all --limit 20`
- 已有 Windows 计划任务“冒泡网创业项目每日检测”时，可继续保留；本 skill 负责对话内即时扫描与人工筛选。
- 用户说“继续/看今天日报”时，先读 `latest.md`；若超过 12 小时或用户明确要求刷新，再重跑脚本。

## 会员登录（可选）

若本机存在：

```text
E:\machengji\maomp-monitor\credentials.json
```

格式：

```json
{
  "username": "你的账号",
  "password": "你的密码",
  "base_url": "https://www.maomp.vip",
  "login_url": "https://www.maomp.vip/wp-login.php"
}
```

脚本会自动登录并缓存 `cookies.txt`，从而抓取会员可见正文、课程目录、网盘链接与提取码。

安全要求：

- 凭据只放本机 `credentials.json`，不要写进对话记录、git、截图或 skill 正文
- 报告可写下载链接，但不要输出密码字段
- 用户说“不要登录”时，加 `--no-login`
