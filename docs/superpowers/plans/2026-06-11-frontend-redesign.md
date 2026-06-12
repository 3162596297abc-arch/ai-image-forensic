# 阿尔法No1 前端改版（方案C）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按已批准规格 v2 完成前端全面改版：修复数据链路、删除死代码、补齐内容、晨昏线流体背景、Apple 式界面语言与"秒懂"文案。

**Architecture:** 新增 `lib/` 数据层（typed api + 状态机上移 page.tsx）；删除第二个 Canvas 与全部空壳组件；`SpatialBackground` 重写为晨昏线 domain-warped fbm shader（全站唯一 Canvas）；结果交接用稳健交叉淡入替代 layoutId 形变（消除规格风险项#1）。

**Tech Stack:** Next.js 16 / React 19 / Tailwind v4 / framer-motion 12 / three+R3F（仅背景）/ Lenis（自驱 rAF，去 GSAP）/ next/font。

**约束（用户）：** 后端业务逻辑不动；无工期预估；测试=tsc+build+手动清单（规格 §5，不引入测试框架）。

**执行环境说明：** 当前会话 shell 分类器故障。所有文件操作即时执行；以下操作进入**延迟队列**，shell 恢复后按序补跑：① `git init` + 基线提交（注：将捕获改后状态，改前原文已留存于会话审计记录）② `npm uninstall` 5 包 + `npm install` ③ `npx tsc --noEmit` ④ `npm run build` ⑤ 手动 E2E。每完成一个大 Task 重试一次 shell。

---

### Task 1: 安全与环境（规格 Phase 0）

**Files:**
- Create: `E:\ai-image-forensic\.gitignore`
- Modify: `E:\ai-image-forensic\.env`（BACKEND_URL 端口）
- Modify: `E:\ai-image-forensic\start.ps1`（端口提示 + PID 限定清理）
- Modify: `E:\ai-image-forensic\README.md`（端口/结构/技术栈纠偏）

- [ ] **Step 1.1: 写根 .gitignore**

```gitignore
# secrets
.env
.env.*
!.env.example

# python
backend/venv/
__pycache__/
*.pyc

# node / next
node_modules/
.next/
out/
*.tsbuildinfo

# logs & artifacts
*.log
backend/evidence_audit.log
backend/test_*.png

# os/editor
.DS_Store
Thumbs.db
```

- [ ] **Step 1.2: .env 端口统一 8001** — `BACKEND_URL=http://localhost:8000` → `:8001`；`NEXT_PUBLIC_BACKEND_URL` 行删除（无消费者）。
- [ ] **Step 1.3: start.ps1** — 两处 `Start-Process` 加 `-PassThru` 存 `$backendProc/$frontendProc`；提示文本 8000→8001；清理段改为 `Stop-Process -Id $backendProc.Id,$frontendProc.Id -Force -ErrorAction SilentlyContinue`（node 由 npm 派生，需按窗口 PID 树终止：用 `taskkill /PID <id> /T /F`）。
- [ ] **Step 1.4: README** — 端口 8000→8001（3 处）；技术栈表 Next.js 14→16；目录树更新为 `src/app`、现存组件名；删除不存在的 result/[id]、lib/、heatmap 组件描述（标注"后续版本"）。
- [ ] **Step 1.5（延迟队列）:** `git init && git add -A && git commit -m "chore: baseline before redesign"`

### Task 2: 数据层 lib/types.ts + lib/api.ts（规格 2.1）

**Files:**
- Create: `frontend/src/lib/types.ts`
- Create: `frontend/src/lib/api.ts`

- [ ] **Step 2.1: types.ts**（规格 2.1 的接口原文 + `AnalysisError` 联合 + tier 文案映射表）

