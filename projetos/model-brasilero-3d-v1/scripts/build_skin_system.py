"""Sistema de skin (estilo Minecraft) sobre o boneco v7.

Uso: python3 build_skin_system.py <v7 model-by-samuel.blend> <pasta_saida>

- Refaz o UV de todas as pecas do corpo/roupa num atlas unico 128x128 (geometria nao muda).
- Um material "Skin" le //skin.png (trocar o PNG e apertar Alt+R no Blender atualiza o boneco).
- Gera: skin.png (skin de teste), template/areas_128.png, template/mapa_template_1024.png, template/layout.json.
- Careca: remove as mechas; a base do cabelo vira couro cabeludo (area propria no template).
"""
import json
import math
import os
import sys

import bpy
import bmesh  # depois de bpy
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
os.makedirs(os.path.join(out, "template"), exist_ok=True)
SZ = 128

# ---------------------------------------------------------------- layout (pixels, origem no canto superior esquerdo)
R = {
    "ROSTO": (0, 0, 48, 48),
    "CABECA_LADOS_TRAS": (48, 0, 48, 24),
    "COURO_CABELUDO": (48, 24, 48, 24),
    "ORELHA_ESQ": (96, 0, 16, 12), "ORELHA_DIR": (112, 0, 16, 12),
    "PESCOCO": (96, 12, 32, 8),
    "MAO_ESQ": (96, 20, 16, 14), "MAO_DIR": (112, 20, 16, 14),
    "CADARCO_ESQ": (96, 34, 16, 14), "CADARCO_DIR": (112, 34, 16, 14),
    "CAMISA_FRENTE": (0, 48, 40, 40), "CAMISA_COSTAS": (40, 48, 40, 40),
    "BRACO_ESQ": (80, 48, 48, 10), "BRACO_DIR": (80, 58, 48, 10),
    "BERMUDA_CINTURA": (80, 68, 48, 20),
    "BERMUDA_PERNA_ESQ": (0, 88, 24, 16), "BERMUDA_PERNA_DIR": (24, 88, 24, 16),
    "SOLA_ESQ": (0, 104, 24, 16), "SOLA_DIR": (24, 104, 24, 16),
    "CRAVOS_ESQ": (0, 120, 24, 8), "CRAVOS_DIR": (24, 120, 24, 8),
    "PERNA_ESQ": (48, 88, 20, 40), "PERNA_DIR": (68, 88, 20, 40),
    "CHUTEIRA_ESQ": (88, 88, 20, 26), "CHUTEIRA_DIR": (108, 88, 20, 26),
}
PAD = 1  # margem interna de cada area (evita vazar cor entre areas)

# ---------------------------------------------------------------- cores do skin de teste
C = {
    "pele": (242, 160, 172), "rosto": (18, 18, 20), "camisa": (34, 150, 64), "bermuda": (32, 72, 190),
    "chuteira": (24, 24, 26), "sola": (24, 24, 26), "cravo": (244, 244, 244),
    "lingua": (24, 24, 26), "cadarco": (24, 24, 26),
}

bpy.ops.wm.open_mainfile(filepath=src)
OB = bpy.data.objects

# careca: remove mechas, base do cabelo vira couro cabeludo
for n in ("Cabelo_Mechas",):
    if n in OB:
        me = OB[n].data
        bpy.data.objects.remove(OB[n])
        bpy.data.meshes.remove(me)
OB["Cabelo_Base"].name = "Couro_Cabeludo"

# papel de cada material antigo -> regiao/cor
ROLE = {
    "Pele_Rosto": "pele", "Rosto_Boca": "pele", "Pele": "pele", "Pele_Sombra": "pele", "Maos": "pele",
    "Cabelo_Base": "pele", "Camisa": "camisa", "Camisa_Manga": "camisa", "Bermuda": "bermuda",
    "Chuteira": "chuteira", "Chuteira_Sola": "sola", "Chuteira_Cravo": "cravo",
    "Chuteira_Lingua": "lingua", "Chuteira_Cadarco": "cadarco",
}


