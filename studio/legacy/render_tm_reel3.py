import math, subprocess, wave, os
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageChops
from kokoro_onnx import Kokoro

W, H, FPS = 1080, 1920, 30
POP_B = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
POP_M = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
POP_R = "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf"
INTER = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
INTER_B = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
WORK = "/home/claude/v7"
OUT = "/home/claude/techmendly_reel_02_ai_prompt_v2.mp4"
os.makedirs(WORK, exist_ok=True)

_fc = {}
def F(p, s):
    k = (p, s)
    if k not in _fc:
        try:
            _fc[k] = ImageFont.truetype(p, s)
        except Exception:
            _fc[k] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", s)
    return _fc[k]

BG = (240, 240, 241)
NAVY = (20, 24, 40)
YEL = (255, 214, 10)
TEAL = (14, 140, 110)
BLUE = (34, 113, 177)
RED = (214, 66, 66)
GRN = (60, 180, 110)
GREY = (90, 95, 100)
BORDER = (200, 204, 210)
ORANGE = (246, 130, 31)

SPOKEN = [
    "Getting boring answers from AI? The problem is usually your prompt.",
    "A good prompt has three parts. Who, what, and how.",
    "One. Tell it who it is. For example, you are a social media manager for a bakery.",
    "Two. Say exactly what you want. Write three Instagram captions for a new chocolate cake.",
    "Three. Say how it should look. Keep each one short and friendly.",
    "Now send it. See the difference? Specific in, useful out.",
    "Save this for your next prompt. Follow Tech Mendly for a new tech tip every day.",
]
SHOWN = SPOKEN[:-1] + ["Save this for your next prompt. Follow TechMendly for a new tech tip every day."]
PAD = [0.3, 0.4, 0.9, 0.9, 0.9, 1.4, 0.5]
LABELS = ["THE PROBLEM", "THE FORMULA", "STEP 1 of 3", "STEP 2 of 3", "STEP 3 of 3", "THE RESULT", "RECAP"]
SR = 48000

# ------------------------------------------------------------------ voice
k = Kokoro("/home/claude/kokoro/kokoro-v1.0.onnx", "/home/claude/kokoro/voices-v1.0.bin")
voice = []
for i, text in enumerate(SPOKEN):
    audio, sr = k.create(text, voice="am_michael", speed=1.05, lang="en-us")
    raw = f"{WORK}/line{i}_raw.wav"
    sf.write(raw, audio, sr)
    out = f"{WORK}/line{i}.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", out], check=True)
    with wave.open(out) as w:
        voice.append(np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768)

SS, SE, TL = [], [], []
cur = 0.0
for i, d_ in enumerate(voice):
    dur = len(d_) / SR
    lead = 0.3 if i == 0 else 0.15
    SS.append(cur)
    TL.append((cur + lead, cur + lead + dur))
    cur = cur + lead + dur + 0.35 + PAD[i]
    SE.append(cur)
TOTAL = SE[-1] + 0.6
SE[-1] = TOTAL
print("timeline", [(round(a, 2), round(b, 2)) for a, b in TL], "total", round(TOTAL, 2))

def T(si, frac):
    return SS[si] + frac * (SE[si] - SS[si])

CLICKS = {5: [0.30]}

