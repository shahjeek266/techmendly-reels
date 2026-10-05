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
WORK = "/home/claude/v_ur"
OUT = "/home/claude/techmendly_reel_01_elementor_urdu.mp4"
os.makedirs(WORK, exist_ok=True)

NAST = "/home/claude/urdu/NotoNastaliqUrdu[wght].ttf"
import re
AR = re.compile(r"[\u0600-\u06FF]")
def is_ur(t): return not re.search(r"[A-Za-z0-9]", t)
def tokens(text):
    """split into (text, [word idx]) runs: Latin words grouped LTR, trailing punctuation split off"""
    out = []
    for i, w in enumerate(text.split()):
        m = re.match(r"^(.*?)([،۔؟]*)$", w)
        core, pun = m.group(1), m.group(2)
        if core and not is_ur(core):
            if out and not is_ur(out[-1][0]) and out[-1][2] == "L":
                out[-1] = (out[-1][0] + " " + core, out[-1][1] + [i], "L")
            else:
                out.append((core, [i], "L"))
            if pun: out.append((pun, [i], "U"))
        else:
            out.append((w, [i], "U"))
    return [(a, b) for a, b, _ in out]
def UF(s):
    k = ("ur", s)
    if k not in _fc:
        f = ImageFont.truetype(NAST, s)
        try: f.set_variation_by_name("Bold")
        except Exception: pass
        _fc[k] = f
    return _fc[k]
def uw(d, t, s):
    if is_ur(t): return d.textlength(t, font=UF(s), direction="rtl", language="ur")
    return d.textlength(t, font=F(POP_B, int(s * 0.9)))
def udraw(d, xr, base, t, s, fill):
    """draw one run with its right edge at xr, baseline at base"""
    w = uw(d, t, s)
    if is_ur(t):
        d.text((xr - w, base), t, font=UF(s), fill=fill, direction="rtl", language="ur", anchor="ls")
    else:
        d.text((xr - w, base), t, font=F(POP_B, int(s * 0.9)), fill=fill, anchor="ls")
    return w
def urline(d, xr, base, text, s, fill, gap=0.28):
    """draw a mixed line right-to-left, word by word"""
    for w_, _ in tokens(text):
        xr -= udraw(d, xr, base, w_, s, fill) + s * gap
    return xr
def ulen(d, text, s, gap=0.28):
    ws = [w_ for w_, _ in tokens(text)]
    return sum(uw(d, w_, s) for w_ in ws) + s * gap * max(0, len(ws) - 1)
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

HI = [
    "एलिमेंटर में तबदीली महफ़ूज़ की, मगर लाइव पेज पुराना ही नज़र आ रहा है?",
    "घबराइए नहीं। आपकी तबदीली महफ़ूज़ है। बस आपकी साइट पेज की कई कॉपियाँ रखती है।",
    "तरतीब से ठीक कीजिए। एक। एलिमेंटर में टूल्स, फिर क्लियर फ़ाइल्स एंड डेटा।",
    "दो। अपने कैश प्लगइन या होस्ट का कैश साफ़ कीजिए।",
    "तीन। क्लाउडफ़्लेयर का कैश साफ़ कीजिए, सिर्फ़ वो पेज जो आपने बदले।",
    "चार। प्राइवेट विंडो में चेक कीजिए।",
    "हमेशा अंदर से बाहर की तरफ़ जाइए, ताकि कोई तह पुराना पेज दोबारा न रख ले। मुकम्मल गाइड टेक मेंडली डॉट कॉम पर। लिंक बायो में।",
]
UR = [
    "Elementor میں تبدیلی محفوظ کی، مگر لائیو پیج پرانا ہی نظر آ رہا ہے؟",
    "گھبرائیں نہیں۔ آپ کی تبدیلی محفوظ ہے۔ بس آپ کی سائٹ پیج کی کئی کاپیاں رکھتی ہے۔",
    "ترتیب سے ٹھیک کریں۔ ایک۔ Elementor میں Tools، پھر Clear Files and Data۔",
    "دو۔ اپنے کیش پلگ اِن یا ہوسٹ کا کیش صاف کریں۔",
    "تین۔ Cloudflare کیش صاف کریں، صرف وہ پیجز جو آپ نے بدلے۔",
    "چار۔ پرائیویٹ ونڈو میں چیک کریں۔",
    "ہمیشہ اندر سے باہر کی طرف جائیں، تاکہ کوئی تہہ پرانا پیج دوبارہ نہ رکھ لے۔ مکمل گائیڈ techmendly.com پر۔ لنک بائیو میں۔",
]
SPOKEN = HI
SHOWN = UR
_OLD = [
    "Saved a change in Elementor, but your live page still looks old?",
    "Don't panic. Your change is saved. Your site just keeps several copies of the page.",
    "Fix it in order. One. Elementor, Tools, Clear Files and Data.",
    "Two. Purge your cache plugin or host cache.",
    "Three. Purge Cloudflare, just the pages you changed.",
    "Four. Check in a private window.",
    "Always go inside out, so no layer caches the old page again. Full guide on Tech Mendly dot com. Link in bio.",
]
PAD = [0.25, 0.4, 1.0, 1.0, 1.3, 1.1, 0.5]
LABELS = ["مسئلہ", "ایسا کیوں ہوتا ہے", "مرحلہ ۱ از ۴", "مرحلہ ۲ از ۴", "مرحلہ ۳ از ۴", "مرحلہ ۴ از ۴", "خلاصہ"]
SR = 48000

