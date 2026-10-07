# Backlog — TechConnect 2.0

> Backlog oficial do projeto, consolidado a partir dos planos de execução já concluídos ([docs/planejamento/plans/](planejamento/plans/)), dos registros de andamento e revisão de cada fase (arquivos de trabalho locais, não versionados) e do [registro de alterações](registro-de-alteracoes-para-documentacao.md). Cada item foi conferido contra o código em 2026-09-21, com um checkpoint adicional em 2026-09-23 para a integração com Supabase.
>
> **Última atualização (2026-10-07, etapa 5 — lançamento):** branch `feature/lancamento`: cobrança recorrente (Asaas), recuperação de senha, 2FA, limite por IP, consentimento, armazenamento S3, exportação XLSX/PDF, sincronização bancária automática, e-mails, lint zerado, testes de frontend e CI. Ver ADR-010, ADR-011 e a [Sprint 03](../sprints/sprint-03.md).
>
> **Etapas 3 e 4 (2026-09-30):** branches `feature/integracao-bancaria` e `feature/ia-generativa`: importação de extrato OFX/CSV com conciliação automática, conexão com bancos via Pluggy (pronta, aguardando credenciais), regras de categoria, IA real com Gemini sobre os dados da empresa/pessoa e cota mensal por plano. Ver ADR-008 e ADR-009.
>
> **Etapa 2 (2026-09-30):** branch `feature/planos-e-abas`: quatro planos com os preços aprovados, anexos de lançamento, exportações privadas, CTC configurável, exclusão de cartão, Minha Conta (troca de senha e direitos LGPD), auditoria na interface, gestão completa de acessos e correções de interface.
>
> **Etapa 1 (2026-09-30):** etapa de endurecimento (branch `fix/endurecimento-seguranca`): suíte de testes automatizados, Alembic, SEC-4, trilha de auditoria e Compose sem troca manual de banco. Ver ADR-007 e a [spec](planejamento/specs/2026-09-30-endurecimento-seguranca-design.md).
>
> **Atualização anterior (2026-09-23):** correção de isolamento multiempresa e pessoal, persistência de assinatura, timers e configurações, reforço dos gates de acesso e correções de cálculos e exportação. Detalhes no ADR-006 e no changelog.
>
> **Checkpoint 2026-09-23:** o commit `913f78d`, feito direto na `main` e fora do fluxo de `issue`/`branch`/PR descrito no [CONTRIBUTING](../CONTRIBUTING.md), integrou suporte a PostgreSQL gerenciado via Supabase e resolveu a parte de `.env`/`load_dotenv()` do item DB-1. O mesmo commit expôs credenciais reais em texto puro no `README.md`; um commit seguinte (`3210242`) as substituiu por placeholders. Ficam abertos SEC-5 (rotação de credenciais pendente, por decisão da equipe) e DB-5 (a troca de banco entre Supabase, MySQL e SQLite não é automática).
>
> Legenda de status: 🔲 aberto · 🔷 em andamento · ✅ concluído · ⏸️ pausado/bloqueado. Prioridade: P0 (crítico/segurança), P1 (alta), P2 (média), P3 (baixa/dívida técnica).

---

