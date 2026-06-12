"use client";

import React from "react";
import { AlertTriangle, Info, ShieldAlert } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface AlertBannerProps {
  triggers?: string[];
  systemDegraded?: boolean;
}

// 后端报警串 → 用户能看懂的人话（前端映射，不动后端逻辑）。
// 命中规则按顺序匹配，未命中的原样展示。
const HUMAN_RULES: { test: (t: string) => boolean; text: string; warn: boolean }[] = [
  {
    test: (t) => t.includes("被系统自动跳过") || t.includes("熔断"),
    text: "部分检测项这次没能完成（网络原因），结果由其余检测项得出，参考价值略有下降。",
    warn: true,
  },
  {
    test: (t) => t.includes("所有探测器"),
    text: "本次所有检测项都未能完成，当前结果仅供参考，建议稍后重试。",
    warn: true,
  },
  {
    test: (t) => t.includes("修图警报") || t.includes("ELA"),
    text: "发现局部修图或拼接的痕迹，这一点已计入最终判断。",
    warn: true,
  },
  {
    test: (t) => t.includes("AI模型特征指纹"),
    text: "发现明显的 AI 绘图特征。",
    warn: false,
  },
  {
    test: (t) => t.includes("结构崩塌"),
    text: "画面局部边缘存在不自然的拼接感。",
    warn: false,
  },
  {
    test: (t) => t.includes("CMOS") || t.includes("底噪"),
    text: "没有找到真实相机应有的噪点特征。",
    warn: false,
  },
];

function humanize(trigger: string): { text: string; warn: boolean } {
  for (const rule of HUMAN_RULES) {
    if (rule.test(trigger)) return { text: rule.text, warn: rule.warn };
  }
  return {
    text: trigger,
    warn: trigger.includes("警告") || trigger.includes("故障"),
  };
}

export const AlertBanner: React.FC<AlertBannerProps> = ({ triggers = [], systemDegraded = false }) => {
  // 翻译 + 去重（多个模块跳过会产生多条相同人话，只留一条）
  const items: { text: string; warn: boolean }[] = [];
  const seen = new Set<string>();
  for (const t of triggers) {
    const h = humanize(t);
    if (!seen.has(h.text)) {
      seen.add(h.text);
      items.push(h);
    }
  }

  if (items.length === 0 && !systemDegraded) return null;

  return (
    <div className="w-full flex flex-col gap-2 z-50">
      <AnimatePresence>
        {systemDegraded && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-3 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400"
          >
            <ShieldAlert size={16} className="shrink-0 mt-0.5" />
            <span className="text-xs leading-relaxed opacity-90">
              本次所有检测项都未能完成，当前结果仅供参考，建议稍后重试。
            </span>
          </motion.div>
        )}

        {items.map((item, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.1 }}
            className={`flex items-start gap-3 p-3 rounded-lg border ${
              item.warn
                ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                : "bg-blue-500/10 border-blue-500/30 text-blue-300"
            }`}
          >
            {item.warn ? (
              <AlertTriangle size={14} className="shrink-0 mt-0.5" />
            ) : (
              <Info size={14} className="shrink-0 mt-0.5" />
            )}
            <span className="text-xs leading-relaxed opacity-90">{item.text}</span>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};