# ------------------------------------------------------------------ voice
k = Kokoro("/home/claude/kokoro/kokoro-v1.0.onnx", "/home/claude/kokoro/voices-v1.0.bin")
voice = []
for i, text in enumerate(SPOKEN):
    audio, sr = k.create(text, voice="hm_omega", speed=1.05, lang="hi")
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

CLICKS = {2: [0.40, 0.70], 3: [0.55], 4: [0.33, 0.76]}

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

# ------------------------------------------------------------------ scenes
def scene_hook(d, lt, dur):
    f = lt / dur
    def card(y, title, head, hc, chiptxt, chipc, a):
        A = int(255 * a)
        d.rounded_rectangle((60, y, 1020, y + 340), radius=30, fill=(255, 255, 255, A), outline=BORDER + (A,), width=3)
        d.rounded_rectangle((60, y, 1020, y + 76), radius=30, fill=(222, 225, 232, A))
        d.rectangle((60, y + 40, 1020, y + 76), fill=(222, 225, 232, A))
        for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
            d.ellipse([92 + i * 38, y + 28, 110 + i * 38, y + 46], fill=c + (A,))
        d.text((250, y + 20), title, font=F(INTER, 30), fill=GREY + (A,))
        d.text((100, y + 118), head, font=F(POP_B, 66), fill=hc + (A,))
        d.text((100, y + 214), "Limited time offer. Order today.", font=F(INTER, 32), fill=GREY + (A,))
        cw = tw(d, chiptxt, F(INTER_B, 30)) + 56
        d.rounded_rectangle((100, y + 268, 100 + cw, y + 322), radius=27, fill=chipc + (A,))
        d.text((128, y + 276), chiptxt, font=F(INTER_B, 30), fill=(255, 255, 255, A))
    a1 = ease(f / 0.14)
    a2 = ease((f - 0.20) / 0.14)
    card(300, "Elementor editor", "Summer Sale: 50% OFF", (14, 130, 100), "Saved", GRN, a1)
    ra = ease((f - 0.40) / 0.1)
    cx, cy, r = 540, 740, 40
    d.arc([cx - r, cy - r, cx + r, cy + r], start=20 + lt * 220, end=300 + lt * 220, fill=GREY + (int(255 * ra),), width=9)
    card(820, "yoursite.com (live page)", "Summer Sale: 20% OFF", (170, 60, 70), "Still old", RED, a2)
    if f > 0.60:
        pa = ease((f - 0.60) / 0.12)
        uc = "پیج وہی۔ کاپی پرانی۔"; udraw(d, 540 + uw(d, uc, 56) / 2, 1250, uc, 56, RED + (int(255 * pa),))

