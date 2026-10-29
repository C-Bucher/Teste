# Nota da pasta app

**Função:** Código do servidor (backend). Divide-se em api (as rotas), core (regras gerais), db (banco de dados) e integrations (serviços de fora: IA, bancos, pagamentos).

## O que tem aqui

- `__init__.py`: Arquivo vazio. Faz o Python tratar a pasta app como pacote importável.
- `api/`: Camada de entrada da API: recebe os pedidos do frontend. Hoje só existe a versão 1 (v1).
- `core/`: Regras usadas por várias rotas: segurança (tokens, senhas, permissões), assinatura/cobrança, plano e limites, e-mail e notificações, alertas diários, auditoria e armazenamento de arquivos.
- `db/`: Banco de dados: models.py define as tabelas, session.py faz a conexão, seed.py cria os dados de demonstração e alembic guarda as migrações (versões do esquema).
- `integrations/`: Ligações com serviços externos, cada uma atrás de uma interface para poder trocar o fornecedor: IA (Gemini), bancos (Pluggy, OFX/CSV) e pagamentos (Asaas).
- `main.py`: Cria o servidor FastAPI. Ao iniciar: cria/atualiza o banco, insere os dados de demonstração se o banco estiver vazio e mostra avisos de configuração em produção. Também: define quais endereços do front podem chamar a API (CORS), limita tentativas por IP nas rotas de login, trata erros de banco, responde /health e entrega o site já compilado (frontend/dist) quando ele existe.
