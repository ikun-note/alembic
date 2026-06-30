# 开发时的迁移控制

日常开发中用到的 Alembic 命令与数据迁移写法. 所有命令在 `backend/` 下用 `uv run` 执行. 迁移是独立的 CLI 操作, 通过 `migrations/env.py` 自建的 engine 直连数据库, **不依赖 FastAPI 应用运行**;建议在应用未运行时执行, 避免请求进行中改表造成 schema 漂移. 连接串由 Settings 构造, `alembic.ini` 不含密钥.

典型流程: 改模型 → 生成迁移 → 检查 `upgrade()`/`downgrade()` → `upgrade` → 验证; 出错则 `downgrade` 修正后重新生成.

## 查看状态

```bash
uv run alembic current          # 数据库当前停在哪个版本
uv run alembic history          # 版本链 (降序)
uv run alembic heads            # 分支头; 多于一个说明存在分叉
```

## 生成迁移

模型 (`backend/app/models/`) 改动后, 生成迁移脚本到 `migrations/versions/`:

```bash
uv run alembic revision --autogenerate -m "add status to articles"   # 基于模型 diff 自动生成
uv run alembic revision -m "manual data backfill"                     # 空脚本, 全手写
```

自动生成后**务必检查**脚本内容, 尤其是默认值、索引、外键、枚举类变更. `compare_type` 与 `compare_server_default` 已在 `env.py` 开启, 但 autogenerate 不保证完全准确, 数据迁移部分必须手写.

## 升级

```bash
uv run alembic upgrade head            # 升到最新
uv run alembic upgrade +1              # 前进一版
uv run alembic upgrade <revision>      # 升到指定版本
```

## 降级

```bash
uv run alembic downgrade -1            # 回退一版
uv run alembic downgrade <revision>    # 回退到指定版本
uv run alembic downgrade base          # 回退到初始 (撤销所有迁移)
```

**"新增字段降级后没了" 的处理**: 这是结构降级的固有特性, 不是 Alembic 缺陷. 新增列的迁移, 自动生成的 `downgrade()` 就是 `op.drop_column(...)`, Alembic 执行后 PostgreSQL 直接 `DROP COLUMN`, **该列及其数据被永久删除, 不可恢复**. Alembic 不会替你留底, 责任在迁移作者:

- 列里是**可重建的派生数据** (如回填的默认值): drop 无妨, 重新 upgrade 可再生.
- 列里是**用户产生的不可重建数据**: 降级会永久丢失; 要保留必须在 `downgrade()` 里先备份 (如导到另一张表), 否则别做这类降级.

## 数据迁移

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

## 离线 SQL (不连库)

生成可审 SQL, 用于人工 review 或受限环境执行, 不实际改动数据库:

```bash
uv run alembic upgrade head --sql
uv run alembic upgrade <rev1>:<rev2> --sql   # 指定区间的 SQL
```

## 重置与标记

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

迁移正确性与可逆性的完整验证矩阵见 `../.docs/testing/migration-verification.md`.
