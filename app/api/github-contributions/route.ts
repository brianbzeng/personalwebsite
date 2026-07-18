const GITHUB_USERNAME = "brianbzeng";
const ACTIVITY_DAYS = 28;

type ContributionDay = {
  date: string;
  count: number;
};

function dateKey(date: Date) {
  return date.toISOString().slice(0, 10);
}

function emptyWindow() {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Los_Angeles",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  const today = new Date(`${value.year}-${value.month}-${value.day}T00:00:00Z`);

  return Array.from({ length: ACTIVITY_DAYS }, (_, index) => {
    const day = new Date(today);
    day.setUTCDate(today.getUTCDate() - (ACTIVITY_DAYS - 1 - index));
    return { date: dateKey(day), count: 0 };
  });
}

export async function GET() {
  try {
    const windowDays = emptyWindow();
    const years = [...new Set(windowDays.map((day) => day.date.slice(0, 4)))];
    const responses = await Promise.all(
      years.map(async (year) => {
        const response = await fetch(
          `https://github.com/users/${GITHUB_USERNAME}/contributions?from=${year}-01-01&to=${year}-12-31`,
          {
            headers: {
              Accept: "text/html",
              "User-Agent": "brian-zeng-portfolio",
            },
          },
        );

        if (!response.ok) {
          throw new Error(`GitHub responded with ${response.status}`);
        }

        return response.text();
      }),
    );

    const counts = new Map<string, number>();
    const dayPattern = /data-date="(\d{4}-\d{2}-\d{2})"[\s\S]*?<tool-tip[^>]*>(No|[\d,]+) contributions? on/g;

    for (const html of responses) {
      for (const match of html.matchAll(dayPattern)) {
        counts.set(match[1], match[2] === "No" ? 0 : Number(match[2].replaceAll(",", "")));
      }
    }

    const daily: ContributionDay[] = windowDays.map((day) => ({
      ...day,
      count: counts.get(day.date) ?? 0,
    }));

    if (counts.size === 0) {
      throw new Error("GitHub contribution calendar could not be parsed");
    }

    return Response.json(
      { daily },
      { headers: { "Cache-Control": "public, max-age=300, s-maxage=1800" } },
    );
  } catch {
    return Response.json({ error: "Unable to load GitHub contributions" }, { status: 502 });
  }
}
