import json, html
T=json.load(open("/tmp/hf/build/timing.json")); SS,SE,TL,TOT,shown=T["SS"],T["SE"],T["TL"],T["TOTAL"],T["shown"]
r=lambda x: round(x,3)
tw=[]  # timeline js lines
def J(s): tw.append(s)

# ---- captions ----
cap_html=[]
for i,txt in enumerate(shown):
    words=txt.split(); wts=[len(w)+1 for w in words]; tot=sum(wts); s0,e0=TL[i]; acc=0
    spans=[]
    for k,w in enumerate(words):
        spans.append(f'<span id="c{i}w{k}">{html.escape(w)}</span>')
        a=s0+(e0-s0)*acc/tot; acc+=wts[k]; b=s0+(e0-s0)*acc/tot
        J(f'tl.to("#c{i}w{k}",{{color:"#FFD60A",duration:0.01}},{r(a)});')
        J(f'tl.to("#c{i}w{k}",{{color:"#ffffff",duration:0.01}},{r(b)});')
    st=SS[i]; du=SE[i]-SS[i]
    cap_html.append(f'<div id="cap{i}" class="clip cap" data-start="{r(st)}" data-duration="{r(du)}" data-track-index="9"><div class="capbox" id="capbox{i}">{" ".join(spans)}</div></div>')
    J(f'tl.fromTo("#capbox{i}",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.25,ease:"power3.out"}},{r(st+0.05)});')
    if i<len(shown)-1: J(f'tl.to("#capbox{i}",{{opacity:0,duration:0.2}},{r(SE[i]-0.25)});')

def scene(id,s,e,inner,idx):
    return f'<div id="{id}" class="clip scene" data-start="{r(s)}" data-duration="{r(e-s)}" data-track-index="{idx}"><div class="wrap" id="{id}w">{inner}</div></div>'
def fade_out(id,e): J(f'tl.to("#{id}w",{{opacity:0,y:-30,duration:0.22,ease:"power2.in"}},{r(e-0.3)});')

chars=lambda id,text:''.join(f'<span class="ch" id="{id}{n}">{html.escape(c) if c!=" " else "&nbsp;"}</span>' for n,c in enumerate(text))
scn=[]

# ---- S0 hook ----
s,e=SS[0],SE[0]
scn.append(scene("s0",s,e,'''
<div class="orb" id="s0orb"><div class="orbring"><i></i><i></i><i></i></div><b>AI</b></div>
<div class="hook"><div class="hl" id="s0a">Is your AI</div><div class="hl acc" id="s0b">making things</div><div class="hl acc" id="s0c">up?</div></div>
<div class="pillbig" id="s0p">Ask it twice.</div>''',1))
J(f'tl.fromTo("#s0orb",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:0.5,ease:"back.out(1.8)"}},{r(s+0.1)});')
J(f'tl.fromTo("#s0orb .orbring",{{rotation:0}},{{rotation:360,duration:{r(e-s)},ease:"none"}},{r(s)});')
for n,(a,off) in enumerate([("s0a",0.3),("s0b",0.7),("s0c",1.0)]):
    J(f'tl.fromTo("#{a}",{{opacity:0,y:60}},{{opacity:1,y:0,duration:0.45,ease:"power3.out"}},{r(s+off)});')
J(f'tl.fromTo("#s0p",{{scale:0.6,opacity:0}},{{scale:1,opacity:1,duration:0.4,ease:"back.out(2)"}},{r(s+3.3)});')
# glitch flicker on orb text
for k,tt in enumerate([1.6,1.75,2.4]):
    J(f'tl.fromTo("#s0orb b",{{opacity:1}},{{opacity:0.2,duration:0.05,yoyo:true,repeat:1,immediateRender:false}},{r(s+tt)});')
fade_out("s0",e)

# ---- S1+S2 chat compare ----
s1,e1=SS[1],SE[1]; s2,e2=SS[2],SE[2]
def panel(n,ans_a,ans_b,top):
    return f'''<div class="panel" id="p{n}" style="top:{top}px">
 <div class="plabel">Chat {n}</div>
 <div class="ub" id="ub{n}">{chars(f"q{n}_","When was Acme Corp founded?")}</div>
 <div class="rb" id="rb{n}">Acme Corp was founded in <span class="yr" id="yr{n}">{ans_a}</span>.</div>
</div>'''
inner=panel(1,"2009","",270)+panel(2,"2014","",690)+'''
<div class="badge red" id="badge">✕ Different answers</div>'''
scn.append(scene("s12",s1,e2,inner,2))
for n,(off) in [(1,0.4),(2,1.6)]:
    st=s1+off
    J(f'tl.fromTo("#p{n}",{{opacity:0,y:50}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{r(st)});')
    J(f'tl.fromTo("#ub{n}",{{opacity:0,scale:0.9}},{{opacity:1,scale:1,duration:0.3,ease:"back.out(1.6)"}},{r(st+0.35)});')
    J(f'tl.fromTo("#ub{n} .ch",{{opacity:0}},{{opacity:1,duration:0.05,stagger:0.035}},{r(st+0.5)});')
