# TechConnect v2.0 — Expansão completa do frontend (fase 1: visual/funcional)

Data: 2026-08-11
Status: aprovado pelo usuário, pronto para plano de execução

## Contexto

A Declaração de Escopo v2.0.1 e a ERS v2.0.1 descrevem 10 módulos (Auth, M0–M8-IA) como
"Implementado", mas o código real cobre apenas uma fração disso no frontend (Login, Register,
Plans, Checkout, Subscription, Dashboard, Kanban, GestaoEquipe) e o backend é inteiramente
mock (FastAPI + listas Python em memória, sem MySQL real). Esta fase fecha a lacuna do lado
visual/funcional do frontend, consumindo os endpoints mock já existentes (e um pequeno conjunto
de endpoints mock novos, no mesmo estilo, para os submódulos financeiros pessoais). A
persistência real em MySQL fica para uma fase seguinte, fora do escopo deste documento.

Durante a conversa, o usuário revelou uma intenção original que não está na documentação
formal: o sistema deveria oferecer dois tipos de conta — **pessoal** e **empresarial** — mais um
plano que cobre as duas, com o Hub Pessoal (M0) expandido para cobrir gestão financeira de
pessoa física de forma completa. Esta decisão de produto está registrada aqui e precisará ser
retroalimentada na Declaração de Escopo/ERS numa fase de atualização de documentação
(fora do escopo desta implementação).

## Decisões de design

### 1. Modelo de conta/plano — Opção A (aprovada)

Conta única de login. O **plano contratado** (`Pessoal`, `Empresarial`, `Completo`) determina
quais módulos aparecem no menu — não há dois fluxos de cadastro distintos nesta fase.

- `PLANS_DB` (`app/api/v1/endpoints/plans.py`) passa a ter 3 planos com campo `scope`:
  `"pessoal" | "empresarial" | "completo"`, substituindo a semântica atual (Starter/Pro/Enterprise
  focados só em métricas empresariais). Preços e features são simplificados para refletir o
  escopo, mantendo o texto voltado a PMEs no plano Empresarial/Completo.
- O objeto `user` (retornado por `/auth/login` e `/auth/register`, guardado em
  `localStorage.user`) passa a incluir `plan_scope` (herdado do plano assinado). Como o backend
  ainda é mock, `register`/`login` simplesmente propagam esse campo a partir do plano
  selecionado/assinado — sem lógica de cobrança real.
- `Layout.tsx` lê `user.plan_scope` e filtra os itens de navegação:
  - `pessoal` → mostra só Hub Pessoal (e seus submódulos) + Assinatura/Planos.
  - `empresarial` → mostra Dashboard, Kanban, Equipe, Financeiro, Fornecedores,
    Configurações, Exportação, IA Empresarial + Assinatura/Planos (sem Hub Pessoal).
  - `completo` → mostra tudo.
  - Ausência de `plan_scope` (contas antigas/mock atuais) tratada como `completo`, para não
    quebrar os usuários de teste existentes (admin/gerente/funcionário do README).

### 2. Hub Pessoal (M0) expandido

Além do que a ERS já descreve (receitas/despesas pessoais, categorias, timeboxes, OKRs),
entram 8 submódulos, todos aprovados pelo usuário:

Essenciais: Contas & Cartões, Orçamento por Categoria, Metas Financeiras, Dashboard
Analítico Pessoal.
Diferenciais: Dívidas & Parcelamentos, Assinaturas Recorrentes, CFO Pessoal IA, Divisão de
Despesas.

Nenhum desses tem endpoint hoje. Serão adicionados ao `app/api/v1/endpoints/personal.py`
seguindo exatamente o estilo já usado ali (listas Python em memória + rotas CRUD simples) —
é scaffolding mock leve para o frontend ter o que consumir, **não** é a implementação de
persistência real (essa fica para a fase de banco de dados, à noite).

## Arquitetura de rotas e navegação

