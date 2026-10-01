import { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import api, { clearSession, saveSession } from '../api';
import Layout from '../components/Layout';
import { useToast } from '../context/ToastContext';
import { useConfirm } from '../context/ConfirmContext';
import { clearPermissionsCache } from '../hooks/usePermissions';

const inputClass =
  'w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none';

function errorMessage(err: unknown, fallback: string) {
  return axios.isAxiosError(err) ? err.response?.data?.detail || fallback : fallback;
}

export default function MinhaConta() {
  const toast = useToast();
  const confirm = useConfirm();
  const navigate = useNavigate();
  let user: { full_name?: string; email?: string; role?: string } = {};
  try { user = JSON.parse(localStorage.getItem('user') || '{}'); } catch { /* sessão inválida */ }

  const [pwd, setPwd] = useState({ current_password: '', new_password: '', confirm: '' });
  const [savingPwd, setSavingPwd] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleting, setDeleting] = useState(false);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (pwd.new_password !== pwd.confirm) {
      toast.error('A confirmação não confere com a nova senha.');
      return;
    }
    setSavingPwd(true);
    try {
      const res = await api.post('/auth/change-password', { current_password: pwd.current_password, new_password: pwd.new_password });
      saveSession(res.data); // other sessions end; this one continues with the new tokens
      setPwd({ current_password: '', new_password: '', confirm: '' });
      toast.success('Senha alterada. Outras sessões abertas foram encerradas.');
    } catch (err) {
      toast.error(errorMessage(err, 'Erro ao alterar a senha.'));
    } finally {
      setSavingPwd(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await api.get('/account/export');
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = 'meus-dados-techconnect.json';
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      toast.error(errorMessage(err, 'Erro ao exportar seus dados.'));
    } finally {
      setExporting(false);
    }
  };

  const handleDelete = async () => {
    const ok = await confirm({
      title: 'Excluir minha conta',
      message: 'Seus dados pessoais serão apagados de forma permanente. Se você for a única pessoa da empresa, todos os dados da empresa também serão apagados. Esta ação não pode ser desfeita.',
      confirmLabel: 'Excluir definitivamente',
      isDestructive: true,
    });
    if (!ok) return;
    setDeleting(true);
    try {
      await api.delete('/account', { data: { password: deletePassword } });
      clearSession();
      clearPermissionsCache();
      navigate('/');
    } catch (err) {
      toast.error(errorMessage(err, 'Erro ao excluir a conta.'));
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Layout>
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-lg max-w-3xl">
        <div>
          <h2 className="font-headline-md text-headline-md text-on-surface">Minha Conta</h2>
          <p className="text-on-surface-variant text-body-sm mt-xs">{user.full_name} · {user.email}</p>
        </div>

        <section className="glass-card p-lg rounded-2xl">
          <h3 className="font-headline-sm text-headline-sm text-on-surface mb-md">Alterar senha</h3>
          <form onSubmit={handleChangePassword} className="space-y-md">
            <div>
              <label className="block text-label-md text-on-surface-variant mb-1">Senha atual</label>
              <input required type="password" autoComplete="current-password" value={pwd.current_password}
                onChange={(e) => setPwd({ ...pwd, current_password: e.target.value })} className={inputClass} />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
              <div>
                <label className="block text-label-md text-on-surface-variant mb-1">Nova senha</label>
                <input required type="password" autoComplete="new-password" value={pwd.new_password}
                  onChange={(e) => setPwd({ ...pwd, new_password: e.target.value })} className={inputClass} />
              </div>
              <div>
                <label className="block text-label-md text-on-surface-variant mb-1">Confirmar nova senha</label>
                <input required type="password" autoComplete="new-password" value={pwd.confirm}
                  onChange={(e) => setPwd({ ...pwd, confirm: e.target.value })} className={inputClass} />
              </div>
            </div>
            <p className="text-[12px] text-on-surface-variant">Mínimo de 8 caracteres, com letras e números.</p>
            <button type="submit" disabled={savingPwd}
              className="bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-2.5 rounded-xl font-label-md disabled:opacity-50">
              {savingPwd ? 'Salvando...' : 'Alterar senha'}
            </button>
          </form>
        </section>

        <section className="glass-card p-lg rounded-2xl">
          <h3 className="font-headline-sm text-headline-sm text-on-surface mb-xs">Privacidade (LGPD)</h3>
          <p className="text-on-surface-variant text-body-sm mb-md">
            Baixe uma cópia de tudo o que guardamos sobre você: perfil, finanças pessoais e registro de atividades.
          </p>
          <button onClick={handleExport} disabled={exporting}
            className="flex items-center gap-sm px-lg py-2.5 rounded-xl border border-border-subtle text-on-surface hover:bg-surface-container-high transition-all font-label-md disabled:opacity-50">
            <span className="material-symbols-outlined text-[18px]">download</span>
            {exporting ? 'Gerando...' : 'Baixar meus dados'}
          </button>
        </section>

        <section className="glass-card p-lg rounded-2xl border border-error/30">
          <h3 className="font-headline-sm text-headline-sm text-error mb-xs">Excluir minha conta</h3>
          <p className="text-on-surface-variant text-body-sm mb-md">
            Remove seu acesso e seus dados pessoais. Se houver outras pessoas na empresa, os dados da empresa continuam com elas;
            se você for o único administrador, promova outra pessoa antes.
          </p>
          <div className="flex flex-col sm:flex-row gap-md sm:items-end">
            <div className="flex-1">
              <label className="block text-label-md text-on-surface-variant mb-1">Confirme com sua senha</label>
              <input type="password" autoComplete="current-password" value={deletePassword}
                onChange={(e) => setDeletePassword(e.target.value)} className={inputClass} />
            </div>
            <button onClick={handleDelete} disabled={!deletePassword || deleting}
              className="px-lg py-2.5 rounded-xl bg-error/10 text-error hover:bg-error/20 font-label-md disabled:opacity-50">
              {deleting ? 'Excluindo...' : 'Excluir conta'}
            </button>
          </div>
        </section>
      </motion.div>
    </Layout>
  );
}
