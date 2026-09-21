# Especificação de Requisitos do Sistema — TechConnect 2.0

Este documento formaliza todos os requisitos do projeto **TechConnect 2.0**, desenvolvido como solução do **Projeto Integrador (PI)** do curso de Tecnologia em Análise e Desenvolvimento de Sistemas (ADS) — CEUB.

---

## 1. Visão do Produto

O **TechConnect 2.0** é uma plataforma completa e inteligente de **Gestão Operacional e Financeira** voltada para Pequenas e Médias Empresas (PMEs), gestores e profissionais autônomos. A solução unifica a gestão operacional de projetos e equipes (Kanban com cálculo de tempo e custo real por tarefa) com o controle financeiro avançado (DRE, projeção de fluxo de caixa D+90 e cálculo de CTC) e um **CFO Virtual baseado em IA (Google Gemini)**. Adicionalmente, a plataforma oferece um **Hub Pessoal** integrado, permitindo ao usuário manter suas finanças e metas pessoais estritamente organizadas sem misturar os fluxos com a pessoa jurídica.

---

## 2. Público-Alvo

1. **Gestores e Donos de PMEs:** Proprietários que precisam de visão unificada do caixa, rentabilidade de projetos e tomada de decisão orientada por dados e IA.
2. **Gerentes de Operações e Projetos:** Responsáveis pela alocação de equipe, acompanhamento de prazos e monitoramento de custos por tarefa (*Cost-per-Task*).
3. **Colaboradores e Funcionários:** Usuários operacionais que visualizam suas tarefas atribuídas, cronometram suas atividades e acompanham métricas de execução.
4. **Profissionais Autônomos e Empreendedores Individuais:** Usuários que necessitam alternar com agilidade entre o controle do seu negócio e sua gestão financeira pessoal.

---

## 3. Problema de Negócio

No cenário das PMEs brasileiras, a operação diária e o controle financeiro costumam operar de maneira desconectada. Planilhas manuais ou sistemas legados fragmentados causam:
- **Cegueira de Custo Operacional:** Impossibilidade de saber quanto custou de fato cada entrega, projeto ou demanda de cliente.
- **Dificuldade no Cálculo do Custo Real da Equipe:** Desconhecimento do Custo Total ao Colaborador (CTC), somando salário base, benefícios e encargos trabalhistas (CLT/PJ).
- **Decisões Financeiras Tardias:** Falta de relatórios preditivos (como fluxo de caixa projetado para 90 dias) e ausência de uma assessoria financeira contínua.
- **Promiscuidade Financeira PJ/PF:** Mistura de despesas pessoais com as da empresa por falta de uma ferramenta que permita a gestão de ambos os mundos em uma interface única e coesa.

---

## 4. Objetivos

### 4.1 Objetivo Geral
Desenvolver e disponibilizar uma plataforma web de alta produtividade (Full Stack) que integre gestão operacional ágil (Kanban com rastreio de custo), controle financeiro corporativo robusto (DRE, D+90, CTC), inteligência financeira generativa (CFO Virtual IA) e módulo de finanças pessoais.

