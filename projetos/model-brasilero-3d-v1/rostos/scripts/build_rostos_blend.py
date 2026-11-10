"""Sistema de rostos animados sobre o model-brasilero-3d-v1.

Uso: python3 build_rostos_blend.py <model-brasilero-3d-v1.blend> <skin.png do v1> <rostos_atlas.png> <pasta_saida>

O que faz (o .blend original NAO e alterado; tudo sai num arquivo novo):
- Cria "Rosto_Expressao": copia das faces da frente da cabeca, 0,6 mm para fora, com UV em projecao
  frontal reta. Le //rostos_atlas.png (fundo transparente, entao a pele de baixo aparece).
- O quadro mostrado vem de 3 propriedades do objeto Rosto_Expressao: tipo_rosto, animacao, quadro (0 a 4).
  O material le essas propriedades direto (no Attribute, tipo Object), sem driver.
- 5 Actions (Rosto_piscada_um_olho ...) de 5 quadros cada, interpolacao constante.
- Gera skin.png proprio: igual ao do v1, mas com a area ROSTO na cor da pele (o desenho do rosto
  agora vem do atlas, por cima).
- Salva calib.json com a posicao (em pixels do quadro 48x48) de olhos, boca e sobrancelhas.
"""
import json
import os
import shutil
import sys

import bpy
import bmesh  # depois de bpy
from mathutils import Vector
from PIL import Image

src_blend, src_skin, atlas_path, out = sys.argv[1:5]
os.makedirs(out, exist_ok=True)

N_TIPOS, N_ANIM, N_QUADROS = 5, 5, 5
COLS, ROWS = N_TIPOS * N_QUADROS, N_ANIM       # 25 x 5 quadros no atlas
CELL = 48
PAD_PX = 1                                     # margem dentro do quadro (evita vazar do vizinho)
FRONT_LIMIT = float(os.environ.get("FRONT_LIMIT", "-0.12"))  # normal.y abaixo disso = frente
OFFSET = float(os.environ.get("DECAL_OFFSET", "0.0006"))
FPS_ANIM = 10
ANIMS = ["piscada_um_olho", "piscada_dois_olhos", "forca", "dor", "felicidade"]

bpy.ops.wm.open_mainfile(filepath=src_blend)
OB = bpy.data.objects
head = OB["Cabeca"]
mw = head.matrix_world
nmat = mw.to_3x3().inverted().transposed()

# ------------------------------------------------------------------ malha decalque (faces da frente)
bm = bmesh.new()
bm.from_mesh(head.data)
bm.transform(mw)
bm.normal_update()
drop = [f for f in bm.faces if f.normal.y >= FRONT_LIMIT]
bmesh.ops.delete(bm, geom=drop, context="FACES")
bm.normal_update()
# empurra cada vertice para fora pela media das normais das faces que o usam
for v in bm.verts:
    if v.link_faces:
        n = Vector((0, 0, 0))
        for f in v.link_faces:
            n += f.normal
        v.co += n.normalized() * OFFSET
xs = [v.co.x for v in bm.verts]
zs = [v.co.z for v in bm.verts]
x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
side = max(x1 - x0, z1 - z0)
cxw, czw = (x0 + x1) / 2, (z0 + z1) / 2
inner = (CELL - 2 * PAD_PX) / CELL


def cell_uv(co):
    """posicao 3D -> UV 0..1 dentro de um quadro (u: esquerda da imagem = lado direito do boneco)"""
    u = (co.x - cxw) / side          # -0.5..0.5 ; -x (lado direito do boneco) fica na esquerda da imagem
    v = (co.z - czw) / side
    return Vector((0.5 + u * inner, 0.5 + v * inner))


uvl = bm.loops.layers.uv.new("RostoUV")
for f in bm.faces:
    for l in f.loops:
        l[uvl].uv = cell_uv(l.vert.co)

me = bpy.data.meshes.new("Rosto_Expressao")
bm.to_mesh(me)
bm.free()
dec = bpy.data.objects.new("Rosto_Expressao", me)
head.users_collection[0].objects.link(dec)
dec.parent = head
dec.matrix_parent_inverse = head.matrix_world.inverted()

# propriedades que escolhem o quadro
for k, desc in (("tipo_rosto", "0 classico, 1 animado, 2 focado, 3 sardento, 4 tranquilo"),
                ("animacao", "0 piscada um olho, 1 piscada dois olhos, 2 forca, 3 dor, 4 felicidade"),
                ("quadro", "0 a 4 (0 e 4 = rosto padrao, 2 = expressao completa)")):
    dec[k] = 0
    ui = dec.id_properties_ui(k)
    ui.update(min=0, max=4, soft_min=0, soft_max=4, description=desc)

# ------------------------------------------------------------------ material do rosto
atlas_dst = os.path.join(out, "rostos_atlas.png")
if os.path.abspath(atlas_path) != os.path.abspath(atlas_dst):
    shutil.copy(atlas_path, atlas_dst)
img = bpy.data.images.load(atlas_dst)
img.filepath = "//rostos_atlas.png"
img.alpha_mode = "STRAIGHT"

mat = bpy.data.materials.new("Rosto")
mat.use_nodes = True
if hasattr(mat, "surface_render_method"):
    mat.surface_render_method = "BLENDED"
if hasattr(mat, "blend_method"):
    try:
        mat.blend_method = "BLEND"
    except Exception:
        pass
