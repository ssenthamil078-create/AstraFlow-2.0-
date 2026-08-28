/**
 * FinancialEarth - Interactive 3D WebGL Financial Globe
 * The central signature hero experience of AstraFlow.
 */

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { FinancialNode } from '../types.ts';

interface FinancialEarthProps {
  nodes?: FinancialNode[];
  confirmedBalance?: number;
  currency?: string;
  selectedNodeId?: string | null;
  onNodeClick?: (node: FinancialNode) => void;
  onNodeHover?: (node: FinancialNode | null, mousePos: { x: number; y: number } | null) => void;
  autoRotate?: boolean;
  interactive?: boolean;
  className?: string;
  showCenterLabel?: boolean;
}

export const FinancialEarth: React.FC<FinancialEarthProps> = ({
  nodes = [],
  confirmedBalance = 845000,
  currency = '₹',
  selectedNodeId = null,
  onNodeClick,
  onNodeHover,
  autoRotate = true,
  interactive = true,
  className = '',
  showCenterLabel = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredNode, setHoveredNode] = useState<FinancialNode | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let width = container.clientWidth || 500;
    let height = container.clientHeight || 500;

    // 1. Scene & Camera Setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0.5, 9.5);

    // 2. Renderer
    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance',
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 3. Lighting
    const ambientLight = new THREE.AmbientLight(0x1a243b, 1.8);
    scene.add(ambientLight);

    const primaryLight = new THREE.PointLight(0x00f2ff, 2.5, 30);
    primaryLight.position.set(6, 5, 8);
    scene.add(primaryLight);

    const secondaryLight = new THREE.PointLight(0xb600f8, 2.0, 30);
    secondaryLight.position.set(-6, -4, 6);
    scene.add(secondaryLight);

    const rimLight = new THREE.DirectionalLight(0x22d3ee, 1.2);
    rimLight.position.set(0, 8, -6);
    scene.add(rimLight);

    // 4. Procedural High-Tech Financial Earth Texture
    const canvas = document.createElement('canvas');
    canvas.width = 2048;
    canvas.height = 1024;
    const ctx = canvas.getContext('2d');

    if (ctx) {
      // Dark cosmic ocean
      const oceanGrad = ctx.createLinearGradient(0, 0, 0, 1024);
      oceanGrad.addColorStop(0, '#030818');
      oceanGrad.addColorStop(0.5, '#060d26');
      oceanGrad.addColorStop(1, '#030818');
      ctx.fillStyle = oceanGrad;
      ctx.fillRect(0, 0, 2048, 1024);

      // High-tech longitude & latitude grid
      ctx.strokeStyle = 'rgba(0, 242, 255, 0.08)';
      ctx.lineWidth = 1;

      // Latitudes
      for (let y = 0; y <= 1024; y += 64) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(2048, y);
        ctx.stroke();
      }
      // Longitudes
      for (let x = 0; x <= 2048; x += 64) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, 1024);
        ctx.stroke();
      }

      // Stylized glowing financial continent clusters (Digital landmass dot-matrix)
      ctx.fillStyle = 'rgba(34, 211, 238, 0.6)';
      const continentBlobs = [
        // North America & Europe trade hubs
        { cx: 500, cy: 380, rx: 220, ry: 150 },
        { cx: 1050, cy: 340, rx: 180, ry: 120 },
        // Asia / India financial hubs
        { cx: 1420, cy: 450, rx: 240, ry: 160 },
        { cx: 1580, cy: 400, rx: 140, ry: 100 },
        // South America & Africa
        { cx: 680, cy: 680, rx: 160, ry: 200 },
        { cx: 1100, cy: 600, rx: 170, ry: 180 },
        // Oceania
        { cx: 1720, cy: 750, rx: 120, ry: 90 },
      ];

      continentBlobs.forEach((blob) => {
        // Draw dotted matrix landmass
        const dots = 300;
        for (let i = 0; i < dots; i++) {
          const angle = Math.random() * Math.PI * 2;
          const r = Math.sqrt(Math.random());
          const x = blob.cx + Math.cos(angle) * blob.rx * r;
          const y = blob.cy + Math.sin(angle) * blob.ry * r;
          if (x >= 0 && x <= 2048 && y >= 0 && y <= 1024) {
            ctx.beginPath();
            ctx.arc(x, y, 1.8, 0, Math.PI * 2);
            ctx.fillStyle = Math.random() > 0.4 ? 'rgba(0, 242, 255, 0.5)' : 'rgba(182, 0, 248, 0.4)';
            ctx.fill();
          }
        }
      });

      // Neon financial trade routes
      ctx.strokeStyle = 'rgba(0, 242, 255, 0.35)';
      ctx.lineWidth = 1.5;
      const routes = [
        [500, 380, 1050, 340],
        [1050, 340, 1420, 450],
        [1420, 450, 1720, 750],
        [500, 380, 680, 680],
        [1050, 340, 1100, 600],
      ];
      routes.forEach(([x1, y1, x2, y2]) => {
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        const cpX = (x1 + x2) / 2;
        const cpY = Math.min(y1, y2) - 80;
        ctx.quadraticCurveTo(cpX, cpY, x2, y2);
        ctx.stroke();
      });
    }

    const earthTexture = new THREE.CanvasTexture(canvas);
    earthTexture.wrapS = THREE.RepeatWrapping;
    earthTexture.wrapT = THREE.ClampToEdgeWrapping;

    // 5. Earth Core Sphere Mesh
    const earthGeometry = new THREE.SphereGeometry(2.35, 64, 64);
    const earthMaterial = new THREE.MeshStandardMaterial({
      map: earthTexture,
      roughness: 0.7,
      metalness: 0.25,
      bumpScale: 0.05,
    });
    const earthMesh = new THREE.Mesh(earthGeometry, earthMaterial);
    scene.add(earthMesh);

    // Glowing Wireframe Core Overlay (Subtle Tech Geometry)
    const wireframeGeo = new THREE.IcosahedronGeometry(2.38, 2);
    const wireframeMat = new THREE.MeshBasicMaterial({
      color: 0x00f2ff,
      wireframe: true,
      transparent: true,
      opacity: 0.07,
    });
    const wireframeMesh = new THREE.Mesh(wireframeGeo, wireframeMat);
    earthMesh.add(wireframeMesh);

    // 6. Atmospheric Glow Layer
    const atmosphereGeo = new THREE.SphereGeometry(2.46, 48, 48);
    const atmosphereMat = new THREE.MeshStandardMaterial({
      color: 0x00f2ff,
      transparent: true,
      opacity: 0.12,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
      roughness: 1,
    });
    const atmosphereMesh = new THREE.Mesh(atmosphereGeo, atmosphereMat);
    scene.add(atmosphereMesh);

    // Outer Halo Haze
    const outerHaloGeo = new THREE.SphereGeometry(2.65, 32, 32);
    const outerHaloMat = new THREE.MeshBasicMaterial({
      color: 0x8b5cf6,
      transparent: true,
      opacity: 0.05,
      blending: THREE.AdditiveBlending,
      side: THREE.BackSide,
    });
    const outerHaloMesh = new THREE.Mesh(outerHaloGeo, outerHaloMat);
    scene.add(outerHaloMesh);

    // 7. Cosmic Particle Field (Stars & Dust)
    const particleCount = 450;
    const particleGeometry = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    const particleColors = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
      const radius = 5.5 + Math.random() * 8.0;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);

      particlePositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      particlePositions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      particlePositions[i * 3 + 2] = radius * Math.cos(phi);

      const isCyan = Math.random() > 0.45;
      particleColors[i * 3] = isCyan ? 0.0 : 0.7;
      particleColors[i * 3 + 1] = isCyan ? 0.95 : 0.3;
      particleColors[i * 3 + 2] = 1.0;
    }

    particleGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
    particleGeometry.setAttribute('color', new THREE.BufferAttribute(particleColors, 3));

    const particleMaterial = new THREE.PointsMaterial({
      size: 0.08,
      vertexColors: true,
      transparent: true,
      opacity: 0.65,
      blending: THREE.AdditiveBlending,
    });
    const particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);

    // 8. Orbital Rings & Interactive Financial Nodes
    const nodeObjects: Array<{
      mesh: THREE.Mesh;
      halo: THREE.Mesh;
      nodeData: FinancialNode;
      radius: number;
      speed: number;
      inclination: number;
      phase: number;
    }> = [];

    const orbitGroup = new THREE.Group();
    scene.add(orbitGroup);

    nodes.forEach((node, idx) => {
      const orbitRadius = node.orbitRadius || 3.2 + idx * 0.45;
      const orbitSpeed = node.orbitSpeed || 0.35 + idx * 0.06;
      const orbitInclination = node.orbitInclination || 0.2 + idx * 0.15;
      const orbitPhase = node.orbitPhase || (idx * Math.PI * 2) / (nodes.length || 1);

      // Glowing Orbit Ring
      const ringGeo = new THREE.RingGeometry(orbitRadius - 0.015, orbitRadius + 0.015, 96);
      const ringMat = new THREE.MeshBasicMaterial({
        color: new THREE.Color(node.color || '#00f2ff'),
        transparent: true,
        opacity: 0.16,
        side: THREE.DoubleSide,
        blending: THREE.AdditiveBlending,
      });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = Math.PI / 2 + orbitInclination;
      ringMesh.rotation.y = orbitInclination * 0.5;
      orbitGroup.add(ringMesh);

      // Node Sphere
      const sphereRadius = 0.12 * (node.size || 1.0);
      const nodeGeo = new THREE.SphereGeometry(sphereRadius, 24, 24);
      const nodeColor = new THREE.Color(node.color || '#00f2ff');

      const nodeMat = new THREE.MeshStandardMaterial({
        color: nodeColor,
        emissive: nodeColor,
        emissiveIntensity: 0.9,
        roughness: 0.3,
        metalness: 0.8,
      });
      const nodeMesh = new THREE.Mesh(nodeGeo, nodeMat);
      nodeMesh.userData = { node };

      // Halo Sprite / Outer Glow Sphere for node
      const haloGeo = new THREE.SphereGeometry(sphereRadius * 1.8, 16, 16);
      const haloMat = new THREE.MeshBasicMaterial({
        color: nodeColor,
        transparent: true,
        opacity: 0.25,
        blending: THREE.AdditiveBlending,
      });
      const haloMesh = new THREE.Mesh(haloGeo, haloMat);
      nodeMesh.add(haloMesh);

      scene.add(nodeMesh);

      nodeObjects.push({
        mesh: nodeMesh,
        halo: haloMesh,
        nodeData: node,
        radius: orbitRadius,
        speed: orbitSpeed,
        inclination: orbitInclination,
        phase: orbitPhase,
      });
    });

    // 9. Interaction & Raycasting
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2(-999, -999);
    let isDragging = false;
    let previousMousePosition = { x: 0, y: 0 };
    let dragVelocity = { x: 0, y: 0 };
    let lastInteractionTime = Date.now();
    let currentRotationY = 0;
    let currentRotationX = 0;

    const onPointerDown = (e: MouseEvent | TouchEvent) => {
      if (!interactive) return;
      isDragging = true;
      lastInteractionTime = Date.now();
      const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
      const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
      previousMousePosition = { x: clientX, y: clientY };
    };

    const onPointerMove = (e: MouseEvent | TouchEvent) => {
      const rect = container.getBoundingClientRect();
      const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
      const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;

      // Update normalized mouse coordinates for raycaster
      mouse.x = ((clientX - rect.left) / width) * 2 - 1;
      mouse.y = -((clientY - rect.top) / height) * 2 + 1;

      if (isDragging && interactive) {
        lastInteractionTime = Date.now();
        const deltaX = clientX - previousMousePosition.x;
        const deltaY = clientY - previousMousePosition.y;

        dragVelocity = { x: deltaX * 0.005, y: deltaY * 0.005 };
        currentRotationY += dragVelocity.x;
        currentRotationX = Math.max(-0.6, Math.min(0.6, currentRotationX + dragVelocity.y));

        previousMousePosition = { x: clientX, y: clientY };
      }

      // Check node hover
      if (!isDragging) {
        raycaster.setFromCamera(mouse, camera);
        const nodeMeshes = nodeObjects.map((n) => n.mesh);
        const intersects = raycaster.intersectObjects(nodeMeshes, true);

        if (intersects.length > 0) {
          container.style.cursor = 'pointer';
          let foundMesh = intersects[0].object as THREE.Mesh;
          while (foundMesh.parent && !foundMesh.userData.node && foundMesh.parent !== scene) {
            foundMesh = foundMesh.parent as THREE.Mesh;
          }
          const matched = foundMesh.userData.node as FinancialNode;
          if (matched) {
            setHoveredNode(matched);
            setTooltipPos({ x: clientX - rect.left, y: clientY - rect.top });
            if (onNodeHover) onNodeHover(matched, { x: clientX - rect.left, y: clientY - rect.top });
          }
        } else {
          container.style.cursor = isDragging ? 'grabbing' : 'grab';
          if (hoveredNode) {
            setHoveredNode(null);
            if (onNodeHover) onNodeHover(null, null);
          }
        }
      }
    };

    const onPointerUp = (e: MouseEvent | TouchEvent) => {
      if (isDragging) {
        isDragging = false;
        lastInteractionTime = Date.now();
      }
    };

    const onPointerClick = (e: MouseEvent) => {
      if (!interactive) return;
      const rect = container.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const nodeMeshes = nodeObjects.map((n) => n.mesh);
      const intersects = raycaster.intersectObjects(nodeMeshes, true);

      if (intersects.length > 0) {
        let foundMesh = intersects[0].object as THREE.Mesh;
        while (foundMesh.parent && !foundMesh.userData.node && foundMesh.parent !== scene) {
          foundMesh = foundMesh.parent as THREE.Mesh;
        }
        const matched = foundMesh.userData.node as FinancialNode;
        if (matched && onNodeClick) {
          onNodeClick(matched);
        }
      }
    };

    const onWheel = (e: WheelEvent) => {
      if (!interactive) return;
      e.preventDefault();
      lastInteractionTime = Date.now();
      camera.position.z = Math.max(6.5, Math.min(14.0, camera.position.z + e.deltaY * 0.005));
    };

    const onDoubleClick = () => {
      if (!interactive) return;
      camera.position.set(0, 0.5, 9.5);
      currentRotationX = 0;
    };

    container.addEventListener('mousedown', onPointerDown);
    window.addEventListener('mousemove', onPointerMove);
    window.addEventListener('mouseup', onPointerUp);
    container.addEventListener('click', onPointerClick);
    container.addEventListener('wheel', onWheel, { passive: false });
    container.addEventListener('dblclick', onDoubleClick);

    container.addEventListener('touchstart', onPointerDown, { passive: true });
    window.addEventListener('touchmove', onPointerMove, { passive: true });
    window.addEventListener('touchend', onPointerUp, { passive: true });

    // 10. Animation Loop
    let animationFrameId: number;
    const startTime = performance.now();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = (performance.now() - startTime) / 1000; // seconds

      // Continuous Earth Roll / Rotation
      const idleTime = Date.now() - lastInteractionTime;
      const isIdle = idleTime > 1500;

      if (autoRotate) {
        if (!isDragging) {
          // Smooth inertia damping when letting go of drag
          currentRotationY += dragVelocity.x;
          dragVelocity.x *= 0.94;
          dragVelocity.y *= 0.94;

          // Natural continuous rotation
          const baseSpeed = isIdle ? 0.0035 : 0.001;
          currentRotationY += baseSpeed;
        }
      }

      earthMesh.rotation.y = currentRotationY;
      earthMesh.rotation.x = currentRotationX;
      atmosphereMesh.rotation.y = currentRotationY * 0.8;
      outerHaloMesh.rotation.y = -currentRotationY * 0.4;
      particles.rotation.y = currentRotationY * 0.15;

      // Animate Orbiting Financial Nodes
      nodeObjects.forEach((n, idx) => {
        const angle = n.phase + elapsedTime * n.speed * 0.5;
        const x = Math.cos(angle) * n.radius;
        const z = Math.sin(angle) * n.radius;
        const y = Math.sin(angle * 1.5) * (n.inclination * 0.8);

        n.mesh.position.set(x, y, z);

        // Highlight selected or hovered node
        const isSelected = selectedNodeId === n.nodeData.id;
        const isHovered = hoveredNode?.id === n.nodeData.id;

        if (isSelected || isHovered) {
          n.mesh.scale.set(1.4, 1.4, 1.4);
          n.halo.scale.set(2.2, 2.2, 2.2);
          (n.halo.material as THREE.MeshBasicMaterial).opacity = 0.5;
        } else {
          // Pulsing animation for uncertain nodes
          const pulse = n.nodeData.status === 'UNCERTAIN' ? 1.0 + Math.sin(elapsedTime * 4.0) * 0.2 : 1.0;
          n.mesh.scale.set(pulse, pulse, pulse);
          n.halo.scale.set(1.8, 1.8, 1.8);
          (n.halo.material as THREE.MeshBasicMaterial).opacity = 0.25;
        }
      });

      renderer.render(scene, camera);
    };

    animate();

    // 11. Handle Container Resize
    const handleResize = () => {
      if (!container) return;
      width = container.clientWidth || 500;
      height = container.clientHeight || 500;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    // Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      resizeObserver.disconnect();

      container.removeEventListener('mousedown', onPointerDown);
      window.removeEventListener('mousemove', onPointerMove);
      window.removeEventListener('mouseup', onPointerUp);
      container.removeEventListener('click', onPointerClick);
      container.removeEventListener('wheel', onWheel);
      container.removeEventListener('dblclick', onDoubleClick);

      container.removeEventListener('touchstart', onPointerDown);
      window.removeEventListener('touchmove', onPointerMove);
      window.removeEventListener('touchend', onPointerUp);

      earthGeometry.dispose();
      earthMaterial.dispose();
      earthTexture.dispose();
      renderer.dispose();
    };
  }, [nodes, autoRotate, interactive, selectedNodeId]);

  return (
    <div className={`relative w-full h-full flex items-center justify-center select-none overflow-hidden ${className}`}>
      {/* 3D WebGL Canvas Container */}
      <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Center Financial Twin Metric Overlay */}
      {showCenterLabel && (
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none z-10">
          <div className="text-center px-6 py-4 rounded-2xl backdrop-blur-[2px] bg-radial from-[#050816]/70 via-transparent to-transparent">
            <span className="font-label-caps text-[12px] font-bold text-[#b600f8] tracking-[0.2em] uppercase block mb-1 drop-shadow-[0_0_8px_rgba(182,0,248,0.6)]">
              TOTAL NET WORTH
            </span>
            <div className="text-4xl md:text-5xl lg:text-[52px] font-extrabold text-white tracking-tight drop-shadow-[0_0_25px_rgba(0,242,255,0.7)] font-heading leading-tight">
              {currency}{confirmedBalance.toLocaleString('en-IN')}
            </div>
            <div className="mt-2 flex items-center justify-center gap-2 text-xs text-cyan-300/80 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
              <span>Financial Earth Living Twin • 60 FPS</span>
            </div>
          </div>
        </div>
      )}

      {/* Floating Node Tooltip */}
      {hoveredNode && (
        <div
          className="absolute z-20 pointer-events-none transition-transform duration-75 ease-out"
          style={{
            left: `${tooltipPos.x + 16}px`,
            top: `${tooltipPos.y - 48}px`,
          }}
        >
          <div className="glass-panel px-3.5 py-2.5 rounded-xl border border-cyan-400/40 shadow-[0_0_20px_rgba(0,242,255,0.25)] min-w-[180px]">
            <div className="flex items-center justify-between gap-2 mb-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 font-heading">
                {hoveredNode.type}
              </span>
              <span
                className={`text-[9px] px-1.5 py-0.5 rounded-full font-semibold ${
                  hoveredNode.status === 'CONFIRMED'
                    ? 'bg-emerald-500/20 text-emerald-300'
                    : hoveredNode.status === 'LIKELY'
                    ? 'bg-cyan-500/20 text-cyan-300'
                    : 'bg-amber-500/20 text-amber-300 animate-pulse'
                }`}
              >
                {hoveredNode.status}
              </span>
            </div>
            <div className="font-semibold text-white text-sm truncate max-w-[200px]">
              {hoveredNode.label}
            </div>
            <div className="text-cyan-200 text-xs font-bold data-mono mt-0.5">
              {currency}{hoveredNode.amount.toLocaleString('en-IN')}
            </div>
            {hoveredNode.secondaryInfo && (
              <div className="text-[11px] text-slate-400 mt-1 border-t border-white/10 pt-1">
                {hoveredNode.secondaryInfo}
              </div>
            )}
            <div className="text-[9px] text-cyan-400/80 mt-1 flex items-center gap-1">
              <span>Click node to inspect →</span>
            </div>
          </div>
        </div>
      )}

      {/* Interaction Hints (Bottom Center) */}
      <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-3 px-3 py-1 rounded-full bg-[#080f10]/80 border border-slate-800/80 text-[11px] text-slate-400 pointer-events-none backdrop-blur-md">
        <span>Drag to rotate</span>
        <span className="w-1 h-1 rounded-full bg-slate-600" />
        <span>Scroll to zoom</span>
        <span className="w-1 h-1 rounded-full bg-slate-600" />
        <span>Click node to inspect</span>
      </div>
    </div>
  );
};
