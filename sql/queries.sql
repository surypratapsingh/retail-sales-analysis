-- Ten SQLite queries on data/retail.db (built by analysis/retail_analysis.ipynb).
-- Tables: customers(customer_id, country), products(stock_code, description),
--         orders(invoice_no, customer_id, invoice_date), order_items(invoice_no, stock_code, quantity, unit_price)
-- Run them all with: python sql/run_queries.py

-- Q1. Headline KPIs: revenue, orders, customers, average order value
SELECT ROUND(SUM(oi.quantity * oi.unit_price), 2)                                 AS revenue,
       COUNT(DISTINCT o.invoice_no)                                               AS orders,
       COUNT(DISTINCT o.customer_id)                                              AS customers,
       ROUND(SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT o.invoice_no), 2)  AS avg_order_value
FROM orders o
JOIN order_items oi ON oi.invoice_no = o.invoice_no;

-- Q2. Revenue and orders by month
SELECT strftime('%Y-%m', o.invoice_date)           AS month,
       COUNT(DISTINCT o.invoice_no)                AS orders,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)  AS revenue
FROM orders o
JOIN order_items oi ON oi.invoice_no = o.invoice_no
GROUP BY month
ORDER BY month;

-- Q3. Top 10 countries by revenue, with share of total (three-table join)
SELECT c.country,
       COUNT(DISTINCT c.customer_id)               AS customers,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)  AS revenue,
       ROUND(100.0 * SUM(oi.quantity * oi.unit_price)
             / (SELECT SUM(quantity * unit_price) FROM order_items), 1) AS pct_of_revenue
FROM customers c
JOIN orders o       ON o.customer_id = c.customer_id
JOIN order_items oi ON oi.invoice_no = o.invoice_no
GROUP BY c.country
ORDER BY revenue DESC
LIMIT 10;

-- Q4. Average order value by country, only countries with at least 10 customers (GROUP BY + HAVING)
WITH order_totals AS (
  SELECT o.invoice_no, o.customer_id, SUM(oi.quantity * oi.unit_price) AS total
  FROM orders o
  JOIN order_items oi ON oi.invoice_no = o.invoice_no
  GROUP BY o.invoice_no
)
SELECT c.country,
       COUNT(DISTINCT c.customer_id)  AS customers,
       COUNT(*)                       AS orders,
       ROUND(AVG(t.total), 2)         AS avg_order_value
FROM order_totals t
JOIN customers c ON c.customer_id = t.customer_id
GROUP BY c.country
HAVING COUNT(DISTINCT c.customer_id) >= 10
ORDER BY avg_order_value DESC;

-- Q5. Top 10 products by revenue
SELECT p.stock_code,
       p.description,
       SUM(oi.quantity)                            AS units,
       ROUND(SUM(oi.quantity * oi.unit_price), 2)  AS revenue
FROM order_items oi
JOIN products p ON p.stock_code = oi.stock_code
GROUP BY p.stock_code
ORDER BY revenue DESC
LIMIT 10;

-- Q6. Top 3 products in each of the 5 biggest countries (RANK window function)
WITH top_countries AS (
  SELECT c.country
  FROM customers c
  JOIN orders o       ON o.customer_id = c.customer_id
  JOIN order_items oi ON oi.invoice_no = o.invoice_no
  GROUP BY c.country
  ORDER BY SUM(oi.quantity * oi.unit_price) DESC
  LIMIT 5
),
sales AS (
  SELECT c.country, p.description, SUM(oi.quantity * oi.unit_price) AS revenue
  FROM order_items oi
  JOIN orders o    ON o.invoice_no = oi.invoice_no
  JOIN customers c ON c.customer_id = o.customer_id
  JOIN products p  ON p.stock_code = oi.stock_code
  WHERE c.country IN (SELECT country FROM top_countries)
  GROUP BY c.country, p.description
),
ranked AS (
  SELECT *, RANK() OVER (PARTITION BY country ORDER BY revenue DESC) AS rnk
  FROM sales
)
SELECT country, rnk, description, ROUND(revenue, 2) AS revenue
FROM ranked
WHERE rnk <= 3
ORDER BY country, rnk;

-- Q7. Running total of revenue and month-over-month growth (SUM OVER, LAG)
-- Note: 2011-12 only covers 1-9 December, so its drop is not a real decline.
WITH monthly AS (
  SELECT strftime('%Y-%m', o.invoice_date) AS month, SUM(oi.quantity * oi.unit_price) AS revenue
  FROM orders o
  JOIN order_items oi ON oi.invoice_no = o.invoice_no
  GROUP BY month
)
SELECT month,
       ROUND(revenue, 2)                                AS revenue,
       ROUND(SUM(revenue) OVER (ORDER BY month), 2)     AS running_total,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
             / LAG(revenue) OVER (ORDER BY month), 1)   AS growth_pct
FROM monthly
ORDER BY month;

-- Q8. Second-highest spending customer (classic subquery; DENSE_RANK() = 2 gives the same answer)
WITH spend AS (
  SELECT o.customer_id, SUM(oi.quantity * oi.unit_price) AS total
  FROM orders o
  JOIN order_items oi ON oi.invoice_no = o.invoice_no
  GROUP BY o.customer_id
)
SELECT s.customer_id, c.country, ROUND(s.total, 2) AS total_spend
FROM spend s
JOIN customers c ON c.customer_id = s.customer_id
WHERE s.total = (SELECT MAX(total) FROM spend WHERE total < (SELECT MAX(total) FROM spend));

-- Q9. How many orders customers place (CASE buckets)
WITH per_customer AS (
  SELECT customer_id, COUNT(*) AS orders FROM orders GROUP BY customer_id
)
SELECT CASE WHEN orders = 1  THEN '1 order'
            WHEN orders <= 5 THEN '2-5 orders'
            WHEN orders <= 20 THEN '6-20 orders'
            ELSE '21+ orders' END                                  AS bucket,
       COUNT(*)                                                    AS customers,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM per_customer), 1) AS pct_of_customers
FROM per_customer
GROUP BY bucket
ORDER BY MIN(orders);

-- Q10. Lapsed customers: no order in the last 90 days of data, by country (LEFT JOIN)
WITH recent AS (
  SELECT DISTINCT customer_id
  FROM orders
  WHERE invoice_date >= date((SELECT MAX(invoice_date) FROM orders), '-90 days')
)
SELECT c.country,
       COUNT(*)                                              AS customers,
       SUM(r.customer_id IS NULL)                            AS lapsed_90d,
       ROUND(100.0 * SUM(r.customer_id IS NULL) / COUNT(*), 1) AS lapsed_pct
FROM customers c
LEFT JOIN recent r ON r.customer_id = c.customer_id
GROUP BY c.country
HAVING COUNT(*) >= 20
ORDER BY customers DESC;
