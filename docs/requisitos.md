# Especificação de Requisitos do Sistema — TechConnect 2.0

Este documento formaliza os requisitos do TechConnect 2.0, desenvolvido como solução do Projeto Integrador (PI) do curso de Tecnologia em Análise e Desenvolvimento de Sistemas (ADS) — CEUB.

---

## 1. Visão do produto

O TechConnect 2.0 junta a gestão operacional de projetos e equipes (Kanban com tempo e custo real por tarefa) com controle financeiro (DRE, projeção de fluxo de caixa D+90, cálculo de CTC) e um CFO Virtual demonstrativo baseado em regras. A integração com o Google Gemini permanece como requisito futuro. O público é PME, gestor e profissional autônomo. Além do Hub Empresarial, o sistema tem um Hub Pessoal que mantém finanças e metas isoladas pelo usuário autenticado, sem misturá-las com os fluxos da empresa.

---

## 2. Público-alvo

1. Gestores e donos de PMEs, que precisam de visão unificada do caixa, da rentabilidade por projeto e de dados para decidir.
2. Gerentes de operações e projetos, responsáveis pela alocação de equipe, prazos e custo por tarefa (*Cost-per-Task*).
3. Colaboradores e funcionários, que acompanham as próprias tarefas, cronometram atividades e veem suas métricas de execução.
4. Profissionais autônomos e empreendedores individuais, que alternam entre o controle do negócio e a própria gestão financeira.

---

## 3. Problema de negócio

Nas PMEs brasileiras, a operação do dia a dia e o controle financeiro costumam andar separados. Planilhas manuais ou sistemas legados fragmentados deixam pelo menos quatro lacunas:
- Ninguém sabe ao certo quanto custou uma entrega, um projeto ou um cliente.
- O custo real da equipe (CTC — salário, benefícios e encargos, CLT ou PJ) não é calculado de forma automática.
- Decisões financeiras chegam tarde, sem projeção de fluxo de caixa nem acompanhamento contínuo.
- As finanças pessoais do dono se misturam com as da empresa, por falta de uma ferramenta que separe os dois mundos na mesma interface.

---

## 4. Objetivos

### 4.1 Objetivo geral
Desenvolver uma plataforma web que una gestão operacional (Kanban com custo por tarefa), controle financeiro (DRE, projeção D+90, CTC), um módulo de IA voltado a diagnóstico financeiro e um módulo de finanças pessoais.

### 4.2 Objetivos específicos
- Kanban com cronômetro em tempo real, calculando o *Cost-per-Task* a partir do valor/hora do responsável.
- Cálculo automático de CTC (Custo Total ao Colaborador), com histórico salarial e motivo de cada alteração.
- DRE gerencial consolidado e projeção de fluxo de caixa para 90 dias (D+90).
- Módulo de IA baseado em Procedimentos Operacionais Padrão (POPs), para diagnósticos financeiros e sugestão de orçamentos.
- Hub Pessoal com extrato, metas, divisão de despesas (*Split*) e cartões.
- Arquitetura desacoplada, com frontend React, backend FastAPI e banco relacional, orquestrada via Docker.

---

## 5. Requisitos Funcionais (RF)

