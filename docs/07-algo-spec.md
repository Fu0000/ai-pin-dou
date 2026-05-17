# 算法工程规范 · 拼豆小程序 v0.5

```yaml
文档名: Algorithm Engineering Spec - 拼豆小程序
版本: v0.5（风格变体分支 + 推荐预分析 + M0 阻塞门）
最后更新: 2026-05-17
关联文档: 04-system-architecture.md, 05-data-model.md, 06-api-spec.md
关联 ADR: ADR-003, ADR-004, ADR-014, ADR-019, ADR-023, ADR-024, ADR-025
```

---

## 0. 文档说明

> 算法是拼豆项目的**核心护城河**之一（关联 ADR-003）。  
> 但单人项目没有专职算法团队，必须用工程化手段保证：
> - **可复现**：每次生成结果在同一参数下稳定一致
> - **可回归**：算法迭代不能让旧样本质量回退
> - **可降级**：上游 lib 出问题时有 Plan B
> - **可解释**：未来回看时知道当时为什么这么调参

---

## 1. 算法管线总览

### 1.1 8 步主管线

```
[原始图片]
    │
    ▼
[① Preprocess 预处理]  ── EXIF 旋转 / 尺寸归一化 / 色彩空间转换
    │
    ▼
[② Cutout 抠图]        ── rembg / OpenCV grabCut
    │
    ▼
[③ Pixelize 降采样]    ── 网格规格 16/32/48/64
    │
    ▼
[④ Quantize 量化]      ── K-Means 色彩聚类（按难度档限色数）
    │
    ▼
[⑤ ColorMap 色号映射]  ── CIE Lab 最近邻 → Mard 色卡
    │
    ▼
[⑥ Constraint 库存约束]── 缺货色号自动替换为可售近似色
    │
    ▼
[⑦ Outline 描边]       ── 主体边缘自动加深色描边（防散架）
    │
    ▼
[⑧ Calculate 算料]     ── 颗粒数统计 + SKU 列表生成
    │
    ▼
[输出]
   ├── pattern_data: [[color_id,...]]   像素矩阵
   ├── color_summary: {color_id: count} 算料清单
   ├── preview_image_url                 预览图
   └── physical_size_cm                  实物尺寸
```

### 1.2 风格变体生成分支（关联 ADR-019）

> Quantize 完成后**并行**分叉到 3 套风格变体生成任务，预写入对象存储与 `patterns.pattern_data.style_variants`，供 `POST /patterns/{id}/style-variants` 接口零延迟读取（关联 06-api-spec.md §4.3）。

```
     ┌──────────────┐
     │ ④ Quantize   │
     └─────┬────────┘
           │
           ├─► ⑤a ColorMap → ⑥ Constraint → ⑦ Outline → ⑧ Calculate（主线）
           │
           └─► ⑤b StyleVariant Branch（并行 3 个 task）
                 ├─ Realistic 变体（默认）
                 ├─ Pixel 变体
                 └─ Cartoon 变体
                       │
                       ▼
                 [对象存储 patterns/{id}/variants/{style}.png + pattern_data.style_variants]
```

**输出**：每张图纸生成时同步产出 3 个变体预览图（写实 / 像素艺术 / 卡通）。
**性能预算**：3 个变体并行执行，端到端总耗时不超过主线 P95 + 2s（关联 §6 性能与质量门）。
**用户体验**：用户在预览页切换风格变体时**不重算**，直接读对象存储；详见 04-system-architecture.md §2.7。

---

## 2. 算法版本管理（核心）

### 2.1 版本号规则

```
algo-v<major>.<minor>.<patch>

例：
algo-v1.0.0   MVP 首发版
algo-v1.0.1   Bug 修复（不影响输出）
algo-v1.1.0   参数调整（可能改变输出）
algo-v2.0.0   重大变更（如换核心库）
```

### 2.2 写入数据库的字段

每张图纸生成时必须记录算法版本：

