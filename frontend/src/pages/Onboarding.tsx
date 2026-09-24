import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import api from '../api';
import { useToast } from '../context/ToastContext';
import PermissionMatrix from '../components/PermissionMatrix';
import IntegrationsStatus from '../components/IntegrationsStatus';

const STEPS = [
  { id: 1, label: 'Dados da Empresa' },
  { id: 2, label: 'Hierarquia de Cargos' },
  { id: 3, label: 'Conexões de API' },
];

export default function Onboarding() {
  const navigate = useNavigate();
  const toast = useToast();
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [savingCompany, setSavingCompany] = useState(false);
  const [companyForm, setCompanyForm] = useState({ name: '', cnpj: '', email: '', phone: '', address: '' });

  useEffect(() => {
    api.get('/company/').then((res) => {
      const company = res.data;
      setCompanyForm({
        name: company.name || '',
        cnpj: company.cnpj || '',
        email: company.email || '',
        phone: company.phone || '',
        address: company.address || '',
      });
    }).catch((err) => console.error('Erro ao carregar dados da empresa', err));
  }, []);

  const handleSaveCompanyStep = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingCompany(true);
    try {
      await api.put('/company/', companyForm);
      toast.success('Dados da empresa salvos.');
      setStep(2);
    } catch (err) {
      console.error('Erro ao salvar dados da empresa', err);
      toast.error('Erro ao salvar dados da empresa.');
    } finally {
      setSavingCompany(false);
    }
  };

  const handleFinish = async () => {
    setSaving(true);
    try {
      const res = await api.post('/company/onboarding/complete');
      localStorage.setItem('company', JSON.stringify(res.data));
      toast.success('Configuração concluída!');
      navigate('/dashboard');
    } catch (err) {
      console.error('Erro ao concluir configuração', err);
      toast.error('Erro ao concluir configuração.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-surface flex items-center justify-center p-lg">
      <div className="w-full max-w-3xl">
        <div className="flex items-center justify-center gap-md mb-2xl">
          {STEPS.map((s, i) => (
            <div key={s.id} className="flex items-center gap-md">
              <div className={`flex items-center gap-sm ${step >= s.id ? 'text-primary' : 'text-on-surface-variant'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-label-md border ${step >= s.id ? 'bg-primary-container border-primary text-on-primary-container' : 'border-border-subtle'}`}>
                  {s.id}
                </div>
                <span className="text-label-md hidden sm:inline">{s.label}</span>
              </div>
              {i < STEPS.length - 1 && <div className="w-8 h-px bg-border-subtle" />}
            </div>
          ))}
        </div>

        <div className="glass-card p-xl rounded-2xl">
          {step === 1 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              <h2 className="font-headline-sm text-headline-sm text-on-surface mb-lg">Dados da Empresa</h2>
              <form onSubmit={handleSaveCompanyStep} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Razão Social</label>
                  <input required type="text" value={companyForm.name} onChange={(e) => setCompanyForm({ ...companyForm, name: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-label-md text-on-surface-variant mb-1">CNPJ</label>
                    <input required type="text" value={companyForm.cnpj} onChange={(e) => setCompanyForm({ ...companyForm, cnpj: e.target.value })}
                      className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                  </div>
                  <div>
                    <label className="block text-label-md text-on-surface-variant mb-1">E-mail</label>
                    <input required type="email" value={companyForm.email} onChange={(e) => setCompanyForm({ ...companyForm, email: e.target.value })}
                      className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                  </div>
                </div>
                <div className="flex justify-end pt-md mt-lg border-t border-border-subtle">
                  <button type="submit" disabled={savingCompany}
                    className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                    {savingCompany ? 'Salvando...' : 'Próximo'}
                  </button>
                </div>
              </form>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              <h2 className="font-headline-sm text-headline-sm text-on-surface mb-lg">Hierarquia de Cargos</h2>
              <p className="text-on-surface-variant text-body-sm mb-lg">Defina o que Gerentes e Funcionários vão poder ver quando você adicioná-los depois. Você pode ajustar isso a qualquer momento em Configurações.</p>
              <PermissionMatrix />
              <div className="flex justify-between pt-lg mt-lg border-t border-border-subtle">
                <button onClick={() => setStep(1)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">Voltar</button>
                <button onClick={() => setStep(3)} className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20">Próximo</button>
              </div>
            </motion.div>
          )}

          {step === 3 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              <h2 className="font-headline-sm text-headline-sm text-on-surface mb-lg">Conexões de API</h2>
              <p className="text-on-surface-variant text-body-sm mb-lg">Confirme que a infraestrutura do sistema está saudável antes de começar a usar.</p>
              <IntegrationsStatus />
              <div className="flex justify-between pt-lg mt-lg border-t border-border-subtle">
                <button onClick={() => setStep(2)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">Voltar</button>
                <button onClick={handleFinish} disabled={saving}
                  className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50">
                  {saving ? 'Concluindo...' : 'Concluir Configuração'}
                </button>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
}
