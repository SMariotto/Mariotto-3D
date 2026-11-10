"""Mechas low-poly (cunhas com quina) para os cabelos v2.

Cada mecha sai de uma raiz no cranio e vai ate a ponta seguindo a curva da cabeca (caminho em arco
entre duas direcoes a partir do centro, com controle no meio para curvar). Secao em triangulo:
duas bordas encostadas na cabeca e uma quina levantada no meio; a largura afina ate a ponta.
UV: metade de cima da textura (v 0.5..1); a casca de baixo usa a metade de baixo.
"""
import math
import random

from mathutils import Vector

import hair_lib as H


def slerp(a, b, t):
    a, b = a.normalized(), b.normalized()
    d = max(-1.0, min(1.0, a.dot(b)))
    om = math.acos(d)
    if om < 1e-5:
        return a.copy()
    return (a * math.sin((1 - t) * om) + b * math.sin(t * om)) / math.sin(om)


class Locks:
    def __init__(self, hair, seed=0):
        self.h = hair
        self.bm = hair.bm
        self.uv = hair.uv
        self.bvh = hair.bvh
        self.rng = random.Random(seed)
        self._eline = {}
        self.hl = hair.hairline if callable(hair.hairline) else (lambda a: H.smooth_interp(hair.hairline, a))
        self.count = 0

    def e_line(self, a):
        k = round(a, 3)
        if k not in self._eline:
            self._eline[k] = H.elev_for_z(self.bvh, a, self.hl(a))
        return self._eline[k]

    def resolve(self, a, spec):
        """spec: ('t', fracao da linha do cabelo) | ('z', altura no mundo) | ('e', elevacao)"""
        kind, val = spec
        if kind == "t":
            return val * self.e_line(a)
        if kind == "z":
            return H.elev_for_z(self.bvh, a, val)
        return val

    def lock(self, a0, s0, a1, s1, width, thick, lift=0.0, lift_pow=2.0, segs=4, layer=0,
             bend=0.0, bend_up=0.0, hang=0.0, hang_segs=2, flick=0.0, base_off=0.0030, taper=0.9):
        e0, e1 = self.resolve(a0, s0), self.resolve(a1, s1)
        d0, d1 = H.direction(a0, e0), H.direction(a1, e1)
        mid = slerp(d0, d1, 0.5)
        side_axis = d0.cross(d1)
        if side_axis.length > 1e-6:
            mid = (mid + side_axis.normalized() * bend + Vector((0, 0, bend_up))).normalized()
        pts, nrm = [], []
        last_r = None
        for i in range(segs + 1):
            s = i / segs
            d = slerp(slerp(d0, mid, s), slerp(mid, d1, s), s)
            r = H.surf_dist(self.bvh, d)
            if r is None:
                r = last_r or 0.05
            last_r = r
            rr = r + base_off + layer * 0.0009 + lift * (s ** lift_pow)
            pts.append(H.C + d * rr)
            nrm.append(d)
        # parte pendurada (mullet): desce reto a partir da ultima ponta
        if hang > 0:
            p_end, n_end = pts[-1], nrm[-1]
            out = Vector((n_end.x, n_end.y, 0))
            out = out.normalized() if out.length > 1e-6 else Vector((0, 1, 0))
            for j in range(1, hang_segs + 1):
                f = j / hang_segs
                pts.append(p_end + Vector((0, 0, -hang * f)) + out * (0.0015 * f + flick * f * f))
                nrm.append(out)
        n = len(pts)
        u0 = self.rng.uniform(0.0, 0.74)
        verts = []
        for i, (p, d) in enumerate(zip(pts, nrm)):
            s = i / (n - 1)
            if i == n - 1:
                verts.append((self.bm.verts.new(p),))
                continue
            T = (pts[i + 1] - pts[i - 1]) if 0 < i < n - 1 else (pts[1] - pts[0] if i == 0 else pts[i] - pts[i - 1])
            T.normalize()
            side = T.cross(d)
            side = side.normalized() if side.length > 1e-6 else Vector((1, 0, 0))
            up = side.cross(T).normalized()
            if up.dot(d) < 0:
                up = -up
            w = width * (1 - s) ** taper * (0.85 + 0.15 * math.sin(math.pi * min(1, s * 1.6)))
            t = thick * (1 - s) ** 0.7
            L = self.bm.verts.new(p + side * w / 2 - up * 0.0008)
            R = self.bm.verts.new(p - side * w / 2 - up * 0.0008)
            G = self.bm.verts.new(p + up * t)
            verts.append((L, G, R))
        U = (u0, u0 + 0.13, u0 + 0.26)
        for i in range(n - 1):
            v0, v1 = 1 - 0.5 * i / (n - 1), 1 - 0.5 * (i + 1) / (n - 1)
            a, b = verts[i], verts[i + 1]
            if len(b) == 1:
                tip = b[0]
                self._f([a[0], tip, a[1]], [(U[0], v0), (U[1], v1), (U[1], v0)])
                self._f([a[1], tip, a[2]], [(U[1], v0), (U[1], v1), (U[2], v0)])
                self._f([a[2], tip, a[0]], [(U[2], v0), (U[1], v1), (U[0], v0)])
            else:
                self._f([a[0], b[0], b[1], a[1]], [(U[0], v0), (U[0], v1), (U[1], v1), (U[1], v0)])
                self._f([a[1], b[1], b[2], a[2]], [(U[1], v0), (U[1], v1), (U[2], v1), (U[2], v0)])
                self._f([a[2], b[2], b[0], a[0]], [(U[2], v0), (U[2], v1), (U[0], v1), (U[0], v0)])
        # tampa da raiz
        r0 = verts[0]
        self._f([r0[0], r0[1], r0[2]], [(U[0], 1.0), (U[1], 1.0), (U[2], 1.0)])
        self.count += 1

    def _f(self, vs, uvs):
        try:
            f = self.bm.faces.new(vs)
        except ValueError:
            return
        for l, uv in zip(f.loops, uvs):
            l[self.uv].uv = uv

    # ------------------------------------------------------------ atalhos
    def fan(self, n, a_from, a_to, root, end, width, thick, sweep=0.0, jitter=0.0, **kw):
        for i in range(n):
            f = (i + 0.5) / n
            a = a_from + (a_to - a_from) * f + self.rng.uniform(-jitter, jitter)
            self.lock(a, root, a + sweep, end, width * self.rng.uniform(0.9, 1.1),
                      thick * self.rng.uniform(0.9, 1.1), **kw)


