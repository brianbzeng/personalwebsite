export const F1_METRICS = { title: "Title", top3: "Top 3", top5: "Top 5", currentPoints: "Standings" } as const;
export type F1Metric = keyof typeof F1_METRICS;
export type F1Standing = { name: string; currentRank: number; currentPoints: number };
export type F1Constructor = F1Standing & { meanRank: number; title: number; top3: number; top5: number };
export const F1_INITIAL_FRAME = { x: .14, y: .08, width: .64, height: .82 };
export const F1_MINIMUM_SIZE = { width: 540, height: 360 };

export function currentConstructorForecast(forecast: F1Constructor[], standings: F1Standing[]): F1Constructor[] {
  return standings.map((standing) => {
    const prediction = forecast.find((team) => team.name === standing.name);
    if (!prediction) throw new Error(`Missing forecast for ${standing.name}`);
    return { ...prediction, ...standing };
  });
}

export function sortedConstructors(teams: F1Constructor[], metric: F1Metric): F1Constructor[] {
  return [...teams].sort((a, b) => b[metric] - a[metric] || a.currentRank - b.currentRank);
}

export function f1Date(value: string): string {
  return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" }).format(new Date(`${value}T12:00:00Z`));
}
