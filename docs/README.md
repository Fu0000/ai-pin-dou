# 拼豆项目 · 文档总索引

> 这里是项目所有文档的**单一入口**。新成员入职、跨团队协作、外部评审，都从这里开始。

---

## 📚 文档体系全景图

拼豆项目采用 **10 层文档体系**，每一层解决一个层级的"对齐"问题：

```
L0  战略层 ─── 为什么做、做什么、何时做、决策记录
L1  产品层 ─── 用户、需求、功能规格
L2  设计层 ─── 视觉、交互、原型
L3  技术层 ─── 架构、API、数据、算法
L4  多端协作层 ─ 小程序、后端、IoT、B端 SaaS
L5  质量层 ─── 编码规范、测试
L6  数据层 ─── 埋点、指标、看板
L7  运维层 ─── 部署、监控、应急
L8  合规层 ─── 隐私、协议、内容审核
L9  运营层 ─── 冷启动、客服、创作者
```

---

## 📂 文档目录

### L0 · 战略层（Why / What / When）✅ 已完成

| 文档 | 路径 | 说明 | 状态 |
|---|---|---|---|
| 战略规划 | [`/guihua.md`](../guihua.md) | 商业判断、需求洞察、市场逻辑 | ✅ v1.0 |
| 研发计划 | [`/project-plan.md`](../project-plan.md) | 5 阶段战略 + 4 Phase 周级计划 | ✅ v1.0 |
| 流程与里程碑 | [`/project-flow-and-milestones.md`](../project-flow-and-milestones.md) | 端到端流程图 + Go/No-Go 决策门 | ✅ v1.0 |
| 决策变更日志（ADR） | [`/decision-log.md`](../decision-log.md) | 10 条决策基线 + 10 条 TBD | ✅ v1.0 |

### L1 · 产品层（What）

| 文档 | 路径 | 说明 | 状态 |
|---|---|---|---|
| 产品需求文档（PRD） | [`./01-prd.md`](./01-prd.md) | MVP 功能粒度 + 用户故事 + 验收标准 | 🟡 v0.1 骨架 |
| 用户画像 | [`./02-personas.md`](./02-personas.md) | 5 类核心用户的画像与诉求 | ⬜ 待创建（M0） |
| 用户旅程图 | （并入 flow-milestones） | 端到端用户流程 | ✅ 已在 L0 |

### L2 · 设计层（How looks）

| 文档 | 路径 | 说明 | 状态 |
|---|---|---|---|
| 设计系统 | [`./03-design-system.md`](./03-design-system.md) | 色板、字体、组件、栅格 | 🟡 v0.1 骨架 |
| 信息架构 + 原型 | （PRD 内含） | 站点地图与线框 | ⬜ 待创建（W1） |

### L3 · 技术层（How works）

| 文档 | 路径 | 说明 | 状态 |
|---|---|---|---|
| 系统架构 | [`./04-system-architecture.md`](./04-system-architecture.md) | 服务拓扑、数据流、部署 | 🟡 v0.1 骨架 |
| 数据模型 | [`./05-data-model.md`](./05-data-model.md) | 核心 6 张表 DDL | 🟡 v0.1 骨架 |
| API 契约 | [`./06-api-spec.md`](./06-api-spec.md) | OpenAPI 风格接口规范 | 🟡 v0.1 骨架 |
| 算法工程规范 | [`./07-algo-spec.md`](./07-algo-spec.md) | 输入/输出/参数/版本管理 | ⬜ 待创建（W1） |

### L4 · 多端协作层

| 文档 | 路径 | 说明 | 状态 |
|---|---|---|---|
| 小程序双端适配 | [`./08-miniapp-spec.md`](./08-miniapp-spec.md) | 微信 vs 抖音差异点 | ⬜ 待创建（W2） |
| IoT 通信协议 | [`./09-iot-protocol.md`](./09-iot-protocol.md) | BLE 数据帧规范 | ⬜ 待创建（Phase 2 末） |
| B 端 SaaS 规范 | [`./10-saas-spec.md`](./10-saas-spec.md) | 多租户/权限模型 | ⬜ 待创建（Phase 2） |

### L5 · 质量层

| 文档 | 路径 | 说明 | 状态 |
|---|---|---|---|
| 编码规范 + Git 工作流 | [`./11-coding-standards.md`](./11-coding-standards.md) | 命名、分支、提交、Review | ⬜ 待创建（W1） |
| 测试计划 | [`./12-test-plan.md`](./12-test-plan.md) | 测试策略 + 核心用例 | ⬜ 待创建（W3） |

### L6 · 数据层

| 文档 | 路径 | 说明 | 状态 |
|---|---|---|---|
| 埋点规范 | [`./13-tracking-spec.md`](./13-tracking-spec.md) | 事件命名、参数、上报格式 | ⬜ 待创建（W2） |
| 指标字典 | [`./14-metrics-dict.md`](./14-metrics-dict.md) | 北极星 + 核心指标定义 | ⬜ 待创建（W2） |
| 数据看板设计 | [`./15-dashboard.md`](./15-dashboard.md) | 周/月度看板布局 | ⬜ 待创建（Phase 2） |

