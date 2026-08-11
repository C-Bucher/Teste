import { useState, useEffect } from 'react';
import api from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import Layout from '../components/Layout';

export default function Kanban() {
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [boardData, setBoardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

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

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const res = await api.get('/kanban/projects');
        setProjects(res.data);
        if (res.data.length > 0) {
          setSelectedProjectId(res.data[0].id);
        } else {
          setLoading(false);
        }
      } catch (err) {
        console.error("Erro ao carregar projetos", err);
        setLoading(false);
      }
    };
    fetchProjects();
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
    } catch (err) {
      console.error("Erro ao criar tarefa", err);
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
            <button className="flex items-center gap-sm bg-gradient-to-r from-primary to-secondary text-on-primary px-lg py-sm rounded-lg hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/10">
              <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>add</span> Novo Projeto
            </button>
          </div>
        </div>

        {/* Kanban Board */}
        <div className="flex gap-lg flex-1 min-w-[1200px] overflow-x-auto overflow-y-hidden pb-4">
          {boardData?.columns?.map((column: any, i: number) => {
            // Determine colors dynamically based on order/name
            let colorClass = 'bg-outline';
            let bgClass = 'bg-white/5 border-border-subtle';
            if (column.name.toLowerCase().includes('andamento') || column.name.toLowerCase().includes('desenvolvimento')) {
              colorClass = 'bg-primary';
              bgClass = 'bg-primary-container/5 border-primary/10';
            } else if (column.name.toLowerCase().includes('revisao')) {
              colorClass = 'bg-warning';
            } else if (column.name.toLowerCase().includes('concluido')) {
              colorClass = 'bg-success';
              bgClass = 'bg-success/5 border-success/10';
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
                <div className="flex items-center justify-between px-md mb-md">
                  <div className="flex items-center gap-sm">
                    <span className={`w-2 h-2 rounded-full ${colorClass}`}></span>
                    <span className="font-headline-sm text-headline-sm uppercase tracking-wider text-on-surface-variant truncate max-w-[200px]">
                      {column.name}
                    </span>
                    <span className="bg-surface-container-highest px-sm py-xs rounded text-xs text-outline">
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
                                     card.priority === 'BAIXA' ? 'bg-surface-container-highest text-outline' :
                                     'bg-primary-container/20 text-primary';

                    return (
                      <div
                        key={card.id}
                        draggable
                        onDragStart={(e) => handleDragStart(e, card.id)}
                        onDragEnd={handleDragEnd}
                        className={`group ${isDone ? 'bg-surface/60 opacity-80' : 'bg-surface'} rounded-xl border ${isActive ? 'border-l-4 border-l-primary border-border-subtle' : 'border-border-subtle'} p-md shadow-sm hover:shadow-lg transition-all duration-300 cursor-grab active:cursor-grabbing hover:border-primary/30`}
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
                        
                        <div className="flex items-center justify-between mt-auto">
                          <div className="flex -space-x-2">
                            <div className="w-7 h-7 rounded-full bg-primary/20 border-2 border-surface flex items-center justify-center text-[10px] font-bold text-primary" title={card.assignee}>
                              {card.assignee ? card.assignee.substring(0, 2).toUpperCase() : 'NN'}
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-sm">
                            <span className="text-[11px] text-outline flex items-center gap-xs">
                              <span className="material-symbols-outlined text-sm">attach_money</span> {card.cost_per_task}
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
    </Layout>
  );
}
