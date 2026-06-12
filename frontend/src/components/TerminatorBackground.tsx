"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

// ----------------------------------------------------------------------------
// 轨道环境光 / 晨昏线背景（Orbital Ambient Light）
//
// 移植自用户设计的 前端背景.html：一道发光的轨道弧线，像从太空看地球的
// 晨昏线——被照亮的光段沿弧线单向匀速扫过（36s 一圈，无来回摆动、无端点），
// 从一侧驶出再从另一侧无缝驶入。叠加极缓慢的呼吸（16s，浅幅 78%→100%）。
// 弧顶锚定在屏幕垂直中心（hero 位置）。背景为近黑，带极微弱的纵向层次。
// ----------------------------------------------------------------------------

const VERT = /* glsl */ `
  void main() {
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const FRAG = /* glsl */ `
  uniform float uTime;
  uniform vec2  uRes;
  uniform float uReduceMotion;

  #define PI 3.14159265359
  #define TWO_PI 6.28318530718

  // ---- palette ----
  const vec3 C_PRIMARY = vec3(0.482, 0.659, 1.000); // #7BA8FF
  const vec3 C_SECOND  = vec3(0.353, 0.529, 1.000); // #5A87FF
  const vec3 C_OUTER   = vec3(0.184, 0.373, 0.847); // #2F5FD8
  const vec3 C_SCATTER = vec3(0.749, 0.839, 1.000); // #BFD6FF

  float g(float x, float s){ return exp(-(x*x)/(2.0*s*s)); }

  void arcInfo(vec2 p, float R, vec2 c, out float radial, out float ang){
    vec2 d = p - c;
    float r = length(d);
    radial = r - R;
    ang = atan(d.y, d.x);
  }

  float arcBand(float radial, float thickness){
    return g(radial, thickness);
  }

  void main(){
    vec2 frag = gl_FragCoord.xy;
    vec2 p = frag / uRes.x;
    float aspectH = uRes.y / uRes.x;

    // ---- geometry: 80vw radius, apex at screen vertical center ----
    float R = 0.80;
    float centerX = 0.5;
    float screenCenterY = aspectH * 0.5;
    float cy = screenCenterY - R;
    vec2  c  = vec2(centerX, cy);

    float radial, ang;
    arcInfo(p, R, c, radial, ang);

    float thickness = (4.5 / uRes.x);

    // ---- moving illuminated segment: single-direction drift, seamless loop ----
    float tt = uReduceMotion > 0.5 ? 18.0 : uTime;

    float angStart = radians(15.0);
    float angEnd   = radians(165.0);
    float sweep = mod(tt / 36.0, 1.0);
    float centerAng = mix(angStart, angEnd, sweep);

    float segSigma = radians(60.0) / 4.0;

    float dAng = ang - centerAng;
    float energy = g(dAng, segSigma);

    float edgeFade = smoothstep(0.0, 0.12, sweep) * smoothstep(1.0, 0.88, sweep);
    energy *= edgeFade;

    // ---- breathing: slow, shallow ----
    float bphase = uReduceMotion > 0.5 ? 0.8 :
                   0.5 + 0.5 * cos(tt * (TWO_PI / 16.0));
    float breath = mix(0.78, 1.0, bphase);
    energy *= breath;

    // restrict to upper half arc softly
    float upper = smoothstep(-0.15, 0.15, sin(ang));
    energy *= upper;

    // ---- multi-layer light structure ----
    vec3 col = vec3(0.0);

    float b1 = arcBand(radial, thickness) * energy;
    col += C_PRIMARY * b1 * 1.0;

    float core = arcBand(radial, thickness*0.45) * energy;
    col += C_SCATTER * core * 0.6;

    float b2 = arcBand(radial - thickness*1.8, thickness*1.6) * energy;
    col += C_SECOND * b2 * 0.25;

    float diff = arcBand(radial - thickness*4.0, thickness*5.0) * energy;
    col += C_OUTER * diff * 0.16;

    float halo = arcBand(radial, thickness*12.0) * energy;
    col += C_SCATTER * halo * 0.045;

    float fog = arcBand(max(radial,0.0), thickness*26.0) * energy;
    col += C_OUTER * fog * 0.03;

    // ---- background: near-black with very subtle vertical depth ----
    vec3 bgA = vec3(0.0157,0.0196,0.0275); // #040507
    vec3 bgB = vec3(0.0235,0.0314,0.0471); // #06080C
    vec3 bgC = vec3(0.0314,0.0431,0.0627); // #080B10
    float by = clamp(p.y / max(aspectH,0.0001), 0.0, 1.0);
    vec3 bg = mix(bgA, mix(bgB, bgC, smoothstep(0.4,1.0,by)), smoothstep(0.0,0.6,by));

    col += bg;
    col *= 1.15;

    gl_FragColor = vec4(col, 1.0);
  }
`;

const OrbitalScene = ({ reduced }: { reduced: boolean }) => {
  const materialRef = useRef<THREE.ShaderMaterial>(null);
  const timeRef = useRef(reduced ? 18 : 0);
  const { size, viewport, gl } = useThree();

  const uniforms = useMemo(
    () => ({
      uTime: { value: reduced ? 18 : 0 },
      uRes: { value: new THREE.Vector2(1, 1) },
      uReduceMotion: { value: reduced ? 1 : 0 },
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  // uRes 必须是帧缓冲实际像素（含 DPR），与 gl_FragCoord 对齐
  useEffect(() => {
    if (materialRef.current) {
      const dpr = gl.getPixelRatio();
      materialRef.current.uniforms.uRes.value.set(size.width * dpr, size.height * dpr);
    }
  }, [size.width, size.height, gl]);

  useFrame((_, delta) => {
    if (reduced) return; // 静帧
    timeRef.current += delta;
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = timeRef.current;
    }
  });

  return (
    <mesh>
      <planeGeometry args={[viewport.width, viewport.height]} />
      <shaderMaterial
        ref={materialRef}
        uniforms={uniforms}
        depthTest={false}
        depthWrite={false}
        vertexShader={VERT}
        fragmentShader={FRAG}
      />
    </mesh>
  );
};

// WebGL 创建失败时落到静态渐变，页面不白屏
class GLBoundary extends React.Component<
  { fallback: React.ReactNode; children: React.ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

export const TerminatorBackground = () => {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(mq.matches);
    const onChange = (e: MediaQueryListEvent) => setReduced(e.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const fallback = <div className="absolute inset-0 terminator-fallback" />;

  return (
    <div className="fixed inset-0 z-0 pointer-events-none bg-[#040507]">
      <GLBoundary fallback={fallback}>
        <Canvas
          camera={{ position: [0, 0, 10], fov: 75 }}
          frameloop={reduced ? "demand" : "always"}
          gl={{
            alpha: false,
            antialias: true,
            powerPreference: "high-performance",
            toneMapping: THREE.ACESFilmicToneMapping,
            toneMappingExposure: 1.08,
          }}
          dpr={[1, 2]}
        >
          <OrbitalScene reduced={reduced} />
        </Canvas>
      </GLBoundary>
    </div>
  );
};