## P0 — Crítico (segurança e integridade de dados)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| MT-1 | Dados de negócio separados por empresa | Concluído: colaboradores, fornecedores, lançamentos, clientes, projetos, notificações, centros de custo, categorias e exportações possuem `company_id`; consultas, alterações e busca global usam a empresa autenticada. Bases existentes recebem backfill aditivo para `cmp-001`. | ✅ | correção 2026-09-23; ADR-006 |
| MT-2 | Hub Pessoal isolado por usuário | Concluído: todas as consultas, criações, exclusões e aportes usam `u["id"]`; tentativas de operar um ID pertencente a outro usuário retornam 404. Dados legados permanecem com o proprietário original `usr-001`. | ✅ | correção 2026-09-23; ADR-006 |
| SEC-1 | RBAC nos endpoints da API | Resolvido para o escopo do plano: `role_permissions` (por empresa/cargo/módulo) + `require_module(...)` retornam 403 real nos routers de equipe, fornecedores, financeiro, exportação, IA e nas rotas de configuração que alteram dados; empresas ainda não customizadas usam os padrões (Gerente: 7 módulos; Funcionário: dashboard e kanban); o frontend guarda cada página pelo módulo concedido, e a busca global filtra resultados pelos módulos do usuário. `GET/PUT /auth/users` são restritos ao admin da própria empresa, com lista de cargos permitidos. | ✅ | Plano `2026-09-08-role-permissions-onboarding`; commits `446dbcd`…`b050a80`, `ecab7fa`, `2dff90c` |
| SEC-3 | Rotas sem gate de módulo | Corrigido: Kanban/clientes exigem `kanban`; Hub Pessoal exige escopo Pessoal/Completo; módulos empresariais verificam também o plano; Dashboard possui endpoints de leitura próprios. Planos seguem públicos intencionalmente e notificações são comuns aos usuários autenticados da própria empresa. | ✅ | correção 2026-09-23 |
| SEC-4 | Endurecimento básico de autenticação | Resolvido: sem `SECRET_KEY` padrão conhecida (produção se recusa a subir; em desenvolvimento, chave aleatória por execução); senha com 8+ caracteres, letras e números; `POST /auth/change-password`; bloqueio de 15 min após 5 senhas erradas (contador em `users`); access token de 60 min e refresh token de 7 dias separados, ambos revogados na troca de senha; o frontend renova a sessão automaticamente. Coberto por testes. | ✅ | etapa 2026-09-30; ADR-007 |
| SEC-5 | Credenciais reais commitadas em texto puro | O commit `913f78d` colou no `README.md` a senha real do banco Supabase, a `SUPABASE_ANON_KEY` real e um `SECRET_KEY` real. Os valores continuam válidos no histórico do Git. Em 2026-09-30 confirmou-se dano concreto de vazamento: o Google bloqueou a `GEMINI_API_KEY` do projeto como "reported as leaked". Antes de qualquer cliente real: trocar a senha do banco e a `anon key` no Supabase, gerar `SECRET_KEY` e chave Gemini novas, e reescrever o histórico. | 🔲 | commit `913f78d`; teste de 2026-09-30 |
| DB-1 | Alinhar banco + persistência confiável | Resolvido: `.env` carregado fora do Docker (`913f78d`) e SQLite padrão com caminho absoluto na raiz do projeto. | ✅ | 2026-09-23 e 2026-09-30 |
| DB-2 | Persistir assinatura/pagamento + registro | Assinaturas e faturas agora usam `SubscriptionModel`/`InvoiceModel`, são filtradas pela empresa e sobrevivem a reinícios. O catálogo estático é sincronizado em `PlanModel` no checkout. O gateway financeiro continua simulado. | ✅ | correção 2026-09-23 |
| DB-5 | Troca de banco não é automática entre Supabase/MySQL/SQLite | Resolvido: no Compose, o backend usa o MySQL do próprio Compose por padrão; para o Supabase, define-se `COMPOSE_DATABASE_URL`. A `DATABASE_URL` do `.env` vale para a execução manual. | ✅ | etapa 2026-09-30 |
| SEC-2 | Auditoria e conformidade LGPD | Resolvido no código: auditoria com tela, direitos do titular em Minha Conta, aceite versionado e datado dos termos (cadastro e próximo acesso). Falta, fora do código: revisão jurídica dos textos (hoje minuta) e política de retenção. | 🔷 | etapas 2026-09-30 e 2026-10-07 |

---