def role_of(o, f):
    m = o.data.materials[f.material_index] if o.data.materials else None
    name = m.name.split(".")[0] if m else ""
    return ROLE.get(name, "pele")


# ---------------------------------------------------------------- utilitarios de UV
def to_uv(region, a, b):
    """a,b em 0..1 dentro da area (a: esquerda->direita, b: cima->baixo) -> UV do Blender"""
    x, y, w, h = R[region]
    px = x + PAD + a * (w - 2 * PAD)
    py = y + PAD + b * (h - 2 * PAD)
    return (px / SZ, 1 - py / SZ)


def fit(vals_a, vals_b, keep_aspect=True):
    a0, a1 = min(vals_a), max(vals_a)
    b0, b1 = min(vals_b), max(vals_b)
    sa, sb = (a1 - a0) or 1e-6, (b1 - b0) or 1e-6
    return a0, b0, sa, sb


JOBS = []   # (obj, face_index, region, [uv por loop], cor)


def planar(o, faces, region, axis_a, axis_b, flip_a=False, keep_aspect=True):
    mw = o.matrix_world
    pts = {l.vert.index: mw @ l.vert.co for f in faces for l in f.loops}
    A = [p[axis_a] for p in pts.values()]
    B = [p[axis_b] for p in pts.values()]
    a0, b0, sa, sb = fit(A, B)
    if keep_aspect:
        x, y, w, h = R[region]
        rw, rh = w - 2 * PAD, h - 2 * PAD
        s = max(sa / rw, sb / rh)
        oa, ob = (rw - sa / s) / 2 / rw, (rh - sb / s) / 2 / rh
        fa = lambda v: oa + (v - a0) / s / rw
        fb = lambda v: ob + (v - b0) / s / rh
    else:
        fa = lambda v: (v - a0) / sa
        fb = lambda v: (v - b0) / sb
    for f in faces:
        uvs = []
        for l in f.loops:
            p = pts[l.vert.index]
            a = fa(p[axis_a])
            a = 1 - a if flip_a else a
            uvs.append(to_uv(region, a, 1 - fb(p[axis_b])))
        JOBS.append((o, f.index, region, uvs, role_of(o, f)))


def cylinder(o, faces, region, axis, center, start_angle=0.0, along_horizontal=False, flip=False):
    """axis: 'z' (vertical) ou 'x' (bracos). u = angulo, v = posicao no eixo."""
    mw = o.matrix_world
    raw = {}
    for f in faces:
        for l in f.loops:
            p = mw @ l.vert.co
            if axis == "z":
                ang = math.atan2(p.y - center[1], p.x - center[0])
                h = p.z
            else:
                ang = math.atan2(p.z - center[1], p.y - center[0])
                h = p.x
            t = ((ang - start_angle) / (2 * math.pi)) % 1.0
            raw[(f.index, l.index)] = (t, h)
    hs = [v[1] for v in raw.values()]
    h0, h1 = min(hs), max(hs)
    per_face = {}
    tmax = 1.0
    for f in faces:
        ts = [raw[(f.index, l.index)][0] for l in f.loops]
        if max(ts) - min(ts) > 0.5:
            ts = [t + 1 if t < 0.5 else t for t in ts]
        per_face[f.index] = ts
        tmax = max(tmax, max(ts))
    for f in faces:
        uvs = []
        for l, t in zip(f.loops, per_face[f.index]):
            h = (raw[(f.index, l.index)][1] - h0) / ((h1 - h0) or 1e-6)
            t = t / tmax
            if flip:
                h = 1 - h
            if along_horizontal:
                uvs.append(to_uv(region, h, t))
            else:
                uvs.append(to_uv(region, t, 1 - h))
        JOBS.append((o, f.index, region, uvs, role_of(o, f)))


