import { useState, useEffect } from 'react';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import api from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { Navigate, useSearchParams } from 'react-router-dom';
import Layout from '../components/Layout';
import { usePermissions } from '../hooks/usePermissions';
import { useToast } from '../context/ToastContext';

type Tab = 'lancamentos' | 'dre' | 'fluxo-caixa';

interface FinancialEntry {
  id: string;
  type: 'RECEITA' | 'DESPESA';
  amount: number;
  description: string;
  due_date: string;
  payment_date: string | null;
  status: 'PAGO' | 'PENDENTE';
  category?: string;
  supplier_id?: string;
  cost_center?: string;
}

interface DreCategory {
  categoria: string;
  total: number;
}

interface DreData {
  period: { start: string; end: string };
  total_receitas: number;
  total_despesas: number;
  receitas: DreCategory[];
  despesas: DreCategory[];
  resultado_liquido: number;
  margem_percentual: number;
}

interface CashflowItem {
  date: string;
  receitas: number;
  despesas: number;
  saldo_acumulado: number;
}

interface CashflowData {
  items: CashflowItem[];
  saldo_atual: number;
  receitas_previstas_30d: number;
  despesas_previstas_30d: number;
  projected_balance: number;
  alert_level: 'VERDE' | 'AMARELO' | 'VERMELHO';
}

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: 'lancamentos', label: 'Lançamentos', icon: 'receipt_long' },
  { id: 'dre', label: 'DRE', icon: 'analytics' },
  { id: 'fluxo-caixa', label: 'Fluxo de Caixa D+90', icon: 'trending_up' },
];

const CATEGORY_COLORS = ['bg-secondary', 'bg-primary', 'bg-tertiary', 'bg-outline'];

const ALERT_CONFIG: Record<CashflowData['alert_level'], { classes: string; icon: string; label: string }> = {
  VERDE: { classes: 'bg-success/10 text-success', icon: 'check_circle', label: 'Saúde financeira estável' },
  AMARELO: { classes: 'bg-warning/10 text-warning', icon: 'warning', label: 'Atenção ao fluxo de caixa' },
  VERMELHO: { classes: 'bg-error/10 text-error', icon: 'error', label: 'Risco de caixa negativo' },
};

const formatCurrency = (value: number | undefined | null) =>
  (value ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 });

const formatDate = (value: string | null | undefined) => {
  if (!value) return '-';
  const [y, m, d] = value.split('-');
  if (!y || !m || !d) return value;
  return `${d}/${m}/${y}`;
};

const formatShortDate = (value: string) => {
  const [, m, d] = value.split('-');
  if (!m || !d) return value;
  return `${d}/${m}`;
};

const EMPTY_ENTRY_FORM = {
  type: 'RECEITA' as 'RECEITA' | 'DESPESA',
  description: '',
  amount: '',
  category: '',
  cost_center: '',
  due_date: '',
};

