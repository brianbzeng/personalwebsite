"use client";

import { useMemo, useState } from "react";

type Team = {
  id: string;
  name: string;
  short: string;
  current: number;
  color: string;
};

const TEAMS: Team[] = [
  { id: "mclaren", name: "McLaren", short: "MCL", current: 362, color: "#ff8700" },
  { id: "ferrari", name: "Ferrari", short: "FER", current: 306, color: "#e8002d" },
  { id: "mercedes", name: "Mercedes", short: "MER", current: 266, color: "#00a19b" },
  { id: "redbull", name: "Red Bull", short: "RBR", current: 253, color: "#3154c7" },
];

const PRESETS = {
  baseline: { mclaren: 29, ferrari: 25, mercedes: 21, redbull: 24 },
  challengers: { mclaren: 25, ferrari: 29, mercedes: 24, redbull: 27 },
  chaos: { mclaren: 22, ferrari: 30, mercedes: 28, redbull: 29 },
};

const apps = [
  {
    number: "01",
    eyebrow: "Sports analytics · Live app",
    title: "NBA Odds Predictor",
    domain: "nba.brianbzeng.com",
    url: "https://nba.brianbzeng.com",
    github: "https://github.com/brianbzeng/nbamodel",
    description:
      "A living prediction system that scrapes games, maintains margin-weighted Elo ratings, and blends strength, form, rest, and injuries into matchup probabilities.",
    proof: ["1,321 games tracked", "30 teams", "64.8% benchmark"],
    theme: "nba",
  },
  {
    number: "02",
    eyebrow: "Applied AI · Live app",
    title: "TTB Label Review Assistant",
    domain: "treasury.brianbzeng.com",
    url: "https://treasury.brianbzeng.com",
    github: "https://github.com/brianbzeng/treasurytakehome",
    description:
      "Decision support for alcohol-label review: extract visible evidence, apply commodity-aware rules, and make uncertainty obvious across single, scan, and batch workflows.",
    proof: ["3 review modes", "Vision + rules", "Human in the loop"],
    theme: "treasury",
  },
];

