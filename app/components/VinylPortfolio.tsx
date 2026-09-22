"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import * as THREE from "three";
import { PROJECTS } from "../data/projects";

type Phase = "shelf" | "spilling" | "rail" | "selecting";

type SceneRecord = {
  group: THREE.Group;
  index: number;
  texture: THREE.CanvasTexture;
  origin: THREE.Vector3;
};

const SPILL_DURATION = 1900;

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function easeOutCubic(value: number) {
  return 1 - Math.pow(1 - clamp(value, 0, 1), 3);
}

function playTone(enabled: boolean, type: "click" | "spill" | "flip") {
  if (!enabled || typeof window === "undefined") return;
  const AudioContextClass = window.AudioContext
    || (window as Window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioContextClass) return;

  const context = new AudioContextClass();
  const settings = {
    click: { start: 360, end: 620, duration: 0.08 },
    spill: { start: 110, end: 240, duration: 0.32 },
    flip: { start: 470, end: 180, duration: 0.18 },
  }[type];
  const oscillator = context.createOscillator();
  const gain = context.createGain();

  oscillator.type = type === "spill" ? "triangle" : "square";
  oscillator.frequency.setValueAtTime(settings.start, context.currentTime);
  oscillator.frequency.exponentialRampToValueAtTime(settings.end, context.currentTime + settings.duration);
  gain.gain.setValueAtTime(0.0001, context.currentTime);
  gain.gain.exponentialRampToValueAtTime(0.035, context.currentTime + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + settings.duration);
  oscillator.connect(gain);
  gain.connect(context.destination);
  oscillator.start();
  oscillator.stop(context.currentTime + settings.duration + 0.02);
  oscillator.addEventListener("ended", () => void context.close(), { once: true });
}

function createCoverTexture(project: (typeof PROJECTS)[number]) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 640;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("Could not create the project cover texture.");

  context.fillStyle = "#10131d";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = project.accent;
  context.fillRect(28, 28, canvas.width - 56, 10);
  context.fillRect(28, canvas.height - 38, canvas.width - 56, 10);
  context.strokeStyle = "rgba(255,255,255,.14)";
  context.lineWidth = 2;
  for (let x = 28; x < canvas.width - 28; x += 46) {
    context.beginPath();
    context.moveTo(x, 62);
    context.lineTo(x, canvas.height - 62);
    context.stroke();
  }
  for (let y = 62; y < canvas.height - 62; y += 46) {
    context.beginPath();
    context.moveTo(28, y);
    context.lineTo(canvas.width - 28, y);
    context.stroke();
  }

  context.fillStyle = project.accent;
  context.font = "700 26px monospace";
  context.fillText(`${project.number} / PROJECT RECORD`, 48, 88);
  context.fillStyle = "#f6f3e9";
  context.font = "700 44px monospace";
  const words = project.title.toUpperCase().split(" ");
  let line = "";
  let lineY = 320;
  for (const word of words) {
    const next = line ? `${line} ${word}` : word;
    if (context.measureText(next).width > 400 && line) {
      context.fillText(line, 48, lineY);
      line = word;
      lineY += 53;
    } else {
      line = next;
    }
  }
  if (line) context.fillText(line, 48, lineY);
  context.fillStyle = "#9da0a9";
  context.font = "500 19px monospace";
  context.fillText(project.category, 48, 532);
  context.fillText("FIELD NOTES / BZ", 48, 570);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = 1;
  return texture;
}

