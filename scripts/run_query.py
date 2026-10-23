"""Run one (or all) of the 25 SQL questions and print the result.

Usage:
    python scripts/run_query.py 1        # run question 1
    python scripts/run_query.py all      # run all 25 and show row counts
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from sql.queries import QUERIES, get_query  # noqa: E402
from utils.db_connection import fetch_df  # noqa: E402

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        return
    if sys.argv[1] == "all":
        for q in QUERIES:
            try:
                df = fetch_df(q["sql"])
                print(f"Q{q['id']:>2} [{q['level']:<12}] {len(df):>4} rows  {q['title']}")
            except Exception as exc:  # show which query broke
                print(f"Q{q['id']:>2} FAILED: {exc}")
        return
    q = get_query(int(sys.argv[1]))
    print(f"Q{q['id']}: {q['title']}\n{q['question']}\n")
    df = fetch_df(q["sql"])
    print(df.head(15).to_string(index=False))
    print(f"\n({len(df)} rows total)")


if __name__ == "__main__":
    main()
