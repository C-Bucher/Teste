# Expansão do Frontend TechConnect v2.0 — Implementation Plan

**Goal:** Construir todas as telas/funcionalidades de frontend que faltam para cobrir os 10 módulos da ERS v2.0.1 (M0 expandido, M1–M8-IA), mais o modelo de conta por plano (Pessoal/Empresarial/Completo), consumindo endpoints mock do FastAPI já existentes ou adicionados neste plano.

**Architecture:** React 19 + Vite + Tailwind v4 ("Obsidian Flow" — glass-card, tokens de `index.css`), React Router v7, Axios (`frontend/src/api.ts`), Framer Motion para transições, Recharts para gráficos, Lucide + Material Symbols para ícones. Backend: FastAPI com dados em memória (`app/db/database.py`), sem persistência real (fora de escopo). Cada página nova segue exatamente o padrão já estabelecido em `GestaoEquipe.tsx` (CRUD lista/cartão + modal), `Kanban.tsx` (board) e `Dashboard.tsx` (KPIs/gráficos).

**Tech Stack:** TypeScript, React 19, react-router-dom 7, axios, framer-motion, recharts, lucide-react, Tailwind v4. Python 3.11, FastAPI, Pydantic implícito via `dict`. Sem MySQL/SQLAlchemy real nesta fase.

## Global Constraints

- Não adicionar novas dependências de pacote — tudo já necessário está em `frontend/package.json` (axios, framer-motion, lucide-react, recharts, react-router-dom, clsx, tailwind-merge).
- Seguir o design system existente: classes `glass-card`, `font-headline-*`, `text-on-surface*`, `bg-surface-container-*`, espaçamento `p-{xs,sm,md,lg,xl}` — nunca introduzir valores de cor/espaçamento fora dos tokens definidos em `frontend/src/index.css`.
- Toda página autenticada é envolvida por `<Layout>` (`frontend/src/components/Layout.tsx`), igual a `Dashboard.tsx`/`Kanban.tsx`/`GestaoEquipe.tsx`.
- Toda chamada de API usa a instância `api` de `frontend/src/api.ts` (injeta o Bearer token automaticamente) — nunca `fetch` ou `axios` direto.
- Não existe test runner configurado no frontend (`package.json` não tem Jest/Vitest apesar de o DAS mencionar) nem no backend (`requirements.txt` não tem pytest). Por isso, os passos de verificação deste plano usam checagem manual no navegador em vez de testes automatizados — cada task tem um checklist de verificação explícito no lugar do ciclo de teste tradicional. Isso é uma adaptação deliberada à realidade do código-base atual, não um placeholder.
- Fora de escopo (não tocar): persistência MySQL real, RBAC de fato aplicado no backend, 2FA/TOTP, chamadas reais à API Gemini, tabelas de auditoria append-only, correção da chave exposta em `docker-compose.yml`, atualização da Declaração de Escopo/ERS.
- Backend continua rodando via `uvicorn app.main:app --reload --port 8000` (ou Docker Compose); frontend via `npm run dev` em `frontend/`. Ambos já sobem sem configuração adicional.
- O diretório do projeto não é um repositório git nesta fase — por isso nenhuma task abaixo termina com passo de commit. Se isso mudar antes da execução, cada task deve ganhar um commit próprio ao final (`git add <arquivos da task> && git commit -m "..."`).
- **Barra de qualidade visual**: o usuário considera o design atual bom, mas pede atenção redobrada de agora em diante — cada tela nova precisa ficar tão bem estruturada, com boa hierarquia e contraste, quanto as melhores partes do que já existe. Nunca aceitar baixo contraste entre elementos empilhados (ex.: um card quase invisível sobre o fundo da coluna que o contém) nem espaçamento apertado demais para o conteúdo. Ao terminar cada task visual, o implementador deve abrir a tela no navegador e avaliar criticamente antes de considerar concluído — não apenas "renderizou sem erro".

---

## Fase 0 — Modelo de conta por plano

### Task 1: Redesenhar `PLANS_DB` com `scope` (Pessoal / Empresarial / Completo)

**Files:**
- Modify: `app/api/v1/endpoints/plans.py`

**Interfaces:**
- Produces: `PLANS_DB` — lista de dicts, cada um agora com campo `"scope": "pessoal" | "empresarial" | "completo"`. Consumido por `frontend/src/pages/Plans.tsx`, `Register.tsx`, `Checkout.tsx` e por `app/api/v1/endpoints/auth.py` (Task 2).

- [ ] **Step 1: Substituir o conteúdo de `PLANS_DB`**

Editar `app/api/v1/endpoints/plans.py`, substituindo o array `PLANS_DB` (linhas 5–68) por:

```python
PLANS_DB = [
    {
        "id": "plan-pessoal",
        "name": "Pessoal",
        "scope": "pessoal",
        "tagline": "Organize suas finanças pessoais com apoio de IA",
        "price_monthly": 19.90,
        "price_yearly": 15.90,
        "popular": False,
        "features": [
            "Hub Pessoal completo: contas, cartões, orçamento e metas",
            "Controle de dívidas e assinaturas recorrentes",
            "Divisão de despesas com terceiros",
            "CFO Pessoal IA com dicas de economia",
            "Dashboard analítico de evolução patrimonial"
        ],
        "limits": {"max_employees": 0, "max_projects": 0, "ai_queries": 30}
    },
    {
        "id": "plan-empresarial",
        "name": "Empresarial",
        "scope": "empresarial",
        "tagline": "Gestão financeira e operacional completa da sua PME",
        "price_monthly": 249.00,
        "price_yearly": 199.00,
        "popular": True,
        "features": [
            "Kanban operacional com Cost-per-Task em tempo real",
            "Financeiro empresarial: DRE, fluxo de caixa D+90, conciliação",
            "Colaboradores com CTC automático, fornecedores e centros de custo",
            "CFO Virtual IA, conciliação bancária e gerador de orçamentos",
            "Exportação de relatórios em CSV, XLSX e PDF"
        ],
        "limits": {"max_employees": 15, "max_projects": -1, "ai_queries": -1}
    },
    {
        "id": "plan-completo",
        "name": "Completo",
        "scope": "completo",
        "tagline": "Pessoa física e empresa, tudo em uma conta só",
        "price_monthly": 279.00,
        "price_yearly": 229.00,
        "popular": False,
        "features": [
            "Tudo do plano Empresarial",
            "Tudo do plano Pessoal",
            "Um único login para gerir sua empresa e suas finanças pessoais",
            "CFO Virtual IA (empresarial) + CFO Pessoal IA (pessoal)"
        ],
        "limits": {"max_employees": 15, "max_projects": -1, "ai_queries": -1}
    }
]
```

- [ ] **Step 2: Verificar manualmente**

Com o backend rodando (`uvicorn app.main:app --reload --port 8000` a partir da raiz do projeto), acessar `http://localhost:8000/api/v1/plans/` no navegador ou via `curl` e confirmar que os 3 planos aparecem com o campo `scope` correto.

---

### Task 2: Propagar `plan_scope` no cadastro/login

**Files:**
- Modify: `app/api/v1/endpoints/auth.py`

**Interfaces:**
- Consumes: `PLANS_DB` de `app/api/v1/endpoints/plans.py` (Task 1) — precisa importar.
- Produces: objeto `user` retornado por `/auth/register` e `/auth/login` agora inclui `plan_scope: str` (`"pessoal" | "empresarial" | "completo"`), lido por `frontend/src/components/Layout.tsx` (Task 3) via `localStorage.getItem('user')`.

- [ ] **Step 1: Importar `PLANS_DB` e resolver o scope no registro**

Em `app/api/v1/endpoints/auth.py`, adicionar ao topo do arquivo (junto aos outros imports):

```python
from app.api.v1.endpoints.plans import PLANS_DB
```

Na função `register` (dentro do bloco que monta `new_user`, por volta da linha 31), adicionar a resolução do scope logo antes de `new_user = {...}`:

```python
    plan = next((p for p in PLANS_DB if p["id"] == b.selected_plan), None)
    plan_scope = plan["scope"] if plan else "completo"
```

E incluir o campo no dict `new_user`:

```python
    new_user = {
        "id": user_id,
        "email": b.email,
        "full_name": b.full_name,
        "role": "ADMIN",
        "company_name": b.company_name,
        "selected_plan": b.selected_plan,
        "plan_scope": plan_scope,
        "password_hash": pwd_hash,
        "is_active": True,
        "mfa_enabled": False
    }
```

- [ ] **Step 2: Garantir que os 3 usuários mock existentes tenham `plan_scope`**

Em `app/db/database.py`, dentro de `USERS_DB` (linhas 5–9), adicionar `"plan_scope":"completo"` a cada um dos três usuários (`admin@techconnect.com.br`, `gerente@techconnect.com.br`, `funcionario@techconnect.com.br`), para que continuem enxergando todos os módulos por padrão:

