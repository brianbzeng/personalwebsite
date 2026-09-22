"use client";

import { useMemo, useState } from "react";
import DesktopWindow from "./DesktopWindow";
import DesktopIcon from "./DesktopIcon";
import forecast from "../data/f1-forecast.json";
import standings from "../data/f1-standings.json";
import { currentConstructorForecast, F1_INITIAL_FRAME, F1_METRICS, F1_MINIMUM_SIZE, f1Date, sortedConstructors, type F1Metric } from "./f1ForecastData";
import "./desktopF1.css";

type Props = { active: boolean; foreground: boolean; minimized: boolean; zIndex: number; onActivate: () => void; onMinimize: () => void; onClose: () => void };
const teams = currentConstructorForecast(forecast.teams, standings.teams);

// Restored from the original portfolio demo (1ed7598), with shared desktop chrome.
export function F1ForecastContent() {
  const [metric, setMetric] = useState<F1Metric>("title");
  const sorted = useMemo(() => sortedConstructors(teams, metric), [metric]);
  const showingStandings = metric === "currentPoints";
  const historicalForecast = forecast.completedRaces !== standings.completedRaces;
  const largest = showingStandings ? Math.max(1, ...teams.map((team) => team.currentPoints)) : 100;
  return <div className="f1-app-body">
    <header className="f1-app-overview">
      <div><p className="f1-eyebrow">FORMULA 1 · {standings.season}</p><h1>Constructors’ Forecast</h1><p>Standings through the {standings.through}</p></div>
      <div className="f1-season-progress"><strong>{String(standings.completedRaces).padStart(2, "0")}<span> / {standings.totalRaces}</span></strong><span>Grands Prix completed</span><progress aria-label="Season progress" value={standings.completedRaces} max={standings.totalRaces} /></div>
    </header>
    <dl className="f1-model-facts">
      <div><dt>Model</dt><dd>Ridge regression</dd></div>
      <div><dt>Simulations</dt><dd>{forecast.simulations.toLocaleString("en-US")}</dd></div>
      <div><dt>Test RMSE</dt><dd>{forecast.validationRmse.toFixed(3)}</dd></div>
      <div><dt>Standings updated</dt><dd>{f1Date(standings.asOf)}</dd></div>
    </dl>
    <section className="f1-leaderboard" aria-label="Constructor leaderboard">
      <div className="f1-caption-toolbar">
        <p id="f1-table-summary" className="f1-table-summary" tabIndex={0}>{forecast.season} constructors sorted by {F1_METRICS[metric]}. Points as of {f1Date(standings.asOf)}; model estimates as of {f1Date(forecast.asOf)}.</p>
        <div className="f1-metric-control" role="group" aria-label="Forecast metric">
          {(Object.keys(F1_METRICS) as F1Metric[]).map((key) => <button type="button" key={key} onClick={() => setMetric(key)} aria-pressed={metric === key}>{F1_METRICS[key]}</button>)}
        </div>
      </div>
      <div className="f1-odds-toolbar"><div className="f1-odds-heading"><h2>{showingStandings ? "Championship standings" : "Model probabilities"}</h2>
        <p className="f1-sort-description" aria-live="polite">Leaderboard sorted by {F1_METRICS[metric].toLowerCase()}{showingStandings ? "." : " probability."}</p></div></div>
      {showingStandings && <p className="f1-snapshot-date">Official standings · {f1Date(standings.asOf)}</p>}
      <div className="f1-table-scroll" tabIndex={0} role="region" aria-label="Constructor results table">
        <table className="f1-odds-table" aria-describedby="f1-table-summary">
          <thead><tr><th scope="col">#</th><th scope="col">Constructor</th><th scope="col">{showingStandings ? "Points" : F1_METRICS[metric]}</th>{!showingStandings && <><th scope="col">Current pts.</th><th scope="col">Avg. rank</th></>}</tr></thead>
          <tbody>{sorted.map((team, index) => <tr key={team.name}>
            <td>{String(showingStandings ? team.currentRank : index + 1).padStart(2, "0")}</td><th scope="row">{team.name}</th>
            <td><div className="f1-odds-value"><span className="f1-odds-track" aria-hidden="true"><i style={{ width: `${team[metric] / largest * 100}%` }} /></span><strong>{showingStandings ? team.currentPoints : `${team[metric].toFixed(2)}%`}</strong></div></td>
            {!showingStandings && <><td>{team.currentPoints}</td><td>{team.meanRank.toFixed(2)}</td></>}
          </tr>)}</tbody>
        </table>
      </div>
    </section>
    <details className="f1-method"><summary>Method &amp; limits</summary>
      <p>The analysis asks how results so far help predict each constructor’s final championship position. Historical seasons are compared at a similar stage of the calendar, using race points, grid and finishing positions, retirements, and win, podium, and top-10 rates. Ridge regression combines these measures while limiting the influence of individual predictors. The 2018 season is excluded because the source data combine two separate Force India entries.</p>
      <p>To test the model, each validation season is predicted using only earlier seasons. The root mean squared error was {forecast.validationRmse.toFixed(2)} championship positions, compared with {forecast.baselineRmse.toFixed(2)} for keeping the current race-points order unchanged. This suggests a modest improvement in rank prediction, but does not establish that the displayed probabilities are equally accurate.</p>
      <p>The next step uses errors from those held-out seasons to simulate {forecast.simulations.toLocaleString("en-US")} possible finishing orders. The table reports how often each constructor places first, in the top three, or in the top five. These estimates assume past errors remain useful for this season and are sampled independently across teams. Regulation changes and new entrants may produce outcomes the historical data do not capture.</p>
      {historicalForecast && <p>The forecast remains the original {f1Date(forecast.asOf)} snapshot. The points and Standings view include results through the {standings.through}; the older probabilities have not been relabeled as a fresh prediction.</p>}
      <p>The forecast includes results through the {forecast.through}, updated {f1Date(forecast.asOf)}. Sprint points count toward the displayed standings and historical final championship positions, but are excluded from race-level predictors consistently across seasons. The probabilities are model estimates, not betting odds or a live feed.</p>
    </details>
    <footer className="f1-app-footer"><a href="https://github.com/brianbzeng/f1model" target="_blank" rel="noopener noreferrer">Model source ↗</a><a href={standings.source} target="_blank" rel="noopener noreferrer">Official standings ↗</a></footer>
  </div>;
}

export default function DesktopF1(props: Props) {
  return <DesktopWindow {...props} title="F1 Forecast" className="mac-f1-window" initialFrame={F1_INITIAL_FRAME} minimumSize={F1_MINIMUM_SIZE}
    titlebar={<div className="mac-window-heading"><DesktopIcon name="f1" /><span>F1 Forecast</span></div>}><F1ForecastContent /></DesktopWindow>;
}
