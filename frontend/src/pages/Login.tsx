import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api';
import { motion } from 'framer-motion';
import { Mail, Lock, ChevronRight, Loader2, User, Shield, Briefcase } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/auth/login', { email, password });
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao realizar login');
    } finally {
      setLoading(false);
    }
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
    <div className="min-h-screen bg-[#0B0F19] flex flex-col justify-center items-center relative overflow-hidden font-sans" style={{ width: '100vw' }}>
      {/* Background decorations */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-500/20 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-500/20 rounded-full blur-[150px] pointer-events-none" />

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="z-10"
        style={{ width: '100%', maxWidth: '448px', minWidth: '350px', padding: '16px' }}
      >
        <div className="rounded-2xl shadow-2xl border border-white/5 bg-[#171b26]/80 backdrop-blur-xl" style={{ padding: '32px', width: '100%' }}>
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-white mb-2 tracking-tight">
              TechConnect <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">Premium</span>
            </h1>
            <p className="text-slate-400">Entre na sua conta para continuar</p>
          </div>

          <div className="flex gap-2 justify-center mb-6">
            <button type="button" onClick={() => autofill('admin')} className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors border border-blue-500/20">
              <Shield size={14} /> Admin
            </button>
            <button type="button" onClick={() => autofill('gerente')} className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-colors border border-emerald-500/20">
              <Briefcase size={14} /> Gerente
            </button>
            <button type="button" onClick={() => autofill('funcionario')} className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-purple-500/10 text-purple-400 hover:bg-purple-500/20 transition-colors border border-purple-500/20">
              <User size={14} /> Funcionário
            </button>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded-xl mb-6 text-sm text-center">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Usuário ou E-mail</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Mail className="text-slate-500" size={20} />
                </div>
                <input
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-11 pr-4 py-3 border border-white/10 rounded-xl bg-[#1c1f2a] text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  placeholder="admin@techconnect.com.br"
                  required
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-sm font-medium text-slate-300">Senha</label>
                <a href="#" className="text-sm text-blue-400 hover:text-blue-300 transition-colors">Esqueceu a senha?</a>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Lock className="text-slate-500" size={20} />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-11 pr-4 py-3 border border-white/10 rounded-xl bg-[#1c1f2a] text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <div className="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                className="h-4 w-4 bg-[#1c1f2a] border-white/10 rounded text-blue-500 focus:ring-blue-500 accent-blue-500"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-slate-300">
                Lembrar de mim
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center items-center gap-2 py-3 px-4 rounded-xl shadow-lg shadow-blue-500/20 text-sm font-semibold text-white bg-gradient-to-r from-blue-500 to-purple-500 hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#0B0F19] focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
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

          <div className="mt-6 text-center text-xs text-slate-400 border-t border-white/10 pt-4">
            Não possui uma conta?{' '}
            <Link to="/cadastro" className="text-blue-400 font-semibold hover:underline">
              Cadastre sua empresa e escolha um plano
            </Link>
          </div>
        </div>
        
        <p className="mt-8 text-center text-sm text-slate-500">
          &copy; {new Date().getFullYear()} TechConnect Inc. Todos os direitos reservados.
        </p>
      </motion.div>
    </div>
  );
}
