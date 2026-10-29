# ADR 012 — Precisão monetária, integridade e histórico de custos

## Status

Implementado; em revisão pelo pull request.

## Data

2026-10-28

## Contexto

Valores monetários eram representados por Float. Algumas regras financeiras dependiam apenas da API, e o cronômetro recalculava todo o custo acumulado pelo custo-hora atual. A base Supabase também mantinha um esquema anterior ao Alembic, com registros de demonstração sem empresa definida.

## Decisão

- Converter 26 colunas para Numeric(14,2), com Numeric(14,4) no custo-hora, e usar Decimal nos cálculos financeiros centrais e na importação bancária. Definir arredondamento monetário HALF_UP nas entradas/cálculos.
- Acrescentar CHECKs de tipo, valor, status e escopo; usar FK composta de empresa/fornecedor. A exclusão de fornecedor pela API desvincula os lançamentos na mesma transação.
- Persistir cada sessão em time_entries, capturando o custo-hora no início e somando somente o custo da nova sessão. Preservar acumulados antigos em linhas identificadas como legacy.
- Versionar a mudança na revisão 0011. Disponibilizar adoção do esquema legado por metadados da revisão histórica 0001, com empresa de destino explicitamente informada, sem executar seed remoto.

## Consequências

- Tipos e restrições passam a garantir a precisão de armazenamento e regras fundamentais no PostgreSQL.
- Mudanças no custo-hora não recalculam os apontamentos anteriores. Editar o cartão não pode sobrescrever os acumulados.
- Valores antigos são arredondados à escala de destino; dados incompatíveis interrompem a migração. O downgrade perde o detalhe dos apontamentos e retorna a Float.
- A FK de fornecedor passa a restringir exclusão direta; a API atualizada mantém a operação de desvinculação e exclusão.
- Novos cronômetros exigem o backend atualizado. A saída JSON continua numérica, e o navegador mantém a representação Number.
- As identidades dos apontamentos são referências históricas em texto. Excluir cartão/empresa também elimina seu histórico; não se trata de auditoria imutável.

## Validação

158 testes locais passaram. No Supabase, foram verificadas a revisão 0011, 26 colunas Numeric, 12 restrições e a preservação de 11 acumulados de legado. A adoção da empresa foi confirmada pelo responsável antes da execução. Não houve seed remoto, e as contagens das 29 tabelas anteriores foram preservadas.

## Referências

- [Implementação e evidências](../analise-banco/IMPLEMENTACAO.md)
- [Migração 0011](../../app/db/alembic/versions/0011_money_integrity_time_entries.py)
- [Roteiro de apresentação](../analise-banco/ROTEIRO-SIMPLES.md)
