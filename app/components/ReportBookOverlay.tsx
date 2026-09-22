"use client";
import { useEffect, useRef, useState } from 'react';
import { loadReportBook, type ReportBook, type ReportPage } from './reportBook';
import type { BookLayout } from './ShelfScene';
import './reportBook.css';

export default function ReportBookOverlay({ spread, layout, busy, onJump, onLoad }: { spread: number; layout: BookLayout | null; busy: boolean; onJump: (page: number) => void; onLoad: (book: ReportBook) => void }) {
 const [book,setBook]=useState<ReportBook|null>(null),[expanded,setExpanded]=useState<number|null>(null),[figure,setFigure]=useState<ReportPage|null>(null);
 const dialog=useRef<HTMLDialogElement>(null), close=useRef<HTMLButtonElement>(null), previousFocus=useRef<HTMLElement|null>(null);
 useEffect(()=>{let live=true;void loadReportBook().then(b=>{if(live){setBook(b);onLoad(b);}});return()=>{live=false;};},[]); // Stable content, independently editable from Blender.
 const modal=expanded!==null||figure!==null;
 useEffect(()=>{if(modal){previousFocus.current=document.activeElement as HTMLElement;dialog.current?.showModal();close.current?.focus();}else{dialog.current?.close();previousFocus.current?.focus();}},[modal]);
 function link(event: React.MouseEvent, page: ReportPage) {
   const a=(event.target as Element).closest('a');
   if(a?.hasAttribute('data-page')){event.preventDefault();const target=Number(a.getAttribute('data-page'));if(expanded!==null)setExpanded(target);else onJump(target);return;}
   if(!a&&(event.target as Element).closest('figure')){setFigure(page);}
 }
 if(!book)return null;
 const leaf=(p:ReportPage,i:number)=> <article className="report-leaf" onClick={event=>link(event,p)} onKeyDown={event=>{if((event.key==='Enter'||event.key===' ')&&(event.target as Element).closest('figure')){event.preventDefault();setFigure(p);}}}><header className="report-running">{p.chapter}</header><div className="report-body" dangerouslySetInnerHTML={{__html:p.html}}/><footer className="report-folio"><span>{i+1}</span></footer></article>;
 return <>
   {layout && layout.visible && !busy && <div className="report-surface" aria-label="Open report">
     {[layout.left,layout.right].map((box,side)=>{const i=spread*2+side,p=book.pages[i];return p&&<div key={side} className="report-position" style={{left:box.x+'%',top:box.y+'%',width:box.width+'%',height:box.height+'%'}}><div className="report-scale">{leaf(p,i)}</div></div>;})}
   </div>}
   <div className="report-navigation"><button disabled={busy||spread===0} onClick={()=>onJump(0)}>First page</button><button disabled={busy} onClick={()=>onJump(book.contentsPage)}>Contents</button><button disabled={busy||spread===Math.ceil(book.pages.length/2)-1} onClick={()=>onJump(book.pages.length-1)}>Last page</button><button disabled={busy} onClick={()=>setExpanded(spread*2)}>Read larger</button></div>
   <dialog ref={dialog} className="report-dialog" onCancel={event=>{event.preventDefault();setExpanded(null);setFigure(null);}} onKeyDown={event=>{if(event.key==='Escape')event.stopPropagation();}}>
     <div className="report-dialog-bar"><span>{figure?`Figure ${figure.figure}`:book.title}</span><button ref={close} onClick={()=>{if(figure&&expanded!==null)setFigure(null);else{setExpanded(null);setFigure(null);}}}>Close</button></div>
     {figure?<div className="report-figure-expanded"><img src={figure.src} alt={figure.alt}/><p>{figure.alt}</p><div dangerouslySetInnerHTML={{__html:figure.caption??''}}/></div>:expanded!==null&&<>
       <div className="report-reading-page">{leaf(book.pages[expanded],expanded)}</div>
       <nav className="report-reader-nav"><button disabled={expanded===0} onClick={()=>setExpanded(Math.max(0,expanded-1))}>Previous page</button><button onClick={()=>setExpanded(book.contentsPage)}>Contents</button><form onSubmit={event=>{event.preventDefault();const value=Number(new FormData(event.currentTarget).get('page'));if(Number.isInteger(value))setExpanded(Math.max(0,Math.min(book.pages.length-1,value-1)));}}><label>Page <input key={expanded} aria-label="Page number" name="page" type="number" min={1} max={book.pages.length} defaultValue={expanded+1}/></label><span> / {book.pages.length}</span><button>Go</button></form><button disabled={expanded===book.pages.length-1} onClick={()=>setExpanded(Math.min(book.pages.length-1,expanded+1))}>Next page</button><button onClick={()=>{onJump(expanded);setExpanded(null);}}>View in book</button></nav>
     </>}
   </dialog>
 </>;
}