function createRecord(project: (typeof PROJECTS)[number], index: number): SceneRecord {
  const group = new THREE.Group();
  group.userData.recordIndex = index;

  const coverMaterial = new THREE.MeshStandardMaterial({ color: 0x202436, roughness: 0.68, metalness: 0.12 });
  const edge = new THREE.Mesh(new THREE.BoxGeometry(2.12, 2.7, 0.12), coverMaterial);
  group.add(edge);

  const texture = createCoverTexture(project);
  const front = new THREE.Mesh(
    new THREE.PlaneGeometry(1.94, 2.52),
    new THREE.MeshBasicMaterial({ map: texture }),
  );
  front.position.z = 0.09;
  group.add(front);

  const back = new THREE.Mesh(
    new THREE.PlaneGeometry(1.94, 2.52),
    new THREE.MeshStandardMaterial({ color: 0x181b28, roughness: 0.82 }),
  );
  back.position.z = -0.09;
  back.rotation.y = Math.PI;
  group.add(back);

  const record = new THREE.Mesh(
    new THREE.CylinderGeometry(0.73, 0.73, 0.08, 40),
    new THREE.MeshStandardMaterial({ color: 0x05060b, roughness: 0.35, metalness: 0.45 }),
  );
  record.rotation.x = Math.PI / 2;
  record.position.set(0.1, -0.02, 0.16);
  group.add(record);

  const label = new THREE.Mesh(
    new THREE.CylinderGeometry(0.18, 0.18, 0.085, 24),
    new THREE.MeshBasicMaterial({ color: project.accent }),
  );
  label.rotation.x = Math.PI / 2;
  label.position.set(0.1, -0.02, 0.21);
  group.add(label);

  const origin = new THREE.Vector3((index - 2) * 0.15, -0.25 + index * 0.08, index * 0.08);
  group.position.copy(origin);
  group.rotation.set(0, 0, (index - 2) * 0.035);
  return { group, index, texture, origin };
}

