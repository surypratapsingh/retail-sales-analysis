# Interview questions on this project

**1. Walk me through how you cleaned the data.**
I started with 541,909 rows and ended with 388,066. I dropped exact duplicates and rows with no CustomerID, because the analysis is about customers. I removed cancellations and also the purchases they undid. I dropped non-product codes like postage and bank charges, and kept only positive quantities and prices. I logged the row count after each step, so every drop can be explained.

**2. What was the most important data problem you found?**
Cancellations. Dropping only the "C" invoices leaves the original orders in, so the totals are wrong. The biggest line in the file, 80,995 paper birds worth £168k, was cancelled 12 minutes later. I matched each cancellation to a purchase with the same customer, item and quantity, and removed both. One £38,970 order was reversed through a "Manual" line instead, so I found it by checking large manual refunds and removed it by invoice number.

**3. How did you find that 20% of customers bring 74% of revenue?**
I added up revenue per customer, sorted from highest to lowest, and took the running share of total revenue (a cumulative sum divided by the total). The value at the 20% mark is 74%. In SQL I would do the same with `SUM(total) OVER (ORDER BY total DESC)` divided by the overall sum.

**4. How do you get the second-highest value in SQL, and what about ties?**
`SELECT MAX(total) FROM spend WHERE total < (SELECT MAX(total) FROM spend)` returns the second-highest distinct value. With window functions, `DENSE_RANK() OVER (ORDER BY total DESC) = 2` gives the same result, ties included. `ROW_NUMBER()` would pick one row at random among ties, and `RANK()` would skip 2 if two customers tie for first.

**5. What would you recommend to the business, and what would you check next?**
Plan stock and staff from August, because September to November brings 38% of the year's revenue. Give the top customers personal service, and win back one-time buyers, who are 35% of customers. Test growth in the Netherlands, Ireland, Germany and France. Next I would add a second year of data to confirm the seasonal pattern. I would also run a cohort analysis to see how many new customers order again within 90 days.
