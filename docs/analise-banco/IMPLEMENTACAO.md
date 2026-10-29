# Implementação das três melhorias

Revisão **0011**, sobre **0010**. Modelos: **41 tabelas** de negócio após criar time_entries.

## Alterações

1. **Precisão:** 26 colunas monetárias convertidas para Numeric(14,2), com Numeric(14,4) para custo-hora de colaboradores. Cálculos financeiros centrais, CTC, importação/conciliação bancária e novos apontamentos usam Decimal. Arredondamento monetário de entrada/cálculo: ROUND_HALF_UP. A saída JSON mantém o contrato numérico da API; o navegador continua usando Number. Percentuais e campos JSON livres não foram convertidos em colunas monetárias.
2. **Integridade:** CHECKs de valor/tipo nos lançamentos empresariais e pessoais; CHECK de status empresarial; CHECK de propriedade/escopo nas contas bancárias; FK composta de empresa/fornecedor. A exclusão de fornecedor pela API remove o vínculo dos lançamentos na mesma transação, preservando-os. SQLite habilita FKs nas conexões da aplicação.
3. **Histórico:** time_entries registra duração, responsável histórico, autor, início/fim, custo-hora, custo e origem. O cronômetro captura a taxa no início; sua parada registra a sessão e soma o custo. O endpoint de edição do cartão não pode sobrescrever os acumulados. GET /api/v1/kanban/cards/{id}/time-entries consulta o histórico com isolamento por empresa. Não foi criada uma tela de histórico no frontend.

## Dados existentes

A migração verifica dados incompatíveis e interrompe com contagens se houver inconsistências. Não apaga nem corrige automaticamente registros inválidos. Valores existentes são arredondados para a escala de destino. Totais antigos dos cartões são preservados em linhas `legacy`, com datas desconhecidas nulas e taxa média implícita; não são apresentados como sessões reais. Cronômetros já ativos recebem a taxa disponível na migração, pois não existe um snapshot anterior.

Autor e responsável nos apontamentos são identificadores históricos em texto. Há FK para o cartão; excluir cartão/empresa também remove os apontamentos. O histórico não é um arquivo de auditoria imutável.

O downgrade elimina o detalhe de apontamentos e retorna valores a Float. Não é um procedimento de rotina.

## Aplicação no Supabase

**Estado: aplicado e verificado no Supabase em 28/10/2026, revisão 0011.**

A base estava em formato anterior ao Alembic. Após inspeção e confirmação do usuário, os registros antigos sem empresa foram associados à TechConnect Solucoes Ltda (cmp-001). Os vínculos existentes da Acme foram preservados. Foram criadas as tabelas/colunas pré-requisito com base no esquema histórico 0001, aplicadas as revisões seguintes e, por fim, a melhoria 0011. Não foi executado seed no banco remoto. As contagens de todas as 29 tabelas que existiam antes foram preservadas.

Conferência remota: **41 tabelas de negócio, 26 colunas Numeric e 12 restrições novas validadas**. Foram criados **11 registros legacy**, preservando 180.000 segundos e R$ 5.212,00 em custos acumulados, sem divergências em relação aos cartões. Evidências somente com esquema/contagens/agregados: VERIFICACAO-SUPABASE.json e VALIDACAO-SUPABASE.json.

Os novos cronômetros e o endpoint de histórico requerem executar o backend atualizado deste clone. A migração do banco não publica nem substitui uma instância antiga do backend.

Arquivo: `C:/Programação/ADS-DASHBOARD-PARA-GEST-O-OPERACIONAL/.env`, com DATABASE_URL PostgreSQL/asyncpg. É ignorado pelo Git; não enviar credenciais pelo chat.

Verificação de leitura, sem iniciar a aplicação ou o seed:

```powershell
.venv/Scripts/python.exe -m scripts.database_upgrade
```

Aplicação transacional, após conferir os dados:

```powershell
.venv/Scripts/python.exe -m scripts.database_upgrade --apply
```

O comando usual espera a base em 0010 ou 0011, limita a espera por locks/execução e salva versão e contagens em VERIFICACAO-SUPABASE.json. Para esta base legada foi usado --apply --legacy-company cmp-001, após confirmação do proprietário pelo usuário e teste específico de adoção. Não reutilizar a opção de legado em uma base já versionada. O comando não imprime conexão nem linhas individuais. Alterações normais de esquema precisam dos locks do PostgreSQL; não foi acrescentado bloqueio explícito antecipado de todas as tabelas.

## Validação

Foram acrescentados 19 testes, cobrindo precisão, restrições por SQL direto, vínculos entre empresas, atualização inválida, histórico de custos, proteção dos acumulados, isolamento, migração do legado, carga idempotente e adoção da base antiga com duas empresas. Resultado em 28/10/2026: **158 testes passaram em 12,80 segundos**, usando SQLite temporário. A sintaxe Python e o diff também foram conferidos. No PostgreSQL remoto, a verificação de leitura confirmou os tipos, as restrições validadas e a equivalência entre histórico e acumulados. Não foi executada a suíte destrutiva de testes no Supabase.

O roteiro atual está em ROTEIRO-SIMPLES.md. Os documentos anteriores registram o estado original e as propostas que motivaram esta implementação.

Antes do envio ao GitHub, a suíte do backend passou novamente com 158 testes. Também passaram ESLint, os 14 testes do frontend e o build TypeScript/Vite. O build informou apenas o aviso de tamanho dos chunks. O .env permaneceu ignorado pelo Git.
