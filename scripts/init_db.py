# scripts/init_db.py
import sqlite3
import json
import os
import sys
import argparse

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB = os.path.join(REPO_ROOT, "data", "autormf.db")
NIST_SEED = os.path.join(REPO_ROOT, "data", "nist_seed.json")
CWE_SEED = os.path.join(REPO_ROOT, "data", "cwe_seed.json")

def main():
    parser = argparse.ArgumentParser(description="Initialize standalone SQLite database from catalog seeds.")
    parser.add_argument("--db-path", default=DEFAULT_DB, help="Target SQLite database path.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing database file if present.")
    args = parser.parse_args()

    db_path = args.db_path
    if os.path.exists(db_path) and not args.force:
        print(f"Database already exists at {db_path}.")
        print("Use --force to recreate if explicitly intended. Preserving existing database.")
        sys.exit(0)

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path) and args.force:
        os.remove(db_path)

    print(f"Creating database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS NistControls (
            ControlId TEXT PRIMARY KEY,
            Family TEXT NOT NULL,
            Title TEXT NOT NULL,
            Description TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS CweControlMaps (
            Id TEXT PRIMARY KEY,
            CweId TEXT NOT NULL,
            ControlId TEXT NOT NULL,
            MappingRationale TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS CveMetadatas (
            CveId TEXT PRIMARY KEY,
            CweId TEXT,
            CvssScore REAL,
            Description TEXT,
            PublishedDate TEXT,
            LastModifiedDate TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS PreComputedMappings (
            Id TEXT PRIMARY KEY,
            SourceId TEXT NOT NULL,
            SourceType TEXT NOT NULL,
            ControlId TEXT NOT NULL,
            ConfidenceScore REAL NOT NULL,
            MappingType TEXT NOT NULL,
            AdjudicatorComments TEXT,
            AdjudicatedBy TEXT,
            AdjudicatedAt TEXT,
            SyncPending INTEGER NOT NULL DEFAULT 0,
            UpdatedAt TEXT
        )
    """)

    if os.path.exists(NIST_SEED):
        print(f"Seeding NIST controls from {NIST_SEED}...")
        with open(NIST_SEED, "r", encoding="utf-8") as f:
            nist_data = json.load(f)
            control_rows = [
                (c["ControlId"], c.get("Family", ""), c.get("Title", ""), c.get("Description", ""))
                for c in nist_data
            ]
            cur.executemany("INSERT OR IGNORE INTO NistControls VALUES (?, ?, ?, ?)", control_rows)
            print(f"Seeded {len(control_rows)} controls.")

    if os.path.exists(CWE_SEED):
        print(f"Seeding CWE control mappings from {CWE_SEED}...")
        with open(CWE_SEED, "r", encoding="utf-8") as f:
            cwe_data = json.load(f)
            import uuid
            cwe_rows = [
                (str(uuid.uuid4()), m["CweId"], m["ControlId"], m.get("MappingRationale", ""))
                for m in cwe_data
            ]
            cur.executemany("INSERT OR IGNORE INTO CweControlMaps VALUES (?, ?, ?, ?)", cwe_rows)
            print(f"Seeded {len(cwe_rows)} CWE mappings.")

    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    main()
