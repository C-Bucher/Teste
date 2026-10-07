import { useState, useEffect } from 'react';
import api from '../api';
import { defer } from '../utils/defer';

interface Integration {
  key: string;
  label: string;
  status: string;
}

const STATUS_STYLES: Record<string, string> = {
  online: 'bg-success/10 text-success',
  configured: 'bg-success/10 text-success',
  offline: 'bg-error/10 text-error',
  unconfigured: 'bg-warning/10 text-warning',
};

const STATUS_LABELS: Record<string, string> = {
  online: 'Online',
  configured: 'Configurada',
  offline: 'Offline',
  unconfigured: 'Não configurada',
};

export default function IntegrationsStatus() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await api.get('/system/integrations');
      setIntegrations(res.data.integrations);
      setLastChecked(new Date());
    } catch (err) {
      console.error('Erro ao verificar integrações', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    defer(fetchStatus);
  }, []);

  return (
    <div className="space-y-md">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
        {integrations.map((it) => (
          <div key={it.key} className="glass-card p-lg rounded-2xl flex items-center justify-between">
            <span className="text-label-md text-on-surface">{it.label}</span>
            <span className={`inline-flex items-center gap-xs px-2 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider ${STATUS_STYLES[it.status] || 'bg-surface-container-highest text-on-surface-variant'}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${it.status === 'online' || it.status === 'configured' ? 'bg-success' : it.status === 'offline' ? 'bg-error' : 'bg-warning'}`}></span>
              {STATUS_LABELS[it.status] || it.status}
            </span>
          </div>
        ))}
        {loading && integrations.length === 0 && (
          <div className="col-span-2 flex justify-center py-xl">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        )}
      </div>
      <div className="flex items-center justify-between pt-sm">
        <span className="text-body-sm text-on-surface-variant">
          {lastChecked ? `Última checagem: ${lastChecked.toLocaleTimeString('pt-BR')}` : ''}
        </span>
        <button
          onClick={fetchStatus}
          disabled={loading}
          className="px-4 py-2 rounded-lg font-label-md text-label-md bg-surface-container border border-border-subtle hover:bg-surface-container-highest transition-colors disabled:opacity-50"
        >
          Testar Conexão
        </button>
      </div>
    </div>
  );
}
