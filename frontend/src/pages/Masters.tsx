import { FormEvent, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { masters, err } from '../api';
import { Button, Empty, Field, PageHeader, Status, Toolbar, money } from '../components/UI';
import type { Contact, Product, Tax, Account, Journal, Analytic, Budget } from '../types/api';

const configs: any = {
  contacts: {
    title: 'Contacts',
    sub: 'Customers, vendors and business partners',
    api: masters.contacts,
    columns: ['Name', 'Type', 'Email', 'Phone', 'Status'],
    fields: [
      ['name', 'Contact Name', 'text', true],
      ['contact_type', 'Contact Type', 'select', true, ['customer', 'vendor', 'both']],
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
      ['name', 'Product Name', 'text', true],
      ['sku', 'SKU', 'text', true],
      ['description', 'Description', 'textarea'],
      ['unit_price', 'Sales Price', 'number', true],
      ['cost_price', 'Cost Price', 'number', true],
      ['tax_id', 'Tax', 'selectTax'],
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
      ['account_type', 'Account Type', 'select', true, ['asset', 'liability', 'equity', 'income', 'expense']],
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
      ['journal_type', 'Journal Type', 'select', true, ['sales', 'purchase', 'cash', 'bank']],
    ],
  },
  analytics: {
    title: 'Analytic Accounts',
    sub: 'Project or area classification for planning and analysis',
    api: masters.analytics,
    columns: ['Code', 'Analytic Account', 'Status'],
    fields: [
      ['code', 'Code', 'text', true],
      ['name', 'Analytic Account', 'text', true],
    ],
  },
  budgets: {
    title: 'Budgets',
    sub: 'Plan amounts against an account and reporting period',
    api: masters.budgets,
    columns: ['Budget', 'Account', 'Period', 'Amount'],
    fields: [
      ['name', 'Budget Name', 'text', true],
      ['account_id', 'Account', 'selectAccount', true],
      ['start_date', 'Start Date', 'date', true],
      ['end_date', 'End Date', 'date', true],
      ['amount', 'Budget Amount', 'number', true],
    ],
  },
};

function Master({ kind }: { kind: keyof typeof configs }) {
  const c = configs[kind];
  const nav = useNavigate();
  const [rows, setRows] = useState<any[]>([]);
  const [q, setQ] = useState('');
  const [view, setView] = useState<'list' | 'kanban'>('list');
  const [form, setForm] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [taxes, setTaxes] = useState<Tax[]>([]);

  const load = async () => {
    setLoading(true);
    try {
      const r = await c.api.list();
      setRows(r.data);
    } catch (e) {
      setError(err(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    if (kind === 'accounts' || kind === 'budgets') masters.accounts.list().then((r) => setAccounts(r.data));
    if (kind === 'products') masters.taxes.list().then((r) => setTaxes(r.data));
  }, [kind]);

  const filtered = useMemo(
    () => rows.filter((x) => JSON.stringify(x).toLowerCase().includes(q.toLowerCase())),
    [rows, q]
  );

  const save = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const payload = { ...form };
      for (const k of ['unit_price', 'cost_price', 'rate', 'amount']) {
        if (payload[k] !== undefined && payload[k] !== '') payload[k] = Number(payload[k]);
      }
      await c.api.create(payload);
      setForm(null);
      load();
    } catch (e) {
      setError(err(e));
    }
  };

  const deactivate = async (id: string) => {
    if (!confirm('Archive this record?')) return;
    try {
      await c.api.deactivate(id);
      load();
    } catch (e) {
      setError(err(e));
    }
  };

  if (form) {
    return (
      <>
        <PageHeader
          title={c.title + ' · ' + (form.id ? 'Edit' : 'New')}
          subtitle="The same form is used for creating and reviewing saved records."
          back={() => setForm(null)}
        />
        <form className="record-form" onSubmit={save}>
          <div className="form-grid">
            {c.fields.map((f: any) => (
              <Field key={f[0]} label={f[1]} required={f[3]}>
                {f[2] === 'textarea' ? (
                  <textarea
                    value={form[f[0]] || ''}
                    onChange={(e) => setForm({ ...form, [f[0]]: e.target.value })}
                  />
                ) : f[2] === 'select' ? (
                  <select
                    value={form[f[0]] || ''}
                    onChange={(e) => setForm({ ...form, [f[0]]: e.target.value })}
                  >
                    <option value="">Select...</option>
                    {f[4].map((x: string) => (
                      <option key={x} value={x}>
                        {x}
                      </option>
                    ))}
                  </select>
                ) : f[2] === 'selectAccount' ? (
                  <select
                    value={form[f[0]] || ''}
                    onChange={(e) => setForm({ ...form, [f[0]]: e.target.value || null })}
                  >
                    <option value="">Select account...</option>
                    {accounts.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.code} · {a.name}
                      </option>
                    ))}
                  </select>
                ) : f[2] === 'selectTax' ? (
                  <select
                    value={form[f[0]] || ''}
                    onChange={(e) => setForm({ ...form, [f[0]]: e.target.value || null })}
                  >
                    <option value="">No tax</option>
                    {taxes.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name} · {t.rate}%
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type={f[2]}
                    value={form[f[0]] ?? ''}
                    onChange={(e) => setForm({ ...form, [f[0]]: e.target.value })}
                  />
                )}
              </Field>
            ))}
          </div>
          {error && <div className="error">{error}</div>}
          <div className="form-actions">
            <Button type="submit">CONFIRM</Button>
            <Button type="button" variant="secondary" onClick={() => setForm(null)}>
              BACK
            </Button>
          </div>
        </form>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title={c.title}
        subtitle={c.sub}
        action={
          <Button onClick={() => setForm({})}>
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
      {error && <div className="error banner">{error}</div>}
      <div className="table-card">
        {loading ? (
          <div className="loading">Loading records...</div>
        ) : filtered.length === 0 ? (
          <Empty />
        ) : view === 'kanban' ? (
          <div className="kanban">
            {filtered.map((r: any) => (
              <div className="kanban-card" key={r.id} onClick={() => setForm({ ...r })}>
                <div className="kanban-top">
                  <div className="kanban-avatar">
                    {String(r.name || r.code || '?')
                      .slice(0, 1)
                      .toUpperCase()}
                  </div>
                  <Status value={r.is_active === false ? 'Archived' : 'Active'} />
                </div>
                <b>{r.name || r.code}</b>
                <span>{r.email || r.sku || r.code || ''}</span>
                <strong>
                  {kind === 'products'
                    ? money(r.unit_price)
                    : kind === 'budgets'
                    ? money(r.amount)
                    : kind === 'taxes'
                    ? `${Number(r.rate)}%`
                    : r.contact_type || r.account_type || r.journal_type || ''}
                </strong>
              </div>
            ))}
          </div>
        ) : (
          <table>
            <thead>
              <tr>
                {kind === 'accounts' ? (
                  <>
                    <th>Code</th>
                    <th>Account</th>
                    <th>Type</th>
                    <th>Status</th>
                  </>
                ) : (
                  c.columns.map((x: string) => <th key={x}>{x}</th>)
                )}
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r: any) => (
                <tr key={r.id} onClick={() => setForm({ ...r })}>
                  {kind === 'accounts' ? (
                    <>
                      <td>
                        <b>{r.code}</b>
                      </td>
                      <td>{r.name}</td>
                      <td>{r.account_type}</td>
                      <td>
                        <Status value={r.is_active ? 'Active' : 'Archived'} />
                      </td>
                    </>
                  ) : (
                    <>
                      <td>
                        <b>{r.name || r.code}</b>
                      </td>
                      {kind === 'contacts' && (
                        <>
                          <td>{r.contact_type}</td>
                          <td>{r.email || '—'}</td>
                          <td>{r.phone || '—'}</td>
                          <td>
                            <Status value={r.is_active ? 'Active' : 'Archived'} />
                          </td>
                        </>
                      )}
                      {kind === 'products' && (
                        <>
                          <td>{r.sku}</td>
                          <td>{money(r.unit_price)}</td>
                          <td>{money(r.cost_price)}</td>
                          <td>
                            <Status value={r.is_active ? 'Active' : 'Archived'} />
                          </td>
                        </>
                      )}
                      {kind === 'taxes' && (
                        <>
                          <td>{Number(r.rate)}%</td>
                          <td>{r.tax_type}</td>
                          <td>
                            <Status value={r.is_active ? 'Active' : 'Archived'} />
                          </td>
                        </>
                      )}
                      {kind === 'journals' && (
                        <>
                          <td>{r.name}</td>
                          <td>{r.journal_type}</td>
                          <td>
                            <Status value={r.is_active ? 'Active' : 'Archived'} />
                          </td>
                        </>
                      )}
                      {kind === 'analytics' && (
                        <>
                          <td>{r.name}</td>
                          <td>
                            <Status value={r.is_active ? 'Active' : 'Archived'} />
                          </td>
                        </>
                      )}
                      {kind === 'budgets' && (
                        <>
                          <td>{r.account_id}</td>
                          <td>
                            {String(r.start_date).slice(0, 10)} → {String(r.end_date).slice(0, 10)}
                          </td>
                          <td>{money(r.amount)}</td>
                        </>
                      )}
                    </>
                  )}
                  <td>
                    {c.api.deactivate && (
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

