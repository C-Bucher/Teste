import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CreditCard, QrCode, ShieldCheck, Lock, CheckCircle2, Loader2, ArrowLeft, Building2 } from 'lucide-react';
import api from '../api';

export default function Checkout() {
  const [searchParams] = useSearchParams();
  const planId = searchParams.get('plan') || 'plan-pro';
  const cycle = searchParams.get('cycle') || 'monthly';
  const navigate = useNavigate();

  const [paymentMethod, setPaymentMethod] = useState<'credit_card' | 'pix'>('credit_card');
  const [cardNumber, setCardNumber] = useState('');
  const [cardName, setCardName] = useState('');
  const [cardExpiry, setCardExpiry] = useState('');
  const [cardCvv, setCardCvv] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [cnpjCpf, setCnpjCpf] = useState('');

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState<any>(null);
  const [error, setError] = useState('');
  const [planDetails, setPlanDetails] = useState<any>(null);

  useEffect(() => {
    const fetchPlanDetails = async () => {
      try {
        const res = await api.get(`/plans/${planId}`);
        setPlanDetails(res.data);
      } catch (err) {
        console.error('Erro ao carregar detalhes do plano', err);
      }
    };
    fetchPlanDetails();
  }, [planId]);

  const price = planDetails
    ? cycle === 'yearly'
      ? planDetails.price_yearly * 12
      : planDetails.price_monthly
    : 0;

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await api.post('/payments/checkout', {
        plan_id: planId,
        billing_cycle: cycle,
        payment_method: paymentMethod,
        card_number: cardNumber,
        card_name: cardName,
        card_expiry: cardExpiry,
        card_cvv: cardCvv,
        company_name: companyName,
        cnpj_cpf: cnpjCpf
      });

      setSuccess(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao processar pagamento');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-white py-12 px-4 sm:px-6 lg:px-8 font-sans relative overflow-hidden" style={{ width: '100vw', minHeight: '100vh' }}>
      {/* Background glow */}
      <div className="absolute top-0 left-1/3 w-[600px] h-[300px] bg-blue-500/10 blur-[150px] pointer-events-none rounded-full" />
      <div className="absolute bottom-0 right-10 w-[400px] h-[300px] bg-purple-500/10 blur-[150px] pointer-events-none rounded-full" />

      <div className="max-w-4xl mx-auto relative z-10">
        <button
          onClick={() => navigate('/planos')}
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeft size={16} /> Voltar para Planos
        </button>

        {success ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-[#151926] border border-emerald-500/30 rounded-3xl p-8 text-center max-w-lg mx-auto shadow-2xl"
          >
            <div className="w-16 h-16 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-500/20">
              <CheckCircle2 size={36} />
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Assinatura Concluída com Sucesso!</h2>
            <p className="text-slate-300 text-sm mb-6">{success.message}</p>

            {success.pix_code && (
              <div className="bg-[#1c2130] p-4 rounded-xl mb-6 text-left border border-white/10">
                <p className="text-xs font-semibold text-slate-400 mb-2 uppercase">Código PIX Copia e Cola:</p>
                <div className="bg-[#0B0F19] p-3 rounded-lg text-xs font-mono text-emerald-400 break-all select-all border border-white/5">
                  {success.pix_code}
                </div>
              </div>
            )}

            <button
              onClick={() => navigate('/dashboard')}
              className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold text-sm hover:opacity-90 transition-all shadow-lg shadow-blue-500/20"
            >
              Acessar Painel Principal (Dashboard)
            </button>
          </motion.div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
            {/* Payment Form */}
            <div className="md:col-span-7 bg-[#151926]/90 border border-white/10 rounded-3xl p-6 sm:p-8 backdrop-blur-xl">
              <h2 className="text-2xl font-bold text-white mb-2">Checkout de Pagamento</h2>
              <p className="text-slate-400 text-sm mb-6">Ambiente de pagamento seguro com criptografia de 256 bits.</p>

              {error && (
                <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded-xl mb-6 text-sm">
                  {error}
                </div>
              )}

              {/* Payment Method Selector */}
              <div className="grid grid-cols-2 gap-3 mb-6">
                <button
                  type="button"
                  onClick={() => setPaymentMethod('credit_card')}
                  className={`flex items-center justify-center gap-2 p-3.5 rounded-xl border text-sm font-semibold transition-all ${
                    paymentMethod === 'credit_card'
                      ? 'border-blue-500 bg-blue-500/10 text-white'
                      : 'border-white/10 bg-[#1c2130]/50 text-slate-400 hover:text-white'
                  }`}
                >
                  <CreditCard size={18} /> Cartão de Crédito
                </button>
                <button
                  type="button"
                  onClick={() => setPaymentMethod('pix')}
                  className={`flex items-center justify-center gap-2 p-3.5 rounded-xl border text-sm font-semibold transition-all ${
                    paymentMethod === 'pix'
                      ? 'border-emerald-500 bg-emerald-500/10 text-emerald-400'
                      : 'border-white/10 bg-[#1c2130]/50 text-slate-400 hover:text-white'
                  }`}
                >
                  <QrCode size={18} /> PIX (Aprovação Instantânea)
                </button>
              </div>

              <form onSubmit={handleCheckout} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Razão Social / Nome Fantasia</label>
                  <div className="relative">
                    <Building2 className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                    <input
                      type="text"
                      required
                      value={companyName}
                      onChange={(e) => setCompanyName(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 bg-[#1c2130] border border-white/10 rounded-xl text-sm text-white focus:ring-2 focus:ring-blue-500 outline-none"
                      placeholder="TechConnect Soluções Ltda"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">CNPJ ou CPF para Nota Fiscal</label>
                  <input
                    type="text"
                    required
                    value={cnpjCpf}
                    onChange={(e) => setCnpjCpf(e.target.value)}
                    className="w-full px-4 py-2.5 bg-[#1c2130] border border-white/10 rounded-xl text-sm text-white focus:ring-2 focus:ring-blue-500 outline-none"
                    placeholder="00.000.000/0001-00"
                  />
                </div>

                {paymentMethod === 'credit_card' ? (
                  <>
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">Número do Cartão</label>
                      <input
                        type="text"
                        required
                        maxLength={19}
                        value={cardNumber}
                        onChange={(e) => setCardNumber(e.target.value)}
                        className="w-full px-4 py-2.5 bg-[#1c2130] border border-white/10 rounded-xl text-sm text-white focus:ring-2 focus:ring-blue-500 outline-none font-mono"
                        placeholder="4532 •••• •••• 8888"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">Nome como impresso no Cartão</label>
                      <input
                        type="text"
                        required
                        value={cardName}
                        onChange={(e) => setCardName(e.target.value)}
                        className="w-full px-4 py-2.5 bg-[#1c2130] border border-white/10 rounded-xl text-sm text-white focus:ring-2 focus:ring-blue-500 outline-none uppercase"
                        placeholder="CARLOS A MENDES"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-semibold text-slate-300 mb-1">Validade (MM/AA)</label>
                        <input
                          type="text"
                          required
                          maxLength={5}
                          value={cardExpiry}
                          onChange={(e) => setCardExpiry(e.target.value)}
                          className="w-full px-4 py-2.5 bg-[#1c2130] border border-white/10 rounded-xl text-sm text-white focus:ring-2 focus:ring-blue-500 outline-none text-center"
                          placeholder="12/28"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-slate-300 mb-1">CVV</label>
                        <input
                          type="password"
                          required
                          maxLength={4}
                          value={cardCvv}
                          onChange={(e) => setCardCvv(e.target.value)}
                          className="w-full px-4 py-2.5 bg-[#1c2130] border border-white/10 rounded-xl text-sm text-white focus:ring-2 focus:ring-blue-500 outline-none text-center font-mono"
                          placeholder="123"
                        />
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="bg-emerald-500/10 border border-emerald-500/20 p-4 rounded-2xl text-center space-y-2">
                    <QrCode className="mx-auto text-emerald-400" size={48} />
                    <p className="text-sm font-semibold text-emerald-300">Ao clicar abaixo, um QR Code PIX será gerado instantaneamente.</p>
                    <p className="text-xs text-slate-400">Liberação imediata assim que a transferência for identificada.</p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-6 py-3.5 px-4 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white font-bold text-sm hover:opacity-90 disabled:opacity-50 transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20"
                >
                  {loading ? (
                    <Loader2 className="animate-spin" size={20} />
                  ) : (
                    <>
                      <Lock size={16} /> Confirmar e Pagar R$ {price.toFixed(2).replace('.', ',')}
                    </>
                  )}
                </button>

                <p className="text-[11px] text-slate-500 text-center flex items-center justify-center gap-1 mt-2">
                  <ShieldCheck size={14} className="text-emerald-400" /> Garantia incondicional de 7 dias com devolução integral.
                </p>
              </form>
            </div>

            {/* Order Summary */}
            <div className="md:col-span-5 space-y-6">
              <div className="bg-[#151926]/90 border border-white/10 rounded-3xl p-6 backdrop-blur-xl">
                <h3 className="text-lg font-bold text-white mb-4 pb-3 border-b border-white/10">Resumo da Assinatura</h3>

                {planDetails ? (
                  <div className="space-y-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-bold text-white text-base">Plano {planDetails.name}</h4>
                        <p className="text-xs text-slate-400">{cycle === 'yearly' ? 'Cobrança Anual (-20%)' : 'Cobrança Mensal'}</p>
                      </div>
                      <span className="text-lg font-extrabold text-blue-400">
                        R$ {price.toFixed(2).replace('.', ',')}
                      </span>
                    </div>

                    <div className="border-t border-white/10 pt-4 space-y-2 text-xs text-slate-300">
                      <p className="font-semibold uppercase text-slate-400 tracking-wider">Recursos Inclusos:</p>
                      {planDetails.features.map((feat: string, idx: number) => (
                        <p key={idx} className="flex items-center gap-2">
                          <CheckCircle2 size={14} className="text-emerald-400 shrink-0" />
                          <span>{feat}</span>
                        </p>
                      ))}
                    </div>

                    <div className="border-t border-white/10 pt-4 flex justify-between items-center font-bold text-white text-base">
                      <span>Total Hoje:</span>
                      <span className="text-xl text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                        R$ {price.toFixed(2).replace('.', ',')}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="py-8 text-center text-slate-400 text-sm">Carregando resumo do plano...</div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
