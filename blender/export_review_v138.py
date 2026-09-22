"""Export only approval models/actions, not new prerecorded room media."""
import bpy, os, json, math
from mathutils import Matrix, Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'public/review/v138');os.makedirs(OUT,exist_ok=True)
assert bpy.data.filepath.endswith(('v138-player-book-review.blend', 'v139-anchored-tonearm.blend', 'v140-reference-tonearm.blend', 'v141-solid-pivot-j-arm.blend', 'v142-detailed-pivot-rest.blend', 'v143-simplified-pivot-sleeve-fade.blend', 'v144-themed-player-delayed-fade.blend', 'v145-lit-player-wireframe.blend', 'v146-seated-blank-vinyl.blend', 'v147-personal-polaroids.blend', 'v148-delayed-record-spin.blend', 'v149-approved-project-covers.blend'))
main=bpy.context.scene

def array(m):return [round(m[r][c],7) for c in range(4) for r in range(4)]
def appearance(m,name):
    if m and m.get('polaroid_texture'):
        return {'color':[.65]*3,'texture':m['polaroid_texture'],'unlit':True,'grayscale':True}
    if m and m.get('logical_model')=='record-player' and m.node_tree.nodes.get('SWEEP_CLOCK'):
        emit=next(n for n in m.node_tree.nodes if n.type=='EMISSION')
        return {'color':[.006]*3,'texture':None,'unlit':True,'frontSide':bool(m.get('review_front_side')),
                'sweep':{'axis':list(m['world_axis']),'min':m['bounds_min'],'span':m['bounds_span'],'start':m['start_frame']-1,'duration':m['sweep_frames'],'cycle':m['cycle_frames'],'color':list(emit.inputs['Color'].default_value[:3])}}
    if m and m.get('review_front_side'):
        return {'color':list(m.diffuse_color[:3]),'texture':None,'unlit':True,'frontSide':True}
    if any(k in name for k in ('WIREFRAME','Outline','SleeveEdges')):
        return {'color':[.65]*3 if name=='CATHODE_WIREFRAME_BOOK_Mid_9' else [.006]*3,'texture':None}
    color=list(m.diffuse_color[:3]) if m else [.12]*3
    tex=None
    if m and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.type=='TEX_IMAGE' and n.image:
                base=os.path.basename(n.image.filepath)
                if '/v149/' in n.image.filepath.replace('\\','/') and os.path.exists(os.path.join(ROOT,'public/room/vinyl-art/v149',base)):
                    tex='/room/vinyl-art/v149/'+base
                elif os.path.exists(os.path.join(ROOT,'public/room/vinyl-art',base)):
                    tex='/room/vinyl-art/'+base
        if not m.name.startswith('V138_'):color=[.006]*3 if ('WIREFRAME' in name or 'Outline' in name or 'Edges' in name) else [.12]*3
        for n in m.node_tree.nodes:
            if n.type=='EMISSION' and not n.inputs['Color'].is_linked:color=list(n.inputs['Color'].default_value[:3])
    result={'color':color,'texture':tex}
    if m and 'review_roughness' in m:result['roughness']=m['review_roughness']
    return result

