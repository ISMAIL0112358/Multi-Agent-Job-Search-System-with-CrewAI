import sqlite3
from backend.config import settings

db_path = settings.DATABASE_URL.replace("sqlite:///", "")

def migrate():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN skills TEXT DEFAULT ''")
        print("Successfully added 'skills' column to 'users' table.")
    except sqlite3.OperationalError as e:
        print(f"Error (maybe column already exists?): {e}")
    finally:
        conn.commit()
        conn.close()

if __name__ == "__main__":
    migrate()
