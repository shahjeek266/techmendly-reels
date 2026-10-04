#!/usr/bin/env python3
"""TechMendly Reel renderer (data-driven). Usage: python3 render_spec.py specs/<id>.json
Writes reels/<id>.mp4, covers/<id>-cover.png, captions/<id>.txt and a contact sheet in /tmp/<id>_check/.
Scene types: hook, myth_fact, steps, compare, stat, tip, outro. Themes: dark, light, teal."""
import json, math, os, re, subprocess, sys, wave
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter

W, H, FPS, SR = 1080, 1920, 30, 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KDIR = os.environ.get("KOKORO_DIR", os.path.expanduser("~/kokoro"))
FD = "/usr/share/fonts/truetype/google-fonts/"
POP_B, POP_M = FD + "Poppins-Bold.ttf", FD + "Poppins-Medium.ttf"
INTER_B = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_fc = {}
def F(p, s):
    s = int(s)
    if (p, s) not in _fc:
        try: _fc[(p, s)] = ImageFont.truetype(p, s)
        except Exception: _fc[(p, s)] = ImageFont.truetype(FALLBACK, s)
    return _fc[(p, s)]

YEL = (255, 214, 10); RED = (232, 84, 84); GRN = (52, 199, 120); TEAL = (94, 234, 212); TEALD = (14, 140, 110)
THEMES = {
    "dark":  dict(bg1=(10, 16, 32), bg2=(22, 34, 64), fg=(255, 255, 255), mute=(150, 165, 195), card=(26, 38, 70), cardline=(52, 70, 112), acc=TEAL, pill=(255, 255, 255), pillfg=(10, 16, 32), cap=(0, 0, 0)),
    "light": dict(bg1=(244, 245, 247), bg2=(226, 232, 240), fg=(15, 23, 42), mute=(100, 110, 125), card=(255, 255, 255), cardline=(205, 212, 222), acc=TEALD, pill=(15, 23, 42), pillfg=(255, 255, 255), cap=(15, 23, 42)),
    "teal":  dict(bg1=(6, 78, 70), bg2=(10, 38, 52), fg=(255, 255, 255), mute=(170, 220, 212), card=(10, 60, 62), cardline=(40, 130, 120), acc=YEL, pill=(255, 255, 255), pillfg=(6, 50, 50), cap=(4, 24, 30)),
}

def ease(t): t = max(0., min(1., t)); return 1 - (1 - t) ** 3
def pop(t):
    t = max(0., min(1., t))
    return 1 + 2.2 * (t - 1) ** 3 + 1.2 * (t - 1) ** 2 if t < 1 else 1.0
def tw(d, t, f): return d.textlength(t, font=f)
def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if tw(d, t, f) <= maxw or not cur: cur = t
        else: out.append(cur); cur = w
    if cur: out.append(cur)
    return out
def col(c, a): return tuple(c[:3]) + (int(255 * max(0, min(1, a))),)

def mark(d, cx, cy, size, navy, tl):
    s = size / 43.0; ox = cx - 30 * s; oy = cy - 30.5 * s
    P = lambda pts: [(ox + x * s, oy + y * s) for x, y in pts]
    d.polygon(P([(9, 15), (23, 15), (34.5, 26.5), (9, 26.5)]), fill=navy)
    d.polygon(P([(34.5, 26.5), (34.5, 52), (23, 52), (23, 38)]), fill=navy)
    d.polygon(P([(32, 9), (51, 9), (51, 27.5), (42, 27.5), (42, 18), (32, 18)]), fill=tl)

def text_block(d, lines, f, cx, y, fill, lh, a=1.0, hl=None, hlcol=None):
    for i, ln in enumerate(lines):
        words = ln.split(); x = cx - tw(d, ln, f) / 2
        for w in words:
            c = hlcol if (hl and re.sub(r"\W", "", w.lower()) in hl) else fill
            d.text((x, y + i * lh), w, font=f, fill=col(c, a)); x += tw(d, w + " ", f)
    return y + len(lines) * lh

# ------------------------------------------------------------------ scenes
def hl_set(s): return set(re.sub(r"\W", "", w.lower()) for w in s.get("hl", []))