LAYERS = [
    ("آپ کا براؤزر", "آپ کے ڈیوائس پر کاپی رکھتا ہے"),
    ("Cloudflare", "وزیٹرز کے قریب کاپی رکھتا ہے"),
    ("سرور یا پیج کیش", "بنا بنایا پیج محفوظ رکھتا ہے"),
    ("Elementor کیش اور فائلیں", "پہلے سے بنے ویجٹس اور CSS"),
    ("WordPress", "جہاں آپ کی تبدیلی محفوظ ہوئی"),
]
def scene_layers(d, lt, dur):
    f = lt / dur
    for i, (name, sub) in enumerate(LAYERS):
        y = 310 + i * 160
        a = ease((lt - 0.25 - i * 0.45) / 0.35)
        if a <= 0:
            continue
        A = int(255 * a)
        x_off = (1 - a) * 80
        d.rounded_rectangle((60 + x_off, y, 1020 + x_off, y + 120), radius=26, fill=(255, 255, 255, A), outline=BORDER + (A,), width=3)
        urline(d, 980 + x_off, y + 58, name, 34, NAVY + (A,))
        urline(d, 980 + x_off, y + 106, sub, 26, GREY + (A,))
        last = i == len(LAYERS) - 1
        tag = "محفوظ" if last else "پرانی کاپی"
        tc = GRN if last else (230, 150, 20)
        wv = uw(d, tag, 30) + 44
        d.rounded_rectangle((80 + x_off, y + 34, 80 + x_off + wv, y + 86), radius=26, fill=tc + (int(60 * a),), outline=tc + (A,), width=3)
        udraw(d, 80 + x_off + wv - 22, y + 76, tag, 30, tc + (A,))
        if i < len(LAYERS) - 1:
            aa = ease((lt - 0.45 - i * 0.45) / 0.3)
            if aa > 0:
                cx = 540
                d.polygon([(cx - 16, y + 128), (cx + 16, y + 128), (cx, y + 152)], fill=GREY + (int(200 * aa),))

def scene_elementor(d, lt, dur):
    f = lt / dur
    items = ["Dashboard", "Posts", "Media", "Pages", "Elementor", "Templates", "Appearance", "Plugins"]
    wp_base(d, items, "Elementor" if f > 0.20 else "Dashboard")
    flyout = 0.22 <= f < 0.42
    on_tools = f >= 0.40
    if not on_tools:
        d.text((310, 395), "Dashboard", font=F(INTER_B, 52), fill=(30, 30, 30))
        for i in range(3):
            y = 500 + i * 190
            d.rounded_rectangle((310, y, 1010, y + 160), radius=14, fill=(246, 247, 248), outline=(225, 228, 232), width=2)
            d.rounded_rectangle((335, y + 28, 335 + 260 + i * 60, y + 52), radius=8, fill=(210, 214, 220))
            d.rounded_rectangle((335, y + 80, 335 + 480, y + 100), radius=8, fill=(228, 231, 235))
    else:
        d.text((310, 395), "Tools", font=F(INTER_B, 52), fill=(30, 30, 30))
        x = 310
        for t_, act in [("General", True), ("Replace URL", False), ("Version Control", False)]:
            fn = F(INTER_B if act else INTER, 25)
            w = tw(d, t_, fn) + 34
            d.rectangle((x, 480, x + w, 530), fill=(255, 255, 255) if act else (232, 232, 234), outline=BORDER, width=2)
            d.text((x + 17, 491), t_, font=fn, fill=(30, 30, 30) if act else GREY)
            x += w + 8
        d.text((310, 575), "Elementor Cache", font=F(INTER_B, 40), fill=(30, 30, 30))
        for i, ln in enumerate(["Elementor saves your design as CSS", "files. If they are out of date, the live", "page can still show the old version."]):
            d.text((310, 645 + i * 44), ln, font=F(INTER, 29), fill=GREY)
    if flyout:
        fa = ease((f - 0.22) / 0.06)
        d.rounded_rectangle((270, 693, 560, 953), radius=10, fill=(50, 55, 60, int(255 * fa)))
        for i, name in enumerate(["Settings", "Role Manager", "Tools", "System Info"]):
            y = 707 + i * 60
            hov = name == "Tools" and f > 0.34
            if hov:
                d.rectangle((270, y - 2, 560, y + 58), fill=(0, 115, 170, int(255 * fa)))
            d.text((298, y + 10), name, font=F(INTER_B if hov else INTER, 28), fill=(255, 255, 255, int(255 * fa)))
    bx = (310, 830, 800, 915)
    pressed = 0.70 <= f < 0.74
    if on_tools:
        ring(d, bx, ease((f - 0.45) / 0.15) * (1 if f < 0.74 else max(0.0, 1 - (f - 0.74) / 0.05)))
        button(d, bx, "Clear Files & Data", BLUE, (255, 255, 255), F(INTER_B, 38), pressed)
    ta = ease((f - 0.74) / 0.06)
    if on_tools:
        toast(d, 310, 1010, 1000, 1110, "Cache cleared", ta)
        if ta > 0:
            d.text((310, 1170), "Rebuilds on the next visit.", font=F(INTER, 28), fill=(120, 125, 130, int(255 * ta)))
    pts = [(0.0, 800, 560), (0.08, 790, 590), (0.20, 150, 722), (0.28, 330, 740), (0.38, 360, 857), (0.46, 520, 870), (0.68, 560, 876), (1.0, 560, 876)]
    cx, cy = path_pos(f, pts)
    for fc in CLICKS[2]:
        ripple(d, cx, cy, f, fc)
    cursor(d, cx - 6, cy - 4)

