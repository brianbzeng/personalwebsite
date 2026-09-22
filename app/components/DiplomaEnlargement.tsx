"use client";
import {useRef} from 'react';

/** The original diploma artwork, rather than a magnified room screenshot. */
export default function DiplomaEnlargement(){
  const dialog=useRef<HTMLDialogElement>(null),trigger=useRef<HTMLButtonElement>(null);
  function close(){dialog.current?.close();trigger.current?.focus({preventScroll:true});}
  return <>
    <div className="diploma-hit-stage"><button ref={trigger} className="diploma-enlarge-target" aria-label="Enlarge diploma" onClick={()=>dialog.current?.showModal()} /></div>
    <dialog ref={dialog} className="diploma-lightbox" aria-label="Brian Zeng’s diploma" onCancel={event=>{event.preventDefault();close();}} onClick={event=>{if(event.target===event.currentTarget)close();}}>
      <button className="diploma-lightbox-close" onClick={close} autoFocus>Close</button>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/room/diploma-art.png" alt="University of California, Santa Barbara diploma: Brian Zeng, Bachelor of Science, Statistics and Data Science, June 12, 2026" />
    </dialog>
  </>;
}
