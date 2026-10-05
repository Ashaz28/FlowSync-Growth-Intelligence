# Optional PostgreSQL route

The downloadable app runs from `data/processed` and **does not require PostgreSQL**. SQL is included to demonstrate that the analyses also have a database-first implementation.

1. Create a local PostgreSQL database named `flowsync`.
2. Run `sql/00_create_tables.sql`.
3. Import the files in `data/raw/` in foreign-key order: `accounts`, `integrations`, `users`, `subscriptions`, `product_events`, `support_tickets`, `customer_feedback`, `ai_usage`, `experiments`.
4. Run `sql/01_core_analysis.sql` and optionally `sql/02_revenue_retention.sql`.

For psql, example after table creation: `\copy accounts FROM 'your/full/path/data/raw/accounts.csv' WITH (FORMAT csv, HEADER true, NULL '');`

**Scope:** The script covers month-end active paid accounts/MRR; the tested Python analytics code additionally computes the revenue movement waterfall.
