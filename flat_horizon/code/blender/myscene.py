import os
import bpy
import math
from mathutils import Vector

from tkblender import add_axis_helpers, look_at,m, km

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def setup_world():
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    for node in list(nodes):
        nodes.remove(node)

    bg = nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.05, 0.08, 0.15, 1.0)   # deep blue sky
    bg.inputs['Strength'].default_value = 1.0

    output = nodes.new('ShaderNodeOutputWorld')
    world.node_tree.links.new(bg.outputs['Background'], output.inputs['Surface'])

def create_shore():
    """Simple land strip near the camera"""
    bpy.ops.mesh.primitive_plane_add(size=200*m, location=(0, -80*m, 0))
    shore = bpy.context.active_object
    shore.name = "Shore"

    mat = bpy.data.materials.new(name="Shore_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.35, 0.30, 0.22, 1.0)  # sandy/beige
    bsdf.inputs["Roughness"].default_value = 0.9
    shore.data.materials.append(mat)
    return shore


def create_ocean():
    """Improved ocean material for Blender 5.1.1 - Less grey, better water look"""
    
    bpy.ops.mesh.primitive_plane_add(size=10000 * m, location=(0, 100 * m, -0.5 * m))
    ocean = bpy.context.active_object
    ocean.name = "Ocean"

    # Subdivision
    sub = ocean.modifiers.new(name="Subdivision", type='SUBSURF')
    sub.levels = 6
    sub.render_levels = 8

    # Geometric displacement waves
    disp = ocean.modifiers.new(name="Ocean_Displace", type='DISPLACE')
    tex = bpy.data.textures.new("OceanWave", type='CLOUDS')
    tex.noise_scale = 6.5 * m
    tex.noise_depth = 4
    disp.texture = tex
    disp.strength = 2.2 * m
    disp.mid_level = 0.5 * m

    # ====================== WATER MATERIAL ======================
    mat = bpy.data.materials.new(name="Ocean_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    for node in list(nodes):
        nodes.remove(node)

    output = nodes.new("ShaderNodeOutputMaterial")
    principled = nodes.new("ShaderNodeBsdfPrincipled")

    output.location = (800, 0)
    principled.location = (400, 0)

    # === Core settings for nice looking water in Blender 5.1 ===
    principled.inputs["Base Color"].default_value = (0.004, 0.018, 0.055, 1.0)   # Deep blue
    principled.inputs["Roughness"].default_value = 0.025
    principled.inputs["Metallic"].default_value = 0.0
    principled.inputs["IOR"].default_value = 1.33

    # Specular control
    if "Specular IOR Level" in principled.inputs:
        principled.inputs["Specular IOR Level"].default_value = 0.92

    # Transmission (correct name in 5.1)
    if "Transmission Weight" in principled.inputs:
        principled.inputs["Transmission Weight"].default_value = 0.88

    principled.inputs["Alpha"].default_value = 1.0

    # Sheen helps give water a bit more "wet" look
    if "Sheen" in principled.inputs:
        principled.inputs["Sheen"].default_value = 0.4
    if "Sheen Tint" in principled.inputs:
        #principled.inputs["Sheen Tint"].default_value = 0.7
        pass

    # === Normal map ripples (fixed for 5.1) ===
    tex_coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    wave = nodes.new("ShaderNodeTexWave")
    vector_math = nodes.new("ShaderNodeVectorMath")

    tex_coord.location = (-800, 100)
    mapping.location = (-600, 100)
    wave.location = (-350, 100)
    vector_math.location = (-100, 100)

    vector_math.operation = 'MULTIPLY'
    vector_math.inputs[1].default_value = (1.8, 1.8, 1.8)

    wave.inputs["Scale"].default_value = 20.0 * m
    wave.inputs["Distortion"].default_value = 3.0 * m
    wave.inputs["Detail"].default_value = 2.0 * m

    # Connections
    links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
    links.new(wave.outputs["Color"], vector_math.inputs[0])
    links.new(vector_math.outputs["Vector"], principled.inputs["Normal"])

    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    ocean.data.materials.append(mat)
    return ocean


def add_earth_curvature_to_ocean(ocean, earth_radius=6371000 * m):
    """
    Projects the ocean onto a sphere with Earth radius (6371 km).
    Fixed for Blender 5.1.1
    """
    # High subdivision needed for smooth curve
    if "Subdivision" not in [mod.name for mod in ocean.modifiers]:
        sub = ocean.modifiers.new(name="Subdivision", type='SUBSURF')
    else:
        sub = ocean.modifiers["Subdivision"]
    
    sub.levels = 7
    sub.render_levels = 9
    sub.use_creases = True

    # Create invisible target sphere (center far below)
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=earth_radius,
        location=(0, 0, -earth_radius),     # Sphere center
        segments=96,
        ring_count=48
    )
    sphere = bpy.context.active_object
    sphere.name = "Earth_Curvature_Target"
    sphere.hide_viewport = True
    sphere.hide_render = True

    # Shrinkwrap modifier - Fixed for Blender 5.1
    shrink = ocean.modifiers.new(name="Earth_Curvature", type='SHRINKWRAP')
    shrink.target = sphere
    shrink.wrap_method = 'PROJECT'           # Project method
    shrink.wrap_mode = 'ON_SURFACE'
    shrink.offset = 0.0

    # In Blender 5.1 we use project_axis_space instead of project_axis
    if hasattr(shrink, "project_axis_space"):
        shrink.project_axis_space = 'NEG_Z'      # Project downward
    elif hasattr(shrink, "project_axis"):
        shrink.project_axis = 'NEG_Z'

    print(f"✅ Ocean curved to Earth radius: {earth_radius/1000:.0f} km")
    return sphere


def create_atmosphere():
    """Simple volumetric atmosphere with absorption (tints distant objects)"""
    # Large cube for volume
    bpy.ops.mesh.primitive_cube_add(
        size=500*m, 
        location=(0, 50*m, 80*m), 
        scale=(1, 1, 0.4)
    )
    volume_obj = bpy.context.active_object
    volume_obj.name = "Atmosphere_Volume"

    mat = bpy.data.materials.new(name="Atmosphere_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in list(nodes):
        nodes.remove(node)

    output = nodes.new("ShaderNodeOutputMaterial")
    volume_abs = nodes.new("ShaderNodeVolumeAbsorption")
    volume_scat = nodes.new("ShaderNodeVolumeScatter")   # optional light scattering

    volume_abs.inputs["Color"].default_value = (0.6, 0.75, 0.9, 1.0)   # bluish haze
    volume_abs.inputs["Density"].default_value = 0.008   # ← Tune this (higher = more absorption)

    volume_scat.inputs["Color"].default_value = (0.7, 0.85, 1.0, 1.0)
    volume_scat.inputs["Density"].default_value = 0.004
    volume_scat.inputs["Anisotropy"].default_value = 0.6

    # Mix them
    mix = nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.6

    links.new(volume_abs.outputs["Volume"], mix.inputs[1])
    links.new(volume_scat.outputs["Volume"], mix.inputs[2])
    links.new(mix.outputs["Shader"], output.inputs["Volume"])

    volume_obj.data.materials.append(mat)
    return volume_obj


def create_sun():
    """Lower sun coming from the left side (good for dramatic horizon lighting)"""
    
    # Position: Far to the left and lower in the sky
    # X = positive → left side (depending on your camera orientation)
    # Z = lower height = sun closer to horizon
    sun_location = (150 * m, -50 * m, 35 * m)        # ← Main change

    bpy.ops.object.light_add(type='SUN', location=sun_location)
    sun = bpy.context.active_object
    sun.name = "Sun_Light"

    # Lighting settings
    sun.data.energy = 4                           # Much stronger than 2.0
    sun.data.angle = math.radians(2.0)               # Softer edges
    sun.data.color = (1.0, 0.88, 0.65)               # Warmer, slightly golden color (good for low sun)

    # Optional: Rotate the sun so light comes more from the side
    sun.rotation_euler = (math.radians(40), 0, math.radians(30))

    print(f"Sun placed at {sun_location} with energy {sun.data.energy}")
    return sun

def create_vertical_bar(dfactor=1000 * m):
    """Creates a vertical bar/pole away from the camera"""
    # Position
    bar_location = (dfactor/5, dfactor, 5 * m)      # Adjust X/Y if needed
    
    # Create a thin tall cylinder
    bpy.ops.mesh.primitive_cylinder_add(
        radius=1.2 * m,      # thickness of the bar
        depth=25 * m,        # height of the bar
        location=bar_location,
        rotation=(0, 0, 0)
    )

    bar = bpy.context.active_object
    bar.name = "Vertical_Bar"

    # Simple dark material
    mat = bpy.data.materials.new(name="Bar_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.08, 0.07, 0.06, 1.0)   # dark brownish/grey
    bsdf.inputs["Roughness"].default_value = 0.7
    bsdf.inputs["Metallic"].default_value = 0.0
    
    bar.data.materials.append(mat)

    # Optional: Add a small base/platform so it doesn't look floating
    bpy.ops.mesh.primitive_cube_add(
        size=3*m,
        location=(bar_location[0], bar_location[1], 0.4*m)
    )
    base = bpy.context.active_object
    base.name = "Bar_Base"
    base.data.materials.append(mat)

    print(f"✅ Vertical bar added at {bar_location}")
    return bar


def setup_camera():
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    cam_obj.location = (-30*m, -50*m, 8*m)      # On the shore, looking out to sea

    # Look toward horizon
    direction = Vector((20*m, 180*m, 5*m)) - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    cam_data.lens = 200
    cam_data.clip_start = 0.1
    cam_data.clip_end = 20000*m

    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    return cam_obj

def setup_render_stamp():
    """Configure clean timestamp stamp (hide filename and scene name)."""
    scene = bpy.context.scene

    scene.render.use_stamp = True
    scene.render.use_stamp_date = True 
    scene.render.use_stamp_time = True

    # Hide unwanted info
    scene.render.use_stamp_filename = False
    scene.render.use_stamp_scene = False
    scene.render.use_stamp_render_time = True
    scene.render.use_stamp_frame = False
    scene.render.use_stamp_camera = False
    scene.render.use_stamp_lens = False
    scene.render.use_stamp_marker = False

    # Visual settings
    scene.render.stamp_font_size = 7
    scene.render.stamp_foreground = (1.0, 1.0, 1.0, 1.0)
    scene.render.stamp_background = (0.0, 0.0, 0.0, 0.6)

    print("✅ Clean stamp enabled")


def setup_render():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 10
    scene.cycles.max_bounces = 12
    scene.cycles.use_denoising = True

    scene.render.resolution_x = 960
    scene.render.resolution_y = 540

    # Important for less dull look
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'High Contrast'
    scene.view_settings.exposure = 1.1          # brighten the image

    setup_render_stamp()
    print("✅ Render settings updated")


# ====================== MAIN ======================
def main():
    clear_scene()
    setup_world()
    create_shore()
    ocean = create_ocean()

    #add_earth_curvature_to_ocean(ocean, earth_radius=6371000 * m)

    #create_atmosphere()
    for i in range(1,10):
        create_vertical_bar(i*km)
    create_sun()
    setup_camera()
    setup_render()

    print("✅ Scene ready: Shore + Wavy Ocean + Atmosphere with Absorption")
    print("   Tip: Increase Atmosphere density or SUN energy if needed.")

    # Output path
    output_dir = os.path.join(os.environ.get('WORKDIR', '/tmp'), 'renders')
    os.makedirs(output_dir, exist_ok=True)

    scene = bpy.context.scene
    scene.render.filepath = os.path.join(output_dir, f"flat_horizon.png")
    print(f"Saving render to: {scene.render.filepath}")

    print(f"→ Rendering ...")
    bpy.ops.render.render(write_still=True)
    print(f"✓ Finished")


if __name__ == "__main__":
    main()
