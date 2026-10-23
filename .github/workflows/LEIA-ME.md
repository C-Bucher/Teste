# Nota da pasta .github/workflows

**Função:** Automações do GitHub Actions. Hoje: ci.yml, que roda testes, lint e build a cada mudança.

## O que tem aqui

- `ci.yml`: Integração contínua do GitHub: a cada pull request e push na main, roda os testes do backend (SQLite e Postgres), e no frontend o lint, os testes e o build.
