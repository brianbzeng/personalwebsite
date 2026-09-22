# -*- coding: utf-8 -*-
"""
cathode_feed.py
===============
Pure-python port of the cinema monitor feed fragment shader from
cathode-cinema.html (lines ~775-830). Generates the 512x288 Non-Color
emission texture used by the monitor screen.

Coordinate system (source):  p = ((1-uv.x)*58, (1-uv.y)*33), i.e. p.x
runs left->right, p.y runs top->bottom across the 58x33 screen.
t is the feed time; the source's reduced-motion fallback is t = 0.75.
"""

import math
import bpy


def _fill(p, c, h):
    x = max(abs(p[0] - c[0]) - h[0], 0.0)
    y = max(abs(p[1] - c[1]) - h[1], 0.0)
    d = max(x, y)
    s = min(1.0, max(0.0, (d - 0.0) / 0.9))
    s = s * s * (3.0 - 2.0 * s)
    return 1.0 - s


def _frame(p, c, h, w):
    x = max(abs(p[0] - c[0]) - h[0], 0.0)
    y = max(abs(p[1] - c[1]) - h[1], 0.0)
    d = max(x, y)
    s = min(1.0, max(0.0, d / 0.8))
    s = s * s * (3.0 - 2.0 * s)
    return (1.0 - s) * (1.0 if w >= 0.0 else 0.0)


def _mix(a, b, f):
    return a + (b - a) * f


def _step(thresh, v):
    return 1.0 if v >= thresh else 0.0


def _hash2(x, y):
    # fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453)
    d = x * 12.9898 + y * 78.233
    return (math.sin(d) * 43758.5453) % 1.0


def _pixel(px, py, t):
    c = 0.0500
    # lit backdrop falling off toward the corners
    qx = px / 58.0 - 0.46
    qy = py / 33.0 - 0.44
    c += 0.085 * math.exp(-(qx * qx + qy * qy) * 5.2)
    # horizon and floor under it
    HZ = 33.0 * 0.63
    s = min(1.0, max(0.0, (py - (HZ - 0.7)) / 1.4))
    s = s * s * (3.0 - 2.0 * s)
    c = _mix(c, 0.052, s)
    s2 = min(1.0, max(0.0, abs(py - HZ) / 0.9))
    s2 = s2 * s2 * (3.0 - 2.0 * s2)
    c = _mix(c, 0.20, 1.0 - s2)
    # drifting subject
    sx = 58.0 * 0.40 + math.sin(t * 0.31) * 2.6
    sy = HZ - 9.0 + math.sin(t * 0.47) * 0.9
    c = _mix(c, 0.62, _fill((px, py), (sx, sy), (3.4, 8.6)))
    c = _mix(c, 0.74, _fill((px, py), (sx, sy - 11.5), (2.5, 2.6)))
    c = _mix(c, 0.30, _fill((px, py), (sx, HZ + 1.2), (5.4, 0.9)))
    # rule of thirds + centre cross
    for i in (1, 2):
        fi = i / 3.0
        c = _mix(c, 0.13, _fill((px, py), (58.0 * fi, 33.0 * 0.5),
                                (0.28, 33.0 * 0.42)))
        c = _mix(c, 0.13, _fill((px, py), (58.0 * 0.5, 33.0 * fi),
                                (58.0 * 0.42, 0.28)))
    c = _mix(c, 0.40, _fill((px, py), (29.0, 16.5), (2.6, 0.32)))
    c = _mix(c, 0.40, _fill((px, py), (29.0, 16.5), (0.32, 2.6)))
    c = _mix(c, 0.20, _frame((px, py), (29.0, 16.5), (23.2, 13.2), 1.0))
    # REC tally + timecode bar
    rec = _step(0.5, (t * 0.85) % 1.0)
    c = _mix(c, _mix(0.14, 0.92, rec),
             _fill((px, py), (5.6, 4.6), (1.7, 1.7)))
    c = _mix(c, 0.34, _fill((px, py), (12.5, 4.6), (3.4, 1.3)))
    # 6 tally blocks, top right
    for i in range(6):
        on = _step(0.35, (t * (0.9 + i * 2.3)) % 1.0)
        c = _mix(c, _mix(0.13, 0.44, on),
                 _fill((px, py), (58.0 - 27.0 + i * 4.6, 33.0 - 4.4),
                       (1.5, 1.9)))
    # exposure ladder down the right edge
    lvl = 0.46 + 0.22 * math.sin(t * 0.9)
    for k in range(7):
        on = _step(k / 7.0, lvl)
        c = _mix(c, _mix(0.11, 0.40, on),
                 _fill((px, py), (58.0 - 3.6, 9.0 + k * 3.2), (1.3, 1.1)))
    # monitor static + slow phosphor breathe
    g = _hash2(px * 3.7 + t * 61.0, py * 3.7 + t * 37.0)
    c += (g - 0.42) * 0.024
    c *= 0.985 + 0.015 * math.sin(py * 2.1 + t * 3.3)
    return max(c, 0.0)


def feed_image(w=512, h=288, t=0.75):
    """Blender image (Non-Color) with the feed rendered at time t."""
    px = bytearray(w * h * 4)
    for row in range(h):
        # blender pixel row 0 = bottom; source p.y=(1-uv.y)*33 runs top->bottom
        py = ((h - 1 - row) / h) * 33.0
        for col in range(w):
            # source p.x=(1-uv.x)*58: texture right edge = image left edge
            pv = _pixel((1.0 - col / w) * 58.0, py, t)
            i = (row * w + col) * 4
            v = int(max(0.0, min(1.0, pv)) * 255.0)
            px[i] = px[i + 1] = px[i + 2] = v
            px[i + 3] = 255
    img = bpy.data.images.new("CATH_FEED_IMG", w, h, alpha=True, float_buffer=False)
    img.pixels = [v / 255.0 for v in px]
    img.colorspace_settings.name = "Non-Color"
    return img
