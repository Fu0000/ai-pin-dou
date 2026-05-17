# 数据模型 · 拼豆小程序 v0.1

```yaml
文档名: Data Model - 拼豆小程序
版本: v0.1（骨架）
状态: 草稿
Owner: <后端负责人 - 待指派>
Reviewers: 技术负责人 / 产品负责人 / DBA
最后更新: 2026-05-17
下次复盘: 2026-05-24
关联文档: 04-system-architecture.md / 06-api-spec.md
关联 ADR: ADR-002 / ADR-007
```

---

## 0. 数据库选型

| 类别 | 选型 | 用途 |
|---|---|---|
| 主库 | PostgreSQL 15 | 事务型业务数据 |
| 缓存 | Redis 7 | 热点数据、会话、限流 |
| 对象存储 | OSS / COS | 图片、图纸文件 |
| 数据仓库 | ClickHouse（Phase 3）| 埋点、BI |

---

## 1. 数据模型总览（ER 图）

```
                ┌──────────────┐
                │    users     │
                └──┬───┬───┬───┘
                   │   │   │
       ┌───────────┘   │   └────────────┐
       ▼               ▼                ▼
  ┌─────────┐    ┌──────────┐     ┌──────────┐
  │ patterns│    │  orders  │     │ px_ledger│
  └────┬────┘    └─────┬────┘     └──────────┘
       │               │
       │               ▼
       │         ┌──────────────┐
       │         │ order_items  │
       │         └──────┬───────┘
       │                │
       └────┐           ▼
            ▼     ┌────────────┐
        ┌─────────┤  bead_skus │
        │colors   └────────────┘
        └─────────┘
```

---

## 2. 核心表 DDL（v0.1 草案）

> ⚠️ 本节为 **v0.1 草案**，字段会在 v0.5 评审时调整。所有 DDL 应同步到迁移工具（推荐 Alembic / Prisma Migrate）。

### 2.1 用户表 `users`

```sql
CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,
    openid          VARCHAR(64)  UNIQUE NOT NULL,    -- 微信 openid
    unionid         VARCHAR(64),                     -- 微信 unionid（跨小程序识别）
    tt_openid       VARCHAR(64),                     -- 抖音 openid（Phase 2）
    nickname        VARCHAR(64),
    avatar_url      TEXT,
    phone           VARCHAR(20),                     -- 加密存储
    px_balance      INTEGER      DEFAULT 0,          -- PX 积分余额（关联 ADR-007）
    level           SMALLINT     DEFAULT 1,          -- 用户等级 1~5
    total_xp        INTEGER      DEFAULT 0,
    invited_by      BIGINT       REFERENCES users(id),
    status          SMALLINT     DEFAULT 1,          -- 1=正常 0=封禁
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  DEFAULT NOW()
);
CREATE INDEX idx_users_openid ON users(openid);
CREATE INDEX idx_users_unionid ON users(unionid);
```

---

### 2.2 图纸表 `patterns`

```sql
CREATE TABLE patterns (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT       NOT NULL REFERENCES users(id),
    name            VARCHAR(128),
    source_image_url TEXT        NOT NULL,           -- 原始图片 OSS URL
    cutout_image_url TEXT,                           -- 抠图后图片 URL
    preview_image_url TEXT,                          -- 像素预览图 URL
    grid_size       VARCHAR(16)  NOT NULL,           -- '32x32' / '48x48'
    difficulty      VARCHAR(16)  NOT NULL,           -- 'easy' / 'normal' / 'pro'
    color_count     SMALLINT     NOT NULL,           -- 实际使用色数
    pattern_data    JSONB        NOT NULL,           -- 像素矩阵 [[color_id,...]]
    color_summary   JSONB        NOT NULL,           -- {color_id: count, ...}
    physical_size_cm NUMERIC(5,1),                   -- 实物尺寸（cm）
    algo_version    VARCHAR(16)  NOT NULL,           -- 算法版本号（关联回归测试）
    is_public       BOOLEAN      DEFAULT FALSE,      -- Phase 2 UGC 用
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);
CREATE INDEX idx_patterns_user_id ON patterns(user_id);
CREATE INDEX idx_patterns_created_at ON patterns(created_at DESC);
```

**JSONB 示例**：
```json
{
  "pattern_data": [[1,1,2,3], [1,2,2,3], ...],
  "color_summary": {"1": 450, "2": 120, "3": 88}
}
```

---

### 2.3 色卡表 `colors`

