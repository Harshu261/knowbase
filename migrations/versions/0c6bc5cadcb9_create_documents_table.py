
"""create documents table

Revision ID: 0c6bc5cadcb9
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0c6bc5cadcb9"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Sequence("documents_id_seq"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("documents")
