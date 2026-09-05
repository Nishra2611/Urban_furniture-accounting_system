import { useEffect, useState } from 'react';
import { portal, err } from '../api';
import { Button, Empty, PageHeader, Status, money } from '../components/UI';
import { Receipt, FileText } from 'lucide-react';

function dateValue(value: string) {
  return String(value || '').slice(0, 10);
}

export default function Portal() {
  const [invoices, setInvoices] = useState<any[]>([]);
  const [bills, setBills] = useState<any[]>([]);
  const [payments, setPayments] = useState<any[]>([]);
  const [error, setError] = useState('');

  const load = async () => {
    try {
      const [invoiceResponse, billResponse, paymentResponse] = await Promise.all([
        portal.myInvoices(),
        portal.myBills(),
        portal.myPayments(),
      ]);
      setInvoices(invoiceResponse.data || []);
      setBills(billResponse.data || []);
      setPayments(paymentResponse.data || []);
      setError('');
    } catch (value) {
      setError(err(value));
    }
  };

  useEffect(() => { load(); }, []);

  const payInvoice = async (invoice: any) => {
    const amount = window.prompt('Payment amount', String(Number(invoice.total) - Number(invoice.amount_paid || 0)));
    if (!amount || Number(amount) <= 0) return;
    try {
      await portal.pay({ sale_invoice_id: invoice.id, amount: Number(amount), receipt_date: new Date().toISOString().slice(0, 10) });
      await load();
    } catch (value) {
      setError(err(value));
    }
  };

  const payBill = async (bill: any) => {
    const amount = window.prompt('Payment amount', String(Number(bill.total) - Number(bill.amount_paid || 0)));
    if (!amount || Number(amount) <= 0) return;
    try {
      await portal.payBill({ purchase_bill_id: bill.id, amount: Number(amount), payment_date: new Date().toISOString().slice(0, 10) });
      await load();
    } catch (value) {
      setError(err(value));
    }
  };

  const canPay = (record: any) => ['posted', 'confirmed', 'partial', 'overdue'].includes(record.status)
    && Number(record.total) > Number(record.amount_paid || 0);

  return <>
    <PageHeader title="My Portal" subtitle="View your own invoices and bills, payment status and dues." />
    {error && <div className="error banner">{error}</div>}
    <div className="portal-grid">
      <div className="panel">
        <div className="panel-head"><h3><Receipt size={18} /> My Invoices</h3></div>
        {invoices.length ? <table><thead><tr><th>Invoice</th><th>Date</th><th>Total</th><th>Paid</th><th>Status</th><th /></tr></thead><tbody>
          {invoices.map((invoice) => <tr key={invoice.id}><td>{invoice.number}</td><td>{dateValue(invoice.invoice_date)}</td><td>{money(invoice.total)}</td><td>{money(invoice.amount_paid)}</td><td><Status value={invoice.status} /></td><td>{canPay(invoice) && <Button onClick={() => payInvoice(invoice)}>Pay</Button>}</td></tr>)}
        </tbody></table> : <Empty text="No invoices" />}
      </div>
      <div className="panel">
        <div className="panel-head"><h3><FileText size={18} /> My Bills</h3></div>
        {bills.length ? <table><thead><tr><th>Bill</th><th>Date</th><th>Total</th><th>Paid</th><th>Status</th><th /></tr></thead><tbody>
          {bills.map((bill) => <tr key={bill.id}><td>{bill.number}</td><td>{dateValue(bill.bill_date)}</td><td>{money(bill.total)}</td><td>{money(bill.amount_paid)}</td><td><Status value={bill.status} /></td><td>{canPay(bill) && <Button onClick={() => payBill(bill)}>Pay</Button>}</td></tr>)}
        </tbody></table> : <Empty text="No bills" />}
      </div>
    </div>
    <div className="panel"><h3>My Payments</h3>{payments.length ? <table><thead><tr><th>Number</th><th>Type</th><th>Date</th><th>Method</th><th>Amount</th></tr></thead><tbody>
      {payments.map((payment) => <tr key={`${payment.payment_type}-${payment.id}`}><td>{payment.number}</td><td><Status value={payment.payment_type} /></td><td>{dateValue(payment.payment_date)}</td><td>{payment.method}</td><td><b>{money(payment.amount)}</b></td></tr>)}
    </tbody></table> : <Empty text="No payments" />}</div>
  </>;
}
