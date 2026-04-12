import os
import math
from mathutils import Vector
import bpy

def look_at(camera_obj, target):
    """Make camera look at a target point (like POV-Ray look_at)."""
    loc = camera_obj.matrix_world.to_translation()
    direction = Vector(target) - loc
    rot_quat = direction.to_track_quat('-Z', 'Y')   # Camera points -Z forward, +Y up
    camera_obj.rotation_euler = rot_quat.to_euler()

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

def add_axis_helpers(length=5.0, thickness=0.05, arrow_size=0.3, add_labels=True):
    """Add renderable X/Y/Z axis lines with arrowheads and optional text labels.
    
    Parameters:
        length (float): Total length of each axis line
        thickness (float): Diameter of the axis lines
        arrow_size (float): Size of the arrowhead cones
        add_labels (bool): Whether to add "X", "Y", "Z" text labels
    """
    collection = bpy.context.scene.collection
    
    # Helper to create a thin cylinder for the axis line
    def create_axis(name, color, direction):
        # Cylinder (main line)
        bpy.ops.mesh.primitive_cylinder_add(
            radius=thickness,
            depth=length,
            location=(0, 0, 0),
            rotation=direction
        )
        axis = bpy.context.active_object
        axis.name = name
        
        # Simple emissive material so it glows a bit and is easy to see
        mat = bpy.data.materials.new(name=f"Axis_{name}")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        for node in list(nodes):
            nodes.remove(node)
        
        emission = nodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value = color
        emission.inputs['Strength'].default_value = 10.0
        
        output = nodes.new('ShaderNodeOutputMaterial')
        mat.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
        
        axis.data.materials.append(mat)
        collection.objects.link(axis)  # ensure it's in scene
        return axis

    # X axis (red) - along positive X
    rot_x = (0, math.radians(90), 0)
    x_axis = create_axis("Axis_X", (1.0, 0.0, 0.0, 1.0), rot_x)
    
    # Y axis (green) - along positive Y
    rot_y = (math.radians(-90), 0, 0)
    y_axis = create_axis("Axis_Y", (0.0, 1.0, 0.0, 1.0), rot_y)
    
    # Z axis (blue) - along positive Z
    rot_z = (0, 0, 0)
    z_axis = create_axis("Axis_Z", (0.0, 0.0, 1.0, 1.0), rot_z)

    # Add arrowheads (cones) at the end of each axis
    def add_arrowhead(name, location, rotation, color):
        bpy.ops.mesh.primitive_cone_add(
            radius1=arrow_size,
            depth=arrow_size * 2,
            location=location,
            rotation=rotation
        )
        cone = bpy.context.active_object
        cone.name = f"Arrow_{name}"
        
        mat = bpy.data.materials.new(name=f"Arrow_{name}")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        for n in list(nodes): nodes.remove(n)
        em = nodes.new('ShaderNodeEmission')
        em.inputs['Color'].default_value = color
        em.inputs['Strength'].default_value = 15.0
        out = nodes.new('ShaderNodeOutputMaterial')
        mat.node_tree.links.new(em.outputs['Emission'], out.inputs['Surface'])
        
        cone.data.materials.append(mat)
        collection.objects.link(cone)

    # Arrowheads
    add_arrowhead("X", (length/2, 0, 0), (0, math.radians(90), 0), (1.0, 0.0, 0.0, 1.0))
    add_arrowhead("Y", (0, length/2, 0), (math.radians(-90), 0, 0), (0.0, 1.0, 0.0, 1.0))
    add_arrowhead("Z", (0, 0, length/2), (0, 0, 0), (0.0, 0.0, 1.0, 1.0))

    # Optional text labels (always face camera approximately)
    if add_labels:
        def create_label(text, location, color):
            bpy.ops.object.text_add(location=location)
            txt = bpy.context.active_object
            txt.name = f"Label_{text}"
            txt.data.body = text
            txt.data.size = 0.6
            txt.data.align_x = 'CENTER'
            txt.data.align_y = 'CENTER'
            
            mat = bpy.data.materials.new(name=f"Label_{text}")
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            for n in list(nodes): nodes.remove(n)
            em = nodes.new('ShaderNodeEmission')
            em.inputs['Color'].default_value = color
            em.inputs['Strength'].default_value = 20.0
            out = nodes.new('ShaderNodeOutputMaterial')
            mat.node_tree.links.new(em.outputs['Emission'], out.inputs['Surface'])
            txt.data.materials.append(mat)
            
            # Simple rotation to face camera better (adjust if needed)
            txt.rotation_euler = (math.radians(90), 0, 0)
            collection.objects.link(txt)
        
        create_label("X", (length/2 + 0.8, 0, 0), (1.0, 0.2, 0.2, 1.0))
        create_label("Y", (0, length/2 + 0.8, 0), (0.2, 1.0, 0.2, 1.0))
        create_label("Z", (0, 0, length/2 + 0.8), (0.2, 0.2, 1.0, 1.0))

    print("✅ Axis helpers added (X=red, Y=green, Z=blue)")
    
def create_emissive_sphere():
    """Create a smooth sphere and turn it into an emissive (glowing) light source."""
    
    # Create the sphere
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=96,
        ring_count=48,
        radius=1.5,
        location=(0, 10, 0)
    )
    
    sphere = bpy.context.active_object

    # Smooth shading + subdivision
    bpy.ops.object.shade_smooth()
    subsurf = sphere.modifiers.new(name="Subsurf", type='SUBSURF')
    subsurf.levels = 2
    subsurf.render_levels = 3

    # === Create emissive material ===
    mat = bpy.data.materials.new(name="EmissiveSphere")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Clear default nodes
    for node in list(nodes):
        nodes.remove(node)

    # Emission node (main light source)
    emission = nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (1.0, 0.6, 0.3, 1.0)   # warm orange
    emission.inputs['Strength'].default_value = 5.0

    # Small diffuse contribution for subtle surface detail
    diffuse = nodes.new('ShaderNodeBsdfDiffuse')
    diffuse.inputs['Color'].default_value = (1.0, 0.7, 0.5, 1.0)

    # Mix them
    mix = nodes.new('ShaderNodeMixShader')
    mix.inputs['Fac'].default_value = 0.15

    # Output
    output = nodes.new('ShaderNodeOutputMaterial')

    # Connect everything
    links.new(emission.outputs['Emission'], mix.inputs[1])
    links.new(diffuse.outputs['BSDF'], mix.inputs[2])
    links.new(mix.outputs['Shader'], output.inputs['Surface'])

    # Assign material
    sphere.data.materials.append(mat)
    
    return sphere


def setup_camera():
    """Create and position the camera."""
    cam_data = bpy.data.cameras.new(name="Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    
    cam_obj.location = (1, -1, 1)
    #cam_obj.rotation_euler = (math.radians(90), 0, 0)
    look_at(cam_obj, (0, 10, 0))
    
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
    scene.render.engine = 'CYCLES'
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 200
    scene.render.resolution_y = 160

    output_dir = os.path.join(os.environ.get('WORKDIR', '/tmp'), 'renders')
    os.makedirs(output_dir, exist_ok=True)

    scene.render.filepath = os.path.join(output_dir, 'glowing_sphere.png')
    #scene.render.filepath = os.path.join('/tmp','glowing_sphere.png')

def main():
    """Main function - orchestrates the entire scene creation and render."""
    print("Starting scene setup...")

    clear_scene()
    setup_world_background()
    add_axis_helpers()
    create_emissive_sphere()
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
