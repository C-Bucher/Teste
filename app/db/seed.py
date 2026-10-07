"""Idempotent database seed.

Populates the database with the exact same demo data that
`app/db/database.py`'s in-memory mock lists contained, so the demo
experience is unchanged after the swap from in-memory lists to real
SQLAlchemy persistence.

`seed_if_empty()` is called once from `app/main.py`'s startup event. It
checks whether the `users` table already has rows; if so it no-ops, so
restarting the backend never creates duplicate rows.

Intentionally NOT seeded:
- `active_timers`: runtime state persisted only when a user starts a timer.
- `PERSONAL_TIMEBOXES` / `PERSONAL_OKRS`: empty lists in the mock. The
  tables exist (via Task 2's models) for later routers to write into,
  but there is nothing to seed.
"""

from datetime import datetime, timedelta, date

import bcrypt
from sqlalchemy import event, select

from app.core.legal import TERMS_VERSION

from app.db.session import async_session_maker
from app.db.models import (
    CompanyModel,
    UserModel,
    RolePermissionModel,
    EmployeeModel,
    SalaryHistoryModel,
    SupplierModel,
    FinancialEntryModel,
    ClientModel,
    ProjectModel,
    KanbanColumnModel,
    KanbanCardModel,
    NotificationModel,
    CostCenterModel,
    CategoryModel,
    PersonalEntryModel,
    PersonalCategoryModel,
    PersonalAccountModel,
    PersonalBudgetModel,
    PersonalGoalModel,
    PersonalDebtModel,
    PersonalSubscriptionModel,
    PersonalSplitModel,
)
from app.core.permissions import DEFAULT_PERMISSIONS

hoje = date.today()


def dias(n: int) -> str:
    return (hoje + timedelta(days=n)).isoformat()


async def _seed_personal_categories_if_empty(session) -> None:
    """Idempotently seeds personal_categories on its own, independent of
    the users-table guard below.

    PersonalCategoryModel was added after the initial `seed_if_empty()`
    guard already shipped, so any database that was seeded before this
    change (users table non-empty) would otherwise never receive these
    rows — the top-level early return would skip them forever. Checking
    this table's own emptiness lets it self-heal on the next startup
    regardless of when the rest of the demo data was seeded.
    """
    result = await session.execute(select(PersonalCategoryModel).limit(1))
    if result.scalar_one_or_none() is not None:
        return  # already seeded, do nothing
    if await session.get(UserModel, DEMO_USER_ID) is None:
        return  # not a demo database; real users get their categories lazily (personal.py)
    session.add_all(
        [
            PersonalCategoryModel(id="pc-1", name="Salario", type="RECEITA"),
            PersonalCategoryModel(id="pc-2", name="Moradia", type="DESPESA"),
            PersonalCategoryModel(id="pc-3", name="Alimentacao", type="DESPESA"),
            PersonalCategoryModel(id="pc-4", name="Saude", type="DESPESA"),
        ]
    )


DEMO_COMPANY_ID = "cmp-001"
DEMO_USER_ID = "usr-001"


def _assign_demo_owner(session, _flush_context=None, _instances=None) -> None:
    """before_flush hook for the seed session only. Demo rows belong to the demo company/user;
    models have no default owner on purpose, so anything else that forgets company_id/owner_id
    fails instead of leaking into the demo account."""
    for obj in session.new:
        if hasattr(obj, "company_id") and obj.company_id is None:
            obj.company_id = DEMO_COMPANY_ID
        if hasattr(obj, "owner_id") and obj.owner_id is None:
            obj.owner_id = DEMO_USER_ID
        if isinstance(obj, UserModel) and obj.terms_version is None:
            obj.terms_version = TERMS_VERSION  # demo logins skip the acceptance screen
            obj.terms_accepted_at = datetime.utcnow().isoformat()


