import { useEffect, useState } from 'react';
import axios from 'axios';
import api from '../api';
import { useToast } from '../context/ToastContext';
import { useConfirm } from '../context/ConfirmContext';

interface CtcParams {
  clt_multiplier: number;
  pj_multiplier: number;
  estagio_multiplier: number;
  monthly_hours: number;
}

const FIELDS: { key: keyof CtcParams; label: string; help: string; step: number; min: number; max: number }[] = [
  { key: 'clt_multiplier', label: 'Multiplicador CLT', help: 'Salário × multiplicador = custo mensal (encargos, férias, 13º, benefícios). Padrão 1,75.', step: 0.01, min: 1, max: 5 },
  { key: 'pj_multiplier', label: 'Multiplicador PJ', help: 'Padrão 1,10 (impostos e taxas sobre a nota).', step: 0.01, min: 1, max: 5 },
  { key: 'estagio_multiplier', label: 'Multiplicador Estágio', help: 'Padrão 1,10 (seguro e auxílios).', step: 0.01, min: 1, max: 5 },
  { key: 'monthly_hours', label: 'Horas produtivas por mês', help: 'Divide o custo mensal para obter o custo-hora usado no Cost-per-Task. Padrão 176.', step: 1, min: 1, max: 744 },
];

const inputClass =
  'w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none';

export default function CtcParamsSection() {
  const toast = useToast();
  const confirm = useConfirm();
  const [params, setParams] = useState<CtcParams | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get('/company/ctc-params')
      .then((res) => setParams(res.data))
      .catch(() => toast.error('Erro ao carregar os parâmetros de CTC.'));
  }, [toast]);

  const handleSave = async () => {
    if (!params) return;
    const ok = await confirm({
      title: 'Recalcular custos',
      message: 'O custo mensal e o custo-hora de todos os colaboradores ativos serão recalculados com os novos parâmetros. Cada alteração fica registrada no histórico salarial.',
      confirmLabel: 'Salvar e recalcular',
    });
    if (!ok) return;
    setSaving(true);
    try {
      const res = await api.put('/company/ctc-params', params);
      const { recalculated_employees, ...saved } = res.data;
      setParams(saved);
      toast.success(`Parâmetros salvos. ${recalculated_employees} colaborador(es) recalculado(s).`);
    } catch (err) {
      toast.error(axios.isAxiosError(err) ? err.response?.data?.detail || 'Erro ao salvar.' : 'Erro ao salvar.');
    } finally {
      setSaving(false);
    }
  };

  if (!params) {
    return <div className="flex justify-center py-lg"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" /></div>;
  }

  return (
    <div className="glass-card p-lg rounded-2xl max-w-2xl">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-lg">
        {FIELDS.map((f) => (
          <div key={f.key}>
            <label className="block text-label-md text-on-surface-variant mb-1">{f.label}</label>
            <input
              type="number" step={f.step} min={f.min} max={f.max}
              value={params[f.key]}
              onChange={(e) => setParams({ ...params, [f.key]: Number(e.target.value) })}
              className={inputClass}
            />
            <p className="text-[12px] text-on-surface-variant mt-1">{f.help}</p>
          </div>
        ))}
      </div>
      <div className="flex justify-end pt-md mt-lg border-t border-border-subtle">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50"
        >
          {saving ? 'Salvando...' : 'Salvar'}
        </button>
      </div>
    </div>
  );
}
