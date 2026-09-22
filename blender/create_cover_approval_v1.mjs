// Approval-only revision of the existing editable cover layout. No live assets change.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {createRequire} from 'node:module';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const require=createRequire(import.meta.url);
const sharp=require(process.env.VINYL_SHARP_PATH||'sharp');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(root,'blender/outputs/cover-approval-v1');
await mkdir(out,{recursive:true});
const icons=JSON.parse((await readFile(path.join(root,'app/components/vinylProjectIcons.ts'),'utf8')).match(/= (\[.*\]);/s)[1]);
const projects=[
 {slug:'castingcompass',name:'CastingCompass',subtitle:'Halibut Planner',icon:0,actors:['Python','PyTorch','Next.js','Cloudflare'],paragraphs:[
 'A fishing trip begins with a practical question: where are the conditions worth exploring? CastingCompass brings ocean, weather, seafloor depth, and trip reports into one planning workflow for California halibut. Environmental inputs and model outputs help anglers compare locations instead of piecing together separate forecasts.',
 'The project connects geospatial processing and machine learning with a mobile-first interface. Its emphasis is on explaining the conditions behind a recommendation, not just displaying a score. Predictions remain planning aids rather than guarantees of a catch; the value is in making the available evidence easier to inspect before heading out.'
 ]},
 {slug:'amazon-review-audit',name:'Amazon',subtitle:'Review Suspicion Audit',icon:2,actors:['Python','TF-IDF','NLP','Blinded LLM Review'],paragraphs:[
 'An unusual review is not necessarily a dishonest one. This project examines how review text and behavioral metadata can help prioritize cases for closer inspection without treating suspicion as proof. Text patterns are represented with TF-IDF, which highlights words that distinguish one review from others in the collection.',
 'The audit combines these signals with blinded language-model review to make the reasoning behind a flag easier to examine. The goal is a transparent triage process: identify what deserves attention, explain why it was selected, and leave the final judgment to a human. Its conclusions concern review priority, not verified deception.'
 ]},
 {slug:'f1-constructors-forecast',name:'F1 Constructor',subtitle:'Championship Forecast',icon:4,actors:['Python','FastF1','Ridge Regression','Monte Carlo'],paragraphs:[
 'A constructor leaderboard shows the season so far, but it does not settle how the championship will finish. This project uses current team performance to build an in-season forecast, then examines how uncertainty in future races changes the range of possible outcomes.',
 'Ridge regression provides a regularized model of performance, while race simulations turn that estimate into probability-weighted championship scenarios. The result is a way to compare plausible finishes rather than present one predicted ranking as a fact. Those probabilities depend on the model inputs and simulation assumptions, so the uncertainty belongs beside the forecast, not hidden behind it.'
 ]},
 {slug:'nba-odds-predictor',name:'NBA Home Win Predictor',subtitle:'Game Forecast Model',icon:1,actors:['Python','Pandas','Elo Ratings','Next.js'],paragraphs:[
 'A matchup involves more than two teams and their season records. This project combines margin-adjusted Elo ratings with recent form, rest, and injury information to estimate NBA game outcomes. Elo provides a running measure of team strength, while the additional inputs capture conditions around a particular game.',
 'The interface presents those estimates as a readable forecast board, with the aim of making the model assumptions visible rather than hiding everything behind a single probability. A forecast describes an uncertain outcome, not a guaranteed winner. Its usefulness depends on both the quality of the inputs and how clearly the estimate can be interpreted.'
 ]},
 {slug:'ttb-label-review-assistant',name:'TTB Labeler',subtitle:'Label Review Assistant',icon:3,actors:['Python','LLM Extraction','Rule Systems','Quarto'],paragraphs:[
 'Reviewing an alcohol label means locating the right evidence and checking it against the rules for that product type. This project organizes that work into a structured review workflow, using language-model-assisted extraction to surface relevant label details and commodity-aware rules to guide the next checks.',
 'The assistant is designed to narrow the search without hiding the source material. Evidence and review prompts support a human decision rather than replace it, keeping attention on what the submission actually contains. This makes the project a decision-support prototype: it helps organize a review, but does not establish that a label has been approved or is compliant.'
 ]}
];
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const wrap=(s,max=53)=>{const rows=[];let row='';for(const w of s.split(' ')){if((row+' '+w).trim().length>max){rows.push(row);row=w;}else row=(row+' '+w).trim();}if(row)rows.push(row);return rows;};
const frame='<rect x="32" y="32" width="832" height="832" fill="none" stroke="#999" stroke-width="2"/>';
const svg=content=>`<svg xmlns="http://www.w3.org/2000/svg" width="896" height="896"><rect width="896" height="896" fill="#292929"/><g fill="#e0e0e0" font-family="Arial,sans-serif">${frame}${content}</g></svg>`;
for(const p of projects){
 const front=svg(`<path transform="translate(298 185) scale(15)" d="${icons[p.icon]}"/><text x="64" y="808" font-size="30">${esc(p.name)}<tspan dx="12" font-size="24">-</tspan><tspan dx="12" font-size="24">${esc(p.subtitle)}</tspan></text>`);
 let y=200;
 const paragraphs=p.paragraphs.map(text=>{const result=wrap(text).map(line=>{const s=`<text x="64" y="${y}" font-size="27">${esc(line)}</text>`;y+=36;return s;}).join('');y+=24;return result;}).join('');
 if(y>830)throw new Error(`Copy overflows: ${p.name} ${y}`);
 const actors=p.actors.map((actor,i)=>`<text x="${160+192*i}" y="97" text-anchor="middle" font-size="${actor.length>15?18:21}">${esc(actor)}</text>${i<3?`<circle cx="${256+192*i}" cy="90" r="2.4"/>`:''}`).join('');
 const back=svg(actors+paragraphs);
 for(const [side,source]of [['front',front],['back',back]]){
   await writeFile(path.join(out,`${p.slug}-${side}.svg`),source);
   await sharp(Buffer.from(source)).png().toFile(path.join(out,`${p.slug}-${side}.png`));
 }
 await sharp({create:{width:1816,height:896,channels:3,background:'#151515'}}).composite([{input:path.join(out,`${p.slug}-front.png`),left:0,top:0},{input:path.join(out,`${p.slug}-back.png`),left:920,top:0}]).png().toFile(path.join(out,`${p.slug}-pair.png`));
}
await writeFile(path.join(out,'copy-and-layout.json'),JSON.stringify({status:'approval-only; not applied',source:'app/data/projects.ts and app/data/vinyls.json',writingSkill:'brian-data-science-writing',projects},null,2));
console.log('Created ten approval-only covers and five front/back pairs at '+out);
