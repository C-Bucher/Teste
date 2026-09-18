import { useState, useEffect } from 'react';
import api from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { Navigate, useSearchParams } from 'react-router-dom';
import Layout from '../components/Layout';
import { useToast } from '../context/ToastContext';
import { useConfirm } from '../context/ConfirmContext';

type Tab = 'empresa' | 'plano-contas' | 'centros-custo' | 'calendario';

interface Category {
  id: string;
  name: string;
  type: 'RECEITA' | 'DESPESA';
}

interface CostCenter {
  id: string;
  name: string;
  code: string;
}

interface WorkCalendar {
  work_days: number[];
  work_hours_per_day: number;
  holidays: any[];
}

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: 'empresa', label: 'Dados da Empresa', icon: 'domain' },
  { id: 'plano-contas', label: 'Plano de Contas', icon: 'account_tree' },
  { id: 'centros-custo', label: 'Centros de Custo', icon: 'apartment' },
  { id: 'calendario', label: 'Calendário Útil', icon: 'calendar_month' },
];

const WEEKDAYS = [
  { value: 0, label: 'Dom' },
  { value: 1, label: 'Seg' },
  { value: 2, label: 'Ter' },
  { value: 3, label: 'Qua' },
  { value: 4, label: 'Qui' },
  { value: 5, label: 'Sex' },
  { value: 6, label: 'Sáb' },
];