J(f'tl.fromTo("#p1",{{scale:1}},{{scale:1.0,duration:0.01}},{r(s1)});')
# replies in S2
J(f'tl.fromTo("#rb1",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.45,ease:"power3.out"}},{r(s2+0.5)});')
J(f'tl.fromTo("#rb2",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.45,ease:"power3.out"}},{r(s2+1.1)});')
for n in (1,2):
    J(f'tl.to("#yr{n}",{{color:"#E85454",scale:1.15,duration:0.3,ease:"back.out(2)"}},{r(s2+2.3)});')
J(f'tl.fromTo("#badge",{{scale:0.5,opacity:0}},{{scale:1,opacity:1,duration:0.4,ease:"back.out(2.2)"}},{r(s2+2.5)});')
fade_out("s12",e2)

# ---- S3 disagree ----
s,e=SS[3],SE[3]
scn.append(scene("s3",s,e,'''
<div class="chiprow"><div class="chip" id="s3a">2009</div><div class="neq" id="s3n">≠</div><div class="chip" id="s3b">2014</div></div>
<svg class="tri" id="s3t" viewBox="0 0 120 108"><path d="M60 8 L112 100 L8 100 Z" fill="none" stroke="#FFD60A" stroke-width="8" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" id="s3tp"/><rect x="55" y="38" width="10" height="34" rx="5" fill="#FFD60A" id="s3e1"/><circle cx="60" cy="84" r="6" fill="#FFD60A" id="s3e2"/></svg>
<div class="big" id="s3x">It may be <span class="red">guessing</span></div>
<div class="sub" id="s3y">Don't trust that answer.</div>''',3))
J(f'tl.fromTo("#s3a",{{x:-120,opacity:0}},{{x:0,opacity:1,duration:0.5,ease:"power3.out"}},{r(s+0.2)});')
J(f'tl.fromTo("#s3b",{{x:120,opacity:0}},{{x:0,opacity:1,duration:0.5,ease:"power3.out"}},{r(s+0.2)});')
J(f'tl.fromTo("#s3n",{{scale:0,opacity:0,rotation:-40}},{{scale:1,opacity:1,rotation:0,duration:0.45,ease:"back.out(2.4)"}},{r(s+0.7)});')
J(f'tl.fromTo("#s3tp",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:0.8,ease:"power2.inOut"}},{r(s+1.2)});')
J(f'tl.fromTo("#s3e1,#s3e2",{{opacity:0}},{{opacity:1,duration:0.2}},{r(s+1.9)});')
J(f'tl.fromTo("#s3t",{{x:0}},{{x:0,duration:0.01}},{r(s)});')
for k in range(4):
    J(f'tl.to("#s3t",{{x:(k%2?-10:10),duration:0.06}},{r(s+2.0+k*0.07)});'.replace("(k%2?-10:10)",str(-10 if k%2 else 10)))
J(f'tl.to("#s3t",{{x:0,duration:0.06}},{r(s+2.3)});')
J(f'tl.fromTo("#s3x",{{opacity:0,y:40}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{r(s+1.6)});')
J(f'tl.fromTo("#s3y",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{r(s+2.4)});')
fade_out("s3",e)

# ---- S4 match ----
s,e=SS[4],SE[4]
scn.append(scene("s4",s,e,'''
<div class="chiprow"><div class="chip ok" id="s4a">2009</div><div class="eq" id="s4n">=</div><div class="chip ok" id="s4b">2009</div></div>
<svg class="tick" id="s4t" viewBox="0 0 120 120"><circle cx="60" cy="60" r="52" fill="none" stroke="#34C778" stroke-width="8" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" id="s4c"/><path d="M34 62 L53 80 L88 42" fill="none" stroke="#34C778" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1 1.2" stroke-dashoffset="1.1" id="s4p"/></svg>
<div class="big" id="s4x">A good sign…</div>
<div class="big" id="s4y"><span class="mute">…but</span> <span class="yel">not proof</span></div>''',4))
J(f'tl.fromTo("#s4a",{{x:-120,opacity:0}},{{x:0,opacity:1,duration:0.5,ease:"power3.out"}},{r(s+0.2)});')
J(f'tl.fromTo("#s4b",{{x:120,opacity:0}},{{x:0,opacity:1,duration:0.5,ease:"power3.out"}},{r(s+0.2)});')
J(f'tl.fromTo("#s4n",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:0.45,ease:"back.out(2.4)"}},{r(s+0.7)});')
J(f'tl.fromTo("#s4c",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:0.6,ease:"power2.inOut"}},{r(s+1.1)});')
J(f'tl.fromTo("#s4p",{{strokeDashoffset:1.1}},{{strokeDashoffset:0,duration:0.5,ease:"power2.out"}},{r(s+1.6)});')
J(f'tl.fromTo("#s4x",{{opacity:0,y:40}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{r(s+1.7)});')
J(f'tl.fromTo("#s4y",{{opacity:0,y:40,scale:0.9}},{{opacity:1,y:0,scale:1,duration:0.5,ease:"back.out(1.8)"}},{r(s+2.5)});')
fade_out("s4",e)

