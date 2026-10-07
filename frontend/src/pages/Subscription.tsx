import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Calendar, CheckCircle2, ArrowUpRight, RefreshCw, AlertTriangle, Clock, ExternalLink, XCircle } from 'lucide-react';
import axios from 'axios';
import api from '../api';
import Layout from '../components/Layout';
import { useToast } from '../context/ToastContext';
import { useConfirm } from '../context/ConfirmContext';

interface Sub {
  plan_name: string;
  company_name: string;
  billing_cycle: string;
  amount: number;
  status: 'TRIAL' | 'PENDING' | 'ACTIVE' | 'PAST_DUE' | 'CANCELED';
  payment_method: string | null;
  trial_ends_at: string | null;
  current_period_end: string;
  pending_payment_url: string | null;
  access: { allowed: boolean };
}

interface Invoice {
  id: string;
  description: string;
  amount: number;
  status: 'PAID' | 'PENDING' | 'OVERDUE' | 'CANCELED' | 'REFUNDED';
  date: string;
  due_date: string | null;
  payment_url: string | null;
}

interface Usage {
  bank_connections: { used: number; limit: number };
  ai_queries: { used: number; limit: number };
}

const STATUS: Record<Sub['status'], { label: string; cls: string; icon: typeof CheckCircle2 }> = {
  TRIAL: { label: 'Período de teste', cls: 'bg-primary/10 text-primary border-primary/20', icon: Clock },
  PENDING: { label: 'Aguardando pagamento', cls: 'bg-warning/10 text-warning border-warning/20', icon: Clock },
  ACTIVE: { label: 'Assinatura ativa', cls: 'bg-success/10 text-success border-success/20', icon: CheckCircle2 },
  PAST_DUE: { label: 'Pagamento em atraso', cls: 'bg-error/10 text-error border-error/20', icon: AlertTriangle },
  CANCELED: { label: 'Cancelada', cls: 'bg-surface-container-highest text-on-surface-variant border-border-subtle', icon: XCircle },
};

const INVOICE_STATUS: Record<Invoice['status'], { label: string; cls: string }> = {
  PAID: { label: 'Pago', cls: 'bg-success/10 text-success' },
  PENDING: { label: 'Em aberto', cls: 'bg-warning/10 text-warning' },
  OVERDUE: { label: 'Vencido', cls: 'bg-error/10 text-error' },
  CANCELED: { label: 'Cancelado', cls: 'bg-surface-container-highest text-on-surface-variant' },
  REFUNDED: { label: 'Estornado', cls: 'bg-surface-container-highest text-on-surface-variant' },
};

const brl = (v: number) => v.toFixed(2).replace('.', ',');
const fmt = (iso: string | null) => (iso ? new Date(iso.length === 10 ? `${iso}T12:00:00` : iso).toLocaleDateString('pt-BR') : '—');

function Meter({ label, used, limit }: { label: string; used: number; limit: number }) {
  const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  return (
    <div className="space-y-xs">
      <div className="flex justify-between text-xs font-label-md">
        <span className="text-on-surface-variant">{label}</span>
        <span className="text-on-surface font-bold">{limit === -1 ? `${used} / sem limite` : limit === 0 ? 'não incluso' : `${used} / ${limit}`}</span>
      </div>
      {limit > 0 && (
        <div className="w-full bg-surface-bright h-2 rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${pct >= 90 ? 'bg-error' : 'bg-primary'}`} style={{ width: `${pct}%` }} />
        </div>
      )}
    </div>
  );
}

