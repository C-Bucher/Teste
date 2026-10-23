# Nota da pasta app/db/alembic

**Função:** Alembic, a ferramenta que versiona o esquema do banco. env.py configura, script.py.mako é o molde e versions guarda as migrações.

## O que tem aqui

- `env.py`: Configuração do Alembic: indica o banco e como aplicar as migrações (pelo app ao iniciar ou pelo comando alembic).
- `script.py.mako`: Molde usado pelo Alembic para gerar cada nova migração.
- `versions/`: As migrações numeradas (0001 a 0010). Cada uma altera o esquema do banco em um passo. Migração já aplicada não se edita; cria-se uma nova.
