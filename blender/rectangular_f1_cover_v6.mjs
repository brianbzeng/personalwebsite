// Approval-only refinement of the existing editable checkered-flag icon.
import {readFile,writeFile,mkdir,copyFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const require=createRequire(import.meta.url),sharp=require(process.env.VINYL_SHARP_PATH||'sharp');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const input=path.join(root,'blender/outputs/cover-approval-v5');
const output=path.join(root,'blender/outputs/cover-approval-v6');
await mkdir(output,{recursive:true});
const slug='f1-constructors-forecast';
const original=await readFile(path.join(input,slug+'-front.svg'),'utf8');
// Eight columns by five rows; each checker is exactly 27 x 27, never stretched.
// Flag + pole bounds: (328,333)..(568,563), centered exactly on (448,448).
let icon='<g id="rectangular-checkered-flag"><rect x="328" y="333" width="240" height="159" rx="6"/><rect x="328" y="333" width="12" height="230" rx="6"/>';
for(let row=0;row<5;row++)for(let col=0;col<8;col++)if((row+col)%2===0)icon+=`<rect x="${340+27*col}" y="${345+27*row}" width="27" height="27" fill="#292929"/>`;
icon+='</g>';
const source=original.replace(/<path transform="[^"]+" d="[^"]+"\/>/,icon);
await writeFile(path.join(output,slug+'-front.svg'),source);
await sharp(Buffer.from(source)).png().toFile(path.join(output,slug+'-front.png'));
for(const ext of ['svg','png'])await copyFile(path.join(input,slug+'-back.'+ext),path.join(output,slug+'-back.'+ext));
await sharp({create:{width:1816,height:896,channels:3,background:'#151515'}}).composite([{input:path.join(output,slug+'-front.png'),left:0,top:0},{input:path.join(output,slug+'-back.png'),left:920,top:0}]).png().toFile(path.join(output,slug+'-pair.png'));
console.log('Centered 8 x 5 rectangular flag; 27px square checkers. Approval only.');
