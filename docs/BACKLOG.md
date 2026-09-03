# Backlog — TechConnect 2.0

> Backlog oficial do projeto. Consolidado a partir dos planos de execução já concluídos
> ([docs/superpowers/plans/](superpowers/plans/)), dos progress ledgers
> ([.superpowers/sdd/](../.superpowers/sdd/)), dos relatórios de revisão e do
> [registro de alterações §9](registro-de-alteracoes-para-documentacao.md).
>
> **Última atualização:** 2026-09-03
>
> **Legenda de status:** 🔲 aberto · 🔷 em andamento · ✅ concluído · ⏸️ pausado/bloqueado
>
> **Prioridade:** P0 (crítico/segurança) · P1 (alta) · P2 (média) · P3 (baixa/dívida técnica)

---

## P0 — Crítico (segurança e integridade de dados)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| SEC-1 | RBAC nos endpoints da API | O controle de acesso por papel (Admin/Gerente/Funcionário) só existe na navegação/UI. Um usuário com token válido pode chamar qualquer rota que a interface esconde dele. Falta reforçar o papel em cada endpoint do backend. | 🔲 | registro §9 |
| DB-1 | Alinhar banco + persistência confiável | SQLite com caminho relativo (`./techconnect.db`), arquivo `.db` versionado no git (qualquer `git checkout`/`stash` apaga dados), `.env` aponta para MySQL mas não é carregado (`load_dotenv()` ausente). Resultado: "dados somem ao reiniciar". | 🔲 | diagnóstico 2026-09-03 |
| DB-2 | Persistir assinatura/pagamento + registro | `payments.py` (`SUBSCRIPTIONS_DB`, `INVOICES_DB`) e `plans.py` são listas/dicts em memória. `POST /auth/register` cria o usuário mas **não** cria a empresa (`CompanyModel`) nem a assinatura (`SubscriptionModel`) do plano escolhido. | 🔲 | `payments.py`, `auth.py` |
| SEC-2 | Auditoria e conformidade LGPD | Nenhuma trilha de auditoria (quem alterou o quê e quando), sem base para conformidade com LGPD. | 🔲 | registro §9 |

---

## P1 — Alta (funcionalidade essencial incompleta)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| IA-1 | Integração real de IA generativa | CFO Virtual, CFO Pessoal, Conciliação e Gerador de Orçamentos respondem por palavra-chave em `ai.py`. A `GEMINI_API_KEY` já está configurada na infra, mas não é usada. Histórico do CFO (`GET /ai/history`) sempre retorna vazio. | 🔲 | registro §9, `ai.py` |
| AUTH-1 | Autenticação de dois fatores (2FA) | O campo `mfa_enabled` existe no `UserModel` e o login aceita `mfa_code`, mas não há fluxo de ativação nem verificação real. | 🔲 | registro §9 |
| EXP-1 | Exportação nunca conclui | Relatórios ficavam presos em "PROCESSANDO". Há uma tentativa de correção nas alterações não commitadas de `exports.py` (gera CSV mock em `uploads/`) — precisa ser finalizada, revisada e commitada. | 🔷 | progress-db Task 14 |
| CFG-1 | Configurações que não persistem | `PUT /company/calendar` (calendário de trabalho) e `GET /company/ctc-params` retornam dicts fixos calculados na hora — não gravam nada, não sobrevivem nem a um reload. Preferências de notificação idem. | 🔲 | task-4-report, `company.py`, `notifications.py` |

---

## P2 — Média (lacunas de UI / comportamento)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| EQ-1 | Botões do menu "kebab" na Gestão de Equipe | Menu de ações (⋮) dos cartões/linhas de funcionário sem handler ligado. | 🔲 | progress-db Task 14 |
| KAN-1 | Excluir cartão no Kanban | Não há botão/UI para excluir um cartão. Verificar se o endpoint existe e ligar a ação. | 🔲 | progress-db Task 14 |
| FIN-1 | DRE — composição por categoria | O detalhamento de receitas/despesas por categoria no DRE ainda tem trechos hardcoded que não batem com a composição real dos lançamentos. | 🔲 | progress-db Task 7 |
| NAV-1 | Guarda de rota do Hub Pessoal | Rotas `/pessoal/:tab` são protegidas só no nível de navegação, não de rota. Slug de aba inválido não redireciona a URL. `plan_scope` não é checado por rota. | 🔲 | progress.md revisão final |
| API-1 | `id` do payload sobrescreve o gerado | Vários POST/PUT aceitam `id` vindo do corpo da requisição e sobrescrevem o id gerado pelo servidor (comportamento herdado do mock antigo). | 🔲 | progress-db (nota herdada) |

