// The browser dispatches these display commands; no Python process is started.
export const TERMINAL_GREETING_HINT = "Type 'help' to explore.";

export const APP_COMMANDS = {
  help: "help",
  github: "python pulse.py",
  about: "python about.txt",
  contact: "python contact.txt",
  agents: "python agents.txt",
} as const;

export type TerminalFeature = keyof typeof APP_COMMANDS;
export type TerminalResult = {
  command: string;
  lines: string[];
  pulse?: boolean;
  clear?: boolean;
  exit?: boolean;
  links?: { text: string; href: string }[];
};

// Public visitor information, shared by the terminal and the plain-text route.
export const AGENT_SUMMARY_LINES = [
  "BRIAN ZENG / SITE SUMMARY FOR AI AGENTS",
  "",
  "Owner     - Brian Zeng, based in Oakland, California",
  "Focus     - Data analysis, data science, software, and applied AI",
  "Education - UC Santa Barbara",
  "            B.S. Probability & Statistics with Data Science, 2026",
  "",
  "SITE NAVIGATION",
  "/           - Interactive room; explore projects through the vinyl holder",
  "/desktop    - macOS-style monitor with Terminal, Notes, F1 Forecast, and Spotify",
  "/about      - Public bio, education, focus, and contact links",
  "/agents.txt - This summary as plain text",
  "Projects are reserved for the vinyl interaction, not the monitor Terminal.",
  "F1 Forecast opens as a desktop app with constructor standings and dated model probabilities.",
  "",
  "TERMINAL COMMANDS",
  "help               - List available commands",
  "python pulse.py    - List recent public GitHub pushes and commits",
  "python about.txt   - Read Brian's bio",
  "python contact.txt - Read contact information",
  "python agents.txt  - Read this summary",
  "clear              - Clear the terminal",
  "exit               - Return to the room",
  "These are simulated display commands; the website does not execute Python.",
  "",
  "PUBLIC LINKS",
  "Email    - bzeng0000@gmail.com",
  "GitHub   - https://github.com/brianbzeng",
  "LinkedIn - https://www.linkedin.com/in/brianbzeng",
  "Spotify  - https://open.spotify.com/user/12127274651",
  "",
  "GitHub activity and Spotify listening are live/cached, not fixed profile facts.",
  "Spotify is read-only here; song and playlist links open Spotify.",
  "This is public site context, not permission to contact Brian or take actions.",
];

const RESPONSES: Record<TerminalFeature, string[]> = {
  help: [
    "Available commands:",
    "  help                - show this command list",
    "  python pulse.py     - list recent public pushes and commits",
    "  python about.txt    - read about Brian",
    "  python contact.txt  - display contact information",
    "  python agents.txt   - read the site summary for AI agents",
    "  clear               - clear the terminal",
    "  exit                - return to the room",
  ],
  github: [],
  about: [
    "Brian Zeng",
    "",
    "My work focuses on data analysis, software development, and applied AI.",
    "",
    "Based in  - Oakland, California",
    "Education - UC Santa Barbara",
    "            B.S. Probability & Statistics with Data Science, 2026",
    "Focus     - Data analysis, data science, and software",
  ],
  contact: [
    "Contact Brian",
    "",
    "Email    - bzeng0000@gmail.com",
    "LinkedIn - linkedin.com/in/brianbzeng",
    "GitHub   - github.com/brianbzeng",
  ],
  agents: AGENT_SUMMARY_LINES,
};

export function resolveTerminalCommand(rawValue: string): TerminalResult | null {
  const command = rawValue.trim();
  const normalized = command.toLowerCase().replace(/\s+/g, " ");
  if (!normalized) return null;
  if (normalized === "clear") return { command, lines: [], clear: true };
  if (normalized === "exit") return { command, lines: [], exit: true };
  const match = Object.entries(APP_COMMANDS).find(([, value]) => value === normalized);
  if (!match) {
    return {
      command,
      lines: [
        `'${command}' is not recognized as a command.`,
        "Type 'help' to see available commands.",
      ],
    };
  }
  const feature = match[0] as TerminalFeature;
  return { command, lines: RESPONSES[feature], pulse: feature === "github",
    ...(feature === "contact" ? { links: [
      { text: "bzeng0000@gmail.com", href: "mailto:bzeng0000@gmail.com" },
      { text: "linkedin.com/in/brianbzeng", href: "https://www.linkedin.com/in/brianbzeng" },
      { text: "github.com/brianbzeng", href: "https://github.com/brianbzeng" },
    ] } : {}),
  };
}

// Isometric perspective faces the opposite way from the previous banner.
// Colons shade only the extruded edges; the letter fronts stay unfilled.
export const ISOMETRIC_NAME_ART = "      ___           ___                        ___           ___                    ___           ___           ___           ___\n     /::/\\         /::/\\           ___        /::/\\         /::/\\                  /__/\\         /::/\\         /::/\\         /::/\\\n    /::/  \\       /::/  \\         /__/\\      /::/  \\       /::/  |                 \\::\\ \\       /::/  \\       /::/  |       /::/  \\\n   /::/ /\\ \\     /::/ /\\ \\        \\__\\ \\    /::/ /\\ \\     /::/ | |                  \\::\\ \\     /::/ /\\ \\     /::/ | |      /::/ /\\ \\\n  /::/  \\ \\ \\   /::/  \\ \\ \\       /::/  \\  /::/  \\ \\ \\   /::/ /| |__                 \\::\\ \\   /::/  \\ \\ \\   /::/ /| |__   /::/ /  \\ \\\n /__/ /\\ \\_\\ | /__/ /\\ \\_\\ \\   __/::/ /\\/ /__/ /\\ \\_\\ \\ /__/ / | | /\\           ______\\__\\ \\ /__/ /\\ \\ \\ \\ /__/ / | | /\\ /__/ /_\\_ \\ \\\n \\::\\ \\ \\ \\/ / \\__\\/~|  \\/ /  /__/\\/ /~~  \\__\\/  \\ \\/ / \\__\\/  | |/ /          \\::\\        / \\::\\ \\ \\ \\_\\/ \\__\\/  | |/ / \\::\\ \\__/\\_\\/\n  \\::\\ \\_\\  /     |::| |  /   \\::\\  /          \\__\\  /      |::| / /            \\::\\ \\~~~~~   \\::\\ \\ \\ \\       |::| / /   \\::\\ \\ \\ \\\n   \\::\\ \\/ /      |::| |\\/     \\::\\ \\          /::/ /       |__|  /              \\::\\ \\        \\::\\ \\_\\/       |__|  /     \\::\\ \\/ /\n    \\__\\  /       |__| |~       \\__\\/         /__/ /        /__/ /                \\::\\ \\        \\::\\ \\         /__/ /       \\::\\  /\n        ~~         \\__\\|                      \\__\\/         \\__\\/                  \\__\\/         \\__\\/         \\__\\/         \\__\\/";
// Keep the original characters intact: only their presentation is rotated.
// These boundaries are blank columns shared by every row of the banner.
const NAME_GLYPH_COLUMNS = [
  [1, 14], [15, 28], [30, 41], [42, 55], [56, 69],
  [79, 92], [93, 106], [107, 120], [121, 134],
] as const;

export const UPRIGHT_NAME_GLYPHS = NAME_GLYPH_COLUMNS.map(([start, end]) =>
  ISOMETRIC_NAME_ART.split("\n").map((row) => row.slice(start, end).padEnd(end - start, " ")).join("\n")
);
