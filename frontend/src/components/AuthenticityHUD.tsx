"use client";

import React, { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, ScanEye, Search } from "lucide-react";
import { motion, AnimatePresence, animate } from "framer-motion";
import { AlertBanner } from "./AlertBanner";
import Button from "./Button";
import { TIER_LABEL, tierOf } from "@/lib/types";
import type { AnalysisResult, Dimension, DimensionKey, Tone } from "@/lib/types";

interface AuthenticityHUDProps {
  file: File;
  result: AnalysisResult;
  onReset: () => void;
}

const EASE_SPATIAL = [0.16, 1, 0.3, 1] as const;

const TONE_TEXT: Record<Tone, string> = {
  ok: "text-emerald-400",
  warn: "text-amber-400",
  bad: "text-red-400",
};
const TONE_GLOW: Record<Tone, string> = {
  ok: "drop-shadow-[0_0_12px_rgba(52,211,153,0.3)]",
  warn: "drop-shadow-[0_0_12px_rgba(251,191,36,0.3)]",
  bad: "drop-shadow-[0_0_12px_rgba(248,113,113,0.3)]",
};
const TONE_CHIP: Record<Tone, string> = {
  ok: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
  warn: "bg-amber-500/10 border-amber-500/30 text-amber-400",
  bad: "bg-red-500/10 border-red-500/30 text-red-400",
};

// 维度状态（后端英文枚举 → 人话）
const STATUS_LABEL: Record<string, string> = {
  ANOMALOUS: "异常",
  SUSPICIOUS: "可疑",
  STABLE: "正常",
};

// 检测项术语 → 人话（覆盖后端两套命名；原术语保留在科普折叠区）
const METRIC_LABEL: Record<string, string> = {
  CMOS物理底噪缺失特征: "相机噪点检查",
  相机真实光感与噪点分析: "相机噪点检查",
  局部边缘强制融合: "画面边缘自然度",
  边缘不自然拼接痕迹: "画面边缘自然度",
  "2D-FFT高频人造尖峰": "隐藏纹理检查",
  AI算法处理残留物: "AI 处理残留",
  全局生成器特定伪影分布: "AI 绘图痕迹",
  主流AI软件画风特征: "AI 绘图痕迹",
  "ELA 像素离散异常": "修图/拼接痕迹",
  后期人为P图篡改痕迹: "修图/拼接痕迹",
};

const TABS: { id: DimensionKey; label: string; title: string }[] = [
  { id: "sensor", label: "光影与噪点", title: "光影与噪点真实度" },
  { id: "structural", label: "画面结构", title: "画面结构合理性" },
  { id: "spatial", label: "AI 绘图痕迹", title: "AI 绘图痕迹检验" },
  { id: "editing", label: "修图痕迹", title: "修图痕迹检测" },
];

const EMPTY_DIMENSION: Dimension = {
  status: "UNKNOWN",
  score: 0,
  description: "暂无数据",
  suggestion: "",
  sub_metrics: [],
};

const scoreTone = (s: number): Tone => (s >= 0.7 ? "bad" : s >= 0.4 ? "warn" : "ok");

// fallback 文案与实际状态可能矛盾（LLM 不可用时统一兜底为"未发现问题"）。
// 根据 status 字段生成符合真实状态的描述文案。
function resolveDescription(dim: Dimension): string {
  const isFallback =
    !dim.description ||
    dim.description === "该项检查未发现明显问题。" ||
    dim.description === "暂无数据";
  if (!isFallback) return dim.description;
  if (dim.status === "ANOMALOUS") return "检测到明显异常特征，已计入最终判断。";
  if (dim.status === "SUSPICIOUS") return "检测到可疑特征，已计入最终判断。";
  return "该项检查未发现明显问题。";
}

