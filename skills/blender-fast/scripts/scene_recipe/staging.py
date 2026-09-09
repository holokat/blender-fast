"""Shared scene staging and explicit quality profiles."""
import bpy
from mathutils import Vector


def assign_changed(owner, key, value):
    """Avoid tagging Blender data dirty when a property already has this value."""
    current = getattr(owner, key)
    if isinstance(value, (tuple, list, Vector)):
        equal = len(current) == len(value) and all(abs(a - b) < 1e-6 for a, b in zip(current, value))
    else:
        equal = abs(current - value) < 1e-6
    if equal:
        return False
    setattr(owner, key, value)
    return True


def stage(scene, geometry, recipe):
    geometry.collection = scene.collection
    geometry.offset = Vector((0, 0, 0))
    for name, at, energy, color, size, target in [
        ('Key', (3, -8, 19), 5200, (1, .80, .57), 13, (0, 0, 1)),
        ('Fill', (-12, -1, 14), 4100, (.38, .59, 1), 12, (0, 1, 1)),
        ('Rim', (4, 12, 13), 3800, (.58, .79, 1), 9, (0, 2, 2)),
    ]:
        light = geometry.light(name, at, energy, color, size, target)
        light['recipe_stage_light'] = name.lower()
        light['recipe_base_energy'] = energy
    world = bpy.data.worlds.new('Recipe ambient')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.13, .19, .29, 1)
    scene.world = world
    camera = bpy.data.cameras.new('Recipe camera')
    obj = bpy.data.objects.new('Recipe camera', camera)
    scene.collection.objects.link(obj)
    camera.type = 'ORTHO'
    scene.camera = obj
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.render.use_stamp = False
    scene.render.use_stamp_filename = False
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = .01
    scene.cycles.max_bounces = 10
    scene.cycles.transmission_bounces = 8
    scene.cycles.seed = 2092026
    scene.cycles.use_animated_seed = False
    scene.render.use_compositing = False
    update_stage(scene, recipe)


def update_stage(scene, recipe):
    camera = recipe.get('camera', {})
    assign_changed(scene.camera, 'location', camera.get('at', (35, -46, 40)))
    target = Vector(camera.get('target', (0, 1, 1.4)))
    assign_changed(scene.camera, 'rotation_euler', tuple((target - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()))
    assign_changed(scene.camera.data, 'ortho_scale', camera.get('ortho_scale', 47))
    lighting = recipe.get('lighting', {})
    for obj in scene.objects:
        if obj.get('recipe_stage_light'):
            assign_changed(obj.data, 'energy', obj['recipe_base_energy'] * lighting.get(obj['recipe_stage_light'], 1))
    assign_changed(scene.world.node_tree.nodes['Background'].inputs['Strength'], 'default_value', .22 * lighting.get('world', 1))
    assign_changed(scene.view_settings, 'exposure', lighting.get('exposure', .5))


def configure(scene, profile):
    """Full resolution unless the profile explicitly says 'interactive'."""
    if profile not in ('opt1', 'optNEW', 'eevee', 'interactive'):
        raise ValueError(profile)
    scene.render.resolution_percentage = 50 if profile == 'interactive' else 100
    scene.render.use_persistent_data = True
    if profile in ('opt1', 'optNEW'):
        scene.render.engine = 'CYCLES'
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        for device in prefs.devices:
            device.use = device.type == 'METAL'
        if not any(d.use for d in prefs.devices):
            raise RuntimeError('This measured profile requires a Metal GPU; inspect another backend explicitly')
        prefs.metalrt = 'AUTO'
        scene.cycles.device = 'GPU'
        scene.cycles.samples = 64 if profile == 'opt1' else 8
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = 'OPENIMAGEDENOISE'
        scene.cycles.denoising_use_gpu = True
        devices = [d.name for d in prefs.devices if d.use]
        samples = scene.cycles.samples
    else:
        scene.render.engine = 'BLENDER_EEVEE'
        scene.eevee.taa_render_samples = 4 if profile == 'interactive' else 16
        scene.eevee.use_raytracing = True
        scene.eevee.use_fast_gi = True
        for mat in {m for obj in scene.objects if obj.type == 'MESH' for m in obj.data.materials if m}:
            if mat.use_nodes and any(n.type == 'BSDF_PRINCIPLED' and n.inputs['Transmission Weight'].default_value > 0 for n in mat.node_tree.nodes):
                mat.use_raytrace_refraction = True
                mat.thickness_mode = 'SLAB'
        devices, samples = ['Eevee GPU'], scene.eevee.taa_render_samples
    return {'profile': profile, 'engine': scene.render.engine, 'samples': samples,
            'resolution': [scene.render.resolution_x * scene.render.resolution_percentage // 100,
                           scene.render.resolution_y * scene.render.resolution_percentage // 100],
            'devices': devices, 'blender': bpy.app.version_string}
