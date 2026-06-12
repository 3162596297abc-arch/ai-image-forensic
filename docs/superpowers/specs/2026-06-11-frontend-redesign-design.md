# 阿尔法No1 前端改版设计方案 v2

- 日期：2026-06-11
- 状态：**已批准（方案 C · 全面视觉改版），执行中**
- 范围：`frontend/`（含少量根目录环境/脚本配套修改）
- 前置：基于 2026-06-11 的全量代码排查结论（4 个关键 bug、成片死代码、性能与安全隐患）

## 0. 背景与目标

当前前端是一次"未收尾的改版"：视觉骨架（暗夜玻璃 × 太空刑侦感）已成型，但旧版 WebGL 交互被挖掉后留下空壳组件、假延迟和断头数据链路；网络层硬编码导致无法部署；失败场景会向用户展示伪造的检测结论；文案充斥伪术语，新用户无法迅速理解产品。

目标按优先级：

1. **可信赖**：失败时诚实报错，绝不展示占位假数据。
2. **秒懂**：新用户 5 秒内明白"这是什么、我该干嘛"；操作路径一步直达。
3. **可部署**：本地 / 局域网 / Vercel 零代码切换。
4. **完成度**：写好没接的内容接上，不存在功能的残骸删净。
5. **视觉叙事**：晨昏线流体背景 + Apple 式克制的界面语言。

### 0.1 用户补充约束（2026-06-11 批准时提出）

- 不需要工期预估。
- **后端/底层业务逻辑一律不动**，仅前端代码优化（根目录脚本/文档中的端口字样修正属环境配套，不属业务逻辑）。
- 冗余代码该删就删，内容补齐照常执行（即包含方案 B 全部工程整改）。
- 背景为**晨昏线**，要有**流体效果**，参考真实晨昏线的物理形态。
- 其余元素参考 **Apple 官网设计语言**。
- 以用户视角重做按钮布局与文案：进来看得懂、马上理解、用得方便。

## 1. 方案选型（已定）

| 方案 | 内容 | 结论 |
|---|---|---|
| A. 最小整改 | 只修 4 个 P0 bug | 否 |
| B. 整改 + 体验补完 | A + 清理 + 内容补完 + 性能 + 无障碍 | 被 C 包含 |
| **C. 全面视觉改版 ✅** | B 全部 + 晨昏线背景重做 + Apple 语言 + 信息架构/文案重写 | **已选** |

## 2. 总体架构调整

### 2.1 新增数据层（核心变更）

```
frontend/src/lib/
├── types.ts   # 后端响应的完整 TypeScript 类型
└── api.ts     # analyzeImage() 封装：相对路径、超时、错误分类
```

`types.ts` 与 `backend/routers/analyze.py` 的响应逐字段对齐：

```ts
export type DimensionKey = "sensor" | "structural" | "spatial" | "editing";
export type DimensionStatus = "STABLE" | "SUSPICIOUS" | "ANOMALOUS";
export type Tier = "Low" | "Moderate" | "High" | "Critical";

export interface Dimension {
  status: DimensionStatus;
  score: number;                 // 0–1
  description: string;
  suggestion: string;
  sub_metrics: { name: string; value: number }[];
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
```

`api.ts`：

- 请求 **`/api/analyze`（相对路径）**，走 `next.config.ts` 已有的 rewrite（`BACKEND_URL` 环境变量 → 本地回退 8001）。删除组件里的 `http://localhost:8001` 硬编码。
- `AbortController` 超时 **90s**（与后端 `timeout_keep_alive=90` 对齐），支持外部 signal 用于"取消"。
- 检查 `res.ok`；非 2xx 解析 FastAPI 的 `{detail}`。
- 错误归一：`NetworkError` / `ServerError(status, detail)` / `TimeoutError`，联合类型 `AnalysisError`。

### 2.2 请求上移，状态收敛

`fetch` 从 `RealityReconstruction` 的 effect 移出，**在 `page.tsx` 的上传事件里发起**，Promise 传给动画组件：

- 修掉 dev StrictMode 双跑导致的**重复请求**（双倍烧 Qwen/DeepSeek token）。
- 动画组件与网络解耦。

`page.tsx` 的 6 个散状态收敛为状态机：

```ts
type AnalysisPhase =
  | { status: "idle" }
  | { status: "analyzing"; file: File; promise: Promise<AnalysisResult> }
  | { status: "success";  file: File; result: AnalysisResult }
  | { status: "error";    file: File; error: AnalysisError };
```

`hovered` 下放到各 `UploadDevice` 内部；`cardRect/swallowed` 随死代码删除。

