import os
import bpy
import math
from mathutils import Vector

from tkblender import add_axis_helpers, look_at,cm, m, km

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

def create_barbed_wire():
    """Creates a single horizontal barbed wire strand across the scene"""
    
    wire_length = 120 * m
    wire_height = 8 * m
    wire_y = 10 * m
    
    # Create straight curve
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, wire_y, wire_height))
    wire = bpy.context.active_object
    wire.name = "Barbed_Wire"
    
    # Make it long and straight
    spline = wire.data.splines[0]
    spline.bezier_points[0].co = (-wire_length/2, 0, 0)
    spline.bezier_points[1].co = ( wire_length/2, 0, 0)
    
    # Convert to mesh
    bpy.ops.object.convert(target='MESH')
    
    # Add Skin modifier for thickness
    skin_mod = wire.modifiers.new(name="Skin", type='SKIN')
    skin_mod.branch_smoothing = 0.0
    
    # Set wire thickness
    skin_layer = wire.data.skin_vertices[0]
    for skin_vert in skin_layer.data:
        skin_vert.radius = (5*cm,5*cm)   # ~1.2 cm thick
    
    # Slight sag at the ends for realism
    verts = wire.data.vertices
    if len(verts) >= 2:
        verts[0].co.z -= 0.12 * m
        verts[-1].co.z -= 0.12 * m
    
    # === Material ===
    mat = bpy.data.materials.new(name="Barbed_Wire_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    for node in list(nodes):
        nodes.remove(node)

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    
    bsdf.inputs['Base Color'].default_value = (0.07, 0.075, 0.08, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.92
    bsdf.inputs['Roughness'].default_value = 0.48
    
    # Safe way to set specular reflection (works in Blender 4.2 → 5.1)
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.6
    elif 'IOR Level' in bsdf.inputs:
        bsdf.inputs['IOR Level'].default_value = 0.6
    elif 'Specular' in bsdf.inputs:
        bsdf.inputs['Specular'].default_value = 0.5

    output = nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    wire.data.materials.append(mat)

    print(f"✅ Barbed wire created at height {wire_height/m:.1f}m")
    return wire


def setup_camera():
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    cam_obj.location = (0*m, 0*m, 8*m) 

    # Look toward horizon
    direction = Vector((0*m, 500*m, 8*m)) - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    cam_data.lens = 50
    cam_data.clip_start = 0.1
    cam_data.clip_end = 2000*m

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

    create_sun()
    create_barbed_wire()

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
