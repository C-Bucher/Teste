import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
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

const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/" />;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/cadastro" element={<Register />} />
        <Route path="/planos" element={<Plans />} />
        <Route path="/checkout" element={<Checkout />} />
        <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        <Route path="/kanban" element={<PrivateRoute><Kanban /></PrivateRoute>} />
        <Route path="/equipe" element={<PrivateRoute><GestaoEquipe /></PrivateRoute>} />
        <Route path="/configuracoes" element={<PrivateRoute><Configuracoes /></PrivateRoute>} />
        <Route path="/fornecedores" element={<PrivateRoute><Fornecedores /></PrivateRoute>} />
        <Route path="/financeiro" element={<PrivateRoute><Financeiro /></PrivateRoute>} />
        <Route path="/exportacao" element={<PrivateRoute><Exportacao /></PrivateRoute>} />
        <Route path="/pessoal" element={<PrivateRoute><HubPessoal /></PrivateRoute>} />
        <Route path="/assinatura" element={<PrivateRoute><Subscription /></PrivateRoute>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
