"""Read-only edge-alignment regression for retired-book composites.

Compares unchanged, high-gradient crop-border pixels with the original full
render. Does not score the book interior, whose material intentionally changed.
Run after generating web-room-v163{,-shelf,-photos}; --version 162 demonstrates
the old regression. Missing output is an error, never silently a pass.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def rgb(path):
    return np.asarray(Image.open(path).convert('RGB'), dtype=np.float32)


def placement(full, crop, source):
    changed = np.argwhere(np.max(np.abs(full - source), axis=2) > 0)
    if not changed.size:
        return None
    y, x = changed.min(axis=0)
    h, w = crop.shape[:2]
    candidates = []
    # Crop border may have unchanged rows/columns, so allow a small margin.
    for dy in range(-min(h, 60), 4):
        for dx in range(-min(w, 60), 4):
            yy, xx = int(y + dy), int(x + dx)
            if yy < 0 or xx < 0 or np.max(np.abs(full[yy,xx]-crop[0,0])) > 1:
                continue
            patch = full[yy:yy+h, xx:xx+w]
            if patch.shape == crop.shape:
                candidates.append((float(np.mean(np.abs(patch-crop))), xx, yy))
    error, x, y = min(candidates)
    if error > .05:
        raise AssertionError(f'Cannot independently locate crop: best MAE {error}')
    return x, y


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='163')
    parser.add_argument('--stride', type=int, default=12)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / 'blender/outputs'
    results, failures, missing = [], [], []
    for suffix, original in (('', '161'), ('-shelf', '155'), ('-photos', '159')):
        old = root / ('web-room-v162' + suffix)
        new = root / ('web-room-v' + args.version + suffix)
        source = root / ('web-room-v' + original)
        crops = sorted(old.glob('*/*.crop.png'))
        selected = [p for p in crops if int(p.name[:4]) % args.stride == 0]
        # Explicitly cover transition from full frames to composited idle.
        selected += [p for p in crops if p.parent.name == 'idle' and int(p.name[:4]) in (42,43)]
        for path in sorted(set(selected)):
            relative = path.relative_to(old)
            relative = relative.with_name(relative.name.replace('.crop.png', ''))
            output = new / relative
            if not output.exists():
                missing.append(str(output))
                continue
            a, b, c = rgb(source/relative), rgb(output), rgb(path)
            try:
                position = placement(b, c, a)
            except AssertionError as error:
                raise AssertionError(f'{output}: {error}') from error
            if position is None:
                continue
            x, y = position
            h, w = c.shape[:2]
            gray = c.mean(axis=2)
            gy, gx = np.gradient(gray)
            edge = np.hypot(gx, gy) > 5
            border = np.zeros((h,w), dtype=bool)
            border[:6] = border[-6:] = True
            border[:,:6] = border[:,-6:] = True
            mask = edge & border
            if mask.sum() < 8:
                continue
            scores = []
            for dy in range(-2,3):
                for dx in range(-2,3):
                    if x+dx < 0 or y+dy < 0:
                        continue
                    p = a[y+dy:y+dy+h, x+dx:x+dx+w]
                    if p.shape == c.shape:
                        scores.append((float(np.mean(np.abs(c[mask]-p[mask]))), dx, dy))
            baseline = next(s[0] for s in scores if s[1:] == (0,0))
            best = min(scores)
            failed = baseline-best[0] > 1 and best[0] < baseline*.8
            record = {'frame':str(relative), 'group':suffix or 'greeting',
                      'position':[x,y], 'edgePixels':int(mask.sum()),
                      'currentMAE':round(baseline,3), 'bestMAE':round(best[0],3),
                      'bestOffset':list(best[1:]), 'failed':failed}
            results.append(record)
            if failed:
                failures.append(record)
    print(json.dumps({'checked':len(results), 'missing':missing,
                      'failures':failures, 'results':results}, indent=2))
    assert results, 'No gradient-rich patches checked'
    assert not missing, f'{len(missing)} corrected frames missing'
    assert not failures, f'{len(failures)} patches favor a neighboring placement'


if __name__ == '__main__':
    main()
