"""Read-only scene inventory for the v110 lighting pass."""

from pathlib import Path
import json
import bpy


def bounds(ob):
    if not hasattr(ob, "bound_box"):
        return None
    pts = [ob.matrix_world @ __import__("mathutils").Vector(corner) for corner in ob.bound_box]
    return {
        "min": [round(min(p[i] for p in pts), 5) for i in range(3)],
        "max": [round(max(p[i] for p in pts), 5) for i in range(3)],
    }


keywords = (
    "window", "blind", "cord", "pull", "monitor", "screen", "mouse", "pad",
    "desk", "lamp", "rain", "grass", "outside", "exterior", "moon", "light",
)

records = []
for ob in bpy.data.objects:
    lower = ob.name.lower()
    if any(word in lower for word in keywords) or ob.type == "LIGHT":
        item = {
            "name": ob.name,
            "type": ob.type,
            "location": [round(v, 5) for v in ob.location],
            "rotation": [round(v, 5) for v in ob.rotation_euler],
            "scale": [round(v, 5) for v in ob.scale],
            "bounds": bounds(ob),
            "collections": [c.name for c in ob.users_collection],
            "hide_render": ob.hide_render,
        }
        if ob.type == "LIGHT":
            item["light"] = {
                "kind": ob.data.type,
                "energy": ob.data.energy,
                "color": list(ob.data.color),
                "shape": getattr(ob.data, "shape", None),
                "size": getattr(ob.data, "size", None),
                "size_y": getattr(ob.data, "size_y", None),
            }
        if ob.type == "MESH":
            item["materials"] = [m.name if m else None for m in ob.data.materials]
        records.append(item)

report = {
    "file": bpy.data.filepath,
    "scene": bpy.context.scene.name,
    "render_engine": bpy.context.scene.render.engine,
    "world": bpy.context.scene.world.name if bpy.context.scene.world else None,
    "objects": records,
    "collections": [c.name for c in bpy.data.collections],
}

out = Path(__file__).with_name("inspect_v110_scene.json")
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
