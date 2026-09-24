# ADR 001 — Adoção de FastAPI, SQLAlchemy 2.0 Assíncrono e MySQL 8.0

## Status
Aprovado / Implementado

## Contexto
O TechConnect 2.0 precisava sair de um protótipo com armazenamento em memória para uma persistência real, capaz de lidar com dados financeiros corporativos (DRE, CTC de colaboradores, lançamentos) e com dados operacionais de alta frequência, como o apontamento de tempo no Kanban e o cronômetro em tempo real.

## Decisão
Adotamos FastAPI (Python 3.11) como framework de backend, SQLAlchemy 2.0 em modo assíncrono (`async_sessionmaker`, `select`, `AsyncEngine`) como ORM, e MySQL 8.0 como banco relacional, orquestrado via Docker Compose.

## Justificativa
1. O modelo assíncrono do FastAPI, com ASGI (Uvicorn) e SQLAlchemy Async, lida bem com I/O não bloqueante — importante com várias conexões de cronômetro do Kanban abertas ao mesmo tempo, e futuramente com chamadas ao modelo de IA.
2. O Pydantic v2 do FastAPI já gera a documentação Swagger/OpenAPI e valida os payloads financeiros sem trabalho extra.
3. O MySQL 8.0 garante integridade referencial com ACID: chaves estrangeiras (`ON DELETE SET NULL`), índices e consistência nos dados contábeis.
4. Um seed idempotente facilita tanto o onboarding de quem vai rodar o projeto quanto a avaliação acadêmica, populando o banco automaticamente só quando ele está vazio.

## Consequências
- Positivas: persistência real, isolamento em contêineres e testes facilitados via Swagger. A resposta assíncrona não mostrou gargalo perceptível nos testes manuais, mas a latência nunca foi medida formalmente (ver RNF01 em [requisitos.md](../requisitos.md)).
- Negativas / mitigações: é preciso gerenciar o ciclo de vida das conexões assíncronas no SQLAlchemy — mitigado com `pool_pre_ping=True` e `pool_recycle` (ajustado depois para diferentes dialetos, ver [ADR 005](adr-005-suporte-postgresql-supabase.md)).
