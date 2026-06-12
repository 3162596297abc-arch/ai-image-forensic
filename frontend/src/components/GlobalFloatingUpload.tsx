"use client";

import React, { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, X } from "lucide-react";
import { UploadDevice } from "./UploadDevice";

interface Props {
  onUpload: (file: File) => void;
  visible: boolean;
}

export const GlobalFloatingUpload: React.FC<Props> = ({ onUpload, visible }) => {
  const [isOpen, setIsOpen] = useState(false);
  const closeBtnRef = useRef<HTMLButtonElement>(null);

  // 弹窗打开：锁滚动 + 焦点移入关闭按钮 + Esc 关闭
  useEffect(() => {
    if (!isOpen) return;
    const lenis = (window as unknown as { lenis?: { stop(): void; start(): void } }).lenis;
    lenis?.stop();
    closeBtnRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => {
      lenis?.start();
      window.removeEventListener("keydown", onKey);
    };
  }, [isOpen]);

  const handleUpload = (file: File) => {
    setIsOpen(false);
    onUpload(file);
  };

  return (
    <>
      {/* 浮动操作按钮：图标 + 文字标签，分析中隐藏 */}
      <AnimatePresence>
        {visible && !isOpen && (
          <motion.button
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 16 }}
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            onClick={() => setIsOpen(true)}
            aria-label="检测图片"
            className="fixed bottom-8 right-8 z-[90] flex items-center gap-2 px-5 py-3 rounded-full bg-white/5 border border-white/15 backdrop-blur-xl text-white/85 text-xs tracking-wide shadow-[0_0_30px_rgba(255,255,255,0.05)] hover:bg-white/10 hover:text-white hover:shadow-[0_0_40px_rgba(255,255,255,0.12)] transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/80"
          >
            <Upload className="w-4 h-4" />
            检测图片
          </motion.button>
        )}
      </AnimatePresence>

      {/* 上传弹窗 */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-label="上传图片检测"
            className="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 backdrop-blur-2xl"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
          >
            <button
              ref={closeBtnRef}
              onClick={() => setIsOpen(false)}
              aria-label="关闭"
              className="absolute top-8 right-8 p-3 rounded-full bg-white/5 border border-white/10 text-white/50 hover:text-white hover:bg-white/10 transition-colors z-[120] cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/80"
            >
              <X className="w-5 h-5" />
            </button>

            <motion.div
              initial={{ scale: 0.92, y: 24, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.92, y: 24, opacity: 0 }}
              transition={{ type: "spring", damping: 25, stiffness: 220 }}
              className="w-full max-w-2xl px-6 relative flex justify-center"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[110%] h-[110%] bg-white/5 blur-[120px] rounded-full pointer-events-none" />
              <UploadDevice onUpload={handleUpload} />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
