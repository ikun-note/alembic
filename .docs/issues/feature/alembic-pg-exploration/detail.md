# Alembic + PostgreSQL 全栈探究搭建

## 背景

本仓库为方案探究项目, 以标准全栈参考应用为载体, 验证 Alembic 在 PostgreSQL 上的数据库管理与数据迁移. 需求与验收见 `../../requirements/alembic-exploration.md`, 技术方案见 `../../architectures/alembic-setup.md`, 迁移验证见 `../../testing/migration-verification.md`. 后端 FastAPI 提供数据读写 API, 前端 React 做数据录入与查看, Alembic 负责结构演进与数据迁移. 本 issue 承载从骨架到四类迁移示例的完整实施方向.

## 目标

- 跑通 Alembic 在容器化 PG 上的完整链路: 初始化、自动生成、执行、回滚
- 以全栈应用为载体, 让迁移作用于真实数据, 可在前端观察迁移影响
- 沉淀 PostgreSQL 友好的配置基线: 配置统一 `.env`、命名约定、env.py 写法
- 覆盖 Schema 迁移、数据迁移与进阶能力, 每类均有可运行示例

## 范围

- 单仓双目录: `backend/` (FastAPI + SQLAlchemy + Alembic + psycopg3) 与 `frontend/` (React + Vite + TS)
- 容器化 PostgreSQL 16 (podman, 编排配置在 `.dev/`)
- 配置: 统一 `.env` (密钥 + 非密钥), pydantic-settings 读 .env
- 前端只做数据录入与查看, 迁移走 CLI
- 四类迁移示例: 基础配置、自动生成与 Schema 迁移、数据迁移、进阶 (分支 / 离线 / 编程式 / 异步)
- 迁移验证闭环: 录入数据 → CLI 迁移 → 前端 / DB 观察

## 非目标

- 不构建面向终端用户的生产级产品
- 不做生产级运维 (并发锁、高可用、CI / CD 集成)
- 不做迁移管理后台 (前端不触发迁移)
- 不接入真实业务数据
- 不引入 asyncpg, 驱动统一 psycopg3

## 方案讨论

### 配置分层

按 `basic-config-system` 的 layering 落地, 各层汇总到单一 Settings 对象:

- DEFAULT: 代码内兜底 (host、port、db name 等)
- ENV: `.env` 注入连接参数与密码 (应用配置统一在此); `.env` 入 gitignore, 提交 `.env.example`
- `alembic.ini`: Alembic 自身的非密钥配置 (script_location 等), 不含连接串与密码
- CLI: 单次执行的显式覆盖

密码属 Secret, 只在 ENV 层. 应用与 env.py 共用同一 Settings, 业务代码不零散读 env.

### 前后端协作

后端 FastAPI 经依赖注入 session, 路由 → services → models 完成数据读写, schemas 负责请求 / 响应校验. 前端只调 API 做录入与查看, 不触发迁移; 迁移演进由开发者在 `backend/` 用 CLI 完成. 迁移作用对象为前端录入的真实数据, 便于观察影响.

### 主线与迁移组织

同步为主线, 异步 env.py 作进阶示例, 统一 psycopg3. 模型在 `app/models`, 迁移在 `migrations/versions`, 二者分离. MetaData 配 naming_convention, 保证约束名稳定可复现.

## 风险与边界

| 主题 | 风险 / 边界 | 应对 |
| --- | --- | --- |
| env.py 与 Settings 不一致 | 连接失败 | Settings 为唯一来源, env.py 不重复拼参数 |
| 前后端契约漂移 | 录入 / 列表字段与模型不符 | schemas 与前端表单共用同一字段定义, 变更同步 |
| autogenerate 漏检 | 类型 / 默认值变更未检出 | 启用 compare_type、compare_server_default |
| 数据迁移不可逆 | downgrade 残留脏数据 | 数据迁移成对写 upgrade / downgrade, testing 闭环验证 |
| 容器依赖 | 需 podman 运行时 | 文档说明起停与复位命令 |

## 验收口径

- 按 `requirements/alembic-exploration.md` 的 FR-1 ~ FR-14 逐项满足
- 迁移验证按 `testing/migration-verification.md` 矩阵全部通过
- 全新库 upgrade 到 head 再 downgrade base 无残留、无报错
- 前端可录入数据并在迁移后观察到结构与数据变化
- 进阶示例 (分支 / 离线 / 编程式 / 异步) 各有可运行演示
