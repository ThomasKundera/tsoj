import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create smoother sphere
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=96,
    ring_count=48,
    radius=2.0,
    location=(0, 0, 0)
)

sphere = bpy.context.active_object

# Make it look smooth
bpy.ops.object.shade_smooth()

# Optional: Subdivision modifier for even better roundness
subsurf = sphere.modifiers.new(name="Subsurf", type='SUBSURF')
subsurf.levels = 2
subsurf.render_levels = 3

# Camera, light, material (same as before)
cam_data = bpy.data.cameras.new(name="Camera")
cam_obj = bpy.data.objects.new("Camera", cam_data)
cam_obj.location = (0, -12, 5)
cam_obj.rotation_euler = (1.1, 0, 0)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

light_data = bpy.data.lights.new(name="Light", type='SUN')
light_obj = bpy.data.objects.new("Light", light_data)
light_obj.location = (5, 5, 10)
bpy.context.scene.collection.objects.link(light_obj)

# Material
mat = bpy.data.materials.new(name="SphereMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs['Base Color'].default_value = (0.7, 0.8, 0.9, 1.0)
bsdf.inputs['Roughness'].default_value = 0.2
sphere.data.materials.append(mat)

# Render settings
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.use_denoising = False   # safe for Ubuntu apt version
scene.render.resolution_x = 1000
scene.render.resolution_y = 800
scene.render.filepath = "//sphere_smooth.png"

bpy.ops.render.render(write_still=True)
print("✅ Render finished! Saved as sphere_smooth.png")