function FinanceiroContent() {
  const toast = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  const tabFromUrl = searchParams.get('tab') as Tab | null;
  const [activeTab, setActiveTab] = useState<Tab>(tabFromUrl && ['lancamentos', 'dre', 'fluxo-caixa'].includes(tabFromUrl) ? tabFromUrl : 'lancamentos');

  // Lançamentos
  const [entries, setEntries] = useState<FinancialEntry[]>([]);
  const [entriesLoading, setEntriesLoading] = useState(true);
  const [filterType, setFilterType] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [entryForm, setEntryForm] = useState(EMPTY_ENTRY_FORM);
  const [saving, setSaving] = useState(false);
  const [payingId, setPayingId] = useState<string | null>(null);

  // DRE
  const [dre, setDre] = useState<DreData | null>(null);
  const [dreLoading, setDreLoading] = useState(true);

  // Fluxo de Caixa
  const [cashflow, setCashflow] = useState<CashflowData | null>(null);
  const [cashflowLoading, setCashflowLoading] = useState(true);

  const fetchEntries = async () => {
    setEntriesLoading(true);
    try {
      const params: Record<string, string | number> = { page, size: 20 };
      if (filterType) params.type = filterType;
      if (filterStatus) params.status = filterStatus;
      if (search) params.search = search;
      const res = await api.get('/financial/entries', { params });
      setEntries(res.data.items);
      setPages(res.data.pages || 1);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error('Erro ao carregar lançamentos', err);
    } finally {
      setEntriesLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchEntries();
    }, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterType, filterStatus, search, page]);

  useEffect(() => {
    setPage(1);
  }, [filterType, filterStatus, search]);

  const fetchDre = async () => {
    setDreLoading(true);
    try {
      const res = await api.get('/financial/dre');
      setDre(res.data);
    } catch (err) {
      console.error('Erro ao carregar DRE', err);
    } finally {
      setDreLoading(false);
    }
  };

  const fetchCashflow = async () => {
    setCashflowLoading(true);
    try {
      const res = await api.get('/financial/cashflow');
      setCashflow(res.data);
    } catch (err) {
      console.error('Erro ao carregar fluxo de caixa', err);
    } finally {
      setCashflowLoading(false);
    }
  };

  useEffect(() => {
    fetchDre();
    fetchCashflow();
  }, []);

  // Re-fetch DRE / Fluxo de Caixa whenever those tabs become active, so
  // mutations made in "Lançamentos" (novo lançamento, marcar como pago)
  // are reflected without requiring a full page reload.
  useEffect(() => {
    if (activeTab === 'dre') {
      fetchDre();
    }
    if (activeTab === 'fluxo-caixa') {
      fetchCashflow();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const handleAddNew = () => {
    setEntryForm(EMPTY_ENTRY_FORM);
    setIsModalOpen(true);
  };

  const handleSaveEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post('/financial/entries', {
        type: entryForm.type,
        description: entryForm.description,
        amount: Number(entryForm.amount),
        category: entryForm.category,
        cost_center: entryForm.cost_center,
        due_date: entryForm.due_date,
      });
      setIsModalOpen(false);
      toast.success('Lançamento criado com sucesso.');
      if (page !== 1) {
        setPage(1);
      } else {
        fetchEntries();
      }
    } catch (err) {
      console.error('Erro ao criar lançamento', err);
      toast.error('Erro ao criar lançamento.');
    } finally {
      setSaving(false);
    }
  };

  const handleMarkAsPaid = async (id: string) => {
    setPayingId(id);
    try {
      const res = await api.post(`/financial/entries/${id}/pay`);
      setEntries((prev) => prev.map((en) => (en.id === id ? res.data : en)));
      toast.success('Lançamento marcado como pago.');
    } catch (err) {
      console.error('Erro ao marcar como pago', err);
      toast.error('Erro ao marcar lançamento como pago.');
    } finally {
      setPayingId(null);
    }
  };

  const maxReceita = Math.max(1, ...(dre?.receitas.map((r) => r.total) || [1]));
  const maxDespesa = Math.max(1, ...(dre?.despesas.map((d) => d.total) || [1]));

  return (
    <Layout>
      {/* Page Header */}
      <div className="mb-xl">
        <nav className="flex text-body-sm text-outline mb-xs gap-xs items-center">
          <span>Empresa</span>
          <span className="material-symbols-outlined text-[12px]">chevron_right</span>
          <span className="text-primary">Financeiro</span>
        </nav>
        <h2 className="font-display-lg text-display-lg text-on-surface">Financeiro</h2>
        <p className="text-on-surface-variant text-body-base mt-xs">
          Controle lançamentos, acompanhe o resultado do período e projete o fluxo de caixa.
        </p>
      </div>

      {/* Tab bar */}
      <div className="inline-flex flex-wrap bg-surface-container-low p-1 rounded-lg border border-border-subtle mb-xl gap-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id);
              setSearchParams({ tab: tab.id });
            }}
            className={`flex items-center gap-sm px-lg py-2 rounded-md transition-all font-label-md text-label-md ${
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

      {/* Aba: Lançamentos */}
      {activeTab === 'lancamentos' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          {/* Filters */}
          <div className="flex flex-wrap items-center gap-md mb-lg">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface text-label-md focus:border-primary focus:ring-1 focus:ring-primary outline-none"
            >
              <option value="">Todos os Tipos</option>
              <option value="RECEITA">Receita</option>
              <option value="DESPESA">Despesa</option>
            </select>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface text-label-md focus:border-primary focus:ring-1 focus:ring-primary outline-none"
            >
              <option value="">Todos os Status</option>
              <option value="PAGO">Pago</option>
              <option value="PENDENTE">Pendente</option>
            </select>
            <div className="flex items-center bg-surface-container-low rounded-full px-md py-2 border border-border-subtle min-w-[220px] flex-1 max-w-[24rem]">
              <span className="material-symbols-outlined text-outline text-[18px]">search</span>
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar por descrição, categoria..."
                className="bg-transparent border-none focus:ring-0 text-body-sm w-full text-on-surface focus:outline-none px-sm"
              />
            </div>
            <button
              onClick={handleAddNew}
              className="ml-auto flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10"
            >
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>add</span>
              Novo Lançamento
            </button>
          </div>

          {/* Table */}
          <div className="glass-panel bg-surface/60 border border-border-subtle rounded-xl overflow-hidden">
            <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full min-w-[820px] text-left border-collapse">
              <thead>
                <tr className="bg-surface-container-highest/30 border-b border-border-subtle">
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Descrição</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Tipo</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Categoria</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Vencimento</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Status</th>
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
                    className="hover:bg-surface-bright/40 transition-colors"
                  >
                    <td className="px-lg py-md text-label-md text-on-surface">{en.description}</td>
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
                    <td className="px-lg py-md">
                      <span className="inline-flex items-center px-2 py-1 rounded-full bg-secondary-container/40 text-on-surface-variant text-[11px] font-bold uppercase tracking-wider">
                        {en.category || '-'}
                      </span>
                    </td>
                    <td className="px-lg py-md text-on-surface-variant font-label-md text-label-md">{formatDate(en.due_date)}</td>
                    <td className="px-lg py-md">
                      <span
                        className={`inline-flex items-center gap-xs px-2 py-1 rounded-full ${
                          en.status === 'PAGO' ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'
                        } text-[11px] font-bold uppercase tracking-wider`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${en.status === 'PAGO' ? 'bg-success' : 'bg-warning'}`}></span>
                        {en.status === 'PAGO' ? 'Pago' : 'Pendente'}
                      </span>
                    </td>
                    <td className={`px-lg py-md text-right font-bold ${en.type === 'RECEITA' ? 'text-success' : 'text-error'}`}>
                      {en.type === 'RECEITA' ? '+' : '-'} R$ {formatCurrency(en.amount)}
                    </td>
                    <td className="px-lg py-md text-right">
                      {en.status === 'PENDENTE' && (
                        <button
                          onClick={() => handleMarkAsPaid(en.id)}
                          disabled={payingId === en.id}
                          className="inline-flex items-center gap-xs px-3 py-1.5 rounded-lg bg-success/10 text-success hover:bg-success/20 transition-all text-[12px] font-bold disabled:opacity-50"
                        >
                          <span className="material-symbols-outlined text-[16px]">task_alt</span>
                          {payingId === en.id ? 'Marcando...' : 'Marcar como Pago'}
                        </button>
                      )}
                    </td>
                  </motion.tr>
                ))}
                {!entriesLoading && entries.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-on-surface-variant">
                      Nenhum lançamento encontrado.
                    </td>
                  </tr>
                )}
                {entriesLoading && (
                  <tr>
                    <td colSpan={7} className="py-12 text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            </div>

            {/* Pagination */}
            {!entriesLoading && entries.length > 0 && (
              <div className="flex justify-between items-center px-lg py-md border-t border-border-subtle">
                <span className="text-body-sm text-on-surface-variant">
                  {total} lançamento{total !== 1 ? 's' : ''} · Página {page} de {pages}
                </span>
                <div className="flex gap-sm">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="px-4 py-1.5 rounded-lg font-label-md text-label-md bg-surface-container hover:bg-surface-bright transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Anterior
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(pages, p + 1))}
                    disabled={page >= pages}
                    className="px-4 py-1.5 rounded-lg font-label-md text-label-md bg-surface-container hover:bg-surface-bright transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Próxima
                  </button>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Aba: DRE */}
      {activeTab === 'dre' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          {dreLoading || !dre ? (
            <div className="flex justify-center py-xl">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <>
              {/* KPI cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-lg mb-xl">
                <div className="glass-card p-lg rounded-xl">
                  <span className="text-on-surface-variant font-label-md">Receita Total</span>
                  <h3 className="font-display-lg text-display-lg text-success mt-sm">R$ {formatCurrency(dre.total_receitas)}</h3>
                  <p className="text-xs text-on-surface-variant mt-sm">Período: {formatDate(dre.period.start)} - {formatDate(dre.period.end)}</p>
                </div>
                <div className="glass-card p-lg rounded-xl">
                  <span className="text-on-surface-variant font-label-md">Despesa Total</span>
                  <h3 className="font-display-lg text-display-lg text-error mt-sm">R$ {formatCurrency(dre.total_despesas)}</h3>
                  <p className="text-xs text-on-surface-variant mt-sm">Período: {formatDate(dre.period.start)} - {formatDate(dre.period.end)}</p>
                </div>
                <div className="glass-card p-lg rounded-xl">
                  <div className="flex justify-between items-start mb-sm">
                    <span className="text-on-surface-variant font-label-md">Resultado Líquido</span>
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                        dre.margem_percentual >= 0 ? 'bg-success/10 text-success' : 'bg-error/10 text-error'
                      }`}
                    >
                      Margem {dre.margem_percentual}%
                    </span>
                  </div>
                  <h3
                    className={`font-display-lg text-display-lg mt-sm ${
                      dre.resultado_liquido >= 0 ? 'text-on-surface' : 'text-error'
                    }`}
                  >
                    R$ {formatCurrency(dre.resultado_liquido)}
                  </h3>
                </div>
              </div>

              {/* Category breakdowns */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-lg">
                <div className="glass-card p-lg rounded-xl">
                  <h4 className="font-headline-sm text-headline-sm mb-xl">Receitas por Categoria</h4>
                  <div className="space-y-lg">
                    {dre.receitas.map((r, i) => (
                      <div key={r.categoria}>
                        <div className="flex justify-between mb-sm">
                          <span className="text-label-md font-label-md">{r.categoria}</span>
                          <span className="text-label-md font-bold">R$ {formatCurrency(r.total)}</span>
                        </div>
                        <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
                          <div
                            className={`h-full ${CATEGORY_COLORS[i % CATEGORY_COLORS.length]} rounded-full`}
                            style={{ width: `${Math.max(4, (r.total / maxReceita) * 100)}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                    {dre.receitas.length === 0 && (
                      <p className="text-on-surface-variant text-body-sm">Nenhuma receita categorizada.</p>
                    )}
                  </div>
                </div>

                <div className="glass-card p-lg rounded-xl">
                  <h4 className="font-headline-sm text-headline-sm mb-xl">Despesas por Categoria</h4>
                  <div className="space-y-lg">
                    {dre.despesas.map((d, i) => (
                      <div key={d.categoria}>
                        <div className="flex justify-between mb-sm">
                          <span className="text-label-md font-label-md">{d.categoria}</span>
                          <span className="text-label-md font-bold">R$ {formatCurrency(d.total)}</span>
                        </div>
                        <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
                          <div
                            className={`h-full ${CATEGORY_COLORS[i % CATEGORY_COLORS.length]} rounded-full`}
                            style={{ width: `${Math.max(4, (d.total / maxDespesa) * 100)}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                    {dre.despesas.length === 0 && (
                      <p className="text-on-surface-variant text-body-sm">Nenhuma despesa categorizada.</p>
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </motion.div>
      )}

      {/* Aba: Fluxo de Caixa D+90 */}
      {activeTab === 'fluxo-caixa' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          {cashflowLoading || !cashflow ? (
            <div className="flex justify-center py-xl">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <>
              {/* Alert banner */}
              <div className={`flex items-center gap-md p-lg rounded-xl border border-border-subtle mb-lg ${ALERT_CONFIG[cashflow.alert_level].classes}`}>
                <span className="material-symbols-outlined text-[32px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                  {ALERT_CONFIG[cashflow.alert_level].icon}
                </span>
                <div>
                  <p className="font-label-md text-label-md uppercase tracking-wider opacity-80">
                    {ALERT_CONFIG[cashflow.alert_level].label}
                  </p>
                  <p className="font-headline-sm text-headline-sm">
                    Saldo projetado em 90 dias: R$ {formatCurrency(cashflow.projected_balance)}
                  </p>
                </div>
              </div>

              {/* Mini stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-lg mb-lg">
                <div className="glass-card p-lg rounded-xl">
                  <span className="text-on-surface-variant font-label-md">Saldo Atual</span>
                  <h3 className="font-display-lg text-display-lg text-on-surface mt-sm">R$ {formatCurrency(cashflow.saldo_atual)}</h3>
                </div>
                <div className="glass-card p-lg rounded-xl">
                  <span className="text-on-surface-variant font-label-md">Receitas Previstas (30d)</span>
                  <h3 className="font-display-lg text-display-lg text-success mt-sm">R$ {formatCurrency(cashflow.receitas_previstas_30d)}</h3>
                </div>
                <div className="glass-card p-lg rounded-xl">
                  <span className="text-on-surface-variant font-label-md">Despesas Previstas (30d)</span>
                  <h3 className="font-display-lg text-display-lg text-error mt-sm">R$ {formatCurrency(cashflow.despesas_previstas_30d)}</h3>
                </div>
              </div>

              {/* Area chart */}
              <div className="glass-card p-lg rounded-xl min-h-[400px] flex flex-col">
                <div className="flex justify-between items-center mb-xl">
                  <h4 className="font-headline-sm text-headline-sm">Projeção de Fluxo de Caixa (D+90)</h4>
                  <div className="flex gap-md">
                    <div className="flex items-center gap-xs">
                      <div className="w-3 h-3 rounded-full bg-primary"></div>
                      <span className="text-xs text-on-surface-variant">Receitas</span>
                    </div>
                    <div className="flex items-center gap-xs">
                      <div className="w-3 h-3 rounded-full bg-tertiary"></div>
                      <span className="text-xs text-on-surface-variant">Despesas</span>
                    </div>
                  </div>
                </div>

                <div className="w-full flex-1">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={cashflow.items} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorReceitasCF" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#adc6ff" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#adc6ff" stopOpacity={0}/>
                        </linearGradient>
                        <linearGradient id="colorDespesasCF" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#ffb786" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#ffb786" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                      <XAxis
                        dataKey="date"
                        stroke="#8c909f"
                        tick={{ fill: '#8c909f', fontSize: 12 }}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={formatShortDate}
                        interval={Math.ceil(cashflow.items.length / 10)}
                      />
                      <YAxis stroke="#8c909f" tick={{ fill: '#8c909f', fontSize: 12 }} axisLine={false} tickLine={false} />
                      <Tooltip
                        contentStyle={{ backgroundColor: 'rgba(28, 31, 42, 0.9)', borderColor: 'rgba(255, 255, 255, 0.1)', borderRadius: '0.75rem', color: '#dfe2f1', backdropFilter: 'blur(8px)' }}
                        itemStyle={{ color: '#dfe2f1' }}
                        labelFormatter={(label) => formatDate(String(label ?? ''))}
                        formatter={(value) => `R$ ${formatCurrency(Number(value))}`}
                      />
                      <Area type="monotone" dataKey="receitas" stroke="#adc6ff" strokeWidth={3} fillOpacity={1} fill="url(#colorReceitasCF)" />
                      <Area type="monotone" dataKey="despesas" stroke="#ffb786" strokeWidth={3} fillOpacity={1} fill="url(#colorDespesasCF)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          )}
        </motion.div>
      )}

      {/* Modal: Novo Lançamento */}
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
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[500px]"
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
                    onChange={(e) => setEntryForm({ ...entryForm, type: e.target.value as 'RECEITA' | 'DESPESA' })}
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
                <div className="grid grid-cols-2 gap-4">
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
                    <label className="block text-label-md text-on-surface-variant mb-1">Vencimento</label>
                    <input
                      required
                      type="date"
                      value={entryForm.due_date}
                      onChange={(e) => setEntryForm({ ...entryForm, due_date: e.target.value })}
                      className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-label-md text-on-surface-variant mb-1">Categoria</label>
                    <input
                      type="text"
                      value={entryForm.category}
                      onChange={(e) => setEntryForm({ ...entryForm, category: e.target.value })}
                      className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-label-md text-on-surface-variant mb-1">Centro de Custo</label>
                    <input
                      type="text"
                      value={entryForm.cost_center}
                      onChange={(e) => setEntryForm({ ...entryForm, cost_center: e.target.value })}
                      className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                    />
                  </div>
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
    </Layout>
  );
}

export default function Financeiro() {
  const { loading, can } = usePermissions();
  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </Layout>
    );
  }
  if (!can('financeiro')) return <Navigate to="/dashboard" />;
  return <FinanceiroContent />;
}
