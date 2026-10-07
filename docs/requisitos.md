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
| **RF12** | Exportação de Relatórios e Auditoria | O sistema deve permitir a exportação de dados e relatórios em CSV, JSON, Excel (XLSX) e PDF e registrar o log de todas as exportações efetuadas. | Admin, Gerente |
| **RF13** | Central de Notificações | O sistema deve emitir alertas sobre prazos de tarefas do Kanban, vencimento de contas e mensagens do sistema através de um painel de notificações no cabeçalho. | Todos |
| **RF14** | Hub Pessoal: Gestão Financeira | O sistema deve disponibilizar controle financeiro pessoal completo: Extrato, Contas & Cartões, Orçamento por Categoria, Metas Financeiras, Dívidas & Parcelamentos e Assinaturas Recorrentes. | Usuários com plano Pessoal ou Completo |
| **RF15** | Hub Pessoal: Divisão de Despesas e Produtividade | O sistema deve possibilitar a divisão de contas entre múltiplos participantes (*Split*) e o gerenciamento de metas pessoais via Timeboxes e OKRs. | Usuários com plano Pessoal ou Completo |
| **RF16** | Hierarquia de Cargos Configurável | O Admin deve definir, por empresa, quais módulos (`dashboard`, `kanban`, `equipe`, `financeiro`, `fornecedores`, `configuracoes`, `exportacao`, `ia`) cada cargo (Gerente, Funcionário) pode acessar. O padrão vale até a primeira matriz salva; o Admin tem acesso total e fixo. O bloqueio é aplicado no servidor (403) e refletido no menu e nas páginas. | Admin (edita), todos (consultam o próprio acesso) |
| **RF17** | Onboarding Guiado | No primeiro login, o Admin de uma empresa nova deve ser conduzido por um assistente de 3 passos (dados da empresa → hierarquia de cargos → conexões de API), concluído por `POST /company/onboarding/complete`. | Admin |
| **RF18** | Painel de Conexões de API | O sistema deve exibir ao Admin o estado em tempo real do banco de dados e da chave da IA (`GET /system/integrations`), sem expor segredos. | Admin |
| **RF19** | Criação de Acessos pelo Admin | O Admin deve criar logins de Gerente e Funcionário na própria empresa (`POST /auth/users`); a listagem/edição de usuários é restrita ao Admin, à mesma empresa e a papéis permitidos. | Admin |
| **RF20** | Integração Bancária e Conciliação | O sistema deve importar extratos bancários (OFX e CSV) e, quando autorizado pelo cliente, sincronizar contas via agregador de Open Finance (Pluggy), sem duplicar movimentações; deve conciliar automaticamente cada movimentação com uma conta a pagar/receber quando houver um único candidato de mesmo tipo e valor com vencimento a até 5 dias, e oferecer conciliação, lançamento e descarte manuais, além de regras de categoria. | Admin, Gerente (módulo Financeiro); titular no Hub Pessoal |
| **RF21** | Assinatura e Cobrança Recorrente | O sistema deve oferecer 7 dias de teste, cobrar a assinatura de forma recorrente por um intermediador (Asaas: Pix, boleto ou cartão, digitados na página do intermediador), ativar e renovar o plano pela confirmação de pagamento (webhook), bloquear os módulos após 5 dias de atraso mantendo o acesso a Assinatura, Planos e Minha Conta, e permitir o cancelamento com acesso até o fim do período pago. | Admin (gerencia); todos (consultam) |
| **RF22** | Recuperação de Senha | O usuário deve poder redefinir a senha por um link de uso único enviado por e-mail, válido por 1 hora; a resposta não deve revelar se o e-mail está cadastrado. | Todos |
| **RF23** | Verificação em Duas Etapas | O usuário deve poder ativar a verificação em duas etapas com aplicativo autenticador (TOTP) e 8 códigos de recuperação de uso único; o Admin pode desativá-la para um membro que perdeu o acesso. | Todos (próprio), Admin (membros) |
| **RF24** | Trilha de Auditoria | O sistema deve registrar quem fez o quê, quando e de qual IP para logins, acessos, permissões, senhas, lançamentos, conciliações, assinatura e exportação de dados pessoais, consultável pelo Admin em Configurações → Auditoria. | Admin |
| **RF25** | Direitos do Titular (LGPD) | O usuário deve poder baixar os próprios dados e excluir a conta; quando for a única pessoa da empresa, a exclusão apaga todos os dados da empresa, inclusive arquivos. | Todos |
| **RF26** | Consentimento | O cadastro deve exigir o aceite dos Termos de Uso e da Política de Privacidade, gravando versão e data; usuários sem aceite da versão vigente devem aceitar no próximo acesso. | Todos |
| **RF27** | Comprovantes de Lançamentos | O sistema deve anexar comprovantes (PDF, imagem ou XML, até 10 MB) aos lançamentos financeiros, guardados em armazenamento privado e entregues somente à empresa dona. | Admin, Gerente |
| **RF28** | Parâmetros de Custo de Pessoal | O Admin deve configurar os multiplicadores de CTC (CLT, PJ, estágio) e as horas produtivas por mês; ao salvar, o custo dos colaboradores ativos é recalculado e registrado no histórico salarial. | Admin |
| **RF29** | Limites por Plano | O sistema deve limitar, conforme o plano, as contas bancárias conectadas e as perguntas mensais à IA, e exibir o consumo em Assinatura. | Todos |

