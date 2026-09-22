import type * as Three from 'three';
import type {ShelfFit} from './shelfMobileLayout';
type TModule=typeof Three;
type PhotoPart={name:string;positions:number[];uvs:number[];indices:number[];groups:{start:number;count:number;materialIndex:number}[];materials:{color:number[];texture:string|null;grayscale?:boolean}[]};
// Pop-out/lineup order follows shelf positions 1,3,2,4, lifting the upper
// middle card first. Each card retains its authored shelf pose below.
const CARDS=[
 {letter:'D',center:[2.465,1.52,.978],quaternion:[0,0,-.632981412,.774166993]},
 {letter:'B',center:[2.455,1.31,.978],quaternion:[0,0,-.667166280,.744908823]},
 {letter:'C',center:[2.48,1.455,.96],quaternion:[0,0,-.734817783,.678264570]},
 {letter:'A',center:[2.47,1.25,.96],quaternion:[0,0,-.767798648,.640691218]},
];
export const PHOTO_LABELS=['Las Vegas selfie','Escape room group','Friends at night','Fishing trip'];
// Display-referred gray sampled from all four card faces in the final v153
// pan frame. Raw Blender diffuse colors omit the baked room lighting.
export const POLAROID_PAPER_COLOR=0x848484;
// The rendered photos use emission strength from photos.json and Blender's
// Standard/sRGB view at -0.3 stops. Apply both in linear space before sRGB output.
export const POLAROID_PHOTO_EXPOSURE=Math.pow(2,-.3);
export async function createPolaroidGallery(T:TModule,scene:Three.Scene,camera:Three.PerspectiveCamera,motion:()=>boolean,onBusy:(busy:boolean)=>void,onPhoto:(index:number|null)=>void,mobileFit:()=>ShelfFit|null=()=>null){
 const response=await fetch('/review/v154/photos.json');if(!response.ok)throw new Error('Photos unavailable');
 const model=await response.json() as {meshes:PhotoPart[];shelfPoses?:Record<string,{center:number[];quaternion:number[]}>};
 const geometries:Three.BufferGeometry[]=[],materials:Three.Material[]=[],textures:Three.Texture[]=[],outlines:Three.LineBasicMaterial[]=[];
 const cards=await Promise.all(CARDS.map(async(data,index)=>{
  const pose=model.shelfPoses?.[data.letter]??data;
  const group=new T.Group(),origin=new T.Vector3().fromArray(pose.center),rest=new T.Quaternion().fromArray(pose.quaternion).normalize();
  group.position.copy(origin);group.quaternion.copy(rest);group.userData.selection='photos';group.userData.photoIndex=index;
  for(const part of model.meshes.filter((p:{name:string})=>p.name.includes(`Polaroid_${data.letter}_`))){
   const geometry=new T.BufferGeometry(),positions=part.positions.slice(),inverse=rest.clone().invert();
   for(let i=0;i<positions.length;i+=3){const p=new T.Vector3(positions[i],positions[i+1],positions[i+2]).sub(origin).applyQuaternion(inverse);positions[i]=p.x;positions[i+1]=p.y;positions[i+2]=p.z;}
   geometry.setAttribute('position',new T.Float32BufferAttribute(positions,3));geometry.setAttribute('uv',new T.Float32BufferAttribute(part.uvs,2));geometry.setIndex(part.indices);geometry.computeVertexNormals();part.groups.forEach((g:{start:number;count:number;materialIndex:number})=>geometry.addGroup(g.start,g.count,g.materialIndex));geometries.push(geometry);
   const mats=await Promise.all(part.materials.map(async(m:{color:number[];texture:string|null;grayscale?:boolean})=>{
    const map=m.texture?await new T.TextureLoader().loadAsync(m.texture):null;if(map){map.colorSpace=T.SRGBColorSpace;map.anisotropy=8;textures.push(map);}
    const paper=part.name.startsWith('SHELF_Polaroid_')&&part.name.endsWith('_Card');
    const color=paper?new T.Color(POLAROID_PAPER_COLOR):new T.Color().fromArray(m.color);
    if(map)color.multiplyScalar(POLAROID_PHOTO_EXPOSURE);
    const material=new T.MeshBasicMaterial({color,map,side:T.DoubleSide,toneMapped:false});
    if(m.grayscale){material.onBeforeCompile=shader=>{shader.fragmentShader=shader.fragmentShader.replace('#include <map_fragment>','#include <map_fragment>\ndiffuseColor.rgb=vec3(dot(diffuseColor.rgb,vec3(.2126,.7152,.0722)));');};material.customProgramCacheKey=()=> 'polaroid-grayscale';}
    materials.push(material);return material;
   }));group.add(new T.Mesh(geometry,mats));
   if(part.name.startsWith('SHELF_Polaroid_')&&part.name.endsWith('_Card')){
    const edges=new T.EdgesGeometry(geometry,25),ink=new T.LineBasicMaterial({color:0xffffff,transparent:true,opacity:0,depthWrite:false,toneMapped:false});
    const outline=new T.LineSegments(edges,ink);outline.position.z=.00012;outline.raycast=()=>{};group.add(outline);
    geometries.push(edges);materials.push(ink);outlines.push(ink);
   }
  }
  scene.add(group);return{group,origin,rest};
 }));
 const bounds=new T.Box3();cards.forEach(c=>bounds.expandByObject(c.group));
 // Pad the whole pile, especially vertically: edge-on cards are otherwise
 // only a few pixels tall. This invisible target never changes their appearance.
 const size=bounds.getSize(new T.Vector3());size.z=Math.max(size.z,.12);size.y+=.075;size.x+=.025;
 const hitGeometry=new T.BoxGeometry(size.x,size.y,size.z),hitMaterial=new T.MeshBasicMaterial({transparent:true,opacity:0,depthWrite:false});
 const deckHit=new T.Mesh(hitGeometry,hitMaterial);deckHit.position.copy(bounds.getCenter(new T.Vector3()));deckHit.userData.selection='photos';scene.add(deckHit);
 let progress=0,direction=0,last=0,photo:number|null=null,zoom=0,zoomTarget=0,returning=false,finish:(()=>void)|null=null,pulseStart=0,lastFit='';
 const stagger=.18,duration=.8,total=duration+stagger*3;
 const smooth=(v:number)=>{const t=Math.max(0,Math.min(1,v));return t*t*(3-2*t);};
 function open(){if(progress>0)return;direction=1;onBusy(true);}
 function inspect(index:number|null){if(direction||returning)return;if(zoomTarget===1&&index!==null){if(index!==photo)return;index=null;}photo=index??photo;zoomTarget=index===null?0:1;onPhoto(index);onBusy(true);}
 function close(){return new Promise<void>(resolve=>{finish=resolve;returning=true;zoomTarget=0;onPhoto(null);onBusy(true);if(zoom===0)direction=-1;});}
 function update(now:number){
  if(!pulseStart)pulseStart=now;
  const pulse=motion()&&progress===0?Math.pow(Math.sin((now-pulseStart)/1000*Math.PI/3.2),2)*.72:0;
  const pulseChanged=outlines.some(m=>Math.abs(m.opacity-pulse)>.002);
  outlines.forEach(m=>{m.opacity=pulse;});
  const dt=last?Math.min(.05,(now-last)/1000):0;last=now;
  const wasMoving=direction!==0||zoom!==zoomTarget;
  if(zoom!==zoomTarget){zoom=motion()?Math.max(0,Math.min(1,zoom+Math.sign(zoomTarget-zoom)*dt/.5)):zoomTarget;if(zoom===zoomTarget){if(zoom===0){photo=null;if(returning)direction=-1;}if(!returning)onBusy(false);}}
  if(direction){progress=motion()?Math.max(0,Math.min(total,progress+direction*dt)):(direction===1?total:0);if(progress===total&&direction===1){direction=0;onBusy(false);}if(progress===0&&direction===-1){direction=0;returning=false;onBusy(false);const done=finish;finish=null;done?.();}}
  const forward=new T.Vector3();camera.getWorldDirection(forward);const right=new T.Vector3(1,0,0).applyQuaternion(camera.quaternion),up=new T.Vector3(0,1,0).applyQuaternion(camera.quaternion);
  const distance=1.2,viewHeight=2*distance*Math.tan(T.MathUtils.degToRad(camera.fov/2)),viewWidth=viewHeight*camera.aspect;
  const fit=mobileFit(),fitKey=JSON.stringify(fit),fitChanged=fitKey!==lastFit;lastFit=fitKey;
  const availableWidth=fit?.width??viewWidth,availableHeight=fit?.height??viewHeight;
  const width=Math.min(availableWidth*.185,availableHeight*(fit ? .8 : .62)*.8),gap=(availableWidth*.90-4*width)/3,scale=width/.16;
  const middle=camera.position.clone().addScaledVector(forward,distance);
  if(fit)middle.addScaledVector(right,fit.x).addScaledVector(up,fit.y);
  cards.forEach((card,i)=>{
   const t=smooth((progress-i*stagger)/duration),row=middle.clone().addScaledVector(right,(i-1.5)*(width+gap));
   card.group.position.copy(card.origin).lerp(row,t).addScaledVector(up,.075*Math.sin(Math.PI*t));card.group.quaternion.copy(card.rest).slerp(camera.quaternion,t);card.group.scale.setScalar(1+(scale-1)*t);
   if(photo===i&&zoom>0){const z=smooth(zoom),large=Math.min(availableHeight*(fit ? .93 : .85)/.20,availableWidth*.78/.16);card.group.position.lerp(middle.clone().addScaledVector(forward,-.035),z);card.group.scale.setScalar(scale+(large-scale)*z);}
  });
  deckHit.visible=progress===0;return fitChanged||pulseChanged||wasMoving||direction!==0||zoom!==zoomTarget;
 }
 return{open,inspect,close,update,
  // Read-only handles let staging cues project the same fitted/animated cards
  // that are actually drawn, rather than guessing their screen positions.
  cueObjects:()=>({cards:cards.map(card=>card.group),selected:zoomTarget===1?photo:null}),
  dispose(){finish?.();cards.forEach(c=>scene.remove(c.group));scene.remove(deckHit);geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());textures.forEach(t=>t.dispose());hitGeometry.dispose();hitMaterial.dispose();}};
}
