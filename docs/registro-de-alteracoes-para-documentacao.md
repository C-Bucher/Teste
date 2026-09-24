# Registro de Alterações — TechConnect 2.0

> Documento de apoio para atualizar Escopo, ERS e DAS. Cobre tudo que foi implementado desde a análise inicial de aderência entre documentação e código, organizado por área funcional. Leve este documento (junto dos PDFs originais) para a conversa onde vocês vão reescrever a documentação formal.

## Contexto: por que a documentação precisa mudar

A análise inicial encontrou divergências reais entre o que o Escopo/ERS/DAS descreviam e o que o código fazia. A partir daí, o desenvolvimento seguiu adiante e **acrescentou funcionalidades que não existiam em nenhuma versão da documentação original** — em especial, o modelo de dois tipos de conta (Pessoal e Empresarial) com um plano combinado, e a expansão do Hub Pessoal para muito além do que estava escrito. Este documento existe pra vocês não perderem nada disso na hora de fechar a versão final da documentação.

---

## 1. Decisão de arquitetura: modelo de contas e planos

Isso **não estava no Escopo/ERS original** e precisa virar um requisito documentado formalmente.

- Três planos: **Pessoal**, **Empresarial** e **Completo** (combina os dois).
- O campo `plan_scope` (`pessoal` / `empresarial` / `completo`) no cadastro do usuário controla o que ele vê.
- A navegação lateral (sidebar) é filtrada por `plan_scope` **e** por papel (Admin / Gerente / Funcionário) — dois eixos de controle de acesso, não um só.
- Um mesmo usuário com plano Completo pode **alternar entre o workspace Empresarial e o Pessoal** por um botão no cabeçalho, sem precisar logar de novo.

**Onde impacta a documentação**: Escopo (novo modelo de negócio/planos), ERS (novos requisitos funcionais de controle de acesso por plano, não só por papel).

---

## 2. Hub Empresarial (ERP para PMEs) — módulos implementados

| Módulo | O que faz | Observação |
|---|---|---|
| **Dashboard** | Visão geral financeira com dados reais (não mais valores fixos de exemplo) | |
| **Kanban de Projetos** | Quadro com colunas, drag & drop, CRUD de clientes, criação de projetos, cronômetro de tarefas, comentários por cartão | Redesenhado 2x para melhorar contraste/legibilidade |
| **Gestão de Equipe** | CRUD de funcionários, cálculo de CTC (Custo Total ao Colaborador), histórico salarial, ação de desligamento | |
| **Financeiro** | Lançamentos financeiros, DRE (Demonstrativo de Resultado), fluxo de caixa projetado D+90 | |
| **Fornecedores** | Cadastro e gestão de fornecedores | |
| **Configurações** | Dados da empresa, plano de contas, centros de custo, calendário, hierarquia de cargos e conexões de API — acesso restrito a Admin por padrão | Ver seção 10 |
| **Notificações** | Sino de notificações com painel, no cabeçalho | |
| **Exportação** | Geração e histórico de relatórios exportados | |
| **IA Empresarial** | CFO Virtual, Conciliação Bancária, Gerador de Orçamentos | **Ainda é um mock por palavra-chave, não uma integração real com IA generativa** — ver seção 9 |

**Onde impacta**: ERS precisa descrever cada módulo como requisito funcional formal (muitos já estavam previstos, mas o texto atual provavelmente não reflete os detalhes como CTC, D+90, timer em cartão, etc.).

---

## 3. Hub Pessoal — expansão significativa

O Hub Pessoal cresceu muito além do que a documentação original previa. Módulos implementados:

- **Visão Geral** e **Extrato**
- **Contas & Cartões**
- **Orçamento por Categoria**
- **Metas Financeiras**
- **Dívidas & Parcelamentos**
- **Assinaturas Recorrentes**
- **Divisão de Despesas**
- **Dashboard Analítico Pessoal**
- **Timeboxes / OKRs** (produtividade pessoal)
- **CFO Pessoal IA**

