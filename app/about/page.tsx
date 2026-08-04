import type { Metadata } from "next";
import Link from "next/link";
import GitHubPulse from "../components/GitHubPulse";

export const metadata: Metadata = {
  title: "Info Desk / Brian Zeng",
  description: "About, experience, GitHub Pulse, and contact links for Brian Zeng.",
};

export default function AboutPage() {
  return (
    <main className="about-page">
      <header className="scene-nav" aria-label="Information desk navigation">
        <Link className="scene-brand" href="/" aria-label="Back to Brian's office">
          <span className="brand-pixel">BZ</span>
          <span className="brand-copy">INFO DESK / 03</span>
        </Link>
        <div className="scene-nav-actions">
          <Link href="/projects">PROJECTS <span aria-hidden="true">↗</span></Link>
          <Link href="/">OFFICE <span aria-hidden="true">↗</span></Link>
        </div>
      </header>

      <section className="about-stage" aria-labelledby="about-title">
        <div className="about-copy">
          <p className="pixel-kicker">ABOUT / EXPERIENCE / CONTACT</p>
          <h1 id="about-title">Inside the desk<span>.</span></h1>
          <p className="about-lead">I’m Brian, a data-minded builder working across analysis, software, and applied AI.</p>
          <p className="about-body">I like projects where the interesting part is not only making a model work, but making the result understandable, useful, and durable enough to leave the notebook.</p>
          <div className="about-actions">
            <a className="primary-control" href="mailto:bzeng0000@gmail.com">Start a conversation <span aria-hidden="true">↗</span></a>
            <a className="outline-control" href="https://github.com/brianbzeng" target="_blank" rel="noreferrer">GitHub <span aria-hidden="true">↗</span></a>
          </div>
        </div>

        <div className="info-console">
          <div className="console-top"><span>WORKSTATION / BZ-01</span><b><i /> ONLINE</b></div>
          <div className="console-grid">
            <div className="console-panel console-experience">
              <p className="detail-label">CURRENT FOCUS</p>
              <h2>Data analysis<br />Data science<br />Software</h2>
              <div className="console-rule" />
              <p className="detail-label">BASED IN</p>
              <p>Oakland, California</p>
              <p className="detail-label console-spaced">EDUCATION</p>
              <p>UC Santa Barbara<br />B.S. Probability &amp; Statistics<br />with Data Science / 2026</p>
            </div>
            <div className="console-panel console-links">
              <p className="detail-label">OPEN CHANNELS</p>
              <a href="mailto:bzeng0000@gmail.com"><span>EMAIL</span><b>bzeng0000@gmail.com ↗</b></a>
              <a href="https://www.linkedin.com/in/brianbzeng" target="_blank" rel="noreferrer"><span>LINKEDIN</span><b>/in/brianbzeng ↗</b></a>
              <a href="https://github.com/brianbzeng" target="_blank" rel="noreferrer"><span>GITHUB</span><b>@brianbzeng ↗</b></a>
              <a href="/contact"><span>RESUME / CONTACT</span><b>OPEN ROUTE ↗</b></a>
            </div>
          </div>
        </div>
      </section>

      <section className="pulse-stage" aria-labelledby="pulse-title">
        <div className="pulse-heading">
          <p className="pixel-kicker">LIVE SYSTEM MONITOR</p>
          <h2 id="pulse-title">GitHub Pulse<span>.</span></h2>
          <p>Recent public activity from the repositories behind the projects.</p>
        </div>
        <GitHubPulse />
      </section>

      <footer className="info-footer">
        <span>BRIAN ZENG / OAKLAND, CA</span>
        <Link href="/">RETURN TO OFFICE ↑</Link>
      </footer>
    </main>
  );
}
