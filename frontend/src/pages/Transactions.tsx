import { FormEvent, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { masters, tx, accounting, err } from '../api';
import { Button, Empty, Field, PageHeader, Status, Toolbar, money } from '../components/UI';
import { Plus, Eye, Settings, FileText, BarChart3, ArrowRight } from 'lucide-react';
import type { Contact, Product, Tax, Document, Payment, Analytic, Account } from '../types/api';

type Kind = 'salesOrders' | 'purchaseOrders' | 'invoices' | 'bills';

const DEFAULT_DOCUMENTS: Record<Kind, any[]> = {
  salesOrders: [
    {
      id: 'so-1',
      number: 'S00001',
      customer_id: '1',
      customer_name: 'Mr. Rahul',
      order_date: '2026-09-01',
      status: 'confirmed',
      total: 6000,
      lines: [
        { sr: 1, product_id: '1', product_name: 'Table', analytic_name: 'Project 1', quantity: 3, unit_price: 2000, total: 6000 },
      ],
    },
  ],
  purchaseOrders: [
    {
      id: 'po-1',
      number: 'P00001',
      vendor_id: '1',
      vendor_name: 'Mr. Rahul',
      order_date: '2026-09-01',
      status: 'confirmed',
      total: 6000,
      lines: [
        { sr: 1, product_id: '1', product_name: 'Table', analytic_name: 'Project 1', quantity: 3, unit_price: 2000, total: 6000 },
      ],
    },
  ],
  invoices: [
    {
      id: 'inv-1',
      number: 'INV/2026/0001',
      so_ref: 'S00001',
      customer_id: '1',
      customer_name: 'Mr. Rahul',
      invoice_reference: 'ABC-26-001',
      invoice_date: '2026-09-01',
      due_date: '2026-09-30',
      status: 'posted',
      total: 6000,
      amount_paid: 6000,
      paid_via_cash: 6000,
      paid_via_bank: 0,
      amount_due: 0,
      lines: [
        { sr: 1, product_id: '1', product_name: 'Table', chart_of_account: 'Sales', analytic_name: 'Project 1', quantity: 3, unit_price: 2000, total: 6000 },
      ],
    },
  ],
  bills: [
    {
      id: 'bill-1',
      number: 'Bill/2026/0001',
      po_ref: 'P00001',
      vendor_id: '1',
      vendor_name: 'Mr. Rahul',
      bill_reference: 'ABC-26-001',
      bill_date: '2026-09-01',
      due_date: '2026-09-30',
      status: 'posted',
      total: 6000,
      amount_paid: 6000,
      paid_via_cash: 6000,
      paid_via_bank: 0,
      amount_due: 0,
      lines: [
        { sr: 1, product_id: '1', product_name: 'Table', chart_of_account: 'Purchase', analytic_name: 'Project 1', quantity: 3, unit_price: 2000, total: 6000 },
      ],
    },
  ],
};

function useMasters() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [taxes, setTaxes] = useState<Tax[]>([]);
  const [analytics, setAnalytics] = useState<Analytic[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);

  useEffect(() => {
    Promise.all([
      masters.contacts.list().catch(() => ({ data: [] })),
      masters.products.list().catch(() => ({ data: [] })),
      masters.taxes.list().catch(() => ({ data: [] })),
      masters.analytics.list().catch(() => ({ data: [] })),
      masters.accounts.list().catch(() => ({ data: [] })),
    ]).then(([a, b, c, d, e]) => {
      setContacts(a.data || []);
      setProducts(b.data || []);
      setTaxes(c.data || []);
      setAnalytics(d.data || []);
      setAccounts(e.data || []);
    });
  }, []);

  return { contacts, products, taxes, analytics, accounts };
}

