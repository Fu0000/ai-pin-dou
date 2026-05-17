# API 契约 · 拼豆小程序 v0.5

```yaml
文档名: API Specification - 拼豆小程序
版本: v0.5（OpenAPI 3.1 + 库存 / 风格变体接口）
最后更新: 2026-05-17
关联文档: 04-system-architecture.md, 05-data-model.md, 07-algo-spec.md
关联 ADR: ADR-017, ADR-018, ADR-019, ADR-023
```

---

## 0. 文档说明

> ⚠️ **文档与代码同步规则**：本文档为人类可读概览，**机器可读源文件为 `./openapi.yaml`**（OpenAPI 3.1 规范）。所有 API 变更必须先改 YAML 再生成本文档。

**约定**：
- 所有 API 路径以 `/api/v1` 开头
- 所有响应使用统一 envelope 格式（见 §1.2）
- 所有时间字段为 ISO 8601 + 时区（如 `2026-05-17T08:30:00+08:00`）
- 所有金额单位为**分**（如 `9900` 表示 99 元）

---

## 1. 全局规范

### 1.1 鉴权

```
Header:
  Authorization: Bearer <JWT_TOKEN>
  X-App-Platform: wechat | tt | web
  X-App-Version: 1.0.0
```

获取 JWT：调用 `POST /api/v1/auth/login`（详见 §4.1）

### 1.2 统一响应格式

**成功**：
```json
{
  "code": 0,
  "message": "ok",
  "data": { ... },
  "request_id": "req_abc123",
  "timestamp": "2026-05-17T08:30:00+08:00"
}
```

**失败**：
```json
{
  "code": 10001,
  "message": "图片大小超出限制",
  "data": null,
  "request_id": "req_abc123",
  "timestamp": "2026-05-17T08:30:00+08:00"
}
```

### 1.3 错误码规范

| 段 | 含义 |
|---|---|
| `0` | 成功 |
| `10000-19999` | 客户端错误（参数/格式）|
| `20000-29999` | 鉴权错误 |
| `30000-39999` | 业务逻辑错误 |
| `40000-49999` | 第三方依赖错误 |
| `50000-59999` | 服务端内部错误 |

### 1.3.1 业务错误码段（v0.5 新增 INVENTORY / STYLE_VARIANT 段）

| 错误码 | 名称 | 含义 |
|---|---|---|
| `30100` | INVENTORY_INSUFFICIENT | 库存不足，无法预占 |
| `30101` | INVENTORY_EXPIRED | 预占已过期（关联 ADR-023）|
| `30102` | INVENTORY_DOUBLE_RELEASE | 同一 reservation_id 重复释放 |
| `40500` | STYLE_VARIANT_NOT_GENERATED | 该风格变体尚未生成（异步生成中）|
| `40501` | STYLE_VARIANT_INVALID | 不支持的风格类型 |

> 完整错误码字典待新建 `./error-codes.md`。

### 1.4 分页规范

```
Query Parameters:
  page=1            # 页码，从 1 开始
  page_size=20      # 每页大小，默认 20，最大 100
  sort=created_at   # 排序字段
  order=desc        # asc | desc
```

响应：
```json
{
  "data": {
    "items": [ ... ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 156,
      "total_pages": 8
    }
  }
}
```

---

## 2. OpenAPI 3.1 规范骨架

> v0.5 起 API 契约同步切到 OpenAPI 3.1 风格表达。机器可读源文件 `./openapi.yaml` 待生成；本节给出骨架对照。

### 2.1 根级结构示例

```yaml
openapi: 3.1.0
info:
  title: 拼豆小程序 API
  version: 0.5.0
servers:
  - url: https://api.pin-dou.example.com/api/v1
paths:
  /patterns: { ... }
  /patterns/{id}/style-variants: { ... }
  /orders: { ... }
  /inventory/reserve: { ... }
  /inventory/release: { ... }
components:
  schemas:
    User: { $ref: '#/components/schemas/User' }
    Pattern: { $ref: '#/components/schemas/Pattern' }
    Order: { $ref: '#/components/schemas/Order' }
    OrderItem: { $ref: '#/components/schemas/OrderItem' }
    BeadSku: { $ref: '#/components/schemas/BeadSku' }
    InventoryReservation: { $ref: '#/components/schemas/InventoryReservation' }
    Address: { $ref: '#/components/schemas/Address' }
    Error: { $ref: '#/components/schemas/Error' }
```

### 2.2 components/schemas 主对象骨架

