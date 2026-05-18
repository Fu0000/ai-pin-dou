# 算法可行性预实测 · ADR-014 阻塞门

> 这是 **Phase 1 启动前的最后一道闸**（关联 [`/decision-log.md` ADR-014](../decision-log.md) / [AGENTS.md §8](../AGENTS.md)）。  
> 不通过 → MVP 推迟，先调算法。

---

## 0. 为什么有这个目录

- ADR-014 把"100 张真实样图实测 P95 ≤ 10s + 优良率 ≥ 60%"列为 M0 唯一 🔴 阻塞项
- 这件事必须在写后端代码之前做，避免发现"算法跑不动"才回头
- 单人项目不需要把它做成 FastAPI 服务，**Jupyter Notebook 跑通即可**
- 通过后，本目录的脚本可作为 Phase 1 后端 `algo-api` 容器的种子代码（关联 [`docs/04-system-architecture.md §2.4`](../docs/04-system-architecture.md)）

---

## 1. 通过标准（M0 阻塞门）

来自 [`docs/07-algo-spec.md §6.1`](../docs/07-algo-spec.md)：

| 维度 | 阈值 | 备注 |
|---|---|---|
| 样本规模 | 100 张真实图（猫 / 人脸 / 宠物 / 风景 各 25 张）| 必须真实图，不要合成 |
| 端到端 P95 耗时 | ≤ 10 秒 | 包含 ① Preprocess ~ ⑧ Calculate 全管线 + 风格变体并行 |
| 人工评分优良率 | ≥ 60% | 5 分制评分 ≥ 3 分视为优良 |

任一未达标 → 阻塞 Phase 1。

---

## 2. 目录结构

```
algo-feasibility/
├── README.md                  ← 本文件（操作手册）
├── pyproject.toml             ← uv 项目配置（依赖锁定）
├── .gitignore
├── samples/                   ← 100 张样图（不入库，见 §3）
│   ├── cat/                   ←  25 张
│   ├── face/                  ←  25 张
│   ├── pet/                   ←  25 张
│   └── scene/                 ←  25 张
├── notebooks/
│   └── m0_feasibility.ipynb   ← 主 Notebook（跑全流程 + 计时 + 输出预览）
├── pipeline/                  ← 算法各步骤的纯函数实现
│   ├── __init__.py
│   ├── preprocess.py
│   ├── cutout.py              ← rembg 包装
│   ├── pixelize.py
│   ├── quantize.py            ← K-Means
│   ├── color_map.py           ← Mard 色卡 + CIE Lab
│   ├── outline.py
│   ├── calculate.py
│   └── pipeline.py            ← 8 步主管线编排
├── data/
│   ├── mard_palette.json      ← Mard 400+ 色卡（关联 ADR-004）
│   └── results/               ← 每次跑的输出（图、JSON、耗时）
└── scoring/
    ├── score_template.csv     ← 评分表头模板（4 行说明 + 0 行数据，入库）
    └── score_summary.py       ← 汇总评分 + 计算优良率
```

---

## 3. 样本来源（W0 必须先备齐）

- 自己拍 / 收集 100 张真实照片，按 4 类各 25 张归到 `samples/<类>/` 目录
- **不要用网图**：版权 + 真实分布偏差
- **必须包含**：明显主体 / 背景复杂 / 暗光 / 高对比 等多样情况
- **隐私**：含人脸的样图实验后立即删（与 ADR-001 用户隐私一致）
- `samples/` 目录已加入 `.gitignore`，不入库

> 100 张样本是单人项目第一周最值得花时间的事，没有它后面所有算法决策都是空想。

---

## 4. 跑通流程（5 步）

### 4.1 安装环境

```bash
cd algo-feasibility
uv venv .venv
source .venv/bin/activate
uv sync
```

### 4.2 准备色卡

把 Mard 400+ 色卡的 RGB/Lab 值放到 `data/mard_palette.json`，格式参考 [`docs/05-data-model.md §2.3 colors 表`](../docs/05-data-model.md)。

可用 `maxcleme/beadcolors` 仓库的 `mard.json` 作为起点（关联 `project-plan.md §三 物理色彩数据库`）。

