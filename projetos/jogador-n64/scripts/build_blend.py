"""Converte o OBJ do Young Link (Smash Remix) em model-by-samuel.blend.

Uso:
    python3 build_blend.py <pasta_com_obj_e_mtl> <pasta_de_saida>

A pasta de saida recebe:
    model-by-samuel.blend
    textures/*.png   (copiadas de <pasta_com_obj_e_mtl>/textures ou informadas via TEXTURES_SRC)

As texturas ficam externas, com caminho relativo, para poderem ser editadas em
qualquer editor de imagem (Alt+R no Blender recarrega).
"""
import os
import re
import shutil
import sys

import bpy

src_dir, out_dir = sys.argv[1], sys.argv[2]
tex_src = os.environ.get("TEXTURES_SRC", os.path.join(src_dir, "textures"))
obj_path = os.path.join(src_dir, "young link.obj")
mtl_path = os.path.join(src_dir, "young link.mtl")

tex_out = os.path.join(out_dir, "textures")
os.makedirs(tex_out, exist_ok=True)
for f in os.listdir(tex_src):
    if f.lower().endswith(".png"):
        shutil.copy2(os.path.join(tex_src, f), os.path.join(tex_out, f))

# nome do material -> hash da textura (o .mtl aponta para um caminho F:\ do autor)
mat_tex = {}
cur = None
for line in open(mtl_path, encoding="utf-8", errors="ignore"):
    if line.startswith("newmtl"):
        cur = line.split(None, 1)[1].strip()
    elif line.startswith("map_Kd") and cur:
        base = re.split(r"[\\/]", line.split(None, 1)[1].strip())[-1]
        mat_tex[cur] = os.path.splitext(base)[0]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=obj_path)

missing = []
for mat in bpy.data.materials:
    h = mat_tex.get(mat.name)
    png = os.path.join(tex_out, f"{h}.png") if h else None
    if not png or not os.path.exists(png):
        missing.append(mat.name)
        continue
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (500, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (200, 0)
    bsdf.inputs["Roughness"].default_value = 1.0
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.location = (-200, 0)
    img = bpy.data.images.load(png, check_existing=True)
    tex.image = img
    tex.interpolation = "Closest"  # visual pixelado de N64
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    # transparencia so se a textura realmente tiver pixels transparentes
    px = img.pixels[:]
    if len(px) >= 4 and min(px[3::4]) < 0.999:
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        mat.surface_render_method = "DITHERED"

for o in bpy.data.objects:
    o.name = o.name.split("_")[0]  # ex: Mesh.016

# pecas a remover (nomes de objeto separados por virgula), ex: REMOVE="Mesh.014,Mesh.016"
for name in filter(None, os.environ.get("REMOVE", "").split(",")):
    obj = bpy.data.objects.get(name.strip())
    if obj is None:
        sys.exit(f"objeto nao encontrado: {name}")
    me = obj.data
    bpy.data.objects.remove(obj)
    bpy.data.meshes.remove(me)
for m in [m for m in bpy.data.materials if m.users == 0]:
    bpy.data.materials.remove(m)
for i in [i for i in bpy.data.images if i.users == 0]:
    bpy.data.images.remove(i)

bpy.ops.wm.save_as_mainfile(
    filepath=os.path.join(out_dir, "model-by-samuel.blend"), relative_remap=True
)

objs = [o for o in bpy.data.objects if o.type == "MESH"]
print("objetos:", len(objs), "materiais:", len(bpy.data.materials), "sem textura:", missing)
mins = [min(v.co[i] for o in objs for v in o.data.vertices) for i in range(3)]
maxs = [max(v.co[i] for o in objs for v in o.data.vertices) for i in range(3)]
print("bbox min", [round(x, 3) for x in mins], "max", [round(x, 3) for x in maxs])