async def seed_if_empty() -> None:
    async with async_session_maker() as session:
        event.listen(session.sync_session, "before_flush", _assign_demo_owner)
        result = await session.execute(select(UserModel).limit(1))
        if result.scalar_one_or_none() is not None:
            # Base demo data already seeded. Still backfill any tables that
            # gained a seed requirement after that initial seed shipped.
            await _seed_personal_categories_if_empty(session)
            await session.commit()
            return

        # --- COMPANY (single row) ---------------------------------------
        session.add(
            CompanyModel(
                id="cmp-001",
                name="TechConnect Solucoes Ltda",
                cnpj="12.345.678/0001-90",
                email="contato@techconnect.com.br",
                phone="(61) 3344-5566",
                address="SHCGN 713 Bloco A - Brasilia/DF",
                fiscal_year_start=1,
                onboarding_completed=True,
            )
        )

        # --- USERS_DB ------------------------------------------------------
        admin_hash = bcrypt.hashpw(b"Admin@123", bcrypt.gensalt()).decode()
        gerente_hash = bcrypt.hashpw(b"Gerente@123", bcrypt.gensalt()).decode()
        func_hash = bcrypt.hashpw(b"Func@123", bcrypt.gensalt()).decode()
        session.add_all(
            [
                UserModel(id="usr-001", company_id="cmp-001", email="admin@techconnect.com.br", full_name="Administrador", role="ADMIN", plan_scope="completo", password_hash=admin_hash, is_active=True, mfa_enabled=False),
                UserModel(id="usr-002", company_id="cmp-001", email="gerente@techconnect.com.br", full_name="Ana Souza", role="GERENTE", plan_scope="completo", password_hash=gerente_hash, is_active=True, mfa_enabled=False),
                UserModel(id="usr-003", company_id="cmp-001", email="funcionario@techconnect.com.br", full_name="Carlos Mendes", role="FUNCIONARIO", plan_scope="completo", password_hash=func_hash, is_active=True, mfa_enabled=False),
            ]
        )

        # --- ROLE PERMISSIONS (empresa de demonstração) ---------------------
        session.add_all([
            RolePermissionModel(id=f"rp-seed-{role.lower()}-{module}", company_id="cmp-001", role=role, module_key=module)
            for role, modules in DEFAULT_PERMISSIONS.items()
            for module in modules
        ])

        # --- EMPLOYEES -------------------------------------------------------
        # Mock has both "start_date" and an identical "hire_date" - both are
        # plain String(20)/String(50) columns storing the same date-only
        # (YYYY-MM-DD) string, matching the old mock's serialization.
        session.add_all(
            [
                EmployeeModel(id="emp-001", full_name="Carlos Mendes", cpf="123.456.789-00", role="Desenvolvedor Senior", position="Desenvolvedor Senior", contract_type="CLT", base_salary=8500.00, ctc_snapshot=14875.00, ctc_monthly=14875.00, hourly_rate=85.00, hourly_cost=85.00, is_active=True, start_date="2024-03-01", hire_date="2024-03-01", email="carlos@tc.com"),
                EmployeeModel(id="emp-002", full_name="Beatriz Lima", cpf="234.567.890-11", role="Designer UX/UI", position="Designer UX/UI", contract_type="CLT", base_salary=6200.00, ctc_snapshot=10850.00, ctc_monthly=10850.00, hourly_rate=62.00, hourly_cost=62.00, is_active=True, start_date="2024-05-15", hire_date="2024-05-15", email="beatriz@tc.com"),
                EmployeeModel(id="emp-003", full_name="Rodrigo Santos", cpf="345.678.901-22", role="Analista Financeiro", position="Analista Financeiro", contract_type="CLT", base_salary=5800.00, ctc_snapshot=10150.00, ctc_monthly=10150.00, hourly_rate=58.00, hourly_cost=58.00, is_active=True, start_date="2024-07-01", hire_date="2024-07-01", email="rodrigo@tc.com"),
                EmployeeModel(id="emp-004", full_name="Fernanda Costa", cpf="456.789.012-33", role="Dev Backend", position="Dev Backend", contract_type="PJ", base_salary=12000.00, ctc_snapshot=13200.00, ctc_monthly=13200.00, hourly_rate=110.00, hourly_cost=110.00, is_active=True, start_date="2023-11-10", hire_date="2023-11-10", email="fernanda@tc.com"),
                EmployeeModel(id="emp-005", full_name="Lucas Oliveira", cpf="567.890.123-44", role="Estagiario Dev", position="Estagiario Dev", contract_type="ESTAGIO", base_salary=1500.00, ctc_snapshot=1800.00, ctc_monthly=1800.00, hourly_rate=12.50, hourly_cost=12.50, is_active=True, start_date="2025-02-01", hire_date="2025-02-01", email="lucas@tc.com"),
            ]
        )

        # Employees must be persisted before salary_history (FK employee_id).
        # SQLAlchemy's unit-of-work only auto-orders INSERTs by FK dependency
        # when an ORM relationship() is declared between the mapped classes;
        # this schema only uses raw ForeignKey columns, so ordering isn't
        # automatic. SQLite (previously used here) doesn't enforce FK
        # constraints by default, so an out-of-order flush was silently
        # accepted there; MySQL enforces them, so explicit flush()
        # checkpoints are required at each parent/child boundary below.
        await session.flush()

        # --- SALARY_HISTORY --------------------------------------------------
        # The old in-memory mock fabricated 2 history rows per employee on
        # every request (a "Reajuste anual" and a "Promocao" entry, each with
        # slightly lower prior salary values). The real SalaryHistoryModel
        # table only gets new rows written on creation/edit, so freshly
        # seeded employees need these backfilled here to keep the demo's
        # "Historico Salarial" modal non-empty out of the box.
        session.add_all(
            [
                SalaryHistoryModel(id="sh-emp-001-1", employee_id="emp-001", base_salary=7800.00, ctc_monthly=13650.00, ctc_snapshot=13650.00, changed_at=dias(-140), reason="Reajuste anual"),
                SalaryHistoryModel(id="sh-emp-001-2", employee_id="emp-001", base_salary=7200.00, ctc_monthly=12600.00, ctc_snapshot=12600.00, changed_at=dias(-280), reason="Promocao"),
                SalaryHistoryModel(id="sh-emp-002-1", employee_id="emp-002", base_salary=5700.00, ctc_monthly=9975.00, ctc_snapshot=9975.00, changed_at=dias(-140), reason="Reajuste anual"),
                SalaryHistoryModel(id="sh-emp-002-2", employee_id="emp-002", base_salary=5200.00, ctc_monthly=9100.00, ctc_snapshot=9100.00, changed_at=dias(-280), reason="Promocao"),
                SalaryHistoryModel(id="sh-emp-003-1", employee_id="emp-003", base_salary=5400.00, ctc_monthly=9450.00, ctc_snapshot=9450.00, changed_at=dias(-140), reason="Reajuste anual"),
                SalaryHistoryModel(id="sh-emp-003-2", employee_id="emp-003", base_salary=5000.00, ctc_monthly=8750.00, ctc_snapshot=8750.00, changed_at=dias(-280), reason="Promocao"),
                SalaryHistoryModel(id="sh-emp-004-1", employee_id="emp-004", base_salary=11200.00, ctc_monthly=12320.00, ctc_snapshot=12320.00, changed_at=dias(-140), reason="Reajuste anual"),
                SalaryHistoryModel(id="sh-emp-004-2", employee_id="emp-004", base_salary=10500.00, ctc_monthly=11550.00, ctc_snapshot=11550.00, changed_at=dias(-280), reason="Promocao"),
                SalaryHistoryModel(id="sh-emp-005-1", employee_id="emp-005", base_salary=1400.00, ctc_monthly=1680.00, ctc_snapshot=1680.00, changed_at=dias(-140), reason="Reajuste anual"),
                SalaryHistoryModel(id="sh-emp-005-2", employee_id="emp-005", base_salary=1200.00, ctc_monthly=1440.00, ctc_snapshot=1440.00, changed_at=dias(-280), reason="Promocao"),
            ]
        )

        # --- SUPPLIERS ---------------------------------------------------
        session.add_all(
            [
                SupplierModel(id="sup-001", name="AWS Brasil", cnpj_cpf="16.670.085/0001-55", category="Cloud", is_active=True, email="billing@aws.com"),
                SupplierModel(id="sup-002", name="Conta Simples", cnpj_cpf="29.925.802/0001-78", category="Bancario", is_active=True, email="suporte@cs.com"),
                SupplierModel(id="sup-003", name="GitHub Inc", cnpj_cpf="01.914.829/0001-39", category="Dev Tools", is_active=True, email="billing@github.com"),
                SupplierModel(id="sup-004", name="Contabilidade Faria", cnpj_cpf="12.345.678/0001-90", category="Contabilidade", is_active=True, email="faria@cont.com.br"),
                SupplierModel(id="sup-005", name="Aluguel Comercial SA", cnpj_cpf="98.765.432/0001-10", category="Aluguel", is_active=True, email="contato@aluguel.com.br"),
            ]
        )

        await session.flush()  # suppliers must exist before financial_entries FK

        # --- FINANCIAL_ENTRIES ---------------------------------------------
        session.add_all(
            [
                FinancialEntryModel(id="fin-001", type="RECEITA", amount=28500.00, description="Projeto Website Varejo - Fase 1", due_date=dias(-5), payment_date=dias(-5), status="PAGO", category="Desenvolvimento", supplier_id=None, cost_center="Tecnologia"),
                FinancialEntryModel(id="fin-002", type="RECEITA", amount=15000.00, description="Consultoria Digital", due_date=dias(5), payment_date=None, status="PENDENTE", category="Consultoria", supplier_id=None, cost_center="Comercial"),
                FinancialEntryModel(id="fin-003", type="RECEITA", amount=9800.00, description="Manutencao ERP - Marco", due_date=dias(-15), payment_date=dias(-15), status="PAGO", category="Suporte", supplier_id=None, cost_center="Tecnologia"),
                FinancialEntryModel(id="fin-004", type="DESPESA", amount=4200.00, description="AWS - Infraestrutura Cloud", due_date=dias(-3), payment_date=dias(-3), status="PAGO", category="Infraestrutura", supplier_id="sup-001", cost_center="Tecnologia"),
                FinancialEntryModel(id="fin-005", type="DESPESA", amount=8500.00, description="Folha de Pagamento - Marco", due_date=dias(-10), payment_date=dias(-10), status="PAGO", category="Pessoal", supplier_id="sup-002", cost_center="Administrativo"),
                FinancialEntryModel(id="fin-006", type="DESPESA", amount=650.00, description="GitHub Enterprise", due_date=dias(2), payment_date=None, status="PENDENTE", category="Ferramentas", supplier_id="sup-003", cost_center="Tecnologia"),
                FinancialEntryModel(id="fin-007", type="DESPESA", amount=2800.00, description="Contabilidade Mensal", due_date=dias(8), payment_date=None, status="PENDENTE", category="Contabilidade", supplier_id="sup-004", cost_center="Administrativo"),
                FinancialEntryModel(id="fin-008", type="DESPESA", amount=3500.00, description="Aluguel Escritorio", due_date=dias(15), payment_date=None, status="PENDENTE", category="Aluguel", supplier_id="sup-005", cost_center="Administrativo"),
                FinancialEntryModel(id="fin-009", type="RECEITA", amount=42000.00, description="Contrato Anual SaaS", due_date=dias(20), payment_date=None, status="PENDENTE", category="SaaS", supplier_id=None, cost_center="Comercial"),
                FinancialEntryModel(id="fin-010", type="DESPESA", amount=490.00, description="Figma Professional", due_date=dias(-1), payment_date=dias(-1), status="PAGO", category="Design", supplier_id="sup-003", cost_center="Tecnologia"),
                FinancialEntryModel(id="fin-011", type="RECEITA", amount=7200.00, description="Suporte Tecnico - Cliente C", due_date=dias(-8), payment_date=dias(-8), status="PAGO", category="Suporte", supplier_id=None, cost_center="Tecnologia"),
                FinancialEntryModel(id="fin-012", type="DESPESA", amount=1200.00, description="Treinamento Equipe", due_date=dias(25), payment_date=None, status="PENDENTE", category="Capacitacao", supplier_id="sup-002", cost_center="Administrativo"),
            ]
        )

        # --- KANBAN_CLIENTS ------------------------------------------------
        session.add_all(
            [
                ClientModel(id="cli-001", name="Varejo Express Ltda", email="ti@varejo.com.br", phone="(11) 3456-7890", cnpj="12.345.678/0001-90", contact_name="João Silva", address="Av. Paulista, 1000 - São Paulo, SP", segment="Varejo", status="ATIVO"),
                ClientModel(id="cli-002", name="FinTech Solutions SA", email="dev@fintech.com.br", phone="(11) 9876-5432", cnpj="98.765.432/0001-10", contact_name="Maria Santos", address="Rua da Consolação, 500 - São Paulo, SP", segment="Financeiro", status="ATIVO"),
                ClientModel(id="cli-003", name="LogiTech Transportes", email="ops@logitech.com.br", phone="(11) 2233-4455", cnpj="11.222.333/0001-44", contact_name="Pedro Costa", address="Rod. Anhanguera, km 15 - Campinas, SP", segment="Logística", status="ATIVO"),
            ]
        )

        await session.flush()  # clients must exist before projects FK

        # --- KANBAN_PROJECTS -------------------------------------------------
        session.add_all(
            [
                ProjectModel(id="proj-001", client_id="cli-001", name="Website Redesign", description="Redesign completo do portal de vendas e checkout", status="EM_ANDAMENTO", start_date="2026-04-01", end_date="2026-06-30"),
                ProjectModel(id="proj-002", client_id="cli-002", name="API Gateway v2", description="Migracao para arquitetura de microsservicos", status="EM_ANDAMENTO", start_date="2026-03-15", end_date="2026-07-15"),
                ProjectModel(id="proj-003", client_id="cli-003", name="App Rastreamento", description="Aplicativo mobile de rastreamento de frota", status="PLANEJAMENTO", start_date="2026-06-01", end_date="2026-09-30"),
            ]
        )

        # --- KANBAN_BOARDS: unpack {project_id: {"columns":[{...,"cards":[...]}]}} --
        kanban_boards = {
            "proj-001": {"columns": [
                {"id": "col-001", "name": "Backlog", "order": 1, "cards": [
                    {"id": "card-001", "title": "Levantamento de Requisitos", "description": "Mapeamento completo das necessidades do cliente", "assignee": "Carlos Mendes", "assignee_id": "emp-001", "cost_per_task": 680.00, "total_time_seconds": 28800, "status": "CONCLUIDO", "priority": "ALTA", "due_date": dias(-20)},
                    {"id": "card-002", "title": "Wireframes e Prototipos", "description": "Prototipacao de todas as telas no Figma", "assignee": "Beatriz Lima", "assignee_id": "emp-002", "cost_per_task": 248.00, "total_time_seconds": 14400, "status": "CONCLUIDO", "priority": "ALTA", "due_date": dias(-15)},
                ]},
                {"id": "col-002", "name": "Em Desenvolvimento", "order": 2, "cards": [
                    {"id": "card-003", "title": "Header, Footer e Menu de Navegacao", "description": "Implementacao dos componentes globais de navegacao", "assignee": "Carlos Mendes", "assignee_id": "emp-001", "cost_per_task": 425.00, "total_time_seconds": 18000, "status": "EM_ANDAMENTO", "priority": "ALTA", "due_date": dias(5)},
                    {"id": "card-004", "title": "Pagina de Produtos e Catalogo", "description": "Listagem, filtros e busca de produtos", "assignee": "Beatriz Lima", "assignee_id": "emp-002", "cost_per_task": 310.00, "total_time_seconds": 18000, "status": "EM_ANDAMENTO", "priority": "MEDIA", "due_date": dias(8)},
                    {"id": "card-007", "title": "Checkout e Pagamento", "description": "Integracao com gateway de pagamento", "assignee": "Fernanda Costa", "assignee_id": "emp-004", "cost_per_task": 890.00, "total_time_seconds": 7200, "status": "EM_ANDAMENTO", "priority": "URGENTE", "due_date": dias(3)},
                ]},
                {"id": "col-003", "name": "Em Revisao", "order": 3, "cards": [
                    {"id": "card-005", "title": "Testes de Responsividade", "description": "Validacao em mobile, tablet e desktop", "assignee": "Rodrigo Santos", "assignee_id": "emp-003", "cost_per_task": 174.00, "total_time_seconds": 10800, "status": "EM_REVISAO", "priority": "MEDIA", "due_date": dias(2)},
                ]},
                {"id": "col-004", "name": "Concluido", "order": 4, "cards": [
                    {"id": "card-008", "title": "Setup do Ambiente", "description": "Configuracao de repositorio e CI", "assignee": "Carlos Mendes", "assignee_id": "emp-001", "cost_per_task": 120.00, "total_time_seconds": 3600, "status": "CONCLUIDO", "priority": "BAIXA", "due_date": dias(-25)},
                ]},
            ]},
            "proj-002": {"columns": [
                {"id": "col-005", "name": "Backlog", "order": 1, "cards": [
                    {"id": "card-009", "title": "Documentacao da API", "description": "Swagger e documentacao de todos os endpoints", "assignee": "Lucas Oliveira", "assignee_id": "emp-005", "cost_per_task": 75.00, "total_time_seconds": 0, "status": "ABERTO", "priority": "BAIXA", "due_date": dias(20)},
                ]},
                {"id": "col-006", "name": "Em Desenvolvimento", "order": 2, "cards": [
                    {"id": "card-006", "title": "Auth Microservice - JWT + MFA", "description": "Servico de autenticacao com suporte a MFA e refresh tokens", "assignee": "Fernanda Costa", "assignee_id": "emp-004", "cost_per_task": 1320.00, "total_time_seconds": 43200, "status": "EM_ANDAMENTO", "priority": "URGENTE", "due_date": dias(4)},
                    {"id": "card-010", "title": "API Gateway - Rate Limiting", "description": "Implementacao de rate limiting e circuit breaker", "assignee": "Carlos Mendes", "assignee_id": "emp-001", "cost_per_task": 680.00, "total_time_seconds": 21600, "status": "EM_ANDAMENTO", "priority": "ALTA", "due_date": dias(7)},
                ]},
                {"id": "col-007", "name": "QA / Testes", "order": 3, "cards": [
                    {"id": "card-011", "title": "Testes de Carga", "description": "Stress test com 10k requisicoes/s", "assignee": "Rodrigo Santos", "assignee_id": "emp-003", "cost_per_task": 290.00, "total_time_seconds": 14400, "status": "EM_REVISAO", "priority": "ALTA", "due_date": dias(1)},
                ]},
                {"id": "col-008", "name": "Concluido", "order": 4, "cards": []},
            ]},
            "proj-003": {"columns": [
                {"id": "col-009", "name": "Backlog", "order": 1, "cards": [
                    {"id": "card-012", "title": "Briefing e Escopo", "description": "Definicao do escopo e cronograma do app", "assignee": "Rodrigo Santos", "assignee_id": "emp-003", "cost_per_task": 0, "total_time_seconds": 0, "status": "ABERTO", "priority": "ALTA", "due_date": dias(15)},
                    {"id": "card-013", "title": "Arquitetura React Native", "description": "Definir stack mobile e patterns", "assignee": "Fernanda Costa", "assignee_id": "emp-004", "cost_per_task": 0, "total_time_seconds": 0, "status": "ABERTO", "priority": "MEDIA", "due_date": dias(18)},
                ]},
                {"id": "col-010", "name": "Em Andamento", "order": 2, "cards": []},
                {"id": "col-011", "name": "Revisao", "order": 3, "cards": []},
                {"id": "col-012", "name": "Concluido", "order": 4, "cards": []},
            ]},
        }

        await session.flush()  # projects must exist before kanban_columns FK

        for project_id, board in kanban_boards.items():
            for col in board["columns"]:
                session.add(
                    KanbanColumnModel(
                        id=col["id"],
                        project_id=project_id,
                        name=col["name"],
                        order=col["order"],
                    )
                )
                await session.flush()  # column must exist before its cards' FK
                for card in col["cards"]:
                    session.add(
                        KanbanCardModel(
                            id=card["id"],
                            column_id=col["id"],
                            title=card["title"],
                            description=card["description"],
                            assignee=card["assignee"],
                            assignee_id=card["assignee_id"],
                            cost_per_task=card["cost_per_task"],
                            total_time_seconds=card["total_time_seconds"],
                            status=card["status"],
                            priority=card["priority"],
                            due_date=card["due_date"],
                        )
                    )

        # Active timers are created only by explicit user action.

        # --- NOTIFICATIONS ---------------------------------------------------
        session.add_all(
            [
                NotificationModel(id="ntf-001", title="Lancamento Vencendo", message="Aluguel Escritorio vence em 15 dias - R$ 3.500,00", type="WARNING", is_read=False, created_at=datetime.now().isoformat()),
                NotificationModel(id="ntf-002", title="Pagamento Recebido", message="Projeto Website Varejo - R$ 28.500,00 confirmado", type="SUCCESS", is_read=False, created_at=(datetime.now() - timedelta(hours=2)).isoformat()),
                NotificationModel(id="ntf-003", title="Card Atualizado", message="Fernanda Costa moveu Auth Microservice", type="INFO", is_read=True, created_at=(datetime.now() - timedelta(hours=5)).isoformat()),
                NotificationModel(id="ntf-004", title="Alerta CTC", message="Parametros INSS atualizados", type="WARNING", is_read=True, created_at=(datetime.now() - timedelta(days=1)).isoformat()),
            ]
        )

        # --- COST_CENTERS ----------------------------------------------------
        session.add_all(
            [
                CostCenterModel(id="cc-001", name="Tecnologia", code="TECH"),
                CostCenterModel(id="cc-002", name="Administrativo", code="ADM"),
                CostCenterModel(id="cc-003", name="Comercial", code="COM"),
            ]
        )

        # --- CATEGORIES --------------------------------------------------------
        session.add_all(
            [
                CategoryModel(id="cat-001", name="Desenvolvimento", type="RECEITA"),
                CategoryModel(id="cat-002", name="Consultoria", type="RECEITA"),
                CategoryModel(id="cat-003", name="Suporte", type="RECEITA"),
                CategoryModel(id="cat-004", name="SaaS", type="RECEITA"),
                CategoryModel(id="cat-005", name="Infraestrutura", type="DESPESA"),
                CategoryModel(id="cat-006", name="Pessoal", type="DESPESA"),
                CategoryModel(id="cat-007", name="Aluguel", type="DESPESA"),
                CategoryModel(id="cat-008", name="Ferramentas", type="DESPESA"),
                CategoryModel(id="cat-009", name="Contabilidade", type="DESPESA"),
            ]
        )

        # --- PERSONAL_ENTRIES -------------------------------------------------
        session.add_all(
            [
                PersonalEntryModel(id="pes-001", type="RECEITA", amount=8500.00, description="Salario Marco", date=dias(-5), category="Salario"),
                PersonalEntryModel(id="pes-002", type="DESPESA", amount=1800.00, description="Aluguel Apartamento", date=dias(-3), category="Moradia"),
                PersonalEntryModel(id="pes-003", type="DESPESA", amount=650.00, description="Supermercado", date=dias(-2), category="Alimentacao"),
                PersonalEntryModel(id="pes-004", type="DESPESA", amount=320.00, description="Plano de Saude", date=dias(-1), category="Saude"),
            ]
        )

        # --- PERSONAL_CATEGORIES -----------------------------------------------
        # Not a `database.py` mock list — this was a hardcoded literal inside
        # personal.py's GET /personal/categories endpoint (pre-Task 12
        # migration). See _seed_personal_categories_if_empty() above for why
        # this has its own independent idempotency check.
        await _seed_personal_categories_if_empty(session)

        # --- PERSONAL_ACCOUNTS --------------------------------------------------
        session.add_all(
            [
                PersonalAccountModel(id="pacc-001", name="Conta Corrente Nubank", type="CONTA", balance=4250.30, limit=None),
                PersonalAccountModel(id="pacc-002", name="Cartão Nubank", type="CARTAO", balance=-890.40, limit=5000.00, closing_day=28, due_day=5),
            ]
        )

        # --- PERSONAL_BUDGETS ------------------------------------------------
        session.add_all(
            [
                PersonalBudgetModel(id="pbud-001", category="Alimentacao", limit_amount=1200.00, spent_amount=650.00),
                PersonalBudgetModel(id="pbud-002", category="Transporte", limit_amount=500.00, spent_amount=410.00),
                PersonalBudgetModel(id="pbud-003", category="Lazer", limit_amount=400.00, spent_amount=390.00),
            ]
        )

        # --- PERSONAL_GOALS --------------------------------------------------
        session.add_all(
            [
                PersonalGoalModel(id="pgoal-001", name="Reserva de Emergencia", target_amount=20000.00, current_amount=8500.00, target_date="2027-01-01"),
                PersonalGoalModel(id="pgoal-002", name="Viagem Europa", target_amount=12000.00, current_amount=3200.00, target_date="2026-12-01"),
            ]
        )

        # --- PERSONAL_DEBTS --------------------------------------------------
        session.add_all(
            [
                PersonalDebtModel(id="pdebt-001", name="Financiamento Notebook", total_amount=4800.00, remaining_amount=2400.00, installments_total=12, installments_paid=6, interest_rate=2.5),
            ]
        )

        # --- PERSONAL_SUBSCRIPTIONS --------------------------------------------
        session.add_all(
            [
                PersonalSubscriptionModel(id="psub-001", name="Netflix", amount=39.90, billing_day=10, category="Streaming", is_active=True),
                PersonalSubscriptionModel(id="psub-002", name="Academia", amount=99.90, billing_day=5, category="Saude", is_active=True),
            ]
        )

        # --- PERSONAL_SPLITS (participants -> JSON column) --------------------
        session.add_all(
            [
                PersonalSplitModel(
                    id="psplit-001",
                    description="Aluguel Republica",
                    total_amount=1800.00,
                    participants=[
                        {"name": "Voce", "share": 600.00, "paid": True},
                        {"name": "Joao", "share": 600.00, "paid": False},
                        {"name": "Maria", "share": 600.00, "paid": True},
                    ],
                ),
            ]
        )

        # PERSONAL_TIMEBOXES / PERSONAL_OKRS are empty lists in the mock —
        # nothing to seed; tables exist via PersonalTimeboxModel /
        # PersonalOkrModel for later routers to write into.

        await session.commit()
