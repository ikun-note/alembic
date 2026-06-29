# Alembic 全栈探究

方案探究项目: 以 FastAPI + React 全栈参考应用为载体, 验证 Alembic 在 PostgreSQL 上的数据库管理与数据迁移. 不接入真实业务, 迁移示例围绕 Article 载体模型演进.

设计依据见 `.docs/`: 需求 `requirements/alembic-exploration.md`、架构 `architectures/alembic-setup.md`、测试 `testing/migration-verification.md`、实施 `issues/feature/alembic-pg-exploration/`.

## 目录结构

~~~text
Alembic/
├── .dev/compose.yaml          # podman compose 起 postgres:16
├── .docs/                     # 需求 / 架构 / 测试 / issue 文档
├── backend/                   # FastAPI + SQLAlchemy + Alembic + psycopg3
│   ├── config.toml            # 非密钥应用配置 (CONFIG 层)
│   ├── config.example.toml    # 配置模板 (提交)
│   ├── .env                   # 密钥 (gitignore)
│   ├── alembic.ini            # sqlalchemy.url 留空
│   ├── migrations/            # env.py + versions/
│   └── app/                   # main / core / db / models / schemas / api / services
└── frontend/                  # React + Vite + TypeScript + Tailwind + shadcn/ui
~~~

## 技术栈

- 后端: Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, psycopg3
- 前端: React + Vite + TypeScript + Tailwind + shadcn/ui
- 数据库: PostgreSQL 16 (podman 容器化, 配置在 `.dev/`)

## 配置分层

优先级 CLI > ENV > CONFIG > DEFAULT. 密钥只在 ENV 层 (`.env`), 不落盘. 应用与 env.py 共用 pydantic-settings 的 Settings 对象, 同时读 `config.toml` 与 `.env`. 详见 `.docs/architectures/alembic-setup.md`.

## 常用命令

~~~bash
# 数据库
podman compose -f .dev/compose.yaml up -d
podman compose -f .dev/compose.yaml down -v   # 销毁卷, 得到全新库

# 后端迁移 (在 backend/)
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "describe change"
alembic upgrade head --sql                    # 离线 SQL, 不实际执行
~~~

## 约束

- 前端只做数据录入与查看, 不触发迁移; 迁移由开发者在 `backend/` 用 CLI 执行
- 迁移与模型分离: 模型在 `backend/app/models`, 迁移在 `backend/migrations/versions`
- MetaData 配 naming_convention, 约束名需稳定可复现
- 文档 CRUD 与 issue 状态走 docsctl, 规则见 `.claude/skills/docs-repo`
- 安全红线与输出约束见 `.claude/rules/`
