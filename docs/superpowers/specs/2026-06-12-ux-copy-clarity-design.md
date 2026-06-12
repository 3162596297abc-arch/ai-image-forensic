# UX 可懂性整改 设计规格（已批准执行）

- 日期：2026-06-12
- 来源：用户要求站在普通用户视角审计"进来知道是干嘛的吗/会操作吗/看得懂结果吗"
- 批准范围：A+B+C（轻改包）、D（结果页人话化）、D12（后端 prompt 文案，用户单独授权）、E（结果页两层结构）

## 已实施清单

| 项 | 内容 | 文件 |
|---|---|---|
| A1 | 副标题取消逐字动画，整块随父容器淡入，3 秒内信息完整可读 | page.tsx |
| A2 | 删除"在线时长"伪信息时钟 → 真实引擎状态点（checkHealth 探活），页脚同源 | page.tsx |
| B3 | 宣言区两段术语墙 → 一段人话 + `<details>` 折叠完整维度列表 | page.tsx |
| B4 | 三步卡描述压至一行；"为什么不直接让AI看图"卡片文案减半 | page.tsx |
| C5 | 分析等待轮播：英文术语 → 中文真实步骤（"正在检查光影是否自然…"），轮换 1.5s | AnalysisOverlay.tsx |
| C6 | 增加预期管理："通常需要 20～60 秒" | AnalysisOverlay.tsx |
| D7 | 状态徽章 ANOMALOUS/SUSPICIOUS/STABLE → 异常/可疑/正常（映射表） | AuthenticityHUD.tsx |
| D8 | "异常指数" → "可疑程度" | AuthenticityHUD.tsx |
| D9 | 检测项术语 → 人话映射表（10 条，覆盖后端两套命名），原术语保留在科普折叠区 | AuthenticityHUD.tsx |
| D10 | 警告横幅人话化 + 去重（"熔断/负载过高" → "部分检测项没能完成（网络原因）…"） | AlertBanner.tsx |
| D11 | 科普入口：14px 图标 → 可见文字链"这是怎么检测的？"；Hash ID 降权 | AuthenticityHUD.tsx |
| D12 | 后端 LLM prompt 重写：禁术语词表、禁复述数字、≤2 句人话总结；user_prompt 喂给 LLM 的证据全部预转人话（仲裁/ELA/熔断等术语不再进入 LLM 输入）；mock/fallback 文案同步人话化。**仅动文案，零算法改动** | backend/services/deepseek_report.py |
| E | 结果页两层：默认 判决章+人话总结+三条关键发现（按可疑度排序）；"查看详细数据 +"展开原四 tab 全量数据 | AuthenticityHUD.tsx |

## 验收

- tsc 零错误 + 截图核对首屏/结果页（结果页需后端在线跑一次真实分析）
- 文案抽查：任何用户可见文本不出现 仲裁/熔断/偏差/ELA/CMOS/FFT/ANOMALOUS 等词（科普折叠区除外，那里是有意保留的术语教学区）
