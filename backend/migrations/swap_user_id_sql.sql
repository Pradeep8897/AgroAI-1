-- Swap user_id_uuid -> user_id (raw SQL for Supabase SQL editor)
-- Run after:
-- 1) You've applied the add-column migration (or manually added user_id_uuid columns)
-- 2) You've executed backfill_by_email.sql and verified values
-- 3) You have a backup

-- For each table: drop old fk, drop old user_id column, rename user_id_uuid -> user_id, ensure type, add new fk

BEGIN;

-- crops
ALTER TABLE IF EXISTS crops DROP CONSTRAINT IF EXISTS fk_crops_user_id_users;
ALTER TABLE IF EXISTS crops DROP COLUMN IF EXISTS user_id;
ALTER TABLE IF EXISTS crops RENAME COLUMN user_id_uuid TO user_id;
ALTER TABLE IF EXISTS crops ALTER COLUMN user_id TYPE uuid USING user_id::uuid;
ALTER TABLE IF EXISTS crops ADD CONSTRAINT fk_crops_user_id_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

-- disease_reports
ALTER TABLE IF EXISTS disease_reports DROP CONSTRAINT IF EXISTS fk_disease_reports_user_id_users;
ALTER TABLE IF EXISTS disease_reports DROP COLUMN IF EXISTS user_id;
ALTER TABLE IF EXISTS disease_reports RENAME COLUMN user_id_uuid TO user_id;
ALTER TABLE IF EXISTS disease_reports ALTER COLUMN user_id TYPE uuid USING user_id::uuid;
ALTER TABLE IF EXISTS disease_reports ADD CONSTRAINT fk_disease_reports_user_id_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

-- orders
ALTER TABLE IF EXISTS orders DROP CONSTRAINT IF EXISTS fk_orders_user_id_users;
ALTER TABLE IF EXISTS orders DROP COLUMN IF EXISTS user_id;
ALTER TABLE IF EXISTS orders RENAME COLUMN user_id_uuid TO user_id;
ALTER TABLE IF EXISTS orders ALTER COLUMN user_id TYPE uuid USING user_id::uuid;
ALTER TABLE IF EXISTS orders ADD CONSTRAINT fk_orders_user_id_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

-- bookings
ALTER TABLE IF EXISTS bookings DROP CONSTRAINT IF EXISTS fk_bookings_user_id_users;
ALTER TABLE IF EXISTS bookings DROP COLUMN IF EXISTS user_id;
ALTER TABLE IF EXISTS bookings RENAME COLUMN user_id_uuid TO user_id;
ALTER TABLE IF EXISTS bookings ALTER COLUMN user_id TYPE uuid USING user_id::uuid;
ALTER TABLE IF EXISTS bookings ADD CONSTRAINT fk_bookings_user_id_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

-- listings
ALTER TABLE IF EXISTS listings DROP CONSTRAINT IF EXISTS fk_listings_user_id_users;
ALTER TABLE IF EXISTS listings DROP COLUMN IF EXISTS user_id;
ALTER TABLE IF EXISTS listings RENAME COLUMN user_id_uuid TO user_id;
ALTER TABLE IF EXISTS listings ALTER COLUMN user_id TYPE uuid USING user_id::uuid;
ALTER TABLE IF EXISTS listings ADD CONSTRAINT fk_listings_user_id_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

-- notifications
ALTER TABLE IF EXISTS notifications DROP CONSTRAINT IF EXISTS fk_notifications_user_id_users;
ALTER TABLE IF EXISTS notifications DROP COLUMN IF EXISTS user_id;
ALTER TABLE IF EXISTS notifications RENAME COLUMN user_id_uuid TO user_id;
ALTER TABLE IF EXISTS notifications ALTER COLUMN user_id TYPE uuid USING user_id::uuid;
ALTER TABLE IF EXISTS notifications ADD CONSTRAINT fk_notifications_user_id_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

-- chat_history
ALTER TABLE IF EXISTS chat_history DROP CONSTRAINT IF EXISTS fk_chat_history_user_id_users;
ALTER TABLE IF EXISTS chat_history DROP COLUMN IF EXISTS user_id;
ALTER TABLE IF EXISTS chat_history RENAME COLUMN user_id_uuid TO user_id;
ALTER TABLE IF EXISTS chat_history ALTER COLUMN user_id TYPE uuid USING user_id::uuid;
ALTER TABLE IF EXISTS chat_history ADD CONSTRAINT fk_chat_history_user_id_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

-- login_attempts
ALTER TABLE IF EXISTS login_attempts DROP CONSTRAINT IF EXISTS fk_login_attempts_user_id_users;
ALTER TABLE IF EXISTS login_attempts DROP COLUMN IF EXISTS user_id;
ALTER TABLE IF EXISTS login_attempts RENAME COLUMN user_id_uuid TO user_id;
ALTER TABLE IF EXISTS login_attempts ALTER COLUMN user_id TYPE uuid USING user_id::uuid;
ALTER TABLE IF EXISTS login_attempts ADD CONSTRAINT fk_login_attempts_user_id_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

-- login_sessions
ALTER TABLE IF EXISTS login_sessions DROP CONSTRAINT IF EXISTS fk_login_sessions_user_id_users;
ALTER TABLE IF EXISTS login_sessions DROP COLUMN IF EXISTS user_id;
ALTER TABLE IF EXISTS login_sessions RENAME COLUMN user_id_uuid TO user_id;
ALTER TABLE IF EXISTS login_sessions ALTER COLUMN user_id TYPE uuid USING user_id::uuid;
ALTER TABLE IF EXISTS login_sessions ADD CONSTRAINT fk_login_sessions_user_id_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

COMMIT;

-- Verification queries (run after the script):
-- SELECT COUNT(*) FROM login_attempts WHERE user_id IS NULL AND user_id_uuid IS NOT NULL; -- should be 0
-- SELECT COUNT(*) FROM login_attempts la JOIN users u ON la.user_id = u.id;
