# 阿尔法No1 — 图像真实性验证系统

> 上传一张图片，看它是相机拍的，还是 AI 生成的。

系统先用计算机视觉从光影、噪声、结构、纹理等物理维度提取真实世界的规律特征，再交给视觉大模型综合研判，输出有依据的判定与多维分析报告。

---

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Next.js 16 + React 19 + Tailwind v4 + framer-motion + Lenis + three/R3F（晨昏线背景） |
| 后端 | FastAPI + OpenCV（物理特征陪审团） |
| 视觉研判 | Qwen-VL（DashScope） |
| 报告生成 | DeepSeek API |
| 部署 | Vercel（前端）+ Railway（后端） |

---

## 快速启动

### 1. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入 `QWEN_API_KEY`、`DEEPSEEK_API_KEY`（没有 key 也能跑通流程，报告走兜底文案）。

### 2. 启动后端（端口 8001）

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:3000`。前端通过 Next rewrite 把 `/api/*` 代理到后端（`BACKEND_URL` 环境变量，默认 `http://localhost:8001`）。

### 一键启动（Windows）

```powershell
.\start.ps1
```

---

## 项目结构

```
ai-image-forensic/
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── layout.tsx               # 根布局（next/font、元数据）
│       │   ├── page.tsx                 # 单页：Hero / 原理 / 三步 / 检测区
│       │   └── globals.css              # 设计 token 与工具类
│       ├── components/
│       │   ├── TerminatorBackground.tsx # 晨昏线流体 shader 背景
│       │   ├── UploadDevice.tsx         # 上传卡（校验 + 引擎状态）
│       │   ├── AnalysisOverlay.tsx      # 分析中覆盖层（进度/错误/取消）
│       │   ├── AuthenticityHUD.tsx      # 结果报告（判决章 + 四维分析）
│       │   ├── GlobalFloatingUpload.tsx # 浮动上传按钮 + 弹窗
│       │   ├── Button.tsx / Magnetic.tsx / RevealText.tsx / ProjectCard.tsx
│       │   ├── SmoothScroll.tsx / ScrollDepthIndicator.tsx / AlertBanner.tsx
│       └── lib/
│           ├── types.ts                 # 后端响应类型 + 判定文案映射
│           └── api.ts                   # analyzeImage / checkHealth / 错误归一
├── backend/
│   ├── main.py                          # FastAPI 入口（端口 8001）
│   ├── routers/analyze.py               # POST /api/analyze、GET /api/health
│   └── services/                        # jury / fusion / ai_detector / deepseek_report
├── start.ps1
└── README.md
```

---

## API

### `POST /api/analyze`

`multipart/form-data`，字段 `file`（image/*，≤10MB）。

```json
{
  "analysis_id": "uuid",
  "scores": { "ai_probability": 0.82, "human_probability": 0.18, "ai_participation": 0.82 },
  "report": {
    "ai_probability_summary": "大白话结论…",
    "dimensions": { "sensor": {}, "structural": {}, "spatial": {}, "editing": {} }
  },
  "jury": { "ai_participation": 0.82, "tier": "High" },
  "system_data": { "relation_triggers": [], "system_degraded": false }
}
```

`tier`：`Low` / `Moderate` / `High` / `Critical`。

### `GET /api/health`

引擎在线状态。

---

## 部署

- 前端 → Vercel：导入 `frontend/`，设置环境变量 `BACKEND_URL=https://<你的后端域名>`。
- 后端 → Railway：导入 `backend/`，配置 `.env.example` 中的变量。

> 推送 GitHub 前确认根目录 `.gitignore` 存在（已包含 `.env*`），真实 key 永不入库。

---

## 后续版本（暂未包含）

用户系统 / 历史记录页（`result/[id]`）/ 热力图查看器 / 分享卡片 / 多语言
