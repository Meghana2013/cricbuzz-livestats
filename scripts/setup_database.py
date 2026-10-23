"""Create the database and tables from sql/schema.sql.

Usage:
    python scripts/setup_database.py            # create (keeps existing data)
    python scripts/setup_database.py --reset    # delete the database first
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.db_connection import DB_PATH, PROJECT_ROOT, get_connection  # noqa: E402


def main() -> None:
    if "--reset" in sys.argv and DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Deleted old database: {DB_PATH}")

    schema = (PROJECT_ROOT / "sql" / "schema.sql").read_text(encoding="utf-8")
    conn = get_connection()
    try:
        conn.executescript(schema)
        conn.commit()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    finally:
        conn.close()

    print(f"Database ready: {DB_PATH}")
    print("Tables:", ", ".join(t["name"] for t in tables))


if __name__ == "__main__":
    main()
