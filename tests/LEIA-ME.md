# Nota da pasta tests

**Função:** Testes automatizados do backend (pytest): segurança, isolamento entre empresas, cobrança, bancos, IA, migrações e exportações. Rodam também no GitHub a cada mudança.

## O que tem aqui

- `conftest.py`: Preparação comum dos testes: banco SQLite temporário, clientes HTTP de duas empresas independentes e funções auxiliares (register_admin, create_member).
- `test_account.py`: Testa exportar os próprios dados, excluir a conta (LGPD) e a gestão de acessos feita pelo administrador.
- `test_ai.py`: Testa a IA: respostas com dados reais, respostas por regras quando a IA falha, histórico e cota mensal.
- `test_api_contract.py`: Testa que toda chamada de API feita pelo frontend tem rota correspondente no backend (método e caminho).
- `test_attachments.py`: Testa o comprovante anexado ao lançamento: upload, download e acesso só pela empresa dona.
- `test_audit.py`: Testa a trilha de auditoria: ações sensíveis são registradas e só o administrador as vê.
- `test_auth_hardening.py`: Testa regra de senha, troca de senha, bloqueio por tentativas e separação entre token de acesso e de renovação.
- `test_bank.py`: Testa importação de extrato, conciliação, regras, isolamento entre empresas, limites do plano e o agregador.
- `test_billing.py`: Testa teste grátis, checkout, webhook (ativação, renovação, atraso) e o bloqueio de acesso.
- `test_consent.py`: Testa o aceite dos termos: o cadastro exige aceitar, e a versão e a data ficam registradas.
- `test_consent_frontend_version.py`: Testa que a versão dos termos é a mesma no backend (legal.py) e no frontend (legal.ts).
- `test_ctc.py`: Testa que os parâmetros de CTC da empresa mudam o custo calculado do colaborador.
- `test_daily_alerts.py`: Testa o job diário: avisa contas a vencer, recebíveis atrasados e prazos do Kanban, uma vez por dia.
- `test_demo_dates.py`: Testa que as datas da demonstração avançam até hoje sem perder a distância entre elas.
- `test_email_and_recovery.py`: Testa a recuperação de senha por e-mail e os e-mails de notificação.
- `test_isolation.py`: Testa o isolamento: uma empresa não vê nem altera dados de outra, e o Hub Pessoal é por usuário.
- `test_kanban.py`: Testa o quadro Kanban: cartões, comentários e exclusão de cartão.
- `test_mfa_and_rate_limit.py`: Testa o login com 2FA (código e códigos de recuperação) e o limite de tentativas por IP.
- `test_migrations.py`: Testa que as migrações do Alembic geram o mesmo esquema dos modelos.
- `test_permissions.py`: Testa o bloqueio de módulos por cargo e as regras de gestão de acessos.
- `test_personal_analytics.py`: Testa que o patrimônio do Hub Pessoal é calculado com contas, dívidas e lançamentos reais.
- `test_plans.py`: Testa os quatro planos e seus preços aprovados.
- `test_smoke.py`: Teste rápido: cadastro, login e /me funcionam, e sem token a API recusa.
- `test_statement_parser.py`: Testa a leitura de extratos OFX (SGML e XML) e CSV.
- `test_storage_and_exports.py`: Testa o armazenamento (local e S3) e as exportações em XLSX e PDF.
