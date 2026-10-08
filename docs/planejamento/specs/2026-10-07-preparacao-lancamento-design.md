# Etapa 5 — Preparação para o lançamento

- **Data:** 2026-10-07
- **Branch:** `feature/lancamento` (empilhado sobre `feature/ia-generativa`)
- **Objetivo:** fechar o que separa o código atual de um produto que pode cobrar clientes. Além disso, colocar a documentação acadêmica em dia com o que foi entregue em 30/09.

## Decisões

| Tema | Decisão | Motivo |
| --- | --- | --- |
| Pagamento (PAY-1) | Asaas atrás de uma interface `PaymentProvider`; o provedor simulado continua para desenvolvimento | Assinatura recorrente nativa (Pix, boleto, cartão), sandbox gratuito. O cartão é digitado na página do Asaas, então o TechConnect não trafega dados de cartão (fora do escopo PCI) |
| E-mail (AUTH-3, NOT-1) | SMTP genérico (`SMTP_*`); sem configuração, o e-mail é só registrado em log | Funciona com qualquer provedor |
| Recuperação de senha (AUTH-3) | Token aleatório de uso único, válido por 1 h, guardado só como hash; a resposta é a mesma exista ou não o e-mail | Evita descobrir quais e-mails têm conta |
| 2FA (AUTH-1) | TOTP (Google Authenticator e similares) com 8 códigos de recuperação de uso único | Padrão de mercado, sem custo de SMS |
| Limite por IP (SEC-7) | Janela deslizante em memória nas rotas de autenticação (padrão: 20 req/min por IP) | Sem dependência nova; uma instância por enquanto |
| Consentimento (SEC-2) | Aceite obrigatório do termo de uso e da política de privacidade no cadastro, com versão e data gravadas; páginas `/termos` e `/privacidade` como minuta | O texto final depende de revisão jurídica |
| Armazenamento (STO-1) | Interface com dois backends: disco local (padrão) e qualquer serviço compatível com S3 (Supabase Storage, AWS S3, R2) via `STORAGE_BACKEND=s3` | Várias instâncias passam a compartilhar arquivos |
| Bancos | Webhook da Pluggy (`/bank/webhook/pluggy`) e rota de sincronização geral para agendador externo (`/bank/sync-all`, protegida por `CRON_SECRET`) | Sincronização sem clique |
| Exportação (EXP-1) | XLSX (openpyxl) e PDF (reportlab), além de CSV e JSON | Formatos que o cliente espera |
| Acesso por assinatura | Cadastro novo ganha 7 dias de teste (`TRIAL_DAYS`). Pagamento vencido há mais de 5 dias (`GRACE_DAYS`) bloqueia os módulos com 402, mantendo acesso a Assinatura, Planos e Minha Conta | Cobrança com consequência, sem trancar a saída |
| Qualidade (QA-1) | Zerar erros do ESLint, criar testes de frontend (Vitest) e CI no GitHub Actions (pytest em SQLite e PostgreSQL, lint, testes e build) | Cada PR verificado automaticamente |
| Contrato de API | Teste que falha se o frontend chamar uma rota que não existe no backend | As 128 chamadas atuais estão cobertas |

## Fora do escopo
- Antivírus nos uploads (fica registrado como pendência).
- O texto jurídico definitivo.
- O contrato com o Asaas e com a Pluggy (credenciais são do dono).

## Pronto quando
- Os testes do backend ficam verdes em SQLite, PostgreSQL e MySQL.
- Os testes do frontend, o lint sem erros e o build passam.
- Os documentos `requisitos.md`, `arquitetura.md`, o registro de alterações, a Sprint 03, o BACKLOG, o README e o CHANGELOG refletem o código.