def scene_cache(d, lt, dur):
    f = lt / dur
    items = ["Dashboard", "Posts", "Pages", "Elementor", "LiteSpeed", "Appearance", "Plugins", "Settings"]
    wp_base(d, items, "LiteSpeed")
    d.text((310, 395), "Toolbox", font=F(INTER_B, 52), fill=(30, 30, 30))
    x = 310
    for t_, act in [("Purge", True), ("Import / Export", False), ("Heartbeat", False)]:
        fn = F(INTER_B if act else INTER, 25)
        w = tw(d, t_, fn) + 34
        d.rectangle((x, 480, x + w, 530), fill=(255, 255, 255) if act else (232, 232, 234), outline=BORDER, width=2)
        d.text((x + 17, 491), t_, font=fn, fill=(30, 30, 30) if act else GREY)
        x += w + 8
    fb = F(INTER_B, 32)
    button(d, (310, 575, 690, 645), "Purge Front Page", (255, 255, 255), BLUE, fb, outline=BLUE)
    button(d, (310, 665, 690, 735), "Purge Pages", (255, 255, 255), BLUE, fb, outline=BLUE)
    pb = (310, 755, 690, 825)
    pressed = 0.55 <= f < 0.60
    ring(d, pb, ease((f - 0.30) / 0.15) * (1 if f < 0.60 else max(0.0, 1 - (f - 0.60) / 0.05)))
    button(d, pb, "Purge All", BLUE, (255, 255, 255), fb, pressed)
    d.text((310, 845), "Clears the stored copy of every page.", font=F(INTER, 27), fill=GREY)
    ta = ease((f - 0.60) / 0.06)
    toast(d, 310, 905, 1000, 1000, "All caches purged", ta)
    d.text((310, 1060), "Not using LiteSpeed?", font=F(INTER_B, 28), fill=NAVY)
    chip(d, 310, 1110, "WP Rocket > Clear and preload cache", F(INTER_B, 26), (232, 236, 242), NAVY)
    chip(d, 310, 1180, "Host panel > Purge cache", F(INTER_B, 26), (232, 236, 242), NAVY)
    pts = [(0.0, 800, 560), (0.10, 780, 600), (0.50, 560, 800), (1.0, 560, 800)]
    cx, cy = path_pos(f, pts)
    ripple(d, cx, cy, f, CLICKS[3][0])
    cursor(d, cx - 6, cy - 4)

