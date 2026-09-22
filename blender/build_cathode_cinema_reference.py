# -*- coding: utf-8 -*-
"""Build the standalone procedural Cathode Cinema reference in Blender 5.x.

Run from this directory with Blender, for example:
    blender -b --python build_cathode_cinema_reference.py
"""

from pathlib import Path
import json
import math
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import bpy
from mathutils import Vector

import cathode_lib as CL
import cathode_geo as CG
import cathode_emit as CE
import cathode_scene as CS


def circle_profile(cx, cy, r, seg=20):
    return [(cx + math.cos(2 * math.pi * i / seg) * r,
             cy + math.sin(2 * math.pi * i / seg) * r) for i in range(seg)]


def add_floor_grid(builder):
    for x in (761, 793.5, 826, 858.5, 891, 923.5, 956, 988.5):
        builder.dashed("grid", x, -1.1, 40, x, -1.1, 430)
    for z in (56, 95, 134, 173, 212, 251, 290, 329, 368, 407):
        builder.dashed("grid", 700, -1.1, z, 1060, -1.1, z)
    builder.dashed("grid", 640, -1.1, 290, 780, -1.1, 290)
    builder.dashed("grid", 620, -1.1, 251, 760, -1.1, 251)
    for x, z in ((891, 173), (891, 212), (891, 251), (891, 329),
                 (923.5, 251), (923.5, 329), (858.5, 290),
                 (956, 212), (826, 329), (793.5, 251), (891, 368),
                 (956, 290)):
        builder.add_line("mark", (x - 3.4, -1.0, z - 3.4),
                         (x + 3.4, -1.0, z + 3.4))
        builder.add_line("mark", (x - 3.4, -1.0, z + 3.4),
                         (x + 3.4, -1.0, z - 3.4))


def build_rig(builder, mats):
    rr = builder.round_rect

    # Panel light and stand.
    builder.prism("CATH_PANEL_CASE", rr(436, 48, 556, 140, 9), 146, 156,
                  "z", "haze_panel")
    builder.add_round_rect_line("dim", 441, 53, 551, 135, 3, 5, "z", 156.08)
    for row in range(5):
        for col in range(7):
            builder.add_round_rect_line("dim", 447 + 15.4 * col,
                                        59 + 14.6 * row,
                                        458 + 15.4 * col,
                                        69 + 14.6 * row, 2, 4, "z", 156.12)
    builder.member("CATH_LIGHT_STAND", (496, 0, 151), (496, 50, 151),
                   6, 5, 4, "haze")
    builder.member("CATH_LIGHT_FOOT_A", (496, 30, 151), (556, 0, 166),
                   4.4, 2.6, 4, "haze", open_a=True)
    builder.member("CATH_LIGHT_FOOT_B", (496, 30, 151), (452, 0, 178),
                   4.4, 2.6, 4, "haze", open_a=True)
    builder.member("CATH_LIGHT_FOOT_C", (496, 30, 151), (480, 0, 116),
                   4.4, 2.6, 4, "haze", open_a=True)

    # Camera tripod, head, body, lens and matte box.
    apex = (700, 118, 202)
    for i, foot in enumerate(((786, 0, 254), (612, 0, 251), (780, 0, 138))):
        builder.member("CATH_TRIPOD_LEG_%d" % i, (700, 112, 202), foot,
                       9.6, 5.4, 4, "light")
        builder.member("CATH_TRIPOD_FOOT_%d" % i, foot,
                       (foot[0], foot[1] + 5, foot[2]), 7.5, 7.5, 12, "dark")
    builder.member("CATH_BOWL", (700, 104, 202), (700, 124, 202),
                   15, 17, 16, "light", rings=(0.55,))
    builder.member("CATH_PAN_BAR", (692, 110, 192), (650, 92, 140),
                   3.6, 4.6, 4, "light")
    builder.prism("CATH_CAMERA_BODY", rr(650, 124, 756, 180, 7), 168, 238,
                  "z", "light")
    builder.add_round_rect_line("line", 662, 133, 744, 171, 5, 5, "z", 238.1)
    builder.add_round_rect_line("line", 654, 128, 752, 176, 6, 5, "z", 167.9)
    for i in range(4):
        builder.add_round_rect_line("line", 664, 206 + i * 9.5,
                                    742, 212 + i * 9.5, 2.4, 4, "y", 180.06)
    for x in (664, 728):
        builder.prism("CATH_HANDLE_POST_%d" % x,
                      rr(x, 186, x + 14, 200, 2.5), 180, 206, "y", "light")
    builder.prism("CATH_HANDLE", rr(658, 182, 748, 204, 5), 206, 215,
                  "y", "light")
    for i in range(6):
        builder.add_circle_line("line", 668 + 14 * i, 215.05, 193, 3.2, 10)

    builder.member("CATH_LENS", (703, 150, 236), (703, 150, 311),
                   27, 23, 20, "light", open_a=True,
                   rings=(0.18, 0.33, 0.47, 0.60))
    builder.member("CATH_LENS_FRONT", (703, 150, 311), (703, 150, 314),
                   22.4, 19, 20, "dark")
    matte_hole = circle_profile(703, 150, 25, 18)
    builder.prism("CATH_MATTE_BOX", rr(662, 110, 744, 190, 6),
                  288, 314, "z", "light", holes=(matte_hole,))
    builder.add_circle_line("line", 703, 314.1, 150, 25, 18)
    builder.prism("CATH_TOP_FLAG", rr(664, 300, 742, 326, 3),
                  190, 195, "y", "light")
    builder.member("CATH_FOLLOW_FOCUS", (728, 150, 266), (744, 150, 266),
                   14, 12, 16, "light", rings=(0.5,))

    # Monitor, arm, and screen.
    builder.prism("CATH_MONITOR", rr(782, 127, 790, 175, 2.5),
                  180, 248, "z", "light")
    builder.add_round_rect_line("line", 786, 130, 790, 172, 1.5, 5, "z", 248.08)
    builder.member("CATH_MONITOR_ARM_A", (706, 214, 192), (758, 205, 187),
                   4.8, 4.4, 4, "light")
    builder.member("CATH_MONITOR_ARM_B", (756, 207, 187), (762, 202, 187),
                   7.2, 7.2, 10, "light")
    builder.member("CATH_MONITOR_ARM_C", (760, 204, 187), (786, 181, 184),
                   4.4, 4.0, 4, "light")
    builder.add_circle_line("line", 742, 180.11, 176, 3.6, 16)

    # Slate and film cans.
    builder.prism("CATH_SLATE", rr(628, 294, 772, 402, 12), 0, 7,
                  "y", "light")
    for z in (334, 354, 374):
        builder.add_line("line", (628, 7.04, -z), (772, 7.04, -z))
    for x in (676, 724):
        builder.add_line("line", (x, 7.04, -294), (x, 7.04, -402))
    builder.prism("CATH_CLAPPER", rr(628, 294, 772, 309, 5),
                  7, 14, "y", "light")
    for i in range(7):
        x = 634 + 18.5 * i
        builder.add_line("line", (x, 14.05, -294),
                         (x + 9, 14.05, -303))
    builder.member("CATH_FILM_CAN_A", (528, 0, 272), (528, 9, 272),
                   24, 24, 22, "haze")
    builder.add_circle_line("line", 528, 9.05, 272, 16, 22)
    builder.member("CATH_FILM_CAN_B", (536, 9, 266), (536, 17, 266),
                   24, 24, 22, "haze")
    builder.add_circle_line("line", 536, 17.05, 266, 16, 22)
    builder.add_circle_line("line", 536, 17.06, 266, 7, 22)

    add_floor_grid(builder)


