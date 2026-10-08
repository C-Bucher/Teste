# Histórico de mudanças

## 2026-10-07 - Preparação para o lançamento

- Cobrança recorrente pelo Asaas, com o cartão digitado na página do Asaas (o checkout deixou de enviar número e CVV ao servidor), 7 dias de teste, webhook autenticado que ativa, renova e marca atraso, bloqueio com tolerância de 5 dias, cancelamento e página de assinatura com dados reais ([ADR 010](docs/decisoes/adr-010-cobranca-recorrente-e-acesso-por-assinatura.md)).
- Corrigido: empresas sem assinatura recebiam automaticamente uma assinatura ativa.
- Conta: recuperação de senha por e-mail, verificação em duas etapas com códigos de recuperação, limite de requisições por IP e aceite versionado dos termos e da política de privacidade ([ADR 011](docs/decisoes/adr-011-conta-2fa-consentimento-armazenamento.md)).
- E-mails transacionais e de notificação (SMTP) e alertas diários de contas a vencer, recebimentos atrasados e prazos do Kanban.
- Arquivos em armazenamento S3 compatível (Supabase Storage, S3, R2) e exportação em Excel e PDF.
- Webhook da Pluggy e job diário de sincronização bancária.
- Painel de Conexões de API cobrindo todas as integrações, com avisos de produção no log.
- Datas da demonstração atualizáveis e contraste WCAG AA no texto secundário.
- Qualidade: ESLint sem erros (eram 59), tipos da API compartilhados, carregamentos fora do corpo dos efeitos, arrastar do Kanban sem mutar o estado, testes de frontend (Vitest), teste de contrato entre frontend e backend e CI no GitHub Actions.
- Documentação: ERS (RF20 a RF29, RNF09 e RNF10, matriz refeita), DAS reescrito, ADRs 010 e 011, Sprint 03 e registro de alterações.
- Correção de registro: a entrada de 30/09 citava "toasts ilegíveis", problema que não existia.

## 2026-09-30 - Bancos, conciliação e IA real

- Bancos & Conciliação (Hub Empresarial e Hub Pessoal): importação de extrato OFX/CSV de qualquer banco, sem duplicar ao reimportar; conciliação automática com as contas a pagar e a receber; ações manuais de conciliar, lançar e ignorar; regras de categoria (BANK-1, [ADR 008](docs/decisoes/adr-008-integracao-bancaria-e-conciliacao.md)).
- Conexão automática com bancos via agregador de Open Finance (Pluggy), pronta no código e ativada quando as credenciais forem configuradas; limite de contas conectadas por plano (LIM-1).
- IA real: CFO Virtual, CFO Pessoal, sugestão de categorias e gerador de orçamentos usam o Gemini sobre os dados reais. Sem IA disponível, respondem por regras com os mesmos dados. Histórico do chat salvo e cota mensal de perguntas por plano (IA-1, [ADR 009](docs/decisoes/adr-009-ia-generativa-com-dados-reais.md)).
- Removidos os últimos dados fictícios das telas de IA.
- Suíte de testes: 99 testes, verdes em SQLite, PostgreSQL e MySQL.

## 2026-09-30 - Planos comerciais e abas completas

- Quatro planos com os preços aprovados: Pessoal Essencial, Pessoal Conectado, Empresarial e Completo (PLAN-1).
- Financeiro: anexo de comprovante por lançamento, guardado em armazenamento privado (FIN-2).
- Exportação: relatórios baixados só com login, sem link público, e protegidos contra injeção de fórmula (EXP-2).
- Configurações: aba Custo de Pessoal (CTC) com recálculo dos colaboradores (CFG-1) e aba Auditoria (SEC-2).
- Minha Conta: troca de senha, download dos próprios dados e exclusão da conta (LGPD).
- Gestão de acessos: troca de cargo, promoção a Admin e redefinição de senha pelo Admin (AUTH-2).
- Kanban: excluir tarefa (KAN-1) e quadro carregado em 3 consultas (DB-4).
- Hub Pessoal: evolução patrimonial calculada com dados reais.
- Correções: padrões que gravavam silenciosamente na conta demo (MT-3), fornecedor de outra empresa num lançamento (FIN-3), cadastro incompleto devolvendo 500 (EMP-2), menu piscando, botões de IA sem permissão, onboarding com botão de salvar separado (UX-1).
- Suíte de testes: 61 testes, verdes em SQLite, PostgreSQL e MySQL.

## 2026-09-30 - Endurecimento de segurança e confiabilidade

