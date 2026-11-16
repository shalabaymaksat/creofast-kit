"""Референс (instagram DewSc9dgI9g) стиліндегі B-roll эффекттері — спикер кадрда қалады, элементтер айналасында/артында.
  orbit — видео карточкалар адамды айналып ұшады (артқы жартысы адамның артынан өтеді, маска арқылы)
  wall  — артқы фон видео/креатив торына ауысады, плиткалар бірінен соң бірі толады (адам алдында)
  card  — скотчпен жапсырылған фото-карточка, ішінде клип ойнайды; бас жанында, жартылай артында
Блюрсыз, таза кесу; кіру — 0,2 с «поп».
"""
import os, subprocess, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import sys as _s0, os as _o0; _s0.path.insert(0, _o0.path.dirname(_o0.path.abspath(__file__))); from paths import FF
FPS = 30

class Tex:
    """Клипті берілген өлшемде (cover) ағынмен оқиды; сурет болса — тұрақты."""
    def __init__(self, src, w, h, ss=0.0):
        self.w, self.h, self.k, self.cur, self.p = w, h, -1, None, None
        if src.lower().endswith(('.jpg', '.jpeg', '.png')):
            im = Image.open(src).convert('RGB'); k = max(w / im.width, h / im.height)
            im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1), Image.LANCZOS)
            x, y = (im.width - w) // 2, (im.height - h) // 2
            self.cur = np.asarray(im.crop((x, y, x + w, y + h))); return
        self.p = subprocess.Popen([FF, '-v', 'error', '-ss', f'{ss:.2f}', '-i', src, '-vf',
                                   f'fps={FPS},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}',
                                   '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    def get(self, dt):
        if self.p is None: return self.cur
        want = int(dt * FPS); fs = self.w * self.h * 3
        while self.k < want:
            b = self.p.stdout.read(fs)
            if len(b) < fs: break
            self.cur = np.frombuffer(b, np.uint8).reshape(self.h, self.w, 3); self.k += 1
        return self.cur
    def close(self):
        if self.p: self.p.kill()

def framed(rgb, border=10, radius=22, tape=False, rot=0.0, shadow=True):
    """Ақ жиекті карточка + көлеңке (+ скотч). RGBA Image қайтарады."""
    h, w = rgb.shape[:2]
    W_, H_ = w + border * 2, h + border * 2
    card = Image.new('RGBA', (W_, H_), (255, 255, 255, 255))
    card.paste(Image.fromarray(rgb), (border, border))
    m = Image.new('L', (W_, H_), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, W_ - 1, H_ - 1), radius=radius, fill=255)
    card.putalpha(m)
    pad = 40
    out = Image.new('RGBA', (W_ + pad * 2, H_ + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new('L', out.size, 0); ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 10, pad + W_, pad + H_ + 10), radius=radius, fill=110)
        out.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(12)))
    out.alpha_composite(card, (pad, pad))
    if tape:
        t = Image.new('RGBA', (int(W_ * 0.38), 46), (240, 228, 190, 215))
        t = t.rotate(-4, expand=True)
        out.alpha_composite(t, (pad + W_ // 2 - t.width // 2, pad - 22))
    if rot: out = out.rotate(rot, resample=Image.BICUBIC, expand=True)
    return out

def paste(fr, im, cx, cy, sc=1.0):
    if sc <= 0.02: return
    if abs(sc - 1) > 1e-3: im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BILINEAR)
    a = np.asarray(im).astype(np.float32); rgb, al = a[..., :3], a[..., 3:] / 255
    h, w = al.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2)
    H, W = fr.shape[:2]
    xs0, ys0, xs1, ys1 = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xs1 <= xs0 or ys1 <= ys0: return
    sub = fr[ys0:ys1, xs0:xs1].astype(np.float32)
    rr, aa = rgb[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0], al[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0]
    fr[ys0:ys1, xs0:xs1] = (sub * (1 - aa) + rr * aa).astype(np.uint8)

def pop(u):  # 0..1 кіру уақыты -> масштаб (0,6 → 1,06 → 1)
    if u >= 1: return 1.0
    return 0.6 + 0.58 * (u / 0.75) if u < 0.75 else 1.18 - 0.18 * ((u - 0.75) / 0.25) - 0.0

