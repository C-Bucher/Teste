import { useEffect, useState } from 'react';
import api from '../api';

interface AuditEntry {
  id: string;
  user_id: string | null;
  action: string;
  entity: string | null;
  entity_id: string | null;
  details: string | null;
  ip: string | null;
  created_at: string;
}

const ACTION_LABELS: Record<string, string> = {
  CADASTRO: 'Cadastro da empresa',
  LOGIN: 'Login',
  LOGIN_FALHA: 'Senha incorreta',
  LOGIN_BLOQUEADO: 'Login bloqueado',
  USUARIO_CRIADO: 'Acesso criado',
  USUARIO_ALTERADO: 'Acesso alterado',
  SENHA_ALTERADA: 'Senha alterada',
  SENHA_REDEFINIDA: 'Senha redefinida pelo admin',
  PERMISSOES_ALTERADAS: 'Permissões alteradas',
  LANCAMENTO_CRIADO: 'Lançamento criado',
  LANCAMENTO_ALTERADO: 'Lançamento alterado',
  LANCAMENTO_PAGO: 'Lançamento pago',
  ANEXO_ENVIADO: 'Comprovante anexado',
  DADOS_EXPORTADOS: 'Dados pessoais exportados',
  CONTA_EXCLUIDA: 'Conta excluída',
};

const PAGE_SIZE = 25;

function formatDateTime(iso: string) {
  const d = new Date(iso.endsWith('Z') ? iso : `${iso}Z`);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString('pt-BR');
}

export default function AuditLogSection() {
  const [items, setItems] = useState<AuditEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [action, setAction] = useState('');
  const [users, setUsers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/auth/users')
      .then((res) => setUsers(Object.fromEntries(res.data.map((u: { id: string; full_name: string }) => [u.id, u.full_name]))))
      .catch(() => setUsers({}));
  }, []);

  useEffect(() => {
    setLoading(true);
    api.get('/audit/', { params: { page, size: PAGE_SIZE, action: action || undefined } })
      .then((res) => { setItems(res.data.items); setTotal(res.data.total); setError(''); })
      .catch((err) => setError(err?.response?.status === 403 ? 'Somente administradores podem consultar a auditoria.' : 'Erro ao carregar a auditoria.'))
      .finally(() => setLoading(false));
  }, [page, action]);

  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-md">
      <div className="flex items-center gap-md">
        <select
          value={action}
          onChange={(e) => { setAction(e.target.value); setPage(1); }}
          className="bg-surface-container border border-border-subtle rounded-lg px-3 py-2 text-label-md text-on-surface outline-none focus:border-primary"
        >
          <option value="">Todas as ações</option>
          {Object.entries(ACTION_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
        <span className="text-on-surface-variant text-body-sm">{total} registro(s)</span>
      </div>

      {error ? (
        <p className="text-error text-body-sm">{error}</p>
      ) : (
        <div className="glass-panel bg-surface/60 border border-border-subtle rounded-xl overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-highest/30 border-b border-border-subtle">
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Quando</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Quem</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Ação</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Detalhes</th>
                <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">IP</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle/50">
              {loading ? (
                <tr><td colSpan={5} className="py-lg text-center text-on-surface-variant">Carregando...</td></tr>
              ) : items.length === 0 ? (
                <tr><td colSpan={5} className="py-lg text-center text-on-surface-variant">Nenhum registro.</td></tr>
              ) : items.map((it) => (
                <tr key={it.id} className="hover:bg-surface-bright/40 transition-colors align-top">
                  <td className="px-lg py-md text-label-md text-on-surface-variant whitespace-nowrap">{formatDateTime(it.created_at)}</td>
                  <td className="px-lg py-md text-label-md text-on-surface">{(it.user_id && users[it.user_id]) || it.user_id || '—'}</td>
                  <td className="px-lg py-md text-label-md text-on-surface">{ACTION_LABELS[it.action] || it.action}</td>
                  <td className="px-lg py-md text-[12px] text-on-surface-variant break-all max-w-md">{it.details || it.entity_id || ''}</td>
                  <td className="px-lg py-md text-[12px] text-on-surface-variant">{it.ip || ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {pages > 1 && (
        <div className="flex items-center justify-end gap-sm">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1.5 rounded-lg border border-border-subtle text-label-md disabled:opacity-40">Anterior</button>
          <span className="text-body-sm text-on-surface-variant">{page} / {pages}</span>
          <button disabled={page >= pages} onClick={() => setPage(page + 1)} className="px-3 py-1.5 rounded-lg border border-border-subtle text-label-md disabled:opacity-40">Próxima</button>
        </div>
      )}
    </div>
  );
}