---

## 6. Requisitos Não-Funcionais (RNF)

| Identificador | Categoria | Descrição |
|---|---|---|
| **RNF01** | **Desempenho** | O backend deve responder às requisições da API com latência inferior a 300ms (operações transacionais) através de chamadas assíncronas com FastAPI e SQLAlchemy 2.0 Async. |
| **RNF02** | **Persistência e Integridade** | O sistema deve utilizar banco de dados relacional (PostgreSQL gerenciado via Supabase, MySQL 8.0 via Docker, ou SQLite como fallback local — selecionável por `DATABASE_URL`), com 40 tabelas, escopo empresarial/pessoal, integridade referencial e evolução do schema por migrações versionadas (Alembic). |
| **RNF03** | **Segurança** | Senhas com hash Bcrypt e política mínima (8 caracteres, letras e números); JWT de acesso (60 min) e de renovação (7 dias) revogados na troca de senha; bloqueio de 15 min após 5 tentativas erradas; limite de requisições por IP nas rotas de autenticação; segredos do 2FA criptografados; arquivos privados servidos apenas com autenticação; segredos fora do código, via `.env` (nunca commitado). |
| **RNF04** | **Usabilidade e Design System** | A interface deve adotar o design system proprietário *Obsidian Flow* (Dark Theme, Glassmorphism, tipografia Outfit/Inter, Framer Motion para micro-interações) e ser responsiva. |
| **RNF05** | **Contêinerização e Deploy** | O ambiente completo (Frontend, Backend, Banco MySQL e Cache Redis) deve ser orquestrado de forma reproduzível através de `docker-compose.yml`; a opção de banco gerenciado (Supabase) roda fora do Compose, à parte dos demais serviços. |
| **RNF06** | **Privacidade e LGPD** | Antes de enviar dados financeiros para modelos de IA generativa (Gemini), o backend deve sanitizar as entradas, ofuscando dados sensíveis e nomes de colaboradores ("Colaborador A", "Colaborador B"). |
| **RNF07** | **Tolerância a Falhas em IA** | Falhas de conexão, rate limits ou timeouts na API do Gemini devem ser tratadas com fallback gracioso no backend, sem interromper as operações do ERP. |
| **RNF08** | **Idempotência de Inicialização** | O banco de dados deve possuir rotina de *seed* idempotente que popula dados de demonstração automaticamente apenas quando a base estiver vazia. |
| **RNF09** | **Qualidade e Verificação** | Toda mudança deve passar por testes automatizados do backend (em SQLite e PostgreSQL) e do frontend, lint sem erros e build, executados no CI (GitHub Actions) a cada pull request. |
| **RNF10** | **Acessibilidade** | Textos devem atingir contraste mínimo WCAG AA (4,5:1) sobre os fundos em que aparecem. |

