"use client";

import React, { useEffect, useRef, useState } from "react";
import { Upload } from "lucide-react";
import { checkHealth, validateFile } from "@/lib/api";
import { trackUploadClick } from "@/lib/analytics";

interface UploadDeviceProps {
  onUpload: (file: File) => void;
  disabled?: boolean;
}

export const UploadDevice: React.FC<UploadDeviceProps> = ({ onUpload, disabled = false }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [hovered, setHovered] = useState(false);
  const [isDragActive, setIsDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [engineOnline, setEngineOnline] = useState<boolean | null>(null);

  useEffect(() => {
    let mounted = true;
    checkHealth().then((ok) => {
      if (mounted) setEngineOnline(ok);
    });
    return () => {
      mounted = false;
    };
  }, []);

  const acceptFile = (file: File) => {
    const problem = validateFile(file);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    onUpload(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
      setHovered(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
      setHovered(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;
    setIsDragActive(false);
    setHovered(false);
    const file = e.dataTransfer.files?.[0];
    if (file) acceptFile(file);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) acceptFile(file);
    // 允许重复选择同一文件
    e.target.value = "";
  };

  const statusDot =
    engineOnline === null
      ? "bg-white/50"
      : engineOnline
        ? "bg-emerald-400 animate-pulse"
        : "bg-zinc-500";
  const statusText =
    engineOnline === null ? "连接分析引擎…" : engineOnline ? "分析引擎 在线" : "引擎离线（仍可重试）";

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => !isDragActive && setHovered(false)}
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      className={`relative w-full max-w-lg aspect-[1.5/1] rounded-3xl spatial-glass p-7 flex flex-col justify-between
        transition-all duration-500 ease-[var(--ease-spatial)] overflow-hidden select-none
        ${disabled ? "opacity-50 pointer-events-none" : "pointer-events-auto"}
        ${hovered ? "border-white/20 -translate-y-1" : "border-white/5"}
      `}
    >
      <div className="hover-glow-ring" style={{ opacity: hovered ? 1 : 0 }} />

      {/* 头部：真实引擎状态 */}
      <div className="flex justify-between items-center z-10">
        <div className="flex items-center gap-2.5">
          <div className={`w-2 h-2 rounded-full ${statusDot}`} />
          <span className="text-xs tracking-wide text-white/60">{statusText}</span>
        </div>
        <span className="font-mono text-[9px] text-white/25 uppercase tracking-widest">
          Physics-Based
        </span>
      </div>

      {/* 拖拽 / 点击上传区 */}
      <label
        onClick={() => trackUploadClick({ source: "upload_device" })}
        className={`relative flex flex-col items-center justify-center flex-1 my-4 rounded-2xl cursor-pointer z-10 overflow-hidden
          border border-dashed transition-colors duration-300 diagnostic-grid
          ${isDragActive ? "border-white/40 bg-white/[0.04]" : "border-white/10 bg-white/[0.01] hover:bg-white/[0.02]"}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept="image/*"
          onChange={handleFileInput}
          disabled={disabled}
        />

        <div className="flex flex-col items-center justify-center gap-3 text-center p-6">
          <div className="p-4 rounded-full bg-white/[0.03] border border-white/10 transition-transform duration-500 ease-[var(--ease-spatial)] group-hover:scale-105">
            <Upload className="w-6 h-6 text-white/80" />
          </div>
          <div className="flex flex-col gap-1.5">
            <span className="text-sm font-semibold tracking-wide text-white/90">
              {isDragActive ? "松手开始检测" : "拖入图片，或点击选择"}
            </span>
            <span className="text-xs text-white/40 tracking-wide">
              JPG / PNG · 10MB 以内 · 不会保存你的图片
            </span>
          </div>
        </div>
      </label>

      {/* 校验错误（内联，可被屏幕阅读器播报） */}
      <div aria-live="polite" className="z-10 min-h-[1rem] -mt-2 mb-1">
        {error && <p className="text-xs text-red-300 text-center">{error}</p>}
      </div>

      {/* 底部装饰性微标签 */}
      <div className="flex justify-between items-center z-10 font-mono text-[9px] text-white/25 uppercase tracking-widest">
        <span>Powered by OpenCV + VLM</span>
        <span>Alpha No.1</span>
      </div>
    </div>
  );
};
