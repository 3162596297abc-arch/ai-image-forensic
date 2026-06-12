"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Cpu, Menu, Shield, X } from "lucide-react";

import { TerminatorBackground } from "@/components/TerminatorBackground";
import { UploadDevice } from "@/components/UploadDevice";
import { AnalysisOverlay } from "@/components/AnalysisOverlay";
import { AuthenticityHUD } from "@/components/AuthenticityHUD";
import { GlobalFloatingUpload } from "@/components/GlobalFloatingUpload";
import ProjectCard from "@/components/ProjectCard";
import RevealText from "@/components/RevealText";
import ParticleTitle from "@/components/ParticleTitle";
import Magnetic from "@/components/Magnetic";
import ScrollDepthIndicator from "@/components/ScrollDepthIndicator";
import Button from "@/components/Button";
import { analyzeImage, checkHealth, validateFile } from "@/lib/api";
import type { AnalysisResult } from "@/lib/types";

// 页面状态机：分析失败的呈现由 AnalysisOverlay 内部处理（页面保持 analyzing）
type Phase =
  | { status: "idle" }
  | { status: "analyzing"; file: File; promise: Promise<AnalysisResult> }
  | { status: "success"; file: File; result: AnalysisResult };

const NAV_LINKS = [
  { id: "#home", label: "首页" },
  { id: "#exhibitions", label: "工作原理" },
  { id: "#laboratory", label: "开始检测" },
];

const scrollToSection = (id: string) => {
  const lenis = (window as unknown as { lenis?: { scrollTo: (t: string, o: object) => void } })
    .lenis;
  if (lenis) {
    lenis.scrollTo(id, { offset: -90, duration: 1.4 });
  } else {
    document.querySelector(id)?.scrollIntoView({ behavior: "smooth" });
  }
};

