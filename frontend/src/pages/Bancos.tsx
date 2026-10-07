import { useCallback, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import axios from 'axios';
import api from '../api';
import Layout from '../components/Layout';
import { useToast } from '../context/ToastContext';
import { useConfirm } from '../context/ConfirmContext';

type Scope = 'empresa' | 'pessoal';

interface BankAccount {
  id: string;
  name: string;
  bank_name: string | null;
  source: 'arquivo' | 'agregador';
  status: string;
  last_sync_at: string | null;
}

interface BankTransaction {
  id: string;
  bank_account_id: string;
  date: string;
  amount: number;
  description: string;
  category: string | null;
  status: 'NOVA' | 'CONCILIADA' | 'LANCADA' | 'IGNORADA';
}

interface Rule { id: string; pattern: string; category: string }
interface PendingEntry { id: string; type: string; amount: number; description: string; due_date: string }
interface Usage { plan_name: string; bank_connections: { used: number; limit: number } }

const STATUS_LABEL: Record<BankTransaction['status'], { label: string; cls: string }> = {
  NOVA: { label: 'A conciliar', cls: 'bg-warning/15 text-warning' },
  CONCILIADA: { label: 'Conciliada', cls: 'bg-success/15 text-success' },
  LANCADA: { label: 'Lançada', cls: 'bg-primary/15 text-primary' },
  IGNORADA: { label: 'Ignorada', cls: 'bg-surface-container-highest text-on-surface-variant' },
};

const inputClass =
  'w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none';

const brl = (v: number) => v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
const fmtDate = (iso: string | null) => (iso ? iso.slice(0, 10).split('-').reverse().join('/') : '—');
const detail = (err: unknown, fallback: string) => (axios.isAxiosError(err) ? err.response?.data?.detail || fallback : fallback);

declare global {
  interface Window { PluggyConnect?: new (opts: Record<string, unknown>) => { init: () => void } }
}

function loadPluggyConnect(): Promise<void> {
  if (window.PluggyConnect) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://cdn.pluggy.ai/pluggy-connect/v2.7.0/pluggy-connect.js';
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('widget'));
    document.body.appendChild(script);
  });
}

