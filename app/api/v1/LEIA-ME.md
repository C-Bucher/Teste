# Nota da pasta app/api/v1

**Função:** Versão 1 da API. api.py junta todas as rotas; a pasta endpoints tem um arquivo por assunto.

## O que tem aqui

- `__init__.py`: Arquivo vazio. Faz o Python tratar a pasta app/api/v1 como pacote.
- `api.py`: Lista de rotas da API v1: junta todos os módulos de app/api/v1/endpoints sob o prefixo /api/v1 e define quais exigem permissão de módulo (ex.: equipe, financeiro) e assinatura ativa.
- `endpoints/`: As rotas da API, um arquivo por assunto (login, financeiro, kanban, bancos, pagamentos etc.).
