# ADR-006 — Isolamento de dados e persistência operacional

- **Status:** Aceito
- **Data:** 2026-09-23

## Contexto

Os cadastros de empresas e usuários eram separados, mas os principais dados operacionais eram globais. O Hub Pessoal gravava todos os registros em `usr-001`, e assinatura, faturas e timers eram mantidos na memória do processo. Esses comportamentos permitiam acesso cruzado e perda de estado após reinícios.

## Decisão

1. Recursos empresariais passam a carregar `company_id`, preenchido exclusivamente a partir do usuário autenticado.
2. Toda consulta e mutação verifica a empresa proprietária; um identificador de outra empresa é tratado como não encontrado.
3. Recursos pessoais usam `owner_id = current_user.id` e aplicam a mesma verificação de propriedade.
4. Assinaturas, faturas, timers, calendário e preferências são persistidos em tabelas SQLAlchemy.
5. Gates de módulo são aplicados no backend; o frontend mantém guards equivalentes apenas como experiência de navegação.
6. Uma migração aditiva idempotente faz o backfill dos dados legados para `cmp-001`. Migrações versionadas continuam como evolução futura.

## Consequências

- Empresas e usuários deixam de compartilhar dados operacionais e pessoais.
- Reinícios não apagam assinatura, faturas, timers ou configurações persistidas.
- Dados legados permanecem associados à empresa e ao usuário de demonstração originais.
- Novos recursos empresariais precisam possuir ou herdar inequivocamente um `company_id`.
- Alembic ainda é necessário antes de mudanças destrutivas ou transformações complexas de schema.
