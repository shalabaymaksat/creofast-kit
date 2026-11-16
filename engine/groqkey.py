import os
def load_api_key():
    k = os.environ.get('GROQ_API_KEY')
    if not k: raise SystemExit('GROQ_API_KEY орта айнымалысы жоқ (Claude Code environment settings-ке қос)')
    return k
