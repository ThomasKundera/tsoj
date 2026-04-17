import os
import multiprocessing as mp
import math
from mathutils import Vector
import colorsys
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

    
def setup_sun_light():
    """Add a weak sun light so the sphere shape remains visible."""
    light_data = bpy.data.lights.new(name="Sun", type='SUN')
    light_obj = bpy.data.objects.new("Sun", light_data)

    light_obj.location = (5, 5, 10)
    light_obj.rotation_euler = (1, 0, 0)

    bpy.context.scene.collection.objects.link(light_obj)
    light_data.energy = 1.0   # keep it dim

def create_emissive_material(hue: float = 0.1, strength: float = 5.0, name=None):
    """Create emissive material with custom hue.

    hue: 0.0 = red, 0.1 = orange, 0.33 = yellow, 0.66 = blue, 0.8 = purple, etc.
    """
    if name is None:
        name = f"Emissive_{int(hue*360):03d}"   # e.g. Emissive_036 for orange

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    for node in list(nodes):
        nodes.remove(node)

    # Emission node (the glow)
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (*colorsys.hsv_to_rgb(hue, 0.95, 1.0), 1.0)
    emission.inputs['Strength'].default_value = strength

    # Small diffuse for subtle surface
    diffuse = nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.inputs['Color'].default_value = (*colorsys.hsv_to_rgb(hue, 0.7, 0.9), 1.0)

    mix = nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = 0.15

    output = nodes.new('ShaderNodeOutputMaterial')

    # Connect nodes
    links.new(emission.outputs['Emission'], mix.inputs[1])
    links.new(diffuse.outputs['BSDF'], mix.inputs[2])
    links.new(mix.outputs['Shader'], output.inputs['Surface'])

    return mat


def create_colored_material(hue: float = 0.1, strength: float = 5.0, name=None):
    """Create a mainly colored sphere with only a subtle glow (like the original request)."""
    
    if name is None:
        name = f"Colored_{int(hue*360):03d}"

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    for node in list(nodes):
        nodes.remove(node)

    # Main colored diffuse / Principled BSDF
    principled = nodes.new('ShaderNodeBsdfPrincipled')
    color = colorsys.hsv_to_rgb(hue, 0.95, 0.95)
    principled.inputs['Base Color'].default_value = (*color, 1.0)
    principled.inputs['Roughness'].default_value = 0.3          # slightly shiny
    principled.inputs['Metallic'].default_value = 0.0

    # Very subtle emission (just a soft glow)
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (*color, 1.0)
    emission.inputs['Strength'].default_value = strength        # usually small: 1.0 ~ 8.0

    # Mix them (mostly diffuse, small emission)
    mix = nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = 0.12                      # 12% emission, 88% colored surface

    output = nodes.new('ShaderNodeOutputMaterial')

    # Connect
    links.new(principled.outputs['BSDF'], mix.inputs[1])
    links.new(emission.outputs['Emission'], mix.inputs[2])
    links.new(mix.outputs['Shader'], output.inputs['Surface'])

    return mat


def create_emissive_sphere(loc=(0,0,0),r=1,hue=0.1):
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
    mat = create_emissive_material(hue=hue)
    sphere.data.materials.append(mat)

    return sphere


def create_colored_sphere(loc=(0,0,0),r=1,hue=0.1):
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
    mat = create_colored_material(hue=hue)
    sphere.data.materials.append(mat)

    return sphere


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
    qual=3
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
    cam_data.lens = 30
    #cam_data.lens = 50       # default
    # cam_data.lens = 85

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

def render_view(view_name, cam_location, target):
    """Render one view in a separate Blender process."""

    clear_scene()
    setup_world_background()
    add_axis_helpers(length=20*m)
    nmax=20
    create_colored_sphere(( 0  ,  6*m, 0  ), .5*m, 1)
    create_colored_sphere(( 0  ,  0  , 6*m), .5*m, 1)
    for i in range(1,nmax+1):
        create_colored_sphere(( 0    , 20*i*m,  0    ), 1.0*m, i/nmax)
        create_colored_sphere(( 0    ,  0    , 20*i*m), 1.0*m, i/nmax)
    setup_sun_light()
    setup_render_settings()

    render_with_camera(view_name, cam_location, target)


def main():
    """Main function - orchestrates the entire scene creation and render."""
    views = [
        ("front", ( 8*m, - 9*m,  4*m), (1*m, 20*m,  2*m)),
        ("up"   , ( 12*m, -10*m,-20*m), (1*m,  1*m, 20*m)),
    ]

    #num_processes = min(8, len(views))   # Adjust: 8–16 is usually good on 128 cores
    #with mp.Pool(processes=num_processes) as pool:
    #    pool.starmap(render_view, views)

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
