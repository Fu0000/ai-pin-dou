# 竞品分析 · 拼豆项目

```yaml
文档名: Competitive Analysis - 拼豆项目
版本: v0.3
最后更新: 2026-05-18
关联文档: guihua.md, project-plan.md, 01-prd.md, 04-system-architecture.md
关联 ADR: ADR-001, ADR-013, ADR-014, ADR-019, ADR-023, ADR-024
```

---

## 0. 这份文档的目的

> 系统性记录与拼豆项目存在直接/间接竞争关系的产品，提炼差异点与可借鉴点，为决策门评审和 PRD 迭代提供证据。

**收录原则**：
- 涵盖直接竞品（拼豆图纸生成器、AI 拼豆工具、拼豆电商）
- 间接竞品（DIY 礼物平台、定制电商）按需收录
- 每条记录至少包含：定位 / 功能矩阵 / 技术栈 / SEO / 商业模式 / 与拼豆的差异 / 可借鉴点 / 参考时点

---

## 1. 已收录竞品索引

| # | 名称 | 类型 | 战场 | 收录时间 | 完成度 |
|---|---|---|---|---|---|
| 1 | [perlerbeads.net](#1-perlerbeadsnet) | Web 工具站 | 国际多语种 | 2026-05-18 | ✅ 完整分析 + Lighthouse |

> 后续新增竞品按"## N. 名称"作为二级标题追加，并同步更新本表。

---

## 1. perlerbeads.net

### 1.1 基本信息

| 项 | 内容 |
|---|---|
| URL | https://perlerbeads.net |
| 域名注册商 / CDN | Cloudflare（HTTP 头 `server: cloudflare` + `cf-ray` 验证） |
| 一句话定位 | Free Online Perler Bead Pattern Designer — 把任意照片 100% 免费转为 Perler / Hama / Artkal 可打印图纸 |
| 主要用户 | 全球 DIY 拼豆爱好者（hreflang 覆盖 10 语种） |
| 商业模式 | 免费工具 + Google AdSense（pub-9110451004718141）+ Buy Me a Coffee 打赏 + `/pricing` 页（疑似有付费版，需要进一步验证） |
| 收录时间 | 2026-05-18 |

### 1.2 核心功能矩阵

| 功能 | 实现细节 | 与拼豆 MVP 对照 |
|---|---|---|
| 图片上传 | 拖拽 / 点击，JPG/PNG ≤ 10MB | 一致 |
| 示例图引导 | 3 张：Kitty / Mario / Before&After | M0 US-0.3 可借鉴"3 张克制式" |
| 算法 | 文案声明 Delta E（CIE Lab 距离）色号匹配 | 与 ADR-003 / 07-algo-spec.md 路径一致 |
| 智能抠图 | 顶部红 banner「✨ New: Smart background removal for precise material estimates」 | 与 PRD 抠图能力对齐 |
| 品牌色卡 | Perler / Hama / Artkal + 自定义 | MVP 仅 Mard（ADR-004），后续扩展 |
| 网格规格 | 10×10 ~ 100×100 任意调 | 拼豆 MVP 走 easy/normal/pro 情境化（ADR-024/025），意图相反 |
| 算料 | "Automatic Bead Counts" 每色号统计 | 一致；拼豆把算料推到供应链下单（差异化护城河） |
| 手动编辑 | 笔刷 / 填充 / 撤销重做 | 拼豆 ADR-019 改为风格变体（去工程化） |
| 导出 | PDF（含 material list）/ PNG | 一致 |
| 实时预览 | 调整明暗对比即看效果 | 一致 |

### 1.3 站点结构

```
/                    首页（图纸生成器入口）
/designer            交互式编辑器
/gallery             图纸画廊
/tutorials           教程
/showcase            作品展示
/pricing             定价（疑似付费版）
/contact             联系
/privacy-policy
/terms-of-service
```

× 10 语种（en / zh / es / de / ja / fr / pt / id / th / ru，共 154 条 sitemap URL）。

### 1.4 技术栈（从 HTTP 头 + HTML 推断）

| 层 | 证据 | 结论 |
|---|---|---|
| 前端框架 | `_next/static/chunks/...` + `x-powered-by: Next.js` + `[locale]` 路由文件名 | Next.js（App Router）+ next-intl |
| 部署 | `x-opennext: 1` + `server: cloudflare` + `cf-ray` | OpenNext + Cloudflare（Workers/Pages），全球边缘 |
| 渲染 | `x-nextjs-prerender: 1` + `x-nextjs-cache: MISS` + `cache-control: s-maxage=3600, stale-while-revalidate=31532400` | 静态预渲染 + ISR |
| 监控 | `googletagmanager.com/gtag/js?id=G-NCY7WCV5JF` | GA4 |
| 广告 | AdSense（pub-9110451004718141） | 主要变现 |
| 协议 | HTTP/2 + HTTP/3（alt-svc h3=":443"） | 现代 Web 性能 |
| HTML 体积 | 142KB（gzip 前），26 个 JS chunks，25 个 inline `<script>` | 中等偏重，但首屏 SSR 预渲染 |

### 1.5 SEO 评估

| 项 | 现状 | 评价 |
|---|---|---|
| Title | "PerlerBeads - Free Online Perler Bead Pattern Designer" | ✅ 包含核心关键词 + 价值 |
| Description | 写 "free 29x29 grid editor / 64 colors / 6 templates / export PNG" | ⚠️ 与正文（10×10~100×100、3 品牌色卡）不一致，应是早期文案没更新 |
| Keywords | perler beads, fuse beads, bead patterns, pixel art, craft, DIY, iron beads | ✅ 覆盖国际同义词 |
| Canonical | `https://perlerbeads.net` | ✅ |
| 多语言 hreflang | 10 语种 + x-default | ✅✅✅ 国际化最专业的部分 |
| Open Graph + Twitter Card | 完整 | ✅ |
| robots.txt | 屏蔽 GPTBot / ClaudeBot / Google-Extended / Bytespider 等 AI 爬虫 | ✅ "内容仅供搜索，不喂 AI" |
| Sitemap | 154 条 URL，每语种 14 个固定路径 | ✅ |
| favicon / icon | 有 | ✅ |

### 1.6 性能（Lighthouse + 真实加载数据）

> 测试时间：2026-05-18；模式：navigation；设备：desktop；网络/CPU：未限速。

**Lighthouse 分类得分**

| 类别 | 分数 | 评价 |
|---|---|---|
| Accessibility | 95 | ✅ 优秀 |
| Best Practices | 73 | ⚠️ 中等（含 1 个 button 缺 accessible name + 第三方 cookie + 控制台 errors） |
| SEO | 100 | ✅ 满分 |
| Agentic Browsing | 33 | ❌ 弱（多在 robots 屏蔽 AI 爬虫导致——刻意为之，非缺陷） |

> 注：本次 MCP Lighthouse 在 navigation 模式下不计算 Performance 分类，性能维度通过 Chrome DevTools 性能 trace 单独采集。

**核心 Web Vitals**

| 指标 | Lab（本机） | Field（CrUX 真实用户 p75） | 评价 |
|---|---|---|---|
| LCP（最大内容渲染） | 2.51s | 2.37s | 🟡 接近"良好"门槛 2.5s，多语种 hreflang + ISR 起作用 |
| CLS（累积布局偏移） | 0.00 | 0.03 | ✅ 几乎无偏移，Next.js 静态尺寸预定义到位 |
| INP（交互到下一次绘制） | — | 640ms | ❌ 真实用户 INP 很差（>500ms 算 Poor），首屏交互卡顿 |
| TTFB | 329ms（lab）/ 1224ms（field p75） | — | 真实用户 TTFB 高，Cloudflare 边缘 + ISR 但仍受 Worker/OpenNext 冷启动影响 |

**LCP 分解（lab）**

- TTFB: 329ms
- Load delay: 262ms
- Load duration: 1865ms（占比最大，主要是 LCP 图片下载）
- Render delay: 54ms

**关键性能问题**

1. **图片严重过度采样**——估算可省 **629.9 kB**：
   - HelloKitty.jpg 实际尺寸 1927×1927 但显示 92×92（多下了 276 kB）
   - Mario_Pattern.jpg 实际 1290×1290 但显示 92×92（多下了 204 kB）
   - Original.png 实际 500×500 显示 472×472，且没用 WebP/AVIF（多下了 149 kB）
   - **拼豆借鉴**：所有图纸预览图必须按渲染尺寸生成多档（next/image 的 `sizes` 配置）+ 强制 WebP/AVIF
2. **第三方脚本占用大量字节**：Google Ads 702 kB + GTM 478 kB + 其他 ≈ 35 kB —— 总计 **1.27 MB 第三方代码**，主要为广告模型托底
3. **缓存策略不够**——估算可省 **670.4 kB**（部分静态资源 cache 时间不够长）
4. **控制台有 JS error + 1 个 button 缺 aria-label** —— 小瑕疵
5. **CLS 0.00 / 0.03** —— 这是它做得最好的指标，Next.js + 预渲染功底扎实

**对拼豆的启示**

- 你的小程序内场景 LCP 受微信小程序运行时控制，不直接对标；但**官网/H5 落地页**（关联 §1.10 第 1 条）必须把首屏图严格按 `sizes` 出多档 + WebP/AVIF
- 第三方脚本总量必须管控，MVP 不引入 GTM/Ads，等 Phase 2 数据中台再上 GA4/百度统计
- INP 是它最痛的指标（640ms），原因大概率是 26 个 JS chunks 阻塞主线程；**你 Phase 4 出海做官网时，按 next-intl 路由切代码 + 严格 lazy load**
- **它的 Best Practices 73 分**给我们一个反例提示：广告对 BP 分扣很狠，拼豆变现靠商品而非广告，反而能更轻松拿满分

### 1.7 与拼豆项目的对比

| 维度 | perlerbeads.net | 拼豆 pin-dou MVP |
|---|---|---|
| 定位 | 免费 Web 工具，靠广告 + 打赏盈利 | C2M 定制电商，靠图纸+算料+一键下单+实物供应链盈利（关联 ADR-001/008） |
| 战场 | 国际多语种 Web | 中国微信 + 抖音小程序（关联 ADR-002/011） |
| 算法 | Delta E（CIE Lab）色号匹配 + 智能抠图 | 同样路径（关联 ADR-003 / 07-algo-spec.md），技术不构成壁垒 |
| 色卡 | Perler / Hama / Artkal 全开放 | MVP 仅 Mard，后续扩展（ADR-004） |
| 网格 | 10~100 任意 | easy/normal/pro 三档情境化（ADR-024/025） |
| 核心差异 | 工具到此为止——做完图纸用户就走了 | **算料→供应链→一键下单→签收推送→心流陪伴卡** 完整闭环（ADR-023/026/021） |
| 库存承诺 | 无 | ✅ 库存预占 30 分钟 TTL（ADR-023） |
| 送礼场景 | 无 | ✅ 微信小店送礼物（ADR-011） |
| 变现模型 | 广告（CPM 低）+ 打赏 | 客单 50~100 元 + 首单大礼包（ADR-008/020） |
| 国际化 | ✅ 10 语种 | ❌ MVP 仅中文 |
| 用户视角语言 | 仍偏工程（Delta E、64 colors） | ✅ 灵魂三句话刻意去技术化（ADR-013/024） |

### 1.8 值得借鉴的 5 件事

1. **多语言 hreflang 站点结构**——Phase 4 出海时直接抄这个 next-intl `[locale]` 路由 + sitemap 自动生成 hreflang 的做法
2. **首页 3 张示例图**（Kitty/Mario/Before&After）——M0 首屏 US-0.3 的"30 张真实案例图"清单可以效仿这种"3 张就能讲清楚价值"的克制设计
3. **OpenNext + Cloudflare 边缘部署**——出海后 Phase 4 的官网/H5 落地页可以直接用，0 运维全球加速。**注意**：和 ADR-027/ADR-028 阿里云 ECS 不冲突，因为这只是营销官网，不是 API 服务
4. **robots.txt 屏蔽 AI 爬虫**——拼豆的图纸数据是核心资产，立项时把这套 robots 配好
5. **`Smart background removal` 当成新 feature 重点宣传**——印证 PRD 把"自动抠图"当成核心卖点是正确的

### 1.9 它的 4 个明显短板（拼豆的差异化机会）

1. **没有闭环**——用户拿到图纸要自己采购豆子，颗数算了也没有"按算料一键加购"能力；这是拼豆 C2M 模式的核心护城河
2. **首页文案有 bug**——meta description 写 "29x29 grid / 64 colors / 6 templates"，正文写 "10×10 to 100×100 / Perler+Hama+Artkal" — 早期文案没更新被搜索引擎抓走了，提醒拼豆迭代时一定同步更新 meta
3. **完全没有用户体系**——"No Sign-up Required" 听起来好，其实意味着没法做留存 / 复购 / 老朋友 9 折（ADR-018/020）。拼豆要刻意保留弱登录（微信 openid）做留存
4. **变现天花板低**——广告 + 打赏的全球工具站典型困境，对比拼豆的客单 50~100 元 + 实物链路，单位用户价值差 ≥ 100 倍

### 1.10 对拼豆立项的 3 条具体建议

1. **官网/H5 落地页**：Phase 1 末考虑用同款 Next.js + Cloudflare 边缘方案做营销主页（与小程序生态互不冲突，关联 ADR-027 主体不变）
2. **国际化预留**：现在写 PRD/UI 时，文案 key 用英文标识符（不是直接写中文），后端 i18n schema 留 `locale` 字段。出海时不用大改
3. **不要去打 perlerbeads.net 这条路**：它的国际 SEO 流量打不过、也没必要打。拼豆的护城河在国内的"图纸→算料→定制下单→签收推送→心流陪伴"完整闭环，关联 ADR-013 三句话是它永远做不出来的

### 1.11 /designer 真实交互链路拆解（2026-05-18 实测）

> 通过 Chrome MCP 在线模拟"点 Kitty 示例 → 进入编辑器"完整流程，并分析网络面板 + DOM 结构。这是最有价值的技术情报。

**核心发现：算法 100% 跑在浏览器端**

- 从首页点 Kitty 跳到 `/designer` 加载示例图后，**XHR/Fetch 列表里零业务接口调用**（只有 GA / Cloudflare RUM / 静态资源）
- 整个抠图、像素化、色号匹配（Delta E）、算料统计**全部在浏览器 JS 里完成**
- 没有 WebAssembly（`.wasm` 文件 0 个）、没有 ONNX/TFLite 模型文件
- "Smart background removal" 大概率是用 canvas 边缘色阈值或固定背景色法做的近似抠图，不是语义抠图

**渲染方式：DOM 暴力**

- 88×88 网格 = **7744 个 `<div>` 直接渲染**（单元格用 CSS grid + gap-px）
- 整页 DOM 节点 **8151 个**，远超 Lighthouse 警告阈值（>1500 即扣 BP 分）
- **没有 `<canvas>`**——选择 DOM 是为了让单格点击 / 鼠标拖拽编辑变简单，但代价是 INP 640ms（关联 §1.6）
- JS 堆内存仅 20 MB，不算大，瓶颈不在内存而在主线程渲染

**色卡数据**：默认调出 34 色 / 1714 颗豆（88×88 网格、Kitty 示例），色号编码 `A1` / `D16` / `I1` 等（看起来是它自己的字母+数字编码体系，未直接对照 Perler 官方色号）。

**对拼豆的关键启示**

| 拼豆决策 / 现状 | 对照 perlerbeads.net /designer | 拼豆的差异化机会 |
|---|---|---|
| 算法在 ECS 容器（ADR-028） | 它是纯前端 JS | 拼豆的 Python + OpenCV/rembg 算法质量上限远高于浏览器 JS（真正语义抠图、CIE Lab 精确匹配、缺货色 Lab 替换） |
| 图纸预览推荐用 canvas 而非 DOM grid | 它用 7744 个 div | **PRD 必须明确**：32×32 / 48×48 网格用 canvas 渲染，避免 DOM 爆炸 |
| 服务端算料 + 一键加购 | 它算完就走，无下单链路 | 这是核心护城河，无法被它复刻（它的浏览器 JS 拿不到供应链库存） |
| 库存预占 30min（ADR-023） | 它无库存概念 | 同上 |
| 灵魂三句话去技术化（ADR-013/024） | 它直接给 "A1" "D16" 这种工程编码 | 拼豆 ADR-024 难度档情境化命名是正确路线 |

**有潜在风险的对照点**

- 它的"零延迟"体验真实存在（点 Kitty 后立即出 1714 颗 / 34 色 / 完整图纸面板）
- 拼豆走服务端算法 + Serverless / ECS 调用，**网络往返 + 算法处理本身**会比纯前端慢
- 这强化了 ADR-014 算法可行性预实测（M0 阻塞项）的重要性：**P95 ≤ 10s 是底线，不是目标**
- 拼豆要补回的"流畅感"靠：① 上传后立即 loading 占位 ② 风格变体并行预生成（ADR-019）③ 后续切换零延迟

---

## 2. 变更日志

| 日期 | 版本 | 变更 | 备注 |
|---|---|---|---|
| 2026-05-18 | v0.1 | 初始化竞品分析文档；新增 perlerbeads.net 完整分析（性能数据待 Lighthouse 跑完补全 §1.6） | 关联 ADR-001 / ADR-013 |
| 2026-05-18 | v0.2 | §1.6 补全 Lighthouse + 性能 trace 数据：A11y 95 / BP 73 / SEO 100 / Agentic 33；LCP 2.51s lab · 2.37s field；INP 640ms（差）；CLS 0；图片可省 629.9 kB；第三方代码 1.27 MB | — |
| 2026-05-18 | v0.3 | 新增 §1.11 /designer 真实交互链路拆解：发现算法 100% 跑浏览器端（零业务接口调用 / 无 WASM / 无 ONNX）+ 88×88 网格用 7744 个 div 渲染（DOM 节点 8151）→ 强化 ADR-014 重要性 + 拼豆图纸预览必须用 canvas | — |
