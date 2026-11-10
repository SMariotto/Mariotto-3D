"""Troca o "Couro_Cabeludo" (que era a base do cabelo antigo: capacete com aba e franja em zigue-zague)
por um "Cranio" de formato normal, emendado na borda do rosto.

Uso: python3 fix_cranio.py <entrada.blend> <saida.blend>

Como: casca convexa (convex hull) dos vertices da borda do rosto + pontos de um elipsoide (topo, lados, nuca).
Tira as faces que ficariam por cima do rosto. UV cilindrico na area COURO_CABELUDO da skin (cor de pele).
"""
import math
import sys

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

src, dst = sys.argv[1], sys.argv[2]
bpy.ops.wm.open_mainfile(filepath=src)
OB = bpy.data.objects
face = OB["Cabeca"]
mat_skin = face.data.materials[0]

CEN = Vector((0.0015, -0.003, 0.383))
RAD = Vector((0.0465, 0.0545, 0.0545))
NECK_Y = 0.008          # centro do pescoco em y (a nuca afina em direcao a ele)
SZ = 128
REG = (52, 24, 23, 18)   # pedaco da area COURO_CABELUDO que e todo cor de pele
PAD = 1

# borda do rosto (mundo)
bmf = bmesh.new()
bmf.from_mesh(face.data)
bmf.transform(face.matrix_world)
border = [v.co.copy() for v in bmf.verts if v.is_boundary]
face_bvh = BVHTree.FromBMesh(bmf)

pts = list(border)
NA, NE = 20, 12
for i in range(NE + 1):
    e = math.pi * i / NE
    for j in range(NA if 0 < i < NE else 1):
        a = 2 * math.pi * j / NA
        d = Vector((math.sin(e) * math.sin(a), -math.sin(e) * math.cos(a), math.cos(e)))
        p = CEN + Vector((d.x * RAD.x, d.y * RAD.y, d.z * RAD.z))
        if d.z < 0:
            # nuca: vai afinando em direcao ao pescoco (sem borda pendurada)
            t = min(1.0, (CEN.z - p.z) / (CEN.z - 0.336))
            k = 1 - 0.5 * t ** 1.6
            p = Vector((CEN.x + (p.x - CEN.x) * k, NECK_Y + (p.y - NECK_Y) * k, p.z))
        if p.z < 0.336:
            continue
        if p.y < -0.026 and p.z < 0.418:      # regiao do rosto: quem cobre e o proprio rosto
            continue
        pts.append(p)

bm = bmesh.new()
vs = [bm.verts.new(p) for p in pts]
nb = len(border)
res = bmesh.ops.convex_hull(bm, input=vs)
bmesh.ops.delete(bm, geom=[g for g in res.get("geom_interior", []) if isinstance(g, bmesh.types.BMVert)], context="VERTS")
bm.verts.ensure_lookup_table()
border_set = set(vs[:nb])
C = Vector((0.002, -0.003, 0.385))
kill = []
for f in bm.faces:
    if all(v in border_set for v in f.verts):
        kill.append(f)
        continue
    c = f.calc_center_median()
    d = (c - C).normalized()
    hit = face_bvh.ray_cast(C, d, 0.2)
    if c.z < 0.397 and abs(c.x - C.x) < 0.036 and hit[0] is not None and (hit[0] - C).length < (c - C).length - 0.0008:
        kill.append(f)          # ficaria na frente do miolo do rosto (olhos/nariz/boca)
        continue
    if f.normal.z < -0.45 and c.z < 0.372 and c.y < -0.004:
        kill.append(f)          # tampa embaixo do queixo (placa atravessando o pescoco)
bmesh.ops.delete(bm, geom=kill, context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:
    if (f.calc_center_median() - CEN).dot(f.normal) < 0:
        f.normal_flip()

# UV cilindrico na area COURO_CABELUDO
uvl = bm.loops.layers.uv.new("SkinUV")
zs = [v.co.z for v in bm.verts]
z0, z1 = min(zs), max(zs)
x, y, w, h = REG
for f in bm.faces:
    ts = []
    for l in f.loops:
        p = l.vert.co
        ang = math.atan2(p.x - CEN.x, -(p.y - CEN.y))          # 0 na frente
        ts.append(((ang + math.pi) / (2 * math.pi)) % 1.0)
    if max(ts) - min(ts) > 0.5:
        ts = [t + 1 if t < 0.5 else t for t in ts]
    for l, t in zip(f.loops, ts):
        t = min(t, 1.0)
        hz = (l.vert.co.z - z0) / (z1 - z0)
        px = x + PAD + t * (w - 2 * PAD)
        py = y + PAD + (1 - hz) * (h - 2 * PAD)
        l[uvl].uv = (px / SZ, 1 - py / SZ)

me = bpy.data.meshes.new("Cranio")
bm.to_mesh(me)
bm.free()
cr = bpy.data.objects.new("Cranio", me)
face.users_collection[0].objects.link(cr)
me.materials.append(mat_skin)
cr.parent = face
cr.matrix_parent_inverse = face.matrix_world.inverted()

old = OB["Couro_Cabeludo"]
oldme = old.data
bpy.data.objects.remove(old)
bpy.data.meshes.remove(oldme)
bpy.ops.wm.save_as_mainfile(filepath=dst, relative_remap=False)
print("cranio faces", len(me.polygons), "borda do rosto", nb)
