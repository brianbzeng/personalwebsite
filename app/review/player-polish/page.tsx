'use client';
import { useState } from 'react';
import BookshelfExperience from '../../components/BookshelfExperience';
import '../../components/cinematicRoom.css';
import '../shelf-motion/review.css';

/** Staging for the disc polish: the vinyl surfaces ride the player's white
    sweep band and carry a soft radial sheen. Review only — not promoted. */
export default function PlayerPolishReview() {
  const [take, setTake] = useState(0);
  return <>
    <BookshelfExperience key={take} review motion initialCubby={1} onExit={() => { window.location.href = '/'; }} />
    <nav className="motion-review-toolbar" aria-label="Disc polish staging">
      <span>Player disc polish · sweep + radial sheen</span>
      <button onClick={() => setTake(value => value + 1)}>Reset preview</button>
    </nav>
  </>;
}
