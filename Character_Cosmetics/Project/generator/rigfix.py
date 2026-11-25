"""Weight rules for Floppy Movers models (see CLAUDE.md "Rigging rules").
numpy-only helpers; callers supply vertex positions, edges, part labels and weight arrays."""
import numpy as np

BONES = ['LowerTorso', 'UpperTorso', 'Head', 'LeftUpperArm', 'LeftLowerArm', 'LeftHand', 'RightUpperArm',
         'RightLowerArm', 'RightHand', 'LeftUpperLeg', 'LeftLowerLeg', 'LeftFoot', 'RightUpperLeg', 'RightLowerLeg', 'RightFoot']
BI = {b: i for i, b in enumerate(BONES)}
TORSO = ['LowerTorso', 'UpperTorso']
ARM = {s: [f'{p}UpperArm', f'{p}LowerArm', f'{p}Hand'] for s, p in (('L', 'Left'), ('R', 'Right'))}
LEG = {s: [f'{p}UpperLeg', f'{p}LowerLeg', f'{p}Foot'] for s, p in (('L', 'Left'), ('R', 'Right'))}
JOINTS = dict(hip_L=(0.25, 0.014, 1.95), hip_R=(-0.25, 0.014, 1.95), knee_L=(0.25, 0.0, 1.19), knee_R=(-0.25, 0.0, 1.19),
              ankle_L=(0.25, -0.03, 0.5), ankle_R=(-0.25, -0.03, 0.5), elbow_L=(0.86, 0.02, 2.2), elbow_R=(-0.86, 0.02, 2.2),
              wrist_L=(1.0, -0.044, 1.36), wrist_R=(-1.0, -0.044, 1.36), shoulder_L=(0.5, 0.0, 3.0), shoulder_R=(-0.5, 0.0, 3.0))


def mask_of(names):
    m = np.zeros(len(BONES)); m[[BI[n] for n in names]] = 1; return m


def region_mask(region, side=None):
    """allowed bones for a body region"""
    if region == 'arm': return mask_of(ARM[side])
    if region == 'foot': return mask_of(LEG[side][1:])
    if region == 'head': return mask_of(['Head'])
    if region == 'neck': return mask_of(['Head', 'UpperTorso'])
    if region == 'leg': return mask_of(['LowerTorso'] + LEG[side])
    if region == 'torso_side': return mask_of(TORSO + LEG[side])
    if region == 'torso_center': return mask_of(TORSO)
    if region == 'garment_torso_side': return mask_of(TORSO + LEG[side])
    if region == 'sleeve': return mask_of(ARM[side])
    if region == 'pelvis': return mask_of(['LowerTorso'])
    raise ValueError(region)


def finalize(W, M=None, minw=0.0105, maxinf=4):   # 0.0105: stored float32 weights stay >= 0.01
    """apply masks, keep 4 largest, drop < minw, normalize. Rows that end empty keep their argmax of the masked original."""
    W = np.array(W, float)
    if M is not None: W = W * M
    out = np.zeros_like(W)
    for i, w in enumerate(W):
        if w.sum() <= 0:
            continue
        idx = np.argsort(-w)[:maxinf]
        o = np.zeros_like(w); o[idx] = w[idx]
        o /= o.sum()
        o[o < minw] = 0
        o /= o.sum()
        out[i] = o
    return out


def smooth(W, edges, zone, iters=10, M=None):
    """Laplacian smoothing of weights over mesh edges, only where zone>0 (0..1 strength). Masks re-applied each step."""
    W = np.array(W, float)
    n = len(W)
    a = np.array([e[0] for e in edges]); b = np.array([e[1] for e in edges])
    deg = np.bincount(a, minlength=n) + np.bincount(b, minlength=n)
    z = np.clip(np.asarray(zone, float), 0, 1)[:, None]
    for _ in range(iters):
        acc = np.zeros_like(W)
        np.add.at(acc, a, W[b]); np.add.at(acc, b, W[a])
        avg = np.where(deg[:, None] > 0, acc / np.maximum(deg, 1)[:, None], W)
        W = W * (1 - z * 0.5) + avg * (z * 0.5)
        if M is not None:
            W = W * M
            s = W.sum(1, keepdims=True); W = np.where(s > 0, W / np.maximum(s, 1e-12), W)
    return W