def box(o, faces, region):
    """projecao em caixa: 3x2 celulas (+X, -X, -Y frente / +Y tras, +Z cima, -Z baixo)"""
    mw = o.matrix_world
    nm = mw.to_3x3().inverted().transposed()
    pts = [mw @ l.vert.co for f in faces for l in f.loops]
    mn = Vector([min(p[i] for p in pts) for i in range(3)])
    mx = Vector([max(p[i] for p in pts) for i in range(3)])
    sz = mx - mn
    cells = {"+X": (0, 0, 1, 2), "-X": (1, 0, 1, 2), "-Y": (2, 0, 0, 2), "+Y": (0, 1, 1, 2),
             "+Z": (1, 1, 0, 1), "-Z": (2, 1, 0, 1)}
    for f in faces:
        n = (nm @ f.normal).normalized()
        k = max(range(3), key=lambda i: abs(n[i]))
        key = ("+" if n[k] > 0 else "-") + "XYZ"[k]
        cx, cy, ia, ib = cells[key]
        uvs = []
        for l in f.loops:
            p = mw @ l.vert.co
            a = (p[ia] - mn[ia]) / (sz[ia] or 1e-6)
            b = 1 - (p[ib] - mn[ib]) / (sz[ib] or 1e-6)
            uvs.append(to_uv(region, (cx + a) / 3, (cy + b) / 2))
        JOBS.append((o, f.index, region, uvs, role_of(o, f)))


