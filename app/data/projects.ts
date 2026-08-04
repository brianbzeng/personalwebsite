export type ProjectRecord = {
  slug: string;
  number: string;
  title: string;
  category: string;
  year: string;
  accent: string;
  shortLabel: string;
  summary: string;
  description: string;
  role: string;
  stack: string[];
  outcomes: string[];
  learnings: string[];
  futureAdditions: string[];
  liveUrl: string;
  githubUrl: string;
};

export const PROJECTS: ProjectRecord[] = [
  {
    slug: "castingcompass",
    number: "01",
    title: "CastingCompass",
    category: "FULL-STACK GEOSPATIAL ML",
    year: "2026",
    accent: "#ff5b45",
    shortLabel: "Halibut planner",
    summary: "A production fishing planner that turns messy ocean, weather, bathymetry, and trip data into explainable opportunities.",
    description: "CastingCompass helps anglers decide where and when to fish for California halibut. The product combines public environmental data, first-party trip reports, and model outputs into a practical, mobile-first planning loop.",
    role: "Product engineer, data scientist, and platform owner",
    stack: ["Next.js", "TypeScript", "Cloudflare Workers", "D1", "Python", "PyTorch", "Rasterio"],
    outcomes: ["47 public spots", "72-hour forecasts", "Full-stack ML + MLOps"],
    learnings: ["Explainability is a product feature when a model influences a real-world decision.", "Spatial validation matters more than a single impressive holdout score."],
    futureAdditions: ["Personalized trip planning", "More historical catch data", "A richer offline map mode"],
    liveUrl: "https://castingcompass.com",
    githubUrl: "https://github.com/brianbzeng/castingcompass",
  },
  {
    slug: "nba-odds-predictor",
    number: "02",
    title: "NBA Odds Predictor",
    category: "SPORTS ANALYTICS / LIVE APP",
    year: "2025",
    accent: "#35d0ff",
    shortLabel: "Game forecast model",
    summary: "NBA game forecasts using margin-adjusted Elo ratings, recent form, rest, and injury data.",
    description: "A compact forecasting system designed to make model assumptions visible. The interface turns a game-level estimate into a readable board instead of hiding the reasoning behind a single probability.",
    role: "Model builder and interface designer",
    stack: ["Python", "Pandas", "scikit-learn", "SQL", "Next.js", "Data visualization"],
    outcomes: ["1,321 games tracked", "30 teams", "64.8% benchmark"],
    learnings: ["A model becomes more useful when uncertainty is easy to inspect.", "Small, legible interfaces make analytical work easier to critique."],
    futureAdditions: ["Player-level lineup adjustments", "Calibration diagnostics", "Historical matchup explorer"],
    liveUrl: "https://nba.brianbzeng.com",
    githubUrl: "https://github.com/brianbzeng/nbamodel",
  },
  {
    slug: "amazon-review-audit",
    number: "03",
    title: "Amazon Review Suspicion Audit",
    category: "NLP / HUMAN-REVIEW TRIAGE",
    year: "2025",
    accent: "#f1ce4b",
    shortLabel: "Review triage",
    summary: "An interpretable NLP pipeline that prioritizes suspicious reviews for human inspection without claiming to prove deception.",
    description: "This audit explores how text signals, metadata, and blinded LLM review can work together as a triage tool. The design keeps the human reviewer in the loop and makes each signal inspectable.",
    role: "Researcher and evaluation designer",
    stack: ["Python", "TF-IDF", "NLP", "OpenAI-compatible APIs", "LLM evaluation"],
    outcomes: ["900-review audit", "TF-IDF + behavioral signals", "Blinded LLM review"],
    learnings: ["Suspicion is a ranking problem, not a binary truth label.", "Blinding and explicit limits improve the credibility of an audit."],
    futureAdditions: ["Reviewer agreement analysis", "Cross-category evaluation", "A reproducible labeling console"],
    liveUrl: "https://github.com/brianbzeng/amazonmodel",
    githubUrl: "https://github.com/brianbzeng/amazonmodel",
  },
  {
    slug: "ttb-label-review-assistant",
    number: "04",
    title: "TTB Label Review Assistant",
    category: "APPLIED AI / DECISION SUPPORT",
    year: "2025",
    accent: "#a985ff",
    shortLabel: "Evidence extraction",
    summary: "AI-assisted alcohol-label review with commodity-aware rules, evidence extraction, and human-in-the-loop workflows.",
    description: "A workflow prototype for turning long label submissions into a structured review queue. The assistant helps surface evidence and rules while keeping the final decision with a human reviewer.",
    role: "Applied AI engineer and workflow designer",
    stack: ["Python", "LLM-assisted extraction", "Rule systems", "Evidence review", "Quarto"],
    outcomes: ["3 human-review workflows", "Commodity-aware rules", "Evidence-first output"],
    learnings: ["Good AI tooling narrows the search space without hiding the source material.", "Workflow design often matters as much as model quality."],
    futureAdditions: ["Document upload pipeline", "Reviewer feedback loops", "Expanded commodity rule coverage"],
    liveUrl: "https://treasury.brianbzeng.com",
    githubUrl: "https://github.com/brianbzeng/treasurytakehome",
  },
  {
    slug: "f1-constructors-forecast",
    number: "05",
    title: "F1 Constructors Forecast",
    category: "INTERACTIVE MODEL / SIMULATION",
    year: "2026",
    accent: "#64ef7f",
    shortLabel: "Race simulation",
    summary: "An in-season Ridge model that turns current constructor performance into probability-weighted championship scenarios.",
    description: "The F1 forecast is a small, honest model lab: it surfaces the inputs, the uncertainty, and the limits of a simulation rather than presenting a prediction as a fact.",
    role: "Data scientist and technical communicator",
    stack: ["Python", "FastF1", "Ridge regression", "Monte Carlo simulation", "Data visualization"],
    outcomes: ["In-season updates", "Residual simulations", "Constructor leaderboard"],
    learnings: ["A useful forecast explains what changed since the last update.", "Model limits belong beside the headline number."],
    futureAdditions: ["Driver-level scenarios", "Pit strategy features", "Race-by-race narrative notes"],
    liveUrl: "https://github.com/brianbzeng/f1model",
    githubUrl: "https://github.com/brianbzeng/f1model",
  },
];

export function getProject(slug: string) {
  return PROJECTS.find((project) => project.slug === slug);
}
