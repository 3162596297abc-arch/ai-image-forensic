import type { Metadata } from "next";
import { Outfit, JetBrains_Mono } from "next/font/google";
import { GoogleAnalytics } from "@next/third-parties/google";
import "./globals.css";
import SmoothScroll from "@/components/SmoothScroll";
import { GA_MEASUREMENT_ID } from "@/lib/analytics";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jbmono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "阿尔法No1 // 图像真实性验证系统",
  description:
    "上传一张图片，看它是相机拍的还是 AI 生成的——基于物理规律的图像真实性分析。",
  openGraph: {
    title: "阿尔法No1 — 图像真实性验证",
    description: "上传一张图片，看它是相机拍的还是 AI 生成的。",
    locale: "zh_CN",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="zh-CN"
      className={`h-full antialiased ${outfit.variable} ${jetbrainsMono.variable}`}
    >
      <body className="min-h-full flex flex-col">
        <SmoothScroll>{children}</SmoothScroll>
      </body>
      {/* GA4：官方组件，hydration 后异步加载 gtag，自动统计 page_view（含 App Router 客户端路由切换），不阻塞渲染、不影响 SEO/性能 */}
      {GA_MEASUREMENT_ID ? <GoogleAnalytics gaId={GA_MEASUREMENT_ID} /> : null}
    </html>
  );
}
