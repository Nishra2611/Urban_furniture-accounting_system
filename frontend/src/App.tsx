import {Navigate,Route,Routes} from 'react-router-dom';import {useAuth} from './context/AuthContext';import Layout from './components/Layout';import {Login,Signup,Forgot,Reset} from './pages/Auth';import Dashboard from './pages/Dashboard';import {Contacts,Products,Taxes,Accounts,Journals,Analytics,Budgets} from './pages/Masters';import {Documents,Payments,PaymentForm} from './pages/Transactions';import {JournalEntries} from './pages/Accounting';import {ProfitLoss,BalanceSheet,BudgetReport,Ledger} from './pages/Reports';import Admin from './pages/Admin';import {UserDashboard,UserDocuments,UserPayments,UserProfile,ChangePassword,UserWorkspaceDetail} from './pages/UserWorkspace';
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
    return <Navigate to={userRole === 'user' ? '/portal' : '/dashboard'} replace />;
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
        <Route path="/dashboard" element={<Guard roles={['accountant','admin']}><Dashboard /></Guard>} />
        <Route path="/portal" element={<Guard roles={['user']}><UserDashboard /></Guard>} />
        <Route path="/user/dashboard" element={<Guard roles={['user']}><UserDashboard /></Guard>} />
        <Route path="/user/invoices" element={<Guard roles={['user']}><UserDocuments type="invoice" /></Guard>} />
        <Route path="/user/bills" element={<Guard roles={['user']}><UserDocuments type="bill" /></Guard>} />
        <Route path="/user/payments" element={<Guard roles={['user']}><UserPayments /></Guard>} />
        <Route path="/user/invoices/:id" element={<Guard roles={['user']}><UserWorkspaceDetail type="invoice" /></Guard>} />
        <Route path="/user/bills/:id" element={<Guard roles={['user']}><UserWorkspaceDetail type="bill" /></Guard>} />
        <Route path="/user/profile" element={<Guard roles={['user']}><UserProfile /></Guard>} />
        <Route path="/user/password" element={<Guard roles={['user']}><ChangePassword /></Guard>} />
        <Route path="/masters/contacts" element={<Guard roles={['accountant','admin']}><Contacts /></Guard>} />
        <Route path="/masters/products" element={<Guard roles={['accountant','admin']}><Products /></Guard>} />
        <Route path="/masters/accounts" element={<Guard roles={['accountant','admin']}><Accounts /></Guard>} />
        <Route path="/masters/journals" element={<Guard roles={['accountant','admin']}><Journals /></Guard>} />
        <Route path="/masters/analytics" element={<Guard roles={['accountant','admin']}><Analytics /></Guard>} />
        <Route path="/masters/budgets" element={<Guard roles={['accountant','admin']}><Budgets /></Guard>} />
        <Route path="/sales/orders" element={<Guard roles={['accountant','admin']}><Documents kind="salesOrders" /></Guard>} />
        <Route path="/sales/invoices" element={<Guard roles={['accountant','admin']}><Documents kind="invoices" /></Guard>} />
        <Route path="/purchase/orders" element={<Guard roles={['accountant','admin']}><Documents kind="purchaseOrders" /></Guard>} />
        <Route path="/purchase/bills" element={<Guard roles={['accountant','admin']}><Documents kind="bills" /></Guard>} />
        <Route path="/payments/customer" element={<Guard roles={['accountant','admin']}><Payments type="customer" /></Guard>} />
        <Route path="/payments/vendor" element={<Guard roles={['accountant','admin']}><Payments type="vendor" /></Guard>} />
        <Route path="/payments/new" element={<Guard roles={['accountant','admin']}><PaymentForm /></Guard>} />
        <Route path="/accounting/entries" element={<Guard roles={['accountant','admin']}><JournalEntries /></Guard>} />
        <Route path="/reports/pl" element={<Guard roles={['accountant','admin']}><ProfitLoss /></Guard>} />
        <Route path="/reports/bs" element={<Guard roles={['accountant','admin']}><BalanceSheet /></Guard>} />
        <Route path="/reports/budget" element={<Guard roles={['accountant','admin']}><BudgetReport /></Guard>} />
        <Route path="/reports/ledger" element={<Guard roles={['accountant','admin']}><Ledger /></Guard>} />
        <Route path="/admin/users" element={<Guard roles={['admin']}><Admin /></Guard>} />
      </Route>
      <Route path="/" element={<Navigate to={defaultHome} replace />} />
      <Route path="*" element={<Navigate to={defaultHome} replace />} />
    </Routes>
  );
}