def joint_zone(P, part, widths=None):
    """0..1 smoothing strength: only around waist, hips, knees, elbows, (shoulders only inside the torso part)."""
    w = dict(hip=0.32, knee=0.34, elbow=0.28, waist=0.18, ankle=0.12, wrist=0.12)
    if widths: w.update(widths)
    P = np.asarray(P)
    Z = np.zeros(len(P))
    J = {k: np.array(v) for k, v in JOINTS.items()}
    def ball(c, r):
        d = np.linalg.norm(P - c, axis=1); return np.clip(1 - d / r, 0, 1) ** 0.5
    for s in 'LR':
        Z = np.maximum(Z, ball(J['knee_' + s], w['knee']))
        Z = np.maximum(Z, ball(J['elbow_' + s], w['elbow']))
        Z = np.maximum(Z, ball(J['ankle_' + s], w['ankle']))
        Z = np.maximum(Z, ball(J['wrist_' + s], w['wrist']))
    # hips: horizontal band around the hip joints, full width of the pelvis
    hz = np.clip(1 - np.abs(P[:, 2] - 1.95) / w['hip'], 0, 1) ** 0.5 * (np.abs(P[:, 0]) < 0.6)
    wz = np.clip(1 - np.abs(P[:, 2] - 2.3) / w['waist'], 0, 1) ** 0.5 * (np.abs(P[:, 0]) < 0.7)
    Z = np.maximum(Z, hz); Z = np.maximum(Z, wz)
    return Z


def side_of_x(x, eps=0.02):
    return np.where(x > eps, 1, np.where(x < -eps, -1, 0))


def cross_limb_count(W):
    L = W[:, [BI[b] for b in ARM['L'] + LEG['L']]].sum(1) > 0
    R = W[:, [BI[b] for b in ARM['R'] + LEG['R']]].sum(1) > 0
    return int((L & R).sum())


def weld_groups(P, edges, tol=0.012, coincident=1e-5):
    """union-find clusters of vertices joined by edges shorter than tol (degenerate / near-duplicate geometry),
    plus vertices at the same position (stitched seams between separate parts, e.g. arm plugged into torso socket)."""
    P = np.asarray(P); n = len(P); par = np.arange(n)
    def f(a):
        while par[a] != a:
            par[a] = par[par[a]]; a = par[a]
        return a
    for a, b in edges:
        if np.linalg.norm(P[a] - P[b]) < tol:
            ra, rb = f(a), f(b)
            if ra != rb: par[ra] = rb
    if coincident:
        first = {}
        for i, p in enumerate(P):
            k = tuple(np.round(p / coincident).astype(np.int64))
            if k in first:
                ra, rb = f(i), f(first[k])
                if ra != rb: par[ra] = rb
            else: first[k] = i
    return np.array([f(i) for i in range(n)])


def weld_equalize(W, groups, M=None):
    """every vertex in a weld group gets the group's mean weights (and the intersection of their masks)."""
    W = np.array(W, float)
    if M is not None: M = np.array(M, float)
    order = np.argsort(groups); g = groups[order]
    starts = np.r_[0, np.nonzero(np.diff(g))[0] + 1, len(g)]
    for s, e in zip(starts[:-1], starts[1:]):
        if e - s < 2: continue
        idx = order[s:e]
        w = W[idx].mean(0)
        if M is not None:
            m = M[idx].min(0)
            if (w * m).sum() > 1e-9: w = w * m
            M[idx] = m if m.sum() > 0 else M[idx]
        W[idx] = w / max(w.sum(), 1e-12)
    return (W, M) if M is not None else W


def sstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def lstep(e0, e1, x, soft=0.25):
    """mostly-linear ramp with softened ends (soft=0 -> linear, 1 -> smoothstep)"""
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return (1 - soft) * t + soft * t * t * (3 - 2 * t)


DEFAULT_RAMPS = dict(knee=0.70, elbow=0.26, wrist=0.10, ankle=0.10, waist=(2.18, 2.52), neck=(3.12, 3.36),
                     hip_top=2.20, hip_bot=1.30, crotch=0.16, soft=0.2, hip_soft=0.5, knee_up=0.68, knee_dn=0.54, skirt_cap=0.2, skirt_x=0.8, sock_alpha=0.0, sock_torso=0.35, sock_arm=0.35,
                     slit_top=2.12, slit_blend=0.85, slit_blend_side=0.85, slit_blend_back=1.3, slit_cap=1.0, slit_cap_back_side=0.9, slit_cap_back=0.8)  # tuned with check_rig.py on the base body


def seg_param(P, a, b):
    a = np.array(a); b = np.array(b); d = b - a; L = np.linalg.norm(d)
    return (P - a) @ (d / L), L