```python
USERS_DB = {
    "admin@techconnect.com.br": {"id":"usr-001","email":"admin@techconnect.com.br","full_name":"Administrador","role":"ADMIN","plan_scope":"completo","password_hash":ADMIN_HASH,"is_active":True,"mfa_enabled":False},
    "gerente@techconnect.com.br": {"id":"usr-002","email":"gerente@techconnect.com.br","full_name":"Ana Souza","role":"GERENTE","plan_scope":"completo","password_hash":bcrypt.hashpw(b"Gerente@123",bcrypt.gensalt()).decode(),"is_active":True,"mfa_enabled":False},
    "funcionario@techconnect.com.br": {"id":"usr-003","email":"funcionario@techconnect.com.br","full_name":"Carlos Mendes","role":"FUNCIONARIO","plan_scope":"completo","password_hash":bcrypt.hashpw(b"Func@123",bcrypt.gensalt()).decode(),"is_active":True,"mfa_enabled":False},
}
```

- [ ] **Step 3: Verificar manualmente**

Reiniciar o backend. Fazer `POST /api/v1/auth/login` com `admin@techconnect.com.br` / `Admin@123` (via navegador na tela de login depois que o frontend subir, ou via `curl`) e confirmar que a resposta `user` contém `"plan_scope":"completo"`.

---

### Task 3: Gating de navegação por `plan_scope` no `Layout.tsx`

**Files:**
- Modify: `frontend/src/components/Layout.tsx`

**Interfaces:**
- Consumes: `user.plan_scope` de `localStorage.getItem('user')` (produzido pela Task 2).
- Produces: array `navItems` filtrado — usado pelas próximas tasks como referência para saber em qual grupo (`empresarial`, `pessoal`, `todos`) cada rota nova entra.

- [ ] **Step 1: Adicionar os novos itens de navegação com filtro por `plan_scope`**

Em `frontend/src/components/Layout.tsx`, substituir o array `navItems` (linhas 29–35) por:

```tsx
  const scope = user.plan_scope || 'completo';
  const showBusiness = scope === 'empresarial' || scope === 'completo';
  const showPersonal = scope === 'pessoal' || scope === 'completo';

  const navItems = [
    ...(showBusiness ? [{ name: 'Dashboard', path: '/dashboard', icon: 'dashboard' }] : []),
    ...(showBusiness ? [{ name: 'Projetos', path: '/kanban', icon: 'view_kanban' }] : []),
    ...(showBusiness && user.role !== 'FUNCIONARIO' ? [{ name: 'Equipe', path: '/equipe', icon: 'groups' }] : []),
    ...(showBusiness && user.role !== 'FUNCIONARIO' ? [{ name: 'Financeiro', path: '/financeiro', icon: 'payments' }] : []),
    ...(showBusiness && user.role !== 'FUNCIONARIO' ? [{ name: 'Fornecedores', path: '/fornecedores', icon: 'local_shipping' }] : []),
    ...(showBusiness && user.role === 'ADMIN' ? [{ name: 'Configurações', path: '/configuracoes', icon: 'settings' }] : []),
    ...(showBusiness && user.role !== 'FUNCIONARIO' ? [{ name: 'Exportação', path: '/exportacao', icon: 'file_download' }] : []),
    ...(showBusiness && user.role !== 'FUNCIONARIO' ? [{ name: 'IA Empresarial', path: '/ia', icon: 'auto_awesome' }] : []),
    ...(showPersonal ? [{ name: 'Hub Pessoal', path: '/pessoal', icon: 'person' }] : []),
    { name: 'Assinatura', path: '/assinatura', icon: 'credit_card' },
    { name: 'Planos & Preços', path: '/planos', icon: 'workspace_premium' },
  ];
```

- [ ] **Step 2: Verificar manualmente**

Com o frontend rodando, fazer login como `admin@techconnect.com.br` e confirmar no menu lateral que todos os itens acima aparecem (scope `completo`). As rotas ainda não existem — está tudo bem que dêem 404 por enquanto; o objetivo desta task é só confirmar que os itens de menu aparecem corretamente antes de cada rota ser criada nas tasks seguintes.

---

## Fase 1 — M5 Configurações da Empresa

### Task 4: Página `Configuracoes.tsx`

**Files:**
- Create: `frontend/src/pages/Configuracoes.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `api` de `frontend/src/api.ts`; `Layout` de `frontend/src/components/Layout.tsx`.
- Endpoints (já existem em `app/api/v1/endpoints/company.py`):
  - `GET /company/` → `{id, name, cnpj, email, phone, address, fiscal_year_start}`
  - `PUT /company/` (body: subset dos campos acima) → objeto atualizado
  - `GET /company/categories` → `[{id, name, type: "RECEITA"|"DESPESA"}]`
  - `POST /company/categories` (body: `{name, type}`) → categoria criada
  - `GET /company/cost-centers` → `[{id, name, code}]`
  - `POST /company/cost-centers` (body: `{name, code}`) → centro criado
  - `DELETE /company/cost-centers/{id}` → `{success:true}`
  - `GET /company/calendar` → `{work_days:[1..5], work_hours_per_day:8, holidays:[]}`
  - `PUT /company/calendar` (body: subset) → objeto atualizado

- [ ] **Step 1: Criar a página com 4 abas**

Criar `frontend/src/pages/Configuracoes.tsx` com a seguinte estrutura funcional (seguir exatamente os componentes visuais já usados em `GestaoEquipe.tsx`: `glass-card`/`glass-panel`, cabeçalho com breadcrumb `font-display-lg`, modal de criação com `AnimatePresence`):

- Estado de aba ativa: `'empresa' | 'plano-contas' | 'centros-custo' | 'calendario'`, barra de abas no topo estilo pill (`bg-surface-container-low p-1 rounded-lg`, item ativo `bg-primary-container text-on-primary-container`).
- **Aba "Dados da Empresa"**: formulário controlado com campos `name`, `cnpj`, `email`, `phone`, `address`; `useEffect` inicial faz `GET /company/`, botão "Salvar" faz `PUT /company/` com os campos alterados e mostra toast simples (reaproveitar `alert()` como já faz `GestaoEquipe.tsx` em erros, para manter consistência) em caso de erro.
- **Aba "Plano de Contas"**: lista de categorias em tabela (`name`, `type` com badge colorido igual ao padrão de status de `GestaoEquipe.tsx`), botão "Nova Categoria" abre modal com campos `name` (texto) e `type` (select RECEITA/DESPESA), `POST /company/categories` ao salvar, atualiza lista local via `setCategories([...categories, res.data])`.
- **Aba "Centros de Custo"**: lista em tabela (`name`, `code`), botão "Novo Centro de Custo" abre modal com `name`+`code`, `POST /company/cost-centers`; botão de excluir por linha chama `DELETE /company/cost-centers/{id}` com `confirm()` antes, igual ao padrão de `handleDelete` de `GestaoEquipe.tsx`.
- **Aba "Calendário Útil"**: 7 checkboxes (Dom–Sáb, valores `0..6`) ligados a `work_days`, input numérico para `work_hours_per_day`; `useEffect` inicial faz `GET /company/calendar`; botão "Salvar" faz `PUT /company/calendar`.

Toda a página envolvida por `<Layout>{...}</Layout>`, com `loading` inicial (`animate-spin` igual às outras páginas) enquanto os 3 GETs iniciais (`/company/`, `/company/categories`, `/company/cost-centers`) não retornam — usar `Promise.all` como em `Dashboard.tsx`.

- [ ] **Step 2: Registrar a rota**

Em `frontend/src/App.tsx`, adicionar o import `import Configuracoes from './pages/Configuracoes';` e a rota:

```tsx
        <Route path="/configuracoes" element={<PrivateRoute><Configuracoes /></PrivateRoute>} />
```

(inserir junto às demais rotas privadas, antes do fechamento de `<Routes>`).

- [ ] **Step 3: Verificar manualmente no navegador**

Com backend e frontend rodando: login como admin → clicar em "Configurações" no menu → confirmar que a aba "Dados da Empresa" carrega os dados de `COMPANY` (nome "TechConnect Solucoes Ltda" etc. — ver `app/db/database.py` linha 108), editar o telefone e salvar, recarregar a página e confirmar que persistiu (em memória, até o backend reiniciar). Repetir para as outras 3 abas: criar uma categoria, criar e excluir um centro de custo, alterar a jornada de trabalho.

---

## Fase 2 — M6 Fornecedores

### Task 5: Página `Fornecedores.tsx`

**Files:**
- Create: `frontend/src/pages/Fornecedores.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Endpoints (já existem em `app/api/v1/endpoints/suppliers.py`):
  - `GET /suppliers/?active_only=true|false` → `[{id, name, cnpj_cpf, category, is_active, email}]`
  - `POST /suppliers/` (body: `{name, cnpj_cpf, category, email}`) → fornecedor criado (`is_active:true` por padrão)
  - `PUT /suppliers/{id}` (body: subset) → atualizado
  - `DELETE /suppliers/{id}` → `{success:true}` (usar como "desativar": em vez de excluir de fato, o botão de exclusão da UI deve chamar `PUT /suppliers/{id}` com `{is_active:false}`, para refletir soft-delete conforme a ERS RN-07 — não usar o `DELETE` físico na UI)

