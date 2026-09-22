# -*- coding: utf-8 -*-
"""
cathode_scene.py
================
Scene-level assembly for cathode renders: iso ortho camera, graded
background plate, film grain, render settings, save/report helpers.
"""

import math
import struct
import zlib

import bpy
from mathutils import Vector

import cathode_lib as CL
import cathode_feed as CF

ASPECT = 16.0 / 9.0


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    if bpy.context.selected_objects:
        bpy.ops.object.delete()
    for block_list in (bpy.data.meshes, bpy.data.materials, bpy.data.images,
                       bpy.data.cameras):
        for b in list(block_list):
            if b.users == 0:
                block_list.remove(b)


def get_collection(name="CATH"):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll


def make_camera(scene):
    cam_data = bpy.data.cameras.new("CATH_CAM")
    cam_data.type = "ORTHO"
    # The source scene uses pixel-like world units and places the camera about
    # 4,200 units from the target. Blender's default 1,000-unit far clip would
    # silently discard every rig mesh.
    cam_data.clip_start = 0.1
    cam_data.clip_end = 10000.0
    left, right, top, bottom = CL.iso_frustum(ASPECT)
    cam_data.ortho_scale = right - left
    # frustum bias: shift the whole frustum
    cam_data.shift_x = (right + left) / (2.0 * (right - left))
    cam_data.shift_y = (top + bottom) / (2.0 * (top - bottom))
    cam = bpy.data.objects.new("CATH_CAM", cam_data)
    scene.collection.objects.link(cam)
    cam.location = CL.iso_camera_position()
    d = Vector((1.0, 1.0, 1.0)).normalized()
    cam.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    scene.camera = cam
    return cam, (left, right, top, bottom)


def render_setup(scene, width=1920, height=1080):
    s = scene.render
    s.resolution_x = width
    s.resolution_y = height
    s.resolution_percentage = 100
    s.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    s.image_settings.file_format = "PNG"
    s.image_settings.color_mode = "RGB"
    if hasattr(s, "engine"):
        try:
            s.engine = "BLENDER_EEVEE_NEXT"
        except (TypeError, ValueError):
            try:
                s.engine = "BLENDER_EEVEE"
            except (TypeError, ValueError):
                pass


# ---------------------------------------------------------------------------
# background plate
# ---------------------------------------------------------------------------
def background_material(scene, aspect=ASPECT):
    """
    Radial ground: v = mix(0.0664, 0.0225, smoothstep(0.04, 0.92, r)),
    q = uv - (0.5, 0.56), q.x *= aspect.  Generated 1024x576 Non-Color.
    """
    W, H = 1024, 576
    px = bytearray(W * H * 4)
    for y in range(H):
        uv_y = 1.0 - y / H
        for x in range(W):
            uv_x = x / W
            qx = (uv_x - 0.5) * aspect
            qy = uv_y - 0.56
            r = math.hypot(qx, qy)
            t = max(0.0, min(1.0, (r - 0.04) / (0.92 - 0.04)))
            t = t * t * (3.0 - 2.0 * t)
            v = 0.0664 + (0.0225 - 0.0664) * t
            c = int(max(0.0, min(1.0, v)) * 255.0)
            i = (y * W + x) * 4
            px[i] = px[i + 1] = px[i + 2] = c
            # Alpha carries the low-amplitude noise so this front-facing quad
            # behaves like the source's additive post pass instead of an
            # opaque black rectangle.
            px[i + 3] = c
    img = bpy.data.images.new("CATH_BG", W, H, alpha=True, float_buffer=False)
    img.pixels = [v / 255.0 for v in px]
    img.colorspace_settings.name = "Non-Color"
    mat = bpy.data.materials.new("CATH_BG_MAT")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


