"use client";

import { useEffect, useMemo, useState } from "react";

const GITHUB_USERNAME = "brianbzeng";
const ACTIVITY_DAYS = 28;
const EVENTS_PER_PAGE = 100;
const MAX_EVENT_PAGES = 3;
const CACHE_KEY = "bz-github-activity-v2";
const CACHE_TTL = 30 * 60 * 1000;
const CHART_WIDTH = 560;
const CHART_HEIGHT = 178;
const CHART_PAD_X = 8;
const CHART_PAD_Y = 14;

type GitHubEvent = {
  id: string;
  type: string;
  created_at: string;
  repo: { name: string };
  payload?: {
    action?: string;
    commits?: unknown[];
    distinct_size?: number;
    number?: number;
    ref?: string | null;
    ref_type?: string | null;
    size?: number;
  };
};

type ActivityItem = {
  id: string;
  action: string;
  repo: string;
  time: string;
  url: string;
};

type ActivitySource = "loading" | "live" | "snapshot";

type GitHubActivity = {
  daily: number[];
  total: number | null;
  repoCount: number | null;
  latest: string;
  recent: ActivityItem[];
  source: ActivitySource;
};

type CachedActivity = {
  savedAt: number;
  activity: GitHubActivity;
};

type ChartPoint = {
  x: number;
  y: number;
  value: number;
};

const EMPTY_ACTIVITY: GitHubActivity = {
  daily: Array.from({ length: ACTIVITY_DAYS }, () => 0),
  total: null,
  repoCount: null,
  latest: "Syncing",
  recent: [],
  source: "loading",
};

const SNAPSHOT_ACTIVITY: GitHubActivity = {
  daily: [0, 0, 0, 0, 25, 8, 6, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 6, 27, 10],
  total: 88,
  repoCount: 3,
  latest: "Jul 11",
  recent: [
    {
      id: "snapshot-pr",
      action: "Merged pull request",
      repo: "treasurytakehome",
      time: "Jul 11",
      url: "https://github.com/brianbzeng/treasurytakehome",
    },
    {
      id: "snapshot-push",
      action: "Pushed to main",
      repo: "treasurytakehome",
      time: "Jul 11",
      url: "https://github.com/brianbzeng/treasurytakehome",
    },
    {
      id: "snapshot-nba",
      action: "Updated repository",
      repo: "nbamodel",
      time: "Jun 20",
      url: "https://github.com/brianbzeng/nbamodel",
    },
  ],
  source: "snapshot",
};

function dateKey(date: Date) {
  return date.toISOString().slice(0, 10);
}

function relativeTime(value: string, now: Date) {
  const elapsed = Math.max(0, now.getTime() - new Date(value).getTime());
  const minutes = Math.floor(elapsed / 60_000);

  if (minutes < 1) return "now";
  if (minutes < 60) return `${minutes}m`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;

  const days = Math.floor(hours / 24);
  return `${days}d`;
}

function repoName(event: GitHubEvent) {
  return event.repo.name.split("/").at(-1) ?? event.repo.name;
}

function describeEvent(event: GitHubEvent) {
  const branch = event.payload?.ref?.replace("refs/heads/", "");

  switch (event.type) {
    case "PushEvent":
      return branch ? `Pushed to ${branch}` : "Pushed changes";
    case "PullRequestEvent": {
      const action = event.payload?.action;
      if (action === "opened") return "Opened pull request";
      if (action === "closed") return "Closed pull request";
      if (action === "merged") return "Merged pull request";
      return "Updated pull request";
    }
    case "CreateEvent":
      return event.payload?.ref_type === "repository" ? "Created repository" : `Created ${event.payload?.ref_type ?? "ref"}`;
    case "PublicEvent":
      return "Made repository public";
    case "DeleteEvent":
      return `Deleted ${event.payload?.ref_type ?? "ref"}`;
    case "IssuesEvent":
      return "Updated issue";
    case "IssueCommentEvent":
      return "Commented on issue";
    case "WatchEvent":
      return "Starred repository";
    default:
      return "Updated repository";
  }
}

function eventContributionCount(event: GitHubEvent) {
  if (event.type !== "PushEvent") return 1;

  return Math.max(
    event.payload?.distinct_size
      ?? event.payload?.size
      ?? event.payload?.commits?.length
      ?? 1,
    1,
  );
}