def build_audio(path):
    n = int(TOTAL * SR)
    vt = np.zeros(n, dtype=np.float32)
    for (s, e), d_ in zip(TL, voice):
        a = int(s * SR)
        vt[a:a + len(d_)] += d_
    vt = vt / (np.max(np.abs(vt)) or 1) * 0.85
    t = np.arange(n) / SR
    chords = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [261.63, 329.63, 392.0], [196.0, 246.94, 293.66]]
    seg = TOTAL / len(chords)
    mus = np.zeros(n)
    for i, ch in enumerate(chords):
        a, b = int(i * seg * SR), int(min(n, (i + 1) * seg * SR))
        tt = t[a:b]
        env = np.minimum(1, (tt - tt[0]) / 0.5) * np.minimum(1, (tt[-1] - tt) / 0.5)
        for f in ch:
            mus[a:b] += 0.016 * np.sin(2 * np.pi * f * tt) * env
    mus *= np.minimum(1, (TOTAL - t) / 1.0)
    rng = np.random.default_rng(3)
    clicks = np.zeros(n)
    for si, fr in CLICKS.items():
        for f in fr:
            a = int(T(si, f) * SR)
            m = int(0.02 * SR)
            tt = np.arange(m) / SR
            clicks[a:a + m] += 0.18 * rng.standard_normal(m) * np.exp(-tt * 260)
    mix = np.clip(vt + mus + clicks, -0.95, 0.95)
    pcm = (np.stack([mix, mix], axis=1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())

# ------------------------------------------------------------------ helpers
def ease(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3

def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def lerp(a, b, t):
    return a + (b - a) * t

def tw(d, t, f):
    return d.textlength(t, font=f)

def ctext(d, y, t, f, fill, cx=W / 2):
    d.text((cx - tw(d, t, f) / 2, y), t, font=f, fill=fill)

def path_pos(f, pts):
    if f <= pts[0][0]:
        return pts[0][1], pts[0][2]
    for (f0, x0, y0), (f1, x1, y1) in zip(pts, pts[1:]):
        if f <= f1:
            u = smooth((f - f0) / (f1 - f0))
            return lerp(x0, x1, u), lerp(y0, y1, u)
    return pts[-1][1], pts[-1][2]

def cursor(d, x, y):
    pts = [(0, 0), (0, 44), (12, 34), (20, 52), (29, 48), (21, 31), (36, 31)]
    d.polygon([(x + a, y + b) for a, b in pts], fill=(255, 255, 255), outline=(15, 15, 15))

def ripple(d, x, y, f, fc):
    u = (f - fc) / 0.10
    if 0 <= u <= 1:
        r = 18 + u * 52
        d.ellipse([x - r, y - r, x + r, y + r], outline=YEL + (int(255 * (1 - u)),), width=7)

def badge(d, cx, cy, size, bg, fg):
    s = size / 43.0
    ox = cx - 30 * s; oy = cy - 30.5 * s
    P = lambda pts: [(ox + x * s, oy + y * s) for x, y in pts]
    nv = (15, 23, 42); tl = (94, 234, 212)
    d.polygon(P([(9, 15), (23, 15), (34.5, 26.5), (9, 26.5)]), fill=nv)
    d.polygon(P([(34.5, 26.5), (34.5, 52), (23, 52), (23, 38)]), fill=nv)
    d.polygon(P([(32, 9), (51, 9), (51, 27.5), (42, 27.5), (42, 18), (32, 18)]), fill=tl)

def button(d, box, label, fill, fg, f, pressed=False, outline=None, radius=12):
    x0, y0, x1, y1 = box
    if pressed:
        x0 += 3; y0 += 3; x1 -= 3; y1 -= 3
        fill = tuple(int(c * 0.82) for c in fill)
    d.rounded_rectangle((x0, y0, x1, y1), radius=radius, fill=fill, outline=outline, width=3 if outline else 0)
    d.text(((x0 + x1) / 2 - tw(d, label, f) / 2, (y0 + y1) / 2 - f.size * 0.68), label, font=f, fill=fg)

def ring(d, box, a):
    if a <= 0:
        return
    x0, y0, x1, y1 = box
    d.rounded_rectangle((x0 - 14, y0 - 14, x1 + 14, y1 + 14), radius=22, outline=YEL + (int(255 * a),), width=8)

def toast(d, x0, y0, x1, y1, text, a):
    if a <= 0:
        return
    A = int(255 * a)
    d.rounded_rectangle((x0, y0, x1, y1), radius=14, fill=(230, 247, 238, A), outline=GRN + (A,), width=3)
    cy = (y0 + y1) / 2
    d.ellipse([x0 + 24, cy - 24, x0 + 72, cy - 24 + 48], fill=GRN + (A,))
    d.line([(x0 + 36, cy), (x0 + 46, cy + 11), (x0 + 62, cy - 12)], fill=(255, 255, 255, A), width=6)
    d.text((x0 + 92, cy - 22), text, font=F(INTER_B, 34), fill=(25, 100, 60, A))

def chip(d, x, y, text, f, fill, fg, pad=22, h=None):
    w = tw(d, text, f) + pad * 2
    h = h or int(f.size * 1.9)
    d.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=fill)
    d.text((x + pad, y + h / 2 - f.size * 0.68), text, font=f, fill=fg)
    return w

def keycap(d, x, y, label, f=None):
    f = f or F(INTER_B, 30)
    w = max(64, tw(d, label, f) + 36)
    d.rounded_rectangle((x, y + 6, x + w, y + 70), radius=12, fill=(190, 194, 200))
    d.rounded_rectangle((x, y, x + w, y + 62), radius=12, fill=(255, 255, 255), outline=(200, 204, 210), width=3)
    d.text((x + w / 2 - tw(d, label, f) / 2, y + 12), label, font=f, fill=NAVY)
    return w + 14

def wp_base(d, items, active):
    d.rounded_rectangle((40, 270, 1040, 1330), radius=30, fill=(255, 255, 255), outline=BORDER, width=3)
    d.rounded_rectangle((40, 270, 1040, 360), radius=30, fill=(29, 35, 39))
    d.rectangle((40, 320, 1040, 360), fill=(29, 35, 39))
    d.ellipse([70, 292, 112, 334], fill=BG)
    d.text((81, 295), "W", font=F(INTER_B, 30), fill=(29, 35, 39))
    d.text((135, 296), "yoursite.com", font=F(INTER, 30), fill=BG)
    d.text((810, 296), "Howdy, admin", font=F(INTER, 28), fill=(190, 195, 200))
    d.rounded_rectangle((42, 360, 270, 1328), radius=28, fill=(35, 40, 45))
    d.rectangle((42, 360, 270, 440), fill=(35, 40, 45))
    for i, m in enumerate(items):
        yy = 395 + i * 78
        if m == active:
            d.rectangle((42, yy - 14, 270, yy + 54), fill=(0, 115, 170))
            d.text((70, yy), m, font=F(INTER_B, 28), fill=(255, 255, 255))
        else:
            d.text((70, yy), m, font=F(INTER, 28), fill=(190, 195, 200))

def browser_base(d, url, dark=False, tabname="New Tab"):
    top = (53, 54, 58) if dark else (222, 225, 230)
    d.rounded_rectangle((40, 270, 1040, 1330), radius=30, fill=(255, 255, 255), outline=BORDER, width=3)
    d.rounded_rectangle((40, 270, 1040, 420), radius=30, fill=top)
    d.rectangle((40, 360, 1040, 420), fill=top)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([72 + i * 40, 300, 92 + i * 40, 320], fill=c)
    d.rounded_rectangle((260, 288, 620, 345), radius=14, fill=(32, 33, 36) if dark else (255, 255, 255))
    d.text((282, 298), tabname, font=F(INTER, 26), fill=(230, 232, 236) if dark else GREY)
    d.rounded_rectangle((70, 350, 1010, 410), radius=30, fill=(32, 33, 36) if dark else (255, 255, 255))
    d.text((100, 358), url, font=F(INTER, 30), fill=(230, 232, 236) if dark else NAVY)
    if dark:
        d.text((760, 296), "Incognito", font=F(INTER_B, 26), fill=(190, 195, 205))

# ------------------------------------------------------------------ prompt reel scenes
PROMPT = ["You are a social media manager for a bakery.",
          "Write 3 Instagram captions for a new chocolate cake.",
          "Keep each one short and friendly."]
ANS = ["Fresh out of the oven! Our new chocolate cake is here.",
       "Chocolate lovers, this one is for you. Come and get a slice.",
       "Slice, share, repeat. New chocolate cake, today only."]
PCOL = [TEAL, BLUE, ORANGE]

def wrap(d, text, f, maxw):
    out, cl = [], ""
    for w_ in text.split():
        t_ = (cl + " " + w_).strip()
        if tw(d, t_, f) <= maxw: cl = t_
        else: out.append(cl); cl = w_
    out.append(cl)
    return out

def chat_base(d, title="AI Assistant"):
    d.rounded_rectangle((40, 270, 1040, 1330), radius=30, fill=(255, 255, 255), outline=BORDER, width=3)
    d.rounded_rectangle((40, 270, 1040, 360), radius=30, fill=(244, 245, 247))
    d.rectangle((40, 330, 1040, 360), fill=(244, 245, 247))
    d.line((41, 360, 1039, 360), fill=(225, 228, 232), width=2)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([72 + i * 40, 303, 92 + i * 40, 323], fill=c)
    ctext(d, 297, title, F(INTER_B, 30), NAVY)

def input_box(d, lines, typed=None, active=-1, lt=0.0, send_pressed=False, ring_a=1.0, hint=True):
    d.rounded_rectangle((70, 1030, 1010, 1300), radius=28, fill=(246, 247, 248), outline=BORDER, width=3)
    fn = F(INTER, 31)
    shown_any = False
    for i, ln in enumerate(lines):
        txt = ln
        if typed is not None and i == active:
            txt = ln[:int(len(ln) * typed)]
        if i > active and typed is not None:
            continue
        y = 1062 + i * 56
        if i == active and typed is not None:
            ring_box = (96, y - 4, 96 + max(40, tw(d, txt, fn)) + 20, y + 46)
            d.rounded_rectangle(ring_box, radius=10, outline=YEL + (int(255 * ring_a),), width=5)
        d.text((106, y + 2), txt, font=fn, fill=(PCOL[i]) if (typed is not None and i == active) else (30, 34, 40))
        shown_any = True
        if i == active and typed is not None and typed < 1 and int(lt * 3) % 2 == 0:
            cx = 106 + tw(d, txt, fn) + 3
            d.rectangle((cx, y + 4, cx + 3, y + 40), fill=NAVY)
    if not shown_any and hint:
        d.text((106, 1064), "Ask anything...", font=fn, fill=(150, 155, 162))
    cx, cy = 955, 1262
    col = tuple(int(c * 0.82) for c in BLUE) if send_pressed else BLUE
    d.ellipse([cx - 36, cy - 36, cx + 36, cy + 36], fill=col)
    d.polygon([(cx - 14, cy + 4), (cx, cy - 16), (cx + 14, cy + 4), (cx + 5, cy + 4), (cx + 5, cy + 16), (cx - 5, cy + 16), (cx - 5, cy + 4)], fill=(255, 255, 255))

def bubble(d, x0, y0, w, lines, f, fill, fg, a=1.0, lh=44):
    A = int(255 * a)
    h = len(lines) * lh + 40
    d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=26, fill=fill + (A,))
    for i, ln in enumerate(lines):
        d.text((x0 + 28, y0 + 20 + i * lh), ln, font=f, fill=fg + (A,))
    return h

