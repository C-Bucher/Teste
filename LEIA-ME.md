# Nota da pasta raiz

**Função:** Raiz do projeto TechConnect 2.0: sistema de gestão financeira e operacional para empresas e para pessoas. O servidor é em Python (FastAPI) e a tela é em React. Esta pasta reúne Docker, integração contínua, dependências e a documentação geral. Pastas que não têm nota por serem geradas ou internas do Git: .git (banco interno do Git com todo o histórico do código; não se mexe à mão), frontend/dist (site compilado; é apagado e refeito a cada build) e .pytest_cache (cache dos testes).

## O que tem aqui

- `.claude/`: Pasta do Claude Code (assistente de programação) neste projeto: configuração de execução e permissões locais. Não faz parte do sistema.
- `.editorconfig`: Padrão de edição (indentação, fim de linha) seguido pelos editores.
- `.env`: Configuração local com chaves e senhas reais. Fica fora do Git. Nunca compartilhe nem publique.
- `.env.example`: Modelo do .env com todas as variáveis e explicações. Copie para .env e preencha.
- `.github/`: Configurações do GitHub: modelos de issue, modelo de pull request e automações (workflows).
- `.gitignore`: Lista do que o Git ignora (.env, bancos locais, node_modules, venv, build).
- `.markdownlint.json`: Regras do verificador de formatação dos arquivos .md.
- `.superpowers/`: Pasta de apoio de uma ferramenta de desenvolvimento assistido (planos e revisões antigas). Não faz parte do sistema.
- `alembic.ini`: Configuração do Alembic (ferramenta de migrações do banco): aponta para app/db/alembic e define o formato dos logs.
- `app/`: Código do servidor (backend). Divide-se em api (as rotas), core (regras gerais), db (banco de dados) e integrations (serviços de fora: IA, bancos, pagamentos).
- `architecture/`: Procedimentos operacionais padrão (POP) das três funções de IA: CFO Virtual, conciliação bancária e gerador de orçamento. Descrevem o passo a passo de cada uma.
- `CHANGELOG.md`: Histórico de mudanças por versão.
- `CODE_OF_CONDUCT.md`: Código de conduta de quem contribui.
- `CONTRIBUTING.md`: Como contribuir: branches, commits e pull requests.
- `docker-compose.yml`: Sobe tudo junto com um comando: db (MySQL), redis, backend (FastAPI) e frontend (tela), com as variáveis lidas do arquivo .env.
- `Dockerfile`: Receita da imagem Docker do backend: parte do Python 3.11, instala o requirements.txt e copia o código.
- `docs/`: Documentação do projeto: requisitos, arquitetura, backlog (pendências), registro de alterações, decisões, reuniões e planejamento.
- `entregas/`: Registros das entregas feitas à faculdade e o modelo para novas entregas.
- `frontend/`: Frontend: as telas do sistema em React + TypeScript, com Vite (compila e serve), Tailwind (estilo) e Vitest (testes). O código está em src; as bibliotecas instaladas estão em node_modules.
- `LICENSE`: Licença de uso do projeto.
- `pytest.ini`: Configuração do pytest: as provas ficam na pasta tests e as funções async rodam automaticamente.
- `README.md`: Apresentação do projeto: o que é, como rodar, variáveis de ambiente, usuários de demonstração e estrutura.
- `requirements-dev.txt`: Bibliotecas para desenvolvimento: tudo do requirements.txt mais pytest e pytest-asyncio para os testes.
- `requirements.txt`: Bibliotecas Python que o servidor precisa para rodar (pip install -r requirements.txt).
- `SECURITY.md`: Política de segurança: como reportar vulnerabilidades.
- `sprints/`: Registro de cada sprint (rodada de trabalho): objetivo, entregas, limitações e evidências.
- `techconnect.db`: Banco SQLite local de desenvolvimento, criado pelo servidor. Fica fora do Git.
- `tests/`: Testes automatizados do backend (pytest): segurança, isolamento entre empresas, cobrança, bancos, IA, migrações e exportações. Rodam também no GitHub a cada mudança.
