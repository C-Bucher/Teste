import { useState, useEffect } from 'react';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import api from '../api';
import { motion } from 'framer-motion';
import Layout from '../components/Layout';

export default function Dashboard() {
  const [financialData, setFinancialData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [cashflowRes, dreRes, entriesRes] = await Promise.all([
          api.get('/financial/cashflow'),
          api.get('/financial/dre'),
          api.get('/financial/entries?page=1&size=5')
        ]);
        setFinancialData({
          cashflow: cashflowRes.data,
          dre: dreRes.data,
          entries: entriesRes.data.items
        });
      } catch (err) {
        console.error("Erro ao carregar dados", err);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <Layout>
        <div className="h-full flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </Layout>
    );
  }

  const chartData = [
    { name: 'Jan', receitas: 4000, despesas: 2400 },
    { name: 'Fev', receitas: 3000, despesas: 1398 },
    { name: 'Mar', receitas: 2000, despesas: 9800 },
    { name: 'Abr', receitas: 2780, despesas: 3908 },
    { name: 'Mai', receitas: 1890, despesas: 4800 },
    { name: 'Jun', receitas: 2390, despesas: 3800 },
  ];

  return (
    <Layout>
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-lg">
        {/* Dashboard Header */}
        <div className="flex justify-between items-end mb-lg">
          <div>
            <h2 className="font-headline-md text-headline-md text-on-surface">Visão Geral Financeira</h2>
            <p className="text-on-surface-variant font-body-sm">
              Bem-vindo de volta. Sua saúde financeira está <span className="text-success font-bold">Estável (+12%)</span>.
            </p>
          </div>
          <div className="flex gap-sm">
            <button className="bg-surface-container-high px-md py-sm rounded-lg flex items-center gap-sm hover:bg-surface-bright transition-colors border border-border-subtle">
              <span className="material-symbols-outlined text-[18px]">calendar_today</span>
              <span className="font-label-md">Últimos 30 dias</span>
            </button>
            <button className="bg-primary text-on-primary px-md py-sm rounded-lg flex items-center gap-sm hover:opacity-90 transition-all font-label-md shadow-lg shadow-primary/20">
              <span className="material-symbols-outlined text-[18px]">download</span>
              Exportar Relatório
            </button>
          </div>
        </div>

        {/* Bento Grid Layout */}
        <div className="grid grid-cols-12 gap-lg h-auto">
          
          {/* KPI Quick Cards */}
          <div className="col-span-12 lg:col-span-3 glass-card p-lg rounded-xl flex flex-col justify-between group">
            <div>
              <div className="flex justify-between items-start mb-sm">
                <span className="text-on-surface-variant font-label-md">Receita Bruta</span>
                <span className="text-success text-xs font-bold bg-success/10 px-2 py-0.5 rounded-full">+8.4%</span>
              </div>
              <h3 className="font-display-lg text-display-lg text-primary transition-transform duration-300 group-hover:scale-105 origin-left">
                R$ {financialData?.dre?.total_receitas?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) || '0,00'}
              </h3>
            </div>
            <div className="mt-md h-8 flex items-end gap-1">
              <div className="bg-primary/20 w-full h-2 rounded-full overflow-hidden relative">
                <div className="bg-primary h-full w-4/5"></div>
              </div>
            </div>
          </div>

          <div className="col-span-12 lg:col-span-3 glass-card p-lg rounded-xl flex flex-col justify-between group">
            <div>
              <div className="flex justify-between items-start mb-sm">
                <span className="text-on-surface-variant font-label-md">Despesas Operacionais</span>
                <span className="text-success text-xs font-bold bg-success/10 px-2 py-0.5 rounded-full">-1.2%</span>
              </div>
              <h3 className="font-display-lg text-display-lg text-on-surface transition-transform duration-300 group-hover:scale-105 origin-left">
                R$ {financialData?.dre?.total_despesas?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) || '0,00'}
              </h3>
            </div>
            <div className="mt-md h-8 flex items-center justify-between">
              <div className="flex gap-1">
                <div className="w-1.5 h-4 bg-primary/40 rounded-full"></div>
                <div className="w-1.5 h-6 bg-primary/40 rounded-full"></div>
                <div className="w-1.5 h-3 bg-primary/40 rounded-full"></div>
                <div className="w-1.5 h-5 bg-primary rounded-full"></div>
              </div>
              <span className="text-xs text-on-surface-variant">Meta: &lt; R$ 10k</span>
            </div>
          </div>

          <div className="col-span-12 lg:col-span-3 glass-card p-lg rounded-xl flex flex-col justify-between group">
            <div>
              <div className="flex justify-between items-start mb-sm">
                <span className="text-on-surface-variant font-label-md">Lucro Líquido</span>
                <span className="text-error text-xs font-bold bg-error/10 px-2 py-0.5 rounded-full">+2.1%</span>
              </div>
              <h3 className="font-display-lg text-display-lg text-on-surface transition-transform duration-300 group-hover:scale-105 origin-left">
                R$ {financialData?.dre?.resultado_liquido?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) || '0,00'}
              </h3>
            </div>
            <div className="mt-md h-8 flex items-center gap-2">
              <span className="text-xs text-on-surface-variant">Margem: {financialData?.dre?.margem_percentual || '0'}%</span>
            </div>
          </div>

          {/* AI Virtual CFO Widget */}
          <div className="col-span-12 lg:col-span-3 glass-card p-lg rounded-xl border-primary/20 ai-aura relative overflow-hidden">
            <div className="absolute -right-4 -top-4 opacity-10">
              <span className="material-symbols-outlined text-[120px] text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
            </div>
            <div className="relative z-10">
              <div className="flex items-center gap-sm mb-md">
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-secondary flex items-center justify-center">
                  <span className="material-symbols-outlined text-on-primary text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
                </div>
                <span className="font-headline-sm text-headline-sm text-primary">CFO Virtual</span>
              </div>
              <p className="text-body-sm text-on-surface mb-lg italic">"Detectei uma anomalia nos gastos de AWS. Recomendo revisar a reserva de instâncias para economizar R$ 2.400/mês."</p>
              <button className="w-full py-sm bg-surface-bright rounded-lg text-primary font-label-md hover:bg-primary hover:text-on-primary transition-all border border-primary/30">
                Aplicar Otimização
              </button>
            </div>
          </div>

          {/* Revenue Chart (Recharts) */}
          <div className="col-span-12 lg:col-span-8 glass-card p-lg rounded-xl min-h-[400px] flex flex-col">
            <div className="flex justify-between items-center mb-xl">
              <h4 className="font-headline-sm text-headline-sm">Receita Mensal</h4>
              <div className="flex gap-md">
                <div className="flex items-center gap-xs">
                  <div className="w-3 h-3 rounded-full bg-primary"></div>
                  <span className="text-xs text-on-surface-variant">Receitas</span>
                </div>
                <div className="flex items-center gap-xs">
                  <div className="w-3 h-3 rounded-full bg-tertiary"></div>
                  <span className="text-xs text-on-surface-variant">Despesas</span>
                </div>
              </div>
            </div>
            
            <div className="w-full flex-1">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorReceitas" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#adc6ff" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#adc6ff" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorDespesas" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ffb786" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#ffb786" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="name" stroke="#8c909f" tick={{fill: '#8c909f', fontSize: 12}} axisLine={false} tickLine={false} />
                  <YAxis stroke="#8c909f" tick={{fill: '#8c909f', fontSize: 12}} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'rgba(28, 31, 42, 0.9)', borderColor: 'rgba(255, 255, 255, 0.1)', borderRadius: '0.75rem', color: '#dfe2f1', backdropFilter: 'blur(8px)' }}
                    itemStyle={{ color: '#dfe2f1' }}
                  />
                  <Area type="monotone" dataKey="receitas" stroke="#adc6ff" strokeWidth={3} fillOpacity={1} fill="url(#colorReceitas)" />
                  <Area type="monotone" dataKey="despesas" stroke="#ffb786" strokeWidth={3} fillOpacity={1} fill="url(#colorDespesas)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Expenses Bar Chart */}
          <div className="col-span-12 lg:col-span-4 glass-card p-lg rounded-xl flex flex-col justify-center">
            <h4 className="font-headline-sm text-headline-sm mb-xl">Categorias de Despesas</h4>
            <div className="space-y-lg">
              <div>
                <div className="flex justify-between mb-sm">
                  <span className="text-label-md font-label-md">Salários e RH</span>
                  <span className="text-label-md font-bold">R$ 22.400</span>
                </div>
                <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
                  <div className="h-full bg-secondary w-3/4 rounded-full"></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-sm">
                  <span className="text-label-md font-label-md">Infraestrutura Cloud</span>
                  <span className="text-label-md font-bold">R$ 12.100</span>
                </div>
                <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
                  <div className="h-full bg-primary w-1/2 rounded-full"></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-sm">
                  <span className="text-label-md font-label-md">Marketing</span>
                  <span className="text-label-md font-bold">R$ 8.500</span>
                </div>
                <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
                  <div className="h-full bg-tertiary w-1/3 rounded-full"></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between mb-sm">
                  <span className="text-label-md font-label-md">Operacional</span>
                  <span className="text-label-md font-bold">R$ 3.200</span>
                </div>
                <div className="h-2 bg-surface-container-highest rounded-full overflow-hidden">
                  <div className="h-full bg-outline w-1/6 rounded-full"></div>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Transactions Data Grid */}
          <div className="col-span-12 glass-card rounded-xl overflow-hidden">
            <div className="p-lg flex justify-between items-center border-b border-border-subtle">
              <h4 className="font-headline-sm text-headline-sm">Transações Recentes</h4>
              <button className="text-primary font-label-md hover:underline">Ver todas</button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-container-low/50">
                    <th className="p-md font-label-md text-on-surface-variant border-b border-border-subtle">Beneficiário / Origem</th>
                    <th className="p-md font-label-md text-on-surface-variant border-b border-border-subtle">Categoria</th>
                    <th className="p-md font-label-md text-on-surface-variant border-b border-border-subtle">Data</th>
                    <th className="p-md font-label-md text-on-surface-variant border-b border-border-subtle">Status</th>
                    <th className="p-md font-label-md text-on-surface-variant border-b border-border-subtle text-right">Valor</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle">
                  {financialData?.entries?.map((entry: any) => (
                    <tr key={entry.id} className="hover:bg-surface-bright transition-colors group">
                      <td className="p-md">
                        <div className="flex items-center gap-sm">
                          <div className="w-8 h-8 rounded bg-surface-container-highest flex items-center justify-center">
                            <span className="material-symbols-outlined text-[18px]">
                              {entry.type === 'RECEITA' ? 'trending_up' : 'trending_down'}
                            </span>
                          </div>
                          <span className="font-body-sm font-medium">{entry.description}</span>
                        </div>
                      </td>
                      <td className="p-md"><span className="text-body-sm text-on-surface-variant">{entry.category}</span></td>
                      <td className="p-md"><span className="text-body-sm text-on-surface-variant">{entry.due_date}</span></td>
                      <td className="p-md">
                        <span className={`px-sm py-0.5 rounded-full text-[10px] font-bold uppercase ${entry.status === 'PAGO' ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning'}`}>
                          {entry.status === 'PAGO' ? 'Concluído' : 'Pendente'}
                        </span>
                      </td>
                      <td className={`p-md text-right font-bold ${entry.type === 'RECEITA' ? 'text-success' : 'text-on-surface'}`}>
                        {entry.type === 'RECEITA' ? '+' : '- '}R$ {Number(entry.amount).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </motion.div>
    </Layout>
  );
}

