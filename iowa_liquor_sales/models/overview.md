# Iowa Liquor Sales Analytics Platform

Welcome to the documentation for my Iowa Liquor Sales showcase. 
This platform translates raw, unorganized transaction data from Iowa state retail accounts 
into a highly optimized **Star Schema (Dimensional Model)** inside BigQuery.

### Core Business Objectives:
1. **Revenue Performance:** Slicing sales volumes and financial yield by product categorization.
2. **Operational Efficiency:** Measuring store-level ordering velocity and transaction density.

### Data Rigor & Governance:
Every layer is covered by structural dbt constraints testing for unique IDs, relationship integrity, and logical business constraints (e.g., non-negative financial inputs).