function buildActivity(events: GitHubEvent[]): GitHubActivity {
  const now = new Date();
  const today = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  const days = Array.from({ length: ACTIVITY_DAYS }, (_, index) => {
    const day = new Date(today);
    day.setUTCDate(today.getUTCDate() - (ACTIVITY_DAYS - 1 - index));
    return dateKey(day);
  });
  const dayIndex = new Map(days.map((day, index) => [day, index]));
  const daily = Array.from({ length: ACTIVITY_DAYS }, () => 0);
  const windowEvents = events
    .filter((event) => dayIndex.has(event.created_at.slice(0, 10)))
    .sort((a, b) => b.created_at.localeCompare(a.created_at));

  windowEvents.forEach((event) => {
    const index = dayIndex.get(event.created_at.slice(0, 10));
    if (index !== undefined) daily[index] += eventContributionCount(event);
  });

  const recent: ActivityItem[] = [];
  const seen = new Set<string>();

  for (const event of windowEvents) {
    const key = `${event.type}:${event.payload?.action ?? ""}:${event.repo.name}`;
    if (seen.has(key)) continue;
    seen.add(key);
    recent.push({
      id: event.id,
      action: describeEvent(event),
      repo: repoName(event),
      time: relativeTime(event.created_at, now),
      url: `https://github.com/${event.repo.name}`,
    });
    if (recent.length === 3) break;
  }

  return {
    daily,
    total: daily.reduce((sum, value) => sum + value, 0),
    repoCount: new Set(windowEvents.map((event) => event.repo.name)).size,
    latest: windowEvents[0] ? relativeTime(windowEvents[0].created_at, now) : "Quiet",
    recent,
    source: "live",
  };
}

function isCachedActivity(value: unknown): value is CachedActivity {
  if (!value || typeof value !== "object") return false;
  const cached = value as Partial<CachedActivity>;
  return Boolean(
    typeof cached.savedAt === "number"
      && cached.activity
      && Array.isArray(cached.activity.daily)
      && cached.activity.daily.length === ACTIVITY_DAYS,
  );
}

function chartPoints(values: number[]): ChartPoint[] {
  const maxValue = Math.max(...values, 1);
  const usableWidth = CHART_WIDTH - CHART_PAD_X * 2;
  const usableHeight = CHART_HEIGHT - CHART_PAD_Y * 2;

  return values.map((value, index) => ({
    x: CHART_PAD_X + (index / Math.max(values.length - 1, 1)) * usableWidth,
    y: CHART_HEIGHT - CHART_PAD_Y - (value / maxValue) * usableHeight,
    value,
  }));
}