def add_emitters(builder, mats, cam):
    emitters = [
        ("CATH_KEY_LIGHT", (496, 94, 156.18), "z", 108, 80, 0.055, 1.9, 0.30),
        ("CATH_MONITOR_GLOW", (790.26, 152.5, 215), "x", 58, 33, 0.0, 2.2, 0.17),
        ("CATH_REC_LAMP", (742, 180.11, 176), "y", 3.6, 3.6, 0.88, 6.0, 0.22),
        ("CATH_SLATE_LAMP", (736, 7.11, 386), "y", 36, 11, 0.42, 3.0, 0.11),
        ("CATH_FOCUS_LAMP", (658, 7.11, 386), "y", 10, 10, 0.34, 4.0, 0.09),
    ]
    for name, pos, axis, w, d, cap, spread, glow in emitters:
        CE.emitter_cap(builder, mats, name + "_CAP", pos, axis, w, d, cap)
        center = CL.W(pos)
        CE.glow_overlay(builder, mats, cam, name + "_GLOW", center,
                        max(w, d) * spread, glow)


def main():
    CS.clear_scene()
    scene = bpy.context.scene
    scene.name = "CATHODE_CINEMA_REFERENCE"
    coll = CS.get_collection("CATHODE_REFERENCE")
    mats = CL.get_materials()
    cam, frustum = CS.make_camera(scene)
    CS.render_setup(scene)
    builder = CG.Builder(coll, mats)
    build_rig(builder, mats)
    add_emitters(builder, mats, cam)
    CS.feed_plane(scene, coll)
    CE.emit_lines(builder, mats)

    left, right, top, bottom = frustum
    hw, hh = (right - left) / 2.0, (top - bottom) / 2.0
    bg = CS.background_material(scene)
    grain = CS.grain_material(scene, CS.grain_image(scene, t=0.0))
    # Camera looks along local -Z; rig geometry is around -4,200, so the
    # background must be farther away than the rig, not closer to the camera.
    CE.full_frame(cam, "CATH_BACKGROUND", hw * 1.02, hh * 1.02, -5000, mat=bg)
    grain_obj = CE.full_frame(cam, "CATH_GRAIN", hw * 1.02, hh * 1.02, -401, mat=grain)
    # Eevee's depth handling can let this transparent overlay occlude the
    # procedural rig. Keep the deterministic validation still clean; grain
    # can be added later in the compositor without changing scene geometry.
    grain_obj.hide_render = True

    out = HERE / "outputs" / "blender"
    out.mkdir(parents=True, exist_ok=True)
    still = out / "cathode-cinema-reference-v01.png"
    blend = out / "cathode-cinema-reference-v01.blend"
    report = out / "cathode-cinema-reference-v01-report.json"
    scene.render.filepath = str(still)
    bpy.ops.render.render(write_still=True)
    CS.save_blend(str(blend))
    CS.report(str(report), source="threeui.com Cathode Cinema procedural HTML",
              output=str(blend), render=str(still), procedural=True,
              object_count=len(builder.objects), stats=builder.stats,
              materials=sorted({m.name for o in builder.objects
                                for m in o.data.materials if m}),
              frustum=list(frustum), timeline_frames=240, fps=24)
    print("Cathode reference written to", blend)


if __name__ == "__main__":
    main()