### L7 · 运维层

| 文档 | 路径 | 说明 | 状态 |
|---|---|---|---|
| 部署运维手册 | [`./16-deployment.md`](./16-deployment.md) | 环境/发布/回滚流程 | ⬜ 待创建（W5） |
| 监控告警 | [`./17-monitoring.md`](./17-monitoring.md) | 监控项 + 告警阈值 | ⬜ 待创建（W5） |
| 故障应急（Runbook） | [`./18-runbook.md`](./18-runbook.md) | 常见故障处置 SOP | ⬜ 待创建（Phase 1 末） |

### L8 · 合规层

| 文档 | 路径 | 说明 | 状态 |
|---|---|---|---|
| 隐私政策 | [`./19-privacy-policy.md`](./19-privacy-policy.md) | 用户数据使用条款 | ⬜ 待创建（W4） |
| 用户协议 | [`./20-user-agreement.md`](./20-user-agreement.md) | 服务使用条款 | ⬜ 待创建（W4） |
| 内容审核 SOP | [`./21-content-moderation.md`](./21-content-moderation.md) | UGC/代拼图纸审核流程 | ⬜ 待创建（Phase 2 W1） |
| 安全合规清单 | [`./22-safety-checklist.md`](./22-safety-checklist.md) | SGS / 警示 / 资质 | ⬜ 待创建（W3） |

### L9 · 运营层

| 文档 | 路径 | 说明 | 状态 |
|---|---|---|---|
| 冷启动运营 SOP | [`./23-cold-start.md`](./23-cold-start.md) | KOL 投放 / 灰度 / 监控 | ⬜ 待创建（Phase 1 末） |
| 客服 FAQ | [`./24-customer-service.md`](./24-customer-service.md) | 常见问题 + 处理话术 | ⬜ 待创建（Phase 1 末） |
| 创作者运营手册 | [`./25-creator-playbook.md`](./25-creator-playbook.md) | 招募 / 激励 / 培训 | ⬜ 待创建（Phase 2） |

---

## 🟢 状态图例

| 标记 | 含义 |
|---|---|
| ✅ | 已完成（v1.0+） |
| 🟡 | 骨架已建（v0.1，需要负责人填充内容） |
| ⬜ | 待创建（按计划时间启动） |
| 🔄 | 重大修订中 |
| ⛔ | 已废弃 |

---

## 📐 文档使用规范

### 1. 每份文档必须有的"五件套"

每份文档顶部必须有以下 metadata：

```yaml
文档名: <名称>
版本: v0.1
状态: 草稿 / 评审中 / 已通过
Owner: <姓名 + 角色>
Reviewers: <评审人列表>
最后更新: YYYY-MM-DD
下次复盘: YYYY-MM-DD
关联文档: <列出依赖的其他文档>
关联 ADR: <如有>
```

### 2. 文档之间必须互相超链接

所有引用其他文档的地方都用 markdown 链接，**不要写"详见某某文档"这种没有跳转的描述**。

### 3. 不追求一次写完美

- v0.1：骨架（结构 + 已知信息 + 明确的 TODO 块）
- v0.5：填充完成 80%
- v1.0：评审通过、可以执行

### 4. 重大变更必须走 ADR

任何文档的核心决策变更（如技术栈替换、流程改造、定价调整），必须先在 [`/decision-log.md`](../decision-log.md) 立 ADR，再修订文档本身。

### 5. 每份文档必须定期复盘

- 高频文档（PRD、API、数据模型）：每周复盘
- 中频文档（架构、设计系统、埋点）：每两周复盘
- 低频文档（合规、运营手册）：每月复盘

---

## 🚀 新成员入职阅读清单（按顺序读 1 小时即可上手）

1. [`/guihua.md`](../guihua.md)（10 min）—— 我们在做什么
2. [`/project-flow-and-milestones.md`](../project-flow-and-milestones.md)（10 min）—— 用户怎么用 + 我们怎么交付
3. [`/decision-log.md`](../decision-log.md)（10 min）—— 关键决策的来龙去脉
4. [`./01-prd.md`](./01-prd.md)（10 min）—— 当前 Sprint 在做什么
5. [`./04-system-architecture.md`](./04-system-architecture.md)（10 min）—— 技术全貌
6. [`./11-coding-standards.md`](./11-coding-standards.md)（10 min）—— 怎么提交代码

---

## 📊 文档健康度（每月更新）

| 维度 | 当前 | 目标 |
|---|---|---|
| 已完成（v1.0）数量 | 4 / 25 | M1 时 ≥ 12 / 25 |
| 骨架（v0.1）数量 | 6 / 25 | M0 启动前 ≥ 10 / 25 |
| 平均"最后更新"距今 | — | ≤ 14 天 |
| 文档评审会执行率 | — | ≥ 90% |

---

## 📝 文档变更日志

| 日期 | 版本 | 变更内容 | Owner |
|---|---|---|---|
| 2026-05-17 | v0.1 | 初始化文档体系，建立 6 份骨架 | 项目组 |
