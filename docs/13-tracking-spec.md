# 埋点规范 · 拼豆小程序 v0.1

```yaml
文档名: Tracking & Analytics Spec - 拼豆小程序
版本: v0.1（骨架）
最后更新: 2026-05-17
关联文档: 01-prd.md / project-flow-and-milestones.md §3 / 14-metrics-dict.md（待创建）
关联 ADR: —
```

---

## 0. 文档说明

> 数据是互联网产品的命脉。**Day 1 起所有用户行为按统一规范上报**，避免后期返工。  
> 这份文档同时是**事件字典 + 上报规则 + 数据契约**，前端、后端、数据分析三方共用。

---

## 1. 设计原则

### 1.1 三条铁律

1. **事件命名一旦发布，永远不能改名**（只能新增 / 标弃用）
2. **统一上报通道，不允许私自加埋点**（一切都过 SDK）
3. **核心链路指标 Day 1 必须有**（不能等业务跑起来才补）

### 1.2 命名规范

```
事件名格式：<对象>_<动作>[_<状态>]

例：
pattern_generate_started     图纸开始生成
pattern_generate_completed   图纸生成完成
pattern_generate_failed      图纸生成失败
order_paid                   订单已支付
cart_item_added              购物车加入商品
```

- 全小写 + 下划线
- 对象在前，动作在后
- 状态用过去式（`_completed` / `_failed` / `_canceled`）

### 1.3 三类事件分级

| 分级 | 描述 | 示例 |
|---|---|---|
| **核心** | 关联北极星指标，必须 100% 上报 | order_paid, pattern_generate_completed |
| **路径** | 描述用户漏斗 | page_viewed, cart_item_added |
| **诊断** | 排查 bug 用 | api_error, network_timeout |

---

## 2. 上报通道架构

```
[小程序前端] ─┐
[小程序前端] ─┤
[B 端 PC]   ─┼──► 埋点 SDK ──► API Gateway ──► 业务后端
[后端服务]  ─┘                                    │
                                                  ▼
                                            ClickHouse / 日志归档
                                                  │
                                                  ▼
                                            BI 看板 / 告警
```

### 2.1 上报方式

- **前端事件**：通过 `track()` SDK 发往 `/api/v1/track`
- **后端事件**：直接写入 ClickHouse（异步队列）
- **批量上报**：前端攒 5 个事件或 5 秒 flush 一次（节省请求）
- **关键事件**：`order_paid` 等钱相关事件**立即上报**，不能 buffer

### 2.2 离线兜底

- 网络失败：写入 localStorage，下次启动重试
- 上报失败 ≥ 3 次：丢弃 + 本地 log（避免无限堆积）

---

## 3. 统一参数（每条事件都有）

| 参数 | 类型 | 必传 | 说明 |
|---|---|---|---|
| `event_name` | string | ✅ | 事件名 |
| `event_id` | string (uuid) | ✅ | 单事件唯一 ID（去重用） |
| `timestamp` | int (ms) | ✅ | 客户端时间戳 |
| `user_id` | int? | — | 已登录则必传 |
| `openid` | string? | — | 未登录用 openid |
| `platform` | enum | ✅ | `wechat` / `tt` / `web` |
| `app_version` | string | ✅ | 客户端版本 |
| `session_id` | string | ✅ | 会话 ID（首启动生成，30min 无操作过期） |
| `device_id` | string | ✅ | 设备唯一标识 |
| `network` | string? | — | `wifi` / `4g` / `5g` / `unknown` |
| `referrer` | string? | — | 来源页 / 上一页 |
| `properties` | object | — | 业务参数（事件特有） |

---

## 4. MVP 阶段核心事件清单

> 所有事件按 PRD §3 模块分组。MVP 阶段必须上线 **27 个事件**。

### 4.1 应用启动 / 会话

| 事件 | 触发时机 | 关键参数 |
|---|---|---|
| `app_launched` | 小程序冷启动 | `launch_scene`, `launch_path` |
| `app_show` | 小程序前台显示 | — |
| `app_hide` | 小程序后台 | `duration_sec` |
| `session_started` | 新会话开始 | — |

### 4.2 页面浏览

| 事件 | 触发时机 | 关键参数 |
|---|---|---|
| `page_viewed` | 进入页面 | `page_path`, `page_title` |
| `page_left` | 离开页面 | `page_path`, `stay_sec` |

### 4.3 上传与抠图（M1 模块）

| 事件 | 触发时机 | 关键参数 |
|---|---|---|
| `image_upload_started` | 用户选图后 | `image_size_kb`, `mime_type` |
| `image_upload_completed` | OSS 上传成功 | `duration_ms`, `object_key` |
| `image_upload_failed` | 上传失败 | `error_code`, `error_msg` |
| `cutout_completed` | 抠图成功 | `duration_ms`, `engine`（rembg/grabcut）|

### 4.4 图纸生成（M2 模块 - **核心**）

| 事件 | 触发时机 | 关键参数 |
|---|---|---|
| `pattern_generate_started` | 算法任务创建 | `grid_size`, `difficulty`, `brand` |
| `pattern_generate_completed` | 算法任务成功 | `duration_ms`, `pattern_id`, `color_count`, `substitution_ratio`, `algo_version` |
| `pattern_generate_failed` | 算法任务失败 | `error_code`, `algo_version` |
| `pattern_regenerated` | 用户点重生成 | `pattern_id`, `attempt_count` |
| `pattern_cell_modified` | 用户改单格 | `pattern_id`, `cell_count` |

### 4.5 难度档与预览（M3/M4）

