Migration plan: Convert user ID columns to UUIDs

Overview

Your codebase now uses UUID primary key for `users.id` and expects all `user_id` foreign keys to be UUIDs. The database schema in Supabase must be updated to match. Directly converting bigint columns to uuid is destructive if the values don't already match valid UUIDs. The plan below gives safe steps and options for mapping legacy bigint user IDs to UUIDs.

Assumptions
- Supabase `users` table currently uses UUID primary keys (as you stated).
- Some application tables still have `BIGINT` `user_id` columns referencing numeric user IDs from a legacy system.

High-level steps

1. Back up your database (required!).
2. Decide mapping strategy from legacy numeric user IDs to existing user UUIDs:
   - Map by `email` or another unique identifier present in both `users` and child tables.
   - If no reliable mapping exists, create new UUIDs for legacy users and insert new `users` rows or maintain a mapping table.
3. For each child table that references `users.id` (crops, disease_reports, orders, bookings, listings, notifications, chat_history, login_attempts, login_sessions):
   a. Add a new column `user_id_uuid` (type `uuid`, nullable).
   b. Backfill `user_id_uuid` using an appropriate join/mapping (SQL shown below).
   c. Create FK constraint on `user_id_uuid` referencing `users(id)`.
   d. After verification, drop old FK constraint and old `user_id` column, then rename `user_id_uuid` to `user_id`.
4. Update application and tests to use UUID values (done in code). Restart services.

Backfill examples (choose one depending on available common fields):

-- If child tables have `email` column aligning to users.email:
UPDATE child_table c
SET user_id_uuid = u.id
FROM users u
WHERE c.email = u.email AND c.user_id IS NOT NULL;

-- If you must map by legacy numeric id to a mapping table `user_id_map(legacy_id bigint, new_id uuid)`:
UPDATE child_table c
SET user_id_uuid = m.new_id
FROM user_id_map m
WHERE c.user_id = m.legacy_id;

-- Fallback: set user_id_uuid to NULL and manually fix
UPDATE child_table
SET user_id_uuid = NULL
WHERE user_id_uuid IS NULL;

Alembic migration template

I added a migration template file in `backend/migrations/versions/convert_user_ids_to_uuid.py` that performs non-destructive schema changes (adds `user_id_uuid` columns and FK constraints). It includes comments with backfill instructions and safe downgrade steps. Review and adjust mapping SQL before running it against production.

If you want, I can:
- Generate a full Alembic migration that performs the backfill using a chosen mapping (email or mapping table).
- Or produce raw SQL statements you can run in Supabase SQL editor.

Next step: tell me which mapping approach you prefer (map by `email`, provide a mapping table, or create new users/UUIDs), and I will generate the full Alembic migration and/or SQL ready to run.