# M0 算法可行性预实测 · Dry-Run 报告

```yaml
报告: M0 Dry-Run Report
版本: v0.1
执行时间: 2026-05-18
执行者: Kiro（AI 代理）
实测机器: macOS (darwin) · Apple Silicon · Python 3.12.3
关联文档: docs/07-algo-spec.md §6.1, decision-log.md ADR-014, ADR-028
样本: 100 张程序合成图（4 类 × 25 张）
```

---

## ⚠️ 本报告的边界

**这是 dry-run，不是 ADR-014 的最终判定。**

本次实测使用程序生成的合成图（几何块 / 软斑点 / 多色斑点 / 加噪斑点），目的是：
1. 验证 8 步管线端到端可执行
2. 量化每步耗时分布与内存峰值
3. 识别性能瓶颈
4. 为 ECS 资源预算提供依据（关联 ADR-028 §4.4 回切阈值）

**最终 M0 通过判定**仍按 [`docs/07-algo-spec.md §6.1`](../docs/07-algo-spec.md) 要求：100 张**真实**照片 + 人工评分 ≥ 60% 优良率。

---

## 1. 执行摘要

| 指标 | with_cutout · grid=48 · 24 色（推荐基线）| 目标 | 结果 |
|---|---|---|---|
| 100 张全部成功率 | 100/100 | 100% | ✅ |
| P50 端到端耗时 | 0.316 s | — | — |
| **P95 端到端耗时** | **0.402 s** | **≤ 10.0 s** | ✅ 25× 余量 |
| P99 端到端耗时 | 0.433 s | — | — |
| 总跑通耗时 | 33.6 s（100 张串行）| — | — |
| 内存峰值（rembg 模型加载后）| +222 MB | < 2 GB（algo 容器上限）| ✅ |

**初步结论**：在合成图条件下，8 步管线性能远超 ADR-014 阈值。但因合成图过度友好（rembg 把大部分背景识别为背景导致前景过小），**质量维度无效**，必须用真实样本复跑。

---

## 2. 性能瓶颈

cutout（rembg/u2netp）占了 ~75% 总耗时。其他 7 步加起来 < 100 ms。

### 2.1 各步骤 P95 耗时（with_cutout · grid=48）

| 步骤 | P95 (ms) | 占比 |
|---|---|---|
| preprocess | 14.5 | 3.6% |
| cutout | **333.6** | **83.0%** |
| pixelize | 1.1 | 0.3% |
| quantize | 46.6 | 11.6% |
| color_map | 22.2 | 5.5% |
| outline | 1.1 | 0.3% |
| calculate | 0.1 | 0% |

### 2.2 三组配置对照

| 配置 | P50 / P95 / P99 (s) | smoothness (Lab) |
|---|---|---|
| with_cutout · grid=48 · 24 色（**推荐 normal 档**）| 0.316 / 0.402 / 0.433 | 28.4 |
| **no_cutout** · grid=48 · 24 色（消融）| 0.095 / 0.113 / 0.133 | 29.7 |
| with_cutout · grid=64 · 32 色（**接近 pro 档**）| 0.361 / 0.415 / 0.507 | 29.7 |

> 关掉 cutout 后耗时降到 ~0.1s，验证了 cutout 是瓶颈。grid 从 48 升到 64 + 色数从 24 升到 32 几乎没影响，说明 K-Means + color_map 在这个量级下不是瓶颈。

---

## 3. 各类样本表现（with_cutout · grid=48）

| 类别 | 样本数 | P95 (s) | 中位色数 | smoothness (Lab) |
|---|---|---|---|---|
| geo（几何块）| 25 | 0.329 | 6 | 21.2 |
| blob（软斑点）| 25 | 0.319 | 4 | 28.4 |
| complex（多色斑点）| 25 | 0.352 | 14 | 32.9 |
| noisy（加噪斑点）| 25 | 0.439 | 13 | 32.3 |

> noisy 类略慢，是因为 rembg 在噪声图上耗时略长。但仍远低于阈值。

---

## 4. 内存与资源行为（关联 ADR-028）

