# Backlog — TechConnect 2.0

> Backlog oficial do projeto, consolidado a partir dos planos de execução já concluídos ([docs/planejamento/plans/](planejamento/plans/)), dos registros de andamento e revisão de cada fase (arquivos de trabalho locais, não versionados) e do [registro de alterações](registro-de-alteracoes-para-documentacao.md). Cada item foi conferido contra o código em 2026-09-21, com um checkpoint adicional em 2026-09-23 para a integração com Supabase.
>
> **Última atualização (2026-09-30, etapa 2):** branch `feature/planos-e-abas`: quatro planos com os preços aprovados, anexos de lançamento, exportações privadas, CTC configurável, exclusão de cartão, Minha Conta (troca de senha e direitos LGPD), auditoria na interface, gestão completa de acessos e correções de interface.
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
| SEC-5 | Credenciais reais commitadas em texto puro | O commit `913f78d` colou no `README.md` a senha real do banco Supabase, a `SUPABASE_ANON_KEY` real e um `SECRET_KEY` real, em vez de placeholders. O commit `3210242` substituiu os valores por placeholders no `README`, mas os valores antigos continuam válidos e visíveis no histórico do Git — a equipe decidiu, em 2026-09-23, não rotacioná-los por ora. Enquanto isso não acontecer, quem tiver acesso ao histórico do repositório pode ler e usar essas credenciais. Rotação recomendada no painel do Supabase (Database → Reset database password; regenerar a `anon key`) e, depois, reescrita do histórico para remover o valor. | 🔲 | commit `913f78d` (exposição), `3210242` (mitigação parcial no README) |
| DB-1 | Alinhar banco + persistência confiável | Resolvido: `.env` carregado fora do Docker (`913f78d`) e SQLite padrão com caminho absoluto na raiz do projeto. | ✅ | 2026-09-23 e 2026-09-30 |
| DB-2 | Persistir assinatura/pagamento + registro | Assinaturas e faturas agora usam `SubscriptionModel`/`InvoiceModel`, são filtradas pela empresa e sobrevivem a reinícios. O catálogo estático é sincronizado em `PlanModel` no checkout. O gateway financeiro continua simulado. | ✅ | correção 2026-09-23 |
| DB-5 | Troca de banco não é automática entre Supabase/MySQL/SQLite | Resolvido: no Compose, o backend usa o MySQL do próprio Compose por padrão; para o Supabase, define-se `COMPOSE_DATABASE_URL`. A `DATABASE_URL` do `.env` vale para a execução manual. | ✅ | etapa 2026-09-30 |
| SEC-2 | Auditoria e conformidade LGPD | Resolvido para o escopo do produto: `audit_logs` com tela em Configurações → Auditoria (filtro por ação, paginação); direitos do titular em Minha Conta: exportar os próprios dados (JSON) e excluir a conta (o único usuário leva junto todos os dados da empresa; com equipe, só os dados pessoais). Falta, fora do código: termo de uso e política de privacidade revisados por jurídico, e política de retenção. | 🔷 | etapas 2026-09-30 |

---

## P1 — Alta (funcionalidade essencial incompleta)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| IA-1 | Integração real de IA generativa | CFO Virtual, CFO Pessoal, Conciliação e Gerador de Orçamentos respondem por palavra-chave em `ai.py`. A `GEMINI_API_KEY` já está configurada na infra, mas não é usada. Histórico do CFO (`GET /ai/history`) sempre retorna vazio, e a resposta de `/ai/chat` informa um modelo (`gemini-2.5-flash`) e um consumo de tokens fixos que não correspondem a nenhuma chamada real. | 🔲 | registro §9, `ai.py` |
| AUTH-1 | Autenticação de dois fatores (2FA) | O campo `mfa_enabled` existe no `UserModel` e o login aceita `mfa_code`, mas não há fluxo de ativação nem verificação real. | 🔲 | registro §9 |
| EXP-1 | Exportação de relatórios | Resolvido: `exports.py` consulta os dados reais da empresa e gera CSV ou JSON válido; o download verifica a propriedade do log. PDF/XLSX foram removidos da interface até existirem geradores próprios. | ✅ | correção 2026-09-23 |
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
| UX-1 | Polimento do onboarding e das permissões | Resolvido: passo 1 já vinha pré-preenchido; no passo 2, "Salvar e continuar" salva e avança, e "Pular" deixa os padrões; o menu não pisca mais (permissões em cache síncrono); os botões de IA só aparecem com o módulo `ia`. Também corrigido: o texto dos toasts de erro e de sucesso usava cores inexistentes ou quase pretas. | ✅ | etapa 2026-09-30 |
| QA-1 | Sem testes automatizados | Backend coberto: `pytest` com 34 testes (isolamento entre empresas e usuários, gates, regras de acesso, autenticação, auditoria, migrações), verde em SQLite, PostgreSQL e MySQL. Falta: testes de frontend e CI automatizado. `npm run lint` ainda reporta erros pré-existentes. | 🔷 | etapa 2026-09-30 |
| API-1 | `id` do payload sobrescreve o gerado | Corrigido nos endpoints de criação: IDs e campos de escopo controlados pelo servidor são aplicados após o payload; updates bloqueiam `id`, `company_id` e campos relacionais sensíveis. | ✅ | correção 2026-09-23 |

---

