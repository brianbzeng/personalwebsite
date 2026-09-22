import {chromium} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
const out='C:/Users/Brian Zeng/Documents/Codex/2026-08-25/realtime-voice-chat-6/book-feedback-frames/';
await mkdir(out,{recursive:true});
const browser=await chromium.launch({headless:true});
try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 // Deterministic RAF clock only in this isolated test page, not application code.
 await page.addInitScript(()=>{let now=0,id=0;const queue=new Map();performance.now=()=>now;window.requestAnimationFrame=callback=>{queue.set(++id,callback);return id;};window.cancelAnimationFrame=id=>queue.delete(id);window.qaStep=ms=>{now+=ms;const callbacks=[...queue.values()];queue.clear();callbacks.forEach(callback=>callback(now));};});
 const advance=async ms=>{for(let n=0;n<ms;n+=16)await page.evaluate(()=>window.qaStep(16));};
 await page.goto('http://127.0.0.1:3000/review/report-book');
 await page.waitForFunction(()=>document.querySelector('canvas'),null,{polling:100});
 await page.waitForTimeout(2000);
 await page.getByRole('button',{name:'Data science report',exact:true}).click({force:true});await advance(1800);
 await page.getByRole('button',{name:'Open book',exact:true}).click({force:true});await advance(1800);
 await page.getByRole('button',{name:'Next spread',exact:true}).hover({force:true});await advance(600);
 await page.screenshot({path:out+'controlled-peek.png'});
 await page.getByRole('button',{name:'Next spread',exact:true}).click({force:true});
 await new Promise(resolve=>setTimeout(resolve,500));
 for(let i=0;i<10;i++){await advance(90);await page.screenshot({path:out+'controlled-v3-'+i+'.png'});}
 await advance(500);
 await page.getByRole('button',{name:'Previous spread',exact:true}).hover({force:true});await advance(600);
 await page.screenshot({path:out+'controlled-left-peek.png'});
 await page.getByRole('button',{name:'Previous spread',exact:true}).click({force:true});
 await new Promise(resolve=>setTimeout(resolve,500));
 for(let i=0;i<10;i++){await advance(90);await page.screenshot({path:out+'controlled-back-v3-'+i+'.png'});}
 await advance(500);
 console.log(await page.locator('.report-surface').innerText());
}finally{await browser.close();}
