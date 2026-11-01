# Retail Sales Analysis

**Live dashboard:** https://retail-sales-dashboard-one.vercel.app/
(also on the site: the [analysis notebook](https://retail-sales-dashboard-one.vercel.app/notebook.html) and the [10 SQL queries with outputs](https://retail-sales-dashboard-one.vercel.app/sql.html))

Where does an online gift shop's revenue come from, and when? I cleaned one year of sales with pandas, loaded it into SQLite, wrote 10 SQL queries, and built a one-page dashboard with 4 KPIs, 5 charts and 3 findings.

## Data
[Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail) by Daqing Chen, UCI Machine Learning Repository, licensed CC BY 4.0. Free to download, no login. It holds 541,909 invoice lines from a UK-based online gift retailer, 1 Dec 2010 to 9 Dec 2011.

The raw file is not in this folder's published output. To get it, download the zip from the UCI page and put `Online Retail.xlsx` in `data/raw/`.

## What is in each folder
| Folder | What it holds |
|---|---|
| `analysis/retail_analysis.ipynb` | Data quality checks, cleaning, exploration, 5 charts, written findings. Saved with its outputs. |
| `analysis/charts/` | The 5 charts as PNG files. |
| `sql/queries.sql` | 10 SQLite queries: joins, GROUP BY + HAVING, RANK, running total, LAG, second-highest, CASE buckets, LEFT JOIN. |
| `sql/results.md` | The output of every query. |
| `dashboard/` | The deployed site: `index.html` (dashboard), `data.json` (made by the notebook), `notebook.html`, `sql.html`. |
| `INTERVIEW.md` | Five interview questions about this project, with short answers. |

## Cleaning, in short
541,909 rows become 388,066:
1. Drop 5,268 exact duplicates.
2. Drop rows with no CustomerID (customer analysis needs it).
3. Drop cancellation rows **and** the purchase each one undid. One 80,995-unit order was cancelled 12 minutes later; without this step it would count as £168k of sales.
4. Drop non-product codes (postage, fees, discounts, manual adjustments, vouchers).
5. Keep Quantity > 0 and UnitPrice > 0.

## Findings
1. **The Christmas run-up drives the year.** September to November 2011 brought 38% of the 12 full months' revenue. November (£1.13M) was 2.1× the January–August monthly average.
2. **A small group of customers carries the business.** The top 20% of customers brought 74% of revenue. 35% of customers ordered only once.
3. **Sales are mostly British.** The UK brought 82% of revenue. The Netherlands, Ireland, Germany and France together brought 11%.

## Run it yourself
Python 3.11+.

```bash
pip install -r requirements.txt
```

```bash
cd analysis && jupyter nbconvert --to notebook --execute --inplace retail_analysis.ipynb
```

The notebook rebuilds `data/retail.db`, the charts and `dashboard/data.json`. Then run the SQL (standard library only):

```bash
python sql/run_queries.py
```

To refresh the notebook page on the site:

```bash
jupyter nbconvert --to html analysis/retail_analysis.ipynb --output-dir dashboard --output notebook
```

## Limits
- Only identified customers are counted (about a quarter of rows have no CustomerID).
- A cancellation is matched to a purchase only when customer, item and quantity are the same.
- One year of data, so the seasonal pattern is seen once.
- In SQL, each customer has one country (their most common one), so country totals can differ slightly from the notebook, which uses the country on each row.