```yaml
components:
  schemas:
    User:
      type: object
      properties:
        id: { type: integer }
        openid: { type: string }
        nickname: { type: string }
        avatar_url: { type: string }
        first_paid_at:
          type: string
          format: date-time
          nullable: true
          description: 首单大礼包判断 / 老朋友 9 折判断（关联 ADR-018, ADR-020）
    Pattern:
      type: object
      properties:
        id: { type: integer }
        preview_image_url: { type: string }
        grid_size: { type: string, enum: ['16x16', '32x32', '48x48', '64x64'] }
        difficulty:
          type: string
          enum: ['easy', 'normal', 'pro']
          description: 用户侧展示为「萌宠 mini / 摆件经典 / 装饰挂画」
        color_count: { type: integer }
        physical_size_cm: { type: number }
        style_variants:
          type: array
          items:
            type: object
            properties:
              style: { type: string, enum: ['realistic', 'pixel', 'cartoon'] }
              preview_url: { type: string }
              is_default: { type: boolean }
        algo_version: { type: string }
    Order:
      type: object
      properties:
        order_id: { type: integer }
        order_no: { type: string }
        status: { type: string, enum: ['pending_pay', 'paid', 'shipped', 'delivered', 'completed', 'cancelled', 'refunding', 'refunded'] }
        total_cents: { type: integer }
        pay_cents: { type: integer }
    OrderItem:
      type: object
      properties:
        sku_id: { type: integer }
        color_id: { type: integer }
        quantity: { type: integer }
        pack_quantity: { type: integer }
    BeadSku:
      type: object
      properties:
        id: { type: integer }
        color_id: { type: integer }
        pack_size: { type: integer }
        price_cents: { type: integer }
    InventoryReservation:
      type: object
      properties:
        reservation_id: { type: integer }
        pattern_id: { type: integer }
        sku_quantities:
          type: object
          additionalProperties:
            type: integer
          description: '{sku_id: qty} 预占清单'
        expires_at: { type: string, format: date-time }
        status: { type: string, enum: ['active', 'released', 'consumed'] }
    Address:
      type: object
      properties:
        id: { type: integer }
        name: { type: string }
        phone: { type: string }
        province: { type: string }
        city: { type: string }
        district: { type: string }
        address_detail: { type: string }
        is_default: { type: boolean }
    Error:
      type: object
      properties:
        code: { type: integer }
        message: { type: string }
        request_id: { type: string }
```

> 关联 ADR-019（style_variants 字段）/ ADR-020（first_paid_at 字段）/ ADR-023（InventoryReservation schema）。

---

## 3. 接口分组总览

| 分组 | 前缀 | 接口数（MVP）| Phase |
|---|---|---|---|
| Auth 鉴权 | `/api/v1/auth` | 3 | P1 |
| Users 用户 | `/api/v1/users` | 4 | P1 |
| Upload 文件 | `/api/v1/upload` | 2 | P1 |
| Patterns 图纸 | `/api/v1/patterns` | 6 | P1 |
| Colors 色卡 | `/api/v1/colors` | 2 | P1 |
| Cart 购物车 | `/api/v1/cart` | 4 | P1 |
| Orders 订单 | `/api/v1/orders` | 6 | P1 |
| Payment 支付 | `/api/v1/payment` | 2 | P1 |
| Address 地址 | `/api/v1/addresses` | 4 | P1 |
| Inventory 库存预占 ⭐ | `/api/v1/inventory` | 2 | P1 |
| ⛔ PX 积分 | `/api/v1/px` | 2 | Phase 2 |
| Webhooks | `/api/v1/webhooks` | 2 | P1 |
| Creators 创作者 | `/api/v1/creators` | — | P2 |
| Community 社区 | `/api/v1/community` | — | P2 |
| Proxy 代拼 | `/api/v1/proxy` | — | P2 |

---

## 4. MVP 核心接口（P1）

### 4.1 鉴权 Auth

#### `POST /api/v1/auth/login`
微信小程序登录换 JWT。

**Request**：
```json
{
  "platform": "wechat",
  "code": "<wx.login 返回的 code>",
  "user_info": {
    "nickname": "...",
    "avatar_url": "..."
  }
}
```

**Response**：
```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGc...",
    "expires_in": 7200,
    "user": {
      "id": 12345,
      "nickname": "...",
      "avatar_url": "...",
      "px_balance": 0,
      "level": 1
    }
  }
}
```

#### `POST /api/v1/auth/refresh`
刷新 JWT。