- 第 1 张：rss +222 MB（rembg 模型 u2netp.onnx ~4.6 MB 下载 + 加载到内存）
- 第 2 张起：rss +0 MB（模型已缓存）
- 模型缓存路径：`~/.u2net/u2netp.onnx`
- **结论**：algo-api 容器在 docker-compose 中设 `mem_limit: 4g` / `cpus: 2` 完全足够（关联 [`docs/04-system-architecture.md §4.2`](../docs/04-system-architecture.md)）。

---

## 5. 关键发现

### ✅ 系统层面已验证

1. **管线打通**：8 步管线 100/100 零失败
2. **Mard 色卡可用**：从 `maxcleme/beadcolors` 拉到 291 色，用 CSV 自带 Lab 值精度更高
3. **CIE Lab 路径正确**：color_map p95 仅 22 ms，纯 numpy 向量化够用，无需 GPU
4. **rembg u2netp 选型恰当**：模型小（4.6 MB）、内存占用低，跑得快，符合 ADR-028 内存预算

### ⚠️ 真实样本必须复跑的原因

合成图对算法太友好，验证不了核心场景：

| 维度 | 合成图表现 | 真实图风险 |
|---|---|---|
| rembg 抠图质量 | 在合成图上把 80% 区域识别为背景（误判）| 真实人脸/宠物会更准但耗时上升 |
| 噪声鲁棒性 | 合成噪声 Gaussian σ=20-40，真实手机噪声更复杂 | 真实暗光照片可能让 quantize 出现脏色 |
| 光照变化 | 合成图无真实阴影 | 真实图阴影会被算法识别为色块 |
| 主体边缘 | 合成边缘绝对清晰 | 真实图毛发/羽毛边缘会让 outline 步骤产生瑕疵 |
| 色彩动态范围 | 合成图色域饱满 | 真实图灰度部分多，可能让 K-Means 聚类成"灰糊一片" |

### ⚠️ 已知限制（不影响 dry-run 通过）

- `outline` 步骤是 Python 双层循环，未向量化。在 grid=64 上 P95 仅 2.1 ms，可接受；grid > 100 时需要重写为 numpy（相关 TODO 已记入 [`docs/07-algo-spec.md`](../docs/07-algo-spec.md)）。
- 风格变体生成分支（ADR-019）在本次 dry-run 未启用——主线还没实现，这是 W1 的事。
- 库存约束步骤（⑥ Constraint，关联 ADR-023）跳过——MVP W1 才接 RDS。

---

## 6. 给 W1 的具体建议

1. **algo-api 容器内存上限设 2 GB 即可**（不是 4 GB），rembg 实测占用 ~250 MB，留足缓冲（关联 ADR-028）
2. **冷启动需预热**：第 1 次调用 7+ 秒，后续 < 0.5s。生产环境 docker-compose 启动时应在 health check 阶段触发一次空跑预热
3. **K-Means 已用 MiniBatchKMeans**，不需要进一步优化
4. **color_map 向量化已到位**，291 × 7744 距离矩阵在 22 ms 内算完，无需 KD-Tree
5. **outline 暂保留**，等真实图测过再决定是否向量化

---

## 7. 下一步（拼豆项目）

| 步骤 | 状态 |
|---|---|
| 8 步管线代码 + Mard 色卡 + dry-run 跑通 | ✅ 已完成（本报告）|
| 100 张真实照片采集（cat/face/pet/scene 各 25）| ⏳ 待执行（用户）|
| 真实图复跑 + 人工评分 | ⏳ 待执行（用户）|
| ADR-014 最终判定（PASS/FAIL）→ 立 ADR-030 归档 | ⏳ 待执行（用户）|

---

## 8. 附录：跑通命令

```bash
cd algo-feasibility
uv venv .venv --python 3.12
source .venv/bin/activate
uv sync

# 拉色卡（如未做过）
curl -sSL -o data/mard.csv \
  https://raw.githubusercontent.com/maxcleme/beadcolors/master/gen/v3/mard.csv
uv run python data/build_palette.py

# 生成合成样图（仅 dry-run；用真实图时跳过）
uv run python data/build_synthetic_samples.py

# 跑 100 张
uv run python run_dryrun.py --grid 48 --colors 24

# 输出
# - data/results/timing_report.csv
# - data/results/summary.json
# - scoring/score_template.csv（人工评分模板）
```

---

## 9. 变更日志

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-05-18 | v0.1 | 初版 dry-run 报告：100 张合成图 + 3 组配置对照 + 性能瓶颈分析 |
