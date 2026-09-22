# -*- coding: utf-8 -*-
"""
cathode_lib.py
==============
Shared constants + material/scene helpers for the "cathode" art system.

Reverse-engineered from the threeui.com cathode page (procedural HTML/Three.js,
no binary models). Full derivation:
  Blender-Asset-Research/references/threeui-cathode/ART_SYSTEM_SPEC.md

Core ideas
----------
* World units = pixels of a 1080x1080 master frame. Floor y = 0, up = +Y.
* Geometry authored in "model space", mirrored into world space:
      W(x, y, z) = (z + MIRROR_K, y, x - MIRROR_K)
* Every surface is an UNLIT emission shader. Flat 3-value face shading:
      top / +X(world) faces -> #1b1b1b
      +Z(world) faces       -> #121212   (matLight set)
      matDark set           -> #121212 everywhere
* Ink lines: thin world-space quads, flat #3a3a3a, nudged 0.55 toward the
  iso camera along (1,1,1).
* Glow: white emission planes, blend ADD, radial falloff (1-d)^2.6.

Engine-agnostic (Emission nodes only). Target Blender 5.x / EEVEE Next,
view transform "Standard", no lights required.
"""

import math
import bpy
from mathutils import Vector

# ---------------------------------------------------------------------------
# constants (exact, from cathode-cinema.html)
# ---------------------------------------------------------------------------
MIRROR_K = 515.5

C_TOP    = (0x1b, 0x1b, 0x1b)   # 27 - faces pointing up
C_FRONT  = (0x1b, 0x1b, 0x1b)   # 27 - faces pointing +Z (model space)
C_SIDE   = (0x12, 0x12, 0x12)   # 18 - faces pointing +X (model space)
C_DARK   = (0x12, 0x12, 0x12)   # 18 - base/plinth material
C_LINE   = (0x3a, 0x3a, 0x3a)   # 58 - drawn edges
C_GRID   = (0x12, 0x12, 0x12)   # 18 - floor grid
C_MARK   = (0x24, 0x24, 0x24)   # 36 - intersection X-marks
C_DIM    = (0x1e, 0x1e, 0x1e)   # 30 - dim line set
C_BG     = (0x0a, 0x0a, 0x0a)   # 10 - page background

LINE_W   = 0.87    # world width of ink line quads (~1 device px at 1080p)
LINE_EPS = 0.55    # nudge toward camera along (1,1,1), per axis

ART = {"x0": 254, "x1": 777, "y0": 214, "y1": 676}
ART_W  = ART["x1"] - ART["x0"]   # 523
ART_H  = ART["y1"] - ART["y0"]   # 462
ART_CX = (ART["x0"] + ART["x1"]) / 2
ART_CY = (ART["y0"] + ART["y1"]) / 2

BASE_THETA = math.pi / 4
BASE_PHI   = math.acos(1.0 / math.sqrt(3.0))
CAM_DIST   = 4200.0
TARGET = Vector((
    ((ART_CY + 1.1547 * 90) / 0.5774 + ART_CX) / 2,   # 733.09
    90,
    ((ART_CY + 1.1547 * 90) / 0.5774 - ART_CX) / 2,   # 217.59
))

# haze fade (post-mirror world space)
HAZE_A = -0.007604   # x
HAZE_B = -0.008591   # y
HAZE_C =  0.016196   # z
HAZE_D = -1.3898
HAZE_LO, HAZE_HI = 0.0666, 0.0902   # raw linear 17 -> 23


# ---------------------------------------------------------------------------
# transforms
# ---------------------------------------------------------------------------
def W(p):
    """model space -> world space (the mirror)."""
    x, y, z = p
    return Vector((z + MIRROR_K, y, x - MIRROR_K))


def WN(n):
    """model normal -> world normal."""
    x, y, z = n
    return Vector((z, y, x))


def iso_camera_position():
    d = CAM_DIST / math.sqrt(3.0)
    return TARGET + Vector((d, d, d))


def iso_frustum(aspect):
    left, right, top, bottom = None, None, None, None
    viewH = max(ART_H * 1.46, ART_W * 1.10 / aspect)
    hh = 0.35355 * viewH
    hw = hh * aspect
    biasY = 0.055 if aspect >= 1.0 else 0.0
    biasX = min(0.24, abs(aspect - 1.0) * 0.34)
    left   = -hw * (1.0 - biasX)
    right  =  hw * (1.0 + biasX)
    bottom = -hh * (1.0 + biasY)
    top    =  hh * (1.0 - biasY)
    return left, right, top, bottom


def face_class(wnormal):
    """
    Dominant-axis face class on the MIRRORED (world) normal.
    1 (dark #121212) only when the face points toward +Z world (i.e. it was
    +X model in the source: C_SIDE). Everything else is bright #1b1b1b
    (top faces and +X world / +Z model faces both map to #1b1b1b).
    """
    nx, ny, nz = wnormal.x, wnormal.y, wnormal.z
    ax, ay, az = abs(nx), abs(ny), abs(nz)
    if az >= ax and az >= ay and nz > 0.0:
        return 1
    return 0


# ---------------------------------------------------------------------------
# materials
# ---------------------------------------------------------------------------
def _new_mat(name):
    old = bpy.data.materials.get(name)
    if old:
        old.user_clear()
        bpy.data.materials.remove(old)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    return mat


