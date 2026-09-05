import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { auth, err, portal } from '../api';
import { Button, Empty, Field, PageHeader, Status, Toolbar, money } from '../components/UI';
import { ArrowLeft, CreditCard, FileText, LayoutDashboard, LockKeyhole, UserRound } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const dateValue = (value: any) => String(value || '-').slice(0, 10);
const dueOf = (row: any) => Number(row.due ?? Number(row.total || 0) - Number(row.paid || row.amount_paid || 0));

function PayButton({ row, type, onDone }: { row: any; type: 'invoice' | 'bill'; onDone: () => void }) {
  const [busy, setBusy] = useState(false);
  const pay = async () => {
    const outstanding = dueOf(row);
    const value = window.prompt(`Pay remaining ${money(outstanding)}`, String(outstanding));
    const amount = Number(value);
    if (!Number.isFinite(amount) || amount <= 0 || amount > outstanding) return;
    setBusy(true);
    try {
      if (type === 'invoice') await portal.pay({ sale_invoice_id: row.id, amount, receipt_date: new Date().toISOString().slice(0, 10) });
      else await portal.payBill({ purchase_bill_id: row.id, amount, payment_date: new Date().toISOString().slice(0, 10) });
      onDone();
    } finally { setBusy(false); }
  };
  return dueOf(row) > 0 ? <Button onClick={pay} disabled={busy}>{busy ? 'Processing...' : 'Pay Remaining'}</Button> : <Status value="Paid" />;
}

function DocumentTable({ rows, type, onRefresh, onOpen }: { rows: any[]; type: 'invoice' | 'bill'; onRefresh: () => void; onOpen: (id: number) => void }) {
  return rows.length ? <div className="table-card"><table><thead><tr><th>Number</th><th>Date</th><th>Due</th><th>Total</th><th>Paid</th><th>Due</th><th>Status</th><th>Action</th></tr></thead><tbody>
    {rows.map((row) => <tr key={row.id}><td><b>{row.number}</b></td><td>{dateValue(row.invoice_date || row.bill_date)}</td><td>{dateValue(row.due_date)}</td><td>{money(row.total)}</td><td>{money(row.amount_paid)}</td><td>{money(dueOf(row))}</td><td><Status value={row.payment_status || row.status} /></td><td><div className="row-actions"><Button variant="secondary" onClick={() => onOpen(row.id)}>View</Button>{dueOf(row) > 0 && <PayButton row={row} type={type} onDone={onRefresh} />}</div></td></tr>)}
  </tbody></table></div> : <Empty text={`No ${type === 'invoice' ? 'invoices' : 'bills'} available.`} />;
}

export function UserDashboard() {
  const [data, setData] = useState<any>(null); const [error, setError] = useState(''); const nav = useNavigate();
  const load = () => portal.dashboard().then((r) => setData(r.data)).catch((e) => setError(err(e)));
  useEffect(() => { load(); }, []);
  if (error) return <div className="error banner">{error}</div>;
  if (!data) return <div className="loading">Loading your workspace...</div>;
  return <><PageHeader title="Dashboard" subtitle="Your invoices, bills, payments, and outstanding dues." />
    <div className="kpi-grid"><div className="kpi"><span>Outstanding Amount</span><b>{money(data.outstanding)}</b></div><div className="kpi"><span>Overdue Amount</span><b>{money(data.overdue)}</b></div><div className="kpi"><span>Paid This Month</span><b>{money(data.paid_this_month)}</b></div><div className="kpi"><span>Total Paid</span><b>{money(data.total_paid)}</b></div></div>
    <div className="section-head"><h2>Outstanding Dues</h2></div><DocumentTable rows={[...(data.invoices || []), ...(data.bills || [])].filter((x) => dueOf(x) > 0)} type="invoice" onRefresh={load} onOpen={(id) => nav(`/user/invoices/${id}`)} />
    <div className="quick-actions"><Button onClick={() => nav('/user/invoices')}>View My Invoices</Button><Button onClick={() => nav('/user/bills')}>View My Bills</Button><Button onClick={() => nav('/user/payments')}>View My Payments</Button></div>
  </>;
}

export function UserDocuments({ type }: { type: 'invoice' | 'bill' }) {
  const [rows, setRows] = useState<any[]>([]); const [q, setQ] = useState(''); const nav = useNavigate();
  const load = () => (type === 'invoice' ? portal.myInvoices() : portal.myBills()).then((r) => setRows(r.data || []));
  useEffect(() => { load(); }, [type]);
  const filtered = rows.filter((x) => JSON.stringify(x).toLowerCase().includes(q.toLowerCase()));
  return <><PageHeader title={type === 'invoice' ? 'My Invoices' : 'My Bills'} subtitle="Only documents belonging to your account are shown." /><Toolbar search={q} onSearch={setQ} refresh={load} /><DocumentTable rows={filtered} type={type} onRefresh={load} onOpen={(id) => nav(`/user/${type === 'invoice' ? 'invoices' : 'bills'}/${id}`)} /></>;
}

