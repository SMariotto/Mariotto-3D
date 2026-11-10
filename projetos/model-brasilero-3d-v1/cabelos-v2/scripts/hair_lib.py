"""Gerador de cabelos low-poly (estilo N64) para o model-brasilero-3d.

Cada corte = uma casca em grade (colunas ao redor da cabeca x aneis do topo ate a linha do cabelo),
colada no cranio por raios a partir do centro da cabeca, com espessura por regiao + detalhes
(franja, risca, mechas, cachos, espetos, mullet). UV: u = volta na cabeca (costura atras),
v = topo (0) ate a ponta (1). Textura 64x64 indexada (tons 0..3, 4 = transparente) + paleta por cor.
"""
import math
import random

import bpy
import bmesh  # depois de bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

C = Vector((0.002, -0.003, 0.385))   # centro de onde saem os raios
TEX = 64


def smooth_interp(pts, x):
    """pts: lista (x, y) ordenada; interpolacao suave (cosseno) e simetrica em |x|"""
    x = abs(x)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            t = (1 - math.cos(t * math.pi)) / 2
            return y0 + (y1 - y0) * t
    return pts[-1][1]


# linha do cabelo (z do mundo) por azimute: 0 = frente, pi = nuca, + = lado esquerdo do boneco
HAIRLINE = [(0.0, 0.399), (0.55, 0.397), (0.95, 0.392), (1.35, 0.376), (1.62, 0.372),
            (1.78, 0.389), (2.05, 0.392), (2.3, 0.389), (2.55, 0.366), (2.85, 0.354), (math.pi, 0.352)]


_EDGE = None


def scalp_edge():
    """linha da borda do couro cabeludo: lista (azimute, z minimo), suavizada"""
    global _EDGE
    if _EDGE is None:
        o = bpy.data.objects["Couro_Cabeludo"]
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.transform(o.matrix_world)
        bins = {}
        for e in bm.edges:
            if e.is_boundary:
                for i in range(9):
                    p = e.verts[0].co.lerp(e.verts[1].co, i / 8)
                    a = math.atan2(p.x - C.x, -(p.y - C.y))
                    b = round(a / 0.1)
                    bins[b] = min(bins.get(b, 9), p.z)
        bm.free()
        _EDGE = sorted((b * 0.1, z) for b, z in bins.items())
    return _EDGE


def hairline_from_scalp(margin=0.0012, ear=(1.68, 2.15), ear_z=0.3895, lift=None):
    """linha do cabelo = borda da careca um pouco abaixo (cobre a borda), mas acima das orelhas.
    lift(a) -> quanto subir em cada azimute (ex.: entradas do raspado)"""
    edge = scalp_edge()

    def f(a):
        z = None
        for (a0, z0), (a1, z1) in zip(edge, edge[1:]):
            if a0 <= a <= a1:
                z = z0 + (z1 - z0) * (a - a0) / (a1 - a0)
                break
        if z is None:
            z = edge[0][1] if a < edge[0][0] else edge[-1][1]
        z -= margin
        if ear[0] <= abs(a) <= ear[1]:
            z = max(z, ear_z)
        if lift:
            z += lift(a)
        return z
    return f


