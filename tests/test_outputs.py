"""Checks that the published numbers agree with each other and with the SQL outputs.

Standard library only:  python -m unittest discover -s tests
The database checks run only when data/retail.db exists (it is not in git).
"""
import json
import re
import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "dashboard" / "data.json").read_text(encoding="utf-8"))
README = (ROOT / "README.md").read_text(encoding="utf-8")
RESULTS = (ROOT / "sql" / "results.md").read_text(encoding="utf-8")
INDEX = (ROOT / "dashboard" / "index.html").read_text(encoding="utf-8")
DB = ROOT / "data" / "retail.db"
MONTHS = dict(zip(DATA["monthly"]["labels"], DATA["monthly"]["values"]))
REVENUE = DATA["kpis"]["revenue"]


def money(x):
    return f"{x:,.2f}"


class CleaningAndKpis(unittest.TestCase):
    def test_readme_cleaning_counts_match_data_json(self):
        steps = DATA["cleaning"]
        self.assertEqual(steps[0], ["Raw rows", 541909])
        self.assertEqual(steps[-1][1], 388066)
        self.assertIn("541,909", README)
        self.assertIn("388,066", README)
        self.assertIn("5,268", README)
        self.assertEqual(steps[0][1] - steps[1][1], 5268)  # duplicates dropped

    def test_kpis_match_sql_q1(self):
        k = DATA["kpis"]
        row = f"| {money(REVENUE)} | {k['orders']:,} | {k['customers']:,} | {money(k['avg_order_value'])} |"
        self.assertIn(row, RESULTS)

    def test_monthly_revenue_matches_sql_q2(self):
        months = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
                  "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
        for label, value in MONTHS.items():
            mon, year = label.split()
            ym = f"{year}-{months[mon]}"
            self.assertRegex(RESULTS, rf"\| {ym} \| [\d,]+ \| {re.escape(money(value))} \|", label)

    def test_top_products_match_sql_q5(self):
        for label, value in zip(DATA["products"]["labels"], DATA["products"]["values"]):
            self.assertIn(money(value), RESULTS, label)

    def test_readme_and_dashboard_numbers(self):
        # Each figure the README or the dashboard text states, recomputed from data.json.
        sep_nov = MONTHS["Sep 2011"] + MONTHS["Oct 2011"] + MONTHS["Nov 2011"]
        full12 = sum(v for k, v in MONTHS.items() if k != "Dec 2011")
        jan_aug = sum(MONTHS[f"{m} 2011"] for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]) / 8
        pct = lambda x: round(x * 100)
        self.assertEqual(pct(sep_nov / full12), 38)
        self.assertEqual(round(MONTHS["Nov 2011"] / jan_aug, 1), 2.1)
        self.assertEqual(round(DATA["pareto"]["values"][20]), 74)
        self.assertEqual(round(DATA["pareto"]["values"][1]), 30)
        self.assertEqual(pct(DATA["kpis"]["uk_share"]), 82)
        top4 = sum(dict(zip(DATA["countries"]["labels"], DATA["countries"]["values"]))[c]
                   for c in ["Netherlands", "EIRE", "Germany", "France"])
        self.assertEqual(pct(top4 / REVENUE), 11)
        self.assertEqual(pct(sum(DATA["products"]["values"]) / REVENUE), 8)
        hours = dict(zip(DATA["hours"]["labels"], DATA["hours"]["values"]))
        mid = sum(v for h, v in hours.items() if 10 <= int(h.split(":")[0]) <= 15)
        self.assertEqual(pct(mid / sum(hours.values())), 79)
        for text in ["38%", "2.1×", "74%", "30%", "82%", "11%"]:
            self.assertIn(text, INDEX)
        self.assertIn("38%", README)
        self.assertIn("74%", README)
        self.assertIn("82%", README)
        self.assertIn("11%", README)


class Deliverables(unittest.TestCase):
    def test_ten_sql_queries_and_five_charts(self):
        queries = (ROOT / "sql" / "queries.sql").read_text(encoding="utf-8").split("-- Q")[1:]
        self.assertEqual(len(queries), 10)
        self.assertEqual(len(list((ROOT / "analysis" / "charts").glob("*.png"))), 5)

    def test_dashboard_says_when_data_fails_to_load(self):
        # Claim from commit 7fb74fc: a missing or malformed data.json shows a message, not a bare dash.
        self.assertIn('id="k-period"', INDEX)
        self.assertIn("Could not load the figures", INDEX)


@unittest.skipUnless(DB.exists(), "data/retail.db not present (not in git)")
class DatabaseClaims(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(DB)

    def tearDown(self):
        self.con.close()

    def test_row_counts_match_kpis(self):
        customers = self.con.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        orders = self.con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        self.assertEqual(customers, DATA["kpis"]["customers"])
        self.assertEqual(orders, DATA["kpis"]["orders"])

    def test_one_order_customers_round_to_35_percent(self):
        share = self.con.execute(
            "SELECT AVG(n = 1) FROM (SELECT customer_id, COUNT(*) AS n FROM orders GROUP BY customer_id)"
        ).fetchone()[0]
        self.assertEqual(round(share * 100), 35)

    def test_no_saturday_orders(self):
        n = self.con.execute("SELECT COUNT(*) FROM orders WHERE strftime('%w', invoice_date) = '6'").fetchone()[0]
        self.assertEqual(n, 0)


if __name__ == "__main__":
    unittest.main()