- [ ] **Step 1: Criar a página copiando a estrutura de `GestaoEquipe.tsx`**

Criar `frontend/src/pages/Fornecedores.tsx` reaproveitando literalmente a estrutura de `frontend/src/pages/GestaoEquipe.tsx` (toggle lista/cartão, modal de criar/editar, `AnimatePresence`), adaptando:
- Título/breadcrumb: "Fornecedores" em vez de "Gestão de Equipe".
- Campos do formulário: `name` (Nome/Razão Social), `cnpj_cpf`, `category` (select livre ou texto: Cloud, Bancário, Dev Tools, Contabilidade, Aluguel, Outros), `email`.
- Badge de status usa `is_active` (Ativo/Inativo) como em `GestaoEquipe.tsx`.
- Botão de card/linha "Desativar" (em vez de "Excluir") chama `api.put('/suppliers/{id}', {is_active: false})`.
- Sem toggle de papel (`isGerente`) restringindo o botão de adicionar — Admin e Gerente podem ambos criar/editar fornecedores, conforme a ERS (M6: Admin, Gerente).

- [ ] **Step 2: Registrar a rota**

Em `frontend/src/App.tsx`: `import Fornecedores from './pages/Fornecedores';` e:

```tsx
        <Route path="/fornecedores" element={<PrivateRoute><Fornecedores /></PrivateRoute>} />
```

- [ ] **Step 3: Verificar manualmente no navegador**

Login como gerente → "Fornecedores" → confirmar que os 5 fornecedores mock (`AWS Brasil`, `Conta Simples`, `GitHub Inc`, `Contabilidade Faria`, `Aluguel Comercial SA` — ver `app/db/database.py` linhas 21–27) aparecem; criar um novo fornecedor, editar um existente, desativar um e confirmar que o badge muda para "Inativo" sem sumir da lista.

---

## Fase 3 — M3 completar (Colaboradores e CTC)

### Task 6: Enriquecer `GestaoEquipe.tsx` com CTC, histórico salarial e desligamento

**Files:**
- Modify: `frontend/src/pages/GestaoEquipe.tsx`

**Interfaces:**
- Endpoints já existentes em `app/api/v1/endpoints/employees.py`:
  - `GET /employees/{id}/salary-history` → `{items:[{id, employee_id, base_salary, ctc_monthly, ctc_snapshot, changed_at, reason}]}`
  - `POST /employees/{id}/terminate` → funcionário atualizado com `is_active:false, end_date`
- Campos já presentes no objeto `employee` retornado por `GET /employees/`: `hourly_rate`, `ctc_monthly`, `contract_type` (ver `app/db/database.py` linhas 15–19).

- [ ] **Step 1: Exibir custo/hora e CTC nos cartões e na tabela**

Em `frontend/src/pages/GestaoEquipe.tsx`, na visão em cartão (dentro do `.map` de `employees`, após o bloco `<div className="space-y-sm border-t ...">` que lista email/telefone/contrato, por volta da linha 289), adicionar:

```tsx
                  <div className="flex items-center gap-sm text-body-sm text-on-surface-variant">
                    <span className="material-symbols-outlined text-[18px]">payments</span>
                    <span>R$ {Number(emp.hourly_rate ?? 0).toFixed(2)}/h · CTC R$ {Number(emp.ctc_monthly ?? 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                  </div>
```

Na visão em lista (tabela), adicionar uma coluna "Custo/Hora" entre "Cargo" e "Status" — cabeçalho `<th className="px-lg py-md font-label-md text-label-md text-on-surface-variant">Custo/Hora</th>` e célula `<td className="px-lg py-md text-on-surface-variant font-label-md text-label-md">R$ {Number(emp.hourly_rate ?? 0).toFixed(2)}/h</td>`.

- [ ] **Step 2: Adicionar modal "Histórico Salarial"**

Adicionar novo estado: `const [historyModal, setHistoryModal] = useState<{ open: boolean; items: any[]; employeeName: string }>({ open: false, items: [], employeeName: '' });`

Adicionar função:

```tsx
  const handleViewHistory = async (emp: any) => {
    try {
      const res = await api.get(`/employees/${emp.id}/salary-history`);
      setHistoryModal({ open: true, items: res.data.items, employeeName: emp.full_name });
    } catch (err) {
      console.error('Erro ao carregar histórico', err);
      alert('Erro ao carregar histórico salarial');
    }
  };
```

Adicionar um botão "Histórico" (ícone `history`) ao lado dos botões de editar/excluir, tanto na linha da tabela quanto no menu do cartão, chamando `handleViewHistory(emp)`.

Adicionar um segundo bloco `<AnimatePresence>` (após o modal existente, antes do fechamento de `</Layout>`) exibindo uma tabela simples com `changed_at`, `base_salary`, `ctc_monthly`, `reason` de `historyModal.items`, título "Histórico Salarial — {historyModal.employeeName}", fechável com `onClick={() => setHistoryModal({ open: false, items: [], employeeName: '' })}` — reaproveitar exatamente o wrapper visual (`bg-black/60 backdrop-blur-sm` + `bg-surface-container-high border ... rounded-2xl`) do modal de edição já existente.

- [ ] **Step 3: Trocar "Excluir" por "Desligar"**

Substituir `handleDelete` (linhas 46–56) por:

```tsx
  const handleTerminate = async (id: string) => {
    if (confirm('Deseja realmente desligar este colaborador? O histórico será preservado.')) {
      try {
        const res = await api.post(`/employees/${id}/terminate`);
        setEmployees(employees.map((e: any) => (e.id === id ? res.data : e)));
      } catch (err) {
        console.error('Erro ao desligar', err);
        alert('Erro ao desligar colaborador');
      }
    }
  };
```

Trocar as chamadas de `handleDelete(emp.id)` (tabela e cartão) por `handleTerminate(emp.id)`, e o ícone/label do botão de "delete" (`<span className="material-symbols-outlined text-sm">delete</span>`) por `person_off` com o mesmo estilo visual (mantendo a cor `text-error` no hover).

- [ ] **Step 4: Verificar manualmente no navegador**

Login como admin → "Equipe" → confirmar que custo/hora e CTC aparecem em cada colaborador (nas duas visões); clicar em "Histórico" de um colaborador e confirmar que exibe os 2 registros mock (ver `salary-history` em `employees.py`); clicar em "Desligar" e confirmar que o badge muda para "Inativo" sem remover o colaborador da lista.

---

## Fase 4 — M2 Financeiro Empresarial

### Task 7: Página `Financeiro.tsx`

**Files:**
- Create: `frontend/src/pages/Financeiro.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Endpoints já existentes em `app/api/v1/endpoints/financial.py`:
  - `GET /financial/entries?type=&status=&search=&category=&page=&size=` → `{items:[...], total, page, size, pages}` — cada item: `{id, type:"RECEITA"|"DESPESA", amount, description, due_date, payment_date, status:"PAGO"|"PENDENTE", category, supplier_id, cost_center}`
  - `POST /financial/entries` (body livre, ex.: `{type, amount, description, due_date, category, cost_center}`) → lançamento criado
  - `PUT /financial/entries/{id}` → atualizado
  - `POST /financial/entries/{id}/pay` → marca como `PAGO`
  - `GET /financial/dre?start_date=&end_date=` → `{period, total_receitas, total_despesas, receitas:[{categoria,total}], despesas:[{categoria,total}], resultado_liquido, margem_percentual}`
  - `GET /financial/cashflow` → `{items:[{date, receitas, despesas, saldo_acumulado}], saldo_atual, receitas_previstas_30d, despesas_previstas_30d, projected_balance, alert_level:"VERDE"|"AMARELO"|"VERMELHO"}`

- [ ] **Step 1: Criar a página com 3 abas**

Criar `frontend/src/pages/Financeiro.tsx`:

- Abas: `'lancamentos' | 'dre' | 'fluxo-caixa'` (mesmo padrão de pill tabs da Task 4).
- **Aba "Lançamentos"**: tabela com colunas Descrição, Tipo (badge RECEITA verde / DESPESA vermelho), Categoria, Vencimento, Status (badge PAGO/PENDENTE), Valor (alinhado à direita, verde se RECEITA, vermelho se DESPESA); filtros no topo (select de Tipo, select de Status, input de busca) que disparam novo `GET /financial/entries` com os query params; botão "Novo Lançamento" abre modal com campos `type` (select RECEITA/DESPESA), `description`, `amount`, `category`, `cost_center`, `due_date` (date input) — `POST /financial/entries`; botão "Marcar como Pago" por linha (só visível se `status === 'PENDENTE'`) chama `POST /financial/entries/{id}/pay` e atualiza a linha localmente.
- **Aba "DRE"**: reaproveitar o padrão visual de `Dashboard.tsx` — 3 KPI cards no topo (Receita Total, Despesa Total, Resultado Líquido, com `margem_percentual` como badge), abaixo duas listas lado a lado ("Receitas por Categoria" e "Despesas por Categoria") vindas de `dre.receitas`/`dre.despesas`, com barra de proporção igual ao bloco "Categorias de Despesas" do `Dashboard.tsx`.
- **Aba "Fluxo de Caixa D+90"**: banner de alerta no topo com cor conforme `alert_level` (`VERDE` → `bg-success/10 text-success`, `AMARELO` → `bg-warning/10 text-warning`, `VERMELHO` → `bg-error/10 text-error`), texto "Saldo projetado em 90 dias: R$ {projected_balance}"; abaixo, `AreaChart` do Recharts com `items` (eixo X = `date`, duas áreas: `receitas` e `despesas`), seguindo exatamente o mesmo código de gradiente/eixos já usado em `Dashboard.tsx` (linhas 166–188).

- [ ] **Step 2: Registrar a rota**

Em `frontend/src/App.tsx`: `import Financeiro from './pages/Financeiro';` e:

```tsx
        <Route path="/financeiro" element={<PrivateRoute><Financeiro /></PrivateRoute>} />
