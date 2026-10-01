import { useState, useEffect, useRef, type ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import AICfoDrawer from './AICfoDrawer';
import api, { clearSession } from '../api';
import { useToast } from '../context/ToastContext';
import { usePermissions, clearPermissionsCache } from '../hooks/usePermissions';

interface SearchResult {
  type: string;
  id: string;
  title: string;
  subtitle: string;
  url: string;
}

const SEARCH_TYPE_ICONS: Record<string, string> = {
  employee: 'badge',
  client: 'handshake',
  project: 'view_kanban',
  financial: 'payments',
  supplier: 'local_shipping',
};

interface LayoutProps {
  children: ReactNode;
}

const NOTIF_TYPE_STYLES: Record<string, string> = {
  WARNING: 'bg-warning/10 text-warning',
  SUCCESS: 'bg-success/10 text-success',
  INFO: 'bg-primary/10 text-primary',
};

const BUSINESS_PATHS = ['/dashboard', '/kanban', '/equipe', '/financeiro', '/fornecedores', '/configuracoes', '/exportacao', '/ia'];

export default function Layout({ children }: LayoutProps) {
  const [isAiDrawerOpen, setIsAiDrawerOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isNotifPanelOpen, setIsNotifPanelOpen] = useState(false);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const location = useLocation();
  const navigate = useNavigate();
  const toast = useToast();
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const [workspaceMode, setWorkspaceMode] = useState<'empresarial' | 'pessoal'>(() => {
    if (location.pathname.startsWith('/pessoal')) return 'pessoal';
    if (BUSINESS_PATHS.includes(location.pathname)) return 'empresarial';
    return (localStorage.getItem('workspace_mode') as 'empresarial' | 'pessoal') || 'empresarial';
  });

  const handleToggleWorkspace = () => {
    const next = workspaceMode === 'empresarial' ? 'pessoal' : 'empresarial';
    setWorkspaceMode(next);
    localStorage.setItem('workspace_mode', next);
    navigate(next === 'pessoal' ? '/pessoal/visao-geral' : '/dashboard');
  };

  useEffect(() => {
    const fetchUnreadCount = async () => {
      try {
        const res = await api.get('/notifications/unread-count');
        setUnreadCount(res.data.count);
      } catch (err) {
        console.error('Erro ao carregar contagem de notificações', err);
      }
    };
    fetchUnreadCount();
  }, []);

  const { modules: allowedModules } = usePermissions();

  const openNotifPanel = async () => {
    setIsNotifPanelOpen(true);
    try {
      const res = await api.get('/notifications/');
      setNotifications(res.data.items);
      setUnreadCount(res.data.unread_count);
    } catch (err) {
      console.error('Erro ao carregar notificações', err);
    }
  };

  const handleMarkRead = async (id: string) => {
    try {
      await api.post(`/notifications/${id}/read`);
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Erro ao marcar notificação como lida', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.post('/notifications/read-all');
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Erro ao marcar todas as notificações como lidas', err);
    }
  };

  const handleLogout = () => {
    clearSession();
    clearPermissionsCache();
    navigate('/');
  };

  const runSearch = async (term: string) => {
    const q = term.trim();
    if (q.length < 2) {
      setSearchResults([]);
      setIsSearchOpen(false);
      return;
    }
    setIsSearching(true);
    setIsSearchOpen(true);
    try {
      const res = await api.get('/search/', { params: { q, limit: 8 } });
      setSearchResults(res.data.results || []);
    } catch (err) {
      console.error('Erro na busca global', err);
      setSearchResults([]);
      toast.error('Não foi possível concluir a busca. Tente novamente.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    searchDebounceRef.current = setTimeout(() => runSearch(value), 300);
  };

  const handleSelectResult = (url: string) => {
    setIsSearchOpen(false);
    setSearchQuery('');
    setSearchResults([]);
    navigate(url);
  };

  const getRoleLabel = (role: string) => {
    if (role === 'ADMIN') return 'Administrador';
    if (role === 'GERENTE') return 'Gerente';
    if (role === 'FUNCIONARIO') return 'Funcionário';
    return role || 'Colaborador';
  };

  const scope = user.plan_scope || 'completo';
  const showBusiness = scope === 'empresarial' || scope === 'completo';
  const showPersonal = scope === 'pessoal' || scope === 'completo';

  const bothScopesAvailable = showBusiness && showPersonal;
  const effectiveMode: 'empresarial' | 'pessoal' = bothScopesAvailable ? workspaceMode : (showPersonal ? 'pessoal' : 'empresarial');

  const ALL_BUSINESS_ITEMS = [
    { name: 'Dashboard', path: '/dashboard', icon: 'dashboard', module: 'dashboard' },
    { name: 'Projetos', path: '/kanban', icon: 'view_kanban', module: 'kanban' },
    { name: 'Equipe', path: '/equipe', icon: 'groups', module: 'equipe' },
    { name: 'Financeiro', path: '/financeiro', icon: 'payments', module: 'financeiro' },
    { name: 'Bancos', path: '/bancos', icon: 'account_balance_wallet', module: 'financeiro' },
    { name: 'Fornecedores', path: '/fornecedores', icon: 'local_shipping', module: 'fornecedores' },
    { name: 'Configurações', path: '/configuracoes', icon: 'settings', module: 'configuracoes' },
    { name: 'Exportação', path: '/exportacao', icon: 'file_download', module: 'exportacao' },
    { name: 'IA Empresarial', path: '/ia', icon: 'auto_awesome', module: 'ia' },
  ];

  const businessNavItems = ALL_BUSINESS_ITEMS.filter((item) => allowedModules.includes(item.module));
  // The CFO drawer calls the business AI endpoints, which require the 'ia' module (403 otherwise).
  const canUseAi = showBusiness && allowedModules.includes('ia');

  const personalNavItems = [
    { name: 'Visão Geral', path: '/pessoal/visao-geral', icon: 'dashboard' },
    { name: 'Extrato', path: '/pessoal/extrato', icon: 'receipt_long' },
    { name: 'Bancos', path: '/pessoal/bancos', icon: 'account_balance_wallet' },
    { name: 'Contas & Cartões', path: '/pessoal/contas-cartoes', icon: 'credit_card' },
    { name: 'Orçamento', path: '/pessoal/orcamento', icon: 'pie_chart' },
    { name: 'Metas', path: '/pessoal/metas', icon: 'flag' },
    { name: 'Dívidas', path: '/pessoal/dividas', icon: 'account_balance' },
    { name: 'Assinaturas', path: '/pessoal/assinaturas', icon: 'subscriptions' },
    { name: 'Divisão de Despesas', path: '/pessoal/divisao', icon: 'groups' },
    { name: 'Analítico', path: '/pessoal/analitico', icon: 'analytics' },
    { name: 'Timeboxes & OKRs', path: '/pessoal/timeboxes-okrs', icon: 'schedule' },
    { name: 'CFO Pessoal IA', path: '/pessoal/cfo-pessoal', icon: 'auto_awesome' },
  ];

  const navItems = [
    ...(showBusiness && effectiveMode === 'empresarial' ? businessNavItems : []),
    ...(showPersonal && effectiveMode === 'pessoal' ? personalNavItems : []),
    { name: 'Assinatura', path: '/assinatura', icon: 'credit_card' },
    { name: 'Planos & Preços', path: '/planos', icon: 'workspace_premium' },
  ];

  return (
    <div className="bg-background text-on-background font-body-base min-h-screen">
      {/* Mobile Header / Hamburger Toggle */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-glass-bg backdrop-blur-xl border-b border-border-subtle z-50 flex items-center justify-between px-md">
        <div className="flex items-center gap-sm">
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 text-on-surface hover:bg-surface-bright rounded-lg"
          >
            <span className="material-symbols-outlined">menu</span>
          </button>
          <h1 className="font-headline-sm font-bold text-primary">TechConnect</h1>
        </div>

        <div className="flex items-center gap-sm">
          {bothScopesAvailable && (
            <button
              onClick={handleToggleWorkspace}
              className="p-2 rounded-full bg-surface-container-high border border-border-subtle text-on-surface-variant hover:text-on-surface transition-all"
              title={workspaceMode === 'empresarial' ? 'Mudar para o Hub Pessoal' : 'Mudar para o Empresarial'}
            >
              <span className="material-symbols-outlined text-[20px]">
                {workspaceMode === 'empresarial' ? 'person' : 'business_center'}
              </span>
            </button>
          )}
          <button
            onClick={openNotifPanel}
            className="relative p-2 rounded-full hover:bg-surface-bright transition-colors text-on-surface-variant hover:text-on-surface"
          >
            <span className="material-symbols-outlined text-[20px]">notifications</span>
            {unreadCount > 0 && (
              <span className="absolute top-0 right-0 w-4 h-4 bg-error text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>
          {canUseAi && (
            <button
              onClick={() => setIsAiDrawerOpen(true)}
              className="p-2 bg-gradient-to-tr from-primary to-secondary rounded-full text-on-primary shadow-md"
            >
              <span className="material-symbols-outlined text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                chat_bubble
              </span>
            </button>
          )}
        </div>
      </div>

      {/* SideNavBar (Desktop & Mobile Drawer) */}
      <aside
        className={`fixed left-0 top-0 h-full w-64 bg-glass-bg backdrop-blur-xl border-r border-border-subtle shadow-md flex flex-col py-lg px-md z-50 transition-transform duration-300 ${
          isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="mb-xl px-sm flex justify-between items-center shrink-0">
          <div>
            <h1 className="font-headline-md text-headline-md font-bold text-primary">TechConnect</h1>
            <p className="font-label-md text-label-md text-on-surface-variant opacity-70">CFO Virtual IA</p>
          </div>
          <button
            onClick={() => setIsMobileMenuOpen(false)}
            className="lg:hidden p-1 text-on-surface-variant hover:text-on-surface"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <nav className="flex-1 min-h-0 overflow-y-auto custom-scrollbar nav-fade pr-1 space-y-xs">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsMobileMenuOpen(false)}
                className={`flex items-center gap-md p-md rounded-lg font-bold transition-colors group ${
                  isActive
                    ? 'text-primary border-r-2 border-primary bg-surface-variant/50'
                    : 'text-on-surface-variant hover:bg-surface-variant/50'
                }`}
              >
                <span className={`material-symbols-outlined ${!isActive && 'group-hover:text-primary'}`}>
                  {item.icon}
                </span>
                <span className="font-label-md">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto space-y-xs pt-lg border-t border-border-subtle shrink-0">
          {canUseAi && (
            <button
              onClick={() => setIsAiDrawerOpen(true)}
              className="w-full flex items-center gap-md p-md rounded-lg text-primary hover:bg-primary-container/20 transition-colors"
            >
              <span className="material-symbols-outlined">psychology</span>
              <span className="font-label-md font-bold">CFO Virtual IA</span>
            </button>
          )}

          <Link
            to="/minha-conta"
            className={`w-full flex items-center gap-md p-md rounded-lg transition-colors ${location.pathname === '/minha-conta' ? 'bg-primary-container/20 text-primary' : 'text-on-surface-variant hover:bg-surface-container-high'}`}
          >
            <span className="material-symbols-outlined">account_circle</span>
            <span className="font-label-md">Minha Conta</span>
          </Link>

          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-md p-md rounded-lg text-error hover:bg-error/10 transition-colors"
          >
            <span className="material-symbols-outlined">logout</span>
            <span className="font-label-md">Sair</span>
          </button>
        </div>
      </aside>

      {/* TopNavBar (Desktop) */}
      <header className="hidden lg:flex fixed top-0 right-0 w-[calc(100%-16rem)] h-16 bg-glass-bg backdrop-blur-xl z-40 border-b border-border-subtle justify-between items-center px-lg">
        <div className="relative w-96">
          <div className="flex items-center bg-surface-container-low rounded-full px-md py-xs border border-border-subtle focus-within:border-primary/40 transition-colors">
            <span className="material-symbols-outlined text-outline">search</span>
            <input
              className="bg-transparent border-none focus:ring-0 text-body-sm w-full text-on-surface focus:outline-none ml-2"
              placeholder="Buscar projetos, pessoas, lançamentos..."
              type="text"
              value={searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              onFocus={() => searchResults.length > 0 && setIsSearchOpen(true)}
            />
            {searchQuery && (
              <button
                onClick={() => { setSearchQuery(''); setSearchResults([]); setIsSearchOpen(false); }}
                className="text-on-surface-variant hover:text-on-surface"
              >
                <span className="material-symbols-outlined text-[18px]">close</span>
              </button>
            )}
          </div>

          <AnimatePresence>
            {isSearchOpen && (
              <>
                <div className="fixed inset-0 z-[59]" onClick={() => setIsSearchOpen(false)} />
                <motion.div
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.15 }}
                  className="absolute top-full mt-2 left-0 w-full max-h-[60vh] overflow-y-auto custom-scrollbar bg-glass-bg backdrop-blur-xl border border-border-subtle rounded-xl shadow-2xl z-[60]"
                >
                  {isSearching ? (
                    <div className="p-lg flex justify-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary" />
                    </div>
                  ) : searchResults.length === 0 ? (
                    <p className="p-lg text-center font-label-md text-on-surface-variant text-body-sm">
                      Nenhum resultado para "{searchQuery}"
                    </p>
                  ) : (
                    <div className="divide-y divide-border-subtle">
                      {searchResults.map((r) => (
                        <button
                          key={`${r.type}-${r.id}`}
                          onClick={() => handleSelectResult(r.url)}
                          className="w-full flex items-center gap-md p-md text-left hover:bg-surface-variant/40 transition-colors"
                        >
                          <span className="material-symbols-outlined text-[20px] text-primary shrink-0">
                            {SEARCH_TYPE_ICONS[r.type] || 'search'}
                          </span>
                          <div className="flex-1 min-w-0">
                            <p className="text-body-sm text-on-surface font-medium truncate">{r.title}</p>
                            <p className="text-[12px] text-on-surface-variant truncate">{r.subtitle}</p>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </motion.div>
              </>
            )}
          </AnimatePresence>
        </div>

        <div className="flex items-center gap-md">
          {bothScopesAvailable && (
            <button
              onClick={handleToggleWorkspace}
              className="flex items-center gap-2 bg-surface-container-high border border-border-subtle px-3.5 py-1.5 rounded-full text-xs font-bold text-on-surface-variant hover:text-on-surface hover:border-primary/30 transition-all"
              title={workspaceMode === 'empresarial' ? 'Mudar para o Hub Pessoal' : 'Mudar para o Empresarial'}
            >
              <span className="material-symbols-outlined text-sm">
                {workspaceMode === 'empresarial' ? 'person' : 'business_center'}
              </span>
              {workspaceMode === 'empresarial' ? 'Ir para Pessoal' : 'Ir para Empresarial'}
            </button>
          )}
          <button
            onClick={openNotifPanel}
            className="relative p-2 rounded-full hover:bg-surface-bright transition-colors text-on-surface-variant hover:text-on-surface"
          >
            <span className="material-symbols-outlined">notifications</span>
            {unreadCount > 0 && (
              <span className="absolute top-0 right-0 w-4 h-4 bg-error text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>
          {canUseAi && (
            <button
              onClick={() => setIsAiDrawerOpen(true)}
              className="flex items-center gap-2 bg-gradient-to-r from-primary to-secondary text-on-primary px-3.5 py-1.5 rounded-full text-xs font-bold shadow-md hover:opacity-90 transition-all"
            >
              <span className="material-symbols-outlined text-sm">auto_awesome</span>
              CFO Virtual IA
            </button>
          )}
          <div className="h-8 w-px bg-border-subtle"></div>
          <div className="flex items-center gap-sm cursor-pointer" onClick={() => navigate('/assinatura')}>
            <div className="text-right hidden sm:block">
              <p className="font-label-md text-label-md text-on-surface">{user?.full_name || 'Usuário TechConnect'}</p>
              <p className="text-[10px] text-primary uppercase tracking-wider font-bold">{getRoleLabel(user?.role)}</p>
            </div>
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-primary to-secondary text-on-primary font-bold flex items-center justify-center text-sm shadow-md">
              {(user?.full_name || 'TC').substring(0, 2).toUpperCase()}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Container */}
      <main className="lg:ml-64 mt-16 p-md lg:p-lg pb-28 lg:pb-28 min-h-[calc(100vh-4rem)] overflow-y-auto custom-scrollbar">
        {children}
      </main>

      {/* Floating Action Button: Talk to AI */}
      <div className="fixed bottom-lg right-lg z-40">
        {canUseAi && (
          <button
            onClick={() => setIsAiDrawerOpen(true)}
            className="w-14 h-14 rounded-full bg-gradient-to-tr from-primary to-secondary flex items-center justify-center shadow-xl shadow-primary/30 hover:scale-110 active:scale-95 transition-all group"
          >
            <span className="material-symbols-outlined text-on-primary text-[28px]" style={{ fontVariationSettings: "'FILL' 1" }}>
              chat_bubble
            </span>
            <div className="absolute right-16 bg-glass-bg border border-border-subtle p-md rounded-xl opacity-0 translate-x-4 group-hover:opacity-100 group-hover:translate-x-0 transition-all pointer-events-none whitespace-nowrap">
              <p className="font-label-md text-primary">Falar com CFO Virtual</p>
            </div>
          </button>
        )}
      </div>

      {/* AI CFO Drawer Component */}
      <AICfoDrawer isOpen={isAiDrawerOpen} onClose={() => setIsAiDrawerOpen(false)} />

      {/* Notifications Dropdown Panel */}
      <AnimatePresence>
        {isNotifPanelOpen && (
          <>
            {/* Click-outside catcher (transparent — this is a popover, not a modal) */}
            <div className="fixed inset-0 z-[89]" onClick={() => setIsNotifPanelOpen(false)} />

            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -8 }}
              transition={{ duration: 0.15 }}
              className="fixed top-16 right-md lg:right-lg w-[calc(100vw-2rem)] sm:w-96 max-h-[70vh] overflow-y-auto bg-glass-bg backdrop-blur-xl border border-border-subtle rounded-xl shadow-2xl z-[90]"
            >
              <div className="flex items-center justify-between p-md border-b border-border-subtle sticky top-0 bg-glass-bg backdrop-blur-xl">
                <h3 className="font-label-md font-bold text-on-surface">Notificações</h3>
                <div className="flex items-center gap-md">
                  {unreadCount > 0 && (
                    <button
                      onClick={handleMarkAllRead}
                      className="text-[11px] font-bold text-primary hover:underline whitespace-nowrap"
                    >
                      Marcar todas como lidas
                    </button>
                  )}
                  <button
                    onClick={() => setIsNotifPanelOpen(false)}
                    className="p-1 text-on-surface-variant hover:text-on-surface"
                  >
                    <span className="material-symbols-outlined text-[18px]">close</span>
                  </button>
                </div>
              </div>

              <div className="divide-y divide-border-subtle">
                {notifications.length === 0 ? (
                  <p className="p-lg text-center font-label-md text-on-surface-variant">
                    Nenhuma notificação
                  </p>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      onClick={() => !n.is_read && handleMarkRead(n.id)}
                      className={`p-md flex items-start gap-sm transition-colors ${
                        !n.is_read ? 'bg-surface-variant/20 cursor-pointer hover:bg-surface-variant/30' : ''
                      }`}
                    >
                      <span
                        className={`w-2 h-2 mt-1.5 rounded-full flex-shrink-0 ${
                          !n.is_read ? 'bg-primary' : 'bg-transparent'
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-sm mb-1">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[9px] font-bold uppercase ${
                              NOTIF_TYPE_STYLES[n.type] || NOTIF_TYPE_STYLES.INFO
                            }`}
                          >
                            {n.type}
                          </span>
                          <p className="font-label-md text-on-surface text-[13px] font-bold truncate">
                            {n.title}
                          </p>
                        </div>
                        <p className="text-[12px] text-on-surface-variant">{n.message}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
