'use client';

import {useState} from 'react';

const clips=['idle','monitor-in','monitor-out','diploma-in','diploma-out','vinyl-in','vinyl-out','photos-in','photos-out','shelf-1-2','shelf-2-1'];

export default function ShelfAlignmentReview(){
  const [clip,setClip]=useState('idle');
  return <main style={{background:'#080808',color:'#eee',minHeight:'100dvh',fontFamily:'sans-serif'}}>
    <video key={clip} src={`/room/v163/${clip}.mp4`} poster="/room/v163/greeting.webp" autoPlay muted loop playsInline controls style={{width:'100%',height:'85dvh',objectFit:'contain'}} />
    <nav aria-label="Corrected animation previews" style={{display:'flex',gap:8,flexWrap:'wrap',padding:16}}>
      {clips.map(name=><button key={name} onClick={()=>setClip(name)} aria-pressed={clip===name}>{name}</button>)}
    </nav>
  </main>;
}
