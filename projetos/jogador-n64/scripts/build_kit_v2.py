"""Jogador low-poly (estilo N64) com uniforme de futebol, a partir do modelo sem espada/escudo.

Uso: python3 build_kit_v2.py <model-by-samuel.blend sem espada/escudo> <pasta_saida>

O que faz:
- remove gorro, cabelo antigo e orelhas pontudas; cria cabelo curto novo (peca unica, textura de fios)
- rosto novo pintado do zero (olhos castanho-escuros, sobrancelhas pretas, nariz e boca neutros)
- orelhas humanas low-poly
- pele em tom mais vivo (todas as texturas de pele refeitas/recoloridas)
- camisa preta (textura original da tunica recolorida, mantendo as dobras)
- bermuda branca nova: elastico na barra da camisa, quadril, gancho e barra nas coxas
- chuteiras brancas com sola, cravos e lingua/cadarco em relevo
Todas as texturas ficam em <saida>/textures com caminho relativo (//textures/...).
Parametros ajustaveis por variavel de ambiente (veja os os.environ.get abaixo).
"""
import math
import os
import sys

import bpy
import bmesh  # precisa vir depois de bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from PIL import Image

src_blend, out_dir = sys.argv[1], sys.argv[2]
src_tex = os.path.join(os.path.dirname(os.path.abspath(src_blend)), "textures")
TEX = os.path.join(out_dir, "textures")
os.makedirs(TEX, exist_ok=True)


def env(name, default):
    return float(os.environ.get(name, default))


# ======================================================================
# Texturas
# ======================================================================
def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(len(a)))


def ramp(t, stops):
    t = max(stops[0][0], min(stops[-1][0], t))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            return lerp(c0, c1, (t - t0) / (t1 - t0) if t1 > t0 else 0)
    return stops[-1][1]


def lum(p):
    return (0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]) / 255


SKIN_STOPS = [
    (0.35, (124, 72, 52)), (0.45, (164, 102, 76)), (0.58, (200, 136, 104)),
    (0.76, (224, 166, 130)), (0.85, (240, 186, 150)), (0.92, (248, 204, 170)), (1.0, (252, 220, 192)),
]
SKIN = ramp(0.85, SKIN_STOPS)        # base
SKIN_S1 = ramp(0.76, SKIN_STOPS)     # sombra leve
SKIN_S2 = ramp(0.60, SKIN_STOPS)     # sombra
SKIN_HI = ramp(0.92, SKIN_STOPS)     # luz
HAIR_D, HAIR_M, HAIR_L = (14, 12, 12), (30, 25, 24), (58, 49, 46)


def h(x, y, s=0):
    """ruido deterministico 0..1"""
    n = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 0xFFFF


def save(img, name):
    p = os.path.join(TEX, name)
    img.save(p)
    return p


def recolor(src_name, fn):
    im = Image.open(os.path.join(src_tex, src_name)).convert("RGBA")
    px = im.load()
    ls = [lum(px[x, y]) for y in range(im.height) for x in range(im.width)]
    lo, hi = min(ls), max(ls)
    for y in range(im.height):
        for x in range(im.width):
            p = px[x, y]
            c = fn(lum(p), (lum(p) - lo) / (hi - lo + 1e-6))
            px[x, y] = (*c, p[3])
    return im


