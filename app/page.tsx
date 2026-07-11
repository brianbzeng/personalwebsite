"use client";

import { useMemo, useState } from "react";
import ThemeToggle from "./components/ThemeToggle";

type OddsMetric = "title" | "top3" | "top5";

type ConstructorOdds = {
  name: string;
  meanRank: number;
  title: number;
  top3: number;
  top5: number;
  color: string;
};

const ODDS_METRICS: Record<OddsMetric, string> = {
  title: "Title",
  top3: "Top 3",
  top5: "Top 5",
};

const F1_ODDS: ConstructorOdds[] = [
  { name: "McLaren", meanRank: 1.9318, title: 48.47, top3: 88.52, top5: 99.57, color: "#ff8700" },
  { name: "Ferrari", meanRank: 2.8744, title: 20.12, top3: 67.79, top5: 95.30, color: "#e8002d" },
  { name: "Mercedes", meanRank: 3.0366, title: 16.53, top3: 63.99, top5: 94.20, color: "#00a19b" },
  { name: "Red Bull", meanRank: 3.2916, title: 13.04, top3: 56.43, top5: 91.85, color: "#3154c7" },
  { name: "Williams", meanRank: 5.2408, title: 1.68, top3: 16.10, top5: 57.90, color: "#00a3e0" },
  { name: "RB", meanRank: 6.8727, title: 0.10, top3: 3.46, top5: 22.48, color: "#6692ff" },
  { name: "Aston Martin", meanRank: 7.1826, title: 0.04, top3: 1.96, top5: 17.39, color: "#229971" },
  { name: "Haas", meanRank: 7.5742, title: 0.02, top3: 1.24, top5: 12.18, color: "#b6babd" },
  { name: "Sauber", meanRank: 8.1826, title: 0.00, top3: 0.39, top5: 6.35, color: "#52e252" },
  { name: "Alpine", meanRank: 8.8127, title: 0.00, top3: 0.12, top5: 2.78, color: "#ff87bc" },
];

const SKILL_GROUPS = [
  {
    title: "Languages",
    skills: ["Python", "R", "SQL", "C++", "SAS"],
  },
  {
    title: "Libraries & data tools",
    skills: ["Pandas", "NumPy", "scikit-learn", "PySpark", "Beautiful Soup", "Tidyverse", "Tidymodels", "Git", "Jupyter", "VS Code", "RStudio"],
  },
  {
    title: "Data science",
    skills: ["Data cleaning", "Feature engineering", "Data visualization", "Model evaluation", "Cross-validation", "Monte Carlo simulation"],
  },
  {
    title: "Modeling",
    skills: ["Regression", "Classification", "Clustering", "PCA", "Bayesian analysis", "NLP", "TF-IDF"],
  },
  {
    title: "AI & LLM",
    skills: ["OpenAI-compatible APIs", "LLM-assisted classification", "Prompt design", "Blinded LLM auditing", "AI evaluation"],
  },
  {
    title: "Visualization & reporting",
    skills: ["Matplotlib", "Seaborn", "ggplot2", "Quarto", "R Markdown", "Correlation heatmaps", "Confusion matrices"],
  },
];

const apps = [
  {
    number: "01",
    eyebrow: "Sports analytics · Live app",
    title: "NBA Odds Predictor",
    domain: "nba.brianbzeng.com",
    url: "https://nba.brianbzeng.com",
    github: "https://github.com/brianbzeng/nbamodel",
    description:
      "NBA game forecasts using margin-adjusted Elo ratings, recent form, rest, and injury data.",
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
      "AI-assisted alcohol-label review with evidence extraction, commodity-aware rules, and three review workflows.",
    proof: ["3 review modes", "Vision + rules", "Human in the loop"],
    theme: "treasury",
  },
];

