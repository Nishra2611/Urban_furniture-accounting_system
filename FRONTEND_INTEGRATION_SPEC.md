# Urban Furniture Accounting System — Backend Analysis & Frontend Integration Blueprint

This document provides a comprehensive, complete technical analysis of the backend API, data structures, authentication mechanisms, business rules, and endpoint contracts, along with a step-by-step blueprint to build a fully connected frontend application.

---

## 1. Executive Summary & Tech Stack Overview

### Backend Architecture
- **Framework**: FastAPI (Python 3.11+)
- **ORM & DB**: SQLAlchemy 2.0 + Alembic migrations + PostgreSQL 16 (or SQLite for isolated testing)
- **Authentication**: JWT (JSON Web Tokens) with `jti` revocation blacklist & BCrypt password hashing
- **Role-Based Access Control (RBAC)**: 3 Roles: `User`, `Accountant`, `Administrator`
- **Base URL**: `http://localhost:8000` (API base path: `/api/v1`)
- **Swagger Docs**: `http://localhost:8000/docs`

---

## 2. Authentication & Security Specifications

### Auth Mechanism
- **Header format**: `Authorization: Bearer <access_token>`
- **Token Type**: Bearer
- **Revocation**: Server-side token revocation on `/api/v1/auth/logout` via `jti` (JWT ID) checking against `revoked_tokens` table.

### User Roles & Permissions Matrix
| Feature / Route | User (Customer) | Accountant | Administrator |
| :--- | :---: | :---: | :---: |
| Auth (Signup/Login/Logout/Me/Forgot/Reset) | ✅ | ✅ | ✅ |
| User Portal (`/api/v1/portal/*`) | ✅ | ❌ (Unless linked to contact) | ❌ (Unless linked to contact) |
| User Creation (`/api/v1/auth/create-user`) | ❌ | ✅ | ✅ |
| Master Data (Contacts, Products, COA, Journals, Budgets) | ❌ | ✅ | ✅ |
| Sales Workflow (SO, Invoices, Receipts) | ❌ | ✅ | ✅ |
| Purchase Workflow (PO, Bills, Vendor Payments) | ❌ | ✅ | ✅ |
| Manual Journal Entries | ❌ | ✅ | ✅ |
| Dashboard & Financial Reports | ❌ | ✅ | ✅ |

### Validation Rules
- `login_id`: String, length between 6 and 12 characters (trimmed).
- `password`: Must be > 8 characters, containing uppercase, lowercase, number, and special character.
- **Account Lockout**: 5 consecutive failed login attempts locks account for 15 minutes.

---

## 3. Data Models & TypeScript Interfaces

Below are the exact TypeScript type definitions required for the frontend application.

