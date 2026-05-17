# 编码规范 · 拼豆小程序 v0.1

```yaml
文档名: Coding Standards - 拼豆小程序
版本: v0.1（骨架）
最后更新: 2026-05-17
关联文档: AGENTS.md §1.4 / 04-system-architecture.md
关联 ADR: ADR-002（技术栈）
```

---

## 0. 文档说明

> 单人项目的编码规范不是给"团队对齐"用的，是给"未来的我"和"AI 代理"用的。  
> 核心目标：**半年后回看代码不迷路 + AI 代理产出代码风格一致**。

---

## 1. 通用原则

### 1.1 写代码三问

每写一个函数前问自己：
1. **它的职责是单一的吗？**（一个函数干两件事是噩梦的开始）
2. **半年后我看到这个名字，能猜到它干什么吗？**
3. **它的输入输出是显式的吗？**（不要靠副作用沟通）

### 1.2 注释规则

- ✅ 写**为什么**这样做（业务逻辑、关键决策）
- ❌ 不写**做什么**（代码本身已经说了）
- ✅ 关联 ADR：`# 关联 ADR-004：MVP 仅 Mard 色卡`
- ✅ TODO 必须带责任人和时间：`# TODO(me, 2026-Q3): 重构为微服务`

---

## 2. Git 工作流（关联 AGENTS.md §1.4）

### 2.1 单人项目精简流程

```
直接在 main 分支开发
    ↓
完成功能 → git diff 自查 → commit
    ↓
（如果 > 200 行）立即 push
    ↓
重大变更打 git tag v*.*.*
```

### 2.2 Conventional Commits 规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**type 枚举**：
| type | 用途 |
|---|---|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档 |
| `refactor` | 重构（不改行为） |
| `perf` | 性能优化 |
| `test` | 测试 |
| `chore` | 构建/工具 |
| `style` | 格式化（不改逻辑） |

**scope 枚举**（按本项目目录）：
- `algo` 算法
- `api` 后端 API
- `mp` 小程序
- `db` 数据库迁移
- `agents` AGENTS.md
- `prd` PRD
- `arch` 架构

**例子**：
```
feat(algo): 新增 LED 指令生成模块

为 Phase 3 IoT 智能板支持，将像素矩阵转化为 BLE 数据帧序列。

关联 ADR-005
```

### 2.3 commit 大小约束

参考 AGENTS.md §1.5：
- ≤ 200 行：正常提交
- 200~500 行：完成立即 push
- > 500 行：拆成多个 commit

---

## 3. Python 规范（后端 / 算法）

### 3.1 工具链

| 工具 | 用途 | 配置文件 |
|---|---|---|
| `uv` | 包管理 + 虚拟环境 | `pyproject.toml` + `uv.lock` |
| `ruff` | Lint + Format | `pyproject.toml` |
| `pytest` | 单元测试 | `pyproject.toml` |
| `mypy` | 类型检查（严格模式） | `pyproject.toml` |
| `pre-commit` | 提交前钩子 | `.pre-commit-config.yaml` |

### 3.2 ruff 关键配置（v0.1 草案）

```toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = [
  "E", "F", "W",   # pycodestyle / pyflakes
  "I",              # isort
  "N",              # naming
  "B",              # bugbear
  "UP",             # pyupgrade
  "SIM",            # simplify
  "RUF",            # ruff-specific
]
ignore = ["E501"]  # 行长由 formatter 控制
```

### 3.3 命名约定

| 类别 | 风格 | 示例 |
|---|---|---|
| 模块/包 | snake_case | `pattern_service.py` |
| 类 | PascalCase | `PatternGenerator` |
| 函数/变量 | snake_case | `generate_pattern()` |
| 常量 | UPPER_SNAKE | `MAX_COLOR_COUNT = 40` |
| 私有 | 前导下划线 | `_internal_helper()` |
| 类型别名 | PascalCase | `PixelMatrix = list[list[int]]` |

### 3.4 类型注解（强制）