def to_ae(d):
    d = d.normalized()
    return math.atan2(d.x, -d.y), math.acos(max(-1.0, min(1.0, d.z)))


def blob(L, a, spec, radius, flat=0.7, segs=6, rings=4, base_off=0.003, sink=0.35):
    """cacho: elipsoide low-poly achatado contra a cabeca"""
    e = L.resolve(a, spec)
    d = H.direction(a, e)
    r = H.surf_dist(L.bvh, d) or 0.05
    n = d
    t1 = n.cross(Vector((0, 0, 1)))
    t1 = t1.normalized() if t1.length > 1e-6 else Vector((1, 0, 0))
    t2 = n.cross(t1).normalized()
    c = H.C + d * (r + base_off + radius * flat * (1 - sink))
    tw = L.rng.random() * 6.28
    u0 = L.rng.uniform(0.0, 0.74)
    top = L.bm.verts.new(c + n * radius * flat)
    bot = L.bm.verts.new(c - n * radius * flat)
    grid = []
    for i in range(1, rings):
        th = math.pi * i / rings
        row = []
        for j in range(segs):
            ph = tw + 2 * math.pi * j / segs
            p = c + (t1 * math.cos(ph) + t2 * math.sin(ph)) * radius * math.sin(th) + n * radius * flat * math.cos(th)
            row.append(L.bm.verts.new(p))
        grid.append(row)
    U = lambda j: u0 + 0.26 * j / segs
    V = lambda i: 1 - 0.5 * i / rings
    for j in range(segs):
        j2 = (j + 1) % segs
        L._f([top, grid[0][j], grid[0][j2]], [(U(j + 0.5), V(0)), (U(j), V(1)), (U(j + 1), V(1))])
        for i in range(rings - 2):
            L._f([grid[i][j], grid[i + 1][j], grid[i + 1][j2], grid[i][j2]],
                 [(U(j), V(i + 1)), (U(j), V(i + 2)), (U(j + 1), V(i + 2)), (U(j + 1), V(i + 1))])
        L._f([grid[-1][j], bot, grid[-1][j2]], [(U(j), V(rings - 1)), (U(j + 0.5), V(rings)), (U(j + 1), V(rings - 1))])
    L.count += 1
