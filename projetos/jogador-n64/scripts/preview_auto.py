import bpy, sys
from mathutils import Vector
blend, out = sys.argv[1], sys.argv[2]
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.context.scene
pts=[o.matrix_world@v.co for o in bpy.data.objects if o.type=="MESH" for v in o.data.vertices]
mn=Vector([min(p[i] for p in pts) for i in range(3)]); mx=Vector([max(p[i] for p in pts) for i in range(3)])
c=(mn+mx)/2; ext=max((mx-mn))*1.15
cam=bpy.data.objects.new("cam",bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type="ORTHO"; cam.data.ortho_scale=ext
sc.render.engine="BLENDER_WORKBENCH"; sc.display.shading.light="STUDIO"; sc.display.shading.color_type="TEXTURE"
sc.render.resolution_x=sc.render.resolution_y=500
sc.render.film_transparent=False
for n,d in {"front":(0,-1,0),"side":(1,0,0),"back":(0,1,0)}.items():
    d=Vector(d); cam.location=c+d*2; cam.rotation_euler=(-d).to_track_quat("-Z","Y").to_euler()
    sc.render.filepath=f"{out}_{n}.png"; bpy.ops.render.render(write_still=True)
