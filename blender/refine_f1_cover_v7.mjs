// Approval-only: smaller flag panel, contrasting medium-gray frame and pole.
import {readFile,writeFile,mkdir,copyFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const require=createRequire(import.meta.url),sharp=require(process.env.VINYL_SHARP_PATH||'sharp');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const input=path.join(root,'blender/outputs/cover-approval-v6');
const output=path.join(root,'blender/outputs/cover-approval-v7');
await mkdir(output,{recursive:true});
const slug='f1-constructors-forecast';
const original=await readFile(path.join(input,slug+'-front.svg'),'utf8');
// Panel: 168 x 111.3, exactly 70% of v6's 240 x 159. Keep exposed pole
// length at 71px. Recenter the complete silhouette at (448,448).
const x=364,y=356.85,cell=18.9,border=8.4;
let icon=`<g id="rectangular-checkered-flag"><rect x="${x}" y="${y}" width="168" height="111.3" rx="4.2" fill="#929292"/><rect x="${x}" y="${y}" width="8.4" height="182.3" rx="4.2" fill="#929292"/>`;
for(let row=0;row<5;row++)for(let col=0;col<8;col++)icon+=`<rect x="${(x+border+cell*col).toFixed(2)}" y="${(y+border+cell*row).toFixed(2)}" width="18.9" height="18.9" fill="${(row+col)%2===0?'#292929':'#e0e0e0'}"/>`;
icon+='</g>';
const source=original.replace(/<g id="rectangular-checkered-flag">.*?<\/g>/,icon);
await writeFile(path.join(output,slug+'-front.svg'),source);
await sharp(Buffer.from(source)).png().toFile(path.join(output,slug+'-front.png'));
for(const ext of ['svg','png'])await copyFile(path.join(input,slug+'-back.'+ext),path.join(output,slug+'-back.'+ext));
await sharp({create:{width:1816,height:896,channels:3,background:'#151515'}}).composite([{input:path.join(output,slug+'-front.png'),left:0,top:0},{input:path.join(output,slug+'-back.png'),left:920,top:0}]).png().toFile(path.join(output,slug+'-pair.png'));
console.log('Approval v7: panel reduced 30% in both dimensions; medium-gray outline/pole; centered silhouette.');
