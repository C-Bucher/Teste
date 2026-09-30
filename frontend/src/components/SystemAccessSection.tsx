import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import api from '../api';
import { useToast } from '../context/ToastContext';

interface SystemUser {
  id: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
}

const ROLE_LABELS: Record<string, string> = {
  ADMIN: 'Administrador',
  GERENTE: 'Gerente',
  FUNCIONARIO: 'Funcionário',
};

export default function SystemAccessSection() {
  const toast = useToast();
  const [users, setUsers] = useState<SystemUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ full_name: '', email: '', password: '', role: 'FUNCIONARIO' });

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await api.get('/auth/users');
      setUsers(res.data);
    } catch (err) {
      console.error('Erro ao carregar acessos', err);
      toast.error('Erro ao carregar acessos.');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (user: SystemUser) => {
    try {
      await api.put(`/auth/users/${user.id}`, { is_active: !user.is_active });
      toast.success(user.is_active ? 'Acesso desativado.' : 'Acesso reativado.');
      await fetchUsers();
    } catch (err: unknown) {
      toast.error(axios.isAxiosError(err) ? err.response?.data?.detail || 'Erro ao alterar o acesso.' : 'Erro ao alterar o acesso.');
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post('/auth/users', form);
      toast.success('Acesso criado com sucesso.');
      setIsModalOpen(false);
      setForm({ full_name: '', email: '', password: '', role: 'FUNCIONARIO' });
      fetchUsers();
    } catch (err: unknown) {
      console.error('Erro ao criar acesso', err);
      toast.error(axios.isAxiosError(err) ? err.response?.data?.detail || 'Erro ao criar acesso.' : 'Erro ao criar acesso.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="glass-card p-lg rounded-2xl mb-xl">
      <div className="flex justify-between items-center mb-lg">
        <div>
          <h3 className="font-headline-sm text-headline-sm text-on-surface">Acessos ao Sistema</h3>
          <p className="text-on-surface-variant text-body-sm mt-xs">Contas de login da sua empresa e o cargo de cada uma.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10"
        >
          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>person_add</span>
          Adicionar Acesso
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-lg">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="glass-panel bg-surface/60 border border-border-subtle rounded-xl overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-highest/30 border-b border-border-subtle">
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Nome</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">E-mail</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Cargo</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Status</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle/50">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-surface-bright/40 transition-colors">
                  <td className="px-lg py-md text-label-md text-on-surface">{u.full_name}</td>
                  <td className="px-lg py-md text-label-md text-on-surface-variant">{u.email}</td>
                  <td className="px-lg py-md">
                    <span className="px-sm py-0.5 rounded-full text-[11px] font-bold bg-surface-container-highest text-on-surface-variant uppercase tracking-wider">
                      {ROLE_LABELS[u.role] || u.role}
                    </span>
                  </td>
                  <td className="px-lg py-md text-label-md text-on-surface-variant">{u.is_active ? 'Ativo' : 'Inativo'}</td>
                  <td className="px-lg py-md text-right">
                    {u.role !== 'ADMIN' && (
                      <button onClick={() => handleToggleActive(u)} className="text-primary hover:underline text-label-md">
                        {u.is_active ? 'Desativar' : 'Reativar'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[440px]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">Novo Acesso</h3>
                <button onClick={() => setIsModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>
              <form onSubmit={handleCreate} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Nome Completo</label>
                  <input required type="text" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">E-mail</label>
                  <input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Senha</label>
                  <input required type="password" minLength={8} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                  <p className="text-label-sm text-on-surface-variant mt-1">Mínimo de 8 caracteres, com letras e números.</p>
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Cargo</label>
                  <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none">
                    <option value="GERENTE">Gerente</option>
                    <option value="FUNCIONARIO">Funcionário</option>
                  </select>
                </div>
                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">Cancelar</button>
                  <button type="submit" disabled={saving} className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                    {saving ? 'Criando...' : 'Criar Acesso'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
