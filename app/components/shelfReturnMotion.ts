import timing from '../data/shelf-return.json';

export const RETURN_TIMING={...timing,revealStart:timing.panStart+timing.panDuration};
export const RETURN_SECONDS=RETURN_TIMING.revealStart+timing.revealDuration+timing.insertDuration;
const smooth=(v:number)=>{const t=Math.max(0,Math.min(1,v));return t*t*(3-2*t);};

/** The Blender return plate reads the same timing data. */
export function shelfReturnPose(t:number){
  return {
    camera:smooth(1-(t-timing.panStart)/timing.panDuration),
    armFrame:122-32*Math.min(1,Math.max(0,t/timing.armDuration)),
    lift:smooth((t-timing.liftStart)/timing.liftDuration),
    discOpacity:1-smooth((t-timing.fadeStart)/timing.fadeDuration),
    coverOpacity:smooth((t-RETURN_TIMING.revealStart)/timing.revealDuration),
    insert:smooth((t-RETURN_TIMING.revealStart-timing.revealDuration)/timing.insertDuration),
  };
}
