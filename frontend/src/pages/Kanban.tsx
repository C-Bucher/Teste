import { useState, useEffect } from 'react';
import api from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { useSearchParams } from 'react-router-dom';
import Layout from '../components/Layout';
import { useToast } from '../context/ToastContext';

export default function Kanban() {
  const toast = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState<any[]>([]);
  const [clients, setClients] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectIdState] = useState<string | null>(searchParams.get('project'));
  const [boardData, setBoardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Wrapper que sincroniza estado e URL ao mesmo tempo
  const setSelectedProjectId = (id: string | null) => {
    setSelectedProjectIdState(id);
    if (id) setSearchParams({ project: id });
    else setSearchParams({});
  };

  // Drag state
  const [draggedCardId, setDraggedCardId] = useState<string | null>(null);

  // Modal State for New Task
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [addingToCol, setAddingToCol] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'MEDIA'
  });

  // Modal State for New Project / New Client
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  const [projectForm, setProjectForm] = useState({ name: '', description: '', client_id: '', start_date: '', end_date: '' });
  const [isClientModalOpen, setIsClientModalOpen] = useState(false);
  const [clientForm, setClientForm] = useState({ name: '', email: '', phone: '', cnpj: '', contact_name: '', segment: '' });

  // Timer State
  const [activeTimerCardId, setActiveTimerCardId] = useState<string | null>(null);

  // Card Detail Panel State
  const [detailCard, setDetailCard] = useState<any>(null);
  const [commentText, setCommentText] = useState('');

  useEffect(() => {
    const fetchInitial = async () => {
      try {
        const [projRes, clientsRes] = await Promise.all([
          api.get('/kanban/projects'),
          api.get('/kanban/clients')
        ]);
        setProjects(projRes.data);
        setClients(clientsRes.data);
        const urlProjectId = searchParams.get('project');
        if (urlProjectId && projRes.data.some((p: any) => p.id === urlProjectId)) {
          // Restaura projeto da URL
          setSelectedProjectIdState(urlProjectId);
        } else if (projRes.data.length > 0) {
          // Seleciona o primeiro projeto e salva na URL
          setSelectedProjectId(projRes.data[0].id);
        } else {
          setLoading(false);
        }
      } catch (err) {
        console.error("Erro ao carregar projetos", err);
        setLoading(false);
      }
    };
    fetchInitial();
  }, []);

  useEffect(() => {
    if (selectedProjectId) {
      fetchBoard(selectedProjectId);
    }
  }, [selectedProjectId]);

  const fetchBoard = async (pid: string) => {
    setLoading(true);
    try {
      const res = await api.get(`/kanban/projects/${pid}/board`);
      setBoardData(res.data);
    } catch (err) {
      console.error("Erro ao carregar board", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDragStart = (e: React.DragEvent, cardId: string) => {
    setDraggedCardId(cardId);
    e.dataTransfer.effectAllowed = 'move';
    // Firefox requires some data to be set
    e.dataTransfer.setData('text/plain', cardId);
    // Add visual feedback
    setTimeout(() => {
      if (e.target instanceof HTMLElement) {
        e.target.style.opacity = '0.5';
      }
    }, 0);
  };

  const handleDragEnd = (e: React.DragEvent) => {
    if (e.target instanceof HTMLElement) {
      e.target.style.opacity = '1';
    }
    setDraggedCardId(null);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = async (e: React.DragEvent, targetColId: string) => {
    e.preventDefault();
    if (!draggedCardId) return;

    // Find current col of the card
    let sourceColId = null;
    for (const col of boardData.columns) {
      if (col.cards.find((c: any) => c.id === draggedCardId)) {
        sourceColId = col.id;
        break;
      }
    }

    if (sourceColId === targetColId) return; // Didn't change column

    // Optimistic UI Update
    const newColumns = [...boardData.columns];
    const sColIndex = newColumns.findIndex(c => c.id === sourceColId);
    const tColIndex = newColumns.findIndex(c => c.id === targetColId);
    
    const cardObj = newColumns[sColIndex].cards.find((c:any) => c.id === draggedCardId);
    newColumns[sColIndex].cards = newColumns[sColIndex].cards.filter((c:any) => c.id !== draggedCardId);
    
    // Update status based on standard column patterns or backend logic
    if (targetColId.includes('col-')) {
       // just move it
    }

    newColumns[tColIndex].cards.push(cardObj);
    
    setBoardData({ ...boardData, columns: newColumns });

    try {
      await api.post(`/kanban/cards/${draggedCardId}/move`, { column_id: targetColId });
      // Reload from server to ensure sync (optional, can just rely on optimistic)
    } catch (err) {
      console.error("Erro ao mover card", err);
      // Revert in case of error
      fetchBoard(selectedProjectId!);
    }
  };

  const handleAddNewCard = (colId: string) => {
    setAddingToCol(colId);
    setFormData({ title: '', description: '', priority: 'MEDIA' });
    setIsModalOpen(true);
  };

  const handleSaveCard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!addingToCol) return;
    try {
      await api.post('/kanban/cards', {
        column_id: addingToCol,
        title: formData.title,
        description: formData.description,
        priority: formData.priority,
        project_id: selectedProjectId
      });
      setIsModalOpen(false);
      fetchBoard(selectedProjectId!);
      toast.success('Tarefa criada.');
    } catch (err) {
      console.error("Erro ao criar tarefa", err);
      toast.error('Erro ao criar tarefa.');
    }
  };

  const handleSaveProject = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post('/kanban/projects', projectForm);
      setProjects([...projects, res.data]);
      setSelectedProjectId(res.data.id);
      setIsProjectModalOpen(false);
      setProjectForm({ name: '', description: '', client_id: '', start_date: '', end_date: '' });
      toast.success('Projeto criado.');
    } catch (err) {
      console.error('Erro ao criar projeto', err);
      toast.error('Erro ao criar projeto.');
    }
  };

  const handleSaveClient = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post('/kanban/clients', clientForm);
      setClients([...clients, res.data]);
      setProjectForm({ ...projectForm, client_id: res.data.id });
      setIsClientModalOpen(false);
      setClientForm({ name: '', email: '', phone: '', cnpj: '', contact_name: '', segment: '' });
      toast.success('Cliente criado.');
    } catch (err) {
      console.error('Erro ao criar cliente', err);
      toast.error('Erro ao criar cliente.');
    }
  };

  const handleToggleTimer = async (cardId: string) => {
    try {
      if (activeTimerCardId === cardId) {
        await api.post(`/kanban/cards/${cardId}/timer/stop`);
        setActiveTimerCardId(null);
      } else {
        await api.post(`/kanban/cards/${cardId}/timer/start`);
        setActiveTimerCardId(cardId);
      }
      fetchBoard(selectedProjectId!);
    } catch (err) {
      console.error('Erro ao controlar timer', err);
    }
  };

  const handleAddComment = async () => {
    if (!commentText.trim() || !detailCard) return;
    try {
      const res = await api.post(`/kanban/cards/${detailCard.id}/comments`, { content: commentText });
      setDetailCard({ ...detailCard, comments: [...(detailCard.comments || []), res.data] });
      setCommentText('');
    } catch (err) {
      console.error('Erro ao comentar', err);
    }
  };

  if (loading && !boardData) {
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
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between mb-lg shrink-0">
          <div>
            <div className="flex items-center gap-sm mb-2">
              <select 
                className="bg-surface-container-high border border-border-subtle rounded-lg px-md py-2 font-headline-sm text-on-surface outline-none focus:ring-1 focus:ring-primary"
                value={selectedProjectId || ''}
                onChange={(e) => setSelectedProjectId(e.target.value)}
              >
                {projects.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <p className="font-body-base text-body-base text-on-surface-variant">
              {boardData?.project?.description || 'Visualize o fluxo de trabalho.'}
            </p>
          </div>
          <div className="flex gap-md">
            <button className="flex items-center gap-sm bg-surface-container-high border border-border-subtle px-md py-sm rounded-lg hover:bg-surface-bright transition-all font-label-md">
              <span className="material-symbols-outlined">filter_list</span> Filtrar
            </button>
            <button onClick={() => setIsProjectModalOpen(true)} className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-sm rounded-lg hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>add</span> Novo Projeto
            </button>
          </div>
        </div>

        {/* Kanban Board */}
        <div className="flex gap-lg flex-1 min-w-[1200px] overflow-x-auto overflow-y-hidden pb-4">
          {boardData?.columns?.map((column: any, i: number) => {
            // Determine colors dynamically based on order/name
            let colorClass = 'bg-outline';
            let bgClass = 'bg-surface-container-low/60 border-border-subtle';
            if (column.name.toLowerCase().includes('andamento') || column.name.toLowerCase().includes('desenvolvimento')) {
              colorClass = 'bg-primary';
              bgClass = 'bg-primary-container/10 border-primary/15';
            } else if (column.name.toLowerCase().includes('revisao')) {
              colorClass = 'bg-warning';
              bgClass = 'bg-surface-container-low/60 border-warning/15';
            } else if (column.name.toLowerCase().includes('concluido')) {
              colorClass = 'bg-success';
              bgClass = 'bg-success/10 border-success/15';
            }

            return (
              <motion.div
                key={column.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex-1 flex flex-col min-w-[300px] max-w-[350px]"
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, column.id)}
              >
                {/* Column Header */}
                <div className="flex items-center justify-between px-md mb-md py-xs">
                  <div className="flex items-center gap-sm">
                    <span className={`w-2.5 h-2.5 rounded-full ${colorClass}`}></span>
                    <span className="font-headline-sm text-headline-sm uppercase tracking-wider text-on-surface truncate max-w-[200px]">
                      {column.name}
                    </span>
                    <span className="bg-surface-container-highest px-sm py-xs rounded-full text-xs text-on-surface-variant font-bold">
                      {column.cards?.length || 0}
                    </span>
                  </div>
                  <button className="text-outline hover:text-on-surface">
                    <span className="material-symbols-outlined">more_horiz</span>
                  </button>
                </div>

                {/* Column Cards Container */}
                <div className={`kanban-column flex-1 overflow-y-auto p-md space-y-md rounded-xl backdrop-blur-sm border ${bgClass}`}>
                  {column.cards?.map((card: any) => {
                    const isDone = card.status === 'CONCLUIDO';
                    const isActive = card.status === 'EM_ANDAMENTO';
                    const tagColor = card.priority === 'URGENTE' ? 'bg-error-container/20 text-error' :
                                     card.priority === 'ALTA' ? 'bg-warning-container/20 text-warning' :
                                     card.priority === 'BAIXA' ? 'bg-outline-variant/30 text-outline' :
                                     'bg-primary-container/20 text-primary';

                    return (
                      <div
                        key={card.id}
                        draggable
                        onDragStart={(e) => handleDragStart(e, card.id)}
                        onDragEnd={handleDragEnd}
                        onClick={() => setDetailCard(card)}
                        className={`group ${isDone ? 'bg-surface-container-high/90' : 'bg-surface-container-highest'} rounded-xl border ${isActive ? 'border-l-4 border-l-primary border-outline-variant/70' : 'border border-outline-variant/70'} p-md shadow-md hover:shadow-lg transition-all duration-300 cursor-grab active:cursor-grabbing hover:border-primary/40 hover:-translate-y-0.5`}
                      >
                        <div className="flex justify-between items-start mb-sm">
                          <div className="flex gap-sm flex-wrap">
                            <span className={`px-sm py-1 ${tagColor} text-[10px] font-bold rounded-full uppercase`}>
                              {card.priority}
                            </span>
                          </div>
                          {card.total_time_seconds > 0 && (
                            <div className="flex items-center gap-xs px-sm py-1 bg-success/10 text-success rounded-full timer-pulse">
                              <span className="material-symbols-outlined text-xs" style={{ fontVariationSettings: "'FILL' 1" }}>timer</span>
                              <span className="text-[10px] font-bold">{Math.floor(card.total_time_seconds / 3600)}h</span>
                            </div>
                          )}
                          {isDone && (
                            <span className="material-symbols-outlined text-success text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                          )}
                        </div>
                        
                        <h3 className={`font-headline-sm text-headline-sm ${isDone ? 'text-on-surface-variant line-through' : 'text-on-surface'} mb-xs leading-tight`}>
                          {card.title}
                        </h3>
                        <p className={`font-body-sm text-body-sm ${isDone ? 'text-outline' : 'text-on-surface-variant'} line-clamp-2 mb-md`}>
                          {card.description}
                        </p>
                        
                        <div className="flex items-end justify-between mt-auto pt-sm border-t border-border-subtle/60 gap-sm">
                          <div className="flex items-center gap-xs min-w-0 flex-1">
                            <div className="w-7 h-7 rounded-full bg-primary/20 border-2 border-surface-container-highest flex items-center justify-center text-[10px] font-bold text-primary shrink-0" title={card.assignee}>
                              {card.assignee ? card.assignee.substring(0, 2).toUpperCase() : 'NN'}
                            </div>
                            <span className="text-[11px] text-on-surface-variant truncate">{card.assignee || 'Sem responsável'}</span>
                          </div>

                          <div className="flex flex-col items-end gap-xs shrink-0">
                            <button
                              onClick={(e) => { e.stopPropagation(); handleToggleTimer(card.id); }}
                              className={`flex items-center gap-xs px-sm py-1 rounded-full text-[10px] font-bold whitespace-nowrap ${activeTimerCardId === card.id ? 'bg-error/10 text-error' : 'bg-primary/10 text-primary'}`}
                            >
                              <span className="material-symbols-outlined text-xs" style={{ fontVariationSettings: "'FILL' 1" }}>
                                {activeTimerCardId === card.id ? 'stop' : 'play_arrow'}
                              </span>
                              {activeTimerCardId === card.id ? 'Parar' : 'Iniciar'}
                            </button>
                            <span className="text-[12px] font-bold text-on-surface flex items-center gap-xs">
                              <span className="material-symbols-outlined text-sm text-primary">attach_money</span> {Number(card.cost_per_task || 0).toFixed(2)}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  
                  <button 
                    onClick={() => handleAddNewCard(column.id)}
                    className="w-full py-3 border-2 border-dashed border-outline/30 hover:border-outline rounded-xl text-outline hover:text-on-surface-variant flex items-center justify-center space-x-2 transition-colors mt-2"
                  >
                    <span className="material-symbols-outlined text-[18px]">add</span>
                    <span className="font-label-md">Adicionar Tarefa</span>
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Modal Nova Tarefa */}
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
                <h3 className="font-display-sm text-display-sm text-on-surface">Nova Tarefa</h3>
                <button onClick={() => setIsModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSaveCard} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Título</label>
                  <input required type="text" value={formData.title} onChange={(e) => setFormData({...formData, title: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Descrição</label>
                  <textarea required rows={3} value={formData.description} onChange={(e) => setFormData({...formData, description: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Prioridade</label>
                  <select value={formData.priority} onChange={(e) => setFormData({...formData, priority: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none">
                    <option value="BAIXA">Baixa</option>
                    <option value="MEDIA">Média</option>
                    <option value="ALTA">Alta</option>
                    <option value="URGENTE">Urgente</option>
                  </select>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
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

      {/* Modal Novo Projeto */}
      <AnimatePresence>
        {isProjectModalOpen && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsProjectModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[500px]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">Novo Projeto</h3>
                <button onClick={() => setIsProjectModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSaveProject} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Nome do Projeto</label>
                  <input required type="text" value={projectForm.name} onChange={(e) => setProjectForm({...projectForm, name: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Descrição</label>
                  <textarea required rows={3} value={projectForm.description} onChange={(e) => setProjectForm({...projectForm, description: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Cliente</label>
                  <select
                    required
                    value={projectForm.client_id}
                    onChange={(e) => {
                      if (e.target.value === '__new__') {
                        setIsClientModalOpen(true);
                      } else {
                        setProjectForm({...projectForm, client_id: e.target.value});
                      }
                    }}
                    className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  >
                    <option value="" disabled>Selecione um cliente</option>
                    {clients.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                    <option value="__new__">+ Novo Cliente</option>
                  </select>
                </div>
                <div className="flex gap-md">
                  <div className="flex-1">
                    <label className="block text-label-md text-on-surface-variant mb-1">Data Início</label>
                    <input required type="date" value={projectForm.start_date} onChange={(e) => setProjectForm({...projectForm, start_date: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                  </div>
                  <div className="flex-1">
                    <label className="block text-label-md text-on-surface-variant mb-1">Data Fim</label>
                    <input required type="date" value={projectForm.end_date} onChange={(e) => setProjectForm({...projectForm, end_date: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                  </div>
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsProjectModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
                    Cancelar
                  </button>
                  <button type="submit" className="px-6 py-2 rounded-lg font-label-md bg-primary text-on-primary hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20">
                    Criar Projeto
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Modal Novo Cliente */}
      <AnimatePresence>
        {isClientModalOpen && (
          <div className="fixed inset-0 z-[110] flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsClientModalOpen(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative bg-surface-container-high border border-border-subtle p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[500px]"
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-display-sm text-display-sm text-on-surface">Novo Cliente</h3>
                <button onClick={() => setIsClientModalOpen(false)} className="text-on-surface-variant hover:text-on-surface">
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              <form onSubmit={handleSaveClient} className="space-y-md">
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Nome</label>
                  <input required type="text" value={clientForm.name} onChange={(e) => setClientForm({...clientForm, name: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Email</label>
                  <input required type="email" value={clientForm.email} onChange={(e) => setClientForm({...clientForm, email: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div className="flex gap-md">
                  <div className="flex-1">
                    <label className="block text-label-md text-on-surface-variant mb-1">Telefone</label>
                    <input required type="text" value={clientForm.phone} onChange={(e) => setClientForm({...clientForm, phone: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                  </div>
                  <div className="flex-1">
                    <label className="block text-label-md text-on-surface-variant mb-1">CNPJ</label>
                    <input required type="text" value={clientForm.cnpj} onChange={(e) => setClientForm({...clientForm, cnpj: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                  </div>
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Nome do Contato</label>
                  <input required type="text" value={clientForm.contact_name} onChange={(e) => setClientForm({...clientForm, contact_name: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>
                <div>
                  <label className="block text-label-md text-on-surface-variant mb-1">Segmento</label>
                  <input required type="text" value={clientForm.segment} onChange={(e) => setClientForm({...clientForm, segment: e.target.value})} className="w-full bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface focus:border-primary focus:ring-1 focus:ring-primary outline-none" />
                </div>

                <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-border-subtle">
                  <button type="button" onClick={() => setIsClientModalOpen(false)} className="px-6 py-2 rounded-lg font-label-md text-on-surface hover:bg-surface-container-highest transition-colors">
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

      {/* Painel de Detalhe do Card */}
      <AnimatePresence>
        {detailCard && (
          <div className="fixed inset-0 z-[100] flex justify-end">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setDetailCard(null)}
            />

            {/* Drawer Sidebar */}
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="relative w-full max-w-[28rem] bg-surface-container-high border-l border-border-subtle shadow-2xl flex flex-col h-full z-10"
            >
              {/* Header */}
              <div className="p-md border-b border-border-subtle flex items-center justify-between bg-surface-container-highest/40">
                <div>
                  <h3 className="font-headline-sm text-headline-sm text-on-surface">{detailCard.title}</h3>
                  <p className="text-[11px] text-on-surface-variant uppercase tracking-wider mt-1">{detailCard.priority}</p>
                </div>
                <button
                  onClick={() => setDetailCard(null)}
                  className="p-2 text-on-surface-variant hover:text-on-surface rounded-lg hover:bg-surface-container-highest transition-colors"
                >
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              {/* Body */}
              <div className="flex-1 overflow-y-auto p-md space-y-lg">
                <div>
                  <h4 className="text-label-md text-on-surface-variant mb-1">Descrição</h4>
                  <p className="font-body-sm text-body-sm text-on-surface whitespace-pre-wrap">{detailCard.description || 'Sem descrição.'}</p>
                </div>

                <div className="flex gap-lg">
                  <div>
                    <h4 className="text-label-md text-on-surface-variant mb-1">Responsável</h4>
                    <p className="font-body-sm text-body-sm text-on-surface">{detailCard.assignee || 'Não atribuído'}</p>
                  </div>
                  <div>
                    <h4 className="text-label-md text-on-surface-variant mb-1">Prioridade</h4>
                    <p className="font-body-sm text-body-sm text-on-surface">{detailCard.priority}</p>
                  </div>
                </div>

                <div>
                  <h4 className="text-label-md text-on-surface-variant mb-sm">Comentários</h4>
                  <div className="space-y-sm">
                    {(detailCard.comments || []).length === 0 && (
                      <p className="text-body-sm text-outline">Nenhum comentário ainda.</p>
                    )}
                    {(detailCard.comments || []).map((c: any) => (
                      <div key={c.id} className="bg-surface-container rounded-lg p-sm border border-border-subtle">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[11px] font-bold text-on-surface">{c.author}</span>
                          <span className="text-[10px] text-outline">{c.created_at ? new Date(c.created_at).toLocaleString() : ''}</span>
                        </div>
                        <p className="text-body-sm text-on-surface-variant whitespace-pre-wrap">{c.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Comment Input */}
              <div className="p-md border-t border-border-subtle bg-surface-container-highest/40">
                <form
                  onSubmit={(e) => { e.preventDefault(); handleAddComment(); }}
                  className="flex items-center gap-sm"
                >
                  <input
                    type="text"
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    placeholder="Adicionar comentário..."
                    className="flex-1 bg-surface-container border border-border-subtle rounded-lg px-4 py-2 text-on-surface placeholder:text-outline focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                  />
                  <button
                    type="submit"
                    disabled={!commentText.trim()}
                    className="p-2.5 rounded-lg bg-primary text-on-primary disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/90 transition-all"
                  >
                    <span className="material-symbols-outlined text-xl">send</span>
                  </button>
                </form>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </Layout>
  );
}
