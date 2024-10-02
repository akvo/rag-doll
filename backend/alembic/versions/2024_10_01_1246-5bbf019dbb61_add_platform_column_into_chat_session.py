"""Add platform column into chat session

Revision ID: 5bbf019dbb61
Revises: 33e313a32ce6
Create Date: 2024-10-01 12:46:52.920462

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa


# revision identifiers, used by Alembic.
revision: str = "5bbf019dbb61"
down_revision: Union[str, None] = "33e313a32ce6"
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
