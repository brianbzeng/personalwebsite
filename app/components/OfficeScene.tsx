import Link from "next/link";

export default function OfficeScene() {
  return (
    <main className="office-page" id="top">
      <header className="scene-nav" aria-label="Site navigation">
        <Link className="scene-brand" href="/" aria-label="Brian Zeng home">
          <span className="brand-pixel">BZ</span>
          <span className="brand-copy">NEON CABINET / 01</span>
        </Link>
        <div className="scene-nav-actions">
          <Link href="/projects">PROJECTS <span aria-hidden="true">↗</span></Link>
          <Link href="/about">INFO DESK <span aria-hidden="true">↗</span></Link>
        </div>
      </header>

      <section className="office-stage" aria-labelledby="office-title">
        <div className="office-intro">
          <p className="pixel-kicker">POINT / CLICK / EXPLORE</p>
          <h1 id="office-title">Brian Zeng<span>.</span></h1>
          <p className="office-deck">
            Data, software, and models built to turn noisy signals into useful decisions.
          </p>
          <p className="office-hint"><span className="hint-dot" /> Start with the glowing objects.</p>
        </div>

        <div className="diorama" aria-label="Interactive office diorama">
          <div className="diorama-sky" aria-hidden="true">
            <span className="scanline scanline-one" />
            <span className="scanline scanline-two" />
            <span className="pixel-star star-one" />
            <span className="pixel-star star-two" />
            <span className="pixel-star star-three" />
          </div>
          <div className="office-window" aria-hidden="true">
            <div className="window-sky" />
            <div className="window-city"><i /><i /><i /><i /><i /></div>
            <span className="window-label">OAKLAND / 37.8044° N</span>
          </div>
          <div className="office-poster" aria-hidden="true">
            <span>MAKE<br />USEFUL<br />THINGS</span>
            <i>{"///"}</i>
          </div>
          <div className="wall-console" aria-hidden="true">
            <span>SYS / BZ-2026</span>
            <b>ONLINE</b>
            <i />
          </div>

          <div className="desk-shadow" aria-hidden="true" />
          <div className="desk" aria-hidden="true">
            <div className="desk-top" />
            <div className="desk-front" />
            <div className="desk-leg desk-leg-left" />
            <div className="desk-leg desk-leg-right" />
          </div>

          <div className="monitor-object" aria-hidden="true">
            <div className="monitor-screen">
              <span className="monitor-bar">/ ABOUT.BZ</span>
              <strong>OPEN<br />INFO<br />DESK</strong>
              <span className="monitor-cursor">_</span>
            </div>
            <div className="monitor-neck" />
            <div className="monitor-base" />
          </div>
          <Link className="scene-hotspot hotspot-desktop" href="/about" aria-label="Open Brian's information desk">
            <span className="hotspot-ring" />
            <span className="hotspot-label">INFO DESK <b>↗</b></span>
          </Link>

          <div className="record-player-object" aria-hidden="true">
            <div className="player-lid"><span /></div>
            <div className="player-body">
              <div className="player-platter"><i /></div>
              <div className="player-arm"><i /></div>
              <span className="player-display">PLAY / 05</span>
            </div>
            <div className="player-feet"><i /><i /></div>
          </div>
          <Link className="scene-hotspot hotspot-player" href="/projects" aria-label="Enter the project record room">
            <span className="hotspot-ring" />
            <span className="hotspot-label">PROJECT ROOM <b>↗</b></span>
          </Link>

          <div className="desk-lamp" aria-hidden="true"><span /><i /><b /></div>
          <div className="plant" aria-hidden="true"><span /><i /><b /><em /></div>
          <div className="desk-items" aria-hidden="true"><i /><i /><i /></div>
        </div>

        <div className="office-footer-note">
          <span>INTERACTIVE PORTFOLIO</span>
          <span>USE TAB TO NAVIGATE</span>
          <span>© BZ / 2026</span>
        </div>
      </section>
    </main>
  );
}
