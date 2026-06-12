"use client";

import React, { useEffect, useRef } from "react";

// ----------------------------------------------------------------------------
// 「像素证物」粒子标题
//
// 产品在像素层面鉴定图片，所以标题本身就是一片被检验的像素场：
//   · 入场：粒子从乱序状态飞行汇聚成字 —— 从杂乱像素中重组出真相
//   · 常态：极轻微抖动 —— CMOS 传感器底噪（真照片的生命体征）
//   · 光弧：背景晨昏线扫过时，字内粒子升温变金，离光后缓慢冷却
//   · 鼠标：靠近拨开粒子，松开弹回 —— 真相可被扰动，但终会复位
// 纯 2D canvas，零依赖。真实文本在 sr-only span 中，canvas 仅是视觉层。
// ----------------------------------------------------------------------------

interface ParticleTitleProps {
  text: string;
  className?: string;
}

const COLD = { r: 0x9f, g: 0xc2, b: 0xff }; // 冷蓝白基底
const WARM = { r: 0xe0, g: 0xa3, b: 0x68 }; // 晨昏暖金
const SWEEP_PERIOD = 14; // 光弧扫掠周期 (s)
const SWEEP_SIGMA = 70; // 光带宽度 (px)
const MOUSE_R = 90; // 鼠标扰动半径 (px)
const SAMPLE_STEP = 3; // 采样步长 (px)

