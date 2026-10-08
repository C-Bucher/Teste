# ADR-010 — Cobrança recorrente e acesso por assinatura

- **Status:** Aceito
- **Data:** 2026-10-07

## Contexto

O checkout gravava a assinatura como paga sem cobrar nada, e enviava número de cartão e CVV ao nosso servidor, o que colocaria o sistema no escopo do PCI DSS. Além disso, `GET /payments/subscription` criava uma assinatura ATIVA para qualquer empresa que não tivesse uma, de modo que, na prática, o acesso era gratuito.

## Decisão

1. **Intermediador:** Asaas, atrás da interface `PaymentProvider` (`app/integrations/payments/providers.py`). O checkout cria cliente e assinatura recorrente (Pix, boleto ou cartão) e devolve o link da página de pagamento do Asaas. O TechConnect não recebe nem guarda dados de cartão.
2. **Confirmação só pelo webhook:** o webhook (`/payments/webhook/asaas`) é autenticado pelo token configurado no painel (`ASAAS_WEBHOOK_TOKEN`), comparado em tempo constante. Ele é a única fonte de "pago": ativa o plano, renova o período a cada cobrança confirmada, marca atraso e estornos. O processamento é idempotente por id de pagamento.
3. **Regras de acesso** (`app/core/billing.py`):
   - 7 dias de teste a partir do cadastro (`TRIAL_DAYS`);
   - tolerância de 5 dias para cobranças vencidas (`GRACE_DAYS`);
   - uma assinatura cancelada vale até o fim do período pago;
   - sem acesso, os módulos respondem 402 com `X-Subscription: blocked`. Autenticação, Assinatura, Planos, Minha Conta e os webhooks continuam abertos, para que o cliente consiga pagar e exercer os direitos da LGPD.
4. **Troca de plano:** a nova assinatura só substitui a anterior quando o primeiro pagamento é confirmado; a anterior é cancelada no intermediador.
5. **Provedor simulado:** sem `ASAAS_API_KEY`, há um provedor que confirma na hora, apenas fora de produção. Em produção, o checkout responde 503.
6. **Bases antigas:** empresas anteriores à cobrança ganham um teste ao primeiro acesso, em vez de bloqueio. A empresa demo tem assinatura ativa sem vencimento.

## Consequências

- Antes de vender, é preciso:
  - abrir a conta no Asaas;
  - configurar o webhook e validar o fluxo no sandbox, inclusive a cobrança recorrente de cartão pela página do Asaas.
- O CPF ou CNPJ do pagador passa a ser obrigatório no checkout real.
- O módulo de pagamentos depende do webhook estar acessível pela internet. Uma cobrança paga sem webhook entregue fica pendente até o Asaas reenviar o evento.
