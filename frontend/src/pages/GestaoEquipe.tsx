import { useState, useEffect } from 'react';
import api from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { Navigate } from 'react-router-dom';
import Layout from '../components/Layout';

export default function GestaoEquipe() {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  const isGerente = user.role === 'GERENTE';
  const isFuncionario = user.role === 'FUNCIONARIO';

  if (isFuncionario) {
    return <Navigate to="/dashboard" />;
  }

  const [employees, setEmployees] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'list' | 'card'>('card');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingEmp, setEditingEmp] = useState<any>(null);
  const [historyModal, setHistoryModal] = useState<{ open: boolean; items: any[]; employeeName: string }>({ open: false, items: [], employeeName: '' });

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    role: '',
    contract_type: 'CLT',
    base_salary: ''
  });

  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const res = await api.get('/employees/');
      setEmployees(res.data);
    } catch (err) {
      console.error("Erro ao carregar equipe", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmployees();
  }, []);

  const handleTerminate = async (id: string) => {
    if (confirm('Deseja realmente desligar este colaborador? O histórico será preservado.')) {
      try {
        const res = await api.post(`/employees/${id}/terminate`);
        setEmployees(employees.map((e: any) => (e.id === id ? res.data : e)));
      } catch (err) {
        console.error('Erro ao desligar', err);
        alert('Erro ao desligar colaborador');
      }
    }
  };

  const handleViewHistory = async (emp: any) => {
    try {
      const res = await api.get(`/employees/${emp.id}/salary-history`);
      setHistoryModal({ open: true, items: res.data.items, employeeName: emp.full_name });
    } catch (err) {
      console.error('Erro ao carregar histórico', err);
      alert('Erro ao carregar histórico salarial');
    }
  };

  const handleEdit = (emp: any) => {
    setEditingEmp(emp);
    setFormData({
      full_name: emp.full_name,
      email: emp.email,
      role: emp.role,
      contract_type: emp.contract_type || 'CLT',
      base_salary: emp.base_salary || ''
    });
    setIsModalOpen(true);
  };

  const handleAddNew = () => {
    setEditingEmp(null);
    setFormData({
      full_name: '',
      email: '',
      role: '',
      contract_type: 'CLT',
      base_salary: ''
    });
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingEmp) {
        const res = await api.put(`/employees/${editingEmp.id}`, { ...formData, base_salary: Number(formData.base_salary) });
        setEmployees(employees.map((emp: any) => emp.id === editingEmp.id ? res.data : emp));
      } else {
        const res = await api.post('/employees/', { ...formData, base_salary: Number(formData.base_salary), is_active: true });
        setEmployees([...employees, res.data]);
      }
      setIsModalOpen(false);
    } catch (err) {
      console.error("Erro ao salvar", err);
      alert('Erro ao salvar funcionário');
    }
  };

  if (loading && employees.length === 0) {
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
      {/* Page Header & Actions */}
      <div className="mb-xl">
        <div className="flex justify-between items-end mb-xl">
          <div>
            <nav className="flex text-body-sm text-outline mb-xs gap-xs items-center">
              <span>Equipe</span>
              <span className="material-symbols-outlined text-[12px]">chevron_right</span>
              <span className="text-primary">Gestão de Funcionários</span>
            </nav>
            <h2 className="font-display-lg text-display-lg text-on-surface">Gestão de Equipe</h2>
            <p className="text-on-surface-variant text-body-base mt-xs">Gerencie os talentos da sua organização em tempo real.</p>
          </div>
          <div className="flex items-center gap-md">
            {/* View Toggle */}
            <div className="flex bg-surface-container-low p-1 rounded-lg border border-border-subtle">
              <button 
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-md transition-all ${viewMode === 'list' ? 'bg-primary-container text-on-primary-container' : 'text-on-surface-variant hover:text-on-surface'}`} 
                title="Ver como Lista"
              >
                <span className="material-symbols-outlined">list</span>
              </button>
              <button 
                onClick={() => setViewMode('card')}
                className={`p-2 rounded-md transition-all ${viewMode === 'card' ? 'bg-primary-container text-on-primary-container' : 'text-on-surface-variant hover:text-on-surface'}`} 
                title="Ver como Cartões"
              >
                <span className="material-symbols-outlined">grid_view</span>
              </button>
            </div>
            {!isGerente && (
              <button 
                onClick={handleAddNew}
                className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10">
                <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>person_add</span>
                Adicionar Funcionário
              </button>
            )}
          </div>
        </div>

        {/* Advanced Filters */}
        <div className="glass-panel bg-surface/60 rounded-xl p-md mb-xl flex flex-wrap items-center gap-md border border-border-subtle">
          <div className="flex items-center gap-sm text-label-md text-on-surface-variant">
            <span className="material-symbols-outlined">filter_list</span>
            <span>Filtrar por:</span>
          </div>
          <select className="bg-surface-container border border-border-subtle rounded-lg text-label-md py-1.5 px-md focus:ring-1 focus:ring-primary focus:border-primary text-on-surface outline-none">
            <option>Todos Departamentos</option>
            <option>Tecnologia</option>
            <option>Financeiro</option>
            <option>Marketing</option>
            <option>Operações</option>
          </select>
          <select className="bg-surface-container border border-border-subtle rounded-lg text-label-md py-1.5 px-md focus:ring-1 focus:ring-primary focus:border-primary text-on-surface outline-none">
            <option>Status: Todos</option>
            <option>Ativo</option>
            <option>Em Férias</option>
            <option>Afastado</option>
          </select>
          <div className="relative ml-4 w-64">
             <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-outline text-sm">search</span>
             <input className="w-full bg-surface-container border border-border-subtle rounded-lg pl-9 pr-4 py-1.5 text-label-md font-label-md focus:ring-1 focus:ring-primary focus:border-primary outline-none text-on-surface placeholder:text-outline-variant" placeholder="Buscar por nome..." type="text"/>
          </div>
          <button className="ml-auto text-primary text-label-md font-label-md hover:underline">Limpar filtros</button>
        </div>

        {viewMode === 'list' ? (
          <div className="glass-panel bg-surface/60 border border-border-subtle rounded-xl overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-container-highest/30 border-b border-border-subtle">
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Funcionário</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Cargo</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Custo/Hora</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Status</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">E-mail</th>
                  {!isGerente && <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant text-right">Ações</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle/50">
                {employees.map((emp: any, i: number) => (
                  <motion.tr 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    key={emp.id} 
                    className="group hover:bg-surface-bright/40 transition-colors"
                  >
                    <td className="px-lg py-md">
                      <div className="flex items-center gap-md">
                        <div className="relative">
                          <div className="w-10 h-10 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center font-bold text-sm">
                            {(emp.full_name || 'NN').substring(0, 2).toUpperCase()}
                          </div>
                          <span className={`absolute bottom-0 right-0 w-3 h-3 ${emp.is_active ? 'bg-success' : 'bg-error'} border-2 border-surface rounded-full`}></span>
                        </div>
                        <div>
                          <p className="font-label-md text-label-md text-on-surface">{emp.full_name}</p>
                          <p className="text-xs text-outline">ID: {emp.id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-lg py-md">
                      <p className="text-label-md text-on-surface">{emp.role}</p>
                    </td>
                    <td className="px-lg py-md text-on-surface-variant font-label-md text-label-md">R$ {Number(emp.hourly_rate ?? 0).toFixed(2)}/h</td>
                    <td className="px-lg py-md">
                      <span className={`inline-flex items-center gap-xs px-2 py-1 rounded-full ${emp.is_active ? 'bg-success/10 text-success' : 'bg-error/10 text-error'} text-[11px] font-bold uppercase tracking-wider`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${emp.is_active ? 'bg-success' : 'bg-error'}`}></span> {emp.is_active ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-lg py-md text-on-surface-variant font-label-md text-label-md">{emp.email}</td>
                    {!isGerente && (
                      <td className="px-lg py-md text-right">
                        <div className="opacity-0 group-hover:opacity-100 transform translate-x-2 group-hover:translate-x-0 transition-all flex justify-end gap-sm">
                          <button onClick={() => handleViewHistory(emp)} className="p-2 rounded-lg bg-surface-container hover:bg-primary-container/20 text-on-surface-variant hover:text-primary transition-all" title="Histórico Salarial">
                            <span className="material-symbols-outlined text-sm">history</span>
                          </button>
                          <button onClick={() => handleEdit(emp)} className="p-2 rounded-lg bg-surface-container hover:bg-primary-container/20 text-on-surface-variant hover:text-primary transition-all">
                            <span className="material-symbols-outlined text-sm">edit</span>
                          </button>
                          <button onClick={() => handleTerminate(emp.id)} className="p-2 rounded-lg bg-surface-container hover:bg-error-container/20 text-on-surface-variant hover:text-error transition-all" title="Desligar">
                            <span className="material-symbols-outlined text-sm">person_off</span>
                          </button>
                        </div>
                      </td>
                    )}
                  </motion.tr>
                ))}
                {employees.length === 0 && (
                  <tr>
                    <td colSpan={isGerente ? 5 : 6} className="py-12 text-center text-on-surface-variant">
                      Nenhum colaborador encontrado.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-lg">
            {employees.map((emp: any, i: number) => (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.05 }}
                key={emp.id} 
                className="glass-card p-lg rounded-2xl hover:scale-[1.02] hover:border-primary/30 transition-all cursor-pointer group flex flex-col h-full"
              >
                <div className="flex justify-between items-start mb-md">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-primary to-secondary flex items-center justify-center text-on-primary font-display-lg text-2xl shadow-lg border-2 border-primary/20">
                    {(emp.full_name || 'NN').substring(0, 2).toUpperCase()}
                  </div>
                  {!isGerente && (
                    <div className="relative group/menu">
                      <button className="text-on-surface-variant hover:text-on-surface p-1 rounded-full hover:bg-surface-bright transition-colors">
                        <span className="material-symbols-outlined">more_vert</span>
                      </button>
                      <div className="absolute right-0 top-full mt-1 w-40 bg-surface-container-high rounded-xl shadow-lg border border-border-subtle opacity-0 invisible group-hover/menu:opacity-100 group-hover/menu:visible transition-all z-10 overflow-hidden">
                        <button onClick={(e) => { e.stopPropagation(); handleViewHistory(emp); }} className="w-full text-left px-4 py-2 text-sm text-on-surface hover:bg-surface-bright flex items-center gap-2"><span className="material-symbols-outlined text-sm">history</span> Histórico</button>
                        <button onClick={(e) => { e.stopPropagation(); handleEdit(emp); }} className="w-full text-left px-4 py-2 text-sm text-on-surface hover:bg-surface-bright flex items-center gap-2"><span className="material-symbols-outlined text-sm">edit</span> Editar</button>
                        <button onClick={(e) => { e.stopPropagation(); handleTerminate(emp.id); }} className="w-full text-left px-4 py-2 text-sm text-error hover:bg-error-container/20 flex items-center gap-2"><span className="material-symbols-outlined text-sm">person_off</span> Desligar</button>
                      </div>
                    </div>
                  )}
                </div>
                
                <h3 className="font-headline-sm text-headline-sm text-on-surface">{emp.full_name}</h3>
                <p className="text-primary text-label-md font-label-md mb-md">{emp.role}</p>
                
                <div className="space-y-sm border-t border-border-subtle pt-md mb-md flex-1">
                  <div className="flex items-center gap-sm text-body-sm text-on-surface-variant">
                    <span className="material-symbols-outlined text-[18px]">mail</span>
                    <span className="truncate">{emp.email}</span>
                  </div>
                  <div className="flex items-center gap-sm text-body-sm text-on-surface-variant">
                    <span className="material-symbols-outlined text-[18px]">phone</span>
                    <span>{emp.phone || '(11) 99999-9999'}</span>
                  </div>
                  <div className="flex items-center gap-sm text-body-sm text-on-surface-variant">
                    <span className="material-symbols-outlined text-[18px]">work</span>
                    <span>{emp.contract_type || 'N/A'}</span>
                  </div>
                  <div className="flex items-center gap-sm text-body-sm text-on-surface-variant">
                    <span className="material-symbols-outlined text-[18px]">payments</span>
                    <span>R$ {Number(emp.hourly_rate ?? 0).toFixed(2)}/h · CTC R$ {Number(emp.ctc_monthly ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                  </div>
                </div>
                
                <div className="flex items-center justify-between mt-auto pt-2">
                  <span className={`inline-flex items-center gap-xs px-2 py-1 rounded-full ${emp.is_active ? 'bg-success/10 text-success' : 'bg-error/10 text-error'} text-[10px] font-bold uppercase tracking-wider`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${emp.is_active ? 'bg-success' : 'bg-error'}`}></span> {emp.is_active ? 'Ativo' : 'Inativo'}
                  </span>
                  <button className="text-primary font-label-md text-label-md group-hover:translate-x-1 transition-transform flex items-center gap-1">
                    Ver Perfil <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
                  </button>
                </div>
              </motion.div>
            ))}

            {!isGerente && (
              <div onClick={handleAddNew} className="border-2 border-dashed border-border-subtle p-lg rounded-2xl flex flex-col items-center justify-center text-on-surface-variant hover:border-primary hover:text-primary transition-all cursor-pointer group bg-surface/20 min-h-[280px]">
                <div className="w-12 h-12 rounded-full border-2 border-current flex items-center justify-center mb-md group-hover:scale-110 transition-transform">
                  <span className="material-symbols-outlined">add</span>
                </div>
                <p className="font-label-md text-label-md">Novo Integrante</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsModalOpen(false)}
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[500px]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">
                  {editingEmp ? 'Editar Funcionário' : 'Novo Funcionário'}
                </h3>
                <button onClick={() => setIsModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSave} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Nome Completo</label>
                  <input required type="text" value={formData.full_name} onChange={(e) => setFormData({...formData, full_name: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">E-mail</label>
                  <input required type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Cargo</label>
                  <input required type="text" value={formData.role} onChange={(e) => setFormData({...formData, role: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-label-md text-on-surface-variant mb-1">Tipo Contrato</label>
                    <select value={formData.contract_type} onChange={(e) => setFormData({...formData, contract_type: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none">
                      <option value="CLT">CLT</option>
                      <option value="PJ">PJ</option>
                      <option value="ESTAGIO">Estágio</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-label-md text-on-surface-variant mb-1">Salário Base (R$)</label>
                    <input required type="number" step="0.01" value={formData.base_salary} onChange={(e) => setFormData({...formData, base_salary: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20">
                    {editingEmp ? 'Salvar Alterações' : 'Adicionar'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Histórico Salarial Modal */}
      <AnimatePresence>
        {historyModal.open && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setHistoryModal({ open: false, items: [], employeeName: '' })}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[600px]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">
                  Histórico Salarial — {historyModal.employeeName}
                </h3>
                <button onClick={() => setHistoryModal({ open: false, items: [], employeeName: '' })} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <div className="overflow-hidden rounded-xl border border-border-subtle">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-highest/30 border-b border-border-subtle">
                      <th className="px-md py-sm font-label-md text-label-md text-on-surface-variant">Data</th>
                      <th className="px-md py-sm font-label-md text-label-md text-on-surface-variant">Salário Base</th>
                      <th className="px-md py-sm font-label-md text-label-md text-on-surface-variant">CTC Mensal</th>
                      <th className="px-md py-sm font-label-md text-label-md text-on-surface-variant">Motivo</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-subtle/50">
                    {historyModal.items.map((item: any) => (
                      <tr key={item.id}>
                        <td className="px-md py-sm text-on-surface-variant font-label-md text-label-md">{item.changed_at}</td>
                        <td className="px-md py-sm text-on-surface-variant font-label-md text-label-md">R$ {Number(item.base_salary ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</td>
                        <td className="px-md py-sm text-on-surface-variant font-label-md text-label-md">R$ {Number(item.ctc_monthly ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</td>
                        <td className="px-md py-sm text-on-surface-variant font-label-md text-label-md">{item.reason}</td>
                      </tr>
                    ))}
                    {historyModal.items.length === 0 && (
                      <tr>
                        <td colSpan={4} className="py-8 text-center text-on-surface-variant">
                          Nenhum registro de histórico encontrado.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </Layout>
  );
}
