// A small, deterministic 3D-to-ASCII renderer for the terminal banner only.
// Every glyph keeps its front, back, and depth walls at every viewing angle.
type Point2 = readonly [number, number];
type Point3 = readonly [number, number, number];
type Glyph = { width: number; loops: readonly (readonly Point2[])[] };
type FaceKind = "front" | "back" | "top" | "bottom" | "side";
type Face = { loops: Point3[][]; normal: Point3; kind: FaceKind; plane?: Point3 };
export type NamePose = { pitch: number; yaw: number };
export const FORWARD_NAME_POSE: NamePose = { pitch: 25, yaw: 20 };
const DEPTH = 4;
const LETTER_WIDTH_SCALE = 1.35;
const X_SCALE = 1.5;
const Y_SCALE = 1;

// Beveled block outlines with open counters, matching the outlined ASCII style.
const GLYPHS: Record<string, Glyph> = {
  B: { width: 8, loops: [
    [[0,0],[6.5,0],[8,1.5],[8,4.5],[6.5,6],[8,7.5],[8,10.5],[6.5,12],[0,12]],
    [[2,2],[6,2],[6,4.5],[5.5,5],[2,5]],
    [[2,7],[5.5,7],[6,7.5],[6,10],[2,10]],
  ] },
  R: { width: 8.3, loops: [
    [[0,0],[2,0],[2,5],[3.8,5],[6,0],[8.3,0],[5.7,5.3],[8,7.5],[8,10.5],[6.5,12],[0,12]],
    [[2,7],[5.5,7],[6,7.5],[6,10],[2,10]],
  ] },
  I: { width: 6, loops: [
    [[0,0],[6,0],[6,2],[4,2],[4,10],[6,10],[6,12],[0,12],[0,10],[2,10],[2,2],[0,2]],
  ] },
  A: { width: 9, loops: [
    [[0,0],[2.2,0],[3,3],[6,3],[6.8,0],[9,0],[6,12],[3,12]],
    [[3.5,5],[5.5,5],[4.5,9.5]],
  ] },
  N: { width: 8, loops: [
    [[0,0],[2,0],[2,8],[6,0],[8,0],[8,12],[6,12],[6,4],[2,12],[0,12]],
  ] },
  Z: { width: 8, loops: [
    [[0,0],[8,0],[8,2],[2.8,2],[8,10],[8,12],[0,12],[0,10],[5.2,10],[0,2]],
  ] },
  E: { width: 8, loops: [
    [[0,0],[8,0],[8,2],[2,2],[2,5],[6.5,5],[6.5,7],[2,7],[2,10],[8,10],[8,12],[0,12]],
  ] },
  G: { width: 8, loops: [
    [[1.5,0],[8,0],[8,7],[4.5,7],[4.5,5],[6,5],[6,2],[2,2],[2,10],[6,10],[6,9],[8,9],[8,10.5],[6.5,12],[1.5,12],[0,10.5],[0,1.5]],
  ] },
  S: { width: 8, loops: [
    [[1.5,0],[6.5,0],[8,1.5],[8,5],[6.5,6.5],[2,6.5],[2,10],[8,10],[8,12],[1.5,12],[0,10.5],[0,6],[1.5,4.5],[6,4.5],[6,2],[0,2],[0,1.5]],
  ] },
  P: { width: 8, loops: [
    [[0,0],[2,0],[2,5],[6.5,5],[8,6.5],[8,10.5],[6.5,12],[0,12]],
    [[2,7],[5.5,7],[6,7.5],[6,10],[2,10]],
  ] },
  O: { width: 8, loops: [
    [[1.5,0],[6.5,0],[8,1.5],[8,10.5],[6.5,12],[1.5,12],[0,10.5],[0,1.5]],
    [[2,2],[6,2],[6,10],[2,10]],
  ] },
  T: { width: 8, loops: [
    [[0,10],[3,10],[3,0],[5,0],[5,10],[8,10],[8,12],[0,12]],
  ] },
  F: { width: 8, loops: [
    [[0,0],[2,0],[2,5],[6.5,5],[6.5,7],[2,7],[2,10],[8,10],[8,12],[0,12]],
  ] },
  L: { width: 8, loops: [
    [[0,0],[8,0],[8,2],[2,2],[2,12],[0,12]],
  ] },
  "'": { width: 2, loops: [
    [[0,9],[1,9],[2,10.5],[2,12],[0,12]],
  ] },
};

