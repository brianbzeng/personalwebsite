# -*- coding: utf-8 -*-
"""
cathode_emit.py
===============
Emitters (lit caps + camera-space glow overlays) and the line-quad
emitter for the cathode art system.

Glow planes are parented to the ortho camera and pushed along its local
-Z axis: under orthographic projection that leaves their screen position
exactly unchanged while putting them in front of all geometry, which is
how the source (depthTest:false, renderOrder 4) behaves.
"""

import math
import bpy
from mathutils import Vector

import cathode_lib as CL

GLOW_CAM_Z = -400.0    # camera-local depth, in front of every prop
GRAIN_CAM_Z = -401.0


def _sxy_delta(d):
    """screen-space (right, canvas-down) of a world delta vector."""
    return (d.z - d.x, 0.5774 * (d.x + d.z) - 1.1547 * d.y)


def perp_world(screen_u, screen_v):
    """small world vector with the given screen-space perpendicular."""
    w = Vector((screen_u / 2.0, -screen_v / 1.1547, -screen_u / 2.0))
    return w


def line_quad(a, b, width=CL.LINE_W):
    """
    Model-space segment (a, b) -> 4 world-space quad verts.
    Nudged LINE_EPS toward the camera along (1,1,1) to sit on top of
    the surfaces it outlines.
    """
    a, b = CL.W(Vector(a)), CL.W(Vector(b))
    d = b - a
    su, sv = _sxy_delta(d)
    sl = math.hypot(su, sv)
    if sl < 1e-9:
        return None
    pu, pv = -sv / sl, su / sl
    off = perp_world(pu, pv)
    if off.length > 1e-12:
        off *= (width / 2.0) / off.length
    eps = Vector((CL.LINE_EPS, CL.LINE_EPS, CL.LINE_EPS))
    a2, b2 = a + eps, b + eps
    return [a2 - off, a2 + off, b2 + off, b2 - off]


def emit_lines(builder, mats):
    """Flatten builder.line_segs into one mesh per line set."""
    made = []
    for key, segs in builder.line_segs.items():
        if not segs:
            continue
        verts, faces = [], []
        for (a, b) in segs:
            q = line_quad(a, b)
            if q is None:
                continue
            base = len(verts)
            verts.extend(q)
            faces.append([base, base + 1, base + 2, base + 3])
        if not verts:
            continue
        me = bpy.data.meshes.new("CATH_LINE_" + key.upper())
        me.from_pydata(verts, [], faces)
        me.update()
        ob = bpy.data.objects.new("CATH_LINE_" + key.upper(), me)
        builder.coll.objects.link(ob)
        ob.data.materials.append(mats[key])
        builder.objects.append(ob)
        made.append(ob.name)
    return made


def emitter_cap(builder, mats, name, pos, axis, w, d, cap_peak):
    """
    Lit diffuser cap. pos/axis/w/d are MODEL space (axis 'x'|'y'|'z').
    Emission strength == their capPeak (white basic material * opacity).
    """
    if cap_peak <= 0.0001:
        return None
    t = pos[{"x": 0, "y": 1, "z": 2}[axis]]
    off = 0.06 if axis != "y" else 0.05
    t += off
    prof = [(-w / 2.0, -d / 2.0), (w / 2.0, -d / 2.0),
            (w / 2.0, d / 2.0), (-w / 2.0, d / 2.0)]
    p0 = [builder.map_profile(a, b, t, axis) for a, b in prof]
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(CL.W(p)) for p in p0], [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new(name, me)
    builder.coll.objects.link(ob)
    ob.data.materials.append(
        CL.flat_grayscale_material((255, 255, 255), name.upper() + "_MAT",
                                   cap_peak))
    builder.objects.append(ob)
    builder.stats["emitters"] += 1
    return ob


def glow_overlay(builder, mats, cam, name, world_center, g, peak,
                 cam_z=GLOW_CAM_Z):
    """
    Screen-aligned glow quad parented to the camera, centered on the lamp's
    screen position, sized g = max(w,d)*spread (world units).
    """
    if peak <= 0.0001:
        return None
    pc = cam.matrix_world.inverted() @ Vector(world_center)
    me = bpy.data.meshes.new(name)
    h = g / 2.0
    me.from_pydata([(-h, -h, cam_z), (h, -h, cam_z),
                    (h, h, cam_z), (-h, h, cam_z)],
                   [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new(name, me)
    builder.coll.objects.link(ob)
    ob.parent = cam
    ob.location = (pc.x, pc.y, 0.0)
    uv = me.uv_layers.new(name="UVMap")
    for li, (u, v) in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[li].uv = (u, v)
    ob.data.materials.append(CL.glow_material(peak, name.upper() + "_MAT",
                                              radial=True))
    builder.objects.append(ob)
    return ob


def full_frame(cam, name, hw, hh, cam_z, image=None, mat=None):
    """Camera-local full-frame plane (for background / grain)."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-hw, -hh, cam_z), (hw, -hh, cam_z),
                    (hw, hh, cam_z), (-hw, hh, cam_z)],
                   [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new(name, me)
    # users_collection is a read-only collection of owners, not a link API.
    # Link into the camera's first owning collection so the camera-local plane
    # survives save/export just like the source scene's post-process quads.
    if cam.users_collection:
        cam.users_collection[0].objects.link(ob)
    else:
        bpy.context.scene.collection.objects.link(ob)
    ob.parent = cam
    uv = me.uv_layers.new(name="UVMap")
    for li, (u, v) in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[li].uv = (u, v)
    if mat is not None:
        ob.data.materials.append(mat)
    return ob
