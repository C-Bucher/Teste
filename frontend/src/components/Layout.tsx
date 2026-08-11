import { useState, type ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import AICfoDrawer from './AICfoDrawer';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [isAiDrawerOpen, setIsAiDrawerOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/');
  };

  const getRoleLabel = (role: string) => {
    if (role === 'ADMIN') return 'Administrador';
    if (role === 'GERENTE') return 'Gerente';
    if (role === 'FUNCIONARIO') return 'Funcionário';
    return role || 'Colaborador';
  };

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: 'dashboard' },
    { name: 'Projetos', path: '/kanban', icon: 'view_kanban' },
    ...(user.role !== 'FUNCIONARIO' ? [{ name: 'Equipe', path: '/equipe', icon: 'groups' }] : []),
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

        <button
          onClick={() => setIsAiDrawerOpen(true)}
          className="p-2 bg-gradient-to-tr from-primary to-secondary rounded-full text-on-primary shadow-md"
        >
          <span className="material-symbols-outlined text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>
            chat_bubble
          </span>
        </button>
      </div>

      {/* SideNavBar (Desktop & Mobile Drawer) */}
      <aside
        className={`fixed left-0 top-0 h-full w-64 bg-glass-bg backdrop-blur-xl border-r border-border-subtle shadow-md flex flex-col py-lg px-md z-50 transition-transform duration-300 ${
          isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="mb-xl px-sm flex justify-between items-center">
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

        <nav className="flex-1 space-y-xs">
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

        <div className="mt-auto space-y-xs pt-lg border-t border-border-subtle">
          <button
            onClick={() => setIsAiDrawerOpen(true)}
            className="w-full flex items-center gap-md p-md rounded-lg text-primary hover:bg-primary-container/20 transition-colors"
          >
            <span className="material-symbols-outlined">psychology</span>
            <span className="font-label-md font-bold">CFO Virtual IA</span>
          </button>

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
        <div className="flex items-center bg-surface-container-low rounded-full px-md py-xs w-96 border border-border-subtle">
          <span className="material-symbols-outlined text-outline">search</span>
          <input
            className="bg-transparent border-none focus:ring-0 text-body-sm w-full text-on-surface focus:outline-none"
            placeholder="Pesquisar métricas ou faturas..."
            type="text"
          />
        </div>

        <div className="flex items-center gap-md">
          <button
            onClick={() => setIsAiDrawerOpen(true)}
            className="flex items-center gap-2 bg-gradient-to-r from-primary to-secondary text-on-primary px-3.5 py-1.5 rounded-full text-xs font-bold shadow-md hover:opacity-90 transition-all"
          >
            <span className="material-symbols-outlined text-sm">auto_awesome</span>
            CFO Virtual IA
          </button>
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
      <main className="lg:ml-64 mt-16 p-md lg:p-lg min-h-[calc(100vh-4rem)] overflow-y-auto custom-scrollbar">
        {children}
      </main>

      {/* Floating Action Button: Talk to AI */}
      <div className="fixed bottom-lg right-lg z-40">
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
      </div>

      {/* AI CFO Drawer Component */}
      <AICfoDrawer isOpen={isAiDrawerOpen} onClose={() => setIsAiDrawerOpen(false)} />
    </div>
  );
}