```ts
export type DimensionKey = "sensor" | "structural" | "spatial" | "editing";
export type DimensionStatus = "STABLE" | "SUSPICIOUS" | "ANOMALOUS" | string;
export type Tier = "Low" | "Moderate" | "High" | "Critical";

export interface SubMetric { name: string; value: number; }
export interface Dimension {
  status: DimensionStatus;
  score: number;
  description: string;
  suggestion: string;
  sub_metrics: SubMetric[];
}
export interface AnalysisResult {
  analysis_id: string;
  scores: { ai_probability: number; human_probability: number; ai_participation: number };
  report: {
    ai_probability_summary: string;
    dimensions: Record<DimensionKey, Dimension>;
    jury: { ai_participation: number; tier: Tier };
  };
  jury: { ai_participation: number; tier: Tier; jury_phases: unknown };
  system_data: { relation_triggers?: string[]; system_degraded?: boolean };
}
export const TIER_LABEL: Record<Tier, { text: string; tone: "ok" | "warn" | "bad" }> = {
  Low:      { text: "未见明显AI痕迹",   tone: "ok"   },
  Moderate: { text: "存在可疑特征",     tone: "warn" },
  High:     { text: "高度疑似AI参与",   tone: "bad"  },
  Critical: { text: "确认AI生成或篡改", tone: "bad"  },
};
```

