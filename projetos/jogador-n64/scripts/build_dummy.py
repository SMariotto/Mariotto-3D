"""Gera um manequim cinza liso (T-pose) com as mesmas proporcoes e juntas do modelo.

Uso: python3 build_dummy.py <model-by-samuel.blend de referencia> <saida.blend>

Le apenas as medidas (bounding boxes em coordenadas de mundo) das pecas do modelo
de referencia e constroi um manequim novo com primitivas. Nada da malha, da pele
ou das texturas do personagem e reaproveitado.
Convencao: Z para cima, frente = -Y, lado esquerdo do manequim = +X.
"""
import sys

import bpy
from mathutils import Vector

ref, out = sys.argv[1], sys.argv[2]

bpy.ops.wm.open_mainfile(filepath=ref)


def wbox(name):
    o = bpy.data.objects[name]
    pts = [o.matrix_world @ v.co for v in o.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)])
    mx = Vector([max(p[i] for p in pts) for i in range(3)])
    return mn, mx


M = {n: wbox(n) for n in (
    "Mesh.003", "Mesh.004", "Mesh.001", "Mesh.012",
    "Mesh.006", "Mesh.007", "Mesh.009", "Mesh.013",
    "Mesh", "Mesh.005", "Mesh.011", "Mesh.015",
)}


def ctr(n):
    mn, mx = M[n]
    return (mn + mx) / 2


def size(n):
    mn, mx = M[n]
    return mx - mn


# --- cena nova, vazia ---
bpy.ops.wm.read_factory_settings(use_empty=True)

mat = bpy.data.materials.new("Dummy_Gray")
mat.use_nodes = True
b = mat.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.62, 0.62, 0.64, 1)
b.inputs["Roughness"].default_value = 0.6


def finish(o, name):
    o.name = name
    o.data.name = name
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def ellipsoid(name, center, half):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=center)
    o = bpy.context.object
    o.scale = half
    bpy.ops.object.transform_apply(scale=True)
    return finish(o, name)


def limb(name, a, b_, r):
    a, b_ = Vector(a), Vector(b_)
    d = b_ - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=r, depth=d.length, location=(a + b_) / 2)
    o = bpy.context.object
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    bpy.ops.object.transform_apply(rotation=True)
    return finish(o, name)


def joint(name, p, r):
    return ellipsoid(name, p, (r, r, r))


# ---- medidas de referencia ----
head_c, head_s = ctr("Mesh.003"), size("Mesh.003")
torso_c, torso_s = ctr("Mesh.001"), size("Mesh.001")
hips_mn, hips_mx = M["Mesh.012"]
x0 = torso_c.x  # eixo central
z_floor = min(M["Mesh.009"][0].z, M["Mesh.013"][0].z)

# cabeca e pescoco
ellipsoid("Head", head_c, (head_s.x * 0.34, head_s.y * 0.30, head_s.z * 0.40))
neck_top = Vector((x0, head_c.y, M["Mesh.003"][0].z + head_s.z * 0.12))
neck_bot = Vector((x0, torso_c.y, torso_c.z + torso_s.z * 0.40))
limb("Neck", neck_bot, neck_top, 0.014)

# tronco e quadril
ellipsoid("Chest", torso_c, (torso_s.x * 0.48, torso_s.y * 0.46, torso_s.z * 0.50))
hip_c = Vector((x0, (hips_mn.y + hips_mx.y) / 2, hips_mn.z + (hips_mx.z - hips_mn.z) * 0.62))
hip_s = hips_mx - hips_mn
limb("Waist", Vector((x0, torso_c.y, torso_c.z)), Vector((x0, torso_c.y, hip_c.z)), min(torso_s.x, hip_s.x) * 0.36)
ellipsoid("Pelvis", hip_c, (hip_s.x * 0.40, hip_s.y * 0.30, hip_s.z * 0.22))

# ---- bracos (T-pose ao longo de X) ----
arm_z = torso_c.z + torso_s.z * 0.30
arm_y = ctr("Mesh.005").y
for side, sx, arm_n, hand_n in (("L", 1, "Mesh", "Mesh.015"), ("R", -1, "Mesh.005", "Mesh.011")):
    hand_c, hand_s = ctr(hand_n), size(hand_n)
    reach = abs(hand_c.x - x0) - hand_s.x * 0.5  # ate o inicio da mao
    shoulder = Vector((x0 + sx * torso_s.x * 0.50, arm_y, arm_z))
    wrist = Vector((x0 + sx * reach, arm_y, arm_z))
    elbow = (shoulder + wrist) / 2
    joint(f"Shoulder.{side}", shoulder, 0.022)
    limb(f"UpperArm.{side}", shoulder, elbow, 0.0175)
    joint(f"Elbow.{side}", elbow, 0.0155)
    limb(f"Forearm.{side}", elbow, wrist, 0.0145)
    joint(f"Wrist.{side}", wrist, 0.0135)
    ellipsoid(f"Hand.{side}", Vector((x0 + sx * abs(hand_c.x - x0), arm_y, arm_z)),
              (hand_s.x * 0.46, hand_s.y * 0.40, hand_s.z * 0.40))

# ---- pernas ----
for side, sx, leg_n, foot_n in (("L", 1, "Mesh.007", "Mesh.013"), ("R", -1, "Mesh.006", "Mesh.009")):
    leg_mn, leg_mx = M[leg_n]
    foot_c, foot_s = ctr(foot_n), size(foot_n)
    lx = x0 + sx * abs(ctr(leg_n).x - x0)
    ly = ctr(leg_n).y
    hip = Vector((lx, ly, hip_c.z - hip_s.z * 0.10))
    ankle = Vector((lx, ly, foot_c.z + foot_s.z * 0.30))
    knee = hip.lerp(ankle, 0.5)
    joint(f"Hip.{side}", hip, 0.024)
    limb(f"Thigh.{side}", hip, knee, 0.021)
    joint(f"Knee.{side}", knee, 0.019)
    limb(f"Shin.{side}", knee, ankle, 0.0165)
    joint(f"Ankle.{side}", ankle, 0.0165)
    ellipsoid(f"Foot.{side}", Vector((lx, foot_c.y, foot_c.z)),
              (foot_s.x * 0.46, foot_s.y * 0.42, foot_s.z * 0.34))

bpy.ops.wm.save_as_mainfile(filepath=out)
print("objetos:", len(bpy.data.objects), "| altura total:", round(max(
    (o.matrix_world @ v.co).z for o in bpy.data.objects for v in o.data.vertices
) - min((o.matrix_world @ v.co).z for o in bpy.data.objects for v in o.data.vertices), 3))
