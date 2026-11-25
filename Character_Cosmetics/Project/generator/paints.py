from pipeline import *

def phys(U, V, m):
    """physical coords: x around circumference (units), z or along-length coordinate (units)"""
    circ = m.get('circ', 1.0)
    if 'zmax' in m: z = m['zmin'] + V * (m['zmax'] - m['zmin'])
    else: z = V * m.get('length', 0.6)
    return U * circ, z

def bands_z(img, z, spec):
    """spec: list of (z0, z1, color)"""
    for z0, z1, c in spec:
        img = mix(img, aa(np.maximum(z0 - z, z - z1) * 500), c)
    return img

def reflective(img, coord, c0, c1, ycol='#f2e01c', scol='#c9cbcf'):
    w = c1 - c0
    img = mix(img, aa(np.maximum(c0 - coord, coord - c1) * 500), ycol)
    img = mix(img, aa(np.maximum(c0 + w * 0.36 - coord, coord - (c1 - w * 0.36)) * 500), scol)
    return img

def checker(U, V, m, size, c1, c2):
    x, z = phys(U, V, m)
    circ = m.get('circ', 1.0)
    n = max(2, int(round(circ / size)) // 2 * 2)  # even count around for seamless wrap
    i = np.floor(U * n).astype(int); j = np.floor(z / size).astype(int)
    img = P_solid(c1)(U, V, m)
    return mix(img, ((i + j) % 2).astype(float), c2)

def vstripes(U, V, m, size, c1, c2):
    circ = m.get('circ', 1.0)
    n = max(2, int(round(circ / size)) // 2 * 2)
    i = np.floor(U * n).astype(int)
    img = P_solid(c1)(U, V, m)
    return mix(img, (i % 2).astype(float), c2)

def scatter(U, V, m, density, seed, draw):
    """draw(img, dx, dz, k) using local physical offsets; tiles seamlessly around circumference"""
    rng = np.random.default_rng(seed)
    circ = m.get('circ', 1.0)
    x, z = phys(U, V, m)
    zlo, zhi = z.min(), z.max()
    area = circ * (zhi - zlo + 0.4)
    n = max(3, int(area * density))
    img = None
    pts = []
    # jittered grid for even coverage
    g = int(math.sqrt(n)) + 1
    for a in range(g):
        for b in range(g):
            px = (a + rng.uniform(0.15, 0.85)) / g * circ
            pz = zlo - 0.2 + (b + rng.uniform(0.15, 0.85)) / g * (zhi - zlo + 0.4)
            pts.append((px, pz, rng.integers(0, 1000)))
    return pts, x, z, circ

def flower(img, x, z, circ, px, pz, R, petal, center, rot=0.0):
    for off in (-circ, 0, circ):
        dx = x - (px + off); dz = z - pz
        if np.min(np.abs(dx)) > R * 1.3: continue
        r = np.sqrt(dx ** 2 + dz ** 2); th = np.arctan2(dz, dx) + rot
        edge = R * (0.55 + 0.45 * np.abs(np.cos(2.5 * th)))
        img = mix(img, aa((r - edge) * 900), petal)
        img = mix(img, aa((r - R * 0.22) * 900), center)
    return img

def star(img, x, z, circ, px, pz, R, col, rot=0.0):
    for off in (-circ, 0, circ):
        dx = x - (px + off); dz = z - pz
        if np.min(np.abs(dx)) > R * 1.3: continue
        r = np.sqrt(dx ** 2 + dz ** 2); th = np.arctan2(dz, dx) + rot
        # 5-point star radius function
        k = np.cos(5 * th) * 0.5 + 0.5
        edge = R * (0.45 + 0.55 * k ** 3)
        img = mix(img, aa((r - edge) * 900), col)
    return img

def moon(img, x, z, circ, px, pz, R, col):
    for off in (-circ, 0, circ):
        dx = x - (px + off); dz = z - pz
        if np.min(np.abs(dx)) > R * 1.3: continue
        r1 = np.sqrt(dx ** 2 + dz ** 2); r2 = np.sqrt((dx - R * 0.45) ** 2 + (dz - R * 0.2) ** 2)
        img = mix(img, aa((r1 - R) * 900) * aa((R * 0.85 - r2) * 900), col)
    return img