// 各检测维度的科普解释（折叠区内容，术语在这里保留给好奇的人）
const getGlossaryForTab = (tab: DimensionKey) => {
  switch (tab) {
    case "sensor":
      return (
        <ul className="flex flex-col gap-1.5 ml-3 list-disc marker:text-white/20">
          <li><strong className="text-white/80">CMOS噪声探测</strong>：分析图片是否存在真实物理相机传感器的固有底噪。AI 生成往往因为缺乏物理实体而缺失这种极微弱的随机电平噪声。</li>
          <li><strong className="text-white/80">光学透镜反演</strong>：画面中的模糊（焦外散景）是否符合真实光学镜头的物理折射规律？</li>
        </ul>
      );
    case "structural":
      return (
        <ul className="flex flex-col gap-1.5 ml-3 list-disc marker:text-white/20">
          <li><strong className="text-white/80">边缘强制融合</strong>：利用 Harris 角点检测，寻找物体边缘是否存在 AI 模型由于理解力不足而强行把两块毫不相干的区域“糊”在一起的崩塌点。</li>
          <li><strong className="text-white/80">高频频域尖峰</strong>：使用 2D-FFT 快速傅里叶变换，检测肉眼看不见的高频频域中，是否有生成算法（如 GAN 或 Diffusion Upscaler）留下的周期性人造纹波。</li>
        </ul>
      );
    case "spatial":
      return (
        <ul className="flex flex-col gap-1.5 ml-3 list-disc marker:text-white/20">
          <li><strong className="text-white/80">生成器特定伪影分布</strong>：通过视觉大模型探针（Qwen-VL-Max），在微观层面识别特定扩散模型（如 Midjourney、Flux、Stable Diffusion）所特有的生成特征。</li>
          <li><strong className="text-white/80">塑料光感/人工放大</strong>：识别模型过度平滑的塑料感，以及常见的重绘放大（Enhancement）痕迹。</li>
        </ul>
      );
    case "editing":
      return (
        <ul className="flex flex-col gap-1.5 ml-3 list-disc marker:text-white/20">
          <li><strong className="text-white/80">误差级别分析 (ELA)</strong>：经典数字法医技术。如果一张图是拼接的，由于不同部分的 JPEG 压缩历史不同，在特定的错误率重算下，拼接区域会突兀地爆出异常亮度。</li>
          <li><strong className="text-white/80">过度锐化探测</strong>：检测后期的强行拉升处理。</li>
        </ul>
      );
  }
};

