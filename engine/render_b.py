#!/usr/bin/env python3
"""creofast: hormozi-razbor render.py + fx.py B-roll (broll2.py спектері) + Instagram «сұрақ» стикері хугы.
  cd <жоба>; RAZBOR_WORK=$PWD RAZBOR_SRC=$PWD/src python3 ~/.claude/skills/creofast/scripts/render_b.py N [--test t ...]
B-roll сөз айтылған уақыт + 0,1 с-та толық экранға таза кесумен шығады, субтитр мен хук үстінде қалады.
"""
import sys, os, subprocess, inspect
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R
sys.path.insert(0, R.WD)                     # жобаның videos.py / broll2.py / cuts.py
try: from broll import BROLL, ASSETS        # ескі толық экран B-roll (міндетті емес)
except ImportError: BROLL, ASSETS = {}, {}

N = int(sys.argv[1])
FF, WD = R.FF, R.WD
BDIR = WD + 'broll/'; os.makedirs(BDIR, exist_ok=True)
FPSN = 30

# ---------- B-roll клиптерін дайындау (1080x1920, 30 fps) ----------
def make_clip(key, dur, out):
    a = ASSETS[key]; kind = a[0]
    if os.path.exists(out): return True
    cover = 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1'
    if kind == 'vid':
        src, ss = a[1], a[2]
        if not os.path.exists(src): return False
        if len(a) > 3 and a[3] == 'land':   # көлденең видео: қара фонда ортасында
            vf = 'scale=-2:1150,crop=1080:1150,pad=1080:1920:0:(oh-ih)/2+60:color=0x0d0d0d,setsar=1'
        else: vf = cover
        cmd = [FF, '-v', 'error', '-y', '-ss', str(ss), '-i', src, '-t', f'{dur:.3f}', '-vf', vf + f',fps={FPSN}', '-an']
    elif kind in ('img', 'imgs'):
        paths = [a[1]] if kind == 'img' else a[1]
        bg = Image.new('RGB', (1080, 1920), (13, 13, 13))
        ims = [Image.open(p).convert('RGB') for p in paths]
        gap, maxw = 40, 960
        ims = [im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS) for im in ims]
        tot = sum(im.height for im in ims) + gap * (len(ims) - 1)
        if tot > 1500:
            k = 1500 / tot; ims = [im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS) for im in ims]
            tot = sum(im.height for im in ims) + gap * (len(ims) - 1)
        y = (1920 - tot) // 2 + 60
        for im in ims:
            m = Image.new('L', im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=28, fill=255)
            bg.paste(im, ((1080 - im.width) // 2, y), m); y += im.height + gap
        png = out[:-4] + '.png'; bg.save(png)
        cmd = [FF, '-v', 'error', '-y', '-loop', '1', '-i', png, '-t', f'{dur:.3f}', '-vf', f'fps={FPSN}', '-an']
    elif kind == 'combo':
        sys.path.insert(0, WD); import combo
        combo.make_combo(out, dur, FF); return True
    elif kind == 'seq':
        # бірнеше активті ретпен: (кілт, үлесі)
        parts, tmp = a[1], []
        for j, (k2, frac) in enumerate(parts):
            o2 = out[:-4] + f'_p{j}.mp4'
            if not make_clip(k2, dur * frac, o2): return False
            tmp.append(o2)
        lst = out[:-4] + '.txt'; open(lst, 'w').write(''.join(f"file '{x}'\n" for x in tmp))
        cmd = [FF, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-an']
    elif kind == 'grid':
        paths, ss, cols, rows = a[1], a[2], a[3], a[4]
        paths = [p for p in paths if os.path.exists(p)][:cols * rows]
        if len(paths) < cols * rows: return False
        tw, th = 1080 // cols, 1920 // rows if rows > 1 else 1920
        if rows == 1: th = int(tw * 16 / 9)
        ins, fl = [], []
        for i, p in enumerate(paths):
            ins += ['-ss', str(ss), '-t', f'{dur:.3f}', '-i', p]
            fl.append(f'[{i}:v]scale={tw}:{th}:force_original_aspect_ratio=increase,crop={tw}:{th},setsar=1,fps={FPSN}[v{i}]')
        lay = '|'.join(f'{(i % cols) * tw}_{(i // cols) * th}' for i in range(len(paths)))
        fl.append(''.join(f'[v{i}]' for i in range(len(paths))) + f'xstack=inputs={len(paths)}:layout={lay}:fill=0x0d0d0d[g]')
        fl.append(f'[g]pad=1080:1920:0:(oh-ih)/2:color=0x0d0d0d[o]')
        cmd = [FF, '-v', 'error', '-y'] + ins + ['-filter_complex', ';'.join(fl), '-map', '[o]', '-t', f'{dur:.3f}', '-an']
    cmd += ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', out]
    subprocess.run(cmd, check=True)
    if os.path.getsize(out) < 20000: os.remove(out); return False
    return True

class Clip:
    def __init__(self, path): self.path, self.p, self.k, self.cur = path, None, -1, None
    def get(self, dt):
        want = int(dt * FPSN)
        if self.p is None or want < self.k:
            if self.p: self.p.kill()
            self.p = subprocess.Popen([FF, '-v', 'error', '-ss', f'{max(0, want) / FPSN:.3f}', '-i', self.path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                                      stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            self.k = want - 1
        fs = 1080 * 1920 * 3
        while self.k < want:
            b = self.p.stdout.read(fs)
            if len(b) < fs: break
            self.cur = np.frombuffer(b, np.uint8).reshape(1920, 1080, 3); self.k += 1
        return None if self.cur is None else self.cur.copy()

SCHED = []   # (t0, t1, Clip)
FXS = []     # (t0, t1, spec) — broll2 эффекттері
def plan_fx(pcs, toks, t, total, cfg):
    global FXS
    from broll2 import BROLL2
    po = [(R.src2out(pcs, a), R.src2out(pcs, b)) for a, b in cfg.get('play', [])]
    raw, i0 = [], 0
    for item in BROLL2[N]:
        if not item: continue
        pre, kind, dur, srcs, kw = item
        k = next((i for i in range(i0, len(toks)) if R.norm(toks[i]).startswith(R.norm(pre))), None)
        if k is None: print('  !! табылмады:', pre); continue
        i0 = k + 1; t0 = t[k] + 0.10
        if any(a <= t0 < b for a, b in po): continue
        if kind in ('shot', 'ads', 'stack') and t0 < R.HOOK_T + 0.05:   # кеудедегі хук қорабымен қабаттаспасын
            dur -= R.HOOK_T + 0.05 - t0; t0 = R.HOOK_T + 0.05
        raw.append([t0, dur, kind, srcs, kw, pre])
    FXS = []
    for j, (t0, dur, kind, srcs, kw, pre) in enumerate(raw):
        nx = next((r[0] for r in raw[j + 1:] if r[2] != 'logo'), total)   # логотип жоғарғы бұрышта — басқаны қимайды
        t1 = min(t0 + dur, total) if kind == 'logo' else min(t0 + dur, nx, total)
        FXS.append([t0, t1, (kind, srcs, kw), None])
        print(f'  fx    {t0:6.2f}-{t1:6.2f} {kind:6s} «{pre}»')

def plan_broll(pcs, toks, t, total, cfg):
    global SCHED
    import broll2
    if N in broll2.BROLL2: SCHED = []; return plan_fx(pcs, toks, t, total, cfg)
    po = [(R.src2out(pcs, a), R.src2out(pcs, b)) for a, b in cfg.get('play', [])]
    raw, i0 = [], 0
    for pre, key, dur in BROLL.get(N, []):
        k = next((i for i in range(i0, len(toks)) if R.norm(toks[i]).startswith(R.norm(pre))), None)
        if k is None: print('  !! табылмады:', pre); continue
        i0 = k + 1
        t0 = t[k] + 0.10
        if any(a <= t0 < b for a, b in po): print('  -- play ішінде:', pre); continue
        raw.append([t0, dur, key, pre])
    SCHED = []
    for j, (t0, dur, key, pre) in enumerate(raw):
        nx = next((r[0] for r in raw[j + 1:] if r[2] != 'logo'), total)   # логотип жоғарғы бұрышта — басқаны қимайды
        t1 = min(t0 + dur, total) if kind == 'logo' else min(t0 + dur, nx, total)
        t1 = min([t1] + [a for a, b in po if a > t0])
        if t1 - t0 < 0.6: print('  -- тым қысқа:', pre); continue
        out = BDIR + f'{N:02d}_{j}_{key}_{t1 - t0:.2f}.mp4'
        if not make_clip(key, t1 - t0 + 0.2, out): print('  !! актив жоқ:', key, '(', pre, ')'); continue
        SCHED.append((t0, t1, Clip(out)))
        print(f'  broll {t0:6.2f}-{t1:6.2f} {key:9s} «{pre}»')

# ---------- Instagram «сұрақ» стикері ----------
def ig_img(txt):
    q = txt.strip('“”"')
    W_, pad = 820, 44
    head = 'Задайте мне вопрос' if N == 16 else 'Маған сұрақ қойыңыз'
    fq = None
    for size in range(60, 38, -2):
        fq = R.font('ExtraBold', size); lines = R.wrap(q, fq, W_ - pad * 2)
        if len(lines) <= 3: break
    lh = int(size * 1.22); hh = 112
    body = lh * len(lines) + pad * 2 - (lh - size)
    Hh = hh + body; top = 90
    im = Image.new('RGBA', (W_ + 40, Hh + top + 40), (0, 0, 0, 0))
    sh = Image.new('L', im.size, 0); ImageDraw.Draw(sh).rounded_rectangle((20, top + 12, 20 + W_, top + Hh + 12), radius=40, fill=120)
    im.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(16)))
    card = Image.new('RGBA', (W_, Hh), (255, 255, 255, 255))
    gr = np.zeros((hh, W_, 3), np.uint8)
    c0, c1, c2 = np.array([131, 58, 180]), np.array([253, 29, 29]), np.array([252, 176, 69])
    for x in range(W_):
        u = x / (W_ - 1); c = c0 + (c1 - c0) * (u * 2) if u < .5 else c1 + (c2 - c1) * ((u - .5) * 2)
        gr[:, x] = c
    card.paste(Image.fromarray(gr), (0, 0))
    m = Image.new('L', card.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, W_ - 1, Hh - 1), radius=40, fill=255)
    d = ImageDraw.Draw(card)
    d.text((W_ / 2, hh / 2 + 22), head, font=R.font('Bold', 40), fill=(255, 255, 255), anchor='mm')
    for i, l in enumerate(lines):
        d.text((W_ / 2, hh + pad + i * lh), l, font=fq, fill=(17, 17, 17), anchor='ma')
    im.paste(card, (20, top), m)
    # аватар шеңбері (стикердің үстінде)
    av = 92; ax = 20 + W_ // 2 - av // 2; ay = top - av + 18
    d2 = ImageDraw.Draw(im)
    d2.ellipse((ax - 6, ay - 6, ax + av + 6, ay + av + 6), fill=(255, 255, 255))
    d2.ellipse((ax, ay, ax + av, ay + av), fill=(253, 29, 29))
    d2.text((ax + av / 2, ay + av / 2 + 2), '?', font=R.font('ExtraBold', 64), fill=(255, 255, 255), anchor='mm')
    arr = np.asarray(im).astype(np.float32)
    return arr[..., :3], arr[..., 3:] / 255

# ---------- патчтар ----------
CFG = R.VIDEOS[N]
try: from cuts import CUTS
except ImportError: CUTS = {}
CFG['cut'] = list(CFG.get('cut', [])) + CUTS.get(N, [])
_orig_hook = R.hook_img
R.hook_img = lambda txt: ig_img(txt) if CFG.get('ig') else _orig_hook(txt)

PCS = None
_orig_pieces = R.pieces_for
def pieces_for(n):
    global PCS
    pcs, total, fill = _orig_pieces(n); PCS = pcs
    return pcs, total, fill

_orig_wt = R.word_times
def word_times(n, cfg, pcs, total):
    """Ойнайтын видео алдындағы соңғы сөздер интерполяциямен play ішіне кетпесін: play басталар алдына қысу."""
    toks, brk, t = _orig_wt(n, cfg, pcs, total)
    for a, b in [(R.src2out(pcs, x), R.src2out(pcs, y)) for x, y in cfg.get('play', [])]:
        idx = [i for i, x in enumerate(t) if a - 0.05 <= x < b]
        for j, i in enumerate(idx):
            t[i] = max(t[i - 1] + 0.05 if i else 0, a - 0.06 - 0.15 * (len(idx) - 1 - j))
    return toks, brk, t

_orig_cards = R.make_cards
def make_cards(toks, brk, t, total, keys):
    plan_broll(PCS, toks, t, total, CFG)
    return _orig_cards(toks, brk, t, total, keys)

class MaskReader:
    def __init__(self, path):
        self.p = subprocess.Popen([FF, '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.k, self.cur = -1, None
    def get(self, ts):
        fs = 360 * 640
        while self.cur is None or (self.k + 0.5) / 30 < ts:
            b = self.p.stdout.read(fs)
            if len(b) < fs: break
            self.cur = np.frombuffer(b, np.uint8).reshape(640, 360); self.k += 1
        m = Image.fromarray(self.cur).resize((1080, 1920), Image.BILINEAR)
        return (np.asarray(m).astype(np.float32) / 255)[..., None]
MASK = None

DARK = {}
_orig_compose = R.compose
def compose(v, t, cards, cfg, hook):
    global MASK
    act = [x for x in FXS if x[0] <= t < x[1]]
    if act:
        import fx
        if MASK is None: MASK = MaskReader(WD + f'masks/{N:02d}.mp4')
        person = MASK.get(R.out2src(PCS, t))
        v = v.copy()
        for x in act:
            if x[3] in (None, 'done'): x[3] = fx.FX(x[2][0], x[0], x[1], x[2][1], **x[2][2])
            x[3].draw(v, t, person)
    for x in FXS:
        if x[3] not in (None, 'done') and t >= x[1]: x[3].close(); x[3] = 'done'
    b = next((x for x in SCHED if x[0] <= t < x[1]), None)
    if b is not None:
        fr = b[2].get(t - b[0])
        if fr is not None: v = fr
    c = next((c for c in cards if c[0] <= t < c[1]), None)
    if c is not None:
        key = (c[0], b is not None)
        if key not in DARK:
            reg = v[cfg['sub_y'] - 40:cfg['sub_y'] + 40, 160:920].astype(np.float32)
            DARK[key] = float((reg @ [0.299, 0.587, 0.114]).mean()) > 175
        cfg = dict(cfg, dark=DARK[key])
    return _orig_compose(v, t, cards, cfg, hook)

R.KEEP = {'Claude', '400К', 'Facebook', 'YouTube', 'Instagram', 'TikTok'}
exec(inspect.getsource(R.sub_img).replace("w.lower() if not", "w.lower() if w not in KEEP and not"), R.__dict__)

def out2src(pcs, t):
    """Түзетілген: кесінділер түйісіндегі float саңылауында видео соңына секірмей, келесі кесіндінің басын береді."""
    for s, e, o in pcs:
        if t < o + (e - s): return s + max(0.0, t - o)
    return pcs[-1][1]
R.out2src = out2src

# Аппараттық декодер (videotoolbox) қатар процестерде кадр қатырып тастады -> бағдарламалық декодер
_src_reader = inspect.getsource(R.Reader).replace("'-hwaccel', 'videotoolbox', ", "")
exec(_src_reader, R.__dict__)
R.compose, R.pieces_for, R.word_times, R.make_cards = compose, pieces_for, word_times, make_cards
R.VIDEOS[N]['keys'] = CFG['keys']

if __name__ == '__main__':
    R.main()