---

## 7. Critérios de Aceitação e Definition of Done (DoD)

Para que uma funcionalidade seja considerada concluída:
1. O backend deve possuir endpoints documentados no Swagger OpenAPI (`/docs`).
2. Toda alteração de modelo deve vir com uma revisão Alembic (um teste falha se modelos e migrações divergirem).
3. O frontend deve tratar estados de carregamento (*loading*), sucesso (*toast/modal*) e falhas (*error boundary*).
4. O controle de acesso por papel, módulo e plano deve estar validado no cliente e no servidor.
5. As variáveis de ambiente necessárias devem estar documentadas no `.env.example`.
6. Testes automatizados cobrindo o comportamento novo, inclusive o isolamento entre empresas quando houver dados novos, passando no CI.

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
| **Exportação e Logs** | `app/api/v1/endpoints/exports.py` | `pages/Exportacao.tsx` | `export_logs` |
| **Hub Pessoal** | `app/api/v1/endpoints/personal.py` | `pages/HubPessoal.tsx` | `personal_entries`, `personal_categories`, `personal_accounts`, `personal_budgets`, `personal_goals`, `personal_debts`, `personal_subscriptions`, `personal_splits`, `personal_timeboxes`, `personal_okrs` |
| **Bancos e Conciliação** | `app/api/v1/endpoints/bank.py`, `bank_hooks.py`, `app/integrations/bank/` | `pages/Bancos.tsx` | `bank_accounts`, `bank_transactions`, `categorization_rules` |
| **Assinatura e Cobrança** | `app/api/v1/endpoints/payments.py`, `app/core/billing.py`, `app/integrations/payments/` | `pages/Checkout.tsx`, `pages/Subscription.tsx`, `components/SubscriptionBanner.tsx` | `subscriptions`, `invoices`, `plans` |
| **Conta, Segurança e LGPD** | `auth.py` (recuperação, 2FA, aceite), `account.py`, `audit.py` | `pages/MinhaConta.tsx`, `pages/RecuperarSenha.tsx`, `pages/Legal.tsx`, `components/TwoFactorSection.tsx`, `components/AuditLogSection.tsx` | `users`, `password_resets`, `audit_logs` |
| **IA com dados reais** | `ai.py`, `personal.py` (insights), `app/integrations/ai/` | `pages/IAEmpresarial.tsx`, `components/AICfoDrawer.tsx` | `ai_messages`, `ai_usage` |
| **Permissões, Onboarding e Integrações** | `app/api/v1/endpoints/permissions.py`, `system.py`, `company.py` (onboarding), `app/core/permissions.py` | `hooks/usePermissions.ts`, `components/PermissionMatrix.tsx`, `IntegrationsStatus.tsx`, `SystemAccessSection.tsx`, `pages/Onboarding.tsx`, `pages/Configuracoes.tsx` | `role_permissions`, `companies` (`onboarding_completed`, `permissions_customized`), `users` |

---

## 9. Matriz de Atendimento (estado real na publicação)

Legenda: ✅ **Atendido** · 🟡 **Parcial** (funciona com limitação registrada) · 🔲 **Pendente**. Itens do backlog em [BACKLOG.md](BACKLOG.md).