class FX:
    """Бір эффект данасы. kind: orbit|wall|card. srcs: клип/сурет тізімі."""
    def __init__(self, kind, t0, t1, srcs, **kw):
        self.kind, self.t0, self.t1, self.kw = kind, t0, t1, kw
        if kind == 'orbit':
            self.tex = [Tex(s, 290, 516, kw.get('ss', 1.0)) for s in srcs]
        elif kind == 'wall':
            cols, rows = kw.get('cols', 6), kw.get('rows', 7)
            tw, th = 1080 // cols + 1, 1920 // rows + 1
            self.cols, self.rows, self.tw, self.th = cols, rows, tw, th
            self.tex = [Tex(s, tw - 8, th - 8, kw.get('ss', 1.0)) for s in srcs]
        elif kind == 'card':
            w, h = kw.get('size', (430, 560))
            self.tex = [Tex(srcs[0], w, h, kw.get('ss', 0.0))]
    def close(self):
        for t in self.tex: t.close()

    def draw(self, fr, t, person):
        """fr — спикер кадры (өзгереді), person — 0..1 маска (H,W,1)."""
        dt, u = t - self.t0, (t - self.t0) / 0.2
        sc0 = pop(min(1, u))
        if self.kind == 'card':
            im = framed(self.tex[0].get(dt), tape=True, rot=self.kw.get('rot', -4))
            cx, cy = self.kw.get('pos', (300, 640))
            back = fr.copy(); paste(back, im, cx, cy, sc0)
            if self.kw.get('behind', True):   # бастың артында: адамды қайта үстіне саламыз
                fr[:] = (back * (1 - person) + fr * person).astype(np.uint8)
            else: fr[:] = back
        elif self.kind == 'wall':
            bg = np.full_like(fr, 13)
            n = len(self.tex); k = min(self.cols * self.rows, int(dt / self.kw.get('step', 0.035)) + 1)
            order = self.kw.get('order')
            for i in range(k):
                j = order[i] if order else i
                r_, c_ = divmod(j, self.cols)
                tex = self.tex[j % n].get(dt)
                y, x = r_ * self.th + 4, c_ * self.tw + 4
                hh, ww = min(tex.shape[0], 1920 - y), min(tex.shape[1], 1080 - x)
                if hh > 0 and ww > 0: bg[y:y + hh, x:x + ww] = tex[:hh, :ww]
            fr[:] = (bg * (1 - person) + fr * person).astype(np.uint8)
        elif self.kind == 'orbit':
            cx, cy = self.kw.get('center', (540, 1420))
            R, ry = self.kw.get('R', 560), self.kw.get('ry', 150)
            n = len(self.tex); w0 = 2 * math.pi / self.kw.get('period', 5.0)
            items = []
            for i, tx in enumerate(self.tex):
                th_ = 2 * math.pi * i / n + w0 * dt + self.kw.get('phase', 0)
                z = math.sin(th_)
                x, y = cx + R * math.cos(th_), cy - ry * z * 0.6 + 40 * z
                items.append((z, x, y, tx))
            items.sort(key=lambda q: q[0])
            back = fr.copy(); front_layer = None
            for z, x, y, tx in items:
                im = framed(tx.get(dt), border=7, radius=18, shadow=True)
                s = sc0 * (0.62 + 0.28 * (1 - z) / 2 + (0.0 if z < 0 else 0.0))
                s = sc0 * (0.95 - 0.25 * (z + 1) / 2) if False else sc0 * (0.70 + 0.30 * (1 - (z + 1) / 2))
                if z > 0:   # артқы жарты — адамның артында
                    paste(back, im, x, y, s * 0.82)
            fr_b = (back * (1 - person) + fr * person).astype(np.uint8)
            for z, x, y, tx in items:
                if z <= 0:
                    im = framed(tx.get(dt), border=7, radius=18, shadow=True)
                    paste(fr_b, im, x, y, sc0 * (0.82 + 0.18 * (-z)))
            fr[:] = fr_b


# ====================== 2-кезең: жаңа эффекттер ======================
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import ImageFont
_MF = None
def F(w, s):
    import render as _R
    return _R.font(w, s)

def ease(u):  # 0..1 -> 0..1 (жұмсақ шығу)
    u = max(0.0, min(1.0, u)); return 1 - (1 - u) ** 3

def rgba_card(w, h, fill=(255, 255, 255, 255), radius=28):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=fill); return im

