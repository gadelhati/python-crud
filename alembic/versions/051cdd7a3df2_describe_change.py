"""describe change

Revision ID: 051cdd7a3df2
Revises: 534278d26a55
Create Date: 2026-11-18 12:02:10.655914

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "051cdd7a3df2"
down_revision: str | Sequence[str] | None = "534278d26a55"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("role_permissions", schema=None) as batch_op:
        batch_op.alter_column(
            "role_id",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=False,
            postgresql_using="lpad(to_hex(role_id::numeric), 32, '0')::uuid",
        )
        batch_op.alter_column(
            "permission_id",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=False,
            postgresql_using="lpad(to_hex(permission_id::numeric), 32, '0')::uuid",
        )

    with op.batch_alter_table("user_roles", schema=None) as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=False,
            postgresql_using="lpad(to_hex(user_id::numeric), 32, '0')::uuid",
        )
        batch_op.alter_column(
            "role_id",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=False,
            postgresql_using="lpad(to_hex(role_id::numeric), 32, '0')::uuid",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("user_roles", schema=None) as batch_op:
        batch_op.alter_column(
            "role_id",
            existing_type=sa.UUID(),
            type_=sa.NUMERIC(),
            existing_nullable=False,
            postgresql_using=(
                "('x' || lpad(replace(role_id::text, '-', ''), 16, '0'))::bit(64)::bigint::numeric"
            ),
        )
        batch_op.alter_column(
            "user_id",
            existing_type=sa.UUID(),
            type_=sa.NUMERIC(),
            existing_nullable=False,
            postgresql_using=(
                "('x' || lpad(replace(user_id::text, '-', ''), 16, '0'))::bit(64)::bigint::numeric"
            ),
        )

    with op.batch_alter_table("role_permissions", schema=None) as batch_op:
        batch_op.alter_column(
            "permission_id",
            existing_type=sa.UUID(),
            type_=sa.NUMERIC(),
            existing_nullable=False,
            postgresql_using=(
                "('x' || lpad(replace(permission_id::text, '-', ''), 16, '0'))"
                "::bit(64)::bigint::numeric"
            ),
        )
        batch_op.alter_column(
            "role_id",
            existing_type=sa.UUID(),
            type_=sa.NUMERIC(),
            existing_nullable=False,
            postgresql_using=(
                "('x' || lpad(replace(role_id::text, '-', ''), 16, '0'))::bit(64)::bigint::numeric"
            ),
        )