## P1 — Alta (funcionalidade essencial incompleta)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| IA-1 | Integração real de IA generativa | Resolvido no código: CFO Virtual (chat com histórico persistido e insights), CFO Pessoal, sugestão de categorias para movimentações bancárias reais e gerador de orçamentos usam o Gemini sobre um resumo dos dados reais. Sem chave, com falha ou com a cota esgotada, respondem por regras calculadas com os mesmos dados (nada de números fixos). **Pendente operacional:** a `GEMINI_API_KEY` atual foi bloqueada pelo Google como vazada (403 "reported as leaked"); é preciso gerar outra no Google AI Studio e mantê-la só no `.env`. | 🔷 | etapa 2026-09-30; ADR-009 |
| AUTH-1 | Autenticação de dois fatores (2FA) | Resolvido: TOTP com QR code em Minha Conta, 8 códigos de recuperação de uso único, segundo passo no login (token intermediário de 5 min), desativação com senha + código e pelo Admin; segredo criptografado com `ENCRYPTION_KEY`. | ✅ | etapa 2026-10-07; ADR-011 |
| EXP-1 | Exportação de relatórios | Resolvido: CSV, JSON, Excel (XLSX) e PDF com os dados reais da empresa, em armazenamento privado, com proteção contra injeção de fórmula. | ✅ | etapa 2026-10-07 |
| CFG-1 | Configurações que não persistem | Resolvido: calendário e preferências persistem (2026-09-23); parâmetros de CTC por empresa (`ctc_params`) editáveis em Configurações → Custo de Pessoal, usados no cálculo real e com recálculo automático dos colaboradores ativos (registrado no histórico salarial). | ✅ | etapa 2026-09-30 |

---

## P2 — Média (lacunas de UI / comportamento)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| EQ-1 | Botões do menu "kebab" na Gestão de Equipe | ~~Menu de ações (⋮) sem handler ligado.~~ Resolvido: o menu `more_vert` na visão em cartões já dispara `handleViewHistory`/`handleEdit`/`handleTerminate`; a visão em lista também tem os três botões ligados. | ✅ | Verificado 2026-09-10 em `GestaoEquipe.tsx` |
| KAN-1 | Excluir cartão no Kanban | Resolvido: botão de excluir no modal da tarefa, com confirmação. | ✅ | etapa 2026-09-30 |
| FIN-1 | DRE — composição por categoria | ~~Trechos hardcoded.~~ Resolvido: `GET /financial/dre` agora agrega receitas e despesas por categoria a partir dos lançamentos reais do banco (`receitas_map`/`despesas_map` em `financial.py`), sem valores fixos. | ✅ | Verificado 2026-09-10 em `financial.py` |
| NAV-1 | Guarda de rota do Hub Pessoal | Corrigido: guards de escopo são aplicados na rota e no backend; slugs inválidos redirecionam para a visão geral. | ✅ | correção 2026-09-23 |
| AUTH-2 | Gestão de acessos: regras de negócio faltando | Resolvido: troca de cargo (inclusive promover a Admin, com confirmação), redefinição de senha pelo Admin (encerra as sessões da pessoa) e ativar/desativar, tudo pela interface. | ✅ | etapa 2026-09-30 |
| UX-1 | Polimento do onboarding e das permissões | Resolvido: passo 1 já vinha pré-preenchido; no passo 2, "Salvar e continuar" salva e avança, e "Pular" deixa os padrões; o menu não pisca mais (permissões em cache síncrono); os botões de IA só aparecem com o módulo `ia`. (Correção do registro: em 30/09 constou aqui que os toasts eram ilegíveis; o campo de cor alterado não era usado no render, então não havia problema.) | ✅ | etapa 2026-09-30 |
| QA-1 | Sem testes automatizados | Resolvido: 139 testes de backend (SQLite, PostgreSQL, MySQL e Python 3.11), 14 de frontend (Vitest), teste de contrato frontend × rotas, ESLint sem erros nem avisos e CI no GitHub Actions a cada PR. | ✅ | etapas 2026-09-30 e 2026-10-07 |
| API-1 | `id` do payload sobrescreve o gerado | Corrigido nos endpoints de criação: IDs e campos de escopo controlados pelo servidor são aplicados após o payload; updates bloqueiam `id`, `company_id` e campos relacionais sensíveis. | ✅ | correção 2026-09-23 |

---