def tex_face_eye():
    """substitui a textura do olho (32x32). No modelo a textura aparece invertida na vertical:
    linhas de baixo da imagem = parte de cima do olho no rosto."""
    im = Image.new("RGBA", (32, 32), (*SKIN, 255))
    px = im.load()
    # sombra suave da orbita
    for y in range(5, 17):
        for x in range(8, 25):
            if ((x - 16) / 8.5) ** 2 + ((y - 11) / 6.0) ** 2 < 1:
                px[x, y] = (*SKIN_S1, 255)
    # esclera (amendoa), mais aberta
    for y in range(6, 15):
        for x in range(10, 23):
            if ((x - 16) / 5.8) ** 2 + ((y - 10.3) / 3.4) ** 2 < 1:
                px[x, y] = (240, 236, 230, 255)
    # iris castanho-escura com pupila e brilho
    for y in range(7, 14):
        for x in range(12, 21):
            d = ((x - 16) / 3.0) ** 2 + ((y - 10.4) / 3.1) ** 2
            if d < 1:
                px[x, y] = (96, 56, 34, 255) if d > 0.55 else (62, 36, 22, 255) if d > 0.2 else (22, 13, 9, 255)
    px[15, 9] = px[14, 9] = (252, 248, 242, 255)
    # palpebra superior fina (linha de baixo da imagem) + canto externo
    for x in range(10, 23):
        px[x, 14 if 11 <= x <= 21 else 13] = (44, 28, 22, 255)
    px[22, 13] = px[23, 12] = (44, 28, 22, 255)
    # palpebra inferior bem suave
    for x in range(12, 21):
        px[x, 6] = (*SKIN_S1, 255)
    # sobrancelha: arco fino e relaxado, cor do cabelo
    for x in range(3, 24):
        t = (x - 3) / 20
        yc = 21.5 - 2.6 * t - 1.2 * math.sin(math.pi * t)
        thick = 1.6 if 0.15 < t < 0.85 else 1.0
        for y in range(15, 26):
            d = abs(y - yc)
            if d < thick * 0.6:
                px[x, y] = (*HAIR_M, 255)
            elif d < thick:
                px[x, y] = (*lerp(HAIR_M, SKIN_S2, 0.55), 255)
    return save(im, "rosto_olho.png")


def tex_face_mouth():
    """substitui a textura de nariz/boca (32x32), tambem invertida na vertical no modelo."""
    im = Image.new("RGBA", (32, 32), (*SKIN, 255))
    px = im.load()
    # nariz: luz no dorso, sombra embaixo (narinas)
    for y in range(12, 16):
        for x in range(14, 19):
            px[x, y] = (*SKIN_HI, 255)
    for x in range(13, 20):
        px[x, 16] = (*SKIN_S1, 255)
    px[14, 17] = px[18, 17] = (*SKIN_S2, 255)
    # boca: linha curta, cantos levemente para cima no modelo
    lip_line, lip_low = (150, 82, 70), (206, 132, 112)
    for x in range(12, 21):
        px[x, 23] = (*lip_line, 255)
    px[11, 24] = px[21, 24] = (*lerp(lip_line, SKIN, 0.4), 255)
    for x in range(13, 20):
        px[x, 22] = (*lip_low, 255)
    for x in range(14, 19):
        px[x, 21] = (*lerp(lip_low, SKIN, 0.5), 255)
    return save(im, "rosto_boca.png")


def tex_skin_plain(name, base):
    im = Image.new("RGBA", (16, 16), (*base, 255))
    px = im.load()
    for y in range(16):
        for x in range(16):
            r = h(x, y, 3)
            if r > 0.94:
                px[x, y] = (*lerp(base, SKIN_HI, 0.35), 255)
            elif r < 0.05:
                px[x, y] = (*lerp(base, SKIN_S1, 0.35), 255)
    return save(im, name)