| 事件 | 触发时机 | 关键参数 |
|---|---|---|
| `difficulty_selected` | 用户选难度 | `difficulty` |
| `size_preview_viewed` | 实物尺寸卡可见 | `physical_size_cm` |
| `size_reference_clicked` | 点击对比图 | — |

### 4.6 加购与下单（M5/M6 - **关键转化**）

| 事件 | 触发时机 | 关键参数 |
|---|---|---|
| `cart_item_added` | 一键加购成功 | `pattern_id`, `total_cents`, `item_count` |
| `checkout_started` | 进入结算页 | `cart_total_cents`, `item_count` |
| `payment_started` | 调起支付 | `order_id`, `pay_cents`, `pay_method` |
| `order_paid` ⭐ | 支付成功 | `order_id`, `pay_cents`, `is_first_order` |
| `payment_failed` | 支付失败 | `order_id`, `error_code` |
| `order_canceled` | 取消订单 | `order_id`, `reason` |

### 4.7 履约（M7）

| 事件 | 触发时机 | 关键参数 |
|---|---|---|
| `order_shipped` | 仓库发货（后端事件） | `order_id`, `shipping_no` |
| `order_delivered` | 物流签收 | `order_id` |
| `refund_requested` | 申请退款 | `order_id`, `reason` |

### 4.8 安全合规（M9）

| 事件 | 触发时机 | 关键参数 |
|---|---|---|
| `safety_dialog_shown` | 安全提示弹窗弹出 | `is_first_time` |
| `safety_dialog_acknowledged` | 用户勾选已读 | `read_duration_sec` |

---

## 5. 事件参数详细规范

### 5.1 枚举值约定

| 字段 | 取值 |
|---|---|
| `platform` | `wechat` / `tt` / `web` |
| `difficulty` | `easy` / `normal` / `pro` |
| `grid_size` | `16x16` / `32x32` / `48x48` / `64x64` |
| `pay_method` | `wechat` / `tt` / `manual` |
| `error_code` | 对应 06-api-spec.md §1.3 错误码 |

### 5.2 命名风格

- 字段统一 `snake_case`
- 时间字段后缀：`_at`（绝对时间）/ `_sec` `_ms`（耗时）
- 金额字段后缀：`_cents`（统一以分为单位）
- 布尔字段前缀：`is_` / `has_`

---

## 6. 北极星指标与漏斗

### 6.1 北极星指标

> **北极星 = 月活付费用户数（Monthly Paying Users, MPU）**

口径：当月发生 ≥ 1 次 `order_paid` 的去重 user_id 数

### 6.2 核心漏斗（M1 决策门指标对应）

```
Step 1: page_viewed (page_path=/upload)         上传页 PV
   ↓ 上传率
Step 2: image_upload_completed                   上传完成
   ↓ 生成率
Step 3: pattern_generate_completed               图纸生成
   ↓ 加购率
Step 4: cart_item_added                          一键加购
   ↓ 支付率
Step 5: order_paid                               支付完成
```

**关键转化率**（M1 决策门：Step1→Step5 ≥ 15%）：
- 上传率 = Step2 / Step1
- 生成率 = Step3 / Step2
- 加购率 = Step4 / Step3
- 支付率 = Step5 / Step4

### 6.3 算法质量指标

| 指标 | 定义 | 目标 |
|---|---|---|
| 算法成功率 | `pattern_generate_completed` / `pattern_generate_started` | ≥ 95% |
| 算法 P95 耗时 | `pattern_generate_completed.duration_ms` P95 | ≤ 10000ms |
| 平均替换比例 | `substitution_ratio` 平均 | ≤ 10% |
| 重生成率 | `pattern_regenerated` / `pattern_generate_started` | ≤ 30% |

---

## 7. 数据治理

### 7.1 隐私合规

- ❌ 不上报：手机号、身份证、支付卡号、地址明文
- ✅ 上报：经哈希的 user_id、openid、device_id
- ✅ 用户行使「删除我的数据」权 → 数据 30 天内清除

### 7.2 事件版本管理

- 新增字段：兼容（旧分析逻辑忽略未识别字段）
- 字段含义变更：禁止，必须新建事件
- 事件下线：标记 `deprecated`，保留至少 6 个月再删

### 7.3 数据保留策略

| 类型 | 保留期 | 备注 |
|---|---|---|
| 原始事件 | 90 天（热）| ClickHouse 主表 |
| 聚合数据 | 永久 | 日/周/月汇总表 |
| 用户行为日志 | 18 个月 | 合规要求 |

---

## 8. 实施 Checklist（Phase 1 W2）

- [ ] 选定 ClickHouse 部署方案（云托管 vs 自建）
- [ ] 实现埋点 SDK（前端 + 后端）
- [ ] 建立事件字典管理工具（推荐：YAML 单一源 + 自动生成 SDK 类型）
- [ ] 上线核心 27 个事件
- [ ] 搭建 Grafana 漏斗看板
- [ ] 关键事件告警（如支付失败率 > 5%）

---

## 9. 待补完成项

- [ ] Phase 2 事件清单（UGC / 创作者 / 代拼 / B 端 SaaS）
- [ ] Phase 3 事件清单（IoT / 数据中台）
- [ ] 事件 YAML 单一源（`/docs/tracking/events.yaml`）
- [ ] 自动化校验脚本（CI 检查事件命名规范）
- [ ] 与 14-metrics-dict.md 的指标对接

---

## 10. 变更日志

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-05-17 | v0.1 | 初始化埋点规范，定义 MVP 阶段 27 个核心事件 |
