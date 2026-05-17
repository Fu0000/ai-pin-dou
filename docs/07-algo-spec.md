# 算法工程规范 · 拼豆小程序 v0.1

```yaml
文档名: Algorithm Engineering Spec - 拼豆小程序
版本: v0.1（骨架）
最后更新: 2026-05-17
关联文档: 04-system-architecture.md / 05-data-model.md / 06-api-spec.md
关联 ADR: ADR-003（算法封装策略）/ ADR-004（色卡优先级）
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

> ⚠️ **任何 `minor` 及以上变更，必须先跑回归测试集（见 §5）**，再上线。

### 2.3 版本变更必须立 ADR

凡修改导致**像素矩阵输出可能不同**的变更，都必须：
1. 在 `/decision-log.md` 立 ADR（哪怕只是单人）
2. 记录回归测试结果（通过率、退化样本）
3. 灰度发布（先 10% 流量，48 小时观察）

---

## 3. 各模块技术约定

### 3.1 ① Preprocess

| 项 | 约定 |
|---|---|
| 输入限制 | JPG/PNG，≤ 10MB，最小 256×256 |
| EXIF 处理 | 强制旋转修正（避免手机竖拍变横） |
| 尺寸归一化 | 长边 resize 到 1024，保持比例 |
| 色彩空间 | 强制 sRGB，剔除 CMYK/灰度图 |

### 3.2 ② Cutout 抠图

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

### 3.3 ③ Pixelize 降采样

| 难度档 | 网格规格 | 重采样算法 |
|---|---|---|
| easy | 16×16 / 32×32 | LANCZOS（保细节） |
| normal | 32×32 / 48×48 | LANCZOS |
| pro | 64×64+ | LANCZOS |

> 不允许用 NEAREST 或 BILINEAR——会损失细节或产生模糊。

### 3.4 ④ Quantize 色彩量化

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

### 3.5 ⑤ ColorMap 色号映射

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

### 3.6 ⑥ Constraint 库存约束

| 状态 | 处理 |
|---|---|
| `available` | 直接使用 |
| `low` | 优先使用，但若该色占比 > 30% 则降级（避免低库存被一单清空） |
| `oos` | 必须用 CIE Lab 最近邻替换 |

**用户提示规则**：
- 替换数量 / 总色数 ≤ 10%：静默处理
- 11% ~ 20%：弱提示「已优化 X 个色号」
- > 20%：强弹窗「建议改为 X 档难度，效果更好」

### 3.7 ⑦ Outline 描边

```python
def add_outline(pattern: ndarray, threshold: int = 30) -> ndarray:
    """主体边缘检测后，将边缘像素替换为最深色"""
    edges = cv2.Canny(pattern, threshold, threshold * 2)
    pattern[edges > 0] = darkest_color_in_palette(pattern)
    return pattern
```

> **easy 档默认开启，pro 档默认关闭**（专业用户自己控制）。

### 3.8 ⑧ Calculate 算料

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

## 4. 性能预算（P95）

| 模块 | 时间预算 | 备注 |
|---|---|---|
| ① Preprocess | ≤ 0.3s | 同步 |
| ② Cutout | ≤ 3s | 异步，最耗时 |
| ③ Pixelize | ≤ 0.5s | 同步 |
| ④ Quantize | ≤ 1.5s | k=40 时 |
| ⑤ ColorMap | ≤ 0.5s | 缓存命中 |
| ⑥ Constraint | ≤ 0.2s | 内存计算 |
| ⑦ Outline | ≤ 0.3s | 同步 |
| ⑧ Calculate | ≤ 0.1s | 同步 |
| **端到端 P95** | **≤ 10s** | M1 决策门硬指标 |

---

## 5. 回归测试集（必须有）

### 5.1 测试集组成

`/algo/regression/` 目录下维护 100 张样图，按类别分布：

| 类别 | 数量 | 用途 |
|---|---|---|
| 人像（自拍） | 25 | P1 主场景 |
| 宠物（猫狗） | 25 | P1 高频场景 |
| 风景 | 15 | 复杂背景 |
| 卡通插画 | 15 | 简单色块 |
| 物品（咖啡/食物） | 10 | 长尾 |
| 边缘 case（暗光、纯色背景、纯文字、超大图） | 10 | 鲁棒性 |

### 5.2 自动化回归脚本

```bash
# 每次算法版本升级前必跑
python algo/regression/run.py --version algo-v1.1.0

# 输出：
# - 每张图的像素矩阵 hash 对比上一版本
# - 算料数量对比
# - 处理耗时分布
# - 质量评分（与基线相比）
```

### 5.3 通过标准

| 维度 | 通过线 |
|---|---|
| 处理成功率 | 100% |
| P95 耗时 | ≤ 10s |
| 人工评分优良率 | ≥ 75%（M1 决策门指标） |
| 与上一版本相比退化样本 | ≤ 5% |

---

## 6. 算法降级与故障处理

| 故障 | 降级方案 |
|---|---|
| rembg 服务超时 | 自动切到 OpenCV grabCut |
| K-Means 不收敛 | 降级为简单分位数量化 |
| Mard 色卡 API 全挂 | 用 Redis 缓存版（接受 24h 滞后） |
| Serverless 冷启动慢 | 前端展示"AI 设计中（约 30 秒）"，调高用户预期 |
| 算法整体失败 | 用户可手动调整参数重试，最多 3 次免费重生成 |

---

## 7. 算法实验工作流（单人版）

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

## 8. 关键依赖与版本锁定

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

## 9. 待补完成项

- [ ] 每个模块的完整代码骨架 + 单元测试
- [ ] 100 张回归测试集（实际收集）
- [ ] 算法 A/B 实验框架（Phase 3）
- [ ] LED 指令生成模块（Phase 3 IoT）
- [ ] 算法可解释性工具（向用户展示"为什么是这个色号"）

---

## 10. 变更日志

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-05-17 | v0.1 | 初始化算法工程规范，建立 8 步管线 + 版本管理基线 |
