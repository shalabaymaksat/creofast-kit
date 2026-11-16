# creofast B-roll кітапханасы. Активтер — пайдаланушының өз файлдары: assets/my/<санат>/
#   results/  — табыс/кабинет/аналитика скриншоттары (png/jpg)
#   photos/   — пікір, клиент хабарламасы, сертификат т.б. суреттер
#   reels/    — өз рилстерің (тік видео)
#   cases/    — клиент/оқушы нәтижелері (тік видео)
#   works/    — мықты жұмыстарың, портфолио (жатық видео)
#   long/     — бір ұзын видео (подкаст/эфир) — «ұзын видеоны қиып рилс» эффекті үшін (reels/ де керек)
# Жобаның broll2.py: `from lib import *` → BROLL2 = {N: [E('сөз', ұзақтығы, спек), ...]}
# Санат бос болса, сол спек None болады да, E(...) эффектісі өздігінен түсіп қалады.
import os, glob
from paths import ASSETS as A
MY = A + 'my/'
_C = MY + '_c/'      # assets.py жасайтын қысқа/кішірейтілген көшірмелер (git-ке кірмейді)
VID, IMG = ('.mp4', '.mov', '.m4v'), ('.png', '.jpg', '.jpeg', '.webp')

def files(cat, ext):
    out = []
    for p in sorted(glob.glob(MY + cat + '/*')):
        if not p.lower().endswith(ext): continue
        c = _C + cat + '/' + os.path.splitext(os.path.basename(p))[0] + '.mp4'
        out.append(c if ext is VID and os.path.exists(c) else p)
    return out

RESULTS, PHOTOS = files('results', IMG), files('photos', IMG)
REELS, CASES, WORKS, LONG = files('reels', VID), files('cases', VID), files('works', VID), files('long', VID)
HAVE = dict(results=len(RESULTS), photos=len(PHOTOS), reels=len(REELS), cases=len(CASES), works=len(WORKS), long=len(LONG))

L, R = (360, 600), (720, 600)
LAND = dict(size=(720, 450))
LOGO_L, LOGO_R = dict(pos=(250, 640), rot=-6), dict(pos=(830, 640), rot=6)
ST_R, ST_L = dict(pos=(790, 650), rot=4), dict(pos=(290, 650), rot=-4)
CHEST = (540, 1560)                               # бет төмен тұрса стикер/скрин осында
VERT = dict(size=(300, 533), ps=[(250, 1450, -6), (540, 1520, 3), (830, 1450, 6), (390, 1600, -3), (690, 1600, 4)])

def _at(lst, i): return lst[i % len(lst)] if lst else None

# ── активсіз жұмыс істейтіндер ──
def logo(side='L'): return ('logo', [], LOGO_L if side == 'L' else LOGO_R)        # Claude логотипі
def stat(big, small, side='R', pos=None):                                             # сан/баға стикері
    d = dict(ST_R if side == 'R' else ST_L, big=big, small=small)
    if pos: d.update(pos=pos, rot=-3)
    return ('stat', [], d)
ADS = ('ads', [], dict(pos=(540, 1560), split=0.45))                                  # Ads Manager тумблер анимациясы

# ── өз активтерің ──
def result(i=0, hl=None, crop=None):
    """results/ скриншоты кеудеде. hl=[(x0,y0,x1,y1)] — белгілейтін аймақ (0..1 үлесімен)."""
    p = _at(RESULTS, i)
    return p and ('shot', [p], dict(crop=crop, pos=(540, 1600), w=960, hl=hl or []))
def photo(i=0, w=980):
    p = _at(PHOTOS, i)
    return p and ('shot', [p], dict(crop=None, w=w, pos=CHEST, hl=[]))
def reel(i=0, side='R'):
    p = _at(REELS + CASES, i)
    return p and ('card', [p], dict(pos=R if side == 'R' else L, size=(360, 640), ss=0.0, rot=4 if side == 'R' else -4))
def work(i=0, side='R'):
    p = _at(WORKS, i)
    return p and ('card', [p], dict(LAND, pos=R if side == 'R' else L, ss=0.0, rot=3 if side == 'R' else -3))

ORB_MY = REELS and ('orbit', REELS[:7], dict(ss=0.0))                                 # өз рилстерің айналады
ORB_ST = CASES and ('orbit', CASES[:7], dict(ss=0.0, center=(540, 1680)))             # клиент нәтижелері айналады
WALL_MY = (REELS + CASES) and ('wall', ((REELS + CASES) * 42)[:42], dict(ss=0.0))     # видео торы (фон)
STK = WORKS and ('stack', [(p, 0.0) for p in WORKS[:5]], dict(step=0.3))              # жұмыстар коллажы
STK_ST = CASES and ('stack', [(p, 0.0) for p in CASES[:5]], dict(VERT, ss=0.0))       # нәтижелер коллажы
CUT = (LONG and len(REELS) >= 2) and ('reelcut', [LONG[0]] + REELS[:4], dict(ss=0.0, rss=0.0))   # ұзын видео → рилстер

def E(w, d, spec):  # (сөз, ұзақтығы, (kind, srcs, kw)); спек жоқ болса — None (эффект түседі)
    if not spec: return None
    k, s, kw = spec; return (w, k, d, s, kw)

BROLL2 = {}
