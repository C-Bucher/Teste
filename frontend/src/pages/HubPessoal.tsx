import { useState, useEffect } from 'react';
import api from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import Layout from '../components/Layout';

// ---------------------------------------------------------------------------
// Tab definitions. This exact list is shared with Tasks 13-17, which each
// replace exactly one placeholder `case` below with real content. Do not
// rename ids — future tasks match on these strings.
// ---------------------------------------------------------------------------
const TABS = [
  { id: 'visao-geral', label: 'Visão Geral', icon: 'dashboard' },
  { id: 'extrato', label: 'Extrato', icon: 'receipt_long' },
  { id: 'contas-cartoes', label: 'Contas & Cartões', icon: 'credit_card' },
  { id: 'orcamento', label: 'Orçamento', icon: 'pie_chart' },
  { id: 'metas', label: 'Metas', icon: 'flag' },
  { id: 'dividas', label: 'Dívidas', icon: 'account_balance' },
  { id: 'assinaturas', label: 'Assinaturas', icon: 'subscriptions' },
  { id: 'divisao', label: 'Divisão de Despesas', icon: 'groups' },
  { id: 'analitico', label: 'Analítico', icon: 'analytics' },
  { id: 'timeboxes-okrs', label: 'Timeboxes & OKRs', icon: 'schedule' },
  { id: 'cfo-pessoal', label: 'CFO Pessoal IA', icon: 'auto_awesome' },
] as const;

type TabId = (typeof TABS)[number]['id'];

interface PersonalEntry {
  id: string;
  type: 'RECEITA' | 'DESPESA';
  amount: number;
  description: string;
  date: string;
  category?: string;
}

interface DashboardData {
  saldo: number;
  receitas_mes: number;
  despesas_mes: number;
  recent_entries: PersonalEntry[];
}

interface PersonalCategory {
  id: string;
  name: string;
  type: 'RECEITA' | 'DESPESA';
}

interface PersonalAccount {
  id: string;
  name: string;
  type: 'CONTA' | 'CARTAO';
  balance: number;
  limit?: number | null;
  closing_day?: number | null;
  due_day?: number | null;
}

interface PersonalBudget {
  id: string;
  category: string;
  limit_amount: number;
  spent_amount: number;
}

const formatCurrency = (value: number | undefined | null) =>
  (value ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 });

const formatDate = (value: string | null | undefined) => {
  if (!value) return '-';
  const [y, m, d] = value.split('-');
  if (!y || !m || !d) return value;
  return `${d}/${m}/${y}`;
};

const EMPTY_ENTRY_FORM = {
  type: 'RECEITA' as 'RECEITA' | 'DESPESA',
  amount: '',
  description: '',
  category: '',
};

const EMPTY_ACCOUNT_FORM = {
  name: '',
  type: 'CONTA' as 'CONTA' | 'CARTAO',
  balance: '',
  limit: '',
  closing_day: '',
  due_day: '',
};

const EMPTY_BUDGET_FORM = {
  category: '',
  limit_amount: '',
};

