"use client";
import {useState} from 'react';
import BookshelfExperience from '../../components/BookshelfExperience';
import '../../components/cinematicRoom.css';
import '../../components/mobileRoom.css';

export default function BookCueReview(){
  const [input,setInput]=useState<'mouse'|'touch'>('mouse');
  return <main className="cinematic-room" data-mobile-layout="true" data-viewport-fit="cover">
    <BookshelfExperience initialCubby={0} motion review coherentPhotos coherentBooks mobileLayout activityCues refinedCues cueFadeIn cueInput={input}
      onExit={()=>{window.location.href='/review/activity-cues';}}/>
    <div className="activity-cue-replay" style={{display:'flex',gap:10,alignItems:'center'}}>
      <label>Preview <select aria-label="Cue input preview" value={input} onChange={event=>{setInput(event.target.value as 'mouse'|'touch');window.dispatchEvent(new Event('bz-replay-cues'));}}>
        <option value="mouse">Mouse</option><option value="touch">Touch</option>
      </select></label>
      <button style={{background:'#333',color:'#eee',border:'1px solid #666',borderRadius:3,padding:'3px 6px'}} onClick={()=>window.dispatchEvent(new Event('bz-replay-cues'))}>Replay notes</button>
    </div>
  </main>;
}
