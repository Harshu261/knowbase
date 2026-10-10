"""add document full text search index

Revision ID: 161a0e6a1b4f
Revises: 0c6bc5cadcb9
Create Date: 2026-10-10 23:57:46.348079

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '161a0e6a1b4f'
down_revision: Union[str, Sequence[str], None] = '0c6bc5cadcb9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "documents_content_fts_idx",
        "documents",
        [
            sa.text(
                "to_tsvector('english', coalesce(content, ''))"
            )
        ],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index(
        "documents_content_fts_idx",
        table_name="documents",
    )
