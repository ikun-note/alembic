# Alembic Lab

方案探究项目: 以 FastAPI + React 全栈参考应用为载体, 验证 Alembic 在 PostgreSQL 上的数据库管理与数据迁移. 后端提供数据读写 API, 前端做数据录入与查看, 迁移由 CLI 驱动.

- 设计文档 (需求 / 架构 / 测试 / issue): `.docs/`
- 迁移操作与发版指南: `docs/`

## 前置

- Python 3.12+ 与 [uv](https://docs.astral.sh/uv/)
- [podman](https://podman.io/) (docker 同理, 命令替换即可)
- Node.js 20+ 与 pnpm

## 快速开始

后端:

```bash
cd backend
cp .env.example .env                   # 填 POSTGRES_PASSWORD 与连接参数
uv sync                                # 安装依赖, 生成 .venv
```

数据库 (从项目根目录, 密码从 backend/.env 注入):

```bash
podman compose --env-file backend/.env -f .dev/compose.yaml up -d
```

迁移 (首次, 在 `backend/` 下):

```bash
uv run alembic revision --autogenerate -m "init articles"   # 生成建表迁移
uv run alembic upgrade head                                 # 应用, 建 articles 表
```

启动后端 (在 `backend/` 下):

```bash
uv run uvicorn app.main:app --reload    # http://localhost:8000
```

验证:打开 `http://localhost:8000/docs` 看 API, 或

```bash
curl http://localhost:8000/health        # 返回 {"status":"ok"}
```

前端:

```bash
cd frontend
pnpm install
pnpm run dev                             # http://localhost:5173, /api 代理到 :8000
```

shadcn 组件按需添加: `npx shadcn@latest add button input textarea`. lint / format: `pnpm run lint`、`pnpm run format` (oxlint + oxfmt).

## 配置分层

优先级 CLI > ENV > DEFAULT. 配置统一在 `backend/.env` (密钥 + 非密钥), 应用与 `migrations/env.py` 共用同一 Settings. 详见 `.docs/architectures/alembic-setup.md`.

## 文档

| 文档 | 内容 |
| --- | --- |
| `docs/migration-best-practices.md` | 从开发到上线: 多人分工 / 定版 / 上线 (建议先读) |
| `docs/development-migration.md` | 开发时的迁移控制: 状态 / 生成 / 升级 / 降级 / 数据迁移 / 离线 SQL / 重置 |
| `docs/release-migration.md` | 发版迁移: 多分支定版 / 升级回滚部署顺序 / roll forward / 迁移部署步骤 |
| `docs/multi-branch-migration-test.md` | 多分支迁移流程测试: feature/dev/v<n> 三分支, 多次结构变更的累积与流转 |
| `.docs/` | 需求 / 架构 / 测试 / issue |

## 目录

```
.dev/        PostgreSQL 容器编排
backend/     FastAPI + SQLAlchemy + Alembic + psycopg3
frontend/    React + Vite + TypeScript + Tailwind v4 + shadcn/ui
docs/        迁移操作与发版指南
.docs/       需求 / 架构 / 测试 / issue
```
