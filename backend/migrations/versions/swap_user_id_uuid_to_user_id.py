"""Swap user_id_uuid -> user_id and drop legacy bigint user_id columns

This migration assumes:
- You already added `user_id_uuid` columns and backfilled them with existing `users.id` UUIDs.
- You have verified backfill results.

What it does (upgrade):
- For each child table, attempts to drop the old FK constraint on `user_id` (if it exists),
  drops the old `user_id` column, renames `user_id_uuid` to `user_id` (UUID type), and
  creates a new FK constraint `fk_<table>_user_id_users` referencing `users(id)` with ON DELETE SET NULL.

Downgrade will try to revert the rename and recreate an empty bigint `user_id` column (data lost).

Run only after you confirm backfill is complete and verified.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'swap_user_id_uuid_to_user_id'
down_revision = 'convert_user_ids_to_uuid'
branch_labels = None
depends_on = None

child_tables = [
    'crops',
    'disease_reports',
    'orders',
    'bookings',
    'listings',
    'notifications',
    'chat_history',
    'login_attempts',
    'login_sessions',
]


def upgrade():
    for table in child_tables:
        # Attempt to drop any existing FK on the old user_id column (best-effort)
        old_fk_name = f'fk_{table}_user_id_users'
        try:
            op.drop_constraint(old_fk_name, table_name=table, type_='foreignkey')
        except Exception:
            pass

        # Use batch_alter_table for safe column operations
        with op.batch_alter_table(table) as batch_op:
            # Drop legacy bigint user_id column if present
            try:
                batch_op.drop_column('user_id')
            except Exception:
                pass

            # Rename user_id_uuid -> user_id (UUID)
            try:
                batch_op.alter_column(
                    'user_id_uuid',
                    new_column_name='user_id',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=True,
                )
            except Exception:
                pass

            # Create FK constraint for the new user_id column
            try:
                batch_op.create_foreign_key(old_fk_name, 'users', ['user_id'], ['id'], ondelete='SET NULL')
            except Exception:
                pass


def downgrade():
    # Reverse: try to rename user_id back to user_id_uuid and recreate empty bigint user_id
    for table in child_tables:
        with op.batch_alter_table(table) as batch_op:
            fk_name = f'fk_{table}_user_id_users'
            try:
                batch_op.drop_constraint(fk_name, type_='foreignkey')
            except Exception:
                pass

            # Rename UUID column back to user_id_uuid
            try:
                batch_op.alter_column(
                    'user_id',
                    new_column_name='user_id_uuid',
                    existing_type=postgresql.UUID(as_uuid=True),
                    nullable=True,
                )
            except Exception:
                pass

            # Recreate empty legacy bigint column (no original data restored)
            try:
                batch_op.add_column(sa.Column('user_id', sa.BigInteger(), nullable=True))
            except Exception:
                pass
