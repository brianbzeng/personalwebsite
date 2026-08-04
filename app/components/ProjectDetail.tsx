"use client";

import Link from "next/link";
import { useEffect, useState, type CSSProperties } from "react";
import type { ProjectRecord } from "../data/projects";

export default function ProjectDetail({ project }: { project: ProjectRecord }) {
  const [flipped, setFlipped] = useState(false);

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const timer = window.setTimeout(() => setFlipped(true), reduced ? 0 : 650);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <main className="detail-page">
      <header className="scene-nav detail-nav" aria-label="Project detail navigation">
        <Link className="scene-brand" href="/projects" aria-label="Back to project room">
          <span className="brand-pixel">BZ</span>
          <span className="brand-copy">PROJECT RECORD / {project.number}</span>
        </Link>
        <div className="scene-nav-actions">
          <Link href="/projects">PROJECT ROOM <span aria-hidden="true">↗</span></Link>
          <Link href="/about">INFO DESK <span aria-hidden="true">↗</span></Link>
        </div>
      </header>

      <section className="detail-stage" aria-labelledby="detail-title">
        <div className="detail-ambient" aria-hidden="true"><span /><span /><span /></div>
        <p className="detail-kicker">{project.category} / {project.year}</p>

        <div className={`record-detail ${flipped ? "is-flipped" : ""}`} style={{ "--record-accent": project.accent } as CSSProperties}>
          <article className="detail-face detail-front" aria-hidden={flipped}>
            <div className="detail-front-art">
              <span className="detail-front-grid" aria-hidden="true" />
              <span className="detail-front-index">{project.number}</span>
              <span className="detail-front-mark" aria-hidden="true"><i /><b /></span>
              <span className="detail-front-label">BZ / FIELD NOTES</span>
            </div>
            <div className="detail-front-copy">
              <p>NOW SPINNING</p>
              <h1 id="detail-title">{project.title}</h1>
              <span>{project.shortLabel}</span>
            </div>
          </article>

          <article className="detail-face detail-back" aria-hidden={!flipped}>
            <div className="detail-back-head">
              <div>
                <p className="pixel-kicker">{project.number} / CASE STUDY</p>
                <h1>{project.title}</h1>
              </div>
              <button className="flip-control" type="button" onClick={() => setFlipped((current) => !current)} aria-label="Flip record back to its cover">
                FLIP BACK <span aria-hidden="true">↻</span>
              </button>
            </div>
            <div className="detail-back-grid">
              <div className="detail-summary">
                <p className="detail-label">SUMMARY</p>
                <p className="detail-summary-copy">{project.summary}</p>
                <p className="detail-description">{project.description}</p>
                <div className="detail-links">
                  <a href={project.liveUrl} target="_blank" rel="noreferrer">Open live project <span aria-hidden="true">↗</span></a>
                  <a href={project.githubUrl} target="_blank" rel="noreferrer">View source <span aria-hidden="true">↗</span></a>
                </div>
              </div>
              <div className="detail-facts">
                <div><p className="detail-label">ROLE</p><p>{project.role}</p></div>
                <div><p className="detail-label">STACK</p><ul>{project.stack.map((item) => <li key={item}>{item}</li>)}</ul></div>
                <div><p className="detail-label">PROOF POINTS</p><ul>{project.outcomes.map((item) => <li key={item}>{item}</li>)}</ul></div>
              </div>
            </div>
            <div className="detail-notes-grid">
              <div><p className="detail-label">LEARNINGS</p><ul>{project.learnings.map((item) => <li key={item}>{item}</li>)}</ul></div>
              <div><p className="detail-label">NEXT ADDITIONS</p><ul>{project.futureAdditions.map((item) => <li key={item}>{item}</li>)}</ul></div>
            </div>
          </article>
        </div>

        <div className="detail-actions">
          <Link className="outline-control" href="/projects">← Back to records</Link>
          <span>{flipped ? "CASE STUDY SIDE" : "LOADING RECORD"}</span>
        </div>
      </section>
    </main>
  );
}