def scene_hook(d, lt, dur):
    f = lt / dur
    chat_base(d)
    fn = F(INTER, 32)
    a1 = ease((f - 0.10) / 0.12)
    ul = ["Write a post about", "my bakery"]
    if a1 > 0:
        w = 520
        bubble(d, 1010 - w - 10, 420, w, ul, fn, BLUE, (255, 255, 255), a1)
    a2 = ease((f - 0.30) / 0.14)
    if a2 > 0:
        al = wrap(d, "Welcome to our bakery! We sell cakes and bread. Visit us today!", fn, 620)
        h = bubble(d, 70, 590, 700, al, fn, (234, 236, 240), (40, 44, 52), a2)
    a3 = ease((f - 0.52) / 0.12)
    if a3 > 0:
        chip(d, 70, 810, "Boring and generic", F(INTER_B, 30), RED + (int(255 * a3),), (255, 255, 255, int(255 * a3)))
    a4 = ease((f - 0.68) / 0.15)
    if a4 > 0:
        ctext(d, 1020, "Vague in. Vague out.", F(POP_B, 62), RED + (int(255 * a4),))

def scene_formula(d, lt, dur):
    f = lt / dur
    items = [("1", "WHO", "Give it a role", TEAL), ("2", "WHAT", "State the task", BLUE), ("3", "HOW", "Pick the format", ORANGE)]
    ctext(d, 330, "A good prompt has", F(POP_M, 48), GREY)
    ctext(d, 400, "3 parts", F(POP_B, 110), NAVY)
    for i, (n, big, sub, col) in enumerate(items):
        y = 600 + i * 230
        ra = ease((f - 0.20 - i * 0.18) / 0.15)
        if ra <= 0: continue
        A = int(255 * ra)
        d.rounded_rectangle((80, y, 1000, y + 190), radius=34, fill=(255, 255, 255, A), outline=BORDER + (A,), width=3)
        d.ellipse([110, y + 40, 220, y + 150], fill=col + (A,))
        ctext(d, y + 52, n, F(POP_B, 70), (255, 255, 255, A), cx=165)
        d.text((260, y + 28), big, font=F(POP_B, 72), fill=col + (A,))
        d.text((260, y + 114), sub, font=F(POP_M, 40), fill=GREY + (A,))

