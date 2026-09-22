"""Give only the two lampshades a restrained, softly backlit fabric treatment."""
import bpy, os, json, sys
from mathutils import Vector

s = bpy.context.scene
root = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(root, 'outputs/web-room-v135')
os.makedirs(out, exist_ok=True)
target = os.path.join(root, 'outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v135-translucent-lamps.blend')
assert 'v134-white-interactives' in bpy.data.filepath
assert not os.path.exists(target) or '--refine-owned-preview' in sys.argv
s.frame_set(1)
names = ['DESK_LampShade', 'FLOOR_LAMP_V129_DESK_LampShade']
before = {o.name: tuple(v for row in o.matrix_world for v in row) for o in s.objects}
slots_before = {o.name: [slot.material.name if slot.material else None for slot in o.material_slots] for o in s.objects}
lights_before = {o.name: (o.data.energy, tuple(o.data.color)) for o in s.objects if o.type == 'LIGHT'}
shared = bpy.data.node_groups['INTERACT_SharedAmberRhythm_v119']
pulse_before = [(f.data_path, f.driver.expression) for f in shared.animation_data.drivers]
changes = []
for name in names:
    obj = bpy.data.objects[name]
    copies = {}
    for slot in obj.material_slots:
        original = slot.material
        assert original and original.name.startswith('CATH_ROOM_')
        if original.name not in copies:
            mat = original.copy()
            mat.name = name + '_SoftFabric_V135_' + original.name
            nodes, links = mat.node_tree.nodes, mat.node_tree.links
            output = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
            base = output.inputs['Surface'].links[0].from_socket
            fabric = nodes.new('ShaderNodeBsdfTranslucent')
            fabric.name = 'Soft light through fabric'
            fabric.inputs['Color'].default_value = (.65, .59, .5, 1)
            scatter = nodes.new('ShaderNodeMixShader')
            scatter.name = 'Mostly opaque fabric'
            scatter.inputs[0].default_value = .3
            links.new(base, scatter.inputs[1])
            links.new(fabric.outputs[0], scatter.inputs[2])
            transparent = nodes.new('ShaderNodeBsdfTransparent')
            opacity = nodes.new('ShaderNodeMixShader')
            opacity.name = 'Twelve percent shade transparency'
            opacity.inputs[0].default_value = .12
            links.new(scatter.outputs[0], opacity.inputs[1])
            links.new(transparent.outputs[0], opacity.inputs[2])
            # A soft center-to-rim falloff avoids a uniformly luminous solid shell.
            coords = nodes.new('ShaderNodeTexCoord')
            xyz = nodes.new('ShaderNodeSeparateXYZ')
            links.new(coords.outputs['Generated'], xyz.inputs[0])
            last = xyz.outputs['Z']
            for operation, value in [('SUBTRACT', .5), ('ABSOLUTE', 0), ('MULTIPLY', 2), ('SUBTRACT', 1)]:
                node = nodes.new('ShaderNodeMath'); node.operation = operation
                if operation == 'SUBTRACT' and value == 1:
                    node.inputs[0].default_value = 1; links.new(last, node.inputs[1])
                else:
                    links.new(last, node.inputs[0]); node.inputs[1].default_value = value
                last = node.outputs[0]
            strength = nodes.new('ShaderNodeMapRange')
            strength.name = 'Restrained glow softer at the rims'
            strength.clamp = True
            strength.inputs['From Min'].default_value = 0
            strength.inputs['From Max'].default_value = 1
            dark = 'DARK' in original.name
            strength.inputs['To Min'].default_value = .035 if dark else .06
            strength.inputs['To Max'].default_value = .13 if dark else .22
            links.new(last, strength.inputs['Value'])
            glow = nodes.new('ShaderNodeEmission')
            glow.name = 'Subtle warm shade glow'
            glow.inputs['Color'].default_value = (1, .89, .74, 1)
            links.new(strength.outputs[0], glow.inputs['Strength'])
            add = nodes.new('ShaderNodeAddShader')
            links.new(opacity.outputs[0], add.inputs[0])
            links.new(glow.outputs[0], add.inputs[1])
            links.new(add.outputs[0], output.inputs['Surface'])
            mat.surface_render_method = 'DITHERED'
            copies[original.name] = mat
        slot.link = 'OBJECT'
        slot.material = copies[original.name]
    bounds = [obj.matrix_world @ Vector(p) for p in obj.bound_box]
    center = sum(bounds, Vector()) / 8
    light = bpy.data.lights.new(name + '_InternalSoftLight_V135', 'POINT')
    light.energy = 3 if name == 'DESK_LampShade' else 4
    light.color = (1, .89, .74)
    light.shadow_soft_size = .065 if name == 'DESK_LampShade' else .08
    lamp = bpy.data.objects.new(light.name, light)
    s.collection.objects.link(lamp); lamp.location = center
    changes.append(dict(object=name, materials=[m.name for m in copies.values()], transparency=.12, fabricScatter=.3, internalLightWatts=light.energy))

assert all(before[n] == tuple(v for row in bpy.data.objects[n].matrix_world for v in row) for n in before)
assert all(slots_before[n] == [slot.material.name if slot.material else None for slot in bpy.data.objects[n].material_slots] for n in slots_before if n not in names)
assert all(lights_before[n] == (bpy.data.objects[n].data.energy, tuple(bpy.data.objects[n].data.color)) for n in lights_before)
assert tuple(shared.nodes['Emission'].inputs['Color'].default_value) == (1, 1, 1, 1)
assert pulse_before == [(f.data_path, f.driver.expression) for f in shared.animation_data.drivers]
s.camera = bpy.data.objects['CAM_APPROVED_GREETING_Restored_v119']
bpy.ops.wm.save_as_mainfile(filepath=target)
with open(os.path.join(out, 'lamp-audit.json'), 'w') as f:
    json.dump(dict(source=bpy.data.filepath, changes=changes, originalTransformsUnchanged=True, otherMaterialsUnchanged=True, existingLightsUnchanged=True, whitePulseUnchanged=True), f, indent=2)
s.render.resolution_percentage = 100
s.eevee.taa_render_samples = 32
for frame in [1, 31, 91]:
    s.frame_set(frame)
    s.render.filepath = os.path.join(out, f'lamp-probe-{frame:03d}.png')
    bpy.ops.render.render(write_still=True)
print('V135_LAMPS_PREPARED', flush=True)
