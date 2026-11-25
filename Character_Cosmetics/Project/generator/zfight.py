# Detect near-coincident surfaces between different pieces of an outfit (z-fighting risk)
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib import *
from pipeline import *
import o01, o02, o03, o04
from mathutils.bvhtree import BVHTree
load_body()
fns = [o01.classic_mover, o02.chill_dude, o02.raincoat, o02.boss_mode, o03.construction_hero, o03.chef, o03.firefighter, o03.pirate, o03.wizard, o04.knight, o04.astronaut, o04.ghost, o04.dino]
for fn in fns:
    P, pal = fn()
    big = [p for p in P if not p.rigid and len(p.verts) > 60]
    def outer_bvh(p):
        nf = p.meta.get('n_outer_faces', len(p.faces))
        return BVHTree.FromPolygons(p.verts, p.faces[:nf])
    trees = [(p, outer_bvh(p)) for p in big]
    issues = []
    for a in big:
        na = a.meta.get('n_outer_verts', len(a.verts))
        vn = vertex_normals(a)
        for b, tb in trees:
            if b is a: continue
            cnt = 0
            for i in range(na):
                loc, nor, fi, d = tb.find_nearest(a.verts[i])
                if loc is not None and d < 0.006 and abs(nor.dot(vn[i])) > 0.8: cnt += 1
            if cnt > 8: issues.append((a.name, b.name, cnt))
    print(fn.__name__, issues if issues else 'OK')