`App.tsx` ganha as rotas abaixo, todas em `PrivateRoute`. Restrição por papel (`ADMIN`,
`GERENTE`, `FUNCIONARIO`) mantém-se como já existe hoje; restrição por `plan_scope` é uma
camada adicional puramente de exibição no menu (a rota em si não bloqueia navegação direta
nesta fase — isso é aceitável para um mock de demonstração).

| Rota | Módulo | Papéis | Plan scope |
|---|---|---|---|
| `/configuracoes` | M5 Configurações da Empresa | ADMIN | empresarial, completo |
| `/fornecedores` | M6 Fornecedores | ADMIN, GERENTE | empresarial, completo |
| `/financeiro` | M2 Financeiro Empresarial | ADMIN, GERENTE | empresarial, completo |
| `/pessoal` | M0 Hub Pessoal (com sub-abas) | todos | pessoal, completo |
| `/notificacoes` | M4 (painel, não precisa de rota própria — ver abaixo) | todos | todos |
| `/exportacao` | M7 Exportação e Relatórios | ADMIN, GERENTE | empresarial, completo |
| `/ia` | M8-IA completo (empresarial) | ADMIN, GERENTE | empresarial, completo |

M4 (Notificações) não vira página dedicada — é um painel/dropdown ancorado no sino do
`Layout.tsx`, disponível em qualquer tela, para todos os papéis e planos.

## Módulos — detalhamento

Ordem de construção (dependência de dados, conforme aprovado):

### 1. M5 — Configurações da Empresa (`/configuracoes`)
Página com abas: Dados da Empresa (form), Plano de Contas, Centros de Custo, Calendário
Útil. Endpoints existentes: `GET/PUT /company/`, `GET/POST /company/categories`,
`GET/POST/DELETE /company/cost-centers`, `GET/PUT /company/calendar`.

### 2. M6 — Fornecedores (`/fornecedores`)
CRUD lista/cartão no mesmo padrão de `GestaoEquipe.tsx` (toggle list/card, modal de
criar/editar). Campos: nome, CNPJ/CPF, categoria, e-mail, ativo/inativo. Endpoints existentes:
`GET/POST/PUT/DELETE /suppliers`.

### 3. M3 — Colaboradores e CTC (completar `GestaoEquipe.tsx`)
Adiciona: badge de custo/hora no card e na linha da tabela; modal "Histórico Salarial"
(`GET /employees/{id}/salary-history`); ação "Desligar" substituindo o delete físico
(`POST /employees/{id}/terminate`); filtro por tipo de contrato.

### 4. M2 — Financeiro Empresarial (`/financeiro`, página nova)
Abas: Lançamentos (tabela com filtros, modal novo lançamento receita/despesa, marcar como
pago), DRE (dado real de `GET /financial/dre`, com breakdown por categoria), Fluxo de Caixa
D+90 (gráfico de `GET /financial/cashflow`, banner de alerta verde/amarelo/vermelho). A tabela
"Transações Recentes" hardcoded do `Dashboard.tsx` passa a puxar de `GET /financial/entries`
em vez de JSX estático.

### 5. M1 — Kanban Operacional (completar `Kanban.tsx`)
Adiciona: seletor/CRUD de Cliente; modal "Novo Projeto" funcional (`POST /kanban/projects`);
botão iniciar/parar timer no card (`POST /kanban/cards/{id}/timer/start|stop`); painel lateral de
detalhe do card com comentários (`POST /kanban/cards/{id}/comments`).

### 6. M0 — Hub Pessoal expandido (`/pessoal`, página nova)
Página com abas/seções:
- **Visão Geral**: saldo, receitas/despesas do mês (`GET /personal/dashboard`).
- **Extrato**: CRUD de lançamentos + categorias (`GET/POST/DELETE /personal/entries`,
  `GET /personal/categories`).
- **Contas & Cartões** *(novo)*: lista de contas/carteiras e cartões com limite/fatura.
- **Orçamento por Categoria** *(novo)*: limite mensal por categoria, barra de progresso, alerta
  de estouro.
