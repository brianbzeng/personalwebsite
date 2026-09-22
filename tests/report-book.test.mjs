import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url),read=p=>readFileSync(new URL(p,root),'utf8');
const book=JSON.parse(read('public/books/f1/book.json')),source=JSON.parse(read('public/books/f1/source.json'));
test('complete report has all chapters, figures, appendix rows and page assets',()=>{
 assert.equal(book.chapters.length,12);assert.equal(book.figures.length,9);assert.deepEqual(book.errors,[]);
 assert.deepEqual(book.tables.map(t=>t.rows),[5,2,4,7,9,4,5,3,418]);
 assert.equal(source.blocks.filter(b=>b.table===9).length,418);
 const html=book.pages.map(p=>p.html).join(' ');
 for(let i=1;i<=418;i++)assert.ok(html.includes(`Decision ${i} / 418`));
 assert.ok(html.includes('complete 920-row source audit'));assert.ok(html.includes('Reproduction notes'));
 assert.equal(book.pages.length%2,0);
 for(let i=0;i<book.pages.length;i++)assert.ok(existsSync(new URL(`public/books/f1/pages/${String(i).padStart(3,'0')}.jpg`,root)));
});
test('figures preserve original color assets and each occupy one page',()=>{
 assert.deepEqual(book.figures.map(f=>f.number),['2.1','3.1','3.2','4.1','4.2','5.1','6.1','7.1','8.1']);
 for(const figure of book.figures){
  assert.equal(createHash('sha256').update(readFileSync(new URL('public'+figure.src,root))).digest('hex'),figure.sha256);
  assert.equal(book.pages.filter(p=>p.figure===figure.number).length,1);
  assert.ok(!book.pages.some(p=>p.html.includes('figure-panorama')));
 }
});
test('contents and source fragments resolve to bounded book pages',()=>{
 for(const chapter of book.chapters)assert.ok(book.anchors[chapter.section]>=0&&book.anchors[chapter.section]<book.pages.length);
 for(const p of book.pages)for(const match of p.html.matchAll(/data-page="(\d+)"/g))assert.ok(Number(match[1])<book.pages.length);
 assert.ok(book.anchors['conclusion-tldr']>=0);
});
test('compact figures keep following prose accessible and avoid centered filler',()=>{
 assert.ok(book.pages.filter(p=>p.kind==='figure'&&p.html.includes('report-block')).length>=6);
 assert.doesNotMatch(read('public/books/f1/page.css'),/\.figure-image[^}]*align-items:center/);
 assert.match(read('app/components/ReportBookOverlay.tsx'),/leaf\(book.pages\[expanded\],expanded\)/);
 assert.doesNotMatch(read('app/components/ReportBookOverlay.tsx'),/className="report-figure-hit"/);
});
