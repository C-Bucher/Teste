# ADR-008 — Integração bancária por agregador e conciliação

- **Status:** Aceito
- **Data:** 2026-09-30

## Contexto

O objetivo comercial é reduzir o trabalho manual: os movimentos do banco do cliente devem entrar no sistema sem digitação. Participar diretamente do Open Finance Brasil exige autorização do Banco Central, o que é inviável para o produto.

## Decisão

1. **Agregador:** a conexão automática usa um agregador de Open Finance. A primeira implementação é a Pluggy, atrás da interface `BankProvider` (`app/integrations/bank/providers.py`), para que a troca de fornecedor (Belvo, por exemplo) não afete o resto. O agregador só é ativado com `PLUGGY_CLIENT_ID`/`PLUGGY_CLIENT_SECRET`; sem eles, a API responde 503 com orientação.
2. **Arquivo como alternativa:** a importação de extrato por arquivo (OFX 1.x/2.x e CSV) funciona com qualquer banco e é o recurso do plano Pessoal Essencial.
3. **Deduplicação:** transações têm id externo (FITID do OFX, id do agregador ou hash estável para CSV), com unicidade por conta. Reimportar nunca duplica.
4. **Conciliação automática só sem ambiguidade:** mesmo tipo, mesmo valor (diferença de até R$ 0,01), vencimento a até 5 dias e exatamente um candidato. O resto fica para decisão humana. Cada conciliação é auditada.
5. **Escopo:** dados bancários da empresa levam `company_id`; os do Hub Pessoal levam `owner_id` e não são visíveis a colegas da mesma empresa.
6. **Limites por plano:** contas conectadas pelo agregador contam para o limite `bank_connections` do plano; a importação por arquivo não tem limite.

## Consequências

- Antes de vender o plano Pessoal Conectado é preciso: contrato e credenciais com a Pluggy, validar o widget e o formato das transações no sandbox, e recalcular os preços com o custo real por conexão.
- A sincronização é sob demanda (botão Sincronizar); a sincronização em tempo real por webhook fica para depois.
- Os dados bancários são dados pessoais/financeiros sensíveis para a LGPD; a exclusão de conta os apaga.
