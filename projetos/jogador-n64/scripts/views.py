"""python3 views.py <blend> <png_saida> <cx,cy,cz> <ortho> <vistas: front,side,back,q,top,bottom,qfoot> [px]"""
import bpy, sys
from mathutils import Vector
from PIL import Image
blend, out, c, scale, names = sys.argv[1], sys.argv[2], Vector(map(float, sys.argv[3].split(","))), float(sys.argv[4]), sys.argv[5].split(",")
px = int(sys.argv[6]) if len(sys.argv) > 6 else 420
D = {"front": (0,-1,0), "side": (1,0,0), "rside": (-1,0,0), "back": (0,1,0), "q": (0.7,-0.7,0.25), "top": (0,-0.15,1), "bottom": (0.01,-0.3,-1), "qfoot": (0.8,-0.8,0.5)}
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = scale
sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "TEXTURE"; sc.display.shading.show_specular_highlight = False
sc.render.resolution_x = sc.render.resolution_y = px
ims = []
for n in names:
    d = Vector(D[n]).normalized(); cam.location = c + d * 2
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = f"{out}_{n}.png"; bpy.ops.render.render(write_still=True)
    ims.append(Image.open(f"{out}_{n}.png").convert("RGB"))
W = Image.new("RGB", (px * len(ims), px), (60, 60, 60))
for i, im in enumerate(ims): W.paste(im, (i * px, 0))
W.save(out + ".png")
