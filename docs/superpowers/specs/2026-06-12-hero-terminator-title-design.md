# Hero 标题「像素证物」粒子化 设计规格 v2

- 日期：2026-06-12（v2，替代被否决的"晨昏线切割"clip-path 方案）
- 状态：方案已获用户确认（canvas 粒子方向），实施中
- 用户核心要求：**用 canvas；把网页元素融进文字本身，而非把特效叠在文字上**。标题文字"辨伪求真"不换；副标题、按钮、信任行、REAL 水印不动。

## 1. 概念

产品在像素层面鉴定图片 → 标题本身就是一片**被检验的像素场**。"辨伪求真"由数千个粒子（检材像素）构成：

- **入场**＝从乱序像素中重组出真相（产品故事的开场白）
- **常态微抖**＝CMOS 传感器底噪（真照片的生命体征，我们检测的核心特征）
- **背景光弧扫过时字内粒子升温变金**＝晨昏线穿过文字内部（与背景共生，不是画在字上的线）
- **鼠标拨动粒子、松开复原**＝用放大镜检查像素，真相可被扰动但终会复位

## 2. 实现（新组件 ParticleTitle，替换 TerminatorTitle）

```
frontend/src/components/ParticleTitle.tsx   纯 2D canvas，零新依赖（~170 行）
frontend/src/app/page.tsx                   h1 内 TerminatorTitle → ParticleTitle
frontend/src/app/globals.css                删除整个 terminator-* 样式块
frontend/src/components/TerminatorTitle.tsx 中和为空 stub，物理删除进延迟队列
```

- **采样**：离屏 canvas 以 `600 {clamp(52, 10.5vw, 120)}px "PingFang SC"/"Microsoft YaHei"` 绘制文本，`getImageData` 按 3px 步长取 alpha>128 的点为粒子 home（预计 2500–4000 粒）。
- **粒子通道**：Float32Array（home/pos/vel/size/phase/warm/bright），无对象分配。
- **物理**：回家弹簧 k=0.075、速度阻尼 ×0.82；鼠标半径 90px 内按 (1-d/R) 推斥；底噪抖动在渲染层叠加（sin/cos 相位偏移 ±0.35px），不进物理。
- **光弧耦合**：lightX 以 14s 正弦往返扫掠，粒子按高斯距离（σ=70px）升温——颜色 冷蓝白 #9FC2FF → 暖金 #E0A368 插值，亮度 0.5→0.95，离光后慢冷却（升温快冷却慢的不对称，模拟物理热惯性）。
- **渲染**：`globalCompositeOperation: "lighter"` 方块粒子（fillRect），发光感与背景体系一致；DPR≤1.5。
- **生命周期**：IntersectionObserver 滚出视口暂停 rAF；resize 防抖 200ms 重采样；卸载全清理。

## 3. 无障碍与降级

- 真实文本放 `sr-only` span（h1 语义保留），canvas `aria-hidden`。
- `prefers-reduced-motion`：不跑动画循环，粒子直接归位渲染**一帧静态点阵文字**（仍保留质感，零运动）。
- canvas 不可用（极端情况）：sr-only 文本仍在，无白屏风险。

## 4. 验收

- `tsc --noEmit` 零错误；dev 截图确认粒子标题渲染、hero 其余元素不变；
- 体感检查项（用户验收）：入场汇聚 ~1s 内完成、底噪抖动"活着但不闹"、光弧扫过有暖金潮汐、鼠标拨动跟手、滚出视口后 CPU 归零。