```python
# ✅ 好
def generate_pattern(
    image_url: str,
    grid_size: tuple[int, int],
    max_colors: int = 8,
) -> PatternResult:
    ...

# ❌ 差
def generate_pattern(image_url, grid_size, max_colors=8):
    ...
```

> **所有公开函数必须有类型注解**，私有函数推荐有。

### 3.5 项目结构（FastAPI 后端）

```
backend/
├── pyproject.toml
├── uv.lock
├── src/
│   └── pindou/
│       ├── __init__.py
│       ├── main.py                  # FastAPI app 入口
│       ├── config.py                # 配置（pydantic-settings）
│       ├── core/
│       │   ├── auth.py
│       │   ├── db.py
│       │   ├── redis.py
│       │   └── exceptions.py
│       ├── api/
│       │   └── v1/
│       │       ├── auth.py
│       │       ├── patterns.py
│       │       └── orders.py
│       ├── domain/                  # 业务模型（Pydantic）
│       │   ├── pattern.py
│       │   └── order.py
│       ├── services/                # 业务逻辑
│       │   ├── pattern_service.py
│       │   └── order_service.py
│       ├── repositories/            # 数据访问
│       │   ├── pattern_repo.py
│       │   └── order_repo.py
│       ├── algo/                    # 算法引擎
│       │   ├── pipeline.py
│       │   ├── cutout.py
│       │   ├── quantize.py
│       │   └── color_map.py
│       └── utils/
└── tests/
    ├── unit/
    └── integration/
```

> **分层原则**：`api → service → repository → db`，不允许跨层跳调。

---

## 4. 前端规范（uni-app + Vue3）

### 4.1 工具链

| 工具 | 用途 |
|---|---|
| `pnpm` | 包管理 |
| `vite` | 构建 |
| `eslint` + `@antfu/eslint-config` | Lint |
| `prettier` | Format |
| `vitest` | 单元测试 |
| `typescript` | 类型 |

### 4.2 命名约定

| 类别 | 风格 | 示例 |
|---|---|---|
| 组件文件 | PascalCase | `PinPixelGrid.vue` |
| 组件目录 | kebab-case | `components/pin-pixel-grid/` |
| 页面 | kebab-case | `pages/pattern-preview/index.vue` |
| 函数/变量 | camelCase | `generatePattern()` |
| Composable | use + camelCase | `usePatternStore()` |
| 类型 | PascalCase | `interface Pattern { ... }` |

### 4.3 项目结构

```
miniapp/
├── package.json
├── pnpm-lock.yaml
├── src/
│   ├── App.vue
│   ├── main.ts
│   ├── pages/                       # 页面（uni-app 约定）
│   │   ├── home/index.vue
│   │   ├── upload/index.vue
│   │   └── pattern-preview/index.vue
│   ├── components/                  # 通用组件（Pin- 前缀）
│   │   ├── PinButton/
│   │   ├── PinPixelGrid/
│   │   └── PinColorChip/
│   ├── composables/                 # 组合式函数
│   │   ├── useAuth.ts
│   │   └── usePattern.ts
│   ├── stores/                      # Pinia stores
│   │   ├── user.ts
│   │   └── cart.ts
│   ├── api/                         # API 封装
│   │   ├── client.ts
│   │   ├── patterns.ts
│   │   └── orders.ts
│   ├── types/                       # 全局类型
│   │   └── index.ts
│   ├── utils/
│   └── styles/
├── pages.json                       # uni-app 路由
└── manifest.json                    # uni-app 平台配置
```

### 4.4 组件规范

- **单文件组件 (SFC)** 强制 `<script setup lang="ts">`
- **props/emits** 用 TypeScript interface 声明
- **样式** 默认 `<style scoped>`，全局样式放 `styles/`

```vue
<script setup lang="ts">
interface Props {
  patternId: number
  editable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  editable: false,
})

const emit = defineEmits<{
  cellChange: [x: number, y: number, colorId: number]
}>()
</script>
```

---

## 5. 数据库与迁移规范

