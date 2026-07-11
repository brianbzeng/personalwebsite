"use client";

import { useEffect, useMemo, useState } from "react";

type Theme = "light" | "dark";

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
  const [theme, setTheme] = useState<Theme>("light");
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

  useEffect(() => {
    const root = document.documentElement;
    const saved = window.localStorage.getItem("bz-theme");
    const initial: Theme = saved === "light" || saved === "dark"
      ? saved
      : window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";

    setTheme(initial);
    root.dataset.theme = initial;
    root.style.colorScheme = initial;

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const syncWithSystem = (event: MediaQueryListEvent) => {
      if (window.localStorage.getItem("bz-theme")) return;
      const nextTheme: Theme = event.matches ? "dark" : "light";
      setTheme(nextTheme);
      root.dataset.theme = nextTheme;
      root.style.colorScheme = nextTheme;
    };

    media.addEventListener("change", syncWithSystem);
    return () => media.removeEventListener("change", syncWithSystem);
  }, []);

  function toggleTheme() {
    const nextTheme: Theme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    document.documentElement.dataset.theme = nextTheme;
    document.documentElement.style.colorScheme = nextTheme;
    window.localStorage.setItem("bz-theme", nextTheme);
  }

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
          <a href="#work">Projects</a>
          <a href="#f1-lab">F1 demo</a>
          <a href="#skills">Skills</a>
        </nav>
        <div className="header-actions">
          <button
            className="theme-toggle"
            type="button"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            aria-pressed={theme === "dark"}
          >
            <span className="theme-icon" aria-hidden="true"><i /></span>
            <span>{theme === "dark" ? "Light" : "Dark"}</span>
          </button>
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

      <section className="work-section shell" id="work" aria-labelledby="work-title">
        <div className="section-heading concise">
          <p className="kicker">01 / Projects</p>
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
            <p className="kicker">02 / Interactive demo</p>
            <h2 id="f1-title">F1 Constructors Championship Predictor</h2>
            <p className="f1-lead">
              Ridge regression trained on 2010–2025 race data, with 10,000 Monte
              Carlo simulations for season outcomes. Adjust the assumptions below.
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
          <p className="kicker">03 / Other project</p>
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

      <section className="skills-section" id="skills" aria-labelledby="skills-title">
        <div className="shell">
          <div className="section-heading concise skills-heading">
            <p className="kicker">04 / Technical skills</p>
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
            <a href="https://github.com/brianbzeng" target="_blank" rel="noreferrer">GitHub ↗</a>
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
