"""Add platform column into chat session table

Revision ID: f22f19678871
Revises: cfc217bbdd23
Create Date: 2024-09-30 04:41:08.624389

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa


# revision identifiers, used by Alembic.
revision: str = "f22f19678871"
down_revision: Union[str, None] = "cfc217bbdd23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type
    op.execute("CREATE TYPE platform_enum AS ENUM ('WHATSAPP', 'SLACK')")

    # Add column with default value and make it nullable
    op.add_column(
        "chat_session",
        sa.Column(
            "platform",
            sa.Enum("WHATSAPP", "SLACK", name="platform_enum"),
            nullable=True,
            server_default="WHATSAPP",
        ),
    )
    # Make column non-nullable
    op.alter_column(
        "chat_session", "platform", nullable=False, server_default=None
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # Drop column
    op.drop_column("chat_session", "platform")
    # Drop enum type
    op.execute("DROP TYPE platform_enum")
    # ### end Alembic commands ###
