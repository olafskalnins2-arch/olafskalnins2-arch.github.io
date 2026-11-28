# Concept sketch sheet for the skin specs (flat colour silhouettes, one card per skin).  python3 sketch.py out.png
import json, sys, os, math
from PIL import Image, ImageDraw, ImageFont
S = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'specs.json')))
RC = {'Common': '#9aa3ad', 'Rare': '#3b82f6', 'Epic': '#a855f7', 'Legendary': '#f59e0b'}
SKIN = '#f2b48a'
def font(sz, bold=True):
    p = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else '')
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()
def dark(c, k=0.7):
    c = c.lstrip('#'); r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4)); return (int(r * k), int(g * k), int(b * k))
CW, CH = 260, 420
def card(s):
    im = Image.new('RGB', (CW, CH), '#f4f1ec'); d = ImageDraw.Draw(im)
    rc = RC[s['rarity']]; d.rectangle((0, 0, CW - 1, CH - 1), outline=rc, width=6)
    d.rectangle((0, 0, CW, 26), fill=rc); d.text((10, 4), s['rarity'].upper(), fill='white', font=font(15))
    top, bot, sh, ac = s['top'], s['bottom'], s['shoes'], s['accent']
    cx = 130; hy = 110; hr = 56
    b = s.get('back')
    # ---- back items (behind the body)
    if b == 'wings_dragon':
        for sg in (-1, 1):
            d.polygon([(cx + sg * 40, 185), (cx + sg * 125, 120), (cx + sg * 118, 175), (cx + sg * 128, 215), (cx + sg * 100, 230), (cx + sg * 90, 265), (cx + sg * 45, 240)], fill='#3a1418', outline='#1a0a0c')
    if b == 'wings_feather':
        for sg in (-1, 1):
            for k in range(5):
                d.ellipse((cx + sg * (40 + k * 18) - 22, 150 + k * 8, cx + sg * (40 + k * 18) + 22, 230 + k * 14), fill='#ffffff' if k % 2 else '#efe9d8', outline='#d8c79a')
    if b == 'wings_flame':
        for k, a in enumerate(range(-70, 75, 18)):
            r = math.radians(a); L = 120 - abs(a) * 0.4
            x2, y2 = cx + math.sin(r) * L, 200 - math.cos(r) * L
            d.polygon([(cx - 12, 205), (x2, y2), (cx + 12, 205)], fill=['#ff5a1f', '#ffb21a', '#ffd84a'][k % 3])
    if b in ('katana', 'katana_neon'):
        d.line((cx - 70, 150, cx + 75, 300), fill='#18e7f2' if b == 'katana_neon' else '#2a2a2a', width=8)
    if b == 'tanks':
        for sg in (-1, 1): d.rounded_rectangle((cx + sg * 30 - 16, 150, cx + sg * 30 + 16, 255), 12, fill='#f3c623', outline='#9a7d10')
    if b == 'backpack': d.rounded_rectangle((cx - 55, 150, cx + 55, 270), 14, fill='#8a7a52'); d.rounded_rectangle((cx - 60, 135, cx + 60, 160), 10, fill='#5a7a4a')
    if b == 'guitar': d.ellipse((cx + 10, 220, cx + 85, 290), fill='#e33b8f'); d.line((cx + 45, 250, cx - 60, 140), fill='#2a2a2a', width=9)
    if b == 'shield': d.ellipse((cx - 72, 160, cx + 72, 300), fill='#b03a2e', outline='#c9a24a', width=6)
    if b == 'jetpack': d.rounded_rectangle((cx - 50, 160, cx + 50, 260), 10, fill='#d5d8dc'); [d.polygon([(cx + sg * 28 - 12, 260), (cx + sg * 28 + 12, 260), (cx + sg * 28 + 18, 285), (cx + sg * 28 - 18, 285)], fill='#ff7a1a') for sg in (-1, 1)]
    if b == 'board': d.rounded_rectangle((cx - 22, 140, cx + 22, 300), 18, fill='#22b8cf', outline='#1b1b1b', width=3)
    # ---- legs, shoes
    for x0 in (cx - 36, cx + 4):
        lc = bot
        if s['coat'] == 'zigzag': lc = top if x0 < cx else ac
        d.rectangle((x0, 262, x0 + 32, 360), fill=lc)
        d.ellipse((x0 - 6, 350, x0 + 40, 376), fill=sh)
    if s['num'] in ('16', '18'):
        for x0 in (cx - 36, cx + 4): d.rectangle((x0 + 2, 300, x0 + 30, 352), fill=SKIN)
    if s['num'] in ('19', '22'):
        for x0 in (cx - 36, cx + 4): d.rectangle((x0 + 2, 300, x0 + 30, 340), fill=SKIN)
    # ---- arms
    for sg in (-1, 1):
        x = cx + sg * 62
        d.rounded_rectangle((x - 12, 170, x + 12, 275), 10, fill=SKIN if s['num'] == '16' else top)
        d.ellipse((x - 13, 268, x + 13, 292), fill=SKIN)
    # ---- torso + coat silhouettes
    c = s['coat']; tb = {'none': 262, 'hip': 280, 'vest': 262, 'apron': 262, 'knee': 322, 'robe': 360, 'tassets': 262, 'kilt': 262, 'zigzag': 285, 'tabard': 262}[c]
    if c == 'robe':
        d.polygon([(cx - 50, 165), (cx + 50, 165), (cx + 78, 362), (cx - 78, 362)], fill=top, outline=dark(top))
        d.rectangle((cx - 52, 240, cx + 52, 252), fill=ac)
    else:
        d.rounded_rectangle((cx - 52, 160, cx + 52, tb), 16, fill=top, outline=dark(top))
    if c == 'knee':
        d.polygon([(cx - 56, 170), (cx - 8, 175), (cx - 14, 325), (cx - 64, 325)], fill=ac if s['num'] == '26' else top, outline=dark(top))
        d.polygon([(cx + 56, 170), (cx + 8, 175), (cx + 14, 325), (cx + 64, 325)], fill=ac if s['num'] == '26' else top, outline=dark(top))
        if s['num'] == '26':
            d.rounded_rectangle((cx - 8, 175, cx + 8, 262), 4, fill=s['top'])
    if c == 'vest':
        for sg in (-1, 1): d.polygon([(cx + sg * 52, 165), (cx + sg * 10, 175), (cx + sg * 14, 265), (cx + sg * 52, 265)], fill='#8a5a34')
    if c == 'apron': d.rounded_rectangle((cx - 40, 185, cx + 40, 300), 8, fill=ac); d.rectangle((cx - 22, 240, cx + 22, 270), outline=dark(ac), width=3)
    if c == 'tassets':
        for k in range(3): d.rounded_rectangle((cx - 56 - k * 6, 245 + k * 18, cx + 56 + k * 6, 268 + k * 18), 6, fill=top if k % 2 == 0 else dark(top, 0.8), outline=ac)
    if c == 'kilt': d.polygon([(cx - 50, 250), (cx + 50, 250), (cx + 62, 310), (cx - 62, 310)], fill='#ffffff', outline='#d9a72e'); d.rectangle((cx - 50, 244, cx + 50, 256), fill='#d9a72e')
    if c == 'zigzag':
        pts = [(cx - 52, 270)] + [(cx - 52 + k * 13, 300 if k % 2 else 270) for k in range(1, 9)]
        d.polygon(pts + [(cx + 52, 270), (cx + 52, 260), (cx - 52, 260)], fill=top)
        for i in range(4):
            for j in range(3): d.polygon([(cx - 39 + i * 26, 170 + j * 32), (cx - 26 + i * 26, 186 + j * 32), (cx - 39 + i * 26, 202 + j * 32), (cx - 52 + i * 26, 186 + j * 32)], fill=ac)
    if c == 'tabard': d.rectangle((cx - 24, 200, cx + 24, 330), fill=ac)
    if c in ('none',) and s['num'] in ('15', '20'):
        d.rectangle((cx - 36, 200, cx + 36, 262), fill=bot); [d.rectangle((cx + sg * 30 - 6, 160, cx + sg * 30 + 6, 205), fill=bot) for sg in (-1, 1)]
    if c in ('none', 'vest') and s['num'] not in ('15', '20', '27', '28', '37'): d.rectangle((cx - 52, 252, cx + 52, 262), fill='#2a2a2a')
    if s['num'] == '27':
        for x in (cx - 16, cx + 8): d.rectangle((x, 160, x + 8, 360), fill='#ffffff')
    if s['num'] == '37': d.ellipse((cx - 16, 190, cx + 16, 222), fill=ac); d.rectangle((cx - 52, 230, cx + 52, 236), fill='#ff7a1a')
    if b == 'satchel': d.line((cx - 50, 165, cx + 40, 260), fill='#7a5230', width=7); d.rounded_rectangle((cx + 20, 245, cx + 75, 295), 6, fill='#7a5230')
    # ---- head
    d.ellipse((cx - hr, hy - hr, cx + hr, hy + hr), fill=SKIN)
    for ex in (-20, 20):
        d.ellipse((cx + ex - 16, hy - 14, cx + ex + 16, hy + 18), fill='white', outline='#333333'); d.ellipse((cx + ex - 5, hy - 2, cx + ex + 5, hy + 8), fill='black')
    h = s['hat']; ht = hy - hr
    if h in ('cap', 'scrubcap', 'beanie', 'bucket', 'pith', 'kabuto', 'horns', 'dragonhelm'):
        col = {'cap': top, 'scrubcap': '#7cc6e8', 'beanie': ac if s['num'] == '30' else '#4a4d52', 'bucket': '#c8b28a', 'pith': '#efe6cf', 'kabuto': '#2a2a2e', 'horns': '#8a9096', 'dragonhelm': '#24222b'}[h]
        if s['num'] == '18': col = '#6b4a2b'
        if s['num'] == '22': col = '#1f3a5f'
        if s['num'] == '20': col = '#f5f3ee'
        d.chord((cx - hr - 2, ht - 4, cx + hr + 2, hy + 40), 180, 360, fill=col)
        if h in ('cap',): d.rectangle((cx - hr - 2, hy - 22, cx + 20, hy - 14), fill=ac if s['num'] == '18' else dark(col))
        if h in ('bucket', 'pith'): d.ellipse((cx - hr - 22, hy - 30, cx + hr + 22, hy - 12), fill=col, outline=dark(col))
        if h == 'kabuto':
            d.polygon([(cx - 50, ht - 30), (cx, ht + 10), (cx + 50, ht - 30), (cx + 40, ht - 22), (cx, ht), (cx - 40, ht - 22)], fill=ac)
        if h in ('horns', 'dragonhelm'):
            for sg in (-1, 1):
                d.polygon([(cx + sg * 40, ht + 30), (cx + sg * 95, ht - 30), (cx + sg * 70, ht + 40)], fill='#efe6cf' if h == 'horns' else '#5a1a1e')
    if h == 'band': d.rectangle((cx - hr + 4, hy - 40, cx + hr - 4, hy - 28), fill=ac if s['num'] == '24' else '#ffffff')
    if h == 'nightcap': d.polygon([(cx - hr, hy - 30), (cx + hr, hy - 30), (cx + 80, hy + 10)], fill='#ffffff', outline='#8fc1e8'); d.ellipse((cx + 70, hy, cx + 92, hy + 22), fill='#ffffff')
    if h == 'stetson': d.ellipse((cx - hr - 34, hy - 46, cx + hr + 34, hy - 26), fill='#c49a5c'); d.rounded_rectangle((cx - 40, ht - 20, cx + 40, hy - 36), 14, fill='#c49a5c'); d.rectangle((cx - 40, hy - 50, cx + 40, hy - 42), fill='#6b4428')
    if h == 'fedora': d.ellipse((cx - hr - 20, hy - 46, cx + hr + 20, hy - 30), fill='#3a3b40'); d.rounded_rectangle((cx - 40, ht - 16, cx + 40, hy - 38), 14, fill='#3a3b40'); d.rectangle((cx - 40, hy - 52, cx + 40, hy - 44), fill=ac)
    if h == 'mask': d.rounded_rectangle((cx - 44, hy - 52, cx + 44, hy - 26), 10, fill='#111111', outline=ac, width=3)
    if h == 'crystal' or h == 'crown':
        for k in range(-2, 3):
            d.polygon([(cx + k * 22 - 10, ht + 14), (cx + k * 22, ht - 34 - (10 if k == 0 else 0)), (cx + k * 22 + 10, ht + 14)], fill='#d8f1ff' if h == 'crystal' else ['#ff5a1f', '#ffb21a'][k % 2])
        if h == 'crown': d.rectangle((cx - 52, ht + 6, cx + 52, ht + 20), fill='#e0ad2a')
    if h == 'headset': d.arc((cx - hr - 4, ht - 4, cx + hr + 4, hy + 30), 180, 360, fill='#ff7a1a', width=8); d.line((cx + hr, hy, cx + 30, hy + 40), fill='#333333', width=4); d.line((cx - 40, ht + 10, cx - 50, ht - 30), fill='#333333', width=3)
    if h == 'bearskin': d.ellipse((cx - 50, ht - 90, cx + 50, hy - 20), fill='#141414')
    if h == 'nemes':
        d.polygon([(cx - hr - 6, hy - 30), (cx + hr + 6, hy - 30), (cx + hr + 16, hy + 70), (cx + hr - 6, hy + 70), (cx + hr - 6, hy - 10), (cx - hr + 6, hy - 10), (cx - hr + 6, hy + 70), (cx - hr - 16, hy + 70)], fill='#2a6fb0')
        for k in range(5): d.line((cx - hr, hy - 28 + k * 6, cx + hr, hy - 28 + k * 6), fill='#d9a72e', width=2)
        d.chord((cx - 50, 160, cx + 50, 210), 0, 180, fill='#d9a72e')
    if h == 'jester':
        for k, (dx, colr) in enumerate(((-75, '#6b2fa0'), (0, '#e5b72b'), (75, '#6b2fa0'))):
            d.polygon([(cx - 30 + k * 30, ht + 20), (cx + dx, ht - 40), (cx - 10 + k * 30, ht + 20)], fill=colr); d.ellipse((cx + dx - 8, ht - 48, cx + dx + 8, ht - 32), fill='#e5b72b')
    if h == 'halo': d.ellipse((cx - 50, ht - 34, cx + 50, ht - 14), outline='#e4b84a', width=7)
    if h == 'kasa': d.polygon([(cx - 100, hy - 30), (cx, ht - 40), (cx + 100, hy - 30)], fill='#1c1c22', outline=ac, width=4)
    if h == 'scrubcap':
        for k in range(4): d.ellipse((cx - 40 + k * 22, ht + 6, cx - 32 + k * 22, ht + 14), fill='#ffffff')
    # ---- label
    d.text((12, CH - 38), f"{s['num']}  {s['name'].replace('_', ' ')}", fill='#1b1b1b', font=font(17))
    return im
cols = 6; rows = -(-len(S) // cols)
sheet = Image.new('RGB', (cols * CW + 20, rows * CH + 80), '#2a2d33'); dd = ImageDraw.Draw(sheet)
dd.text((14, 18), 'Floppy Movers - 30 new skins (concept sketch)', fill='white', font=font(26))
x = 960
for r, c in RC.items(): dd.rectangle((x, 26, x + 22, 48), fill=c); dd.text((x + 30, 26), r, fill='white', font=font(18)); x += 150
for k, s in enumerate(S):
    sheet.paste(card(s), (10 + (k % cols) * CW, 70 + (k // cols) * CH))
sheet.save(sys.argv[1]); print('saved', sheet.size)
