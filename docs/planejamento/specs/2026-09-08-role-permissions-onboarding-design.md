# Hierarquia de Cargos, Conexões de API e Onboarding — Design

**Status:** Aprovado para virar plano de implementação.

## Contexto e motivação

Hoje o controle de acesso por cargo (Admin / Gerente / Funcionário) é **inteiramente hardcoded no frontend** (`Layout.tsx`, ex: `user.role !== 'FUNCIONARIO'`), sem nenhuma tela de configuração e — mais grave — **sem nenhuma validação no backend**: qualquer usuário autenticado pode chamar qualquer endpoint da API, independente do cargo, bastando saber a URL. A página de Configurações também não tem nenhuma visão sobre o estado das integrações do sistema (banco de dados, IA), e não existe nenhum fluxo guiado de primeira configuração para uma empresa recém-cadastrada.

Este documento cobre a correção desses três pontos, decididos em conversa com o usuário (respostas registradas abaixo).

## Decisões já tomadas (não reabrir)

1. **Escopo**: implementar Configurações (hierarquia + conexões) por completo, e corrigir bugs críticos de lógica encontrados no caminho — não é uma auditoria geral do sistema.
2. **Hierarquia de cargos**: bloqueio real no backend (403), não só visual.
3. **Modelo de cargos**: os 3 cargos fixos existentes (Admin, Gerente, Funcionário); o Admin configura quais módulos cada um vê — sem cargos customizados.
4. **Conexões de API**: painel de status/saúde (testa e mostra Online/Offline), **não** um formulário editável de credenciais.
5. **Onboarding**: wizard guiado obrigatório no primeiro login do Admin de uma empresa nova.

## Bug crítico encontrado durante a análise (dentro do escopo combinado)

`GET /health` (`app/main.py:22`) retorna `"redis":"ok"` como **literal fixo no código**, sem testar nada — e o Redis não é usado em nenhum outro lugar da aplicação (grep confirma zero uso real). Isso é corrigido junto: o Redis sai da lista de integrações reportadas (não é uma dependência funcional real hoje) e o `/health` para de alegar uma checagem que não faz.

---

## Parte 1 — Backend: dados e autorização

### Modelo de dados novo

**`RolePermissionModel`** (`app/db/models.py`):
```python
class RolePermissionModel(Base):
    __tablename__ = "role_permissions"
    id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)       # GERENTE | FUNCIONARIO (ADMIN nunca é gravado — tem acesso implícito total)
    module_key = Column(String(50), nullable=False) # ver lista de módulos abaixo
```
Uma linha presente = aquele cargo tem acesso àquele módulo, para aquela empresa. Ausência = sem acesso. Sem coluna `allowed` booleana — presença/ausência já basta e evita estado ambíguo.

**`CompanyModel.onboarding_completed`** (novo `Column(Boolean, default=False)`).

### Lista canônica de módulos (constante compartilhada, backend e frontend)

```
dashboard, kanban, equipe, financeiro, fornecedores, configuracoes, exportacao, ia
```
(Os mesmos 8 itens do Hub Empresarial hoje gateados por cargo em `Layout.tsx`. O Hub Pessoal não entra — é escopo individual, não corporativo, não faz sentido ter "cargo" ali.)

**Nota sobre `dashboard` e `kanban`**: esses dois módulos aparecem na matriz (pra Admin poder ver/ajustar tudo num só lugar), mas não têm um endpoint de backend 1:1 pra gatear — o Dashboard agrega dados de outras rotas já protegidas por seus próprios módulos, e Kanban fica sem gate por decisão explícita (ver acima). Desmarcar `dashboard` só esconde o item do menu, sem bloquear nada no servidor. Isso é uma limitação conhecida e aceitável — os dois já vêm marcados por padrão pra todos os cargos e não é um caso de uso esperado desmarcá-los.

### Permissões padrão (seed, replica o comportamento hardcoded atual — zero regressão)

