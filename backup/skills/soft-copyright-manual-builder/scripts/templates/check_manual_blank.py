from PIL import Image
import glob, os
d = r"C:\Temp\_mimo_man\pages"
BLOCK = 30
rows_out = []
for f in sorted(glob.glob(os.path.join(d, "*.png")), key=lambda x: int(''.join(filter(str.isdigit, os.path.basename(x))))):
    im = Image.open(f).convert("L")
    w, h = im.size
    px = im.load()
    # 去掉页边距区域（A4 20mm 边距 ≈ 8%）
    sx, ex = int(w*0.07), int(w*0.93)
    sy, ey = int(h*0.06), int(h*0.95)
    blank = total = 0
    last_content = sy
    for y0 in range(sy, ey - BLOCK, BLOCK):
        row_has = False
        for x0 in range(sx, ex - BLOCK, BLOCK):
            vals = [px[x0+dx, y0+dy] for dx in range(0, BLOCK, 6) for dy in range(0, BLOCK, 6)]
            total += 1
            if max(vals) - min(vals) < 8:
                blank += 1
            else:
                row_has = True
        if row_has:
            last_content = y0
    tail_gap = ey - last_content
    n = int(''.join(filter(str.isdigit, os.path.basename(f))))
    rows_out.append((n, blank/total*100 if total else 0, tail_gap/h*100))
bad = [r for r in rows_out if r[2] > 45]
print("页数:", len(rows_out))
print("尾部空白超 45% 的页:", [(r[0], round(r[2],1)) for r in bad] or "无")
print()
print("逐页（页码, 空白块占比%, 尾部空白%）:")
for n, b, t in rows_out:
    flag = "  <<<" if t > 45 else ""
    print(f"  p{n:02d}  {b:5.1f}  {t:5.1f}{flag}")
