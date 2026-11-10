"""Young Link (sem espada/escudo) com uniforme de futebol simples.

Uso: python3 build_football.py <model-by-samuel.blend sem espada/escudo> <pasta_saida>

- tira o gorro, fecha o cabelo (calota preta) e pinta o cabelo de preto
- camisa preta lisa (aproveita a malha do tronco e das mangas)
- bermuda branca curta (geometria nova, substitui a saia da tunica)
- chuteiras brancas lisas
Texturas externas em <saida>/textures (so as que continuam em uso).
"""
import os
import shutil
import sys

import bpy
import bmesh  # precisa vir depois de bpy
from mathutils import Matrix, Vector

src_blend, out_dir = sys.argv[1], sys.argv[2]
src_tex = os.path.join(os.path.dirname(os.path.abspath(src_blend)), "textures")
os.makedirs(os.path.join(out_dir, "textures"), exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=src_blend)
OB = bpy.data.objects


def flat_mat(name, rgb, rough=0.9):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*rgb, 1)
    return m


M_HAIR = flat_mat("Cabelo_Preto", (0.02, 0.02, 0.02))
M_JERSEY = flat_mat("Camisa_Preta", (0.03, 0.03, 0.035))
M_SHORTS = flat_mat("Bermuda_Branca", (0.92, 0.92, 0.92))
M_BOOT = flat_mat("Chuteira_Branca", (0.92, 0.92, 0.92))


def srgb(r, g, b):
    f = lambda c: ((c / 255 + 0.055) / 1.055) ** 2.4 if c / 255 > 0.04045 else c / 255 / 12.92
    return (f(r), f(g), f(b))


# mesma cor dominante da pele da textura original (248,216,136), lisa, para as pernas
M_SKIN = flat_mat("Pele_Perna", srgb(248, 216, 136), rough=1.0)


def world_center(o, p):
    return o.matrix_world @ p.center


# ---------------- cabeca ----------------
head = OB["Mesh.003"]
bm = bmesh.new()
bm.from_mesh(head.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == 3], context="FACES_ONLY")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bm.to_mesh(head.data)
hair_pts = [head.matrix_world @ v.co for f in bm.faces if f.material_index == 0 for v in f.verts]
skin_pts = [head.matrix_world @ v.co for v in bm.verts]
bm.free()
head.data.materials[0] = M_HAIR
head.data.materials[3] = M_HAIR  # slot do gorro, ja sem faces


def bbox(pts):
    return (Vector([min(p[i] for p in pts) for i in range(3)]),
            Vector([max(p[i] for p in pts) for i in range(3)]))


hmn, hmx = bbox(hair_pts)
smn, smx = bbox(skin_pts)
print("cabelo bbox", [round(x, 3) for x in hmn], [round(x, 3) for x in hmx])
print("cabeca bbox", [round(x, 3) for x in smn], [round(x, 3) for x in smx])

# calota de cabelo: elipsoide cobrindo topo e nuca, aberta na frente (onde fica o rosto)
cx = (hmn.x + hmx.x) / 2
cy = (smn.y + smx.y) / 2 + 0.006
cz = hmn.z + 0.005
hx = (hmx.x - hmn.x) / 2 * 1.04
hd = (smx.y - smn.y) / 2 * 1.02
hz = (hmx.z - cz) * 1.02
Z_CUT = float(os.environ.get("HAIR_Z_CUT", smn.z + 0.032))
Y_CUT = float(os.environ.get("HAIR_Y_CUT", cy - 0.010))

bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=1.0)
for v in bm.verts:
    v.co = Vector((cx + v.co.x * hx, cy + v.co.y * hd, cz + v.co.z * hz))
kill = [f for f in bm.faces if f.calc_center_median().z < Z_CUT or f.calc_center_median().y < Y_CUT]
bmesh.ops.delete(bm, geom=kill, context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
me = bpy.data.meshes.new("Cabelo_Calota")
bm.to_mesh(me)
bm.free()
cap = bpy.data.objects.new("Cabelo_Calota", me)
bpy.context.scene.collection.objects.link(cap)
me.materials.append(M_HAIR)
for p in me.polygons:
    p.use_smooth = False

# ---------------- camisa (tronco + mangas) ----------------
for n in ("Mesh.001",):
    OB[n].data.materials[1] = M_JERSEY
for n in ("Mesh", "Mesh.005"):
    OB[n].data.materials[1] = M_JERSEY

# ---------------- bermuda ----------------
skirt = OB["Mesh.012"]
spts = [skirt.matrix_world @ v.co for v in skirt.data.vertices]
kmn, kmx = bbox(spts)
legs = {s: bbox([OB[n].matrix_world @ v.co for v in OB[n].data.vertices])
        for s, n in (("L", "Mesh.007"), ("R", "Mesh.006"))}
sk_mesh = skirt.data
bpy.data.objects.remove(skirt)
bpy.data.meshes.remove(sk_mesh)

z_top = kmx.z - 0.004
z_hem = float(os.environ.get("SHORTS_HEM", 0.148))
bm = bmesh.new()
cxs = (kmn.x + kmx.x) / 2
cys = (kmn.y + kmx.y) / 2
# pelve (bloco arredondado)
bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=1.0, radius2=1.0, depth=1.0,
                      matrix=Matrix.Translation((0, 0, 0)))
for v in bm.verts:
    v.co = Vector((cxs + v.co.x * (kmx.x - kmn.x) / 2 * 0.72, cys + v.co.y * (kmx.y - kmn.y) / 2 * 0.72,
                   (z_top + 0.185) / 2 + v.co.z * (z_top - 0.185)))
for s, (lmn, lmx) in legs.items():
    lx, ly = (lmn.x + lmx.x) / 2, (lmn.y + lmx.y) / 2
    r_top, r_hem = (lmx.x - lmn.x) * 0.58, (lmx.x - lmn.x) * 0.63
    h = z_top - z_hem
    geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=r_hem, radius2=r_top, depth=h,
                                 matrix=Matrix.Translation((lx, ly, z_hem + h / 2)))
me = bpy.data.meshes.new("Bermuda")
bm.to_mesh(me)
bm.free()
shorts = bpy.data.objects.new("Bermuda", me)
bpy.context.scene.collection.objects.link(shorts)
me.materials.append(M_SHORTS)

# ---------------- pernas e chuteiras ----------------
for n in ("Mesh.006", "Mesh.007"):
    for i in range(len(OB[n].data.materials)):
        OB[n].data.materials[i] = M_SKIN  # perna inteira em pele; a chuteira cobre so o pe
for n in ("Mesh.009", "Mesh.013"):
    OB[n].data.materials[0] = M_BOOT

# ---------------- limpeza e salvar ----------------
for m in [m for m in bpy.data.materials if m.users == 0]:
    bpy.data.materials.remove(m)
for i in [i for i in bpy.data.images if i.users == 0]:
    bpy.data.images.remove(i)
for img in bpy.data.images:
    fn = os.path.basename(bpy.path.abspath(img.filepath))
    dst = os.path.join(out_dir, "textures", fn)
    shutil.copy2(os.path.join(src_tex, fn), dst)
    img.filepath = "//textures/" + fn  # relativo ao .blend

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "model-by-samuel.blend"), relative_remap=False)
print("objetos:", len(OB), "materiais:", [m.name[:18] for m in bpy.data.materials])