```sql
patterns.algo_version VARCHAR(16)  -- 'algo-v1.0.0'
```

> ⚠️ **任何 `minor` 及以上变更，必须先跑回归测试集（见 §7）**，再上线。

### 2.3 版本变更必须立 ADR

凡修改导致**像素矩阵输出可能不同**的变更，都必须：
1. 在 `/decision-log.md` 立 ADR（哪怕只是单人）
2. 记录回归测试结果（通过率、退化样本）
3. 灰度发布（先 10% 流量，48 小时观察）

---

## 3. 推荐档位预分析模块（关联 ADR-024 / ADR-025）

> "零智商税"灵魂落地：用户上传后系统自动判断推荐档位，免去用户在 3 档间纠结。失败时回退「摆件经典」。

### 3.1 输入特征

| 特征 | 计算方式 | 用途 |
|---|---|---|
| 颜色多样性 | K-Means 试探 (K=32) 后的非空簇数 | 复杂度近似 |
| 边缘密度 | Canny 边缘像素 / 总像素 | 主体细节密度 |

```python
def precompute_difficulty_features(image: PIL.Image) -> dict:
    """轻量预分析：颜色多样性 + 边缘密度，耗时 ≤ 0.3s"""
    arr = np.asarray(image.convert("RGB"))
    # 颜色多样性
    pixels = arr.reshape(-1, 3)
    kmeans = KMeans(n_clusters=32, n_init=3, max_iter=20, random_state=42)
    kmeans.fit(pixels[::100])  # 1% 抽样以加速
    color_diversity = len(np.unique(kmeans.labels_))
    # 边缘密度
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    edge_density = edges.sum() / 255 / edges.size
    return {"color_diversity": color_diversity, "edge_density": edge_density}
```

### 3.2 阈值草案

| 推荐档 | 显示名（用户侧）| 触发条件 |
|---|---|---|
| `easy` | 萌宠 mini | `color_diversity < 10` |
| `normal` | 摆件经典 | `10 ≤ color_diversity ≤ 25` 且 `edge_density ≤ 0.15` |
| `pro` | 装饰挂画 | `color_diversity > 25` 或 `edge_density > 0.15` |

> 阈值在 W0~W2 算法实测期（关联 §6 M0 阻塞门）持续校准。

### 3.3 失败回退策略

预分析超时 (> 0.5s) 或异常 (`KMeans` 不收敛 / 图像解码失败) → **回退到「摆件经典」(`normal`)，不报错给用户**。
日志记录 `recommend.fallback` 事件，用于运营观测推荐准确率。

---

## 4. 色号映射 ↔ 库存预占衔接（关联 ADR-023）

> 算法侧 `⑤ ColorMap` 与 `⑥ Constraint` 与后端库存预占模块（04-system-architecture.md §2.5）的握手约定。

### 4.1 数据流

```
[Quantize 输出簇心]
        │
        ▼
[⑤ ColorMap] ── 拉取 colors 表 + Redis sku:stock 缓存（最新可售色号集合）
        │
        ▼
[⑥ Constraint] ── 缺货色号用 CIE Lab Delta-E 替换，最多 1 次
        │
        ▼
[BizSvc 调用 POST /inventory/reserve（30 min TTL）]
        │
        ▼
[支付成功 → 转正式扣减 / 失败 → release]
```

### 4.2 关键约定

- **算法 ⑤ Quantize 阶段必须使用「最新可售色号集合」**（`bead_skus.stock_status IN ('available','low')`），避免预占阶段才发现色号下架导致整单回滚。
- **同色系替换**：缺货色号走 CIE Lab 最小色差替换，最多 1 次（避免链式替换偏离主色调）。
- **预占失败回滚**：若 reserve 返回 `30100 INVENTORY_INSUFFICIENT`，算法自动用替换色号重跑 `⑥ Constraint` + 再次 reserve，最多 2 轮，再失败提示用户「这张图比较复杂，建议改用 [推荐档] 档」。

