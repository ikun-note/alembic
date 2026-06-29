# Alembic Lab

方案探究项目: 以 FastAPI + React 全栈参考应用为载体, 验证 Alembic 在 PostgreSQL 上的数据库管理与数据迁移. 后端提供数据读写 API, 前端做数据录入与查看, 迁移由 CLI 驱动. 详细设计见 `.docs/`.

## 前置

- Python 3.12+ 与 [uv](https://docs.astral.sh/uv/)
- [podman](https://podman.io/) (docker 同理, 命令替换即可)
- Node.js 20+ 与 npm

## 后端

```bash
cd backend
cp config.example.toml config.toml     # 非密钥配置
cp .env.example .env                   # 填入 POSTGRES_PASSWORD
uv sync                                # 安装依赖, 生成 .venv
```

## 数据库

从项目根目录运行 (密码从 backend/.env 注入, 单一来源):

```bash
podman compose --env-file backend/.env -f .dev/compose.yaml up -d
podman compose -f .dev/compose.yaml down -v    # 销毁卷, 全新库
```

## 迁移操作

迁移是独立的 Alembic CLI 操作, 通过 `migrations/env.py` 自建的 engine 直连数据库, **不依赖 FastAPI 应用运行**. 建议在应用未运行时执行迁移, 避免请求进行中改表造成 schema 漂移. 所有命令在 `backend/` 下用 `uv run` 执行, 连接串由 Settings 构造, `alembic.ini` 不含密钥.

典型流程: 改模型 → 生成迁移 → 检查 `upgrade()`/`downgrade()` → `upgrade` → 验证; 出错则 `downgrade` 修正后重新生成.

### 查看状态

```bash
uv run alembic current          # 数据库当前停在哪个版本
uv run alembic history          # 版本链 (降序)
uv run alembic heads            # 分支头; 多于一个说明存在分叉
```

### 生成迁移

模型 (`backend/app/models/`) 改动后, 生成迁移脚本到 `migrations/versions/`:

```bash
uv run alembic revision --autogenerate -m "add status to articles"   # 基于模型 diff 自动生成
uv run alembic revision -m "manual data backfill"                     # 空脚本, 全手写
```

自动生成后**务必检查**脚本内容, 尤其是默认值、索引、外键、枚举类变更. `compare_type` 与 `compare_server_default` 已在 `env.py` 开启, 但 autogenerate 不保证完全准确, 数据迁移部分必须手写.

### 升级

```bash
uv run alembic upgrade head            # 升到最新
uv run alembic upgrade +1              # 前进一版
uv run alembic upgrade <revision>      # 升到指定版本
```

### 降级

```bash
uv run alembic downgrade -1            # 回退一版
uv run alembic downgrade <revision>    # 回退到指定版本
uv run alembic downgrade base          # 回退到初始 (撤销所有迁移)
```

### 升级与回滚: 与代码部署的配合

**升级 (前向, 低风险)**: 新结构是增量的. 部署新代码 → 迁移向前跑 (`alembic upgrade head`, 作为部署一步或 init container) → 启动应用. 不丢数据.

**回滚 (需谨慎, 顺序反着来)**: 不能直接拿旧代码覆盖. 正确做法是**先用当前 (新) 代码把迁移降回去, 再部署旧代码**:

```bash
uv run alembic downgrade <target>   # 仍在当前 (新) 代码环境里执行
# 降级完成后再切回旧代码部署
```

原因: `downgrade()` 只存在于**新**版本的迁移文件里, 旧代码的迁移历史不含这条 revision, 自己无法反向. 所以必须趁新代码还在时降回去, 再换旧代码.

折中方案: 只回滚代码、保留新结构 (旧代码需能容忍多余列). 适合结构无破坏性、旧 ORM 能忽略新增列的场景.

**"新增字段降级后没了" 怎么处理**: 这是结构降级的固有特性, 不是 Alembic 缺陷. 新增列的迁移, 自动生成的 `downgrade()` 就是 `op.drop_column(...)`, Alembic 执行后 PostgreSQL 直接 `DROP COLUMN`, **该列及其数据被永久删除, 不可恢复**. Alembic 不会替你留底, 责任在迁移作者:

- 列里是**可重建的派生数据** (如回填的默认值): drop 无妨, 重新 upgrade 可再生.
- 列里是**用户产生的不可重建数据**: 降级会永久丢失; 要保留必须在 `downgrade()` 里先备份 (如导到另一张表), 否则别在生产做这类降级.

因此生产环境通常**只进不退**: 出问题靠写一个修复迁移 (roll forward), 而非 `downgrade`. 降级主要留给开发 / 测试.

### 数据迁移

结构变更之外, 数据回填 / 转换 / 清洗写在同一迁移的 `upgrade()` / `downgrade()` 内, 用 `op.execute()` 跑 SQL 或 `op.bulk_insert()` 批量写入. **每条数据变更都要在 `downgrade()` 写对应的反向操作**, 否则降级会留下脏数据.

```python
def upgrade():
    # 结构: 加列
    op.add_column("articles", sa.Column("status", sa.String(20), nullable=True))
    # 数据: 回填存量行
    op.execute("UPDATE articles SET status = 'draft' WHERE status IS NULL")
    # 收尾: 收紧约束
    op.alter_column("articles", "status", nullable=False)

def downgrade():
    op.drop_column("articles", "status")
```

数据量大的回填优先分批 (LIMIT/OFFSET 或键集分页), 避免长事务锁表.

### 离线 SQL (不连库)

生成可审 SQL, 用于人工 review 或受限环境执行, 不实际改动数据库:

```bash
uv run alembic upgrade head --sql
uv run alembic upgrade <rev1>:<rev2> --sql   # 指定区间的 SQL
```

### 分支合并

并行开发产生分叉时, 用合并迁移收口:

```bash
uv run alembic merge -m "merge branches" <rev_a> <rev_b>
```

### 重置与标记

```bash
# 重置到干净状态: 回退到底再升到顶
uv run alembic downgrade base && uv run alembic upgrade head

# 销毁数据库重建 (最快, 容器化场景常用)
podman compose -f .dev/compose.yaml down -v
podman compose --env-file backend/.env -f .dev/compose.yaml up -d
uv run alembic upgrade head

# 标记当前库为某版本但不执行迁移 (已有结构、只想对齐版本表时)
uv run alembic stamp head
```

迁移正确性与可逆性的完整验证矩阵见 `.docs/testing/migration-verification.md`.

## 运行应用

```bash
cd backend
uv run uvicorn app.main:app --reload    # http://localhost:8000, /docs 查看 API
```

## 前端

```bash
cd frontend
npm install
npm run dev                                      # http://localhost:5173, /api 代理到 :8000

# shadcn 组件按需添加
npx shadcn@latest add button input textarea

# lint / format (oxlint + oxfmt)
npm run lint
npm run format
```

## 配置分层

优先级 CLI > ENV > CONFIG > DEFAULT. 密钥只在 ENV (`backend/.env`), 非密钥在 `backend/config.toml`, 应用与 `migrations/env.py` 共用同一 Settings. 详见 `.docs/architectures/alembic-setup.md`.

## 目录

```
.dev/        PostgreSQL 容器编排
backend/     FastAPI + SQLAlchemy + Alembic + psycopg3
frontend/    React + Vite + TypeScript + Tailwind v4 + shadcn/ui
.docs/       需求 / 架构 / 测试 / issue
```
