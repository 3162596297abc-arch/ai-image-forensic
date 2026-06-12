"use client";

import { useState, useCallback, useRef } from "react";
import { Upload, X, Check, FileText, Image, Film, Music } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadedFile {
  id: string;
  file: File;
  progress: number;
  status: "uploading" | "completed" | "error";
}

export function UploadZone() {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const simulateUpload = (uploadedFile: UploadedFile) => {
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 15;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setFiles((prev) =>
          prev.map((f) =>
            f.id === uploadedFile.id
              ? { ...f, progress: 100, status: "completed" }
              : f
          )
        );
      } else {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === uploadedFile.id ? { ...f, progress } : f
          )
        );
      }
    }, 200);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    const newFiles: UploadedFile[] = droppedFiles.map((file) => ({
      id: crypto.randomUUID(),
      file,
      progress: 0,
      status: "uploading",
    }));

    setFiles((prev) => [...prev, ...newFiles]);
    newFiles.forEach(simulateUpload);
  }, []);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (!e.target.files) return;

      const selectedFiles = Array.from(e.target.files);
      const newFiles: UploadedFile[] = selectedFiles.map((file) => ({
        id: crypto.randomUUID(),
        file,
        progress: 0,
        status: "uploading",
      }));

      setFiles((prev) => [...prev, ...newFiles]);
      newFiles.forEach(simulateUpload);
    },
    []
  );

  const removeFile = useCallback((id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  const getFileIcon = (type: string) => {
    if (type.startsWith("image/")) return Image;
    if (type.startsWith("video/")) return Film;
    if (type.startsWith("audio/")) return Music;
    return FileText;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      {/* 3D Upload Zone */}
      <div className="perspective-1000">
        <div
          onClick={() => inputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "relative group cursor-pointer preserve-3d transition-all duration-500 ease-out",
            isDragging && "scale-[1.02]"
          )}
          style={{
            transform: isDragging
              ? "rotateX(2deg) rotateY(0deg) translateZ(20px)"
              : "rotateX(0deg) rotateY(0deg) translateZ(0px)",
          }}
        >
          {/* Glass Card */}
          <div
            className={cn(
              "relative overflow-hidden rounded-3xl border border-border/50 p-12",
              "bg-card/80 backdrop-blur-xl",
              "shadow-[0_8px_32px_rgba(0,0,0,0.08)]",
              "transition-all duration-500 ease-out",
              "group-hover:shadow-[0_20px_60px_rgba(0,0,0,0.12)]",
              "group-hover:border-accent/30",
              isDragging && "border-accent bg-accent/5"
            )}
          >
            {/* Animated Gradient Background */}
            <div
              className={cn(
                "absolute inset-0 opacity-0 transition-opacity duration-500",
                "bg-gradient-to-br from-accent/10 via-transparent to-accent/5",
                "group-hover:opacity-100",
                isDragging && "opacity-100"
              )}
            />

            {/* Content */}
            <div className="relative flex flex-col items-center gap-6 text-center">
              {/* 3D Icon Container */}
              <div
                className={cn(
                  "relative w-20 h-20 rounded-2xl",
                  "bg-gradient-to-br from-muted to-secondary",
                  "flex items-center justify-center",
                  "shadow-[0_4px_20px_rgba(0,0,0,0.06)]",
                  "transition-all duration-500 ease-out preserve-3d",
                  "group-hover:shadow-[0_12px_40px_rgba(0,0,0,0.1)]",
                  isDragging && "scale-110"
                )}
                style={{
                  transform: isDragging
                    ? "translateZ(30px) rotateX(-5deg)"
                    : "translateZ(0px)",
                }}
              >
                <Upload
                  className={cn(
                    "w-8 h-8 text-muted-foreground transition-all duration-500",
                    "group-hover:text-accent group-hover:scale-110",
                    isDragging && "text-accent scale-110 animate-bounce"
                  )}
                />
              </div>

              <div className="space-y-2">
                <h3
                  className={cn(
                    "text-xl font-semibold tracking-tight text-foreground",
                    "transition-colors duration-300"
                  )}
                >
                  {isDragging ? "松开以上传" : "拖放文件到这里"}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  支持任意格式的文件
                  <br />
                  或{" "}
                  <span className="text-accent font-medium cursor-pointer hover:underline">
                    点击选择文件
                  </span>
                </p>
              </div>

              {/* Supported Formats */}
              <div className="flex items-center gap-3 text-xs text-muted-foreground/60">
                <span className="px-2 py-1 rounded-full bg-muted">图片</span>
                <span className="px-2 py-1 rounded-full bg-muted">视频</span>
                <span className="px-2 py-1 rounded-full bg-muted">文档</span>
                <span className="px-2 py-1 rounded-full bg-muted">音频</span>
              </div>
            </div>
          </div>

          {/* 3D Shadow Layer */}
          <div
            className={cn(
              "absolute inset-0 -z-10 rounded-3xl",
              "bg-gradient-to-b from-foreground/5 to-foreground/10",
              "blur-2xl transition-all duration-500",
              "opacity-0 group-hover:opacity-100",
              isDragging && "opacity-100 scale-105"
            )}
            style={{
              transform: "translateY(10px) translateZ(-20px)",
            }}
          />
        </div>

        <input
          ref={inputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {/* Uploaded Files List */}
      {files.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-muted-foreground px-1">
            已上传文件
          </h4>
          <div className="space-y-2">
            {files.map((uploadedFile, index) => {
              const FileIcon = getFileIcon(uploadedFile.file.type);
              return (
                <div
                  key={uploadedFile.id}
                  className="perspective-1000"
                  style={{
                    animationDelay: `${index * 50}ms`,
                  }}
                >
                  <div
                    className={cn(
                      "group relative flex items-center gap-4 p-4 rounded-2xl",
                      "bg-card/80 backdrop-blur-sm border border-border/50",
                      "shadow-[0_2px_12px_rgba(0,0,0,0.04)]",
                      "transition-all duration-300 ease-out",
                      "hover:shadow-[0_8px_24px_rgba(0,0,0,0.08)]",
                      "hover:border-border",
                      "animate-in slide-in-from-bottom-2 fade-in duration-300"
                    )}
                  >
                    {/* File Icon */}
                    <div
                      className={cn(
                        "flex-shrink-0 w-12 h-12 rounded-xl",
                        "bg-gradient-to-br from-muted to-secondary",
                        "flex items-center justify-center",
                        "transition-transform duration-300",
                        "group-hover:scale-105"
                      )}
                    >
                      <FileIcon className="w-5 h-5 text-muted-foreground" />
                    </div>

                    {/* File Info */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">
                        {uploadedFile.file.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(uploadedFile.file.size)}
                      </p>

                      {/* Progress Bar */}
                      {uploadedFile.status === "uploading" && (
                        <div className="mt-2 h-1 w-full bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-accent rounded-full transition-all duration-300 ease-out"
                            style={{ width: `${uploadedFile.progress}%` }}
                          />
                        </div>
                      )}
                    </div>

                    {/* Status / Actions */}
                    <div className="flex-shrink-0">
                      {uploadedFile.status === "completed" ? (
                        <div className="w-8 h-8 rounded-full bg-green-500/10 flex items-center justify-center">
                          <Check className="w-4 h-4 text-green-600" />
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground tabular-nums">
                          {Math.round(uploadedFile.progress)}%
                        </span>
                      )}
                    </div>

                    {/* Remove Button */}
                    <button
                      onClick={() => removeFile(uploadedFile.id)}
                      className={cn(
                        "absolute -top-2 -right-2 w-6 h-6 rounded-full",
                        "bg-foreground text-background",
                        "flex items-center justify-center",
                        "opacity-0 scale-75 transition-all duration-200",
                        "group-hover:opacity-100 group-hover:scale-100",
                        "hover:bg-destructive"
                      )}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