**Mudança estrutural importante**: originalmente o Hub Pessoal era uma página única com abas internas. Foi **redesenhado para espelhar exatamente o layout do Hub Empresarial** — cada módulo agora é uma rota própria na barra lateral (`/pessoal/:tab`), não uma aba dentro de uma página só.

**Onde impacta**: Escopo e ERS precisam listar esses 10 módulos do Hub Pessoal como requisitos funcionais formais — hoje provavelmente só uma versão simplificada consta na documentação.

---

## 4. Design e experiência do usuário

- Sistema de design próprio, "**Obsidian Flow**": glassmorphism, tipografia Inter/Outfit, tema escuro.
- Correção de um bug real de layout: os tokens de espaçamento customizados do Tailwind colidiam com a escala nativa de `max-width`, quebrando o texto em várias telas (inclusive o CFO Virtual, que você reportou com print de tela).
- Botão de alternância Empresarial ↔ Pessoal no cabeçalho.

**Onde impacta**: se o DAS descreve a stack de front-end, vale mencionar o sistema de design (Obsidian Flow) e a decisão de arquitetura de navegação (rotas por módulo, não abas).

---

## 5. Backend: de dados em memória para banco de dados real

Esta é a mudança mais estrutural de todas. **Toda a persistência de dados era simulada em listas/dicionários Python na memória do processo** — ou seja, qualquer reinício do servidor apagava tudo. Isso foi substituído por um banco de dados relacional real.

- **SQLAlchemy 2.0 assíncrono** como camada de ORM.
- **29 tabelas** modelando todas as entidades do sistema (usuários, funcionários, fornecedores, lançamentos financeiros, projetos/kanban, notificações, módulos do Hub Pessoal, etc.).
- **Seed idempotente**: os dados de demonstração (3 usuários de teste, funcionários, projetos etc.) são inseridos automaticamente na primeira execução, e nunca duplicados em execuções seguintes.
- **13 routers da API migrados** de leitura/escrita em memória para consultas reais ao banco, mantendo exatamente os mesmos contratos de resposta (nenhuma mudança perceptível pro front-end).
- Autenticação (login/JWT) também migrada — usuários cadastrados agora persistem de verdade.

**Onde impacta**: DAS precisa de uma seção nova ou substancialmente revisada descrevendo a arquitetura de persistência de dados — hoje provavelmente descreve (ou nem menciona) o antigo modelo em memória.

---

## 6. Infraestrutura: Docker Compose + MySQL real

- Stack completo orquestrado via **Docker Compose**: banco de dados (MySQL 8), Redis, backend (FastAPI) e frontend (React/Vite), cada um em seu container.
- Banco de dados evoluiu de SQLite (etapa intermediária) para **MySQL 8 real**, mudando só a variável `DATABASE_URL` — nenhuma mudança de código nos modelos ou rotas.
- Ajustes de robustez específicos para banco real em produção: `pool_recycle`/`pool_pre_ping` na conexão (evita erros de conexão expirada), regras de exclusão em cascata (`ON DELETE SET NULL`) para não deixar referências quebradas quando um fornecedor ou cliente é excluído, normalização de e-mail para minúsculas (garante comportamento consistente entre bancos).

**Onde impacta**: DAS — diagrama de arquitetura/implantação precisa refletir os 4 containers e o MySQL real, não mais um servidor único com dados em memória.

---

## 7. Segurança

- **Credenciais sensíveis** (chave de assinatura JWT, chave da API Gemini, senhas do MySQL) **removidas do código-fonte** e movidas para variáveis de ambiente (`.env`, nunca versionado no Git).
- Encontrada e corrigida uma segunda cópia da chave JWT que estava hardcoded em outro arquivo (`app/core/config.py`) — sem essa correção, mover as credenciais no `docker-compose.yml` teria sido só aparência, a chave real continuaria fixa no código.
- **Histórico do Git reescrito** para remover as credenciais antigas de todos os commits (elas tinham sido commitadas em texto puro antes desta etapa), e a `SECRET_KEY` foi rotacionada (trocada por uma nova).
- Revisão de segurança dedicada rodada sobre essas mudanças antes do envio ao GitHub.