def tex_hair():
    """fios verticais (v = altura na cabeca), 32x32."""
    im = Image.new("RGBA", (32, 32), (*HAIR_M, 255))
    px = im.load()
    for x in range(32):
        col = h(x, 0, 4)
        for y in range(32):
            k = 0.55 * col + 0.45 * h(x, y // 3, 5)
            c = HAIR_D if k < 0.33 else HAIR_M if k < 0.72 else HAIR_L
            if y >= 26 and h(x, y, 6) > 0.6:  # pontas mais escuras perto da borda inferior da imagem
                c = HAIR_D
            px[x, y] = (*c, 255)
    return save(im, "cabelo.png")


def tex_shorts():
    """32x32: v=1 (linha 0) = cintura. Elastico nas linhas 0-5, vinco na 6, dobras perto da barra."""
    base, band, crease, fold = (234, 234, 236), (244, 244, 246), (190, 190, 196), (214, 214, 220)
    im = Image.new("RGBA", (32, 32), (*base, 255))
    px = im.load()
    for y in range(32):
        for x in range(32):
            if y <= 5:
                c = band if y not in (0, 5) else lerp(band, crease, 0.35)
            elif y == 6:
                c = crease
            else:
                c = base
                # dobras verticais que nascem na barra e somem para cima
                f = h(x, 0, 7)
                if f > 0.72 and y > 31 - int(6 + 14 * h(x, 1, 8)):
                    c = fold
                if y == 31:
                    c = lerp(base, crease, 0.5)
            px[x, y] = (*c, 255)
        px[0, y] = px[16, y] = (*lerp(base, crease, 0.35), 255)  # costuras laterais
    return save(im, "bermuda.png")


def tex_boot():
    base, shade, crease = (238, 238, 240), (214, 214, 220), (196, 196, 204)
    im = Image.new("RGBA", (32, 32), (*base, 255))
    px = im.load()
    for y in range(32):
        for x in range(32):
            c = base
            if y > 24:
                c = lerp(base, shade, (y - 24) / 7)
            if h(x, y, 9) > 0.95:
                c = shade
            px[x, y] = (*c, 255)
    for x in range(6, 26):  # dois vincos suaves (couro dobrando)
        px[x, 14 + (x % 3 == 0)] = (*crease, 255)
        px[x + 2 if x < 24 else x, 18] = (*shade, 255)
    return save(im, "chuteira.png")


T = {
    "eye": tex_face_eye(),
    "mouth": tex_face_mouth(),
    "skin": tex_skin_plain("pele.png", SKIN),
    "skin_shade": tex_skin_plain("pele_sombra.png", SKIN_S1),
    "hair": tex_hair(),
    "shorts": tex_shorts(),
    "boot": tex_boot(),
    "hand": save(recolor("54641CCF_c.png", lambda l, t: ramp(l, SKIN_STOPS)), "mao.png"),
    "jersey": save(recolor("63297E4D_c.png", lambda l, t: lerp((12, 12, 14), (74, 74, 82), t)), "camisa.png"),
    "sleeve": save(recolor("23ED79E2_c.png", lambda l, t: lerp((12, 12, 14), (74, 74, 82), t)), "manga.png"),
}

# ======================================================================
# Cena
# ======================================================================
bpy.ops.wm.open_mainfile(filepath=src_blend)
OB = bpy.data.objects
IMGS = {}


def image(key):
    if key not in IMGS:
        img = bpy.data.images.load(T[key])
        img.filepath = "//textures/" + os.path.basename(T[key])
        IMGS[key] = img
    return IMGS[key]


def tex_mat(name, key):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 1.0
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.0
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = image(key)
    t.interpolation = "Closest"
    t.location = (-300, 0)
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    return m


def flat_mat(name, rgb8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    f = lambda c: ((c / 255 + 0.055) / 1.055) ** 2.4 if c / 255 > 0.04045 else c / 255 / 12.92
    col = (f(rgb8[0]), f(rgb8[1]), f(rgb8[2]), 1)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = 0.9
    m.diffuse_color = col
    return m


M = {
    "eye": tex_mat("Pele_Rosto", "eye"),
    "mouth": tex_mat("Rosto_Boca", "mouth"),
    "skin": tex_mat("Pele", "skin"),
    "skin_shade": tex_mat("Pele_Sombra", "skin_shade"),
    "hand": tex_mat("Maos", "hand"),
    "hair": tex_mat("Cabelo", "hair"),
    "jersey": tex_mat("Camisa", "jersey"),
    "sleeve": tex_mat("Camisa_Manga", "sleeve"),
    "shorts": tex_mat("Bermuda", "shorts"),
    "boot": tex_mat("Chuteira", "boot"),
    "sole": flat_mat("Chuteira_Sola", (200, 200, 206)),
    "stud": flat_mat("Chuteira_Cravo", (72, 72, 78)),
    "lace": flat_mat("Chuteira_Cadarco", (252, 252, 252)),
    "tongue": flat_mat("Chuteira_Lingua", (176, 176, 184)),
}

# troca de material por hash da textura original
BY_HASH = {
    "68EF4A2": "eye", "1FC43BAA": "mouth", "54641CCF": "hand",
    "63297E4D": "jersey", "23ED79E2": "sleeve", "4E1A6C27": "boot", "3ABAC9F9": "hair",
}
for o in list(OB):
    if o.type != "MESH":
        continue
    for i, m in enumerate(o.data.materials):
        for hsh, key in BY_HASH.items():
            if m and hsh in m.name:
                o.data.materials[i] = M[key]
for n in ("Mesh.006", "Mesh.007"):  # pernas: pele lisa (a textura antiga era meia-calca)
    for i in range(len(OB[n].data.materials)):
        OB[n].data.materials[i] = M["skin"]


def new_obj(name, bm, mats):
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(o)
    for m in mats:
        me.materials.append(m)
    return o


def set_uv(bm, fn):
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        us = [fn(l.vert.co) for l in f.loops]
        # costura: evita face esticada quando u da a volta
        mx = max(u[0] for u in us)
        us = [(u[0] + 1 if mx - u[0] > 0.5 else u[0], u[1]) for u in us]
        for l, u in zip(f.loops, us):
            l[uv].uv = u


# ======================================================================
# Cabeca: tira gorro, cabelo antigo e orelhas pontudas
# ======================================================================
head = OB["Mesh.003"]
mw = head.matrix_world
bm = bmesh.new()
bm.from_mesh(head.data)
tips = [v for v in bm.verts if abs((mw @ v.co).x) > 0.055]
ear_bases = []
for t in tips:
    ear_bases.append({v for f in t.link_faces for v in f.verts if v is not t})
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in (0, 3)], context="FACES_ONLY")
bmesh.ops.delete(bm, geom=tips, context="VERTS")
# pedacos de pele que ficavam escondidos pelo gorro na nuca (o cabelo novo cobre essa area)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if max((mw @ v.co).y for v in f.verts) > 0.03], context="FACES_ONLY")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
ear_centers = []
for base in ear_bases:
    base = [v for v in base if v.is_valid]
    if len(base) >= 3 and not any(set(f.verts) >= set(base[:3]) for f in base[0].link_faces):
        f = bm.faces.new(base[:3])
        f.material_index = 1
    ear_centers.append(sum((mw @ v.co for v in base), Vector()) / max(1, len(base)))