export default function Subscription() {
  const [sub, setSub] = useState<Sub | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const toast = useToast();
  const confirm = useConfirm();
  let role = '';
  try { role = JSON.parse(localStorage.getItem('user') || '{}').role || ''; } catch { /* sessão inválida */ }

  const load = useCallback(async () => {
    try {
      const [subRes, invRes, useRes] = await Promise.all([
        api.get('/payments/subscription'), api.get('/payments/invoices'), api.get('/payments/usage'),
      ]);
      setSub(subRes.data);
      setInvoices(invRes.data);
      setUsage(useRes.data);
    } catch {
      toast.error('Erro ao carregar a assinatura.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleCancel = async () => {
    const ok = await confirm({
      title: 'Cancelar assinatura',
      message: 'As próximas cobranças deixam de ser geradas. Você continua usando o sistema até o fim do período já pago; os dados não são apagados.',
      confirmLabel: 'Cancelar assinatura',
      isDestructive: true,
    });
    if (!ok) return;
    try {
      await api.post('/payments/cancel');
      toast.success('Assinatura cancelada.');
      await load();
    } catch (err) {
      toast.error(axios.isAxiosError(err) ? err.response?.data?.detail || 'Erro ao cancelar.' : 'Erro ao cancelar.');
    }
  };

  if (loading || !sub) {
    return (
      <Layout>
        <div className="h-full flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </Layout>
    );
  }

  const status = STATUS[sub.status] ?? STATUS.ACTIVE;
  const StatusIcon = status.icon;
  const endLabel = sub.status === 'TRIAL' ? 'Teste termina em' : sub.status === 'CANCELED' ? 'Acesso até' : 'Próxima renovação';
  const endDate = sub.status === 'TRIAL' ? sub.trial_ends_at : sub.current_period_end;

  return (
    <Layout>
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-lg">
        {(params.get('bloqueado') || !sub.access.allowed) && (
          <div className="p-md rounded-xl border border-error/40 bg-error/5 text-body-sm text-on-surface flex items-start gap-sm">
            <AlertTriangle className="text-error shrink-0" size={18} />
            <span>O acesso aos módulos está suspenso porque {sub.status === 'TRIAL' ? 'o período de teste terminou' : 'há um pagamento pendente'}. Escolha um plano ou pague a cobrança em aberto para voltar a usar o sistema — seus dados estão preservados.</span>
          </div>
        )}

        <div className="flex flex-col md:flex-row md:justify-between md:items-end gap-md">
          <div>
            <h2 className="font-headline-md text-headline-md text-on-surface">Assinatura e faturamento</h2>
            <p className="text-on-surface-variant font-body-sm">Plano, cobranças e consumo da sua conta.</p>
          </div>
          {role === 'ADMIN' && (
            <button onClick={() => navigate('/planos')}
              className="bg-primary text-on-primary px-lg py-sm rounded-xl flex items-center gap-2 hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/20">
              <RefreshCw size={16} /> {sub.status === 'ACTIVE' ? 'Mudar de plano' : 'Escolher plano e pagar'}
            </button>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-lg">
          <div className="md:col-span-8 glass-card p-lg rounded-2xl border border-primary/20 flex flex-col justify-between gap-md">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-md">
              <div>
                <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase border inline-flex items-center gap-1 ${status.cls}`}>
                  <StatusIcon size={14} /> {status.label}
                </span>
                <h3 className="font-display-lg text-display-lg text-on-surface mt-2">Plano {sub.plan_name}</h3>
                <p className="text-on-surface-variant text-body-sm">
                  {sub.status === 'TRIAL' ? 'Teste gratuito' : `Cobrança ${sub.billing_cycle === 'yearly' ? 'anual' : 'mensal'}`} · {sub.company_name}
                </p>
              </div>
              {sub.status !== 'TRIAL' && (
                <div className="sm:text-right">
                  <p className="text-xs text-on-surface-variant">{sub.billing_cycle === 'yearly' ? 'Valor anual' : 'Valor mensal'}</p>
                  <p className="font-display-lg text-display-lg text-primary">R$ {brl(sub.amount)}</p>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-md pt-md border-t border-border-subtle">
              <div className="flex items-center gap-sm">
                <Calendar className="text-primary" size={20} />
                <div>
                  <p className="text-xs text-on-surface-variant">{endLabel}</p>
                  <p className="font-label-md text-on-surface">{fmt(endDate)}</p>
                </div>
              </div>
              {sub.pending_payment_url && (
                <a href={sub.pending_payment_url} target="_blank" rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 px-md py-2 rounded-xl bg-warning/10 text-warning hover:bg-warning/20 font-label-md">
                  Pagar cobrança em aberto <ExternalLink size={16} />
                </a>
              )}
            </div>
            {role === 'ADMIN' && ['ACTIVE', 'PAST_DUE', 'PENDING'].includes(sub.status) && (
              <button onClick={handleCancel} className="self-start text-xs text-on-surface-variant hover:text-error hover:underline">Cancelar assinatura</button>
            )}
          </div>

          <div className="md:col-span-4 glass-card p-lg rounded-2xl flex flex-col justify-between gap-md">
            <div className="space-y-md">
              <h4 className="font-headline-sm text-headline-sm text-on-surface">Consumo do mês</h4>
              {usage && (
                <>
                  <Meter label="Perguntas à IA" used={usage.ai_queries.used} limit={usage.ai_queries.limit} />
                  <Meter label="Bancos conectados" used={usage.bank_connections.used} limit={usage.bank_connections.limit} />
                </>
              )}
            </div>
            <button onClick={() => navigate('/planos')}
              className="w-full py-2.5 bg-surface-bright hover:bg-surface-container-highest text-primary font-label-md rounded-xl transition-all border border-border-subtle flex items-center justify-center gap-2">
              Comparar planos <ArrowUpRight size={16} />
            </button>
          </div>
        </div>

        <div className="glass-card rounded-2xl overflow-hidden border border-border-subtle">
          <div className="p-lg border-b border-border-subtle flex justify-between items-center">
            <div>
              <h4 className="font-headline-sm text-headline-sm text-on-surface">Cobranças</h4>
              <p className="text-xs text-on-surface-variant">Histórico de cobranças da empresa.</p>
            </div>
            <span className="text-xs text-outline font-mono">{invoices.length} cobrança(s)</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-container-low/50 border-b border-border-subtle">
                  <th className="p-md font-label-md text-on-surface-variant">Descrição</th>
                  <th className="p-md font-label-md text-on-surface-variant">Vencimento</th>
                  <th className="p-md font-label-md text-on-surface-variant">Situação</th>
                  <th className="p-md font-label-md text-on-surface-variant text-right">Valor</th>
                  <th className="p-md font-label-md text-on-surface-variant text-right"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {invoices.length === 0 && (
                  <tr><td colSpan={5} className="p-lg text-center text-on-surface-variant text-body-sm">Nenhuma cobrança ainda.</td></tr>
                )}
                {invoices.map((inv) => {
                  const st = INVOICE_STATUS[inv.status] ?? INVOICE_STATUS.PENDING;
                  return (
                    <tr key={inv.id} className="hover:bg-surface-bright transition-colors">
                      <td className="p-md text-sm text-on-surface">{inv.description}</td>
                      <td className="p-md text-sm text-on-surface-variant">{fmt(inv.due_date || inv.date)}</td>
                      <td className="p-md"><span className={`px-sm py-0.5 rounded-full text-[10px] font-bold uppercase ${st.cls}`}>{st.label}</span></td>
                      <td className="p-md text-right font-bold text-on-surface">R$ {brl(inv.amount)}</td>
                      <td className="p-md text-right">
                        {inv.payment_url && inv.status !== 'PAID' && (
                          <a href={inv.payment_url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline text-label-md">Pagar</a>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </motion.div>
    </Layout>
  );
}
