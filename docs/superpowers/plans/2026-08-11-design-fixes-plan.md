# Correções de Design: colisão max-w + reestruturação do Hub Pessoal

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** Corrigir a colisão de tema Tailwind que quebra todas as classes `max-w-{xs,sm,md,lg,xl}` do projeto, e reestruturar o Hub Pessoal de "uma página com abas internas" para "itens de menu lateral próprios", com um alternador de workspace (Empresarial/Pessoal) no cabeçalho.

**Architecture:** Fix 1 é uma correção pontual de classes CSS, sem mudança estrutural. Fix 2 muda `HubPessoal.tsx` de estado interno (`useState<TabId>`) para roteamento por parâmetro de URL (`useParams`), e adiciona um estado de "modo de workspace" em `Layout.tsx` que decide qual conjunto de `navItems` é renderizado.

**Tech Stack:** React Router v7 (`useParams`, rotas aninhadas), mesmo stack já em uso.

## Global Constraints

- Não alterar a escala `--spacing-{xs,sm,md,lg,xl}` em `frontend/src/index.css` — ela é usada corretamente em centenas de lugares (`p-md`, `gap-lg` etc.). O fix é só nos usos de `max-w-*`/`w-*` que colidem com ela.
- Sem test runner configurado — verificação é manual no navegador (Chrome real do usuário, ou o navegador integrado).
- Projeto não é repositório git nesta fase — nenhuma task termina com commit.

---

### Task A: Corrigir colisão `max-w-*` em todos os 9 pontos

**Files:**
- Modify: `frontend/src/pages/IAEmpresarial.tsx` (3 ocorrências de `max-w-xl`, 1 de `max-w-xs`)
- Modify: `frontend/src/pages/HubPessoal.tsx` (1 ocorrência de `max-w-xl`, na seção "CFO Pessoal IA")
- Modify: `frontend/src/components/AICfoDrawer.tsx` (1 ocorrência de `max-w-md`)
- Modify: `frontend/src/pages/Kanban.tsx` (1 ocorrência de `max-w-md`)
- Modify: `frontend/src/pages/Checkout.tsx` (1 ocorrência de `max-w-lg`)
- Modify: `frontend/src/pages/Configuracoes.tsx` (1 ocorrência de `max-w-xs`)
- Modify: `frontend/src/pages/Financeiro.tsx` (1 ocorrência de `max-w-sm`, coexistindo com `min-w-[220px]`)

**Interfaces:** nenhuma — são trocas de className isoladas, sem novo estado ou prop.

- [ ] **Step 1: Trocar cada classe de escala nomeada por valor explícito em rem**

Mapa de substituição (usar Tailwind arbitrary value, que ignora a escala nomeada e aplica o valor exato):
`max-w-xs` → `max-w-[20rem]` (320px, valor padrão do Tailwind para xs)
`max-w-sm` → `max-w-[24rem]` (384px)
`max-w-md` → `max-w-[28rem]` (448px)
`max-w-lg` → `max-w-[32rem]` (512px)
`max-w-xl` → `max-w-[36rem]` (576px)

Aplicar essa troca exata nas 9 ocorrências listadas acima (grep `max-w-(xs|sm|md|lg|xl)\b` em `frontend/src` para confirmar que não sobrou nenhuma depois do fix — o grep deve retornar zero resultados).

- [ ] **Step 2: Verificar manualmente no navegador**

Com o frontend rodando: abrir `/ia` (aba CFO Virtual, Conciliação Bancária, Gerador de Orçamentos) e `/pessoal` → aba "CFO Pessoal IA" (antes da Task B, ainda é aba interna) e confirmar que os parágrafos de introdução agora fluem normalmente em 2-3 linhas, não mais uma palavra por linha. Abrir a gaveta de chat do CFO Virtual (botão flutuante) e confirmar que tem largura visível e usável (não mais 16px). No Kanban, clicar em um card e confirmar que o painel de detalhe abre com largura adequada. No Checkout, confirmar que a tela de confirmação de pagamento não está espremida. Em Configurações e Financeiro, conferir os campos afetados.

---

### Task B: Reestruturar Hub Pessoal em itens de menu lateral + alternador de workspace

**Files:**
- Modify: `frontend/src/pages/HubPessoal.tsx`
- Modify: `frontend/src/components/Layout.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Produces (Layout.tsx): estado `workspaceMode: 'empresarial' | 'pessoal'`, persistido em `localStorage.getItem('workspace_mode')`, lido/gravado por um botão alternador no header.
- Consumes (HubPessoal.tsx): `useParams<{ tab: string }>()` de `react-router-dom` em vez do atual `useState<TabId>('visao-geral')`.

- [ ] **Step 1: Trocar navegação interna por rota, em `HubPessoal.tsx`**

No topo do componente, importar `useParams, useNavigate` de `react-router-dom`. Substituir:

```tsx
const [activeTab, setActiveTab] = useState<TabId>('visao-geral');
```

por:

```tsx
const { tab } = useParams<{ tab: string }>();
const navigate = useNavigate();
const activeTab: TabId = (TABS.some((t) => t.id === tab) ? tab : 'visao-geral') as TabId;
```

Em todos os lugares do arquivo que hoje chamam `setActiveTab('algum-id')` (ex.: o botão "Ver extrato completo" na Visão Geral, que hoje faz `setActiveTab('extrato')`), trocar por `navigate('/pessoal/algum-id')`.

Remover inteiramente o bloco da barra de abas horizontal (linhas 918–934: `{/* Tab bar — pill style ... */}` até o `</div>` de fechamento) — a navegação entre seções passa a ser feita pelo menu lateral, não mais por abas internas.

Nos dois `useEffect` que hoje reagem a mudanças de `activeTab` (linhas 474–483, que recarregam dashboard/analytics ao trocar de aba), trocar a dependência de `[activeTab]` para `[tab]` (já que `activeTab` deixou de ser estado próprio).

Atualizar o breadcrumb do cabeçalho (linhas 906–911) para ser dinâmico, usando o label da aba atual:

```tsx
        <nav className="flex text-body-sm text-outline mb-xs gap-xs items-center">
          <span>Pessoal</span>
          <span className="material-symbols-outlined text-[12px]">chevron_right</span>
          <span className="text-primary">{TABS.find((t) => t.id === activeTab)?.label ?? 'Hub Pessoal'}</span>
        </nav>
        <h2 className="font-display-lg text-display-lg text-on-surface">{TABS.find((t) => t.id === activeTab)?.label ?? 'Hub Pessoal'}</h2>