STEP_INFO = {2: ("WHO", "Tell it who it is", "A role gives better tone and detail."),
             3: ("WHAT", "Say what you want", "Be exact: how many, about what."),
             4: ("HOW", "Say how it should look", "Length, tone, format.")}

def scene_step(d, lt, dur, idx):
    f = lt / dur
    chat_base(d)
    big, title, sub = STEP_INFO[idx]
    col = PCOL[idx - 2]
    a = ease((f - 0.02) / 0.15)
    ctext(d, 450, big, F(POP_B, 170), col + (int(255 * a),))
    ctext(d, 680, title, F(POP_B, 52), NAVY + (int(255 * a),))
    ctext(d, 760, sub, F(INTER, 34), GREY + (int(255 * a),))
    n = idx - 2
    typed = ease((f - 0.15) / 0.60)
    lines_done = PROMPT[:n]
    for i in range(n):
        pass
    input_box_multi(d, n, typed, lt, f)

def input_box_multi(d, n, typed, lt, f):
    d.rounded_rectangle((70, 1030, 1010, 1300), radius=28, fill=(246, 247, 248), outline=BORDER, width=3)
    fn = F(INTER, 31)
    for i in range(n + 1):
        y = 1062 + i * 56
        txt = PROMPT[i]
        cur = (i == n)
        if cur:
            txt = txt[:int(len(txt) * typed)]
            if typed > 0:
                ring_a = 1.0
                d.rounded_rectangle((96, y - 4, 96 + max(40, tw(d, txt, fn)) + 20, y + 46), radius=10, outline=YEL, width=5)
        d.text((106, y + 2), txt, font=fn, fill=PCOL[i] if cur else (30, 34, 40))
        if cur and typed < 1 and int(lt * 3) % 2 == 0:
            cx = 106 + tw(d, txt, fn) + 3
            d.rectangle((cx, y + 4, cx + 3, y + 40), fill=NAVY)
    if n == 0 and typed <= 0:
        d.text((106, 1064), "Ask anything...", font=fn, fill=(150, 155, 162))
    cx, cy = 955, 1262
    d.ellipse([cx - 36, cy - 36, cx + 36, cy + 36], fill=BLUE)
    d.polygon([(cx - 14, cy + 4), (cx, cy - 16), (cx + 14, cy + 4), (cx + 5, cy + 4), (cx + 5, cy + 16), (cx - 5, cy + 16), (cx - 5, cy + 4)], fill=(255, 255, 255))