def shadowed(im, radius=28, pad=36, op=120):
    out = Image.new('RGBA', (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new('L', out.size, 0); ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 12, pad + im.width, pad + im.height + 12), radius=radius, fill=op)
    out.paste((0, 0, 0, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(14)))
    out.alpha_composite(im, (pad, pad)); return out

def claude_mark(size, col=(217, 119, 87)):
    """Claude белгісі — сәулелі «жұлдызша» (12 сәуле)."""
    S = size * 4; im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = S / 2
    for i in range(12):
        a = 2 * math.pi * i / 12 + 0.13 * (i % 3)
        L = S * (0.47 if i % 2 == 0 else 0.40); w = S * 0.055
        dx, dy = math.cos(a), math.sin(a); px, py = -dy, dx
        pts = [(c + px * w, c + py * w), (c + dx * L + px * w * 0.55, c + dy * L + py * w * 0.55),
               (c + dx * L - px * w * 0.55, c + dy * L - py * w * 0.55), (c - px * w, c - py * w)]
        d.polygon(pts, fill=col); d.ellipse((c + dx * L - w * 0.55, c + dy * L - w * 0.55, c + dx * L + w * 0.55, c + dy * L + w * 0.55), fill=col)
    d.ellipse((c - S * 0.09, c - S * 0.09, c + S * 0.09, c + S * 0.09), fill=col)
    return im.resize((size, size), Image.LANCZOS)

def logo_img():
    from paths import ASSETS as _A
    if os.path.exists(_A + 'claude_logo.png'): return Image.open(_A + 'claude_logo.png').convert('RGBA')
    W_, H_ = 430, 470
    card = rgba_card(W_, H_, (250, 247, 240, 255), 60)
    card.alpha_composite(claude_mark(280), ((W_ - 280) // 2, 40))
    d = ImageDraw.Draw(card)
    try: f = ImageFont.truetype('/System/Library/Fonts/Supplemental/Georgia.ttf', 92)
    except Exception: f = F('Bold', 84)
    d.text((W_ / 2, 400), 'Claude', font=f, fill=(31, 30, 29), anchor='mm')
    return shadowed(card, 60)

def stat_img(big, small, col=(17, 17, 17), acc=(227, 6, 19)):
    fb, fs = F('ExtraBold', 118), F('Bold', 44)
    d0 = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    wb = d0.textlength(big, font=fb); ws = d0.textlength(small, font=fs) if small else 0
    W_ = int(max(wb, ws) + 90); H_ = 175 + (62 if small else 0)
    card = rgba_card(W_, H_, (255, 255, 255, 255), 36); d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, 16, H_ - 1), radius=8, fill=acc)
    d.text((W_ / 2 + 6, 92), big, font=fb, fill=col, anchor='mm')
    if small: d.text((W_ / 2 + 6, 190), small, font=fs, fill=(110, 110, 110), anchor='mm')
    return shadowed(card, 36)

def _num_fmt(v, tmpl):
    # tmpl: '{:,.0f} ₸' сияқты; мыңдықты бос орынмен
    return tmpl.format(v).replace(',', ' ')

