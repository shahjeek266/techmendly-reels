import re
base = open('/home/claude/render_tm_reel3.py').read()
HEAD = base[:base.index('# ------------------------------------------------------------------ prompt reel scenes')]
TAIL = base[base.index('def header(d, si):'):]
MAIN_MARKS = re.search(r'    marks = \{.*\}\n', TAIL).group(0)

def build(out_py, spoken, shown_last, pad, labels, clicks, scenes_code, scene_list, marks, out_mp4, work):
    h = HEAD
    a = h.index('SPOKEN = ['); b = h.index('SR = 48000')
    blk = 'SPOKEN = %r\nSHOWN = SPOKEN[:-1] + [%r]\nPAD = %r\nLABELS = %r\n' % (spoken, shown_last, pad, labels)
    h = h[:a] + blk + h[b:]
    h = re.sub(r'CLICKS = \{.*\}', 'CLICKS = ' + repr(clicks), h)
    h = re.sub(r'OUT = "[^"]+"', 'OUT = "%s"' % out_mp4, h)
    h = re.sub(r'WORK = "[^"]+"', 'WORK = "%s"' % work, h)
    t = TAIL.replace(MAIN_MARKS, '    marks = %s\n' % marks)
    open(out_py, 'w').write(h + '\n' + scenes_code + '\nSCENES = ' + scene_list + '\n\n' + t)