def scene_result(d, lt, dur):
    f = lt / dur
    chat_base(d)
    fn = F(INTER, 30)
    sent = f >= 0.32
    if not sent:
        for i in range(3):
            y = 1062 + i * 56
            d.text((106, y + 2), PROMPT[i], font=F(INTER, 31), fill=(30, 34, 40))
        d.rounded_rectangle((70, 1030, 1010, 1300), radius=28, outline=BORDER, width=3)
    else:
        d.rounded_rectangle((70, 1030, 1010, 1300), radius=28, fill=(246, 247, 248), outline=BORDER, width=3)
        d.text((106, 1064), "Ask anything...", font=F(INTER, 31), fill=(150, 155, 162))
    pressed = 0.28 <= f < 0.34
    cx0, cy0 = 955, 1262
    d.ellipse([cx0 - 36, cy0 - 36, cx0 + 36, cy0 + 36], fill=tuple(int(c * 0.82) for c in BLUE) if pressed else BLUE)
    d.polygon([(cx0 - 14, cy0 + 4), (cx0, cy0 - 16), (cx0 + 14, cy0 + 4), (cx0 + 5, cy0 + 4), (cx0 + 5, cy0 + 16), (cx0 - 5, cy0 + 16), (cx0 - 5, cy0 + 4)], fill=(255, 255, 255))
    if not sent:
        ring(d, (cx0 - 36, cy0 - 36, cx0 + 36, cy0 + 36), ease((f - 0.10) / 0.10))
    y = 390
    for i, txt in enumerate(ANS):
        a = ease((f - 0.38 - i * 0.12) / 0.10)
        al = wrap(d, txt, fn, 800)
        h = len(al) * 40 + 40
        if a > 0:
            bubble(d, 70, y, 860, al, fn, (234, 247, 240), (30, 60, 45), a, lh=40)
        y += h + 18
    a = ease((f - 0.78) / 0.12)
    if a > 0:
        chip(d, 70, y + 4, "Useful and ready to post", F(INTER_B, 30), GRN + (int(255 * a),), (255, 255, 255, int(255 * a)))
        ctext(d, y + 90, "Specific in. Useful out.", F(POP_B, 56), TEAL + (int(255 * a),))
    pts = [(0.0, 700, 1130), (0.15, 760, 1180), (0.27, 950, 1262), (1.0, 950, 1262)]
    cx, cy = path_pos(f, pts)
    for fc in CLICKS[5]:
        ripple(d, cx, cy, f, fc)
    if f < 0.6:
        cursor(d, cx - 6, cy - 4)

