// Approval-only icon swap using the same installed MIT Fluent icon family.
import {readFile,writeFile,mkdir,copyFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const require=createRequire(import.meta.url),sharp=require(process.env.VINYL_SHARP_PATH||'sharp');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const input=path.join(root,'blender/outputs/cover-approval-v4');
const output=path.join(root,'blender/outputs/cover-approval-v5');
await mkdir(output,{recursive:true});
const slug='f1-constructors-forecast';
const library=await readFile(path.join(root,'node_modules/@fluentui/react-icons/lib/icons/chunk-18.js'),'utf8');
const d=library.match(/createFluentIcon\('FlagCheckeredRegular', "1em", \["([^"]+)"\]/)[1];
const original=await readFile(path.join(input,slug+'-front.svg'),'utf8');
// Bounds x=5..16, y=3..18 at scale 15: center the visible shape at (448,448).
const svg=original.replace(/<path transform="[^"]+" d="[^"]+"\/>/,`<path transform="translate(290.5 290.5) scale(15)" d="${d}"/>`);
await writeFile(path.join(output,slug+'-front.svg'),svg);
await sharp(Buffer.from(svg)).png().toFile(path.join(output,slug+'-front.png'));
for(const ext of ['svg','png'])await copyFile(path.join(input,slug+'-back.'+ext),path.join(output,slug+'-back.'+ext));
await sharp({create:{width:1816,height:896,channels:3,background:'#151515'}}).composite([{input:path.join(output,slug+'-front.png'),left:0,top:0},{input:path.join(output,slug+'-back.png'),left:920,top:0}]).png().toFile(path.join(output,slug+'-pair.png'));
console.log('F1 checkered flag approval draft saved; other covers and live assets unchanged.');
