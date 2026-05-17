# API 契约 · 拼豆小程序 v0.1

```yaml
文档名: API Specification - 拼豆小程序
版本: v0.1（骨架）
状态: 草稿
Owner: <后端负责人 - 待指派>
Reviewers: 前端负责人 / 算法负责人
最后更新: 2026-05-17
下次复盘: 2026-05-24
关联文档: 04-system-architecture.md / 05-data-model.md
契约源文件: ./openapi.yaml（待生成）
```

---

## 0. 文档说明

> ⚠️ **文档与代码同步规则**：本文档为人类可读概览，**机器可读源文件为 `./openapi.yaml`**（OpenAPI 3.1 规范）。所有 API 变更必须先改 YAML 再生成本文档。

**约定**：
- 所有 API 路径以 `/api/v1` 开头
- 所有响应使用统一 envelope 格式（见第 3 节）
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

完整错误码表见 `./error-codes.md`（待创建）

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

## 2. 接口分组总览

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
| PX 积分 | `/api/v1/px` | 2 | P1 |
| Webhooks | `/api/v1/webhooks` | 2 | P1 |
| Creators 创作者 | `/api/v1/creators` | — | P2 |
| Community 社区 | `/api/v1/community` | — | P2 |
| Proxy 代拼 | `/api/v1/proxy` | — | P2 |

---

## 3. MVP 核心接口（P1）

### 3.1 鉴权 Auth

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

### 3.2 文件上传 Upload

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

### 3.3 图纸 Patterns（核心模块）

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
    "status": "completed",   // processing | completed | failed
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
单格修改（用户在预览页改某格颜色）。

**Request**：
```json
{
  "changes": [
    {"x": 5, "y": 8, "color_id": 23},
    {"x": 5, "y": 9, "color_id": 23}
  ]
}
```

#### `POST /api/v1/patterns/{pattern_id}/regenerate`
重新生成（同图不同参数）。

#### `GET /api/v1/patterns`
获取我的图纸列表（分页）。

---

### 3.4 色卡 Colors

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

### 3.5 购物车 Cart

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

### 3.6 订单 Orders

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

### 3.7 支付 Payment

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

### 3.8 收货地址 Addresses

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

### 3.9 PX 积分

#### `GET /api/v1/px/balance`
当前余额。

#### `GET /api/v1/px/ledger`
流水（分页）。

---

## 4. 异步与 Webhook

### 4.1 算法异步任务

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

### 4.2 第三方回调

| Webhook | URL | 验签方式 |
|---|---|---|
| 微信支付 | `/api/v1/webhooks/wechat-pay` | HMAC-SHA256 |
| 字节支付 | `/api/v1/webhooks/tt-pay` | RSA |
| 物流回调 | `/api/v1/webhooks/logistics` | Token + IP 白名单 |

---

## 5. 限流与配额

| 接口类别 | 限流策略 |
|---|---|
| 登录 | 10 次/分钟/IP |
| 上传 | 5 次/分钟/用户 |
| 算法生成 | 3 次/分钟/用户（防滥用 GPU 资源） |
| 通用读接口 | 100 次/分钟/用户 |
| Webhook | 不限流（IP 白名单 + 验签） |

---

## 6. 版本管理

### 6.1 路径版本（Major）
```
/api/v1/...   ← 当前版本
/api/v2/...   ← 不兼容变更时启用
```

### 6.2 兼容性原则
- 新增字段：兼容（前端忽略未识别字段）
- 字段含义变更：不兼容，必须升 v2
- 字段删除：不兼容
- 错误码新增：兼容

---

## 7. Mock 与联调

### 7.1 Mock 服务
- **工具**：Apifox / Postman
- **环境**：
  - dev: `http://mock.pindou.local`
  - test: `https://test-api.pindou.com`

### 7.2 联调约定
- 后端必须先发布 OpenAPI YAML 才能开始前端开发
- 前端发现接口问题在 Apifox 评论区反馈，不直接改 YAML

---

## 8. 待补完成项

- [ ] 完整 OpenAPI 3.1 YAML 源文件 `./openapi.yaml`
- [ ] 全量错误码字典 `./error-codes.md`
- [ ] Phase 2 创作者 / 社区 / 代拼接口
- [ ] B 端 SaaS 接口规范
- [ ] IoT BLE 协议（关联 `09-iot-protocol.md`）
- [ ] 接口性能基准（每个 API P95 目标）

---

## 9. 变更日志

| 日期 | 版本 | 变更 | 作者 |
|---|---|---|---|
| 2026-05-17 | v0.1 | 初始化 MVP 阶段 38 个接口骨架 | 项目组 |
