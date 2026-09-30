import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, Lock, User, Building, ShieldCheck, ChevronRight, Loader2, ArrowLeft } from 'lucide-react';
import api, { saveSession } from '../api';
import { clearPermissionsCache } from '../hooks/usePermissions';

export default function Register() {
  const [step, setStep] = useState<1 | 2>(1);
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [cnpjCpf, setCnpjCpf] = useState('');
  const [selectedPlan, setSelectedPlan] = useState('plan-empresarial');
  const [plans, setPlans] = useState<any[]>([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const res = await api.get('/plans/');
        setPlans(res.data);
      } catch (err) {
        console.error('Erro ao carregar planos', err);
      }
    };
    fetchPlans();
  }, []);

  const handleNext = (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName || !email || !password || !companyName) {
      setError('Por favor, preencha todos os campos obrigatórios.');
      return;
    }
    setError('');
    setStep(2);
  };

  const handleRegister = async () => {
    localStorage.removeItem('company');
    clearPermissionsCache();
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/auth/register', {
        full_name: fullName,
        email,
        password,
        company_name: companyName,
        cnpj_cpf: cnpjCpf,
        selected_plan: selectedPlan
      });

      saveSession(response.data);
      localStorage.setItem('user', JSON.stringify(response.data.user));

      try {
        const companyRes = await api.get('/company/');
        localStorage.setItem('company', JSON.stringify(companyRes.data));
      } catch (err) {
        console.error('Erro ao carregar dados da empresa', err);
      }

      // Redirect to payment checkout with selected plan
      navigate(`/checkout?plan=${selectedPlan}&cycle=monthly`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao realizar cadastro.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] flex flex-col justify-center items-center relative overflow-hidden font-sans p-4 sm:p-6" style={{ width: '100vw', minHeight: '100vh' }}>
      {/* Background decorations */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-blue-500/15 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-purple-500/15 rounded-full blur-[150px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="z-10"
        style={{ width: '100%', maxWidth: '580px', minWidth: '340px' }}
      >
        <div className="rounded-3xl shadow-2xl border border-white/10 bg-[#151926]/90 backdrop-blur-xl p-6 sm:p-10 w-full" style={{ width: '100%' }}>
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2 tracking-tight">
              Criar Conta no <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">TechConnect</span>
            </h1>
            <p className="text-slate-400 text-sm">
              {step === 1 ? 'Passo 1 de 2: Seus dados e da sua empresa' : 'Passo 2 de 2: Escolha seu plano ideal'}
            </p>
          </div>

          {/* Stepper Progress Bar */}
          <div className="flex items-center gap-2 mb-8">
            <div className={`flex-1 h-1.5 rounded-full transition-all ${step >= 1 ? 'bg-blue-500' : 'bg-white/10'}`} />
            <div className={`flex-1 h-1.5 rounded-full transition-all ${step === 2 ? 'bg-purple-500' : 'bg-white/10'}`} />
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded-xl mb-6 text-sm text-center">
              {error}
            </div>
          )}

          {step === 1 ? (
            <form onSubmit={handleNext} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Nome Completo *</label>
                <div className="relative">
                  <User className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-[#1c2130] border border-white/10 rounded-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Seu nome"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">E-mail Profissional *</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-[#1c2130] border border-white/10 rounded-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="seuemail@empresa.com.br"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Nome da Empresa *</label>
                <div className="relative">
                  <Building className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                  <input
                    type="text"
                    required
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-[#1c2130] border border-white/10 rounded-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Tech Solutions Ltda"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">CNPJ ou CPF da Empresa</label>
                <input
                  type="text"
                  value={cnpjCpf}
                  onChange={(e) => setCnpjCpf(e.target.value)}
                  className="w-full px-4 py-2.5 bg-[#1c2130] border border-white/10 rounded-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="00.000.000/0001-00"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Senha de Acesso *</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-[#1c2130] border border-white/10 rounded-xl text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="••••••••"
                  />
                </div>
                <p className="text-xs text-slate-500 mt-1">Mínimo de 8 caracteres, com letras e números.</p>
              </div>

              <button
                type="submit"
                className="w-full mt-4 flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold text-sm hover:opacity-90 transition-all shadow-lg shadow-blue-500/20"
              >
                Continuar para Seleção de Planos
                <ChevronRight size={18} />
              </button>
            </form>
          ) : (
            <div className="space-y-4">
              <p className="text-xs text-slate-300 font-medium mb-2">Selecione o plano desejado para sua conta:</p>

              {plans.map((plan) => (
                <div
                  key={plan.id}
                  onClick={() => setSelectedPlan(plan.id)}
                  className={`p-4 rounded-2xl border cursor-pointer transition-all relative overflow-hidden ${
                    selectedPlan === plan.id
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-white/10 bg-[#1c2130]/50 hover:border-white/20'
                  }`}
                >
                  {plan.popular && (
                    <div className="absolute top-0 right-0 bg-purple-600 text-white text-[10px] font-bold px-3 py-0.5 rounded-bl-lg">
                      Mais Recomendado
                    </div>
                  )}
                  <div className="flex justify-between items-center mb-1">
                    <h4 className="font-bold text-white text-base">{plan.name}</h4>
                    <span className="text-blue-400 font-bold text-sm">
                      R$ {plan.price_monthly.toFixed(2).replace('.', ',')}/mês
                    </span>
                  </div>
                  <p className="text-slate-400 text-xs">{plan.tagline}</p>
                </div>
              ))}

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setStep(1)}
                  className="flex items-center justify-center gap-1.5 px-4 py-3 rounded-xl border border-white/10 text-slate-300 hover:bg-white/5 text-sm font-semibold transition-all"
                >
                  <ArrowLeft size={16} /> Voltar
                </button>
                <button
                  type="button"
                  disabled={loading}
                  onClick={handleRegister}
                  className="flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition-all shadow-lg shadow-purple-500/20"
                >
                  {loading ? (
                    <Loader2 className="animate-spin" size={20} />
                  ) : (
                    <>
                      Ir para Pagamento
                      <ShieldCheck size={18} />
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          <div className="mt-8 text-center text-xs text-slate-400 border-t border-white/10 pt-4">
            Já possui uma conta?{' '}
            <Link to="/" className="text-blue-400 font-semibold hover:underline">
              Fazer Login
            </Link>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
