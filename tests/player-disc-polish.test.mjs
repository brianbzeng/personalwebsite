import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const player = readFileSync(new URL("../app/components/shelfRecordPlayer.ts", import.meta.url), "utf8");

test("disc surfaces join the tonearm sweep band and carry a radial sheen", () => {
  assert.match(player, /DISC_SURFACE=\/\^\(V138_Player_Platter\|V138_Platter_Rim\|V138_Playback_Record\|V148_LabelMark\|V138_Groove_\|V138_Spindle\)\//);
  // The default band matches the authored sweep exactly, so one light pass moves in step.
  const model = JSON.parse(readFileSync(new URL("../public/review/v138/player.json", import.meta.url), "utf8"));
  const authored = model.meshes.flatMap((part) => part.materials).find((material) => material.sweep).sweep;
  const band = player.match(/const DISC_SWEEP=\{axis:\[(\d),(\d),(\d)\],min:([\d.]+),span:([\d.]+),start:(\d+),duration:(\d+),cycle:(\d+)/);
  assert.ok(band, "DISC_SWEEP present");
  assert.equal(Number(band[1]), authored.axis[0]);
  assert.equal(Number(band[4]), authored.min);
  assert.equal(Number(band[5]), authored.span);
  assert.equal(Number(band[6]), authored.start);
  assert.equal(Number(band[7]), authored.duration);
  assert.equal(Number(band[8]), authored.cycle);
  assert.match(player, /const sweep=item\.sweep\?\?\(DISC_SURFACE\.test\(part\.name\)\?DISC_SWEEP:undefined\)/);
  // Rotation-invariant sheen uses object-space radius; the label gains visible contrast.
  assert.match(player, /DISC_SHEEN:Record<string,number>=\{'V138_Playback_Record':\.12,'V148_LabelMark':\.024\}/);
  assert.match(player, /discR=clamp\(length\(discLocal\.xy\)\/\$\{sheen\},0\.0,1\.0\)/);
  assert.match(player, /V148_LabelMark'\)for\(const material of materials\)material\.color\.setRGB\(\.14,\.14,\.14\)/);
  // Sheen materials use a distinct program cache; sweep-only parts keep the v145 key.
  assert.match(player, /sheen\?'shelf-player-disc-v157':'shelf-player-sweep-v145'/);
});

test("retouched plates carry a cache-busting revision so cached black discs refresh", () => {
  const panHandoff = readFileSync(new URL("../app/components/panHandoff.ts", import.meta.url), "utf8");
  const room = readFileSync(new URL("../app/components/CinematicRoom.tsx", import.meta.url), "utf8");
  const staging = readFileSync(new URL("../app/components/shelfPlaybackStaging.ts", import.meta.url), "utf8");
  for (const source of [panHandoff, room, staging]) assert.match(source, /\?v=157/);
  assert.match(panHandoff, /vinyl-background\.webp\?v=157/);
});

test("the staging route reviews the polish without touching the main experience", () => {
  const route = readFileSync(new URL("../app/review/player-polish/page.tsx", import.meta.url), "utf8");
  assert.match(route, /initialCubby=\{1\}/);
  assert.match(route, /BookshelfExperience/);
  const home = readFileSync(new URL("../app/page.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(home, /player-polish/);
});
