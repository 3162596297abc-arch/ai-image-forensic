import { UploadZone } from "@/components/upload-zone";
import { FloatingShapes } from "@/components/floating-shapes";
import { Cloud } from "lucide-react";

export default function UploadPage() {
  return (
    <main className="relative min-h-screen bg-background overflow-hidden">
      {/* Floating Background Shapes */}
      <FloatingShapes />

      {/* Subtle Grid Pattern */}
      <div 
        className="absolute inset-0 opacity-[0.015]"
        style={{
          backgroundImage: `
            linear-gradient(to right, currentColor 1px, transparent 1px),
            linear-gradient(to bottom, currentColor 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />

      {/* Content */}
      <div className="relative z-10 flex flex-col min-h-screen">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 lg:px-12">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-foreground flex items-center justify-center">
              <Cloud className="w-5 h-5 text-background" />
            </div>
            <span className="text-lg font-semibold tracking-tight text-foreground">
              CloudDrop
            </span>
          </div>
          
          <nav className="hidden md:flex items-center gap-8">
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              功能介绍
            </a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              定价方案
            </a>
            <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
              关于我们
            </a>
          </nav>

          <button className="px-4 py-2 text-sm font-medium rounded-full bg-foreground text-background hover:opacity-90 transition-opacity">
            登录
          </button>
        </header>

        {/* Main Content */}
        <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
          {/* Hero Text */}
          <div className="text-center mb-12 space-y-4 max-w-xl">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-semibold tracking-tight text-foreground text-balance">
              优雅上传
              <br />
              <span className="text-muted-foreground">简约而不简单</span>
            </h1>
            <p className="text-muted-foreground text-lg leading-relaxed">
              拖放即可上传任何文件，享受极简的云端存储体验
            </p>
          </div>

          {/* Upload Zone */}
          <UploadZone />

          {/* Features */}
          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-3xl w-full">
            {[
              {
                title: "安全加密",
                description: "端到端加密，保护您的数据隐私",
              },
              {
                title: "极速传输",
                description: "智能分片上传，享受极致速度",
              },
              {
                title: "无限存储",
                description: "海量空间，满足所有存储需求",
              },
            ].map((feature, index) => (
              <div
                key={index}
                className="text-center p-6 rounded-2xl bg-card/50 backdrop-blur-sm border border-border/30 hover:border-border/60 transition-all duration-300 hover:shadow-lg"
              >
                <h3 className="text-base font-semibold text-foreground mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <footer className="px-6 py-6 lg:px-12 text-center">
          <p className="text-xs text-muted-foreground">
            © 2024 CloudDrop. 简约设计，极致体验。
          </p>
        </footer>
      </div>
    </main>
  );
}
