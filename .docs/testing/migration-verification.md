# 迁移验证

## 测试范围

验证 Alembic 迁移脚本本身的正确性、可逆性与可重复性. 覆盖 Schema 迁移与数据迁移两类, 以及进阶能力 (分支、离线、编程式、异步) 的关键路径. 迁移的作用对象为经前端 / API 录入的真实数据, 验证其结构与数据变化可观察.

## 环境准备

| 项目 | 值 |
| --- | --- |
| 数据库 | PostgreSQL 16, podman compose 起于 `.dev/` |
| Python | 3.12, 依赖按 `backend/pyproject.toml` 安装 |
| 配置 | `backend/.env` 填入容器 PG 的连接参数 |
| 工具 | alembic CLI、psql (容器内或宿主) |
| 应用 | backend FastAPI 与 frontend React 起服务, 用于录入数据与观察结果 |
| 复位方式 | `podman compose down -v` 销毁卷后重建, 得到全新库 |

## 场景矩阵

| 场景 | 前置条件 | 操作 | 预期结果 |
| --- | --- | --- | --- |
| 全新库初始化 | 空数据库 | `alembic upgrade head` | 迁移按序执行, `alembic current` 指向 head |
| 自动生成准确 | 模型已变更 | `alembic revision --autogenerate` | 生成的迁移与模型 diff 一致, 无遗漏 / 误检 |
| upgrade 正确 | 迁移已生成 | `alembic upgrade head` | 表结构与模型一致, 数据迁移结果正确 |
| downgrade 可逆 | 已 upgrade 到 head | `alembic downgrade base` | 结构与数据回到初始状态, 无残留 |
| 单步回滚 | 已 upgrade 多步 | `alembic downgrade -1` | 仅回退最近一版, 其余保留 |
| 数据迁移正确 | 含数据迁移 | upgrade 后查询 | 回填 / 转换后的数据符合预期 |
| 应用数据迁移 | 已经前端 / API 录入数据 | upgrade 含数据迁移 | 转换后数据符合规则, 前端列表可见变化 |
| 数据迁移可逆 | 已 upgrade | downgrade 后查询 | 数据还原到迁移前状态 |
| 离线 SQL | 无需连库 | `alembic upgrade head --sql` | 输出可审 DDL, 不实际执行 |
| 分支合并 | 存在分支迁移 | `alembic merge` 后 upgrade | 合并点无冲突, upgrade 成功 |
| 编程式 API | 应用代码内 | 调用 API upgrade | 与 CLI 结果等价 |
| 异步 env.py | 异步配置 | 异步上下文 upgrade | 迁移成功, 与同步结果一致 |
| 幂等性 | 已 upgrade head | 再次 `alembic upgrade head` | 无操作, 不报错 |

## 关键用例

### 全新库到 head 再回到 base 的闭环

1. `podman compose down -v && podman compose up -d` 得到全新空库
2. `alembic upgrade head`, 记录 `alembic current`
3. 用 psql 核对关键表结构、约束名与模型一致
4. `alembic downgrade base`
5. 再次核对: 业务表消失, 仅剩 alembic_version 或为空

预期结果:

- upgrade 后结构与模型完全一致, 约束名符合 naming_convention
- downgrade base 后无业务表残留
- 全过程无报错

### 数据迁移 upgrade / downgrade 数据一致性

1. 准备含待处理数据的初始状态 (按数据迁移示例前置)
2. `alembic upgrade head` 执行数据迁移
3. 查询验证数据已按规则转换 / 回填
4. `alembic downgrade -1` 回退数据迁移
5. 查询验证数据回到迁移前状态

预期结果:

- upgrade 后数据符合迁移规则
- downgrade 后数据可逆还原, 无部分写入残留

### 前端录入 → 数据迁移 → 观察变化

1. 起后端与前端服务, 在录入页新建若干 Article 数据
2. 修改模型并生成含数据迁移的版本
3. `alembic upgrade head` 执行迁移
4. 回到前端列表与详情, 核对数据已按迁移规则变化
5. `alembic downgrade -1` 回退, 再次核对数据还原

预期结果:

- upgrade 后前端展示的数据符合迁移规则
- downgrade 后数据还原, 前端可见
- 全过程数据无丢失或残留

## 不测范围

- 不测业务模型字段的业务语义正确性
- 不测并发迁移与锁竞争 (探究项目不深入运维)
- 不测前端组件单元测试与端到端自动化 (聚焦迁移验证)
- 不测 CI / CD 集成
- 不测性能基准