export default function Bancos({ scope }: { scope: Scope }) {
  const toast = useToast();
  const confirm = useConfirm();
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [transactions, setTransactions] = useState<BankTransaction[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [onlyPending, setOnlyPending] = useState(scope === 'empresa');
  const [loading, setLoading] = useState(true);

  const [importOpen, setImportOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importAccount, setImportAccount] = useState('');
  const [importName, setImportName] = useState('');
  const [importing, setImporting] = useState(false);
  const [syncingId, setSyncingId] = useState<string | null>(null);

  const [matchTx, setMatchTx] = useState<BankTransaction | null>(null);
  const [pendingEntries, setPendingEntries] = useState<PendingEntry[]>([]);
  const [launchTx, setLaunchTx] = useState<BankTransaction | null>(null);
  const [launchCategory, setLaunchCategory] = useState('');
  const [newRule, setNewRule] = useState({ pattern: '', category: '' });

  const fetchAll = useCallback(async () => {
    const [acc, tx, rl, us] = await Promise.all([
      api.get('/bank/accounts', { params: { scope } }),
      api.get('/bank/transactions', { params: { scope, status: onlyPending ? 'NOVA' : undefined } }),
      api.get('/bank/rules', { params: { scope } }),
      api.get('/bank/usage'),
    ]);
    return { accounts: acc.data as BankAccount[], transactions: tx.data as BankTransaction[], rules: rl.data as Rule[], usage: us.data as Usage };
  }, [scope, onlyPending]);

  const apply = useCallback((d: Awaited<ReturnType<typeof fetchAll>>) => {
    setAccounts(d.accounts);
    setTransactions(d.transactions);
    setRules(d.rules);
    setUsage(d.usage);
  }, []);

  const load = useCallback(async () => {
    try {
      apply(await fetchAll());
    } catch (err) {
      toast.error(detail(err, 'Erro ao carregar dados bancários.'));
    }
  }, [fetchAll, apply, toast]);

  useEffect(() => {
    let active = true;
    fetchAll()
      .then((d) => { if (active) apply(d); })
      .catch((err) => { if (active) toast.error(detail(err, 'Erro ao carregar dados bancários.')); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [fetchAll, apply, toast]);

  const accountName = (id: string) => accounts.find((a) => a.id === id)?.name || '';

  const handleImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!importFile) return;
    setImporting(true);
    try {
      const form = new FormData();
      form.append('scope', scope);
      form.append('file', importFile);
      if (importAccount) form.append('account_id', importAccount);
      else if (importName.trim()) form.append('account_name', importName.trim());
      const { data } = await api.post('/bank/import', form, { headers: { 'Content-Type': 'multipart/form-data' } });
      const parts = [`${data.imported} nova(s)`];
      if (data.duplicates) parts.push(`${data.duplicates} já importada(s)`);
      if (scope === 'empresa') parts.push(`${data.reconciled} conciliada(s) automaticamente`);
      else parts.push(`${data.launched} lançada(s) no seu extrato`);
      toast.success(`Extrato importado: ${parts.join(', ')}.`);
      setImportOpen(false);
      setImportFile(null);
      setImportName('');
      await load();
    } catch (err) {
      toast.error(detail(err, 'Erro ao importar o extrato.'));
    } finally {
      setImporting(false);
    }
  };

  const handleConnect = async () => {
    try {
      const { data } = await api.post('/bank/connect-token', { scope });
      await loadPluggyConnect();
      const widget = new window.PluggyConnect!({
        connectToken: data.connect_token,
        includeSandbox: import.meta.env.DEV,
        onSuccess: async ({ item }: { item: { id: string } }) => {
          try {
            const res = await api.post('/bank/connections', { scope, item_id: item.id });
            toast.success(`${res.data.length} conta(s) conectada(s). Sincronizando...`);
            for (const acc of res.data as BankAccount[]) await api.post(`/bank/accounts/${acc.id}/sync`);
            await load();
          } catch (err) {
            toast.error(detail(err, 'Erro ao registrar a conexão.'));
          }
        },
        onError: () => toast.error('Não foi possível concluir a conexão com o banco.'),
      });
      widget.init();
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 402) toast.warning(detail(err, 'Limite do plano atingido.'));
      else if (axios.isAxiosError(err) && err.response?.status === 503) toast.info(detail(err, 'Conexão automática indisponível.'));
      else toast.error(detail(err, 'Erro ao iniciar a conexão com o banco.'));
    }
  };

  const handleSync = async (acc: BankAccount) => {
    setSyncingId(acc.id);
    try {
      const { data } = await api.post(`/bank/accounts/${acc.id}/sync`);
      toast.success(`${data.imported} nova(s) transação(ões)${scope === 'empresa' ? `, ${data.reconciled} conciliada(s)` : ''}.`);
      await load();
    } catch (err) {
      toast.error(detail(err, 'Erro ao sincronizar.'));
    } finally {
      setSyncingId(null);
    }
  };

  const handleRemoveAccount = async (acc: BankAccount) => {
    const ok = await confirm({
      title: 'Remover conta',
      message: `Remover "${acc.name}" e as transações importadas dela? Lançamentos já criados ou conciliados continuam no sistema.`,
      confirmLabel: 'Remover',
      isDestructive: true,
    });
    if (!ok) return;
    try {
      await api.delete(`/bank/accounts/${acc.id}`);
      toast.success('Conta removida.');
      await load();
    } catch (err) {
      toast.error(detail(err, 'Erro ao remover a conta.'));
    }
  };

  const openMatch = async (tx: BankTransaction) => {
    try {
      const { data } = await api.get('/financial/entries', { params: { status: 'PENDENTE', type: tx.amount > 0 ? 'RECEITA' : 'DESPESA', size: 200 } });
      setPendingEntries(data.items);
      setMatchTx(tx);
    } catch (err) {
      toast.error(detail(err, 'Erro ao buscar lançamentos pendentes.'));
    }
  };

  const doMatch = async (entryId: string) => {
    if (!matchTx) return;
    try {
      await api.post(`/bank/transactions/${matchTx.id}/match`, { entry_id: entryId });
      toast.success('Transação conciliada e lançamento marcado como pago.');
      setMatchTx(null);
      await load();
    } catch (err) {
      toast.error(detail(err, 'Erro ao conciliar.'));
    }
  };

  const doLaunch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!launchTx) return;
    try {
      await api.post(`/bank/transactions/${launchTx.id}/create-entry`, { category: launchCategory || undefined });
      toast.success('Lançamento criado como pago.');
      setLaunchTx(null);
      await load();
    } catch (err) {
      toast.error(detail(err, 'Erro ao criar lançamento.'));
    }
  };

  const doIgnore = async (tx: BankTransaction) => {
    try {
      await api.post(`/bank/transactions/${tx.id}/ignore`);
      await load();
    } catch (err) {
      toast.error(detail(err, 'Erro ao ignorar.'));
    }
  };

  const addRule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/bank/rules', { scope, ...newRule });
      setNewRule({ pattern: '', category: '' });
      await load();
    } catch (err) {
      toast.error(detail(err, 'Erro ao salvar a regra.'));
    }
  };

  const removeRule = async (id: string) => {
    await api.delete(`/bank/rules/${id}`).catch(() => toast.error('Erro ao remover a regra.'));
    await load();
  };

  const conn = usage?.bank_connections;

  return (
    <Layout>
      <div className="mb-xl flex flex-col lg:flex-row lg:items-end lg:justify-between gap-md">
        <div>
          <nav className="flex text-body-sm text-outline mb-xs gap-xs items-center">
            <span>{scope === 'empresa' ? 'Empresa' : 'Pessoal'}</span>
            <span className="material-symbols-outlined text-[12px]">chevron_right</span>
            <span className="text-primary">Bancos</span>
          </nav>
          <h2 className="font-display-lg text-display-lg text-on-surface">Bancos & Conciliação</h2>
          <p className="text-on-surface-variant text-body-base mt-xs">
            {scope === 'empresa'
              ? 'Traga o extrato do banco e o sistema dá baixa sozinho nas contas a pagar e a receber correspondentes.'
              : 'Traga o extrato do banco e suas movimentações entram direto no seu extrato pessoal.'}
          </p>
        </div>
        <div className="flex flex-wrap gap-sm">
          <button onClick={() => { setImportAccount(''); setImportOpen(true); }}
            className="flex items-center gap-sm px-lg py-3 rounded-xl border border-border-subtle text-on-surface hover:bg-surface-container-high transition-all font-label-md">
            <span className="material-symbols-outlined">upload_file</span> Importar extrato
          </button>
          <button onClick={handleConnect}
            className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10">
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>account_balance</span> Conectar banco
          </button>
        </div>
      </div>

      {conn && (
        <p className="text-body-sm text-on-surface-variant mb-lg">
          Contas conectadas automaticamente: <strong className="text-on-surface">{conn.used} de {conn.limit}</strong> no plano {usage?.plan_name}.
          {conn.limit === 0 && <> A importação de extrato é ilimitada. <Link to="/planos" className="text-primary hover:underline">Conheça o Pessoal Conectado</Link>.</>}
        </p>
      )}

      {/* Accounts */}
      <section className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-md mb-xl">
        {loading ? null : accounts.length === 0 ? (
          <div className="glass-card rounded-2xl p-lg text-on-surface-variant text-body-sm md:col-span-2 xl:col-span-3">
            Nenhuma conta ainda. Exporte o extrato no app ou site do seu banco (formato <strong>OFX</strong> ou <strong>CSV</strong>) e clique em “Importar extrato”.
          </div>
        ) : accounts.map((acc) => (
          <div key={acc.id} className="glass-card rounded-2xl p-lg">
            <div className="flex justify-between items-start gap-sm">
              <div>
                <p className="font-label-md text-on-surface">{acc.name}</p>
                <p className="text-[12px] text-on-surface-variant">{acc.bank_name || 'Banco não informado'}</p>
              </div>
              <span className={`px-sm py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider ${acc.source === 'agregador' ? 'bg-success/15 text-success' : 'bg-surface-container-highest text-on-surface-variant'}`}>
                {acc.source === 'agregador' ? 'Automática' : 'Por arquivo'}
              </span>
            </div>
            <p className="text-[12px] text-on-surface-variant mt-md">Atualizada em {fmtDate(acc.last_sync_at)}{acc.status === 'ERRO' && <span className="text-error"> · falha na última sincronização</span>}</p>
            <div className="flex gap-md mt-md">
              {acc.source === 'agregador' ? (
                <button onClick={() => handleSync(acc)} disabled={syncingId === acc.id} className="text-primary hover:underline text-label-md disabled:opacity-50">
                  {syncingId === acc.id ? 'Sincronizando...' : 'Sincronizar'}
                </button>
              ) : (
                <button onClick={() => { setImportAccount(acc.id); setImportOpen(true); }} className="text-primary hover:underline text-label-md">Importar mais</button>
              )}
              <button onClick={() => handleRemoveAccount(acc)} className="text-on-surface-variant hover:text-error text-label-md">Remover</button>
            </div>
          </div>
        ))}
      </section>

      {/* Transactions */}
      <section className="mb-xl">
        <div className="flex items-center justify-between mb-md">
          <h3 className="font-headline-sm text-headline-sm text-on-surface">Movimentações</h3>
          <label className="flex items-center gap-sm text-body-sm text-on-surface-variant cursor-pointer">
            <input type="checkbox" checked={onlyPending} onChange={(e) => setOnlyPending(e.target.checked)} />
            Só as que faltam conciliar
          </label>
        </div>
        <div className="glass-panel bg-surface/60 border border-border-subtle rounded-xl overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-highest/30 border-b border-border-subtle">
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Data</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Descrição</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Conta</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Categoria</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant text-right">Valor</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Situação</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant text-right">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle/50">
              {transactions.length === 0 ? (
                <tr><td colSpan={7} className="py-lg text-center text-on-surface-variant">{onlyPending ? 'Nada pendente. Tudo conciliado.' : 'Nenhuma movimentação importada.'}</td></tr>
              ) : transactions.map((tx) => (
                <tr key={tx.id} className="hover:bg-surface-bright/40 transition-colors">
                  <td className="px-lg py-md text-label-md text-on-surface-variant whitespace-nowrap">{fmtDate(tx.date)}</td>
                  <td className="px-lg py-md text-label-md text-on-surface">{tx.description}</td>
                  <td className="px-lg py-md text-[12px] text-on-surface-variant">{accountName(tx.bank_account_id)}</td>
                  <td className="px-lg py-md text-[12px] text-on-surface-variant">{tx.category || '—'}</td>
                  <td className={`px-lg py-md text-right font-bold whitespace-nowrap ${tx.amount > 0 ? 'text-success' : 'text-error'}`}>{brl(tx.amount)}</td>
                  <td className="px-lg py-md"><span className={`px-sm py-0.5 rounded-full text-[11px] font-bold ${STATUS_LABEL[tx.status].cls}`}>{STATUS_LABEL[tx.status].label}</span></td>
                  <td className="px-lg py-md text-right whitespace-nowrap">
                    {tx.status === 'NOVA' && scope === 'empresa' && (
                      <>
                        <button onClick={() => openMatch(tx)} className="text-primary hover:underline text-label-md mr-md">Conciliar</button>
                        <button onClick={() => { setLaunchTx(tx); setLaunchCategory(tx.category || ''); }} className="text-primary hover:underline text-label-md mr-md">Lançar</button>
                        <button onClick={() => doIgnore(tx)} className="text-on-surface-variant hover:underline text-label-md">Ignorar</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Rules */}
      <section className="glass-card rounded-2xl p-lg max-w-3xl">
        <h3 className="font-headline-sm text-headline-sm text-on-surface mb-xs">Regras de categoria</h3>
        <p className="text-on-surface-variant text-body-sm mb-md">Quando a descrição do banco contiver o texto, a movimentação recebe a categoria automaticamente.</p>
        <form onSubmit={addRule} className="flex flex-col sm:flex-row gap-sm mb-md">
          <input required placeholder='Texto (ex.: "uber")' value={newRule.pattern} onChange={(e) => setNewRule({ ...newRule, pattern: e.target.value })} className={inputClass} />
          <input required placeholder="Categoria (ex.: Transporte)" value={newRule.category} onChange={(e) => setNewRule({ ...newRule, category: e.target.value })} className={inputClass} />
          <button type="submit" className="px-lg py-2 rounded-lg bg-primary text-on-primary font-label-md whitespace-nowrap">Adicionar</button>
        </form>
        <ul className="divide-y divide-border-subtle/50">
          {rules.map((r) => (
            <li key={r.id} className="flex justify-between items-center py-sm text-body-sm">
              <span className="text-on-surface">contém “{r.pattern}” → <strong>{r.category}</strong></span>
              <button onClick={() => removeRule(r.id)} className="text-on-surface-variant hover:text-error"><span className="material-symbols-outlined text-[18px]">delete</span></button>
            </li>
          ))}
        </ul>
      </section>

      {/* Import modal */}
      <AnimatePresence>
        {importOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setImportOpen(false)} />
            <motion.form onSubmit={handleImport} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              className="relative glass-card rounded-2xl p-lg w-full max-w-md mx-4 space-y-md">
              <h3 className="font-headline-sm text-headline-sm text-on-surface">Importar extrato</h3>
              <p className="text-on-surface-variant text-body-sm">No app ou site do banco, exporte o extrato em <strong>OFX</strong> (Money/Quicken) ou <strong>CSV</strong>. Reimportar o mesmo período não duplica nada.</p>
              <div>
                <label className="block text-label-md text-on-surface-variant mb-1">Conta</label>
                <select value={importAccount} onChange={(e) => setImportAccount(e.target.value)} className={inputClass}>
                  <option value="">Nova conta</option>
                  {accounts.filter((a) => a.source === 'arquivo').map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
                </select>
              </div>
              {!importAccount && (
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Nome da nova conta</label>
                  <input value={importName} onChange={(e) => setImportName(e.target.value)} placeholder="Ex.: Itaú PJ" className={inputClass} />
                </div>
              )}
              <input required type="file" accept=".ofx,.csv,.txt" onChange={(e) => setImportFile(e.target.files?.[0] || null)} className="text-body-sm text-on-surface-variant" />
              <div className="flex justify-end gap-sm">
                <button type="button" onClick={() => setImportOpen(false)} className="px-lg py-2 rounded-xl text-on-surface-variant hover:bg-surface-container-high">Cancelar</button>
                <button type="submit" disabled={importing || !importFile} className="px-lg py-2 rounded-xl bg-gradient-to-r from-primary to-secondary text-on-primary font-label-md disabled:opacity-50">
                  {importing ? 'Importando...' : 'Importar'}
                </button>
              </div>
            </motion.form>
          </div>
        )}
      </AnimatePresence>

      {/* Match modal */}
      <AnimatePresence>
        {matchTx && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMatchTx(null)} />
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              className="relative glass-card rounded-2xl p-lg w-full max-w-lg mx-4">
              <h3 className="font-headline-sm text-headline-sm text-on-surface mb-xs">Conciliar movimentação</h3>
              <p className="text-on-surface-variant text-body-sm mb-md">{matchTx.description} · {fmtDate(matchTx.date)} · <strong>{brl(matchTx.amount)}</strong></p>
              <div className="max-h-80 overflow-y-auto divide-y divide-border-subtle/50">
                {pendingEntries.length === 0 && <p className="text-on-surface-variant text-body-sm py-md">Nenhum lançamento pendente deste tipo. Use “Lançar” para criar um já pago.</p>}
                {pendingEntries.map((en) => {
                  const fits = Math.abs(en.amount - Math.abs(matchTx.amount)) <= 0.01;
                  return (
                    <button key={en.id} disabled={!fits} onClick={() => doMatch(en.id)}
                      className="w-full flex justify-between items-center py-sm px-sm text-left hover:bg-surface-container-high rounded-lg disabled:opacity-40 disabled:cursor-not-allowed">
                      <span>
                        <span className="block text-label-md text-on-surface">{en.description}</span>
                        <span className="block text-[12px] text-on-surface-variant">vence {fmtDate(en.due_date)}{!fits && ' · valor diferente'}</span>
                      </span>
                      <span className="font-bold text-on-surface">{brl(en.amount)}</span>
                    </button>
                  );
                })}
              </div>
              <div className="flex justify-end mt-md">
                <button onClick={() => setMatchTx(null)} className="px-lg py-2 rounded-xl text-on-surface-variant hover:bg-surface-container-high">Fechar</button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Launch modal */}
      <AnimatePresence>
        {launchTx && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setLaunchTx(null)} />
            <motion.form onSubmit={doLaunch} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              className="relative glass-card rounded-2xl p-lg w-full max-w-md mx-4 space-y-md">
              <h3 className="font-headline-sm text-headline-sm text-on-surface">Lançar no financeiro</h3>
              <p className="text-on-surface-variant text-body-sm">Cria um lançamento de {launchTx.amount > 0 ? 'receita' : 'despesa'} já pago: {launchTx.description}, {brl(Math.abs(launchTx.amount))} em {fmtDate(launchTx.date)}.</p>
              <div>
                <label className="block text-label-md text-on-surface-variant mb-1">Categoria</label>
                <input value={launchCategory} onChange={(e) => setLaunchCategory(e.target.value)} placeholder="Ex.: Tarifas bancárias" className={inputClass} />
              </div>
              <div className="flex justify-end gap-sm">
                <button type="button" onClick={() => setLaunchTx(null)} className="px-lg py-2 rounded-xl text-on-surface-variant hover:bg-surface-container-high">Cancelar</button>
                <button type="submit" className="px-lg py-2 rounded-xl bg-gradient-to-r from-primary to-secondary text-on-primary font-label-md">Lançar</button>
              </div>
            </motion.form>
          </div>
        )}
      </AnimatePresence>
    </Layout>
  );
}