export default function VinylPortfolio() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const phaseRef = useRef<Phase>("shelf");
  const activeIndexRef = useRef(0);
  const selectedIndexRef = useRef<number | null>(null);
  const hoveredIndexRef = useRef<number | null>(null);
  const reducedMotionRef = useRef(false);
  const soundRef = useRef(false);
  const [phase, setPhase] = useState<Phase>("shelf");
  const [activeIndex, setActiveIndex] = useState(0);
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const activeProject = PROJECTS[activeIndex];

  const updateActiveIndex = useCallback((next: number) => {
    const value = clamp(next, 0, PROJECTS.length - 1);
    activeIndexRef.current = value;
    setActiveIndex(value);
    playTone(soundRef.current, "click");
  }, []);

  const selectProject = useCallback((index: number) => {
    if (phaseRef.current !== "rail" || selectedIndexRef.current !== null) return;
    selectedIndexRef.current = index;
    activeIndexRef.current = index;
    setActiveIndex(index);
    setSelectedIndex(index);
    phaseRef.current = "selecting";
    setPhase("selecting");
    playTone(soundRef.current, "flip");
    if (reducedMotionRef.current) window.location.assign(`/projects/${PROJECTS[index].slug}`);
  }, []);

  const spillRecords = useCallback(() => {
    if (phaseRef.current !== "shelf" && phaseRef.current !== "rail") return;
    if (phaseRef.current === "rail") return;
    phaseRef.current = reducedMotionRef.current ? "rail" : "spilling";
    setPhase(phaseRef.current);
    playTone(soundRef.current, "spill");
  }, []);

  const replaySpill = useCallback(() => {
    if (phaseRef.current === "spilling" || phaseRef.current === "selecting") return;
    selectedIndexRef.current = null;
    setSelectedIndex(null);
    phaseRef.current = "shelf";
    setPhase("shelf");
    window.requestAnimationFrame(() => spillRecords());
  }, [spillRecords]);

  useEffect(() => {
    soundRef.current = soundEnabled;
  }, [soundEnabled]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const stage = stageRef.current;
    if (!canvas || !stage) return;

    const reducedQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    reducedMotionRef.current = reducedQuery.matches;
    const reducedListener = () => { reducedMotionRef.current = reducedQuery.matches; };
    reducedQuery.addEventListener("change", reducedListener);

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.08;
    renderer.setClearColor(0x08090e, 1);

    const scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0x08090e, 10, 24);
    const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 60);
    camera.position.set(0, 1.35, 11.5);

    scene.add(new THREE.HemisphereLight(0xa7c8ff, 0x08090e, 1.65));
    const keyLight = new THREE.DirectionalLight(0xffffff, 2.4);
    keyLight.position.set(-4, 8, 8);
    scene.add(keyLight);
    const cyanLight = new THREE.PointLight(0x35d0ff, 10, 12, 2);
    cyanLight.position.set(-5.4, 1.8, 2.5);
    scene.add(cyanLight);
    const pinkLight = new THREE.PointLight(0xff4fba, 9, 12, 2);
    pinkLight.position.set(5.3, 2.6, 0.3);
    scene.add(pinkLight);

    const wall = new THREE.Mesh(
      new THREE.BoxGeometry(22, 13, 0.35),
      new THREE.MeshStandardMaterial({ color: 0x11131d, roughness: 0.9 }),
    );
    wall.position.set(0, 3.1, -4.5);
    scene.add(wall);
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(24, 18),
      new THREE.MeshStandardMaterial({ color: 0x0b0d14, roughness: 0.88, metalness: 0.12 }),
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -1.86;
    scene.add(floor);

    const grid = new THREE.GridHelper(24, 24, 0x24324b, 0x141a29);
    grid.position.set(0, -1.84, 0.4);
    (grid.material as THREE.Material).opacity = 0.68;
    (grid.material as THREE.Material).transparent = true;
    scene.add(grid);

    const neonBarMaterial = new THREE.MeshBasicMaterial({ color: 0x35d0ff });
    const neonBar = new THREE.Mesh(new THREE.BoxGeometry(7.5, 0.035, 0.05), neonBarMaterial);
    neonBar.position.set(0, 4.6, -4.25);
    scene.add(neonBar);
    const neonBarTwo = new THREE.Mesh(new THREE.BoxGeometry(3.2, 0.035, 0.05), new THREE.MeshBasicMaterial({ color: 0xff4fba }));
    neonBarTwo.position.set(5.7, 3.7, -4.25);
    scene.add(neonBarTwo);

    const holder = new THREE.Group();
    holder.position.set(-4.25, 0.05, -0.45);
    holder.rotation.z = -0.08;
    scene.add(holder);
    const metal = new THREE.MeshStandardMaterial({ color: 0x262c3b, roughness: 0.32, metalness: 0.8 });
    const addHolderBar = (width: number, height: number, depth: number, x: number, y: number, z: number, rotation = 0) => {
      const bar = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), metal);
      bar.position.set(x, y, z);
      bar.rotation.z = rotation;
      holder.add(bar);
    };
    addHolderBar(0.15, 4.1, 0.22, -1.75, 0, 0, -0.42);
    addHolderBar(0.15, 4.1, 0.22, 1.75, 0, 0, 0.42);
    addHolderBar(4.3, 0.15, 0.24, 0, -1.78, 0);
    addHolderBar(4.3, 0.15, 0.24, 0, 1.55, 0);
    addHolderBar(4.05, 0.16, 0.26, 0, -0.58, 0.08);
    const holderLabel = new THREE.Mesh(new THREE.BoxGeometry(1.35, 0.42, 0.1), new THREE.MeshBasicMaterial({ color: 0xff4fba }));
    holderLabel.position.set(0, -1.25, 0.16);
    holder.add(holderLabel);

    const records = PROJECTS.map((project, index) => {
      const record = createRecord(project, index);
      record.origin.add(holder.position);
      record.group.position.copy(record.origin);
      scene.add(record.group);
      return record;
    });

    let spillStartedAt = 0;
    let selectedStartedAt = 0;
    let selectedRouteStarted = false;
    let targetCameraX = 0;
    let targetCameraY = 1.35;
    let wheelAccumulator = 0;
    let dragStartX: number | null = null;
    let lastHovered: number | null = null;

    const resize = () => {
      const width = stage.clientWidth;
      const height = stage.clientHeight;
      renderer.setSize(width, height, false);
      camera.aspect = width / Math.max(height, 1);
      camera.updateProjectionMatrix();
    };
    resize();
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(stage);

    const getRailTarget = (index: number, selected: number | null) => {
      const focus = selected ?? activeIndexRef.current;
      const offset = index - focus;
      const distance = Math.abs(offset);
      const isSelected = selected === index;
      return {
        position: new THREE.Vector3(offset * 2.25, 0.12 + Math.max(0, 1 - distance) * 0.28, -distance * 0.72 + (isSelected ? 2.0 : 0)),
        rotation: new THREE.Euler(0, offset * -0.15 + (isSelected ? Math.PI : 0), offset * 0.045),
        scale: 1 - Math.min(distance, 3) * 0.075,
      };
    };

    const pointerPosition = (event: PointerEvent) => {
      const bounds = canvas.getBoundingClientRect();
      return new THREE.Vector2(((event.clientX - bounds.left) / bounds.width) * 2 - 1, -((event.clientY - bounds.top) / bounds.height) * 2 + 1);
    };
    const raycaster = new THREE.Raycaster();
    const updateHover = (event: globalThis.PointerEvent) => {
      if (phaseRef.current !== "rail") return;
      const point = pointerPosition(event as unknown as PointerEvent);
      raycaster.setFromCamera(point, camera);
      const intersections = raycaster.intersectObjects(records.map((record) => record.group), true);
      const hit = intersections[0]?.object;
      let next: number | null = null;
      if (hit) {
        let node: THREE.Object3D | null = hit;
        while (node && typeof node.userData.recordIndex !== "number") node = node.parent;
        next = node?.userData.recordIndex ?? null;
      }
      if (next !== lastHovered) {
        lastHovered = next;
        hoveredIndexRef.current = next;
        setHoveredIndex(next);
      }
    };
    const onPointerMove = (event: globalThis.PointerEvent) => {
      const bounds = canvas.getBoundingClientRect();
      const x = (event.clientX - bounds.left) / bounds.width - 0.5;
      const y = (event.clientY - bounds.top) / bounds.height - 0.5;
      targetCameraX = clamp(x * 1.15, -0.7, 0.7);
      targetCameraY = clamp(1.35 - y * 0.5, 0.95, 1.8);
      updateHover(event);
    };
    const onPointerDown = (event: globalThis.PointerEvent) => {
      dragStartX = event.clientX;
      canvas.setPointerCapture(event.pointerId);
    };
    const onPointerUp = (event: globalThis.PointerEvent) => {
      if (phaseRef.current !== "rail" || dragStartX === null) {
        dragStartX = null;
        return;
      }
      const delta = event.clientX - dragStartX;
      dragStartX = null;
      if (Math.abs(delta) > 28) {
        updateActiveIndex(activeIndexRef.current + (delta < 0 ? 1 : -1));
        return;
      }
      const point = pointerPosition(event as unknown as PointerEvent);
      raycaster.setFromCamera(point, camera);
      const intersections = raycaster.intersectObjects(records.map((record) => record.group), true);
      const hit = intersections[0]?.object;
      let node: THREE.Object3D | null = hit ?? null;
      while (node && typeof node.userData.recordIndex !== "number") node = node.parent;
      if (typeof node?.userData.recordIndex === "number") selectProject(node.userData.recordIndex);
    };
    const onWheel = (event: WheelEvent) => {
      if (phaseRef.current !== "rail") return;
      event.preventDefault();
      wheelAccumulator += event.deltaY;
      if (Math.abs(wheelAccumulator) > 42) {
        updateActiveIndex(activeIndexRef.current + (wheelAccumulator > 0 ? 1 : -1));
        wheelAccumulator = 0;
      }
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (phaseRef.current !== "rail") return;
      if (event.key === "ArrowRight" || event.key === "ArrowDown") {
        event.preventDefault();
        updateActiveIndex(activeIndexRef.current + 1);
      }
      if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
        event.preventDefault();
        updateActiveIndex(activeIndexRef.current - 1);
      }
      if (event.key === "Home") updateActiveIndex(0);
      if (event.key === "End") updateActiveIndex(PROJECTS.length - 1);
      if (event.key === "Enter" && hoveredIndexRef.current !== null) selectProject(hoveredIndexRef.current);
    };

    canvas.addEventListener("pointermove", onPointerMove);
    canvas.addEventListener("pointerdown", onPointerDown);
    canvas.addEventListener("pointerup", onPointerUp);
    canvas.addEventListener("wheel", onWheel, { passive: false });
    window.addEventListener("keydown", onKeyDown);

    const clock = new THREE.Clock();
    let frame = 0;
    let running = true;
    const animate = (now: number) => {
      if (!running) return;
      frame = window.requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();
      const currentPhase = phaseRef.current;
      if (currentPhase === "spilling" && !spillStartedAt) spillStartedAt = now;
      if (currentPhase === "selecting" && !selectedStartedAt) selectedStartedAt = now;

      const spillProgress = currentPhase === "shelf" ? 0 : currentPhase === "spilling" ? (reducedMotionRef.current ? 1 : easeOutCubic((now - spillStartedAt) / SPILL_DURATION)) : 1;
      if (currentPhase === "spilling" && (reducedMotionRef.current || now - spillStartedAt >= SPILL_DURATION)) {
        phaseRef.current = "rail";
        setPhase("rail");
        spillStartedAt = 0;
      }
      holder.rotation.z = -0.08 + spillProgress * 0.34;
      holder.position.x = -4.25 - spillProgress * 0.12;

      records.forEach((record, index) => {
        const group = record.group;
        const delayed = clamp((spillProgress - index * 0.075) / 0.92, 0, 1);
        const spillEase = easeOutCubic(delayed);
        const rail = getRailTarget(index, currentPhase === "selecting" ? selectedIndexRef.current : null);
        if (spillProgress < 1) {
          const landing = new THREE.Vector3((index - 2) * 2.1, 0.1, 0.45 - Math.abs(index - 2) * 0.4);
          group.position.lerpVectors(record.origin, landing, spillEase);
          group.position.y += Math.sin(spillEase * Math.PI) * (0.6 + index * 0.05);
          group.rotation.z = (index - 2) * 0.035 + Math.sin(spillEase * Math.PI) * (index - 2) * 0.15;
          group.rotation.y = Math.sin(spillEase * Math.PI) * (index - 2) * 0.14;
          group.scale.setScalar(1);
        } else {
          const selectionProgress = currentPhase === "selecting" && selectedIndexRef.current === index ? easeOutCubic((now - selectedStartedAt) / 900) : 0;
          const target = rail.position.clone();
          const rotation = rail.rotation;
          group.position.lerp(target, 0.13);
          group.rotation.x = THREE.MathUtils.lerp(group.rotation.x, rotation.x, 0.14);
          group.rotation.y = THREE.MathUtils.lerp(group.rotation.y, rotation.y, 0.14);
          group.rotation.z = THREE.MathUtils.lerp(group.rotation.z, rotation.z, 0.14);
          group.scale.lerp(new THREE.Vector3(rail.scale + selectionProgress * 0.08, rail.scale + selectionProgress * 0.08, rail.scale + selectionProgress * 0.08), 0.14);
          if (currentPhase === "selecting" && selectedIndexRef.current === index && !selectedRouteStarted && selectionProgress > 0.92) {
            selectedRouteStarted = true;
            window.location.assign(`/projects/${PROJECTS[index].slug}`);
          }
        }
        const hoverScale = hoveredIndexRef.current === index && currentPhase === "rail" ? 1.035 : 1;
        if (currentPhase === "rail") group.scale.multiplyScalar(hoverScale);
      });

      camera.position.x = THREE.MathUtils.lerp(camera.position.x, targetCameraX, 0.045);
      camera.position.y = THREE.MathUtils.lerp(camera.position.y, targetCameraY, 0.045);
      camera.lookAt(0, 0.15, -0.2);
      cyanLight.position.x = -5.4 + Math.sin(elapsed * 0.7) * 0.45;
      pinkLight.position.y = 2.6 + Math.cos(elapsed * 0.55) * 0.3;
      renderer.render(scene, camera);
    };
    frame = window.requestAnimationFrame(animate);

    return () => {
      running = false;
      window.cancelAnimationFrame(frame);
      resizeObserver.disconnect();
      reducedQuery.removeEventListener("change", reducedListener);
      canvas.removeEventListener("pointermove", onPointerMove);
      canvas.removeEventListener("pointerdown", onPointerDown);
      canvas.removeEventListener("pointerup", onPointerUp);
      canvas.removeEventListener("wheel", onWheel);
      window.removeEventListener("keydown", onKeyDown);
      records.forEach((record) => {
        record.texture.dispose();
        record.group.traverse((object) => {
          if (object instanceof THREE.Mesh) {
            object.geometry.dispose();
            const material = object.material;
            if (Array.isArray(material)) material.forEach((item) => item.dispose());
            else material.dispose();
          }
        });
      });
      renderer.dispose();
    };
  }, [selectProject, updateActiveIndex]);

  const phaseCopy = {
    shelf: "The archive is loaded. Tip the holder to release the records.",
    spilling: "The archive is in motion. Stand by for the landing sequence.",
    rail: "Scroll, drag, or use the arrow keys to move through the record rail.",
    selecting: `Opening ${PROJECTS[selectedIndex ?? activeIndex].title}...`,
  }[phase];

  return (
    <main className="vinyl-portfolio">
      <header className="vinyl-topbar" aria-label="Project archive navigation">
        <Link className="vinyl-brand" href="/" aria-label="Brian Zeng project archive home">
          <span className="brand-pixel">BZ</span>
          <span><b>PROJECT ARCHIVE</b><small>FULL 3D / 05 RECORDS</small></span>
        </Link>
        <div className="vinyl-top-actions">
          <button className={`sound-toggle ${soundEnabled ? "is-on" : ""}`} type="button" onClick={() => setSoundEnabled((value) => !value)} aria-pressed={soundEnabled}>
            SOUND {soundEnabled ? "ON" : "OFF"}
          </button>
          <Link href="/about">INFO DESK <span aria-hidden="true">↗</span></Link>
        </div>
      </header>

      <section className={`vinyl-stage vinyl-phase-${phase}`} ref={stageRef} aria-labelledby="vinyl-stage-title">
        <canvas ref={canvasRef} className="vinyl-webgl-canvas" aria-label="Interactive three dimensional project record archive" />
        <div className="vinyl-stage-vignette" aria-hidden="true" />

        <div className="vinyl-stage-copy">
          <p className="pixel-kicker">PROJECT ARCHIVE / 2026</p>
          <h1 id="vinyl-stage-title">Spill the archive<span>.</span></h1>
          <p>{phaseCopy}</p>
        </div>

        <aside className="vinyl-readout" aria-live="polite">
          <p className="pixel-kicker">ACTIVE RECORD / {activeProject.number}</p>
          <h2>{activeProject.title}</h2>
          <p className="vinyl-readout-category">{activeProject.category}</p>
          <p className="vinyl-readout-summary">{activeProject.summary}</p>
          {phase === "rail" && <button className="primary-control vinyl-open-control" type="button" onClick={() => selectProject(activeIndex)}>OPEN RECORD <span aria-hidden="true">↗</span></button>}
        </aside>

        {phase === "shelf" && (
          <button className="holder-hotspot" type="button" onClick={spillRecords} aria-label="Tip the vinyl holder and spill the project records">
            <span className="holder-hotspot-pip" /> TIP HOLDER
          </button>
        )}

        <div className="vinyl-rail-controls" aria-label="Project record selection">
          <div className="vinyl-rail-line" aria-hidden="true" />
          {PROJECTS.map((project, index) => (
            <button
              className={`vinyl-rail-button ${index === activeIndex ? "is-active" : ""} ${index === hoveredIndex ? "is-hovered" : ""}`}
              key={project.slug}
              type="button"
              disabled={phase !== "rail"}
              onClick={() => { updateActiveIndex(index); if (phase === "rail") selectProject(index); }}
              style={{ "--record-accent": project.accent } as CSSProperties}
              aria-label={`${project.number} ${project.title}`}
            >
              <span>{project.number}</span>
              <small>{project.shortLabel}</small>
            </button>
          ))}
        </div>

        <div className="mobile-project-menu" aria-label="Mobile project records">
          {PROJECTS.map((project, index) => (
            <button className={index === activeIndex ? "is-active" : ""} key={project.slug} type="button" onClick={() => phase === "shelf" ? spillRecords() : selectProject(index)}>
              <span style={{ color: project.accent }}>{project.number}</span>
              <span><strong>{project.title}</strong><small>{project.category}</small></span>
              <b aria-hidden="true">↗</b>
            </button>
          ))}
        </div>

        <div className="vinyl-stage-footer">
          <span><i className="status-pip" /> {phase === "shelf" ? "HOLDER LOCKED" : phase === "spilling" ? "SEQUENCE ACTIVE" : phase === "selecting" ? "RECORD OPENING" : "ARCHIVE READY"}</span>
          <span>{String(PROJECTS.length).padStart(2, "0")} RECORDS / {phase === "rail" ? "SCROLL TO SCRUB" : "CLICK TO BEGIN"}</span>
          <button type="button" onClick={replaySpill} disabled={phase === "spilling" || phase === "selecting"}>↻ REPLAY SPILL</button>
        </div>
      </section>
    </main>
  );
}