### 4.2 Objetivos Específicos
- Implementar um quadro Kanban com cronômetro em tempo real que calcule dinamicamente o *Cost-per-Task* associado ao valor/hora do funcionário responsável.
- Automatizar o cálculo de CTC (Custo Total ao Colaborador) e manter o histórico salarial com auditoria de alterações.
- Gerar DRE gerencial consolidado e projeção preditiva de fluxo de caixa para 90 dias (D+90).
- Estruturar agentes de IA baseados em Procedimentos Operacionais Padrão (POPs) para gerar diagnósticos financeiros executivos e orçamentos.
- Disponibilizar um Hub Pessoal com controle de extratos, metas, divisão de despesas (*Split*) e cartões.
- Garantir arquitetura desacoplada e orquestrada via contêineres Docker (Frontend React, Backend FastAPI, Banco MySQL e Cache Redis).

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
| **RNF02** | **Persistência e Integridade** | O sistema deve utilizar banco de dados relacional MySQL 8.0, com schema normalizado em 29 tabelas, integridade referencial com chaves estrangeiras e índices otimizados. |
| **RNF03** | **Segurança** | Todas as senhas devem ser armazenadas com hash criptográfico (Bcrypt). A autenticação deve utilizar tokens JWT com tempo de expiração. Chaves de API e segredos nunca devem constar no código-fonte, sendo injetadas via `.env`. |
| **RNF04** | **Usabilidade e Design System** | A interface deve adotar o design system proprietário *Obsidian Flow* (Dark Theme, Glassmorphism, tipografia Outfit/Inter, Framer Motion para micro-interações) e ser responsiva. |
| **RNF05** | **Contêinerização e Deploy** | O ambiente completo (Frontend, Backend, Banco MySQL e Cache Redis) deve ser orquestrado de forma reproduzível através de `docker-compose.yml`. |
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
| RF01 Autenticação e RBAC | ✅ | JWT, usuário inativo bloqueado, 403 real. Lacunas de rotas sem gate: SEC-3; endurecimento de senha/lockout: SEC-4. |
| RF02 Planos e escopo | 🟡 | Alternância de hub implementada; assinatura/pagamento ainda em memória (DB-2). |
| RF03 Dashboard executivo | ✅ | DRE e fluxo de caixa a partir de `/financial/*`. Dados compartilhados entre empresas: MT-1. |
| RF04–RF05 Kanban e Cost-per-Task | 🟡 | Implementados; rotas sem gate de módulo (SEC-3) e dados globais (MT-1). |
| RF06 Clientes / RF08 Fornecedores / RF09 Lançamentos | 🟡 | CRUD funcional; dados globais (MT-1). |
| RF07 Equipe e CTC | ✅ | CRUD, CTC, histórico salarial e desligamento; dados globais (MT-1). |
| RF10–RF11 IA (CFO Virtual, orçamentos) | 🟡 | Respostas por palavras-chave; **sem** modelo generativo real (IA-1). |
| RF12 Exportação e auditoria | 🟡 | Arquivo real gerado e servido para download, com log registrado (EXP-1); porém o conteúdo é um CSV de exemplo, não os dados reais do relatório, e não há PDF. |
| RF13 Notificações | 🟡 | Painel funciona com notificações do seed; não há geração automática de alertas. |
| RF14–RF15 Hub Pessoal | 🟡 | Módulos funcionais, **mas sem isolamento por usuário** (MT-2). |
| RF16 Hierarquia de cargos | ✅ | Verificado ponta a ponta com 3 papéis (matriz, 403, menu). |
| RF17 Onboarding | ✅ | Verificado ponta a ponta; refinamentos em UX-1. |
| RF18 Painel de integrações | ✅ | Banco e chave de IA; Redis não é usado pela aplicação. |
| RF19 Criação de acessos | ✅ | Faltam regras de negócio (edição/desativação pela interface, proteção do último admin): AUTH-2. |
| RNF01 Latência < 300 ms | 🟡 | Stack assíncrona; **latência não medida formalmente**. |
| RNF02 Persistência relacional | ✅ | 29 tabelas; MySQL 8 (Docker) e SQLite (execução manual). Sem migrações versionadas (DB-3). |
| RNF03 Segurança | ✅ | Bcrypt, JWT com expiração, segredos em `.env`. |
| RNF04 Design System | ✅ | Obsidian Flow. |
| RNF05 Contêinerização | 🟡 | `docker-compose.yml` com 4 serviços; a verificação final foi feita por execução manual (SQLite), não pelo Compose. |
| RNF06 LGPD na IA | 🔲 | Sem chamada a LLM externo, não há sanitização implementada (SEC-2, IA-1). |
| RNF07 Tolerância a falhas da IA | 🔲 | Depende da integração real (IA-1). |
| RNF08 Seed idempotente | ✅ | Executa apenas com a base vazia. |
