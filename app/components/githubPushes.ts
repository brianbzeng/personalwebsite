export type PublicPush = {
  id: string; repo: string; branch: string; date: string; url: string;
  commits: { sha: string; message: string; url: string }[];
};

// Public events can omit commit details. Never invent a commit or its count.
export function publicPushes(value: unknown): PublicPush[] {
  if (!Array.isArray(value)) return [];
  const seen = new Set<string>();
  return value.filter((event) => event?.type === "PushEvent" && event.public !== false
    && typeof event.id === "string" && typeof event.repo?.name === "string"
    && /^[\w.-]+\/[\w.-]+$/.test(event.repo.name)
    && typeof event.created_at === "string" && Number.isFinite(Date.parse(event.created_at)))
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
    .filter((event) => { if (seen.has(event.id)) return false; seen.add(event.id); return true; })
    .slice(0, 12).map((event) => {
      const base = `https://github.com/${event.repo.name}`;
      const branch = typeof event.payload?.ref === "string" ? event.payload.ref.replace(/^refs\/heads\//, "") : "";
      const head = typeof event.payload?.head === "string" && /^[0-9a-f]{40}$/i.test(event.payload.head) ? event.payload.head : null;
      const commits = (Array.isArray(event.payload?.commits) ? event.payload.commits : [])
        .filter((commit: { sha?: string }) => typeof commit?.sha === "string" && /^[0-9a-f]{40}$/i.test(commit.sha))
        .slice(0, 5).map((commit: { sha: string; message?: string }) => ({
          sha: commit.sha, message: typeof commit.message === "string" ? commit.message.split("\n")[0] : "View commit",
          url: `${base}/commit/${commit.sha}`,
        }));
      if (head && !commits.length) commits.push({ sha: head, message: "Latest commit in this push", url: `${base}/commit/${head}` });
      return { id: event.id, repo: event.repo.name, branch, date: event.created_at,
        url: head ? `${base}/commit/${head}` : branch ? `${base}/commits/${encodeURIComponent(branch)}` : base, commits };
    });
}
