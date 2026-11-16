# Адам маскасы (MediaPipe selfie multiclass): src видео -> masks/NN.mp4 (сұр, 360x640, бастапқы fps)
#   python3 mask.py N
import sys, subprocess, numpy as np, mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions
import sys as _s0, os as _o0; _s0.path.insert(0, _o0.path.dirname(_o0.path.abspath(__file__))); from paths import FF
n = int(sys.argv[1]); name = [l.strip() for l in open('list.txt')][n - 1]
W, H = 360, 640
seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
    base_options=BaseOptions(model_asset_path=__import__('paths').MODEL),
    running_mode=vision.RunningMode.VIDEO, output_confidence_masks=True))
rd = subprocess.Popen([FF, '-v', 'error', '-i', 'src/' + name, '-vf', f'fps=30,scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
wr = subprocess.Popen([FF, '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'gray', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                       '-c:v', 'libx264', '-crf', '12', '-pix_fmt', 'yuv420p', f'masks/{n:02d}.mp4'], stdin=subprocess.PIPE)
k = 0
while True:
    b = rd.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.frombuffer(b, np.uint8).reshape(H, W, 3).copy())
    r = seg.segment_for_video(img, int(k * 1000 / 30))
    bg = r.confidence_masks[0].numpy_view()          # 0-класс = фон
    m = np.clip((1 - bg) * 255, 0, 255).astype(np.uint8)
    wr.stdin.write(m.tobytes()); k += 1
wr.stdin.close(); wr.wait(); print(n, 'frames', k)
