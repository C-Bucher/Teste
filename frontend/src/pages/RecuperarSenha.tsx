import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import api from '../api';
import AuthCard, { authButtonClass, authInputClass } from '../components/AuthCard';
import { useToast } from '../context/ToastContext';

const detail = (err: unknown, fallback: string) => (axios.isAxiosError(err) ? err.response?.data?.detail || fallback : fallback);

/** /esqueci-senha: asks for the e-mail and always answers the same way. */
export function EsqueciSenha() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const toast = useToast();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.post('/auth/forgot-password', { email });
      setSent(true);
    } catch (err) {
      toast.error(detail(err, 'Não foi possível enviar agora. Tente novamente.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthCard subtitle="Recuperar acesso">
      {sent ? (
        <p className="text-on-surface text-sm text-center">
          Se <strong>{email}</strong> estiver cadastrado, você vai receber um link para criar uma nova senha. O link vale por 1 hora.
        </p>
      ) : (
        <form onSubmit={submit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-on-surface-variant mb-1.5">E-mail da conta</label>
            <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className={authInputClass} placeholder="voce@empresa.com.br" />
          </div>
          <button type="submit" disabled={loading} className={authButtonClass}>{loading ? 'Enviando...' : 'Enviar link'}</button>
        </form>
      )}
      <div className="mt-6 text-center text-xs text-on-surface-variant border-t border-border-subtle pt-4">
        <Link to="/" className="text-primary font-semibold hover:underline">Voltar para o login</Link>
      </div>
    </AuthCard>
  );
}

/** /redefinir-senha?token=...: the link from the recovery e-mail. */
export function RedefinirSenha() {
  const [params] = useSearchParams();
  const token = params.get('token') || '';
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const toast = useToast();
  const navigate = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirm) {
      toast.error('A confirmação não confere com a nova senha.');
      return;
    }
    setLoading(true);
    try {
      await api.post('/auth/reset-password', { token, new_password: password });
      toast.success('Senha redefinida. Entre com a nova senha.');
      navigate('/');
    } catch (err) {
      toast.error(detail(err, 'Não foi possível redefinir a senha.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthCard subtitle="Criar uma nova senha">
      {!token ? (
        <p className="text-on-surface text-sm text-center">Link incompleto. Peça um novo em “Esqueci minha senha”.</p>
      ) : (
        <form onSubmit={submit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-on-surface-variant mb-1.5">Nova senha</label>
            <input type="password" required autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} className={authInputClass} />
          </div>
          <div>
            <label className="block text-sm font-medium text-on-surface-variant mb-1.5">Confirmar nova senha</label>
            <input type="password" required autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} className={authInputClass} />
            <p className="text-xs text-outline mt-1">Mínimo de 8 caracteres, com letras e números.</p>
          </div>
          <button type="submit" disabled={loading} className={authButtonClass}>{loading ? 'Salvando...' : 'Redefinir senha'}</button>
        </form>
      )}
      <div className="mt-6 text-center text-xs text-on-surface-variant border-t border-border-subtle pt-4">
        <Link to="/esqueci-senha" className="text-primary font-semibold hover:underline">Pedir um novo link</Link>
      </div>
    </AuthCard>
  );
}