export default function HubPessoal() {
  // Note: no role guard here on purpose — Hub Pessoal is reachable by every
  // authenticated user regardless of role. Access is gated at the nav level
  // in Layout.tsx by `plan_scope`, not by role.

  const [activeTab, setActiveTab] = useState<TabId>('visao-geral');

  // Visão Geral
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(true);

  // Extrato
  const [entries, setEntries] = useState<PersonalEntry[]>([]);
  const [entriesLoading, setEntriesLoading] = useState(true);
  const [categories, setCategories] = useState<PersonalCategory[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [entryForm, setEntryForm] = useState(EMPTY_ENTRY_FORM);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Contas & Cartões
  const [accounts, setAccounts] = useState<PersonalAccount[]>([]);
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [isAccountModalOpen, setIsAccountModalOpen] = useState(false);
  const [accountForm, setAccountForm] = useState(EMPTY_ACCOUNT_FORM);
  const [savingAccount, setSavingAccount] = useState(false);
  const [deletingAccountId, setDeletingAccountId] = useState<string | null>(null);

  // Orçamento
  const [budgets, setBudgets] = useState<PersonalBudget[]>([]);
  const [budgetsLoading, setBudgetsLoading] = useState(true);
  const [isBudgetModalOpen, setIsBudgetModalOpen] = useState(false);
  const [budgetForm, setBudgetForm] = useState(EMPTY_BUDGET_FORM);
  const [savingBudget, setSavingBudget] = useState(false);
  const [deletingBudgetId, setDeletingBudgetId] = useState<string | null>(null);

  const fetchDashboard = async () => {
    setDashboardLoading(true);
    try {
      const res = await api.get('/personal/dashboard');
      setDashboard(res.data);
    } catch (err) {
      console.error('Erro ao carregar visão geral pessoal', err);
    } finally {
      setDashboardLoading(false);
    }
  };

  const fetchEntries = async () => {
    setEntriesLoading(true);
    try {
      const res = await api.get('/personal/entries');
      setEntries(res.data.items || []);
    } catch (err) {
      console.error('Erro ao carregar extrato pessoal', err);
    } finally {
      setEntriesLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const res = await api.get('/personal/categories');
      setCategories(res.data || []);
    } catch (err) {
      console.error('Erro ao carregar categorias pessoais', err);
    }
  };

  const fetchAccounts = async () => {
    setAccountsLoading(true);
    try {
      const res = await api.get('/personal/accounts');
      setAccounts(res.data || []);
    } catch (err) {
      console.error('Erro ao carregar contas e cartões', err);
    } finally {
      setAccountsLoading(false);
    }
  };

  const fetchBudgets = async () => {
    setBudgetsLoading(true);
    try {
      const res = await api.get('/personal/budgets');
      setBudgets(res.data || []);
    } catch (err) {
      console.error('Erro ao carregar orçamentos', err);
    } finally {
      setBudgetsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
    fetchEntries();
    fetchCategories();
    fetchAccounts();
    fetchBudgets();
  }, []);

  // Re-fetch the dashboard whenever the user comes back to "Visão Geral" so
  // the saldo/receitas/despesas reflect any entries created in "Extrato".
  useEffect(() => {
    if (activeTab === 'visao-geral') {
      fetchDashboard();
    }
  }, [activeTab]);

  const handleAddNew = () => {
    setEntryForm(EMPTY_ENTRY_FORM);
    setIsModalOpen(true);
  };

  const handleSaveEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post('/personal/entries', {
        type: entryForm.type,
        amount: Number(entryForm.amount),
        description: entryForm.description,
        category: entryForm.category,
      });
      setIsModalOpen(false);
      await fetchEntries();
      await fetchDashboard();
    } catch (err) {
      console.error('Erro ao criar lançamento pessoal', err);
      alert('Erro ao criar lançamento');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteEntry = async (id: string) => {
    if (!confirm('Deseja realmente excluir este lançamento?')) return;
    setDeletingId(id);
    try {
      await api.delete(`/personal/entries/${id}`);
      setEntries((prev) => prev.filter((en) => en.id !== id));
      await fetchDashboard();
    } catch (err) {
      console.error('Erro ao excluir lançamento pessoal', err);
      alert('Erro ao excluir lançamento');
    } finally {
      setDeletingId(null);
    }
  };

  const handleAddAccount = () => {
    setAccountForm(EMPTY_ACCOUNT_FORM);
    setIsAccountModalOpen(true);
  };

  const handleSaveAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingAccount(true);
    try {
      const payload: Record<string, unknown> = {
        name: accountForm.name,
        type: accountForm.type,
        balance: Number(accountForm.balance || 0),
      };
      if (accountForm.type === 'CARTAO') {
        payload.limit = Number(accountForm.limit || 0);
        payload.closing_day = Number(accountForm.closing_day || 0);
        payload.due_day = Number(accountForm.due_day || 0);
      }
      await api.post('/personal/accounts', payload);
      setIsAccountModalOpen(false);
      await fetchAccounts();
    } catch (err) {
      console.error('Erro ao criar conta/cartão', err);
      alert('Erro ao criar conta/cartão');
    } finally {
      setSavingAccount(false);
    }
  };

  const handleDeleteAccount = async (id: string) => {
    if (!confirm('Deseja realmente excluir esta conta/cartão?')) return;
    setDeletingAccountId(id);
    try {
      await api.delete(`/personal/accounts/${id}`);
      setAccounts((prev) => prev.filter((a) => a.id !== id));
    } catch (err) {
      console.error('Erro ao excluir conta/cartão', err);
      alert('Erro ao excluir conta/cartão');
    } finally {
      setDeletingAccountId(null);
    }
  };

  const handleAddBudget = () => {
    setBudgetForm(EMPTY_BUDGET_FORM);
    setIsBudgetModalOpen(true);
  };

  const handleSaveBudget = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingBudget(true);
    try {
      await api.post('/personal/budgets', {
        category: budgetForm.category,
        limit_amount: Number(budgetForm.limit_amount || 0),
      });
      setIsBudgetModalOpen(false);
      await fetchBudgets();
    } catch (err) {
      console.error('Erro ao criar orçamento', err);
      alert('Erro ao criar orçamento');
    } finally {
      setSavingBudget(false);
    }
  };

  const handleDeleteBudget = async (id: string) => {
    if (!confirm('Deseja realmente excluir este orçamento?')) return;
    setDeletingBudgetId(id);
    try {
      await api.delete(`/personal/budgets/${id}`);
      setBudgets((prev) => prev.filter((b) => b.id !== id));
    } catch (err) {
      console.error('Erro ao excluir orçamento', err);
      alert('Erro ao excluir orçamento');
    } finally {
      setDeletingBudgetId(null);
    }
  };

  const categoryOptions = categories.filter((c) => c.type === entryForm.type);

  // The backend returns `recent_entries` in insertion order (oldest first),
  // not pre-sorted by recency, so sort by date descending client-side before
  // taking the top 5.
  const recentEntries = [...(dashboard?.recent_entries || [])]
    .sort((a, b) => (b.date || '').localeCompare(a.date || ''))
    .slice(0, 5);

  return (
    <Layout>
      {/* Page Header */}
      <div className="mb-xl">
        <nav className="flex text-body-sm text-outline mb-xs gap-xs items-center">
          <span>Pessoal</span>
          <span className="material-symbols-outlined text-[12px]">chevron_right</span>
          <span className="text-primary">Hub Pessoal</span>
        </nav>
        <h2 className="font-display-lg text-display-lg text-on-surface">Hub Pessoal</h2>
        <p className="text-on-surface-variant text-body-base mt-xs">
          Organize suas finanças pessoais: extrato, orçamento, metas, dívidas e muito mais.
        </p>
      </div>

      {/* Tab bar — pill style, horizontal scroll for overflow (11 tabs) */}
      <div className="flex overflow-x-auto bg-surface-container-low p-1 rounded-lg border border-border-subtle mb-xl gap-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-sm px-lg py-2 rounded-md transition-all font-label-md text-label-md whitespace-nowrap shrink-0 ${
              activeTab === tab.id
                ? 'bg-primary-container text-on-primary-container'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* -----------------------------------------------------------------
          Tab content. One case per tab id — this switch is the structure
          Tasks 13-17 will extend. Each future task should replace exactly
          one `case` below (see the TODO comment above each placeholder)
          with real content, leaving the others untouched.
      ----------------------------------------------------------------- */}
      {(() => {
        switch (activeTab) {
          // ---------------------------------------------------------------
          case 'visao-geral': {
            if (dashboardLoading) {
              return (
                <div className="flex justify-center py-xl">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              );
            }
            return (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-lg">
                {/* KPI cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-lg">
                  <div className="glass-card p-lg rounded-xl">
                    <span className="text-on-surface-variant font-label-md">Saldo</span>
                    <h3
                      className={`font-display-lg text-display-lg mt-sm ${
                        (dashboard?.saldo ?? 0) >= 0 ? 'text-on-surface' : 'text-error'
                      }`}
                    >
                      R$ {formatCurrency(dashboard?.saldo)}
                    </h3>
                  </div>
                  <div className="glass-card p-lg rounded-xl">
                    <span className="text-on-surface-variant font-label-md">Receitas do Mês</span>
                    <h3 className="font-display-lg text-display-lg text-success mt-sm">
                      R$ {formatCurrency(dashboard?.receitas_mes)}
                    </h3>
                  </div>
                  <div className="glass-card p-lg rounded-xl">
                    <span className="text-on-surface-variant font-label-md">Despesas do Mês</span>
                    <h3 className="font-display-lg text-display-lg text-error mt-sm">
                      R$ {formatCurrency(dashboard?.despesas_mes)}
                    </h3>
                  </div>
                </div>

                {/* Recent entries */}
                <div className="glass-card rounded-xl overflow-hidden">
                  <div className="p-lg flex justify-between items-center border-b border-border-subtle">
                    <h4 className="font-headline-sm text-headline-sm">Lançamentos Recentes</h4>
                    <button onClick={() => setActiveTab('extrato')} className="text-primary font-label-md hover:underline">
                      Ver extrato completo
                    </button>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-surface-container-low/50">
                          <th className="p-md font-label-md text-on-surface-variant border-b border-border-subtle">Descrição</th>
                          <th className="p-md font-label-md text-on-surface-variant border-b border-border-subtle">Categoria</th>
                          <th className="p-md font-label-md text-on-surface-variant border-b border-border-subtle">Data</th>
                          <th className="p-md font-label-md text-on-surface-variant border-b border-border-subtle text-right">Valor</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border-subtle">
                        {recentEntries.map((entry) => (
                          <tr key={entry.id} className="hover:bg-surface-bright transition-colors">
                            <td className="p-md">
                              <div className="flex items-center gap-sm">
                                <div className="w-8 h-8 rounded bg-surface-container-highest flex items-center justify-center">
                                  <span className="material-symbols-outlined text-[18px]">
                                    {entry.type === 'RECEITA' ? 'trending_up' : 'trending_down'}
                                  </span>
                                </div>
                                <span className="font-body-sm font-medium">{entry.description}</span>
                              </div>
                            </td>
                            <td className="p-md"><span className="text-body-sm text-on-surface-variant">{entry.category || '-'}</span></td>
                            <td className="p-md"><span className="text-body-sm text-on-surface-variant">{formatDate(entry.date)}</span></td>
                            <td className={`p-md text-right font-bold ${entry.type === 'RECEITA' ? 'text-success' : 'text-error'}`}>
                              {entry.type === 'RECEITA' ? '+' : '-'} R$ {formatCurrency(entry.amount)}
                            </td>
                          </tr>
                        ))}
                        {recentEntries.length === 0 && (
                          <tr>
                            <td colSpan={4} className="py-12 text-center text-on-surface-variant">
                              Nenhum lançamento registrado ainda.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </motion.div>
            );
          }

          // ---------------------------------------------------------------
          case 'extrato':
            return (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                <div className="flex justify-end items-center mb-lg">
                  <button
                    onClick={handleAddNew}
                    className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10"
                  >
                    <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>add</span>
                    Novo Lançamento
                  </button>
                </div>

                <div className="glass-panel bg-surface/60 border border-border-subtle rounded-xl overflow-hidden">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-surface-container-highest/30 border-b border-border-subtle">
                        <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Descrição</th>
                        <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Categoria</th>
                        <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Data</th>
                        <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Tipo</th>
                        <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant text-right">Valor</th>
                        <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant text-right">Ações</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border-subtle/50">
                      {entries.map((en, i) => (
                        <motion.tr
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.03 }}
                          key={en.id}
                          className="group hover:bg-surface-bright/40 transition-colors"
                        >
                          <td className="px-lg py-md text-label-md text-on-surface">{en.description}</td>
                          <td className="px-lg py-md">
                            <span className="inline-flex items-center px-2 py-1 rounded-full bg-secondary-container/40 text-on-surface-variant text-[11px] font-bold uppercase tracking-wider">
                              {en.category || '-'}
                            </span>
                          </td>
                          <td className="px-lg py-md text-on-surface-variant font-label-md text-label-md">{formatDate(en.date)}</td>
                          <td className="px-lg py-md">
                            <span
                              className={`inline-flex items-center gap-xs px-2 py-1 rounded-full ${
                                en.type === 'RECEITA' ? 'bg-success/10 text-success' : 'bg-error/10 text-error'
                              } text-[11px] font-bold uppercase tracking-wider`}
                            >
                              <span className={`w-1.5 h-1.5 rounded-full ${en.type === 'RECEITA' ? 'bg-success' : 'bg-error'}`}></span>
                              {en.type === 'RECEITA' ? 'Receita' : 'Despesa'}
                            </span>
                          </td>
                          <td className={`px-lg py-md text-right font-bold ${en.type === 'RECEITA' ? 'text-success' : 'text-error'}`}>
                            {en.type === 'RECEITA' ? '+' : '-'} R$ {formatCurrency(en.amount)}
                          </td>
                          <td className="px-lg py-md text-right">
                            <button
                              onClick={() => handleDeleteEntry(en.id)}
                              disabled={deletingId === en.id}
                              className="p-2 rounded-lg bg-surface-container hover:bg-error-container/20 text-on-surface-variant hover:text-error transition-all disabled:opacity-50"
                              title="Excluir lançamento"
                            >
                              <span className="material-symbols-outlined text-sm">delete</span>
                            </button>
                          </td>
                        </motion.tr>
                      ))}
                      {!entriesLoading && entries.length === 0 && (
                        <tr>
                          <td colSpan={6} className="py-12 text-center text-on-surface-variant">
                            Nenhum lançamento encontrado.
                          </td>
                        </tr>
                      )}
                      {entriesLoading && (
                        <tr>
                          <td colSpan={6} className="py-12 text-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            );

          // ---------------------------------------------------------------
          case 'contas-cartoes':
            return (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                <div className="flex justify-end items-center mb-lg">
                  <button
                    onClick={handleAddAccount}
                    className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10"
                  >
                    <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>add</span>
                    Nova Conta/Cartão
                  </button>
                </div>

                {accountsLoading ? (
                  <div className="flex justify-center py-xl">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-lg">
                    {accounts.map((acc) => {
                      const isCard = acc.type === 'CARTAO';
                      const usagePct =
                        isCard && acc.limit ? Math.min((Math.abs(acc.balance) / acc.limit) * 100, 100) : 0;
                      return (
                        <div key={acc.id} className="glass-card p-lg rounded-xl relative group">
                          <button
                            onClick={() => handleDeleteAccount(acc.id)}
                            disabled={deletingAccountId === acc.id}
                            className="absolute top-md right-md p-2 rounded-lg bg-surface-container hover:bg-error-container/20 text-on-surface-variant hover:text-error transition-all opacity-0 group-hover:opacity-100 disabled:opacity-50"
                            title="Remover"
                          >
                            <span className="material-symbols-outlined text-sm">delete</span>
                          </button>

                          <div className="flex items-center gap-sm mb-md">
                            <div className="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center">
                              <span className="material-symbols-outlined text-[20px]">
                                {isCard ? 'credit_card' : 'account_balance'}
                              </span>
                            </div>
                            <div>
                              <h4 className="font-headline-sm text-headline-sm text-on-surface">{acc.name}</h4>
                              <span className="text-body-sm text-on-surface-variant">
                                {isCard ? 'Cartão de Crédito' : 'Conta'}
                              </span>
                            </div>
                          </div>

                          <div className="mb-sm">
                            <span className="text-on-surface-variant font-label-md text-label-md">
                              {isCard ? 'Fatura atual' : 'Saldo'}
                            </span>
                            <h3
                              className={`font-display-sm text-display-sm mt-1 ${
                                acc.balance >= 0 ? 'text-on-surface' : 'text-error'
                              }`}
                            >
                              R$ {formatCurrency(acc.balance)}
                            </h3>
                          </div>

                          {isCard && (
                            <div className="mt-md space-y-sm">
                              <div className="flex justify-between text-body-sm text-on-surface-variant">
                                <span>Limite usado</span>
                                <span>
                                  {usagePct.toFixed(0)}% de R$ {formatCurrency(acc.limit)}
                                </span>
                              </div>
                              <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${
                                    usagePct >= 100 ? 'bg-error' : usagePct >= 80 ? 'bg-warning' : 'bg-primary'
                                  }`}
                                  style={{ width: `${usagePct}%` }}
                                ></div>
                              </div>
                              <div className="flex justify-between text-body-sm text-on-surface-variant pt-xs">
                                <span>Fecha dia {acc.closing_day ?? '-'}</span>
                                <span>Vence dia {acc.due_day ?? '-'}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                    {accounts.length === 0 && (
                      <div className="col-span-full glass-card p-xl rounded-xl text-center text-on-surface-variant">
                        Nenhuma conta ou cartão cadastrado ainda.
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            );

          // ---------------------------------------------------------------
          case 'orcamento':
            return (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                <div className="flex justify-end items-center mb-lg">
                  <button
                    onClick={handleAddBudget}
                    className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10"
                  >
                    <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>add</span>
                    Novo Orçamento
                  </button>
                </div>

                {budgetsLoading ? (
                  <div className="flex justify-center py-xl">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                ) : (
                  <div className="glass-card p-xl rounded-xl">
                    <div className="space-y-lg">
                      {budgets.map((b) => {
                        const pct = b.limit_amount > 0 ? (b.spent_amount / b.limit_amount) * 100 : 0;
                        const barColor = pct >= 100 ? 'bg-error' : pct >= 80 ? 'bg-warning' : 'bg-success';
                        return (
                          <div key={b.id} className="group">
                            <div className="flex justify-between items-center mb-sm">
                              <span className="text-label-md font-label-md">{b.category}</span>
                              <div className="flex items-center gap-md">
                                <span className="text-label-md font-bold">
                                  R$ {formatCurrency(b.spent_amount)} / R$ {formatCurrency(b.limit_amount)}
                                </span>
                                <button
                                  onClick={() => handleDeleteBudget(b.id)}
                                  disabled={deletingBudgetId === b.id}
                                  className="p-1.5 rounded-lg bg-surface-container hover:bg-error-container/20 text-on-surface-variant hover:text-error transition-all opacity-0 group-hover:opacity-100 disabled:opacity-50"
                                  title="Remover orçamento"
                                >
                                  <span className="material-symbols-outlined text-sm">delete</span>
                                </button>
                              </div>
                            </div>
                            <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${barColor}`}
                                style={{ width: `${Math.min(pct, 100)}%` }}
                              ></div>
                            </div>
                            <div className="text-body-sm text-on-surface-variant mt-1 text-right">
                              {pct.toFixed(1)}%
                            </div>
                          </div>
                        );
                      })}
                      {budgets.length === 0 && (
                        <div className="text-center text-on-surface-variant py-xl">
                          Nenhum orçamento cadastrado ainda.
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </motion.div>
            );

          // ---------------------------------------------------------------
          // TODO Task 14: Metas
          case 'metas':
            return <PlaceholderTab label="Metas" />;

          // ---------------------------------------------------------------
          // TODO Task 14: Dívidas
          case 'dividas':
            return <PlaceholderTab label="Dívidas" />;

          // ---------------------------------------------------------------
          // TODO Task 15: Assinaturas
          case 'assinaturas':
            return <PlaceholderTab label="Assinaturas" />;

          // ---------------------------------------------------------------
          // TODO Task 15: Divisão de Despesas
          case 'divisao':
            return <PlaceholderTab label="Divisão de Despesas" />;

          // ---------------------------------------------------------------
          // TODO Task 16: Analítico
          case 'analitico':
            return <PlaceholderTab label="Analítico" />;

          // ---------------------------------------------------------------
          // TODO Task 16: Timeboxes & OKRs
          case 'timeboxes-okrs':
            return <PlaceholderTab label="Timeboxes & OKRs" />;

          // ---------------------------------------------------------------
          // TODO Task 17: CFO Pessoal IA
          case 'cfo-pessoal':
            return <PlaceholderTab label="CFO Pessoal IA" />;

          default:
            return null;
        }
      })()}

      {/* Modal: Novo Lançamento (Extrato) */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[440px]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">Novo Lançamento</h3>
                <button onClick={() => setIsModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSaveEntry} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Tipo</label>
                  <select
                    value={entryForm.type}
                    onChange={(e) =>
                      setEntryForm({ ...entryForm, type: e.target.value as 'RECEITA' | 'DESPESA', category: '' })
                    }
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  >
                    <option value="RECEITA">Receita</option>
                    <option value="DESPESA">Despesa</option>
                  </select>
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Descrição</label>
                  <input
                    required
                    type="text"
                    value={entryForm.description}
                    onChange={(e) => setEntryForm({ ...entryForm, description: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Valor (R$)</label>
                  <input
                    required
                    type="number"
                    step="0.01"
                    min="0"
                    value={entryForm.amount}
                    onChange={(e) => setEntryForm({ ...entryForm, amount: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Categoria</label>
                  <select
                    required
                    value={entryForm.category}
                    onChange={(e) => setEntryForm({ ...entryForm, category: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  >
                    <option value="" disabled>Selecione...</option>
                    {categoryOptions.map((cat) => (
                      <option key={cat.id} value={cat.name}>{cat.name}</option>
                    ))}
                  </select>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" disabled={saving} className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                    {saving ? 'Salvando...' : 'Adicionar'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Modal: Nova Conta/Cartão */}
      <AnimatePresence>
        {isAccountModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsAccountModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[440px]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">Nova Conta/Cartão</h3>
                <button onClick={() => setIsAccountModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSaveAccount} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Nome</label>
                  <input
                    required
                    type="text"
                    value={accountForm.name}
                    onChange={(e) => setAccountForm({ ...accountForm, name: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Tipo</label>
                  <select
                    value={accountForm.type}
                    onChange={(e) =>
                      setAccountForm({ ...accountForm, type: e.target.value as 'CONTA' | 'CARTAO' })
                    }
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  >
                    <option value="CONTA">Conta</option>
                    <option value="CARTAO">Cartão</option>
                  </select>
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">
                    {accountForm.type === 'CARTAO' ? 'Fatura atual (R$)' : 'Saldo (R$)'}
                  </label>
                  <input
                    required
                    type="number"
                    step="0.01"
                    value={accountForm.balance}
                    onChange={(e) => setAccountForm({ ...accountForm, balance: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>

                {accountForm.type === 'CARTAO' && (
                  <>
                    <div>
                      <label className="block text-label-md text-on-surface-variant mb-1">Limite (R$)</label>
                      <input
                        required
                        type="number"
                        step="0.01"
                        min="0"
                        value={accountForm.limit}
                        onChange={(e) => setAccountForm({ ...accountForm, limit: e.target.value })}
                        className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-md">
                      <div>
                        <label className="block text-label-md text-on-surface-variant mb-1">Dia de fechamento</label>
                        <input
                          required
                          type="number"
                          min="1"
                          max="31"
                          value={accountForm.closing_day}
                          onChange={(e) => setAccountForm({ ...accountForm, closing_day: e.target.value })}
                          className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-label-md text-on-surface-variant mb-1">Dia de vencimento</label>
                        <input
                          required
                          type="number"
                          min="1"
                          max="31"
                          value={accountForm.due_day}
                          onChange={(e) => setAccountForm({ ...accountForm, due_day: e.target.value })}
                          className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                        />
                      </div>
                    </div>
                  </>
                )}

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsAccountModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" disabled={savingAccount} className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                    {savingAccount ? 'Salvando...' : 'Adicionar'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Modal: Novo Orçamento */}
      <AnimatePresence>
        {isBudgetModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsBudgetModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[440px]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">Novo Orçamento</h3>
                <button onClick={() => setIsBudgetModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSaveBudget} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Categoria</label>
                  <input
                    required
                    type="text"
                    value={budgetForm.category}
                    onChange={(e) => setBudgetForm({ ...budgetForm, category: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Limite mensal (R$)</label>
                  <input
                    required
                    type="number"
                    step="0.01"
                    min="0"
                    value={budgetForm.limit_amount}
                    onChange={(e) => setBudgetForm({ ...budgetForm, limit_amount: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsBudgetModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" disabled={savingBudget} className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                    {savingBudget ? 'Salvando...' : 'Adicionar'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </Layout>
  );
}

// Shared placeholder used by the 9 tabs not yet implemented. Future tasks
// remove the `PlaceholderTab` call for their tab (see TODO comments above)
// and replace it with real markup / state / effects for that tab only.
function PlaceholderTab({ label }: { label: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-xl rounded-xl flex flex-col items-center justify-center text-center min-h-[240px]"
    >
      <span className="material-symbols-outlined text-[40px] text-on-surface-variant mb-md">construction</span>
      <h3 className="font-headline-sm text-headline-sm text-on-surface mb-xs">{label}</h3>
      <p className="text-on-surface-variant text-body-sm">Em breve</p>
    </motion.div>
  );
}
