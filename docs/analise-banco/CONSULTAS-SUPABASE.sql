-- Diagnóstico de leitura para executar no SQL Editor do Supabase.
-- Execute cada bloco separadamente. Não altera estrutura nem dados.
-- Os blocos 1 a 6 consultam metadados. Compartilhe os resultados sem credenciais.
-- Os blocos 7 a 10 pressupõem as tabelas no schema public e a migração aplicada.

-- 1. Tabelas da aplicação e estado de RLS.
SELECT schemaname, tablename, rowsecurity AS rls_ativada
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- 2. Colunas e tipos reais (comparar com o dicionário gerado do código).
SELECT table_name, column_name, data_type, udt_name,
       is_nullable, column_default, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;

-- 3. Chaves e restrições reais: PK, FK, UNIQUE e CHECK.
SELECT c.relname AS tabela, con.conname AS restricao,
       con.contype AS tipo, pg_get_constraintdef(con.oid) AS definicao
FROM pg_constraint con
JOIN pg_class c ON c.oid = con.conrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
ORDER BY c.relname, con.conname;

-- 4. Índices existentes.
SELECT tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- 5. Políticas RLS, se existirem. Resultado vazio significa ausência de
-- políticas visíveis nesta consulta, não comprova ausência de todos os controles.
SELECT schemaname, tablename, policyname, roles, cmd, qual, with_check
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- 6. Grants da Data API e características de papéis relevantes.
-- O papel atual aqui é o do SQL Editor; não identifica o papel usado pela API FastAPI.
SELECT table_name, grantee, privilege_type
FROM information_schema.table_privileges
WHERE table_schema = 'public' AND grantee IN ('anon', 'authenticated', 'PUBLIC')
ORDER BY table_name, grantee, privilege_type;

SELECT rolname, rolsuper, rolbypassrls
FROM pg_roles
WHERE rolname IN ('postgres', 'anon', 'authenticated', 'service_role', current_user)
ORDER BY rolname;

-- 7. Revisão aplicada: o head com as melhorias de banco é 0011.
-- Se a relação não existir, registrar isso e não criar nada manualmente.
SELECT version_num FROM public.alembic_version;

-- 8. Qualidade básica: domínios financeiros observados, sem expor linhas individuais.
SELECT type, status, COUNT(*) AS quantidade,
       COUNT(*) FILTER (WHERE amount <= 0) AS valores_nao_positivos
FROM public.financial_entries
GROUP BY type, status
ORDER BY type, status;

-- 9. Contas com propriedade inconsistente, apenas contagem.
SELECT COUNT(*) AS contas_inconsistentes
FROM public.bank_accounts
WHERE NOT (
    (scope = 'empresa' AND company_id IS NOT NULL AND owner_id IS NULL)
    OR (scope = 'pessoal' AND owner_id IS NOT NULL AND company_id IS NULL)
);

-- 10. Exemplo de relatório agregado. Substitua SOMENTE o ID fictício pelo
-- ID de uma empresa de demonstração autorizada. Não agrega empresas diferentes.
-- Usa as datas em texto ISO atuais e reproduz o critério por vencimento.
-- É um resumo operacional; não deve ser chamado de DRE contábil completa.
WITH parametros AS (
    SELECT 'cmp-001'::varchar AS empresa,
           '2026-10-01'::varchar AS inicio,
           '2026-10-31'::varchar AS fim
)
SELECT f.type, COALESCE(f.category, 'Sem categoria') AS categoria,
       COUNT(*) AS quantidade, ROUND(SUM(f.amount)::numeric, 2) AS total
FROM public.financial_entries f
CROSS JOIN parametros p
WHERE f.company_id = p.empresa
  AND f.due_date >= p.inicio AND f.due_date <= p.fim
GROUP BY f.type, COALESCE(f.category, 'Sem categoria')
ORDER BY f.type, categoria;

-- ROUND na saída não corrige a representação aproximada de Float na origem.
-- Depois de migrar para Numeric, o cálculo pode ser realizado no tipo exato.
