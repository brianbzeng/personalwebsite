"use client";

import { useState } from "react";
import { calendarMonth, pacificClock } from "./desktopState";

export default function DesktopCalendar({ now }: { now: Date }) {
  const clock = pacificClock(now);
  const [year, month] = clock.dayKey.split("-").map(Number);
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState(clock.dayKey);
  const viewed = new Date(Date.UTC(year, month - 1 + offset, 1));
  const title = new Intl.DateTimeFormat("en-US", { month: "long", year: "numeric", timeZone: "UTC" }).format(viewed);
  return <section className="win-flyout win-calendar" aria-label="Calendar">
    <header><p>{clock.fullDate}</p><span>{clock.time} {clock.zone}</span></header>
    <div className="win-calendar-heading"><button type="button" title="Go to today" onClick={() => { setOffset(0); setSelected(clock.dayKey); }}>{title}</button><div>
      <button type="button" aria-label="Previous month" onClick={() => setOffset(offset - 1)}><svg viewBox="0 0 20 20" aria-hidden="true"><path d="m5 12.5 5-5 5 5" /></svg></button>
      <button type="button" aria-label="Next month" onClick={() => setOffset(offset + 1)}><svg viewBox="0 0 20 20" aria-hidden="true"><path d="m5 7.5 5 5 5-5" /></svg></button>
    </div></div>
    <div className="win-calendar-grid">
      {["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"].map((day) => <span key={day}>{day}</span>)}
      {calendarMonth(viewed.getUTCFullYear(), viewed.getUTCMonth()).map((day) => <button type="button" key={day.key} aria-label={day.key} aria-current={day.key === clock.dayKey ? "date" : undefined} aria-pressed={day.key === selected}
        className={`${day.current ? "" : "is-other-month"} ${day.key === clock.dayKey ? "is-today" : ""} ${day.key === selected ? "is-selected" : ""}`} onClick={() => setSelected(day.key)}>{day.date}</button>)}
    </div>
    <footer>Pacific Time · {clock.zone}</footer>
  </section>;
}