def build_bvh():
    objs = [bpy.data.objects[n] for n in ("Couro_Cabeludo", "Cabeca")]
    verts, polys = [], []
    for o in objs:
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in o.data.vertices]
        polys += [[base + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys)


def surf_dist(bvh, d):
    """maior distancia de acerto ao longo do raio (a casca mais externa)"""
    best, o = None, C.copy()
    for _ in range(6):
        hit = bvh.ray_cast(o, d, 0.2)
        if hit[0] is None:
            break
        dist = (hit[0] - C).length
        best = dist if best is None else max(best, dist)
        o = hit[0] + d * 1e-4
    return best


def direction(a, e):
    return Vector((math.sin(e) * math.sin(a), -math.sin(e) * math.cos(a), math.cos(e)))


def elev_for_z(bvh, a, z_target):
    lo, hi = 0.15, 2.7
    for _ in range(26):
        m = (lo + hi) / 2
        d = direction(a, m)
        r = surf_dist(bvh, d)
        z = (C + d * (r or 0.05)).z
        if z > z_target:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


class Hair:
    """Monta a malha. thick(a, t) -> espessura (m); t = 0 topo .. 1 linha do cabelo."""

    def __init__(self, name, cols=20, rings=7, hairline=None, seed=1):
        self.name = name
        self.cols, self.rings = cols, rings
        self.hairline = hairline or hairline_from_scalp()
        self.rng = random.Random(seed)
        self.bvh = build_bvh()
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("CabeloUV")
        self.grid = {}      # (col, ring) -> BMVert
        self.surf = {}      # (col, ring) -> ponto na pele
        self.normal = {}
        self.v_of_ring = {}

    def a_of(self, c):
        return -math.pi + (c + 0.5) * 2 * math.pi / self.cols   # costura atras

    def shell(self, thick, jitter=0.0, extra_rings=None, v_scale=1.0):
        """extra_rings: funcao(a, j) -> deslocamento extra abaixo da linha (mullet)"""
        bm = self.bm
        R = self.rings
        hl = self.hairline if callable(self.hairline) else (lambda a: smooth_interp(self.hairline, a))
        e_line = [elev_for_z(self.bvh, self.a_of(c), hl(self.a_of(c))) for c in range(self.cols)]
        top_d = direction(0, 0)
        r0 = surf_dist(self.bvh, top_d)
        pole = bm.verts.new(C + top_d * (r0 + thick(0.0, 0.0)))
        self.pole = pole
        for c in range(self.cols):
            a = self.a_of(c)
            for k in range(1, R + 1):
                t = k / R
                e = e_line[c] * t
                d = direction(a, e)
                r = surf_dist(self.bvh, d) or 0.05
                th = thick(a, t)
                if jitter:
                    th += self.rng.uniform(-jitter, jitter) * (1 - t * 0.6)
                p = C + d * (r + max(th, 0.0003))
                self.grid[(c, k)] = bm.verts.new(p)
                self.surf[(c, k)] = C + d * r
                self.normal[(c, k)] = d
        self.R_total = R
        # aneis extras (mullet) abaixo da linha
        if extra_rings:
            j = 1
            while True:
                any_ring = False
                for c in range(self.cols):
                    a = self.a_of(c)
                    off = extra_rings(a, j)
                    if off is None:
                        continue
                    any_ring = True
                    prev = self.grid.get((c, R + j - 1))
                    if prev is None:
                        continue
                    self.grid[(c, R + j)] = bm.verts.new(prev.co + off)
                    self.normal[(c, R + j)] = self.normal[(c, R)]
                if not any_ring:
                    break
                j += 1
            self.R_total = R + j - 1
        # faces: leque no topo + quads
        Rt = self.R_total
        vmax = Rt + 1   # +1 para a borda (lip)
        for c in range(self.cols):
            c2 = (c + 1) % self.cols
            u0, u1 = c / self.cols, (c + 1) / self.cols
            self._face([pole, self.grid[(c, 1)], self.grid[(c2, 1)]],
                       [((u0 + u1) / 2, 0), (u0, 1 / vmax), (u1, 1 / vmax)], v_scale)
            for k in range(1, Rt):
                if (c, k) not in self.grid or (c2, k) not in self.grid:
                    continue
                if (c, k + 1) in self.grid and (c2, k + 1) in self.grid:
                    vs = [self.grid[(c, k)], self.grid[(c, k + 1)], self.grid[(c2, k + 1)], self.grid[(c2, k)]]
                    uvs = [(u0, k / vmax), (u0, (k + 1) / vmax), (u1, (k + 1) / vmax), (u1, k / vmax)]
                    self._face(vs, uvs, v_scale)
                elif (c, k + 1) in self.grid and (c2, k + 1) not in self.grid:
                    vs = [self.grid[(c, k)], self.grid[(c, k + 1)], self.grid[(c2, k)]]
                    uvs = [(u0, k / vmax), (u0, (k + 1) / vmax), (u1, k / vmax)]
                    self._face(vs, uvs, v_scale)
                elif (c2, k + 1) in self.grid and (c, k + 1) not in self.grid:
                    vs = [self.grid[(c, k)], self.grid[(c2, k + 1)], self.grid[(c2, k)]]
                    uvs = [(u0, k / vmax), (u1, (k + 1) / vmax), (u1, k / vmax)]
                    self._face(vs, uvs, v_scale)
        # borda: dobra para dentro (da espessura a ponta do cabelo)
        for c in range(self.cols):
            c2 = (c + 1) % self.cols
            kc = max(key[1] for key in self.grid if len(key) == 2 and key[0] == c)
            kc2 = max(key[1] for key in self.grid if len(key) == 2 and key[0] == c2)
            if kc != kc2:
                continue
            a, b = self.grid[(c, kc)], self.grid[(c2, kc2)]
            na = self._inner(c, kc)
            nb = self._inner(c2, kc2)
            u0, u1 = c / self.cols, (c + 1) / self.cols
            self._face([a, na, nb, b], [(u0, kc / vmax), (u0, 1.0), (u1, 1.0), (u1, kc / vmax)], v_scale)

    def _inner(self, c, k):
        key = ("in", c, k)
        if key not in self.grid:
            v = self.grid[(c, k)]
            if (c, k) in self.surf:
                p = self.surf[(c, k)] - self.normal[(c, k)] * 0.0015
            else:
                n = self.normal[(c, min(k, self.rings))]
                p = v.co - n * 0.004
            self.grid[key] = self.bm.verts.new(p)
        return self.grid[key]

    def _face(self, vs, uvs, v_scale=1.0):
        try:
            f = self.bm.faces.new(vs)
        except ValueError:
            return None
        for l, uv in zip(f.loops, uvs):
            l[self.uv].uv = (uv[0], 1 - uv[1] * v_scale)
        return f

    # ---------------------------------------------------------------- detalhes
    def spike(self, c, k, length, tilt=Vector((0, 0, 0)), width=0.006, sides=4, twist=0.0):
        """espeto/mecha: piramide saindo do ponto (c,k) da casca"""
        base = self.grid[(c, k)].co
        n = (self.normal[(c, k)] + tilt).normalized()
        # base em volta do ponto, no plano perpendicular a n
        t1 = n.cross(Vector((0, 0, 1)))
        if t1.length < 1e-4:
            t1 = Vector((1, 0, 0))
        t1.normalize()
        t2 = n.cross(t1).normalized()
        ring = []
        for i in range(sides):
            ang = twist + i * 2 * math.pi / sides
            ring.append(self.bm.verts.new(base - n * 0.002 + (t1 * math.cos(ang) + t2 * math.sin(ang)) * width))
        tip = self.bm.verts.new(base + n * length)
        u = (c + 0.5) / self.cols
        for i in range(sides):
            j = (i + 1) % sides
            self._face([ring[i], ring[j], tip],
                       [(u - 0.02, 0.35), (u + 0.02, 0.35), (u, 0.02)])

    def lock(self, pts, width, u, v0=0.05, v1=0.6):
        """mecha achatada (fita triangular) por uma lista de pontos; largura afina ate a ponta"""
        n = len(pts)
        prev = None
        for i, p in enumerate(pts):
            w = width * (1 - i / (n - 1)) if i < n - 1 else 0.0
            d = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
            side = d.cross(Vector((0, 0, 1)))
            if side.length < 1e-4:
                side = Vector((1, 0, 0))
            side.normalize()
            up = side.cross(d).normalized()
            a = self.bm.verts.new(p + side * w + up * 0.0008)
            b = self.bm.verts.new(p - side * w + up * 0.0008)
            if prev:
                v = v0 + (v1 - v0) * i / (n - 1)
                vp = v0 + (v1 - v0) * (i - 1) / (n - 1)
                self._face([prev[0], prev[1], b, a], [(u - 0.03, vp), (u + 0.03, vp), (u + 0.03, v), (u - 0.03, v)])
            prev = (a, b)

    def to_object(self, coll):
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        # garante normais para fora (do centro)
        for f in self.bm.faces:
            if (f.calc_center_median() - C).dot(f.normal) < 0:
                f.normal_flip()
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        ob = bpy.data.objects.new(self.name, me)
        coll.objects.link(ob)
        return ob