```sql
CREATE TABLE colors (
    id              SERIAL PRIMARY KEY,
    brand           VARCHAR(32)  NOT NULL,           -- 'mard' / 'artkal' / 'perler'
    code            VARCHAR(32)  NOT NULL,           -- 品牌色号 'M-023'
    name            VARCHAR(64),                     -- '玫瑰红'
    hex             CHAR(7)      NOT NULL,           -- '#FF6B9D'
    rgb_r           SMALLINT     NOT NULL,
    rgb_g           SMALLINT     NOT NULL,
    rgb_b           SMALLINT     NOT NULL,
    lab_l           NUMERIC(6,3),                    -- CIE Lab 值
    lab_a           NUMERIC(6,3),
    lab_b           NUMERIC(6,3),
    is_active       BOOLEAN      DEFAULT TRUE,       -- 是否启用
    is_rare         BOOLEAN      DEFAULT FALSE,      -- 是否为稀有色（积分兑换专属）
    sku_id          BIGINT       REFERENCES bead_skus(id),
    UNIQUE (brand, code)
);
CREATE INDEX idx_colors_brand_active ON colors(brand, is_active);
```

---

### 2.4 库存/SKU 表 `bead_skus`

```sql
CREATE TABLE bead_skus (
    id              BIGSERIAL PRIMARY KEY,
    color_id        INTEGER      NOT NULL REFERENCES colors(id),
    pack_size       INTEGER      NOT NULL,           -- 每包颗数（如 500）
    price_cents     INTEGER      NOT NULL,           -- 单价（分）
    stock_qty       INTEGER      DEFAULT 0,          -- 当前库存（颗）
    stock_status    VARCHAR(16)  DEFAULT 'available',-- 'available' / 'low' / 'oos'
    low_threshold   INTEGER      DEFAULT 5000,       -- 低库存阈值
    supplier        VARCHAR(64),                     -- 供应商名
    sgs_certified   BOOLEAN      DEFAULT FALSE,      -- SGS 认证（关联 22-safety-checklist.md）
    sgs_cert_url    TEXT,                            -- 证书图片 URL
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  DEFAULT NOW()
);
CREATE INDEX idx_bead_skus_status ON bead_skus(stock_status);
```

---

### 2.5 订单表 `orders`

```sql
CREATE TABLE orders (
    id              BIGSERIAL PRIMARY KEY,
    order_no        VARCHAR(32)  UNIQUE NOT NULL,    -- 业务单号 'PD202605170001'
    user_id         BIGINT       NOT NULL REFERENCES users(id),
    pattern_id      BIGINT       REFERENCES patterns(id),
    
    -- 金额
    total_cents     INTEGER      NOT NULL,           -- 订单总额（分）
    pay_cents       INTEGER      NOT NULL,           -- 实付金额
    discount_cents  INTEGER      DEFAULT 0,
    
    -- 状态机
    status          VARCHAR(24)  NOT NULL,           
    -- 'pending_pay' / 'paid' / 'shipped' / 'delivered' / 'completed'
    -- 'cancelled'  / 'refunding' / 'refunded'
    
    -- 支付
    pay_method      VARCHAR(16),                     -- 'wechat' / 'tt'
    pay_tx_id       VARCHAR(64),                     -- 第三方支付流水号
    paid_at         TIMESTAMPTZ,
    
    -- 收货
    address_snapshot JSONB,                          -- 下单时地址快照
    shipping_no     VARCHAR(64),                     -- 物流单号
    shipped_at      TIMESTAMPTZ,
    delivered_at    TIMESTAMPTZ,
    
    -- 履约
    sorting_pushed_at TIMESTAMPTZ,                   -- 配料单推送供应链时间
    
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  DEFAULT NOW()
);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
```

**订单状态机**：
```
pending_pay ──支付──► paid ──发货──► shipped ──签收──► delivered ──7天──► completed
     │                  │                                   │
     └──取消──► cancelled└──申请退款──► refunding ──► refunded
```

---

### 2.6 订单明细表 `order_items`

```sql
CREATE TABLE order_items (
    id              BIGSERIAL PRIMARY KEY,
    order_id        BIGINT       NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    sku_id          BIGINT       NOT NULL REFERENCES bead_skus(id),
    color_id        INTEGER      NOT NULL REFERENCES colors(id),
    quantity        INTEGER      NOT NULL,           -- 颗数
    pack_quantity   INTEGER      NOT NULL,           -- 包数
    unit_price_cents INTEGER     NOT NULL,
    subtotal_cents  INTEGER      NOT NULL
);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
```

