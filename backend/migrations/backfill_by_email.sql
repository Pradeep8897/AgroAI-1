-- BACKFILL BY EMAIL: map child rows to users.id via users.email
-- Run these statements in Supabase SQL editor after applying the add-column migration.

-- 1) Backfill login_attempts (has `email` column in models)
UPDATE login_attempts la
SET user_id_uuid = u.id
FROM users u
WHERE la.email IS NOT NULL
  AND u.email IS NOT NULL
  AND la.email = u.email
  AND la.user_id IS NOT NULL;

-- 2) If any other child tables actually store `email`, add similar statements.
-- Example (uncomment and edit table/column names):
-- UPDATE some_table t
-- SET user_id_uuid = u.id
-- FROM users u
-- WHERE t.email IS NOT NULL AND u.email IS NOT NULL AND t.email = u.email AND t.user_id IS NOT NULL;

-- 3) After verifying backfill, run verification queries to confirm counts:
-- SELECT COUNT(*) FROM login_attempts WHERE user_id_uuid IS NULL AND user_id IS NOT NULL;
-- SELECT COUNT(*) FROM login_attempts la JOIN users u ON la.user_id_uuid = u.id;

-- 4) Once all child tables are backfilled and verified, create another migration to
-- drop old user_id columns, rename user_id_uuid -> user_id, and recreate any
-- indexes or constraints as needed.
