// 统一的 GA4 埋点工具模块。
// 基于 Next.js 官方推荐方案 @next/third-parties/google：脚本注入与 page_view
// 由根布局的 <GoogleAnalytics> 负责，本模块只负责「自定义事件」。
// 所有事件都集中经过这里上报，避免事件名字符串散落各处。
import { sendGAEvent } from "@next/third-parties/google";

/**
 * GA4 Measurement ID（单一事实来源）。
 * 生产环境可用 NEXT_PUBLIC_GA_ID 覆盖；缺省回退到当前站点 ID。
 */
export const GA_MEASUREMENT_ID =
  process.env.NEXT_PUBLIC_GA_ID ?? "G-B8QGCQP3CP";

/** 事件参数：仅允许 GA4 支持的标量类型。 */
export type AnalyticsParams = Record<
  string,
  string | number | boolean | undefined
>;

/**
 * 统一事件上报入口。
 * 内部使用官方 sendGAEvent（向 dataLayer push），由 <GoogleAnalytics> 注入的 gtag 消费。
 * SSR 阶段或未配置 ID 时自动空操作，任意位置调用都安全。
 */
export function trackEvent(name: string, params: AnalyticsParams = {}): void {
  if (typeof window === "undefined" || !GA_MEASUREMENT_ID) return;
  sendGAEvent("event", name, params);
}

/* ------------------------------ 业务事件 ------------------------------ */
/* 可复用的具名追踪函数：调用点只关心「发生了什么」，不关心实现细节。     */

/** 用户点击「上传/检测」入口（打开文件选择器）。 */
export const trackUploadClick = (params?: AnalyticsParams) =>
  trackEvent("upload_click", params);

/** 成功选中一张合规图片（通过前端校验，准备分析）。 */
export const trackUploadSuccess = (params?: AnalyticsParams) =>
  trackEvent("upload_success", params);

/** 分析请求已发往后端。 */
export const trackAnalysisStart = (params?: AnalyticsParams) =>
  trackEvent("analysis_start", params);

/** 分析完成并拿到结果。 */
export const trackAnalysisFinish = (params?: AnalyticsParams) =>
  trackEvent("analysis_finish", params);

/** 用户分享了检测结果。 */
export const trackShareResult = (params?: AnalyticsParams) =>
  trackEvent("share_result", params);