function signedArea(loop: readonly Point2[]) {
  return loop.reduce((sum, [x, y], index) => {
    const next = loop[(index + 1) % loop.length];
    return sum + x * next[1] - next[0] * y;
  }, 0);
}

function rotate([x, y, z]: Point3, pose: NamePose): Point3 {
  const yaw = pose.yaw * Math.PI / 180;
  const pitch = pose.pitch * Math.PI / 180;
  // Tip the tops toward the camera, then turn slightly to reveal the left edge.
  // This order keeps horizontal front edges level as the viewing angle changes.
  const ry = y * Math.cos(pitch) - z * Math.sin(pitch);
  const rz = y * Math.sin(pitch) + z * Math.cos(pitch);
  return [x * Math.cos(yaw) + rz * Math.sin(yaw), ry, -x * Math.sin(yaw) + rz * Math.cos(yaw)];
}

function glyphFaces(glyph: Glyph, pose: NamePose): Face[] {
  const loops = glyph.loops.map((loop, index) => {
    // Widen the letter contours, not the depth or the gaps between letters.
    const points: Point2[] = loop.map(([x,y]) => [x * LETTER_WIDTH_SCALE,y]);
    if ((signedArea(points) > 0) !== (index === 0)) points.reverse();
    return points;
  });
  const vertex = ([x, y]: Point2, z: number): Point3 => {
    const [rx, ry, rz] = rotate([x - glyph.width * LETTER_WIDTH_SCALE / 2, y - 6, z], pose);
    const yaw = pose.yaw * Math.PI / 180, pitch = pose.pitch * Math.PI / 180;
    // An oblique parallel projection keeps front contours upright on the
    // character grid. Rotation still determines the visible depth faces.
    return [(rx - Math.sin(yaw) * Math.tan(pitch) * ry) / Math.cos(yaw), ry / Math.cos(pitch), rz];
  };
  const front = loops.map((loop) => loop.map((point) => vertex(point, DEPTH / 2)));
  const back = loops.map((loop) => loop.map((point) => vertex(point, -DEPTH / 2)));
  const faces: Face[] = [
    { loops: front, normal: rotate([0,0,1], pose), kind: "front" },
    { loops: back, normal: rotate([0,0,-1], pose), kind: "back" },
  ];
  loops.forEach((loop, loopIndex) => loop.forEach(([x, y], index) => {
    const next = (index + 1) % loop.length;
    const [nx, ny] = loop[next];
    const length = Math.hypot(nx - x, ny - y);
    // Outer CCW / counters CW: the solid is always left of the contour.
    const outward: Point3 = [(ny - y) / length, -(nx - x) / length, 0];
    faces.push({
      loops: [[front[loopIndex][index], back[loopIndex][index], back[loopIndex][next], front[loopIndex][next]]],
      normal: rotate(outward, pose),
      kind: outward[1] > .999 ? "top" : outward[1] < -.999 ? "bottom" : "side",
    });
  }));
  return faces.map((face) => {
    const [a,b,c] = face.loops[0];
    const u = b.map((value,index) => value - a[index]);
    const v = c.map((value,index) => value - a[index]);
    return { ...face, plane: [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]] as Point3 };
  });
}

function inLoop(x: number, y: number, loop: readonly Point3[]) {
  let inside = false;
  for (let index = 0, previous = loop.length - 1; index < loop.length; previous = index++) {
    const [ax, ay] = loop[previous], [bx, by] = loop[index];
    const cross = (x - ax) * (by - ay) - (y - ay) * (bx - ax);
    if (Math.abs(cross) < 1e-7 && x >= Math.min(ax,bx) - 1e-7 && x <= Math.max(ax,bx) + 1e-7 && y >= Math.min(ay,by) - 1e-7 && y <= Math.max(ay,by) + 1e-7) return true;
    if ((ay > y) !== (by > y) && x < (bx - ax) * (y - ay) / (by - ay) + ax) inside = !inside;
  }
  return inside;
}

