from garments import *
from pipeline import *

def _shin(pc):
    pc.region = 'shin_' + pc.region[-1]; return pc

def classic_mover():
    pal = {'blue': '#3f73b8', 'blue_d': '#2f5a94', 'beige': '#cdbb94', 'beige_d': '#b09d77', 'brown': '#6b4428', 'brown_d': '#3d2618',
           'sole': '#2a2a2e', 'silver': '#a9adb3', 'btn': '#e8e8e8', 'white': '#f2f2f2'}
    P = []
    # shirt body (tucked), slight looseness
    shirt = torso_shell('Shirt', 2.12, 0.045, nseg=32, extra=lambda z, a: 0.01, th=0.02)
    def paint_shirt(U, V, m):
        img = P_solid(pal['blue'])(U, V, m)
        z, az = zc(U, V, m)
        # placket line + buttons drawn subtly (real buttons are geometry)
        img = mix(img, aa((np.abs(az) - 0.012) * 400), pal['blue_d'])
        # side seams
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.006) * 400) * 0.6, pal['blue_d'])
        return img
    shirt.paint = paint_shirt; P.append(shirt)
    for s in 'LR':
        sl = sleeve('Sleeve_' + s, s, 0.0, 0.40, 0.045, extra=lambda t, a: 0.015 * t)
        sl.paint = lambda U, V, m: mix(P_solid(pal['blue'])(U, V, m), aa((V - 0.12) * -300), pal['blue_d'])
        P.append(sl)
        # rolled cuff
        cf = sleeve('Cuff_' + s, s, 0.36, 0.42, 0.075, nrows=3, cap=False, th=0.02, col='blue', extra=lambda t, a: 0.01)
        P.append(cf)
    P.append(collar('Collar', 'fold', h=0.06, flare=0.03, open_front=0.28, col='blue', fold=0.08))
    # chest pocket
    bv = piece_bvh(shirt)
    pk = surface_patch('Pocket', bv, lambda s, t: Vector((0.17 + s * 0.2, 0, 2.62 + t * 0.2)), Vector((0, 1, 0)), 0.01, 4, 4, col='blue_d', th=0.012)
    pk.rigid = True; P.append(pk)
    pf = surface_patch('PocketFlap', bv, lambda s, t: Vector((0.16 + s * 0.22, 0, 2.79 + t * 0.06)), Vector((0, 1, 0)), 0.024, 4, 2, col='blue', th=0.012)
    pf.rigid = True; P.append(pf)
    for i, z in enumerate((2.95, 2.75, 2.55, 2.35, 2.17)):
        loc, n = project(bv, Vector((0.0, 0, z)), Vector((0, 1, 0)))
        P.append(prim_cyl(f'Button{i}', loc, loc + n * 0.02, 0.028, n=8, col='btn', group='Top'))
    # trousers
    pt = pants('Pants', 2.27, 0.50, 0.04, hip_off=0.08, extra=lambda z, a: 0.0, leg_extra=lambda z, a: 0.02 + 0.04 * max(0, (1.4 - z)), nseg=16)
    def paint_pants(U, V, m):
        img = P_solid(pal['beige'])(U, V, m)
        z, az = zc(U, V, m)
        img = mix(img, aa((np.abs(az) - 0.01) * 300) * (m.get('kind') == 'hip'), pal['beige_d'])
        img = mix(img, aa((np.abs(np.abs(az) - PI / 2) - 0.008) * 300) * 0.8, pal['beige_d'])
        return img
    for p in pt: p.paint = paint_pants
    P += pt
    # cargo pockets on thighs (outer side)
    for s, sg in (('L', 1), ('R', -1)):
        lb = piece_bvh(pt[1] if s == 'L' else pt[2])
        cp = surface_patch('Cargo_' + s, lb, lambda u, t, sg=sg: Vector((0, -0.12 + u * 0.24, 1.32 + t * 0.26)), Vector((-sg, 0, 0)), 0.012, 4, 4, col='beige_d', th=0.015, group='Bottom')
        cp.rigid = True; P.append(cp)
        cf = surface_patch('CargoFlap_' + s, lb, lambda u, t, sg=sg: Vector((0, -0.13 + u * 0.26, 1.55 + t * 0.07)), Vector((-sg, 0, 0)), 0.03, 4, 2, col='beige', th=0.015, group='Bottom')
        cf.rigid = True; P.append(cf)
    # belt
    bl = band('Belt', 2.14, 2.25, 0.10, th=0.02); bl.group = 'Bottom'
    bl.paint = lambda U, V, m: mix(P_solid(pal['brown'])(U, V, m), aa(np.minimum(V - 0.12, 0.88 - V) * -200), pal['brown_d'])
    P.append(bl)
    loc, n = project(piece_bvh(bl), Vector((0, 0, 2.2)), Vector((0, 1, 0)))
    P.append(prim_box('Buckle', loc + n * 0.015, (0.16, 0.03, 0.12), 'silver', group='Bottom'))
    # boots
    for s in 'LR':
        sh = shoe('Boot_' + s, s, off=0.04, bulk=0.03, toe=0.03)
        sh.paint = lambda U, V, m: mix(P_solid(pal['brown'])(U, V, m), aa((zc(U, V, m)[0] - m['sole_top']) * 600), pal['sole'])
        P.append(sh)
        shaft = _shin(leg_tube('BootShaft_' + s, s, 0.64, 0.47, 0.068, nseg=16, group='Feet'))
        shaft.paint = lambda U, V, m: mix(P_solid(pal['brown'])(U, V, m), aa((0.88 - V) * 300), pal['brown_d'])
        P.append(shaft)
    return P, pal