# ---- Ads Manager үлгісі (мок) ----
BLUE = (24, 119, 242)
def ads_img(tab, rows, k_on, prog, W_=980, H_=640):
    im = rgba_card(W_, H_, (255, 255, 255, 255), 26); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W_ - 1, 74), radius=26, fill=(245, 246, 248)); d.rectangle((0, 40, W_ - 1, 74), fill=(245, 246, 248))
    tabs = ['Кампании', 'Группы объявлений', 'Объявления']; x = 28; ft = F('Bold', 28)
    for i, tname in enumerate(tabs):
        w = d.textlength(tname, font=ft) + 36
        if i == tab:
            d.rounded_rectangle((x, 14, x + w, 62), radius=12, fill=(255, 255, 255), outline=BLUE, width=3)
            d.text((x + w / 2, 38), tname, font=ft, fill=BLUE, anchor='mm')
        else: d.text((x + w / 2, 38), tname, font=ft, fill=(90, 96, 104), anchor='mm')
        x += w + 12
    fh, fr = F('SemiBold', 22), F('SemiBold', 27)
    cols = [(40, 'Вкл.'), (150, 'Название'), (560, 'Статус'), (720, 'Бюджет'), (860, 'Лиды')]
    for cx, cname in cols: d.text((cx, 100), cname, font=fh, fill=(120, 124, 130))
    d.line((24, 134, W_ - 24, 134), fill=(228, 230, 234), width=2)
    for i, (name, bud) in enumerate(rows):
        y = 150 + i * 92; on = min(1.0, max(0.0, k_on - i))
        # тумблер
        tx, ty = 40, y + 14
        bg = tuple(int(200 + (b - 200) * on) for b in BLUE) if on else (205, 208, 213)
        d.rounded_rectangle((tx, ty, tx + 78, ty + 42), radius=21, fill=bg)
        kx = tx + 4 + 36 * ease(on); d.ellipse((kx, ty + 4, kx + 34, ty + 38), fill=(255, 255, 255))
        d.text((150, y + 35), name, font=fr, fill=(28, 30, 33), anchor='lm')
        if on >= 1:
            d.ellipse((560, y + 27, 576, y + 43), fill=(49, 162, 76)); d.text((586, y + 35), 'Активна', font=fr, fill=(49, 162, 76), anchor='lm')
            leads = int(prog * (37 - i * 7) * max(0, 1))
            d.text((860, y + 35), str(max(0, leads)), font=F('Bold', 30), fill=(28, 30, 33), anchor='lm')
        else: d.text((586, y + 35), 'Выкл.', font=fr, fill=(150, 150, 150), anchor='lm')
        d.text((720, y + 35), bud, font=fr, fill=(60, 64, 70), anchor='lm')
        d.line((24, y + 84, W_ - 24, y + 84), fill=(238, 239, 242), width=2)
    return shadowed(im, 26)

ADS_CAMP = [('Claude курс | Креатив 01', '₸3 000'), ('Claude курс | Креатив 02', '₸3 000'), ('Claude курс | Креатив 03', '₸3 000'),
            ('Claude курс | Креатив 04', '₸3 000'), ('Claude курс | Креатив 05', '₸3 000')]
ADS_SETS = [('KZ 18–45 | Reels', '₸1 500'), ('KZ 18–45 | Stories', '₸1 500'), ('Алматы | Интересы', '₸1 500'),
            ('Астана | Широкая', '₸1 500'), ('Look-alike 3%', '₸1 500')]

