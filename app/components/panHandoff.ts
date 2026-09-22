import {useCallback,useEffect,useRef} from 'react';

/** Keep the last decoded frame until the destination has actually painted. */
export function usePanHandoff(){
  const canvas=useRef<HTMLCanvasElement>(null),generation=useRef(0);
  const capture=useCallback((video:HTMLVideoElement|null)=>{
    const token=++generation.current,node=canvas.current;
    if(node&&video&&video.readyState>=2&&video.videoWidth){
      node.width=video.videoWidth;node.height=video.videoHeight;
      node.getContext('2d')!.drawImage(video,0,0);node.style.visibility='visible';
      node.dataset.holding='true';
    }
    return token;
  },[]);
  const release=useCallback(()=>{
    const token=generation.current;
    requestAnimationFrame(()=>requestAnimationFrame(()=>{
      if(generation.current!==token)return;
      if(canvas.current){canvas.current.style.visibility='hidden';canvas.current.dataset.holding='false';}
    }));
  },[]);
  useEffect(()=>()=>{generation.current++;},[]);
  return {canvas,capture,release};
}

export const shelfPlates=[
  {still:'/room/v149/books-still.webp',background:'/room/v149/books-background.webp'},
  {still:'/room/v156/vinyl-still.webp',background:'/room/v156/vinyl-background.webp'},
  {still:'/room/v154/photos-still.webp',background:'/room/v152/photos-background.webp'},
];

// Opt-in media only: the approved experience keeps its current release until review.
export const PHOTO_CONSISTENCY_MEDIA='/room/v159/';
export const BOOK_CONSISTENCY_MEDIA='/room/v160/';
const coherentPhotoPlates=shelfPlates.map((plate,index)=>index===2?{
  still:`${PHOTO_CONSISTENCY_MEDIA}photos-still.webp`,
  background:`${PHOTO_CONSISTENCY_MEDIA}photos-background.webp`,
}:plate);
const coherentBookPlate={still:`${BOOK_CONSISTENCY_MEDIA}books-still.webp`,background:`${BOOK_CONSISTENCY_MEDIA}books-background.webp`};
const coherentBookPlates=shelfPlates.map((plate,index)=>index===0?coherentBookPlate:plate);
const coherentShelfPlates=coherentPhotoPlates.map((plate,index)=>index===0?coherentBookPlate:plate);
export function getShelfPlates(coherentPhotos=false,coherentBooks=false){
  if(coherentBooks)return coherentPhotos?coherentShelfPlates:coherentBookPlates;
  return coherentPhotos?coherentPhotoPlates:shelfPlates;
}
export function shelfTravelClip(from:number,to:number,coherentPhotos=false,coherentBooks=false){
  const photoAdjacent=(from===1&&to===2)||(from===2&&to===1);
  const bookAdjacent=(from===1&&to===0)||(from===0&&to===1);
  return `${coherentBooks&&bookAdjacent?BOOK_CONSISTENCY_MEDIA:coherentPhotos&&photoAdjacent?PHOTO_CONSISTENCY_MEDIA:'/room/v155/'}shelf-${from}-${to}.mp4`;
}