export const AuthenticityHUD: React.FC<AuthenticityHUDProps> = ({ file, result, onReset }) => {
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<DimensionKey>("sensor");
  const [showGlossary, setShowGlossary] = useState(false);
  const [showDetail, setShowDetail] = useState(false);
  const [display, setDisplay] = useState(0);
  const [resolved, setResolved] = useState(false);

  const tier = tierOf(result);
  const verdict = TIER_LABEL[tier];
  const tone = verdict.tone;
  const probability = result.scores?.ai_participation ?? 0;
  const timestamp = useMemo(() => new Date().toLocaleTimeString(), []);

  // 关键发现：可疑程度最高的三个维度（两层结构的第一层）
  const findings = useMemo(() => {
    const dims = result.report?.dimensions;
    if (!dims) return [];
    return TABS.map((t) => ({ ...t, dim: dims[t.id] ?? EMPTY_DIMENSION }))
      .sort((a, b) => b.dim.score - a.dim.score)
      .slice(0, 3);
  }, [result]);

  useEffect(() => {
    const url = URL.createObjectURL(file);
    setImageSrc(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  // 判决时刻：概率 count-up，行至 60% 时颜色由白解析为判定色
  useEffect(() => {
    const target = probability * 100;
    const controls = animate(0, target, {
      duration: 1.2,
      ease: EASE_SPATIAL,
      onUpdate: (v) => {
        setDisplay(v);
        if (v >= target * 0.6) setResolved(true);
      },
    });
    return () => controls.stop();
  }, [probability]);

  const dimData: Dimension = result.report?.dimensions?.[activeTab] ?? EMPTY_DIMENSION;
  const activeTitle = TABS.find((t) => t.id === activeTab)?.title ?? "";

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 24, scale: 0.98 }}
      transition={{ duration: 0.45, ease: EASE_SPATIAL }}
      className="relative w-full max-w-5xl rounded-3xl spatial-glass p-8 flex flex-col gap-6 border border-white/5 shadow-2xl pointer-events-auto z-10 overflow-hidden"
    >
      {/* 判定水印：与首页 REAL 巨字呼应 */}
      <div
        aria-hidden
        className="absolute inset-0 flex items-center justify-center pointer-events-none select-none z-0"
      >
        <span className="text-[10vw] font-thin uppercase tracking-[0.3em] text-[#D8E3F0] opacity-[0.03] whitespace-nowrap">
          {tone === "ok" ? "REAL" : "SYNTHETIC"}
        </span>
      </div>

      {/* ===== 第一层：结论 ===== */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-start gap-6 border-b border-white/5 pb-6 z-10">
        <div className="flex items-start gap-4 min-w-0">
          <div className={`p-2 mt-1 rounded-xl border shrink-0 ${TONE_CHIP[tone]}`}>
            {tone === "ok" ? (
              <ScanEye size={20} strokeWidth={1.5} />
            ) : (
              <AlertTriangle size={20} strokeWidth={1.5} />
            )}
          </div>
          <div className="flex flex-col gap-2 min-w-0">
            <span className="font-mono text-[9px] uppercase tracking-widest text-white/40">
              鉴定结论 · {timestamp}
            </span>
            <motion.h2
              initial={{ scale: 1.5, opacity: 0, rotate: -6 }}
              animate={{ scale: 1, opacity: 1, rotate: 0 }}
              transition={{ delay: 0.85, duration: 0.4, ease: EASE_SPATIAL }}
              className={`text-2xl md:text-3xl font-bold tracking-wide origin-left ${TONE_TEXT[tone]} ${TONE_GLOW[tone]}`}
            >
              {verdict.text}
            </motion.h2>
            {result.report?.ai_probability_summary && (
              <p className="text-sm text-white/75 leading-relaxed max-w-xl">
                {result.report.ai_probability_summary}
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-col items-end gap-3 shrink-0">
          <div className="flex flex-col items-end">
            <span className="font-mono text-[9px] uppercase tracking-widest text-white/40">
              AI 参与概率
            </span>
            <span
              className={`font-black tracking-tighter text-5xl tabular-nums transition-colors duration-300 ${
                resolved ? `${TONE_TEXT[tone]} ${TONE_GLOW[tone]}` : "text-white"
              }`}
            >
              {display.toFixed(1)}%
            </span>
          </div>
          <Button variant="secondary" onClick={onReset} className="px-4 py-1.5 text-xs">
            重新检测
          </Button>
        </div>
      </div>

      <AlertBanner
        triggers={result.system_data?.relation_triggers ?? []}
        systemDegraded={result.system_data?.system_degraded ?? false}
      />

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 z-10">
        {/* 左：证据图（不裁切） */}
        <div className="md:col-span-5 flex flex-col gap-3">
          <div className="relative aspect-square w-full rounded-2xl overflow-hidden shadow-2xl border border-white/5 bg-black/40">
            {imageSrc && (
              <>
                <img
                  src={imageSrc}
                  alt=""
                  aria-hidden
                  className="absolute inset-0 w-full h-full object-cover blur-2xl scale-110 opacity-40"
                />
                <img
                  src={imageSrc}
                  alt="待鉴定图片"
                  className="relative z-10 w-full h-full object-contain"
                />
              </>
            )}
          </div>
          <span className="text-[9px] font-mono text-white/15 truncate px-1">
            ID {result.analysis_id}
          </span>
        </div>

        {/* 右：关键发现（人话，最多三条） */}
        <div className="md:col-span-7 flex flex-col gap-3">
          <span className="font-mono text-[9px] uppercase tracking-widest text-white/40">
            关键发现
          </span>
          <div className="flex flex-col gap-2.5">
            {findings.map(({ id, label, dim }) => {
              const t = scoreTone(dim.score);
              return (
                <div
                  key={id}
                  className="flex flex-col gap-1.5 p-4 rounded-xl border border-white/5 bg-white/[0.02]"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <span
                        className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                          t === "bad" ? "bg-red-400" : t === "warn" ? "bg-amber-400" : "bg-emerald-400"
                        }`}
                      />
                      <span className="text-sm text-white/85 tracking-wide">{label}</span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded border shrink-0 ${TONE_CHIP[t]}`}
                      >
                        {STATUS_LABEL[dim.status] ?? "未知"}
                      </span>
                    </div>
                    <span className={`text-sm font-mono font-bold shrink-0 ${TONE_TEXT[t]}`}>
                      {(dim.score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-xs text-white/55 leading-relaxed line-clamp-2 pl-4">
                    {resolveDescription(dim)}
                  </p>
                </div>
              );
            })}
          </div>

          <div className="mt-auto pt-2">
            <Button
              variant="tertiary"
              withArrow={false}
              onClick={() => setShowDetail((s) => !s)}
              aria-expanded={showDetail}
            >
              {showDetail ? "收起详细数据 −" : "查看详细数据 +"}
            </Button>
          </div>
        </div>
      </div>

      {/* ===== 第二层：详细数据（默认折叠） ===== */}
      <AnimatePresence initial={false}>
        {showDetail && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.4, ease: EASE_SPATIAL }}
            className="overflow-hidden z-10"
          >
            <div className="flex flex-col gap-4 pt-2 border-t border-white/5">
              <div className="flex gap-1.5 p-1.5 bg-white/[0.02] rounded-xl border border-white/5 mt-4">
                {TABS.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex-1 py-2 px-2 rounded-lg text-xs tracking-wide transition-all cursor-pointer
                      focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60
                      ${
                        activeTab === tab.id
                          ? "bg-white/10 text-white font-semibold border border-white/10"
                          : "text-white/40 hover:text-white/70 hover:bg-white/[0.03]"
                      }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              <div className="rounded-2xl border border-white/5 bg-gradient-to-b from-white/[0.03] to-transparent p-6 flex flex-col gap-4 shadow-inner">
                <div className="flex justify-between items-start gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <Activity className="w-5 h-5 text-white/40 shrink-0" strokeWidth={1.5} />
                    <div className="flex flex-col min-w-0">
                      <span className="text-base tracking-wide text-white/90">{activeTitle}</span>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] text-white/40 tracking-wider">可疑程度</span>
                        <span
                          className={`text-2xl font-black font-mono tracking-tight ${TONE_TEXT[scoreTone(dimData.score)]}`}
                        >
                          {(dimData.score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                  <span
                    className={`text-[10px] tracking-wide px-3 py-1.5 rounded-md border font-semibold shrink-0 ${
                      STATUS_LABEL[dimData.status]
                        ? TONE_CHIP[scoreTone(dimData.score)]
                        : "bg-white/5 border-white/10 text-white/50"
                    }`}
                  >
                    {STATUS_LABEL[dimData.status] ?? "未知"}
                  </span>
                </div>

                <p className="text-xs text-white/70 leading-relaxed">{resolveDescription(dimData)}</p>

                {dimData.suggestion && (
                  <div className="p-3 rounded-xl border border-white/5 bg-white/[0.02]">
                    <div className="flex gap-2">
                      <Search size={12} className="text-white/40 shrink-0 mt-0.5" />
                      <span className="text-xs text-white/70 leading-5">{dimData.suggestion}</span>
                    </div>
                  </div>
                )}

                <div className="flex flex-col gap-3">
                  {dimData.sub_metrics?.map((metric, idx) => {
                    const t = scoreTone(metric.value);
                    return (
                      <div
                        key={idx}
                        className="flex flex-col gap-2 w-full p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.02]"
                      >
                        <div className="flex justify-between items-center w-full">
                          <span className="text-xs text-white/60 tracking-wide">
                            {METRIC_LABEL[metric.name] ?? metric.name}
                          </span>
                          <span className={`text-xs font-mono font-bold ${TONE_TEXT[t]}`}>
                            {(metric.value * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="w-full h-1 bg-white/5 relative rounded-full overflow-hidden">
                          <div
                            className={`absolute left-0 top-0 bottom-0 transition-all duration-1000 ease-out ${
                              t === "bad" ? "bg-red-400" : t === "warn" ? "bg-amber-400" : "bg-emerald-400"
                            }`}
                            style={{ width: `${Math.min(Math.max(metric.value * 100, 2), 100)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* 科普入口：可见文字链替代隐蔽小图标 */}
                <div className="border-t border-white/5 pt-3">
                  <button
                    onClick={() => setShowGlossary((s) => !s)}
                    aria-expanded={showGlossary}
                    className="text-xs text-white/45 hover:text-white/80 transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60 rounded"
                  >
                    这是怎么检测的？{showGlossary ? "−" : "+"}
                  </button>
                  <AnimatePresence initial={false}>
                    {showGlossary && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: EASE_SPATIAL }}
                        className="overflow-hidden"
                      >
                        <div className="mt-3 text-xs text-white/60 leading-relaxed">
                          {getGlossaryForTab(activeTab)}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
