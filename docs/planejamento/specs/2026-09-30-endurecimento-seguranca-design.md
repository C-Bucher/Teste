# Etapa 1 — Endurecimento de segurança e confiabilidade

- **Data:** 2026-09-30
- **Branch:** `fix/endurecimento-seguranca` (a partir de `origin/main` @ `03e87b8`)
- **Contexto:** o TechConnect passa a ser tratado como produto comercial. O isolamento por empresa e por usuário (MT-1, MT-2, ADR-006) já foi entregue, mas não tem nenhum teste automático, e a autenticação ainda tem lacunas (SEC-4). A integração bancária prevista (etapa 3) só pode receber dados reais depois desta etapa.

## Objetivo

Garantir, com testes automáticos, que uma empresa nunca enxerga dados de outra e que um usuário nunca enxerga as finanças pessoais de outro. Além disso, fechar as lacunas de autenticação, versionar o schema do banco e registrar uma trilha de auditoria.

## Escopo

### 1. Suíte de testes automáticos (QA-1)
- `pytest` + `pytest-asyncio` + `httpx.ASGITransport`, com banco SQLite temporário por sessão de teste. `get_db` é sobrescrito, e a aplicação real sobe sem o seed de demonstração.
- Fixtures que registram duas empresas independentes (A e B) pelo próprio `/auth/register`.
- **Testes de isolamento:** para cada recurso empresarial (fornecedores, lançamentos, clientes, projetos/Kanban, colaboradores, notificações, exportações), a empresa A cria e a empresa B não lista, não lê, não altera e não exclui (resposta 404 ou lista vazia). O mesmo vale para o Hub Pessoal entre dois usuários.
- **Testes de gate:** um Funcionário recebe 403 nos módulos não concedidos.
- Comando: `venv\Scripts\python -m pytest` (dependências em `requirements-dev.txt`).

### 2. Autenticação (SEC-4)
- **`SECRET_KEY`:** em produção a aplicação já se recusa a subir sem a chave. Fora de produção, se a chave faltar, é gerada uma aleatória a cada início, com aviso no log. Não existe mais uma chave padrão conhecida publicamente.
- **Política de senha:** mínimo de 8 caracteres, com pelo menos uma letra e um número. Vale no cadastro, na criação de acesso e na troca de senha.
- **Bloqueio por tentativas:** após 5 senhas erradas seguidas, a conta fica bloqueada por 15 minutos (resposta 429). O contador fica no banco (`users.failed_login_count`, `users.locked_until`), então sobrevive a reinícios e vale para mais de uma instância. O login certo zera o contador.
- **Tokens separados:** o access token dura 60 minutos. O refresh token dura 7 dias e leva `type=refresh`. `/auth/refresh` só aceita refresh token, e as rotas protegidas só aceitam access token. Tokens emitidos antes de uma troca de senha ou de uma desativação deixam de valer (claim `pwd` com parte do hash atual).
- **Frontend:** guarda o `refresh_token`. Diante de um 401, tenta renovar uma única vez e repete a requisição; se não conseguir, faz logout.

### 3. Migrações versionadas (DB-3) e troca de banco (DB-1/DB-5)
- **Alembic** com a revisão base igual ao schema atual (32 tabelas + as colunas desta etapa), compatível com SQLite, MySQL e PostgreSQL (`render_as_batch` no SQLite).
- **No início da aplicação:**
  - banco vazio: `upgrade head`;
  - banco criado antes do Alembic (tabelas existentes, sem `alembic_version`): roda a migração de compatibilidade já existente, faz `stamp` da base e então `upgrade head`;
  - demais casos: `upgrade head`.
- **SQLite padrão** com caminho absoluto na raiz do projeto, e não mais relativo ao diretório de onde o comando foi executado.
- **Docker Compose:** o backend usa o MySQL do próprio Compose por padrão. Para apontar para o Supabase dentro do Docker, define-se `COMPOSE_DATABASE_URL`. O `DATABASE_URL` do `.env` continua valendo para a execução manual.

### 4. Trilha de auditoria (SEC-2, parte 1)
- Nova tabela `audit_logs`: `id`, `company_id`, `user_id`, `action`, `entity`, `entity_id`, `details` (JSON em texto), `ip`, `created_at`.
- **Eventos registrados:** login com sucesso, login com falha e bloqueio; criação e alteração de acessos; alteração da matriz de permissões; criação, alteração, pagamento e exclusão de lançamento financeiro; troca de senha.
- `GET /audit` só para ADMIN, filtrado pela própria empresa, com paginação.
- A tela de consulta fica na etapa 2 (Configurações → Auditoria).

## Fora do escopo (etapas seguintes)
- **SEC-5:** a troca das credenciais do Supabase é feita pelo dono do projeto no painel; o código não resolve.
- **LGPD, parte 2** (exportar meus dados, excluir conta, termo de consentimento): etapa 2.
- 2FA (AUTH-1) e IA real (IA-1): etapa 4.

## Tarefas (TDD — o teste vem antes do código)
1. Infraestrutura de testes + fixtures de duas empresas + teste de fumaça.
2. Testes de isolamento empresarial e pessoal, e de gate por módulo. Corrigir qualquer vazamento encontrado.
3. `SECRET_KEY` sem padrão conhecido + política de senha + endpoint de troca de senha.
4. Bloqueio por tentativas.
5. Access/refresh separados + invalidação por troca de senha + interceptor de refresh no frontend.
6. Alembic (base + colunas novas) + inicialização em 3 casos + SQLite com caminho absoluto.
7. Docker Compose com `COMPOSE_DATABASE_URL`.
8. Auditoria: modelo, helper, eventos e `GET /audit`.
9. Documentação: BACKLOG, CHANGELOG, ADR-007 e README (como rodar os testes).

## Critério de pronto
- `pytest` passa inteiro e `npm run build` passa.
- O login demo (`admin@techconnect.com.br`) funciona num banco novo.
- O backlog reflete o estado real.
