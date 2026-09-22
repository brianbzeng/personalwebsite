export type PulseDay = { date: string; count: number };
// Six columns per day-to-day interval: every one of the 28 daily totals has
// an exact plot position instead of being skipped by the sampling grid.
export const PULSE_COLUMNS = 27 * 6 + 1;
export const PULSE_ROWS = 10;
export const PULSE_CYCLE_MS = 6720;

// Shape-preserving Hermite interpolation rounds the joins without averaging
// observations, inventing new peaks, or dipping below zero between days.
export function samplePulseValues(days: PulseDay[]): number[] {
  const values = days.map(({ count }) => Number.isFinite(count) ? Math.max(0, count) : 0);
  const differences = values.slice(1).map((value, index) => value - values[index]);
  const tangents = values.map((_, index) => {
    if (index === 0) return differences[0] ?? 0;
    if (index === values.length - 1) return differences[index - 1] ?? 0;
    const before = differences[index - 1], after = differences[index];
    return before * after > 0 ? 2 * before * after / (before + after) : 0;
  });
  return Array.from({ length: PULSE_COLUMNS }, (_, column) => {
    if (values.length < 2) return values[0] ?? 0;
    const position = column * (values.length - 1) / (PULSE_COLUMNS - 1);
    const index = Math.min(Math.floor(position), values.length - 2);
    const t = position - index, t2 = t * t, t3 = t2 * t;
    const left = values[index], right = values[index + 1];
    const value = (2 * t3 - 3 * t2 + 1) * left + (t3 - 2 * t2 + t) * tangents[index]
      + (-2 * t3 + 3 * t2) * right + (t3 - t2) * tangents[index + 1];
    return Math.max(Math.min(left, right), Math.min(Math.max(left, right), value));
  });
}

// Plot actual daily totals. Only the read-head moves; the data never animates.
export function formatPulseGraph(days: PulseDay[], cursor: number | null): string {
  const maximum = Math.max(1, ...days.map(({ count }) => Number.isFinite(count) ? Math.max(0, count) : 0));
  const labelWidth = Math.max(4, String(maximum).length);
  const grid: string[][] = Array.from({ length: PULSE_ROWS }, () => Array(PULSE_COLUMNS).fill(" "));
  const heights = samplePulseValues(days).map((value) => PULSE_ROWS - 1 - Math.round(value / maximum * (PULSE_ROWS - 1)));
  const strokeRows: number[] = [];
  heights.forEach((row, column) => {
    const next = heights[Math.min(PULSE_COLUMNS - 1, column + 1)];
    // Vertices sit on glyph baselines. Both diagonals belong in the lower
    // cell, so /, \\, and _ meet instead of leaving a one-row gap on rises.
    const strokeRow = Math.max(row, next);
    for (let y = Math.min(row, next) + 1; y < strokeRow; y++) grid[y][column] = "|";
    grid[strokeRow][column] = next < row ? "/" : next > row ? "\\" : "_";
    strokeRows.push(strokeRow);
  });
  const column = cursor === null ? null : Math.max(0, Math.min(PULSE_COLUMNS - 1, Math.floor(Number.isNaN(cursor) ? 0 : cursor)));
  if (column !== null) grid[strokeRows[column]][column] = "o";
  const rows = grid.map((row, index) => {
    const label = index === 0 ? String(maximum) : index === PULSE_ROWS - 1 ? "0" : "";
    return `${label.padStart(labelWidth)} |${row.join("")}|`;
  });
  return [
    `${" ".repeat(labelWidth + 1)}+${"-".repeat(PULSE_COLUMNS)}+`,
    ...rows,
    `${" ".repeat(labelWidth + 1)}+${"-".repeat(PULSE_COLUMNS)}+`,
    `${" ".repeat(labelWidth + 2)}${column === null ? " ".repeat(PULSE_COLUMNS) : " ".repeat(column) + "^" + " ".repeat(PULSE_COLUMNS - column - 1)}`,
  ].join("\n");
}
