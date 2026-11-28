from o04 import *
NUM, NAME, RARITY, MAXD = '16', 'Gym_Buddy', 'Common', 0.32


BODY_SKIN = SKIN   # same tone as the arms in Roblox (see o02.SKIN)


def _shin(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc


def build():
    pal = {'lime': '#9be22d', 'lime_d': '#7cc01e', 'black': '#1e1e22', 'black_l': '#34343a', 'white': '#ffffff',
           'white_d': '#e4e4e6', 'orange': '#ff5a36', 'orange_d': '#d9431f', 'skin': BODY_SKIN}
    P = []

    # ---- athletic shorts (lower layer first) ----
    pt = pants('Shorts', 2.2, 1.42, 0.045, hip_off=0.06, leg_extra=lambda z, a: 0.025 + 0.05 * max(0, 1.85 - z))

    def shorts_paint(U, V, m):
        img = P_solid(pal['black'])(U, V, m)
        z, az = zc(U, V, m)
        if m.get('kind') == 'leg':
            sg = 1 if m.get('side') == 'L' else -1
            img = mix(img, aa((np.abs(az - sg * PI / 2) - 0.16) * 300), pal['white'])         # outer side stripe
            img = mix(img, aa((np.abs(az - sg * PI / 2) - 0.035) * 300), pal['black'])        # split into two lines
            img = mix(img, aa(np.abs(z - 1.47) * 500 - 1.5), pal['black_l'])                  # hem stitch
        else:
            img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.10) * 300), pal['white'])
            img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.022) * 300), pal['black'])
            img = mix(img, aa(np.abs(z - 2.12) * 500 - 1.5), pal['black_l'])                  # waistband seam
        return img
    for p in pt: p.paint = shorts_paint

    # ---- lime tank top: hangs over the shorts; deep armholes + scoop neck painted as skin with a rib trim ----
    tank = torso_shell('Tank', 1.98, 0.045, nseg=32, extra=lambda z, a: 0.015 + 0.02 * max(0, 2.2 - z), th=0.02,
                       hang=2.3, over=pt)
    zmax = tank.meta['zmax']

    def tank_paint(U, V, m):
        img = P_solid(pal['lime'])(U, V, m)
        z, az = zc(U, V, m)
        aaz = np.abs(az)
        # armholes: ellipse around the shoulder side
        da = np.sqrt(((aaz - PI / 2) / 0.56) ** 2 + ((z - 2.8) / 0.34) ** 2)
        # scoop necks (front deeper than back)
        dn = np.sqrt((az / 0.62) ** 2 + ((z - zmax - 0.02) / 0.34) ** 2)
        db = np.sqrt(((PI - aaz) / 0.55) ** 2 + ((z - zmax - 0.02) / 0.16) ** 2)
        for d in (da, dn, db):
            img = mix(img, aa((d - 1.07) * 120), pal['lime_d'])                              # rib trim
            img = mix(img, aa((d - 1.0) * 120), pal['skin'])
        # side seams + hem band
        img = mix(img, aa((np.abs(aaz - PI / 2) - 0.008) * 300) * 0.6 * (z < 2.4), pal['lime_d'])
        img = mix(img, aa(np.abs(z - 2.06) * 500 - 1.5), pal['lime_d'])
        # chest logo: white roundel with a black dumbbell (wearer's left chest)
        x = az * 0.45; lx, lz = 0.2, 2.6
        r = np.sqrt((x - lx) ** 2 + (z - lz) ** 2)
        img = mix(img, aa((r - 0.105) * 900), pal['black'])
        img = mix(img, aa((r - 0.09) * 900), pal['white'])
        dx, dz = x - lx, z - lz
        bar = np.maximum(np.abs(dx) - 0.05, np.abs(dz) - 0.009)
        plate = np.minimum(np.maximum(np.abs(np.abs(dx) - 0.05) - 0.012, np.abs(dz) - 0.04),
                           np.maximum(np.abs(np.abs(dx) - 0.068) - 0.008, np.abs(dz) - 0.028))
        img = mix(img, aa(np.minimum(bar, plate) * 900), pal['black'])
        return img
    tank.paint = tank_paint
    P.append(tank)
    P += pt

    # ---- wristbands ----
    for s in 'LR':
        wb = sleeve('Wristband_' + s, s, 0.83, 0.95, 0.04, nrows=4, cap=False, th=0.025, extra=lambda t, a: 0.008)
        wb.paint = lambda U, V, m: mix(P_solid(pal['white'])(U, V, m), aa(np.abs(V - 0.5) * 300 - 6), pal['lime'])
        P.append(wb)

    # ---- legs, socks, running shoes ----
    for s in 'LR':
        sl = skin_leg(s, 1.5, 0.5); sl.paint = P_solid(BODY_SKIN); P.append(sl)
        sk = _shin(leg_tube('Sock_' + s, s, 0.66, 0.5, 0.032, nseg=16, nrows=3, group='Feet', th=0.012))
        sk.paint = lambda U, V, m: mix(P_solid(pal['white'])(U, V, m), aa(np.abs(V - 0.72) * 300 - 4), pal['lime'])
        P.append(sk)
        sh = shoe('Runner_' + s, s, off=0.04, bulk=0.025, toe=0.05, sole_h=0.055, open_elev=44)

        def shoe_paint(U, V, m):
            img = P_solid(pal['orange'])(U, V, m)
            z, az = zc(U, V, m)
            aaz = np.abs(az)
            st = m['sole_top']
            # swoosh stripe along both sides, rising to the heel
            zc_ = st + 0.025 + 0.07 * np.clip((aaz - 0.7) / 1.8, 0, 1)
            img = mix(img, aa((np.abs(z - zc_) - 0.014) * 600) * ((aaz > 0.7) & (aaz < 2.6)), pal['white'])
            # laces across the instep
            lz = (z - 0.47) / 0.035
            lace = (np.abs(lz - np.round(lz)) < 0.22) & (np.round(lz) >= 0) & (np.round(lz) <= 3)
            img = mix(img, (lace & (aaz < 0.3)).astype(float), pal['white'])
            # heel tab
            img = mix(img, aa((np.abs(PI - aaz) - 0.25) * 300) * (z > st + 0.06), pal['orange_d'])
            # white midsole + dark tread
            img = mix(img, aa((z - st) * 600), pal['white'])
            img = mix(img, aa((z - (st - 0.04)) * 600), pal['black'])
            return img
        sh.paint = shoe_paint
        P.append(sh)
    return P, pal
