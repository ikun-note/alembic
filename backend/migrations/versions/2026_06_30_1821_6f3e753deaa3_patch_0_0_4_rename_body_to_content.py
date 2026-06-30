"""patch(0.0.4): rename body to content

Revision ID: 6f3e753deaa3
Revises: d1b79f3bfb7a
Create Date: 2026-06-30 18:21:26.006821
"""
from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '6f3e753deaa3'
down_revision: str | None = 'd1b79f3bfb7a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # autogenerate 检测不了改名 (body -> content 会被误判成 drop body + add content, 丢数据),
    # 这里手写 PG 原生 RENAME COLUMN, 数据保留。
    op.alter_column('articles', 'body', new_column_name='content')


def downgrade() -> None:
    op.alter_column('articles', 'content', new_column_name='body')
