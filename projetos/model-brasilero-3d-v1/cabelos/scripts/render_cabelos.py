"""Renders de conferencia (Cycles CPU) da cabeca com cabelo.

Modo 1 (arquivos prontos): python3 render_cabelos.py files <png_saida> <px> <blend1> [<blend2> ...]
    -> uma coluna por arquivo, linhas = vistas (frente, 3/4, tras 3/4)
Modo 2 (biblioteca):       python3 render_cabelos.py lib <lib.blend> <pasta_texturas> <cor> <png_saida> <px>
"""
import os
import sys

import bpy
from mathutils import Vector
from PIL import Image

VIEWS = [("frente", (0, -1, 0.08)), ("tres_quartos", (0.75, -0.65, 0.18)), ("tras", (-0.55, 0.85, 0.2))]
TARGET = Vector((0.002, 0.0, 0.372))


def setup(sc, px):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 24
    sc.cycles.use_denoising = False
    sc.render.resolution_x = sc.render.resolution_y = px
    w = sc.world or bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.2, 0.2, 0.22, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.1
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.0
    sc.collection.objects.link(sun)
    sun.rotation_euler = Vector((0.35, -1, 0.45)).normalized().to_track_quat("Z", "Y").to_euler()
    sc.view_settings.view_transform = "Standard"
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 0.17
    dec = bpy.data.objects.get("Rosto_Expressao")
    if dec and dec.animation_data:
        dec.animation_data.action = None
    return cam


def shoot(sc, cam, tag):
    ims = []
    for vn, d in VIEWS:
        d = Vector(d).normalized()
        cam.location = TARGET + d * 2
        cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = f"/tmp/_h_{tag}_{vn}.png"
        bpy.ops.render.render(write_still=True)
        ims.append(Image.open(sc.render.filepath).convert("RGB"))
    return ims


def column_sheet(cols, px, out):
    W = Image.new("RGB", (px * len(cols), px * len(VIEWS)), (30, 30, 34))
    for i, ims in enumerate(cols):
        for j, im in enumerate(ims):
            W.paste(im, (i * px, j * px))
    W.save(out)


mode = sys.argv[1]
if mode == "files":
    out, px, files = sys.argv[2], int(sys.argv[3]), sys.argv[4:]
    cols = []
    for k, f in enumerate(files):
        bpy.ops.wm.open_mainfile(filepath=f)
        for im in bpy.data.images:
            if not im.packed_file and not os.path.exists(bpy.path.abspath(im.filepath)):
                print("FALTANDO", f, im.filepath)
        sc = bpy.context.scene
        cam = setup(sc, px)
        cols.append(shoot(sc, cam, k))
    column_sheet(cols, px, out)
else:
    lib, texdir, cor, out, px = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], int(sys.argv[6])
    bpy.ops.wm.open_mainfile(filepath=lib)
    sc = bpy.context.scene
    cam = setup(sc, px)
    hairs = sorted([o for o in bpy.data.objects if o.name.startswith("Cabelo_")], key=lambda o: o.name)
    order = ["liso-repartido", "jogador-degrade", "raspado", "cacheado-curto", "crespo-curto", "espetado-gel", "mullet"]
    hairs.sort(key=lambda o: order.index(o["corte"]))
    cols = []
    for k, h in enumerate(hairs):
        m = bpy.data.materials.new("t")
        m.use_nodes = True
        m.use_backface_culling = False
        nt = m.node_tree
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(os.path.join(texdir, f"{h['corte']}_{cor}.png"))
        tex.interpolation = "Closest"
        b = nt.nodes["Principled BSDF"]
        b.inputs["Roughness"].default_value = 0.85
        nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
        nt.links.new(tex.outputs["Alpha"], b.inputs["Alpha"])
        h.data.materials.clear()
        h.data.materials.append(m)
        for o in hairs:
            o.hide_render = o is not h
        cols.append(shoot(sc, cam, k))
    column_sheet(cols, px, out)
