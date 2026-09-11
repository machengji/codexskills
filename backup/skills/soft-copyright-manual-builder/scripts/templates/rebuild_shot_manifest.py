import re, json, os, glob

wd = r"{{WORKDIR}}"
out = r"{{SHOTS_DIR}}"

pat = re.compile(
    r'shot\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*"([^"]+)"\s*(?:,\s*(true|false)\s*)?\)',
    re.S,
)

rows = {}
for f in ("dam_capture2.mjs", "dam_capture3.mjs"):
    p = os.path.join(wd, f)
    if not os.path.exists(p):
        continue
    src = open(p, encoding="utf-8").read()
    for m in pat.finditer(src):
        sid = m.group(1)
        rows[sid] = {
            "id": sid,
            "group": m.group(2),
            "action": m.group(3),
            "beforeState": m.group(4),
            "afterState": m.group(5),
            "visibleChanges": m.group(6),
            "popup": m.group(7) == "true",
        }

ordered = [rows[k] for k in sorted(rows.keys())]
files = sorted(glob.glob(os.path.join(out, "s*.jpg")))
have = {os.path.basename(f).replace(".jpg", "") for f in files}
missing = [r["id"] for r in ordered if r["id"] not in have]
extra = [f for f in have if f not in rows]

print("metadata entries:", len(ordered))
print("image files:", len(files))
print("missing images for metadata:", missing or "none")
print("images without metadata:", sorted(extra) or "none")

with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as fh:
    json.dump(ordered, fh, ensure_ascii=False, indent=2)
print("manifest rewritten")
