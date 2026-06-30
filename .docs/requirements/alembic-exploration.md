# Alembic + PostgreSQL 全栈探究

## 背景

本仓库为方案探究项目, 以一个标准全栈参考应用为载体, 验证 Alembic 在 PostgreSQL 上的数据库管理与数据迁移能力. 后端 FastAPI 提供数据读写 API, 前端 React 做数据录入与查看, Alembic 负责结构演进与数据迁移. 产出包括可运行代码与探究文档, 不接入真实业务数据.

## 目标

- 跑通 Alembic 在容器化 PG 上的完整链路: 初始化、自动生成、执行、回滚
- 以全栈应用为载体, 让迁移作用于真实数据, 可在前端观察迁移影响
- 沉淀 PostgreSQL 友好的配置基线: 配置统一 `.env`、命名约定、env.py 写法
- 覆盖 Schema 迁移、数据迁移与进阶能力, 每类均有可运行示例

## 用户流程 / 页面结构

### 数据录入流程

1. 前端打开数据录入页, 填写 Article 字段
2. 提交后调用后端 API, 经 schemas 校验、services 写入模型
3. 列表页刷新展示已录入数据

### 迁移验证流程

1. 通过前端录入若干条示例数据
2. 在 `backend/` 用 CLI 执行迁移 (`alembic upgrade head` 等)
3. 回到前端或 DB 观察结构与数据的变化, 验证迁移正确性与可逆性

## 功能要求

| 编号 | 说明 | 验收标准 |
| --- | --- | --- |
| FR-1 | 单仓结构与依赖 | `backend/`、`frontend/` 骨架就位, 各自依赖可装可跑 |
| FR-2 | PG 容器化环境 | podman compose 起 PG 16, 后端可连上 |
| FR-3 | 配置统一 | 配置统一在 `.env` (密钥不落配置文件); Settings 汇总 DEFAULT + ENV |
| FR-4 | 命名约定 | MetaData 配 naming_convention, 约束名稳定可读 |
| FR-5 | 后端 FastAPI CRUD + DTO | Article 增删改查 API 可用, 请求 / 响应经 Pydantic 校验 |
| FR-6 | 前端数据录入与查看 | 录入表单可新建 / 编辑, 列表可查看, 调用后端 API |
| FR-7 | Alembic 初始化与模型对接 | `alembic current` 能连库并返回版本状态 |
| FR-8 | 自动生成与检测 | autogenerate 生成正确迁移; 启用 compare_type / compare_server_default 检出类型与默认值变更 |
| FR-9 | 手写迁移 | 至少一个手写迁移示例, 说明自动生成不足时的处理 |
| FR-10 | 数据迁移与可逆 | 至少一个数据迁移示例, upgrade 后数据正确, downgrade 可还原 |
| FR-11 | 分支迁移合并 | 存在分支迁移, 合并后 upgrade 不冲突 |
| FR-12 | 离线 SQL | `alembic upgrade head --sql` 生成可审 SQL |
| FR-13 | 编程式 API | 代码内调用 API 完成 revision / upgrade, 等价 CLI |
| FR-14 | 异步 env.py | 异步 env.py 示例, 异步上下文 upgrade 可用 |

## 边界与约束

- 数据库限定 PostgreSQL 16, 由容器化提供
- 驱动统一 psycopg3, 不引入 asyncpg
- 配置优先级 CLI > ENV > DEFAULT, 密钥不进配置文件
- 前端只做数据录入与查看, 不触发迁移
- 以探究为主, 不追求生产级高可用、并发迁移锁、CI / CD 集成等运维深度
- 迁移示例围绕 Article 载体模型构造, 不接入真实业务

## 非目标

- 不构建面向终端用户的生产级产品
- 不做多租户、分库分表等架构级主题
- 不做迁移管理后台 (前端不触发迁移)
- 不把 Alembic 自身能力封装为重型框架
- 不覆盖 CI / CD 流水线集成 (留作后续独立主题)
