# Alembic 探究项目技术方案

## 背景与目标

承接需求 `../requirements/alembic-exploration.md`. 本项目以一个标准全栈参考应用为载体, 验证 Alembic 在 PostgreSQL 上的数据库管理与数据迁移能力: 后端 FastAPI 提供数据读写 API, 前端 React 做数据录入与查看, Alembic 负责结构演进与数据迁移. 本方案回答: 仓库怎么组织、前后端怎么拆、配置怎么分层、迁移与应用如何协作.

## 方案概览

- 单仓双目录: `backend/` 与 `frontend/`, 共用 `.dev/` 的 PostgreSQL 16 (podman)
- 后端: FastAPI + SQLAlchemy 2.x + Alembic + psycopg3; 配置走 `config.toml` (非密钥) + `.env` (密钥)
- 前端: React + Vite + TypeScript + Tailwind + shadcn/ui; 只做数据录入与查看, 不触发迁移
- 迁移探究四块 (基础配置 / 自动生成与 Schema 迁移 / 数据迁移 / 进阶) 在真实应用里被使用和验证
- 同步为主线, 异步 env.py 作进阶示例, 统一 psycopg3

## 模块职责

| 模块 | 职责 | 不负责 |
| --- | --- | --- |
| `.dev/` | podman compose 编排 PG 容器, 提供可重建数据库 | 不承载应用代码 |
| `backend/app/core/config` | 合并 DEFAULT + TOML + ENV, 输出单一 Settings | 不执行迁移、不处理 HTTP |
| `backend/app/db` | engine 与 session 工厂 | 不定义模型 |
| `backend/app/models` | SQLAlchemy 模型与 MetaData 命名约定 | 不含迁移逻辑、不含 HTTP |
| `backend/app/schemas` | Pydantic 请求 / 响应 DTO | 不触碰数据库 |
| `backend/app/api` | FastAPI 路由, 提供 CRUD | 不含业务规则细节 |
| `backend/app/services` | 业务规则与数据操作 | 不直接暴露 HTTP |
| `backend/migrations/env.py` | 从 Settings 构造 engine, 装配 autogenerate 上下文, 执行迁移 | 不定义模型 |
| `backend/migrations/versions` | 存放迁移脚本 | 不存运行时配置 |
| `backend/alembic.ini` | 承载 Alembic 非密钥配置 | 不存连接串与密码 |
| `frontend/` | 数据录入与查看 UI, 调用后端 API | 不触发迁移、不含业务规则 |

## 关键结构

~~~text
Alembic/
├── .dev/
│   └── compose.yaml              # podman compose 起 postgres:16
├── backend/
│   ├── pyproject.toml
│   ├── config.toml               # CONFIG 层, 非密钥应用配置
│   ├── config.example.toml       # 配置模板 (提交)
│   ├── .env                      # 密钥 (gitignore)
│   ├── alembic.ini               # sqlalchemy.url 留空
│   ├── migrations/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── app/
│   │   ├── main.py               # FastAPI 入口
│   │   ├── core/config.py        # pydantic-settings 读 TOML + .env
│   │   ├── db/                   # engine, session
│   │   ├── models/               # SQLAlchemy
│   │   ├── schemas/              # Pydantic DTO
│   │   ├── api/                  # 路由
│   │   └── services/
│   └── tests/
└── frontend/
    ├── package.json
    ├── vite.config.ts
    └── src/
~~~

## 关键流程

### 应用读写数据

1. `podman compose up` 起 PG, 连接参数从 `.env` 注入
2. `Settings` 读取 DEFAULT + `config.toml` + `.env`, 校验汇总为单一对象
3. FastAPI 启动, 依赖注入 session, 路由经 services 操作模型
4. 前端经 API 增删改查数据

### 迁移演进

1. 模型变更后, 在 `backend/` 执行 `alembic revision --autogenerate`
2. `env.py` 用 Settings 构造 engine, 生成迁移到 `versions/`
3. `alembic upgrade head` 在线执行; `--sql` 生成离线 SQL
4. 前端录入的数据成为迁移作用对象, 迁移后在 UI / DB 观察影响

## 设计原则与约束

- 密钥不落盘: 密码只在 ENV 层, 不进 `config.toml`、`alembic.ini` 与代码
- 单一配置对象: DEFAULT + TOML + ENV 汇总到 Settings, 应用与 env.py 共用同一来源
- 配置分层优先级: CLI > ENV > CONFIG (`config.toml` / `alembic.ini`) > DEFAULT
- 迁移与模型分离: 模型在 `app/models`, 迁移在 `migrations/versions`
- 命名稳定: MetaData 配 naming_convention, 约束名可复现
- 前端不触发迁移: 迁移由 CLI 负责, 前端仅读写数据
- 可重建环境: PG 容器化, 随时销毁重建不丢代码

## 取舍与风险

| 主题 | 结论 | 影响 |
| --- | --- | --- |
| 单仓双目录 vs workspace | 单仓双目录 | 共用文档与 PG, 维护简单; 缺少 workspace 级跨包联动 |
| 配置文件 TOML vs YAML vs 纯 .env | TOML | Python 原生、与 pyproject 一致; YAML 更通用但多一种格式 |
| 前端不触发迁移 | 迁移走 CLI | 避免应用运行时执行迁移的反模式; 升级验证靠"录入 → 迁移 → 观察" |
| 同步为主 vs 全异步 | 同步主线 + 异步进阶 | 上手简单; 异步仅作示例 |
| psycopg3 vs asyncpg | 统一 psycopg3 | 同步异步同驱动; 极致性能场景 asyncpg 更优, 探究不需要 |
| 前端仅录入查看 | 不做迁移管理台 | 范围收敛; 如需触发迁移再扩展管理 API |
| `alembic.ini` 留空 url | env.py 构造 | 密钥安全; 需保证 env.py 与 Settings 一致 |