| Módulo | Admin | Gerente | Funcionário |
|---|---|---|---|
| dashboard | ✅ (implícito) | ✅ | ✅ |
| kanban | ✅ | ✅ | ✅ |
| equipe | ✅ | ✅ | ❌ |
| financeiro | ✅ | ✅ | ❌ |
| fornecedores | ✅ | ✅ | ❌ |
| configuracoes | ✅ | ❌ | ❌ |
| exportacao | ✅ | ✅ | ❌ |
| ia | ✅ | ✅ | ❌ |

### Autorização no backend

Nova dependência em `app/core/security.py` (ou novo `app/core/permissions.py`, a decidir na hora da implementação conforme tamanho):

```python
def require_module(module_key: str):
    async def _check(u=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
        if u["role"] == "ADMIN":
            return u
        exists = await db.execute(
            select(RolePermissionModel).where(
                RolePermissionModel.company_id == u["company_id"],
                RolePermissionModel.role == u["role"],
                RolePermissionModel.module_key == module_key,
            )
        )
        if not exists.scalar_one_or_none():
            raise HTTPException(403, "Seu cargo não tem acesso a este módulo")
        return u
    return _check
```

Aplicada como `Depends(require_module("financeiro"))` (em conjunto com `Depends(get_current_user)` onde já usado) nos routers: `employees.py` → `equipe`, `financial.py` → `financeiro`, `suppliers.py` → `fornecedores`, `exports.py` → `exportacao`, `ai.py` → `ia`. `kanban.py` fica de fora — todos os cargos têm acesso por padrão, e não há necessidade de gate por enquanto.

Em `company.py`, **atenção a uma exceção importante**: `GET /company/` **não** leva o gate de `configuracoes` — precisa continuar acessível a qualquer usuário autenticado, porque `Login.tsx`/`Register.tsx` o chamam para todo mundo (inclusive Gerente/Funcionário) só para ler `onboarding_completed` e o contexto básico da empresa. Só as rotas que **alteram** configuração — `PUT /company/`, `POST`/`GET`/`DELETE` de `/company/categories` e `/company/cost-centers`, e `GET`/`PUT /company/calendar` — levam `Depends(require_module("configuracoes"))`.

### Novos endpoints

- `app/api/v1/endpoints/permissions.py` (novo router, prefixo `/permissions`):
  - `GET /permissions/matrix` — admin-only, retorna a matriz completa `{GERENTE: [module_keys], FUNCIONARIO: [module_keys]}` da empresa do usuário (preenche com o padrão se a empresa ainda não tiver linhas customizadas).
  - `PUT /permissions/matrix` — admin-only, substitui as linhas da empresa pelo payload enviado.
  - `GET /permissions/mine` — qualquer usuário autenticado, retorna a lista de módulos do **seu próprio** cargo (ADMIN recebe a lista completa, fixa). Usado pelo `Layout.tsx` pra montar o menu.

- `app/api/v1/endpoints/system.py` (novo router, prefixo `/system`):
  - `GET /system/integrations` — admin-only. Testa `SELECT 1` no banco (reporta dialeto + host, Online/Offline) e reporta se `GEMINI_API_KEY` está configurada (sem chamar a API de verdade). Sem Redis (ver bug crítico acima).

- `app/api/v1/endpoints/company.py`:
  - `GET /company/` passa a incluir `onboarding_completed` na resposta.
  - `POST /company/onboarding/complete` — admin-only, marca `onboarding_completed = True`.

### Migração de schema

O projeto usa `Base.metadata.create_all` (sem Alembic) — não altera tabelas existentes. As tabelas novas (e a coluna nova em `companies`) só aparecem recriando o banco do zero. Isso será feito na hora de implementar (apagar `techconnect.db` local / recriar o volume MySQL), do mesmo jeito que já foi feito na troca pra MySQL.

### Seed

- Popula `role_permissions` com a tabela padrão acima, para a empresa de demonstração.
- `onboarding_completed = True` para a empresa de demonstração (a conta usada em apresentações **não** deve cair no wizard).

---

## Parte 2 — Frontend

### Componentes novos e compartilhados

