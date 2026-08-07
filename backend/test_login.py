from app import app
import json, time


def main():
    email = f"testuser+{int(time.time())}@example.com"
    pwd = "TestPass123"
    username = "testuser"
    print("Using email:", email)
    # Ensure schema has expected columns (add username if missing)
    with app.app_context():
        from extensions import db as _db
        try:
            from sqlalchemy import text
            _db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(255) DEFAULT ''"))
            _db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(255) DEFAULT ''"))
            # Ensure existing `name` column allows inserts when omitted
            try:
                _db.session.execute(text("ALTER TABLE users ALTER COLUMN name DROP NOT NULL"))
                _db.session.execute(text("ALTER TABLE users ALTER COLUMN name SET DEFAULT ''"))
            except Exception:
                pass
            _db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50)"))
            _db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS location VARCHAR(255)"))
            _db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS state VARCHAR(255)"))
            _db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS farm_size NUMERIC"))
            _db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(100)"))
            _db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'farmer'"))
            _db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now()"))
            _db.session.commit()
            print('Ensured users.username column exists')
        except Exception as e:
            _db.session.rollback()
            print('Schema adjustment failed:', e)

    with app.test_client() as c:
        resp = c.post('/api/auth/register', json={"username": username, "email": email, "password": pwd})
        print('REGISTER', resp.status_code)
        try:
            print(resp.get_json())
        except Exception:
            print(resp.data)

        resp2 = c.post('/api/auth/login', json={"email": email, "password": pwd})
        print('LOGIN', resp2.status_code)
        try:
            print(resp2.get_json())
        except Exception:
            print(resp2.data)


if __name__ == '__main__':
    main()