def faces_of(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    return bm


BMS = {}


def get(o):
    if o.name not in BMS:
        BMS[o.name] = faces_of(o)
    return BMS[o.name]


def wcenter(o, f):
    return o.matrix_world @ f.calc_center_median()


def wnormal(o, f):
    return (o.matrix_world.to_3x3().inverted().transposed() @ f.normal).normalized()


# ---------------------------------------------------------------- mapeamento por peca
head = OB["Cabeca"]
bm = get(head)
front = [f for f in bm.faces if wnormal(head, f).y < -0.35]
rest = [f for f in bm.faces if f not in front]
planar(head, front, "ROSTO", 0, 2)
hpts = [head.matrix_world @ v.co for v in bm.verts]
hc = (sum(p.x for p in hpts) / len(hpts), sum(p.y for p in hpts) / len(hpts))
cylinder(head, rest, "CABECA_LADOS_TRAS", "z", hc, start_angle=-math.pi / 2)

sc = OB["Couro_Cabeludo"]
cylinder(sc, list(get(sc).faces), "COURO_CABELUDO", "z", hc, start_angle=-math.pi / 2)

for side, n in (("ESQ", "Orelha.L"), ("DIR", "Orelha.R")):
    box(OB[n], list(get(OB[n]).faces), f"ORELHA_{side}")

nk = OB["Pescoco"]
npts = [nk.matrix_world @ v.co for v in get(nk).verts]
cylinder(nk, list(get(nk).faces), "PESCOCO", "z",
         (sum(p.x for p in npts) / len(npts), sum(p.y for p in npts) / len(npts)), start_angle=-math.pi / 2)

for side, n in (("ESQ", "Mao.L"), ("DIR", "Mao.R")):
    box(OB[n], list(get(OB[n]).faces), f"MAO_{side}")

for side, n in (("ESQ", "Chuteira_Cadarco.L"), ("DIR", "Chuteira_Cadarco.R")):
    box(OB[n], list(get(OB[n]).faces), f"CADARCO_{side}")

tor = OB["Camisa_Tronco"]
bm = get(tor)
planar(tor, [f for f in bm.faces if wnormal(tor, f).y <= 0], "CAMISA_FRENTE", 0, 2)
planar(tor, [f for f in bm.faces if wnormal(tor, f).y > 0], "CAMISA_COSTAS", 0, 2, flip_a=True)

for side, n in (("ESQ", "Braco.L"), ("DIR", "Braco.R")):
    o = OB[n]
    pts = [o.matrix_world @ v.co for v in get(o).verts]
    cy = sum(p.y for p in pts) / len(pts)
    cz = sum(p.z for p in pts) / len(pts)
    cylinder(o, list(get(o).faces), f"BRACO_{side}", "x", (cy, cz), along_horizontal=True, flip=(side == "DIR"))

sh = OB["Bermuda"]
bm = get(sh)
zs = [(sh.matrix_world @ v.co).z for v in bm.verts]
zcut = min(zs) + 0.56 * (max(zs) - min(zs))
spts = [sh.matrix_world @ v.co for v in bm.verts]
scx = sum(p.x for p in spts) / len(spts)
scy = sum(p.y for p in spts) / len(spts)
waist = [f for f in bm.faces if wcenter(sh, f).z >= zcut]
cylinder(sh, waist, "BERMUDA_CINTURA", "z", (scx, scy), start_angle=-math.pi / 2)
for side, sgn in (("ESQ", 1), ("DIR", -1)):
    fs = [f for f in bm.faces if wcenter(sh, f).z < zcut and (wcenter(sh, f).x - scx) * sgn > 0]
    pts = [sh.matrix_world @ l.vert.co for f in fs for l in f.loops]
    cylinder(sh, fs, f"BERMUDA_PERNA_{side}", "z",
             (sum(p.x for p in pts) / len(pts), sum(p.y for p in pts) / len(pts)), start_angle=-math.pi / 2)

for side, n in (("ESQ", "Perna.L"), ("DIR", "Perna.R")):
    o = OB[n]
    pts = [o.matrix_world @ v.co for v in get(o).verts]
    cylinder(o, list(get(o).faces), f"PERNA_{side}", "z",
             (sum(p.x for p in pts) / len(pts), sum(p.y for p in pts) / len(pts)), start_angle=-math.pi / 2)

for side, n in (("ESQ", "Chuteira.L"), ("DIR", "Chuteira.R")):
    box(OB[n], list(get(OB[n]).faces), f"CHUTEIRA_{side}")
for side, n in (("ESQ", "Chuteira_Sola.L"), ("DIR", "Chuteira_Sola.R")):
    o = OB[n]
    fs = list(get(o).faces)
    box(o, [f for f in fs if role_of(o, f) != "cravo"], f"SOLA_{side}")
    box(o, [f for f in fs if role_of(o, f) == "cravo"], f"CRAVOS_{side}")

# ---------------------------------------------------------------- grava UV e material unico
img_path = os.path.join(out, "skin.png")
mat = bpy.data.materials.new("Skin")
mat.use_nodes = True
nt = mat.node_tree
b = nt.nodes["Principled BSDF"]
b.inputs["Roughness"].default_value = 1.0
if "Specular IOR Level" in b.inputs:
    b.inputs["Specular IOR Level"].default_value = 0.0
tex = nt.nodes.new("ShaderNodeTexImage")
tex.interpolation = "Closest"
tex.location = (-300, 0)
nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])

by_obj = {}
for o, fi, region, uvs, role in JOBS:
    by_obj.setdefault(o.name, []).append((fi, uvs))
for name, items in by_obj.items():
    o = OB[name]
    bm = BMS[name]
    uvl = bm.loops.layers.uv.new("SkinUV")
    bm.faces.ensure_lookup_table()
    for fi, uvs in items:
        for l, uv in zip(bm.faces[fi].loops, uvs):
            l[uvl].uv = uv
    for f in bm.faces:
        f.material_index = 0
    bm.to_mesh(o.data)
    # deixa so o UV novo
    for layer in list(o.data.uv_layers):
        if layer.name != "SkinUV":
            o.data.uv_layers.remove(layer)
    o.data.uv_layers["SkinUV"].active = True
    o.data.uv_layers["SkinUV"].active_render = True
    o.data.materials.clear()
    o.data.materials.append(mat)

# ---------------------------------------------------------------- pinta o skin de teste (rasteriza cada face na cor do papel)
def raster(img, uvs, col):
    px = [(u * SZ, (1 - v) * SZ) for u, v in uvs]
    d = ImageDraw.Draw(img)
    for i in range(1, len(px) - 1):
        d.polygon([px[0], px[i], px[i + 1]], fill=col)


