"""
GLM exterior build — script 01: clean working copy + collection scaffold + curved glass tower block-in.

RUN (on your Windows machine, with v128 closed in any other Blender instance):
    D:\\Blender5.2\\blender.exe "C:/Users/Brian Zeng/Documents/Blender-Asset-Research/personalwebsite/blender/outputs/blender/lofi-room-cathode-v128-blanket-field.blend" --python "C:/.../glm_exterior_01_blockin.py"

WHAT IT DOES (non-destructive to the room):
  1. Verifies the open file is v128 (aborts otherwise — never operates on the wrong file).
  2. Hides (does NOT delete) the exterior placeholder collection CATHODE_EXTERIOR_SOURCE_FIELD
     from viewport + render. Room is untouched.
  3. Creates a new top collection GLM_EXTERIOR_SOURCE with child collections:
       GLM_EXT_TOWERS, GLM_EXT_SKY
  4. Creates purpose-built exterior materials (Cathode line-work language, emission grayscale).
  5. Blocks in TWO curved (tapered, faceted) glass towers on the left of the window view,
     as dark fill + bright emissive edge/floor lines, outside the window plane (Y > 2.84).
  6. Adds a large dark sky dome so the home render is not a black void (lets us judge silhouettes).
  7. Renders CAM_HOME_Perspective to outputs/blender/glm-exterior-renders/v01/home.png
  8. Saves as a NEW file: lofi-room-cathode-glm-exterior-source-v01.blend  (never overwrites v128)
  9. Writes a JSON report: outputs/blender/glm-exterior-renders/v01/report.json

All tower placement values are PARAMETERS at the top — easy to tune in the next iteration
once you send back the home render. This is a block-in, not a final composition.
"""

import bpy
import bmesh
import json
import math
import os
from mathutils import Vector

SCRIPT_VERSION = "v4"
print(f"\n[GLM-EXT-01] SCRIPT VERSION {SCRIPT_VERSION}  <-- if this is not v3, your local copy is STALE; re-copy from the workspace file view.\n")

# ----------------------------------------------------------------------------
# PATHS  (edit the blender root here if your layout differs)
# ----------------------------------------------------------------------------
BLENDER_DIR = "C:/Users/Brian Zeng/Documents/Blender-Asset-Research/personalwebsite/blender"
OUTPUTS     = BLENDER_DIR + "/outputs/blender"
SRC_NAME    = "lofi-room-cathode-v128-blanket-field.blend"
DST         = OUTPUTS + "/lofi-room-cathode-glm-exterior-source-v01.blend"
RENDER_DIR  = OUTPUTS + "/glm-exterior-renders/v02"

PLACEHOLDER_COLLECTION = "CATHODE_EXTERIOR_SOURCE_FIELD"
ROOT_COLLECTION         = "GLM_EXTERIOR_SOURCE"
HOME_CAMERA             = "CAM_HOME_Perspective"

# ----------------------------------------------------------------------------
# TOWER BLOCK-IN PARAMETERS  (tune after first render)
#   Windows are at X = -1.4 and X = +1.4, glass at Y = 2.715, exterior is Y > 2.84.
#   In the inspiration photo the curved glass towers sit on the LEFT of the frame,
#   so we place them at negative X, beyond the left window.
# ----------------------------------------------------------------------------
TOWERS = [
    # (name, x, y, base_z, radius_base, radius_top, height, facets, fill_mat, line_mat)
    # Home camera is at X=-9.8 looking toward +X/+Y, so the visible exterior through the
    # windows opens toward +X. Towers spread across the +X side of the window wall.
    ("GLM_TOWER_A",  1.6,  6.5, 0.0, 1.00, 0.72, 11.0, 14, "GLM_EXT_FILL_DARK", "GLM_EXT_LINE"),
    ("GLM_TOWER_B",  3.6,  9.0, 0.0, 1.25, 0.95,  8.5, 14, "GLM_EXT_FILL_MID",  "GLM_EXT_LINE"),
    ("GLM_TOWER_C", -0.6,  8.5, 0.0, 0.85, 0.62,  9.5, 14, "GLM_EXT_FILL_MID",  "GLM_EXT_LINE"),
]
TOWER_FLOOR_LINES = 16   # horizontal loop cuts -> floor-line count
TOWER_LINE_THICK  = 0.035  # wireframe thickness for edge lines (meters)

# Exterior ground plane (the home camera looks DOWN through the windows, so it sees ground)
GROUND_SIZE = 80.0
GROUND_Z   = 0.0

# Sky dome
SKY_RADIUS = 120.0

# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def log(msg):
    print(f"[GLM-EXT-01] {msg}")

def abort(msg):
    log("ABORT: " + msg)
    raise SystemExit(1)

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def get_collection(name):
    return bpy.data.collections.get(name)

