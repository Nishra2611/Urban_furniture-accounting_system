import { FormEvent, useEffect, useState, useMemo } from 'react';
import { users, err } from '../api';
import { useAuth } from '../context/AuthContext';
import { Button, Field, PageHeader, Status, Toolbar, Empty } from '../components/UI';
import { Trash2 } from 'lucide-react';
import type { User } from '../types/api';

export default function Admin() {
  const { user: currentUser } = useAuth();
  const [rows, setRows] = useState<User[]>([]);
  const [form, setForm] = useState(false);
  const [q, setQ] = useState('');
  const [error, setError] = useState('');
  const [selectedIds, setSelectedIds] = useState<Set<number | string>>(new Set());
  const [confirmModal, setConfirmModal] = useState<{
    title: string;
    message: string;
    confirmText: string;
    isDanger?: boolean;
    onConfirm: () => Promise<void>;
  } | null>(null);

  const load = () => {
    users.list().then((r) => setRows(r.data)).catch((x) => setError(err(x)));
  };

  useEffect(() => {
    setSelectedIds(new Set());
    load();
  }, []);

  const filtered = useMemo(() => {
    return rows.filter((x) => JSON.stringify(x).toLowerCase().includes(q.toLowerCase()));
  }, [rows, q]);

  const toggleSelectAll = () => {
    if (selectedIds.size === filtered.length) {
      setSelectedIds(new Set());
    } else {
      const all = new Set(filtered.map((u) => u.id));
      setSelectedIds(all);
    }
  };

  const toggleSelectRow = (id: number | string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedIds((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  };


  const promptDeleteUser = (u: User, e: React.MouseEvent) => {
    e.stopPropagation();
    if (currentUser && u.id === currentUser.id) {
      alert("You cannot delete your own account.");
      return;
    }
    setConfirmModal({
      title: `Delete User ${u.name}?`,
      message: `Are you sure you want to permanently delete user "${u.name}" (${u.login_id})?`,
      confirmText: 'Delete User',
      isDanger: true,
      onConfirm: async () => {
        try {
          await users.delete(u.id);
          setSelectedIds((prev) => {
            const n = new Set(prev);
            n.delete(u.id);
            return n;
          });
          load();
        } catch (errVal) {
          setError(err(errVal));
        }
      },
    });
  };

  const promptBulkDelete = () => {
    const validIds = Array.from(selectedIds).filter((id) => !currentUser || id !== currentUser.id);
    if (validIds.length === 0) {
      alert("No valid users selected (you cannot delete yourself).");
      return;
    }
    setConfirmModal({
      title: `Delete ${validIds.length} Selected User(s)?`,
      message: `Are you sure you want to PERMANENTLY DELETE ${validIds.length} selected user account(s)?`,
      confirmText: 'Delete Selected',
      isDanger: true,
      onConfirm: async () => {
        try {
          await users.bulkDelete(validIds);
          setSelectedIds(new Set());
          load();
        } catch (errVal) {
          setError(err(errVal));
        }
      },
    });
  };

  if (form) return <UserForm onDone={() => { setForm(false); load(); }} />;

  return (
    <>
      <PageHeader
        title="Users & Access"
        subtitle="Create and manage application users and their roles."
        action={<Button onClick={() => setForm(true)}>＋ Create User</Button>}
      />
      <Toolbar search={q} onSearch={setQ} refresh={load} />

      {error && <div className="error banner" style={{ marginBottom: 14 }}>{error}</div>}

      {selectedIds.size > 0 && (
        <div className="bulk-action-bar">
          <span>{selectedIds.size} user(s) selected</span>
          <Button variant="danger" onClick={promptBulkDelete}>
            Delete Selected
          </Button>
          <Button variant="ghost" onClick={() => setSelectedIds(new Set())}>
            Deselect All
          </Button>
        </div>
      )}

      <div className="table-card">
        {filtered.length === 0 ? (
          <Empty text="No users found" />
        ) : (
          <table>
            <thead>
              <tr>
                <th style={{ width: 40, textAlign: 'center' }}>
                  <input
                    type="checkbox"
                    checked={filtered.length > 0 && selectedIds.size === filtered.length}
                    onChange={toggleSelectAll}
                  />
                </th>
                <th>Name</th>
                <th>Login Id</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((u) => (
                <tr key={u.id}>
                  <td style={{ textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selectedIds.has(u.id)}
                      onChange={(e) => toggleSelectRow(u.id, e as any)}
                    />
                  </td>
                  <td><b>{u.name}</b></td>
                  <td>{u.login_id}</td>
                  <td>{u.email}</td>
                  <td>{u.role}</td>
                  <td><Status value={u.is_active ? 'Active' : 'Inactive'} /></td>
                  <td style={{ textAlign: 'right' }}>
                    {currentUser && u.id === currentUser.id ? (
                      <span className="protected-badge">Current User</span>
                    ) : (
                      <button
                        type="button"
                        className="icon-btn small danger"
                        title="Delete User"
                        style={{ color: '#ef4444' }}
                        onClick={(e) => promptDeleteUser(u, e)}
                      >
                        <Trash2 size={15} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {confirmModal && (
        <div className="modal-overlay" onClick={() => setConfirmModal(null)}>
          <div className="confirmation-modal" onClick={(e) => e.stopPropagation()}>
            <h3>{confirmModal.title}</h3>
            <p>{confirmModal.message}</p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end', marginTop: 24 }}>
              <Button variant="secondary" onClick={() => setConfirmModal(null)}>
                Cancel
              </Button>
              <Button
                variant={confirmModal.isDanger ? 'danger' : 'primary'}
                onClick={async () => {
                  await confirmModal.onConfirm();
                  setConfirmModal(null);
                }}
              >
                {confirmModal.confirmText}
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function UserForm({ onDone }: { onDone: () => void }) {
  const [f, setF] = useState<any>({ name: '', login_id: '', email: '', role: 'Accountant', password: '', re_enter_password: '' });
  const [e, setE] = useState('');

  const submit = async (x: FormEvent) => {
    x.preventDefault();
    if (f.password !== f.re_enter_password) return setE('Passwords do not match');
    try {
      const payload = { name: f.name, login_id: f.login_id, email: f.email, role: f.role, password: f.password, re_password: f.re_enter_password || f.password };
      await users.create(payload);
      onDone();
    } catch (x) {
      setE(err(x));
    }
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="form-modal">
        <PageHeader title="Create User" subtitle="Administrator can create Accountant or Contact User accounts." back={onDone} />
        <form className="record-form" onSubmit={submit}>
          <div className="form-grid">
            <Field label="Name" required><input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
            <Field label="Login Id" required><input minLength={6} maxLength={12} value={f.login_id} onChange={(e) => setF({ ...f, login_id: e.target.value })} /></Field>
            <Field label="Email Id" required><input type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></Field>
            <Field label="Role" required>
              <select value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}>
                <option value="User">Contact User</option>
                <option value="Accountant">Accountant</option>
              </select>
            </Field>
            <Field label="Password" required><input type="password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} /></Field>
            <Field label="Re-enter Password" required><input type="password" value={f.re_enter_password} onChange={(e) => setF({ ...f, re_enter_password: e.target.value })} /></Field>
          </div>
          {e && <div className="error">{e}</div>}
          <div className="form-actions">
            <Button type="submit">CREATE</Button>
            <Button type="button" variant="secondary" onClick={onDone}>CANCEL</Button>
          </div>
        </form>
      </div>
    </div>
  );
}