```typescript
// --- Enums ---
export enum UserRole {
  USER = 'User',
  ACCOUNTANT = 'Accountant',
  ADMINISTRATOR = 'Administrator',
}

export enum DocumentStatus {
  DRAFT = 'Draft',
  CONFIRMED = 'Confirmed',
  POSTED = 'Posted',
  CANCELLED = 'Cancelled',
}

export enum PaymentStatus {
  UNPAID = 'Unpaid',
  PARTIALLY_PAID = 'Partially Paid',
  PAID = 'Paid',
}

export enum PartyType {
  CUSTOMER = 'Customer',
  VENDOR = 'Vendor',
  BOTH = 'Both',
}

export enum AccountType {
  ASSET = 'Asset',
  LIABILITY = 'Liability',
  EQUITY = 'Equity',
  INCOME = 'Income',
  EXPENSE = 'Expense',
}

// --- Auth Types ---
export interface UserOut {
  id: number;
  name?: string | null;
  login_id: string;
  email: string;
  role: UserRole;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string; // "bearer"
  role: UserRole;
}

export interface SignupRequest {
  login_id: string;
  email: string;
  password: str;
  re_password: str;
}

export interface LoginRequest {
  login_id: string;
  password: str;
}

export interface CreateUserRequest {
  name: string;
  login_id: string;
  email: string;
  role: UserRole;
  password: str;
  re_password: str;
}

// --- Master Data Types ---
export interface Contact {
  id: number;
  code: string;
  name: string;
  party_type: PartyType;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  receivable_account_id?: number | null;
  payable_account_id?: number | null;
  is_active: boolean;
}

export interface ContactCreate {
  code: string;
  name: string;
  party_type: PartyType;
  email?: string;
  phone?: string;
  address?: string;
  receivable_account_id?: number;
  payable_account_id?: number;
}

export interface Product {
  id: number;
  code: string;
  name: string;
  description?: string | null;
  sales_price: number | string;
  purchase_price: number | string;
  tax_rate: number | string;
  track_stock: boolean;
  stock_quantity: number | string;
  income_account_id?: number | null;
  expense_account_id?: number | null;
  is_active: boolean;
}

export interface ProductCreate {
  code: string;
  name: string;
  description?: string;
  sales_price?: number;
  purchase_price?: number;
  tax_rate?: number;
  track_stock?: boolean;
  income_account_id?: number;
  expense_account_id?: number;
}

export interface ChartOfAccount {
  id: number;
  code: string;
  name: string;
  account_type: AccountType;
  parent_id?: number | null;
  is_active: boolean;
}

export interface ChartOfAccountCreate {
  code: string;
  name: string;
  account_type: AccountType;
  parent_id?: number;
}

export interface Journal {
  id: number;
  code: string;
  name: string;
  journal_type: string;
  default_debit_account_id?: number | null;
  default_credit_account_id?: number | null;
  is_active: boolean;
}

export interface AnalyticAccount {
  id: number;
  code: string;
  name: string;
  is_active: boolean;
}

export interface AnalyticBudget {
  id: number;
  name: string;
  analytic_account_id: number;
  period_start: string; // ISO Date "YYYY-MM-DD"
  period_end: string;   // ISO Date "YYYY-MM-DD"
  budget_amount: number | string;
}

// --- Transaction Types ---
export interface LineItemCreate {
  product_id: number;
  quantity: number;
  unit_price?: number;
  tax_rate?: number;
}

export interface SalesOrderCreate {
  contact_id: number;
  order_date: string; // "YYYY-MM-DD"
  lines: LineItemCreate[];
}

export interface SaleInvoiceCreate {
  contact_id: number;
  invoice_date: string; // "YYYY-MM-DD"
  sales_order_id?: number;
  lines?: LineItemCreate[];
}

export interface ReceiptCreate {
  sale_invoice_id: number;
  amount: number;
  receipt_date: string; // "YYYY-MM-DD"
  idempotency_key?: string;
}

export interface PurchaseOrderCreate {
  contact_id: number;
  order_date: string;
  lines: LineItemCreate[];
}

export interface PurchaseBillCreate {
  contact_id: number;
  bill_date: string;
  purchase_order_id?: number;
  lines?: LineItemCreate[];
}

export interface VendorPaymentCreate {
  purchase_bill_id: number;
  amount: number;
  payment_date: string;
  idempotency_key?: string;
}

export interface JournalEntryLineCreate {
  account_id: number;
  debit: number;
  credit: number;
  description?: string;
}

export interface JournalEntryCreate {
  journal_id: number;
  entry_date: string; // "YYYY-MM-DD"
  narration?: string;
  analytic_account_id?: number;
  lines: JournalEntryLineCreate[];
}

// --- Report & Dashboard Types ---
export interface DashboardSummary {
  sales: { all: number; confirmed: number; draft: number };
  purchase: { all: number; confirmed: number; draft: number };
  budget: { achieved: number; budget: number; committed: number };
}

export interface AccountBalance {
  code: string;
  name: string;
  balance: number;
}

export interface BalanceSheetReport {
  assets: AccountBalance[];
  liabilities: AccountBalance[];
  equity: AccountBalance[];
  total_assets: number;
  total_liabilities: number;
  total_equity: number;
}

export interface ProfitAndLossReport {
  income: AccountBalance[];
  expense: AccountBalance[];
  total_income: number;
  total_expense: number;
  net_profit: number;
}

export interface PortalInvoice {
  id: number;
  invoice_number: string;
  invoice_date: string;
  total_amount: string;
  amount_paid: string;
  payment_status: PaymentStatus;
}
```

---

## 4. Full API Endpoint Reference

### 🔐 Authentication (`/api/v1/auth`)

| Endpoint | Method | Auth Required | Request Body | Response (Status Code) |
| :--- | :--- | :---: | :--- | :--- |
| `/api/v1/auth/signup` | POST | ❌ | `SignupRequest` | `UserOut` (201) |
| `/api/v1/auth/login` | POST | ❌ | `LoginRequest` | `TokenResponse` (200) |
| `/api/v1/auth/logout` | POST | ✅ | None | None (204) |
| `/api/v1/auth/create-user` | POST | ✅ (Acct/Admin) | `CreateUserRequest` | `UserOut` (201) |
| `/api/v1/auth/me` | GET | ✅ | None | `UserOut` (200) |
| `/api/v1/auth/forgot-password` | POST | ❌ | `{ email }` | None (204) |
| `/api/v1/auth/reset-password` | POST | ❌ | `{ token, new_password, re_password }` | None (204) |

