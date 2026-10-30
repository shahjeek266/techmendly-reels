import json, os, wave, subprocess, numpy as np, soundfile as sf, re, html
SR=48000
OUT="/tmp/hf/reel37"; os.makedirs(OUT+"/assets",exist_ok=True)
scenes=[
 "Is your AI making things up? Ask it the same question twice.",
 "Open two fresh chats, and ask both the exact same question.",
 "Now compare the facts. Watch the names, dates and numbers.",
 "If they disagree, the AI may be guessing. Don't trust that answer.",
 "If they match, that's a good sign. But it's not proof.",
 "Either way, check anything important in a trusted source. Save this for later.",
 "Follow Tech Mendly for a new tech tip every day.",
]
shown=[s.replace("Tech Mendly","@techmendly") for s in scenes]
pads=[0.3,0.3,0.4,0.4,0.4,0.5,0.4]
from kokoro_onnx import Kokoro
k=Kokoro(os.path.expanduser("~/kokoro/kokoro-v1.0.onnx"),os.path.expanduser("~/kokoro/voices-v1.0.bin"))
voice=[]
for i,t in enumerate(scenes):
    a,sr=k.create(t,voice="am_michael",speed=1.05,lang="en-us")
    sf.write(f"/tmp/hf/build/l{i}_raw.wav",a,sr)
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",f"/tmp/hf/build/l{i}_raw.wav","-ar",str(SR),"-ac","1","-sample_fmt","s16",f"/tmp/hf/build/l{i}.wav"],check=True)
    with wave.open(f"/tmp/hf/build/l{i}.wav") as w: voice.append(np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768)
SS,SE,TL,cur=[],[],[],0.0
for i,v in enumerate(voice):
    dur=len(v)/SR; lead=0.25 if i==0 else 0.1
    SS.append(cur); TL.append((cur+lead,cur+lead+dur)); cur+=lead+dur+0.3+pads[i]; SE.append(cur)
TOTAL=SE[-1]+0.4; SE[-1]=TOTAL
n=int(TOTAL*SR); vt=np.zeros(n,dtype=np.float32)
for (s_,e_),v in zip(TL,voice): vt[int(s_*SR):int(s_*SR)+len(v)]+=v
vt=vt/(np.max(np.abs(vt)) or 1)*0.85
t=np.arange(n)/SR; mus=np.zeros(n); chords=[[220,261.63,329.63],[174.61,220,261.63],[261.63,329.63,392],[196,246.94,293.66]]
seg=TOTAL/len(chords)
for i,ch in enumerate(chords):
    a,b=int(i*seg*SR),int(min(n,(i+1)*seg*SR)); tt=t[a:b]
    env=np.minimum(1,(tt-tt[0])/0.5)*np.minimum(1,(tt[-1]-tt)/0.5)
    for fq in ch: mus[a:b]+=0.016*np.sin(2*np.pi*fq*tt)*env
mus*=np.minimum(1,(TOTAL-t)/1.0)
rng=np.random.default_rng(7); fx=np.zeros(n)
for i in range(1,len(SS)):
    a=int((SS[i]-0.05)*SR); m=int(0.22*SR); tt=np.arange(m)/SR
    env=np.sin(np.pi*np.minimum(1,tt/0.22))**2
    fx[a:a+m]+=0.10*np.convolve(rng.standard_normal(m),np.ones(40)/40,mode="same")*env
mix=np.clip(vt+mus+fx,-0.95,0.95)
pcm=(np.stack([mix,mix],1)*32767).astype(np.int16)
with wave.open(OUT+"/assets/voice.wav","wb") as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())
json.dump(dict(SS=SS,SE=SE,TL=TL,TOTAL=TOTAL,shown=shown),open("/tmp/hf/build/timing.json","w"))
print([round(x,2) for x in SS],round(TOTAL,2))
