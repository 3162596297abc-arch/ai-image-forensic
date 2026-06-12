import type { AnalysisResult } from "./types";

// 统一走 next.config.ts 的 /api/* rewrite：
// 本地回退 http://localhost:8001，部署时由 BACKEND_URL 环境变量决定。
const ANALYZE_TIMEOUT_MS = 90_000; // 与后端 timeout_keep_alive=90 对齐
const HEALTH_TIMEOUT_MS = 3_000;
const MAX_FILE_SIZE = 10 * 1024 * 1024;

export class NetworkError extends Error {
  readonly kind = "network";
  constructor() {
    super("无法连接分析引擎");
  }
}

export class ServerError extends Error {
  readonly kind = "server";
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(detail || `服务端错误 ${status}`);
  }
}

export class TimeoutError extends Error {
  readonly kind = "timeout";
  constructor() {
    super("分析超时");
  }
}

export class CancelledError extends Error {
  readonly kind = "cancelled";
  constructor() {
    super("已取消");
  }
}

export type AnalysisError = NetworkError | ServerError | TimeoutError | CancelledError;

/** 上传前置校验，与后端规则一致。返回中文错误信息，合规返回 null。 */
export function validateFile(file: File): string | null {
  if (!file.type.startsWith("image/")) return "请上传图片文件（JPG / PNG）";
  if (file.size > MAX_FILE_SIZE) return "图片不能超过 10MB";
  return null;
}

export async function analyzeImage(file: File, signal?: AbortSignal): Promise<AnalysisResult> {
  const fd = new FormData();
  fd.append("file", file);

  const timeoutSignal = AbortSignal.timeout(ANALYZE_TIMEOUT_MS);
  const merged = signal ? AbortSignal.any([signal, timeoutSignal]) : timeoutSignal;

  let res: Response;
  try {
    res = await fetch("/api/analyze", { method: "POST", body: fd, signal: merged });
  } catch {
    if (signal?.aborted) throw new CancelledError();
    if (timeoutSignal.aborted) throw new TimeoutError();
    throw new NetworkError();
  }

  if (!res.ok) {
    let detail = "";
    try {
      detail = ((await res.json()) as { detail?: string })?.detail ?? "";
    } catch {
      // 非 JSON 错误体，保持 detail 为空
    }
    throw new ServerError(res.status, detail);
  }

  return (await res.json()) as AnalysisResult;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch("/api/health", { signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS) });
    return res.ok;
  } catch {
    return false;
  }
}

/** 错误 → 错误码行 + 用户可读文案（规格 §4 错误处理总表）。 */
export function describeError(err: unknown): { code: string; message: string } {
  if (err instanceof CancelledError) {
    return { code: "CANCELLED", message: "分析已取消。" };
  }
  if (err instanceof TimeoutError) {
    return { code: "ERR_TIMEOUT_90S", message: "分析超时（90 秒）。可能是引擎负载过高，请稍后重试。" };
  }
  if (err instanceof NetworkError) {
    return { code: "ERR_CONNECTION // /api/analyze", message: "无法连接分析引擎。请确认后端服务已启动。" };
  }
  if (err instanceof ServerError) {
    if (err.status === 429) {
      return { code: "ERR_429_RATE_LIMIT", message: "请求过于频繁，请稍后再试。" };
    }
    if (err.status >= 500) {
      return {
        code: `ERR_${err.status}_ENGINE`,
        message: err.detail || "分析引擎过载或异常，请稍后重试。",
      };
    }
    return { code: `ERR_${err.status}`, message: err.detail || "请求被拒绝，请更换图片重试。" };
  }
  return { code: "ERR_UNKNOWN", message: "发生未知错误，请重试。" };
}
