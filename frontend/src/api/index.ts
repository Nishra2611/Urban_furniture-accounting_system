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
  delete: (id: string | number) => api.delete(`/auth/users/${id}`),
  bulkDelete: (ids: (string | number)[]) => api.post('/auth/users/bulk-delete', { ids: ids.map(Number) }),
};

export const masters = {
  contacts: {
    list: (includeArchived?: boolean) => api.get('/contacts', { params: { include_archived: includeArchived } }),
    create: (d: any) => api.post('/contacts', d),
    update: (id: string | number, d: any) => api.put(`/contacts/${id}`, d),
    deactivate: (id: string | number) => api.post(`/contacts/${id}/deactivate`),
    activate: (id: string | number) => api.post(`/contacts/${id}/activate`),
    delete: (id: string | number) => api.delete(`/contacts/${id}`),
    bulkArchive: (ids: (string | number)[]) => api.post('/contacts/bulk-archive', { ids: ids.map(Number) }),
    bulkDelete: (ids: (string | number)[]) => api.post('/contacts/bulk-delete', { ids: ids.map(Number) }),
  },
  products: {
    list: (includeArchived?: boolean) => api.get('/products', { params: { include_archived: includeArchived } }),
    create: (d: any) => api.post('/products', d),
    update: (id: string | number, d: any) => api.put(`/products/${id}`, d),
    deactivate: (id: string | number) => api.post(`/products/${id}/deactivate`),
    activate: (id: string | number) => api.post(`/products/${id}/activate`),
    delete: (id: string | number) => api.delete(`/products/${id}`),
    bulkArchive: (ids: (string | number)[]) => api.post('/products/bulk-archive', { ids: ids.map(Number) }),
    bulkDelete: (ids: (string | number)[]) => api.post('/products/bulk-delete', { ids: ids.map(Number) }),
  },
  taxes: {
    list: (includeArchived?: boolean) => api.get('/taxes', { params: { include_archived: includeArchived } }),
    create: (d: any) => api.post('/taxes', d),
    update: (id: string | number, d: any) => api.put(`/taxes/${id}`, d),
    deactivate: (id: string | number) => api.post(`/taxes/${id}/deactivate`),
    activate: (id: string | number) => api.post(`/taxes/${id}/activate`),
    delete: (id: string | number) => api.delete(`/taxes/${id}`),
    bulkArchive: (ids: (string | number)[]) => api.post('/taxes/bulk-archive', { ids: ids.map(Number) }),
    bulkDelete: (ids: (string | number)[]) => api.post('/taxes/bulk-delete', { ids: ids.map(Number) }),
  },
  accounts: {
    list: (includeArchived?: boolean) => api.get('/chart-of-accounts', { params: { include_archived: includeArchived } }),
    create: (d: any) => api.post('/chart-of-accounts', d),
    update: (id: string | number, d: any) => api.put(`/chart-of-accounts/${id}`, d),
    deactivate: (id: string | number) => api.post(`/chart-of-accounts/${id}/deactivate`),
  },
  journals: {
    list: (includeArchived?: boolean) => api.get('/journals', { params: { include_archived: includeArchived } }),
    create: (d: any) => api.post('/journals', d),
    update: (id: string | number, d: any) => api.put(`/journals/${id}`, d),
    deactivate: (id: string | number) => api.post(`/journals/${id}/deactivate`),
  },
  analytics: {
    list: (includeArchived?: boolean) => api.get('/analytic-accounts', { params: { include_archived: includeArchived } }),
    create: (d: any) => api.post('/analytic-accounts', d),
    update: (id: string | number, d: any) => api.put(`/analytic-accounts/${id}`, d),
    deactivate: (id: string | number) => api.post(`/analytic-accounts/${id}/deactivate`),
    activate: (id: string | number) => api.post(`/analytic-accounts/${id}/activate`),
    delete: (id: string | number) => api.delete(`/analytic-accounts/${id}`),
    bulkArchive: (ids: (string | number)[]) => api.post('/analytic-accounts/bulk-archive', { ids: ids.map(Number) }),
    bulkDelete: (ids: (string | number)[]) => api.post('/analytic-accounts/bulk-delete', { ids: ids.map(Number) }),
  },
  budgets: {
    list: (includeArchived?: boolean) => api.get('/analytic-budgets', { params: { include_archived: includeArchived } }),
    create: (d: any) => api.post('/analytic-budgets', d),
    update: (id: string | number, d: any) => api.put(`/analytic-budgets/${id}`, d),
    deactivate: (id: string | number) => api.post(`/analytic-budgets/${id}/deactivate`),
    activate: (id: string | number) => api.post(`/analytic-budgets/${id}/activate`),
    delete: (id: string | number) => api.delete(`/analytic-budgets/${id}`),
    bulkArchive: (ids: (string | number)[]) => api.post('/analytic-budgets/bulk-archive', { ids: ids.map(Number) }),
    bulkDelete: (ids: (string | number)[]) => api.post('/analytic-budgets/bulk-delete', { ids: ids.map(Number) }),
  },
};

export const tx = {
  salesOrders: {
    list: () => api.get('/sales/orders'),
    create: (d: any) => api.post('/sales/orders', d),
    confirm: (id: string | number) => api.post(`/sales/orders/${id}/confirm`),
    delete: (id: string | number) => api.delete(`/sales/orders/${id}`),
    bulkDelete: (ids: (string | number)[]) => api.post('/sales/orders/bulk-delete', { ids: ids.map(Number) }),
  },
  purchaseOrders: {
    list: () => api.get('/purchase/orders'),
    create: (d: any) => api.post('/purchase/orders', d),
    confirm: (id: string | number) => api.post(`/purchase/orders/${id}/confirm`),
    delete: (id: string | number) => api.delete(`/purchase/orders/${id}`),
    bulkDelete: (ids: (string | number)[]) => api.post('/purchase/orders/bulk-delete', { ids: ids.map(Number) }),
  },
  invoices: {
    list: () => api.get('/sales/invoices'),
    create: (d: any) => api.post('/sales/invoices', d),
    post: (id: string | number) => api.post(`/sales/invoices/${id}/confirm`),
    delete: (id: string | number) => api.delete(`/sales/invoices/${id}`),
    bulkDelete: (ids: (string | number)[]) => api.post('/sales/invoices/bulk-delete', { ids: ids.map(Number) }),
  },
  bills: {
    list: () => api.get('/purchase/bills'),
    create: (d: any) => api.post('/purchase/bills', d),
    post: (id: string | number) => api.post(`/purchase/bills/${id}/confirm`),
    delete: (id: string | number) => api.delete(`/purchase/bills/${id}`),
    bulkDelete: (ids: (string | number)[]) => api.post('/purchase/bills/bulk-delete', { ids: ids.map(Number) }),
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
    delete: (id: string | number, paymentType?: string) => {
      if (paymentType === 'receipt') {
        return api.delete(`/sales/receipts/${id}`);
      }
      return api.delete(`/purchase/payments/${id}`);
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
