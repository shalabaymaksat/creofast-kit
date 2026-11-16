"""«36 креатив» құралу анимациясы: HOOK × BODY × CTA клиптері → 36 креатив торы.
  make_combo(out_mp4, dur, ff)  — 1080x1920, 30 fps. Блюрсыз, таза кесу; элементтер «поп» болып шығады.
"""
import glob, os, subprocess
import numpy as np
from PIL import Image, ImageDraw
import render as R

TH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'broll', 'thumbs')
BG, INK, RED, YEL, WHITE = (13, 13, 13), (17, 17, 17), (227, 6, 19), (255, 214, 0), (255, 255, 255)
FPS = 30

def rounded(im, r):
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=r, fill=255)
    return m

def tile(path, w, h):
    im = Image.open(path).convert('RGB')
    k = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))

def make_combo(out, dur, ff):
    hooks = sorted(glob.glob(TH + '/hook_*.jpg')); bodies = sorted(glob.glob(TH + '/body_*.jpg'))
    ctas = sorted(glob.glob(TH + '/cta_*.jpg')); c36 = sorted(glob.glob(TH + '/c36_*.jpg'))
    tw, th = 101, 180
    rows = [('HOOK', hooks, RED), ('BODY', bodies, (40, 120, 255)), ('CTA', ctas, (0, 170, 110))]
    tiles = {p: tile(p, tw, th) for _, ps, _ in rows for p in ps}
    gw, gh = 100, 178   # 9x4 тор
    gt = [tile(p, gw, gh) for p in c36[:36]]
    fL, fT, fN = R.font('ExtraBold', 54), R.font('ExtraBold', 64), R.font('ExtraBold', 150)
    n = int(dur * FPS)
    p = subprocess.Popen([ff, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    split = 0.42 * dur          # 1-бөлім: 3 қатар клип; 2-бөлім: 36 тор
    for fi in range(n):
        t = fi / FPS
        im = Image.new('RGB', (1080, 1920), BG); d = ImageDraw.Draw(im)
        if t < split:
            d.text((540, 480), 'HOOK × BODY × CTA', font=fT, fill=WHITE, anchor='mm')
            y0 = 560
            for ri, (lab, ps, col) in enumerate(rows):
                tr = ri * split / 4          # қатарлар ретпен шығады
                if t < tr: continue
                y = y0 + ri * (th + 100)
                d.rounded_rectangle((70, y, 70 + 230, y + 70), radius=16, fill=col)
                d.text((185, y + 35), lab, font=fL, fill=WHITE, anchor='mm')
                x = 70
                for j, pth in enumerate(ps):
                    if t < tr + j * 0.08: break
                    xx = 70 + j * (tw + 24); yy = y + 88
                    im.paste(tiles[pth], (xx, yy), rounded(tiles[pth], 18))
                d.text((1010, y + 88 + th // 2), f'×{len(ps)}' if ri else f'{len(ps)}', font=fL, fill=WHITE, anchor='rm')
        else:
            u = (t - split) / (dur - split)
            k = min(36, int(u / 0.6 * 36) + 1)       # 60% уақытта 36 плитка толады
            ox, oy = (1080 - 9 * gw - 8 * 8) // 2, 520
            for i in range(k):
                r_, c_ = divmod(i, 9)
                im.paste(gt[i], (ox + c_ * (gw + 8), oy + r_ * (gh + 8)), rounded(gt[i], 12))
            num = 4 * 3 * 3 if k == 36 else k
            d.text((540, oy + 4 * (gh + 8) + 80), f'{num} КРЕАТИВ', font=fT, fill=YEL if k == 36 else WHITE, anchor='mm')
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()