```

- [ ] **Step 3: Verificar manualmente no navegador**

Login como gerente → "Financeiro" → aba Lançamentos: confirmar que os 12 lançamentos mock aparecem (ver `FINANCIAL_ENTRIES` em `app/db/database.py`), filtrar por "DESPESA", criar um lançamento novo, marcar um pendente como pago. Aba DRE: confirmar que os totais batem com a soma dos lançamentos. Aba Fluxo de Caixa: confirmar que o gráfico renderiza e o banner de alerta aparece com a cor certa (`VERDE`, conforme o mock).

---

### Task 8: Substituir dados fixos do Dashboard por dados reais

**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx`

**Interfaces:**
- Consumes: `GET /financial/entries?page=1&size=5` (mesmo endpoint da Task 7).

- [ ] **Step 1: Buscar as últimas transações junto com cashflow/dre**

Em `frontend/src/pages/Dashboard.tsx`, dentro de `fetchDashboardData` (linhas 12–29), adicionar `/financial/entries` ao `Promise.all`:

```tsx
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
```

- [ ] **Step 2: Substituir a tabela hardcoded por dados reais**

Substituir o bloco `<tbody className="divide-y divide-border-subtle">...</tbody>` (linhas 252–301, as 3 linhas fixas de AWS/Apple/Stripe) por:

```tsx
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
```

- [ ] **Step 3: Verificar manualmente no navegador**

Recarregar o Dashboard e confirmar que a tabela "Transações Recentes" agora mostra 5 lançamentos vindos do mock (não mais AWS/Apple/Stripe fixos), e que ao marcar um lançamento como pago na tela de Financeiro (Task 7) e voltar ao Dashboard, o status refletido é consistente.

---

## Fase 5 — M1 completar (Kanban Operacional)

### Task 9: CRUD de clientes e criação de projeto no `Kanban.tsx`

**Files:**
- Modify: `frontend/src/pages/Kanban.tsx`

**Interfaces:**
- Endpoints já existentes em `app/api/v1/endpoints/kanban.py`:
  - `GET /kanban/clients` → `[{id, name, email, phone, cnpj, contact_name, address, segment, status}]`
  - `POST /kanban/clients` (body: `{name, email, phone, cnpj, contact_name, segment}`) → cliente criado
  - `POST /kanban/projects` (body: `{name, description, client_id, start_date, end_date}`) → cria projeto + board padrão (Backlog/Em Andamento/Concluído)

- [ ] **Step 1: Buscar clientes junto com projetos**

Em `frontend/src/pages/Kanban.tsx`, adicionar estado `const [clients, setClients] = useState<any[]>([]);` e, dentro do `useEffect` que hoje só busca `/kanban/projects` (linhas 24–40), buscar também clientes em paralelo:

```tsx
  useEffect(() => {
    const fetchInitial = async () => {
      try {
        const [projRes, clientsRes] = await Promise.all([
          api.get('/kanban/projects'),
          api.get('/kanban/clients')
        ]);
        setProjects(projRes.data);
        setClients(clientsRes.data);
        if (projRes.data.length > 0) {
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
```

(Isso substitui o `fetchProjects` atual — remover a função antiga e sua chamada.)

- [ ] **Step 2: Modal "Novo Projeto" funcional**

Adicionar estados:

```tsx
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  const [projectForm, setProjectForm] = useState({ name: '', description: '', client_id: '', start_date: '', end_date: '' });
  const [isClientModalOpen, setIsClientModalOpen] = useState(false);
  const [clientForm, setClientForm] = useState({ name: '', email: '', phone: '', cnpj: '', contact_name: '', segment: '' });
```

Adicionar funções:

```tsx
  const handleSaveProject = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.post('/kanban/projects', projectForm);
      setProjects([...projects, res.data]);
      setSelectedProjectId(res.data.id);
      setIsProjectModalOpen(false);
      setProjectForm({ name: '', description: '', client_id: '', start_date: '', end_date: '' });
    } catch (err) {
      console.error('Erro ao criar projeto', err);
      alert('Erro ao criar projeto');
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
    } catch (err) {
      console.error('Erro ao criar cliente', err);
      alert('Erro ao criar cliente');
    }
  };
```

Trocar o `onClick` do botão "Novo Projeto" (hoje sem ação, linha 186–188) para `onClick={() => setIsProjectModalOpen(true)}`.

Adicionar um novo bloco `<AnimatePresence>` (mesmo padrão visual do modal de nova tarefa já existente) com o formulário de projeto: `name`, `description` (textarea), select `client_id` (populado de `clients`, com uma opção extra "+ Novo Cliente" que abre `isClientModalOpen`), `start_date`/`end_date` (date inputs). Um segundo `<AnimatePresence>` para o modal de novo cliente com os campos de `clientForm`.

- [ ] **Step 3: Verificar manualmente no navegador**

Login como gerente → "Projetos" → clicar em "Novo Projeto", criar um cliente novo pelo atalho dentro do modal, selecionar esse cliente, preencher nome/descrição e salvar; confirmar que o novo projeto aparece no select de projetos e que o board é criado com as 3 colunas padrão.

---

### Task 10: Timer e comentários nos cards do Kanban

**Files:**
- Modify: `frontend/src/pages/Kanban.tsx`

**Interfaces:**
- Endpoints já existentes: `POST /kanban/cards/{id}/timer/start`, `POST /kanban/cards/{id}/timer/stop` (retorna `{card_id, total_time_seconds, cost_per_task}`), `POST /kanban/cards/{id}/comments` (body: `{content}` → retorna `{id, card_id, author, content, created_at}`).

- [ ] **Step 1: Adicionar estado de timer ativo e botão start/stop no card**

Adicionar estado: `const [activeTimerCardId, setActiveTimerCardId] = useState<string | null>(null);`

Adicionar função:

```tsx
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
```

No bloco do card (dentro do `.map` de `column.cards`, próximo ao trecho `<span className="text-[11px] text-outline flex items-center gap-xs">` do cost_per_task, por volta da linha 283–288), adicionar antes dele um botão:

```tsx
                            <button
                              onClick={(e) => { e.stopPropagation(); handleToggleTimer(card.id); }}
                              className={`flex items-center gap-xs px-sm py-1 rounded-full text-[10px] font-bold ${activeTimerCardId === card.id ? 'bg-error/10 text-error' : 'bg-primary/10 text-primary'}`}
                            >
                              <span className="material-symbols-outlined text-xs" style={{ fontVariationSettings: "'FILL' 1" }}>
                                {activeTimerCardId === card.id ? 'stop' : 'play_arrow'}
                              </span>
                              {activeTimerCardId === card.id ? 'Parar' : 'Iniciar'}
                            </button>
```

- [ ] **Step 2: Painel lateral de detalhe do card com comentários**

Adicionar estados: `const [detailCard, setDetailCard] = useState<any>(null);` e `const [commentText, setCommentText] = useState('');`

Tornar o card clicável (adicionar `onClick={() => setDetailCard(card)}` na `div` raiz do card, cuidado para não conflitar com o `draggable`/drag handlers já existentes — manter os handlers de drag e apenas adicionar o `onClick` extra).

Adicionar função:

```tsx
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
```

Adicionar um painel lateral (drawer à direita, mesmo padrão de posicionamento do `AICfoDrawer.tsx`: `fixed inset-0 z-[100] flex justify-end`, largura `max-w-md`) que abre quando `detailCard` não é `null`, mostrando: título, descrição, responsável, prioridade, e uma lista de comentários (`detailCard.comments || []`) com input de novo comentário no rodapé chamando `handleAddComment`. Botão de fechar seta `setDetailCard(null)`.

- [ ] **Step 3: Verificar manualmente no navegador**

Clicar em "Iniciar" no timer de um card, confirmar que o botão muda para "Parar" com estilo vermelho; clicar em "Parar" e confirmar que `cost_per_task`/`total_time_seconds` do card atualizam após o `fetchBoard`. Clicar no corpo de um card (fora do botão de timer) e confirmar que o painel de detalhe abre; adicionar um comentário e confirmar que aparece na lista.

---