### 2.3 删除层

| 目标 | 处理 |
|---|---|
| `SpatialCanvas.tsx`（return null 空壳） | 删除，连同 page.tsx 的 props |
| `UploadDevice` 的 ResizeObserver + scroll 监听 + `onRectUpdate` | 删除 |
| `src/shaders/index.ts`（291 行无引用 GLSL） | 删除 |
| `handleUpload` 的 1400ms 假延迟 + 600ms 滚动串行 | 删除/并行化 |
| 依赖 `canvas-confetti`、`ogl`、`@react-three/postprocessing` | 卸载 |
| `gsap` + `ScrollTrigger`（仅 handleReset 一处使用） | 卸载；reset 改 framer-motion exit |
| `@react-three/drei`（分析层 Canvas 移除后无消费者） | 卸载 |
| HUD 内 `logs/logContainerRef/containerRef`（未绑定 DOM） | 删除 |
| CSS `custom-cursor-active`（无自定义光标功能） | 删除 |
| CSS `diagnostic-grid`/`scanner-line` | 复用（上传区底纹/扫描光）；`dot-grid` 无处可用则删 |
| `Magnetic.tsx`（收参数不干活） | **真实现**（见 V.6） |

### 2.4 渲染层简化

分析过程的第二个 `<Canvas>`（`MeshTransmissionMaterial` + `Environment`）整体移除，玻璃效果 DOM 化。全站只保留 `SpatialBackground` 一个常驻 Canvas（晨昏线 shader，见 V.2）。

## 3. 工程阶段（继承自 v1，估时按用户要求移除）

### Phase 0 — 安全与环境（先行）

1. **根目录新建 `.gitignore`**（`.env*`、`backend/venv/`、`node_modules/`、`.next/`、`*.log`、`tsconfig.tsbuildinfo` 等），**先于任何 git 操作**（.env 内有真实 key）。随后 git init + 基线提交，保护改版过程可回滚。
2. 端口统一 **8001**：README、start.ps1 提示输出、根 `.env` 的 `BACKEND_URL`。
3. `start.ps1` 只杀自己启动的进程（记录 PID），不再全机强杀 python/node。

### Phase 1 — 数据链路与可靠性

