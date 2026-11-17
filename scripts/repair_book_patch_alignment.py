"""Recompose existing book renders at their measured pixel alignment.

Keeps all v162 frames/media intact. No scene or camera changes and no resampling.
Outer crop margins contain unchanged geometry, providing registration evidence.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
import shutil
import subprocess
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / 'blender/outputs'
SOURCES = {'web-room-v162': 'web-room-v161',
           'web-room-v162-shelf': 'web-room-v155',
           'web-room-v162-photos': 'web-room-v159'}

def repair(job):
    folder, relative = job
    old = ROOT/folder/relative
    dest = ROOT/folder.replace('v162','v163')/relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    crop_path = Path(str(old)+'.crop.png')
    if not crop_path.exists():
        shutil.copyfile(old, dest)
        return {'frame':str(relative), 'folder':folder, 'fullFrame':True}
    original = ROOT/SOURCES[folder]/relative
    a = np.asarray(Image.open(original).convert('RGB')).astype(np.int16)
    b = np.asarray(Image.open(old).convert('RGB')).astype(np.int16)
    c = np.asarray(Image.open(crop_path).convert('RGB')).astype(np.int16)
    h,w = c.shape[:2]
    changed = np.argwhere(np.max(abs(a-b),axis=2)>0)
    if not len(changed):
        shutil.copyfile(old,dest)
        return {'frame':str(relative),'folder':folder,'unchanged':True}
    by,bx = changed.min(axis=0)
    candidates=[]
    for y in range(max(0,by-4),min(a.shape[0]-h,by+4)+1):
        for x in range(max(0,bx-4),min(a.shape[1]-w,bx+4)+1):
            candidates.append((float(np.mean(abs(b[y:y+h,x:x+w]-c))),x,y))
    exact,x,y = min(candidates)
    assert exact == 0, (old, 'Cannot locate existing crop', exact)
    mask = np.zeros((h,w),bool)
    mask[:6,:]=mask[-6:,:]=mask[:,:6]=mask[:,-6:]=True
    # Reproduce Blender's float32 multiply then integer truncation exactly.
    # Do not use image fitting to choose placement: clipped/offscreen book
    # patches do not always contain enough unchanged edge pixels to register.
    height,width=a.shape[:2]
    xx=int(np.float32(x/width)*np.float32(width))
    yy=height-int(np.float32((height-y)/height)*np.float32(height))
    score=float(np.mean(abs(a[yy:yy+h,xx:xx+w]-c)[mask]))
    old_score=float(np.mean(abs(a[y:y+h,x:x+w]-c)[mask]))
    existing=np.asarray(Image.open(dest).convert('RGB')) if dest.exists() else None
    if existing is None or not np.array_equal(existing[yy:yy+h,xx:xx+w],c):
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(original),'-i',str(crop_path),
            '-filter_complex',f'[0:v][1:v]overlay={xx}:{yy}:format=rgb',
            '-frames:v','1','-threads','1',str(dest)],check=True)
    return {'folder':folder,'frame':str(relative),'old':[x,y],'new':[xx,yy],
            'oldBorderMAE':old_score,'newBorderMAE':score}

if __name__ == '__main__':
    jobs=[(folder,p.relative_to(ROOT/folder)) for folder in SOURCES
          for p in (ROOT/folder).rglob('*.png') if not p.name.endswith('.crop.png')]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(repair,jobs))
    report=ROOT/'book-patch-v163-alignment.json'
    report.write_text(json.dumps(results,indent=2))
    print(json.dumps({'frames':len(results),'moved':sum(r.get('old')!=r.get('new') for r in results),
                      'report':str(report)}))