export function UserPayments() {
  const [rows, setRows] = useState<any[]>([]); const [q, setQ] = useState('');
  const load = () => portal.myPayments().then((r) => setRows(r.data || [])); useEffect(() => { load(); }, []);
  const filtered = rows.filter((x) => JSON.stringify(x).toLowerCase().includes(q.toLowerCase()));
  return <><PageHeader title="My Payments" subtitle="Your payment history only." /><Toolbar search={q} onSearch={setQ} refresh={load} />{filtered.length ? <div className="table-card"><table><thead><tr><th>Payment Number</th><th>Date</th><th>Amount</th><th>Method</th><th>Status</th></tr></thead><tbody>{filtered.map((p) => <tr key={`${p.payment_type}-${p.id}`}><td>{p.number}</td><td>{dateValue(p.payment_date)}</td><td>{money(p.amount)}</td><td>{p.method || 'Bank'}</td><td><Status value={p.status || 'Posted'} /></td></tr>)}</tbody></table></div> : <Empty text="No payments recorded yet." />}</>;
}

export function UserWorkspaceDetail({ type }: { type: 'invoice' | 'bill' }) {
  const { id } = useParams(); const [data, setData] = useState<any>(null); const nav = useNavigate();
  useEffect(() => { (type === 'invoice' ? portal.invoice(Number(id)) : portal.bill(Number(id))).then((r) => setData(r.data)); }, [id, type]);
  if (!data) return <div className="loading">Loading document...</div>;
  return <><PageHeader title={data.number} subtitle={`${type === 'invoice' ? 'Invoice' : 'Bill'} detail`} back={() => nav(`/user/${type === 'invoice' ? 'invoices' : 'bills'}`)} action={dueOf(data) > 0 ? <PayButton row={data} type={type} onDone={() => nav('/user/payments')} /> : <Status value="Paid" />} /><div className="detail-grid"><div className="panel"><h3>Document Information</h3><p>Status: <Status value={data.status} /></p><p>Payment: <Status value={data.payment_status} /></p><p>Date: {dateValue(data.invoice_date || data.bill_date)}</p><p>Due: {dateValue(data.due_date)}</p></div><div className="panel"><h3>Party</h3><p>{data.contact?.name || '-'}</p><p>{data.contact?.email || '-'}</p><p>{data.contact?.phone || '-'}</p></div></div><div className="table-card"><table><thead><tr><th>Product</th><th>Qty</th><th>Unit Price</th><th>Tax</th><th>Line Total</th></tr></thead><tbody>{(data.lines || []).map((line: any, i: number) => <tr key={i}><td>{line.product}</td><td>{line.quantity}</td><td>{money(line.unit_price)}</td><td>{line.tax_rate}%</td><td>{money(line.line_total)}</td></tr>)}</tbody></table></div><div className="panel"><h3>Payment History</h3>{data.payments?.length ? data.payments.map((p: any) => <p key={p.number}>{p.number} · {dateValue(p.date)} · {money(p.amount)}</p>) : <Empty text="No payments recorded yet." />}</div></>;
}

export function UserProfile() { const { user } = useAuth(); return <><PageHeader title="My Profile" subtitle="Your account information." /><div className="panel profile-panel"><UserRound size={28} /><p><b>Name</b><br />{user?.name || '-'}</p><p><b>Login ID</b><br />{user?.login_id}</p><p><b>Email</b><br />{user?.email}</p><p><b>Role</b><br />User</p><p><b>Account Status</b><br />{user?.is_active ? 'Active' : 'Inactive'}</p></div></>; }

export function ChangePassword() { const [form, setForm] = useState({ current_password: '', new_password: '', re_password: '' }); const [message, setMessage] = useState(''); const [error, setError] = useState(''); const submit = async (e: any) => { e.preventDefault(); setError(''); setMessage(''); if (form.new_password !== form.re_password) return setError('Passwords do not match'); try { await auth.changePassword(form); setForm({ current_password: '', new_password: '', re_password: '' }); setMessage('Password changed successfully.'); } catch (value) { setError(err(value)); } }; return <><PageHeader title="Change Password" subtitle="Keep your account secure." /><form className="record-form" onSubmit={submit}><Field label="Current Password" required><input type="password" value={form.current_password} onChange={(e) => setForm({ ...form, current_password: e.target.value })} /></Field><Field label="New Password" required><input type="password" value={form.new_password} onChange={(e) => setForm({ ...form, new_password: e.target.value })} /></Field><Field label="Confirm New Password" required><input type="password" value={form.re_password} onChange={(e) => setForm({ ...form, re_password: e.target.value })} /></Field>{error && <div className="error">{error}</div>}{message && <div className="success">{message}</div>}<Button type="submit">CHANGE PASSWORD</Button></form></>; }