export default function ParticleTitle({ text, className = "" }: ParticleTitleProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let raf = 0;
    let running = false;
    let W = 0;
    let H = 0;

    // 粒子通道（typed array，无逐帧对象分配）
    let n = 0;
    let hx = new Float32Array(0);
    let hy = new Float32Array(0);
    let px = new Float32Array(0);
    let py = new Float32Array(0);
    let vx = new Float32Array(0);
    let vy = new Float32Array(0);
    let sz = new Float32Array(0);
    let ph = new Float32Array(0);
    let warm = new Float32Array(0);
    let bright = new Float32Array(0);

    const mouse = { x: -9999, y: -9999 };

    // 离屏采样：把字形转换成粒子 home 点阵
    const sample = () => {
      const fontPx = Math.min(120, Math.max(52, window.innerWidth * 0.105));
      const font = `600 ${fontPx}px "PingFang SC", "Microsoft YaHei", system-ui, sans-serif`;

      const off = document.createElement("canvas");
      const octx = off.getContext("2d");
      if (!octx) return;
      octx.font = font;
      const pad = Math.ceil(fontPx * 0.18);
      W = Math.ceil(octx.measureText(text).width) + pad * 2;
      H = Math.ceil(fontPx * 1.3);
      off.width = W;
      off.height = H;
      octx.font = font; // canvas 尺寸变更会重置状态
      octx.textBaseline = "middle";
      octx.fillStyle = "#fff";
      octx.fillText(text, pad, H / 2);

      const img = octx.getImageData(0, 0, W, H).data;
      const pts: number[] = [];
      for (let y = 0; y < H; y += SAMPLE_STEP) {
        for (let x = 0; x < W; x += SAMPLE_STEP) {
          if (img[(y * W + x) * 4 + 3] > 128) pts.push(x, y);
        }
      }

      n = pts.length / 2;
      hx = new Float32Array(n);
      hy = new Float32Array(n);
      px = new Float32Array(n);
      py = new Float32Array(n);
      vx = new Float32Array(n);
      vy = new Float32Array(n);
      sz = new Float32Array(n);
      ph = new Float32Array(n);
      warm = new Float32Array(n);
      bright = new Float32Array(n);

      for (let i = 0; i < n; i++) {
        hx[i] = pts[i * 2];
        hy[i] = pts[i * 2 + 1];
        // 入场：从全场乱序位置出发，弹簧自然汇聚成字
        px[i] = Math.random() * W * 1.4 - W * 0.2;
        py[i] = Math.random() * H * 2.4 - H * 0.7;
        vx[i] = (Math.random() - 0.5) * 2;
        vy[i] = (Math.random() - 0.5) * 2;
        sz[i] = 0.9 + Math.random() * 0.9;
        ph[i] = Math.random() * Math.PI * 2;
      }

      const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      canvas.width = W * dpr;
      canvas.height = H * dpr;
      canvas.style.width = `${W}px`;
      canvas.style.height = `${H}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    // reduced-motion：粒子直接归位，渲染一帧静态点阵
    const renderStatic = () => {
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = "rgba(216, 227, 240, 0.85)";
      for (let i = 0; i < n; i++) {
        ctx.fillRect(hx[i], hy[i], sz[i], sz[i]);
      }
    };

    const t0 = performance.now();
    const frame = (now: number) => {
      if (!running) return;
      const t = (now - t0) / 1000;
      // 晨昏光扫掠位置：缓慢正弦往返
      const lightX = W * (0.5 + 0.5 * Math.sin((t * 2 * Math.PI) / SWEEP_PERIOD - Math.PI / 2));

      ctx.clearRect(0, 0, W, H);
      ctx.globalCompositeOperation = "lighter";

      for (let i = 0; i < n; i++) {
        // 回家弹簧 + 阻尼
        vx[i] = (vx[i] + (hx[i] - px[i]) * 0.075) * 0.82;
        vy[i] = (vy[i] + (hy[i] - py[i]) * 0.075) * 0.82;

        // 鼠标拨动：放大镜检查像素
        const dx = px[i] - mouse.x;
        const dy = py[i] - mouse.y;
        const d2 = dx * dx + dy * dy;
        if (d2 < MOUSE_R * MOUSE_R) {
          const d = Math.sqrt(d2) || 1;
          const f = (1 - d / MOUSE_R) * 2.4;
          vx[i] += (dx / d) * f;
          vy[i] += (dy / d) * f;
        }

        px[i] += vx[i];
        py[i] += vy[i];

        // 晨昏光潮汐：升温快、冷却慢（热惯性）
        const lx = px[i] - lightX;
        const heat = Math.exp(-(lx * lx) / (2 * SWEEP_SIGMA * SWEEP_SIGMA));
        warm[i] += (heat - warm[i]) * (heat > warm[i] ? 0.1 : 0.045);
        bright[i] += (heat - bright[i]) * 0.1;

        // CMOS 底噪微抖（渲染层叠加，不进物理）
        const jx = Math.sin(t * 2.1 + ph[i]) * 0.35;
        const jy = Math.cos(t * 1.7 + ph[i] * 1.3) * 0.35;

        const w = warm[i];
        const r = (COLD.r + (WARM.r - COLD.r) * w) | 0;
        const g = (COLD.g + (WARM.g - COLD.g) * w) | 0;
        const b = (COLD.b + (WARM.b - COLD.b) * w) | 0;
        const a = 0.5 + bright[i] * 0.45;
        ctx.fillStyle = `rgba(${r},${g},${b},${a})`;
        ctx.fillRect(px[i] + jx, py[i] + jy, sz[i], sz[i]);
      }

      ctx.globalCompositeOperation = "source-over";
      raf = requestAnimationFrame(frame);
    };

    const start = () => {
      if (running || reduced) return;
      running = true;
      raf = requestAnimationFrame(frame);
    };
    const stop = () => {
      running = false;
      cancelAnimationFrame(raf);
    };

    sample();
    if (reduced) {
      renderStatic();
    } else {
      start();
    }

    const onMouse = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    };
    const onLeave = () => {
      mouse.x = -9999;
      mouse.y = -9999;
    };
    window.addEventListener("mousemove", onMouse, { passive: true });
    window.addEventListener("mouseout", onLeave, { passive: true });

    let resizeTimer: ReturnType<typeof setTimeout> | undefined;
    const onResize = () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        sample();
        if (reduced) renderStatic();
      }, 200);
    };
    window.addEventListener("resize", onResize);

    // 滚出视口即暂停，CPU 归零
    const io = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) start();
      else stop();
    });
    io.observe(canvas);

    return () => {
      stop();
      clearTimeout(resizeTimer);
      window.removeEventListener("mousemove", onMouse);
      window.removeEventListener("mouseout", onLeave);
      window.removeEventListener("resize", onResize);
      io.disconnect();
    };
  }, [text]);

  return (
    <span className={`relative inline-block ${className}`}>
      <span className="sr-only">{text}</span>
      <canvas ref={canvasRef} aria-hidden className="block" />
    </span>
  );
}
