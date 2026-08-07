"""Alembic migration template: add UUID user_id columns and FK constraints

This is a safe, non-destructive template. It:
- Adds new UUID columns named `user_id_uuid` to child tables
- Creates FK constraints referencing `users(id)` for the new columns
- DOES NOT attempt to backfill data — you must supply mapping SQL appropriate to your data

Before running:
- Backup the DB.
- Edit the `backfill_statements` list with SQL that maps legacy `user_id` values to existing `users.id` UUIDs.

Run order recommendation:
1. Apply this migration to add columns and constraints.
2. Run backfill SQL (via Supabase SQL editor or a controlled script).
3. Verify data correctness.
4. Create another migration to drop old columns and rename `user_id_uuid` -> `user_id`.

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'convert_user_ids_to_uuid'
down_revision = None
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
    # Add new UUID columns and FK constraints
    for table in child_tables:
        op.add_column(
            table,
            sa.Column('user_id_uuid', postgresql.UUID(as_uuid=True), nullable=True)
        )
        # create FK constraint name based on table
        fk_name = f'fk_{table}_user_id_uuid_users'
        op.create_foreign_key(
            fk_name, table, 'users', ['user_id_uuid'], ['id'], ondelete='SET NULL'
        )

    # IMPORTANT: Insert your backfill statements here and run them separately using the SQL editor
    # Example backfill (UNCOMMENT and edit as needed):
    # op.execute("""
    # UPDATE crops c
    # SET user_id_uuid = u.id
    # FROM users u
    # WHERE c.email = u.email AND c.user_id IS NOT NULL;
    # """)
        # Backfill by email for tables that store an `email` column.
        # The project models show only `login_attempts.email` as an available join key.
        # This statement will set `user_id_uuid` for login attempts where the email matches an existing user.
        op.execute("""
        -- Backfill login_attempts.user_id_uuid from users.id via email
        UPDATE login_attempts la
        SET user_id_uuid = u.id
        FROM users u
        WHERE la.email IS NOT NULL
            AND u.email IS NOT NULL
            AND la.email = u.email
            AND la.user_id IS NOT NULL;
        """)

        # NOTE: Other child tables (crops, disease_reports, orders, bookings, listings,
        # notifications, chat_history, login_sessions) do NOT have an `email` column in the
        # current models. They require a mapping table or manual mapping strategy.


def downgrade():
    # Drop FK constraints and columns added in upgrade
    for table in child_tables:
        fk_name = f'fk_{table}_user_id_uuid_users'
        try:
            op.drop_constraint(fk_name, table, type_='foreignkey')
        except Exception:
            pass
        try:
            op.drop_column(table, 'user_id_uuid')
        except Exception:
            pass
