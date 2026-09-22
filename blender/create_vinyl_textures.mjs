// Shared, typography-led cover textures: Blender and Three.js use the same PNGs.
// Icon paths are the existing MIT-licensed Fluent UI symbols, not new artwork.
import { readFile, mkdir } from 'node:fs/promises';
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const require = createRequire(import.meta.url);
const sharp = require(process.env.VINYL_SHARP_PATH || 'sharp');
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const projects = JSON.parse(await readFile(path.join(root,'app/data/vinyls.json'),'utf8'));
const icons = JSON.parse((await readFile(path.join(root,'app/components/vinylProjectIcons.ts'),'utf8')).match(/= (\[.*\]);/s)[1]);
const output = path.join(root,'public/room/vinyl-art'); await mkdir(output,{recursive:true});
const escape = text => text.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
function lines(text, max) {
  const result=[]; let line='';
  for(const word of text.split(' ')){if(line.length+word.length>max){result.push(line.trim());line='';}line+=word+' ';}
  result.push(line.trim());return result;
}
function textLines(text,y,size,max){return lines(text,max).map((s,i)=>`<text x="64" y="${y+i*size*1.4}" font-size="${size}">${escape(s)}</text>`).join('');}
for(const [i,p] of projects.entries()){
 for(const side of ['front','back','spine']){
  const spine=side==='spine'; const width=spine?128:896;
  // Rotated +90 rather than the old -90: only the spine reading direction flips.
  const content=spine?`<g transform="translate(64 448) rotate(90)"><text x="0" y="17" text-anchor="middle" font-size="49" font-weight="bold" textLength="${Math.min(790,p.title.length*27)}" lengthAdjust="spacingAndGlyphs">${escape(p.title)}</text></g>`:
   `<rect x="32" y="32" width="832" height="832" fill="none" stroke="#999" stroke-width="2"/><text x="64" y="92" font-size="24">${String(i+1).padStart(2,'0')} / ${p.href?'2026':'COMING SOON'}</text>`+
   (side==='front'?`${p.icon===null?'<text x="448" y="430" text-anchor="middle" font-size="100">…</text>':`<path transform="translate(298 185) scale(15)" d="${icons[p.icon]}"/>`}${textLines(p.title,610,44,30)}<text x="64" y="810" font-size="24">${escape(p.label.toUpperCase())}</text>`:
   `${textLines(p.title,180,42,30)}${textLines(p.summary,180+lines(p.title,30).length*60+60,36,37)}<text x="64" y="810" font-size="23">${p.href?'CLICK THE RECORD TO OPEN':'COMING SOON'}</text>`);
  await sharp(Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="896"><rect width="100%" height="100%" fill="#292929"/><g fill="#e0e0e0" font-family="Arial,sans-serif">${content}</g></svg>`)).png().toFile(path.join(output,`${p.slug}-${side}.png`));
 }
}
console.log('Created shared textures for all seven records.');