def analytic_weights(P, region, side=None, R=None):
    """Smooth joint ramps for a body region. P: (n,3) points (Blender space, Z up, +X = character left).
    region: 'torso' (torso+legs mesh), 'arm', 'foot', 'head', 'neck'. Returns (n,15)."""
    R = dict(DEFAULT_RAMPS, **(R or {}))
    P = np.asarray(P, float); n = len(P); W = np.zeros((n, len(BONES)))
    J = {k: np.array(v) for k, v in JOINTS.items()}
    def put(name, w): W[:, BI[name]] += w
    if region == 'head': put('Head', 1.0); return W
    if region == 'neck':
        t = sstep(R['neck'][0], R['neck'][1], P[:, 2]); put('Head', t); put('UpperTorso', 1 - t); return W
    if region == 'arm':
        p = 'Left' if side == 'L' else 'Right'
        sock = (R.get('sockets') or {}).get(side)
        sh, el, wr = J['shoulder_' + side], J['elbow_' + side], J['wrist_' + side]
        # distance along the arm chain (shoulder->elbow->wrist), measured past the elbow / wrist
        s_el, _ = seg_param(P, el, wr)              # >0 below elbow
        s_up, Lu = seg_param(P, sh, el)
        s_wr, _ = seg_param(P, wr, wr + (wr - el))  # >0 below wrist
        lower = lstep(-R['elbow'], R['elbow'], s_el, R.get('soft', 0.25))
        hand = sstep(-R['wrist'], R['wrist'], s_wr)
        put(p + 'UpperArm', 1 - lower); put(p + 'LowerArm', lower * (1 - hand)); put(p + 'Hand', lower * hand)
        if sock is not None and len(sock) and 0 < R['sock_alpha'] < 1:
            # arm side of the shoulder seam: blend toward UpperTorso so seam verts match the torso socket rim exactly
            d = np.min(np.linalg.norm(P[:, None, :] - sock[None, :, :], axis=2), axis=1)
            t = (1 - R['sock_alpha']) * (1 - lstep(0, R['sock_arm'], d, 0.5))
            W *= (1 - t)[:, None]; W[:, BI['UpperTorso']] += t
        return W
    if region == 'foot':
        p = 'Left' if side == 'L' else 'Right'
        t = sstep(J['ankle_' + side][2] + R['ankle'], J['ankle_' + side][2] - R['ankle'], P[:, 2])
        put(p + 'Foot', t); put(p + 'LowerLeg', 1 - t); return W
    # torso + legs mesh
    z = P[:, 2]; x = P[:, 0]
    up = sstep(R['waist'][0], R['waist'][1], z)
    crotch_band = sstep(R.get('crotch_lo', 1.70), R.get('crotch_hi', 1.90), z)   # 0 below the crotch, 1 at/above it
    leg = lstep(R['hip_top'], R['hip_bot'], z, R.get('hip_soft', R.get('soft', 0.25))) * (1 - (1 - sstep(0.0, R['crotch'], np.abs(x))) * crotch_band)
    lowerleg = lstep(J['knee_L'][2] + R.get('knee_up', R['knee']), J['knee_L'][2] - R.get('knee_dn', R['knee']), z, R.get('soft', 0.25))
    foot = sstep(J['ankle_L'][2] + R['ankle'], J['ankle_L'][2] - R['ankle'], z)
    torso = 1 - leg
    put('UpperTorso', torso * up); put('LowerTorso', torso * (1 - up))
    for s, sg, p in (('L', 1, 'Left'), ('R', -1, 'Right')):
        on = (x * sg > 0.02).astype(float)   # centre line |x| <= 0.02: torso bones only
        put(p + 'UpperLeg', on * leg * (1 - lowerleg))
        put(p + 'LowerLeg', on * leg * lowerleg * (1 - foot))
        put(p + 'Foot', on * leg * lowerleg * foot)
    # shoulder sockets: torso skin around each arm socket follows that upper arm (full alpha at the rim, fading out)
    for s, sg, p in (('L', 1, 'Left'), ('R', -1, 'Right')):
        sock = (R.get('sockets') or {}).get(s)
        if sock is None or not len(sock): continue
        idx = np.where(x * sg > 0.2)[0]
        if not len(idx): continue
        d = np.min(np.linalg.norm(P[idx, None, :] - sock[None, :, :], axis=2), axis=1)
        a = R['sock_alpha'] * (1 - lstep(0, R['sock_torso'], d, 0.5))
        W[idx] *= (1 - a)[:, None]; W[idx, BI[p + 'UpperArm']] += a
    return W


def lbs(P, W, mats):
    """linear blend skinning in numpy. mats: (15,4,4) skinning matrices (pose @ rest^-1)."""
    Ph = np.c_[P, np.ones(len(P))]
    out = np.zeros((len(P), 3))
    for bi in range(len(BONES)):
        w = W[:, bi]
        nz = w > 0
        if nz.any(): out[nz] += w[nz, None] * (Ph[nz] @ mats[bi].T)[:, :3]
    return out


