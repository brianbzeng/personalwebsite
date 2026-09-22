"use client";

import { useEffect, useRef, useState } from 'react';
import './review.css';

type View = 'player' | 'hardback' | 'paperback' | 'stack' | 'photos';
type Pose = { matrix: number[]; opacity: number };
type Sweep = { axis: number[]; min: number; span: number; start: number; duration: number; cycle: number; color: number[] };
type Mesh = { name: string; rig: string | null; positions: number[]; bent?: number[]; uvs: number[]; indices: number[]; groups: { start: number; count: number; materialIndex: number }[]; materials: { color: number[]; texture: string | null; unlit?: boolean; frontSide?: boolean; roughness?: number; sweep?: Sweep; grayscale?: boolean }[] };
type Model = { frames: number; fps: number; meshes: Mesh[]; samples: Record<string, Pose>[]; camera: { position: number[]; quaternion: number[]; fov: number } };
type Controls = { frame: (value: number) => void; angle: (angled: boolean) => void };

function ReviewCanvas({ view, onReady, onFailure, onDisc, onBookAction, controls }: { view: View; onReady: () => void; onFailure: () => void; onDisc: () => void; onBookAction: (action: 'open' | 'previous' | 'next') => void; controls: React.MutableRefObject<Controls | null> }) {
  const host = useRef<HTMLDivElement>(null), latest = useRef({ onReady, onFailure, onDisc, onBookAction }); latest.current = { onReady, onFailure, onDisc, onBookAction };
  useEffect(() => {
    let cancelled = false, dispose = () => {};
    async function load() {
      const [T, response] = await Promise.all([import('three'), fetch(`/review/v138/${view}.json`)]);
      if (!response.ok) throw new Error('Review asset missing');
      const model: Model = await response.json(); if (cancelled) return;
      const renderer = new T.WebGLRenderer({ antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.setClearColor(0x151515);
      const scene = new T.Scene(), camera = new T.PerspectiveCamera(model.camera.fov, 1, .01, 20);
      camera.position.fromArray(model.camera.position); camera.quaternion.fromArray(model.camera.quaternion); camera.up.set(0,0,1);
      scene.add(new T.AmbientLight(0xffffff, 2)); const key = new T.DirectionalLight(0xffffff, 2); key.position.set(0,-3,5); scene.add(key);
      const rigs = new Map<string, InstanceType<typeof T.Group>>(), materials: InstanceType<typeof T.Material>[] = [], geometries: InstanceType<typeof T.BufferGeometry>[] = [], textures: InstanceType<typeof T.Texture>[] = [];
      const sweepClock={value:0};
      const leaves: { mesh: InstanceType<typeof T.Mesh>; data: Mesh }[] = [];
      for (const name of Object.keys(model.samples[0])) { const group = new T.Group(); group.matrixAutoUpdate = false; scene.add(group); rigs.set(name,group); }
      for (const data of model.meshes) {
        const g = new T.BufferGeometry(); g.setAttribute('position',new T.Float32BufferAttribute(data.positions,3)); g.setAttribute('uv',new T.Float32BufferAttribute(data.uvs,2)); g.setIndex(data.indices); g.computeVertexNormals(); data.groups.forEach(v=>g.addGroup(v.start,v.count,v.materialIndex)); geometries.push(g);
        const mats = await Promise.all(data.materials.map(async item => {
          const map = item.texture ? await new T.TextureLoader().loadAsync(item.texture) : null;
          if (map) { map.colorSpace=T.SRGBColorSpace; textures.push(map); }
          const color = map && view!=='photos' ? new T.Color(1,1,1) : new T.Color().fromArray(item.color);
          const side = item.frontSide ? T.FrontSide : T.DoubleSide;
          const mat = item.unlit ? new T.MeshBasicMaterial({ color, map, side }) : new T.MeshStandardMaterial({ color, map, roughness:item.roughness??.8, side });
          if(item.grayscale){
            mat.onBeforeCompile=shader=>{shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>','#include <map_fragment>\ndiffuseColor.rgb=vec3(dot(diffuseColor.rgb,vec3(.2126,.7152,.0722)));');};
            mat.customProgramCacheKey=()=> 'polaroid-grayscale-v147';
          }
          if(item.sweep){
            const sweep=item.sweep;
            mat.onBeforeCompile=shader=>{
              Object.assign(shader.uniforms,{sweepClock,sweepAxis:{value:new T.Vector3().fromArray(sweep.axis)},sweepMin:{value:sweep.min},sweepSpan:{value:sweep.span},sweepStart:{value:sweep.start},sweepDuration:{value:sweep.duration},sweepCycle:{value:sweep.cycle},sweepColor:{value:new T.Color().fromArray(sweep.color)}});
              shader.vertexShader='varying vec3 sweepPosition;\n'+shader.vertexShader;
              shader.vertexShader=shader.vertexShader.replace('#include <project_vertex>','#include <project_vertex>\nsweepPosition=(modelMatrix*vec4(transformed,1.0)).xyz;');
              shader.fragmentShader='varying vec3 sweepPosition; uniform float sweepClock, sweepMin, sweepSpan, sweepStart, sweepDuration, sweepCycle; uniform vec3 sweepAxis, sweepColor;\n'+shader.fragmentShader;
              shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
                float u=(dot(sweepPosition,sweepAxis)-sweepMin)/sweepSpan;
                float elapsed=mod(sweepClock-sweepStart,sweepCycle);
                float distance=min(elapsed/sweepDuration,1.0)*1.83-.18-u;
                float light=smoothstep(-.16,0.0,distance)*(1.0-smoothstep(.05,.65,distance))*.65;
                diffuseColor.rgb+=sweepColor*light;`);
            };
            mat.customProgramCacheKey=()=> 'room-player-sweep-v145';
          }
          materials.push(mat); return mat;
        }));
        const mesh = new T.Mesh(g,mats); mesh.name=data.name; (data.rig ? rigs.get(data.rig)! : scene).add(mesh); if(data.bent) leaves.push({mesh,data});
      }
      if (cancelled) { materials.forEach(m=>m.dispose()); geometries.forEach(g=>g.dispose()); textures.forEach(t=>t.dispose()); renderer.dispose(); return; }
      const mount=host.current!; mount.appendChild(renderer.domElement);
      // Fade the opaque sleeve as a single image. Switching individual box faces
      // to transparent/depthWrite=false exposes rear faces and causes an onset pop.
      const fullTarget=new T.WebGLRenderTarget(1,1,{samples:4}),backgroundTarget=new T.WebGLRenderTarget(1,1,{samples:4});
      const fadeScene=new T.Scene(),fadeCamera=new T.OrthographicCamera(-1,1,1,-1,0,1);
      const fadeMaterial=new T.ShaderMaterial({depthTest:false,depthWrite:false,toneMapped:false,uniforms:{fullImage:{value:fullTarget.texture},backgroundImage:{value:backgroundTarget.texture},opacity:{value:1}},vertexShader:'varying vec2 vUv; void main(){vUv=uv;gl_Position=vec4(position.xy,0.0,1.0);}',fragmentShader:'uniform sampler2D fullImage,backgroundImage; uniform float opacity; varying vec2 vUv; void main(){gl_FragColor=mix(texture2D(backgroundImage,vUv),texture2D(fullImage,vUv),opacity);\n#include <colorspace_fragment>\n}'});
      const fadeGeometry=new T.PlaneGeometry(2,2);fadeScene.add(new T.Mesh(fadeGeometry,fadeMaterial));
      const sleeveGroup=rigs.get('V138_Playback_Sleeve_Rig');
      let current=1, spinHoldStart:number|null=null;
      const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
      function draw(value:number) {
        current=Math.max(1,Math.min(model.frames,value)); const index=Math.min(model.frames-1,Math.floor(current)-1), fraction=current-Math.floor(current), a=model.samples[index], b=model.samples[Math.min(index+1,model.frames-1)];
        if(current<138||reducedMotion)spinHoldStart=null;
        else spinHoldStart??=performance.now();
        const pa=new T.Vector3(),pb=new T.Vector3(),qa=new T.Quaternion(),qb=new T.Quaternion(),sa=new T.Vector3(),sb=new T.Vector3();
        for (const [name,group] of rigs) {
          new T.Matrix4().fromArray(a[name].matrix).decompose(pa,qa,sa); new T.Matrix4().fromArray(b[name].matrix).decompose(pb,qb,sb);
          group.matrix.compose(pa.lerp(pb,fraction),qa.slerp(qb,fraction),sa.lerp(sb,fraction)); group.matrixWorldNeedsUpdate=true;
          if(name==='V138_Playback_Record_Rig'&&spinHoldStart!==null){
            const angle=-(performance.now()-spinHoldStart)/1000*Math.PI*2*(100/3)/60;
            qa.premultiply(new T.Quaternion().setFromAxisAngle(new T.Vector3(0,0,1),angle));
            group.matrix.compose(pa,qa,sa);
          }
          const opacity=a[name].opacity*(1-fraction)+b[name].opacity*fraction; group.visible=opacity>0;
          if(name.includes('Sleeve'))fadeMaterial.uniforms.opacity.value=opacity;
        }
        for(const {mesh,data} of leaves) {
          const i=Number(data.name.slice(-1)), start=94+i*30, t=Math.max(0,Math.min(1,(current-start)/24)), curl=Math.sin(t*Math.PI);
          const attr=mesh.geometry.getAttribute('position'); for(let j=0;j<attr.array.length;j++)attr.array[j]=data.positions[j]+(data.bent![j]-data.positions[j])*curl;
          attr.needsUpdate=true; mesh.geometry.computeVertexNormals();
        }
        const opacity=fadeMaterial.uniforms.opacity.value;
        if(sleeveGroup&&opacity>0&&opacity<1){
          renderer.setRenderTarget(fullTarget);renderer.render(scene,camera);
          sleeveGroup.visible=false;renderer.setRenderTarget(backgroundTarget);renderer.render(scene,camera);sleeveGroup.visible=true;
          renderer.setRenderTarget(null);renderer.render(fadeScene,fadeCamera);
        }else{renderer.setRenderTarget(null);renderer.render(scene,camera);}
      }
      const resize=new ResizeObserver(()=>{camera.aspect=mount.clientWidth/mount.clientHeight;camera.fov=Math.max(model.camera.fov,model.camera.fov/camera.aspect*.95);camera.updateProjectionMatrix();renderer.setSize(mount.clientWidth,mount.clientHeight);const size=renderer.getDrawingBufferSize(new T.Vector2());fullTarget.setSize(size.x,size.y);backgroundTarget.setSize(size.x,size.y);draw(current);}); resize.observe(mount);
      const ray=new T.Raycaster(),pointer=new T.Vector2();
      function hit(event:PointerEvent) {
        const rect=renderer.domElement.getBoundingClientRect();pointer.set((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(pointer,camera);
        return ray.intersectObjects(scene.children,true).find(h=>{let o:InstanceType<typeof T.Object3D>|null=h.object;while(o){if(!o.visible)return false;o=o.parent;}return true;});
      }
      function actionAt(event:PointerEvent) {
        const result=hit(event);if(!result)return null;
        if(view==='player')return result.object.name==='V138_Playback_Record'?'disc':null;
        if(view==='stack'||view==='photos')return null;
        if(current<78)return 'open';
        const root=rigs.get(`V138_${view==='hardback'?'Hardback':'Paperback'}_Root`)!;
        const p=result.point.clone().applyMatrix4(root.matrix.clone().invert());
        if(p.z<-.065 && p.x<-.17)return 'previous';
        if(p.z<-.065 && p.x>.025)return 'next';
        return null;
      }
      function click(event:PointerEvent){const action=actionAt(event);if(action==='disc')latest.current.onDisc();else if(action)latest.current.onBookAction(action);}
      function move(event:PointerEvent){renderer.domElement.style.cursor=actionAt(event)?'pointer':'default';}
      renderer.domElement.addEventListener('pointerup',click);renderer.domElement.addEventListener('pointermove',move);
      controls.current={frame:draw,angle:angled=>{camera.position.fromArray(model.camera.position);camera.quaternion.fromArray(model.camera.quaternion);if(angled){const target=camera.position.clone().add(new T.Vector3(0,0,-1).applyQuaternion(camera.quaternion).multiplyScalar(.66));camera.position.x+=.25;camera.position.z+=.23;camera.lookAt(target);}draw(current);}};
      draw(1);latest.current.onReady();
      let lightingRaf=0;const lightingStart=performance.now();
      if(view==='player'&&!matchMedia('(prefers-reduced-motion: reduce)').matches){const tick=(now:number)=>{sweepClock.value=(now-lightingStart)/1000*model.fps;draw(current);lightingRaf=requestAnimationFrame(tick);};lightingRaf=requestAnimationFrame(tick);}
      dispose=()=>{cancelAnimationFrame(lightingRaf);resize.disconnect();controls.current=null;renderer.domElement.remove();fullTarget.dispose();backgroundTarget.dispose();fadeGeometry.dispose();fadeMaterial.dispose();materials.forEach(m=>m.dispose());geometries.forEach(g=>g.dispose());textures.forEach(t=>t.dispose());renderer.dispose();};
    }
    void load().catch(()=>{if(!cancelled)latest.current.onFailure();});
    return()=>{cancelled=true;dispose();};
  },[view,controls]);
  return <div className="review-stage" ref={host} aria-label="3D design review" />;
}

export default function PlayerBookReview() {
  const [view,setView]=useState<View>('player'),[ready,setReady]=useState(false),[failed,setFailed]=useState(false),[frame,setFrame]=useState(1),[playing,setPlaying]=useState(false),[sound,setSound]=useState(true),[status,setStatus]=useState('Ready'),[fallback,setFallback]=useState(false),[angled,setAngled]=useState(false);
  const controls=useRef<Controls|null>(null),raf=useRef(0),generation=useRef(0),audio=useRef<AudioContext|null>(null),playingRef=useRef(false);
  function stop() {generation.current++;cancelAnimationFrame(raf.current);playingRef.current=false;setPlaying(false);}
  useEffect(()=>()=>{generation.current++;cancelAnimationFrame(raf.current);void audio.current?.close();},[]);
  function display(value:number){controls.current?.frame(value);setFrame(value);}
  function needleDrop(){
    if(!sound||!audio.current)return;const ctx=audio.current,buffer=ctx.createBuffer(1,Math.floor(ctx.sampleRate*.07),ctx.sampleRate),data=buffer.getChannelData(0);
    for(let i=0;i<data.length;i++)data[i]=(Math.random()*2-1)*Math.exp(-i/(ctx.sampleRate*.012));
    const source=ctx.createBufferSource(),filter=ctx.createBiquadFilter(),gain=ctx.createGain();source.buffer=buffer;filter.type='lowpass';filter.frequency.value=1900;gain.gain.value=.065;source.connect(filter).connect(gain).connect(ctx.destination);source.start();source.onended=()=>{source.disconnect();filter.disconnect();gain.disconnect();};
  }
  function openProject(){
    // Only after landing + needle contact. If delayed popups are blocked, leave
    // a normal accessible link instead of opening a blank tab before the motion.
    const child=window.open('','_blank');
    if(child){child.opener=null;child.location.replace('https://castingcompass.com');setStatus('Playing · project opened in a new tab');}
    else{setFallback(true);setStatus('Playing · open the project below');}
  }
  function animate(from:number,to:number,done?:()=>void,needle=false){
    if(!ready||playingRef.current)return;
    const token=++generation.current,start=performance.now();playingRef.current=true;setPlaying(true);let sounded=false;
    const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    function tick(now:number){
      if(token!==generation.current)return;const progress=reduced?1:Math.min(1,(now-start)/(Math.abs(to-from)/24*1000));const value=from+(to-from)*progress;display(value);
      if(needle&&value>=122&&!sounded){sounded=true;needleDrop();}
      if(needle)setStatus(value<42?'Sleeve slides left · record stays still':value<88?'Record flips onto the platter':value<122?'Arm lifts, swings, and lowers':'Playing');
      if(progress<1)raf.current=requestAnimationFrame(tick);else{playingRef.current=false;setPlaying(false);done?.();}
    }
    tick(start);
  }
  function play(navigate=false){
    if(playingRef.current||!ready)return;setFallback(false);
    if(sound){audio.current??=new AudioContext();void audio.current.resume().catch(()=>{});}
    animate(1,138,navigate?openProject:undefined,true);
  }
  function switchView(next:View){if(next===view)return;stop();setReady(false);setFailed(false);setView(next);setFrame(1);setStatus('Ready');setFallback(false);setAngled(false);}
  const book=view==='hardback'||view==='paperback',spread=frame<118?1:frame<148?2:3;
  function bookAction(action:'open'|'previous'|'next') {
    if(action==='open'&&frame<78)animate(frame,86);
    if(action==='previous'&&frame>=118)animate(frame,spread===3?118:86);
    if(action==='next'&&frame>=78&&spread<3)animate(frame,spread===1?118:148);
  }
  return <main className="model-review">
    <header><div><p>Design review · not yet applied to the room</p><h1>Player & books</h1></div><a href="/">Back to room</a></header>
    <nav aria-label="Review models">{(['player','hardback','paperback','stack','photos'] as View[]).map(v=><button key={v} aria-pressed={view===v} onClick={()=>switchView(v)}>{({player:'Record player',hardback:'Hardback',paperback:'Paperback',stack:'Shelf spacing',photos:'Polaroids'})[v]}</button>)}</nav>
    <ReviewCanvas view={view} controls={controls} onReady={()=>setReady(true)} onFailure={()=>setFailed(true)} onDisc={()=>play(true)} onBookAction={bookAction} />
    <section className="review-controls" aria-label="Preview controls">
      {!ready&&<p role="status">{failed?'Could not load this model. Choose another view or reload.':'Loading review model…'}</p>}
      {view==='player'&&<><p>Click the exposed record to play and open CastingCompass in a new tab.</p><div><button disabled={!ready||playing} onClick={()=>play()}>Preview animation</button><button disabled={!ready||playing} onClick={()=>play(true)}>Play & open project ↗</button><label><input type="checkbox" checked={sound} onChange={e=>setSound(e.target.checked)} /> Needle-drop sound</label></div><p role="status">{status}</p>{fallback&&<a href="https://castingcompass.com" target="_blank" rel="noopener noreferrer">Open CastingCompass ↗</a>}</>}
      {book&&<><p>{view==='hardback'?'Hardback: inset pages, thicker covers, and a visible cover-to-page gap.':'Paperback: thinner covers and nearly flush page edges.'}</p><div><button disabled={!ready||playing} onClick={()=>animate(frame,frame<78?86:1)}>{frame<78?'Open book':'Close book'}</button><button disabled={!ready||playing||frame<110} onClick={()=>animate(frame,spread===3?118:86)}>← Previous spread</button><button disabled={!ready||playing||frame<78||spread===3} onClick={()=>animate(frame,spread===1?118:148)}>Next spread →</button><button disabled={!ready||playing} aria-pressed={angled} onClick={()=>{setAngled(!angled);controls.current?.angle(!angled);}}>{angled?'Front view':'Inspect binding'}</button></div><p>Blank spread {spread} of 3</p></>}
      {view==='stack'&&<p>The upright stack is packed with narrow outline-to-outline gaps. The leftmost book has a gentler lean and no intersecting contours.</p>}
      {view!=='stack'&&view!=='photos'&&<div><button disabled={!ready} onClick={()=>{stop();display(1);setStatus('Ready');setFallback(false);}}>Reset</button><label className="review-timeline">Animation position<input aria-label="Animation position" type="range" min="1" max={book?148:144} step="1" value={frame} disabled={!ready||playing} onChange={e=>display(Number(e.target.value))}/></label></div>}
    </section>
  </main>;
}
