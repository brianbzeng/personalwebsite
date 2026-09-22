'use client';
import {useState} from 'react';
import BookshelfExperience from '../../components/BookshelfExperience';
import '../../components/cinematicRoom.css';
import './review.css';

export default function ShelfMotionReview(){
  const [view,setView]=useState<'records'|'book'>('records');
  const [take,setTake]=useState(0);
  return <>
    <BookshelfExperience key={`${view}-${take}`} review motion initialCubby={view==='records'?1:0} onExit={()=>{window.location.href='/';}}/>
    <nav className="motion-review-toolbar" aria-label="Animation staging">
      <span>Animation review · no automatic redirects</span>
      <button aria-pressed={view==='records'} onClick={()=>setView('records')}>Vinyl playback & returns</button>
      <button aria-pressed={view==='book'} onClick={()=>setView('book')}>Book closing</button>
      <button onClick={()=>setTake(value=>value+1)}>Reset preview</button>
    </nav>
  </>;
}
