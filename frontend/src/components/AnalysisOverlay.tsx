"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle } from "lucide-react";
import Button from "./Button";
import { CancelledError, describeError } from "@/lib/api";
import type { AnalysisResult } from "@/lib/types";

interface AnalysisOverlayProps {
  file: File;
  promise: Promise<AnalysisResult>;
  onDone: (result: AnalysisResult) => void;
  onRetry: () => void;
  onExit: () => void;
}

// 用户能看懂的真实步骤（对应后端各检测模块）
const TECH_PHRASES = [
  "正在读取图片基本信息…",
  "正在检查光影是否自然…",
  "正在分析相机噪点特征…",
  "正在检测画面边缘的拼接感…",
  "正在比对主流 AI 绘图痕迹…",
  "正在检查修图痕迹…",
  "正在汇总各项证据…",
  "正在生成分析报告…",
];

const EASE_SPATIAL = [0.16, 1, 0.3, 1] as const;

export const AnalysisOverlay: React.FC<AnalysisOverlayProps> = ({
  file,
  promise,
  onDone,
  onRetry,
  onExit,
}) => {
  const [imgUrl, setImgUrl] = useState("");
  const [stage, setStage] = useState<"scanning" | "error">("scanning");
  const [error, setError] = useState<{ code: string; message: string } | null>(null);
  const [progress, setProgress] = useState(0);
  const [phraseIdx, setPhraseIdx] = useState(0);
  const [showCancel, setShowCancel] = useState(false);

  // 预览图
  useEffect(() => {
    const url = URL.createObjectURL(file);
    setImgUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  // 滚动锁：随覆盖层挂载锁定、退出释放（规格 §4 不变量）
  useEffect(() => {
    const lenis = (window as unknown as { lenis?: { stop(): void; start(): void } }).lenis;
    lenis?.stop();
    const prevent = (e: Event) => e.preventDefault();
    window.addEventListener("wheel", prevent, { passive: false });
    window.addEventListener("touchmove", prevent, { passive: false });
    return () => {
      lenis?.start();
      window.removeEventListener("wheel", prevent);
      window.removeEventListener("touchmove", prevent);
    };
  }, []);

  // 取消出口延迟浮现
  useEffect(() => {
    const t = setTimeout(() => setShowCancel(true), 3000);
    return () => clearTimeout(t);
  }, []);

  // 等待分析 Promise：模拟进度 + 文案轮换；成功/失败分流
  useEffect(() => {
    let cancelled = false;
    setStage("scanning");
    setProgress(0);

    let sim = 0;
    const progressTimer = setInterval(() => {
      sim = Math.min(95, sim + Math.random() * 7 + 3);
      setProgress(Math.floor(sim));
    }, 180);
    const phraseTimer = setInterval(() => setPhraseIdx((i) => i + 1), 1500);

    const stopTimers = () => {
      clearInterval(progressTimer);
      clearInterval(phraseTimer);
    };

    promise
      .then((result) => {
        if (cancelled) return;
        stopTimers();
        setProgress(100);
        setTimeout(() => {
          if (!cancelled) onDone(result);
        }, 350);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        stopTimers();
        if (err instanceof CancelledError) return; // 用户取消，由页面状态机处理
        setError(describeError(err));
        setStage("error"); // 失败路径：进度保持原值，绝不出现 100%/“分析完成”
      });

    return () => {
      cancelled = true;
      stopTimers();
    };
  }, [promise, onDone]);

  return (
    <motion.div
      role="dialog"
      aria-modal="true"
      aria-label={stage === "error" ? "分析失败" : "正在分析图片"}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="fixed inset-0 z-[100] flex items-center justify-center overflow-hidden bg-[#040507]/95 backdrop-blur-sm"
    >
      <AnimatePresence mode="wait">
        {stage === "scanning" ? (
          <motion.div
            key="scanning"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="flex flex-col items-center gap-10 px-6"
          >
            {/* 证据图：不裁切（object-contain + 模糊垫底） */}
            <motion.div
              initial={{ scale: 0.92, opacity: 0, y: 16, filter: "blur(6px)" }}
              animate={{ scale: 1, opacity: 1, y: 0, filter: "blur(0px)" }}
              transition={{ duration: 0.6, ease: EASE_SPATIAL }}
              className="relative w-[min(72vw,400px)] aspect-square rounded-2xl overflow-hidden shadow-2xl border border-white/10 bg-black/40"
            >
              {imgUrl && (
                <>
                  <img
                    src={imgUrl}
                    alt=""
                    aria-hidden
                    className="absolute inset-0 w-full h-full object-cover blur-2xl scale-110 opacity-50"
                  />
                  <img
                    src={imgUrl}
                    alt="待分析图片"
                    className="relative z-10 w-full h-full object-contain"
                  />
                </>
              )}
              {/* 扫描光 */}
              <div className="absolute inset-0 z-20 overflow-hidden pointer-events-none">
                <div className="scanner-line absolute inset-x-0 top-0 h-full bg-gradient-to-b from-transparent via-white/20 to-transparent mix-blend-overlay" />
              </div>
            </motion.div>

            {/* 状态与进度 */}
            <div className="flex flex-col items-center gap-3">
              <span className="text-sm text-white/80 tracking-wide">
                {progress >= 100 ? "分析完成" : "正在分析图像物理特征…"}
              </span>
              <AnimatePresence mode="wait">
                <motion.span
                  key={phraseIdx % TECH_PHRASES.length}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 0.55, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.25 }}
                  className="text-[11px] tracking-wide text-white"
                >
                  {TECH_PHRASES[phraseIdx % TECH_PHRASES.length]}
                </motion.span>
              </AnimatePresence>
              <div className="w-56 h-[2px] bg-white/10 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-sky-400 shadow-[0_0_12px_rgba(56,189,248,0.8)]"
                  animate={{ width: `${progress}%` }}
                  transition={{ ease: "easeOut", duration: 0.2 }}
                />
              </div>
              <span className="text-[10px] text-white/30 tracking-wide">通常需要 20～60 秒</span>
            </div>

            {/* 取消出口（3s 后浮现） */}
            <AnimatePresence>
              {showCancel && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute bottom-8 right-8"
                >
                  <Button variant="tertiary" onClick={onExit} withArrow={false}>
                    取消分析
                  </Button>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ) : (
          <motion.div
            key="error"
            initial={{ opacity: 0, scale: 0.96, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35, ease: EASE_SPATIAL }}
            className="w-full max-w-md mx-6 spatial-glass rounded-3xl p-8 border border-red-500/30 shadow-[0_0_30px_rgba(248,113,113,0.08)] flex flex-col gap-4"
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400">
                <AlertTriangle size={18} strokeWidth={1.5} />
              </div>
              <span className="text-sm font-semibold text-white/90 tracking-wide">分析失败</span>
            </div>
            <span className="font-mono text-[10px] tracking-widest uppercase text-red-300/70">
              {error?.code}
            </span>
            <p className="text-sm text-white/70 leading-relaxed">{error?.message}</p>
            <div className="flex items-center gap-4 mt-2">
              <Button variant="secondary" onClick={onRetry}>
                重新分析
              </Button>
              <Button variant="tertiary" onClick={onExit} withArrow={false}>
                返回
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
