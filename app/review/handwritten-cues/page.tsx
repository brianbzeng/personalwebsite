"use client";

import { useState } from "react";
import HandwrittenCue, { ManicLettering } from "../../components/HandwrittenCue";

export default function HandwrittenCuesReview() {
  const [paused, setPaused] = useState(false);
  return <main className="cue-review" data-paused={paused || undefined}>
    <header className="cue-review__header">
      <div>
        <p className="cue-review__eyebrow">Motion study · staging only</p>
        <h1>Manic, with a little variation.</h1>
        <p>The actual Manic font, with alternate forms for repeated letters. Existing controls stay until the notes are approved.</p>
      </div>
      <button type="button" onClick={() => setPaused(!paused)} aria-pressed={paused}>{paused ? "Resume loops" : "Pause loops"}</button>
    </header>
    <section className="cue-review__grid" aria-label="Handwritten cue previews">
      <figure className="cue-review__card">
        <div className="cue-review__scene">
          <svg className="cue-review__book" viewBox="0 0 360 280" aria-label="Sample open book" role="img">
            <path d="M8 20L179 29L352 20V264L181 270L8 264Z" fill="#191919" />
            <path d="M17 13Q93 8 179 25V258Q99 240 17 252Z" fill="#deded7" />
            <path d="M179 25Q264 8 343 13V252Q267 240 179 258Z" fill="#eaeae4" />
            <path d="M179 26V257" stroke="#9f9f99" strokeWidth="2" />
            <g stroke="#92928b" strokeWidth="2.2" opacity=".7">
              <path d="M35 70H135M35 85H151M35 100H147M35 115H148M35 130H126M35 165H143M35 180H151M35 195H143M35 210H125" />
              <path d="M205 60H319M205 75H312M205 90H316M205 105H295M205 140H316M205 155H318M205 170H306M205 185H311M205 200H286" />
            </g>
            <path d="M316 250Q328 230 343 226L338 250Z" fill="#bdbdb5" />
          </svg>
          <HandwrittenCue kind="swipe-right" className="cue-review__swipe" />
        </div>
        <figcaption><strong>Swipe Right</strong> · two different “i”s, entirely beside the book.</figcaption>
      </figure>
      <figure className="cue-review__card">
        <div className="cue-review__scene">
          <svg className="cue-review__vinyl" viewBox="0 0 340 300" aria-label="Sample record cover" role="img">
            <circle cx="212" cy="144" r="123" fill="#151515" stroke="#777" strokeWidth="1" />
            {[107, 96, 85, 73].map(radius => <circle key={radius} cx="212" cy="144" r={radius} fill="none" stroke="#555" strokeWidth="1" />)}
            <path d="M12 6H259V281H12Z" fill="#202020" stroke="#111" strokeWidth="5" />
            <path d="M23 17H248V270H23Z" fill="none" stroke="#909090" strokeWidth="1" />
            <circle cx="135" cy="135" r="34" fill="none" stroke="#ddd" strokeWidth="4" />
            <path d="M118 118L146 128L154 153L127 143Z" fill="none" stroke="#ddd" strokeWidth="3" />
          </svg>
          <HandwrittenCue kind="drag" className="cue-review__drag" />
        </div>
        <figcaption><strong>Drag</strong> · centered above the cover, with nothing covering the artwork.</figcaption>
      </figure>
    </section>
    <section className="cue-review__variants" aria-label="Repeated-letter sample">
      <svg viewBox="0 0 300 72" role="img" aria-label="Seventeen, with four distinct e variants"><ManicLettering text="seventeen" x={150} y={48} /></svg>
      <p>Four “e”s, four actual glyph variants. Other letters begin with the regular form; repeats advance through the three alternates.</p>
    </section>
    <p className="cue-review__footer">Only a pointing arrow’s tip may barely overlap an object; lettering and gesture loops stay clear. Once this style is approved, each floating note gets its own staging preview. Nothing is live yet.</p>
  </main>;
}