export default function GitHubPulse() {
  const [activity, setActivity] = useState<GitHubActivity>(EMPTY_ACTIVITY);
  const points = useMemo(() => chartPoints(activity.daily), [activity.daily]);
  const linePoints = points.map((point) => `${point.x},${point.y}`).join(" ");
  const areaPoints = `${CHART_PAD_X},${CHART_HEIGHT - CHART_PAD_Y} ${linePoints} ${CHART_WIDTH - CHART_PAD_X},${CHART_HEIGHT - CHART_PAD_Y}`;
  const latestPoint = activity.total
    ? [...points].reverse().find((point) => point.value > 0)
    : undefined;

  useEffect(() => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 5_000);

    async function loadActivity() {
      try {
        try {
          const stored = window.localStorage.getItem(CACHE_KEY);
          if (stored) {
            const cached: unknown = JSON.parse(stored);
            if (isCachedActivity(cached) && Date.now() - cached.savedAt < CACHE_TTL) {
              setActivity({ ...cached.activity, source: "live" });
              return;
            }
          }
        } catch {
          try {
            window.localStorage.removeItem(CACHE_KEY);
          } catch {
            // Continue without local caching when storage is unavailable.
          }
        }

        const windowStart = new Date();
        windowStart.setUTCDate(windowStart.getUTCDate() - (ACTIVITY_DAYS - 1));
        windowStart.setUTCHours(0, 0, 0, 0);
        const events: GitHubEvent[] = [];

        for (let page = 1; page <= MAX_EVENT_PAGES; page += 1) {
          const response = await fetch(
            `https://api.github.com/users/${GITHUB_USERNAME}/events/public?per_page=${EVENTS_PER_PAGE}&page=${page}`,
            { signal: controller.signal },
          );
          if (!response.ok) throw new Error(`GitHub responded with ${response.status}`);

          const pageEvents = await response.json() as GitHubEvent[];
          events.push(...pageEvents);

          const oldestEvent = pageEvents.at(-1);
          if (
            pageEvents.length < EVENTS_PER_PAGE
            || (oldestEvent && new Date(oldestEvent.created_at) < windowStart)
          ) {
            break;
          }
        }

        const nextActivity = buildActivity(events);
        setActivity(nextActivity);
        try {
          window.localStorage.setItem(
            CACHE_KEY,
            JSON.stringify({ savedAt: Date.now(), activity: nextActivity } satisfies CachedActivity),
          );
        } catch {
          // Live data still renders when storage is unavailable.
        }
      } catch {
        setActivity(SNAPSHOT_ACTIVITY);
      } finally {
        window.clearTimeout(timeout);
      }
    }

    void loadActivity();
    return () => {
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, []);

  const statusLabel = activity.source === "live"
    ? "Live · public"
    : activity.source === "snapshot"
      ? "Recent snapshot"
      : "Syncing feed";

  return (
    <aside className={`github-pulse source-${activity.source}`} aria-labelledby="github-pulse-title">
      <div className="github-pulse-header">
        <h2 id="github-pulse-title">GitHub Pulse</h2>
        <span className="github-feed-status" aria-live="polite">
          <i aria-hidden="true" /> {statusLabel}
        </span>
      </div>

      <dl className="github-stats">
        <div>
          <dt>Public contributions · 28d</dt>
          <dd>{activity.total ?? "—"}</dd>
        </div>
        <div>
          <dt>Active repos</dt>
          <dd>{activity.repoCount ?? "—"}</dd>
        </div>
        <div>
          <dt>Last activity</dt>
          <dd className="github-latest">{activity.latest}</dd>
        </div>
      </dl>

      <div className="github-chart-block">
        <div className="github-chart-meta">
          <span>Public contribution volume</span>
          <span>Last 28 days</span>
        </div>
        <div className="github-chart">
          <svg
            viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
            preserveAspectRatio="none"
            role="img"
            aria-labelledby="github-chart-title github-chart-description"
          >
            <title id="github-chart-title">GitHub public activity over the last 28 days</title>
            <desc id="github-chart-description">
              {activity.total ?? 0} public contributions across {activity.repoCount ?? 0} repositories.
            </desc>
            <line className="github-chart-grid" x1="0" x2={CHART_WIDTH} y1="14" y2="14" />
            <line className="github-chart-grid" x1="0" x2={CHART_WIDTH} y1="89" y2="89" />
            <line className="github-chart-grid" x1="0" x2={CHART_WIDTH} y1="164" y2="164" />
            <polygon className="github-chart-area" points={areaPoints} />
            <polyline
              key={`${activity.source}-${activity.total}`}
              className="github-chart-line"
              points={linePoints}
            />
            {latestPoint && (
              <>
                <circle className="github-chart-ping" cx={latestPoint.x} cy={latestPoint.y} r="9" />
                <circle className="github-chart-dot" cx={latestPoint.x} cy={latestPoint.y} r="4.5" />
              </>
            )}
          </svg>
        </div>
        <div className="github-chart-axis" aria-hidden="true">
          <span>4 weeks ago</span>
          <span>2 weeks</span>
          <span>Today</span>
        </div>
      </div>

      <div className="github-activity">
        <div className="github-activity-heading">
          <span>Recent activity</span>
          <span>{activity.source === "snapshot" ? "Fallback" : "Latest"}</span>
        </div>
        {activity.recent.length > 0 ? (
          <ul>
            {activity.recent.map((item) => (
              <li key={item.id}>
                <span className="github-activity-mark" aria-hidden="true" />
                <a href={item.url} target="_blank" rel="noreferrer">
                  <strong>{item.action}</strong>
                  <small>{item.repo}</small>
                </a>
                <time>{item.time}</time>
              </li>
            ))}
          </ul>
        ) : (
          <div className="github-activity-loading" aria-hidden="true">
            <span /><span /><span />
          </div>
        )}
      </div>

      <a
        className="github-pulse-link"
        href={`https://github.com/${GITHUB_USERNAME}`}
        target="_blank"
        rel="noreferrer"
      >
        View @{GITHUB_USERNAME} <span aria-hidden="true">↗</span>
      </a>
    </aside>
  );
}
