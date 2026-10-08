import { useEffect, useState } from 'react';
import axios from 'axios';
import api from '../api';
import { useToast } from '../context/ToastContext';

const inputClass =
  'w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none';
const detail = (err: unknown, fallback: string) => (axios.isAxiosError(err) ? err.response?.data?.detail || fallback : fallback);

/** Minha Conta → verificação em duas etapas (TOTP + códigos de recuperação). */
export default function TwoFactorSection() {
  const toast = useToast();
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [setup, setSetup] = useState<{ secret: string; qr_svg: string } | null>(null);
  const [code, setCode] = useState('');
  const [recoveryCodes, setRecoveryCodes] = useState<string[] | null>(null);
  const [disableForm, setDisableForm] = useState({ password: '', code: '' });
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get('/auth/me').then((res) => setEnabled(Boolean(res.data.mfa_enabled))).catch(() => setEnabled(false));
  }, []);

  const start = async () => {
    setBusy(true);
    try {
      const { data } = await api.post('/auth/mfa/setup');
      setSetup(data);
      setCode('');
    } catch (err) {
      toast.error(detail(err, 'Erro ao iniciar a configuração.'));
    } finally {
      setBusy(false);
    }
  };

  const confirm = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      const { data } = await api.post('/auth/mfa/enable', { code });
      setRecoveryCodes(data.recovery_codes);
      setSetup(null);
      setEnabled(true);
      toast.success('Verificação em duas etapas ativada.');
    } catch (err) {
      toast.error(detail(err, 'Código inválido.'));
    } finally {
      setBusy(false);
    }
  };

  const disable = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post('/auth/mfa/disable', disableForm);
      setEnabled(false);
      setDisableForm({ password: '', code: '' });
      toast.success('Verificação em duas etapas desativada.');
    } catch (err) {
      toast.error(detail(err, 'Não foi possível desativar.'));
    } finally {
      setBusy(false);
    }
  };

  if (enabled === null) return null;

  return (
    <section className="glass-card p-lg rounded-2xl">
      <h3 className="font-headline-sm text-headline-sm text-on-surface mb-xs">Verificação em duas etapas</h3>
      <p className="text-on-surface-variant text-body-sm mb-md">
        Além da senha, o login pede um código do seu aplicativo autenticador (Google Authenticator, Microsoft Authenticator, Authy).
      </p>

      {recoveryCodes && (
        <div className="mb-md p-md rounded-xl border border-warning/40 bg-warning/5">
          <p className="text-body-sm text-on-surface mb-sm">
            Guarde estes códigos de recuperação em local seguro. Cada um funciona uma única vez, se você perder o celular. Eles não serão mostrados de novo.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-sm font-mono text-label-md text-on-surface">
            {recoveryCodes.map((c) => <span key={c} className="px-sm py-xs rounded bg-surface-container text-center">{c}</span>)}
          </div>
          <button onClick={() => setRecoveryCodes(null)} className="mt-md text-primary hover:underline text-label-md">Já guardei</button>
        </div>
      )}

      {enabled ? (
        <form onSubmit={disable} className="space-y-md">
          <p className="text-body-sm text-success">Ativada.</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
            <input required type="password" placeholder="Sua senha" value={disableForm.password}
              onChange={(e) => setDisableForm({ ...disableForm, password: e.target.value })} className={inputClass} />
            <input required placeholder="Código do aplicativo" value={disableForm.code}
              onChange={(e) => setDisableForm({ ...disableForm, code: e.target.value })} className={inputClass} />
          </div>
          <button type="submit" disabled={busy} className="px-lg py-2.5 rounded-xl bg-error/10 text-error hover:bg-error/20 font-label-md disabled:opacity-50">
            Desativar
          </button>
        </form>
      ) : setup ? (
        <form onSubmit={confirm} className="space-y-md">
          <div className="flex flex-col sm:flex-row gap-lg items-start">
            <img src={setup.qr_svg} alt="QR code para o aplicativo autenticador" className="w-40 h-40 bg-white rounded-lg p-2" />
            <div className="text-body-sm text-on-surface-variant space-y-sm">
              <p>1. No aplicativo, adicione uma conta lendo o QR code.</p>
              <p>2. Sem câmera? Digite a chave: <code className="text-on-surface break-all">{setup.secret}</code></p>
              <p>3. Informe o código de 6 dígitos que aparecer.</p>
            </div>
          </div>
          <div className="flex gap-sm max-w-sm">
            <input required inputMode="numeric" autoComplete="one-time-code" placeholder="000000" value={code}
              onChange={(e) => setCode(e.target.value)} className={inputClass} />
            <button type="submit" disabled={busy} className="px-lg py-2 rounded-xl bg-gradient-to-r from-primary to-secondary text-on-primary font-label-md disabled:opacity-50">
              Ativar
            </button>
          </div>
        </form>
      ) : (
        <button onClick={start} disabled={busy}
          className="px-lg py-2.5 rounded-xl bg-gradient-to-r from-primary to-secondary text-on-primary font-label-md disabled:opacity-50">
          Configurar
        </button>
      )}
    </section>
  );
}
