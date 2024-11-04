"""add user_broadcast to sender_role_enum

Revision ID: f5a9dc155fe8
Revises: 0f35b0530dd7
Create Date: 2024-10-29 02:03:42.447384

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa  # noqa
import sqlmodel  # noqa


# revision identifiers, used by Alembic.
revision: str = "f5a9dc155fe8"
down_revision: Union[str, None] = "0f35b0530dd7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Enum details
old_options = (
    "USER",
    "CLIENT",
    "ASSISTANT",
    "SYSTEM",
)


def upgrade() -> None:
    # Add the new value to the Enum type in PostgreSQL
    op.execute("ALTER TYPE sender_role_enum ADD VALUE 'USER_BROADCAST'")
    # ### end Alembic commands ###


def downgrade() -> None:
    # Step 1: Update any rows that have the `USER_BROADCAST` value
    op.execute(
        """
        UPDATE chat
        SET sender_role = 'USER'
        WHERE sender_role = 'USER_BROADCAST'
        """
    )

    # Step 2: Rename the existing type to keep it as a backup
    op.execute("ALTER TYPE sender_role_enum RENAME TO sender_role_enum_old")

    # Step 3: Create a new Enum type without the 'USER_BROADCAST' value
    op.execute(f"CREATE TYPE sender_role_enum AS ENUM{old_options}")

    # Step 4: Alter the column to use the new Enum type
    op.execute(
        """
        ALTER TABLE chat
        ALTER COLUMN sender_role
        TYPE sender_role_enum
        USING sender_role::text::sender_role_enum
        """
    )

    # Step 5: Drop the old Enum type
    op.execute("DROP TYPE sender_role_enum_old")
    # ### end Alembic commands ###
