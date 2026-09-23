import type * as Three from 'three';

export const RECORD_RIG = 'V138_Playback_Record_Rig';
type Part = { name:string; rig:string|null; positions:number[]; uvs:number[]; indices:number[]; groups:{start:number;count:number;materialIndex:number}[]; materials:{color:number[];texture:string|null;unlit?:boolean;frontSide?:boolean;roughness?:number;sweep?:{axis:number[];min:number;span:number;start:number;duration:number;cycle:number;color:number[]}}[] };
export type PlayerModel = {frames:number;fps:number;meshes:Part[];samples:Record<string,{matrix:number[];opacity:number}>[];camera:{position:number[];quaternion:number[];fov:number}};
type TModule = typeof Three;

// The disc surfaces ride the same highlight band as the tonearm parts so one
// coherent light pass moves across the whole player, in step with the model.
const DISC_SURFACE=/^(V138_Player_Platter|V138_Platter_Rim|V138_Playback_Record|V148_LabelMark|V138_Groove_|V138_Spindle)/;
const DISC_SWEEP={axis:[0,1,0],min:0.9259585738182068,span:0.38808292150497437,start:152,duration:96,cycle:240,color:[0.8299999833106995,0.8899999856948853,1]};
// Object-space radii for a rotation-invariant radial sheen on the vinyl faces.
const DISC_SHEEN:Record<string,number>={'V138_Playback_Record':.12,'V148_LabelMark':.024};

export async function createShelfPlayer(T:TModule, model:PlayerModel) {
  const background=new T.Scene(), rigs=new Map<string,Three.Group>(), clock={value:0};
  const resources:{geometry:Three.BufferGeometry;materials:Three.Material[]}[]=[];
  const maps:Three.Texture[]=[];
  for(const name of Object.keys(model.samples[0])) {const g=new T.Group();rigs.set(name,g);if(name!==RECORD_RIG&&!name.includes('Sleeve'))background.add(g);}
  background.background=new T.Color(0x151515);
  const ambient=new T.AmbientLight(0xffffff,1.8),lamp=new T.DirectionalLight(0xffffff,2);lamp.position.set(0,-3,5);background.add(ambient,lamp);
  const record=new T.Group();record.userData.disc=true;
  for(const part of model.meshes){
    // The room is the existing photographic plate, never the incomplete review set.
    if(!/^(V138_|V148_LabelMark|INTERACT_RecordPlayer_Base)/.test(part.name))continue;
    if(part.rig?.includes('Sleeve'))continue;
    const groove=part.name.startsWith('V138_Groove_');
    const geometry=groove?new T.TorusGeometry(Number(part.name.substring('V138_Groove_'.length)),.00022,6,256):new T.BufferGeometry();
    if(groove){geometry.translate(0,0,.00174);geometry.addGroup(0,geometry.index!.count,0);}
    else{geometry.setAttribute('position',new T.Float32BufferAttribute(part.positions,3));geometry.setAttribute('uv',new T.Float32BufferAttribute(part.uvs,2));geometry.setIndex(part.indices);geometry.computeVertexNormals();part.groups.forEach(g=>geometry.addGroup(g.start,g.count,g.materialIndex));}
    const materials=await Promise.all(part.materials.map(async item=>{
      const map=item.texture?await new T.TextureLoader().loadAsync(item.texture):null;if(map){map.colorSpace=T.SRGBColorSpace;maps.push(map);}
      const options={color:map?new T.Color(1,1,1):new T.Color().fromArray(item.color),map,side:item.frontSide?T.FrontSide:T.DoubleSide};
      const material=new T.MeshBasicMaterial(options);
      const sweep=item.sweep??(DISC_SURFACE.test(part.name)?DISC_SWEEP:undefined);
      const sheen=DISC_SHEEN[part.name];
      if(sweep||sheen){material.onBeforeCompile=shader=>{
        if(sweep){const s=sweep;Object.assign(shader.uniforms,{sweepClock:clock,sweepAxis:{value:new T.Vector3().fromArray(s.axis)},sweepMin:{value:s.min},sweepSpan:{value:s.span},sweepStart:{value:s.start},sweepDuration:{value:s.duration},sweepCycle:{value:s.cycle},sweepColor:{value:new T.Color().fromArray(s.color)}});}
        const varyings='varying vec3 sweepPosition;\n'+(sheen?'varying vec3 discLocal;\n':'');
        shader.vertexShader=varyings+shader.vertexShader;
        shader.vertexShader=shader.vertexShader.replace('#include <project_vertex>','#include <project_vertex>\nsweepPosition=(modelMatrix*vec4(transformed,1.0)).xyz;'+(sheen?'\ndiscLocal=position;':''));
        let prefix=varyings;
        if(sweep)prefix+='uniform float sweepClock,sweepMin,sweepSpan,sweepStart,sweepDuration,sweepCycle; uniform vec3 sweepAxis,sweepColor;\n';
        shader.fragmentShader=prefix+shader.fragmentShader;
        let inject='';
        if(sweep)inject+='\nfloat u=(dot(sweepPosition,sweepAxis)-sweepMin)/sweepSpan; float elapsed=mod(sweepClock-sweepStart,sweepCycle); float distance=min(elapsed/sweepDuration,1.0)*1.83-.18-u; diffuseColor.rgb+=sweepColor*smoothstep(-.16,0.0,distance)*(1.0-smoothstep(.05,.65,distance))*.65;';
        if(sheen)inject+=`\nfloat discR=clamp(length(discLocal.xy)/${sheen},0.0,1.0); diffuseColor.rgb+=vec3(1.0)*(.02+.055*discR*discR);`;
        shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>','#include <color_fragment>'+inject);
      };material.customProgramCacheKey=()=> sheen?'shelf-player-disc-v157':'shelf-player-sweep-v145';}
      return material;
    }));
    resources.push({geometry,materials});const mesh=new T.Mesh(geometry,materials);mesh.name=part.name;
    if(part.name.startsWith('V138_Groove_'))for(const material of materials)material.color.setRGB(.075,.075,.075);
    if(part.name==='V148_LabelMark')for(const material of materials)material.color.setRGB(.14,.14,.14);
    if(part.rig===RECORD_RIG){mesh.userData.disc=true;record.add(mesh);if(part.name.startsWith('V138_Groove_')){const reverse=mesh.clone();reverse.scale.z=-1;reverse.name+='Back';record.add(reverse);}}else(part.rig?rigs.get(part.rig)!:background).add(mesh);
  }
  const matrix=new T.Matrix4(),p=new T.Vector3(),q=new T.Quaternion(),s=new T.Vector3(),p2=p.clone(),q2=q.clone(),s2=s.clone();
  function pose(name:string,frame:number,target:Three.Object3D){
    const n=Math.min(model.frames,Math.max(1,frame)),i=Math.floor(n)-1,f=n-Math.floor(n);
    matrix.fromArray(model.samples[i][name].matrix).decompose(p,q,s);matrix.fromArray(model.samples[Math.min(i+1,model.frames-1)][name].matrix).decompose(p2,q2,s2);
    target.position.copy(p.lerp(p2,f));target.quaternion.copy(q.slerp(q2,f));target.scale.copy(s.lerp(s2,f));
  }
  function update(frame:number,seconds:number){for(const [name,g]of rigs)if(name!==RECORD_RIG&&!name.includes('Sleeve'))pose(name,frame,g);clock.value=72+seconds*model.fps;}
  background.background=null;
  update(1,0);
  return {background,record,pose,update,dispose(){for(const r of resources){r.geometry.dispose();r.materials.forEach(m=>m.dispose());}maps.forEach(t=>t.dispose());}};
}

