import { useState } from 'react';
import api from '../api';
import { motion } from 'framer-motion';
import { Navigate } from 'react-router-dom';
import Layout from '../components/Layout';

// ---------------------------------------------------------------------------
// M8-IA — three independent AI-consultant tools sharing one page: CFO Virtual
// (business-scoped analogue of HubPessoal.tsx's "CFO Pessoal IA" tab),
// Conciliação Bancária (mocked file-upload → per-line AI categorization) and
// Gerador de Orçamentos (briefing → cost/price/margin estimate).
// ---------------------------------------------------------------------------
const TABS = [
  { id: 'cfo-virtual', label: 'CFO Virtual', icon: 'auto_awesome' },
  { id: 'conciliacao', label: 'Conciliação Bancária', icon: 'account_balance' },
  { id: 'orcamentos', label: 'Gerador de Orçamentos', icon: 'request_quote' },
] as const;

type TabId = (typeof TABS)[number]['id'];

interface CfoInsight {
  type: 'OPORTUNIDADE' | 'ALERTA';
  title: string;
  description: string;
  impact: string;
  urgency: string;
}

// The mock backend doesn't parse files — selecting any file simulates these
// three fixed transaction descriptions being read off a statement.
const SIMULATED_TRANSACTIONS = ['Uber - transporte', 'Amazon AWS', 'Assinatura Spotify'];

interface ConciliationRow {
  description: string;
  suggested_category: string;
  confidence: number;
  status: string;
}

interface ProposalResult {
  estimated_internal_cost: number;
  suggested_price: number;
  margin_percentage: number;
}

const formatCurrency = (value: number | undefined | null) =>
  (value ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 });

const CFO_INSIGHT_CONFIG: Record<
  CfoInsight['type'],
  { label: string; icon: string; badge: string; border: string }
> = {
  OPORTUNIDADE: {
    label: 'Oportunidade',
    icon: 'trending_up',
    badge: 'bg-success/10 text-success',
    border: 'border-l-success',
  },
  ALERTA: { label: 'Alerta', icon: 'warning', badge: 'bg-error/10 text-error', border: 'border-l-error' },
};