def sc_hook(d, th, s, f, lt):
    a = ease(f / 0.15)
    sz = s.get("size", 120); ft = F(POP_B, sz * (0.9 + 0.1 * min(1, pop(f / 0.25))))
    lines = wrap(d, s["text"], ft, 940)
    y = 480
    text_block(d, lines, ft, W / 2, y, th["fg"], int(sz * 1.2), a, hl_set(s), th["acc"])
    if s.get("sub"):
        sa = ease((f - 0.35) / 0.2)
        sf_ = F(POP_M, 50)
        text_block(d, wrap(d, s["sub"], sf_, 880), sf_, W / 2, y + len(lines) * int(sz * 1.2) + 50 + 20 * (1 - sa), th["mute"], 66, sa)

def sc_myth_fact(d, th, s, f, lt):
    for i, (tag, key, c, f0) in enumerate([("MYTH", "myth", RED, 0.05), ("FACT", "fact", GRN, 0.45)]):
        a = ease((f - f0) / 0.15); sl = (1 - a) * 80
        y = 400 + i * 540 + sl
        d.rounded_rectangle((70, y, 1010, y + 470), radius=44, fill=col(th["card"], a), outline=col(c, a), width=5)
        d.rounded_rectangle((110, y + 36, 110 + 40 + tw(d, tag, F(POP_B, 40)), y + 106), radius=35, fill=col(c, a))
        d.text((130, y + 46), tag, font=F(POP_B, 40), fill=col((255, 255, 255), a))
        fb = F(POP_B, 58 if len(s[key]) < 70 else 50)
        text_block(d, wrap(d, s[key], fb, 840), fb, W / 2, y + 150, th["fg"], 78 if len(s[key]) < 70 else 68, a, hl_set(s), th["acc"])
        if key == "myth" and f > 0.45:  # strike-through
            u = ease((f - 0.45) / 0.12)
            d.line((110, y + 235, 110 + 860 * u, y + 235), fill=col(RED, 0.9), width=8)