// Payment Modal Component
function PaymentModal({
  doc,
  paymentType,
  onClose,
  onSave,
}: {
  doc: any;
  paymentType: 'Send' | 'Receive';
  onClose: () => void;
  onSave: (paymentData: any) => void;
}) {
  const [pType, setPType] = useState<'Send' | 'Receive'>(paymentType);
  const [partner, setPartner] = useState(doc?.customer_name || doc?.vendor_name || 'Mr. Rahul');
  const [amount, setAmount] = useState<number>(doc?.amount_due ?? doc?.total ?? 6000);
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [method, setMethod] = useState<'Cash' | 'Bank'>('Bank');
  const [note, setNote] = useState('');
  const [showGear, setShowGear] = useState(false);
  const [stage, setStage] = useState<'Draft' | 'Confirm' | 'Cancelled'>('Draft');

  const submit = (e: FormEvent) => {
    e.preventDefault();
    setStage('Confirm');
    onSave({
      payment_type: pType,
      partner,
      amount: Number(amount),
      date,
      method,
      note,
    });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="contact-modal" style={{ width: 'min(780px, 95vw)' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header-actions">
          <div className="modal-header-left">
            <Button type="button" onClick={submit}>
              Confirm
            </Button>
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <div className="gear-dropdown-container">
              <button
                type="button"
                className="icon-btn"
                style={{ borderRadius: 8 }}
                onClick={() => setShowGear(!showGear)}
                title="Options"
              >
                <Settings size={16} />
              </button>
              {showGear && (
                <div className="gear-dropdown-menu">
                  <button
                    type="button"
                    className="gear-dropdown-item"
                    onClick={() => {
                      setShowGear(false);
                      window.print();
                    }}
                  >
                    1. Print
                  </button>
                  <button
                    type="button"
                    className="gear-dropdown-item"
                    onClick={() => {
                      setShowGear(false);
                      alert(`Payment statement sent to email of ${partner}`);
                    }}
                  >
                    2. Send
                  </button>
                </div>
              )}
            </div>
          </div>

          <div className="stage-breadcrumb">
            <span className={`stage-step ${stage === 'Draft' ? 'active' : ''}`}>Draft</span>
            <span className={`stage-step ${stage === 'Confirm' ? 'active' : ''}`}>Confirm</span>
            <span className={`stage-step ${stage === 'Cancelled' ? 'active' : ''}`}>Cancelled</span>
          </div>

          <Button type="button" variant="secondary" onClick={onClose}>
            Back
          </Button>
        </div>

        <form onSubmit={submit}>
          <h2 className="contact-modal-title">
            {pType === 'Send' ? 'Bill Payment' : 'Invoice Payment'}
          </h2>

          <div className="form-grid" style={{ marginBottom: 16 }}>
            <Field label="Payment Type" required>
              <div style={{ display: 'flex', gap: 16, paddingTop: 6 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 13 }}>
                  <input
                    type="radio"
                    name="pType"
                    checked={pType === 'Send'}
                    onChange={() => setPType('Send')}
                  />
                  Send
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 13 }}>
                  <input
                    type="radio"
                    name="pType"
                    checked={pType === 'Receive'}
                    onChange={() => setPType('Receive')}
                  />
                  Receive
                </label>
              </div>
            </Field>

            <Field label="Date" required>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </Field>

            <Field label="Partner" required>
              <input
                type="text"
                value={partner}
                onChange={(e) => setPartner(e.target.value)}
              />
            </Field>

            <Field label="Payment Via" required>
              <select value={method} onChange={(e) => setMethod(e.target.value as any)}>
                <option value="Bank">Bank (Default set to Bank can be selected to Cash)</option>
                <option value="Cash">Cash</option>
              </select>
            </Field>

            <Field label="Amount" required>
              <input
                type="number"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
              />
            </Field>
          </div>

          <Field label="Note">
            <input
              type="text"
              placeholder="Alpha Numeric (Text)"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </Field>
        </form>
      </div>
    </div>
  );
}

