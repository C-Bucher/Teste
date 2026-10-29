# Roteiro simples — melhorias implementadas no banco

Tempo sugerido: 2 a 3 minutos. As mudanças foram aplicadas e verificadas no Supabase em 28/10/2026, revisão 0011. O backend atualizado deste clone deve ser executado para usar os novos apontamentos.

**Abertura**

“Nesta etapa, implementei três melhorias no banco: precisão dos valores financeiros, regras de integridade e histórico dos custos por tarefa.”

**1. Valores financeiros mais precisos**

“Antes, os valores monetários eram armazenados em ponto flutuante. Agora, 26 colunas passaram a usar o tipo decimal, incluindo lançamentos, salários, saldos e custos. Também adaptei os cálculos principais e a leitura dos extratos para usar Decimal no Python. Isso permite trabalhar com casas decimais e arredondamento definidos.”

**2. Regras que o próprio banco verifica**

“Acrescentei restrições para impedir lançamentos com valores inválidos, tipos ou status não permitidos. As contas bancárias precisam pertencer a uma empresa ou a uma pessoa, conforme seu escopo. Além disso, um lançamento só pode referenciar um fornecedor da mesma empresa. A API continua validando, e o banco passa a reforçar essas regras.”

**3. Histórico dos custos por tarefa**

“Criei uma tabela de apontamentos de tempo. Cada sessão registra duração, custo-hora e custo calculado. A taxa é capturada quando o cronômetro começa, e o custo é somado ao finalizar. Assim, uma mudança salarial não recalcula o trabalho anterior.”

“Por exemplo: duas horas a R$ 50 e uma hora a R$ 60 totalizam R$ 160. O sistema preserva os custos de cada período. Os totais antigos são mantidos como registros históricos, identificados como legado.”

**Fechamento**

“As alterações foram aplicadas no Supabase por uma migração versionada. A suíte local passou com 158 testes, e a conferência no banco confirmou os tipos, as restrições e a preservação dos custos anteriores. O objetivo foi tornar os dados financeiros mais confiáveis e rastreáveis.”

Se perguntarem como demonstrar: mostrar uma coluna Numeric, as restrições de financial_entries e dois registros de time_entries com taxas diferentes. O exemplo de R$ 160 também é coberto por teste automatizado.
