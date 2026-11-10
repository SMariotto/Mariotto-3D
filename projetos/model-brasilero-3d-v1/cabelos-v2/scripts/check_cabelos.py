"""Checagem de bugs nos cortes da biblioteca: faces degeneradas, vertices dentro da cabeca,
cabelo na frente dos olhos, pontas soltas longe da cabeca."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import bpy, bmesh
from mathutils import Vector
import hair_lib as H
bpy.ops.wm.open_mainfile(filepath=sys.argv[1])
bvh = H.build_bvh()
ok = True
for o in sorted([o for o in bpy.data.objects if o.name.startswith("Cabelo_")], key=lambda o: o.name):
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    degen = sum(1 for f in bm.faces if f.calc_area() < 1e-9)
    inside = olhos = longe = 0
    for v in bm.verts:
        d = v.co - H.C
        r = d.length
        s = H.surf_dist(bvh, d.normalized())
        if s is not None and r < s - 0.0012:
            inside += 1
        if -0.034 < v.co.x < 0.038 and 0.366 < v.co.z < 0.3885 and v.co.y < -0.035:
            olhos += 1
        # distancia ate a superficie mais proxima
        loc, n, i, dist = bvh.find_nearest(v.co)
        if dist > 0.045:
            longe += 1
    print(f"{o['corte']:16s} faces {len(bm.faces):5d} degeneradas {degen:3d} dentro_da_cabeca {inside:3d} frente_dos_olhos {olhos:3d} longe>4.5cm {longe:3d}")
    bm.free()
