# 迁移最佳实践: 从开发到上线

一个迭代里多名开发者分工、合并、最终上线的完整迁移流程,
**每个阶段给出具体人员操作**。
命令细节见 `development-migration.md`,
定版与部署机制见 `release-migration.md`。

## 心智模型

> **迁移是模型的派生产物**, 但 dev 环境要持续部署,
> 所以开发期就得提交真实迁移 (alpha);
> 发版时再把攒下的一批 alpha **衍合**成一条 rc。

环境与角色:

| 环境 / 角色 | 说明 |
| --- | --- |
| 本地库 | 开发者自测 |
| dev 环境 | 共享, 每次合并自动部署 + 自动 `upgrade head` |
| staging / prod | 发版产物上线, 只跑 rc 迁移 |
| 开发者 | 改模型 + 生成 alpha 迁移, 保持线性 |
| 发布者 | 定版:把 alpha 衍合成一条 rc |
| 运维 | 上线时迁移作独立步骤先跑 |

## 贯穿示例

上一正式版 `R_last`, 只有 `articles` 表。
本迭代三人并行, 各自生成并提交 alpha 迁移:

- **A** `feature/article-status`:给 `Article` 加 `status` 列
- **B** `feature/comments`:新增 `Comment` 模型 (新表)
- **C** `feature/title-length`:`Article.title` 长度 200 → 500

## 阶段一: 开发期 — 开发者操作

以 A (`feature/article-status`) 为例。

> **关键纪律:先把分支同步到 dev 最新, 再生成迁移。**
> autogenerate 把新迁移的 `down_revision` 设为本地库当前版本,
> 所以只要本地库在 dev head, 新迁移就自动接在 head 上、diff 也基于最新结构,
> 链天然线性。

1. 同步 dev 最新, 建分支:

   ```bash
   git checkout dev && git pull
   git checkout -b feature/article-status
   ```

2. 本地库升到当前 dev head
   (刚 pull 进来的新迁移也要应用, 否则 down_revision 会指错):

   ```bash
   cd backend
   uv run alembic upgrade head
   ```

3. 改模型 (`app/models/article.py`, 加 `status` 字段)。

4. 生成 alpha 迁移
   (此时 `down_revision` = 当前 dev head):

   ```bash
   uv run alembic revision --autogenerate -m "add article status"
   ```

5. 检查并补全迁移:
   - review `upgrade()` / `downgrade()`
   - 需要回填就在 upgrade 里加
     `op.execute("UPDATE articles SET status='draft' WHERE status IS NULL")`,
     downgrade 写反向

6. 本地验证可逆:

   ```bash
   uv run alembic upgrade head      # 应用
   uv run alembic downgrade -1      # 回退一版
   uv run alembic upgrade head      # 再升, 确认无残留
   ```

7. 提交模型 + 迁移:

   ```bash
   git add app/models/article.py migrations/versions/<新迁移>.py
   git commit -m "feat: add article status"
   ```

8. **合并前再同步一次** (期间可能有人合了新迁移):

   ```bash
   git fetch origin
   git rebase origin/dev
   ```

   - 若 rebase 带进了新迁移, 自己的迁移可能不再接在 head 上 ——
     把它的 `down_revision` 改指到新 head, 或删掉重新生成,
     保持线性。

9. 推送、提 PR;CI 校验 `alembic heads` 只有一个 head。

B、C 同理, 各自的 alpha 迁移依次接在链上
(`R_last -> alpha_A -> alpha_B -> alpha_C`)。

## 阶段一附: dev 环境持续部署 — CI/CD

每次 PR 合并进 dev 分支, 流水线自动:

1. 构建镜像、部署到 dev
2. 迁移作独立一步、先于应用:

   ```bash
   uv run alembic upgrade head
   ```

3. 重启 dev 应用、健康检查

dev 库逐条累计 alpha, 始终和 dev 分支模型一致。
这正是开发期必须提交真实迁移的原因 —— dev 等不到 rc。

## 阶段二: 定版 (alpha → rc) — 发布者

dev 分支攒了 `alpha_A..alpha_C`。发布者衍合成一条 rc:

1. 切到 release 分支 (PR 都已并入), 拉最新:

   ```bash
   git checkout release && git pull
   ```