export default function IAEmpresarial() {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const isFuncionario = user.role === 'FUNCIONARIO';

  if (isFuncionario) {
    return <Navigate to="/dashboard" />;
  }

  const [activeTab, setActiveTab] = useState<TabId>('cfo-virtual');

  // CFO Virtual
  const [cfoInsights, setCfoInsights] = useState<CfoInsight[] | null>(null);
  const [cfoLoading, setCfoLoading] = useState(false);

  // Conciliação Bancária
  const [conciliationRows, setConciliationRows] = useState<ConciliationRow[]>([]);
  const [conciliationLoading, setConciliationLoading] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  // Gerador de Orçamentos
  const [briefing, setBriefing] = useState('');
  const [markup, setMarkup] = useState('');
  const [proposal, setProposal] = useState<ProposalResult | null>(null);
  const [proposalLoading, setProposalLoading] = useState(false);

  const handleGenerateCfoInsights = async () => {
    setCfoLoading(true);
    try {
      const res = await api.post('/ai/consultant/cfo', {});
      setCfoInsights(res.data.insights || []);
    } catch (err) {
      console.error('Erro ao gerar análise do CFO Virtual', err);
      alert('Erro ao gerar análise');
    } finally {
      setCfoLoading(false);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setConciliationLoading(true);
    setConciliationRows([]);
    try {
      const results = await Promise.all(
        SIMULATED_TRANSACTIONS.map(async (description) => {
          const res = await api.post('/ai/consultant/conciliation', { description });
          const result = res.data.results?.[0];
          return {
            description: result?.description ?? description,
            suggested_category: result?.suggested_category ?? '-',
            confidence: result?.confidence ?? 0,
            status: result?.status ?? 'PENDENTE',
          } as ConciliationRow;
        })
      );
      setConciliationRows(results);
    } catch (err) {
      console.error('Erro ao conciliar transações', err);
      alert('Erro ao processar arquivo de conciliação');
    } finally {
      setConciliationLoading(false);
      // Reset the input value so selecting the same file again re-triggers onChange.
      e.target.value = '';
    }
  };

  const handleRowDecision = (index: number, decision: 'APROVADO' | 'REJEITADO') => {
    setConciliationRows((prev) => prev.map((row, i) => (i === index ? { ...row, status: decision } : row)));
  };

  const handleGenerateProposal = async (e: React.FormEvent) => {
    e.preventDefault();
    setProposalLoading(true);
    try {
      const res = await api.post('/ai/consultant/proposal', {
        briefing,
        markup: Number(markup || 0),
      });
      setProposal(res.data);
    } catch (err) {
      console.error('Erro ao gerar orçamento', err);
      alert('Erro ao gerar orçamento');
    } finally {
      setProposalLoading(false);
    }
  };

  return (
    <Layout>
      {/* Page Header */}
      <div className="mb-xl">
        <nav className="flex text-body-sm text-outline mb-xs gap-xs items-center">
          <span>Empresa</span>
          <span className="material-symbols-outlined text-[12px]">chevron_right</span>
          <span className="text-primary">IA Empresarial</span>
        </nav>
        <h2 className="font-display-lg text-display-lg text-on-surface">IA Empresarial</h2>
        <p className="text-on-surface-variant text-body-base mt-xs">
          Ferramentas de IA para decisões financeiras: análise de CFO virtual, conciliação bancária automática e
          geração de orçamentos.
        </p>
      </div>

      {/* Tab bar */}
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

      {(() => {
        switch (activeTab) {
          // ---------------------------------------------------------------
          case 'cfo-virtual':
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
                        <span className="font-headline-sm text-headline-sm text-primary">CFO Virtual</span>
                      </div>
                      <p className="text-body-sm text-on-surface-variant max-w-[36rem]">
                        Peça uma análise inteligente das finanças da empresa: oportunidades de crescimento e alertas
                        de risco de fluxo de caixa, com impacto e urgência estimados.
                      </p>
                    </div>
                    <button
                      onClick={handleGenerateCfoInsights}
                      disabled={cfoLoading}
                      className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10 disabled:opacity-50 shrink-0"
                    >
                      {cfoLoading ? (
                        <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-on-primary"></span>
                      ) : (
                        <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
                          auto_awesome
                        </span>
                      )}
                      {cfoLoading ? 'Analisando...' : 'Gerar Análise'}
                    </button>
                  </div>
                </div>

                {cfoLoading && (
                  <div className="flex justify-center py-xl">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                )}

                {!cfoLoading && cfoInsights && (
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
                          </div>
                          <h4 className="font-headline-sm text-headline-sm text-on-surface mb-xs">{insight.title}</h4>
                          <p className="text-body-sm text-on-surface-variant mb-md">{insight.description}</p>
                          <div className="flex gap-lg text-xs text-on-surface-variant pt-sm border-t border-border-subtle">
                            <span>
                              Impacto: <b className="text-on-surface">{insight.impact}</b>
                            </span>
                            <span>
                              Urgência: <b className="text-on-surface">{insight.urgency}</b>
                            </span>
                          </div>
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
              </motion.div>
            );

          // ---------------------------------------------------------------
          case 'conciliacao':
            return (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-lg">
                <div className="glass-card p-xl rounded-xl border border-primary/20 ai-aura relative overflow-hidden">
                  <div className="absolute -right-6 -top-6 opacity-10">
                    <span
                      className="material-symbols-outlined text-[160px] text-primary"
                      style={{ fontVariationSettings: "'FILL' 1" }}
                    >
                      account_balance
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
                        <span className="font-headline-sm text-headline-sm text-primary">Conciliação Bancária</span>
                      </div>
                      <p className="text-body-sm text-on-surface-variant max-w-[36rem]">
                        Envie um extrato (CSV/OFX) e deixe a IA sugerir a categoria de cada transação com um nível de
                        confiança — aprove ou rejeite cada sugestão.
                      </p>
                    </div>
                    <label
                      className={`flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10 shrink-0 cursor-pointer ${
                        conciliationLoading ? 'opacity-50 pointer-events-none' : ''
                      }`}
                    >
                      {conciliationLoading ? (
                        <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-on-primary"></span>
                      ) : (
                        <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
                          upload_file
                        </span>
                      )}
                      {conciliationLoading ? 'Processando...' : 'Importar Extrato'}
                      <input
                        type="file"
                        accept=".csv,.ofx"
                        onChange={handleFileChange}
                        disabled={conciliationLoading}
                        className="hidden"
                      />
                    </label>
                  </div>
                  {fileName && (
                    <p className="relative z-10 text-xs text-on-surface-variant mt-md">
                      Arquivo selecionado: <span className="text-on-surface font-medium">{fileName}</span>
                    </p>
                  )}
                </div>

                {conciliationLoading && (
                  <div className="flex justify-center py-xl">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                )}

                {!conciliationLoading && conciliationRows.length > 0 && (
                  <div className="glass-panel bg-surface/60 border border-border-subtle rounded-xl overflow-hidden">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="bg-surface-container-highest/30 border-b border-border-subtle">
                          <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Descrição</th>
                          <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">
                            Categoria Sugerida
                          </th>
                          <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Confiança</th>
                          <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant text-right">
                            Ações
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border-subtle/50">
                        {conciliationRows.map((row, i) => {
                          const isConfident = row.confidence >= 0.6;
                          const decided = row.status === 'APROVADO' || row.status === 'REJEITADO';
                          return (
                            <motion.tr
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ delay: i * 0.05 }}
                              key={i}
                              className="group hover:bg-surface-bright/40 transition-colors"
                            >
                              <td className="px-lg py-md text-label-md text-on-surface">{row.description}</td>
                              <td className="px-lg py-md">
                                <span className="inline-flex items-center px-2 py-1 rounded-full bg-secondary-container/40 text-on-surface-variant text-[11px] font-bold uppercase tracking-wider">
                                  {row.suggested_category}
                                </span>
                              </td>
                              <td className="px-lg py-md">
                                <span
                                  className={`inline-flex items-center gap-xs px-2 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider ${
                                    isConfident ? 'bg-success/10 text-success' : 'bg-error/10 text-error'
                                  }`}
                                >
                                  <span
                                    className={`w-1.5 h-1.5 rounded-full ${isConfident ? 'bg-success' : 'bg-error'}`}
                                  ></span>
                                  {(row.confidence * 100).toFixed(0)}%
                                </span>
                              </td>
                              <td className="px-lg py-md text-right">
                                {decided ? (
                                  <span
                                    className={`inline-flex items-center gap-xs px-sm py-1 rounded-full text-[11px] font-bold uppercase tracking-wider ${
                                      row.status === 'APROVADO'
                                        ? 'bg-success/10 text-success'
                                        : 'bg-error/10 text-error'
                                    }`}
                                  >
                                    {row.status === 'APROVADO' ? 'Aprovado' : 'Rejeitado'}
                                  </span>
                                ) : (
                                  <div className="flex justify-end gap-sm">
                                    <button
                                      onClick={() => handleRowDecision(i, 'APROVADO')}
                                      className="px-sm py-1.5 rounded-lg bg-success/10 text-success hover:bg-success/20 transition-all font-label-md text-label-md"
                                    >
                                      Aprovar
                                    </button>
                                    <button
                                      onClick={() => handleRowDecision(i, 'REJEITADO')}
                                      className="px-sm py-1.5 rounded-lg bg-error/10 text-error hover:bg-error/20 transition-all font-label-md text-label-md"
                                    >
                                      Rejeitar
                                    </button>
                                  </div>
                                )}
                              </td>
                            </motion.tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}

                {!conciliationLoading && conciliationRows.length === 0 && (
                  <div className="glass-card p-xl rounded-xl text-center text-on-surface-variant">
                    Nenhuma transação conciliada ainda. Importe um extrato para começar.
                  </div>
                )}
              </motion.div>
            );

          // ---------------------------------------------------------------
          case 'orcamentos':
            return (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-lg">
                <div className="glass-card p-xl rounded-xl border border-primary/20 ai-aura relative overflow-hidden">
                  <div className="absolute -right-6 -top-6 opacity-10">
                    <span
                      className="material-symbols-outlined text-[160px] text-primary"
                      style={{ fontVariationSettings: "'FILL' 1" }}
                    >
                      request_quote
                    </span>
                  </div>
                  <div className="relative z-10">
                    <div className="flex items-center gap-sm mb-md">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary to-secondary flex items-center justify-center">
                        <span
                          className="material-symbols-outlined text-on-primary text-[20px]"
                          style={{ fontVariationSettings: "'FILL' 1" }}
                        >
                          auto_awesome
                        </span>
                      </div>
                      <span className="font-headline-sm text-headline-sm text-primary">Gerador de Orçamentos</span>
                    </div>
                    <p className="text-body-sm text-on-surface-variant max-w-[36rem] mb-lg">
                      Descreva o escopo do projeto e a IA estima o custo interno, o preço sugerido ao cliente e a
                      margem resultante.
                    </p>

                    <form onSubmit={handleGenerateProposal} className="space-y-md max-w-2xl">
                      <div>
                        <label className="block text-label-md text-on-surface-variant mb-1">
                          Briefing do Projeto
                        </label>
                        <textarea
                          required
                          rows={4}
                          value={briefing}
                          onChange={(e) => setBriefing(e.target.value)}
                          placeholder="Ex: Desenvolvimento de landing page com integração de pagamentos e painel administrativo..."
                          className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none resize-none"
                        />
                      </div>
                      <div className="max-w-[20rem]">
                        <label className="block text-label-md text-on-surface-variant mb-1">Markup (%)</label>
                        <input
                          required
                          type="number"
                          min="0"
                          step="0.1"
                          value={markup}
                          onChange={(e) => setMarkup(e.target.value)}
                          placeholder="Ex: 40"
                          className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                        />
                      </div>
                      <button
                        type="submit"
                        disabled={proposalLoading}
                        className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10 disabled:opacity-50"
                      >
                        {proposalLoading ? (
                          <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-on-primary"></span>
                        ) : (
                          <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>
                            auto_awesome
                          </span>
                        )}
                        {proposalLoading ? 'Gerando...' : 'Gerar Orçamento'}
                      </button>
                    </form>
                  </div>
                </div>

                {proposalLoading && (
                  <div className="flex justify-center py-xl">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  </div>
                )}

                {!proposalLoading && proposal && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-lg">
                    <div className="glass-card p-lg rounded-xl">
                      <span className="text-on-surface-variant font-label-md">Custo Interno Estimado</span>
                      <h3 className="font-display-lg text-display-lg text-on-surface mt-sm">
                        R$ {formatCurrency(proposal.estimated_internal_cost)}
                      </h3>
                    </div>
                    <div className="glass-card p-lg rounded-xl">
                      <span className="text-on-surface-variant font-label-md">Preço Sugerido</span>
                      <h3 className="font-display-lg text-display-lg text-primary mt-sm">
                        R$ {formatCurrency(proposal.suggested_price)}
                      </h3>
                    </div>
                    <div className="glass-card p-lg rounded-xl">
                      <span className="text-on-surface-variant font-label-md">Margem</span>
                      <h3 className="font-display-lg text-display-lg text-success mt-sm">
                        {proposal.margin_percentage.toFixed(1)}%
                      </h3>
                    </div>
                  </div>
                )}
              </motion.div>
            );

          default:
            return null;
        }
      })()}
    </Layout>
  );
}
