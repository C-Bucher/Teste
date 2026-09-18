import { useState, useEffect } from 'react';
import api from '../api';
import { motion } from 'framer-motion';
import { Navigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { useToast } from '../context/ToastContext';

interface ExportLog {
  id: string;
  type: string;
  format: string;
  status: string;
  created_at: string;
  size_bytes?: number;
}

interface ReportType {
  type: string;
  label: string;
  description: string;
  icon: string;
}

const REPORT_TYPES: ReportType[] = [
  { type: 'DRE', label: 'DRE', description: 'Demonstrativo de resultado do período.', icon: 'analytics' },
  { type: 'FLUXO_CAIXA', label: 'Fluxo de Caixa', description: 'Projeção de entradas e saídas D+90.', icon: 'trending_up' },
  { type: 'COLABORADORES', label: 'Colaboradores', description: 'Relação de colaboradores e cargos.', icon: 'groups' },
  { type: 'FORNECEDORES', label: 'Fornecedores', description: 'Cadastro de fornecedores e prestadores.', icon: 'local_shipping' },
  { type: 'COST_PER_TASK', label: 'Cost-per-Task', description: 'Custo médio por tarefa concluída.', icon: 'payments' },
];

const FORMATS: { format: string; label: string; icon: string }[] = [
  { format: 'CSV', label: 'CSV', icon: 'description' },
  { format: 'XLSX', label: 'XLSX', icon: 'table_chart' },
  { format: 'PDF', label: 'PDF', icon: 'picture_as_pdf' },
];

const STATUS_CONFIG: Record<string, { badge: string; dot: string }> = {
  PRONTO: { badge: 'bg-success/10 text-success', dot: 'bg-success' },
  PROCESSANDO: { badge: 'bg-warning/10 text-warning', dot: 'bg-warning' },
  ERRO: { badge: 'bg-error/10 text-error', dot: 'bg-error' },
};
const DEFAULT_STATUS = { badge: 'bg-outline/10 text-outline', dot: 'bg-outline' };

const formatDateTime = (value: string) => {
  const d = new Date(value);
  if (isNaN(d.getTime())) return value;
  return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
};

const formatSize = (bytes?: number) => {
  if (bytes === undefined || bytes === null) return '-';
  return `${(bytes / 1024).toFixed(1)} KB`;
};

export default function Exportacao() {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const isFuncionario = user.role === 'FUNCIONARIO';

  if (isFuncionario) {
    return <Navigate to="/dashboard" />;
  }

  const toast = useToast();
  const [logs, setLogs] = useState<ExportLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [requesting, setRequesting] = useState<string | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await api.get('/exports/logs');
      setLogs(res.data);
    } catch (err) {
      console.error('Erro ao carregar histórico de exportações', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const handleRequestExport = async (type: string, format: string) => {
    const key = `${type}-${format}`;
    setRequesting(key);
    try {
      const res = await api.post('/exports/request', { type, format });
      setLogs((prev) => [res.data, ...prev]);
      toast.success(`Relatório ${type} (${format}) gerado.`);
    } catch (err) {
      console.error('Erro ao solicitar exportação', err);
      toast.error('Erro ao solicitar exportação.');
    } finally {
      setRequesting(null);
    }
  };

  const handleDownload = async (id: string) => {
    try {
      const res = await api.get(`/exports/download/${id}`);
      window.open(res.data.download_url, '_blank');
    } catch (err) {
      console.error('Erro ao baixar exportação', err);
      toast.error('Erro ao baixar exportação.');
    }
  };

  return (
    <Layout>
      {/* Page Header */}
      <div className="mb-xl">
        <nav className="flex text-body-sm text-outline mb-xs gap-xs items-center">
          <span>Empresa</span>
          <span className="material-symbols-outlined text-[12px]">chevron_right</span>
          <span className="text-primary">Exportação</span>
        </nav>
        <h2 className="font-display-lg text-display-lg text-on-surface">Exportação</h2>
        <p className="text-on-surface-variant text-body-base mt-xs">
          Gere relatórios e acompanhe o histórico de exportações da sua organização.
        </p>
      </div>

      {/* Report cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-lg mb-2xl">
        {REPORT_TYPES.map((report, i) => (
          <motion.div
            key={report.type}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="glass-card p-lg rounded-2xl flex flex-col"
          >
            <div className="flex items-center gap-md mb-md">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-primary to-secondary flex items-center justify-center text-on-primary shadow-lg border-2 border-primary/20">
                <span className="material-symbols-outlined">{report.icon}</span>
              </div>
              <div>
                <h3 className="font-headline-sm text-headline-sm text-on-surface">{report.label}</h3>
              </div>
            </div>
            <p className="text-on-surface-variant text-body-sm mb-lg flex-1">{report.description}</p>
            <div className="flex gap-sm">
              {FORMATS.map((f) => {
                const key = `${report.type}-${f.format}`;
                const isLoading = requesting === key;
                return (
                  <button
                    key={f.format}
                    onClick={() => handleRequestExport(report.type, f.format)}
                    disabled={isLoading}
                    className="flex-1 flex items-center justify-center gap-xs px-3 py-2 rounded-lg bg-surface-container border border-border-subtle hover:bg-primary-container/20 hover:border-primary/30 hover:text-primary text-on-surface-variant transition-all text-[12px] font-bold uppercase tracking-wider disabled:opacity-50"
                  >
                    {isLoading ? (
                      <span className="animate-spin rounded-full h-3 w-3 border-b-2 border-current"></span>
                    ) : (
                      <span className="material-symbols-outlined text-[16px]">{f.icon}</span>
                    )}
                    {f.label}
                  </button>
                );
              })}
            </div>
          </motion.div>
        ))}
      </div>

      {/* Histórico de Exportações */}
      <div className="mb-lg">
        <h3 className="font-headline-sm text-headline-sm text-on-surface mb-xs">Histórico de Exportações</h3>
        <p className="text-on-surface-variant text-body-sm">Acompanhe o status e baixe os relatórios já gerados.</p>
      </div>

      <div className="glass-panel bg-surface/60 border border-border-subtle rounded-xl overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container-highest/30 border-b border-border-subtle">
              <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Tipo</th>
              <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Formato</th>
              <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Status</th>
              <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Criado em</th>
              <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Tamanho</th>
              <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant text-right">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle/50">
            {logs.map((log, i) => (
              <motion.tr
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.03 }}
                key={log.id}
                className="hover:bg-surface-bright/40 transition-colors"
              >
                <td className="px-lg py-md">
                  <p className="font-label-md text-label-md text-on-surface">{log.type}</p>
                </td>
                <td className="px-lg py-md">
                  <span className="inline-flex items-center px-2 py-1 rounded-full bg-secondary-container/40 text-on-surface-variant text-[11px] font-bold uppercase tracking-wider">
                    {log.format}
                  </span>
                </td>
                <td className="px-lg py-md">
                  <span className={`inline-flex items-center gap-xs px-2 py-1 rounded-full ${(STATUS_CONFIG[log.status] || DEFAULT_STATUS).badge} text-[11px] font-bold uppercase tracking-wider`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${(STATUS_CONFIG[log.status] || DEFAULT_STATUS).dot}`}></span>
                    {log.status}
                  </span>
                </td>
                <td className="px-lg py-md text-on-surface-variant font-label-md text-label-md">{formatDateTime(log.created_at)}</td>
                <td className="px-lg py-md text-on-surface-variant font-label-md text-label-md">{formatSize(log.size_bytes)}</td>
                <td className="px-lg py-md text-right">
                  <button
                    onClick={() => handleDownload(log.id)}
                    className="inline-flex items-center gap-xs px-3 py-1.5 rounded-lg bg-primary-container/20 text-primary hover:bg-primary-container/40 transition-all text-[12px] font-bold"
                  >
                    <span className="material-symbols-outlined text-[16px]">download</span>
                    Baixar
                  </button>
                </td>
              </motion.tr>
            ))}
            {!loading && logs.length === 0 && (
              <tr>
                <td colSpan={6} className="py-12 text-center text-on-surface-variant">
                  Nenhuma exportação encontrada.
                </td>
              </tr>
            )}
            {loading && (
              <tr>
                <td colSpan={6} className="py-12 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