def scene_end(d, lt, dur):
    f = lt / dur
    badge(d, 540, 400, 170, TEAL, (255, 255, 255))
    ctext(d, 515, "TechMendly", F(POP_B, 96), NAVY)
    ctext(d, 640, "Tech made simple", F(POP_M, 44), TEAL)
    rows = ["Who: give it a role", "What: state the task", "How: pick the format"]
    for i, r in enumerate(rows):
        y = 760 + i * 100
        ra = ease((lt - 0.4 - i * 0.5) / 0.3)
        if ra <= 0: continue
        RA = int(255 * ra)
        d.rounded_rectangle((170, y, 910, y + 80), radius=40, fill=(255, 255, 255, RA), outline=BORDER + (RA,), width=3)
        d.ellipse([188, y + 12, 188 + 56, y + 12 + 56], fill=GRN + (RA,))
        d.line([(201, y + 41), (212, y + 52), (230, y + 29)], fill=(255, 255, 255, RA), width=7)
        d.text((266, y + 18), r, font=F(POP_B, 36), fill=NAVY + (RA,))
    pa = ease((lt - 2.2) / 0.4)
    if pa > 0:
        pulse = 1 + 0.025 * math.sin(lt * 6)
        pw, ph = 700 * pulse, 100 * pulse
        cx, cy = 540, 1215
        d.rounded_rectangle((cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2), radius=50, fill=NAVY + (int(255 * pa),))
        ctext(d, cy - 31, "Follow @techmendly", F(POP_B, 44), YEL + (int(255 * pa),))

