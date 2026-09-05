import { useEffect, useState } from 'react';
import { dashboard, err } from '../api';
import { Button, PageHeader, money } from '../components/UI';
import { ArrowDownRight, ArrowUpRight, Receipt, ShoppingCart, CircleDollarSign, Plus } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const [d, setD] = useState<any>(null);
  const [e, setE] = useState('');
  const nav = useNavigate();

  useEffect(() => {
    dashboard()
      .then((r) => setD(r.data))
      .catch((x) => setE(err(x)));
  }, []);

  const cards = [
    ['Total Sales Orders', d?.sales?.all ?? 0, ShoppingCart],
    ['Confirmed Sales', d?.sales?.confirmed ?? 0, ShoppingCart],
    ['Total Purchases', d?.purchase?.all ?? 0, Receipt],
    ['Confirmed Purchases', d?.purchase?.confirmed ?? 0, Receipt],
    ['Total Budget', money(d?.budget?.budget ?? 0), ArrowDownRight],
    ['Achieved Spend', money(d?.budget?.achieved ?? 0), ArrowUpRight],
  ];

  return (
    <>
      <PageHeader title="Dashboard" subtitle="A live overview of sales, purchases, receivables and budgets." />
      <div className="quick-actions">
        <Button onClick={() => nav('/sales/orders')}>
          <Plus size={15} /> New Sales Order
        </Button>
        <Button onClick={() => nav('/purchase/orders')}>
          <Plus size={15} /> New Purchase Order
        </Button>
        <Button variant="secondary" onClick={() => nav('/sales/invoices')}>
          New Invoice
        </Button>
        <Button variant="secondary" onClick={() => nav('/purchase/bills')}>
          New Bill
        </Button>
        <Button variant="secondary" onClick={() => nav('/payments/new')}>
          Record Payment
        </Button>
      </div>
      {e && <div className="error banner">{e}</div>}
      <div className="stat-grid">
        {cards.map(([name, value, Icon]: any) => (
          <div className="stat-card" key={name}>
            <div className="stat-icon">
              <Icon size={18} />
            </div>
            <span>{name}</span>
            <strong>{value ?? '—'}</strong>
          </div>
        ))}
      </div>
      <div className="dashboard-grid">
        <div className="panel">
          <div className="panel-head">
            <div>
              <h3>Accounting flow</h3>
              <p>Master data feeds transactions, then journals and reports.</p>
            </div>
            <CircleDollarSign size={22} />
          </div>
          <div className="flow">
            <span>Masters</span>
            <i>→</i>
            <span>Orders</span>
            <i>→</i>
            <span>Invoices / Bills</span>
            <i>→</i>
            <span>Payments</span>
            <i>→</i>
            <span>Journal</span>
            <i>→</i>
            <span>Reports</span>
          </div>
        </div>
        <div className="panel">
          <h3>Workspace principles</h3>
          <ul>
            <li>Use master records in every transaction.</li>
            <li>Posted documents create accounting entries.</li>
            <li>Payments reduce receivables or payables.</li>
            <li>Reports are calculated from ledger activity.</li>
          </ul>
        </div>
      </div>
    </>
  );
}

