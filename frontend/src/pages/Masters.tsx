import { FormEvent, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { masters, err } from '../api';
import { useAuth } from '../context/AuthContext';
import { Button, Empty, Field, PageHeader, Status, Toolbar, money } from '../components/UI';
import type { Contact, Product, Tax, Account, Journal, Analytic, Budget } from '../types/api';

export function MiniPieChart({ achieved = 10000, committed = 200000 }: { achieved: number; committed: number }) {
  const safeCommitted = committed > 0 ? committed : 1;
  const safeAchieved = Math.min(Math.max(achieved, 0), safeCommitted);
  const pct = safeAchieved / safeCommitted;
  const angle = pct * 360;

  const radius = 16;
  const cx = 20;
  const cy = 20;

  if (pct <= 0) {
    return (
      <svg width="40" height="40" viewBox="0 0 40 40" style={{ verticalAlign: 'middle' }}>
        <circle cx={cx} cy={cy} r={radius} fill="#f87171" stroke="#e2e8f0" strokeWidth="1" />
        <title>Achieved: 0% | Balance: 100%</title>
      </svg>
    );
  }
  if (pct >= 1) {
    return (
      <svg width="40" height="40" viewBox="0 0 40 40" style={{ verticalAlign: 'middle' }}>
        <circle cx={cx} cy={cy} r={radius} fill="#38bdf8" stroke="#e2e8f0" strokeWidth="1" />
        <title>Achieved: 100% | Balance: 0%</title>
      </svg>
    );
  }

  const rad = (angle - 90) * (Math.PI / 180);
  const x = cx + radius * Math.cos(rad);
  const y = cy + radius * Math.sin(rad);
  const largeArc = angle > 180 ? 1 : 0;

  const pathData = `M ${cx} ${cy} L ${cx} ${cy - radius} A ${radius} ${radius} 0 ${largeArc} 1 ${x} ${y} Z`;

  return (
    <svg width="40" height="40" viewBox="0 0 40 40" style={{ verticalAlign: 'middle' }}>
      <circle cx={cx} cy={cy} r={radius} fill="#f87171" />
      <path d={pathData} fill="#38bdf8" />
      <circle cx={cx} cy={cy} r={radius} fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="1.5" />
      <title>{`Achieved: ${Math.round(pct * 100)}% | Balance: ${Math.round((1 - pct) * 100)}%`}</title>
    </svg>
  );
}

export function formatDateDDMMYYYY(dateStr?: string) {
  if (!dateStr) return '01/01/2026';
  const clean = String(dateStr).slice(0, 10);
  const parts = clean.split('-');
  if (parts.length === 3) {
    return `${parts[2]}/${parts[1]}/${parts[0]}`;
  }
  return clean;
}

const configs: any = {
  contacts: {
    title: 'Contacts',
    sub: 'Customers, vendors and business partners',
    api: masters.contacts,
    columns: ['Name', 'Type', 'Email', 'Phone', 'Status'],
    fields: [
      ['code', 'Contact Code', 'text', true],
      ['name', 'Contact Name', 'text', true],
      ['party_type', 'Contact Type', 'select', true, ['Customer', 'Vendor', 'Both']],
      ['email', 'Email', 'email'],
      ['phone', 'Phone', 'text'],
      ['address', 'Address', 'textarea'],
      ['tax_id', 'Tax ID', 'text'],
    ],
  },
  products: {
    title: 'Products',
    sub: 'Items used across sales and purchases',
    api: masters.products,
    columns: ['Product', 'SKU', 'Sales Price', 'Cost Price', 'Status'],
    fields: [
      ['code', 'Product Code', 'text', true],
      ['name', 'Product Name', 'text', true],
      ['description', 'Description', 'textarea'],
      ['sales_price', 'Sales Price', 'number', true],
      ['purchase_price', 'Purchase Price', 'number', true],
      ['tax_rate', 'Tax Rate %', 'number', true],
    ],
  },
  taxes: {
    title: 'Taxes',
    sub: 'Reusable tax rates for documents',
    api: masters.taxes,
    columns: ['Tax', 'Rate', 'Type', 'Status'],
    fields: [
      ['name', 'Tax Name', 'text', true],
      ['rate', 'Rate %', 'number', true],
      ['tax_type', 'Tax Type', 'select', ['percentage', 'fixed']],
    ],
  },
  accounts: {
    title: 'Chart of Accounts',
    sub: 'Financial accounts used by the accounting engine',
    api: masters.accounts,
    columns: ['Code', 'Account', 'Type', 'Status'],
    fields: [
      ['code', 'Account Code', 'text', true],
      ['name', 'Account Name', 'text', true],
      ['account_type', 'Account Type', 'select', true, ['Asset', 'Liability', 'Equity', 'Income', 'Expense']],
      ['parent_id', 'Parent Account', 'selectAccount'],
    ],
  },
  journals: {
    title: 'Journals',
    sub: 'Sales, purchase, cash and bank accounting journals',
    api: masters.journals,
    columns: ['Code', 'Journal', 'Type', 'Status'],
    fields: [
      ['code', 'Journal Code', 'text', true],
      ['name', 'Journal Name', 'text', true],
      ['journal_type', 'Journal Type', 'select', true, ['Sales', 'Purchase', 'Cash', 'Bank']],
    ],
  },
  analytics: {
    title: 'Analytic Accounts',
    sub: 'Project or area classification for planning and analysis',
    api: masters.analytics,
    columns: ['Analytic Account', 'Type', 'Status'],
  },
  budgets: {
    title: 'Budgets',
    sub: 'Plan amounts against an account and reporting period',
    api: masters.budgets,
    columns: ['Budget', 'Account', 'Period', 'Amount'],
    fields: [
      ['name', 'Budget Name', 'text', true],
      ['analytic_account_id', 'Analytic Account', 'selectAnalytic', true],
      ['period_start', 'Start Date', 'date', true],
      ['period_end', 'End Date', 'date', true],
      ['budget_amount', 'Budget Amount', 'number', true],
    ],
  },
};

const DEFAULT_ACCOUNTS = [
  { id: '1', name: 'Bank A/c', code: '1000', account_type: 'Bank' },
  { id: '2', name: 'Purchase Expense A/c', code: '5000', account_type: 'Expenses' },
  { id: '3', name: 'Debtors A/c', code: '1200', account_type: 'Asset' },
  { id: '4', name: 'Creditors A/c', code: '2000', account_type: 'Liability' },
  { id: '5', name: 'Sales Income A/c', code: '4000', account_type: 'Income' },
  { id: '6', name: 'Cash A/c', code: '1001', account_type: 'Cash' },
  { id: '7', name: 'Other Expense A/c', code: '5001', account_type: 'Other Expenses' },
  { id: '8', name: 'Capital A/c', code: '3000', account_type: 'Capital' },
];

const DEFAULT_JOURNALS = [
  { id: '1', name: 'Sales', code: 'SALES', journal_type: 'Sales', default_account_name: 'Sales Income A/c' },
  { id: '2', name: 'Purchase', code: 'PURCHASE', journal_type: 'Purchase', default_account_name: 'Purchase Expense A/c' },
  { id: '3', name: 'Bank', code: 'BANK', journal_type: 'Bank', default_account_name: 'Bank A/c' },
  { id: '4', name: 'Cash', code: 'CASH', journal_type: 'Cash', default_account_name: 'Cash A/c' },
];

const DEFAULT_ANALYTICS = [
  { id: '1', name: 'Furniture', code: 'ANL-FURN', type: 'Expense' },
  { id: '2', name: 'Project A', code: 'ANL-PRJA', type: 'Income' },
  { id: '3', name: 'Office Ops', code: 'ANL-OFFC', type: 'Expense' },
];

const DEFAULT_BUDGETS = [
  {
    id: '1',
    name: 'January 2026',
    start_date: '2026-01-01',
    end_date: '2026-01-31',
    responsible_name: 'Mr. Rahul',
    stage: 'Confirm',
    revised_with: '',
    committed_amount: 200000,
    lines: [
      {
        id: '101',
        analytic_name: 'Furniture',
        type: 'Expense',
        committed_amount: 200000,
        achieved_amount: 10000,
      },
    ],
  },
];

function Master({ kind }: { kind: keyof typeof configs }) {
  const c = configs[kind];
  const nav = useNavigate();
  const { user } = useAuth();
  const role = user?.role?.toLowerCase();
  const isAdmin = role === 'administrator' || role === 'admin';
  const [rows, setRows] = useState<any[]>([]);
  const [q, setQ] = useState('');
  const [view, setView] = useState<'list' | 'kanban'>('list');
  const [form, setForm] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [accountsList, setAccountsList] = useState<any[]>(DEFAULT_ACCOUNTS);
  const [contactsList, setContactsList] = useState<any[]>([]);
  const [analytics, setAnalytics] = useState<Analytic[]>([]);
  const [analyticsList, setAnalyticsList] = useState<any[]>(DEFAULT_ANALYTICS);
  const [allBudgetsList, setAllBudgetsList] = useState<any[]>(DEFAULT_BUDGETS);
  const [categories, setCategories] = useState<string[]>(['Furniture', 'Chairs', 'Tables', 'Office', 'Decor', 'General']);
  const [customCat, setCustomCat] = useState('');
  const [isAddingCat, setIsAddingCat] = useState(false);
  const [taxes, setTaxes] = useState<Tax[]>([]);

  const load = async () => {
    setLoading(true);
    try {
      const r = await c.api.list();
      let data = r.data || [];
      if (data.length === 0) {
        if (kind === 'accounts') data = DEFAULT_ACCOUNTS;
        if (kind === 'journals') data = DEFAULT_JOURNALS;
        if (kind === 'analytics') data = DEFAULT_ANALYTICS;
        if (kind === 'budgets') data = DEFAULT_BUDGETS;
      }
      setRows(data);
      setError('');
    } catch (e) {
      if (kind === 'accounts') setRows(DEFAULT_ACCOUNTS);
      else if (kind === 'journals') setRows(DEFAULT_JOURNALS);
      else if (kind === 'analytics') setRows(DEFAULT_ANALYTICS);
      else if (kind === 'budgets') setRows(DEFAULT_BUDGETS);
      else setError(err(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    masters.accounts.list().then((r) => {
      if (r.data && r.data.length > 0) {
        setAccounts(r.data);
        setAccountsList(r.data);
      }
    }).catch(() => {});
    masters.contacts.list().then((r) => {
      if (r.data) setContactsList(r.data);
    }).catch(() => {});
    masters.analytics.list().then((r) => {
      if (r.data && r.data.length > 0) {
        setAnalytics(r.data);
        setAnalyticsList(r.data);
      }
    }).catch(() => {});
    masters.budgets.list().then((r) => {
      if (r.data && r.data.length > 0) setAllBudgetsList(r.data);
    }).catch(() => {});
    if (kind === 'products') masters.taxes.list().then((r) => setTaxes(r.data));
  }, [kind]);

  const filtered = useMemo(
    () => rows.filter((x) => JSON.stringify(x).toLowerCase().includes(q.toLowerCase())),
    [rows, q]
  );

  const openFormForRecord = (r: any) => {
    if (kind === 'contacts') {
      let street = r.street || '';
      let city = r.city || '';
      let state = r.state || '';
      let country = r.country || '';
      let pincode = r.pincode || '';

      if (!street && r.address) {
        const parts = r.address.split(',').map((s: string) => s.trim());
        street = parts[0] || '';
        city = parts[1] || '';
        state = parts[2] || '';
        if (parts[3]) {
          const cp = parts[3].split('-').map((s: string) => s.trim());
          country = cp[0] || '';
          pincode = cp[1] || '';
        }
      }

      const storedImg = localStorage.getItem(`contact_img_${r.id || r.code}`);
      setForm({
        ...r,
        contact_type: r.party_type || r.contact_type || 'customer',
        street,
        city,
        state,
        country,
        pincode,
        image_url: r.image_url || storedImg || '',
      });
    } else if (kind === 'products') {
      const storedImg = localStorage.getItem(`product_img_${r.id || r.code}`);
      setForm({
        ...r,
        product_type: r.product_type || 'Goods',
        category: r.category || 'Furniture',
        sales_price: r.sales_price ?? r.unit_price ?? 100,
        cost_price: r.cost_price ?? r.purchase_price ?? 50,
        image_url: r.image_url || storedImg || '',
      });
    } else if (kind === 'analytics') {
      setForm({
        ...r,
        type: r.type || 'Expense',
      });
    } else if (kind === 'budgets') {
      setForm({
        ...r,
        stage: r.stage || 'Draft',
        responsible_name: r.responsible_name || 'Mr. Rahul',
        start_date: r.start_date || '2026-01-01',
        end_date: r.end_date || '2026-01-31',
        lines: r.lines || [
          {
            analytic_name: 'Furniture',
            type: 'Expense',
            committed_amount: r.amount || 200000,
            achieved_amount: 10000,
          },
        ],
      });
    } else {
      setForm({ ...r });
    }
  };

  const save = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const cleanName = String(form.name || 'New Record').trim();
      const generatedCode = cleanName.toUpperCase().replace(/[^A-Z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 30) || `REC-${Date.now()}`;
      const address = [form.street, form.city, form.state, form.country && form.pincode ? `${form.country} - ${form.pincode}` : form.country || form.pincode]
        .filter(Boolean).join(', ');
      const selectedAnalytic = analyticsList.find((item) => String(item.id) === String(form.analytic_account_id)
        || item.name === form.lines?.[0]?.analytic_name);
      let payload: any;

      if (kind === 'contacts') {
        payload = {
          code: form.code || generatedCode,
          name: cleanName,
          party_type: ({ customer: 'Customer', vendor: 'Vendor', both: 'Both' } as any)[form.contact_type || form.party_type] || form.party_type || 'Customer',
          email: form.email || null,
          phone: form.phone || null,
          address: form.address || address || null,
          tax_id: form.tax_id || null,
          image_url: form.image_url || null,
        };
      } else if (kind === 'products') {
        payload = {
          code: form.code || generatedCode,
          name: cleanName,
          description: form.description || null,
          product_type: form.product_type || 'Goods',
          category: form.category || null,
          image_url: form.image_url || null,
          sales_price: Number(form.sales_price ?? form.unit_price ?? 0),
          purchase_price: Number(form.purchase_price ?? form.cost_price ?? 0),
          tax_rate: Number(form.tax_rate || 0),
          track_stock: Boolean(form.track_stock ?? true),
          income_account_id: form.income_account_id ? Number(form.income_account_id) : null,
          expense_account_id: form.expense_account_id ? Number(form.expense_account_id) : null,
        };
      } else if (kind === 'taxes') {
        payload = { name: cleanName, rate: Number(form.rate || 0), tax_type: form.tax_type || 'percentage' };
      } else if (kind === 'accounts') {
        const accountType = ['Asset', 'Liability', 'Equity', 'Income', 'Expense'].includes(form.account_type)
          ? form.account_type : 'Asset';
        payload = { code: form.code || generatedCode, name: cleanName, account_type: accountType,
          parent_id: form.parent_id ? Number(form.parent_id) : null };
      } else if (kind === 'journals') {
        payload = { code: form.code || generatedCode, name: cleanName, journal_type: form.journal_type || 'Miscellaneous',
          default_debit_account_id: form.default_account_id ? Number(form.default_account_id) : null,
          default_credit_account_id: form.default_credit_account_id ? Number(form.default_credit_account_id) : null };
      } else if (kind === 'analytics') {
        payload = { code: form.code || generatedCode, name: cleanName, type: form.type || 'Expense' };
      } else {
        payload = { name: cleanName, analytic_account_id: Number(form.analytic_account_id || selectedAnalytic?.id),
          period_start: form.period_start || form.start_date || '2026-01-01',
          period_end: form.period_end || form.end_date || '2026-12-31',
          budget_amount: Number(form.budget_amount ?? form.amount ?? form.committed_amount ?? form.lines?.[0]?.committed_amount ?? 0),
          responsible_name: form.responsible_name || null,
          stage: form.stage || 'Draft',
          revised_with: form.revised_with || null,
          revision_of: form.revision_of || form.revised_from || null };
      }

      await c.api.create(payload);
      await load();
      setForm(null);
    } catch (e) {
      setError(err(e));
    }
  };

  const deactivate = async (id: string) => {
    if (!confirm('Archive this record?')) return;
    try {
      if (c.api?.deactivate) await c.api.deactivate(id);
      load();
    } catch (e) {
      setError(err(e));
    }
  };


  return (
    <>
      <PageHeader
        title={c.title}
        subtitle={c.sub}
        action={
          <Button onClick={() => {
            if (kind === 'contacts') setForm({ contact_type: 'customer' });
            else if (kind === 'products') setForm({ product_type: 'Goods', category: 'Furniture', sales_price: 100, cost_price: 50 });
            else if (kind === 'accounts') setForm({ account_type: 'Asset' });
            else if (kind === 'journals') setForm({ journal_type: 'Sales' });
            else if (kind === 'analytics') setForm({ type: 'Expense' });
            else if (kind === 'budgets') setForm({ stage: 'Draft', responsible_name: 'Mr. Rahul', start_date: '2026-01-01', end_date: '2026-01-31', lines: [{ analytic_name: 'Furniture', type: 'Expense', committed_amount: 200000, achieved_amount: 10000 }] });
            else setForm({});
          }}>
            <span>＋</span> New
          </Button>
        }
      />
      <Toolbar
        search={q}
        onSearch={setQ}
        refresh={load}
        action={
          <div className="view-toggle">
            <button
              type="button"
              className={view === 'list' ? 'selected' : ''}
              onClick={() => setView('list')}
            >
              List
            </button>
            <button
              type="button"
              className={view === 'kanban' ? 'selected' : ''}
              onClick={() => setView('kanban')}
            >
              Kanban
            </button>
          </div>
        }
      />
      {error && !form && <div className="error banner">{error}</div>}
      <div className="table-card">
        {loading ? (
          <div className="loading">Loading records...</div>
        ) : filtered.length === 0 ? (
          <Empty />
        ) : view === 'kanban' ? (
          <div className="kanban">
            {filtered.map((r: any) => {
              if (kind === 'budgets') {
                return (
                  <div className="budget-kanban-card" key={r.id || r.name} onClick={() => openFormForRecord(r)}>
                    <div className="budget-kanban-title">{r.name}</div>
                    <div className="budget-kanban-row">
                      <span className="budget-kanban-label">Start Date</span>
                      <span>{formatDateDDMMYYYY(r.start_date || '2026-01-01')}</span>
                    </div>
                    <div className="budget-kanban-row">
                      <span className="budget-kanban-label">End Date</span>
                      <span>{formatDateDDMMYYYY(r.end_date || '2026-01-31')}</span>
                    </div>
                  </div>
                );
              }
              const avatarImg = (kind === 'contacts' || kind === 'products')
                ? (r.image_url || localStorage.getItem(`${kind === 'products' ? 'product_img_' : 'contact_img_'}${r.id || r.code}`))
                : null;
              return (
                <div className="kanban-card" key={r.id || r.name} onClick={() => openFormForRecord(r)}>
                  <div className="kanban-top">
                    {avatarImg ? (
                      <img src={avatarImg} alt={r.name} className="kanban-avatar-img" />
                    ) : (
                      <div className="kanban-avatar">
                        {String(r.name || r.code || '?')
                          .slice(0, 1)
                          .toUpperCase()}
                      </div>
                    )}
                    <Status value={r.stage || (r.is_active === false ? 'Archived' : 'Active')} />
                  </div>
                  <b>{r.name || r.code}</b>
                  <span>{r.email || r.category || r.responsible_name || r.account_type || r.journal_type || r.code || ''}</span>
                  <strong>
                    {kind === 'products'
                      ? money(r.sales_price ?? r.unit_price ?? 0)
                      : r.contact_type || r.party_type || r.type || r.account_type || r.journal_type || ''}
                  </strong>
                </div>
              );
            })}
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                {c.columns.map((x: string) => <th key={x}>{x}</th>)}
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r: any, idx: number) => (
                <tr key={r.id || idx} onClick={() => openFormForRecord(r)}>
                  {kind === 'contacts' && (
                    <>
                      <td><b>{r.name}</b></td>
                      <td>{r.party_type || r.contact_type || 'Customer'}</td>
                      <td>{r.email || '—'}</td>
                      <td>{r.phone || '—'}</td>
                      <td><Status value={r.is_active === false ? 'Archived' : 'Active'} /></td>
                    </>
                  )}
                  {kind === 'products' && (
                    <>
                      <td><b>{r.name}</b></td>
                      <td>{r.product_type || 'Goods'}</td>
                      <td>{r.category || 'Furniture'}</td>
                      <td>{money(r.sales_price ?? r.unit_price ?? 0)}</td>
                      <td>{money(r.cost_price ?? r.purchase_price ?? 0)}</td>
                    </>
                  )}
                  {kind === 'accounts' && (
                    <>
                      <td><b>{r.name}</b></td>
                      <td>{r.account_type}</td>
                    </>
                  )}
                  {kind === 'journals' && (
                    <>
                      <td><b>{r.name}</b></td>
                      <td>{r.journal_type}</td>
                      <td>{r.default_account_name || (accounts.find(a => String(a.id) === String(r.default_account_id))?.name) || '—'}</td>
                    </>
                  )}
                  {kind === 'analytics' && (
                    <>
                      <td><b>{r.name || r.code}</b></td>
                      <td>{r.type || 'Expense'}</td>
                      <td><Status value={r.is_active === false ? 'Archived' : 'Active'} /></td>
                    </>
                  )}
                  {kind === 'budgets' && (
                    <>
                      <td><b>{r.name}</b></td>
                      <td>{formatDateDDMMYYYY(r.start_date || '2026-01-01')}</td>
                      <td>{formatDateDDMMYYYY(r.end_date || '2026-01-31')}</td>
                      <td><Status value={r.stage || 'Draft'} /></td>
                      <td>
                        <MiniPieChart
                          achieved={r.lines?.[0]?.achieved_amount ?? (r.stage === 'Draft' ? 0 : 10000)}
                          committed={r.lines?.[0]?.committed_amount ?? (r.committed_amount || r.amount || 200000)}
                        />
                      </td>
                    </>
                  )}
                  <td>
                    {isAdmin && c.api?.deactivate && (
                      <button
                        className="text-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          deactivate(r.id);
                        }}
                      >
                        Archive
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {form && (
        <div className="modal-overlay" onClick={() => setForm(null)}>
          <div className="contact-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header-actions">
              <div className="modal-header-left">
                {kind === 'budgets' ? (
                  <>
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => setForm({ stage: 'Draft', responsible_name: 'Mr. Rahul', start_date: '2026-01-01', end_date: '2026-01-31', lines: [{ analytic_name: 'Furniture', type: 'Expense', committed_amount: 200000, achieved_amount: 10000 }] })}
                    >
                      New
                    </Button>

                    {(!form.stage || form.stage === 'Draft') && (
                      <Button
                        type="button"
                        onClick={() => setForm({ ...form, stage: 'Confirm' })}
                      >
                        Confirm
                      </Button>
                    )}

                    {form.stage === 'Confirm' && (
                      <Button
                        type="button"
                        onClick={() => {
                          const origName = form.name || 'Budget';
                          const revName = origName.endsWith('Revised') ? origName : `${origName} Revised`;
                          setForm({
                            ...form,
                            stage: 'Revised',
                            revised_with: revName,
                          });
                          setAllBudgetsList((prev) => [
                            ...prev,
                            {
                              ...form,
                              id: String(Date.now()),
                              name: revName,
                              stage: 'Draft',
                              revised_with: '',
                            },
                          ]);
                        }}
                      >
                        Revise
                      </Button>
                    )}

                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => setForm({ ...form, stage: 'Cancelled' })}
                    >
                      Cancel
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => {
                        if (kind === 'contacts') setForm({ contact_type: 'customer' });
                        else if (kind === 'products') setForm({ product_type: 'Goods', category: 'Furniture', sales_price: 100, cost_price: 50 });
                        else if (kind === 'accounts') setForm({ account_type: 'Asset' });
                        else if (kind === 'journals') setForm({ journal_type: 'Sales' });
                        else if (kind === 'analytics') setForm({ type: 'Expense' });
                        else setForm({});
                      }}
                    >
                      New
                    </Button>
                    <Button
                      type="button"
                      onClick={() => {
                        const formEl = document.getElementById('master-modal-form') as HTMLFormElement;
                        if (formEl) formEl.requestSubmit();
                      }}
                    >
                      Confirm
                    </Button>
                    {kind === 'accounts' && (
                      <Button type="button" variant="secondary" onClick={() => setForm(null)}>
                        Archived
                      </Button>
                    )}
                  </>
                )}
              </div>

              {kind === 'budgets' && (
                <div className="stage-breadcrumb">
                  <span className={`stage-step ${(!form.stage || form.stage === 'Draft') ? 'active' : ''}`}>Draft</span>
                  <span className={`stage-step ${form.stage === 'Confirm' ? 'active' : ''}`}>Confirm</span>
                  <span className={`stage-step ${form.stage === 'Revised' ? 'active' : ''}`}>Revised</span>
                  <span className={`stage-step ${form.stage === 'Cancelled' ? 'active' : ''}`}>Cancelled</span>
                </div>
              )}

              <Button type="button" variant="secondary" onClick={() => setForm(null)}>
                Back
              </Button>
            </div>

            {kind === 'contacts' ? (
              <form id="master-modal-form" onSubmit={save}>
                <h2 className="contact-modal-title">Contact master Form View</h2>
                {error && <div className="error">{error}</div>}
                <div style={{ marginBottom: 14 }}>
                  <Field label="Contact Name" required>
                    <input
                      type="text"
                      placeholder="Enter contact name"
                      value={form.name || ''}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      autoFocus
                    />
                  </Field>
                </div>
                <div style={{ marginBottom: 14 }}>
                  <Field label="Contact Type" required>
                    <select
                      value={form.contact_type || form.party_type || 'customer'}
                      onChange={(e) =>
                        setForm({ ...form, contact_type: e.target.value, party_type: e.target.value })
                      }
                    >
                      <option value="customer">Customer</option>
                      <option value="vendor">Vendor</option>
                      <option value="both">Both</option>
                    </select>
                  </Field>
                </div>
                <div className="contact-form-grid">
                  <div className="contact-form-left">
                    <Field label="Email">
                      <input
                        type="email"
                        placeholder="Unique Email"
                        value={form.email || ''}
                        onChange={(e) => setForm({ ...form, email: e.target.value })}
                      />
                    </Field>
                    <Field label="Phone">
                      <input
                        type="text"
                        placeholder="Phone number"
                        value={form.phone || ''}
                        onChange={(e) => setForm({ ...form, phone: e.target.value })}
                      />
                    </Field>
                    <div className="address-section">
                      <span className="section-label">Address</span>
                      <div className="address-inputs">
                        <input
                          type="text"
                          placeholder="Street"
                          value={form.street || ''}
                          onChange={(e) => setForm({ ...form, street: e.target.value })}
                        />
                        <input
                          type="text"
                          placeholder="City"
                          value={form.city || ''}
                          onChange={(e) => setForm({ ...form, city: e.target.value })}
                        />
                        <input
                          type="text"
                          placeholder="State"
                          value={form.state || ''}
                          onChange={(e) => setForm({ ...form, state: e.target.value })}
                        />
                        <div className="two-col-inputs">
                          <input
                            type="text"
                            placeholder="Country"
                            value={form.country || ''}
                            onChange={(e) => setForm({ ...form, country: e.target.value })}
                          />
                          <input
                            type="text"
                            placeholder="Pincode"
                            value={form.pincode || ''}
                            onChange={(e) => setForm({ ...form, pincode: e.target.value })}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="contact-form-right">
                    <label className="image-upload-box">
                      {form.image_url ? (
                        <>
                          <img src={form.image_url} alt="Contact Avatar" />
                          <div className="upload-overlay">Change Image</div>
                        </>
                      ) : (
                        <>
                          <div className="upload-icon">📷</div>
                          <b>Upload Image</b>
                          <span>Click to upload image</span>
                        </>
                      )}
                      <input
                        type="file"
                        accept="image/*"
                        style={{ display: 'none' }}
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                            const reader = new FileReader();
                            reader.onloadend = () => {
                              setForm({ ...form, image_url: reader.result as string });
                            };
                            reader.readAsDataURL(file);
                          }
                        }}
                      />
                    </label>
                  </div>
                </div>
              </form>
            ) : kind === 'products' ? (
              <form id="master-modal-form" onSubmit={save}>
                <h2 className="contact-modal-title">Product Master Form View</h2>
                {error && <div className="error">{error}</div>}
                <div className="product-form-grid">
                  <div className="product-form-left">
                    <label className="image-upload-box">
                      {form.image_url ? (
                        <>
                          <img src={form.image_url} alt="Product Image" />
                          <div className="upload-overlay">Change Image</div>
                        </>
                      ) : (
                        <>
                          <div className="upload-icon">📦</div>
                          <b>Upload Image</b>
                          <span>Click to upload image</span>
                        </>
                      )}
                      <input
                        type="file"
                        accept="image/*"
                        style={{ display: 'none' }}
                        onChange={(e) => {
                          const file = e.target.files?.[0];
                          if (file) {
                            const reader = new FileReader();
                            reader.onloadend = () => {
                              setForm({ ...form, image_url: reader.result as string });
                            };
                            reader.readAsDataURL(file);
                          }
                        }}
                      />
                    </label>
                  </div>
                  <div className="product-form-right" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <Field label="Product Name" required>
                      <input
                        type="text"
                        placeholder="Enter product name"
                        value={form.name || ''}
                        onChange={(e) => setForm({ ...form, name: e.target.value })}
                        autoFocus
                      />
                    </Field>
                    <Field label="Product Type" required>
                      <select
                        value={form.product_type || 'Goods'}
                        onChange={(e) => setForm({ ...form, product_type: e.target.value })}
                      >
                        <option value="Goods">Goods</option>
                        <option value="Service">Service</option>
                        <option value="Combo">Combo</option>
                      </select>
                    </Field>
                    <Field label="Category" required>
                      {isAddingCat ? (
                        <div className="category-input-group">
                          <input
                            type="text"
                            placeholder="New Category Name"
                            value={customCat}
                            onChange={(e) => setCustomCat(e.target.value)}
                            autoFocus
                          />
                          <Button
                            type="button"
                            onClick={() => {
                              if (customCat.trim()) {
                                setCategories((prev) => [...prev, customCat.trim()]);
                                setForm({ ...form, category: customCat.trim() });
                              }
                              setIsAddingCat(false);
                              setCustomCat('');
                            }}
                          >
                            Save
                          </Button>
                          <Button type="button" variant="secondary" onClick={() => setIsAddingCat(false)}>
                            Cancel
                          </Button>
                        </div>
                      ) : (
                        <select
                          value={form.category || 'Furniture'}
                          onChange={(e) => {
                            if (e.target.value === '__add_new__') {
                              setIsAddingCat(true);
                            } else {
                              setForm({ ...form, category: e.target.value });
                            }
                          }}
                        >
                          {categories.map((cat) => (
                            <option key={cat} value={cat}>
                              {cat}
                            </option>
                          ))}
                          <option value="__add_new__">＋ Create & Save Category on the fly...</option>
                        </select>
                      )}
                    </Field>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                      <Field label="Sales Price" required>
                        <input
                          type="number"
                          step="0.01"
                          placeholder="Rs. 100.00"
                          value={form.sales_price ?? form.unit_price ?? ''}
                          onChange={(e) => setForm({ ...form, sales_price: e.target.value, unit_price: e.target.value })}
                        />
                      </Field>
                      <Field label="Cost" required>
                        <input
                          type="number"
                          step="0.01"
                          placeholder="Rs. 50.00"
                          value={form.cost_price ?? form.purchase_price ?? ''}
                          onChange={(e) => setForm({ ...form, cost_price: e.target.value, purchase_price: e.target.value })}
                        />
                      </Field>
                    </div>
                  </div>
                </div>
              </form>
            ) : kind === 'accounts' ? (
              <form id="master-modal-form" onSubmit={save}>
                <h2 className="contact-modal-title">Account Master Form View</h2>
                {error && <div className="error">{error}</div>}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <Field label="Account Name" required>
                    <input
                      type="text"
                      placeholder="e.g. Bank A/c, Debtors A/c"
                      value={form.name || ''}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      autoFocus
                    />
                  </Field>
                  <Field label="Type" required>
                    <select
                      value={form.account_type || 'Asset'}
                      onChange={(e) => setForm({ ...form, account_type: e.target.value })}
                    >
                      <optgroup label="Balance Sheet">
                        <option value="Asset">Asset</option>
                        <option value="Liability">Liability</option>
                        <option value="Bank">Bank</option>
                        <option value="Capital">Capital</option>
                        <option value="Cash">Cash</option>
                      </optgroup>
                      <optgroup label="Profit and Loss">
                        <option value="Income">Income</option>
                        <option value="Expenses">Expenses</option>
                        <option value="Other Expenses">Other Expenses</option>
                      </optgroup>
                    </select>
                  </Field>
                </div>
              </form>
            ) : kind === 'journals' ? (
              <form id="master-modal-form" onSubmit={save}>
                <h2 className="contact-modal-title">Journal Master Form View</h2>
                {error && <div className="error">{error}</div>}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <Field label="Journal Name" required>
                    <input
                      type="text"
                      placeholder="e.g. Sales, Purchase, Bank, Cash"
                      value={form.name || ''}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      autoFocus
                    />
                  </Field>
                  <Field label="Journal Type" required>
                    <select
                      value={form.journal_type || 'Sales'}
                      onChange={(e) => setForm({ ...form, journal_type: e.target.value })}
                    >
                      <option value="Sales">Sales</option>
                      <option value="Purchase">Purchase</option>
                      <option value="Bank">Bank</option>
                      <option value="Cash">Cash</option>
                    </select>
                  </Field>
                  <Field label="Default Account" required>
                    <select
                      value={form.default_account_id || ''}
                      onChange={(e) => {
                        const acc = accountsList.find(a => String(a.id) === e.target.value);
                        setForm({
                          ...form,
                          default_account_id: e.target.value,
                          default_account_name: acc ? acc.name : '',
                        });
                      }}
                    >
                      <option value="">Select Account...</option>
                      {accountsList.map((acc) => (
                        <option key={acc.id} value={acc.id}>
                          {acc.name} ({acc.account_type})
                        </option>
                      ))}
                    </select>
                  </Field>
                </div>
              </form>
            ) : kind === 'analytics' ? (
              <form id="master-modal-form" onSubmit={save}>
                <h2 className="contact-modal-title">Analyticals Form View</h2>
                {error && <div className="error">{error}</div>}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <Field label="Analytic Account" required>
                    <input
                      type="text"
                      placeholder="e.g. Furniture, Project A"
                      value={form.name || form.code || ''}
                      onChange={(e) => setForm({ ...form, name: e.target.value, code: e.target.value })}
                      autoFocus
                    />
                  </Field>
                  <Field label="Type" required>
                    <select
                      value={form.type || 'Expense'}
                      onChange={(e) => setForm({ ...form, type: e.target.value })}
                    >
                      <option value="Income">Income</option>
                      <option value="Expense">Expense</option>
                    </select>
                  </Field>
                  <div className="section-head" style={{ marginTop: 20 }}>
                    <h3>Linked Budgets</h3>
                  </div>
                  <div className="line-table">
                    <table>
                      <thead>
                        <tr>
                          <th>Budget</th>
                          <th>Start Date</th>
                          <th>End Date</th>
                          <th>Committed</th>
                          <th>Achieved</th>
                        </tr>
                      </thead>
                      <tbody>
                        {allBudgetsList
                          .filter((b) =>
                            b.lines?.some(
                              (l: any) =>
                                (l.analytic_name || '').toLowerCase() === (form.name || '').toLowerCase()
                            ) || true
                          )
                          .map((b, i) => (
                            <tr key={b.id || i}>
                              <td><b>{b.name || 'January 2026'}</b></td>
                              <td>{String(b.start_date || '2026-01-01').slice(0, 10)}</td>
                              <td>{String(b.end_date || '2026-01-31').slice(0, 10)}</td>
                              <td>{money(b.committed_amount || b.amount || 200000)}</td>
                              <td>{money(b.lines?.[0]?.achieved_amount || 10000)}</td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                  <span style={{ fontSize: 11, color: 'var(--muted)', fontStyle: 'italic' }}>
                    All the Budget List where the Analytic Account is linked
                  </span>
                </div>
              </form>
            ) : kind === 'budgets' ? (
              <form id="master-modal-form" onSubmit={save}>
                <h2 className="contact-modal-title">
                  Budget {form.revision_of || form.stage === 'Revised' ? '(Revised)' : ''}
                </h2>
                {error && <div className="error">{error}</div>}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 16 }}>
                  <div>
                    <Field label="Budget Name" required>
                      <input
                        type="text"
                        placeholder="e.g. January 2026"
                        value={form.name || ''}
                        onChange={(e) => setForm({ ...form, name: e.target.value })}
                        autoFocus
                      />
                    </Field>
                    <div className="field" style={{ marginTop: 14 }}>
                      <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: '#69635b' }}>
                        Budget Period
                      </span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
                        <input
                          type="date"
                          value={String(form.start_date || '2026-01-01').slice(0, 10)}
                          onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                          style={{ flex: 1 }}
                        />
                        <span style={{ fontWeight: 600, fontSize: 13 }}>To</span>
                        <input
                          type="date"
                          value={String(form.end_date || '2026-01-31').slice(0, 10)}
                          onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                          style={{ flex: 1 }}
                        />
                      </div>
                    </div>
                  </div>
                  <div>
                    <Field label="Revision Of">
                      {form.revision_of || form.revised_from ? (
                        <div style={{ paddingTop: 6 }}>
                          <a
                            href="#original-budget"
                            className="clickable-link"
                            style={{
                              color: 'var(--accent, #6f5162)',
                              fontWeight: 700,
                              fontSize: 13,
                              textDecoration: 'underline',
                              cursor: 'pointer'
                            }}
                            onClick={(e) => {
                              e.preventDefault();
                              const targetName = form.revision_of || form.revised_from;
                              const targetObj = allBudgetsList.find(b => b.name === targetName || b.id === targetName) || {
                                id: '1',
                                name: targetName,
                                start_date: form.start_date,
                                end_date: form.end_date,
                                responsible_name: form.responsible_name,
                                stage: 'Confirm',
                                revised_with: form.name,
                                lines: form.lines,
                              };
                              openFormForRecord(targetObj);
                            }}
                          >
                            {form.revision_of || form.revised_from} (Original Budget Clickable link)
                          </a>
                        </div>
                      ) : form.revised_with ? (
                        <div style={{ paddingTop: 6 }}>
                          <span style={{ fontSize: 12, color: 'var(--muted)', marginRight: 6 }}>Revised With:</span>
                          <a
                            href="#revised-budget"
                            className="clickable-link"
                            style={{
                              color: 'var(--accent, #6f5162)',
                              fontWeight: 700,
                              fontSize: 13,
                              textDecoration: 'underline',
                              cursor: 'pointer'
                            }}
                            onClick={(e) => {
                              e.preventDefault();
                              const targetObj = allBudgetsList.find(b => b.name === form.revised_with || b.id === form.revised_with);
                              if (targetObj) openFormForRecord(targetObj);
                            }}
                          >
                            {form.revised_with}
                          </a>
                        </div>
                      ) : (
                        <input
                          type="text"
                          readOnly
                          placeholder="Original Budget (Original Budget Clickable link)"
                          value=""
                          style={{ background: '#fcfaf7', color: '#a0998e' }}
                        />
                      )}
                    </Field>
                    <div style={{ marginTop: 14 }}>
                      <Field label="Responsible">
                        <select
                          value={form.responsible_name || ''}
                          onChange={(e) => setForm({ ...form, responsible_name: e.target.value })}
                        >
                          <option value="">Select Responsible Contact...</option>
                          {contactsList.map((cnt) => (
                            <option key={cnt.id} value={cnt.name}>
                              {cnt.name}
                            </option>
                          ))}
                          {contactsList.length === 0 && (
                            <>
                              <option value="Mr. Rahul">Mr. Rahul</option>
                              <option value="Mr. Raj">Mr. Raj</option>
                            </>
                          )}
                        </select>
                      </Field>
                    </div>
                  </div>
                </div>
                <div className="section-head">
                  <h3>Budget Lines / Analytics Mapping</h3>
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => {
                      const curLines = form.lines || [];
                      setForm({
                        ...form,
                        lines: [
                          ...curLines,
                          {
                            analytic_name: analyticsList[0]?.name || 'Furniture',
                            type: 'Expense',
                            committed_amount: 200000,
                            achieved_amount: 10000,
                          },
                        ],
                      });
                    }}
                  >
                    ＋ Add Line
                  </Button>
                </div>
                <div className="line-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Analytic</th>
                        <th>Type</th>
                        <th>Committed Amount</th>
                        <th>Achieved Amount</th>
                        <th>Achieved %</th>
                        <th>Amount To Achieve</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {(form.lines || [
                        {
                          analytic_name: 'Furniture',
                          type: 'Expense',
                          committed_amount: 200000,
                          achieved_amount: 10000,
                        },
                      ]).map((l: any, i: number) => {
                        const committed = Number(l.committed_amount || 0);
                        const achieved = form.stage === 'Draft' ? 0 : Number(l.achieved_amount || 10000);
                        const pct = committed > 0 ? Math.round((achieved / committed) * 100) : 0;
                        const toAchieve = committed - achieved;
                        return (
                          <tr key={i}>
                            <td>
                              <select
                                value={l.analytic_name || ''}
                                onChange={(e) => {
                                  const anl = analyticsList.find((a) => a.name === e.target.value);
                                  const newLines = [...(form.lines || [])];
                                  newLines[i] = {
                                    ...newLines[i],
                                    analytic_name: e.target.value,
                                    type: anl?.type || newLines[i].type || 'Expense',
                                  };
                                  setForm({ ...form, lines: newLines });
                                }}
                              >
                                {analyticsList.map((anl) => (
                                  <option key={anl.id} value={anl.name}>
                                    {anl.name}
                                  </option>
                                ))}
                              </select>
                            </td>
                            <td>
                              <select
                                value={l.type || 'Expense'}
                                onChange={(e) => {
                                  const newLines = [...(form.lines || [])];
                                  newLines[i] = { ...newLines[i], type: e.target.value };
                                  setForm({ ...form, lines: newLines });
                                }}
                              >
                                <option value="Income">Income</option>
                                <option value="Expense">Expense</option>
                              </select>
                            </td>
                            <td>
                              <input
                                type="number"
                                step="0.01"
                                value={l.committed_amount || ''}
                                onChange={(e) => {
                                  const newLines = [...(form.lines || [])];
                                  newLines[i] = { ...newLines[i], committed_amount: e.target.value };
                                  setForm({ ...form, lines: newLines });
                                }}
                              />
                            </td>
                            <td>{form.stage === 'Draft' ? '0' : money(achieved)}</td>
                            <td>{form.stage === 'Draft' ? '0%' : `${pct}%`}</td>
                            <td>{form.stage === 'Draft' ? money(committed) : money(toAchieve)}</td>
                            <td>
                              {(form.lines || []).length > 1 && (
                                <button
                                  type="button"
                                  className="text-btn"
                                  onClick={() => {
                                    const newLines = form.lines.filter((_: any, idx: number) => idx !== i);
                                    setForm({ ...form, lines: newLines });
                                  }}
                                >
                                  ✕
                                </button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </form>
            ) : (
              <form id="master-modal-form" className="record-form-modal" onSubmit={save}>
                <h2 className="contact-modal-title">
                  {c.title} · {form.id ? 'Edit' : 'New'}
                </h2>
                <div className="form-grid">
                  {(c.fields || []).map((f: any) => (
                    <Field key={f[0]} label={f[1]} required={f[3]}>
                      <input
                        type={f[2] || 'text'}
                        value={form[f[0]] ?? ''}
                        onChange={(e) => setForm({ ...form, [f[0]]: e.target.value })}
                      />
                    </Field>
                  ))}
                </div>
                {error && <div className="error">{error}</div>}
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
}

export const Contacts = () => <Master kind="contacts" />;
export const Products = () => <Master kind="products" />;
export const Taxes = () => <Master kind="taxes" />;
export const Accounts = () => <Master kind="accounts" />;
export const Journals = () => <Master kind="journals" />;
export const Analytics = () => <Master kind="analytics" />;
export const Budgets = () => <Master kind="budgets" />;