---

### 2.7 PX 积分流水 `px_ledger`

> 关联 ADR-007：PX 是准现金负债，必须有完整流水

```sql
CREATE TABLE px_ledger (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT       NOT NULL REFERENCES users(id),
    delta           INTEGER      NOT NULL,           -- 正=获得，负=消耗
    balance_after   INTEGER      NOT NULL,           -- 变动后余额（核对用）
    
    source_type     VARCHAR(32)  NOT NULL,           
    -- 'order_paid' / 'daily_login' / 'invite' / 'redeem' / 'admin_adjust'
    source_id       VARCHAR(64),                     -- 关联订单/活动 ID
    
    description     TEXT,
    expire_at       TIMESTAMPTZ,                     -- 部分活动 PX 有过期时间
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);
CREATE INDEX idx_px_ledger_user ON px_ledger(user_id, created_at DESC);
```

---

## 3. Phase 2+ 扩展表（预留设计）

| 表名 | 用途 | 何时启用 |
|---|---|---|
| `creators` | 创作者档案 | Phase 2 |
| `creator_earnings` | 佣金流水 | Phase 2 |
| `pattern_likes` / `pattern_comments` | 社区互动 | Phase 2 |
| `merchants` | B 端门店 | Phase 2 |
| `proxy_orders` | 代拼撮合 | Phase 1 末加分项 / Phase 2 |
| `iot_devices` | 智能板设备绑定 | Phase 3 |
| `badges` / `user_badges` | 徽章系统 | Phase 1 |

---

## 4. Redis Key 规范

### 4.1 命名规范
```
<业务域>:<对象>:<id>[:<子键>]

例：
user:profile:12345
order:status:PD202605170001
algo:queue:pending
ratelimit:upload:openid_xxx
sku:stock:42
```

### 4.2 关键缓存

| Key | TTL | 用途 |
|---|---|---|
| `user:session:<openid>` | 7d | 登录态 |
| `sku:stock:<sku_id>` | 60s | 库存热点缓存 |
| `colors:active:<brand>` | 1h | 启用色卡列表 |
| `algo:result:<task_id>` | 24h | 算法异步任务结果 |
| `ratelimit:upload:<user>` | 1m | 上传频率限制 |

---

## 5. OSS 目录结构

```
oss-bucket/
├── uploads/                          # 用户原图（24h 自动删除）
│   └── <yyyy-mm-dd>/<openid>/<uuid>.jpg
├── cutouts/                          # 抠图结果（30d 保留）
│   └── <yyyy-mm-dd>/<pattern_id>.png
├── patterns/                         # 像素图纸预览（永久）
│   └── <pattern_id>.png
├── creators/                         # 创作者上传图纸（Phase 2）
└── certs/                            # SGS 证书图片
```

---

## 6. 数据安全与合规

| 数据类别 | 处理方式 |
|---|---|
| 用户原图 | 24 小时后自动删除（隐私要求） |
| 手机号 | AES-256 加密存储，展示时脱敏 |
| 微信 openid | 脱敏不可外露 |
| 支付流水 | 不存储完整卡号；仅留第三方流水号 |
| 数据库连接 | 强制 SSL/TLS |
| 备份 | 每日全量 + binlog 增量；保留 30 天 |

---

## 7. 数据库性能预留

| 对象 | MVP 估算 | Phase 3 估算 |
|---|---|---|
| `users` 行数 | 10K | 1M |
| `patterns` 行数 | 50K | 10M |
| `orders` 行数 | 5K/月 | 50K/月 |
| 主库 QPS | < 200 | < 5000 |

**未来扩展计划**：
- Phase 3 启用读写分离
- Phase 4 按 user_id 分库（>10M 用户时）

---

## 8. 待补完成项

- [ ] 全部 Phase 2+ 扩展表的详细 DDL
- [ ] 索引策略评审（DBA 介入）
- [ ] 数据归档策略（冷数据 → S3 / OSS 归档）
- [ ] 数据字典完整版（每个字段含义 / 取值范围）
- [ ] 与埋点表（ClickHouse）的字段对应

---

## 9. 变更日志

| 日期 | 版本 | 变更 | 作者 |
|---|---|---|---|
| 2026-05-17 | v0.1 | 初始化 7 张核心表 DDL | 项目组 |