### 5.1 工具链
- **Alembic**（SQLAlchemy 配套）管理 schema 迁移
- 迁移文件按时间戳命名：`20260517_001_init_users.py`
- 一次迁移只做一件事

### 5.2 命名约定

| 对象 | 风格 | 示例 |
|---|---|---|
| 表名 | snake_case 复数 | `users` `bead_skus` |
| 字段 | snake_case | `created_at` `px_balance` |
| 索引 | `idx_<table>_<col>` | `idx_orders_status` |
| 外键 | `fk_<table>_<ref>` | `fk_orders_user_id` |
| 唯一约束 | `uq_<table>_<col>` | `uq_users_openid` |

### 5.3 迁移流程

```bash
# 修改模型后
alembic revision --autogenerate -m "add px_ledger table"

# 检查生成的迁移文件，必须人工 review
# 然后执行
alembic upgrade head
```

> **生产环境迁移前必须备份**，且 schema 变更必须向后兼容（先加字段，再废弃旧字段）。

---

## 6. 测试规范

### 6.1 测试金字塔

```
       E2E (5%)         <- Playwright（关键链路）
      ─────────
   Integration (25%)    <- pytest + httpx（API 层）
  ─────────────────
 Unit Tests (70%)       <- pytest / vitest（业务逻辑）
```

### 6.2 单元测试约定

- 测试文件：`test_<module>.py` / `<module>.test.ts`
- 命名：`test_<功能>_<场景>_<期望>`
  - `test_generate_pattern_with_easy_mode_returns_8_colors`

### 6.3 必须有测试的场景

- ✅ 算法管线每一步（输入 → 输出可验证）
- ✅ 订单状态机所有转换
- ✅ 支付回调验签
- ✅ PX 积分流水（涉及钱）
- ⏳ UI 组件（按需）

---

## 7. 安全规范

### 7.1 永远不要

- ❌ 在 git 中提交密钥/Token（用 `.env` + `.gitignore`）
- ❌ 在日志中打印手机号、身份证号、支付流水原文
- ❌ 信任用户输入（前后端双重校验）
- ❌ 用 RGB 欧氏距离做色彩匹配（用 CIE Lab，关联算法规范 §3.5）

### 7.2 必须

- ✅ 所有 API 加鉴权（除 webhook）
- ✅ 用户图片 24h 自动删除（隐私合规）
- ✅ 数据库连接强制 SSL
- ✅ 限流（Redis 令牌桶）

---

## 8. 日志与错误处理

### 8.1 结构化日志

```python
import structlog
log = structlog.get_logger()

log.info(
    "pattern_generated",
    pattern_id=pattern.id,
    user_id=user.id,
    grid_size=grid_size,
    color_count=color_count,
    duration_ms=elapsed,
)
```

### 8.2 错误码（关联 06-api-spec.md §1.3）

```python
class BizError(Exception):
    code: int
    message: str

class ImageTooLargeError(BizError):
    code = 10001
    message = "图片大小超出限制"
```

---

## 9. AI 代理产出代码的额外要求

> 单人项目大量代码会由 AI 代理产出，必须额外约束：

- ✅ AI 产出代码必须**通过 ruff/eslint 全部规则**才能 commit
- ✅ AI 产出函数必须**有类型注解 + docstring**
- ✅ AI 不得引入 `pyproject.toml` / `package.json` 之外的依赖
- ✅ AI 完成任务后主动跑 `git diff --stat`，触发 §1.5 规则
- ❌ AI 不得用占位符（如 `pass # TODO`），必须实现完整逻辑

---

## 10. 待补完成项

- [ ] `pyproject.toml` 完整配置文件
- [ ] `eslint.config.js` 完整配置文件
- [ ] `.pre-commit-config.yaml`
- [ ] 性能基准（每个 API P95 目标）
- [ ] 代码安全扫描配置（bandit / npm audit）

---

## 11. 变更日志

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-05-17 | v0.1 | 初始化编码规范，覆盖 Python / 前端 / DB / 测试 / AI 协作 |