class FX2:
    """kind: shot | ads | logo | stat | stack"""
    def __init__(self, kind, t0, t1, srcs, **kw):
        self.kind, self.t0, self.t1, self.kw, self.tex = kind, t0, t1, kw, []
        if kind == 'shot':
            im = Image.open(srcs[0]).convert('RGB')
            if kw.get('crop'): x0, y0, x1, y1 = kw['crop']; im = im.crop((int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height)))
            W_ = kw.get('w', 960); k = W_ / im.width; im = im.resize((W_, int(im.height * k)), Image.LANCZOS)
            self.base = im; self.hl = kw.get('hl', [])
        elif kind == 'logo': self.img = logo_img()
        elif kind == 'stat': pass
        elif kind == 'stack':
            w, h = kw.get('size', (560, 315))
            self.tex = [Tex(s if isinstance(s, str) else s[0], w, h, kw.get('ss', 0.0) if isinstance(s, str) else s[1]) for s in srcs]
    def close(self):
        for t in self.tex: t.close()

    def draw(self, fr, t, person):
        dt = t - self.t0; sc0 = pop(min(1, dt / 0.2)); kw = self.kw
        behind = kw.get('behind', False)
        lay = fr.copy()
        if self.kind == 'shot':
            im = self.base.copy().convert('RGBA'); ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
            for j, (x0, y0, x1, y1) in enumerate(self.hl):
                u = ease((dt - kw.get('hl_t', 0.45) - j * 0.5) / 0.3)
                if u <= 0: continue
                X0, Y0, X1, Y1 = x0 * im.width, y0 * im.height, x1 * im.width, y1 * im.height
                d.rectangle((X0, Y0, X0 + (X1 - X0) * u, Y1), fill=(255, 214, 0, 95))
                if u >= 1: d.rounded_rectangle((X0 - 6, Y0 - 4, X1 + 6, Y1 + 4), radius=10, outline=(227, 6, 19, 255), width=6)
            im = Image.alpha_composite(im, ov)
            c2 = rgba_card(im.width + 20, im.height + 20, (255, 255, 255, 255), 24); c2.paste(im, (10, 10))
            m = Image.new('L', c2.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, c2.width - 1, c2.height - 1), radius=24, fill=255); c2.putalpha(m)
            out = shadowed(c2, 24)
            if kw.get('rot'): out = out.rotate(kw['rot'], resample=Image.BICUBIC, expand=True)
            paste(lay, out, *kw.get('pos', (540, 1520)), sc0)
        elif self.kind == 'ads':
            dur = self.t1 - self.t0; half = dur * kw.get('split', 0.5)
            tab, tt = (0, dt) if dt < half else (1, dt - half)
            rows = ADS_CAMP if tab == 0 else ADS_SETS
            st = kw.get('step', 0.22)
            k_on = max(0.0, (tt - 0.2) / st); prog = max(0.0, tt - 0.2 - st * len(rows)) / 1.0
            paste(lay, ads_img(tab, rows, k_on, min(1.0, prog)), *kw.get('pos', (540, 1520)), sc0 if tab == 0 else 1.0)
        elif self.kind == 'logo':
            im = self.img.rotate(kw.get('rot', -6), resample=Image.BICUBIC, expand=True)
            paste(lay, im, *kw.get('pos', (250, 640)), sc0 * kw.get('scale', 0.8)); behind = kw.get('behind', True)
        elif self.kind == 'stat':
            u = ease((dt - 0.05) / kw.get('count', 0.7))
            big = _num_fmt(kw['to'] * u, kw.get('fmt', '{:,.0f}')) if 'to' in kw else kw['big']
            im = stat_img(big, kw.get('small', ''), acc=kw.get('acc', (227, 6, 19)))
            im = im.rotate(kw.get('rot', 4), resample=Image.BICUBIC, expand=True)
            cx, cy = kw.get('pos', (780, 640)); cx = min(max(cx, im.width / 2 - 20), 1080 - im.width / 2 + 20)
            paste(lay, im, cx, cy, sc0)
        elif self.kind == 'stack':
            P = kw.get('ps', [(300, 1360, -6), (790, 1440, 5), (330, 1700, 4), (770, 1760, -4), (540, 1560, -2)])
            for i, tx in enumerate(self.tex):
                ti = dt - i * kw.get('step', 0.35)
                if ti < 0: break
                x, y, r = P[i % len(P)]
                im = framed(tx.get(dt), border=8, radius=16, tape=(i % 2 == 0), rot=r)
                paste(lay, im, x, y, pop(min(1, ti / 0.2)))
        if behind: fr[:] = (lay * (1 - person) + fr * person).astype(np.uint8)
        else: fr[:] = lay

_FX1 = FX
def FX(kind, t0, t1, srcs, **kw):
    if kind in ('shot', 'ads', 'logo', 'stat', 'stack'): return FX2(kind, t0, t1, srcs, **kw)
    return _FX1(kind, t0, t1, srcs, **kw)