function depthAt(face: Face, x: number, y: number) {
  if (!inLoop(x, y, face.loops[0]) || face.loops.slice(1).some((hole) => inLoop(x, y, hole))) return -Infinity;
  const [px, py, pz] = face.loops[0][0];
  const [nx, ny, nz] = face.plane!;
  return pz - (nx * (x - px) + ny * (y - py)) / nz;
}

export function renderNameGlyph(letter: string, pose: NamePose = FORWARD_NAME_POSE) {
  const glyph = GLYPHS[letter];
  if (!glyph) throw new Error(`Unsupported banner letter: ${letter}`);
  if (!Number.isFinite(pose.pitch) || !Number.isFinite(pose.yaw) || Math.abs(pose.pitch) > 60 || Math.abs(pose.yaw) > 60) throw new Error("Banner angles must be within -60 to 60 degrees.");
  const allFaces = glyphFaces(glyph, pose);
  const visible = allFaces.filter((face) => face.normal[2] > 1e-7);
  const vertices = allFaces.flatMap((face) => face.loops.flat());
  const minX = Math.floor(Math.min(...vertices.map(([x]) => x)) * X_SCALE) - 1;
  const maxX = Math.ceil(Math.max(...vertices.map(([x]) => x)) * X_SCALE) + 1;
  // Shared vertical extent keeps every letter on the same baseline.
  const extentY = 6 + DEPTH / 2 * Math.abs(Math.tan(pose.pitch * Math.PI / 180));
  const minY = Math.floor(-extentY * Y_SCALE) - 1;
  const maxY = Math.ceil(extentY * Y_SCALE) + 1;
  const width = maxX - minX + 1, height = maxY - minY + 1;
  const cells = Array.from({ length: height }, () => Array<string>(width).fill(" "));
  const pixelsByFace: Record<FaceKind, number> = { front: 0, back: 0, top: 0, bottom: 0, side: 0 };

  const nearestAt = (x: number, y: number) => {
    let depth = -Infinity, face: Face | undefined;
    for (const candidate of visible) {
      const candidateDepth = depthAt(candidate, x, y);
      if (candidateDepth > depth) { depth = candidateDepth; face = candidate; }
    }
    return { depth, face };
  };
  for (let row = 0; row < height; row++) for (let column = 0; column < width; column++) {
    const hit = nearestAt((column + minX) / X_SCALE, (maxY - row) / Y_SCALE);
    if (!hit.face) continue;
    pixelsByFace[hit.face.kind]++;
    // Blank fronts still occlude depth walls; only those walls get colon fill.
    cells[row][column] = hit.face.kind === "front" || hit.face.kind === "back" ? " " : ":";
  }
  // Front contours and silhouettes only: adjacent visible depth walls share
  // their colon fill without exposing the extrusion's internal mesh seams.
  const edges = new Map<string, { start: Point3; end: Point3; faces: Face[] }>();
  const vertexKey = (point: Point3) => point.map((value) => value.toFixed(6)).join(",");
  for (const face of allFaces) for (const loop of face.loops) loop.forEach((start, index) => {
    const end = loop[(index + 1) % loop.length];
    const key = [vertexKey(start),vertexKey(end)].sort().join(";");
    const edge = edges.get(key);
    if (edge) edge.faces.push(face);
    else edges.set(key, { start, end, faces: [face] });
  });
  const outlineEdges = [...edges.values()].filter(({ faces }) => {
    const visibleNeighbors = faces.filter((face) => face.normal[2] > 1e-7);
    return visibleNeighbors.some((face) => face.kind === "front") || visibleNeighbors.length === 1;
  });
  const horizontalJoints = new Set(outlineEdges
    .filter(({ start,end }) => Math.abs(end[1] - start[1]) < 1e-7)
    .flatMap(({ start,end }) => [vertexKey(start),vertexKey(end)]));
  const edgePriority = Array.from({ length: height }, () => Array<number>(width).fill(-1));
  for (const { start, end, faces } of outlineEdges) {
    const frontEdge = faces.some((face) => face.kind === "front" && face.normal[2] > 1e-7);
    const dx = (end[0] - start[0]) * X_SCALE, dy = -(end[1] - start[1]) * Y_SCALE;
    const character = Math.abs(dx) < Math.abs(dy) * .3 ? "|" : Math.abs(dy) < Math.abs(dx) * .3 ? "_" : dx * dy > 0 ? "\\" : "/";
    // A baseline underscore would erase the shading in the rest of its cell,
    // leaving a blank strip before the front face. Carry colon fill through
    // shared top/front rims; the outer top silhouette stays outlined.
    const shadedRim = frontEdge && Math.abs(dy) < 1e-7
      && faces.some((face) => face.kind === "top" && face.normal[2] > 1e-7);
    const ink = shadedRim ? ":" : character;
    const upper = start[1] > end[1] ? start : end;
    const capRow = Math.abs(dy) > 1e-7 && horizontalJoints.has(vertexKey(upper))
      ? Math.round(maxY - upper[1] * Y_SCALE) : -1;
    const priority = (frontEdge ? 4 : 0) + (character === "_" ? 0 : 1);
    let column = Math.round(start[0] * X_SCALE - minX), row = Math.round(maxY - start[1] * Y_SCALE);
    const endColumn = Math.round(end[0] * X_SCALE - minX), endRow = Math.round(maxY - end[1] * Y_SCALE);
    const spanX = Math.abs(endColumn - column), spanY = -Math.abs(endRow - row);
    const stepX = column < endColumn ? 1 : -1, stepY = row < endRow ? 1 : -1;
    let error = spanX + spanY;
    for (;;) {
      // Integer Bresenham picks one cell per dominant-axis step. Visibility
      // still uses the closest point on the original, unrounded 3D edge.
      const cellX = (column + minX) - start[0] * X_SCALE;
      const cellY = (maxY - row) - start[1] * Y_SCALE;
      const t = Math.max(0, Math.min(1, (cellX * dx - cellY * dy) / (dx * dx + dy * dy || 1)));
      const point = start.map((value, axis) => value + (end[axis] - value) * t) as unknown as Point3;
      // '_' sits on a character's baseline. Let the cap own its joint row;
      // starting a descending stroke there would stick above the horizontal.
      // The full edge geometry and all lower joints are retained.
      if (row !== capRow && point[2] >= nearestAt(point[0], point[1]).depth - 1e-6 && cells[row]?.[column] !== undefined && priority > edgePriority[row][column]) {
        cells[row][column] = ink;
        edgePriority[row][column] = priority;
      }
      if (column === endColumn && row === endRow) break;
      const twiceError = 2 * error;
      if (twiceError >= spanY) { error += spanY; column += stepX; }
      if (twiceError <= spanX) { error += spanX; row += stepY; }
    }
  }
  let left = 0, right = width - 1;
  while (left < right && cells.every((row) => row[left] === " ")) left++;
  while (right > left && cells.every((row) => row[right] === " ")) right--;
  return {
    rows: cells.map((row) => row.slice(left, right + 1).join("")),
    faceCount: allFaces.length,
    visibleFaces: visible.map((face) => face.kind),
    pixelsByFace,
  };
}

export function renderAsciiText(text: string, pose: NamePose = FORWARD_NAME_POSE) {
  const normalized = text.trim().toUpperCase();
  if (!normalized) return "";
  const words = normalized.split(/\s+/).map((word) => [...word].map((letter) => renderNameGlyph(letter, pose)));
  const rows = words[0][0].rows.map((_, row) => words.map((glyphs) => glyphs.map((glyph) => glyph.rows[row]).join(" ")).join("        ").trimEnd());
  while (rows.length && !rows[0].trim()) rows.shift();
  while (rows.length && !rows.at(-1)!.trim()) rows.pop();
  return rows.join("\n");
}

export function renderAsciiName(pose: NamePose = FORWARD_NAME_POSE) {
  return renderAsciiText("Brian Zeng", pose);
}

export const FORWARD_NAME_ART = renderAsciiName();
export const PORTFOLIO_GREETING = "Brian Zeng's Portfolio";
export const PORTFOLIO_GREETING_ART = renderAsciiText(PORTFOLIO_GREETING);
