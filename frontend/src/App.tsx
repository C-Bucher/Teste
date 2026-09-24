import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Plans from './pages/Plans';
import Checkout from './pages/Checkout';
import Subscription from './pages/Subscription';
import Dashboard from './pages/Dashboard';
import Kanban from './pages/Kanban';
import GestaoEquipe from './pages/GestaoEquipe';
import Configuracoes from './pages/Configuracoes';
import Fornecedores from './pages/Fornecedores';
import Financeiro from './pages/Financeiro';
import HubPessoal from './pages/HubPessoal';
import Exportacao from './pages/Exportacao';
import IAEmpresarial from './pages/IAEmpresarial';
import Onboarding from './pages/Onboarding';
import { usePermissions } from './hooks/usePermissions';

const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token');
  const location = useLocation();
  if (!token) return <Navigate to="/" />;

  let user: { role?: string } = {};
  let company: { onboarding_completed?: boolean } = {};
  try {
    user = JSON.parse(localStorage.getItem('user') || '{}');
    company = JSON.parse(localStorage.getItem('company') || '{}');
  } catch {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('company');
    return <Navigate to="/" replace />;
  }
  if (user.role === 'ADMIN' && company.onboarding_completed === false && location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" />;
  }

  return children;
};

const ModuleRoute = ({ module, children }: { module: string; children: React.ReactNode }) => {
  const { loading, can } = usePermissions();
  if (loading) return <div className="min-h-screen bg-background" />;
  return can(module) ? children : <Navigate to="/dashboard" replace />;
};

const ScopeRoute = ({ scope, children }: { scope: 'pessoal' | 'empresarial'; children: React.ReactNode }) => {
  let user: { plan_scope?: string } = {};
  try { user = JSON.parse(localStorage.getItem('user') || '{}'); } catch { /* sessão inválida */ }
  const allowed = user.plan_scope === 'completo' || user.plan_scope === scope;
  return allowed ? children : <Navigate to={scope === 'pessoal' ? '/dashboard' : '/pessoal/visao-geral'} replace />;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/cadastro" element={<Register />} />
        <Route path="/planos" element={<Plans />} />
        <Route path="/checkout" element={<Checkout />} />
        <Route path="/dashboard" element={<PrivateRoute><ScopeRoute scope="empresarial"><ModuleRoute module="dashboard"><Dashboard /></ModuleRoute></ScopeRoute></PrivateRoute>} />
        <Route path="/onboarding" element={<PrivateRoute><Onboarding /></PrivateRoute>} />
        <Route path="/kanban" element={<PrivateRoute><ScopeRoute scope="empresarial"><ModuleRoute module="kanban"><Kanban /></ModuleRoute></ScopeRoute></PrivateRoute>} />
        <Route path="/equipe" element={<PrivateRoute><GestaoEquipe /></PrivateRoute>} />
        <Route path="/configuracoes" element={<PrivateRoute><Configuracoes /></PrivateRoute>} />
        <Route path="/fornecedores" element={<PrivateRoute><Fornecedores /></PrivateRoute>} />
        <Route path="/financeiro" element={<PrivateRoute><Financeiro /></PrivateRoute>} />
        <Route path="/exportacao" element={<PrivateRoute><Exportacao /></PrivateRoute>} />
        <Route path="/ia" element={<PrivateRoute><IAEmpresarial /></PrivateRoute>} />
        <Route path="/pessoal" element={<Navigate to="/pessoal/visao-geral" />} />
        <Route path="/pessoal/:tab" element={<PrivateRoute><ScopeRoute scope="pessoal"><HubPessoal /></ScopeRoute></PrivateRoute>} />
        <Route path="/assinatura" element={<PrivateRoute><Subscription /></PrivateRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
