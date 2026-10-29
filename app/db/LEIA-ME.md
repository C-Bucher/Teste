# Nota da pasta app/db

**Função:** Banco de dados: models.py define as tabelas, session.py faz a conexão, seed.py cria os dados de demonstração e alembic guarda as migrações (versões do esquema).

## O que tem aqui

- `__init__.py`: Arquivo vazio. Faz o Python tratar a pasta app/db como pacote.
- `alembic/`: Alembic, a ferramenta que versiona o esquema do banco. env.py configura, script.py.mako é o molde e versions guarda as migrações.
- `demo_dates.py`: Atualiza as datas dos dados de demonstração para perto de hoje, mantendo a distância entre elas. Manual: python -m app.db.demo_dates, ou automático com DEMO_REFRESH_DATES=1.
- `migrations.py`: Migrações simples e repetíveis para bancos criados antes do Alembic: acrescenta colunas que faltam sem apagar dados.
- `models.py`: Define todas as tabelas do banco (41 ao todo) como classes SQLAlchemy, incluindo apontamentos históricos em `time_entries`. Valores monetários usam Numeric e a revisão 0011 acrescenta restrições financeiras e de propriedade. Mudou uma tabela aqui? Crie também uma migração.
- `seed.py`: Dados de demonstração: se a tabela de usuários estiver vazia, cria a empresa, usuários, lançamentos, projetos e demais exemplos. Se já houver dados, não faz nada.
- `session.py`: Conexão com o banco (SQLite, MySQL ou PostgreSQL, conforme DATABASE_URL), fábrica de sessões por requisição e inicialização (cria tabelas e aplica as migrações ao iniciar).
- `utils.py`: Converte um registro do banco em dicionário, no formato que o front espera.
