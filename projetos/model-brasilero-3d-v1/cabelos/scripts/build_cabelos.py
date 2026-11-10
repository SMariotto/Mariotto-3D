"""Gera os 7 cortes x 5 cores (35 versoes) sobre o model-brasilero-3d-rostos.

Uso: python3 build_cabelos.py <model-brasilero-3d-rostos.blend> <pasta_saida cabelos/> [so_lib]

Saida:
  cabelos/<NN>-<corte>_<cor>.blend   (35 arquivos; leem //texturas/..., //../rostos/skin.png e //../rostos/rostos_atlas.png)
  cabelos/texturas/<corte>_<cor>.png (64x64, pixel, tons em degraus)
  cabelos/_lib_cabelos.blend         (os 7 cortes num arquivo so, usado para montar as versoes)
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
import bpy
from mathutils import Vector
from PIL import Image

import hair_lib as H

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
PART_A = -0.75      # risca do liso (lado direito do boneco)


def lerp(a, b, t):
    return a + (b - a) * max(0.0, min(1.0, t))


def front(a, w=0.9):
    return max(0.0, 1 - abs(a) / w)


# ------------------------------------------------------------------ cortes
def corte(nome, coll):
    if nome == "liso-repartido":
        hl = H.hairline_from_scalp(lift=lambda a: -0.0012 * max(0.0, math.sin(a)) if abs(a) < 1.0 else 0.0)

        def th(a, t):
            v = lerp(0.0052, 0.0036, (t - 0.55) / 0.45)
            v += 0.0022 * front(a, 1.0) * max(0, (t - 0.7) / 0.3)          # franja com volume
            if abs(a - PART_A) < 0.2 and t < 0.6:
                v -= 0.0022 * (1 - abs(a - PART_A) / 0.2)                  # risca
            return v
        h = H.Hair("Cabelo", cols=22, rings=7, hairline=hl, seed=1)
        h.shell(th)
        # 3 mechas da franja varrendo para o lado esquerdo do boneco
        for i, (c0, c1) in enumerate(((9, 12), (10, 13), (11, 14))):
            p0 = h.grid[(c0, 5)].co
            p1 = h.grid[(c1, 7)].co + Vector((0, -0.0035, -0.004))
            mid = (p0 + p1) / 2 + Vector((0, -0.004, 0.001))
            h.lock([p0, mid, p1], 0.0045, (c0 + 0.5) / h.cols, 0.55, 0.85)
    elif nome == "jogador-degrade":
        def th(a, t):
            side = max(0.0, min(1.0, (abs(a) - 0.75) / 0.35))       # 0 na frente, 1 nas laterais/nuca
            thin = lerp(0.0065, 0.0022, (t - 0.42) / 0.18)
            return lerp(0.0062, thin, side)
        h = H.Hair("Cabelo", cols=28, rings=9, seed=2)
        h.shell(th)
        # mechas curtas para frente no topo da franja
        for c in range(h.cols):
            a = h.a_of(c)
            if abs(a) < 0.75 and c % 2 == 0:
                h.spike(c, 3, 0.011, tilt=Vector((0, -1.2, -0.1)), width=0.0055, sides=4, twist=0.4 * c)
            elif abs(a) < 1.4 and c % 3 == 0:
                h.spike(c, 3, 0.007, tilt=Vector((0, -0.6, 0.3)), width=0.005, sides=4)
    elif nome == "raspado":
        hl = H.hairline_from_scalp()

        def th(a, t):
            return lerp(0.0026, 0.0018, (t - 0.8) / 0.2)
        h = H.Hair("Cabelo", cols=30, rings=9, hairline=hl, seed=3)
        h.shell(th)
    elif nome == "cacheado-curto":
        def th(a, t):
            return lerp(0.0078, 0.0045, (t - 0.6) / 0.4) + 0.0015 * front(a) * (t > 0.75)
        h = H.Hair("Cabelo", cols=24, rings=8, seed=4)
        h.shell(th, jitter=0.0018)
        rng = random.Random(44)
        for c in range(h.cols):
            for k in range(1, 8):
                if rng.random() < 0.42:
                    h.spike(c, k, rng.uniform(0.0024, 0.0034), width=rng.uniform(0.0042, 0.0052),
                            sides=6, twist=rng.random() * 6)
    elif nome == "crespo-curto":
        def th(a, t):
            return lerp(0.0115, 0.0075, (t - 0.35) / 0.4) if t < 0.86 else lerp(0.0075, 0.0028, (t - 0.86) / 0.14)
        h = H.Hair("Cabelo", cols=24, rings=9, seed=5)
        h.shell(th, jitter=0.0009)
    elif nome == "espetado-gel":
        def th(a, t):
            return lerp(0.0034, 0.0022, (t - 0.6) / 0.4)
        h = H.Hair("Cabelo", cols=22, rings=7, seed=6)
        h.shell(th)
        rng = random.Random(66)
        for c in range(h.cols):
            a = h.a_of(c)
            for k in (1, 2, 3, 4):
                if abs(a) > 2.5 and k > 2:
                    continue
                if (c + k) % 2:
                    continue
                if abs(a) < 0.8:
                    tilt = Vector((0, -0.25, 0.9))       # frente: pra cima e um pouco pra frente
                else:
                    tilt = Vector((0, 0.45, 0.8))        # resto: pra cima e pra tras
                h.spike(c, k, rng.uniform(0.011, 0.016) * (1.1 if k <= 2 else 0.85), tilt=tilt,
                        width=0.0058, sides=4, twist=rng.random())
    elif nome == "mullet":
        def th(a, t):
            v = 0.0048 if abs(a) < 0.9 else (0.0024 if abs(a) < 2.1 else lerp(0.0024, 0.0052, (abs(a) - 2.1) / 0.5))
            v += 0.0018 * front(a) * max(0, (t - 0.7) / 0.3)
            return lerp(v, 0.003, (t - 0.85) / 0.15) if abs(a) < 2.2 else v

        def extra(a, j):
            if abs(a) < 2.05:
                return None
            n_max = 4 if abs(a) > 2.45 else 2
            if j > n_max:
                return None
            out_dir = Vector((math.sin(a), -math.cos(a), 0)).normalized()
            return Vector((0, 0, -0.0095)) + out_dir * (0.0016 if j == 1 else 0.0006)
        h = H.Hair("Cabelo", cols=26, rings=8, seed=7)
        h.shell(th, extra_rings=extra)
    else:
        raise ValueError(nome)
    ob = h.to_object(coll)
    ob["corte"] = nome
    ob["v_rings"] = h.R_total + 1
    ob["rings"] = h.rings
    return ob


# ------------------------------------------------------------------ texturas (indices 0..3, 4 = transparente)
def tex_index(nome, ob):
    rng = random.Random(hash(nome) % 1000)
    W = Hh = H.TEX
    idx = [[1] * W for _ in range(Hh)]
    vr, rings = ob["v_rings"], ob["rings"]
    lip_y = int(Hh * (vr - 1) / vr)          # daqui pra baixo e a borda dobrada
    line_y = int(Hh * rings / vr)            # linha do cabelo (onde comeca o mullet)

    def streaks(dark_p=0.2, hi_band=(8, 16)):
        col_base = []
        b = 1
        for x in range(W):
            if rng.random() < 0.35:
                b = 2 if b == 1 else 1
            col_base.append(b)
        for x in range(W):
            dark = rng.random() < dark_p
            hb0 = hi_band[0] + rng.randint(-2, 2)
            hb1 = hi_band[1] + rng.randint(-2, 2)
            for y in range(Hh):
                v = col_base[x]
                if dark and y > 3:
                    v = 0
                if hb0 <= y <= hb1 and not dark:
                    v = min(3, v + 1)
                idx[y][x] = v

    def stipple(levels=(1, 2), dark=0.12, hi=0.06):
        for y in range(Hh):
            for x in range(W):
                r = rng.random()
                v = rng.choice(levels)
                if r < dark:
                    v = 0
                elif r < dark + hi and y < Hh * 0.45:
                    v = 3
                idx[y][x] = v

    if nome in ("liso-repartido", "mullet", "jogador-degrade", "espetado-gel"):
        streaks(0.18 if nome != "espetado-gel" else 0.25)
    elif nome == "raspado":
        stipple((1, 2, 2), 0.10, 0.10)
    elif nome == "cacheado-curto":
        stipple((1, 1, 2), 0.08, 0.0)
        for _ in range(170):  # cachinhos em "c"
            cx, cy = rng.randrange(W), rng.randrange(Hh)
            for dx, dy, v in ((0, 0, 0), (1, 0, 0), (-1, 1, 0), (-1, 2, 0), (0, 3, 0), (1, 3, 0),
                              (0, 1, 2), (0, 2, 2), (1, 1, 3 if cy < Hh * 0.5 else 2)):
                idx[(cy + dy) % Hh][(cx + dx) % W] = v
    elif nome == "crespo-curto":
        stipple((0, 1, 1), 0.18, 0.05)
        for _ in range(260):
            x, y = rng.randrange(W), rng.randrange(Hh)
            if y < Hh * 0.6:
                idx[y][x] = 2
    # risca do liso: linha transparente (aparece o couro cabeludo)
    if nome == "liso-repartido":
        up = (PART_A + math.pi) / (2 * math.pi)
        xp = int(up * W)
        for y in range(0, int(Hh * 0.62 * rings / vr)):
            idx[y][xp] = 4
    # degrade: laterais rareiam ate sumir (pontilhado)
    if nome == "jogador-degrade":
        y0 = int(Hh * 0.52 * rings / vr)
        for y in range(y0, Hh):
            t = (y - y0) / max(1, (lip_y - y0))
            for x in range(W):
                a = (x + 0.5) / W * 2 * math.pi - math.pi
                side = max(0.0, min(1.0, (abs(a) - 0.75) / 0.35))
                if side <= 0:
                    continue
                tt = t * side
                v = idx[y][x]
                if v == 3:
                    v = 2
                if rng.random() < tt * 0.85:
                    v = 4
                elif rng.random() < 0.5:
                    v = 0
                idx[y][x] = v
    # sombra perto da linha do cabelo e borda escura
    for y in range(Hh):
        for x in range(W):
            if idx[y][x] == 4:
                continue
            if y >= lip_y:
                idx[y][x] = 0
            elif y >= lip_y - 2 and idx[y][x] > 0:
                idx[y][x] -= 1
    if nome == "mullet":   # pontas do mullet um pouco mais claras
        for y in range(line_y, lip_y):
            for x in range(W):
                if idx[y][x] == 1 and rng.random() < 0.3:
                    idx[y][x] = 2
    return idx


def write_tex(idx, pal, path):
    img = Image.new("RGBA", (H.TEX, H.TEX))
    px = img.load()
    for y, row in enumerate(idx):
        for x, v in enumerate(row):
            px[x, y] = (0, 0, 0, 0) if v == 4 else (*pal[v], 255)
    img.save(path)


# ------------------------------------------------------------------ material
def hair_material(name, tex_path_rel, abs_path):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    if hasattr(mat, "surface_render_method"):
        mat.surface_render_method = "DITHERED"
    mat.use_backface_culling = False
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.85
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.1
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


# ------------------------------------------------------------------ 1) biblioteca com os 7 cortes
bpy.ops.wm.open_mainfile(filepath=src)
head = bpy.data.objects["Cabeca"]
coll = head.users_collection[0]
lib_objs = {}
for i, nome in enumerate(CORTES):
    ob = corte(nome, coll)
    ob.name = f"Cabelo_{nome}"
    ob.data.name = f"Cabelo_{nome}"
    lib_objs[nome] = ob
    idx = tex_index(nome, ob)
    for cor, pal in CORES.items():
        write_tex(idx, pal, os.path.join(out, "texturas", f"{nome}_{cor}.png"))
    print(nome, "faces", len(ob.data.polygons))
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
        ob.name = "Cabelo"
        ob.data.name = "Cabelo"
        head = bpy.data.objects["Cabeca"]
        head.users_collection[0].objects.link(ob)
        ob.parent = head
        ob.matrix_parent_inverse = head.matrix_world.inverted()
        ob["corte"] = nome
        ob["cor"] = cor
        for k in ("v_rings", "rings"):
            if k in ob:
                del ob[k]
        tex_rel = f"//texturas/{nome}_{cor}.png"
        mat = hair_material("Cabelo", tex_rel, os.path.join(out, "texturas", f"{nome}_{cor}.png"))
        ob.data.materials.clear()
        ob.data.materials.append(mat)
        for im in bpy.data.images:
            if im.filepath.endswith("skin.png"):
                im.filepath = "//../rostos/skin.png"
            elif im.filepath.endswith("rostos_atlas.png"):
                im.filepath = "//../rostos/rostos_atlas.png"
        fn = f"{i + 1:02d}-{nome}_{cor}.blend"
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, fn), relative_remap=False)
print("ok")
