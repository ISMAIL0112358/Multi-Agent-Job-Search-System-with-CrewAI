"""
Migration script for the HR Dashboard feature.

Adds:
- 'role' column to users table
- candidates table
- job_descriptions table
- screening_results table

Safe to run multiple times (checks if tables/columns already exist).
"""
import sqlite3
import os

DB_PATH = os.path.join("data", "app.db")


def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. It will be created on first app start.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- 1. Add 'role' column to users table ---
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    if "role" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'job_seeker'")
        print("✅ Added 'role' column to users table")
    else:
        print("⏭️  'role' column already exists in users table")

    # --- 2. Create candidates table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            resume_filename TEXT NOT NULL,
            resume_text TEXT NOT NULL,
            chroma_doc_id TEXT,
            uploaded_by TEXT REFERENCES users(id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_candidates_uploaded_by ON candidates(uploaded_by)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_candidates_status ON candidates(status)")
    print("✅ candidates table ready")

    # --- 3. Create job_descriptions table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            department TEXT,
            created_by TEXT REFERENCES users(id) ON DELETE SET NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_job_descriptions_created_by ON job_descriptions(created_by)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_job_descriptions_status ON job_descriptions(status)")
    print("✅ job_descriptions table ready")

    # --- 4. Create screening_results table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screening_results (
            id TEXT PRIMARY KEY,
            job_description_id TEXT NOT NULL REFERENCES job_descriptions(id) ON DELETE CASCADE,
            candidate_id TEXT NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
            match_score REAL NOT NULL DEFAULT 0.0,
            match_justification TEXT,
            vetting_questions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_screening_results_jd ON screening_results(job_description_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_screening_results_candidate ON screening_results(candidate_id)")
    print("✅ screening_results table ready")

    conn.commit()
    conn.close()
    print("\n🎉 HR Dashboard migration complete!")


if __name__ == "__main__":
    migrate()
