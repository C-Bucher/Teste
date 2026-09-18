import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import Layout from '../components/Layout';
import { useToast } from '../context/ToastContext';
import { useConfirm } from '../context/ConfirmContext';

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

interface PersonalGoal {
  id: string;
  name: string;
  target_amount: number;
  current_amount: number;
  target_date: string;
}

interface PersonalDebt {
  id: string;
  name: string;
  total_amount: number;
  remaining_amount: number;
  installments_total: number;
  installments_paid: number;
  interest_rate: number;
}

interface PersonalSubscription {
  id: string;
  name: string;
  amount: number;
  billing_day: number;
  category: string;
  is_active: boolean;
}

interface SplitParticipant {
  name: string;
  share: number;
  paid: boolean;
}

interface PersonalSplit {
  id: string;
  description: string;
  total_amount: number;
  participants: SplitParticipant[];
}

interface SpendByCategory {
  category: string;
  total: number;
}

interface NetWorthPoint {
  month: string;
  value: number;
}

interface PersonalAnalytics {
  spend_by_category: SpendByCategory[];
  net_worth_series: NetWorthPoint[];
}

interface PersonalTimebox {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
}

interface PersonalOkr {
  id: string;
  objective: string;
  key_results: string[];
}

interface PersonalCfoInsight {
  type: 'ALERT' | 'OPPORTUNITY' | 'CUT';
  message: string;
  impact_value: number;
}

const formatCurrency = (value: number | undefined | null) =>
  (value ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 });

const formatDate = (value: string | null | undefined) => {
  if (!value) return '-';
  const [y, m, d] = value.split('-');
  if (!y || !m || !d) return value;
  return `${d}/${m}/${y}`;
};

