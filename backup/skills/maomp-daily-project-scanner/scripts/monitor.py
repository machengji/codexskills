#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Daily scanner for maomp.vip entrepreneurship project clues.

Supports optional member login via local credentials.json.
Never print or write passwords into reports.
"""

from __future__ import annotations

import argparse
import csv
import html
import http.cookiejar
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

FEED_URL = "https://www.maomp.vip/feed/"
DEFAULT_DATA_DIR = Path(r"E:\machengji\maomp-monitor")

POSITIVE = [
    "人工智能", "AI", "Codex", "自动化", "软件", "工具", "知识库", "客服", "网站",
    "开发", "办公", "电商", "获客", "商家", "企业服务", "本地生活", "设计", "翻译",
    "远程支持", "GEO", "外贸", "标书", "方案", "智能体", "Agent", "系统",
]
CONCRETE = [
    "流程", "SOP", "案例", "客户", "交付", "服务", "报价", "成本", "步骤",
    "工具", "数据", "复购", "售后", "闭环", "模板", "清单", "课程目录", "网盘",
]
HYPE = [
    "日入", "月入", "躺赚", "躺賺", "暴利", "稳赚", "稳賺", "当天变现", "保底收入",
    "轻松月入", "一夜暴富", "无需经验", "零成本", "不封号", "日入过万", "月入过万",
]
RISK = [
    "挂机", "挂G", "外挂", "破解", "搬运", "刷量", "刷单", "写真", "男粉", "色情",
    "赌博", "博彩", "黑产", "规避风控", "不封号", "截流", "租号", "跳人脸", "防风",
    "报白", "矩阵放大", "解锁会员",
]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def strip_html(value: str) -> str:
    if not value:
        return ""
    value = re.sub(r"(?is)<script.*?</script>", " ", value)
    value = re.sub(r"(?is)<style.*?</style>", " ", value)
    value = re.sub(r"(?is)<noscript.*?</noscript>", " ", value)
    value = re.sub(r"(?is)<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def xml_text(node: ET.Element | None) -> str:
    if node is None:
        return ""
    return "".join(node.itertext()).strip()


class MaompClient:
    def __init__(self, data_dir: Path, credentials_path: Path | None = None, no_proxy: bool = False):
        self.data_dir = data_dir
        self.credentials_path = credentials_path or (data_dir / "credentials.json")
        self.cookie_path = data_dir / "cookies.txt"
        self.cj = http.cookiejar.MozillaCookieJar(str(self.cookie_path))
        if self.cookie_path.exists():
            try:
                self.cj.load(ignore_discard=True, ignore_expires=True)
            except Exception:
                self.cj = http.cookiejar.MozillaCookieJar(str(self.cookie_path))
        handlers = [urllib.request.HTTPCookieProcessor(self.cj)]
        if no_proxy:
            handlers.append(urllib.request.ProxyHandler({}))
        self.opener = urllib.request.build_opener(*handlers)
        self.opener.addheaders = [
            (
                "User-Agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) maomp-daily-project-scanner/1.2",
            ),
            ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
        ]
        self.logged_in = False
        self.login_user = ""

    def fetch(self, url: str, timeout: int = 45, data: bytes | None = None, headers: dict | None = None) -> str:
        req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        with self.opener.open(req, timeout=timeout) as resp:
            raw = resp.read()
        for enc in ("utf-8", "gb18030", "latin-1"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="replace")

    def _has_login_cookie(self) -> bool:
        return any(c.name.startswith("wordpress_logged_in_") for c in self.cj)

    def _load_credentials(self) -> dict:
        if not self.credentials_path.exists():
            return {}
        try:
            data = json.loads(self.credentials_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def ensure_login(self) -> bool:
        cred = self._load_credentials()
        username = str(cred.get("username") or "").strip()
        if self._has_login_cookie():
            self.logged_in = True
            self.login_user = username
            return True
        if not cred:
            self.logged_in = False
            return False
        password = str(cred.get("password") or "")
        login_url = str(cred.get("login_url") or "https://www.maomp.vip/wp-login.php")
        base_url = str(cred.get("base_url") or "https://www.maomp.vip")
        if not username or not password:
            self.logged_in = False
            return False

        # warm login page cookies
        try:
            self.fetch(login_url, timeout=30)
        except Exception:
            pass

        form = {
            "log": username,
            "pwd": password,
            "wp-submit": "登录",
            "redirect_to": base_url.rstrip("/") + "/",
            "testcookie": "1",
        }
        body = urllib.parse.urlencode(form).encode("utf-8")
        try:
            self.fetch(
                login_url,
                timeout=45,
                data=body,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": login_url,
                },
            )
        except Exception:
            self.logged_in = False
            return False

        self.logged_in = self._has_login_cookie()
        if self.logged_in:
            self.login_user = username
            try:
                self.cj.save(ignore_discard=True, ignore_expires=True)
            except Exception:
                pass
        return self.logged_in


def parse_feed(content: str) -> list[dict[str, Any]]:
    root = ET.fromstring(content)
    channel = root.find("channel")
    if channel is None:
        return []
    items = []
    for item in channel.findall("item"):
        link = xml_text(item.find("link"))
        if not link:
            continue
        pub_raw = xml_text(item.find("pubDate"))
        try:
            published = parsedate_to_datetime(pub_raw).astimezone()
        except Exception:
            published = datetime.now().astimezone()
        cats = [xml_text(c) for c in item.findall("category") if xml_text(c)]
        items.append(
            {
                "link": link,
                "title": xml_text(item.find("title")),
                "description": strip_html(xml_text(item.find("description"))),
                "category": "、".join(cats),
                "published": published,
            }
        )
    items.sort(key=lambda x: x["published"], reverse=True)
    return items


def extract_article_html(page_html: str) -> str:
    m = re.search(r"(?is)<article\b[^>]*>.*?</article>", page_html)
    return m.group(0) if m else page_html


def extract_member_extras(page_html: str, article_html: str) -> dict[str, Any]:
    text = strip_html(article_html)
    links = re.findall(r"https?://[^\s\"'<>]+", page_html)
    download_links = []
    for u in links:
        low = u.lower()
        if any(k in low for k in [
            "pan.baidu.com", "pan.quark.cn", "aliyundrive.com", "alipan.com",
            "lanzou", "123pan.com", "cloud.189.cn", "share.",
        ]):
            if u not in download_links:
                download_links.append(u)
    extract_codes = re.findall(r"(?:提取码|密码|pwd)[:：\s]*([a-zA-Z0-9]{3,8})", text, flags=re.I)
    extract_codes = list(dict.fromkeys(extract_codes))
    gated = bool(re.search(r"会员登录就能查看|加入会员联系客服|本项目仅供会员下载学习", text))
    has_catalog = "课程目录" in text or "课程内容" in text
    has_outline = bool(re.search(r"第\s*\d+\s*节|第[一二三四五六七八九十]+[章节课]", text))
    return {
        "download_links": download_links[:10],
        "extract_codes": extract_codes[:10],
        "member_gated_text": gated and not download_links,
        "has_course_catalog": has_catalog or has_outline,
        "body_len": len(text),
    }


def word_hits(text: str, words: list[str]) -> list[str]:
    lower = text.lower()
    return [w for w in words if w.lower() in lower]


def assess(title: str, description: str, body: str, category: str, extras: dict[str, Any]) -> dict[str, Any]:
    text = f"{title} {description} {body} {category}"
    positive_hits = word_hits(text, POSITIVE)
    concrete_hits = word_hits(text, CONCRETE)
    hype_hits = word_hits(text, HYPE)
    risk_hits = word_hits(text, RISK)

    score = 45
    score += min(20, len(positive_hits) * 4)
    score += min(15, len(concrete_hits) * 3)
    if re.search(r"真实客户|企业客户|本地商家|服务商|收费|报价|交付", text):
        score += 10
    if re.search(r"低成本|无需囤货|开源|免费工具", text):
        score += 5
    if extras.get("download_links"):
        score += 4
    if extras.get("has_course_catalog"):
        score += 3
    if extras.get("member_gated_text"):
        score -= 6
    score -= min(25, len(hype_hits) * 5)
    score -= min(45, len(risk_hits) * 9)
    if re.search(r"会员|课程|教程|付费文章|加入会员", text):
        score -= 8
    score = max(0, min(100, score))

    if len(risk_hits) >= 2 or score < 35:
        level = "不建议"
    elif score >= 65:
        level = "可优先验证"
    elif score >= 45:
        level = "可小成本验证"
    else:
        level = "谨慎观察"

    reasons = []
    if positive_hits:
        reasons.append("有明确业务方向：" + "、".join(positive_hits[:5]))
    if concrete_hits:
        reasons.append("页面出现落地线索：" + "、".join(concrete_hits[:5]))
    if extras.get("download_links"):
        reasons.append("会员可见下载资源：" + "、".join(extras["download_links"][:2]))
    if extras.get("has_course_catalog"):
        reasons.append("已看到课程目录/大纲，可评估交付拆解")
    if hype_hits:
        reasons.append("夸大收益/零门槛信号：" + "、".join(hype_hits[:4]))
    if risk_hits:
        reasons.append("平台或合规风险词：" + "、".join(risk_hits[:5]))
    if re.search(r"会员|课程|教程|付费文章", text):
        reasons.append("主要是付费课程或会员内容，不能仅凭课程介绍验证收益")
    if extras.get("member_gated_text"):
        reasons.append("关键内容仍像会员门控，完整资料可能未完全展开")

    return {
        "score": score,
        "level": level,
        "reason": "；".join(reasons),
        "positive_hits": positive_hits,
        "concrete_hits": concrete_hits,
        "hype_hits": hype_hits,
        "risk_hits": risk_hits,
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"seenLinks": [], "lastRun": None, "lastNewCount": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data.get("seenLinks"), list):
            data["seenLinks"] = []
        return data
    except Exception:
        return {"seenLinks": [], "lastRun": None, "lastNewCount": 0}


def build_report(assessed, *, is_first_run: bool, new_count: int, feed_url: str, now: datetime, logged_in: bool, login_user: str) -> str:
    date = now.strftime("%Y-%m-%d")
    lines = [
        f"# 冒泡网创业项目日报（{date}）",
        "",
        f"检测时间：{now.strftime('%Y-%m-%d %H:%M:%S %z')}",
        f"来源：[{feed_url}]({feed_url})",
        f"会员登录：{'是（' + login_user + '）' if logged_in else '否（仅公开内容）'}",
        "",
        "> 说明：网站内容多为会员投稿、课程推广和转载。标题中的收益数字不作为事实；本日报只做线索筛选，最终要以平台规则、真实客户、实际订单和小额测试为准。会员资源链接仅用于本地分析，不要公开传播。",
        "",
    ]
    if is_first_run:
        lines.append("本次为首次检测：先建立当前 RSS 基线，并对最新内容做初筛。")
    elif new_count == 0:
        lines.append("今日 RSS 没有发现新文章；以下不重复展开项目，只保留检测记录。")
    lines.append("")

    if assessed:
        lines.extend([
            "## 今日筛选结果",
            "",
            "| 级别 | 分数 | 项目 | 日期 | 会员资源 | 主要判断 |",
            "|---|---:|---|---|---|---|",
        ])
        for row in assessed:
            reason = row["assessment"]["reason"].replace("|", "/")
            if len(reason) > 110:
                reason = reason[:110] + "…"
            title = row["item"]["title"].replace("|", "/")
            link = row["item"]["link"]
            pub = row["item"]["published"].strftime("%Y-%m-%d %H:%M")
            level = row["assessment"]["level"]
            score = row["assessment"]["score"]
            extras = row.get("extras") or {}
            res = "有下载" if extras.get("download_links") else ("目录可见" if extras.get("has_course_catalog") else "未见")
            lines.append(f"| {level} | {score} | [{title}]({link}) | {pub} | {res} | {reason} |")
        lines.append("")

        priority = [r for r in assessed if r["assessment"]["level"] == "可优先验证"][:3]
        if priority:
            lines.extend(["## 建议优先验证", ""])
            for row in priority:
                item = row["item"]
                a = row["assessment"]
                extras = row.get("extras") or {}
                lines.extend([
                    f"### {item['title']}",
                    f"- 评分：{a['score']}/100",
                    f"- 判断：{a['reason']}",
                    "- 7天验证：先选一个明确客户群，做一个最小可交付样品；联系10个潜在客户；记录回复、报价接受度、实际交付耗时和回款，不先买高价课程、不先投广告。",
                    f"- 原文：{item['link']}",
                ])
                if extras.get("download_links"):
                    lines.append("- 会员下载：")
                    for u in extras["download_links"][:5]:
                        lines.append(f"  - {u}")
                if extras.get("extract_codes"):
                    lines.append("- 提取码：" + "、".join(extras["extract_codes"][:5]))
                lines.append("")

        lines.extend([
            "## 明确不建议直接跟做",
            "",
            "- 以“挂机、挂G、外挂、破解、刷量、搬运、规避风控、不封号”等为核心卖点的项目：封号、侵权、资金和合规风险高。",
            "- 以“日入、躺赚、保底、当天变现、零成本”作为主要证据的项目：先要求可核验的成本、流量来源、订单记录和退款率，否则按营销文案处理。",
            "- 即使会员能看到网盘，也不代表项目可做；先验证客户和交付，再决定是否投入时间。",
        ])
    else:
        lines.extend([
            "## 当前状态",
            "",
            "本次没有新增 RSS 内容。下次检测到新文章后会自动抓取正文并评分。",
        ])

    lines.extend([
        "",
        "## 当前检测规则",
        "",
        "- 优先加分：AI/自动化、软件工具、企业服务、本地商家、真实客户、交付、报价、复购、会员可见目录/下载资源。",
        "- 扣分：夸大收益、零门槛、付费课程包装，以及搬运、挂机、刷量、规避风控、成人/灰产等高风险信号。",
        "- 评分只是筛选器，不代表项目一定赚钱；要通过小额、短周期、可停止的实验验证。",
        "",
    ])
    return "\n".join(lines)


def write_csv(path: Path, assessed) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "level", "score", "title", "published", "link", "category", "reason",
                "download_links", "extract_codes", "has_course_catalog",
            ],
        )
        writer.writeheader()
        for row in assessed:
            extras = row.get("extras") or {}
            writer.writerow({
                "level": row["assessment"]["level"],
                "score": row["assessment"]["score"],
                "title": row["item"]["title"],
                "published": row["item"]["published"].isoformat(),
                "link": row["item"]["link"],
                "category": row["item"]["category"],
                "reason": row["assessment"]["reason"],
                "download_links": " | ".join(extras.get("download_links") or []),
                "extract_codes": " | ".join(extras.get("extract_codes") or []),
                "has_course_catalog": extras.get("has_course_catalog"),
            })


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan maomp.vip feed for project clues")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--feed-url", default=FEED_URL)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--force-all", action="store_true")
    parser.add_argument("--no-login", action="store_true")
    parser.add_argument("--no-proxy", action="store_true", help="bypass system proxy (direct connection)")
    parser.add_argument("--credentials", default="")
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    report_dir = data_dir / "reports"
    state_path = data_dir / "state.json"
    latest_path = data_dir / "latest.md"
    data_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    cred_path = Path(args.credentials) if args.credentials else (data_dir / "credentials.json")
    client = MaompClient(data_dir, credentials_path=cred_path, no_proxy=args.no_proxy)
    logged_in = False
    if not args.no_login:
        logged_in = client.ensure_login()

    state = load_state(state_path)
    seen = list(state.get("seenLinks") or [])

    try:
        feed_xml = client.fetch(args.feed_url)
    except Exception as exc:
        print(f"ERROR: failed to fetch feed: {exc}", file=sys.stderr)
        return 1

    all_items = parse_feed(feed_xml)
    if len(seen) == 0:
        new_items = all_items[: args.limit]
        first_flag = True
    elif args.force_all:
        new_items = all_items[: args.limit]
        first_flag = False
    else:
        new_items = [x for x in all_items if x["link"] not in seen][: args.limit]
        first_flag = False

    assessed = []
    for item in new_items:
        body = ""
        extras = {
            "download_links": [],
            "extract_codes": [],
            "member_gated_text": False,
            "has_course_catalog": False,
            "body_len": 0,
        }
        try:
            page = client.fetch(item["link"], timeout=30)
            article_html = extract_article_html(page)
            body = strip_html(article_html)[:12000]
            extras = extract_member_extras(page, article_html)
        except Exception:
            pass
        assessment = assess(item["title"], item["description"], body, item["category"], extras)
        assessed.append({
            "item": item,
            "assessment": assessment,
            "extras": extras,
            "body_preview": body[:500],
        })

    assessed.sort(key=lambda x: x["assessment"]["score"], reverse=True)
    now = datetime.now().astimezone()
    report = build_report(
        assessed,
        is_first_run=first_flag and len(seen) == 0,
        new_count=len(new_items),
        feed_url=args.feed_url,
        now=now,
        logged_in=logged_in,
        login_user=client.login_user if logged_in else "",
    )

    date = now.strftime("%Y-%m-%d")
    write_text(report_dir / f"{date}.md", report)
    write_text(latest_path, report)
    write_csv(report_dir / f"{date}.csv", assessed)

    combined_seen = []
    for link in [x["link"] for x in all_items] + seen:
        if link not in combined_seen:
            combined_seen.append(link)
    combined_seen = combined_seen[:500]
    write_text(
        state_path,
        json.dumps(
            {
                "seenLinks": combined_seen,
                "lastRun": now.isoformat(),
                "lastNewCount": len(new_items),
                "source": args.feed_url,
                "loggedIn": logged_in,
                "loginUser": client.login_user if logged_in else "",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    if args.json_out:
        payload = {
            "generated_at": now.isoformat(),
            "logged_in": logged_in,
            "login_user": client.login_user if logged_in else "",
            "new_count": len(new_items),
            "priority_count": sum(1 for x in assessed if x["assessment"]["level"] == "可优先验证"),
            "items": [
                {
                    "title": x["item"]["title"],
                    "link": x["item"]["link"],
                    "published": x["item"]["published"].isoformat(),
                    "category": x["item"]["category"],
                    "score": x["assessment"]["score"],
                    "level": x["assessment"]["level"],
                    "reason": x["assessment"]["reason"],
                    "download_links": x.get("extras", {}).get("download_links", []),
                    "extract_codes": x.get("extras", {}).get("extract_codes", []),
                    "has_course_catalog": x.get("extras", {}).get("has_course_catalog", False),
                }
                for x in assessed
            ],
            "latest_md": str(latest_path),
        }
        write_text(Path(args.json_out), json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    priority = sum(1 for x in assessed if x["assessment"]["level"] == "可优先验证")
    print(
        f"完成：{latest_path}；新增 {len(new_items)} 条；优先验证 {priority} 条；会员登录={'是' if logged_in else '否'}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())