bm.normal_update()
bm.to_mesh(head.data)
skin_pts = [mw @ v.co for v in bm.verts]
bm.free()
head.data.materials[0] = M["hair"]
head.data.materials[3] = M["hair"]
smn = Vector([min(p[i] for p in skin_pts) for i in range(3)])
smx = Vector([max(p[i] for p in skin_pts) for i in range(3)])
print("cabeca sem cabelo/orelha:", [round(x, 3) for x in smn], [round(x, 3) for x in smx])
print("centro das orelhas antigas:", [[round(c, 3) for c in e] for e in ear_centers])

# ======================================================================
# Cabelo novo (corte curto, peca unica)
# ======================================================================
HC = Vector((env("HAIR_CX", 0.002), env("HAIR_CY", -0.004), env("HAIR_CZ", 0.384)))
HR = Vector((env("HAIR_RX", 0.054), env("HAIR_RY", 0.064), env("HAIR_RZ", 0.060)))
FRONT, SIDE, BACK = env("HAIR_FRONT", 0.409), env("HAIR_SIDE", 0.366), env("HAIR_BACK", 0.334)

bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=1.0)
for v in bm.verts:
    v.co = Vector((HC.x + v.co.x * HR.x, HC.y + v.co.y * HR.y, HC.z + v.co.z * HR.z))


def hairline(p):
    dy = max(-1, min(1, (p.y - HC.y) / HR.y))
    # frente (dy=-1) -> FRONT, lados (0) -> SIDE, nuca (+1) -> BACK
    return SIDE + (FRONT - SIDE) * max(0, -dy) ** 1.3 + (BACK - SIDE) * max(0, dy)


bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().z < hairline(f.calc_center_median())],
                 context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
