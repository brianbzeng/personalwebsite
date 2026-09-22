/* Measured pagination at the exact texture dimensions. No content is discarded. */
(async () => {
 const source = await (await fetch('source.json')).json();
 const root = document.querySelector('#proof'), pages = [], anchors = {};
 let current = null, header = 'Introduction';
 function page(kind='text') {
   const leaf = document.createElement('article'); leaf.className='report-leaf';
   leaf.innerHTML='<header class="report-running"></header><div class="report-body"></div><footer class="report-folio"><span></span></footer>';
   leaf.querySelector('header').textContent=header;
   root.appendChild(leaf);
   const item={kind, chapter:header, html:'', anchors:[], element:leaf, body:leaf.querySelector('.report-body')};
   pages.push(item);current=item;return item;
 }
 function overflow() { return current.body.scrollHeight > current.body.clientHeight + 1; }
 function add(html, block) {
   if(!current)page();
   const wrap=document.createElement('div');wrap.className='report-block';wrap.innerHTML=html;current.body.appendChild(wrap);
   if(overflow()&&current.kind==='figure'&&wrap.firstElementChild?.tagName==='P'){
     const original=wrap.firstElementChild.cloneNode(true),text=original.textContent;
     const available=current.body.getBoundingClientRect().bottom-wrap.getBoundingClientRect().top;
     // Fill usable space after a figure with at least four lines, retaining
     // inline markup and all words, rather than stranding the whole paragraph.
     if(available>=150&&text.length>220){
       const nodes=[],walker=document.createTreeWalker(original,NodeFilter.SHOW_TEXT);while(walker.nextNode())nodes.push(walker.currentNode);
       const point=offset=>{for(const node of nodes){if(offset<=node.length)return[node,offset];offset-=node.length;}return[original,original.childNodes.length];};
       function segment(start,end){const range=document.createRange();range.setStart(...point(start));range.setEnd(...point(end));const p=original.cloneNode(false);if(start)p.removeAttribute('id');p.appendChild(range.cloneContents());return p.outerHTML;}
       const cuts=[...text.matchAll(/\s+/g)].map(m=>m.index+m[0].length).filter(n=>n>100&&n<text.length-100);
       let low=0,high=cuts.length-1,best=-1;
       while(low<=high){const mid=(low+high)>>1;wrap.innerHTML=segment(0,cuts[mid]);if(overflow())high=mid-1;else{best=mid;low=mid+1;}}
       if(best>=0){const split=cuts[best];wrap.innerHTML=segment(0,split);for(const id of block.anchors||[])if(!(id in anchors)){anchors[id]=pages.length-1;current.anchors.push(id);}page();add(segment(split,text.length),{...block,anchors:[]});return;}
       wrap.innerHTML=html;
     }
   }
   if(overflow() && current.body.children.length>1){
     const previous=wrap.previousElementSibling,heading=previous?.firstElementChild;
     const carry=heading&&['H3','H4'].includes(heading.tagName)?previous:null,old=current;
     wrap.remove();if(carry)carry.remove();page();
     if(carry){current.body.appendChild(carry);for(const node of carry.querySelectorAll('[id]')){anchors[node.id]=pages.length-1;old.anchors=old.anchors.filter(id=>id!==node.id);current.anchors.push(node.id);}}
     current.body.appendChild(wrap);
   }
   if(overflow()) {
     // Split exceptionally long entries at field boundaries; repeat their identity.
     const fields=wrap.querySelectorAll('.table-field');
     if(fields.length>1){const label=wrap.querySelector('.entry-label').outerHTML;wrap.remove();for(const field of fields)add(`<section class="table-entry">${label}<dl>${field.outerHTML}</dl></section>`,block);return;}
     // Long paragraphs retain inline markup and links by moving whole sentences.
     const content=wrap.firstElementChild;
     if(content && content.tagName==='P') {
       const range=document.createRange(), textNodes=[];const walker=document.createTreeWalker(content,NodeFilter.SHOW_TEXT);while(walker.nextNode())textNodes.push(walker.currentNode);
       const total=content.textContent.length;
       let remaining=Math.floor(total/2), point;
       for(const node of textNodes){if(remaining<node.length){const cut=node.textContent.lastIndexOf(' ',remaining);point=[node,Math.max(1,cut)];break;}remaining-=node.length;}
       if(point){range.setStart(...point);range.setEnd(content,content.childNodes.length);const tail=content.cloneNode(false);tail.appendChild(range.extractContents());const first=content.outerHTML;wrap.remove();add(first,block);page();add(tail.outerHTML,{...block,anchors:[]});return;}
     }
     throw new Error('Oversized unsplittable block: '+wrap.textContent.slice(0,100));
   }
   for(const id of block.anchors||[])if(!(id in anchors)){anchors[id]=pages.length-1;current.anchors.push(id);}
 }
 header='Brian Zeng';page('title');current.body.innerHTML=`<div class="title-page"><p class="chapter-kicker">Data science studies · Volume 01</p><h1>${source.title}</h1><p class="subtitle">${source.subtitle}</p><p class="repository"><a href="https://github.com/brianbzeng/f1-stewarding-analysis" target="_blank" rel="noopener noreferrer">GitHub · f1-stewarding-analysis</a></p><p class="author">${source.author}</p><p class="source"><a href="mailto:bzeng0000@gmail.com">bzeng0000@gmail.com</a><br><a href="https://brianbzeng.com">brianbzeng.com</a></p></div>`;
 current=null;header='Introduction';
 let contentsInserted=false;
 const tocPages=[];
 for(let bi=0;bi<source.blocks.length;bi++) {
   const b=source.blocks[bi];
   if(b.kind==='chapter') {
     if(!contentsInserted){header='Contents';tocPages.push(page('contents'),page('contents'));current=null;contentsInserted=true;}
     header=b.chapter;current=null;page();anchors[b.section]=pages.length-1;
   }
   if(b.kind==='figure'){
     current=null;
     const p=page('figure');p.figure=b.figure;p.src=b.src;p.caption=b.caption;p.alt=b.alt;
     p.body.innerHTML=`<figure role="button" tabindex="0" aria-label="Enlarge Figure ${b.figure}"><div class="figure-label">Figure ${b.figure}</div><div class="figure-image"><img src="${b.src}" alt="${b.alt.replaceAll('"','&quot;')}"></div><figcaption>${b.caption}<div class="figure-detail">Select figure to view at full size</div></figcaption></figure>`;
     // Measure the real image before letting following prose use the remaining
     // page; never reserve a full-height centered figure or split its artwork.
     await p.body.querySelector('img').decode();
     if(overflow())throw new Error('Figure exceeds one page: '+b.figure);
     continue;
   }
   if(b.kind==='heading' && current){const last=current.body.lastElementChild;const used=last?last.getBoundingClientRect().bottom-current.body.getBoundingClientRect().top:0;if(current.body.clientHeight-used<170)current=null;}
   add(b.html,b);
 }
 const toc=[{title:'Introduction',section:'introduction'},...source.chapters.map(c=>({title:(c.number?c.number+'. ':'')+c.title,section:c.section})),{title:'Conclusion · TL;DR',section:'conclusion-tldr'}];
 anchors.introduction=1;
 for(let i=0;i<toc.length;i++){
   const p=tocPages[i<7?0:1];if(!p.body.innerHTML)p.body.innerHTML='<h2>Contents'+(i>=7?' · continued':'')+'</h2>';
   const entry=toc[i],target=anchors[entry.section];if(target===undefined)throw new Error('Unresolved contents '+entry.section);
   p.body.insertAdjacentHTML('beforeend',`<a class="toc-entry" href="#${entry.section}" data-page="${target}"><span>${entry.title}</span><span class="toc-number">${target+1}</span></a>`);
 }
 // Source fragment links become book page destinations, never dead in-page anchors.
 for(const p of pages)for(const a of p.body.querySelectorAll('a[href^="#"]')){const key=decodeURIComponent(a.getAttribute('href').slice(1));if(key in anchors)a.dataset.page=anchors[key];else a.href=source.source+a.getAttribute('href');}
 if(pages.length%2){header='Colophon';page('colophon');current.body.innerHTML=`<h2>End of report</h2><p>${source.title}</p><p>Brian Zeng</p><p><a href="${source.source}">Original report</a><br><a href="https://github.com/brianbzeng/f1-stewarding-analysis">Code and research materials</a></p>`;}
 for(let i=0;i<pages.length;i++){const p=pages[i];p.element.dataset.page=i;p.element.querySelector('footer span:last-child').textContent=i+1;p.html=p.body.innerHTML;delete p.body;delete p.element;}
 await Promise.all([...document.images].map(img=>img.decode()));await document.fonts.ready;
 const errors=[...root.children].filter(el=>el.querySelector('.report-body').scrollHeight>el.querySelector('.report-body').clientHeight+1).map(el=>Number(el.dataset.page));
 window.bookProof={...source,blocks:undefined,pages,anchors,contentsPage:pages.findIndex(p=>p.kind==='contents'),width:600,height:750,errors};
 document.body.dataset.ready='true';
})().catch(error=>{document.body.dataset.error=error.message;console.error(error);});