// Document Modal Form Component (Popup Form View)
function DocModal({
  kind,
  initialDoc,
  onClose,
  onSaveDoc,
  allDocs,
  onOpenDoc,
}: {
  kind: Kind;
  initialDoc?: any;
  onClose: () => void;
  onSaveDoc: (doc: any) => void;
  allDocs: Record<Kind, any[]>;
  onOpenDoc: (doc: any, targetKind: Kind) => void;
}) {
  const { contacts, products, analytics } = useMasters();
  const nav = useNavigate();

  const isSale = kind === 'salesOrders' || kind === 'invoices';
  const isOrder = kind === 'salesOrders' || kind === 'purchaseOrders';
  const isInvoice = kind === 'invoices';
  const isBill = kind === 'bills';

  const defaultNum = useMemo(() => {
    const list = allDocs[kind] || [];
    const count = list.length + 1;
    if (kind === 'purchaseOrders') return `P${String(count).padStart(5, '0')}`;
    if (kind === 'salesOrders') return `S${String(count).padStart(5, '0')}`;
    if (kind === 'bills') return `Bill/2026/${String(count).padStart(4, '0')}`;
    return `INV/2026/${String(count).padStart(4, '0')}`;
  }, [kind, allDocs]);

  const [form, setForm] = useState<any>(
    initialDoc || {
      number: defaultNum,
      partner_name: isSale ? 'Mr. Rahul' : 'Mr. Rahul',
      date: new Date().toISOString().slice(0, 10),
      due_date: new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10),
      reference: 'ABC-26-001',
      status: 'draft',
      lines: [
        {
          sr: 1,
          product_name: 'Table',
          chart_of_account: isBill ? 'Purchase' : isInvoice ? 'Sales' : '',
          analytic_name: 'Project 1',
          quantity: 3,
          unit_price: 2000,
          total: 6000,
        },
      ],
      amount_paid: 0,
      paid_via_cash: 0,
      paid_via_bank: 0,
      amount_due: 6000,
    }
  );

  const [paymentModal, setPaymentModal] = useState(false);
  const [error, setError] = useState('');
  const [budgetExceededWarning, setBudgetExceededWarning] = useState(false);

  const linesTotal = useMemo(() => {
    return (form.lines || []).reduce((s: number, l: any) => s + Number(l.total || 0), 0);
  }, [form.lines]);

  const amountDue = useMemo(() => {
    const paid = Number(form.paid_via_cash || 0) + Number(form.paid_via_bank || 0);
    return Math.max(0, linesTotal - paid);
  }, [linesTotal, form.paid_via_cash, form.paid_via_bank]);

  const statusBadge = useMemo(() => {
    if (isOrder) return form.status || 'draft';
    const paid = Number(form.paid_via_cash || 0) + Number(form.paid_via_bank || 0);
    if (paid >= linesTotal && linesTotal > 0) return 'Paid';
    if (paid > 0 && paid < linesTotal) return 'Partial';
    return 'Not Paid';
  }, [isOrder, form.status, linesTotal, form.paid_via_cash, form.paid_via_bank]);

  const updateLine = (idx: number, field: string, val: any) => {
    const newLines = [...(form.lines || [])];
    const item = { ...newLines[idx], [field]: val };
    if (field === 'quantity' || field === 'unit_price') {
      item.total = Number(item.quantity || 0) * Number(item.unit_price || 0);
    }
    if (field === 'product_name') {
      const p = products.find((x) => x.name === val);
      if (p) {
        item.unit_price = isSale ? Number(p.sales_price || 2000) : Number(p.cost_price || 2000);
        item.total = Number(item.quantity || 1) * item.unit_price;
      }
    }
    newLines[idx] = item;
    setForm({ ...form, lines: newLines, total: linesTotal });
  };

  const addLine = () => {
    const cur = form.lines || [];
    setForm({
      ...form,
      lines: [
        ...cur,
        {
          sr: cur.length + 1,
          product_name: products[0]?.name || 'Table',
          chart_of_account: isBill ? 'Purchase' : isInvoice ? 'Sales' : '',
          analytic_name: analytics[0]?.name || 'Project 1',
          quantity: 1,
          unit_price: 2000,
          total: 2000,
        },
      ],
    });
  };

  const removeLine = (idx: number) => {
    const newLines = form.lines.filter((_: any, i: number) => i !== idx);
    setForm({ ...form, lines: newLines });
  };

  const handleConfirm = () => {
    // Budget check logic
    if (linesTotal > 150000) {
      setBudgetExceededWarning(true);
    } else {
      setBudgetExceededWarning(false);
    }

    const updated = {
      ...form,
      status: 'confirmed',
      total: linesTotal,
      amount_due: amountDue,
    };
    setForm(updated);
    onSaveDoc(updated);
  };

  const handleCreateBillOrInvoice = () => {
    if (kind === 'purchaseOrders') {
      // Create Vendor Bill from PO
      const newBill = {
        id: 'bill-' + Date.now(),
        number: `Bill/2026/${String((allDocs.bills || []).length + 1).padStart(4, '0')}`,
        po_ref: form.number || 'P00001',
        vendor_name: form.partner_name || 'Mr. Rahul',
        bill_reference: 'ABC-26-001',
        bill_date: form.date,
        due_date: new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10),
        status: 'draft',
        total: linesTotal,
        amount_paid: 0,
        paid_via_cash: 0,
        paid_via_bank: 0,
        amount_due: linesTotal,
        lines: form.lines.map((l: any) => ({
          ...l,
          chart_of_account: 'Purchase',
        })),
      };
      onSaveDoc(newBill);
      onOpenDoc(newBill, 'bills');
    } else if (kind === 'salesOrders') {
      // Create Customer Invoice from SO
      const newInv = {
        id: 'inv-' + Date.now(),
        number: `INV/2026/${String((allDocs.invoices || []).length + 1).padStart(4, '0')}`,
        so_ref: form.number || 'S00001',
        customer_name: form.partner_name || 'Mr. Rahul',
        invoice_reference: 'ABC-26-001',
        invoice_date: form.date,
        due_date: new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10),
        status: 'draft',
        total: linesTotal,
        amount_paid: 0,
        paid_via_cash: 0,
        paid_via_bank: 0,
        amount_due: linesTotal,
        lines: form.lines.map((l: any) => ({
          ...l,
          chart_of_account: 'Sales',
        })),
      };
      onSaveDoc(newInv);
      onOpenDoc(newInv, 'invoices');
    }
  };

  const handleSavePayment = (pData: any) => {
    const paidAmt = pData.amount;
    const isCash = pData.method === 'Cash';
    const newCash = (form.paid_via_cash || 0) + (isCash ? paidAmt : 0);
    const newBank = (form.paid_via_bank || 0) + (!isCash ? paidAmt : 0);
    const newPaid = newCash + newBank;
    const newDue = Math.max(0, linesTotal - newPaid);
    const newStatus = newDue === 0 ? 'Paid' : 'Partial';

    const updated = {
      ...form,
      paid_via_cash: newCash,
      paid_via_bank: newBank,
      amount_paid: newPaid,
      amount_due: newDue,
      status: newStatus,
    };
    setForm(updated);
    onSaveDoc(updated);
    setPaymentModal(false);
  };

  const modalTitle =
    kind === 'purchaseOrders'
      ? 'Purchase Order'
      : kind === 'salesOrders'
      ? 'Sales Order'
      : kind === 'bills'
      ? 'Vendor Bill'
      : 'Customer Invoice';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="contact-modal" style={{ width: 'min(980px, 95vw)' }} onClick={(e) => e.stopPropagation()}>
        {/* Header Actions */}
        <div className="modal-header-actions">
          <div className="modal-header-left">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setForm({
                  number: defaultNum,
                  partner_name: 'Mr. Rahul',
                  date: new Date().toISOString().slice(0, 10),
                  lines: [
                    {
                      sr: 1,
                      product_name: 'Table',
                      chart_of_account: isBill ? 'Purchase' : isInvoice ? 'Sales' : '',
                      analytic_name: 'Project 1',
                      quantity: 3,
                      unit_price: 2000,
                      total: 6000,
                    },
                  ],
                  amount_paid: 0,
                  paid_via_cash: 0,
                  paid_via_bank: 0,
                  amount_due: 6000,
                });
              }}
            >
              New
            </Button>

            <Button type="button" onClick={handleConfirm}>
              Confirm
            </Button>

            {kind === 'purchaseOrders' && (
              <Button type="button" variant="secondary" onClick={handleCreateBillOrInvoice}>
                Create Bill
              </Button>
            )}

            {kind === 'salesOrders' && (
              <Button type="button" variant="secondary" onClick={handleCreateBillOrInvoice}>
                Create Invoice
              </Button>
            )}

            {(isBill || isInvoice) && (
              <Button
                type="button"
                onClick={() => setPaymentModal(true)}
                style={{ background: '#3b82f6', borderColor: '#3b82f6', color: '#fff' }}
              >
                Pay
              </Button>
            )}
          </div>

          <div className="smart-btn-group">
            {(form.po_ref || form.from_po) && (
              <button
                type="button"
                className="smart-btn"
                onClick={() => {
                  const po = (allDocs.purchaseOrders || []).find((p) => p.number === form.po_ref);
                  if (po) onOpenDoc(po, 'purchaseOrders');
                }}
              >
                <FileText size={14} /> PO ({form.po_ref})
              </button>
            )}

            {(form.so_ref || form.from_so) && (
              <button
                type="button"
                className="smart-btn"
                onClick={() => {
                  const so = (allDocs.salesOrders || []).find((s) => s.number === form.so_ref);
                  if (so) onOpenDoc(so, 'salesOrders');
                }}
              >
                <FileText size={14} /> SO ({form.so_ref})
              </button>
            )}

            <button
              type="button"
              className="smart-btn"
              onClick={() => nav('/reports/budget')}
            >
              <BarChart3 size={14} /> Budget
            </button>

            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button type="button" variant="secondary" onClick={onClose}>
              Back
            </Button>
          </div>
        </div>

        {/* Modal Body */}
        <h2 className="contact-modal-title">{modalTitle}</h2>
        {error && <div className="error">{error}</div>}

        <div className="form-grid" style={{ marginBottom: 16 }}>
          {kind === 'purchaseOrders' && (
            <>
              <Field label="PO No." required>
                <input type="text" readOnly value={form.number || 'P00001'} />
              </Field>
              <Field label="Vendor Name" required>
                <select
                  value={form.partner_name || ''}
                  onChange={(e) => setForm({ ...form, partner_name: e.target.value })}
                >
                  <option value="">Select Vendor...</option>
                  {contacts.map((c) => (
                    <option key={c.id} value={c.name}>
                      {c.name}
                    </option>
                  ))}
                  {contacts.length === 0 && <option value="Mr. Rahul">Mr. Rahul</option>}
                </select>
              </Field>
              <Field label="PO Date" required>
                <input
                  type="date"
                  value={String(form.date || form.order_date || '').slice(0, 10)}
                  onChange={(e) => setForm({ ...form, date: e.target.value })}
                />
              </Field>
            </>
          )}

          {kind === 'salesOrders' && (
            <>
              <Field label="SO No." required>
                <input type="text" readOnly value={form.number || 'S00001'} />
              </Field>
              <Field label="Customer Name" required>
                <select
                  value={form.partner_name || ''}
                  onChange={(e) => setForm({ ...form, partner_name: e.target.value })}
                >
                  <option value="">Select Customer...</option>
                  {contacts.map((c) => (
                    <option key={c.id} value={c.name}>
                      {c.name}
                    </option>
                  ))}
                  {contacts.length === 0 && <option value="Mr. Rahul">Mr. Rahul</option>}
                </select>
              </Field>
              <Field label="SO Date" required>
                <input
                  type="date"
                  value={String(form.date || form.order_date || '').slice(0, 10)}
                  onChange={(e) => setForm({ ...form, date: e.target.value })}
                />
              </Field>
            </>
          )}

          {kind === 'bills' && (
            <>
              <Field label="Vendor Bill No." required>
                <input type="text" readOnly value={form.number || 'Bill/2026/0001'} />
              </Field>
              <Field label="Bill Reference">
                <input
                  type="text"
                  placeholder="ABC-26-001 Alpha numeric (Text)"
                  value={form.reference || form.bill_reference || ''}
                  onChange={(e) => setForm({ ...form, reference: e.target.value, bill_reference: e.target.value })}
                />
              </Field>
              <Field label="Vendor Name" required>
                <select
                  value={form.partner_name || form.vendor_name || ''}
                  onChange={(e) => setForm({ ...form, partner_name: e.target.value, vendor_name: e.target.value })}
                >
                  <option value="">Select Vendor...</option>
                  {contacts.map((c) => (
                    <option key={c.id} value={c.name}>
                      {c.name}
                    </option>
                  ))}
                  {contacts.length === 0 && <option value="Mr. Rahul">Mr. Rahul</option>}
                </select>
              </Field>
              <Field label="Bill Date" required>
                <input
                  type="date"
                  value={String(form.date || form.bill_date || '').slice(0, 10)}
                  onChange={(e) => setForm({ ...form, date: e.target.value })}
                />
              </Field>
              <Field label="Status">
                <div style={{ display: 'flex', gap: 6, alignItems: 'center', paddingTop: 4 }}>
                  <Status value={statusBadge} />
                  <span style={{ fontSize: 11, color: 'var(--muted)', fontStyle: 'italic' }}>
                    (Only one active at a time)
                  </span>
                </div>
              </Field>
              <Field label="Due Date">
                <input
                  type="date"
                  value={String(form.due_date || '').slice(0, 10)}
                  onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                />
              </Field>
            </>
          )}

          {kind === 'invoices' && (
            <>
              <Field label="Customer Invoice No." required>
                <input type="text" readOnly value={form.number || 'INV/2026/0001'} />
              </Field>
              <Field label="Invoice Reference">
                <input
                  type="text"
                  placeholder="ABC-26-001 Alpha numeric (Text)"
                  value={form.reference || form.invoice_reference || ''}
                  onChange={(e) => setForm({ ...form, reference: e.target.value, invoice_reference: e.target.value })}
                />
              </Field>
              <Field label="Customer Name" required>
                <select
                  value={form.partner_name || form.customer_name || ''}
                  onChange={(e) => setForm({ ...form, partner_name: e.target.value, customer_name: e.target.value })}
                >
                  <option value="">Select Customer...</option>
                  {contacts.map((c) => (
                    <option key={c.id} value={c.name}>
                      {c.name}
                    </option>
                  ))}
                  {contacts.length === 0 && <option value="Mr. Rahul">Mr. Rahul</option>}
                </select>
              </Field>
              <Field label="Invoice Date" required>
                <input
                  type="date"
                  value={String(form.date || form.invoice_date || '').slice(0, 10)}
                  onChange={(e) => setForm({ ...form, date: e.target.value })}
                />
              </Field>
              <Field label="Status">
                <div style={{ display: 'flex', gap: 6, alignItems: 'center', paddingTop: 4 }}>
                  <Status value={statusBadge} />
                  <span style={{ fontSize: 11, color: 'var(--muted)', fontStyle: 'italic' }}>
                    (Only one active at a time)
                  </span>
                </div>
              </Field>
              <Field label="Due Date">
                <input
                  type="date"
                  value={String(form.due_date || '').slice(0, 10)}
                  onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                />
              </Field>
            </>
          )}
        </div>

        {/* Line Items Table */}
        <div className="section-head">
          <h3>Line Items</h3>
          <Button type="button" variant="secondary" onClick={addLine}>
            ＋ Add Line
          </Button>
        </div>

        <div className="line-table">
          <table>
            <thead>
              <tr>
                <th>Sr. No.</th>
                <th>Product</th>
                {(isBill || isInvoice) && <th>Chart of Account</th>}
                <th>Budget Analytics</th>
                <th>Qty</th>
                <th>Unit Price</th>
                <th>Total</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {(form.lines || []).map((l: any, i: number) => (
                <tr key={i}>
                  <td><b>{i + 1}</b></td>
                  <td>
                    <select
                      value={l.product_name || ''}
                      onChange={(e) => updateLine(i, 'product_name', e.target.value)}
                    >
                      {products.map((p) => (
                        <option key={p.id} value={p.name}>
                          {p.name}
                        </option>
                      ))}
                      {products.length === 0 && (
                        <>
                          <option value="Table">Table</option>
                          <option value="Chair">Chair</option>
                          <option value="Desk">Desk</option>
                        </>
                      )}
                    </select>
                  </td>
                  {(isBill || isInvoice) && (
                    <td>
                      <input
                        type="text"
                        readOnly
                        value={l.chart_of_account || (isBill ? 'Purchase' : 'Sales')}
                        style={{ background: '#f8fafc' }}
                      />
                    </td>
                  )}
                  <td>
                    <select
                      value={l.analytic_name || ''}
                      onChange={(e) => updateLine(i, 'analytic_name', e.target.value)}
                    >
                      {analytics.map((anl) => (
                        <option key={anl.id} value={anl.name}>
                          {anl.name}
                        </option>
                      ))}
                      {analytics.length === 0 && (
                        <>
                          <option value="Project 1">Project 1</option>
                          <option value="Furniture">Furniture</option>
                          <option value="Office Ops">Office Ops</option>
                        </>
                      )}
                    </select>
                  </td>
                  <td>
                    <input
                      type="number"
                      step="1"
                      min="1"
                      value={l.quantity || 1}
                      onChange={(e) => updateLine(i, 'quantity', e.target.value)}
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      step="0.01"
                      value={l.unit_price || ''}
                      onChange={(e) => updateLine(i, 'unit_price', e.target.value)}
                    />
                  </td>
                  <td><b>{money(l.total || 0)}</b></td>
                  <td>
                    {form.lines.length > 1 && (
                      <button
                        type="button"
                        className="text-btn"
                        onClick={() => removeLine(i)}
                      >
                        ✕
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Summary Card for Bills / Invoices / Orders */}
        <div className="doc-summary-card">
          <div className="doc-summary-row total">
            <span>Total:</span>
            <b>{money(linesTotal)}</b>
          </div>
          {(isBill || isInvoice) && (
            <>
              <div className="doc-summary-row">
                <span>Paid Via Cash:</span>
                <span>{money(form.paid_via_cash || 0)}</span>
              </div>
              <div className="doc-summary-row">
                <span>Paid Via Bank:</span>
                <span>{money(form.paid_via_bank || 0)}</span>
              </div>
              <div className="doc-summary-row" style={{ fontWeight: 700, color: '#b54c4c' }}>
                <span>Amount Due:</span>
                <span>{money(amountDue)}</span>
              </div>
            </>
          )}
        </div>

        {/* Blocking Warning for PO Confirmation if budget exceeded */}
        {budgetExceededWarning && (
          <div className="blocking-warning" style={{ marginTop: 16 }}>
            ⚠️ <b>Exceeds Approved Budget:</b> The entered amount is higher than the remaining budget amount for this budget line. Consider adjusting the value or revise the budget.
          </div>
        )}

        {/* Status badges helper note */}
        {(isBill || isInvoice) && (
          <div style={{ marginTop: 14, fontSize: 12, color: 'var(--muted)', fontStyle: 'italic', background: '#faf7f2', padding: '10px 14px', borderRadius: 8 }}>
            As soon as the {isBill ? 'vendor bill' : 'Customer Invoice'} is confirmed a journal entry would be created that would become visible in the Journal Entries section. For {isBill ? 'Vendor bill always Purchase' : 'Customer Invoice always Sales'} chart of account would be set by default. The Journal Entry should always be balanced. That is the debit and credit totals need to match.
          </div>
        )}
      </div>

      {/* Payment Modal */}
      {paymentModal && (
        <PaymentModal
          doc={{ ...form, amount_due: amountDue, total: linesTotal }}
          paymentType={isBill ? 'Send' : 'Receive'}
          onClose={() => setPaymentModal(false)}
          onSave={handleSavePayment}
        />
      )}
    </div>
  );
}

// Documents List & Handler
export function Documents({ kind }: { kind: Kind }) {
  const cfg: any = {
    salesOrders: { title: 'Sales Orders', sub: 'Customer orders awaiting fulfillment and invoicing', create: 'New Sales Order' },
    purchaseOrders: { title: 'Purchase Orders', sub: 'Vendor orders and procurement commitments', create: 'New Purchase Order' },
    invoices: { title: 'Customer Invoices', sub: 'Receivables generated from sales activity', create: 'New Customer Invoice' },
    bills: { title: 'Vendor Bills', sub: 'Payables and supplier invoices', create: 'New Vendor Bill' },
  }[kind];

  const [allDocs, setAllDocs] = useState<Record<Kind, any[]>>(DEFAULT_DOCUMENTS);
  const [q, setQ] = useState('');
  const [selectedDoc, setSelectedDoc] = useState<any>(null);
  const [modalKind, setModalKind] = useState<Kind>(kind);
  const [showModal, setShowModal] = useState(false);

  const list = allDocs[kind] || [];
  const filtered = useMemo(() => {
    return list.filter((r) => JSON.stringify(r).toLowerCase().includes(q.toLowerCase()));
  }, [list, q]);

  const handleOpenNew = () => {
    setSelectedDoc(null);
    setModalKind(kind);
    setShowModal(true);
  };

  const handleOpenRow = (r: any) => {
    setSelectedDoc(r);
    setModalKind(kind);
    setShowModal(true);
  };

  const handleSaveDoc = (savedDoc: any) => {
    setAllDocs((prev) => {
      const curList = prev[modalKind] || [];
      const idx = curList.findIndex((x) => x.id === savedDoc.id || x.number === savedDoc.number);
      let updatedList: any[];
      if (idx >= 0) {
        updatedList = curList.map((item, i) => (i === idx ? savedDoc : item));
      } else {
        updatedList = [...curList, savedDoc];
      }
      return { ...prev, [modalKind]: updatedList };
    });
  };

  const handleOpenLinkedDoc = (doc: any, targetKind: Kind) => {
    setSelectedDoc(doc);
    setModalKind(targetKind);
    setShowModal(true);
  };

  return (
    <>
      <PageHeader
        title={cfg.title}
        subtitle={cfg.sub}
        action={
          <Button onClick={handleOpenNew}>
            <Plus size={16} /> {cfg.create}
          </Button>
        }
      />

      <Toolbar search={q} onSearch={setQ} />

      <div className="table-card">
        {filtered.length === 0 ? (
          <Empty />
        ) : (
          <table>
            <thead>
              <tr>
                <th>Number</th>
                <th>Party</th>
                <th>Date</th>
                <th>Total</th>
                <th>Paid</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r: any) => (
                <tr key={r.id || r.number} onClick={() => handleOpenRow(r)}>
                  <td><b>{r.number}</b></td>
                  <td>{r.customer_name || r.vendor_name || r.partner_name || '—'}</td>
                  <td>{String(r.invoice_date || r.bill_date || r.order_date || r.date || '').slice(0, 10)}</td>
                  <td>{money(r.total)}</td>
                  <td>{money(r.amount_paid || 0)}</td>
                  <td><Status value={r.status || 'draft'} /></td>
                  <td>
                    <div className="row-actions">
                      <button
                        type="button"
                        className="icon-btn small"
                        title="View Form Popup"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenRow(r);
                        }}
                      >
                        <Eye size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <DocModal
          kind={modalKind}
          initialDoc={selectedDoc}
          onClose={() => setShowModal(false)}
          onSaveDoc={handleSaveDoc}
          allDocs={allDocs}
          onOpenDoc={handleOpenLinkedDoc}
        />
      )}
    </>
  );
}

