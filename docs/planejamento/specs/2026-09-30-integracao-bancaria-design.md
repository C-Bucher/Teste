# Etapa 3 — Integração bancária e conciliação

- **Data:** 2026-09-30
- **Branch:** `feature/integracao-bancaria` (empilhado sobre `feature/planos-e-abas`)
- **Objetivo:** reduzir o trabalho manual. Os movimentos do banco entram no sistema sozinhos (agregador de Open Finance) ou por arquivo (OFX/CSV), e o sistema concilia com as contas a pagar e receber.

## Decisões

- **Open Finance direto:** não é viável, porque exige autorização do Banco Central. O caminho é um **agregador** (Pluggy como primeira implementação; Belvo é alternativa) atrás de uma interface `BankProvider`, para que a troca de fornecedor não mexa no resto.
- **OFX/CSV:** funciona com qualquer banco, sem custo. É o recurso do plano Pessoal Essencial e a alternativa quando a conexão cair.
- **Dados bancários:** sempre escopados. Conta e transação da empresa levam `company_id`; do Hub Pessoal, `owner_id`. O isolamento é coberto pelos mesmos testes cruzados da etapa 1.

## Modelo de dados

- `bank_accounts`: `id`, `company_id` ou `owner_id`, `scope` (`empresa`/`pessoal`), `name`, `bank_name`, `source` (`arquivo`/`agregador`), `provider`, `provider_item_id`, `provider_account_id`, `status`, `last_sync_at`.
- `bank_transactions`: `id`, `bank_account_id`, `company_id`/`owner_id`, `external_id` (FITID ou hash), `date`, `amount` (com sinal), `description`, `category`, `status` (`NOVA`/`CONCILIADA`/`LANCADA`/`IGNORADA`), `entry_id`, `created_at`. É única por (`bank_account_id`, `external_id`): reimportar o mesmo extrato não duplica nada.
- `categorization_rules`: `company_id`/`owner_id`, `pattern` (texto contido na descrição), `category`.

## Fluxos

1. **Importar** (`POST /bank/import`): recebe o arquivo, o escopo e a conta (existente ou nova). Interpreta OFX 1.x (SGML) e 2.x (XML), além de CSV (`;` ou `,`, vírgula decimal, cabeçalhos data/descrição/valor). Grava as transações novas, ignora as repetidas, aplica as regras de categoria e roda a conciliação.
2. **Conciliação automática (empresa):** uma transação casa com um lançamento PENDENTE da mesma empresa quando tem o mesmo tipo (crédito = RECEITA), o mesmo valor (diferença de até R$ 0,01) e vencimento a até 5 dias da data. Só concilia sozinho quando há exatamente um candidato. O lançamento vira PAGO com a data do banco, e a transação vira CONCILIADA. Cada conciliação é auditada.
3. **Pessoal:** cada transação importada vira um lançamento pessoal (`LANCADA`). Não existem "contas a pagar" pessoais para conciliar.
4. **Ações manuais (empresa):** sobre uma transação NOVA, é possível criar um lançamento já pago, conciliar com um lançamento escolhido ou ignorar.
5. **Agregador:**
   - `POST /bank/connect-token` → token do widget;
   - `POST /bank/connections` (registra o item autorizado e as contas);
   - `POST /bank/accounts/{id}/sync` (busca as transações desde a última sincronização).

   Desabilitado, com resposta 503 e mensagem clara, enquanto `PLUGGY_CLIENT_ID`/`PLUGGY_CLIENT_SECRET` não estiverem configurados.

## Limites por plano (LIM-1)

- O plano atual vem da assinatura ativa da empresa; sem assinatura, vale o plano correspondente ao `plan_scope`.
- `bank_connections`: contas com `source=agregador` no escopo. Acima do limite → 402 com mensagem "faça upgrade".
- O Pessoal Essencial tem 0 conexões, mas importação por arquivo à vontade.
- `ai_queries`: contador mensal por empresa ou usuário, usado na etapa 4.

## Fora do escopo
- Webhook do agregador (sincronização em tempo real): a sincronização é sob demanda e diária.
- Iniciação de pagamento via Pix.
- O contrato e as credenciais do agregador são do dono do produto.

## Pronto quando
- Os testes cobrem: parser OFX/CSV, deduplicação, conciliação (1 candidato, 0, mais de 1), isolamento cruzado, limites e provedor simulado.
- A suíte fica verde nos 3 bancos e o build passa.