## P3 — Baixa (cosmético e dívida técnica)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| CSS-1 | Token `--color-warning-container` ausente | Resolvido: token `--color-warning-container` definido. | ✅ | etapa 2026-09-30 |
| CSS-2 | Contraste das colunas do Kanban | Resolvido: contraste medido pela fórmula WCAG; só o texto `outline` sobre cartões ficava abaixo de 4,5:1 (3,85) e foi clareado para `#999dac` (4,54:1 no pior fundo). | ✅ | etapa 2026-10-07 |
| SEED-1 | Dados de seed "envelhecem" | Resolvido: `python -m app.db.demo_dates` (ou `DEMO_REFRESH_DATES=1` na inicialização) desloca as datas da empresa e do usuário demo para hoje, mantendo os intervalos. | ✅ | etapa 2026-10-07 |
| DB-3 | Sem migrations versionadas | Resolvido: Alembic (`app/db/alembic`), com revisão base `0001` = schema anterior; bases pré-Alembic são carimbadas e atualizadas no startup; um teste falha se models e migrações divergirem. | ✅ | etapa 2026-09-30; ADR-007 |
| DB-4 | Limpeza pós-migração MySQL | Resolvido: o quadro do Kanban carrega com 3 consultas (colunas, cartões e comentários) em vez de N+1. | ✅ | etapa 2026-09-30 |

---

