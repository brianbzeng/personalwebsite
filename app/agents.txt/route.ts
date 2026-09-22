import { AGENT_SUMMARY_LINES } from "../components/terminalContent";

export function GET() {
  return new Response(`${AGENT_SUMMARY_LINES.join("\n")}\n`, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