SCENES = [scene_hook, scene_formula, lambda d, lt, dur: scene_step(d, lt, dur, 2), lambda d, lt, dur: scene_step(d, lt, dur, 3),
          lambda d, lt, dur: scene_step(d, lt, dur, 4), scene_result, scene_end]


def header(d, si):
    if si == 6:
        return
    d.rounded_rectangle((60, 150, 60 + tw(d, LABELS[si], F(POP_B, 38)) + 64, 230), radius=40, fill=NAVY)
    d.text((92, 163), LABELS[si], font=F(POP_B, 38), fill=(255, 255, 255))
    badge(d, 985, 190, 64, TEAL, (255, 255, 255))
    hf = F(POP_M, 34)
    d.text((940 - tw(d, "@techmendly", hf), 172), "@techmendly", font=hf, fill=GREY)

def captions(d, t):
    for i, (s, e) in enumerate(TL):
        if s - 0.05 <= t <= e + 0.30:
            words = SHOWN[i].split()
            wts = [len(w) + 1 for w in words]
            tot = sum(wts); acc = 0; curw = len(words) - 1
            prog = (t - s) / (e - s)
            for kk, wt in enumerate(wts):
                if prog <= (acc + wt) / tot:
                    curw = kk; break
                acc += wt
            f = F(POP_B, 50)
            lines, cl, idx = [], "", []
            for kk, w_ in enumerate(words):
                test = (cl + " " + w_).strip()
                if tw(d, test, f) <= 900:
                    cl = test; idx.append(kk)
                else:
                    lines.append((cl, idx)); cl = w_; idx = [kk]
            lines.append((cl, idx))
            top = 1420
            d.rounded_rectangle((60, top, 1020, top + len(lines) * 72 + 44), radius=20, fill=NAVY)
            for li, (ln, ix) in enumerate(lines):
                x = W / 2 - tw(d, ln, f) / 2
                y = top + 22 + li * 72
                for kk in ix:
                    d.text((x, y), words[kk], font=f, fill=YEL if kk == curw else (255, 255, 255))
                    x += tw(d, words[kk] + " ", f)
            return

def frame(t):
    img = Image.new("RGBA", (W, H), BG + (255,))
    si = max(i for i in range(len(SS)) if SS[i] <= t) if t < TOTAL else len(SS) - 1
    lt = t - SS[si]
    dur = SE[si] - SS[si]
    fa = min(ease(lt / 0.3), 1 - ease((lt - (dur - 0.25)) / 0.25)) if si < 6 else ease(lt / 0.3)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    SCENES[si](d, lt, dur)
    a = layer.getchannel("A")
    layer.putalpha(ImageChops.multiply(a, Image.new("L", (W, H), int(255 * max(0, min(1, fa))))))
    img = Image.alpha_composite(img, layer)
    top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dt = ImageDraw.Draw(top)
    header(dt, si)
    captions(dt, t)
    return Image.alpha_composite(img, top).convert("RGB")

def main():
    build_audio(f"{WORK}/mix.wav")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", f"{WORK}/mix.wav", "-c:v", "libx264", "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p",
           "-preset", "medium", "-crf", "19", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
           "-shortest", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(TOTAL * FPS)):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    marks = {"hook": T(0, 0.8), "formula": T(1, 0.85), "s1": T(2, 0.85), "s2": T(3, 0.85), "s3": T(4, 0.85), "result_pre": T(5, 0.2), "result": T(5, 0.95), "end": T(6, 0.85)}
    for name, tt in marks.items():
        frame(min(tt, TOTAL - 0.05)).save(f"{WORK}/p_{name}.png")

main()