#### `POST /api/v1/auth/logout`
退出登录（使 token 失效）。

---

### 4.2 文件上传 Upload

#### `POST /api/v1/upload/image`
获取临时上传凭证（预签名 URL 模式，前端直传 OSS）。

**Request**：
```json
{
  "type": "user_photo",
  "file_size": 2048000,
  "mime_type": "image/jpeg"
}
```

**Response**：
```json
{
  "data": {
    "upload_url": "https://oss.../...?signature=xxx",
    "object_key": "uploads/2026-05-17/openid_xxx/uuid.jpg",
    "expires_in": 600
  }
}
```

> ⚠️ 前端拿到 `upload_url` 后直接 PUT 到 OSS，不经过业务后端。

---

### 4.3 图纸 Patterns（核心模块）

#### `POST /api/v1/patterns/generate`
**异步**算法生成图纸。

**Request**：
```json
{
  "source_object_key": "uploads/2026-05-17/openid_xxx/uuid.jpg",
  "grid_size": "32x32",
  "difficulty": "normal",
  "brand": "mard",
  "options": {
    "remove_background": true,
    "add_outline": true
  }
}
```

**Response**（立即返回，进入异步处理）：
```json
{
  "data": {
    "task_id": "task_abc123",
    "status": "processing",
    "estimated_seconds": 8
  }
}
```

#### `GET /api/v1/patterns/tasks/{task_id}`
轮询算法任务状态（前端 1s 间隔轮询，可改 WebSocket）。

**Response**：
```json
{
  "data": {
    "task_id": "task_abc123",
    "status": "completed",
    "progress": 100,
    "pattern_id": 9876
  }
}
```

#### `GET /api/v1/patterns/{pattern_id}`
获取图纸详情。

**Response**：
```json
{
  "data": {
    "id": 9876,
    "name": "我的拼豆图纸",
    "preview_image_url": "https://oss.../patterns/9876.png",
    "grid_size": "32x32",
    "difficulty": "normal",
    "physical_size_cm": 16.0,
    "color_count": 18,
    "color_summary": [
      {
        "color_id": 23,
        "code": "M-023",
        "name": "玫瑰红",
        "hex": "#FF6B9D",
        "count": 450,
        "stock_status": "available",
        "is_substituted": false
      }
    ],
    "estimated_hours": 2.5,
    "substitution_ratio": 0.05,
    "algo_version": "v1.0.0"
  }
}
```

#### `PUT /api/v1/patterns/{pattern_id}/cells`

> ⛔ `PUT /api/v1/patterns/{pattern_id}/cells`（单格修改色号）— v0.5 起废弃
> 取代方案：`POST /api/v1/patterns/{pattern_id}/style-variants`（list / switch 双 action）
> 关联 ADR：ADR-019

单格修改（用户在预览页改某格颜色）。**v0.5 起不再启用，保留段落作审计轨迹。**

**Request**：
```json
{
  "changes": [
    {"x": 5, "y": 8, "color_id": 23},
    {"x": 5, "y": 9, "color_id": 23}
  ]
}
```

#### `POST /api/v1/patterns/{pattern_id}/style-variants`
风格变体接口（关联 ADR-019）：支持 list / switch 双 action。

**Request (list 模式)**：
```json
{
  "action": "list"
}
```

**Response**：
```json
{
  "code": 0,
  "data": {
    "variants": [
      {"style": "realistic", "preview_url": "...", "is_default": true},
      {"style": "pixel",     "preview_url": "...", "is_default": false},
      {"style": "cartoon",   "preview_url": "...", "is_default": false}
    ]
  }
}
```

**Request (switch 模式)**：
```json
{
  "action": "switch",
  "variant_style": "cartoon"
}
```
- `variant_style` 必须 ∈ `{realistic, pixel, cartoon}`
- 切换后 `patterns.pattern_data.style_variants[*].is_default` 同步更新

**Response**：
```json
{
  "code": 0,
  "data": {
    "current_default": "cartoon"
  }
}
```

**错误码**：`STYLE_VARIANT_NOT_GENERATED` (40500) / `STYLE_VARIANT_INVALID` (40501)

#### `POST /api/v1/patterns/{pattern_id}/regenerate`
重新生成（同图不同参数）。

#### `GET /api/v1/patterns`
获取我的图纸列表（分页）。

---

### 4.4 色卡 Colors

#### `GET /api/v1/colors`
获取色卡（含库存状态）。

**Query**：`brand=mard&active=true`