# ---------------------------------------------------------------------------
# film grain
# ---------------------------------------------------------------------------
def grain_image(scene, w=960, h=540, t=0.0, amp=0.056):
    """
    Two-octave hash noise (source fxScene), pow 2.3, amplitude 0.056,
    plus the faint interference band. Static frame at time t (24fps
    quantized when animating).
    """
    px = bytearray(w * h * 4)
    band_phase = 0.7 * t
    for y in range(h):
        fy = (h - 1 - y) * (1080.0 / h)
        band = 0.0035 * max(0.0, math.sin(fy * 0.0035 - band_phase)) ** 8
        for x in range(w):
            fx = x * (1920.0 / w)
            tx, ty = 37.0, 61.0
            a = (fx + tx) % 917.0
            b = (fy + ty) % 917.0
            n1 = _hash2(a, b)
            a2 = (fx * 0.5 + 11.0) % 613.0
            b2 = (fy * 0.5 + 7.0) % 613.0
            n2 = _hash2(a2, b2)
            n = n1 * 0.72 + n2 * 0.28
            v = n ** 2.3 * amp + band
            c = int(max(0.0, min(1.0, v)) * 255.0)
            i = (y * w + x) * 4
            px[i] = px[i + 1] = px[i + 2] = c
            px[i + 3] = 255
    img = bpy.data.images.new("CATH_GRAIN", w, h, alpha=True, float_buffer=False)
    img.pixels = [v / 255.0 for v in px]
    img.colorspace_settings.name = "Non-Color"
    return img


def _hash2(x, y):
    q = [(x * 0.1031) % 1.0, (y * 0.1031) % 1.0, (x * 0.1031) % 1.0]
    d = (q[0] * q[1] + q[1] * q[2] + q[2] * q[0]) + 33.33
    q = [(q[i] + d) % 1.0 for i in range(3)]
    return ((q[0] + q[1]) * q[2]) % 1.0


def grain_material(scene, img):
    mat = bpy.data.materials.new("CATH_GRAIN_MAT")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    transparent = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tex.outputs["Alpha"], mix.inputs[0])
    nt.links.new(transparent.outputs[0], mix.inputs[1])
    nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    try:
        mat.surface_render_method = "BLENDED"
    except (TypeError, AttributeError, ValueError):
        try:
            mat.blend_method = "BLEND"
        except (TypeError, AttributeError):
            pass
    mat.use_backface_culling = False
    return mat


# ---------------------------------------------------------------------------
# monitor feed plane
# ---------------------------------------------------------------------------
def feed_plane(scene, builder_coll, aspect=ASPECT):
    """512x288 emission quad on the monitor screen (model space)."""
    img = CF.feed_image(512, 288, t=0.75)
    mat = bpy.data.materials.new("CATH_FEED_MAT")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    x = 790.05
    y0, y1 = 136.0, 169.0
    z0, z1 = 186.0, 244.0
    from cathode_geo import Builder
    prof = [(-z1, y0), (-z0, y0), (-z0, y1), (-z1, y1)]
    p0 = [Builder.map_profile(a, b, x, "x") for a, b in prof]
    me = bpy.data.meshes.new("CATH_FEED")
    me.from_pydata([tuple(CL.W(p)) for p in p0], [], [(0, 1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new("CATH_FEED", me)
    builder_coll.objects.link(ob)
    # verts: (y0,z1) BR, (y0,z0) BL, (y1,z0) TL, (y1,z1) TR
    uv = me.uv_layers.new(name="UVMap")
    for li, (u, v) in enumerate([(1, 0), (0, 0), (0, 1), (1, 1)]):
        uv.data[li].uv = (u, v)
    ob.data.materials.append(mat)
    return ob, img


# ---------------------------------------------------------------------------
# save / report
# ---------------------------------------------------------------------------
def save_blend(path):
    bpy.ops.wm.save_as_mainfile(filepath=path)


def report(path, **kw):
    import json
    with open(path, "w", encoding="utf-8") as f:
        json.dump(kw, f, indent=2, default=str)
    return path