| Identificador | Nome do Requisito | Descrição Detalhada | Papéis com Acesso |
|---|---|---|---|
| **RF01** | Autenticação e RBAC | O sistema deve autenticar usuários via JSON Web Token (JWT), rejeitar usuários inativos e aplicar controle de acesso baseado em papéis (`ADMIN`, `GERENTE`, `FUNCIONARIO`), com bloqueio efetivo no servidor (HTTP 403). | Todos |
| **RF02** | Gestão de Planos e Escopo | O sistema deve suportar planos (`pessoal`, `empresarial`, `completo`), permitindo alternar de contexto entre Hub Empresarial e Hub Pessoal na barra de navegação sem deslogar. | Todos |
| **RF03** | Dashboard Executivo | O sistema deve exibir indicadores-chave (Receita, Despesas, Lucro Líquido, Margem Operacional), gráfico dinâmico de DRE e projeção de Fluxo de Caixa D+90. | Admin, Gerente |
| **RF04** | Quadro Kanban de Projetos | O sistema deve fornecer quadro Kanban com colunas personalizáveis, funcionalidade de arrastar e soltar (*Drag & Drop*), associação a clientes e priorização de cards. | Todos |
| **RF05** | Apontamento de Tempo e Cost-per-Task | O sistema deve disponibilizar cronômetro em cada card do Kanban e calcular automaticamente o custo acumulado da tarefa com base no valor da hora de trabalho do responsável. | Todos |
| **RF06** | Gestão de Clientes | O sistema deve permitir o cadastro, edição, consulta e segmentação de clientes com CNPJ, contato e projetos vinculados. | Admin, Gerente |
| **RF07** | Gestão de Equipe e CTC | O sistema deve calcular automaticamente o Custo Total ao Colaborador (CTC) a partir do regime de contratação (CLT/PJ), registrar histórico salarial com motivo e permitir o desligamento com inativação lógica. | Admin (CRUD), Gerente (Leitura) |
| **RF08** | Gestão de Fornecedores | O sistema deve gerenciar o cadastro de fornecedores com CNPJ/CPF, categoria de atuação e vínculo aos lançamentos financeiros, mantendo integridade com exclusão segura (`ON DELETE SET NULL`). | Admin, Gerente |
| **RF09** | Lançamentos Financeiros | O sistema deve permitir o registro de contas a pagar e receber, centros de custo, status de liquidação (Pendente/Pago/Atrasado) e categorias financeiras. | Admin, Gerente |
| **RF10** | Módulo de IA (CFO Virtual) | O sistema deve integrar rotinas de IA baseadas em POPs para analisar o DRE mensal, detectar tarefas que estouraram o orçamento e sugerir planos de ação econômicos em formato estruturado. | Admin, Gerente |
| **RF11** | Conciliação e Gerador de Orçamentos IA | O sistema deve sugerir orçamentos baseando-se no histórico de custos de tarefas semelhantes e apoiar na conciliação de lançamentos bancários. | Admin, Gerente |
| **RF12** | Exportação de Relatórios e Auditoria | O sistema deve permitir a exportação de dados e relatórios em formato CSV/PDF e registrar o log de todas as exportações efetuadas. | Admin, Gerente |
| **RF13** | Central de Notificações | O sistema deve emitir alertas sobre prazos de tarefas do Kanban, vencimento de contas e mensagens do sistema através de um painel de notificações no cabeçalho. | Todos |
| **RF14** | Hub Pessoal: Gestão Financeira | O sistema deve disponibilizar controle financeiro pessoal completo: Extrato, Contas & Cartões, Orçamento por Categoria, Metas Financeiras, Dívidas & Parcelamentos e Assinaturas Recorrentes. | Usuários com plano Pessoal ou Completo |
| **RF15** | Hub Pessoal: Divisão de Despesas e Produtividade | O sistema deve possibilitar a divisão de contas entre múltiplos participantes (*Split*) e o gerenciamento de metas pessoais via Timeboxes e OKRs. | Usuários com plano Pessoal ou Completo |
| **RF16** | Hierarquia de Cargos Configurável | O Admin deve definir, por empresa, quais módulos (`dashboard`, `kanban`, `equipe`, `financeiro`, `fornecedores`, `configuracoes`, `exportacao`, `ia`) cada cargo (Gerente, Funcionário) pode acessar. O padrão vale até a primeira matriz salva; o Admin tem acesso total e fixo. O bloqueio é aplicado no servidor (403) e refletido no menu e nas páginas. | Admin (edita), todos (consultam o próprio acesso) |
| **RF17** | Onboarding Guiado | No primeiro login, o Admin de uma empresa nova deve ser conduzido por um assistente de 3 passos (dados da empresa → hierarquia de cargos → conexões de API), concluído por `POST /company/onboarding/complete`. | Admin |
| **RF18** | Painel de Conexões de API | O sistema deve exibir ao Admin o estado em tempo real do banco de dados e da chave da IA (`GET /system/integrations`), sem expor segredos. | Admin |
| **RF19** | Criação de Acessos pelo Admin | O Admin deve criar logins de Gerente e Funcionário na própria empresa (`POST /auth/users`); a listagem/edição de usuários é restrita ao Admin, à mesma empresa e a papéis permitidos. | Admin |

---

## 6. Requisitos Não-Funcionais (RNF)

