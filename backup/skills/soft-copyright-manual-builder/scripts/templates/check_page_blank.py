from PIL import Image
import glob, os
d = r"{{WORKDIR}}\dam_shots"
BLOCK = 40
for f in sorted(glob.glob(os.path.join(d,"audit-*.png"))):
    im = Image.open(f).convert("L")
    w,h = im.size
    sy, ey = 124, 1052
    sx, ex = 100, w-30
    px = im.load()
    blank_blocks = 0
    total_blocks = 0
    worst_row = None
    for y0 in range(sy, ey-BLOCK, BLOCK):
        row_blank = 0
        row_total = 0
        for x0 in range(sx, ex-BLOCK, BLOCK):
            vals = [px[x0+dx, y0+dy] for dx in range(0,BLOCK,8) for dy in range(0,BLOCK,8)]
            total_blocks += 1
            row_total += 1
            if max(vals)-min(vals) < 6:
                blank_blocks += 1
                row_blank += 1
        if row_blank == row_total and worst_row is None:
            worst_row = y0
    print(f"{os.path.basename(f):26s} 空白块={blank_blocks:4d}/{total_blocks:4d} = {blank_blocks/total_blocks*100:5.1f}%  首个全空行y={worst_row}")
