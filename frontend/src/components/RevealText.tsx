"use client";

import React from "react";
import { motion } from "framer-motion";

interface RevealTextProps {
  text: string;
  className?: string;
  delay?: number;
  by?: "words" | "chars";
  once?: boolean;
}

export default function RevealText({
  text,
  className = "",
  delay = 0,
  by = "words",
  once = true,
}: RevealTextProps) {
  // Container orchestrating staggered animations for children
  const containerVariants = {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: by === "chars" ? 0.02 : 0.06,
        delayChildren: delay,
      },
    },
  };

  // Child element animating upwards from masking overflow boundary
  const childVariants = {
    hidden: {
      y: "115%",
      opacity: 0,
    },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.9,
        ease: [0.16, 1, 0.3, 1] as const, // Expansive cinematic deceleration ease
      },
    },
  };

  // Tokenize text based on characters or words
  const items = by === "chars" ? Array.from(text) : text.split(" ");

  return (
    <motion.span
      variants={containerVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once, margin: "-10% 0px -10% 0px" }}
      className={`inline-block select-none ${className}`}
    >
      {items.map((item, idx) => {
        const isSpace = item === " ";
        return (
          <span
            key={idx}
            className="inline-block overflow-hidden"
            style={{ 
              verticalAlign: "bottom", 
              paddingBottom: "0.18em", 
              marginBottom: "-0.18em" // Safeguards letters like y, g, p from overflow clipping
            }}
          >
            <motion.span
              variants={childVariants}
              className="inline-block"
              style={{ display: "inline-block" }}
            >
              {by === "chars" ? (isSpace ? "\u00A0" : item) : item}
            </motion.span>
            {by === "words" && idx < items.length - 1 && (
              <span className="inline-block">&nbsp;</span>
            )}
          </span>
        );
      })}
    </motion.span>
  );
}
