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
| **Configurações** | Dados da empresa — acesso restrito a Admin | |
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
- **~28 tabelas** modelando todas as entidades do sistema (usuários, funcionários, fornecedores, lançamentos financeiros, projetos/kanban, notificações, módulos do Hub Pessoal, etc.).
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

- Projeto publicado no GitHub em `github.com/gabrielsalles-bit/TechConnect2.0`, branch `main` atualizada com todo o histórico de desenvolvimento.
- `README.md` reescrito para refletir o estado atual: banco de dados real, passo de configuração de `.env`, modelo de planos, estrutura de pastas atualizada.

---

## 9. O que a documentação deve registrar como "ainda não implementado" / trabalho futuro

Importante ser honesto sobre isso na entrega — são lacunas reais, conhecidas, não escondidas:

- **Controle de acesso (RBAC)** hoje só existe em nível de navegação/interface (o menu muda por papel), **não é reforçado em cada endpoint da API** — um usuário com token válido poderia, tecnicamente, chamar uma rota que a interface esconde dele.
- **Autenticação de dois fatores (2FA)**: não implementada.
- **IA (CFO Virtual, CFO Pessoal, etc.)**: hoje é um mock que reage a palavras-chave, **não uma integração real com um modelo de IA generativa** (apesar de já existir uma `GEMINI_API_KEY` configurada na infraestrutura, pronta para quando essa integração for feita).
- **Auditoria e conformidade com LGPD**: não implementada.
- Histórico antigo do Git (antes da limpeza de segurança) só foi reescrito localmente — se este repositório já tinha sido clonado por outra pessoa em algum outro lugar antes desta limpeza, aquela cópia ainda teria as credenciais antigas.

---

## Sugestão de como dividir a atualização entre Escopo / ERS / DAS

- **Escopo**: seção 1 (modelo de planos/contas) é a mudança mais estrutural — precisa entrar como novo requisito de negócio. Seções 2 e 3 (lista de módulos) confirmam/expandem o que já estava previsto.
- **ERS**: requisitos funcionais detalhados de cada módulo das seções 2 e 3, mais os requisitos não-funcionais de segurança (seção 7) e as lacunas da seção 9 (documentar como "fora do escopo desta entrega" é tão importante quanto documentar o que foi feito).
- **DAS**: arquitetura de persistência (seção 5), diagrama de implantação com os 4 containers Docker + MySQL (seção 6), e menção ao sistema de design de front-end (seção 4).
