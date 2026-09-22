"use client";

import type { GitHubActivity } from "./GitHubPulse";

export default function TerminalPulse({ activity }: { activity: GitHubActivity; active: boolean }) {
  const loading = activity.source === "loading";
  // Shared activity stays newest-first; terminal output is read from its tail.
  const pushes = [...activity.pushes].reverse();
  return <section className="windows-terminal-pulse" aria-label="Recent GitHub pushes">
    <p>~/github/recent-pushes/</p>
    <p>{activity.source === "snapshot" ? "Saved public pushes · oldest first" : "Public pushes · oldest first"}</p><br />
    {loading ? <p role="status">Loading public pushes…</p> : pushes.map((push) => <div className="terminal-push-entry" key={push.id}>
      <p><time dateTime={push.date}>{new Date(push.date).toLocaleString("en-US", { timeZone: "America/Los_Angeles", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })} PT</time></p>
      <p>├─ <a href={push.url} target="_blank" rel="noopener noreferrer">{push.repo}/</a>{push.branch && <span> → {push.branch}</span>}</p>
      {push.commits.map(commit => <p key={commit.sha}>│  <a href={commit.url} target="_blank" rel="noopener noreferrer">{commit.sha.slice(0, 7)}</a> {commit.message}</p>)}
    </div>)}
    {!loading && !activity.pushes.length && <p>{activity.pushesAvailable ? "No recent public pushes." : "Public pushes are unavailable right now."}</p>}
    <p><a href="https://github.com/brianbzeng" target="_blank" rel="noopener noreferrer">Open GitHub ↗</a></p>
  </section>;
}