# mechas: na borda, vertices alternados descem (franja e nuca)
edge = sorted([v for v in bm.verts if v.is_boundary], key=lambda v: math.atan2(v.co.y - HC.y, v.co.x - HC.x))
for i, v in enumerate(edge):
    dy = (v.co.y - HC.y) / HR.y
    if i % 2 == 0:
        drop = 0.009 if dy < -0.5 else 0.007 if dy > 0.3 else 0.005
        v.co.z -= drop
        # puxa a ponta levemente para dentro, colando na cabeca
        v.co.x = HC.x + (v.co.x - HC.x) * 0.96
        v.co.y = HC.y + (v.co.y - HC.y) * 0.96
# volume no topo (topete leve) para nao parecer capacete
for v in bm.verts:
    if v.co.z > HC.z + HR.z * 0.75:
        v.co.z += 0.004
set_uv(bm, lambda co: ((math.atan2(co.y - HC.y, co.x - HC.x) / (2 * math.pi) + 0.5) * 3,
                       (co.z - (HC.z - HR.z)) / (2 * HR.z)))
hair = new_obj("Cabelo", bm, [M["hair"]])

# ======================================================================
# Orelhas humanas
# ======================================================================
def make_ear(center, side):
    n = Vector((side, -0.30, 0.05)).normalized()   # face externa voltada para fora e um pouco para frente
    up = Vector((0, 0, 1))
    a_ax = up.cross(n).normalized() * side             # eixo frente-tras no plano da orelha
    b_ax = n.cross(a_ax).normalized() * side
    if b_ax.z < 0:
        b_ax = -b_ax
    bm = bmesh.new()
    N = 10
    outer, inner, base = [], [], []
    for k in range(N):
        th = 2 * math.pi * k / N + math.pi / 2
        a, b = math.cos(th), math.sin(th)
        sa = 0.0085 * (1.12 if b > 0 else 0.86)
        sb = 0.0135
        p = Vector(center) + a_ax * (a * sa + 0.002) + b_ax * (b * sb)
        outer.append(bm.verts.new(p + n * 0.0015))
        inner.append(bm.verts.new(Vector(center) + a_ax * (a * sa * 0.55 + 0.001) + b_ax * (b * sb * 0.6) - n * 0.0008))
        base.append(bm.verts.new(Vector(center) + a_ax * (a * sa * 0.6) + b_ax * (b * sb * 0.7) - n * 0.0070))
    c = bm.verts.new(Vector(center) + a_ax * (-0.0015) + b_ax * (-0.002) - n * 0.0025)
    rim, concha, back = [], [], []
    for k in range(N):
        k2 = (k + 1) % N
        rim.append(bm.faces.new((outer[k], outer[k2], inner[k2], inner[k])))
        concha.append(bm.faces.new((inner[k], inner[k2], c)))
        back.append(bm.faces.new((outer[k2], outer[k], base[k], base[k2])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    for f in concha:
        f.material_index = 1
    set_uv(bm, lambda co: (((co - Vector(center)).dot(a_ax) / 0.02) + 0.5, ((co - Vector(center)).dot(b_ax) / 0.03) + 0.5))
    return new_obj("Orelha." + ("L" if side > 0 else "R"), bm, [M["skin"], M["skin_shade"]])


EAR_Z, EAR_Y, EAR_X = env("EAR_Z", 0.367), env("EAR_Y", 0.012), env("EAR_X", 0.046)
for side in (1, -1):
    make_ear((HC.x + side * EAR_X, EAR_Y, EAR_Z), side)

# ======================================================================
# Bermuda nova (peca unica)
# ======================================================================
skirt = OB["Mesh.012"]
sk_mesh = skirt.data
bpy.data.objects.remove(skirt)
bpy.data.meshes.remove(sk_mesh)

BC = Vector((0.002, 0.001, 0))
WX, WY = env("WAIST_RX", 0.0525), env("WAIST_RY", 0.0435)
HX, HY = env("HIP_RX", 0.0585), env("HIP_RY", 0.0445)
Z_W, Z_B, Z_H = env("Z_WAIST", 0.229), env("Z_BAND", 0.213), env("Z_HIP", 0.196)
Z_CR, Z_HEM = env("Z_CROTCH", 0.172), env("Z_HEM", 0.150)
LEGC = {1: Vector((0.029, -0.008)), -1: Vector((-0.027, -0.008))}
LR = env("LEG_R", 0.0345)

bm = bmesh.new()
N = 12


def ring(z, rx, ry, cy=0.0):
    return [bm.verts.new((BC.x + rx * math.cos(2 * math.pi * k / N), BC.y + cy + ry * math.sin(2 * math.pi * k / N), z))
            for k in range(N)]


def bridge(r1, r2, closed=True):
    n = len(r1)
    for k in range(n if closed else n - 1):
        k2 = (k + 1) % n
        bm.faces.new((r1[k], r1[k2], r2[k2], r2[k]))


A0 = ring(Z_W - 0.003, WX * 0.90, WY * 0.90)    # borda interna do elastico
A = ring(Z_W, WX, WY)
B = ring(Z_B, WX * 1.01, WY * 1.01)
C = ring(Z_B - 0.0025, WX * 0.975, WY * 0.975)   # vinco abaixo do elastico
D = ring(Z_H, HX, HY, 0.002)
bridge(A0, A)
bridge(A, B)
bridge(B, C)
bridge(C, D)
X = bm.verts.new((BC.x - 0.001, BC.y - 0.002, Z_CR))
loops = {1: [D[k] for k in (9, 10, 11, 0, 1, 2, 3)] + [X], -1: [D[k] for k in (3, 4, 5, 6, 7, 8, 9)] + [X]}
for side, loop in loops.items():
    lc = LEGC[side]
    hem, lip = [], []
    for v in loop:
        d = Vector((v.co.x - lc.x, v.co.y - lc.y))
        d = d.normalized() if d.length > 1e-6 else Vector((-side, 0))
        hem.append(bm.verts.new((lc.x + d.x * LR, lc.y + d.y * LR * 1.03, Z_HEM)))
        lip.append(bm.verts.new((lc.x + d.x * LR * 0.86, lc.y + d.y * LR * 0.86, Z_HEM + 0.004)))
    bridge(loop, hem)
    bridge(hem, lip)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
set_uv(bm, lambda co: (math.atan2(co.y - BC.y, co.x - BC.x) / (2 * math.pi) + 0.5,
                       (co.z - (Z_HEM - 0.001)) / (Z_W - Z_HEM + 0.002)))
shorts = new_obj("Bermuda", bm, [M["shorts"]])

# ======================================================================
# Chuteiras: sola, cravos, lingua e cadarco
# ======================================================================
STUD_H, SOLE_T = 0.006, 0.003


def hull2d(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


for side, n in ((1, "Mesh.013"), (-1, "Mesh.009")):
    foot = OB[n]
    W = [foot.matrix_world @ v.co for v in foot.data.vertices]
    zmin = min(p.z for p in W)
    low = [(round(p.x, 5), round(p.y, 5)) for p in W if p.z < zmin + 0.012]
    hull = hull2d(low)
    cx = sum(p[0] for p in hull) / len(hull)
    cy = sum(p[1] for p in hull) / len(hull)
    xs, ys = [p[0] for p in W], [p[1] for p in W]
    L, Wd, ymin = max(ys) - min(ys), max(xs) - min(xs), min(ys)

    bm = bmesh.new()
    # sola
    top = [bm.verts.new((cx + (x - cx) * 1.04, cy + (y - cy) * 1.03, zmin + 0.0035)) for x, y in hull]
    bot = [bm.verts.new((cx + (x - cx) * 1.0, cy + (y - cy) * 1.0, zmin - SOLE_T + 0.0035)) for x, y in hull]
    bm.faces.new(top)
    bm.faces.new(list(reversed(bot)))
    for k in range(len(hull)):
        k2 = (k + 1) % len(hull)
        bm.faces.new((top[k], top[k2], bot[k2], bot[k]))
    sole_faces = list(bm.faces)
    # cravos (4 na frente, 2 no calcanhar)
    zs = zmin - SOLE_T + 0.0035
    spots = [(-0.26, 0.18), (0.26, 0.18), (-0.30, 0.40), (0.30, 0.40), (-0.22, 0.86), (0.22, 0.86)]
    stud_faces = []
    for fx, fy in spots:
        geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.0028, radius2=0.0036, depth=STUD_H,
                                     matrix=Matrix.Translation((cx + fx * Wd, ymin + fy * L, zs - STUD_H / 2)))
        stud_faces += [f for f in bm.faces if f not in sole_faces and f not in stud_faces]
    for f in stud_faces:
        f.material_index = 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    set_uv(bm, lambda co: (co.x * 10, co.y * 10))
    new_obj(f"Chuteira_Sola.{'L' if side > 0 else 'R'}", bm, [M["sole"], M["stud"]])

    # lingua e cadarco: projeta no peito do pe via raycast
    tris = [tuple(foot.matrix_world @ foot.data.vertices[i].co for i in p.vertices) for p in foot.data.polygons]
    verts, polys = [], []
    for tri in tris:
        polys.append(tuple(range(len(verts), len(verts) + len(tri))))
        verts += list(tri)
    bvh = BVHTree.FromPolygons(verts, polys)
    bm = bmesh.new()
    lace_faces = []
    ys_l = [ymin + L * t for t in (0.30, 0.38, 0.46, 0.54)]
    hits = []
    for y in [ymin + L * 0.26] + ys_l + [ymin + L * 0.60]:
        loc, nrm, _, _ = bvh.ray_cast(Vector((cx, y, 0.3)), Vector((0, 0, -1)))
        hits.append((y, loc, nrm))
    # lingua: tira fina seguindo a superficie
    strip = []
    for y, loc, nrm in hits:
        if loc is None:
            continue
        nrm = nrm if nrm.z > 0 else -nrm
        p = loc + nrm * 0.0008
        side_v = Vector((1, 0, 0))
        strip.append((bm.verts.new(p - side_v * Wd * 0.13), bm.verts.new(p + side_v * Wd * 0.13)))
    for (a0, a1), (b0, b1) in zip(strip, strip[1:]):
        bm.faces.new((a0, a1, b1, b0))
    tongue_faces = list(bm.faces)
    # passadas do cadarco (barras atravessadas, levemente em relevo)
    for y, loc, nrm in hits[1:-1]:
        if loc is None:
            continue
        nrm = nrm if nrm.z > 0 else -nrm
        rot = nrm.to_track_quat("Z", "Y").to_matrix().to_4x4()
        geom = bmesh.ops.create_cube(bm, size=1.0,
                                     matrix=Matrix.Translation(loc + nrm * 0.0016) @ rot @
                                     Matrix.Diagonal((Wd * 0.36, 0.0032, 0.0018, 1)))
    for f in bm.faces:
        if f not in tongue_faces:
            f.material_index = 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    set_uv(bm, lambda co: (co.x * 10, co.y * 10))
    new_obj(f"Chuteira_Cadarco.{'L' if side > 0 else 'R'}", bm, [M["tongue"], M["lace"]])

# levanta tudo para os cravos tocarem o chao (z=0)
lift = STUD_H + SOLE_T - 0.0035
for o in OB:
    o.location.z += lift

# nomes legiveis
RENAME = {"Mesh.003": "Cabeca", "Mesh.004": "Pescoco", "Mesh.001": "Camisa_Tronco", "Mesh": "Braco.L",
          "Mesh.005": "Braco.R", "Mesh.015": "Mao.L", "Mesh.011": "Mao.R", "Mesh.007": "Perna.L",
          "Mesh.006": "Perna.R", "Mesh.013": "Chuteira.L", "Mesh.009": "Chuteira.R"}
for old, new in RENAME.items():
    if old in OB:
        OB[old].name = new

for m in [m for m in bpy.data.materials if m.users == 0]:
    bpy.data.materials.remove(m)
for i in [i for i in bpy.data.images if i.users == 0]:
    bpy.data.images.remove(i)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "model-by-samuel.blend"), relative_remap=False)
print("objetos:", sorted(o.name for o in OB))
print("imagens:", sorted(i.filepath for i in bpy.data.images))
