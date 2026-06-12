// 与 backend/routers/analyze.py 的响应逐字段对齐的类型定义。

export type DimensionKey = "sensor" | "structural" | "spatial" | "editing";
export type DimensionStatus = "STABLE" | "SUSPICIOUS" | "ANOMALOUS" | string;
export type Tier = "Low" | "Moderate" | "High" | "Critical";

export interface SubMetric {
  name: string;
  value: number; // 0–1
}

export interface Dimension {
  status: DimensionStatus;
  score: number; // 0–1
  description: string;
  suggestion: string;
  sub_metrics: SubMetric[];
}

export interface AnalysisResult {
  analysis_id: string;
  scores: {
    ai_probability: number;
    human_probability: number;
    ai_participation: number;
  };
  report: {
    ai_probability_summary: string;
    dimensions: Record<DimensionKey, Dimension>;
    jury: { ai_participation: number; tier: Tier };
  };
  jury: { ai_participation: number; tier: Tier; jury_phases: unknown };
  system_data: {
    relation_triggers?: string[];
    system_degraded?: boolean;
  };
}

export type Tone = "ok" | "warn" | "bad";

// 判定等级 → 用户可读结论。tier 是主结论，概率数字只是辅助。
export const TIER_LABEL: Record<Tier, { text: string; tone: Tone }> = {
  Low: { text: "未见明显AI痕迹", tone: "ok" },
  Moderate: { text: "存在可疑特征", tone: "warn" },
  High: { text: "高度疑似AI参与", tone: "bad" },
  Critical: { text: "确认AI生成或篡改", tone: "bad" },
};

export const FALLBACK_TIER: Tier = "Moderate";

export function tierOf(result: AnalysisResult): Tier {
  const t = result.jury?.tier ?? result.report?.jury?.tier;
  return t && t in TIER_LABEL ? t : FALLBACK_TIER;
}
