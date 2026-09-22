"use client";
import {useEffect,useState} from 'react';

/** Thin projected edges from the actual Blender cards, not a hotspot box. */
export default function PolaroidPulse(){
  const [edges,setEdges]=useState<number[][][]>([]);
  useEffect(()=>{const controller=new AbortController();
    void fetch('/room/v157/polaroid-outlines.json',{signal:controller.signal}).then(r=>r.ok?r.json():[]).then(value=>setEdges(value as number[][][])).catch(()=>{});
    return()=>controller.abort();
  },[]);
  return <svg className="polaroid-room-pulse" viewBox="0 0 1920 1080" aria-hidden="true">
    <path d={edges.map(([a,b])=>`M${a[0]} ${a[1]}L${b[0]} ${b[1]}`).join('')} fill="none" stroke="white" strokeWidth="1.4" strokeLinejoin="round" strokeLinecap="round" />
  </svg>;
}
