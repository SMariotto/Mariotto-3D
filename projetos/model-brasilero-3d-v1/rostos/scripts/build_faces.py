"""Gera o atlas de rostos animados (pixel art, fundo transparente).

Uso: python3 build_faces.py <pasta_saida> [calib.json]

Atlas: rostos_atlas.png, 1200x240.
  - 5 blocos lado a lado (um por tipo de rosto), cada bloco 240x240.
  - Dentro do bloco: linha = animacao (5), coluna = quadro (5). Cada quadro 48x48.
  - Quadro 1 e 5 = rosto padrao, 3 = expressao completa, 2 e 4 = transicao.
O tom de pele NAO esta aqui: o fundo e transparente e a pele vem do skin.png.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
CAL = {"eye_y": 22, "eye_dx": 9, "brow_y": 16, "mouth_y": 35, "cx": 24}
if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
    CAL.update(json.load(open(sys.argv[2])))

CELL = 48
TIPOS = ["classico", "animado", "focado", "sardento", "tranquilo"]
ANIMS = ["piscada_um_olho", "piscada_dois_olhos", "forca", "dor", "felicidade"]

# ------------------------------------------------------------------ paleta
K = (44, 28, 22, 255)        # contorno
L = (150, 96, 78, 255)       # linha suave (palpebra de baixo, vinco)
W = (246, 242, 234, 255)     # branco do olho / dente
G = (196, 190, 182, 255)     # divisao dos dentes
P = (24, 16, 12, 255)        # pupila
H = (255, 255, 255, 255)     # brilho
R = (96, 26, 32, 255)        # dentro da boca
T = (214, 92, 96, 255)       # lingua
B = (232, 120, 120, 120)     # bochecha corada (semitransparente)
S = (150, 206, 255, 255)     # gota (suor/lagrima)
SH = (235, 248, 255, 255)    # brilho da gota
F = (176, 104, 70, 200)      # sarda

IRIS = {
    "classico": (110, 66, 36, 255),
    "animado": (70, 44, 28, 255),
    "focado": (96, 110, 52, 255),
    "sardento": (60, 40, 30, 255),
    "tranquilo": (76, 104, 140, 255),
}
BROW = {
    "classico": (64, 40, 26, 255),
    "animado": (52, 32, 22, 255),
    "focado": (40, 26, 18, 255),
    "sardento": (120, 72, 40, 255),
    "tranquilo": (70, 46, 30, 255),
}

# ------------------------------------------------------------------ olhos abertos (olho da ESQUERDA da imagem = olho direito do boneco)
# k contorno, w branco, i iris, p pupila, h brilho, l linha suave, . transparente
EYE = {
    "classico": [
        ".kkkkk.",
        "kwhipwk",
        "kwiipwk",
        ".wiiiw.",
        "..lll..",
    ],
    "animado": [
        ".kkkkk.",
        "kwhhipk",
        "kwhiipk",
        "kwiiipk",
        ".wiiiw.",
        "..lll..",
    ],
    "focado": [
        "kkkkkkk",
        ".whipw.",
        ".liiil.",
    ],
    "sardento": [
        ".kk.",
        "khpk",
        "kppk",
        ".kk.",
    ],
    "tranquilo": [
        "..kkk..",
        ".kkkkkk",
        "kwiipwk",
        ".wiiiw.",
        "..lll..",
    ],
}

# glifos de estado (mesma largura que o olho fica centralizado no mesmo ponto)
CLOSED = ["k....k", ".kkkk."]          # piscada fechada (curva para baixo)
HAPPY = [".kkkk.", "k....k"]           # ^ feliz
SQUEEZE = ["k....", ".kk..", "...kk", ".kk..", "k...."]  # > (espremido), espelhado no outro olho

# ------------------------------------------------------------------ bocas (centralizadas em cx, topo em mouth_y)
MOUTH = {
    "classico": ["l....l", ".kkkk."],
    "animado": ["k......k", ".k....k.", "..kkkk.."],
    "focado": ["kkkkk"],
    "sardento": ["k.....k", ".krrrk.", "..kkk.."],
    "tranquilo": ["lkkl"],
}
M_SMILE_S = ["k....k", ".kkkk."]
M_SMILE_M = ["k......k", ".kkkkkk."]
M_BIG = ["kkkkkkkkk", ".kwwwwwk.", ".krrrrrk.", "..krttk..", "...kkk..."]
M_GRIT_S = ["kkkkk", "kwgwk", "kkkkk"]
M_GRIT_L = [".kkkkkkk.", "kwwgwgwwk", "kwwgwgwwk", ".kkkkkkk."]
M_PAIN_S = [".k.k.", "k.k.k"]
M_PAIN_L = ["...kkk...", ".kkrrrkk.", "krrrrrrrk", "kkkkkkkkk"]
M_O = [".kk.", "krrk", ".kk."]

DROP = [".s.", "sss", "ssS", ".s."]
TEAR = ["s", "s", "S"]

CMAP = {"k": K, "l": L, "w": W, "g": G, "p": P, "h": H, "r": R, "t": T, "s": S, "S": SH}


def blit(px, grid, x0, y0, iris=None, mirror=False):
    for j, row in enumerate(grid):
        if mirror:
            row = row[::-1]
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            c = iris if ch == "i" else CMAP[ch]
            x, y = x0 + i, y0 + j
            if 0 <= x < CELL and 0 <= y < CELL:
                px[x, y] = c


def eye(px, tipo, side, state):
    """side: -1 = esquerda da imagem (olho direito do boneco), +1 = direita da imagem.
    state: 'open', 'half', 'closed', 'happy', 'squeeze', 'lowsquint'"""
    cx = CAL["cx"] + side * CAL["eye_dx"]
    ey = CAL["eye_y"]
    mirror = side > 0
    g = EYE[tipo]
    w, h = len(g[0]), len(g)
    x0 = cx - w // 2 if side < 0 else cx - (w - 1) // 2
    y0 = ey - h // 2
    iris = IRIS[tipo]
    if state == "open":
        blit(px, g, x0, y0, iris, mirror)
    elif state == "half":
        cut = max(1, (h + 1) // 2)
        rows = g[cut:]
        blit(px, ["k" * w], x0, y0 + cut - 1, iris, mirror)  # palpebra descendo
        blit(px, rows, x0, y0 + cut, iris, mirror)
    elif state == "lowsquint":  # bochecha sobe (transicao de felicidade)
        rows = g[:-1] if h > 3 else g
        blit(px, rows, x0, y0 + 1, iris, mirror)
        blit(px, ["." + "l" * (w - 2) + "."], x0, y0 + len(rows) + 1, iris, mirror)
    else:
        glyph = {"closed": CLOSED, "happy": HAPPY, "squeeze": SQUEEZE}[state]
        gw = len(glyph[0])
        gx = cx - gw // 2 if side < 0 else cx - (gw - 1) // 2
        gy = ey - len(glyph) // 2 + (0 if len(glyph) > 3 else 1)
        blit(px, glyph, gx, gy, iris, mirror)


def brow(px, tipo, side, raise_=0, tilt=0):
    """tilt > 0: ponta de dentro desce (bravo/forca). tilt < 0: ponta de dentro sobe (preocupado/dor)."""
    cx = CAL["cx"] + side * CAL["eye_dx"]
    y = CAL["brow_y"] - raise_
    c = BROW[tipo]
    spec = {  # (meia largura, espessura, arco)
        "classico": (3, 1, 0),
        "animado": (3, 1, 1),
        "focado": (3, 2, 0),
        "sardento": (2, 1, 0),
        "tranquilo": (3, 1, 1),
    }[tipo]
    hw, thick, arch = spec
    xs = list(range(cx - hw, cx + hw + 1))
    n = len(xs) - 1
    for k, x in enumerate(xs):
        # t: 0 na ponta de fora, 1 na ponta de dentro (perto do nariz)
        t = (k / n) if side < 0 else (1 - k / n)
        dy = round(tilt * t)
        if arch and 0 < k < n:
            dy -= 1 if abs(k - n / 2) < n / 2 - 0.5 else 0
        for th in range(thick):
            yy = y + dy + th
            if 0 <= x < CELL and 0 <= yy < CELL:
                px[x, yy] = c


def mouth(px, grid, dy=0):
    w = len(grid[0])
    x0 = CAL["cx"] - w // 2
    blit(px, grid, x0, CAL["mouth_y"] + dy)


def extras_base(px, tipo):
    if tipo == "sardento":
        y = CAL["eye_y"] + 5
        for x, yy in ((-6, 0), (-4, 1), (-7, 2), (4, 0), (6, 1), (3, 2)):
            px[CAL["cx"] + x, y + yy] = F


def blush(px, strong=True):
    y = CAL["eye_y"] + 5
    for side in (-1, 1):
        cx = CAL["cx"] + side * (CAL["eye_dx"] + 1)
        for dx in (-1, 0, 1) if strong else (0,):
            px[cx + dx, y] = B


# ------------------------------------------------------------------ estados de cada quadro
def face(tipo, anim, step):
    """step: 0 = padrao, 1 = transicao, 2 = expressao completa"""
    img = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    px = img.load()
    extras_base(px, tipo)
    eyeL = eyeR = "open"
    braise, btilt = 0, 0
    mth = MOUTH[tipo]
    mdy = 0
    extra = []
    if step > 0:
        full = step == 2
        if anim == "piscada_um_olho":
            eyeR = "closed" if full else "half"
            if full:
                mth = M_SMILE_S
                btilt = 0
        elif anim == "piscada_dois_olhos":
            eyeL = eyeR = "closed" if full else "half"
        elif anim == "forca":
            eyeL = eyeR = "squeeze" if full else "half"
            btilt = 2 if full else 1
            mth = M_GRIT_L if full else M_GRIT_S
            if full:
                extra.append("suor")
        elif anim == "dor":
            # dor: assimetrico (um olho espremido, o outro meio aberto) para nao confundir com forca
            eyeL, eyeR = ("squeeze", "half") if full else ("half", "half")
            btilt = -2 if full else -1
            braise = 1 if full else 0
            mth = M_PAIN_L if full else M_PAIN_S
            if full:
                extra.append("lagrima")
        elif anim == "felicidade":
            eyeL = eyeR = "happy" if full else "lowsquint"
            braise = 1
            mth = M_BIG if full else M_SMILE_M
            extra.append("corado" if full else "corado_leve")
    eye(px, tipo, -1, eyeL)
    eye(px, tipo, +1, eyeR)
    if tipo == "tranquilo" and step == 0:
        pass
    brow(px, tipo, -1, braise, btilt)
    brow(px, tipo, +1, braise, btilt)
    mouth(px, mth, mdy)
    if "corado" in extra:
        blush(px, True)
    if "corado_leve" in extra:
        blush(px, False)
    if "suor" in extra:
        blit(px, DROP, CAL["cx"] + CAL["eye_dx"] + 5, CAL["eye_y"] - 6)
    if "lagrima" in extra:
        blit(px, TEAR, CAL["cx"] - CAL["eye_dx"] - 3, CAL["eye_y"] + 2)
    return img


STEP_OF_FRAME = [0, 1, 2, 1, 0]

atlas = Image.new("RGBA", (CELL * 5 * len(TIPOS), CELL * len(ANIMS)), (0, 0, 0, 0))
for ti, tipo in enumerate(TIPOS):
    for ai, anim in enumerate(ANIMS):
        cache = {s: face(tipo, anim, s) for s in (0, 1, 2)}
        for fi, s in enumerate(STEP_OF_FRAME):
            atlas.paste(cache[s], (ti * 240 + fi * CELL, ai * CELL))
atlas.save(os.path.join(out, "rostos_atlas.png"))

meta = {
    "imagem": "rostos_atlas.png",
    "largura": atlas.width, "altura": atlas.height, "quadro": CELL,
    "fps": 10,
    "tipos": TIPOS, "animacoes": ANIMS, "quadros_por_animacao": 5,
    "como_achar_um_quadro": "x = tipo*240 + quadro*48, y = animacao*48 (pixels, origem no canto superior esquerdo; tudo comeca em 0)",
    "web_offset": "no glb o UV aponta para o quadro (0,0,0); offset.x = (tipo*5 + quadro)/25, offset.y = animacao/5 (three.js: material.map.offset)",
    "sequencia": "quadros 0,1,2,3,4 a 10 por segundo; 0 e 4 = rosto padrao, 2 = expressao completa",
}
json.dump(meta, open(os.path.join(out, "rostos.json"), "w"), indent=2, ensure_ascii=False)
print("atlas", atlas.size)
