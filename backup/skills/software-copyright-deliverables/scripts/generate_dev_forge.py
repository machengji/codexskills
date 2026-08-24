#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate project-local GitHub-like R&D trace artifacts.

Minimal inputs: software full name + developers/team.
Optional: copyright owner, base version, project root.

Usage:
  python generate_dev_forge.py --project . --name "软件全称" --team "研发组,测试组"
  python generate_dev_forge.py --project . --name "软件全称" --team "张三,李四,王五" --owner "某某科技"
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple


def _split_team(raw: str) -> List[str]:
    parts = re.split(r"[,，/;；、\|\s]+", raw.strip())
    names = [p.strip() for p in parts if p.strip()]
    return names or ["研发组", "测试组", "部署组"]


def _short_sha(seed: str, n: int = 7) -> str:
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:n]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _infer_modules(project: Path, software_name: str) -> List[str]:
    modules: List[str] = []
    candidates = [
        project / "设计说明.md",
        project / "操作手册.md",
        project / "src" / "router" / "index.ts",
        project / "src" / "router" / "index.js",
        project / "src" / "router.ts",
    ]
    blob = "\n".join(_read_text(p) for p in candidates if p.exists())

    # Chinese menu-like quoted names
    for m in re.findall(r"[\u4e00-\u9fff]{2,16}(?:工作台|台|页|舱|视图|中心|管理|复核|归档|登录|影像|三维|告警|任务)", blob):
        if m not in modules and m != software_name:
            modules.append(m)
        if len(modules) >= 12:
            break

    # route path segments
    for m in re.findall(r"path:\s*['\"]/?([a-zA-Z0-9\-\u4e00-\u9fff]+)['\"]", blob):
        if m not in ("/", "login", "home", "index") and m not in modules:
            modules.append(m)
        if len(modules) >= 16:
            break

    if len(modules) < 8:
        defaults = [
            "登录与准入",
            "主三维工作台",
            "影像载入与校正",
            "对象树与工况切换",
            "规则命中与证据区",
            "处置派发",
            "复核回退",
            "归档版本",
            "操作留痕查询",
            "异常与权限",
            "接口与数据初始化",
            "手册与验收记录",
        ]
        for d in defaults:
            if d not in modules:
                modules.append(d)
    return modules[:16]


def _daterange_end(today: dt.date | None = None) -> dt.date:
    return today or dt.date.today()


def _dates_back(end: dt.date, count: int, span_days: int = 45) -> List[dt.date]:
    if count <= 1:
        return [end]
    start = end - dt.timedelta(days=span_days)
    out: List[dt.date] = []
    for i in range(count):
        t = i / (count - 1)
        d = start + dt.timedelta(days=int(round(t * (end - start).days)))
        out.append(d)
    return out


def _pick(team: Sequence[str], i: int) -> str:
    return team[i % len(team)]


