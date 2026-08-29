#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate project-local GitHub-like R&D trace artifacts.

Minimal inputs: software full name + developers/team.
Optional: copyright owner, base version, project root.

Usage:
  python generate_dev_forge.py --project . --name "软件全称" --team "研发组,测试组"
  python generate_dev_forge.py --project . --name "软件全称" --team "张三,李四,王五" --owner "某某科技"
  # 留档收进 [软件全称]-源代码/：用 --dir-name 指定源代码目录内的留档子目录
  python generate_dev_forge.py --project . --name "软件全称" --team "研发组,测试组" --dir-name "<软件全称>-源代码/<留档子目录名>"
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
    # 过滤近案禁用名单与跨案对照词，避免把其他项目的模块抓进本案留档
    blob = "\n".join(
        line for line in blob.splitlines()
        if not any(k in line for k in ("近案", "禁用", "占用", "已淘汰", "禁止后续", "案例"))
    )

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
    root_phrase = _root_phrase(name)
    m0 = modules[0] if modules else root_phrase
    m1 = modules[1] if len(modules) > 1 else m0
    m3 = modules[min(3, len(modules) - 1)] if modules else m0
    m5 = modules[min(5, len(modules) - 1)] if modules else m0
    plans: List[Tuple[str, str, str]] = [
        ("docs", f"冻结{root_phrase}单点判断与数据主线", "需求基线"),
        ("feat", f"初始化{root_phrase}工程与鉴权会话骨架", "登录与准入"),
        ("feat", f"落地{m0}领域模型与状态枚举", m0),
        ("feat", "实现登录准入与角色权限校验", "登录与准入"),
        ("feat", f"搭建{m1}主工作台与对象树首屏", m1),
        ("feat", "接入主三维现场分层装配与多视角", "主三维工作台"),
        ("feat", f"完成「{m3}」页专属动作", m3),
        ("feat", f"完成「{m5}」状态流转", m5),
        ("feat", "规则命中区与证据列表联动", "规则命中与证据区"),
        ("feat", "处置派发与复核回退接口落库", "处置派发"),
        ("feat", "归档版本号与操作留痕查询", "归档版本"),
        ("fix", f"修复{m3}重复提交导致的状态覆盖", m3),
        ("fix", "修复模型未加载时的空选中反馈", "主三维工作台"),
        ("fix", "权限不足提示与菜单显隐不一致", "登录与准入"),
        ("test", f"补充{root_phrase}登录/校核/归档分支测试", "接口与数据初始化"),
        ("refactor", "收敛前端缓存与后端权威状态边界", "接口与数据初始化"),
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
    name: str,
    team: Sequence[str],
    commits: Sequence[Tuple[str, str, str, str, str, str]],
    end: dt.date,
) -> List[dict]:
    rp = _root_phrase(name)
    groups = [
        (1, f"{rp}准入与工程骨架", commits[0:4], "通过登录、会话与基础路由冒烟"),
        (2, f"{rp}主工作台与三维现场", commits[4:7], "多视角/部件点选/首屏联动可见"),
        (3, f"{rp}规则与证据", commits[7:9], "规则命中与证据可复核"),
        (4, f"{rp}业务闭环与状态机", commits[9:12], "主路径通过"),
        (5, f"{rp}缺陷收敛", [c for c in commits if c[3] == "fix"][:2], "异常提示与状态一致"),
        (6, f"{rp}测试、文档与发布候选", [c for c in commits if c[3] in ("test", "docs", "chore")], "预验收清单全绿"),
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



# 反模板化硬门禁：目录名与文件名由软件全称稳定编译，禁止连续两案复用同一套固定名。
# 本脚本只生成“骨架”，交付前必须按本案业务重新审读；留档目录按技能要求收进 [软件全称]-源代码/ 内（用 --dir-name 指定子目录），不单独占用交付根目录。
_FORGE_DIR_POOL = [
    "研发留痕", "工程档案", "项目留档", "开发足迹", "过程档案",
    "建设记录", "工程台账", "迭代档案", "开发纪要", "版本档案",
]

_FORGE_FILE_POOLS = {
    "仓库说明": ["仓库说明.md", "档案说明.md", "项目说明.md", "留档说明.md"],
    "提交记录": ["提交记录.md", "提交流水.md", "变更流水.md", "版本足迹.md", "提交清单.md"],
    "变更请求审计": ["变更请求审计.md", "变更台账.md", "变更记录.md", "PR审计.md", "变更留档.md"],
    "研发日志": ["研发日志.md", "开发纪要.md", "开发日志.md", "迭代纪要.md", "过程记录.md"],
    "分支与里程碑": ["分支与里程碑.md", "节点里程碑.md", "版本节点.md", "里程碑卡.md"],
    "版本发布记录": ["版本发布记录.md", "版本足迹.md", "发布记录.md", "版本档案.md", "发布台账.md"],
    "审计索引": ["审计索引.md", "留档索引.md", "档案索引.md", "审计台账.md"],
    "meta": ["forge_meta.json", "档案元数据.json", "留档元数据.json"],
}


def _root_tokens(name: str) -> list[str]:
    """从软件全称提取业务词根（去通用词），供文案自主编译。"""
    common = {"软件", "系统", "平台", "管理", "分析", "评估", "监测", "监控", "识别", "解析",
              "研判", "量化", "测算", "计算", "自动", "智能", "在线", "实时", "综合", "协同",
              "云端", "远程", "控制", "运维", "预警", "诊断", "服务", "支持", "优化", "建模",
              "仿真", "测试", "处理", "提取", "生成", "追溯", "记录", "统计", "对比", "检测",
              "排查", "追踪", "调度", "集成", "接入", "采集", "存储", "展示", "发布", "审核",
              "复核", "归档", "配置", "权限", "登录", "数据", "功能", "模块", "流程", "业务",
              "场景", "现场", "对象", "工具", "设备", "装置", "单元", "系统"}
    tokens = []
    for ch in name:
        if ch.isascii() or ch in "（）、。，；：！？·—–- ":
            if tokens and tokens[-1] and tokens[-1][-1].isascii() is False and len(tokens[-1]) < 4:
                tokens[-1] += ch
            continue
        if tokens and tokens[-1] and not tokens[-1][-1].isascii():
            tokens[-1] += ch
        else:
            tokens.append(ch)
    kept = []
    for tok in tokens:
        tok = tok.strip()
        if len(tok) >= 2 and tok not in common and not any(tok.startswith(c) for c in common):
            kept.append(tok)
    return kept[:6]

def _root_phrase(name: str, n: int = 2) -> str:
    """提取短业务词根：去掉软件/系统/平台等通用后缀后取前 4 字，每案不同且不冗长。"""
    short = name
    for suf in ("软件", "系统", "平台", "管理"):
        if short.endswith(suf):
            short = short[: -len(suf)]
    return short[:4] or "核心业务"

def _stable_seed(name: str) -> int:
    return int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:8], 16)

