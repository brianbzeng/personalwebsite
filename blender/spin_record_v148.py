"""Delay platter rotation by exactly half a second; preserve the flight and arm."""
import bpy, os, math, json
from mathutils import Quaternion

assert bpy.data.filepath.endswith('v147-personal-polaroids.blend')
target=bpy.data.filepath.replace('v147-personal-polaroids','v148-delayed-record-spin')
assert not os.path.exists(target)
s=bpy.context.scene
rig=bpy.data.objects['V138_Playback_Record_Rig']
s.frame_set(88)
landed=rig.rotation_quaternion.copy()
position=rig.location.copy()
for frame in range(88,145):
    rig.rotation_quaternion=Quaternion((0,0,1),-max(0,frame-100)/24*math.tau*(100/3)/60) @ landed
    rig.keyframe_insert('rotation_quaternion',frame=frame)
rig['spin_start_frame']=100
rig['spin_rpm']=100/3
rig['spin_direction']=-1
# A discreet mark on the otherwise rotationally symmetric label makes the
# existing record's rotation legible without changing its grayscale theme.
mesh=bpy.data.meshes.new('V148_LabelMark')
mesh.from_pydata([(.014,-.00065,.00162),(.024,-.00065,.00162),(.024,.00065,.00162),(.014,.00065,.00162)],[],[(0,1,2,3)])
mark=bpy.data.objects.new('V148_LabelMark',mesh)
rig.users_collection[0].objects.link(mark);mark.parent=rig
mesh.materials.append(bpy.data.objects['V138_Playback_Record'].data.materials[0])
for frame in range(88,145):
    s.frame_set(frame)
    assert (rig.location-position).length<1e-7
    if frame<=100: assert rig.rotation_quaternion.rotation_difference(landed).angle<1e-6
s.timeline_markers.new('RECORD_SPIN_AFTER_HALF_SECOND',frame=100)
s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=target)
out=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'blender/outputs/review-v148')
os.makedirs(out,exist_ok=True)
with open(os.path.join(out,'spin-audit.json'),'w') as f: json.dump({'landedFrame':88,'spinStartFrame':100,'fps':24,'delaySeconds':.5,'rpm':100/3,'clockwiseFromAbove':True,'landedPositionPreserved':True},f,indent=2)
