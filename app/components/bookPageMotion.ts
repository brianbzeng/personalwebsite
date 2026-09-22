/** Offset along the cover's inward normal; the page stays inside the board. */
export function closingPageOffset(opening:number,clearance=.0025){
  const angle=Math.PI*Math.max(0,Math.min(1,opening));
  return {x:clearance*Math.sin(angle),y:clearance*Math.cos(angle)};
}

/** Developable paper curl confined to the lower outside corner; metres. */
export function curlPageCorner(x: number, z: number, width: number, height: number, amount: number) {
  const curvature = Math.PI / (Math.min(width, height) * .30) * Math.max(0, Math.min(1, amount));
  if (curvature < 1e-6) return { x, y: 0, z };
  const d = Math.max(0, .8 * (x - width) - .6 * (z + height / 2) + Math.min(width, height) * .30);
  if (d === 0) return { x, y: 0, z };
  const angle = curvature * d, along = Math.sin(angle) / curvature - d;
  return { x: x + .8 * along, y: -(1 - Math.cos(angle)) / curvature, z: z - .6 * along };
}

/** A rounded diagonal crease travels from the grabbed corner to the spine.
 * Beyond the half-circle bend, paper is a reflected flat flap, never a tube.
 * Canonical coordinates are the right page; mirroring makes the reverse turn.
 */
export function pageTurnVertex(x: number, z: number, width: number, height: number, progress: number, initialCurl: number, direction: -1 | 1) {
  const t=Math.max(0,Math.min(1,progress)), s=t*t*(3-2*t);
  if(t===1)return {x:direction===1?-x:x,y:0,z};
  const reach=.30*Math.min(width,height), b=.6*(1-s), a=Math.sqrt(1-b*b);
  const crease=(.8*width-reach)*(1-s);
  const d=Math.max(0,a*x-b*(z+height/2)-crease);
  const k=(1-s)*Math.PI*Math.max(0,Math.min(1,initialCurl))/reach+s*s/(.15*width*(1-s));
  if(k<1e-6||d===0)return {x:direction*x,y:0,z};
  const angle=Math.min(k*d,Math.PI), tail=Math.max(0,d-Math.PI/k);
  const delta=Math.sin(angle)/k-tail-d;
  return {x:direction*(x+a*delta),y:-(1-Math.cos(angle))/k,z:z-b*delta};
}

export function pageTurnPose(progress: number, direction: -1 | 1) {
  const t = Math.max(0, Math.min(1, progress)), eased = t * t * (3 - 2 * t);
  return { angle: Math.PI * (direction === 1 ? eased : 1 - eased), bend: Math.sin(Math.PI * t) * direction };
}
