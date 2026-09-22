"""Read-only scene audit; evaluates the actual sweep node graph numerically."""
import bpy,os,json,math,hashlib,array
from mathutils import Vector
s=bpy.context.scene;s.frame_set(1)
def fingerprint():
    objects={}
    for o in s.objects:
        item={'type':o.type,'matrix':[v for row in o.matrix_world for v in row]}
        if o.type=='MESH':
            data=array.array('f',[0])*(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',data)
            item['vertices']=hashlib.sha256(data.tobytes()).hexdigest();item['topology']=[len(o.data.edges),len(o.data.polygons)]
        if o.type=='LIGHT':item['light']=[o.data.energy,*o.data.color]
        objects[o.name]=item
    return objects
after=fingerprint();materials=[m for m in bpy.data.materials if m.name.startswith('CATHODE_V131_Travel_')]
def intensity(mat,point):
    def socket(sock):return output(sock.links[0].from_socket) if sock.is_linked else sock.default_value
    def output(sock):
        n=sock.node
        if n.type=='VALUE':return n.outputs[0].default_value
        if n.type=='NEW_GEOMETRY':return point
        if n.type=='VECT_MATH':return Vector(socket(n.inputs[0])).dot(Vector(socket(n.inputs[1])))
        if n.type=='MATH':
            a=socket(n.inputs[0]);b=socket(n.inputs[1])
            return {'SUBTRACT':lambda:a-b,'DIVIDE':lambda:a/b,'MULTIPLY':lambda:a*b,'MINIMUM':lambda:min(a,b),'FLOORED_MODULO':lambda:a%b}[n.operation]()
        if n.type=='MAP_RANGE':
            x,a,b=[socket(n.inputs[i]) for i in range(3)];t=max(0,min(1,(x-a)/(b-a)))
            return t*t*(3-2*t)
        raise AssertionError(n.type)
    emission=next(n for n in mat.node_tree.nodes if n.type=='EMISSION')
    return socket(emission.inputs['Strength'])
checks={}
for m in materials:
    axis=Vector(m['world_axis']);low=m['bounds_min'];span=m['bounds_span'];offset=m['start_frame']-1
    clock=m.node_tree.nodes['SWEEP_CLOCK'].outputs[0]
    curve=next(fc for layer in m.node_tree.animation_data.action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves)
    peaks=[];durations=[]
    for u in [0,.25,.5,.75,1]:
        point=axis*(low+span*u);values=[]
        for elapsed in range(241):
            clock.default_value=curve.evaluate(offset+1+elapsed);values.append(intensity(m,point))
        assert max(values)>.63,(m.name,u,max(values))
        assert abs(values[0]-values[240])<1e-5,(m.name,'seam')
        assert sum(v>.05 for v in values)>25,(m.name,'too brief')
        peaks.append(max(range(241),key=values.__getitem__));durations.append(sum(v>.05 for v in values))
    assert peaks==sorted(peaks) and peaks[-1]-peaks[0]>48,(m.name,peaks)
    checks[m['logical_model']]={'peakFramesAcrossModel':peaks,'visibleFramesPerPoint':durations,'span':span}
root=os.path.dirname(os.path.abspath(__file__));out=os.path.join(root,'outputs/web-room-v131')
original=os.path.join(root,'outputs/blender/glm-5-3-flash-iterations/lofi-room-cathode-glm53f-city-v130-cubby-monitor-pan.blend')
bpy.ops.wm.open_mainfile(filepath=original);s=bpy.context.scene;s.frame_set(1)
assert after==fingerprint(),'Geometry, camera transforms, or lamps changed'
with open(os.path.join(out,'verified-motion.json'),'w') as f:json.dump({'geometryAndLampsUnchanged':True,'groups':checks},f,indent=2)
print('V131_MOTION_AUDIT_PASS',len(checks),flush=True)
