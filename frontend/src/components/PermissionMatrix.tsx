import { useState, useEffect } from 'react';
import api from '../api';
import { useToast } from '../context/ToastContext';

const MODULE_LABELS: Record<string, string> = {
  dashboard: 'Dashboard',
  kanban: 'Projetos (Kanban)',
  equipe: 'Gestão de Equipe',
  financeiro: 'Financeiro',
  fornecedores: 'Fornecedores',
  configuracoes: 'Configurações',
  exportacao: 'Exportação',
  ia: 'IA Empresarial',
};

const MODULES = Object.keys(MODULE_LABELS);
const ROLES: { key: 'GERENTE' | 'FUNCIONARIO'; label: string }[] = [
  { key: 'GERENTE', label: 'Gerente' },
  { key: 'FUNCIONARIO', label: 'Funcionário' },
];

interface Props {
  onSaved?: () => void;
}

export default function PermissionMatrix({ onSaved }: Props) {
  const toast = useToast();
  const [matrix, setMatrix] = useState<Record<string, string[]>>({ GERENTE: [], FUNCIONARIO: [] });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get('/permissions/matrix').then((res) => setMatrix(res.data)).finally(() => setLoading(false));
  }, []);

  const toggle = (role: string, moduleKey: string) => {
    setMatrix((prev) => {
      const current = prev[role] || [];
      const has = current.includes(moduleKey);
      return { ...prev, [role]: has ? current.filter((m) => m !== moduleKey) : [...current, moduleKey] };
    });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await api.put('/permissions/matrix', matrix);
      setMatrix(res.data);
      toast.success('Permissões salvas.');
      onSaved?.();
    } catch (err) {
      console.error('Erro ao salvar permissões', err);
      toast.error('Erro ao salvar permissões.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-xl">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="glass-panel bg-surface/60 border border-border-subtle rounded-xl overflow-hidden">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-surface-container-highest/30 border-b border-border-subtle">
            <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Módulo</th>
            <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant text-center">Admin</th>
            {ROLES.map((r) => (
              <th key={r.key} className="px-lg py-md font-label-md text-label-md text-on-surface-variant text-center">{r.label}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border-subtle/50">
          {MODULES.map((moduleKey) => (
            <tr key={moduleKey} className="hover:bg-surface-bright/40 transition-colors">
              <td className="px-lg py-md text-label-md text-on-surface">{MODULE_LABELS[moduleKey]}</td>
              <td className="px-lg py-md text-center">
                <input type="checkbox" checked disabled className="w-4 h-4 accent-primary opacity-60" />
              </td>
              {ROLES.map((r) => (
                <td key={r.key} className="px-lg py-md text-center">
                  <input
                    type="checkbox"
                    checked={(matrix[r.key] || []).includes(moduleKey)}
                    onChange={() => toggle(r.key, moduleKey)}
                    className="w-4 h-4 accent-primary cursor-pointer"
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex justify-end p-lg border-t border-border-subtle">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50"
        >
          {saving ? 'Salvando...' : 'Salvar Permissões'}
        </button>
      </div>
    </div>
  );
}