| Requisito | Status | Observação / item do backlog |
|---|---|---|
| RF01 Autenticação e RBAC | ✅ | JWT de acesso e renovação, bloqueio por tentativas, limite por IP, 403 no backend, guards no frontend, proteção do último administrador. |
| RF02 Planos e escopo | ✅ | 4 planos com preços aprovados; cobrança real em RF21. |
| RF03 Dashboard executivo | ✅ | Endpoints próprios de leitura, DRE e fluxo de caixa escopados pela empresa. |
| RF04–RF05 Kanban e Cost-per-Task | ✅ | Gate de módulo, isolamento, timer persistente, exclusão de tarefa, quadro em 3 consultas. |
| RF06 Clientes / RF08 Fornecedores / RF09 Lançamentos | ✅ | CRUD isolado por empresa; validação de fornecedor de outra empresa no lançamento. |
| RF07 Equipe e CTC | ✅ | CTC com parâmetros configuráveis (RF28). |
| RF10–RF11 IA (CFO Virtual, orçamentos) | 🟡 | Gemini sobre os dados reais com fallback por regras; a chave atual do projeto foi bloqueada pelo Google como vazada e precisa ser trocada (SEC-5). |
| RF12 Exportação e auditoria | ✅ | CSV, JSON, XLSX e PDF com dados reais, privados; auditoria em RF24. |
| RF13 Notificações | ✅ | Avisos de importação de extrato, pagamento, contas a vencer, recebimentos atrasados e prazos do Kanban (job diário), com e-mail conforme preferência. |
| RF14–RF15 Hub Pessoal | ✅ | Isolado pelo usuário; patrimônio calculado com dados reais; importação de extrato pessoal. |
| RF16 Hierarquia de cargos | ✅ | Matriz, 403 e menu verificados por testes automatizados. |
| RF17 Onboarding | ✅ | Salvar permissões avança o passo. |
| RF18 Painel de integrações | ✅ | Banco, IA, pagamentos, e-mail, bancos, armazenamento, agendador e criptografia, com orientação do que falta. |
| RF19 Criação de acessos | ✅ | Troca de cargo, promoção a Admin, redefinição de senha e desativação pela interface. |
| RF20 Integração bancária | 🟡 | OFX/CSV e conciliação completos; conexão automática pronta, aguardando contrato e credenciais da Pluggy (BANK-1). |
| RF21 Assinatura e cobrança | 🟡 | Fluxo completo com o Asaas atrás de interface e verificado com provedor simulado; falta validar no sandbox do Asaas com credenciais reais (PAY-1). |
| RF22 Recuperação de senha | 🟡 | Implementada; depende de um SMTP configurado para o e-mail chegar ao usuário. |
| RF23 Verificação em duas etapas | ✅ | TOTP, códigos de recuperação e desativação pelo Admin. |
| RF24 Trilha de auditoria | ✅ | Tela em Configurações → Auditoria. |
| RF25 Direitos do titular | ✅ | Exportar e excluir em Minha Conta. |
| RF26 Consentimento | 🟡 | Aceite versionado implementado; textos são minuta e precisam de revisão jurídica. |
| RF27 Comprovantes | ✅ | Armazenamento privado local ou S3 compatível. |
| RF28 Parâmetros de CTC | ✅ | Recalcula colaboradores ativos ao salvar. |
| RF29 Limites por plano | ✅ | Contas conectadas e perguntas à IA. |
| RNF01 Latência < 300 ms | 🟡 | Stack assíncrona; latência não medida formalmente. |
| RNF02 Persistência relacional | ✅ | 40 tabelas; PostgreSQL, MySQL e SQLite; 10 revisões Alembic. |
| RNF03 Segurança | 🟡 | Controles implementados; as credenciais expostas em `913f78d` continuam válidas até serem trocadas (SEC-5). |
| RNF04 Design System | ✅ | Obsidian Flow. |
| RNF05 Contêinerização | 🟡 | `docker-compose.yml` com 4 serviços e MySQL próprio por padrão; implantação em nuvem ainda não definida. |
| RNF06 LGPD na IA | 🟡 | Envia só um resumo agregado (sem CPF, e-mails ou nomes de colaboradores), mas descrições de lançamentos podem conter nomes; é preciso usar o nível pago do Gemini e citar o Google como operador. |
| RNF07 Tolerância a falhas da IA | ✅ | Erro, saída inválida ou cota esgotada caem nas regras sem interromper o sistema. |
| RNF08 Seed idempotente | ✅ | Executa apenas com a base vazia; datas da demonstração podem ser trazidas para hoje. |
| RNF09 Qualidade e verificação | ✅ | 139 testes de backend, 14 de frontend, lint sem erros e CI. |
| RNF10 Acessibilidade | 🟡 | Contraste AA corrigido no texto secundário; auditoria completa de acessibilidade não realizada. |
