import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Check, Zap, ArrowRight, Building2, HelpCircle } from 'lucide-react';
import api from '../api';
import type { Plan } from '../types';

export default function Plans() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [yearly, setYearly] = useState(true);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const res = await api.get('/plans/');
        setPlans(res.data);
      } catch (err) {
        console.error('Erro ao carregar planos', err);
      } finally {
        setLoading(false);
      }
    };
    fetchPlans();
  }, []);

  const handleSelectPlan = (planId: string) => {
    navigate(`/checkout?plan=${planId}&cycle=${yearly ? 'yearly' : 'monthly'}`);
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-white py-12 px-4 sm:px-6 lg:px-8 font-sans relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-blue-600/10 blur-[160px] pointer-events-none rounded-full" />
      <div className="absolute bottom-0 right-10 w-[500px] h-[300px] bg-purple-600/10 blur-[150px] pointer-events-none rounded-full" />

      <div className="max-w-7xl mx-auto relative z-10">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
            <span className="px-3.5 py-1.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase tracking-widest inline-block mb-4">
              Planos e Preços
            </span>
            <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-4 text-white">
              Escolha o plano ideal para alavancar a saúde financeira do seu negócio
            </h1>
            <p className="text-slate-400 text-lg">
              Potencialize a gestão financeira com o suporte contínuo do **CFO Virtual com IA**. Cancele ou altere a qualquer momento.
            </p>
          </motion.div>

          {/* Toggle Mensal / Anual */}
          <div className="mt-8 flex items-center justify-center gap-4">
            <span className={`text-sm font-medium ${!yearly ? 'text-white' : 'text-slate-400'}`}>Mensal</span>
            <button
              onClick={() => setYearly(!yearly)}
              className="relative w-16 h-8 rounded-full bg-[#1c2130] border border-white/10 p-1 transition-colors"
            >
              <div
                className={`w-6 h-6 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 transition-transform ${
                  yearly ? 'translate-x-8' : 'translate-x-0'
                }`}
              />
            </button>
            <div className="flex items-center gap-1.5">
              <span className={`text-sm font-medium ${yearly ? 'text-white' : 'text-slate-400'}`}>Anual</span>
              <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs px-2 py-0.5 rounded-full font-bold">
                Economize até 20%
              </span>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
          </div>
        ) : (
          /* Cards Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-16">
            {plans.map((plan) => {
              const price = yearly ? plan.price_yearly : plan.price_monthly;
              return (
                <motion.div
                  key={plan.id}
                  whileHover={{ y: -8 }}
                  transition={{ duration: 0.2 }}
                  className={`relative rounded-3xl p-8 bg-[#151926]/90 border backdrop-blur-xl flex flex-col justify-between ${
                    plan.popular
                      ? 'border-blue-500/50 shadow-2xl shadow-blue-500/10 bg-gradient-to-b from-[#1a2035] to-[#131725]'
                      : 'border-white/10'
                  }`}
                >
                  {plan.popular && (
                    <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-xs font-bold px-4 py-1 rounded-full shadow-lg flex items-center gap-1">
                      <Zap size={14} /> Recomendado
                    </div>
                  )}

                  <div>
                    <h3 className="text-2xl font-bold text-white mb-2">{plan.name}</h3>
                    <p className="text-slate-400 text-sm mb-6 min-h-[40px]">{plan.tagline}</p>

                    <div className="mb-6">
                      <div className="flex items-baseline gap-1">
                        <span className="text-xs text-slate-400">R$</span>
                        <span className="text-4xl font-extrabold text-white tracking-tight">
                          {price.toFixed(2).replace('.', ',')}
                        </span>
                        <span className="text-slate-400 text-sm">/mês</span>
                      </div>
                      {yearly && (
                        <p className="text-xs text-blue-400 mt-1 font-medium">
                          Cobrado anualmente (R$ {(price * 12).toFixed(2).replace('.', ',')}/ano)
                        </p>
                      )}
                    </div>

                    <div className="space-y-3 mb-8 border-t border-white/10 pt-6">
                      <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                        Recursos inclusos:
                      </p>
                      {plan.features.map((feature: string, idx: number) => (
                        <div key={idx} className="flex items-start gap-3">
                          <div className="w-5 h-5 rounded-full bg-blue-500/10 text-blue-400 flex items-center justify-center shrink-0 mt-0.5 border border-blue-500/20">
                            <Check size={12} />
                          </div>
                          <span className="text-sm text-slate-300">{feature}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <button
                    onClick={() => handleSelectPlan(plan.id)}
                    className={`w-full py-3.5 px-4 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all ${
                      plan.popular
                        ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:opacity-90 shadow-lg shadow-blue-500/25'
                        : 'bg-white/10 text-white hover:bg-white/20 border border-white/10'
                    }`}
                  >
                    Assinar {plan.name}
                    <ArrowRight size={16} />
                  </button>
                </motion.div>
              );
            })}
          </div>
        )}

        {/* Enterprise Banner */}
        <div className="rounded-3xl border border-white/10 bg-[#151926]/60 p-8 flex flex-col md:flex-row items-center justify-between gap-6 backdrop-blur-xl mb-16">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-purple-500/10 border border-purple-500/20 text-purple-400 flex items-center justify-center shrink-0">
              <Building2 size={28} />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white mb-1">Precisa de uma solução customizada para sua empresa?</h3>
              <p className="text-slate-400 text-sm">
                Oferecemos implantação personalizada, treinamento para equipes e modelo de dados isolado no ambiente Enterprise.
              </p>
            </div>
          </div>
          <button
            onClick={() => handleSelectPlan('plan-completo')}
            className="whitespace-nowrap px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-sm transition-all shadow-lg shadow-purple-600/20"
          >
            Falar com Especialistas
          </button>
        </div>

        {/* FAQ Section */}
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-white text-center mb-8 flex items-center justify-center gap-2">
            <HelpCircle className="text-blue-400" size={24} /> Perguntas Frequentes
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-[#151926]/80 p-6 rounded-2xl border border-white/5">
              <h4 className="font-semibold text-white mb-2">Posso alterar meu plano a qualquer momento?</h4>
              <p className="text-slate-400 text-sm">
                Sim! Você pode realizar o upgrade ou downgrade diretamente pelo painel de assinaturas. Os créditos restantes serão abatidos proporcionalmente.
              </p>
            </div>
            <div className="bg-[#151926]/80 p-6 rounded-2xl border border-white/5">
              <h4 className="font-semibold text-white mb-2">Como funciona a garantia e reembolso?</h4>
              <p className="text-slate-400 text-sm">
                Oferecemos 7 dias de garantia incondicional. Se você não estiver satisfeito com o CFO Virtual IA, devolvemos 100% do valor.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