def scene_cloudflare(d, lt, dur):
    f = lt / dur
    browser_base(d, "dash.cloudflare.com", False, "Dashboard")
    d.rectangle((41, 420, 270, 1328), fill=(248, 248, 249))
    d.rounded_rectangle((42, 1200, 270, 1329), radius=28, fill=(248, 248, 249))
    d.line((270, 420, 270, 1328), fill=(225, 228, 232), width=2)
    for i, m in enumerate(["Overview", "DNS", "SSL/TLS", "Caching", "Rules"]):
        yy = 460 + i * 78
        if m == "Caching":
            d.rectangle((42, yy - 14, 270, yy + 54), fill=(253, 240, 228))
            d.rectangle((42, yy - 14, 50, yy + 54), fill=ORANGE)
            d.text((70, yy), m, font=F(INTER_B, 28), fill=ORANGE)
        else:
            d.text((70, yy), m, font=F(INTER, 28), fill=GREY)
    d.text((310, 460), "Caching", font=F(INTER_B, 52), fill=(30, 30, 30))
    d.text((310, 540), "Configuration", font=F(INTER, 30), fill=GREY)
    d.text((310, 620), "Purge Cache", font=F(INTER_B, 38), fill=(30, 30, 30))
    d.text((310, 676), "Clear stored files so a fresh copy is fetched.", font=F(INTER, 27), fill=GREY)
    b1 = (310, 735, 610, 805)
    b2 = (630, 735, 890, 805)
    c_click = CLICKS[4][0]
    p_click = CLICKS[4][1]
    button(d, b1, "Purge Everything", (255, 255, 255), RED, F(INTER_B, 28), outline=RED)
    sel = f >= c_click
    ring(d, b2, ease((f - 0.15) / 0.12) * (1 if f < c_click + 0.02 else 0.0))
    button(d, b2, "Custom Purge", ORANGE, (255, 255, 255), F(INTER_B, 28), c_click <= f < c_click + 0.04)
    if sel:
        pa = ease((f - c_click) / 0.05)
        d.rounded_rectangle((310, 835, 1010, 1060), radius=14, fill=(250, 250, 251, int(255 * pa)), outline=BORDER + (int(255 * pa),), width=2)
        d.text((335, 855), "URLs to purge", font=F(INTER_B, 27), fill=NAVY + (int(255 * pa),))
        d.rounded_rectangle((335, 905, 985, 975), radius=10, fill=(255, 255, 255, int(255 * pa)), outline=BORDER + (int(255 * pa),), width=2)
        url = "https://yoursite.com/summer-sale/"
        n = int(max(0.0, (f - (c_click + 0.03)) / 0.26) * len(url))
        d.text((355, 920), url[:n], font=F(INTER, 28), fill=NAVY + (int(255 * pa),))
        pb = (335, 990, 505, 1045)
        pr = p_click <= f < p_click + 0.04
        ring(d, pb, ease((f - 0.62) / 0.1) * (1 if f < p_click + 0.02 else 0.0))
        button(d, pb, "Purge", ORANGE, (255, 255, 255), F(INTER_B, 28), pr)
    ta = ease((f - p_click - 0.03) / 0.06)
    toast(d, 310, 1100, 1000, 1195, "Purge successful", ta)
    if ta > 0:
        d.text((310, 1235), "Only the pages you changed.", font=F(INTER, 28), fill=(120, 125, 130, int(255 * ta)))
    pts = [(0.0, 820, 520), (0.08, 800, 600), (0.30, 760, 780), (0.40, 790, 830), (0.55, 700, 940), (0.72, 420, 1020), (1.0, 420, 1020)]
    cx, cy = path_pos(f, pts)
    ripple(d, cx, cy, f, c_click)
    ripple(d, cx, cy, f, p_click)
    cursor(d, cx - 6, cy - 4)

def scene_private(d, lt, dur):
    f = lt / dur
    browser_base(d, "", True, "New Incognito Tab")
    url = "yoursite.com/summer-sale/"
    n = int(ease(f / 0.40) * len(url))
    d.text((100, 358), url[:n], font=F(INTER, 30), fill=(230, 232, 236))
    if f < 0.40:
        bx = 100 + tw(d, url[:n], F(INTER, 30)) + 2
        d.line((bx, 366, bx, 400), fill=(230, 232, 236), width=3)
    pa = ease((f - 0.46) / 0.12)
    if pa > 0:
        A = int(255 * pa)
        d.text((100, 500), "Summer Sale: 50% OFF", font=F(POP_B, 70), fill=(14, 130, 100, A))
        d.text((100, 610), "Limited time offer. Order today.", font=F(INTER, 34), fill=GREY + (A,))
        cw = tw(d, "The new version is live", F(INTER_B, 32)) + 120
        d.rounded_rectangle((100, 700, 100 + cw, 790), radius=45, fill=(230, 247, 238, A), outline=GRN + (A,), width=3)
        d.ellipse([122, 718, 122 + 54, 718 + 54], fill=GRN + (A,))
        d.line([(136, 745), (146, 756), (163, 735)], fill=(255, 255, 255, A), width=7)
        d.text((198, 727), "The new version is live", font=F(INTER_B, 32), fill=(25, 100, 60, A))
    ka = ease((f - 0.30) / 0.12)
    if ka > 0:
        A = int(255 * ka)
        d.text((100, 960), "Open a private window", font=F(POP_B, 34), fill=NAVY + (A,))
        x = 100
        for lab in ["Ctrl", "Shift", "N"]:
            x += keycap(d, x, 1020, lab)
        d.text((100, 1140), "Or hard reload", font=F(POP_B, 34), fill=NAVY + (A,))
        x = 100
        for lab in ["Ctrl", "Shift", "R"]:
            x += keycap(d, x, 1200, lab)
        x += 20
        d.text((x, 1215), "Mac: Cmd + Shift + R", font=F(INTER, 28), fill=GREY + (A,))