## Próximas etapas (roteiro comercial aprovado em 2026-09-30)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| PLAN-1 | Novos planos e preços | Resolvido: catálogo com Pessoal Essencial (R$ 29,90 / R$ 24,90), Pessoal Conectado (R$ 59,90 / R$ 49,90), Empresarial (R$ 249 / R$ 199) e Completo (R$ 299 / R$ 249), com limites `ai_queries` e `bank_connections` por plano; a linha do plano no banco acompanha o preço do catálogo. O catálogo não promete mais exportação em XLSX/PDF. A cobrança dos limites é o LIM-1. | ✅ | etapa 2026-09-30 |
| LIM-1 | Limites de uso por plano | Resolvido: limite de contas conectadas por plano (402 com mensagem de upgrade) e cota mensal de perguntas à IA por empresa (`ai_usage`); consumo visível em `GET /bank/usage` e na tela Bancos. | ✅ | etapa 2026-09-30 |
| BANK-1 | Integração bancária | Resolvido no código: importação OFX/CSV, conciliação, regras, telas nos dois hubs, Pluggy atrás de interface, webhook da Pluggy (`/bank/webhook/pluggy`) e sincronização agendada (`/bank/sync-all`), que pulam empresas inadimplentes. Pendente: contrato e credenciais da Pluggy e validação do widget e das transações no sandbox. | 🔷 | etapas 2026-09-30 e 2026-10-07; ADR-008 |
| EMP-2 | Validação de payload nos cadastros | Resolvido: o cadastro de colaborador valida nome e e-mail, e qualquer violação de integridade do banco vira 400 com mensagem clara, em vez de 500. | ✅ | etapa 2026-09-30 |
| FIN-2 | Anexo de lançamento | Resolvido: anexo de comprovante (PDF, imagem ou XML, até 10 MB) em armazenamento privado fora de `/uploads`, servido só para a empresa dona; a chave interna não aparece na API nem nas exportações. | ✅ | etapa 2026-09-30 |
| EXP-2 | Exportações acessíveis sem login | Resolvido: os relatórios ficavam em `/uploads` (público); agora ficam em armazenamento privado e são baixados por `GET /exports/download/{id}` autenticado. Células que começam com `=`, `+`, `-` ou `@` são neutralizadas contra injeção de fórmula no Excel. | ✅ | achado na etapa 2026-09-30 |
| MT-3 | Padrões silenciosos de empresa/dono demo | Resolvido: 19 colunas `company_id`/`owner_id` tinham padrão `"cmp-001"`/`"usr-001"`, de modo que um código que esquecesse o campo gravaria na conta demo sem erro. Os padrões foram removidos e o seed atribui o dono demo explicitamente. | ✅ | achado na etapa 2026-09-30 |
| FIN-3 | Lançamento ligado a fornecedor de outra empresa | Resolvido: `PUT /financial/entries/{id}` aceitava `supplier_id` de outra empresa; agora valida, com teste. | ✅ | achado na etapa 2026-09-30 |
| PES-1 | Gráfico de patrimônio fictício | Resolvido: a evolução patrimonial do Hub Pessoal era uma rampa fixa; agora vem de saldos, dívidas e lançamentos reais. | ✅ | achado na etapa 2026-09-30 |
| PES-2 | Importação de extrato no Hub Pessoal | Resolvido: a tela Bancos (`/pessoal/bancos`) importa OFX/CSV e transforma cada movimentação em lançamento pessoal, sem duplicar ao reimportar. | ✅ | etapa 2026-09-30 |
| IA-2 | Conciliação de IA com dados simulados | Resolvido: a aba Conciliação da IA Empresarial ignorava o arquivo e usava três transações fixas; agora sugere categorias para as movimentações reais importadas em Bancos, e aprovar aplica a categoria e cria regra. | ✅ | etapa 2026-09-30 |
| PAY-1 | Pagamento real | Resolvido no código: Asaas atrás de `PaymentProvider`, página de pagamento hospedada (sem dados de cartão no servidor), teste de 7 dias, webhook autenticado e idempotente que ativa, renova, marca atraso e estorno, bloqueio com 402 após 5 dias, cancelamento com acesso até o fim do período e página de assinatura com dados reais. Pendente: conta no Asaas, webhook configurado e validação no sandbox (inclusive cartão recorrente). | 🔷 | etapa 2026-10-07; ADR-010 |
| AUTH-3 | Recuperação de senha por e-mail | Resolvido: link de uso único (1 h, só o hash guardado), resposta igual exista ou não o e-mail, desbloqueio da conta e revogação das sessões; telas `/esqueci-senha` e `/redefinir-senha`. Depende de SMTP configurado para chegar ao usuário. | ✅ | etapa 2026-10-07; ADR-011 |
| STO-1 | Armazenamento compartilhado | Resolvido: anexos e exportações em disco local ou em S3 compatível (Supabase Storage, AWS S3, R2) via `STORAGE_BACKEND=s3`. | ✅ | etapa 2026-10-07 |
| SEC-7 | Limite de requisições por IP | Resolvido: janela deslizante nas rotas de autenticação (20/min por IP); `X-Forwarded-For` só com `TRUSTED_PROXY_HOPS`. Vale por instância (ver SEC-9). | ✅ | etapa 2026-10-07 |
| NOT-1 | E-mail de notificações | Resolvido: notificações de importação de extrato e de pagamento vão também por e-mail conforme a preferência; e-mails de segurança (senha, bloqueio, 2FA) sempre são enviados. | ✅ | etapa 2026-10-07 |
| NOT-2 | Alertas automáticos de vencimento | Resolvido: `POST /jobs/daily` (agendador, `X-Cron-Secret`) cria avisos de contas a pagar nos próximos 3 dias, recebimentos atrasados e tarefas do Kanban com prazo em até 2 dias, uma vez por dia por empresa, com e-mail ao Admin; empresas inadimplentes são puladas. A mesma rota roda a sincronização bancária. | ✅ | etapa 2026-10-07 |
| SEC-8 | Antivírus nos uploads | Comprovantes e extratos não passam por antivírus (ex.: ClamAV ou serviço do provedor de armazenamento). | 🔲 | ADR-011 |
| SEC-9 | Limite global entre instâncias | O limite por IP e o contador de cota são por processo; com várias instâncias, mover o limite por IP para o Redis já provisionado. | 🔲 | ADR-011 |
| DEP-1 | Implantação em produção | Definir onde hospedar backend e frontend, domínio, HTTPS, `APP_ENV=production`, `TRUSTED_PROXY_HOPS`, webhooks e agendador diário; o painel de Conexões de API lista o que falta. | 🔲 | auditoria 2026-10-07 |
| SEC-6 | Nova sessão após o deploy | Os tokens anteriores a 2026-09-30 não têm `type`/`pwd` e deixam de valer: todos os usuários precisam entrar de novo uma vez. Avisar antes de publicar. | 🔲 | ADR-007 |

