import os
import math
from mathutils import Vector
import bpy

from tkblender import add_axis_helpers, look_at,m, km

def clear_scene():
    """Remove all objects from the current scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def setup_world_background():
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    # Clear existing nodes
    for node in list(nodes):
        nodes.remove(node)

    # Create a simple black background
    bg = nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.0, 0.0, 0.05, 1.0)  # very dark blue instead of pure black
    bg.inputs['Strength'].default_value = 1.0

    output = nodes.new('ShaderNodeOutputWorld')

    # Connect
    links.new(bg.outputs['Background'], output.inputs['Surface'])

def create_ground_plane():
    bpy.ops.mesh.primitive_plane_add(size=100.0 * 1000, location=(0, 0, 0))  # reduced from 100*km for testing
    ground = bpy.context.active_object
    ground.name = "Ground"

    # Create material
    mat_ground = bpy.data.materials.new(name="Ground_Checker_Mat")
    mat_ground.use_nodes = True
    nodes = mat_ground.node_tree.nodes
    links = mat_ground.node_tree.links
    for node in list(nodes):
        nodes.remove(node)

    # Add nodes for checker texture
    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (600, 0)

    principled = nodes.new("ShaderNodeBsdfPrincipled")
    principled.inputs["Roughness"].default_value = 0.8

    checker = nodes.new("ShaderNodeTexChecker")
    checker.inputs["Scale"].default_value = 2000.0      # adjusted for better visibility
    checker.inputs["Color1"].default_value = (0.4, 0.3, 0.2, 1.0)   # brown
    checker.inputs["Color2"].default_value = (0.1, 0.3, 0.6, 1.0)   # blue

    links.new(checker.outputs["Color"], principled.inputs["Base Color"])
    links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    ground.data.materials.append(mat_ground)
    return ground


def create_sun(location=(0, 0, 5000*km)):
    # Visual sphere (emissive)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=50*km, location=location)
    sun_sphere = bpy.context.active_object
    sun_sphere.name = "Sun_Sphere"

    mat_sun = bpy.data.materials.new(name="Sun_Mat")
    mat_sun.use_nodes = True
    nodes = mat_sun.node_tree.nodes
    for n in list(nodes):
        nodes.remove(n)

    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (1.0, 0.95, 0.8, 1.0)
    emission.inputs['Strength'].default_value = 100000.0   # ← MUCH STRONGER

    output = nodes.new('ShaderNodeOutputMaterial')
    links = mat_sun.node_tree.links
    links.new(emission.outputs['Emission'], output.inputs['Surface'])
    sun_sphere.data.materials.append(mat_sun)

    # Strong point light (this actually lights the scene)
    bpy.ops.object.light_add(type='POINT', location=location)
    sun_light = bpy.context.active_object
    sun_light.name = "Sun_Light"
    sun_light.data.energy = 5000000.0          # ← Very strong
    sun_light.data.shadow_soft_size = 50.0

    return sun_sphere, sun_light

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


def setup_render_quality(quality: int = 0):
    """Set render quality. 0 = very fast/low, 5 = high quality (HD)."""
    scene = bpy.context.scene

    # Resolution
    if quality == 0:
        scene.render.resolution_x = 200
        scene.render.resolution_y = 160
    elif quality == 5:
        scene.render.resolution_x = 1920
        scene.render.resolution_y = 1080
    else:
        scale = 200 + (1920 - 200) * (math.pow(quality / 5, 2))
        scene.render.resolution_x = int(scale)
        scene.render.resolution_y = int(scale * 0.8)

    if quality <= 1:                    # Low / fastest
        scene.eevee.taa_render_samples = 4
        scene.eevee.use_raytracing = False
        scene.eevee.use_fast_gi = False
    elif quality <= 3:                  # Medium
        scene.eevee.taa_render_samples = 16
        scene.eevee.use_raytracing = True
        scene.eevee.use_fast_gi = True
        scene.eevee.fast_gi_quality = 0.3
    else:                               # High (4-5)
        scene.eevee.taa_render_samples = 64
        scene.eevee.use_raytracing = True
        scene.eevee.use_fast_gi = True
        scene.eevee.fast_gi_quality = 0.8
        scene.eevee.ray_tracing_options.screen_trace_quality = 0.6

    print(f"Render quality set to level {quality} ({scene.render.resolution_x}x{scene.render.resolution_y})")


def setup_cycles_cpu(quality: int = 3):
    """Configure Cycles for heavy CPU rendering (good for 128 cores)."""
    scene = bpy.context.scene

    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'

    # Quality based samples
    if quality <= 1:
        scene.cycles.samples = 16
        #scene.cycles.noise_threshold = 0.1
    elif quality <= 3:
        scene.cycles.samples = 64
        #scene.cycles.noise_threshold = 0.05
    else:  # high
        scene.cycles.samples = 128
        #scene.cycles.noise_threshold = 0.03

    # Performance tweaks for many cores
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4

    print(f"✅ Cycles CPU enabled (quality {quality})")


def setup_render_settings():
    """Configure render engine, resolution, output path, etc."""
    #bpy.context.preferences.system.gpu_backend = 'OPENGL'
    scene = bpy.context.scene

    scene.render.resolution_x = 200
    scene.render.resolution_y = 160

    # Stamps
    setup_render_stamp()

    # Quality
    qual=1
    setup_render_quality(quality=qual)

    # Engine
    # bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    setup_cycles_cpu(quality=qual)
    scene.render.threads_mode = 'AUTO'
    #scene.render.threads_mode = 'FIXED'
    #scene.render.threads = mp.cpu_count()//4

    print(f"✅ Render settings set (threads: {scene.render.threads})")


def setup_camera(name,camloc, target):
    """Create and position the camera."""
    cam_data = bpy.data.cameras.new(name=name)

    # FOV
    cam_data.lens = 15
    #cam_data.lens = 50       # default
    # cam_data.lens = 85

    cam_data.clip_start = 0.1*m
    cam_data.clip_end = 10000*km

    cam_obj = bpy.data.objects.new("Camera", cam_data)

    cam_obj.location = camloc
    look_at(cam_obj,camloc,target)

    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    return cam_obj


def render_with_camera(name, location, target):
    """Render the scene with a specific camera position"""
    scene = bpy.context.scene
    cam_obj = setup_camera(name, location, target)

    # Set output filename based on camera name

    # Output path
    output_dir = os.path.join(os.environ.get('WORKDIR', '/tmp'), 'renders')
    os.makedirs(output_dir, exist_ok=True)

    scene = bpy.context.scene
    scene.render.filepath = os.path.join(output_dir, f"glowing_spheres_{name}.png")
    print(f"Saving render to: {scene.render.filepath}")

    print(f"→ Rendering {name} ...")
    bpy.ops.render.render(write_still=True)
    print(f"✓ Finished {name}")

    return cam_obj

def render_view(view_name, cam_location, target):
    """Render one view in a separate Blender process."""

    clear_scene()
    #setup_world_background()
    create_ground_plane()
    setup_render_settings()

    render_with_camera(view_name, cam_location, target)


def main():
    """Main function - orchestrates the entire scene creation and render."""
    views = [
        ("front", ( 0*m, 0*m,  2*m), (10*m, 10*m,  0*m)),
    ]

    for view_name, cam_location, target in views:
        render_view(view_name, cam_location, target)

    print("GPU Backend:", bpy.context.preferences.system.gpu_backend)
    print("Eevee TAA Samples:", bpy.context.scene.eevee.taa_render_samples)
    print("Raytracing enabled:", bpy.context.scene.eevee.use_raytracing)

    print("✅ Render finished! Image saved as glowing_sphere.png")


# ======================
# Run the script
# ======================
if __name__ == "__main__":
    main()