- **Metas Financeiras** *(novo)*: metas com valor alvo, aportes, progresso.
- **Dívidas & Parcelamentos** *(novo)*: empréstimos/financiamentos, parcelas, juros, quitação.
- **Assinaturas Recorrentes** *(novo)*: serviços recorrentes com alerta de renovação.
- **Divisão de Despesas** *(novo)*: despesas compartilhadas com terceiros, split e saldo entre
  participantes.
- **Dashboard Analítico Pessoal** *(novo)*: gráficos de evolução patrimonial e gasto por
  categoria (Recharts, reaproveitando o padrão do Dashboard empresarial).
- **Timeboxes** e **OKRs**: lista + criação simples (`GET/POST /personal/timeboxes`,
  `GET/POST /personal/okrs`).
- **CFO Pessoal IA** *(novo)*: reaproveita o padrão do `AICfoDrawer`/M8-IA, mas com prompt e
  endpoint próprios voltados a finanças pessoais.

Novos endpoints mock a adicionar em `personal.py` (mesmo estilo do arquivo):
`GET/POST/DELETE /personal/accounts`, `GET/POST/DELETE /personal/budgets`,
`GET/POST/DELETE /personal/goals`, `POST /personal/goals/{id}/contribute`,
`GET/POST/DELETE /personal/debts`, `GET/POST/DELETE /personal/subscriptions`,
`GET/POST/DELETE /personal/splits`, `GET /personal/analytics`,
`POST /personal/ai/insights` (CFO Pessoal IA — mesma lógica mock de `ai.py`, adaptada).

### 7. M4 — Notificações (painel no `Layout.tsx`)
Sino com badge de não lidas (`GET /notifications/unread-count`), dropdown com lista
(`GET /notifications/?unread_only=`), marcar como lida/todas
(`POST /notifications/{id}/read`, `POST /notifications/read-all`), preferências simples
(`GET/PUT /notifications/preferences`).

### 8. M7 — Exportação e Relatórios (`/exportacao`, página nova)
Cards por tipo de relatório (DRE, Fluxo de Caixa, Colaboradores, Fornecedores, Cost-per-Task)
com botões CSV/XLSX/PDF (`POST /exports/request`), histórico de exportações
(`GET /exports/logs`), download mock (`GET /exports/download/{id}`).

### 9. M8-IA completo — Empresarial (`/ia`, página nova)
3 abas: **CFO Virtual** (botão gerar análise → `POST /ai/consultant/cfo` → lista de insights
ALERT/OPPORTUNITY/CUT com impacto); **Conciliação Bancária** (upload CSV/OFX mock →
`POST /ai/consultant/conciliation` → tabela de sugestões com badge de confidence score,
aprovar/rejeitar por linha); **Gerador de Orçamentos** (form briefing + markup →
`POST /ai/consultant/proposal` → WBS, custo interno, preço sugerido). O `AICfoDrawer` (chat
flutuante) continua existindo como atalho rápido, sem mudanças.

## Fora de escopo nesta fase

- Persistência real em MySQL/SQLAlchemy (fase seguinte, "banco de dados").
- RBAC realmente aplicado no backend, 2FA/TOTP, chamadas reais à API Gemini, tabelas de
  auditoria append-only, LGPD — já mapeados na análise anterior, ficam para depois.
- Correção da exposição de credenciais no `docker-compose.yml` — pendente, tratar à parte.
- Atualização formal da Declaração de Escopo/ERS refletindo o modelo de conta/plano e o Hub
  Pessoal expandido — fazer depois que o comportamento estiver validado na tela.

## Verificação

Após implementar cada bloco (ordem acima), subir o frontend (`npm run dev`, já configurado) e
percorrer manualmente as telas novas no navegador integrado, conferindo: chamada de API sem
erro no console, estados de loading/vazio, CRUD completo (criar/editar/excluir) refletindo na UI,
e navegação/gating condizente com o `plan_scope` do usuário logado.
