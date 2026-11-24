"""Smoke test for the SQL stage of the pipeline, on a tiny synthetic sample.

The schema is read from the notebook (analysis/retail_analysis.ipynb, cell that defines SCHEMA),
the sample rows are tests/data/sample/*.csv (made-up, cleaned shape), and sql/run_queries.py runs
all ten queries into a temporary folder. The pandas cleaning steps are not covered here: they
need pandas and the raw UCI file.

Standard library only:  python -m unittest tests/test_pipeline_smoke.py -v
"""
import csv
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "tests" / "data" / "sample"
RUNNER = ROOT / "sql" / "run_queries.py"


def notebook_schema():
    nb = json.loads((ROOT / "analysis" / "retail_analysis.ipynb").read_text(encoding="utf-8"))
    for cell in nb["cells"]:
        source = "".join(cell["source"])
        match = re.search(r"SCHEMA = '''(.*?)'''", source, re.S)
        if match:
            return match.group(1)
    raise AssertionError("SCHEMA not found in the notebook")


def rows(name, casts):
    with open(SAMPLE / f"{name}.csv", newline="", encoding="utf-8") as f:
        return [tuple(cast(v) for cast, v in zip(casts, r.values())) for r in csv.DictReader(f)]


class SqlStageSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls.tmp.name)
        db = tmp / "sample.db"
        con = sqlite3.connect(db)
        con.executescript(notebook_schema())
        con.executemany("INSERT INTO customers VALUES (?, ?)", rows("customers", [int, str]))
        con.executemany("INSERT INTO products VALUES (?, ?)", rows("products", [str, str]))
        con.executemany("INSERT INTO orders VALUES (?, ?, ?)", rows("orders", [str, int, str]))
        con.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?)", rows("order_items", [str, str, int, float]))
        con.commit()
        con.close()
        cls.result = subprocess.run(
            [sys.executable, str(RUNNER), "--db", str(db), "--out-dir", str(tmp)],
            capture_output=True, text=True, timeout=120,
        )
        cls.results = (tmp / "results.md").read_text(encoding="utf-8") if (tmp / "results.md").exists() else ""

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_runner_exits_cleanly(self):
        self.assertEqual(self.result.returncode, 0, self.result.stderr)
        self.assertIn("wrote", self.result.stdout)

    def test_all_ten_queries_ran(self):
        self.assertEqual(self.results.count("\n## Q"), 10)

    def test_headline_kpis_match_hand_totals(self):
        # Sample revenue: 25 + 12 + 10 + 20 + 4 + 58 = 129.00; 6 orders; 4 customers; 129 / 6 = 21.50.
        self.assertIn("| 129.00 | 6 | 4 | 21.50 |", self.results)

    def test_monthly_totals_match_hand_totals(self):
        self.assertIn("| 2011-01 | 2 | 37.00 |", self.results)  # 25 + 12
        self.assertIn("| 2011-02 | 3 | 34.00 |", self.results)  # 10 + 20 + 4
        self.assertIn("| 2011-03 | 1 | 58.00 |", self.results)  # 58

    def test_top_country_matches_hand_totals(self):
        self.assertIn("| Germany | 1 | 68.00 | 52.70 |", self.results)  # customer 1002: 10 + 58
        self.assertIn("| United Kingdom | 2 | 41.00 | 31.80 |", self.results)  # customers 1001 and 1004
        self.assertIn("| France | 1 | 20.00 | 15.50 |", self.results)  # customer 1003


if __name__ == "__main__":
    unittest.main()
