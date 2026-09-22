# -*- coding: utf-8 -*-
"""
cathode_geo.py
==============
Geometry Builder for the cathode art system. Port of the construction
helpers from cathode-cinema.html (prism / member / loft3 / loopAt /
railAt / dashed), authored in MODEL space and emitted in mirrored
WORLD space (W()).

Face shading: each face gets material 0 (bright #1b1b1b) or 1 (dark
#121212) from the dominant axis of its MIRRORED normal (see
cathode_lib.face_class). matDark objects are single-material.
"""

import math
import bpy
from mathutils import Vector

import cathode_lib as CL


def _sxy(g):
    """screen-space coords of a model point (source's sxy)."""
    return (g[2] - g[0], 0.5774 * (g[0] + g[2]) - 1.1547 * g[1])


class Builder:
    def __init__(self, collection, mats):
        self.coll = collection
        self.mats = mats
        self.objects = []
        self.line_segs = {"line": [], "grid": [], "mark": [], "dim": []}
        self.stats = {"prisms": 0, "members": 0, "lofts": 0, "lines": 0,
                      "emitters": 0, "meshes": 0}

    # -- profiles -------------------------------------------------------------
    @staticmethod
    def round_rect(x0, y0, x1, y1, r, seg=5):
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        corners = [(x1 - r, y0 + r, -math.pi / 2, 0),
                   (x1 - r, y1 - r, 0, math.pi / 2),
                   (x0 + r, y1 - r, math.pi / 2, math.pi),
                   (x0 + r, y0 + r, math.pi, math.pi * 1.5)]
        p = []
        for cx, cy, a0, a1 in corners:
            for i in range(seg + 1):
                a = a0 + (a1 - a0) * i / seg
                p.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        return p

    @staticmethod
    def map_profile(a, b, t, axis):
        if axis == "z":
            return Vector((a, b, t))
        if axis == "x":
            return Vector((t, b, -a))
        return Vector((a, t, -b))

    # -- mesh plumbing ----------------------------------------------------------
    def _new_object(self, name, verts, faces):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in verts], [], faces)
        me.update()
        ob = bpy.data.objects.new(name, me)
        self.coll.objects.link(ob)
        self.objects.append(ob)
        self.stats["meshes"] += 1
        return ob, me

    @staticmethod
    def _face_normal(pts):
        a, b, c = Vector(pts[0]), Vector(pts[1]), Vector(pts[2])
        n = (b - a).cross(c - a)
        return n.normalized() if n.length > 1e-12 else Vector((0, 0, 1))

    def _assign(self, ob, me, model_faces, matset):
        if matset == "haze_panel":
            ob.data.materials.append(CL.haze_material(1.0, "CATH_HAZE_PANEL"))
            return
        if matset == "haze":
            ob.data.materials.append(CL.haze_material(0.8, "CATH_HAZE"))
            return
        if matset == "dark":
            ob.data.materials.append(self.mats["dark"])
            return
        ob.data.materials.append(self.mats["bright"])
        ob.data.materials.append(self.mats["dark"])
        # W() is a reflection: world winding normal == -geometric normal.
        for i in range(len(model_faces)):
            wn = self._face_normal(model_faces[i])
            me.polygons[i].material_index = CL.face_class(
                CL.WN((-wn.x, -wn.y, -wn.z)))

    # -- primitives -------------------------------------------------------------
    def prism(self, name, profile, t0, t1, axis, matset="light", holes=()):
        """
        Extruded profile from t0 to t1 along `axis`.
        holes: list of closed (a,b) profile loops; caps become bridged
        annuli and each hole gets a vertical wall.
        """
        pts0 = [self.map_profile(a, b, t0, axis) for a, b in profile]
        pts1 = [self.map_profile(a, b, t1, axis) for a, b in profile]
        n = len(profile)
        faces, mf, verts_model = [], [], []
        if holes:
            hpts = [self.map_profile(a, b, t0, axis) for a, b in holes[0]]
            hpts1 = [self.map_profile(a, b, t1, axis) for a, b in holes[0]]
            m = len(holes[0])
            step = [round(n * i / m) % n for i in range(m)]
            verts_model = pts0 + pts1 + hpts + hpts1
            for i in range(m):
                j = (i + 1) % m
                faces.append([step[i], step[j], 2 * n + j, 2 * n + i])
                mf.append([pts0[step[i]], pts0[step[j]], hpts[j], hpts[i]])
                faces.append([n + step[i], n + step[j],
                              2 * n + m + i, 2 * n + m + j])
                mf.append([pts1[step[i]], pts1[step[j]],
                           hpts1[i], hpts1[j]])
                faces.append([2 * n + i, 2 * n + j,
                              2 * n + m + j, 2 * n + m + i])
                mf.append([hpts[i], hpts[j], hpts1[j], hpts1[i]])
            for i in range(n):
                j = (i + 1) % n
                faces.append([i, j, n + j, n + i])
                mf.append([pts0[i], pts0[j], pts1[j], pts1[i]])
        else:
            verts_model = pts0 + pts1
            faces.append(list(range(n - 1, -1, -1)))
            faces.append(list(range(n, 2 * n)))
            mf.append(pts0)
            mf.append(pts1)
            for i in range(n):
                j = (i + 1) % n
                faces.append([i, j, n + j, n + i])
                mf.append([pts0[i], pts0[j], pts1[j], pts1[i]])
        ob, me = self._new_object(name, [CL.W(p) for p in verts_model], faces)
        self._assign(ob, me, mf, matset)
        self.stats["prisms"] += 1
        return ob

    def member(self, name, p, q, r0, r1, seg, matset="light",
               line_key="line", open_a=False, open_b=False, rings=()):
        """
        Lofted seg-gon tube p (radius r0) -> q (radius r1).
        Edges (source member()): end loops unless open, corner strokes for
        seg<=6, two screen-extreme strokes for barrels, plus rings.
        """
        p, q = Vector(p), Vector(q)
        d = q - p
        L = d.length
        up = Vector((1, 0, 0)) if abs(d.y) > L * 0.94 else Vector((0, 1, 0))
        u = up.cross(d).normalized()
        v = d.cross(u).normalized()
        phase = 0.5

        def ring(t):
            r = r0 + (r1 - r0) * t
            c = p.lerp(q, t)
            return [c + (u * math.cos((i + phase) / seg * 2 * math.pi)
                         + v * math.sin((i + phase) / seg * 2 * math.pi)) * r
                    for i in range(seg)]

        A, B = ring(0.0), ring(1.0)
        stack = [0.0] + sorted(t for t in rings if 0.0 < t < 1.0) + [1.0]
        ring_of = {t: ring(t) for t in stack}
        all_pts = [pt for t in stack for pt in ring_of[t]]
        base_of = {t: i * seg for i, t in enumerate(stack)}
        all_faces, mf = [], []
        if not open_a:
            all_faces.append(list(range(seg - 1, -1, -1)))
            mf.append(ring_of[0.0])
        if not open_b:
            b0 = base_of[1.0]
            all_faces.append([b0 + i for i in range(seg)])
            mf.append(ring_of[1.0])
        for k in range(len(stack) - 1):
            a, b = stack[k], stack[k + 1]
            if (open_a and a == 0.0) or (open_b and b == 1.0):
                continue
            ba, bb = base_of[a], base_of[b]
            for i in range(seg):
                j = (i + 1) % seg
                all_faces.append([ba + i, ba + j, bb + j, bb + i])
                mf.append([ring_of[a][i], ring_of[a][j],
                           ring_of[b][j], ring_of[b][i]])
        ob, me = self._new_object(name, [CL.W(pt) for pt in all_pts], all_faces)
        self._assign(ob, me, mf, matset)
        self.stats["members"] += 1
        if not open_a:
            self.add_loop(line_key, A)
        if not open_b:
            self.add_loop(line_key, B)
        if seg <= 6:
            for i in range(seg):
                self.add_line(line_key, A[i], B[i])
        else:
            s0, s1 = _sxy(p), _sxy(q)
            ax, ay = s1[0] - s0[0], s1[1] - s0[1]
            al = math.hypot(ax, ay) or 1.0
            ax, ay = ax / al, ay / al
            lo, hi, lo_v, hi_v = 0, 0, float("inf"), -float("inf")
            for i in range(seg):
                s = _sxy(A[i])
                across = (s[0] - s0[0]) * (-ay) + (s[1] - s0[1]) * ax
                if across < lo_v:
                    lo_v, lo = across, i
                if across > hi_v:
                    hi_v, hi = across, i
            self.add_line(line_key, A[lo], B[lo])
            self.add_line(line_key, A[hi], B[hi])
        for t in sorted(rings):
            if 0.0 < t < 1.0:
                self.add_loop(line_key, ring_of[t])
        return ob

    def loft3(self, name, A, B, C, r0, r1, seg, matset="light"):
        mid = (r0 + r1) / 2
        self.member(name + "_ab", A, B, r0, mid, seg, matset,
                    open_a=True, open_b=True)
        self.member(name + "_bc", B, C, mid, r1, seg, matset,
                    open_a=True, open_b=True)
        self.stats["lofts"] += 1

    # -- line API -----------------------------------------------------------------
    def add_line(self, key, a, b):
        self.line_segs[key].append((Vector(a), Vector(b)))
        self.stats["lines"] += 1

    def add_loop(self, key, pts):
        pts = [Vector(p) for p in pts]
        for i in range(len(pts)):
            self.add_line(key, pts[i], pts[(i + 1) % len(pts)])

    def loop_at(self, key, profile, t, axis):
        self.add_loop(key, [self.map_profile(a, b, t, axis)
                            for a, b in profile])

    def add_round_rect_line(self, key, x0, y0, x1, y1, r, seg=5,
                            axis="z", at=0.0):
        self.loop_at(key, self.round_rect(x0, y0, x1, y1, r, seg), at, axis)

    def add_circle_line(self, key, cx, cy, cz, r, seg=16):
        pts = [(cx + math.cos(2 * math.pi * i / seg) * r, cy,
                cz + math.sin(2 * math.pi * i / seg) * r)
               for i in range(seg)]
        self.add_loop(key, pts)

    def rail_at(self, key, profile, indices, t0, t1, axis):
        for i in indices:
            a = self.map_profile(profile[i][0], profile[i][1], t0, axis)
            b = self.map_profile(profile[i][0], profile[i][1], t1, axis)
            self.add_line(key, a, b)

    def dashed(self, key, ax, ay, az, bx, by, bz, on=6.5, off=5.0):
        dx, dz = bx - ax, bz - az
        L = math.hypot(dx, dz)
        if L < 1e-9:
            return
        t = 0.0
        while t < L:
            t2 = min(t + on, L)
            self.add_line(key, (ax + dx * t / L, ay, az + dz * t / L),
                          (ax + dx * t2 / L, ay, az + dz * t2 / L))
            t = t2 + off
