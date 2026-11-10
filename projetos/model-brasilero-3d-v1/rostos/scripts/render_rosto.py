"""Renderiza a cabeca de frente (ou outras vistas) mostrando quadros do rosto.

Uso: python3 render_rosto.py <blend> <png_saida> <lista "tipo,anim,quadro;..."> [vista front|q|side] [px] [atlas_override]
Gera uma tira horizontal com um render por item da lista.
"""
import sys

import bpy
from mathutils import Vector
from PIL import Image

blend, out, items = sys.argv[1], sys.argv[2], sys.argv[3]
view = sys.argv[4] if len(sys.argv) > 4 else "front"
px = int(sys.argv[5]) if len(sys.argv) > 5 else 360
atlas_override = sys.argv[6] if len(sys.argv) > 6 else None

bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
dec = bpy.data.objects["Rosto_Expressao"]
if dec.animation_data:
    dec.animation_data.action = None
if atlas_override:
    for im in bpy.data.images:
        if "rostos_atlas" in im.filepath:
            im.filepath = atlas_override
            im.reload()

head = bpy.data.objects["Cabeca"]
ps = [head.matrix_world @ v.co for v in head.data.vertices]
c = Vector([(min(p[i] for p in ps) + max(p[i] for p in ps)) / 2 for i in range(3)])
D = {"front": (0, -1, 0), "q": (0.6, -0.8, 0.1), "side": (1, 0, 0), "body": (0, -1, 0)}
d = Vector(D[view]).normalized()
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = 0.14 if view != "body" else 0.55
cc = c if view != "body" else Vector((0, 0, 0.22))
cam.location = cc + d * 2
cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()

sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 24
sc.cycles.use_denoising = False
sc.render.resolution_x = sc.render.resolution_y = px
sc.render.film_transparent = False
w = sc.world or bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.18, 0.18, 0.2, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 3.0
sc.collection.objects.link(sun)
sun.rotation_euler = (Vector((0.25, -1, 0.25))).normalized().to_track_quat("Z", "Y").to_euler()
sc.view_settings.view_transform = "Standard"

ims = []
for k, it in enumerate(items.split(";")):
    t, a, q = map(int, it.split(","))
    dec["tipo_rosto"], dec["animacao"], dec["quadro"] = t, a, q
    dec.update_tag()
    sc.render.filepath = f"/tmp/_r{k}.png"
    bpy.ops.render.render(write_still=True)
    ims.append(Image.open(f"/tmp/_r{k}.png").convert("RGB"))
W = Image.new("RGB", (px * len(ims), px), (40, 40, 40))
for i, im in enumerate(ims):
    W.paste(im, (i * px, 0))
W.save(out)
