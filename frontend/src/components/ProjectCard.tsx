"use client";

import React, { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import Image from "next/image";
import { ArrowUpRight } from "lucide-react";
import Magnetic from "./Magnetic";

interface ProjectCardProps {
  index: string;
  title: string;
  category: string;
  description: string;
  imageSrc: string;
  link?: string;
}

export default function ProjectCard({
  index,
  title,
  category,
  description,
  imageSrc,
  link = "#",
}: ProjectCardProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  // Track the card's position relative to the viewport
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  });

  // Inertial Parallax: slides the image inside its bounds
  const imageY = useTransform(scrollYProgress, [0, 1], ["-12%", "12%"]);
  // Subtle scaling transition
  const imageScale = useTransform(scrollYProgress, [0, 0.5, 1], [1.16, 1.08, 1.01]);

  return (
    <div
      ref={containerRef}
      className="group relative w-full flex flex-col gap-6 text-white select-none z-10"
    >
      {/* 1. Image viewport (overflow hidden contains the moving image) */}
      <div className="relative w-full aspect-[16/10] overflow-hidden rounded-2xl border border-white/5 bg-[#08080f] spatial-glass shadow-[0_8px_32px_rgba(0,0,0,0.5)] transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:border-white/15 group-hover:shadow-[0_20px_40px_rgba(0,0,0,0.7)]">
        {/* Parallax moving image wrapper */}
        <motion.div
          style={{ y: imageY, scale: imageScale }}
          className="absolute -inset-y-16 inset-x-0 w-full h-[calc(100%+128px)] origin-center"
        >
          <Image
            src={imageSrc}
            alt={title}
            fill
            sizes="(max-width: 768px) 100vw, 50vw"
            className="object-cover object-center opacity-80 transition-opacity duration-700 group-hover:opacity-95"
          />
        </motion.div>

        {/* Ambient Dark Overlay to assure readability and luxury atmosphere */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#020205]/85 via-transparent to-black/20 pointer-events-none" />

        {/* Hover boundary glows */}
        <div className="absolute inset-0 border border-white/0 group-hover:border-white/10 rounded-2xl transition-all duration-700 pointer-events-none" />
        <div className="absolute -inset-px bg-gradient-to-tr from-white/0 via-white/2 to-white/6 opacity-0 group-hover:opacity-100 transition-opacity duration-700 rounded-2xl pointer-events-none" />

        {/* Spatial capsule indicator (category) */}
        <div className="absolute top-4 left-4 flex items-center gap-2">
          <span className="px-3 py-1 rounded-full text-[9px] font-mono tracking-widest text-white/70 uppercase bg-black/40 border border-white/5 backdrop-blur-md">
            {category}
          </span>
        </div>

        {/* Magnetic Snapping Action Arrow */}
        <div className="absolute bottom-5 right-5 z-20">
          <Magnetic range={40} strength={0.4}>
            <a
              href={link}
              aria-label={title}
              className="flex h-11 w-11 items-center justify-center rounded-full bg-black/40 border border-white/10 text-white/80 transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:bg-white group-hover:text-[#020205] group-hover:border-white group-hover:scale-105 active:scale-95"
            >
              <ArrowUpRight 
                size={16} 
                className="transition-transform duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:rotate-45" 
              />
            </a>
          </Magnetic>
        </div>
      </div>

      {/* 2. Fine metadata details */}
      <div className="flex flex-col gap-2.5 px-1">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[10px] text-white/30 tracking-widest uppercase">
            {index}
          </span>
          <h3 className="text-lg font-medium tracking-wide text-white/90 group-hover:text-white transition-colors duration-300">
            {title}
          </h3>
        </div>
        <p className="text-xs text-white/40 leading-relaxed font-light tracking-wide font-sans pl-7 max-w-[90%]">
          {description}
        </p>
      </div>
    </div>
  );
}