### 4.3 摆好 100 张样图

```bash
mkdir -p samples/{cat,face,pet,scene}
# 把图片复制进去，每类 25 张
```

### 4.4 跑 Notebook

```bash
jupyter lab
# 打开 notebooks/m0_feasibility.ipynb
# Run All
```

Notebook 会：
1. 遍历 100 张图
2. 对每张跑完整 8 步管线 + 风格变体并行
3. 记录每步耗时、总耗时、内存峰值
4. 输出 `data/results/<sample_id>/` 含原图、抠图、像素图、3 套风格变体、color_summary.json
5. 汇总输出 `data/results/timing_report.csv`

### 4.5 人工评分

跑完 `run_dryrun.py` 会自动生成 `scoring/score_pending.csv`（不入库），对照 `data/results/<sample_id>/preview.png` 给 1~5 分（5 分制）后保存。

跑 `uv run python scoring/score_summary.py scoring/score_pending.csv` 输出：
- 平均分
- 优良率（≥3 分占比）
- 各类样本（猫/人脸/宠物/风景）单独统计

---

## 5. 通过判定

```python
# scoring/score_summary.py 最终输出示例
{
  "p95_total_ms": 8420,         # ✅ ≤ 10000
  "good_rate": 0.68,            # ✅ ≥ 0.60
  "verdict": "PASS",
  "category_breakdown": {
    "cat":   {"good_rate": 0.84, "p95_ms": 6800},
    "face":  {"good_rate": 0.56, "p95_ms": 9200},   # ⚠️ 人脸最难
    "pet":   {"good_rate": 0.72, "p95_ms": 7900},
    "scene": {"good_rate": 0.60, "p95_ms": 8800}
  }
}
```

**通过路径**：

- ✅ PASS → 把 `pipeline/` 各模块作为种子搬进 Phase 1 后端 `algo-api` 容器
- ⚠️ FAIL（耗时）→ 优先优化抠图（rembg 模型选 `u2net_lite` 而非 `u2net`），再优化 K-Means（minibatch + 限色数）
- ❌ FAIL（优良率）→ 找最低分的类（一般是人脸），单独调整该类的预处理/量化参数；样本不达标先扩样本

---

## 6. 与 04-system-architecture.md 的衔接

通过后，`pipeline/*.py` 直接搬到 `algo-api` 容器（关联 [`docs/04-system-architecture.md §2.4 / §4.2`](../docs/04-system-architecture.md)）：

```
algo-feasibility/pipeline/        →  backend/algo/  + FastAPI 路由壳
notebooks/m0_feasibility.ipynb    →  backend/tests/algo/test_regression.py（回归测试集）
scoring/score_template.csv        →  作为算法版本回归基线（关联 docs/07-algo-spec.md §7）
```

---

## 7. 时间盒

> 单人项目这一步最容易拖。给自己定死时间盒：

| 阶段 | 投入 | 产出 |
|---|---|---|
| W0.1 | 1 天 | 100 张样图采集 |
| W0.2~3 | 2 天 | 8 步管线 + Notebook 跑通 |
| W0.4 | 0.5 天 | 100 张人工评分 + 汇总报告 |
| W0.5 | 0.5 天 | 不通过则迭代调参 1 轮（最多 1 轮，超过就推迟 MVP） |

**总投入：4 天**。超出此时间盒就触发 ADR-014 复盘——算法策略可能要重新考虑。

---

## 8. 输出归档

预实测完成后必须归档以下证据到 `decision-log.md`（不论 PASS/FAIL）：

- M0 阻塞门评估结果（PASS / FAIL）
- `data/results/timing_report.csv` 摘要
- `scoring/score_summary.py scoring/score_pending.csv` 输出
- 任何参数调整记录
- 100 张样本的总目录大小（用于评估算法容器内存预算，关联 ADR-028 §4.4 回切条件）

---

## 9. 变更日志

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-05-18 | v0.1 | 初始化预实测脚手架：README + 目录结构 + 时间盒 + 通过判定 + 与后端衔接 |