mat.use_backface_culling = True
nt = mat.node_tree
N = nt.nodes
Lk = nt.links
bsdf = N["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = 1.0
if "Specular IOR Level" in bsdf.inputs:
    bsdf.inputs["Specular IOR Level"].default_value = 0.0


def node(t, x, y, **kw):
    n = N.new(t)
    n.location = (x, y)
    for k, v in kw.items():
        setattr(n, k, v)
    return n


uvn = node("ShaderNodeUVMap", -1300, 200, uv_map="RostoUV")
a_t = node("ShaderNodeAttribute", -1300, 0, attribute_type="OBJECT", attribute_name="tipo_rosto")
a_a = node("ShaderNodeAttribute", -1300, -150, attribute_type="OBJECT", attribute_name="animacao")
a_q = node("ShaderNodeAttribute", -1300, -300, attribute_type="OBJECT", attribute_name="quadro")
# coluna = tipo*5 + quadro ; linha (de baixo para cima no Blender) = 4 - animacao
m5 = node("ShaderNodeMath", -1100, 0, operation="MULTIPLY_ADD")
m5.inputs[1].default_value = 5.0
Lk.new(a_t.outputs["Fac"], m5.inputs[0])
Lk.new(a_q.outputs["Fac"], m5.inputs[2])
col_r = node("ShaderNodeMath", -950, 0, operation="ROUND")
Lk.new(m5.outputs[0], col_r.inputs[0])
row = node("ShaderNodeMath", -1100, -150, operation="SUBTRACT")
row.inputs[0].default_value = 4.0
Lk.new(a_a.outputs["Fac"], row.inputs[1])
row_r = node("ShaderNodeMath", -950, -150, operation="ROUND")
Lk.new(row.outputs[0], row_r.inputs[0])
comb = node("ShaderNodeCombineXYZ", -800, -60)
Lk.new(col_r.outputs[0], comb.inputs[0])
Lk.new(row_r.outputs[0], comb.inputs[1])
add = node("ShaderNodeVectorMath", -650, 120, operation="ADD")
Lk.new(uvn.outputs["UV"], add.inputs[0])
Lk.new(comb.outputs[0], add.inputs[1])
div = node("ShaderNodeVectorMath", -500, 120, operation="DIVIDE")
div.inputs[1].default_value = (COLS, ROWS, 1.0)
Lk.new(add.outputs[0], div.inputs[0])
tex = node("ShaderNodeTexImage", -320, 120, image=img, interpolation="Closest", extension="CLIP")
Lk.new(div.outputs[0], tex.inputs["Vector"])
Lk.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
Lk.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
me.materials.append(mat)
if hasattr(dec, "visible_shadow"):
    dec.visible_shadow = False

# ------------------------------------------------------------------ animacoes (5 Actions, 5 quadros, constante)
step = max(1, round(bpy.context.scene.render.fps / FPS_ANIM))   # 24 fps da cena -> ~2 quadros da cena por quadro de rosto
dec.animation_data_create()
actions = []
for ai, name in enumerate(ANIMS):
    act = bpy.data.actions.new(f"Rosto_{name}")
    act.use_fake_user = True
    dec.animation_data.action = act
    for fi in range(N_QUADROS):
        f = 1 + fi * step
        dec["animacao"] = ai
        dec["quadro"] = fi
        dec.keyframe_insert('["animacao"]', frame=f)
        dec.keyframe_insert('["quadro"]', frame=f)
    # segura o ultimo quadro um passo para fechar o ciclo
    dec.keyframe_insert('["quadro"]', frame=1 + N_QUADROS * step)
    actions.append(act)


def all_fcurves(act):
    """Blender 4.4+ usa layers/strips/channelbags; antes, act.fcurves"""
    if hasattr(act, "layers") and act.layers:
        out_ = []
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out_.extend(cb.fcurves)
        return out_
    return list(act.fcurves)


for act in actions:
    for fc in all_fcurves(act):
        for kp in fc.keyframe_points:
            kp.interpolation = "CONSTANT"

dec.animation_data.action = actions[0]
dec["animacao"] = 0
dec["quadro"] = 0
sc = bpy.context.scene
sc.frame_start = 1
sc.frame_end = 1 + N_QUADROS * step
sc.frame_set(1)

# ------------------------------------------------------------------ skin proprio (area ROSTO vira pele lisa)
skin = Image.open(src_skin).convert("RGBA")
px = skin.load()
# cor da pele = a mais comum na area CABECA_LADOS_TRAS (48,0,48,24)
from collections import Counter
cnt = Counter(px[x, y] for x in range(48, 96) for y in range(0, 24) if px[x, y][3] > 0)
pele = cnt.most_common(1)[0][0]
for y in range(0, 48):
    for x in range(0, 48):
        px[x, y] = pele
skin.save(os.path.join(out, "skin.png"))
for im in bpy.data.images:
    if im.filepath.endswith("skin.png"):
        im.filepath = "//skin.png"

# ------------------------------------------------------------------ calibracao: onde ficam olhos/boca no quadro 48x48
# referencia: os pontos da malha original da cabeca (frente) projetados no quadro
pts = [(cell_uv(mw @ v.co), (mw @ v.co)) for v in head.data.vertices]
info = {
    "box_world": {"x0": cxw - side / 2, "x1": cxw + side / 2, "z0": czw - side / 2, "z1": czw + side / 2},
    "head_z": [min(p[1].z for p in pts), max(p[1].z for p in pts)],
}
json.dump(info, open(os.path.join(out, "_decal_box.json"), "w"), indent=2)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "model-brasilero-3d-rostos.blend"), relative_remap=False)
print("decal faces:", len(me.polygons), "box", round(side, 4), "pele", pele, "step", step)
