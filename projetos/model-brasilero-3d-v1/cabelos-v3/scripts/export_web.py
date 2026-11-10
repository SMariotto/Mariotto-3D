"""Exporta a versao web (glTF binario .glb) do boneco com rostos.

Uso: python3 export_web.py <model-brasilero-3d-rostos.blend> <saida.glb>

Diferenca para o .blend: no glTF nao existe o truque de ler propriedades do objeto no material.
Entao o UV do Rosto_Expressao aponta para o PRIMEIRO quadro do atlas (tipo 0, animacao 0, quadro 0)
e o jogo troca o quadro mudando o deslocamento (offset) da textura:
    offset.x = (tipo*5 + quadro) / 25
    offset.y = animacao / 5
(no three.js: material.map.offset.set(x, y)). Ver rostos.json e demo_web.html.
"""
import sys

import bpy

blend, out = sys.argv[1], sys.argv[2]
bpy.ops.wm.open_mainfile(filepath=blend)
dec = bpy.data.objects["Rosto_Expressao"]
me = dec.data
src = me.uv_layers["RostoUV"]
dst = me.uv_layers.new(name="AtlasUV")
for i, d in enumerate(src.data):
    u, v = d.uv
    dst.data[i].uv = (u / 25.0, (v + 4.0) / 5.0)   # celula do canto superior esquerdo
me.uv_layers.remove(me.uv_layers["RostoUV"])
me.uv_layers["AtlasUV"].active = True
me.uv_layers["AtlasUV"].active_render = True

mat = dec.active_material
nt = mat.node_tree
tex = next(n for n in nt.nodes if n.type == "TEX_IMAGE")
bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
for n in list(nt.nodes):
    if n not in (tex, bsdf) and n.type != "OUTPUT_MATERIAL":
        nt.nodes.remove(n)
nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
tex.extension = "REPEAT"
if dec.animation_data:
    dec.animation_data_clear()
for k in ("tipo_rosto", "animacao", "quadro"):
    if k in dec:
        del dec[k]
dec["rosto_atlas"] = "offset.x=(tipo*5+quadro)/25, offset.y=animacao/5"

bpy.ops.export_scene.gltf(
    filepath=out,
    export_format="GLB",
    export_image_format="AUTO",
    export_extras=True,
    export_animations=False,
    export_yup=True,
    export_apply=True,
)
print("ok", out)
