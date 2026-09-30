# ADR-007 — Endurecimento de autenticação, migrações versionadas e auditoria

- **Status:** Aceito
- **Data:** 2026-09-30

## Contexto

O TechConnect passa a ser preparado para clientes pagantes e, na próxima etapa, para receber dados bancários reais via agregador de Open Finance. O isolamento entregue no ADR-006 não tinha nenhum teste automático. Além disso, a autenticação aceitava qualquer senha de 8 caracteres, não limitava tentativas e usava um único token de 8 horas que também servia de refresh. O schema evoluía por `create_all` mais uma rotina aditiva, e não havia registro de quem alterou o quê.

## Decisão

1. **Testes:** suíte `pytest` sobre a API real em memória (`httpx.ASGITransport`), com SQLite descartável por padrão e `TEST_DATABASE_URL` para rodar em PostgreSQL/MySQL reais. O isolamento é testado atacando cada recurso a partir de uma segunda empresa.
2. **Migrações:** Alembic com revisão base `0001` igual ao schema pré-existente. No startup:
   - banco vazio: `upgrade head`;
   - banco pré-Alembic: `create_all` das tabelas da base, rotina de compatibilidade, `stamp 0001` e então `upgrade head`.

   Um teste falha se os models divergirem das migrações.
3. **Tokens:** access token (60 min, `type=access`) e refresh token (7 dias, `type=refresh`) distintos. Ambos carregam uma impressão do hash da senha (`pwd`), de modo que trocar a senha revoga todas as sessões anteriores sem precisar de uma tabela de revogação.
4. **Bloqueio de login:** o contador fica em `users` (e não em memória), para valer entre reinícios e entre instâncias. São 5 falhas para 15 minutos de bloqueio.
5. **Auditoria:** tabela `audit_logs`, gravada na mesma transação da alteração auditada. `user_id` não tem chave estrangeira, para que a trilha sobreviva à exclusão do usuário. O IP vem de um middleware (`X-Forwarded-For` ou cliente direto).

## Consequências

- Mudanças de schema passam a exigir uma revisão Alembic. O teste de divergência pega o esquecimento.
- Tokens emitidos antes desta versão deixam de valer (não têm `type`/`pwd`): todos os usuários fazem login de novo uma vez.
- O SQLite não confere chaves estrangeiras por padrão; um erro desse tipo só apareceu ao rodar a suíte em PostgreSQL. Rodar a suíte contra PostgreSQL passa a fazer parte da verificação antes de publicar.
- **Pendente:** a interface da auditoria e os direitos do titular (LGPD) ficam para a etapa seguinte; a rotação das credenciais do Supabase (SEC-5) depende do dono do projeto.