// Formats a `datetime-local` input value ("YYYY-MM-DDTHH:mm") for display;
// falls back to the raw string for any other shape so mock data never blows up.
const formatDateTime = (value: string | null | undefined) => {
  if (!value) return '-';
  const [datePart, timePart] = value.split('T');
  const formattedDate = formatDate(datePart);
  if (formattedDate === '-' || formattedDate === datePart) return value;
  return timePart ? `${formattedDate} ${timePart}` : formattedDate;
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

const EMPTY_GOAL_FORM = {
  name: '',
  target_amount: '',
  target_date: '',
};

const EMPTY_DEBT_FORM = {
  name: '',
  total_amount: '',
  remaining_amount: '',
  installments_total: '',
  interest_rate: '',
};

const EMPTY_SUBSCRIPTION_FORM = {
  name: '',
  amount: '',
  billing_day: '',
  category: '',
};

const EMPTY_SPLIT_PARTICIPANT_FORM = { name: '', share: '' };

const EMPTY_SPLIT_FORM = {
  description: '',
  total_amount: '',
  participants: [{ ...EMPTY_SPLIT_PARTICIPANT_FORM }, { ...EMPTY_SPLIT_PARTICIPANT_FORM }],
};

const EMPTY_TIMEBOX_FORM = {
  title: '',
  start_time: '',
  end_time: '',
};

const MAX_OKR_KEY_RESULTS = 5;

const EMPTY_OKR_FORM = {
  objective: '',
  key_results: [''],
};

export default function HubPessoal() {
  // Note: no role guard here on purpose — Hub Pessoal is reachable by every
  // authenticated user regardless of role. Access is gated at the nav level
  // in Layout.tsx by `plan_scope`, not by role.

  const { tab } = useParams<{ tab: string }>();
  const navigate = useNavigate();
  const toast = useToast();
  const confirm = useConfirm();
  const activeTab: TabId = (TABS.some((t) => t.id === tab) ? tab : 'visao-geral') as TabId;

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

  // Metas
  const [goals, setGoals] = useState<PersonalGoal[]>([]);
  const [goalsLoading, setGoalsLoading] = useState(true);
  const [isGoalModalOpen, setIsGoalModalOpen] = useState(false);
  const [goalForm, setGoalForm] = useState(EMPTY_GOAL_FORM);
  const [savingGoal, setSavingGoal] = useState(false);
  const [deletingGoalId, setDeletingGoalId] = useState<string | null>(null);
  const [contributingGoalId, setContributingGoalId] = useState<string | null>(null);
  const [contributeAmount, setContributeAmount] = useState('');
  const [savingContribution, setSavingContribution] = useState(false);

  // Dívidas
  const [debts, setDebts] = useState<PersonalDebt[]>([]);
  const [debtsLoading, setDebtsLoading] = useState(true);
  const [isDebtModalOpen, setIsDebtModalOpen] = useState(false);
  const [debtForm, setDebtForm] = useState(EMPTY_DEBT_FORM);
  const [savingDebt, setSavingDebt] = useState(false);
  const [deletingDebtId, setDeletingDebtId] = useState<string | null>(null);

  // Assinaturas
  const [subscriptions, setSubscriptions] = useState<PersonalSubscription[]>([]);
  const [subscriptionsLoading, setSubscriptionsLoading] = useState(true);
  const [isSubscriptionModalOpen, setIsSubscriptionModalOpen] = useState(false);
  const [subscriptionForm, setSubscriptionForm] = useState(EMPTY_SUBSCRIPTION_FORM);
  const [savingSubscription, setSavingSubscription] = useState(false);
  const [deletingSubscriptionId, setDeletingSubscriptionId] = useState<string | null>(null);

  // Divisão de Despesas
  const [splits, setSplits] = useState<PersonalSplit[]>([]);
  const [splitsLoading, setSplitsLoading] = useState(true);
  const [isSplitModalOpen, setIsSplitModalOpen] = useState(false);
  const [splitForm, setSplitForm] = useState(EMPTY_SPLIT_FORM);
  const [savingSplit, setSavingSplit] = useState(false);
  const [deletingSplitId, setDeletingSplitId] = useState<string | null>(null);

  // Analítico
  const [analytics, setAnalytics] = useState<PersonalAnalytics | null>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);

  // Timeboxes & OKRs
  const [timeboxes, setTimeboxes] = useState<PersonalTimebox[]>([]);
  const [timeboxesLoading, setTimeboxesLoading] = useState(true);
  const [isTimeboxModalOpen, setIsTimeboxModalOpen] = useState(false);
  const [timeboxForm, setTimeboxForm] = useState(EMPTY_TIMEBOX_FORM);
  const [savingTimebox, setSavingTimebox] = useState(false);

  const [okrs, setOkrs] = useState<PersonalOkr[]>([]);
  const [okrsLoading, setOkrsLoading] = useState(true);
  const [isOkrModalOpen, setIsOkrModalOpen] = useState(false);
  const [okrForm, setOkrForm] = useState(EMPTY_OKR_FORM);
  const [savingOkr, setSavingOkr] = useState(false);

  // CFO Pessoal IA
  const [cfoInsights, setCfoInsights] = useState<PersonalCfoInsight[] | null>(null);
  const [cfoInsightsLoading, setCfoInsightsLoading] = useState(false);

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

  const fetchGoals = async () => {
    setGoalsLoading(true);
    try {
      const res = await api.get('/personal/goals');
      setGoals(res.data || []);
    } catch (err) {
      console.error('Erro ao carregar metas', err);
    } finally {
      setGoalsLoading(false);
    }
  };

  const fetchDebts = async () => {
    setDebtsLoading(true);
    try {
      const res = await api.get('/personal/debts');
      setDebts(res.data || []);
    } catch (err) {
      console.error('Erro ao carregar dívidas', err);
    } finally {
      setDebtsLoading(false);
    }
  };

  const fetchSubscriptions = async () => {
    setSubscriptionsLoading(true);
    try {
      const res = await api.get('/personal/subscriptions');
      setSubscriptions(res.data || []);
    } catch (err) {
      console.error('Erro ao carregar assinaturas', err);
    } finally {
      setSubscriptionsLoading(false);
    }
  };

  const fetchSplits = async () => {
    setSplitsLoading(true);
    try {
      const res = await api.get('/personal/splits');
      setSplits(res.data || []);
    } catch (err) {
      console.error('Erro ao carregar divisões de despesas', err);
    } finally {
      setSplitsLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    setAnalyticsLoading(true);
    try {
      const res = await api.get('/personal/analytics');
      setAnalytics(res.data);
    } catch (err) {
      console.error('Erro ao carregar dashboard analítico', err);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const fetchTimeboxes = async () => {
    setTimeboxesLoading(true);
    try {
      const res = await api.get('/personal/timeboxes');
      setTimeboxes(res.data || []);
    } catch (err) {
      console.error('Erro ao carregar timeboxes', err);
    } finally {
      setTimeboxesLoading(false);
    }
  };

  const fetchOkrs = async () => {
    setOkrsLoading(true);
    try {
      const res = await api.get('/personal/okrs');
      setOkrs(res.data || []);
    } catch (err) {
      console.error('Erro ao carregar OKRs', err);
    } finally {
      setOkrsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
    fetchEntries();
    fetchCategories();
    fetchAccounts();
    fetchBudgets();
    fetchGoals();
    fetchDebts();
    fetchSubscriptions();
    fetchSplits();
    fetchAnalytics();
    fetchTimeboxes();
    fetchOkrs();
  }, []);

  // Re-fetch the dashboard whenever the user comes back to "Visão Geral" so
  // the saldo/receitas/despesas reflect any entries created in "Extrato".
  useEffect(() => {
    if (activeTab === 'visao-geral') {
      fetchDashboard();
    }
    // Same idea for "Analítico" — spend_by_category should reflect entries
    // created/removed elsewhere in the hub.
    if (activeTab === 'analitico') {
      fetchAnalytics();
    }
  }, [tab]);

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
      toast.success('Lançamento criado.');
    } catch (err) {
      console.error('Erro ao criar lançamento pessoal', err);
      toast.error('Erro ao criar lançamento.');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteEntry = async (id: string) => {
    const ok = await confirm({
      title: 'Excluir lançamento',
      message: 'Deseja realmente excluir este lançamento?',
      confirmLabel: 'Excluir',
      isDestructive: true,
    });
    if (!ok) return;
    setDeletingId(id);
    try {
      await api.delete(`/personal/entries/${id}`);
      setEntries((prev) => prev.filter((en) => en.id !== id));
      await fetchDashboard();
      toast.success('Lançamento excluído.');
    } catch (err) {
      console.error('Erro ao excluir lançamento pessoal', err);
      toast.error('Erro ao excluir lançamento.');
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
      toast.success('Conta/cartão criado.');
    } catch (err) {
      console.error('Erro ao criar conta/cartão', err);
      toast.error('Erro ao criar conta/cartão.');
    } finally {
      setSavingAccount(false);
    }
  };

  const handleDeleteAccount = async (id: string) => {
    const ok = await confirm({
      title: 'Excluir conta/cartão',
      message: 'Deseja realmente excluir esta conta/cartão?',
      confirmLabel: 'Excluir',
      isDestructive: true,
    });
    if (!ok) return;
    setDeletingAccountId(id);
    try {
      await api.delete(`/personal/accounts/${id}`);
      setAccounts((prev) => prev.filter((a) => a.id !== id));
      toast.success('Conta/cartão excluído.');
    } catch (err) {
      console.error('Erro ao excluir conta/cartão', err);
      toast.error('Erro ao excluir conta/cartão.');
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
      toast.success('Orçamento criado.');
    } catch (err) {
      console.error('Erro ao criar orçamento', err);
      toast.error('Erro ao criar orçamento.');
    } finally {
      setSavingBudget(false);
    }
  };

  const handleDeleteBudget = async (id: string) => {
    const ok = await confirm({
      title: 'Excluir orçamento',
      message: 'Deseja realmente excluir este orçamento?',
      confirmLabel: 'Excluir',
      isDestructive: true,
    });
    if (!ok) return;
    setDeletingBudgetId(id);
    try {
      await api.delete(`/personal/budgets/${id}`);
      setBudgets((prev) => prev.filter((b) => b.id !== id));
      toast.success('Orçamento excluído.');
    } catch (err) {
      console.error('Erro ao excluir orçamento', err);
      toast.error('Erro ao excluir orçamento.');
    } finally {
      setDeletingBudgetId(null);
    }
  };

  const handleAddGoal = () => {
    setGoalForm(EMPTY_GOAL_FORM);
    setIsGoalModalOpen(true);
  };

  const handleSaveGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingGoal(true);
    try {
      await api.post('/personal/goals', {
        name: goalForm.name,
        target_amount: Number(goalForm.target_amount || 0),
        target_date: goalForm.target_date,
      });
      setIsGoalModalOpen(false);
      await fetchGoals();
      toast.success('Meta criada.');
    } catch (err) {
      console.error('Erro ao criar meta', err);
      toast.error('Erro ao criar meta.');
    } finally {
      setSavingGoal(false);
    }
  };

  const handleDeleteGoal = async (id: string) => {
    const ok = await confirm({
      title: 'Excluir meta',
      message: 'Deseja realmente excluir esta meta?',
      confirmLabel: 'Excluir',
      isDestructive: true,
    });
    if (!ok) return;
    setDeletingGoalId(id);
    try {
      await api.delete(`/personal/goals/${id}`);
      setGoals((prev) => prev.filter((g) => g.id !== id));
      toast.success('Meta excluída.');
    } catch (err) {
      console.error('Erro ao excluir meta', err);
      toast.error('Erro ao excluir meta.');
    } finally {
      setDeletingGoalId(null);
    }
  };

  const handleOpenContribute = (id: string) => {
    setContributeAmount('');
    setContributingGoalId((prev) => (prev === id ? null : id));
  };

  const handleConfirmContribute = async (id: string) => {
    const value = Number(contributeAmount);
    if (!value || value <= 0) return;
    setSavingContribution(true);
    try {
      const res = await api.post(`/personal/goals/${id}/contribute`, { amount: value });
      const updated = res.data;
      setGoals((prev) => prev.map((g) => (g.id === id ? { ...g, current_amount: updated.current_amount } : g)));
      setContributingGoalId(null);
      setContributeAmount('');
      toast.success('Aporte adicionado.');
    } catch (err) {
      console.error('Erro ao adicionar aporte', err);
      toast.error('Erro ao adicionar aporte.');
    } finally {
      setSavingContribution(false);
    }
  };

  const handleAddDebt = () => {
    setDebtForm(EMPTY_DEBT_FORM);
    setIsDebtModalOpen(true);
  };

  const handleSaveDebt = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingDebt(true);
    try {
      await api.post('/personal/debts', {
        name: debtForm.name,
        total_amount: Number(debtForm.total_amount || 0),
        remaining_amount: Number(debtForm.remaining_amount || 0),
        installments_total: Number(debtForm.installments_total || 0),
        interest_rate: Number(debtForm.interest_rate || 0),
      });
      setIsDebtModalOpen(false);
      await fetchDebts();
      toast.success('Dívida cadastrada.');
    } catch (err) {
      console.error('Erro ao criar dívida', err);
      toast.error('Erro ao criar dívida.');
    } finally {
      setSavingDebt(false);
    }
  };

  const handleDeleteDebt = async (id: string) => {
    const ok = await confirm({
      title: 'Quitar/excluir dívida',
      message: 'Deseja realmente quitar/excluir esta dívida?',
      confirmLabel: 'Confirmar',
      isDestructive: true,
    });
    if (!ok) return;
    setDeletingDebtId(id);
    try {
      await api.delete(`/personal/debts/${id}`);
      setDebts((prev) => prev.filter((d) => d.id !== id));
      toast.success('Dívida removida.');
    } catch (err) {
      console.error('Erro ao excluir dívida', err);
      toast.error('Erro ao excluir dívida.');
    } finally {
      setDeletingDebtId(null);
    }
  };

  const handleAddSubscription = () => {
    setSubscriptionForm(EMPTY_SUBSCRIPTION_FORM);
    setIsSubscriptionModalOpen(true);
  };

  const handleSaveSubscription = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingSubscription(true);
    try {
      await api.post('/personal/subscriptions', {
        name: subscriptionForm.name,
        amount: Number(subscriptionForm.amount || 0),
        billing_day: Number(subscriptionForm.billing_day || 0),
        category: subscriptionForm.category,
      });
      setIsSubscriptionModalOpen(false);
      await fetchSubscriptions();
      toast.success('Assinatura criada.');
    } catch (err) {
      console.error('Erro ao criar assinatura', err);
      toast.error('Erro ao criar assinatura.');
    } finally {
      setSavingSubscription(false);
    }
  };

  const handleDeleteSubscription = async (id: string) => {
    const ok = await confirm({
      title: 'Excluir assinatura',
      message: 'Deseja realmente excluir esta assinatura?',
      confirmLabel: 'Excluir',
      isDestructive: true,
    });
    if (!ok) return;
    setDeletingSubscriptionId(id);
    try {
      await api.delete(`/personal/subscriptions/${id}`);
      setSubscriptions((prev) => prev.filter((s) => s.id !== id));
      toast.success('Assinatura excluída.');
    } catch (err) {
      console.error('Erro ao excluir assinatura', err);
      toast.error('Erro ao excluir assinatura.');
    } finally {
      setDeletingSubscriptionId(null);
    }
  };

  const handleAddSplit = () => {
    setSplitForm(EMPTY_SPLIT_FORM);
    setIsSplitModalOpen(true);
  };

  const handleSplitParticipantChange = (index: number, field: 'name' | 'share', value: string) => {
    setSplitForm((prev) => ({
      ...prev,
      participants: prev.participants.map((p, i) => (i === index ? { ...p, [field]: value } : p)),
    }));
  };

  const handleAddSplitParticipantRow = () => {
    setSplitForm((prev) => ({
      ...prev,
      participants: [...prev.participants, { ...EMPTY_SPLIT_PARTICIPANT_FORM }],
    }));
  };

  const handleRemoveSplitParticipantRow = (index: number) => {
    setSplitForm((prev) => ({
      ...prev,
      participants: prev.participants.filter((_, i) => i !== index),
    }));
  };

  const handleSaveSplit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingSplit(true);
    try {
      await api.post('/personal/splits', {
        description: splitForm.description,
        total_amount: Number(splitForm.total_amount || 0),
        participants: splitForm.participants
          .filter((p) => p.name.trim() !== '')
          .map((p) => ({ name: p.name, share: Number(p.share || 0), paid: false })),
      });
      setIsSplitModalOpen(false);
      await fetchSplits();
      toast.success('Divisão de despesas criada.');
    } catch (err) {
      console.error('Erro ao criar divisão de despesas', err);
      toast.error('Erro ao criar divisão de despesas.');
    } finally {
      setSavingSplit(false);
    }
  };

  const handleDeleteSplit = async (id: string) => {
    const ok = await confirm({
      title: 'Excluir divisão',
      message: 'Deseja realmente excluir esta divisão?',
      confirmLabel: 'Excluir',
      isDestructive: true,
    });
    if (!ok) return;
    setDeletingSplitId(id);
    try {
      await api.delete(`/personal/splits/${id}`);
      setSplits((prev) => prev.filter((s) => s.id !== id));
      toast.success('Divisão excluída.');
    } catch (err) {
      console.error('Erro ao excluir divisão de despesas', err);
      toast.error('Erro ao excluir divisão de despesas.');
    } finally {
      setDeletingSplitId(null);
    }
  };

  const handleAddTimebox = () => {
    setTimeboxForm(EMPTY_TIMEBOX_FORM);
    setIsTimeboxModalOpen(true);
  };

  const handleSaveTimebox = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingTimebox(true);
    try {
      const res = await api.post('/personal/timeboxes', {
        title: timeboxForm.title,
        start_time: timeboxForm.start_time,
        end_time: timeboxForm.end_time,
      });
      setTimeboxes((prev) => [...prev, res.data]);
      setIsTimeboxModalOpen(false);
      toast.success('Timebox criado.');
    } catch (err) {
      console.error('Erro ao criar timebox', err);
      toast.error('Erro ao criar timebox.');
    } finally {
      setSavingTimebox(false);
    }
  };

  const handleAddOkr = () => {
    setOkrForm(EMPTY_OKR_FORM);
    setIsOkrModalOpen(true);
  };

  const handleOkrKeyResultChange = (index: number, value: string) => {
    setOkrForm((prev) => ({
      ...prev,
      key_results: prev.key_results.map((kr, i) => (i === index ? value : kr)),
    }));
  };

  const handleAddOkrKeyResultRow = () => {
    setOkrForm((prev) =>
      prev.key_results.length >= MAX_OKR_KEY_RESULTS ? prev : { ...prev, key_results: [...prev.key_results, ''] }
    );
  };

  const handleRemoveOkrKeyResultRow = (index: number) => {
    setOkrForm((prev) => ({
      ...prev,
      key_results: prev.key_results.filter((_, i) => i !== index),
    }));
  };

  const handleSaveOkr = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingOkr(true);
    try {
      const res = await api.post('/personal/okrs', {
        objective: okrForm.objective,
        key_results: okrForm.key_results.map((kr) => kr.trim()).filter((kr) => kr !== ''),
      });
      setOkrs((prev) => [...prev, res.data]);
      setIsOkrModalOpen(false);
      toast.success('OKR criado.');
    } catch (err) {
      console.error('Erro ao criar OKR', err);
      toast.error('Erro ao criar OKR.');
    } finally {
      setSavingOkr(false);
    }
  };

  const handleGenerateCfoInsights = async () => {
    setCfoInsightsLoading(true);
    try {
      const res = await api.post('/personal/ai/insights', {});
      setCfoInsights(res.data.insights || []);
    } catch (err) {
      console.error('Erro ao gerar análise do CFO Pessoal IA', err);
      toast.error('Erro ao gerar análise.');
    } finally {
      setCfoInsightsLoading(false);
    }
  };

  const categoryOptions = categories.filter((c) => c.type === entryForm.type);

  // Total mensal somado apenas das assinaturas ativas — assinaturas inativas
  // não representam cobrança recorrente corrente, então não entram na soma.
  const totalMonthlySubscriptions = subscriptions
    .filter((s) => s.is_active)
    .reduce((sum, s) => sum + (s.amount || 0), 0);

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
          <span className="text-primary">{TABS.find((t) => t.id === activeTab)?.label ?? 'Hub Pessoal'}</span>
        </nav>
        <h2 className="font-display-lg text-display-lg text-on-surface">{TABS.find((t) => t.id === activeTab)?.label ?? 'Hub Pessoal'}</h2>
        <p className="text-on-surface-variant text-body-base mt-xs">
          Organize suas finanças pessoais: extrato, orçamento, metas, dívidas e muito mais.
        </p>
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
                    <button onClick={() => navigate('/pessoal/extrato')} className="text-primary font-label-md hover:underline">
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
          case 'metas':
            return (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                <div className="flex justify-end items-center mb-lg">
                  <button
                    onClick={handleAddGoal}
                    className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10"
                  >
                    <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>add</span>
                    Nova Meta
                  </button>
                </div>

                {goalsLoading ? (
                  <div className="flex justify-center py-xl">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-lg">
                    {goals.map((goal) => {
                      const pct = goal.target_amount > 0 ? Math.min((goal.current_amount / goal.target_amount) * 100, 100) : 0;
                      const isContributing = contributingGoalId === goal.id;
                      return (
                        <div key={goal.id} className="glass-card p-lg rounded-xl relative group">
                          <button
                            onClick={() => handleDeleteGoal(goal.id)}
                            disabled={deletingGoalId === goal.id}
                            className="absolute top-md right-md p-2 rounded-lg bg-surface-container hover:bg-error-container/20 text-on-surface-variant hover:text-error transition-all opacity-0 group-hover:opacity-100 disabled:opacity-50"
                            title="Remover meta"
                          >
                            <span className="material-symbols-outlined text-sm">delete</span>
                          </button>

                          <div className="flex items-center gap-sm mb-md">
                            <div className="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center">
                              <span className="material-symbols-outlined text-[20px]">flag</span>
                            </div>
                            <div>
                              <h4 className="font-headline-sm text-headline-sm text-on-surface">{goal.name}</h4>
                              <span className="text-body-sm text-on-surface-variant">
                                Meta para {formatDate(goal.target_date)}
                              </span>
                            </div>
                          </div>

                          <div className="mb-sm">
                            <span className="text-label-md font-bold">
                              R$ {formatCurrency(goal.current_amount)} / R$ {formatCurrency(goal.target_amount)}
                            </span>
                          </div>
                          <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full bg-primary"
                              style={{ width: `${pct}%` }}
                            ></div>
                          </div>
                          <div className="text-body-sm text-on-surface-variant mt-1 text-right mb-md">
                            {pct.toFixed(1)}%
                          </div>

                          {isContributing ? (
                            <div className="flex items-center gap-sm mt-sm">
                              <input
                                type="number"
                                step="0.01"
                                min="0"
                                autoFocus
                                placeholder="Valor (R$)"
                                value={contributeAmount}
                                onChange={(e) => setContributeAmount(e.target.value)}
                                className="w-full bg-surface-container border border-border-subtle rounded-lg px-3 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none text-body-sm"
                              />
                              <button
                                onClick={() => handleConfirmContribute(goal.id)}
                                disabled={savingContribution}
                                className="p-2 rounded-lg bg-primary text-on-primary hover:bg-primary/90 transition-colors disabled:opacity-50 shrink-0"
                                title="Confirmar aporte"
                              >
                                <span className="material-symbols-outlined text-sm">check</span>
                              </button>
                              <button
                                onClick={() => setContributingGoalId(null)}
                                className="p-2 rounded-lg bg-surface-container hover:bg-surface-container-highest text-on-surface-variant transition-colors shrink-0"
                                title="Cancelar"
                              >
                                <span className="material-symbols-outlined text-sm">close</span>
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => handleOpenContribute(goal.id)}
                              className="w-full mt-sm px-4 py-2 rounded-lg font-label-md text-label-md bg-surface-container hover:bg-surface-container-highest text-on-surface transition-colors"
                            >
                              Adicionar Aporte
                            </button>
                          )}
                        </div>
                      );
                    })}
                    {goals.length === 0 && (
                      <div className="col-span-full glass-card p-xl rounded-xl text-center text-on-surface-variant">
                        Nenhuma meta cadastrada ainda.
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            );

          // ---------------------------------------------------------------
          case 'dividas':
            return (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                <div className="flex justify-end items-center mb-lg">
                  <button
                    onClick={handleAddDebt}
                    className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10"
                  >
                    <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>add</span>
                    Nova Dívida
                  </button>
                </div>

                {debtsLoading ? (
                  <div className="flex justify-center py-xl">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-lg">
                    {debts.map((debt) => {
                      const paidAmount = debt.total_amount - debt.remaining_amount;
                      const pct = debt.total_amount > 0 ? Math.min((paidAmount / debt.total_amount) * 100, 100) : 0;
                      return (
                        <div key={debt.id} className="glass-card p-lg rounded-xl relative group">
                          <button
                            onClick={() => handleDeleteDebt(debt.id)}
                            disabled={deletingDebtId === debt.id}
                            className="absolute top-md right-md p-2 rounded-lg bg-surface-container hover:bg-error-container/20 text-on-surface-variant hover:text-error transition-all opacity-0 group-hover:opacity-100 disabled:opacity-50"
                            title="Quitar / remover dívida"
                          >
                            <span className="material-symbols-outlined text-sm">delete</span>
                          </button>

                          <div className="flex items-center gap-sm mb-md">
                            <div className="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center">
                              <span className="material-symbols-outlined text-[20px]">account_balance</span>
                            </div>
                            <div>
                              <h4 className="font-headline-sm text-headline-sm text-on-surface">{debt.name}</h4>
                              <span className="text-body-sm text-on-surface-variant">
                                Juros: {debt.interest_rate}% a.m.
                              </span>
                            </div>
                          </div>

                          <div className="mb-sm">
                            <span className="text-on-surface-variant font-label-md text-label-md">Saldo devedor</span>
                            <h3 className="font-display-sm text-display-sm mt-1 text-error">
                              R$ {formatCurrency(debt.remaining_amount)}
                            </h3>
                            <span className="text-body-sm text-on-surface-variant">
                              de R$ {formatCurrency(debt.total_amount)}
                            </span>
                          </div>

                          <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full bg-success"
                              style={{ width: `${pct}%` }}
                            ></div>
                          </div>
                          <div className="flex justify-between text-body-sm text-on-surface-variant mt-1">
                            <span>{pct.toFixed(1)}% quitado</span>
                            <span>{debt.installments_paid}/{debt.installments_total} parcelas</span>
                          </div>
                        </div>
                      );
                    })}
                    {debts.length === 0 && (
                      <div className="col-span-full glass-card p-xl rounded-xl text-center text-on-surface-variant">
                        Nenhuma dívida cadastrada ainda.
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            );

          // ---------------------------------------------------------------
          case 'assinaturas':
            return (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-md mb-lg">
                  <div className="glass-card px-lg py-md rounded-xl">
                    <span className="text-on-surface-variant font-label-md text-label-md">Total mensal (ativas)</span>
                    <h3 className="font-display-sm text-display-sm text-on-surface mt-1">
                      R$ {formatCurrency(totalMonthlySubscriptions)}/mês
                    </h3>
                  </div>
                  <button
                    onClick={handleAddSubscription}
                    className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10"
                  >
                    <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>add</span>
                    Nova Assinatura
                  </button>
                </div>

                {subscriptionsLoading ? (
                  <div className="flex justify-center py-xl">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-lg">
                    {subscriptions.map((sub) => (
                      <div key={sub.id} className="glass-card p-lg rounded-xl relative group">
                        <button
                          onClick={() => handleDeleteSubscription(sub.id)}
                          disabled={deletingSubscriptionId === sub.id}
                          className="absolute top-md right-md p-2 rounded-lg bg-surface-container hover:bg-error-container/20 text-on-surface-variant hover:text-error transition-all opacity-0 group-hover:opacity-100 disabled:opacity-50"
                          title="Remover assinatura"
                        >
                          <span className="material-symbols-outlined text-sm">delete</span>
                        </button>

                        <div className="flex items-center gap-sm mb-md">
                          <div className="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center">
                            <span className="material-symbols-outlined text-[20px]">subscriptions</span>
                          </div>
                          <div>
                            <h4 className="font-headline-sm text-headline-sm text-on-surface">{sub.name}</h4>
                            <span className="text-body-sm text-on-surface-variant">{sub.category || '-'}</span>
                          </div>
                        </div>

                        <div className="mb-sm">
                          <span className="text-on-surface-variant font-label-md text-label-md">Valor</span>
                          <h3 className="font-display-sm text-display-sm mt-1 text-on-surface">
                            R$ {formatCurrency(sub.amount)}
                          </h3>
                        </div>

                        <div className="flex items-center justify-between mt-md pt-md border-t border-border-subtle">
                          <span className="text-body-sm text-on-surface-variant">
                            Cobra todo dia {sub.billing_day}
                          </span>
                          <span
                            className={`inline-flex items-center gap-xs px-2 py-1 rounded-full ${
                              sub.is_active ? 'bg-success/10 text-success' : 'bg-on-surface-variant/10 text-on-surface-variant'
                            } text-[11px] font-bold uppercase tracking-wider`}
                          >
                            <span className={`w-1.5 h-1.5 rounded-full ${sub.is_active ? 'bg-success' : 'bg-on-surface-variant'}`}></span>
                            {sub.is_active ? 'Ativo' : 'Inativo'}
                          </span>
                        </div>
                      </div>
                    ))}
                    {subscriptions.length === 0 && (
                      <div className="col-span-full glass-card p-xl rounded-xl text-center text-on-surface-variant">
                        Nenhuma assinatura cadastrada ainda.
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            );

          // ---------------------------------------------------------------
          case 'divisao':
            return (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                <div className="flex justify-end items-center mb-lg">
                  <button
                    onClick={handleAddSplit}
                    className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10"
                  >
                    <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>add</span>
                    Nova Divisão
                  </button>
                </div>

                {splitsLoading ? (
                  <div className="flex justify-center py-xl">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-lg">
                    {splits.map((split) => (
                      <div key={split.id} className="glass-card p-lg rounded-xl relative group">
                        <button
                          onClick={() => handleDeleteSplit(split.id)}
                          disabled={deletingSplitId === split.id}
                          className="absolute top-md right-md p-2 rounded-lg bg-surface-container hover:bg-error-container/20 text-on-surface-variant hover:text-error transition-all opacity-0 group-hover:opacity-100 disabled:opacity-50"
                          title="Remover divisão"
                        >
                          <span className="material-symbols-outlined text-sm">delete</span>
                        </button>

                        <div className="flex items-center gap-sm mb-md">
                          <div className="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center">
                            <span className="material-symbols-outlined text-[20px]">groups</span>
                          </div>
                          <div>
                            <h4 className="font-headline-sm text-headline-sm text-on-surface">{split.description}</h4>
                            <span className="text-body-sm text-on-surface-variant">
                              Total: R$ {formatCurrency(split.total_amount)}
                            </span>
                          </div>
                        </div>

                        <div className="divide-y divide-border-subtle/50 mt-md">
                          {split.participants.map((p, i) => (
                            <div key={`${split.id}-${i}`} className="flex items-center justify-between py-sm">
                              <span className="font-body-sm text-on-surface">{p.name}</span>
                              <div className="flex items-center gap-md">
                                <span className="text-label-md font-bold text-on-surface">
                                  R$ {formatCurrency(p.share)}
                                </span>
                                <span
                                  className={`inline-flex items-center gap-xs px-2 py-1 rounded-full ${
                                    p.paid ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'
                                  } text-[11px] font-bold uppercase tracking-wider`}
                                >
                                  <span className={`w-1.5 h-1.5 rounded-full ${p.paid ? 'bg-success' : 'bg-warning'}`}></span>
                                  {p.paid ? 'Pago' : 'Pendente'}
                                </span>
                              </div>
                            </div>
                          ))}
                          {split.participants.length === 0 && (
                            <div className="py-sm text-body-sm text-on-surface-variant">Nenhum participante.</div>
                          )}
                        </div>
                      </div>
                    ))}
                    {splits.length === 0 && (
                      <div className="col-span-full glass-card p-xl rounded-xl text-center text-on-surface-variant">
                        Nenhuma divisão de despesas cadastrada ainda.
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            );

          // ---------------------------------------------------------------
          case 'analitico': {
            if (analyticsLoading) {
              return (
                <div className="flex justify-center py-xl">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              );
            }
            const spendByCategory = analytics?.spend_by_category || [];
            const maxSpend = Math.max(...spendByCategory.map((s) => s.total), 1);
            const spendBarColors = ['bg-secondary', 'bg-primary', 'bg-tertiary', 'bg-outline'];
            return (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="grid grid-cols-12 gap-lg">
                {/* Net worth chart (Recharts) — same gradient/axis styling as Dashboard.tsx */}
                <div className="col-span-12 lg:col-span-8 glass-card p-lg rounded-xl min-h-[400px] flex flex-col">
                  <div className="flex justify-between items-center mb-xl">
                    <h4 className="font-headline-sm text-headline-sm">Evolução Patrimonial</h4>
                    <div className="flex items-center gap-xs">
                      <div className="w-3 h-3 rounded-full bg-primary"></div>
                      <span className="text-xs text-on-surface-variant">Patrimônio Líquido</span>
                    </div>
                  </div>

                  <div className="w-full flex-1">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={analytics?.net_worth_series || []} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                        <defs>
                          <linearGradient id="colorPatrimonio" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#adc6ff" stopOpacity={0.3} />
                            <stop offset="95%" stopColor="#adc6ff" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="month" stroke="#8c909f" tick={{ fill: '#8c909f', fontSize: 12 }} axisLine={false} tickLine={false} />
                        <YAxis stroke="#8c909f" tick={{ fill: '#8c909f', fontSize: 12 }} axisLine={false} tickLine={false} />
                        <Tooltip
                          contentStyle={{ backgroundColor: 'rgba(28, 31, 42, 0.9)', borderColor: 'rgba(255, 255, 255, 0.1)', borderRadius: '0.75rem', color: '#dfe2f1', backdropFilter: 'blur(8px)' }}
                          itemStyle={{ color: '#dfe2f1' }}
                          formatter={(value: any) => [`R$ ${formatCurrency(Number(value))}`, 'Patrimônio']}
                        />
                        <Area type="monotone" dataKey="value" stroke="#adc6ff" strokeWidth={3} fillOpacity={1} fill="url(#colorPatrimonio)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Spend by category — same proportional-bar pattern as Dashboard.tsx's "Categorias de Despesas" */}
                <div className="col-span-12 lg:col-span-4 glass-card p-lg rounded-xl flex flex-col justify-center">
                  <h4 className="font-headline-sm text-headline-sm mb-xl">Categorias de Despesas</h4>
                  <div className="space-y-lg">
                    {spendByCategory.map((item, i) => (
                      <div key={item.category}>
                        <div className="flex justify-between mb-sm">
                          <span className="text-label-md font-label-md">{item.category}</span>
                          <span className="text-label-md font-bold">R$ {formatCurrency(item.total)}</span>
                        </div>
                        <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${spendBarColors[i % spendBarColors.length]}`}
                            style={{ width: `${(item.total / maxSpend) * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                    {spendByCategory.length === 0 && (
                      <div className="text-center text-on-surface-variant py-xl">
                        Nenhum gasto registrado ainda.
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          }

          // ---------------------------------------------------------------
          case 'timeboxes-okrs':
            return (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="grid grid-cols-1 lg:grid-cols-2 gap-lg">
                {/* Timeboxes */}
                <div>
                  <div className="flex justify-between items-center mb-lg">
                    <h4 className="font-headline-sm text-headline-sm">Timeboxes</h4>
                    <button
                      onClick={handleAddTimebox}
                      className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-2 rounded-xl hover:opacity-90 transition-all font-label-md text-label-md shadow-lg shadow-primary/10"
                    >
                      <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>add</span>
                      Novo Timebox
                    </button>
                  </div>

                  {timeboxesLoading ? (
                    <div className="flex justify-center py-xl">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                  ) : (
                    <div className="space-y-md">
                      {timeboxes.map((tb) => (
                        <div key={tb.id} className="glass-card p-lg rounded-xl">
                          <div className="flex items-center gap-sm mb-sm">
                            <div className="w-10 h-10 rounded-lg bg-surface-container-highest flex items-center justify-center">
                              <span className="material-symbols-outlined text-[20px]">schedule</span>
                            </div>
                            <h5 className="font-headline-sm text-headline-sm text-on-surface">{tb.title}</h5>
                          </div>
                          <div className="flex justify-between text-body-sm text-on-surface-variant">
                            <span>Início: {formatDateTime(tb.start_time)}</span>
                            <span>Fim: {formatDateTime(tb.end_time)}</span>
                          </div>
                        </div>
                      ))}
                      {timeboxes.length === 0 && (
                        <div className="glass-card p-xl rounded-xl text-center text-on-surface-variant">
                          Nenhum timebox criado ainda. Crie o primeiro para organizar seu tempo.
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* OKRs */}
                <div>
                  <div className="flex justify-between items-center mb-lg">
                    <h4 className="font-headline-sm text-headline-sm">OKRs</h4>
                    <button
                      onClick={handleAddOkr}
                      className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-2 rounded-xl hover:opacity-90 transition-all font-label-md text-label-md shadow-lg shadow-primary/10"
                    >
                      <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>add</span>
                      Novo OKR
                    </button>
                  </div>

                  {okrsLoading ? (
                    <div className="flex justify-center py-xl">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                  ) : (
                    <div className="space-y-md">
                      {okrs.map((okr) => (
                        <div key={okr.id} className="glass-card p-lg rounded-xl">
                          <h5 className="font-headline-sm text-headline-sm text-on-surface mb-sm">{okr.objective}</h5>
                          <ul className="space-y-1 mb-md">
                            {(okr.key_results || []).map((kr, i) => (
                              <li key={i} className="flex items-center gap-sm text-body-sm text-on-surface-variant">
                                <span className="material-symbols-outlined text-[14px]">radio_button_unchecked</span>
                                {kr}
                              </li>
                            ))}
                          </ul>
                          <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
                            <div className="h-full rounded-full bg-primary" style={{ width: '0%' }}></div>
                          </div>
                          <div className="text-body-sm text-on-surface-variant mt-1 text-right">
                            Sem progresso ainda
                          </div>
                        </div>
                      ))}
                      {okrs.length === 0 && (
                        <div className="glass-card p-xl rounded-xl text-center text-on-surface-variant">
                          Nenhum OKR definido ainda. Defina seu primeiro objetivo.
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </motion.div>
            );

          // ---------------------------------------------------------------
          case 'cfo-pessoal': {
            const CFO_INSIGHT_CONFIG: Record<
              PersonalCfoInsight['type'],
              { label: string; icon: string; badge: string; border: string }
            > = {
              ALERT: { label: 'Alerta', icon: 'warning', badge: 'bg-error/10 text-error', border: 'border-l-error' },
              OPPORTUNITY: {
                label: 'Oportunidade',
                icon: 'trending_up',
                badge: 'bg-success/10 text-success',
                border: 'border-l-success',
              },
              CUT: { label: 'Corte', icon: 'content_cut', badge: 'bg-warning/10 text-warning', border: 'border-l-warning' },
            };

            return (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-lg">
                {/* Hero — echoes the "AI Virtual CFO Widget" from Dashboard.tsx (ai-aura, psychology watermark, gradient icon badge) */}
                <div className="glass-card p-xl rounded-xl border border-primary/20 ai-aura relative overflow-hidden">
                  <div className="absolute -right-6 -top-6 opacity-10">
                    <span
                      className="material-symbols-outlined text-[160px] text-primary"
                      style={{ fontVariationSettings: "'FILL' 1" }}
                    >
                      psychology
                    </span>
                  </div>
                  <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-lg">
                    <div>
                      <div className="flex items-center gap-sm mb-md">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary to-secondary flex items-center justify-center">
                          <span
                            className="material-symbols-outlined text-on-primary text-[20px]"
                            style={{ fontVariationSettings: "'FILL' 1" }}
                          >
                            auto_awesome
                          </span>
                        </div>
                        <span className="font-headline-sm text-headline-sm text-primary">CFO Pessoal IA</span>
                      </div>
                      <p className="text-body-sm text-on-surface-variant max-w-[36rem]">
                        Peça uma análise inteligente das suas finanças: alertas de orçamento estourando, oportunidades
                        de rendimento e assinaturas/gastos que dá para cortar.
                      </p>
                    </div>
                    <button
                      onClick={handleGenerateCfoInsights}
                      disabled={cfoInsightsLoading}
                      className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10 disabled:opacity-50 shrink-0"
                    >
                      {cfoInsightsLoading ? (
                        <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-on-primary"></span>
                      ) : (
                        <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
                          auto_awesome
                        </span>
                      )}
                      {cfoInsightsLoading ? 'Analisando...' : 'Gerar Análise'}
                    </button>
                  </div>
                </div>

                {/* Loading state */}
                {cfoInsightsLoading && (
                  <div className="flex justify-center py-xl">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                )}

                {/* Results */}
                {!cfoInsightsLoading && cfoInsights && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-lg">
                    {cfoInsights.map((insight, i) => {
                      const config = CFO_INSIGHT_CONFIG[insight.type];
                      return (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.05 }}
                          className={`glass-card p-lg rounded-xl border-l-4 ${config.border}`}
                        >
                          <div className="flex items-center justify-between mb-md">
                            <span
                              className={`inline-flex items-center gap-xs px-sm py-1 rounded-full text-[11px] font-bold uppercase tracking-wider ${config.badge}`}
                            >
                              <span className="material-symbols-outlined text-[14px]">{config.icon}</span>
                              {config.label}
                            </span>
                            <span className="font-bold text-label-md text-on-surface">
                              R$ {formatCurrency(insight.impact_value)}
                            </span>
                          </div>
                          <p className="text-body-sm text-on-surface italic">"{insight.message}"</p>
                        </motion.div>
                      );
                    })}
                    {cfoInsights.length === 0 && (
                      <div className="col-span-full glass-card p-xl rounded-xl text-center text-on-surface-variant">
                        Nenhum insight disponível no momento.
                      </div>
                    )}
                  </div>
                )}

                {/* Empty state before first run */}
                {!cfoInsightsLoading && !cfoInsights && (
                  <div className="glass-card p-xl rounded-xl text-center text-on-surface-variant">
                    Clique em "Gerar Análise" para receber recomendações personalizadas do seu CFO Pessoal IA.
                  </div>
                )}
              </motion.div>
            );
          }

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
      {/* Modal: Nova Meta */}
      <AnimatePresence>
        {isGoalModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsGoalModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[440px]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">Nova Meta</h3>
                <button onClick={() => setIsGoalModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSaveGoal} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Nome</label>
                  <input
                    required
                    type="text"
                    value={goalForm.name}
                    onChange={(e) => setGoalForm({ ...goalForm, name: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Valor alvo (R$)</label>
                  <input
                    required
                    type="number"
                    step="0.01"
                    min="0"
                    value={goalForm.target_amount}
                    onChange={(e) => setGoalForm({ ...goalForm, target_amount: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Data alvo</label>
                  <input
                    required
                    type="date"
                    value={goalForm.target_date}
                    onChange={(e) => setGoalForm({ ...goalForm, target_date: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsGoalModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" disabled={savingGoal} className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                    {savingGoal ? 'Salvando...' : 'Adicionar'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Modal: Nova Dívida */}
      <AnimatePresence>
        {isDebtModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsDebtModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[440px]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">Nova Dívida</h3>
                <button onClick={() => setIsDebtModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSaveDebt} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Nome</label>
                  <input
                    required
                    type="text"
                    value={debtForm.name}
                    onChange={(e) => setDebtForm({ ...debtForm, name: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Valor total (R$)</label>
                  <input
                    required
                    type="number"
                    step="0.01"
                    min="0"
                    value={debtForm.total_amount}
                    onChange={(e) => setDebtForm({ ...debtForm, total_amount: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Valor restante (R$)</label>
                  <input
                    required
                    type="number"
                    step="0.01"
                    min="0"
                    value={debtForm.remaining_amount}
                    onChange={(e) => setDebtForm({ ...debtForm, remaining_amount: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>
                <div className="grid grid-cols-2 gap-md">
                  <div>
                    <label className="block text-label-md text-on-surface-variant mb-1">Parcelas totais</label>
                    <input
                      required
                      type="number"
                      min="1"
                      value={debtForm.installments_total}
                      onChange={(e) => setDebtForm({ ...debtForm, installments_total: e.target.value })}
                      className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-label-md text-on-surface-variant mb-1">Juros (% a.m.)</label>
                    <input
                      required
                      type="number"
                      step="0.01"
                      min="0"
                      value={debtForm.interest_rate}
                      onChange={(e) => setDebtForm({ ...debtForm, interest_rate: e.target.value })}
                      className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsDebtModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" disabled={savingDebt} className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                    {savingDebt ? 'Salvando...' : 'Adicionar'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Modal: Nova Assinatura */}
      <AnimatePresence>
        {isSubscriptionModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsSubscriptionModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[440px]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">Nova Assinatura</h3>
                <button onClick={() => setIsSubscriptionModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSaveSubscription} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Nome</label>
                  <input
                    required
                    type="text"
                    value={subscriptionForm.name}
                    onChange={(e) => setSubscriptionForm({ ...subscriptionForm, name: e.target.value })}
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
                    value={subscriptionForm.amount}
                    onChange={(e) => setSubscriptionForm({ ...subscriptionForm, amount: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>
                <div className="grid grid-cols-2 gap-md">
                  <div>
                    <label className="block text-label-md text-on-surface-variant mb-1">Dia de cobrança</label>
                    <input
                      required
                      type="number"
                      min="1"
                      max="31"
                      value={subscriptionForm.billing_day}
                      onChange={(e) => setSubscriptionForm({ ...subscriptionForm, billing_day: e.target.value })}
                      className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-label-md text-on-surface-variant mb-1">Categoria</label>
                    <input
                      required
                      type="text"
                      value={subscriptionForm.category}
                      onChange={(e) => setSubscriptionForm({ ...subscriptionForm, category: e.target.value })}
                      className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsSubscriptionModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" disabled={savingSubscription} className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                    {savingSubscription ? 'Salvando...' : 'Adicionar'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Modal: Nova Divisão */}
      <AnimatePresence>
        {isSplitModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsSplitModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[480px] max-h-[85vh] overflow-y-auto"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">Nova Divisão</h3>
                <button onClick={() => setIsSplitModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSaveSplit} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Descrição</label>
                  <input
                    required
                    type="text"
                    value={splitForm.description}
                    onChange={(e) => setSplitForm({ ...splitForm, description: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Valor total (R$)</label>
                  <input
                    required
                    type="number"
                    step="0.01"
                    min="0"
                    value={splitForm.total_amount}
                    onChange={(e) => setSplitForm({ ...splitForm, total_amount: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>

                <div>
                  <label className="block text-label-md text-on-surface-variant mb-2">Participantes</label>
                  <div className="space-y-sm">
                    {splitForm.participants.map((p, i) => (
                      <div key={i} className="flex items-center gap-sm">
                        <input
                          required
                          type="text"
                          placeholder="Nome"
                          value={p.name}
                          onChange={(e) => handleSplitParticipantChange(i, 'name', e.target.value)}
                          className="flex-1 bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                        />
                        <input
                          required
                          type="number"
                          step="0.01"
                          min="0"
                          placeholder="Valor (R$)"
                          value={p.share}
                          onChange={(e) => handleSplitParticipantChange(i, 'share', e.target.value)}
                          className="w-32 bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                        />
                        <button
                          type="button"
                          onClick={() => handleRemoveSplitParticipantRow(i)}
                          disabled={splitForm.participants.length <= 1}
                          className="p-2 rounded-lg bg-surface-container hover:bg-error-container/20 text-on-surface-variant hover:text-error transition-all disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
                          title="Remover participante"
                        >
                          <span className="material-symbols-outlined text-sm">close</span>
                        </button>
                      </div>
                    ))}
                  </div>
                  <button
                    type="button"
                    onClick={handleAddSplitParticipantRow}
                    className="mt-sm flex items-center gap-xs text-primary font-label-md text-label-md hover:underline"
                  >
                    <span className="material-symbols-outlined text-[18px]">add</span>
                    Adicionar Participante
                  </button>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsSplitModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" disabled={savingSplit} className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                    {savingSplit ? 'Salvando...' : 'Adicionar'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Modal: Novo Timebox */}
      <AnimatePresence>
        {isTimeboxModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsTimeboxModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[440px]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">Novo Timebox</h3>
                <button onClick={() => setIsTimeboxModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSaveTimebox} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Título</label>
                  <input
                    required
                    type="text"
                    value={timeboxForm.title}
                    onChange={(e) => setTimeboxForm({ ...timeboxForm, title: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Início</label>
                  <input
                    required
                    type="datetime-local"
                    value={timeboxForm.start_time}
                    onChange={(e) => setTimeboxForm({ ...timeboxForm, start_time: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Fim</label>
                  <input
                    required
                    type="datetime-local"
                    value={timeboxForm.end_time}
                    onChange={(e) => setTimeboxForm({ ...timeboxForm, end_time: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsTimeboxModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" disabled={savingTimebox} className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                    {savingTimebox ? 'Salvando...' : 'Adicionar'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Modal: Novo OKR */}
      <AnimatePresence>
        {isOkrModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsOkrModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[480px] max-h-[85vh] overflow-y-auto"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">Novo OKR</h3>
                <button onClick={() => setIsOkrModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSaveOkr} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Objetivo</label>
                  <input
                    required
                    type="text"
                    value={okrForm.objective}
                    onChange={(e) => setOkrForm({ ...okrForm, objective: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>

                <div>
                  <label className="block text-label-md text-on-surface-variant mb-2">Resultados-chave (até {MAX_OKR_KEY_RESULTS})</label>
                  <div className="space-y-sm">
                    {okrForm.key_results.map((kr, i) => (
                      <div key={i} className="flex items-center gap-sm">
                        <input
                          required
                          type="text"
                          placeholder={`Resultado-chave ${i + 1}`}
                          value={kr}
                          onChange={(e) => handleOkrKeyResultChange(i, e.target.value)}
                          className="flex-1 bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                        />
                        <button
                          type="button"
                          onClick={() => handleRemoveOkrKeyResultRow(i)}
                          disabled={okrForm.key_results.length <= 1}
                          className="p-2 rounded-lg bg-surface-container hover:bg-error-container/20 text-on-surface-variant hover:text-error transition-all disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
                          title="Remover resultado-chave"
                        >
                          <span className="material-symbols-outlined text-sm">close</span>
                        </button>
                      </div>
                    ))}
                  </div>
                  <button
                    type="button"
                    onClick={handleAddOkrKeyResultRow}
                    disabled={okrForm.key_results.length >= MAX_OKR_KEY_RESULTS}
                    className="mt-sm flex items-center gap-xs text-primary font-label-md text-label-md hover:underline disabled:opacity-30 disabled:cursor-not-allowed disabled:no-underline"
                  >
                    <span className="material-symbols-outlined text-[18px]">add</span>
                    Adicionar Resultado-chave
                  </button>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsOkrModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" disabled={savingOkr} className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                    {savingOkr ? 'Salvando...' : 'Adicionar'}
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