- **`PermissionMatrix.tsx`** — a grade de checkboxes (módulos × Admin/Gerente/Funcionário, coluna Admin travada em "marcado"). Usado dentro de `Configuracoes.tsx` e dentro do wizard.
- **`IntegrationsStatus.tsx`** — os cards de status (Banco de Dados, IA Gemini), com botão "Testar Conexão". Usado nos mesmos dois lugares.

### `Configuracoes.tsx` — duas abas novas (total 6)

- **Hierarquia de Cargos**: `PermissionMatrix` + botão Salvar → `PUT /permissions/matrix`.
- **Conexões de API**: `IntegrationsStatus`, somente leitura.

### `Onboarding.tsx` (página nova, rota `/onboarding`)

Wizard de 3 passos com indicador de progresso:
1. **Dados da Empresa** — mesmo formulário já existente (nome, CNPJ, e-mail, telefone, endereço).
2. **Hierarquia de Cargos** — `PermissionMatrix`.
3. **Conexões de API** — `IntegrationsStatus` (informativo, não bloqueia o avanço mesmo se algo estiver offline — é uma confirmação, não um requisito duro).

Botão final "Concluir Configuração" → `POST /company/onboarding/complete` → atualiza o estado local → redireciona para `/dashboard`.

### Roteamento e guarda de onboarding

- `App.tsx`: nova rota `/onboarding` (`PrivateRoute`).
- `PrivateRoute` (em `App.tsx`) passa a checar, além do token: se `user.role === 'ADMIN'` e a empresa armazenada tem `onboarding_completed === false` e a rota atual não é `/onboarding`, redireciona para `/onboarding`. Gerente e Funcionário nunca são redirecionados para lá — só o Admin passa pelo wizard, e só quando pendente.
- `Login.tsx` e `Register.tsx`: após autenticar, além de `user`, passam a buscar e guardar os dados da empresa (`GET /company/`) em `localStorage`, para o `PrivateRoute` conseguir checar `onboarding_completed` sem um fetch extra a cada troca de rota. Atualizado novamente assim que o wizard é concluído.

### `Layout.tsx` — menu lateral dirigido por permissão real

Os itens do Hub Empresarial (`businessNavItems`) deixam de usar `user.role !== 'FUNCIONARIO'` hardcoded e passam a filtrar pela lista retornada por `GET /permissions/mine` (buscada uma vez ao montar o Layout, junto com a contagem de notificações que já é buscada hoje). ADMIN continua com acesso total, sem precisar da chamada.

---

## Jornada completa do usuário (validação end-to-end do design)

1. Empresa se cadastra em `/cadastro` → conta Admin criada, empresa nasce com `onboarding_completed=False` e sem linhas em `role_permissions` (usa os padrões da tabela acima até serem customizados).
2. Primeiro login do Admin → `PrivateRoute` detecta onboarding pendente → redireciona para `/onboarding`.
3. Admin passa pelos 3 passos, conclui → empresa marcada como configurada → cai no Dashboard.
4. Admin cadastra um Gerente em Gestão de Equipe → esse usuário loga normalmente (nunca vê `/onboarding`) → menu lateral mostra só os módulos liberados para Gerente.
5. Um mês depois, Admin decide que Gerente também deve ver Fornecedores → volta em Configurações → Hierarquia de Cargos → marca a caixa → salva → próximo login do Gerente já reflete isso (o filtro do menu é buscado a cada carregamento do Layout).
6. Se um Gerente tentar acessar `/api/v1/fornecedores/` diretamente sem essa permissão, recebe 403 do backend — não é só uma questão de esconder no menu.

---

## Fora de escopo (explicitamente, por decisão do usuário)

- Cargos customizáveis além de Admin/Gerente/Funcionário.
- Edição de credenciais reais (string de conexão do banco, chaves de API) pela interface.
- Auditoria geral de toda a lógica do sistema além do que foi encontrado no caminho (o bug do `/health`).
- 2FA, LGPD/auditoria, integração real com Gemini — já documentados como pendências conhecidas em sessões anteriores, não fazem parte deste design.