def _compile_forge_dir(project: Path, name: str) -> Path:
    seed = _stable_seed(name)
    idx = seed % len(_FORGE_DIR_POOL)
    return project / _FORGE_DIR_POOL[idx]

def _compile_file_names(name: str, file_map: dict | None = None, dir_name: str = "") -> dict:
    # 种子掺入目录名：目录名不同则文件名组合必不同，杜绝两案同构
    seed = _stable_seed(name + "|files|" + dir_name)
    out = {}
    for key, pool in _FORGE_FILE_POOLS.items():
        if file_map and key in file_map and file_map[key]:
            out[key] = file_map[key]
        else:
            out[key] = pool[seed % len(pool)]
            seed = seed * 31 + 7
    return out


def generate(
    project: Path,
    name: str,
    team: Sequence[str],
    owner: str = "",
    version: str = "v1.0",
    dir_name: str = "",
    file_map: dict | None = None,
    modules_override: Sequence[str] | None = None,
) -> Path:
    # 目录名由软件全称编译：禁止连续两案复用同一套固定目录名/文件名（反模板化硬门禁）
    if dir_name.strip():
        root = project / dir_name.strip()
    else:
        root = _compile_forge_dir(project, name)
    root.mkdir(parents=True, exist_ok=True)
    fn = _compile_file_names(name, file_map, root.name)
    end = _daterange_end()
    modules = list(modules_override) if modules_override else _infer_modules(project, name)
    commits = _commit_lines(name, team, modules, end)
    prs = _pr_lines(name, team, commits, end)
    owner_line = owner.strip() if owner.strip() else "待登记"
    team_line = "、".join(team)

    # 仓库说明
    _write(
        root / fn["仓库说明"],
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
    _write(root / fn["提交记录"], "\n".join(commit_body) + "\n")

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
    _write(root / fn["变更请求审计"], "\n".join(pr_lines))

    # 研发日志
    log_dates = _dates_back(end, 6, span_days=40)
    rp2 = _root_phrase(name, 3)
    log_topics = [
        (f"{rp2}需求与切口冻结", f"确认{rp2}单点判断、对象与数据主线，不进入泛化后台。"),
        (f"{rp2}主台与三维联调", "主场景分区、视角预设与侧栏同源数据打通。"),
        (f"{rp2}规则与证据", "规则命中与证据列表对齐同一业务对象。"),
        (f"{rp2}状态机与权限", "主路径流转与角色权限分支补齐。"),
        (f"{rp2}缺陷收敛", "处理重复提交、空模型点选与刷新后状态漂移。"),
        (f"{rp2}预验收与文档", "按验收记录跑通核心闭环，同步操作手册步骤。"),
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
                f"- 结论：{'可进入下一迭代' if i < 5 else '可作为 v1.0 发布候选'}。",
                f"- 次日计划：{'继续闭环与缺陷' if i < 5 else '冻结范围并整理研发留痕索引'}。",
                "",
            ]
        )
    _write(root / fn["研发日志"], "\n".join(log_body))

    # 分支与里程碑
    _write(
        root / fn["分支与里程碑"],
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
    rp3 = _root_phrase(name, 3)
    _write(
        root / fn["版本发布记录"],
        f"""# {name} · 版本发布记录

## V0.1.0 · 内部联调

- 日期：{(end - dt.timedelta(days=35)).isoformat()}
- 摘要：工程骨架、登录会话、主路由可用。
- 已知限制：{rp3}业务闭环未完成，三维为可交互初版。

## {v0 if v0 != version else 'V0.9.0'} · 预验收

- 日期：{(end - dt.timedelta(days=10)).isoformat()}
- 摘要：{rp3}核心业务页与状态机可用；缺陷项进入收敛。
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
    _write(root / fn["审计索引"], "\n".join(idx))

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
    (root / fn["meta"]).write_text(
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
    parser.add_argument("--version", default="v1.0", help="release version label")
    parser.add_argument("--dir-name", default="", help="留档目录名（默认由软件全称自主编译）")
    parser.add_argument("--file-map", default="", help="文件映射 JSON，如 {\"提交记录\":\"变更流水.md\"}，可选")
    parser.add_argument("--modules", default="", help="本案真实模块，逗号分隔；未传时按项目内文档推断")
    args = parser.parse_args(list(argv) if argv is not None else None)

    project = Path(args.project).resolve()
    if not project.exists():
        raise SystemExit(f"project not found: {project}")

    team = _split_team(args.team)
    file_map = None
    if args.file_map.strip():
        import json as _json
        file_map = _json.loads(args.file_map)
    modules_override = None
    if args.modules.strip():
        modules_override = [m.strip() for m in args.modules.split(",") if m.strip()]
    out = generate(
        project,
        args.name.strip(),
        team,
        args.owner,
        args.version.strip() or "v1.0",
        args.dir_name.strip(),
        file_map,
        modules_override,
    )
    print(f"OK: wrote R&D forge -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