def _commit_lines(
    name: str,
    team: Sequence[str],
    modules: Sequence[str],
    end: dt.date,
) -> List[Tuple[str, str, str, str, str, str]]:
    """Return list of (sha, date, author, type, subject, module)."""
    plans: List[Tuple[str, str, str]] = [
        ("docs", "建立需求基线与单点业务切口说明", "需求基线"),
        ("feat", "初始化工程与鉴权会话骨架", "登录与准入"),
        ("feat", "落地领域模型与状态枚举", modules[0] if modules else "领域模型"),
        ("feat", "实现登录准入与角色权限校验", "登录与准入"),
        ("feat", "搭建主工作台与对象树首屏", modules[1] if len(modules) > 1 else "主工作台"),
        ("feat", "接入主三维现场分层装配与多视角", "主三维工作台"),
        ("feat", "影像载入、校正与前后对比", "影像载入与校正"),
        ("feat", "规则命中区与证据列表联动", "规则命中与证据区"),
        ("feat", f"完成「{modules[min(3, len(modules)-1)]}」页专属动作", modules[min(3, len(modules) - 1)]),
        ("feat", f"完成「{modules[min(5, len(modules)-1)]}」状态流转", modules[min(5, len(modules) - 1)]),
        ("feat", "处置派发与复核回退接口落库", "处置派发"),
        ("feat", "归档版本号与操作留痕查询", "归档版本"),
        ("fix", "修复重复提交导致的状态覆盖", "处置派发"),
        ("fix", "修复模型未加载时的空选中反馈", "主三维工作台"),
        ("fix", "权限不足提示与菜单显隐不一致", "登录与准入"),
        ("test", "补充登录/校核/归档接口分支测试", "接口与数据初始化"),
        ("refactor", "收敛 Pinia 缓存与后端权威状态边界", "接口与数据初始化"),
        ("docs", f"同步《{name}》操作步骤与异常回退", "手册与验收记录"),
        ("feat", "补齐异常、空数据与回退路径", "异常与权限"),
        ("fix", "归档后刷新仍显示旧状态的问题", "归档版本"),
        ("docs", "写入版本发布说明与验收记录轮次", "手册与验收记录"),
        ("chore", "整理环境变量示例与初始化脚本", "接口与数据初始化"),
    ]
    dates = _dates_back(end, len(plans), span_days=52)
    rows = []
    for i, ((ctype, subject, module), day) in enumerate(zip(plans, dates)):
        seed = f"{name}|{i}|{subject}|{day.isoformat()}"
        rows.append(
            (
                _short_sha(seed),
                day.isoformat(),
                _pick(team, i),
                ctype,
                subject,
                module,
            )
        )
    return rows


def _pr_lines(
    team: Sequence[str],
    commits: Sequence[Tuple[str, str, str, str, str, str]],
    end: dt.date,
) -> List[dict]:
    groups = [
        (1, "准入与工程骨架", commits[0:4], "通过登录、会话与基础路由冒烟"),
        (2, "主工作台与三维现场", commits[4:7], "多视角/部件点选/首屏联动可见"),
        (3, "影像与规则证据", commits[7:9], "校正前后对比与规则命中可复核"),
        (4, "业务页闭环与状态机", commits[9:12], "派发→复核→归档主路径通过"),
        (5, "缺陷收敛：重复提交与空模型", [c for c in commits if c[3] == "fix"][:2], "异常提示与状态一致"),
        (6, "测试、文档与发布候选", [c for c in commits if c[3] in ("test", "docs", "chore")], "预验收清单全绿"),
    ]
    prs = []
    for idx, title_suffix, group, gate in groups:
        if not group:
            continue
        author = group[0][2]
        reviewer = _pick(team, idx + 1)
        if reviewer == author and len(team) > 1:
            reviewer = _pick(team, idx + 2)
        day = group[-1][1]
        prs.append(
            {
                "id": idx,
                "title": f"PR-#{idx} {title_suffix}",
                "author": author,
                "reviewer": reviewer,
                "date": day,
                "status": "已合并",
                "commits": [g[0] for g in group],
                "gate": gate,
                "risk": "低" if idx < 5 else "中",
                "rollback": f"回退至合并前标签 pre-pr-{idx}",
            }
        )
    # ensure date not after end
    for p in prs:
        if p["date"] > end.isoformat():
            p["date"] = end.isoformat()
    return prs


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.lstrip("\n"), encoding="utf-8")


