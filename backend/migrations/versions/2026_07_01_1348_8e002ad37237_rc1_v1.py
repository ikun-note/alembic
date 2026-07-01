"""rc1(v1)

Revision ID: 8e002ad37237
Revises: ed44bb17ba4a
Create Date: 2026-07-01 13:48:07.442673
"""
from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '8e002ad37237'
down_revision: str | None = 'ed44bb17ba4a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 合并 alpha 0.0.1 ~ 0.0.8 的净变更 (v0 -> 最终结构)。
    # 含 rename 和 enum, autogenerate 处理不了, 整段手写原始 SQL。
    # title 加长 (alpha 0.0.2)
    op.execute("ALTER TABLE articles ALTER COLUMN title TYPE varchar(500)")
    # body 改名 content (alpha 0.0.4, RENAME 保留数据, 非 drop+add)
    op.execute("ALTER TABLE articles RENAME COLUMN body TO content")
    # status: 建 PG enum + 加列 + 回填 + NOT NULL (alpha 0.0.1 / 0.0.5 / 0.0.6 合并)
    op.execute("CREATE TYPE article_status AS ENUM ('draft', 'published', 'archived')")
    op.execute("ALTER TABLE articles ADD COLUMN status article_status")
    op.execute("UPDATE articles SET status = 'draft' WHERE status IS NULL")
    op.execute("ALTER TABLE articles ALTER COLUMN status SET NOT NULL")
    # metadata: jsonb (alpha 0.0.7)
    op.execute("ALTER TABLE articles ADD COLUMN metadata jsonb")
    # tags: alpha 0.0.3 加、0.0.8 删, 净零, 不体现。


def downgrade() -> None:
    op.execute("ALTER TABLE articles DROP COLUMN metadata")
    op.execute("ALTER TABLE articles DROP COLUMN status")
    op.execute("DROP TYPE article_status")
    op.execute("ALTER TABLE articles RENAME COLUMN content TO body")
    op.execute("ALTER TABLE articles ALTER COLUMN title TYPE varchar(200)")
