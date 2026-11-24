"""Cleaning steps for the Online Retail file, as used by retail_analysis.ipynb.

The logic is moved here unchanged from the notebook's cleaning cell. Needs pandas.
The notebook calls clean(raw) on the sheet read with pd.read_excel(..., dtype={'InvoiceNo': str, 'StockCode': str}).
"""
import pandas as pd

NON_PRODUCT = {'POST', 'D', 'C2', 'M', 'BANK CHARGES', 'AMAZONFEE', 'B', 'CRUK', 'DOT', 'S', 'PADS'}


def clean(raw):
    """Return (df, steps): the cleaned line items, and (label, row count) after each step."""
    steps = [('Raw rows', len(raw))]
    df = raw.drop_duplicates()
    steps.append(('After dropping duplicates', len(df)))

    df = df[df.CustomerID.notna()].copy()
    df['CustomerID'] = df.CustomerID.astype(int)
    steps.append(('After dropping missing CustomerID', len(df)))

    is_cancel = df.InvoiceNo.str.startswith('C')
    cancels, df = df[is_cancel], df[~is_cancel].copy()
    steps.append(('After dropping cancellation rows', len(df)))

    # Match each cancellation to one earlier purchase of the same item, quantity and customer, then drop that purchase.
    # ponytail: one-to-one match in date order; partial cancellations (smaller quantity) are not matched.
    key = ['CustomerID', 'StockCode', 'Quantity']
    undone = cancels.assign(Quantity=-cancels.Quantity)[key]
    undone = undone.assign(n=undone.groupby(key).cumcount(), cancelled=True)
    df = df.sort_values('InvoiceDate')
    df['n'] = df.groupby(key).cumcount()
    df = df.merge(undone, on=key + ['n'], how='left')
    df = df[df.cancelled.isna()].drop(columns=['n', 'cancelled'])
    # Invoice 556444 (60 wicker picnic baskets, £38,970) was reversed by a 'Manual' line of the same amount
    # (C556445), which the item match above cannot see. It is the only such case for a product line.
    df = df[~((df.InvoiceNo == '556444') & (df.StockCode == '22502'))]
    steps.append(('After dropping purchases that were cancelled', len(df)))

    df = df[~df.StockCode.str.upper().isin(NON_PRODUCT) & ~df.StockCode.str.startswith('gift_')]
    steps.append(('After dropping non-product codes', len(df)))

    df = df[(df.Quantity > 0) & (df.UnitPrice > 0)].copy()
    steps.append(('After keeping Quantity > 0 and UnitPrice > 0', len(df)))

    df['Description'] = df.Description.str.strip()
    df['Revenue'] = df.Quantity * df.UnitPrice
    return df, steps