export default function Home() {
  const [remaining, setRemaining] = useState(8);
  const [averages, setAverages] = useState<Record<string, number>>(PRESETS.baseline);
  const [activePreset, setActivePreset] = useState<keyof typeof PRESETS | null>("baseline");

  const standings = useMemo(
    () =>
      TEAMS.map((team) => ({
        ...team,
        average: averages[team.id],
        projected: team.current + remaining * averages[team.id],
      })).sort((a, b) => b.projected - a.projected),
    [averages, remaining],
  );

  const leader = standings[0];
  const gap = standings[0].projected - standings[1].projected;
  const maxProjected = standings[0].projected;

  function selectPreset(preset: keyof typeof PRESETS) {
    setActivePreset(preset);
    setAverages(PRESETS[preset]);
  }

  function updateAverage(teamId: string, value: number) {
    setActivePreset(null);
    setAverages((current) => ({ ...current, [teamId]: value }));
  }

  return (
    <main id="top">
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Brian Zeng, back to top">
          <span>BZ</span>
          <span className="brand-index">/ 01</span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#work">Work</a>
          <a href="#f1-lab">F1 lab</a>
          <a href="#about">About</a>
        </nav>
        <a
          className="header-github"
          href="https://github.com/brianbzeng"
          target="_blank"
          rel="noreferrer"
        >
          GitHub <span aria-hidden="true">↗</span>
        </a>
      </header>

      <section className="hero shell" aria-labelledby="hero-title">
        <div className="hero-copy">
          <p className="kicker">Brian Zeng · Data + software</p>
          <h1 id="hero-title">
            Tools for questions that don&apos;t have <em>tidy answers.</em>
          </h1>
          <div className="hero-bottom">
            <p>
              Sports, markets, models, and practical software. I turn messy data
              into interfaces people can actually use.
            </p>
            <div className="hero-actions">
              <a className="button button-dark" href="#work">
                Explore the work <span aria-hidden="true">↓</span>
              </a>
              <a
                className="text-link"
                href="https://github.com/brianbzeng"
                target="_blank"
                rel="noreferrer"
              >
                See all code <span aria-hidden="true">↗</span>
              </a>
            </div>
          </div>
        </div>

        <div className="signal-map" aria-label="Project signal map">
          <div className="signal-meta">
            <span>SELECTED SYSTEMS</span>
            <span>04 / ACTIVE</span>
          </div>
          <div className="signal-rule signal-rule-one" />
          <div className="signal-rule signal-rule-two" />
          <div className="signal-rule signal-rule-three" />
          <div className="signal-node node-nba">
            <span>01</span>
            <strong>NBA</strong>
            <small>Prediction</small>
          </div>
          <div className="signal-node node-treasury">
            <span>02</span>
            <strong>TTB</strong>
            <small>Review</small>
          </div>
          <div className="signal-node node-f1">
            <span>03</span>
            <strong>F1</strong>
            <small>Simulation</small>
          </div>
          <div className="signal-node node-amazon">
            <span>04</span>
            <strong>AMZ</strong>
            <small>Audit</small>
          </div>
          <div className="signal-dot" aria-hidden="true" />
          <p className="signal-caption">
            One connected practice: collect carefully, model honestly, present clearly.
          </p>
        </div>
      </section>

      <section className="work-section shell" id="work" aria-labelledby="work-title">
        <div className="section-heading">
          <p className="kicker">01 / Selected work</p>
          <h2 id="work-title">Built to leave the notebook.</h2>
          <p>
            The flagship projects are complete, usable products—each with its own
            data pipeline, interface, and point of view.
          </p>
        </div>

        <div className="app-grid">
          {apps.map((app) => (
            <article className={`app-card ${app.theme}`} key={app.title}>
              <a
                className="app-card-link"
                href={app.url}
                target="_blank"
                rel="noreferrer"
                aria-label={`Open ${app.title} live app`}
              >
                <div className="app-topline">
                  <span>{app.number}</span>
                  <span>{app.eyebrow}</span>
                  <span className="live-status"><i /> Live</span>
                </div>

                {app.theme === "nba" ? <NbaPreview /> : <TreasuryPreview />}

                <div className="app-copy">
                  <div>
                    <p className="app-domain">{app.domain}</p>
                    <h3>{app.title}</h3>
                  </div>
                  <p>{app.description}</p>
                </div>
                <div className="app-footer">
                  <ul aria-label={`${app.title} highlights`}>
                    {app.proof.map((item) => <li key={item}>{item}</li>)}
                  </ul>
                  <span className="launch-link">Open live app <b aria-hidden="true">↗</b></span>
                </div>
              </a>
              <a className="repo-link" href={app.github} target="_blank" rel="noreferrer">
                View source <span aria-hidden="true">↗</span>
              </a>
            </article>
          ))}
        </div>
      </section>

      <section className="f1-section" id="f1-lab" aria-labelledby="f1-title">
        <div className="shell f1-layout">
          <div className="f1-intro">
            <p className="kicker">02 / Interactive model</p>
            <h2 id="f1-title">Put the paddock on a whiteboard.</h2>
            <p className="f1-lead">
              The full notebook learns from 2010–2025 race history and runs 10,000
              Monte Carlo simulations. This lightweight lab lets you pressure-test
              one legible part of the idea: the points each constructor might carry
              through the remaining calendar.
            </p>
            <dl className="model-facts">
              <div><dt>Model</dt><dd>Tuned Ridge</dd></div>
              <div><dt>Test RMSE</dt><dd>1.524</dd></div>
              <div><dt>Simulations</dt><dd>10,000</dd></div>
            </dl>
            <a
              className="f1-source"
              href="https://github.com/brianbzeng/f1model"
              target="_blank"
              rel="noreferrer"
            >
              Open the full notebook <span aria-hidden="true">↗</span>
            </a>
          </div>

          <div className="predictor" aria-label="F1 constructor points scenario explorer">
            <div className="predictor-header">
              <div>
                <p className="instrument-label">Scenario explorer · Sample data</p>
                <h3>Constructor projection</h3>
              </div>
              <span className="model-online"><i /> Interactive</span>
            </div>

            <div className="predictor-controls">
              <div className="round-control">
                <span>Remaining weekends</span>
                <div className="stepper">
                  <button
                    type="button"
                    onClick={() => setRemaining((value) => Math.max(1, value - 1))}
                    aria-label="Decrease remaining race weekends"
                  >−</button>
                  <strong>{remaining}</strong>
                  <button
                    type="button"
                    onClick={() => setRemaining((value) => Math.min(12, value + 1))}
                    aria-label="Increase remaining race weekends"
                  >+</button>
                </div>
              </div>
              <div className="preset-control" role="group" aria-label="Scenario presets">
                {(Object.keys(PRESETS) as Array<keyof typeof PRESETS>).map((preset) => (
                  <button
                    type="button"
                    key={preset}
                    className={activePreset === preset ? "active" : ""}
                    onClick={() => selectPreset(preset)}
                    aria-pressed={activePreset === preset}
                  >
                    {preset === "baseline" ? "Current form" : preset === "challengers" ? "Closing pack" : "Chaos"}
                  </button>
                ))}
              </div>
            </div>

            <fieldset className="team-inputs">
              <legend>Average points per race weekend</legend>
              {TEAMS.map((team) => (
                <label key={team.id}>
                  <span className="team-key">
                    <i style={{ background: team.color }} />
                    <b>{team.short}</b>
                    <span>{averages[team.id]} pts</span>
                  </span>
                  <input
                    type="range"
                    min="12"
                    max="38"
                    value={averages[team.id]}
                    onChange={(event) => updateAverage(team.id, Number(event.target.value))}
                    aria-label={`${team.name} average points per race weekend`}
                  />
                </label>
              ))}
            </fieldset>

            <div className="result-head">
              <div aria-live="polite">
                <span>Projected leader</span>
                <strong>{leader.name}</strong>
              </div>
              <p>+{gap} pts over P2</p>
            </div>

            <ol className="standings">
              {standings.map((team, index) => (
                <li key={team.id}>
                  <span className="rank">{String(index + 1).padStart(2, "0")}</span>
                  <span className="standing-name"><i style={{ background: team.color }} />{team.name}</span>
                  <span className="score-track" aria-hidden="true">
                    <i style={{ width: `${Math.max(15, (team.projected / maxProjected) * 100)}%`, background: team.color }} />
                  </span>
                  <strong>{team.projected}</strong>
                </li>
              ))}
            </ol>
            <p className="formula">Projection = sample current points + weekends × average points</p>
          </div>
        </div>
      </section>

      <section className="archive-section shell" aria-labelledby="archive-title">
        <div className="section-heading compact">
          <p className="kicker">03 / Model archive</p>
          <h2 id="archive-title">One more useful rabbit hole.</h2>
        </div>
        <a
          className="archive-row"
          href="https://github.com/brianbzeng/amazonmodel"
          target="_blank"
          rel="noreferrer"
        >
          <span className="archive-number">04</span>
          <div>
            <p>Classification · NLP · Audit design</p>
            <h3>Amazon Review Suspicion Audit</h3>
          </div>
          <p className="archive-description">
            An interpretable risk score for the 2023 Amazon Reviews dataset, paired
            with an independent LLM audit and explicit disagreement review.
          </p>
          <div className="archive-result">
            <strong>92.18%</strong>
            <span>rating-proxy baseline</span>
          </div>
          <span className="archive-arrow" aria-hidden="true">↗</span>
        </a>
        <p className="archive-note">
          Carefully scoped: this is a review-risk audit, not a claim that a review is fake.
        </p>
      </section>

      <section className="about-section" id="about" aria-labelledby="about-title">
        <div className="shell about-grid">
          <p className="kicker">04 / About the work</p>
          <div>
            <h2 id="about-title">The model is only half the product.</h2>
            <p>
              I like projects where the hard part isn&apos;t only training a model.
              It&apos;s collecting the right data, exposing the assumptions, and deciding
              what the result should let someone do next.
            </p>
            <p className="serif-note">
              Some serious, some for Sundays. All built to be used.
            </p>
          </div>
          <div className="toolkit">
            <span>Often working with</span>
            <ul>
              <li>Python</li><li>scikit-learn</li><li>Flask</li><li>React</li>
              <li>Data pipelines</li><li>Applied AI</li><li>Product design</li>
            </ul>
          </div>
        </div>
      </section>

      <footer className="site-footer">
        <div className="shell footer-top">
          <p className="kicker">BZ / End</p>
          <h2>Have a problem worth making smaller?</h2>
          <a
            className="button button-paper"
            href="https://github.com/brianbzeng"
            target="_blank"
            rel="noreferrer"
          >
            Find me on GitHub <span aria-hidden="true">↗</span>
          </a>
        </div>
        <div className="shell footer-bottom">
          <p>Brian Zeng · Data products & software</p>
          <div>
            <a href="https://nba.brianbzeng.com" target="_blank" rel="noreferrer">NBA app ↗</a>
            <a href="https://treasury.brianbzeng.com" target="_blank" rel="noreferrer">Treasury app ↗</a>
            <a href="#top">Back to top ↑</a>
          </div>
        </div>
      </footer>
    </main>
  );
}

