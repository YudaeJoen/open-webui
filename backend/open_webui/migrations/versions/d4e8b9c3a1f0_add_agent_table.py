"""Add agent table

Revision ID: d4e8b9c3a1f0
Revises: ca81bd47c050
Create Date: 2026-01-07 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e8b9c3a1f0"
down_revision: Union[str, None] = "9f0c9cd09105"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "agent",
        sa.Column("id", sa.String(), nullable=False, primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("chat_id", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="idle"),
        sa.Column("user_request", sa.Text(), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("plan", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("execution_history", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("current_step", sa.String(), nullable=True),
        sa.Column("artifacts", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.BigInteger(), nullable=False),
        sa.Column("completed_at", sa.BigInteger(), nullable=True),
    )

    # Create indexes for better query performance
    op.create_index("idx_agent_user_id", "agent", ["user_id"])
    op.create_index("idx_agent_chat_id", "agent", ["chat_id"])
    op.create_index("idx_agent_status", "agent", ["status"])
    op.create_index("idx_agent_task_type", "agent", ["task_type"])
    op.create_index("idx_agent_created_at", "agent", ["created_at"])


def downgrade():
    op.drop_index("idx_agent_created_at", table_name="agent")
    op.drop_index("idx_agent_task_type", table_name="agent")
    op.drop_index("idx_agent_status", table_name="agent")
    op.drop_index("idx_agent_chat_id", table_name="agent")
    op.drop_index("idx_agent_user_id", table_name="agent")
    op.drop_table("agent")