def hide_collection_recursive(coll, viewport=True, render=True):
    """Hide a collection and all descendants from viewport/render. Non-destructive."""
    coll.hide_viewport = viewport
    # Collections do not all carry hide_render across versions; also hide member objects.
    for obj in coll.objects:
        if viewport: obj.hide_set(True)
        if render:   obj.hide_render = True
    for child in coll.children:
        hide_collection_recursive(child, viewport, render)

def new_collection(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent if parent else bpy.context.scene.collection).children.link(c)
    return c

def link_to(coll, obj):
    # ensure object only linked to the target collection
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)

def make_emission_material(name, color, strength):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (color[0], color[1], color[2], 1.0)
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    out.location = (300, 0); em.location = (0, 0)
    mat.blend_method = "BLEND"
    return mat

# ----------------------------------------------------------------------------
# 1. VERIFY SOURCE FILE
# ----------------------------------------------------------------------------
current = os.path.basename(bpy.data.filepath)
if current != SRC_NAME:
    abort(f"Open file is '{current}', expected '{SRC_NAME}'. "
          f"Run: blender.exe <path-to-v128> --python this_script.py")
log(f"Operating on verified source: {current}")

# ----------------------------------------------------------------------------
# 2. HIDE PLACEHOLDER EXTERIOR FIELD (room untouched)
# ----------------------------------------------------------------------------
ph = get_collection(PLACEHOLDER_COLLECTION)
if ph:
    hide_collection_recursive(ph, viewport=True, render=True)
    log(f"Hid placeholder collection '{PLACEHOLDER_COLLECTION}' (not deleted).")
else:
    log(f"Placeholder collection '{PLACEHOLDER_COLLECTION}' not found — skipping.")

