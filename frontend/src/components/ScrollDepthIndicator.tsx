"use client";

import React, { useEffect, useState } from "react";
import { motion, useScroll, useTransform, useSpring, AnimatePresence } from "framer-motion";
import Magnetic from "./Magnetic";

export default function ScrollDepthIndicator() {
  const { scrollYProgress } = useScroll();
  
  // Smooth out coordinate tracking with physical dampening spring
  const smoothProgress = useSpring(scrollYProgress, { stiffness: 120, damping: 20 });
  
  // Real-time states
  const [activeSection, setActiveSection] = useState("home");
  const [hexStamp, setHexStamp] = useState("0x0000");
  const [percentString, setPercentString] = useState("0.0%");

  // Track hex stamp generation on scroll (maps 0.0 - 1.0 directly to memory index 0x0000 - 0xFFFF)
  useEffect(() => {
    const unsubscribeHex = scrollYProgress.on("change", (latest) => {
      const intVal = Math.floor(latest * 65535);
      const hex = "0x" + intVal.toString(16).toUpperCase().padStart(4, "0");
      setHexStamp(hex);
      setPercentString((latest * 100).toFixed(1) + "%");
    });
    return () => unsubscribeHex();
  }, [scrollYProgress]);

  // Track active section via bounding boxes intersecting viewport center
  useEffect(() => {
    const handleScroll = () => {
      const sections = ["home", "manifesto", "exhibitions", "laboratory"];
      let currentSection = "home";

      for (const section of sections) {
        const el = document.getElementById(section);
        if (el) {
          const rect = el.getBoundingClientRect();
          // If section is intersecting past the middle threshold of the screen
          if (rect.top <= window.innerHeight * 0.45 && rect.bottom >= window.innerHeight * 0.45) {
            currentSection = section;
            break;
          }
        }
      }
      setActiveSection(currentSection);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    // Initial evaluation
    handleScroll();

    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Smooth glide navigation using Lenis instance
  const scrollToSection = (id: string) => {
    const lenis = (window as any).lenis;
    if (lenis) {
      lenis.scrollTo("#" + id, { offset: -90, duration: 1.6 });
    } else {
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Convert smooth spring progress directly to 256px ruler Y coordinates
  const crosshairY = useTransform(smoothProgress, [0, 1], [0, 256]);

  const sectionsList = [
    { id: "home", label: "01 // 首页", index: "01" },
    { id: "manifesto", label: "02 // 理念", index: "02" },
    { id: "exhibitions", label: "03 // 原理", index: "03" },
    { id: "laboratory", label: "04 // 检测", index: "04" },
  ];

  return (
    <div className="fixed right-10 top-1/2 -translate-y-1/2 hidden xl:flex flex-row items-center gap-10 z-40 select-none pointer-events-none">
      
      {/* 1. Volumetric Navigation labels */}
      <div className="flex flex-col gap-6 items-end pointer-events-auto">
        {sectionsList.map((item) => {
          const isActive = activeSection === item.id;
          return (
            <Magnetic key={item.id} range={24} strength={0.35}>
              <button
                onClick={() => scrollToSection(item.id)}
                className="flex items-center gap-4 group cursor-pointer text-right border-0 bg-transparent outline-none p-1"
              >
                {/* Dynamic micro-holographic banner */}
                <AnimatePresence>
                  {isActive && (
                    <motion.span
                      initial={{ opacity: 0, x: 8, scale: 0.9 }}
                      animate={{ opacity: 1, x: 0, scale: 1 }}
                      exit={{ opacity: 0, x: 4, scale: 0.9 }}
                      transition={{ duration: 0.35, ease: "easeOut" }}
                      className="font-mono text-[7px] text-zinc-400 bg-white/5 border border-white/10 px-1.5 py-0.5 rounded select-none tracking-widest"
                    >
                      状态.激活
                    </motion.span>
                  )}
                </AnimatePresence>
                
                <span
                  className={`font-mono text-[9px] tracking-widest transition-all duration-500 font-medium
                    ${isActive ? "text-white scale-105 shadow-[0_0_8px_rgba(255,255,255,0.15)]" : "text-white/20 group-hover:text-white/50"}
                  `}
                >
                  {item.label}
                </span>

                {/* Snapping bullet locator */}
                <div
                  className={`w-1.5 h-1.5 rounded-full border transition-all duration-500 origin-center
                    ${isActive ? "bg-white border-white scale-125 shadow-[0_0_8px_#ffffff]" : "bg-transparent border-white/20 group-hover:border-white/40"}
                  `}
                />
              </button>
            </Magnetic>
          );
        })}
      </div>

      {/* 2. Holographic measurement ruler scale */}
      <div className="flex flex-col items-center">
        {/* Header telemetry text */}
        <span className="font-mono text-[7px] text-white/25 tracking-widest mb-3">深度</span>
        
        {/* Physical ruler scale track */}
        <div className="w-[1px] h-64 bg-white/10 relative">
          
          {/* Micro Measurement hash marks */}
          {Array.from({ length: 9 }).map((_, i) => (
            <div
              key={i}
              className="absolute w-1.5 h-px bg-white/15 -left-[3px]"
              style={{ top: `${(i / 8) * 100}%` }}
            />
          ))}

          {/* Deceleration floating crosshair notches */}
          <motion.div
            style={{ y: crosshairY }}
            className="absolute -left-1 w-4 h-3 flex items-center pointer-events-none"
          >
            {/* Tiny neon horizontal scanner notch */}
            <div className="w-2.5 h-[1.5px] bg-white/80 shadow-[0_0_6px_rgba(255,255,255,0.8)] rounded-full" />
            
            {/* Float HUD tooltip panel next to cursor */}
            <div className="flex flex-col absolute left-6 -translate-y-1/2 font-mono text-[8px] text-white/50 items-start leading-none bg-[#0A0A0A]/80 border border-white/5 px-2 py-1.5 rounded-md backdrop-blur-md w-16 gap-1 shadow-[0_4px_16px_rgba(0,0,0,0.5)]">
              <span className="text-white/95 font-bold tracking-wider">{percentString}</span>
              <span className="text-zinc-400/90 text-[7px] font-mono tracking-widest">{hexStamp}</span>
            </div>
          </motion.div>
        </div>

        {/* Footer telemetry text */}
        <span className="font-mono text-[7px] text-white/25 tracking-widest mt-3">层级</span>
      </div>

    </div>
  );
}