### Task 23: Redesenho visual dos cards do Kanban (legibilidade e hierarquia) — executar logo após a Task 10

**Motivo:** feedback direto do usuário — os cards do board estão com baixo contraste em relação ao fundo da coluna e ao fundo da página, dificultando a leitura; o layout em si é bom, mas precisa desses ajustes de superfície antes de acumular mais funcionalidade (timer, painel de detalhe) em cima.

**Files:**
- Modify: `frontend/src/pages/Kanban.tsx`

**Interfaces:** nenhuma nova — apenas ajustes de classes Tailwind/JSX nos mesmos elementos já existentes.

- [ ] **Step 1: Aumentar o contraste do fundo das colunas**

O problema raiz: o contêiner de cada coluna usa `bg-white/5` (ou `bg-primary-container/5`/`bg-success/5`) — 5% de opacidade sobre um fundo já quase preto (`--color-background: #0f131d`), o que deixa a coluna quase indistinguível do restante da página, e o card (`bg-surface` = `#111827`) some dentro dela por ter uma cor muito próxima.

Substituir a lógica de cores da coluna (por volta da linha 196–206 de `Kanban.tsx`):

```tsx
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
```

- [ ] **Step 2: Aumentar o contraste e a hierarquia visual do card**

Substituir a `className` da `div` raiz do card (por volta da linha 250) — trocar `bg-surface`/`bg-surface/60` por `bg-surface-container-high`/`bg-surface-container` (tons mais claros e mais distantes do fundo da página) e engrossar levemente a borda:

```tsx
                        className={`group ${isDone ? 'bg-surface-container/70 opacity-90' : 'bg-surface-container-high'} rounded-xl border ${isActive ? 'border-l-4 border-l-primary border-border-subtle' : 'border border-border-subtle/80'} p-md shadow-md hover:shadow-lg transition-all duration-300 cursor-grab active:cursor-grabbing hover:border-primary/40 hover:-translate-y-0.5`}
```

- [ ] **Step 3: Melhorar a legibilidade do rodapé do card (responsável + custo)**

O avatar hoje só mostra iniciais sem nome ao lado, e o valor de custo aparece pequeno e apagado (`text-[11px] text-outline`). Substituir o bloco de rodapé do card (por volta das linhas 276–288) por:

```tsx
                        <div className="flex items-center justify-between mt-auto pt-sm border-t border-border-subtle/60">
                          <div className="flex items-center gap-xs">
                            <div className="w-7 h-7 rounded-full bg-primary/20 border-2 border-surface flex items-center justify-center text-[10px] font-bold text-primary shrink-0" title={card.assignee}>
                              {card.assignee ? card.assignee.substring(0, 2).toUpperCase() : 'NN'}
                            </div>
                            <span className="text-[11px] text-on-surface-variant truncate max-w-[90px]">{card.assignee || 'Sem responsável'}</span>
                          </div>

                          <div className="flex items-center gap-sm shrink-0">
                            <span className="text-[12px] font-bold text-on-surface flex items-center gap-xs">
                              <span className="material-symbols-outlined text-sm text-primary">attach_money</span> {Number(card.cost_per_task || 0).toFixed(2)}
                            </span>
                          </div>
                        </div>
```

- [ ] **Step 4: Espaçamento e legibilidade do cabeçalho de coluna**

No cabeçalho da coluna (por volta das linhas 219–232), aumentar o contraste do texto do nome (hoje `text-on-surface-variant`, que é discreto demais para um título de coluna) e dar mais respiro:

```tsx
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
```

- [ ] **Step 5: Verificar manualmente no navegador**

Abrir "Projetos" e comparar visualmente com o estado anterior: os cards agora devem se destacar claramente do fundo da coluna, que por sua vez se destaca do fundo da página; o nome do responsável fica legível sem precisar passar o mouse; o valor de custo por card é a informação mais visível do rodapé. Testar em pelo menos 2 projetos diferentes (com colunas "Em Desenvolvimento" e "Concluído") para confirmar que as variações de cor de fundo por status continuam sutis, mas perceptíveis.

---

## Fase 6 — M0 Hub Pessoal expandido

### Task 11: Novos endpoints mock em `personal.py`

**Files:**
- Modify: `app/api/v1/endpoints/personal.py`
- Modify: `app/db/database.py`

**Interfaces:**
- Produces: endpoints consumidos pelas Tasks 12–17.

- [ ] **Step 1: Adicionar as novas listas mock em `database.py`**

Em `app/db/database.py`, ao final do arquivo (após `EXPORT_LOGS`), adicionar:

```python
PERSONAL_ACCOUNTS = [
    {"id":"pacc-001","name":"Conta Corrente Nubank","type":"CONTA","balance":4250.30,"limit":None},
    {"id":"pacc-002","name":"Cartão Nubank","type":"CARTAO","balance":-890.40,"limit":5000.00,"closing_day":28,"due_day":5},
]
PERSONAL_BUDGETS = [
    {"id":"pbud-001","category":"Alimentacao","limit_amount":1200.00,"spent_amount":650.00},
    {"id":"pbud-002","category":"Transporte","limit_amount":500.00,"spent_amount":410.00},
    {"id":"pbud-003","category":"Lazer","limit_amount":400.00,"spent_amount":390.00},
]
PERSONAL_GOALS = [
    {"id":"pgoal-001","name":"Reserva de Emergencia","target_amount":20000.00,"current_amount":8500.00,"target_date":"2027-01-01"},
    {"id":"pgoal-002","name":"Viagem Europa","target_amount":12000.00,"current_amount":3200.00,"target_date":"2026-12-01"},
]
PERSONAL_DEBTS = [
    {"id":"pdebt-001","name":"Financiamento Notebook","total_amount":4800.00,"remaining_amount":2400.00,"installments_total":12,"installments_paid":6,"interest_rate":2.5},
]
PERSONAL_SUBSCRIPTIONS = [
    {"id":"psub-001","name":"Netflix","amount":39.90,"billing_day":10,"category":"Streaming","is_active":True},
    {"id":"psub-002","name":"Academia","amount":99.90,"billing_day":5,"category":"Saude","is_active":True},
]
PERSONAL_SPLITS = [
    {"id":"psplit-001","description":"Aluguel Republica","total_amount":1800.00,"participants":[{"name":"Voce","share":600.00,"paid":True},{"name":"Joao","share":600.00,"paid":False},{"name":"Maria","share":600.00,"paid":True}]},
]
```

- [ ] **Step 2: Adicionar as rotas em `personal.py`**

Em `app/api/v1/endpoints/personal.py`, ajustar o import do topo para trazer as novas listas:

```python
from app.db.database import PERSONAL_ENTRIES, PERSONAL_ACCOUNTS, PERSONAL_BUDGETS, PERSONAL_GOALS, PERSONAL_DEBTS, PERSONAL_SUBSCRIPTIONS, PERSONAL_SPLITS
```

E adicionar ao final do arquivo:

```python
@router.get("/accounts")
async def get_accounts(u=Depends(get_current_user)): return PERSONAL_ACCOUNTS
@router.post("/accounts")
async def create_account(d:dict,u=Depends(get_current_user)):
    a={"id":f"pacc-{uuid.uuid4().hex[:6]}",**d}; PERSONAL_ACCOUNTS.append(a); return a
@router.delete("/accounts/{aid}")
async def del_account(aid:str,u=Depends(get_current_user)):
    global PERSONAL_ACCOUNTS
    PERSONAL_ACCOUNTS[:]=[x for x in PERSONAL_ACCOUNTS if x["id"]!=aid]; return {"success":True}

@router.get("/budgets")
async def get_budgets(u=Depends(get_current_user)): return PERSONAL_BUDGETS
@router.post("/budgets")
async def create_budget(d:dict,u=Depends(get_current_user)):
    b={"id":f"pbud-{uuid.uuid4().hex[:6]}","spent_amount":0.0,**d}; PERSONAL_BUDGETS.append(b); return b
@router.delete("/budgets/{bid}")
async def del_budget(bid:str,u=Depends(get_current_user)):
    global PERSONAL_BUDGETS
    PERSONAL_BUDGETS[:]=[x for x in PERSONAL_BUDGETS if x["id"]!=bid]; return {"success":True}

@router.get("/goals")
async def get_goals(u=Depends(get_current_user)): return PERSONAL_GOALS
@router.post("/goals")
async def create_goal(d:dict,u=Depends(get_current_user)):
    g={"id":f"pgoal-{uuid.uuid4().hex[:6]}","current_amount":0.0,**d}; PERSONAL_GOALS.append(g); return g
@router.post("/goals/{gid}/contribute")
async def contribute_goal(gid:str,d:dict,u=Depends(get_current_user)):
    g=next((x for x in PERSONAL_GOALS if x["id"]==gid),None)
    if not g: raise HTTPException(404)
    g["current_amount"]=round(g["current_amount"]+d.get("amount",0),2); return g
@router.delete("/goals/{gid}")
async def del_goal(gid:str,u=Depends(get_current_user)):
    global PERSONAL_GOALS
    PERSONAL_GOALS[:]=[x for x in PERSONAL_GOALS if x["id"]!=gid]; return {"success":True}

@router.get("/debts")
async def get_debts(u=Depends(get_current_user)): return PERSONAL_DEBTS
@router.post("/debts")
async def create_debt(d:dict,u=Depends(get_current_user)):
    deb={"id":f"pdebt-{uuid.uuid4().hex[:6]}","installments_paid":0,**d}; PERSONAL_DEBTS.append(deb); return deb
@router.delete("/debts/{did}")
async def del_debt(did:str,u=Depends(get_current_user)):
    global PERSONAL_DEBTS
    PERSONAL_DEBTS[:]=[x for x in PERSONAL_DEBTS if x["id"]!=did]; return {"success":True}

@router.get("/subscriptions")
async def get_subs(u=Depends(get_current_user)): return PERSONAL_SUBSCRIPTIONS
@router.post("/subscriptions")
async def create_sub(d:dict,u=Depends(get_current_user)):
    s={"id":f"psub-{uuid.uuid4().hex[:6]}","is_active":True,**d}; PERSONAL_SUBSCRIPTIONS.append(s); return s
@router.delete("/subscriptions/{sid}")
async def del_sub(sid:str,u=Depends(get_current_user)):
    global PERSONAL_SUBSCRIPTIONS
    PERSONAL_SUBSCRIPTIONS[:]=[x for x in PERSONAL_SUBSCRIPTIONS if x["id"]!=sid]; return {"success":True}

@router.get("/splits")
async def get_splits(u=Depends(get_current_user)): return PERSONAL_SPLITS
@router.post("/splits")
async def create_split(d:dict,u=Depends(get_current_user)):
    sp={"id":f"psplit-{uuid.uuid4().hex[:6]}",**d}; PERSONAL_SPLITS.append(sp); return sp
@router.delete("/splits/{spid}")
async def del_split(spid:str,u=Depends(get_current_user)):
    global PERSONAL_SPLITS
    PERSONAL_SPLITS[:]=[x for x in PERSONAL_SPLITS if x["id"]!=spid]; return {"success":True}

@router.get("/analytics")
async def get_analytics(u=Depends(get_current_user)):
    total_by_cat: dict = {}
    for e in PERSONAL_ENTRIES:
        if e["type"] == "DESPESA":
            total_by_cat[e["category"]] = total_by_cat.get(e["category"], 0) + e["amount"]
    net_worth_series = [{"month": m, "value": 8000 + i * 650} for i, m in enumerate(["Mar","Abr","Mai","Jun","Jul","Ago"])]
    return {"spend_by_category": [{"category": k, "total": round(v, 2)} for k, v in total_by_cat.items()], "net_worth_series": net_worth_series}

@router.post("/ai/insights")
async def personal_ai_insights(d:dict,u=Depends(get_current_user)):
    return {"insights": [
        {"type": "ALERT", "message": "Seus gastos com Lazer estão em 97% do orçamento mensal.", "impact_value": 390.00},
        {"type": "OPPORTUNITY", "message": "Você poderia render R$ 42/mês a mais movendo sua reserva para um CDB de liquidez diária.", "impact_value": 42.00},
        {"type": "CUT", "message": "Você tem 2 assinaturas ativas (Netflix, Academia) somando R$ 139,80/mês.", "impact_value": 139.80},
    ]}
```

- [ ] **Step 2: Verificar manualmente**

Reiniciar o backend e acessar `http://localhost:8000/docs` (Swagger, já habilitado pelo FastAPI) — confirmar que as novas rotas `/api/v1/personal/accounts`, `/budgets`, `/goals`, `/debts`, `/subscriptions`, `/splits`, `/analytics`, `/ai/insights` aparecem e retornam 200 com um token válido.

---

### Task 12: Página `HubPessoal.tsx` — esqueleto + Visão Geral + Extrato

**Files:**
- Create: `frontend/src/pages/HubPessoal.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `GET /personal/dashboard` → `{saldo, receitas_mes, despesas_mes, recent_entries}`; `GET/POST/DELETE /personal/entries`; `GET /personal/categories`.

- [ ] **Step 1: Criar o esqueleto da página com navegação por abas**

Criar `frontend/src/pages/HubPessoal.tsx` com um array de abas (usadas também pelas próximas 5 tasks, que só adicionam o `case` correspondente):

```tsx
const TABS = [
  { id: 'visao-geral', label: 'Visão Geral', icon: 'dashboard' },
  { id: 'extrato', label: 'Extrato', icon: 'receipt_long' },
  { id: 'contas-cartoes', label: 'Contas & Cartões', icon: 'credit_card' },
  { id: 'orcamento', label: 'Orçamento', icon: 'pie_chart' },
  { id: 'metas', label: 'Metas', icon: 'flag' },
  { id: 'dividas', label: 'Dívidas', icon: 'account_balance' },
  { id: 'assinaturas', label: 'Assinaturas', icon: 'subscriptions' },
  { id: 'divisao', label: 'Divisão de Despesas', icon: 'groups' },
  { id: 'analitico', label: 'Analítico', icon: 'analytics' },
  { id: 'timeboxes-okrs', label: 'Timeboxes & OKRs', icon: 'schedule' },
  { id: 'cfo-pessoal', label: 'CFO Pessoal IA', icon: 'auto_awesome' },
] as const;
```

Layout: barra de abas horizontal com scroll (`overflow-x-auto`, mesmo padrão de pill usado nas outras páginas), estado `activeTab`, e um `switch (activeTab)` que renderiza o conteúdo de cada aba — nesta task, implementar apenas `'visao-geral'` e `'extrato'`; as demais abas renderizam um placeholder simples (`<p>Em breve</p>`) até serem implementadas nas Tasks 13–17 (isso é temporário e esperado — cada task subsequente troca o placeholder pelo conteúdo real).

- **Aba "Visão Geral"**: 3 KPI cards (`glass-card`, mesmo padrão do `Dashboard.tsx`) — Saldo, Receitas do Mês, Despesas do Mês, vindos de `GET /personal/dashboard`; lista dos 5 lançamentos mais recentes (`recent_entries`) abaixo.
- **Aba "Extrato"**: tabela de `PERSONAL_ENTRIES` (via `GET /personal/entries`) com colunas Descrição, Categoria, Data, Tipo, Valor; botão "Novo Lançamento" abre modal com `type` (RECEITA/DESPESA), `amount`, `description`, `category` (select populado por `GET /personal/categories`) — `POST /personal/entries`; botão excluir por linha chama `DELETE /personal/entries/{id}` com `confirm()`.

- [ ] **Step 2: Registrar a rota**

Em `frontend/src/App.tsx`: `import HubPessoal from './pages/HubPessoal';` e:

```tsx
        <Route path="/pessoal" element={<PrivateRoute><HubPessoal /></PrivateRoute>} />
