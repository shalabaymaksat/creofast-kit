import sys, subprocess, numpy as np
import sys as _s0, os as _o0; _s0.path.insert(0, _o0.path.dirname(_o0.path.abspath(__file__))); from paths import FF
f=sys.argv[1]
raw=subprocess.run([FF,'-v','error','-i',f,'-vf','scale=90:160,format=gray','-f','rawvideo','-'],capture_output=True).stdout
a=np.frombuffer(raw,np.uint8).reshape(-1,160,90).astype(np.int16)
d=np.abs(np.diff(a,axis=0)).mean((1,2))
run=0; out=[]
for i,x in enumerate(d):
    if x<0.25: run+=1
    else:
        if run>=15: out.append((round((i-run)/30,2),round(run/30,2)))
        run=0
if run>=15: out.append((round((len(d)-run)/30,2),round(run/30,2)))
print(f.split('/')[-1], out)
