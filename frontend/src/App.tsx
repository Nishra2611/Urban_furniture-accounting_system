import {Navigate,Route,Routes} from 'react-router-dom';import {useAuth} from './context/AuthContext';import Layout from './components/Layout';import {Login,Signup,Forgot,Reset} from './pages/Auth';import Dashboard from './pages/Dashboard';import {Contacts,Products,Taxes,Accounts,Journals,Analytics,Budgets} from './pages/Masters';import {Documents,Payments,PaymentForm} from './pages/Transactions';import {JournalEntries} from './pages/Accounting';import {ProfitLoss,BalanceSheet,BudgetReport,Ledger} from './pages/Reports';import Admin from './pages/Admin';import Portal from './pages/Portal';
const normalizeRole = (role?: string) => {
  if (!role) return '';
  const r = role.toLowerCase();
  if (r === 'administrator' || r === 'admin') return 'admin';
  if (r === 'accountant') return 'accountant';
  if (r === 'user') return 'user';
  return r;
};

function Guard({ children, roles }: { children: any; roles?: string[] }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading-screen">Loading workspace…</div>;
  if (!user) return <Navigate to="/login" replace />;

  const userRole = normalizeRole(user.role);

  if (roles && !roles.includes(userRole)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

export default function App() {
  const defaultHome = '/dashboard';

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/forgot-password" element={<Forgot />} />
      <Route path="/reset-password" element={<Reset />} />
      <Route element={<Guard><Layout /></Guard>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/portal" element={<Portal />} />
        <Route path="/masters/contacts" element={<Contacts />} />
        <Route path="/masters/products" element={<Products />} />
        <Route path="/masters/accounts" element={<Accounts />} />
        <Route path="/masters/journals" element={<Journals />} />
        <Route path="/masters/analytics" element={<Analytics />} />
        <Route path="/masters/budgets" element={<Budgets />} />
        <Route path="/sales/orders" element={<Documents kind="salesOrders" />} />
        <Route path="/sales/invoices" element={<Documents kind="invoices" />} />
        <Route path="/purchase/orders" element={<Documents kind="purchaseOrders" />} />
        <Route path="/purchase/bills" element={<Documents kind="bills" />} />
        <Route path="/payments/customer" element={<Payments type="customer" />} />
        <Route path="/payments/vendor" element={<Payments type="vendor" />} />
        <Route path="/payments/new" element={<PaymentForm />} />
        <Route path="/accounting/entries" element={<JournalEntries />} />
        <Route path="/reports/pl" element={<ProfitLoss />} />
        <Route path="/reports/bs" element={<BalanceSheet />} />
        <Route path="/reports/budget" element={<BudgetReport />} />
        <Route path="/reports/ledger" element={<Ledger />} />
        <Route path="/admin/users" element={<Guard roles={['admin']}><Admin /></Guard>} />
      </Route>
      <Route path="/" element={<Navigate to={defaultHome} replace />} />
      <Route path="*" element={<Navigate to={defaultHome} replace />} />
    </Routes>
  );
}

