# Iowa Liquor Sales Analytics

> End-to-end Analytics Engineering showcase demonstrating modern data modeling, transformation, testing, and reporting using dbt and Google BigQuery.

---

# Project Overview

This project transforms the public **Iowa Liquor Sales** dataset into an analytics-ready data warehouse using a layered dbt architecture.

The objective is to demonstrate Analytics Engineering best practices by designing a maintainable star schema, 
implementing automated data quality tests, and delivering business-ready datasets for reporting in Google Looker.

The final solution follows a modern ELT workflow:

```
Google BigQuery Public Dataset
            │
            ▼
      Source Layer
            │
            ▼
      Staging Models
            │
            ▼
     Star Schema (Marts)
            │
            ▼
     Reporting Models
            │
            ▼
    Google Looker Dashboard
```

## dbt DAG

The following graph shows the lineage of the dbt models used in this project.

![dbt DAG](assets/iowa_liquor_sales_dag.png)


# Objectives

This showcase demonstrates how to:

- Design a dimensional data model
- Build scalable dbt projects
- Apply modern Analytics Engineering practices
- Create reusable fact and dimension tables
- Implement automated data quality testing
- Produce analytics-ready datasets for business intelligence
- Document data models using dbt YAML metadata


# Dataset

**Source**

Google BigQuery Public Dataset

```
bigquery-public-data.iowa_liquor_sales.sales
```

The dataset contains historical wholesale liquor transactions between the State of Iowa and licensed retail stores.

Each record represents a single invoice line item including information about:

- Store
- Product
- Vendor
- Sales Amount
- Bottle Volume
- Transaction Date

---

# Architecture

The project follows a layered dbt architecture.

```
models/

├── 1_staging
│
├── 2_marts
│
└── 3_reporting
```
Note: The intermediate layer was dropped as it is not required for this particular showcase.

### Staging Layer

The staging layer standardizes the raw source data by:

- Renaming columns
- Applying data types
- Removing inconsistencies
- Creating reusable source models

---

### Mart Layer

The mart layer exposes a dimensional model optimized for analytics and reporting.

```
                dim_date
                   │
                   │
dim_store ─── fct_liquor_sales ─── dim_product
                   │
                   │
               dim_vendor    
```

### Reporting Layer

While the core warehouse follows a dimensional star schema, dedicated reporting models are created for 
Google Looker.  
These model pre-join the fact and dimension tables to reduce client-side processing, improve dashboard performance, 
and keep business logic centralized in dbt.

# Data Model

## Fact Table

### fct_liquor_sales

The central fact table contains one record per wholesale liquor sales line item.

### Grain

> One row per invoice line item.

### Key Measures

- Wholesale Revenue
- Wholesale Profit
- Estimated Retail Revenue
- Bottles Sold
- Volume Sold (Liters)

---

## Dimensions

### dim_date

Reusable calendar dimension supporting time intelligence.

Example attributes include:

- Year
- Quarter
- Month
- Week
- Day
- Weekend Indicator

---

### dim_store

Store dimension containing descriptive and aggregated information for every retail location.

Includes:

- Geographic attributes
- Lifetime revenue
- Total orders
- Customer tier
- Store activity status

---

### dim_product

Product dimension containing descriptive information about each liquor product.

Includes:

- Product description
- Product category
- Bottle volume
- Bottles per case

To ensure one record per product, changing product descriptions in the source data are resolved 
by retaining the latest known descriptive attributes based on the most recent transaction.

---
## Reporting Tables

### rpt_liquor_sales_dashboard

The main reporting table for Google Looker. Joins the fact table with the dimension tables.

### rpt_pipeline_health (Pipeline Monitoring)

The project also includes a dedicated monitoring model.

Tracks operational metrics including:

- Source freshness
- Rows processed
- Missing categories
- Missing stores
- Invalid sales values

This model demonstrates how operational metadata can be modeled alongside business data.

---

# Data Quality

The project uses dbt tests to validate model integrity.

Current tests include:

- Primary key uniqueness
- Not Null constraints
- Referential integrity

---

# Dashboard

The mart layer is designed specifically for reporting in **Google Looker**.

[![Looker Dashboard](assets/iowa_sales_dashboard.jpg)](https://datastudio.google.com/s/lqpDEqjDORI)

The dashboard includes:

- Executive KPI overview
- Revenue/profit trends
- Profit analysis
- Geographic sales distribution
- Pipeline and data metrics

---

# Skills Demonstrated

## Analytics Engineering

- dbt
- SQL
- BigQuery
- ELT Pipelines
- Modular Data Modeling
- Star Schema Design
- Dimensional Modeling

## Data Quality

- Automated Testing
- YAML Documentation
- Data Validation
- Pipeline Monitoring

## Analytics

- KPI Design
- Business Metrics
- Revenue Analysis
- Profit Analysis
- Geographic Analysis

## Software Engineering

- Git
- GitHub
- Version Control
- Reproducible Development

# Project Status

**Status:** ✅ Released (Maintenance Mode)