```

- [ ] **Step 3: Verificar manualmente no navegador**

Login (qualquer usuário) → "Hub Pessoal" → confirmar que "Visão Geral" mostra saldo/receitas/despesas coerentes com os 4 lançamentos mock (`PERSONAL_ENTRIES` em `database.py`); na aba "Extrato", criar um novo lançamento e confirmar que aparece na lista e que o saldo da Visão Geral atualiza ao voltar para essa aba.

---

### Task 13: Abas "Contas & Cartões" e "Orçamento por Categoria"

**Files:**
- Modify: `frontend/src/pages/HubPessoal.tsx`

**Interfaces:**
- Consumes: `GET/POST/DELETE /personal/accounts`, `GET/POST/DELETE /personal/budgets` (Task 11).

- [ ] **Step 1: Implementar "Contas & Cartões"**

Substituir o placeholder da aba `'contas-cartoes'`: grid de cartões (`glass-card`) — um por item de `GET /personal/accounts`. Para `type === 'CONTA'`: mostrar `name` e `balance` formatado; para `type === 'CARTAO'`: mostrar `name`, `balance` (fatura atual, negativo = a pagar), `limit`, barra de uso (`Math.abs(balance)/limit`), `closing_day`/`due_day`. Botão "Nova Conta/Cartão" abre modal com `name`, `type` (select CONTA/CARTAO), `balance`, e campos condicionais `limit`/`closing_day`/`due_day` quando `type === 'CARTAO'` — `POST /personal/accounts`. Botão de remover por cartão chama `DELETE /personal/accounts/{id}`.

- [ ] **Step 2: Implementar "Orçamento por Categoria"**

Substituir o placeholder da aba `'orcamento'`: lista de barras de progresso (mesmo padrão visual de "Categorias de Despesas" do `Dashboard.tsx`) — uma por item de `GET /personal/budgets`, mostrando `category`, `spent_amount`/`limit_amount`, barra colorida (`bg-success` se `< 80%`, `bg-warning` se `80–99%`, `bg-error` se `>= 100%`). Botão "Novo Orçamento" abre modal com `category` (texto) e `limit_amount` — `POST /personal/budgets`. Botão de remover por item chama `DELETE /personal/budgets/{id}`.

- [ ] **Step 3: Verificar manualmente no navegador**

Aba "Contas & Cartões": confirmar que a Conta Corrente e o Cartão mock aparecem com os valores corretos; criar uma conta nova. Aba "Orçamento": confirmar que Alimentação (650/1200, verde), Transporte (410/500, amarelo — 82%) e Lazer (390/400, amarelo — 97,5%) aparecem com as cores certas; criar um orçamento novo.

---

### Task 14: Abas "Metas Financeiras" e "Dívidas & Parcelamentos"

**Files:**
- Modify: `frontend/src/pages/HubPessoal.tsx`

**Interfaces:**
- Consumes: `GET/POST/DELETE /personal/goals`, `POST /personal/goals/{id}/contribute`, `GET/POST/DELETE /personal/debts` (Task 11).

- [ ] **Step 1: Implementar "Metas Financeiras"**

Substituir o placeholder da aba `'metas'`: grid de cards — um por item de `GET /personal/goals`, mostrando `name`, barra de progresso (`current_amount/target_amount`), `target_date`, botão "Adicionar Aporte" que abre um mini-form inline (input de valor + botão confirmar) chamando `POST /personal/goals/{id}/contribute` com `{amount}`. Botão "Nova Meta" abre modal com `name`, `target_amount`, `target_date` — `POST /personal/goals`. Botão remover chama `DELETE /personal/goals/{id}`.

- [ ] **Step 2: Implementar "Dívidas & Parcelamentos"**

Substituir o placeholder da aba `'dividas'`: tabela/cards — um por item de `GET /personal/debts`, mostrando `name`, `remaining_amount`/`total_amount`, `installments_paid`/`installments_total`, `interest_rate`, barra de progresso de quitação. Botão "Nova Dívida" abre modal com `name`, `total_amount`, `remaining_amount`, `installments_total`, `interest_rate` — `POST /personal/debts`. Botão remover (quitação total) chama `DELETE /personal/debts/{id}`.

- [ ] **Step 3: Verificar manualmente no navegador**

Aba "Metas": confirmar "Reserva de Emergência" (8500/20000) e "Viagem Europa" (3200/12000); adicionar um aporte de R$500 na reserva e confirmar que o valor atualiza. Aba "Dívidas": confirmar "Financiamento Notebook" (2400/4800, 6/12 parcelas); criar uma dívida nova.

---

### Task 15: Abas "Assinaturas Recorrentes" e "Divisão de Despesas"

**Files:**
- Modify: `frontend/src/pages/HubPessoal.tsx`

**Interfaces:**
- Consumes: `GET/POST/DELETE /personal/subscriptions`, `GET/POST/DELETE /personal/splits` (Task 11).

- [ ] **Step 1: Implementar "Assinaturas Recorrentes"**

Substituir o placeholder da aba `'assinaturas'`: lista — um item por `GET /personal/subscriptions`, mostrando `name`, `amount`, "Cobra todo dia {billing_day}", `category`, badge Ativo/Inativo. Total mensal somado no topo. Botão "Nova Assinatura" abre modal com `name`, `amount`, `billing_day`, `category` — `POST /personal/subscriptions`. Botão remover chama `DELETE /personal/subscriptions/{id}`.

- [ ] **Step 2: Implementar "Divisão de Despesas"**

Substituir o placeholder da aba `'divisao'`: card por item de `GET /personal/splits`, mostrando `description`, `total_amount`, e lista de `participants` (nome, `share`, badge Pago/Pendente). Botão "Nova Divisão" abre modal com `description`, `total_amount`, e uma lista dinâmica de participantes (nome + valor, com botão "+ Adicionar Participante") — `POST /personal/splits` com `{description, total_amount, participants: [{name, share, paid: false}, ...]}`. Botão remover chama `DELETE /personal/splits/{id}`.

- [ ] **Step 3: Verificar manualmente no navegador**

Aba "Assinaturas": confirmar Netflix (R$39,90) e Academia (R$99,90), total R$139,80/mês; criar uma assinatura nova. Aba "Divisão de Despesas": confirmar "Aluguel República" com 3 participantes (Você, João, Maria); criar uma divisão nova com 2 participantes.

---

### Task 16: Aba "Dashboard Analítico Pessoal" e "Timeboxes & OKRs"

**Files:**
- Modify: `frontend/src/pages/HubPessoal.tsx`

**Interfaces:**
- Consumes: `GET /personal/analytics` (Task 11); `GET/POST /personal/timeboxes`, `GET/POST /personal/okrs`.

- [ ] **Step 1: Implementar "Analítico"**

Substituir o placeholder da aba `'analitico'`: `GET /personal/analytics` retorna `{spend_by_category, net_worth_series}`. Renderizar um `BarChart` ou `AreaChart` do Recharts para `net_worth_series` (eixo X `month`, área/barra `value`) seguindo o mesmo padrão de cores/gradiente de `Dashboard.tsx`; abaixo, lista de barras de proporção para `spend_by_category` (mesmo padrão visual de "Categorias de Despesas").

- [ ] **Step 2: Implementar "Timeboxes & OKRs"**

Substituir o placeholder da aba `'timeboxes-okrs'`: duas seções lado a lado. **Timeboxes**: lista de `GET /personal/timeboxes` (array vazio no mock — a lista aparece vazia até o usuário criar), botão "Novo Timebox" com modal (`title`, `start_time`, `end_time`) — `POST /personal/timeboxes`. **OKRs**: lista de `GET /personal/okrs` (também vazio no mock), botão "Novo OKR" com modal (`objective`, e até 5 `key_results` como inputs de texto dinâmicos) — `POST /personal/okrs`, exibindo cada OKR criado com uma barra de progresso placeholder em 0%.

- [ ] **Step 3: Verificar manualmente no navegador**

Aba "Analítico": confirmar que o gráfico de evolução patrimonial renderiza (6 meses) e a lista de gastos por categoria bate com os dados do Extrato. Aba "Timeboxes & OKRs": criar um timebox e um OKR, confirmar que ambos aparecem nas respectivas listas.

---

### Task 17: Aba "CFO Pessoal IA"

**Files:**
- Modify: `frontend/src/pages/HubPessoal.tsx`

**Interfaces:**
- Consumes: `POST /personal/ai/insights` (Task 11).

- [ ] **Step 1: Implementar a aba**

Substituir o placeholder da aba `'cfo-pessoal'`: botão "Gerar Análise" que chama `POST /personal/ai/insights` (body `{}`) e exibe os `insights` retornados como cards (mesmo estilo visual do widget "AI Virtual CFO" do `Dashboard.tsx`: ícone `psychology`, borda `border-primary/20`, classe `ai-aura`), um por insight, com badge de tipo (`ALERT` vermelho, `OPPORTUNITY` verde, `CUT` amarelo) e `impact_value` formatado em R$. Estado de loading enquanto a chamada não retorna (spinner igual ao padrão já usado nas outras páginas).

- [ ] **Step 2: Verificar manualmente no navegador**

Aba "CFO Pessoal IA": clicar em "Gerar Análise" e confirmar que os 3 insights mock aparecem (alerta de orçamento de Lazer, oportunidade de CDB, corte de assinaturas) com as cores certas por tipo.

---

## Fase 7 — M4 Notificações

### Task 18: Sino de notificações no `Layout.tsx`

**Files:**
- Modify: `frontend/src/components/Layout.tsx`

**Interfaces:**
- Consumes: `GET /notifications/unread-count` → `{count}`; `GET /notifications/?unread_only=` → `{items, total, unread_count}`; `POST /notifications/{id}/read`; `POST /notifications/read-all`.

- [ ] **Step 1: Buscar contagem de não lidas e montar o painel**

Em `frontend/src/components/Layout.tsx`, adicionar estados: `const [unreadCount, setUnreadCount] = useState(0);`, `const [isNotifPanelOpen, setIsNotifPanelOpen] = useState(false);`, `const [notifications, setNotifications] = useState<any[]>([]);`

Adicionar `useEffect` que busca `GET /notifications/unread-count` ao montar o componente e popula `unreadCount`.

Adicionar função:

```tsx
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
    await api.post(`/notifications/${id}/read`);
    setNotifications(notifications.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    setUnreadCount(Math.max(0, unreadCount - 1));
  };

  const handleMarkAllRead = async () => {
    await api.post('/notifications/read-all');
    setNotifications(notifications.map((n) => ({ ...n, is_read: true })));
    setUnreadCount(0);
  };