**Onde impacta**: se a documentação (ERS/DAS) tem uma seção de requisitos não-funcionais de segurança, ela precisa registrar essa prática (segredos fora do código-fonte, via variável de ambiente).

---

## 8. Repositório e versionamento

- O código passa a viver no repositório institucional do curso (GitHub da organização CAMPUSCEUB, "ADS – Dashboard para Gestão Operacional"); o repositório pessoal usado no início do desenvolvimento deixa de ser a referência.
- `README.md` mantido em sincronia com o código: banco real (MySQL no Docker, SQLite na execução manual), passo de configuração de `.env`, modelo de planos, permissões por cargo, onboarding, estrutura de pastas e limitações conhecidas.
- `docs/BACKLOG.md` é o backlog oficial; `docs/planejamento/` guarda as especificações e os planos de cada fase como registro histórico do processo.

---

## 9. O que a documentação deve registrar como "ainda não implementado" / trabalho futuro

Importante ser honesto sobre isso na entrega — são lacunas reais, conhecidas, não escondidas:

- **Autenticação de dois fatores (2FA)**: não implementada.
- **IA (CFO Virtual, CFO Pessoal, etc.)**: hoje é um mock que reage a palavras-chave, **não uma integração real com um modelo de IA generativa** (apesar de já existir uma `GEMINI_API_KEY` configurada na infraestrutura, pronta para quando essa integração for feita).
- **Auditoria e conformidade com LGPD**: não implementada.
- **Credenciais antigas**: a chave da API de IA e a chave JWT que estiveram hardcoded no início do projeto foram removidas de todo o histórico publicado agora, mas precisam ser **revogadas/rotacionadas** nos respectivos serviços, pois chegaram a ficar em repositório público anterior.

---

---

## 10. Hierarquia de cargos, painel de conexões e onboarding (entregue, com limites)

Trabalho de 08/09 a 21/09 que fechou a lacuna de RBAC da seção 9 (removida daquela lista). Entregue e verificado de ponta a ponta no navegador.

- **Permissões por cargo configuráveis**: tabela `role_permissions` (empresa × cargo × módulo) no lugar do controle fixo no código do frontend. Admin tem sempre acesso total; Gerente e Funcionário têm um conjunto configurável em *Configurações → Hierarquia de Cargos*. Empresas que ainda não salvaram uma matriz usam os padrões (Gerente: 7 módulos; Funcionário: Dashboard e Projetos); uma matriz salva prevalece, inclusive vazia.
- **Bloqueio real no backend e nas páginas**: equipe, fornecedores, financeiro, exportação, IA e as rotas de configuração que alteram dados retornam **403** sem permissão; as páginas do frontend são protegidas pelo módulo concedido (conceder e revogar funcionam); a busca global só devolve resultados dos módulos permitidos.
- **Painel de conexões de API** (Configurações): testa de verdade o banco de dados e informa se a chave da IA está configurada, sem editar credenciais pela interface. O `/health` deixou de afirmar um Redis que a aplicação nunca usou.
- **Onboarding guiado**: assistente de 3 passos (empresa → cargos → conexões) no primeiro login do Admin de cada empresa nova; a empresa de demonstração já nasce configurada.
- **Criação de logins**: o Admin cria Gerentes/Funcionários em *Gestão de Equipe → Acessos ao Sistema* (antes só existia cadastro de Admin).
- **Correções de segurança encontradas no caminho**: o cadastro nunca criava a empresa no banco (todas colidiam na mesma linha); `GET/PUT /auth/users` não tinham autorização — qualquer usuário podia se promover a ADMIN ou alterar usuários de outras empresas — e agora são restritos ao Admin da própria empresa, com lista de cargos permitidos; usuários desativados agora perdem o acesso; `techconnect.db` saiu do controle de versão.