---

## P3 — Baixa (cosmético e dívida técnica)

| ID | Item | Descrição | Status | Fonte |
|----|------|-----------|--------|-------|
| CSS-1 | Token `--color-warning-container` ausente | Referenciado pela tag de prioridade "ALTA" no Kanban, mas nunca definido em `frontend/src/index.css`. | 🔲 | progress.md Task 23 |
| CSS-2 | Contraste das colunas do Kanban | O tema quase-preto comprime as razões de contraste WCAG. Fechar mais exige um novo token mais claro que `surface-container-highest` no design system. | 🔲 | task-23-report |
| SEED-1 | Dados de seed "envelhecem" | As datas do seed são congeladas na primeira execução (o mock antigo recalculava a cada request). Com o tempo, o seed fica com datas defasadas. | 🔲 | progress-db (nota) |
| DB-3 | Sem caminho de migração de schema | `Base.metadata.create_all` cria tabelas novas mas não faz `ALTER` em tabelas existentes. Qualquer coluna nova exige recriar o banco ou migração manual. | 🔲 | revisão final DB |
| DB-4 | Limpeza pós-migração MySQL | `pool_recycle` e FK `ON DELETE SET NULL` já foram tratados. Confirmar que não sobrou nenhuma referência a `app/db/database.py` (removido) e revisar N+1 em `get_board`. | 🔲 | progress-db |

---

## Documentação formal pendente

A partir de [registro-de-alteracoes-para-documentacao.md](registro-de-alteracoes-para-documentacao.md).
Trabalho de reescrita do Escopo / ERS / DAS oficiais:

| ID | Documento | O que atualizar |
|----|-----------|-----------------|
| DOC-1 | Escopo | Modelo de 3 planos (Pessoal / Empresarial / Completo) como novo requisito de negócio; confirmar lista de módulos dos dois Hubs. |
| DOC-2 | ERS | Requisitos funcionais detalhados de cada módulo (CTC, fluxo de caixa D+90, timer em cartão, 10 módulos do Hub Pessoal); requisitos não-funcionais de segurança (segredos fora do código); lista honesta de lacunas (itens P0/P1 deste backlog) como "fora do escopo desta entrega". |
| DOC-3 | DAS | Arquitetura de persistência (SQLAlchemy async, ~28 tabelas, seed idempotente); diagrama de implantação com os 4 containers Docker + MySQL; sistema de design de frontend "Obsidian Flow" (rotas por módulo, não abas). |

---

## Concluído (histórico)

Referência do que já foi entregue — todos os planos em [docs/superpowers/plans/](superpowers/plans/)
estão 100% concluídos e aprovados segundo os progress ledgers:

- ✅ **Expansão do frontend** (22 tasks + redesign visual do Kanban) — 10 módulos do Hub Empresarial e Hub Pessoal, modelo de conta por plano, QA manual com os 3 papéis. [progress.md](../.superpowers/sdd/progress.md)
- ✅ **Correções de design** (colisão `max-w` do Tailwind, reestruturação do Hub Pessoal para rotas próprias + alternador Empresarial/Pessoal). [progress.md](../.superpowers/sdd/progress.md)
- ✅ **Persistência real** (16 tasks) — migração de listas em memória para SQLAlchemy async, 28 modelos ORM, seed idempotente, 13 routers migrados. [progress-db.md](../.superpowers/sdd/progress-db.md)
- ✅ **Troca para MySQL** — Docker Compose com MySQL 8 real, segredos fora do compose, `pool_recycle`/`pool_pre_ping`, FK `ON DELETE SET NULL`, e-mail case-insensitive. [progress-db.md](../.superpowers/sdd/progress-db.md)
- ✅ **Revisão de segurança** — credenciais removidas do código-fonte, histórico do Git reescrito, `SECRET_KEY` rotacionada.