---

### 📦 Master Data (`/api/v1`)

| Endpoint | Method | Auth Required | Request Body | Response (Status Code) |
| :--- | :--- | :---: | :--- | :--- |
| `/api/v1/contacts` | GET | ✅ (Acct/Admin) | None | `Contact[]` (200) |
| `/api/v1/contacts` | POST | ✅ (Acct/Admin) | `ContactCreate` | `Contact` (201) |
| `/api/v1/contacts/{id}/deactivate` | POST | ✅ (Acct/Admin) | None | `Contact` (200) |
| `/api/v1/products` | GET | ✅ (Acct/Admin) | None | `Product[]` (200) |
| `/api/v1/products` | POST | ✅ (Acct/Admin) | `ProductCreate` | `Product` (201) |
| `/api/v1/products/{id}/deactivate` | POST | ✅ (Acct/Admin) | None | `Product` (200) |
| `/api/v1/chart-of-accounts` | GET | ✅ (Acct/Admin) | None | `ChartOfAccount[]` (200) |
| `/api/v1/chart-of-accounts` | POST | ✅ (Acct/Admin) | `ChartOfAccountCreate` | `ChartOfAccount` (201) |
| `/api/v1/journals` | GET | ✅ (Acct/Admin) | None | `Journal[]` (200) |
| `/api/v1/journals` | POST | ✅ (Acct/Admin) | `JournalCreate` | `Journal` (201) |
| `/api/v1/analytic-accounts` | POST | ✅ (Acct/Admin) | `{ code, name }` | `AnalyticAccount` (201) |
| `/api/v1/analytic-budgets` | GET | ✅ (Acct/Admin) | None | `AnalyticBudget[]` (200) |
| `/api/v1/analytic-budgets` | POST | ✅ (Acct/Admin) | `AnalyticBudgetCreate` | `AnalyticBudget` (201) |

---

### 🛒 Sales Module (`/api/v1/sales`)

| Endpoint | Method | Auth Required | Request Body | Response (Status Code) |
| :--- | :--- | :---: | :--- | :--- |
| `/api/v1/sales/orders` | POST | ✅ (Acct/Admin) | `SalesOrderCreate` | `{ id, order_number, status, total_amount }` (201) |
| `/api/v1/sales/orders/{id}/confirm` | POST | ✅ (Acct/Admin) | None | `{ id, status }` (200) |
| `/api/v1/sales/invoices` | POST | ✅ (Acct/Admin) | `SaleInvoiceCreate` | `{ id, invoice_number, status, total_amount }` (201) |
| `/api/v1/sales/invoices/{id}/confirm` | POST | ✅ (Acct/Admin) | None | `{ id, status }` (200) |
| `/api/v1/sales/receipts` | POST | ✅ (Acct/Admin) | `ReceiptCreate` | `{ id, receipt_number, amount }` (201) |

---

### 🛍️ Purchase Module (`/api/v1/purchase`)

| Endpoint | Method | Auth Required | Request Body | Response (Status Code) |
| :--- | :--- | :---: | :--- | :--- |
| `/api/v1/purchase/orders` | POST | ✅ (Acct/Admin) | `PurchaseOrderCreate` | `{ id, order_number, status, total_amount }` (201) |
| `/api/v1/purchase/orders/{id}/confirm` | POST | ✅ (Acct/Admin) | None | `{ id, status }` (200) |
| `/api/v1/purchase/bills` | POST | ✅ (Acct/Admin) | `PurchaseBillCreate` | `{ id, bill_number, status, total_amount }` (201) |
| `/api/v1/purchase/bills/{id}/confirm` | POST | ✅ (Acct/Admin) | None | `{ id, status }` (200) |
| `/api/v1/purchase/payments` | POST | ✅ (Acct/Admin) | `VendorPaymentCreate` | `{ id, payment_number, amount }` (201) |

---

### 📖 Manual Accounting Journal Entries (`/api/v1/journal-entries`)

| Endpoint | Method | Auth Required | Request Body | Response (Status Code) |
| :--- | :--- | :---: | :--- | :--- |
| `/api/v1/journal-entries` | POST | ✅ (Acct/Admin) | `JournalEntryCreate` | `{ id, entry_number, status }` (201) |

---

### 📊 Dashboard & Financial Reports (`/api/v1`)

