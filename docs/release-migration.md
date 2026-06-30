# 发版迁移文档

发版与部署阶段的迁移策略, 覆盖四件事:

- **alpha → rc 融合**:开发期攒下的 alpha 迁移如何定版
- **升级 / 回滚**:与代码部署的先后顺序
- **生产降级原则**:只进不退 (roll forward)
- **迁移部署步骤**:迁移作为独立一次性步骤

## 发版前: alpha 到 rc 的迁移融合 (定版)

开发期攒下一批 alpha 迁移,
发版转 rc 时希望压成一条干净的 rc 迁移。
核心原则:**迁移是模型的派生产物,
在"融合后的模型"上生成, 而不是拼接各分支迁移**。

> Alembic **没有 squash 命令**;
> `alembic merge` 也只收口**多个分叉 head**, 不压线性链。
> 所以"一键指定 n → n+x 融合"做不到 ——
> 但 alpha → rc 融合可以靠**锚定起点 + autogenerate 聚合**实现,
> 起点即区间。

> **先选路子**:有持续部署的 dev 环境 (常见),
> 开发期必须提交 alpha 迁移、走路子 B;
> 纯本地开发、无共享 dev 环境才走路子 A。

### 路子 A — 开发期不提交迁移 (无共享 dev 环境)

| 阶段 | 做法 |
| --- | --- |
| 开发期 | 只改**模型** (`app/models/`), PR 正常合并, 不涉及迁移图 |
| 本地建库 | `create_all()` 建表, 或建**不提交**的本地迁移 |
| 发版定版 | 升到上一正式版后 autogenerate (见下) |

```bash
uv run alembic upgrade <last_release_rev>     # 全新库升到上一正式版 (融合起点)
uv run alembic revision --autogenerate -m "rc1"
```

起点即区间:换 `base` (空库) 就是压整段历史。

### 路子 B — 已提交 alpha 迁移, rc 时 squash

设上一正式版 `R_last`, alpha 段为 A1..Ak。

1. **升到起点** —— 全新库升到 alpha 之前:

   ```bash
   uv run alembic upgrade R_last
   ```

2. **生成聚合迁移** —— autogenerate 出 rc1,
   `down_revision = R_last`,
   内容为 R_last → 当前模型的全部差异:

   ```bash
   uv run alembic revision --autogenerate -m "rc1 squash alpha A1..Ak"
   ```

3. **抄数据迁移** —— 趁 A1..Ak 还在,
   把数据迁移逻辑并进 rc1 的 `upgrade()` / `downgrade()`
   (autogenerate 只做结构)。

4. **删 alpha** —— 删掉 A1..Ak,
   链变为 `... -> R_last -> rc1`;
   跑 upgrade / downgrade 闭环。

5. **对齐存量库** —— 已跑过 alpha 的库结构已是 rc1 结果,
   但版本表还指着已删除的 Ak,
   用 stamp 改指针、不重跑:

   ```bash
   uv run alembic stamp rc1
   ```

6. **全新库** —— 直接 `uv run alembic upgrade head`, 走 R_last → rc1。

区间可控:第 1 步起点换成任意 `n`, 即 n → 当前的融合。

### 备选 — 保留细粒度历史 (不压缩)

用 PR 规范保持线性:

- 每个 PR 的迁移 rebase 到当前唯一 head
- CI 用 `alembic heads` 卡只有一个 head
- 发版前仍有分叉才用 `alembic merge` 收口;同表冲突手工 rebase

代价:维护线性纪律。

## 升级与回滚: 与代码部署的配合

| 场景 | 顺序 | 风险 |
| --- | --- | --- |
| **升级** | 部署新代码 → 迁移向前 → 启动应用 | 低, 增量、不丢数据 |
| **回滚** | 先 `downgrade` (新代码) → 再部署旧代码 | 高, 可能丢数据 |

回滚命令 (仍在当前新代码环境执行):

```bash
uv run alembic downgrade <target>
# 降级完成后再切回旧代码部署
```

- **为什么回滚要先在新代码上 downgrade**:
  `downgrade()` 只存在于**新**版本的迁移文件里,
  旧代码的迁移历史不含这条 revision, 自己反向不了。

- **折中方案**:
  只回滚代码、保留新结构 (旧代码需容忍多余列)。
  适合结构无破坏性、旧 ORM 能忽略新增列的场景。

## 生产只进不退 (roll forward)

结构降级会永久丢数据
(新增列降级即 `DROP COLUMN`, 机制见 `development-migration.md` 的"降级")。
因此:

- 生产**只进不退** —— 出问题写一个修复迁移 (roll forward) 把数据 / 结构改对
- `downgrade` 主要留给开发 / 测试

## 迁移作为独立部署步骤

迁移不塞进应用启动流程,
而是作为**独立的一次性步骤**, 先于应用容器跑完。
一般**复用应用镜像、换 entrypoint/command** 跑 `alembic upgrade head`
(迁移脚本和模型代码都在应用镜像里, 不必另做镜像)。

| 场景 | 做法 |
| --- | --- |
| Kubernetes | init container 跑迁移; 或独立 Job + Helm `pre-upgrade` hook |
| CI/CD 流水线 | 部署前单独一步连库跑 `alembic upgrade` (可先 `--sql` review) |
| compose | 一次性 `migrate` service, 应用 `depends_on` 且条件 `service_completed_successfully` |

三条要点:

- **只跑一次** —— 多副本不能各跑一遍
- **先于应用** —— 新代码依赖新结构
- **失败即中止** —— 迁移不过, 不让新版本启动