---

## 5. 各模块技术约定

### 5.1 ① Preprocess

| 项 | 约定 |
|---|---|
| 输入限制 | JPG/PNG，≤ 10MB，最小 256×256 |
| EXIF 处理 | 强制旋转修正（避免手机竖拍变横） |
| 尺寸归一化 | 长边 resize 到 1024，保持比例 |
| 色彩空间 | 强制 sRGB，剔除 CMYK/灰度图 |

### 5.2 ② Cutout 抠图

| 项 | 约定 |
|---|---|
| 主选 | `rembg` (u2net) — 复杂背景效果好 |
| 备选 | OpenCV `grabCut` — 简单背景，速度快 |
| 失败兜底 | 不抠，直接进入 ③（用户可手动修） |
| 性能预算 | P95 ≤ 3s |

```python
# 伪代码
def cutout(image: PIL.Image, mode: str = 'auto') -> PIL.Image:
    """
    mode: 'auto' | 'rembg' | 'grabcut' | 'none'
    返回带 alpha 通道的图，背景透明
    """
    ...
```

### 5.3 ③ Pixelize 降采样

| 难度档 | 网格规格 | 重采样算法 |
|---|---|---|
| easy | 16×16 / 32×32 | LANCZOS（保细节） |
| normal | 32×32 / 48×48 | LANCZOS |
| pro | 64×64+ | LANCZOS |

> 不允许用 NEAREST 或 BILINEAR——会损失细节或产生模糊。

### 5.4 ④ Quantize 色彩量化

| 难度档 | 最大色数 | 算法 |
|---|---|---|
| easy | 8 | K-Means (k=8) |
| normal | 20 | K-Means (k=20) |
| pro | 40 | K-Means (k=40) |

**关键参数**：
```python
KMeans(
    n_clusters=k,
    init='k-means++',
    n_init=10,           # 多次初始化取最优
    max_iter=100,
    random_state=42      # ⭐ 必须固定，保证可复现
)
```

> ⚠️ `random_state=42` 是**复现性的命脉**，禁止改动除非升 minor 版本。

### 5.5 ⑤ ColorMap 色号映射

| 项 | 约定 |
|---|---|
| 距离度量 | **CIE Lab Delta-E**（不用 RGB 欧氏距离） |
| 色卡来源 | `colors` 表 + Redis 缓存 |
| 实时性 | 库存状态 ≤ 60s 滞后可接受 |

```python
def find_nearest_color(target_lab: tuple, palette: list[Color]) -> Color:
    """从 palette 中找 Delta-E 最小的色号"""
    return min(palette, key=lambda c: delta_e_cie2000(target_lab, c.lab))
```

### 5.6 ⑥ Constraint 库存约束

| 状态 | 处理 |
|---|---|
| `available` | 直接使用 |
| `low` | 优先使用，但若该色占比 > 30% 则降级（避免低库存被一单清空） |
| `oos` | 必须用 CIE Lab 最近邻替换 |

**用户提示规则**：
- 替换数量 / 总色数 ≤ 10%：静默处理
- 11% ~ 20%：弱提示「已优化 X 个色号」
- > 20%：强弹窗「建议改为 X 档难度，效果更好」

### 5.7 ⑦ Outline 描边

```python
def add_outline(pattern: ndarray, threshold: int = 30) -> ndarray:
    """主体边缘检测后，将边缘像素替换为最深色"""
    edges = cv2.Canny(pattern, threshold, threshold * 2)
    pattern[edges > 0] = darkest_color_in_palette(pattern)
    return pattern
```

> **easy 档默认开启，pro 档默认关闭**（专业用户自己控制）。

### 5.8 ⑧ Calculate 算料

