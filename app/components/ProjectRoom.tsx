"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type CSSProperties } from "react";
import { PROJECTS } from "../data/projects";

type SpillPhase = "shelf" | "spilling" | "spilled";

function playTone(enabled: boolean, type: "click" | "spill" | "flip") {
  if (!enabled || typeof window === "undefined") return;
  const AudioContextClass = window.AudioContext
    || (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioContextClass) return;

  const context = new AudioContextClass();
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  const settings = {
    click: { start: 280, end: 520, duration: 0.08 },
    spill: { start: 120, end: 260, duration: 0.32 },
    flip: { start: 420, end: 180, duration: 0.18 },
  }[type];

  oscillator.type = type === "spill" ? "triangle" : "square";
  oscillator.frequency.setValueAtTime(settings.start, context.currentTime);
  oscillator.frequency.exponentialRampToValueAtTime(settings.end, context.currentTime + settings.duration);
  gain.gain.setValueAtTime(0.0001, context.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.035, context.currentTime + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + settings.duration);
  oscillator.connect(gain);
  gain.connect(context.destination);
  oscillator.start();
  oscillator.stop(context.currentTime + settings.duration + 0.02);
  oscillator.addEventListener("ended", () => void context.close(), { once: true });
}

export default function ProjectRoom() {
  const [phase, setPhase] = useState<SpillPhase>("shelf");
  const [soundEnabled, setSoundEnabled] = useState(false);
  const timer = useRef<number | null>(null);

  useEffect(() => () => {
    if (timer.current) window.clearTimeout(timer.current);
  }, []);

  function spillRecords() {
    if (phase !== "shelf" && phase !== "spilled") return;
    setPhase("spilling");
    playTone(soundEnabled, "spill");
    timer.current = window.setTimeout(() => setPhase("spilled"), 1750);
  }

  function replaySpill() {
    setPhase("shelf");
    window.requestAnimationFrame(() => spillRecords());
  }

  return (
    <main className="project-page">
      <header className="scene-nav project-nav" aria-label="Project room navigation">
        <Link className="scene-brand" href="/" aria-label="Back to Brian's office">
          <span className="brand-pixel">BZ</span>
          <span className="brand-copy">PROJECT ROOM / 02</span>
        </Link>
        <div className="scene-nav-actions">
          <button
            className={`sound-toggle ${soundEnabled ? "is-on" : ""}`}
            type="button"
            onClick={() => setSoundEnabled((current) => !current)}
            aria-pressed={soundEnabled}
          >
            <span className="sound-bars" aria-hidden="true"><i /><i /><i /></span>
            SOUND {soundEnabled ? "ON" : "OFF"}
          </button>
          <Link href="/about">INFO DESK <span aria-hidden="true">↗</span></Link>
        </div>
      </header>

      <section className="project-stage" aria-labelledby="project-room-title">
        <div className="project-heading">
          <div>
            <p className="pixel-kicker">ARCHIVE / PROJECTS / 2026</p>
            <h1 id="project-room-title">The record room<span>.</span></h1>
          </div>
          <p className="project-instruction">
            {phase === "shelf" ? "The shelf is loaded. Tap the holder to release the records." : phase === "spilling" ? "Unpacking the archive..." : "Pick a record. Each one opens a full case study."}
          </p>
        </div>

        <div className={`record-room phase-${phase}`}>
          <div className="room-grid" aria-hidden="true" />
          <div className="room-sign" aria-hidden="true"><span>ARCHIVE</span><b>05</b></div>
          <div className="room-cable cable-one" aria-hidden="true" />
          <div className="room-cable cable-two" aria-hidden="true" />

          <button className="vinyl-holder" type="button" onClick={spillRecords} disabled={phase === "spilling"} aria-label="Tip the holder and spill the project records">
            <span className="holder-side holder-side-left" />
            <span className="holder-side holder-side-right" />
            <span className="holder-rail holder-rail-top" />
            <span className="holder-rail holder-rail-bottom" />
            <span className="holder-base" />
            <span className="holder-label">CLICK TO<br />UNLOAD</span>
            <span className="holder-records" aria-hidden="true">
              {PROJECTS.map((project, index) => <i key={project.slug} style={{ "--record-accent": project.accent, "--record-index": index } as CSSProperties} />)}
            </span>
          </button>

          <div className="record-line" aria-label="Project records">
            {PROJECTS.map((project, index) => (
              <Link
                className="record-card"
                href={`/projects/${project.slug}`}
                key={project.slug}
                style={{ "--record-accent": project.accent, "--record-index": index } as CSSProperties}
                onClick={() => playTone(soundEnabled, "click")}
                aria-label={`Open ${project.title} case study`}
              >
                <span className="record-shadow" aria-hidden="true" />
                <span className="record-sleeve">
                  <span className="record-number">{project.number}</span>
                  <span className="record-icon" aria-hidden="true"><i /><b /></span>
                  <strong>{project.title}</strong>
                  <small>{project.shortLabel}</small>
                </span>
                <span className="record-spine" aria-hidden="true" />
              </Link>
            ))}
          </div>

          <div className="mobile-arcade-menu" aria-label="Mobile project menu">
            {PROJECTS.map((project) => (
              <Link className="mobile-record" href={`/projects/${project.slug}`} key={project.slug}>
                <span className="mobile-record-number" style={{ color: project.accent }}>{project.number}</span>
                <span><strong>{project.title}</strong><small>{project.category}</small></span>
                <b aria-hidden="true">↗</b>
              </Link>
            ))}
          </div>

          <div className="room-status" aria-live="polite">
            <span className="status-pip" />
            {phase === "spilled" ? "ARCHIVE READY" : phase === "spilling" ? "SEQUENCE ACTIVE" : "HOLDER LOCKED"}
          </div>
        </div>

        <div className="project-controls">
          <Link className="outline-control" href="/">← Back to office</Link>
          <div className="control-group">
            <button className="outline-control" type="button" onClick={replaySpill} disabled={phase === "spilling"}>↻ Replay spill</button>
            <span className="project-count">{String(PROJECTS.length).padStart(2, "0")} records / {String(PROJECTS.length).padStart(2, "0")} projects</span>
          </div>
        </div>
      </section>
    </main>
  );
}
