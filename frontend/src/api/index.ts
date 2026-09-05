import { api, err } from './client';
export { err };

export const auth = {
  login: (d: any) => api.post('/auth/login', d),
  signup: (d: any) => api.post('/auth/signup', d),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
  forgot: (email: string) => api.post('/auth/forgot-password', { email }),
  reset: (d: any) => api.post('/auth/reset-password', d),
  changePassword: (d: any) => api.post('/auth/change-password', d),
};

export const users = {
  list: () => api.get('/auth/users'),
  create: (d: any) => api.post('/auth/create-user', d),
};

export const masters = {
  contacts: {
    list: () => api.get('/contacts'),
    create: (d: any) => api.post('/contacts', d),
    update: (id: string | number, d: any) => api.put(`/contacts/${id}`, d),
    deactivate: (id: string | number) => api.post(`/contacts/${id}/deactivate`),
  },
  products: {
    list: () => api.get('/products'),
    create: (d: any) => api.post('/products', d),
    update: (id: string | number, d: any) => api.put(`/products/${id}`, d),
    deactivate: (id: string | number) => api.post(`/products/${id}/deactivate`),
  },
  taxes: {
    list: () => api.get('/taxes'),
    create: (d: any) => api.post('/taxes', d),
    update: (id: string | number, d: any) => api.put(`/taxes/${id}`, d),
    deactivate: (id: string | number) => api.post(`/taxes/${id}/deactivate`),
  },
  accounts: {
    list: () => api.get('/chart-of-accounts'),
    create: (d: any) => api.post('/chart-of-accounts', d),
    update: (id: string | number, d: any) => api.put(`/chart-of-accounts/${id}`, d),
    deactivate: (id: string | number) => api.post(`/chart-of-accounts/${id}/deactivate`),
  },
  journals: {
    list: () => api.get('/journals'),
    create: (d: any) => api.post('/journals', d),
    update: (id: string | number, d: any) => api.put(`/journals/${id}`, d),
    deactivate: (id: string | number) => api.post(`/journals/${id}/deactivate`),
  },
  analytics: {
    list: () => api.get('/analytic-accounts'),
    create: (d: any) => api.post('/analytic-accounts', d),
    update: (id: string | number, d: any) => api.put(`/analytic-accounts/${id}`, d),
    deactivate: (id: string | number) => api.post(`/analytic-accounts/${id}/deactivate`),
  },
  budgets: {
    list: () => api.get('/analytic-budgets'),
    create: (d: any) => api.post('/analytic-budgets', d),
    update: (id: string | number, d: any) => api.put(`/analytic-budgets/${id}`, d),
    deactivate: (id: string | number) => api.post(`/analytic-budgets/${id}/deactivate`),
  },
};

export const tx = {
  salesOrders: {
    list: () => api.get('/sales/orders'),
    create: (d: any) => api.post('/sales/orders', d),
    confirm: (id: string | number) => api.post(`/sales/orders/${id}/confirm`),
  },
  purchaseOrders: {
    list: () => api.get('/purchase/orders'),
    create: (d: any) => api.post('/purchase/orders', d),
    confirm: (id: string | number) => api.post(`/purchase/orders/${id}/confirm`),
  },
  invoices: {
    list: () => api.get('/sales/invoices'),
    create: (d: any) => api.post('/sales/invoices', d),
    post: (id: string | number) => api.post(`/sales/invoices/${id}/confirm`),
  },
  bills: {
    list: () => api.get('/purchase/bills'),
    create: (d: any) => api.post('/purchase/bills', d),
    post: (id: string | number) => api.post(`/purchase/bills/${id}/confirm`),
  },
  payments: {
    list: async () => {
      const [r1, r2] = await Promise.all([
        api.get('/sales/receipts').catch(() => ({ data: [] })),
        api.get('/purchase/payments').catch(() => ({ data: [] })),
      ]);
      return { data: [...(r1.data || []), ...(r2.data || [])] };
    },
    create: (d: any) => {
      if (d.payment_type === 'receipt' || d.invoice_id) {
        return api.post('/sales/receipts', {
          sale_invoice_id: Number(d.invoice_id || d.sale_invoice_id),
          amount: Number(d.amount),
          receipt_date: d.payment_date ? new Date(d.payment_date).toISOString().slice(0, 10) : new Date().toISOString().slice(0, 10),
          idempotency_key: d.reference || undefined,
        });
      } else {
        return api.post('/purchase/payments', {
          purchase_bill_id: Number(d.bill_id || d.purchase_bill_id),
          amount: Number(d.amount),
          payment_date: d.payment_date ? new Date(d.payment_date).toISOString().slice(0, 10) : new Date().toISOString().slice(0, 10),
          idempotency_key: d.reference || undefined,
        });
      }
    },
  },
};

export const accounting = {
  entries: {
    list: () => api.get('/journal-entries'),
    create: (d: any) => api.post('/journal-entries', d),
  },
};

export const reports = {
  pl: (params?: any) => api.get('/reports/profit-and-loss', { params }),
  bs: (params?: any) => api.get('/reports/balance-sheet', { params }),
  gl: (params?: any) => api.get('/reports/balance-sheet', { params }),
  budget: () => api.get('/reports/budget-report'),
};

export const dashboard = () => api.get('/dashboard');

export const portal = {
  dashboard: () => api.get('/portal/dashboard'),
  myInvoices: () => api.get('/portal/my-invoices'),
  myBills: () => api.get('/portal/my-bills'),
  myPayments: () => api.get('/portal/my-payments'),
  invoice: (id: string | number) => api.get(`/portal/invoices/${id}`),
  bill: (id: string | number) => api.get(`/portal/bills/${id}`),
  pay: (d: any) => api.post('/portal/pay', d),
  payBill: (d: any) => api.post('/portal/pay-bill', d),
};

