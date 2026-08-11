import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Plans from './pages/Plans';
import Checkout from './pages/Checkout';
import Subscription from './pages/Subscription';
import Dashboard from './pages/Dashboard';
import Kanban from './pages/Kanban';
import GestaoEquipe from './pages/GestaoEquipe';

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
        <Route path="/assinatura" element={<PrivateRoute><Subscription /></PrivateRoute>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
