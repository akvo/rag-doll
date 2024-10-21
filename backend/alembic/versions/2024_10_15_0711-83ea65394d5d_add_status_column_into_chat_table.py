"""add status column into chat table

Revision ID: 83ea65394d5d
Revises: 5bbf019dbb61
Create Date: 2024-10-15 07:11:05.159445

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # noqa


# revision identifiers, used by Alembic.
revision: str = "83ea65394d5d"
down_revision: Union[str, None] = "5bbf019dbb61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Create enum type
    op.execute("CREATE TYPE chat_status_enum AS ENUM ('UNREAD', 'READ')")

    # Add column with default value and make it nullable
    op.add_column(
        "chat",
        sa.Column(
            "status",
            sa.Enum("UNREAD", "READ", name="chat_status_enum"),
            nullable=True,
            server_default="READ",
        ),
    )
    # Make column non-nullable
    op.alter_column("chat", "status", nullable=False, server_default="UNREAD")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("chat", "status")
    # Drop enum type
    op.execute("DROP TYPE chat_status_enum")
    # ### end Alembic commands ###
