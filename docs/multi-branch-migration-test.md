# 多分支迁移流程测试

验证 `feature` / `dev` / `v<n>` 三分支下,
多次结构变更提交的迁移能正确累积、保持线性、随合并流转。
存储用 PostgreSQL, 每个整链校验点用脚本化全新库重置。

> 迭代分支 = dev 分支 (本测试三分支拓扑)。

## 前提

- podman PG 已起, `backend/` 可跑 `uv run alembic`
- 校验整链时用全新库, 重置 (根目录):

  ```bash
  podman compose -f .dev/compose.yaml down -v
  podman compose --env-file backend/.env -f .dev/compose.yaml up -d
  ```

## 分支

- `feature`:开发者工作分支 (本测试单 feature, 3 次结构变更提交)
- `dev`:集成分支 (= 迭代分支)
- `v<n>`:版本分支, 如 `v1`

## 步骤 0: 基线 R0

dev 上生成基线迁移 (建 `articles` 表), 并切出 feature 与 v<n>:

```bash
git checkout dev
cd backend
uv run alembic revision --autogenerate -m "init articles"
uv run alembic upgrade head
git commit -am "feat: init articles migration"

cd ..
git checkout -b v1          # v<n> 从基线切出
git checkout dev
git checkout -b feature     # feature 从 dev (R0) 切出
```

## 步骤 1: feature Commit 1 — 新建 tags 表

每次提交都**先同步 dev**, 保证迁移基于最新结构、`down_revision` 接在当前 head。

1. 同步 dev (本周期 dev 未动, 为 no-op;多人时这里会带入他人迁移):

   ```bash
   git merge dev
   cd backend && uv run alembic upgrade head
   ```

2. 新增 `Tag` 模型 (`app/models/tag.py`)。

3. 生成迁移:

   ```bash
   uv run alembic revision --autogenerate -m "add tags table"
   ```

4. **校验线性**:打开新迁移, `down_revision` 必须指向当前 head (`R0`);

   ```bash
   uv run alembic history      # 链为 R0 -> m1
   ```

5. **校验可逆** (当前库即可):

   ```bash
   uv run alembic upgrade head
   uv run alembic downgrade -1
   uv run alembic upgrade head
   ```

6. 提交并合并进 dev:

   ```bash
   git add -A && git commit -m "feat: add tags"
   git checkout dev && git merge feature
   ```

## 步骤 2: feature Commit 2 — articles 加 status 列

1. 回 feature, 同步 dev (带入步骤 1 的迁移):

   ```bash
   git checkout feature
   git merge dev
   cd backend && uv run alembic upgrade head
   ```

2. `Article` 加 `status` 字段。

3. 生成迁移 `add article status`。

4. 校验 `down_revision` = 当前 head (步骤 1 的 `m1`), `history` 链为 `R0 -> m1 -> m2`。

5. 校验可逆 (upgrade → downgrade -1 → upgrade)。

6. 提交、合并进 dev。

## 步骤 3: feature Commit 3 — articles 加 summary 列

同步骤 2:加 `summary` 字段, 生成迁移,
校验 `down_revision` 接步骤 2 head、`history` 链为 `R0 -> m1 -> m2 -> m3`、可逆,
合并进 dev。

## 步骤 4: dev 三次合并后校验

dev 现有 `R0 -> m1 -> m2 -> m3`, 单 head。
**全新库**验证整链:

```bash
git checkout dev
# (根目录) down -v && up -d 重置
cd backend
uv run alembic upgrade head      # 走完 R0..m3
uv run alembic current           # 指向 m3
uv run alembic heads             # 只有一个 head
uv run alembic downgrade base    # 全退
uv run alembic upgrade head      # 再升, 无残留
```

## 步骤 5: 合并到 v<n>

```bash
git checkout v1
git merge dev
```

**全新库**验证版本分支:

```bash
# (根目录) down -v && up -d 重置
cd backend
uv run alembic upgrade head                       # R0..m3
uv run alembic downgrade base && uv run alembic upgrade head
```

## 验收清单

- 全程 `alembic heads` 只有一个 head —— 线性, 无分叉。
- 每条迁移 `down_revision` 指向当时 dev head —— 基于最新结构。
- 每条迁移 upgrade → downgrade → upgrade 闭环无残留。
- dev 三次合并后, 整链 `upgrade head` / `downgrade base` 通过。
- `v<n>` 合并后全新库 `upgrade head` 通过, 结构与模型一致。
- 可选:在 `v<n>` 上做一次定版 squash, 见 `migration-best-practices.md` 阶段二。