2. 全新库, 升到上一发版基线:

   ```bash
   podman compose -f .dev/compose.yaml down -v
   podman compose --env-file backend/.env -f .dev/compose.yaml up -d
   cd backend && uv run alembic upgrade R_last
   ```

3. autogenerate 出聚合迁移
   (净 diff = status 列 + comments 表 + title 长度):

   ```bash
   uv run alembic revision --autogenerate -m "rc1"
   ```

4. review, 把 alpha 里的数据迁移并进 rc1 的 `upgrade()` / `downgrade()`。

5. 删掉 `alpha_A..alpha_C` 文件,
   链变为 `... -> R_last -> rc1`。

6. 闭环验证 rc1 能独立跑通:

   ```bash
   uv run alembic downgrade base
   uv run alembic upgrade head
   ```

7. dev 环境 (已在 `alpha_C`) 对齐到 rc1, 不重跑:

   ```bash
   uv run alembic stamp rc1
   ```

8. 提交 rc1 + 删除, 打 tag。

## 阶段三: 上线 (rc → staging / prod) — 运维

staging 验证后再上 prod, 两环境步骤相同:

1. 部署新镜像。
2. 迁移作独立步骤先跑 (`R_last -> rc1`):
   - k8s:init container / 独立 Job 跑 `alembic upgrade head`
   - CI/CD:流水线一步连库跑 `alembic upgrade head`
   - compose:一次性 `migrate` service, 应用 `depends_on` 它
3. 迁移成功后, 启动新版本应用。
4. 健康检查不过则中止 (新版本不接管流量)。

## 阶段四: 上线后

- rc1 成为下一迭代的 `R_last`, 回到阶段一。
- 出问题:写修复迁移 (roll forward), 不 `downgrade`。
- 代码回滚 (非破坏性):
  在当前新代码上 `alembic downgrade <target>`, 再部署旧代码。

## 高风险变更: 合并前必须验证

以下几类迁移风险高,
PR 合并前**必须验证** (upgrade / downgrade 闭环 + 数据检查) 并把结果贴出来,
不能 autogenerate 生成完就直接合:

| 情形 | 风险 | 强制动作 |
| --- | --- | --- |
| **重命名列 / 表** | autogenerate 误判成 drop+add → **丢数据** | 走**空迁移**手写 `op.alter_column(new_column_name=...)`; 验证数据条数与内容不变 |
| **删除列 / 删除表** | downgrade 不可逆, 数据永久丢失 | 确认无代码 / 外键引用; 评估 downgrade 是否可接受 (生产只进不退时尤其慎重) |
| **加 NOT NULL 约束** | 存量行无值 → 失败或留下非法 NULL | 先回填或加 `server_default`, 再加约束; 验证无 NULL 残留 |
| **加 UNIQUE / CHECK 约束** | 存量重复 / 违规数据 → 建约束失败 | 先清洗存量; 验证约束能成功创建 |
| **类型变更 (尤其缩窄 / 跨类)** | 截断 / 转换失败 (`varchar(500)→(50)`、string→int) | 核对存量是否符合新类型; 必要时 `USING` 显式转换; 验证无丢失 |
| **数据迁移 (回填 / 转换)** | 业务 SQL 出错、downgrade 残留脏数据 | 成对写 upgrade / downgrade; 验证 upgrade 后数据正确、downgrade 可还原 |
| **PG ENUM 改值** | 删值 / 改名极难, 加值要兼顾旧版本代码 | 优先只加值; 验证存量与代码枚举一致 |

一句话:**结构变更里凡是涉及"数据"或"不可逆"的, 合并前都要人工验证**;
纯加列、加索引这类增量变更可以放宽。

## 关键原则速查

- 合并前先同步 dev 最新, 基于最新结构生成迁移 (链天然线性)。
- dev 环境持续部署 ⇒ 开发期必须提交真实 alpha 迁移。
- CI 卡单 head;同表改动靠 review + rebase 迁移, 不用 merge。
- 定版 = 把 alpha 衍合成一条 rc (autogenerate 净 diff + 删 alpha + stamp dev)。
- 迁移独立于应用, 部署时单独先跑。
- 生产只进不退 (roll forward)。
