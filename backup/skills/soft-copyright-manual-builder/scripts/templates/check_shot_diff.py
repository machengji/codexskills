from PIL import Image, ImageChops
import glob, os
d = r"{{SHOTS_DIR}}"
fs = sorted(glob.glob(os.path.join(d,"s*.jpg")))
def small(f):
    return Image.open(f).convert("L").resize((240,135))
prev = None
prevname = None
for f in fs:
    cur = small(f)
    if prev is not None:
        diff = ImageChops.difference(cur, prev)
        h = diff.histogram()
        tot = sum(h)
        changed = sum(h[10:])
        pct = changed/tot*100
        flag = "OK " if pct > 1.2 else "!! "
        print(f"{flag}{prevname} -> {os.path.basename(f):26s} 变化像素 {pct:5.2f}%")
    prev = cur
    prevname = os.path.basename(f)
