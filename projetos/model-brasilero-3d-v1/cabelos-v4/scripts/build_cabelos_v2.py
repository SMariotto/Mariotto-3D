"""Cabelos v2: 7 cortes feitos de MECHAS (cunhas com quina, em camadas) x 5 cores = 35 versoes.

Uso: python3 build_cabelos_v2.py <model-brasilero-3d-rostos.blend> <pasta_saida> [lib]

Cada corte = casca fina e escura (sombra entre as mechas, esconde a careca) + mechas por cima.
Textura 64x64 por corte/cor: metade de cima = fios das mechas, metade de baixo = casca.
Os .blend leem //texturas/<corte>_<cor>.png, //../rostos/skin.png e //../rostos/rostos_atlas.png.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bpy
import bmesh
from mathutils import Vector
from PIL import Image

import hair_lib as H
from hair_locks import Locks, blob, to_ae

src, out = sys.argv[1], sys.argv[2]
only_lib = len(sys.argv) > 3
os.makedirs(os.path.join(out, "texturas"), exist_ok=True)

CORTES = ["liso-repartido", "jogador-degrade", "raspado", "cacheado-curto", "crespo-curto", "espetado-gel", "mullet"]
CORES = {
    "loiro-natural": [(126, 88, 42), (176, 130, 64), (214, 172, 100), (238, 208, 146)],
    "loiro-pintado": [(170, 165, 142), (208, 204, 182), (230, 228, 210), (248, 247, 236)],
    "ruivo": [(112, 40, 20), (162, 68, 30), (200, 98, 46), (228, 136, 78)],
    "preto": [(20, 18, 20), (38, 34, 36), (62, 57, 60), (94, 90, 94)],
    "castanho": [(54, 34, 22), (88, 58, 36), (122, 84, 52), (156, 114, 74)],
}
PI = math.pi
BROW_Z = 0.3935          # pontas da franja param aqui (sobrancelha comeca em ~0.390)


def lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))


def shell_half(h):
    """joga o UV da casca para a metade de baixo da textura"""
    for f in h.bm.faces:
        for l in f.loops:
            u, v = l[h.uv].uv
            l[h.uv].uv = (u, v * 0.5)


# ------------------------------------------------------------------ cortes
def corte(nome, coll):
    SH = 0.0030
    if nome == "liso-repartido":
        h = H.Hair("Cabelo", cols=30, rings=10, seed=11)
        h.shell(lambda a, t: SH)
        shell_half(h)
        L = Locks(h, seed=11)
        P = -0.62     # risca (lado direito do boneco)
        L.fan(7, 1.8, 2 * PI - 1.8, ("t", 0.12), ("t", 1.0), 0.036, 0.009, lift=0.002, segs=4, jitter=0.04)
        L.fan(2, 1.0, 1.65, ("t", 0.15), ("t", 1.0), 0.032, 0.008, sweep=0.05, lift=0.0015, layer=1, segs=4)
        L.fan(2, -1.65, -1.0, ("t", 0.30), ("t", 1.0), 0.030, 0.008, sweep=-0.05, lift=0.0015, layer=1, segs=4)
        for i, t0 in enumerate((0.12, 0.30, 0.48)):
            L.lock(P + 0.10, ("t", t0), 0.85 + 0.28 * i, ("t", 0.95), 0.036, 0.010, lift=0.003,
                   segs=6, layer=2, bend=0.04)
        for i, a in enumerate((-0.45, -0.15, 0.15, 0.42)):
            L.lock(a, ("t", 0.40), a + 0.32, ("z", BROW_Z + 0.0012 * i), 0.029, 0.008, lift=0.0022,
                   segs=4, layer=3)
        L.lock(P - 0.05, ("t", 0.35), P - 0.35, ("z", BROW_Z - 0.002), 0.026, 0.007, lift=0.0018, segs=4, layer=3)
        shell_dark = True
    elif nome == "jogador-degrade":
        def th(a, t):
            side = max(0.0, min(1.0, (abs(a) - 0.75) / 0.35))
            thin = lerp(0.0045, 0.0024, (t - 0.42) / 0.18)
            return lerp(SH, thin, side)
        h = H.Hair("Cabelo", cols=32, rings=10, seed=12)
        h.shell(th)
        shell_half(h)
        L = Locks(h, seed=12)
        for i in range(6):
            a_root = PI + (i - 2.5) * 0.36
            a_end = (i - 2.5) * 0.2
            L.lock(a_root, ("t", 0.30), a_end, ("z", 0.401), 0.032, 0.009, lift=0.0055, lift_pow=3,
                   segs=6, layer=1 + (i % 2))
        for i in range(5):
            a = (i - 2) * 0.42
            L.lock(a, ("t", 0.10), a * 1.1, ("t", 0.62), 0.028, 0.008, lift=0.007, lift_pow=2, segs=3, layer=3)
        shell_dark = False
    elif nome == "raspado":
        h = H.Hair("Cabelo", cols=30, rings=9, seed=13)
        h.shell(lambda a, t: lerp(0.0028, 0.002, (t - 0.8) / 0.2))
        shell_half(h)
        L = Locks(h, seed=13)
        shell_dark = False
    elif nome == "cacheado-curto":
        h = H.Hair("Cabelo", cols=30, rings=10, seed=14)
        h.shell(lambda a, t: 0.0030)
        shell_half(h)
        L = Locks(h, seed=14)
        rng = random.Random(14)
        rows = [(0.0, 1), (0.15, 6), (0.3, 9), (0.45, 12), (0.6, 14), (0.75, 15), (0.88, 16), (0.99, 16)]
        for r, (t0, n) in enumerate(rows):
            for i in range(n):
                a = -PI + (i + 0.5 * (r % 2)) * 2 * PI / n + rng.uniform(-0.07, 0.07)
                t = t0 + rng.uniform(-0.03, 0.03)
                if t0 > 0.9 and 0.9 < abs(a) < 2.3:
                    continue                       # nada de cacho em cima da orelha/costeleta
                rad = rng.uniform(0.0115, 0.0135) * (0.8 if t0 > 0.95 else 1.0)
                if t0 > 0.85 and abs(a) < 1.0:
                    rad *= 0.78                    # franja de cachos menor, sem cobrir sobrancelha/olho
                    t = min(t, 0.9)
                blob(L, a, ("t", max(0.0, t)), rad, flat=rng.uniform(0.55, 0.68), segs=7, rings=4,
                     base_off=0.0032 + 0.001 * (r % 2), sink=0.45)
        shell_dark = True
    elif nome == "crespo-curto":
        def th(a, t):
            return lerp(0.0095, 0.007, (t - 0.35) / 0.4) if t < 0.86 else lerp(0.007, 0.0028, (t - 0.86) / 0.14)
        h = H.Hair("Cabelo", cols=26, rings=9, seed=15)
        h.shell(th, jitter=0.0006)
        shell_half(h)
        L = Locks(h, seed=15)
        rng = random.Random(15)
        rows = [(0.05, 5), (0.22, 9), (0.4, 12), (0.58, 14), (0.74, 15)]
        for r, (t0, n) in enumerate(rows):
            for i in range(n):
                a = -PI + (i + 0.5 * (r % 2)) * 2 * PI / n + rng.uniform(-0.05, 0.05)
                L.lock(a, ("t", t0), a + rng.uniform(-0.08, 0.08), ("t", t0 + 0.16), 0.02, 0.0045,
                       lift=0.0018, lift_pow=1.5, segs=2, base_off=0.0075 if t0 < 0.6 else 0.0062)
        shell_dark = False
    elif nome == "espetado-gel":
        h = H.Hair("Cabelo", cols=30, rings=10, seed=16)
        h.shell(lambda a, t: SH)
        shell_half(h)
        L = Locks(h, seed=16)
        rng = random.Random(16)
        BACK = Vector((0, 1.0, 0.55))
        spec = [(0.86, 9, 0.006, 0.038), (0.6, 8, 0.011, 0.042), (0.34, 6, 0.015, 0.044), (0.08, 3, 0.017, 0.042)]
        for r, (t0, n, lift, w) in enumerate(spec):
            for i in range(n):
                a = -PI + (i + 0.5 * (r % 2)) * 2 * PI / n + rng.uniform(-0.05, 0.05)
                front = abs(a) < 0.8
                if abs(a) < 0.85 and t0 > 0.8:
                    continue                       # frente baixa: quem cobre e a franja abaixo
                if t0 > 0.8:
                    t0 = 0.72                       # nuca: raiz mais alta, ponta nao sai da cabeca
                e0 = L.resolve(a, ("t", t0))
                d0 = H.direction(a, e0)
                if front and t0 < 0.7:
                    # topo da frente: topete pra cima e um pouco pra frente (fecha a "coroa")
                    a1, e1 = to_ae(d0 + Vector((0, -0.25, 1.0)).normalized() * 0.55)
                else:
                    a1, e1 = to_ae(d0 + BACK.normalized() * (0.75 if t0 < 0.8 else 0.45))
                L.lock(a, ("e", e0), a1, ("e", e1), w, 0.011, lift=lift * rng.uniform(0.9, 1.1),
                       lift_pow=1.7, segs=4, layer=3 - r, taper=1.0)
        # franja espetada: mechas grossas descendo na testa com a ponta levantada pra frente
        for i, a in enumerate((-0.62, -0.31, 0.0, 0.31, 0.62)):
            L.lock(a * 0.7, ("t", 0.38), a, ("z", BROW_Z + 0.004 + 0.002 * (i % 2)), 0.036, 0.010,
                   lift=0.0075, lift_pow=3, segs=5, layer=4)
        # nuca: mechas deitadas descendo, para nao ficar so a casca escura atras
        L.fan(6, 1.9, 2 * PI - 1.9, ("t", 0.45), ("t", 0.98), 0.036, 0.009, lift=0.003, lift_pow=3,
              segs=4, layer=0, jitter=0.05)
        shell_dark = True
    elif nome == "mullet":
        h = H.Hair("Cabelo", cols=30, rings=10, seed=17)
        h.shell(lambda a, t: SH)
        shell_half(h)
        L = Locks(h, seed=17)
        L.fan(5, 2.45, 2 * PI - 2.45, ("t", 0.25), ("t", 1.0), 0.038, 0.009, lift=0.002, segs=4,
              hang=0.036, hang_segs=3, flick=0.005, jitter=0.03)
        L.fan(2, 2.05, 2.45, ("t", 0.3), ("t", 1.0), 0.032, 0.008, lift=0.0018, segs=4, hang=0.014, hang_segs=2)
        L.fan(2, -2.45, -2.05, ("t", 0.3), ("t", 1.0), 0.032, 0.008, lift=0.0018, segs=4, hang=0.014, hang_segs=2)
        L.fan(2, 1.0, 1.75, ("t", 0.35), ("t", 0.98), 0.028, 0.007, lift=0.001, layer=1, segs=3)
        L.fan(2, -1.75, -1.0, ("t", 0.35), ("t", 0.98), 0.028, 0.007, lift=0.001, layer=1, segs=3)
        L.fan(5, 1.0, 2 * PI - 1.0, ("t", 0.05), ("t", 0.8), 0.036, 0.009, lift=0.0025, layer=1, segs=4)
        for i, a in enumerate((-0.5, -0.18, 0.18, 0.5)):
            sw = -0.14 if a < 0 else 0.14
            L.lock(a * 0.6, ("t", 0.3), a + sw, ("z", BROW_Z + 0.004), 0.029, 0.008, lift=0.0025,
                   segs=4, layer=2 + (i % 2))
        shell_dark = True
    else:
        raise ValueError(nome)
    ob = h.to_object(coll)
    for p in ob.data.polygons:
        p.use_smooth = True
    ob["corte"] = nome
    ob["mechas"] = L.count
    ob["shell_dark"] = shell_dark
    return ob


# ------------------------------------------------------------------ texturas (indices 0..3, 4 = transparente)
def tex_index(nome, shell_dark):
    rng = random.Random(sum(map(ord, nome)))
    W = Hh = H.TEX
    idx = [[1] * W for _ in range(Hh)]
    half = Hh // 2
    # metade de cima: fios das mechas (raiz em cima, ponta embaixo)
    base = []
    b = 1
    for x in range(W):
        if rng.random() < 0.3:
            b = 2 if b == 1 else 1
        base.append(b)
    for x in range(W):
        dark = rng.random() < 0.16
        hb0, hb1 = 6 + rng.randint(-2, 1), 13 + rng.randint(-1, 2)
        for y in range(half):
            v = base[x]
            if dark and y > 2:
                v = 0
            elif hb0 <= y <= hb1:
                v = min(3, v + 1)
            if y < 2:
                v = max(0, v - 1)            # raiz mais escura
            if y > half - 6 and v > 1:
                v -= 1                       # ponta um tom abaixo
            idx[y][x] = v
    if nome in ("cacheado-curto", "crespo-curto"):
        for _ in range(90):
            x, y = rng.randrange(W), rng.randrange(half)
            idx[y][x] = rng.choice((0, 3 if y < half * 0.5 else 2))
    # metade de baixo: casca
    for y in range(half, Hh):
        for x in range(W):
            if shell_dark:
                idx[y][x] = 0 if rng.random() < 0.7 else 1
            else:
                r = rng.random()
                v = rng.choice((1, 2, 2) if nome == "raspado" else (1, 1, 2))
                if r < 0.12:
                    v = 0
                elif r < 0.2 and y < half + 14:
                    v = 3
                idx[y][x] = v
    # borda da casca (dobra) escura
    for y in range(Hh - 4, Hh):
        for x in range(W):
            idx[y][x] = 0
    if nome == "jogador-degrade":     # laterais e nuca rareiam ate sumir
        y0 = half + 9
        for y in range(y0, Hh):
            t = (y - y0) / (Hh - 4 - y0)
            for x in range(W):
                a = (x + 0.5) / W * 2 * PI - PI
                side = max(0.0, min(1.0, (abs(a) - 0.75) / 0.35))
                if side <= 0:
                    continue
                r = rng.random()
                if t > 0.55 and r < (t - 0.55) * side * 0.9:
                    idx[y][x] = 4
                elif r < 0.25 + t * side * 0.6:
                    idx[y][x] = 0
    return idx


def write_tex(idx, pal, path):
    img = Image.new("RGBA", (H.TEX, H.TEX))
    px = img.load()
    for y, row in enumerate(idx):
        for x, v in enumerate(row):
            px[x, y] = (0, 0, 0, 0) if v == 4 else (*pal[v], 255)
    img.save(path)


def hair_material(name, tex_path_rel, abs_path):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    mat.use_backface_culling = False
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.8
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.15
    img = bpy.data.images.load(abs_path)
    img.filepath = tex_path_rel
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Closest"
    tex.location = (-500, 0)
    rnd = nt.nodes.new("ShaderNodeMath")
    rnd.operation = "ROUND"
    rnd.location = (-220, -200)
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], rnd.inputs[0])
    nt.links.new(rnd.outputs[0], b.inputs["Alpha"])
    return mat


# ------------------------------------------------------------------ 1) biblioteca
bpy.ops.wm.open_mainfile(filepath=src)
head = bpy.data.objects["Cabeca"]
coll = head.users_collection[0]
for nome in CORTES:
    ob = corte(nome, coll)
    ob.name = ob.data.name = f"Cabelo_{nome}"
    idx = tex_index(nome, ob["shell_dark"])
    for cor, pal in CORES.items():
        write_tex(idx, pal, os.path.join(out, "texturas", f"{nome}_{cor}.png"))
    print(nome, "faces", len(ob.data.polygons), "mechas", ob["mechas"])
lib_path = os.path.join(out, "_lib_cabelos.blend")
bpy.ops.wm.save_as_mainfile(filepath=lib_path, relative_remap=False)
if only_lib:
    sys.exit(0)

# ------------------------------------------------------------------ 2) 35 versoes
for i, nome in enumerate(CORTES):
    for cor in CORES:
        bpy.ops.wm.open_mainfile(filepath=src)
        with bpy.data.libraries.load(lib_path, link=False) as (data_from, data_to):
            data_to.objects = [f"Cabelo_{nome}"]
        ob = data_to.objects[0]
        ob.name = ob.data.name = "Cabelo"
        head = bpy.data.objects["Cabeca"]
        head.users_collection[0].objects.link(ob)
        ob.parent = head
        ob.matrix_parent_inverse = head.matrix_world.inverted()
        for k in ("mechas", "shell_dark"):
            if k in ob:
                del ob[k]
        ob["corte"], ob["cor"] = nome, cor
        mat = hair_material("Cabelo", f"//texturas/{nome}_{cor}.png", os.path.join(out, "texturas", f"{nome}_{cor}.png"))
        ob.data.materials.clear()
        ob.data.materials.append(mat)
        for im in bpy.data.images:
            if im.filepath.endswith("skin.png"):
                im.filepath = "//../rostos/skin.png"
            elif im.filepath.endswith("rostos_atlas.png"):
                im.filepath = "//../rostos/rostos_atlas.png"
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, f"{i + 1:02d}-{nome}_{cor}.blend"), relative_remap=False)
print("ok")
