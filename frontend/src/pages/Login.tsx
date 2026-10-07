import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api, { saveSession } from '../api';
import { clearPermissionsCache } from '../hooks/usePermissions';
import { motion } from 'framer-motion';
import { Mail, Lock, ChevronRight, Loader2, User, Shield, Briefcase } from 'lucide-react';
import axios from 'axios';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mfaToken, setMfaToken] = useState('');
  const [mfaCode, setMfaCode] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.removeItem('company');
    clearPermissionsCache();
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/auth/login', { email, password });
      if (response.data.mfa_required) {
        setMfaToken(response.data.mfa_token);
        return;
      }
      await finishLogin(response.data);
    } catch (err) {
      setError(axios.isAxiosError(err) ? err.response?.data?.detail || 'Erro ao realizar login' : 'Erro ao realizar login');
    } finally {
      setLoading(false);
    }
  };

  const handleMfa = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const response = await api.post('/auth/login/mfa', { mfa_token: mfaToken, code: mfaCode });
      await finishLogin(response.data);
    } catch (err) {
      const status = axios.isAxiosError(err) ? err.response?.status : undefined;
      if (status === 401 && axios.isAxiosError(err) && err.response?.data?.detail !== 'Código de verificação inválido') {
        setMfaToken(''); // the 5-minute step expired: back to the password
      }
      setError(axios.isAxiosError(err) ? err.response?.data?.detail || 'Código inválido' : 'Código inválido');
    } finally {
      setLoading(false);
    }
  };

  const finishLogin = async (data: { user: { role: string }; access_token: string; refresh_token?: string }) => {
    saveSession(data);
    localStorage.setItem('user', JSON.stringify(data.user));
    try {
      const companyRes = await api.get('/company/');
      localStorage.setItem('company', JSON.stringify(companyRes.data));
      if (data.user.role === 'ADMIN' && companyRes.data.onboarding_completed === false) {
        navigate('/onboarding');
        return;
      }
    } catch (err) {
      console.error('Erro ao carregar dados da empresa', err);
    }
    navigate('/dashboard');
  };

  const autofill = (role: 'admin' | 'gerente' | 'funcionario') => {
    if (role === 'admin') {
      setEmail('admin@techconnect.com.br');
      setPassword('Admin@123');
    } else if (role === 'gerente') {
      setEmail('gerente@techconnect.com.br');
      setPassword('Gerente@123');
    } else {
      setEmail('funcionario@techconnect.com.br');
      setPassword('Func@123');
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center relative overflow-hidden font-sans" style={{ width: '100vw' }}>
      {/* Background decorations */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/20 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-secondary/20 rounded-full blur-[150px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="z-10"
        style={{ width: '100%', maxWidth: '448px', minWidth: '350px', padding: '16px' }}
      >
        <div className="rounded-2xl shadow-2xl border border-border-subtle bg-glass-bg backdrop-blur-xl" style={{ padding: '32px', width: '100%' }}>
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-on-surface mb-2 tracking-tight" style={{ fontFamily: '"Outfit", sans-serif' }}>
              TechConnect <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">Premium</span>
            </h1>
            <p className="text-on-surface-variant">Entre na sua conta para continuar</p>
          </div>

          {import.meta.env.DEV && !mfaToken && (
          <div className="flex gap-2 justify-center mb-6">
            <button type="button" onClick={() => autofill('admin')} className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-primary/10 text-primary hover:bg-primary/20 transition-colors border border-primary/20">
              <Shield size={14} /> Admin
            </button>
            <button type="button" onClick={() => autofill('gerente')} className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-success/10 text-success hover:bg-success/20 transition-colors border border-success/20">
              <Briefcase size={14} /> Gerente
            </button>
            <button type="button" onClick={() => autofill('funcionario')} className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-secondary/10 text-secondary hover:bg-secondary/20 transition-colors border border-secondary/20">
              <User size={14} /> Funcionário
            </button>
          </div>
          )}

          {error && (
            <div className="bg-error/10 border border-error/50 text-error p-3 rounded-xl mb-6 text-sm text-center">
              {error}
            </div>
          )}

          {mfaToken ? (
            <form onSubmit={handleMfa} className="space-y-5">
              <p className="text-sm text-on-surface-variant text-center">
                Digite o código de 6 dígitos do seu aplicativo autenticador, ou um código de recuperação.
              </p>
              <input
                autoFocus
                inputMode="numeric"
                autoComplete="one-time-code"
                value={mfaCode}
                onChange={(e) => setMfaCode(e.target.value)}
                className="block w-full px-4 py-3 border border-border-subtle rounded-xl bg-surface-container text-on-surface text-center tracking-[0.4em] text-lg focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="000000"
                required
              />
              <button type="submit" disabled={loading} className="w-full flex justify-center items-center gap-2 py-3 px-4 rounded-xl shadow-lg shadow-primary/20 text-sm font-semibold text-on-primary bg-gradient-to-r from-primary to-secondary hover:opacity-90 disabled:opacity-50 transition-all">
                {loading ? <Loader2 className="animate-spin" size={20} /> : 'Confirmar'}
              </button>
              <button type="button" onClick={() => { setMfaToken(''); setMfaCode(''); }} className="w-full text-sm text-on-surface-variant hover:text-on-surface">
                Voltar
              </button>
            </form>
          ) : (
          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-on-surface-variant mb-1.5">Usuário ou E-mail</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Mail className="text-outline" size={20} />
                </div>
                <input
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-11 pr-4 py-3 border border-border-subtle rounded-xl bg-surface-container text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                  placeholder="admin@techconnect.com.br"
                  required
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-sm font-medium text-on-surface-variant">Senha</label>
                <Link to="/esqueci-senha" className="text-sm text-primary hover:opacity-80 transition-colors">
                  Esqueceu a senha?
                </Link>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="text-outline" size={20} />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-11 pr-4 py-3 border border-border-subtle rounded-xl bg-surface-container text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center gap-2 py-3 px-4 rounded-xl shadow-lg shadow-primary/20 text-sm font-semibold text-on-primary bg-gradient-to-r from-primary to-secondary hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-background focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {loading ? (
                <Loader2 className="animate-spin" size={20} />
              ) : (
                <>
                  Entrar no Sistema
                  <ChevronRight size={20} />
                </>
              )}
            </button>
          </form>
          )}

          <div className="mt-6 text-center text-xs text-on-surface-variant border-t border-border-subtle pt-4">
            Não possui uma conta?{' '}
            <Link to="/cadastro" className="text-primary font-semibold hover:underline">
              Cadastre sua empresa e escolha um plano
            </Link>
          </div>
        </div>

        <p className="mt-8 text-center text-sm text-outline">
          &copy; {new Date().getFullYear()} TechConnect Inc. Todos os direitos reservados.
        </p>
      </motion.div>
    </div>
  );
}