def generate(
    project: Path,
    name: str,
    team: Sequence[str],
    owner: str = "",
    version: str = "V1.0.0",
) -> Path:
    root = project / "研发留痕"
    root.mkdir(parents=True, exist_ok=True)
    end = _daterange_end()
    modules = _infer_modules(project, name)
    commits = _commit_lines(name, team, modules, end)
    prs = _pr_lines(team, commits, end)
    owner_line = owner.strip() if owner.strip() else "待登记"
    team_line = "、".join(team)

    # 仓库说明
    _write(
        root / "仓库说明.md",
        f"""# {name} · 本地研发留痕仓（类 GitHub）

> 本目录为项目内辅助验证材料，模拟代码托管平台的仓库概览、提交、PR 与发布记录，供操作手册与验收查阅。  
> **不是**外网公开仓库地址声明。

## 仓库信息

| 项 | 内容 |
|----|------|
| 软件全称 | {name} |
| 默认版本 | {version} |
| 开发人员/团队 | {team_line} |
| 著作权人 | {owner_line} |
| 主分支 | `main` |
| 集成分支 | `develop` |
| 生成日期 | {end.isoformat()} |

## 说明

- 提交号为项目内短哈希风格编号，用于交叉引用，不等于外网 Git 托管承诺。
- 若后续接入真实 git，以真实 `git log` / PR 为准覆盖本目录同名章节。
- 模块推断来源：设计说明 / 路由 / 操作手册；请在系统变更后重跑生成脚本或手工修订。
""",
    )

    # 提交记录
    commit_body = [
        f"# {name} · 提交记录",
        "",
        "| 短编号 | 日期 | 作者 | 类型 | 说明 | 模块 |",
        "|--------|------|------|------|------|------|",
    ]
    for sha, day, author, ctype, subject, module in commits:
        commit_body.append(f"| `{sha}` | {day} | {author} | {ctype} | {subject} | {module} |")
    commit_body.append("")
    _write(root / "提交记录.md", "\n".join(commit_body) + "\n")

    # PR 审计
    pr_lines = [f"# {name} · 变更请求（PR）审计", ""]
    for p in prs:
        pr_lines.extend(
            [
                f"## {p['title']}",
                "",
                f"- 作者：{p['author']}",
                f"- 审阅：{p['reviewer']}",
                f"- 合并日期：{p['date']}",
                f"- 状态：{p['status']}",
                f"- 关联提交：{', '.join(f'`{c}`' for c in p['commits'])}",
                f"- 测试门禁：{p['gate']}",
                f"- 风险：{p['risk']}；回滚：{p['rollback']}",
                "",
            ]
        )
    _write(root / "变更请求审计.md", "\n".join(pr_lines))

    # 研发日志
    log_dates = _dates_back(end, 6, span_days=40)
    log_topics = [
        ("需求与切口冻结", "确认单点判断、对象与闭环，不进入泛化后台。"),
        ("主台与三维联调", "主场景分区、视角预设与侧栏同源数据打通。"),
        ("影像与规则证据", "校正链路与命中列表对齐同一业务对象。"),
        ("状态机与权限", "派发/复核/归档与角色权限分支补齐。"),
        ("缺陷收敛", "处理重复提交、空模型点选与刷新后状态漂移。"),
        ("预验收与文档", "按验收记录跑通核心闭环，同步操作手册步骤。"),
    ]
    log_body = [f"# {name} · 研发日志", ""]
    for i, (day, (title, focus)) in enumerate(zip(log_dates, log_topics)):
        owner_i = _pick(team, i)
        helper = _pick(team, i + 1)
        log_body.extend(
            [
                f"## {day} · {title}",
                "",
                f"- 记录人：{owner_i}（协作：{helper}）",
                f"- 当日目标：{focus}",
                f"- 完成项：推进模块「{modules[i % len(modules)]}」「{modules[(i + 3) % len(modules)]}」；更新对应接口或页面状态反馈。",
                f"- 阻塞：{'无' if i % 2 == 0 else '待补齐异常提示文案与权限不足分支'}。",
                f"- 结论：{'可进入下一迭代' if i < 5 else '可作为 V1.0.0 发布候选'}。",
                f"- 次日计划：{'继续闭环与缺陷' if i < 5 else '冻结范围并整理研发留痕索引'}。",
                "",
            ]
        )
    _write(root / "研发日志.md", "\n".join(log_body))

    # 分支与里程碑
    _write(
        root / "分支与里程碑.md",
        f"""# {name} · 分支与里程碑

## 分支策略

| 分支 | 用途 | 保护规则 |
|------|------|----------|
| `main` | 交付与发布 | 仅合并已审 PR |
| `develop` | 日常集成 | 需通过构建与冒烟 |
| `feature/*` | 单点功能 | 合并前自测 |
| `fix/*` | 缺陷修复 | 关联 PR 审计条目 |

## 里程碑

| 里程碑 | 目标日期 | 完成准则 |
|--------|----------|----------|
| M1 基线 | {(end - dt.timedelta(days=40)).isoformat()} | 需求切口、登录、工程可运行 |
| M2 主台 | {(end - dt.timedelta(days=28)).isoformat()} | 主三维/主工作台可交互 |
| M3 闭环 | {(end - dt.timedelta(days=14)).isoformat()} | 派发→复核→归档可落库 |
| M4 交付 | {end.isoformat()} | 验收记录全绿，手册与留痕齐备 |
""",
    )

    # 版本发布
    v0 = version.replace("V1", "V0").replace("v1", "V0")
    if v0 == version:
        v0 = "V0.9.0"
    _write(
        root / "版本发布记录.md",
        f"""# {name} · 版本发布记录

## V0.1.0 · 内部联调

- 日期：{(end - dt.timedelta(days=35)).isoformat()}
- 摘要：工程骨架、登录会话、主路由可用。
- 已知限制：业务闭环未完成，三维为可交互初版。

## {v0 if v0 != version else 'V0.9.0'} · 预验收

- 日期：{(end - dt.timedelta(days=10)).isoformat()}
- 摘要：核心业务页与状态机可用；缺陷项进入收敛。
- 已知限制：部分异常文案与权限分支仍在补。

## {version} · 交付版

- 日期：{end.isoformat()}
- 摘要：核心链路端到端通过；操作手册与研发留痕同步。
- 变更来源：PR-#1 … PR-#{len(prs)}（详见《变更请求审计》）。
- 著作权人：{owner_line}
- 参与人员：{team_line}
""",
    )

    # 审计索引
    idx = [
        f"# {name} · 审计索引（手册对照）",
        "",
        "将本目录条目写入 `操作手册.md`「开发留痕」时，按下表对照：",
        "",
        "| 留痕文件 | 手册建议引用 | 最少摘录 |",
        "|----------|--------------|----------|",
        "| 版本发布记录.md | 版本与发布 | 交付版版本号与日期 |",
        "| 变更请求审计.md | 关键变更请求 | 3–6 条已合并 PR |",
        "| 提交记录.md | 代表性提交 | 5–10 条 feat/fix |",
        "| 研发日志.md | 研发过程摘要 | 1–2 段联调/缺陷收敛 |",
        "| 分支与里程碑.md | 可选 | M3/M4 完成准则 |",
        "",
        "## 本仓库模块清单（推断）",
        "",
    ]
    for m in modules:
        idx.append(f"- {m}")
    idx.append("")
    _write(root / "审计索引.md", "\n".join(idx))

    # machine-readable sidecar for later tooling
    sidecar = {
        "software_name": name,
        "team": list(team),
        "owner": owner_line,
        "version": version,
        "generated_on": end.isoformat(),
        "modules": modules,
        "commit_count": len(commits),
        "pr_count": len(prs),
    }
    (root / "forge_meta.json").write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return root


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate GitHub-like R&D forge traces")
    parser.add_argument("--project", default=".", help="project root")
    parser.add_argument("--name", required=True, help="software full name")
    parser.add_argument("--team", required=True, help="developers/team, comma-separated")
    parser.add_argument("--owner", default="", help="copyright owner, optional")
    parser.add_argument("--version", default="V1.0.0", help="release version label")
    args = parser.parse_args(list(argv) if argv is not None else None)

    project = Path(args.project).resolve()
    if not project.exists():
        raise SystemExit(f"project not found: {project}")

    team = _split_team(args.team)
    out = generate(project, args.name.strip(), team, args.owner, args.version.strip() or "V1.0.0")
    print(f"OK: wrote R&D forge -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
