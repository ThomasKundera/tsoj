import os
import math
from mathutils import Vector
import bpy

from tkblender import add_axis_helpers, look_at,m

def clear_scene():
    """Remove all objects from the current scene."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def setup_world_background():
    """Set the world background to pure black (space-like dark)."""
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    # Clear existing nodes
    for node in list(nodes):
        nodes.remove(node)

    # Create a simple black background
    bg = nodes.new('ShaderNodeBackground')
    bg.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0)   # pure black
    bg.inputs['Strength'].default_value = 1.0

    output = nodes.new('ShaderNodeOutputWorld')

    # Connect
    links.new(bg.outputs['Background'], output.inputs['Surface'])


def setup_camera():
    """Create and position the camera."""
    cam_data = bpy.data.cameras.new(name="Camera")
    # FOV
    cam_data.lens = 18
    #cam_data.lens = 50       # default
    # cam_data.lens = 85

    cam_obj = bpy.data.objects.new("Camera", cam_data)
    
    cam_obj.location = (6*m, -8*m, 6*m)
    #cam_obj.rotation_euler = (math.radians(90), 0, 0)
    look_at(cam_obj, (1*m, 2*m, 0))

    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    
def setup_sun_light():
    """Add a weak sun light so the sphere shape remains visible."""
    light_data = bpy.data.lights.new(name="Sun", type='SUN')
    light_obj = bpy.data.objects.new("Sun", light_data)
    
    light_obj.location = (5, 5, 10)
    light_obj.rotation_euler = (1, 0, 0)
    
    bpy.context.scene.collection.objects.link(light_obj)
    light_data.energy = 1.0   # keep it dim


def create_emissive_material(name="EmissiveSphere"):
    """Create and return the emissive material only."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    for node in list(nodes):
        nodes.remove(node)

    # Emission
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (1.0, 0.6, 0.3, 1.0)
    emission.inputs['Strength'].default_value = 5.0

    # Diffuse
    diffuse = nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.inputs['Color'].default_value = (1.0, 0.7, 0.5, 1.0)

    # Mix
    mix = nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = 0.15

    # Output
    output = nodes.new('ShaderNodeOutputMaterial')

    # Connect
    links.new(emission.outputs['Emission'], mix.inputs[1])
    links.new(diffuse.outputs['BSDF'], mix.inputs[2])
    links.new(mix.outputs['Shader'], output.inputs['Surface'])

    return mat


def create_emissive_sphere(loc=(0,0,0),r=1):
    """Create sphere + apply smooth + subsurf + emissive material."""
    
    # Create sphere
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=96,
        ring_count=48,
        radius=r,
        location=loc
    )
    
    sphere = bpy.context.active_object
    sphere.name = "EmissiveSphere"

    # Smooth + Subdivision
    bpy.ops.object.shade_smooth()
    subsurf = sphere.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = 2
    subsurf.render_levels = 3

    # Apply material
    mat = create_emissive_material()
    sphere.data.materials.append(mat)
    
    return sphere


def setup_render_stamp():
    """Configure timestamp stamp (date/time) on the bottom of the image."""
    scene = bpy.context.scene
    
    scene.render.use_stamp = True
    scene.render.use_stamp_date = True          # shows date + time
    scene.render.stamp_font_size = 7
    scene.render.stamp_foreground = (1.0, 1.0, 1.0, 1.0)   # white
    scene.render.stamp_background = (0.0, 0.0, 0.0, 0.7)   # semi-transparent black

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
        scale = 200 + (1920 - 200) * (quality / 5)
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

    # Output path
    output_dir = os.path.join(os.environ.get('WORKDIR', '/tmp'), 'renders')
    os.makedirs(output_dir, exist_ok=True)
    
    scene.render.filepath = os.path.join(output_dir, 'glowing_sphere.png')
    print(f"Saving render to: {scene.render.filepath}")

    # Stamps
    setup_render_stamp()

    # Quality
    setup_render_quality(quality=1)

    # Engine
    # bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    setup_cycles_cpu(quality=1)


def main():
    """Main function - orchestrates the entire scene creation and render."""
    print("Starting scene setup...")

    clear_scene()
    setup_world_background()
    add_axis_helpers(length=20*m)
    for i in range(1,10):
        create_emissive_sphere((0, 10*i*m, 0), 1.0*m)
    setup_camera()
    #setup_sun_light()
    setup_render_settings()

    print("Rendering...")
    bpy.ops.render.render(write_still=True)
    print("GPU Backend:", bpy.context.preferences.system.gpu_backend)
    print("Eevee TAA Samples:", bpy.context.scene.eevee.taa_render_samples)
    print("Raytracing enabled:", bpy.context.scene.eevee.use_raytracing)

    print("✅ Render finished! Image saved as glowing_sphere.png")


# ======================
# Run the script
# ======================
if __name__ == "__main__":
    main()