| Endpoint | Method | Auth Required | Request Body | Response (Status Code) |
| :--- | :--- | :---: | :--- | :--- |
| `/api/v1/dashboard` | GET | ✅ (Acct/Admin) | None | `DashboardSummary` (200) |
| `/api/v1/reports/balance-sheet` | GET | ✅ (Acct/Admin) | None | `BalanceSheetReport` (200) |
| `/api/v1/reports/profit-and-loss` | GET | ✅ (Acct/Admin) | None | `ProfitAndLossReport` (200) |
| `/api/v1/reports/budget-report` | GET | ✅ (Acct/Admin) | None | `{ achieved, budget, committed }` (200) |

---

### 👤 Restricted Customer Portal (`/api/v1/portal`)

| Endpoint | Method | Auth Required | Request Body | Response (Status Code) |
| :--- | :--- | :---: | :--- | :--- |
| `/api/v1/portal/my-invoices` | GET | ✅ (User Role) | None | `PortalInvoice[]` (200) |
| `/api/v1/portal/pay` | POST | ✅ (User Role) | `ReceiptCreate` | `{ id, receipt_number, amount }` (200) |

---

## 5. Critical Business Rules & Workflows

1. **Double-Entry Balance Invariant**:
   - For every manual journal entry or automatic document confirmation, `Sum(Debits) == Sum(Credits)`.
   - Each line item can have a positive `debit` XOR a positive `credit`.
2. **Sales Lifecycle**:
   - `Sales Order (Draft)` ➔ `Sales Order (Confirmed)` ➔ `Sale Invoice (Draft)` ➔ `Sale Invoice (Confirmed & Posted to SALES Journal)` ➔ `Receipt (Paid/Partially Paid)`
3. **Purchase Lifecycle**:
   - `Purchase Order (Draft)` ➔ `Purchase Order (Confirmed)` ➔ `Purchase Bill (Draft)` ➔ `Purchase Bill (Confirmed & Posted to PURCHASE Journal)` ➔ `Vendor Payment`
4. **Idempotency Keys**:
   - Payment endpoints (`/receipts`, `/payments`, `/portal/pay`) accept an optional `idempotency_key`. Sending duplicate submissions with the same key returns the existing receipt/payment record without duplicate debits/credits.
5. **Data Protection for Customer Portal**:
   - Endpoints under `/api/v1/portal/*` automatically scope DB queries to `user.contact_id`. Trying to pay another customer's invoice ID yields `404 Not Found`.

---

## 6. Backend CORS Setup Requirement

To allow a frontend running on `http://localhost:5173` (Vite) or `http://localhost:3000` to communicate with `http://localhost:8000`, add `CORSMiddleware` in `app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Or ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 7. Recommended Frontend Folder & Component Blueprint

```
frontend/
├── public/
├── src/
│   ├── api/
│   │   ├── axiosInstance.ts      # Axios setup with Bearer token & 401 interceptor
│   │   ├── auth.ts               # Auth API calls
│   │   ├── masterData.ts         # Contacts, Products, COA, Journals APIs
│   │   ├── sales.ts              # Sales Orders, Invoices, Receipts APIs
│   │   ├── purchase.ts           # Purchase Orders, Bills, Payments APIs
│   │   ├── accounting.ts         # Journal Entry APIs
│   │   ├── reports.ts            # Dashboard & Financial Reports APIs
│   │   └── portal.ts             # Customer Portal APIs
│   ├── components/
│   │   ├── common/               # Navbar, Sidebar, StatCards, Modal, Table, Badge
│   │   ├── layout/               # AdminLayout, UserLayout, AuthLayout
│   │   └── ProtectedRoute.tsx    # Role-based route guard
│   ├── context/
│   │   └── AuthContext.tsx       # Auth state (user, token, role, login, logout)
│   ├── pages/
│   │   ├── auth/                 # Login, Signup, ForgotPassword, ResetPassword
│   │   ├── dashboard/            # Executive Dashboard (Sales, Purchases, Budgets)
│   │   ├── masterData/           # Contacts, Products, ChartOfAccounts, Journals
│   │   ├── sales/                # SalesOrders, SaleInvoices, RecordReceipt
│   │   ├── purchase/             # PurchaseOrders, PurchaseBills, RecordPayment
│   │   ├── accounting/           # ManualJournalEntries
│   │   ├── reports/              # BalanceSheet, ProfitAndLoss, BudgetReport
│   │   ├── admin/                # CreateUser
│   │   └── portal/               # MyInvoices, PayDues
│   ├── types/
│   │   └── api.ts                # TypeScript interfaces (from section 3 above)
│   ├── App.tsx                   # Routes configuration
│   └── main.tsx
├── package.json
└── vite.config.ts
```

---

## 8. Sample Axios Client Interceptor Setup (`src/api/axiosInstance.ts`)

```typescript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach JWT Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response Interceptor: Handle 401 Unauthorized
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```
