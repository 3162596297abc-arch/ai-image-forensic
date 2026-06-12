"use client";

import React from "react";

// 全站统一按钮体系（Apple 式层级）：
//  primary   — 白底黑字胶囊，同屏唯一
//  secondary — 玻璃胶囊 + 白描边
//  tertiary  — 纯文字 + 箭头
type Variant = "primary" | "secondary" | "tertiary";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  withArrow?: boolean;
}

const BASE =
  "inline-flex items-center justify-center gap-2 rounded-full font-medium tracking-wide cursor-pointer select-none " +
  "transition-all duration-300 ease-[var(--ease-spatial)] " +
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/80 focus-visible:ring-offset-2 focus-visible:ring-offset-black " +
  "disabled:opacity-40 disabled:pointer-events-none";

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-white text-black px-7 py-3 text-sm hover:-translate-y-0.5 " +
    "hover:shadow-[0_8px_30px_rgba(255,255,255,0.18)] active:scale-[0.97] active:translate-y-0",
  secondary:
    "border border-white/25 bg-white/5 px-6 py-2.5 text-sm text-white/90 backdrop-blur-md " +
    "hover:bg-white/10 hover:border-white/40 active:scale-[0.97]",
  tertiary: "group px-1 py-1 text-xs text-white/70 hover:text-white",
};

export default function Button({
  variant = "primary",
  withArrow = variant === "tertiary",
  className = "",
  children,
  ...rest
}: ButtonProps) {
  return (
    <button className={`${BASE} ${VARIANTS[variant]} ${className}`} {...rest}>
      {children}
      {withArrow && (
        <span
          aria-hidden
          className="inline-block transition-transform duration-300 ease-[var(--ease-spatial)] group-hover:translate-x-0.5"
        >
          →
        </span>
      )}
    </button>
  );
}