export default function Home() {
  const [phase, setPhase] = useState<Phase>({ status: "idle" });
  const [engineOnline, setEngineOnline] = useState<boolean | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [heroError, setHeroError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 引擎状态探活：真实有用的信息，取代原"在线时长"伪信息
  useEffect(() => {
    let mounted = true;
    checkHealth().then((ok) => {
      if (mounted) setEngineOnline(ok);
    });
    return () => {
      mounted = false;
    };
  }, []);

  // 上传即发请求（请求与滚动并行，无人为延迟）
  const startAnalysis = useCallback((file: File) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    const promise = analyzeImage(file, controller.signal);
    promise.catch(() => {}); // 防 unhandled rejection；真正的处理在 AnalysisOverlay
    setPhase({ status: "analyzing", file, promise });
    requestAnimationFrame(() => scrollToSection("#laboratory"));
  }, []);

  const handleDone = useCallback((result: AnalysisResult) => {
    setPhase((prev) =>
      prev.status === "analyzing" ? { status: "success", file: prev.file, result } : prev
    );
  }, []);

  const handleExit = useCallback(() => {
    abortRef.current?.abort();
    setPhase({ status: "idle" });
  }, []);

  const handleRetry = useCallback(() => {
    setPhase((prev) => {
      if (prev.status !== "analyzing") return prev;
      const controller = new AbortController();
      abortRef.current = controller;
      const promise = analyzeImage(prev.file, controller.signal);
      promise.catch(() => {});
      return { status: "analyzing", file: prev.file, promise };
    });
  }, []);

  const handleHeroFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const problem = validateFile(file);
      if (problem) {
        setHeroError(problem);
      } else {
        setHeroError(null);
        startAnalysis(file);
      }
    }
    e.target.value = "";
  };

  const navigate = (id: string) => {
    setMenuOpen(false);
    scrollToSection(id);
  };

  return (
    <main className="relative min-h-screen w-full flex flex-col items-center overflow-x-hidden bg-black text-white">
      {/* 晨昏线流体背景（全站唯一 Canvas） */}
      <TerminatorBackground />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_45%,rgba(10,10,10,0.9)_100%)] pointer-events-none z-[1]" />

      <ScrollDepthIndicator />

      {/* 隐藏文件选择器：Hero 主按钮直接触发 */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleHeroFile}
      />

      {/* 顶部胶囊导航 */}
      <header className="fixed top-6 left-1/2 -translate-x-1/2 w-[calc(100%-2rem)] max-w-5xl spatial-glass rounded-2xl px-5 md:px-6 py-3.5 flex items-center justify-between z-50 animate-[fadeIn_1.2s_ease-out]">
        <button
          className="flex items-center gap-3 cursor-pointer text-left"
          onClick={() => navigate("#home")}
          aria-label="回到首页"
        >
          <div className="p-1.5 bg-white/5 border border-white/10 rounded-lg">
            <Shield size={14} className="text-white/80" />
          </div>
          <div className="flex flex-col">
            <span className="text-[11px] font-bold tracking-widest text-white/90">阿尔法No1</span>
            <span className="hidden sm:block font-mono text-[7px] text-white/40 uppercase tracking-widest leading-none">
              AI era, seeing is no longer believing
            </span>
          </div>
        </button>

        <nav className="hidden md:flex items-center gap-7 text-xs text-white/55">
          {NAV_LINKS.map((link, i) => (
            <Magnetic key={link.id} range={26} strength={0.3}>
              <button
                onClick={() => navigate(link.id)}
                className="hover:text-white transition-colors duration-300 cursor-pointer tracking-wide"
              >
                <span className="font-mono text-[9px] text-white/30 mr-1.5">
                  0{i + 1}
                </span>
                {link.label}
              </button>
            </Magnetic>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <div className="hidden lg:flex items-center gap-2 text-[10px] text-white/45 border-r border-white/10 pr-4">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                engineOnline === null
                  ? "bg-white/40"
                  : engineOnline
                    ? "bg-emerald-400 animate-pulse"
                    : "bg-zinc-500"
              }`}
            />
            <span>{engineOnline === null ? "连接引擎中" : engineOnline ? "检测引擎在线" : "引擎离线"}</span>
          </div>
          <Button
            variant="primary"
            className="hidden md:inline-flex px-5 py-2 text-xs"
            onClick={() => navigate("#laboratory")}
          >
            开始检测
          </Button>
          <button
            className="md:hidden p-2 rounded-lg border border-white/10 bg-white/5 text-white/70 cursor-pointer"
            onClick={() => setMenuOpen(true)}
            aria-label="打开菜单"
          >
            <Menu size={16} />
          </button>
        </div>
      </header>

      {/* 移动端全屏菜单 */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[120] bg-[#040507]/90 backdrop-blur-2xl flex flex-col items-center justify-center gap-8 md:hidden"
            role="dialog"
            aria-modal="true"
            aria-label="导航菜单"
          >
            <button
              onClick={() => setMenuOpen(false)}
              aria-label="关闭菜单"
              className="absolute top-8 right-8 p-3 rounded-full bg-white/5 border border-white/10 text-white/60 cursor-pointer"
            >
              <X size={18} />
            </button>
            {NAV_LINKS.map((link, i) => (
              <button
                key={link.id}
                onClick={() => navigate(link.id)}
                className="text-2xl font-light text-white/85 tracking-wide cursor-pointer"
              >
                <span className="font-mono text-xs text-white/30 mr-3">0{i + 1}</span>
                {link.label}
              </button>
            ))}
            <Button
              variant="primary"
              className="mt-4"
              onClick={() => navigate("#laboratory")}
            >
              开始检测
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* SECTION 1: Hero —— 5 秒内说清“这是什么、我该干嘛” */}
      <section
        id="home"
        className="relative w-full min-h-screen flex flex-col justify-center items-center overflow-hidden z-10"
      >
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none select-none">
          <span
            className="text-[12vw] md:text-[8vw] font-thin tracking-[0.4em] leading-none ml-[0.4em] -mt-10"
            style={{ color: "#D8E3F0", opacity: 0.03 }}
          >
            REAL
          </span>
        </div>

        <div className="relative z-10 flex flex-col items-center justify-center gap-8 mt-24 px-6 animate-[fadeIn_1.2s_ease-out]">
          <h1 className="leading-none select-none text-center">
            <ParticleTitle text="辨伪求真" />
          </h1>

          <h2 className="text-base md:text-xl font-light text-white/70 tracking-wide text-center max-w-xl">
            上传一张图片，看它是相机拍的，还是 AI 生成的。
          </h2>

          <div className="flex flex-col sm:flex-row items-center gap-4 mt-4">
            <Button variant="primary" onClick={() => fileInputRef.current?.click()}>
              上传图片检测
            </Button>
            <Button variant="secondary" onClick={() => scrollToSection("#exhibitions")}>
              它是怎么判断的？
            </Button>
          </div>

          <div aria-live="polite">
            {heroError && <p className="text-xs text-red-300">{heroError}</p>}
          </div>

          <p className="text-[11px] text-white/35 tracking-widest">
            免费 · 无需注册 · 不保存你的图片
          </p>
        </div>

        <div className="absolute bottom-10 flex flex-col items-center pointer-events-none select-none">
          <span className="font-mono text-[9px] tracking-widest uppercase text-white/20">
            Powered by Alpha No.1
          </span>
        </div>
      </section>

      {/* SECTION 2: 我们在做什么 */}
      <section
        id="manifesto"
        className="relative w-full max-w-5xl mx-auto py-36 px-6 flex flex-col gap-8 z-10 border-t border-white/5"
      >
        <span className="font-mono text-[9px] text-zinc-400 tracking-widest uppercase">
          // 我们在做什么
        </span>

        <p className="text-2xl md:text-4xl font-light text-white/80 leading-relaxed max-w-4xl tracking-wide">
          <RevealText
            text="AI 生成的图片越来越逼真。我们不猜测它像不像 AI，而是用物理规律来验证它是否真实。"
            by="words"
            delay={0.15}
          />
        </p>

        <div className="flex flex-col gap-5 mt-10 max-w-3xl">
          <p className="text-sm font-light text-white/55 leading-relaxed">
            系统先像鉴定师一样检查这张图的“物理常识”——光影自不自然、有没有真实相机留下的噪点、边缘有没有拼接的痕迹——再把这些证据连同图片一起交给
            AI 视觉模型，给出有依据的判断。
          </p>
          <details className="group select-none">
            <summary className="cursor-pointer list-none text-xs text-white/40 hover:text-white/70 transition-colors inline-flex items-center gap-1.5">
              查看全部检测维度
              <span aria-hidden className="inline-block transition-transform duration-300 group-open:rotate-45">
                ＋
              </span>
            </summary>
            <p className="mt-3 text-xs text-white/40 font-light leading-relaxed">
              光影方向 · 阴影逻辑 · 噪声结构 · 材质纹理 · 景深一致性 · 色彩分布 · 空间透视 ·
              边缘融合 · 频域纹理 · 修图痕迹——共十余个维度。这些是相机照片天然具备、而 AI
              很难完美模拟的物理特征。
            </p>
          </details>
        </div>
      </section>

      {/* SECTION 3: 三步流程 */}
      <section
        id="exhibitions"
        className="relative w-full max-w-5xl mx-auto py-24 px-6 flex flex-col gap-16 z-10 border-t border-white/5"
      >
        <div className="flex justify-between items-end w-full">
          <div className="flex flex-col gap-2">
            <span className="font-mono text-[9px] text-zinc-400 tracking-widest uppercase">
              // 工作原理
            </span>
            <h2 className="text-2xl font-normal tracking-wide text-white/90">
              三步完成真实性验证
            </h2>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-24 items-start w-full">
          <div className="w-full">
            <ProjectCard
              index="Step.01"
              category="物理特征提取"
              title="上传图片"
              description="拖入图片，系统立刻读取它的光影、噪点等物理特征。"
              imageSrc="/organic_trust.png"
              link="#laboratory"
            />
          </div>

          <div className="w-full md:mt-24">
            <ProjectCard
              index="Step.02"
              category="AI 视觉理解"
              title="AI 多维分析"
              description="物理证据连同图片一起，交给 AI 视觉模型综合研判。"
              imageSrc="/volumetric_shell.png"
              link="#laboratory"
            />
          </div>

          <div className="w-full md:-mt-12">
            <ProjectCard
              index="Step.03"
              category="多维报告输出"
              title="拿到判定报告"
              description="结论、依据、可疑点——一份看得懂的报告说清楚。"
              imageSrc="/spatial_interfaces.png"
              link="#laboratory"
            />
          </div>

          <div className="w-full h-full flex flex-col justify-center gap-6 p-8 border border-white/5 rounded-2xl bg-white/[0.01] spatial-glass text-left select-none md:mt-12">
            <div className="flex items-center gap-2">
              <Cpu size={14} className="text-zinc-400" />
              <span className="font-mono text-[10px] uppercase tracking-widest text-white/70">
                为什么不直接让 AI 看图判断？
              </span>
            </div>
            <p className="text-xs text-white/50 leading-relaxed font-light">
              AI 生成的图越来越逼真，光“看”不够。先提取物理证据，再让 AI
              据证判断——有依据的结论，比直觉可靠。
            </p>
            <div className="h-px bg-white/5 w-full my-1" />
            <Button variant="tertiary" onClick={() => scrollToSection("#laboratory")}>
              立即体验
            </Button>
          </div>
        </div>
      </section>

      {/* SECTION 4: 检测区 */}
      <section
        id="laboratory"
        className="relative w-full max-w-5xl mx-auto py-32 px-6 flex flex-col items-center gap-16 z-10 border-t border-white/5"
      >
        <div className="flex flex-col items-center text-center gap-3">
          <span className="font-mono text-[9px] text-zinc-400 tracking-widest uppercase">
            // 开始检测
          </span>
          <h2 className="text-2xl md:text-3xl font-normal tracking-wide text-white/90">
            上传图片，查看真相
          </h2>
          <p className="text-sm text-white/45 max-w-md font-light leading-relaxed">
            拖入或点击上传一张图片，系统将自动提取物理特征并交由 AI 进行多维度真实性分析。
          </p>
        </div>

        <div className="w-full flex justify-center items-center py-6 min-h-[400px]">
          <AnimatePresence mode="wait">
            {phase.status === "success" ? (
              <AuthenticityHUD
                key="hud"
                file={phase.file}
                result={phase.result}
                onReset={handleExit}
              />
            ) : (
              <motion.div
                key="upload"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, scale: 0.96 }}
                transition={{ duration: 0.3 }}
                className="w-full max-w-lg flex justify-center"
              >
                <UploadDevice onUpload={startAnalysis} disabled={phase.status === "analyzing"} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>

      {/* 分析中覆盖层 */}
      <AnimatePresence>
        {phase.status === "analyzing" && (
          <AnalysisOverlay
            key="overlay"
            file={phase.file}
            promise={phase.promise}
            onDone={handleDone}
            onRetry={handleRetry}
            onExit={handleExit}
          />
        )}
      </AnimatePresence>

      {/* SECTION 5: 页脚 */}
      <footer className="relative w-full max-w-5xl mx-auto flex flex-col gap-12 z-10 border-t border-white/5 py-16 px-6 font-mono text-[10px] text-white/30">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
          <div className="flex flex-col gap-3">
            <span className="text-white/60 tracking-wider font-bold">阿尔法No1</span>
            <p className="text-[10px] leading-relaxed text-white/35 max-w-xs font-light font-sans">
              AI 时代的图片真实性验证引擎。用现实世界的物理规律，帮你判断每一张图片能不能信。
            </p>
          </div>

          <div className="flex flex-col gap-2">
            <span className="text-white/60 tracking-wider">导航</span>
            <ul className="flex flex-col gap-1">
              {[
                { id: "#home", label: "首页" },
                { id: "#manifesto", label: "我们在做什么" },
                { id: "#exhibitions", label: "工作原理" },
                { id: "#laboratory", label: "开始检测" },
              ].map((link) => (
                <li key={link.id}>
                  <button
                    onClick={() => scrollToSection(link.id)}
                    className="hover:text-white transition-colors duration-300 cursor-pointer"
                  >
                    {link.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex flex-col gap-2 sm:text-right sm:items-end">
            <span className="text-white/60 tracking-wider">系统</span>
            <div className="flex flex-col gap-1 sm:items-end">
              <span>POWERED BY OPENCV + AI VISION</span>
              <div className="flex items-center gap-1.5 text-[9px] mt-1">
                <div
                  className={`w-1.5 h-1.5 rounded-full ${
                    engineOnline ? "bg-emerald-400 animate-pulse" : "bg-zinc-500"
                  }`}
                />
                <span>{engineOnline ? "检测引擎在线" : engineOnline === null ? "连接引擎中" : "引擎离线"}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="h-px bg-white/5 w-full" />

        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 text-[9px]">
          <span>用物理规律验证每一个像素的真实性</span>
          <span>© 2026 阿尔法No1</span>
        </div>
      </footer>

      <GlobalFloatingUpload visible={phase.status === "idle"} onUpload={startAnalysis} />
    </main>
  );
}
