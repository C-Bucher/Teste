# Etapa 4 — IA generativa real (IA-1) e cota de uso (LIM-1)

- **Data:** 2026-09-30
- **Branch:** `feature/ia-generativa` (empilhado sobre `feature/integracao-bancaria`)

## Problema

O CFO Virtual, o CFO Pessoal, a conciliação e o gerador de orçamentos respondem com textos e números **fixos no código**, iguais para qualquer empresa. A tela de conciliação ignora o arquivo enviado e usa três transações simuladas. O histórico do chat sempre volta vazio.

## Decisões

- **Modelo:** Gemini (`GEMINI_API_KEY`, já prevista na infra), chamado por REST (`generateContent`). O modelo é configurável em `GEMINI_MODEL` (padrão `gemini-2.5-flash`). O cliente fica atrás de uma função `get_llm()` para os testes injetarem um modelo simulado.
- **Contexto com dados reais e mínimos:** cada pedido monta um resumo agregado da empresa (receitas e despesas pagas em 30/90 dias, contas a pagar e a receber dos próximos 30 dias, principais categorias, custo mensal da equipe, projetos ativos, movimentações bancárias sem categoria) ou da pessoa (saldos, dívidas, orçamento × gasto, assinaturas, metas). Não vão CPF, e-mails nem dados de outras empresas.
- **Sem chave, com falha ou com cota esgotada:** respostas por regra, **calculadas a partir do mesmo resumo real**. Nada é inventado. A resposta informa a origem (`source: "ia"` ou `"regra"`).
- **Cota (LIM-1):** contador mensal por empresa (`ai_usage`). Só chamadas reais ao modelo contam. O limite vem do plano (`ai_queries`).
- **Histórico:** `ai_messages` (empresa, usuário, papel, texto, modelo). `GET /ai/history` devolve só as mensagens do próprio usuário.

## Endpoints

- `POST /ai/chat` `{message}` → `{response, source, model}`, com histórico recente como contexto.
- `GET /ai/history` → mensagens do usuário.
- `POST /ai/consultant/cfo` → `insights[]` (`OPORTUNIDADE`/`ALERTA`, título, descrição, impacto, urgência).
- `POST /ai/consultant/conciliation` → sugere categorias para as movimentações bancárias NOVAS sem categoria da empresa (até 30), usando as categorias que a empresa já usa. A aprovação grava via `POST /bank/transactions/{id}/category`.
- `POST /ai/consultant/proposal` `{briefing, markup}` → horas estimadas pelo modelo × custo-hora médio real da equipe (CTC). Sem IA disponível, responde 503, porque não há estimativa honesta de horas sem o modelo.
- `POST /personal/ai/insights` → `insights[]` (`ALERT`/`OPPORTUNITY`/`CUT`, mensagem, valor de impacto).

## LGPD e custo

- O resumo enviado ao Google contém valores e descrições de lançamentos. Para produção:
  - usar o **nível pago** da API Gemini ou o Vertex AI, porque no nível gratuito o Google pode usar os dados para melhorar seus produtos;
  - citar o Google como operador na política de privacidade.
- O custo por pergunta é baixo (modelo Flash), mas a cota por plano protege a margem.

## Pronto quando
- Os testes cobrem: chat com modelo simulado (resposta, histórico, contexto real no prompt), fallback sem chave com números reais, cota esgotada, insights de CFO empresarial e pessoal, sugestão de categoria e orçamento.
- Nenhum número fixo sobra em `ai.py` ou em `personal.py`.
- A suíte fica verde nos 3 bancos e o build passa.