```python
def calculate_summary(pattern: ndarray) -> dict[int, int]:
    """统计每个 color_id 的颗粒数"""
    unique, counts = np.unique(pattern, return_counts=True)
    return dict(zip(unique.tolist(), counts.tolist()))


def calculate_skus(summary: dict, safety_buffer: float = 0.10) -> list[OrderItem]:
    """
    将颗粒数转换为 SKU 采购清单
    safety_buffer: 安全冗余（默认 +10% 防丢失）
    """
    items = []
    for color_id, count in summary.items():
        sku = get_sku_by_color(color_id)
        adjusted_count = int(count * (1 + safety_buffer))
        pack_qty = math.ceil(adjusted_count / sku.pack_size)
        items.append(OrderItem(sku_id=sku.id, quantity=adjusted_count, pack_quantity=pack_qty))
    return items
```

---

## 6. 性能与质量门（关联 ADR-014）

### 6.1 M0 阻塞门（开干门槛）

> Phase 1 启动前必须用 Jupyter 跑 100 张真实样图实测；不过则 MVP 推迟、先调算法。

| 指标 | 阈值 | 备注 |
|---|---|---|
| 样本规模 | 100 张真实图（猫 / 人脸 / 宠物 / 风景 各 25 张）| 关联启动 Checklist 第 1 项 |
| 端到端 P95 耗时 | ≤ 10 秒 | 包含 ① Preprocess ~ ⑧ Calculate 全管线 + 风格变体并行（§1.2）|
| 人工评分优良率 | **≥ 60%**（M0 开干门槛）| 主观打分：5 分制 ≥ 3 分视为优良 |

### 6.2 M1 决策门（上线指标）

| 模块 | 时间预算 | 备注 |
|---|---|---|
| ① Preprocess | ≤ 0.3s | 同步 |
| ② Cutout | ≤ 3s | 异步，最耗时 |
| ③ Pixelize | ≤ 0.5s | 同步 |
| ④ Quantize | ≤ 1.5s | k=40 时；之后并行分叉到 §1.2 风格变体 |
| ⑤ ColorMap | ≤ 0.5s | 缓存命中 |
| ⑥ Constraint | ≤ 0.2s | 内存计算 + 库存预占握手（§4）|
| ⑦ Outline | ≤ 0.3s | 同步 |
| ⑧ Calculate | ≤ 0.1s | 同步 |
| 风格变体（并行）| ≤ 2s | 3 个 task 并行（§1.2）|
| **端到端 P95** | **≤ 10s** | M1 决策门硬指标 |

| 维度 | 通过线 |
|---|---|
| 处理成功率 | 100% |
| P95 耗时 | ≤ 10s |
| **人工评分优良率** | **≥ 75%**（M1 决策门）|
| 与上一版本相比退化样本 | ≤ 5% |

---

## 7. 回归测试集（必须有）

### 7.1 测试集组成

`/algo/regression/` 目录下维护 100 张样图，按类别分布：

| 类别 | 数量 | 用途 |
|---|---|---|
| 人像（自拍） | 25 | P1 主场景 |
| 宠物（猫狗） | 25 | P1 高频场景 |
| 风景 | 15 | 复杂背景 |
| 卡通插画 | 15 | 简单色块 |
| 物品（咖啡/食物） | 10 | 长尾 |
| 边缘 case（暗光、纯色背景、纯文字、超大图） | 10 | 鲁棒性 |

### 7.2 自动化回归脚本

```bash
# 每次算法版本升级前必跑
python algo/regression/run.py --version algo-v1.1.0

# 输出：
# - 每张图的像素矩阵 hash 对比上一版本
# - 算料数量对比
# - 处理耗时分布
# - 质量评分（与基线相比）
```

### 7.3 通过标准

| 维度 | 通过线 |
|---|---|
| 处理成功率 | 100% |
| P95 耗时 | ≤ 10s |
| 人工评分优良率 | ≥ 75%（M1 决策门指标） |
| 与上一版本相比退化样本 | ≤ 5% |

---

## 8. 算法降级与故障处理