1. 落地 2.1 / 2.2。
2. **错误态 UI**：覆盖层在 reject 时原地变形为错误卡（红描边 + `AlertTriangle` + 等宽错误码 + 中文说明 + [重新分析] [返回]）。文案映射见 §4。错误时恢复滚动，绝不出现 "ANALYSIS COMPLETE"。
3. **取消出口**：覆盖层挂载 3s 后浮现"取消"按钮 → abort → 回 idle。
4. `AuthenticityHUD` 删除 `0.0086` 占位逻辑，仅在 success 下渲染，prop 改为必填 `result: AnalysisResult`。
5. 上传前置校验（image/* 且 ≤10MB），不合规即时内联提示。

### Phase 2 — 清理与提速

1. 执行 2.3 删除清单 + 卸载五个依赖。
2. 新上传时序：点击/拖入 → 立即发请求 + 滚动（并行）→ 上传卡 300ms 吸入微动画 → 覆盖层即刻入场。无效等待 ≤600ms。
3. 浮动上传钮 `status !== "idle"` 时隐藏。

### Phase 3 — 内容补完

1. `getGlossaryForTab` 四组科普文案接入 HUD 各 tab（`HelpCircle` 图标 → "这项检测在看什么？"折叠区）。
2. `jury.tier` 接入为中文判决章：Low→"未见明显AI痕迹"（绿）/ Moderate→"存在可疑特征"（琥珀）/ High→"高度疑似AI参与"（红）/ Critical→"确认AI生成或篡改"（红+强）。判决章为主结论，概率数字降为辅助。
3. HUD `TIMESTAMP` 固定为分析完成时刻；首页"系统时间戳"改"在线时长"。

### Phase 4 — 性能与加载

1. 删 Google Fonts `@import`；`next/font/google` 自托管 Outfit + JetBrains Mono（swap，latin）；中文显式系统栈 `'PingFang SC','Microsoft YaHei',system-ui`。
2. 执行 2.4；`SpatialBackground` 提供 `prefers-reduced-motion`/WebGL 失败的静态渐变降级。
3. blur 审计：去嵌套 blur。
4. `ProjectCard` 图去 `priority` 改懒加载。

### Phase 5 — 体验与无障碍

1. `lang="zh-CN"`；metadata 中文化 + 基础 OpenGraph。
2. 弹窗规范：lenis.stop/start、Esc、点遮罩关闭、焦点管理、图标按钮 aria-label。
3. **证据图不裁切**：object-contain + 同图模糊放大垫底（letterbox）。
4. 移动端导航：汉堡 → 玻璃面板锚点列表。
5. 信息文字对比度下限 `text-white/50`（≤12px 时）；纯装饰微标签除外。
6. `prefers-reduced-motion` 全降级。

## V. 视觉改版设计（方案 C 核心）

### V.1 概念：晨昏线 The Terminator

产品隐喻：晨昏线是行星上昼与夜的分界——**真实与生成之间的那条线**。背景不再是装饰，是品牌叙事。

取自真实晨昏线的物理特征 → 设计映射：

| 真实物理 | 设计映射 |
|---|---|
| 不是锐利的线，是暮光渐变带（民用/航海/天文暮光三层） | 宽渐变带，多层亮度结构 |
| 大气散射：贴近地表的暖金→桃→青→深蓝光谱过渡 | 带内光谱渐变（压暗去饱和，维持 dark luxury） |
| 云层把晨昏线切割成不规则流体边缘 | fbm + domain warping 扰动边界（**流体感的来源**） |
| 轨道视角下是大半径弧线 | 屏宽 1.5–2 倍半径的弧形带 |
| 移动极缓慢 | 全周期 ≥60s 的时间系数 |

### V.2 晨昏线 shader（重写 SpatialBackground 片元）

保留单 Canvas + ShaderMaterial + DPR≤1.5 架构，片元分层：

1. **夜侧基底**：近黑深蓝三段渐变（沿用 #040507/#06080C/#080B10）。
2. **晨昏带**：以大半径弧的符号距离为坐标，构造宽渐变带；带内光谱（由近弧到远弧）：暖金 `#C98A4B` 调 → 玫瑰灰 → 青 `#4FD1C5` 调 → 融入夜侧深蓝。所有色压饱和压亮度，峰值亮度不超过现版本弧光。
3. **流体扰动**：两层 domain-warped fbm（`fbm(p + fbm(p))`）调制：a) 边界位置（云层切割感）、b) 带内密度（流动的明暗斑块）。时间系数 ≤0.02，叠加极缓慢横向漂移。
4. **大气辉光 rim**：沿弧线的细高亮层（复用现 primary/secondary/halo 多层高斯结构与蓝白色系）。
5. **呼吸**：保留但改为 0.55–1.0 区间（现版 cos² 会周期性全黑熄灭）。
6. **grain**：细颗粒防 banding。

降级：`prefers-reduced-motion` 或 WebGL 创建失败 → 静态 CSS 渐变（同色板）。

### V.3 Apple 设计语言应用

三原则落地：

- **Clarity**：每屏一个主信息、一个主操作；信息载体字号 ≥12px（7–9px 等宽字只做装饰性 micro-label）。
- **Deference**：界面退后内容向前——玻璃卡减少嵌套描边/内发光层（现 UploadDevice 叠 4 层光效），留白加大。
- **Depth**：层次靠模糊与视差，不靠边框堆叠。

**按钮体系（全站统一 token）**：

| 层级 | 样式 | 用途 |
|---|---|---|
| Primary | 白底黑字胶囊，hover 提亮上浮 2px，active 0.97 | 上传/检测主操作，**同屏唯一** |
| Secondary | 玻璃胶囊 + 白描边 | 次操作（了解原理、返回） |
| Tertiary | 纯文字 + 箭头 | 行内链接 |

焦点环：2px 白 ring + offset（键盘可达）。圆角与间距 token：`--radius-pill`、`--radius-card: 24px`、8pt 网格。

### V.4 信息架构与文案重写（"秒懂"原则）

诊断：现首屏诗意有余信息不足；上传区"零知识资产验证 / 加密完整性 / 置入视觉资产"为伪术语，阻碍理解。

重写原则：主文案直白回答"这是什么 + 我能干嘛"；刑侦风术语降级为装饰，不承载关键信息。

- **Hero**：
  - H1：辨伪求真（品牌，保留）
  - 副标题：**"上传一张图片，看它是相机拍的，还是 AI 生成的。"**
  - 主按钮：`[上传图片检测]`（Primary，点击直接弹文件选择器——首屏不再陈列整个上传卡，认知负担减半）
  - 次按钮：`[它是怎么判断的？]` → 滚动到原理区
  - 信任行（小字）：免费 · 无需注册 · 不保存你的图片
- **导航**：首页 / 工作原理 / 开始检测 + 右侧常驻 Primary CTA；编号前缀保留为风格但不再是唯一标识。移动端汉堡（Phase 5.4）。
- **上传卡**（实验区保留完整卡）：「拖入图片，或点击选择」「JPG / PNG · 10MB 以内 · 不会保存你的图片」；"安全协议//激活"等假状态灯删除或接 `/api/health` 真状态。
- **三步卡**：用户视角动词重写——上传图片 → AI 多维分析 → 拿到判定报告。
- **结果页**：判决章（tier）为主结论 + `ai_probability_summary` 大白话一句 + 四维 tab；术语进折叠科普区。
- **页脚**：删除 "DESIGNED BY ANTIGRAVITY / 引擎节点 © 2026 // 连贯态" 等占位文案，改为产品一句话 + 导航 + 状态行。
- **浮动上传钮**：图标 + "检测图片" 文字标签；非 idle 隐藏。

### V.5 判决时刻

概率数字 0→终值 1.2s count-up（ease-out-expo），60% 进度处颜色由白解析为绿/琥珀/红；tier 判决章盖章动效（scale 1.15→1 + 微震）落下；首页巨字水印在结果区按判定回显 **REAL / SYNTHETIC**（同款 0.03 透明度），首尾叙事闭环。

### V.6 Magnetic 真实现

framer-motion `useMotionValue` + spring（stiffness 150 / damping 15 / mass 0.1），进入 `range` 按 `strength` 偏移，离开回弹；`prefers-reduced-motion` 直通渲染。

### V.7 动效原则

- 时长 200–600ms，统一 `--ease-spatial: cubic-bezier(0.16,1,0.3,1)`
- 入场 stagger ≤60ms；滚动 reveal 仅一次
- reduced-motion 全降级为淡入

## 4. 错误处理总表

| 场景 | 检测方式 | 用户所见 | 可恢复操作 |
|---|---|---|---|
| 后端未启动 | fetch TypeError | 错误卡：无法连接分析引擎 | 重试 / 返回 |
| 文件非图片 / 超 10MB | 前端预校验 | 上传卡内联红字 | 重新选择 |
| 429 限流 | res.status | "请求过于频繁，请稍后再试" | 重试 |
| 503 / 5xx | res.status | "分析引擎过载或异常" + detail | 重试 / 返回 |
| 超时 90s | AbortController | "分析超时" | 重试 / 返回 |
| 用户取消 | abort() | 静默回 idle | — |
| system_degraded（成功但降级） | 响应字段 | 现有 AlertBanner 保留 | — |

不变量：**任何失败路径不得出现进度 100%、"ANALYSIS COMPLETE" 或占位概率；滚动锁随覆盖层退出释放。**

## 5. 测试与验收

- 每阶段：`npx tsc --noEmit` + `npm run build` 通过（当前执行器故障，恢复后首先补跑基线）。
- 手动 E2E：① 在线全流程；② 后端关闭→错误卡+重试；③ 超限文件；④ 分析中取消；⑤ Network 面板确认单次请求；⑥ 375px 走查；⑦ `BACKEND_URL` 指向局域网验证 rewrite；⑧ reduced-motion 走查。
- 视觉验收：晨昏线在 1080p/4K/375px 三档分辨率下弧形与流体形态成立；峰值亮度不破坏 dark 氛围；文字对比度抽查。
- 不引入测试框架（YAGNI）。

## 6. 明确不做（YAGNI）

- 不动后端业务逻辑（用户明确约束）
- 不恢复 README 中的 `result/[id]` 路由、热力图、分享卡片（后端 heatmap 已禁用）
- 不加用户系统、多语言、单元测试框架
- 不做自定义光标、不加鼠标视差（克制）

## 7. 风险与对策

| 风险 | 对策 |
|---|---|
| `layoutId` 跨组件 morph 在请求上移后行为变化 | 完成后实测；若跳变降级为坐标过渡并删除重复布局算式 |
| 晨昏线 shader 在低端 GPU 卡顿 | fbm 限 4 octave、warp 限 2 层、DPR≤1.5；降级路径兜底 |
| 字体替换视觉回归 | 单独提交，前后对比 |
| Next 16 行为差异（AGENTS.md 警告） | 涉 next/font、rewrites、Image 先查 `node_modules/next/dist/docs/`；`devIndicators` 按 16 schema 修正 |
| 删依赖后隐藏引用 | 卸载前全局 grep + build 验证 |

## 8. 执行顺序

0 → 1 → 2 严格顺序；3 / 4 / 5 任意顺序；V（视觉改版）最后整体进行，其中 V.2 晨昏线可与 3–5 并行。每阶段独立可交付。
