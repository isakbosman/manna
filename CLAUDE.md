# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Financial and Accounting Hub that functions as an agentic accounting firm. The system handles:

- Transaction downloads from personal and business accounts via Plaid API
- Transaction reconciliation
- Bookkeeping and financial planning
- Financial reporting (P&L, Balance Sheet, Cash Flow)

## Repository Structure

```
accounts/
├── data/          # Raw transaction and financial data storage
├── reports/       # Generated financial reports and owner packages
└── tools/         # Plaid API implementation for transaction pulling
```

## Key Components

### Reports (Owner Package)

The reports directory contains standardized financial packages including:

- P&L statements (YTD + prior month comparison)
- Balance Sheet
- Simple Cash Flow statements
- KPIs tracking:
  - Effective hourly rate
  - Utilization percentage
  - Accounts Receivable aging
  - Project margins
  - Cash runway
- One-page narrative summaries with highlights, risks, and action items

### Tools

Contains the Plaid API integration for pulling financial transactions from connected accounts.

## Development Notes

- This is currently a data-focused repository without traditional source code files
- The system appears to be in early development stages
- Integration with Plaid API is the primary technical component
- Focus is on financial data processing and report generation
- Before running any python or pip commands you must activate the conda environment manna
- Postgres is running locally the connection string is in the docker-compose.yml file