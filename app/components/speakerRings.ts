/** Eighteen smooth, closed wave silhouettes: ovals, rounded lobes and uneven rings. */
export const SPEAKER_RING_COUNT = 18;
export function speakerRingPoints(shape: number) {
  const phase = shape * 2.399963, lobes = 2 + shape % 4;
  const points = Array.from({ length: 24 }, (_, i) => {
    const a = i * Math.PI * 2 / 24;
    const radius = 10 * (1 + (.075 + (shape % 3) * .035) * Math.sin(lobes * a + phase)
      + .045 * Math.cos((lobes + 1) * a - phase * .7));
    const stretch = .92 + (shape % 5) * .04;
    return { x: Math.cos(a) * radius * stretch, y: Math.sin(a) * radius / stretch };
  });
  const center = points.reduce((sum, p) => ({ x: sum.x + p.x / points.length, y: sum.y + p.y / points.length }), { x: 0, y: 0 });
  return points.map(p => ({ x: p.x - center.x, y: p.y - center.y }));
}
export function speakerRingPath(shape: number) {
  const p = speakerRingPoints(shape), n = p.length;
  const f = (x: number) => x.toFixed(3);
  let d = `M ${f(p[0].x)} ${f(p[0].y)}`;
  for (let i = 0; i < n; i++) {
    const a = p[(i + n - 1) % n], b = p[i], c = p[(i + 1) % n], e = p[(i + 2) % n];
    d += ` C ${f(b.x + (c.x - a.x) / 6)} ${f(b.y + (c.y - a.y) / 6)} ${f(c.x - (e.x - b.x) / 6)} ${f(c.y - (e.y - b.y) / 6)} ${f(c.x)} ${f(c.y)}`;
  }
  return d + " Z";
}
export const SPEAKER_RING_PATHS = Array.from({ length: SPEAKER_RING_COUNT }, (_, i) => speakerRingPath(i));

/** Shuffle bag: exhaust the pool before reusing a shape, no repeat at refill. */
export function createRingPicker(random = Math.random) {
  let bag: number[] = [], previous = -1;
  return () => {
    if (!bag.length) {
      bag = Array.from({ length: SPEAKER_RING_COUNT }, (_, i) => i);
      for (let i = bag.length - 1; i > 0; i--) {
        const j = Math.floor(random() * (i + 1)); [bag[i], bag[j]] = [bag[j], bag[i]];
      }
      if (bag[bag.length - 1] === previous) [bag[0], bag[bag.length - 1]] = [bag[bag.length - 1], bag[0]];
    }
    previous = bag.pop()!; return previous;
  };
}