| Identificador | Categoria | Descrição |
|---|---|---|
| **RNF01** | **Desempenho** | O backend deve responder às requisições da API com latência inferior a 300ms (operações transacionais) através de chamadas assíncronas com FastAPI e SQLAlchemy 2.0 Async. |
| **RNF02** | **Persistência e Integridade** | O sistema deve utilizar banco de dados relacional (PostgreSQL gerenciado via Supabase, MySQL 8.0 via Docker, ou SQLite como fallback local — selecionável por `DATABASE_URL`), com 32 tabelas, escopo empresarial/pessoal e integridade referencial. |
| **RNF03** | **Segurança** | Todas as senhas devem ser armazenadas com hash criptográfico (Bcrypt). A autenticação deve utilizar tokens JWT com tempo de expiração. Chaves de API e segredos nunca devem constar no código-fonte ou na documentação, sendo injetadas via `.env` (nunca commitado). |
| **RNF04** | **Usabilidade e Design System** | A interface deve adotar o design system proprietário *Obsidian Flow* (Dark Theme, Glassmorphism, tipografia Outfit/Inter, Framer Motion para micro-interações) e ser responsiva. |
| **RNF05** | **Contêinerização e Deploy** | O ambiente completo (Frontend, Backend, Banco MySQL e Cache Redis) deve ser orquestrado de forma reproduzível através de `docker-compose.yml`; a opção de banco gerenciado (Supabase) roda fora do Compose, à parte dos demais serviços. |
| **RNF06** | **Privacidade e LGPD** | Antes de enviar dados financeiros para modelos de IA generativa (Gemini), o backend deve sanitizar as entradas, ofuscando dados sensíveis e nomes de colaboradores ("Colaborador A", "Colaborador B"). |
| **RNF07** | **Tolerância a Falhas em IA** | Falhas de conexão, rate limits ou timeouts na API do Gemini devem ser tratadas com fallback gracioso no backend, sem interromper as operações do ERP. |
| **RNF08** | **Idempotência de Inicialização** | O banco de dados deve possuir rotina de *seed* idempotente que popula dados de demonstração automaticamente apenas quando a base estiver vazia. |

---

## 7. Critérios de Aceitação e Definition of Done (DoD)

Para que uma funcionalidade seja considerada concluída:
1. O backend deve possuir endpoints documentados no Swagger OpenAPI (`/docs`).
2. Os modelos de dados devem estar sincronizados com o banco MySQL via SQLAlchemy Async.
3. O frontend deve tratar estados de carregamento (*loading*), sucesso (*toast/modal*) e falhas (*error boundary*).
4. O controle de acesso por papel, módulo e plano deve estar validado no cliente e no servidor.
5. As variáveis de ambiente necessárias devem estar documentadas no `.env.example`.

---

## 8. Rastreabilidade com a Implementação do Código

| Módulo do Sistema | Endpoints da API (Backend) | Páginas/Componentes (Frontend) | Tabelas MySQL |
|---|---|---|---|
| **Autenticação e Usuários** | `app/api/v1/endpoints/auth.py` | `pages/Login.tsx`, `pages/Register.tsx` | `users`, `companies`, `plans`, `subscriptions` |
| **Dashboard e Métricas** | `app/api/v1/endpoints/financial.py` | `pages/Dashboard.tsx`, `components/Layout.tsx` | `financial_entries`, `cost_centers`, `categories` |
| **Kanban e Operações** | `app/api/v1/endpoints/kanban.py`, `clients.py` | `pages/Kanban.tsx` | `projects`, `kanban_columns`, `kanban_cards`, `card_comments`, `clients` |
| **Gestão de Equipe & CTC** | `app/api/v1/endpoints/employees.py` | `pages/GestaoEquipe.tsx` | `employees`, `salary_history` |
| **Fornecedores** | `app/api/v1/endpoints/suppliers.py` | `pages/Fornecedores.tsx` | `suppliers` |
| **Lançamentos Financeiros** | `app/api/v1/endpoints/financial.py` | `pages/Financeiro.tsx` | `financial_entries`, `categories`, `cost_centers` |
| **IA / CFO Virtual** | `app/api/v1/endpoints/ai.py` | `pages/IAEmpresarial.tsx`, `components/AICfoDrawer.tsx` | Integração com dados de `financial_entries` e `kanban_cards` |
| **Exportação e Logs** | `app/api/v1/endpoints/exports.py` | `pages/Exportacao.tsx` | `export_logs` |
| **Hub Pessoal** | `app/api/v1/endpoints/personal.py` | `pages/HubPessoal.tsx` | `personal_entries`, `personal_categories`, `personal_accounts`, `personal_budgets`, `personal_goals`, `personal_debts`, `personal_subscriptions`, `personal_splits`, `personal_timeboxes`, `personal_okrs` |
| **Permissões, Onboarding e Integrações** | `app/api/v1/endpoints/permissions.py`, `system.py`, `company.py` (onboarding), `app/core/permissions.py` | `hooks/usePermissions.ts`, `components/PermissionMatrix.tsx`, `IntegrationsStatus.tsx`, `SystemAccessSection.tsx`, `pages/Onboarding.tsx`, `pages/Configuracoes.tsx` | `role_permissions`, `companies` (`onboarding_completed`, `permissions_customized`), `users` |