def scene_end(d, lt, dur):
    f = lt / dur
    a = ease(lt / 0.5)
    A = int(255 * a)
    badge(d, 540, 400, 170, TEAL, (255, 255, 255))
    ctext(d, 515, "TechMendly", F(POP_B, 96), NAVY)
    uc = "ٹیکنالوجی آسان زبان میں"; udraw(d, 540 + uw(d, uc, 48) / 2, 700, uc, 48, TEAL)
    rows = ["Elementor فائلیں", "کیش پلگ اِن یا ہوسٹ", "Cloudflare", "پرائیویٹ ونڈو"]
    for i, r in enumerate(rows):
        y = 740 + i * 96
        ra = ease((lt - 0.4 - i * 0.5) / 0.3)
        if ra <= 0:
            continue
        RA = int(255 * ra)
        d.rounded_rectangle((200, y, 880, y + 78), radius=39, fill=(255, 255, 255, RA), outline=BORDER + (RA,), width=3)
        d.ellipse([218, y + 11, 218 + 56, y + 11 + 56], fill=GRN + (RA,))
        d.line([(231, y + 40), (242, y + 51), (260, y + 28)], fill=(255, 255, 255, RA), width=7)
        urline(d, 850, y + 56, "۱۲۳۴"[i] + ".  " + r, 36, NAVY + (RA,))
    pa = ease((lt - 2.4) / 0.4)
    if pa > 0:
        pulse = 1 + 0.025 * math.sin(lt * 6)
        pw, ph = 760 * pulse, 100 * pulse
        cx, cy = 540, 1215
        d.rounded_rectangle((cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2), radius=50, fill=NAVY + (int(255 * pa),))
        uc = "مکمل گائیڈ: techmendly.com"; urline(d, 540 + ulen(d, uc, 44) / 2, cy + 18, uc, 44, YEL + (int(255 * pa),))

SCENES = [scene_hook, scene_layers, scene_elementor, scene_cache, scene_cloudflare, scene_private, scene_end]

def header(d, si):
    if si == 6:
        return
    lw = ulen(d, LABELS[si], 42)
    d.rounded_rectangle((60, 150, 60 + lw + 64, 230), radius=40, fill=NAVY)
    urline(d, 60 + 32 + lw, 205, LABELS[si], 42, (255, 255, 255))
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
            fs = 46
            sp = fs * 0.28
            lines, cl, idx = [], 0, []
            cur = []
            toks = tokens(SHOWN[i])
            for kk, (w_, _ix) in enumerate(toks):
                ww = uw(d, w_, fs)
                need = ww + (sp if cur else 0)
                if cl + need <= 880:
                    cur.append(kk); cl += need
                else:
                    lines.append(cur); cur = [kk]; cl = ww
            lines.append(cur)
            LH = 116
            top = 1330
            d.rounded_rectangle((60, top, 1020, top + len(lines) * LH + 40), radius=20, fill=NAVY)
            for li, ix in enumerate(lines):
                base = top + 20 + li * LH + 78
                xr = 540 + (sum(uw(d, toks[k_][0], fs) for k_ in ix) + sp * (len(ix) - 1)) / 2
                for kk in ix:
                    xr -= udraw(d, xr, base, toks[kk][0], fs, YEL if curw in toks[kk][1] else (255, 255, 255)) + sp
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
    marks = {"hook": T(0, 0.8), "layers": T(1, 0.85), "el_fly": T(2, 0.33), "el_tools": T(2, 0.58), "el_done": T(2, 0.92),
             "cache": T(3, 0.85), "cf_type": T(4, 0.55), "cf_done": T(4, 0.92), "private": T(5, 0.9), "end": T(6, 0.85)}
    for name, tt in marks.items():
        frame(min(tt, TOTAL - 0.05)).save(f"{WORK}/p_{name}.png")

main()
