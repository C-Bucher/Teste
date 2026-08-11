from datetime import datetime, timedelta, date
import bcrypt

ADMIN_HASH = bcrypt.hashpw(b"Admin@123", bcrypt.gensalt()).decode()
USERS_DB = {
    "admin@techconnect.com.br": {"id":"usr-001","email":"admin@techconnect.com.br","full_name":"Administrador","role":"ADMIN","password_hash":ADMIN_HASH,"is_active":True,"mfa_enabled":False},
    "gerente@techconnect.com.br": {"id":"usr-002","email":"gerente@techconnect.com.br","full_name":"Ana Souza","role":"GERENTE","password_hash":bcrypt.hashpw(b"Gerente@123",bcrypt.gensalt()).decode(),"is_active":True,"mfa_enabled":False},
    "funcionario@techconnect.com.br": {"id":"usr-003","email":"funcionario@techconnect.com.br","full_name":"Carlos Mendes","role":"FUNCIONARIO","password_hash":bcrypt.hashpw(b"Func@123",bcrypt.gensalt()).decode(),"is_active":True,"mfa_enabled":False},
}

hoje = date.today()
def dias(n): return (hoje + timedelta(days=n)).isoformat()

EMPLOYEES = [
    {"id":"emp-001","full_name":"Carlos Mendes","cpf":"123.456.789-00","role":"Desenvolvedor Senior","position":"Desenvolvedor Senior","contract_type":"CLT","base_salary":8500.00,"ctc_snapshot":14875.00,"ctc_monthly":14875.00,"hourly_rate":85.00,"hourly_cost":85.00,"is_active":True,"start_date":"2024-03-01","hire_date":"2024-03-01","email":"carlos@tc.com"},
    {"id":"emp-002","full_name":"Beatriz Lima","cpf":"234.567.890-11","role":"Designer UX/UI","position":"Designer UX/UI","contract_type":"CLT","base_salary":6200.00,"ctc_snapshot":10850.00,"ctc_monthly":10850.00,"hourly_rate":62.00,"hourly_cost":62.00,"is_active":True,"start_date":"2024-05-15","hire_date":"2024-05-15","email":"beatriz@tc.com"},
    {"id":"emp-003","full_name":"Rodrigo Santos","cpf":"345.678.901-22","role":"Analista Financeiro","position":"Analista Financeiro","contract_type":"CLT","base_salary":5800.00,"ctc_snapshot":10150.00,"ctc_monthly":10150.00,"hourly_rate":58.00,"hourly_cost":58.00,"is_active":True,"start_date":"2024-07-01","hire_date":"2024-07-01","email":"rodrigo@tc.com"},
    {"id":"emp-004","full_name":"Fernanda Costa","cpf":"456.789.012-33","role":"Dev Backend","position":"Dev Backend","contract_type":"PJ","base_salary":12000.00,"ctc_snapshot":13200.00,"ctc_monthly":13200.00,"hourly_rate":110.00,"hourly_cost":110.00,"is_active":True,"start_date":"2023-11-10","hire_date":"2023-11-10","email":"fernanda@tc.com"},
    {"id":"emp-005","full_name":"Lucas Oliveira","cpf":"567.890.123-44","role":"Estagiario Dev","position":"Estagiario Dev","contract_type":"ESTAGIO","base_salary":1500.00,"ctc_snapshot":1800.00,"ctc_monthly":1800.00,"hourly_rate":12.50,"hourly_cost":12.50,"is_active":True,"start_date":"2025-02-01","hire_date":"2025-02-01","email":"lucas@tc.com"},
]
SUPPLIERS = [
    {"id":"sup-001","name":"AWS Brasil","cnpj_cpf":"16.670.085/0001-55","category":"Cloud","is_active":True,"email":"billing@aws.com"},
    {"id":"sup-002","name":"Conta Simples","cnpj_cpf":"29.925.802/0001-78","category":"Bancario","is_active":True,"email":"suporte@cs.com"},
    {"id":"sup-003","name":"GitHub Inc","cnpj_cpf":"01.914.829/0001-39","category":"Dev Tools","is_active":True,"email":"billing@github.com"},
    {"id":"sup-004","name":"Contabilidade Faria","cnpj_cpf":"12.345.678/0001-90","category":"Contabilidade","is_active":True,"email":"faria@cont.com.br"},
    {"id":"sup-005","name":"Aluguel Comercial SA","cnpj_cpf":"98.765.432/0001-10","category":"Aluguel","is_active":True,"email":"contato@aluguel.com.br"},
]
FINANCIAL_ENTRIES = [
    {"id":"fin-001","type":"RECEITA","amount":28500.00,"description":"Projeto Website Varejo - Fase 1","due_date":dias(-5),"payment_date":dias(-5),"status":"PAGO","category":"Desenvolvimento","supplier_id":None,"cost_center":"Tecnologia"},
    {"id":"fin-002","type":"RECEITA","amount":15000.00,"description":"Consultoria Digital","due_date":dias(5),"payment_date":None,"status":"PENDENTE","category":"Consultoria","supplier_id":None,"cost_center":"Comercial"},
    {"id":"fin-003","type":"RECEITA","amount":9800.00,"description":"Manutencao ERP - Marco","due_date":dias(-15),"payment_date":dias(-15),"status":"PAGO","category":"Suporte","supplier_id":None,"cost_center":"Tecnologia"},
    {"id":"fin-004","type":"DESPESA","amount":4200.00,"description":"AWS - Infraestrutura Cloud","due_date":dias(-3),"payment_date":dias(-3),"status":"PAGO","category":"Infraestrutura","supplier_id":"sup-001","cost_center":"Tecnologia"},
    {"id":"fin-005","type":"DESPESA","amount":8500.00,"description":"Folha de Pagamento - Marco","due_date":dias(-10),"payment_date":dias(-10),"status":"PAGO","category":"Pessoal","supplier_id":"sup-002","cost_center":"Administrativo"},
    {"id":"fin-006","type":"DESPESA","amount":650.00,"description":"GitHub Enterprise","due_date":dias(2),"payment_date":None,"status":"PENDENTE","category":"Ferramentas","supplier_id":"sup-003","cost_center":"Tecnologia"},
    {"id":"fin-007","type":"DESPESA","amount":2800.00,"description":"Contabilidade Mensal","due_date":dias(8),"payment_date":None,"status":"PENDENTE","category":"Contabilidade","supplier_id":"sup-004","cost_center":"Administrativo"},
    {"id":"fin-008","type":"DESPESA","amount":3500.00,"description":"Aluguel Escritorio","due_date":dias(15),"payment_date":None,"status":"PENDENTE","category":"Aluguel","supplier_id":"sup-005","cost_center":"Administrativo"},
    {"id":"fin-009","type":"RECEITA","amount":42000.00,"description":"Contrato Anual SaaS","due_date":dias(20),"payment_date":None,"status":"PENDENTE","category":"SaaS","supplier_id":None,"cost_center":"Comercial"},
    {"id":"fin-010","type":"DESPESA","amount":490.00,"description":"Figma Professional","due_date":dias(-1),"payment_date":dias(-1),"status":"PAGO","category":"Design","supplier_id":"sup-003","cost_center":"Tecnologia"},
    {"id":"fin-011","type":"RECEITA","amount":7200.00,"description":"Suporte Tecnico - Cliente C","due_date":dias(-8),"payment_date":dias(-8),"status":"PAGO","category":"Suporte","supplier_id":None,"cost_center":"Tecnologia"},
    {"id":"fin-012","type":"DESPESA","amount":1200.00,"description":"Treinamento Equipe","due_date":dias(25),"payment_date":None,"status":"PENDENTE","category":"Capacitacao","supplier_id":"sup-002","cost_center":"Administrativo"},
]
KANBAN_CLIENTS = [
    {"id":"cli-001","name":"Varejo Express Ltda","email":"ti@varejo.com.br","phone":"(11) 3456-7890","cnpj":"12.345.678/0001-90","contact_name":"João Silva","address":"Av. Paulista, 1000 - São Paulo, SP","segment":"Varejo","status":"ATIVO"},
    {"id":"cli-002","name":"FinTech Solutions SA","email":"dev@fintech.com.br","phone":"(11) 9876-5432","cnpj":"98.765.432/0001-10","contact_name":"Maria Santos","address":"Rua da Consolação, 500 - São Paulo, SP","segment":"Financeiro","status":"ATIVO"},
    {"id":"cli-003","name":"LogiTech Transportes","email":"ops@logitech.com.br","phone":"(11) 2233-4455","cnpj":"11.222.333/0001-44","contact_name":"Pedro Costa","address":"Rod. Anhanguera, km 15 - Campinas, SP","segment":"Logística","status":"ATIVO"},
]
KANBAN_PROJECTS = [
    {"id":"proj-001","client_id":"cli-001","name":"Website Redesign","description":"Redesign completo do portal de vendas e checkout","status":"EM_ANDAMENTO","start_date":"2026-04-01","end_date":"2026-06-30"},
    {"id":"proj-002","client_id":"cli-002","name":"API Gateway v2","description":"Migracao para arquitetura de microsservicos","status":"EM_ANDAMENTO","start_date":"2026-03-15","end_date":"2026-07-15"},
    {"id":"proj-003","client_id":"cli-003","name":"App Rastreamento","description":"Aplicativo mobile de rastreamento de frota","status":"PLANEJAMENTO","start_date":"2026-06-01","end_date":"2026-09-30"},
]
KANBAN_BOARDS = {
    "proj-001":{"columns":[
        {"id":"col-001","name":"Backlog","order":1,"cards":[
            {"id":"card-001","title":"Levantamento de Requisitos","description":"Mapeamento completo das necessidades do cliente","assignee":"Carlos Mendes","assignee_id":"emp-001","cost_per_task":680.00,"total_time_seconds":28800,"status":"CONCLUIDO","priority":"ALTA","due_date":dias(-20)},
            {"id":"card-002","title":"Wireframes e Prototipos","description":"Prototipacao de todas as telas no Figma","assignee":"Beatriz Lima","assignee_id":"emp-002","cost_per_task":248.00,"total_time_seconds":14400,"status":"CONCLUIDO","priority":"ALTA","due_date":dias(-15)},
        ]},
        {"id":"col-002","name":"Em Desenvolvimento","order":2,"cards":[
            {"id":"card-003","title":"Header, Footer e Menu de Navegacao","description":"Implementacao dos componentes globais de navegacao","assignee":"Carlos Mendes","assignee_id":"emp-001","cost_per_task":425.00,"total_time_seconds":18000,"status":"EM_ANDAMENTO","priority":"ALTA","due_date":dias(5)},
            {"id":"card-004","title":"Pagina de Produtos e Catalogo","description":"Listagem, filtros e busca de produtos","assignee":"Beatriz Lima","assignee_id":"emp-002","cost_per_task":310.00,"total_time_seconds":18000,"status":"EM_ANDAMENTO","priority":"MEDIA","due_date":dias(8)},
            {"id":"card-007","title":"Checkout e Pagamento","description":"Integracao com gateway de pagamento","assignee":"Fernanda Costa","assignee_id":"emp-004","cost_per_task":890.00,"total_time_seconds":7200,"status":"EM_ANDAMENTO","priority":"URGENTE","due_date":dias(3)},
        ]},
        {"id":"col-003","name":"Em Revisao","order":3,"cards":[
            {"id":"card-005","title":"Testes de Responsividade","description":"Validacao em mobile, tablet e desktop","assignee":"Rodrigo Santos","assignee_id":"emp-003","cost_per_task":174.00,"total_time_seconds":10800,"status":"EM_REVISAO","priority":"MEDIA","due_date":dias(2)},
        ]},
        {"id":"col-004","name":"Concluido","order":4,"cards":[
            {"id":"card-008","title":"Setup do Ambiente","description":"Configuracao de repositorio e CI","assignee":"Carlos Mendes","assignee_id":"emp-001","cost_per_task":120.00,"total_time_seconds":3600,"status":"CONCLUIDO","priority":"BAIXA","due_date":dias(-25)},
        ]},
    ]},
    "proj-002":{"columns":[
        {"id":"col-005","name":"Backlog","order":1,"cards":[
            {"id":"card-009","title":"Documentacao da API","description":"Swagger e documentacao de todos os endpoints","assignee":"Lucas Oliveira","assignee_id":"emp-005","cost_per_task":75.00,"total_time_seconds":0,"status":"ABERTO","priority":"BAIXA","due_date":dias(20)},
        ]},
        {"id":"col-006","name":"Em Desenvolvimento","order":2,"cards":[
            {"id":"card-006","title":"Auth Microservice - JWT + MFA","description":"Servico de autenticacao com suporte a MFA e refresh tokens","assignee":"Fernanda Costa","assignee_id":"emp-004","cost_per_task":1320.00,"total_time_seconds":43200,"status":"EM_ANDAMENTO","priority":"URGENTE","due_date":dias(4)},
            {"id":"card-010","title":"API Gateway - Rate Limiting","description":"Implementacao de rate limiting e circuit breaker","assignee":"Carlos Mendes","assignee_id":"emp-001","cost_per_task":680.00,"total_time_seconds":21600,"status":"EM_ANDAMENTO","priority":"ALTA","due_date":dias(7)},
        ]},
        {"id":"col-007","name":"QA / Testes","order":3,"cards":[
            {"id":"card-011","title":"Testes de Carga","description":"Stress test com 10k requisicoes/s","assignee":"Rodrigo Santos","assignee_id":"emp-003","cost_per_task":290.00,"total_time_seconds":14400,"status":"EM_REVISAO","priority":"ALTA","due_date":dias(1)},
        ]},
        {"id":"col-008","name":"Concluido","order":4,"cards":[]},
    ]},
    "proj-003":{"columns":[
        {"id":"col-009","name":"Backlog","order":1,"cards":[
            {"id":"card-012","title":"Briefing e Escopo","description":"Definicao do escopo e cronograma do app","assignee":"Rodrigo Santos","assignee_id":"emp-003","cost_per_task":0,"total_time_seconds":0,"status":"ABERTO","priority":"ALTA","due_date":dias(15)},
            {"id":"card-013","title":"Arquitetura React Native","description":"Definir stack mobile e patterns","assignee":"Fernanda Costa","assignee_id":"emp-004","cost_per_task":0,"total_time_seconds":0,"status":"ABERTO","priority":"MEDIA","due_date":dias(18)},
        ]},
        {"id":"col-010","name":"Em Andamento","order":2,"cards":[]},
        {"id":"col-011","name":"Revisao","order":3,"cards":[]},
        {"id":"col-012","name":"Concluido","order":4,"cards":[]},
    ]},
}
ACTIVE_TIMERS = {}  # card_id -> {started_at, employee_id, timer_id}
NOTIFICATIONS = [
    {"id":"ntf-001","title":"Lancamento Vencendo","message":"Aluguel Escritorio vence em 15 dias - R$ 3.500,00","type":"WARNING","is_read":False,"created_at":datetime.now().isoformat()},
    {"id":"ntf-002","title":"Pagamento Recebido","message":"Projeto Website Varejo - R$ 28.500,00 confirmado","type":"SUCCESS","is_read":False,"created_at":(datetime.now()-timedelta(hours=2)).isoformat()},
    {"id":"ntf-003","title":"Card Atualizado","message":"Fernanda Costa moveu Auth Microservice","type":"INFO","is_read":True,"created_at":(datetime.now()-timedelta(hours=5)).isoformat()},
    {"id":"ntf-004","title":"Alerta CTC","message":"Parametros INSS atualizados","type":"WARNING","is_read":True,"created_at":(datetime.now()-timedelta(days=1)).isoformat()},
]
COST_CENTERS = [{"id":"cc-001","name":"Tecnologia","code":"TECH"},{"id":"cc-002","name":"Administrativo","code":"ADM"},{"id":"cc-003","name":"Comercial","code":"COM"}]
CATEGORIES = [
    {"id":"cat-001","name":"Desenvolvimento","type":"RECEITA"},{"id":"cat-002","name":"Consultoria","type":"RECEITA"},
    {"id":"cat-003","name":"Suporte","type":"RECEITA"},{"id":"cat-004","name":"SaaS","type":"RECEITA"},
    {"id":"cat-005","name":"Infraestrutura","type":"DESPESA"},{"id":"cat-006","name":"Pessoal","type":"DESPESA"},
    {"id":"cat-007","name":"Aluguel","type":"DESPESA"},{"id":"cat-008","name":"Ferramentas","type":"DESPESA"},
    {"id":"cat-009","name":"Contabilidade","type":"DESPESA"},
]
COMPANY = {"id":"cmp-001","name":"TechConnect Solucoes Ltda","cnpj":"12.345.678/0001-90","email":"contato@techconnect.com.br","phone":"(61) 3344-5566","address":"SHCGN 713 Bloco A - Brasilia/DF","fiscal_year_start":1}
PERSONAL_ENTRIES = [
    {"id":"pes-001","type":"RECEITA","amount":8500.00,"description":"Salario Marco","date":dias(-5),"category":"Salario"},
    {"id":"pes-002","type":"DESPESA","amount":1800.00,"description":"Aluguel Apartamento","date":dias(-3),"category":"Moradia"},
    {"id":"pes-003","type":"DESPESA","amount":650.00,"description":"Supermercado","date":dias(-2),"category":"Alimentacao"},
    {"id":"pes-004","type":"DESPESA","amount":320.00,"description":"Plano de Saude","date":dias(-1),"category":"Saude"},
]
EXPORT_LOGS = [
    {"id":"exp-001","type":"DRE","format":"PDF","status":"PRONTO","created_at":(datetime.now()-timedelta(days=2)).isoformat(),"size_bytes":245000},
    {"id":"exp-002","type":"COLABORADORES","format":"EXCEL","status":"PRONTO","created_at":(datetime.now()-timedelta(days=5)).isoformat(),"size_bytes":89000},
]