def export(name,scene,objects,roots,cam,frames):
    bpy.context.window.scene=scene;scene.frame_set(1);bpy.context.view_layer.update()
    rootnames={o.name for o in roots};meshes=[]
    def closest(o):
        while o:
            if o.name in rootnames:return o
            o=o.parent
        return None
    deps=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        if o.type not in ('MESH','CURVE') or o.hide_render:continue
        rig=closest(o);matrix=(rig.matrix_world.inverted() if rig else Matrix.Identity(4))@o.matrix_world
        ev=o.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles()
        pos=[];uv=[];indices=[];groups=[];lastmat=None
        for tri in mesh.loop_triangles:
            mi=tri.material_index
            if mi!=lastmat:groups.append({'start':len(indices),'count':0,'materialIndex':mi});lastmat=mi
            for vi,li in zip(tri.vertices,tri.loops):
                p=matrix@mesh.vertices[vi].co;pos.extend(round(v,7) for v in p);indices.append(len(indices))
                uv.extend(mesh.uv_layers.active.data[li].uv[:] if mesh.uv_layers.active else (0,0))
                groups[-1]['count']+=1
        item={'name':o.name,'rig':rig.name if rig else None,'positions':pos,'uvs':uv,'indices':indices,'groups':groups,'materials':[appearance(slot.material,o.name) for slot in o.material_slots] or [appearance(None,o.name)]}
        ev.to_mesh_clear()
        if o.type=='MESH' and o.data.shape_keys and 'Turning curl' in o.data.shape_keys.key_blocks:
            bend=o.data.shape_keys.key_blocks['Turning curl'];bend.value=1;bpy.context.view_layer.update()
            ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
            item['bent']=[round(v,7) for tri in me.loop_triangles for vi in tri.vertices for v in (matrix@me.vertices[vi].co)]
            ev.to_mesh_clear();bend.value=0;bpy.context.view_layer.update()
        meshes.append(item)
    samples=[]
    for frame in range(1,frames+1):
        scene.frame_set(frame);bpy.context.view_layer.update()
        samples.append({o.name:{'matrix':array(o.matrix_world),'opacity':float(o.get('opacity',1))} for o in roots})
    camera={'position':list(cam.location),'quaternion':[cam.rotation_euler.to_quaternion()[i] for i in (1,2,3,0)],'fov':math.degrees(2*math.atan(36/cam.data.lens/2/ (1280/900)))}
    with open(os.path.join(OUT,name+'.json'),'w') as f:json.dump({'fps':24,'frames':frames,'meshes':meshes,'samples':samples,'camera':camera},f,separators=(',',':'))
    print('V138_EXPORTED',name,len(meshes),os.path.getsize(os.path.join(OUT,name+'.json')),flush=True)

# Review shelf includes the real carcass, rack, and sleeves. Exclude the selected
# source sleeve: it is currently in the viewer's hand, not duplicated in the rack.
def shelf_object(o):
    return any(k in o.name for k in ('SHELF_Carcass','SHELF_VinylRack','BOOK_Mid_','INTERACT_Vinyl_','PROJECT_VINYL_V126_','INTERACT_RecordPlayer_Base','V138_','V148_LabelMark')) and o.type in ('MESH','CURVE')
obs=[o for o in main.objects if shelf_object(o) and not o.name.endswith(('_Vinyl_6','_Outline_6','_Record_6'))]
rigs=[bpy.data.objects[n] for n in ('V138_Playback_Record_Rig','V138_Playback_Sleeve_Rig','V138_Tonearm_Rig')]
if 'V138_Pivot_YawRig' in bpy.data.objects:rigs.append(bpy.data.objects['V138_Pivot_YawRig'])
export('player',main,obs,rigs,bpy.data.objects['CAM_V138_Player_Review'],144)
stack=[o for o in main.objects if 'BOOK_Mid_' in o.name or 'SHELF_Carcass' in o.name]
export('stack',main,stack,[],bpy.data.objects['CAM_V138_BookStack_Review'],1)
if 'CAM_V147_Polaroid_Review' in bpy.data.objects:
    photos=[o for o in main.objects if 'SHELF_Polaroid_' in o.name and not o.hide_render]
    export('photos',main,photos,[],bpy.data.objects['CAM_V147_Polaroid_Review'],1)
bs=bpy.data.scenes['V138_Book_Prototypes']
for kind in ('Hardback','Paperback'):
    root=bpy.data.objects['V138_'+kind+'_Root']
    allobs=list(root.children_recursive)
    rigs=[root]+[o for o in allobs if o.type=='EMPTY']
    # Front-facing book review, with a separate angled camera available in UI.
    cam=bs.camera;cam.location=(root.location.x-.06,-.66,.03);cam.rotation_euler=(Vector((root.location.x-.06,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=50
    export(kind.lower(),bs,allobs,rigs,cam,240)
print('V138_REVIEW_EXPORT_COMPLETE',flush=True)