def clean_row(w, m=None, minw=0.0105, maxinf=4):
    w = np.array(w, float)
    if m is not None: w = w * m
    if w.sum() <= 0: return w
    idx = np.argsort(-w)[:maxinf]; o = np.zeros_like(w); o[idx] = w[idx]; o /= o.sum()
    o[o < minw] = 0; return o / o.sum()


def relax_failing(P, edges, W, pose_mats, M=None, lo=0.5, hi=1.5, margin=0.0, iters=60, steps=(0.25, 0.5, 0.75, 1.0),
                  zone=None, tie=None):
    """Weights-only repair, greedy and local: for every edge that would stretch/squash past the limits in any pose,
    try blending its endpoint weights together or shifting a little weight between a vertex's own allowed bones;
    a change is kept only if the worst violation over all edges touching the changed verts (all poses) improves.
    tie: representative index per vertex - tied verts (shell twins, weld groups) always get identical weights.
    Candidates are cleaned (masks, max 4, >= 0.01, normalized) before scoring, so later cleanup can't undo them."""
    P = np.asarray(P, float); W = np.array(W, float); n = len(P)
    E = np.array(edges); a, b = E[:, 0], E[:, 1]
    l0 = np.linalg.norm(P[a] - P[b], axis=1); ok = l0 > 1e-5
    lo2, hi2 = lo + margin, hi - margin
    allowed = np.ones(n, bool) if zone is None else np.asarray(zone) > 0
    rep = np.arange(n) if tie is None else np.asarray(tie)
    members = {}
    for i in range(n): members.setdefault(rep[i], []).append(i)
    inc = [[] for _ in range(n)]
    for k, (u, v) in enumerate(E):
        if ok[k]: inc[u].append(k); inc[v].append(k)
    Ph = np.c_[P, np.ones(n)]
    def viol_local(ks, Wloc):
        vs = np.unique(np.r_[a[ks], b[ks]])
        Wv = np.array([Wloc.get(rep[v], W[v]) for v in vs]); vi = {v: i for i, v in enumerate(vs)}
        ia = [vi[x] for x in a[ks]]; ib = [vi[x] for x in b[ks]]
        worst = 0.0
        for mats in pose_mats:
            Q = np.einsum('vb,bij,vj->vi', Wv, mats[:, :3, :], Ph[vs])
            r = np.linalg.norm(Q[ia] - Q[ib], axis=1) / l0[ks]
            v = np.maximum(np.log(np.maximum(r, 1e-9) / hi2), np.log(lo2 / np.maximum(r, 1e-9)))
            worst = max(worst, float(v.max()))
        return worst
    def edges_of(groups):
        ks = []
        for g in groups:
            for x in members[g]: ks += inc[x]
        return np.unique(ks)
    hist = []
    for it in range(iters):
        bad = np.zeros(len(E), bool)
        for mats in pose_mats:
            Q = lbs(P, W, mats)
            r = np.linalg.norm(Q[a] - Q[b], axis=1) / np.maximum(l0, 1e-9)
            bad |= ok & ((r > hi2) | (r < lo2))
        hist.append(int(bad.sum()))
        if not bad.any(): break
        changed = False
        for k in np.nonzero(bad)[0]:
            gu, gv = rep[a[k]], rep[b[k]]
            groups = [g for g in {gu, gv} if any(allowed[x] for x in members[g])]
            if not groups: continue
            ks = edges_of({gu, gv})
            base = viol_local(ks, {})
            mid = (W[members[gu][0]] + W[members[gv][0]]) / 2
            cands = []
            for st in steps:
                cand = {}
                for g in groups:
                    x = members[g][0]
                    cand[g] = clean_row(W[x] * (1 - st) + mid * st, None if M is None else M[x])
                cands.append(cand)
            for g in groups:
                x = members[g][0]
                bones_x = np.nonzero(M[x] if M is not None else np.ones(W.shape[1]))[0]
                for i in bones_x:
                    for j in bones_x:
                        if i == j or W[x, i] <= 0: continue
                        for d in (0.03, 0.08, 0.15):
                            w = W[x].copy(); t = min(d, w[i]); w[i] -= t; w[j] += t
                            cands.append({g: clean_row(w, None if M is None else M[x])})
            best = None
            for cand in cands:
                if any(c.sum() <= 0 for c in cand.values()): continue
                vv = viol_local(ks, cand)
                if vv < base - 1e-6 and (best is None or vv < best[0]): best = (vv, cand)
            if best:
                for g, w in best[1].items():
                    for x in members[g]: W[x] = w
                changed = True
        if not changed: break
    return W, hist