```

- [ ] **Step 2: Rota com parâmetro em `App.tsx`**

Em `frontend/src/App.tsx`, substituir a rota `<Route path="/pessoal" element={<PrivateRoute><HubPessoal /></PrivateRoute>} />` por duas rotas:

```tsx
        <Route path="/pessoal" element={<Navigate to="/pessoal/visao-geral" />} />
        <Route path="/pessoal/:tab" element={<PrivateRoute><HubPessoal /></PrivateRoute>} />
```

(o import de `Navigate` já existe no arquivo, usado pelo `PrivateRoute`.)

- [ ] **Step 3: Estado de workspace mode em `Layout.tsx`**

Adicionar, junto aos outros estados do componente:

```tsx
  const [workspaceMode, setWorkspaceMode] = useState<'empresarial' | 'pessoal'>(
    () => (localStorage.getItem('workspace_mode') as 'empresarial' | 'pessoal') || (location.pathname.startsWith('/pessoal') ? 'pessoal' : 'empresarial')
  );

  const handleToggleWorkspace = () => {
    const next = workspaceMode === 'empresarial' ? 'pessoal' : 'empresarial';
    setWorkspaceMode(next);
    localStorage.setItem('workspace_mode', next);
    navigate(next === 'pessoal' ? '/pessoal/visao-geral' : '/dashboard');
  };
```

- [ ] **Step 4: `navItems` passa a depender de `workspaceMode`, com a lista pessoal completa**

Substituir o array `navItems` atual (linhas 87–99) por:

```tsx
  const bothScopesAvailable = showBusiness && showPersonal;
  const effectiveMode: 'empresarial' | 'pessoal' = bothScopesAvailable ? workspaceMode : (showPersonal ? 'pessoal' : 'empresarial');

  const businessNavItems = [
    { name: 'Dashboard', path: '/dashboard', icon: 'dashboard' },
    { name: 'Projetos', path: '/kanban', icon: 'view_kanban' },
    ...(user.role !== 'FUNCIONARIO' ? [{ name: 'Equipe', path: '/equipe', icon: 'groups' }] : []),
    ...(user.role !== 'FUNCIONARIO' ? [{ name: 'Financeiro', path: '/financeiro', icon: 'payments' }] : []),
    ...(user.role !== 'FUNCIONARIO' ? [{ name: 'Fornecedores', path: '/fornecedores', icon: 'local_shipping' }] : []),
    ...(user.role === 'ADMIN' ? [{ name: 'Configurações', path: '/configuracoes', icon: 'settings' }] : []),
    ...(user.role !== 'FUNCIONARIO' ? [{ name: 'Exportação', path: '/exportacao', icon: 'file_download' }] : []),
    ...(user.role !== 'FUNCIONARIO' ? [{ name: 'IA Empresarial', path: '/ia', icon: 'auto_awesome' }] : []),
  ];

  const personalNavItems = [
    { name: 'Visão Geral', path: '/pessoal/visao-geral', icon: 'dashboard' },
    { name: 'Extrato', path: '/pessoal/extrato', icon: 'receipt_long' },
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
```

Ajustar o `isActive` do `<Link>` (linha ~159) para lidar com sub-rotas do Hub Pessoal, já que `location.pathname` agora é `/pessoal/visao-geral` etc. e não bate exatamente com `item.path` quando o item é, por exemplo, `/pessoal/extrato` mas o usuário está em `/pessoal/extrato` mesmo — na verdade os `path` de `personalNavItems` já são as rotas completas de cada aba, então a comparação exata `location.pathname === item.path` continua funcionando sem mudança adicional.

- [ ] **Step 5: Botão alternador no header (desktop e mobile), só quando `bothScopesAvailable`**

No header desktop (`TopNavBar`, dentro da `<div className="flex items-center gap-md">`, antes do botão de notificações), adicionar, condicionado a `bothScopesAvailable`:

```tsx
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
```

Adicionar o mesmo botão (versão compacta, só ícone, mesmo padrão dos outros botões do header mobile) no header mobile, ao lado do sino de notificações.

- [ ] **Step 6: Verificar manualmente no navegador**

Login como admin (plano Completo): confirmar que o botão "Ir para Pessoal" aparece no header; clicar nele e confirmar que a URL vai para `/pessoal/visao-geral`, o menu lateral troca inteiramente para os 11 itens pessoais (sem os itens empresariais visíveis), e não há mais barra de abas horizontal dentro da página. Clicar em cada item do menu pessoal e confirmar que a URL muda (`/pessoal/extrato`, `/pessoal/metas` etc.) e o conteúdo correspondente aparece. Clicar em "Ir para Empresarial" e confirmar que volta ao menu de negócio. Testar com um usuário de plano só "Pessoal" (criar um via `/cadastro` selecionando o plano Pessoal) e confirmar que o botão alternador não aparece — o menu já vem direto com os itens pessoais.
