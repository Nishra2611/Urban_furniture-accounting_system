# Urban Furniture Accounting Frontend

React + Vite + TypeScript frontend for the Urban Furniture accounting application.

## Run

```bash
npm install
npm run dev
```

The frontend expects the FastAPI backend at `http://localhost:8000/api/v1` by default. Copy `.env.example` to `.env` if you need another API URL.

## Included
- Login, signup, forgot/reset password
- Three roles: User, Accountant, Administrator
- Odoo-inspired accounting workspace with compact sidebar and master-data list/kanban pattern
- Contacts, Products, Taxes, Chart of Accounts, Journals, Analytic Accounts, Budgets
- Sales Orders, Customer Invoices, Purchase Orders, Vendor Bills
- Customer and vendor payments
- Automatic-posting-aware accounting UI and manual Journal Entries with debit/credit validation
- Profit & Loss, Balance Sheet, General Ledger and Budget Report
- User portal for own invoices/bills/payments
- Admin user management

## Backend contract
This UI is wired to the supplied FastAPI `/api/v1` contract. It deliberately does not invent unsupported backend fields such as product category/image or budget revision fields. The visual structure follows the supplied mockups while using fields that the current backend actually accepts.