export default function Configuracoes() {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const isAdmin = user.role === 'ADMIN';

  if (!isAdmin) {
    return <Navigate to="/dashboard" />;
  }

  const toast = useToast();
  const confirm = useConfirm();
  const TAB_IDS: Tab[] = ['empresa', 'plano-contas', 'centros-custo', 'calendario'];
  const [searchParams, setSearchParams] = useSearchParams();
  const tabFromUrl = searchParams.get('tab') as Tab | null;
  const [activeTab, setActiveTab] = useState<Tab>(tabFromUrl && TAB_IDS.includes(tabFromUrl) ? tabFromUrl : 'empresa');
  const [loading, setLoading] = useState(true);
  const [savingCompany, setSavingCompany] = useState(false);
  const [savingCalendar, setSavingCalendar] = useState(false);

  const [companyForm, setCompanyForm] = useState({ name: '', cnpj: '', email: '', phone: '', address: '' });

  const [categories, setCategories] = useState<Category[]>([]);
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);
  const [categoryForm, setCategoryForm] = useState<{ name: string; type: 'RECEITA' | 'DESPESA' }>({ name: '', type: 'RECEITA' });

  const [costCenters, setCostCenters] = useState<CostCenter[]>([]);
  const [isCostCenterModalOpen, setIsCostCenterModalOpen] = useState(false);
  const [costCenterForm, setCostCenterForm] = useState({ name: '', code: '' });

  const [calendar, setCalendar] = useState<WorkCalendar>({ work_days: [1, 2, 3, 4, 5], work_hours_per_day: 8, holidays: [] });
  const [calendarLoading, setCalendarLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [companyRes, categoriesRes, costCentersRes] = await Promise.all([
          api.get('/company/'),
          api.get('/company/categories'),
          api.get('/company/cost-centers'),
        ]);
        setCompanyForm({
          name: companyRes.data.name || '',
          cnpj: companyRes.data.cnpj || '',
          email: companyRes.data.email || '',
          phone: companyRes.data.phone || '',
          address: companyRes.data.address || '',
        });
        setCategories(categoriesRes.data);
        setCostCenters(costCentersRes.data);
      } catch (err) {
        console.error('Erro ao carregar configurações', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  useEffect(() => {
    const fetchCalendar = async () => {
      try {
        const res = await api.get('/company/calendar');
        setCalendar(res.data);
      } catch (err) {
        console.error('Erro ao carregar calendário', err);
      } finally {
        setCalendarLoading(false);
      }
    };
    fetchCalendar();
  }, []);

  const handleSaveCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingCompany(true);
    try {
      const res = await api.put('/company/', companyForm);
      setCompanyForm({
        name: res.data.name || '',
        cnpj: res.data.cnpj || '',
        email: res.data.email || '',
        phone: res.data.phone || '',
        address: res.data.address || '',
      });
      toast.success('Dados da empresa salvos.');
    } catch (err) {
      console.error('Erro ao salvar dados da empresa', err);
      toast.error('Erro ao salvar dados da empresa.');
    } finally {
      setSavingCompany(false);
    }
  };

  const handleAddCategory = () => {
    setCategoryForm({ name: '', type: 'RECEITA' });
    setIsCategoryModalOpen(true);
  };

  const handleSaveCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post('/company/categories', categoryForm);
      setCategories([...categories, res.data]);
      setIsCategoryModalOpen(false);
      toast.success('Categoria criada.');
    } catch (err) {
      console.error('Erro ao criar categoria', err);
      toast.error('Erro ao criar categoria.');
    }
  };

  const handleAddCostCenter = () => {
    setCostCenterForm({ name: '', code: '' });
    setIsCostCenterModalOpen(true);
  };

  const handleSaveCostCenter = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post('/company/cost-centers', costCenterForm);
      setCostCenters([...costCenters, res.data]);
      setIsCostCenterModalOpen(false);
      toast.success('Centro de custo criado.');
    } catch (err) {
      console.error('Erro ao criar centro de custo', err);
      toast.error('Erro ao criar centro de custo.');
    }
  };

  const handleDeleteCostCenter = async (id: string) => {
    const ok = await confirm({
      title: 'Remover centro de custo',
      message: 'Deseja realmente remover este centro de custo?',
      confirmLabel: 'Remover',
      isDestructive: true,
    });
    if (!ok) return;
    try {
      await api.delete(`/company/cost-centers/${id}`);
      setCostCenters(costCenters.filter((c) => c.id !== id));
      toast.success('Centro de custo removido.');
    } catch (err) {
      console.error('Erro ao excluir centro de custo', err);
      toast.error('Erro ao excluir centro de custo.');
    }
  };

  const toggleWorkDay = (day: number) => {
    setCalendar((prev) => {
      const has = prev.work_days.includes(day);
      const work_days = has ? prev.work_days.filter((d) => d !== day) : [...prev.work_days, day].sort((a, b) => a - b);
      return { ...prev, work_days };
    });
  };

  const handleSaveCalendar = async () => {
    setSavingCalendar(true);
    try {
      const res = await api.put('/company/calendar', calendar);
      setCalendar(res.data);
      toast.success('Calendário salvo.');
    } catch (err) {
      console.error('Erro ao salvar calendário', err);
      toast.error('Erro ao salvar calendário.');
    } finally {
      setSavingCalendar(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="h-full flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      {/* Page Header */}
      <div className="mb-xl">
        <nav className="flex text-body-sm text-outline mb-xs gap-xs items-center">
          <span>Empresa</span>
          <span className="material-symbols-outlined text-[12px]">chevron_right</span>
          <span className="text-primary">Configurações</span>
        </nav>
        <h2 className="font-display-lg text-display-lg text-on-surface">Configurações da Empresa</h2>
        <p className="text-on-surface-variant text-body-base mt-xs">Gerencie dados cadastrais, plano de contas, centros de custo e calendário de trabalho.</p>
      </div>

      {/* Tab bar */}
      <div className="inline-flex flex-wrap bg-surface-container-low p-1 rounded-lg border border-border-subtle mb-xl gap-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id);
              setSearchParams({ tab: tab.id });
            }}
            className={`flex items-center gap-sm px-lg py-2 rounded-md transition-all font-label-md text-label-md ${
              activeTab === tab.id
                ? 'bg-primary-container text-on-primary-container'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <span className="material-symbols-outlined text-[18px]">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Aba: Dados da Empresa */}
      {activeTab === 'empresa' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-lg rounded-2xl max-w-3xl">
          <h3 className="font-headline-sm text-headline-sm text-on-surface mb-lg">Dados Cadastrais</h3>
          <form onSubmit={handleSaveCompany} className="space-y-md">
            <div>
              <label className="block text-label-md text-on-surface-variant mb-1">Razão Social</label>
              <input
                required
                type="text"
                value={companyForm.name}
                onChange={(e) => setCompanyForm({ ...companyForm, name: e.target.value })}
                className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-label-md text-on-surface-variant mb-1">CNPJ</label>
                <input
                  required
                  type="text"
                  value={companyForm.cnpj}
                  onChange={(e) => setCompanyForm({ ...companyForm, cnpj: e.target.value })}
                  className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                />
              </div>
              <div>
                <label className="block text-label-md text-on-surface-variant mb-1">E-mail</label>
                <input
                  required
                  type="email"
                  value={companyForm.email}
                  onChange={(e) => setCompanyForm({ ...companyForm, email: e.target.value })}
                  className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-label-md text-on-surface-variant mb-1">Telefone</label>
                <input
                  type="text"
                  value={companyForm.phone}
                  onChange={(e) => setCompanyForm({ ...companyForm, phone: e.target.value })}
                  className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                />
              </div>
              <div>
                <label className="block text-label-md text-on-surface-variant mb-1">Endereço</label>
                <input
                  type="text"
                  value={companyForm.address}
                  onChange={(e) => setCompanyForm({ ...companyForm, address: e.target.value })}
                  className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-md mt-lg border-t border-border-subtle">
              <button
                type="submit"
                disabled={savingCompany}
                className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50"
              >
                {savingCompany ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </form>
        </motion.div>
      )}

      {/* Aba: Plano de Contas */}
      {activeTab === 'plano-contas' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex justify-between items-center mb-lg">
            <div>
              <h3 className="font-headline-sm text-headline-sm text-on-surface">Plano de Contas</h3>
              <p className="text-on-surface-variant text-body-sm mt-xs">Categorias de receitas e despesas usadas nos lançamentos financeiros.</p>
            </div>
            <button
              onClick={handleAddCategory}
              className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10"
            >
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>add</span>
              Nova Categoria
            </button>
          </div>

          <div className="glass-panel bg-surface/60 border border-border-subtle rounded-xl overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-container-highest/30 border-b border-border-subtle">
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Nome</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Tipo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle/50">
                {categories.map((cat, i) => (
                  <motion.tr
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.03 }}
                    key={cat.id}
                    className="hover:bg-surface-bright/40 transition-colors"
                  >
                    <td className="px-lg py-md text-label-md text-on-surface">{cat.name}</td>
                    <td className="px-lg py-md">
                      <span
                        className={`inline-flex items-center gap-xs px-2 py-1 rounded-full ${
                          cat.type === 'RECEITA' ? 'bg-success/10 text-success' : 'bg-error/10 text-error'
                        } text-[11px] font-bold uppercase tracking-wider`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${cat.type === 'RECEITA' ? 'bg-success' : 'bg-error'}`}></span>
                        {cat.type === 'RECEITA' ? 'Receita' : 'Despesa'}
                      </span>
                    </td>
                  </motion.tr>
                ))}
                {categories.length === 0 && (
                  <tr>
                    <td colSpan={2} className="py-12 text-center text-on-surface-variant">
                      Nenhuma categoria cadastrada.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Aba: Centros de Custo */}
      {activeTab === 'centros-custo' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <div className="flex justify-between items-center mb-lg">
            <div>
              <h3 className="font-headline-sm text-headline-sm text-on-surface">Centros de Custo</h3>
              <p className="text-on-surface-variant text-body-sm mt-xs">Unidades usadas para segmentar despesas e receitas por área.</p>
            </div>
            <button
              onClick={handleAddCostCenter}
              className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10"
            >
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>add</span>
              Novo Centro de Custo
            </button>
          </div>

          <div className="glass-panel bg-surface/60 border border-border-subtle rounded-xl overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-container-highest/30 border-b border-border-subtle">
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Nome</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Código</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle/50">
                {costCenters.map((cc, i) => (
                  <motion.tr
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.03 }}
                    key={cc.id}
                    className="group hover:bg-surface-bright/40 transition-colors"
                  >
                    <td className="px-lg py-md text-label-md text-on-surface">{cc.name}</td>
                    <td className="px-lg py-md">
                      <span className="px-sm py-0.5 rounded-full text-[11px] font-bold bg-surface-container-highest text-on-surface-variant uppercase tracking-wider">
                        {cc.code}
                      </span>
                    </td>
                    <td className="px-lg py-md text-right">
                      <button
                        onClick={() => handleDeleteCostCenter(cc.id)}
                        className="p-2 rounded-lg bg-surface-container hover:bg-error-container/20 text-on-surface-variant hover:text-error transition-all"
                        title="Excluir centro de custo"
                      >
                        <span className="material-symbols-outlined text-sm">delete</span>
                      </button>
                    </td>
                  </motion.tr>
                ))}
                {costCenters.length === 0 && (
                  <tr>
                    <td colSpan={3} className="py-12 text-center text-on-surface-variant">
                      Nenhum centro de custo cadastrado.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Aba: Calendário Útil */}
      {activeTab === 'calendario' && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="glass-card p-lg rounded-2xl max-w-2xl">
          <h3 className="font-headline-sm text-headline-sm text-on-surface mb-lg">Calendário de Trabalho</h3>

          {calendarLoading ? (
            <div className="flex justify-center py-xl">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : (
            <>
              <div className="mb-lg">
                <label className="block text-label-md text-on-surface-variant mb-sm">Dias Úteis</label>
                <div className="flex flex-wrap gap-sm">
                  {WEEKDAYS.map((day) => {
                    const checked = calendar.work_days.includes(day.value);
                    return (
                      <label key={day.value} className="cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={checked}
                          onChange={() => toggleWorkDay(day.value)}
                        />
                        <div
                          className={`w-14 h-14 rounded-xl flex items-center justify-center font-label-md text-label-md border transition-all ${
                            checked
                              ? 'bg-primary-container text-on-primary-container border-primary'
                              : 'bg-surface-container border-border-subtle text-on-surface-variant hover:border-primary/50'
                          }`}
                        >
                          {day.label}
                        </div>
                      </label>
                    );
                  })}
                </div>
              </div>

              <div className="mb-lg max-w-[20rem]">
                <label className="block text-label-md text-on-surface-variant mb-1">Carga Horária Diária (horas)</label>
                <input
                  type="number"
                  min={1}
                  max={24}
                  value={calendar.work_hours_per_day}
                  onChange={(e) => setCalendar({ ...calendar, work_hours_per_day: Number(e.target.value) })}
                  className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                />
              </div>

              <div className="flex justify-end pt-md mt-lg border-t border-border-subtle">
                <button
                  onClick={handleSaveCalendar}
                  disabled={savingCalendar}
                  className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20 disabled:opacity-50"
                >
                  {savingCalendar ? 'Salvando...' : 'Salvar'}
                </button>
              </div>
            </>
          )}
        </motion.div>
      )}

      {/* Modal: Nova Categoria */}
      <AnimatePresence>
        {isCategoryModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsCategoryModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[440px]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">Nova Categoria</h3>
                <button onClick={() => setIsCategoryModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSaveCategory} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Nome</label>
                  <input
                    required
                    type="text"
                    value={categoryForm.name}
                    onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Tipo</label>
                  <select
                    value={categoryForm.type}
                    onChange={(e) => setCategoryForm({ ...categoryForm, type: e.target.value as 'RECEITA' | 'DESPESA' })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  >
                    <option value="RECEITA">Receita</option>
                    <option value="DESPESA">Despesa</option>
                  </select>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsCategoryModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20">
                    Adicionar
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Modal: Novo Centro de Custo */}
      <AnimatePresence>
        {isCostCenterModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsCostCenterModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[440px]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">Novo Centro de Custo</h3>
                <button onClick={() => setIsCostCenterModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSaveCostCenter} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Nome</label>
                  <input
                    required
                    type="text"
                    value={costCenterForm.name}
                    onChange={(e) => setCostCenterForm({ ...costCenterForm, name: e.target.value })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Código</label>
                  <input
                    required
                    type="text"
                    value={costCenterForm.code}
                    onChange={(e) => setCostCenterForm({ ...costCenterForm, code: e.target.value.toUpperCase() })}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsCostCenterModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20">
                    Adicionar
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </Layout>
  );
}
