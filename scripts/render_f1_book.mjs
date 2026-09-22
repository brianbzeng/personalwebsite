import { chromium } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
const out=fileURLToPath(new URL('../public/books/f1/',import.meta.url));
const browser=await chromium.launch({headless:true});
try {
 const page=await browser.newPage({viewport:{width:620,height:780},deviceScaleFactor:1});
 await page.goto('http://127.0.0.1:3000/books/f1/layout.html');
 await page.waitForFunction(()=>document.body.dataset.ready||document.body.dataset.error);
 const error=await page.getAttribute('body','data-error');if(error)throw new Error(error);
 const book=await page.evaluate(()=>window.bookProof);
 if(book.errors.length)throw new Error('Overflow on '+book.errors.join(','));
 await mkdir(out+'pages',{recursive:true});
 await writeFile(out+'book.json',JSON.stringify(book));
 for(let i=0;i<book.pages.length;i++){
   if(process.argv.includes('--title-only')&&i!==0)continue;
   await page.locator('.report-leaf').nth(i).screenshot({path:out+'pages/'+String(i).padStart(3,'0')+'.jpg',type:'jpeg',quality:94,scale:'css'});
   if(i%40===0)console.log('Rendered',i+1,'/',book.pages.length);
 }
 console.log('Complete:',book.pages.length,'pages. No overflowing pages.');
} finally {await browser.close();}
