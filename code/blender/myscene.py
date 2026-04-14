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

def setup_camera():
    """Create and position the camera."""
    cam_data = bpy.data.cameras.new(name="Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    
    cam_obj.location = (1*m, -1*m, 1*m)
    #cam_obj.rotation_euler = (math.radians(90), 0, 0)
    look_at(cam_obj, (0, 10*m, 0))
    
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


def setup_render_settings():
    """Configure Cycles render settings (safe for Ubuntu apt version)."""
    scene = bpy.context.scene
    #scene.render.engine = 'CYCLES'
    scene.render.engine = 'BLENDER_EEVEE'
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 200
    scene.render.resolution_y = 160

    scene = bpy.context.scene
    scene.render.use_stamp = True
    scene.render.use_stamp_date = True
    scene.render.stamp_font_size = 7
    scene.render.stamp_foreground = (1.0, 1.0, 1.0, 1.0) 
    scene.render.stamp_background = (0.0, 0.0, 0.0, 0.7)

    output_dir = os.path.join(os.environ.get('WORKDIR', '/tmp'), 'renders')
    print(f"Saving render to: {output_dir}")
    os.makedirs(output_dir, exist_ok=True)

    scene.render.filepath = os.path.join(output_dir, 'glowing_sphere.png')
    #scene.render.filepath = os.path.join('/tmp','glowing_sphere.png')

def main():
    """Main function - orchestrates the entire scene creation and render."""
    print("Starting scene setup...")

    clear_scene()
    setup_world_background()
    add_axis_helpers()
    create_emissive_sphere((0, 10, 0), 1.0)
    setup_camera()
    #setup_sun_light()
    setup_render_settings()

    print("Rendering...")
    bpy.ops.render.render(write_still=True)
    
    print("✅ Render finished! Image saved as glowing_sphere.png")


# ======================
# Run the script
# ======================
if __name__ == "__main__":
    main()