## P3 — Baixa (cosmético e dívida técnica)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| CSS-1 | Token `--color-warning-container` ausente | Resolvido: token `--color-warning-container` definido. | ✅ | etapa 2026-09-30 |
| CSS-2 | Contraste das colunas do Kanban | O tema quase-preto comprime as razões de contraste WCAG. Fechar mais exige um novo token mais claro que `surface-container-highest` no design system. | 🔲 | task-23-report |
| SEED-1 | Dados de seed "envelhecem" | As datas do seed são congeladas na primeira execução (o mock antigo recalculava a cada request). Com o tempo, o seed fica com datas defasadas. | 🔲 | progress-db (nota) |
| DB-3 | Sem migrations versionadas | Resolvido: Alembic (`app/db/alembic`), com revisão base `0001` = schema anterior; bases pré-Alembic são carimbadas e atualizadas no startup; um teste falha se models e migrações divergirem. | ✅ | etapa 2026-09-30; ADR-007 |
| DB-4 | Limpeza pós-migração MySQL | Resolvido: o quadro do Kanban carrega com 3 consultas (colunas, cartões e comentários) em vez de N+1. | ✅ | etapa 2026-09-30 |

---

## Próximas etapas (roteiro comercial aprovado em 2026-09-30)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| PLAN-1 | Novos planos e preços | Resolvido: catálogo com Pessoal Essencial (R$ 29,90 / R$ 24,90), Pessoal Conectado (R$ 59,90 / R$ 49,90), Empresarial (R$ 249 / R$ 199) e Completo (R$ 299 / R$ 249), com limites `ai_queries` e `bank_connections` por plano; a linha do plano no banco acompanha o preço do catálogo. O catálogo não promete mais exportação em XLSX/PDF. A cobrança dos limites é o LIM-1. | ✅ | etapa 2026-09-30 |
| LIM-1 | Limites de uso por plano | Contar e limitar bancos conectados e mensagens de IA por mês, conforme o plano, para proteger a margem. | 🔲 | decisão 2026-09-30 |
| BANK-1 | Integração bancária | Conexão com o banco do cliente via agregador de Open Finance (Pluggy/Belvo), importação OFX/CSV como alternativa e conciliação automática com contas a pagar e receber. Depende de contrato com o agregador. | 🔲 | decisão 2026-09-30 |
| EMP-2 | Validação de payload nos cadastros | Resolvido: o cadastro de colaborador valida nome e e-mail, e qualquer violação de integridade do banco vira 400 com mensagem clara, em vez de 500. | ✅ | etapa 2026-09-30 |
| FIN-2 | Anexo de lançamento | Resolvido: anexo de comprovante (PDF, imagem ou XML, até 10 MB) em armazenamento privado fora de `/uploads`, servido só para a empresa dona; a chave interna não aparece na API nem nas exportações. | ✅ | etapa 2026-09-30 |
| EXP-2 | Exportações acessíveis sem login | Resolvido: os relatórios ficavam em `/uploads` (público); agora ficam em armazenamento privado e são baixados por `GET /exports/download/{id}` autenticado. Células que começam com `=`, `+`, `-` ou `@` são neutralizadas contra injeção de fórmula no Excel. | ✅ | achado na etapa 2026-09-30 |
| MT-3 | Padrões silenciosos de empresa/dono demo | Resolvido: 19 colunas `company_id`/`owner_id` tinham padrão `"cmp-001"`/`"usr-001"`, de modo que um código que esquecesse o campo gravaria na conta demo sem erro. Os padrões foram removidos e o seed atribui o dono demo explicitamente. | ✅ | achado na etapa 2026-09-30 |
| FIN-3 | Lançamento ligado a fornecedor de outra empresa | Resolvido: `PUT /financial/entries/{id}` aceitava `supplier_id` de outra empresa; agora valida, com teste. | ✅ | achado na etapa 2026-09-30 |
| PES-1 | Gráfico de patrimônio fictício | Resolvido: a evolução patrimonial do Hub Pessoal era uma rampa fixa; agora vem de saldos, dívidas e lançamentos reais. | ✅ | achado na etapa 2026-09-30 |
| SEC-6 | Nova sessão após o deploy | Os tokens anteriores a 2026-09-30 não têm `type`/`pwd` e deixam de valer: todos os usuários precisam entrar de novo uma vez. Avisar antes de publicar. | 🔲 | ADR-007 |

---

## Documentação formal pendente

A partir de [registro-de-alteracoes-para-documentacao.md](registro-de-alteracoes-para-documentacao.md).
Trabalho de reescrita do Escopo / ERS / DAS oficiais:

| ID | Documento | O que atualizar |
|----|-----------|-----------------|
| DOC-1 | Escopo | Modelo de 3 planos (Pessoal / Empresarial / Completo) como novo requisito de negócio; confirmar lista de módulos dos dois Hubs. |
| DOC-2 | ERS | Requisitos funcionais detalhados de cada módulo (CTC, fluxo de caixa D+90, timer em cartão, 10 módulos do Hub Pessoal); requisitos não-funcionais de segurança (segredos fora do código); lista honesta de lacunas (itens P0/P1 deste backlog) como "fora do escopo desta entrega". |
| DOC-3 | DAS | Atualizado para SQLAlchemy async, 32 tabelas, isolamento, persistência operacional, migração de compatibilidade e guards por módulo/escopo. |

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