skin = Image.new("RGBA", (SZ, SZ), (0, 0, 0, 0))
for o, fi, region, uvs, role in JOBS:
    col = C["rosto"] if region == "ROSTO" else C[role]
    raster(skin, uvs, (*col, 255))
# area do rosto inteira preta (pedido do teste) e dilatacao de 1 px dentro de cada area
x, y, w, hh = R["ROSTO"]
ImageDraw.Draw(skin).rectangle([x, y, x + w - 1, y + hh - 1], fill=(*C["rosto"], 255))
for _ in range(2):
    src_px = skin.copy().load()
    px = skin.load()
    for (rx, ry, rw, rh) in R.values():
        for yy in range(ry, ry + rh):
            for xx in range(rx, rx + rw):
                if src_px[xx, yy][3] == 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = xx + dx, yy + dy
                        if rx <= nx < rx + rw and ry <= ny < ry + rh and src_px[nx, ny][3]:
                            px[xx, yy] = src_px[nx, ny]
                            break
skin.save(img_path)

img = bpy.data.images.load(img_path)
img.filepath = "//skin.png"
tex.image = img

# limpeza
for m in [m for m in bpy.data.materials if m.users == 0]:
    bpy.data.materials.remove(m)
for i in [i for i in bpy.data.images if i.users == 0]:
    bpy.data.images.remove(i)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "model-brasilero-3d-v1.blend"), relative_remap=False)

# ---------------------------------------------------------------- template
PAL = ["#f4a6a6", "#a6d8f4", "#b8f4a6", "#f4e0a6", "#d8a6f4", "#a6f4e6", "#f4c2a6", "#c9c9f4"]
areas = Image.new("RGBA", (SZ, SZ), (0, 0, 0, 0))
d = ImageDraw.Draw(areas)
for i, (k, (x, y, w, hh)) in enumerate(R.items()):
    c = PAL[i % len(PAL)]
    d.rectangle([x, y, x + w - 1, y + hh - 1], fill=c, outline="#303030")
areas.save(os.path.join(out, "template", "areas_128.png"))

S8 = 8
big = Image.new("RGBA", (SZ * S8, SZ * S8), (255, 255, 255, 255))
big.paste(skin.resize((SZ * S8, SZ * S8), Image.NEAREST), (0, 0), skin.resize((SZ * S8, SZ * S8), Image.NEAREST))
d = ImageDraw.Draw(big)
for o, fi, region, uvs, role in JOBS:  # malha (wireframe)
    pts = [(u * SZ * S8, (1 - v) * SZ * S8) for u, v in uvs]
    d.line(pts + [pts[0]], fill=(255, 255, 255, 140), width=1)
try:
    font = ImageFont.load_default(size=22)
    small = ImageFont.load_default(size=16)
except TypeError:
    font = small = ImageFont.load_default()
for k, (x, y, w, hh) in R.items():
    d.rectangle([x * S8, y * S8, (x + w) * S8 - 1, (y + hh) * S8 - 1], outline=(255, 200, 0, 255), width=3)
    label = k.replace("_", " ")
    tx, ty = x * S8 + 6, y * S8 + 4
    d.rectangle([tx - 3, ty - 2, tx + d.textlength(label, font=small) + 3, ty + 18], fill=(0, 0, 0, 200))
    d.text((tx, ty), label, fill=(255, 220, 60, 255), font=small)
    d.text((x * S8 + 6, (y + hh) * S8 - 20), f"x{x} y{y} {w}x{hh}px", fill=(255, 255, 255, 230), font=small)
big.save(os.path.join(out, "template", "mapa_template_1024.png"))
json.dump({k: {"x": x, "y": y, "w": w, "h": hh} for k, (x, y, w, hh) in R.items()},
          open(os.path.join(out, "template", "layout.json"), "w"), indent=2, ensure_ascii=False)
print("faces mapeadas:", len(JOBS), "objetos:", sorted(by_obj))