**Limites que a documentação formal deve registrar honestamente** (detalhes no [BACKLOG](BACKLOG.md)):
- **MT-1**: só empresas, usuários e permissões são isolados por empresa; funcionários, financeiro, Kanban, clientes, fornecedores, notificações e exportações são um conjunto único compartilhado — uma empresa nova vê os dados da demonstração.
- **SEC-3**: Kanban, clientes, notificações, planos, pagamentos e Hub Pessoal não têm gate por módulo; as permissões Dashboard/Projetos afetam só o menu.
- **SEC-4/QA-1**: sem política de senha nem limite de tentativas de login; nenhum teste automatizado (toda verificação foi manual).

**Onde impacta**: ERS (requisito funcional de controle de acesso configurável e de onboarding; requisitos não-funcionais de segurança); Escopo (a promessa de multiempresa deve ser descrita como "em evolução" enquanto MT-1 estiver aberto); DAS (diagrama de autorização: `role_permissions` + `require_module`).

---

## 11. Suporte a PostgreSQL gerenciado (Supabase) e um incidente de credencial (23/09)

Commit `913f78d`, feito direto na `main` (sem `issue`/`branch`/PR), adicionou suporte a PostgreSQL via Supabase como banco padrão, ao lado de MySQL (Docker) e SQLite (fallback). Ver [ADR 005](decisoes/adr-005-suporte-postgresql-supabase.md).

- **O que mudou de fato**: `DATABASE_URL` aceita `postgresql+asyncpg://…`; `.env.example` ativa o Supabase por padrão; `load_dotenv()` adicionado (resolve parte do **DB-1** — antes, a execução manual não lia o `.env` sozinha).
- **Incidente:** o mesmo commit colou no `README.md`, em texto puro, a senha real do banco Supabase, a `SUPABASE_ANON_KEY` real e um `SECRET_KEY` real — não placeholders. Um commit seguinte (`3210242`) corrigiu o `README` para usar placeholders. **Os valores antigos continuam válidos e ficam visíveis no histórico do Git** (visível a toda a organização no GitHub, não só à equipe); a equipe decidiu, em 23/09, não rotacioná-los por ora. Registrado como **SEC-5** no [BACKLOG](BACKLOG.md) — a documentação formal não deve descrever a gestão de segredos do projeto como isenta de falhas enquanto esse item estiver aberto.
- **Efeito colateral não intencional:** como o `docker-compose.yml` repassa `DATABASE_URL=${DATABASE_URL}` do `.env` do host para o container do backend, sem sobrescrevê-la, a opção "Docker Compose (MySQL)" só funciona se essa linha for trocada manualmente para o MySQL antes de subir os containers — do contrário, o backend em Docker tenta falar com o Supabase. Registrado como **DB-5**.

**Onde impacta**: DAS (múltiplos backends relacionais atrás de uma única variável de configuração; nova dependência externa — Supabase); ERS (RNF02 já não pressupõe um único SGBD); Escopo/avaliação de segurança (incidente de credencial deve constar como limitação conhecida, não ser omitido).

---

## Sugestão de como dividir a atualização entre Escopo / ERS / DAS

- **Escopo**: seção 1 (modelo de planos/contas) é a mudança mais estrutural — precisa entrar como novo requisito de negócio. Seções 2 e 3 (lista de módulos) confirmam/expandem o que já estava previsto.
- **ERS**: requisitos funcionais detalhados de cada módulo das seções 2 e 3, mais os requisitos não-funcionais de segurança (seção 7) e controle de acesso configurável (seção 10), e as lacunas restantes da seção 9 (documentar como "fora do escopo desta entrega" é tão importante quanto documentar o que foi feito).
- **DAS**: arquitetura de persistência (seção 5), diagrama de implantação com os 4 containers Docker + MySQL (seção 6), e menção ao sistema de design de front-end (seção 4).