```

(Adicionar `import api from '../api';` no topo do arquivo — hoje `Layout.tsx` não importa `api`.)

- [ ] **Step 2: Adicionar o ícone de sino com badge no header desktop e mobile**

No header desktop (dentro da `<div className="flex items-center gap-md">` que já contém o botão "CFO Virtual IA", por volta da linha 133), adicionar antes do botão de CFO:

```tsx
          <button onClick={openNotifPanel} className="relative p-2 rounded-full hover:bg-surface-bright transition-colors text-on-surface-variant hover:text-on-surface">
            <span className="material-symbols-outlined">notifications</span>
            {unreadCount > 0 && (
              <span className="absolute top-0 right-0 w-4 h-4 bg-error text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>
```

No header mobile (dentro do bloco `lg:hidden fixed top-0`, ao lado do botão de chat, por volta da linha 51–58), adicionar o mesmo botão com estilo compacto equivalente.

- [ ] **Step 3: Painel dropdown de notificações**

Adicionar um bloco `<AnimatePresence>` (após o `<AICfoDrawer>` no fim do componente) que renderiza um painel ancorado no canto superior direito quando `isNotifPanelOpen` é `true` (`className="fixed top-16 right-lg w-96 max-h-[70vh] overflow-y-auto glass-card rounded-xl z-[90]"`), cabeçalho "Notificações" com botão "Marcar todas como lidas" (`handleMarkAllRead`) e botão fechar, lista de `notifications` (título, mensagem, badge de tipo `WARNING`/`SUCCESS`/`INFO` com cor correspondente, ponto indicador se `!is_read`, `onClick` no item chama `handleMarkRead(n.id)`).

- [ ] **Step 4: Verificar manualmente no navegador**

Login → confirmar que o sino mostra o badge com a contagem de não lidas (2, conforme o mock em `NOTIFICATIONS`); clicar no sino, ver o painel abrir com as 4 notificações; clicar em uma não lida e confirmar que o badge diminui; clicar em "Marcar todas como lidas" e confirmar que o badge some.

---

## Fase 8 — M7 Exportação e Relatórios

### Task 19: Página `Exportacao.tsx`

**Files:**
- Create: `frontend/src/pages/Exportacao.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Endpoints já existentes em `app/api/v1/endpoints/exports.py`: `GET /exports/logs` → lista de `{id, type, format, status, created_at, size_bytes}`; `POST /exports/request` (body: `{type, format}`) → novo log; `GET /exports/download/{id}` → `{download_url, expires_in}`.

- [ ] **Step 1: Criar a página**

Criar `frontend/src/pages/Exportacao.tsx`: grid de cards, um por tipo de relatório (`DRE`, `Fluxo de Caixa`, `Colaboradores`, `Fornecedores`, `Cost-per-Task`), cada card com 3 botões de formato (CSV, XLSX, PDF) que chamam `api.post('/exports/request', { type: <tipo>, format: <formato> })` e, ao retornar, adicionam o item ao topo de uma segunda seção "Histórico de Exportações" (tabela com `type`, `format`, `status`, `created_at`, `size_bytes` formatado em KB, botão "Baixar" que chama `GET /exports/download/{id}` e faz `window.open(res.data.download_url)`). Buscar o histórico inicial com `GET /exports/logs` no `useEffect`.

- [ ] **Step 2: Registrar a rota**

Em `frontend/src/App.tsx`: `import Exportacao from './pages/Exportacao';` e:

```tsx
        <Route path="/exportacao" element={<PrivateRoute><Exportacao /></PrivateRoute>} />
```

- [ ] **Step 3: Verificar manualmente no navegador**

Login como gerente → "Exportação" → confirmar que o histórico mostra os 2 registros mock (`EXPORT_LOGS`); clicar em "PDF" no card do DRE e confirmar que um novo item "PROCESSANDO" aparece no topo do histórico; clicar em "Baixar" em qualquer item.

---

## Fase 9 — M8-IA completo (empresarial)

### Task 20: Página `IAEmpresarial.tsx`

**Files:**
- Create: `frontend/src/pages/IAEmpresarial.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Endpoints já existentes em `app/api/v1/endpoints/ai.py`:
  - `POST /ai/consultant/cfo` → `{insights:[{type:"OPORTUNIDADE"|"ALERTA", title, description, impact, urgency}]}`
  - `POST /ai/consultant/conciliation` (body: `{description}`) → `{results:[{description, suggested_category, confidence, status}]}`
  - `POST /ai/consultant/proposal` (body livre) → `{estimated_internal_cost, suggested_price, margin_percentage}`

- [ ] **Step 1: Criar a página com 3 abas**

Criar `frontend/src/pages/IAEmpresarial.tsx`:

- **Aba "CFO Virtual"**: botão "Gerar Análise" → `POST /ai/consultant/cfo` → renderiza os `insights` como cards (badge `OPORTUNIDADE` verde / `ALERTA` vermelho, `title`, `description`, `impact`, `urgency`) — mesmo estilo visual do widget de IA do `Dashboard.tsx`.
- **Aba "Conciliação Bancária"**: input de arquivo (`<input type="file" accept=".csv,.ofx">`) — como o mock não processa arquivo de verdade, ao selecionar um arquivo simular 3 linhas fixas de transação (`["Uber - transporte", "Amazon AWS", "Assinatura Spotify"]`) e, para cada uma, chamar `POST /ai/consultant/conciliation` com `{description}`; exibir os resultados numa tabela com colunas Descrição, Categoria Sugerida, Confiança (badge — vermelho se `confidence < 0.6`, verde caso contrário), Ações (botões "Aprovar"/"Rejeitar" que só alteram um estado local `status` da linha, sem persistir — é mock).
- **Aba "Gerador de Orçamentos"**: formulário com `briefing` (textarea) e `markup` (input numérico, %) → `POST /ai/consultant/proposal` → exibe `estimated_internal_cost`, `suggested_price`, `margin_percentage` em 3 KPI cards.

- [ ] **Step 2: Registrar a rota**

Em `frontend/src/App.tsx`: `import IAEmpresarial from './pages/IAEmpresarial';` e:

```tsx
        <Route path="/ia" element={<PrivateRoute><IAEmpresarial /></PrivateRoute>} />
```

- [ ] **Step 3: Verificar manualmente no navegador**

Login como gerente → "IA Empresarial" → aba CFO Virtual: gerar análise e confirmar os 2 insights mock. Aba Conciliação: selecionar um arquivo fake e confirmar que as 3 transações simuladas aparecem com sugestão de categoria e confiança. Aba Orçamentos: preencher briefing e markup, gerar, confirmar que os 3 valores aparecem.

---

## Fase 10 — Ajustes finais

### Task 21: Atualizar `Register.tsx` e `Plans.tsx` para os 3 planos por escopo

**Files:**
- Modify: `frontend/src/pages/Register.tsx`
- Modify: `frontend/src/pages/Plans.tsx` (nenhuma mudança de código é estritamente necessária aqui, pois já busca `GET /plans/` dinamicamente — apenas verificar visualmente)

**Interfaces:**
- Consumes: `GET /plans/` já retorna os 3 planos redesenhados pela Task 1.

- [ ] **Step 1: Trocar os 3 cards fixos de plano no passo 2 do cadastro**

Em `frontend/src/pages/Register.tsx`, o passo 2 (linhas 173–224) tem 3 blocos `<div onClick={() => setSelectedPlan(...)}>` hardcoded para `plan-starter`/`plan-pro`/`plan-enterprise`. Substituir por um `.map` sobre os planos buscados de `GET /plans/` (adicionar `useEffect` que busca a lista ao montar o componente e guarda em um novo estado `const [plans, setPlans] = useState<any[]>([]);`), mantendo o mesmo estilo visual de card (borda azul quando `selectedPlan === plan.id`), mas usando `plan.name`, `plan.tagline`, `plan.price_monthly` dinamicamente. Atualizar `selectedPlan` inicial para `'plan-empresarial'` (linha 14).

- [ ] **Step 2: Verificar manualmente no navegador**

Acessar `/cadastro`, preencher o passo 1, avançar para o passo 2 e confirmar que aparecem os 3 planos "Pessoal" (R$19,90), "Empresarial" (R$249,00) e "Completo" (R$279,00) com as features corretas; selecionar "Pessoal", completar o cadastro e, após redirecionado (checkout/login), confirmar que o usuário criado só vê "Hub Pessoal" no menu (gating da Task 3). Repetir rapidamente selecionando "Completo" e confirmar que todos os módulos aparecem.

---

### Task 22: Passagem final de QA manual

**Files:** nenhum arquivo novo — apenas verificação.

- [ ] **Step 1: Percorrer o sistema com os 3 usuários de teste**

Com backend e frontend rodando, usando o navegador:
- Login `admin@techconnect.com.br` / `Admin@123`: percorrer todas as rotas novas (`/configuracoes`, `/fornecedores`, `/financeiro`, `/pessoal`, `/exportacao`, `/ia`), confirmar zero erros no console (console do navegador, filtrando só erros).
- Login `gerente@techconnect.com.br` / `Gerente@123`: confirmar que "Configurações" não aparece no menu (só Admin), mas o restante sim.
- Login `funcionario@techconnect.com.br` / `Func@123`: confirmar que "Equipe", "Financeiro", "Fornecedores", "Configurações", "Exportação", "IA Empresarial" não aparecem no menu (papel `FUNCIONARIO`), mas "Dashboard", "Projetos", "Hub Pessoal" sim.

- [ ] **Step 2: Registrar quaisquer bugs encontrados e corrigir inline**

Se algum fluxo quebrar (erro 404/500 no console, tela em branco, dado não carregando), corrigir o arquivo correspondente antes de encerrar esta fase — não deixar para depois.
