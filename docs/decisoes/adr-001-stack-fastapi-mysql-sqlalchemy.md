# ADR 001 — Adoção de FastAPI, SQLAlchemy 2.0 Assíncrono e MySQL 8.0

## Status
Aprovado / Implementado

## Contexto
O projeto TechConnect 2.0 necessitava evoluir de um protótipo com armazenamento em memória para uma solução robusta, persistente e escalável, capaz de processar dados financeiros corporativos (DRE, CTC de colaboradores, lançamentos) e dados operacionais de alta frequência (apontamento de tempo no Kanban e cronômetro em tempo real).

## Decisão
Decidiu-se pela utilização do **FastAPI** (Python 3.11) como framework de backend, combinado com o **SQLAlchemy 2.0 em modo assíncrono** (`async_sessionmaker`, `select`, `AsyncEngine`) e o banco de dados relacional **MySQL 8.0** orquestrado via Docker Compose.

## Justificativa
1. **Performance e Concorrência:** O modelo assíncrono do FastAPI com ASGI (Uvicorn) e SQLAlchemy Async permite lidar com alto volume de I/O não bloqueante (essencial para múltiplas conexões de cronômetros Kanban e chamadas ao modelo de IA).
2. **Tipagem e Documentação Automática:** O ecossistema Pydantic v2 do FastAPI gera documentação interativa Swagger/OpenAPI nativamente e garante validação rigorosa dos payloads financeiros.
3. **Persistência Relacional Estruturada:** O MySQL 8.0 oferece integridade referencial com ACID, permitindo gerenciar chaves estrangeiras (`ON DELETE SET NULL`), índices e consistência contábil.
4. **Seed Idempotente:** Facilita o onboarding e avaliação acadêmica, populando o banco automaticamente apenas se vazio.

## Consequências
- **Positivas:** Persistência real dos dados, alta velocidade de resposta (< 300ms), isolamento em contêineres e facilidade de testes via Swagger.
- **Negativas / Mitigações:** Necessidade de gerenciar o ciclo de vida de conexões assíncronas no SQLAlchemy (mitigado com `pool_pre_ping=True` e `pool_recycle=3600`).
