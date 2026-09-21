import { useState, useEffect } from 'react';
import api from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { Navigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { usePermissions } from '../hooks/usePermissions';
import { useToast } from '../context/ToastContext';
import { useConfirm } from '../context/ConfirmContext';

function FornecedoresContent() {
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const toast = useToast();
  const confirm = useConfirm();

  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'list' | 'card'>('card');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSup, setEditingSup] = useState<any>(null);

  const [formData, setFormData] = useState({
    name: '',
    cnpj_cpf: '',
    category: '',
    email: ''
  });

  const fetchSuppliers = async () => {
    setLoading(true);
    try {
      const res = await api.get('/suppliers/');
      setSuppliers(res.data);
    } catch (err) {
      console.error("Erro ao carregar fornecedores", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const handleDeactivate = async (id: string) => {
    const ok = await confirm({
      title: 'Desativar fornecedor',
      message: 'Deseja realmente desativar este fornecedor?',
      confirmLabel: 'Desativar',
      isDestructive: true,
    });
    if (!ok) return;
    try {
      const res = await api.put(`/suppliers/${id}`, { is_active: false });
      setSuppliers(suppliers.map((s: any) => s.id === id ? res.data : s));
      toast.success('Fornecedor desativado.');
    } catch (err) {
      console.error("Erro ao desativar", err);
      toast.error('Erro ao desativar fornecedor.');
    }
  };

  const handleEdit = (sup: any) => {
    setEditingSup(sup);
    setFormData({
      name: sup.name,
      cnpj_cpf: sup.cnpj_cpf,
      category: sup.category || '',
      email: sup.email
    });
    setIsModalOpen(true);
  };

  const handleAddNew = () => {
    setEditingSup(null);
    setFormData({
      name: '',
      cnpj_cpf: '',
      category: '',
      email: ''
    });
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingSup) {
        const res = await api.put(`/suppliers/${editingSup.id}`, { ...formData });
        setSuppliers(suppliers.map((sup: any) => sup.id === editingSup.id ? res.data : sup));
        toast.success('Fornecedor atualizado.');
      } else {
        const res = await api.post('/suppliers/', { ...formData });
        setSuppliers([...suppliers, res.data]);
        toast.success('Fornecedor cadastrado.');
      }
      setIsModalOpen(false);
    } catch (err) {
      console.error("Erro ao salvar", err);
      toast.error('Erro ao salvar fornecedor.');
    }
  };

  if (loading && suppliers.length === 0) {
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
              <span>Empresa</span>
              <span className="material-symbols-outlined text-[12px]">chevron_right</span>
              <span className="text-primary">Fornecedores</span>
            </nav>
            <h2 className="font-display-lg text-display-lg text-on-surface">Fornecedores</h2>
            <p className="text-on-surface-variant text-body-base mt-xs">Gerencie os fornecedores e prestadores de serviço da sua organização.</p>
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
            <button
              onClick={handleAddNew}
              className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-3 rounded-xl hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>add_business</span>
              Adicionar Fornecedor
            </button>
          </div>
        </div>

        {viewMode === 'list' ? (
          <div className="glass-panel bg-surface/60 border border-border-subtle rounded-xl overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-surface-container-highest/30 border-b border-border-subtle">
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Fornecedor</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">CNPJ/CPF</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Categoria</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Status</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">E-mail</th>
                  <th className="px-lg py-md font-label-md text-label-md text-on-surface-variant text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle/50">
                {suppliers.map((sup: any, i: number) => (
                  <motion.tr
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    key={sup.id}
                    className="group hover:bg-surface-bright/40 transition-colors"
                  >
                    <td className="px-lg py-md">
                      <div className="flex items-center gap-md">
                        <div className="relative">
                          <div className="w-10 h-10 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center font-bold text-sm">
                            {(sup.name || 'NN').substring(0, 2).toUpperCase()}
                          </div>
                          <span className={`absolute bottom-0 right-0 w-3 h-3 ${sup.is_active ? 'bg-success' : 'bg-error'} border-2 border-surface rounded-full`}></span>
                        </div>
                        <div>
                          <p className="font-label-md text-label-md text-on-surface">{sup.name}</p>
                          <p className="text-xs text-outline">ID: {sup.id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-lg py-md">
                      <p className="text-label-md text-on-surface">{sup.cnpj_cpf}</p>
                    </td>
                    <td className="px-lg py-md">
                      <span className="inline-flex items-center px-2 py-1 rounded-full bg-secondary-container/40 text-on-surface-variant text-[11px] font-bold uppercase tracking-wider">
                        {sup.category}
                      </span>
                    </td>
                    <td className="px-lg py-md">
                      <span className={`inline-flex items-center gap-xs px-2 py-1 rounded-full ${sup.is_active ? 'bg-success/10 text-success' : 'bg-error/10 text-error'} text-[11px] font-bold uppercase tracking-wider`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${sup.is_active ? 'bg-success' : 'bg-error'}`}></span> {sup.is_active ? 'Ativo' : 'Inativo'}
                      </span>
                    </td>
                    <td className="px-lg py-md text-on-surface-variant font-label-md text-label-md">{sup.email}</td>
                    <td className="px-lg py-md text-right">
                      <div className="opacity-0 group-hover:opacity-100 transform translate-x-2 group-hover:translate-x-0 transition-all flex justify-end gap-sm">
                        <button onClick={() => handleEdit(sup)} className="p-2 rounded-lg bg-surface-container hover:bg-primary-container/20 text-on-surface-variant hover:text-primary transition-all">
                          <span className="material-symbols-outlined text-sm">edit</span>
                        </button>
                        {sup.is_active && (
                          <button onClick={() => handleDeactivate(sup.id)} className="p-2 rounded-lg bg-surface-container hover:bg-error-container/20 text-on-surface-variant hover:text-error transition-all">
                            <span className="material-symbols-outlined text-sm">block</span>
                          </button>
                        )}
                      </div>
                    </td>
                  </motion.tr>
                ))}
                {suppliers.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-on-surface-variant">
                      Nenhum fornecedor encontrado.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-lg">
            {suppliers.map((sup: any, i: number) => (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.05 }}
                key={sup.id}
                className="glass-card p-lg rounded-2xl hover:scale-[1.02] hover:border-primary/30 transition-all cursor-pointer group flex flex-col h-full"
              >
                <div className="flex justify-between items-start mb-md">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-primary to-secondary flex items-center justify-center text-on-primary font-display-lg text-2xl shadow-lg border-2 border-primary/20">
                    {(sup.name || 'NN').substring(0, 2).toUpperCase()}
                  </div>
                  <div className="relative group/menu">
                    <button className="text-on-surface-variant hover:text-on-surface p-1 rounded-full hover:bg-surface-bright transition-colors">
                      <span className="material-symbols-outlined">more_vert</span>
                    </button>
                    <div className="absolute right-0 top-full mt-1 w-36 bg-surface-container-high rounded-xl shadow-lg border border-border-subtle opacity-0 invisible group-hover/menu:opacity-100 group-hover/menu:visible transition-all z-10 overflow-hidden">
                      <button onClick={(e) => { e.stopPropagation(); handleEdit(sup); }} className="w-full text-left px-4 py-2 text-sm text-on-surface hover:bg-surface-bright flex items-center gap-2"><span className="material-symbols-outlined text-sm">edit</span> Editar</button>
                      {sup.is_active && (
                        <button onClick={(e) => { e.stopPropagation(); handleDeactivate(sup.id); }} className="w-full text-left px-4 py-2 text-sm text-error hover:bg-error-container/20 flex items-center gap-2"><span className="material-symbols-outlined text-sm">block</span> Desativar</button>
                      )}
                    </div>
                  </div>
                </div>

                <h3 className="font-headline-sm text-headline-sm text-on-surface">{sup.name}</h3>
                <p className="text-primary text-label-md font-label-md mb-md">{sup.category}</p>

                <div className="space-y-sm border-t border-border-subtle pt-md mb-md flex-1">
                  <div className="flex items-center gap-sm text-body-sm text-on-surface-variant">
                    <span className="material-symbols-outlined text-[18px]">mail</span>
                    <span className="truncate">{sup.email}</span>
                  </div>
                  <div className="flex items-center gap-sm text-body-sm text-on-surface-variant">
                    <span className="material-symbols-outlined text-[18px]">badge</span>
                    <span>{sup.cnpj_cpf}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between mt-auto pt-2">
                  <span className={`inline-flex items-center gap-xs px-2 py-1 rounded-full ${sup.is_active ? 'bg-success/10 text-success' : 'bg-error/10 text-error'} text-[10px] font-bold uppercase tracking-wider`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${sup.is_active ? 'bg-success' : 'bg-error'}`}></span> {sup.is_active ? 'Ativo' : 'Inativo'}
                  </span>
                </div>
              </motion.div>
            ))}

            <div onClick={handleAddNew} className="border-2 border-dashed border-border-subtle p-lg rounded-2xl flex flex-col items-center justify-center text-on-surface-variant hover:border-primary hover:text-primary transition-all cursor-pointer group bg-surface/20 min-h-[280px]">
              <div className="w-12 h-12 rounded-full border-2 border-current flex items-center justify-center mb-md group-hover:scale-110 transition-transform">
                <span className="material-symbols-outlined">add</span>
              </div>
              <p className="font-label-md text-label-md">Novo Fornecedor</p>
            </div>
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
                  {editingSup ? 'Editar Fornecedor' : 'Novo Fornecedor'}
                </h3>
                <button onClick={() => setIsModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSave} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Nome / Razão Social</label>
                  <input required type="text" value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">CNPJ/CPF</label>
                  <input required type="text" value={formData.cnpj_cpf} onChange={(e) => setFormData({...formData, cnpj_cpf: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">E-mail</label>
                  <input required type="email" value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Categoria</label>
                  <select required value={formData.category} onChange={(e) => setFormData({...formData, category: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none">
                    <option value="" disabled>Selecione...</option>
                    <option value="Cloud">Cloud</option>
                    <option value="Bancario">Bancário</option>
                    <option value="Dev Tools">Dev Tools</option>
                    <option value="Contabilidade">Contabilidade</option>
                    <option value="Aluguel">Aluguel</option>
                    <option value="Outros">Outros</option>
                  </select>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20">
                    {editingSup ? 'Salvar Alterações' : 'Adicionar'}
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

export default function Fornecedores() {
  const { loading, can } = usePermissions();
  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </Layout>
    );
  }
  if (!can('fornecedores')) return <Navigate to="/dashboard" />;
  return <FornecedoresContent />;
}
