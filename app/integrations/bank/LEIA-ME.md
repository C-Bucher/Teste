# Nota da pasta app/integrations/bank

**Função:** Bancos: statement lê os extratos, providers fala com o agregador Pluggy e service guarda e concilia as transações.

## O que tem aqui

- `__init__.py`: Arquivo vazio. Faz o Python tratar a pasta de bancos como pacote.
- `providers.py`: Interface para agregadores bancários (Open Finance). Só o Pluggy está implementado; sem credenciais, as rotas respondem 503.
- `service.py`: Grava as transações do extrato sem duplicar e concilia cada uma com contas a pagar/receber (mesmo valor, até 5 dias de diferença).
- `statement.py`: Lê arquivos de extrato (OFX 1.x, OFX 2.x e CSV) dos bancos brasileiros e converte para um formato único.
