#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate original Xiaohongshu posts from project notes or maomp scan JSON.

Fused with xiaohongshu-post-writer patterns:
- stage raw: screening facts only
- stage polished: publish package with titles/cover/tags/compliance
- stage both: default
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_COVER_MODEL = "gemini-3.1-flash-image"


LEVEL_RANK = {
    "可优先验证": 3,
    "可小成本验证": 2,
    "谨慎观察": 1,
    "不建议": 0,
}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def load_items_from_json(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items") or []
    result = []
    for it in items:
        result.append(
            {
                "title": it.get("title") or "",
                "level": it.get("level") or "谨慎观察",
                "score": int(it.get("score") or 0),
                "reason": it.get("reason") or "",
                "link": it.get("link") or "",
                "category": it.get("category") or "",
            }
        )
    return result


def load_items_from_notes(path: Path) -> list[dict[str, Any]]:
    """Parse simple markdown notes."""
    text = path.read_text(encoding="utf-8")
    section = "谨慎观察"
    items: list[dict[str, Any]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("##"):
            name = line.lstrip("#").strip()
            if "推荐" in name or "优先" in name:
                section = "可优先验证"
            elif "观察" in name:
                section = "谨慎观察"
            elif "避雷" in name or "不建议" in name:
                section = "不建议"
            elif "小成本" in name:
                section = "可小成本验证"
            continue
        if line.startswith("-"):
            body = line.lstrip("- ").strip()
            parts = [p.strip() for p in re.split(r"[｜|]", body)]
            title = parts[0] if parts else body
            reason = parts[1] if len(parts) > 1 else ""
            audience = parts[2] if len(parts) > 2 else ""
            score = {
                "可优先验证": 80,
                "可小成本验证": 60,
                "谨慎观察": 45,
                "不建议": 20,
            }.get(section, 45)
            # keep structured fields so later split does not crush judgment/audience
            items.append(
                {
                    "title": title,
                    "level": section,
                    "score": score,
                    "reason": reason,
                    "audience": audience,
                    "validation": "",
                    "link": "",
                    "category": "",
                }
            )
            # if audience itself embeds 小验证, peel it here
            if "小验证" in (items[-1]["audience"] or ""):
                import re as _re
                m = _re.search(r"小验证[:：]\s*(.+)$", items[-1]["audience"])
                if m:
                    items[-1]["validation"] = m.group(1).strip()
                    items[-1]["audience"] = items[-1]["audience"][: m.start()].strip(" ；;,，")
            if "小验证" in (items[-1]["reason"] or ""):
                import re as _re
                m = _re.search(r"小验证[:：]\s*(.+)$", items[-1]["reason"])
                if m:
                    items[-1]["validation"] = items[-1]["validation"] or m.group(1).strip()
                    items[-1]["reason"] = items[-1]["reason"][: m.start()].strip(" ；;,，")
    return items


def classify(items: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rec = [x for x in items if x["level"] in ("可优先验证", "可小成本验证")]
    obs = [x for x in items if x["level"] == "谨慎观察"]
    bad = [x for x in items if x["level"] == "不建议"]
    rec = sorted(rec, key=lambda x: (LEVEL_RANK.get(x["level"], 0), x["score"]), reverse=True)
    obs = sorted(obs, key=lambda x: x["score"], reverse=True)
    bad = sorted(bad, key=lambda x: x["score"])
    return {"recommend": rec[:2], "observe": obs[:2], "avoid": bad[:3], "all": items}


def short_name(title: str) -> str:
    t = re.sub(r"[【\[][^】\]]*[】\]]", "", title)
    t = re.sub(r"(实战课|体系课|训练营|从0到1|全流程|保姆级|最新|揭秘).*$", "", t)
    t = re.sub(r"\s+", "", t)
    return t[:28] if t else title[:28]


def split_reason_audience(item: dict[str, Any]) -> tuple[str, str, str]:
    judgment = (item.get("reason") or "").strip()
    audience = (item.get("audience") or "").strip()
    validation = (item.get("validation") or "").strip()
    blob = "；".join([x for x in [judgment, audience] if x])
    if not validation:
        m_val = re.search(r"小验证[:：]\s*(.+)$", blob)
        if m_val:
            validation = m_val.group(1).strip()
            blob = blob[: m_val.start()].rstrip(" ；;,，")
            # reassign judgment/audience only when structured audience missing
            if not audience and "；" in blob:
                parts = [p.strip() for p in blob.split("；") if p.strip()]
                judgment = parts[0]
                audience = "；".join(parts[1:])
            else:
                judgment = judgment or blob
    audience = re.sub(r"^适合", "", audience).strip(" ：:")
    # if judgment still contains a trailing "没货..." style second clause from notes, keep it in judgment
    return judgment, audience, validation


def original_angle(item: dict[str, Any]) -> str:
    title = item["title"]
    level = item["level"]
    reason = item.get("reason") or ""
    if level == "不建议":
        if any(k in title + reason for k in ["挂G", "挂机", "外挂", "矩阵", "防风", "跳人脸"]):
            return "高风险自动化/风控类，普通人容易封号或踩合规线"
        if any(k in title for k in ["日入", "月入", "躺赚", "保底"]):
            return "收益包装过重，缺少可验证客户与交付闭环"
        return "更像课程营销，不像可落地生意"
    if level == "谨慎观察":
        return "信息还不够，先看客户从哪来、交付是什么，再决定要不要做"
    if any(k in title for k in ["代运营", "获客", "本地", "服务", "设计", "剪辑", "咨询"]):
        return "能拆成对客户收费的服务，适合小范围验证"
    return "有一定可行性，但要先做小样，再谈放大"


def extract_validation(text: str) -> str:
    m = re.search(r"(小验证[:：]?.*)$", text)
    if m:
        return m.group(1).replace("小验证：", "").replace("小验证:", "").strip()
    if "天" in text and any(k in text for k in ["测", "样", "验证", "反馈"]):
        return text
    return ""


def item_lines(item: dict[str, Any], idx: int | None = None) -> list[str]:
    name = short_name(item["title"])
    judgment, audience, validation = split_reason_audience(item)
    if not judgment:
        judgment = original_angle(item)
    if not validation:
        validation = extract_validation(judgment) or extract_validation(audience)
    lines = []
    prefix = f"{idx}. " if idx is not None else "- "
    lines.append(f"{prefix}{name}")
    lines.append(f"判断：{judgment}")
    if audience:
        lines.append(f"适合：{audience}")
    else:
        if item["level"] in ("可优先验证", "可小成本验证"):
            lines.append("适合：能自己找到客户、并完成最小交付的人")
        elif item["level"] == "谨慎观察":
            lines.append("适合：先研究方法、不急着当主业的人")
        else:
            lines.append("适合：谁都不建议当主业")
    if item["level"] in ("可优先验证", "可小成本验证"):
        if not validation:
            validation = "3-7天做出最小样稿，找1个真实对象要反馈，再决定是否继续"
        lines.append(f"小验证：{validation}")
    return lines


def build_titles(bundle: dict[str, list[dict[str, Any]]], total: int) -> list[str]:
    rec_n = len(bundle["recommend"])
    avoid_n = len(bundle["avoid"])
    top = short_name(bundle["recommend"][0]["title"]) if bundle["recommend"] else "可验证服务"
    return [
        f"今天看了{total}个项目，能做的只有{rec_n}个",
        f"别先问赚不赚钱，先问有没有客户｜今日可做{rec_n}个",
        f"这{avoid_n}类我直接避雷，只留下{top}",
    ]


def build_cover_prompt(bundle: dict[str, list[dict[str, Any]]], total: int, cover_text: str) -> dict[str, str]:
    rec_n = len(bundle["recommend"])
    obs_n = len(bundle["observe"])
    avoid_n = len(bundle["avoid"])

    prompt_zh = (
        f"小红书爆款风格高吸引力封面海报，比例3:4竖屏。设计风格：极简高对比现代创业日记卡片，"
        f"暖白与柔和灰米色拼色背景。画面中央为高质感半透明玻璃感卡片，印有粗体黑字与橙色高亮大字：\n"
        f"“今日可做 {rec_n} 个 | 观察 {obs_n} · 避雷 {avoid_n} | 共看 {total} 条线索 | 项目筛选日记”。\n"
        f"卡片四周点缀极简矢量勾选框、放大镜、警示角标和数据卡片元素，配色为橙色、深灰与白色，视觉清晰醒目，极具点击欲望。"
    )
    prompt_en = (
        f"Xiaohongshu style high-converting vertical cover poster, 3:4 aspect ratio. Clean, modern project screening review card aesthetic, "
        f"soft off-white and warm beige gradient background. Translucent glassmorphism card in center displaying bold high contrast text: "
        f"'今日可做 {rec_n} 个', '观察 {obs_n} · 避雷 {avoid_n}', '共看 {total} 条线索', '项目筛选日记'. "
        f"Minimalist decorative elements like checkboxes, magnifying glass icon, warning badge, vibrant orange accent, ultra clear typography, high click-through rate."
    )
    return {
        "model": DEFAULT_COVER_MODEL,
        "aspect_ratio": "3:4",
        "prompt_zh": prompt_zh,
        "prompt_en": prompt_en,
    }


def build_cover(bundle: dict[str, list[dict[str, Any]]], total: int) -> str:
    rec_n = len(bundle["recommend"])
    avoid_n = len(bundle["avoid"])
    return "\n".join(
        [
            f"今日可做 {rec_n} 个",
            f"观察 {len(bundle['observe'])} · 避雷 {avoid_n}",
            f"共看 {total} 条线索",
            "项目筛选日记",
        ]
    )


def build_raw_body(bundle: dict[str, list[dict[str, Any]]], total: int, persona: str) -> str:
    lines: list[str] = []
    lines.append(f"【{persona}】")
    lines.append(f"今天一共看了 {total} 条线索。")
    lines.append("")
    lines.append("【今天可关注】")
    if bundle["recommend"]:
        for i, it in enumerate(bundle["recommend"], 1):
            lines.extend(item_lines(it, i))
            lines.append("")
    else:
        lines.append("今天没有达到“可优先验证”的项。")
        lines.append("")
    lines.append("【可以观察】")
    if bundle["observe"]:
        for it in bundle["observe"]:
            lines.extend(item_lines(it))
        lines.append("")
    else:
        lines.append("- 暂无")
        lines.append("")
    lines.append("【建议避雷】")
    if bundle["avoid"]:
        for it in bundle["avoid"]:
            lines.extend(item_lines(it))
        lines.append("")
    else:
        lines.append("- 暂无")
        lines.append("")
    lines.append("【我的筛选标准】")
    lines.append("1. 客户是谁，能不能找到")
    lines.append("2. 交付物是什么，能不能7天做样稿")
    lines.append("3. 是否必须先投流/买课/买软件")
    lines.append("4. 有没有封号、侵权、资金风险")
    lines.append("")
    if bundle["recommend"]:
        top = short_name(bundle["recommend"][0]["title"])
        lines.append("【今日结论】")
        lines.append(f"如果只能选一个方向，优先看：{top}。")
        lines.append("核心不是“项目新不新”，而是“你能不能把它变成可收费服务”。")
    else:
        lines.append("【今日结论】")
        lines.append("今天先不追新项目，把筛选标准练熟比盲目跟更重要。")
    return "\n".join(lines).strip() + "\n"


def build_polished_body(bundle: dict[str, list[dict[str, Any]]], total: int, persona: str) -> str:
    rec_n = len(bundle["recommend"])
    avoid_n = len(bundle["avoid"])
    lines: list[str] = []
    lines.append(f"今天看了{total}个项目，最后觉得能做的只有{rec_n}个。")
    lines.append("不是看热闹，是按“有没有客户、7天能不能小验证”筛的。")
    lines.append("")
    lines.append("先说结论：")
    lines.append(f"可做 {rec_n} 个 · 观察 {len(bundle['observe'])} 个 · 避雷 {avoid_n} 个")
    lines.append("")
    lines.append("【今天可做】")
    if bundle["recommend"]:
        for i, it in enumerate(bundle["recommend"], 1):
            name = short_name(it["title"])
            judgment, audience, validation = split_reason_audience(it)
            judgment = judgment or original_angle(it)
            if not validation:
                validation = extract_validation(judgment) or extract_validation(audience) or "3-7天做最小样稿，找1个真实对象要反馈"
            if not audience:
                audience = "能自己找到客户、并完成最小交付的人"
            lines.append(f"{i}) {name}")
            lines.append(f"- 为什么留下：{judgment}")
            lines.append(f"- 适合谁：{audience}")
            lines.append(f"- 小验证：{validation}")
            lines.append("")
    else:
        lines.append("今天没有达到“可做”线的项目。")
        lines.append("")
    lines.append("【可以观察，先别All in】")
    if bundle["observe"]:
        for it in bundle["observe"]:
            name = short_name(it["title"])
            judgment, audience, _validation = split_reason_audience(it)
            judgment = judgment or original_angle(it)
            extra = f"（{audience}）" if audience else ""
            lines.append(f"- {name}：{judgment}{extra}")
    else:
        lines.append("- 暂无")
    lines.append("")
    lines.append("【建议直接避雷】")
    if bundle["avoid"]:
        for it in bundle["avoid"]:
            name = short_name(it["title"])
            judgment, _audience, _validation = split_reason_audience(it)
            judgment = judgment or original_angle(it)
            lines.append(f"- {name}：{judgment}")
    else:
        lines.append("- 暂无")
    lines.append("")
    lines.append("【我的4道筛选】")
    lines.append("1. 客户是谁，能不能找到")
    lines.append("2. 交付是什么，7天能不能出样")
    lines.append("3. 是不是必须先买课/投流/买工具")
    lines.append("4. 有没有封号、侵权、资金风险")
    lines.append("")
    if bundle["recommend"]:
        top = short_name(bundle["recommend"][0]["title"])
        lines.append("【今日只留一句】")
        lines.append(f"如果只选一个，我会先看：{top}。")
        lines.append("先把它做成对一个人有用的服务，再谈什么矩阵和放大。")
    else:
        lines.append("【今日只留一句】")
        lines.append("今天与其追新项目，不如把筛选标准用熟。")
    lines.append("")
    lines.append("你也在天天看项目、却不知道该不该做？")
    lines.append("评论“清单”或“检测”，发你最纠结的方向，我按可验证标准帮你看。")
    lines.append("")
    lines.append("不荐挂机，不吹暴富，只讲可验证路径。")
    lines.append(f"— {persona}")
    return "\n".join(lines).strip() + "\n"


def build_tags(bundle: dict[str, list[dict[str, Any]]]) -> str:
    tags = ["#副业", "#项目筛选", "#避雷", "#普通人副业", "#创业日记", "#可验证"]
    blob = " ".join(short_name(x["title"]) for x in bundle["all"][:6])
    if "小红书" in blob:
        tags.append("#小红书运营")
    if "AI" in blob:
        tags.append("#AI创业")
    if any(k in blob for k in ["代运营", "获客", "图文"]):
        tags.append("#接单思维")
    seen = set()
    out = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return " ".join(out[:8])


def compliance_block() -> list[str]:
    return [
        "## 合规与去AI味检查（post-writer）",
        "- [ ] 无收益承诺 / 稳赚 / 保底 / 日入月入包装",
        "- [ ] 无网盘链接、提取码、课程原文搬运",
        "- [ ] 无绝对化：必火、百分百、全网第一",
        "- [ ] 未编造亲测收入或虚假经历",
        "- [ ] 开头是具体反差，不是空泛时代开头",
        "- [ ] 每段都钉在事实或判断上，少堆形容词",
        "- [ ] 人设像“项目过滤器”，不像成功学导师",
        "- [ ] 评论引导是有信息量的问题，不是空要赞藏",
        "- [ ] 若大量AI生成，发布时按平台要求考虑AI标识",
    ]


def image_order_block(bundle: dict[str, list[dict[str, Any]]]) -> list[str]:
    lines = [
        "## 图片排序建议",
        "1. 封面：大字结论（今日可做X / 避雷Y）",
        "2. 可做项目卡片（判断 + 小验证）",
    ]
    if bundle["observe"]:
        lines.append("3. 观察项：为什么先别All in")
        lines.append("4. 避雷项：风险点一句话")
        lines.append("5. 4道筛选标准")
        lines.append("6. 今日结论 + 互动引导")
    else:
        lines.append("3. 避雷项：风险点一句话")
        lines.append("4. 4道筛选标准")
        lines.append("5. 今日结论 + 互动引导")
    return lines


def build_week_plan() -> list[dict[str, str]]:
    themes = [
        ("反差盘点", "今天看了N个项目，能做的只有X个"),
        ("推荐深拆", "这个方向为什么能做成服务"),
        ("避雷专题", "别碰这几类项目"),
        ("执行方法", "7天验证一个项目的方法"),
        ("行业视角", "商家真正愿意付费的服务是什么"),
        ("复盘日记", "我这周筛项目的标准变了吗"),
        ("互动征集", "把你看到的项目发我，我帮你排雷"),
    ]
    return [
        {"day": f"D{i}", "theme": theme, "title_pattern": title}
        for i, (theme, title) in enumerate(themes, 1)
    ]


def render_markdown(
    *,
    date: str,
    source: str,
    stage: str,
    persona: str,
    bundle: dict[str, list[dict[str, Any]]],
    raw_body: str,
    polished_body: str,
    titles: list[str],
    cover: str,
    cover_prompt: dict[str, str],
    tags: str,
) -> str:
    chosen_title = titles[0]
    body = polished_body if stage in ("polished", "both") else raw_body
    lines = [
        f"# 小红书笔记草稿（{date}）",
        "",
        f"- 来源模式：{source}",
        f"- 生成阶段：{stage}",
        f"- 融合技能：xhs-project-digest + xiaohongshu-post-writer",
        f"- 人设：{persona}",
        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 推荐标题（可A/B）",
    ]
    for i, t in enumerate(titles, 1):
        mark = "（主推）" if i == 1 else ""
        lines.append(f"{i}. {t}{mark}")
    lines.extend(
        [
            "",
            "## 最终标题（默认）",
            chosen_title,
            "",
            "## 封面文案与生图（指定模型：gemini-3.1-flash-image）",
            f"- **指定模型**：`{cover_prompt.get('model', 'gemini-3.1-flash-image')}`",
            "- **图片比例**：3:4（小红书标准竖屏）",
            "- **封面大字排版**：",
            "```",
            cover,
            "```",
            "- **Gemini 3.1 Flash Image 提示词 (中文)**：",
            "```",
            cover_prompt.get("prompt_zh", ""),
            "```",
            "- **Gemini 3.1 Flash Image 提示词 (English)**：",
            "```",
            cover_prompt.get("prompt_en", ""),
            "```",
            "",
            "## 正文",
            body.strip(),
            "",
            "## 话题",
            tags,
            "",
            "## 评论区引导",
            "评论“清单”或“检测”，发你今天最纠结的方向，我按可验证标准帮你看。",
            "",
        ]
    )
    lines.extend(image_order_block(bundle))
    lines.append("")
    lines.extend(compliance_block())
    lines.extend(
        [
            "",
            "## 发布前检查（筛选硬规则）",
            "发布前自查：无网盘链接、无提取码、无课程原文、无收益承诺、无绝对化用语。",
            "",
            "## 发布动作",
            "1. 粘贴标题和正文",
            "2. 加话题标签",
            "3. 封面用大字结论图",
            "4. 按图片排序建议排版",
            "5. 先自己预览一遍",
            "6. 发布后置顶评论引导“清单”",
            "",
        ]
    )
    if stage == "both":
        lines.extend(["## 附录：事实层原文（raw）", raw_body.strip(), ""])
    lines.extend(
        [
            "## 人工润色提示",
            "- 把“我”改成你的真实口吻",
            "- 若某条不是你亲自判断的，删掉或改成观察",
            "- 需要更强个人经历时，只补真实细节，不编造结果",
            "- 仍觉得模板感重：把正文丢给 $xiaohongshu-post-writer 做 Rewrite/Audit",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate fused Xiaohongshu project-digest posts")
    parser.add_argument("--json", default="", help="maomp latest.json path")
    parser.add_argument("--notes", default="", help="self summary markdown path")
    parser.add_argument("--out-dir", default=r"E:\machengji\xhs-project-digest\output")
    parser.add_argument("--persona", default="每天筛项目的实战记录者")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument(
        "--stage",
        default="both",
        choices=["raw", "polished", "both"],
        help="raw=事实稿, polished=发布润色包, both=两者",
    )
    args = parser.parse_args()

    source = ""
    items: list[dict[str, Any]] = []
    if args.notes:
        items = load_items_from_notes(Path(args.notes))
        source = f"self-notes:{args.notes}"
    elif args.json:
        items = load_items_from_json(Path(args.json))
        source = f"scan-json:{args.json}"
    else:
        default_json = Path(r"E:\machengji\maomp-monitor\latest.json")
        default_notes = Path(r"E:\machengji\xhs-project-digest\input\today-notes.md")
        if default_notes.exists() and default_notes.read_text(encoding="utf-8").strip():
            items = load_items_from_notes(default_notes)
            source = f"self-notes:{default_notes}"
        elif default_json.exists():
            items = load_items_from_json(default_json)
            source = f"scan-json:{default_json}"
        else:
            raise SystemExit("No input. Provide --notes or --json, or create input/today-notes.md")

    if not items:
        raise SystemExit("No project items parsed from input")

    bundle = classify(items)
    total = len(bundle["all"])
    titles = build_titles(bundle, total)
    cover = build_cover(bundle, total)
    cover_prompt = build_cover_prompt(bundle, total, cover)
    raw_body = build_raw_body(bundle, total, args.persona)
    polished_body = build_polished_body(bundle, total, args.persona)
    tags = build_tags(bundle)

    post = {
        "title": titles[0],
        "title_options": titles,
        "cover_text": cover,
        "cover_model": DEFAULT_COVER_MODEL,
        "cover_image_config": cover_prompt,
        "body": polished_body if args.stage in ("polished", "both") else raw_body,
        "body_raw": raw_body,
        "body_polished": polished_body,
        "tags": tags,
        "comment_cta": "评论“清单”或“检测”，发你今天最纠结的方向，我按可验证标准帮你看。",
        "publish_note": "发布前自查：无网盘链接、无提取码、无课程原文、无收益承诺、无绝对化用语。",
        "persona": args.persona,
        "stage": args.stage,
        "fusion": ["xhs-project-digest", "xiaohongshu-post-writer"],
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    md_path = out_dir / f"xhs-{args.date}.md"
    json_path = out_dir / f"xhs-{args.date}.json"
    week_path = out_dir / "week-content-plan.md"

    write_text(
        md_path,
        render_markdown(
            date=args.date,
            source=source,
            stage=args.stage,
            persona=args.persona,
            bundle=bundle,
            raw_body=raw_body,
            polished_body=polished_body,
            titles=titles,
            cover=cover,
            cover_prompt=cover_prompt,
            tags=tags,
        ),
    )
    write_text(
        json_path,
        json.dumps(
            {
                "date": args.date,
                "source": source,
                "post": post,
                "bundle": {
                    "recommend": bundle["recommend"],
                    "observe": bundle["observe"],
                    "avoid": bundle["avoid"],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    week = build_week_plan()
    week_lines = ["# 7天小红书内容计划", ""]
    for row in week:
        week_lines.append(f"- {row['day']}｜{row['theme']}｜标题方向：{row['title_pattern']}")
    week_lines.append("")
    week_lines.append("> 每天只发1条。先筛选事实，再做人设润色；不搬运原文。")
    write_text(week_path, "\n".join(week_lines) + "\n")

    print(f"完成：{md_path}")
    print(f"JSON：{json_path}")
    print(f"周计划：{week_path}")
    print(f"阶段：{args.stage}")
    print(f"标题：{post['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
