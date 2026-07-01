"""alpha(0.0.6): status to pg enum

Revision ID: 4eecb03a1096
Revises: 8b729e8d7a05
Create Date: 2026-07-01 09:57:49.670349
"""
from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '4eecb03a1096'
down_revision: str | None = '8b729e8d7a05'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # PG enum 是命名类型, 必须先 CREATE TYPE (autogenerate 不会自动建)。
    op.execute("CREATE TYPE article_status AS ENUM ('draft', 'published', 'archived')")
    # varchar -> enum, USING 显式转换存量值 (autogenerate 也不会加 USING)。
    op.execute(
        "ALTER TABLE articles ALTER COLUMN status TYPE article_status "
        "USING status::article_status"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE articles ALTER COLUMN status TYPE varchar(20) USING status::text")
    op.execute("DROP TYPE article_status")
