# Nota da pasta app/integrations/payments

**Função:** Pagamentos: providers tem o Asaas (real) e o provedor simulado (só fora de produção).

## O que tem aqui

- `__init__.py`: Arquivo vazio. Faz o Python tratar a pasta de pagamentos como pacote.
- `providers.py`: Provedores de pagamento da assinatura: Asaas (real; o cartão é digitado na página do Asaas) e um provedor simulado, que só existe fora de produção.
