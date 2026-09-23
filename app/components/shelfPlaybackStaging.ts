import type * as Three from 'three';
import {RECORD_RIG, type PlayerModel, createShelfPlayer} from './shelfRecordPlayer';
import {RETURN_SECONDS,RETURN_TIMING,shelfReturnPose} from './shelfReturnMotion';
export {RETURN_SECONDS} from './shelfReturnMotion';

const smooth=(v:number)=>{const t=Math.max(0,Math.min(1,v));return t*t*(3-2*t);};

export async function loadPlaybackFilms(){
  const make=async(name:string)=>{
    const video=document.createElement('video');video.muted=true;video.playsInline=true;video.preload='auto';
    video.src=name==='return'?'/room/v158/return-background.mp4':`/room/v156/${name}-background.mp4`;
    await new Promise<void>((resolve,reject)=>{
      const timer=setTimeout(()=>{cleanup();reject(new Error('Playback preview unavailable'));},20000);
      const cleanup=()=>{clearTimeout(timer);video.removeEventListener('loadeddata',ready);video.removeEventListener('error',failed);};
      const ready=()=>{cleanup();resolve();};const failed=()=>{cleanup();reject(new Error('Playback preview unavailable'));};
      video.addEventListener('loadeddata',ready);video.addEventListener('error',failed);video.load();
    });return video;
  };
  const image=async(name:string)=>{const value=new Image();value.src=`/room/v156/${name}.webp${name==='vinyl-background'?'?v=157':''}`;await value.decode();return value;};
  const [play,back,first,last]=await Promise.all([make('playback'),make('return'),image('vinyl-background'),image('playback-end')]);
  return {play,back,first,last,dispose(){for(const video of [play,back]){video.pause();video.removeAttribute('src');video.load();}}};
}

