"""Restrained grayscale player, silhouette-only contours and 0.2s fade delay."""
import bpy, bmesh, os, json

assert bpy.data.filepath.endswith('v143-simplified-pivot-sleeve-fade.blend')
target = os.path.join(os.path.dirname(bpy.data.filepath), 'lofi-room-cathode-glm53f-city-v144-themed-player-delayed-fade.blend')
assert not os.path.exists(target), target
scene = bpy.context.scene
sleeve = bpy.data.objects['V138_Playback_Sleeve_Rig']
poses = []
for frame in range(1, 145):
    scene.frame_set(frame)
    poses.append((sleeve.location.copy(), sleeve.rotation_quaternion.copy(), sleeve.scale.copy(), sleeve.matrix_world.copy()))
sleeve.animation_data_clear()
# 24 fps: 4.8 frames is exactly 0.2 seconds. Keep the long fade duration.
start, end = 16.8, 48.8
for frame, (location, rotation, scale, _) in enumerate(poses, 1):
    scene.frame_set(frame)
    sleeve.location, sleeve.rotation_quaternion, sleeve.scale = location, rotation, scale
    t = max(0., min(1., (frame-start)/(end-start)))
    sleeve['opacity'] = 1-t*t*(3-2*t)
    for path in ('location', 'rotation_quaternion', 'scale', '["opacity"]'):
        sleeve.keyframe_insert(path, frame=frame)

def material(name, value, outline=False):
    mat = bpy.data.materials.new('V138_Theme_'+name)
    mat.diffuse_color = (value, value, value, 1)
    mat.use_nodes = True
    if outline:
        mat.node_tree.nodes.clear()
        output = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
        emission = mat.node_tree.nodes.new('ShaderNodeEmission')
        emission.inputs['Color'].default_value = (value, value, value, 1)
        mat.node_tree.links.new(emission.outputs[0], output.inputs['Surface'])
        mat.use_backface_culling = True
        mat['review_unlit'] = True
        mat['review_front_side'] = True
    else:
        node = mat.node_tree.nodes.get('Principled BSDF')
        node.inputs['Base Color'].default_value = (value, value, value, 1)
        node.inputs['Roughness'].default_value = .9
        node.inputs['Metallic'].default_value = 0
        node.inputs['Specular IOR Level'].default_value = .15
        mat['review_roughness'] = .9
    return mat

charcoal = material('Charcoal', .065)
gray = material('Graphite', .105)
accent = material('SoftGray', .19)
ink = material('Silhouette', .006, True)
scene.frame_set(1)
parts = []
for ob in list(scene.objects):
    if ob.hide_render or ob.type not in ('MESH', 'CURVE'): continue
    if not ob.name.startswith(('V138_Pivot_', 'V138_ArmRest_', 'V138_Tonearm', 'V138_Headshell', 'V138_Player_Platter', 'V138_Platter_Rim', 'V138_Spindle')): continue
    if any(k in ob.name for k in ('Seam', 'Slot', 'Edges', 'Outline')): continue
    mat = accent if any(k in ob.name for k in ('Collar', 'MountFlange', 'Rim', 'Spindle')) else gray if any(k in ob.name for k in ('Terrace', 'Skirt', 'Base', 'SocketLip', 'Platter')) else charcoal
    # Object-local assignments avoid altering materials shared by books/records.
    for slot in ob.material_slots:
        slot.link = 'OBJECT'
        slot.material = mat
    parts.append(ob)

# Reverse-wound, slightly expanded copies draw only outer silhouettes, never a
# triangulated wireframe. Children follow each source part's exact transform.
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
outlines = []
for ob in parts:
    if any(k in ob.name for k in ('MoldedPad', 'ClampHinge', 'ClampTab', 'Rim', 'Spindle')): continue
    mesh = bpy.data.meshes.new_from_object(ob.evaluated_get(deps))
    bm = bmesh.new(); bm.from_mesh(mesh); bm.normal_update()
    width = .00016
    for vertex in bm.verts: vertex.co += vertex.normal * width
    bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    bm.to_mesh(mesh); bm.free(); mesh.update()
    mesh.materials.clear(); mesh.materials.append(ink)
    for poly in mesh.polygons: poly.material_index = 0
    outline = bpy.data.objects.new(ob.name+'_ThemeOutline', mesh)
    bpy.data.collections['V138_PLAYER_REVIEW'].objects.link(outline)
    outline.parent = ob
    outline['contour_width_m'] = width
    outlines.append(outline.name)

max_error = 0.
for frame, pose in enumerate(poses, 1):
    scene.frame_set(frame); bpy.context.view_layer.update()
    max_error = max(max_error, max(abs(sleeve.matrix_world[r][c]-pose[3][r][c]) for r in range(4) for c in range(4)))
assert max_error < 1e-6
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=target)
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'blender/outputs/review-v144')
os.makedirs(out, exist_ok=True)
with open(os.path.join(out, 'theme-audit.json'), 'w') as f:
    json.dump({'fadeDelaySeconds': .2, 'fadeStartFrame': start, 'fadeEndFrame': end, 'maxSleevePoseError': max_error, 'themedParts': [o.name for o in parts], 'silhouettes': outlines, 'contourWidthMeters': .00016, 'palette': [.006,.065,.105,.19]}, f, indent=2)
print('V144_THEME_COMPLETE', target)
