import sys, os; os.chdir(os.environ.get('RAZBOR_WORK', '.')); sys.path.insert(0, '.'); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, subprocess
from PIL import Image
import fx
FF = fx.FF
def frame(n, t):
    b = subprocess.run([FF, '-v', 'error', '-ss', str(t), '-i', 'src/' + open('list.txt').read().split()[n-1], '-vf', 'scale=1080:1920', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True).stdout
    return np.frombuffer(b, np.uint8).reshape(1920, 1080, 3).copy()
def mask(n, t):
    b = subprocess.run([FF, '-v', 'error', '-ss', str(t), '-i', f'masks/{n:02d}.mp4', '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True).stdout
    m = Image.fromarray(np.frombuffer(b, np.uint8).reshape(640, 360)).resize((1080, 1920))
    return (np.asarray(m).astype(np.float32) / 255)[..., None]
from broll2 import *
def _main():
    tests = [('shot', [H + '/target_nov12/assets/rnp_total.png'], dict(crop=(0,0.04,1,1), hl=[(0.0, 0.38, 1, 0.47)]), 1.4),
             ('ads', [], dict(), 1.6), ('ads', [], dict(), 3.0), ('logo', [], dict(), 0.5),
             ('stat', [], dict(to=400, fmt='{:,.0f} ₸', small='жарнамаға'), 1.0),
             ('stack', MONT, dict(), 2.0)]
    outs = []
    fr0, m0 = frame(2, 20), mask(2, 20)
    for i, (k, s, kw, tt) in enumerate(tests):
        e = fx.FX(k, 0, 3.4, s, **kw); v = fr0.copy(); 
        if k == 'stack':
            for q in np.arange(0, tt, 1/30): e.draw(v.copy(), q, m0)
        e.draw(v, tt, m0); e.close()
        outs.append(Image.fromarray(v).resize((360, 640)))
    sheet = Image.new('RGB', (360 * len(outs), 640))
    for i, o in enumerate(outs): sheet.paste(o, (360 * i, 0))
    sheet.save('test/fx2.jpg'); print('ok')
if __name__ == "__main__": _main()
