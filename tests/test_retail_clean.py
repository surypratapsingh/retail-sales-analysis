"""Checks the cleaning steps (analysis/retail_clean.py) on a small made-up sheet.

Each row below is made up and stands for one rule: a duplicate, a missing customer, a cancellation and the
purchase it undoes, a non-product code, a zero quantity, a zero price, and two rows that must survive.
Needs pandas (already listed in requirements.txt). Skipped if pandas is not installed.

Standard library only apart from pandas:  python -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "analysis"))

try:
    import pandas as pd
    import retail_clean
except ImportError:
    pd = None

COLUMNS = ['InvoiceNo', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'UnitPrice', 'CustomerID', 'Country']


def sample_sheet():
    d = pd.Timestamp
    rows = [
        ['1001', '84001', 'TEST ITEM A', 2, d('2010-12-01 08:00'), 3.0, 17001.0, 'Testland'],   # bought, later cancelled
        ['1001', '84001', 'TEST ITEM A', 2, d('2010-12-01 08:00'), 3.0, 17001.0, 'Testland'],   # exact duplicate
        ['1002', '84002', 'TEST ITEM B', 1, d('2010-12-01 09:00'), 5.0, float('nan'), 'Testland'],  # no CustomerID
        ['C1003', '84001', 'TEST ITEM A', -2, d('2010-12-02 10:00'), 3.0, 17001.0, 'Testland'],  # cancellation
        ['1004', 'POST', 'POSTAGE', 1, d('2010-12-03 11:00'), 18.0, 17002.0, 'Testland'],       # non-product code
        ['1005', '84003', 'TEST ITEM C', 0, d('2010-12-04 12:00'), 2.0, 17003.0, 'Testland'],   # quantity 0
        ['1006', '84004', 'TEST ITEM D', 3, d('2010-12-04 13:00'), 0.0, 17003.0, 'Testland'],   # price 0
        ['1007', '84005', 'TEST ITEM E  ', 4, d('2010-12-05 14:00'), 2.5, 17004.0, 'Otherland'],  # kept, trailing spaces
        ['1008', 'gift_0001_40', 'Dotcom gift', 1, d('2010-12-05 15:00'), 10.0, 17004.0, 'Otherland'],  # gift code
        ['1010', '84006', 'TEST ITEM F', 6, d('2010-12-06 16:00'), 1.5, 17005.0, 'Otherland'],  # kept
    ]
    return pd.DataFrame(rows, columns=COLUMNS)


@unittest.skipIf(pd is None, "pandas is not installed")
class CleanSteps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df, cls.steps = retail_clean.clean(sample_sheet())

    def test_row_counts_after_each_step(self):
        self.assertEqual(self.steps, [
            ('Raw rows', 10),
            ('After dropping duplicates', 9),
            ('After dropping missing CustomerID', 8),
            ('After dropping cancellation rows', 7),
            ('After dropping purchases that were cancelled', 6),
            ('After dropping non-product codes', 4),
            ('After keeping Quantity > 0 and UnitPrice > 0', 2),
        ])

    def test_only_the_two_valid_rows_survive(self):
        self.assertEqual(list(self.df.InvoiceNo), ['1007', '1010'])

    def test_revenue_and_description(self):
        self.assertEqual(list(self.df.Revenue), [10.0, 9.0])  # 4 x 2.5 and 6 x 1.5
        self.assertEqual(list(self.df.Description), ['TEST ITEM E', 'TEST ITEM F'])

    def test_customer_id_is_an_integer(self):
        self.assertEqual(list(self.df.CustomerID), [17004, 17005])
        self.assertEqual(str(self.df.CustomerID.dtype), 'int64')


if __name__ == "__main__":
    unittest.main()