/** Original camera and actor samples; only the full-room background is rerendered. */
export function startRestoredPlayback(T:typeof Three,player:Awaited<ReturnType<typeof createShelfPlayer>>,model:PlayerModel,
  renderer:Three.WebGLRenderer,source:Three.Scene,camera:Three.PerspectiveCamera,sleeve:Three.Group,record:Three.Group,
  films:Awaited<ReturnType<typeof loadPlaybackFilms>>,reduced:boolean,done:()=>void,
  shelfPose:{position:Three.Vector3;quaternion:Three.Quaternion}){
  source.updateMatrixWorld(true);
  const recordParent=record.parent!,recordLocal=record.position.clone(),recordLocalQ=record.quaternion.clone();
  const sleevePosition=sleeve.position.clone(),sleeveQuaternion=sleeve.quaternion.clone();
  const sleeveScale=sleeve.scale.clone(),recordStartScale=record.getWorldScale(new T.Vector3());
  const cameraPosition=camera.position.clone(),cameraQuaternion=camera.quaternion.clone(),cameraFov=camera.fov;
  const endPosition=new T.Vector3().fromArray(model.camera.position),endQ=new T.Quaternion().fromArray(model.camera.quaternion);
  const recordStart=record.getWorldPosition(new T.Vector3()),recordStartQ=record.getWorldQuaternion(new T.Quaternion());
  const first=new T.Object3D();player.pose(RECORD_RIG,1,first);
  const offset=recordStart.clone().sub(first.position),rotationOffset=recordStartQ.clone().multiply(first.quaternion.clone().invert());
  const right=new T.Vector3(1,0,0).applyQuaternion(cameraQuaternion);
  const exit=-Math.sign(new T.Vector3(1,0,0).applyQuaternion(sleeveQuaternion).dot(right)||1);
  const foreground=new T.Scene();foreground.attach(sleeve);foreground.attach(record);
  const movies=[films.play,films.back],textures=movies.map(v=>{const t=new T.VideoTexture(v);t.colorSpace=T.SRGBColorSpace;return t;});
  const stills=[films.first,films.last].map(image=>{const t=new T.Texture(image);t.colorSpace=T.SRGBColorSpace;t.needsUpdate=true;return t;});
  const targets=[new T.WebGLRenderTarget(1,1,{samples:4}),new T.WebGLRenderTarget(1,1,{samples:4})];
  const quadScene=new T.Scene(),quadCamera=new T.OrthographicCamera(-1,1,1,-1,0,1),geometry=new T.PlaneGeometry(2,2);
  const uniforms={a:{value:textures[0] as Three.Texture},b:{value:textures[0] as Three.Texture},mixValue:{value:0},videoInput:{value:1}};
  const material=new T.ShaderMaterial({depthTest:false,depthWrite:false,toneMapped:false,uniforms,
    vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}',
    fragmentShader:'varying vec2 vUv;uniform sampler2D a,b;uniform float mixValue,videoInput;void main(){vec4 color=mix(texture2D(a,vUv),texture2D(b,vUv),mixValue);if(videoInput>.5){color.rgb=mix(pow((color.rgb+.055)/1.055,vec3(2.4)),color.rgb/12.92,lessThanEqual(color.rgb,vec3(.04045)));}gl_FragColor=color;\n#include <colorspace_fragment>\n}'});
  quadScene.add(new T.Mesh(geometry,material));
  let active=true,mode:0|1=0,decoded=0,completed=false,sounded=false,finishReturn:(()=>void)|null=null;
  let movieReady=false,mediaFailed=false,epoch=0,holdStart=0,returned=false;
  const began=performance.now();let returnBegan=0;
  const recordRest=new T.Vector3(),recordRestQ=new T.Quaternion();
  let audio:AudioContext|null=null;
  try{audio=new AudioContext();void audio.resume();}catch{/* Optional sound. */}
  const callbacks=new Map<HTMLVideoElement,number>();
  function watch(video:HTMLVideoElement,token:number){if(typeof video.requestVideoFrameCallback==='function'){const id=video.requestVideoFrameCallback((_now,meta)=>{if(!active||token!==epoch)return;if(video===movies[mode]){decoded=meta.mediaTime;movieReady=true;}watch(video,token);});callbacks.set(video,id);}}
  function playMovie(index:0|1){
    const token=++epoch;movies.forEach(v=>{v.pause();const id=callbacks.get(v);if(id!==undefined)v.cancelVideoFrameCallback(id);});
    mode=index;decoded=0;movieReady=false;mediaFailed=false;if(reduced)return;
    const video=movies[index];
    const begin=()=>{if(!active||token!==epoch)return;watch(video,token);void video.play().catch(()=>{if(active&&token===epoch){mediaFailed=true;movieReady=false;}});};
    if(video.currentTime>.001){video.addEventListener('seeked',begin,{once:true});video.currentTime=0;}else begin();
  }
  playMovie(0);
  function cameraAt(weight:number){
    camera.position.copy(cameraPosition).lerp(endPosition,weight);camera.quaternion.copy(cameraQuaternion).slerp(endQ,weight);
    camera.fov=cameraFov+(model.camera.fov-cameraFov)*weight;camera.updateProjectionMatrix();
  }
  function composite(opacity:number,fading:'sleeve'|'record'='sleeve'){
    const size=renderer.getDrawingBufferSize(new T.Vector2());size.multiplyScalar(Math.min(1.5,2560/size.x,1440/size.y)).floor();
    for(const target of targets)if(target.width!==size.x||target.height!==size.y)target.setSize(size.x,size.y);
    for(let i=0;i<2;i++){
      const useVideo=!reduced&&!mediaFailed&&movieReady;
      const background=useVideo?textures[mode]:stills[reduced||mediaFailed?(mode===0?1:0):mode];
      uniforms.a.value=background;uniforms.b.value=background;uniforms.mixValue.value=0;uniforms.videoInput.value=useVideo?1:0;
      renderer.setRenderTarget(targets[i]);renderer.render(quadScene,quadCamera);
      renderer.autoClear=false;renderer.clearDepth();renderer.render(source,camera);
      sleeve.visible=fading==='sleeve'&&i===1&&opacity>0;
      record.visible=fading==='record'?i===1&&opacity>0:mode===0;
      renderer.render(foreground,camera);renderer.autoClear=true;
    }
    uniforms.a.value=targets[0].texture;uniforms.b.value=targets[1].texture;uniforms.mixValue.value=opacity;uniforms.videoInput.value=0;
    renderer.setRenderTarget(null);renderer.render(quadScene,quadCamera);
  }
  function draw(now:number){
    if(!active)return;
    const video=movies[mode],seconds=typeof video.requestVideoFrameCallback==='function'?decoded:video.currentTime;
    if(typeof video.requestVideoFrameCallback!=='function'&&!video.seeking&&video.readyState>=2)movieReady=true;
    if(mode===0){
      const frame=reduced||mediaFailed?138:Math.min(138,1+seconds*model.fps),flight=smooth((frame-42)/46);
      cameraAt(flight);player.update(frame,(now-began)/1000);player.pose(RECORD_RIG,frame,record);
      // A mobile inspection may be scaled down. Preserve its first frame and
      // grow the detached disc to its physical platter size along the flight.
      record.scale.copy(recordStartScale).lerp(new T.Vector3(1,1,1),flight);
      record.position.addScaledVector(offset,1-flight);record.quaternion.premultiply(rotationOffset.clone().slerp(new T.Quaternion(),flight));
      if(video.ended&&!reduced){if(!holdStart)holdStart=now;record.quaternion.premultiply(new T.Quaternion().setFromAxisAngle(new T.Vector3(0,0,1),-(now-holdStart)/1000*Math.PI*2*(100/3)/60));}
      sleeve.position.copy(sleevePosition).addScaledVector(right,exit*.31*smooth((frame-1)/41));
      composite(1-smooth((frame-5.8)/43));
      if(frame>=122&&!sounded){sounded=true;if(audio){const buffer=audio.createBuffer(1,Math.floor(audio.sampleRate*.07),audio.sampleRate),data=buffer.getChannelData(0);for(let i=0;i<data.length;i++)data[i]=(Math.random()*2-1)*Math.exp(-i/(audio.sampleRate*.012));const noise=audio.createBufferSource(),filter=audio.createBiquadFilter(),gain=audio.createGain();noise.buffer=buffer;filter.frequency.value=1900;gain.gain.value=.065;noise.connect(filter).connect(gain).connect(audio.destination);noise.start();}}
      if((frame>=138||video.ended)&&!completed){completed=true;done();}
    }else{
      // A stalled/short clip must paint the final pose before resolving, too.
      if((now-returnBegan)>(RETURN_SECONDS+5)*1000)mediaFailed=true;
      const t=reduced||mediaFailed||(movieReady&&video.ended)?RETURN_SECONDS:seconds;
      const returning=shelfReturnPose(t);
      cameraAt(returning.camera);
      // Reverse the actual 90–122 arm samples, not the entire 138-frame clip:
      // lift the stylus, swing around its anchored pivot, lower onto the rest.
      player.update(returning.armFrame,(now-began)/1000);
      record.position.copy(recordRest);record.position.z+=returning.lift*.16;
      record.quaternion.copy(recordRestQ);
      if(t<RETURN_TIMING.revealStart)composite(returning.discOpacity,'record');
      else {
        // The disc has gone. Only the aligned cover returns to its own slot;
        // never bring the viewer back to the resleeving/inspection pose.
        sleeve.position.copy(shelfPose.position).add(new T.Vector3(-.32*(1-returning.insert),0,0));
        sleeve.scale.setScalar(1);
        sleeve.quaternion.copy(shelfPose.quaternion);composite(returning.coverOpacity);
      }
      if(t>=RETURN_SECONDS&&finishReturn){returned=true;const finish=finishReturn;finishReturn=null;finish();}
    }
  }
  function returnToShelf(){
    return new Promise<void>(resolve=>{finishReturn=resolve;recordRest.copy(record.position);recordRestQ.copy(record.quaternion);returnBegan=performance.now();playMovie(1);});
  }
  function stop(){
    active=false;epoch++;movies.forEach(v=>{v.pause();const id=callbacks.get(v);if(id!==undefined)v.cancelVideoFrameCallback(id);});
    source.attach(sleeve);sleeve.position.copy(returned?shelfPose.position:sleevePosition);sleeve.quaternion.copy(returned?shelfPose.quaternion:sleeveQuaternion);sleeve.visible=true;
    if(returned)sleeve.scale.setScalar(1);else sleeve.scale.copy(sleeveScale);
    recordParent.add(record);record.position.copy(recordLocal);record.quaternion.copy(recordLocalQ);record.scale.setScalar(1);record.visible=true;
    player.update(1,0);camera.position.copy(cameraPosition);camera.quaternion.copy(cameraQuaternion);camera.fov=cameraFov;camera.updateProjectionMatrix();
    targets.forEach(t=>t.dispose());[...textures,...stills].forEach(t=>t.dispose());geometry.dispose();material.dispose();void audio?.close();renderer.setRenderTarget(null);renderer.autoClear=true;finishReturn?.();finishReturn=null;
  }
  return {draw,stop,returnToShelf};
}