# ---- S5 verify ----
s,e=SS[5],SE[5]
scn.append(scene("s5",s,e,'''
<svg class="shield" id="s5s" viewBox="0 0 120 140"><path d="M60 8 L108 26 V68 C108 98 86 122 60 132 C34 122 12 98 12 68 V26 Z" fill="rgba(94,234,212,0.10)" stroke="#5EEAD4" stroke-width="7" stroke-linejoin="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1" id="s5sp"/><path d="M38 70 L54 86 L84 50" fill="none" stroke="#5EEAD4" stroke-width="9" stroke-linecap="round" stroke-linejoin="round" pathLength="1" stroke-dasharray="1 1.2" stroke-dashoffset="1.1" id="s5ck"/></svg>
<div class="big" id="s5x">Check it in a<br><span class="teal">trusted source</span></div>
<div class="rows"><div class="row" id="s5r1"><i></i>Official websites</div><div class="row" id="s5r2"><i></i>Trusted guides and docs</div></div>
<div class="pillbig save" id="s5p">🔖 Save this</div>''',5))
J(f'tl.fromTo("#s5s",{{scale:0.6,opacity:0}},{{scale:1,opacity:1,duration:0.4,ease:"back.out(1.8)"}},{r(s+0.1)});')
J(f'tl.fromTo("#s5sp",{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:0.8,ease:"power2.inOut"}},{r(s+0.3)});')
J(f'tl.fromTo("#s5ck",{{strokeDashoffset:1.1}},{{strokeDashoffset:0,duration:0.5,ease:"power2.out"}},{r(s+1.0)});')
J(f'tl.fromTo("#s5x",{{opacity:0,y:40}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{r(s+0.9)});')
J(f'tl.fromTo("#s5r1",{{opacity:0,x:-80}},{{opacity:1,x:0,duration:0.45,ease:"power3.out"}},{r(s+1.7)});')
J(f'tl.fromTo("#s5r2",{{opacity:0,x:-80}},{{opacity:1,x:0,duration:0.45,ease:"power3.out"}},{r(s+2.1)});')
J(f'tl.fromTo("#s5p",{{scale:0.5,opacity:0}},{{scale:1,opacity:1,duration:0.45,ease:"back.out(2.2)"}},{r(s+(SE[5]-SS[5])-1.9)});')
fade_out("s5",e)

# ---- S6 outro ----
s,e=SS[6],SE[6]
scn.append(scene("s6",s,e,'''
<svg class="logo" id="s6l" viewBox="5 5 50 50"><polygon points="9,15 23,15 34.5,26.5 9,26.5" fill="#fff"/><polygon points="34.5,26.5 34.5,52 23,52 23,38" fill="#fff"/><polygon points="32,9 51,9 51,27.5 42,27.5 42,18 32,18" fill="#5EEAD4"/></svg>
<div class="big" id="s6x">Follow <span class="teal">@techmendly</span></div>
<div class="sub" id="s6y">A new tech tip every day</div>''',6))
J(f'tl.fromTo("#s6l",{{scale:0,rotation:-90,opacity:0}},{{scale:1,rotation:0,opacity:1,duration:0.7,ease:"back.out(1.7)"}},{r(s+0.1)});')
J(f'tl.fromTo("#s6x",{{opacity:0,y:50}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{r(s+0.7)});')
J(f'tl.fromTo("#s6y",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.5,ease:"power3.out"}},{r(s+1.2)});')

# ---- ambient ----
J(f'tl.fromTo("#glow1",{{x:-80,y:0}},{{x:120,y:160,duration:{r(TOT)},ease:"none"}},0);')
J(f'tl.fromTo("#glow2",{{x:60,y:0}},{{x:-140,y:-200,duration:{r(TOT)},ease:"none"}},0);')
J(f'tl.fromTo("#bar",{{scaleX:0}},{{scaleX:1,duration:{r(TOT)},ease:"none"}},0);')

css=open("/tmp/hf/build/style.css").read()
page=f'''<!doctype html>
<html lang="en" data-resolution="portrait">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<script src="assets/gsap.min.js"></script>
<style>{css}</style></head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{r(TOT)}" data-width="1080" data-height="1920">
<div class="bg"><div class="glow g1" id="glow1"></div><div class="glow g2" id="glow2"></div></div>
<div class="hdr"><svg viewBox="5 5 50 50" class="hl2"><polygon points="9,15 23,15 34.5,26.5 9,26.5" fill="#fff"/><polygon points="34.5,26.5 34.5,52 23,52 23,38" fill="#fff"/><polygon points="32,9 51,9 51,27.5 42,27.5 42,18 32,18" fill="#5EEAD4"/></svg><span>@techmendly</span></div>
<div class="tag">AI TIP</div>
{chr(10).join(scn)}
{chr(10).join(cap_html)}
<div id="bar" class="bar"></div>
<audio id="voice" src="assets/voice.wav" data-start="0" data-duration="{r(TOT)}" data-track-index="20" data-volume="1"></audio>
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(tw)}
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body></html>'''
open("/tmp/hf/reel37/index.html","w").write(page)
print("ok",len(page))