// One physical record is detached from the sleeve and carried into the player
// shot. Both shots use its original mesh/materials, including all five grooves.
export function startShelfPlayback(T:TModule, player:Awaited<ReturnType<typeof createShelfPlayer>>, model:PlayerModel,
  renderer:Three.WebGLRenderer, source:Three.Scene, camera:Three.PerspectiveCamera, sleeve:Three.Group, record:Three.Group,
  plate:HTMLImageElement, reduced:boolean, done:()=>void) {
  const start=performance.now(),originalParent=record.parent!,recordLocal=record.position.clone(),recordQ=record.quaternion.clone();
  const sleevePosition=sleeve.position.clone(),sleeveQuaternion=sleeve.quaternion.clone();
  const cameraPosition=camera.position.clone(),cameraQuaternion=camera.quaternion.clone(),cameraFov=camera.fov;
  const foreground=new T.Scene();foreground.add(new T.AmbientLight(0xffffff,1.8));const lamp=new T.DirectionalLight(0xffffff,2);lamp.position.copy(cameraPosition).add(new T.Vector3(0,1,2));foreground.add(lamp);
  source.updateMatrixWorld(true);
  const capturedPosition=record.getWorldPosition(new T.Vector3()),capturedRotation=record.getWorldQuaternion(new T.Quaternion());
  const first=new T.Object3D();player.pose(RECORD_RIG,1,first);
  const offset=capturedPosition.clone().sub(first.position),rotationOffset=capturedRotation.clone().multiply(first.quaternion.clone().invert());
  const right=new T.Vector3(1,0,0).applyQuaternion(cameraQuaternion);
  const exitDirection=-Math.sign(new T.Vector3(1,0,0).applyQuaternion(sleeveQuaternion).dot(right)||1);
  const size=renderer.getDrawingBufferSize(new T.Vector2());
  const targetSize=(v:Three.Vector2)=>v.multiplyScalar(Math.min(2,2560/v.x,1440/v.y)).floor();
  targetSize(size);
  const targets=Array.from({length:2},()=>new T.WebGLRenderTarget(size.x,size.y,{samples:4}));
  const [full,bare]=targets;
  const quadScene=new T.Scene(),quadCamera=new T.OrthographicCamera(-1,1,1,-1,0,1),quadGeometry=new T.PlaneGeometry(2,2);
  const uniforms={a:{value:full.texture as Three.Texture},b:{value:bare.texture as Three.Texture},mixValue:{value:0},zoom:{value:1},center:{value:new T.Vector2(.5,.5)}};
  const quadMaterial=new T.ShaderMaterial({depthTest:false,depthWrite:false,toneMapped:false,uniforms,vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}',fragmentShader:'varying vec2 vUv;uniform sampler2D a,b;uniform float mixValue,zoom;uniform vec2 center;void main(){vec2 uv=center+(vUv-.5)/zoom;gl_FragColor=mix(texture2D(a,uv),texture2D(b,uv),mixValue);\n#include <colorspace_fragment>\n}'});
  quadScene.add(new T.Mesh(quadGeometry,quadMaterial));
  const plateTexture=new T.Texture(plate);plateTexture.colorSpace=T.SRGBColorSpace;plateTexture.needsUpdate=true;
  function mix(a:Three.Texture,b:Three.Texture,t:number,target:Three.WebGLRenderTarget|null){uniforms.a.value=a;uniforms.b.value=b;uniforms.mixValue.value=t;renderer.setRenderTarget(target);renderer.render(quadScene,quadCamera);}
  // Keep the camera and plate together. A gentle optical push-in crops the
  // completed frame, so every shelf, outline and decoration stays consistent.
  const playerCenter=new T.Box3().setFromObject(player.background).getCenter(new T.Vector3()).project(camera);
  foreground.attach(sleeve);foreground.attach(record);
  let completed=false,sounded=false,context:AudioContext|null=null;
  try{context=new AudioContext();void context.resume();}catch{/* Audio is optional. */}
  const smooth=(v:number)=>{const t=Math.max(0,Math.min(1,v));return t*t*(3-2*t);};
  function draw(now:number){
    const elapsed=(now-start)/1000,frame=reduced?138:Math.min(138,1+elapsed*model.fps),flight=smooth((frame-42)/46);
    player.update(frame,elapsed);player.pose(RECORD_RIG,frame,record);
    record.position.addScaledVector(offset,1-flight);record.quaternion.premultiply(rotationOffset.clone().slerp(new T.Quaternion(),flight));
    if(frame===138&&!reduced)record.quaternion.premultiply(new T.Quaternion().setFromAxisAngle(new T.Vector3(0,0,1),-Math.max(0,elapsed-137/model.fps)*Math.PI*2*(100/3)/60));
    sleeve.position.copy(sleevePosition).addScaledVector(right,exitDirection*.31*smooth((frame-1)/41));
    const opacity=1-smooth((frame-5.8)/43);
    const nextSize=targetSize(renderer.getDrawingBufferSize(new T.Vector2()));if(full.width!==nextSize.x||full.height!==nextSize.y)for(const target of targets)target.setSize(nextSize.x,nextSize.y);
    uniforms.zoom.value=1;uniforms.center.value.set(.5,.5);
    for(const [target,showSleeve] of [[full,true],[bare,false]] as const){
      mix(plateTexture,plateTexture,0,target);
      renderer.autoClear=false;renderer.clearDepth();renderer.render(source,camera);
      sleeve.visible=showSleeve&&opacity>0;renderer.render(foreground,camera);renderer.autoClear=true;
    }
    const zoom=1+flight*.65;
    uniforms.zoom.value=zoom;
    const margin=.5/zoom;
    uniforms.center.value.set(.5+playerCenter.x*.5*flight,.5+playerCenter.y*.5*flight).clamp(new T.Vector2(margin,margin),new T.Vector2(1-margin,1-margin));
    mix(bare.texture,full.texture,opacity,null);
    if(frame>=122&&!sounded){sounded=true;if(context){const c=context,buffer=c.createBuffer(1,Math.floor(c.sampleRate*.07),c.sampleRate),data=buffer.getChannelData(0);for(let i=0;i<data.length;i++)data[i]=(Math.random()*2-1)*Math.exp(-i/(c.sampleRate*.012));const noise=c.createBufferSource(),filter=c.createBiquadFilter(),gain=c.createGain();noise.buffer=buffer;filter.frequency.value=1900;gain.gain.value=.065;noise.connect(filter).connect(gain).connect(c.destination);noise.start();}}
    if(frame>=138&&!completed){completed=true;done();}
  }
  function stop(){source.attach(sleeve);sleeve.position.copy(sleevePosition);sleeve.quaternion.copy(sleeveQuaternion);sleeve.visible=true;originalParent.add(record);record.position.copy(recordLocal);record.quaternion.copy(recordQ);record.scale.setScalar(1);player.update(1,0);camera.position.copy(cameraPosition);camera.quaternion.copy(cameraQuaternion);camera.fov=cameraFov;camera.updateProjectionMatrix();targets.forEach(t=>t.dispose());quadGeometry.dispose();quadMaterial.dispose();plateTexture.dispose();void context?.close();renderer.setRenderTarget(null);renderer.autoClear=true;}
  return {draw,stop};
}
