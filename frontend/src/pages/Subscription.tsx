import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CreditCard, Calendar, CheckCircle2, Download, ArrowUpRight, ShieldCheck, RefreshCw } from 'lucide-react';
import api from '../api';
import Layout from '../components/Layout';

export default function Subscription() {
  const [sub, setSub] = useState<any>(null);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [subRes, invRes] = await Promise.all([
          api.get('/payments/subscription'),
          api.get('/payments/invoices')
        ]);
        setSub(subRes.data);
        setInvoices(invRes.data);
      } catch (err) {
        console.error('Erro ao carregar dados da assinatura', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <Layout>
        <div className="h-full flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-lg">
        {/* Page Header */}
        <div className="flex justify-between items-end mb-lg">
          <div>
            <h2 className="font-headline-md text-headline-md text-on-surface">Gestão de Assinatura e Faturamento</h2>
            <p className="text-on-surface-variant font-body-sm">
              Gerencie seu plano ativo, histórico de pagamentos e faturas fiscais.
            </p>
          </div>
          <button
            onClick={() => navigate('/planos')}
            className="bg-primary text-on-primary px-lg py-sm rounded-xl flex items-center gap-2 hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/20"
          >
            <RefreshCw size={16} /> Alterar ou Fazer Upgrade do Plano
          </button>
        </div>

        {/* Current Plan Overview Card */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-lg">
          <div className="md:col-span-8 glass-card p-lg rounded-2xl border border-primary/20 relative overflow-hidden flex flex-col justify-between">
            <div className="flex justify-between items-start mb-md">
              <div>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-success/10 text-success uppercase border border-success/20 inline-flex items-center gap-1">
                  <CheckCircle2 size={14} /> Assinatura Ativa
                </span>
                <h3 className="font-display-lg text-display-lg text-on-surface mt-2">
                  Plano {sub?.plan_name || 'Pro'}
                </h3>
                <p className="text-on-surface-variant text-body-sm">
                  Cobrança {sub?.billing_cycle === 'yearly' ? 'Anual' : 'Mensal'} autorizada para <span className="text-on-surface font-semibold">{sub?.company_name}</span>.
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-on-surface-variant">Valor da Mensalidade</p>
                <p className="font-display-lg text-display-lg text-primary">
                  R$ {sub?.amount?.toFixed(2).replace('.', ',') || '249,00'}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-md pt-md border-t border-border-subtle">
              <div className="flex items-center gap-sm">
                <Calendar className="text-primary" size={20} />
                <div>
                  <p className="text-xs text-on-surface-variant">Próxima Renovação</p>
                  <p className="font-label-md text-on-surface">
                    {sub?.current_period_end ? new Date(sub.current_period_end).toLocaleDateString('pt-BR') : '28/02/2026'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-sm">
                <CreditCard className="text-primary" size={20} />
                <div>
                  <p className="text-xs text-on-surface-variant">Método Cadastrado</p>
                  <p className="font-label-md text-on-surface">
                    {sub?.card_brand || 'Visa'} •••• {sub?.card_last4 || '4242'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-sm">
                <ShieldCheck className="text-success" size={20} />
                <div>
                  <p className="text-xs text-on-surface-variant">Renovação</p>
                  <p className="font-label-md text-success">Automática Ativada</p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Support & Usage */}
          <div className="md:col-span-4 glass-card p-lg rounded-2xl flex flex-col justify-between">
            <div>
              <h4 className="font-headline-sm text-headline-sm text-on-surface mb-xs">CFO Virtual IA</h4>
              <p className="text-xs text-on-surface-variant mb-md">
                Seu plano atual inclui consultas ilimitadas ao assistente de IA.
              </p>
              <div className="bg-surface-container-high p-md rounded-xl space-y-sm mb-md border border-border-subtle">
                <div className="flex justify-between text-xs font-label-md">
                  <span>Consultas Utilizadas neste mês:</span>
                  <span className="text-primary font-bold">142 / Ilimitado</span>
                </div>
                <div className="w-full bg-surface-bright h-2 rounded-full overflow-hidden">
                  <div className="bg-primary h-full w-[40%] rounded-full" />
                </div>
              </div>
            </div>

            <button
              onClick={() => navigate('/planos')}
              className="w-full py-2.5 bg-surface-bright hover:bg-surface-container-highest text-primary font-label-md rounded-xl transition-all border border-border-subtle flex items-center justify-center gap-2"
            >
              Ver Tabela Completa de Recursos <ArrowUpRight size={16} />
            </button>
          </div>
        </div>

        {/* Invoice History Table */}
        <div className="glass-card rounded-2xl overflow-hidden border border-border-subtle">
          <div className="p-lg border-b border-border-subtle flex justify-between items-center">
            <div>
              <h4 className="font-headline-sm text-headline-sm text-on-surface">Histórico de Faturas e Notas Fiscais</h4>
              <p className="text-xs text-on-surface-variant">Baixe os comprovantes e documentos em PDF.</p>
            </div>
            <span className="text-xs text-outline font-mono">Total de faturas: {invoices.length}</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-container-low/50 border-b border-border-subtle">
                  <th className="p-md font-label-md text-on-surface-variant">Número da Fatura</th>
                  <th className="p-md font-label-md text-on-surface-variant">Descrição</th>
                  <th className="p-md font-label-md text-on-surface-variant">Data</th>
                  <th className="p-md font-label-md text-on-surface-variant">Status</th>
                  <th className="p-md font-label-md text-on-surface-variant text-right">Valor</th>
                  <th className="p-md font-label-md text-on-surface-variant text-right">Download</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-surface-bright transition-colors">
                    <td className="p-md font-mono text-sm font-semibold text-primary">{inv.id}</td>
                    <td className="p-md text-sm text-on-surface">{inv.description}</td>
                    <td className="p-md text-sm text-on-surface-variant">
                      {new Date(inv.date).toLocaleDateString('pt-BR')}
                    </td>
                    <td className="p-md">
                      <span className="px-sm py-0.5 rounded-full text-[10px] font-bold bg-success/10 text-success uppercase">
                        Pago
                      </span>
                    </td>
                    <td className="p-md text-right font-bold text-on-surface">
                      R$ {inv.amount.toFixed(2).replace('.', ',')}
                    </td>
                    <td className="p-md text-right">
                      <button
                        onClick={() => alert(`Download da fatura ${inv.id} iniciado.`)}
                        className="p-2 text-primary hover:bg-primary-container/20 rounded-lg transition-all inline-flex items-center gap-1 text-xs font-semibold"
                      >
                        <Download size={14} /> PDF
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </motion.div>
    </Layout>
  );
}