def sc_steps(d, th, s, f, lt):
    ft = F(POP_B, 66)
    if s.get("title"):
        text_block(d, wrap(d, s["title"], ft, 900), ft, W / 2, 330, th["fg"], 80, ease(f / 0.12))
    items = s["items"]; n = len(items); top = 520; hgt = min(230, 760 // n)
    for i, it in enumerate(items):
        f0 = 0.15 + 0.8 * i / n; a = ease((f - f0) / 0.14); sl = (1 - a) * 120
        y = top + i * (hgt + 24)
        d.rounded_rectangle((70 + sl, y, 1010 + sl, y + hgt), radius=38, fill=col(th["card"], a), outline=col(th["cardline"], a), width=4)
        r = 52; cy = y + hgt / 2
        d.ellipse((110 + sl, cy - r, 110 + sl + 2 * r, cy + r), fill=col(th["acc"], a))
        d.text((110 + sl + r, cy), str(i + 1), font=F(POP_B, 56), fill=col(th["bg1"], a), anchor="mm")
        fb = F(POP_B, 50); lines = wrap(d, it, fb, 700)
        text_block(d, [l for l in lines[:3]], fb, 0, 0, (0, 0, 0), 0, 0)  # measure only
        yy = cy - len(lines) * 30
        for li, ln in enumerate(lines):
            d.text((250 + sl, yy + li * 60), ln, font=fb, fill=col(th["fg"], a))

def sc_compare(d, th, s, f, lt):
    ft = F(POP_B, 56)
    for i, (key, c, sym) in enumerate([("left", RED, "x"), ("right", GRN, "ok")]):
        side = s[key]; f0 = 0.08 + i * 0.4; a = ease((f - f0) / 0.15); sl = (1 - a) * 60
        y = 300 + i * 500 + sl
        d.rounded_rectangle((70, y, 1010, y + 450), radius=44, fill=col(th["card"], a), outline=col(c, a), width=5)
        cx0, cy0 = 150, y + 85
        d.ellipse((cx0 - 40, cy0 - 40, cx0 + 40, cy0 + 40), fill=col(c, a))
        if sym == "x":
            d.line((cx0 - 15, cy0 - 15, cx0 + 15, cy0 + 15), fill=col((255, 255, 255), a), width=8); d.line((cx0 + 15, cy0 - 15, cx0 - 15, cy0 + 15), fill=col((255, 255, 255), a), width=8)
        else:
            d.line([(cx0 - 17, cy0 + 2), (cx0 - 4, cy0 + 15), (cx0 + 18, cy0 - 14)], fill=col((255, 255, 255), a), width=8)
        d.text((220, y + 52), side["title"], font=F(POP_B, 50), fill=col(c, a))
        fb = F(POP_B, 54 if len(side["text"]) < 60 else 46)
        text_block(d, wrap(d, side["text"], fb, 820), fb, W / 2, y + 170, th["fg"], 70 if len(side["text"]) < 60 else 62, a, hl_set(s), th["acc"])

def sc_stat(d, th, s, f, lt):
    sc = pop(f / 0.3); fb = F(POP_B, 230 * (0.6 + 0.4 * sc))
    a = ease(f / 0.12)
    d.text((W / 2, 640), s["big"], font=fb, fill=col(th["acc"], a), anchor="mm")
    fl = F(POP_B, 60)
    text_block(d, wrap(d, s["label"], fl, 880), fl, W / 2, 820, th["fg"], 80, ease((f - 0.25) / 0.2), hl_set(s), th["acc"])
    if s.get("sub"):
        fs = F(POP_M, 44)
        text_block(d, wrap(d, s["sub"], fs, 860), fs, W / 2, 1090, th["mute"], 60, ease((f - 0.55) / 0.2))

def sc_tip(d, th, s, f, lt):
    a = ease(f / 0.12)
    ft = F(POP_B, 40); lab = s.get("chip", "TIP")
    d.rounded_rectangle((70, 380, 70 + tw(d, lab, ft) + 70, 460), radius=40, fill=col(th["acc"], a))
    d.text((105, 394), lab, font=ft, fill=col(th["bg1"], a))
    fb = F(POP_B, 82)
    y = text_block(d, wrap(d, s["title"], fb, 920), fb, W / 2, 520 + 30 * (1 - a), th["fg"], 100, a, hl_set(s), th["acc"])
    if s.get("code"):
        ba = ease((f - 0.3) / 0.15); bf = F(INTER_B, 40); lines = wrap(d, s["code"], bf, 800)
        hh = 60 + len(lines) * 58
        d.rounded_rectangle((70, y + 50, 1010, y + 50 + hh), radius=30, fill=col((8, 12, 24) if th is not THEMES["light"] else (15, 23, 42), ba), outline=col(th["acc"], ba), width=3)
        for li, ln in enumerate(lines): d.text((110, y + 80 + li * 58), ln, font=bf, fill=col((235, 245, 255), ba))
        y += hh + 50
    if s.get("body"):
        fm = F(POP_M, 46)
        text_block(d, wrap(d, s["body"], fm, 880), fm, W / 2, y + 60, th["mute"], 64, ease((f - 0.5) / 0.2))

def sc_outro(d, th, s, f, lt):
    a = ease(f / 0.15); sc = pop(f / 0.4)
    mark(d, W / 2, 620, 190 * sc, th["fg"] if th is THEMES["dark"] or th is THEMES["teal"] else (15, 23, 42), TEAL if th is not THEMES["light"] else TEALD)
    d.text((W / 2, 790), "TechMendly", font=F(POP_B, 74), fill=col(th["fg"], a), anchor="mm")
    fb = F(POP_B, 62)
    text_block(d, wrap(d, s.get("text", "Follow @techmendly"), fb, 900), fb, W / 2, 900, th["acc"], 80, ease((f - 0.2) / 0.2))
    if s.get("sub"):
        fs = F(POP_M, 44); text_block(d, wrap(d, s["sub"], fs, 880), fs, W / 2, 1060, th["mute"], 60, ease((f - 0.4) / 0.2))

SCENES = dict(hook=sc_hook, myth_fact=sc_myth_fact, steps=sc_steps, compare=sc_compare, stat=sc_stat, tip=sc_tip, outro=sc_outro)

# ------------------------------------------------------------------ build
def main(spec_path):
    spec = json.load(open(spec_path)); rid = spec["id"]; th = THEMES[spec.get("theme", "dark")]
    work = f"/tmp/{rid}_work"; os.makedirs(work, exist_ok=True)
    scenes = spec["scenes"]
    spoken = [s["say"].replace("TechMendly", "Tech Mendly") for s in scenes]
    shown = [s.get("shown", s["say"]) for s in scenes]
    from kokoro_onnx import Kokoro
    k = Kokoro(f"{KDIR}/kokoro-v1.0.onnx", f"{KDIR}/voices-v1.0.bin")
    voice = []
    for i, t in enumerate(spoken):
        a, sr = k.create(t, voice="am_michael", speed=1.05, lang="en-us")
        sf.write(f"{work}/l{i}_raw.wav", a, sr)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{work}/l{i}_raw.wav", "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", f"{work}/l{i}.wav"], check=True)
        with wave.open(f"{work}/l{i}.wav") as w: voice.append(np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768)
    SS, SE, TL, cur = [], [], [], 0.0
    for i, v in enumerate(voice):
        dur = len(v) / SR; lead = 0.25 if i == 0 else 0.1
        SS.append(cur); TL.append((cur + lead, cur + lead + dur)); cur += lead + dur + 0.3 + scenes[i].get("pad", 0.4); SE.append(cur)
    TOTAL = SE[-1] + 0.4; SE[-1] = TOTAL
    print("total", round(TOTAL, 1), "s")
    assert 18 <= TOTAL <= 58, f"Reel length {TOTAL:.1f}s out of range (aim 25-45s)"

    # audio: voice + soft pad + whoosh at each scene start
    n = int(TOTAL * SR); vt = np.zeros(n, dtype=np.float32)
    for (s_, e_), v in zip(TL, voice): vt[int(s_ * SR):int(s_ * SR) + len(v)] += v
    vt = vt / (np.max(np.abs(vt)) or 1) * 0.85
    t = np.arange(n) / SR; mus = np.zeros(n); chords = [[220, 261.63, 329.63], [174.61, 220, 261.63], [261.63, 329.63, 392], [196, 246.94, 293.66]]
    seg = TOTAL / len(chords)
    for i, ch in enumerate(chords):
        a, b = int(i * seg * SR), int(min(n, (i + 1) * seg * SR)); tt = t[a:b]
        env = np.minimum(1, (tt - tt[0]) / 0.5) * np.minimum(1, (tt[-1] - tt) / 0.5)
        for fq in ch: mus[a:b] += 0.016 * np.sin(2 * np.pi * fq * tt) * env
    mus *= np.minimum(1, (TOTAL - t) / 1.0)
    rng = np.random.default_rng(7); fx = np.zeros(n)
    for i in range(1, len(SS)):
        a = int((SS[i] - 0.05) * SR); m = int(0.22 * SR); tt = np.arange(m) / SR
        noise = rng.standard_normal(m); env = np.sin(np.pi * np.minimum(1, tt / 0.22)) ** 2
        sm = np.convolve(noise, np.ones(40) / 40, mode="same")
        fx[a:a + m] += 0.10 * sm * env
    mix = np.clip(vt + mus + fx, -0.95, 0.95)
    pcm = (np.stack([mix, mix], 1) * 32767).astype(np.int16)
    with wave.open(f"{work}/mix.wav", "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())

    # background (static gradient + drifting dots)
    yy = np.linspace(0, 1, H)[:, None, None]
    grad = (np.array(th["bg1"])[None, None, :] * (1 - yy) + np.array(th["bg2"])[None, None, :] * yy).repeat(W, 1).astype(np.uint8)
    BGI = Image.fromarray(grad).convert("RGBA")
    dots = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(3, 9), rng.uniform(15, 40)) for _ in range(34)]

    def header(d, si):
        lab = scenes[si].get("tag") or ""
        if lab and scenes[si]["type"] != "outro":
            ft = F(POP_B, 36); d.rounded_rectangle((60, 150, 60 + tw(d, lab, ft) + 64, 226), radius=38, fill=th["pill"])
            d.text((92, 162), lab, font=ft, fill=th["pillfg"])
        mark(d, 985, 188, 62, th["fg"], TEAL if spec.get("theme", "dark") != "light" else TEALD)
        d.text((940 - tw(d, "@techmendly", F(POP_M, 32)), 172), "@techmendly", font=F(POP_M, 32), fill=th["mute"])

    def captions(d, tm):
        for i, (s_, e_) in enumerate(TL):
            if s_ - 0.05 <= tm <= e_ + 0.3:
                words = shown[i].split(); wts = [len(w) + 1 for w in words]; tot = sum(wts); acc = 0; cw = len(words) - 1
                prog = (tm - s_) / (e_ - s_)
                for kk, wt in enumerate(wts):
                    if prog <= (acc + wt) / tot: cw = kk; break
                    acc += wt
                f = F(POP_B, 52); lines, cl, idx = [], "", []
                for kk, w_ in enumerate(words):
                    test = (cl + " " + w_).strip()
                    if tw(d, test, f) <= 900: cl = test; idx.append(kk)
                    else: lines.append((cl, idx)); cl = w_; idx = [kk]
                lines.append((cl, idx)); top = 1350
                d.rounded_rectangle((60, top, 1020, top + len(lines) * 74 + 44), radius=24, fill=col(th["cap"], 0.88))
                for li, (ln, ix) in enumerate(lines):
                    x = W / 2 - tw(d, ln, f) / 2
                    for kk in ix:
                        d.text((x, top + 22 + li * 74), words[kk], font=f, fill=YEL if kk == cw else (255, 255, 255)); x += tw(d, words[kk] + " ", f)
                return

    def frame(tm):
        img = BGI.copy(); dd = ImageDraw.Draw(img)
        for (x, y0, r, sp) in dots:
            y = (y0 - tm * sp) % H; dd.ellipse((x - r, y - r, x + r, y + r), fill=col(th["acc"], 0.06))
        si = max(i for i in range(len(SS)) if SS[i] <= tm) if tm < TOTAL else len(SS) - 1
        lt = tm - SS[si]; dur = SE[si] - SS[si]; f = lt / dur
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
        SCENES[scenes[si]["type"]](d, th, scenes[si], f, lt)
        fa = min(ease(lt / 0.2), 1 - ease((lt - (dur - 0.2)) / 0.2)) if si < len(SS) - 1 else ease(lt / 0.2)
        layer.putalpha(ImageChops.multiply(layer.getchannel("A"), Image.new("L", (W, H), int(255 * max(0, min(1, fa))))))
        img = Image.alpha_composite(img, layer)
        top = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dt = ImageDraw.Draw(top)
        header(dt, si); captions(dt, tm)
        dt.rectangle((0, 0, int(W * tm / TOTAL), 10), fill=th["acc"])
        return Image.alpha_composite(img, top).convert("RGB")

    out = f"{ROOT}/reels/{rid}.mp4"; os.makedirs(f"{ROOT}/reels", exist_ok=True)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", f"{work}/mix.wav",
        "-c:v", "libx264", "-profile:v", "high", "-level", "4.0", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "19", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(int(TOTAL * FPS)): p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()

    chk = f"/tmp/{rid}_check"; os.makedirs(chk, exist_ok=True); ims = []
    for i in range(len(SS)):
        im = frame(min(SS[i] + (SE[i] - SS[i]) * 0.85, TOTAL - 0.05)); im.save(f"{chk}/s{i}.png"); ims.append(im.resize((360, 640)))
    sheet = Image.new("RGB", (len(ims) * 370, 640), (90, 90, 90))
    for i, im in enumerate(ims): sheet.paste(im, (i * 370, 0))
    sheet.save(f"{chk}/sheet.png")

    # cover + caption
    cv = spec["cover"]; ci = Image.new("RGB", (W, H), th["bg1"]); cd = ImageDraw.Draw(ci)
    ci = Image.alpha_composite(BGI, Image.new("RGBA", (W, H), (0, 0, 0, 0))).convert("RGB"); cd = ImageDraw.Draw(ci)
    dk = spec.get("theme", "dark") != "light"
    mark(cd, 540, 600, 130, th["fg"] if dk else (15, 23, 42), TEAL if dk else TEALD)
    cd.text((540, 710), "TechMendly", font=F(POP_B, 44), fill=th["fg"], anchor="mm")
    y = 820; fb = F(POP_B, 112)
    for i, ln in enumerate(cv["lines"]):
        cd.text((540, y), ln, font=fb, fill=th["acc"] if i in cv.get("hl", []) else th["fg"], anchor="mt"); y += 145
    sf_ = F(POP_B, 46); w = cd.textlength(cv["pill"], font=sf_) + 90
    cd.rounded_rectangle((540 - w / 2, y + 50, 540 + w / 2, y + 150), radius=50, fill=YEL); cd.text((540, y + 100), cv["pill"], font=sf_, fill=(15, 23, 42), anchor="mm")
    os.makedirs(f"{ROOT}/covers", exist_ok=True); ci.save(f"{ROOT}/covers/{rid}-cover.png")
    os.makedirs(f"{ROOT}/captions", exist_ok=True); open(f"{ROOT}/captions/{rid}.txt", "w").write(spec["caption"].strip() + "\n")
    print("done", out)

if __name__ == "__main__":
    main(sys.argv[1])