def _emission(mat, rgb, strength=1.0):
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (
        rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0, 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def get_materials():
    """Core cathode flat materials: bright, dark, line, grid, mark, dim."""
    m = {}
    m["bright"] = _emission(_new_mat("CATH_BRIGHT"), (0x1b, 0x1b, 0x1b))
    m["dark"]   = _emission(_new_mat("CATH_DARK"),   (0x12, 0x12, 0x12))
    m["line"]   = _emission(_new_mat("CATH_LINE"),   C_LINE)
    m["grid"]   = _emission(_new_mat("CATH_GRID"),   C_GRID)
    m["mark"]   = _emission(_new_mat("CATH_MARK"),   C_MARK)
    m["dim"]    = _emission(_new_mat("CATH_DIM"),    C_DIM)
    return m


def haze_material(side_mul=0.8, name="CATH_HAZE"):
    """
    Depth-fade haze (panel light case, stand, film cans).
    f = clamp(HAZE_A*x + HAZE_B*y + HAZE_C*z + HAZE_D, 0, 1)   (world space)
    v = mix(0.0666, 0.0902, f); non-top faces *= side_mul.
    """
    # Haze is shared by many objects. Rebuilding/removing the datablock on
    # every call invalidates material slots already assigned to earlier
    # meshes, so reuse the configured material once it exists.
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    mat = _new_mat(name)
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 1.0

    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep_n = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sep_n.inputs["Vector"])

    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = (HAZE_A, HAZE_B, HAZE_C)
    nt.links.new(geo.outputs["Position"], dot.inputs[0])
    sub = nt.nodes.new("ShaderNodeMath")
    sub.operation = "ADD"
    sub.inputs[1].default_value = HAZE_D
    nt.links.new(dot.outputs["Value"], sub.inputs[0])
    clampn = nt.nodes.new("ShaderNodeClamp")
    nt.links.new(sub.outputs["Value"], clampn.inputs["Value"])

    mixv = nt.nodes.new("ShaderNodeMix")
    mixv.data_type = "FLOAT"
    mixv.inputs[2].default_value = HAZE_LO   # A
    mixv.inputs[3].default_value = HAZE_HI   # B
    nt.links.new(clampn.outputs["Result"], mixv.inputs[0])  # Factor

    axn = nt.nodes.new("ShaderNodeMath"); axn.operation = "ABSOLUTE"
    ayn = nt.nodes.new("ShaderNodeMath"); ayn.operation = "ABSOLUTE"
    azn = nt.nodes.new("ShaderNodeMath"); azn.operation = "ABSOLUTE"
    nt.links.new(sep_n.outputs["X"], axn.inputs[0])
    nt.links.new(sep_n.outputs["Y"], ayn.inputs[0])
    nt.links.new(sep_n.outputs["Z"], azn.inputs[0])
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
    nt.links.new(axn.outputs["Value"], mx.inputs[0])
    nt.links.new(azn.outputs["Value"], mx.inputs[1])
    less = nt.nodes.new("ShaderNodeMath"); less.operation = "LESS_THAN"
    nt.links.new(ayn.outputs["Value"], less.inputs[0])
    nt.links.new(mx.outputs["Value"], less.inputs[1])
    mult = nt.nodes.new("ShaderNodeMath"); mult.operation = "MULTIPLY_ADD"
    mult.inputs[1].default_value = side_mul - 1.0
    mult.inputs[2].default_value = 1.0
    nt.links.new(less.outputs["Value"], mult.inputs[0])

    fin = nt.nodes.new("ShaderNodeMath"); fin.operation = "MULTIPLY"
    nt.links.new(mixv.outputs[2], fin.inputs[0])    # mixv float result
    nt.links.new(mult.outputs["Value"], fin.inputs[1])

    rgb = nt.nodes.new("ShaderNodeCombineColor")
    for i in range(3):
        nt.links.new(fin.outputs["Value"], rgb.inputs[i])
    nt.links.new(rgb.outputs["Color"], em.inputs["Color"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat


def glow_material(peak, name, radial=False):
    """
    White glow with (1-d)^2.6 spherical falloff (radial=True) or flat.
    peak ~ their glowPeak/capPeak (0.055 .. 0.88). EEVEE has no true additive
    blend, so this uses BLENDED surface method with emission alpha; on the
    near-black background it reads as additive.
    """
    mat = _new_mat(name)
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    val = None
    if radial:
        ramp = nt.nodes.new("ShaderNodeTexGradient")
        ramp.gradient_type = "SPHERICAL"
        uv = nt.nodes.new("ShaderNodeUVMap")
        uv.uv_map = "UVMap"
        nt.links.new(uv.outputs["UV"], ramp.inputs["Vector"])
        pw = nt.nodes.new("ShaderNodeMath")
        pw.operation = "POWER"
        pw.inputs[1].default_value = 2.6
        nt.links.new(ramp.outputs["Fac"], pw.inputs[0])
        val = pw
    sc = nt.nodes.new("ShaderNodeMath")
    sc.operation = "MULTIPLY"
    sc.inputs[1].default_value = peak
    if val is not None:
        nt.links.new(val.outputs["Value"], sc.inputs[0])
    else:
        sc.inputs[0].default_value = 1.0
    nt.links.new(sc.outputs["Value"], em.inputs["Strength"])
    try:
        nt.links.new(sc.outputs["Value"], em.inputs["Alpha"])
    except (IndexError, KeyError):
        pass
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    try:  # EEVEE Next (4.2+/5.x)
        mat.surface_render_method = "BLENDED"
    except (TypeError, AttributeError, ValueError):
        try:  # legacy EEVEE
            mat.blend_method = "BLEND"
        except (TypeError, AttributeError):
            pass
    mat.use_backface_culling = False
    return mat


def flat_grayscale_material(hex255, name, strength=1.0):
    """Generic flat emission, e.g. for restyled props. hex255 = (r,g,b)."""
    return _emission(_new_mat(name), hex255, strength)
