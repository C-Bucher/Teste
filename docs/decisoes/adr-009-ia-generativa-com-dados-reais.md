# ADR-009 — IA generativa sobre dados reais, com fallback por regras e cota

- **Status:** Aceito
- **Data:** 2026-09-30

## Contexto

As telas de IA respondiam com textos e números fixos no código, iguais para qualquer empresa. Para um produto pago, a IA precisa falar dos números do cliente, ter custo controlado e continuar útil quando o modelo não estiver disponível.

## Decisão

1. **Modelo:** Gemini via REST (`generateContent`), modelo configurável (`GEMINI_MODEL`, padrão `gemini-2.5-flash`), atrás de `get_llm()` para testes com modelo simulado.
2. **Contexto mínimo e real:** cada pedido envia um resumo agregado da empresa ou da pessoa (`app/integrations/ai/context.py`), sem CPF, e-mails ou dados de terceiros. O prompt de sistema proíbe inventar números.
3. **Fallback honesto:** sem chave, com erro ou com cota esgotada, a resposta vem de regras calculadas sobre o mesmo resumo (`app/integrations/ai/rules.py`), marcada com `source: "regra"`. O gerador de orçamentos é a exceção: sem modelo, responde 503, porque não há estimativa honesta de horas sem ele.
4. **Saída estruturada:** insights, categorias e orçamento pedem JSON e são validados; uma saída inválida cai no fallback.
5. **Cota:** `ai_usage` conta só as chamadas reais ao modelo, por empresa e mês, contra o `ai_queries` do plano.

## Consequências

- Em produção: usar o nível pago do Gemini (ou Vertex AI) e citar o Google como operador de dados na política de privacidade.
- A chave atual foi bloqueada como vazada (ver SEC-5): sem uma chave nova, o sistema funciona apenas no modo por regras.