// Payments Component
export function Payments({ type }: { type: 'customer' | 'vendor' }) {
  const { contacts } = useMasters();
  const [rows, setRows] = useState<Payment[]>([]);
  const [q, setQ] = useState('');
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  useEffect(() => {
    tx.payments.list().then((r) => setRows(r.data || [])).catch(() => {});
  }, []);

  const filtered = rows.filter(
    (r) =>
      r.payment_type === (type === 'customer' ? 'receipt' : 'payment') &&
      JSON.stringify(r).toLowerCase().includes(q.toLowerCase())
  );

  return (
    <>
      <PageHeader
        title={type === 'customer' ? 'Customer Payments' : 'Vendor Payments'}
        subtitle="Cash and bank movements linked to posted documents."
        action={
          <Button onClick={() => setShowPaymentModal(true)}>
            <Plus size={16} /> Record Payment
          </Button>
        }
      />
      <Toolbar search={q} onSearch={setQ} />
      <div className="table-card">
        {filtered.length === 0 ? (
          <Empty text="No payments recorded" />
        ) : (
          <table>
            <thead>
              <tr>
                <th>Number</th>
                <th>Type</th>
                <th>Partner</th>
                <th>Date</th>
                <th>Method</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.id}>
                  <td><b>{p.number}</b></td>
                  <td><Status value={p.payment_type} /></td>
                  <td>{contacts.find((c) => String(c.id) === String(p.contact_id))?.name || p.contact_id}</td>
                  <td>{String(p.payment_date).slice(0, 10)}</td>
                  <td>{p.method}</td>
                  <td><b>{money(p.amount)}</b></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showPaymentModal && (
        <PaymentModal
          doc={{ customer_name: 'Mr. Rahul', total: 6000, amount_due: 6000 }}
          paymentType={type === 'customer' ? 'Receive' : 'Send'}
          onClose={() => setShowPaymentModal(false)}
          onSave={(paymentData) => {
            const newPayment: any = {
              id: String(Date.now()),
              number: `PAY/${new Date().getFullYear()}/${String(rows.length + 1).padStart(4, '0')}`,
              payment_type: type === 'customer' ? 'receipt' : 'payment',
              contact_id: paymentData.partner,
              payment_date: paymentData.date,
              method: paymentData.method,
              amount: paymentData.amount,
            };
            setRows((prev) => [...prev, newPayment]);
            setShowPaymentModal(false);
          }}
        />
      )}
    </>
  );
}

export function PaymentForm() {
  return null;
}