| 故障 | 降级方案 |
|---|---|
| rembg 服务超时 | 自动切到 OpenCV grabCut |
| K-Means 不收敛 | 降级为简单分位数量化 |
| Mard 色卡 API 全挂 | 用 Redis 缓存版（接受 24h 滞后） |
| Serverless 冷启动慢 | 前端展示"AI 设计中（约 30 秒）"，调高用户预期 |
| 算法整体失败 | 用户可手动调整参数重试，最多 3 次免费重生成 |
| 推荐档位预分析超时 / 异常 | 回退到「摆件经典」(`normal`)，不报错给用户（关联 §3.3）|

---

## 9. 算法实验工作流（单人版）

由于是单人项目，没有完整的 ML 实验平台，按下面流程跑：

```
1. 在 jupyter notebook 调参，跑 10 张样图看效果
        ↓
2. 满意后写到 algo/v_next/ 目录
        ↓
3. 跑完整 100 张回归测试
        ↓
4. 通过 → 立 ADR → 升 algo 版本号 → 灰度上线
   不通过 → 回到 step 1
```

> **不要直接改线上 algo 模块**，每次都用新目录，方便回滚。

---

## 10. 关键依赖与版本锁定

```toml
# pyproject.toml （算法相关依赖）
[project]
dependencies = [
  "opencv-python==4.10.0.84",    # 不轻易升级
  "rembg==2.0.59",
  "scikit-learn==1.5.2",
  "numpy==2.1.3",
  "Pillow==11.0.0",
  "colormath==3.0.0",            # CIE Lab Delta-E
]
```

> 任何依赖升级必须跑回归测试，不允许直接 `pip install -U`。

---

## 11. 待补完成项

- [ ] 每个模块的完整代码骨架 + 单元测试
- [ ] 100 张回归测试集（实际收集）
- [ ] 算法 A/B 实验框架（Phase 3）
- [ ] LED 指令生成模块（Phase 3 IoT）
- [ ] 算法可解释性工具（向用户展示"为什么是这个色号"）

---

## 12. 灵魂三句话锚点

> 拼豆产品灵魂三句话（关联 ADR-013）：
> 1. 零智商税
> 2. 把感情做成礼物
> 3. 在心流中找回自我
>
> 本文档关键算法决策与三句话的对应关系如下，逐条接受未来重大改动的"反查"。

| # | 设计 / 决策点 | 对应灵魂 | 一句话理由（≤ 40 字） |
|---|---|---|---|
| 1 | 推荐档位预分析自动选档（§3） | 零智商税 | 系统帮你选好，不让用户做技术决策 |
| 2 | 风格变体并行预生成 3 套（§1.2） | 把感情做成礼物 | 给礼物多选项，让用户挑感觉 |
| 3 | M0 阻塞门 P95 ≤ 10s（§6.1） | 在心流中找回自我 | 等待不打断决策，10s 是心流上限 |
| 4 | 色号映射 ↔ 库存预占衔接（§4） | 零智商税 | 算法不让用户为缺货回滚买单 |
| 5 | 预分析失败回退「摆件经典」（§3.3） | 零智商税 | 即使算法失败也不报错给用户 |

---

## 13. 变更日志

| 日期 | 版本 | 变更 | 备注 |
|---|---|---|---|
| 2026-05-17 | v0.1 | 初始化算法工程规范，建立 8 步管线 + 版本管理基线 | — |
| 2026-05-17 | v0.5 | 新增 §1.2 风格变体生成分支 + §3 推荐档位预分析（颜色多样性 + 边缘密度 + 失败回退「摆件经典」）+ §4 色号映射 ↔ 库存预占衔接 + §6 性能与质量门（M0 阻塞门 100 张样图 P95 ≤ 10s + 优良率 ≥ 60%；M1 决策门 ≥ 75%）+ 灵魂三句话锚点 | 关联 ADR-014, ADR-019, ADR-023, ADR-024, ADR-025 |