export default function Home() {
  const [oddsMetric, setOddsMetric] = useState<OddsMetric>("title");
  const sortedOdds = useMemo(
    () => [...F1_ODDS].sort((a, b) => b[oddsMetric] - a[oddsMetric]),
    [oddsMetric],
  );

  return (
    <main id="top">
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Brian Zeng, back to top">
          <span>BZ</span>
          <span className="brand-index">/ 01</span>
        </a>
        <nav aria-label="Primary navigation">
          <a className="nav-skills" href="#skills">Skills</a>
          <a className="nav-projects" href="#work">Projects</a>
          <a className="nav-f1" href="#f1-lab">F1 Demo</a>
          <a className="nav-contact" href="/contact">Contact</a>
        </nav>
        <div className="header-actions">
          <ThemeToggle />
          <a
            className="header-github"
            href="https://github.com/brianbzeng"
            target="_blank"
            rel="noreferrer"
          >
            GitHub <span aria-hidden="true">↗</span>
          </a>
        </div>
      </header>

      <section className="hero shell" aria-labelledby="hero-title">
        <div className="hero-copy">
          <p className="kicker">Portfolio / 2026</p>
          <h1 id="hero-title">Brian Zeng</h1>
          <div className="hero-bottom">
            <dl className="profile-facts">
              <div>
                <dt>Current focus</dt>
                <dd>Data Analyst · Data Engineer · Data Scientist · AI/IT Specialist</dd>
              </div>
              <div>
                <dt>Education</dt>
                <dd>UC Santa Barbara · B.S. Probability &amp; Statistics with Data Science · 2026</dd>
              </div>
              <div>
                <dt>Based in</dt>
                <dd>Oakland, California</dd>
              </div>
            </dl>
            <div className="hero-actions">
              <a className="button button-dark" href="#work">
                View projects <span aria-hidden="true">↓</span>
              </a>
              <a
                className="text-link"
                href="https://github.com/brianbzeng"
                target="_blank"
                rel="noreferrer"
              >
                GitHub <span aria-hidden="true">↗</span>
              </a>
            </div>
          </div>
        </div>

        <div className="signal-map" aria-label="Project signal map">
          <div className="signal-meta">
            <span>SELECTED PROJECTS</span>
            <span>04 PROJECTS</span>
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
        </div>
      </section>

      <section className="skills-section" id="skills" aria-labelledby="skills-title">
        <div className="shell">
          <div className="section-heading concise skills-heading">
            <p className="kicker">01 / Technical Skills</p>
            <h2 id="skills-title">Skills</h2>
          </div>
          <div className="skills-grid">
            {SKILL_GROUPS.map((group, index) => (
              <article className="skill-group" key={group.title}>
                <div className="skill-group-title">
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <h3>{group.title}</h3>
                </div>
                <ul>
                  {group.skills.map((skill) => <li key={skill}>{skill}</li>)}
                </ul>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="work-section shell" id="work" aria-labelledby="work-title">
        <div className="section-heading concise">
          <p className="kicker">02 / Projects</p>
          <h2 id="work-title">Projects</h2>
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
                  <span className="launch-link">Open app <b aria-hidden="true">↗</b></span>
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
            <p className="kicker">03 / Interactive Demo</p>
            <h2 id="f1-title">2026 Constructors&rsquo; Model Odds</h2>
            <p className="f1-lead">
              Tuned Ridge forecast using 2025 constructor inputs and 10,000
              residual-resampled simulations.
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
              View on GitHub <span aria-hidden="true">↗</span>
            </a>
          </div>

          <div className="predictor odds-panel" aria-label="2026 F1 constructors model forecast">
            <div className="predictor-header">
              <div>
                <p className="instrument-label">Model snapshot · 2025 inputs</p>
                <h3>Championship odds</h3>
              </div>
              <span className="model-snapshot">10,000 simulations</span>
            </div>

            <div className="odds-toolbar">
              <span>Sort leaderboard by</span>
              <div className="odds-metrics" role="group" aria-label="Forecast metric">
                {(Object.keys(ODDS_METRICS) as OddsMetric[]).map((metric) => (
                  <button
                    type="button"
                    key={metric}
                    className={oddsMetric === metric ? "active" : ""}
                    onClick={() => setOddsMetric(metric)}
                    aria-pressed={oddsMetric === metric}
                  >
                    {ODDS_METRICS[metric]}
                  </button>
                ))}
              </div>
            </div>

            <p className="sr-only" aria-live="polite">
              Leaderboard sorted by {ODDS_METRICS[oddsMetric]} probability.
            </p>

            <div className="odds-table-wrap">
              <table className="odds-table">
                <caption className="sr-only">
                  2026 constructors forecast sorted by {ODDS_METRICS[oddsMetric]} probability
                </caption>
                <thead>
                  <tr>
                    <th scope="col">#</th>
                    <th scope="col">Constructor</th>
                    <th scope="col">{ODDS_METRICS[oddsMetric]}</th>
                    <th scope="col">Avg. finish</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedOdds.map((team, index) => {
                    const value = team[oddsMetric];
                    const barWidth = value === 0 ? 0 : Math.max(value, 0.35);
                    return (
                      <tr key={team.name}>
                        <td>{String(index + 1).padStart(2, "0")}</td>
                        <th scope="row">
                          <i className="constructor-dot" style={{ background: team.color }} />
                          {team.name}
                        </th>
                        <td>
                          <div className="odds-value">
                            <span className="odds-track" aria-hidden="true">
                              <i style={{ width: `${barWidth}%`, background: team.color }} />
                            </span>
                            <strong>{value.toFixed(2)}%</strong>
                          </div>
                        </td>
                        <td>{team.meanRank.toFixed(2)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <details className="odds-method">
              <summary>Method &amp; limits</summary>
              <p>
                Prior-season constructor performance and driver-strength features feed a tuned
                Ridge model. Probabilities are each team&rsquo;s share of 10,000 residual-resampled
                simulations. This is a model forecast, not betting odds or a live data feed;
                2026 regulation changes, Cadillac, and Sauber&rsquo;s Audi transition are not modeled.
              </p>
            </details>
          </div>
        </div>
      </section>

      <section className="archive-section shell" aria-labelledby="archive-title">
        <div className="section-heading compact">
          <p className="kicker">04 / Other Project</p>
          <h2 id="archive-title">Amazon Review Classification</h2>
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
            NLP pipeline for 2023 Amazon reviews using TF-IDF, engineered signals,
            and a blinded LLM audit.
          </p>
          <span className="archive-arrow" aria-hidden="true">↗</span>
        </a>
      </section>

      <footer className="site-footer">
        <div className="shell footer-profile">
          <div>
            <p className="kicker">Portfolio / 2026</p>
            <h2>Brian Zeng</h2>
          </div>
          <p>Data analysis · data science · software</p>
        </div>
        <div className="shell footer-bottom">
          <p>Oakland, California</p>
          <div>
            <a href="/contact">Contact</a>
            <a href="mailto:bzeng0000@gmail.com">Email ↗</a>
            <a href="https://www.linkedin.com/in/brianbzeng" target="_blank" rel="noreferrer">LinkedIn ↗</a>
            <a href="https://github.com/brianbzeng" target="_blank" rel="noreferrer">GitHub ↗</a>
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
