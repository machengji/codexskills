#!/usr/bin/env python3
"""校验垂直系统项目的中国境内真实案例图台账与运行引用。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
FOREIGN_HINTS = {
    "karachi", "pakistan", "hyderabad", "india", "bangkok", "thailand",
    "tokyo", "japan", "seoul", "korea", "london", "paris", "berlin",
    "new-york", "new_york", "usa", "america", "singapore", "malaysia",
    "vietnam", "indonesia", "菲律宾", "日本", "韩国", "美国", "英国",
    "法国", "德国", "泰国", "印度", "巴基斯坦", "新加坡", "马来西亚",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="校验中国境内真实案例图门禁")
    parser.add_argument("project_root", type=Path, help="待校验项目根目录")
    parser.add_argument(
        "--allow-foreign",
        action="store_true",
        help="仅当用户明确要求外国场景且设计说明已记录时使用",
    )
    return parser.parse_args()


def load_manifest(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("cases", "items", "images"):
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError("manifest.json 必须是数组，或包含 cases/items/images 数组")


def entry_file(entry: dict) -> str:
    value = entry.get("file") or entry.get("localPath") or entry.get("local_path")
    return str(value or "").replace("\\", "/")


def find_runtime_refs(src_root: Path) -> set[str]:
    refs: set[str] = set()
    if not src_root.exists():
        return refs
    pattern = re.compile(r"/cases/([^\"'?)]+\.(?:jpg|jpeg|png|webp|avif))", re.I)
    for path in src_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".vue", ".ts", ".tsx", ".js", ".jsx", ".css", ".scss", ".html"}:
            continue
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        refs.update(match.group(1).replace("\\", "/") for match in pattern.finditer(text))
    return refs


def main() -> int:
    args = parse_args()
    root = args.project_root.resolve()
    cases_dir = root / "public" / "cases"
    manifest_path = cases_dir / "manifest.json"
    errors: list[str] = []

    if not manifest_path.exists():
        errors.append("缺少 public/cases/manifest.json")
        entries: list[dict] = []
    else:
        try:
            entries = load_manifest(manifest_path)
        except Exception as exc:
            errors.append(f"台账无法读取：{exc}")
            entries = []

    if len(entries) < 6:
        errors.append(f"真实案例图台账不足 6 条：当前 {len(entries)} 条")

    manifest_files: set[str] = set()
    for index, entry in enumerate(entries, start=1):
        file_name = entry_file(entry)
        location = str(entry.get("location") or "")
        country = str(entry.get("country") or "")
        source = str(entry.get("sourcePage") or entry.get("source") or entry.get("url") or "")
        license_name = str(entry.get("license") or entry.get("许可") or "")
        role = str(entry.get("role") or entry.get("业务角色") or "")
        evidence = str(entry.get("locationEvidence") or entry.get("location_evidence") or entry.get("地点依据") or source)

        if not file_name:
            errors.append(f"第 {index} 条缺少 file/localPath")
            continue
        normalized = file_name.removeprefix("public/cases/").removeprefix("/cases/")
        manifest_files.add(normalized)
        local_file = cases_dir / normalized
        if not local_file.exists():
            errors.append(f"台账文件不存在：{normalized}")
        if local_file.suffix.lower() not in IMAGE_SUFFIXES:
            errors.append(f"台账不是支持的图片格式：{normalized}")

        if not args.allow_foreign:
            if "中国" not in country and "中国" not in location:
                errors.append(f"第 {index} 条未证明为中国境内场景：{normalized}")
            combined = f"{normalized} {country} {location}".lower()
            hit = sorted(word for word in FOREIGN_HINTS if word in combined)
            if hit:
                errors.append(f"第 {index} 条疑似外国场景关键词 {hit}：{normalized}")
        if not location:
            errors.append(f"第 {index} 条缺少具体中国地点：{normalized}")
        if not evidence:
            errors.append(f"第 {index} 条缺少地点依据：{normalized}")
        if not source:
            errors.append(f"第 {index} 条缺少来源页面：{normalized}")
        if not license_name:
            errors.append(f"第 {index} 条缺少许可说明：{normalized}")
        if not role:
            errors.append(f"第 {index} 条缺少业务角色：{normalized}")

    runtime_refs = find_runtime_refs(root / "src")
    missing_ledger = sorted(ref for ref in runtime_refs if ref not in manifest_files)
    if missing_ledger:
        errors.append("运行引用未登记台账：" + "、".join(missing_ledger))

    all_case_images = {
        str(path.relative_to(cases_dir)).replace("\\", "/")
        for path in cases_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    }
    if not args.allow_foreign:
        suspicious = sorted(
            name for name in all_case_images
            if any(word in name.lower() for word in FOREIGN_HINTS)
        )
        if suspicious:
            errors.append("案例目录仍保留疑似外国图片：" + "、".join(suspicious))

    result = {
        "项目": str(root),
        "台账数量": len(entries),
        "运行引用数量": len(runtime_refs),
        "中国境内门禁": "显式豁免" if args.allow_foreign else "强制启用",
        "结论": "不通过" if errors else "通过",
        "缺口": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