function NbaPreview() {
  const games = [
    ["OKC", "2133", "+12"],
    ["CLE", "1920", "+04"],
    ["BOS", "1900", "−02"],
  ];
  return (
    <div className="app-preview nba-preview" aria-hidden="true">
      <div className="preview-chrome"><span /><span /><span /><b>LIVE ELO BOARD</b></div>
      <div className="nba-board">
        <div className="court-map">
          <span className="court-ring" />
          <i className="shot shot-one" /><i className="shot shot-two" /><i className="shot shot-three" />
          <i className="shot shot-four" /><i className="shot shot-five" />
          <div className="matchup-score"><small>HOME WIN</small><strong>67.4%</strong></div>
        </div>
        <div className="elo-list">
          <p><span>TEAM</span><span>ELO</span><span>FORM</span></p>
          {games.map((game, index) => (
            <div key={game[0]}><b>{String(index + 1).padStart(2, "0")} {game[0]}</b><span>{game[1]}</span><em>{game[2]}</em></div>
          ))}
        </div>
      </div>
    </div>
  );
}

function TreasuryPreview() {
  return (
    <div className="app-preview treasury-preview" aria-hidden="true">
      <div className="ttb-header"><span>TTB LABEL REVIEW</span><b>DECISION SUPPORT ONLY</b></div>
      <div className="review-workspace">
        <div className="label-art">
          <span>BARREL No. 8</span><strong>NORTH COAST</strong><i>45% ALC / VOL</i>
        </div>
        <div className="review-results">
          <p>REVIEW SIGNALS <span>5 / 6</span></p>
          <div><i className="check">✓</i><span>Brand name located</span></div>
          <div><i className="check">✓</i><span>Class / type aligned</span></div>
          <div><i className="warn">!</i><span>Human review suggested</span></div>
        </div>
      </div>
    </div>
  );
}
