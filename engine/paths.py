import os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/'
_local = os.path.expanduser('~/Downloads/groq_stt/bin/ffmpeg')
FF = _local if os.path.exists(_local) else (shutil.which('ffmpeg') or 'ffmpeg')
ASSETS = ROOT + 'assets/'
FONTS = ROOT + 'fonts/'
MODEL = ROOT + 'models/selfie_multiclass.tflite'
