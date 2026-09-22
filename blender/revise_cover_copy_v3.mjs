// Approval-only copy revision. Keep v2 centered fronts and existing top labels.
import {readFile,writeFile,mkdir,copyFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const require=createRequire(import.meta.url);
const sharp=require(process.env.VINYL_SHARP_PATH||'sharp');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const previous=path.join(root,'blender/outputs/cover-approval-v2');
const out=path.join(root,'blender/outputs/cover-approval-v4');
await mkdir(out,{recursive:true});
const copy={
 'castingcompass':[
  'CastingCompass is a full-stack fishing planner for California halibut that combines environmental forecasts, seafloor depth, and trip reports in a mobile-first application. The platform presents location-based recommendations with supporting conditions for trip planning.',
  'The implementation combines Python, PyTorch, and Rasterio for machine learning and geospatial processing with a Next.js and TypeScript interface. Cloudflare Workers and D1 support the application backend and data storage. Public environmental data and first-party trip reports are integrated with model outputs to connect the analysis directly to the planning interface.'
 ],
 'amazon-review-audit':[
  'The Amazon Review Suspicion Audit is an interpretable pipeline that prioritizes suspicious reviews for human inspection. The project evaluates text and behavioral signals across a 900-review audit, treating suspicion as a review priority rather than a confirmed deception label.',
  'The Python pipeline combines TF-IDF text features, review metadata, and behavioral indicators with blinded language-model review through OpenAI-compatible APIs. The evaluation uses inspectable signals and human judgment to separate automated flags from final assessments. The resulting workflow supports targeted review while retaining the evidence behind each case.'
 ],
 'f1-constructors-forecast':[
  'The F1 Constructor forecast estimates championship outcomes from in-season team performance. An interactive leaderboard presents title, top-three, and top-five probabilities alongside current standings.',
  'The Python pipeline uses Ridge regression with expanding-window season validation and 10,000 seeded residual simulations to estimate finishing-position probabilities. Race-only features are kept separate from championship targets that include Sprint points, and the displayed standings align with the forecast snapshot. The interface exposes model inputs and uncertainty alongside the projected rankings.'
 ],
 'nba-odds-predictor':[
  'The NBA Home Win Predictor presents matchup-level predictions in an interactive forecast board. The project combines a statistical model with a web interface for reviewing team strength and game-specific conditions.',
  'The forecasting approach combines margin-adjusted Elo ratings with recent form, rest, and injury data. Python and Pandas support the analytical workflow, while a Next.js interface presents model outputs and their assumptions. The application connects game-level estimates to a readable presentation of the factors used in the forecast.'
 ],
 'ttb-label-review-assistant':[
  'TTB Labeler is an AI-assisted alcohol-label review prototype that organizes submission evidence into a structured review queue. The project supports three human-review workflows while keeping final decisions with the reviewer.',
  'The implementation combines Python, language-model-assisted extraction, and commodity-aware rule systems to identify relevant label details and guide product-specific checks. Outputs are structured around extracted evidence and review prompts, with Quarto used for project reporting. Each review step is linked to the source material without treating the automated output as regulatory approval.'
 ]
};
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
function wrap(text){const rows=[];let row='';for(const word of text.split(' ')){if((row+' '+word).trim().length>53){rows.push(row);row=word;}else row=(row+' '+word).trim();}if(row)rows.push(row);return rows;}
for(const [slug,paragraphs]of Object.entries(copy)){
 if(paragraphs.some(p=>/\b(I|me|my|we|our|us)\b|\?/i.test(p)))throw new Error(`Unexpected personal phrasing or question: ${slug}`);
 let y=200;
 const body=paragraphs.map(p=>{const result=wrap(p).map(line=>{const text=`<text x="64" y="${y}" font-size="27">${esc(line)}</text>`;y+=36;return text;}).join('');y+=24;return result;}).join('');
 if(y>830)throw new Error(`Copy overflow: ${slug}`);
 const old=await readFile(path.join(previous,`${slug}-back.svg`),'utf8');
 const prefix=old.slice(0,old.indexOf('<text x="64" y="200"'));
 if(prefix===old)throw new Error('Missing copy boundary');
 const source=prefix+body+'</g></svg>';
 await writeFile(path.join(out,`${slug}-back.svg`),source);
 await sharp(Buffer.from(source)).png().toFile(path.join(out,`${slug}-back.png`));
 for(const ext of ['svg','png'])await copyFile(path.join(previous,`${slug}-front.${ext}`),path.join(out,`${slug}-front.${ext}`));
 await sharp({create:{width:1816,height:896,channels:3,background:'#151515'}}).composite([{input:path.join(out,`${slug}-front.png`),left:0,top:0},{input:path.join(out,`${slug}-back.png`),left:920,top:0}]).png().toFile(path.join(out,`${slug}-pair.png`));
}
await writeFile(path.join(out,'copy.json'),JSON.stringify({status:'approval-only; not applied',style:'Project-led descriptions and implementation statements; no first person, storytelling or questions',sources:['app/data/projects.ts','docs/f1-desktop.md'],copy},null,2));
console.log('Rendered five revised backs; centered fronts and top labels unchanged. '+out);
