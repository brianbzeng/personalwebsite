export function dragVinyl(turn: number, tilt: number, dx: number, dy: number) {
  // Upward dragging tips the top edge toward the viewer.
  return { turn: turn + dx * .012, tilt: Math.max(-.7, Math.min(.7, tilt - dy * .008)) };
}
export function snapVinylFace(turn: number) {
  // Opposite of the nearest face, with all free-drag tilt reset.
  return { turn: (Math.round(turn / Math.PI) + 1) * Math.PI, tilt: 0 };
}