---

## 9. Matriz de Atendimento (estado real na publicação)

Legenda: ✅ **Atendido** · 🟡 **Parcial** (funciona com limitação registrada) · 🔲 **Pendente**. Itens do backlog em [BACKLOG.md](BACKLOG.md).

| Requisito | Status | Observação / item do backlog |
|---|---|---|
| RF01 Autenticação e RBAC | ✅ | JWT, usuário inativo bloqueado, 403 no backend, guards de módulo/escopo no frontend e proteção do último administrador. Rate limiting e MFA permanecem pendentes. |
| RF02 Planos e escopo | 🟡 | Alternância de hub e persistência de assinatura/fatura implementadas; processamento financeiro externo continua simulado. |
| RF03 Dashboard executivo | ✅ | Endpoints próprios de leitura, DRE e fluxo de caixa escopados pela empresa. |
| RF04–RF05 Kanban e Cost-per-Task | ✅ | Gate de módulo, isolamento empresarial e timer persistente, sem acréscimo fictício ao parar timer inexistente. |
| RF06 Clientes / RF08 Fornecedores / RF09 Lançamentos | ✅ | CRUD e consultas isolados por empresa. |
| RF07 Equipe e CTC | ✅ | CRUD, CTC, histórico salarial, desligamento e isolamento empresarial. |
| RF10–RF11 IA (CFO Virtual, orçamentos) | 🟡 | Respostas por palavras-chave; **sem** modelo generativo real (IA-1). |
| RF12 Exportação e auditoria | 🟡 | CSV e JSON válidos são gerados a partir dos dados reais da empresa e possuem log; PDF/XLSX não são anunciados enquanto não houver geradores próprios. Trilha de auditoria de alterações continua pendente. |
| RF13 Notificações | 🟡 | Painel funciona com notificações do seed; não há geração automática de alertas. |
| RF14–RF15 Hub Pessoal | ✅ | Módulos isolados pelo usuário autenticado e limitados aos planos Pessoal/Completo. |
| RF16 Hierarquia de cargos | ✅ | Verificado ponta a ponta com 3 papéis (matriz, 403, menu). |
| RF17 Onboarding | ✅ | Verificado ponta a ponta; refinamentos em UX-1. |
| RF18 Painel de integrações | ✅ | Banco e chave de IA; Redis não é usado pela aplicação. |
| RF19 Criação de acessos | ✅ | IDs não sequenciais, senha mínima, e-mail duplicado tratado e proteção contra remoção do último administrador. Edição completa pela interface ainda pode evoluir. |
| RNF01 Latência < 300 ms | 🟡 | Stack assíncrona; latência não medida formalmente. |
| RNF02 Persistência relacional | ✅ | 32 tabelas; PostgreSQL, MySQL e SQLite. Migração aditiva de compatibilidade implementada; Alembic e troca automática de banco continuam pendentes (DB-3/DB-5). |
| RNF03 Segurança | 🟡 | Bcrypt, JWT com expiração, segredos em `.env`. Um commit chegou a expor credenciais reais em texto puro no README; corrigido para placeholders, mas os valores originais ainda não foram rotacionados (SEC-5). |
| RNF04 Design System | ✅ | Obsidian Flow. |
| RNF05 Contêinerização | 🟡 | `docker-compose.yml` com 4 serviços; a verificação final foi feita por execução manual (SQLite), não pelo Compose. A opção de banco gerenciado (Supabase) não passa pelo Compose e exige troca manual da `DATABASE_URL` para não conflitar com o MySQL local (DB-5). |
| RNF06 LGPD na IA | 🔲 | Sem chamada a LLM externo, não há sanitização implementada (SEC-2, IA-1). |
| RNF07 Tolerância a falhas da IA | 🔲 | Depende da integração real (IA-1). |
| RNF08 Seed idempotente | ✅ | Executa apenas com a base vazia. |
