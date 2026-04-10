import bpy

# Clear everything
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Create the sphere (make it reasonably smooth)
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=96,
    ring_count=48,
    radius=1.5,
    location=(0, 0, 0)
)

sphere = bpy.context.active_object

# Make shading smooth
bpy.ops.object.shade_smooth()

# Add Subdivision Surface for extra roundness
subsurf = sphere.modifiers.new(name="Subsurf", type='SUBSURF')
subsurf.levels = 2
subsurf.render_levels = 3

# === Make the sphere a light source (Emission) ===
mat = bpy.data.materials.new(name="EmissiveSphere")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

# Clear default nodes
for node in nodes:
    nodes.remove(node)

# Create nodes for simple anisotropic emission
emission = nodes.new('ShaderNodeEmission')
emission.inputs['Color'].default_value = (1.0, 0.6, 0.3, 1.0)   # warm orange glow
emission.inputs['Strength'].default_value = 5.0                 # brightness

# Mix with a very faint diffuse for subtle surface detail (optional but nice)
diffuse = nodes.new('ShaderNodeBsdfDiffuse')
diffuse.inputs['Color'].default_value = (1.0, 0.7, 0.5, 1.0)

mix = nodes.new('ShaderNodeMixShader')
mix.inputs['Fac'].default_value = 0.15   # mostly emission, small diffuse contribution

output = nodes.new('ShaderNodeOutputMaterial')

# Connect nodes
links.new(emission.outputs['Emission'], mix.inputs[1])
links.new(diffuse.outputs['BSDF'], mix.inputs[2])
links.new(mix.outputs['Shader'], output.inputs['Surface'])

# Assign material to sphere
sphere.data.materials.append(mat)

# === Camera Setup ===
cam_data = bpy.data.cameras.new(name="Camera")
cam_obj = bpy.data.objects.new("Camera", cam_data)
cam_obj.location = (0, -8, 4)
cam_obj.rotation_euler = (1.0, 0, 0)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# Add a weak sun light so we still see the sphere shape
light_data = bpy.data.lights.new(name="Sun", type='SUN')
light_obj = bpy.data.objects.new("Sun", light_data)
light_obj.location = (5, 5, 10)
light_obj.rotation_euler = (0.8, 0, 0)
bpy.context.scene.collection.objects.link(light_obj)
light_data.energy = 1.0   # keep it dim so the sphere is the main light

# === Render Settings ===
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.use_denoising = False # Ubuntu native apt
scene.render.resolution_x = 1000
scene.render.resolution_y = 800
scene.render.filepath = "//glowing_sphere.png"

# Render
bpy.ops.render.render(write_still=True)

print("✅ Render finished! Saved as glowing_sphere.png")