---

## Documentação formal pendente

A partir de [registro-de-alteracoes-para-documentacao.md](registro-de-alteracoes-para-documentacao.md).
Trabalho de reescrita do Escopo / ERS / DAS oficiais:

| ID | Documento | O que atualizar |
|----|-----------|-----------------|
| DOC-1 | Escopo | Modelo de 4 planos com cobrança recorrente, teste de 7 dias e limites por plano; integrações (bancos, IA, pagamentos) como requisito de negócio; lista de módulos dos dois Hubs. Insumo pronto no [registro de alterações](registro-de-alteracoes-para-documentacao.md) §12. |
| DOC-2 | ERS | [requisitos.md](requisitos.md) está atualizado (RF01–RF29, RNF01–RNF10, matriz de 07/10). Falta transpor para o documento oficial da disciplina. |
| DOC-3 | DAS | [arquitetura.md](arquitetura.md) reescrito em 07/10: 40 tabelas versionadas por Alembic, integrações externas atrás de interfaces, cobrança e acesso por assinatura, controles de segurança e CI. Falta transpor para o documento oficial da disciplina. |

---

## Concluído (histórico)

Referência do que já foi entregue. Todos os planos em [docs/planejamento/plans/](planejamento/plans/) estão concluídos e aprovados, segundo os registros de andamento de cada fase:

- ✅ **Expansão do frontend** (22 tasks, mais o redesign visual do Kanban): os 10 módulos do Hub Empresarial e do Hub Pessoal, o modelo de conta por plano, tudo passou por QA manual com os 3 papéis.
- ✅ **Correções de design**: a colisão de `max-w` do Tailwind foi resolvida, e o Hub Pessoal ganhou rotas próprias com um alternador Empresarial/Pessoal.
- ✅ **Persistência real** (16 tasks). Saímos de listas em memória para SQLAlchemy async: 28 modelos ORM, seed idempotente e 13 routers migrados.
- ✅ **Troca para MySQL**, via Docker Compose, com MySQL 8 real, segredos fora do compose, `pool_recycle`/`pool_pre_ping`, FK `ON DELETE SET NULL` e e-mail tratado como case-insensitive.
- ✅ **Revisão de segurança**: credenciais tiradas do código-fonte, histórico do Git reescrito e `SECRET_KEY` rotacionada.
- ✅ **Menu de ações da Gestão de Equipe** (EQ-1). Os botões de Histórico, Editar e Desligar já funcionam tanto na visão em lista quanto no menu "⋮" da visão em cartões.
- ✅ **DRE por categoria real** (FIN-1): `GET /financial/dre` passou a agregar receitas e despesas por categoria direto dos lançamentos do banco, sem valores fixos no código.
- ✅ **Limpeza de `app/db/database.py`** (parte de DB-4). O arquivo legado saiu sem deixar referência pendente; só falta resolver o N+1 de `get_board`.
- ✅ **Hierarquia de cargos, painel de conexões e onboarding** (plano `2026-09-08`, cerca de 17 tasks mais os ajustes da revisão final). Permissões configuráveis por empresa com bloqueio real (403) no backend e nas páginas, abas de Hierarquia de Cargos e Conexões de API em Configurações, assistente de 3 passos no primeiro login do admin, criação de logins de Gerente/Funcionário, e o fechamento de `GET/PUT /auth/users` (que antes permitia escalação de privilégio). O limite conhecido que ficou dessa entrega é o MT-1 — ver [spec](planejamento/specs/2026-09-08-role-permissions-onboarding-design.md) e [plano](planejamento/plans/2026-09-08-role-permissions-onboarding-plan.md).
- ✅ **Notificações, busca global e exportação de verdade** (`761afd4`): toasts e modal de confirmação no lugar de `alert()`/`confirm()`, busca do topo ligada ao `/search/`, e exportação que efetivamente gera um arquivo.
