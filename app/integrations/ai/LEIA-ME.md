# Nota da pasta app/integrations/ai

**Função:** IA: context monta os dados enviados, llm chama o Gemini, rules responde sem IA e service controla a cota do plano.

## O que tem aqui

- `__init__.py`: Arquivo vazio. Faz o Python tratar a pasta de IA como pacote.
- `context.py`: Monta o resumo dos dados reais enviado à IA (empresa ou pessoa): só totais e descrições curtas, sem CPF, e-mail ou dados de outras empresas.
- `llm.py`: Cliente do Gemini (REST). Sem GEMINI_API_KEY devolve vazio e o sistema usa as respostas por regras.
- `rules.py`: Respostas por regras, usadas quando a IA está indisponível ou a cota do plano acabou. Todo número vem dos dados reais.
- `service.py`: Porta única para chamar a IA: confere disponibilidade, cota mensal do plano e registra cada uso.