- Suíte de testes automatizados (`pytest`, 34 testes) cobrindo o isolamento entre empresas e entre usuários, gates por módulo e por plano, regras de acesso, autenticação, auditoria e migrações. Passa em SQLite, PostgreSQL e MySQL (QA-1).
- Migrações versionadas com Alembic, com revisão base igual ao schema anterior; bases criadas antes do Alembic são reconhecidas e atualizadas automaticamente (DB-3, [ADR 007](docs/decisoes/adr-007-endurecimento-autenticacao-migracoes-auditoria.md)).
- Autenticação: sem `SECRET_KEY` padrão conhecida; política de senha (8+ caracteres, letras e números); troca de senha; bloqueio de 15 minutos após 5 senhas erradas; access token de 60 minutos e refresh token de 7 dias, ambos invalidados ao trocar a senha; o frontend renova a sessão sozinho (SEC-4).
- Trilha de auditoria em `audit_logs`, com `GET /audit/` restrito ao Admin da própria empresa (SEC-2, parte 1).
- Docker Compose usa o próprio MySQL por padrão (`COMPOSE_DATABASE_URL` para o Supabase) e o SQLite usa caminho absoluto (DB-5, DB-1).
- Corrigido: o cadastro gravava o registro de auditoria antes da empresa, o que o PostgreSQL e o MySQL recusavam por chave estrangeira.

## 2026-09-23 - Isolamento, autorização e persistência operacional

- Dados empresariais passaram a ser isolados por `company_id` em modelos, CRUDs, busca, notificações e exportações.
- O Hub Pessoal passou a usar o usuário autenticado como `owner_id`, com verificação de propriedade nas mutações.
- Kanban e clientes agora exigem o módulo correspondente; escopos de plano são verificados no backend e nas rotas React.
- Assinaturas, faturas, timers ativos, calendário de trabalho e preferências de notificação passaram a ser persistidos no banco.
- Corrigidos: timer inexistente adicionando uma hora, resposta de custo divergente, DRE ignorando período e dupla contagem no fluxo de caixa.
- IDs de empresa/usuário passaram a usar UUID; cadastro valida senha/plano e a gestão de acessos protege o último administrador.
- Exportações passaram a aceitar apenas CSV/JSON válidos e a consultar dados reais da empresa.
- CORS tornou-se configurável e `SECRET_KEY` insegura bloqueia inicialização em produção.
- Adicionada migração aditiva de compatibilidade para bancos existentes e ADR-006.

Registre aqui as mudanças relevantes por sprint ou marco avaliativo.

## Sprint 00 - Planejamento

- Criação do repositório.
- Definição do problema, da equipe, dos papéis e do backlog inicial.

## Sprint 01 - MVP e Persistência Relacional

- Hub Empresarial e Hub Pessoal no frontend (React 19 + Tailwind v4, design Obsidian Flow).
- Backend FastAPI com SQLAlchemy 2.0 assíncrono, seed idempotente e Docker Compose (MySQL, Redis, backend, frontend).
- Segredos migrados para `.env`.

## Sprint 02 - Controle de Acesso por Cargo e Onboarding

- Hierarquia de cargos configurável com bloqueio real (HTTP 403) no servidor e nas páginas (RF16, [ADR 004](docs/decisoes/adr-004-permissoes-por-cargo-e-onboarding.md)).
- Onboarding guiado de 3 passos, painel de conexões de API e criação de logins pelo Admin (RF17–RF19).
- Correções de segurança em `/auth/users` (escalação de privilégio), `is_active` exigido, busca filtrada por módulo.
- Repositório consolidado: código e histórico completo incorporados, README e `.gitignore` unificados, documentação atualizada com a matriz de atendimento dos requisitos.
- Registradas como pendências: MT-1 (dados de negócio por empresa) e MT-2 (Hub Pessoal por usuário) — ver [BACKLOG](docs/BACKLOG.md).

## 2026-09-23 - Suporte a PostgreSQL Gerenciado (Supabase)

- `DATABASE_URL` passa a aceitar PostgreSQL (via `asyncpg`) além de MySQL e SQLite, com `.env.example` ativando o Supabase por padrão ([ADR 005](docs/decisoes/adr-005-suporte-postgresql-supabase.md)).
- `load_dotenv()` adicionado ao backend: a execução manual (fora do Docker) agora lê o `.env` automaticamente.
- Correção de segurança: um commit deste mesmo dia (`913f78d`) havia colado credenciais reais do Supabase e um `SECRET_KEY` real em texto puro no `README.md`; foram substituídas por placeholders (`3210242`). Os valores antigos ainda não foram rotacionados no Supabase — ver SEC-5 no [BACKLOG](docs/BACKLOG.md).
- Registrada como pendência a DB-5: a troca entre Supabase, MySQL (Docker) e SQLite exige editar manualmente a `DATABASE_URL` no `.env`.