# ── reelcut: ұзын видео таймлайнда қиылып → рилстер шығады  ──
class FXCut:
    def __init__(self, t0, t1, srcs, **kw):
        self.t0, self.t1, self.kw = t0, t1, kw
        long_src, reels = srcs[0], srcs[1:]
        ss = kw.get('ss', 300.0)
        self.player = Tex(long_src, 600, 338, ss)
        n = 12; self.thumbs = []
        if kw.get('thumbs'):
            self.thumbs = [Image.open(p).convert('RGB').resize((80, 45)) for p in kw['thumbs']]; n = 0
        for i in range(n):
            b = subprocess.run([FF, '-v', 'error', '-ss', f'{ss + i * 90:.1f}', '-i', long_src, '-vf', 'scale=80:45',
                                '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
            self.thumbs.append(Image.fromarray(np.frombuffer(b, np.uint8).reshape(45, 80, 3)) if len(b) == 80 * 45 * 3 else Image.new('RGB', (80, 45), (40, 40, 40)))
        self.reels = [Tex(r, 216, 384, kw.get('rss', 3.0)) for r in reels[:4]]
        self.segs = [(0.06, 0.20), (0.30, 0.43), (0.55, 0.68), (0.80, 0.93)]
        self.cols = [(255, 196, 0), (0, 200, 140), (60, 150, 255), (255, 80, 120)]
        self.tex = [self.player] + self.reels
    def close(self):
        for t in self.tex: t.close()
    def draw(self, fr, t, person):
        dt = t - self.t0; dur = self.t1 - self.t0; kw = self.kw
        cut_t = kw.get('cut_t', 0.45); split = kw.get('split', 1.7)
        PW, PH = 1000, 720; X0, Y0 = 40, kw.get('y', 1170)
        ov = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        d.rounded_rectangle((0, 0, PW - 1, PH - 1), radius=28, fill=(22, 24, 30, 240))
        # таймлайн
        TX, TY, TW, TH = 20, PH - 120, PW - 40, 70
        d.rounded_rectangle((TX - 6, TY - 30, TX + TW + 6, TY + TH + 14), radius=12, fill=(34, 36, 44, 255))
        for i, th in enumerate(self.thumbs):
            w_ = TW / len(self.thumbs); im = th.resize((int(w_) + 1, TH))
            ov.paste(im, (int(TX + i * w_), TY))
        for i in range(0, 41):
            x = TX + TW * i / 40; d.line((x, TY - 26, x, TY - (14 if i % 5 else 6)), fill=(150, 150, 160, 255), width=2)
        f_s = F('Bold', 24)
        d.text((TX, TY - 62), self.kw.get('label', 'podcast_FULL.mp4  ·  42:17'), font=f_s, fill=(200, 200, 210, 255))
        # кесу белгілері + түсті кесектер
        for j, (a, b) in enumerate(self.segs):
            u = ease((dt - cut_t - j * 0.28) / 0.25)
            if u <= 0: continue
            xa, xb = TX + TW * a, TX + TW * b
            hl = Image.new('RGBA', (int(xb - xa), TH), self.cols[j] + (int(110 * u),)); ov.alpha_composite(hl, (int(xa), TY))
            d.rectangle((xa, TY - 4, xb, TY + TH + 4), outline=self.cols[j] + (255,), width=5)
            for x in (xa, xb): d.line((x, TY - 30, x, TY + TH + 10), fill=(255, 40, 40, 255), width=4)
            d.text((xa + 6, TY + TH - 30), f'#{j + 1}', font=F('Bold', 22), fill=(255, 255, 255, 255))
        # ойнатқыш немесе рилстер
        ph = dt / max(0.1, dur) ; px = TX + TW * min(1, dt / split * 0.95) if dt < split else None
        if dt < split:
            pl = Image.fromarray(self.player.get(dt)).convert('RGBA')
            ov.alpha_composite(pl, ((PW - 600) // 2, 40))
            d.rounded_rectangle(((PW - 600) // 2, 40, (PW + 600) // 2, 378), radius=10, outline=(70, 70, 80, 255), width=3)
            d.line((px, TY - 34, px, TY + TH + 12), fill=(255, 255, 255, 255), width=4)
        else:
            ft = dt - split
            for j, rt in enumerate(self.reels):
                u = ease((ft - j * 0.18) / 0.35)
                if u <= 0: continue
                a, b = self.segs[j]; sx = TX + TW * (a + b) / 2
                cx = 60 + 125 + j * 250 - 63; cx = PW * (j + 0.5) / 4
                cy = 40 + 220
                x = sx + (cx - sx) * u; y = TY + (cy - TY) * u
                d.line((sx, TY - 6, x, y + 160 * u), fill=self.cols[j] + (200,), width=4)
                im = Image.fromarray(rt.get(ft)).convert('RGBA'); s = 0.35 + 0.65 * u
                im = im.resize((max(1, int(216 * s)), max(1, int(384 * s))))
                card = Image.new('RGBA', (im.width + 10, im.height + 10), self.cols[j] + (255,)); card.paste(im, (5, 5))
                ov.alpha_composite(card, (int(x - card.width / 2), int(y - card.height / 2 + 30)))
                if u >= 1: d.text((x - 40, y + 230), f'Reels #{j + 1}', font=F('Bold', 22), fill=(255, 255, 255, 255))
        sc0 = pop(min(1, dt / 0.2))
        paste(fr, ov, X0 + PW / 2, Y0 + PH / 2, sc0)

_FX2W = FX
def FX(kind, t0, t1, srcs, **kw):
    if kind == 'reelcut': return FXCut(t0, t1, srcs, **kw)
    return _FX2W(kind, t0, t1, srcs, **kw)