**Response**：
```json
{
  "data": {
    "items": [
      {
        "id": 23,
        "brand": "mard",
        "code": "M-023",
        "name": "玫瑰红",
        "hex": "#FF6B9D",
        "stock_status": "available"
      }
    ]
  }
}
```

#### `GET /api/v1/colors/{color_id}`
单色详情。

---

### 4.5 购物车 Cart

#### `GET /api/v1/cart`
获取购物车。

#### `POST /api/v1/cart/add-from-pattern`
**核心接口**：从图纸算料一键加购。

**Request**：
```json
{
  "pattern_id": 9876,
  "extras": ["base_board_32", "ironing_paper"]
}
```

#### `PATCH /api/v1/cart/items/{item_id}`
修改购物车单项数量。

#### `DELETE /api/v1/cart/items/{item_id}`
移除购物车项。

---

### 4.6 订单 Orders

#### `POST /api/v1/orders`
创建订单（从购物车结算）。

**Request**：
```json
{
  "address_id": 100,
  "remark": "请尽快发货",
  "use_px": 0
}
```

> v0.5 起：`POST /orders` **不再要求** `safety_acknowledged` 字段（关联 ADR-017 履约关怀，取代付款前强弹窗）。

**Response**：
```json
{
  "data": {
    "order_id": 5001,
    "order_no": "PD202605170001",
    "total_cents": 9900,
    "pay_cents": 9900,
    "status": "pending_pay"
  }
}
```

#### `GET /api/v1/orders`
我的订单列表（分页 + 状态筛选）。

#### `GET /api/v1/orders/{order_id}`
订单详情。

#### `POST /api/v1/orders/{order_id}/cancel`
取消订单。

#### `POST /api/v1/orders/{order_id}/refund`
申请退款。

#### `GET /api/v1/orders/{order_id}/logistics`
物流追踪。

---

### 4.7 支付 Payment

#### `POST /api/v1/payment/wechat/prepay`
微信支付预下单。

**Response**（返回 `wx.requestPayment` 所需参数）：
```json
{
  "data": {
    "timeStamp": "...",
    "nonceStr": "...",
    "package": "prepay_id=...",
    "signType": "MD5",
    "paySign": "..."
  }
}
```

#### `POST /api/v1/webhooks/wechat-pay`
微信支付异步回调（**无需鉴权**，但要校验签名）。

---

### 4.8 收货地址 Addresses

#### `GET /api/v1/addresses`
列表。

#### `POST /api/v1/addresses`
新增。

**Request**：
```json
{
  "name": "张三",
  "phone": "13800138000",
  "province": "浙江省",
  "city": "金华市",
  "district": "义乌市",
  "address_detail": "稠州北路 88 号",
  "is_default": true
}
```

#### `PATCH /api/v1/addresses/{id}`
修改。

#### `DELETE /api/v1/addresses/{id}`
删除。

---

### 4.9 PX 积分

> ⛔ PX 积分接口（`/api/v1/px/balance` / `/api/v1/px/ledger`）— v0.5 起 MVP 不实现
> 推迟到 Phase 2 与 UGC 社区一起做；Schema 保留以便 Phase 2 直接启用
> 关联 ADR：ADR-018

#### `GET /api/v1/px/balance`
当前余额。

#### `GET /api/v1/px/ledger`
流水（分页）。

---

### 4.10 库存预占（关联 ADR-023）

#### `POST /api/v1/inventory/reserve`
图纸生成成功后调用，预占 30 分钟库存。

**Request**：
```json
{
  "pattern_id": 9876,
  "sku_quantities": {
    "42": 450,
    "57": 120,
    "63": 88
  }
}
```

**Response**：
```json
{
  "code": 0,
  "data": {
    "reservation_id": 100023,
    "expires_at": "2026-05-17T15:00:00+08:00",
    "ttl_seconds": 1800
  }
}
```

**错误码**：

| 错误码 | 含义 |
|---|---|
| `30100` | 库存不足（INVENTORY_INSUFFICIENT）|
| `30101` | 预占已过期（INVENTORY_EXPIRED）|
| `30102` | 重复释放（INVENTORY_DOUBLE_RELEASE）|

> 30 分钟 TTL 由 Redis EXPIRE 兜底；持久化轨迹见 05-data-model.md §2.7 `inventory_reservations` 表。

#### `POST /api/v1/inventory/release`
显式释放预占（用户取消 / 支付失败）或超时回调。

