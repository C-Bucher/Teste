# Nota da pasta app/db/alembic/versions

**Função:** As migrações numeradas (0001 a 0010). Cada uma altera o esquema do banco em um passo. Migração já aplicada não se edita; cria-se uma nova.

## O que tem aqui

- `0001_baseline_schema.py`: Migração 0001: cria o esquema inicial com todas as tabelas.
- `0002_login_lockout_and_audit_log.py`: Migração 0002: colunas de bloqueio por tentativas de login e a tabela de auditoria.
- `0003_financial_entry_attachment.py`: Migração 0003: colunas para anexar comprovante ao lançamento financeiro.
- `0004_ctc_params.py`: Migração 0004: tabela de parâmetros do CTC (multiplicadores por empresa).
- `0005_bank_accounts_transactions_rules.py`: Migração 0005: tabelas de contas bancárias, transações do extrato e regras de categorização.
- `0006_ai_messages_and_usage.py`: Migração 0006: tabelas do histórico de conversas com a IA e do consumo mensal.
- `0007_password_resets.py`: Migração 0007: tabela dos pedidos de redefinição de senha (uso único e com validade).
- `0008_two_factor_secrets.py`: Migração 0008: colunas do segredo do 2FA e dos códigos de recuperação.
- `0009_terms_acceptance.py`: Migração 0009: colunas do aceite dos termos (versão e data).
- `0010_billing_provider_fields.py`: Migração 0010: campos que ligam assinaturas e faturas ao provedor de pagamento (Asaas).
