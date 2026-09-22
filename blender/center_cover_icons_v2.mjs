// Reposition the existing vector icons only; retain the approved-draft typography.
import {readFile,writeFile,mkdir,copyFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const require=createRequire(import.meta.url);
const sharp=require(process.env.VINYL_SHARP_PATH||'sharp');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const previous=path.join(root,'blender/outputs/cover-approval-v1');
const out=path.join(root,'blender/outputs/cover-approval-v2');
await mkdir(out,{recursive:true});
const manifest=JSON.parse(await readFile(path.join(previous,'copy-and-layout.json'),'utf8'));
const audit=[];
for(const p of manifest.projects){
 const source=await readFile(path.join(previous,`${p.slug}-front.svg`),'utf8');
 const d=source.match(/<path transform="[^"]+" d="([^"]+)"/)[1];
 const {data,info}=await sharp(Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300"><path transform="scale(15)" fill="white" d="${d}"/></svg>`)).ensureAlpha().raw().toBuffer({resolveWithObject:true});
 let minX=300,minY=300,maxX=0,maxY=0;
 for(let y=0;y<300;y++)for(let x=0;x<300;x++)if(data[(y*300+x)*info.channels+3]>127){minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);}
 const x=448-(minX+maxX+1)/2,y=448-(minY+maxY+1)/2;
 const centered=source.replace('translate(298 185)',`translate(${x} ${y})`);
 await writeFile(path.join(out,`${p.slug}-front.svg`),centered);
 await sharp(Buffer.from(centered)).png().toFile(path.join(out,`${p.slug}-front.png`));
 for(const ext of ['png','svg'])await copyFile(path.join(previous,`${p.slug}-back.${ext}`),path.join(out,`${p.slug}-back.${ext}`));
 await sharp({create:{width:1816,height:896,channels:3,background:'#151515'}}).composite([{input:path.join(out,`${p.slug}-front.png`),left:0,top:0},{input:path.join(out,`${p.slug}-back.png`),left:920,top:0}]).png().toFile(path.join(out,`${p.slug}-pair.png`));
 audit.push({slug:p.slug,iconCenter:[448,448],translation:[x,y],sizeUnchanged:true,backUnchanged:true});
}
await writeFile(path.join(out,'centering-audit.json'),JSON.stringify(audit,null,2));
console.log(JSON.stringify(audit));