# ----------------------------------------------------------------------------
# 3. COLLECTION SCAFFOLD  (clear any prior GLM_EXTERIOR_SOURCE for clean re-runs)
# ----------------------------------------------------------------------------
existing = get_collection(ROOT_COLLECTION)
if existing:
    for obj in list(existing.all_objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(existing)
root = new_collection(ROOT_COLLECTION)
coll_towers = new_collection("GLM_EXT_TOWERS", parent=root)
coll_sky    = new_collection("GLM_EXT_SKY",    parent=root)
coll_ground = new_collection("GLM_EXT_GROUND", parent=root)
log("Created collection scaffold: GLM_EXTERIOR_SOURCE > {GLM_EXT_TOWERS, GLM_EXT_SKY, GLM_EXT_GROUND}")

# ----------------------------------------------------------------------------
# 4. MATERIALS  (Cathode line-work language, emission grayscale)
# ----------------------------------------------------------------------------
mats = {}
mats["GLM_EXT_FILL_DARK"] = make_emission_material("GLM_EXT_FILL_DARK", (0.039, 0.039, 0.039), 1.0)
mats["GLM_EXT_FILL_MID"]  = make_emission_material("GLM_EXT_FILL_MID",  (0.105, 0.105, 0.105), 1.0)
mats["GLM_EXT_LINE"]      = make_emission_material("GLM_EXT_LINE",      (0.86,  0.86,  0.86),  0.65)
mats["GLM_EXT_SKY"]       = make_emission_material("GLM_EXT_SKY",       (0.02,  0.025, 0.035), 0.6)
mats["GLM_EXT_GROUND"]    = make_emission_material("GLM_EXT_GROUND",    (0.05,  0.05,  0.05), 0.7)
log("Created exterior materials: FILL_DARK, FILL_MID, LINE, SKY")

# ----------------------------------------------------------------------------
# 5. CURVED GLASS TOWERS  (dark fill mesh + bright emissive edge/floor-line mesh)
# ----------------------------------------------------------------------------
def build_tower(name, x, y, base_z, r_base, r_top, height, facets, fill_mat, line_mat, floor_lines):
    # --- fill mesh: tapered faceted cylinder ---
    bpy.ops.mesh.primitive_cylinder_add(vertices=facets, radius=r_base, depth=height,
                                         location=(x, y, base_z + height / 2.0))
    fill = bpy.context.active_object
    fill.name = name + "_Fill"
    # taper top
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(fill.data)
    bm.verts.ensure_lookup_table()
    z_top = max(v.co.z for v in bm.verts)
    scale = r_top / r_base
    for v in bm.verts:
        if abs(v.co.z - z_top) < 1e-4:
            v.co.x *= scale
            v.co.y *= scale
    # add horizontal loop cuts for floor lines
    if floor_lines > 0:
        bpy.ops.mesh.select_all(action="DESELECT")
        for v in bm.verts:
            v.select = False
        bmesh.update_edit_mesh(fill.data)
        # use subdivide on horizontal edges via edge loops: simpler -> loop cut with cuts
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.subdivide(number_cuts=floor_lines)
    bmesh.update_edit_mesh(fill.data)
    bpy.ops.object.mode_set(mode="OBJECT")
    fill.data.materials.append(mats[fill_mat])

    # --- line mesh: duplicate + wireframe modifier, emissive white ---
    line = fill.copy()
    line.data = fill.data.copy()
    line.name = name + "_Lines"
    line.data.materials.clear()
    line.data.materials.append(mats[line_mat])
    wf = line.modifiers.new("Wireframe", "WIREFRAME")
    wf.thickness = TOWER_LINE_THICK
    wf.use_even_offset = True
    if hasattr(wf, "use_replace"):
        wf.use_replace = True
    elif hasattr(wf, "replace"):
        wf.replace = True
    link_to(coll_towers, fill)
    link_to(coll_towers, line)
    return fill, line

created = []
for t in TOWERS:
    f, l = build_tower(*t, floor_lines=TOWER_FLOOR_LINES)
    created.append((f.name, l.name, tuple(f.location), tuple(f.dimensions)))
log(f"Built {len(created)} towers: {created}")

# ----------------------------------------------------------------------------
# 6. SKY DOME  (large dark sphere, inward-facing, so renders aren't a black void)
# ----------------------------------------------------------------------------
bpy.ops.mesh.primitive_uv_sphere_add(radius=SKY_RADIUS, location=(0, 6, 0), segments=32, ring_count=16)
sky = bpy.context.active_object
sky.name = "GLM_SKY_Dome"
# flip normals so we see inside
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.flip_normals()
bpy.ops.object.mode_set(mode="OBJECT")
sky.data.materials.append(mats["GLM_EXT_SKY"])
link_to(coll_sky, sky)
log("Added sky dome.")

# ----------------------------------------------------------------------------
# 6b. EXTERIOR GROUND PLANE  (home camera looks DOWN through the windows)
# ----------------------------------------------------------------------------
bpy.ops.mesh.primitive_plane_add(size=GROUND_SIZE, location=(0, 8, GROUND_Z))
ground = bpy.context.active_object
ground.name = "GLM_Ground"
ground.data.materials.append(mats["GLM_EXT_GROUND"])
link_to(coll_ground, ground)
log("Added exterior ground plane.")

# ----------------------------------------------------------------------------
# 7. RENDER CAM_HOME_PERSPECTIVE
# ----------------------------------------------------------------------------
ensure_dir(RENDER_DIR)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1100
scene.render.resolution_y = 760
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.render.filepath = os.path.join(RENDER_DIR, "home.png")
cam = bpy.data.objects.get(HOME_CAMERA)
if not cam:
    abort(f"Production camera '{HOME_CAMERA}' not found.")
scene.camera = cam
log(f"Rendering {HOME_CAMERA} -> {scene.render.filepath}")
bpy.ops.render.render(write_still=True)

# ----------------------------------------------------------------------------
# 8. SAVE AS NEW FILE (never overwrite v128)
# ----------------------------------------------------------------------------
ensure_dir(OUTPUTS)
bpy.ops.wm.save_as_mainfile(filepath=DST)
log(f"Saved working copy: {DST}")

# ----------------------------------------------------------------------------
# 9. REPORT
# ----------------------------------------------------------------------------
report = {
    "script": "glm_exterior_01_blockin.py",
    "source_file": SRC_NAME,
    "saved_file": DST,
    "render": scene.render.filepath,
    "placeholder_hidden": PLACEHOLDER_COLLECTION if ph else None,
    "collections": [ROOT_COLLECTION, "GLM_EXT_TOWERS", "GLM_EXT_SKY", "GLM_EXT_GROUND"],
    "materials": list(mats.keys()),
    "towers": [
        {"fill": n[0], "lines": n[1], "location": list(n[2]), "dimensions": list(n[3])}
        for n in created
    ],
    "sky": {"name": sky.name, "radius": SKY_RADIUS},
    "ground": {"name": ground.name, "size": GROUND_SIZE, "z": GROUND_Z},
    "camera_used": HOME_CAMERA,
    "render_resolution": [scene.render.resolution_x, scene.render.resolution_y],
    "room_touched": False,
    "notes": "Block-in only. Tower X/Y/height/radius are parameters at top of script; "
             "tune after reviewing home.png. Bridge, bay, hills come in later scripts.",
}
rp = os.path.join(RENDER_DIR, "report.json")
with open(rp, "w") as fh:
    json.dump(report, fh, indent=2)
log(f"Report written: {rp}")
log("DONE. Send back home.png and report.json for the next iteration.")