- [ ] **Step 2.2: api.ts** — `analyzeImage(file, signal?)`：相对路径 `/api/analyze`、90s AbortSignal.any 合成超时、`res.ok` 检查、FastAPI `{detail}` 解析；错误类 `NetworkError/ServerError/TimeoutError` + `toAnalysisError()`；`checkHealth()`：GET `/api/health` 3s 超时返回 boolean；`validateFile(file)`：image/* 且 ≤10MB，返回中文错误或 null。

- [ ] **Step 2.3（延迟队列）:** `npx tsc --noEmit` 通过。

### Task 3: 晨昏线背景 TerminatorBackground（规格 V.1/V.2）

**Files:**
- Create: `frontend/src/components/TerminatorBackground.tsx`
- Delete: `frontend/src/components/SpatialBackground.tsx`（Task 11 统一删除）

- [ ] **Step 3.1: 实现**。单 Canvas + ShaderMaterial，`dpr=[1,1.5]`，`powerPreference:"high-performance"`。片元分层（GLSL 全文写入组件）：
  1. 夜侧三段渐变（#040507/#06080C/#080B10 原色板）；
  2. 大半径弧 `R=1.45*aspect.x`、`center=(0,-1.35*aspect.x)` 的符号距离 `sd`；
  3. **流体**：`warp(p)=p+uWarpStrength*(fbm(p*1.6+t)-0.5, fbm(p*1.6+5.2-0.7t)-0.5)`，边界 `sdF=sd+(fbm(warp(uv*2.2))-0.5)*0.16`（云层切割），带内密度 `dens=0.6+0.8*fbm(warp(uv*3.0+drift))`；
  4. 暮光带三色（day 侧→night 侧偏置的高斯）：金 `#C98A4B`、玫瑰灰 `#8A6A6E`、青 `#3FA8A0`，总和×0.5 亮度护栏；
  5. 大气 rim：沿 `sd` 的 2.5px/4px/8px/20px 四层高斯（复用旧弧光结构与蓝白色系）；
  6. 呼吸 `0.775+0.225*sin(2πt/40)`（区间 0.55–1.0，不熄灭）；grain 防 banding。
  uniforms：`uTime/uResolution/uWarpStrength(0.35)/uBandScale(1.0)`。
- [ ] **Step 3.2: 降级**。`matchMedia("(prefers-reduced-motion: reduce)")` 或 Canvas 抛错（内联 ErrorBoundary）→ 渲染 `.terminator-fallback` 静态 CSS 渐变（globals.css 定义，同色板对角渐变 + 径向暖斑）。
- [ ] **Step 3.3 验收**：1080p/375px 下弧形横贯、边缘云絮状起伏可辨、整体仍是暗页面（延迟队列后人工确认）。

### Task 4: UI 基件 Button + Magnetic 真实现（规格 V.3/V.6）

**Files:**
- Create: `frontend/src/components/Button.tsx`
- Rewrite: `frontend/src/components/Magnetic.tsx`

- [ ] **Step 4.1: Button.tsx** — `variant: "primary"|"secondary"|"tertiary"`，胶囊；primary 白底黑字 hover 上浮 2px/active scale .97；secondary 玻璃+白描边；tertiary 文字+箭头；统一 `focus-visible:ring-2 ring-white/80 ring-offset-2 ring-offset-black`；接受 `as`/onClick/href。
- [ ] **Step 4.2: Magnetic.tsx** — framer-motion `useMotionValue+useSpring({stiffness:150,damping:15,mass:0.1})`；onMouseMove 距中心 ≤range 时按 strength 偏移 x/y，leave 归零；`useReducedMotion()` 为 true 时直通 children。保持现有 props 签名 `{children, range=24, strength=0.35}`（3 处调用零改动）。

### Task 5: SmoothScroll 去 GSAP（规格 2.3）

**Files:**
- Rewrite: `frontend/src/components/SmoothScroll.tsx`

- [ ] **Step 5.1**: 删 gsap/ScrollTrigger import 与 ticker；Lenis 自驱：`const raf=(t:number)=>{lenis.raf(t);rafId=requestAnimationFrame(raf)}`；`prefers-reduced-motion` 时不实例化 Lenis（window.lenis 留空，调用方已有 scrollIntoView 兜底）；卸载时 cancelAnimationFrame + destroy。

### Task 6: UploadDevice 重写（规格 V.4 文案 + Phase 1.5 校验）

**Files:**
- Rewrite: `frontend/src/components/UploadDevice.tsx`

- [ ] **Step 6.1**: 删 onRectUpdate/ResizeObserver/scroll 监听/swallowed prop；props 收敛为 `{onUpload, disabled?}`，hovered 内部化。
- [ ] **Step 6.2 文案**: 头部状态灯接 `checkHealth()`（挂载时一次）：绿点"分析引擎 在线"/灰点"引擎离线（仍可重试）"；中央「拖入图片，或点击选择」副行「JPG / PNG · 10MB 以内 · 不会保存你的图片」；删除"零知识资产验证/EXIF深度审计/加密完整性/置入视觉资产"等伪术语（footer 改 mono 微标签：`PHYSICS-BASED ANALYSIS` / `POWERED BY OPENCV + VLM`，纯装饰）。
- [ ] **Step 6.3 校验**: `validateFile` 不通过 → 卡内红字内联提示（aria-live="polite"），不触发 onUpload。
- [ ] **Step 6.4 视觉**: 拖拽区底纹复用 `.diagnostic-grid`；光效层从 4 层减至 1 层（Deference）。

### Task 7: AnalysisOverlay（替换 RealityReconstruction，规格 Phase 1.2-1.3 + 2.4）

**Files:**
- Create: `frontend/src/components/AnalysisOverlay.tsx`
- Delete: `frontend/src/components/RealityReconstruction.tsx`（Task 11）

- [ ] **Step 7.1 接口**: `{file, promise, onSuccess(result), onError(err), onCancel}`。无 Canvas/three/drei。
- [ ] **Step 7.2 流程**: 挂载锁滚（lenis.stop + wheel/touch preventDefault）；图片入场（scale .9→.96 + blur 2px→0）；`.scanner-line` 扫描光循环；主状态行大白话「正在分析图像物理特征…」+ 下方 mono 微标签轮换 TECH_PHRASES（沿用现有数组）；模拟进度上限 95%，promise resolve→100%。
- [ ] **Step 7.3 成功**: 300ms 定格 → `onSuccess(result)`；交接为整层 0.4s 交叉淡出（**不用 layoutId**，消除规格风险#1；HUD 同图淡入，连续性由图片内容本身保证）。
- [ ] **Step 7.4 失败**: 原地变形错误卡（红描边 spatial-glass + AlertTriangle + mono 错误码行 + §4 中文文案 + [重新分析][返回] 按钮=Button secondary/tertiary）；**立即恢复滚动**。
- [ ] **Step 7.5 取消**: 挂载 3s 后右下浮现 tertiary"取消分析"→ abort → onCancel。卸载清理：恢复 lenis、移除监听、revoke objectURL。
- [ ] **Step 7.6**: 进度/状态文案任何失败路径不得出现 "ANALYSIS COMPLETE"/100%（断言于代码路径：error 分支 setProgress 不变）。

### Task 8: AuthenticityHUD 重写（规格 Phase 3 + V.5 + 5.3）

**Files:**
- Rewrite: `frontend/src/components/AuthenticityHUD.tsx`

- [ ] **Step 8.1 类型化**: props `{file, result: AnalysisResult, onReset}`；删除 0.0086 占位、logs、未绑定 refs、isComplete 分支。
- [ ] **Step 8.2 判决章**: 头部以 `TIER_LABEL[result.jury.tier]` 为主结论（大号、tone 着色、盖章动效 scale 1.15→1 + 2px 震动）；其下 `ai_probability_summary` 一句大白话；右侧概率数字降级为辅助。
- [ ] **Step 8.3 count-up**: framer-motion `animate(0, p, {duration:1.2, ease:[0.16,1,0.3,1], onUpdate})`，60% 进度处颜色 white→tone 色（state 切换）。
- [ ] **Step 8.4 水印**: HUD 容器后绝对定位巨字（text-[10vw] opacity-[0.03]）：tone==="ok"→"REAL" 否则 "SYNTHETIC"。
- [ ] **Step 8.5 科普折叠**: 各 tab 标题旁 HelpCircle 按钮（aria-expanded）→ AnimatePresence 折叠区渲染 `getGlossaryForTab(activeTab)`（现有文案原样接入）。
- [ ] **Step 8.6 证据图**: `object-contain` + 底层同图 `object-cover blur-2xl scale-110 opacity-40` 垫底；alt="待鉴定图片"。
- [ ] **Step 8.7**: TIMESTAMP 用 `useMemo(()=>new Date().toLocaleTimeString(),[])` 固定；AlertBanner 保留；reset 改 framer-motion exit（gsap 移除）。

### Task 9: GlobalFloatingUpload 重写（规格 Phase 2.3 + 5.2）

**Files:**
- Rewrite: `frontend/src/components/GlobalFloatingUpload.tsx`

- [ ] **Step 9.1**: props 加 `visible:boolean`（page 在 status!=="idle" 时 false → AnimatePresence 退场）；FAB 加文字「检测图片」（图标+字，aria-label 同文）。
- [ ] **Step 9.2 弹窗规范**: 打开 `window.lenis?.stop()` 关闭 start；Esc 关闭（useEffect keydown）；遮罩 onClick 关闭（卡片 stopPropagation）；打开时 focus 关闭按钮（ref+useEffect）；关闭按钮 aria-label="关闭"。

### Task 10: layout/globals/字体/token（规格 Phase 4.1 + V.3 + V.7）

**Files:**
- Rewrite: `frontend/src/app/layout.tsx`
- Modify: `frontend/src/app/globals.css`

- [ ] **Step 10.1 layout.tsx**: `import { Outfit, JetBrains_Mono } from "next/font/google"`（`display:"swap"`, subsets latin, CSS 变量 `--font-outfit/--font-jbmono`）；`<html lang="zh-CN" className={...variables}>`；metadata 中文：title 保留，description「上传一张图片，看它是相机拍的还是 AI 生成的——基于物理规律的图像真实性分析」+ openGraph {title, description, locale:"zh_CN", type:"website"}。
- [ ] **Step 10.2 globals.css**: 删 Google Fonts @import；`--font-sans: var(--font-outfit), 'PingFang SC','Microsoft YaHei',system-ui,sans-serif`、`--font-mono: var(--font-jbmono), ui-monospace,monospace`；新增 token：`--ease-spatial`、`--radius-card:24px`、状态三色组（--tone-ok/warn/bad 各 text/bg/border）；删 `.custom-cursor-active` 块与 `.dot-grid`；新增 `.terminator-fallback` 渐变；`@media (prefers-reduced-motion: reduce)` 全局 `*{animation-duration:.01ms!important;transition-duration:.01ms!important}`。

### Task 11: page.tsx 总装 + 文件删除（规格 2.2 + V.4 + 2.3）

**Files:**
- Rewrite: `frontend/src/app/page.tsx`
- Delete: `frontend/src/components/SpatialCanvas.tsx`、`frontend/src/components/RealityReconstruction.tsx`、`frontend/src/components/SpatialBackground.tsx`、`frontend/src/shaders/index.ts`

- [ ] **Step 11.1 状态机**: 规格 2.2 的 `AnalysisPhase` 判别联合 + `startAnalysis(file)`（validate → `analyzeImage` 发起 → setPhase analyzing → 滚动并行）+ `handleSuccess/handleError/handleCancel/handleReset`。AbortController 存 ref。
- [ ] **Step 11.2 Header**: logo（Shield+阿尔法No1+副标）；nav 3 项：首页/工作原理/开始检测；右侧 Primary CTA「开始检测」→ scrollTo laboratory；移动端汉堡 → 全屏玻璃面板 4 锚点（AnimatePresence）；"系统时间戳"→"在线时长"。
- [ ] **Step 11.3 Hero**: REAL 巨字保留；H1 辨伪求真 + 副标「上传一张图片，看它是相机拍的，还是 AI 生成的。」（RevealText）；主按钮 Primary「上传图片检测」→ 隐藏 `<input type=file>` ref.click()；次按钮 Secondary「它是怎么判断的？」→ scrollTo exhibitions；信任行小字「免费 · 无需注册 · 不保存你的图片」；**首屏不再陈列上传卡**。
- [ ] **Step 11.4 中段**: manifesto 文案保留；三步卡标题改：上传图片/AI 多维分析/拿到判定报告（描述微调动词视角）；胶囊问答卡保留。
- [ ] **Step 11.5 实验区**: idle→UploadDevice；analyzing→AnalysisOverlay（fixed 层）；success→AuthenticityHUD；error 由 Overlay 内部呈现（仍处 analyzing 容器，promise 已 reject → overlay 错误态；[返回]→handleReset）。
- [ ] **Step 11.6 Footer**: 左「阿尔法No1 — 用物理规律验证图片真实性」；中导航 4 锚点；右状态行（绿点 引擎在线 接 checkHealth 共享 state）+ `© 2026 阿尔法No1`；删除 ANTIGRAVITY/连贯态/空间导航等占位词。
- [ ] **Step 11.7**: `<GlobalFloatingUpload visible={phase.status==="idle"} onUpload={startAnalysis}>`；ScrollDepthIndicator 保留（标签改：01 首页/02 原理/03 步骤/04 检测）；删除 4 个目标文件。

### Task 12: ProjectCard 微调（规格 Phase 4.4）

**Files:**
- Modify: `frontend/src/components/ProjectCard.tsx`

- [ ] **Step 12.1**: `<Image>` 去 `priority`；alt 用 title；箭头 `<a>` 加 `aria-label={title}`。

### Task 13: 依赖与清理收尾（规格 2.3）

**Files:**
- Modify: `frontend/package.json`

- [ ] **Step 13.1**: dependencies 删除 `canvas-confetti/ogl/@react-three/postprocessing/gsap/@react-three/drei`；devDependencies 删 `@types/canvas-confetti`。保留 three/@react-three/fiber/@types/three（背景）、framer-motion、lenis、lucide-react、next/react。
- [ ] **Step 13.2**: 全局 grep 确认无残留 import（gsap|drei|ogl|confetti|postprocessing|shaders/|SpatialCanvas|RealityReconstruction|SpatialBackground）。
- [ ] **Step 13.3**: `next.config.ts` 的 `devIndicators` 按 Next16 schema 修正（查 node_modules/next/dist/docs 后定：删除或改 `devIndicators:false`）。
- [ ] **Step 13.4（延迟队列）**: `npm install`（重建 lockfile）→ `npx tsc --noEmit` → `npm run build`。

### Task 14: 验收（规格 §5）

- [ ] **Step 14.1（延迟队列）**: build 零错误零 type error。
- [ ] **Step 14.2（延迟队列）**: 手动 E2E 八项（规格 §5）。
- [ ] **Step 14.3（延迟队列）**: git 提交 `feat: full frontend redesign (plan C)`。

---

## Self-Review 记录

- **规格覆盖**: Phase0→T1；2.1/2.2→T2/T11；Phase1→T2/T7/T8/T11；Phase2→T6/T7/T9/T11/T13；Phase3→T8；Phase4→T3/T10/T12；Phase5→T8/T9/T10/T11；V.1/V.2→T3；V.3→T4/T10；V.4→T6/T9/T11；V.5→T8；V.6→T4；V.7→T10。无缺口。
- **占位符**: 无 TBD/TODO；所有文案给出原文；shader 给出分层公式与参数。
- **类型一致**: `AnalysisResult/AnalysisError/TIER_LABEL` 定义于 T2，T7/T8/T11 引用同名；`AnalysisPhase` 仅 T11 使用；Magnetic props 签名与现调用方一致。
- **规格偏差（2 处，均为降险）**: ① 结果交接弃 layoutId 改交叉淡入（消除风险#1）；② shader uniforms 取 uWarpStrength/uBandScale 两个（uPalette 以 GLSL 常量实现）。
