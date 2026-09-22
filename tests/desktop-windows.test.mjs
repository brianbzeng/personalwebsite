import test from "node:test";
import assert from "node:assert/strict";
import { pacificClock, calendarMonth, fitFrame, fitFrameToArea, modeFrame, INITIAL_FRAME, INITIAL_NOTES_FRAME } from "../app/components/desktopState.ts";

test("Pacific clock handles daylight saving, standard time, and date boundaries", () => {
  const summer = pacificClock(new Date("2026-09-05T01:00:00Z"));
  assert.equal(summer.time, "6:00 PM"); assert.equal(summer.date, "9/4/2026"); assert.equal(summer.zone, "PDT");
  const winter = pacificClock(new Date("2026-01-02T07:30:00Z"));
  assert.equal(winter.time, "11:30 PM"); assert.equal(winter.date, "1/1/2026"); assert.equal(winter.zone, "PST");
  assert.equal(pacificClock(new Date("2026-11-01T08:30:00Z")).zone, "PDT");
  assert.equal(pacificClock(new Date("2026-11-01T09:30:00Z")).zone, "PST");
});

test("calendar has six complete Sunday-first weeks including leap years", () => {
  const days = calendarMonth(2028, 1);
  assert.equal(days.length, 42); assert.equal(new Set(days.map(d => d.key)).size, 42);
  assert.equal(new Date(days[0].key).getUTCDay(), 0);
  assert.equal(days.filter(d => d.current).length, 29);
});

test("window resize and movement remain inside the workarea", () => {
  for (const x of [-100, 0, .2, 1, 200]) for (const width of [-10, .3, 3]) {
    const frame = fitFrame({x, y:x, width, height:width});
    assert.ok(frame.x >= 0 && frame.y >= 0);
    assert.ok(frame.x + frame.width <= 1 && frame.y + frame.height <= 1);
    assert.ok(frame.width >= .25 && frame.height >= .2);
  }
});

test("maximize and snap preserve the normal restore frame", () => {
  const normal = {...INITIAL_FRAME};
  assert.deepEqual(modeFrame("maximized", normal), {x:0,y:0,width:1,height:1});
  assert.equal(modeFrame("left", normal).width, .5);
  assert.equal(modeFrame("right", normal).x, .5);
  assert.deepEqual(modeFrame("normal", normal), INITIAL_FRAME);
});

test("Notes launches at the compact reference size, remaining usable inside small workareas", () => {
  const reference = fitFrameToArea(INITIAL_NOTES_FRAME, { width: 1918, height: 877 }, { width: 440, height: 300 });
  assert.equal(Math.round(reference.x * 1918), 194);
  assert.equal(Math.round(reference.y * 877 + 28), 316);
  assert.equal(Math.round(reference.width * 1918), 888);
  assert.equal(Math.round(reference.height * 877), 540);
  for (const [width, height] of [[390, 700], [800, 550], [320, 240], [1920, 1052]]) {
    const frame = fitFrameToArea(INITIAL_NOTES_FRAME, { width, height }, { width: 440, height: 300 });
    assert.ok(frame.width * width >= Math.min(width, 440) - 1e-8);
    assert.ok(frame.height * height >= Math.min(height, 300) - 1e-8);
    assert.ok(frame.x >= 0 && frame.y >= 0);
    assert.ok(frame.x + frame.width <= 1 && frame.y + frame.height <= 1);
  }
});