**Request**：
```json
{
  "reservation_id": 100023,
  "reason": "user_cancel"
}
```
- `reason` ∈ `{user_cancel, ttl_expired, payment_failed}`

**Response**：
```json
{
  "code": 0,
  "data": {
    "status": "released"
  }
}
```

---

## 5. 异步与 Webhook

### 5.1 算法异步任务

```
[前端] POST /patterns/generate
    │  返回 task_id
    ▼
[前端] 每 1s 轮询 GET /patterns/tasks/{task_id}
    │
    ▼
[前端] 收到 status=completed → 跳转预览页
```

> Phase 2 改造为 WebSocket 推送，减少轮询。

### 5.2 第三方回调

| Webhook | URL | 验签方式 |
|---|---|---|
| 微信支付 | `/api/v1/webhooks/wechat-pay` | HMAC-SHA256 |
| 字节支付 | `/api/v1/webhooks/tt-pay` | RSA |
| 物流回调 | `/api/v1/webhooks/logistics` | Token + IP 白名单 |

---

## 6. 限流与配额

| 接口类别 | 限流策略 |
|---|---|
| 登录 | 10 次/分钟/IP |
| 上传 | 5 次/分钟/用户 |
| 算法生成 | 3 次/分钟/用户（防滥用 GPU 资源） |
| 库存预占 | 10 次/分钟/用户（同一 pattern 幂等）|
| 通用读接口 | 100 次/分钟/用户 |
| Webhook | 不限流（IP 白名单 + 验签） |

---

## 7. 版本管理

### 7.1 路径版本（Major）
```
/api/v1/...   ← 当前版本
/api/v2/...   ← 不兼容变更时启用
```

### 7.2 兼容性原则
- 新增字段：兼容（前端忽略未识别字段）
- 字段含义变更：不兼容，必须升 v2
- 字段删除：不兼容
- 错误码新增：兼容

---

## 8. Mock 与联调

### 8.1 Mock 服务
- **工具**：Apifox / Postman
- **环境**：
  - dev: `http://mock.pindou.local`
  - test: `https://test-api.pindou.com`

### 8.2 联调约定
- 后端必须先发布 OpenAPI YAML 才能开始前端开发
- 前端发现接口问题在 Apifox 评论区反馈，不直接改 YAML

---

## 9. 待补完成项

- [ ] 完整 OpenAPI 3.1 YAML 源文件 `./openapi.yaml`
- [ ] 全量错误码字典 `./error-codes.md`
- [ ] Phase 2 创作者 / 社区 / 代拼接口
- [ ] B 端 SaaS 接口规范
- [ ] IoT BLE 协议（关联 `09-iot-protocol.md`）
- [ ] 接口性能基准（每个 API P95 目标）

---

## 10. 灵魂三句话锚点

> 拼豆产品灵魂三句话（关联 ADR-013）：
> 1. 零智商税
> 2. 把感情做成礼物
> 3. 在心流中找回自我
>
> 本文档关键 API 决策与三句话的对应关系如下，逐条接受未来重大改动的"反查"。

| # | 设计 / 决策点 | 对应灵魂 | 一句话理由（≤ 40 字） |
|---|---|---|---|
| 1 | `POST /orders` 移除 `safety_acknowledged` 必填 | 零智商税 | 用户付款不被法律免责文案打断 |
| 2 | `POST /inventory/reserve` 30 min TTL | 把感情做成礼物 | 下单即承诺，礼物永远买得到 |
| 3 | `style-variants` list / switch 双 action | 在心流中找回自我 | 用户挑感觉而非改色号，零延迟 |
| 4 | `/api/v1/px/*` ⛔ 推迟到 Phase 2 | 零智商税 | 不给用户暴露不能用的余额 |

---

## 11. 变更日志

| 日期 | 版本 | 变更 | 备注 |
|---|---|---|---|
| 2026-05-17 | v0.1 | 初始化 MVP 阶段 38 个接口骨架 | 项目组 |
| 2026-05-17 | v0.5 | 新增 §2 OpenAPI 3.1 骨架 + components/schemas 8 个主对象；新增 `POST /patterns/{id}/style-variants` (list/switch)、`POST /inventory/reserve` / `release`；⛔ `PUT /patterns/{id}/cells` 与 `/api/v1/px/*`；`POST /orders` 移除 safety_acknowledged；新增 INVENTORY_* / STYLE_VARIANT_* 错误码段；灵魂三句话锚点 | 关联 ADR-017, ADR-018, ADR-019, ADR-023 |
