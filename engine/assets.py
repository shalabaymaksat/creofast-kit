#!/usr/bin/env python3
"""Өз активтеріңді дайындау + тізім: python3 engine/assets.py
 - өз активтер папкасындағы (<CREO_HOME>/assets/<санат>/) видеолардың қысқа, кішірейтілген көшірмесін assets/my/_c/ ішіне жасайды
   (B-roll тез оқылады; түпнұсқа өзгермейді). Қайта іске қосса — тек жаңаларын өңдейді.
 - Қай санатта неше файл барын және қай B-roll эффектілері қолжетімді екенін басады.
"""
import os, sys, glob, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import MY, FF
C = MY + '_c/'
LEN = dict(reels=8, cases=8, works=8, long=90)
SCALE = dict(reels='scale=-2:640', cases='scale=-2:640', works='scale=720:-2', long='scale=640:-2')
for cat in LEN:
    for p in sorted(glob.glob(MY + cat + '/*')):
        if not p.lower().endswith(('.mp4', '.mov', '.m4v')): continue
        out = C + cat + '/' + os.path.splitext(os.path.basename(p))[0] + '.mp4'
        if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(p): continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        r = subprocess.run([FF, '-v', 'error', '-y', '-i', p, '-t', str(LEN[cat]), '-an', '-vf', SCALE[cat] + ',fps=30',
                            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-pix_fmt', 'yuv420p', out])
        print(('ok  ' if r.returncode == 0 else 'ҚАТЕ ') + cat + '/' + os.path.basename(p))
import lib
h = lib.HAVE
print('\nАктивтер:', ', '.join(f'{k}={v}' for k, v in h.items()))
eff = ['logo() — Claude логотипі', 'stat(...) — сан/баға стикері', 'ADS — Ads Manager анимациясы']
if h['results']: eff.append('result(i, hl) — табыс/кабинет скрині')
if h['photos']: eff.append('photo(i) — пікір/хабарлама суреті')
if h['reels'] or h['cases']: eff += ['reel(i) — тік видео карточка', 'WALL_MY — видео торы']
if h['reels']: eff.append('ORB_MY — рилстер айналады')
if h['cases']: eff += ['ORB_ST — нәтижелер айналады', 'STK_ST — нәтижелер коллажы']
if h['works']: eff += ['work(i) — жатық видео карточка', 'STK — жұмыстар коллажы']
if lib.CUT: eff.append('CUT — ұзын видео таймлайнда қиылып рилстер шығады')
print('Қолжетімді B-roll:\n  ' + '\n  '.join(eff))
