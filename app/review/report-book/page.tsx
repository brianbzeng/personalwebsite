"use client";
import {useEffect,useState} from 'react';
import BookshelfExperience from '../../components/BookshelfExperience';
import '../../components/cinematicRoom.css';
export default function ReportBookReview(){const [motion,setMotion]=useState(true);useEffect(()=>{const query=window.matchMedia('(prefers-reduced-motion: reduce)');const update=()=>setMotion(!query.matches);update();query.addEventListener('change',update);return()=>query.removeEventListener('change',update);},[]);return <BookshelfExperience initialCubby={0} motion={motion} onExit={()=>{window.location.href='/';}}/>;}
