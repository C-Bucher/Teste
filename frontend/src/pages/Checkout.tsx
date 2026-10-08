import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CreditCard, QrCode, ShieldCheck, Lock, CheckCircle2, Loader2, ArrowLeft, Building2, Barcode, ExternalLink } from 'lucide-react';
import axios from 'axios';
import api from '../api';

type Method = 'pix' | 'boleto' | 'credit_card';

interface PlanDetails {
  name: string;
  tagline: string;
  price_monthly: number;
  price_yearly: number;
  features: string[];
}

interface CheckoutResult {
  provider: string;
  message: string;
  payment_url: string | null;
  plan_scope: string;
  subscription: { status: string; plan_name: string };
}

const METHODS: { id: Method; label: string; icon: typeof QrCode }[] = [
  { id: 'pix', label: 'Pix', icon: QrCode },
  { id: 'boleto', label: 'Boleto', icon: Barcode },
  { id: 'credit_card', label: 'Cartão', icon: CreditCard },
];

const brl = (v: number) => v.toFixed(2).replace('.', ',');

export default function Checkout() {
  const [searchParams] = useSearchParams();
  const planId = searchParams.get('plan') || 'plan-empresarial';
  const cycle = searchParams.get('cycle') === 'yearly' ? 'yearly' : 'monthly';
  const navigate = useNavigate();

  const [paymentMethod, setPaymentMethod] = useState<Method>('pix');
  const [companyName, setCompanyName] = useState('');
  const [cnpjCpf, setCnpjCpf] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CheckoutResult | null>(null);
  const [error, setError] = useState('');
  const [planDetails, setPlanDetails] = useState<PlanDetails | null>(null);

  useEffect(() => {
    // Visitors without an account sign up first, keeping the chosen plan.
    if (!localStorage.getItem('token')) navigate(`/cadastro?plan=${planId}`, { replace: true });
  }, [planId, navigate]);

  useEffect(() => {
    api.get(`/plans/${planId}`)
      .then((res) => setPlanDetails(res.data))
      .catch(() => setError('Plano não encontrado.'));
  }, [planId]);

  const price = planDetails ? (cycle === 'yearly' ? planDetails.price_yearly * 12 : planDetails.price_monthly) : 0;

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/payments/checkout', {
        plan_id: planId, billing_cycle: cycle, payment_method: paymentMethod, company_name: companyName || undefined, cnpj_cpf: cnpjCpf,
      });
      if (res.data.subscription.status === 'ACTIVE') {
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        localStorage.setItem('user', JSON.stringify({ ...user, plan_scope: res.data.plan_scope }));
      }
      setResult(res.data);
      // The provider's page collects the payment (Pix, boleto or card): card data never touches TechConnect.
      if (res.data.payment_url) window.open(res.data.payment_url, '_blank', 'noopener');
    } catch (err) {
      setError(axios.isAxiosError(err) ? err.response?.data?.detail || 'Erro ao iniciar o pagamento' : 'Erro ao iniciar o pagamento');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-white py-12 px-4 sm:px-6 lg:px-8 font-sans relative overflow-hidden" style={{ width: '100vw', minHeight: '100vh' }}>
      <div className="absolute top-0 left-1/3 w-[600px] h-[300px] bg-blue-500/10 blur-[150px] pointer-events-none rounded-full" />
      <div className="absolute bottom-0 right-10 w-[400px] h-[300px] bg-purple-500/10 blur-[150px] pointer-events-none rounded-full" />

      <div className="max-w-4xl mx-auto relative z-10">
        <button onClick={() => navigate('/planos')} className="flex items-center gap-2 text-sm text-slate-400 hover:text-white mb-6 transition-colors">
          <ArrowLeft size={16} /> Voltar para Planos
        </button>

        {result ? (
          <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
            className="bg-[#151926] border border-emerald-500/30 rounded-3xl p-8 text-center max-w-[32rem] mx-auto shadow-2xl">
            <div className="w-16 h-16 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-500/20">
              <CheckCircle2 size={36} />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">
              {result.subscription.status === 'ACTIVE' ? 'Assinatura ativa' : 'Falta só o pagamento'}
            </h2>
            <p className="text-slate-300 text-sm mb-6">
              {result.subscription.status === 'ACTIVE'
                ? result.message
                : 'Abrimos a página de pagamento em outra aba. Assim que o pagamento for confirmado, o plano é ativado sozinho — o Pix leva segundos, o boleto até 3 dias úteis. Enquanto isso, seu período de teste continua valendo.'}
            </p>
            {result.payment_url && (
              <a href={result.payment_url} target="_blank" rel="noopener noreferrer"
                className="w-full mb-3 inline-flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl border border-white/15 text-white font-semibold text-sm hover:bg-white/5 transition-all">
                Abrir página de pagamento <ExternalLink size={16} />
              </a>
            )}
            <button onClick={() => navigate('/dashboard')}
              className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold text-sm hover:opacity-90 transition-all shadow-lg shadow-blue-500/20">
              Ir para o painel
            </button>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
            <form onSubmit={handleCheckout} className="md:col-span-7 bg-[#151926]/90 border border-white/10 rounded-3xl p-6 sm:p-8 backdrop-blur-xl">
              <h2 className="text-2xl font-bold text-white mb-2">Pagamento</h2>
              <p className="text-slate-400 text-sm mb-6">
                O pagamento é feito na página segura do Asaas, nosso intermediador. O TechConnect não recebe nem guarda dados de cartão.
              </p>

              {error && <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded-xl mb-6 text-sm">{error}</div>}

              <p className="text-xs font-semibold text-slate-300 mb-2">Forma de pagamento</p>
              <div className="grid grid-cols-3 gap-3 mb-6">
                {METHODS.map(({ id, label, icon: Icon }) => (
                  <button key={id} type="button" onClick={() => setPaymentMethod(id)}
                    className={`flex flex-col items-center gap-1.5 py-3 rounded-xl border text-sm font-semibold transition-all ${
                      paymentMethod === id ? 'border-blue-500 bg-blue-500/10 text-white' : 'border-white/10 text-slate-400 hover:border-white/20'}`}>
                    <Icon size={20} /> {label}
                  </button>
                ))}
              </div>

              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">CPF ou CNPJ do pagador *</label>
                  <div className="relative">
                    <Building2 className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                    <input required value={cnpjCpf} onChange={(e) => setCnpjCpf(e.target.value)} placeholder="00.000.000/0001-00"
                      className="w-full pl-10 pr-4 py-2.5 bg-[#1c2130] border border-white/10 rounded-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Exigido para emitir a cobrança e a nota.</p>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Nome para a cobrança (opcional)</label>
                  <input value={companyName} onChange={(e) => setCompanyName(e.target.value)} placeholder="Razão social ou nome completo"
                    className="w-full px-4 py-2.5 bg-[#1c2130] border border-white/10 rounded-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500" />
                </div>
              </div>

              <button type="submit" disabled={loading || !planDetails}
                className="w-full flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold text-sm hover:opacity-90 transition-all shadow-lg shadow-blue-500/20 disabled:opacity-50">
                {loading ? <Loader2 className="animate-spin" size={18} /> : <><Lock size={16} /> Ir para o pagamento de R$ {brl(price)}</>}
              </button>
              <button type="button" onClick={() => navigate('/dashboard')} className="w-full mt-3 text-sm text-slate-400 hover:text-white">
                Continuar no período de teste
              </button>
              <p className="flex items-center justify-center gap-1.5 text-xs text-slate-500 mt-4"><ShieldCheck size={14} /> Cobrança recorrente; cancele quando quiser em Assinatura.</p>
            </form>

            <div className="md:col-span-5 bg-[#151926]/60 border border-white/10 rounded-3xl p-6 h-fit">
              <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">Resumo</h3>
              {planDetails && (
                <>
                  <p className="text-xl font-bold text-white">{planDetails.name}</p>
                  <p className="text-slate-400 text-sm mb-4">{planDetails.tagline}</p>
                  <ul className="space-y-2 mb-6 text-sm text-slate-300">
                    {planDetails.features.map((f) => <li key={f} className="flex gap-2"><CheckCircle2 size={16} className="text-emerald-400 shrink-0 mt-0.5" /> {f}</li>)}
                  </ul>
                  <div className="border-t border-white/10 pt-4 flex justify-between items-baseline">
                    <span className="text-slate-400 text-sm">{cycle === 'yearly' ? 'Total anual' : 'Total mensal'}</span>
                    <span className="text-2xl font-bold text-white">R$ {brl(price)}</span>
                  </div>
                  {cycle === 'yearly' && <p className="text-xs text-slate-500 text-right">equivale a R$ {brl(planDetails.price_yearly)}/mês</p>}
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
