# Nota da pasta app/integrations

**Função:** Ligações com serviços externos, cada uma atrás de uma interface para poder trocar o fornecedor: IA (Gemini), bancos (Pluggy, OFX/CSV) e pagamentos (Asaas).

## O que tem aqui

- `__init__.py`: Arquivo vazio. Faz o Python tratar a pasta app/integrations como pacote.
- `ai/`: IA: context monta os dados enviados, llm chama o Gemini, rules responde sem IA e service controla a cota do plano.
- `bank/`: Bancos: statement lê os extratos, providers fala com o agregador Pluggy e service guarda e concilia as transações.
- `payments/`: Pagamentos: providers tem o Asaas (real) e o provedor simulado (só fora de produção).
